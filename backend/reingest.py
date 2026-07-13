"""
Corpus re-ingest orchestration + optional background schedule.

Used by:
  - CLI: python reingest.py [--force]
  - FastAPI admin endpoints
  - Background thread when REINGEST_INTERVAL_HOURS > 0
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_lock = threading.Lock()
_state: dict[str, Any] = {
    "running": False,
    "last_started": None,
    "last_finished": None,
    "last_ok": None,
    "last_error": None,
    "last_result": None,
    "runs": 0,
    "scheduler": {
        "enabled": False,
        "interval_hours": 0,
        "next_run": None,
        "thread_alive": False,
    },
}


def backend_dir() -> Path:
    return Path(__file__).resolve().parent


def state_path() -> Path:
    d = backend_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "reingest_state.json"


def get_state() -> dict[str, Any]:
    with _lock:
        return json.loads(json.dumps(_state))  # deep-ish copy via JSON


def _persist() -> None:
    try:
        with open(state_path(), "w", encoding="utf-8") as f:
            json.dump(_state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[reingest] state save error: {e}")


def _load_persisted() -> None:
    path = state_path()
    if not path.exists():
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            saved = json.load(f)
        with _lock:
            for k in ("last_started", "last_finished", "last_ok", "last_error", "last_result", "runs"):
                if k in saved:
                    _state[k] = saved[k]
    except Exception:
        pass


_load_persisted()


def run_reingest(
    *,
    force: bool = False,
    import_pdfs_from: str | None = None,
    reload_callback: Optional[Callable[[], Any]] = None,
) -> dict[str, Any]:
    """
    Full pipeline: optional bulk PDF import → scraper → optional RAG reload callback.
    Thread-safe: only one run at a time.
    """
    with _lock:
        if _state["running"]:
            return {"ok": False, "error": "Re-ingest already running", "state": get_state()}
        _state["running"] = True
        _state["last_started"] = datetime.now(timezone.utc).isoformat()
        _state["last_error"] = None
        _persist()

    result: dict[str, Any] = {
        "ok": False,
        "force": force,
        "import": None,
        "scraper": None,
        "reload": None,
        "started": _state["last_started"],
    }

    try:
        if import_pdfs_from:
            from bulk_import_pdfs import import_folder

            print(f"[reingest] Bulk import from {import_pdfs_from}")
            # import_folder already rebuilds; we still rebuild below if needed
            result["import"] = import_folder(
                import_pdfs_from,
                copy=True,
                rebuild=False,
                force=False,
            )

        from scraper import run_scraper

        print(f"[reingest] Running scraper force={force}")
        docs = run_scraper(force_arlis=force, force_all=force)
        by_type: dict[str, int] = {}
        for d in docs or []:
            t = d.get("doc_type") or "?"
            by_type[t] = by_type.get(t, 0) + 1
        result["scraper"] = {
            "documents": len(docs or []),
            "by_type": by_type,
        }

        if reload_callback:
            print("[reingest] Reloading RAG engine…")
            reload_info = reload_callback()
            result["reload"] = reload_info if reload_info is not None else {"ok": True}

        result["ok"] = True
        result["finished"] = datetime.now(timezone.utc).isoformat()

        with _lock:
            _state["last_ok"] = True
            _state["last_error"] = None
            _state["last_result"] = {
                "documents": result["scraper"]["documents"],
                "by_type": by_type,
                "finished": result["finished"],
            }
            _state["runs"] = int(_state.get("runs") or 0) + 1
            _state["last_finished"] = result["finished"]
            _persist()

        print(f"[reingest] OK — {result['scraper']['documents']} docs")
        return result

    except Exception as e:
        err = f"{e}\n{traceback.format_exc()}"
        print(f"[reingest] FAILED: {e}")
        result["ok"] = False
        result["error"] = str(e)
        result["finished"] = datetime.now(timezone.utc).isoformat()
        with _lock:
            _state["last_ok"] = False
            _state["last_error"] = str(e)
            _state["last_finished"] = result["finished"]
            _state["last_result"] = {"error": str(e)}
            _persist()
        return result
    finally:
        with _lock:
            _state["running"] = False
            _persist()


def run_reingest_async(
    *,
    force: bool = False,
    import_pdfs_from: str | None = None,
    reload_callback: Optional[Callable[[], Any]] = None,
) -> dict[str, Any]:
    """Start re-ingest in a daemon thread if not already running."""
    with _lock:
        if _state["running"]:
            return {"ok": False, "error": "Re-ingest already running", "started": False}

    def _worker():
        run_reingest(
            force=force,
            import_pdfs_from=import_pdfs_from,
            reload_callback=reload_callback,
        )

    t = threading.Thread(target=_worker, name="mlsa-reingest", daemon=True)
    t.start()
    return {"ok": True, "started": True, "message": "Re-ingest started in background"}


_scheduler_stop = threading.Event()
_scheduler_thread: Optional[threading.Thread] = None


def start_scheduler(
    interval_hours: float,
    *,
    force: bool = False,
    reload_callback: Optional[Callable[[], Any]] = None,
    run_immediately: bool = False,
) -> dict[str, Any]:
    """Start recurring re-ingest. Safe to call once at app startup."""
    global _scheduler_thread

    if interval_hours <= 0:
        with _lock:
            _state["scheduler"] = {
                "enabled": False,
                "interval_hours": 0,
                "next_run": None,
                "thread_alive": False,
            }
        return {"enabled": False, "reason": "interval_hours <= 0"}

    # Restart if already running
    stop_scheduler()
    _scheduler_stop.clear()

    interval_sec = max(300.0, float(interval_hours) * 3600.0)  # min 5 minutes

    def _loop():
        if run_immediately:
            run_reingest(force=force, reload_callback=reload_callback)
        while not _scheduler_stop.is_set():
            next_ts = time.time() + interval_sec
            with _lock:
                _state["scheduler"] = {
                    "enabled": True,
                    "interval_hours": interval_hours,
                    "next_run": datetime.fromtimestamp(next_ts, tz=timezone.utc).isoformat(),
                    "thread_alive": True,
                }
                _persist()
            # Sleep in small chunks so stop is responsive
            while time.time() < next_ts:
                if _scheduler_stop.wait(timeout=min(30.0, next_ts - time.time())):
                    return
            if _scheduler_stop.is_set():
                return
            run_reingest(force=force, reload_callback=reload_callback)

        with _lock:
            _state["scheduler"]["thread_alive"] = False
            _state["scheduler"]["enabled"] = False

    _scheduler_thread = threading.Thread(target=_loop, name="mlsa-reingest-scheduler", daemon=True)
    _scheduler_thread.start()
    print(f"[reingest] Scheduler started: every {interval_hours}h")
    return {
        "enabled": True,
        "interval_hours": interval_hours,
        "run_immediately": run_immediately,
    }


def stop_scheduler() -> None:
    global _scheduler_thread
    _scheduler_stop.set()
    t = _scheduler_thread
    if t and t.is_alive():
        t.join(timeout=2.0)
    _scheduler_thread = None


if __name__ == "__main__":
    force = "--force" in sys.argv
    import_from = None
    for i, a in enumerate(sys.argv):
        if a == "--import" and i + 1 < len(sys.argv):
            import_from = sys.argv[i + 1]
    out = run_reingest(force=force, import_pdfs_from=import_from)
    print(json.dumps({k: v for k, v in out.items() if k != "error" or not out.get("ok")}, ensure_ascii=False, indent=2))
    if not out.get("ok"):
        print(out.get("error") or "failed", file=sys.stderr)
        raise SystemExit(1)

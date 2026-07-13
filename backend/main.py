import os
import sys
import time
import json
from collections import defaultdict, deque
from pathlib import Path
from threading import Lock

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Any, Optional
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rag_engine import RAGEngine, OLLAMA_HOST, OLLAMA_MODEL
from fidelity import load_eval_stats, EVAL_CASES, evaluate_grounding, log_qa_event
from reingest import (
    get_state as get_reingest_state,
    run_reingest_async,
    start_scheduler,
)

app = FastAPI(
    title="MLSA Welfare RAG API",
    version="2.5",
    description="WISE Foundation website + MLSA/ARLIS RAG (summaries, legal acts, PDFs, web) + scheduled re-ingest",
)

# CORS: production-safe default is same-origin + localhost.
# Set CORS_ORIGINS=* only when you explicitly want wide-open public API.
# Or CORS_ORIGINS=https://a.com,https://b.com for multi-host.
def _resolve_cors_origins() -> list[str]:
    raw = (os.environ.get("CORS_ORIGINS") or "").strip()
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()] or ["*"]
    # Explicit opt-in to wide open
    if (os.environ.get("WISEF_CORS_OPEN") or "").strip().lower() in ("1", "true", "yes"):
        return ["*"]
    # Default: local dev + same host patterns (browser same-origin still works without CORS)
    return [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ]


_cors_origins = _resolve_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False if "*" in _cors_origins else True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Simple in-memory rate limit (per IP) for expensive endpoints
_RATE_LIMIT = int(os.environ.get("CHAT_RATE_LIMIT", "20"))  # requests
_RATE_WINDOW = int(os.environ.get("CHAT_RATE_WINDOW_SEC", "60"))  # seconds
_rate_buckets: dict[str, deque] = defaultdict(deque)
_rate_lock = Lock()


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") or ""
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host or "unknown"
    return "unknown"


def _rate_limit_ok(ip: str, limit: int = _RATE_LIMIT, window: int = _RATE_WINDOW) -> bool:
    now = time.time()
    with _rate_lock:
        q = _rate_buckets[ip]
        while q and now - q[0] > window:
            q.popleft()
        if len(q) >= limit:
            return False
        q.append(now)
        return True

print("Initializing RAG Engine...")
try:
    rag_engine = RAGEngine()
except Exception as e:
    print(f"Error starting RAG Engine: {e}")
    rag_engine = None

_rag_lock = Lock()
_ADMIN_TOKEN = (os.environ.get("ADMIN_TOKEN") or os.environ.get("REINGEST_TOKEN") or "").strip()


def reload_rag_engine() -> dict[str, Any]:
    """Hot-reload corpus into a new RAGEngine without restarting the process."""
    global rag_engine
    print("[main] Hot-reloading RAG engine…")
    new_engine = RAGEngine()
    with _rag_lock:
        rag_engine = new_engine
    return {
        "ok": True,
        "documents": len(new_engine.documents),
        "chunks": len(new_engine.chunks),
        "vector_search": new_engine.vector_enabled,
        "corpus_hash": new_engine.corpus_hash,
        "legal_acts": new_engine.legal_acts,
    }


def _require_admin(authorization: Optional[str], x_admin_token: Optional[str]) -> None:
    """
    Protect admin/ingest endpoints.
    If ADMIN_TOKEN is unset, allow only from localhost (dev convenience).
    """
    provided = ""
    if x_admin_token:
        provided = x_admin_token.strip()
    elif authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()

    if _ADMIN_TOKEN:
        if provided != _ADMIN_TOKEN:
            raise HTTPException(status_code=401, detail="Invalid or missing admin token")
        return

    # No token configured — only local machine may trigger re-ingest
    # (checked by caller with request client when needed)


def _admin_or_local(request: Request, authorization: Optional[str], x_admin_token: Optional[str]) -> None:
    if _ADMIN_TOKEN:
        _require_admin(authorization, x_admin_token)
        return
    ip = _client_ip(request)
    if ip not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(
            status_code=401,
            detail="Set ADMIN_TOKEN env to allow remote re-ingest, or call from localhost",
        )


# Frontend paths (Docker: /app/frontend ; local: ../src next to backend/)
_BACKEND_DIR = Path(__file__).resolve().parent
_FRONTEND_CANDIDATES = [
    _BACKEND_DIR / "frontend",
    _BACKEND_DIR.parent / "src",
]
FRONTEND_ROOT = next((p for p in _FRONTEND_CANDIDATES if p.is_dir()), None)
if FRONTEND_ROOT:
    print(f"Frontend static files: {FRONTEND_ROOT}")
else:
    print("Frontend static folder not found — / will show API-only page")

def _reingest_mode_file() -> Path:
    return _BACKEND_DIR / "data" / "reingest_mode.json"


def _read_reingest_mode() -> str:
    """
    Single schedule path:
      - env REINGEST_MODE=inprocess|windows|off overrides
      - data/reingest_mode.json written by install_scheduled_reingest.ps1
      - default: inprocess when REINGEST_INTERVAL_HOURS>0, else off
    """
    env_mode = (os.environ.get("REINGEST_MODE") or "").strip().lower()
    if env_mode in ("inprocess", "windows", "off"):
        return env_mode
    path = _BACKEND_DIR / "data" / "reingest_mode.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            m = (data.get("mode") or "").strip().lower()
            if m in ("inprocess", "windows", "off"):
                return m
        except Exception:
            pass
    return "inprocess"


# Optional background re-ingest — disabled if Windows task owns the schedule
try:
    _interval = float(os.environ.get("REINGEST_INTERVAL_HOURS") or "0")
except ValueError:
    _interval = 0.0
_sched_force = (os.environ.get("REINGEST_FORCE") or "").lower() in ("1", "true", "yes")
_sched_immediate = (os.environ.get("REINGEST_ON_START") or "").lower() in ("1", "true", "yes")
_reingest_mode = _read_reingest_mode()
if _reingest_mode == "windows":
    print("[main] Re-ingest mode=windows — in-process scheduler OFF (use Task Scheduler only)")
    _interval = 0.0
elif _reingest_mode == "off":
    print("[main] Re-ingest mode=off")
    _interval = 0.0
if _interval > 0:
    start_scheduler(
        _interval,
        force=_sched_force,
        reload_callback=reload_rag_engine,
        run_immediately=_sched_immediate,
    )
else:
    print("[main] In-process scheduled re-ingest off (set REINGEST_INTERVAL_HOURS=24 + mode=inprocess)")


class ChatHistoryTurn(BaseModel):
    role: str = "user"
    content: str = ""


class ChatRequest(BaseModel):
    query: str
    lang: str = "hy"
    history: list[ChatHistoryTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[Any] = Field(default_factory=list)
    vector_search: bool = False
    follow_ups: list[str] = Field(default_factory=list)
    fidelity: Optional[dict[str, Any]] = None
    generation_mode: Optional[str] = None


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=200)
    subject: str = Field(default="", max_length=300)
    message: str = Field(..., min_length=5, max_length=5000)


def _doc_type_counts() -> dict[str, int]:
    if not rag_engine:
        return {}
    counts: dict[str, int] = {}
    for d in getattr(rag_engine, "documents", []) or []:
        t = d.get("doc_type") or "?"
        counts[t] = counts.get(t, 0) + 1
    return counts


def _status_payload() -> dict:
    ollama_ok = False
    try:
        r = requests.get(OLLAMA_HOST, timeout=2)
        if r.status_code == 200:
            ollama_ok = True
    except Exception:
        pass

    legal_acts = 0
    cache_ok = False
    corpus_hash = ""
    if rag_engine:
        legal_acts = getattr(rag_engine, "legal_acts", 0)
        cache_ok = getattr(rag_engine, "cache_ok", False)
        corpus_hash = getattr(rag_engine, "corpus_hash", "")

    stats = load_eval_stats(limit=200)
    return {
        "status": "ready" if rag_engine else "error",
        "version": "2.5",
        "vector_search_active": rag_engine.vector_enabled if rag_engine else False,
        "vector_backend": getattr(rag_engine, "vector_backend", None) if rag_engine else None,
        "embed_skip_reason": getattr(rag_engine, "embed_skip_reason", None) if rag_engine else None,
        "ollama_connected": ollama_ok,
        "ollama_host": OLLAMA_HOST,
        "model": OLLAMA_MODEL,
        "documents_indexed": len(rag_engine.documents) if rag_engine else 0,
        "chunks_indexed": len(rag_engine.chunks) if rag_engine else 0,
        "doc_types": _doc_type_counts(),
        "legal_acts": legal_acts,
        "cache_ok": cache_ok,
        "corpus_hash": corpus_hash,
        "frontend_mounted": bool(FRONTEND_ROOT),
        "rate_limit": {"max": _RATE_LIMIT, "window_sec": _RATE_WINDOW},
        "admin_token_configured": bool(_ADMIN_TOKEN),
        "cors_origins": _cors_origins,
        "reingest_mode": _reingest_mode,
        "reingest": get_reingest_state(),
        "fidelity_summary": {
            "entries": stats.get("entries"),
            "avg_grounding_score": stats.get("avg_grounding_score"),
            "avg_hallucination_rate": stats.get("avg_hallucination_rate"),
            "risk_counts": stats.get("risk_counts"),
        },
    }


def _api_only_html() -> str:
    s = _status_payload()
    ok = s["status"] == "ready"
    badge = "#10b981" if ok else "#ef4444"
    label = "READY" if ok else "ERROR"
    fs = s.get("fidelity_summary") or {}
    hall = fs.get("avg_hallucination_rate")
    ground = fs.get("avg_grounding_score")
    hall_s = f"{hall:.0%}" if isinstance(hall, (int, float)) else "n/a"
    ground_s = f"{ground:.0%}" if isinstance(ground, (int, float)) else "n/a"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WISE AI Backend (not the full site)</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto;
           padding: 0 20px; color: #0f172a; line-height: 1.5; }}
    .warn {{ background: #fff7ed; border: 1px solid #fdba74; border-radius: 12px;
             padding: 14px 16px; margin: 16px 0; }}
    .badge {{ display: inline-block; background: {badge}; color: #fff;
              padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }}
    a {{ color: #183960; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
             padding: 14px 16px; margin: 16px 0; }}
  </style>
</head>
<body>
  <h1>WISE AI Backend</h1>
  <p><span class="badge">{label}</span></p>
  <div class="warn">
    <strong>This is not the full WISE marketing website.</strong><br>
    This page is the <em>AI server</em> status. The public site is either:
    <ul>
      <li>GitHub Pages (your static site), with <code>productionApiBase</code> pointing here, or</li>
      <li>Redeploy this service with the latest Docker image that includes the frontend
          (then open <code>/pages/index.html</code>).</li>
    </ul>
  </div>
  <div class="card">
    <strong>Corpus</strong>
    <ul>
      <li>Documents: {s['documents_indexed']}</li>
      <li>Chunks: {s['chunks_indexed']}</li>
      <li>ARLIS acts: {s['legal_acts']}</li>
    </ul>
    <strong>Fidelity</strong>
    <ul>
      <li>Logged: {fs.get('entries', 0)}</li>
      <li>Grounding: {ground_s}</li>
      <li>Hallucination rate: {hall_s}</li>
    </ul>
  </div>
  <p>API:</p>
  <ul>
    <li><a href="/api/status"><code>GET /api/status</code></a></li>
    <li><code>POST /api/chat</code></li>
    <li><a href="/api/eval/stats"><code>GET /api/eval/stats</code></a></li>
    <li><a href="/docs"><code>/docs</code></a></li>
  </ul>
</body>
</html>"""


@app.get("/api/status")
def get_status():
    return _status_payload()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, req: Request):
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if len(request.query) > 2000:
        raise HTTPException(status_code=400, detail="Query too long (max 2000 characters)")

    ip = _client_ip(req)
    if not _rate_limit_ok(ip):
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit {_RATE_LIMIT} per {_RATE_WINDOW}s. Try again shortly.",
        )

    print(f"Received query ({request.lang}) from {ip}: {request.query[:120]}")
    try:
        with _rag_lock:
            engine = rag_engine
        if not engine:
            raise HTTPException(status_code=500, detail="RAG Engine is not initialized")
        hist = [
            {"role": t.role, "content": t.content}
            for t in (request.history or [])
            if (t.content or "").strip()
        ][-8:]
        result = engine.generate_response(request.query, request.lang, history=hist or None)
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources") or [],
            vector_search=bool(result.get("vector_search")),
            follow_ups=result.get("follow_ups") or [],
            fidelity=result.get("fidelity"),
            generation_mode=result.get("generation_mode"),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ReingestRequest(BaseModel):
    force: bool = False
    import_path: Optional[str] = Field(
        default=None,
        description="Optional folder of PDFs to copy into backend/pdfs before rebuild",
    )


class ImportPdfsRequest(BaseModel):
    source: Optional[str] = Field(
        default=None,
        description="Folder or PDF path. Default: backend/pdfs",
    )
    force: bool = False
    rebuild: bool = True


@app.get("/api/admin/ingest-status")
def ingest_status(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    _admin_or_local(request, authorization, x_admin_token)
    st = get_reingest_state()
    pdf_dir = _BACKEND_DIR / "pdfs"
    pdfs = sorted([p.name for p in pdf_dir.glob("*.pdf")]) if pdf_dir.is_dir() else []
    return {
        "reingest": st,
        "library_pdfs": pdfs,
        "library_count": len(pdfs),
        "documents_indexed": len(rag_engine.documents) if rag_engine else 0,
        "doc_types": _doc_type_counts(),
        "corpus_hash": getattr(rag_engine, "corpus_hash", None) if rag_engine else None,
    }


@app.post("/api/admin/reingest")
def admin_reingest(
    payload: ReingestRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Trigger full corpus rebuild (async) and hot-reload RAG when done."""
    _admin_or_local(request, authorization, x_admin_token)
    out = run_reingest_async(
        force=bool(payload.force),
        import_pdfs_from=payload.import_path,
        reload_callback=reload_rag_engine,
    )
    if not out.get("ok") and not out.get("started"):
        raise HTTPException(status_code=409, detail=out.get("error") or "Could not start re-ingest")
    return out


@app.post("/api/admin/import-pdfs")
def admin_import_pdfs(
    payload: ImportPdfsRequest,
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """
    Bulk-import PDFs from a folder (or backend/pdfs), rebuild corpus, hot-reload.
    Runs async so the HTTP call returns immediately.
    """
    _admin_or_local(request, authorization, x_admin_token)

    source = (payload.source or "").strip() or str(_BACKEND_DIR / "pdfs")
    lib = str((_BACKEND_DIR / "pdfs").resolve())
    try:
        src_resolved = str(Path(source).resolve())
    except Exception:
        src_resolved = source

    st = get_reingest_state()
    if st.get("running"):
        raise HTTPException(status_code=409, detail="Re-ingest already running")

    # Always rebuild via reingest; copy from external folders first
    import_from = None if src_resolved == lib else source
    out = run_reingest_async(
        force=bool(payload.force),
        import_pdfs_from=import_from,
        reload_callback=reload_rag_engine if payload.rebuild else None,
    )
    if not out.get("started") and not out.get("ok"):
        raise HTTPException(status_code=409, detail=out.get("error") or "busy")

    mode = "rebuild_from_library" if import_from is None else "import_and_rebuild"
    return {**out, "source": source, "mode": mode}


@app.post("/api/admin/reload")
def admin_reload(
    request: Request,
    authorization: Optional[str] = Header(default=None),
    x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
):
    """Reload RAG from existing mlsa_programs.json without re-downloading."""
    _admin_or_local(request, authorization, x_admin_token)
    try:
        return reload_rag_engine()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/contact")
def contact(payload: ContactRequest, req: Request):
    """Store contact form submissions (and optional webhook)."""
    ip = _client_ip(req)
    if not _rate_limit_ok(ip, limit=8, window=300):
        raise HTTPException(status_code=429, detail="Too many contact submissions. Try later.")

    name = payload.name.strip()
    email = payload.email.strip()
    subject = (payload.subject or "").strip() or "Website contact"
    message = payload.message.strip()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Invalid email")

    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ip": ip,
        "name": name,
        "email": email,
        "subject": subject,
        "message": message,
    }
    data_dir = _BACKEND_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    log_path = data_dir / "contact_messages.jsonl"
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"Contact log error: {e}")
        raise HTTPException(status_code=500, detail="Could not save message")

    # Optional webhook (Slack/email service)
    webhook = (os.environ.get("CONTACT_WEBHOOK_URL") or "").strip()
    if webhook:
        try:
            requests.post(webhook, json=entry, timeout=10)
        except Exception as e:
            print(f"Contact webhook error: {e}")

    return {"ok": True, "message": "Message received"}


@app.get("/api/eval/stats")
def eval_stats(limit: int = 500):
    return load_eval_stats(limit=min(max(limit, 10), 5000))


@app.post("/api/eval/check")
def eval_check(payload: dict[str, Any]):
    answer = (payload or {}).get("answer") or ""
    context = (payload or {}).get("context") or ""
    if not answer:
        raise HTTPException(status_code=400, detail="answer is required")
    result = evaluate_grounding(answer, context)
    try:
        log_qa_event({
            "query": (payload or {}).get("query") or "(manual check)",
            "mode": "manual",
            "answer_preview": answer[:400],
            **result,
        })
    except Exception:
        pass
    return result


@app.post("/api/eval/run")
def eval_run():
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

    results = []
    for case in EVAL_CASES:
        try:
            out = rag_engine.generate_response(case["query"], case.get("lang", "hy"))
            answer = out.get("answer") or ""
            fid = out.get("fidelity") or {}
            must = case.get("must_contain_any") or []
            hit = any(m.lower() in answer.lower() for m in must) if must else True
            results.append({
                "id": case["id"],
                "query": case["query"],
                "ok_keyword_check": hit,
                "generation_mode": out.get("generation_mode"),
                "answer_len": len(answer),
                "answer_preview": answer[:280],
                "fidelity": fid,
                "sources": [s.get("title") for s in (out.get("sources") or [])[:4]],
            })
        except Exception as e:
            results.append({
                "id": case["id"],
                "query": case["query"],
                "error": str(e),
            })

    halls = [
        r["fidelity"]["hallucination_rate"]
        for r in results
        if r.get("fidelity") and r["fidelity"].get("hallucination_rate") is not None
    ]
    grounds = [
        r["fidelity"]["grounding_score"]
        for r in results
        if r.get("fidelity") and r["fidelity"].get("grounding_score") is not None
    ]
    summary = {
        "cases": len(results),
        "avg_hallucination_rate": round(sum(halls) / len(halls), 3) if halls else None,
        "avg_grounding_score": round(sum(grounds) / len(grounds), 3) if grounds else None,
        "keyword_pass": sum(1 for r in results if r.get("ok_keyword_check")),
    }
    return {"summary": summary, "results": results}


@app.get("/api", response_class=HTMLResponse, include_in_schema=False)
@app.get("/api/", response_class=HTMLResponse, include_in_schema=False)
def api_dashboard():
    """Backend status dashboard (not the public marketing site)."""
    return HTMLResponse(content=_api_only_html())


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if FRONTEND_ROOT:
        icon = FRONTEND_ROOT / "assets" / "logos" / "favicon.svg"
        if icon.is_file():
            return FileResponse(icon, media_type="image/svg+xml")
    return Response(status_code=204)


# ── Static website (when frontend folder is present) ─────────────────
if FRONTEND_ROOT:
    _css = FRONTEND_ROOT / "css"
    _js = FRONTEND_ROOT / "js"
    _assets = FRONTEND_ROOT / "assets"
    _pages = FRONTEND_ROOT / "pages"

    if _css.is_dir():
        app.mount("/css", StaticFiles(directory=str(_css)), name="css")
    if _js.is_dir():
        app.mount("/js", StaticFiles(directory=str(_js)), name="js")
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")
    if _pages.is_dir():
        app.mount("/pages", StaticFiles(directory=str(_pages), html=True), name="pages")

    @app.get("/", include_in_schema=False)
    def site_home():
        return RedirectResponse(url="/pages/index.html", status_code=302)

else:

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def root_api_only():
        return HTMLResponse(content=_api_only_html())


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    uvicorn.run("main:app", host=host, port=port, reload=reload)

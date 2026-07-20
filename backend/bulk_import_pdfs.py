"""
Bulk-import ministry PDFs into the RAG corpus.

Usage:
  python bulk_import_pdfs.py
  python bulk_import_pdfs.py "D:\\MLSA_PDFs"
  python bulk_import_pdfs.py "D:\\MLSA_PDFs" --no-copy --rebuild
  python bulk_import_pdfs.py --rebuild-only

What it does:
  1) Collects .pdf from the source folder (recursive)
  2) Copies them into backend/pdfs/ (unless --no-copy and source IS pdfs)
  3) Optionally rebuilds the full corpus via scraper (default: yes)
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from ingest_common import backend_dir as _backend_dir

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def default_pdf_dir() -> Path:
    return _backend_dir() / "pdfs"


def safe_name(path: Path, used: set[str]) -> str:
    """Avoid overwriting different files that share the same filename."""
    name = path.name
    if name not in used:
        used.add(name)
        return name
    stem, suffix = path.stem, path.suffix
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:8]
    candidate = f"{stem}_{digest}{suffix}"
    n = 1
    while candidate in used:
        candidate = f"{stem}_{digest}_{n}{suffix}"
        n += 1
    used.add(candidate)
    return candidate


def collect_pdfs(source: Path) -> list[Path]:
    if not source.exists():
        return []
    if source.is_file() and source.suffix.lower() == ".pdf":
        return [source]
    files = sorted(source.rglob("*.pdf"))
    # Also accept uppercase extension on Windows (rglob is case-insensitive usually)
    return [p for p in files if p.is_file()]


def copy_into_library(pdfs: list[Path], dest: Path) -> dict[str, Any]:
    dest.mkdir(parents=True, exist_ok=True)
    used = {p.name.lower() for p in dest.glob("*.pdf")}
    copied = []
    skipped = []
    for src in pdfs:
        try:
            # Skip if identical content already present
            src_hash = hashlib.sha256(src.read_bytes()).hexdigest()
            already = False
            for existing in dest.glob("*.pdf"):
                try:
                    if hashlib.sha256(existing.read_bytes()).hexdigest() == src_hash:
                        skipped.append({"file": str(src), "reason": f"duplicate of {existing.name}"})
                        already = True
                        break
                except Exception:
                    continue
            if already:
                continue

            name = safe_name(src, used)
            target = dest / name
            # If source is already inside dest, don't recopy
            if src.resolve() == target.resolve():
                skipped.append({"file": str(src), "reason": "already in library"})
                continue
            shutil.copy2(src, target)
            copied.append({"from": str(src), "to": str(target)})
            print(f"[import] + {target.name}")
        except Exception as e:
            skipped.append({"file": str(src), "reason": str(e)})
            print(f"[import] ! failed {src}: {e}")
    return {"copied": copied, "skipped": skipped, "library": str(dest)}


def rebuild_corpus(force: bool = False) -> dict[str, Any]:
    from scraper import run_scraper

    docs = run_scraper(force_arlis=force, force_all=force)
    by_type: dict[str, int] = {}
    for d in docs or []:
        t = d.get("doc_type") or "?"
        by_type[t] = by_type.get(t, 0) + 1
    return {
        "documents": len(docs or []),
        "by_type": by_type,
    }


def import_folder(
    source: str | Path | None = None,
    *,
    copy: bool = True,
    rebuild: bool = True,
    force: bool = False,
) -> dict[str, Any]:
    dest = default_pdf_dir()
    src = Path(source) if source else dest

    result: dict[str, Any] = {
        "source": str(src.resolve()) if src.exists() else str(src),
        "library": str(dest),
        "found": 0,
        "copy": None,
        "rebuild": None,
    }

    pdfs = collect_pdfs(src)
    result["found"] = len(pdfs)
    print(f"[import] Found {len(pdfs)} PDF(s) under {src}")

    if not pdfs and not rebuild:
        result["ok"] = False
        result["error"] = "No PDFs found"
        return result

    if copy and pdfs:
        # If source is the library itself, skip copy
        if src.resolve() == dest.resolve():
            result["copy"] = {"copied": [], "skipped": [{"reason": "source is library folder"}], "library": str(dest)}
            print("[import] Source is backend/pdfs — no copy needed")
        else:
            result["copy"] = copy_into_library(pdfs, dest)
    elif not copy:
        result["copy"] = {"copied": [], "skipped": [], "note": "copy disabled"}

    if rebuild:
        print("[import] Rebuilding full MLSA corpus…")
        result["rebuild"] = rebuild_corpus(force=force)
        print(f"[import] Corpus ready: {result['rebuild']}")

    result["ok"] = True
    result["library_pdf_count"] = len(list(dest.glob("*.pdf")))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bulk import MLSA/ministry PDFs into WISE RAG")
    parser.add_argument(
        "source",
        nargs="?",
        default=None,
        help="Folder (or single PDF) to import. Default: backend/pdfs",
    )
    parser.add_argument("--no-copy", action="store_true", help="Do not copy files into backend/pdfs")
    parser.add_argument("--no-rebuild", action="store_true", help="Only copy files; skip corpus rebuild")
    parser.add_argument("--rebuild-only", action="store_true", help="Only rebuild corpus from existing library")
    parser.add_argument("--force", action="store_true", help="Force re-download ARLIS/PDF catalog")
    args = parser.parse_args(argv)

    if args.rebuild_only:
        print("[import] Rebuild-only mode")
        stats = rebuild_corpus(force=args.force)
        print(stats)
        return 0

    result = import_folder(
        args.source,
        copy=not args.no_copy,
        rebuild=not args.no_rebuild,
        force=args.force,
    )
    print(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())

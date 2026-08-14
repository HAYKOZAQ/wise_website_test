"""
Administration and background re-ingestion router.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from core.security import verify_admin_token
from reingest import get_state as get_reingest_state, run_reingest_async

router = APIRouter(tags=["Admin"], dependencies=[Depends(verify_admin_token)])

BACKEND_DIR = Path(__file__).resolve().parents[1]


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


@router.get("/api/admin/ingest-status")
def ingest_status():
    from rag_engine import rag_engine_instance

    st = get_reingest_state()
    pdf_dir = BACKEND_DIR / "pdfs"
    pdfs = sorted([p.name for p in pdf_dir.glob("*.pdf")]) if pdf_dir.is_dir() else []
    doc_types = dict(getattr(rag_engine_instance, "doc_type_counts", {}) or {}) if rag_engine_instance else {}
    return {
        "reingest": st,
        "library_pdfs": pdfs,
        "library_count": len(pdfs),
        "documents_indexed": rag_engine_instance.document_count if rag_engine_instance else 0,
        "doc_types": doc_types,
        "corpus_hash": getattr(rag_engine_instance, "corpus_hash", None) if rag_engine_instance else None,
    }


@router.post("/api/admin/reingest")
def admin_reingest(payload: ReingestRequest):
    from rag_engine import reload_rag_engine

    out = run_reingest_async(
        force=bool(payload.force),
        import_pdfs_from=payload.import_path,
        reload_callback=reload_rag_engine,
    )
    if not out.get("ok") and not out.get("started"):
        raise HTTPException(status_code=409, detail=out.get("error") or "Could not start re-ingest")
    return out


@router.post("/api/admin/import-pdfs")
def admin_import_pdfs(payload: ImportPdfsRequest):
    from rag_engine import reload_rag_engine

    source = (payload.source or "").strip() or str(BACKEND_DIR / "pdfs")
    lib = str((BACKEND_DIR / "pdfs").resolve())
    try:
        src_resolved = str(Path(source).resolve())
    except Exception:
        src_resolved = source

    st = get_reingest_state()
    if st.get("running"):
        raise HTTPException(status_code=409, detail="Re-ingest already running")

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


@router.post("/api/admin/reload")
def admin_reload():
    from rag_engine import reload_rag_engine

    try:
        return reload_rag_engine()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

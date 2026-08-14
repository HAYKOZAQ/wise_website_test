"""
Health, status, and version endpoints.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Response

router = APIRouter(tags=["Health & Status"])

BACKEND_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_DIR / "frontend"
if not FRONTEND_DIR.is_dir():
    FRONTEND_DIR = BACKEND_DIR.parent / "_site"
if not FRONTEND_DIR.is_dir():
    FRONTEND_DIR = None


def get_status_payload(engine: Any = None) -> Dict[str, Any]:
    dense_on = False
    if engine and hasattr(engine, "vector_enabled"):
        dense_on = bool(engine.vector_enabled)

    return {
        "status": "ready" if engine else "initializing",
        "documents": getattr(engine, "document_count", 0),
        "chunks": len(getattr(engine, "chunks", [])),
        "legal_acts": getattr(engine, "legal_acts", 0),
        "dense_retrieval": dense_on,
        "corpus_hash": getattr(engine, "corpus_hash", ""),
        "vector_backend": getattr(engine, "vector_backend", "none"),
    }


@router.api_route("/api/status", methods=["GET", "HEAD"])
def status_endpoint():
    from rag_engine import rag_engine_instance
    return get_status_payload(rag_engine_instance)


@router.api_route("/healthz", methods=["GET", "HEAD"], include_in_schema=False)
def healthz():
    return {"status": "ok"}


@router.get("/api/version")
def version_endpoint():
    """Returns runtime build metadata and verified asset stamps."""
    payload: Dict[str, Any] = {
        "ok": True,
        "service": "wisef",
        "frontend_root": str(FRONTEND_DIR) if FRONTEND_DIR else None,
        "frontend_mounted": bool(FRONTEND_DIR),
    }
    for cand in (BACKEND_DIR / "version.json", Path("/app/version.json")):
        if cand.is_file():
            try:
                payload.update(json.loads(cand.read_text(encoding="utf-8")))
            except Exception as e:
                payload["version_file_error"] = str(e)
            break

    if FRONTEND_DIR and FRONTEND_DIR.is_dir():
        dark = FRONTEND_DIR / "css" / "dark.css"
        i18n = FRONTEND_DIR / "js" / "i18n.js"
        payload["has_dark_css"] = dark.is_file()
        payload["has_i18n_js"] = i18n.is_file()

    return payload

"""
WISE Foundation — MLSA Welfare RAG API Application Entry Point.
Modular FastAPI architecture with Clean separation of concerns.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.config import settings
from rag_engine import RAGEngine, get_rag_engine, rag_engine_instance
import rag_engine as rag_module
from routers import health_router, chat_router, contact_router, admin_router, eval_router

BACKEND_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BACKEND_DIR / "frontend"
if not FRONTEND_DIR.is_dir():
    FRONTEND_DIR = BACKEND_DIR.parent / "_site"
if not FRONTEND_DIR.is_dir():
    FRONTEND_DIR = None

# Initialize FastAPI application
app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
)


class RenderFriendlyMiddleware(BaseHTTPMiddleware):
    """Normalize HEAD requests and manage deploy-safe cache headers."""

    async def dispatch(self, request: Request, call_next):
        is_head = request.method == "HEAD"
        if is_head:
            request.scope["method"] = "GET"

        response = await call_next(request)
        path = request.url.path or ""

        if path.endswith(".html") or path in ("/", "/pages", "/pages/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
        elif path.startswith(("/css/", "/js/", "/assets/")):
            response.headers.setdefault("Cache-Control", "public, max-age=300, must-revalidate")

        if is_head:
            return Response(status_code=response.status_code, headers=dict(response.headers))
        return response


# Register middlewares
app.add_middleware(RenderFriendlyMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=500)

_cors_origins = settings.resolve_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False if "*" in _cors_origins else True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Ensure RAGEngine initializes on startup."""
    rag_module.rag_engine_instance = get_rag_engine()


# Mount Modular API Routers
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(contact_router)
app.include_router(admin_router)
app.include_router(eval_router)


# Dashboard HTML for standalone API deployments
def _api_dashboard_html() -> str:
    engine = rag_module.rag_engine_instance
    docs = getattr(engine, "document_count", 0) if engine else 0
    chunks = len(getattr(engine, "chunks", [])) if engine else 0
    acts = getattr(engine, "legal_acts", 0) if engine else 0
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WISE AI Backend</title>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 720px; margin: 40px auto; padding: 0 20px; color: #0f172a; line-height: 1.5; }}
    .badge {{ display: inline-block; background: #10b981; color: #fff; padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 16px; margin: 16px 0; }}
    a {{ color: #183960; }}
  </style>
</head>
<body>
  <h1>WISE AI Backend</h1>
  <p><span class="badge">READY</span></p>
  <div class="card">
    <strong>Corpus Status</strong>
    <ul>
      <li>Indexed Documents: {docs}</li>
      <li>Semantic Chunks: {chunks}</li>
      <li>ARLIS Legal Acts: {acts}</li>
    </ul>
  </div>
  <p>Available Endpoints:</p>
  <ul>
    <li><a href="/api/status"><code>GET /api/status</code></a></li>
    <li><code>POST /api/chat</code></li>
    <li><a href="/api/eval/stats"><code>GET /api/eval/stats</code></a></li>
    <li><a href="/docs"><code>Interactive Docs (/docs)</code></a></li>
  </ul>
</body>
</html>"""


@app.get("/api", response_class=HTMLResponse, include_in_schema=False)
@app.get("/api/", response_class=HTMLResponse, include_in_schema=False)
def api_dashboard():
    return HTMLResponse(content=_api_dashboard_html())


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    if FRONTEND_DIR:
        icon = FRONTEND_DIR / "assets" / "logos" / "favicon.svg"
        if icon.is_file():
            return FileResponse(icon, media_type="image/svg+xml")
    return Response(status_code=204)


# Static Site Mounting (Eleventy output)
if FRONTEND_DIR and FRONTEND_DIR.is_dir():
    _css = FRONTEND_DIR / "css"
    _js = FRONTEND_DIR / "js"
    _assets = FRONTEND_DIR / "assets"

    if _css.is_dir():
        app.mount("/css", StaticFiles(directory=str(_css)), name="css")
    if _js.is_dir():
        app.mount("/js", StaticFiles(directory=str(_js)), name="js")
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=str(_assets)), name="assets")

    @app.api_route("/pages", methods=["GET", "HEAD"], include_in_schema=False)
    @app.api_route("/pages/", methods=["GET", "HEAD"], include_in_schema=False)
    def pages_root_compat():
        return RedirectResponse(url="/index.html", status_code=301)

    @app.api_route("/pages/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def pages_compat(path: str):
        target = (path or "index.html").lstrip("/")
        return RedirectResponse(url=f"/{target}", status_code=301)

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="site")
else:
    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    def root_api_only():
        return HTMLResponse(content=_api_dashboard_html())


if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=False)

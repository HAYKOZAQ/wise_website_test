"""
Centralized, typed application configuration with environment loading and validation.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field


def _load_env_files() -> None:
    """Load key-value pairs from available .env files without overwriting existing environment variables."""
    backend_dir = Path(__file__).resolve().parents[1]
    candidates = [
        backend_dir / ".env",
        backend_dir.parent / ".env",
        Path(".env"),
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())
            except Exception:
                pass


_load_env_files()


def _env_bool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, str(default)))
    except (TypeError, ValueError):
        return default


def _env_list(key: str, default: str) -> list[str]:
    raw = os.environ.get(key, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseModel):
    # App Information
    app_title: str = "MLSA Welfare RAG API"
    app_version: str = "2.6"
    app_description: str = "WISE Foundation website + MLSA/ARLIS RAG + scheduled re-ingest"
    
    # Server & Network
    host: str = Field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: _env_int("PORT", 8000))
    cors_origins_raw: str = Field(default_factory=lambda: os.environ.get("CORS_ORIGINS", ""))
    cors_open: bool = Field(default_factory=lambda: _env_bool("WISEF_CORS_OPEN", False))
    pages_origin: str = Field(default_factory=lambda: os.environ.get("WISEF_PAGES_ORIGIN", ""))
    admin_token: str = Field(default_factory=lambda: os.environ.get("ADMIN_TOKEN", ""))

    # Rate Limiting
    chat_rate_limit: int = Field(default_factory=lambda: _env_int("CHAT_RATE_LIMIT", 20))
    chat_rate_window_sec: int = Field(default_factory=lambda: _env_int("CHAT_RATE_WINDOW_SEC", 60))

    # LLM Settings
    gemini_api_key: str = Field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", ""))
    gemini_generate_models: list[str] = Field(
        default_factory=lambda: _env_list("GEMINI_GENERATE_MODELS", "gemini-3.5-flash-lite")
    )
    gemini_max_retries: int = Field(default_factory=lambda: _env_int("GEMINI_MAX_RETRIES", 1))
    gemini_deadline_sec: float = Field(default_factory=lambda: _env_float("GEMINI_DEADLINE_SEC", 45.0))
    gemini_timeout_sec: float = Field(default_factory=lambda: _env_float("GEMINI_TIMEOUT_SEC", 40.0))

    ollama_host: str = Field(default_factory=lambda: os.environ.get("OLLAMA_HOST", "http://localhost:11434"))
    ollama_model: str = Field(default_factory=lambda: os.environ.get("OLLAMA_MODEL", "gemma2"))

    # Retrieval & Indexing
    use_local_embedder: bool = Field(default_factory=lambda: _env_bool("USE_LOCAL_EMBEDDER", True))
    use_reranker: bool = Field(default_factory=lambda: _env_bool("USE_RERANKER", False))
    use_local_tfidf: bool = Field(default_factory=lambda: _env_bool("USE_LOCAL_TFIDF", True))
    hybrid_semantic_weight: float = Field(default_factory=lambda: _env_float("HYBRID_SEMANTIC_WEIGHT", 0.6))
    query_expansion: bool = Field(default_factory=lambda: _env_bool("QUERY_EXPANSION", False))
    force_embed: bool = Field(default_factory=lambda: _env_bool("FORCE_EMBED", False))
    auto_embed_max_chunks: int = Field(default_factory=lambda: _env_int("AUTO_EMBED_MAX_CHUNKS", 400))

    # SMTP Configuration
    smtp_host: str = Field(default_factory=lambda: os.environ.get("SMTP_HOST", ""))
    smtp_port: int = Field(default_factory=lambda: _env_int("SMTP_PORT", 587))
    smtp_user: str = Field(default_factory=lambda: os.environ.get("SMTP_USER", ""))
    smtp_password: str = Field(default_factory=lambda: os.environ.get("SMTP_PASSWORD", ""))
    smtp_from: str = Field(default_factory=lambda: os.environ.get("SMTP_FROM", ""))
    contact_to_email: str = Field(default_factory=lambda: os.environ.get("CONTACT_TO_EMAIL", "info@wisef.am"))
    smtp_use_tls: bool = Field(default_factory=lambda: _env_bool("SMTP_USE_TLS", True))
    contact_webhook_url: str = Field(default_factory=lambda: os.environ.get("CONTACT_WEBHOOK_URL", ""))

    def resolve_cors_origins(self) -> list[str]:
        if self.cors_origins_raw.strip():
            raw_list = [o.strip().rstrip("/") for o in self.cors_origins_raw.split(",") if o.strip()]
            return [o for o in raw_list if o] or ["*"]
        if self.cors_open:
            return ["*"]
        origins = [
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
            "https://wise-website-test.onrender.com",
            "http://wise-website-test.onrender.com",
        ]
        if self.pages_origin.strip():
            cleaned = self.pages_origin.strip().rstrip("/")
            if cleaned and cleaned not in origins:
                origins.append(cleaned)
        return origins


settings = Settings()

"""
Shared utilities for WISE data-ingestion scripts.

This module consolidates duplicated boilerplate across arlis_ingest, mlsa_web_ingest,
pdf_ingest, harvest_all_pdfs, bulk_import_pdfs, and scraper. It is intentionally
dependency-light (only stdlib + requests/bs4) so it can be imported by all scripts.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


def ensure_utf8_stdout() -> None:
    """Reconfigure stdout to UTF-8 on Windows so Armenian prints correctly."""
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def backend_dir() -> Path:
    return Path(__file__).resolve().parent


def data_dir() -> Path:
    d = backend_dir() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def subdir(name: str) -> Path:
    d = data_dir() / name
    d.mkdir(parents=True, exist_ok=True)
    return d


def corpus_dir() -> Path:
    return subdir("corpus")


def default_headers(accept: str | None = None) -> dict[str, str]:
    h = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "hy,en;q=0.8",
    }
    if accept:
        h["Accept"] = accept
    return h


def http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 30,
    retries: int = 3,
    backoff: float = 2.0,
    session: requests.Session | None = None,
    fix_encoding: bool = True,
) -> requests.Response | None:
    """Robust GET with retries, exponential backoff, and Armenian encoding fix."""
    h = {**(headers or default_headers())}
    client = session or requests
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            r = client.get(url, headers=h, timeout=timeout, allow_redirects=True)
            if r.status_code == 200:
                if fix_encoding:
                    r.encoding = r.apparent_encoding or r.encoding or "utf-8"
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                wait = backoff * (2 ** (attempt - 1))
                retry_after = r.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = max(wait, int(retry_after))
                print(f"[http] {r.status_code} for {url[:80]} — retry {attempt}/{retries} after {wait:.1f}s")
                time.sleep(wait)
                continue
            print(f"[http] {r.status_code} for {url[:80]}")
            return r
        except Exception as e:
            last_error = e
            wait = backoff * (2 ** (attempt - 1))
            print(f"[http] error {url[:80]}: {e} — retry {attempt}/{retries} after {wait:.1f}s")
            time.sleep(wait)
    if last_error:
        print(f"[http] failed after {retries} attempts: {last_error}")
    return None


def load_json(path: str | Path, default: Any = None) -> Any:
    p = Path(path)
    if not p.exists():
        return default
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[json] failed reading {p}: {e}")
        return default


def save_json(path: str | Path, data: Any, indent: int | None = 2) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)


def atomic_write_json(path: str | Path, data: Any, indent: int | None = 2) -> None:
    """Write JSON atomically so crashes don't leave a truncated file."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        os.replace(tmp, p)
    except Exception:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        raise


def armenian_tokenize(text: str, min_len: int = 2) -> list[str]:
    """Tokenizer shared across BM25, TF–IDF, and keyword fallback paths."""
    text = (text or "").lower()
    return [t for t in re.findall(r"[\w\u0531-\u0587]+", text, flags=re.UNICODE) if len(t) > min_len]


def hard_split(text: str, max_chars: int = 1400, overlap: int = 120) -> list[str]:
    """Split long text into overlapping chunks at paragraph/sentence boundaries."""
    text = text or ""
    if len(text) <= max_chars:
        return [text] if text.strip() else []
    chunks: list[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            window = text[start:end]
            br = max(window.rfind("\n\n"), window.rfind("\n"), window.rfind(". "))
            if br > max_chars // 3:
                end = start + br + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= n:
            break
        start = max(0, end - overlap)
    return chunks


def normalize_text(text: str, drop_lines: tuple[str, ...] | None = None) -> str:
    """Basic whitespace cleanup plus optional chrome-line removal."""
    text = (text or "").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    if drop_lines:
        cleaned = []
        for line in text.splitlines():
            low = line.strip().lower()
            if any(d in low for d in drop_lines) and len(line.strip()) < 80:
                continue
            cleaned.append(line.rstrip())
        text = "\n".join(cleaned)
    return text.strip()


def slug(s: str, max_len: int = 80) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return (s[:max_len] or "doc").strip("_")


def safe_canonical_act_id(act_id: Any) -> str | None:
    """Return a stable 4+ digit identifier from ARLIS/pdf/web act ids.

    Handles variants like 64540, "arlis-64540", "pdf:arlis-64540".
    """
    if not act_id:
        return None
    s = str(act_id)
    m = re.search(r"(\d{4,})", s)
    return m.group(1) if m else None


def dedupe_content_key(text: str, url: str | None = None, max_len: int = 800) -> str:
    """Return a short hash for cross-source content deduplication."""
    content = (text or "")[:max_len].strip()
    if url:
        content = f"{url}\n{content}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def cache_key(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]


class TextCache:
    """Generic JSONL-ish cache for extracted text keyed by an id/hash."""

    def __init__(self, cache_dir: str | Path, min_chars: int = 120):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.min_chars = min_chars

    def _path(self, key: str) -> Path:
        return self.dir / f"{key}.json"

    def load(self, key: str) -> str | None:
        data = load_json(self._path(key))
        if not isinstance(data, dict):
            return None
        text = data.get("text") or ""
        return text if len(text) >= self.min_chars else None

    def save(self, key: str, text: str, meta: dict[str, Any] | None = None) -> None:
        save_json(
            self._path(key),
            {
                "meta": meta or {},
                "text": text,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "char_count": len(text),
            },
        )


__all__ = [
    "ensure_utf8_stdout",
    "backend_dir",
    "data_dir",
    "subdir",
    "corpus_dir",
    "default_headers",
    "http_get",
    "load_json",
    "save_json",
    "atomic_write_json",
    "armenian_tokenize",
    "hard_split",
    "normalize_text",
    "slug",
    "safe_canonical_act_id",
    "dedupe_content_key",
    "cache_key",
    "TextCache",
]

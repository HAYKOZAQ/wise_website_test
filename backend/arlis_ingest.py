"""
ARLIS legal act ingestion for MLSA social programs.
Fetches official acts from arlis.am (HTML preferred, PDF fallback),
chunks by legal articles, and returns structured documents for the RAG index.
"""

from __future__ import annotations

import os
import re
import sys
from io import BytesIO
from typing import Any

from bs4 import BeautifulSoup

from ingest_common import (
    TextCache,
    backend_dir,
    corpus_dir,
    data_dir,
    default_headers,
    hard_split,
    http_get,
    load_json,
    normalize_text,
    save_json,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore

ARTICLE_SPLIT_RE = re.compile(
    r"(?=(?:^|\n)\s*(?:Հոդված|HOՎԱԾ|Article)\s+\d+)",
    re.IGNORECASE | re.MULTILINE,
)
ARTICLE_HEAD_RE = re.compile(
    r"^\s*((?:Հոդված|Article)\s+\d+[^\n]*)",
    re.IGNORECASE | re.MULTILINE,
)

_arlis_drop_lines = (
    "պաշտոնական ինկորպորացիա",
    "arlis",
    "հայաստանի իրավական տեղեկատվական համակարգ",
)

_arlis_cache = TextCache(corpus_dir(), min_chars=200)


def load_catalog(catalog_path: str | None = None) -> list[dict[str, Any]]:
    candidates = []
    if catalog_path:
        candidates.append(Path(catalog_path))
    candidates.extend([
        backend_dir() / "arlis_catalog.json",
        data_dir() / "arlis_catalog.json",
    ])
    path = next((p for p in candidates if p.exists()), None)
    if not path:
        print("[arlis] Catalog not found (backend/arlis_catalog.json)")
        return []
    return load_json(path, default=[])


def _normalize_arlis_text(text: str) -> str:
    return normalize_text(text, drop_lines=_arlis_drop_lines)


def fetch_html_text(arlis_url: str, timeout: int = 45) -> str | None:
    r = http_get(arlis_url, timeout=timeout)
    if r is None:
        return None
    if r.status_code != 200:
        print(f"[arlis] HTML {r.status_code} for {arlis_url}")
        return None
    soup = BeautifulSoup(r.text, "lxml")
    body = (
        soup.select_one("#act_body")
        or soup.select_one(".act-content__wrapper")
        or soup.select_one(".act-content")
        or soup.select_one("main")
    )
    if not body:
        return None
    text = body.get_text("\n", strip=True)
    text = _normalize_arlis_text(text)
    return text if len(text) > 200 else None


def fetch_pdf_text(download_url: str, timeout: int = 60) -> str | None:
    if PdfReader is None:
        print("[arlis] pypdf not installed; skip PDF extract")
        return None
    r = http_get(download_url, timeout=timeout, fix_encoding=False)
    if r is None:
        return None
    if r.status_code != 200:
        print(f"[arlis] PDF {r.status_code} for {download_url}")
        return None
    ctype = (r.headers.get("content-type") or "").lower()
    if "pdf" not in ctype and not r.content.startswith(b"%PDF"):
        print(f"[arlis] Not a PDF at {download_url} ({ctype})")
        return None
    reader = PdfReader(BytesIO(r.content))
    parts = []
    for page in reader.pages:
        t = page.extract_text() or ""
        if t.strip():
            parts.append(t)
    text = _normalize_arlis_text("\n".join(parts))
    return text if len(text) > 200 else None


def split_into_articles(text: str) -> list[tuple[str, str]]:
    """Return list of (article_label, article_body)."""
    if not text:
        return []

    parts = ARTICLE_SPLIT_RE.split(text)
    articles: list[tuple[str, str]] = []

    for part in parts:
        part = part.strip()
        if len(part) < 40:
            continue
        m = ARTICLE_HEAD_RE.match(part)
        if m:
            label = re.sub(r"\s+", " ", m.group(1)).strip()
            body = part[m.end() :].strip()
            full = f"{label}\n{body}".strip() if body else label
            articles.append((label, full))
        else:
            # preamble / non-article block
            articles.append(("Ներածություն / preamble", part))

    if not articles:
        articles.append(("Ամբողջ ակտ", text))
    return articles


def act_to_documents(entry: dict[str, Any], full_text: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    act_id = str(entry.get("act_id", ""))
    title = entry.get("title_hy") or entry.get("title_en") or f"ARLIS {act_id}"
    category = entry.get("category") or "general"
    program_keys = entry.get("program_keys") or []
    source_url = entry.get("arlis_url") or f"https://www.arlis.am/hy/acts/{act_id}"

    for label, body in split_into_articles(full_text):
        for i, piece in enumerate(hard_split(body, max_chars=1100, overlap=120)):
            piece_title = title if label.startswith("Ներած") else f"{title} — {label}"
            if i > 0:
                piece_title = f"{piece_title} (մաս {i + 1})"
            docs.append(
                {
                    "title": piece_title,
                    "content": piece,
                    "doc_type": "legal",
                    "act_id": act_id,
                    "article": label,
                    "category": category,
                    "program_keys": program_keys,
                    "source_url": source_url,
                    "priority": entry.get("priority", 2),
                }
            )
    return docs


def ingest_act(entry: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    act_id = str(entry.get("act_id", "")).strip()
    if not act_id:
        return []

    text = None if force else _arlis_cache.load(act_id)
    if text:
        print(f"[arlis] Cache hit act {act_id} ({len(text)} chars)")
    else:
        arlis_url = entry.get("arlis_url") or f"https://www.arlis.am/hy/acts/{act_id}"
        download_url = entry.get("download_url") or f"{arlis_url}/download/act"
        print(f"[arlis] Fetching act {act_id} …")
        text = fetch_html_text(arlis_url)
        if not text:
            print(f"[arlis] Falling back to PDF for {act_id}")
            text = fetch_pdf_text(download_url)
        if not text:
            print(f"[arlis] FAILED to extract act {act_id}")
            return []
        _arlis_cache.save(act_id, text, entry)
        print(f"[arlis] Saved act {act_id} ({len(text)} chars)")

    docs = act_to_documents(entry, text)
    print(f"[arlis] Act {act_id} → {len(docs)} legal chunks")
    return docs


def ingest_all(force: bool = False, catalog_path: str | None = None) -> list[dict[str, Any]]:
    catalog = load_catalog(catalog_path)
    if not catalog:
        return []

    # Prefer higher-priority acts first; stable order
    catalog = sorted(catalog, key=lambda e: (e.get("priority", 9), str(e.get("act_id"))))
    all_docs: list[dict[str, Any]] = []
    for entry in catalog:
        try:
            all_docs.extend(ingest_act(entry, force=force))
        except Exception as e:
            print(f"[arlis] Error on act {entry.get('act_id')}: {e}")
    print(f"[arlis] Total legal documents: {len(all_docs)}")
    return all_docs


if __name__ == "__main__":
    force = "--force" in sys.argv
    docs = ingest_all(force=force)
    out = data_dir() / "arlis_legal_docs.json"
    save_json(out, docs)
    print(f"[arlis] Wrote {len(docs)} docs to {out}")

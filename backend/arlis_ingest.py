"""
ARLIS legal act ingestion for MLSA social programs.
Fetches official acts from arlis.am (HTML preferred, PDF fallback),
chunks by legal articles, and returns structured documents for the RAG index.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from io import BytesIO
from typing import Any

import requests
from bs4 import BeautifulSoup

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None  # type: ignore

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "hy,en;q=0.8",
}

ARTICLE_SPLIT_RE = re.compile(
    r"(?=(?:^|\n)\s*(?:Հոդված|HOՎԱԾ|Article)\s+\d+)",
    re.IGNORECASE | re.MULTILINE,
)
ARTICLE_HEAD_RE = re.compile(
    r"^\s*((?:Հոդված|Article)\s+\d+[^\n]*)",
    re.IGNORECASE | re.MULTILINE,
)


def backend_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def data_dir() -> str:
    path = os.path.join(backend_dir(), "data")
    os.makedirs(path, exist_ok=True)
    return path


def corpus_dir() -> str:
    path = os.path.join(data_dir(), "corpus")
    os.makedirs(path, exist_ok=True)
    return path


def load_catalog(catalog_path: str | None = None) -> list[dict[str, Any]]:
    candidates = []
    if catalog_path:
        candidates.append(catalog_path)
    candidates.extend([
        os.path.join(backend_dir(), "arlis_catalog.json"),
        os.path.join(data_dir(), "arlis_catalog.json"),
    ])
    path = next((p for p in candidates if os.path.exists(p)), None)
    if not path:
        print("[arlis] Catalog not found (backend/arlis_catalog.json)")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Drop common ARLIS chrome phrases
    drop_lines = (
        "պաշտոնական ինկորպորացիա",
        "arlis",
        "հայաստանի իրավական տեղեկատվական համակարգ",
    )
    cleaned = []
    for line in text.splitlines():
        low = line.strip().lower()
        if any(d in low for d in drop_lines) and len(line.strip()) < 80:
            continue
        cleaned.append(line.rstrip())
    return "\n".join(cleaned).strip()


def fetch_html_text(arlis_url: str, timeout: int = 45) -> str | None:
    try:
        r = requests.get(arlis_url, headers=HEADERS, timeout=timeout)
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
        text = normalize_text(text)
        return text if len(text) > 200 else None
    except Exception as e:
        print(f"[arlis] HTML fetch error {arlis_url}: {e}")
        return None


def fetch_pdf_text(download_url: str, timeout: int = 60) -> str | None:
    if PdfReader is None:
        print("[arlis] pypdf not installed; skip PDF extract")
        return None
    try:
        r = requests.get(download_url, headers=HEADERS, timeout=timeout)
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
        text = normalize_text("\n".join(parts))
        return text if len(text) > 200 else None
    except Exception as e:
        print(f"[arlis] PDF extract error {download_url}: {e}")
        return None


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


def hard_split(text: str, max_chars: int = 1100, overlap: int = 120) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        if end < n:
            # prefer break at paragraph/sentence
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


def act_to_documents(entry: dict[str, Any], full_text: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    act_id = str(entry.get("act_id", ""))
    title = entry.get("title_hy") or entry.get("title_en") or f"ARLIS {act_id}"
    category = entry.get("category") or "general"
    program_keys = entry.get("program_keys") or []
    source_url = entry.get("arlis_url") or f"https://www.arlis.am/hy/acts/{act_id}"

    for label, body in split_into_articles(full_text):
        for i, piece in enumerate(hard_split(body)):
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


def save_raw_act(act_id: str, text: str, meta: dict[str, Any]) -> None:
    path = os.path.join(corpus_dir(), f"{act_id}.json")
    payload = {
        "act_id": act_id,
        "meta": meta,
        "text": text,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "char_count": len(text),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def load_cached_act(act_id: str) -> str | None:
    path = os.path.join(corpus_dir(), f"{act_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("text") or ""
        return text if len(text) > 200 else None
    except Exception:
        return None


def ingest_act(entry: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    act_id = str(entry.get("act_id", "")).strip()
    if not act_id:
        return []

    text = None if force else load_cached_act(act_id)
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
        save_raw_act(act_id, text, entry)
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
    out = os.path.join(data_dir(), "arlis_legal_docs.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print(f"[arlis] Wrote {len(docs)} docs to {out}")

"""
Ingest MLSA / USS / ARLIS program PDFs into the RAG corpus.

Sources (in order):
  1. Local drop folders: backend/pdfs/, backend/data/pdfs/
  2. Catalog URLs in backend/mlsa_pdf_catalog.json
  3. Optional force re-download with --force

Each PDF is cached under data/pdf_cache/ and chunked into doc_type="pdf".
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

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
    "Accept": "application/pdf,*/*",
    "Accept-Language": "hy,en;q=0.8",
}


def backend_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def data_dir() -> str:
    path = os.path.join(backend_dir(), "data")
    os.makedirs(path, exist_ok=True)
    return path


def pdf_cache_dir() -> str:
    path = os.path.join(data_dir(), "pdf_cache")
    os.makedirs(path, exist_ok=True)
    return path


def local_pdf_dirs() -> list[str]:
    candidates = [
        os.path.join(backend_dir(), "pdfs"),
        os.path.join(data_dir(), "pdfs"),
        os.path.join(backend_dir(), "seed", "pdfs"),
    ]
    return [p for p in candidates if os.path.isdir(p)]


def load_catalog(catalog_path: str | None = None) -> list[dict[str, Any]]:
    paths = []
    if catalog_path:
        paths.append(catalog_path)
    paths.extend(
        [
            os.path.join(backend_dir(), "mlsa_pdf_catalog.json"),
            os.path.join(data_dir(), "mlsa_pdf_catalog.json"),
        ]
    )
    path = next((p for p in paths if os.path.exists(p)), None)
    if not path:
        print("[pdf] Catalog not found (backend/mlsa_pdf_catalog.json)")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    text = (text or "").replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf_bytes(content: bytes) -> str | None:
    if PdfReader is None:
        print("[pdf] pypdf not installed")
        return None
    try:
        if not content.startswith(b"%PDF") and b"%PDF" not in content[:1024]:
            # May still be PDF served with wrong header
            if not content[:8].startswith(b"%PDF") and b"PDF" not in content[:200]:
                return None
        reader = PdfReader(BytesIO(content))
        parts: list[str] = []
        for page in reader.pages:
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
        text = normalize_text("\n".join(parts))
        return text if len(text) > 120 else None
    except Exception as e:
        print(f"[pdf] extract error: {e}")
        return None


def hard_split(text: str, max_chars: int = 1400, overlap: int = 150) -> list[str]:
    if len(text) <= max_chars:
        return [text]
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


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "_", s, flags=re.UNICODE)
    return s[:80] or "doc"


def cache_key(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:20]


def load_cached_text(key: str) -> str | None:
    path = os.path.join(pdf_cache_dir(), f"{key}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        text = data.get("text") or ""
        return text if len(text) > 120 else None
    except Exception:
        return None


def save_cached_text(key: str, text: str, meta: dict[str, Any]) -> None:
    path = os.path.join(pdf_cache_dir(), f"{key}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "meta": meta,
                "text": text,
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "char_count": len(text),
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def download_pdf(url: str, timeout: int = 90) -> bytes | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code != 200:
            print(f"[pdf] HTTP {r.status_code} for {url[:90]}")
            return None
        content = r.content
        if len(content) < 500:
            print(f"[pdf] Too small response for {url[:90]}")
            return None
        return content
    except Exception as e:
        print(f"[pdf] download error {url[:90]}: {e}")
        return None


def text_to_docs(
    text: str,
    *,
    title: str,
    category: str,
    program_keys: list[str],
    source_url: str | None,
    doc_id: str,
    priority: int = 2,
) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    pieces = hard_split(text)
    for i, piece in enumerate(pieces):
        piece_title = title if i == 0 else f"{title} (մաս {i + 1})"
        docs.append(
            {
                "title": piece_title,
                "content": piece,
                "doc_type": "pdf",
                "act_id": f"pdf:{doc_id}",
                "article": f"PDF part {i + 1}/{len(pieces)}",
                "category": category or "general",
                "program_keys": program_keys or [],
                "source_url": source_url,
                "priority": priority,
            }
        )
    return docs


def load_exclude_set() -> dict[str, str]:
    """filename(lower) -> reason"""
    path = os.path.join(backend_dir(), "pdf_exclude.json")
    out: dict[str, str] = {}
    if not os.path.exists(path):
        return out
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data.get("excluded") or []:
            name = (item.get("file") or "").strip().lower()
            if name:
                out[name] = item.get("reason") or "excluded"
    except Exception as e:
        print(f"[pdf] exclude list error: {e}")
    return out


def record_exclude(name: str, reason: str) -> None:
    """Append runtime exclude entry to data/pdf_excluded_runtime.json."""
    path = os.path.join(data_dir(), "pdf_excluded_runtime.json")
    rows = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                rows = json.load(f) or []
        except Exception:
            rows = []
    key = name.lower()
    if any((r.get("file") or "").lower() == key for r in rows):
        return
    rows.append({"file": name, "reason": reason})
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def try_ocr_pdf(path: str) -> str | None:
    """Optional OCR if pytesseract + pdf2image + system deps exist."""
    try:
        import pytesseract  # type: ignore
        from pdf2image import convert_from_path  # type: ignore
    except ImportError:
        return None
    try:
        images = convert_from_path(path, dpi=200, first_page=1, last_page=3)
        parts = []
        for img in images:
            # Armenian + English if available; fallback eng
            try:
                t = pytesseract.image_to_string(img, lang="hye+eng")
            except Exception:
                t = pytesseract.image_to_string(img, lang="eng")
            if t and t.strip():
                parts.append(t)
        text = normalize_text("\n".join(parts))
        return text if len(text) > 120 else None
    except Exception as e:
        print(f"[pdf] OCR failed for {path}: {e}")
        return None


def ingest_local_pdfs() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    excluded = load_exclude_set()
    for folder in local_pdf_dirs():
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(".pdf"):
                continue
            if name.lower() in excluded:
                print(f"[pdf] EXCLUDED {name}: {excluded[name.lower()]}")
                record_exclude(name, excluded[name.lower()])
                continue
            path = os.path.join(folder, name)
            key = cache_key(f"local:{path}:{os.path.getmtime(path)}")
            text = load_cached_text(key)
            if not text:
                try:
                    with open(path, "rb") as f:
                        raw = f.read()
                except Exception as e:
                    print(f"[pdf] Cannot read {path}: {e}")
                    continue
                text = extract_pdf_bytes(raw)
                if not text:
                    ocr = try_ocr_pdf(path)
                    if ocr:
                        text = ocr
                        print(f"[pdf] OCR ok {name} → {len(text)} chars")
                    else:
                        reason = "no extractable text (scanned/image-only; OCR unavailable or failed)"
                        print(f"[pdf] No text from local {name} — excluding")
                        record_exclude(name, reason)
                        continue
                save_cached_text(
                    key,
                    text,
                    {"path": path, "name": name, "source": "local"},
                )
                print(f"[pdf] Local {name} → {len(text)} chars")
            title = Path(name).stem.replace("_", " ").replace("-", " ")
            docs.extend(
                text_to_docs(
                    text,
                    title=f"MLSA PDF — {title}",
                    category="general",
                    program_keys=[],
                    source_url=f"file://{name}",
                    doc_id=_slug(name),
                    priority=1,
                )
            )
    print(f"[pdf] Local PDF docs: {len(docs)}")
    return docs


def ingest_catalog_entry(entry: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    url = (entry.get("url") or "").strip()
    doc_id = str(entry.get("id") or cache_key(url))
    if not url:
        return []

    excluded = load_exclude_set()
    # Match exclude by id.pdf or local library twin
    for key_name in (f"{doc_id}.pdf".lower(), f"{doc_id.lower()}.pdf"):
        if key_name in excluded:
            print(f"[pdf] EXCLUDED catalog {doc_id}: {excluded[key_name]}")
            record_exclude(key_name, excluded[key_name])
            return []

    key = cache_key(url)
    text = None if force else load_cached_text(key)
    if not text:
        print(f"[pdf] Fetching {doc_id} …")
        raw = download_pdf(url)
        if not raw:
            return []
        text = extract_pdf_bytes(raw)
        if not text:
            # Some social.gov.am assets are HTML/binary not pure PDF
            try:
                decoded = raw.decode("utf-8", errors="ignore")
                if len(decoded) > 300 and ("ՀՀ" in decoded or "նպաստ" in decoded or "կենսաթոշակ" in decoded):
                    text = normalize_text(re.sub(r"<[^>]+>", "\n", decoded))
            except Exception:
                pass
        if not text or len(text) < 120:
            reason = f"FAILED extract {doc_id}"
            print(f"[pdf] {reason}")
            record_exclude(f"{doc_id}.pdf", reason)
            return []
        save_cached_text(key, text, entry)
        print(f"[pdf] Saved {doc_id} ({len(text)} chars)")
    else:
        print(f"[pdf] Cache hit {doc_id} ({len(text)} chars)")

    title = entry.get("title_hy") or entry.get("title_en") or doc_id
    return text_to_docs(
        text,
        title=title,
        category=entry.get("category") or "general",
        program_keys=entry.get("program_keys") or [],
        source_url=url,
        doc_id=doc_id,
        priority=int(entry.get("priority") or 2),
    )


def ingest_all(force: bool = False, catalog_path: str | None = None) -> list[dict[str, Any]]:
    all_docs: list[dict[str, Any]] = []
    all_docs.extend(ingest_local_pdfs())

    catalog = load_catalog(catalog_path)
    catalog = sorted(catalog, key=lambda e: (e.get("priority", 9), str(e.get("id", ""))))
    for entry in catalog:
        try:
            all_docs.extend(ingest_catalog_entry(entry, force=force))
        except Exception as e:
            print(f"[pdf] Error on {entry.get('id')}: {e}")

    print(f"[pdf] Total PDF documents: {len(all_docs)}")
    return all_docs


if __name__ == "__main__":
    force = "--force" in sys.argv
    docs = ingest_all(force=force)
    out = os.path.join(data_dir(), "mlsa_pdf_docs.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)
    print(f"[pdf] Wrote {len(docs)} docs → {out}")

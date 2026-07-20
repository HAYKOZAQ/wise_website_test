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
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ingest_common import (
    TextCache,
    backend_dir,
    cache_key,
    data_dir,
    default_headers,
    hard_split,
    http_get,
    load_json,
    normalize_text,
    save_json,
    slug,
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


def pdf_cache_dir() -> str:
    path = data_dir() / "pdf_cache"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


_pdf_cache = TextCache(pdf_cache_dir(), min_chars=120)


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
            backend_dir() / "mlsa_pdf_catalog.json",
            data_dir() / "mlsa_pdf_catalog.json",
        ]
    )
    path = next((p for p in paths if p.exists()), None)
    if not path:
        print("[pdf] Catalog not found (backend/mlsa_pdf_catalog.json)")
        return []
    return load_json(path, default=[])


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


def download_pdf(url: str, timeout: int = 90) -> bytes | None:
    r = http_get(
        url,
        headers=default_headers("application/pdf,*/*"),
        timeout=timeout,
        fix_encoding=False,
    )
    if r is None:
        return None
    if r.status_code != 200:
        print(f"[pdf] HTTP {r.status_code} for {url[:90]}")
        return None
    content = r.content
    if len(content) < 500:
        print(f"[pdf] Too small response for {url[:90]}")
        return None
    return content


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
    pieces = hard_split(text, max_chars=1400, overlap=150)
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
    path = backend_dir() / "pdf_exclude.json"
    out: dict[str, str] = {}
    if not path.exists():
        return out
    data = load_json(path, default={})
    for item in data.get("excluded") or []:
        name = (item.get("file") or "").strip().lower()
        if name:
            out[name] = item.get("reason") or "excluded"
    return out


def record_exclude(name: str, reason: str) -> None:
    """Append runtime exclude entry to data/pdf_excluded_runtime.json."""
    path = data_dir() / "pdf_excluded_runtime.json"
    rows = load_json(path, default=[])
    key = name.lower()
    if any((r.get("file") or "").lower() == key for r in rows):
        return
    rows.append({"file": name, "reason": reason})
    save_json(path, rows)


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
            text = _pdf_cache.load(key)
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
                _pdf_cache.save(
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
                    doc_id=slug(name),
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
    text = None if force else _pdf_cache.load(key)
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
        _pdf_cache.save(key, text, entry)
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
    out = data_dir() / "mlsa_pdf_docs.json"
    save_json(out, docs)
    print(f"[pdf] Wrote {len(docs)} docs → {out}")

"""One-shot: download catalog PDFs into backend/pdfs/ for bulk library."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BACKEND = Path(__file__).resolve().parent
PDFS = BACKEND / "pdfs"
PDFS.mkdir(exist_ok=True)
CATALOG = json.loads((BACKEND / "mlsa_pdf_catalog.json").read_text(encoding="utf-8"))
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0",
    "Accept": "application/pdf,*/*",
}

saved = 0
skipped = 0
failed = 0
for entry in CATALOG:
    eid = str(entry.get("id") or "doc")
    url = (entry.get("url") or "").strip()
    out = PDFS / f"{eid}.pdf"
    if out.exists() and out.stat().st_size > 2000:
        print(f"skip {out.name}")
        skipped += 1
        continue
    if not url:
        failed += 1
        continue
    try:
        print(f"GET {eid} …")
        r = requests.get(url, headers=HEADERS, timeout=90, allow_redirects=True)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            failed += 1
            continue
        raw = r.content
        if not (raw.startswith(b"%PDF") or b"%PDF" in raw[:1024]):
            print(f"  not a PDF ({len(raw)} bytes)")
            failed += 1
            continue
        out.write_bytes(raw)
        print(f"  saved {out.name} ({len(raw)} bytes)")
        saved += 1
    except Exception as e:
        print(f"  error: {e}")
        failed += 1

print(f"DONE saved={saved} skipped={skipped} failed={failed} total_pdfs={len(list(PDFS.glob('*.pdf')))}")

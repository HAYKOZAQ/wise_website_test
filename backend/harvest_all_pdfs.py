"""
Harvest all reachable MLSA / USS / ARLIS program PDFs into backend/pdfs/,
then optionally rebuild the RAG corpus.

Sources:
  1) backend/arlis_catalog.json  → every act download_url
  2) backend/mlsa_pdf_catalog.json
  3) EXTRA_ARLIS_ACTS (hardcoded high-value act ids)
  4) Crawl social.gov.am / uss.social.gov.am pages for /api/assets/ and .pdf links
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from ingest_common import backend_dir, load_json, save_json, slug

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BACKEND = backend_dir()
PDFS = BACKEND / "pdfs"
PDFS.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,text/html,*/*",
    "Accept-Language": "hy,en;q=0.8",
}

# Extra ARLIS acts commonly tied to social programs (beyond arlis_catalog.json)
EXTRA_ARLIS_ACTS: list[dict[str, Any]] = [
    {"act_id": "183639", "title": "Պետական կենսաթոշակների մասին — կիրառում", "category": "pensions"},
    {"act_id": "147840", "title": "Պետական կենսաթոշակների մասին — փոփոխություններ", "category": "pensions"},
    {"act_id": "92207", "title": "Պետական կենսաթոշակների մասին — հաշմանդամություն", "category": "pensions"},
    {"act_id": "187129", "title": "Պետական նպաստների մասին — լրացումներ", "category": "allowances"},
    {"act_id": "152960", "title": "Հաշմանդամություն ունեցող անձանց իրավունքներ", "category": "services"},
    {"act_id": "199715", "title": "Զբաղվածության մասին օրենք (նոր)", "category": "employment"},
    {"act_id": "138920", "title": "Զբաղվածության մասին օրենք", "category": "employment"},
    {"act_id": "34317", "title": "Հաշմանդամություն / կենսաթոշակ կիրառում", "category": "pensions"},
    {"act_id": "109076", "title": "Պետական կենսաթոշակների մասին — կառավարության որոշում", "category": "pensions"},
    {"act_id": "73884", "title": "Հաշմանդամության կենսաթոշակների չափեր", "category": "pensions"},
    {"act_id": "170541", "title": "Խնամքի նպաստի դրույթներ", "category": "allowances"},
    {"act_id": "221323", "title": "Մինչև 2 տարեկան խնամքի նպաստ նոր կարգ", "category": "allowances"},
    {"act_id": "199679", "title": "Նպաստների օրենքի փոփոխություններ 2024", "category": "allowances"},
    {"act_id": "223036", "title": "Անապահովության գնահատում", "category": "allowances"},
    {"act_id": "31548", "title": "Կենսաթոշակների մասին օրենքի կիրառում", "category": "pensions"},
    {"act_id": "194144", "title": "Կենսաթոշակային հաշվի միջոցներ", "category": "pensions"},
    {"act_id": "28191", "title": "Զինծառայողների սոցիալական ապահովություն բազային", "category": "services"},
    {"act_id": "178327", "title": "Հաշմանդամություն ունեցող անձանց սոցիալական աջակցություն", "category": "services"},
    {"act_id": "149174", "title": "Վերականգնողական օգնություն և պրոթեզավորում", "category": "services"},
    {"act_id": "100867", "title": "Տարեցների և հաշմանդամների սոցիալական սպասարկում", "category": "services"},
    {"act_id": "99943", "title": "Սահմանամերձ համայնքների սոցիալական աջակցություն", "category": "allowances"},
    {"act_id": "97201", "title": "Զբաղվածության մասին օրենքի կիրառող ակտեր", "category": "employment"},
    {"act_id": "194668", "title": "Աջակցող միջոցներ", "category": "services"},
    {"act_id": "183771", "title": "Էլեկտրաէներգիայի փոխհատուցում", "category": "contacts"},
    {"act_id": "186338", "title": "Զինծառայողներ սոց ապահովություն", "category": "services"},
    {"act_id": "175252", "title": "Խնամքի նպաստ կարգ", "category": "allowances"},
    {"act_id": "144492", "title": "Պետական նպաստների մասին", "category": "allowances"},
    {"act_id": "64540", "title": "Պետական կենսաթոշակների մասին", "category": "pensions"},
    {"act_id": "87734", "title": "Զբաղվածության մասին", "category": "employment"},
    {"act_id": "202013", "title": "Անապահովություն 2025 N 27-Ն", "category": "allowances"},
    {"act_id": "218849", "title": "Նպաստների փոփոխություններ 2025", "category": "allowances"},
    {"act_id": "94822", "title": "Պետական նպաստների մասին բազային", "category": "allowances"},
]

CRAWL_PAGES = [
    "https://social.gov.am/",
    "https://social.gov.am/employment",
    "https://social.gov.am/pension-security",
    "https://social.gov.am/demography-family-support",
    "https://social.gov.am/equal-opportunities",
    "https://uss.social.gov.am/",
    "https://uss.social.gov.am/%D5%B6%D5%BA%D5%A1%D5%BD%D5%BF%D5%B6%D5%A5%D6%80-1",
    "https://uss.social.gov.am/%D5%A1%D5%B7%D5%AD%D5%A1%D5%BF%D5%A1%D5%B6%D6%84-%D6%87-%D5%A6%D5%A2%D5%A1%D5%B2%D5%BE%D5%A1%D5%AE%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6",
    "https://uss.social.gov.am/%D5%BD%D5%B8%D6%81%D5%AB%D5%A1%D5%AC%D5%A1%D5%AF%D5%A1%D5%B6-%D5%A1%D5%BA%D5%A1%D5%B0%D5%B8%D5%BE%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6",
    "https://uss.social.gov.am/%D5%A1%D5%B6%D5%B1%D5%AB-%D6%86%D5%B8%D6%82%D5%B6%D5%AF%D6%81%D5%AB%D5%B8%D5%B6%D5%A1%D5%AC%D5%B8%D6%82%D5%A9%D5%B5%D5%A1%D5%B6-%D5%A3%D5%B6%D5%A1%D5%B0%D5%A1%D5%BF%D5%B8%D6%82%D5%B4",
    "https://uss.social.gov.am/%D5%BD%D5%B8%D6%81%D5%AB%D5%A1%D5%AC%D5%A1%D5%AF%D5%A1%D5%B6-%D5%A1%D5%BB%D5%A1%D5%AF%D6%81%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6",
    "https://old.mlsa.am/",
    "https://old.socservice.am/",
]


def collect_targets() -> list[dict[str, str]]:
    """Return list of {id, url, title} unique by url."""
    by_url: dict[str, dict[str, str]] = {}

    def add(doc_id: str, url: str, title: str = "") -> None:
        url = (url or "").strip()
        if not url or not url.startswith("http"):
            return
        if url in by_url:
            return
        by_url[url] = {"id": slug(doc_id), "url": url, "title": title or doc_id}

    # 1) ARLIS catalog
    arlis = load_json(BACKEND / "arlis_catalog.json") or []
    for e in arlis:
        aid = str(e.get("act_id") or "")
        dl = e.get("download_url") or (f"https://www.arlis.am/hy/acts/{aid}/download/act" if aid else "")
        add(f"arlis-{aid}", dl, e.get("title_hy") or aid)

    # 2) PDF catalog
    pdf_cat = load_json(BACKEND / "mlsa_pdf_catalog.json") or []
    for e in pdf_cat:
        add(str(e.get("id") or e.get("url")), e.get("url") or "", e.get("title_hy") or "")

    # 3) Extra acts
    for e in EXTRA_ARLIS_ACTS:
        aid = str(e["act_id"])
        add(
            f"arlis-{aid}",
            f"https://www.arlis.am/hy/acts/{aid}/download/act",
            e.get("title") or aid,
        )

    # 4) Crawl pages for PDF / asset links
    session = requests.Session()
    session.headers.update(HEADERS)
    for page in CRAWL_PAGES:
        try:
            print(f"[crawl] {page[:80]}")
            r = session.get(page, timeout=40, allow_redirects=True)
            if r.status_code != 200:
                print(f"  HTTP {r.status_code}")
                continue
            # Armenian gov pages sometimes lack charset; requests defaults to ISO-8859-1.
            r.encoding = r.apparent_encoding or "utf-8"
            soup = BeautifulSoup(r.text, "lxml")
            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                full = urljoin(page, href)
                low = full.lower()
                label = a.get_text(" ", strip=True) or Path(urlparse(full).path).name
                if (
                    ".pdf" in low
                    or "/download/act" in low
                    or "/api/assets/" in low
                    or "/assets/" in low and "cms.uss" in low
                ):
                    add(f"crawl-{slug(label)[:40]}-{slug(Path(urlparse(full).path).name)[:30]}", full, label)
            # also scan raw HTML for asset UUIDs
            for m in re.finditer(
                r"https?://[^\s\"']+(?:/api/assets/[a-f0-9\-]+|/assets/[a-f0-9\-]+|/hy/acts/\d+/download/act|\.pdf)",
                r.text,
                re.I,
            ):
                full = m.group(0).rstrip(").,;'\"")
                add(f"scan-{slug(Path(urlparse(full).path).name)}", full, full)
            time.sleep(0.3)
        except Exception as ex:
            print(f"  crawl error: {ex}")

    return list(by_url.values())


def looks_like_pdf(content: bytes) -> bool:
    return content[:4] == b"%PDF" or b"%PDF" in content[:2048]


def download_one(session: requests.Session, target: dict[str, str]) -> str:
    """Returns: saved | skip | fail"""
    doc_id = target["id"]
    url = target["url"]
    out = PDFS / f"{doc_id}.pdf"
    if out.exists() and out.stat().st_size > 2000:
        return "skip"

    try:
        r = session.get(url, timeout=90, allow_redirects=True)
        if r.status_code != 200:
            print(f"  fail HTTP {r.status_code} {doc_id}")
            return "fail"
        raw = r.content
        if len(raw) < 800:
            print(f"  fail tiny {doc_id} ({len(raw)})")
            return "fail"
        if not looks_like_pdf(raw):
            # keep non-PDF binary only if large and we can still try later; skip for library
            print(f"  fail not-pdf {doc_id} ({len(raw)} bytes, ctype={r.headers.get('content-type','')})")
            return "fail"
        out.write_bytes(raw)
        print(f"  saved {out.name} ({len(raw)} bytes)")
        return "saved"
    except Exception as e:
        print(f"  fail {doc_id}: {e}")
        return "fail"


def harvest() -> dict[str, Any]:
    targets = collect_targets()
    print(f"[harvest] {len(targets)} unique URLs to fetch")
    session = requests.Session()
    session.headers.update(HEADERS)
    stats = {"saved": 0, "skip": 0, "fail": 0, "targets": len(targets)}
    for i, t in enumerate(targets, 1):
        print(f"[{i}/{len(targets)}] {t['id']}")
        res = download_one(session, t)
        stats[res] = stats.get(res, 0) + 1
        time.sleep(0.15)
    stats["library_pdfs"] = len(list(PDFS.glob("*.pdf")))
    print(f"[harvest] DONE {stats}")
    # write manifest
    manifest = {
        "stats": stats,
        "files": sorted(p.name for p in PDFS.glob("*.pdf")),
    }
    save_json(PDFS / "_harvest_manifest.json", manifest)
    return stats


def sync_arlis_catalog_from_extra() -> None:
    """Ensure EXTRA acts exist in arlis_catalog for HTML legal ingest too."""
    path = BACKEND / "arlis_catalog.json"
    catalog = load_json(path) or []
    have = {str(e.get("act_id")) for e in catalog}
    added = 0
    for e in EXTRA_ARLIS_ACTS:
        aid = str(e["act_id"])
        if aid in have:
            continue
        catalog.append(
            {
                "act_id": aid,
                "title_hy": e.get("title") or f"ARLIS {aid}",
                "title_en": e.get("title") or f"ARLIS {aid}",
                "category": e.get("category") or "general",
                "program_keys": [],
                "arlis_url": f"https://www.arlis.am/hy/acts/{aid}",
                "download_url": f"https://www.arlis.am/hy/acts/{aid}/download/act",
                "priority": 2,
            }
        )
        have.add(aid)
        added += 1
    if added:
        save_json(path, catalog)
        print(f"[harvest] Added {added} acts to arlis_catalog.json (now {len(catalog)})")
    else:
        print(f"[harvest] arlis_catalog already complete ({len(catalog)} acts)")


def expand_pdf_catalog_from_arlis() -> None:
    """Mirror every arlis act into mlsa_pdf_catalog for catalog-based ingest."""
    arlis = load_json(BACKEND / "arlis_catalog.json") or []
    pdf_path = BACKEND / "mlsa_pdf_catalog.json"
    pdf_cat = load_json(pdf_path) or []
    have_urls = {e.get("url") for e in pdf_cat}
    added = 0
    for e in arlis:
        aid = str(e.get("act_id") or "")
        url = e.get("download_url") or f"https://www.arlis.am/hy/acts/{aid}/download/act"
        if url in have_urls:
            continue
        pdf_cat.append(
            {
                "id": f"arlis-act-{aid}",
                "title_hy": e.get("title_hy") or f"ARLIS {aid}",
                "title_en": e.get("title_en") or f"ARLIS {aid}",
                "category": e.get("category") or "general",
                "program_keys": e.get("program_keys") or [],
                "url": url,
                "source": "arlis.am",
                "priority": e.get("priority", 2),
            }
        )
        have_urls.add(url)
        added += 1
    if added:
        save_json(pdf_path, pdf_cat)
        print(f"[harvest] Expanded mlsa_pdf_catalog +{added} (now {len(pdf_cat)})")


if __name__ == "__main__":
    rebuild = "--no-rebuild" not in sys.argv
    sync_arlis_catalog_from_extra()
    expand_pdf_catalog_from_arlis()
    stats = harvest()
    if rebuild:
        print("[harvest] Rebuilding full corpus…")
        from scraper import run_scraper

        docs = run_scraper(force_arlis=False, force_all=False)
        by: dict[str, int] = {}
        for d in docs or []:
            t = d.get("doc_type") or "?"
            by[t] = by.get(t, 0) + 1
        print(f"[harvest] Corpus: {len(docs or [])} docs {by}")
    print("[harvest] Complete.")

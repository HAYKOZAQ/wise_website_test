"""
Scrape public MLSA / USS / program pages into citizen-readable RAG docs.

Targets official pages that describe social programs (not news fluff).
Falls back gracefully when a page is JS-heavy or offline.
"""

from __future__ import annotations

import sys
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from ingest_common import (
    TextCache,
    backend_dir,
    data_dir,
    default_headers,
    hard_split,
    http_get,
    normalize_text,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Curated official program / service pages (MLSA + USS + hartak for displaced)
PROGRAM_PAGES: list[dict[str, Any]] = [
    {
        "id": "mlsa-home",
        "url": "https://social.gov.am/",
        "title_hy": "ԱՍՀՆ — պաշտոնական ծառայություններ (ակնարկ)",
        "category": "general",
        "program_keys": [],
        "priority": 2,
    },
    {
        "id": "mlsa-employment",
        "url": "https://social.gov.am/employment",
        "title_hy": "ԱՍՀՆ — Աշխատանք և զբաղվածություն",
        "category": "employment",
        "program_keys": ["unemployment", "job_placement", "vocational_training"],
        "priority": 1,
    },
    {
        "id": "mlsa-equal",
        "url": "https://social.gov.am/equal-opportunities",
        "title_hy": "ԱՍՀՆ — Հավասար հնարավորություններ",
        "category": "services",
        "program_keys": ["disability_social", "equal_opportunities"],
        "priority": 2,
    },
    {
        "id": "mlsa-pension",
        "url": "https://social.gov.am/pension-security",
        "title_hy": "ԱՍՀՆ — Կենսաթոշակներ և դրամական վճարներ",
        "category": "pensions",
        "program_keys": ["age_pension", "disability_pension", "survivor_pension"],
        "priority": 1,
    },
    {
        "id": "mlsa-demography",
        "url": "https://social.gov.am/demography-family-support",
        "title_hy": "ԱՍՀՆ — Ժողովրդագրություն և ընտանիքի սոցիալական երաշխիքներ",
        "category": "allowances",
        "program_keys": ["childbirth_benefit", "childcare_allowance", "family_benefit"],
        "priority": 1,
    },
    {
        "id": "uss-home",
        "url": "https://uss.social.gov.am/",
        "title_hy": "Միասնական սոցիալական ծառայություն — ծառայություններ",
        "category": "general",
        "program_keys": [],
        "priority": 1,
    },
    {
        "id": "uss-employment",
        "url": "https://uss.social.gov.am/%D5%A1%D5%B7%D5%AD%D5%A1%D5%BF%D5%A1%D5%B6%D6%84-%D6%87-%D5%A6%D5%A2%D5%A1%D5%B2%D5%BE%D5%A1%D5%AE%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6",
        "title_hy": "ՄՍԾ — Աշխատանք և զբաղվածություն",
        "category": "employment",
        "program_keys": ["unemployment", "job_placement"],
        "priority": 1,
    },
    {
        "id": "uss-social-security",
        "url": "https://uss.social.gov.am/%D5%BD%D5%B8%D6%81%D5%AB%D5%A1%D5%AC%D5%A1%D5%AF%D5%A1%D5%B6-%D5%A1%D5%BA%D5%A1%D5%B0%D5%B8%D5%BE%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6",
        "title_hy": "ՄՍԾ — Սոցիալական ապահովություն (կենսաթոշակներ, նպաստներ)",
        "category": "pensions",
        "program_keys": ["age_pension", "childbirth_benefit", "childcare_allowance"],
        "priority": 1,
    },
    {
        "id": "uss-functional",
        "url": "https://uss.social.gov.am/%D5%A1%D5%B6%D5%B1%D5%AB-%D6%86%D5%B8%D6%82%D5%B6%D5%AF%D6%81%D5%AB%D5%B8%D5%B6%D5%A1%D5%AC%D5%B8%D6%82%D5%A9%D5%B5%D5%A1%D5%B6-%D5%A3%D5%B6%D5%A1%D5%B0%D5%A1%D5%BF%D5%B8%D6%82%D5%B4",
        "title_hy": "ՄՍԾ — Անձի ֆունկցիոնալության գնահատում (հաշմանդամություն)",
        "category": "services",
        "program_keys": ["disability_social", "disability_pension"],
        "priority": 1,
    },
    {
        "id": "uss-support",
        "url": "https://uss.social.gov.am/%D5%BD%D5%B8%D6%81%D5%AB%D5%A1%D5%AC%D5%A1%D5%AF%D5%A1%D5%B6-%D5%A1%D5%BB%D5%A1%D5%AF%D6%81%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6",
        "title_hy": "ՄՍԾ — Սոցիալական աջակցություն (նպաստներ, բնակապահովում)",
        "category": "allowances",
        "program_keys": ["family_benefit", "social_benefit", "housing"],
        "priority": 1,
    },
    {
        "id": "uss-benefits",
        "url": "https://uss.social.gov.am/%D5%B6%D5%BA%D5%A1%D5%BD%D5%BF%D5%B6%D5%A5%D6%80-1",
        "title_hy": "ՄՍԾ — Նպաստներ",
        "category": "allowances",
        "program_keys": ["family_benefit", "social_benefit", "emergency_aid"],
        "priority": 1,
    },
    {
        "id": "e-social",
        "url": "https://e-social.am/",
        "title_hy": "e-social.am — առցանց սոցիալական ծառայություններ",
        "category": "contacts",
        "program_keys": ["esoc", "apply_online"],
        "priority": 1,
    },
    {
        "id": "e-work",
        "url": "https://e-work.am/",
        "title_hy": "e-work.am — աշխատանքի որոնում (պետական)",
        "category": "employment",
        "program_keys": ["job_placement", "unemployment"],
        "priority": 2,
    },
    {
        "id": "hartak-displaced",
        "url": "https://hartak.am/categories/%D5%A1%D5%BB%D5%A1%D5%AF%D6%81%D5%B8%D6%82%D5%A9%D5%B5%D5%B8%D6%82%D5%B6-%D5%AC%D5%B2-%D5%AB%D6%81-%D5%A2%D5%BC%D5%B6%D5%AB-%D5%BF%D5%A5%D5%B2%D5%A1%D5%B0%D5%A1%D5%B6%D5%BE%D5%A1%D5%AE-%D5%A1%D5%B6%D5%B1%D5%A1%D5%B6%D6%81/",
        "title_hy": "Ղարաբաղից տեղահանված անձանց աջակցության ծրագրեր (հավաքածու)",
        "category": "services",
        "program_keys": ["displaced", "artsakh_support", "housing"],
        "priority": 1,
    },
    {
        "id": "old-mlsa",
        "url": "https://old.mlsa.am/",
        "title_hy": "ԱՍՀՆ նախկին կայք — բաժիններ (ակնարկ)",
        "category": "general",
        "program_keys": [],
        "priority": 3,
    },
]


_text_cache = TextCache(data_dir() / "web_cache", min_chars=80)


def extract_page_text(html: str, base_url: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        tag.decompose()

    main = (
        soup.select_one("main")
        or soup.select_one("article")
        or soup.select_one("#content")
        or soup.select_one(".content")
        or soup.body
    )
    if not main:
        return ""

    # Prefer headings + paragraphs + list items
    blocks: list[str] = []
    for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th"]):
        t = el.get_text(" ", strip=True)
        if t and len(t) > 2:
            blocks.append(t)

    if not blocks:
        blocks = [main.get_text("\n", strip=True)]

    # Collect same-domain PDF links for context
    pdf_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        low = href.lower()
        if ".pdf" in low or "/api/assets/" in low or "/download/" in low:
            full = urljoin(base_url, href)
            label = a.get_text(" ", strip=True) or full
            pdf_links.append(f"{label}: {full}")

    text = normalize_text("\n".join(blocks))
    if pdf_links:
        text += "\n\nՓաստաթղթեր / հղումներ:\n" + "\n".join(pdf_links[:25])
    return text


def fetch_page(url: str, timeout: int = 40) -> str | None:
    r = http_get(url, timeout=timeout)
    if r is None:
        return None
    if r.status_code != 200:
        print(f"[web] HTTP {r.status_code} {url[:90]}")
        return None
    return r.text


def page_to_docs(entry: dict[str, Any], text: str) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    title = entry.get("title_hy") or entry.get("id")
    pieces = hard_split(text, max_chars=1600, overlap=120)
    for i, piece in enumerate(pieces):
        piece_title = title if i == 0 else f"{title} (մաս {i + 1})"
        docs.append(
            {
                "title": piece_title,
                "content": piece,
                "doc_type": "web",
                "act_id": f"web:{entry.get('id')}",
                "article": None,
                "category": entry.get("category") or "general",
                "program_keys": entry.get("program_keys") or [],
                "source_url": entry.get("url"),
                "priority": int(entry.get("priority") or 2),
            }
        )
    return docs


def ingest_page(entry: dict[str, Any], force: bool = False) -> list[dict[str, Any]]:
    page_id = str(entry.get("id") or urlparse(entry.get("url", "")).path or "page")
    text = None if force else _text_cache.load(page_id)
    if not text:
        html = fetch_page(entry["url"])
        if not html:
            return []
        text = extract_page_text(html, entry["url"])
        # JS shells often yield almost nothing — keep if we still got some ministry wording
        if len(text) < 100:
            print(f"[web] Thin page {page_id} ({len(text)} chars) — skip")
            return []
        _text_cache.save(page_id, text, entry)
        print(f"[web] Saved {page_id} ({len(text)} chars)")
    else:
        print(f"[web] Cache hit {page_id} ({len(text)} chars)")
    return page_to_docs(entry, text)


def ingest_all(force: bool = False) -> list[dict[str, Any]]:
    all_docs: list[dict[str, Any]] = []
    for entry in PROGRAM_PAGES:
        try:
            all_docs.extend(ingest_page(entry, force=force))
        except Exception as e:
            print(f"[web] Error {entry.get('id')}: {e}")
    print(f"[web] Total web documents: {len(all_docs)}")
    return all_docs


if __name__ == "__main__":
    force = "--force" in sys.argv
    docs = ingest_all(force=force)
    out = data_dir() / "mlsa_web_docs.json"
    from ingest_common import save_json
    save_json(out, docs)
    print(f"[web] Wrote {len(docs)} docs → {out}")

"""
Fetch partner logos for WISE Foundation redesign.

For each partner: try to download the real logo from their website
(falling back through og:image → apple-touch-icon → common logo paths →
Google's favicon service). If everything fails, generate a clean SVG
placeholder with the partner's initials.

Output: SVG/PNG files in src/assets/images/partners/
"""

from __future__ import annotations

import os
import re
import sys
import json
import hashlib
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "src" / "assets" / "images" / "partners"
OUT_DIR.mkdir(parents=True, exist_ok=True)
# Cache to skip already-fetched logos (rerun-safe)
CACHE = OUT_DIR / "_fetched.json"

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
TIMEOUT = 15

# Curated partner definitions.
# (id, display_name, website, ext_hint)
# ext_hint: 'svg' | 'png' | 'jpg' | 'ico' — preferred extension if we must guess
PARTNERS = [
    ("p21", "Պետական եկամուտների կոմիտե", "https://www.taxservice.am", "png"),
    ("p22", "Միասնական Սոցիալական Ծառայություն", "https://socservice.am", "svg"),
    ("p23", "ISTC", "https://istc.am", "png"),
    ("p24", "EIF", "https://eif.am", "png"),
    ("p25", "ID Bank", "https://idbank.am", "svg"),
    ("p26", "Biblos Bank", "https://biblosbank.am", "png"),
    ("p27", "Mellat Bank", "https://mellatbank.com", "png"),
    ("p28", "Inecobank", "https://inecobank.am", "svg"),
    ("p29", "Haybusinessbank", "https://hibbank.am", "png"),
    ("p30", "Hayeknembank", "https://hekembank.am", "png"),
    ("p31", "VTB Armenia", "https://www.vtb.am", "svg"),
    ("p32", "Credo Finance", "https://credofinance.am", "svg"),
    ("p33", "Mogo", "https://mogo.am", "svg"),
    ("p34", "Aregak", "https://aregakumc.am", "png"),
    ("p35", "Rosgosstrakh Armenia", "https://rgs.am", "png"),
    ("p36", "Armenia Insurance", "https://ains.am", "png"),
    ("p37", "Global Credit", "https://globalcredit.am", "png"),
    ("p38", "Norman Credit", "https://norman.am", "png"),
    ("p39", "SEF International", "https://sef.am", "svg"),
    ("p40", "Finca Armenia", "https://finca.am", "svg"),
    ("p41", "Araratbank", "https://araratbank.am", "svg"),
    ("p42", "KAMURJ", "https://kamurj.org", "png"),
    ("p43", "Rostelecom", "https://rt.ru", "svg"),
]

# Common paths to probe in order after scraping
COMMON_LOGO_PATHS = [
    "/logo.svg", "/logo.png", "/img/logo.svg", "/img/logo.png",
    "/images/logo.svg", "/images/logo.png", "/assets/logo.svg",
    "/assets/logo.png", "/assets/img/logo.svg", "/assets/img/logo.png",
    "/static/logo.svg", "/static/logo.png",
    "/wp-content/uploads/logo.svg", "/wp-content/uploads/logo.png",
    "/sites/default/files/logo.png", "/sites/default/files/logo.svg",
    "/upload/logo.png", "/upload/logo.svg",
    "/favicon.svg",
]

# Some Armenian bank/finance sites use the favicon as the only public logo
FAVICON_PATHS = ["/favicon.ico", "/favicon.png", "/apple-touch-icon.png",
                 "/apple-touch-icon-precomposed.png", "/apple-touch-icon-120x120.png"]


def get(url: str, *, binary: bool = False, max_bytes: int = 4_000_000) -> bytes | None:
    """Fetch URL with proper headers. Returns None on any failure."""
    try:
        req = Request(url, headers={
            "User-Agent": UA,
            "Accept": ("image/avif,image/webp,image/apng,image/svg+xml,"
                       "image/*,*/*;q=0.8" if binary else
                       "text/html,application/xhtml+xml,application/xml;q=0.9,"
                       "image/webp,*/*;q=0.8"),
            "Accept-Language": "en-US,en;q=0.8,hy;q=0.5",
        })
        with urlopen(req, timeout=TIMEOUT) as r:
            data = r.read()
            if len(data) > max_bytes:
                return None
            return data
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as e:
        return None


def find_logo_in_html(html: str, base: str) -> str | None:
    """Return absolute URL of a likely logo, or None."""
    if not html:
        return None
    # og:image first (most reliable)
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
                  html, re.I)
    if m:
        return urljoin(base, m.group(1).strip())
    # apple-touch-icon
    m = re.search(r'<link[^>]+rel=["\']apple-touch-icon["\'][^>]+href=["\']([^"\']+)',
                  html, re.I)
    if m:
        return urljoin(base, m.group(1).strip())
    # favicon SVG / ico
    m = re.search(r'<link[^>]+rel=["\'](?:icon|shortcut icon)["\'][^>]+href=["\']([^"\']+)',
                  html, re.I)
    if m:
        return urljoin(base, m.group(1).strip())
    # <img> with "logo" in src/alt
    for m in re.finditer(r'<img[^>]+(?:src|alt)=["\']([^"\']*logo[^"\']*)["\']',
                         html, re.I):
        url = m.group(1)
        if url.startswith("data:"):
            continue
        return urljoin(base, url)
    return None


def google_favicon(domain: str) -> bytes | None:
    """Use Google's free favicon service as last-ditch fallback."""
    url = f"https://www.google.com/s2/favicons?domain={domain}&sz=128"
    return get(url, binary=True)


def best_extension(content_type: str, url: str, default: str) -> str:
    ct = (content_type or "").lower()
    if "svg" in ct or url.lower().endswith(".svg"):
        return "svg"
    if "png" in ct or url.lower().endswith(".png"):
        return "png"
    if "jpeg" in ct or "jpg" in ct or url.lower().endswith(".jpg"):
        return "jpg"
    if "webp" in ct:
        return "png"
    if "ico" in ct or url.lower().endswith(".ico"):
        return "png"
    return default


def try_download_logo(partner: tuple, ext_hint: str) -> tuple[Path | None, str]:
    """Try a sequence of strategies to fetch a real logo. Returns (path, source)."""
    pid, name, website, _ = partner
    parsed = urlparse(website)
    domain = parsed.netloc or website
    origin = f"{parsed.scheme}://{parsed.netloc}"

    tried = []

    # Strategy 1: homepage HTML → og:image / apple-touch-icon / img[logo]
    html = get(website)
    if html:
        try:
            html_str = html.decode("utf-8", errors="ignore")
        except Exception:
            html_str = ""
        logo_url = find_logo_in_html(html_str, website)
        if logo_url and not logo_url.startswith("data:"):
            tried.append(logo_url)
            data = get(logo_url, binary=True)
            if data and len(data) > 200:
                ct = ""
                # Re-fetch to read content-type? Cheap to skip; guess from URL
                ext = best_extension(ct, logo_url, ext_hint)
                return save_logo(pid, data, ext, source=logo_url)

    # Strategy 2: probe COMMON_LOGO_PATHS
    for path in COMMON_LOGO_PATHS:
        url = urljoin(origin, path)
        tried.append(url)
        data = get(url, binary=True)
        if data and len(data) > 200 and not is_html(data):
            ext = best_extension("", url, ext_hint)
            return save_logo(pid, data, ext, source=url)

    # Strategy 3: probe FAVICON_PATHS
    for path in FAVICON_PATHS:
        url = urljoin(origin, path)
        tried.append(url)
        data = get(url, binary=True)
        if data and len(data) > 200 and not is_html(data):
            ext = best_extension("", url, ext_hint)
            return save_logo(pid, data, ext, source=url)

    # Strategy 4: Google's favicon service
    data = google_favicon(domain)
    if data and len(data) > 200:
        return save_logo(pid, data, "png", source="google-favicon")

    return None, ""


def is_html(data: bytes) -> bool:
    head = data[:200].lstrip().lower()
    return head.startswith(b"<!doctype") or head.startswith(b"<html") or b"<head" in head[:100]


def save_logo(pid: str, data: bytes, ext: str, source: str) -> tuple[Path, str]:
    name = f"{pid}.{ext}"
    path = OUT_DIR / name
    path.write_bytes(data)
    return path, source


def make_placeholder_svg(partner: tuple) -> Path:
    """Generate a clean monogram SVG when no real logo is available."""
    pid, name, website, ext_hint = partner
    # Initials: take first 2-3 words, then first letter of each (Latin or Armenian)
    # For Armenian names, fall back to English transliteration via simple title letters.
    initials = extract_initials(name)
    if not initials:
        initials = name[:2].upper()

    # Hash partner name → stable hue
    h = int(hashlib.sha1(pid.encode("utf-8")).hexdigest()[:6], 16)
    hue = h % 360
    bg = f"hsl({hue}, 38%, 92%)"
    fg = f"hsl({hue}, 55%, 28%)"
    accent = f"hsl({hue}, 60%, 38%)"

    # Choose a clean display name (shorten if too long)
    short = name
    if len(name) > 22:
        short = name[:20] + "…"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 120" role="img" aria-label="{escape(name)}">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{bg}"/>
      <stop offset="100%" stop-color="hsl({hue}, 38%, 84%)"/>
    </linearGradient>
  </defs>
  <rect width="240" height="120" rx="14" fill="url(#g)"/>
  <rect x="6" y="6" width="228" height="108" rx="10" fill="none" stroke="{accent}" stroke-width="1.2" stroke-opacity="0.35"/>
  <text x="120" y="62" font-family="'Inter','Segoe UI',system-ui,sans-serif" font-size="42" font-weight="700"
        text-anchor="middle" dominant-baseline="central" fill="{fg}" letter-spacing="-1">{escape(initials)}</text>
  <text x="120" y="100" font-family="'Inter','Segoe UI',system-ui,sans-serif" font-size="11" font-weight="500"
        text-anchor="middle" fill="{fg}" fill-opacity="0.78">{escape(short)}</text>
</svg>
'''
    out = OUT_DIR / f"{pid}.svg"
    out.write_text(svg, encoding="utf-8")
    return out


def extract_initials(name: str) -> str:
    """Best-effort initials from an Armenian / English name."""
    if not name:
        return ""
    parts = re.split(r"[\s()]+", name.strip())
    letters = []
    for p in parts:
        if not p:
            continue
        # First character of each meaningful word
        c = p[0]
        if c.isalpha():
            letters.append(c.upper())
        if len(letters) >= 3:
            break
    return "".join(letters) or name[:2].upper()


def escape(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("'", "&apos;"))


def main() -> int:
    print(f"Fetching partner logos → {OUT_DIR}\n")
    cache: dict[str, dict] = {}
    if CACHE.is_file():
        try:
            cache = json.loads(CACHE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    results = []
    for partner in PARTNERS:
        pid, name, website, ext_hint = partner
        # Skip if we already have a real logo and cache says it succeeded
        if cache.get(pid, {}).get("source") and cache[pid]["source"] != "placeholder":
            existing = OUT_DIR / cache[pid]["file"]
            if existing.is_file():
                results.append(cache[pid])
                print(f"[{pid}] {name}  → cached {cache[pid]['file']}")
                continue
        print(f"[{pid}] {name}  ({website})")
        path, source = try_download_logo(partner, ext_hint)
        if path:
            print(f"   ✓ {path.name}  ({path.stat().st_size:>6} B)  ← {source}")
        else:
            path = make_placeholder_svg(partner)
            print(f"   ◇ placeholder  → {path.name}  ({path.stat().st_size} B)")
        entry = {
            "id": pid,
            "name": name,
            "file": path.name,
            "source": source or "placeholder",
        }
        results.append(entry)
        cache[pid] = entry

    manifest = OUT_DIR / "_manifest.json"
    manifest.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote manifest → {manifest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

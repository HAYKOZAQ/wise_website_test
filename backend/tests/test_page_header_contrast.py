"""
Regression: page-header must never be cream + white (unreadable).
Always brand navy (#0f2740) + white title.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
PAGES = SRC / "pages"
CSS = SRC / "css"
JS = SRC / "js"

NAVY = "#0f2740"
CREAM_FORBIDDEN = ("#f8f6f0", "#ede8dd", "#f5f2eb")


class TestPageHeaderContrast(unittest.TestCase):
    def test_components_css_navy_page_header(self):
        css = (CSS / "components.css").read_text(encoding="utf-8")
        self.assertIn(".page-header", css)
        self.assertIn(NAVY, css)
        start = css.find("/* ===== PAGE HEADER")
        end = css.find("/* ===== MODAL")
        self.assertGreater(start, -1, "PAGE HEADER section missing")
        block = css[start:end]
        for cream in CREAM_FORBIDDEN:
            self.assertNotIn(cream, block, f"cream {cream} must not appear in page-header CSS")
        self.assertIn(NAVY, block)
        self.assertRegex(block, r"color:\s*#ffffff")

    def test_dark_css_does_not_paint_page_header_cream(self):
        dark = (CSS / "dark.css").read_text(encoding="utf-8")
        for cream in CREAM_FORBIDDEN:
            if cream in dark:
                idx = dark.find(cream)
                ctx = dark[max(0, idx - 80) : idx + 80]
                self.assertNotIn("page-header", ctx.lower())

    def test_partners_has_page_header(self):
        html = (PAGES / "partners.html").read_text(encoding="utf-8")
        self.assertIn('class="page-header"', html)
        self.assertNotIn("page-header fade-in", html)
        self.assertIn("page-header__title", html)

    def test_main_js_force_function(self):
        js = (JS / "main.js").read_text(encoding="utf-8")
        self.assertIn("forcePageHeaderContrast", js)
        self.assertIn("#0f2740", js)

    def test_catalog_no_arlis_overlap(self):
        """mlsa_pdf_catalog must not re-list acts already in arlis_catalog."""
        import json

        backend = ROOT / "backend"
        arlis = json.loads((backend / "arlis_catalog.json").read_text(encoding="utf-8"))
        acts = {str(e["act_id"]) for e in arlis}
        cat = json.loads((backend / "mlsa_pdf_catalog.json").read_text(encoding="utf-8"))
        for e in cat:
            url = e.get("url") or ""
            eid = e.get("id") or ""
            act = None
            if "/acts/" in url:
                part = url.split("/acts/")[1].split("/")[0]
                if part.isdigit():
                    act = part
            if eid.startswith("arlis-act-"):
                act = eid.replace("arlis-act-", "")
            self.assertFalse(
                act and act in acts,
                f"catalog entry {eid} duplicates arlis act {act}",
            )


if __name__ == "__main__":
    unittest.main()

"""
Regression: page-header must never be cream + white (unreadable).
Always brand navy (#0f2740) + white title in CSS, HTML inline, and JS force.
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
        # Extract page-header background block
        m = re.search(
            r"\.page-header[\s\S]{0,400}?background(?:-color)?:\s*([^;!]+)",
            css,
        )
        self.assertIsNotNone(m, "page-header background rule missing")
        self.assertIn(NAVY, css)
        # Must not reintroduce cream gradients on page-header rules
        block = css[css.find("/* ===== PAGE HEADER"): css.find("/* ===== MODAL")]
        self.assertTrue(block, "PAGE HEADER section missing")
        for cream in CREAM_FORBIDDEN:
            self.assertNotIn(cream, block, f"cream {cream} must not appear in page-header CSS")
        self.assertIn("#ffffff", block)
        self.assertRegex(block, r"color:\s*#ffffff")

    def test_base_css_page_header_vars_not_cream(self):
        base = (CSS / "base.css").read_text(encoding="utf-8")
        # Light-mode page-header vars must be navy (not cream)
        self.assertIn("--page-header-grad-start: #0f2740", base)
        self.assertIn("--page-header-grad-end: #0f2740", base)

    def test_dark_css_does_not_override_to_cream(self):
        dark = (CSS / "dark.css").read_text(encoding="utf-8")
        # Explicit navy guard present
        self.assertIn("html[data-theme=\"dark\"] .page-header", dark)
        self.assertIn(NAVY, dark)
        for cream in CREAM_FORBIDDEN:
            # cream may appear nowhere in dark for page-header; allow zero
            if cream in dark:
                # only fail if near page-header context
                idx = dark.find(cream)
                ctx = dark[max(0, idx - 80) : idx + 80]
                self.assertNotIn("page-header", ctx.lower())

    def test_partners_html_inline_and_critical(self):
        html = (PAGES / "partners.html").read_text(encoding="utf-8")
        self.assertIn("wisef-page-header-critical", html)
        self.assertIn(NAVY, html)
        self.assertIn('class="page-header"', html)
        self.assertNotIn("page-header fade-in", html)
        self.assertIn("?v=33", html)
        # Inline style on section
        self.assertRegex(
            html,
            r'class="page-header"[^>]*style="[^"]*#0f2740',
        )
        self.assertRegex(
            html,
            r'class="page-header__title"[^>]*style="[^"]*#ffffff',
        )

    def test_about_blog_same_guards(self):
        for name in ("about.html", "blog.html"):
            html = (PAGES / name).read_text(encoding="utf-8")
            self.assertIn("wisef-page-header-critical", html, name)
            self.assertIn(NAVY, html, name)
            self.assertNotIn("page-header fade-in", html, name)
            self.assertIn("?v=33", html, name)

    def test_main_js_force_function(self):
        js = (JS / "main.js").read_text(encoding="utf-8")
        self.assertIn("forcePageHeaderContrast", js)
        self.assertIn("#0f2740", js)
        self.assertIn("setProperty", js)

    def test_all_pages_asset_v32(self):
        for p in PAGES.glob("*.html"):
            t = p.read_text(encoding="utf-8")
            if 'href="/css/' in t:
                self.assertIn("?v=33", t, p.name)
                self.assertNotIn("?v=32", t, p.name)


if __name__ == "__main__":
    unittest.main()

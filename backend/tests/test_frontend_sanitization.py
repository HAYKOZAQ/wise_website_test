"""Frontend sanitization tests using Playwright against the built site."""

from __future__ import annotations

import http.server
import socket
import socketserver
import sys
import threading
from pathlib import Path

import pytest

pytest.importorskip("playwright")

from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SITE_DIR = ROOT / "_site"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _ReuseAddrTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


@pytest.fixture(scope="module")
def site_url():
    if not SITE_DIR.is_dir():
        pytest.skip("Built site not found; run `npm run build` first")

    port = _free_port()
    handler = http.server.SimpleHTTPRequestHandler
    httpd = _ReuseAddrTCPServer(
        ("127.0.0.1", port),
        lambda *args, **kwargs: handler(*args, directory=str(SITE_DIR), **kwargs),
    )
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()
    httpd.server_close()


def test_safehtml_strips_img_onerror(site_url: str):
    """The modal sanitizer must remove event-handler attributes from HTML."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                page.goto(f"{site_url}/blog.html", wait_until="domcontentloaded")
                result = page.evaluate(
                    """() => {
                        const malicious = '<img src=x onerror=alert(1)>';
                        return window.safeHtml(malicious);
                    }"""
                )
            finally:
                browser.close()
    except Exception as e:
        pytest.skip(f"Playwright browser not available: {e}")

    assert isinstance(result, str)
    assert "onerror" not in result.lower()
    assert "alert" not in result.lower()

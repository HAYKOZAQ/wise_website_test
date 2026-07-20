"""Tests for shared ingestion utilities."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from ingest_common import (  # noqa: E402
    dedupe_content_key,
    hard_split,
    http_get,
    safe_canonical_act_id,
)


def _response(status_code: int, *, text: str = "", apparent_encoding: str | None = None, encoding: str | None = None, headers: dict | None = None) -> Mock:
    r = Mock()
    r.status_code = status_code
    r.text = text
    r.content = text.encode("utf-8")
    r.apparent_encoding = apparent_encoding
    r.encoding = encoding
    r.headers = headers or {}
    return r


@patch("ingest_common.time.sleep", return_value=None)
@patch("ingest_common.requests.get")
def test_http_get_retries_429_then_200(mock_get, _sleep):
    mock_get.side_effect = [
        _response(429, headers={"Retry-After": "0"}),
        _response(200, text="ok"),
    ]
    r = http_get("https://example.com/test", retries=3, backoff=0)
    assert r is not None
    assert r.status_code == 200
    assert r.text == "ok"
    assert mock_get.call_count == 2


@patch("ingest_common.time.sleep", return_value=None)
@patch("ingest_common.requests.get")
def test_http_get_returns_none_after_exhausted_retries(mock_get, _sleep):
    mock_get.return_value = _response(503)
    r = http_get("https://example.com/test", retries=2, backoff=0)
    assert r is None
    assert mock_get.call_count == 2


@patch("ingest_common.requests.get")
def test_http_get_encoding_fix(mock_get):
    mock_get.return_value = _response(
        200,
        text="Հայերեն տեքստ",
        apparent_encoding="utf-8",
        encoding="ISO-8859-1",
    )
    r = http_get("https://example.com/test", fix_encoding=True)
    assert r is not None
    assert r.encoding == "utf-8"


def test_hard_split_short_text_no_split():
    text = "Short text."
    assert hard_split(text, max_chars=1000) == [text]


def test_hard_split_long_text_returns_overlapping_chunks():
    text = "\n\n".join(f"Paragraph {i}. " + "word " * 50 for i in range(5))
    chunks = hard_split(text, max_chars=400, overlap=50)
    assert len(chunks) > 1
    total_unique = len(set(chunks))
    assert total_unique == len(chunks)
    # Each chunk should be at most max_chars (allowing boundary rounding)
    for c in chunks:
        assert len(c) <= 450


def test_safe_canonical_act_id_variants():
    assert safe_canonical_act_id("64540") == "64540"
    assert safe_canonical_act_id("arlis-64540") == "64540"
    assert safe_canonical_act_id("pdf:arlis-64540") == "64540"
    assert safe_canonical_act_id(64540) == "64540"
    assert safe_canonical_act_id(123) is None  # too short
    assert safe_canonical_act_id("") is None
    assert safe_canonical_act_id(None) is None


def test_dedupe_content_key_stable_and_distinct():
    a = dedupe_content_key("same content", url="https://a.am/doc1")
    b = dedupe_content_key("same content", url="https://a.am/doc2")
    c = dedupe_content_key("different content", url="https://a.am/doc1")
    assert a == dedupe_content_key("same content", url="https://a.am/doc1")
    assert a != b
    assert a != c
    assert len(a) == 16

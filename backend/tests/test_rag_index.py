"""Tests for RAGIndex build/load/search edge cases."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from rag_index import RAGIndex  # noqa: E402


def _make_chunks(n: int = 3) -> list[dict]:
    return [
        {"title": f"doc {i}", "text": f"ընտանիք երեխա unique{i} կենսաթոշակ"}
        for i in range(n)
    ]


def _make_embeddings(n: int = 3, dim: int = 3) -> list[tuple[int, list[float]]]:
    return [(i, [float((i + 1) * (j + 1)) for j in range(dim)]) for i in range(n)]


def test_build_empty_corpus_returns_false(tmp_path):
    idx = RAGIndex(str(tmp_path))
    assert idx.build([], "hash", []) is False
    assert not idx.is_ready()


def test_build_mismatched_embeddings_returns_false(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(2)
    # Too few embeddings
    embeddings = _make_embeddings(1, 3)
    assert idx.build(chunks, "hash", embeddings) is False
    assert not idx.is_ready()


def test_build_valid_index(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(3)
    embeddings = _make_embeddings(3, 3)
    assert idx.build(chunks, "hash-1", embeddings) is True
    assert idx.is_ready()
    # Should persist and reload with matching hash
    assert idx.load("hash-1") is True


def test_load_hash_mismatch_returns_false(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(2)
    embeddings = _make_embeddings(2, 3)
    assert idx.build(chunks, "hash-a", embeddings) is True
    assert idx.load("hash-b") is False


def test_search_hybrid_dimension_mismatch_falls_back_to_lexical(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(3)
    embeddings = _make_embeddings(3, 3)
    assert idx.build(chunks, "hash", embeddings) is True

    # Query vector has wrong dimension; should not crash and should still
    # return BM25-based results.
    results = idx.search_hybrid("unique0", [0.1, 0.2, 0.3, 0.4], k=5)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_hybrid_empty_query_vector_uses_lexical_only(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(3)
    embeddings = _make_embeddings(3, 3)
    assert idx.build(chunks, "hash", embeddings) is True

    results = idx.search_hybrid("unique1", [], k=5)
    assert isinstance(results, list)
    assert len(results) > 0


def test_search_hybrid_returns_at_most_k_results(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(10)
    embeddings = _make_embeddings(10, 3)
    assert idx.build(chunks, "hash", embeddings) is True

    results = idx.search_hybrid("unique0", _make_embeddings(1, 3)[0][1], k=3)
    assert len(results) <= 3


def test_search_hybrid_not_ready_returns_empty():
    idx = RAGIndex(str(Path(__file__).parent / "nonexistent"))
    results = idx.search_hybrid("query", [0.1, 0.2], k=5)
    assert results == []


def test_build_zero_dimensional_vectors_rejected(tmp_path):
    idx = RAGIndex(str(tmp_path))
    chunks = _make_chunks(2)
    embeddings = [(i, []) for i in range(2)]
    assert idx.build(chunks, "hash", embeddings) is False
    assert not idx.is_ready()

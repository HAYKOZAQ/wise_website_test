"""
Persistent hybrid index for WISE RAG: FAISS dense vectors + BM25 keyword index.

Replaces the previous in-memory cosine scan / TF-IDF with fast, persisted
FAISS + BM25 indexes. Keeps a fallback to the old sparse path if deps are
missing.
"""

from __future__ import annotations

import os
import pickle
import re
from typing import Any

import numpy as np


def _tokenize_bm25(text: str) -> list[str]:
    """Whitespace-ish tokenization that keeps Armenian letters."""
    text = (text or "").lower()
    return [t for t in re.findall(r"[\w\u0531-\u0587]+", text, flags=re.UNICODE) if len(t) > 1]


class RAGIndex:
    """Hybrid dense/sparse index with disk persistence."""

    def __init__(self, backend_dir: str):
        self.backend_dir = backend_dir
        self.index_dir = os.path.join(backend_dir, "data", "index")
        self.chunks: list[dict[str, Any]] = []
        self.faiss_index: Any = None
        self.bm25: Any = None
        self.corpus_hash = ""
        self._faiss_available = False
        self._bm25_available = False

    def _load_deps(self) -> bool:
        """Lazy-load optional deps; return True if both available."""
        if not self._faiss_available:
            try:
                import faiss
                self._faiss = faiss
                self._faiss_available = True
            except Exception:
                self._faiss_available = False
        if not self._bm25_available:
            try:
                from rank_bm25 import BM25Okapi
                self._BM25Okapi = BM25Okapi
                self._bm25_available = True
            except Exception:
                self._bm25_available = False
        return self._faiss_available and self._bm25_available

    def _paths(self):
        return {
            "chunks": os.path.join(self.index_dir, "chunks.pkl"),
            "faiss": os.path.join(self.index_dir, "faiss.index"),
            "bm25": os.path.join(self.index_dir, "bm25.pkl"),
            "hash": os.path.join(self.index_dir, "corpus_hash.txt"),
        }

    def _save(self):
        os.makedirs(self.index_dir, exist_ok=True)
        paths = self._paths()
        with open(paths["chunks"], "wb") as f:
            pickle.dump(self.chunks, f)
        with open(paths["bm25"], "wb") as f:
            pickle.dump(self.bm25, f)
        self._faiss.write_index(self.faiss_index, paths["faiss"])
        with open(paths["hash"], "w", encoding="utf-8") as f:
            f.write(self.corpus_hash)

    def load(self, corpus_hash: str) -> bool:
        """Load persisted index if corpus hash matches."""
        if not self._load_deps():
            return False
        paths = self._paths()
        if not all(os.path.exists(p) for p in paths.values()):
            return False
        try:
            with open(paths["hash"], "r", encoding="utf-8") as f:
                cached_hash = f.read().strip()
            if cached_hash != corpus_hash:
                return False
            with open(paths["chunks"], "rb") as f:
                self.chunks = pickle.load(f)
            with open(paths["bm25"], "rb") as f:
                self.bm25 = pickle.load(f)
            self.faiss_index = self._faiss.read_index(paths["faiss"])
            self.corpus_hash = corpus_hash
            return True
        except Exception as e:
            print(f"Error loading RAG index: {e}")
            return False

    def build(
        self,
        chunks: list[dict[str, Any]],
        corpus_hash: str,
        embeddings: list[tuple[int, list[float]]],
    ) -> bool:
        """Build FAISS + BM25 indexes from chunks and dense embeddings."""
        if not self._load_deps():
            return False
        if not chunks or not embeddings or len(embeddings) != len(chunks):
            return False

        self.chunks = chunks
        self.corpus_hash = corpus_hash

        # BM25
        tokenized = [_tokenize_bm25(c.get("text", "")) for c in chunks]
        self.bm25 = self._BM25Okapi(tokenized)

        # FAISS
        dim = len(embeddings[0][1])
        vectors = np.array([vec for _, vec in embeddings]).astype("float32")
        # Normalize for cosine similarity via inner product
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vectors = vectors / norms
        self.faiss_index = self._faiss.IndexFlatIP(dim)
        self.faiss_index.add(vectors)

        self._save()
        return True

    def is_ready(self) -> bool:
        return self.faiss_index is not None and self.bm25 is not None

    def search_dense(self, query_vector: list[float], k: int = 40) -> list[tuple[int, float]]:
        """Return (chunk_id, score) sorted by FAISS inner product."""
        if not self.is_ready():
            return []
        q = np.array([query_vector]).astype("float32")
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm
        distances, indices = self.faiss_index.search(q, min(k, len(self.chunks)))
        results: list[tuple[int, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(dist)))
        return results

    def search_bm25(self, query: str, k: int = 40) -> list[tuple[int, float]]:
        """Return (chunk_id, score) sorted by BM25."""
        if not self.is_ready():
            return []
        tokens = _tokenize_bm25(query)
        if not tokens:
            return []
        scores = self.bm25.get_scores(tokens)
        top_k = min(k, len(scores))
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_idx if scores[i] > 0]

    def search_hybrid(
        self,
        query: str,
        query_vector: list[float] | None,
        k: int = 40,
        semantic_weight: float = 0.6,
    ) -> list[tuple[int, float]]:
        """Merge BM25 and dense scores with weighted sum."""
        dense = self.search_dense(query_vector, k=k * 2) if query_vector else []
        lexical = self.search_bm25(query, k=k * 2)

        def rank_scores(pairs: list[tuple[int, float]]) -> dict[int, float]:
            if not pairs:
                return {}
            return {cid: 1.0 - (i / max(len(pairs) - 1, 1)) for i, (cid, _) in enumerate(pairs)}

        dmap = rank_scores(dense)
        lmap = rank_scores(lexical)
        merged: dict[int, float] = {}
        for cid, score in dmap.items():
            merged[cid] = score * semantic_weight
        for cid, score in lmap.items():
            merged[cid] = merged.get(cid, 0.0) + score * (1.0 - semantic_weight)

        results = sorted(merged.items(), key=lambda x: x[1], reverse=True)
        return results[:k]

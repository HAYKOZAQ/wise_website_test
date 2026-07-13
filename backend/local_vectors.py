"""
Local TF–IDF sparse vectors for hybrid retrieval without cloud APIs.

This is real offline IR (not random fake embeddings). Used when Gemini/Ollama
bulk embed is unavailable or the corpus is too large for online embed.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable


_TOKEN_RE = re.compile(r"[\w\u0531-\u0587]+", re.UNICODE)


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) > 2]


class LocalTfidfIndex:
    """In-memory TF–IDF over a list of documents (one string each)."""

    def __init__(self, documents: list[str], max_features: int = 12000):
        self.max_features = max_features
        self.doc_tokens: list[list[str]] = [tokenize(d) for d in documents]
        self.df: Counter[str] = Counter()
        for toks in self.doc_tokens:
            for t in set(toks):
                self.df[t] += 1
        # Keep most frequent document-frequency terms (stable-ish features)
        common = [t for t, _ in self.df.most_common(max_features)]
        self.vocab = {t: i for i, t in enumerate(common)}
        self.n_docs = max(len(documents), 1)
        self.idf = {
            t: math.log((1.0 + self.n_docs) / (1.0 + self.df[t])) + 1.0
            for t in self.vocab
        }
        self.vectors: list[dict[int, float]] = [
            self._tfidf_vec(toks) for toks in self.doc_tokens
        ]

    def _tfidf_vec(self, tokens: list[str]) -> dict[int, float]:
        if not tokens:
            return {}
        tf = Counter(tokens)
        vec: dict[int, float] = {}
        length = float(len(tokens))
        for term, count in tf.items():
            idx = self.vocab.get(term)
            if idx is None:
                continue
            w = (count / length) * self.idf.get(term, 1.0)
            if w > 0:
                vec[idx] = w
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return {k: v / norm for k, v in vec.items()}

    def embed(self, text: str) -> dict[int, float]:
        return self._tfidf_vec(tokenize(text))

    @staticmethod
    def cosine_sparse(a: dict[int, float], b: dict[int, float]) -> float:
        if not a or not b:
            return 0.0
        # iterate smaller
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(i, 0.0) for i, v in a.items())

    def scores(self, query: str) -> list[tuple[int, float]]:
        q = self.embed(query)
        out: list[tuple[int, float]] = []
        for i, vec in enumerate(self.vectors):
            s = self.cosine_sparse(q, vec)
            if s > 0:
                out.append((i, s))
        out.sort(key=lambda x: x[1], reverse=True)
        return out

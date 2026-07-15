"""
Optional cross-encoder re-ranker for WISE RAG.

Improves retrieval precision by scoring [query, chunk_text] pairs with a
multilingual cross-encoder. Disabled automatically if dependencies or the
model are unavailable.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"


class CrossEncoderReranker:
    _instance: "CrossEncoderReranker | None" = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "CrossEncoderReranker":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str | None = None):
        if self._initialized:
            return
        self.model_name = model_name or os.environ.get("RERANK_MODEL", DEFAULT_RERANK_MODEL)
        self._model: Any = None
        self._initialized = True

    def _load(self) -> bool:
        if self._model is not None:
            return True
        try:
            from sentence_transformers import CrossEncoder
        except ImportError:
            return False
        try:
            print(f"Loading cross-encoder re-ranker {self.model_name}…")
            self._model = CrossEncoder(self.model_name, max_length=512)
            return True
        except Exception as e:
            print(f"Could not load re-ranker: {e}")
            return False

    def rerank(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_k: int = 8,
    ) -> list[dict[str, Any]]:
        if not chunks or not self._load():
            return chunks
        texts = [(c.get("text") or "")[:8000] for c in chunks]
        pairs = [[query, t] for t in texts]
        try:
            scores = self._model.predict(pairs, show_progress_bar=False)
        except Exception as e:
            print(f"Re-ranker inference failed: {e}")
            return chunks
        scored = [
            {**chunk, "rerank_score": float(score), "hybrid_score": chunk.get("hybrid_score", 0.0)}
            for chunk, score in zip(chunks, scores)
        ]
        scored.sort(key=lambda x: x["rerank_score"], reverse=True)
        return scored[:top_k]


def get_reranker() -> CrossEncoderReranker:
    return CrossEncoderReranker()

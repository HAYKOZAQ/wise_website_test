"""
Local dense embedding backend using sentence-transformers.

Runs entirely on the backend host — no Google, OpenAI, or Ollama embedding
calls. Useful as the primary vector channel when you want to own the
embedding architecture end-to-end.
"""

from __future__ import annotations

import math
import os
import threading
from typing import Any

LOCAL_EMBED_MODEL = os.environ.get(
    "LOCAL_EMBED_MODEL",
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
)
LOCAL_EMBED_DEVICE = os.environ.get("LOCAL_EMBED_DEVICE", "cpu")


class LocalSentenceEmbedder:
    """Lightweight wrapper around sentence-transformers."""

    _instance: "LocalSentenceEmbedder | None" = None
    _lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "LocalSentenceEmbedder":
        # Singleton so the model is loaded only once per process.
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name: str | None = None, device: str | None = None):
        if self._initialized:
            return
        self.model_name = model_name or LOCAL_EMBED_MODEL
        self.device = device or LOCAL_EMBED_DEVICE
        self._model: Any = None
        self._dim: int | None = None
        self._load_lock = threading.Lock()
        self._initialized = True

    def _load(self):
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "sentence-transformers is required for local embeddings. "
                    "Install it with: pip install sentence-transformers"
                ) from e

            print(f"Loading local embedding model {self.model_name} on {self.device}…")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self._dim = self._model.get_sentence_embedding_dimension()
            print(f"Local embedder ready. Dimension={self._dim}")

    @property
    def dim(self) -> int:
        self._load()
        return self._dim or 0

    def embed(self, texts: str | list[str]) -> list[list[float]]:
        self._load()
        single = isinstance(texts, str)
        inputs = [texts] if single else list(texts)
        if not inputs:
            return []
        vectors = self._model.encode(inputs, convert_to_numpy=True, show_progress_bar=False)
        # Normalize vectors for cosine similarity
        out: list[list[float]] = []
        for v in vectors:
            norm = math.sqrt(sum(float(x) * float(x) for x in v)) or 1.0
            out.append([float(x) / norm for x in v])
        return out

    def embed_one(self, text: str) -> list[float] | None:
        try:
            return self.embed(text)[0]
        except Exception as e:
            print(f"Local embed error: {e}")
            return None


def get_local_embedder() -> LocalSentenceEmbedder:
    return LocalSentenceEmbedder()

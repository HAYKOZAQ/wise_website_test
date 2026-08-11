"""
Persistent hybrid index for WISE RAG.

The sparse channel is stored as compact NumPy posting arrays instead of a
rank_bm25 object.  A BM25 query only needs the postings for the query terms,
so this keeps the runtime footprint small while preserving lexical search.
FAISS remains optional: the full image can use dense search, while the slim
Render image loads the same index as BM25-only.
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import Counter, defaultdict
from typing import Any

import numpy as np

from filelock import FileLock


def _tokenize_bm25(text: str) -> list[str]:
    """Whitespace-ish tokenization that keeps Armenian letters."""
    text = (text or "").lower()
    return [t for t in re.findall(r"[\w\u0531-\u0587]+", text, flags=re.UNICODE) if len(t) > 1]


class CompactBM25:
    """BM25 over compact term postings, without Python objects per token."""

    K1 = 1.5
    B = 0.75

    def __init__(
        self,
        terms: list[str],
        indptr: np.ndarray,
        doc_ids: np.ndarray,
        term_freqs: np.ndarray,
        idf: np.ndarray,
        doc_lengths: np.ndarray,
        avgdl: float,
    ):
        self.vocabulary = {term: i for i, term in enumerate(terms)}
        self.indptr = np.asarray(indptr, dtype=np.int32)
        self.doc_ids = np.asarray(doc_ids, dtype=np.int32)
        self.term_freqs = np.asarray(term_freqs, dtype=np.float32)
        self.idf = np.asarray(idf, dtype=np.float32)
        self.doc_lengths = np.asarray(doc_lengths, dtype=np.float32)
        self.avgdl = float(avgdl) or 1.0
        self.document_count = int(len(self.doc_lengths))

    @classmethod
    def from_documents(cls, documents: list[str]) -> "CompactBM25":
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        doc_lengths = np.zeros(len(documents), dtype=np.float32)

        # Only postings survive this build step. The token lists and Counters
        # are intentionally short-lived so they do not become index state.
        for doc_id, text in enumerate(documents):
            counts = Counter(_tokenize_bm25(text))
            doc_lengths[doc_id] = sum(counts.values())
            for term, frequency in counts.items():
                postings[term].append((doc_id, frequency))

        terms = sorted(postings)
        indptr = [0]
        doc_ids: list[int] = []
        term_freqs: list[int] = []
        idf: list[float] = []
        n_docs = max(len(documents), 1)
        for term in terms:
            entries = postings[term]
            doc_ids.extend(doc_id for doc_id, _ in entries)
            term_freqs.extend(frequency for _, frequency in entries)
            document_frequency = len(entries)
            idf.append(math.log(1.0 + (n_docs - document_frequency + 0.5) / (document_frequency + 0.5)))
            indptr.append(len(doc_ids))

        avgdl = float(doc_lengths.mean()) if len(doc_lengths) else 1.0
        return cls(
            terms,
            np.asarray(indptr, dtype=np.int32),
            np.asarray(doc_ids, dtype=np.int32),
            np.asarray(term_freqs, dtype=np.float32),
            np.asarray(idf, dtype=np.float32),
            doc_lengths,
            avgdl,
        )

    def save(self, npz_path: str, vocabulary_path: str) -> None:
        """Write numeric arrays and vocabulary separately, without pickle."""
        terms = [None] * len(self.vocabulary)
        for term, term_id in self.vocabulary.items():
            terms[term_id] = term

        # Passing an open file prevents NumPy from appending a second suffix
        # to the temporary path used by the atomic index writer.
        with open(npz_path, "wb") as f:
            np.savez_compressed(
                f,
                indptr=self.indptr,
                doc_ids=self.doc_ids,
                term_freqs=self.term_freqs,
                idf=self.idf,
                doc_lengths=self.doc_lengths,
                avgdl=np.asarray([self.avgdl], dtype=np.float32),
            )
        with open(vocabulary_path, "w", encoding="utf-8") as f:
            json.dump(
                {"version": 1, "terms": terms},
                f,
                ensure_ascii=False,
                separators=(",", ":"),
            )

    @classmethod
    def load(cls, npz_path: str, vocabulary_path: str) -> "CompactBM25":
        with open(vocabulary_path, "r", encoding="utf-8") as f:
            vocabulary = json.load(f)
        terms = vocabulary.get("terms") if isinstance(vocabulary, dict) else None
        if not isinstance(terms, list):
            raise ValueError("Invalid BM25 vocabulary")

        with np.load(npz_path, allow_pickle=False) as data:
            avgdl = float(np.asarray(data["avgdl"]).reshape(-1)[0])
            index = cls(
                [str(term) for term in terms],
                data["indptr"],
                data["doc_ids"],
                data["term_freqs"],
                data["idf"],
                data["doc_lengths"],
                avgdl,
            )
        if len(index.indptr) != len(index.vocabulary) + 1:
            raise ValueError("BM25 vocabulary and postings do not match")
        return index

    def get_scores(self, query: str) -> np.ndarray:
        scores = np.zeros(self.document_count, dtype=np.float32)
        if not self.document_count:
            return scores
        length_norm = self.K1 * (
            1.0 - self.B + self.B * (self.doc_lengths / self.avgdl)
        )
        for term in set(_tokenize_bm25(query)):
            term_id = self.vocabulary.get(term)
            if term_id is None:
                continue
            start = int(self.indptr[term_id])
            end = int(self.indptr[term_id + 1])
            docs = self.doc_ids[start:end]
            frequencies = self.term_freqs[start:end]
            scores[docs] += self.idf[term_id] * (
                frequencies * (self.K1 + 1.0) / (frequencies + length_norm[docs])
            )
        return scores


class RAGIndex:
    """Hybrid dense/sparse index with disk persistence."""

    def __init__(self, backend_dir: str):
        self.backend_dir = backend_dir
        self.index_dir = os.path.join(backend_dir, "data", "index")
        self.chunks: list[dict[str, Any]] = []
        self.faiss_index: Any = None
        self.bm25: CompactBM25 | None = None
        self.corpus_hash = ""
        self._faiss_available = False
        self._faiss: Any = None
        self._lock = FileLock(os.path.join(self.index_dir, ".index.lock"))

    def _paths(self) -> dict[str, str]:
        return {
            "chunks": os.path.join(self.index_dir, "chunks.json"),
            "faiss": os.path.join(self.index_dir, "faiss.index"),
            "bm25": os.path.join(self.index_dir, "bm25.npz"),
            "vocabulary": os.path.join(self.index_dir, "bm25_vocab.json"),
            "hash": os.path.join(self.index_dir, "corpus_hash.txt"),
        }

    def _load_faiss(self) -> bool:
        if self._faiss_available:
            return True
        try:
            import faiss

            self._faiss = faiss
            self._faiss_available = True
        except Exception:
            self._faiss_available = False
        return self._faiss_available

    def _read_faiss_if_available(self, path: str) -> None:
        if not os.path.exists(path) or not self._load_faiss():
            return
        try:
            self.faiss_index = self._faiss.read_index(path)
        except Exception as e:
            print(f"Warning: could not load optional FAISS index: {e}")
            self.faiss_index = None

    def _save(self) -> None:
        os.makedirs(self.index_dir, exist_ok=True)
        paths = self._paths()
        tmp = {key: path + ".tmp" for key, path in paths.items()}
        try:
            with open(tmp["chunks"], "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, separators=(",", ":"))
            if self.bm25 is None:
                raise ValueError("BM25 index is empty")
            self.bm25.save(tmp["bm25"], tmp["vocabulary"])
            if self.faiss_index is not None and self._load_faiss():
                self._faiss.write_index(self.faiss_index, tmp["faiss"])
            with open(tmp["hash"], "w", encoding="utf-8") as f:
                f.write(self.corpus_hash)

            for key in ("chunks", "bm25", "vocabulary", "hash"):
                os.replace(tmp[key], paths[key])
            if self.faiss_index is not None and os.path.exists(tmp["faiss"]):
                os.replace(tmp["faiss"], paths["faiss"])
            elif os.path.exists(paths["faiss"]):
                # A sparse-only rebuild must not leave a stale dense index.
                os.remove(paths["faiss"])
        except Exception:
            for path in tmp.values():
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass
            raise

    def load(self, corpus_hash: str) -> bool:
        """Load the compact index if its corpus hash matches."""
        paths = self._paths()
        required = ("chunks", "bm25", "vocabulary", "hash")
        if not all(os.path.exists(paths[key]) for key in required):
            return False
        try:
            with open(paths["hash"], "r", encoding="utf-8") as f:
                cached_hash = f.read().strip()
            if cached_hash != corpus_hash:
                return False
            with open(paths["chunks"], "r", encoding="utf-8") as f:
                chunks = json.load(f)
            if not isinstance(chunks, list):
                raise TypeError("chunks.json must contain a list")
            self.chunks = chunks
            self.bm25 = CompactBM25.load(paths["bm25"], paths["vocabulary"])
            self._read_faiss_if_available(paths["faiss"])
            self.corpus_hash = corpus_hash
            return True
        except Exception as e:
            print(f"Error loading RAG index: {e}")
            self.chunks = []
            self.bm25 = None
            self.faiss_index = None
            return False

    def _build_sparse(self, chunks: list[dict[str, Any]], corpus_hash: str) -> None:
        self.chunks = chunks
        self.corpus_hash = corpus_hash
        self.bm25 = CompactBM25.from_documents([c.get("text", "") for c in chunks])

    def build_sparse(
        self,
        chunks: list[dict[str, Any]],
        corpus_hash: str,
        preserve_faiss: bool = True,
    ) -> bool:
        """Persist BM25 even when no dense embedder is available."""
        if not chunks:
            return False
        with self._lock:
            paths = self._paths()
            old_faiss_path = paths["faiss"]
            self.faiss_index = None
            old_hash = ""
            if os.path.exists(paths["hash"]):
                try:
                    with open(paths["hash"], "r", encoding="utf-8") as f:
                        old_hash = f.read().strip()
                except Exception:
                    old_hash = ""
            if preserve_faiss and old_hash == corpus_hash:
                self._read_faiss_if_available(old_faiss_path)
            self._build_sparse(chunks, corpus_hash)
            self._save()
        return True

    def build(
        self,
        chunks: list[dict[str, Any]],
        corpus_hash: str,
        embeddings: list[tuple[int, list[float]]],
    ) -> bool:
        """Build sparse postings and optional FAISS vectors."""
        if not chunks or not embeddings or len(embeddings) != len(chunks):
            return False
        if len(embeddings[0][1]) == 0:
            return False

        with self._lock:
            self._build_sparse(chunks, corpus_hash)
            self.faiss_index = None
            if self._load_faiss():
                dim = len(embeddings[0][1])
                vectors = np.asarray([vec for _, vec in embeddings], dtype="float32")
                norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                norms[norms == 0] = 1.0
                vectors = vectors / norms
                self.faiss_index = self._faiss.IndexFlatIP(dim)
                self.faiss_index.add(vectors)
            self._save()
        return True

    def is_ready(self) -> bool:
        return bool(self.chunks) and self.bm25 is not None

    def search_dense(self, query_vector: list[float], k: int = 40) -> list[tuple[int, float]]:
        """Return (chunk_id, score) sorted by FAISS inner product."""
        if not self.is_ready() or self.faiss_index is None:
            return []
        q = np.asarray([query_vector], dtype="float32")
        q_norm = np.linalg.norm(q)
        if q_norm > 0:
            q = q / q_norm
        distances, indices = self.faiss_index.search(q, min(k, len(self.chunks)))
        return [
            (int(idx), float(dist))
            for dist, idx in zip(distances[0], indices[0])
            if idx != -1
        ]

    def search_bm25(self, query: str, k: int = 40) -> list[tuple[int, float]]:
        """Return (chunk_id, score) sorted by compact BM25."""
        if not self.is_ready():
            return []
        scores = self.bm25.get_scores(query)
        top_k = min(k, len(scores))
        if top_k <= 0:
            return []
        top_idx = np.argsort(scores)[::-1][:top_k]
        return [(int(i), float(scores[i])) for i in top_idx if scores[i] > 0]

    def search_hybrid(
        self,
        query: str,
        query_vector: list[float] | None,
        k: int = 40,
        semantic_weight: float = 0.6,
    ) -> list[tuple[int, float]]:
        """Merge BM25 and dense scores with weighted rank fusion."""
        if not self.is_ready():
            return []
        if (
            query_vector
            and self.faiss_index is not None
            and len(query_vector) != self.faiss_index.d
        ):
            query_vector = None
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

        return sorted(merged.items(), key=lambda x: x[1], reverse=True)[:k]

"""
WISE Foundation — MLSA Social Programs RAG Engine
Hybrid vector + keyword retrieval over citizen summaries and ARLIS legal acts.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
from collections import defaultdict
from functools import lru_cache
from typing import Any

import requests
import threading

try:
    from rag_index import RAGIndex
except ImportError:
    from backend.rag_index import RAGIndex  # type: ignore

try:
    from reranker import get_reranker
except ImportError:
    from backend.reranker import get_reranker  # type: ignore

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_env():
    for env_path in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        "backend/.env",
        ".env",
        "../.env",
    ]:
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())
            except Exception:
                pass


load_env()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gemma2")
USE_LOCAL_EMBEDDER = os.environ.get("USE_LOCAL_EMBEDDER", "1").strip().lower() not in ("0", "false", "no")
USE_RERANKER = os.environ.get("USE_RERANKER", "0").strip().lower() in ("1", "true", "yes")
HYBRID_SEMANTIC_WEIGHT = float(os.environ.get("HYBRID_SEMANTIC_WEIGHT", "0.6"))
QUERY_EXPANSION = os.environ.get("QUERY_EXPANSION", "0").strip().lower() in ("1", "true", "yes")
# Prefer stable Gemini models first; Gemma experimental last
GEMINI_GENERATE_MODELS = [
    m.strip()
    for m in os.environ.get(
        "GEMINI_GENERATE_MODELS",
        "gemma-4-26b-a4b-it,gemma-4-31b-it",
    ).split(",")
    if m.strip()
]
GEMINI_MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "2"))

LEGAL_QUERY_HINTS = (
    "իրավունք", "չափորոշիչ", "հոդված", "մերժում", "ստաժ", "կարգ", "որոշում",
    "օրենք", "պահանջ", "փաստաթղթ", "eligibility", "criteria", "article", "reject",
    "document", "law", "procedure",
)
SUMMARY_QUERY_HINTS = (
    "որքան", "ինչքան", "ինչպես դիմել", "որտեղ", "պարզ", "կարճ", "how much",
    "how to apply", "where", "simple", "amount", "documents needed",
)

_IMAGE_REF_RE = re.compile(r'\b[\w\-]+\.(?:png|jpg|jpeg|gif|svg|webp|bmp|ico)\b', re.I)

def _strip_image_refs(text: str) -> str:
    return _IMAGE_REF_RE.sub('', text or '')


class RAGEngine:
    def __init__(self):
        self.documents: list[dict[str, Any]] = []
        self.chunks: list[dict[str, Any]] = []
        self.embeddings: list[tuple[int, list[float]]] = []
        self.vector_enabled = False
        self.vector_backend = "none"  # local_embedder | gemini | ollama | tfidf_local | faiss_bm25 | none
        self.use_gemini = bool(GEMINI_API_KEY)
        self.corpus_hash = ""
        self.legal_acts = 0
        self.cache_ok = False
        self._tfidf = None  # LocalTfidfIndex | None
        self._rag_index: Any = None
        self._reranker: Any = None
        self.embed_skip_reason = ""

        self.load_data()
        self.build_index()

    def _backend_dir(self) -> str:
        return os.path.dirname(os.path.abspath(__file__))

    def _candidate_data_files(self) -> list[str]:
        b = self._backend_dir()
        return [
            os.path.join(b, "data", "mlsa_programs.json"),
            os.path.join(b, "seed", "mlsa_programs.json"),
        ]

    def load_data(self):
        data_file = next((p for p in self._candidate_data_files() if os.path.exists(p)), None)
        if not data_file:
            print("Data file not found. Running scraper...")
            try:
                from scraper import run_scraper
            except ImportError:
                sys.path.append(self._backend_dir())
                from scraper import run_scraper
            run_scraper()
            data_file = next((p for p in self._candidate_data_files() if os.path.exists(p)), None)

        def _load_file(path: str) -> list[dict[str, Any]]:
            with open(path, "r", encoding="utf-8") as f:
                docs = json.load(f)
            if not isinstance(docs, list):
                raise TypeError(f"{path}: expected list, got {type(docs).__name__}")
            return docs

        def _normalize(docs: list[dict[str, Any]]) -> None:
            for doc in docs:
                doc.setdefault("doc_type", "summary")
                doc.setdefault("act_id", None)
                doc.setdefault("article", None)
                doc.setdefault("category", "general")
                doc.setdefault("program_keys", [])
                doc.setdefault("source_url", None)
                doc.setdefault("priority", 2)

        candidates = self._candidate_data_files()
        last_error = None
        for candidate in candidates:
            if not os.path.exists(candidate):
                continue
            try:
                self.documents = _load_file(candidate)
                _normalize(self.documents)
                self.legal_acts = len(
                    {
                        d.get("act_id")
                        for d in self.documents
                        if d.get("act_id") and not str(d.get("act_id")).startswith(("pdf:", "web:"))
                    }
                )
                by_type: dict[str, int] = {}
                for d in self.documents:
                    t = d.get("doc_type") or "?"
                    by_type[t] = by_type.get(t, 0) + 1
                print(
                    f"Loaded {len(self.documents)} documents from {candidate} "
                    f"(legal acts≈{self.legal_acts}, by_type={by_type})."
                )
                return
            except Exception as e:
                print(f"Warning: failed to load {candidate}: {e}")
                last_error = e

        if not candidates:
            print("Error: no mlsa_programs.json or seed found")
        else:
            print(f"Error loading social programs JSON: {last_error}")
        self.documents = []

    def build_index(self):
        self.chunks = []
        for doc_id, doc in enumerate(self.documents):
            title = doc.get("title", "")
            content = doc.get("content", "")
            doc_type = doc.get("doc_type", "summary")
            if not content:
                continue

            # Keep one coherent unit per summary; legal/pdf/web already chunk-sized
            if doc_type in ("legal", "pdf", "web"):
                pieces = [content]
            else:
                pieces = [content.strip()] if content.strip() else []

            for p in pieces:
                cleaned = _strip_image_refs(p)
                if doc_type == "legal":
                    chunk_text = f"Ակտ՝ {title}\n{cleaned}"
                elif doc_type == "pdf":
                    chunk_text = f"Պաշտոնական PDF՝ {title}\n{cleaned}"
                elif doc_type == "web":
                    chunk_text = f"Պաշտոնական էջ՝ {title}\n{cleaned}"
                else:
                    chunk_text = f"Ծրագիր՝ {title}\nՆկարագրություն՝ {cleaned}"

                self.chunks.append({
                    "chunk_id": len(self.chunks),
                    "doc_id": doc_id,
                    "title": title,
                    "text": chunk_text,
                    "doc_type": doc_type,
                    "act_id": doc.get("act_id"),
                    "article": doc.get("article"),
                    "category": doc.get("category"),
                    "source_url": doc.get("source_url"),
                    "priority": doc.get("priority", 2),
                })

        print(f"Created {len(self.chunks)} semantic chunks.")
        self.corpus_hash = hashlib.sha256(
            json.dumps(
                [{"t": c["title"], "x": c["text"]} for c in self.chunks],
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:16]

        self._load_or_build_embeddings()

    def _cache_path(self) -> str:
        return os.path.join(self._backend_dir(), "data", "embeddings_cache.json")

    def _enable_local_tfidf(self) -> None:
        """Offline vector channel that always works for any corpus size."""
        try:
            from local_vectors import LocalTfidfIndex
        except ImportError:
            from backend.local_vectors import LocalTfidfIndex  # type: ignore
        texts = [c.get("text") or "" for c in self.chunks]
        self._tfidf = LocalTfidfIndex(texts)
        self.vector_enabled = True
        self.vector_backend = "tfidf_local"
        self.cache_ok = False
        self.embed_skip_reason = ""
        print(f"Local TF–IDF vector search enabled ({len(self.chunks)} docs).")

    def _embed_with_local_backend(self):
        """Embed all chunks using the local sentence-transformer backend."""
        try:
            from local_embedder import get_local_embedder
        except ImportError:
            from backend.local_embedder import get_local_embedder  # type: ignore
        embedder = get_local_embedder()
        texts = [(c.get("text") or "")[:8000] for c in self.chunks]
        vectors = embedder.embed(texts)
        if len(vectors) != len(self.chunks):
            return []
        return [(c["chunk_id"], v) for c, v in zip(self.chunks, vectors)]

    def _load_or_build_embeddings(self):
        self.embeddings = []
        self.vector_enabled = False
        self.vector_backend = "none"
        self.cache_ok = False
        self._tfidf = None
        self._rag_index = None
        self.embed_skip_reason = ""
        force_embed = os.environ.get("FORCE_EMBED", "").strip() in ("1", "true", "yes")
        max_auto = int(os.environ.get("AUTO_EMBED_MAX_CHUNKS", "400"))
        prefer_local = os.environ.get("USE_LOCAL_TFIDF", "1").strip().lower() not in ("0", "false", "no")

        # Try persisted FAISS + BM25 index first
        self._rag_index = RAGIndex(self._backend_dir())
        if self._rag_index.load(self.corpus_hash):
            self.embeddings = [(c["chunk_id"], []) for c in self._rag_index.chunks]
            self.vector_enabled = True
            self.cache_ok = True
            self.vector_backend = "faiss_bm25"
            print(f"Loaded persisted FAISS+BM25 index ({len(self._rag_index.chunks)} chunks).")
            return

        # Build dense embeddings, then construct FAISS + BM25 index
        embeddings: list[tuple[int, list[float]]] = []
        backend_name = "none"

        # 1) Own local dense embedding backend (no Google / no Ollama)
        if USE_LOCAL_EMBEDDER:
            print("Trying own local embedding backend…")
            try:
                local_vectors = self._embed_with_local_backend()
                if local_vectors and len(local_vectors) == len(self.chunks):
                    embeddings = local_vectors
                    backend_name = "local_embedder"
            except Exception as e:
                print(f"Local embedder failed: {e}")

        # 2) Large corpora: skip online bulk embed unless forced
        if not embeddings and len(self.chunks) > max_auto and not force_embed:
            self.embed_skip_reason = (
                f"bulk cloud embed skipped for {len(self.chunks)} chunks "
                f"(limit={max_auto}; set FORCE_EMBED=1 for Gemini/Ollama cache)"
            )
            print(self.embed_skip_reason + ". Enabling local TF–IDF vectors.")
            if prefer_local:
                self._enable_local_tfidf()
            return

        # 3) Google Gemini embeddings
        if not embeddings and self.use_gemini and (force_embed or len(self.chunks) <= max_auto):
            print("Using Google Gemini API for embeddings…")
            success = True
            for i, chunk in enumerate(self.chunks):
                if i and i % 25 == 0:
                    print(f"  … embedded {i}/{len(self.chunks)}")
                vector = self.get_gemini_embedding(chunk["text"])
                if vector:
                    embeddings.append((chunk["chunk_id"], vector))
                else:
                    success = False
                    break
            if success and len(embeddings) == len(self.chunks):
                backend_name = "gemini"
            else:
                print("Gemini embeddings incomplete; trying Ollama…")
                embeddings = []

        # 4) Local Ollama embeddings
        if not embeddings:
            print("Falling back to local Ollama for embeddings…")
            try:
                r = requests.get(OLLAMA_HOST, timeout=3)
                if r.status_code == 200:
                    for i, chunk in enumerate(self.chunks):
                        if i and i % 25 == 0:
                            print(f"  … embedded {i}/{len(self.chunks)}")
                        vector = self.get_ollama_embedding(chunk["text"])
                        if vector:
                            embeddings.append((chunk["chunk_id"], vector))
                    if len(embeddings) == len(self.chunks):
                        backend_name = "ollama"
                    else:
                        print("Could not generate all embeddings.")
                else:
                    print("Ollama non-200.")
            except Exception as e:
                print(f"Ollama not available: {e}.")

        # 5) Build and persist FAISS + BM25 index
        if embeddings and len(embeddings) == len(self.chunks):
            self.embeddings = embeddings
            if self._rag_index.build(self.chunks, self.corpus_hash, embeddings):
                self.vector_enabled = True
                self.vector_backend = "faiss_bm25"
                self.cache_ok = True
                self.embed_skip_reason = ""
                print(f"FAISS+BM25 index built ({len(embeddings)} embeddings, backend={backend_name}).")
                return

        # 6) Always provide a working offline vector channel
        if prefer_local:
            self._enable_local_tfidf()
        else:
            self.embed_skip_reason = "no cloud embeddings; USE_LOCAL_TFIDF=0"
            print("Keyword search only.")

    def _save_embeddings_cache(self):
        try:
            cache_file = self._cache_path()
            payload = {
                "corpus_hash": self.corpus_hash,
                "chunks_count": len(self.chunks),
                "embeddings": [
                    {"chunk_id": cid, "vector": vec} for cid, vec in self.embeddings
                ],
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            self.cache_ok = True
            print("Saved embeddings cache.")
        except Exception as e:
            print(f"Error saving embeddings cache: {e}")

    def get_gemini_embedding(self, text: str):
        try:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-embedding-2:embedContent?key={GEMINI_API_KEY}"
            )
            payload = {"content": {"parts": [{"text": text[:8000]}]}}
            r = requests.post(url, json=payload, timeout=20)
            if r.status_code == 200:
                return r.json().get("embedding", {}).get("values")
            print(f"Gemini embedding status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"Gemini embedding error: {e}")
        return None

    def get_ollama_embedding(self, text: str):
        try:
            url = f"{OLLAMA_HOST}/api/embeddings"
            payload = {"model": OLLAMA_MODEL, "prompt": text[:8000]}
            r = requests.post(url, json=payload, timeout=15)
            if r.status_code == 200:
                return r.json().get("embedding")
        except Exception as e:
            print(f"Ollama embedding error: {e}")
        return None

    def get_local_embedding(self, text: str):
        try:
            from local_embedder import get_local_embedder
        except ImportError:
            from backend.local_embedder import get_local_embedder  # type: ignore
        return get_local_embedder().embed_one(text[:8000])

    @staticmethod
    def cosine_similarity(vec1, vec2) -> float:
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            print(
                f"cosine_similarity dimension mismatch: {len(vec1)} vs {len(vec2)}; "
                "returning 0.0 (different embedders or corrupt vector)"
            )
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        na = math.sqrt(sum(a * a for a in vec1))
        nb = math.sqrt(sum(b * b for b in vec2))
        if na == 0.0 or nb == 0.0:
            return 0.0
        return dot / (na * nb)

    def _tokenize(self, text: str) -> set[str]:
        text = text.lower()
        # Keep Armenian letters and alphanumerics
        words = re.findall(r"[\w\u0531-\u0587]+", text, flags=re.UNICODE)
        return {w for w in words if len(w) > 2}

    def _keyword_scores(self, query: str) -> list[tuple[int, float]]:
        if self._rag_index is not None and self._rag_index.is_ready():
            return self._rag_index.search_bm25(query, k=80)

        # Fallback legacy keyword scorer
        q_words = self._tokenize(query)
        if not q_words:
            return []
        scores = []
        for chunk in self.chunks:
            text = chunk["text"] or ""
            c_words = self._tokenize(text)
            if not c_words:
                continue
            overlap = len(q_words & c_words)
            sub_hits = 0
            low = text.lower()
            for w in q_words:
                if len(w) >= 4 and w in low:
                    sub_hits += 1
            title_words = self._tokenize(chunk.get("title") or "")
            title_hit = len(q_words & title_words)
            length_norm = max(2.0, min(math.log(1 + len(c_words)), 6.5))
            score = (float(overlap) + 0.65 * float(sub_hits)) / length_norm
            score += 2.2 * float(title_hit)
            if overlap >= 2:
                score += 0.35 * (overlap - 1)
            if score > 0:
                scores.append((chunk["chunk_id"], score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    @lru_cache(maxsize=256)
    def _embed_query(self, query: str) -> list[float] | None:
        """Centralized query embedding with fallback chain and LRU cache."""
        return self._embed_queries_batch([query])[0]

    def _embed_queries_batch(self, queries: list[str]) -> list[list[float] | None]:
        """Embed a batch of query strings, preferring local backend then Gemini then Ollama."""
        if not queries:
            return []

        # 1) Local sentence-transformer backend (fast, no network, batched).
        if USE_LOCAL_EMBEDDER:
            try:
                from local_embedder import get_local_embedder

                embedder = get_local_embedder()
                vectors = embedder.embed(queries)
                if len(vectors) == len(queries):
                    return vectors
            except Exception as e:
                print(f"Local query embedder failed: {e}")

        # 2) Gemini embeddings.
        if self.use_gemini:
            out: list[list[float] | None] = []
            for q in queries:
                out.append(self.get_gemini_embedding(q))
            if all(v is not None for v in out):
                return out

        # 3) Ollama embeddings.
        out = []
        for q in queries:
            out.append(self.get_ollama_embedding(q))
        return out

    def _vector_scores(self, query: str) -> list[tuple[int, float]]:
        if not self.vector_enabled:
            return []
        # Local TF–IDF path (offline)
        if self._tfidf is not None:
            return self._tfidf.scores(query)[:80]
        # FAISS + BM25 hybrid index path
        if self._rag_index is not None and self._rag_index.is_ready():
            q_vec = self._embed_query(query)
            return self._rag_index.search_dense(q_vec, k=80) if q_vec else []
        # Legacy dense embedding path
        if not self.embeddings:
            return []
        q_vec = self._embed_query(query)
        if not q_vec:
            return []
        scores = []
        for chunk_id, vec in self.embeddings:
            sim = self.cosine_similarity(q_vec, vec)
            scores.append((chunk_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    @staticmethod
    def _canonical_act_id(act_id: Any) -> str | None:
        if not act_id:
            return None
        s = str(act_id)
        m = re.search(r"(\d{4,})", s)
        return m.group(1) if m else s

    def _query_prefers_legal(self, query: str) -> bool:
        q = query.lower()
        return any(h in q for h in LEGAL_QUERY_HINTS)

    def _query_prefers_summary(self, query: str) -> bool:
        q = query.lower()
        return any(h in q for h in SUMMARY_QUERY_HINTS)

    def _expand_query(self, query: str) -> list[str]:
        """Generate query variants for better recall (optional, LLM-powered)."""
        if not QUERY_EXPANSION:
            return [query]
        if len(query.split()) > 15:
            return [query]
        # Use the fastest available generator for a cheap rewrite
        variants = [query]
        rewrite_prompt = (
            "Rewrite this question in Armenian in 1 different way to help search a database. "
            "Return ONLY the rewritten question, no explanation.\n\nQuestion: "
        ) + query
        try:
            rewritten = ""
            if self.use_gemini:
                rewritten = self._generate_with_gemini(rewrite_prompt)
            if not rewritten:
                rewritten = self._generate_with_ollama(rewrite_prompt)
            if rewritten:
                clean = rewritten.strip().split("\n")[0].strip()
                if clean and clean.lower() != query.lower():
                    variants.append(clean)
        except Exception as e:
            print(f"Query expansion failed: {e}")
        return variants

    def _merge_rank(self, query: str, top_n: int = 8) -> list[dict[str, Any]]:
        """Hybrid retrieval with optional re-ranking and diversification."""
        prefer_legal = self._query_prefers_legal(query)
        prefer_summary = self._query_prefers_summary(query)
        initial_k = max(top_n * 3, 24)

        # Query expansion
        query_variants = self._expand_query(query)

        # Collect candidates from FAISS+BM25 hybrid or legacy channels.
        # Pre-compute query embeddings in one batch to avoid N sequential API calls.
        candidate_scores: dict[int, float] = {}
        use_hybrid = self._rag_index is not None and self._rag_index.is_ready()
        variant_vectors: list[list[float] | None] = []
        if use_hybrid:
            variant_vectors = self._embed_queries_batch(query_variants)

        for i, q in enumerate(query_variants):
            if use_hybrid:
                q_vec = variant_vectors[i] if i < len(variant_vectors) else None
                pairs = self._rag_index.search_hybrid(
                    q, q_vec, k=initial_k, semantic_weight=HYBRID_SEMANTIC_WEIGHT
                )
            else:
                vec = self._vector_scores(q)
                kw = self._keyword_scores(q)

                def normalize(pairs: list[tuple[int, float]]) -> dict[int, float]:
                    if not pairs:
                        return {}
                    mx = max(s for _, s in pairs) or 1.0
                    mn = min(s for _, s in pairs)
                    span = (mx - mn) or 1.0
                    return {cid: (s - mn) / span for cid, s in pairs}

                vmap = normalize(vec[:40])
                kmap = normalize(kw[:40])
                pairs = []
                all_ids = set(vmap) | set(kmap)
                for cid in all_ids:
                    if self.vector_backend == "tfidf_local":
                        score = 0.50 * vmap.get(cid, 0.0) + 0.50 * kmap.get(cid, 0.0)
                    else:
                        score = 0.55 * vmap.get(cid, 0.0) + 0.45 * kmap.get(cid, 0.0)
                    pairs.append((cid, score))
                pairs.sort(key=lambda x: x[1], reverse=True)
                pairs = pairs[:initial_k]

            # Merge variant scores keeping the max
            for cid, score in pairs:
                candidate_scores[cid] = max(candidate_scores.get(cid, 0.0), score)

        # Precompute which canonical acts have legal HTML chunks available
        acts_with_legal: set[str] = set()
        for ch in self.chunks:
            if (ch.get("doc_type") or "") == "legal":
                ca = self._canonical_act_id(ch.get("act_id"))
                if ca:
                    acts_with_legal.add(ca)

        # Apply type/priority boosts and build candidate list
        candidates: list[dict[str, Any]] = []
        for cid, score in candidate_scores.items():
            chunk = self.chunks[cid]
            dtype = chunk.get("doc_type") or "summary"
            ca = self._canonical_act_id(chunk.get("act_id"))
            adjusted = score
            if dtype == "legal":
                adjusted += 0.20
            elif dtype == "pdf":
                if ca and ca in acts_with_legal:
                    adjusted -= 0.28
                else:
                    adjusted += 0.06
            if prefer_legal and dtype == "legal":
                adjusted += 0.18
            if prefer_legal and dtype == "pdf" and not (ca and ca in acts_with_legal):
                adjusted += 0.10
            if prefer_summary and dtype == "summary":
                adjusted += 0.18
            if dtype == "summary" and not prefer_legal:
                adjusted += 0.06
            if dtype == "web" and not prefer_legal:
                adjusted += 0.05
            pr = chunk.get("priority") or 2
            adjusted += max(0, (3 - pr)) * 0.02
            candidates.append({**chunk, "hybrid_score": adjusted})

        candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)

        # Optional cross-encoder re-ranking
        if USE_RERANKER and candidates:
            if self._reranker is None:
                self._reranker = get_reranker()
            candidates = self._reranker.rerank(query, candidates, top_k=max(top_n * 2, 16))

        # Diversify: limit per act/title; skip PDF if legal already picked for act
        picked: list[dict[str, Any]] = []
        act_counts: dict[str, int] = defaultdict(int)
        title_counts: dict[str, int] = defaultdict(int)
        type_counts: dict[str, int] = defaultdict(int)
        legal_picked_acts: set[str] = set()

        def try_pick(chunk: dict[str, Any]) -> bool:
            cid = chunk["chunk_id"]
            ca = self._canonical_act_id(chunk.get("act_id"))
            act_key = ca or str(chunk.get("act_id") or f"t:{chunk.get('title')}" or cid)
            title_key = chunk.get("title") or str(cid)
            dtype = chunk.get("doc_type") or "summary"
            if dtype == "pdf" and ca and ca in legal_picked_acts:
                return False
            if dtype == "pdf" and ca and ca in acts_with_legal and act_counts[act_key] >= 1:
                return False
            if act_counts[act_key] >= 2:
                return False
            if title_counts[title_key] >= 1:
                return False
            if type_counts[dtype] >= max(3, top_n // 2 + 1):
                return False
            picked.append(chunk)
            act_counts[act_key] += 1
            title_counts[title_key] += 1
            type_counts[dtype] += 1
            if dtype == "legal" and ca:
                legal_picked_acts.add(ca)
            return True

        for c in candidates:
            try_pick(c)
            if len(picked) >= top_n:
                break

        have_legal = any(c.get("doc_type") == "legal" for c in picked)
        have_sum = any(c.get("doc_type") == "summary" for c in picked)
        if not have_legal or not have_sum:
            for c in candidates:
                if not have_legal and c.get("doc_type") == "legal":
                    if try_pick(c):
                        have_legal = True
                if not have_sum and c.get("doc_type") == "summary":
                    if try_pick(c):
                        have_sum = True
                if have_legal and have_sum:
                    break
            if len(picked) > top_n:
                picked = picked[:top_n]

        # Fallback pure keyword if hybrid empty
        if not picked:
            kw = self._keyword_scores(query)
            for cid, _ in kw[:top_n]:
                picked.append(self.chunks[cid])

        return picked

    def retrieve(self, query: str, top_n: int = 8) -> list[dict[str, Any]]:
        if not self.chunks:
            return []
        if self.vector_enabled:
            print(f"Hybrid retrieval for: {query}")
        else:
            print(f"Keyword retrieval for: {query}")
        return self._merge_rank(query, top_n=top_n)

    def _build_sources(self, chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen = set()
        sources = []
        for c in chunks:
            key = (c.get("title"), c.get("article"), c.get("act_id"))
            if key in seen:
                continue
            seen.add(key)
            act_id = c.get("act_id")
            url = c.get("source_url")
            if act_id and not url:
                url = f"https://www.arlis.am/hy/acts/{act_id}"
            sources.append({
                "title": c.get("title") or "Source",
                "act_id": act_id,
                "url": url,
                "article": c.get("article"),
                "doc_type": c.get("doc_type"),
            })
        return sources[:8]

    def _follow_ups(self, query: str, lang: str, chunks: list[dict[str, Any]]) -> list[str]:
        cats = {c.get("category") for c in chunks if c.get("category")}
        if lang == "en":
            base = [
                "Who is eligible?",
                "What documents are required?",
                "How and where do I apply?",
                "What is the amount?",
            ]
            if "pensions" in cats:
                base.append("What is the minimum work history?")
            if "employment" in cats:
                base.append("How do I register as unemployed?")
            return base[:4]
        base = [
            "Ո՞վ ունի իրավունք",
            "Ի՞նչ փաստաթղթեր են պետք",
            "Ինչպե՞ս և որտե՞ղ դիմել",
            "Որքա՞ն է չափը",
        ]
        if "pensions" in cats:
            base.append("Որքա՞ն է նվազագույն ստաժը")
        if "employment" in cats:
            base.append("Ինչպե՞ս ձևակերպել գործազրկության կարգավիճակ")
        return base[:4]

    def _prompt(
        self,
        query: str,
        context_str: str,
        user_lang: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        hist_block = ""
        if history:
            lines = []
            for turn in history[-6:]:
                role = (turn.get("role") or "user").lower()
                content = (turn.get("content") or "").strip()
                if not content:
                    continue
                label = "Citizen" if role == "user" else "Assistant"
                lines.append(f"{label}: {content[:500]}")
            if lines:
                hist_block = "\n\nPRIOR TURNS (for context only; still ground facts in CONTEXT):\n" + "\n".join(lines)

        if user_lang == "en":
            return f"""You are a careful citizen guide for Armenia's social protection programs (MLSA / Unified Social Service).

GOAL: Give a COMPLETE, practical explanation so a person understands how the program works end-to-end.

RULES:
1) Use ONLY the CONTEXT below. Never invent amounts, ages, documents, deadlines, or article numbers.
2) If a detail is missing in CONTEXT, write clearly: "This is not specified in the available materials" and suggest hotline 114 / e-soc.am / USS office.
3) Write FULL sentences. Never cut off mid-word or mid-list. Finish every section.
4) Prefer concrete numbers and lists FROM the context. Prefer [legal] facts over citizen [summary] when they conflict. Treat [summary] amounts as provisional.
5) For any money amount, age threshold, or deadline: if it comes only from a citizen summary, add: "Please verify the current amount with hotline 114 or e-social.am."
6) Explain the logic: who → what benefit → how much → how it works → how to apply.

Required markdown structure (fill every section; if unknown, say so):
## Short answer
(2–4 sentences: what the program is and who it is for)

## How the program works
(Explain the mechanism / process in plain language)

## Who is eligible
(Bullet criteria)

## Amount / calculation
(All amounts or formula found in context)

## Required documents
(Bullet list)

## How / where to apply
(e-soc.am, USS centers, hotline 114 when relevant)

## Deadlines
(If any)

## Important notes
(Exceptions, border villages, working vs non-working, etc. if in context)

## Sources
(Titles from context only)

CONTEXT:
{context_str}
{hist_block}

CITIZEN QUESTION:
{query}

Write a complete answer in clear English:"""

        hist_hy = ""
        if history:
            lines = []
            for turn in history[-6:]:
                role = (turn.get("role") or "user").lower()
                content = (turn.get("content") or "").strip()
                if not content:
                    continue
                label = "Քաղաքացի" if role == "user" else "Օգնական"
                lines.append(f"{label}: {content[:500]}")
            if lines:
                hist_hy = "\n\nՆԱԽՈՐԴ ՀԱՐՑՈՒՄՆԵՐ (միայն համատեքստի համար. փաստերը՝ ՀԱՄԱՏԵՔՍՏԻՑ).\n" + "\n".join(lines)

        return f"""Դուք Հայաստանի սոցիալական պաշտպանության ծրագրերի (ԱՍՀՆ / Միասնական սոցիալական ծառայություն) քաղաքացիական ուղեցույցն եք։

ՆՊԱՏԱԿ. տվեք ԱՄԲՈՂՋԱԿԱՆ, գործնական բացատրություն, որպեսզի մարդը հասկանա՝ ինչպես է ծրագիրն աշխատում սկզբից մինչև վերջ։

ԿԱՆՈՆՆԵՐ.
1) Օգտագործեք ՄԻԱՅՆ ստորև տրված ՀԱՄԱՏԵՔՍՏԸ։ Երբեք մի հորինեք գումարներ, տարիք, փաստաթղթեր, ժամկետներ կամ հոդվածների համարներ։
2) Եթե որևէ մանրամասն չկա համատեքստում, գրեք հստակ՝ «Առկա նյութերում սա նշված չէ» և առաջարկեք թեժ գիծ 114 / e-soc.am / ՄՍԾ տարածքային կենտրոն։
3) Գրեք ԼՐԻՎ նախադասություններ։ Երբեք մի կտրեք բառի կամ ցուցակի կեսից։ Ավարտեք յուրաքանչյուր բաժին։
3ա) Եթե [legal] և [summary] հակասում են, նախընտրեք [legal]։ Summary-ի գումարները պայմանական են.
3բ) Յուրաքանչյուր գումար/տարիք/ժամկետ summary-ից՝ ավելացրեք. «Ստուգեք ակտուալ չափը 114 կամ e-social.am»։
4) Նախընտրեք համատեքստի կոնկրետ թվերն ու ցուցակները։
5) Բացատրեք տրամաբանությունը՝ ով → ինչ նպաստ → որքան → ինչպես է աշխատում → ինչպես դիմել։

Պարտադիր markdown կառուցվածք (լրացրեք բոլոր բաժինները. եթե անհայտ է՝ ասեք).
## Կարճ պատասխան
(2–4 նախադասություն՝ ինչ է ծրագիրը և ում համար է)

## Ինչպես է աշխատում ծրագիրը
(Պարզ լեզվով մեխանիզմը / ընթացակարգը)

## Ով ունի իրավունք
(Չափորոշիչների ցուցակ)

## Չափ / հաշվարկ
(Բոլոր գումարները կամ բանաձևը համատեքստից)

## Անհրաժեշտ փաստաթղթեր
(Ցուցակ)

## Ինչպես և որտեղ դիմել
(e-soc.am, ՄՍԾ կենտրոններ, թեժ գիծ 114)

## Ժամկետներ
(Եթե կան)

## Կարևոր նշումներ
(Բացառություններ, սահմանամերձ, աշխատող/չաշխատող և այլն՝ եթե կա համատեքստում)

## Աղբյուրներ
(Միայն համատեքստի վերնագրերը)

ՀԱՄԱՏԵՔՍՏ.
{context_str}
{hist_hy}

ՔԱՂԱՔԱՑՈՒ ՀԱՐՑ.
{query}

Գրեք ամբողջական պատասխանը պարզ հայերենով՝"""

    def _parse_gemini_answer(self, data: dict) -> tuple[str, str]:
        """Returns (answer_text, finish_reason)."""
        candidates = data.get("candidates") or []
        if not candidates:
            return "", "NO_CANDIDATES"
        c0 = candidates[0]
        finish = str(c0.get("finishReason") or c0.get("finish_reason") or "")
        parts = c0.get("content", {}).get("parts", [])
        answer = ""
        for part in parts:
            if not part.get("thought", False):
                answer += part.get("text", "")
        return answer.strip(), finish

    def _generate_with_gemini(self, system_prompt: str) -> str:
        """Try multiple Gemini models with light retries on 5xx/timeouts."""
        if not self.use_gemini:
            return ""
        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "generationConfig": {
                "temperature": 0.15,
                "maxOutputTokens": 8192,
                # gemini-2.5* may spend tokens on hidden "thinking" and hit MAX_TOKENS early
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }
        for model in GEMINI_GENERATE_MODELS:
            for attempt in range(1, GEMINI_MAX_RETRIES + 1):
                try:
                    print(f"Querying Gemini model={model} attempt={attempt}…")
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{model}:generateContent?key={GEMINI_API_KEY}"
                    )
                    r = requests.post(url, json=payload, timeout=90)
                    if r.status_code == 200:
                        answer, finish = self._parse_gemini_answer(r.json())
                        if answer:
                            print(f"Gemini OK via {model} finish={finish} len={len(answer)}")
                            # Treat MAX_TOKENS as usable but caller may enrich
                            return answer
                        print(f"Gemini {model}: empty candidates finish={finish}")
                    elif r.status_code in (429, 500, 502, 503, 504):
                        print(f"Gemini {model} status {r.status_code}; retrying…")
                        continue
                    else:
                        err_snippet = r.text[:300]
                        print(f"Gemini {model} status {r.status_code}: {err_snippet}")
                        if "image input" in err_snippet.lower() and "not support" in err_snippet.lower():
                            print(f"  ↳ Image file reference detected in context text — corpus may contain image filenames")
                        break  # non-retryable for this model
                except requests.Timeout:
                    print(f"Gemini {model} timeout on attempt {attempt}")
                except Exception as e:
                    print(f"Gemini {model} error: {e}")
                    break
        return ""

    def _generate_with_ollama(self, system_prompt: str) -> str:
        print("Falling back to local Ollama…")
        try:
            url = f"{OLLAMA_HOST}/api/generate"
            payload = {
                "model": OLLAMA_MODEL,
                "prompt": system_prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                return (r.json().get("response") or "").strip()
            print(f"Ollama status {r.status_code}")
        except Exception as e:
            print(f"Ollama generate error: {e}")
        return ""

    def generate_response(
        self,
        query: str,
        user_lang: str = "hy",
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        from fidelity import (
            evaluate_grounding,
            is_answer_incomplete,
            log_qa_event,
        )

        # Expand query with last user turn terms for follow-ups ("իսկ չափը?")
        search_query = query
        if history:
            prior_user = [
                (t.get("content") or "").strip()
                for t in history
                if (t.get("role") or "").lower() == "user" and (t.get("content") or "").strip()
            ]
            if prior_user and len(query.split()) <= 6:
                search_query = prior_user[-1] + " " + query

        relevant = self.retrieve(search_query, top_n=12)
        context_parts = []
        for c in relevant:
            src = c.get("source_url") or ""
            art = c.get("article") or ""
            header = f"[{c.get('doc_type', 'doc')}] {c.get('title', '')}"
            if art:
                header += f" | {art}"
            if src:
                header += f" | {src}"
            # Give model more room per chunk for complete answers
            text = _strip_image_refs(c.get("text") or "")
            if len(text) > 2500:
                text = text[:2500] + "…"
            context_parts.append(f"{header}\n{text}")
        context_str = "\n\n---\n\n".join(context_parts) if context_parts else "(no context)"

        system_prompt = self._prompt(query, context_str, user_lang, history=history)
        sources = self._build_sources(relevant)
        follow_ups = self._follow_ups(query, user_lang, relevant)

        answer = ""
        mode = "none"

        if self.use_gemini:
            answer = self._generate_with_gemini(system_prompt)
            if answer:
                mode = "gemini"
                # Retry once if truncated / incomplete
                if is_answer_incomplete(answer):
                    print("Answer looks incomplete — regenerating with stricter finish instruction…")
                    retry_prompt = system_prompt + (
                        "\n\nIMPORTANT: Your previous draft was incomplete. "
                        "Rewrite the FULL answer. Complete every section. Do not stop mid-sentence."
                        if user_lang == "en"
                        else "\n\nԿԱՐևՈՐ. Նախորդ տարբերակը կիսատ էր։ Վերագրեք ԱՄԲՈՂՋԱԿԱՆ պատասխանը։ Ավարտեք բոլոր բաժինները։ Մի կանգնեք նախադասության կեսից։"
                    )
                    retry = self._generate_with_gemini(retry_prompt)
                    if retry and len(retry) > len(answer):
                        answer = retry

        if not answer:
            answer = self._generate_with_ollama(system_prompt)
            if answer:
                mode = "ollama"

        if not answer and relevant:
            answer = self._extractive_answer(query, relevant, user_lang)
            mode = "extractive"

        if not answer:
            if user_lang == "en":
                answer = (
                    "Sorry, no matching program information was found. "
                    "Please call Unified Social Service hotline 114 or visit e-soc.am."
                )
            else:
                answer = (
                    "Ցավոք, համապատասխան տեղեկատվություն չի գտնվել։ "
                    "Խնդրում ենք զանգահարել ՄՍԾ թեժ գիծ 114 կամ այցելել e-soc.am։"
                )
            mode = "empty"

        # If generative answer is thin/truncated, replace or heavily enrich from corpus
        if mode in ("gemini", "ollama") and is_answer_incomplete(answer) and relevant:
            extract = self._extractive_answer(query, relevant, user_lang)
            # Prefer full extractive guide when model cut off badly
            if len(answer) < 400:
                answer = extract
                mode = mode + "→extractive"
            else:
                if user_lang == "en":
                    answer = (
                        answer.rstrip()
                        + "\n\n---\n\n## Full details from official materials\n\n"
                        + extract
                    )
                else:
                    answer = (
                        answer.rstrip()
                        + "\n\n---\n\n## Ամբողջական մանրամասներ պաշտոնական նյութերից\n\n"
                        + extract
                    )
                mode = mode + "+extractive"

        fidelity = evaluate_grounding(answer, context_str)

        def _log_event():
            try:
                log_qa_event({
                    "query": query,
                    "lang": user_lang,
                    "mode": mode,
                    "answer_preview": answer[:400],
                    "answer_len": len(answer),
                    "sources": [s.get("title") for s in sources[:6]],
                    "chunks_used": len(relevant),
                    "vector_search": self.vector_enabled,
                    **fidelity,
                })
            except Exception as e:
                print(f"QA log error: {e}")

        # Logging (and the optional semantic grounding branch inside it) should not
        # block returning the answer to the user.
        threading.Thread(target=_log_event, daemon=True).start()

        return {
            "answer": answer,
            "sources": sources,
            "vector_search": self.vector_enabled,
            "follow_ups": follow_ups,
            "fidelity": fidelity,
            "generation_mode": mode,
        }

    def _extractive_answer(
        self, query: str, chunks: list[dict[str, Any]], user_lang: str
    ) -> str:
        """Rich structured answer from top chunks when LLM is offline/weak."""
        # Prefer summary docs first for readability, then legal
        summaries = [c for c in chunks if c.get("doc_type") == "summary"]
        legals = [c for c in chunks if c.get("doc_type") == "legal"]
        ordered = (summaries + legals) or chunks

        def clean(t: str) -> str:
            t = re.sub(r"^(Ծրագիր|Ակտ|Նկարագրություն)՝\s*", "", t or "", flags=re.M)
            return t.strip()

        primary = clean(ordered[0].get("text") or "")[:2200]
        extra_blocks = []
        for c in ordered[1:5]:
            block = clean(c.get("text") or "")[:900]
            if block:
                title = c.get("title") or "Source"
                extra_blocks.append(f"**{title}**\n{block}")

        if user_lang == "en":
            parts = [
                "## Short answer",
                f"Here is what official materials say about **«{query}»**:",
                "",
                primary,
                "",
                "## How the program works",
                "See the rules and steps in the materials above. Details may depend on your exact situation.",
                "",
                "## How / where to apply",
                "- Online: **e-soc.am**",
                "- In person: Unified Social Service (USS) territorial center",
                "- Hotline: **114**",
            ]
            if extra_blocks:
                parts += ["", "## Additional official excerpts", ""] + [
                    b + "\n" for b in extra_blocks
                ]
            parts += [
                "",
                "## Sources",
                *[f"- {c.get('title')}" for c in ordered[:5]],
            ]
            return "\n".join(parts)

        parts = [
            "## Կարճ պատասխան",
            f"Ձեր հարցի (**«{query}»**) վերաբերյալ պաշտոնական նյութերից.",
            "",
            primary,
            "",
            "## Ինչպես է աշխատում ծրագիրը",
            "Տե՛ս վերևի կանոններն ու քայլերը։ Ձեր կոնկրետ իրավիճակից կախված մանրամասները կարող են տարբերվել։",
            "",
            "## Ինչպես և որտեղ դիմել",
            "- Առցանց՝ **e-soc.am**",
            "- Անձամբ՝ Միասնական սոցիալական ծառայության (ՄՍԾ) տարածքային կենտրոն",
            "- Թեժ գիծ՝ **114**",
        ]
        if extra_blocks:
            parts += ["", "## Լրացուցիչ պաշտոնական հատվածներ", ""] + [
                b + "\n" for b in extra_blocks
            ]
        parts += [
            "",
            "## Աղբյուրներ",
            *[f"- {c.get('title')}" for c in ordered[:5]],
        ]
        return "\n".join(parts)


if __name__ == "__main__":
    engine = RAGEngine()
    res = engine.generate_response("ընտանեկան նպաստ չափորոշիչներ")
    print(json.dumps(res, ensure_ascii=False, indent=2)[:2000])

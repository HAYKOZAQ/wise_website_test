"""
WISE Foundation — MLSA Social Programs RAG Engine
Modular hybrid vector + keyword retrieval over citizen summaries and ARLIS legal acts.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from collections import defaultdict
from functools import lru_cache
from typing import Any, Optional

import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Core & LLM modules
from core.config import settings
from llm.gemini import gemini_client, GeminiClient
from llm.ollama import ollama_client, OllamaClient
from llm.prompts import (
    LEGAL_QUERY_HINTS,
    SUMMARY_QUERY_HINTS,
    strip_image_refs,
    build_rag_prompt,
    build_follow_ups,
    expand_colloquial_query,
    reorder_context_chunks,
)
from retrieval.hybrid import (
    canonical_act_id,
    query_prefers_legal,
    query_prefers_summary,
    diversify_and_pick,
)

try:
    from rag_index import RAGIndex
except ImportError:
    from backend.rag_index import RAGIndex  # type: ignore

try:
    from reranker import get_reranker
except ImportError:
    from backend.reranker import get_reranker  # type: ignore


# Expose configuration constants for backward compatibility
GEMINI_API_KEY = settings.gemini_api_key
OLLAMA_HOST = settings.ollama_host
OLLAMA_MODEL = settings.ollama_model
USE_LOCAL_EMBEDDER = settings.use_local_embedder
USE_RERANKER = settings.use_reranker
HYBRID_SEMANTIC_WEIGHT = settings.hybrid_semantic_weight
QUERY_EXPANSION = settings.query_expansion
GEMINI_GENERATE_MODELS = settings.gemini_generate_models
GEMINI_MAX_RETRIES = settings.gemini_max_retries
GEMINI_DEADLINE_SEC = settings.gemini_deadline_sec
GEMINI_TIMEOUT_SEC = settings.gemini_timeout_sec


def _strip_image_refs(text: str) -> str:
    return strip_image_refs(text)


class RAGEngine:
    """Orchestrator for document indexing, hybrid retrieval, and grounded response generation."""

    def __init__(self):
        self.documents: list[dict[str, Any]] = []
        self.document_count = 0
        self.doc_type_counts: dict[str, int] = {}
        self.chunks: list[dict[str, Any]] = []
        self.embeddings: list[tuple[int, list[float]]] = []
        self.vector_enabled = False
        self.vector_backend = "none"
        self.use_gemini = gemini_client.is_available
        self.corpus_hash = ""
        self.legal_acts = 0
        self.cache_ok = False
        self._tfidf = None
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
                self.document_count = len(self.documents)
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
                self.doc_type_counts = by_type
                print(
                    f"Loaded {len(self.documents)} documents from {candidate} "
                    f"(legal acts≈{self.legal_acts}, by_type={by_type})."
                )
                return
            except Exception as e:
                print(f"Warning: failed to load {candidate}: {e}")
                last_error = e

        if not candidates:
            print("Error: no mlsa_programs.json found")
        else:
            print(f"Error loading social programs JSON: {last_error}")
        self.documents = []
        self.document_count = 0
        self.doc_type_counts = {}

    def _split_into_windows(self, text: str, max_chars: int = 900, overlap: int = 150) -> list[str]:
        text = (text or "").strip()
        if len(text) <= max_chars:
            return [text] if text else []
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text]
        chunks: list[str] = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) + 2 <= max_chars:
                current = f"{current}\n\n{p}".strip() if current else p
            else:
                if current:
                    chunks.append(current)
                if len(p) > max_chars:
                    sentences = re.split(r'(?<=[.!?։])\s+', p)
                    sub_curr = ""
                    for s in sentences:
                        if len(sub_curr) + len(s) + 1 <= max_chars:
                            sub_curr = f"{sub_curr} {s}".strip() if sub_curr else s
                        else:
                            if sub_curr:
                                chunks.append(sub_curr)
                            sub_curr = s
                    if sub_curr:
                        chunks.append(sub_curr)
                    current = ""
                else:
                    current = p
        if current:
            chunks.append(current)
        return chunks if chunks else [text]

    def build_index(self):
        self.chunks = []
        for doc_id, doc in enumerate(self.documents):
            title = doc.get("title", "")
            content = doc.get("content", "")
            doc_type = doc.get("doc_type", "summary")
            if not content:
                continue

            if doc_type in ("legal", "pdf", "web"):
                pieces = self._split_into_windows(content, max_chars=900, overlap=150)
            else:
                pieces = self._split_into_windows(content.strip(), max_chars=1200, overlap=200)

            for p in pieces:
                cleaned = strip_image_refs(p)
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
        self.documents = []

    def _cache_path(self) -> str:
        return os.path.join(self._backend_dir(), "data", "embeddings_cache.json")

    def _enable_local_tfidf(self) -> None:
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
        force_embed = settings.force_embed
        max_auto = settings.auto_embed_max_chunks
        prefer_local = settings.use_local_tfidf

        # Try persisted FAISS + BM25 index first
        self._rag_index = RAGIndex(self._backend_dir())
        if self._rag_index.load(self.corpus_hash):
            self.chunks = self._rag_index.chunks
            self.embeddings = []
            self.vector_enabled = self._rag_index.faiss_index is not None
            self.cache_ok = True
            self.vector_backend = "faiss_bm25" if self.vector_enabled else "bm25"
            print(
                f"Loaded persisted index ({len(self._rag_index.chunks)} chunks, "
                f"dense={'on' if self.vector_enabled else 'off'})."
            )
            return

        embeddings: list[tuple[int, list[float]]] = []
        backend_name = "none"

        if settings.use_local_embedder:
            try:
                embeddings = self._embed_with_local_backend()
                backend_name = "local_embedder" if embeddings else "none"
            except Exception as e:
                print(f"Local embedder unavailable: {e}")

        if embeddings:
            try:
                self._rag_index.build(self.chunks, embeddings, self.corpus_hash)
                self.vector_enabled = self._rag_index.faiss_index is not None
                self.vector_backend = "faiss_bm25" if self.vector_enabled else "bm25"
                self.cache_ok = True
                print(f"Constructed hybrid index ({len(self.chunks)} chunks, dense={self.vector_enabled}).")
                return
            except Exception as e:
                print(f"Failed constructing index from embeddings: {e}")

        if prefer_local:
            try:
                self._enable_local_tfidf()
                return
            except Exception as e:
                print(f"Local TF-IDF fallback failed: {e}")

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"\b\w{3,}\b", text.lower()))

    def _keyword_scores(self, query: str) -> list[tuple[int, float]]:
        if not self.chunks:
            return []
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return []
        scores = []
        for c in self.chunks:
            t_tokens = self._tokenize(c["text"])
            match = len(q_tokens & t_tokens)
            if match > 0:
                scores.append((c["chunk_id"], float(match)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    def _embed_query(self, query: str) -> list[float] | None:
        if settings.use_local_embedder:
            try:
                from local_embedder import get_local_embedder
                return get_local_embedder().embed_one(query)
            except Exception:
                pass
        return None

    def _embed_queries_batch(self, queries: list[str]) -> list[list[float] | None]:
        if settings.use_local_embedder:
            try:
                from local_embedder import get_local_embedder
                embedder = get_local_embedder()
                vectors = embedder.embed(queries)
                if len(vectors) == len(queries):
                    return [list(v) for v in vectors]
            except Exception:
                pass
        return [None] * len(queries)

    def _vector_scores(self, query: str) -> list[tuple[int, float]]:
        if not self.vector_enabled or not self.embeddings:
            return []
        q_vec = self._embed_query(query)
        if not q_vec:
            return []
        scores = []
        for chunk_id, emb in self.embeddings:
            dot = sum(a * b for a, b in zip(q_vec, emb))
            sim = max(0.0, dot)
            scores.append((chunk_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores

    @staticmethod
    def _canonical_act_id(act_id: Any) -> str | None:
        return canonical_act_id(act_id)

    def _query_prefers_legal(self, query: str) -> bool:
        return query_prefers_legal(query)

    def _query_prefers_summary(self, query: str) -> bool:
        return query_prefers_summary(query)

    def _expand_query(self, query: str) -> list[str]:
        # Step 1: Add domain-specific colloquial expansions
        variants = expand_colloquial_query(query)
        if not settings.query_expansion or len(query.split()) > 15:
            return variants
        prompt = (
            "Rewrite this question in Armenian in 1 different way to help search a database. "
            "Return ONLY the rewritten question, no explanation.\n\nQuestion: "
        ) + query
        try:
            rewritten = ""
            if self.use_gemini:
                rewritten = gemini_client.generate(prompt)
            if not rewritten:
                rewritten = ollama_client.generate(prompt)
            if rewritten:
                clean = rewritten.strip().split("\n")[0].strip()
                if clean and clean.lower() != query.lower() and clean not in variants:
                    variants.append(clean)
        except Exception:
            pass
        return variants

    def _merge_rank(self, query: str, top_n: int = 8) -> list[dict[str, Any]]:
        prefer_legal = self._query_prefers_legal(query)
        prefer_summary = self._query_prefers_summary(query)
        initial_k = max(top_n * 3, 24)

        query_variants = self._expand_query(query)
        candidate_scores: dict[int, float] = {}
        use_hybrid = self._rag_index is not None and self._rag_index.is_ready()
        dense_available = use_hybrid and self._rag_index.faiss_index is not None
        variant_vectors: list[list[float] | None] = []
        if dense_available:
            variant_vectors = self._embed_queries_batch(query_variants)

        for i, q in enumerate(query_variants):
            if use_hybrid:
                q_vec = variant_vectors[i] if dense_available and i < len(variant_vectors) else None
                pairs = self._rag_index.search_hybrid(
                    q, q_vec, k=initial_k, semantic_weight=settings.hybrid_semantic_weight
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
                    score = 0.50 * vmap.get(cid, 0.0) + 0.50 * kmap.get(cid, 0.0)
                    pairs.append((cid, score))
                pairs.sort(key=lambda x: x[1], reverse=True)
                pairs = pairs[:initial_k]

            for cid, score in pairs:
                candidate_scores[cid] = max(candidate_scores.get(cid, 0.0), score)

        acts_with_legal: set[str] = set()
        for ch in self.chunks:
            if (ch.get("doc_type") or "") == "legal":
                ca = canonical_act_id(ch.get("act_id"))
                if ca:
                    acts_with_legal.add(ca)

        candidates: list[dict[str, Any]] = []
        for cid, score in candidate_scores.items():
            chunk = self.chunks[cid]
            dtype = chunk.get("doc_type") or "summary"
            ca = canonical_act_id(chunk.get("act_id"))
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

        if settings.use_reranker and candidates:
            if self._reranker is None:
                self._reranker = get_reranker()
            candidates = self._reranker.rerank(query, candidates, top_k=max(top_n * 2, 16))

        picked = diversify_and_pick(candidates, acts_with_legal, top_n=top_n)

        if not picked:
            kw = self._keyword_scores(query)
            for cid, _ in kw[:top_n]:
                picked.append(self.chunks[cid])

        return picked

    def retrieve(self, query: str, top_n: int = 8) -> list[dict[str, Any]]:
        if not self.chunks:
            return []
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
            if not url and act_id and not str(act_id).startswith(("pdf:", "web:")):
                url = f"https://www.arlis.am/hy/acts/{act_id}"
            sources.append({
                "title": c.get("title") or "Անանուն փաստաթուղթ",
                "doc_type": c.get("doc_type") or "summary",
                "category": c.get("category"),
                "act_id": act_id,
                "article": c.get("article"),
                "source_url": url,
            })
        return sources[:8]

    def _follow_ups(self, query: str, lang: str, chunks: list[dict[str, Any]]) -> list[str]:
        return build_follow_ups(query, lang, chunks)

    def _prompt(
        self,
        query: str,
        context_str: str,
        user_lang: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        return build_rag_prompt(query, context_str, user_lang, history)

    def _generate_with_gemini(self, system_prompt: str) -> str:
        return gemini_client.generate(system_prompt)

    def _generate_with_ollama(self, system_prompt: str) -> str:
        return ollama_client.generate(system_prompt)

    def _extractive_answer(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        user_lang: str = "hy",
    ) -> str:
        if not chunks:
            if user_lang == "en":
                return "No matching materials were found in the database."
            if user_lang == "ru":
                return "В базе данных не найдено подходящих материалов."
            return "Տվյալների բազայում համապատասխան նյութեր չեն գտնվել:"

        lines = []
        if user_lang == "en":
            lines.append("### Relevant Information")
        elif user_lang == "ru":
            lines.append("### Найденная информация")
        else:
            lines.append("### Համապատասխան տեղեկատվություն")

        for c in chunks[:4]:
            t = c.get("title") or ""
            text = (c.get("text") or "").strip()
            lines.append(f"**{t}**\n{text[:500]}...\n")
        return "\n\n".join(lines)

    def generate_response(
        self,
        query: str,
        user_lang: str = "hy",
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        from fidelity import evaluate_grounding, is_answer_incomplete, log_qa_event

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
        ordered_chunks = reorder_context_chunks(relevant)
        context_parts = []
        for c in ordered_chunks:
            src = c.get("source_url") or ""
            art = c.get("article") or ""
            header = f"[{c.get('doc_type', 'doc')}] {c.get('title', '')}"
            if art:
                header += f" — {art}"
            if src:
                header += f" ({src})"
            context_parts.append(f"{header}\n{c.get('text', '')}")

        context_str = "\n\n---\n\n".join(context_parts)
        prompt = self._prompt(query, context_str, user_lang, history=history)

        answer = ""
        mode = "none"

        if self.use_gemini:
            answer = self._generate_with_gemini(prompt)
            if answer:
                mode = "gemini"

        if not answer:
            answer = self._generate_with_ollama(prompt)
            if answer:
                mode = "ollama"

        if not answer:
            answer = self._extractive_answer(query, relevant, user_lang=user_lang)
            mode = "extractive"

        sources = self._build_sources(relevant)
        follow_ups = self._follow_ups(query, user_lang, relevant)
        fidelity = evaluate_grounding(answer, context_str) if context_str else None

        try:
            log_qa_event({
                "query": query,
                "mode": mode,
                "answer_preview": answer[:400],
                "sources_count": len(sources),
                "fidelity": fidelity,
            })
        except Exception:
            pass

        return {
            "answer": answer,
            "sources": sources,
            "vector_search": self.vector_enabled,
            "follow_ups": follow_ups,
            "fidelity": fidelity,
            "generation_mode": mode,
        }


# Global engine singleton and lock for thread safety
rag_lock = threading.Lock()
rag_engine_instance: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    global rag_engine_instance
    with rag_lock:
        if rag_engine_instance is None:
            rag_engine_instance = RAGEngine()
        return rag_engine_instance


def reload_rag_engine() -> dict[str, Any]:
    global rag_engine_instance
    with rag_lock:
        rag_engine_instance = RAGEngine()
        return {
            "ok": True,
            "documents": rag_engine_instance.document_count,
            "chunks": len(rag_engine_instance.chunks),
            "legal_acts": rag_engine_instance.legal_acts,
        }

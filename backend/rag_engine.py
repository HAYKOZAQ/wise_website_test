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
    get_standard_refusal,
)
from retrieval.hybrid import (
    canonical_act_id,
    query_prefers_legal,
    query_prefers_summary,
    diversify_and_pick,
    reciprocal_rank_fusion,
    compute_retrieval_confidence,
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

        # Check for structural section breaks: Articles, numbered clauses, and bullet points
        section_matches = list(re.finditer(r"(?:\n|^)(?:Հոդված\s+\d+|Article\s+\d+|Статья\s+\d+|\d+\.\s+[Ա-ՖA-ZА-Я])", text))
        if len(section_matches) >= 2:
            raw_sections: list[str] = []
            prev_idx = 0
            for m in section_matches[1:]:
                raw_sections.append(text[prev_idx:m.start()].strip())
                prev_idx = m.start()
            raw_sections.append(text[prev_idx:].strip())

            chunks: list[str] = []
            for sec in raw_sections:
                if not sec:
                    continue
                if len(sec) <= max_chars:
                    chunks.append(sec)
                else:
                    # Further split large sections by paragraphs
                    paragraphs = [p.strip() for p in sec.split("\n\n") if p.strip()]
                    cur = ""
                    for p in paragraphs:
                        if len(cur) + len(p) + 2 <= max_chars:
                            cur = f"{cur}\n\n{p}".strip() if cur else p
                        else:
                            if cur:
                                chunks.append(cur)
                            cur = p
                    if cur:
                        chunks.append(cur)
            if chunks:
                return chunks

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
            category = doc.get("category") or ""
            article = doc.get("article") or ""
            if not content:
                continue

            if doc_type in ("legal", "pdf", "web"):
                pieces = self._split_into_windows(content, max_chars=900, overlap=150)
            else:
                pieces = self._split_into_windows(content.strip(), max_chars=1200, overlap=200)

            for p in pieces:
                cleaned = strip_image_refs(p)
                meta_tag = f"[{title}"
                if article:
                    meta_tag += f" | {article}"
                if category:
                    meta_tag += f" | {category}"
                meta_tag += "]"

                if doc_type == "legal":
                    chunk_text = f"Ակտ՝ {meta_tag}\n{cleaned}"
                elif doc_type == "pdf":
                    chunk_text = f"Պաշտոնական PDF՝ {meta_tag}\n{cleaned}"
                elif doc_type == "web":
                    chunk_text = f"Պաշտոնական էջ՝ {meta_tag}\n{cleaned}"
                else:
                    chunk_text = f"Ծրագիր՝ {meta_tag}\nՆկարագրություն՝ {cleaned}"

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

        if settings.use_local_embedder and (force_embed or len(self.chunks) <= max_auto):
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
        else:
            try:
                self._rag_index.build_sparse(self.chunks, self.corpus_hash)
                self.vector_enabled = False
                self.vector_backend = "bm25"
                self.cache_ok = True
                print(f"Constructed compact BM25 index ({len(self.chunks)} chunks).")
                return
            except Exception as e:
                print(f"Failed constructing sparse index: {e}")

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

        variant_rankings: list[list[tuple[int, float]]] = []
        for i, q in enumerate(query_variants):
            if use_hybrid:
                q_vec = variant_vectors[i] if dense_available and i < len(variant_vectors) else None
                pairs = self._rag_index.search_hybrid(
                    q, q_vec, k=initial_k, semantic_weight=settings.hybrid_semantic_weight
                )
            else:
                vec = self._vector_scores(q)
                kw = self._keyword_scores(q)
                pairs = reciprocal_rank_fusion([vec[:40], kw[:40]], weights=[0.5, 0.5])[:initial_k]
            variant_rankings.append(pairs)

        merged_pairs = reciprocal_rank_fusion(variant_rankings)
        for cid, score in merged_pairs:
            candidate_scores[cid] = score

        acts_with_legal: set[str] = set()
        for ch in self.chunks:
            if (ch.get("doc_type") or "") == "legal":
                ca = canonical_act_id(ch.get("act_id"))
                if ca:
                    acts_with_legal.add(ca)

        candidates: list[dict[str, Any]] = []
        for cid, score in candidate_scores.items():
            if cid < 0 or cid >= len(self.chunks) or score <= 0.0:
                continue
            chunk = self.chunks[cid]
            dtype = chunk.get("doc_type") or "summary"
            ca = canonical_act_id(chunk.get("act_id"))
            multiplier = 1.0
            if dtype == "legal":
                multiplier += 0.20
            elif dtype == "pdf":
                if ca and ca in acts_with_legal:
                    multiplier -= 0.30
                else:
                    multiplier += 0.10
            if prefer_legal and dtype == "legal":
                multiplier += 0.30
            if prefer_legal and dtype == "pdf" and not (ca and ca in acts_with_legal):
                multiplier += 0.15
            if prefer_summary and dtype == "summary":
                multiplier += 0.30
            if dtype == "summary" and not prefer_legal:
                multiplier += 0.10
            if dtype == "web" and not prefer_legal:
                multiplier += 0.08
            pr = chunk.get("priority") or 2
            multiplier += max(0, (3 - pr)) * 0.05

            candidates.append({**chunk, "hybrid_score": score * multiplier})

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
        confidence: float = 0.5,
    ) -> str:
        if not chunks or confidence < 0.25:
            return get_standard_refusal(user_lang)

        lines = []
        if user_lang == "en":
            lines.append("### Relevant Official Information")
        elif user_lang == "ru":
            lines.append("### Найденная официальная информация")
        else:
            lines.append("### Համապատասխան պաշտոնական տեղեկատվություն")

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
        confidence = compute_retrieval_confidence(search_query, relevant)

        # Tier 3 & 5 Pre-LLM Guardrail:
        # If retrieval confidence is zero or below threshold, return safe 114 refusal
        if not relevant or confidence < 0.10:
            refusal_text = get_standard_refusal(user_lang)
            fidelity = evaluate_grounding(refusal_text, "")
            return {
                "answer": refusal_text,
                "sources": [],
                "vector_search": self.vector_enabled,
                "follow_ups": [],
                "fidelity": fidelity,
                "generation_mode": "guardrail_refusal",
                "retrieval_confidence": confidence,
            }
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
            answer = self._extractive_answer(query, relevant, user_lang=user_lang, confidence=confidence)
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
            "retrieval_confidence": confidence,
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

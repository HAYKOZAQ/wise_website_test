"""
Hybrid retrieval logic, reciprocal rank fusion, query routing, and result diversification.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any, Callable

from core.config import settings
from llm.prompts import LEGAL_QUERY_HINTS, SUMMARY_QUERY_HINTS


def canonical_act_id(act_id: Any) -> str | None:
    """Extract standard numeric act id from strings or numbers."""
    if not act_id:
        return None
    s = str(act_id)
    m = re.search(r"(\d{4,})", s)
    return m.group(1) if m else s


def query_prefers_legal(query: str) -> bool:
    q = query.lower()
    return any(h in q for h in LEGAL_QUERY_HINTS)


def query_prefers_summary(query: str) -> bool:
    q = query.lower()
    return any(h in q for h in SUMMARY_QUERY_HINTS)


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[int, float]]],
    weights: list[float] | None = None,
    k: int = 60,
) -> list[tuple[int, float]]:
    """
    Standard Reciprocal Rank Fusion (RRF) combining sparse and dense rankings.
    RRF(d) = sum_i( weight_i / (k + rank_i(d)) )
    """
    if not ranked_lists:
        return []
    if weights is None:
        weights = [1.0 / len(ranked_lists)] * len(ranked_lists)

    scores: dict[int, float] = defaultdict(float)
    for ranked, weight in zip(ranked_lists, weights):
        for rank, (doc_id, _) in enumerate(ranked, start=1):
            scores[doc_id] += weight / (k + rank)

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_scores


_RETRIEVAL_STOP_WORDS = {
    "the", "and", "for", "how", "what", "with", "from", "this", "that", "are", "was", "can", "you",
    "որ", "եւ", "և", "ինչ", "ինչպես", "համար", "այս", "այն", "մասին", "նաև", "եթե", "որտեղ", "երբ", "կամ", "նրա", "իր", "ինչքան", "որքան",
    "что", "как", "для", "или", "где", "когда", "если", "это", "этот", "эти", "все",
}


def compute_retrieval_confidence(
    query: str,
    picked_chunks: list[dict[str, Any]],
    min_keyword_overlap: int = 1,
) -> float:
    """
    Evaluates whether the retrieved chunks have genuine lexical/semantic support for the query.
    Returns confidence between 0.0 and 1.0.
    """
    if not picked_chunks or not query or not query.strip():
        return 0.0

    raw_tokens = re.findall(r"[\w\u0531-\u0587]{2,}", query.lower())
    q_tokens = {t for t in raw_tokens if t not in _RETRIEVAL_STOP_WORDS and len(t) >= 3}
    if not q_tokens:
        q_tokens = set(raw_tokens)
        if not q_tokens:
            return 0.0

    # Calculate token overlap across top chunks
    combined_chunk_text = " ".join((c.get("text") or "").lower() for c in picked_chunks[:5])
    chunk_tokens = set(re.findall(r"[\w\u0531-\u0587]{3,}", combined_chunk_text))
    overlap = len(q_tokens & chunk_tokens)

    # For queries with 3+ content tokens, require at least 2 distinct token matches
    if len(q_tokens) >= 3 and overlap < 2:
        return 0.0

    overlap_ratio = overlap / len(q_tokens)
    if overlap_ratio < 0.35:
        return 0.0

    top_score = float(picked_chunks[0].get("hybrid_score", 0.0))

    confidence = 0.5 * min(1.0, top_score * 10.0) + 0.5 * overlap_ratio
    return round(max(0.0, min(1.0, confidence)), 3)


def diversify_and_pick(
    candidates: list[dict[str, Any]],
    acts_with_legal: set[str],
    top_n: int = 8,
) -> list[dict[str, Any]]:
    """Applies diversity filtering across legal acts, titles, and document types."""
    picked: list[dict[str, Any]] = []
    act_counts: dict[str, int] = defaultdict(int)
    title_counts: dict[str, int] = defaultdict(int)
    type_counts: dict[str, int] = defaultdict(int)
    legal_picked_acts: set[str] = set()

    def try_pick(chunk: dict[str, Any]) -> bool:
        cid = chunk["chunk_id"]
        ca = canonical_act_id(chunk.get("act_id"))
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

    return picked

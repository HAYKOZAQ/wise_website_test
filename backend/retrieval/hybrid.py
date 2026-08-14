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

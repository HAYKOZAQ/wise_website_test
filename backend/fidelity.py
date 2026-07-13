"""
Grounding / hallucination checks for RAG answers.

Compares factual-looking claims in the model answer against retrieved context.
Logs every evaluation so you can audit quality in the backend.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any


_NUM_CLAIM_RE = re.compile(
    r"(?:"
    r"\d{1,3}(?:[ \u00a0]?\d{3})+(?:\s*(?:ՀՀ\s*)?դրամ|դր\.?|AMD)?"
    r"|\d+(?:[.,]\d+)?\s*(?:%|տոկոս|տարի|ամիս|օր|դրամ|դր\.?)"
    r"|\d{2,6}"
    r")",
    re.IGNORECASE,
)


def _backend_data_dir() -> str:
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(d, exist_ok=True)
    return d


def extract_numeric_claims(text: str) -> list[str]:
    if not text:
        return []
    found = []
    seen = set()
    for m in _NUM_CLAIM_RE.finditer(text):
        raw = m.group(0).strip()
        digits = re.sub(r"\D", "", raw)
        if len(digits) < 2:
            continue
        if len(digits) == 2 and int(digits) > 80:
            if "տարի" not in raw and "ամիս" not in raw:
                continue
        key = re.sub(r"\D", "", raw)
        if key in seen:
            continue
        seen.add(key)
        found.append(raw)
    return found[:40]


# Always-safe public service facts (not treated as hallucinations)
_SAFE_CLAIMS = {"114", "e-soc", "esoc"}


def claim_supported(claim: str, context: str) -> bool:
    if not claim or not context:
        return False
    claim_l = claim.lower().strip()
    if claim_l in _SAFE_CLAIMS or re.sub(r"\D", "", claim) == "114":
        return True
    ctx_l = context.lower()
    if claim_l in ctx_l:
        return True
    digits = re.sub(r"\D", "", claim)
    if not digits:
        return False
    if digits in re.sub(r"\D", "", context):
        return True
    if len(digits) <= 3 and re.search(rf"(?<!\d){re.escape(digits)}(?!\d)", context):
        return True
    return False


def evaluate_grounding(answer: str, context: str) -> dict[str, Any]:
    claims = extract_numeric_claims(answer)
    if not claims:
        ans_tokens = set(re.findall(r"[\w\u0531-\u0587]{4,}", (answer or "").lower()))
        ctx_tokens = set(re.findall(r"[\w\u0531-\u0587]{4,}", (context or "").lower()))
        if not ans_tokens:
            score = 0.0
        else:
            score = len(ans_tokens & ctx_tokens) / max(len(ans_tokens), 1)
        score = max(0.0, min(1.0, score))
        risk = "low" if score >= 0.45 else ("medium" if score >= 0.25 else "high")
        return {
            "grounding_score": round(score, 3),
            "hallucination_rate": round(1.0 - score, 3),
            "risk": risk,
            "claims_total": 0,
            "claims_supported": 0,
            "claims_unsupported": 0,
            "supported_claims": [],
            "unsupported_claims": [],
            "method": "lexical_overlap",
        }

    supported = []
    unsupported = []
    for c in claims:
        if claim_supported(c, context):
            supported.append(c)
        else:
            unsupported.append(c)

    total = len(claims)
    n_sup = len(supported)
    score = n_sup / total if total else 1.0
    hall = 1.0 - score
    if hall <= 0.15:
        risk = "low"
    elif hall <= 0.4:
        risk = "medium"
    else:
        risk = "high"

    return {
        "grounding_score": round(score, 3),
        "hallucination_rate": round(hall, 3),
        "risk": risk,
        "claims_total": total,
        "claims_supported": n_sup,
        "claims_unsupported": len(unsupported),
        "supported_claims": supported,
        "unsupported_claims": unsupported,
        "method": "numeric_claim_check",
    }


def is_answer_incomplete(answer: str) -> bool:
    """Heuristic: truncated / too short / cut mid-sentence."""
    if not answer or len(answer.strip()) < 280:
        return True
    a = answer.strip()
    # ends mid-word without punctuation
    if a[-1] not in ".!?:…»\"'”)":
        if re.search(r"[\w\u0531-\u0587]{2,}$", a) and len(a) < 1500:
            return True
    if re.search(r"(Մինչև|մինչև|դրամ|տարեկան|Հոդված|Հայաստ)\s*$", a):
        return True
    headers = len(re.findall(r"^##\s+", a, re.M))
    if headers < 3 and len(a) < 900:
        return True
    low = a.lower()
    has_apply = any(x in low for x in ("դիմել", "e-soc", "մսծ", "114", "apply", "hotline"))
    if not has_apply and len(a) < 1500:
        return True
    return False


def log_qa_event(event: dict[str, Any]) -> str:
    path = os.path.join(_backend_data_dir(), "qa_eval_log.jsonl")
    event = dict(event)
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return path


def load_eval_stats(limit: int = 500) -> dict[str, Any]:
    path = os.path.join(_backend_data_dir(), "qa_eval_log.jsonl")
    if not os.path.exists(path):
        return {
            "entries": 0,
            "avg_grounding_score": None,
            "avg_hallucination_rate": None,
            "risk_counts": {"low": 0, "medium": 0, "high": 0},
            "recent": [],
        }

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    recent = rows[-limit:]
    rates = [r.get("hallucination_rate") for r in recent if r.get("hallucination_rate") is not None]
    grounds = [r.get("grounding_score") for r in recent if r.get("grounding_score") is not None]
    risks = {"low": 0, "medium": 0, "high": 0}
    for r in recent:
        k = r.get("risk") or "medium"
        if k in risks:
            risks[k] += 1

    def avg(xs):
        return round(sum(xs) / len(xs), 3) if xs else None

    preview = []
    for r in recent[-30:]:
        preview.append({
            "ts": r.get("ts"),
            "query": (r.get("query") or "")[:120],
            "grounding_score": r.get("grounding_score"),
            "hallucination_rate": r.get("hallucination_rate"),
            "risk": r.get("risk"),
            "claims_unsupported": r.get("claims_unsupported"),
            "answer_preview": (r.get("answer_preview") or "")[:160],
            "mode": r.get("mode"),
        })

    return {
        "entries": len(recent),
        "total_logged": len(rows),
        "avg_grounding_score": avg(grounds),
        "avg_hallucination_rate": avg(rates),
        "risk_counts": risks,
        "log_path": path,
        "recent": list(reversed(preview)),
    }


EVAL_CASES = [
    {
        "id": "childcare",
        "query": "մինչև 2 տարեկան երեխայի խնամքի նպաստ",
        "lang": "hy",
        "must_contain_any": ["նպաստ", "երեխա", "դրամ", "2"],
    },
    {
        "id": "family",
        "query": "ընտանեկան նպաստ չափորոշիչներ",
        "lang": "hy",
        "must_contain_any": ["ընտանեկան", "անապահով", "նպաստ"],
    },
    {
        "id": "pension",
        "query": "տարիքային կենսաթոշակ",
        "lang": "hy",
        "must_contain_any": ["կենսաթոշակ", "տարիք", "ստաժ"],
    },
    {
        "id": "electricity",
        "query": "էլեկտրաէներգիայի փոխհատուցում",
        "lang": "hy",
        "must_contain_any": ["էլեկտր", "փոխհատուց", "դրամ"],
    },
    {
        "id": "childbirth",
        "query": "երեխայի ծննդյան միանվագ նպաստ",
        "lang": "hy",
        "must_contain_any": ["ծննդ", "նպաստ", "դրամ"],
    },
    {
        "id": "unemployment",
        "query": "գործազրկության կարգավիճակ ինչպես ձևակերպել",
        "lang": "hy",
        "must_contain_any": ["գործազրկ", "ՄՍԾ", "աշխատանք"],
    },
    {
        "id": "displaced",
        "query": "Ղարաբաղից տեղահանվածների աջակցություն",
        "lang": "hy",
        "must_contain_any": ["տեղահան", "աջակց", "114"],
    },
    {
        "id": "disability",
        "query": "հաշմանդամության կենսաթոշակ",
        "lang": "hy",
        "must_contain_any": ["հաշմանդամ", "կենսաթոշակ"],
    },
]

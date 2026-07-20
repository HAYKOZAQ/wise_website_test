"""
Grounding / hallucination checks for RAG answers.

Compares factual-looking claims in the model answer against retrieved context.
Logs every evaluation so you can audit quality in the backend.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import threading
from datetime import datetime, timezone
from typing import Any


_semantic_model = None
_semantic_lock = threading.Lock()


def _get_semantic_model():
    """Return the shared local sentence-transformer model (loads once per process).

    Reuses the LocalSentenceEmbedder singleton so the same MiniLM instance serves
    both retrieval embeddings and grounding checks, cutting RAM ~in half.
    """
    global _semantic_model
    if _semantic_model is not None:
        return _semantic_model
    with _semantic_lock:
        if _semantic_model is not None:
            return _semantic_model
        try:
            from local_embedder import get_local_embedder

            embedder = get_local_embedder()
            embedder._load()
            _semantic_model = embedder._model
        except Exception:
            pass
    return _semantic_model


def _semantic_similarity(text1: str, text2: str) -> float:
    """Lightweight sentence-transformer cosine similarity if available."""
    model = _get_semantic_model()
    if model is None:
        return 0.0
    try:
        from sentence_transformers import util
        # Batch the two encodes to avoid two separate forward passes.
        embs = model.encode([text1, text2], convert_to_tensor=True)
        return float(util.cos_sim(embs[0], embs[1]))
    except Exception:
        return 0.0


def _split_sentences(text: str) -> list[str]:
    """Split on Armenian/English sentence terminators."""
    parts = re.split(r"(?<=[.!?:։])\s+", (text or "").strip())
    return [p.strip() for p in parts if p.strip()]


_UNIT_SUFFIX = (
    r"(?:դրամ|դր\.?|AMD|ՀՀ\s*դրամ|"
    r"տարի|տարեկան|ամիս|ամսական|օր|օրյա|միանվագ|"
    r"տոկոս|%|ամենամսյա|ամենամյա|ամսամեկ|ամսվա)"
)
_UNIT_PHRASE = _UNIT_SUFFIX + r"(?:\s+" + _UNIT_SUFFIX + r")*"

_NUM_CLAIM_RE = re.compile(
    r"(?:"
    r"\d{1,3}(?:[ \u00a0]?\d{3})+(?:[.,]\d+)?(?:\s*" + _UNIT_PHRASE + r")?"
    r"|\d+(?:[.,]\d+)?(?:\s*" + _UNIT_PHRASE + r")"
    r"|\d{2,6}"
    r")",
    re.IGNORECASE,
)


def _backend_data_dir() -> str:
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(d, exist_ok=True)
    return d


_QA_LOG_MAX_BYTES = 64 * 1024 * 1024  # 64 MB cap per log file



def _redact_event(event: dict[str, Any]) -> dict[str, Any]:
    """Strip or hash fields that can contain personal / welfare information."""
    event = dict(event)
    query = event.get("query") or ""
    # Never store any textual preview of the raw query: social-welfare questions
    # routinely contain names, IDs, ages, addresses, family composition, etc.
    if query:
        event["query_hash"] = hashlib.sha256(query.encode("utf-8")).hexdigest()
        event["query_len"] = len(query)
    event.pop("query_preview", None)
    event.pop("query", None)

    # Never store the answer text content: it may contain names, family details,
    # IDs, or other welfare-related PII. Keep length and a structural flag only.
    if "answer_preview" in event:
        event.pop("answer_preview")
    if "answer" in event:
        event["answer_len"] = len(str(event.pop("answer")))

    # Remove any direct PII that may have slipped in.
    event.pop("ip", None)
    event.pop("name", None)
    event.pop("email", None)
    event.pop("message", None)
    return event


# Frequency-related unit tokens take priority over currency so that
# "50000 դրամ ամսական" and "50000 դրամ տարեկան" are treated as distinct claims.
_FREQUENCY_UNITS = ("ամսական", "ամենամսյա", "ամսամեկ", "ամսվա", "ամիս",
                    "տարեկան", "ամենամյա", "տարի",
                    "օրյա", "օր", "միանվագ")
_CURRENCY_UNITS = ("դրամ", "դր.", "տոկոս", "%")
_UNIT_TOKENS = _FREQUENCY_UNITS + _CURRENCY_UNITS

# Morphological variants that should be treated as the same unit concept.
_UNIT_EQUIVALENTS: dict[str, tuple[str, ...]] = {
    "ամսական": ("ամսական", "ամենամսյա", "ամսամեկ", "ամսվա", "ամիս", "ամսում"),
    "ամիս": ("ամսական", "ամենամսյա", "ամսամեկ", "ամսվա", "ամիս", "ամսում"),
    "տարեկան": ("տարեկան", "ամենամյա", "տարի", "տարին", "տարեկանից", "տարեկանների"),
    "տարի": ("տարեկան", "ամենամյա", "տարի", "տարին", "տարեկանից", "տարեկանների"),
    "օրյա": ("օրյա", "օր", "օրում", "օրական"),
    "օր": ("օրյա", "օր", "օրում", "օրական"),
    "դրամ": ("դրամ", "դր.", "amd", "հհ դրամ"),
    "դր.": ("դրամ", "դր.", "amd", "հհ դրամ"),
    "տոկոս": ("տոկոս", "%"),
    "%": ("տոկոս", "%"),
}


def _claim_unit(raw: str) -> str:
    """Return the most specific unit token found in the raw claim, or ''."""
    low = raw.lower()
    for unit in _UNIT_TOKENS:
        if unit in low:
            return unit
    return ""


def _unit_matches(unit: str, context: str) -> bool:
    """Check whether the context contains the unit or an equivalent variant."""
    if not unit:
        return True
    ctx_l = context.lower()
    for equiv in _UNIT_EQUIVALENTS.get(unit, (unit,)):
        if equiv in ctx_l:
            return True
    return False


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
        # Don't drop 81-99 claims; let the context check decide support.
        unit = _claim_unit(raw)
        key = (digits, unit)
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
    # Exact substring match is safe for claims that contain words/context,
    # but a bare digit like "63" must not be considered supported by "63,500".
    if claim_l in ctx_l and not re.fullmatch(r"\d+", claim_l):
        return True
    digits = re.sub(r"\D", "", claim)
    if not digits:
        return False

    unit = _claim_unit(claim)
    ctx_digits = re.sub(r"\D", "", context)

    # If the claim has a unit (currency/frequency), require that unit (or an
    # equivalent variant) to appear in the context too. This catches
    # "50000 դրամ ամսական" vs "50000 դրամ տարեկան" while allowing "տարեկան" vs "տարին".
    if unit and not _unit_matches(unit, context):
        return False

    # Short digit runs (<=3 digits, e.g. ages 63, 85) must match as a standalone
    # number in the context so "63" is not considered supported by "63,500".
    if len(digits) <= 3:
        return bool(re.search(rf"(?<![\d.,]){re.escape(digits)}(?![\d.,])", context))

    # Longer digit runs (>=4 digits, e.g. amounts 37500) may match as a substring
    # after stripping punctuation/whitespace, so "37,500" still supports "37500".
    if digits in ctx_digits:
        return True
    return False


def evaluate_grounding(answer: str, context: str) -> dict[str, Any]:
    claims = extract_numeric_claims(answer)
    if not claims:
        # Semantic grounding: compare answer to context via sentence-transformers
        score = _semantic_similarity(answer or "", context or "")
        # Boost with lexical overlap as a fallback signal
        ans_tokens = set(re.findall(r"[\w\u0531-\u0587]{4,}", (answer or "").lower()))
        ctx_tokens = set(re.findall(r"[\w\u0531-\u0587]{4,}", (context or "").lower()))
        if ans_tokens:
            lex_score = len(ans_tokens & ctx_tokens) / max(len(ans_tokens), 1)
        else:
            lex_score = 0.0
        if score > 0:
            score = 0.75 * score + 0.25 * lex_score
        else:
            score = lex_score
        score = max(0.0, min(1.0, score))
        risk = "low" if score >= 0.55 else ("medium" if score >= 0.35 else "high")
        return {
            "grounding_score": round(score, 3),
            "hallucination_rate": round(1.0 - score, 3),
            "risk": risk,
            "claims_total": 0,
            "claims_supported": 0,
            "claims_unsupported": 0,
            "supported_claims": [],
            "unsupported_claims": [],
            "method": "semantic_similarity",
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
    """Append a redacted event to the QA audit log with a size cap."""
    path = os.path.join(_backend_data_dir(), "qa_eval_log.jsonl")
    event = _redact_event(event)
    event.setdefault("ts", datetime.now(timezone.utc).isoformat())

    # Simple size-capped rotation: if current log exceeds cap, keep one backup.
    try:
        if os.path.exists(path) and os.path.getsize(path) >= _QA_LOG_MAX_BYTES:
            backup = path + ".1"
            if os.path.exists(backup):
                os.remove(backup)
            os.replace(path, backup)
    except Exception:
        # Rotation failures are non-fatal; still try to append the event.
        pass

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
            "query_hash": r.get("query_hash"),
            "query_len": r.get("query_len"),
            "grounding_score": r.get("grounding_score"),
            "hallucination_rate": r.get("hallucination_rate"),
            "risk": r.get("risk"),
            "claims_unsupported": r.get("claims_unsupported"),
            "answer_len": r.get("answer_len"),
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

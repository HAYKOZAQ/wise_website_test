"""Tests for fidelity grounding / hallucination detection."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from fidelity import evaluate_grounding, claim_supported  # noqa: E402


def test_wrong_amount_is_unsupported_and_risk_high_or_medium():
    """A fabricated large amount must be flagged as unsupported."""
    answer = "Վճարվում է 999999 դրամ ամսական"
    context = "Նպաստի մասին ընդհանուր տեքստ առանց այդ գումարի"
    res = evaluate_grounding(answer, context)
    assert res["claims_total"] >= 1
    assert res["claims_unsupported"] >= 1
    assert res["risk"] in ("high", "medium")
    assert res["method"] == "numeric_claim_check"


def test_no_numeric_claims_uses_semantic_similarity():
    """When the answer contains no numeric claims, fall back to semantic/lexical scoring."""
    answer = "Կենսաթոշակ ստանում են տարիքային շեմին հասած քաղաքացիները"
    context = "Տարիքային կենսաթոշակ նշանակվում է 63 տարին լրացած քաղաքացիներին"
    res = evaluate_grounding(answer, context)
    assert res["claims_total"] == 0
    assert res["method"] == "semantic_similarity"
    assert res["risk"] in ("low", "medium", "high")
    assert 0.0 <= res["grounding_score"] <= 1.0


def test_wrong_frequency_is_unsupported():
    """Same amount with different frequency units must not be considered supported."""
    answer = "Վճարվում է 50000 դրամ ամսական"
    context = "Տարեկան նպաստի չափը 50000 դրամ է"
    res = evaluate_grounding(answer, context)
    assert res["claims_total"] >= 1
    assert res["claims_unsupported"] >= 1


def test_claim_supported_detects_unit_mismatch():
    assert claim_supported("50000 դրամ ամսական", "50000 դրամ տարեկան") is False


def test_claim_supported_short_age_not_subsumed_by_amount():
    """'63' as an age must not be supported by '63,500' as an amount."""
    assert claim_supported("63", "63,500 դրամ") is False
    assert claim_supported("63", "63 տարեկան") is True


def test_unsupported_age_claim():
    """A numeric age claim that is not in the context must be unsupported."""
    answer = "Տարիքային կենսաթոշակ ստանալու իրավունք ունի 85 տարին լրացած անձը"
    context = "Տարիքային կենսաթոշակ ստանալու իրավունք ունի 63 տարին լրացած անձը"
    res = evaluate_grounding(answer, context)
    assert res["claims_unsupported"] >= 1
    assert res["risk"] in ("high", "medium")

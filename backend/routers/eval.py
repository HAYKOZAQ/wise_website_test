"""
Grounding evaluation and hallucination verification router.
"""

from __future__ import annotations

from typing import Any, Dict
from fastapi import APIRouter, HTTPException

from fidelity import load_eval_stats, evaluate_grounding, log_qa_event, EVAL_CASES

router = APIRouter(tags=["Evaluation"])


@router.get("/api/eval/stats")
def eval_stats(limit: int = 500):
    return load_eval_stats(limit=min(max(limit, 10), 5000))


@router.post("/api/eval/check")
def eval_check(payload: Dict[str, Any]):
    answer = (payload or {}).get("answer") or ""
    context = (payload or {}).get("context") or ""
    if not answer:
        raise HTTPException(status_code=400, detail="answer is required")

    result = evaluate_grounding(answer, context)
    try:
        log_qa_event({
            "query": (payload or {}).get("query") or "(manual check)",
            "mode": "manual",
            "answer_preview": answer[:400],
            **result,
        })
    except Exception:
        pass
    return result


@router.post("/api/eval/run")
def eval_run():
    from rag_engine import rag_engine_instance

    if not rag_engine_instance:
        raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

    results = []
    for case in EVAL_CASES:
        try:
            out = rag_engine_instance.generate_response(case["query"], case.get("lang", "hy"))
            answer = out.get("answer") or ""
            fid = out.get("fidelity") or {}
            must = case.get("must_contain_any") or []
            hit = any(m.lower() in answer.lower() for m in must) if must else True
            results.append({
                "id": case["id"],
                "query": case["query"],
                "ok_keyword_check": hit,
                "generation_mode": out.get("generation_mode"),
                "answer_len": len(answer),
                "answer_preview": answer[:280],
                "fidelity": fid,
                "sources": [s.get("title") for s in (out.get("sources") or [])[:4]],
            })
        except Exception as e:
            results.append({
                "id": case["id"],
                "query": case["query"],
                "error": str(e),
            })

    halls = [
        r["fidelity"]["hallucination_rate"]
        for r in results
        if r.get("fidelity") and r["fidelity"].get("hallucination_rate") is not None
    ]
    grounds = [
        r["fidelity"]["grounding_score"]
        for r in results
        if r.get("fidelity") and r["fidelity"].get("grounding_score") is not None
    ]

    summary = {
        "cases_tested": len(results),
        "cases_ok_keyword": sum(1 for r in results if r.get("ok_keyword_check")),
        "avg_grounding_score": round(sum(grounds) / len(grounds), 3) if grounds else None,
        "avg_hallucination_rate": round(sum(halls) / len(halls), 3) if halls else None,
    }
    return {"summary": summary, "results": results}

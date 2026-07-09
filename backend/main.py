import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Any, Optional
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rag_engine import RAGEngine, OLLAMA_HOST, OLLAMA_MODEL
from fidelity import load_eval_stats, EVAL_CASES, evaluate_grounding, log_qa_event

app = FastAPI(
    title="MLSA Welfare RAG API",
    version="2.1",
    description="WISE Foundation social programs assistant — ARLIS-backed RAG + fidelity checks",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("Initializing RAG Engine...")
try:
    rag_engine = RAGEngine()
except Exception as e:
    print(f"Error starting RAG Engine: {e}")
    rag_engine = None


class ChatRequest(BaseModel):
    query: str
    lang: str = "hy"


class ChatResponse(BaseModel):
    answer: str
    sources: list[Any] = Field(default_factory=list)
    vector_search: bool = False
    follow_ups: list[str] = Field(default_factory=list)
    fidelity: Optional[dict[str, Any]] = None
    generation_mode: Optional[str] = None


def _status_payload() -> dict:
    ollama_ok = False
    try:
        r = requests.get(OLLAMA_HOST, timeout=2)
        if r.status_code == 200:
            ollama_ok = True
    except Exception:
        pass

    legal_acts = 0
    cache_ok = False
    corpus_hash = ""
    if rag_engine:
        legal_acts = getattr(rag_engine, "legal_acts", 0)
        cache_ok = getattr(rag_engine, "cache_ok", False)
        corpus_hash = getattr(rag_engine, "corpus_hash", "")

    stats = load_eval_stats(limit=200)
    return {
        "status": "ready" if rag_engine else "error",
        "vector_search_active": rag_engine.vector_enabled if rag_engine else False,
        "ollama_connected": ollama_ok,
        "ollama_host": OLLAMA_HOST,
        "model": OLLAMA_MODEL,
        "documents_indexed": len(rag_engine.documents) if rag_engine else 0,
        "chunks_indexed": len(rag_engine.chunks) if rag_engine else 0,
        "legal_acts": legal_acts,
        "cache_ok": cache_ok,
        "corpus_hash": corpus_hash,
        "fidelity_summary": {
            "entries": stats.get("entries"),
            "avg_grounding_score": stats.get("avg_grounding_score"),
            "avg_hallucination_rate": stats.get("avg_hallucination_rate"),
            "risk_counts": stats.get("risk_counts"),
        },
    }


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def root():
    s = _status_payload()
    ok = s["status"] == "ready"
    badge = "#10b981" if ok else "#ef4444"
    label = "READY" if ok else "ERROR"
    fs = s.get("fidelity_summary") or {}
    hall = fs.get("avg_hallucination_rate")
    ground = fs.get("avg_grounding_score")
    hall_s = f"{hall:.0%}" if isinstance(hall, (int, float)) else "n/a"
    ground_s = f"{ground:.0%}" if isinstance(ground, (int, float)) else "n/a"
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WISE RAG API</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 40px auto;
           padding: 0 20px; color: #0f172a; line-height: 1.5; }}
    h1 {{ font-size: 1.4rem; }}
    .badge {{ display: inline-block; background: {badge}; color: #fff;
              padding: 4px 10px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }}
    a {{ color: #183960; }}
    code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }}
    .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
             padding: 14px 16px; margin: 16px 0; }}
  </style>
</head>
<body>
  <h1>WISE Social Programs RAG API</h1>
  <p><span class="badge">{label}</span></p>
  <div class="card">
    <strong>Corpus</strong>
    <ul>
      <li>Documents: {s['documents_indexed']}</li>
      <li>Chunks: {s['chunks_indexed']}</li>
      <li>ARLIS acts: {s['legal_acts']}</li>
    </ul>
    <strong>Fidelity (recent chats)</strong>
    <ul>
      <li>Logged answers: {fs.get('entries', 0)}</li>
      <li>Avg grounding: {ground_s}</li>
      <li>Avg hallucination rate: {hall_s}</li>
      <li>Risk counts: {fs.get('risk_counts')}</li>
    </ul>
  </div>
  <p>Endpoints:</p>
  <ul>
    <li><a href="/api/status"><code>GET /api/status</code></a></li>
    <li><code>POST /api/chat</code></li>
    <li><a href="/api/eval/stats"><code>GET /api/eval/stats</code></a> — hallucination dashboard JSON</li>
    <li><a href="/api/eval/run"><code>POST /api/eval/run</code></a> — run built-in test cases</li>
    <li><a href="/docs"><code>/docs</code></a></li>
  </ul>
</body>
</html>"""
    return HTMLResponse(content=html)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/api/status")
def get_status():
    return _status_payload()


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    print(f"Received query ({request.lang}): {request.query}")
    try:
        result = rag_engine.generate_response(request.query, request.lang)
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources") or [],
            vector_search=bool(result.get("vector_search")),
            follow_ups=result.get("follow_ups") or [],
            fidelity=result.get("fidelity"),
            generation_mode=result.get("generation_mode"),
        )
    except Exception as e:
        print(f"Chat generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/eval/stats")
def eval_stats(limit: int = 500):
    """Hallucination / grounding dashboard over logged answers."""
    return load_eval_stats(limit=min(max(limit, 10), 5000))


@app.post("/api/eval/check")
def eval_check(payload: dict[str, Any]):
    """
    Manually score an answer against context text.
    Body: { "answer": "...", "context": "..." }
    """
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


@app.post("/api/eval/run")
def eval_run():
    """
    Run built-in regression questions through the live RAG engine
    and return per-case grounding + hallucination metrics.
    """
    if not rag_engine:
        raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

    results = []
    for case in EVAL_CASES:
        try:
            out = rag_engine.generate_response(case["query"], case.get("lang", "hy"))
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
        "cases": len(results),
        "avg_hallucination_rate": round(sum(halls) / len(halls), 3) if halls else None,
        "avg_grounding_score": round(sum(grounds) / len(grounds), 3) if grounds else None,
        "keyword_pass": sum(1 for r in results if r.get("ok_keyword_check")),
    }
    return {"summary": summary, "results": results}


if __name__ == "__main__":
    # Cloud hosts (Render/Railway) inject PORT; local default 8000
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("UVICORN_RELOAD", "").lower() in ("1", "true", "yes")
    uvicorn.run("main:app", host=host, port=port, reload=reload)

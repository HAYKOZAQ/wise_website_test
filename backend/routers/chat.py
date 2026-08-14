"""
Primary RAG chat endpoint.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request

from core.security import rate_limiter

router = APIRouter(tags=["Chat"])


class ChatHistoryTurn(BaseModel):
    role: str = "user"
    content: str = ""


class ChatRequest(BaseModel):
    query: str
    lang: str = "hy"
    history: list[ChatHistoryTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[Any] = Field(default_factory=list)
    vector_search: bool = False
    follow_ups: list[str] = Field(default_factory=list)
    fidelity: Optional[dict[str, Any]] = None
    generation_mode: Optional[str] = None


@router.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, req: Request):
    from rag_engine import rag_engine_instance, rag_lock

    if not rag_engine_instance:
        raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    if len(request.query) > 2000:
        raise HTTPException(status_code=400, detail="Query too long (max 2000 characters)")

    # Enforce sliding-window rate limit
    rate_limiter.check(req)

    try:
        with rag_lock:
            engine = rag_engine_instance
        if not engine:
            raise HTTPException(status_code=500, detail="RAG Engine is not initialized")

        hist = [
            {"role": t.role, "content": t.content}
            for t in (request.history or [])
            if (t.content or "").strip()
        ][-8:]

        result = engine.generate_response(request.query, request.lang, history=hist or None)
        return ChatResponse(
            answer=result["answer"],
            sources=result.get("sources") or [],
            vector_search=bool(result.get("vector_search")),
            follow_ups=result.get("follow_ups") or [],
            fidelity=result.get("fidelity"),
            generation_mode=result.get("generation_mode"),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Chat generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

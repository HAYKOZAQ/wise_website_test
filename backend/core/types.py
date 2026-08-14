"""
Canonical Pydantic models and types for requests, responses, and RAG retrieval entities.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    session_id: Optional[str] = Field(default=None, max_length=64)
    history: Optional[list[dict[str, Any]]] = Field(default=None, max_length=20)
    mode: Optional[str] = Field(default="auto")
    language: Optional[str] = Field(default="hy")


class SourceDoc(BaseModel):
    title: str
    doc_type: str = "summary"
    category: Optional[str] = None
    act_id: Optional[Any] = None
    article: Optional[str] = None
    source_url: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceDoc] = []
    model: str = "rag"
    session_id: Optional[str] = None
    error: Optional[str] = None
    fidelity: Optional[dict[str, Any]] = None
    cached: Optional[bool] = None
    follow_ups: list[str] = []


class ContactRequest(BaseModel):
    name: str = Field(..., max_length=120)
    email: str = Field(..., max_length=160)
    subject: Optional[str] = Field(default="Website contact", max_length=200)
    message: str = Field(..., max_length=4000)


class EvalCheckRequest(BaseModel):
    answer: str
    context: str


class EvalRunRequest(BaseModel):
    sample_size: Optional[int] = 15

import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

# Fix Windows terminal encoding for Armenian Unicode
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

from rag_engine import RAGEngine, OLLAMA_HOST, OLLAMA_MODEL

app = FastAPI(title="MLSA Welfare RAG API", version="1.0")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all origins for local deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instantiate the RAG Engine
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
    sources: list[str] = []
    vector_search: bool = False

@app.get("/api/status")
def get_status():
    ollama_ok = False
    try:
        r = requests.get(OLLAMA_HOST, timeout=2)
        if r.status_code == 200:
            ollama_ok = True
    except:
        pass
        
    return {
        "status": "ready" if rag_engine else "error",
        "vector_search_active": rag_engine.vector_enabled if rag_engine else False,
        "ollama_connected": ollama_ok,
        "ollama_host": OLLAMA_HOST,
        "model": OLLAMA_MODEL,
        "documents_indexed": len(rag_engine.documents) if rag_engine else 0,
        "chunks_indexed": len(rag_engine.chunks) if rag_engine else 0
    }

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
            sources=result["sources"],
            vector_search=result["vector_search"]
        )
    except Exception as e:
        print(f"Chat generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

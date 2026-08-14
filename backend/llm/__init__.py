"""LLM clients and prompt utilities."""
from llm.gemini import gemini_client, GeminiClient
from llm.ollama import ollama_client, OllamaClient
from llm.prompts import (
    LEGAL_QUERY_HINTS,
    SUMMARY_QUERY_HINTS,
    strip_image_refs,
    build_rag_prompt,
    build_follow_ups,
)

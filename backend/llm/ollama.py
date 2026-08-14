"""
Local Ollama fallback inference client.
"""

from __future__ import annotations

import requests
from core.config import settings


class OllamaClient:
    """Client for local Ollama LLM generation."""

    def __init__(self):
        self.host = settings.ollama_host.rstrip("/")
        self.model = settings.ollama_model

    def generate(self, system_prompt: str, timeout_sec: float = 60.0) -> str:
        """Invokes the local Ollama instance if reachable."""
        try:
            url = f"{self.host}/api/generate"
            payload = {
                "model": self.model,
                "prompt": system_prompt,
                "stream": False,
                "options": {"temperature": 0.2},
            }
            r = requests.post(url, json=payload, timeout=timeout_sec)
            if r.status_code == 200:
                return (r.json().get("response") or "").strip()
        except Exception as e:
            print(f"Ollama generate error: {e}")
        return ""


ollama_client = OllamaClient()

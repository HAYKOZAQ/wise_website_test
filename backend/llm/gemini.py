"""
Google Gemini generation client with resilient fallback, retry policies, and deadline budget.
"""

from __future__ import annotations

import time
import requests
from typing import Optional, Tuple

from core.config import settings


class GeminiClient:
    """Client for generating grounded RAG answers with Google Gemini models."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.models = settings.gemini_generate_models
        self.max_retries = settings.gemini_max_retries
        self.deadline_sec = settings.gemini_deadline_sec
        self.timeout_sec = settings.gemini_timeout_sec

    @property
    def is_available(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    @staticmethod
    def parse_response(data: dict) -> Tuple[str, str]:
        """Extract answer text and finish reason from Gemini response JSON."""
        candidates = data.get("candidates") or []
        if not candidates:
            return "", "NO_CANDIDATES"
        c0 = candidates[0]
        finish = str(c0.get("finishReason") or c0.get("finish_reason") or "")
        parts = c0.get("content", {}).get("parts", [])
        answer = ""
        for part in parts:
            if not part.get("thought", False):
                answer += part.get("text", "")
        return answer.strip(), finish

    def generate(self, system_prompt: str) -> str:
        """Tries configured Gemini models in order with retries, bounded by the global deadline."""
        if not self.is_available:
            return ""

        payload = {
            "contents": [{"parts": [{"text": system_prompt}]}],
            "generationConfig": {
                "temperature": 0.15,
                "maxOutputTokens": 4096,
                "thinkingConfig": {"thinkingBudget": 0},
            },
        }

        deadline = time.monotonic() + self.deadline_sec
        for model in self.models:
            for attempt in range(1, self.max_retries + 1):
                remaining = deadline - time.monotonic()
                if remaining <= 2:
                    print("Gemini deadline reached; terminating generation attempt.")
                    return ""
                try:
                    url = (
                        f"https://generativelanguage.googleapis.com/v1beta/models/"
                        f"{model}:generateContent?key={self.api_key}"
                    )
                    r = requests.post(
                        url,
                        json=payload,
                        timeout=min(self.timeout_sec, remaining),
                    )
                    if r.status_code == 200:
                        answer, finish = self.parse_response(r.json())
                        if answer:
                            return answer
                    elif r.status_code in (429, 500, 502, 503, 504):
                        continue
                    else:
                        break
                except requests.Timeout:
                    pass
                except Exception as e:
                    print(f"Gemini {model} error: {e}")
                    break
        return ""


gemini_client = GeminiClient()

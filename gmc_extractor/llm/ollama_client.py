"""
gmc_extractor/llm/ollama_client.py
Ollama LLM client using plain requests.
Calls http://localhost:11434/api/chat with format=json, num_ctx=16384.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import requests

from gmc_extractor.llm.base import LLMClient
from gmc_extractor.llm.cache import ResponseCache
from gmc_extractor.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 120  # seconds


class OllamaClient(LLMClient):
    """
    LLM client for locally-running Ollama.

    Args:
        base_url: Ollama server base URL.
        model: Model name (e.g. 'qwen2.5:7b').
        cache: Optional ResponseCache instance.
        rate_limiter: Optional RateLimiter instance.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        api_key: Optional[str] = None,
        cache: Optional[ResponseCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._cache = cache
        self._rate_limiter = rate_limiter

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model

    def ask_json(self, system: str, prompt: str) -> dict:
        """Send a prompt to Ollama and return a parsed JSON dict."""
        if self._cache:
            cached = self._cache.get(self.provider_name, self._model, system, prompt)
            if cached is not None:
                return cached

        result = self._call_api(system, prompt)

        if self._cache:
            self._cache.put(self.provider_name, self._model, system, prompt, result)

        return result

    def _call_api(self, system: str, prompt: str) -> dict:
        """Make a single API call to Ollama."""
        if self._rate_limiter:
            self._rate_limiter.acquire()

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0,
                "num_ctx": 16384,
            },
        }

        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        try:
            resp = requests.post(
                f"{self._base_url}/api/chat",
                json=payload,
                headers=headers,
                timeout=_DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "{}")
            # Strip markdown fences if present
            content = content.strip()
            if content.startswith("```"):
                lines = content.splitlines()
                content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(content)
        except requests.ConnectionError as exc:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self._base_url}. Is Ollama running?"
            ) from exc
        except json.JSONDecodeError as exc:
            logger.error("Ollama returned non-JSON content.")
            raise ValueError(f"Ollama response is not valid JSON: {exc}") from exc

"""
gmc_extractor/llm/openai_client.py
OpenAI LLM client using plain requests to https://api.openai.com/v1/chat/completions.
Uses JSON-only mode, temperature 0, with retry and rate limiting.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from gmc_extractor.llm.base import LLMClient
from gmc_extractor.llm.cache import ResponseCache
from gmc_extractor.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 120  # seconds


class OpenAIClient(LLMClient):
    """
    LLM client for OpenAI API via standard HTTP requests.

    Args:
        api_key: OpenAI API key.
        model: Model name (e.g. 'gpt-4o-mini' or 'gpt-4o').
        cache: Optional ResponseCache instance.
        rate_limiter: Optional RateLimiter instance.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        cache: Optional[ResponseCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._cache = cache
        self._rate_limiter = rate_limiter

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._model

    def ask_json(self, system: str, prompt: str) -> dict:
        """Send prompt to OpenAI and return parsed JSON dict."""
        if self._cache:
            cached = self._cache.get(self.provider_name, self._model, system, prompt)
            if cached is not None:
                return cached

        result = self._call_with_retry(system, prompt)

        if self._cache:
            self._cache.put(self.provider_name, self._model, system, prompt, result)

        return result

    @retry(
        retry=retry_if_exception_type((requests.RequestException, ValueError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def _call_with_retry(self, system: str, prompt: str) -> dict:
        """Execute the API call with rate limiting and exponential backoff retry."""
        if self._rate_limiter:
            self._rate_limiter.acquire()

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=_DEFAULT_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            raw_text = data["choices"][0]["message"]["content"]
            raw_text = raw_text.strip()
            if raw_text.startswith("```"):
                lines = raw_text.splitlines()
                raw_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
            return json.loads(raw_text)
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else 0
            err_msg = exc.response.text if exc.response is not None else str(exc)
            logger.error("OpenAI API error %d: %s", status, err_msg)
            raise
        except (KeyError, json.JSONDecodeError) as exc:
            logger.error("Failed to parse OpenAI JSON response: %s", exc)
            raise ValueError(f"Invalid JSON response from OpenAI: {exc}") from exc

"""
gmc_extractor/llm/gemini_client.py
Gemini LLM client using the official google-genai SDK.
Uses JSON-only mode, temperature 0, with retry + rate limiting.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from gmc_extractor.llm.base import LLMClient
from gmc_extractor.llm.cache import ResponseCache
from gmc_extractor.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class GeminiClient(LLMClient):
    """
    LLM client for Google Gemini via the google-genai SDK.

    Args:
        api_key: Gemini API key.
        model: Model name (e.g. 'gemini-2.0-flash-lite').
        cache: Optional ResponseCache instance.
        rate_limiter: Optional RateLimiter instance.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-3.5-flash-lite",
        cache: Optional[ResponseCache] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._cache = cache
        self._rate_limiter = rate_limiter
        self._client = self._build_client()

    def _build_client(self):
        """Initialise the google-genai client."""
        try:
            import os
            # Fix httpx bug where unbracketed IPv6 entries like '::1' in NO_PROXY cause InvalidURL: Invalid port: ':1'
            for _var in ("NO_PROXY", "no_proxy"):
                _val = os.environ.get(_var)
                if _val:
                    os.environ[_var] = ",".join([e.strip() for e in _val.split(",") if ":" not in e and e.strip()])

            from google import genai
            client = genai.Client(api_key=self._api_key)
            return client
        except ImportError as exc:
            raise ImportError("google-genai package is required. pip install google-genai") from exc

    @property
    def provider_name(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._model

    def ask_json(self, system: str, prompt: str) -> dict:
        """Send a prompt and return a parsed JSON dict."""
        # Check cache first
        if self._cache:
            cached = self._cache.get(self.provider_name, self._model, system, prompt)
            if cached is not None:
                return cached

        result = self._call_with_retry(system, prompt)

        # Store in cache
        if self._cache:
            self._cache.put(self.provider_name, self._model, system, prompt, result)

        return result

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        reraise=True,
    )
    def _call_with_retry(self, system: str, prompt: str) -> dict:
        """Actual API call with exponential backoff retry."""
        return self._call_api(system, prompt)

    def _call_api(self, system: str, prompt: str) -> dict:
        """Make a single API call to Gemini."""
        from google.genai import types

        if self._rate_limiter:
            self._rate_limiter.acquire()

        try:
            full_prompt = f"{system}\n\n{prompt}"
            response = self._client.models.generate_content(
                model=self._model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0,
                    response_mime_type="application/json",
                ),
            )
            text = response.text or ""
            text = text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                lines = text.splitlines()
                text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            return json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error("Gemini returned non-JSON: %s", exc)
            raise ValueError(f"Gemini response is not valid JSON: {exc}") from exc
        except Exception as exc:
            logger.error("Gemini API error: %s", exc)
            raise

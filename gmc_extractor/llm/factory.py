"""
gmc_extractor/llm/factory.py
Factory function to create the appropriate LLM client from settings.
"""
from __future__ import annotations

import logging

from gmc_extractor.config import Settings
from gmc_extractor.llm.base import LLMClient
from gmc_extractor.llm.cache import ResponseCache
from gmc_extractor.llm.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


def get_client(
    settings: Settings,
    use_cache: bool = True,
    provider_override: str | None = None,
    model_override: str | None = None,
) -> LLMClient:
    """
    Instantiate and return the appropriate LLMClient based on settings.

    Args:
        settings: The global Settings object.
        use_cache: Whether to attach a ResponseCache to the client.
        provider_override: Override the LLM provider from settings.
        model_override: Override the model name from settings.

    Returns:
        A configured LLMClient instance.

    Raises:
        ValueError: If an unknown provider is specified.
    """
    provider = (provider_override or settings.llm_provider).lower()
    cache = ResponseCache(settings.cache_dir) if use_cache else None
    rate_limiter = RateLimiter(
        requests_per_minute=settings.requests_per_minute,
        max_requests_per_run=settings.max_requests_per_run,
    )

    if provider == "gemini":
        from gmc_extractor.llm.gemini_client import GeminiClient
        if not settings.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please set GEMINI_API_KEY in your .env file, "
                "or run with --provider ollama (local) or --provider mock (offline testing)."
            )
        model = model_override or settings.gemini_model
        logger.info("Using Gemini provider, model=%s", model)
        return GeminiClient(
            api_key=settings.gemini_api_key,
            model=model,
            cache=cache,
            rate_limiter=rate_limiter,
        )
    elif provider == "openai":
        from gmc_extractor.llm.openai_client import OpenAIClient
        if not settings.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Please set OPENAI_API_KEY in your .env file."
            )
        model = model_override or settings.openai_model
        logger.info("Using OpenAI provider, model=%s", model)
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=model,
            cache=cache,
            rate_limiter=rate_limiter,
        )
    elif provider == "ollama":
        from gmc_extractor.llm.ollama_client import OllamaClient
        model = model_override or settings.ollama_model
        logger.info("Using Ollama provider, model=%s", model)
        return OllamaClient(
            base_url=settings.ollama_base_url,
            model=model,
            api_key=settings.ollama_api_key or None,
            cache=cache,
            rate_limiter=rate_limiter,
        )
    elif provider == "mock":
        import os
        if os.environ.get("ALLOW_MOCK_LLM") != "1":
            raise RuntimeError(
                "Mock LLM client is strictly prohibited outside unit test environments. "
                "Never fabricate extraction results. Please configure a real LLM provider "
                "(gemini, openai, ollama) or set ALLOW_MOCK_LLM=1 for pytest runs."
            )
        from gmc_extractor.llm.mock_client import MockLLMClient
        model = model_override or "mock-model"
        logger.info("Using Mock provider (test mode: ALLOW_MOCK_LLM=1), model=%s", model)
        return MockLLMClient(model=model)
    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. Set LLM_PROVIDER=gemini, openai, ollama, or mock."
        )

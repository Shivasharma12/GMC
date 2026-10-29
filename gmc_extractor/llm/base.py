"""
gmc_extractor/llm/base.py
Abstract base class for LLM clients.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def ask_json(self, system: str, prompt: str) -> dict:
        """
        Send a prompt to the LLM and return a parsed JSON dict.

        Args:
            system: The system-level instructions string.
            prompt: The user-facing prompt with extracted content.

        Returns:
            A dict parsed from the LLM's JSON response.

        Raises:
            ValueError: If the response cannot be parsed as valid JSON.
        """
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short identifier for this provider (e.g. 'gemini', 'ollama')."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """The model name being used."""
        ...

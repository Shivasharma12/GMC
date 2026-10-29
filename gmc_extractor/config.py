"""
gmc_extractor/config.py
Loads environment variables and YAML configuration files.
Provides a singleton Settings dataclass.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Load .env from the project root (parent of this package)
_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env", override=False)


@dataclass
class Settings:
    """Central configuration loaded from environment variables and YAML files."""

    # ── LLM ──────────────────────────────────────────────────────────────────
    llm_provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini"))
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(
        default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    )
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(
        default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    )
    ollama_base_url: str = field(
        default_factory=lambda: os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    )
    ollama_model: str = field(
        default_factory=lambda: os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    )
    ollama_api_key: str = field(
        default_factory=lambda: os.getenv("OLLAMA_API_KEY", "")
    )

    # ── Rate limiting ─────────────────────────────────────────────────────────
    requests_per_minute: int = field(
        default_factory=lambda: int(os.getenv("REQUESTS_PER_MINUTE", "10"))
    )
    max_requests_per_run: int = field(
        default_factory=lambda: int(os.getenv("MAX_REQUESTS_PER_RUN", "60"))
    )

    # ── Paths ─────────────────────────────────────────────────────────────────
    cache_dir: Path = field(
        default_factory=lambda: _ROOT / os.getenv("CACHE_DIR", ".cache")
    )
    output_dir: Path = field(default_factory=lambda: _ROOT / "output")
    config_dir: Path = field(default_factory=lambda: _ROOT / "config")

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # ── YAML configs (loaded lazily) ─────────────────────────────────────────
    _keywords: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _qms_mapping: dict[str, Any] | None = field(default=None, init=False, repr=False)

    @property
    def keywords(self) -> dict[str, Any]:
        """Return the keywords config, loading from YAML if not yet cached."""
        if self._keywords is None:
            path = self.config_dir / "keywords.yaml"
            with open(path, encoding="utf-8") as f:
                self._keywords = yaml.safe_load(f)
        return self._keywords  # type: ignore[return-value]

    @property
    def qms_mapping(self) -> dict[str, Any]:
        """Return the QMS mapping config, loading from YAML if not yet cached."""
        if self._qms_mapping is None:
            path = self.config_dir / "qms_mapping.yaml"
            with open(path, encoding="utf-8") as f:
                self._qms_mapping = yaml.safe_load(f)
        return self._qms_mapping  # type: ignore[return-value]

    def ensure_dirs(self) -> None:
        """Create output and cache directories if they don't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


# Module-level singleton
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the global Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings

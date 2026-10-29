"""
gmc_extractor/llm/cache.py
On-disk JSON cache for LLM responses.
Cache keys are sha256(provider + model + system + prompt).
"""
from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class ResponseCache:
    """
    Disk-backed cache for LLM responses.

    Args:
        cache_dir: Directory where cache JSON files are stored.
    """

    def __init__(self, cache_dir: Path) -> None:
        self._dir = cache_dir / "llm_responses"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _key(self, provider: str, model: str, system: str, prompt: str) -> str:
        """Generate a deterministic cache key."""
        raw = f"{provider}|{model}|{system}|{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, provider: str, model: str, system: str, prompt: str) -> Optional[dict]:
        """Return cached response dict, or None if not cached."""
        key = self._key(provider, model, system, prompt)
        path = self._dir / f"{key}.json"
        if path.exists():
            logger.debug("Cache HIT for key %s...", key[:8])
            return json.loads(path.read_text(encoding="utf-8"))
        logger.debug("Cache MISS for key %s...", key[:8])
        return None

    def put(self, provider: str, model: str, system: str, prompt: str, response: dict) -> None:
        """Store a response dict in the cache."""
        key = self._key(provider, model, system, prompt)
        path = self._dir / f"{key}.json"
        path.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.debug("Cached response to %s", path.name)

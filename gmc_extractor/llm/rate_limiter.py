"""
gmc_extractor/llm/rate_limiter.py
Token-bucket rate limiter and per-run request counter.
Thread-safe using a simple threading.Lock.
"""
from __future__ import annotations

import logging
import threading
import time

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token-bucket rate limiter.

    Args:
        requests_per_minute: Maximum allowed requests per 60-second window.
        max_requests_per_run: Hard cap on total requests in one run. 0 = unlimited.
    """

    def __init__(self, requests_per_minute: int = 10, max_requests_per_run: int = 60) -> None:
        self._rpm = requests_per_minute
        self._max_per_run = max_requests_per_run
        self._interval = 60.0 / max(requests_per_minute, 1)
        self._last_call: float = 0.0
        self._total_calls: int = 0
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """
        Block until a request token is available.

        Raises:
            RuntimeError: If max_requests_per_run is exceeded.
        """
        with self._lock:
            if self._max_per_run > 0 and self._total_calls >= self._max_per_run:
                raise RuntimeError(
                    f"MAX_REQUESTS_PER_RUN ({self._max_per_run}) reached. "
                    "Aborting to protect free-tier quota."
                )
            now = time.monotonic()
            elapsed = now - self._last_call
            wait = self._interval - elapsed
            if wait > 0:
                logger.debug("Rate limiter: sleeping %.2fs", wait)
                time.sleep(wait)
            self._last_call = time.monotonic()
            self._total_calls += 1
            logger.debug("Request %d/%d", self._total_calls, self._max_per_run or "∞")

    @property
    def total_calls(self) -> int:
        return self._total_calls

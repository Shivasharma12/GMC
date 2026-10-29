"""
gmc_extractor/logging_utils.py
Rich-based logging setup for the GMC extractor.
"""
from __future__ import annotations

import logging

from rich.console import Console
from rich.logging import RichHandler

console = Console()
_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger to use Rich formatting."""
    global _configured
    if _configured:
        return
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, markup=True)],
    )
    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "pdfminer"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger (call setup_logging first)."""
    return logging.getLogger(name)

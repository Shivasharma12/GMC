"""
Pytest configuration for GMC Extractor test suite.
Enables ALLOW_MOCK_LLM=1 for test runs only.
"""
import os
import pytest

os.environ["ALLOW_MOCK_LLM"] = "1"


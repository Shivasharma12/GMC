import sys
import os
import json
import time
from pathlib import Path

# Add project root to path and force UTF-8 console output
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from gmc_extractor.pdf.ocr import _check_tesseract
from gmc_extractor.llm.cache import ResponseCache
from gmc_extractor.llm.rate_limiter import RateLimiter

print("==================================================")
print("TEST 7: TESSERACT OCR AVAILABILITY TEST")
print("==================================================")
tess_ok = _check_tesseract()
print(f"_check_tesseract(): {tess_ok}")

print("\n==================================================")
print("TEST 8: DETERMINISM & RESPONSE CACHING")
print("==================================================")
cache = ResponseCache(Path(".cache/test_audit_cache"))
cache.put("test_provider", "model", "sys_prompt", "user_prompt", {"test_key": "cached_val"})
cached = cache.get("test_provider", "model", "sys_prompt", "user_prompt")
print(f"Cache hit verified: {cached == {'test_key': 'cached_val'}}")

print("\n==================================================")
print("TEST 9: FREE-TIER RATE LIMITER VERIFICATION")
print("==================================================")
rl = RateLimiter(requests_per_minute=1000, max_requests_per_run=5)
print(f"Rate limiter initialized: max_requests={rl._max_per_run}")
for i in range(5):
    rl.acquire()
print(f"Acquired {rl.total_calls} requests successfully.")
try:
    rl.acquire()
    print("FAIL: Should have blocked on request 6")
except RuntimeError as exc:
    print(f"PASS: Safeguard triggered: {exc}")

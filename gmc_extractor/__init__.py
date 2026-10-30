"""
gmc_extractor package initialization.
Applies environment sanitization for httpx/HTTP client compatibility.
"""
import os

# Fix httpx bug where unbracketed IPv6 entries like '::1' in NO_PROXY cause:
# httpx.InvalidURL: Invalid port: ':1'
for _var in ("NO_PROXY", "no_proxy"):
    _val = os.environ.get(_var)
    if _val:
        _cleaned = ",".join([entry.strip() for entry in _val.split(",") if ":" not in entry and entry.strip()])
        os.environ[_var] = _cleaned


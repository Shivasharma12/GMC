
# GMC Extractor — Phase 8: Remediation & Fix Plan

**Plan Timestamp:** 2026-10-30T19:16:00+05:30  
**Status:** In Execution

---

## 1. Findings Prioritized by Severity

| Finding ID | Severity | Category | File:Line | Description | Action Planned |
|---|---|---|---|---|---|
| **F-01** | **HIGH** | Dependency | `requirements.txt:19` | `google-genai==1.16.0` yanked on PyPI | Update to stable release `google-genai>=1.0.0` or pin `0.1.1` / latest stable |
| **F-02** | **HIGH** | Dependency | `requirements.txt` | Missing `fastapi`, `uvicorn`, `python-multipart` | Add required web dependencies with pinned versions |
| **F-04** | **HIGH** | Data Integrity | `samples/`, `output/` | Synthetic PDF `sample_gmc_policy.pdf` in `samples/` and outputs in `output/` | Move synthetic fixture to `tests/fixtures/` and remove synthetic artifacts from `output/` |
| **F-05** | **HIGH** | Data Integrity | `uploads/` | Official policy `1.Policy Copy.pdf` located in `uploads/` | Copy `1.Policy Copy.pdf` into official `samples/` directory |
| **F-06** | **HIGH** | Hardcoding | `mock_client.py:41-94` | Hardcoded Star Health answers in `MockLLMClient` | Refactor mock client to return generic schema-compliant dynamic responses without hardcoded policy values |
| **F-09** | **HIGH** | Robustness | `normalizer.py:53-70` | Fails on date format `Month DD, YYYY` (e.g. `April 26, 2024`) | Add regex pattern and test case for `Month DD, YYYY` |
| **F-10** | **HIGH** | Security | `requirements.txt:1-20` | Vulnerabilities in `pillow`, `pdfminer-six`, `requests` | Bump versions to `pillow>=11.0.0`, `pdfminer.six>=20240706`, `requests>=2.32.4` |
| **F-SEC-01**| **HIGH** | Security | `server.py:358` | Server binds to `0.0.0.0` by default | Change default host to `127.0.0.1` |
| **F-SEC-02**| **HIGH** | Security | `server.py:45` | Wildcard CORS (`*`) with credentials enabled | Restrict `allow_origins` to `["http://127.0.0.1:8000", "http://localhost:5173", "http://localhost:8000"]` |
| **F-SEC-03**| **HIGH** | Security | `server.py:301-306` | Unrestricted upload without size limit or `%PDF` magic bytes | Validate `%PDF` magic bytes, enforce 30MB limit, sanitize filename |
| **F-SEC-04**| **HIGH** | Security | `server.py:266-284, 308-311` | Potential path traversal in file serving & existing_path | Restrict to canonical child paths of `samples/`, `output/`, and `uploads/` |
| **F-03** | **MEDIUM** | Extraction | `cleaner.py:35-60` | False-positive header removal on unstructured single-page docs | Add length and positional guardrails to header stripper |
| **F-07** | **MEDIUM** | Schema/QMS | `schema/policy.py:20,38,55` | `Identity`, `PolicyDetails`, and `Demographics` lack `evidence` attribute | Add `evidence: Optional[str] = None` and update `qms_mapper.py` to extract evidence |
| **F-SEC-05**| **MEDIUM** | Security | `server.py:36-50` | Missing standard security headers | Add security middleware injecting `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` |
| **F-SEC-06**| **MEDIUM** | Security | `server.py:286-330` | Unhandled PDF parser errors return HTTP 500 | Catch `FileDataError`, `EmptyFileError`, `ValueError` and raise clean HTTP 400 |
| **F-08** | **LOW** | CLI | `main.py:1` | Printing `₹` crashes on standard Windows cmd/powershell | Add `sys.stdout.reconfigure(encoding="utf-8")` at entry point |
| **F-SEC-07**| **LOW** | Privacy/Docs | `README.md:220` | Missing Gemini Free Tier data policy disclosure & Ollama guide | Add prominent Privacy & Data Security section |
| **F-SEC-08**| **LOW** | Repo Hygiene | `.gitignore:38` | `samples/*.pdf` and `uploads/` not in `.gitignore` | Add `samples/*.pdf` and `uploads/` to `.gitignore` |

---

## 2. Execution Order
1. **Fix 1: Dependencies & Environment (`requirements.txt`)** [F-01, F-02, F-10]
2. **Fix 2: Sample & Output Integrity (`samples/`, `uploads/`, `output/`)** [F-04, F-05]
3. **Fix 3: Anti-Hardcoding Mock Client Refactor (`mock_client.py`)** [F-06]
4. **Fix 4: Date Normalizer Enhancement (`normalizer.py`)** [F-09]
5. **Fix 5: Schema & QMS Evidence Attribute (`schema/policy.py`, `qms_mapper.py`)** [F-07]
6. **Fix 6: Web Server Hardening (`server.py`)** [F-SEC-01, F-SEC-02, F-SEC-03, F-SEC-04, F-SEC-05, F-SEC-06]
7. **Fix 7: CLI Windows Unicode Output (`main.py`)** [F-08]
8. **Fix 8: Privacy Disclosures & Git Hygiene (`README.md`, `.gitignore`)** [F-SEC-07, F-SEC-08]
9. **Fix 9: Header Detection Guardrails (`cleaner.py`)** [F-03]
10. **Validation: Re-run Full Test Suite & Audits**

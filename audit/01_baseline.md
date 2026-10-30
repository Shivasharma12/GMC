# Phase 1: Environment and Baseline Audit

**Date**: 2026-10-30  
**Auditor**: Independent Senior Reviewer & QA/Security Engineer  
**Status**: Completed  

---

## 1. Fresh Virtual Environment & Dependency Installation

A clean virtual environment was created outside the project tree at:
`C:\Users\shiva\.gemini\antigravity-ide\brain\072d346e-cfdd-47a2-9531-d0ac97be96d9\scratch\test_venv`

### Command Output (`pip install -r requirements.txt`)
```text
Installing collected packages: websockets, urllib3, typing-extensions, tenacity, shellingham, rapidfuzz, PyYAML, python-dotenv, pypdfium2, PyMuPDFb, pygments, pycparser, pyasn1, pluggy, Pillow, packaging, numpy, mdurl, iniconfig, idna, h11, colorama, charset-normalizer, certifi, annotated-types, requests, rank-bm25, pytest, pytesseract, pymupdf, pydantic-core, pyasn1-modules, markdown-it-py, httpcore, click, cffi, anyio, rich, pytest-mock, pydantic, httpx, cryptography, typer, pdfminer.six, google-auth, pdfplumber, google-genai
Successfully installed Pillow-10.4.0 PyMuPDFb-1.24.3 PyYAML-6.0.2 annotated-types-0.8.0 anyio-4.15.1 certifi-2026.10.23 cffi-2.1.1 charset-normalizer-3.5.2 click-8.1.7 colorama-0.4.6 cryptography-50.0.2 google-auth-2.62.0 google-genai-1.16.0 h11-0.16.0 httpcore-1.0.9 httpx-0.28.1 idna-3.20 iniconfig-2.3.1 markdown-it-py-4.2.0 mdurl-0.1.2 numpy-2.5.4 packaging-26.3 pdfminer.six-20231228 pdfplumber-0.11.4 pluggy-1.7.0 pyasn1-0.6.5 pyasn1-modules-0.4.2 pycparser-3.12 pydantic-2.8.2 pydantic-core-2.20.1 pygments-2.21.0 pymupdf-1.24.5 pypdfium2-5.14.0 pytesseract-0.3.13 pytest-8.3.3 pytest-mock-3.14.0 python-dotenv-1.0.1 rank-bm25-0.2.2 rapidfuzz-3.9.7 requests-2.32.3 rich-13.8.1 shellingham-1.5.4 tenacity-9.0.0 typer-0.12.5 typing-extensions-4.16.0 urllib3-2.8.0 websockets-15.0.1
```

### Baseline Findings
- **[HIGH] F-01: Pinned version `google-genai==1.16.0` is YANKED on PyPI**
  - *Location*: [`requirements.txt:19`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/requirements.txt#L19)
  - *Pip Warning*: `WARNING: The candidate selected for download or install is a yanked version: 'google-genai' candidate (version 1.16.0 at https://files.pythonhosted.org/packages/9b/a7/b5d5481ae266c2b6ae2064003a0ccaa8427ca7b2754df16e6727ab41ee6c/google_genai-1.16.0-py3-none-any.whl) Reason for being yanked: <none given>`
  - *Impact*: In strict CI/CD environments with `--no-yanked`, pip install will fail.
  - *Recommendation*: Upgrade to a non-yanked release (e.g., `>=1.17.0` or `>=1.20.0`).

- **[HIGH] F-02: Missing web server dependencies in `requirements.txt`**
  - *Location*: [`requirements.txt`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/requirements.txt)
  - *Evidence*: `server.py` and `main.py serve` require `fastapi`, `uvicorn`, `python-multipart`. When installing purely from `requirements.txt` in a fresh environment, running `python main.py serve` fails with `ModuleNotFoundError: No module named 'fastapi'`.
  - *Impact*: Dashboard server will not run on a newly set up clone unless these are installed.
  - *Recommendation*: Add `fastapi`, `uvicorn`, `python-multipart` to `requirements.txt` (or a dedicated `requirements-server.txt`).

---

## 2. CLI and Test Suite Verification

### `python main.py --help`
```text
Usage: main.py [OPTIONS] COMMAND [ARGS]...

Extract structured data from GMC insurance policy PDFs.

Options:
  --install-completion          Install completion for the current shell.
  --show-completion             Show completion for the current shell.
  --help                        Show this message and exit.

Commands:
  inspect   Print diagnostic info about a PDF: page count, scanned pages, section headings.
  run       Process a single PDF and write JSON/CSV/report to output/.
  run-all   Process all PDFs in a folder.
  serve     Start the GMC Extractor API and Dashboard server.
```

### `python main.py inspect samples/sample_gmc_policy.pdf`
```text
Inspecting: samples\sample_gmc_policy.pdf
INFO Reading PDF: sample_gmc_policy.pdf
INFO Read 8 pages (0 scanned)
  Total pages : 8
  Scanned     : 0 []
  Headings    : 6
Page 1: POLICY SCHEDULE - GROUP MEDICAL COVER
Page 2: MEMBER CENSUS AND DEMOGRAPHICS SCHEDULE
Page 3: SECTION I - HOSPITALIZATION EXPENSES & ROOM RENT
Page 4: SECTION II - MATERNITY AND NEWBORN BABY BENEFIT
Page 5: SECTION III - WAITING PERIODS AND WAIVERS
Page 8: ANNEXURE I - SPECIAL ENDORSEMENTS AND CONDITIONS
```

### `python main.py inspect "uploads/1.Policy Copy.pdf"`
```text
Inspecting: uploads\1.Policy Copy.pdf
INFO Reading PDF: 1.Policy Copy.pdf
INFO Read 4 pages (0 scanned)
  Total pages : 4
  Scanned     : 0 []
  Headings    : 6
Page 1: AAYUV TECHNOLOGIES
Page 1: PRIVATE LIMITED
Page 1: AAYUV TECHNOLOGIES PRIVATE LIMITED
Page 1: TELANGANA
Page 1: ANNUAL PREMIUM
Page 4: MANISH DODEJA
```
- **[MEDIUM] F-03: Section Heading Detection on Real PDFs lacks semantic filtering**
  - *Location*: [`gmc_extractor/pdf/cleaner.py:112`](file:///c:/Users/shiva/OneDrive/Desktop/assignment%20gmc/gmc-extractor/gmc_extractor/pdf/cleaner.py#L112)
  - *Evidence*: For `1.Policy Copy.pdf`, company address lines and signatory names (`TELANGANA`, `MANISH DODEJA`) were classified as section headings because of font-size / uppercase heuristics.
  - *Impact*: Low operational impact on extraction (BM25 searches page text), but misleading diagnostic output in `inspect`.

### `pytest -q`
```text
......................................................................... [100%]
73 passed in 3.67s
```
- 73 passed, 0 failed, 0 skipped.
- Tests cover schema validation, normalizer (amounts, dates, units), grounding fuzzy match, retriever, and full pipeline with mock LLM client.

---

## 3. Directory Structure Analysis

### Intended vs Actual Comparison:
| Expected Item | Exists? | Path | Notes |
|---|:---:|---|---|
| `README.md` | YES | `README.md` | Present |
| `requirements.txt` | YES | `requirements.txt` | Present (missing fastapi/uvicorn) |
| `.env.example` | YES | `.env.example` | Present |
| `.gitignore` | YES | `.gitignore` | Present |
| `main.py` | YES | `main.py` | Present |
| `config/` | YES | `config/` | Contains `keywords.yaml`, `qms_mapping.yaml` |
| `gmc_extractor/pdf/` | YES | `gmc_extractor/pdf/` | `reader.py`, `cleaner.py`, `ocr.py`, `table_extractor.py` |
| `gmc_extractor/retrieval/` | YES | `gmc_extractor/retrieval/` | `bm25.py`, `retriever.py` |
| `gmc_extractor/llm/` | YES | `gmc_extractor/llm/` | `base.py`, `cache.py`, `factory.py`, `gemini_client.py`, `mock_client.py`, `ollama_client.py`, `openai_client.py`, `rate_limiter.py` |
| `gmc_extractor/schema/` | YES | `gmc_extractor/schema/` | `common.py`, `features.py`, `output.py`, `policy.py` |
| `gmc_extractor/prompts/` | YES | `gmc_extractor/prompts/` | `builder.py`, `groups.py`, `system.py` |
| `gmc_extractor/extraction/` | YES | `gmc_extractor/extraction/` | `runner.py` |
| `gmc_extractor/postprocess/` | YES | `gmc_extractor/postprocess/` | `confidence.py`, `grounding.py`, `normalizer.py`, `validator.py` |
| `gmc_extractor/export/` | YES | `gmc_extractor/export/` | `json_writer.py`, `qms_mapper.py` |
| `tests/` | YES | `tests/` | 5 test modules |
| `samples/` | YES | `samples/` | Contains `sample_gmc_policy.pdf` (synthetic) |
| `output/` | YES | `output/` | Outputs for `sample_gmc_policy` and `1.Policy Copy` |
| `docs/` | YES | `docs/` | `architecture.md`, `sample_analysis.md` |

### Extra Files / Folders Identified:
- `create_sample_pdf.py` (Script used to synthesize `sample_gmc_policy.pdf`)
- `dashboard/` (React.js frontend application with Vite)
- `server.py` (FastAPI backend server)
- `uploads/` (Contains user-uploaded policy: `1.Policy Copy.pdf`)
- `audit/` (Created for this evaluation)

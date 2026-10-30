"""
server.py — FastAPI backend for the GMC Extractor React Dashboard
Provides REST endpoints to:
- List extracted policies and samples
- Run extraction on new or existing PDFs (with Gemini, OpenAI, Ollama, or Mock provider)
- Inspect policy structure & QMS schema
- Stream PDFs for in-browser side-by-side inspection
- Serve the compiled React dashboard frontend
"""
from __future__ import annotations

import csv
import io
import json
import logging
import os
import re

# Fix httpx bug where unbracketed IPv6 entries like '::1' in NO_PROXY cause:
# httpx.InvalidURL: Invalid port: ':1'
for _var in ("NO_PROXY", "no_proxy"):
    _val = os.environ.get(_var)
    if _val:
        os.environ[_var] = ",".join([e.strip() for e in _val.split(",") if ":" not in e and e.strip()])
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

from gmc_extractor.config import get_settings
from gmc_extractor.logging_utils import setup_logging
from gmc_extractor.llm.factory import get_client
from gmc_extractor.pipeline import run_pdf
from gmc_extractor.schema.output import ExtractionResult

logger = logging.getLogger("gmc_server")
setup_logging("INFO")

app = FastAPI(
    title="GMC Insurance Policy Extractor API",
    description="Backend API powering the GMC Extractor React Dashboard",
    version="1.0.0",
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Restrict CORS to local dashboard origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"
SAMPLES_DIR = BASE_DIR / "samples"
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


def _get_policy_summary(json_path: Path) -> Optional[Dict[str, Any]]:
    """Parse output JSON file and return a summary object for dashboard listing."""
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
        doc_info = data.get("document_info", {})
        identity = data.get("identity", {})
        policy = data.get("policy_details", {})
        demographics = data.get("demographics", {})
        features = data.get("features", {})

        stem = json_path.stem
        qms_json_path = OUTPUT_DIR / f"{stem}.qms.json"
        csv_path = OUTPUT_DIR / f"{stem}.qms.csv"
        report_path = OUTPUT_DIR / f"{stem}.report.md"

        # Calculate quick coverage counts
        coverage_counts = {"covered": 0, "not_covered": 0, "not_mentioned": 0}
        def count_features(obj):
            if isinstance(obj, dict):
                if "status" in obj and isinstance(obj["status"], str):
                    st = obj["status"].lower()
                    if st in coverage_counts:
                        coverage_counts[st] += 1
                for v in obj.values():
                    count_features(v)
        count_features(features)

        # Average confidence
        confidences = [
            identity.get("confidence", 0) or 0,
            policy.get("confidence", 0) or 0,
            demographics.get("confidence", 0) or 0,
        ]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        doc_file_name = doc_info.get("file_name", f"{stem}.pdf")
        rel_pdf_path = (
            f"samples/{doc_file_name}" if (SAMPLES_DIR / doc_file_name).exists()
            else (f"uploads/{doc_file_name}" if (UPLOADS_DIR / doc_file_name).exists() else None)
        )

        return {
            "id": stem,
            "filename": doc_file_name,
            "pdf_path": rel_pdf_path,
            "insurer_name": identity.get("insurer_name") or "Unknown Insurer",
            "tpa_name": identity.get("tpa_name") or "Direct / Not Listed",
            "policy_number": policy.get("policy_number") or "N/A",
            "policy_start_date": policy.get("policy_start_date"),
            "policy_end_date": policy.get("policy_end_date"),
            "tenure_months": policy.get("tenure_months"),
            "premium_including_gst": policy.get("premium_including_gst"),
            "premium_excluding_gst": policy.get("premium_excluding_gst"),
            "total_lives": demographics.get("total_lives_stated") or demographics.get("total_lives_computed"),
            "count_mismatch": demographics.get("count_mismatch", False),
            "confidence": round(avg_conf, 2),
            "run_timestamp": doc_info.get("run_timestamp"),
            "provider": doc_info.get("provider"),
            "model": doc_info.get("model"),
            "total_pages": doc_info.get("total_pages", 0),
            "scanned_pages": doc_info.get("scanned_pages", 0),
            "coverage_counts": coverage_counts,
            "has_qms": qms_json_path.exists(),
            "has_csv": csv_path.exists(),
            "has_report": report_path.exists(),
        }
    except Exception as e:
        logger.warning("Could not read policy summary for %s: %s", json_path, e)
        return None


@app.get("/api/health")
def health_check():
    """Health & config check."""
    settings = get_settings()
    return {
        "status": "healthy",
        "default_provider": settings.llm_provider,
        "providers_available": {
            "mock": True,
            "gemini": bool(settings.gemini_api_key),
            "openai": bool(settings.openai_api_key),
            "ollama": True,
        },
        "models": {
            "gemini": settings.gemini_model,
            "openai": settings.openai_model,
            "ollama": settings.ollama_model,
        },
    }


@app.get("/api/policies")
def list_policies():
    """List all extracted policies in output directory."""
    policies = []
    for f in OUTPUT_DIR.glob("*.json"):
        if f.name.endswith(".qms.json"):
            continue
        summary = _get_policy_summary(f)
        if summary:
            policies.append(summary)

    # Sort descending by run_timestamp or filename
    policies.sort(key=lambda x: str(x.get("run_timestamp") or ""), reverse=True)
    return {"policies": policies}


@app.get("/api/samples")
def list_samples():
    """List sample and uploaded PDFs available for extraction."""
    samples = []
    for p in SAMPLES_DIR.glob("*.pdf"):
        samples.append({
            "name": p.name,
            "path": f"samples/{p.name}",
            "size_bytes": p.stat().st_size,
            "is_sample": True,
        })
    for p in UPLOADS_DIR.glob("*.pdf"):
        samples.append({
            "name": p.name,
            "path": f"uploads/{p.name}",
            "size_bytes": p.stat().st_size,
            "is_sample": False,
        })
    return {"files": samples}


@app.get("/api/policies/{policy_id}")
def get_policy_detail(policy_id: str):
    """Get full details for a policy including raw JSON, QMS JSON, CSV, and Markdown report."""
    json_path = OUTPUT_DIR / f"{policy_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"Policy '{policy_id}' not found.")

    extracted_data = json.loads(json_path.read_text(encoding="utf-8"))

    # QMS JSON
    qms_data = None
    qms_path = OUTPUT_DIR / f"{policy_id}.qms.json"
    if qms_path.exists():
        try:
            qms_data = json.loads(qms_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # QMS CSV
    csv_content = ""
    csv_rows = []
    csv_path = OUTPUT_DIR / f"{policy_id}.qms.csv"
    if csv_path.exists():
        try:
            csv_content = csv_path.read_text(encoding="utf-8")
            reader = csv.DictReader(io.StringIO(csv_content))
            csv_rows = list(reader)
        except Exception:
            pass

    # Markdown Report
    report_content = ""
    report_path = OUTPUT_DIR / f"{policy_id}.report.md"
    if report_path.exists():
        try:
            report_content = report_path.read_text(encoding="utf-8")
        except Exception:
            pass

    # Summary
    summary = _get_policy_summary(json_path)

    # PDF path check
    doc_info = extracted_data.get("document_info", {})
    pdf_filename = doc_info.get("file_name", f"{policy_id}.pdf")
    pdf_exists = (SAMPLES_DIR / pdf_filename).exists() or (UPLOADS_DIR / pdf_filename).exists()

    return {
        "summary": summary,
        "extracted": extracted_data,
        "qms": qms_data,
        "csv_text": csv_content,
        "csv_rows": csv_rows,
        "report_markdown": report_content,
        "pdf_url": f"/api/pdf/{pdf_filename}" if pdf_exists else None,
        "pdf_filename": pdf_filename,
        "pdf_path": summary.get("pdf_path") if summary else None,
    }


@app.get("/api/policies/{policy_id}/export/{export_type}")
def download_policy_export(policy_id: str, export_type: str):
    """
    Direct HTTP file download for policy export artifacts with proper
    Content-Disposition and MIME types.
    """
    filename_map = {
        "csv": (OUTPUT_DIR / f"{policy_id}.qms.csv", f"{policy_id}.qms.csv", "text/csv"),
        "qms": (OUTPUT_DIR / f"{policy_id}.qms.json", f"{policy_id}.qms.json", "application/json"),
        "json": (OUTPUT_DIR / f"{policy_id}.json", f"{policy_id}.json", "application/json"),
        "report": (OUTPUT_DIR / f"{policy_id}.report.md", f"{policy_id}.report.md", "text/markdown"),
    }

    if export_type not in filename_map:
        raise HTTPException(status_code=400, detail=f"Invalid export type '{export_type}'. Choose csv, qms, json, or report.")

    file_path, download_name, media_type = filename_map[export_type]
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Export file '{download_name}' not found.")

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type=media_type,
    )


@app.get("/api/pdf/{filename:path}")
def get_pdf_file(filename: str, download: bool = False):
    """Stream PDF for in-browser rendering (inline) or direct attachment download."""
    # Prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename format.")

    candidates = [
        SAMPLES_DIR / filename,
        UPLOADS_DIR / filename,
        OUTPUT_DIR / filename,
    ]
    for p in candidates:
        try:
            resolved = p.resolve()
            # Must be strictly inside allowed directories
            if (
                (resolved.is_relative_to(SAMPLES_DIR.resolve()) or
                 resolved.is_relative_to(UPLOADS_DIR.resolve()) or
                 resolved.is_relative_to(OUTPUT_DIR.resolve()))
                and resolved.exists()
                and resolved.is_file()
            ):
                return FileResponse(
                    path=resolved,
                    media_type="application/pdf",
                    content_disposition_type="attachment" if download else "inline",
                    filename=resolved.name,
                )
        except Exception:
            continue
    raise HTTPException(status_code=404, detail=f"PDF file '{filename}' not found.")


@app.post("/api/extract")
async def extract_pdf(
    file: Optional[UploadFile] = File(None),
    existing_path: Optional[str] = Form(None),
    provider: Optional[str] = Form("gemini"),
    model: Optional[str] = Form(None),
    no_cache: bool = Form(False),
):
    """
    Run the extraction pipeline on an uploaded file or an existing sample PDF.
    Supports provider: 'gemini', 'openai', 'ollama' (or 'mock' with ALLOW_MOCK_LLM=1 in tests).
    """
    settings = get_settings()

    selected_provider = (provider or "gemini").lower()
    if selected_provider == "mock" and os.environ.get("ALLOW_MOCK_LLM") != "1":
        raise HTTPException(
            status_code=400,
            detail="Mock LLM provider is strictly disabled outside test environments. Please choose Google Gemini, OpenAI, or Ollama."
        )

    target_pdf_path: Path
    if file and file.filename:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are supported.")

        # Read file with 30MB limit
        MAX_UPLOAD_SIZE = 30 * 1024 * 1024
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            raise HTTPException(status_code=413, detail="File too large (exceeds 30MB limit).")
        if not content.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Invalid PDF file format (missing %PDF magic header).")

        clean_name = re.sub(r"[^A-Za-z0-9_\-\. ]", "_", Path(file.filename).name)
        target_pdf_path = UPLOADS_DIR / clean_name
        target_pdf_path.write_bytes(content)
    elif existing_path:
        # Prevent path traversal outside BASE_DIR
        resolved = (BASE_DIR / existing_path).resolve()
        if not str(resolved).startswith(str(BASE_DIR.resolve())):
            raise HTTPException(status_code=400, detail="Path traversal attempt detected.")
        if not resolved.exists() or not resolved.is_file():
            raise HTTPException(status_code=400, detail=f"File {existing_path} not found.")
        target_pdf_path = resolved
    else:
        sample_candidates = list(SAMPLES_DIR.glob("*.pdf"))
        if sample_candidates:
            target_pdf_path = sample_candidates[0]
        else:
            raise HTTPException(status_code=400, detail="No PDF file provided or selected.")

    # Initialize client
    selected_provider = (provider or "gemini").lower()
    try:
        client = get_client(
            settings,
            use_cache=not no_cache,
            provider_override=selected_provider,
            model_override=model or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"LLM Client error: {exc}")

    try:
        logger.info("Starting pipeline extraction for %s using provider=%s", target_pdf_path.name, selected_provider)
        result: ExtractionResult = run_pdf(
            pdf_path=target_pdf_path,
            client=client,
            settings=settings,
            use_cache=not no_cache,
        )
        stem = target_pdf_path.stem
        summary = _get_policy_summary(OUTPUT_DIR / f"{stem}.json")
        return {
            "status": "success",
            "policy_id": stem,
            "summary": summary,
            "message": f"Successfully extracted {target_pdf_path.name}",
        }
    except (ValueError, FileNotFoundError) as exc:
        logger.warning("Extraction input error: %s", exc)
        raise HTTPException(status_code=400, detail=f"Invalid or unreadable document: {str(exc)}")
    except Exception as exc:
        logger.exception("Extraction failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(exc)}")


# Mount built React app if exists
DIST_DIR = BASE_DIR / "dashboard" / "dist"
if DIST_DIR.exists():
    app.mount("/", StaticFiles(directory=str(DIST_DIR), html=True), name="static")


def run_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """Start uvicorn server."""
    uvicorn.run("server:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Start GMC Extractor API & Dashboard Server")
    parser.add_argument("--host", default="127.0.0.1", help="Host IP")
    parser.add_argument("--port", type=int, default=8000, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto reload")
    args = parser.parse_args()
    print(f"Starting GMC Extractor Server on http://{args.host}:{args.port}")
    run_server(host=args.host, port=args.port, reload=args.reload)

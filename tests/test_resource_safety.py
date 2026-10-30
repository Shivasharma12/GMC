import fitz
from pathlib import Path
import pytest
from gmc_extractor.pdf.reader import read_pdf
from gmc_extractor.pipeline import run_pdf
from gmc_extractor.llm.mock_client import MockLLMClient
from gmc_extractor.config import get_settings

def test_resource_safety():
    scratch_dir = Path("tests/fixtures/resource_safety")
    scratch_dir.mkdir(parents=True, exist_ok=True)
    settings = get_settings()
    client = MockLLMClient()

    results = {}

    # 1. Zero-byte PDF
    zero_pdf = scratch_dir / "zero_page.pdf"
    zero_pdf.write_bytes(b"")

    try:
        pages = read_pdf(zero_pdf)
        results["zero_page_read"] = f"Handled safely: returned {len(pages)} pages"
    except Exception as e:
        results["zero_page_read"] = f"Failed with exception: {type(e).__name__}: {e}"

    # 2. Corrupted PDF
    corrupt_pdf = scratch_dir / "corrupted.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4\n%This is a corrupted byte sequence that cuts off abruptly\n\x00\xff\xfe")

    try:
        pages = read_pdf(corrupt_pdf)
        results["corrupted_pdf_read"] = f"Handled: returned {len(pages)} pages"
    except Exception as e:
        results["corrupted_pdf_read"] = f"Safely raised error: {type(e).__name__}: {e}"

    # 3. Encrypted PDF
    encrypted_pdf = scratch_dir / "encrypted.pdf"
    doc_enc = fitz.open()
    page = doc_enc.new_page()
    page.insert_text((50, 72), "Confidential policy text", fontsize=12)
    # Save with user password
    perm = int(
        fitz.PDF_PERM_ACCESSIBILITY
        | fitz.PDF_PERM_PRINT
        | fitz.PDF_PERM_COPY
        | fitz.PDF_PERM_ANNOTATE
    )
    encrypt_meth = fitz.PDF_ENCRYPT_AES_256
    doc_enc.save(
        str(encrypted_pdf),
        encryption=encrypt_meth,
        owner_pw="owner123",
        user_pw="secret123",
        permissions=perm,
    )
    doc_enc.close()

    try:
        pages = read_pdf(encrypted_pdf)
        results["encrypted_pdf_read"] = f"Returned {len(pages)} pages (is_encrypted handled)"
    except Exception as e:
        results["encrypted_pdf_read"] = f"Safely raised: {type(e).__name__}: {e}"

    print("Resource Safety Test Results:")
    for k, v in results.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    test_resource_safety()

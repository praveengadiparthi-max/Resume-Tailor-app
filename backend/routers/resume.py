import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response

from models.schemas import TailorResponse, TailorTextRequest
from services.claude_service import tailor_resume
from services.parser import parse_resume
from services.pdf_generator import generate_pdf

router = APIRouter(prefix="/api")

# Cache parsed resume text by file MD5 — avoids re-running pdfplumber on the same file
_parse_cache: dict[str, str] = {}


def _parse_cached(file_bytes: bytes, filename: str, content_type: str) -> str:
    key = hashlib.md5(file_bytes).hexdigest()
    if key not in _parse_cache:
        _parse_cache[key] = parse_resume(file_bytes, filename, content_type)
    return _parse_cache[key]

# token -> (pdf_bytes, expiry_unix_timestamp, filename, company_name)
pdf_store: dict[str, tuple[bytes, float, str, str]] = {}

TOKEN_TTL_SECONDS = 600  # 10 minutes

ASSETS_DIR = Path(__file__).parent.parent / "assets"
SAVE_DIR = Path.home() / "Desktop" / "Resumes"
COUNTER_FILE = Path(__file__).parent.parent / "data" / "counter.json"


def _read_count() -> int:
    try:
        return json.loads(COUNTER_FILE.read_text())["count"]
    except Exception:
        return 0


def _increment_count() -> int:
    count = _read_count() + 1
    COUNTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    COUNTER_FILE.write_text(json.dumps({"count": count}))
    return count


def _find_default_resume() -> Path | None:
    if not ASSETS_DIR.exists():
        return None
    for pdf in ASSETS_DIR.glob("*.pdf"):
        return pdf
    return None


def _safe_filename(name: str) -> str:
    clean = re.sub(r"[^\w\s]", "", name).strip()
    return re.sub(r"\s+", "_", clean) if clean else "resume"


def _store_pdf(pdf_bytes: bytes, filename: str, company_name: str) -> str:
    token = str(uuid.uuid4())
    pdf_store[token] = (pdf_bytes, time.time() + TOKEN_TTL_SECONDS, filename, company_name)
    return token


def _purge_expired():
    now = time.time()
    expired = [t for t, (_, exp, _fn, _co) in pdf_store.items() if now > exp]
    for t in expired:
        pdf_store.pop(t, None)


def _tailor_and_store(structured: dict) -> tuple[str, str, str, int]:
    """Generate PDF, store it, return (token, candidate_name, company_name, total_count)."""
    try:
        pdf_bytes = generate_pdf(structured)
    except Exception as e:
        print(f"PDF generation error: {e}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}") from e
    _purge_expired()
    candidate_name = structured.get("contact", {}).get("name", "")
    company_name = structured.get("target_company", "")
    filename = f"{_safe_filename(candidate_name)}.pdf" if candidate_name else "resume.pdf"
    token = _store_pdf(pdf_bytes, filename, company_name)
    total_count = _increment_count()
    return token, candidate_name, company_name, total_count


@router.get("/default-resume")
async def get_default_resume():
    path = _find_default_resume()
    if not path:
        raise HTTPException(status_code=404, detail="No default resume configured.")
    return FileResponse(path, media_type="application/pdf", filename=path.name)


@router.post("/tailor/upload", response_model=TailorResponse)
async def tailor_from_upload(
    file: UploadFile = File(...),
    job_description: str = Form(..., min_length=20, max_length=20000),
    quality_mode: bool = Form(False),
):
    file_bytes = await file.read()
    resume_text = _parse_cached(file_bytes, file.filename or "", file.content_type or "")
    structured = tailor_resume(resume_text, job_description, quality_mode=quality_mode)
    token, candidate_name, company_name, total_count = _tailor_and_store(structured)
    return TailorResponse(message="Resume tailored successfully", download_token=token, candidate_name=candidate_name, company_name=company_name, total_count=total_count)


@router.post("/tailor/text", response_model=TailorResponse)
async def tailor_from_text(body: TailorTextRequest):
    structured = tailor_resume(body.resume_text, body.job_description, quality_mode=body.quality_mode)
    token, candidate_name, company_name, total_count = _tailor_and_store(structured)
    return TailorResponse(message="Resume tailored successfully", download_token=token, candidate_name=candidate_name, company_name=company_name, total_count=total_count)


@router.post("/save-local/{token}")
async def save_local(token: str):
    entry = pdf_store.get(token)
    if not entry:
        raise HTTPException(status_code=404, detail="Token not found or already used.")
    pdf_bytes, expiry, filename, company_name = entry
    if time.time() > expiry:
        pdf_store.pop(token, None)
        raise HTTPException(status_code=410, detail="Download link has expired. Please tailor again.")

    company_folder = _safe_filename(company_name) if company_name else "Unknown_Company"
    save_path = SAVE_DIR / company_folder / filename
    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_bytes(pdf_bytes)
    pdf_store.pop(token, None)

    return {"saved_to": str(save_path)}


@router.get("/download/{token}")
async def download_pdf(token: str):
    entry = pdf_store.get(token)
    if not entry:
        raise HTTPException(status_code=404, detail="Download token not found or already used.")
    pdf_bytes, expiry, filename, _company = entry
    if time.time() > expiry:
        pdf_store.pop(token, None)
        raise HTTPException(status_code=410, detail="Download link has expired. Please tailor again.")
    pdf_store.pop(token, None)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

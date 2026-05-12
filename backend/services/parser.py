import io
import re
import unicodedata

import pdfplumber
from docx import Document
from fastapi import HTTPException


MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB

SUPPORTED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def _sanitize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_from_pdf(file_bytes: bytes) -> str:
    try:
        pages = []
        links: list[str] = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
                for hl in (page.hyperlinks or []):
                    uri = hl.get("uri", "").strip()
                    if not uri:
                        continue
                    try:
                        x0 = hl.get("x0", 0)
                        top = hl.get("top", hl.get("y0", 0))
                        x1 = hl.get("x1", page.width)
                        bottom = hl.get("bottom", hl.get("y1", page.height))
                        link_text = (page.crop((x0, top, x1, bottom)).extract_text() or "").strip()
                    except Exception:
                        link_text = ""
                    entry = f"{link_text}: {uri}" if link_text else uri
                    if entry not in links:
                        links.append(entry)
        if not pages:
            raise HTTPException(
                status_code=422,
                detail="Could not extract text from this PDF. Try pasting the text instead.",
                headers={"X-Error-Code": "PARSE_FAILED"},
            )
        result = _sanitize("\n\n".join(pages))
        if links:
            result += "\n\n[HYPERLINKS IN DOCUMENT]\n" + "\n".join(links)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail="Could not read this PDF file. Try pasting the text instead.",
            headers={"X-Error-Code": "PARSE_FAILED"},
        ) from e


def extract_from_docx(file_bytes: bytes) -> str:
    try:
        doc = Document(io.BytesIO(file_bytes))
        parts = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue
            if para.style and para.style.name and "Heading" in para.style.name:
                parts.append(f"\n{text}")
            else:
                parts.append(text)
        if not parts:
            raise HTTPException(
                status_code=422,
                detail="Could not extract text from this DOCX file. Try pasting the text instead.",
                headers={"X-Error-Code": "PARSE_FAILED"},
            )
        return _sanitize("\n".join(parts))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail="Could not read this DOCX file. Try pasting the text instead.",
            headers={"X-Error-Code": "PARSE_FAILED"},
        ) from e


def parse_resume(file_bytes: bytes, filename: str, content_type: str) -> str:
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the 5 MB size limit.",
            headers={"X-Error-Code": "FILE_TOO_LARGE"},
        )

    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    is_pdf = content_type == "application/pdf" or ext == ".pdf"
    is_docx = (
        content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        or ext == ".docx"
    )

    if is_pdf:
        return extract_from_pdf(file_bytes)
    elif is_docx:
        return extract_from_docx(file_bytes)
    else:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are supported.",
            headers={"X-Error-Code": "UNSUPPORTED_FORMAT"},
        )

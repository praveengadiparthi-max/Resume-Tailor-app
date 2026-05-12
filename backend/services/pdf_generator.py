import io
import pdfplumber
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


NAVY = colors.HexColor("#1a3a5c")
DARK = colors.HexColor("#1a1a1a")
GRAY = colors.HexColor("#555555")

PAGE_H = LETTER[1]  # 792 pts
TOP_MARGIN = 0.65 * inch
BOT_MARGIN = 0.65 * inch


def _styles(compact: bool = False):
    # compact mode trims spacing ~15% to collapse a sparse last page
    sb = 7 if compact else 10       # section spaceBefore
    bl = 12 if compact else 13      # bullet/body leading
    ba = 1 if compact else 2        # body spaceAfter
    bul_sa = 0 if compact else 1    # bullet spaceAfter
    sr_sa = 1 if compact else 2     # skill_row spaceAfter
    jm_sa = 2 if compact else 3     # job_meta spaceAfter
    ct_sa = 5 if compact else 8     # contact spaceAfter
    hr_sa = 3 if compact else 4     # HR spaceAfter

    return {
        "name": ParagraphStyle(
            "name", fontName="Helvetica-Bold", fontSize=18, textColor=DARK,
            alignment=TA_CENTER, leading=22, spaceAfter=2 if compact else 3,
        ),
        "contact": ParagraphStyle(
            "contact", fontName="Helvetica", fontSize=9, textColor=GRAY,
            alignment=TA_CENTER, leading=12, spaceAfter=ct_sa,
        ),
        "section": ParagraphStyle(
            "section", fontName="Helvetica-Bold", fontSize=10, textColor=NAVY,
            spaceBefore=sb, spaceAfter=2, leading=13,
        ),
        "job_title": ParagraphStyle(
            "job_title", fontName="Helvetica-Bold", fontSize=10, textColor=DARK,
            leading=12 if compact else 13, spaceAfter=1,
        ),
        "job_meta": ParagraphStyle(
            "job_meta", fontName="Helvetica-Oblique", fontSize=9, textColor=GRAY,
            leading=11 if compact else 12, spaceAfter=jm_sa,
        ),
        "body": ParagraphStyle(
            "body", fontName="Helvetica", fontSize=9.5, textColor=DARK,
            leading=bl, spaceAfter=ba,
        ),
        "bullet": ParagraphStyle(
            "bullet", fontName="Helvetica", fontSize=9.5, textColor=DARK,
            leading=bl, leftIndent=10, firstLineIndent=0, spaceAfter=bul_sa,
        ),
        "skill_row": ParagraphStyle(
            "skill_row", fontName="Helvetica", fontSize=9.5, textColor=DARK,
            leading=bl, spaceAfter=sr_sa,
        ),
        "_hr_sa": hr_sa,
        "_job_spacer": 3 if compact else 5,
    }


def _section_block(story, title, s):
    story.append(Paragraph(title.upper(), s["section"]))
    story.append(HRFlowable(width="100%", thickness=0.75, color=NAVY, spaceAfter=s["_hr_sa"]))


def _contact_line(contact: dict) -> str:
    parts = []
    for key in ("email", "phone", "location", "linkedin", "github"):
        if contact.get(key):
            parts.append(contact[key])
    return "  |  ".join(parts)


def _esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_pdf(data: dict, compact: bool = False) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=TOP_MARGIN,
        bottomMargin=BOT_MARGIN,
    )
    s = _styles(compact)
    story = []

    # ── Header ──────────────────────────────────────────────────────────
    contact = data.get("contact", {})
    story.append(Paragraph(_esc(contact.get("name", "")), s["name"]))
    contact_line = _contact_line(contact)
    if contact_line:
        story.append(Paragraph(_esc(contact_line), s["contact"]))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=2))

    # ── Professional Summary ─────────────────────────────────────────────
    if data.get("summary"):
        _section_block(story, "Professional Summary", s)
        story.append(Paragraph(_esc(data["summary"]), s["body"]))

    # ── Technical Skills ────────────────────────────────────────────────
    skills = data.get("skills", {})
    groups = skills.get("groups", [])
    soft = skills.get("soft", [])
    if not groups and skills.get("technical"):
        groups = [{"label": "Technical", "items": ", ".join(skills["technical"])}]
    if groups or soft:
        _section_block(story, "Technical Skills", s)
        for grp in groups:
            label = _esc(grp.get("label", ""))
            items = _esc(grp.get("items", ""))
            if label or items:
                story.append(Paragraph(f"<b>{label}:</b>  {items}", s["skill_row"]))
        if soft:
            story.append(
                Paragraph(f'<b>Core Competencies:</b>  {_esc(", ".join(soft))}', s["skill_row"])
            )

    # ── Work Experience ──────────────────────────────────────────────────
    if data.get("experience"):
        _section_block(story, "Work Experience", s)
        for job in data["experience"]:
            title = _esc(job.get("title", ""))
            company = _esc(job.get("company", ""))
            location = _esc(job.get("location", ""))
            start = _esc(job.get("start_date", ""))
            end = _esc(job.get("end_date", ""))
            date_range = f"{start} – {end}" if start else end
            company_loc = f"{company}, {location}" if location else company
            header_block = KeepTogether([
                Paragraph(
                    f'<b>{title}</b><font color="#555555" size="8.5">    {date_range}</font>',
                    s["job_title"],
                ),
                Paragraph(f'<i>{company_loc}</i>', s["job_meta"]),
            ])
            story.append(header_block)
            for bullet in job.get("bullets", []):
                story.append(Paragraph(f"•  {_esc(bullet)}", s["bullet"]))
            story.append(Spacer(1, s["_job_spacer"]))

    # ── Education ────────────────────────────────────────────────────────
    if data.get("education"):
        _section_block(story, "Education", s)
        for edu in data["education"]:
            degree = _esc(edu.get("degree", ""))
            institution = _esc(edu.get("institution", ""))
            year = _esc(edu.get("graduation_year", ""))
            gpa = _esc(edu.get("gpa", ""))
            honors = _esc(edu.get("honors", ""))
            meta_parts = [institution]
            if gpa:
                meta_parts.append(f"GPA: {gpa}")
            if honors:
                meta_parts.append(honors)
            story.append(KeepTogether([
                Paragraph(
                    f'<b>{degree}</b><font color="#555555" size="8.5">    {year}</font>',
                    s["job_title"],
                ),
                Paragraph("  ·  ".join(meta_parts), s["job_meta"]),
                Spacer(1, 4),
            ]))

    # ── Certifications ───────────────────────────────────────────────────
    if data.get("certifications"):
        _section_block(story, "Certifications", s)
        for cert in data["certifications"]:
            if isinstance(cert, dict):
                name = _esc(cert.get("name", ""))
                url = (cert.get("url") or "").strip()
                text = (
                    f'•  <link href="{url}" color="#1a3a5c"><u>{name}</u></link>'
                    if url else f"•  {name}"
                )
            else:
                text = f"•  {_esc(str(cert))}"
            story.append(Paragraph(text, s["bullet"]))

    # ── Projects ─────────────────────────────────────────────────────────
    if data.get("projects"):
        _section_block(story, "Projects", s)
        for proj in data["projects"]:
            name = _esc(proj.get("name", ""))
            desc = _esc(proj.get("description", ""))
            techs = [_esc(t) for t in proj.get("technologies", [])]
            story.append(Paragraph(f"<b>{name}</b>", s["job_title"]))
            if desc:
                story.append(Paragraph(desc, s["body"]))
            if techs:
                story.append(Paragraph(
                    f'<font color="#555555" size="8.5">Technologies: {", ".join(techs)}</font>',
                    s["body"],
                ))
            story.append(Spacer(1, 4))

    doc.build(story)
    return buf.getvalue()


def _last_page_fill(pdf_bytes: bytes) -> tuple[int, float]:
    """Returns (page_count, fill_fraction_of_last_page)."""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        page_count = len(pdf.pages)
        if page_count <= 1:
            return page_count, 1.0
        last = pdf.pages[-1]
        words = last.extract_words()
        if not words:
            return page_count, 0.0
        # pdfplumber top-down coords: 'bottom' = distance from top of page to bottom of word
        max_bottom = max(float(w["bottom"]) for w in words)
        usable_height = last.height - TOP_MARGIN - BOT_MARGIN
        fill = (max_bottom - TOP_MARGIN) / usable_height
        return page_count, max(0.0, min(fill, 1.0))


def generate_pdf(data: dict) -> bytes:
    pdf_bytes = _build_pdf(data, compact=False)
    page_count, fill = _last_page_fill(pdf_bytes)
    if page_count > 1 and fill < 0.5:
        compact_bytes = _build_pdf(data, compact=True)
        compact_count, _ = _last_page_fill(compact_bytes)
        if compact_count < page_count:
            return compact_bytes
    return pdf_bytes

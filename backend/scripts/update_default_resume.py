"""
One-time script: adds AI-Assisted Development skills to the default resume PDF.
Run from the backend/ directory:
    python scripts/update_default_resume.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import anthropic
from services.parser import extract_from_pdf
from services.pdf_generator import generate_pdf

ASSETS_DIR = Path(__file__).parent.parent / "assets"

SCHEMA = '{"contact":{"name":"","email":"","phone":"","location":"","linkedin":"","github":""},"summary":"","experience":[{"title":"","company":"","location":"","start_date":"","end_date":"","bullets":["..."]}],"education":[{"degree":"","institution":"","graduation_year":"","gpa":"","honors":""}],"skills":{"groups":[{"label":"","items":""}],"soft":[""]},"certifications":[{"name":"","url":""}],"projects":[{"name":"","description":"","technologies":[""]}]}'

def main():
    pdf_path = next(ASSETS_DIR.glob("*.pdf"), None)
    if not pdf_path:
        print("No PDF found in assets/")
        sys.exit(1)

    print(f"Reading {pdf_path.name} ...")
    resume_text = extract_from_pdf(pdf_path.read_bytes())

    # Append the AI skills supplement so Claude includes them in the structured output
    ai_supplement = (
        "\n\nSKILLS SUPPLEMENT (add these to skills section):\n"
        "AI-Assisted Development: GitHub Copilot, Claude AI, Amazon Q, Cursor"
    )
    resume_text += ai_supplement

    print("Calling Claude to structure resume ...")
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=8192,
        system="You are a resume parser. Extract ALL content from the resume exactly as-is into JSON. Do not change, rewrite, or omit any content. Add any SKILLS SUPPLEMENT items to the appropriate skills group. Output ONLY valid JSON, no prose, no markdown fences.",
        messages=[{
            "role": "user",
            "content": f"Parse this resume into JSON matching exactly:\n{SCHEMA}\n\nResume:\n{resume_text}"
        }],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:])
        if "```" in raw:
            raw = raw[:raw.rindex("```")]

    data = json.loads(raw.strip())

    print("Generating updated PDF ...")
    pdf_bytes = generate_pdf(data)

    out_path = ASSETS_DIR / pdf_path.name
    out_path.write_bytes(pdf_bytes)
    print(f"Saved updated resume to {out_path}")


if __name__ == "__main__":
    main()

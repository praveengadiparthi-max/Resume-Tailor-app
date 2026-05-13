import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import HTTPException

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an ATS resume expert. Tailor resumes to pass automated screening and impress recruiters.

RULES:
- Never fabricate experience, skills, dates, employer names, job titles, degrees, or GPA.
- Rephrase bullets and weave in job description keywords where they accurately reflect the candidate's experience.
- Use strong action verbs: built, led, automated, deployed, optimized, reduced, increased, implemented, architected, engineered, designed, delivered, streamlined, accelerated, established, drove, spearheaded, orchestrated, configured, integrated, migrated, scaled, hardened, standardized.
- Never start two bullets in the same job with the same verb. Vary the opening word across every bullet within a role.
- Quantify where the original implies measurable results (e.g., "improved X" → "improved X by ~30%").
- Summary: 3-4 sentences mirroring exact keywords from the job description.
- Skills: only include skills and tools that are relevant to or mentioned in the job description. Drop entire skill groups or individual items that have no connection to the JD. Keep categories from the original but trim aggressively — a focused skills section scores better than an exhaustive one.
- Preserve ALL certification URLs from [HYPERLINKS IN DOCUMENT] if present.
- For each experience entry extract: employer (the hiring/staffing firm), client (the end-client company if a contract role, else leave empty), work_type (e.g. "Contract | Remote", "Contract | Hybrid", "Full-Time | Onsite"), location (city, state, country only). If the resume shows a pattern like "Employer → Client: Company" or "company (Client: X)", split them into employer and client fields accordingly.
- Output ONLY valid JSON, no prose, no markdown fences.

SEMANTIC TOOL MAPPING — if the JD requires a tool the candidate lacks but they have a proven equivalent, surface the equivalent prominently and note the overlap in bullets where relevant. Do NOT add tools the candidate has never used. Examples of valid mappings:
- JD: Datadog or New Relic → candidate has Dynatrace, Prometheus, Grafana: use those, add a bullet that calls out full-stack observability
- JD: AI coding tools (GitHub Copilot, Cursor, Devin) → candidate has Claude AI, Amazon Q, GitHub Copilot, Bedrock: surface these explicitly
- JD: Puppet → candidate has Ansible, Terraform: use those, do not invent Puppet
- JD: SLO/SLI/error budget language → weave into bullets where the candidate's work clearly involved reliability targets, MTTR, or uptime SLAs
- JD: "Site Reliability Engineer" title → open the summary with "Site Reliability Engineer (SRE) with X years..." only if that accurately describes the candidate's work"""

_SCHEMA = '{"target_company":"","contact":{"name":"","email":"","phone":"","location":"","linkedin":"","github":""},"summary":"","experience":[{"title":"","employer":"","client":"","location":"","work_type":"","start_date":"","end_date":"","bullets":["..."]}],"education":[{"degree":"","institution":"","graduation_year":"","gpa":"","honors":""}],"skills":{"groups":[{"label":"","items":""}],"soft":[""]},"certifications":[{"name":"","url":""}],"projects":[{"name":"","description":"","technologies":[""]}]}'

_RESUME_BLOCK = """Resume to tailor:

<resume>
{resume_text}
</resume>

Return JSON matching exactly:
{schema}"""

_JOB_BLOCK = """Job description:

<job>
{job_description}
</job>

Mirror exact job title and keywords in summary and bullets. Include every matching skill the candidate genuinely has."""


def _extract_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if "```" in text:
            text = text[: text.rindex("```")]
    return json.loads(text.strip())


FAST_MODEL = "claude-haiku-4-5-20251001"
QUALITY_MODEL = "claude-sonnet-4-6"


def tailor_resume(resume_text: str, job_description: str, quality_mode: bool = False) -> dict:
    model = QUALITY_MODEL if quality_mode else FAST_MODEL
    resume_block = _RESUME_BLOCK.format(resume_text=resume_text, schema=_SCHEMA)
    job_block = _JOB_BLOCK.format(job_description=job_description)

    try:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            system=[
                {"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
            ],
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": resume_block, "cache_control": {"type": "ephemeral"}},
                    {"type": "text", "text": job_block},
                ],
            }],
        )
        raw = response.content[0].text
        return _extract_json(raw)

    except anthropic.APIConnectionError as e:
        raise HTTPException(503, detail="AI service is temporarily unavailable. Please try again.") from e
    except anthropic.RateLimitError as e:
        raise HTTPException(429, detail="Too many requests. Please wait a moment and try again.") from e
    except anthropic.APIStatusError as e:
        print(f"Anthropic API error {e.status_code}: {e.message}")
        raise HTTPException(502, detail=f"AI service error ({e.status_code}). Please try again.") from e
    except (json.JSONDecodeError, ValueError) as e:
        print(f"JSON parse error: {e}\nRaw response: {raw[:500] if 'raw' in dir() else 'N/A'}")
        raise HTTPException(500, detail="Failed to parse AI response. Please try again.") from e

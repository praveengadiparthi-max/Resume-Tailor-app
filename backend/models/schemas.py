from pydantic import BaseModel, Field


class TailorTextRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=50000)
    job_description: str = Field(..., min_length=20, max_length=20000)
    quality_mode: bool = False


class TailorResponse(BaseModel):
    message: str
    download_token: str
    candidate_name: str

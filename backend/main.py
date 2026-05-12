import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from routers.resume import router

app = FastAPI(title="Resume Tailor API", version="1.0.0")

_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
_allowed_origins = [_origin] + [f"http://localhost:{p}" for p in range(5173, 5180) if f"http://localhost:{p}" != _origin]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok"}

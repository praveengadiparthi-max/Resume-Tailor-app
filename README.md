# Resume Tailor 📝

AI-powered resume tailoring tool that customizes your resume to match any job description using Claude AI.

## Overview

Resume Tailor automates the tedious task of rewriting your resume for each job application. Simply upload your resume (PDF/DOCX or paste text) and paste the job description — Claude AI will tailor your resume to highlight the most relevant skills and experience for that specific role.

**Key Features:**
- ✅ Upload resumes in **PDF**, **DOCX**, or paste as **plain text**
- ✨ AI-powered tailoring using **Claude Haiku** (fast) or **Claude Sonnet** (quality) — toggle in UI
- 📄 Download tailored resume as **professional PDF** — filename = your first + last name
- 🔒 API key stays local — never stored on servers
- ⚡ Fast processing with prompt caching; shows generation time per model in UI
- 🎯 ATS-optimised: skills filtered to JD-relevant only, semantic tool mapping (e.g. Dynatrace → Datadog equivalent)
- 🔗 Certification hyperlink URLs preserved from source PDF
- 📐 Smart PDF layout: auto-compacts spacing if last page is less than 50% full
- 🗂️ Auto-preloads your default resume on page load (place PDF in `backend/assets/`)

---

## Tech Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| **Frontend** | React 18 + Vite | Modern bundler, HMR, Tailwind CSS for styling |
| **Backend** | FastAPI + Python | Async API, fast development |
| **AI** | Anthropic Claude API | `claude-sonnet-4-6` with prompt caching |
| **PDF Input** | pdfplumber + python-docx | Extract text from PDF and DOCX files |
| **PDF Output** | reportlab | Pure Python PDF generation (no system deps) |
| **HTTP** | Axios (frontend) | Promise-based HTTP client |
| **File Upload** | react-dropzone | Drag & drop file upload UI |

---

## Project Structure

```
resume-tailor/
├── backend/                    # FastAPI Python server
│   ├── .env                    # Environment variables (gitignored)
│   ├── .env.example            # Template for .env
│   ├── requirements.txt        # Python dependencies
│   ├── venv/                   # Python virtual environment
│   ├── main.py                 # FastAPI app entry point
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── parser.py           # PDF/DOCX/text extraction
│   │   ├── claude_service.py   # Claude AI integration
│   │   └── pdf_generator.py    # reportlab PDF generation
│   └── routers/
│       └── resume.py           # API endpoints
│
├── frontend/                   # React + Vite web app
│   ├── public/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx             # Main state machine component
│   │   ├── index.css           # Tailwind imports
│   │   ├── components/
│   │   │   ├── ResumeInput.jsx        # Upload/paste toggle
│   │   │   ├── JobDescriptionInput.jsx
│   │   │   ├── TailorButton.jsx
│   │   │   ├── StatusMessage.jsx      # Progress bar
│   │   │   └── DownloadSection.jsx
│   │   └── api/
│   │       └── resumeApi.js    # axios HTTP client
│   ├── package.json
│   └── vite.config.js
│
├── package.json                # Root npm scripts (concurrently)
└── README.md                   # This file
```

---

## Start & Stop (Windows PowerShell)

### Start (frontend + backend together)
```powershell
cd C:\Users\Prave\Desktop\Claude-Project\resume-tailor
npm run dev
```
Opens frontend at http://localhost:5173 and backend at http://localhost:8000.

### Stop
```powershell
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### If ports are stuck
```powershell
@(8000, 5173) | ForEach-Object {
    $pid = (Get-NetTCPConnection -LocalPort $_ -ErrorAction SilentlyContinue).OwningProcess
    if ($pid) { Stop-Process -Id $pid -Force }
}
```

---

## Quick Start

### Prerequisites
- **Python 3.10+** (backend)
- **Node.js 18+** (frontend)
- **Anthropic API key** from [console.anthropic.com](https://console.anthropic.com)

### 1. Get the API Key

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Create an API key
4. Copy it (starts with `sk-ant-`)

### 2. Set Up the Project

```bash
# Clone the repo
git clone https://github.com/praveengadiparthi-max/DevOps-Code-Base.git
cd DevOps-Code-Base/resume-tailor

# Add your API key to .env
cp backend/.env.example backend/.env
# Edit backend/.env and replace 'your_anthropic_api_key_here' with your actual key
```

### 3. Run the App

From the `resume-tailor/` folder:

```bash
npm run dev
```

This single command starts **both** services with `concurrently`:
- **Backend**: FastAPI on `http://localhost:8000`
- **Frontend**: Vite React on `http://localhost:5173` (or next available port)

Open your browser to the URL shown in the terminal.

---

## How It Works

### 1. Upload Your Resume
- **Drag & drop** a PDF or DOCX file, OR
- **Paste** your resume text directly
- Supported formats: PDF, DOCX, plain text
- Max file size: 5 MB

### 2. Paste the Job Description
- Copy the full job posting into the text area
- More detail = better tailoring

### 3. Click "Tailor My Resume"
- Frontend sends resume + job description to the backend
- Backend:
  - Extracts text from your resume (PDF/DOCX)
  - Sends to Claude API with a structured prompt
  - Claude rewrites/highlights relevant experience
  - Generates a professional PDF with the tailored content
- Returns a download token

### 4. Download Your Tailored Resume
- Click the download button
- Receive a professionally formatted PDF
- Download link expires in 10 minutes (one-time use)

---

## API Endpoints

### `POST /api/tailor/upload`
Upload a resume file + job description.

**Request:**
```
Content-Type: multipart/form-data
file: (PDF or DOCX)
job_description: (string, 20-20,000 chars)
```

**Response:**
```json
{
  "message": "Resume tailored successfully",
  "download_token": "uuid-here"
}
```

### `POST /api/tailor/text`
Tailor using plain text resume.

**Request:**
```json
{
  "resume_text": "...",
  "job_description": "..."
}
```

**Response:**
Same as `/upload`

### `GET /api/download/{token}`
Download the tailored resume PDF.

**Response:** PDF file (one-time use, expires after 10 minutes)

---

## Backend Details

### Resume Parsing
**`services/parser.py`**
- **PDF**: Uses `pdfplumber` — page-by-page text extraction, joins with newlines
- **DOCX**: Uses `python-docx` — preserves heading structure
- **Text**: Accepts plain text input directly
- Validates file size (max 5 MB) and type

### Claude AI Integration
**`services/claude_service.py`**
- **Model**: `claude-sonnet-4-6` (fast & capable)
- **Prompt Caching**: System prompt is cached (ephemeral) for cost savings
- **Output**: Structured JSON with resume sections:
  - `contact`, `summary`, `experience[]`, `education[]`, `skills`, `projects[]`, `certifications`
- **Rules**: Never fabricates experience, only rewrites/reorders what exists

### PDF Generation
**`services/pdf_generator.py`**
- Uses **reportlab** (pure Python, no system dependencies)
- Generates professional single-column ATS-safe layout
- Navy blue section headers, Georgia serif font
- Optimized for 8.5×11" letter size

---

## Frontend Details

### State Management
**`src/App.jsx`** uses React state with 4 phases:
- `idle` — waiting for input
- `processing` — uploading & tailoring
- `ready` — download available
- `error` — something went wrong

### Components

| Component | Purpose |
|-----------|---------|
| `ResumeInput` | Tab toggle between file upload and text paste; uses `react-dropzone` |
| `JobDescriptionInput` | Text area for job description with char counter |
| `TailorButton` | Submit button, disabled while processing |
| `StatusMessage` | Fake progress bar (actual API time is opaque) |
| `DownloadSection` | Success card with download link |

### API Layer
**`src/api/resumeApi.js`**
- Centralized axios client with error handling
- Maps HTTP error codes to user-friendly messages
- 120s timeout for Claude processing

---

## Error Handling

| Error | HTTP | User Message |
|-------|------|--------------|
| File > 5 MB | 413 | "File exceeds the 5 MB size limit." |
| Wrong file type | 400 | "Only PDF and DOCX files are supported." |
| Unreadable file | 422 | "Could not extract text from this file. Try pasting the text instead." |
| Claude API down | 503 | "AI service is temporarily unavailable." |
| Claude rate limit | 429 | "Too many requests. Please wait a moment and try again." |
| Bad JSON response | 500 | "Something went wrong generating your resume. Please try again." |

---

## Configuration

### Environment Variables
Create `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
FRONTEND_ORIGIN=http://localhost:5173
```

- `ANTHROPIC_API_KEY` — Claude API key (required)
- `FRONTEND_ORIGIN` — Frontend URL for CORS (default: localhost:5173)

### Max File Size
Edit in `backend/services/parser.py`:
```python
MAX_FILE_BYTES = 5 * 1024 * 1024  # 5 MB
```

### Token Expiry
Edit in `backend/routers/resume.py`:
```python
TOKEN_TTL_SECONDS = 600  # 10 minutes
```

---

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
uvicorn main:app --reload --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Backend Testing
Test PDF generation:
```bash
cd backend
python -c "from services.pdf_generator import generate_pdf; pdf = generate_pdf({...}); print(f'Generated: {len(pdf)} bytes')"
```

---

## Deployment Considerations

### Production Checklist
- [ ] Set strong `ANTHROPIC_API_KEY` in production environment
- [ ] Use `FRONTEND_ORIGIN` matching your actual frontend domain
- [ ] Set `uvicorn --workers` to number of CPU cores
- [ ] Add rate limiting to `/api/tailor/*` endpoints
- [ ] Store PDFs to cloud storage (S3) instead of in-memory
- [ ] Add auth/user tracking if scaling to multiple users
- [ ] Set up logging for debugging

### Scaling Notes
- **In-memory PDF storage**: Currently stores PDFs in a dict with 10-min TTL. For production, use Redis or S3.
- **Async processing**: Consider Celery + Redis for long-running Claude requests
- **Caching**: Prompt caching saves ~30% on cost for repeated requests within 5 minutes

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173 (frontend)
lsof -ti:5173 | xargs kill -9
```

### API Key Not Working
- Check `backend/.env` exists with correct key
- Verify key starts with `sk-ant-`
- Try generating a new key at console.anthropic.com

### PDF Not Downloading
- Check download link hasn't expired (10-min TTL)
- Try refreshing the page
- Check browser console for errors

### Virtual Environment Issues
```bash
# Reset venv
cd backend
rm -rf venv
python -m venv venv
./venv/Scripts/pip install -r requirements.txt
```

---

## Security

✅ **Safe**
- API key stored locally in `.env` (gitignored)
- No resume/JD data persisted to database
- PDFs deleted after download (one-time use)
- `.gitignore` prevents accidental key commits

⚠️ **Be Careful**
- Don't commit `.env` to git
- PDFs are stored in-memory (not suitable for >100 concurrent users)
- Rate-limit API endpoints in production

---

## License

ISC

---

## Contributing

Found a bug? Want to add a feature? Feel free to open an issue or PR on GitHub.

### Ideas for Future Enhancements
- [ ] Support for DOCX resume output (not just PDF)
- [ ] Resume templates (different styles)
- [ ] Compare original vs. tailored side-by-side
- [ ] Save tailored resumes with history
- [ ] Batch tailor multiple jobs at once
- [ ] LinkedIn profile import
- [ ] Export to ATS plain-text format

---

## Support

Need help?
- Check the [Troubleshooting](#troubleshooting) section
- Review error messages in the UI
- Check backend logs in terminal
- Open an issue on GitHub

---

**Built with ❤️ using Claude AI, FastAPI, and React**

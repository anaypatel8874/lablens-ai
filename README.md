# LabLens AI - Medical & Pathology Report Analyzer

A production-quality AI-powered platform for analyzing medical laboratory reports.

## Features

- **Multi-format Upload**: PDF, JPG, JPEG, PNG including scanned documents
- **OCR & Text Extraction**: Pluggable OCR with Tesseract/AWS Textract support
- **100+ Test Coverage**: CBC, LFT, KFT, Lipid, Thyroid, Vitamins, Coagulation, Tumor Markers, and more
- **AI Analysis**: GPT-4o powered summaries in English, Hindi, and Hinglish
- **Trend Analysis**: Compare multiple reports over time
- **Ask My Report**: Grounded chatbot for report-specific questions
- **PDF Generation**: Professional downloadable summaries
- **Privacy & Security**: Encrypted storage, JWT auth, audit logs

## Tech Stack

- **Backend**: Python, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: React, TypeScript, Tailwind CSS, Vite
- **AI**: OpenAI GPT-4o (provider-agnostic)
- **OCR**: Tesseract / AWS Textract
- **PDF**: ReportLab
- **Charts**: Recharts

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OpenAI API key (optional, fallback summaries work without it)

### Setup

1. Clone the repository
2. Copy environment file:
   ```bash
   cp backend/.env.example backend/.env
   ```
3. Add your API keys to `.env`
4. Start services:
   ```bash
   docker-compose up --build
   ```
5. Access:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Development (without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Install Tesseract OCR on your system
cp .env.example .env
# Edit .env with your database URL and API keys
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
cd backend
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Architecture

```
backend/
  app/
    api/v1/          # API routes
    core/            # Config, security, logging
    db/              # Database setup
    models/          # SQLAlchemy models
    schemas/         # Pydantic schemas
    services/        # Business logic
      document/      # PDF/image processing
      ocr/           # OCR pipeline
      extraction/    # Test extraction & terminology
      validation/    # Reference ranges & classification
      analysis/      # Abnormality detection
      ai/            # LLM summaries & chat
      trends/        # Multi-report comparison
      pdf/           # PDF generation
      security/      # Storage & encryption
  tests/             # Unit tests

frontend/
  src/
    components/      # React components
    pages/           # Route pages
    services/        # API client
    hooks/           # Custom hooks
    context/         # Auth context
    types/           # TypeScript types
```

## Safety & Compliance

- Never diagnoses diseases from lab results alone
- Never prescribes medications
- Always recommends consulting healthcare professionals
- Encrypted file storage with signed URLs
- Role-based access control
- Audit logging for all report access

## License

Proprietary - LabLens AI

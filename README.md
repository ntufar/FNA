## Financial Narrative Analyzer (FNA)

The Financial Narrative Analyzer is an AI-powered platform for extracting, analyzing, and comparing narrative insights from financial reports. It consists of a FastAPI backend, a React + Vite frontend, PostgreSQL with pgvector, and optional local LLM integration via LM Studio.

### Repository Structure

```text
backend/    FastAPI app, services, database, migrations, tests
frontend/   React (Vite + TypeScript) app
postman/    Collections and environments for API testing
specs/      API contracts, plans, and product docs
docs/       Setup guides and PRD
```

### Prerequisites

- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 14+ with `pgvector` extension
- Optional: **LM Studio** for local LLM at `http://127.0.0.1:1234` (see `docs/LM_STUDIO_SETUP.md`)

### Quick Start

1) Clone and enter the project

```bash
git clone <your-fork-or-origin> FNA
cd FNA
```

2) Set up the database (local dev)

- Default local credentials are `postgres / qwerty123` and database `fna_development`.
- You can customize via environment variables later.

```bash
# Create DB and enable pgvector
psql -U postgres -h localhost -f backend/setup_database.sql

# Or run Alembic migrations (after creating the DB)
cd backend
alembic upgrade head
```

3) Backend: create venv, install, run

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: configure .env (see below). Defaults are suitable for local dev.

# Run API (hot reload)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
# API docs (dev): http://localhost:8000/docs
```

4) Frontend: install and run

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

### Configuration (.env)

Create `backend/.env` to override defaults from `src/core/config.py`. Useful keys:

```dotenv
# Environment: development | testing | production
ENVIRONMENT=development

# Database
DATABASE_URL=postgresql://postgres:qwerty123@localhost:5432/fna_development

# Security / Auth (change for production)
SECRET_KEY=dev-secret-key-change-in-production
JWT_EXPIRE_HOURS=24
JWT_REFRESH_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

# CORS
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# LM Studio (optional local LLM)
MODEL_NAME=qwen/qwen3-4b-2507
MODEL_API_URL=http://127.0.0.1:1234
MODEL_API_TIMEOUT=30

# SEC API
SEC_USER_AGENT=FNACompany contact@fnacompany.com
SEC_REQUEST_RATE_LIMIT=10
```

Defaults:
- Dev mode enables interactive docs at `/docs` and CORS for `localhost:5173`.
- Testing mode switches the DB to `fna_test`.

### Database and Vectors

The backend auto-configures vector support at startup:
- Tries to enable `pgvector` and create required indexes.
- Falls back to JSONB mode if `pgvector` is unavailable (slower similarity search).

SQL helper: `backend/setup_database.sql`
Runtime setup: `backend/src/database/vector_setup.py`

### Running Tests

Backend tests (pytest):

```bash
cd backend
source .venv/bin/activate
pytest
```

Integration tests will exercise real interfaces where possible.

### API

- Contract: `specs/001-fna-platform/contracts/api-v1.yaml`
- Docs (dev): `http://localhost:8000/docs`
- Versioned routes: `backend/src/api/v1/`

Key endpoints include:
- `v1/auth` authentication
- `v1/companies` company search and retrieval
- `v1/reports` report upload and listing
- `v1/analysis` narrative and sentiment analysis
- `v1/alerts` alerting

Health probes:
- `/health` overall
- `/health/ready` readiness
- `/health/live` liveness

### Postman

- Collection: `postman/FNA-API-Collection.json`
- Environments: `postman/environments/` (Development, Staging, Production)

Import the collection into Postman and select the appropriate environment. Update variables like `base_url`, tokens, and company IDs as needed.

### Reports: Download Flow and Processing (CLI-only)

- When you click "Download from SEC.gov" in the UI (Reports page), a report entry is created immediately with status **PENDING** and appears in the table.
- The backend does NOT auto-start LLM processing on download or upload. Processing is performed only via the CLI tool below.
- The "Re-process"/"Re-run Analysis" action resets status to **PENDING** only; run the CLI to process.

API responses (subset):

```json
{
  "report_id": "<uuid>",
  "message": "...",
  "processing_status": "PENDING",
  "file_path": "<relative path>",
  "estimated_processing_time": "..."
}
```

Endpoints involved:
- `POST v1/reports/download` → downloads report from SEC and creates a PENDING report
- `POST v1/reports/upload` → uploads a file and creates a PENDING report
- `GET  v1/reports/:id` → fetch report details
- `POST v1/reports/:id/analyze` → resets status to PENDING (no background processing)

Keep the Postman collection updated with these endpoints, request bodies, and example responses.

### CLI: Process Reports (Pending/Failed/All)

There is a command-line utility to process reports outside of the web background queue. Useful for batch reprocessing or server tasks.

File: `backend/src/cli/process_pending_reports.py`

Usage examples:

```bash
# Process PENDING (default)
python -m backend.src.cli.process_pending_reports

# Process FAILED only
python -m backend.src.cli.process_pending_reports --status failed

# Process PENDING and FAILED
python -m backend.src.cli.process_pending_reports --status all

# Limit to 5
python -m backend.src.cli.process_pending_reports --limit 5

# Filter by company ticker
python -m backend.src.cli.process_pending_reports --ticker AAPL

# Process a specific report ID
python -m backend.src.cli.process_pending_reports --report-id <UUID>

# Force reprocess even if COMPLETED
python -m backend.src.cli.process_pending_reports --status all --force
```

Notes:
- The CLI initializes the database and uses the same `DocumentProcessor` as the background tasks.
- Status transitions follow the data model: PENDING → PROCESSING → COMPLETED/FAILED; FAILED can be re-queued to PENDING.

### Frontend

- App root: `frontend/src`
- Router: `frontend/src/router/AppRouter.tsx`
- Services: `frontend/src/services/api.ts`
- Pages and components are organized by feature (e.g., `analysis`, `reports`, `alerts`).

Start with `npm run dev` and ensure the backend is running on `http://localhost:8000`.

### Migrations

Use Alembic for schema changes:

```bash
cd backend
alembic revision -m "your change message"
alembic upgrade head
```

Existing migrations live in `backend/alembic/versions/`.

### Useful Commands

```bash
# Backend
uvicorn src.main:app --reload

# Lint & format (backend)
flake8
isort . && black .

# Type-check (backend)
mypy

# Frontend
npm run lint
npm run type-check
```

### Troubleshooting

- If `pgvector` is missing, enable it in the database (`CREATE EXTENSION IF NOT EXISTS vector;`) or rely on the JSONB fallback.
- If CORS issues occur, update `CORS_ORIGINS` in `backend/.env`.
- Ensure Python 3.11+ and Node 18+ are active in your shell.

### License

This repository is provided for internal development; licensing to be determined.



# Career Network Copilot

Career Network Copilot is a human-in-the-loop assistant for students finding
professionals for internships, mentorship, career advice, and project
collaboration. It will rank manually supplied and permitted-source contacts,
explain recommendations, draft evidence-based outreach, and track outreach
progress. It will never scrape LinkedIn or send messages automatically.

## Phase 2 status

Phase 2 adds PostgreSQL/pgvector connection configuration, SQLAlchemy models,
Alembic migrations, and an unauthenticated student profile API. Later phases
will add authentication, matching, integrations, and outreach flows.

## Architecture

```text
Next.js + TypeScript frontend
          │ REST/JSON
          ▼
FastAPI + Pydantic backend
          │ SQLAlchemy/Alembic
          ▼
PostgreSQL 16 + pgvector
```

The frontend owns accessible presentation and browser interaction. The backend
will own authorization, validation, matching, message grounding, integrations,
and analytics. PostgreSQL is the system of record; pgvector is optional for
semantic similarity and will not replace explainable deterministic scoring.

## Planned repository structure

```text
frontend/       Next.js application
backend/        FastAPI application and Python tests
database/       PostgreSQL initialization and migration home
docs/            Architecture, privacy, and operational decisions
tests/           End-to-end test home
.github/         Continuous integration
```

## Technology choices

- Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, and pytest
- Next.js, TypeScript, Tailwind CSS, Vitest, and Playwright
- PostgreSQL 16 with the pgvector extension
- Docker Compose for the local database
- GitHub Actions for reproducible checks

## Local setup (PowerShell on Windows)

Prerequisites are listed below. From the repository root:

```powershell
Copy-Item .env.example .env
docker compose up -d db

py -3.12 -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e "backend[dev]"

Set-Location frontend
npm install
Set-Location ..
```

Run the backend:

```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```

Run the frontend in a second PowerShell window:

```powershell
Set-Location frontend
npm run dev
```

The backend health endpoint is `http://localhost:8000/health`.
Interactive API documentation will be at `http://localhost:8000/docs` once the
backend is running.

## Database migrations

With Docker Desktop running and the database service started:

```powershell
Set-Location C:\Users\Admin\Documents\coding-journey\career-network-copilot
docker compose up -d db
.\backend\.venv\Scripts\Activate.ps1
Set-Location backend
alembic -c alembic.ini upgrade head
Set-Location ..
```

The migration creates `student_profiles`, `career_goals`, `skills`, and
`student_skills`. Alembic and the application read `DATABASE_URL` from `.env`.

## Checks

```powershell
.\backend\.venv\Scripts\Activate.ps1
python -m pytest
python -m ruff check backend
Set-Location frontend
npm run lint
npm run typecheck
npm run test
Set-Location ..
```

## Matching algorithm

The planned transparent score uses role (25%), company/industry (20%), shared
context (20%), skills/projects (15%), location (10%), and networking goal
relevance (10%). Each factor will be 0–100, and explanations will expose every
factor. Sensitive characteristics will not be used.

## LinkedIn compliance and privacy

The product will accept user-entered public profile details and source URLs but
will not scrape LinkedIn, automate browser activity, send connection requests,
or send messages. Recommendations are assistance, not endorsements. Resumes
will be private by default, data deletion will be user-controlled, and external
API data will be minimized and attributed.

## Documentation

- [Architecture decisions](docs/architecture.md)
- [Privacy notice](docs/privacy.md)

## Known limitations and future improvements

Phase 2 does not include authentication, contact management, matching,
GitHub/CSV integrations, message generation, outreach tracking, seed data, or
end-to-end journeys. Those are planned for later phases.

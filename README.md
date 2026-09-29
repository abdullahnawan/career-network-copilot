# Career Network Copilot

Career Network Copilot is a human-in-the-loop assistant for students finding
professionals for internships, mentorship, career advice, and project
collaboration. It will rank manually supplied and permitted-source contacts,
explain recommendations, draft evidence-based outreach, and track outreach
progress. It will never scrape LinkedIn or send messages automatically.

## Phase 4 status

Phase 4 adds a compliant contact directory, manual and CSV imports, filters,
pagination, and deterministic rule-based matching. Profile links are stored as
references only; the application never fetches or scrapes them.

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
Set-Content .env.local "NEXT_PUBLIC_API_URL=http://127.0.0.1:8000"
Set-Location ..
```

Run the backend in a PowerShell window:

```powershell
.\backend\.venv\Scripts\Activate.ps1
uvicorn backend.app.main:app --reload --port 8000
```

Run the frontend in a second PowerShell window:

```powershell
Set-Location frontend
npm run dev
```

The frontend reads `NEXT_PUBLIC_API_URL` from `frontend/.env.local` and uses
`http://127.0.0.1:8000` by default. The backend allows local development
origins at `http://localhost:3000` and `http://127.0.0.1:3000`.

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

The migrations create `student_profiles`, `career_goals`, `skills`,
`student_skills`, and `contacts`. Alembic and the application read
`DATABASE_URL` from `.env`.

The example CSV at `examples/contacts.example.csv` contains fictional records.
CSV imports require `full_name` and `source_name`; the other contact fields are
optional. Imports are limited to 500 rows and 5 MB. Users must have permission
to use every imported record.

## Checks

```powershell
.\backend\.venv\Scripts\Activate.ps1
python -m pytest
python -m ruff check backend
Set-Location frontend
npm run lint
npm run typecheck
npm run test
npm run build
npm audit
Set-Location ..
```

## Matching algorithm

Phase 4 uses deterministic token overlap only. Each component is 0 or 100:

```text
total_score =
  role_score     × 0.30 +
  industry_score × 0.20 +
  location_score × 0.15 +
  school_score   × 0.15 +
  skills_score   × 0.20
```

Role, industry, and location targets come from career goals. School comes from
the student profile, and skills come from the student's saved skills. A
component is 100 when normalized words overlap and 0 otherwise. Every returned
match includes its component scores and plain-language reasons. No embeddings,
LLM, sensitive traits, or fabricated facts are used.

The matches page is explicitly labeled as rule-based matching, not AI ranking.

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

Phase 4 does not include authentication, GitHub/API discovery, message
generation, outreach tracking, embeddings, or automated communication. Those
are planned for later phases.

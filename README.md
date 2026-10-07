# SENTRA Backend (Phase 2)

FastAPI + PostgreSQL + JWT authentication.

## Requirements

- Python 3.11 or 3.12
- Docker Desktop (for PostgreSQL), OR a local PostgreSQL install

## Setup

    cd C:\dev\sentra_backend

    # 1. Start PostgreSQL
    docker compose up -d

    # 2. Create and activate a virtual environment
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1

    # 3. Install dependencies
    pip install -r requirements.txt

    # 4. Create your .env from the example
    Copy-Item .env.example .env

    # 5. Run the API
    uvicorn app.main:app --reload --port 8000

Open http://localhost:8000/docs for Swagger UI.

## Endpoints (Phase 2)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET  | /                     | No  | API info |
| GET  | /health               | No  | Health check |
| POST | /auth/register        | No  | Create account |
| POST | /auth/login           | No  | Get JWT token |
| GET  | /users/me             | Yes | Current user + contacts |
| GET  | /users/me/emergency-contacts    | Yes | List contacts |
| POST | /users/me/emergency-contacts    | Yes | Add contact |
| DELETE | /users/me/emergency-contacts/{id} | Yes | Remove contact |

## Running tests

    pytest -v

Tests use SQLite in-memory and do not touch your PostgreSQL data.

## What Phase 2 does NOT include

- Risk ML model (Phase 3)
- Anomaly detection (Phase 4)
- Privacy state machine (Phase 4)
- Trips, routes, incidents tables (later phases)
- Flutter integration (Phase 5)

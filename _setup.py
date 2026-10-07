import pathlib

root = pathlib.Path(r"C:\dev\sentra_backend")
(root / "tests").mkdir(parents=True, exist_ok=True)

files = {}

files["tests/conftest.py"] = '''import os

os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["DATABASE_URL"] = "sqlite:///./test_sentra.db"
os.environ["JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite:///./test_sentra.db",
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)
'''

files["tests/test_auth.py"] = '''def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


def test_register_login_and_me(client):
    payload = {
        "email": "test@example.com",
        "name": "Test User",
        "phone": "+91 90000 00001",
        "password": "secret123",
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["email"] == "test@example.com"
    assert "id" in body
    assert "password" not in body
    assert "password_hash" not in body

    r2 = client.post("/auth/register", json=payload)
    assert r2.status_code == 400

    r3 = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "secret123"},
    )
    assert r3.status_code == 200, r3.text
    token = r3.json()["access_token"]
    assert token

    r4 = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 200
    assert r4.json()["email"] == "test@example.com"

    r5 = client.get("/users/me")
    assert r5.status_code == 401


def test_login_wrong_password(client):
    client.post(
        "/auth/register",
        json={
            "email": "wrong@example.com",
            "name": "W",
            "phone": "1",
            "password": "secret123",
        },
    )
    r = client.post(
        "/auth/login",
        data={"username": "wrong@example.com", "password": "bad"},
    )
    assert r.status_code == 401


def test_emergency_contacts_flow(client):
    r = client.post(
        "/auth/register",
        json={
            "email": "contacts@example.com",
            "name": "C",
            "phone": "1",
            "password": "secret123",
        },
    )
    assert r.status_code == 201

    r_login = client.post(
        "/auth/login",
        data={"username": "contacts@example.com", "password": "secret123"},
    )
    token = r_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rc = client.post(
        "/users/me/emergency-contacts",
        json={
            "name": "Riya",
            "phone": "+91 90000 11111",
            "relationship": "Sister",
            "priority": 1,
        },
        headers=headers,
    )
    assert rc.status_code == 201, rc.text
    contact_id = rc.json()["id"]

    rl = client.get("/users/me/emergency-contacts", headers=headers)
    assert rl.status_code == 200
    assert len(rl.json()) == 1

    rd = client.delete(
        f"/users/me/emergency-contacts/{contact_id}", headers=headers
    )
    assert rd.status_code == 204

    rl2 = client.get("/users/me/emergency-contacts", headers=headers)
    assert len(rl2.json()) == 0
'''

files["README.md"] = """# SENTRA Backend (Phase 2)

FastAPI + PostgreSQL + JWT authentication.

## Requirements

- Python 3.11 or 3.12
- Docker Desktop (for PostgreSQL), OR a local PostgreSQL install

## Setup

    cd C:\\dev\\sentra_backend

    # 1. Start PostgreSQL
    docker compose up -d

    # 2. Create and activate a virtual environment
    python -m venv .venv
    .\\.venv\\Scripts\\Activate.ps1

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
"""

for rel_path, content in files.items():
    target = root / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print("wrote:", target)

print()
print("Done. All Phase 2 files written.")
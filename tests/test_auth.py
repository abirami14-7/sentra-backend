def test_root(client):
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

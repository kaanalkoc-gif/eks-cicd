"""Integration tests for JWT auth endpoints."""


def test_register_user(client):
    """POST /auth/register creates a user and returns 201 without password."""
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client, registered_user):
    """POST /auth/register returns 409 when email is already taken."""
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    assert response.status_code == 409
    assert response.json()["code"] == "USER_EMAIL_EXISTS"


def test_login_success(client, registered_user):
    """POST /auth/login returns a bearer token for valid credentials."""
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


def test_login_invalid_password(client, registered_user):
    """POST /auth/login returns 401 for wrong password."""
    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_read_current_user(client, auth_headers):
    """GET /auth/me returns the authenticated user."""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_read_current_user_without_token(client):
    """GET /auth/me returns 401 when no Bearer token is sent."""
    response = client.get("/auth/me")
    assert response.status_code == 401

"""Integration tests for IP-based rate limiting."""

import pytest

from app.rate_limit import limiter

pytestmark = pytest.mark.rate_limit


@pytest.fixture(autouse=True)
def enable_rate_limiter():
    """Turn rate limiting on and clear in-memory counters between tests."""
    limiter.enabled = True
    limiter.reset()
    yield
    limiter.enabled = False
    limiter.reset()


def test_login_rate_limit_exceeded(client, registered_user):
    """POST /auth/login returns 429 after exceeding 10 requests per minute."""
    for _ in range(10):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "wrong-password"},
        )
        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"


def test_register_rate_limit_exceeded(client):
    """POST /auth/register returns 429 after exceeding 10 requests per minute."""
    for index in range(10):
        response = client.post(
            "/auth/register",
            json={"email": f"user{index}@example.com", "password": "password123"},
        )
        assert response.status_code == 201

    response = client.post(
        "/auth/register",
        json={"email": "one-too-many@example.com", "password": "password123"},
    )
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"


def test_create_item_rate_limit_exceeded(client, auth_headers):
    """POST /items returns 429 after exceeding 60 write requests per minute."""
    for index in range(60):
        response = client.post(
            "/items",
            headers=auth_headers,
            json={"name": f"Widget {index}", "price": 1.0},
        )
        assert response.status_code == 201

    response = client.post(
        "/items",
        headers=auth_headers,
        json={"name": "One too many", "price": 1.0},
    )
    assert response.status_code == 429
    assert response.json()["code"] == "RATE_LIMIT_EXCEEDED"

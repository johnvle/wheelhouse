"""Tests for JWT auth middleware and get_current_user dependency."""

import os
import time
from uuid import UUID, uuid4

import jwt
import pytest
from fastapi import Depends
from httpx import ASGITransport, AsyncClient

# conftest.py sets env vars before app imports
from app.auth import get_current_user
from app.main import app

JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
ALGORITHM = "HS256"


# Register a test-only route that requires authentication
@app.get("/api/v1/test-auth")
async def _test_auth_route(user: UUID = Depends(get_current_user)):
    return {"user_id": str(user)}


def _make_token(
    user_id: str | None = None,
    expired: bool = False,
    audience: str = "authenticated",
) -> str:
    """Create a test JWT token."""
    now = int(time.time())
    payload = {
        "aud": audience,
        "iat": now,
        "exp": now - 10 if expired else now + 3600,
    }
    if user_id is not None:
        payload["sub"] = user_id
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


@pytest.fixture
def user_id() -> str:
    return str(uuid4())


@pytest.fixture
def valid_token(user_id: str) -> str:
    return _make_token(user_id=user_id)


@pytest.fixture
def expired_token(user_id: str) -> str:
    return _make_token(user_id=user_id, expired=True)


# --- Health endpoint (public) ---


@pytest.mark.asyncio
async def test_health_no_auth_required():
    """GET /health should succeed without any auth header."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# --- Missing / malformed auth ---


@pytest.mark.asyncio
async def test_missing_auth_header_returns_401():
    """Requests without Authorization header should receive 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/test-auth")
    assert resp.status_code == 401
    assert "missing" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invalid_auth_header_format_returns_401():
    """Auth header without 'Bearer <token>' format should receive 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": "Basic abc123"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_returns_401():
    """Requests with a malformed JWT should receive 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": "Bearer not-a-valid-jwt"},
        )
    assert resp.status_code == 401
    assert "invalid" in resp.json()["detail"].lower()


# --- Expired / wrong secret / wrong audience ---


@pytest.mark.asyncio
async def test_expired_token_returns_401(expired_token: str):
    """Requests with an expired JWT should receive 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_wrong_secret_returns_401(user_id: str):
    """JWT signed with wrong secret should receive 401."""
    token = jwt.encode(
        {"sub": user_id, "aud": "authenticated", "exp": int(time.time()) + 3600},
        "wrong-secret",
        algorithm=ALGORITHM,
    )
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_wrong_audience_returns_401(user_id: str):
    """JWT with wrong audience claim should receive 401."""
    token = _make_token(user_id=user_id, audience="wrong-audience")
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_sub_claim_returns_401():
    """JWT without 'sub' claim should receive 401."""
    token = _make_token(user_id=None)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 401


# --- Valid token ---


@pytest.mark.asyncio
async def test_valid_token_returns_user_id(valid_token: str, user_id: str):
    """Valid JWT should pass middleware and get_current_user returns correct UUID."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
    assert resp.status_code == 200
    assert resp.json()["user_id"] == user_id


@pytest.mark.asyncio
async def test_get_current_user_returns_uuid_type(valid_token: str, user_id: str):
    """get_current_user should return a UUID object, not a string."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/test-auth",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
    assert resp.status_code == 200
    # Verify it's a valid UUID by parsing it
    returned_id = UUID(resp.json()["user_id"])
    assert returned_id == UUID(user_id)

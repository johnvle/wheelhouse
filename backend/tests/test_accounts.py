"""Tests for accounts CRUD endpoints."""

import os
import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models.account import Account

JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
ALGORITHM = "HS256"


def _make_token(user_id: str) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "aud": "authenticated",
        "iat": now,
        "exp": now + 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def _make_account(user_id: UUID, **overrides) -> Account:
    """Create a fake Account ORM instance for testing."""
    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "name": "Test Account",
        "broker": "robinhood",
        "tax_treatment": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    account = MagicMock(spec=Account)
    for k, v in defaults.items():
        setattr(account, k, v)
    return account


class _FakeQuery:
    """Minimal mock that chains .filter().all() / .filter().first()."""

    def __init__(self, results):
        self._results = results

    def filter(self, *args):
        return self

    def all(self):
        return self._results

    def first(self):
        return self._results[0] if self._results else None


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def auth_headers(user_id: UUID) -> dict:
    token = _make_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


# --- GET /api/v1/accounts ---


@pytest.mark.asyncio
async def test_list_accounts_returns_user_accounts(user_id: UUID, auth_headers: dict):
    """GET /api/v1/accounts returns only the authenticated user's accounts."""
    acct1 = _make_account(user_id, name="Acct1")
    acct2 = _make_account(user_id, name="Acct2")

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([acct1, acct2])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/accounts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["name"] == "Acct1"
        assert data[1]["name"] == "Acct2"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_accounts_empty(user_id: UUID, auth_headers: dict):
    """GET /api/v1/accounts returns empty list when user has no accounts."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/accounts", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_accounts_requires_auth():
    """GET /api/v1/accounts without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/accounts")
    assert resp.status_code == 401


# --- POST /api/v1/accounts ---


@pytest.mark.asyncio
async def test_create_account_success(user_id: UUID, auth_headers: dict):
    """POST /api/v1/accounts creates an account and returns it."""
    now = datetime.now(timezone.utc)
    created_id = uuid4()

    mock_db = MagicMock()

    def fake_refresh(obj):
        obj.id = created_id
        obj.user_id = user_id
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/accounts",
                json={"name": "My Robinhood", "broker": "robinhood"},
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My Robinhood"
        assert data["broker"] == "robinhood"
        assert data["tax_treatment"] is None
        assert data["user_id"] == str(user_id)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_account_with_tax_treatment(user_id: UUID, auth_headers: dict):
    """POST /api/v1/accounts with tax_treatment sets the field."""
    now = datetime.now(timezone.utc)

    mock_db = MagicMock()

    def fake_refresh(obj):
        obj.id = uuid4()
        obj.user_id = user_id
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/accounts",
                json={
                    "name": "Roth IRA",
                    "broker": "merrill",
                    "tax_treatment": "roth_ira",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["tax_treatment"] == "roth_ira"
        assert data["broker"] == "merrill"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_account_invalid_broker(auth_headers: dict):
    """POST /api/v1/accounts with invalid broker returns 422."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/accounts",
                json={"name": "Bad", "broker": "nonexistent_broker"},
                headers=auth_headers,
            )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_account_missing_name(auth_headers: dict):
    """POST /api/v1/accounts without name returns 422."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/accounts",
                json={"broker": "robinhood"},
                headers=auth_headers,
            )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


# --- PATCH /api/v1/accounts/{id} ---


@pytest.mark.asyncio
async def test_update_account_success(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/accounts/{id} updates fields and returns updated account."""
    acct = _make_account(user_id, name="Old Name", broker="robinhood")
    acct_id = acct.id

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([acct])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/accounts/{acct_id}",
                json={"name": "New Name"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New Name"
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_account_broker(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/accounts/{id} can update broker."""
    acct = _make_account(user_id, broker="robinhood")

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([acct])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/accounts/{acct.id}",
                json={"broker": "merrill"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert acct.broker == "merrill"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_account_not_found(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/accounts/{id} returns 404 if account doesn't exist."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/accounts/{uuid4()}",
                json={"name": "Updated"},
                headers=auth_headers,
            )
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_account_other_user(auth_headers: dict):
    """PATCH returns 404 if account belongs to another user (filtered by user_id)."""
    other_user = uuid4()
    acct = _make_account(other_user)

    mock_db = MagicMock()
    # Filter by user_id means this account won't be found
    mock_db.query.return_value = _FakeQuery([])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/accounts/{acct.id}",
                json={"name": "Hacked"},
                headers=auth_headers,
            )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_account_no_fields(user_id: UUID, auth_headers: dict):
    """PATCH with empty body is valid (no changes applied)."""
    acct = _make_account(user_id, name="Same Name")

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([acct])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/accounts/{acct.id}",
                json={},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert acct.name == "Same Name"
    finally:
        app.dependency_overrides.clear()


# --- Response schema ---


@pytest.mark.asyncio
async def test_response_uses_account_response_schema(
    user_id: UUID, auth_headers: dict
):
    """All responses use AccountResponse schema with expected fields."""
    acct = _make_account(
        user_id, name="Schema Test", broker="other", tax_treatment="taxable"
    )

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([acct])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/accounts", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()[0]
        expected_fields = {
            "id",
            "user_id",
            "name",
            "broker",
            "tax_treatment",
            "created_at",
            "updated_at",
        }
        assert set(data.keys()) == expected_fields
    finally:
        app.dependency_overrides.clear()

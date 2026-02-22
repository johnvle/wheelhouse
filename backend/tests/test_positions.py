"""Tests for positions CRUD endpoints."""

import os
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models.account import Account
from app.models.position import Position

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


def _make_position(user_id: UUID, account_id: UUID, **overrides) -> Position:
    now = datetime.now(timezone.utc)
    defaults = {
        "id": uuid4(),
        "user_id": user_id,
        "account_id": account_id,
        "ticker": "AAPL",
        "type": "COVERED_CALL",
        "status": "OPEN",
        "open_date": date(2026, 1, 15),
        "expiration_date": date(2026, 2, 21),
        "close_date": None,
        "strike_price": Decimal("150.00"),
        "contracts": 1,
        "multiplier": 100,
        "premium_per_share": Decimal("3.50"),
        "open_fees": Decimal("0.65"),
        "close_fees": Decimal("0"),
        "close_price_per_share": None,
        "outcome": None,
        "roll_group_id": None,
        "notes": None,
        "tags": None,
        "created_at": now,
        "updated_at": now,
    }
    defaults.update(overrides)
    position = MagicMock(spec=Position)
    for k, v in defaults.items():
        setattr(position, k, v)
    return position


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


def _valid_position_body(account_id: UUID) -> dict:
    return {
        "account_id": str(account_id),
        "ticker": "aapl",
        "type": "COVERED_CALL",
        "open_date": "2026-01-15",
        "expiration_date": "2026-02-21",
        "strike_price": "150.00",
        "contracts": 1,
        "premium_per_share": "3.50",
    }


# --- POST /api/v1/positions ---


@pytest.mark.asyncio
async def test_create_position_success(user_id: UUID, auth_headers: dict):
    """POST /api/v1/positions creates a position and returns it with computed fields."""
    account = _make_account(user_id)
    account_id = account.id
    now = datetime.now(timezone.utc)

    mock_db = MagicMock()

    # query(Account).filter(...).first() returns the account
    account_query = _FakeQuery([account])
    mock_db.query.return_value = account_query

    def fake_refresh(obj):
        obj.id = uuid4()
        obj.user_id = user_id
        obj.account_id = account_id
        obj.ticker = "AAPL"
        obj.type = "COVERED_CALL"
        obj.status = "OPEN"
        obj.open_date = date(2026, 1, 15)
        obj.expiration_date = date(2026, 2, 21)
        obj.close_date = None
        obj.strike_price = Decimal("150.00")
        obj.contracts = 1
        obj.multiplier = 100
        obj.premium_per_share = Decimal("3.50")
        obj.open_fees = Decimal("0")
        obj.close_fees = Decimal("0")
        obj.close_price_per_share = None
        obj.outcome = None
        obj.roll_group_id = None
        obj.notes = None
        obj.tags = None
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/positions",
                json=_valid_position_body(account_id),
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["ticker"] == "AAPL"
        assert data["type"] == "COVERED_CALL"
        assert data["status"] == "OPEN"
        assert data["user_id"] == str(user_id)
        # Computed fields
        assert "premium_total" in data
        assert "collateral" in data
        assert "roc_period" in data
        assert "dte" in data
        assert "annualized_roc" in data
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_ticker_uppercased(user_id: UUID, auth_headers: dict):
    """POST /api/v1/positions uppercases the ticker before storage."""
    account = _make_account(user_id)
    now = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([account])

    def fake_refresh(obj):
        # Do not overwrite ticker — let it keep the value set by the router
        obj.id = uuid4()
        obj.user_id = user_id
        obj.account_id = account.id
        obj.status = "OPEN"
        obj.close_date = None
        obj.close_fees = Decimal("0")
        obj.close_price_per_share = None
        obj.outcome = None
        obj.roll_group_id = None
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            body = _valid_position_body(account.id)
            body["ticker"] = "tsla"  # lowercase
            resp = await client.post(
                "/api/v1/positions",
                json=body,
                headers=auth_headers,
            )
        assert resp.status_code == 201
        # Check the ORM object was created with uppercased ticker
        created_obj = mock_db.add.call_args[0][0]
        assert created_obj.ticker == "TSLA"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_invalid_account(user_id: UUID, auth_headers: dict):
    """POST /api/v1/positions returns 400 if account_id doesn't belong to user."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])  # Account not found

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/positions",
                json=_valid_position_body(uuid4()),
                headers=auth_headers,
            )
        assert resp.status_code == 400
        assert "account" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_with_optional_fields(user_id: UUID, auth_headers: dict):
    """POST /api/v1/positions accepts optional fields: multiplier, open_fees, notes, tags."""
    account = _make_account(user_id)
    now = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([account])

    def fake_refresh(obj):
        obj.id = uuid4()
        obj.user_id = user_id
        obj.account_id = account.id
        obj.status = "OPEN"
        obj.close_date = None
        obj.close_fees = Decimal("0")
        obj.close_price_per_share = None
        obj.outcome = None
        obj.roll_group_id = None
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            body = _valid_position_body(account.id)
            body["multiplier"] = 50
            body["open_fees"] = "1.30"
            body["notes"] = "Test trade"
            body["tags"] = ["earnings", "weekly"]
            resp = await client.post(
                "/api/v1/positions",
                json=body,
                headers=auth_headers,
            )
        assert resp.status_code == 201
        created_obj = mock_db.add.call_args[0][0]
        assert created_obj.multiplier == 50
        assert created_obj.open_fees == Decimal("1.30")
        assert created_obj.notes == "Test trade"
        assert created_obj.tags == ["earnings", "weekly"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_requires_auth():
    """POST /api/v1/positions without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.post(
            "/api/v1/positions",
            json=_valid_position_body(uuid4()),
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_position_missing_required_fields(auth_headers: dict):
    """POST /api/v1/positions without required fields returns 422."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/positions",
                json={"ticker": "AAPL"},  # Missing most required fields
                headers=auth_headers,
            )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_invalid_type(user_id: UUID, auth_headers: dict):
    """POST /api/v1/positions with invalid type returns 422."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            body = _valid_position_body(uuid4())
            body["type"] = "INVALID_TYPE"
            resp = await client.post(
                "/api/v1/positions",
                json=body,
                headers=auth_headers,
            )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_response_has_computed_fields(
    user_id: UUID, auth_headers: dict
):
    """Response includes all computed fields: premium_total, premium_net, collateral, roc_period, dte, annualized_roc."""
    account = _make_account(user_id)
    now = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([account])

    def fake_refresh(obj):
        obj.id = uuid4()
        obj.user_id = user_id
        obj.account_id = account.id
        obj.ticker = "AAPL"
        obj.type = "COVERED_CALL"
        obj.status = "OPEN"
        obj.open_date = date(2026, 1, 15)
        obj.expiration_date = date(2026, 2, 21)
        obj.close_date = None
        obj.strike_price = Decimal("150.00")
        obj.contracts = 2
        obj.multiplier = 100
        obj.premium_per_share = Decimal("3.50")
        obj.open_fees = Decimal("1.30")
        obj.close_fees = Decimal("0")
        obj.close_price_per_share = None
        obj.outcome = None
        obj.roll_group_id = None
        obj.notes = None
        obj.tags = None
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            body = _valid_position_body(account.id)
            body["contracts"] = 2
            body["open_fees"] = "1.30"
            resp = await client.post(
                "/api/v1/positions",
                json=body,
                headers=auth_headers,
            )
        assert resp.status_code == 201
        data = resp.json()
        # premium_total = 3.50 * 2 * 100 = 700
        assert Decimal(str(data["premium_total"])) == Decimal("700.00")
        # premium_net = 700 - 1.30 - 0 = 698.70
        assert Decimal(str(data["premium_net"])) == Decimal("698.70")
        # collateral = 150 * 2 * 100 = 30000
        assert Decimal(str(data["collateral"])) == Decimal("30000.00")
        # roc_period = 698.70 / 30000 ≈ 0.02329
        assert Decimal(str(data["roc_period"])) > 0
        # dte and annualized_roc exist
        assert "dte" in data
        assert "annualized_roc" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_position_cash_secured_put(user_id: UUID, auth_headers: dict):
    """POST /api/v1/positions works with CASH_SECURED_PUT type."""
    account = _make_account(user_id)
    now = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([account])

    def fake_refresh(obj):
        obj.id = uuid4()
        obj.user_id = user_id
        obj.account_id = account.id
        obj.status = "OPEN"
        obj.close_date = None
        obj.close_fees = Decimal("0")
        obj.close_price_per_share = None
        obj.outcome = None
        obj.roll_group_id = None
        obj.created_at = now
        obj.updated_at = now

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            body = _valid_position_body(account.id)
            body["type"] = "CASH_SECURED_PUT"
            resp = await client.post(
                "/api/v1/positions",
                json=body,
                headers=auth_headers,
            )
        assert resp.status_code == 201
        created_obj = mock_db.add.call_args[0][0]
        assert created_obj.type == "CASH_SECURED_PUT"
    finally:
        app.dependency_overrides.clear()

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
    """Minimal mock that chains .filter().all() / .filter().first() / .order_by()."""

    def __init__(self, results):
        self._results = results

    def filter(self, *args):
        return self

    def order_by(self, *args):
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


# --- GET /api/v1/positions ---


@pytest.mark.asyncio
async def test_list_positions_returns_user_positions(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions returns only the authenticated user's positions."""
    account_id = uuid4()
    positions = [
        _make_position(user_id, account_id, ticker="AAPL"),
        _make_position(user_id, account_id, ticker="TSLA"),
    ]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/positions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        tickers = {p["ticker"] for p in data}
        assert tickers == {"AAPL", "TSLA"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_empty(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions returns empty list when no positions match."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/positions", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_with_status_filter(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions?status=OPEN filters by status."""
    account_id = uuid4()
    positions = [_make_position(user_id, account_id, status="OPEN")]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/positions?status=OPEN", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_with_ticker_filter(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions?ticker=aapl filters by ticker (case-insensitive)."""
    account_id = uuid4()
    positions = [_make_position(user_id, account_id, ticker="AAPL")]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/positions?ticker=aapl", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_with_type_filter(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions?type=COVERED_CALL filters by type."""
    account_id = uuid4()
    positions = [_make_position(user_id, account_id, type="COVERED_CALL")]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/positions?type=COVERED_CALL", headers=auth_headers
            )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_with_account_filter(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions?account_id=... filters by account."""
    account_id = uuid4()
    positions = [_make_position(user_id, account_id)]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"/api/v1/positions?account_id={account_id}", headers=auth_headers
            )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_with_expiration_range(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions?expiration_start=...&expiration_end=... filters by expiration range."""
    account_id = uuid4()
    positions = [
        _make_position(user_id, account_id, expiration_date=date(2026, 3, 15))
    ]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/positions?expiration_start=2026-03-01&expiration_end=2026-03-31",
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_with_sort_and_order(user_id: UUID, auth_headers: dict):
    """GET /api/v1/positions?sort=ticker&order=asc applies sorting."""
    account_id = uuid4()
    positions = [
        _make_position(user_id, account_id, ticker="AAPL"),
        _make_position(user_id, account_id, ticker="TSLA"),
    ]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/positions?sort=ticker&order=asc", headers=auth_headers
            )
        assert resp.status_code == 200
        assert len(resp.json()) == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_default_sort_open_date_desc(
    user_id: UUID, auth_headers: dict
):
    """GET /api/v1/positions default sort is open_date descending."""
    account_id = uuid4()
    positions = [_make_position(user_id, account_id)]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/positions", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_includes_computed_fields(
    user_id: UUID, auth_headers: dict
):
    """Each position in the response includes computed fields."""
    account_id = uuid4()
    positions = [_make_position(user_id, account_id)]

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery(positions)

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/positions", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        pos = data[0]
        assert "premium_total" in pos
        assert "premium_net" in pos
        assert "collateral" in pos
        assert "roc_period" in pos
        assert "dte" in pos
        assert "annualized_roc" in pos
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_positions_requires_auth():
    """GET /api/v1/positions without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/positions")
    assert resp.status_code == 401


# --- PATCH /api/v1/positions/{id} ---


@pytest.mark.asyncio
async def test_update_position_success(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} updates provided fields and returns updated position."""
    account_id = uuid4()
    position = _make_position(user_id, account_id)
    position_id = position.id

    mock_db = MagicMock()

    # First query(Position).filter(...).first() returns the position
    # We need to handle two possible query calls: Position lookup, and potentially Account lookup
    mock_db.query.return_value = _FakeQuery([position])

    def fake_refresh(obj):
        obj.strike_price = Decimal("155.00")
        obj.notes = "Updated note"
        obj.updated_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position_id}",
                json={"strike_price": "155.00", "notes": "Updated note"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(position_id)
        assert Decimal(str(data["strike_price"])) == Decimal("155.00")
        assert data["notes"] == "Updated note"
        # Computed fields present
        assert "premium_total" in data
        assert "collateral" in data
        assert "annualized_roc" in data
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_not_found(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} returns 404 if position doesn't exist."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])  # Position not found

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{uuid4()}",
                json={"notes": "test"},
                headers=auth_headers,
            )
        assert resp.status_code == 404
        assert "position" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_other_users_position(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} returns 404 if position belongs to another user."""
    mock_db = MagicMock()
    # Filter by user_id means other user's position won't be found
    mock_db.query.return_value = _FakeQuery([])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{uuid4()}",
                json={"notes": "hacker"},
                headers=auth_headers,
            )
        assert resp.status_code == 404
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_cannot_change_user_id(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} cannot change user_id (not in PositionUpdate schema)."""
    account_id = uuid4()
    position = _make_position(user_id, account_id)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([position])
    mock_db.refresh.side_effect = lambda obj: setattr(
        obj, "updated_at", datetime.now(timezone.utc)
    )

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"user_id": str(uuid4()), "notes": "test"},
                headers=auth_headers,
            )
        # user_id is not in PositionUpdate schema, so it's ignored (not an error)
        assert resp.status_code == 200
        # user_id should remain the original
        assert resp.json()["user_id"] == str(user_id)
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_ticker_uppercased(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} uppercases ticker if provided."""
    account_id = uuid4()
    position = _make_position(user_id, account_id)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([position])

    def fake_refresh(obj):
        obj.updated_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"ticker": "msft"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        # Verify setattr was called with uppercased ticker
        assert position.ticker == "MSFT"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_type_enum_stored_as_value(
    user_id: UUID, auth_headers: dict
):
    """PATCH /api/v1/positions/{id} stores type enum as string value."""
    account_id = uuid4()
    position = _make_position(user_id, account_id, type="COVERED_CALL")

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([position])

    def fake_refresh(obj):
        obj.updated_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"type": "CASH_SECURED_PUT"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        assert position.type == "CASH_SECURED_PUT"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_invalid_account_id(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} returns 400 if new account_id doesn't belong to user."""
    account_id = uuid4()
    position = _make_position(user_id, account_id)
    new_account_id = uuid4()

    mock_db = MagicMock()

    # First call: query(Position) → found
    # Second call: query(Account) → not found
    position_query = _FakeQuery([position])
    account_query = _FakeQuery([])
    mock_db.query.side_effect = [position_query, account_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"account_id": str(new_account_id)},
                headers=auth_headers,
            )
        assert resp.status_code == 400
        assert "account" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_updated_at_refreshed(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} refreshes updated_at timestamp."""
    account_id = uuid4()
    original_updated_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    position = _make_position(user_id, account_id, updated_at=original_updated_at)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([position])

    new_updated_at = datetime(2026, 2, 22, 12, 0, 0, tzinfo=timezone.utc)

    def fake_refresh(obj):
        obj.updated_at = new_updated_at

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"notes": "timestamp test"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        # After commit+refresh, updated_at should be refreshed
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_response_has_computed_fields(
    user_id: UUID, auth_headers: dict
):
    """PATCH response includes recalculated computed fields."""
    account_id = uuid4()
    position = _make_position(
        user_id,
        account_id,
        strike_price=Decimal("100.00"),
        contracts=2,
        multiplier=100,
        premium_per_share=Decimal("5.00"),
        open_fees=Decimal("1.00"),
        close_fees=Decimal("0"),
    )

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([position])

    def fake_refresh(obj):
        obj.strike_price = Decimal("110.00")
        obj.updated_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"strike_price": "110.00"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        # collateral = 110 * 2 * 100 = 22000
        assert Decimal(str(data["collateral"])) == Decimal("22000.00")
        # premium_total = 5 * 2 * 100 = 1000
        assert Decimal(str(data["premium_total"])) == Decimal("1000.00")
        assert "roc_period" in data
        assert "dte" in data
        assert "annualized_roc" in data
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_position_requires_auth():
    """PATCH /api/v1/positions/{id} without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.patch(
            f"/api/v1/positions/{uuid4()}",
            json={"notes": "no auth"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_position_exclude_unset(user_id: UUID, auth_headers: dict):
    """PATCH /api/v1/positions/{id} only updates fields that were sent."""
    account_id = uuid4()
    position = _make_position(
        user_id, account_id, notes="original", tags=["keep"]
    )

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([position])

    def fake_refresh(obj):
        obj.updated_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = fake_refresh

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Only send notes, not tags
            resp = await client.patch(
                f"/api/v1/positions/{position.id}",
                json={"notes": "changed"},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        # notes was updated
        assert position.notes == "changed"
        # tags was NOT overwritten (exclude_unset)
        assert position.tags == ["keep"]
    finally:
        app.dependency_overrides.clear()

"""Tests for dashboard summary endpoint."""

import os
import time
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
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
    """Minimal mock that chains .filter().all()."""

    def __init__(self, results):
        self._results = results

    def filter(self, *args):
        return self

    def all(self):
        return self._results


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def auth_headers(user_id: UUID) -> dict:
    token = _make_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


# --- GET /api/v1/dashboard/summary ---


@pytest.mark.asyncio
async def test_dashboard_summary_no_data(user_id: UUID, auth_headers: dict):
    """Returns zeroes when no positions exist."""
    mock_db = MagicMock()
    # Two queries: all positions (date-scoped) and open positions
    all_query = _FakeQuery([])
    open_query = _FakeQuery([])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(str(data["total_premium_collected"])) == Decimal("0")
        assert Decimal(str(data["premium_mtd"])) == Decimal("0")
        assert data["open_position_count"] == 0
        assert data["upcoming_expirations"] == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_with_positions(user_id: UUID, auth_headers: dict):
    """Returns correct totals with a mix of open and closed positions."""
    account_id = uuid4()
    today = date.today()

    # Open position opened this month: premium_total = 3.50 * 1 * 100 = 350
    open_pos = _make_position(
        user_id,
        account_id,
        status="OPEN",
        open_date=today.replace(day=1),
        expiration_date=today + timedelta(days=5),
        premium_per_share=Decimal("3.50"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0.65"),
        close_fees=Decimal("0"),
    )

    # Closed position opened last month: premium_net = 500 - 1.00 - 0.50 = 498.50
    closed_pos = _make_position(
        user_id,
        account_id,
        status="CLOSED",
        open_date=date(2026, 1, 10),
        expiration_date=date(2026, 1, 31),
        close_date=date(2026, 1, 31),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("1.00"),
        close_fees=Decimal("0.50"),
        outcome="EXPIRED",
    )

    all_positions = [open_pos, closed_pos]

    mock_db = MagicMock()
    all_query = _FakeQuery(all_positions)
    open_query = _FakeQuery([open_pos])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        # total = open premium_total (350) + closed premium_net (498.50) = 848.50
        assert Decimal(str(data["total_premium_collected"])) == Decimal("848.50")
        # premium_mtd = only open_pos (opened this month) → 350
        assert Decimal(str(data["premium_mtd"])) == Decimal("350")
        assert data["open_position_count"] == 1
        # open_pos expires within 7 days
        assert len(data["upcoming_expirations"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_premium_mtd_only_current_month(
    user_id: UUID, auth_headers: dict
):
    """premium_mtd only includes positions opened in the current month."""
    account_id = uuid4()

    # Opened last month — should NOT be in MTD
    old_pos = _make_position(
        user_id,
        account_id,
        status="CLOSED",
        open_date=date(2026, 1, 5),
        expiration_date=date(2026, 1, 20),
        close_date=date(2026, 1, 20),
        premium_per_share=Decimal("10.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    mock_db = MagicMock()
    all_query = _FakeQuery([old_pos])
    open_query = _FakeQuery([])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        # total premium = 1000 (closed, premium_net = 1000 - 0 - 0)
        assert Decimal(str(data["total_premium_collected"])) == Decimal("1000")
        # MTD should be 0 — position opened in January, not current month
        assert Decimal(str(data["premium_mtd"])) == Decimal("0")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_upcoming_expirations_within_7_days(
    user_id: UUID, auth_headers: dict
):
    """upcoming_expirations only includes open positions expiring within 7 days."""
    account_id = uuid4()
    today = date.today()

    # Expires in 3 days — should be included
    soon_pos = _make_position(
        user_id,
        account_id,
        status="OPEN",
        open_date=date(2026, 1, 15),
        expiration_date=today + timedelta(days=3),
    )

    # Expires in 30 days — should NOT be included
    far_pos = _make_position(
        user_id,
        account_id,
        status="OPEN",
        open_date=date(2026, 1, 15),
        expiration_date=today + timedelta(days=30),
    )

    mock_db = MagicMock()
    all_query = _FakeQuery([soon_pos, far_pos])
    open_query = _FakeQuery([soon_pos, far_pos])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["open_position_count"] == 2
        # Only the soon-expiring position
        assert len(data["upcoming_expirations"]) == 1
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_with_date_range(user_id: UUID, auth_headers: dict):
    """start/end query params scope total_premium_collected."""
    account_id = uuid4()

    # Position in range
    in_range = _make_position(
        user_id,
        account_id,
        status="CLOSED",
        open_date=date(2026, 1, 15),
        expiration_date=date(2026, 2, 15),
        close_date=date(2026, 2, 15),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    # The DB mock returns only in-range positions (the endpoint applies the filter via SQL)
    mock_db = MagicMock()
    all_query = _FakeQuery([in_range])
    open_query = _FakeQuery([])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary?start=2026-01-01&end=2026-01-31",
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        # premium_net = 500 - 0 - 0 = 500
        assert Decimal(str(data["total_premium_collected"])) == Decimal("500")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_closed_uses_premium_net(
    user_id: UUID, auth_headers: dict
):
    """Closed positions use premium_net (premium_total - open_fees - close_fees)."""
    account_id = uuid4()

    closed_pos = _make_position(
        user_id,
        account_id,
        status="CLOSED",
        open_date=date(2026, 1, 15),
        expiration_date=date(2026, 2, 15),
        close_date=date(2026, 2, 15),
        premium_per_share=Decimal("5.00"),
        contracts=2,
        multiplier=100,
        open_fees=Decimal("1.30"),
        close_fees=Decimal("0.70"),
        outcome="CLOSED_EARLY",
    )

    mock_db = MagicMock()
    all_query = _FakeQuery([closed_pos])
    open_query = _FakeQuery([])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        # premium_total = 5.00 * 2 * 100 = 1000
        # premium_net = 1000 - 1.30 - 0.70 = 998
        assert Decimal(str(data["total_premium_collected"])) == Decimal("998")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_open_uses_premium_total(
    user_id: UUID, auth_headers: dict
):
    """Open positions use premium_total (not premium_net)."""
    account_id = uuid4()
    today = date.today()

    open_pos = _make_position(
        user_id,
        account_id,
        status="OPEN",
        open_date=date(2026, 1, 15),
        expiration_date=today + timedelta(days=30),
        premium_per_share=Decimal("4.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("1.00"),
        close_fees=Decimal("0"),
    )

    mock_db = MagicMock()
    all_query = _FakeQuery([open_pos])
    open_query = _FakeQuery([open_pos])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        # premium_total = 4.00 * 1 * 100 = 400 (NOT 399 with fees)
        assert Decimal(str(data["total_premium_collected"])) == Decimal("400")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_dashboard_summary_requires_auth():
    """GET /api/v1/dashboard/summary without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/dashboard/summary")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_summary_upcoming_expirations_has_computed_fields(
    user_id: UUID, auth_headers: dict
):
    """Upcoming expirations include computed fields in the response."""
    account_id = uuid4()
    today = date.today()

    pos = _make_position(
        user_id,
        account_id,
        status="OPEN",
        open_date=date(2026, 1, 15),
        expiration_date=today + timedelta(days=2),
        premium_per_share=Decimal("3.50"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0.65"),
        close_fees=Decimal("0"),
    )

    mock_db = MagicMock()
    all_query = _FakeQuery([pos])
    open_query = _FakeQuery([pos])
    mock_db.query.side_effect = [all_query, open_query]

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/summary", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["upcoming_expirations"]) == 1
        exp_pos = data["upcoming_expirations"][0]
        assert "premium_total" in exp_pos
        assert "premium_net" in exp_pos
        assert "collateral" in exp_pos
        assert "dte" in exp_pos
        assert "annualized_roc" in exp_pos
    finally:
        app.dependency_overrides.clear()


# --- GET /api/v1/dashboard/by-ticker ---


@pytest.mark.asyncio
async def test_by_ticker_no_data(user_id: UUID, auth_headers: dict):
    """Returns empty list when no positions exist."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/by-ticker", headers=auth_headers
            )
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_by_ticker_groups_by_ticker(user_id: UUID, auth_headers: dict):
    """Returns per-ticker stats grouped correctly."""
    account_id = uuid4()

    aapl_pos = _make_position(
        user_id,
        account_id,
        ticker="AAPL",
        status="CLOSED",
        open_date=date(2026, 1, 10),
        expiration_date=date(2026, 2, 10),
        close_date=date(2026, 2, 10),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    tsla_pos1 = _make_position(
        user_id,
        account_id,
        ticker="TSLA",
        status="CLOSED",
        open_date=date(2026, 1, 5),
        expiration_date=date(2026, 2, 5),
        close_date=date(2026, 2, 5),
        premium_per_share=Decimal("10.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    tsla_pos2 = _make_position(
        user_id,
        account_id,
        ticker="TSLA",
        status="OPEN",
        open_date=date(2026, 1, 15),
        expiration_date=date(2026, 3, 15),
        premium_per_share=Decimal("8.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("1.00"),
        close_fees=Decimal("0"),
    )

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([aapl_pos, tsla_pos1, tsla_pos2])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/by-ticker", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        # Find tickers in response
        tickers = {d["ticker"] for d in data}
        assert tickers == {"AAPL", "TSLA"}

        tsla = next(d for d in data if d["ticker"] == "TSLA")
        assert tsla["trade_count"] == 2
        # TSLA total: closed premium_net = 1000 + open premium_total = 800 = 1800
        assert Decimal(str(tsla["total_premium"])) == Decimal("1800")

        aapl = next(d for d in data if d["ticker"] == "AAPL")
        assert aapl["trade_count"] == 1
        # AAPL total: closed premium_net = 500
        assert Decimal(str(aapl["total_premium"])) == Decimal("500")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_by_ticker_sorted_by_total_premium_desc(
    user_id: UUID, auth_headers: dict
):
    """Results are sorted by total_premium descending."""
    account_id = uuid4()

    # Low premium ticker
    low_pos = _make_position(
        user_id,
        account_id,
        ticker="LOW",
        status="CLOSED",
        open_date=date(2026, 1, 10),
        expiration_date=date(2026, 2, 10),
        close_date=date(2026, 2, 10),
        premium_per_share=Decimal("1.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    # High premium ticker
    high_pos = _make_position(
        user_id,
        account_id,
        ticker="HIGH",
        status="CLOSED",
        open_date=date(2026, 1, 5),
        expiration_date=date(2026, 2, 5),
        close_date=date(2026, 2, 5),
        premium_per_share=Decimal("20.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    mock_db = MagicMock()
    # low_pos first in DB result to verify sorting
    mock_db.query.return_value = _FakeQuery([low_pos, high_pos])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/by-ticker", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # HIGH should be first (2000 > 100)
        assert data[0]["ticker"] == "HIGH"
        assert data[1]["ticker"] == "LOW"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_by_ticker_with_date_range(user_id: UUID, auth_headers: dict):
    """start/end query params scope the by-ticker results."""
    account_id = uuid4()

    # In range
    in_range = _make_position(
        user_id,
        account_id,
        ticker="AAPL",
        status="CLOSED",
        open_date=date(2026, 1, 15),
        expiration_date=date(2026, 2, 15),
        close_date=date(2026, 2, 15),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    # Mock returns only in-range (endpoint applies SQL filters)
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([in_range])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/by-ticker?start=2026-01-01&end=2026-01-31",
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["ticker"] == "AAPL"
        assert Decimal(str(data[0]["total_premium"])) == Decimal("500")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_by_ticker_avg_annualized_roc(user_id: UUID, auth_headers: dict):
    """avg_annualized_roc is the average of annualized_roc across positions for a ticker."""
    account_id = uuid4()

    # Two closed positions with known annualized_roc
    pos1 = _make_position(
        user_id,
        account_id,
        ticker="AAPL",
        status="CLOSED",
        open_date=date(2026, 1, 1),
        expiration_date=date(2026, 2, 1),
        close_date=date(2026, 2, 1),
        strike_price=Decimal("100.00"),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    pos2 = _make_position(
        user_id,
        account_id,
        ticker="AAPL",
        status="CLOSED",
        open_date=date(2026, 1, 1),
        expiration_date=date(2026, 2, 1),
        close_date=date(2026, 2, 1),
        strike_price=Decimal("200.00"),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("0"),
        close_fees=Decimal("0"),
        outcome="EXPIRED",
    )

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos1, pos2])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/by-ticker", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        aapl = data[0]
        assert aapl["ticker"] == "AAPL"
        # Verify avg_annualized_roc is a number > 0
        assert Decimal(str(aapl["avg_annualized_roc"])) > 0
        assert aapl["trade_count"] == 2
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_by_ticker_premium_calculation(user_id: UUID, auth_headers: dict):
    """Closed positions use premium_net, open positions use premium_total."""
    account_id = uuid4()
    today = date.today()

    # Open position: premium_total = 4.00 * 1 * 100 = 400
    open_pos = _make_position(
        user_id,
        account_id,
        ticker="AAPL",
        status="OPEN",
        open_date=date(2026, 1, 15),
        expiration_date=today + timedelta(days=30),
        premium_per_share=Decimal("4.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("1.00"),
        close_fees=Decimal("0"),
    )

    # Closed position: premium_net = 500 - 1.00 - 0.50 = 498.50
    closed_pos = _make_position(
        user_id,
        account_id,
        ticker="AAPL",
        status="CLOSED",
        open_date=date(2026, 1, 10),
        expiration_date=date(2026, 2, 10),
        close_date=date(2026, 2, 10),
        premium_per_share=Decimal("5.00"),
        contracts=1,
        multiplier=100,
        open_fees=Decimal("1.00"),
        close_fees=Decimal("0.50"),
        outcome="EXPIRED",
    )

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([open_pos, closed_pos])

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/dashboard/by-ticker", headers=auth_headers
            )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        aapl = data[0]
        # total = open premium_total (400) + closed premium_net (498.50) = 898.50
        assert Decimal(str(aapl["total_premium"])) == Decimal("898.50")
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_by_ticker_requires_auth():
    """GET /api/v1/dashboard/by-ticker without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/dashboard/by-ticker")
    assert resp.status_code == 401

"""Tests for CSV export endpoint."""

import csv
import io
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


def _parse_csv(content: str) -> list[dict]:
    """Parse CSV text into a list of dicts."""
    reader = csv.DictReader(io.StringIO(content))
    return list(reader)


# --- GET /api/v1/export/positions.csv ---


@pytest.mark.anyio
async def test_export_csv_returns_csv_with_positions(user_id, auth_headers):
    """Exporting with positions returns CSV with data rows."""
    account_id = uuid4()
    pos = _make_position(user_id, account_id)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/export/positions.csv", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")
    assert "attachment" in resp.headers["content-disposition"]
    assert "positions_" in resp.headers["content-disposition"]
    assert ".csv" in resp.headers["content-disposition"]

    rows = _parse_csv(resp.text)
    assert len(rows) == 1
    assert rows[0]["ticker"] == "AAPL"
    assert rows[0]["type"] == "COVERED_CALL"
    assert rows[0]["status"] == "OPEN"


@pytest.mark.anyio
async def test_export_csv_empty_returns_headers_only(user_id, auth_headers):
    """Empty result set returns CSV with headers only."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/export/positions.csv", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    lines = resp.text.strip().split("\n")
    assert len(lines) == 1  # headers only
    assert "ticker" in lines[0]
    assert "premium_total" in lines[0]


@pytest.mark.anyio
async def test_export_csv_includes_computed_fields(user_id, auth_headers):
    """CSV includes computed fields like premium_total, premium_net, collateral, etc."""
    account_id = uuid4()
    pos = _make_position(user_id, account_id)

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/export/positions.csv", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    rows = _parse_csv(resp.text)
    row = rows[0]

    # premium_total = 3.50 * 1 * 100 = 350.00
    assert Decimal(row["premium_total"]) == Decimal("350.00")
    # premium_net = 350.00 - 0.65 - 0 = 349.35
    assert Decimal(row["premium_net"]) == Decimal("349.35")
    # collateral = 150.00 * 1 * 100 = 15000.00
    assert Decimal(row["collateral"]) == Decimal("15000.00")
    # roc_period = 349.35 / 15000.00
    assert Decimal(row["roc_period"]) == Decimal("349.35") / Decimal("15000.00")
    # dte and annualized_roc should be present
    assert row["dte"] != ""
    assert row["annualized_roc"] != ""


@pytest.mark.anyio
async def test_export_csv_filter_by_status(user_id, auth_headers):
    """Supports status query param filter."""
    account_id = uuid4()
    pos = _make_position(user_id, account_id, status="CLOSED", outcome="EXPIRED",
                         close_date=date(2026, 2, 15))

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                "/api/v1/export/positions.csv?status=CLOSED",
                headers=auth_headers,
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1


@pytest.mark.anyio
async def test_export_csv_filter_by_ticker(user_id, auth_headers):
    """Supports ticker query param filter (case-insensitive)."""
    account_id = uuid4()
    pos = _make_position(user_id, account_id, ticker="TSLA")

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                "/api/v1/export/positions.csv?ticker=tsla",
                headers=auth_headers,
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1
    assert rows[0]["ticker"] == "TSLA"


@pytest.mark.anyio
async def test_export_csv_filter_by_date_range(user_id, auth_headers):
    """Supports start and end date query params."""
    account_id = uuid4()
    pos = _make_position(user_id, account_id, open_date=date(2026, 1, 15))

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get(
                "/api/v1/export/positions.csv?start=2026-01-01&end=2026-01-31",
                headers=auth_headers,
            )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    rows = _parse_csv(resp.text)
    assert len(rows) == 1


@pytest.mark.anyio
async def test_export_csv_auth_required():
    """Endpoint requires authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        resp = await ac.get("/api/v1/export/positions.csv")

    assert resp.status_code == 401


@pytest.mark.anyio
async def test_export_csv_content_disposition_filename(user_id, auth_headers):
    """Content-Disposition header contains a descriptive filename with date."""
    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/export/positions.csv", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    today = date.today().isoformat()
    assert f"positions_{today}.csv" in resp.headers["content-disposition"]


@pytest.mark.anyio
async def test_export_csv_tags_serialized(user_id, auth_headers):
    """Tags list is serialized as semicolon-separated string in CSV."""
    account_id = uuid4()
    pos = _make_position(user_id, account_id, tags=["wheel", "weekly"])

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/export/positions.csv", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    rows = _parse_csv(resp.text)
    assert rows[0]["tags"] == "wheel;weekly"


@pytest.mark.anyio
async def test_export_csv_multiple_positions(user_id, auth_headers):
    """Multiple positions each get their own row."""
    account_id = uuid4()
    pos1 = _make_position(user_id, account_id, ticker="AAPL")
    pos2 = _make_position(user_id, account_id, ticker="TSLA")
    pos3 = _make_position(user_id, account_id, ticker="MSFT")

    mock_db = MagicMock()
    mock_db.query.return_value = _FakeQuery([pos1, pos2, pos3])

    try:
        app.dependency_overrides[get_db] = lambda: mock_db
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            resp = await ac.get("/api/v1/export/positions.csv", headers=auth_headers)
    finally:
        app.dependency_overrides.clear()

    rows = _parse_csv(resp.text)
    assert len(rows) == 3
    tickers = [r["ticker"] for r in rows]
    assert "AAPL" in tickers
    assert "TSLA" in tickers
    assert "MSFT" in tickers

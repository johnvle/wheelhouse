"""Tests for prices proxy endpoint."""

import os
import time
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import UUID, uuid4

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.routers import prices as prices_module
from app.schemas.price import TickerPrice

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


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def auth_headers(user_id: UUID) -> dict:
    token = _make_token(str(user_id))
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def clear_price_cache():
    """Clear the price cache before each test."""
    prices_module._price_cache.clear()
    yield
    prices_module._price_cache.clear()


def _mock_fetch(tickers):
    """Mock _fetch_prices that returns fake price data."""
    now = datetime.now(timezone.utc)
    results = {}
    for t in tickers:
        if t in ("AAPL", "TSLA", "MSFT"):
            prices_map = {
                "AAPL": (175.50, 1.25),
                "TSLA": (250.00, -2.10),
                "MSFT": (420.00, 0.50),
            }
            price, change = prices_map[t]
            results[t] = TickerPrice(
                ticker=t,
                current_price=price,
                change_percent=change,
                last_fetched=now,
            )
        else:
            # Invalid ticker — null values
            results[t] = TickerPrice(ticker=t)
    return results


# --- GET /api/v1/prices ---


@pytest.mark.asyncio
async def test_get_prices_returns_data(auth_headers: dict):
    """Returns price data for valid tickers."""
    with patch.object(prices_module, "_fetch_prices", side_effect=_mock_fetch):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/prices?tickers=AAPL,TSLA", headers=auth_headers
            )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["prices"]) == 2

    aapl = next(p for p in data["prices"] if p["ticker"] == "AAPL")
    assert aapl["current_price"] == 175.50
    assert aapl["change_percent"] == 1.25
    assert aapl["last_fetched"] is not None

    tsla = next(p for p in data["prices"] if p["ticker"] == "TSLA")
    assert tsla["current_price"] == 250.00
    assert tsla["change_percent"] == -2.10


@pytest.mark.asyncio
async def test_get_prices_invalid_ticker_returns_null(auth_headers: dict):
    """Invalid tickers return null values, not errors."""
    with patch.object(prices_module, "_fetch_prices", side_effect=_mock_fetch):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/prices?tickers=AAPL,INVALIDTICKER", headers=auth_headers
            )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["prices"]) == 2

    invalid = next(p for p in data["prices"] if p["ticker"] == "INVALIDTICKER")
    assert invalid["current_price"] is None
    assert invalid["change_percent"] is None
    assert invalid["last_fetched"] is None


@pytest.mark.asyncio
async def test_get_prices_cached_within_ttl(auth_headers: dict):
    """Second request within 60s uses cached data (no second fetch call)."""
    call_count = 0

    def counting_fetch(tickers):
        nonlocal call_count
        call_count += 1
        return _mock_fetch(tickers)

    with patch.object(prices_module, "_fetch_prices", side_effect=counting_fetch):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # First request — should call fetch
            resp1 = await client.get(
                "/api/v1/prices?tickers=AAPL", headers=auth_headers
            )
            assert resp1.status_code == 200
            assert call_count == 1

            # Second request — should use cache
            resp2 = await client.get(
                "/api/v1/prices?tickers=AAPL", headers=auth_headers
            )
            assert resp2.status_code == 200
            assert call_count == 1  # no additional fetch call

    # Both responses should have the same data
    assert resp1.json() == resp2.json()


@pytest.mark.asyncio
async def test_get_prices_cache_expired(auth_headers: dict):
    """Expired cache entries trigger a new fetch."""
    call_count = 0

    def counting_fetch(tickers):
        nonlocal call_count
        call_count += 1
        return _mock_fetch(tickers)

    with patch.object(prices_module, "_fetch_prices", side_effect=counting_fetch):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # First request
            resp1 = await client.get(
                "/api/v1/prices?tickers=AAPL", headers=auth_headers
            )
            assert resp1.status_code == 200
            assert call_count == 1

            # Expire the cache by backdating the timestamp
            for key in prices_module._price_cache:
                price, _ = prices_module._price_cache[key]
                prices_module._price_cache[key] = (price, time.time() - 120)

            # Second request — cache expired, should fetch again
            resp2 = await client.get(
                "/api/v1/prices?tickers=AAPL", headers=auth_headers
            )
            assert resp2.status_code == 200
            assert call_count == 2


@pytest.mark.asyncio
async def test_get_prices_requires_auth():
    """GET /api/v1/prices without auth returns 401."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get("/api/v1/prices?tickers=AAPL")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_prices_includes_timestamp(auth_headers: dict):
    """Response includes last_fetched timestamp for each ticker."""
    with patch.object(prices_module, "_fetch_prices", side_effect=_mock_fetch):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/prices?tickers=AAPL", headers=auth_headers
            )
    assert resp.status_code == 200
    data = resp.json()
    aapl = data["prices"][0]
    assert aapl["last_fetched"] is not None
    # Verify it's a valid ISO timestamp
    datetime.fromisoformat(aapl["last_fetched"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_get_prices_tickers_uppercased(auth_headers: dict):
    """Tickers are uppercased before fetching."""
    with patch.object(prices_module, "_fetch_prices", side_effect=_mock_fetch) as mock:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/prices?tickers=aapl", headers=auth_headers
            )
    assert resp.status_code == 200
    # The mock was called with uppercased tickers
    mock.assert_called_once_with(["AAPL"])


@pytest.mark.asyncio
async def test_get_prices_empty_tickers(auth_headers: dict):
    """Empty tickers param returns empty list."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        resp = await client.get(
            "/api/v1/prices?tickers=", headers=auth_headers
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["prices"] == []


@pytest.mark.asyncio
async def test_get_prices_multiple_tickers(auth_headers: dict):
    """Returns data for multiple tickers in a single request."""
    with patch.object(prices_module, "_fetch_prices", side_effect=_mock_fetch):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/v1/prices?tickers=AAPL,TSLA,MSFT", headers=auth_headers
            )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["prices"]) == 3
    tickers = {p["ticker"] for p in data["prices"]}
    assert tickers == {"AAPL", "TSLA", "MSFT"}

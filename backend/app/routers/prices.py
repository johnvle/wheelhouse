"""Price proxy endpoint using Yahoo Finance."""

import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user
from app.schemas.price import PriceResponse, TickerPrice

router = APIRouter(prefix="/api/v1/prices", tags=["prices"])

# Simple in-memory cache: {ticker: (TickerPrice, fetch_timestamp)}
_price_cache: dict[str, tuple[TickerPrice, float]] = {}
CACHE_TTL_SECONDS = 60


def _fetch_prices(tickers: list[str]) -> dict[str, TickerPrice]:
    """Fetch prices from Yahoo Finance for the given tickers.

    Returns a dict mapping ticker -> TickerPrice.
    Invalid tickers get null values.
    """
    import yfinance as yf

    results: dict[str, TickerPrice] = {}
    now = datetime.now(timezone.utc)

    try:
        data = yf.download(
            tickers=tickers,
            period="2d",
            interval="1d",
            progress=False,
            auto_adjust=True,
        )
    except Exception:
        # On any yfinance error, return null values for all tickers
        for t in tickers:
            results[t] = TickerPrice(ticker=t)
        return results

    for ticker in tickers:
        try:
            if len(tickers) == 1:
                close_series = data["Close"]
            else:
                close_series = data["Close"][ticker]

            # Drop NaN values to get actual data points
            close_values = close_series.dropna()

            if len(close_values) == 0:
                results[ticker] = TickerPrice(ticker=ticker)
                continue

            current_price = float(close_values.iloc[-1])

            change_percent = None
            if len(close_values) >= 2:
                prev_price = float(close_values.iloc[-2])
                if prev_price != 0:
                    change_percent = ((current_price - prev_price) / prev_price) * 100

            results[ticker] = TickerPrice(
                ticker=ticker,
                current_price=round(current_price, 2),
                change_percent=round(change_percent, 2) if change_percent is not None else None,
                last_fetched=now,
            )
        except Exception:
            results[ticker] = TickerPrice(ticker=ticker)

    return results


@router.get("", response_model=PriceResponse)
def get_prices(
    user_id: UUID = Depends(get_current_user),
    tickers: str = Query(..., description="Comma-separated ticker symbols"),
):
    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]

    if not ticker_list:
        return PriceResponse(prices=[])

    now = time.time()
    results: list[TickerPrice] = []
    tickers_to_fetch: list[str] = []

    # Check cache for each ticker
    for ticker in ticker_list:
        cached = _price_cache.get(ticker)
        if cached is not None:
            cached_price, cached_time = cached
            if now - cached_time < CACHE_TTL_SECONDS:
                results.append(cached_price)
                continue
        tickers_to_fetch.append(ticker)

    # Fetch uncached tickers
    if tickers_to_fetch:
        fetched = _fetch_prices(tickers_to_fetch)
        for ticker in tickers_to_fetch:
            price = fetched.get(ticker, TickerPrice(ticker=ticker))
            _price_cache[ticker] = (price, now)
            results.append(price)

    return PriceResponse(prices=results)

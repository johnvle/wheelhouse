"""Dashboard summary endpoints."""

from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.position import Position
from app.schemas.dashboard import DashboardSummaryResponse, TickerSummary

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


def _compute_premium(position: Position) -> Decimal:
    """Compute premium for a position.

    Closed positions use premium_net (premium_total - open_fees - close_fees).
    Open positions use premium_total.
    """
    premium_total = position.premium_per_share * position.contracts * position.multiplier
    if position.status == "CLOSED":
        return premium_total - position.open_fees - position.close_fees
    return premium_total


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
):
    # All user's positions (for total_premium_collected, scoped by date range)
    query = db.query(Position).filter(Position.user_id == user_id)
    if start is not None:
        query = query.filter(Position.open_date >= start)
    if end is not None:
        query = query.filter(Position.open_date <= end)
    positions = query.all()

    total_premium_collected = sum(
        (_compute_premium(p) for p in positions),
        Decimal("0"),
    )

    # Premium MTD: always query from 1st of current month, independent of date range
    today = date.today()
    mtd_start = today.replace(day=1)
    mtd_positions = (
        db.query(Position)
        .filter(
            Position.user_id == user_id,
            Position.open_date >= mtd_start,
        )
        .all()
    )
    premium_mtd = sum(
        (_compute_premium(p) for p in mtd_positions),
        Decimal("0"),
    )

    # Open position count (not scoped by date range)
    open_query = db.query(Position).filter(
        Position.user_id == user_id,
        Position.status == "OPEN",
    )
    open_positions = open_query.all()
    open_position_count = len(open_positions)

    # Upcoming expirations: open positions expiring within 7 days
    expiration_cutoff = today + timedelta(days=7)
    upcoming_expirations = [
        p for p in open_positions
        if p.expiration_date <= expiration_cutoff
    ]

    return DashboardSummaryResponse(
        total_premium_collected=total_premium_collected,
        premium_mtd=premium_mtd,
        open_position_count=open_position_count,
        upcoming_expirations=upcoming_expirations,
    )


@router.get("/by-ticker", response_model=list[TickerSummary])
def dashboard_by_ticker(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
):
    query = db.query(Position).filter(Position.user_id == user_id)
    if start is not None:
        query = query.filter(Position.open_date >= start)
    if end is not None:
        query = query.filter(Position.open_date <= end)
    positions = query.all()

    # Group by ticker
    by_ticker: dict[str, list[Position]] = defaultdict(list)
    for p in positions:
        by_ticker[p.ticker].append(p)

    results: list[TickerSummary] = []
    for ticker, ticker_positions in by_ticker.items():
        total_premium = sum(
            (_compute_premium(p) for p in ticker_positions),
            Decimal("0"),
        )
        trade_count = len(ticker_positions)

        # Compute avg annualized ROC directly (mirrors PositionResponse logic)
        roc_sum = Decimal("0")
        for p in ticker_positions:
            collateral = p.strike_price * p.contracts * p.multiplier
            if collateral == 0:
                continue
            premium_total = p.premium_per_share * p.contracts * p.multiplier
            premium_net = premium_total - p.open_fees - p.close_fees
            roc_period = premium_net / collateral
            days_in_trade = (
                (p.close_date - p.open_date).days
                if p.close_date is not None
                else (p.expiration_date - p.open_date).days
            )
            if days_in_trade <= 0:
                continue
            roc_sum += roc_period * Decimal(365) / Decimal(days_in_trade)
        avg_annualized_roc = roc_sum / trade_count if trade_count else Decimal("0")

        results.append(
            TickerSummary(
                ticker=ticker,
                total_premium=total_premium,
                trade_count=trade_count,
                avg_annualized_roc=avg_annualized_roc,
            )
        )

    # Sort by total_premium descending
    results.sort(key=lambda x: x.total_premium, reverse=True)

    return results

"""Dashboard summary endpoints."""

from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.position import Position
from app.schemas.dashboard import DashboardSummaryResponse

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

    # Premium MTD: positions opened in current month
    today = date.today()
    mtd_start = today.replace(day=1)
    mtd_positions = [p for p in positions if p.open_date >= mtd_start]
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

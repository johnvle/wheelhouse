"""Dashboard response schemas."""

from decimal import Decimal

from pydantic import BaseModel

from app.schemas.position import PositionResponse


class DashboardSummaryResponse(BaseModel):
    total_premium_collected: Decimal
    premium_mtd: Decimal
    open_position_count: int
    upcoming_expirations: list[PositionResponse]


class TickerSummary(BaseModel):
    ticker: str
    total_premium: Decimal
    trade_count: int
    avg_annualized_roc: Decimal

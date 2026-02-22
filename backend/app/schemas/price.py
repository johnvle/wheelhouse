"""Price response schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TickerPrice(BaseModel):
    ticker: str
    current_price: Optional[float] = None
    change_percent: Optional[float] = None
    last_fetched: Optional[datetime] = None


class PriceResponse(BaseModel):
    prices: list[TickerPrice]

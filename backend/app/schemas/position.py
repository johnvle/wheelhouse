import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, computed_field

from app.schemas.enums import PositionOutcome, PositionStatus, PositionType


class PositionCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    account_id: uuid.UUID
    ticker: str
    type: PositionType
    open_date: date
    expiration_date: date
    strike_price: Decimal
    contracts: int
    premium_per_share: Decimal
    multiplier: int = 100
    open_fees: Decimal = Decimal("0")
    notes: Optional[str] = None
    tags: Optional[list[str]] = None


class PositionUpdate(BaseModel):
    model_config = ConfigDict(strict=False)

    account_id: Optional[uuid.UUID] = None
    ticker: Optional[str] = None
    type: Optional[PositionType] = None
    open_date: Optional[date] = None
    expiration_date: Optional[date] = None
    strike_price: Optional[Decimal] = None
    contracts: Optional[int] = None
    premium_per_share: Optional[Decimal] = None
    multiplier: Optional[int] = None
    open_fees: Optional[Decimal] = None
    close_fees: Optional[Decimal] = None
    close_price_per_share: Optional[Decimal] = None
    notes: Optional[str] = None
    tags: Optional[list[str]] = None


class PositionClose(BaseModel):
    model_config = ConfigDict(strict=False)

    outcome: Literal["EXPIRED", "ASSIGNED", "CLOSED_EARLY"]
    close_date: date
    close_price_per_share: Optional[Decimal] = None
    close_fees: Optional[Decimal] = None


class PositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    account_id: uuid.UUID
    ticker: str
    type: str
    status: str
    open_date: date
    expiration_date: date
    close_date: Optional[date]
    strike_price: Decimal
    contracts: int
    multiplier: int
    premium_per_share: Decimal
    open_fees: Decimal
    close_fees: Decimal
    close_price_per_share: Optional[Decimal]
    outcome: Optional[str]
    roll_group_id: Optional[uuid.UUID]
    notes: Optional[str]
    tags: Optional[list[str]]
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def premium_total(self) -> Decimal:
        return self.premium_per_share * self.contracts * self.multiplier

    @computed_field  # type: ignore[prop-decorator]
    @property
    def premium_net(self) -> Decimal:
        return self.premium_total - self.open_fees - self.close_fees

    @computed_field  # type: ignore[prop-decorator]
    @property
    def collateral(self) -> Decimal:
        return self.strike_price * self.contracts * self.multiplier

    @computed_field  # type: ignore[prop-decorator]
    @property
    def roc_period(self) -> Decimal:
        if self.collateral == 0:
            return Decimal("0")
        return self.premium_net / self.collateral

    @computed_field  # type: ignore[prop-decorator]
    @property
    def dte(self) -> int:
        return (self.expiration_date - date.today()).days

    @computed_field  # type: ignore[prop-decorator]
    @property
    def annualized_roc(self) -> Decimal:
        if self.collateral == 0:
            return Decimal("0")
        if self.close_date is not None:
            days_in_trade = (self.close_date - self.open_date).days
        else:
            days_in_trade = (self.expiration_date - self.open_date).days
        if days_in_trade <= 0:
            return Decimal("0")
        return self.roc_period * Decimal(365) / Decimal(days_in_trade)

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    ARRAY,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.account import Account


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id"), nullable=False
    )
    ticker: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column("type", Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'OPEN'")
    )
    open_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiration_date: Mapped[date] = mapped_column(Date, nullable=False)
    close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    strike_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    contracts: Mapped[int] = mapped_column(Integer, nullable=False)
    multiplier: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("100")
    )
    premium_per_share: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    open_fees: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False, server_default=text("0")
    )
    close_fees: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False, server_default=text("0")
    )
    close_price_per_share: Mapped[Optional[Decimal]] = mapped_column(
        Numeric, nullable=True
    )
    outcome: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    roll_group_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    account: Mapped["Account"] = relationship(back_populates="positions")

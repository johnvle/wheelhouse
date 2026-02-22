"""CRUD endpoints for option positions."""

from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.account import Account
from app.models.position import Position
from app.schemas.enums import PositionStatus, PositionType
from app.schemas.position import (
    PositionClose,
    PositionCreate,
    PositionResponse,
    PositionRoll,
    PositionRollResponse,
    PositionUpdate,
)

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

SORTABLE_COLUMNS = {
    "open_date",
    "expiration_date",
    "ticker",
    "strike_price",
    "contracts",
    "premium_per_share",
    "status",
    "type",
    "created_at",
    "updated_at",
}


@router.get("", response_model=list[PositionResponse])
def list_positions(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    status: Optional[PositionStatus] = Query(None),
    ticker: Optional[str] = Query(None),
    type: Optional[PositionType] = Query(None),
    account_id: Optional[UUID] = Query(None),
    expiration_start: Optional[date] = Query(None),
    expiration_end: Optional[date] = Query(None),
    sort: str = Query("open_date"),
    order: str = Query("desc"),
):
    query = db.query(Position).filter(Position.user_id == user_id)

    if status is not None:
        query = query.filter(Position.status == status.value)
    if ticker is not None:
        query = query.filter(Position.ticker == ticker.upper())
    if type is not None:
        query = query.filter(Position.type == type.value)
    if account_id is not None:
        query = query.filter(Position.account_id == account_id)
    if expiration_start is not None:
        query = query.filter(Position.expiration_date >= expiration_start)
    if expiration_end is not None:
        query = query.filter(Position.expiration_date <= expiration_end)

    # Sorting
    sort_col_name = sort if sort in SORTABLE_COLUMNS else "open_date"
    sort_col = getattr(Position, sort_col_name)
    if order.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    return query.all()


@router.post("", response_model=PositionResponse, status_code=201)
def create_position(
    body: PositionCreate,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify account belongs to authenticated user
    account = (
        db.query(Account)
        .filter(Account.id == body.account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=400,
            detail="Account not found or does not belong to you",
        )

    position = Position(
        user_id=user_id,
        account_id=body.account_id,
        ticker=body.ticker.upper(),
        type=body.type.value,
        status="OPEN",
        open_date=body.open_date,
        expiration_date=body.expiration_date,
        strike_price=body.strike_price,
        contracts=body.contracts,
        multiplier=body.multiplier,
        premium_per_share=body.premium_per_share,
        open_fees=body.open_fees,
        notes=body.notes,
        tags=body.tags,
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


@router.patch("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: UUID,
    body: PositionUpdate,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user_id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    update_data = body.model_dump(exclude_unset=True)

    # Validate new account_id belongs to the user
    if "account_id" in update_data and update_data["account_id"] is not None:
        account = (
            db.query(Account)
            .filter(
                Account.id == update_data["account_id"],
                Account.user_id == user_id,
            )
            .first()
        )
        if not account:
            raise HTTPException(
                status_code=400,
                detail="Account not found or does not belong to you",
            )

    for field, value in update_data.items():
        if field == "ticker" and value is not None:
            value = value.upper()
        if field == "type" and value is not None:
            value = value.value
        setattr(position, field, value)

    db.commit()
    db.refresh(position)
    return position


@router.post("/{position_id}/close", response_model=PositionResponse)
def close_position(
    position_id: UUID,
    body: PositionClose,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user_id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    if position.status == "CLOSED":
        raise HTTPException(status_code=400, detail="Position is already closed")

    position.status = "CLOSED"
    position.outcome = body.outcome
    position.close_date = body.close_date
    if body.close_price_per_share is not None:
        position.close_price_per_share = body.close_price_per_share
    if body.close_fees is not None:
        position.close_fees = body.close_fees

    db.commit()
    db.refresh(position)
    return position


@router.post("/{position_id}/roll", response_model=PositionRollResponse)
def roll_position(
    position_id: UUID,
    body: PositionRoll,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Look up the existing position
    position = (
        db.query(Position)
        .filter(Position.id == position_id, Position.user_id == user_id)
        .first()
    )
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")

    if position.status == "CLOSED":
        raise HTTPException(status_code=400, detail="Position is already closed")

    # Validate new position's account_id belongs to user
    account = (
        db.query(Account)
        .filter(Account.id == body.open.account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise HTTPException(
            status_code=400,
            detail="Account not found or does not belong to you",
        )

    # Generate shared roll_group_id
    roll_group_id = uuid4()

    # Close the old position
    position.status = "CLOSED"
    position.outcome = "ROLLED"
    position.roll_group_id = roll_group_id
    position.close_date = body.close.close_date
    if body.close.close_price_per_share is not None:
        position.close_price_per_share = body.close.close_price_per_share
    if body.close.close_fees is not None:
        position.close_fees = body.close.close_fees

    # Create the new position
    new_position = Position(
        user_id=user_id,
        account_id=body.open.account_id,
        ticker=body.open.ticker.upper(),
        type=body.open.type.value,
        status="OPEN",
        open_date=body.open.open_date,
        expiration_date=body.open.expiration_date,
        strike_price=body.open.strike_price,
        contracts=body.open.contracts,
        multiplier=body.open.multiplier,
        premium_per_share=body.open.premium_per_share,
        open_fees=body.open.open_fees,
        notes=body.open.notes,
        tags=body.open.tags,
        roll_group_id=roll_group_id,
    )
    db.add(new_position)

    # Single transaction commit
    db.commit()
    db.refresh(position)
    db.refresh(new_position)

    return {"closed": position, "opened": new_position}

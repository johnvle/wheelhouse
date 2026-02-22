"""CRUD endpoints for option positions."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.account import Account
from app.models.position import Position
from app.schemas.position import PositionCreate, PositionResponse

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])


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

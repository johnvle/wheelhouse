"""CRUD endpoints for brokerage accounts."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.account import Account
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
def list_accounts(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    accounts = db.query(Account).filter(Account.user_id == user_id).all()
    return accounts


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(
    body: AccountCreate,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = Account(
        user_id=user_id,
        name=body.name,
        broker=body.broker.value,
        tax_treatment=body.tax_treatment,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: UUID,
    body: AccountUpdate,
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    account = (
        db.query(Account)
        .filter(Account.id == account_id, Account.user_id == user_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "broker" and value is not None:
            value = value.value
        setattr(account, field, value)

    db.commit()
    db.refresh(account)
    return account

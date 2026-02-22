import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.enums import Broker


class AccountCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str
    broker: Broker
    tax_treatment: Optional[str] = None


class AccountUpdate(BaseModel):
    model_config = ConfigDict(strict=False)

    name: Optional[str] = None
    broker: Optional[Broker] = None
    tax_treatment: Optional[str] = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    broker: str
    tax_treatment: Optional[str]
    created_at: datetime
    updated_at: datetime

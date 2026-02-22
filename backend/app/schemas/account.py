import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import Broker


class AccountCreate(BaseModel):
    model_config = ConfigDict(strict=False)

    name: str = Field(min_length=1, max_length=255)
    broker: Broker
    tax_treatment: Optional[str] = None


class AccountUpdate(BaseModel):
    model_config = ConfigDict(strict=False)

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
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

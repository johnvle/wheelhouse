"""CSV export endpoint for positions."""

import csv
import io
from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models.position import Position
from app.schemas.enums import PositionStatus
from app.schemas.position import PositionResponse

router = APIRouter(prefix="/api/v1/export", tags=["export"])

CSV_COLUMNS = [
    "id",
    "user_id",
    "account_id",
    "ticker",
    "type",
    "status",
    "open_date",
    "expiration_date",
    "close_date",
    "strike_price",
    "contracts",
    "multiplier",
    "premium_per_share",
    "open_fees",
    "close_fees",
    "close_price_per_share",
    "outcome",
    "roll_group_id",
    "notes",
    "tags",
    "created_at",
    "updated_at",
    "premium_total",
    "premium_net",
    "collateral",
    "roc_period",
    "dte",
    "annualized_roc",
]


@router.get("/positions.csv")
def export_positions_csv(
    user_id: UUID = Depends(get_current_user),
    db: Session = Depends(get_db),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None),
    status: Optional[PositionStatus] = Query(None),
    ticker: Optional[str] = Query(None),
):
    query = db.query(Position).filter(Position.user_id == user_id)

    if start is not None:
        query = query.filter(Position.open_date >= start)
    if end is not None:
        query = query.filter(Position.open_date <= end)
    if status is not None:
        query = query.filter(Position.status == status.value)
    if ticker is not None:
        query = query.filter(Position.ticker == ticker.upper())

    positions = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_COLUMNS)

    for pos in positions:
        resp = PositionResponse.model_validate(pos)
        row = []
        for col in CSV_COLUMNS:
            value = getattr(resp, col)
            if isinstance(value, list):
                value = ";".join(value) if value else ""
            elif value is None:
                value = ""
            row.append(str(value))
        writer.writerow(row)

    output.seek(0)
    today = date.today().isoformat()
    filename = f"positions_{today}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

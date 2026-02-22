"""create positions table

Revision ID: 0003
Revises: 0002
Create Date: 2026-02-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.Uuid(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("ticker", sa.Text(), nullable=False),
        sa.Column("type", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default=sa.text("'OPEN'")),
        sa.Column("open_date", sa.Date(), nullable=False),
        sa.Column("expiration_date", sa.Date(), nullable=False),
        sa.Column("close_date", sa.Date(), nullable=True),
        sa.Column("strike_price", sa.Numeric(), nullable=False),
        sa.Column("contracts", sa.Integer(), nullable=False),
        sa.Column("multiplier", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("premium_per_share", sa.Numeric(), nullable=False),
        sa.Column("open_fees", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("close_fees", sa.Numeric(), nullable=False, server_default=sa.text("0")),
        sa.Column("close_price_per_share", sa.Numeric(), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=True),
        sa.Column("roll_group_id", sa.Uuid(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.ARRAY(sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["auth.users.id"], name="fk_positions_user_id"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], name="fk_positions_account_id"),
        sa.CheckConstraint("type IN ('COVERED_CALL', 'CASH_SECURED_PUT')", name="ck_positions_type"),
        sa.CheckConstraint("status IN ('OPEN', 'CLOSED')", name="ck_positions_status"),
        sa.CheckConstraint(
            "outcome IN ('EXPIRED', 'ASSIGNED', 'CLOSED_EARLY', 'ROLLED')",
            name="ck_positions_outcome",
        ),
    )

    op.create_index("ix_positions_user_id_status", "positions", ["user_id", "status"])
    op.create_index("ix_positions_user_id_ticker", "positions", ["user_id", "ticker"])
    op.create_index("ix_positions_user_id_expiration_date", "positions", ["user_id", "expiration_date"])


def downgrade() -> None:
    op.drop_index("ix_positions_user_id_expiration_date", table_name="positions")
    op.drop_index("ix_positions_user_id_ticker", table_name="positions")
    op.drop_index("ix_positions_user_id_status", table_name="positions")
    op.drop_table("positions")

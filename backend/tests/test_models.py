"""Tests for SQLAlchemy ORM models — verify structure without requiring a live DB."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Mapped, RelationshipProperty

from app.models.account import Account
from app.models.position import Position


# ---------- US-004: Account model ----------


class TestAccountModel:
    def test_tablename(self):
        assert Account.__tablename__ == "accounts"

    def test_has_all_columns(self):
        mapper = sa_inspect(Account)
        col_names = {c.key for c in mapper.column_attrs}
        expected = {
            "id", "user_id", "name", "broker", "tax_treatment",
            "created_at", "updated_at",
        }
        assert expected == col_names

    def test_column_types(self):
        mapper = sa_inspect(Account)
        columns = {c.key: c.columns[0] for c in mapper.column_attrs}

        assert isinstance(columns["id"].type, sa.Uuid)
        assert isinstance(columns["user_id"].type, sa.Uuid)
        assert isinstance(columns["name"].type, sa.Text)
        assert isinstance(columns["broker"].type, sa.Text)
        assert isinstance(columns["tax_treatment"].type, sa.Text)
        assert isinstance(columns["created_at"].type, sa.DateTime)
        assert columns["created_at"].type.timezone is True
        assert isinstance(columns["updated_at"].type, sa.DateTime)
        assert columns["updated_at"].type.timezone is True

    def test_primary_key(self):
        mapper = sa_inspect(Account)
        pk_cols = [c.name for c in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_nullability(self):
        mapper = sa_inspect(Account)
        columns = {c.key: c.columns[0] for c in mapper.column_attrs}

        assert columns["user_id"].nullable is False
        assert columns["name"].nullable is False
        assert columns["broker"].nullable is False
        assert columns["tax_treatment"].nullable is True

    def test_positions_relationship_exists(self):
        mapper = sa_inspect(Account)
        assert "positions" in mapper.relationships
        rel = mapper.relationships["positions"]
        assert rel.mapper.class_ is Position
        assert rel.back_populates == "account"

    def test_uses_mapped_column_style(self):
        """Verify models use SQLAlchemy 2.0 Mapped[] annotations."""
        annotations = Account.__annotations__
        # Check a few representative columns use Mapped type hints
        assert "id" in annotations
        assert "name" in annotations
        assert "positions" in annotations


# ---------- US-004: Position model ----------


class TestPositionModel:
    def test_tablename(self):
        assert Position.__tablename__ == "positions"

    def test_has_all_columns(self):
        mapper = sa_inspect(Position)
        col_names = {c.key for c in mapper.column_attrs}
        expected = {
            "id", "user_id", "account_id", "ticker", "type", "status",
            "open_date", "expiration_date", "close_date",
            "strike_price", "contracts", "multiplier",
            "premium_per_share", "open_fees", "close_fees",
            "close_price_per_share", "outcome", "roll_group_id",
            "notes", "tags", "created_at", "updated_at",
        }
        assert expected == col_names

    def test_column_types(self):
        mapper = sa_inspect(Position)
        columns = {c.key: c.columns[0] for c in mapper.column_attrs}

        assert isinstance(columns["id"].type, sa.Uuid)
        assert isinstance(columns["user_id"].type, sa.Uuid)
        assert isinstance(columns["account_id"].type, sa.Uuid)
        assert isinstance(columns["ticker"].type, sa.Text)
        assert isinstance(columns["type"].type, sa.Text)
        assert isinstance(columns["status"].type, sa.Text)
        assert isinstance(columns["open_date"].type, sa.Date)
        assert isinstance(columns["expiration_date"].type, sa.Date)
        assert isinstance(columns["close_date"].type, sa.Date)
        assert isinstance(columns["strike_price"].type, sa.Numeric)
        assert isinstance(columns["contracts"].type, sa.Integer)
        assert isinstance(columns["multiplier"].type, sa.Integer)
        assert isinstance(columns["premium_per_share"].type, sa.Numeric)
        assert isinstance(columns["open_fees"].type, sa.Numeric)
        assert isinstance(columns["close_fees"].type, sa.Numeric)
        assert isinstance(columns["close_price_per_share"].type, sa.Numeric)
        assert isinstance(columns["outcome"].type, sa.Text)
        assert isinstance(columns["roll_group_id"].type, sa.Uuid)
        assert isinstance(columns["notes"].type, sa.Text)
        assert isinstance(columns["tags"].type, sa.ARRAY)
        assert isinstance(columns["created_at"].type, sa.DateTime)
        assert columns["created_at"].type.timezone is True
        assert isinstance(columns["updated_at"].type, sa.DateTime)
        assert columns["updated_at"].type.timezone is True

    def test_tags_is_text_array(self):
        mapper = sa_inspect(Position)
        columns = {c.key: c.columns[0] for c in mapper.column_attrs}
        tags_type = columns["tags"].type
        assert isinstance(tags_type, sa.ARRAY)
        assert isinstance(tags_type.item_type, sa.Text)

    def test_primary_key(self):
        mapper = sa_inspect(Position)
        pk_cols = [c.name for c in mapper.primary_key]
        assert pk_cols == ["id"]

    def test_nullability(self):
        mapper = sa_inspect(Position)
        columns = {c.key: c.columns[0] for c in mapper.column_attrs}

        # Required fields
        assert columns["user_id"].nullable is False
        assert columns["account_id"].nullable is False
        assert columns["ticker"].nullable is False
        assert columns["type"].nullable is False
        assert columns["status"].nullable is False
        assert columns["open_date"].nullable is False
        assert columns["expiration_date"].nullable is False
        assert columns["strike_price"].nullable is False
        assert columns["contracts"].nullable is False
        assert columns["multiplier"].nullable is False
        assert columns["premium_per_share"].nullable is False
        assert columns["open_fees"].nullable is False
        assert columns["close_fees"].nullable is False

        # Nullable fields
        assert columns["close_date"].nullable is True
        assert columns["close_price_per_share"].nullable is True
        assert columns["outcome"].nullable is True
        assert columns["roll_group_id"].nullable is True
        assert columns["notes"].nullable is True
        assert columns["tags"].nullable is True

    def test_account_id_foreign_key(self):
        mapper = sa_inspect(Position)
        columns = {c.key: c.columns[0] for c in mapper.column_attrs}
        fk_targets = {fk.target_fullname for fk in columns["account_id"].foreign_keys}
        assert "accounts.id" in fk_targets

    def test_account_relationship_exists(self):
        mapper = sa_inspect(Position)
        assert "account" in mapper.relationships
        rel = mapper.relationships["account"]
        assert rel.mapper.class_ is Account
        assert rel.back_populates == "positions"

    def test_uses_mapped_column_style(self):
        """Verify models use SQLAlchemy 2.0 Mapped[] annotations."""
        annotations = Position.__annotations__
        assert "id" in annotations
        assert "ticker" in annotations
        assert "tags" in annotations
        assert "account" in annotations

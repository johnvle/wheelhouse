"""Tests for Alembic migrations — verify structure without requiring a live DB."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import sqlalchemy as sa

VERSIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def _load_migration(filename: str):
    """Import a migration module by its filename from alembic/versions/."""
    filepath = VERSIONS_DIR / filename
    mod_name = f"_migration_{filename.removesuffix('.py')}"
    spec = importlib.util.spec_from_file_location(mod_name, filepath)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod_name, mod


# ---------- US-002: accounts table ----------

_MOD_NAME_002, _MOD_002 = _load_migration("0002_create_accounts_table.py")


class TestAccountsMigration:
    mod = _MOD_002
    mod_name = _MOD_NAME_002

    def test_revision_metadata(self):
        assert self.mod.revision == "0002"
        assert self.mod.down_revision is None

    def _run_upgrade(self, mock_op: MagicMock):
        self.mod.upgrade()
        mock_op.create_table.assert_called_once()
        return mock_op.create_table.call_args

    @patch(f"{_MOD_NAME_002}.op")
    def test_upgrade_creates_accounts_table(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        assert args[0] == "accounts"

    @patch(f"{_MOD_NAME_002}.op")
    def test_upgrade_has_required_columns(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = [a for a in args[1:] if isinstance(a, sa.Column)]
        col_names = {c.name for c in columns}
        expected = {"id", "user_id", "name", "broker", "tax_treatment", "created_at", "updated_at"}
        assert expected == col_names

    @patch(f"{_MOD_NAME_002}.op")
    def test_upgrade_column_types(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = {c.name: c for c in args[1:] if isinstance(c, sa.Column)}

        assert isinstance(columns["id"].type, sa.Uuid)
        assert isinstance(columns["user_id"].type, sa.Uuid)
        assert isinstance(columns["name"].type, sa.Text)
        assert isinstance(columns["broker"].type, sa.Text)
        assert isinstance(columns["tax_treatment"].type, sa.Text)
        assert isinstance(columns["created_at"].type, sa.DateTime)
        assert columns["created_at"].type.timezone is True
        assert isinstance(columns["updated_at"].type, sa.DateTime)
        assert columns["updated_at"].type.timezone is True

    @patch(f"{_MOD_NAME_002}.op")
    def test_upgrade_nullability(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = {c.name: c for c in args[1:] if isinstance(c, sa.Column)}

        assert columns["user_id"].nullable is False
        assert columns["name"].nullable is False
        assert columns["broker"].nullable is False
        assert columns["tax_treatment"].nullable is True

    @patch(f"{_MOD_NAME_002}.op")
    def test_upgrade_id_is_primary_key(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = {c.name: c for c in args[1:] if isinstance(c, sa.Column)}
        assert columns["id"].primary_key is True

    @patch(f"{_MOD_NAME_002}.op")
    def test_upgrade_has_user_id_fk(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        fks = [a for a in args[1:] if isinstance(a, sa.ForeignKeyConstraint)]
        assert len(fks) == 1
        assert fks[0].column_keys == ["user_id"]
        assert list(fks[0].elements)[0].target_fullname == "auth.users.id"

    @patch(f"{_MOD_NAME_002}.op")
    def test_downgrade_drops_accounts_table(self, mock_op: MagicMock):
        self.mod.downgrade()
        mock_op.drop_table.assert_called_once_with("accounts")


# ---------- US-003: positions table ----------

_MOD_NAME_003, _MOD_003 = _load_migration("0003_create_positions_table.py")


class TestPositionsMigration:
    mod = _MOD_003
    mod_name = _MOD_NAME_003

    def test_revision_metadata(self):
        assert self.mod.revision == "0003"
        assert self.mod.down_revision == "0002"

    def _run_upgrade(self, mock_op: MagicMock):
        self.mod.upgrade()
        mock_op.create_table.assert_called_once()
        return mock_op.create_table.call_args

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_creates_positions_table(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        assert args[0] == "positions"

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_has_required_columns(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = [a for a in args[1:] if isinstance(a, sa.Column)]
        col_names = {c.name for c in columns}
        expected = {
            "id", "user_id", "account_id", "ticker", "type", "status",
            "open_date", "expiration_date", "close_date",
            "strike_price", "contracts", "multiplier",
            "premium_per_share", "open_fees", "close_fees",
            "close_price_per_share", "outcome", "roll_group_id",
            "notes", "tags", "created_at", "updated_at",
        }
        assert expected == col_names

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_column_types(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = {c.name: c for c in args[1:] if isinstance(c, sa.Column)}

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

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_nullability(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = {c.name: c for c in args[1:] if isinstance(c, sa.Column)}

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

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_id_is_primary_key(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        columns = {c.name: c for c in args[1:] if isinstance(c, sa.Column)}
        assert columns["id"].primary_key is True

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_has_foreign_keys(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        fks = [a for a in args[1:] if isinstance(a, sa.ForeignKeyConstraint)]
        assert len(fks) == 2

        fk_map = {fk.column_keys[0]: fk for fk in fks}
        assert "user_id" in fk_map
        assert "account_id" in fk_map
        assert list(fk_map["user_id"].elements)[0].target_fullname == "auth.users.id"
        assert list(fk_map["account_id"].elements)[0].target_fullname == "accounts.id"

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_has_check_constraints(self, mock_op: MagicMock):
        args, _kw = self._run_upgrade(mock_op)
        checks = [a for a in args[1:] if isinstance(a, sa.CheckConstraint)]
        check_names = {c.name for c in checks}
        assert "ck_positions_type" in check_names
        assert "ck_positions_status" in check_names
        assert "ck_positions_outcome" in check_names

    @patch(f"{_MOD_NAME_003}.op")
    def test_upgrade_creates_indexes(self, mock_op: MagicMock):
        self.mod.upgrade()
        index_calls = mock_op.create_index.call_args_list
        assert len(index_calls) == 3

        index_map = {call.args[0]: call.args for call in index_calls}
        assert index_map["ix_positions_user_id_status"] == (
            "ix_positions_user_id_status", "positions", ["user_id", "status"]
        )
        assert index_map["ix_positions_user_id_ticker"] == (
            "ix_positions_user_id_ticker", "positions", ["user_id", "ticker"]
        )
        assert index_map["ix_positions_user_id_expiration_date"] == (
            "ix_positions_user_id_expiration_date", "positions", ["user_id", "expiration_date"]
        )

    @patch(f"{_MOD_NAME_003}.op")
    def test_downgrade_drops_indexes_and_table(self, mock_op: MagicMock):
        self.mod.downgrade()
        # Indexes should be dropped before the table
        drop_index_calls = mock_op.drop_index.call_args_list
        assert len(drop_index_calls) == 3
        dropped_names = {call.args[0] for call in drop_index_calls}
        assert dropped_names == {
            "ix_positions_user_id_status",
            "ix_positions_user_id_ticker",
            "ix_positions_user_id_expiration_date",
        }
        mock_op.drop_table.assert_called_once_with("positions")

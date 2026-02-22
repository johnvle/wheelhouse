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

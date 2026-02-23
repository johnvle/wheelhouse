import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    Broker,
    PositionCreate,
    PositionOutcome,
    PositionResponse,
    PositionStatus,
    PositionType,
    PositionUpdate,
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TestEnums:
    def test_position_type_values(self):
        assert PositionType.COVERED_CALL == "COVERED_CALL"
        assert PositionType.CASH_SECURED_PUT == "CASH_SECURED_PUT"
        assert len(PositionType) == 2

    def test_position_status_values(self):
        assert PositionStatus.OPEN == "OPEN"
        assert PositionStatus.CLOSED == "CLOSED"
        assert len(PositionStatus) == 2

    def test_position_outcome_values(self):
        assert PositionOutcome.EXPIRED == "EXPIRED"
        assert PositionOutcome.ASSIGNED == "ASSIGNED"
        assert PositionOutcome.CLOSED_EARLY == "CLOSED_EARLY"
        assert PositionOutcome.ROLLED == "ROLLED"
        assert len(PositionOutcome) == 4

    def test_broker_values(self):
        assert Broker.ROBINHOOD == "robinhood"
        assert Broker.MERRILL == "merrill"
        assert Broker.OTHER == "other"
        assert len(Broker) == 3

    def test_enums_are_str(self):
        assert isinstance(PositionType.COVERED_CALL, str)
        assert isinstance(PositionStatus.OPEN, str)
        assert isinstance(PositionOutcome.EXPIRED, str)
        assert isinstance(Broker.ROBINHOOD, str)


# ---------------------------------------------------------------------------
# Account schemas
# ---------------------------------------------------------------------------

class TestAccountCreate:
    def test_valid_create(self):
        schema = AccountCreate(name="My Account", broker=Broker.ROBINHOOD)
        assert schema.name == "My Account"
        assert schema.broker == Broker.ROBINHOOD
        assert schema.tax_treatment is None

    def test_with_tax_treatment(self):
        schema = AccountCreate(
            name="IRA", broker=Broker.MERRILL, tax_treatment="roth_ira"
        )
        assert schema.tax_treatment == "roth_ira"

    def test_broker_from_string(self):
        schema = AccountCreate(name="Test", broker="robinhood")
        assert schema.broker == Broker.ROBINHOOD

    def test_invalid_broker(self):
        with pytest.raises(ValidationError) as exc_info:
            AccountCreate(name="Test", broker="invalid_broker")
        assert "broker" in str(exc_info.value)

    def test_missing_name(self):
        with pytest.raises(ValidationError):
            AccountCreate(broker=Broker.ROBINHOOD)

    def test_missing_broker(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="Test")


class TestAccountUpdate:
    def test_all_none_by_default(self):
        schema = AccountUpdate()
        assert schema.name is None
        assert schema.broker is None
        assert schema.tax_treatment is None

    def test_partial_update(self):
        schema = AccountUpdate(name="New Name")
        assert schema.name == "New Name"
        assert schema.broker is None

    def test_broker_update(self):
        schema = AccountUpdate(broker="merrill")
        assert schema.broker == Broker.MERRILL

    def test_invalid_broker_update(self):
        with pytest.raises(ValidationError):
            AccountUpdate(broker="invalid")


class TestAccountResponse:
    def _make_response(self, **overrides):
        defaults = dict(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Test Account",
            broker="robinhood",
            tax_treatment=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        defaults.update(overrides)
        return AccountResponse(**defaults)

    def test_valid_response(self):
        resp = self._make_response()
        assert resp.name == "Test Account"
        assert resp.broker == "robinhood"

    def test_from_attributes_config(self):
        assert AccountResponse.model_config.get("from_attributes") is True

    def test_all_fields_present(self):
        fields = set(AccountResponse.model_fields.keys())
        expected = {
            "id", "user_id", "name", "broker", "tax_treatment",
            "created_at", "updated_at",
        }
        assert fields == expected


# ---------------------------------------------------------------------------
# Position schemas
# ---------------------------------------------------------------------------

class TestPositionCreate:
    def _make_create(self, **overrides):
        defaults = dict(
            account_id=uuid.uuid4(),
            ticker="AAPL",
            type=PositionType.COVERED_CALL,
            open_date=date(2025, 1, 15),
            expiration_date=date(2025, 2, 21),
            strike_price=Decimal("150.00"),
            contracts=1,
            premium_per_share=Decimal("3.50"),
        )
        defaults.update(overrides)
        return PositionCreate(**defaults)

    def test_valid_create(self):
        schema = self._make_create()
        assert schema.ticker == "AAPL"
        assert schema.type == PositionType.COVERED_CALL
        assert schema.multiplier == 100
        assert schema.open_fees == Decimal("0")
        assert schema.notes is None
        assert schema.tags is None

    def test_with_optional_fields(self):
        schema = self._make_create(
            multiplier=50,
            open_fees=Decimal("1.50"),
            notes="test note",
            tags=["earnings", "weekly"],
        )
        assert schema.multiplier == 50
        assert schema.open_fees == Decimal("1.50")
        assert schema.notes == "test note"
        assert schema.tags == ["earnings", "weekly"]

    def test_type_from_string(self):
        schema = self._make_create(type="CASH_SECURED_PUT")
        assert schema.type == PositionType.CASH_SECURED_PUT

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            self._make_create(type="INVALID")

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            PositionCreate(ticker="AAPL")


class TestPositionUpdate:
    def test_all_none_by_default(self):
        schema = PositionUpdate()
        for field_name in PositionUpdate.model_fields:
            assert getattr(schema, field_name) is None

    def test_partial_update(self):
        schema = PositionUpdate(
            ticker="TSLA", strike_price=Decimal("200.00")
        )
        assert schema.ticker == "TSLA"
        assert schema.strike_price == Decimal("200.00")
        assert schema.contracts is None

    def test_type_validation(self):
        schema = PositionUpdate(type="COVERED_CALL")
        assert schema.type == PositionType.COVERED_CALL

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            PositionUpdate(type="INVALID")

    def test_update_includes_close_fields(self):
        schema = PositionUpdate(
            close_fees=Decimal("2.00"),
            close_price_per_share=Decimal("1.50"),
        )
        assert schema.close_fees == Decimal("2.00")
        assert schema.close_price_per_share == Decimal("1.50")


class TestPositionResponse:
    def _make_response(self, **overrides):
        defaults = dict(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            ticker="AAPL",
            type="COVERED_CALL",
            status="OPEN",
            open_date=date(2025, 1, 15),
            expiration_date=date(2025, 2, 21),
            close_date=None,
            strike_price=Decimal("150.00"),
            contracts=2,
            multiplier=100,
            premium_per_share=Decimal("3.50"),
            open_fees=Decimal("1.30"),
            close_fees=Decimal("0"),
            close_price_per_share=None,
            outcome=None,
            roll_group_id=None,
            notes=None,
            tags=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        defaults.update(overrides)
        return PositionResponse(**defaults)

    def test_premium_total(self):
        resp = self._make_response(
            premium_per_share=Decimal("3.50"),
            contracts=2,
            multiplier=100,
        )
        # 3.50 * 2 * 100 = 700.00
        assert resp.premium_total == Decimal("700.00")

    def test_premium_net(self):
        resp = self._make_response(
            premium_per_share=Decimal("3.50"),
            contracts=2,
            multiplier=100,
            open_fees=Decimal("1.30"),
            close_fees=Decimal("1.30"),
        )
        # 700.00 - 1.30 - 1.30 = 697.40
        assert resp.premium_net == Decimal("697.40")

    def test_collateral(self):
        resp = self._make_response(
            strike_price=Decimal("150.00"),
            contracts=2,
            multiplier=100,
        )
        # 150.00 * 2 * 100 = 30000.00
        assert resp.collateral == Decimal("30000.00")

    def test_roc_period(self):
        resp = self._make_response(
            premium_per_share=Decimal("3.50"),
            contracts=2,
            multiplier=100,
            open_fees=Decimal("1.30"),
            close_fees=Decimal("0"),
            strike_price=Decimal("150.00"),
        )
        # premium_net = 700 - 1.30 = 698.70
        # collateral = 30000
        # roc_period = 698.70 / 30000 = 0.02329
        expected = Decimal("698.70") / Decimal("30000")
        assert resp.roc_period == expected

    def test_roc_period_zero_collateral(self):
        resp = self._make_response(strike_price=Decimal("0"))
        assert resp.roc_period == Decimal("0")

    def test_dte(self):
        today = date.today()
        exp = date(today.year + 1, today.month, today.day)
        resp = self._make_response(expiration_date=exp)
        # Should be approximately 365 (could be 365 or 366 for leap year)
        assert 364 <= resp.dte <= 366

    def test_dte_expired(self):
        resp = self._make_response(expiration_date=date(2020, 1, 1))
        assert resp.dte < 0

    def test_annualized_roc_open_position(self):
        resp = self._make_response(
            premium_per_share=Decimal("3.50"),
            contracts=2,
            multiplier=100,
            open_fees=Decimal("0"),
            close_fees=Decimal("0"),
            strike_price=Decimal("150.00"),
            open_date=date(2025, 1, 1),
            expiration_date=date(2025, 2, 7),  # 37 days
            close_date=None,
        )
        # premium_net = 700
        # collateral = 30000
        # roc_period = 700/30000
        # days_in_trade = 37
        # annualized = (700/30000) * (365/37)
        roc = Decimal("700") / Decimal("30000")
        expected = roc * Decimal("365") / Decimal("37")
        assert resp.annualized_roc == expected

    def test_annualized_roc_closed_position(self):
        resp = self._make_response(
            premium_per_share=Decimal("3.50"),
            contracts=2,
            multiplier=100,
            open_fees=Decimal("0"),
            close_fees=Decimal("0"),
            strike_price=Decimal("150.00"),
            open_date=date(2025, 1, 1),
            expiration_date=date(2025, 2, 7),
            close_date=date(2025, 1, 20),  # closed after 19 days
        )
        roc = Decimal("700") / Decimal("30000")
        expected = roc * Decimal("365") / Decimal("19")
        assert resp.annualized_roc == expected

    def test_annualized_roc_zero_days(self):
        resp = self._make_response(
            open_date=date(2025, 1, 1),
            expiration_date=date(2025, 1, 1),
            close_date=None,
        )
        assert resp.annualized_roc == Decimal("0")

    def test_annualized_roc_zero_collateral(self):
        resp = self._make_response(strike_price=Decimal("0"))
        assert resp.annualized_roc == Decimal("0")

    def test_from_attributes_config(self):
        assert PositionResponse.model_config.get("from_attributes") is True

    def test_all_stored_fields_present(self):
        stored_fields = {
            "id", "user_id", "account_id", "ticker", "type", "status",
            "open_date", "expiration_date", "close_date", "strike_price",
            "contracts", "multiplier", "premium_per_share", "open_fees",
            "close_fees", "close_price_per_share", "outcome",
            "roll_group_id", "notes", "tags", "created_at", "updated_at",
        }
        assert stored_fields.issubset(set(PositionResponse.model_fields.keys()))

    def test_computed_fields_in_serialization(self):
        resp = self._make_response()
        data = resp.model_dump()
        for field in ("premium_total", "premium_net", "collateral",
                       "roc_period", "dte", "annualized_roc"):
            assert field in data, f"computed field {field!r} missing from serialized output"

    def test_model_config_uses_pydantic_v2(self):
        # Ensure model_config is used (Pydantic v2 style, not class Config)
        assert hasattr(PositionResponse, "model_config")
        assert hasattr(AccountResponse, "model_config")
        assert hasattr(PositionCreate, "model_config")
        assert hasattr(AccountCreate, "model_config")


# ---------------------------------------------------------------------------
# QA: Validation edge cases (US-036)
# ---------------------------------------------------------------------------

class TestAccountCreateValidation:
    """QA validation: account schema rejects invalid inputs."""

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="", broker=Broker.ROBINHOOD)

    def test_very_long_name_rejected(self):
        with pytest.raises(ValidationError):
            AccountCreate(name="x" * 256, broker=Broker.ROBINHOOD)

    def test_max_length_name_accepted(self):
        schema = AccountCreate(name="x" * 255, broker=Broker.ROBINHOOD)
        assert len(schema.name) == 255


class TestAccountUpdateValidation:
    """QA validation: account update rejects invalid inputs."""

    def test_empty_name_rejected(self):
        with pytest.raises(ValidationError):
            AccountUpdate(name="")

    def test_very_long_name_rejected(self):
        with pytest.raises(ValidationError):
            AccountUpdate(name="x" * 256)


class TestPositionCreateValidation:
    """QA validation: position create rejects invalid numeric/string inputs."""

    def _defaults(self, **overrides):
        base = dict(
            account_id=uuid.uuid4(),
            ticker="AAPL",
            type=PositionType.COVERED_CALL,
            open_date=date(2025, 1, 15),
            expiration_date=date(2025, 2, 21),
            strike_price=Decimal("150.00"),
            contracts=1,
            premium_per_share=Decimal("3.50"),
        )
        base.update(overrides)
        return base

    def test_negative_strike_price_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(strike_price=Decimal("-1")))

    def test_zero_strike_price_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(strike_price=Decimal("0")))

    def test_negative_contracts_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(contracts=-1))

    def test_zero_contracts_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(contracts=0))

    def test_negative_premium_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(premium_per_share=Decimal("-0.01")))

    def test_zero_premium_accepted(self):
        schema = PositionCreate(**self._defaults(premium_per_share=Decimal("0")))
        assert schema.premium_per_share == Decimal("0")

    def test_negative_multiplier_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(multiplier=-1))

    def test_zero_multiplier_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(multiplier=0))

    def test_negative_open_fees_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(open_fees=Decimal("-0.50")))

    def test_zero_open_fees_accepted(self):
        schema = PositionCreate(**self._defaults(open_fees=Decimal("0")))
        assert schema.open_fees == Decimal("0")

    def test_empty_ticker_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(ticker=""))

    def test_very_long_ticker_rejected(self):
        with pytest.raises(ValidationError):
            PositionCreate(**self._defaults(ticker="X" * 11))

    def test_max_length_ticker_accepted(self):
        schema = PositionCreate(**self._defaults(ticker="A" * 10))
        assert len(schema.ticker) == 10


class TestPositionUpdateValidation:
    """QA validation: position update rejects invalid values when provided."""

    def test_negative_strike_price_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(strike_price=Decimal("-1"))

    def test_zero_strike_price_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(strike_price=Decimal("0"))

    def test_negative_contracts_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(contracts=-1)

    def test_zero_contracts_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(contracts=0)

    def test_negative_close_fees_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(close_fees=Decimal("-0.01"))

    def test_negative_close_price_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(close_price_per_share=Decimal("-1"))

    def test_zero_close_fees_accepted(self):
        schema = PositionUpdate(close_fees=Decimal("0"))
        assert schema.close_fees == Decimal("0")

    def test_zero_close_price_accepted(self):
        schema = PositionUpdate(close_price_per_share=Decimal("0"))
        assert schema.close_price_per_share == Decimal("0")

    def test_empty_ticker_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(ticker="")

    def test_negative_multiplier_rejected(self):
        with pytest.raises(ValidationError):
            PositionUpdate(multiplier=0)


class TestPositionCloseValidation:
    """QA validation: close schema rejects invalid values."""

    def test_negative_close_fees_rejected(self):
        from app.schemas import PositionClose

        with pytest.raises(ValidationError):
            PositionClose(
                outcome="EXPIRED",
                close_date=date(2025, 2, 21),
                close_fees=Decimal("-1"),
            )

    def test_negative_close_price_rejected(self):
        from app.schemas import PositionClose

        with pytest.raises(ValidationError):
            PositionClose(
                outcome="EXPIRED",
                close_date=date(2025, 2, 21),
                close_price_per_share=Decimal("-0.01"),
            )

    def test_zero_close_fees_accepted(self):
        from app.schemas import PositionClose

        schema = PositionClose(
            outcome="EXPIRED",
            close_date=date(2025, 2, 21),
            close_fees=Decimal("0"),
        )
        assert schema.close_fees == Decimal("0")


class TestPositionRollCloseValidation:
    """QA validation: roll close schema rejects invalid values."""

    def test_negative_close_fees_rejected(self):
        from app.schemas.position import PositionRollClose

        with pytest.raises(ValidationError):
            PositionRollClose(
                close_date=date(2025, 2, 21),
                close_fees=Decimal("-1"),
            )

    def test_negative_close_price_rejected(self):
        from app.schemas.position import PositionRollClose

        with pytest.raises(ValidationError):
            PositionRollClose(
                close_date=date(2025, 2, 21),
                close_price_per_share=Decimal("-0.01"),
            )

"""Tests for core models."""

from datetime import date

import pytest

from src.tello_renewal.core.models import (
    AccountBalance,
    AccountSummary,
    BalanceQuantity,
    RenewalResult,
    RenewalStatus,
)


class TestBalanceQuantity:
    """Test BalanceQuantity model."""

    def test_from_tello_data_gb(self):
        """Test parsing data in GB format."""
        quantity = BalanceQuantity.from_tello("5.0 GB")
        assert quantity.value == 5.0
        assert quantity.unit == "GB"
        assert not quantity.is_unlimited

    def test_from_tello_unlimited(self):
        """Test parsing unlimited quantity."""
        quantity = BalanceQuantity.from_tello("unlimited minutes")
        assert quantity.value is None
        assert quantity.unit == "minutes"
        assert quantity.is_unlimited

    def test_from_tello_minutes(self):
        """Test parsing minutes."""
        quantity = BalanceQuantity.from_tello("300 minutes")
        assert quantity.value == 300
        assert quantity.unit == "minutes"
        assert not quantity.is_unlimited

    def test_addition_normal(self):
        """Test adding two normal quantities."""
        q1 = BalanceQuantity(5.0, "GB")
        q2 = BalanceQuantity(2.0, "GB")
        result = q1 + q2
        assert result.value == 7.0
        assert result.unit == "GB"

    def test_addition_unlimited(self):
        """Test adding with unlimited quantity."""
        q1 = BalanceQuantity(5.0, "GB")
        q2 = BalanceQuantity(None, "GB")
        result = q1 + q2
        assert result.value is None
        assert result.unit == "GB"
        assert result.is_unlimited

    def test_addition_different_units_raises_error(self):
        """Test that adding different units raises error."""
        q1 = BalanceQuantity(5.0, "GB")
        q2 = BalanceQuantity(300, "minutes")
        with pytest.raises(ValueError, match="Cannot add different units"):
            q1 + q2

    def test_string_representation(self):
        """Test string representation."""
        q1 = BalanceQuantity(5.0, "GB")
        assert str(q1) == "5.0 GB"

        q2 = BalanceQuantity(None, "minutes")
        assert str(q2) == "Unlimited minutes"


class TestAccountBalance:
    """Test AccountBalance model."""

    def test_creation(self):
        """Test creating account balance."""
        data = BalanceQuantity(5.0, "GB")
        minutes = BalanceQuantity(300, "minutes")
        texts = BalanceQuantity(None, "texts")

        balance = AccountBalance(data=data, minutes=minutes, texts=texts)
        assert balance.data == data
        assert balance.minutes == minutes
        assert balance.texts == texts

    def test_addition(self):
        """Test adding two account balances."""
        balance1 = AccountBalance(
            data=BalanceQuantity(5.0, "GB"),
            minutes=BalanceQuantity(300, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        balance2 = AccountBalance(
            data=BalanceQuantity(2.0, "GB"),
            minutes=BalanceQuantity(100, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        result = balance1 + balance2
        assert result.data.value == 7.0
        assert result.minutes.value == 400
        assert result.texts.is_unlimited

    def test_to_dict(self):
        """Test converting to dictionary."""
        balance = AccountBalance(
            data=BalanceQuantity(5.0, "GB"),
            minutes=BalanceQuantity(300, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        result = balance.to_dict()
        expected = {
            "data": "5.0 GB",
            "minutes": "300 minutes",
            "texts": "Unlimited texts",
        }
        assert result == expected


class TestAccountSummary:
    """Test AccountSummary model."""

    def test_creation(self):
        """Test creating account summary."""
        current_balance = AccountBalance(
            data=BalanceQuantity(5.0, "GB"),
            minutes=BalanceQuantity(300, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        plan_balance = AccountBalance(
            data=BalanceQuantity(2.0, "GB"),
            minutes=BalanceQuantity(100, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        summary = AccountSummary(
            email="test@example.com",
            renewal_date=date(2024, 1, 15),
            current_balance=current_balance,
            plan_balance=plan_balance,
            days_until_renewal=5,
        )

        assert summary.email == "test@example.com"
        assert summary.renewal_date == date(2024, 1, 15)
        assert summary.days_until_renewal == 5

    def test_new_balance_property(self):
        """Test new balance calculation."""
        current_balance = AccountBalance(
            data=BalanceQuantity(5.0, "GB"),
            minutes=BalanceQuantity(300, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        plan_balance = AccountBalance(
            data=BalanceQuantity(2.0, "GB"),
            minutes=BalanceQuantity(100, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        summary = AccountSummary(
            email="test@example.com",
            renewal_date=date(2024, 1, 15),
            current_balance=current_balance,
            plan_balance=plan_balance,
            days_until_renewal=5,
        )

        new_balance = summary.new_balance
        assert new_balance.data.value == 7.0
        assert new_balance.minutes.value == 400

    def test_is_renewal_due(self):
        """Test renewal due check."""
        current_balance = AccountBalance(
            data=BalanceQuantity(5.0, "GB"),
            minutes=BalanceQuantity(300, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        plan_balance = AccountBalance(
            data=BalanceQuantity(2.0, "GB"),
            minutes=BalanceQuantity(100, "minutes"),
            texts=BalanceQuantity(None, "texts"),
        )

        # Test renewal due (1 day)
        summary_due = AccountSummary(
            email="test@example.com",
            renewal_date=date(2024, 1, 15),
            current_balance=current_balance,
            plan_balance=plan_balance,
            days_until_renewal=1,
        )
        assert summary_due.is_renewal_due

        # Test renewal not due (5 days)
        summary_not_due = AccountSummary(
            email="test@example.com",
            renewal_date=date(2024, 1, 15),
            current_balance=current_balance,
            plan_balance=plan_balance,
            days_until_renewal=5,
        )
        assert not summary_not_due.is_renewal_due


class TestRenewalResult:
    """Test RenewalResult model."""

    def test_creation(self):
        """Test creating renewal result."""
        from datetime import datetime

        result = RenewalResult(
            status=RenewalStatus.SUCCESS,
            timestamp=datetime(2024, 1, 15, 10, 30),
            message="Renewal completed successfully",
            duration_seconds=45.5,
        )

        assert result.status == RenewalStatus.SUCCESS
        assert result.message == "Renewal completed successfully"
        assert result.duration_seconds == 45.5
        assert result.success is True

    def test_success_property(self):
        """Test success property."""
        from datetime import datetime

        success_result = RenewalResult(
            status=RenewalStatus.SUCCESS, timestamp=datetime.now(), message="Success"
        )
        assert success_result.success is True

        failed_result = RenewalResult(
            status=RenewalStatus.FAILED, timestamp=datetime.now(), message="Failed"
        )
        assert failed_result.success is False

    def test_to_dict(self):
        """Test converting to dictionary."""
        from datetime import datetime

        timestamp = datetime(2024, 1, 15, 10, 30)
        result = RenewalResult(
            status=RenewalStatus.SUCCESS,
            timestamp=timestamp,
            message="Renewal completed successfully",
            duration_seconds=45.5,
        )

        result_dict = result.to_dict()
        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Renewal completed successfully"
        assert result_dict["success"] is True
        assert result_dict["duration_seconds"] == 45.5
        assert result_dict["timestamp"] == timestamp.isoformat()

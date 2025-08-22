"""Data models for Tello renewal system.

This module contains the core data models used throughout the application,
including balance quantities, account information, and renewal results.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional, Union

from ..utils.logging import get_logger

logger = get_logger(__name__)


class RenewalStatus(Enum):
    """Status of a renewal operation."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NOT_DUE = "not_due"


class BalanceQuantity:
    """Represents a balance quantity with value and unit.

    This class handles parsing and arithmetic operations on Tello balance
    quantities, which can be unlimited or have specific numeric values.
    """

    def __init__(self, value: Optional[Union[int, float]], unit: str) -> None:
        """Initialize a balance quantity.

        Args:
            value: The numeric value, or None for unlimited
            unit: The unit of measurement (e.g., "GB", "minutes", "texts")
        """
        self._value = value
        self._unit = unit

    @classmethod
    def from_tello(cls, tello_str: str) -> BalanceQuantity:
        """Parse a balance quantity from Tello's string format.

        Args:
            tello_str: String from Tello website (e.g., "5.0 GB", "unlimited minutes")

        Returns:
            BalanceQuantity instance

        Raises:
            ValueError: If the format is not recognized
        """
        parts = tello_str.strip().split(" ", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid balance format: {tello_str}")

        value_str, unit = parts

        # Normalize unit names - handle both singular and plural forms
        unit_mapping = {
            "min": "minutes",
            "minute": "minutes",
            "minutes": "minutes",
            "text": "texts",
            "texts": "texts",
            "gb": "GB",
            "mb": "MB",
        }
        normalized_unit = unit_mapping.get(unit.lower(), unit.lower())

        if value_str.lower() == "unlimited":
            return cls(None, normalized_unit)

        try:
            if normalized_unit in ("GB", "MB"):
                return cls(float(value_str), normalized_unit)
            elif normalized_unit in ("minutes", "texts"):
                return cls(int(value_str), normalized_unit)
            else:
                # Default to float for unknown units
                return cls(float(value_str), normalized_unit)
        except ValueError as e:
            raise ValueError(f"Cannot parse value '{value_str}' as number: {e}")

    def __add__(self, other: BalanceQuantity) -> BalanceQuantity:
        """Add two balance quantities.

        Args:
            other: Another BalanceQuantity to add

        Returns:
            New BalanceQuantity with the sum

        Raises:
            ValueError: If units don't match
        """
        if self._unit != other._unit:
            raise ValueError(
                f"Cannot add different units: {self._unit} + {other._unit}"
            )

        if self._value is None or other._value is None:
            return BalanceQuantity(None, self._unit)

        return BalanceQuantity(self._value + other._value, self._unit)

    def __str__(self) -> str:
        """String representation of the balance quantity."""
        if self._value is None:
            return f"Unlimited {self._unit}"
        return f"{self._value} {self._unit}"

    def __repr__(self) -> str:
        """Developer representation of the balance quantity."""
        return f"BalanceQuantity(value={self._value}, unit='{self._unit}')"

    @property
    def value(self) -> Optional[Union[int, float]]:
        """Get the numeric value."""
        return self._value

    @property
    def unit(self) -> str:
        """Get the unit."""
        return self._unit

    @property
    def is_unlimited(self) -> bool:
        """Check if this quantity is unlimited."""
        return self._value is None


@dataclass
class AccountBalance:
    """Account balance information containing data, minutes, and texts."""

    data: BalanceQuantity
    minutes: BalanceQuantity
    texts: BalanceQuantity

    def __add__(self, other: AccountBalance) -> AccountBalance:
        """Add two account balances.

        Args:
            other: Another AccountBalance to add

        Returns:
            New AccountBalance with the sum of all quantities
        """
        return AccountBalance(
            data=self.data + other.data,
            minutes=self.minutes + other.minutes,
            texts=self.texts + other.texts,
        )

    def __str__(self) -> str:
        """String representation of the account balance."""
        return f"{self.data}, {self.minutes}, {self.texts}"

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "data": str(self.data),
            "minutes": str(self.minutes),
            "texts": str(self.texts),
        }


@dataclass
class RenewalResult:
    """Result of a renewal operation."""

    status: RenewalStatus
    timestamp: datetime
    message: str
    new_balance: Optional[AccountBalance] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None

    @property
    def success(self) -> bool:
        """Check if the renewal was successful."""
        return self.status == RenewalStatus.SUCCESS

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        result = {
            "status": self.status.value,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "success": self.success,
        }

        if self.new_balance:
            result["new_balance"] = self.new_balance.to_dict()
        if self.error:
            result["error"] = self.error
        if self.duration_seconds:
            result["duration_seconds"] = self.duration_seconds

        return result


@dataclass
class AccountSummary:
    """Complete account summary information."""

    email: str
    renewal_date: date
    current_balance: AccountBalance
    plan_balance: AccountBalance
    days_until_renewal: int

    @property
    def new_balance(self) -> AccountBalance:
        """Calculate the balance after renewal."""
        return self.current_balance + self.plan_balance

    @property
    def is_renewal_due(self) -> bool:
        """Check if renewal is due (within 1 day)."""
        return self.days_until_renewal <= 1

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "email": self.email,
            "renewal_date": self.renewal_date.isoformat(),
            "current_balance": self.current_balance.to_dict(),
            "plan_balance": self.plan_balance.to_dict(),
            "new_balance": self.new_balance.to_dict(),
            "days_until_renewal": self.days_until_renewal,
            "is_renewal_due": self.is_renewal_due,
        }

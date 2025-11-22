"""Balance service for Tello renewal system.

This module provides balance-related business logic including
current balance retrieval and balance calculations.
"""

from ...utils.logging import get_logger
from ...web.client import TelloWebClient
from ..models import AccountBalance

logger = get_logger(__name__)


class BalanceService:
    """Service for balance-related operations."""

    def __init__(self, web_client: TelloWebClient):
        """Initialize balance service.

        Args:
            web_client: Web client for automation
        """
        self.web_client = web_client

    def get_current_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            Current account balance

        Raises:
            Exception: If balance retrieval fails
        """
        try:
            current_balance = self.web_client.get_current_balance()
            logger.info(f"Retrieved current balance: {current_balance}")
            return current_balance

        except Exception as e:
            logger.error(f"Failed to get current balance: {e}")
            raise

    def get_plan_balance(self) -> AccountBalance:
        """Get plan balance information.

        Returns:
            Plan balance that will be added upon renewal

        Raises:
            Exception: If plan balance retrieval fails
        """
        try:
            plan_balance = self.web_client.get_plan_balance()
            logger.info(f"Retrieved plan balance: {plan_balance}")
            return plan_balance

        except Exception as e:
            logger.error(f"Failed to get plan balance: {e}")
            raise

    def calculate_new_balance(
        self, current: AccountBalance, plan: AccountBalance
    ) -> AccountBalance:
        """Calculate new balance after renewal.

        Args:
            current: Current account balance
            plan: Plan balance to be added

        Returns:
            New balance after renewal
        """
        try:
            new_balance = current + plan
            logger.info(f"Calculated new balance: {new_balance}")
            return new_balance

        except Exception as e:
            logger.error(f"Failed to calculate new balance: {e}")
            raise

    def get_balance_summary(self) -> dict[str, AccountBalance]:
        """Get complete balance summary.

        Returns:
            Dictionary containing current, plan, and new balances

        Raises:
            Exception: If balance retrieval fails
        """
        try:
            current_balance = self.get_current_balance()
            plan_balance = self.get_plan_balance()
            new_balance = self.calculate_new_balance(current_balance, plan_balance)

            summary = {
                "current": current_balance,
                "plan": plan_balance,
                "new": new_balance,
            }

            logger.info("Retrieved complete balance summary")
            return summary

        except Exception as e:
            logger.error(f"Failed to get balance summary: {e}")
            raise

    def is_balance_sufficient(self, minimum_data_gb: float = 0.1) -> bool:
        """Check if current balance is sufficient.

        Args:
            minimum_data_gb: Minimum data balance required in GB

        Returns:
            True if balance is sufficient, False otherwise
        """
        try:
            current_balance = self.get_current_balance()

            # Check if data is unlimited
            if current_balance.data.is_unlimited:
                logger.info("Data balance is unlimited - sufficient")
                return True

            # Check if data balance meets minimum requirement
            if current_balance.data.value is not None:
                data_gb = current_balance.data.value
                if current_balance.data.unit == "MB":
                    data_gb = data_gb / 1024  # Convert MB to GB

                is_sufficient = data_gb >= minimum_data_gb
                logger.info(
                    f"Data balance: {data_gb:.2f} GB, minimum: {minimum_data_gb} GB, sufficient: {is_sufficient}"
                )
                return is_sufficient

            logger.warning("Could not determine data balance value")
            return False

        except Exception as e:
            logger.error(f"Failed to check balance sufficiency: {e}")
            return False

    def format_balance_for_display(self, balance: AccountBalance) -> str:
        """Format balance for human-readable display.

        Args:
            balance: Account balance to format

        Returns:
            Formatted balance string
        """
        return (
            f"Data: {balance.data}, Minutes: {balance.minutes}, Texts: {balance.texts}"
        )

    def log_balance_details(
        self, balance: AccountBalance, label: str = "Balance"
    ) -> None:
        """Log detailed balance information.

        Args:
            balance: Account balance to log
            label: Label for the balance (e.g., "Current", "Plan", "New")
        """
        logger.info(f"{label} Balance Details:")
        logger.info(f"  Data: {balance.data}")
        logger.info(f"  Minutes: {balance.minutes}")
        logger.info(f"  Texts: {balance.texts}")

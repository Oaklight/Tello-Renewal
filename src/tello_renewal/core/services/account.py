"""Account service for Tello renewal system.

This module provides account-related business logic including
account summary retrieval and renewal date checking.
"""

from datetime import date

from ...utils.logging import get_logger
from ...web.client import TelloWebClient
from ..models import AccountSummary

logger = get_logger(__name__)


class AccountService:
    """Service for account-related operations."""

    def __init__(self, web_client: TelloWebClient):
        """Initialize account service.

        Args:
            web_client: Web client for automation
        """
        self.web_client = web_client

    def get_account_summary(self) -> AccountSummary:
        """Get complete account summary information.

        Returns:
            Complete account summary

        Raises:
            Exception: If account information retrieval fails
        """
        try:
            # Get renewal date
            renewal_date = self.web_client.get_renewal_date()

            # Get current and plan balances
            current_balance = self.web_client.get_current_balance()
            plan_balance = self.web_client.get_plan_balance()

            # Calculate days until renewal
            days_until = (renewal_date - date.today()).days

            # Get email from web client (would need to be passed in or stored)
            # For now, we'll need to get this from configuration
            email = "unknown@example.com"  # This should be passed from config

            summary = AccountSummary(
                email=email,
                renewal_date=renewal_date,
                current_balance=current_balance,
                plan_balance=plan_balance,
                days_until_renewal=days_until,
            )

            logger.info(f"Retrieved account summary for {email}")
            return summary

        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            raise

    def get_renewal_date(self) -> date:
        """Get account renewal date.

        Returns:
            Next renewal date

        Raises:
            Exception: If renewal date retrieval fails
        """
        try:
            renewal_date = self.web_client.get_renewal_date()
            logger.info(f"Retrieved renewal date: {renewal_date}")
            return renewal_date

        except Exception as e:
            logger.error(f"Failed to get renewal date: {e}")
            raise

    def check_renewal_needed(self, renewal_date: date, days_before: int = 1) -> bool:
        """Check if renewal is needed based on date.

        Args:
            renewal_date: The renewal due date
            days_before: Days before renewal to trigger

        Returns:
            True if renewal should be performed
        """
        today = date.today()
        days_until = (renewal_date - today).days

        logger.info(f"Renewal date: {renewal_date}, Days until renewal: {days_until}")

        if days_until <= days_before:
            logger.info("Renewal is due")
            return True
        else:
            logger.info(f"Renewal not due yet ({days_until} days remaining)")
            return False

    def is_logged_in(self) -> bool:
        """Check if user is currently logged in.

        Returns:
            True if logged in, False otherwise
        """
        try:
            return self.web_client.is_logged_in()
        except Exception as e:
            logger.warning(f"Failed to check login status: {e}")
            return False

    def login(self, email: str, password: str, base_url: str) -> None:
        """Login to Tello account.

        Args:
            email: Account email
            password: Account password
            base_url: Tello base URL

        Raises:
            Exception: If login fails
        """
        try:
            self.web_client.open_login_page(base_url)
            self.web_client.login(email, password)
            logger.info(f"Successfully logged in as {email}")

        except Exception as e:
            logger.error(f"Login failed for {email}: {e}")
            raise

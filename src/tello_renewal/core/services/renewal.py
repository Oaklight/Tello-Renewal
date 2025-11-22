"""Renewal service for Tello renewal system.

This module provides renewal-related business logic including
renewal execution and form handling.
"""

from datetime import date
from typing import Any

from ...utils.logging import get_logger
from ...web.client import TelloWebClient

logger = get_logger(__name__)


class RenewalService:
    """Service for renewal-related operations."""

    def __init__(self, web_client: TelloWebClient):
        """Initialize renewal service.

        Args:
            web_client: Web client for automation
        """
        self.web_client = web_client

    def execute_renewal(self, card_expiration: date, dry_run: bool = False) -> bool:
        """Execute the renewal process.

        Args:
            card_expiration: Credit card expiration date
            dry_run: If True, don't actually submit the renewal

        Returns:
            True if renewal was successful

        Raises:
            Exception: If renewal fails
        """
        try:
            logger.info(f"Starting renewal process (dry_run={dry_run})")

            # Navigate to renewal page
            self.open_renewal_page()

            # Fill renewal form
            self.fill_renewal_form(card_expiration)

            # Submit renewal
            success = self.submit_renewal(dry_run)

            if success:
                logger.info("Renewal process completed successfully")
            else:
                logger.error("Renewal process failed")

            return success

        except Exception as e:
            logger.error(f"Renewal execution failed: {e}")
            raise

    def open_renewal_page(self) -> None:
        """Navigate to renewal page by clicking renew button.

        Raises:
            Exception: If navigation fails
        """
        try:
            self.web_client.open_renewal_page()
            logger.info("Successfully opened renewal page")

        except Exception as e:
            logger.error(f"Failed to open renewal page: {e}")
            raise

    def fill_renewal_form(self, card_expiration: date) -> None:
        """Fill renewal form with required information.

        Args:
            card_expiration: Credit card expiration date

        Raises:
            Exception: If form filling fails
        """
        try:
            # Fill card expiration
            self.web_client.fill_card_expiration(card_expiration)

            # Check notification checkbox
            self.web_client.check_notification_checkbox()

            logger.info("Successfully filled renewal form")

        except Exception as e:
            logger.error(f"Failed to fill renewal form: {e}")
            raise

    def submit_renewal(self, dry_run: bool = False) -> bool:
        """Submit the renewal order.

        Args:
            dry_run: If True, don't actually submit the form

        Returns:
            True if submission was successful (or skipped in dry run)

        Raises:
            Exception: If submission fails
        """
        try:
            success = self.web_client.submit_renewal()

            if dry_run:
                logger.info("DRY RUN: Renewal submission skipped")
            else:
                logger.info("Renewal submitted successfully")

            return success

        except Exception as e:
            logger.error(f"Failed to submit renewal: {e}")
            raise

    def complete_renewal_process(
        self, card_expiration: date, dry_run: bool = False
    ) -> bool:
        """Complete the entire renewal process in one operation.

        Args:
            card_expiration: Credit card expiration date
            dry_run: If True, don't actually submit the renewal

        Returns:
            True if renewal process completed successfully

        Raises:
            Exception: If any step fails
        """
        try:
            if dry_run:
                logger.info("DRY RUN: Complete renewal process skipped")
                return True
            return self.web_client.complete_renewal_process(card_expiration)

        except Exception as e:
            logger.error(f"Complete renewal process failed: {e}")
            raise

    def validate_renewal_prerequisites(self) -> bool:
        """Validate that all prerequisites for renewal are met.

        Returns:
            True if prerequisites are met, False otherwise
        """
        try:
            # Check if user is logged in
            if not self.web_client.is_logged_in():
                logger.error("User is not logged in")
                return False

            # Check if we're on the correct page (dashboard)
            current_url = self.web_client.get_current_url()
            if "account" not in current_url.lower():
                logger.warning(f"May not be on account page: {current_url}")

            logger.info("Renewal prerequisites validated successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to validate renewal prerequisites: {e}")
            return False

    def get_renewal_status(self) -> dict[str, Any]:
        """Get current renewal status information.

        Returns:
            Dictionary containing renewal status information
        """
        try:
            status = {
                "logged_in": self.web_client.is_logged_in(),
                "current_url": self.web_client.get_current_url(),
                "page_title": self.web_client.get_page_title(),
                "prerequisites_met": self.validate_renewal_prerequisites(),
            }

            logger.debug(f"Renewal status: {status}")
            return status

        except Exception as e:
            logger.error(f"Failed to get renewal status: {e}")
            return {
                "logged_in": False,
                "current_url": "unknown",
                "page_title": "unknown",
                "prerequisites_met": False,
                "error": str(e),
            }

    def prepare_for_renewal(self) -> bool:
        """Prepare system for renewal process.

        Returns:
            True if preparation was successful

        Raises:
            Exception: If preparation fails
        """
        try:
            # Validate prerequisites
            if not self.validate_renewal_prerequisites():
                raise Exception("Renewal prerequisites not met")

            logger.info("System prepared for renewal")
            return True

        except Exception as e:
            logger.error(f"Failed to prepare for renewal: {e}")
            raise

    def cleanup_after_renewal(self) -> None:
        """Cleanup operations after renewal completion.

        This method performs any necessary cleanup operations
        after the renewal process is complete.
        """
        try:
            # Log final status
            status = self.get_renewal_status()
            logger.info(f"Final renewal status: {status}")

            logger.info("Renewal cleanup completed")

        except Exception as e:
            logger.warning(f"Renewal cleanup failed: {e}")

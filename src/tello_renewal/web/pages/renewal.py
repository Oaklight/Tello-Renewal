"""Renewal page implementation for Tello website.

This module provides renewal functionality including form filling
and submission using the Page Object Model pattern.
"""

from datetime import date

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import Select

from ...utils.exceptions import RenewalError
from ...utils.logging import get_logger, log_function_call
from ..elements.locators import TelloLocators
from .base import BasePage

logger = get_logger(__name__)


class RenewalPage(BasePage):
    """Renewal page for Tello website."""

    def __init__(self, driver: WebDriver, timeout: int = 30):
        """Initialize renewal page.

        Args:
            driver: WebDriver instance
            timeout: Default timeout for operations
        """
        super().__init__(driver, timeout)

    def fill_card_expiration(self, expiration_date: date) -> None:
        """Fill credit card expiration date on renewal form.

        Args:
            expiration_date: Card expiration date

        Raises:
            RenewalError: If form elements not found or filling fails
        """
        log_function_call("fill_card_expiration", expiration_date=expiration_date)

        try:
            # Fill expiration month
            month_element = self.wait_for_element(TelloLocators.CARD_EXPIRY_MONTH)
            month_select = Select(month_element)
            month_select.select_by_value(str(expiration_date.month))
            logger.debug(f"Selected expiration month: {expiration_date.month}")

            # Fill expiration year
            year_element = self.wait_for_element(TelloLocators.CARD_EXPIRY_YEAR)
            year_select = Select(year_element)
            year_select.select_by_value(str(expiration_date.year))
            logger.debug(f"Selected expiration year: {expiration_date.year}")

            logger.info(
                f"Filled card expiration: {expiration_date.month}/{expiration_date.year}"
            )

        except Exception as e:
            raise RenewalError(f"Failed to fill card expiration: {e}")

    def check_notification_checkbox(self) -> None:
        """Check the recurring charge notification checkbox.

        Raises:
            RenewalError: If checkbox not found
        """
        try:
            checkbox_element = self.wait_for_element(
                TelloLocators.NOTIFICATION_CHECKBOX
            )

            if not checkbox_element.is_selected():
                checkbox_element.click()
                logger.info("Checked notification checkbox")
            else:
                logger.info("Notification checkbox already checked")

        except Exception as e:
            raise RenewalError(f"Failed to check notification checkbox: {e}")

    def submit_renewal(self, dry_run: bool = False) -> bool:
        """Submit the renewal order.

        Args:
            dry_run: If True, don't actually submit the form

        Returns:
            True if submission was successful (or skipped in dry run)

        Raises:
            RenewalError: If submission fails
        """
        try:
            finalize_button_element = self.wait_for_element(
                TelloLocators.FINALIZE_ORDER_BUTTON
            )

            if dry_run:
                button_text = finalize_button_element.text
                if "Finalize Order" in button_text:
                    logger.info(
                        f"DRY RUN: Found finalize order button '{button_text}', skipping click"
                    )
                    return True
                else:
                    raise RenewalError(
                        f"Expected 'Finalize Order' button, found: '{button_text}'"
                    )
            else:
                finalize_button_element.click()
                logger.info("Clicked finalize order button")

                # Wait a bit for processing
                import time

                time.sleep(5)
                return True

        except Exception as e:
            raise RenewalError(f"Failed to submit renewal: {e}")

    def complete_renewal_process(
        self, expiration_date: date, dry_run: bool = False
    ) -> bool:
        """Complete the entire renewal process.

        Args:
            expiration_date: Card expiration date
            dry_run: If True, don't actually submit the form

        Returns:
            True if renewal process completed successfully

        Raises:
            RenewalError: If any step fails
        """
        try:
            self.fill_card_expiration(expiration_date)
            self.check_notification_checkbox()
            success = self.submit_renewal(dry_run)

            if success:
                logger.info("Renewal process completed successfully")

            return success

        except RenewalError:
            raise
        except Exception as e:
            raise RenewalError(f"Renewal process failed: {e}")

    def is_on_renewal_page(self) -> bool:
        """Check if currently on renewal page.

        Returns:
            True if on renewal page, False otherwise
        """
        return self.is_element_present(TelloLocators.FINALIZE_ORDER_BUTTON, timeout=5)

    def get_renewal_summary(self) -> dict:
        """Get renewal summary information if available.

        Returns:
            Dictionary with renewal summary data
        """
        # This would need to be implemented based on actual renewal page structure
        # Placeholder for now
        return {
            "status": "ready_for_submission",
            "has_finalize_button": self.is_on_renewal_page(),
        }

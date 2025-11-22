"""Dashboard page implementation for Tello website.

This module provides dashboard functionality including balance checking
and renewal date retrieval using the Page Object Model pattern.
"""

import re
from datetime import date, datetime
from typing import List, Optional

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from ...core.models import AccountBalance, BalanceQuantity
from ...utils.exceptions import ElementNotFoundError
from ...utils.logging import get_logger
from ..elements.locators import TelloLocators
from .base import BasePage

logger = get_logger(__name__)


class DashboardPage(BasePage):
    """Dashboard page for Tello website."""

    def __init__(self, driver: WebDriver, timeout: int = 30):
        """Initialize dashboard page.

        Args:
            driver: WebDriver instance
            timeout: Default timeout for operations
        """
        super().__init__(driver, timeout)

    def get_renewal_date(self) -> date:
        """Extract renewal date from account page.

        Returns:
            Next renewal date

        Raises:
            ElementNotFoundError: If renewal date element not found
        """
        try:
            date_text = self.get_text_safe(TelloLocators.RENEWAL_DATE)

            # Parse date in MM/DD/YYYY format
            renewal_date = datetime.strptime(date_text, "%m/%d/%Y").date()
            logger.info(f"Found renewal date: {renewal_date}")
            return renewal_date

        except ValueError as e:
            # date_text is guaranteed to be defined here since we're in the try block
            date_text_safe = locals().get("date_text", "unknown")
            raise ElementNotFoundError(
                f"Failed to parse renewal date '{date_text_safe}': {e}"
            )
        except Exception as e:
            raise ElementNotFoundError(f"Failed to get renewal date: {e}")

    def get_current_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            Current account balance

        Raises:
            ElementNotFoundError: If balance elements not found
        """
        try:
            # Get account balance from pack_card structure
            account_balance_amount = self._extract_account_balance()

            if account_balance_amount is not None:
                # Get usage data from balance-details elements
                balance_details = self._get_balance_details()

                if len(balance_details) >= 2:
                    data_text = balance_details[0].text
                    minutes_text = balance_details[1].text

                    # Handle texts - check if there's a third element or assume unlimited
                    if len(balance_details) >= 3:
                        texts_text = balance_details[2].text
                    else:
                        texts_text = "unlimited texts"
                        logger.debug("No texts balance found, assuming unlimited texts")

                    balance = AccountBalance(
                        data=BalanceQuantity.from_tello(data_text),
                        minutes=BalanceQuantity.from_tello(minutes_text),
                        texts=BalanceQuantity.from_tello(texts_text),
                    )

                    logger.info(f"Current balance: {balance}")
                    return balance
                else:
                    raise ElementNotFoundError(
                        f"Insufficient balance-details elements: {len(balance_details)}"
                    )
            else:
                raise ElementNotFoundError("Could not extract account balance amount")

        except Exception as e:
            raise ElementNotFoundError(f"Failed to get current balance: {e}")

    def get_plan_balance(self) -> AccountBalance:
        """Get plan balance information.

        Returns:
            Plan balance that will be added upon renewal

        Raises:
            ElementNotFoundError: If plan elements not found
        """
        try:
            # Get plan data
            plan_data_text = self.get_text_safe(TelloLocators.PLAN_DATA)
            plan_data = BalanceQuantity.from_tello(plan_data_text)

            # Get plan minutes
            plan_minutes_text = self.get_text_safe(TelloLocators.PLAN_MINUTES)
            plan_minutes = BalanceQuantity.from_tello(plan_minutes_text)

            # Get plan texts
            plan_texts_text = self.get_text_safe(TelloLocators.PLAN_TEXTS)
            plan_texts = BalanceQuantity.from_tello(plan_texts_text)

            balance = AccountBalance(
                data=plan_data,
                minutes=plan_minutes,
                texts=plan_texts,
            )

            logger.info(f"Plan balance: {balance}")
            return balance

        except Exception as e:
            raise ElementNotFoundError(f"Failed to get plan balance: {e}")

    def click_renew_button(self) -> None:
        """Click the plan renewal button.

        Raises:
            ElementNotFoundError: If renew button not found or not clickable
        """
        try:
            success = self.click_with_strategies(TelloLocators.RENEW_BUTTON)
            if success:
                logger.info("Successfully clicked renew button")
                # Wait a bit for page transition
                import time

                time.sleep(3)
            else:
                raise ElementNotFoundError("Failed to click renew button")

        except Exception as e:
            raise ElementNotFoundError(f"Failed to click renew button: {e}")

    def _extract_account_balance(self) -> Optional[float]:
        """Extract account balance amount from pack cards.

        Returns:
            Account balance amount

        Raises:
            ElementNotFoundError: If balance cannot be extracted
        """
        try:
            # Look for pack_card elements that contain "Remaining balance"
            pack_cards = self.driver.find_elements(
                *TelloLocators.BALANCE_PACK_CARDS.by_value_tuple()
            )

            for card in pack_cards:
                card_text = card.text
                if "Remaining balance" in card_text:
                    logger.debug(f"Found balance card text: {card_text}")

                    # Extract balance amount using regex - handle Unicode directional marks
                    balance_match = re.search(r"[⁦]?\$(\d+(?:\.\d{2})?)[⁩]?", card_text)
                    if balance_match:
                        account_balance_amount = float(balance_match.group(1))
                        logger.info(
                            f"Successfully extracted account balance: ${account_balance_amount}"
                        )
                        return account_balance_amount

            raise ElementNotFoundError("Could not find balance amount in pack cards")

        except Exception as e:
            raise ElementNotFoundError(f"Failed to extract account balance: {e}")

    def _get_balance_details(self) -> List[WebElement]:
        """Get balance details elements.

        Returns:
            List of balance details elements

        Raises:
            ElementNotFoundError: If balance details not found
        """
        try:
            balance_details = self.driver.find_elements(
                *TelloLocators.BALANCE_DETAILS.by_value_tuple()
            )
            logger.debug(f"Found {len(balance_details)} balance-details elements")
            return balance_details

        except Exception as e:
            raise ElementNotFoundError(f"Failed to get balance details: {e}")

    def is_on_dashboard(self) -> bool:
        """Check if currently on dashboard page.

        Returns:
            True if on dashboard, False otherwise
        """
        return self.is_element_present(TelloLocators.RENEWAL_DATE, timeout=5)

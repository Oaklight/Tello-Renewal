"""Element locators for Tello website automation.

This module centralizes all element locators used for web automation,
providing fallback strategies and clear documentation for each element.
"""

from dataclasses import dataclass, field
from typing import Any

from selenium.webdriver.common.by import By


@dataclass
class Locator:
    """Element locator with fallback support."""

    by: str
    value: str
    description: str
    fallbacks: list["Locator"] = field(default_factory=list)

    def __post_init__(self):
        """Validate locator after initialization."""
        valid_by_types = {
            By.ID,
            By.NAME,
            By.CLASS_NAME,
            By.TAG_NAME,
            By.LINK_TEXT,
            By.PARTIAL_LINK_TEXT,
            By.CSS_SELECTOR,
            By.XPATH,
        }
        if self.by not in valid_by_types:
            raise ValueError(f"Invalid locator type: {self.by}")

    def by_value_tuple(self) -> tuple[str, str]:
        """Get (by, value) tuple for Selenium operations.

        Returns:
            Tuple of (by, value) for use with find_element/find_elements
        """
        return (self.by, self.value)


class TelloLocators:
    """Centralized collection of Tello website element locators."""

    # Login page elements
    LOGIN_EMAIL = Locator(
        By.CSS_SELECTOR, "input#i_username", "Login email input field"
    )

    LOGIN_PASSWORD = Locator(
        By.CSS_SELECTOR, "input#i_current_password", "Login password input field"
    )

    # Dashboard page elements
    RENEWAL_DATE = Locator(
        By.CSS_SELECTOR, "span.card_text > span", "Renewal date display"
    )

    RENEW_BUTTON = Locator(
        By.CSS_SELECTOR,
        "button#renew_plan",
        "Plan renewal button",
        fallbacks=[
            Locator(
                By.CSS_SELECTOR,
                "button[id*='renew']",
                "Plan renewal button (id contains renew)",
            ),
            Locator(
                By.CSS_SELECTOR,
                "button[onclick*='renew']",
                "Plan renewal button (onclick contains renew)",
            ),
            Locator(
                By.XPATH,
                "//button[contains(text(), 'Renew') or contains(text(), 'RENEW')]",
                "Plan renewal button (text contains renew)",
            ),
            Locator(By.CSS_SELECTOR, "a[href*='renew']", "Plan renewal link"),
        ],
    )

    # Balance related elements - with fallback strategies
    BALANCE_PACK_CARDS = Locator(
        By.CSS_SELECTOR,
        ".pack_card",
        "Balance pack cards container",
        fallbacks=[
            Locator(By.CSS_SELECTOR, "div.pack_card", "Balance pack cards (div)")
        ],
    )

    BALANCE_DETAILS = Locator(
        By.CSS_SELECTOR,
        ".balance-details",
        "Balance details elements",
        fallbacks=[
            Locator(By.CSS_SELECTOR, "div.balance-details", "Balance details (div)"),
            Locator(
                By.CSS_SELECTOR,
                "[class*='balance-detail']",
                "Balance details (partial class)",
            ),
            Locator(
                By.CSS_SELECTOR,
                "[class*='balance']",
                "Balance elements (partial class)",
            ),
            Locator(By.CSS_SELECTOR, ".pack_card div", "Pack card child divs"),
            Locator(
                By.XPATH,
                "//div[contains(@class, 'balance')]",
                "Balance elements (xpath)",
            ),
            Locator(
                By.XPATH,
                "//div[contains(text(), 'GB') or contains(text(), 'minutes') or contains(text(), 'text')]",
                "Usage elements by text content",
            ),
        ],
    )

    # Plan information elements
    PLAN_DATA = Locator(
        By.CSS_SELECTOR, "div.subtitle > div.subtitle_heading", "Plan data amount"
    )

    PLAN_MINUTES = Locator(
        By.CSS_SELECTOR, "div.subtitle > div:nth-child(4)", "Plan minutes amount"
    )

    PLAN_TEXTS = Locator(
        By.CSS_SELECTOR, "div.subtitle > div:nth-child(5)", "Plan texts amount"
    )

    # Renewal page elements
    CARD_EXPIRY_MONTH = Locator(
        By.CSS_SELECTOR, "select#cc_expiry_month", "Credit card expiry month selector"
    )

    CARD_EXPIRY_YEAR = Locator(
        By.CSS_SELECTOR, "select#cc_expiry_year", "Credit card expiry year selector"
    )

    NOTIFICATION_CHECKBOX = Locator(
        By.CSS_SELECTOR,
        "input[type=checkbox][name=recurring_charge_notification]",
        "Recurring charge notification checkbox",
    )

    FINALIZE_ORDER_BUTTON = Locator(
        By.CSS_SELECTOR, "button#checkout_form_submit_holder", "Finalize order button"
    )

    @classmethod
    def get_all_locators(cls) -> list[Locator]:
        """Get all defined locators.

        Returns:
            List of all Locator instances defined in this class
        """
        locators: list[Any] = []
        for attr_name in dir(cls):
            if not attr_name.startswith("_") and attr_name != "get_all_locators":
                attr_value = getattr(cls, attr_name)
                if isinstance(attr_value, Locator):
                    locators.append(attr_value)
        return locators

    @classmethod
    def validate_all_locators(cls) -> bool:
        """Validate all locators are properly defined.

        Returns:
            True if all locators are valid

        Raises:
            ValueError: If any locator is invalid
        """
        locators = cls.get_all_locators()
        for locator in locators:
            if not locator.by or not locator.value or not locator.description:
                raise ValueError(f"Invalid locator: {locator}")
        return True

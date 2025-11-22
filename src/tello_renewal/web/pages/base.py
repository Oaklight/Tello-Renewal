"""Base page class for Page Object Model implementation.

This module provides the foundation for all page classes with common
functionality like element waiting, clicking strategies, and error handling.
"""

import time

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ...utils.exceptions import ElementNotFoundError, PageLoadError
from ...utils.logging import get_logger
from ..elements.locators import Locator

logger = get_logger(__name__)


class BasePage:
    """Base page class providing common functionality for all pages."""

    def __init__(self, driver: WebDriver, timeout: int = 30):
        """Initialize base page.

        Args:
            driver: WebDriver instance
            timeout: Default timeout for element operations
        """
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def wait_for_element(
        self, locator: Locator, timeout: int | None = None
    ) -> WebElement:
        """Wait for element to be present and return it.

        Args:
            locator: Element locator
            timeout: Custom timeout (uses default if None)

        Returns:
            WebElement when found

        Raises:
            ElementNotFoundError: If element is not found within timeout
        """
        wait_timeout = timeout or self.timeout

        try:
            # Try primary locator first
            element = WebDriverWait(self.driver, wait_timeout).until(
                EC.presence_of_element_located((locator.by, locator.value))
            )
            logger.debug(f"Found element: {locator.description}")
            return element
        except Exception as primary_error:
            logger.debug(
                f"Primary locator failed for {locator.description}: {primary_error}"
            )

            # Try fallback locators if available
            for fallback in locator.fallbacks:
                try:
                    element = WebDriverWait(self.driver, wait_timeout).until(
                        EC.presence_of_element_located((fallback.by, fallback.value))
                    )
                    logger.info(f"Found element using fallback: {fallback.description}")
                    return element
                except Exception as fallback_error:
                    logger.debug(
                        f"Fallback locator failed for {fallback.description}: {fallback_error}"
                    )
                    continue

            # All locators failed
            raise ElementNotFoundError(
                f"Element not found: {locator.description} "
                f"(tried {1 + len(locator.fallbacks)} locators)"
            ) from None

    def wait_for_clickable(
        self, locator: Locator, timeout: int | None = None
    ) -> WebElement:
        """Wait for element to be clickable and return it.

        Args:
            locator: Element locator
            timeout: Custom timeout (uses default if None)

        Returns:
            WebElement when clickable

        Raises:
            ElementNotFoundError: If element is not clickable within timeout
        """
        wait_timeout = timeout or self.timeout

        try:
            element = WebDriverWait(self.driver, wait_timeout).until(
                EC.element_to_be_clickable((locator.by, locator.value))
            )
            logger.debug(f"Element is clickable: {locator.description}")
            return element
        except Exception as e:
            raise ElementNotFoundError(
                f"Element not clickable: {locator.description}"
            ) from e

    def click_with_strategies(self, locator: Locator) -> bool:
        """Click element using multiple strategies for reliability.

        Args:
            locator: Element locator

        Returns:
            True if click was successful

        Raises:
            ElementNotFoundError: If element cannot be clicked
        """
        element = self.wait_for_element(locator)

        # Strategy 1: Regular click
        try:
            element.click()
            logger.debug(f"Clicked element using regular click: {locator.description}")
            return True
        except Exception as click_error:
            logger.debug(
                f"Regular click failed for {locator.description}: {click_error}"
            )

        # Strategy 2: JavaScript click
        try:
            self.driver.execute_script("arguments[0].click();", element)
            logger.debug(f"Clicked element using JavaScript: {locator.description}")
            return True
        except Exception as js_error:
            logger.debug(
                f"JavaScript click failed for {locator.description}: {js_error}"
            )

        # Strategy 3: Scroll into view and click
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)  # Wait for scroll to complete
            element.click()
            logger.debug(f"Clicked element after scrolling: {locator.description}")
            return True
        except Exception as scroll_error:
            logger.debug(
                f"Scroll and click failed for {locator.description}: {scroll_error}"
            )

        # Strategy 4: JavaScript click after scroll
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", element)
            logger.info(
                f"Clicked element using JavaScript after scroll: {locator.description}"
            )
            return True
        except Exception as final_error:
            logger.error(
                f"All click strategies failed for {locator.description}: {final_error}"
            )

        raise ElementNotFoundError(f"Failed to click element: {locator.description}")

    def get_text_safe(self, locator: Locator) -> str:
        """Safely get text from element.

        Args:
            locator: Element locator

        Returns:
            Element text content, empty string if not found

        Raises:
            ElementNotFoundError: If element is not found
        """
        try:
            element = self.wait_for_element(locator)
            text = element.text.strip()
            logger.debug(f"Got text from {locator.description}: '{text}'")
            return text
        except Exception as e:
            raise ElementNotFoundError(
                f"Failed to get text from {locator.description}"
            ) from e

    def is_element_present(self, locator: Locator, timeout: int = 5) -> bool:
        """Check if element is present on page.

        Args:
            locator: Element locator
            timeout: Timeout for check

        Returns:
            True if element is present, False otherwise
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator.by, locator.value))
            )
            return True
        except Exception:
            return False

    def navigate_to(self, url: str) -> None:
        """Navigate to specified URL.

        Args:
            url: URL to navigate to

        Raises:
            PageLoadError: If navigation fails
        """
        try:
            self.driver.get(url)
            logger.info(f"Navigated to: {url}")
        except Exception as e:
            raise PageLoadError(f"Failed to navigate to {url}") from e

    def get_current_url(self) -> str:
        """Get current page URL.

        Returns:
            Current URL
        """
        return self.driver.current_url

    def get_page_title(self) -> str:
        """Get current page title.

        Returns:
            Page title
        """
        return self.driver.title

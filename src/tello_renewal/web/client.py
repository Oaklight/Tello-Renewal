"""Web client for Tello automation using Page Object Model.

This module provides a high-level interface for web automation
using the Page Object Model pattern with centralized driver management.
"""

from datetime import date
from types import TracebackType
from typing import Optional

from selenium.webdriver.remote.webdriver import WebDriver

from ..core.models import AccountBalance
from ..utils.config import BrowserConfig
from ..utils.exceptions import WebDriverError
from ..utils.logging import get_logger

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

from .driver import BrowserDriverManager
from .pages import DashboardPage, LoginPage, RenewalPage

logger = get_logger(__name__)


class TelloWebClient:
    """High-level web client for Tello automation using Page Object Model."""

    def __init__(self, browser_config: BrowserConfig, dry_run: bool = False):
        """Initialize web client.

        Args:
            browser_config: Browser configuration
            dry_run: If True, don't perform actual renewal submission
        """
        self.config = browser_config
        self.dry_run = dry_run
        self._driver: Optional[WebDriver] = None
        self._driver_manager = BrowserDriverManager(browser_config)

        # Page objects - initialized when driver is available
        self._login_page: Optional[LoginPage] = None
        self._dashboard_page: Optional[DashboardPage] = None
        self._renewal_page: Optional[RenewalPage] = None

    def __enter__(self) -> Self:
        """Context manager entry - initialize browser and pages."""
        self._initialize_driver()
        self._initialize_pages()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Context manager exit - cleanup browser."""
        self._cleanup_driver()

    def _initialize_driver(self) -> None:
        """Initialize the web driver."""
        try:
            self._driver = self._driver_manager.create_driver()
            logger.info("Web driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize web driver: {e}")
            raise WebDriverError(f"Failed to initialize browser: {e}")

    def _initialize_pages(self) -> None:
        """Initialize page objects."""
        if self._driver is None:
            raise WebDriverError("Driver not initialized")

        self._login_page = LoginPage(self._driver)
        self._dashboard_page = DashboardPage(self._driver)
        self._renewal_page = RenewalPage(self._driver)

        logger.debug("Page objects initialized")

    def _cleanup_driver(self) -> None:
        """Clean up the web driver."""
        if self._driver:
            try:
                self._driver.quit()
                logger.debug("Web driver cleaned up successfully")
            except Exception as e:
                logger.warning(f"Error cleaning up web driver: {e}")
            finally:
                self._driver = None
                self._login_page = None
                self._dashboard_page = None
                self._renewal_page = None

    @property
    def login_page(self) -> LoginPage:
        """Get login page object."""
        if self._login_page is None:
            raise WebDriverError("Login page not initialized")
        return self._login_page

    @property
    def dashboard_page(self) -> DashboardPage:
        """Get dashboard page object."""
        if self._dashboard_page is None:
            raise WebDriverError("Dashboard page not initialized")
        return self._dashboard_page

    @property
    def renewal_page(self) -> RenewalPage:
        """Get renewal page object."""
        if self._renewal_page is None:
            raise WebDriverError("Renewal page not initialized")
        return self._renewal_page

    # High-level operations that delegate to page objects

    def open_login_page(self, base_url: str) -> None:
        """Navigate to Tello login page.

        Args:
            base_url: Tello base URL
        """
        self.login_page.navigate_to_login(base_url)

    def login(self, email: str, password: str) -> None:
        """Login to Tello account.

        Args:
            email: Account email
            password: Account password
        """
        self.login_page.login(email, password)

    def get_renewal_date(self) -> date:
        """Extract renewal date from account page.

        Returns:
            Next renewal date
        """
        return self.dashboard_page.get_renewal_date()

    def get_current_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            Current account balance
        """
        return self.dashboard_page.get_current_balance()

    def get_plan_balance(self) -> AccountBalance:
        """Get plan balance information.

        Returns:
            Plan balance that will be added upon renewal
        """
        return self.dashboard_page.get_plan_balance()

    def open_renewal_page(self) -> None:
        """Navigate to renewal page by clicking renew button."""
        self.dashboard_page.click_renew_button()

    def fill_card_expiration(self, expiration_date: date) -> None:
        """Fill credit card expiration date on renewal form.

        Args:
            expiration_date: Card expiration date
        """
        self.renewal_page.fill_card_expiration(expiration_date)

    def check_notification_checkbox(self) -> None:
        """Check the recurring charge notification checkbox."""
        self.renewal_page.check_notification_checkbox()

    def submit_renewal(self) -> bool:
        """Submit the renewal order.

        Returns:
            True if submission was successful (or skipped in dry run)
        """
        return self.renewal_page.submit_renewal(self.dry_run)

    def complete_renewal_process(self, expiration_date: date) -> bool:
        """Complete the entire renewal process.

        Args:
            expiration_date: Card expiration date

        Returns:
            True if renewal process completed successfully
        """
        return self.renewal_page.complete_renewal_process(expiration_date, self.dry_run)

    # Utility methods

    def is_logged_in(self) -> bool:
        """Check if user is currently logged in.

        Returns:
            True if logged in, False otherwise
        """
        return self.login_page.is_logged_in()

    def get_current_url(self) -> str:
        """Get current page URL.

        Returns:
            Current URL
        """
        if self._driver is None:
            raise WebDriverError("Driver not initialized")
        return self._driver.current_url

    def get_page_title(self) -> str:
        """Get current page title.

        Returns:
            Page title
        """
        if self._driver is None:
            raise WebDriverError("Driver not initialized")
        return self._driver.title

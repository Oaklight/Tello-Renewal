"""Main renewal engine for Tello plan automation.

This module contains the core renewal logic, including web automation
for interacting with the Tello website and orchestrating the renewal process.
"""

import time
from datetime import date, datetime
from types import TracebackType
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from typing_extensions import Self
else:
    try:
        from typing import Self
    except ImportError:
        from typing_extensions import Self

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from ..utils.config import BrowserConfig, Config
from ..utils.logging import get_logger, log_duration, log_function_call
from .models import (
    AccountBalance,
    AccountSummary,
    BalanceQuantity,
    RenewalResult,
    RenewalStatus,
)

logger = get_logger(__name__)


class TelloWebError(Exception):
    """Base exception for Tello web automation errors."""

    pass


class LoginFailedError(TelloWebError):
    """Failed to login to Tello account."""

    pass


class ElementNotFoundError(TelloWebError):
    """Required web element not found."""

    pass


class RenewalPageError(TelloWebError):
    """Error on renewal page."""

    pass


class TelloWebClient:
    """Web automation client for Tello website using Selenium."""

    def __init__(self, browser_config: BrowserConfig, dry_run: bool = False):
        """Initialize web client.

        Args:
            browser_config: Browser configuration
            dry_run: If True, don't perform actual renewal submission
        """
        self.config = browser_config
        self.dry_run = dry_run
        self._driver: Optional[webdriver.Remote] = None

    def __enter__(self) -> Self:
        """Context manager entry - initialize browser."""
        self._initialize_driver()
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
        """Initialize the web driver based on configuration."""
        log_function_call(
            "_initialize_driver",
            browser_type=self.config.browser_type,
            headless=self.config.headless,
        )

        try:
            if self.config.browser_type == "firefox":
                options = FirefoxOptions()
                if self.config.headless:
                    options.add_argument("--headless")

                # Add container environment necessary parameters
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-setuid-sandbox")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-plugins")

                options.add_argument(f"--width={self.config.window_size.split('x')[0]}")
                options.add_argument(
                    f"--height={self.config.window_size.split('x')[1]}"
                )

                # Configure proxy if specified
                if self.config.proxy_server:
                    proxy_url = self.config.proxy_server
                    logger.info(f"Configuring Firefox with proxy: {proxy_url}")

                    # Set proxy preferences using Firefox profile
                    profile = webdriver.FirefoxProfile()

                    if self.config.proxy_type.lower() == "socks5":
                        profile.set_preference("network.proxy.type", 1)
                        proxy_parts = proxy_url.replace("socks5://", "").split(":")
                        if len(proxy_parts) >= 2:
                            profile.set_preference(
                                "network.proxy.socks", proxy_parts[0]
                            )
                            profile.set_preference(
                                "network.proxy.socks_port", int(proxy_parts[1])
                            )
                            profile.set_preference("network.proxy.socks_version", 5)
                    else:
                        # HTTP/HTTPS proxy
                        profile.set_preference("network.proxy.type", 1)
                        proxy_parts = (
                            proxy_url.replace("http://", "")
                            .replace("https://", "")
                            .split(":")
                        )
                        if len(proxy_parts) >= 2:
                            profile.set_preference("network.proxy.http", proxy_parts[0])
                            profile.set_preference(
                                "network.proxy.http_port", int(proxy_parts[1])
                            )
                            profile.set_preference("network.proxy.ssl", proxy_parts[0])
                            profile.set_preference(
                                "network.proxy.ssl_port", int(proxy_parts[1])
                            )

                    profile.update_preferences()
                    options.profile = profile

                self._driver = webdriver.Firefox(options=options)

            elif self.config.browser_type == "chrome":
                options = ChromeOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                options.add_argument(f"--window-size={self.config.window_size}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

                # Configure proxy if specified
                if self.config.proxy_server:
                    proxy_url = self.config.proxy_server
                    logger.info(f"Configuring Chrome with proxy: {proxy_url}")
                    options.add_argument(f"--proxy-server={proxy_url}")

                self._driver = webdriver.Chrome(options=options)

            elif self.config.browser_type == "edge":
                options = EdgeOptions()
                if self.config.headless:
                    options.add_argument("--headless")
                options.add_argument(f"--window-size={self.config.window_size}")

                # Configure proxy if specified
                if self.config.proxy_server:
                    proxy_url = self.config.proxy_server
                    logger.info(f"Configuring Edge with proxy: {proxy_url}")
                    options.add_argument(f"--proxy-server={proxy_url}")

                self._driver = webdriver.Edge(options=options)

            else:
                raise ValueError(
                    f"Unsupported browser type: {self.config.browser_type}"
                )

            # Set timeouts
            self._driver.implicitly_wait(self.config.implicit_wait)
            self._driver.set_page_load_timeout(self.config.page_load_timeout)

            logger.info(f"Initialized {self.config.browser_type} driver successfully")

        except Exception as e:
            logger.error(f"Failed to initialize web driver: {e}")
            raise TelloWebError(f"Failed to initialize browser: {e}")

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

    def _wait_for_element(self, by: str, value: str, timeout: int = 30) -> WebElement:
        """Wait for element to be present and return it.

        Args:
            by: Selenium By locator type
            value: Locator value
            timeout: Timeout in seconds

        Returns:
            WebElement when found

        Raises:
            ElementNotFoundError: If element is not found within timeout
        """
        if self._driver is None:
            raise ElementNotFoundError("Driver not initialized")

        try:
            element = WebDriverWait(self._driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            raise ElementNotFoundError(f"Element not found: {by}='{value}' - {e}")

    def open_login_page(self, base_url: str) -> None:
        """Navigate to Tello login page.

        Args:
            base_url: Tello base URL
        """
        login_url = f"{base_url.rstrip('/')}/account/login"
        log_function_call("open_login_page", url=login_url)

        if self._driver is None:
            raise TelloWebError("Driver not initialized")

        try:
            self._driver.get(login_url)
            logger.info(f"Opened login page: {login_url}")
        except Exception as e:
            raise TelloWebError(f"Failed to open login page: {e}")

    def login(self, email: str, password: str) -> None:
        """Login to Tello account.

        Args:
            email: Account email
            password: Account password

        Raises:
            LoginFailedError: If login fails
        """
        log_function_call("login", email=email, password="***")

        try:
            # Find and fill email field
            email_input = self._wait_for_element(By.CSS_SELECTOR, "input#i_username")
            email_input.clear()
            email_input.send_keys(email)

            # Find and fill password field
            password_input = self._wait_for_element(
                By.CSS_SELECTOR, "input#i_current_password"
            )
            password_input.clear()
            password_input.send_keys(password)

            # Submit form
            email_input.send_keys(Keys.ENTER)

            # Wait for login to complete - look for account page elements
            try:
                self._wait_for_element(
                    By.CSS_SELECTOR, "span.card_text > span", timeout=15
                )
                logger.info("Login successful")
            except ElementNotFoundError:
                raise LoginFailedError(
                    "Login failed - could not find account page elements"
                )

        except ElementNotFoundError as e:
            raise LoginFailedError(f"Login failed - login form elements not found: {e}")
        except Exception as e:
            raise LoginFailedError(f"Login failed: {e}")

    def get_renewal_date(self) -> date:
        """Extract renewal date from account page.

        Returns:
            Next renewal date

        Raises:
            ElementNotFoundError: If renewal date element not found
        """
        try:
            renewal_element = self._wait_for_element(
                By.CSS_SELECTOR, "span.card_text > span"
            )
            date_text = renewal_element.text.strip()

            # Parse date in MM/DD/YYYY format
            renewal_date = datetime.strptime(date_text, "%m/%d/%Y").date()
            logger.info(f"Found renewal date: {renewal_date}")
            return renewal_date

        except ValueError as e:
            # date_text is guaranteed to be defined here since we're in the try block
            date_text_safe = locals().get("date_text", "unknown")
            raise TelloWebError(f"Failed to parse renewal date '{date_text_safe}': {e}")
        except Exception as e:
            raise ElementNotFoundError(f"Failed to get renewal date: {e}")

    def get_current_balance(self) -> AccountBalance:
        """Get current account balance.

        Returns:
            Current account balance

        Raises:
            ElementNotFoundError: If balance elements not found
        """
        if self._driver is None:
            raise ElementNotFoundError("Driver not initialized")

        try:
            # First try to get account balance from pack_card (new structure)
            try:
                # Look for the pack_card that contains "Remaining balance"
                pack_cards = self._driver.find_elements(By.CSS_SELECTOR, ".pack_card")
                account_balance_amount = None

                for card in pack_cards:
                    card_text = card.text
                    if "Remaining balance" in card_text:
                        logger.debug(f"Found balance card text: {card_text}")
                        # Extract balance amount using regex - handle Unicode directional marks
                        import re

                        balance_match = re.search(
                            r"[⁦]?\$(\d+(?:\.\d{2})?)[⁩]?", card_text
                        )
                        if balance_match:
                            account_balance_amount = float(balance_match.group(1))
                            logger.info(
                                f"Successfully extracted account balance: ${account_balance_amount}"
                            )
                            break

                if account_balance_amount is not None:
                    # Now get usage data from balance-details elements
                    balance_details = self._driver.find_elements(
                        By.CSS_SELECTOR, ".balance-details"
                    )

                    if len(balance_details) >= 2:
                        # First balance-details is data usage
                        data_text = balance_details[0].text
                        logger.debug(f"Data balance text: {data_text}")

                        # Second balance-details is minutes usage
                        minutes_text = balance_details[1].text
                        logger.debug(f"Minutes balance text: {minutes_text}")

                        # For texts, check if there's a third balance-details or assume unlimited
                        if len(balance_details) >= 3:
                            texts_text = balance_details[2].text
                            logger.debug(f"Texts balance text: {texts_text}")
                        else:
                            # Most Tello plans have unlimited texts
                            texts_text = "unlimited texts"
                            logger.debug(
                                "No texts balance found, assuming unlimited texts"
                            )

                        balance = AccountBalance(
                            data=BalanceQuantity.from_tello(data_text),
                            minutes=BalanceQuantity.from_tello(minutes_text),
                            texts=BalanceQuantity.from_tello(texts_text),
                        )

                        logger.info(
                            f"Current balance: {balance} (using new pack_card structure)"
                        )
                        return balance
                    else:
                        logger.debug(
                            f"Found balance amount but insufficient balance-details elements: {len(balance_details)}"
                        )

            except Exception as e:
                logger.debug(f"New structure parsing failed: {e}")

            # If new structure failed, raise error immediately to avoid long waits
            logger.error(
                "New balance structure parsing failed, website structure may have changed"
            )
            raise ElementNotFoundError(
                "Could not find balance elements with new website structure. Website may have been updated."
            )

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
            plan_data_element = self._wait_for_element(
                By.CSS_SELECTOR, "div.subtitle > div.subtitle_heading"
            )
            plan_data = BalanceQuantity.from_tello(plan_data_element.text)

            # Get plan minutes
            plan_minutes_element = self._wait_for_element(
                By.CSS_SELECTOR, "div.subtitle > div:nth-child(4)"
            )
            plan_minutes = BalanceQuantity.from_tello(plan_minutes_element.text)

            # Get plan texts
            plan_texts_element = self._wait_for_element(
                By.CSS_SELECTOR, "div.subtitle > div:nth-child(5)"
            )
            plan_texts = BalanceQuantity.from_tello(plan_texts_element.text)

            balance = AccountBalance(
                data=plan_data,
                minutes=plan_minutes,
                texts=plan_texts,
            )

            logger.info(f"Plan balance: {balance}")
            return balance

        except Exception as e:
            raise ElementNotFoundError(f"Failed to get plan balance: {e}")

    def open_renewal_page(self) -> None:
        """Navigate to renewal page by clicking renew button.

        Raises:
            ElementNotFoundError: If renew button not found
        """
        try:
            renew_button = self._wait_for_element(By.CSS_SELECTOR, "button#renew_plan")

            # Try multiple click strategies to handle element interception
            try:
                # First try regular click
                renew_button.click()
                logger.info("Clicked renew button using regular click")
            except Exception as click_error:
                logger.debug(f"Regular click failed: {click_error}")
                try:
                    # Try JavaScript click if regular click fails
                    self._driver.execute_script("arguments[0].click();", renew_button)
                    logger.info("Clicked renew button using JavaScript click")
                except Exception as js_error:
                    logger.debug(f"JavaScript click failed: {js_error}")
                    try:
                        # Try scrolling into view and then clicking
                        self._driver.execute_script(
                            "arguments[0].scrollIntoView(true);", renew_button
                        )
                        time.sleep(1)  # Wait for scroll to complete
                        renew_button.click()
                        logger.info("Clicked renew button after scrolling into view")
                    except Exception as scroll_error:
                        logger.debug(f"Scroll and click failed: {scroll_error}")
                        # Final attempt: JavaScript click after scroll
                        self._driver.execute_script(
                            "arguments[0].scrollIntoView(true);", renew_button
                        )
                        time.sleep(1)
                        self._driver.execute_script(
                            "arguments[0].click();", renew_button
                        )
                        logger.info(
                            "Clicked renew button using JavaScript after scroll"
                        )

            # Wait for renewal page to load
            time.sleep(3)

        except Exception as e:
            raise ElementNotFoundError(f"Failed to open renewal page: {e}")

    def fill_card_expiration(self, expiration_date: date) -> None:
        """Fill credit card expiration date on renewal form.

        Args:
            expiration_date: Card expiration date

        Raises:
            RenewalPageError: If form elements not found or filling fails
        """
        log_function_call("fill_card_expiration", expiration_date=expiration_date)

        try:
            # Fill expiration month
            month_select = Select(
                self._wait_for_element(By.CSS_SELECTOR, "select#cc_expiry_month")
            )
            month_select.select_by_value(str(expiration_date.month))

            # Fill expiration year
            year_select = Select(
                self._wait_for_element(By.CSS_SELECTOR, "select#cc_expiry_year")
            )
            year_select.select_by_value(str(expiration_date.year))

            logger.info(
                f"Filled card expiration: {expiration_date.month}/{expiration_date.year}"
            )

        except Exception as e:
            raise RenewalPageError(f"Failed to fill card expiration: {e}")

    def check_notification_checkbox(self) -> None:
        """Check the recurring charge notification checkbox.

        Raises:
            RenewalPageError: If checkbox not found
        """
        try:
            checkbox = self._wait_for_element(
                By.CSS_SELECTOR,
                "input[type=checkbox][name=recurring_charge_notification]",
            )
            if not checkbox.is_selected():
                checkbox.click()
                logger.info("Checked notification checkbox")
            else:
                logger.info("Notification checkbox already checked")

        except Exception as e:
            raise RenewalPageError(f"Failed to check notification checkbox: {e}")

    def submit_renewal(self) -> bool:
        """Submit the renewal order.

        Returns:
            True if submission was successful (or skipped in dry run)

        Raises:
            RenewalPageError: If submission fails
        """
        try:
            finalize_button = self._wait_for_element(
                By.CSS_SELECTOR, "button#checkout_form_submit_holder"
            )

            if self.dry_run:
                button_text = finalize_button.text
                if "Finalize Order" in button_text:
                    logger.info(
                        f"DRY RUN: Found finalize order button '{button_text}', skipping click"
                    )
                    return True
                else:
                    raise RenewalPageError(
                        f"Expected 'Finalize Order' button, found: '{button_text}'"
                    )
            else:
                finalize_button.click()
                logger.info("Clicked finalize order button")

                # Wait a bit for processing
                time.sleep(5)
                return True

        except Exception as e:
            raise RenewalPageError(f"Failed to submit renewal: {e}")


class RenewalEngine:
    """Main renewal logic and orchestration."""

    def __init__(self, config: Config, dry_run: bool = False):
        """Initialize renewal engine.

        Args:
            config: Application configuration
            dry_run: If True, don't perform actual renewal
        """
        self.config = config
        self.dry_run = dry_run or config.renewal.dry_run
        self._web_client: Optional[TelloWebClient] = None

    def check_renewal_needed(self, renewal_date: date) -> bool:
        """Check if renewal is needed based on date.

        Args:
            renewal_date: The renewal due date

        Returns:
            True if renewal should be performed
        """
        today = date.today()
        days_until = (renewal_date - today).days

        logger.info(f"Renewal date: {renewal_date}, Days until renewal: {days_until}")

        if days_until <= self.config.renewal.days_before_renewal:
            logger.info("Renewal is due")
            return True
        else:
            logger.info(f"Renewal not due yet ({days_until} days remaining)")
            return False

    def get_account_summary(self) -> AccountSummary:
        """Get current account status and balance.

        Returns:
            Complete account summary

        Raises:
            TelloWebError: If web automation fails
        """
        start_time = time.time()

        try:
            with TelloWebClient(self.config.browser, dry_run=True) as client:
                client.open_login_page(self.config.tello.base_url)
                client.login(self.config.tello.email, self.config.tello.password)

                renewal_date = client.get_renewal_date()
                current_balance = client.get_current_balance()
                plan_balance = client.get_plan_balance()

                days_until = (renewal_date - date.today()).days

                summary = AccountSummary(
                    email=self.config.tello.email,
                    renewal_date=renewal_date,
                    current_balance=current_balance,
                    plan_balance=plan_balance,
                    days_until_renewal=days_until,
                )

                duration = time.time() - start_time
                log_duration("get_account_summary", duration)

                return summary

        except Exception as e:
            logger.error(f"Failed to get account summary: {e}")
            raise

    def execute_renewal(self) -> RenewalResult:
        """Execute the complete renewal process.

        Returns:
            Result of the renewal operation
        """
        start_time = time.time()
        timestamp = datetime.now()

        logger.info(f"Starting renewal process (dry_run={self.dry_run})")

        try:
            with TelloWebClient(self.config.browser, self.dry_run) as client:
                # Login and get account info
                client.open_login_page(self.config.tello.base_url)
                client.login(self.config.tello.email, self.config.tello.password)

                renewal_date = client.get_renewal_date()

                # Check if renewal is needed
                if not self.check_renewal_needed(renewal_date):
                    days_until = (renewal_date - date.today()).days
                    message = f"Renewal not due yet. {days_until} days remaining until {renewal_date}"

                    if self.dry_run:
                        message += " (dry run mode - aborting)"

                    logger.info(message)
                    duration = time.time() - start_time
                    return RenewalResult(
                        status=RenewalStatus.NOT_DUE,
                        timestamp=timestamp,
                        message=message,
                        duration_seconds=duration,
                    )

                # Get balances
                current_balance = client.get_current_balance()
                plan_balance = client.get_plan_balance()
                new_balance = current_balance + plan_balance

                logger.info(f"Current balance: {current_balance}")
                logger.info(f"Plan balance: {plan_balance}")
                logger.info(f"New balance after renewal: {new_balance}")

                # Perform renewal
                client.open_renewal_page()
                client.fill_card_expiration(self.config.tello.card_expiration)
                client.check_notification_checkbox()

                success = client.submit_renewal()

                duration = time.time() - start_time

                if success:
                    status = RenewalStatus.SUCCESS
                    message = "Renewal completed successfully"
                    if self.dry_run:
                        message += " (dry run)"

                    logger.info(message)

                    return RenewalResult(
                        status=status,
                        timestamp=timestamp,
                        message=message,
                        new_balance=new_balance,
                        duration_seconds=duration,
                    )
                else:
                    raise TelloWebError("Renewal submission failed")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Renewal failed: {error_msg}")

            return RenewalResult(
                status=RenewalStatus.FAILED,
                timestamp=timestamp,
                message="Renewal failed",
                error=error_msg,
                duration_seconds=duration,
            )

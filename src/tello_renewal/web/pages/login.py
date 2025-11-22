"""Login page implementation for Tello website.

This module provides login functionality using the Page Object Model pattern.
"""

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webdriver import WebDriver

from ...utils.exceptions import LoginError
from ...utils.logging import get_logger, log_function_call
from ..elements.locators import TelloLocators
from .base import BasePage

logger = get_logger(__name__)


class LoginPage(BasePage):
    """Login page for Tello website."""

    def __init__(self, driver: WebDriver, timeout: int = 30):
        """Initialize login page.

        Args:
            driver: WebDriver instance
            timeout: Default timeout for operations
        """
        super().__init__(driver, timeout)

    def navigate_to_login(self, base_url: str) -> None:
        """Navigate to Tello login page.

        Args:
            base_url: Tello base URL

        Raises:
            LoginError: If navigation fails
        """
        login_url = f"{base_url.rstrip('/')}/account/login"
        log_function_call("navigate_to_login", url=login_url)

        try:
            self.navigate_to(login_url)
            logger.info(f"Opened login page: {login_url}")
        except Exception as e:
            raise LoginError("Failed to open login page") from e

    def enter_credentials(self, email: str, password: str) -> None:
        """Enter login credentials.

        Args:
            email: Account email
            password: Account password

        Raises:
            LoginError: If credential entry fails
        """
        log_function_call("enter_credentials", email=email, password="***")

        try:
            # Find and fill email field
            email_element = self.wait_for_element(TelloLocators.LOGIN_EMAIL)
            email_element.clear()
            email_element.send_keys(email)
            logger.debug("Email entered successfully")

            # Find and fill password field
            password_element = self.wait_for_element(TelloLocators.LOGIN_PASSWORD)
            password_element.clear()
            password_element.send_keys(password)
            logger.debug("Password entered successfully")

        except Exception as e:
            raise LoginError(f"Failed to enter credentials") from e

    def submit_login(self) -> None:
        """Submit the login form.

        Raises:
            LoginError: If form submission fails
        """
        try:
            # Submit form by pressing Enter on email field
            email_element = self.wait_for_element(TelloLocators.LOGIN_EMAIL)
            email_element.send_keys(Keys.ENTER)
            logger.debug("Login form submitted")

        except Exception as e:
            raise LoginError("Failed to submit login form") from e

    def wait_for_login_success(self, timeout: int = 15) -> bool:
        """Wait for login to complete successfully.

        Args:
            timeout: Timeout for waiting

        Returns:
            True if login was successful

        Raises:
            LoginError: If login fails or times out
        """
        try:
            # Wait for account page elements to appear (indicates successful login)
            self.wait_for_element(TelloLocators.RENEWAL_DATE, timeout=timeout)
            logger.info("Login successful - account page loaded")
            return True

        except Exception as e:
            raise LoginError(
                "Login failed - could not find account page elements"
            ) from e

    def login(self, email: str, password: str) -> None:
        """Complete login process.

        Args:
            email: Account email
            password: Account password

        Raises:
            LoginError: If any step of login fails
        """
        log_function_call("login", email=email, password="***")

        try:
            self.enter_credentials(email, password)
            self.submit_login()
            self.wait_for_login_success()
            logger.info("Login completed successfully")

        except LoginError:
            raise
        except Exception as e:
            raise LoginError("Login failed") from e

    def is_logged_in(self) -> bool:
        """Check if user is currently logged in.

        Returns:
            True if logged in, False otherwise
        """
        try:
            # Check for presence of account page elements
            return self.is_element_present(TelloLocators.RENEWAL_DATE, timeout=5)
        except Exception:
            return False

    def get_login_error_message(self) -> str:
        """Get login error message if present.

        Returns:
            Error message text, empty string if no error
        """
        # This would need to be implemented based on actual error elements
        # on the Tello login page - placeholder for now
        return ""

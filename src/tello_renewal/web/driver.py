"""Browser driver management for Tello web automation.

This module provides centralized browser driver creation and configuration,
supporting multiple browser types with proxy and headless options.
"""


from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.remote.webdriver import WebDriver

from ..utils.config import BrowserConfig
from ..utils.exceptions import WebDriverError
from ..utils.logging import get_logger, log_function_call

logger = get_logger(__name__)


class BrowserDriverManager:
    """Centralized browser driver management with configuration support."""

    def __init__(self, config: BrowserConfig):
        """Initialize driver manager with browser configuration.

        Args:
            config: Browser configuration settings
        """
        self.config = config

    def create_driver(self) -> WebDriver:
        """Create and configure a web driver instance.

        Returns:
            Configured WebDriver instance

        Raises:
            WebDriverError: If driver creation fails
        """
        log_function_call(
            "create_driver",
            browser_type=self.config.browser_type,
            headless=self.config.headless,
        )

        try:
            if self.config.browser_type == "firefox":
                driver = self._create_firefox_driver()
            elif self.config.browser_type == "chrome":
                driver = self._create_chrome_driver()
            elif self.config.browser_type == "edge":
                driver = self._create_edge_driver()
            else:
                raise WebDriverError(
                    f"Unsupported browser type: {self.config.browser_type}"
                )

            # Configure timeouts
            self._setup_timeouts(driver)

            logger.info(f"Initialized {self.config.browser_type} driver successfully")
            return driver

        except Exception as e:
            logger.error(f"Failed to initialize web driver: {e}")
            raise WebDriverError("Failed to initialize browser") from e

    def _create_firefox_driver(self) -> WebDriver:
        """Create Firefox driver with configuration."""
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

        # Set window size
        width, height = self.config.window_size.split("x")
        options.add_argument(f"--width={width}")
        options.add_argument(f"--height={height}")

        # Configure proxy if specified
        if self.config.proxy_server:
            self._configure_firefox_proxy(options)

        return webdriver.Firefox(options=options)

    def _create_chrome_driver(self) -> WebDriver:
        """Create Chrome driver with configuration."""
        options = ChromeOptions()

        if self.config.headless:
            options.add_argument("--headless")

        options.add_argument(f"--window-size={self.config.window_size}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # Configure proxy if specified
        if self.config.proxy_server:
            self._configure_chrome_proxy(options)

        return webdriver.Chrome(options=options)

    def _create_edge_driver(self) -> WebDriver:
        """Create Edge driver with configuration."""
        options = EdgeOptions()

        if self.config.headless:
            options.add_argument("--headless")

        options.add_argument(f"--window-size={self.config.window_size}")

        # Configure proxy if specified
        if self.config.proxy_server:
            self._configure_edge_proxy(options)

        return webdriver.Edge(options=options)

    def _configure_firefox_proxy(self, options: FirefoxOptions) -> None:
        """Configure Firefox proxy settings."""
        proxy_url = self.config.proxy_server
        logger.info(f"Configuring Firefox with proxy: {proxy_url}")

        # Set proxy preferences using Firefox profile
        profile = webdriver.FirefoxProfile()

        if self.config.proxy_type.lower() == "socks5":
            profile.set_preference("network.proxy.type", 1)
            proxy_parts = proxy_url.replace("socks5://", "").split(":")
            if len(proxy_parts) >= 2:
                profile.set_preference("network.proxy.socks", proxy_parts[0])
                profile.set_preference("network.proxy.socks_port", int(proxy_parts[1]))
                profile.set_preference("network.proxy.socks_version", 5)
        else:
            # HTTP/HTTPS proxy
            profile.set_preference("network.proxy.type", 1)
            proxy_parts = (
                proxy_url.replace("http://", "").replace("https://", "").split(":")
            )
            if len(proxy_parts) >= 2:
                profile.set_preference("network.proxy.http", proxy_parts[0])
                profile.set_preference("network.proxy.http_port", int(proxy_parts[1]))
                profile.set_preference("network.proxy.ssl", proxy_parts[0])
                profile.set_preference("network.proxy.ssl_port", int(proxy_parts[1]))

        profile.update_preferences()
        options.profile = profile

    def _configure_chrome_proxy(self, options: ChromeOptions) -> None:
        """Configure Chrome proxy settings."""
        proxy_url = self.config.proxy_server
        logger.info(f"Configuring Chrome with proxy: {proxy_url}")
        options.add_argument(f"--proxy-server={proxy_url}")

    def _configure_edge_proxy(self, options: EdgeOptions) -> None:
        """Configure Edge proxy settings."""
        proxy_url = self.config.proxy_server
        logger.info(f"Configuring Edge with proxy: {proxy_url}")
        options.add_argument(f"--proxy-server={proxy_url}")

    def _setup_timeouts(self, driver: WebDriver) -> None:
        """Configure driver timeouts."""
        driver.implicitly_wait(self.config.implicit_wait)
        driver.set_page_load_timeout(self.config.page_load_timeout)

"""Configuration management for Tello renewal system.

This module handles loading and validating configuration from TOML files,
with support for environment variable overrides and type validation.
"""

import sys
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Handle tomllib import for different Python versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class TelloConfig(BaseModel):
    """Tello account configuration."""

    email: str = Field(..., description="Tello account email")
    password: str = Field(..., description="Tello account password")
    card_expiration: date = Field(..., description="Credit card expiration date")
    base_url: str = Field(
        default="https://tello.com", description="Tello website base URL"
    )
    login_timeout: int = Field(default=30, description="Login timeout in seconds")

    @field_validator("card_expiration", mode="before")
    @classmethod
    def parse_card_expiration(cls, value) -> date:
        """Parse various card expiration date formats.

        Supports formats like:
        - "1/25", "01/25" (MM/YY)
        - "1/2025", "01/2025" (MM/YYYY)
        - "1-25", "01-25" (MM-YY)
        - "1-2025", "01-2025" (MM-YYYY)
        - "2025-01", "2025-1" (YYYY-MM)
        - "2025-01-01" (YYYY-MM-DD)
        """
        if isinstance(value, date):
            return value

        if not isinstance(value, str):
            raise ValueError(
                f"Card expiration must be a string or date, got {type(value)}"
            )

        import datetime as dt

        formats = [
            "%m/%y",  # 1/25
            "%m-%y",  # 1-25
            "%m/%Y",  # 1/2025
            "%m-%Y",  # 1-2025
            "%m/%d/%y",  # 1/1/25
            "%m-%d-%y",  # 1-1-25
            "%m/%d/%Y",  # 1/1/2025
            "%m-%d-%Y",  # 1-1-2025
            "%Y-%m",  # 2025-1
            "%Y-%m-%d",  # 2025-1-1
        ]

        for fmt in formats:
            try:
                parsed_date = dt.datetime.strptime(value.strip(), fmt).date()
                # For MM/YY and MM-YY formats, set day to last day of month
                if fmt in ("%m/%y", "%m-%y", "%m/%Y", "%m-%Y", "%Y-%m"):
                    # Get last day of the month
                    if parsed_date.month == 12:
                        next_month = parsed_date.replace(
                            year=parsed_date.year + 1, month=1
                        )
                    else:
                        next_month = parsed_date.replace(month=parsed_date.month + 1)
                    last_day = (next_month - dt.timedelta(days=1)).day
                    parsed_date = parsed_date.replace(day=last_day)
                return parsed_date
            except ValueError:
                continue

        raise ValueError(f"Unknown card expiration date format: {value}")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        """Basic email validation."""
        if "@" not in value or "." not in value:
            raise ValueError("Invalid email format")
        return value.strip().lower()


class BrowserConfig(BaseModel):
    """Browser automation configuration."""

    headless: bool = Field(default=True, description="Run browser in headless mode")
    browser_type: str = Field(
        default="firefox", description="Browser type (firefox, chrome, edge)"
    )
    page_load_timeout: int = Field(
        default=30, description="Page load timeout in seconds"
    )
    implicit_wait: int = Field(
        default=10, description="Implicit wait timeout in seconds"
    )
    window_size: str = Field(default="1920x1080", description="Browser window size")

    @field_validator("browser_type")
    @classmethod
    def validate_browser_type(cls, value: str) -> str:
        """Validate browser type."""
        allowed_browsers = {"firefox", "chrome", "edge", "safari"}
        if value.lower() not in allowed_browsers:
            raise ValueError(f"Browser type must be one of: {allowed_browsers}")
        return value.lower()

    @field_validator("window_size")
    @classmethod
    def validate_window_size(cls, value: str) -> str:
        """Validate window size format."""
        try:
            width, height = value.split("x")
            int(width)
            int(height)
            return value
        except (ValueError, AttributeError):
            raise ValueError(
                "Window size must be in format 'WIDTHxHEIGHT' (e.g., '1920x1080')"
            )


class RenewalConfig(BaseModel):
    """Renewal behavior configuration."""

    auto_renew: bool = Field(default=True, description="Enable automatic renewal")
    days_before_renewal: int = Field(
        default=1, description="Days before renewal date to execute"
    )
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay: int = Field(
        default=300, description="Delay between retries in seconds"
    )
    dry_run: bool = Field(default=False, description="Global dry run setting")

    @field_validator("days_before_renewal")
    @classmethod
    def validate_days_before(cls, value: int) -> int:
        """Validate days before renewal."""
        if value < 0 or value > 30:
            raise ValueError("Days before renewal must be between 0 and 30")
        return value

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, value: int) -> int:
        """Validate max retries."""
        if value < 0 or value > 10:
            raise ValueError("Max retries must be between 0 and 10")
        return value


class SmtpConfig(BaseModel):
    """SMTP email configuration."""

    server: str = Field(..., description="SMTP server hostname")
    port: int = Field(default=587, description="SMTP server port")
    username: str = Field(..., description="SMTP username")
    password: str = Field(..., description="SMTP password")
    from_email: str = Field(..., description="From email address")
    use_tls: bool = Field(default=True, description="Use TLS encryption")

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int) -> int:
        """Validate SMTP port."""
        if value < 1 or value > 65535:
            raise ValueError("SMTP port must be between 1 and 65535")
        return value


class NotificationConfig(BaseModel):
    """Notification configuration."""

    email_enabled: bool = Field(default=True, description="Enable email notifications")
    recipients: list[str] = Field(default_factory=list, description="Email recipients")
    send_on_success: bool = Field(
        default=True, description="Send notification on success"
    )
    send_on_failure: bool = Field(
        default=True, description="Send notification on failure"
    )
    send_on_not_due: bool = Field(
        default=False, description="Send notification when not due"
    )


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    format: str = Field(
        default="detailed", description="Log format (simple, detailed, json)"
    )
    file: Optional[str] = Field(default=None, description="Log file path")
    max_size: str = Field(default="10MB", description="Maximum log file size")
    backup_count: int = Field(default=5, description="Number of backup log files")
    console_output: bool = Field(default=True, description="Enable console output")

    @field_validator("level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate log level."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if value.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return value.upper()

    @field_validator("format")
    @classmethod
    def validate_log_format(cls, value: str) -> str:
        """Validate log format."""
        allowed_formats = {"simple", "detailed", "json"}
        if value.lower() not in allowed_formats:
            raise ValueError(f"Log format must be one of: {allowed_formats}")
        return value.lower()


class Config(BaseSettings):
    """Main configuration class."""

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        case_sensitive=False,
        env_prefix="TELLO_",
    )

    tello: TelloConfig
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    renewal: RenewalConfig = Field(default_factory=RenewalConfig)
    smtp: SmtpConfig
    notifications: NotificationConfig = Field(default_factory=NotificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_toml_config(config_path: Path) -> dict:
    """Load configuration from TOML file.

    Args:
        config_path: Path to the TOML configuration file

    Returns:
        Dictionary containing configuration data

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid TOML
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        raise ValueError(f"Invalid TOML configuration file: {e}")


@lru_cache(maxsize=1)
def get_settings(config_path: Optional[str] = None) -> Config:
    """Load and cache configuration settings.

    Args:
        config_path: Path to configuration file (defaults to config.toml)

    Returns:
        Validated configuration object

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If configuration is invalid
    """
    if config_path is None:
        # Look for config file in common locations
        possible_paths = [
            Path("config.toml"),
            Path("config/config.toml"),
            Path("tello_renewal.toml"),
        ]

        config_file = None
        for path in possible_paths:
            if path.exists():
                config_file = path
                break

        if config_file is None:
            raise FileNotFoundError(
                f"No configuration file found. Looked in: {[str(p) for p in possible_paths]}"
            )
    else:
        config_file = Path(config_path)

    config_data = load_toml_config(config_file)

    try:
        return Config(**config_data)
    except Exception as e:
        raise ValueError(f"Invalid configuration: {e}")


def create_example_config(output_path: Path) -> None:
    """Create an example configuration file.

    Args:
        output_path: Path where to create the example config
    """
    example_config = """# Tello Renewal Configuration
# This is an example configuration file in TOML format

[tello]
email = "your_email@example.com"
password = "your_password"
card_expiration = "1/25"  # MM/YY format
base_url = "https://tello.com"
login_timeout = 30

[browser]
headless = true
browser_type = "firefox"  # firefox, chrome, edge
page_load_timeout = 30
implicit_wait = 10
window_size = "1920x1080"

[renewal]
auto_renew = true
days_before_renewal = 1
max_retries = 3
retry_delay = 300  # seconds
dry_run = false

[smtp]
server = "smtp.gmail.com"
port = 587
username = "your_email@gmail.com"
password = "your_app_password"
from_email = '"Tello Renewal" <your_email@gmail.com>'
use_tls = true

[notifications]
email_enabled = true
recipients = ["admin@example.com"]
send_on_success = true
send_on_failure = true
send_on_not_due = false

[logging]
level = "INFO"
format = "detailed"  # simple, detailed, json
file = "tello_renewal.log"
max_size = "10MB"
backup_count = 5
console_output = true
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(example_config)

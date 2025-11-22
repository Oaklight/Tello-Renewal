"""Simplified logging configuration using loguru.

This module provides a clean, simple logging setup with automatic
sensitive data redaction and easy configuration.
"""

import re
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from .config import LoggingConfig


def _redact_sensitive_data(record: Any) -> bool:
    """Redact sensitive information from log messages."""
    message: str = record["message"]

    # Patterns to redact sensitive information
    patterns = [
        (r'password["\s]*[:=]["\s]*([^"\s,}]+)', r'password="***"'),
        (r'card_expiration["\s]*[:=]["\s]*([^"\s,}]+)', r'card_expiration="***"'),
        (r'smtp.*password["\s]*[:=]["\s]*([^"\s,}]+)', r'smtp_password="***"'),
        (r'from_email["\s]*[:=]["\s]*([^"\s,}]+)', r'from_email="***"'),
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", r"****-****-****-****"),
        (r'email["\s]*[:=]["\s]*([^"\s,}]+@[^"\s,}]+)', r'email="***@***.***"'),
    ]

    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

    record["message"] = message
    return True  # Always allow the record to be logged


def configure_logging(config: LoggingConfig | None = None) -> None:
    """Configure logging using loguru.

    Args:
        config: Logging configuration. If None, uses default settings.
    """
    if config is None:
        config = LoggingConfig()

    # Remove default handler
    logger.remove()

    # Add console handler if enabled
    if config.console_output:
        logger.add(
            sys.stdout,
            level=config.level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            filter=_redact_sensitive_data,
            colorize=True,
        )

    # Add file handler if specified
    if config.file:
        log_path = Path(config.file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            config.file,
            level=config.level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} - {message}",
            filter=_redact_sensitive_data,
            rotation=config.max_size,
            retention=config.backup_count,
            compression="zip",
            encoding="utf-8",
        )

    # Configure third-party loggers to reduce noise
    logger.disable("selenium")
    logger.disable("urllib3")


def get_logger(name: str) -> Any:
    """Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Loguru logger instance
    """
    # For loguru, we just return the main logger since it handles context automatically
    return logger


# Convenience functions
def log_function_call(func_name: str, **kwargs: Any) -> None:
    """Log function call with parameters (sensitive data will be redacted).

    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.debug(f"Calling {func_name}({params})")


# Legacy compatibility function for old signature
def log_function_call_legacy(
    logger_instance: Any, func_name: str, **kwargs: Any
) -> None:
    """Legacy compatibility for log_function_call with logger parameter."""
    log_function_call(func_name, **kwargs)


def log_duration(operation: str, duration: float) -> None:
    """Log operation duration.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
    """
    logger.info(f"{operation} completed in {duration:.2f} seconds")


# Export the main logger for direct use
__all__ = [
    "logger",
    "configure_logging",
    "get_logger",
    "log_function_call",
    "log_duration",
]

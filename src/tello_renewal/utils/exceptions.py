"""Custom exceptions for Tello renewal system.

This module defines the exception hierarchy used throughout the application
to provide clear error handling and debugging information.
"""


class TelloRenewalError(Exception):
    """Base exception class for all Tello renewal related errors."""

    pass


class WebDriverError(TelloRenewalError):
    """Browser driver related errors."""

    pass


class PageLoadError(TelloRenewalError):
    """Page loading errors."""

    pass


class ElementNotFoundError(TelloRenewalError):
    """Element not found on page errors."""

    pass


class LoginError(TelloRenewalError):
    """Login failure errors."""

    pass


class RenewalError(TelloRenewalError):
    """Renewal operation errors."""

    pass


class ConfigurationError(TelloRenewalError):
    """Configuration related errors."""

    pass


class NotificationError(TelloRenewalError):
    """Notification system errors."""

    pass

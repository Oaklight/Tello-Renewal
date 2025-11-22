"""Web automation module for Tello renewal system.

This module provides web automation capabilities using the Page Object Model
and strategy patterns for robust and maintainable web interactions.
"""

from .client import TelloWebClient
from .driver import BrowserDriverManager

__all__ = ["TelloWebClient", "BrowserDriverManager"]

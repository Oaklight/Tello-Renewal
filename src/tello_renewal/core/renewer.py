"""Main renewal engine for Tello plan automation.

This module provides backward compatibility with the original RenewalEngine
while using the new refactored architecture internally.
"""

from datetime import date

from ..utils.config import Config

# Re-export exceptions for backward compatibility
from ..utils.exceptions import (
    ElementNotFoundError,
)
from ..utils.exceptions import (
    LoginError as LoginFailedError,
)
from ..utils.exceptions import (
    RenewalError as RenewalPageError,
)
from ..utils.exceptions import (
    TelloRenewalError as TelloWebError,
)
from ..utils.logging import get_logger

# Import the new web client for backward compatibility
from ..web.client import TelloWebClient
from .engine import RenewalEngine as NewRenewalEngine
from .models import AccountSummary, RenewalResult

logger = get_logger(__name__)


class RenewalEngine:
    """Main renewal logic and orchestration.

    This class provides backward compatibility with the original interface
    while using the new refactored architecture internally.
    """

    def __init__(self, config: Config, dry_run: bool = False):
        """Initialize renewal engine.

        Args:
            config: Application configuration
            dry_run: If True, don't perform actual renewal
        """
        # Use the new engine internally
        self._engine = NewRenewalEngine(config, dry_run)

        # Keep original attributes for backward compatibility
        self.config = config
        self.dry_run = dry_run or config.renewal.dry_run

    def check_renewal_needed(self, renewal_date: date) -> bool:
        """Check if renewal is needed based on date.

        Args:
            renewal_date: The renewal due date

        Returns:
            True if renewal should be performed
        """
        return self._engine.check_renewal_needed(renewal_date)

    def get_account_summary(self) -> AccountSummary:
        """Get current account status and balance.

        Returns:
            Complete account summary

        Raises:
            TelloWebError: If web automation fails
        """
        try:
            return self._engine.get_account_summary()
        except Exception as e:
            # Convert to original exception type for backward compatibility
            raise TelloWebError(f"Failed to get account summary: {e}")

    def execute_renewal(self) -> RenewalResult:
        """Execute the complete renewal process.

        Returns:
            Result of the renewal operation
        """
        return self._engine.execute_renewal()

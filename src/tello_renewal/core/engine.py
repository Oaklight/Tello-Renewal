"""Renewal engine using the new refactored architecture.

This module provides the main renewal engine that orchestrates
all services using the Page Object Model and service layer.
"""

import time
from datetime import date, datetime
from typing import Any

from ..utils.cache import (
    DueDateCache,
    ExecutionStatus,
    ExecutionStatusCache,
    RunStateCache,
)
from ..utils.config import Config
from ..utils.exceptions import TelloRenewalError
from ..utils.logging import get_logger, log_duration
from ..web.client import TelloWebClient
from .models import AccountSummary, RenewalResult, RenewalStatus
from .services import AccountService, BalanceService, RenewalService

logger = get_logger(__name__)


class RenewalEngine:
    """Main renewal engine using the refactored architecture."""

    def __init__(self, config: Config, dry_run: bool = False):
        """Initialize renewal engine.

        Args:
            config: Application configuration
            dry_run: If True, don't perform actual renewal
        """
        self.config = config
        self.dry_run = dry_run or config.renewal.dry_run

        # Initialize state managers
        self.cache = DueDateCache(config.renewal.state_folder_path)
        self.run_state_cache = RunStateCache(config.renewal.state_folder_path)
        # Keep old execution status cache for backward compatibility
        self.exec_status_cache = ExecutionStatusCache("EXEC_STATUS")

        # Services will be initialized when web client is available
        self._account_service: AccountService | None = None
        self._balance_service: BalanceService | None = None
        self._renewal_service: RenewalService | None = None

    def _initialize_services(self, web_client: TelloWebClient) -> None:
        """Initialize all services with web client.

        Args:
            web_client: Initialized web client
        """
        self._account_service = AccountService(web_client)
        self._balance_service = BalanceService(web_client)
        self._renewal_service = RenewalService(web_client)

        logger.debug("Services initialized successfully")

    @property
    def account_service(self) -> AccountService:
        """Get account service."""
        if self._account_service is None:
            raise TelloRenewalError("Account service not initialized")
        return self._account_service

    @property
    def balance_service(self) -> BalanceService:
        """Get balance service."""
        if self._balance_service is None:
            raise TelloRenewalError("Balance service not initialized")
        return self._balance_service

    @property
    def renewal_service(self) -> RenewalService:
        """Get renewal service."""
        if self._renewal_service is None:
            raise TelloRenewalError("Renewal service not initialized")
        return self._renewal_service

    def get_account_summary(self) -> AccountSummary:
        """Get current account status and balance.

        Returns:
            Complete account summary

        Raises:
            TelloRenewalError: If web automation fails
        """
        start_time = time.time()

        try:
            with TelloWebClient(self.config.browser, dry_run=True) as client:
                self._initialize_services(client)

                # Login to account
                self.account_service.login(
                    self.config.tello.email,
                    self.config.tello.password,
                    self.config.tello.base_url,
                )

                # Get account summary with proper email
                renewal_date = self.account_service.get_renewal_date()
                current_balance = self.balance_service.get_current_balance()
                plan_balance = self.balance_service.get_plan_balance()

                days_until = (renewal_date - datetime.now().date()).days

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
            raise TelloRenewalError("Failed to get account summary") from e

    def execute_renewal(self, force: bool = False) -> RenewalResult:
        """Execute the complete renewal process.

        Args:
            force: If True, ignore cached due date and force renewal check

        Returns:
            Result of the renewal operation
        """
        start_time = time.time()
        timestamp = datetime.now()
        current_date = datetime.now().date()

        logger.info(f"Starting renewal process (dry_run={self.dry_run}, force={force})")

        # Check cache first unless force is True
        if not force:
            # First check due date cache
            if self.cache.should_skip_renewal(
                current_date, self.config.renewal.days_before_renewal
            ):
                cached_date = self.cache.read_cached_date()
                message = f"Skipping renewal check - within {self.config.renewal.days_before_renewal} days of cached date {cached_date}"
                logger.info(message)
                duration = time.time() - start_time
                return RenewalResult(
                    status=RenewalStatus.SKIPPED,
                    timestamp=timestamp,
                    message=message,
                    duration_seconds=duration,
                )

            # Then check run state cache for today's execution
            cached_date = self.cache.read_cached_date()
            if cached_date and self.run_state_cache.should_skip_renewal(
                cached_date, self.config.renewal.days_before_renewal
            ):
                message = "Skipping renewal - already successfully completed today"
                logger.info(message)
                duration = time.time() - start_time
                return RenewalResult(
                    status=RenewalStatus.SKIPPED,
                    timestamp=timestamp,
                    message=message,
                    duration_seconds=duration,
                )

        try:
            with TelloWebClient(self.config.browser, self.dry_run) as client:
                self._initialize_services(client)

                # Login to account
                self.account_service.login(
                    self.config.tello.email,
                    self.config.tello.password,
                    self.config.tello.base_url,
                )

                # Get renewal date and check if renewal is needed
                renewal_date = self.account_service.get_renewal_date()

                # Always update cache with the actual renewal date
                # This helps keep the cache fresh for future runs
                cached_date = self.cache.read_cached_date()
                if cached_date != renewal_date:
                    self.cache.write_cached_date(renewal_date)
                    logger.info(
                        f"Updated due_date cache with renewal date: {renewal_date}"
                    )
                else:
                    logger.debug(f"Due date cache already up to date: {renewal_date}")

                if not self.account_service.check_renewal_needed(
                    renewal_date, self.config.renewal.days_before_renewal
                ):
                    days_until = (renewal_date - datetime.now().date()).days
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

                # Get balance information
                balance_summary = self.balance_service.get_balance_summary()
                current_balance = balance_summary["current"]
                plan_balance = balance_summary["plan"]
                new_balance = balance_summary["new"]

                # Log balance information
                self.balance_service.log_balance_details(current_balance, "Current")
                self.balance_service.log_balance_details(plan_balance, "Plan")
                self.balance_service.log_balance_details(new_balance, "New")

                # Execute renewal process
                success = self.renewal_service.execute_renewal(
                    self.config.tello.card_expiration, self.dry_run
                )

                duration = time.time() - start_time

                if success:
                    status = RenewalStatus.SUCCESS
                    message = "Renewal completed successfully"
                    if self.dry_run:
                        message += " (dry run)"

                    logger.info(message)

                    # Record success status in new run state cache
                    self.run_state_cache.write_run_state(
                        success=True, dry=self.dry_run, timestamp=timestamp
                    )

                    # Also record in old execution status cache for backward compatibility
                    if not self.dry_run:
                        self.exec_status_cache.write_execution_status(
                            ExecutionStatus.SUCCESS, timestamp
                        )

                    return RenewalResult(
                        status=status,
                        timestamp=timestamp,
                        message=message,
                        new_balance=new_balance,
                        duration_seconds=duration,
                    )
                else:
                    raise TelloRenewalError("Renewal submission failed")

        except Exception as e:
            duration = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Renewal failed: {error_msg}")

            # Record failure status in new run state cache
            self.run_state_cache.write_run_state(
                success=False, dry=self.dry_run, timestamp=timestamp
            )

            # Also record in old execution status cache for backward compatibility
            self.exec_status_cache.write_execution_status(
                ExecutionStatus.FAILED, timestamp
            )

            return RenewalResult(
                status=RenewalStatus.FAILED,
                timestamp=timestamp,
                message="Renewal failed",
                error=error_msg,
                duration_seconds=duration,
            )

    def check_renewal_needed(self, renewal_date: date) -> bool:
        """Check if renewal is needed based on date.

        Args:
            renewal_date: The renewal due date

        Returns:
            True if renewal should be performed
        """
        return self.account_service.check_renewal_needed(
            renewal_date, self.config.renewal.days_before_renewal
        )

    def validate_configuration(self) -> bool:
        """Validate that configuration is complete for renewal.

        Returns:
            True if configuration is valid

        Raises:
            TelloRenewalError: If configuration is invalid
        """
        try:
            # Check required Tello configuration
            if not self.config.tello.email:
                raise TelloRenewalError("Tello email not configured")

            if not self.config.tello.password:
                raise TelloRenewalError("Tello password not configured")

            if not self.config.tello.card_expiration:
                raise TelloRenewalError("Card expiration not configured")

            # Check browser configuration
            if not self.config.browser.browser_type:
                raise TelloRenewalError("Browser type not configured")

            logger.info("Configuration validation passed")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

    def get_system_status(self) -> dict[str, Any]:
        """Get current system status information.

        Returns:
            Dictionary containing system status
        """
        try:
            status = {
                "config_valid": False,
                "dry_run": self.dry_run,
                "browser_type": self.config.browser.browser_type,
                "headless": self.config.browser.headless,
                "days_before_renewal": self.config.renewal.days_before_renewal,
            }

            try:
                status["config_valid"] = self.validate_configuration()
            except Exception as e:
                status["config_error"] = str(e)

            return status

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"error": str(e)}

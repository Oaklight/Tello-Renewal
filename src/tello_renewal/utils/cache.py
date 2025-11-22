"""Cache management for Tello renewal system.

This module provides functionality to manage the DUE_DATE cache file
to prevent frequent renewal checks and avoid upstream bot detection.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any

from .logging import get_logger

logger = get_logger(__name__)


class ExecutionStatus:
    """Represents the execution status of a renewal attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    NOT_DUE = "not_due"
    SKIPPED = "skipped"


class DueDateCache:
    """Manages the DUE_DATE cache file for renewal scheduling."""

    def __init__(self, cache_file_path: str = "DUE_DATE"):
        """Initialize the cache manager.

        Args:
            cache_file_path: Path to the cache file
        """
        self.cache_file_path = Path(cache_file_path)
        logger.debug(f"Initialized DueDateCache with path: {self.cache_file_path}")

    def read_cached_date(self) -> date | None:
        """Read the cached renewal date from file.

        Returns:
            The cached renewal date, or None if file doesn't exist or is invalid

        Raises:
            ValueError: If the cached date format is invalid
        """
        if not self.cache_file_path.exists():
            logger.debug("Cache file does not exist")
            return None

        try:
            with open(self.cache_file_path, encoding="utf-8") as f:
                date_str = f.read().strip()

            if not date_str:
                logger.warning("Cache file is empty")
                return None

            # Parse the date in ISO format (YYYY-MM-DD)
            cached_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"Read cached renewal date: {cached_date}")
            return cached_date

        except OSError as e:
            logger.error(f"Failed to read cache file: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid date format in cache file: {e}")
            # Remove invalid cache file
            self._remove_cache_file()
            return None

    def write_cached_date(self, renewal_date: date) -> bool:
        """Write the renewal date to cache file.

        Args:
            renewal_date: The renewal date to cache

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create parent directories if they don't exist
            self.cache_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write the date in ISO format
            with open(self.cache_file_path, "w", encoding="utf-8") as f:
                f.write(renewal_date.strftime("%Y-%m-%d"))

            logger.info(f"Cached renewal date: {renewal_date}")
            return True

        except OSError as e:
            logger.error(f"Failed to write cache file: {e}")
            return False

    def is_within_range(self, current_date: date, range_days: int) -> bool:
        """Check if current date is within range of cached renewal date.

        Args:
            current_date: The current date to check
            range_days: Number of days range to check

        Returns:
            True if within range, False otherwise
        """
        cached_date = self.read_cached_date()
        if cached_date is None:
            logger.debug("No cached date found, not within range")
            return False

        days_diff = abs((current_date - cached_date).days)
        within_range = days_diff <= range_days

        logger.info(
            f"Date check: current={current_date}, cached={cached_date}, "
            f"diff={days_diff} days, range={range_days} days, "
            f"within_range={within_range}"
        )

        return within_range

    def should_skip_renewal(self, current_date: date, range_days: int) -> bool:
        """Determine if renewal should be skipped based on cache.

        Args:
            current_date: The current date
            range_days: Number of days range to check

        Returns:
            True if renewal should be skipped, False otherwise
        """
        if not self.cache_file_path.exists():
            logger.debug("No cache file exists, should not skip renewal")
            return False

        return self.is_within_range(current_date, range_days)

    def clear_cache(self) -> bool:
        """Remove the cache file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        return self._remove_cache_file()

    def _remove_cache_file(self) -> bool:
        """Remove the cache file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        try:
            if self.cache_file_path.exists():
                self.cache_file_path.unlink()
                logger.info("Cache file removed")
            else:
                logger.debug("Cache file does not exist, nothing to remove")
            return True

        except OSError as e:
            logger.error(f"Failed to remove cache file: {e}")
            return False

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the cache file.

        Returns:
            Dictionary containing cache information
        """
        info: dict[str, Any] = {
            "cache_file_path": str(self.cache_file_path),
            "exists": self.cache_file_path.exists(),
            "cached_date": None,
            "file_size": None,
            "last_modified": None,
        }

        if info["exists"]:
            try:
                stat = self.cache_file_path.stat()
                info["file_size"] = stat.st_size
                info["last_modified"] = datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()
                info["cached_date"] = self.read_cached_date()
            except OSError as e:
                logger.error(f"Failed to get cache file info: {e}")

        return info


class ExecutionStatusCache:
    """Manages the execution status cache file for renewal tracking."""

    def __init__(self, status_file_path: str = "EXEC_STATUS"):
        """Initialize the execution status cache manager.

        Args:
            status_file_path: Path to the execution status cache file
        """
        self.status_file_path = Path(status_file_path)
        logger.debug(
            f"Initialized ExecutionStatusCache with path: {self.status_file_path}"
        )

    def read_execution_status(self) -> tuple[datetime, str] | None:
        """Read the last execution status from file.

        Returns:
            Tuple of (timestamp, status) or None if file doesn't exist or is invalid

        Raises:
            ValueError: If the cached status format is invalid
        """
        if not self.status_file_path.exists():
            logger.debug("Execution status file does not exist")
            return None

        try:
            with open(self.status_file_path, encoding="utf-8") as f:
                lines = f.read().strip().split("\n")

            if len(lines) != 2:
                logger.warning(
                    f"Invalid execution status file format: expected 2 lines, got {len(lines)}"
                )
                return None

            timestamp_str, status = lines[0].strip(), lines[1].strip()

            if not timestamp_str or not status:
                logger.warning("Execution status file contains empty lines")
                return None

            # Parse the timestamp in ISO format
            timestamp = datetime.fromisoformat(timestamp_str)

            # Validate status
            valid_statuses = {
                ExecutionStatus.SUCCESS,
                ExecutionStatus.FAILED,
                ExecutionStatus.NOT_DUE,
                ExecutionStatus.SKIPPED,
            }
            if status not in valid_statuses:
                logger.warning(f"Invalid execution status: {status}")
                return None

            logger.info(f"Read execution status: {timestamp} - {status}")
            return timestamp, status

        except OSError as e:
            logger.error(f"Failed to read execution status file: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid timestamp format in execution status file: {e}")
            # Remove invalid status file
            self._remove_status_file()
            return None

    def write_execution_status(
        self, status: str, timestamp: datetime | None = None
    ) -> bool:
        """Write the execution status to cache file.

        Args:
            status: The execution status (success, failed, not_due, skipped)
            timestamp: The execution timestamp (defaults to current time)

        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = datetime.now()

        try:
            # Create parent directories if they don't exist
            self.status_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write timestamp and status
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                f.write(f"{timestamp.isoformat()}\n{status}")

            logger.info(f"Cached execution status: {timestamp} - {status}")
            return True

        except OSError as e:
            logger.error(f"Failed to write execution status file: {e}")
            return False

    def should_retry_renewal(self, renewal_date: date, days_before: int) -> bool:
        """Determine if renewal should be retried based on execution status.

        Args:
            renewal_date: The renewal due date
            days_before: Days before renewal to start attempting

        Returns:
            True if renewal should be attempted, False if should skip
        """
        current_date = date.today()

        # Check if we're in the renewal window
        days_until_renewal = (renewal_date - current_date).days
        in_renewal_window = 0 <= days_until_renewal <= days_before

        if not in_renewal_window:
            logger.debug(
                f"Not in renewal window: {days_until_renewal} days until renewal"
            )
            return True  # Outside window, normal logic applies

        logger.info(f"In renewal window: {days_until_renewal} days until renewal")

        # Check execution status
        status_info = self.read_execution_status()
        if status_info is None:
            logger.info("No execution status found, should attempt renewal")
            return True

        timestamp, status = status_info

        # Check if the status is from today
        if timestamp.date() != current_date:
            logger.info(
                f"Execution status is from {timestamp.date()}, not today, should attempt renewal"
            )
            return True

        # If we had a successful renewal today, don't retry
        if status == ExecutionStatus.SUCCESS:
            logger.info("Renewal was successful today, skipping retry")
            return False

        # If it failed or was not due, we can retry
        if status in (ExecutionStatus.FAILED, ExecutionStatus.NOT_DUE):
            logger.info(f"Previous attempt was {status}, should retry")
            return True

        # If it was skipped, we can retry
        if status == ExecutionStatus.SKIPPED:
            logger.info("Previous attempt was skipped, should retry")
            return True

        # Default to retry
        logger.info(f"Unknown status {status}, defaulting to retry")
        return True

    def clear_status(self) -> bool:
        """Remove the execution status file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        return self._remove_status_file()

    def _remove_status_file(self) -> bool:
        """Remove the execution status file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        try:
            if self.status_file_path.exists():
                self.status_file_path.unlink()
                logger.info("Execution status file removed")
            else:
                logger.debug("Execution status file does not exist, nothing to remove")
            return True

        except OSError as e:
            logger.error(f"Failed to remove execution status file: {e}")
            return False

    def get_status_info(self) -> dict[str, Any]:
        """Get information about the execution status file.

        Returns:
            Dictionary containing status file information
        """
        info: dict[str, Any] = {
            "status_file_path": str(self.status_file_path),
            "exists": self.status_file_path.exists(),
            "last_execution": None,
            "last_status": None,
            "file_size": None,
            "last_modified": None,
        }

        if info["exists"]:
            try:
                stat = self.status_file_path.stat()
                info["file_size"] = stat.st_size
                info["last_modified"] = datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()

                status_info = self.read_execution_status()
                if status_info:
                    info["last_execution"] = status_info[0].isoformat()
                    info["last_status"] = status_info[1]
            except OSError as e:
                logger.error(f"Failed to get execution status file info: {e}")

        return info

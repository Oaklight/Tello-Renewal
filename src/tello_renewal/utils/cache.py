"""State management for Tello renewal system.

This module provides functionality to manage state files including
due date tracking and renewal execution status to prevent frequent
renewal checks and avoid upstream bot detection.
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytz

from .logging import get_logger

logger = get_logger(__name__)


class ExecutionStatus:
    """Represents the execution status of a renewal attempt."""

    SUCCESS = "success"
    FAILED = "failed"
    NOT_DUE = "not_due"
    SKIPPED = "skipped"


class DueDateCache:
    """Manages the due_date state file for renewal scheduling."""

    def __init__(self, state_folder_path: str = ".tello_state"):
        """Initialize the cache manager.

        Args:
            state_folder_path: Path to the state folder
        """
        self.state_folder = Path(state_folder_path)
        self.due_date_file = self.state_folder / "due_date"
        logger.debug(f"Initialized DueDateCache with folder: {self.state_folder}")

    def read_cached_date(self) -> date | None:
        """Read the cached renewal date from file.

        Returns:
            The cached renewal date, or None if file doesn't exist or is invalid

        Raises:
            ValueError: If the cached date format is invalid
        """
        if not self.due_date_file.exists():
            logger.debug("Due date file does not exist")
            return None

        try:
            with open(self.due_date_file, encoding="utf-8") as f:
                date_str = f.read().strip()

            if not date_str:
                logger.warning("Due date file is empty")
                return None

            # Parse the date in ISO format (YYYY-MM-DD)
            cached_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            logger.info(f"Read cached renewal date: {cached_date}")
            return cached_date

        except OSError as e:
            logger.error(f"Failed to read due date file: {e}")
            return None
        except ValueError as e:
            logger.error(f"Invalid date format in due date file: {e}")
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
            # Create state directory if it doesn't exist
            self.state_folder.mkdir(parents=True, exist_ok=True)

            # Write the date in ISO format
            with open(self.due_date_file, "w", encoding="utf-8") as f:
                f.write(renewal_date.strftime("%Y-%m-%d"))

            logger.info(f"Cached renewal date: {renewal_date}")
            return True

        except OSError as e:
            logger.error(f"Failed to write due date file: {e}")
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
        if not self.due_date_file.exists():
            logger.debug("No due date file exists, should not skip renewal")
            return False

        # If we're within range of the cached renewal date, we should NOT skip
        # (i.e., we should proceed with renewal check)
        # If we're outside the range, we should skip (too far from renewal date)
        within_range = self.is_within_range(current_date, range_days)
        should_skip = not within_range

        logger.debug(
            f"should_skip_renewal: within_range={within_range}, should_skip={should_skip}"
        )
        return should_skip

    def clear_cache(self) -> bool:
        """Remove the cache file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        return self._remove_cache_file()

    def _remove_cache_file(self) -> bool:
        """Remove the due date file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        try:
            if self.due_date_file.exists():
                self.due_date_file.unlink()
                logger.info("Due date file removed")
            else:
                logger.debug("Due date file does not exist, nothing to remove")
            return True

        except OSError as e:
            logger.error(f"Failed to remove due date file: {e}")
            return False

    def get_cache_info(self) -> dict[str, Any]:
        """Get information about the due date file.

        Returns:
            Dictionary containing cache information
        """
        info: dict[str, Any] = {
            "state_folder_path": str(self.state_folder),
            "due_date_file_path": str(self.due_date_file),
            "exists": self.due_date_file.exists(),
            "cached_date": None,
            "file_size": None,
            "last_modified": None,
        }

        if info["exists"]:
            try:
                stat = self.due_date_file.stat()
                info["file_size"] = stat.st_size
                info["last_modified"] = datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()
                info["cached_date"] = self.read_cached_date()
            except OSError as e:
                logger.error(f"Failed to get due date file info: {e}")

        return info


def get_chicago_time() -> datetime:
    """Get current time in Chicago timezone.

    Returns:
        Current datetime in America/Chicago timezone
    """
    chicago_tz = pytz.timezone("America/Chicago")
    return datetime.now(chicago_tz)


class RunStateCache:
    """Manages the run_state file for renewal execution tracking."""

    def __init__(self, state_folder_path: str = ".tello_state"):
        """Initialize the run state cache manager.

        Args:
            state_folder_path: Path to the state folder
        """
        self.state_folder = Path(state_folder_path)
        self.run_state_file = self.state_folder / "run_state"
        logger.debug(f"Initialized RunStateCache with folder: {self.state_folder}")

    def read_run_state(self) -> dict[str, Any] | None:
        """Read the last run state from file.

        Returns:
            Dictionary containing run state or None if file doesn't exist or is invalid
        """
        if not self.run_state_file.exists():
            logger.debug("Run state file does not exist")
            return None

        try:
            with open(self.run_state_file, encoding="utf-8") as f:
                state_data = json.load(f)

            # Validate required fields
            required_fields = ["date", "success", "dry"]
            if not all(field in state_data for field in required_fields):
                logger.warning(
                    f"Run state file missing required fields: {required_fields}"
                )
                return None

            # Parse the date
            try:
                state_data["date"] = datetime.fromisoformat(state_data["date"])
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid date format in run state file: {e}")
                return None

            logger.info(f"Read run state: {state_data}")
            return state_data

        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Failed to read run state file: {e}")
            # Remove invalid state file
            self._remove_state_file()
            return None

    def write_run_state(
        self, success: bool, dry: bool, timestamp: datetime | None = None
    ) -> bool:
        """Write the run state to file.

        Args:
            success: Whether the renewal was successful
            dry: Whether this was a dry run
            timestamp: The execution timestamp (defaults to current Chicago time)

        Returns:
            True if successful, False otherwise
        """
        if timestamp is None:
            timestamp = get_chicago_time()

        state_data = {"date": timestamp.isoformat(), "success": success, "dry": dry}

        try:
            # Create state directory if it doesn't exist
            self.state_folder.mkdir(parents=True, exist_ok=True)

            # Write state data as JSON
            with open(self.run_state_file, "w", encoding="utf-8") as f:
                json.dump(state_data, f, indent=2)

            logger.info(f"Wrote run state: {state_data}")
            return True

        except OSError as e:
            logger.error(f"Failed to write run state file: {e}")
            return False

    def should_skip_renewal(self, due_date: date, days_before: int) -> bool:
        """Determine if renewal should be skipped based on run state.

        Args:
            due_date: The renewal due date
            days_before: Days before renewal to start attempting

        Returns:
            True if renewal should be skipped, False otherwise
        """
        chicago_time = get_chicago_time()
        current_date = chicago_time.date()

        # Check if we're in the renewal window
        days_until_renewal = (due_date - current_date).days
        in_renewal_window = 0 <= days_until_renewal <= days_before

        if not in_renewal_window:
            logger.debug(
                f"Not in renewal window: {days_until_renewal} days until renewal"
            )
            return False  # Outside window, don't skip

        logger.info(f"In renewal window: {days_until_renewal} days until renewal")

        # Check run state
        state_info = self.read_run_state()
        if state_info is None:
            logger.info("No run state found, should attempt renewal")
            return False

        # Check if the state is from today (Chicago time)
        state_date = state_info["date"].date()
        if state_date != current_date:
            logger.info(
                f"Run state is from {state_date}, not today ({current_date}), should attempt renewal"
            )
            return False

        # If we had a successful renewal today, skip
        if state_info["success"] and not state_info["dry"]:
            logger.info("Renewal was successful today (not dry run), skipping")
            return True

        # If it was a dry run success, we can retry with real run
        if state_info["success"] and state_info["dry"]:
            logger.info(
                "Previous attempt was successful dry run, should attempt real renewal"
            )
            return False

        # If it failed, we can retry
        if not state_info["success"]:
            logger.info("Previous attempt failed, should retry")
            return False

        # Default to not skip
        logger.info("Default behavior: should attempt renewal")
        return False

    def clear_state(self) -> bool:
        """Remove the run state file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        return self._remove_state_file()

    def _remove_state_file(self) -> bool:
        """Remove the run state file.

        Returns:
            True if successful or file doesn't exist, False otherwise
        """
        try:
            if self.run_state_file.exists():
                self.run_state_file.unlink()
                logger.info("Run state file removed")
            else:
                logger.debug("Run state file does not exist, nothing to remove")
            return True

        except OSError as e:
            logger.error(f"Failed to remove run state file: {e}")
            return False

    def get_state_info(self) -> dict[str, Any]:
        """Get information about the run state file.

        Returns:
            Dictionary containing state file information
        """
        info: dict[str, Any] = {
            "state_folder_path": str(self.state_folder),
            "run_state_file_path": str(self.run_state_file),
            "exists": self.run_state_file.exists(),
            "last_run": None,
            "file_size": None,
            "last_modified": None,
        }

        if info["exists"]:
            try:
                stat = self.run_state_file.stat()
                info["file_size"] = stat.st_size
                info["last_modified"] = datetime.fromtimestamp(
                    stat.st_mtime
                ).isoformat()

                state_info = self.read_run_state()
                if state_info:
                    info["last_run"] = state_info
            except OSError as e:
                logger.error(f"Failed to get run state file info: {e}")

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

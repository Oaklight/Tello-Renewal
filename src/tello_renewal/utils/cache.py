"""Cache management for Tello renewal system.

This module provides functionality to manage the DUE_DATE cache file
to prevent frequent renewal checks and avoid upstream bot detection.
"""

from datetime import date, datetime
from pathlib import Path
from typing import Any

from .logging import get_logger

logger = get_logger(__name__)


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

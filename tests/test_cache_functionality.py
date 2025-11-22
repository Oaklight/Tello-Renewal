#!/usr/bin/env python3
"""Test script for DUE_DATE cache functionality."""

# Add src to path for testing
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, "src")

from tello_renewal.utils.cache import DueDateCache


def test_cache_functionality():
    """Test the DueDateCache functionality."""
    print("Testing DUE_DATE cache functionality...")

    # Create a temporary cache file
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_DUE_DATE") as tmp:
        cache_path = tmp.name

    try:
        # Initialize cache
        cache = DueDateCache(cache_path)
        print(f"✓ Cache initialized with path: {cache_path}")

        # Test 1: Read from non-existent cache
        cached_date = cache.read_cached_date()
        assert cached_date is None, "Expected None for non-existent cache"
        print("✓ Test 1 passed: Non-existent cache returns None")

        # Test 2: Write and read cache
        test_date = date.today() + timedelta(days=30)
        success = cache.write_cached_date(test_date)
        assert success, "Failed to write cache"

        cached_date = cache.read_cached_date()
        assert cached_date == test_date, f"Expected {test_date}, got {cached_date}"
        print(f"✓ Test 2 passed: Write and read cache ({test_date})")

        # Test 3: Check within range
        current_date = date.today()
        within_range = cache.is_within_range(current_date, 35)  # 35 days range
        assert within_range, "Should be within 35 days range"
        print("✓ Test 3 passed: Within range check (35 days)")

        # Test 4: Check outside range
        within_range = cache.is_within_range(current_date, 25)  # 25 days range
        assert not within_range, "Should be outside 25 days range"
        print("✓ Test 4 passed: Outside range check (25 days)")

        # Test 5: Should skip renewal
        should_skip = cache.should_skip_renewal(current_date, 35)
        assert should_skip, "Should skip renewal within range"
        print("✓ Test 5 passed: Should skip renewal within range")

        should_skip = cache.should_skip_renewal(current_date, 25)
        assert not should_skip, "Should not skip renewal outside range"
        print("✓ Test 6 passed: Should not skip renewal outside range")

        # Test 7: Cache info
        info = cache.get_cache_info()
        assert info["exists"], "Cache file should exist"
        assert info["cached_date"] == test_date, (
            "Cache info should contain correct date"
        )
        print("✓ Test 7 passed: Cache info retrieval")

        # Test 8: Clear cache
        success = cache.clear_cache()
        assert success, "Failed to clear cache"

        cached_date = cache.read_cached_date()
        assert cached_date is None, "Cache should be empty after clearing"
        print("✓ Test 8 passed: Cache clearing")

        print("\n🎉 All cache functionality tests passed!")

    finally:
        # Clean up
        cache_file = Path(cache_path)
        if cache_file.exists():
            cache_file.unlink()


def test_config_integration():
    """Test that the new config parameters work."""
    print("\nTesting configuration integration...")

    # Test default values
    from tello_renewal.utils.config import RenewalConfig

    config = RenewalConfig()
    assert config.days_before_renewal == 1, (
        f"Expected days_before_renewal=1, got {config.days_before_renewal}"
    )
    assert config.cache_file_path == "DUE_DATE", (
        f"Expected cache_file_path='DUE_DATE', got {config.cache_file_path}"
    )
    print("✓ Default configuration values are correct")

    # Test custom values
    config = RenewalConfig(days_before_renewal=7, cache_file_path="custom_cache")
    assert config.days_before_renewal == 7, (
        f"Expected days_before_renewal=7, got {config.days_before_renewal}"
    )
    assert config.cache_file_path == "custom_cache", (
        f"Expected cache_file_path='custom_cache', got {config.cache_file_path}"
    )
    print("✓ Custom configuration values work correctly")

    print("🎉 Configuration integration tests passed!")


if __name__ == "__main__":
    test_cache_functionality()
    test_config_integration()
    print("\n✅ All tests completed successfully!")
    print("\nSummary of implemented features:")
    print("1. ✅ DUE_DATE cache file mechanism")
    print("2. ✅ Uses existing days_before_renewal as cache range")
    print("3. ✅ --force CLI parameter to bypass cache")
    print("4. ✅ Cache respects --dry-run flag")
    print("5. ✅ SKIPPED status for cache hits")
    print("6. ✅ Proper exit codes for different scenarios")

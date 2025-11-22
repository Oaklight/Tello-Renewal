#!/usr/bin/env python3
"""Test script for the new state management system."""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path

from src.tello_renewal.utils.cache import DueDateCache, RunStateCache, get_chicago_time


def test_due_date_cache():
    """Test DueDateCache functionality."""
    print("Testing DueDateCache...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = DueDateCache(temp_dir)
        
        # Test writing and reading
        test_date = date(2025, 1, 15)
        assert cache.write_cached_date(test_date)
        
        read_date = cache.read_cached_date()
        assert read_date == test_date
        
        # Test file structure
        due_date_file = Path(temp_dir) / "due_date"
        assert due_date_file.exists()
        
        # Test cache info
        info = cache.get_cache_info()
        assert info["exists"]
        assert info["cached_date"] == test_date
        
        print("✓ DueDateCache tests passed")


def test_run_state_cache():
    """Test RunStateCache functionality."""
    print("Testing RunStateCache...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = RunStateCache(temp_dir)
        
        # Test writing and reading
        test_time = get_chicago_time()
        assert cache.write_run_state(success=True, dry=False, timestamp=test_time)
        
        state = cache.read_run_state()
        assert state is not None
        assert state["success"] is True
        assert state["dry"] is False
        assert state["date"].date() == test_time.date()
        
        # Test file structure
        run_state_file = Path(temp_dir) / "run_state"
        assert run_state_file.exists()
        
        # Test JSON format
        with open(run_state_file) as f:
            data = json.load(f)
        assert "date" in data
        assert "success" in data
        assert "dry" in data
        
        # Test state info
        info = cache.get_state_info()
        assert info["exists"]
        assert info["last_run"] is not None
        
        print("✓ RunStateCache tests passed")


def test_chicago_time():
    """Test Chicago time functionality."""
    print("Testing Chicago time...")
    
    chicago_time = get_chicago_time()
    assert chicago_time.tzinfo is not None
    assert str(chicago_time.tzinfo) == "America/Chicago"
    
    print(f"✓ Chicago time: {chicago_time}")


def test_renewal_logic():
    """Test renewal skip logic."""
    print("Testing renewal skip logic...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = RunStateCache(temp_dir)
        
        # Test with no state (should not skip)
        due_date = date.today()
        assert not cache.should_skip_renewal(due_date, 1)
        
        # Test with successful run today (should skip)
        cache.write_run_state(success=True, dry=False)
        assert cache.should_skip_renewal(due_date, 1)
        
        # Test with dry run success (should not skip for real run)
        cache.write_run_state(success=True, dry=True)
        assert not cache.should_skip_renewal(due_date, 1)
        
        # Test with failed run (should not skip)
        cache.write_run_state(success=False, dry=False)
        assert not cache.should_skip_renewal(due_date, 1)
        
        print("✓ Renewal logic tests passed")


def main():
    """Run all tests."""
    print("Testing new state management system...\n")
    
    try:
        test_due_date_cache()
        test_run_state_cache()
        test_chicago_time()
        test_renewal_logic()
        
        print("\n🎉 All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()
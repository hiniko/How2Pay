#!/usr/bin/env python3
"""
Test runner for the Finances project.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py test_cash_flow     # Run specific test file
    python run_tests.py TestCalculateMonthlyBillTotal  # Run specific test class
"""

import sys
import unittest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_tests(test_pattern=None):
    """Run unit tests with optional pattern matching."""
    
    # Discover tests in the tests directory
    loader = unittest.TestLoader()
    
    if test_pattern:
        # Try to load specific test pattern
        try:
            suite = loader.loadTestsFromName(f'tests.{test_pattern}')
        except Exception:
            try:
                # Maybe it's a test class
                suite = loader.loadTestsFromName(f'tests.test_cash_flow.{test_pattern}')
            except Exception:
                print(f"Could not find test pattern: {test_pattern}")
                return False
    else:
        # Load all tests
        suite = loader.discover('tests', pattern='test_*.py')
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()


if __name__ == '__main__':
    test_pattern = sys.argv[1] if len(sys.argv) > 1 else None
    success = run_tests(test_pattern)
    sys.exit(0 if success else 1)
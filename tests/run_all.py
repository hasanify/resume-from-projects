#!/usr/bin/env python3
"""Unified test runner for resume-from-projects."""
import os
import sys
import unittest


def main():
    print("=" * 60)
    print(" Running resume-from-projects test suite")
    print("=" * 60)

    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.dirname(__file__), pattern="test_*.py")

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print(f" ALL TESTS PASSED: {result.testsRun} tests executed successfully.")
        print("=" * 60)
        sys.exit(0)
    else:
        print(f" FAILURES: {len(result.failures)} failed, {len(result.errors)} errors out of {result.testsRun} tests.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

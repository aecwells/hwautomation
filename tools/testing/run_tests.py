#!/usr/bin/env python3
"""
Test runner for HWAutomation project.
Runs all test files or specific test modules.
"""

import argparse
import sys
import unittest
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def discover_and_run_tests(test_dir=None, pattern="test_*.py", verbosity=2):
    """
    Discover and run all tests.

    Args:
        test_dir: Directory to search for tests (default: current directory)
        pattern: Pattern to match test files
        verbosity: Test output verbosity (0=quiet, 1=normal, 2=verbose)

    Returns:
        TestResult object
    """
    if test_dir is None:
        test_dir = Path(__file__).parent

    # Discover tests
    loader = unittest.TestLoader()
    start_dir = str(test_dir)
    suite = loader.discover(start_dir, pattern=pattern)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result


def run_specific_test(test_module, verbosity=2):
    """
    Run a specific test module.

    Args:
        test_module: Name of test module (e.g., 'test_bios_config')
        verbosity: Test output verbosity

    Returns:
        TestResult object
    """
    try:
        module = __import__(test_module)
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)

        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)

        return result
    except ImportError as e:
        print(f"Error importing test module '{test_module}': {e}")
        return None


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="HWAutomation Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run all tests
  %(prog)s --module test_bios_config # Run specific test module
  %(prog)s --quick                  # Run basic integration test
  %(prog)s --verbose                # Run with verbose output
        """,
    )

    parser.add_argument(
        "--module", "-m", help="Run specific test module (e.g., test_bios_config)"
    )
    parser.add_argument(
        "--pattern",
        "-p",
        default="test_*.py",
        help="Pattern to match test files (default: test_*.py)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    parser.add_argument(
        "--quick", action="store_true", help="Run quick integration test only"
    )

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    print("HWAutomation Test Runner")
    print("=" * 25)

    if args.quick:
        # Run the quick integration test
        print("Running quick integration test...")
        try:
            from test_bios_system import main as quick_test_main

            return quick_test_main()
        except ImportError as e:
            print(f"Error running quick test: {e}")
            return 1

    elif args.module:
        # Run specific module
        print(f"Running test module: {args.module}")
        result = run_specific_test(args.module, verbosity)
        if result is None:
            return 1
        return 0 if result.wasSuccessful() else 1

    else:
        # Run all tests
        print("Discovering and running all tests...")
        result = discover_and_run_tests(pattern=args.pattern, verbosity=verbosity)

        # Print summary
        print("\n" + "=" * 50)
        print("Test Summary:")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")

        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  {test}: {traceback.splitlines()[-1]}")

        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  {test}: {traceback.splitlines()[-1]}")

        return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

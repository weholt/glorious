#!/usr/bin/env python3
"""Test runner script for unit and integration tests."""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(test_type: str, suite: str | None = None, verbose: bool = False) -> int:
    """Run tests based on type and suite.
    
    Args:
        test_type: 'unit' or 'integration'
        suite: For integration tests, the suite name ('all', 'daemon', etc.)
        verbose: Enable verbose output
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    project_root = Path(__file__).parent.parent
    
    # Use uv run pytest to ensure we use dependencies from pyproject.toml
    cmd = ["uv", "run", "pytest"]
    
    if test_type == "unit":
        cmd.extend(["tests/unit", "-v"])
    elif test_type == "integration":
        if suite == "all":
            cmd.extend(["tests/integration", "-v"])
        else:
            # Run specific integration test suite
            cmd.extend([f"tests/integration/test_{suite}_integration.py", "-v"])
    else:
        print(f"Unknown test type: {test_type}", file=sys.stderr)
        return 1
    
    # Add coverage options for unit tests only
    if test_type == "unit":
        cmd.extend([
            "--cov=issue_tracker",
            "--cov-report=term-missing",
            "--cov-fail-under=70",
        ])
    
    # Integration tests need more time for daemon startup/cleanup
    if test_type == "integration":
        cmd.append("--timeout=15")
    else:
        cmd.append("--timeout=5")
    
    if verbose:
        cmd.append("-vv")
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\nTests interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error running tests: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run unit or integration tests")
    parser.add_argument(
        "--unit",
        action="store_true",
        help="Run unit tests"
    )
    parser.add_argument(
        "--integration",
        type=str,
        metavar="SUITE",
        help="Run integration tests (all, daemon, etc.)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    if args.unit:
        exit_code = run_tests("unit", verbose=args.verbose)
    elif args.integration:
        exit_code = run_tests("integration", suite=args.integration, verbose=args.verbose)
    else:
        parser.print_help()
        print("\nError: Specify either --unit or --integration SUITE", file=sys.stderr)
        exit_code = 1
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

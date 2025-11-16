#!/usr/bin/env python3
"""Simple verification that dispose_all_engines is called during integration tests."""

import subprocess
import sys


def main() -> int:
    print("=" * 70)
    print("VERIFICATION: Engine Disposal in Integration Tests")
    print("=" * 70)

    # Run a subset of daemon tests
    print("\nRunning daemon integration tests...")
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/integration/test_daemon_integration.py::TestDaemonLifecycle", "-v", "-s"],
        capture_output=True,
        text=True,
        timeout=60,
    )

    output = result.stdout + result.stderr

    # Check for cleanup message
    if "[CLEANUP] Disposed all database engines" in output:
        print("✅ PASS: dispose_all_engines() IS being called")
        print("\nCleanup message found in output:")
        for line in output.split("\n"):
            if "CLEANUP" in line:
                print(f"  {line.strip()}")
        return 0
    else:
        print("❌ FAIL: dispose_all_engines() NOT being called")
        print("\nSearched output for '[CLEANUP] Disposed all database engines'")
        print("but it was not found.")
        print("\nLast 20 lines of output:")
        for line in output.split("\n")[-20:]:
            if line.strip():
                print(f"  {line}")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.TimeoutExpired:
        print("\n❌ ERROR: Tests timed out")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

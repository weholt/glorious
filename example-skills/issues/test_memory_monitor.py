#!/usr/bin/env python3
"""Monitor memory usage while running integration tests."""

import subprocess
import sys
import time
import gc

# Try to import psutil
try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not available, using /proc/meminfo")


def get_memory_mb():
    """Get current memory usage in MB."""
    if HAS_PSUTIL:
        import psutil as ps

        return ps.virtual_memory().used / 1024 / 1024
    else:
        # Fallback: read from /proc/meminfo
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    # Total - Available = Used (approximate)
                    available = int(line.split()[1]) / 1024  # KB to MB
                    return available
        return 0


def run_test(test_path):
    """Run a single test and return success status."""
    result = subprocess.run(
        ["uv", "run", "pytest", test_path, "-v", "--tb=line"], capture_output=True, text=True, timeout=20
    )
    return result.returncode == 0, result.stdout, result.stderr


def main():
    """Run tests and monitor memory."""
    print("Memory Leak Test - Running 3 Integration Tests")
    print("=" * 70)

    # Tests to run
    tests = [
        "tests/integration/test_issue_lifecycle.py::TestIssueLifecycleWorkflows::test_create_modify_close_reopen",
        "tests/integration/test_issue_lifecycle.py::TestIssueLifecycleWorkflows::test_add_labels_workflow",
        "tests/integration/test_issue_lifecycle.py::TestIssueLifecycleWorkflows::test_set_epic_relationship",
    ]

    # Get baseline
    gc.collect()
    time.sleep(0.5)
    baseline_mem = get_memory_mb()
    print(f"Baseline memory: {baseline_mem:.1f} MB\n")

    results = []

    for i, test in enumerate(tests, 1):
        test_name = test.split("::")[-1]
        print(f"Test {i}/3: {test_name}")
        print("-" * 70)

        try:
            mem_before = get_memory_mb()
            success, stdout, stderr = run_test(test)
            gc.collect()
            time.sleep(0.5)
            mem_after = get_memory_mb()

            delta = mem_after - mem_before
            total_delta = mem_after - baseline_mem

            status = "✓ PASS" if success else "✗ FAIL"
            print(f"  Status: {status}")
            print(f"  Memory before: {mem_before:.1f} MB")
            print(f"  Memory after:  {mem_after:.1f} MB")
            print(f"  Delta: {delta:+.1f} MB")
            print(f"  Total delta from baseline: {total_delta:+.1f} MB")

            if not success:
                print(f"\n  Error output:")
                print(stderr[-500:] if stderr else stdout[-500:])

            results.append({"test": test_name, "success": success, "delta": delta, "total": total_delta})

        except subprocess.TimeoutExpired:
            print(f"  Status: ✗ TIMEOUT")
            results.append({"test": test_name, "success": False, "delta": 0, "total": 0})
        except Exception as e:
            print(f"  Status: ✗ ERROR - {e}")
            results.append({"test": test_name, "success": False, "delta": 0, "total": 0})

        print()

    # Final summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    final_mem = get_memory_mb()
    total_increase = final_mem - baseline_mem

    passed = sum(1 for r in results if r["success"])
    print(f"Tests passed: {passed}/3")
    print(f"Baseline memory: {baseline_mem:.1f} MB")
    print(f"Final memory: {final_mem:.1f} MB")
    print(f"Total increase: {total_increase:+.1f} MB")
    print()

    # Expected: Each test should not leak more than ~50MB
    # 3 tests * 50MB = 150MB max acceptable
    if total_increase > 150:
        print("❌ MEMORY LEAK DETECTED!")
        print(f"   Expected: < 150 MB increase")
        print(f"   Actual: {total_increase:.1f} MB increase")
        return 1
    else:
        print("✅ MEMORY USAGE ACCEPTABLE")
        print(f"   Expected: < 150 MB increase")
        print(f"   Actual: {total_increase:.1f} MB increase")
        return 0 if passed == 3 else 1


if __name__ == "__main__":
    sys.exit(main())

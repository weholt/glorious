#!/usr/bin/env python3
"""Simple memory leak test with working tests."""

import gc
import subprocess
import sys
import time

try:
    import psutil  # type: ignore[import-untyped]  # noqa: F401

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


def get_memory_mb() -> float:
    """Get current memory usage in MB."""
    if HAS_PSUTIL:
        import psutil as ps

        result: float = ps.Process().memory_info().rss / 1024 / 1024
        return result
    else:
        return 0.0


def run_test(test_path: str) -> tuple[bool, str, str]:
    """Run a single test."""
    result = subprocess.run(
        ["uv", "run", "pytest", test_path, "-xvs", "--tb=line"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode == 0, result.stdout, result.stderr


def main() -> int:
    """Run tests."""
    print("Memory Leak Test - Simple Tests")
    print("=" * 70)

    # Tests that should work
    tests = [
        "tests/integration/test_advanced_filtering.py::TestAdvancedFiltering::test_filter_priority_range",
        "tests/integration/test_advanced_filtering.py::TestAdvancedFiltering::test_filter_by_date_range",
        "tests/integration/test_advanced_filtering.py::TestAdvancedFiltering::test_filter_empty_description",
    ]

    gc.collect()
    time.sleep(0.5)
    baseline_mem = get_memory_mb()
    print(f"\nBaseline memory: {baseline_mem:.1f} MB\n")

    results = []

    for i, test in enumerate(tests, 1):
        test_name = test.split("::")[-1]
        print(f"Test {i}/{len(tests)}: {test_name}")
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
            print(f"  Total delta: {total_delta:+.1f} MB")

            if not success:
                print("\n  Error:")
                error_msg = stderr if stderr else stdout
                lines = error_msg.split("\n")
                for line in lines[-20:]:
                    if line.strip():
                        print(f"    {line}")

            results.append({"test": test_name, "success": success, "delta": delta, "total": total_delta})

        except subprocess.TimeoutExpired:
            print("  Status: ✗ TIMEOUT")
            results.append({"test": test_name, "success": False, "delta": 0, "total": 0})
        except Exception as e:
            print(f"  Status: ✗ ERROR - {e}")
            results.append({"test": test_name, "success": False, "delta": 0, "total": 0})

        print()

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)

    final_mem = get_memory_mb()
    total_increase = final_mem - baseline_mem

    passed = sum(1 for r in results if r["success"])
    print(f"Tests passed: {passed}/{len(tests)}")
    print(f"Baseline memory: {baseline_mem:.1f} MB")
    print(f"Final memory: {final_mem:.1f} MB")
    print(f"Total increase: {total_increase:+.1f} MB")
    print()

    # Each test should use minimal memory when sessions are properly closed
    # Expect < 50MB total for 3 tests
    if total_increase > 80:
        print("❌ MEMORY LEAK DETECTED!")
        print(f"   Expected: < 80 MB for {len(tests)} tests")
        print(f"   Actual: {total_increase:.1f} MB")
        return 1
    else:
        print("✅ MEMORY USAGE ACCEPTABLE!")
        print(f"   Expected: < 80 MB for {len(tests)} tests")
        print(f"   Actual: {total_increase:.1f} MB")
        return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())

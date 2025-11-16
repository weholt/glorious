#!/usr/bin/env python3
"""Test memory leak with integration_cli_runner fixture tests."""

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

        result: float = ps.virtual_memory().used / 1024 / 1024
        return result
    else:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    available: float = int(line.split()[1]) / 1024
                    return available
        return 0.0


def run_test(test_path: str) -> tuple[bool, str, str]:
    """Run a single test."""
    result = subprocess.run(
        ["uv", "run", "pytest", test_path, "-v", "--tb=line"], capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0, result.stdout, result.stderr


def main() -> int:
    """Run tests that use integration_cli_runner fixture."""
    print("Memory Leak Test - integration_cli_runner Fixture")
    print("=" * 70)
    print("These tests create temporary workspaces with unique DB paths")
    print("Each should dispose engines properly to prevent leaks")
    print("=" * 70)

    # Tests that use integration_cli_runner fixture
    tests = [
        "tests/integration/test_advanced_filtering.py::TestAdvancedFiltering::test_filter_priority_range",
        "tests/integration/test_agent_workflows.py::TestAgentWorkflows::test_agent_workflow_claim_task",
        "tests/integration/test_bulk_operations.py::TestBulkOperations::test_bulk_close_multiple_issues",
    ]

    gc.collect()
    time.sleep(0.5)
    baseline_mem = get_memory_mb()
    print(f"\nBaseline memory: {baseline_mem:.1f} MB\n")

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
    print(f"Tests passed: {passed}/3")
    print(f"Baseline memory: {baseline_mem:.1f} MB")
    print(f"Final memory: {final_mem:.1f} MB")
    print(f"Total increase: {total_increase:+.1f} MB")
    print()

    # With the fix: each test should use ~20-30MB max
    # 3 tests * 30MB = 90MB acceptable
    # Without fix: 3 tests * 50MB+ = 150MB+ leaked
    if total_increase > 150:
        print("❌ MEMORY LEAK DETECTED!")
        print("   Without fix, expected: > 150 MB")
        print("   With fix, expected: < 100 MB")
        print(f"   Actual: {total_increase:.1f} MB")
        return 1
    else:
        print("✅ MEMORY LEAK FIXED!")
        print("   Without fix: would leak > 150 MB")
        print("   With fix: < 100 MB is expected")
        print(f"   Actual: {total_increase:.1f} MB")
        return 0 if passed == 3 else 1


if __name__ == "__main__":
    sys.exit(main())

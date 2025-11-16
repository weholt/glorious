#!/usr/bin/env python3
"""Verify that the engine leak fix works correctly."""

import os
import sys
import tempfile
from pathlib import Path


def test_engine_registry():
    """Test that engines are tracked and can be disposed."""
    # Import after changing dir to avoid polluting real workspace
    from issue_tracker.cli.dependencies import get_engine, dispose_all_engines, _engine_registry

    print("Test 1: Creating engines for different DB URLs")
    print("=" * 70)

    # Create temp dirs
    temp_dirs = []
    engines = []

    for i in range(3):
        tmp_dir = Path(tempfile.mkdtemp())
        temp_dirs.append(tmp_dir)

        # Set environment to point to this temp dir
        os.environ["ISSUES_FOLDER"] = str(tmp_dir / ".issues")

        # Clear cache so get_db_url recalculates
        from issue_tracker.cli.dependencies import get_db_url

        get_db_url.cache_clear()

        # Get engine
        engine = get_engine()
        engines.append(engine)

        print(f"  Created engine {i + 1}: {engine.url}")

    print(f"\nEngines in registry: {len(_engine_registry)}")
    print(f"Expected: 3")

    assert len(_engine_registry) == 3, f"Expected 3 engines, got {len(_engine_registry)}"

    # Verify each engine is unique
    assert len(set(id(e) for e in engines)) == 3, "Engines should be unique instances"

    # Verify registry contains all URLs
    for engine in engines:
        url_str = str(engine.url)
        assert url_str in _engine_registry, f"URL {url_str} not in registry"

    print("✓ All engines tracked correctly\n")

    print("Test 2: Disposing all engines")
    print("=" * 70)

    dispose_all_engines()

    print(f"Engines in registry after dispose: {len(_engine_registry)}")
    print(f"Expected: 0")

    assert len(_engine_registry) == 0, f"Registry should be empty, has {len(_engine_registry)}"

    print("✓ All engines disposed and registry cleared\n")

    print("Test 3: Getting engine after dispose creates new one")
    print("=" * 70)

    # Get engine again
    os.environ["ISSUES_FOLDER"] = str(temp_dirs[0] / ".issues")
    get_db_url.cache_clear()

    new_engine = get_engine()
    print(f"New engine created: {new_engine.url}")
    print(f"Engines in registry: {len(_engine_registry)}")

    assert len(_engine_registry) == 1, "Should have one new engine"
    assert new_engine is not engines[0], "Should be a NEW engine instance"

    print("✓ New engine created correctly\n")

    # Final cleanup
    dispose_all_engines()

    # Clean up temp dirs
    import shutil

    for tmp_dir in temp_dirs:
        try:
            shutil.rmtree(tmp_dir)
        except:
            pass

    print("=" * 70)
    print("✅ ALL TESTS PASSED - Engine leak fix is working!")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(test_engine_registry())
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

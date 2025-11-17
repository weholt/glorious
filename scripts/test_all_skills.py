#!/usr/bin/env python3
"""
Run unit tests for all skills in the skills/ directory.

Each skill is a separate project with its own pyproject.toml and tests/ directory.
This script discovers all skills and runs their tests independently.
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def find_skill_directories(skills_dir: Path) -> list[Path]:
    """Find all skill directories that have a pyproject.toml and tests directory."""
    skills = []

    if not skills_dir.exists():
        print(f"Error: Skills directory not found: {skills_dir}")
        return skills

    for item in sorted(skills_dir.iterdir()):
        if not item.is_dir():
            continue

        # Skip hidden directories and __pycache__
        if item.name.startswith(".") or item.name == "__pycache__":
            continue

        # Check if it has a pyproject.toml (indicates it's a Python project)
        pyproject = item / "pyproject.toml"
        tests_dir = item / "tests"

        if pyproject.exists() and tests_dir.exists():
            skills.append(item)

    return skills


def run_tests_for_skill(skill_dir: Path, project_root: Path) -> tuple[str, bool, str]:
    """
    Run tests for a single skill using pytest.

    Args:
        skill_dir: Path to the skill directory
        project_root: Path to the project root (for installing glorious agents framework)

    Returns:
        Tuple of (skill_name, success, output)
    """
    skill_name = skill_dir.name

    print(f"\n{'=' * 80}")
    print(f"Running tests for: {skill_name}")
    print(f"{'=' * 80}")

    try:
        # Sync dependencies first
        print(f"Syncing dependencies for {skill_name}...")
        sync_result = subprocess.run(
            ["uv", "sync"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for sync
        )

        if sync_result.returncode != 0:
            print(f"Warning: uv sync failed for {skill_name}")
            print(sync_result.stderr)

        # Install glorious agents framework from project root
        print(f"Installing glorious agents framework for {skill_name}...")
        install_result = subprocess.run(
            ["uv", "pip", "install", str(project_root)],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout for install
        )

        if install_result.returncode != 0:
            print(f"Warning: Installing glorious agents framework failed for {skill_name}")
            print(install_result.stderr)

        # Run pytest in the skill directory
        # Use -v for verbose output, --tb=short for shorter tracebacks
        result = subprocess.run(
            ["uv", "run", "pytest", "-v", "--tb=short"],
            cwd=skill_dir,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout per skill
        )

        # Print the output
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        success = result.returncode == 0

        if success:
            print(f"✓ {skill_name}: PASSED")
        else:
            print(f"✗ {skill_name}: FAILED")

        return skill_name, success, result.stdout + result.stderr

    except subprocess.TimeoutExpired:
        error_msg = f"✗ {skill_name}: TIMEOUT (exceeded 5 minutes)"
        print(error_msg)
        return skill_name, False, error_msg

    except Exception as e:
        error_msg = f"✗ {skill_name}: ERROR - {str(e)}"
        print(error_msg)
        return skill_name, False, error_msg


def main():
    """Main entry point."""
    # Get the project root (parent of scripts/)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    skills_dir = project_root / "skills"

    print(f"Scanning for skills in: {skills_dir}")

    # Find all skills
    skills = find_skill_directories(skills_dir)

    if not skills:
        print("No skills with tests found!")
        return 1

    print(f"\nFound {len(skills)} skill(s) with tests:")
    for skill in skills:
        print(f"  - {skill.name}")

    # Run tests for each skill
    results = []
    for skill_dir in skills:
        result = run_tests_for_skill(skill_dir, project_root)
        results.append(result)

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")

    passed = [r for r in results if r[1]]
    failed = [r for r in results if not r[1]]

    print(f"\nTotal: {len(results)} skill(s)")
    print(f"Passed: {len(passed)} skill(s)")
    print(f"Failed: {len(failed)} skill(s)")

    if passed:
        print("\n✓ Passed:")
        for name, _, _ in passed:
            print(f"  - {name}")

    if failed:
        print("\n✗ Failed:")
        for name, _, _ in failed:
            print(f"  - {name}")

    # Exit with error code if any tests failed
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

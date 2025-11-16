#!/usr/bin/env python3
"""Release automation script for Glorious Agents.

This script automates the release process:
1. Validates version number
2. Runs tests
3. Builds package
4. Creates git tag
5. Provides instructions for GitHub release
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("❌ pyproject.toml not found")
        sys.exit(1)
    
    content = pyproject.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print("❌ Could not find version in pyproject.toml")
        sys.exit(1)
    
    return match.group(1)


def validate_version(version: str) -> bool:
    """Validate semantic version format."""
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
    return bool(re.match(pattern, version))


def run_tests() -> bool:
    """Run the test suite."""
    print("\n📋 Running tests...")
    result = run_command(["uv", "run", "pytest", "--cov"], check=False)
    return result.returncode == 0


def run_quality_checks() -> bool:
    """Run code quality checks."""
    print("\n🔍 Running quality checks...")
    
    # Format check
    print("  • Checking code formatting...")
    result = run_command(["uv", "run", "ruff", "format", "--check", "."], check=False)
    if result.returncode != 0:
        print("    ❌ Format check failed")
        return False
    print("    ✓ Format check passed")
    
    # Linting
    print("  • Running linter...")
    result = run_command(["uv", "run", "ruff", "check", "."], check=False)
    if result.returncode != 0:
        print("    ❌ Linting failed")
        return False
    print("    ✓ Linting passed")
    
    # Type checking
    print("  • Running type checker...")
    result = run_command(["uv", "run", "mypy", "src"], check=False)
    if result.returncode != 0:
        print("    ❌ Type checking failed")
        return False
    print("    ✓ Type checking passed")
    
    return True


def build_package() -> bool:
    """Build the distribution packages."""
    print("\n📦 Building package...")
    
    # Clean previous builds
    for path in Path("dist").glob("*"):
        path.unlink()
    
    result = run_command(
        ["uv", "tool", "run", "--from", "build", "pyproject-build"],
        check=False
    )
    
    if result.returncode != 0:
        print("❌ Build failed")
        return False
    
    # List built files
    print("\n  Built files:")
    for file in Path("dist").glob("*"):
        size = file.stat().st_size / 1024
        print(f"    • {file.name} ({size:.1f} KB)")
    
    return True


def verify_package() -> bool:
    """Verify the built package."""
    print("\n✅ Verifying package...")
    
    # Check wheel contents
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        print("❌ No wheel file found")
        return False
    
    wheel = wheel_files[0]
    result = run_command(
        ["python3", "-m", "zipfile", "-l", str(wheel)],
        check=False
    )
    
    if "skills/" not in result.stdout:
        print("❌ Skills folder not found in package!")
        return False
    
    print("  ✓ Skills folder included in package")
    
    # Count skills
    skill_count = result.stdout.count("skill.json")
    print(f"  ✓ {skill_count} skills found in package")
    
    return True


def create_git_tag(version: str, dry_run: bool = False) -> bool:
    """Create a git tag for the release."""
    print(f"\n🏷️  Creating git tag v{version}...")
    
    tag = f"v{version}"
    
    # Check if tag already exists
    result = run_command(["git", "tag", "-l", tag], check=False)
    if result.stdout.strip():
        print(f"❌ Tag {tag} already exists")
        return False
    
    if dry_run:
        print(f"  [DRY RUN] Would create tag: {tag}")
        return True
    
    # Create tag
    result = run_command(
        ["git", "tag", "-a", tag, "-m", f"Release {version}"],
        check=False
    )
    
    if result.returncode != 0:
        print(f"❌ Failed to create tag: {result.stderr}")
        return False
    
    print(f"  ✓ Created tag {tag}")
    return True


def print_next_steps(version: str, dry_run: bool = False):
    """Print instructions for completing the release."""
    print("\n" + "=" * 70)
    print("✅ Release preparation complete!")
    print("=" * 70)
    
    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes were made")
    
    print(f"\n📝 Next steps to publish v{version}:\n")
    print("1. Push the tag to GitHub:")
    print(f"   git push origin v{version}\n")
    print("2. Create a GitHub release:")
    print(f"   • Go to: https://github.com/weholt/glorious-agents/releases/new")
    print(f"   • Tag: v{version}")
    print(f"   • Title: Release {version}")
    print("   • Add release notes describing changes\n")
    print("3. GitHub Actions will automatically:")
    print("   • Run tests")
    print("   • Build package")
    print("   • Publish to PyPI using trusted publishing\n")
    print("4. Verify on PyPI:")
    print("   https://pypi.org/project/glorious-agents/\n")
    print("=" * 70)


def main():
    """Main release workflow."""
    parser = argparse.ArgumentParser(description="Release automation for Glorious Agents")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without making changes"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests (not recommended)"
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip quality checks (not recommended)"
    )
    
    args = parser.parse_args()
    
    print("🚀 Starting release process for Glorious Agents\n")
    
    # Get version
    version = get_current_version()
    print(f"📌 Current version: {version}")
    
    if not validate_version(version):
        print("❌ Invalid version format. Use semver: X.Y.Z")
        sys.exit(1)
    
    # Run tests
    if not args.skip_tests:
        if not run_tests():
            print("\n❌ Tests failed! Fix errors before releasing.")
            sys.exit(1)
        print("✓ Tests passed")
    else:
        print("⚠️  Skipping tests")
    
    # Run quality checks
    if not args.skip_quality:
        if not run_quality_checks():
            print("\n❌ Quality checks failed! Fix errors before releasing.")
            sys.exit(1)
        print("✓ Quality checks passed")
    else:
        print("⚠️  Skipping quality checks")
    
    # Build package
    if not build_package():
        print("\n❌ Build failed!")
        sys.exit(1)
    print("✓ Package built")
    
    # Verify package
    if not verify_package():
        print("\n❌ Package verification failed!")
        sys.exit(1)
    print("✓ Package verified")
    
    # Create git tag
    if not create_git_tag(version, dry_run=args.dry_run):
        print("\n❌ Failed to create git tag")
        sys.exit(1)
    
    # Print next steps
    print_next_steps(version, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

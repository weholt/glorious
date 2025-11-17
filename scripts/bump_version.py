#!/usr/bin/env python3
"""Bump version across the project.

This script automatically bumps the version number in pyproject.toml
following semantic versioning (semver) conventions.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def get_current_version(pyproject_path: Path = Path("pyproject.toml")) -> str:
    """Get current version from pyproject.toml."""
    if not pyproject_path.exists():
        print(f"❌ {pyproject_path} not found")
        sys.exit(1)
    
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        print(f"❌ Could not find version in {pyproject_path}")
        sys.exit(1)
    
    return match.group(1)


def parse_version(version: str) -> tuple[int, int, int, str]:
    """Parse a semantic version string into components."""
    pattern = r'^(\d+)\.(\d+)\.(\d+)(-[a-zA-Z0-9]+)?$'
    match = re.match(pattern, version)
    if not match:
        print(f"❌ Invalid version format: {version}")
        sys.exit(1)
    
    major, minor, patch, prerelease = match.groups()
    return int(major), int(minor), int(patch), prerelease or ""


def bump_version(version: str, part: str) -> str:
    """Bump the specified part of the version."""
    major, minor, patch, prerelease = parse_version(version)
    
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        print(f"❌ Invalid version part: {part}. Use major, minor, or patch.")
        sys.exit(1)


def update_version_in_file(file_path: Path, old_version: str, new_version: str) -> bool:
    """Update version in a file."""
    if not file_path.exists():
        return False
    
    content = file_path.read_text()
    old_pattern = f'version = "{old_version}"'
    new_pattern = f'version = "{new_version}"'
    
    if old_pattern not in content:
        return False
    
    updated = content.replace(old_pattern, new_pattern)
    file_path.write_text(updated)
    return True


def generate_changelog_entry(version: str, dry_run: bool = False) -> None:
    """Generate changelog entry from git commits since last tag."""
    print("\n📝 Generating changelog...")
    
    # Get last tag
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
        check=False
    )
    
    if result.returncode == 0:
        last_tag = result.stdout.strip()
        print(f"  Last tag: {last_tag}")
        
        # Get commits since last tag
        result = subprocess.run(
            ["git", "log", f"{last_tag}..HEAD", "--oneline"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            commits = result.stdout.strip().split('\n')
            print(f"\n  Changes since {last_tag}:")
            for commit in commits:
                print(f"    • {commit}")
        else:
            print("  No commits since last tag")
    else:
        print("  No previous tags found")


def update_changelog(version: str, dry_run: bool = False) -> bool:
    """Update CHANGELOG.md with new version."""
    changelog_path = Path("CHANGELOG.md")
    
    if not changelog_path.exists():
        print("\n📄 Creating CHANGELOG.md...")
        if dry_run:
            print("  [DRY RUN] Would create CHANGELOG.md")
            return True
        
        changelog_content = f"""# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [{version}] - {get_current_date()}

### Added
- Initial release

"""
        changelog_path.write_text(changelog_content)
        print(f"  ✓ Created CHANGELOG.md with version {version}")
        return True
    
    content = changelog_path.read_text()
    
    # Add new version section after [Unreleased]
    unreleased_pattern = r'## \[Unreleased\]\s*\n'
    new_section = f"""## [Unreleased]

## [{version}] - {get_current_date()}

### Added
- 

### Changed
- 

### Fixed
- 

"""
    
    if dry_run:
        print("\n  [DRY RUN] Would update CHANGELOG.md:")
        print(f"    • Add section for version {version}")
        return True
    
    updated = re.sub(unreleased_pattern, new_section, content, count=1)
    changelog_path.write_text(updated)
    print(f"  ✓ Updated CHANGELOG.md with version {version}")
    return True


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def main():
    """Main version bump workflow."""
    parser = argparse.ArgumentParser(
        description="Bump version for Glorious Agents",
        epilog="Example: python scripts/bump_version.py minor"
    )
    parser.add_argument(
        "part",
        choices=["major", "minor", "patch"],
        help="Part of version to bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--no-changelog",
        action="store_true",
        help="Skip changelog update"
    )
    
    args = parser.parse_args()
    
    print("🔢 Version Bump Tool for Glorious Agents\n")
    
    # Get current version
    current_version = get_current_version()
    print(f"📌 Current version: {current_version}")
    
    # Calculate new version
    new_version = bump_version(current_version, args.part)
    print(f"📈 New version: {new_version} ({args.part} bump)")
    
    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    
    # Update pyproject.toml
    print("\n📝 Updating version in files...")
    pyproject = Path("pyproject.toml")
    
    if args.dry_run:
        print(f"  [DRY RUN] Would update {pyproject}")
    else:
        if update_version_in_file(pyproject, current_version, new_version):
            print(f"  ✓ Updated {pyproject}")
        else:
            print(f"  ❌ Failed to update {pyproject}")
            sys.exit(1)
    
    # Generate changelog summary
    if not args.no_changelog:
        generate_changelog_entry(new_version, dry_run=args.dry_run)
        update_changelog(new_version, dry_run=args.dry_run)
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ Version bump complete!")
    print("=" * 70)
    
    if args.dry_run:
        print("\n⚠️  This was a DRY RUN - No changes were made")
        print("   Run without --dry-run to apply changes")
    else:
        print(f"\n✓ Version bumped from {current_version} to {new_version}")
        print("\n📝 Next steps:")
        print("1. Review and update CHANGELOG.md with actual changes")
        print("2. Commit the version bump:")
        print("   git add pyproject.toml CHANGELOG.md")
        print(f"   git commit -m 'chore: bump version to {new_version}'")
        print("3. Run the release script:")
        print("   python scripts/release.py")
    
    print("=" * 70)


if __name__ == "__main__":
    main()

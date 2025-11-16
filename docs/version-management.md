# Version Management Guide

This guide explains how to manage versions in Glorious Agents.

## Overview

Glorious Agents uses **Semantic Versioning** (semver):
- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backwards compatible
- **Patch** (0.0.1): Bug fixes, backwards compatible

## Automated Version Bumping

### Basic Usage

```bash
# Bump patch version (0.1.0 → 0.1.1)
python scripts/bump_version.py patch

# Bump minor version (0.1.0 → 0.2.0)
python scripts/bump_version.py minor

# Bump major version (0.1.0 → 1.0.0)
python scripts/bump_version.py major
```

### Preview Changes (Dry Run)

```bash
# See what would change without making changes
python scripts/bump_version.py --dry-run minor
```

### Skip Changelog

```bash
# Update version only, skip changelog
python scripts/bump_version.py --no-changelog patch
```

## What Gets Updated

When you bump the version, the script:

1. ✓ Updates `version` in `pyproject.toml`
2. ✓ Creates/updates `CHANGELOG.md` with new version section
3. ✓ Lists recent git commits for your reference
4. ✓ Provides next steps for committing and releasing

## Integrated Release Workflow

### Quick Release (Recommended)

Bump version and release in one command:

```bash
# Bump patch and run full release checks
python scripts/release.py --bump patch

# This will:
# 1. Bump version
# 2. Update changelog
# 3. Run tests
# 4. Run quality checks
# 5. Build package
# 6. Verify package contents
# 7. Create git tag
# 8. Show instructions for GitHub release
```

### Manual Workflow

If you prefer more control:

```bash
# Step 1: Bump version
python scripts/bump_version.py minor

# Step 2: Review and edit CHANGELOG.md
vim CHANGELOG.md

# Step 3: Commit version bump
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"

# Step 4: Run release script
python scripts/release.py

# Step 5: Follow instructions to push tag and create GitHub release
```

## Changelog Management

The script automatically creates/updates `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format.

### Example Changelog Entry

```markdown
## [Unreleased]

## [0.2.0] - 2025-11-16

### Added
- New skill for code analysis
- Support for Python 3.12

### Changed
- Improved database performance
- Updated CLI help text

### Fixed
- Bug in skill loading
- Memory leak in daemon
```

### Manual Editing

After running the bump script, you should:

1. Review the auto-generated changelog entry
2. Add specific details about changes
3. Organize changes into Added/Changed/Fixed/Removed sections
4. Remove empty sections

## Version Naming Conventions

### When to Bump

- **Patch (0.1.0 → 0.1.1)**
  - Bug fixes
  - Documentation updates
  - Performance improvements
  - No API changes

- **Minor (0.1.0 → 0.2.0)**
  - New features
  - New skills
  - New CLI commands
  - Backwards compatible

- **Major (0.9.0 → 1.0.0)**
  - Breaking API changes
  - Removed deprecated features
  - Incompatible changes
  - First stable release

### Pre-release Versions

For pre-release versions, manually edit `pyproject.toml`:

```toml
version = "1.0.0-alpha.1"  # Alpha release
version = "1.0.0-beta.1"   # Beta release
version = "1.0.0-rc.1"     # Release candidate
```

## Git Tags

Version tags should always use the `v` prefix:

```bash
v0.1.0
v0.2.0
v1.0.0
```

The scripts handle this automatically.

## Troubleshooting

### "Could not find version in pyproject.toml"

Make sure `pyproject.toml` has a version line:
```toml
[project]
version = "0.1.0"
```

### "Invalid version format"

Version must follow semantic versioning: `X.Y.Z`
- ✓ Valid: `0.1.0`, `1.2.3`, `2.0.0-beta.1`
- ✗ Invalid: `v0.1`, `1.2`, `0.1.0.0`

### Git Tag Already Exists

If the tag already exists:
```bash
# Delete local tag
git tag -d v0.2.0

# Delete remote tag (careful!)
git push origin --delete v0.2.0

# Then bump again
python scripts/bump_version.py minor
```

## Best Practices

1. **Always use the bump script** - Don't manually edit version numbers
2. **Update changelog** - Add meaningful descriptions, not just commit messages
3. **One version per release** - Don't skip versions
4. **Test before releasing** - Run `python scripts/release.py --dry-run` first
5. **Follow semver** - Be consistent with version increments

## Examples

### Bug Fix Release

```bash
# Fix a bug
git commit -m "fix: resolve database connection issue"

# Bump patch version
python scripts/bump_version.py patch

# Update changelog with fix details
vim CHANGELOG.md

# Commit and release
git add .
git commit -m "chore: bump version to 0.1.1"
python scripts/release.py
```

### Feature Release

```bash
# Add a new feature
git commit -m "feat: add new caching skill"

# Bump minor version
python scripts/bump_version.py minor

# Update changelog with feature details
vim CHANGELOG.md

# Commit and release
git add .
git commit -m "chore: bump version to 0.2.0"
python scripts/release.py
```

### Quick Hotfix

```bash
# Fix critical bug
git commit -m "fix: critical security issue"

# One-command release
python scripts/release.py --bump patch

# Follow instructions to push and release
```

## See Also

- [Releasing Guide](../RELEASING.md) - Complete release process
- [Semantic Versioning](https://semver.org/) - Version naming specification
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format

# Version Scheme

This document defines the official versioning scheme for Glorious Agents.

## Overview

Glorious Agents follows **[Semantic Versioning 2.0.0](https://semver.org/)** (semver).

Given a version number `MAJOR.MINOR.PATCH`, increment the:
- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backward compatible manner
- **PATCH** version when you make backward compatible bug fixes

## Version Format

```
MAJOR.MINOR.PATCH[-PRERELEASE][+BUILDMETADATA]
```

### Examples

- `1.0.0` - First stable release
- `0.2.1` - Pre-1.0 minor version 2, patch 1
- `2.3.0-alpha.1` - Pre-release alpha version
- `2.3.0-beta.2` - Pre-release beta version
- `2.3.0-rc.1` - Release candidate

## Versioning Rules

### Pre-1.0 Development Versions (0.x.x)

During initial development (before 1.0.0):
- **Minor** versions (0.x.0) MAY introduce breaking changes
- **Patch** versions (0.x.y) SHOULD be backward compatible
- Public API is not considered stable

**Current Status:** Glorious Agents is in pre-1.0 development.

### Post-1.0 Stable Versions (1.x.x+)

Once version 1.0.0 is released:
- **Major** version MUST be incremented for breaking changes
- **Minor** version MUST be incremented for new features
- **Patch** version MUST be incremented for bug fixes only

## When to Bump Versions

### MAJOR Version (X.0.0)

Increment when making **incompatible** changes:

- Breaking changes to public APIs
- Removing deprecated features
- Changing data formats that break existing databases
- Changing configuration file formats incompatibly
- Renaming or removing CLI commands
- Removing or renaming public modules, classes, or functions

**Examples:**
- Changing function signatures in a breaking way
- Removing a skill or CLI command
- Changing database schema incompatibly

### MINOR Version (0.X.0)

Increment when adding **backward-compatible** functionality:

- Adding new skills
- Adding new CLI commands or options
- Adding new public APIs or functions
- Deprecating features (but not removing them)
- Adding new optional dependencies
- Substantial performance improvements

**Examples:**
- Adding a new skill like `glorious-security`
- Adding new CLI flags to existing commands
- Adding new event types or handlers
- Adding database tables (without changing existing ones)

### PATCH Version (0.0.X)

Increment when making **backward-compatible** bug fixes:

- Fixing bugs
- Performance improvements
- Documentation updates
- Security patches (if backward compatible)
- Internal refactoring (no API changes)
- Dependency updates (for bug fixes)

**Examples:**
- Fixing a crash in the notes skill
- Correcting typos in help text
- Improving query performance
- Fixing memory leaks

## Pre-release Versions

Pre-release versions are used for testing before official releases.

### Format

```
X.Y.Z-TYPE.NUMBER
```

Where:
- `TYPE` is one of: `alpha`, `beta`, `rc` (release candidate)
- `NUMBER` is an incrementing integer starting from 1

### Types

1. **Alpha** (`-alpha.N`)
   - Feature incomplete
   - May be unstable
   - For early testing by developers

2. **Beta** (`-beta.N`)
   - Feature complete
   - May have bugs
   - For testing by early adopters

3. **Release Candidate** (`-rc.N`)
   - Feature complete and tested
   - No known critical bugs
   - Final testing before release

### Precedence

Versions are compared in this order:
```
1.0.0-alpha.1 < 1.0.0-alpha.2 < 1.0.0-beta.1 < 1.0.0-rc.1 < 1.0.0
```

## Version Sources

The version number is stored in multiple locations:

1. **Primary Source:** `pyproject.toml`
   ```toml
   [project]
   version = "0.1.0"
   ```

2. **Documentation:** Version badges in `README.md`
3. **Git Tags:** Created during release process (format: `vX.Y.Z`)
4. **Changelog:** `CHANGELOG.md` tracks version history

### Version Synchronization

All version references MUST be kept in sync. The automated version bump script (`scripts/bump_version.py`) handles this.

## Automated Version Bumping

### Using the Bump Script

```bash
# Bump patch version (0.1.0 → 0.1.1)
python scripts/bump_version.py patch

# Bump minor version (0.1.0 → 0.2.0)
python scripts/bump_version.py minor

# Bump major version (0.1.0 → 1.0.0)
python scripts/bump_version.py major

# Preview changes without applying them
python scripts/bump_version.py --dry-run minor
```

The script automatically:
- Updates version in `pyproject.toml`
- Creates or updates `CHANGELOG.md`
- Lists recent commits for reference
- Provides next steps for committing and releasing

### Manual Version Changes

**DO NOT** manually edit version numbers. Always use the bump script to ensure:
- All files are updated consistently
- Changelog is updated
- Semantic versioning rules are followed

## Version History

All version changes MUST be documented in `CHANGELOG.md` following the [Keep a Changelog](https://keepachangelog.com/) format.

### Changelog Format

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes to existing functionality

### Deprecated
- Features marked for removal

### Removed
- Features removed in this release

### Fixed
- Bug fixes

### Security
- Security fixes
```

## Release Process

1. **Bump version** using the script
2. **Update CHANGELOG.md** with specific changes
3. **Commit changes**
4. **Run release script** (`python scripts/release.py`)
5. **Create and push Git tag** (format: `vX.Y.Z`)
6. **Create GitHub release**
7. **Automated publishing** to PyPI via GitHub Actions

See [RELEASING.md](./RELEASING.md) for complete release instructions.

## Version Compatibility

### Python Version

Glorious Agents requires **Python ≥3.12**.

### Skill Versions

Skills have independent versions but SHOULD match the framework's major version:

- Framework 0.x.x → Skills 0.x.x (pre-1.0)
- Framework 1.x.x → Skills 1.x.x (stable)

Skills MAY use different minor/patch versions.

### Dependency Versions

Dependencies use flexible version constraints in `pyproject.toml`:

```toml
dependencies = [
    "typer>=0.12.0",      # Allows 0.12.x and 0.13.x
    "rich>=13.7.0",       # Allows 13.7.x and 13.8.x
]
```

## Breaking Change Policy

### Before 1.0.0

Breaking changes are allowed in minor versions (0.x.0) but SHOULD be:
- Clearly documented in CHANGELOG.md
- Announced in release notes
- Provided with migration guides when significant

### After 1.0.0

Breaking changes MUST:
- Only occur in major versions (X.0.0)
- Be documented with clear migration paths
- Provide deprecation warnings in the previous major version when possible
- Include automated migration tools when feasible

## Deprecation Policy

When deprecating features:

1. Mark feature as deprecated in code with warnings
2. Document deprecation in CHANGELOG.md
3. Specify removal version (next major release)
4. Keep deprecated features for at least one minor version

Example:
```python
import warnings

def deprecated_function():
    warnings.warn(
        "deprecated_function is deprecated and will be removed in v2.0.0. "
        "Use new_function instead.",
        DeprecationWarning,
        stacklevel=2
    )
```

## Version Queries

### Getting Current Version

```bash
# From command line
agent version

# From Python
from glorious_agents import __version__
print(__version__)

# From pyproject.toml
grep 'version = ' pyproject.toml
```

### Comparing Versions

The framework includes version comparison utilities:

```python
from glorious_agents.core.loader import parse_version, check_version_constraint

# Parse version
major, minor, patch = parse_version("1.2.3")

# Check constraints
check_version_constraint("1.2.3", ">=1.2.0")  # True
check_version_constraint("1.2.3", "^1.2.0")   # True (caret)
check_version_constraint("1.2.3", "~1.2.0")   # True (tilde)
```

## Best Practices

1. **Always use the bump script** - Don't manually edit versions
2. **Update CHANGELOG.md** - Document what changed in each version
3. **One version per release** - Don't skip version numbers
4. **Test before releasing** - Use `--dry-run` mode first
5. **Follow semver strictly** - Be consistent with version increments
6. **Tag releases** - Always create Git tags for releases
7. **Write clear release notes** - Help users understand changes

## Related Documentation

- [Version Management Guide](./docs/version-management.md) - Detailed usage instructions
- [Releasing Guide](./RELEASING.md) - Complete release process
- [Semantic Versioning Spec](https://semver.org/) - Official semver specification
- [Keep a Changelog](https://keepachangelog.com/) - Changelog format guidelines

## Version Scheme Updates

This document is versioned along with the project. When the version scheme changes:

1. Update this document
2. Announce changes in CHANGELOG.md
3. Provide migration guidance if needed

---

**Last Updated:** 2025-11-18  
**Document Version:** 1.0  
**Applies to:** Glorious Agents ≥0.1.0

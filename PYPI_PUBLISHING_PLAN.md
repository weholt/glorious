# Glorious Agents - PyPI Publishing Plan

> **Created:** 2025-11-16  
> **Status:** Planning Phase  
> **Goal:** Publish glorious-agents and all skills to PyPI with proper packaging

## Overview

This plan outlines the steps needed to publish the glorious-agents framework and all individual skills to PyPI. The publishing system will ensure skills are properly included, versioned, and installable from PyPI.

## Critical Issues

### Skills Packaging Architecture

Currently, glorious-agents has a **unique architecture** where:
- Main package: `glorious-agents` (core framework)
- Skills are in: `src/glorious_agents/skills/` directory
- Each skill has its own `pyproject.toml` as a separate package
- Skills can be installed individually or via extras

**Decision needed:** Should skills be:
1. **Bundled** with main package (simpler for users)
2. **Separate** packages on PyPI (more flexible)
3. **Hybrid** approach (core skills bundled, optional skills separate)

## Issues Created

### High Priority

#### issue-e12df6: Setup PyPI publishing infrastructure
**Priority:** 🟠 High  
**Labels:** infrastructure, publishing, pypi

Setup the infrastructure for publishing glorious-agents to PyPI:
1. Configure pyproject.toml for publishing
2. Setup GitHub Actions workflow for releases
3. Create release checklist
4. Test publishing to TestPyPI
5. Document release process

#### issue-72a4ad: Configure package data to include skills folder ⚠️ CRITICAL
**Priority:** 🟠 High  
**Labels:** critical, packaging, pypi

Ensure skills folder is properly included in published package:
1. Add package data configuration to pyproject.toml
2. Verify skills/ directory structure is preserved
3. Test that installed package includes all skills
4. Update build configuration if needed

**Note:** This is critical to ensure skills work after `pip install glorious-agents`

### Medium Priority

#### issue-834b66: Create individual skill packages for PyPI
**Priority:** 🟡 Medium  
**Labels:** packaging, pypi, skills

Publish individual skills as separate PyPI packages:
1. Review skill pyproject.toml files
2. Ensure proper dependencies
3. Create publishing workflow for skills
4. Test skill installation from PyPI
5. Update main package to use PyPI skill versions

#### issue-45a268: Setup automated version management
**Priority:** 🟡 Medium  
**Labels:** automation, publishing, versioning

Implement automated version management:
1. Setup semantic versioning
2. Create version bump scripts
3. Automate changelog generation
4. Tag releases automatically
5. Update version in all skill packages

#### issue-502559: Create release automation script
**Priority:** 🟡 Medium  
**Labels:** automation, publishing, pypi

Create scripts/release.py to automate release process:
1. Version validation
2. Build package
3. Run tests
4. Publish to PyPI
5. Create GitHub release
6. Update documentation

#### issue-1437b2: Setup PyPI trusted publishing with GitHub Actions
**Priority:** 🟡 Medium  
**Labels:** github-actions, publishing, pypi, security

Configure trusted publishing for secure releases:
1. Setup PyPI trusted publisher
2. Configure GitHub Actions OIDC
3. Remove need for API tokens
4. Document secure publishing process
5. Test trusted publishing workflow

#### issue-5deaf6: Create pre-release testing workflow
**Priority:** 🟡 Medium  
**Labels:** ci, publishing, testing

Create comprehensive pre-release testing:
1. Fresh install testing
2. Test all skills load correctly
3. Test CLI commands
4. Run full test suite
5. Test on multiple Python versions

### Low Priority

#### issue-23f275: Add PyPI badges and metadata to README
**Priority:** 🟢 Low  
**Labels:** documentation, pypi

Update README with PyPI information:
1. Add PyPI version badge
2. Add download stats badge
3. Update installation instructions for PyPI
4. Add links to package pages
5. Document skill installation from PyPI

## Implementation Plan

### Phase 1: Core Package Publishing (High Priority)

**Goal:** Get the main `glorious-agents` package on PyPI

#### Step 1: Configure pyproject.toml (issue-e12df6, issue-72a4ad)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/glorious_agents"]
include = [
    "src/glorious_agents/**/*.py",
    "src/glorious_agents/**/*.sql",
    "src/glorious_agents/**/*.json",
    "src/glorious_agents/**/*.md",
    "src/glorious_agents/skills/**/*",  # Include all skills
]

[tool.hatch.build.targets.sdist]
include = [
    "src/",
    "tests/",
    "README.md",
    "LICENSE",
    "pyproject.toml",
]
```

**Actions:**
- [ ] Update pyproject.toml with proper package configuration
- [ ] Add MANIFEST.in if needed for non-Python files
- [ ] Test local build: `python -m build`
- [ ] Verify skills are included in wheel: `unzip -l dist/*.whl`

#### Step 2: Test Build Locally

```bash
# Clean previous builds
rm -rf dist/ build/ *.egg-info

# Build package
python -m build

# Check package contents
tar -tzf dist/glorious-agents-*.tar.gz | grep skills
unzip -l dist/glorious_agents-*.whl | grep skills

# Test install in clean environment
uv venv --python 3.13 .test-env
source .test-env/bin/activate
pip install dist/glorious_agents-*.whl
agent --help
agent skills list
```

#### Step 3: Test on TestPyPI (issue-e12df6)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ glorious-agents

# Verify skills are accessible
python -c "from glorious_agents.skills import *"
```

**Actions:**
- [ ] Create TestPyPI account
- [ ] Configure ~/.pypirc
- [ ] Test upload to TestPyPI
- [ ] Test installation from TestPyPI
- [ ] Verify all skills load correctly

### Phase 2: GitHub Actions CI/CD (Medium Priority)

#### Step 4: Create Release Workflow (issue-e12df6, issue-1437b2)

Create `.github/workflows/release.yml`:

```yaml
name: Release to PyPI

on:
  release:
    types: [published]

permissions:
  id-token: write  # For PyPI trusted publishing
  contents: write

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Run tests
        run: |
          uv sync --extra dev
          uv run pytest

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Build package
        run: |
          uv build
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  publish:
    needs: build
    runs-on: ubuntu-latest
    environment: release
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dist
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

**Actions:**
- [ ] Create GitHub Actions workflow
- [ ] Setup PyPI trusted publisher on PyPI website
- [ ] Configure GitHub environment protection rules
- [ ] Test workflow with TestPyPI first

#### Step 5: Pre-release Testing (issue-5deaf6)

Create `.github/workflows/pre-release-test.yml`:

```yaml
name: Pre-release Testing

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  test-install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v1
      - name: Test fresh install
        run: |
          # Build and install locally
          uv build
          uv venv .test
          .test/bin/pip install dist/*.whl
          
          # Test CLI
          .test/bin/agent --help
          .test/bin/agent version
          
          # Test skills load
          .test/bin/agent skills list
          
          # Test basic commands
          .test/bin/agent init
```

### Phase 3: Individual Skill Publishing (Medium Priority)

#### Step 6: Skill Package Publishing (issue-834b66)

Currently each skill has its own pyproject.toml. Options:

**Option A: Keep skills in main package (Recommended for v0.1.0)**
- Bundle all skills with glorious-agents
- Simpler installation: `pip install glorious-agents`
- Users get all skills by default
- Can still use extras for optional dependencies

**Option B: Separate PyPI packages**
- Publish each skill individually (17 packages!)
- More complex: users need to know which skills to install
- Better for: large ecosystems, version independence
- Consider for: v0.2.0+ when ecosystem matures

**Recommendation:** Start with Option A, move to Option B later if needed.

**Actions for Option A:**
- [x] Skills already in src/glorious_agents/skills/
- [ ] Verify pyproject.toml includes skills directory
- [ ] Test that skills load after pip install
- [ ] Document skill installation in README

**Actions for Option B (future):**
- [ ] Review each skill's pyproject.toml
- [ ] Ensure proper inter-skill dependencies
- [ ] Create publishing script for all skills
- [ ] Setup monorepo versioning strategy

### Phase 4: Version Management (Medium Priority)

#### Step 7: Automated Versioning (issue-45a268)

Create `scripts/bump_version.py`:

```python
#!/usr/bin/env python3
"""Bump version across all packages."""

import re
from pathlib import Path

def bump_version(version: str, part: str = "patch"):
    """Bump semantic version."""
    major, minor, patch = map(int, version.split("."))
    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"

def update_pyproject_version(path: Path, new_version: str):
    """Update version in pyproject.toml."""
    content = path.read_text()
    updated = re.sub(
        r'version = "[^"]+"',
        f'version = "{new_version}"',
        content
    )
    path.write_text(updated)

# Update main package
main_pyproject = Path("pyproject.toml")
# ... update version

# Update all skill packages
for skill_pyproject in Path("src/glorious_agents/skills").rglob("pyproject.toml"):
    # ... update version
```

**Actions:**
- [ ] Create version bump script
- [ ] Add changelog generation (using git-changelog or similar)
- [ ] Integrate with GitHub Actions
- [ ] Add git tag creation

#### Step 8: Release Automation (issue-502559)

Create `scripts/release.py`:

```python
#!/usr/bin/env python3
"""Automate the release process."""

import subprocess
import sys
from pathlib import Path

def run_tests():
    """Run full test suite."""
    result = subprocess.run(["uv", "run", "pytest"], check=False)
    return result.returncode == 0

def build_package():
    """Build distribution packages."""
    subprocess.run(["uv", "build"], check=True)

def publish_to_pypi():
    """Publish to PyPI (using trusted publishing)."""
    # This will be done via GitHub Actions
    print("Creating GitHub release will trigger PyPI publishing...")

def main():
    print("🚀 Starting release process...")
    
    # 1. Run tests
    print("📋 Running tests...")
    if not run_tests():
        print("❌ Tests failed!")
        sys.exit(1)
    
    # 2. Build package
    print("📦 Building package...")
    build_package()
    
    # 3. Instructions for GitHub release
    print("\n✅ Package built successfully!")
    print("\n📝 Next steps:")
    print("1. Create a GitHub release with tag v{version}")
    print("2. GitHub Actions will automatically publish to PyPI")
    print("3. Announce the release!")

if __name__ == "__main__":
    main()
```

### Phase 5: Documentation & Polish (Low Priority)

#### Step 9: Update Documentation (issue-23f275)

**Actions:**
- [ ] Add PyPI badges to README
- [ ] Update installation instructions
- [ ] Document skill installation options
- [ ] Add troubleshooting section
- [ ] Create RELEASING.md guide

## Package Structure Verification

After publishing, verify:

```python
# Test that skills are accessible
import glorious_agents
from glorious_agents.core.loader import load_all_skills
from glorious_agents.core.registry import get_registry

# Load skills
load_all_skills()
registry = get_registry()

# List loaded skills
for manifest in registry.list_all():
    print(f"✓ {manifest.name} v{manifest.version}")
```

Expected output:
```
✓ cache v0.1.0
✓ notes v0.1.0
✓ issues v0.1.0
✓ planner v0.1.0
... (all skills)
```

## Release Checklist

Before publishing to PyPI:

### Pre-release
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in all packages
- [ ] Skills folder included in build
- [ ] Tested local install from wheel
- [ ] Tested on TestPyPI

### Publishing
- [ ] Create GitHub release
- [ ] GitHub Actions publishes to PyPI
- [ ] Verify package on PyPI
- [ ] Test installation: `pip install glorious-agents`
- [ ] Verify skills load correctly

### Post-release
- [ ] Announce on social media
- [ ] Update documentation site
- [ ] Close milestone on GitHub
- [ ] Plan next version

## Success Criteria

A successful PyPI release means:

1. **Package is installable**
   ```bash
   pip install glorious-agents
   agent --help  # Works!
   ```

2. **Skills are accessible**
   ```bash
   agent skills list  # Shows all skills
   ```

3. **CLI works**
   ```bash
   agent init
   agent version
   ```

4. **Skills can be used**
   ```bash
   agent issues create "Test"
   agent notes add "Test"
   ```

5. **Documentation is clear**
   - Installation instructions work
   - Examples run successfully
   - Troubleshooting helps users

## Timeline Estimate

- **Phase 1 (Core Package):** 1-2 days
- **Phase 2 (GitHub Actions):** 1-2 days
- **Phase 3 (Individual Skills):** 1-3 days (if doing separate packages)
- **Phase 4 (Version Management):** 1 day
- **Phase 5 (Documentation):** 1 day

**Total:** 5-9 days for complete publishing setup

**Minimum Viable Release:** 2-3 days (Phases 1-2 only)

## Current Status

- [x] Project structure analysis complete
- [x] Issues created in tracker
- [ ] pyproject.toml not yet configured for publishing
- [ ] No MANIFEST.in (may not be needed with hatchling)
- [ ] No GitHub Actions workflows yet
- [ ] Skills packaging strategy to be decided

## Next Steps

1. **Immediate:** Fix pyproject.toml to include skills (issue-72a4ad)
2. **Next:** Test local build and verify skills included
3. **Then:** Setup TestPyPI testing (issue-e12df6)
4. **Finally:** Create GitHub Actions workflow (issue-1437b2)

## Important Notes

### Skills Must Be Included!

The most critical issue is **issue-72a4ad**. Without proper configuration:
- Skills won't be in the published package
- `pip install glorious-agents` will install a broken package
- Users won't be able to use any skills

### Python 3.13 Compatibility

Note: Some skills have Python 3.13 compatibility issues (planner skill has type hint errors). These should be fixed before publishing.

### Testing Strategy

Always test the **installed** package, not the development environment:

```bash
# Wrong: Testing from source
cd glorious && uv run agent skills list

# Right: Testing installed package
pip install dist/glorious_agents-*.whl
agent skills list
```

## Related Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Hatchling Documentation](https://hatch.pypa.io/latest/)

# Release Process for Glorious Agents

This document describes the complete release process for publishing new versions of Glorious Agents to PyPI.

## Prerequisites

### 1. PyPI Trusted Publishing Setup

Glorious Agents uses **PyPI Trusted Publishing** via GitHub Actions OIDC. This eliminates the need for API tokens.

#### Setup Steps:

1. **On PyPI:**
   - Go to https://pypi.org/manage/account/publishing/
   - Add a new "pending publisher"
   - Fill in:
     - **PyPI Project Name:** `glorious-agents`
     - **Owner:** `weholt`
     - **Repository name:** `glorious-agents`
     - **Workflow name:** `release.yml`
     - **Environment name:** `pypi`

2. **On GitHub:**
   - Go to repository Settings → Environments
   - Create environment `pypi`
   - Add protection rules (optional but recommended):
     - Required reviewers
     - Deployment branches: only `main`

3. **For TestPyPI** (optional):
   - Repeat above steps at https://test.pypi.org/manage/account/publishing/
   - Use environment name: `testpypi`

## Release Workflow

### Step 1: Prepare the Release

1. **Bump Version** using the automated script:
   ```bash
   # Bump patch version (0.1.0 → 0.1.1)
   python scripts/bump_version.py patch
   
   # Bump minor version (0.1.0 → 0.2.0)
   python scripts/bump_version.py minor
   
   # Bump major version (0.1.0 → 1.0.0)
   python scripts/bump_version.py major
   
   # Dry run to preview changes
   python scripts/bump_version.py --dry-run minor
   ```
   
   This will:
   - ✓ Update version in `pyproject.toml`
   - ✓ Create/update `CHANGELOG.md` with new version section
   - ✓ Show git commits since last release

2. **Update CHANGELOG.md**:
   - Review the auto-generated changelog entry
   - Add details for breaking changes, new features, bug fixes
   - Edit as needed for clarity

3. **Run Pre-Release Checks**:
   ```bash
   # Run the automated release script
   python scripts/release.py --dry-run
   ```

   This will:
   - ✓ Validate version format
   - ✓ Run all tests
   - ✓ Run quality checks (ruff, mypy)
   - ✓ Build the package
   - ✓ Verify skills are included
   - ✓ Create git tag (dry-run mode)

4. **Review Changes**:
   ```bash
   git status
   git diff
   ```

### Step 2: Create and Push Tag

Once all checks pass:

```bash
# Option 1: Run release script (after manually bumping version)
python scripts/release.py

# Option 2: Bump version AND release in one command
python scripts/release.py --bump minor

# This creates a git tag and provides next steps
```

Or manually:

```bash
# Create annotated tag
git tag -a v0.2.0 -m "Release 0.2.0"

# Push tag to GitHub
git push origin v0.2.0
```

**Quick Release Workflow:**
```bash
# Complete release in minimal steps
python scripts/release.py --bump patch  # Bump and validate
# Review changes, then push tag as instructed
```

### Step 3: Create GitHub Release

1. Go to: https://github.com/weholt/glorious-agents/releases/new
2. Select the tag you just pushed: `v0.2.0`
3. Release title: `Release 0.2.0`
4. Description: Copy changelog or describe key changes
5. Click "Publish release"

### Step 4: Automated Publishing

GitHub Actions will automatically:

1. ✓ Run all tests
2. ✓ Run quality checks
3. ✓ Build the package
4. ✓ Verify package contents
5. ✓ Publish to PyPI using trusted publishing

Monitor the workflow:
- https://github.com/weholt/glorious-agents/actions

### Step 5: Verify Release

Once published, verify:

```bash
# Check PyPI page
open https://pypi.org/project/glorious-agents/

# Install and test with uv
uv tool install --force glorious-agents[all-skills]
uvx agent version

# Should show new version
```

## Testing on TestPyPI (Optional)

Before publishing to production PyPI, you can test on TestPyPI:

1. **Trigger TestPyPI Workflow**:
   - Go to Actions → Release to PyPI
   - Click "Run workflow"
   - Check "Publish to TestPyPI"
   - Click "Run workflow"

2. **Test Installation**:
   ```bash
   uv tool install --force \
       --index-url https://test.pypi.org/simple/ \
       --extra-index-url https://pypi.org/simple/ \
       glorious-agents[all-skills]
   ```

3. **Verify**:
   ```bash
   uvx agent --help
   uvx agent version
   uvx agent skills list
   ```

## Release Checklist

Use this checklist for each release:

### Pre-Release
- [ ] All tests passing locally
- [ ] All CI checks passing
- [ ] Version bumped in `pyproject.toml`
- [ ] CHANGELOG.md updated (if exists)
- [ ] Documentation updated
- [ ] Release notes drafted

### Release
- [ ] Git tag created: `v0.x.y`
- [ ] Tag pushed to GitHub
- [ ] GitHub release created
- [ ] Release notes published
- [ ] GitHub Actions workflow completed successfully

### Post-Release
- [ ] Package visible on PyPI
- [ ] Version number correct on PyPI
- [ ] Installation works: `uv tool install glorious-agents[all-skills]`
- [ ] CLI works: `uvx agent --help`
- [ ] Skills load: `uvx agent skills list`
- [ ] Announce release (Twitter, Discord, etc.)
- [ ] Update documentation site (if exists)

## Versioning Guidelines

> **📖 Complete Specification:** See [VERSION_SCHEME.md](./VERSION_SCHEME.md) for the official versioning policy.

Glorious Agents follows **Semantic Versioning** (semver):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backwards compatible
- **Patch** (0.0.1): Bug fixes, backwards compatible

### Examples:

- `0.1.0` → `0.2.0`: Added new skills or features
- `0.2.0` → `0.2.1`: Fixed bugs
- `0.9.0` → `1.0.0`: First stable release, API finalized

For detailed rules on when to bump each version component, see [VERSION_SCHEME.md](./VERSION_SCHEME.md).

## Troubleshooting

### Build Fails

```bash
# Clean and rebuild
rm -rf dist/ build/ *.egg-info
python scripts/release.py
```

### Tests Fail

```bash
# Run tests locally
uv run pytest -v

# Run specific test
uv run pytest tests/test_specific.py -v
```

### Skills Not Included

```bash
# Verify skills in wheel
python -m zipfile -l dist/*.whl | grep skills/
```

Should show all 17 skills. If not, check `pyproject.toml`:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/glorious_agents"]
```

### PyPI Trusted Publishing Fails

1. Check GitHub Actions logs
2. Verify PyPI trusted publisher configuration
3. Ensure environment name matches: `pypi`
4. Check environment protection rules

### Version Already Exists on PyPI

You cannot re-upload the same version. Options:

1. Bump to next patch version (e.g., 0.2.0 → 0.2.1)
2. Use `--skip-existing` for development uploads
3. Or use TestPyPI for testing

## Emergency Rollback

If a release has critical issues:

1. **Yank the release on PyPI** (don't delete):
   - Go to https://pypi.org/manage/project/glorious-agents/releases/
   - Click on problematic version
   - Click "Yank release"
   - Provide reason

2. **Create hotfix release**:
   ```bash
   # Fix the issue
   git commit -m "fix: critical bug"
   
   # Bump patch version
   # 0.2.0 → 0.2.1
   
   # Release
   python scripts/release.py
   ```

3. **Announce**:
   - Update GitHub release notes
   - Notify users to upgrade

## CI/CD Workflows

### `release.yml`
Main release workflow:
- Triggered by: Publishing a GitHub release
- Runs: Tests, quality checks, builds, publishes to PyPI
- Uses: PyPI trusted publishing (OIDC)

### `pre-release.yml`
Pre-release testing workflow:
- Triggered by: Push to main, PRs
- Runs: Multi-platform tests, fresh install tests, package verification
- Ensures: Package is ready for release

### `ci.yml`
Continuous integration:
- Triggered by: Every push, every PR
- Runs: Tests, linting, type checking
- Ensures: Code quality

## Useful Commands

```bash
# Check current version
grep 'version =' pyproject.toml

# Bump version (automated)
python scripts/bump_version.py patch  # or minor, or major
python scripts/bump_version.py --dry-run minor  # Preview changes

# Complete release workflow
python scripts/release.py --bump patch  # Bump and release

# Build package locally
uv tool run --from build pyproject-build

# Check package contents
python -m zipfile -l dist/*.whl | less

# Verify metadata
unzip -p dist/*.whl glorious_agents-*.dist-info/METADATA | head -30

# Test installation
python -m venv /tmp/test-install
/tmp/test-install/bin/pip install dist/*.whl
/tmp/test-install/bin/agent --help
```

## Support

If you encounter issues with the release process:

1. Check GitHub Actions logs
2. Review this documentation
3. Open an issue: https://github.com/weholt/glorious-agents/issues
4. Contact maintainer: thomas@weholt.org

---

**Last Updated:** 2025-11-16
**Maintainer:** Thomas Weholt <thomas@weholt.org>

# Testing Guide

## Running Tests Locally

### Standard Python Tests

```bash
# Install dependencies
uv pip install .[dev]

# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=term --cov-report=html

# Run specific test file
uv run pytest tests/test_specific.py

# Run with verbose output
uv run pytest -v
```

### Code Quality Checks

```bash
# Format check
uv run ruff format --check .

# Format code
uv run ruff format .

# Lint check
uv run ruff check .

# Lint with auto-fix
uv run ruff check --fix .

# Type checking
uv run mypy src

# Security scan
uv run bandit -r src

# Run all pre-commit hooks
uv run pre-commit run --all-files
```

## Running GitHub Actions Locally

This project includes the `act` tool for running GitHub Actions workflows locally in Docker containers.

### Prerequisites

1. **Docker** must be installed and running
2. **GitHub Token** (required for downloading dependencies)

### Setup GitHub Token

The workflows require a GitHub token to download tools like UV. Choose one method:

**Option 1: Using GitHub CLI (Recommended)**
```bash
gh auth login
# Then run the helper script
./run-ci-tests.sh
```

**Option 2: Environment Variable**
```bash
export GITHUB_TOKEN=your_token_here
./run-ci-tests.sh
```

**Option 3: .secrets File**
```bash
echo "GITHUB_TOKEN=your_token_here" > .secrets
./bin/act --action-offline-mode --pull=false
```

> **Note:** Create a token at https://github.com/settings/tokens
> No special scopes/permissions are needed for public repository access.

### Running Workflows

**Use the helper script (recommended):**
```bash
# Run all workflows
./run-ci-tests.sh

# Run specific workflow
./run-ci-tests.sh -W .github/workflows/ci.yml

# Run specific job
./run-ci-tests.sh --job quality

# Dry run (see what would execute)
./run-ci-tests.sh -n
```

**Or use act directly:**
```bash
# Run all workflows
./bin/act --action-offline-mode --pull=false

# Run CI workflow only
./bin/act --action-offline-mode --pull=false -W .github/workflows/ci.yml

# Run specific job
./bin/act --action-offline-mode --pull=false --job quality

# List all workflows
./bin/act --list

# List jobs in workflow
./bin/act -W .github/workflows/ci.yml --list
```

### Workflow Files

- `.github/workflows/ci.yml` - Main CI pipeline (quality, tests, build)
- `.github/workflows/pre-release.yml` - Pre-release testing (package validation)
- `.github/workflows/release.yml` - PyPI release workflow

### Understanding Flags

- `--action-offline-mode` - Use cached GitHub actions (faster, doesn't require repeated downloads)
- `--pull=false` - Skip pulling Docker images if already present (faster)
- `-n` or `--dryrun` - Show what would run without executing
- `-W` or `--workflows` - Specify workflow file
- `--job` - Run specific job only

### Common Issues

**"Bad credentials" error**
- Solution: Provide a valid GitHub token (see Setup section)
- The token doesn't need any special permissions

**"authentication required" for git operations**
- Solution: Use `--action-offline-mode` flag

**Docker errors**
- Solution: Ensure Docker is running: `docker ps`
- Check Docker has enough resources (4GB+ RAM recommended)

**Rate limiting**
- Solution: Use a GitHub token to avoid anonymous API rate limits

### CI/CD Pipeline

The CI pipeline runs:

1. **Code Quality Checks**
   - Ruff formatting check
   - Ruff linting
   - MyPy type checking
   - Bandit security scan

2. **Tests**
   - Unit tests with pytest
   - Coverage reporting
   - Matrix testing (Ubuntu, Windows, macOS)

3. **Build**
   - Package building with UV
   - Artifact upload

4. **Integration Tests**
   - Integration test suite
   - (Only on pull requests and main branch)

5. **Pre-commit Hooks**
   - All pre-commit hooks validation

6. **Documentation**
   - Documentation file validation

## Continuous Integration

All pull requests and pushes to `main` or `develop` branches automatically run the full CI pipeline on GitHub Actions.

### Status Checks

- ✅ All checks must pass before merging
- 📊 Coverage reports uploaded to Codecov
- 🔒 Security scan results archived as artifacts

## Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
uv run pre-commit install

# Run manually
uv run pre-commit run --all-files

# Update hooks to latest versions
uv run pre-commit autoupdate
```

Hooks include:
- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file detection
- Ruff formatting and linting

## Integration Tests

Integration tests verify end-to-end functionality:

```bash
# Run only integration tests
uv run pytest -m integration

# Run with coverage
uv run pytest -m integration --cov
```

Mark tests as integration tests:

```python
import pytest

@pytest.mark.integration
def test_full_workflow():
    # Integration test code
    pass
```

## Test Organization

```
tests/
├── test_core.py          # Core functionality tests
├── test_cli.py           # CLI command tests
├── test_skills.py        # Skills framework tests
├── test_database.py      # Database tests
├── test_integration.py   # Integration tests
└── conftest.py          # Pytest configuration and fixtures
```

## Coverage

```bash
# Generate coverage report
uv run pytest --cov --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

Coverage targets:
- Overall: > 80%
- Critical modules: > 90%

## More Information

- Act documentation: https://github.com/nektos/act
- GitHub Actions docs: https://docs.github.com/en/actions
- Pytest docs: https://docs.pytest.org/
- Pre-commit docs: https://pre-commit.com/

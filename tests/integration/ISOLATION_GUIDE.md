# Integration Test Isolation Guide

## Overview

All integration tests in this suite run in **complete isolation** to ensure they don't affect your workspace, database, or any existing data.

## How Isolation Works

### 1. Temporary Directories

Every test gets its own temporary directory structure:

```
/tmp/pytest-of-user/pytest-current/test_name/
├── .agent/                    # Isolated agent data folder
│   └── agents/
│       └── default/
│           └── agent.db       # Isolated database
├── home/                      # Isolated home directory
└── tmp/                       # Isolated temp directory
```

### 2. Environment Variables

The `isolated_env` fixture sets these environment variables for each test:

- `GLORIOUS_DATA_FOLDER` → Points to temp `.agent` folder
- `DATA_FOLDER` → Points to temp `.agent` folder  
- `HOME` → Points to temp `home` folder
- `TMPDIR` → Points to temp `tmp` folder

### 3. Subprocess Isolation

The `run_agent_cli()` function ensures CLI commands run with isolated environment:

```python
def run_agent_cli(args, isolated_env=isolated_env):
    # Uses minimal environment + isolated_env variables
    # Prevents leaking workspace settings
    # All file operations happen in temp directories
```

## Using Isolated Environment

### Basic Pattern

```python
def test_example(isolated_env):
    """Test with complete isolation."""
    # This runs in temp directory with isolated database
    result = run_agent_cli(['notes', 'add', 'Test'], isolated_env=isolated_env)
    
    assert result['success']
    
    # Files created are in isolated_env['cwd']
    # Database is in isolated_env['agent_folder']
```

### Accessing Isolated Paths

```python
def test_with_files(isolated_env):
    """Test that creates files."""
    # Create file in isolated root
    test_file = isolated_env['root'] / 'test.txt'
    test_file.write_text('content')
    
    # Use isolated cwd for commands
    result = run_agent_cli(['command'], isolated_env=isolated_env)
    
    # Check isolated agent folder
    db_path = isolated_env['agent_folder'] / 'agents' / 'default' / 'agent.db'
    if db_path.exists():
        # Database is in isolated location
        assert str(db_path).startswith(str(isolated_env['root']))
```

### Available Paths

The `isolated_env` fixture provides:

- `isolated_env['root']` - Root temporary directory
- `isolated_env['agent_folder']` - Agent data folder (`.agent`)
- `isolated_env['cwd']` - Current working directory for commands
- `isolated_env['env']` - Environment variables dict

## Verification

### Run Isolation Tests

```bash
# Run isolation verification tests
pytest tests/integration/test_isolation_verification.py -v

# These tests verify:
# - Temp directories are used
# - Environment variables are correct
# - No workspace contamination
# - Proper cleanup
```

### What Gets Isolated

✓ **Database** - Each test gets its own SQLite database in temp folder
✓ **Agent Data** - All agent data stored in temp `.agent` folder
✓ **File Operations** - All file I/O happens in temp directories
✓ **Environment** - Isolated HOME, TMPDIR, and data folders
✓ **Configuration** - Config resets between tests

### What Doesn't Get Isolated

- Python imports (shared across tests)
- System-level resources (network, etc.)
- Installed packages

## Cleanup

Cleanup is **automatic**:

1. pytest's `tmp_path` fixture automatically removes temp directories after each test
2. The `isolated_env` fixture calls `reset_config()` after each test
3. No manual cleanup needed

## Troubleshooting

### Tests Creating Files in Workspace

If tests create files in your workspace:

1. Check that `isolated_env` is passed to `run_agent_cli()`:
   ```python
   # ✗ Wrong - uses current workspace
   result = run_agent_cli(['notes', 'add', 'Test'], cwd=some_path)
   
   # ✓ Correct - uses isolated environment
   result = run_agent_cli(['notes', 'add', 'Test'], isolated_env=isolated_env)
   ```

2. Verify environment variables are set:
   ```python
   assert 'env' in isolated_env
   assert isolated_env['env']['DATA_FOLDER'] == str(isolated_env['agent_folder'])
   ```

### Database Not Isolated

If database operations affect your workspace:

1. Ensure `isolated_env` fixture is used
2. Check that `GLORIOUS_DATA_FOLDER` and `DATA_FOLDER` are set correctly
3. Verify `reset_config()` is called

### Temp Files Not Cleaned Up

If temp files persist:

1. Check that tests complete successfully (failures may prevent cleanup)
2. Verify pytest's `tmp_path` is being used (it auto-cleans)
3. Look for manual file operations outside `isolated_env['root']`

## Best Practices

### DO ✓

```python
def test_good_isolation(isolated_env):
    """Properly isolated test."""
    # Use isolated_env parameter
    result = run_agent_cli(['notes', 'add', 'Test'], isolated_env=isolated_env)
    
    # Create files in isolated root
    test_file = isolated_env['root'] / 'test.txt'
    test_file.write_text('content')
    
    # Access isolated database
    db_path = isolated_env['agent_folder'] / 'agents' / 'default' / 'agent.db'
```

### DON'T ✗

```python
def test_bad_isolation(isolated_env):
    """Improperly isolated test."""
    # ✗ Don't use cwd without isolated_env
    result = run_agent_cli(['notes', 'add', 'Test'], cwd=isolated_env['cwd'])
    
    # ✗ Don't create files outside isolated root
    bad_file = Path('/home/user/test.txt')
    bad_file.write_text('content')
    
    # ✗ Don't access workspace database
    workspace_db = Path('/home/user/.agent/agents/default/agent.db')
```

## Running Tests Safely

### Safe Commands

```bash
# Run all integration tests (completely isolated)
pytest tests/integration/ -v

# Run specific test file (isolated)
pytest tests/integration/test_main_cli.py -v

# Run with parallel execution (each worker isolated)
pytest tests/integration/ -n auto

# Run isolation verification first
pytest tests/integration/test_isolation_verification.py -v
```

### Verify Isolation Before Full Run

```bash
# 1. Run isolation verification tests
pytest tests/integration/test_isolation_verification.py -v

# 2. If all pass, run full suite
pytest tests/integration/ -v

# 3. Check workspace is clean
git status  # Should show no unexpected changes
```

## Summary

✓ **Complete Isolation** - Every test runs in its own temp directory
✓ **No Workspace Impact** - Your workspace and data remain untouched
✓ **Automatic Cleanup** - Temp directories removed after each test
✓ **Safe to Run** - Can run entire suite without any side effects
✓ **Parallel Safe** - Tests can run in parallel without conflicts

The integration test suite is designed to be **completely safe** to run at any time without affecting your development environment.
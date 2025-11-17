# Running GitHub Actions Locally with Act

This project uses [act](https://github.com/nektos/act) to test GitHub Actions workflows locally.

## Prerequisites

1. Docker must be installed and running
2. `act` binary is included in `./bin/act`

## Setup

### GitHub Token (Required)

The workflows use the `astral-sh/setup-uv@v4` action which requires GitHub API access to download UV releases. To run act successfully, you need to provide a GitHub token:

**Option 1: Using gh CLI (Recommended)**
```bash
gh auth login
# Token will be automatically used by the run script
./scripts/run-act.sh
```

**Option 2: Personal Access Token**
1. Create a GitHub Personal Access Token (no special permissions needed for public repo access)
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - No scopes need to be selected for public repository access
2. Create a `.secrets` file in the project root:
   ```bash
   echo "GITHUB_TOKEN=your_token_here" > .secrets
   ```
3. Run act:
   ```bash
   ./bin/act
   ```

**Option 3: Environment Variable**
```bash
export GITHUB_TOKEN=your_token_here
./bin/act
```

## Usage

### Run all workflows
```bash
./bin/act --action-offline-mode --pull=false
```

### Run specific workflow
```bash
./bin/act --action-offline-mode --pull=false -W .github/workflows/ci.yml
```

### Run specific job
```bash
./bin/act --action-offline-mode --pull=false --job quality
```

### Dry run (to see what would execute)
```bash
./bin/act --action-offline-mode --pull=false -n
```

## Flags Explained

- `--action-offline-mode`: Uses cached GitHub actions instead of fetching updates
- `--pull=false`: Skips pulling Docker images if already present (faster)

## Common Issues

### "Bad credentials" error
- You need to provide a valid GitHub token (see Setup section above)
- Even a token with no special scopes works for downloading UV releases

### "authentication required" for git operations
- Use `--action-offline-mode` flag to use cached actions

### Rate limiting
- Use a GitHub token to avoid anonymous rate limits
- The token doesn't need any special permissions

## Files

- `.secrets` - Contains GitHub token (gitignored, must be created by you)
- `scripts/run-act.sh` - Helper script that automatically configures tokens from gh CLI

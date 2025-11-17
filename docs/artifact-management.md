# GitHub Actions Artifact Management

## Overview

This document explains how artifacts are managed in GitHub Actions workflows to avoid exceeding storage quotas.

## Current Configuration

### Artifact Retention Policies

1. **CI Workflow** (`ci.yml`)
   - **Security reports**: 7 days retention, only uploaded on failures or main branch pushes
   - **Build artifacts**: 3 days retention, only uploaded on main branch pushes
   - **Purpose**: Quick access to recent builds while minimizing storage

2. **Release Workflow** (`release.yml`)
   - **Build artifacts**: 5 days retention
   - **Purpose**: Available during release process, automatically cleaned up after

3. **Pre-release Workflow** (`pre-release.yml`)
   - **No artifacts uploaded** - all testing is done in-place
   - **Purpose**: Validation only, no storage needed

### Automatic Cleanup

- A dedicated workflow (`cleanup-artifacts.yml`) runs daily at 2 AM UTC
- Deletes artifacts older than 7 days
- Keeps the 5 most recent artifacts regardless of age
- Preserves artifacts from tagged releases

## Artifact Naming Strategy

All artifacts now use unique names with run IDs to prevent conflicts:
- `dist-${{ github.run_id }}`
- `security-report-${{ github.run_id }}`

This allows multiple concurrent workflow runs without artifact name collisions.

## Manual Cleanup

If you need to manually clean up artifacts:

1. Go to repository **Actions** tab
2. Click on **Artifacts** in the left sidebar
3. Review and delete old/unnecessary artifacts
4. Or run the cleanup workflow manually via **Actions** → **Cleanup Old Artifacts** → **Run workflow**

## Storage Limits

- **Free tier**: 500 MB storage, 2,000 minutes/month
- **Pro tier**: 2 GB storage, 3,000 minutes/month
- **Team tier**: 2 GB storage, 10,000 minutes/month

See [GitHub's billing documentation](https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions) for details.

## Best Practices

1. **Only upload artifacts when necessary**
   - Use conditionals to limit uploads to specific branches or events
   - Don't upload on every pull request unless needed for review

2. **Set appropriate retention periods**
   - 1-3 days for CI artifacts
   - 5-7 days for release candidates
   - Never use indefinite retention unless absolutely necessary

3. **Use descriptive names with run IDs**
   - Makes it easier to identify and clean up old artifacts
   - Prevents naming conflicts in parallel runs

4. **Regularly review artifact usage**
   - Check the Actions tab periodically
   - Identify workflows that generate excessive artifacts
   - Adjust retention policies as needed

## Troubleshooting

### "Artifact storage quota exceeded" Error

If you encounter this error:

1. **Immediate fix**: Manually delete old artifacts from the Actions tab
2. **Long-term fix**: The cleanup workflow should prevent this
3. **Emergency**: Run the cleanup workflow manually with `workflow_dispatch`

### Finding Large Artifacts

```bash
# List all artifacts with sizes (using GitHub CLI)
gh api repos/{owner}/{repo}/actions/artifacts --paginate | jq '.artifacts[] | {name: .name, size_mb: (.size_in_bytes / 1048576 | floor), created_at: .created_at}'
```

## Related Files

- `.github/workflows/ci.yml` - Main CI pipeline
- `.github/workflows/release.yml` - Release workflow
- `.github/workflows/pre-release.yml` - Pre-release testing
- `.github/workflows/cleanup-artifacts.yml` - Automatic cleanup

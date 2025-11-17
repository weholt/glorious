#!/bin/bash
# Helper script to run CI tests locally with act
#
# This script will:
# 1. Try to get a GitHub token from gh CLI or environment
# 2. Run act with proper flags for offline action use
# 3. Clean up temporary files

set -e

echo "🚀 Running CI workflows locally with act..."
echo

# Check if act binary exists
if [ ! -f "./bin/act" ]; then
    echo "❌ Error: ./bin/act not found"
    echo "Please ensure the act binary is in ./bin/"
    exit 1
fi

# Try to get a GitHub token
TOKEN_SOURCE="none"
if [ -n "$GITHUB_TOKEN" ]; then
    echo "✓ Using GITHUB_TOKEN from environment"
    TOKEN_SOURCE="environment"
elif command -v gh &> /dev/null; then
    GITHUB_TOKEN=$(gh auth token 2>/dev/null || echo "")
    if [ -n "$GITHUB_TOKEN" ]; then
        export GITHUB_TOKEN
        echo "✓ Using GitHub token from gh CLI"
        TOKEN_SOURCE="gh_cli"
    fi
fi

# Create .secrets file
if [ "$TOKEN_SOURCE" != "none" ]; then
    echo "GITHUB_TOKEN=$GITHUB_TOKEN" > .secrets
    echo "✓ Created .secrets file with token"
else
    echo "⚠️  Warning: No GitHub token available"
    echo "   The workflows will fail when trying to install uv"
    echo "   To fix this:"
    echo "   1. Run: gh auth login"
    echo "   2. Or set: export GITHUB_TOKEN=your_token"
    echo "   3. Or create .secrets file with: GITHUB_TOKEN=your_token"
    echo
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    # Create dummy .secrets for act to read
    echo "GITHUB_TOKEN=dummy" > .secrets
fi

echo
echo "Running act with flags:"
echo "  --action-offline-mode  (use cached actions)"
echo "  --pull=false          (don't pull Docker images)"
echo

# Run act with appropriate flags
./bin/act \
    --action-offline-mode \
    --pull=false \
    "$@"

exit_code=$?

# Clean up .secrets if we created it
if [ "$TOKEN_SOURCE" != "none" ] || [ -f ".secrets" ]; then
    rm -f .secrets
    echo
    echo "✓ Cleaned up .secrets file"
fi

echo
if [ $exit_code -eq 0 ]; then
    echo "✅ All workflows completed successfully!"
else
    echo "❌ Some workflows failed (exit code: $exit_code)"
    echo
    echo "Common issues:"
    echo "  - No GitHub token: Run 'gh auth login' or set GITHUB_TOKEN"
    echo "  - Docker not running: Start Docker daemon"
    echo "  - Insufficient resources: Increase Docker memory limit"
fi

exit $exit_code

#!/bin/bash
# Wrapper script for running act with proper configuration

# Try to get a real GitHub token if available
if [ -z "$GITHUB_TOKEN" ]; then
    # Try to get token from gh CLI
    TOKEN=$(gh auth token 2>/dev/null)
    if [ -n "$TOKEN" ]; then
        export GITHUB_TOKEN="$TOKEN"
        echo "Using GitHub token from gh CLI"
    else
        # Use anonymous access (will have rate limits but works for most operations)
        echo "Warning: No GitHub token available. Using anonymous access."
        echo "Note: You may hit rate limits. Run 'gh auth login' to authenticate."
    fi
fi

# Create .secrets file with token if it exists
if [ -n "$GITHUB_TOKEN" ]; then
    echo "GITHUB_TOKEN=$GITHUB_TOKEN" > .secrets
else
    # Create with dummy token to prevent errors
    echo "GITHUB_TOKEN=ghp_dummy_token_for_local_testing_only" > .secrets
fi

# Run act with appropriate flags
./bin/act \
    --action-offline-mode \
    --pull=false \
    "$@"

exit_code=$?

# Clean up .secrets file
rm -f .secrets

exit $exit_code

#!/bin/bash
# Antigravity (agy) Hook to ensure README.md is always in sync with customizations.

# ⚡ Fast Exit: Only intercept git commit or push tool commands
if [[ ! "$CommandLine" =~ "git commit" ]] && [[ ! "$CommandLine" =~ "git push" ]]; then
    exit 0
fi

# Compare to origin/main or previous commits to detect modified configs

comparison_target="origin/main"
current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")

if [ "$current_branch" != "main" ]; then
    comparison_target="main"
fi

if ! git rev-parse --verify "$comparison_target" &>/dev/null; then
    comparison_target="HEAD~1"
fi

# Check if comparison target exists at all
if ! git rev-parse --verify "$comparison_target" &>/dev/null; then
    # New repo or empty history fallback
    exit 0
fi

# Check modified customizations in current diff scope
CH_PROMPTS=$(git diff --name-only "$comparison_target" | grep -E "agents/|install.sh|bootstrap.py" || true)
CH_README=$(git diff --name-only "$comparison_target" | grep "README.md" || true)

# Also check staged changes in case of pre-commit tool actions
STAGED_PROMPTS=$(git diff --name-only --cached | grep -E "agents/|install.sh|bootstrap.py" || true)
STAGED_README=$(git diff --name-only --cached | grep "README.md" || true)

if { [ -n "$CH_PROMPTS" ] && [ -z "$CH_README" ]; } || { [ -n "$STAGED_PROMPTS" ] && [ -z "$STAGED_README" ]; }; then
    echo -e "\n\033[91m================================================================"
    echo -e "⚠️  ANTIGRAVITY COMPLIANCE GUARD: README.md IS OUT OF SYNC!"
    echo -e "================================================================"
    echo -e "You are attempting to execute a git action on modified configs:"
    if [ -n "$STAGED_PROMPTS" ]; then
        echo -e "Staged configs:\n$STAGED_PROMPTS" | sed 's/^/  - /'
    else
        echo -e "Modified configs compared to $comparison_target:\n$CH_PROMPTS" | sed 's/^/  - /'
    fi
    echo -e "\nBut README.md has NOT been updated!"
    echo -e "Please ensure your documentation is updated before completing this action."
    echo -e "================================================================\033[0m\n"
    exit 1
fi

echo -e "\033[92m[agy-hook] README consistency check passed. Allowing command execution.\033[0m"
exit 0

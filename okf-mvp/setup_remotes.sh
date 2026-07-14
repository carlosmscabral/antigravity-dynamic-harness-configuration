#!/bin/bash
# setup_remotes.sh - Sets up two GitHub repositories for our MVP configurations using the gh CLI.

set -e

CORP_REPO="dhc-corp-global-config"
GROUP_REPO="dhc-group-wealth-config"
USER_NAME="carlosmscabral"

echo "=========================================================="
echo "🚀 Setting up DHC MVP Remote Config Repositories via gh"
echo "=========================================================="

# Check if gh is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed. Please install it to use remote repos."
    echo "💡 Fallback: The DHC Configurator will use the local /okf-mvp/mock_remotes/ directory."
    exit 0
fi

# Check auth status
if ! gh auth status &> /dev/null; then
    echo "❌ You are not logged into the GitHub CLI (gh auth login)."
    echo "💡 Fallback: The DHC Configurator will use the local /okf-mvp/mock_remotes/ directory."
    exit 0
fi

echo "✅ GitHub CLI is installed and authenticated."

# Function to create and seed repository
setup_repo() {
    local repo_name=$1
    local config_dir=$2
    local config_file=$3
    
    echo "----------------------------------------------------------"
    echo "📦 Setting up remote repository: $USER_NAME/$repo_name"
    echo "----------------------------------------------------------"
    
    # Check if repo already exists
    if gh repo view "$USER_NAME/$repo_name" &> /dev/null; then
        echo "⚠️ Repo $USER_NAME/$repo_name already exists. Proceeding to push updates."
    else
        echo "Creating repo $USER_NAME/$repo_name on GitHub..."
        gh repo create "$USER_NAME/$repo_name" --public --confirm
    fi
    
    # Create a temporary folder to push files
    TEMP_DIR=$(mktemp -d)
    cp "$config_dir/$config_file" "$TEMP_DIR/"
    cd "$TEMP_DIR"
    
    git init -b main
    git config user.name "Carlos Cabral (DHC Agent)"
    git config user.email "carlos.cabral@agentic.internal"
    git add "$config_file"
    git commit -m "feat: initial release of OKF configuration manifest"
    
    # Set remote URL using gh and push
    git remote add origin "https://github.com/carlosmscabral/$repo_name.git"
    git push -u origin main --force
    
    echo "✅ Successfully pushed $config_file to $USER_NAME/$repo_name!"
    # Clean up
    rm -rf "$TEMP_DIR"
}

# Execute
BASE_DIR="/Users/carloscabral/_demos/antigravity-okf-customizations/okf-mvp"
setup_repo "$CORP_REPO" "$BASE_DIR/mock_remotes/corp-global" "okf-global.json"
setup_repo "$GROUP_REPO" "$BASE_DIR/mock_remotes/group-wealth" "okf-group.json"

echo "=========================================================="
echo "🎉 Remote setup complete!"
echo "=========================================================="

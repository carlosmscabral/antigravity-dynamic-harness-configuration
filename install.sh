#!/bin/bash
# 🚀 Antigravity Dynamic Harness Configurator (DHC) Shell Installer
# Dynamically installs the latest DHC and plugins without cloning or hardcoding file names.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/carlosmscabral/antigravity-okf-customizations/main/install.sh | bash

set -e

# Banners and Colors
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BLUE='\033[94m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================================${NC}"
echo -e "${BLUE}${BOLD}     🚀 ANTIGRAVITY DYNAMIC HARNESS CONFIGURATOR (DHC) INSTALLER${NC}"
echo -e "${BLUE}====================================================================${NC}"

WORKSPACE_ROOT=$(pwd)
echo -e "[DHC] Local target workspace: ${BOLD}${WORKSPACE_ROOT}${NC}\n"

# Verify system utilities
if ! command -v curl &> /dev/null; then
    echo -e "${RED}ERROR: 'curl' is required but not installed. Exiting.${NC}" >&2
    exit 1
fi

if ! command -v unzip &> /dev/null; then
    echo -e "${RED}ERROR: 'unzip' is required but not installed. Exiting.${NC}" >&2
    exit 1
fi

# Define temp download targets
TEMP_ZIP="dhc_archive.zip"
EXTRACT_DIR="antigravity-okf-customizations-main"
REPO_ZIP_URL="https://github.com/carlosmscabral/antigravity-okf-customizations/archive/refs/heads/main.zip"

echo -e "[DHC] Fetching latest customization assets archive from GitHub..."
curl -fsSL -o "$TEMP_ZIP" "$REPO_ZIP_URL"

echo -e "[DHC] Unpacking archive dynamically..."
unzip -q -o "$TEMP_ZIP"

# Establish target directories
echo -e "[DHC] Provisioning local workspace structures..."
mkdir -p .agents/agents
mkdir -p .agents/plugins_cache

# Clean up any legacy, flat harness-configurator.md file from previous versions
rm -f .agents/agents/harness-configurator.md

# Copy agent prompts dynamically
echo -e "[DHC] Moving harness-configurator agent..."
if [ -d "$EXTRACT_DIR/agents" ]; then
    cp -R "$EXTRACT_DIR/agents/" .agents/agents/
fi

# Copy all plugins dynamically to the inactive cache folder
echo -e "[DHC] Staging customization library plugins in cache recursively..."
if [ -d "$EXTRACT_DIR/.agents/plugins" ]; then
    cp -R "$EXTRACT_DIR/.agents/plugins/" .agents/plugins_cache/
fi

# Make any scripts inside cached plugins executable
echo -e "[DHC] Enforcing execution permissions on plugin scripts in cache..."
find .agents/plugins_cache/ -name "*.sh" -exec chmod +x {} + 2>/dev/null || true


# Cleanup temp files
echo -e "[DHC] Cleaning up temporary download caches..."
rm -rf "$TEMP_ZIP" "$EXTRACT_DIR"

echo -e "\n${BLUE}====================================================================${NC}"
echo -e "${GREEN}${BOLD}🎉 SUCCESS! DHC JIT-harness assets dynamically downloaded and ready.${NC}"
echo -e "${BLUE}====================================================================${NC}"
echo -e "\nTo launch the interactive configuration session with your setup agent:"
echo -e "  1. Run: ${YELLOW}${BOLD}agy${NC}"
echo -e "  2. Type: ${YELLOW}${BOLD}/agents${NC} and select ${BOLD}harness-configurator${NC}"
echo -e "\nThis will:"
echo -e "  1. Silently scan your code files and dependencies."
echo -e "  2. Propose relevant rules, ignores, and secure upstream sources."
echo -e "  3. Provision your workspace security and testing boundaries JIT!"
echo -e "${BLUE}====================================================================${NC}"

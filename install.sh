#!/bin/bash
# 🚀 Antigravity Dynamic Harness Configurator (DHC) Shell Installer
# Thin installer: fetches the harness-configurator agent from this repo and the
# harness plugins + skills from the cabral-skills monorepo at a PINNED git tag.
#
# Usage:
#   curl -fsSL -H 'Cache-Control: no-cache' https://raw.githubusercontent.com/carlosmscabral/antigravity-dynamic-harness-configuration/main/install.sh | bash

set -e

# ── Pinned content source ────────────────────────────────────────────────────
# Plugins and skills live in the cabral-skills monorepo. Bump this tag to adopt
# a new release of the customization library. Everything (plugins + skills) is
# fetched at this single tag so a promoted plugin and the skills it references
# are always mutually consistent.
CABRAL_SKILLS_REPO="carlosmscabral/cabral-skills"
CABRAL_SKILLS_TAG="v1.2.1"

# ── Banners and Colors ───────────────────────────────────────────────────────
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
echo -e "[DHC] Local target workspace: ${BOLD}${WORKSPACE_ROOT}${NC}"
echo -e "[DHC] Content source: ${BOLD}${CABRAL_SKILLS_REPO}@${CABRAL_SKILLS_TAG}${NC}\n"

# Verify system utilities
if ! command -v curl &> /dev/null; then
    echo -e "${RED}ERROR: 'curl' is required but not installed. Exiting.${NC}" >&2
    exit 1
fi

if ! command -v unzip &> /dev/null; then
    echo -e "${RED}ERROR: 'unzip' is required but not installed. Exiting.${NC}" >&2
    exit 1
fi

# ── Download targets ─────────────────────────────────────────────────────────
DHC_ZIP="dhc_archive.zip"
DHC_EXTRACT="antigravity-dynamic-harness-configuration-main"
DHC_ZIP_URL="https://github.com/carlosmscabral/antigravity-dynamic-harness-configuration/archive/refs/heads/main.zip"

SKILLS_ZIP="cabral_skills_archive.zip"
SKILLS_ZIP_URL="https://github.com/${CABRAL_SKILLS_REPO}/archive/refs/tags/${CABRAL_SKILLS_TAG}.zip"

# 1) Fetch the DHC repo (for the configurator agent). Latest/main is fine — this
#    is the installer itself, not the pinned content.
echo -e "[DHC] Fetching harness-configurator agent from DHC repo..."
curl -fsSL -o "$DHC_ZIP" "$DHC_ZIP_URL"
unzip -q -o "$DHC_ZIP"

# 2) Fetch the cabral-skills monorepo at the PINNED TAG (plugins + skills).
#    curl -f makes a nonexistent tag fail fast with a clear error.
echo -e "[DHC] Fetching plugins + skills from ${CABRAL_SKILLS_REPO}@${CABRAL_SKILLS_TAG}..."
if ! curl -fsSL -o "$SKILLS_ZIP" "$SKILLS_ZIP_URL"; then
    echo -e "${RED}ERROR: Could not download ${CABRAL_SKILLS_REPO}@${CABRAL_SKILLS_TAG}.${NC}" >&2
    echo -e "${RED}       Verify the tag exists: ${SKILLS_ZIP_URL}${NC}" >&2
    rm -f "$DHC_ZIP" "$SKILLS_ZIP"; rm -rf "$DHC_EXTRACT"
    exit 1
fi
unzip -q -o "$SKILLS_ZIP"

# GitHub strips the leading "v" from the extracted tag folder (cabral-skills-1.0.0).
# Resolve by glob rather than hardcoding.
SKILLS_EXTRACT=$(find . -maxdepth 1 -type d -name 'cabral-skills-*' | head -n 1)
if [ -z "$SKILLS_EXTRACT" ] || [ ! -d "$SKILLS_EXTRACT/plugins" ]; then
    echo -e "${RED}ERROR: cabral-skills archive did not contain a plugins/ directory.${NC}" >&2
    rm -f "$DHC_ZIP" "$SKILLS_ZIP"; rm -rf "$DHC_EXTRACT" "$SKILLS_EXTRACT"
    exit 1
fi

# ── Provision local workspace ────────────────────────────────────────────────
echo -e "[DHC] Provisioning local workspace structures..."
# Clean rebuild of the dormant caches and the configurator agent.
rm -rf .agents/agents/harness-configurator
rm -rf .agents/plugins_cache
rm -rf .agents/skills_cache

mkdir -p .agents/agents
mkdir -p .agents/plugins_cache
mkdir -p .agents/skills_cache

# Clean up any legacy, flat harness-configurator.md file from previous versions
rm -f .agents/agents/harness-configurator.md

# Deploy the configurator agent (from the DHC repo). The "/." copies the CONTENTS
# of agents/ into .agents/agents/ so the result is
# .agents/agents/harness-configurator/ (not a nested .agents/agents/agents/).
echo -e "[DHC] Deploying harness-configurator agent..."
if [ -d "$DHC_EXTRACT/agents" ]; then
    cp -R "$DHC_EXTRACT/agents/". .agents/agents/
fi

# Stage plugins (dormant) and skills (local cache) from cabral-skills@tag.
echo -e "[DHC] Staging plugins into dormant cache..."
cp -R "$SKILLS_EXTRACT/plugins/". .agents/plugins_cache/

echo -e "[DHC] Staging skills into local cache (air-gap-safe promotion source)..."
if [ -d "$SKILLS_EXTRACT/skills" ]; then
    cp -R "$SKILLS_EXTRACT/skills/". .agents/skills_cache/
fi

# Make any scripts inside the harness, cached plugins, and cached skills executable
echo -e "[DHC] Enforcing execution permissions on scripts..."
find .agents/ -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
find .agents/ -name "*.py" -exec chmod +x {} + 2>/dev/null || true

# Keep the build-time caches out of git. They are the offline install source for
# future reconfiguration (kept on purpose, esp. for air-gapped setups), but must
# never be committed into the developer's repo. Append idempotently — only the
# caches, not the rest of .agents/ (rules/mcp/AGENTS.md may be worth committing).
echo -e "[DHC] Ensuring build-time caches are git-ignored..."
if ! grep -qsF ".agents/plugins_cache/" .gitignore 2>/dev/null; then
    {
        echo ""
        echo "# DHC build-time caches (offline install source; do not commit)"
        echo ".agents/plugins_cache/"
        echo ".agents/skills_cache/"
    } >> .gitignore
fi

# ── Cleanup (preserve plugins_cache/ + skills_cache/) ────────────────────────
echo -e "[DHC] Cleaning up temporary download caches..."
rm -f "$DHC_ZIP" "$SKILLS_ZIP"
rm -rf "$DHC_EXTRACT" "$SKILLS_EXTRACT"

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

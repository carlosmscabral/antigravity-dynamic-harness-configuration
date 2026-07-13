#!/usr/bin/env python3
"""
🚀 Antigravity Dynamic Harness Configurator (DHC) Remote Installer
Installs and provisions the DHC secure local environment into your current workspace.

Usage:
  curl -fsSL https://raw.githubusercontent.com/carlosmscabral/antigravity-okf-customizations/main/install.py | python3
"""

import os
import sys
import urllib.request
import ssl

REPO_RAW_URL = "https://raw.githubusercontent.com/carlosmscabral/antigravity-okf-customizations/main"

# Map of remote source paths to local target paths
INSTALL_MANIFEST = {
    # Harness Configurator Agent Prompt
    "agents/harness-configurator.md": ".agents/agents/harness-configurator.md",
    
    # Standard Harness Plugin
    ".agents/plugins/standard-harness/hooks.json": ".agents/plugins/standard-harness/hooks.json",
    ".agents/plugins/standard-harness/rules/documentation.md": ".agents/plugins/standard-harness/rules/documentation.md",
    ".agents/plugins/standard-harness/rules/testing-conventions.md": ".agents/plugins/standard-harness/rules/testing-conventions.md",
    ".agents/plugins/standard-harness/scripts/pre-test.sh": ".agents/plugins/standard-harness/scripts/pre-test.sh",
    ".agents/plugins/standard-harness/skills/pytest-linter/SKILL.md": ".agents/plugins/standard-harness/skills/pytest-linter/SKILL.md",
    ".agents/plugins/standard-harness/agents/refactoring-expert.md": ".agents/plugins/standard-harness/agents/refactoring-expert.md",
    
    # Strict Banking Harness Plugin
    ".agents/plugins/strict-banking-harness/hooks.json": ".agents/plugins/strict-banking-harness/hooks.json",
    ".agents/plugins/strict-banking-harness/rules/air-gap.md": ".agents/plugins/strict-banking-harness/rules/air-gap.md",
    ".agents/plugins/strict-banking-harness/rules/secrets.md": ".agents/plugins/strict-banking-harness/rules/secrets.md",
    ".agents/plugins/strict-banking-harness/scripts/command-blocker.sh": ".agents/plugins/strict-banking-harness/scripts/command-blocker.sh",
    ".agents/plugins/strict-banking-harness/skills/sec-auditor/SKILL.md": ".agents/plugins/strict-banking-harness/skills/sec-auditor/SKILL.md",
    ".agents/plugins/strict-banking-harness/agents/crypto-auditor.md": ".agents/plugins/strict-banking-harness/agents/crypto-auditor.md"
}

# Executable scripts that require chmod +x
EXECUTABLE_SCRIPTS = [
    ".agents/plugins/standard-harness/scripts/pre-test.sh",
    ".agents/plugins/strict-banking-harness/scripts/command-blocker.sh"
]

def main():
    print("=" * 68)
    print("     🚀 ANTIGRAVITY DYNAMIC HARNESS CONFIGURATOR (DHC) REMOTE INSTALLER")
    print("=" * 68)
    
    workspace_root = os.getcwd()
    print(f"[DHC] Local target workspace: {workspace_root}\n")

    # Bypass SSL verification if running in tight corporate proxies
    ssl_context = ssl._create_unverified_context()

    # Iterate over files and download them
    success_count = 0
    for remote_path, local_path in INSTALL_MANIFEST.items():
        # Clean local path separator
        local_path = os.path.normpath(local_path)
        
        # Create parent directories
        parent_dir = os.path.dirname(local_path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)
            
        url = f"{REPO_RAW_URL}/{remote_path}"
        print(f"[DHC] Fetching remote asset: {remote_path} ...", end="", flush=True)
        
        try:
            with urllib.request.urlopen(url, context=ssl_context, timeout=10) as response:
                content = response.read()
                with open(local_path, "wb") as f:
                    f.write(content)
            print(" ✅ OK")
            success_count += 1
        except Exception as e:
            print(f" ❌ ERROR: {e}")

    # Set execution permissions on scripts
    for script_path in EXECUTABLE_SCRIPTS:
        normalized_script = os.path.normpath(script_path)
        if os.path.exists(normalized_script):
            try:
                os.chmod(normalized_script, 0o755)
                print(f"[DHC] Marked script as executable: {normalized_script}")
            except Exception as e:
                print(f"[DHC] Warning: Failed to chmod script {normalized_script}: {e}")

    print("\n" + "=" * 68)
    if success_count == len(INSTALL_MANIFEST):
        print("🎉 SUCCESS! DHC JIT-harness assets downloaded and ready.")
        print("=" * 68)
        print("\nTo launch the interactive configuration session with your setup agent:")
        print("      agy --agent harness-configurator")
        print("\nThis will:")
        print("  1. Silently scan your code files and dependencies.")
        print("  2. Propose relevant rules, ignores, and secure upstream sources.")
        print("  3. Provision your workspace security and testing boundaries JIT!")
    else:
        print(f"⚠️ COMPLETED WITH WARNINGS ({success_count}/{len(INSTALL_MANIFEST)} assets downloaded).")
        print("Please check your network connection and proxy configurations.")
    print("=" * 68)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🚀 Antigravity Dynamic Harness Configurator (DHC) — Harness Integrity Verifier
#
# Verifies a provisioned workspace under the install-based model:
#   - plugins are registered via `agy plugin install` (skills/agents/hooks/mcp/commands)
#   - rules are authored as workspace policy under .agents/rules/
#   - workspace-level .antigravityignore / mcp_config.json / hooks.json are optional

import os
import sys
import json
import shutil
import subprocess

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"


def check_file_executable(filepath):
    """Checks if a file exists and is executable; attempts to remediate if not."""
    if not os.path.exists(filepath):
        return False, "File not found"
    if os.access(filepath, os.X_OK):
        return True, "Executable"
    try:
        os.chmod(filepath, os.stat(filepath).st_mode | 0o111)
        return True, "Auto-remediated (chmod +x applied)"
    except Exception as e:
        return False, f"Not executable & failed to chmod: {str(e)}"


def verify_harness():
    workspace_root = os.getcwd()
    agents_dir = os.path.join(workspace_root, ".agents")

    print(f"\n{BLUE}{BOLD}================================================================{RESET}")
    print(f"{BLUE}{BOLD}📋 RUNNING ANTIGRAVITY HARNESS INTEGRITY & REACHABILITY AUDIT...{RESET}")
    print(f"{BLUE}{BOLD}================================================================{RESET}\n")

    if not os.path.exists(agents_dir):
        print(f"{RED}[ERROR] No configured .agents/ harness directory found in this workspace.{RESET}")
        print("Please run the installer and the Harness Configurator Agent first.")
        sys.exit(1)

    warnings_count = 0
    errors_count = 0

    # ---------------------------------------------------------
    # 1. Registered plugins (agy plugin install)
    # ---------------------------------------------------------
    print(f"{BOLD}[1/5] Verifying Registered Plugins (agy plugin list)...{RESET}")
    agy = shutil.which("agy")
    if not agy:
        print(f"  {YELLOW}[-] 'agy' not found in $PATH — skipping plugin registry check.{RESET}")
        warnings_count += 1
    else:
        try:
            out = subprocess.run([agy, "plugin", "list"], capture_output=True, text=True, timeout=30)
            imports = []
            try:
                imports = (json.loads(out.stdout or "{}") or {}).get("imports", [])
            except json.JSONDecodeError:
                pass
            if imports:
                for p in imports:
                    comps = ", ".join(p.get("components", [])) or "no components"
                    print(f"  {GREEN}[✓]{RESET} Plugin: {p.get('name','?'):<28} [{comps}]")
            else:
                print(f"  {YELLOW}[⚠️] No imported plugins. If you selected plugins, run `agy plugin install` for each.{RESET}")
                warnings_count += 1
        except Exception as e:
            print(f"  {YELLOW}[⚠️] Could not query plugin registry: {e}{RESET}")
            warnings_count += 1
    print()

    # ---------------------------------------------------------
    # 2. Workspace rules (.agents/rules/) — authored policy
    # ---------------------------------------------------------
    rules_dir = os.path.join(agents_dir, "rules")
    print(f"{BOLD}[2/5] Verifying Workspace Rules (.agents/rules/)...{RESET}")
    if os.path.isdir(rules_dir):
        rule_files = [f for f in os.listdir(rules_dir) if f.endswith(".md")]
        if rule_files:
            for r in sorted(rule_files):
                print(f"  {GREEN}[✓]{RESET} Rule: {r}")
        else:
            print(f"  {YELLOW}[-] .agents/rules/ exists but contains no .md rules.{RESET}")
    else:
        print(f"  {YELLOW}[-] No .agents/rules/ directory (no authored workspace policy).{RESET}")
    print()

    # ---------------------------------------------------------
    # 3. Workspace ignore boundaries (.antigravityignore)
    # ---------------------------------------------------------
    ignore_file = os.path.join(workspace_root, ".antigravityignore")
    print(f"{BOLD}[3/5] Checking Workspace Ignore Boundaries...{RESET}")
    if os.path.exists(ignore_file):
        print(f"  {GREEN}[✓] .antigravityignore template .................... [PLACED]{RESET}")
    else:
        print(f"  {YELLOW}[⚠️] .antigravityignore is missing in root .......... [WARNING]{RESET}")
        warnings_count += 1
    print()

    # ---------------------------------------------------------
    # 4. Workspace-level hooks (.agents/hooks.json) — OPTIONAL
    #    (plugin hooks are registered by `agy plugin install`, not here)
    # ---------------------------------------------------------
    hooks_file = os.path.join(agents_dir, "hooks.json")
    print(f"{BOLD}[4/5] Verifying Workspace-Level Hooks (optional)...{RESET}")
    if os.path.exists(hooks_file):
        try:
            with open(hooks_file, "r", encoding="utf-8") as f:
                hooks_data = json.load(f)
            hook_scripts = set()

            def extract_scripts(node):
                if isinstance(node, dict):
                    if "command" in node and isinstance(node["command"], str):
                        cmd = node["command"].split()[0]
                        if cmd.endswith(".sh") or cmd.endswith(".py"):
                            hook_scripts.add(cmd)
                    for val in node.values():
                        extract_scripts(val)
                elif isinstance(node, list):
                    for item in node:
                        extract_scripts(item)

            extract_scripts(hooks_data)
            if hook_scripts:
                for script in sorted(hook_scripts):
                    ok, status_msg = check_file_executable(os.path.join(workspace_root, script))
                    if ok:
                        color = GREEN if status_msg == "Executable" else YELLOW
                        print(f"  {GREEN}[✓]{RESET} Script Hook: {script:<40} {color}[{status_msg}]{RESET}")
                    else:
                        print(f"  {RED}[✗]{RESET} Script Hook: {script:<40} {RED}[BROKEN: {status_msg}]{RESET}")
                        errors_count += 1
            else:
                print(f"  {GREEN}[✓] Workspace hooks.json active with no external script dependencies.{RESET}")
        except Exception as e:
            print(f"  {RED}[✗] Failed to parse hooks.json: {str(e)}{RESET}")
            errors_count += 1
    else:
        print(f"  {YELLOW}[-] No workspace .agents/hooks.json (plugin hooks are registered via agy plugin install).{RESET}")
    print()

    # ---------------------------------------------------------
    # 5. Workspace MCP servers (.agents/mcp_config.json) — OPTIONAL
    # ---------------------------------------------------------
    mcp_file = os.path.join(agents_dir, "mcp_config.json")
    print(f"{BOLD}[5/5] Auditing Workspace MCP Servers (optional)...{RESET}")
    if os.path.exists(mcp_file):
        try:
            with open(mcp_file, "r", encoding="utf-8") as f:
                mcp_data = json.load(f)
            servers = mcp_data.get("mcpServers", {})
            if servers:
                for server_name, config in sorted(servers.items()):
                    command = config.get("command")
                    if command:
                        if shutil.which(command):
                            print(f"  {GREEN}[✓]{RESET} MCP Server [{server_name}]: command '{command}' ... {GREEN}[AVAILABLE]{RESET}")
                        else:
                            print(f"  {RED}[✗]{RESET} MCP Server [{server_name}]: command '{command}' ... {RED}[UNAVAILABLE in $PATH]{RESET}")
                            errors_count += 1
                    else:
                        print(f"  {YELLOW}[⚠️] MCP Server [{server_name}]: missing launch command.{RESET}")
                        warnings_count += 1
            else:
                print(f"  {YELLOW}[-] mcp_config.json has no registered servers.{RESET}")
        except Exception as e:
            print(f"  {RED}[✗] Failed to parse mcp_config.json: {str(e)}{RESET}")
            errors_count += 1
    else:
        print(f"  {YELLOW}[-] No workspace .agents/mcp_config.json (plugin MCP servers are registered via agy plugin install).{RESET}")

    # ---------------------------------------------------------
    # Verdict
    # ---------------------------------------------------------
    print(f"\n{BLUE}{BOLD}================================================================{RESET}")
    print(f"{BLUE}{BOLD}🏁 HARNESS INTEGRITY AUDIT RESULTS: {RESET}", end="")
    if errors_count > 0:
        print(f"{RED}{BOLD}NON-COMPLIANT ({errors_count} Errors, {warnings_count} Warnings){RESET}")
        print(f"{BLUE}{BOLD}================================================================{RESET}")
        print(f"{RED}[CRITICAL] Some components are broken or unreachable. Review the errors above.{RESET}\n")
        sys.exit(1)
    elif warnings_count > 0:
        print(f"{YELLOW}{BOLD}COMPLIANT WITH WARNINGS ({warnings_count} Warnings){RESET}")
        print(f"{BLUE}{BOLD}================================================================{RESET}")
        print(f"{YELLOW}[ADVISORY] Active components verified; some optional configs are absent.{RESET}\n")
    else:
        print(f"{GREEN}{BOLD}FULLY COMPLIANT (0 Errors, 0 Warnings){RESET}")
        print(f"{BLUE}{BOLD}================================================================{RESET}")
        print(f"{GREEN}🎉 Registered plugins, workspace rules, and configs are all in order!{RESET}\n")


if __name__ == "__main__":
    verify_harness()

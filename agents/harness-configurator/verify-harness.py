#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🚀 Antigravity Dynamic Harness Configurator (DHC) — Harness Integrity Verifier
#
# Verifies a workspace provisioned by dhc_provision.py, reading its deterministic receipt
# (.agents/.dhc-provision.json):
#   - DEFAULT mode: plugins under .agents/plugins/* (auto-discovered by interactive `agy`)
#   - FLATTEN mode: components in direct scope (.agents/skills, .agents/agents, and
#     merged .agents/hooks.json / .agents/mcp_config.json) — loads under `agy -p` too
#   - rules are authored workspace policy under .agents/rules/
# Falls back to directory inference when no receipt is present (pre-1.1 workspaces).

import os
import sys
import json
import shutil


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

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
    # 1. Provisioned harness — from the dhc_provision receipt
    #    (falls back to directory inference for pre-1.1 workspaces)
    # ---------------------------------------------------------
    print(f"{BOLD}[1/5] Verifying Provisioned Harness (receipt)...{RESET}")
    receipt = _read_json(os.path.join(agents_dir, ".dhc-provision.json"))
    if receipt is not None:
        mode = receipt.get("mode", "?")
        if mode == "flatten":
            print(f"  {GREEN}[✓]{RESET} Mode: FLATTEN (direct scope — loads interactive AND headless `agy -p`)")
        else:
            print(f"  {GREEN}[✓]{RESET} Mode: DEFAULT (plugin auto-discovery under .agents/plugins/)")
            print(f"  {YELLOW}[⚠️] Loads in interactive `agy` only — `agy -p` (CI/headless/goal) skips plugins.{RESET}")
            print(f"      For headless coverage, re-provision with DHC_FLATTEN enabled.")
            warnings_count += 1
        hooks_now = _read_json(os.path.join(agents_dir, "hooks.json")) or {}
        mcp_now = (_read_json(os.path.join(agents_dir, "mcp_config.json")) or {}).get("mcpServers", {})
        for name, entry in sorted(receipt.get("plugins", {}).items()):
            miss_paths = [p for p in entry.get("createdPaths", [])
                          if not os.path.exists(os.path.join(workspace_root, *p.split("/")))]
            miss_hooks = [g for g in entry.get("hookGroups", []) if g not in hooks_now]
            miss_mcp = [s for s in entry.get("mcpServers", []) if s not in mcp_now]
            if miss_paths or miss_hooks or miss_mcp:
                print(f"  {RED}[✗]{RESET} {name}: missing "
                      f"{miss_paths + [f'hook:{g}' for g in miss_hooks] + [f'mcp:{s}' for s in miss_mcp]}")
                errors_count += 1
            else:
                print(f"  {GREEN}[✓]{RESET} {name} "
                      f"({len(entry.get('createdPaths', []))} paths, "
                      f"{len(entry.get('hookGroups', []))} hooks, {len(entry.get('mcpServers', []))} mcp)")
        if receipt.get("collisions"):
            n = len(receipt["collisions"])
            print(f"  {YELLOW}[⚠️] {n} collision(s) recorded — some plugin controls were skipped (name clashes).{RESET}")
            warnings_count += 1
        if not receipt.get("plugins"):
            print(f"  {YELLOW}[-] Receipt records no provisioned plugins.{RESET}")
        sp = receipt.get("superpowers") or {}
        if sp.get("active"):
            sp_missing = [p for p in sp.get("createdPaths", [])
                          if not os.path.exists(os.path.join(workspace_root, *p.split("/")))]
            if sp_missing:
                print(f"  {RED}[✗]{RESET} Superpowers active but missing: {sp_missing}")
                errors_count += 1
            else:
                n = len([p for p in sp.get("createdPaths", []) if p.startswith(".agents/skills/")])
                print(f"  {GREEN}[✓]{RESET} Superpowers methodology active ({n} skills + always-on bootstrap rule).")
                print(f"       Spec-first is instruction-enforced; launch `agy --mode=plan` for a session-level gate.")
    else:
        # Fallback: directory inference (no receipt / pre-1.1 workspace)
        plugins_dir = os.path.join(agents_dir, "plugins")
        plugin_dirs = ([d for d in os.listdir(plugins_dir)
                        if os.path.isfile(os.path.join(plugins_dir, d, "plugin.json"))]
                       if os.path.isdir(plugins_dir) else [])
        if plugin_dirs:
            print(f"  {GREEN}[✓]{RESET} Mode: DEFAULT (no receipt; inferred from .agents/plugins/)")
            for p in sorted(plugin_dirs):
                print(f"        - {p}")
            warnings_count += 1
        else:
            print(f"  {YELLOW}[⚠️] No receipt and no .agents/plugins/ — nothing provisioned.{RESET}")
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
        print(f"  {YELLOW}[-] No workspace .agents/hooks.json (default mode: plugin hooks load from .agents/plugins/; flatten mode merges them here).{RESET}")
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
        print(f"  {YELLOW}[-] No workspace .agents/mcp_config.json (default mode: plugin MCP loads from .agents/plugins/; flatten mode merges them here).{RESET}")

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

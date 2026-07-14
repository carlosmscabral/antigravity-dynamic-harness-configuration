#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🚀 Antigravity Dynamic Harness Configurator (DHC) — Harness Integrity Verifier

import os
import sys
import json
import shutil

# ANSI Colors for styled terminal reports
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def check_file_executable(filepath):
    """Checks if a file exists and is executable. If not, attempts to make it executable."""
    if not os.path.exists(filepath):
        return False, "File not found"
    
    # Check if executable
    if os.access(filepath, os.X_OK):
        return True, "Executable"
    
    # Try to make executable
    try:
        os.chmod(filepath, os.stat(filepath).st_mode | 0o111)
        return True, "Auto-remediated (chmod +x applied)"
    except Exception as e:
        return False, f"Not executable & failed to chmod: {str(e)}"

def verify_harness():
    """Runs a high-fidelity integrity check on the configured workspace harness."""
    # Find workspace root (assumed to be current working directory)
    workspace_root = os.getcwd()
    agents_dir = os.path.join(workspace_root, ".agents")
    
    print(f"\n{BLUE}{BOLD}================================================================{RESET}")
    print(f"{BLUE}{BOLD}📋 RUNNING ANTIGRAVITY HARNESS INTEGRITY & REACHABILITY AUDIT...{RESET}")
    print(f"{BLUE}{BOLD}================================================================{RESET}\n")
    
    if not os.path.exists(agents_dir):
        print(f"{RED}[ERROR] No configured .agents/ harness directory found in this workspace.{RESET}")
        print(f"Please run the bootstrap/installation and run the Harness Configurator Agent first.")
        sys.exit(1)
        
    warnings_count = 0
    errors_count = 0
    
    # ---------------------------------------------------------
    # 1. Verify Ignorables (.antigravityignore)
    # ---------------------------------------------------------
    ignore_file = os.path.join(workspace_root, ".antigravityignore")
    print(f"{BOLD}[1/3] Checking Workspace Ignore Boundaries...{RESET}")
    if os.path.exists(ignore_file):
        print(f"  {GREEN}[✓] .antigravityignore template .................... [PLACED]{RESET}")
    else:
        print(f"  {YELLOW}[⚠️] .antigravityignore is missing in root .......... [WARNING]{RESET}")
        print(f"      (This could cause coding agents to bloat their contexts with build/temporary caches).")
        warnings_count += 1
        
    print()

    # ---------------------------------------------------------
    # 2. Verify Command Interceptors (hooks.json)
    # ---------------------------------------------------------
    hooks_file = os.path.join(agents_dir, "hooks.json")
    print(f"{BOLD}[2/3] Verifying Interceptor Hooks & Scripts...{RESET}")
    if os.path.exists(hooks_file):
        try:
            with open(hooks_file, 'r', encoding='utf-8') as f:
                hooks_data = json.load(f)
            
            hook_scripts = set()
            # Walk JSON structure to collect hook script paths
            def extract_scripts(node):
                if isinstance(node, dict):
                    if "command" in node and isinstance(node["command"], str):
                        # Filter out system utility commands, keep script paths
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
                    script_path = os.path.join(workspace_root, script)
                    ok, status_msg = check_file_executable(script_path)
                    if ok:
                        # Display OK or remediated status
                        status_color = GREEN if status_msg == "Executable" else YELLOW
                        print(f"  {GREEN}[✓]{RESET} Script Hook: {script:<40} {status_color}[{status_msg}]{RESET}")
                    else:
                        print(f"  {RED}[✗]{RESET} Script Hook: {script:<40} {RED}[BROKEN: {status_msg}]{RESET}")
                        errors_count += 1
            else:
                print(f"  {GREEN}[✓] hooks.json is active with no external script dependencies.{RESET}")
                
        except Exception as e:
            print(f"  {RED}[✗] Failed to parse hooks.json: {str(e)}{RESET}")
            errors_count += 1
    else:
        print(f"  {YELLOW}[-] hooks.json is inactive (no active command interceptors).{RESET}")
        
    print()

    # ---------------------------------------------------------
    # 3. Verify MCP Server Availability (mcp_config.json)
    # ---------------------------------------------------------
    mcp_file = os.path.join(agents_dir, "mcp_config.json")
    print(f"{BOLD}[3/3] Auditing MCP Server Executables & Reachability...{RESET}")
    if os.path.exists(mcp_file):
        try:
            with open(mcp_file, 'r', encoding='utf-8') as f:
                mcp_data = json.load(f)
            
            servers = mcp_data.get("mcpServers", {})
            if servers:
                for server_name, config in sorted(servers.items()):
                    command = config.get("command")
                    if command:
                        # Verify executable binary exists in system $PATH
                        found_path = shutil.which(command)
                        if found_path:
                            print(f"  {GREEN}[✓]{RESET} MCP Server [{server_name}]: command '{command}' ... {GREEN}[AVAILABLE]{RESET}")
                        else:
                            print(f"  {RED}[✗]{RESET} MCP Server [{server_name}]: command '{command}' ... {RED}[UNAVAILABLE in $PATH]{RESET}")
                            print(f"      (Ensure the required engine is installed in the local workspace shell environment.)")
                            errors_count += 1
                    else:
                        print(f"  {YELLOW}[⚠️] MCP Server [{server_name}]: missing launch command configuration.{RESET}")
                        warnings_count += 1
            else:
                print(f"  {YELLOW}[-] mcp_config.json has no registered servers.{RESET}")
        except Exception as e:
            print(f"  {RED}[✗] Failed to parse mcp_config.json: {str(e)}{RESET}")
            errors_count += 1
    else:
        print(f"  {YELLOW}[-] mcp_config.json is not configured (no active MCP tools).{RESET}")
        
    # ---------------------------------------------------------
    # 4. Final Verdict Display
    # ---------------------------------------------------------
    print(f"\n{BLUE}{BOLD}================================================================{RESET}")
    print(f"{BLUE}{BOLD}🏁 HARNESS INTEGRITY AUDIT RESULTS: {RESET}", end="")
    
    if errors_count > 0:
        print(f"{RED}{BOLD}NON-COMPLIANT ({errors_count} Errors, {warnings_count} Warnings){RESET}")
        print(f"{BLUE}{BOLD}================================================================{RESET}")
        print(f"{RED}[CRITICAL] Some components are broken or unreachable. Review the errors above.")
        print(f"Fix the paths/permissions and re-run this tool before handing off the session.{RESET}\n")
        sys.exit(1)
    elif warnings_count > 0:
        print(f"{YELLOW}{BOLD}COMPLIANT WITH WARNINGS ({warnings_count} Warnings){RESET}")
        print(f"{BLUE}{BOLD}================================================================{RESET}")
        print(f"{YELLOW}[ADVISORY] All active scripts and servers are verified, but some optional configs are missing.{RESET}\n")
    else:
        print(f"{GREEN}{BOLD}FULLY COMPLIANT (0 Errors, 0 Warnings){RESET}")
        print(f"{BLUE}{BOLD}================================================================{RESET}")
        print(f"{GREEN}🎉 All active command hooks, execution permissions, and MCP servers are functional!{RESET}\n")

if __name__ == "__main__":
    verify_harness()

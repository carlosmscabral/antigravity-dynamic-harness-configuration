#!/usr/bin/env python3
"""
Dynamic Harness Configurator (DHC) — Bootstrap Installer
Part of the Antigravity OKF Customizations Ecosystem.

This script initializes the DHC Agent inside any cloned repository, 
symlinking/copying the central Antigravity Customization Library (ACL) plugins
and setting up the initial interactive harness-engineering loop.
"""

import os
import sys
import shutil
from pathlib import Path

# Color styling for terminal outputs
GREEN = "\033[92m"
BLUE = "\033[94m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header():
    print(f"\n{BLUE}{BOLD}===================================================================={RESET}")
    print(f"{BLUE}{BOLD}     🚀 ANTIGRAVITY DYNAMIC HARNESS CONFIGURATOR (DHC) BOOTSTRAP    {RESET}")
    print(f"{BLUE}{BOLD}===================================================================={RESET}\n")

def bootstrap():
    print_header()
    
    # 1. Determine active paths
    # Source path is where this bootstrap.py file resides
    src_dir = Path(__file__).parent.resolve()
    # Target path is the current working directory where the script is executed
    target_dir = Path(os.getcwd()).resolve()
    
    print(f"{BLUE}[DHC]* Source Customizations Directory: {src_dir}{RESET}")
    print(f"{BLUE}[DHC]* Target Project Workspace Root:   {target_dir}{RESET}\n")
    
    # Check if target is same as source (prevent self-bootstrapping)
    if src_dir == target_dir:
        print(f"{YELLOW}[DHC] Source and target are identical. Entering developer sandbox mode.{RESET}")
    
    # 2. Establish target agent folders
    target_agents_dir = target_dir / ".agents" / "agents"
    target_plugins_dir = target_dir / ".agents" / "plugins"
    
    print(f"{GREEN}[DHC] Provisioning local workspace gates at .agents/...{RESET}")
    target_agents_dir.mkdir(parents=True, exist_ok=True)
    target_plugins_dir.mkdir(parents=True, exist_ok=True)
    
    # 3. Deploy the Harness Configurator Agent
    src_agent_prompt = src_dir / "agents" / "harness-configurator.md"
    target_agent_prompt = target_agents_dir / "harness-configurator.md"
    
    if not src_agent_prompt.exists():
        print(f"\033[91m[DHC ERROR] Could not find the source agent prompt at {src_agent_prompt}{RESET}")
        sys.exit(1)
        
    print(f"{GREEN}[DHC] Deploying Harness Configurator Agent prompt...{RESET}")
    shutil.copy2(src_agent_prompt, target_agent_prompt)
    
    # 4. Deploy standard/strict ACL Plugins
    src_plugins = src_dir / ".agents" / "plugins"
    if src_plugins.exists():
        print(f"{GREEN}[DHC] Linking customization library plugins...{RESET}")
        for plugin_folder in src_plugins.iterdir():
            if plugin_folder.is_dir():
                target_plugin = target_plugins_dir / plugin_folder.name
                if target_plugin.exists():
                    if target_plugin.is_symlink() or target_plugin.is_file():
                        target_plugin.unlink()
                    else:
                        shutil.rmtree(target_plugin)
                
                # We use symlinking for rapid, live updates during developer runs
                try:
                    os.symlink(plugin_folder, target_plugin)
                    print(f"      - Symlinked: {plugin_folder.name} -> .agents/plugins/{plugin_folder.name}")
                except Exception as e:
                    # Fallback to copy if symlinking not supported/permitted
                    shutil.copytree(plugin_folder, target_plugin)
                    print(f"      - Copied: {plugin_folder.name} -> .agents/plugins/{plugin_folder.name}")
    else:
        print(f"{YELLOW}[DHC WARNING] No central plugins folder discovered at {src_plugins}.{RESET}")
        
    print(f"\n{GREEN}{BOLD}===================================================================={RESET}")
    print(f"{GREEN}{BOLD}🎉 BOOTSTRAP COMPLETE! The Harness Configurator is ready to run.{RESET}")
    print(f"{GREEN}{BOLD}===================================================================={RESET}\n")
    print(f"{BOLD}Next Step: Run the dynamic configurator inside your terminal:{RESET}")
    print(f"      {YELLOW}{BOLD}agy --agent harness-configurator{RESET}\n")
    print(f"{BLUE}This will launch an interactive session where the configurator agent will:{RESET}")
    print(f"  1. Silently scan your directory to auto-suggest files and framework setups.")
    print(f"  2. Conduct a structured discovery chat to customize safety levels and databases.")
    print(f"  3. Write local settings.json, hooks, and ignorable structures dynamically!")
    print(f"====================================================================\n")

if __name__ == "__main__":
    bootstrap()

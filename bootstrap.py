#!/usr/bin/env python3
"""
Dynamic Harness Configurator (DHC) — Bootstrap Installer (developer / offline mode)
Part of the Antigravity OKF Customizations Ecosystem.

This script initializes the DHC Agent inside any cloned repository. The
configurator agent comes from THIS repo; the harness plugins and skills come
from a local checkout of the cabral-skills monorepo (the single source of
truth). Set CABRAL_SKILLS_DEV_PATH to point at that checkout — it defaults to a
sibling directory `../cabral-skills`.

Plugins are symlinked/copied into .agents/plugins_cache/ (dormant) and skills
into .agents/skills_cache/ (the air-gap-safe source the configurator copies
from at promotion time).
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
    
    # Resolve the cabral-skills monorepo checkout (source of plugins + skills).
    cabral_skills_dir = Path(
        os.environ.get("CABRAL_SKILLS_DEV_PATH", src_dir.parent / "cabral-skills")
    ).resolve()
    print(f"{BLUE}[DHC]* cabral-skills source (plugins + skills): {cabral_skills_dir}{RESET}")
    if not cabral_skills_dir.exists():
        print(f"\033[91m[DHC ERROR] cabral-skills checkout not found at {cabral_skills_dir}.{RESET}")
        print(f"{YELLOW}[DHC] Clone https://github.com/carlosmscabral/cabral-skills next to this repo,{RESET}")
        print(f"{YELLOW}      or set CABRAL_SKILLS_DEV_PATH to its location.{RESET}")
        sys.exit(1)

    # 2. Establish target agent folders
    target_agents_dir = target_dir / ".agents" / "agents" / "harness-configurator"
    target_plugins_dir = target_dir / ".agents" / "plugins_cache"
    target_skills_dir = target_dir / ".agents" / "skills_cache"

    def _clean_cache(path):
        """Remove a cache dir whose entries may be symlinks, files, or trees."""
        if path.exists():
            for item in path.iterdir():
                if item.is_symlink() or item.is_file():
                    item.unlink()
                else:
                    shutil.rmtree(item)
            path.rmdir()

    print(f"{GREEN}[DHC] Provisioning local workspace gates at .agents/...{RESET}")
    # Clean target folders to prevent stale ghost files
    if target_agents_dir.exists():
        shutil.rmtree(target_agents_dir)
    _clean_cache(target_plugins_dir)
    _clean_cache(target_skills_dir)

    target_agents_dir.mkdir(parents=True, exist_ok=True)
    target_plugins_dir.mkdir(parents=True, exist_ok=True)
    target_skills_dir.mkdir(parents=True, exist_ok=True)
    
    # Clean up any legacy, flat harness-configurator.md file from previous versions
    legacy_file = target_dir / ".agents" / "agents" / "harness-configurator.md"
    if legacy_file.exists():
        legacy_file.unlink()

    # 3. Deploy the WHOLE Harness Configurator dir (agent.md, verify-harness.py,
    #    dhc_provision.py, merge_config.py + shim). Whole-dir copy matches install.sh's
    #    `cp -R agents/.` so dev/offline mode has the provisioner + merge helper too.
    src_cfg = src_dir / "agents" / "harness-configurator"
    if not (src_cfg / "agent.md").exists():
        print(f"\033[91m[DHC ERROR] Could not find the configurator at {src_cfg}{RESET}")
        sys.exit(1)

    print(f"{GREEN}[DHC] Deploying Harness Configurator assets...{RESET}")
    if target_agents_dir.exists():
        shutil.rmtree(target_agents_dir)
    shutil.copytree(src_cfg, target_agents_dir,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for py in target_agents_dir.glob("*.py"):
        os.chmod(py, os.stat(py).st_mode | 0o111)


    # 4. Stage plugins + skills from the cabral-skills monorepo into the caches.
    #    Symlink for rapid live updates during developer runs; fall back to copy.
    def _stage(src_root, target_root, label):
        if not src_root.exists():
            print(f"{YELLOW}[DHC WARNING] No {label} folder discovered at {src_root}.{RESET}")
            return
        print(f"{GREEN}[DHC] Staging {label} in cache...{RESET}")
        for entry in src_root.iterdir():
            if not entry.is_dir():
                continue
            target_entry = target_root / entry.name
            if target_entry.exists():
                if target_entry.is_symlink() or target_entry.is_file():
                    target_entry.unlink()
                else:
                    shutil.rmtree(target_entry)
            try:
                os.symlink(entry, target_entry)
                print(f"      - Symlinked: {entry.name} -> .agents/{target_root.name}/{entry.name}")
            except Exception:
                shutil.copytree(entry, target_entry)
                print(f"      - Copied: {entry.name} -> .agents/{target_root.name}/{entry.name}")

    _stage(cabral_skills_dir / "plugins", target_plugins_dir, "plugins")
    _stage(cabral_skills_dir / "skills", target_skills_dir, "skills")

    # Keep the build-time caches out of git (they are the offline install source
    # for reconfiguration, kept on purpose, but must never be committed).
    gitignore = target_dir / ".gitignore"
    existing = gitignore.read_text() if gitignore.exists() else ""
    if ".agents/plugins_cache/" not in existing:
        with open(gitignore, "a") as f:
            f.write(
                "\n# DHC build-time caches (offline install source; do not commit)\n"
                ".agents/plugins_cache/\n.agents/skills_cache/\n"
            )
        print(f"{GREEN}[DHC] Added .agents/*_cache/ to .gitignore.{RESET}")
        
    print(f"\n{GREEN}{BOLD}===================================================================={RESET}")
    print(f"{GREEN}{BOLD}🎉 BOOTSTRAP COMPLETE! The Harness Configurator is ready to run.{RESET}")
    print(f"{GREEN}{BOLD}===================================================================={RESET}\n")
    print(f"{BOLD}Next Step: Launch the interactive configuration session:{RESET}")
    print(f"  1. Run: {YELLOW}{BOLD}agy{RESET}")
    print(f"  2. Type: {YELLOW}{BOLD}/agents{RESET} and select {BOLD}harness-configurator{RESET}\n")
    print(f"{BLUE}This will launch an interactive session where the configurator agent will:{RESET}")
    print(f"  1. Silently scan your directory to auto-suggest files and framework setups.")
    print(f"  2. Conduct a structured discovery chat to customize safety levels and databases.")
    print(f"  3. Write local settings.json, hooks, and ignorable structures dynamically!")
    print(f"====================================================================\n")

if __name__ == "__main__":
    bootstrap()

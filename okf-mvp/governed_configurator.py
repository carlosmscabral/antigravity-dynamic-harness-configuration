#!/usr/bin/env python3
"""
governed_configurator.py
DHC OKF-Governed Dynamic Harness Configurator MVP Orchestrator.
Performs static workspace analysis, loads/merges hierarchical OKF manifests,
and JIT-provisions the hardened workspace harness configuration.
"""

import os
import sys
import json
import fnmatch
import tempfile
import subprocess
import shutil

# --- Configuration & Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CORP_REPO = "dhc-corp-global-config"
GROUP_REPO = "dhc-group-wealth-config"

MOCK_GLOBAL_PATH = os.path.join(BASE_DIR, "mock_remotes", "corp-global", "okf-global.json")
MOCK_GROUP_PATH = os.path.join(BASE_DIR, "mock_remotes", "group-wealth", "okf-group.json")

# --- Helper Functions ---

def fetch_remote_manifest(repo_name, filename):
    """
    Attempts to clone the remote configuration repository in a temp directory
    and read the manifest JSON, fully separating indexing from storage.
    """
    url = f"https://github.com/carlosmscabral/{repo_name}.git"
    temp_dir = tempfile.mkdtemp()
    try:
        # Run standard git clone with depth 1
        subprocess.run(
            ["git", "clone", "--depth", "1", url, temp_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        filepath = os.path.join(temp_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                return json.load(f)
    except Exception:
        pass
    finally:
        shutil.rmtree(temp_dir)
    return None

def load_manifest(repo_name, filename, fallback_path):
    """
    Attempts remote fetch, falling back seamlessly to local mock catalog.
    """
    data = fetch_remote_manifest(repo_name, filename)
    if data:
        print(f"✅ Loaded manifest [{filename}] dynamically from Remote GitHub Repo: carlosmscabral/{repo_name}")
        return data
    else:
        print(f"⚠️ Remote GitHub repo [carlosmscabral/{repo_name}] unreachable. Falling back to local offline OKF cache.")
        with open(fallback_path, "r") as f:
            return json.load(f)

def scan_workspace(target_path):
    """
    Silently scans the target directory to detect active files and languages.
    """
    detected_files = []
    for root, _, files in os.walk(target_path):
        # Ignore git or hidden config directories
        if ".git" in root or ".agents" in root:
            continue
        for file in files:
            # Get relative file path
            rel_path = os.path.relpath(os.path.join(root, file), target_path)
            detected_files.append(rel_path)
    return detected_files

def deep_merge_manifests(global_manifest, group_manifest, local_manifest=None):
    """
    Implements Hierarchical Deep Merge of manifest layers:
    Global (Corp) > Group (Division) > Local (Workspace).
    Higher tier properties (especially locking constraints) override lower tiers.
    """
    merged_plugins = {}

    # 1. Process Global Baseline (Tier 1)
    for plugin in global_manifest.get("plugins", []):
        p_id = plugin["id"]
        merged_plugins[p_id] = {
            "id": p_id,
            "version": plugin.get("version"),
            "enforcement": plugin.get("enforcement", "optional"),
            "locked": plugin.get("locked", False),
            "triggers": plugin.get("triggers", {}),
            "rules": plugin.get("rules", []),
            "hooks": plugin.get("hooks", {}),
            "source_tier": "Global (Corporate)"
        }

    # 2. Process Group Standards (Tier 2)
    for plugin in group_manifest.get("plugins", []):
        p_id = plugin["id"]
        if p_id in merged_plugins:
            existing = merged_plugins[p_id]
            # Higher tier locking constraints override group
            if not existing["locked"]:
                existing["enforcement"] = plugin.get("enforcement", existing["enforcement"])
                existing["locked"] = plugin.get("locked", existing["locked"])
            # Combine and deduplicate triggers
            existing_triggers = set(existing["triggers"].get("files", []))
            group_triggers = set(plugin.get("triggers", {}).get("files", []))
            existing["triggers"]["files"] = list(existing_triggers.union(group_triggers))
            # Merge rules
            existing["rules"] = list(set(existing["rules"] + plugin.get("rules", [])))
            # Merge hooks
            for h_type, h_cmds in plugin.get("hooks", {}).items():
                existing["hooks"][h_type] = list(set(existing["hooks"].get(h_type, []) + h_cmds))
        else:
            merged_plugins[p_id] = {
                "id": p_id,
                "version": plugin.get("version"),
                "enforcement": plugin.get("enforcement", "suggested"),
                "locked": plugin.get("locked", False),
                "triggers": plugin.get("triggers", {}),
                "rules": plugin.get("rules", []),
                "hooks": plugin.get("hooks", {}),
                "source_tier": "Group (Division)"
            }

    # 3. Process Local Workspace Specifics (Tier 3 - Optional)
    if local_manifest:
        for plugin in local_manifest.get("plugins", []):
            p_id = plugin["id"]
            if p_id in merged_plugins:
                existing = merged_plugins[p_id]
                # If locked upstream, local cannot override locks
                if not existing["locked"]:
                    existing["enforcement"] = plugin.get("enforcement", existing["enforcement"])
                    existing["locked"] = plugin.get("locked", existing["locked"])
                existing_triggers = set(existing["triggers"].get("files", []))
                local_triggers = set(plugin.get("triggers", {}).get("files", []))
                existing["triggers"]["files"] = list(existing_triggers.union(local_triggers))
                existing["rules"] = list(set(existing["rules"] + plugin.get("rules", [])))
                for h_type, h_cmds in plugin.get("hooks", {}).items():
                    existing["hooks"][h_type] = list(set(existing["hooks"].get(h_type, []) + h_cmds))
            else:
                merged_plugins[p_id] = {
                    "id": p_id,
                    "version": plugin.get("version"),
                    "enforcement": plugin.get("enforcement", "optional"),
                    "locked": plugin.get("locked", False),
                    "triggers": plugin.get("triggers", {}),
                    "rules": plugin.get("rules", []),
                    "hooks": plugin.get("hooks", {}),
                    "source_tier": "Local (Workspace)"
                }

    return merged_plugins

def check_triggers(workspace_files, triggers):
    """
    Evaluates whether any workspace file matches the plugin glob trigger filters.
    """
    trigger_globs = triggers.get("files", [])
    for file in workspace_files:
        for glob in trigger_globs:
            if fnmatch.fnmatch(file, glob):
                return True
    return False

# --- Core Orchestration Pipeline ---

def execute_configurator(target_workspace):
    print("==========================================================")
    print("⚙️ Booting OKF-Governed DHC Configurator Engine")
    print(f"🎯 Target Workspace: {target_workspace}")
    print("==========================================================")

    # 1. Pull / Fetch manifests (Remote Index Sync with Local Cache fallback)
    global_manifest = load_manifest(CORP_REPO, "okf-global.json", MOCK_GLOBAL_PATH)
    group_manifest = load_manifest(GROUP_REPO, "okf-group.json", MOCK_GROUP_PATH)

    # Optional local project overrides
    local_manifest = None
    local_okf_path = os.path.join(target_workspace, ".agents", "okf-local.json")
    if os.path.exists(local_okf_path):
        print("✅ Local workspace config [okf-local.json] detected.")
        with open(local_okf_path, "r") as f:
            local_manifest = json.load(f)

    # 2. Compile Unified Harness Catalog (Deep Merge)
    print("\n🔀 Merging governance layers...")
    unified_plugins = deep_merge_manifests(global_manifest, group_manifest, local_manifest)

    # 3. Static Analysis of Workspace
    print("🔍 Silently scanning workspace files...")
    workspace_files = scan_workspace(target_workspace)
    print(f"   Detected {len(workspace_files)} files.")

    # 4. Trigger Matcher & Dynamic Selection
    selected_plugins = []
    locked_enforced = []
    auto_suggested = []
    
    for p_id, plugin in unified_plugins.items():
        is_enforced = plugin["enforcement"] == "enforced_globally" or plugin["locked"]
        matches_triggers = check_triggers(workspace_files, plugin["triggers"])

        if is_enforced:
            selected_plugins.append(plugin)
            locked_enforced.append(p_id)
        elif matches_triggers:
            selected_plugins.append(plugin)
            auto_suggested.append(p_id)

    # 5. Interactive Interview Sim Output
    print("\n==========================================================")
    print("📋 DHC OKF HARNESS DISCOVERY REPORT")
    print("==========================================================")
    print(f"🔒 Corporate Mandated Policies (LOCKED):")
    for p_id in locked_enforced:
        print(f"   - {p_id} (Reason: Global SecOps Compliance Requirement)")
    print(f"⚡ Auto-Detected suggested profiles:")
    for p_id in auto_suggested:
        print(f"   - {p_id} (Reason: Trigger match on workspace stack)")
    print("==========================================================")

    # 6. JIT Assembly and Provisioning
    print("\n🏗️ Assembling and JIT-provisioning the workspace harness...")
    
    # Ensure target .agents directory exists
    agents_dir = os.path.join(target_workspace, ".agents")
    os.makedirs(agents_dir, exist_ok=True)

    # A. Assemble AGENTS.md (Unified Rules Document)
    agents_rules_path = os.path.join(target_workspace, ".agents", "AGENTS.md")
    rules_content = [
        "# Unified Harness Rule Specification",
        "<!-- GENERATED JIT BY DHC OKF-GOVERNED AGENT - DO NOT MANUALLY EDIT -->\n",
        "This workspace operates under a multi-tier governance model compiled from your group and corporate baseline catalogs.",
        "\n---"
    ]
    
    for plugin in selected_plugins:
        rules_content.append(f"\n## 🔌 Plugin: {plugin['id']} (Tier: {plugin['source_tier']})")
        for rule in plugin.get("rules", []):
            rules_content.append(f"*   {rule}")
        rules_content.append("\n---")

    with open(agents_rules_path, "w") as f:
        f.write("\n".join(rules_content))
    print(f"   📝 Wrote unified compliance rules to: .agents/AGENTS.md")

    # B. Assemble hooks.json (Tool and Command Interceptor Hooks)
    combined_hooks = {
        "pre-run": []
    }
    for plugin in selected_plugins:
        for hook_type, cmds in plugin.get("hooks", {}).items():
            if hook_type not in combined_hooks:
                combined_hooks[hook_type] = []
            combined_hooks[hook_type].extend(cmds)

    hooks_path = os.path.join(agents_dir, "hooks.json")
    with open(hooks_path, "w") as f:
        json.dump(combined_hooks, f, indent=2)
    print(f"   ⚙️ Wrote tool interceptor hooks to: .agents/hooks.json")

    # C. Assemble .antigravityignore
    ignore_path = os.path.join(target_workspace, ".antigravityignore")
    default_ignores = [
        "# Antigravity default ignore",
        "*.pyc",
        "__pycache__/",
        "*.log",
        ".git/",
        ".env",
        "*.db"
    ]
    with open(ignore_path, "w") as f:
        f.write("\n".join(default_ignores) + "\n")
    print(f"   🛡️ Wrote workspace ignore rules to: .antigravityignore")

    print("\n==========================================================")
    print("🎉 HARNESS PROVISIONING COMPLETED SUCCESSFULLY!")
    print("   Your development sandbox is secured and aligned.")
    print("   Launch commands:")
    print("   $ agy --sandbox")
    print("==========================================================")


if __name__ == "__main__":
    # If a target path is passed, use it. Otherwise, target a temporary test folder
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        # Create a temporary sandbox directory for test-running
        target = os.path.join(BASE_DIR, "test_sandbox")
        os.makedirs(target, exist_ok=True)
        # Create some sample files to trigger rules
        open(os.path.join(target, "package.json"), "a").close()
        open(os.path.join(target, "database.yaml"), "a").close()

    execute_configurator(target)

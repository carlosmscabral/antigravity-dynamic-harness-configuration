#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DHC deterministic provisioning core (roadmap 1.1).

The configurator agent authors a selection (discovery + interview) and calls this ONCE.
This script performs ALL mechanical promotion — reconcile, skill materialization, default
copy vs flatten distribution, script relocation + hook-path rewrite, in-process hook/mcp
merges, cache gitignore, and a deterministic receipt — so there is no agent-authored shell
in the mechanical path and identical selection -> identical result.

Usage:
    dhc_provision.py <selection.json>
        [--workspace DIR]        # project root (default: cwd)
        [--plugins-cache DIR]    # default: <workspace>/.agents/plugins_cache
        [--skills-cache DIR]     # default: <workspace>/.agents/skills_cache
        [--dry-run]              # compute + print the plan, write nothing
        [--quiet]

selection.json:
    { "schemaVersion": 1, "mode": "default"|"flatten", "plugins": [...], "sdd": false }

Exit: 0 ok/no-op, 1 provisioning error, 2 usage error.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys

import merge_config  # sibling module (same dir); dhc adds its dir to sys.path in main()

SCHEMA_VERSION = 1
RECEIPT_NAME = ".dhc-provision.json"
GITIGNORE_MARKER = "# DHC build-time caches (offline install source; do not commit)"
CACHE_IGNORES = [".agents/plugins_cache/", ".agents/skills_cache/"]


class ProvisionError(Exception):
    pass


# ── small path/io helpers ────────────────────────────────────────────────────

class Paths:
    def __init__(self, workspace, plugins_cache, skills_cache):
        self.root = os.path.abspath(workspace)
        self.agents = os.path.join(self.root, ".agents")
        self.plugins_cache = plugins_cache or os.path.join(self.agents, "plugins_cache")
        self.skills_cache = skills_cache or os.path.join(self.agents, "skills_cache")
        self.receipt = os.path.join(self.agents, RECEIPT_NAME)
        self.hooks = os.path.join(self.agents, "hooks.json")
        self.mcp = os.path.join(self.agents, "mcp_config.json")
        self.gitignore = os.path.join(self.root, ".gitignore")

    def abs(self, rel):
        """Resolve a workspace-relative POSIX path (e.g. '.agents/skills/x') to absolute."""
        return os.path.join(self.root, *rel.split("/"))


def _log(msg, quiet=False):
    if not quiet:
        print(msg)


def canonical_json(obj):
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def make_executable(path):
    os.chmod(path, os.stat(path).st_mode | 0o111)


def chmod_scripts(root):
    for dirpath, _dirs, files in os.walk(root):
        for f in files:
            if f.endswith(".sh") or f.endswith(".py"):
                make_executable(os.path.join(dirpath, f))


def _copytree_clean(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


# ── selection / receipt ──────────────────────────────────────────────────────

def load_selection(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ProvisionError(f"selection file not found: {path}")
    except json.JSONDecodeError as e:
        raise ProvisionError(f"selection is not valid JSON: {e}")


def validate_selection(sel):
    if not isinstance(sel, dict):
        raise ProvisionError("selection must be a JSON object")
    if sel.get("schemaVersion") != SCHEMA_VERSION:
        raise ProvisionError(f"schemaVersion must be {SCHEMA_VERSION}")
    if sel.get("mode") not in ("default", "flatten"):
        raise ProvisionError('mode must be "default" or "flatten"')
    plugins = sel.get("plugins", [])
    if not isinstance(plugins, list) or not all(isinstance(p, str) for p in plugins):
        raise ProvisionError("plugins must be a list of strings")
    sel.setdefault("sdd", False)


def load_receipt(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        raise ProvisionError(f"existing receipt is corrupt ({path}): {e}")


# ── cache inspection ─────────────────────────────────────────────────────────

def read_plugin_manifest(paths, name):
    pj = os.path.join(paths.plugins_cache, name, "plugin.json")
    try:
        with open(pj, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise ProvisionError(f"plugin '{name}' not found in cache ({pj})")
    except json.JSONDecodeError as e:
        raise ProvisionError(f"plugin '{name}' has invalid plugin.json: {e}")


def plugin_components(paths, name):
    base = os.path.join(paths.plugins_cache, name)
    manifest = read_plugin_manifest(paths, name)
    agents_dir = os.path.join(base, "agents")
    scripts_dir = os.path.join(base, "scripts")
    hooks = os.path.join(base, "hooks.json")
    mcp = os.path.join(base, "mcp_config.json")
    return {
        "skills": list(manifest.get("skills", [])),
        "version": manifest.get("version", "0.0.0"),
        "agents": sorted(f for f in os.listdir(agents_dir)
                         if os.path.isfile(os.path.join(agents_dir, f))) if os.path.isdir(agents_dir) else [],
        "scripts_dir": scripts_dir if os.path.isdir(scripts_dir) else None,
        "hooks": hooks if os.path.isfile(hooks) else None,
        "mcp": mcp if os.path.isfile(mcp) else None,
    }


def preflight_validate(sel, paths):
    """Fail fast BEFORE any mutation: every plugin + every declared skill must exist."""
    problems = []
    for name in sel["plugins"]:
        pj = os.path.join(paths.plugins_cache, name, "plugin.json")
        if not os.path.isfile(pj):
            problems.append(f"missing plugin in cache: {name}")
            continue
        for skill in plugin_components(paths, name)["skills"]:
            if not os.path.isdir(os.path.join(paths.skills_cache, skill)):
                problems.append(f"plugin '{name}' references missing skill: {skill}")
    if problems:
        raise ProvisionError("preflight failed:\n  - " + "\n  - ".join(problems))


# ── planning ─────────────────────────────────────────────────────────────────

def compute_created_paths(name, mode, comps):
    if mode == "default":
        return [f".agents/plugins/{name}"]
    paths = [f".agents/skills/{s}" for s in comps["skills"]]
    paths += [f".agents/agents/{a}" for a in comps["agents"]]
    if comps["scripts_dir"]:
        paths.append(f".agents/scripts/{name}")
    return sorted(paths)


def is_already_provisioned(name, comps, mode, prior_entry, paths):
    if not prior_entry or prior_entry.get("version") != comps["version"]:
        return False
    for rel in prior_entry.get("createdPaths", []):
        if not os.path.exists(paths.abs(rel)):
            return False
    hooks_now = merge_config._load(paths.hooks) or {}
    for g in prior_entry.get("hookGroups", []):
        if g not in hooks_now:
            return False
    mcp_now = (merge_config._load(paths.mcp) or {}).get("mcpServers", {})
    for s in prior_entry.get("mcpServers", []):
        if s not in mcp_now:
            return False
    # recorded set must match the intended set for this version/mode
    return sorted(prior_entry.get("createdPaths", [])) == compute_created_paths(name, mode, comps)


# ── reconcile / undo ─────────────────────────────────────────────────────────

def unprovision_plugin(entry, paths, quiet=False):
    # remove created paths, longest first (children before parents)
    for rel in sorted(entry.get("createdPaths", []), key=len, reverse=True):
        target = paths.abs(rel)
        if os.path.isdir(target) and not os.path.islink(target):
            shutil.rmtree(target, ignore_errors=True)
        elif os.path.lexists(target):
            try:
                os.remove(target)
            except OSError:
                pass
    if entry.get("hookGroups"):
        merge_config.unmerge_hooks(entry["hookGroups"], paths.hooks)
    if entry.get("mcpServers"):
        merge_config.unmerge_mcp(entry["mcpServers"], paths.mcp)


# ── provisioning ─────────────────────────────────────────────────────────────

def materialize_skills(skills, skills_cache, dest_dir):
    created = []
    for s in skills:
        dst = os.path.join(dest_dir, s)
        _copytree_clean(os.path.join(skills_cache, s), dst)
        chmod_scripts(dst)
        created.append(dst)
    return created


def rewrite_hook_paths(node, old, new):
    """Return a copy of the hooks dict with any `command` string's `old` prefix replaced by
    `new`. Used to point hook commands at ABSOLUTE script locations, which resolve regardless
    of the working directory Antigravity runs hooks from (relative paths do not)."""
    def walk(n):
        if isinstance(n, dict):
            return {k: (v.replace(old, new) if k == "command" and isinstance(v, str) else walk(v))
                    for k, v in n.items()}
        if isinstance(n, list):
            return [walk(x) for x in n]
        return n

    return walk(node)


def provision_default(name, comps, paths, quiet=False):
    target = paths.abs(f".agents/plugins/{name}")
    _copytree_clean(os.path.join(paths.plugins_cache, name), target)
    skills_dest = os.path.join(target, "skills")
    if comps["skills"]:
        os.makedirs(skills_dest, exist_ok=True)
        materialize_skills(comps["skills"], paths.skills_cache, skills_dest)
    chmod_scripts(target)
    # Absolutize the copied plugin's hook command paths so they resolve regardless of the
    # hook working directory (relative `.agents/...` paths fail — see the flatten fix).
    tgt_hooks = os.path.join(target, "hooks.json")
    if os.path.isfile(tgt_hooks):
        data = merge_config._load(tgt_hooks)
        if data:
            old = f".agents/plugins/{name}/scripts/"
            new = os.path.join(paths.root, ".agents", "plugins", name, "scripts") + "/"
            merge_config._save(tgt_hooks, rewrite_hook_paths(data, old, new))
    _log(f"  [default] .agents/plugins/{name} ({len(comps['skills'])} skills)", quiet)
    return {"version": comps["version"],
            "createdPaths": [f".agents/plugins/{name}"],
            "hookGroups": [], "mcpServers": []}, []


def provision_flatten(name, comps, paths, quiet=False):
    created, collisions = [], []
    # skills -> .agents/skills/<s>
    os.makedirs(os.path.join(paths.agents, "skills"), exist_ok=True)
    for abspath in materialize_skills(comps["skills"], paths.skills_cache,
                                      os.path.join(paths.agents, "skills")):
        created.append(".agents/skills/" + os.path.basename(abspath))
    # agents/*.md -> .agents/agents/ (no-clobber)
    if comps["agents"]:
        dst_agents = os.path.join(paths.agents, "agents")
        os.makedirs(dst_agents, exist_ok=True)
        for a in comps["agents"]:
            dst = os.path.join(dst_agents, a)
            if os.path.exists(dst):
                print(f"[provision] WARNING: agent '{a}' already exists; skipped (collision).", file=sys.stderr)
                collisions.append({"plugin": name, "kind": "agent", "name": a})
                continue
            shutil.copy2(os.path.join(paths.plugins_cache, name, "agents", a), dst)
            created.append(f".agents/agents/{a}")
    # scripts -> .agents/scripts/<name>/  (namespaced; fixes the flatten hook-path bug)
    if comps["scripts_dir"]:
        dst_scripts = paths.abs(f".agents/scripts/{name}")
        _copytree_clean(comps["scripts_dir"], dst_scripts)
        chmod_scripts(dst_scripts)
        created.append(f".agents/scripts/{name}")
    # hooks -> rewrite paths, merge into .agents/hooks.json
    hook_groups = []
    if comps["hooks"]:
        src = merge_config._load(comps["hooks"]) or {}
        old = f".agents/plugins/{name}/scripts/"
        new = os.path.join(paths.root, ".agents", "scripts", name) + "/"
        rewritten = rewrite_hook_paths(src, old, new)
        added = merge_config.merge_hooks_data(rewritten, paths.hooks)
        hook_groups = sorted(added)
        for g in src.keys():
            if g not in added:
                collisions.append({"plugin": name, "kind": "hook", "name": g})
    # mcp -> merge into .agents/mcp_config.json
    mcp_servers = []
    if comps["mcp"]:
        src = merge_config._load(comps["mcp"]) or {}
        added = merge_config.merge_mcp_data(src, paths.mcp)
        mcp_servers = sorted(added)
        for s in src.get("mcpServers", {}):
            if s not in added:
                collisions.append({"plugin": name, "kind": "mcp", "name": s})
    _log(f"  [flatten] {name}: {len(comps['skills'])} skills, {len(comps['agents'])} agents, "
         f"{len(hook_groups)} hooks, {len(mcp_servers)} mcp", quiet)
    return {"version": comps["version"],
            "createdPaths": sorted(created),
            "hookGroups": hook_groups, "mcpServers": mcp_servers}, collisions


# ── gitignore / receipt ──────────────────────────────────────────────────────

def ensure_gitignore_cache_block(paths):
    existing = ""
    if os.path.exists(paths.gitignore):
        with open(paths.gitignore, "r", encoding="utf-8") as f:
            existing = f.read()
    if ".agents/plugins_cache/" in existing:
        return
    with open(paths.gitignore, "a", encoding="utf-8") as f:
        f.write(("\n" if existing and not existing.endswith("\n") else "")
                + GITIGNORE_MARKER + "\n" + "\n".join(CACHE_IGNORES) + "\n")


def build_receipt(sel, entries, collisions):
    core = {
        "schemaVersion": SCHEMA_VERSION,
        "mode": sel["mode"],
        "sdd": sel.get("sdd", False),
        "selection": {k: sel[k] for k in ("schemaVersion", "mode", "plugins", "sdd")},
        "plugins": entries,
        "collisions": collisions,
    }
    digest = hashlib.sha256(canonical_json(core).encode("utf-8")).hexdigest()
    core["receiptHash"] = "sha256:" + digest
    return core


def write_receipt(path, receipt):
    data = canonical_json(receipt)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            if f.read() == data:
                return False
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(data)
    os.replace(tmp, path)
    return True


# ── orchestration ────────────────────────────────────────────────────────────

def provision(selection_path, workspace, plugins_cache, skills_cache, dry_run=False, quiet=False):
    sel = load_selection(selection_path)
    validate_selection(sel)
    paths = Paths(workspace, plugins_cache, skills_cache)
    if not os.path.isdir(paths.plugins_cache):
        raise ProvisionError(f"plugins cache not found: {paths.plugins_cache}")
    preflight_validate(sel, paths)

    prior = load_receipt(paths.receipt)
    selected = sorted(sel["plugins"])
    mode_switch = bool(prior) and prior.get("mode") != sel["mode"]

    # plan: who is removed, who needs (re)provisioning
    survivors = {}
    to_remove = []
    if prior:
        for pname, entry in prior.get("plugins", {}).items():
            if mode_switch or pname not in selected:
                to_remove.append((pname, entry))
            else:
                survivors[pname] = entry

    comps_by_name = {n: plugin_components(paths, n) for n in selected}
    to_provision = [n for n in selected
                    if not (n in survivors
                            and is_already_provisioned(n, comps_by_name[n], sel["mode"], survivors[n], paths))]

    if dry_run:
        _log(f"[dry-run] mode={sel['mode']} (mode_switch={mode_switch})", quiet)
        _log(f"[dry-run] remove:      {[n for n, _ in to_remove]}", quiet)
        _log(f"[dry-run] provision:   {to_provision}", quiet)
        _log(f"[dry-run] unchanged:   {[n for n in selected if n not in to_provision]}", quiet)
        return 0

    # 1) reconcile (remove deselected / mode-switched)
    for pname, entry in to_remove:
        unprovision_plugin(entry, paths, quiet)
        _log(f"  [remove] {pname}", quiet)

    # 2) provision selected
    entries, collisions = {}, []
    for name in selected:
        comps = comps_by_name[name]
        if name in survivors and name not in to_provision:
            entries[name] = survivors[name]
            continue
        if name in survivors:  # refresh-on-change: undo stale before re-provisioning
            unprovision_plugin(survivors[name], paths, quiet)
        fn = provision_flatten if sel["mode"] == "flatten" else provision_default
        entry, coll = fn(name, comps, paths, quiet)
        entries[name] = entry
        collisions.extend(coll)

    # 3) gitignore caches + 4) receipt
    # NOTE: SDD is NOT enforced via .agents/settings.json — Antigravity does not honor
    # workspace agentMode at runtime. SDD = the sdd.md rule + launching `agy --mode=plan`
    # (surfaced in the Phase-5 handoff). The receipt just records that sdd was requested.
    ensure_gitignore_cache_block(paths)
    receipt = build_receipt(sel, entries, sorted(collisions, key=lambda c: (c["plugin"], c["kind"], c["name"])))
    changed = write_receipt(paths.receipt, receipt)
    _log(f"[dhc-provision] {'wrote' if changed else 'no change to'} {RECEIPT_NAME} "
         f"(mode={sel['mode']}, plugins={len(entries)}, collisions={len(collisions)})", quiet)
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog="dhc_provision.py", add_help=True)
    ap.add_argument("selection")
    ap.add_argument("--workspace", default=os.getcwd())
    ap.add_argument("--plugins-cache", default=None)
    ap.add_argument("--skills-cache", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    try:
        args = ap.parse_args(argv[1:])
    except SystemExit:
        return 2
    try:
        return provision(args.selection, args.workspace, args.plugins_cache,
                         args.skills_cache, args.dry_run, args.quiet)
    except ProvisionError as e:
        print(f"[dhc-provision] ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

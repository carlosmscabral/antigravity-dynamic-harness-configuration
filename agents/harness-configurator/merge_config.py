#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic config merge/un-merge helpers for the DHC configurator (flatten mode).

Unions a plugin's bundled hooks.json / mcp_config.json into the workspace-level
.agents/hooks.json / .agents/mcp_config.json so plugin-provided hooks/MCP servers load in
BOTH interactive and headless (`agy -p`) modes (the plugin tree itself is skipped by `agy -p`).

Idempotent and never clobbers existing keys — on a collision it keeps the existing entry and
warns. Merge functions RETURN the list of names actually added, so callers (dhc_provision.py)
can record them in the provisioning receipt for precise un-merge on reconcile.

Importable module (underscore name). Also runnable as a CLI:
    merge_config.py hooks <source_plugin_hooks.json> <target .agents/hooks.json>
    merge_config.py mcp   <source_plugin_mcp.json>   <target .agents/mcp_config.json>
"""

import json
import sys

_SENT = object()


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as e:
        print(f"[merge] ERROR: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def _save(path, data):
    # NOTE: no sort_keys — preserve the developer's existing key order (minimal diffs).
    # Determinism of the merged file comes from callers processing plugins/names in
    # sorted order, so appended keys land deterministically.
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


# ── merge (union, no-clobber) — dict cores return names added ────────────────

def merge_hooks_data(src, tgt_path):
    """hooks.json is a flat map {hook_group_name: spec}. Union by group name."""
    src = src or {}
    tgt = _load(tgt_path) or {}
    added = []
    for name, spec in src.items():
        if name in tgt:
            print(f"[merge] WARNING: hook group '{name}' already present in {tgt_path}; "
                  f"kept existing (assign unique names to avoid collisions).", file=sys.stderr)
            continue
        tgt[name] = spec
        added.append(name)
    _save(tgt_path, tgt)
    return added


def merge_mcp_data(src, tgt_path):
    """mcp_config.json = {"mcpServers": {name: cfg}}. Union under mcpServers."""
    src = src or {}
    src_servers = src.get("mcpServers", {})
    tgt = _load(tgt_path) or {}
    tgt.setdefault("mcpServers", {})
    added = []
    for name, cfg in src_servers.items():
        if name in tgt["mcpServers"]:
            print(f"[merge] WARNING: mcp server '{name}' already present in {tgt_path}; "
                  f"kept existing.", file=sys.stderr)
            continue
        tgt["mcpServers"][name] = cfg
        added.append(name)
    _save(tgt_path, tgt)
    return added


def merge_hooks(src_path, tgt_path):
    return merge_hooks_data(_load(src_path) or {}, tgt_path)


def merge_mcp(src_path, tgt_path):
    return merge_mcp_data(_load(src_path) or {}, tgt_path)


# ── un-merge (removal) — for reconcile of deselected plugins ─────────────────

def unmerge_hooks(names, tgt_path):
    """Remove the named hook groups. Only touches names the caller recorded, so
    developer- and other-plugin-owned groups are never removed. Leaves {} rather than
    deleting the file."""
    tgt = _load(tgt_path)
    if tgt is None:
        return []
    removed = [n for n in names if tgt.pop(n, _SENT) is not _SENT]
    _save(tgt_path, tgt)
    return removed


def unmerge_mcp(names, tgt_path):
    tgt = _load(tgt_path)
    if tgt is None:
        return []
    servers = tgt.get("mcpServers", {})
    removed = [n for n in names if servers.pop(n, _SENT) is not _SENT]
    _save(tgt_path, tgt)
    return removed


def main(argv):
    if len(argv) != 4 or argv[1] not in ("hooks", "mcp"):
        print(__doc__)
        return 2
    kind, src, tgt = argv[1], argv[2], argv[3]
    if _load(src) is None:
        print(f"[merge] nothing to merge (no {src})")
        return 0
    added = merge_hooks(src, tgt) if kind == "hooks" else merge_mcp(src, tgt)
    print(f"[merge] {kind}: +{len(added)} {added}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

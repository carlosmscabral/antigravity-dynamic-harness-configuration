#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deterministic config merge helper for the DHC configurator (flatten mode).

Used only when DHC_FLATTEN is enabled: it unions a plugin's bundled hooks.json or
mcp_config.json into the workspace-level .agents/hooks.json / .agents/mcp_config.json,
so plugin-provided hooks/MCP servers load in BOTH interactive and headless (`agy -p`)
modes (the plugin tree itself is skipped by `agy -p`).

It is idempotent and never clobbers existing keys — on a key collision it keeps the
existing entry and warns (so the caller can assign unique names). This replaces
LLM-improvised merging with a deterministic operation.

Usage:
    merge-config.py hooks <source_plugin_hooks.json> <target .agents/hooks.json>
    merge-config.py mcp   <source_plugin_mcp.json>   <target .agents/mcp_config.json>
"""

import json
import sys


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
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def merge_hooks(src_path, tgt_path):
    """hooks.json is a flat map of {hook_group_name: spec}. Union by group name."""
    src = _load(src_path) or {}
    tgt = _load(tgt_path) or {}
    added, skipped = [], []
    for name, spec in src.items():
        if name in tgt:
            skipped.append(name)
            print(f"[merge] WARNING: hook group '{name}' already present in {tgt_path}; "
                  f"kept existing (assign unique names to avoid collisions).", file=sys.stderr)
            continue
        tgt[name] = spec
        added.append(name)
    _save(tgt_path, tgt)
    print(f"[merge] hooks: +{len(added)} {added} (skipped {skipped})")


def merge_mcp(src_path, tgt_path):
    """mcp_config.json = {\"mcpServers\": {name: cfg}}. Union under mcpServers."""
    src = _load(src_path) or {}
    tgt = _load(tgt_path) or {}
    src_servers = src.get("mcpServers", {})
    tgt.setdefault("mcpServers", {})
    added, skipped = [], []
    for name, cfg in src_servers.items():
        if name in tgt["mcpServers"]:
            skipped.append(name)
            print(f"[merge] WARNING: mcp server '{name}' already present in {tgt_path}; "
                  f"kept existing.", file=sys.stderr)
            continue
        tgt["mcpServers"][name] = cfg
        added.append(name)
    _save(tgt_path, tgt)
    print(f"[merge] mcp: +{len(added)} {added} (skipped {skipped})")


def main(argv):
    if len(argv) != 4 or argv[1] not in ("hooks", "mcp"):
        print(__doc__)
        return 2
    kind, src, tgt = argv[1], argv[2], argv[3]
    if _load(src) is None:
        print(f"[merge] nothing to merge (no {src})")
        return 0
    (merge_hooks if kind == "hooks" else merge_mcp)(src, tgt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

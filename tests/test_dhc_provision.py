#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the DHC deterministic provisioning core (roadmap 1.1).

Self-contained: builds synthetic plugin/skill fixtures in a temp workspace (no dependency on
the cabral-skills checkout or `agy`). Runs `dhc_provision` in-process and asserts on the
resulting files + receipt. Run:  python3 -m unittest tests/test_dhc_provision.py
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

_CFG = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "..", "agents", "harness-configurator")
sys.path.insert(0, os.path.abspath(_CFG))
import dhc_provision as dp           # noqa: E402
import merge_config                  # noqa: E402


def _w(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_fixtures(agents):
    """Create synthetic plugins_cache + skills_cache under <agents>."""
    pc = os.path.join(agents, "plugins_cache")
    sc = os.path.join(agents, "skills_cache")
    # skills
    _w(os.path.join(sc, "skill-a", "SKILL.md"), "---\nname: skill-a\ndescription: a\n---\n")
    _w(os.path.join(sc, "skill-a", "scripts", "run.sh"), "#!/bin/bash\necho a\n")
    _w(os.path.join(sc, "skill-b", "SKILL.md"), "---\nname: skill-b\ndescription: b\n---\n")
    # plugin alpha: skill-a + hook (-> scripts/a.sh) + agent
    _w(os.path.join(pc, "alpha", "plugin.json"),
       json.dumps({"name": "alpha", "version": "1.0.0", "skills": ["skill-a"]}))
    _w(os.path.join(pc, "alpha", "scripts", "a.sh"), "#!/bin/bash\necho alpha\n")
    _w(os.path.join(pc, "alpha", "agents", "agent-a.md"), "# agent a\n")
    _w(os.path.join(pc, "alpha", "hooks.json"), json.dumps({
        "alpha-hook": {"enabled": True, "preToolUse": [
            {"matcher": "run_command", "hooks": [
                {"command": ".agents/plugins/alpha/scripts/a.sh", "timeout": 5}]}]}}))
    # plugin beta: skill-b + hook (-> scripts/b.sh)
    _w(os.path.join(pc, "beta", "plugin.json"),
       json.dumps({"name": "beta", "version": "1.0.0", "skills": ["skill-b"]}))
    _w(os.path.join(pc, "beta", "scripts", "b.sh"), "#!/bin/bash\necho beta\n")
    _w(os.path.join(pc, "beta", "hooks.json"), json.dumps({
        "beta-hook": {"enabled": True, "preToolUse": [
            {"matcher": "run_command", "hooks": [
                {"command": ".agents/plugins/beta/scripts/b.sh", "timeout": 5}]}]}}))
    # plugin gamma: shares skill-a + mcp
    _w(os.path.join(pc, "gamma", "plugin.json"),
       json.dumps({"name": "gamma", "version": "1.0.0", "skills": ["skill-a"]}))
    _w(os.path.join(pc, "gamma", "mcp_config.json"),
       json.dumps({"mcpServers": {"gamma-mcp": {"command": "echo", "args": ["hi"]}}}))
    # plugin delta: references a missing skill
    _w(os.path.join(pc, "delta", "plugin.json"),
       json.dumps({"name": "delta", "version": "1.0.0", "skills": ["skill-missing"]}))
    return pc, sc


class DhcProvisionTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="dhc-test-")
        self.agents = os.path.join(self.root, ".agents")
        os.makedirs(self.agents)
        build_fixtures(self.agents)
        self.receipt = os.path.join(self.agents, dp.RECEIPT_NAME)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    # helpers
    def _prov(self, mode, plugins, dry=False, sdd=False):
        sel = os.path.join(self.agents, "selection.json")
        _w(sel, json.dumps({"schemaVersion": 1, "mode": mode, "plugins": plugins, "sdd": sdd}))
        return dp.provision(sel, self.root, None, None, dry_run=dry, quiet=True)

    def path(self, rel):
        return os.path.join(self.root, *rel.split("/"))

    def load_receipt(self):
        with open(self.receipt) as f:
            return json.load(f)

    def _json(self, rel):
        with open(self.path(rel)) as f:
            return json.load(f)

    def _rbytes(self, path):
        with open(path, "rb") as f:
            return f.read()

    # ── T1 invalid selection ──
    def test_T1_invalid_selection(self):
        sel = os.path.join(self.agents, "bad.json")
        _w(sel, json.dumps({"schemaVersion": 99, "mode": "nope", "plugins": "x"}))
        rc = dp.main(["dhc_provision.py", sel, "--workspace", self.root, "--quiet"])
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(self.receipt))
        self.assertFalse(os.path.exists(self.path(".agents/plugins")))

    # ── T2 default provision ──
    def test_T2_default(self):
        self._prov("default", ["alpha", "gamma"])
        self.assertTrue(os.path.isfile(self.path(".agents/plugins/alpha/skills/skill-a/SKILL.md")))
        self.assertTrue(os.access(self.path(".agents/plugins/alpha/scripts/a.sh"), os.X_OK))
        self.assertTrue(os.path.isfile(self.path(".agents/plugins/gamma/mcp_config.json")))
        self.assertFalse(os.path.exists(self.path(".agents/hooks.json")))  # no merge in default
        r = self.load_receipt()
        self.assertEqual(r["mode"], "default")
        self.assertEqual(r["plugins"]["alpha"]["hookGroups"], [])
        self.assertEqual(r["plugins"]["alpha"]["createdPaths"], [".agents/plugins/alpha"])

    # ── T3 flatten + hook-path bug fix ──
    def test_T3_flatten(self):
        self._prov("flatten", ["alpha", "gamma"])
        self.assertTrue(os.path.isfile(self.path(".agents/skills/skill-a/SKILL.md")))
        self.assertTrue(os.path.isfile(self.path(".agents/agents/agent-a.md")))
        script = self.path(".agents/scripts/alpha/a.sh")
        self.assertTrue(os.access(script, os.X_OK))
        hooks = self._json(".agents/hooks.json")
        cmd = hooks["alpha-hook"]["preToolUse"][0]["hooks"][0]["command"]
        self.assertEqual(cmd, ".agents/scripts/alpha/a.sh")
        self.assertTrue(os.path.exists(self.path(cmd)))  # rewritten path resolves
        mcp = self._json(".agents/mcp_config.json")
        self.assertIn("gamma-mcp", mcp["mcpServers"])
        r = self.load_receipt()
        self.assertEqual(r["plugins"]["alpha"]["hookGroups"], ["alpha-hook"])
        self.assertEqual(r["plugins"]["gamma"]["mcpServers"], ["gamma-mcp"])
        # skill scripts are executable too
        self.assertTrue(os.access(self.path(".agents/skills/skill-a/scripts/run.sh"), os.X_OK))

    # ── T4 idempotency: byte-identical receipt, no-op re-run ──
    def test_T4_idempotent(self):
        self._prov("flatten", ["alpha", "gamma"])
        first = self._rbytes(self.receipt)
        # dry-run should report nothing to provision
        # (capture by asserting write_receipt returns False on real re-run)
        sel = os.path.join(self.agents, "selection.json")
        changed = dp.write_receipt(self.receipt, self.load_receipt())
        self.assertFalse(changed)
        self._prov("flatten", ["alpha", "gamma"])
        second = self._rbytes(self.receipt)
        self.assertEqual(first, second)

    # ── T5 reconcile (default) ──
    def test_T5_reconcile_default(self):
        self._prov("default", ["alpha", "beta"])
        self._prov("default", ["alpha"])
        self.assertFalse(os.path.exists(self.path(".agents/plugins/beta")))
        self.assertTrue(os.path.exists(self.path(".agents/plugins/alpha")))
        self.assertNotIn("beta", self.load_receipt()["plugins"])

    # ── T6 reconcile (flatten) with un-merge ──
    def test_T6_reconcile_flatten(self):
        self._prov("flatten", ["alpha", "beta"])
        self._prov("flatten", ["alpha"])
        self.assertFalse(os.path.exists(self.path(".agents/skills/skill-b")))
        self.assertFalse(os.path.exists(self.path(".agents/scripts/beta")))
        hooks = self._json(".agents/hooks.json")
        self.assertNotIn("beta-hook", hooks)
        self.assertIn("alpha-hook", hooks)                       # alpha retained
        self.assertTrue(os.path.exists(self.path(".agents/skills/skill-a")))

    # ── T7 collision: developer-owned hook not clobbered / not removed ──
    def test_T7_collision(self):
        _w(self.path(".agents/hooks.json"), json.dumps({"alpha-hook": {"enabled": True, "mine": 1}}))
        self._prov("flatten", ["alpha"])
        r = self.load_receipt()
        self.assertEqual(r["plugins"]["alpha"]["hookGroups"], [])   # not recorded (collided)
        self.assertTrue(any(c["name"] == "alpha-hook" for c in r["collisions"]))
        self._prov("flatten", [])                                     # reconcile away alpha
        hooks = self._json(".agents/hooks.json")
        self.assertIn("alpha-hook", hooks)                          # developer's group survives
        self.assertEqual(hooks["alpha-hook"].get("mine"), 1)

    # ── T8 mode switch ──
    def test_T8_mode_switch(self):
        self._prov("default", ["alpha"])
        self.assertTrue(os.path.exists(self.path(".agents/plugins/alpha")))
        self._prov("flatten", ["alpha"])
        self.assertFalse(os.path.exists(self.path(".agents/plugins/alpha")))
        self.assertTrue(os.path.exists(self.path(".agents/skills/skill-a")))
        self.assertEqual(self.load_receipt()["mode"], "flatten")

    # ── T9 missing skill in cache ──
    def test_T9_missing_skill(self):
        rc = self._run_rc("flatten", ["delta"])
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(self.receipt))
        self.assertFalse(os.path.exists(self.path(".agents/skills")))

    # ── T10 missing plugin in cache ──
    def test_T10_missing_plugin(self):
        rc = self._run_rc("flatten", ["nonexistent"])
        self.assertEqual(rc, 1)
        self.assertFalse(os.path.exists(self.receipt))

    # ── T11 empty selection after prior ──
    def test_T11_empty_selection(self):
        self._prov("flatten", ["alpha"])
        self._prov("flatten", [])
        self.assertFalse(os.path.exists(self.path(".agents/skills/skill-a")))
        self.assertFalse(os.path.exists(self.path(".agents/scripts/alpha")))
        self.assertEqual(self.load_receipt()["plugins"], {})

    # ── T12 gitignore appended exactly once ──
    def test_T12_gitignore_once(self):
        self._prov("default", ["alpha"])
        self._prov("default", ["alpha", "beta"])
        with open(os.path.join(self.root, ".gitignore")) as _f:
            gi = _f.read()
        self.assertEqual(gi.count(".agents/plugins_cache/"), 1)
        self.assertEqual(gi.count(".agents/skills_cache/"), 1)

    # ── T13 SDD enforcement via settings.json agentMode=plan ──
    def test_T13_sdd_plan_mode(self):
        self._prov("default", ["alpha"], sdd=True)
        self.assertEqual(self._json(".agents/settings.json")["agentMode"], "plan")
        self.assertTrue(self.load_receipt()["sdd"])
        # preserve other keys, and revert agentMode when sdd flips off
        _w(self.path(".agents/settings.json"), json.dumps({"agentMode": "plan", "theme": "dark"}))
        self._prov("default", ["alpha"], sdd=False)
        sj = self._json(".agents/settings.json")
        self.assertNotIn("agentMode", sj)
        self.assertEqual(sj.get("theme"), "dark")

    def _run_rc(self, mode, plugins):
        sel = os.path.join(self.agents, "selection.json")
        _w(sel, json.dumps({"schemaVersion": 1, "mode": mode, "plugins": plugins, "sdd": False}))
        return dp.main(["dhc_provision.py", sel, "--workspace", self.root, "--quiet"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

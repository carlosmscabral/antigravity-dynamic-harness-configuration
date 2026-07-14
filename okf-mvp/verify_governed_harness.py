#!/usr/bin/env python3
"""
verify_governed_harness.py
Automated security audit and verification script for OKF DHC.
Checks generated workspace harness settings to guarantee corporate compliance.
"""

import os
import sys
import json

def run_compliance_audit(target_workspace):
    print("==========================================================")
    print("🛡️ Booting OKF DHC Compliance Audit Engine")
    print(f"🎯 Target Workspace Audit: {target_workspace}")
    print("==========================================================")

    agents_dir = os.path.join(target_workspace, ".agents")
    hooks_path = os.path.join(agents_dir, "hooks.json")
    agents_rules_path = os.path.join(agents_dir, "AGENTS.md")

    errors = 0

    # 1. Verify existence of harness configurations
    if not os.path.exists(hooks_path):
        print("❌ CRITICAL: .agents/hooks.json is missing!")
        errors += 1
    if not os.path.exists(agents_rules_path):
        print("❌ CRITICAL: .agents/AGENTS.md is missing!")
        errors += 1

    if errors > 0:
        print("\n💥 Compliance check FAILED due to missing infrastructure files.")
        sys.exit(1)

    # 2. Check corporate-locked pre-run hooks in hooks.json
    print("🔍 Auditing tool interceptor hooks...")
    with open(hooks_path, "r") as f:
        hooks_data = json.load(f)
    
    pre_run_cmds = hooks_data.get("pre-run", [])
    expected_security_hook = "sh -c 'echo \"[GLOBAL-SECURITY-HOOK] Scanning command... OK\"'"
    
    if expected_security_hook not in pre_run_cmds:
        print(f"❌ COMPLIANCE VIOLATION: Mandatory Corporate Security Hook is missing!")
        print(f"   Expected: {expected_security_hook}")
        errors += 1
    else:
        print("   ✅ Verified: Corporate-enforced command scanner is active.")

    # 3. Check corporate-enforced global security rules in AGENTS.md
    print("🔍 Auditing workspace rules configuration...")
    with open(agents_rules_path, "r") as f:
        rules_text = f.read()

    expected_rule = "Never attempt to download raw executable binaries via curl/wget."
    
    if expected_rule not in rules_text:
        print(f"❌ COMPLIANCE VIOLATION: Mandatory Corporate Security Rule is missing from AGENTS.md!")
        print(f"   Expected: {expected_rule}")
        errors += 1
    else:
        print("   ✅ Verified: Corporate-enforced terminal audit rule is present.")

    # 4. Final Verdict
    print("==========================================================")
    if errors == 0:
        print("🎉 SUCCESS: All corporate compliance locks verified!")
        print("   Harness is compliant with Global Enterprise Policies.")
        print("==========================================================")
        sys.exit(0)
    else:
        print(f"💥 AUDIT FAIL: Detected {errors} security/compliance violations.")
        print("==========================================================")
        sys.exit(1)

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = os.path.join(BASE_DIR, "test_sandbox")

    run_compliance_audit(target)

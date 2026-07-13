---
type: AI Methodology Concept
title: Dynamic Harness Configurator (DHC) — Meta-Harness Engineering
description: Design architecture for a bootstrap-level meta-agent that reads best-practice database constraints, dynamically provisions the agentic execution harness (sandboxes, MCP, skills, rules), and hands off a pre-configured environment to coding agents.
tags: [architecture, harness-engineering, security, automation, meta-agents]
timestamp: 2026-07-13T15:03:00-03:00
---

# Dynamic Harness Configurator (DHC) — Meta-Harness Engineering

In traditional software development, the developer configures the environment. In the age of **Vibe Coding**, letting an autonomous agent execute unsandboxed or unconfigured tools is a high-risk security hazard and leads to rapid accumulation of **Context Debt** and **Capability Gaps**.

The **Dynamic Harness Configurator (DHC)** is an architectural paradigm where a specialized, high-security **Meta-Agent** reads the project requirements and your core organization policies (OKF Database), dynamically structures and hardens the agentic execution environment (the Harness), and hands off this pre-configured container to a lower-security "Coding Agent" or to the human developer.

---

## 1. The Meta-Harness Separation of Concerns

By dividing the lifecycle into **Harness Provisioning** and **Code Execution**, we resolve the fundamental paradox: *An agent cannot securely configure its own sandbox from the inside.*

```
                 ┌──────────────────────────────────────┐
                 │       OKF KNOWLEDGE DATABASE         │
                 │   - Playbooks, Rules, and Policies   │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │   DYNAMIC HARNESS CONFIGURATOR       │ (Meta-Agent)
                 │  - Reads project requirements        │
                 │  - Generates secure settings.json    │
                 │  - Seeds skills, rules, and schemas  │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼  [BOOTSTRAPS HARNESS]
                 ┌──────────────────────────────────────┐
                 │       THE HARDENED HARNESS           │ (Isolated Container)
                 │  - enableTerminalSandbox: true       │
                 │  - allowNonWorkspaceAccess: false     │
                 │  - Custom MCPs & skills pre-wired    │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼  [LAUNCHES HANDOFF]
                 ┌──────────────────────────────────────┐
                 │           CODING AGENT               │ (Developer/TUI Session)
                 │  - Operates safely within boundaries │
                 └──────────────────────────────────────┘
```

---

## 2. The 4-Step DHC Lifecycle Pipeline

### Step 1: Requirements Discovery & Scan
The DHC agent scans the user's high-level goal (e.g., *"Build a local FastAPI pizza app with Firebase Firestore storage"*). It determines:
*   **FS Bounds**: Active workspace directories.
*   **External Reach**: Needs Firestore MCP access, pytest shell tools, and port `8000` network ingress.
*   **Security Posture**: Level 3 (requires strict docker/gVisor sandboxing and tool-call approval gates).

### Step 2: Synthesis & Provisioning
The DHC programmatically writes the configuration files to build the workspace boundaries *prior* to launching any code generators:
1.  **Workspace Settings (`settings.json`)**:
    *   Locks `"allowNonWorkspaceAccess": false` and downscopes `"allowed_paths"`.
    *   Forces `"enableTerminalSandbox": true` and `"toolPermission": "request-review"`.
    *   Binds the pre-configured Firestore MCP server transport channels.
2.  **Repository Rules (`.agents/AGENTS.md`)**:
    *   Writes strict styling and architectural guidelines to prevent vibe coding hallucinations.
3.  **Skills Repository (`.agents/skills/`)**:
    *   Seeds pre-built verification and compilation skills to enforce Spec-Driven and Evaluation-Driven development.

### Step 3: Sandboxed Bootstrapping (JIT Isolation)
The DHC exports environment flags to the active terminal:
```bash
export GEMINI_SANDBOX=docker
export GEMINI_TRUSTED_WORKSPACE=$(pwd)
```
This forces the subsequent execution engine to spin up sandboxed runtimes, preventing any shell tools from touching the developer's underlying OS.

### Step 4: Secure Handoff
Once the boundary is active, the DHC spawns the actual **Coding Agent** as a child sub-agent thread inside this pre-wired environment, OR signals the human developer via a clean interface:
> *"Your hardened workspace is ready at `/temp_pizza_project/` with gVisor sandboxing and Firestore MCP pre-configured. Type `agy` to begin coding safely."*

---

## 3. Practical Implementation: The DHC Bootstrap Script

The DHC can be programmatically executed using a simple, ungameable Python bootstrapping script. This script acts as the automated "harness factory":

```python
# bootstrap_harness.py
import os
import json
import yaml
from pathlib import Path

class DynamicHarnessConfigurator:
    def __init__(self, project_path: str, requirements: dict):
        self.project_path = Path(project_path)
        self.requirements = requirements
        self.project_path.mkdir(parents=True, exist_ok=True)

    def provision_settings(self):
        # 1. Synthesize secure settings.json based on requirements
        settings = {
            "allowNonWorkspaceAccess": False,
            "enableTerminalSandbox": True,
            "toolPermission": "request-review",
            "artifactReviewPolicy": "asks-for-review",
            "trustedWorkspaces": [str(self.project_path.resolve())],
            "permissions": {
                "allowed_commands": ["pytest", "pip install", "uvicorn"],
                "denied_commands": ["rm -rf /", "curl", "wget"]
            }
        }
        
        # Inject MCP configurations if database required
        if self.requirements.get("database") == "firestore":
            settings["mcp_servers"] = {
                "firestore-mcp": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-firestore"],
                    "env": {
                        "FIREBASE_PROJECT_ID": self.requirements.get("firebase_project_id", "demo-pizza")
                    }
                }
            }

        config_dir = self.project_path / ".gemini" / "antigravity-cli"
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "settings.json", "w") as f:
            json.dump(settings, f, indent=2)
        print("[DHC] Provisioned secure settings.json with sandboxing and Firestore MCP.")

    def provision_rules(self):
        # 2. Write project rules to .agents/AGENTS.md
        agents_dir = self.project_path / ".agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        
        rules_content = """# Project Rules for Configured Workspace

## 1. Safety & Sandboxing
* All shell commands run inside our gVisor docker container.
* Never disable sandboxing or write credentials to the git tree.

## 2. Spec-First & EDD (Evaluation-Driven Design)
* A Gherkin spec inside `/specs/` must precede any logic.
* You must define at least 3 evaluation cases inside `/evals/` before coding.
"""
        with open(agents_dir / "AGENTS.md", "w") as f:
            f.write(rules_content)
        print("[DHC] Created project rules at .agents/AGENTS.md.")

    def execute_bootstrap(self):
        self.provision_settings()
        self.provision_rules()
        print(f"\n[DHC SUCCESS] Hardened Harness is successfully established at: {self.project_path}")
        print("[DHC HANDOFF] Ready to launch the coding agent inside the secure sandbox.")

if __name__ == "__main__":
    # Example requirement ingestion
    reqs = {
        "database": "firestore",
        "firebase_project_id": "pizza-ordering-35a2"
    }
    dhc = DynamicHarnessConfigurator(
        project_path="/Users/carloscabral/.gemini/antigravity/scratch/temp_pizza_project",
        requirements=reqs
    )
    dhc.execute_bootstrap()
```

---

## 4. Why This Architecture is Game-Changing

1.  **Eliminates the "Trust Gap"**: By forcing the environment layout, sandboxing rules, and allowed tools before the coding model starts, you completely remove the threat of malicious code executions or data exfiltration during the "vibe coding" phase.
2.  **Bypasses Context Bloat**: Instead of asking the coding agent to hold sandboxing rules, Firestore API definitions, and Gherkin formatting guides in its prompt memory, the DHC seeds these into the directory structure. The coding model discovers them naturally through the file system and local skills, saving thousands of tokens and improving focal attention.
3.  **Perfect Reproducibility**: Any project initialized by the DHC contains a deterministic, self-documenting agent setup. Any other agent (or CI builder) that loads the directory will run it in the exact same sandboxed, compliant configuration.

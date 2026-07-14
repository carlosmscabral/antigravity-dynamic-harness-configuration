# Antigravity Customizations & Dynamic Harness Configurator (DHC)

An operational repository that implements the **New SDLC** best practices using the **Google Antigravity (AGY)** agentic customization engine. 

This repository houses your central Antigravity playbooks, flexible, hot-swappable plugins, and an interactive **Harness Configurator Agent** with a dynamic, shell-only installer to instantly provision safe, sandboxed workspaces.

---

## ⚡ Key Components

```
                [A: REMOTE install.sh]            [B: LOCAL bootstrap.py]
                          │                                  │
                          └─────────────────┬────────────────┘
                                            │
                                            ▼ (Downloads / Links JIT custom rules)
                             [agy ──> /agents ──> harness-configurator]
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼ (Silently scans workspace)                     ▼ (Interviews the developer)
             [Auto-Suggest Stack & Sources]                  [Selects standard/strict profile]
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼ (Generates root AGENTS.md, hooks, & ignores)
                              [READY FOR CODES IN SANDBOX!]
```

1.  **The Shell Installer (`install.sh`)**: A lightweight, zero-dependency, and dynamic shell script (`curl | bash`). It downloads the customizations archive, JIT-unpacks the entire suite locally, and configures permissions without cloning the repository or hardcoding file names.
2.  **The Bootstrap Installer (`bootstrap.py`)**: A local, programmatic python utility that symlinks or copies templates and deploys assets to `.agents/` in one click.
3.  **The Harness Configurator Agent (`agents/harness-configurator/agent.md`)**: A simplified, decoupled, and generic setup orchestrator. It silent-scans your workspace for manifests and SDK indicators, conducts a structured interview with the developer, and programmatically copies selected plugins JIT, writes `.agents/mcp_config.json`, `.agents/hooks.json`, and `.antigravityignore`.
4.  **Dormant Plugins Cache (`.agents/plugins_cache/`)**: An inactive holding directory. Storing your customization library plugins here prevents them from auto-activating on startup. Only selected plugins are promoted JIT into `.agents/plugins/` by the configurator!
5.  **Modular Customization Plugins**:
    -   `standard-harness` *(General SDLC)*: Enforces standard styling, modular testing conventions, formatting linter execution, and the `refactoring-expert` subagent.
    -   `strict-banking-harness` *(Enterprise Security)*: Establishes a strict air-gapped security perimeter, restrictions, and **command-interceptor hooks blocking `curl`/`wget`** via `crypto-auditor` subagents.
    -   `adk-developer` *(Specialty ADK)*: Tailored for Google Agent Development Kit (ADK) projects. It **loads `agents-cli` as cognitive AI Skills (under `.agents/skills/`)**, enforces pre-flight Pydantic schema validation, documentation grounding, and design pattern replication from Google samples.
6.  **Operational Integration Playbook (`playbooks/antigravity_integration_playbook.md`)**: The master manual detailing sandboxing parameters, hierarchical rule overrides, skill triggers, background tasks, sidecars, and Python SDK pipelines.



---

## 🚀 Quick Start Guide (Harness Bootstrapping)

You can bootstrap and harden any target workspace prior to coding using either a single-line remote installer (no repository clone required) or a local clone.

### Option A: Remote Installer (Zero-Clone, Recommended)
Inside the root of the target project workspace you want to configure, run this single-line command:
```bash
curl -fsSL https://raw.githubusercontent.com/carlosmscabral/antigravity-okf-customizations/main/install.sh | bash
```
*This downloads the latest main zip archive, unpacks all customization folders dynamically, and recursively copies them to `.agents/` without hardcoding any file names.*


### Option B: Local Bootstrap (From Clone)
If you have cloned this optimizations repository locally, run the bootstrap installer pointing to its path:
```bash
cd /path/to/target/project
python3 /path/to/antigravity_okf_customizations/bootstrap.py
```
*This programmatically symlinks the plugins and copies the configurator agent prompt.*

---

## ⚡ Interactive Configuration and Sandbox Handoff

Once JIT-harness files are written, follow these simple handoff steps:

### Step 1: Run the Configurator Agent
Launch the interactive configuration session inside your workspace, then activate the configurator from the Agent Selection panel:

```bash
# 1. Start the session
agy

# 2. Type this mid-session and select 'harness-configurator'
/agents
```
*The agent will greet you with its static discovery report, ask you key questions regarding your tech stack, database, and safety posture, and dynamically generate your harness settings.*

### Step 2: Run the Sandbox Coding Session
Once the configurator writes your local `AGENTS.md` and hooks, start coding with 100% security containment:
```bash
# Option A: Run with native OS sandboxing flags
agy --sandbox

# Option B: Run in isolated Docker container
export GEMINI_SANDBOX=docker && agy
```
*Because the configurations are now locked JIT, subsequent sessions automatically run inside a highly secure sandbox matching your chosen posture and hooks.*


---

## 🛡️ Meta-Compliance Governance

To ensure this operational customization repository never suffers from stale documentation, we enforce native **Antigravity Tool Interceptor Hooks (`agy-hooks`)**:

*   **Tool Interceptor Hook (`.agents/hooks.json` $\rightarrow$ `.agents/scripts/verify-readme.sh`)**: Intercepts command-execution tools (such as staging, commits, or pushes inside `agy` sessions).
*   **Compliance Block**: If changes are detected in core configurations (such as `agents/`, `.agents/plugins/`, `install.sh`, or `bootstrap.py`) compared to `origin/main` but `README.md` is **not updated**, the hook outputs a high-consequence panel and halts the tool execution!

These checks guarantee that documentation is treated as a first-class citizen alongside configurations inside active `agy` sessions!


---

## 👥 Contributions & Governance

This suite is maintained by **Carlos Cabral** and agentic architects. Pull requests are welcomed to expand the plugin library (e.g., adding a `disposable-code-harness` or stack-specific templates).


# Antigravity Customizations & Dynamic Harness Configurator (DHC)

An operational repository that implements the **New SDLC** best practices using the **Google Antigravity (AGY)** agentic customization engine. 

This repository houses your central Antigravity playbooks, flexible, hot-swappable plugins, and an interactive **Harness Configurator Agent** with a python bootstrap installer to instantly provision safe, sandboxed workspaces.

---

## ⚡ Key Components

```
                      [CLONE TARGET REPOSITORY]
                                 │
                                 ▼
                     [RUN bootstrap.py SCRIPT]
                                 │
                                 ▼ (Deploys Configurator Prompt & symlinks plugins)
                 [agy --agent harness-configurator]
                                 │
        ┌────────────────────────┴────────────────────────┐
        ▼ (Silently scans repository manifests)            ▼ (Interviews the developer)
 [Auto-Suggest Frameworks]                         [Selects standard/strict profiles]
        └────────────────────────┬────────────────────────┘
                                 │
                                 ▼ (Generates settings, rules, hooks JIT)
                  [READY FOR CODES IN SANDBOX!]
```

1.  **The Bootstrap Installer (`bootstrap.py`)**: A zero-dependency script. Running this in any cloned target project establishes local `.agents/` structures, copying the Configurator Agent and linking all reference plugins in one click.
2.  **The Harness Configurator Agent (`agents/harness-configurator.md`)**: A specialized, pre-configured Antigravity Agent. It silent-scans your workspace manifests (`package.json`, `requirements.txt`), conducts a structured interview with the developer, and programmatically writes local `settings.json`, custom linter/blocker `hooks.json`, and `.antigravityignore` configurations.
3.  **Flexible Customization Plugins (`.agents/plugins/`)**:
    -   `standard-harness`: Enforces standard style guidelines, code formatting, linter execution, and testing boundaries.
    -   `strict-banking-harness`: Implements an air-gapped, zero-network security perimeter. Restricts filesystem read/writes, blocks public package mirrors, and features **pre-command hooks blocking `curl` and `wget`** to prevent unverified script execution.
4.  **Operational Integration Playbook (`playbooks/antigravity_integration_playbook.md`)**: The master manual detailing sandboxing parameters, hierarchical rule overrides, skill triggers, background tasks, sidecars, and Python SDK pipelines.

---

## 🚀 Quick Start Guide (Git-to-Sandbox Loop)

To bootstrap and harden any target workspace prior to coding, follow this simple 3-step loop:

### Step 1: Run the Bootstrap Script
Inside the target workspace you want to configure, execute the bootstrap script from this folder:
```bash
cd /path/to/target/project
python3 /path/to/antigravity_okf_customizations/bootstrap.py
```
*This deploys the Harness Configurator Agent prompt and links the standard/strict plugins.*

### Step 2: Run the Configurator Agent TUI
Launch the interactive configuration session:
```bash
agy --agent harness-configurator
```
*The agent will greet you with its static discovery report, ask you key questions regarding your tech stack, database, and safety posture, and dynamically generate your harness settings.*

### Step 3: Run the Sandbox Coding Session
Once the configurator writes your local `settings.json` and hooks, start coding with 100% security:
```bash
export GEMINI_SANDBOX=docker
agy
```
*Because the configurations are now locked JIT, subsequent sessions automatically run inside a highly secure, restricted gVisor terminal container.*

---

## 👥 Contributions & Governance

This suite is maintained by **Carlos Cabral** and agentic architects. Pull requests are welcomed to expand the plugin library (e.g., adding a `disposable-code-harness` or stack-specific templates).

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

## 🚀 Quick Start Guide (Harness Bootstrapping)

You can bootstrap and harden any target workspace prior to coding using either a single-line remote installer (no repository clone required) or a local clone.

### Option A: Remote Installer (Zero-Clone, Recommended)
Inside the root of the target project workspace you want to configure, run this single-line command:
```bash
curl -fsSL https://raw.githubusercontent.com/carlosmscabral/antigravity-okf-customizations/main/install.py | python3
```
*This downloads all necessary DHC agent prompts, plugin assets, rules, scripts, and hooks directly from GitHub Raw and marks script gates as executable.*

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
Launch the interactive configuration session inside your workspace:

```bash
agy --agent harness-configurator
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

## 👥 Contributions & Governance

This suite is maintained by **Carlos Cabral** and agentic architects. Pull requests are welcomed to expand the plugin library (e.g., adding a `disposable-code-harness` or stack-specific templates).

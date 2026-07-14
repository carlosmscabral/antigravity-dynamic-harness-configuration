# Antigravity Dynamic Harness Configuration (DHC) 🚀

An operational repository implementing modern **agentic SDLC sandboxing and harness customization** using the **Google Antigravity (AGY)** engine.

This repository houses central Antigravity playbooks, modular hot-swappable plugins, and an interactive **Harness Configurator Agent** with a dynamic installer to instantly provision safe, sandboxed workspaces.

---

## ⚡ TL;DR Quick Start

Bootstrap, configure, and code inside any target workspace in three simple commands:

### 1. Bootstrap the Workspace
Inside the root of the target project folder you want to configure, run the dynamic installer:
```bash
curl -fsSL https://raw.githubusercontent.com/carlosmscabral/antigravity-dynamic-harness-configuration/main/install.sh | bash
```
> [!NOTE]
> For offline/air-gapped banking environments, clone this repo and run the local installer instead:
> `python3 /path/to/cloned/antigravity-dynamic-harness-configuration/bootstrap.py`

### 2. Run the Interactive Configurator
Open your Antigravity session and activate the configurator agent:
```bash
# 1. Start the CLI session
agy

# 2. Inside the chat, select the configurator:
/agents -> harness-configurator
```
*The configurator will scan your workspace, interview you, and write your JIT security rules, custom hooks, `.antigravityignore`, and `mcp_config.json` templates.*

### 3. Code with 100% Security Sandbox
Once configuration files are written, run your subsequent coding sessions with native OS or containerized isolation:
```bash
# Option A: Native OS sandboxing
agy --sandbox

# Option B: Isolated Docker container
export GEMINI_SANDBOX=docker && agy
```

---

## 🏗️ Components Architecture

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

---

## ⚡ Key Components & Architecture

1.  **The Shell Installer (`install.sh`)**: A lightweight, zero-dependency shell script. It dynamically fetches the latest optimizations archive, unpacks the entire suite locally, and configures permissions without hardcoding file names.
2.  **The Bootstrap Installer (`bootstrap.py`)**: A local python utility that programmatically symlinks (for active development) or copies files and deploys config files to `.agents/` in one execution.
3.  **The Harness Configurator Agent (`agents/harness-configurator/agent.md`)**: A simplified, decoupled setup orchestrator. It silent-scans your workspace for frameworks and SDK manifest indicators, conducts a structured interview with the developer, and programmatically copies selected plugins, writes `.agents/mcp_config.json`, `.agents/hooks.json`, and `.antigravityignore`.
4.  **Dormant Plugins Cache (`.agents/plugins_cache/`)**: An inactive cache directory. Storing your customization plugins here prevents them from auto-activating on startup. Only selected plugins are promoted JIT into `.agents/plugins/` by the configurator.
5.  **Operational Integration Playbook (`playbooks/antigravity_integration_playbook.md`)**: The master manual detailing sandboxing parameters, hierarchical rule overrides, skill triggers, background tasks, sidecars, and Python SDK pipelines.

---

## 🔌 Modular Customization Plugins

*   **`standard-harness` (General SDLC)**:
    Enforces standard styling, modular testing conventions, formatting linter execution, the `refactoring-expert` subagent, and deploys a robust default `.antigravityignore` template.
*   **`strict-banking-harness` (Enterprise Security)**:
    Establishes a strict, air-gapped security perimeter with **command-interceptor hooks blocking `curl`/`wget`** via `crypto-auditor` subagents.
*   **`adk-developer` (Specialty ADK)**:
    Tailored for Google Agent Development Kit (ADK) projects. It **loads `agents-cli` as cognitive AI Skills (under `.agents/skills/`)**, enforces pre-flight Pydantic schema validation, and **configures the `adk-docs-mcp` server out-of-the-box** to retrieve real-time classes and SDK tutorials directly from `https://adk.dev/llms.txt`.

---

## 🛡️ Meta-Compliance Governance

To ensure this operational customization repository never suffers from stale documentation, we enforce native **Antigravity Tool Interceptor Hooks (`agy-hooks`)**:

*   **Tool Interceptor Hook (`.agents/hooks.json` $\rightarrow$ `.agents/scripts/verify-readme.sh`)**: Intercepts command-execution tools (such as staging, commits, or pushes inside `agy` sessions).
*   **Compliance Block**: If changes are detected in core configurations (such as `agents/`, `.agents/plugins/`, `install.sh`, or `bootstrap.py`) compared to `origin/main` but `README.md` is **not updated**, the hook outputs a high-consequence panel and halts the tool execution!

---

## 👥 Contributions & Governance

This suite is maintained by **Carlos Cabral** and agentic architects. Pull requests are welcomed to expand the plugin library (e.g., adding a `disposable-code-harness` or stack-specific templates).

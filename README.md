# Antigravity Dynamic Harness Configuration (DHC) 🚀

An operational repository implementing modern **agentic SDLC sandboxing and harness customization** using the **Google Antigravity (AGY)** engine.

This repository is a **thin installer**: it houses the interactive **Harness Configurator Agent**, the dynamic installers (`install.sh` / `bootstrap.py`), and the Antigravity playbooks. The harness **plugins and skills themselves live in the [cabral-skills](https://github.com/carlosmscabral/cabral-skills) monorepo** (the single source of truth) and are fetched at a **pinned git tag** at install time.

---

## ⚡ TL;DR Quick Start

Bootstrap, configure, and code inside any target workspace in three simple commands:

### 1. Bootstrap the Workspace
Inside the root of the target project folder you want to configure, run the dynamic installer:
```bash
curl -fsSL https://raw.githubusercontent.com/carlosmscabral/antigravity-dynamic-harness-configuration/main/install.sh | bash
```
> [!NOTE]
> For offline/air-gapped banking environments, clone **both** this repo and [cabral-skills](https://github.com/carlosmscabral/cabral-skills) side by side, then run the local installer:
> `python3 /path/to/antigravity-dynamic-harness-configuration/bootstrap.py`
> It sources plugins + skills from `../cabral-skills` by default (override with `CABRAL_SKILLS_DEV_PATH`).

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

1.  **The Shell Installer (`install.sh`)**: A lightweight, zero-dependency shell script. It fetches the configurator agent from this repo and the plugins + skills from `cabral-skills` at the **pinned tag** (`CABRAL_SKILLS_TAG`, top of the script — bump it to adopt a new content release), unpacks them into local caches, and configures permissions.
2.  **The Bootstrap Installer (`bootstrap.py`)**: A local python utility for developer/offline mode. It symlinks (for live edits) or copies plugins + skills from a local `cabral-skills` checkout (`../cabral-skills` by default, or `CABRAL_SKILLS_DEV_PATH`) into the `.agents/` caches.
3.  **The Harness Configurator Agent (`agents/harness-configurator/agent.md`)**: A simplified, decoupled setup orchestrator. It silent-scans your workspace, interviews you, and **promotes** the selected plugins in one of two modes (`DHC_FLATTEN` flag, default off): **default** copies the skill-materialized bundle into `.agents/plugins/` (auto-discovered by *interactive* `agy`); **flatten** distributes components into direct workspace scope (`.agents/skills/`, `.agents/hooks.json`, …) so the harness also loads under headless `agy -p`. It also **authors workspace rules into `.agents/rules/`** (project policy, both modes) and writes project-specific `.agents/mcp_config.json` / `.antigravityignore` / `AGENTS.md` (no-clobber).
4.  **Dormant Caches (`.agents/plugins_cache/` + `.agents/skills_cache/`)**: Inactive cache directories populated at install — the *source* the configurator promotes from. They are **kept on purpose** (the offline source for later reconfiguration, e.g. air-gapped setups) and the installer **git-ignores them** so they never land in your repo.
5.  **Operational Integration Playbook (`playbooks/antigravity_integration_playbook.md`)**: The master manual detailing sandboxing parameters, hierarchical rule overrides, skill triggers, background tasks, sidecars, and Python SDK pipelines.

---

## 🔌 Modular Customization Plugins

> Plugins are defined in the [cabral-skills](https://github.com/carlosmscabral/cabral-skills) monorepo under `plugins/`. Each is a capability bundle (skills/agents/hooks/mcp/commands) that references its skills by name (`plugin.json` → `skills[]`); the bodies live under `cabral-skills/skills/` and are materialized into the workspace during promotion (default: into `.agents/plugins/<name>/`; flatten: into direct `.agents/` scope). Plugins do **not** carry rules — those are authored into the workspace `.agents/rules/` by the configurator.

*   **`standard-harness` (General SDLC)**:
    Enforces standard styling, modular testing conventions, formatting linter execution, the `refactoring-expert` subagent, and deploys a robust default `.antigravityignore` template.
*   **`strict-banking-harness` (Enterprise Security)**:
    Establishes a strict, air-gapped security perimeter with **command-interceptor hooks blocking `curl`/`wget`** via `crypto-auditor` subagents.
*   **`adk-developer` (Specialty ADK)**:
    Tailored for Google Agent Development Kit (ADK) projects. It **materializes the `google-agents-cli-adk-frontend` cognitive AI Skill** into the active plugin, enforces pre-flight Pydantic schema validation, and **configures the `adk-docs-mcp` server out-of-the-box** to retrieve real-time classes and SDK tutorials directly from `https://adk.dev/llms.txt`.

---

## 🛡️ Meta-Compliance Governance

To ensure this operational customization repository never suffers from stale documentation, we enforce native **Antigravity Tool Interceptor Hooks (`agy-hooks`)**:

*   **Tool Interceptor Hook (`.agents/hooks.json` $\rightarrow$ `.agents/scripts/verify-readme.sh`)**: Intercepts command-execution tools (such as staging, commits, or pushes inside `agy` sessions).
*   **Compliance Block**: If changes are detected in core configurations (such as `agents/`, `install.sh`, or `bootstrap.py`) compared to `origin/main` but `README.md` is **not updated**, the hook outputs a high-consequence panel and halts the tool execution!

---

## 🗺️ Roadmap

The DHC today is a proven skeleton. [`ROADMAP.md`](ROADMAP.md) tracks the hardening plan:
**Phase 1** — make provisioning deterministic, rules governed, and verification efficacy-based;
**Phase 2** — enterprise distributed harness management from one company source of truth
(mandatory global controls + team defaults + project opt-in, pinned/signed/audited).

## 👥 Contributions & Governance

This suite is maintained by **Carlos Cabral** and agentic architects. Pull requests are welcomed to expand the plugin library (e.g., adding a `disposable-code-harness` or stack-specific templates).

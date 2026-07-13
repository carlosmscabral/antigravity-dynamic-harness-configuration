---
type: AI Methodology Concept
title: Dynamic Harness Configurator (DHC) — Agentic Harness Engineering
description: Overhauled architecture for an interactive, agent-driven bootstrap loop. Discovers repository stacks, suggests tailored safety/tool profiles, conducts developer interviews, and provisions hardened hooks and rules JIT.
tags: [architecture, harness-engineering, security, automation, meta-agents]
timestamp: 2026-07-13T16:03:00-03:00
---

# Dynamic Harness Configurator (DHC) — Agentic Harness Engineering

In traditional software development, configuring the local development environment is a manual, error-prone task. In the era of **Vibe Coding**, allowing autonomous agents to operate unsandboxed or unconfigured is a massive security risk and causes rapid accumulation of **Context Debt** and **Capability Gaps**.

The **Dynamic Harness Configurator (DHC)** is an agentic design paradigm. Instead of a static setup script, a specialized, high-security **Harness Architect Agent** is loaded JIT to scan the workspace manifests, interview the developer, suggest optimized tool sets, and programmatically construct the security, linter, and subagent perimeters *prior* to starting any implementation work.

---

## 1. The Dynamic Handoff Topology

By separating the setup into **Harness Provisioning** and **Code Implementation**, we resolve the fundamental paradox of agent security: *An agent cannot securely sandbox or restrict itself from the inside.*

```
                 ┌──────────────────────────────────────┐
                 │    ANTIGRAVITY CUSTOMIZATION LIB     │
                 │   - Standard & Strict banking plugins│
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼ [bootstrap.py Installer]
                 ┌──────────────────────────────────────┐
                 │     HARNESS CONFIGURATOR AGENT       │
                 │  - Silently scans framework manifests│
                 │  - Interviews developer in TUI chat  │
                 │  - Deploys rules, hooks, and ignores │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼ [DYNAMIC JIT PROVISIONING]
                 ┌──────────────────────────────────────┐
                 │         THE HARDENED HARNESS         │
                 │  - env: GEMINI_SANDBOX=docker        │
                 │  - Command-blocking hooks active     │
                 │  - Customized subagents pre-wired     │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼ [SANDBOXED CODES]
                 ┌──────────────────────────────────────┐
                 │          SECURE CODING AGENT         │
                 │  - Executes tools inside gVisor      │
                 └──────────────────────────────────────┘
```

---

## 2. Hard technical Constraints of the External CLI

When designing an operational DHC, we must adhere strictly to the security model of the external Antigravity CLI:

1.  **No Workspace `settings.json`**: To prevent malicious repositories from silently hijacking developer environments, the CLI **completely ignores** local workspace settings (e.g., `.agents/settings.json` or `.gemini/settings.json`). 
2.  **Global Sandbox Control & Enforcement**: Sandboxing is governed globally via `~/.gemini/antigravity-cli/settings.json` (using `"enableTerminalSandbox": true` and `"toolPermission": "proceed-in-sandbox"`) or can be dynamically forced at launch using either:
    *   **CLI Launcher Flags**: `agy --sandbox` or `agy -s` (preferred, zero friction).
    *   **Environment Variables**: `export GEMINI_SANDBOX=true` (or specify backend like `docker`, `sandbox-exec` for macOS, `nsjail` for Linux).
3.  **Local Workspace-Level Gates**: While global sandboxing is host-governed, the DHC agent dynamically manages workspace-level tool boundaries by generating:
    *   `.agents/hooks.json`: Intercepting, linter-enforcing, or command-blocking gates (e.g., blocking `curl`/`wget`).
    *   `AGENTS.md` (Workspace Root): Defining cumulative repository rules and tech-stack conventions.
    *   `.agents/plugins/`: Swapping whole compliance profiles (e.g., standard vs strict-banking).
    *   `.antigravityignore`: Masking virtual envs, API credentials, and databases.


---

## 3. The 3-Phase DHC Loop in Action

### Phase 1: Silent Discovery & Manifest Scan
At boot, the DHC Agent silently scans the workspace directory. It avoids asking the user basic questions that can be extracted programmatically:
*   **Node.js**: Detects `package.json` $\rightarrow$ Suggests node testing, formatting, and port bindings.
*   **Python**: Detects `requirements.txt`/`pyproject.toml` $\rightarrow$ Suggests black/ruff linter hooks and pytest.
*   **Datastores**: Detects `.env.example` SQL connection strings $\rightarrow$ Suggests loading a local database MCP.

### Phase 2: Interactive Developer Interview
The agent presents a structured **Harness Discovery Report** inside the TUI and interviews the developer to confirm preferences:
*   *"I detected Python (FastAPI) and PostgreSQL connection variables. I suggest our Standard Harness profile with local PostgreSQL MCP integrations and automatic pytest-linter hooks. Would you like to proceed, or switch to our air-gapped Strict Banking posture?"*

### Phase 3: JIT Provisioning (Assembly)
Upon confirmation, the agent uses its filesystem tools to write the customized workspace boundaries:
*   Deploys selected plugins (e.g., `standard-harness` or `strict-banking-harness` containing pre-built rules and blocker hooks).
*   Writes `.agents/hooks.json` to configure interceptors.
*   Writes `.antigravityignore` to restrict agent visibility.
*   Signals completion, instructing the user to run the sandbox handoff command.

---

## 4. Operational Implementation Patterns

### I. The Configurator Agent Prompt (`agents/harness-configurator.md`)
The DHC agent is equipped with a highly structured prompt commanding filesystem access and instructing it how to compose `.agents/mcp_config.json` and `.agents/hooks.json` schemas dynamically based on user selections.

### II. The Bootstrap Installer (`bootstrap.py`)
A robust, zero-dependency Python bootstrap script resides at the repository root. When executed inside a clean target workspace, it programmatically symlinks the customizations library and copies the configurator agent prompt, preparing the workspace for the interactive setup chat.

---

## 5. Architectural Benefits

*   **Bypasses Context Bloat**: Pre-wiring rules and hooks into `.agents/` eliminates the need to load extensive guidelines into the model's memory, reducing token consumption and focusing attention.
*   **Absolute Compliance**: Forcing command-blocking gates (such as intercepting public `npm install` scopes or external web curls) ensures that the subsequently booted coding agent cannot violate organizational security rules, even if malicious instructions are injected into the codebase.

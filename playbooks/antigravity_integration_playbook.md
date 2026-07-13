---
type: Playbook
title: Antigravity Practical Integration Playbook — Engineering the Harness
description: A practical operational manual for configuring and programming the Antigravity Harness. Integrates all OKF database concepts (Zero-Trust, SDD, EDD, A2UI, A2A, SecOps) using native Antigravity configurations, Skills, Rules, MCP, Sidecars, and SDK pipelines.
tags: [playbook, antigravity, sdk, mcp, sidecars, skills, rules, sandboxing, sdk-examples]
timestamp: 2026-07-13T14:48:00-03:00
---

# Antigravity Practical Integration Playbook — Engineering the Harness

In modern agentic engineering, **$\text{Agent} = \text{Model} + \text{Harness}$**. The LLM model is the generic cognitive engine, while the **Harness** is the specialized control loop, transport layer, sandboxing environment, and permission framework that binds the model to your workspace.

This playbook provides a practical guide on how to configure and program the **Antigravity Harness** (across Antigravity 2.0, the `agy` CLI, and the Python SDK) to implement the security, testing, planning, and integration concepts of the New SDLC database.

---

## 1. Zero-Trust Security & Sandboxing (FS & Terminal Control)

To enforce **Zero Ambient Authority** and mitigate **Denial of Wallet (DoW)** or **poisoned repository attacks**, you must establish a rigid perimeter around Antigravity's filesystem and shell tools.

### I. Hardening the Filesystem Perimeter (`settings.json`)
Configure your global or project-level settings in **`~/.gemini/antigravity-cli/settings.json`** to define strict boundaries. Never allow an agent free rein of your machine:

```json
{
  "model": "gemini-3.5-pro",
  "allowNonWorkspaceAccess": false,
  "trustedWorkspaces": [
    "/Users/carloscabral/.gemini/antigravity/scratch/new_sdlc_okf"
  ],
  "toolPermission": "request-review",
  "artifactReviewPolicy": "asks-for-review"
}
```
*   `allowNonWorkspaceAccess: false` blocks the agent from reading or writing files outside the active workspace directory (protecting SSH keys, application data, and internal configurations).
*   `toolPermission: "request-review"` enforces an interactive verification step. The agent must explicitly request permission for tool execution, preventing automated silent execution.

### II. Enabling Process Isolation (Antigravity Sandbox)
To prevent agents from executing destructive or unverified shell scripts natively on your host OS, you can force all command execution into a secure, contained sandbox:

1.  **Launch with Sandbox Flags (Recommended)**:
    Simply launch the Antigravity session with the sandbox flag:
    ```bash
    agy --sandbox
    # Or using the shorthand alias:
    agy -s
    ```
2.  **Using Environment Variables**:
    Alternatively, export the sandbox controller variable in your active terminal:
    ```bash
    export GEMINI_SANDBOX=docker
    ```
    *(Other valid sandbox providers include `true` for auto-detect, `sandbox-exec` for native macOS containment, or `nsjail` on Linux).*
3.  **Global Settings Configuration**:
    To enforce sandboxing across all sessions, configure your global settings at `~/.gemini/antigravity-cli/settings.json`:
    ```json
    {
      "enableTerminalSandbox": true,
      "toolPermission": "proceed-in-sandbox"
    }
    ```
    This ensures that any subsequent `run_command` executes inside a containerized, low-privilege sandbox, keeping your local host files and kernel fully protected.


---

## 2. Setting System Posture: Rules (`AGENTS.md`)

Rules establish static constraints that the agent must load into memory on every execution. To prevent context rot and bloated prompts, manage rules hierarchically:

```
        ~/.gemini/config/AGENTS.md                 .agents/AGENTS.md
       ┌───────────────────────────┐         ┌───────────────────────────┐
       │   GLOBAL COMPLIANCE RULE  │         │   PROJECT-SPECIFIC RULE   │
       │  - Zero-Trust security    │────────►│  - Tech Stack conventions  │
       │  - Mandatory logging      │         │  - Formatting, directories│
       └───────────────────────────┘         └───────────────────────────┘
```

### I. Global Rules (`~/.gemini/config/AGENTS.md`)
Create this file to define universal, non-negotiable security behaviors and diagnostic logging patterns:
```markdown
# Global Agent Governance Rules

## 1. Safety & Sandboxing
*   All terminal executions must be audited for command injections.
*   Never attempt to download raw executable binaries via curl/wget.

## 2. Maintain Documentation Integrity
*   Always preserve all existing docstrings and comments.
*   Do not overwrite files to make minor edits—use multi_replace_file_content.
```

### II. Project-Scoped Rules (`.agents/AGENTS.md`)
Create this file at your active workspace root to enforce design guidelines, language-specific conventions, and testing constraints:
```markdown
# Project Rules for OKF Database

## 1. Engineering Conventions
*   All concept documents must contain valid YAML frontmatter matching index.md schemas.
*   All playbook guides must use the Gherkin scenario format for test-driven behavior patterns.

## 2. Directory Layout
*   Save all core concept documents in `/concepts/` using snake_case.
*   Save day-to-day playbook guides in `/playbooks/`.
```

---

## 3. Custom Skills: Modular Know-How (`skills/` directory)

A **Skill** represents a package of know-how. By packaging instructions as on-demand Skills rather than "Always-On" rules, you keep context windows lightweight and prevent attention dilution.

### I. Directory Topology for a Custom Skill
Place your custom skills in `.agents/skills/<skill_name>/` for project-scoped access:

```
.agents/skills/spec-validation/
├── SKILL.md        # Main instruction file (YAML frontmatter + Markdown)
├── scripts/        # Deterministic validation and linting scripts
│   └── validate_markdown.py
├── examples/       # Exemplar markdown specifications (worked examples)
│   └── valid_spec.md
└── references/     # Deep-dive formatting constraints and rules
    └── yaml_parsing_rules.md
```

### II. Drafting `SKILL.md` with Trigger Frontmatter
YAML frontmatter fields (`name`, `description`) are used by Antigravity's router for semantic matching. Keep the description extremely descriptive:

```markdown
---
name: spec-validation
description: Validates markdown syntax, YAML frontmatter formatting, and cross-reference links across our OKF database directories. Trigger this skill whenever a markdown file is created, modified, or audited for syntax.
---

# Spec Validation Skill

You are a specialized markdown validator. When triggered, use the script in your scripts/ folder to run syntax checks and link resolution audits.

## Instructions
1. Invoke the script: `python3 scripts/validate_markdown.py --path <workspace_root>`
2. Capture any output errors and report them as code-block annotations.
3. If errors are found, automatically execute surgical replace_file_content calls to resolve them.
```

### III. Shifting Intelligence Left: The Script Helper
Avoid writing massive semantic rules inside `SKILL.md` (e.g., *"ALWAYS check that files start with three dashes"*). Write a deterministic Python script inside `.agents/skills/spec-validation/scripts/validate_markdown.py` to run regular expression checks. Let the LLM trigger the script, but let the script enforce the hard formatting constraints.

---

## 4. Connecting Reach: Model Context Protocol (MCP)

While Skills teach agents **how** to work (know-how), MCP servers grant agents **access** to external resources (reach)—databases, local developer tools, system APIs, or third-party web endpoints.

```
 [ANTIGRAVITY HARNESS] ─────── MCP Transport (stdio/SSE) ───────► [MCP SERVERS]
  - Resolves tool calls                                           - cloudrun
  - Manages schemas dynamically                                   - chrome-devtools
```

### I. Composing Skills with MCP
Never write custom agent code to handle standard, repeatable external actions. Composing skills with pre-built MCP servers reduces development complexity:

*   **Firebase Actions**: Load `firebase-basics` and `firebase-firestore` skills, and let them communicate via the standard system tools.
*   **Browser Control**: Use the pre-loaded `chrome-devtools-plugin` to automate browser audits, rather than writing bespoke curl or selenium commands.

### II. Debugging MCP Transport
If tool schemas fail to parse or connection timeouts occur:
1.  Open the Antigravity TUI settings panel via `/mcp` (in the CLI) or the left sidebar (in App 2.0).
2.  Inspect active server states and trace standard input/output streams.
3.  Execute raw schemas to verify JSON-RPC payload integrity, isolating transport issues from LLM prompt errors.

---

## 5. Background Tasks, Sidecars & Scheduled Timers

Real-world development involves slow-running tasks (such as end-to-end integration tests, static code audits, and security vulnerability scans) that are unsuited for synchronous chat loops. Antigravity handles these as asynchronous background tasks.

### I. Programmatic One-Shot Timers
Use the `schedule` tool to trigger an action after a delay, or to wait for background operations to complete without blocking the main terminal session. This is an elegant alternative to setting up fragile, sleeping bash subprocesses:

```json
{
  "DurationSeconds": "300",
  "Prompt": "Check on the status of our automated CI integration test and report any test failures",
  "TimerCondition": "any"
}
```
`TimerCondition: "any"` ensures that if any background event completes early (or a user sends a message), the timer cancels itself, preventing wasteful liveness loops.

### II. Automated "Evaluator Sidecars" (Active Telemetry)
Configure recurring cron-based background jobs to run repository sanitization audits dynamically. For example, to run an integrity scanner every hour to detect repo poisoning (homoglyphs) or broken files:

```json
{
  "CronExpression": "0 * * * *",
  "MaxIterations": "24",
  "Prompt": "Scan our workspace for zero-width Unicode characters or broken internal markdown links."
}
```
This deploys an **Active Evaluator Sidecar** that monitors the codebase's health while you are offline, warning you instantly via system notifications if trust decay or regression occurs.

---

## 6. Programmatic Pipelines: Antigravity Python SDK

When integrating agentic capabilities directly into your CI/CD pipelines, automated testing harnesses, or custom IDE plugins, use the official Python SDK: `google-antigravity`.

### Complete SDK Pipeline with Active Telemetry & Interception
The following script demonstrates how to programmatically initialize an agent with write capabilities, execute a task, and intercept the agent's internal reasoning and tool calls in real time to generate active telemetry:

```python
import asyncio
import sys
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

async def run_governed_pipeline():
    # 1. Configure the agent with complete capabilities (read/write access)
    config = LocalAgentConfig(
        system_instructions="You are an automated code refactoring specialist.",
        capabilities=CapabilitiesConfig(), # Permits file edits and command executions
    )

    # 2. Initialize the agent within the async context manager
    async with Agent(config) as agent:
        print("[System] Spawning Antigravity Agent...")
        
        # 3. Submit a prompt to start the asynchronous execution path
        response = await agent.chat("Refactor utility.py to match standard Python docstrings.")
        
        # 4. Concurrently monitor thoughts, tools, and token deltas
        async def monitor_thoughts():
            async for thought in response.thoughts:
                # Intercept internal reasoning (Glass Box telemetry)
                print(f"[Telemetry - Thinking] {thought}")

        async def monitor_tools():
            async for call in response.tool_calls:
                # Intercept strongly-typed tool call telemetry before execution
                print(f"[Telemetry - Tool Call] Executing: {call.name} with args: {call.args}")

        async def stream_output():
            # Stream finalized response tokens as they arrive
            async for token in response:
                sys.stdout.write(token)
                sys.stdout.flush()

        # Execute concurrently over the event loop
        await asyncio.gather(
            monitor_thoughts(),
            monitor_tools(),
            stream_output()
        )
        print("\n[System] Refactoring pipeline execution complete.")

if __name__ == "__main__":
    asyncio.run(run_governed_pipeline())
```

---

## 7. Custom Subagents & Multi-Agent Microservices

To avoid the monolithic ceiling and keep context debt low, programmatically divide massive workflows into specialized subagents:

### I. Spawning Parallel Subagents
Within your automation scripts or custom skills, use the `invoke_subagent` tool to spawn focused subagents. This is how you orchestrate a multi-agent workforce concurrently:

```json
{
  "Subagents": [
    {
      "TypeName": "self",
      "Role": "Database Schema Auditor",
      "Prompt": "Audit the newly generated database schemas for 3NF compliance and index performance."
    },
    {
      "TypeName": "self",
      "Role": "Frontend UI Auditor",
      "Prompt": "Audit the dynamic visual layouts for color contrast, mobile reflow, and accessibility."
    }
  ]
}
```

### II. State Management & Lifecycle Handoffs
*   **Workspace Branching**: Use the `"Workspace": "branch"` parameter to create isolated git branches for each subagent. This prevents overlapping code edits and merge conflicts.
*   **The Message Bus**: Subagents should never pass heavy text payloads to communicate. Instruct them to write intermediate artifacts (such as schemas or reports) to the shared workspace and pass lightweight JSON file URIs (e.g., `file:///tmp/schema.json`) via the messaging system (`send_message`).

---

## 8. Practical DHC Git-to-Sandbox Developer Loop with `bootstrap.py`

To configure and execute the **Dynamic Harness Configurator (DHC)** workflow in your day-to-day development, follow this 4-step Git-to-Sandbox developer loop. This eliminates manual configuration and JIT-provisions your workspace boundaries before coding.

### Step 1: Clone your target repository
When starting a new feature or project, clone the repository and move into its root directory:
```bash
git clone git@github.com:yourorg/temp_pizza_project.git
cd temp_pizza_project
```

### Step 2: Run the zero-dependency Bootstrap Installer
Run the central customizations library installer inside your project root. This prepares your directory for the interactive setup chat:
```bash
python3 /path/to/cloned/antigravity-okf-customizations/bootstrap.py
```
*This programmatically creates `.agents/agents/`, deploys our specialized Harness Configurator Agent prompt, and symlinks your standard and strict banking plugins under `.agents/plugins/` in one command.*

### Step 3: Run the Configurator Agent to Provision your Harness JIT
Boot up the Antigravity CLI session explicitly targeting the Configurator Agent:
```bash
agy --agent harness-configurator
```
*At boot, the Configurator Agent silently scans your workspace files (detecting `requirements.txt` or `package.json`), pre-suggests tailored testing and linter setups, and conducts an interactive interview to determine your compliance posture (e.g., standard vs. strict-banking).*

Based on your inputs, the agent dynamically:
1.  Symlinks your selected harness plugins.
2.  Writes `.agents/hooks.json` to configure sequential command-sanitizers or blockers (such as blocking public `npm` mirrors or external web curls).
3.  Writes `.agents/AGENTS.md` and `.antigravityignore` files.

*(Note: Workspace-scoped settings.json files are ignored by the Antigravity CLI to prevent malicious repositories from overriding your local execution permissions. All security and transport gates are managed locally via plugins, rules, and hooks, while sandboxing is handled in the next step).*

### Step 4: The Sandboxed Handoff
Once the configurator writes your local workspace gates, exit the setup session and launch the coding agent inside a 100% compliant, container-isolated Sandbox:
```bash
# Exit setup
/exit

# Launch secure, sandboxed coding session with preferred OS sandbox:
agy --sandbox

# Or force Docker execution container:
export GEMINI_SANDBOX=docker && agy
```
Because the local plugins, hooks, rules, and ignores are now written, the subsequent coding session automatically runs inside a gVisor-isolated Docker sandbox (or native OS containment layer). The agent will inherit all your exact linter hooks, blocked commands, and design rules, letting you write the application with zero compliance friction!



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

### II. Enabling Process Isolation (Docker & gVisor Sandbox)
To prevent agents from executing malicious or destructive shell scripts natively on your host OS:
1.  **Configure environment**: Run the following in your terminal session before starting the CLI:
    ```bash
    export GEMINI_SANDBOX=docker
    ```
2.  **Configure settings**: Ensure that terminal sandboxing is enabled inside your `settings.json`:
    ```json
    {
      "enableTerminalSandbox": true
    }
    ```
    This forces Antigravity to boot gVisor-isolated Docker containers JIT, executing every `run_command` action inside a restricted, low-privilege runtime container, protecting your machine's kernel.

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

## 8. Practical DHC Git-to-Sandbox Developer Loop with `agy`

To configure and execute the **Dynamic Harness Configurator (DHC)** workflow in your day-to-day development using the standard **Antigravity CLI (`agy`)**, follow this 4-step Git-to-Sandbox developer loop.

### Step 1: Link your central OKF Database Repository
To make our best-practice concepts, rules, and playbooks universally accessible to your `agy` sessions:
1.  **Globally (Recommended)**: Symlink your local OKF Knowledge Database repository path directly to the global customizations root:
    ```bash
    ln -s /path/to/cloned/new_sdlc_okf ~/.gemini/config/new_sdlc_okf
    ```
2.  **Workspace-scoped**: Alternatively, add your OKF database repository as a git submodule or folder directly inside your newly cloned project's `.agents/` folder.

### Step 2: Clone your target repository & initialize `agy`
When starting a new feature or project:
1.  Clone the project repository and move into its root:
    ```bash
    git clone git@github.com:yourorg/temp_pizza_project.git
    cd temp_pizza_project
    ```
2.  Boot up the Antigravity CLI session inside the clean workspace:
    ```bash
    agy
    ```
    *(At boot, `agy` dynamically discovers the linked OKF DB playbooks and skills from the global customization root at `~/.gemini/config/` and loads them into active memory).*

### Step 3: Prompt `agy` to execute the DHC bootstrap phase
In your first message to the CLI, instruct the agent to act as the **Dynamic Harness Configurator** to bootstrap the workspace before starting any coding. Point it directly to your OKF rules and playbooks:

> **Developer Prompt:**  
> *"As our Dynamic Harness Configurator (DHC), read the playbooks at `/new_sdlc_okf/playbooks/` and our project's README/requirements. Let's bootstrap our local execution Harness before coding. Generate our workspace's secure `.gemini/antigravity-cli/settings.json` (force terminal sandboxing, disable non-workspace access), author `.agents/AGENTS.md` with our styling rules, and write our first Gherkin specification inside `/specs/`."*

`agy` will execute tools locally to:
1.  Generate `.gemini/antigravity-cli/settings.json`.
2.  Write your styling/coding conventions to `.agents/AGENTS.md`.
3.  Draft `/specs/feature_name.feature` and `/evals/test_eval.json` to lock in **Spec-Driven Design (SDD)** and **Evaluation-Driven Design (EDD)**.

### Step 4: The Sandboxed Handoff
Once the bootstrap outputs are written:
1.  **Fork your thread**: Type `/fork` or `/branch` inside the TUI to branch your conversation thread into a clean, dedicated coding slate.
2.  **Exit and Re-enter (Clean Sandbox Boot)**: Alternatively, exit the session and launch `agy` again.
    ```bash
    # Exit current bootstrap
    /exit
    
    # Launch clean coding session
    agy
    ```
    Because the local `settings.json` file is now written, **the subsequent session will automatically boot inside the restricted gVisor Docker sandbox**, pre-loaded with all your exact OKF rules, secure file boundaries, and custom project skills active. You can now build the application with 100% security compliance!

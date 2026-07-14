---
trigger: always_on
description: Guidelines for high-fidelity Google ADK development, pre-flight validations, and GCP deployment grounding.
---
# Google ADK Development and Deployment Guidelines

You are operating inside a workspace configured with the **ADK Developer Plugin**. Follow these guidelines strictly during any Agent Development Kit (ADK) development, testing, and deployment:

### 1. Unified Command Execution via `agents-cli`
- Always leverage the official `agents-cli` for all scaffolding, configuration validation, testing, and deployment tasks.
- Familiarize yourself with CLI help (e.g., `agents-cli --help`) to discover native flags, build commands, and service targets before writing bespoke scripts.

### 2. Pre-Flight Pydantic & Schema Validation
- **Dry-Run Validations**: Before triggering any long-running Cloud Run or GCP Agent Runtime deployment operations, **always validate local Pydantic rules, schemas, agent manifests, and tool definitions locally**.
- Write simple, fast-running Python tests or execute a local dry-run script to parse and assert the validity of your Pydantic models and configurations.
- Do NOT push code to Cloud environments if local validation fails, preventing wasteful wait times on simple syntax or schema mismatches.

### 3. Documentation & Code Grounding
- **Primary Source Grounding**: Ground all architectural decisions on the official ADK and GCP documentation.
- **Developer Knowledge MCP**: If the `google-developer-knowledge` MCP server is active, always use it to query real-time Google Docs, specifications, and authentication architectures.
- **ADK Source Inspection**: When dealing with advanced tool callbacks or complex execution states, look up and inspect the source code of the `agents-cli` or local SDK libraries directly to ensure correct function signatures.

### 4. Reference-First Implementation (ADK Samples)
- For design patterns such as User OAuth, token propagation, BigQuery MCP connections, and credential caching:
  - Locate, clone (e.g., as a sparse clone), or read similar reference patterns inside the official Google ADK Samples repository at: `https://github.com/google/adk-samples/tree/main/python`
  - Model your local schemas, credential caches, and tool architectures directly on these official Google-authored samples.

### 5. Secure Auth & GCP Skills Integration
- Refer to relevant GCP authentication skills and deployment guidelines from the official skills repository: `https://github.com/google/skills`.
- When dealing with End User propagation, use GCP's latest managed Auth Server specifications. Assert that the authentication token passed to downstream APIs (like BigQuery) matches the exact credentials of the acting end user.

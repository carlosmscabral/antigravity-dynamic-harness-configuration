---
name: visual-documentation
description: Multi-format visual diagram design and validation playbook. Enforces syntax safety for Mermaid.js and interactive HTML/SVG mapping, utilizing headless verification tools.
---
# Visual Documentation Skill Playbook

Use this skill when you need to construct, document, or verify software architectures, sequence paths, transactional event maps, database relations, or user-interface flows.

---

### 🛡️ Strict Mermaid.js Syntax Safety
When writing embedded Markdown `mermaid` diagrams, you must strictly satisfy these parsing rules to prevent browser or markdown renderer compilation failures:
1.  **Quoted Special Labels**: Any node label containing non-alphanumeric characters, parentheses, brackets, or math symbols **must be enclosed in double quotes**:
    *   *Correct*: `node_a["User Interface (GCP App)"]`
    *   *Incorrect*: `node_a[User Interface (GCP App)]`
2.  **No HTML Brackets**: Never use unescaped HTML characters (`<`, `>`) inside nodes. Use entities or quotes.
3.  **Strict Subgraphs**: Ensure all subgraphs have a explicit ending block (`end`) and do not cross-link internals across sibling boundaries without declaring target nodes explicitly.

---

### 🚀 Automation & Verification Tools

Before presenting any visual diagrams to the user, you must execute active verification gates to guarantee syntax correctness:

#### 1. Static Mermaid.js Syntax Check (CLI Validation)
If the project has `npm` or `npx` available, execute a headless render using the official Mermaid CLI. If this command outputs any non-zero exit status, parse its error stream to locate and repair your syntax:
```bash
# Perform a dry-run compile to null to check for syntax correctness
npx -y @mermaid-js/mermaid-cli -i input.mmd -o /dev/null
```
If compile passes, render it directly to a local project asset directory for markdown embedding:
```bash
# Render to target asset PNG
npx -y @mermaid-js/mermaid-cli -i input.mmd -o docs/images/architecture.png
```

#### 2. Interactive HTML/SVG Diagram Validation
When building richer interactive visual maps (like clickable D3.js or custom responsive SVG structures packaged as standalone single-file HTML scripts):
1.  Write the HTML diagram into a temporary workspace artifact: `scratch/diagram_test.html`.
2.  Invoke the **`browser_subagent`** to load the file locally in headless Chrome.
3.  Check the page's console logs and capture a high-resolution screenshot to visually inspect the canvas and verify that the layout displays beautifully without layout overlaps.

---

### 📊 Supported Diagram Formats

Choose the most appropriate diagram specification for your documentation target:

| Diagram Type | Best Format | Focus/Usage |
| :--- | :--- | :--- |
| **System Flowchart** | Mermaid `graph TD` / `graph LR` | Step-by-step logic, routing gateways, and sequential operations. |
| **Service Sequence** | Mermaid `sequenceDiagram` | Cross-system transaction timings, API requests, and message loops. |
| **Data ERD Model** | Mermaid `erDiagram` | Database schemas, column keys, entity relations, and data bounds. |
| **Architecture Map** | HTML + Inline SVG / SVG Canvas | Premium multi-layered system components, network zones, and databases. |

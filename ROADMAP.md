# DHC Roadmap — toward a hardened, enterprise-grade harness manager

## Where we are today (honest baseline)

The DHC is a **proven skeleton**: it rides Antigravity's native model correctly — plugins
are registered with `agy plugin install`, skills are materialized from a pinned source
([cabral-skills](https://github.com/carlosmscabral/cabral-skills)), rules are authored into
`.agents/rules/` as workspace policy, and provisioning is verified end-to-end. What it is
**not** yet: deterministic (the configurator is an LLM hand-running steps), governed (rules
are LLM-improvised), or distributed (single source, single user, self-declared selection).

This roadmap hardens it in two phases. **Phase 1** makes the single-source flow deterministic,
governed, and verifiable. **Phase 2** turns it into distributed, enterprise harness management
(mandatory org controls + team defaults + project opt-in, from one company source of truth).

## Guiding principles

1. **Deterministic where it matters.** Security/compliance provisioning must be reproducible
   and auditable — not left to model judgment. The LLM handles discovery, interview, and
   *advisory* choices; a script handles the mechanical, security-relevant steps.
2. **Mandatory controls cannot be bypassed** — not by the developer, not by the agent.
3. **Everything pinned + provenanced.** Version + digest for every artifact; a re-verifiable
   lockfile per workspace.
4. **Air-gap first.** Every mechanism must work offline (mirror/cache), because that is the
   banking/regulated use case, not an edge case.
5. **Ride the tool.** Use `agy plugin install`/marketplace, hook veto semantics, and
   `.agents/rules/` — do not reinvent what Antigravity already provides.
6. **DHC stays thin.** Content lives in the source repo(s); the DHC orchestrates and verifies.

## Scope × mode (hard design constraint, from the loader)

Antigravity loads customizations differently by run mode — this dictates *where* provisioning must write:

| Location | Interactive `agy` | Headless `agy -p` (CI, scripting, `/goal`) |
|---|---|---|
| `.agents/plugins/*/` (auto-discovery) | ✅ loads | ❌ **skipped** |
| `.agents/rules/*.md`, `.agents/skills/*`, `.agents/hooks.json` (direct) | ✅ | ✅ |
| `~/.gemini/config/*` (global rules/skills/mcp) | ✅ | ✅ |

Implication: **plugin-scoped provisioning is interactive-only; guardrails that must survive headless
runs belong in direct workspace scope or global scope.** The DHC exposes this as the **`DHC_FLATTEN`**
flag — default OFF (copy to `.agents/plugins/`, simplest, interactive); ON flattens into direct
`.agents/` scope (loads in both modes). Org-mandatory controls go **global** (§2.2). *`agy plugin install`
is NOT used for per-project provisioning — it installs to `~/.gemini/jetski/plugins/` (global, all
projects).*

---

## Phase 1 — Harden the foundation

Goal: make the existing single-source flow **deterministic, governed, verifiable, and generic**.

### 1.1 Deterministic provisioning core — ✅ DELIVERED
- **Problem:** promotion steps (`cp`, JSON merges, cache gitignore) hand-run by the LLM —
  non-auditable and drift-prone.
- **Delivered:** `agents/harness-configurator/dhc_provision.py` — a single CLI
  (`dhc_provision.py <selection.json>`) that does ALL mechanical promotion deterministically:
  preflight (fail before any write), reconcile (remove deselected via the receipt),
  skill materialization, default-copy vs flatten-distribute, plugin `scripts/` relocation to
  `.agents/scripts/<plugin>/` **+ hook-path rewrite (fixes the flatten hook bug)**, in-process
  hook/mcp merges, cache gitignore, and a deterministic `.agents/.dhc-provision.json` receipt
  (canonical JSON, no timestamps, `receiptHash`). `merge_config.py` (renamed, importable) gained
  dict cores + `unmerge_hooks`/`unmerge_mcp`. `verify-harness.py` parses the receipt (asserts
  createdPaths + hook/mcp presence + hook-script executability). `bootstrap.py` deploys the whole
  configurator dir. `agent.md` Phase 4 = author `selection.json` → one `dhc_provision.py` call
  (no agent-authored shell). 12 self-contained tests in `tests/test_dhc_provision.py`.
- **Done when (met):** identical selection → byte-identical receipt (verified, T4); no
  agent-authored shell in the mechanical path (agent authors only `selection.json` + rules/config).
- **Deferred to 1.5:** wiring the test module into GitHub Actions CI.

### 1.2 Governance rules as pinned artifacts (not improvised)
- **Problem:** rules are authored by LLM judgment — fine for conventions, unsafe for compliance.
- **Deliverable:** a versioned, reviewed `rules/` (governance) area in the source repo. The
  configurator **fetches and applies named, pinned rule sets** into `.agents/rules/`. Split
  rules into two classes: **governed** (pinned, reviewed, LLM may not author) and **advisory**
  (project conventions the LLM may draft).
- **Done when:** a compliance rule set applies deterministically from a pinned source; the LLM
  cannot originate a governed rule.

### 1.3 Efficacy-based verification
- **Problem:** `verify-harness.py` checks *presence* (plugin imported, rule file exists, script
  is executable), not *efficacy*. Antigravity's **documented** behavior has diverged from
  **runtime** twice, and presence-checks missed both:
  - **Hook CWD:** hooks execute from a working directory that is *not* the workspace root, so
    workspace-relative hook `command` paths fail (`exit 127`, "No such file") even though the
    script exists + is executable. (Fixed in 1.1 by writing **absolute** hook paths; the
    verifier should still *resolve every hook command from the runtime CWD*, not just stat it.)
  - **Workspace `agentMode` ignored:** a `.agents/settings.json` `{"agentMode":"plan"}` does
    **not** put sessions in plan mode — so SDD "enforcement" via that file was a no-op. Plan mode
    is only reliably set by the `--mode=plan` launch flag. (SDD is now the `sdd.md` rule + a
    `--mode=plan` launch recommendation, not a workspace setting.)
- **Principle:** *never assume a control works from docs — exercise it at runtime.* Presence ≠
  efficacy; resolvability ≠ the documented path; a written setting ≠ an applied setting.
- **Deliverable:** the verifier actively exercises controls — attempt a `curl` under a blocking
  posture and confirm it is blocked; resolve + dry-run each hook `command` from the real hook
  CWD; confirm each declared rule is actually loaded; confirm plan mode is active when SDD is on.
  Emit a hashable receipt.
- **Done when:** verification **fails** when a control is present but ineffective.

### 1.4 Generic discovery + metadata-driven plugin matching
- **Problem:** discovery is GCP/Python/Node-biased; plugin trigger matching is hardcoded in the
  agent prompt.
- **Deliverable:** broaden stack detection (Rust/Java/Kotlin/Ruby/PHP/.NET/C++/…; cloud-neutral,
  monorepo-aware). Each `plugin.json` declares its own `triggers` (file globs / content / stack);
  the configurator matches generically. "No match → baseline only" is a first-class outcome.
- **Done when:** adding a plugin requires no prompt edit; non-GCP stacks are recognized.

### 1.5 DHC self-tests / CI
- **Problem:** the flow is verified by hand.
- **Deliverable:** an automated end-to-end test (scratch install → provision → verify) in DHC CI,
  plus prompt-invariant checks.
- **Done when:** regressions are caught in CI, not in production.

---

## Phase 2 — Enterprise distributed harness management

Goal: manage harnesses across an org from **one company source of truth**, with **mandatory
global controls + team defaults + project opt-in**, pinned, signed, audited, and drift-enforced.

The model: a **Company Harness Repo** that mirrors the cabral-skills structure (`plugins/`,
`skills/`, governance `rules/`) but adds a **policy layer**, identity-driven resolution,
signing, enterprise distribution, controlled rollout, and audit — sitting on top of an
**MDM/endpoint enforcement substrate** (see 2.0) that makes the mandatory layer truly
non-bypassable.

```
   ┌──────────────────────────────────────────────────────────────────────┐
   │  MDM / endpoint mgmt + SSO   (below the developer's control)           │
   │  pins the source/registry · binds identity · ensures the DHC ran ·     │
   │  resists tampering · can block non-compliant sessions                  │
   └───────────────────────────────────┬──────────────────────────────────┘
                                        ▼
        Company Harness Repo (org source of truth)
        ├── plugins/            capability bundles (agy plugin install)
        ├── skills/             referenced by plugins + standalone
        ├── rules/              governed, reviewed rule sets (pinned)
        └── policy/org.yaml     mandatory-global · domain map · team map · allowed-optional
                                        │
                                        ▼   resolve for (identity, detected stack, project)
        global  (mandatory)   ── org security/compliance baseline · non-overridable
        team    (identity)    ── the team's required + default posture
        domain  (stack)       ── e.g. python / terraform · applied when the stack is detected
        project (opt-in)      ── additions from the allowed catalog only
                                        │
                    ▼  additive union · conflicts: global > team > domain > project · mandatory = locked
                                        ▼
        pinned + digest-verified install → workspace .agents/ + lockfile → fleet audit
```

### 2.0 Enforcement model & trust boundary (assumes MDM)
The DHC/harness enforces **in-session**: hook veto blocks disallowed tools, the mandatory
layer is applied, rules are loaded, the sandbox is available. That defends against **accidents
and casual bypass** — it does **not** make itself non-bypassable. A determined developer could
edit `.agents/`, point the installer at a personal source, run `agy` without the sandbox, disable
a hook, or skip the DHC entirely.

Making mandatory controls **truly non-bypassable** requires a layer **below the developer's
control** — assume an **MDM / endpoint-management + SSO** substrate (we do **not** build it):

| Concern | Harness can do (best-effort) | Requires MDM / device layer |
|---|---|---|
| Mandatory plugin/rule applied | load + hook-veto in session | prevent removal/tamper of `.agents/`; force re-provision |
| Source of truth | pin a tag in `install.sh` | pin the company registry at OS/config level; block personal sources |
| Identity → team (2.3) | ask / read env | bind SSO identity; developer cannot spoof team |
| DHC actually ran | n/a | ensure provisioning happened before coding; block un-provisioned sessions |
| Sandbox used | offer `agy --sandbox` | enforce sandbox/isolation at the endpoint |

**When it's needed:** regulated / high-assurance (banking, "the developer must not be able to
weaken controls"). **When honor-system is fine:** personal use and low-assurance teams — the
harness-level layer alone is adequate. Items **2.2 (mandatory), 2.3 (identity), 2.4 (tamper),
2.6 (drift enforcement)** are best-effort at the harness level and become *hard guarantees* only
with MDM; the roadmap calls this out per item.

### 2.1 Company harness repo + policy manifest
- **Deliverable:** one org repo (cabral-skills structure) plus `policy/org.yaml` declaring: the
  **global mandatory set**, **domain → bundle** mappings (technology-scoped, e.g. `python`,
  `terraform`), **team → bundle** mappings (identity-scoped), the **allowed optional catalog**,
  and pinned versions/digests for each.
- **Done when:** `(identity, detected stack, project)` resolves to a required + optional set from
  a single reviewed manifest.

### 2.2 Layered deterministic resolution (global > team > domain > project)
- **The four layers:**
  - **Global (mandatory):** org security/compliance baseline. Non-overridable — enforced via
    Antigravity's global-scope hook veto in-session, and *made hard* by MDM (2.0).
  - **Team (identity-driven):** the team's required + default posture (see 2.3).
  - **Domain (stack-triggered):** technology-scoped plugins that apply **whenever a stack is
    detected**, across teams — e.g. a `python` domain bundle (lint/type/test posture) or a
    `terraform` one. These are exactly the plugins whose `plugin.json` `triggers` match
    (Phase **1.4**); the domain layer is the org-governed subset of trigger-matched plugins.
  - **Project (opt-in):** additions the developer selects from the **allowed catalog only** —
    can add, never weaken higher layers.
- **Deliverable:** a resolver that computes the exact, pinned plugin + rule set as the **additive
  union** of applicable layers; on conflict, authority order **global > team > domain > project**
  decides, and any layer may mark an item **mandatory** (locked).
- **Done when:** given `(identity, stack, project)` the resolved set is reproducible; mandatory
  controls provably cannot be dropped by domain/project/agent choices (hard-guaranteed with MDM).

### 2.3 Identity-driven team resolution
- **Problem:** self-declared team selection lets a developer dodge team/mandatory controls.
- **Deliverable:** derive team (and thus the team + mandatory layer) from SSO / directory group
  membership, not from the interview. (Domain is derived from the detected stack; project from
  the allowed catalog — only *team* needs identity.)
- **Trust note (2.0):** identity binding is only trustworthy if the SSO/MDM layer supplies it;
  without that substrate this is advisory (a developer could still self-select).
- **Done when:** the applied team policy is a function of verified identity, not of what the user
  types.

### 2.4 Integrity, trust & pinning
- **Deliverable:** every artifact pinned to version **and** digest; signature/checksum verified
  **before** install; a per-workspace **lockfile** (resolved manifest with digests) that is
  re-verifiable at any time.
- **Done when:** tampered or unpinned artifacts are rejected; the lockfile proves exactly what
  was provisioned.

### 2.5 Enterprise distribution (private registry + air-gap mirror)
- **Deliverable:** publish the company repo as a **private marketplace**
  (`agy plugin install <name>@company`) and/or a **mirrored artifactory** for air-gapped sites;
  the DHC installer targets the company registry at a **pinned policy version**.
- **Done when:** provisioning works online (private marketplace) and offline (mirror), both
  pinned.

### 2.6 Controlled rollout & drift enforcement
- **Deliverable:** staged rollout of mandatory-version bumps (canary → fleet) with rollback;
  **drift detection** comparing a workspace's actual posture to its required policy, with alert
  and enforced re-provision.
- **Done when:** a mandatory bump can be rolled out safely, and stale/drifted/tampered
  workspaces are detected and remediated.

### 2.7 Audit & fleet reporting
- **Deliverable:** a per-provision receipt (who / what / when / versions / digests) plus central
  reporting of harness posture across teams and projects (a compliance view).
- **Done when:** you can answer "which projects run which harness version, and which are
  non-compliant?" from one place.

---

## Cross-cutting & non-goals

- **Cross-cutting:** least-privilege by default; air-gap parity for every feature; keep the DHC
  thin (content in the company repo); prefer native `agy` mechanisms over bespoke engines.
- **Non-goals (for now):** building the **MDM / endpoint-enforcement layer** — it is *assumed to
  exist* and we design to plug into it (see 2.0); building a custom policy engine if `agy`
  marketplace + hook veto suffice; replacing SSO/identity infrastructure; supporting
  non-Antigravity harness engines.

## Sequencing & dependencies

Phase 2 depends on Phase 1: enterprise distribution needs the **deterministic provisioning
core (1.1)** and **governed rules (1.2)** to be safe, and rollout/audit (2.6/2.7) build on the
**efficacy verification + receipts (1.3)**. Do Phase 1 first; it is also independently valuable
for single-user work.

| Phase | Theme | Turns the DHC into… |
|---|---|---|
| **1** | Deterministic · governed · verifiable · generic | a trustworthy single-source provisioner |
| **2** | Distributed · mandatory/team/project · signed · audited | an enterprise harness-management system |

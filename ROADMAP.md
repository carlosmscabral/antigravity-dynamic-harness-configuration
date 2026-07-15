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

---

## Phase 1 — Harden the foundation

Goal: make the existing single-source flow **deterministic, governed, verifiable, and generic**.

### 1.1 Deterministic provisioning core
- **Problem:** promotion steps (`cp`, `agy plugin install`, `enable`, cache gitignore) are
  hand-run by the LLM — non-auditable and drift-prone.
- **Deliverable:** a provisioning CLI (e.g. `dhc-provision <selection.json>`) that performs the
  mechanical work deterministically — reconcile (uninstall deselected), materialize skills,
  `agy plugin install` + `enable`, gitignore caches, emit a receipt. The configurator agent
  computes a *selection* (discovery + interview) and calls the CLI; it no longer improvises
  shell for security-relevant steps.
- **Done when:** identical selection → identical result + a provisioning receipt; no
  agent-authored shell in the mechanical path.

### 1.2 Governance rules as pinned artifacts (not improvised)
- **Problem:** rules are authored by LLM judgment — fine for conventions, unsafe for compliance.
- **Deliverable:** a versioned, reviewed `rules/` (governance) area in the source repo. The
  configurator **fetches and applies named, pinned rule sets** into `.agents/rules/`. Split
  rules into two classes: **governed** (pinned, reviewed, LLM may not author) and **advisory**
  (project conventions the LLM may draft).
- **Done when:** a compliance rule set applies deterministically from a pinned source; the LLM
  cannot originate a governed rule.

### 1.3 Efficacy-based verification
- **Problem:** `verify-harness.py` checks *presence* (plugin imported, rule file exists), not
  *efficacy*.
- **Deliverable:** the verifier actively exercises controls — e.g. attempt a `curl` under a
  blocking posture and confirm it is blocked; confirm each declared rule is actually loaded;
  confirm each selected plugin's components are registered (`agy plugin list`). Emit a hashable
  receipt.
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
signing, enterprise distribution, controlled rollout, and audit.

```
        Company Harness Repo (org source of truth)
        ├── plugins/            capability bundles (agy plugin install)
        ├── skills/             referenced by plugins + standalone
        ├── rules/              governed, reviewed rule sets (pinned)
        └── policy/org.yaml     mandatory-global · team→bundle map · allowed-optional catalog
                    │
                    ▼  (identity + policy) → deterministic resolution
   global (mandatory, non-overridable)  >  team (defaults)  >  project (opt-in)
                    │
                    ▼  pinned + digest-verified install
        workspace .agents/  +  lockfile (receipt)  →  fleet audit
```

### 2.1 Company harness repo + policy manifest
- **Deliverable:** one org repo (cabral-skills structure) plus `policy/org.yaml` declaring: the
  **global mandatory set**, **team → bundle** mappings, the **allowed optional catalog**, and
  pinned versions/digests for each.
- **Done when:** `(team, project)` resolves to a required + optional set from a single reviewed
  manifest.

### 2.2 Layered deterministic resolution (global > team > project)
- **Deliverable:** a resolver that computes the exact, pinned plugin + rule set for a workspace.
  **Global = mandatory and non-overridable** (enforced via Antigravity's global-scope hook veto
  — a mandatory blocker cannot be disabled by a project). **Team = defaults.** **Project =
  opt-in** from the allowed catalog only.
- **Done when:** mandatory controls provably cannot be dropped by project or agent choices.

### 2.3 Identity-driven team resolution
- **Problem:** self-declared team selection lets a developer dodge team/mandatory controls.
- **Deliverable:** derive team (and thus the team + mandatory layer) from SSO / directory group
  membership, not from the interview.
- **Done when:** the applied policy is a function of identity, not of what the user types.

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
- **Non-goals (for now):** building a custom policy engine if `agy` marketplace + hook veto
  suffice; replacing SSO/identity infrastructure; supporting non-Antigravity harness engines.

## Sequencing & dependencies

Phase 2 depends on Phase 1: enterprise distribution needs the **deterministic provisioning
core (1.1)** and **governed rules (1.2)** to be safe, and rollout/audit (2.6/2.7) build on the
**efficacy verification + receipts (1.3)**. Do Phase 1 first; it is also independently valuable
for single-user work.

| Phase | Theme | Turns the DHC into… |
|---|---|---|
| **1** | Deterministic · governed · verifiable · generic | a trustworthy single-source provisioner |
| **2** | Distributed · mandatory/team/project · signed · audited | an enterprise harness-management system |

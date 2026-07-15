# AGENTS.md — DHC maintainer guide

This file tells an AI agent (or a human) how to work on **this repository**. It is the
canonical contributor guide; `CLAUDE.md` is a symlink to it.

## What this repo is

The **Dynamic Harness Configurator (DHC)** is a *thin installer*. It contains only:

- `agents/harness-configurator/` — the configurator agent (`agent.md`) + `verify-harness.py`.
- `install.sh` — remote `curl | bash` installer.
- `bootstrap.py` — local/offline (developer) installer.
- `.agents/hooks.json`, `.agents/scripts/verify-readme.sh` — this repo's own governance.
- `concepts/`, `playbooks/`, `README.md`.

It contains **no skills and no plugins**. Those live in the
[cabral-skills](https://github.com/carlosmscabral/cabral-skills) monorepo, which is the single
source of truth. This repo *consumes* cabral-skills at a **pinned git tag**.

## The pin — the only coupling to cabral-skills

The pinned tag is declared **once**, at the top of `install.sh`:

```bash
CABRAL_SKILLS_REPO="carlosmscabral/cabral-skills"
CABRAL_SKILLS_TAG="v1.2.0"
```

- `install.sh` downloads `cabral-skills@$CABRAL_SKILLS_TAG` once, staging `plugins/` into
  `.agents/plugins_cache/` (dormant) and `skills/` into `.agents/skills_cache/` (the local,
  air-gap-safe source the configurator copies from at promotion time).
- `bootstrap.py` (dev mode) sources the same content from a sibling `../cabral-skills`
  checkout instead (override with `CABRAL_SKILLS_DEV_PATH`); it does not use the tag.
- The configurator's **Phase 4** authors `.agents/selection.json` (`mode`, `plugins`, `sdd`)
  then runs **one deterministic call**: `python3 .agents/agents/harness-configurator/dhc_provision.py .agents/selection.json`.
  That script (roadmap 1.1) does ALL mechanical work — reconcile, skill materialization,
  default-copy vs flatten-distribute, `scripts/` relocation + hook-path rewrite, hook/mcp
  merges, cache gitignore, and a deterministic `.agents/.dhc-provision.json` receipt. The
  `DHC_FLATTEN` flag (default OFF) only sets `mode` in the selection:
  - **default** → copy to `.agents/plugins/<name>/` (auto-discovered by *interactive* `agy`).
  - **flatten** → distribute into direct scope (`.agents/skills/`, `.agents/agents/`,
    `.agents/scripts/<name>/`, merged `.agents/hooks.json` / `.agents/mcp_config.json`) so the
    harness also loads under headless `agy -p`.
  The agent authors no `cp`/`rm`/merge shell; `merge_config.py` is used in-process by the script.
- **Scope × mode reality (from the loader):** interactive `agy` reads `.agents/plugins/*`;
  headless `agy -p` **skips the plugin tree** but reads direct scope (`.agents/rules/*.md`,
  `.agents/skills/*`, `.agents/hooks.json`) and global `~/.gemini/config/*`. So default mode is
  interactive-only; flatten mode (or global scope) is required for headless/CI/`/goal` guardrails.
- **Do not use `agy plugin install` for per-project provisioning** — it installs to
  `~/.gemini/jetski/plugins/` (**global, all projects**). Reserve it for org-mandatory globals.
- **Rules are not a plugin component.** Antigravity loads them from `.agents/rules/*.md`
  (both modes). The configurator **authors** workspace rules there as project policy.

## When to bump the pin

Bump `CABRAL_SKILLS_TAG` whenever you want this installer to deliver a newer release of the
upstream content, e.g. cabral-skills:

- added or changed a **skill** that a plugin references,
- added or changed a **plugin** (new hooks/agents/scripts/mcp, new `skills[]`),
- added a **new plugin** you want the configurator to offer.

You do **not** edit skills or plugins here — that all happens in cabral-skills. This repo only
changes when the **agent/installer logic** changes, or when the **pin** moves.

## How to bump the pin (procedure)

Ordering hazard: the upstream tag must exist **before** you point at it, or `install.sh` 404s.

1. Confirm the target tag exists upstream (`git ls-remote --tags` on cabral-skills, or open
   the release page).
2. Edit `CABRAL_SKILLS_TAG` in `install.sh`.
3. Test end-to-end (see below).
4. Update `README.md` if the change is user-visible (new plugin, changed flow). The
   `verify-readme.sh` guard blocks commits/pushes that touch `agents/`, `install.sh`, or
   `bootstrap.py` without also touching `README.md`.
5. Commit and push `main`. Because the public `curl | bash` target is `main/install.sh`, the
   new pin goes live immediately.

## Testing end-to-end

Run the installer into a throwaway workspace and exercise the flow:

```bash
SCRATCH=$(mktemp -d); cd "$SCRATCH"
bash /path/to/this-repo/install.sh            # or: curl | bash the raw main URL
ls .agents/plugins_cache   # expect the upstream plugins, no skills/ inside each
ls .agents/skills_cache    # expect the upstream skills
ls .agents/agents/harness-configurator/agent.md   # agent deployed (NOT nested under agents/agents/agents)
```

Then exercise a promotion and audit it:

- **Default mode** — materialize skills into the bundle and copy it into `.agents/plugins/`:
  ```bash
  echo '{"schemaVersion":1,"mode":"default","plugins":["standard-harness"],"sdd":false}' > .agents/selection.json
  python3 .agents/agents/harness-configurator/dhc_provision.py .agents/selection.json
  python3 .agents/agents/harness-configurator/verify-harness.py   # expect Mode: DEFAULT
  ```
  (Verify in an interactive `agy` session that a plugin skill/rule is active; `agy -p` will NOT see it.)
- **Flatten mode** — same call with `"mode":"flatten"`:
  ```bash
  echo '{"schemaVersion":1,"mode":"flatten","plugins":["standard-harness"],"sdd":false}' > .agents/selection.json
  python3 .agents/agents/harness-configurator/dhc_provision.py .agents/selection.json
  python3 .agents/agents/harness-configurator/verify-harness.py   # expect Mode: FLATTEN
  ```
  (Verify with `agy -p` that a flattened `.agents/rules/` rule fires — headless coverage is the point.)
- Unit tests: `python3 -m unittest tests.test_dhc_provision` (self-contained; no `agy` needed).
- Rules: confirm the configurator authored `.agents/rules/*.md` (these load in BOTH modes).
- Bad-pin sanity: a nonexistent `CABRAL_SKILLS_TAG` must make `install.sh` fail fast with a
  clear error and leave no partial `.agents/` caches.

## Relationship summary

```
cabral-skills (source of truth)        this repo (DHC, a consumer)
  skills/  plugins/  --- tag vX.Y.Z --->  install.sh: CABRAL_SKILLS_TAG=vX.Y.Z
                                          bootstrap.py: ../cabral-skills (dev)
                                          agent.md: promote (default: copy -> .agents/plugins/
                                                    | flatten: -> direct .agents/ scope)
                                                    + author .agents/rules/ (policy)
```

cabral-skills does not know this repo exists. It publishes tagged releases; we choose when to
adopt them. See cabral-skills `AGENTS.md` for the upstream authoring/release workflow.

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
- The configurator's **Phase 4** materializes each selected plugin's declared skills from
  `skills_cache/` into its bundle (local copy, air-gap safe), then registers it natively with
  `agy plugin install` + `agy plugin enable`. Antigravity composes the installed plugins'
  skills/agents/hooks/mcp — the configurator does **not** hand-merge those into `.agents/*.json`.
- **Rules are not a plugin component.** `agy plugin install` does not install rules; Antigravity
  loads them only from `.agents/rules/*.md`. The configurator **authors** workspace rules there
  as project policy (from its interview), separate from plugins.

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

- Materialize a plugin's skills into its cached bundle, then register it natively:
  ```bash
  # for each skill in .agents/plugins_cache/<name>/plugin.json "skills":
  cp -R .agents/skills_cache/<skill> .agents/plugins_cache/<name>/skills/<skill>
  agy plugin install .agents/plugins_cache/<name>
  agy plugin enable <name>
  agy plugin list        # expect <name> imported with its components
  python3 .agents/agents/harness-configurator/verify-harness.py   # expect FULLY COMPLIANT
  ```
- Rules: confirm the configurator authored `.agents/rules/*.md` (rules are NOT installed by
  `agy plugin install` — they must be authored into the workspace).
- Bad-pin sanity: a nonexistent `CABRAL_SKILLS_TAG` must make `install.sh` fail fast with a
  clear error and leave no partial `.agents/` caches.

## Relationship summary

```
cabral-skills (source of truth)        this repo (DHC, a consumer)
  skills/  plugins/  --- tag vX.Y.Z --->  install.sh: CABRAL_SKILLS_TAG=vX.Y.Z
                                          bootstrap.py: ../cabral-skills (dev)
                                          agent.md: materialize skills -> agy plugin install
                                                    + author .agents/rules/ (policy)
```

cabral-skills does not know this repo exists. It publishes tagged releases; we choose when to
adopt them. See cabral-skills `AGENTS.md` for the upstream authoring/release workflow.

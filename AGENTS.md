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
CABRAL_SKILLS_TAG="v1.0.0"
```

- `install.sh` downloads `cabral-skills@$CABRAL_SKILLS_TAG` once, staging `plugins/` into
  `.agents/plugins_cache/` (dormant) and `skills/` into `.agents/skills_cache/` (the local,
  air-gap-safe source the configurator copies from at promotion time).
- `bootstrap.py` (dev mode) sources the same content from a sibling `../cabral-skills`
  checkout instead (override with `CABRAL_SKILLS_DEV_PATH`); it does not use the tag.
- The configurator's **Phase 4** copies each promoted plugin's declared skills from
  `skills_cache/` into the active plugin — a pure local copy, never a network fetch (so it
  works under the air-gapped `strict-banking-harness` posture).

## When to bump the pin

Bump `CABRAL_SKILLS_TAG` whenever you want this installer to deliver a newer release of the
upstream content, e.g. cabral-skills:

- added or changed a **skill** that a plugin references,
- added or changed a **plugin** (new rules/hooks/agents/scripts, new `skills[]`),
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

Then simulate a promotion and audit it:

- Copy one plugin from `plugins_cache/` to `.agents/plugins/<name>/`, copy each skill named in
  its `plugin.json` `skills[]` from `skills_cache/` into `.agents/plugins/<name>/skills/`,
  assemble its `hooks.json` into `.agents/hooks.json`, then run
  `python3 .agents/agents/harness-configurator/verify-harness.py` — expect **FULLY COMPLIANT**.
- Air-gap sanity: `strict-banking-harness/scripts/command-blocker.sh` must block `curl`/`wget`
  while a local `cp` (the skill materialization) is allowed.
- Bad-pin sanity: a nonexistent `CABRAL_SKILLS_TAG` must make `install.sh` fail fast with a
  clear error and leave no partial `.agents/` caches.

## Relationship summary

```
cabral-skills (source of truth)        this repo (DHC, a consumer)
  skills/  plugins/  --- tag vX.Y.Z --->  install.sh: CABRAL_SKILLS_TAG=vX.Y.Z
                                          bootstrap.py: ../cabral-skills (dev)
                                          agent.md: materialize skills at promotion
```

cabral-skills does not know this repo exists. It publishes tagged releases; we choose when to
adopt them. See cabral-skills `AGENTS.md` for the upstream authoring/release workflow.

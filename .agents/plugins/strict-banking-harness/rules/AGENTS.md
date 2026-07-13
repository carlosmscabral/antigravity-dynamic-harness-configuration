# Strict Banking Compliance Rules

You are operating within a highly secure, regulated, and audited Banking environments. Absolute zero-trust compliance is non-negotiable.

## 1. Zero Network Access (Air-gapped Posture)
*   You are strictly forbidden from initiating or requesting external URL reads or writes (`read_url`, `execute_url` are blocked).
*   All libraries and dependencies must be retrieved exclusively from pre-audited, internal artifactories. Never request `pip install` or `npm install` on public mirrors.

## 2. Terminal Sandboxing Enforcements
*   You must assume every terminal execution is sandboxed using isolated gVisor/Docker nodes.
*   Do not attempt to execute administrative or system-level scripts natively. Only run low-privilege workspace actions.

## 3. Cryptographic and Secrets Protection
*   Never write, logging, or leak API keys, credit card numbers, SPIFFE keys, or PII into text files, terminal outputs, or thoughts.
*   All config variables must be read from `.env` template definitions.

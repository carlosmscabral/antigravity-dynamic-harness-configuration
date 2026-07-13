---
trigger: always_on
description: Standard styling rules and coding conventions
---
# Standard Harness Coding Conventions

All agents operating in this workspace must adhere to the following baseline development standards:

## 1. Documentation Integrity
*   Maintain docstrings for all functions, endpoints, and modules using standard docstring formats (Google style for Python, JSDoc for Node).
*   Preserve all existing docstrings and comments that are unrelated to your active modifications.

## 2. Testing Constraints (No Big Batches)
*   Never write or modify implementation code and test code in a single turn. Write or modify tests first, ensure the tests compile/fail correctly, and then implement/fix the code in a subsequent turn.
*   Enforce structured spec-first boundaries inside `/specs` using Gherkin syntax prior to coding.

## 3. Directory Conventions
*   Source files go into standard structure (`src/`, `lib/`, or main root depending on tech stack).
*   Test files go into `tests/` or alongside sources (`*.test.js`).

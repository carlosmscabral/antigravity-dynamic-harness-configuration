---
trigger: always_on
description: Strict Spec-First and Evaluation-Driven (EDD) testing rules
---
# Testing Conventions

*   Never write or modify implementation code and test code in a single turn. Write or modify tests first, ensure the tests compile/fail correctly, and then implement/fix the code in a subsequent turn.
*   Enforce structured spec-first boundaries inside `/specs` using Gherkin syntax prior to coding.
*   Source files go into standard structure (`src/`, `lib/`, or main root depending on tech stack).
*   Test files go into `tests/` or alongside sources (`*.test.js`).

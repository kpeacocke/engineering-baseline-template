---
name: pr-preflight
description: Author-side final readiness gate before opening, updating, or merging a pull request. Use when asked to prepare a PR, check whether a change is ready, preflight changes, clean up before commit, finish the work, or ship. Reviews the final diff against intent, detects scope creep and accidental files, runs repository-native validation, checks tests/docs/security/dependencies/migrations, confirms no debug or secret leakage, and produces a READY, READY WITH WARNINGS, or NOT READY decision with concrete evidence.
metadata:
  version: "1.0.0"
---

# PR Preflight

This is the last author-side gate. Do not turn it into another feature-development phase.

## Gate 1 — Intent versus diff

Read the request/issue and the complete diff. Confirm every changed file is necessary for the intended outcome. Identify unrelated refactors, formatting churn, generated artefacts, local configuration, debug output, temporary files, or accidental dependency changes.

Ask explicitly:

> What did we choose not to change?

If scope expanded, either justify it or remove it.

## Gate 2 — Correctness and regression protection

- Behavioural changes have meaningful tests where practical.
- Confirmed defects have regression protection where practical.
- New failure paths, boundaries, and negative cases are covered proportionately to risk.
- Existing valid tests were not weakened or removed without a contractual reason.

## Gate 3 — Repository-native checks

Run the project's relevant:

- targeted and broader tests;
- lint/format checks;
- type/static analysis;
- build/package validation;
- security/dependency checks;
- generated-file consistency checks.

Record command and outcome. "Not run" is not "passed".

## Gate 4 — Delivery and operations

Check as applicable:

- migrations and rollback;
- configuration/defaults;
- backwards compatibility;
- release notes/changelog;
- user/operator/API documentation;
- logging/metrics/errors;
- dependency/lock changes;
- secrets and credentials;
- required environment or infrastructure changes.

## Gate 5 — Final diff hygiene

Inspect the final diff after all fixes. Search for TODO/FIXME added by the change, debugging code, commented-out code, weakened assertions, blanket ignores, test skips, temporary feature flags, secrets, and oversized binary/generated content.

## Decision

- **READY** — no material blocker remains and verification is adequate.
- **READY WITH WARNINGS** — mergeable but explicit non-blocking follow-ups or environment gaps remain.
- **NOT READY** — known defect, required check failure, missing critical migration/security/compatibility work, or unverifiable high-risk change remains.

## Output contract

1. **Decision**.
2. **Scope check** — intended change versus actual diff.
3. **Verification evidence** — commands and results, including failures encountered on the way.
4. **Blocking issues** — or `None`.
5. **Warnings/follow-ups** — non-blocking only.
6. **PR summary** — concise What / Why / Verification / Risk text ready to paste into the PR.
7. **Most important thing you may be missing**.
8. **Three high-leverage things you did not ask for** — exactly three ranked next actions with an offer to execute them.

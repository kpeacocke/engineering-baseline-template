---
name: test-and-verify
description: Evidence-driven verification for code, configuration, automation, fixes, and implementation claims. Use when asked to test, verify, prove, validate, demonstrate that something works, reproduce a bug, confirm a fix, or keep iterating until checks pass. Establishes observable acceptance criteria, captures a baseline, builds the smallest useful reproducer or regression test, executes repository-native checks, records failures on the way, and refuses to substitute inspection for execution when execution is available.
metadata:
  version: "1.0.0"
---

# Test and Verify

The job is to prove or falsify a concrete claim about behaviour. A plausible implementation is not proof.

## Non-negotiable rules

1. Define what observable result would count as success before choosing tests.
2. Use repository-native commands and existing test infrastructure before inventing a parallel harness.
3. When execution is available, execute. Do not replace a runnable test with code inspection.
4. Capture the before state for defect fixes when practical.
5. Never hide failed attempts; failures that changed the investigation belong in the verification evidence.
6. Never weaken a valid test, assertion, linter, type check, or security control to get green.
7. Prefer the smallest high-signal test first, then broaden verification proportionately to risk.
8. Stop only when acceptance criteria are proven, disproven, or blocked by a concrete environmental limitation.

## Phase 1 — Turn the request into a verification contract

Identify:

- the claim being tested;
- observable success and failure states;
- input/state required to exercise the behaviour;
- important boundaries and negative paths;
- side effects that must or must not occur;
- compatibility, performance, security, or operability constraints that are part of "works".

If the request is vague, derive the narrowest defensible acceptance criteria from repository context and state any assumption.

## Phase 2 — Discover the native verification path

Read relevant CI workflows, package/build scripts, test configuration, contributing guidance, and nearby tests. Prefer commands already used by the repository.

Create a verification ladder from cheap to expensive, for example:

1. deterministic reproducer or targeted unit test;
2. affected module/package tests;
3. lint/type/static analysis;
4. build/package validation;
5. integration/e2e checks;
6. security/dependency checks;
7. broader suite.

## Phase 3 — Establish the before state

For a bug fix or behavioural correction, try to prove the defect before changing code:

- reproduce the failure;
- capture the failing test or command and exit status;
- verify that the failure is actually caused by the suspected path.

If a before-state reproduction is impossible, explain why and use the strongest alternative evidence available.

## Phase 4 — Execute and iterate

For each failed check:

1. classify it as introduced, pre-existing, environmental, flaky, or unresolved;
2. investigate root cause rather than patching the symptom;
3. make the smallest coherent correction when action is permitted;
4. rerun the targeted check;
5. repeat until it passes or the hypothesis is disproven.

Do not restart from a clean narrative after failures. The evidence trail matters.

## Phase 5 — Broaden proportionately

After the targeted check passes, run enough broader validation to catch collateral damage. Expand more aggressively when the change touches public interfaces, persistence, auth/authz, concurrency, migration, infrastructure, packaging, dependencies, or deployment.

## Phase 6 — Inspect the actual result

Tests can be wrong. Inspect produced files, output, state changes, API responses, logs, generated artefacts, or diffs where relevant. Confirm that the observed result matches the acceptance criteria rather than merely returning exit code 0.

## Mandatory blind-spot pass

Ask:

> What is the most important thing this verification could still be missing?

Then:

> What is the most plausible way this passes here but fails in production?

Investigate the strongest answer before finalising.

## Output contract

Report, in order:

1. **Verdict** — VERIFIED / PARTIALLY VERIFIED / NOT VERIFIED / BLOCKED.
2. **Acceptance criteria** — the observable claims tested.
3. **Evidence** — commands/probes actually run with result and exit status where available.
4. **Failures encountered** — material red states and what changed as a result.
5. **Changes made** — only when action mode changed files/configuration.
6. **Checks not run** — important omitted checks and why.
7. **Residual risk** — what remains unproven.
8. **Most important thing you may be missing** — one investigated blind spot or none found.
9. **Three high-leverage things you did not ask for** — exactly three concrete follow-ups, ranked, with one-sentence value and an offer to execute them.

Never use "all good" or equivalent when meaningful checks were not run.

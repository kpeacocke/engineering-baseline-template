---
name: debug-root-cause
description: Systematic root-cause debugging for failing tests, runtime errors, crashes, regressions, infrastructure failures, CI issues, automation failures, and intermittent behaviour. Use when asked to debug, troubleshoot, diagnose, investigate why something fails, or fix an unexplained problem. Reproduces the symptom, gathers discriminating evidence, maintains competing hypotheses, falsifies them, isolates the causal mechanism, applies the smallest fix, adds regression protection, and proves the fix rather than stopping at a plausible explanation.
metadata:
  version: "1.0.0"
---

# Debug Root Cause

Debugging is hypothesis testing, not a sequence of guesses.

## Rules

- Reproduce before changing things when practical.
- Preserve the original error, logs, inputs, versions, and environmental facts.
- Keep at least two plausible hypotheses until evidence collapses the space.
- Prefer tests that distinguish hypotheses over tests that merely gather more data.
- Change one causal variable at a time when isolating a fault.
- Do not call a workaround a root cause.
- Do not clear caches, reinstall everything, reboot, or reset state before preserving evidence unless safety requires it.
- If a full reset fixes the symptom, investigate what state the reset changed.

## Phase 1 — Define the symptom precisely

Capture:

- exact observed behaviour and expected behaviour;
- first known bad state and last known good state when known;
- frequency and determinism;
- environment, versions, inputs, timing, and topology;
- error text, exit status, logs, traces, dumps, or screenshots;
- what has already been tried and its result.

## Phase 2 — Reproduce with the smallest useful case

Reduce variables while preserving the failure. If it is intermittent, measure frequency and identify conditions correlated with failure.

Do not modify the production path until you can tell whether a proposed change affects the symptom.

## Phase 3 — Build a hypothesis table

For each plausible cause record:

- hypothesis;
- evidence for;
- evidence against;
- a discriminating test;
- current confidence.

Prioritise tests that can falsify multiple hypotheses cheaply.

## Phase 4 — Trace the causal path

Follow the failing state through inputs, boundaries, transformations, dependencies, state transitions, and side effects. Look especially for:

- stale state and caches;
- configuration precedence;
- version/API incompatibility;
- race/timing/order problems;
- warm-restart versus cold-start state;
- permission/identity differences;
- resource exhaustion;
- retries/timeouts;
- network/DNS/proxy/TLS boundaries;
- data shape/encoding/timezone/unit mismatches;
- hidden environmental assumptions.

## Phase 5 — Prove root cause

A root cause should explain:

1. why the symptom occurs;
2. why it occurs under these conditions;
3. why competing hypotheses do not fit as well;
4. why the proposed fix removes the causal mechanism.

Whenever practical, create a regression test or deterministic probe that fails before the fix.

## Phase 6 — Fix minimally and verify broadly

Apply the smallest correction that removes the cause without masking errors. Run the regression test, affected tests, and relevant broader validation. Verify the original symptom no longer occurs under the original triggering conditions.

## Mandatory blind-spot pass

Ask:

> What evidence would prove my current root-cause conclusion wrong?

Try to obtain it.

Then ask:

> What is the most important thing the investigation has not accounted for?

## Output contract

1. **Root-cause status** — PROVEN / STRONGLY SUPPORTED / UNRESOLVED / ENVIRONMENT BLOCKED.
2. **Symptom** — precise observed versus expected behaviour.
3. **Evidence timeline** — key observations and experiments, including failed attempts.
4. **Hypotheses tested** — accepted/rejected with evidence.
5. **Root cause** — causal mechanism, not just location of failure.
6. **Fix** — smallest corrective action when permitted.
7. **Verification** — commands/probes and observed results.
8. **Residual risk** — remaining uncertainty or recurrence conditions.
9. **Most important thing you may be missing**.
10. **Three high-leverage things you did not ask for** — exactly three ranked next actions with an offer to execute them.

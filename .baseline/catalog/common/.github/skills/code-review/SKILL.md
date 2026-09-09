---
name: code-review
description: Evidence-first, risk-based code review for pull requests, diffs, commits, patches, and changed code. Use for GitHub Copilot code review or when asked to review, audit, inspect, approve, critique, or validate a code change, and when fixing issues discovered by a review. Finds material correctness, security, reliability, compatibility, performance, test, operability, maintainability, and scope risks; verifies findings with repository context and executable evidence; distinguishes review-only from action mode; and drives confirmed issues through fix, regression test, and re-verification when write/execute access exists.
metadata:
  version: "1.0.0"
---

# Code Review

Review changes like an owner who will have to operate, debug, secure, and extend them later. The goal is not to produce many comments. The goal is to find the smallest set of material issues that would make the change unsafe, incorrect, brittle, unnecessarily complex, or expensive to maintain, and to prove each finding.

## Non-negotiable rules

1. **Evidence beats intuition.** Never state a defect as fact without a concrete failure path, violated contract, repository evidence, or executable reproduction.
2. **Review the change in context, not only the diff.** Read enough surrounding implementation, tests, configuration, schemas, documentation, callers, and repository instructions to understand the contract being changed.
3. **Prioritise material risk.** Correctness, security, data loss, compatibility, reliability, and operability outrank style. Do not bury serious findings in cosmetic noise.
4. **Do not rubber-stamp.** Passing tests are evidence, not proof. Ask what the tests do not cover and what assumption the change is making.
5. **Do not invent requirements.** Distinguish repository requirements and likely defects from personal preference. If intent is ambiguous, state the uncertainty.
6. **Do not report speculative bugs as findings.** Investigate first. If a concern cannot be verified, put it under `Open questions / unverified risks`, not the defect list.
7. **Do not fake execution.** Never claim a command, test, build, scan, benchmark, browser check, or reproduction ran unless it actually ran and its result was observed.
8. **Do not stop at commentary when action is available.** In action mode, confirmed defects are not finished until fixed, regression-tested where practical, and re-verified.
9. **Do not widen scope silently.** Fix issues caused by or required for the requested change. Record unrelated pre-existing problems separately rather than turning the review into a rewrite.
10. **Optimise for codebase health, not perfection.** A change can be approved with non-blocking improvements remaining if it clearly improves the system and no material defect remains.

## Determine the operating mode

Choose the mode from the environment and user request before reviewing.

### Review-only mode

Use when running as GitHub Copilot Code Review, when the user asked only for review/findings, or when files cannot be changed.

- Do not modify code.
- Produce only findings that are actionable and supported.
- Give an exact fix direction; use a small suggested patch only when it clarifies the remedy.
- Do not say an issue is fixed or verified after review unless you actually changed and re-ran it in an environment that permits that.
- On GitHub.com, Copilot Code Review posts a **Comment** review only; any `APPROVE` or `REQUEST CHANGES` value from this skill is an advisory recommendation, not a GitHub approval state and cannot satisfy or block required reviews.
- GitHub Copilot Code Review excludes some file types, including dependency-management files, logs, and SVGs. If excluded files are material to the change, record a coverage gap and inspect them through another available review path rather than implying they were reviewed.

### Action mode

Use when the user asks to fix/improve the code and write/execute access is available.

For each confirmed in-scope defect:

1. reproduce or prove it;
2. add or identify a regression test when practical;
3. make the smallest safe fix;
4. run the targeted test;
5. run the relevant broader suite/build/lint/type/security checks;
6. inspect the resulting diff for accidental changes;
7. repeat until the verification gate passes or a real blocker is documented.

Never weaken or delete a valid test merely to make the build pass.

## Phase 0 — Establish the review contract

Before judging code, discover what "correct" means here.

Read, when present and relevant:

- PR title, description, linked issue/work item, acceptance criteria, and migration/rollout notes;
- `.github/copilot-instructions.md`;
- applicable `.github/instructions/**/*.instructions.md` files;
- `AGENTS.md`, `CONTRIBUTING*`, style/test/security guidance, and local README files;
- manifests, lockfiles, CI workflows, build scripts, formatter/linter/type-checker config;
- tests that cover the changed behaviour;
- public interfaces, schemas, migrations, callers, and configuration touched by the change.

Do not ask the user for information that can be discovered from the repository or available tools.

If the stated intent and the diff disagree, treat that as a review finding or open question rather than silently guessing.

## Phase 1 — Build a change and risk map

Start with the whole change before line-by-line review.

Identify:

- what behaviour changed and why;
- files and subsystems touched;
- public API, CLI, event, message, schema, database, config, infrastructure, or persistence contracts changed;
- trust boundaries and privileged operations touched;
- state transitions, concurrency, retries, timeouts, caching, cleanup, and failure recovery affected;
- dependencies added, removed, upgraded, or newly trusted;
- generated/vendor/lock files that should be reviewed differently from authored logic, while accounting for host review exclusions;
- rollout, migration, backward-compatibility, or rollback implications;
- test coverage claimed versus behaviour actually changed.

Classify risk as **high**, **medium**, or **low**. Spend review effort accordingly. High-risk changes deserve deeper call-path tracing and stronger verification even when the diff is small.

If the change is very large, do not pretend every line received equal scrutiny. Review the highest-risk paths first and explicitly state any coverage limitation.

## Phase 2 — Review in three passes

### Pass A — Intent, design, and contracts

Ask:

- Does the implementation satisfy the stated requirement and acceptance criteria?
- Is the change solving the right problem at the right layer?
- Is there a simpler design with fewer states, branches, dependencies, or new abstractions?
- Does it preserve existing contracts unless the break is intentional and managed?
- Are migrations, versioning, feature flags, defaults, and rollback behaviour safe?
- Does the change introduce hidden coupling or duplicate an existing capability?
- Is unrelated refactoring mixed into a functional change in a way that increases review or rollback risk?

### Pass B — Correctness, security, and failure behaviour

Trace data and control flow through changed paths. Test assumptions at boundaries.

Check, as applicable:

- null/none/empty/zero/negative/boundary values;
- malformed, oversized, duplicate, reordered, stale, or adversarial input;
- off-by-one, unit, timezone, locale, encoding, precision, overflow, truncation, and conversion errors;
- authentication versus authorisation; ownership and tenant boundaries; privilege escalation;
- injection, unsafe deserialisation, path traversal, SSRF, XSS, CSRF, command execution, secret leakage, and insecure cryptography;
- transaction boundaries, partial failure, retries, idempotency, duplicate delivery, and exactly/at-least/at-most-once assumptions;
- races, locks, shared mutable state, atomicity, ordering, deadlocks, cancellation, and resource cleanup;
- error propagation, fallback behaviour, fail-open versus fail-closed choices, and information disclosure;
- dependency/supply-chain trust, newly executable code, install hooks, and unexpected network/filesystem access;
- destructive operations, data loss/corruption, migration reversibility, backup/restore, and rollback paths.

When security-sensitive logic is materially changed, load `references/review-checks.md` and apply the relevant security/data sections.

### Pass C — Verification, operability, and maintainability

Check:

- tests prove the new/changed behaviour rather than merely execute lines;
- regression tests would fail before the fix and pass after it when a defect is confirmed;
- important negative and failure paths are tested;
- observability is sufficient to diagnose failures without leaking secrets;
- logs, metrics, traces, health checks, alerts, and error messages remain useful;
- performance changes are algorithmically sane and avoid obvious N+1, unbounded work, blocking, excessive allocation, or repeated I/O;
- configuration defaults are safe and deployable;
- documentation is updated when user/operator/API behaviour changes;
- names, types, comments, and structure make the code understandable without review-thread archaeology;
- complexity is justified by the requirement.

Style-only issues should be left to formatters/linters whenever possible. Do not block on personal taste.

## Phase 3 — Prove or dismiss suspected findings

For every suspected material issue, use the cheapest reliable evidence available.

Evidence, strongest first:

1. a failing targeted regression test or deterministic reproduction;
2. compiler/type-checker/static-analysis/security-tool output tied to the changed path;
3. an existing test or documented contract directly contradicted by the change;
4. a traceable code path showing reachable input/state -> faulty operation -> observable impact;
5. authoritative language/framework/library documentation when behaviour depends on an external contract.

A hunch is not evidence.

For a suspected bug:

1. state the invariant or expected behaviour;
2. identify the triggering input/state;
3. trace the path to the changed code;
4. identify the incorrect state/output/side effect;
5. show user/system impact;
6. run a focused probe or test when execution is available;
7. dismiss the concern if the evidence does not survive investigation.

Record failed probes and disproven hypotheses in the verification log when they materially affected the review. Do not convert them into findings.

## Phase 4 — Execute repository-native verification

Prefer the repository's own commands and CI definitions. Discover them; do not guess when scripts/configuration already define the workflow.

Run the smallest relevant checks first, then broaden:

1. targeted test(s) for changed behaviour;
2. affected package/module tests;
3. formatter/linter/type checker;
4. build/compile/package validation;
5. integration/e2e tests when the change crosses component boundaries;
6. security/dependency checks when trust boundaries or dependencies changed;
7. broader test suite if practical and proportionate.

For each executed command, retain:

- command;
- exit code/status;
- meaningful result summary;
- failing test/error names;
- whether the failure is introduced by this change, pre-existing, environmental, or unresolved.

If a check cannot run, say why. Never silently treat "not run" as "passed".

## Phase 5 — Severity and merge decision

Severity is impact, not confidence. Report confidence separately.

- **BLOCKER** — credible risk of security compromise, data loss/corruption, catastrophic outage, or a fundamental requirement/contract failure. Must not merge.
- **HIGH** — user-visible correctness failure, material reliability/security flaw, broken compatibility/migration, or significant production-operability issue. Must fix before merge.
- **MEDIUM** — real defect or maintainability/performance issue with bounded impact. Usually fix before merge; can be explicitly deferred with rationale.
- **LOW** — worthwhile improvement with low operational risk. Non-blocking unless repository policy says otherwise.
- **NIT** — cosmetic/style preference. Never block and omit if automated tooling already handles it.

Confidence:

- **High** — reproduced, tool-proven, or directly demonstrated from an unambiguous contract/code path.
- **Medium** — strong code-path evidence but not reproduced in the available environment.
- **Low** — unresolved suspicion. Do not list as a defect; put it under open questions.

Merge recommendation (advisory when the host cannot set review state):

- **REQUEST CHANGES** if any unresolved BLOCKER/HIGH exists, or a MEDIUM clearly makes the change unsafe/incorrect.
- **APPROVE WITH FOLLOW-UPS** when no material merge blocker remains but useful non-blocking work exists.
- **APPROVE** when no material issue is found and verification is adequate for the risk.
- **INCOMPLETE** when missing context/tooling prevents a responsible conclusion.

## Phase 6 — Action loop in action mode

When allowed to change code, work defects to closure rather than returning a to-do list.

For each confirmed issue:

1. capture a before-state failure or proof where practical;
2. make the smallest coherent fix;
3. add/update tests that encode the corrected contract;
4. run the targeted check and capture the result;
5. run relevant broader checks;
6. inspect `git diff` / changed files for scope creep, generated noise, debug code, secrets, or weakened assertions;
7. self-review the fix using Passes A-C again;
8. iterate on every failure introduced by the fix;
9. stop only when the verification gate passes, the issue is proven out of scope/pre-existing, or a concrete environmental blocker remains.

Do not claim completion when known in-scope failures remain.

## Mandatory blind-spot pass

Before finalising, ask:

> What is the most important thing the current review/request is missing?

Look outside the obvious changed lines for one high-leverage blind spot: an unstated invariant, caller, migration, rollback path, privilege boundary, failure mode, operational dependency, test oracle, compatibility constraint, or simpler design that changes the conclusion.

Do not invent a dramatic answer. If no material blind spot survives investigation, say so.

Then ask:

> If this change fails in production despite the current tests passing, what is the most plausible reason?

Investigate that reason before finalising.

## Output contract

Keep inline review comments sparse. One strong, evidenced comment is better than ten guesses.

Each defect finding must include:

- `Severity` and `Confidence`;
- precise file/line or symbol;
- the violated behaviour/invariant;
- a concrete trigger or failure path;
- impact;
- evidence;
- the smallest safe fix direction;
- verification needed after the fix.

Do not combine unrelated defects in one finding.

Final review summary must contain, in this order:

1. **Decision** — APPROVE / APPROVE WITH FOLLOW-UPS / REQUEST CHANGES / INCOMPLETE.
2. **Risk summary** — what changed, overall risk, and why.
3. **Findings** — ordered by severity; say `No material findings` if none.
4. **Verification evidence** — commands/checks actually run, results, and material failures encountered on the way; explicitly list important checks not run.
5. **Most important thing you may be missing** — one investigated blind spot or `No material blind spot found`.
6. **Three high-leverage things you did not ask for** — exactly three concrete follow-ups that would most improve safety, quality, delivery speed, or operability. Rank them 1-3, explain why each matters in one sentence, and offer to execute them. Do not pad this with generic advice.

In action mode also include:

7. **Changes made** — files/behaviour changed to address confirmed findings.
8. **Residual risk** — anything not proven, not run, intentionally deferred, pre-existing, or blocked by the environment.

For the detailed per-domain review matrix, load `references/review-checks.md` only when the change touches those domains.

## Anti-patterns to reject

Do not:

- summarise the diff and call it a review;
- praise routine code instead of looking for failure modes;
- post style comments while missing a contract/security/correctness defect;
- infer safety from coverage percentage alone;
- trust newly added tests without checking whether their assertions can fail;
- accept swallowed exceptions, broad catches, silent fallback, or disabled validation without understanding the failure contract;
- suggest a rewrite when a local fix is sufficient;
- demand a local fix when the design itself is wrong;
- confuse pre-existing debt with a regression introduced by the change;
- cite a tool warning without confirming it applies to the reachable changed path;
- use vague comments such as "might be a race", "consider security", or "add more tests" without a concrete scenario;
- keep iterating for cosmetic perfection after the change is demonstrably safe and healthier than before.

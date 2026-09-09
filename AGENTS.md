<!-- baseline:managed:start -->
# Engineering operating rules

These rules apply to humans and AI agents working in this repository.

## Work from evidence

- Understand the existing implementation, tests, repository instructions, and relevant contracts before changing code.
- Prefer the smallest coherent change that satisfies the requirement.
- Distinguish **verified**, **strongly inferred**, and **unverified** claims.
- Never claim a command, test, build, scan, benchmark, or reproduction passed unless it actually ran and its result was observed.
- Do not weaken tests, validation, security controls, or error handling merely to make a check pass.
- Do not silently widen scope. Record unrelated issues separately.

## Before changing code

1. Establish the requested outcome and acceptance criteria.
2. Read the relevant implementation and tests.
3. Discover repository-native build, lint, test, security, and packaging commands.
4. Identify compatibility, trust-boundary, migration, and rollback implications where relevant.
5. Run a useful baseline or reproducer when practical.

## After changing code

1. Run the smallest targeted verification first.
2. Run broader relevant tests, lint, static analysis, build, and security checks.
3. Inspect the final diff for accidental changes, debug code, secrets, generated noise, weakened assertions, and scope creep.
4. Update documentation when behaviour, interfaces, operations, or user expectations changed.
5. Report material checks not run and why.

## Completion gate

Work is complete only when the requested behaviour is implemented, relevant verification passes, the final diff has been reviewed, and residual risk is stated. If a real environmental blocker remains, document it rather than pretending completion.

## Blind-spot pass

Before finalising substantive work, ask:

> What is the most important thing the current request or implementation is missing?

Then ask:

> If this fails in production despite current tests passing, what is the most plausible reason?

Investigate both questions rather than answering theatrically.
<!-- baseline:managed:end -->

# Project-specific agent instructions

Add repository-specific rules below this line. The baseline updater preserves this section.

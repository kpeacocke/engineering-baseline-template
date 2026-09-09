<!-- baseline:managed:start -->
# Copilot repository instructions

Follow [AGENTS.md](../AGENTS.md) as the repository operating contract.

Use path-specific instructions under `.github/instructions/` when they apply. Use repository skills under `.github/skills/` for task-specific methodology rather than recreating those workflows in chat.

Default behaviour:

- discover existing repository conventions before introducing new ones;
- minimise scope and complexity;
- preserve compatibility unless a breaking change is explicit and managed;
- test behavioural changes;
- execute relevant validation rather than relying on inspection alone;
- report evidence, failures encountered, checks not run, and residual risk;
- do not invent requirements or suppress valid failures.
<!-- baseline:managed:end -->

# Project-specific Copilot instructions

Add stack, architecture, naming, domain, and repository-specific rules below this line.

---
applyTo: "**/*.py,pyproject.toml,poetry.lock"
---

# Python instructions

- Use the Python version declared by the project and Poetry for dependency management.
- Prefer explicit types at public boundaries and for non-trivial data structures.
- Use Ruff for lint/format policy and pytest for tests.
- Keep functions focused; prefer clear data flow over clever abstraction.
- Do not catch `Exception` broadly unless the boundary deliberately converts/records all failures and preserves useful context.
- Preserve exception chaining when wrapping errors.
- Avoid shell execution when a direct Python/library/API call is available; never combine untrusted input with `shell=True`.
- Add regression tests for defects and useful negative/boundary tests for behavioural changes.

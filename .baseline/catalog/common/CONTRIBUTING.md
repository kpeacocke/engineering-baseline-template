# Contributing

## Before coding

- Read `AGENTS.md` and applicable repository instructions.
- Keep changes focused on one outcome.
- For non-trivial design choices, record an ADR under `docs/decisions/`.

## Before opening a pull request

Run:

```bash
python scripts/baseline.py doctor
```

Then run repository/profile-native tests and checks. In VS Code, `/preflight` runs the author-side readiness protocol.

Pull requests must state what changed, why, verification evidence, risk/rollout considerations, and what was intentionally left out of scope.

---
applyTo: "tests/**,**/test_*.py,**/*_test.py,**/*.spec.*,**/*.test.*"
---

# Test instructions

- Test behaviour and contracts, not implementation trivia.
- A regression test for a confirmed defect should fail before the fix and pass after it when practical.
- Include negative and boundary cases when they are material to the changed behaviour.
- Do not use weak assertions solely to increase coverage.
- Do not remove or skip a valid failing test without identifying why its contract is no longer valid.
- Keep tests deterministic; control time, randomness, network, and external state where possible.

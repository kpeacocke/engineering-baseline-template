---
name: implement
description: Implement a scoped change and prove it works rather than stopping at code generation. Use when implementing a requested bug fix or feature.
argument-hint: Describe exactly what should be implemented
user-invocable: true
---

# Implement

Implement the requested outcome.

Keep scope to the requested outcome. Use [test-and-verify](../test-and-verify/SKILL.md) as the completion protocol. If you encounter an unexplained failure, switch to the [debug-root-cause](../debug-root-cause/SKILL.md) method rather than guessing.

Do not stop at a plausible diff. Run relevant checks and inspect the final result.

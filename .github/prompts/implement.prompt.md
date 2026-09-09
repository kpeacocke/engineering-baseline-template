---
name: implement
description: Implement a scoped change and prove it works rather than stopping at code generation.
argument-hint: "Describe exactly what should be implemented"
agent: implementer
---

Implement: `${input:request}`

Keep scope to the requested outcome. Use [test-and-verify](../skills/test-and-verify/SKILL.md) as the completion protocol. If you encounter an unexplained failure, switch to the [debug-root-cause](../skills/debug-root-cause/SKILL.md) method rather than guessing.

Do not stop at a plausible diff. Run relevant checks and inspect the final result.

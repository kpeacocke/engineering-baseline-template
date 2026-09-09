---
name: debug
description: Reproduce and root-cause a failure, then apply and verify the smallest safe fix.
argument-hint: "Describe the failure or provide the error/symptom"
agent: implementer
---

Debug this problem: `${input:problem}`

Follow [debug-root-cause](../skills/debug-root-cause/SKILL.md) strictly. Preserve evidence, keep competing hypotheses, run discriminating tests, and do not call a reset/reinstall/workaround the root cause without explaining the state it changes.

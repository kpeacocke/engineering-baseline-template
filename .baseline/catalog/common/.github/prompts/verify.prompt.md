---
name: verify
description: Prove or falsify a concrete implementation or behaviour claim with executable evidence.
argument-hint: "What claim should be proven?"
agent: implementer
---

Verify this claim: `${input:claim}`

Apply [test-and-verify](../skills/test-and-verify/SKILL.md). Define observable acceptance criteria first, run the smallest high-signal check, broaden proportionately to risk, and report failed attempts and checks not run.

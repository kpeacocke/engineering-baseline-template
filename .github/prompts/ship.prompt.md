---
name: ship
description: Finish the smallest useful version already in progress; resist scope expansion, close verification gaps, and make it PR-ready.
argument-hint: "Describe what must be shipped now"
agent: implementer
---

Ship the smallest useful version of: `${input:outcome}`

Do not add adjacent features unless they are required for correctness or safe operation. Identify what is already sufficient, finish only the missing in-scope work, run [test-and-verify](../skills/test-and-verify/SKILL.md), then run [pr-preflight](../skills/pr-preflight/SKILL.md).

Explicitly list attractive follow-on ideas that were deferred so they do not leak into this change.

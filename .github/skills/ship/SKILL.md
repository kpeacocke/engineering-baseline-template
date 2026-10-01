---
name: ship
description: Finish the smallest useful version already in progress; resist scope expansion, close verification gaps, and make it pull-request ready. Use when completing work for delivery.
argument-hint: Describe what must be shipped now
user-invocable: true
---

# Ship

Ship the smallest useful version of the requested outcome.

Do not add adjacent features unless required for correctness or safe operation. Identify what is already sufficient, finish only the missing in-scope work, run [test-and-verify](../test-and-verify/SKILL.md), then run [pr-preflight](../pr-preflight/SKILL.md).

Explicitly list attractive follow-on ideas that were deferred so they do not leak into this change.

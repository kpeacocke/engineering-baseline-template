---
name: preflight
description: Run the final author-side readiness gate before opening or updating a PR.
argument-hint: "Optional PR/issue context"
agent: implementer
---

Prepare the current work for a pull request. Context: `${input:context}`

Apply [pr-preflight](../skills/pr-preflight/SKILL.md). Remove accidental scope, run repository-native checks, inspect the final diff, and return READY / READY WITH WARNINGS / NOT READY with evidence plus a concise PR summary.

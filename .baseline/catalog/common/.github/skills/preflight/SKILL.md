---
name: preflight
description: Run the final author-side readiness gate before opening or updating a pull request. Use when preparing, preflighting, or finishing a change for review.
argument-hint: Optional pull request or issue context
user-invocable: true
---

# Preflight

Prepare the current work for a pull request.

Apply [pr-preflight](../pr-preflight/SKILL.md). Remove accidental scope, run repository-native checks, inspect the final diff, and return READY / READY WITH WARNINGS / NOT READY with evidence plus a concise pull request summary.

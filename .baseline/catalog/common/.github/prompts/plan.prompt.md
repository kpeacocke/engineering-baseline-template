---
name: plan
description: Understand the repository and produce the smallest defensible implementation plan before editing.
argument-hint: "Describe the outcome, bug, feature, or decision to plan"
agent: architect
---

Plan this work without modifying the repository: `${input:request}`

First apply the repository discovery methodology in [repo-discovery](../skills/repo-discovery/SKILL.md). Challenge the requested approach if the repository evidence suggests a simpler or safer path.

The plan must define acceptance criteria, exact likely files/components, verification steps, risks, and what is intentionally out of scope. Finish with the smallest useful first implementation slice.

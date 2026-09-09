---
name: repo-discovery
description: Rapid, evidence-based acquisition of repository knowledge before implementation, debugging, architecture work, or review. Use when asked to understand, map, explore, onboard to, explain, or work in an unfamiliar repository, or before substantive changes when architecture and conventions are unclear. Maps purpose, architecture, runtime, entry points, data/control flow, build/test/CI, dependencies, trust boundaries, conventions, ownership, operational surfaces, and unknowns without modifying the repository.
metadata:
  version: "1.0.0"
---

# Repository Discovery

Build enough accurate context to act safely. Do not read the entire repository indiscriminately.

## Rules

- Start from manifests, README/architecture docs, repository instructions, CI, and top-level structure.
- Follow execution paths from entry points into important components.
- Distinguish documented architecture from architecture demonstrated by code.
- Prefer concrete file/symbol references over generic summaries.
- Do not modify files during discovery.
- Record uncertainty instead of filling gaps with convention-based guesses.

## Discovery sequence

### 1. Purpose and shape

Identify repository purpose, primary deliverables, supported users/operators, major directories, generated/vendor content, and whether it is an application, library, collection, infrastructure repo, monorepo, or mixed system.

### 2. Runtime and build

Map languages, runtime versions, package/dependency management, build/package commands, local developer setup, containers/devcontainers, and platform assumptions.

### 3. Entry points and architecture

Find primary entry points, public interfaces, major modules/services, dependency direction, state/persistence, external integrations, queues/events, and deployment boundaries.

### 4. Testing and CI

Identify test frameworks, test levels, fixtures/mocks, coverage policy, lint/type/static analysis, CI workflows, release pipeline, and checks required for merge.

### 5. Security and operations

Map authentication/authorisation, secret handling, trust boundaries, privileged operations, network exposure, configuration, migrations, logging/metrics, failure recovery, and rollback.

### 6. Conventions and governance

Read `AGENTS.md`, Copilot instructions, contributing guidance, CODEOWNERS, style/lint config, ADRs, issue/PR templates, and naming/structure conventions.

### 7. Risk map

Identify the components where a small change has high blast radius, areas with weak tests/ownership, deprecated or fragile dependencies, and important unknowns.

## Output contract

1. **Repository purpose**.
2. **Architecture map** — components and relationships.
3. **Runtime/build/dependencies**.
4. **Testing and CI**.
5. **Security/operations**.
6. **Conventions and governance**.
7. **High-risk areas**.
8. **Unknowns** — facts not established.
9. **Recommended first commands/files** for the requested next task.
10. **Most important thing you may be missing**.
11. **Three high-leverage things you did not ask for** — exactly three ranked next actions with an offer to execute them.

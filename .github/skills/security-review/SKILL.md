---
name: security-review
description: Threat-informed security review for code, configuration, infrastructure, workflows, authentication, APIs, dependencies, and automation changes. Use when asked for a security review, AppSec review, threat review, secure-code audit, secret/authentication/authorization review, or when a change materially crosses trust boundaries. Maps assets, actors, entry points, privileges and data flows; tests realistic abuse paths; checks common vulnerability classes and supply-chain risk; verifies findings with reachable evidence; and separates confirmed vulnerabilities from hardening suggestions.
metadata:
  version: "1.0.0"
---

# Security Review

Find realistic ways the system can violate confidentiality, integrity, availability, authorisation, provenance, or tenant boundaries. Do not generate a generic OWASP checklist and call it a review.

## Rules

- Threat-model the changed path before scanning for vulnerability names.
- Trace attacker-controlled data to security-sensitive sinks.
- Separate authentication from authorisation.
- Treat secrets, CI/CD, dependencies, package execution, and agent/tool permissions as supply-chain attack surfaces.
- A scanner warning is evidence to investigate, not automatically a vulnerability.
- A theoretical weakness without a reachable abuse path belongs under hardening/open risk, not confirmed findings.
- Never expose real secrets while proving a finding.

## Phase 1 — Security context

Identify:

- assets and sensitive data;
- actors, identities, roles, tenants, and privilege levels;
- entry points and attacker-controlled inputs;
- trust boundaries and network/process isolation;
- security controls relied upon;
- external dependencies and services;
- destructive or privileged operations;
- logging/audit expectations.

## Phase 2 — Abuse-path review

Check relevant paths for:

- broken object/tenant/function-level authorisation;
- injection and command execution;
- path traversal and unsafe file/archive handling;
- SSRF and untrusted outbound requests;
- unsafe deserialisation/parsing;
- XSS/CSRF/session/token handling where applicable;
- secret leakage in code, logs, errors, CI, artefacts, or generated output;
- insecure crypto/key/token generation or validation;
- race/replay/idempotency weaknesses around privileged state changes;
- fail-open validation and insecure fallback;
- excessive permissions, unsafe defaults, and privilege escalation;
- dependency confusion, typosquatting, unpinned executable dependencies, install hooks, mutable GitHub Actions tags, and compromised build inputs;
- unsafe AI/agent tool access, prompt-controlled tool arguments, or untrusted retrieved content when agentic systems are involved.

Load `references/security-checks.md` for a deeper matrix when the surface is broad.

## Phase 3 — Verify

For each suspected issue establish:

1. attacker preconditions;
2. controllable input/state;
3. reachable vulnerable operation;
4. missing or bypassed control;
5. security impact;
6. reproduction/static trace/tool evidence;
7. smallest safe remediation;
8. regression/security test required.

## Severity

Use impact and exploitability together. BLOCKER/HIGH findings require a credible path, not merely a dangerous API existing somewhere in the repo.

## Mandatory blind-spot pass

Ask:

> Which trust assumption would be most damaging if it is wrong?

Then investigate it.

Ask:

> What can an attacker influence indirectly through CI, dependencies, configuration, artefacts, plugins, or agents even if normal application inputs are validated?

## Output contract

1. **Security decision** — PASS / PASS WITH HARDENING / FAIL / INCOMPLETE.
2. **Threat context** — assets, actors, trust boundaries and exposed surface.
3. **Confirmed findings** — severity, confidence, path, impact, evidence and fix.
4. **Hardening opportunities** — clearly non-vulnerability improvements.
5. **Verification evidence** — scans/tests/traces actually performed.
6. **Coverage gaps** — material surfaces not inspected or tools unavailable.
7. **Most important thing you may be missing**.
8. **Three high-leverage things you did not ask for** — exactly three ranked next actions with an offer to execute them.

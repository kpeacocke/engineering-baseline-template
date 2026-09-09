# Security review matrix

Use only sections relevant to the changed attack surface.

## Identity and authorisation

- object, function, tenant and administrative boundaries
- default/anonymous identity behaviour
- token audience, issuer, expiry, replay, revocation and storage
- confused-deputy and service-to-service privilege
- privilege transitions and impersonation

## Input and execution

- SQL/NoSQL/LDAP/template/shell/code injection
- file paths, archives, uploads and symlinks
- URL parsing, redirects, DNS rebinding and SSRF
- deserialisation, parsers, regular expressions and resource exhaustion
- unsafe eval/dynamic import/plugin loading

## Data and secrets

- secret generation, storage, rotation and redaction
- encryption/key management and nonce/randomness requirements
- sensitive fields in logs, traces, errors, analytics, caches and artefacts
- data retention, deletion, backup and restore

## State and concurrency

- replay, duplicate delivery and idempotency
- TOCTOU, races and lock boundaries
- transaction/partial failure and rollback
- quota/rate-limit bypass

## Supply chain and CI/CD

- dependency provenance and unexpected new transitive trust
- mutable action/image/package references
- dangerous package lifecycle scripts
- build credentials and artifact provenance
- fork PRs, `pull_request_target`, workflow chaining and untrusted artefacts
- generated code, vendored code and lockfile changes

## Agentic systems

- prompt injection from retrieved/untrusted content
- tool allowlists and least privilege
- data exfiltration through tools/network
- untrusted tool output treated as instructions
- approval boundaries for destructive/high-impact actions
- provenance/attestation of models, prompts, tools and artefacts

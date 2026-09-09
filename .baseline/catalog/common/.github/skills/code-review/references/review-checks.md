# Domain review checks

Load only the sections relevant to the changed code. These checks are prompts for investigation, not a quota of comments.

## API and compatibility

- Request/response shape, status/error semantics, nullability, defaults, ordering, pagination and versioning.
- Backward/forward compatibility for clients, events, stored data and configuration.
- Validation at trust boundaries, including canonicalisation and size/rate limits.
- Idempotency and duplicate request behaviour.
- Retry safety and timeout/cancellation propagation.

## Authentication, authorisation and tenancy

- Authentication proves identity; authorisation separately proves permission for the specific object/action.
- Object ownership is enforced server-side, not inferred from client input.
- Tenant/org/project boundaries cannot be crossed by identifiers, filters, caches or background jobs.
- Admin/service paths apply least privilege and do not silently bypass policy.
- Deny paths fail closed and do not disclose existence of protected resources unnecessarily.

## Injection and untrusted input

- SQL/NoSQL queries use safe parameterisation or equivalent structured APIs.
- Shell/process execution does not concatenate untrusted values into command strings.
- File paths are normalised and constrained to intended roots.
- URLs/hosts used for server-side fetches are constrained against SSRF and redirect bypass.
- HTML/JS/template output uses context-appropriate escaping.
- Deserialisation does not instantiate arbitrary types or execute hooks from untrusted data.

## Secrets and cryptography

- No credentials, private keys, tokens, signing material or sensitive payloads enter source, logs, test fixtures or error responses.
- Randomness is cryptographically appropriate where security depends on unpredictability.
- Encryption/signature verification checks algorithms, key selection, expiry and failure behaviour.
- Certificate/TLS verification is not disabled.
- Secret comparison and token verification use established library primitives rather than custom crypto.

## Data and persistence

- Schema migrations are compatible with mixed application versions during rollout where required.
- Destructive changes have a safe sequencing/rollback strategy.
- Transactions cover all state that must change atomically.
- Partial failure cannot leave orphaned, duplicated or contradictory records.
- Uniqueness, foreign-key and business invariants are enforced at the correct layer.
- Read-modify-write operations account for concurrent writers.
- Retention/deletion behaviour covers replicas, caches, indexes and derived data if applicable.

## Concurrency and asynchronous work

- Shared state has an explicit ownership/synchronisation model.
- Cancellation and timeout paths release locks, connections, files and goroutines/tasks/threads.
- Queued work is idempotent where retries/redelivery are possible.
- Ordering assumptions are explicit and enforced.
- Check-then-act logic cannot race between validation and mutation.
- Background jobs preserve tenant/auth context safely or intentionally use service identity.

## Reliability and external dependencies

- Network calls have bounded timeouts and meaningful retry policy.
- Retryable versus permanent errors are distinguished.
- Retries use backoff/jitter where load amplification is possible.
- Circuit breaking/load shedding/bulkheads are considered for critical fan-out paths.
- Fallback behaviour does not return stale/unsafe/unauthorised data.
- Dependency outages degrade predictably and observably.

## Performance and resource use

- Complexity is reasonable for worst-case expected input, not only the happy path.
- No unbounded loops, recursion, collection growth, queues, caches or response buffering.
- Database access avoids avoidable N+1/query-per-item patterns.
- Repeated network/filesystem operations are not introduced in hot paths.
- Large payloads can stream/chunk when appropriate.
- Expensive work is not accidentally moved into request-critical or lock-held sections.

## Infrastructure, configuration and CI/CD

- Defaults are secure, deployable and backward compatible.
- Environment-specific values are not hardcoded.
- Permissions/RBAC/IAM are least-privilege and scoped to actual resources/actions.
- Network exposure, ingress/egress and firewall changes match intended trust boundaries.
- CI changes do not disable tests/scans, widen token permissions, expose secrets, execute untrusted PR code with privileged credentials, or use mutable/untrusted actions unexpectedly.
- Deployment changes include readiness/health semantics and rollback considerations.

## Dependencies and supply chain

- New dependency is necessary and maintained enough for the use case.
- Version/lock changes match the stated dependency change; no unexplained transitive churn.
- Install/build hooks and generated code are understood.
- Dependency provenance, signatures/checksums or repository policy are preserved where used.
- Upgrades account for breaking changes, deprecated APIs and changed defaults.

## Tests

- A test has an assertion that can fail for the behaviour it claims to prove.
- Negative, boundary and failure paths are covered where risk justifies them.
- Mocks/fakes do not bypass the exact integration contract being changed.
- Time, randomness and concurrency tests are deterministic enough to be useful.
- Tests do not merely duplicate implementation logic as their oracle.
- Regression test would fail on the buggy version and pass on the fixed version when practical to demonstrate.

## Observability and operations

- Errors preserve enough context to diagnose root cause without leaking secrets.
- Logs have useful identifiers/correlation context and appropriate levels.
- Metrics/alerts cover new critical failure modes where operationally necessary.
- Health checks reflect actual dependency/readiness requirements rather than only process liveness.
- Operators can tell the difference between retrying, degraded, failed and completed states.

## Maintainability

- Abstractions reduce rather than relocate complexity.
- Public names/types make invalid states difficult to express where practical.
- Comments explain why/constraints rather than restating code.
- Dead compatibility branches/TODOs created by the change have an exit condition or tracking path.
- New patterns fit the existing architecture unless there is a clear reason to change it.

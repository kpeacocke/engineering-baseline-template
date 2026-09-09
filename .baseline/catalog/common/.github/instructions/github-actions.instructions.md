---
applyTo: ".github/workflows/**,.github/actions/**"
---

# GitHub Actions instructions

- Declare the minimum required `permissions` explicitly.
- Pin third-party and GitHub-maintained actions to a full 40-character commit SHA and retain the release tag in a comment.
- Treat `pull_request_target`, `workflow_run`, write tokens, artifact execution, and fork-controlled input as high risk.
- Never interpolate untrusted event fields directly into shell scripts; pass them through environment variables and quote them.
- Prefer repository-native scripts over large inline shell blocks.
- Do not expose secrets to pull requests from forks.
- Keep CI deterministic and fail loudly when required checks cannot run.

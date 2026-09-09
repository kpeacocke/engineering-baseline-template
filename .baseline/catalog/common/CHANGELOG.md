# Changelog

## 0.2.0

- Hardened the project factory with manifest path-boundary enforcement, consistent optional GitHub API handling, and optimisation-proof self-tests.

- Add the project factory (`new`, `adopt`, `doctor`, `update`) so repository creation and governance are one supported workflow.
- Add conservative existing-repository adoption with local override tracking.
- Configure downstream baseline update source automatically.
- Audit/enable private vulnerability reporting for public repositories.
- Add CI smoke coverage for first template bootstrap and the project factory.
- Preserve adopted local overrides and exclude recovery/tmp data in scheduled and interactive baseline updates.

## 0.1.3

- Fix VS Code `files.eol` so it is a real newline value rather than the literal characters `\n`.
- Harden installer seeding so managed `.vscode` assets are committed even when the user has a global Git ignore for `.vscode/`.
- Render the golden template repository `CODEOWNERS` owner to the authenticated GitHub user before the first audit.

Significant user-visible changes should be recorded here or generated from release notes according to the project's release process.

# Development

## VS Code extensions

Install the extensions recommended by the workspace. All profiles recommend
[GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)
for chat, agent mode and inline suggestions. The separate `GitHub.copilot`
extension is deprecated; uninstall it if it is still installed.

## Baseline workflow updates

When updating an action in a managed workflow under `.github/workflows/`, update
the matching workflow under `.baseline/catalog/common/.github/workflows/` to the
same full commit SHA and release comment. Dependabot changes to the live workflow
alone leave catalogue drift, which blocks the `baseline` check.

Run `python scripts/project_factory.py local-doctor` to check consistency before
pushing the update.

## Project-specific setup

Document project-specific setup, local commands, environment assumptions, test strategy, and debugging notes here after bootstrap.

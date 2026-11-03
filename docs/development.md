# Development

## VS Code extensions

Install the extensions recommended by the workspace. All profiles recommend
[GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)
for chat, agent mode and inline suggestions. The separate `GitHub.copilot`
extension is deprecated; uninstall it if it is still installed.

## Baseline workflow updates

Dependabot scans both the live workflows and the common, Python and Ansible
catalogue workflow directories. Its `group-by: dependency-name` configuration
puts each action's version update into one PR across those directories, so the
installed and catalogue pins update together without an extra write-token workflow.

For manual action updates, change every occurrence in the live workflows and
catalogue to the same full commit SHA and release comment. Catalogue drift still
blocks the `baseline` check; CI does not repair or ignore it.

Run `python scripts/project_factory.py local-doctor` to check consistency before
pushing the update.

The golden template also runs `python -m unittest discover -s .baseline/tests -v`. These
regressions verify workflow consistency and current extension recommendations,
including the output of a fresh bootstrap for every profile.

## Project-specific setup

Document project-specific setup, local commands, environment assumptions, test strategy, and debugging notes here after bootstrap.

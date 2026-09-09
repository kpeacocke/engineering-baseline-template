# Engineering Baseline Project Factory

This repository is the golden GitHub + VS Code engineering baseline for `kpeacocke`.

**Do not manually create a repository from the template and then remember a list of setup commands.** Use the project factory; it creates or adopts the repository, selects the profile, applies GitHub governance/security settings, verifies the result, and leaves a normal project repository ready to work in.

## New project — one command

From a clone of this repository:

```powershell
.\baseline.ps1 new my-project --profile python --private
```

Or without the PowerShell wrapper:

```powershell
python .\scripts\project_factory.py new my-project --profile python --private
```

Profiles: `generic`, `python`, `ansible`. Omit `--private` for a public repository. For Ansible you may additionally provide `--ansible-namespace` and `--ansible-collection`.

`new` performs the complete lifecycle:

1. verifies the active `gh` identity;
2. creates the repository from `kpeacocke/engineering-baseline-template`;
3. clones it locally;
4. bootstraps the selected profile and renders project metadata/CODEOWNERS;
5. runs baseline `doctor`;
6. commits and pushes the bootstrap;
7. configures the central baseline update source;
8. applies repository, Actions, Dependabot, security and `main` ruleset policy;
9. audits the GitHub settings again without fix flags;
10. waits for GitHub Actions and fails if required validation is not green.

Success ends with `RESULT: PROJECT READY`.

## Adopt an existing repository

```powershell
.\baseline.ps1 adopt kpeacocke/attest --profile python
```

Adoption is deliberately conservative: existing project-specific managed files are preserved and recorded in `.baseline/state.json` as `local_overrides`; extensible files retain project text and receive the baseline-managed region. The command applies GitHub settings, opens an adoption PR, and waits for its checks. It does not merge by default.

## Verify a governed repository

```powershell
.\baseline.ps1 doctor kpeacocke/my-project
```

Inside a governed repository, the repository argument is optional:

```powershell
.\baseline.ps1 doctor
```

This verifies both the checked-in baseline and the GitHub-side settings, including the configured baseline update source.

## Update a governed repository

```powershell
.\baseline.ps1 update kpeacocke/my-project
```

`update` resolves the central template repository, takes its latest baseline snapshot, performs the transactional baseline upgrade, runs `doctor`, applies/audits GitHub policy, and opens a tested update PR. Project overrides are preserved.

## Direct low-level commands

The underlying tools remain available for diagnosis and CI:

```powershell
python .\scripts\baseline.py doctor
python .\scripts\github_reconcile.py --repo kpeacocke/my-project
python .\scripts\project_factory.py self-test
```

Use `baseline.py` / `github_reconcile.py` directly for troubleshooting or advanced workflows; normal project creation/adoption should go through `project_factory.py`.

## Repository policy

The personal-account default is PR-required with the `baseline` status check and resolved review conversations, but **0 mandatory human approvals** so a solo owner is not deadlocked. Merge commits and rebase merges are disabled at repository level; squash merge is the normal merge path. Actions default token permissions are read-only, Actions are SHA-pinned, Dependabot/security controls are enabled where supported, and public repositories enable private vulnerability reporting.

## Requirements

- Git
- GitHub CLI (`gh`) authenticated as the intended owner
- Python 3
- Python 3.14 is used by the generated Python/Ansible GitHub Actions profiles

Run `gh auth status` and `gh api user --jq .login` if identity is ever in doubt.

# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

This repository is governed by engineering baseline **{{BASELINE_VERSION}}** using the **{{PROFILE}}** profile.

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/{{OPENSSF_PROJECT_ID}}/badge)]({{OPENSSF_PROJECT}})

## Normal workflow

Verify the local baseline and GitHub settings:

```powershell
.\baseline.ps1 doctor
```

The source repository is recorded in `.baseline/state.json`; no separate GitHub repository variable is required.

Request an update from the central golden baseline:

```powershell
.\baseline.ps1 update
```

For local-only structural/drift diagnosis:

```powershell
python .\scripts\baseline.py doctor
```

In VS Code, use `/plan`, `/implement`, `/debug`, `/verify`, `/review`, `/preflight`, and `/ship`. Durable methodology lives in `.github/skills/`; repository-specific guidance can extend the managed instructions without replacing it.

## OpenSSF Best Practices

This factory includes the documentation and controls needed to prepare a project for the [OpenSSF Best Practices Badge](https://openssf.org/projects/best-practices-badge/). Use [docs/openssf-best-practices.md](docs/openssf-best-practices.md) to review the criteria, register the project at [bestpractices.dev](https://www.bestpractices.dev/), and record the resulting badge link after the project has been assessed.

## Repository-specific documentation

Add architecture, setup, operation and usage documentation under `docs/` as the project takes shape.

# {{PROJECT_NAME}}

{{PROJECT_DESCRIPTION}}

This repository is governed by engineering baseline **{{BASELINE_VERSION}}** using the **{{PROFILE}}** profile.

## Normal workflow

Verify the local baseline and GitHub settings:

```powershell
.\baseline.ps1 doctor
```

Request an update from the central golden baseline:

```powershell
.\baseline.ps1 update
```

For local-only structural/drift diagnosis:

```powershell
python .\scripts\baseline.py doctor
```

In VS Code, use `/plan`, `/implement`, `/debug`, `/verify`, `/review`, `/preflight`, and `/ship`. Durable methodology lives in `.github/skills/`; repository-specific guidance can extend the managed instructions without replacing it.

## Repository-specific documentation

Add architecture, setup, operation and usage documentation under `docs/` as the project takes shape.

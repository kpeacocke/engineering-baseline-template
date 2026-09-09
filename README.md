# Engineering Baseline GitHub Template

Template distribution for engineering-baseline **0.1.2**.

Create a repository from this GitHub template, then choose the project profile once:

```powershell
./scripts/bootstrap.ps1 -Profile generic -Name my-project -Owner my-github-user
./scripts/bootstrap.ps1 -Profile python -Name my-python-project -Owner my-github-user
./scripts/bootstrap.ps1 -Profile ansible -Name my-collection -Owner my-github-user -AnsibleNamespace my_namespace -AnsibleCollection my_collection
```

or:

```bash
./scripts/bootstrap.sh --profile python --name my-project --owner my-github-user
```

Bootstrap consumes template mode, renders the selected profile, and reseeds project-owned starter files such as this README. After bootstrap, profile switching is intentionally rejected.

Then run:

```bash
python scripts/baseline.py doctor
python scripts/github_reconcile.py
```

When authenticated GitHub CLI is available, apply low-risk repository settings with `--fix`. Security features and repository-level fallback rulesets require explicit `--fix-security` and `--fix-ruleset` flags; organisation-level policy is preferred where available.

In VS Code, the template provides custom agents, path-specific instructions, Agent Skills, slash-command prompt files, tasks, debug scaffolding, and recommended GitHub/Copilot tooling.

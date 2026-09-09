from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from .common import FactoryError, Runner, RUNNER, gh_json


def _api_unavailable(returncode: int, stdout: str, stderr: str) -> bool:
    if returncode == 0:
        return False
    text = f"{stdout}\n{stderr}".casefold()
    return any(token in text for token in ("404", "not found", "not implemented", "unsupported endpoint"))


def reconcile(repo: str, *, source_root: Path, runner: Runner = RUNNER, fix: bool) -> None:
    args = [sys.executable, str(source_root / "scripts/github_reconcile.py"), "--repo", repo]
    if fix:
        args += ["--fix", "--fix-security", "--fix-ruleset"]
    runner.run(args, cwd=source_root)


def enable_vulnerability_reporting(repo: str, *, runner: Runner = RUNNER) -> None:
    r = runner.run(["gh", "api", "--method", "PUT", f"repos/{repo}/private-vulnerability-reporting"], check=False)
    if r.returncode == 0:
        print("[PASS ] private vulnerability reporting enabled")
        return
    if _api_unavailable(r.returncode, r.stdout, r.stderr):
        print("[N/A  ] private vulnerability reporting unavailable")
        return
    raise FactoryError(f"could not enable private vulnerability reporting for {repo}: {r.stderr.strip() or r.stdout.strip()}")


def check_vulnerability_reporting(repo: str, *, runner: Runner = RUNNER) -> None:
    meta = gh_json(["repo", "view", repo, "--json", "visibility"], runner=runner)
    if str(meta.get("visibility", "")).casefold() == "private":
        print("[N/A  ] private vulnerability reporting is a public-repository control"); return
    r = runner.run(["gh", "api", f"repos/{repo}/private-vulnerability-reporting"], check=False)
    if r.returncode:
        if _api_unavailable(r.returncode, r.stdout, r.stderr):
            print("[N/A  ] private vulnerability reporting unavailable")
            return
        raise FactoryError(f"cannot inspect private vulnerability reporting for {repo}: {r.stderr.strip() or r.stdout.strip()}")
    try:
        body = json.loads(r.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise FactoryError("private vulnerability reporting endpoint returned invalid JSON") from exc
    if body.get("enabled") is not True:
        raise FactoryError(f"private vulnerability reporting is disabled for public repository {repo}")
    print("[PASS ] private vulnerability reporting enabled")


def set_source_variable(repo: str, template_repo: str, *, runner: Runner = RUNNER) -> None:
    r = runner.run(["gh", "variable", "set", "BASELINE_REPOSITORY", "--repo", repo, "--body", template_repo], check=False)
    if r.returncode:
        raise FactoryError(f"could not set BASELINE_REPOSITORY for {repo}: {r.stderr.strip()}")
    print(f"[PASS ] BASELINE_REPOSITORY={template_repo}")


def check_source_variable(repo: str, template_repo: str, *, runner: Runner = RUNNER) -> None:
    r = runner.run(["gh", "variable", "get", "BASELINE_REPOSITORY", "--repo", repo, "--json", "value", "--jq", ".value"], check=False)
    if r.returncode or r.stdout.strip() != template_repo:
        raise FactoryError(f"BASELINE_REPOSITORY drift for {repo}: current={r.stdout.strip()!r} desired={template_repo!r}")
    print(f"[PASS ] BASELINE_REPOSITORY={template_repo}")


def wait_commit(repo: str, commit: str, *, runner: Runner = RUNNER, timeout: int = 900, poll: int = 5) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r = runner.run(["gh", "run", "list", "--repo", repo, "--commit", commit, "--limit", "20", "--json", "databaseId,name,status,conclusion,url"], check=False)
        if r.returncode:
            raise FactoryError(f"cannot inspect Actions for {repo}: {r.stderr.strip()}")
        runs = json.loads(r.stdout or "[]")
        relevant = [x for x in runs if x.get("name") in {"Baseline conformance", "CI"}]
        failed = [x for x in relevant if x.get("status") == "completed" and x.get("conclusion") not in {"success", "skipped", "neutral"}]
        if failed:
            raise FactoryError("GitHub Actions failed: " + ", ".join(f"{x.get('name')}={x.get('conclusion')} {x.get('url')}" for x in failed))
        baseline_ok = any(x.get("name") == "Baseline conformance" and x.get("conclusion") == "success" for x in relevant)
        if relevant and baseline_ok and all(x.get("status") == "completed" for x in relevant):
            print("[PASS ] GitHub Actions: " + ", ".join(f"{x.get('name')}={x.get('conclusion')}" for x in relevant)); return
        time.sleep(poll)
    raise FactoryError(f"timed out waiting for Baseline conformance on {repo}@{commit}")


def wait_pr(pr_url: str, *, runner: Runner = RUNNER, timeout: int = 900) -> None:
    r = runner.run(["gh", "pr", "checks", pr_url, "--watch", "--fail-fast", "--interval", "10"], check=False, timeout=timeout)
    if r.returncode:
        raise FactoryError(f"pull-request checks failed:\n{r.stdout}\n{r.stderr}")
    print("[PASS ] pull-request checks")

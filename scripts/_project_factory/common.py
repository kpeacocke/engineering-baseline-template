from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TEMPLATE = "kpeacocke/engineering-baseline-template"
DEFAULT_BRANCH_PREFIX = "chore/engineering-baseline"


class FactoryError(RuntimeError):
    pass


class Result:
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


class Runner:
    def run(self, args: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None,
            stdin: str | None = None, check: bool = True, timeout: int | None = None) -> Result:
        p = subprocess.run(args, cwd=cwd, env=env, text=True, input=stdin, capture_output=True,
                           check=False, timeout=timeout)
        r = Result(p.returncode, p.stdout, p.stderr)
        if check and p.returncode:
            raise FactoryError(f"command failed ({p.returncode}): {' '.join(args)}\nstdout:\n{p.stdout}\nstderr:\n{p.stderr}")
        return r


RUNNER = Runner()


def require_tools() -> None:
    missing = [x for x in ("gh", "git") if shutil.which(x) is None]
    if missing:
        raise FactoryError(f"missing required tool(s): {', '.join(missing)}")


def validate_repo_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", name) or name in {".", ".."}:
        raise FactoryError(f"invalid repository name: {name!r}")
    return name


def split_repo(repo: str, default_owner: str | None = None) -> tuple[str, str]:
    if "/" in repo:
        owner, name = repo.split("/", 1)
    elif default_owner:
        owner, name = default_owner, repo
    else:
        raise FactoryError("repository must be owner/name")
    if not re.fullmatch(r"[A-Za-z0-9-]+", owner):
        raise FactoryError(f"invalid GitHub owner: {owner!r}")
    return owner, validate_repo_name(name)


def gh_json(args: list[str], *, runner: Runner = RUNNER) -> Any:
    r = runner.run(["gh", *args])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError as exc:
        raise FactoryError(f"GitHub CLI returned invalid JSON for {' '.join(args)}") from exc


def authenticated_login(*, runner: Runner = RUNNER) -> str:
    runner.run(["gh", "auth", "status"])
    login = runner.run(["gh", "api", "user", "--jq", ".login"]).stdout.strip()
    if not login:
        raise FactoryError("could not determine authenticated GitHub login")
    return login


def repo_exists(repo: str, *, runner: Runner = RUNNER) -> bool:
    return runner.run(["gh", "repo", "view", repo, "--json", "nameWithOwner"], check=False).returncode == 0


def current_repo(*, runner: Runner = RUNNER, cwd: Path | None = None) -> str:
    value = runner.run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
                       cwd=cwd or ROOT).stdout.strip()
    if not value:
        raise FactoryError("could not determine current GitHub repository")
    return value


def source_template_repository(*, runner: Runner = RUNNER) -> str:
    p = ROOT / ".baseline/state.json"
    if p.exists():
        value = json.loads(p.read_text(encoding="utf-8")).get("source_repository")
        if value:
            return str(value)
    try:
        return current_repo(runner=runner)
    except FactoryError:
        return DEFAULT_TEMPLATE


def state_values(target: Path) -> dict[str, Any]:
    p = target / ".baseline/state.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def clone_repo(repo: str, target: Path, *, runner: Runner = RUNNER) -> None:
    if target.exists() and any(target.iterdir()):
        raise FactoryError(f"target directory is not empty: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    runner.run(["gh", "repo", "clone", repo, str(target)])


def git_identity(owner: str, *, runner: Runner = RUNNER, cwd: Path) -> None:
    runner.run(["git", "config", "user.name", owner], cwd=cwd)
    runner.run(["git", "config", "user.email", f"{owner}@users.noreply.github.com"], cwd=cwd)


def default_branch(*, runner: Runner = RUNNER, cwd: Path) -> str:
    r = runner.run(["git", "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], cwd=cwd, check=False)
    if r.returncode == 0 and "/" in r.stdout.strip():
        return r.stdout.strip().split("/", 1)[1]
    return runner.run(["git", "branch", "--show-current"], cwd=cwd).stdout.strip() or "main"


def run_baseline(target: Path, args: list[str], *, runner: Runner = RUNNER, source_root: Path | None = None) -> Result:
    # Always execute the target repository's installed engine. Upgrade accepts
    # an explicit --source checkout; running the source checkout's script would
    # operate on the wrong repository because baseline.py intentionally roots
    # itself next to its own file.
    script = target / "scripts/baseline.py"
    if not script.exists():
        raise FactoryError(f"baseline script missing: {script}")
    return runner.run([sys.executable, str(script), *args], cwd=target, env=os.environ.copy())


def stage_known(target: Path, paths: list[str], *, runner: Runner = RUNNER) -> None:
    runner.run(["git", "add", "-u"], cwd=target)
    paths = sorted(set(p for p in paths if (target / p).exists()))
    for i in range(0, len(paths), 80):
        runner.run(["git", "add", "--force", "--", *paths[i:i+80]], cwd=target)


def commit_push(target: Path, message: str, *, runner: Runner = RUNNER, branch: str | None = None) -> str:
    if not runner.run(["git", "status", "--porcelain"], cwd=target).stdout.strip():
        return runner.run(["git", "rev-parse", "HEAD"], cwd=target).stdout.strip()
    git_identity(authenticated_login(runner=runner), runner=runner, cwd=target)
    runner.run(["git", "commit", "-m", message], cwd=target)
    runner.run(["git", "push", "-u", "origin", branch] if branch else ["git", "push", "origin", "HEAD"], cwd=target)
    return runner.run(["git", "rev-parse", "HEAD"], cwd=target).stdout.strip()


class SourceCheckout:
    def __init__(self, repo: str, *, runner: Runner = RUNNER) -> None:
        self.repo, self.runner, self.temp = repo, runner, None
    def __enter__(self) -> Path:
        try:
            here = current_repo(runner=self.runner, cwd=ROOT)
        except FactoryError:
            here = ""
        if here.casefold() == self.repo.casefold() and (ROOT / ".baseline/VERSION").exists():
            return ROOT
        self.temp = tempfile.TemporaryDirectory(prefix="engineering-baseline-source-")
        target = Path(self.temp.name) / "baseline"
        clone_repo(self.repo, target, runner=self.runner)
        return target
    def __exit__(self, *_: object) -> None:
        if self.temp:
            self.temp.cleanup()

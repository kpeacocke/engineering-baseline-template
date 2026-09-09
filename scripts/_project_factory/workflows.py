from __future__ import annotations

import argparse
import re
import shutil
import tempfile
from pathlib import Path

from .common import (DEFAULT_BRANCH_PREFIX, FactoryError, RUNNER, Runner, SourceCheckout,
                     authenticated_login, clone_repo, commit_push, current_repo, default_branch,
                     repo_exists, require_tools, run_baseline, source_template_repository, split_repo,
                     stage_known, state_values, validate_repo_name)
from .github_ops import (check_source_variable, check_vulnerability_reporting, enable_vulnerability_reporting,
                         reconcile, set_source_variable, wait_commit, wait_pr)
from .local import adopt, applicable_paths, local_doctor, preserve_overrides, restore_overrides, snapshot_paths


def govern(repo: str, template_repo: str, source_root: Path, *, runner: Runner, fix: bool) -> None:
    if fix:
        set_source_variable(repo, template_repo, runner=runner)
        enable_vulnerability_reporting(repo, runner=runner)
    reconcile(repo, source_root=source_root, runner=runner, fix=fix)
    check_source_variable(repo, template_repo, runner=runner)
    check_vulnerability_reporting(repo, runner=runner)


def create(args: argparse.Namespace, *, runner: Runner = RUNNER) -> int:
    require_tools(); login = authenticated_login(runner=runner); owner = args.owner or login
    if owner.casefold() != login.casefold() and not args.allow_other_owner:
        raise FactoryError(f"gh is authenticated as {login!r}; refusing owner {owner!r} without --allow-other-owner")
    name = validate_repo_name(args.name); repo = f"{owner}/{name}"
    if repo_exists(repo, runner=runner): raise FactoryError(f"repository already exists: {repo}")
    template = args.template or source_template_repository(runner=runner)
    target = Path(args.directory or name).resolve(); visibility = "--private" if args.private else "--public"
    print(f"[CREATE] {repo} from {template}")
    runner.run(["gh", "repo", "create", repo, "--template", template, visibility, "--description", args.description or f"{name} — engineering baseline project"])
    try:
        clone_repo(repo, target, runner=runner)
        b = ["bootstrap", "--profile", args.profile, "--name", name, "--owner", owner, "--owner-name", owner,
             "--codeowner", f"@{owner}", "--source-repository", template]
        if args.description: b += ["--description", args.description]
        if args.profile == "ansible":
            b += ["--ansible-namespace", args.ansible_namespace or re.sub(r"[^a-z0-9_]", "_", owner.lower()),
                  "--ansible-collection", args.ansible_collection or re.sub(r"[^a-z0-9_]+", "_", name.lower().replace("-", "_"))]
        run_baseline(target, b, runner=runner); local_doctor(target, runner=runner)
        stage_known(target, applicable_paths(target) + snapshot_paths(target), runner=runner)
        commit = commit_push(target, f"chore: bootstrap engineering baseline {args.profile}", runner=runner)
        with SourceCheckout(template, runner=runner) as source:
            govern(repo, template, source, runner=runner, fix=True)
        if not args.no_wait: wait_commit(repo, commit, runner=runner, timeout=args.timeout)
        print(f"RESULT: PROJECT READY — https://github.com/{repo}\nWORKTREE: {target}"); return 0
    except Exception:
        print(f"[INFO ] repository left intact for diagnosis: https://github.com/{repo}"); raise


def adopt_repo(args: argparse.Namespace, *, runner: Runner = RUNNER) -> int:
    require_tools(); login = authenticated_login(runner=runner); owner, name = split_repo(args.repo, login); repo=f"{owner}/{name}"
    if not repo_exists(repo, runner=runner): raise FactoryError(f"repository does not exist: {repo}")
    template = args.template or source_template_repository(runner=runner)
    temp = None; target = Path(args.directory).resolve() if args.directory else None
    if target is None:
        temp = tempfile.TemporaryDirectory(prefix="engineering-baseline-adopt-"); target = Path(temp.name)/name
    try:
        clone_repo(repo, target, runner=runner); base = default_branch(runner=runner, cwd=target)
        with SourceCheckout(template, runner=runner) as source:
            version=(source/".baseline/VERSION").read_text().strip(); branch=f"{DEFAULT_BRANCH_PREFIX}-{version}"
            runner.run(["git", "checkout", "-b", branch], cwd=target)
            overrides=adopt(source, target, profile=args.profile, owner=owner, name=name, source_repository=template)
            local_doctor(target, runner=runner); stage_known(target, applicable_paths(target)+snapshot_paths(target), runner=runner)
            commit_push(target, f"chore: adopt engineering baseline {version}", runner=runner, branch=branch)
            govern(repo, template, source, runner=runner, fix=True)
            body=("Adopt the engineering baseline conservatively. Existing conflicting managed files were preserved and recorded in "
                  f"`.baseline/state.json` `local_overrides` ({len(overrides)} override(s)).")
            url=runner.run(["gh","pr","create","--repo",repo,"--base",base,"--head",branch,"--title",f"chore: adopt engineering baseline {version}","--body",body]).stdout.strip().splitlines()[-1]
            if not args.no_wait: wait_pr(url, runner=runner, timeout=args.timeout)
            if args.merge:
                runner.run(["gh","pr","merge",url,"--squash","--delete-branch"]); print(f"RESULT: ADOPTED AND MERGED — {repo}")
            else: print(f"RESULT: ADOPTION PR READY — {url}")
            return 0
    finally:
        if temp: temp.cleanup()


def doctor(args: argparse.Namespace, *, runner: Runner = RUNNER) -> int:
    require_tools(); login=authenticated_login(runner=runner); repo_arg=args.repo or current_repo(runner=runner); owner,name=split_repo(repo_arg,login); repo=f"{owner}/{name}"
    if not repo_exists(repo, runner=runner): raise FactoryError(f"repository does not exist: {repo}")
    template=args.template or source_template_repository(runner=runner)
    with SourceCheckout(template, runner=runner) as source, tempfile.TemporaryDirectory(prefix="engineering-baseline-doctor-") as td:
        target=Path(td)/name; clone_repo(repo,target,runner=runner); local_doctor(target,runner=runner); govern(repo,template,source,runner=runner,fix=False)
    print(f"RESULT: HEALTHY — https://github.com/{repo}"); return 0


def update(args: argparse.Namespace, *, runner: Runner = RUNNER) -> int:
    require_tools(); login=authenticated_login(runner=runner); repo_arg=args.repo or current_repo(runner=runner); owner,name=split_repo(repo_arg,login); repo=f"{owner}/{name}"
    if not repo_exists(repo, runner=runner): raise FactoryError(f"repository does not exist: {repo}")
    template=args.template or source_template_repository(runner=runner)
    with SourceCheckout(template, runner=runner) as source, tempfile.TemporaryDirectory(prefix="engineering-baseline-update-") as td:
        version=(source/".baseline/VERSION").read_text().strip(); target=Path(td)/name; clone_repo(repo,target,runner=runner)
        st=state_values(target)
        if not st: raise FactoryError(f"{repo} has no installed baseline; use adopt")
        if str(st.get("installed_version")) == version:
            local_doctor(target,runner=runner); govern(repo,template,source,runner=runner,fix=False); print(f"RESULT: CURRENT — {repo} already uses baseline {version}"); return 0
        saved=preserve_overrides(target); base=default_branch(runner=runner,cwd=target); branch=f"{DEFAULT_BRANCH_PREFIX}-{version}"
        runner.run(["git","checkout","-b",branch],cwd=target)
        run_baseline(target,["upgrade","--source",str(source),"--fix"],runner=runner,source_root=source)
        restore_overrides(target,saved,template); local_doctor(target,runner=runner); stage_known(target,applicable_paths(target)+snapshot_paths(target),runner=runner)
        if not runner.run(["git","status","--porcelain"],cwd=target).stdout.strip(): print(f"RESULT: CURRENT — no changes required for {repo}"); return 0
        commit_push(target,f"chore: update engineering baseline to {version}",runner=runner,branch=branch); govern(repo,template,source,runner=runner,fix=True)
        url=runner.run(["gh","pr","create","--repo",repo,"--base",base,"--head",branch,"--title",f"chore: update engineering baseline to {version}","--body","Automated engineering-baseline update. Project overrides are preserved; review managed-file changes and CI before merging."]).stdout.strip().splitlines()[-1]
        if not args.no_wait: wait_pr(url,runner=runner,timeout=args.timeout)
        if args.merge: runner.run(["gh","pr","merge",url,"--squash","--delete-branch"]); print(f"RESULT: UPDATED AND MERGED — {repo}")
        else: print(f"RESULT: UPDATE PR READY — {url}")
        return 0

def apply_update_local(args: argparse.Namespace, *, runner: Runner = RUNNER) -> int:
    target = Path.cwd()
    source = Path(args.source).resolve()
    if not (source / ".baseline/VERSION").exists():
        raise FactoryError(f"not an engineering baseline checkout: {source}")
    st = state_values(target)
    if not st:
        raise FactoryError("current repository has no installed baseline")
    saved = preserve_overrides(target)
    source_repo = str(st.get("source_repository") or "")
    run_baseline(target, ["upgrade", "--source", str(source), "--fix"], runner=runner)
    restore_overrides(target, saved, source_repo)
    local_doctor(target, runner=runner)
    stage_known(target, applicable_paths(target) + snapshot_paths(target), runner=runner)
    print(f"RESULT: LOCAL UPDATE APPLIED — {(target / '.baseline/VERSION').read_text().strip()}")
    return 0

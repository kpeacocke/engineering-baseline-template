#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "repository.json"


class Result:
    def __init__(self, drift: int = 0, blocked: int = 0, fixed: int = 0) -> None:
        self.drift = drift
        self.blocked = blocked
        self.fixed = fixed

    @property
    def failed(self) -> bool:
        return self.drift > 0 or self.blocked > 0


def run_gh(args: list[str], *, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], cwd=ROOT, text=True, input=stdin, capture_output=True, check=False)


def repo_name(explicit: str | None) -> str:
    if explicit:
        return explicit
    p = run_gh(["repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"])
    if p.returncode != 0:
        raise RuntimeError(f"cannot resolve GitHub repository: {p.stderr.strip()}")
    return p.stdout.strip()


def desired_patch(config: dict[str, Any]) -> dict[str, Any]:
    return {**config["merge"], **config["features"]}


def api_json(args: list[str]) -> tuple[subprocess.CompletedProcess[str], Any | None]:
    proc = run_gh(["api", *args])
    if proc.returncode != 0:
        return proc, None
    if not proc.stdout.strip():
        return proc, None
    try:
        return proc, json.loads(proc.stdout)
    except json.JSONDecodeError:
        return proc, None


def has_http_status(proc: subprocess.CompletedProcess[str], status: int) -> bool:
    combined = f"{proc.stdout}\n{proc.stderr}".casefold()
    return str(status) in combined


def patch_repo(repo: str, payload: dict[str, Any]) -> subprocess.CompletedProcess[str]:
    return run_gh(["api", "--method", "PATCH", f"repos/{repo}", "--input", "-"], stdin=json.dumps(payload))


def put_endpoint(endpoint: str, payload: dict[str, Any] | None = None) -> subprocess.CompletedProcess[str]:
    args = ["api", "--method", "PUT", endpoint]
    if payload is not None:
        args += ["--input", "-"]
        return run_gh(args, stdin=json.dumps(payload))
    return run_gh(args)


def check_core_settings(repo: str, current: dict[str, Any], config: dict[str, Any], fix: bool) -> Result:
    result = Result()
    patch: dict[str, Any] = {}
    print("\n== Repository settings ==")
    for key, want in desired_patch(config).items():
        have = current.get(key)
        if have == want:
            print(f"[PASS ] {key}: {want!r}")
            continue
        print(f"[DRIFT] {key}: current={have!r} desired={want!r}")
        result.drift += 1
        patch[key] = want

    if fix and patch:
        proc = patch_repo(repo, patch)
        if proc.returncode == 0:
            result.fixed += len(patch)
            result.drift -= len(patch)
            print(f"[FIXED] repository settings: {len(patch)}")
        else:
            result.blocked += len(patch)
            print(f"[BLOCK] repository settings update failed: {proc.stderr.strip()}")
    return result


def check_actions_permissions(repo: str, config: dict[str, Any], fix: bool) -> Result:
    result = Result()
    print("\n== GitHub Actions permissions ==")

    policy_proc, policy = api_json([f"repos/{repo}/actions/permissions"])
    if policy_proc.returncode != 0 or not isinstance(policy, dict):
        print(f"[BLOCK] cannot read Actions repository policy: {policy_proc.stderr.strip()}")
        result.blocked += 1
    else:
        desired_policy = {
            "enabled": config["actions"].get("enabled", True),
            "allowed_actions": config["actions"].get("allowed_actions", "all"),
            "sha_pinning_required": config["actions"].get("sha_pinning_required", True),
        }
        mismatch = {key: value for key, value in desired_policy.items() if policy.get(key) != value}
        for key, want in desired_policy.items():
            have = policy.get(key)
            print(f"[{'PASS ' if have == want else 'DRIFT'}] {key}: current={have!r} desired={want!r}")
        result.drift += len(mismatch)
        if fix and mismatch:
            update = put_endpoint(f"repos/{repo}/actions/permissions", desired_policy)
            if update.returncode == 0:
                result.fixed += len(mismatch)
                result.drift -= len(mismatch)
                print("[FIXED] Actions repository policy / SHA pinning")
            else:
                result.blocked += len(mismatch)
                print(f"[BLOCK] Actions repository policy update failed: {update.stderr.strip()}")

    proc, current = api_json([f"repos/{repo}/actions/permissions/workflow"])
    if proc.returncode != 0 or not isinstance(current, dict):
        print(f"[BLOCK] cannot read Actions workflow permissions: {proc.stderr.strip()}")
        result.blocked += 1
        return result

    desired = {
        "default_workflow_permissions": config["actions"].get("default_workflow_permissions", "read"),
        "can_approve_pull_request_reviews": config["actions"].get("can_approve_pull_request_reviews", False),
    }
    mismatch = {key: value for key, value in desired.items() if current.get(key) != value}
    for key, want in desired.items():
        have = current.get(key)
        print(f"[{'PASS ' if have == want else 'DRIFT'}] {key}: current={have!r} desired={want!r}")
    result.drift += len(mismatch)

    if fix and mismatch:
        update = put_endpoint(f"repos/{repo}/actions/permissions/workflow", desired)
        if update.returncode == 0:
            result.fixed += len(mismatch)
            result.drift -= len(mismatch)
            print("[FIXED] Actions default workflow permissions")
        else:
            # A 409 commonly means an owning organisation/enterprise enforces the value.
            result.blocked += len(mismatch)
            print(f"[BLOCK] Actions permission update failed: {update.stderr.strip()}")
    return result


def check_labels(repo: str, config: dict[str, Any], fix: bool) -> Result:
    result = Result()
    desired_labels = config.get("labels", [])
    if not desired_labels:
        return result
    print("\n== Labels ==")
    proc, current = api_json([f"repos/{repo}/labels?per_page=100"])
    if proc.returncode != 0 or not isinstance(current, list):
        print(f"[BLOCK] cannot list labels: {proc.stderr.strip()}")
        result.blocked += 1
        return result
    by_name = {item.get("name"): item for item in current if isinstance(item, dict)}

    for desired in desired_labels:
        name = desired["name"]
        have = by_name.get(name)
        if have is not None:
            print(f"[PASS ] label: {name}")
            continue
        print(f"[DRIFT] missing label: {name}")
        result.drift += 1
        if fix:
            create = run_gh(
                ["api", "--method", "POST", f"repos/{repo}/labels", "--input", "-"],
                stdin=json.dumps(desired),
            )
            if create.returncode == 0:
                result.fixed += 1
                result.drift -= 1
                print(f"[FIXED] label: {name}")
            else:
                result.blocked += 1
                print(f"[BLOCK] could not create label {name}: {create.stderr.strip()}")
    return result


def check_dependabot(repo: str, fix: bool) -> Result:
    result = Result()
    print("\n== Dependency security ==")

    alerts = run_gh(["api", f"repos/{repo}/vulnerability-alerts"])
    alerts_enabled = alerts.returncode == 0
    if alerts_enabled:
        print("[PASS ] Dependabot alerts / dependency graph enabled")
    elif has_http_status(alerts, 404):
        print("[DRIFT] Dependabot alerts / dependency graph disabled")
        result.drift += 1
        if fix:
            enable = put_endpoint(f"repos/{repo}/vulnerability-alerts")
            if enable.returncode == 0:
                result.fixed += 1
                result.drift -= 1
                print("[FIXED] Dependabot alerts / dependency graph enabled")
            else:
                result.blocked += 1
                print(f"[BLOCK] could not enable vulnerability alerts: {enable.stderr.strip()}")
    else:
        result.blocked += 1
        print(f"[BLOCK] cannot determine vulnerability-alert status: {alerts.stderr.strip()}")

    updates, body = api_json([f"repos/{repo}/automated-security-fixes"])
    enabled = isinstance(body, dict) and body.get("enabled") is True and body.get("paused") is not True
    if updates.returncode == 0 and enabled:
        print("[PASS ] Dependabot security updates enabled")
    elif updates.returncode == 0 or has_http_status(updates, 404):
        print("[DRIFT] Dependabot security updates disabled or paused")
        result.drift += 1
        if fix:
            enable = put_endpoint(f"repos/{repo}/automated-security-fixes")
            if enable.returncode == 0:
                result.fixed += 1
                result.drift -= 1
                print("[FIXED] Dependabot security updates enabled")
            else:
                result.blocked += 1
                print(f"[BLOCK] could not enable Dependabot security updates: {enable.stderr.strip()}")
    else:
        result.blocked += 1
        print(f"[BLOCK] cannot determine Dependabot security-update status: {updates.stderr.strip()}")
    return result


def check_security_features(repo: str, current: dict[str, Any], fix_security: bool) -> Result:
    """Audit plan-dependent controls; only change them with explicit --fix-security."""
    result = Result()
    print("\n== Security features ==")
    security = current.get("security_and_analysis") or {}
    desired_fields = ["secret_scanning", "secret_scanning_push_protection"]
    patch: dict[str, Any] = {}

    for field in desired_fields:
        info = security.get(field)
        if info is None:
            print(f"[N/A  ] {field}: not exposed/supported for this repository or token")
            continue
        status = info.get("status") if isinstance(info, dict) else None
        if status == "enabled":
            print(f"[PASS ] {field}: enabled")
        else:
            print(f"[DRIFT] {field}: {status!r}; desired='enabled'")
            result.drift += 1
            patch[field] = {"status": "enabled"}

    if fix_security and patch:
        proc = patch_repo(repo, {"security_and_analysis": patch})
        if proc.returncode == 0:
            result.fixed += len(patch)
            result.drift -= len(patch)
            print(f"[FIXED] security_and_analysis: {', '.join(sorted(patch))}")
        else:
            result.blocked += len(patch)
            print(f"[BLOCK] security feature update failed: {proc.stderr.strip()}")

    codeql, body = api_json([f"repos/{repo}/code-scanning/default-setup"])
    if codeql.returncode == 0 and isinstance(body, dict):
        state = body.get("state")
        if state == "configured":
            print("[PASS ] CodeQL default setup configured")
        else:
            print(f"[DRIFT] CodeQL default setup state={state!r}")
            result.drift += 1
            if fix_security:
                update = run_gh(
                    ["api", "--method", "PATCH", f"repos/{repo}/code-scanning/default-setup", "--input", "-"],
                    stdin=json.dumps({"state": "configured"}),
                )
                if update.returncode == 0:
                    result.fixed += 1
                    result.drift -= 1
                    print("[FIXED] CodeQL default setup configured")
                else:
                    result.blocked += 1
                    print(f"[BLOCK] CodeQL default setup update failed: {update.stderr.strip()}")
    elif has_http_status(codeql, 403) or has_http_status(codeql, 404):
        print("[N/A  ] CodeQL default setup unavailable/not eligible; prefer organisation code-security configuration where supported")
    else:
        result.blocked += 1
        print(f"[BLOCK] cannot determine CodeQL default setup: {codeql.stderr.strip()}")

    if patch and not fix_security:
        print("[INFO ] rerun with --fix-security to enable supported secret scanning / push protection controls")
    return result


def effective_branch_governance(rules: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    by_type = {str(rule.get("type")): rule for rule in rules if isinstance(rule, dict)}
    gaps: list[str] = []

    if "deletion" not in by_type:
        gaps.append("block branch deletion")
    if "non_fast_forward" not in by_type:
        gaps.append("block force pushes")

    desired = json.loads((ROOT / "config" / "main-ruleset.example.json").read_text(encoding="utf-8"))
    desired_pr = next((r for r in desired.get("rules", []) if r.get("type") == "pull_request"), None)
    desired_params = desired_pr.get("parameters", {}) if isinstance(desired_pr, dict) else {}

    pr_rule = by_type.get("pull_request")
    if pr_rule is None:
        gaps.append("require pull requests")
    else:
        params = pr_rule.get("parameters") if isinstance(pr_rule.get("parameters"), dict) else {}
        required_approvals = int(desired_params.get("required_approving_review_count") or 0)
        actual_approvals = int(params.get("required_approving_review_count") or 0)
        if actual_approvals < required_approvals:
            gaps.append(f"require at least {required_approvals} approving review(s)")
        if desired_params.get("dismiss_stale_reviews_on_push") is True and params.get("dismiss_stale_reviews_on_push") is not True:
            gaps.append("dismiss stale approvals after new pushes")
        if desired_params.get("required_review_thread_resolution") is True and params.get("required_review_thread_resolution") is not True:
            gaps.append("require review-thread resolution")

    desired_checks = next((r for r in desired.get("rules", []) if r.get("type") == "required_status_checks"), None)
    if isinstance(desired_checks, dict):
        actual_checks = by_type.get("required_status_checks")
        if actual_checks is None:
            gaps.append("require baseline status check")
        else:
            wanted = {item.get("context") for item in desired_checks.get("parameters", {}).get("required_status_checks", []) if isinstance(item, dict)}
            actual = {item.get("context") for item in actual_checks.get("parameters", {}).get("required_status_checks", []) if isinstance(item, dict)}
            missing = sorted(str(item) for item in wanted - actual if item)
            for context in missing:
                gaps.append(f"require status check: {context}")

    return not gaps, gaps


def apply_repository_ruleset(repo: str) -> subprocess.CompletedProcess[str]:
    desired = json.loads((ROOT / "config" / "main-ruleset.example.json").read_text(encoding="utf-8"))
    listed, rulesets = api_json([f"repos/{repo}/rulesets?includes_parents=false&targets=branch"])
    if listed.returncode == 0 and isinstance(rulesets, list):
        existing = next(
            (
                item
                for item in rulesets
                if isinstance(item, dict)
                and item.get("name") == desired.get("name")
                and str(item.get("source_type", "")).casefold() == "repository"
            ),
            None,
        )
        if existing is not None and existing.get("id") is not None:
            return run_gh(
                ["api", "--method", "PUT", f"repos/{repo}/rulesets/{existing['id']}", "--input", "-"],
                stdin=json.dumps(desired),
            )
    return run_gh(
        ["api", "--method", "POST", f"repos/{repo}/rulesets", "--input", "-"],
        stdin=json.dumps(desired),
    )


def check_rulesets(repo: str, current: dict[str, Any], fix_ruleset: bool) -> Result:
    result = Result()
    print("\n== Branch governance ==")
    branch = str(current.get("default_branch") or "main")
    proc, rules = api_json([f"repos/{repo}/rules/branches/{branch}"])
    if proc.returncode != 0 or not isinstance(rules, list):
        print(f"[BLOCK] cannot inspect effective rules for {branch}: {proc.stderr.strip()}")
        result.blocked += 1
        return result

    compliant, gaps = effective_branch_governance(rules)
    if compliant:
        sources = sorted(
            {
                f"{rule.get('ruleset_source_type', 'unknown')}:{rule.get('ruleset_source', 'unknown')}"
                for rule in rules
                if isinstance(rule, dict) and rule.get("type") in {"deletion", "non_fast_forward", "pull_request"}
            }
        )
        source_text = ", ".join(sources) if sources else "effective branch rules"
        print(f"[PASS ] {branch}: protected by {source_text}")
        return result

    result.drift += 1
    print(f"[DRIFT] {branch}: governance gaps")
    for gap in gaps:
        print(f"        - {gap}")

    if fix_ruleset:
        updated = apply_repository_ruleset(repo)
        if updated.returncode == 0:
            result.fixed += 1
            result.drift -= 1
            print("[FIXED] repository fallback ruleset applied from config/main-ruleset.example.json")
        else:
            result.blocked += 1
            print(f"[BLOCK] repository ruleset update failed: {updated.stderr.strip()}")
    else:
        print("[INFO ] prefer an organisation ruleset; use --fix-ruleset only for a repository-level fallback")
    return result

def check_codeowners(repo: str) -> Result:
    result = Result()
    print("\n== CODEOWNERS ==")
    proc, body = api_json([f"repos/{repo}/codeowners/errors"])
    if proc.returncode == 0 and isinstance(body, dict):
        errors = body.get("errors") or []
        if errors:
            result.drift += len(errors)
            print(f"[DRIFT] CODEOWNERS has {len(errors)} syntax error(s)")
            for error in errors[:10]:
                if isinstance(error, dict):
                    print(f"        line {error.get('line', '?')}: {error.get('message', error)}")
        else:
            print("[PASS ] CODEOWNERS syntax")
    elif has_http_status(proc, 404):
        print("[INFO ] CODEOWNERS API unavailable until the file/default branch is visible on GitHub")
    else:
        print(f"[INFO ] cannot inspect CODEOWNERS syntax: {proc.stderr.strip()}")
    return result


def merge_results(*results: Result) -> Result:
    total = Result()
    for item in results:
        total.drift += item.drift
        total.blocked += item.blocked
        total.fixed += item.fixed
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit/reconcile GitHub repository settings that do not travel with a template repository")
    parser.add_argument("--repo", help="owner/repository; defaults to current gh repository")
    parser.add_argument("--fix", action="store_true", help="apply safe repository settings, labels, Actions defaults and Dependabot controls")
    parser.add_argument(
        "--fix-security",
        action="store_true",
        help="also enable supported secret scanning, push protection and CodeQL default setup",
    )
    parser.add_argument(
        "--fix-ruleset",
        action="store_true",
        help="apply/update the repository fallback branch ruleset when effective default-branch governance is insufficient",
    )
    args = parser.parse_args()

    if shutil.which("gh") is None:
        print("BLOCKED: GitHub CLI `gh` is not installed.")
        return 2

    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    try:
        repo = repo_name(args.repo)
    except RuntimeError as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2

    current_proc, current = api_json([f"repos/{repo}"])
    if current_proc.returncode != 0 or not isinstance(current, dict):
        print(current_proc.stderr.strip(), file=sys.stderr)
        return 2

    print(f"GitHub repository baseline — {repo}")
    results = merge_results(
        check_core_settings(repo, current, config, args.fix),
        check_actions_permissions(repo, config, args.fix),
        check_labels(repo, config, args.fix),
        check_dependabot(repo, args.fix),
        check_security_features(repo, current, args.fix_security),
        check_rulesets(repo, current, args.fix_ruleset),
        check_codeowners(repo),
    )

    print("\n== Summary ==")
    print(f"fixed={results.fixed} drift={results.drift} blocked={results.blocked}")
    if results.failed:
        print("RESULT: NON-COMPLIANT")
        return 1
    print("RESULT: COMPLIANT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

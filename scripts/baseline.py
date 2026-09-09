#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / ".baseline"
MANIFEST = BASELINE / "manifest.json"
STATE = BASELINE / "state.json"
VERSION = BASELINE / "VERSION"
RECOVERY = BASELINE / "recovery"

START_DEFAULT = "<!-- baseline:managed:start -->"
END_DEFAULT = "<!-- baseline:managed:end -->"


class BaselineError(RuntimeError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BaselineError(f"missing required file: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise BaselineError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def manifest(root: Path = ROOT) -> dict[str, Any]:
    return load_json(root / ".baseline" / "manifest.json")


def state() -> dict[str, Any]:
    if not STATE.exists():
        return {}
    return load_json(STATE)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def render_path(path: str, values: dict[str, str]) -> str:
    return render(path, values)


def slug_python(name: str) -> str:
    result = re.sub(r"[^A-Za-z0-9_]+", "_", name.replace("-", "_")).strip("_").lower()
    if not result:
        result = "project"
    if result[0].isdigit():
        result = "project_" + result
    return result


def slug_dist(name: str) -> str:
    result = re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower()
    return result or "project"


def discover_remote() -> tuple[str | None, str | None]:
    try:
        proc = subprocess.run(
            ["git", "remote", "get-url", "origin"], cwd=ROOT, text=True,
            capture_output=True, check=False, timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None, None
    if proc.returncode != 0:
        return None, None
    url = proc.stdout.strip()
    patterns = [
        r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
        r"https?://[^/]+/(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        m = re.search(pattern, url)
        if m:
            return m.group("owner"), m.group("repo")
    return None, None


def values_from_args(args: argparse.Namespace, existing: dict[str, Any] | None = None) -> dict[str, str]:
    existing = existing or {}
    remote_owner, remote_repo = discover_remote()
    project_name = getattr(args, "name", None) or existing.get("project_name") or remote_repo or ROOT.name
    owner = getattr(args, "owner", None) or existing.get("owner") or remote_owner or "OWNER"
    owner_name = getattr(args, "owner_name", None) or existing.get("owner_name") or owner
    profile = getattr(args, "profile", None) or existing.get("profile") or "generic"
    description = getattr(args, "description", None) or existing.get("description") or "TODO: describe this project."
    codeowner = getattr(args, "codeowner", None) or existing.get("codeowner") or ("@" + owner if owner != "OWNER" else "@OWNER")
    ansible_namespace = getattr(args, "ansible_namespace", None) or existing.get("ansible_namespace") or re.sub(r"[^a-z0-9_]", "_", owner.lower())
    ansible_collection = getattr(args, "ansible_collection", None) or existing.get("ansible_collection") or slug_python(project_name)
    return {
        "PROJECT_NAME": project_name,
        "PROJECT_DESCRIPTION": description,
        "PROFILE": profile,
        "BASELINE_VERSION": VERSION.read_text(encoding="utf-8").strip() if VERSION.exists() else "unknown",
        "OWNER": owner,
        "OWNER_NAME": owner_name,
        "CODEOWNER": codeowner,
        "PYTHON_PACKAGE": slug_python(project_name),
        "PYTHON_DIST_NAME": slug_dist(project_name),
        "ANSIBLE_NAMESPACE": ansible_namespace,
        "ANSIBLE_COLLECTION": ansible_collection,
    }


def safe_repo_path(root: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute():
        raise BaselineError(f"baseline path must be relative: {relative!r}")
    resolved_root = root.resolve()
    candidate = (resolved_root / rel).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise BaselineError(f"baseline path escapes repository root: {relative!r}") from exc
    return candidate


def asset_source(asset: dict[str, Any], root: Path = ROOT) -> Path:
    return safe_repo_path(root, asset["source"])


def asset_dest(asset: dict[str, Any], values: dict[str, str], root: Path = ROOT) -> Path:
    return safe_repo_path(root, render_path(asset["path"], values))


def managed_region(text: str, start: str, end: str) -> str:
    if start not in text or end not in text:
        raise BaselineError(f"managed markers missing: {start!r} / {end!r}")
    a = text.index(start)
    b = text.index(end, a) + len(end)
    return text[a:b]


def update_extensible(current: str, canonical: str, start: str, end: str) -> str:
    expected_region = managed_region(canonical, start, end)
    if start not in current or end not in current:
        raise BaselineError("extensible file is missing baseline managed markers; refusing destructive overwrite")
    a = current.index(start)
    b = current.index(end, a) + len(end)
    return current[:a] + expected_region + current[b:]


def applicable_assets(m: dict[str, Any], profile: str) -> list[dict[str, Any]]:
    if profile not in m.get("profiles", {}):
        raise BaselineError(f"unknown profile {profile!r}; choose one of: {', '.join(sorted(m.get('profiles', {})))}")
    return list(m["common_assets"]) + list(m["profiles"][profile]["assets"])


def apply_asset(asset: dict[str, Any], values: dict[str, str], *, force_seed: bool = False, source_root: Path = ROOT) -> str:
    src = asset_source(asset, source_root)
    dest = asset_dest(asset, values)
    ownership = asset["ownership"]
    canonical = render(src.read_text(encoding="utf-8"), values if ownership == "seed" else {})
    dest.parent.mkdir(parents=True, exist_ok=True)

    if ownership == "managed":
        changed = not dest.exists() or dest.read_text(encoding="utf-8") != canonical
        if changed:
            dest.write_text(canonical, encoding="utf-8", newline="\n")
        return "UPDATED" if changed else "OK"

    if ownership == "seed":
        if dest.exists() and not force_seed:
            return "PRESERVED"
        changed = not dest.exists() or dest.read_text(encoding="utf-8") != canonical
        if changed:
            dest.write_text(canonical, encoding="utf-8", newline="\n")
        return "SEEDED" if changed else "OK"

    if ownership == "extensible":
        if not dest.exists():
            dest.write_text(canonical, encoding="utf-8", newline="\n")
            return "SEEDED"
        start = asset.get("start_marker", START_DEFAULT)
        end = asset.get("end_marker", END_DEFAULT)
        current = dest.read_text(encoding="utf-8")
        expected = render(src.read_text(encoding="utf-8"), {})
        updated = update_extensible(current, expected, start, end)
        if updated != current:
            dest.write_text(updated, encoding="utf-8", newline="\n")
            return "UPDATED"
        return "OK"

    raise BaselineError(f"unsupported ownership: {ownership}")


def write_state(
    values: dict[str, str],
    source_repository: str | None = None,
    *,
    template_mode: bool = False,
) -> None:
    data = {
        "schema_version": 1,
        "installed_version": VERSION.read_text(encoding="utf-8").strip(),
        "profile": values["PROFILE"],
        "project_name": values["PROJECT_NAME"],
        "description": values["PROJECT_DESCRIPTION"],
        "owner": values["OWNER"],
        "owner_name": values["OWNER_NAME"],
        "codeowner": values["CODEOWNER"],
        "ansible_namespace": values["ANSIBLE_NAMESPACE"],
        "ansible_collection": values["ANSIBLE_COLLECTION"],
        "source_repository": source_repository,
        "template_mode": template_mode,
        "last_reconciled": now_iso(),
    }
    STATE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")


def cmd_bootstrap(args: argparse.Namespace) -> int:
    m = manifest()
    old = state()
    if old and old.get("profile") and old["profile"] != args.profile and not old.get("template_mode", False):
        raise BaselineError(
            f"repository already uses profile {old['profile']!r}; profile changes after bootstrap are unsupported in baseline 0.1"
        )
    force_seed = bool(old.get("template_mode", False))
    values = values_from_args(args, old)
    values["PROFILE"] = args.profile
    print(f"Engineering baseline {m['baseline_version']} bootstrap — profile={args.profile}")
    for asset in applicable_assets(m, args.profile):
        result = apply_asset(asset, values, force_seed=force_seed)
        print(f"[{result:<9}] {render_path(asset['path'], values)} ({asset['ownership']})")
    write_state(values, args.source_repository or old.get("source_repository"))
    print("RESULT: BOOTSTRAPPED")
    return 0


def drift_for_asset(asset: dict[str, Any], values: dict[str, str], source_root: Path = ROOT) -> tuple[str, str]:
    src = asset_source(asset, source_root)
    dest = asset_dest(asset, values)
    ownership = asset["ownership"]
    if ownership == "seed":
        return ("PROJECT" if dest.exists() else "PROJECT-MISSING", str(dest.relative_to(ROOT)))
    if not dest.exists():
        return ("MISSING", str(dest.relative_to(ROOT)))
    current = dest.read_text(encoding="utf-8")
    canonical = src.read_text(encoding="utf-8")
    if ownership == "managed":
        return ("OK" if current == canonical else "DRIFT", str(dest.relative_to(ROOT)))
    start = asset.get("start_marker", START_DEFAULT)
    end = asset.get("end_marker", END_DEFAULT)
    try:
        cur_region = managed_region(current, start, end)
        exp_region = managed_region(canonical, start, end)
    except BaselineError:
        return ("DRIFT", str(dest.relative_to(ROOT)))
    return ("OK" if cur_region == exp_region else "DRIFT", str(dest.relative_to(ROOT)))


def validate_frontmatter(path: Path, kind: str) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return [f"{path.relative_to(ROOT)}: missing YAML frontmatter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return [f"{path.relative_to(ROOT)}: unterminated YAML frontmatter"]
    fm = text[4:end]
    if kind == "skill":
        name_match = re.search(r"^name:\s*([^\n]+)$", fm, re.M)
        desc_match = re.search(r"^description:\s*([^\n]+)$", fm, re.M)
        if not name_match:
            errors.append(f"{path.relative_to(ROOT)}: skill name missing")
        else:
            name = name_match.group(1).strip().strip('"\'')
            if name != path.parent.name:
                errors.append(f"{path.relative_to(ROOT)}: skill name {name!r} != directory {path.parent.name!r}")
            if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
                errors.append(f"{path.relative_to(ROOT)}: invalid skill name {name!r}")
        if not desc_match or not desc_match.group(1).strip():
            errors.append(f"{path.relative_to(ROOT)}: skill description missing")
    elif kind == "agent":
        if not re.search(r"^description:\s*\S", fm, re.M):
            errors.append(f"{path.relative_to(ROOT)}: agent description missing")
    elif kind == "prompt":
        if not re.search(r"^name:\s*\S", fm, re.M):
            errors.append(f"{path.relative_to(ROOT)}: prompt name missing")
        if not re.search(r"^description:\s*\S", fm, re.M):
            errors.append(f"{path.relative_to(ROOT)}: prompt description missing")
    elif kind == "instruction":
        if not re.search(r"^applyTo:\s*\S", fm, re.M):
            errors.append(f"{path.relative_to(ROOT)}: instruction applyTo missing")
    return errors


def validate_actions_pins() -> list[str]:
    errors: list[str] = []
    pattern = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)", re.M)
    for path in sorted((ROOT / ".github" / "workflows").glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        for use in pattern.findall(text):
            if use.startswith("./"):
                continue
            if "@" not in use:
                errors.append(f"{path.relative_to(ROOT)}: action has no ref: {use}")
                continue
            _, ref = use.rsplit("@", 1)
            if not re.fullmatch(r"[0-9a-fA-F]{40}", ref):
                errors.append(f"{path.relative_to(ROOT)}: action ref is not pinned to full SHA: {use}")
    return errors


def validate_structure() -> list[str]:
    errors: list[str] = []
    try:
        m = manifest()
    except BaselineError as exc:
        return [str(exc)]
    current_version = VERSION.read_text(encoding="utf-8").strip()
    if current_version != m.get("baseline_version"):
        errors.append(".baseline/VERSION does not match manifest baseline_version")
    st = state()
    if st and st.get("installed_version") != current_version:
        errors.append(
            f".baseline/state.json installed_version {st.get('installed_version')!r} "
            f"does not match snapshot version {current_version!r}; upgrade may be staged or incomplete"
        )
    for path in sorted((ROOT / ".github" / "skills").glob("*/SKILL.md")):
        errors.extend(validate_frontmatter(path, "skill"))
    for path in sorted((ROOT / ".github" / "agents").glob("*.agent.md")):
        errors.extend(validate_frontmatter(path, "agent"))
    for path in sorted((ROOT / ".github" / "prompts").glob("*.prompt.md")):
        errors.extend(validate_frontmatter(path, "prompt"))
    for path in sorted((ROOT / ".github" / "instructions").glob("**/*.instructions.md")):
        errors.extend(validate_frontmatter(path, "instruction"))
    for path in [ROOT / ".vscode" / "settings.json", ROOT / ".vscode" / "tasks.json", ROOT / ".vscode" / "extensions.json", ROOT / "config" / "repository.json"]:
        if path.exists():
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
    errors.extend(validate_actions_pins())
    return errors


def cmd_reconcile(args: argparse.Namespace) -> int:
    m = manifest()
    st = state()
    if not st:
        raise BaselineError("repository is not bootstrapped; run bootstrap first")
    profile = st.get("profile", "generic")
    values = values_from_args(args, st)
    values["PROFILE"] = profile
    bad = 0
    print(f"Engineering baseline {m['baseline_version']} reconcile — profile={profile}")
    for asset in applicable_assets(m, profile):
        status, rel = drift_for_asset(asset, values)
        if status in {"DRIFT", "MISSING"}:
            bad += 1
            if args.fix:
                try:
                    result = apply_asset(asset, values)
                    print(f"[FIXED    ] {rel} ({result.lower()})")
                    bad -= 1
                except BaselineError as exc:
                    print(f"[FAILED   ] {rel}: {exc}")
            else:
                print(f"[{status:<9}] {rel}")
        elif args.verbose or status != "PROJECT":
            print(f"[{status:<9}] {rel}")
    if args.fix and bad == 0:
        write_state(
            values,
            st.get("source_repository"),
            template_mode=bool(st.get("template_mode", False)),
        )
    print("RESULT: COMPLIANT" if bad == 0 else f"RESULT: DRIFT ({bad} asset(s))")
    return 0 if bad == 0 else 1


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_structure()
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        print(f"RESULT: INVALID ({len(errors)} issue(s))")
        return 1
    print("[PASS] manifest/version")
    print("[PASS] skills/agents/prompts/instructions frontmatter")
    print("[PASS] JSON configuration")
    print("[PASS] GitHub Actions SHA pinning")
    print("RESULT: VALID")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    print("== Structure ==")
    v = cmd_validate(args)
    print("\n== Drift ==")
    try:
        r = cmd_reconcile(argparse.Namespace(fix=False, verbose=False))
    except BaselineError as exc:
        print(f"[FAIL] {exc}")
        r = 1
    result = 0 if v == 0 and r == 0 else 1
    print("\nDOCTOR: PASS" if result == 0 else "\nDOCTOR: FAIL")
    return result


def parse_release_version(value: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+].*)?", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def recovery_directories() -> list[Path]:
    if not RECOVERY.exists():
        return []
    return sorted(
        [p for p in RECOVERY.iterdir() if p.is_dir() and (p / "recovery.json").exists()],
        key=lambda p: p.name,
        reverse=True,
    )


def create_recovery_snapshot(source: Path) -> Path:
    """Capture all baseline-owned files that an upgrade could change."""
    old_state = state()
    if not old_state:
        raise BaselineError("repository is not bootstrapped")
    old_manifest = manifest()
    new_manifest = manifest(source)
    profile = old_state.get("profile", "generic")
    values = values_from_args(argparse.Namespace(), old_state)
    values["PROFILE"] = profile

    old_version = VERSION.read_text(encoding="utf-8").strip()
    new_version = (source / ".baseline" / "VERSION").read_text(encoding="utf-8").strip()

    # Include both old and new baseline-owned destinations. This lets rollback
    # restore files changed by an upgrade and remove newly introduced assets.
    destinations: dict[str, Path] = {}
    for candidate_manifest in (old_manifest, new_manifest):
        for asset in applicable_assets(candidate_manifest, profile):
            if asset["ownership"] == "seed":
                continue
            dest = asset_dest(asset, values)
            rel = dest.relative_to(ROOT.resolve()).as_posix()
            destinations[rel] = dest

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base_name = f"{stamp}-{old_version}-to-{new_version}"
    snapshot = RECOVERY / base_name
    suffix = 1
    while snapshot.exists():
        snapshot = RECOVERY / f"{base_name}-{suffix}"
        suffix += 1
    temp = RECOVERY / f".{snapshot.name}.tmp"
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir(parents=True, exist_ok=False)

    baseline_backup = temp / "baseline"
    shutil.copytree(BASELINE / "catalog", baseline_backup / "catalog")
    shutil.copy2(MANIFEST, baseline_backup / "manifest.json")
    shutil.copy2(VERSION, baseline_backup / "VERSION")
    shutil.copy2(STATE, baseline_backup / "state.json")

    assets: list[dict[str, Any]] = []
    for rel, dest in sorted(destinations.items()):
        existed = dest.exists()
        if existed and not dest.is_file():
            shutil.rmtree(temp)
            raise BaselineError(f"baseline-managed destination is not a regular file: {rel}")
        assets.append({"path": rel, "existed": existed})
        if existed:
            backup = safe_repo_path(temp / "files", rel)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, backup)

    metadata = {
        "schema_version": 1,
        "created_at": now_iso(),
        "old_version": old_version,
        "new_version": new_version,
        "profile": profile,
        "assets": assets,
    }
    (temp / "recovery.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")
    RECOVERY.mkdir(parents=True, exist_ok=True)
    temp.rename(snapshot)
    return snapshot


def restore_recovery_snapshot(snapshot: Path) -> None:
    snapshot = snapshot.resolve()
    recovery_root = RECOVERY.resolve()
    try:
        snapshot.relative_to(recovery_root)
    except ValueError as exc:
        raise BaselineError("recovery snapshot must be inside .baseline/recovery") from exc

    metadata_path = snapshot / "recovery.json"
    if not metadata_path.exists():
        raise BaselineError(f"invalid recovery snapshot: {snapshot}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    # Restore baseline-owned installed files first, using the exact pre-upgrade
    # contents. Project-owned seed files are intentionally never in this list.
    for item in metadata.get("assets", []):
        rel = item["path"]
        dest = safe_repo_path(ROOT, rel)
        if item.get("existed"):
            backup = safe_repo_path(snapshot / "files", rel)
            if not backup.is_file():
                raise BaselineError(f"recovery snapshot is incomplete; missing {rel}")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup, dest)
        elif dest.exists():
            if not dest.is_file():
                raise BaselineError(f"refusing to remove non-file during rollback: {rel}")
            dest.unlink()

    baseline_backup = snapshot / "baseline"
    if (BASELINE / "catalog").exists():
        shutil.rmtree(BASELINE / "catalog")
    shutil.copytree(baseline_backup / "catalog", BASELINE / "catalog")
    shutil.copy2(baseline_backup / "manifest.json", MANIFEST)
    shutil.copy2(baseline_backup / "VERSION", VERSION)
    shutil.copy2(baseline_backup / "state.json", STATE)


def copy_baseline_snapshot(source: Path) -> dict[str, Any]:
    source = source.resolve()
    source_manifest = manifest(source)
    source_version = (source / ".baseline" / "VERSION").read_text(encoding="utf-8").strip()
    if source_manifest.get("baseline_version") != source_version:
        raise BaselineError("source baseline VERSION/manifest mismatch")
    current_version = VERSION.read_text(encoding="utf-8").strip()
    if source_version == current_version:
        print(f"Source and installed baseline are both {current_version}.")
    # Replace only the immutable snapshot metadata/catalog. Installed files are applied afterwards.
    tmp = BASELINE / "tmp" / "upgrade"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / ".baseline" / "catalog", tmp / "catalog")
    shutil.copy2(source / ".baseline" / "manifest.json", tmp / "manifest.json")
    shutil.copy2(source / ".baseline" / "VERSION", tmp / "VERSION")
    if (BASELINE / "catalog").exists():
        shutil.rmtree(BASELINE / "catalog")
    shutil.move(str(tmp / "catalog"), str(BASELINE / "catalog"))
    shutil.copy2(tmp / "manifest.json", MANIFEST)
    shutil.copy2(tmp / "VERSION", VERSION)
    shutil.rmtree(tmp)
    return source_manifest


def cmd_upgrade(args: argparse.Namespace) -> int:
    source = Path(args.source).resolve()
    if not (source / ".baseline" / "manifest.json").exists():
        raise BaselineError(f"not an engineering baseline checkout: {source}")
    old = state()
    if not old:
        raise BaselineError("repository is not bootstrapped")

    old_version = old.get("installed_version", VERSION.read_text(encoding="utf-8").strip())
    source_version = (source / ".baseline" / "VERSION").read_text(encoding="utf-8").strip()
    old_semver = parse_release_version(old_version)
    new_semver = parse_release_version(source_version)
    if old_semver and new_semver and new_semver < old_semver and not args.allow_downgrade:
        raise BaselineError(
            f"refusing baseline downgrade {old_version} -> {source_version}; use rollback for recovery "
            "or --allow-downgrade when the downgrade is intentional"
        )

    recovery = create_recovery_snapshot(source)
    print(f"Recovery snapshot: {recovery.relative_to(ROOT)}")
    try:
        copy_baseline_snapshot(source)
        new_version = VERSION.read_text(encoding="utf-8").strip()
        print(f"Baseline snapshot: {old_version} -> {new_version}")
        if args.fix:
            rc = cmd_reconcile(argparse.Namespace(fix=True, verbose=True))
            if rc != 0:
                print("Upgrade reconciliation failed; restoring pre-upgrade snapshot.")
                restore_recovery_snapshot(recovery)
                print(f"ROLLBACK: restored {old_version}")
                return rc
            return 0
        print("Snapshot staged. Run `python scripts/baseline.py reconcile --fix` to apply managed changes.")
        print("`doctor` will remain non-compliant until the staged snapshot is reconciled or rolled back.")
        return 0
    except Exception:
        # Any unexpected failure after the recovery point is created must not
        # strand the repository in a half-upgraded baseline state.
        restore_recovery_snapshot(recovery)
        raise


def cmd_rollback(args: argparse.Namespace) -> int:
    snapshots = recovery_directories()
    if not snapshots:
        raise BaselineError("no recovery snapshots are available")

    if args.snapshot:
        candidate = RECOVERY / args.snapshot
        if candidate not in snapshots:
            available = ", ".join(p.name for p in snapshots[:5])
            raise BaselineError(f"recovery snapshot not found: {args.snapshot}; available: {available}")
        snapshot = candidate
    else:
        snapshot = snapshots[0]

    metadata = json.loads((snapshot / "recovery.json").read_text(encoding="utf-8"))
    restore_recovery_snapshot(snapshot)
    print(
        f"ROLLBACK: restored baseline {metadata.get('old_version', 'unknown')} "
        f"from {snapshot.relative_to(ROOT)}"
    )
    return cmd_doctor(argparse.Namespace())

def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Engineering baseline bootstrap, validation, drift, upgrade and rollback tool")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("bootstrap", help="initialise this repository from the baseline")
    b.add_argument("--profile", choices=["generic", "python", "ansible"], default="generic")
    b.add_argument("--name")
    b.add_argument("--description")
    b.add_argument("--owner")
    b.add_argument("--owner-name")
    b.add_argument("--codeowner")
    b.add_argument("--ansible-namespace")
    b.add_argument("--ansible-collection")
    b.add_argument("--source-repository", help="central baseline GitHub repository, e.g. owner/engineering-baseline")
    b.set_defaults(func=cmd_bootstrap)

    r = sub.add_parser("reconcile", help="detect or repair drift from managed baseline assets")
    r.add_argument("--fix", action="store_true")
    r.add_argument("--verbose", action="store_true")
    r.set_defaults(func=cmd_reconcile)

    v = sub.add_parser("validate", help="validate baseline structure and customization files")
    v.set_defaults(func=cmd_validate)

    d = sub.add_parser("doctor", help="run structure validation and drift checks")
    d.set_defaults(func=cmd_doctor)

    u = sub.add_parser("upgrade", help="transactionally load a newer baseline snapshot from another checkout")
    u.add_argument("--source", required=True)
    u.add_argument("--fix", action="store_true", help="apply managed/extensible changes immediately")
    u.add_argument("--allow-downgrade", action="store_true", help="allow an intentional version downgrade")
    u.set_defaults(func=cmd_upgrade)

    rb = sub.add_parser("rollback", help="restore the latest or selected pre-upgrade recovery snapshot")
    rb.add_argument("--snapshot", help="snapshot directory name under .baseline/recovery; defaults to latest")
    rb.set_defaults(func=cmd_rollback)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except BaselineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

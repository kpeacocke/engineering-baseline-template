from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from .common import FactoryError, Runner, RUNNER, run_baseline, state_values

START = "<!-- baseline:managed:start -->"
END = "<!-- baseline:managed:end -->"


def slug_python(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", name.replace("-", "_")).strip("_").lower() or "project"
    return "project_" + value if value[0].isdigit() else value


def values(profile: str, owner: str, name: str, description: str, source_repository: str,
           *, codeowner: str | None = None, ansible_namespace: str | None = None,
           ansible_collection: str | None = None) -> dict[str, str]:
    return {
        "PROJECT_NAME": name, "PROJECT_DESCRIPTION": description, "PROFILE": profile,
        "OWNER": owner, "OWNER_NAME": owner, "CODEOWNER": codeowner or f"@{owner}",
        "PYTHON_PACKAGE": slug_python(name),
        "PYTHON_DIST_NAME": re.sub(r"[^A-Za-z0-9]+", "-", name).strip("-").lower() or "project",
        "ANSIBLE_NAMESPACE": ansible_namespace or re.sub(r"[^a-z0-9_]", "_", owner.lower()),
        "ANSIBLE_COLLECTION": ansible_collection or slug_python(name),
        "SOURCE_REPOSITORY": source_repository,
    }


def render(text: str, vals: dict[str, str]) -> str:
    for k, v in vals.items():
        text = text.replace("{{" + k + "}}", v)
    return text


def manifest(root: Path) -> dict[str, Any]:
    return json.loads((root / ".baseline/manifest.json").read_text(encoding="utf-8"))


def assets(root: Path, profile: str) -> list[dict[str, Any]]:
    m = manifest(root)
    if profile not in m.get("profiles", {}):
        raise FactoryError(f"unknown profile: {profile}")
    return list(m["common_assets"]) + list(m["profiles"][profile]["assets"])


def managed_region(text: str, start: str, end: str) -> str:
    if start not in text or end not in text:
        raise FactoryError(f"managed markers missing: {start!r} / {end!r}")
    a = text.index(start); b = text.index(end, a) + len(end)
    return text[a:b]


def merge_extensible(current: str, canonical: str, start: str, end: str) -> str:
    region = managed_region(canonical, start, end)
    if start in current and end in current:
        a = current.index(start); b = current.index(end, a) + len(end)
        return current[:a] + region + current[b:]
    sep = "" if not current or current.endswith("\n\n") else ("\n" if current.endswith("\n") else "\n\n")
    return current + sep + region + "\n"


def rendered_path(asset: dict[str, Any], vals: dict[str, str]) -> str:
    return render(str(asset["path"]), vals)


def write_state(target: Path, vals: dict[str, str], version: str, profile: str, overrides: list[str]) -> None:
    data = {
        "schema_version": 1, "installed_version": version, "profile": profile,
        "project_name": vals["PROJECT_NAME"], "description": vals["PROJECT_DESCRIPTION"],
        "owner": vals["OWNER"], "owner_name": vals["OWNER_NAME"], "codeowner": vals["CODEOWNER"],
        "ansible_namespace": vals["ANSIBLE_NAMESPACE"], "ansible_collection": vals["ANSIBLE_COLLECTION"],
        "source_repository": vals["SOURCE_REPOSITORY"], "template_mode": False,
        "local_overrides": sorted(set(overrides)), "last_reconciled": None,
    }
    (target / ".baseline/state.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def adopt(source: Path, target: Path, *, profile: str, owner: str, name: str,
          source_repository: str, description: str = "TODO: describe this project.") -> list[str]:
    existing_state = state_values(target)
    if existing_state and not existing_state.get("template_mode", False):
        raise FactoryError("repository already has an installed baseline; use update")
    if (target / ".baseline").exists():
        shutil.rmtree(target / ".baseline")
    shutil.copytree(source / ".baseline", target / ".baseline")
    version = (source / ".baseline/VERSION").read_text(encoding="utf-8").strip()
    vals = values(profile, owner, name, description, source_repository)
    overrides: list[str] = []
    for asset in assets(source, profile):
        rel = rendered_path(asset, vals)
        src = source / str(asset["source"])
        dst = target / rel
        ownership = str(asset["ownership"])
        canonical = render(src.read_text(encoding="utf-8"), vals if ownership == "seed" else {})
        dst.parent.mkdir(parents=True, exist_ok=True)
        if ownership == "managed":
            if not dst.exists():
                dst.write_text(canonical, encoding="utf-8", newline="\n")
            elif dst.read_text(encoding="utf-8") != canonical:
                overrides.append(rel)
        elif ownership == "seed":
            if not dst.exists():
                dst.write_text(canonical, encoding="utf-8", newline="\n")
        elif ownership == "extensible":
            if not dst.exists():
                dst.write_text(canonical, encoding="utf-8", newline="\n")
            else:
                current = dst.read_text(encoding="utf-8")
                updated = merge_extensible(current, canonical, asset.get("start_marker", START), asset.get("end_marker", END))
                if updated != current:
                    dst.write_text(updated, encoding="utf-8", newline="\n")
        else:
            raise FactoryError(f"unsupported ownership: {ownership}")
    write_state(target, vals, version, profile, overrides)
    return overrides


def snapshot_paths(target: Path) -> list[str]:
    paths = [".baseline/VERSION", ".baseline/manifest.json", ".baseline/state.json"]
    catalog = target / ".baseline/catalog"
    if catalog.exists():
        paths.extend(p.relative_to(target).as_posix() for p in catalog.rglob("*") if p.is_file())
    return sorted(set(paths))


def applicable_paths(target: Path) -> list[str]:
    st = state_values(target); profile = str(st.get("profile") or "generic")
    vals = values(profile, str(st.get("owner") or "OWNER"), str(st.get("project_name") or "project"),
                  str(st.get("description") or ""), str(st.get("source_repository") or ""),
                  codeowner=str(st.get("codeowner") or "@OWNER"),
                  ansible_namespace=str(st.get("ansible_namespace") or "owner"),
                  ansible_collection=str(st.get("ansible_collection") or "project"))
    return sorted(set(rendered_path(a, vals) for a in assets(target, profile) if (target / rendered_path(a, vals)).exists()))


def local_doctor(target: Path, *, runner: Runner = RUNNER) -> None:
    run_baseline(target, ["validate"], runner=runner)
    st = state_values(target)
    if not st:
        raise FactoryError("missing .baseline/state.json")
    profile = str(st.get("profile") or "generic")
    overrides = set(st.get("local_overrides") or [])
    vals = values(profile, str(st.get("owner") or "OWNER"), str(st.get("project_name") or "project"),
                  str(st.get("description") or ""), str(st.get("source_repository") or ""),
                  codeowner=str(st.get("codeowner") or "@OWNER"),
                  ansible_namespace=str(st.get("ansible_namespace") or "owner"),
                  ansible_collection=str(st.get("ansible_collection") or "project"))
    drift: list[str] = []
    for asset in assets(target, profile):
        rel = rendered_path(asset, vals); dst = target / rel; own = str(asset["ownership"])
        if own == "seed":
            continue
        if not dst.exists():
            drift.append(f"missing {rel}"); continue
        if rel in overrides:
            continue
        canonical = (target / str(asset["source"])).read_text(encoding="utf-8")
        current = dst.read_text(encoding="utf-8")
        if own == "managed" and current != canonical:
            drift.append(f"managed drift {rel}")
        elif own == "extensible":
            try:
                if managed_region(current, asset.get("start_marker", START), asset.get("end_marker", END)) != managed_region(canonical, asset.get("start_marker", START), asset.get("end_marker", END)):
                    drift.append(f"extensible drift {rel}")
            except FactoryError:
                drift.append(f"managed markers missing {rel}")
    if drift:
        raise FactoryError("local baseline drift:\n  " + "\n  ".join(drift))
    print(f"[PASS ] local baseline {st.get('installed_version')} profile={profile} overrides={len(overrides)}")


def preserve_overrides(target: Path) -> dict[str, bytes]:
    return {rel: (target / rel).read_bytes() for rel in state_values(target).get("local_overrides", []) if (target / rel).exists()}


def restore_overrides(target: Path, saved: dict[str, bytes], source_repository: str) -> None:
    st = state_values(target)
    for rel, data in saved.items():
        p = target / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(data)
    st["local_overrides"] = sorted(saved)
    st["source_repository"] = source_repository
    (target / ".baseline/state.json").write_text(json.dumps(st, indent=2) + "\n", encoding="utf-8")

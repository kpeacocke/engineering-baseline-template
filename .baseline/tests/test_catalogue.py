import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


class CatalogueTests(unittest.TestCase):
    def assert_current_recommendations(self, path: Path) -> None:
        recommendations = json.loads(path.read_text(encoding="utf-8"))[
            "recommendations"
        ]
        self.assertIsInstance(recommendations, list)
        self.assertTrue(all(isinstance(value, str) for value in recommendations))
        normalised = [value.casefold() for value in recommendations]
        self.assertNotIn("github.copilot", normalised, str(path))
        self.assertIn("github.copilot-chat", normalised, str(path))
        self.assertEqual(len(normalised), len(set(normalised)), str(path))

    def test_workspace_and_profile_recommendations(self) -> None:
        self.assert_current_recommendations(ROOT / ".vscode/extensions.json")
        manifest = json.loads(
            (ROOT / ".baseline/manifest.json").read_text(encoding="utf-8")
        )
        for profile in manifest["profiles"]:
            with self.subTest(profile=profile):
                self.assert_current_recommendations(
                    ROOT
                    / ".baseline/catalog/profiles"
                    / profile
                    / ".vscode/extensions.json"
                )

    def test_bootstrap_recommendations_for_every_profile(self) -> None:
        manifest = json.loads(
            (ROOT / ".baseline/manifest.json").read_text(encoding="utf-8")
        )
        with tempfile.TemporaryDirectory(prefix="baseline-catalogue-") as tmp:
            for profile in manifest["profiles"]:
                with self.subTest(profile=profile):
                    target = Path(tmp) / profile
                    shutil.copytree(ROOT / ".baseline", target / ".baseline")
                    (target / "scripts").mkdir()
                    shutil.copy2(
                        ROOT / "scripts/baseline.py",
                        target / "scripts/baseline.py",
                    )
                    commands = [
                        [
                            "scripts/baseline.py",
                            "bootstrap",
                            "--profile",
                            profile,
                            "--name",
                            "catalogue-smoke",
                            "--owner",
                            "ci-owner",
                            "--openssf-project",
                            "0",
                        ],
                        ["scripts/project_factory.py", "local-doctor"],
                    ]
                    for command in commands:
                        result = subprocess.run(
                            [sys.executable, *command],
                            cwd=target,
                            capture_output=True,
                            text=True,
                            timeout=60,
                            check=False,
                        )
                        self.assertEqual(
                            result.returncode,
                            0,
                            result.stdout + result.stderr,
                        )
                    actual = target / ".vscode/extensions.json"
                    self.assert_current_recommendations(actual)
                    expected = (
                        ROOT
                        / ".baseline/catalog/profiles"
                        / profile
                        / ".vscode/extensions.json"
                    )
                    self.assertEqual(
                        json.loads(actual.read_text(encoding="utf-8")),
                        json.loads(expected.read_text(encoding="utf-8")),
                    )
                    self.assertEqual(
                        yaml.safe_load(
                            (target / ".github/dependabot.yml").read_text(
                                encoding="utf-8"
                            )
                        ),
                        yaml.safe_load(
                            (
                                ROOT
                                / ".baseline/catalog/profiles"
                                / profile
                                / ".github/dependabot.yml"
                            ).read_text(encoding="utf-8")
                        ),
                    )
                    self.assertEqual(
                        json.loads(
                            (target / ".baseline/state.json").read_text(
                                encoding="utf-8"
                            )
                        )["installed_version"],
                        manifest["baseline_version"],
                    )

    def test_managed_workflows_match_catalogue(self) -> None:
        manifest = json.loads(
            (ROOT / ".baseline/manifest.json").read_text(encoding="utf-8")
        )
        workflows = [
            asset
            for asset in manifest["common_assets"]
            if asset["path"].startswith(".github/workflows/")
            and asset["ownership"] == "managed"
        ]
        self.assertTrue(workflows)
        for asset in workflows:
            with self.subTest(workflow=asset["path"]):
                self.assertEqual(
                    (ROOT / asset["path"]).read_bytes(),
                    (ROOT / asset["source"]).read_bytes(),
                )

    def test_action_versions_match_across_catalogue_directories(self) -> None:
        paths = [
            *sorted((ROOT / ".github/workflows").glob("*.y*ml")),
            *sorted((ROOT / ".baseline/catalog").glob("**/workflows/*.y*ml")),
        ]
        self.assert_action_versions_match(paths)

    def assert_action_versions_match(self, paths: list[Path]) -> None:
        declarations: dict[str, set[str]] = {}
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for action, version in re.findall(
                r"^\s*-?\s*uses:\s*([^@\s]+)@([^\n]+)", text, re.MULTILINE
            ):
                declarations.setdefault(action, set()).add(version.strip())
        self.assertTrue(declarations)
        for action, versions in declarations.items():
            self.assertEqual(len(versions), 1, f"{action}: {sorted(versions)}")

    def test_named_step_action_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="baseline-action-fixture-") as tmp:
            path = Path(tmp) / "workflow.yml"
            path.write_text(
                "steps:\n"
                "  - uses: actions/setup-python@" + "a" * 40 + " # v7.1.0\n"
                "  - name: Set up Python\n"
                "    uses: actions/setup-python@" + "b" * 40 + " # v7.0.0\n",
                encoding="utf-8",
            )
            with self.assertRaises(AssertionError):
                self.assert_action_versions_match([path])

    def assert_dependabot_config(self, text: str, directories: set[str]) -> None:
        config = yaml.safe_load(text)
        self.assertIsInstance(config, dict)
        self.assertEqual(config.get("version"), 2)
        updates = config.get("updates")
        self.assertIsInstance(updates, list)
        self.assertTrue(all(isinstance(entry, dict) for entry in updates))
        actions = [
            entry for entry in updates
            if entry.get("package-ecosystem") == "github-actions"
        ]
        self.assertEqual(len(actions), 1, "expected one Actions update entry")
        entry = actions[0]
        self.assertNotIn("directory", entry)
        actual = entry.get("directories")
        self.assertIsInstance(actual, list)
        self.assertTrue(all(isinstance(value, str) for value in actual))
        self.assertEqual(set(actual), directories)
        self.assertEqual(len(actual), len(directories), "duplicate directories")
        self.assertEqual(entry.get("schedule"), {"interval": "weekly"})
        self.assertEqual(
            entry.get("groups"),
            {
                "workflow-actions": {
                    "group-by": "dependency-name",
                    "patterns": ["*"],
                }
            },
        )

    def test_dependabot_configuration_for_every_profile(self) -> None:
        workflow_dirs = {
            "/" + str(path.relative_to(ROOT))
            for path in (ROOT / ".baseline/catalog").glob("**/workflows")
            if any(path.glob("*.y*ml"))
        }
        self.assertTrue(workflow_dirs)
        directories = {"/", *workflow_dirs}
        manifest = json.loads(
            (ROOT / ".baseline/manifest.json").read_text(encoding="utf-8")
        )
        paths = [ROOT / ".github/dependabot.yml"]
        paths.extend(
            ROOT / ".baseline/catalog/profiles" / profile / ".github/dependabot.yml"
            for profile in manifest["profiles"]
        )
        for path in paths:
            with self.subTest(path=path):
                text = path.read_text(encoding="utf-8")
                self.assert_dependabot_config(text, directories)
                if path == ROOT / ".baseline/catalog/profiles/python/.github/dependabot.yml":
                    pip = [
                        entry for entry in yaml.safe_load(text)["updates"]
                        if entry["package-ecosystem"] == "pip"
                    ]
                    self.assertEqual(
                        pip,
                        [{
                            "package-ecosystem": "pip",
                            "directory": "/",
                            "schedule": {"interval": "weekly"},
                        }],
                    )

    def test_dependabot_configuration_rejects_regressions(self) -> None:
        config = yaml.safe_load(
            (ROOT / ".github/dependabot.yml").read_text(encoding="utf-8")
        )
        directories = set(config["updates"][0]["directories"])
        for defect in ("missing-directory", "duplicate-directory", "no-grouping", "root-only"):
            with self.subTest(defect=defect):
                broken = json.loads(json.dumps(config))
                entry = broken["updates"][0]
                if defect == "missing-directory":
                    entry["directories"].pop()
                elif defect == "duplicate-directory":
                    entry["directories"].append("/")
                elif defect == "no-grouping":
                    del entry["groups"]["workflow-actions"]["group-by"]
                else:
                    del entry["directories"]
                    entry["directory"] = "/"
                with self.assertRaises(AssertionError):
                    self.assert_dependabot_config(yaml.safe_dump(broken), directories)
        with self.assertRaises(yaml.YAMLError):
            self.assert_dependabot_config("updates: [", directories)
        with self.assertRaises(AssertionError):
            self.assert_dependabot_config("[]", directories)

    def test_release_metadata_is_consistent(self) -> None:
        version = (ROOT / ".baseline/VERSION").read_text(encoding="utf-8").strip()
        self.assertRegex(version, r"^\d+\.\d+\.\d+$")
        manifest = json.loads(
            (ROOT / ".baseline/manifest.json").read_text(encoding="utf-8")
        )
        state = json.loads(
            (ROOT / ".baseline/state.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["baseline_version"], version)
        self.assertEqual(state["installed_version"], version)
        for path in (
            ROOT / "CHANGELOG.md",
            ROOT / ".baseline/catalog/common/CHANGELOG.md",
        ):
            self.assertIn(f"\n## {version}\n", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

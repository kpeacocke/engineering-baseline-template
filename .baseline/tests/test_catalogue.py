import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


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
        declarations: dict[str, set[str]] = {}
        paths = [
            *sorted((ROOT / ".github/workflows").glob("*.y*ml")),
            *sorted((ROOT / ".baseline/catalog").glob("**/workflows/*.y*ml")),
        ]
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for action, version in re.findall(
                r"^\s*-\s*uses:\s*([^@\s]+)@([^\n]+)", text, re.MULTILINE
            ):
                declarations.setdefault(action, set()).add(version.strip())
        self.assertTrue(declarations)
        for action, versions in declarations.items():
            with self.subTest(action=action):
                self.assertEqual(len(versions), 1, sorted(versions))


if __name__ == "__main__":
    unittest.main()

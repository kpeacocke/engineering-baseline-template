import argparse
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOTS = (ROOT / "scripts", ROOT / ".baseline/catalog/common/scripts")


class FactoryLegacyTests(unittest.TestCase):
    def factory(self, script_root):
        name = "_baseline_legacy_test_factory"
        spec = importlib.util.spec_from_file_location(
            name, script_root / "_project_factory/__init__.py"
        )
        package = importlib.util.module_from_spec(spec)
        sys.modules[name] = package
        self.addCleanup(sys.modules.pop, name, None)
        spec.loader.exec_module(package)
        for submodule in ("common", "local"):
            module_name = f"{name}.{submodule}"
            spec = importlib.util.spec_from_file_location(
                module_name, script_root / f"_project_factory/{submodule}.py"
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            self.addCleanup(sys.modules.pop, module_name, None)
            spec.loader.exec_module(module)
            setattr(package, submodule, module)
        return package

    def test_badge_values_and_validation(self):
        for script_root in SCRIPT_ROOTS:
            factory = self.factory(script_root)
            for value, expected in (
                ("", ""),
                ("  ", ""),
                ("12345", "https://www.bestpractices.dev/en/projects/12345"),
            ):
                with self.subTest(root=script_root, registration=value):
                    result = factory.local.values(
                        "generic", "owner", "project", "", "owner/template", value
                    )
                    self.assertEqual(result["OPENSSF_PROJECT"], expected)
                    self.assertEqual(
                        result["OPENSSF_PROJECT_ID"], "12345" if expected else ""
                    )
            with self.assertRaises(factory.common.FactoryError):
                factory.local.values(
                    "generic", "owner", "project", "", "owner/template", "invalid"
                )

    def test_seed_excludes_direct_and_nested_destinations(self):
        for script_root in SCRIPT_ROOTS:
            factory = self.factory(script_root)
            for destination in ("project", "generated/project"):
                with self.subTest(root=script_root, destination=destination):
                    with tempfile.TemporaryDirectory() as tmp:
                        source = Path(tmp) / "source"
                        source.mkdir()
                        (source / "template.txt").write_text("template")
                        (source / ".git").mkdir()
                        (source / ".git/source-only").write_text("source")
                        target = source / destination
                        (target / ".git").mkdir(parents=True)
                        (target / ".git/HEAD").write_text("destination")
                        factory.common.seed_from_source(source, target)
                        self.assertEqual((target / "template.txt").read_text(), "template")
                        self.assertEqual((target / ".git/HEAD").read_text(), "destination")
                        self.assertFalse((target / ".git/source-only").exists())
                        self.assertFalse((target / destination).exists())

    def test_legacy_maintenance_without_registration(self):
        for script_root in SCRIPT_ROOTS:
            with self.subTest(root=script_root), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                scripts = root / "scripts"
                scripts.mkdir()
                shutil.copyfile(script_root / "baseline.py", scripts / "baseline.py")
                baseline = root / ".baseline"
                (baseline / "catalog").mkdir(parents=True)
                (baseline / "VERSION").write_text("0.5.1\n")
                (baseline / "state.json").write_text(json.dumps({
                    "installed_version": "0.5.1", "profile": "generic",
                    "project_name": "legacy", "owner": "owner",
                }))
                (baseline / "manifest.json").write_text(json.dumps({
                    "baseline_version": "0.5.1", "common_assets": [],
                    "profiles": {"generic": {"assets": []}},
                }))
                spec = importlib.util.spec_from_file_location(
                    "_baseline_legacy_test_engine", scripts / "baseline.py"
                )
                engine = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(engine)
                self.assertEqual(engine.cmd_doctor(argparse.Namespace()), 0)
                self.assertEqual(
                    engine.cmd_reconcile(argparse.Namespace(fix=True, verbose=False)), 0
                )
                self.assertEqual(engine.state()["openssf_project"], "")
                snapshot = engine.create_recovery_snapshot(root)
                snapshot_state = json.loads(
                    (snapshot / "baseline/state.json").read_text()
                )
                self.assertEqual(snapshot_state["openssf_project"], "")


if __name__ == "__main__":
    unittest.main()

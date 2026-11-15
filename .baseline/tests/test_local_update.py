import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class LocalUpdateTests(unittest.TestCase):
    def run_command(self, target, *args):
        result = subprocess.run(
            args,
            cwd=target,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_repeat_update_stages_only_real_changes(self):
        with tempfile.TemporaryDirectory(prefix="baseline-update-test-") as tmp:
            target = Path(tmp) / "target"
            target.mkdir()
            source = Path(tmp) / "source"
            ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
            shutil.copytree(ROOT / ".baseline", source / ".baseline", ignore=ignore)
            shutil.copytree(source / ".baseline", target / ".baseline")
            scripts = target / "scripts"
            scripts.mkdir()
            shutil.copyfile(ROOT / "scripts/baseline.py", scripts / "baseline.py")
            self.run_command(
                target, sys.executable, "scripts/baseline.py", "bootstrap",
                "--profile", "generic", "--name", "test-project",
                "--owner", "test-owner", "--openssf-project", "12345",
            )
            state_path = target / ".baseline/state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["last_reconciled"] = "2000-01-01T00:00:00+00:00"
            override_path = ".github/workflows/baseline-update.yml"
            override = target / override_path
            override.write_text(
                override.read_text(encoding="utf-8") + "\n# Local override\n",
                encoding="utf-8",
            )
            original_override = override.read_bytes()
            state["local_overrides"] = [override_path]
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            self.run_command(target, "git", "init")
            self.run_command(target, "git", "add", ".")
            self.run_command(
                target, "git", "-c", "user.name=Test", "-c",
                "user.email=test@example.invalid", "-c", "commit.gpgsign=false",
                "commit", "-m", "initial baseline",
            )

            cache = source / ".baseline/catalog/common/scripts/__pycache__"
            cache.mkdir()
            (cache / "generated.pyc").write_bytes(b"generated")
            self.run_command(
                target, sys.executable, "scripts/project_factory.py",
                "apply-update", "--source", str(source),
            )
            staged = self.run_command(target, "git", "diff", "--cached", "--name-only")
            self.assertEqual(staged, "")
            self.assertEqual(json.loads(state_path.read_text())["last_reconciled"],
                             "2000-01-01T00:00:00+00:00")
            self.assertEqual(override.read_bytes(), original_override)

            catalogue_file = source / ".baseline/catalog/common/CHANGELOG.md"
            with catalogue_file.open("a", encoding="utf-8") as handle:
                handle.write("\nSame-version catalogue change.\n")
            self.run_command(
                target, sys.executable, "scripts/project_factory.py",
                "apply-update", "--source", str(source),
            )
            staged = self.run_command(target, "git", "diff", "--cached", "--name-only")
            self.assertIn(".baseline/catalog/common/CHANGELOG.md", staged.splitlines())
            self.assertNotEqual(json.loads(state_path.read_text())["last_reconciled"],
                                "2000-01-01T00:00:00+00:00")
            self.assertEqual(override.read_bytes(), original_override)


if __name__ == "__main__":
    unittest.main()

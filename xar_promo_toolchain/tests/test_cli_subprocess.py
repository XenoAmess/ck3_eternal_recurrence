from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PACKAGE_ROOT / "src"
PYPROJECT = PACKAGE_ROOT / "pyproject.toml"
CONSOLE_BOOTSTRAP = (
    "from xar_promo.cli import main; raise SystemExit(main())"
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


class CliSubprocessWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.project = self.root / "demo-project"
        self.source = self.root / "source-material" / "final-cut.mp4"
        self.source.parent.mkdir(parents=True)
        self.source.write_bytes(
            b"xar-promo black-box source material\x00\x01\xff\n"
        )
        stat = self.source.stat()
        self.source_contract = {
            "bytes": self.source.read_bytes(),
            "size": stat.st_size,
            "mtime_ns": stat.st_mtime_ns,
            "sha256": sha256_bytes(self.source.read_bytes()),
        }
        self.environment = os.environ.copy()
        existing_pythonpath = self.environment.get("PYTHONPATH")
        self.environment["PYTHONPATH"] = str(SOURCE_ROOT) + (
            os.pathsep + existing_pythonpath if existing_pythonpath else ""
        )
        self.environment["PYTHONDONTWRITEBYTECODE"] = "1"
        self.environment["PYTHONUTF8"] = "1"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def invoke(
        self,
        entry: str,
        *arguments: object,
        expected: int = 0,
    ) -> subprocess.CompletedProcess[str]:
        argv = [str(value) for value in arguments]
        if entry == "module":
            command = [sys.executable, "-m", "xar_promo", *argv]
        elif entry == "console":
            # pyproject binds ``xar-promo`` to this exact callable.  Invoking
            # it in a fresh Python process is the installer-independent
            # equivalent of a generated console-script shim.
            command = [
                sys.executable,
                "-c",
                CONSOLE_BOOTSTRAP,
                *argv,
            ]
        else:  # pragma: no cover - test author invariant
            raise AssertionError(f"unknown entry mode: {entry}")
        completed = subprocess.run(
            command,
            cwd=self.root,
            env=self.environment,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            expected,
            completed.returncode,
            msg=(
                f"command={command!r}\nstdout={completed.stdout}\n"
                f"stderr={completed.stderr}"
            ),
        )
        return completed

    def assert_source_unchanged(self) -> None:
        stat = self.source.stat()
        self.assertEqual(self.source_contract["bytes"], self.source.read_bytes())
        self.assertEqual(self.source_contract["size"], stat.st_size)
        self.assertEqual(self.source_contract["mtime_ns"], stat.st_mtime_ns)
        self.assertEqual(
            self.source_contract["sha256"],
            sha256_bytes(self.source.read_bytes()),
        )

    def assert_config_binding(
        self,
        manifest_path: Path,
        expected_payload: bytes,
    ) -> dict[str, object]:
        manifest = read_json(manifest_path)
        binding = manifest["project_config"]
        self.assertIsInstance(binding, dict)
        binding = dict(binding)
        snapshot = (manifest_path.parent / str(binding["path"])).resolve()
        expected_digest = sha256_bytes(expected_payload)
        self.assertTrue(snapshot.is_file())
        self.assertEqual(expected_payload, snapshot.read_bytes())
        self.assertEqual(len(expected_payload), binding["bytes"])
        self.assertEqual(expected_digest, binding["sha256"])
        self.assertIn(
            f"artifacts{os.sep}project-config{os.sep}sha256",
            str(snapshot),
        )
        self.assertEqual(
            snapshot.name,
            f"{expected_digest}.json",
        )
        return manifest

    def assert_history_copy(
        self,
        manifest_path: Path,
        old_payload: bytes,
    ) -> Path:
        digest = sha256_bytes(old_payload)
        history = (
            manifest_path.parent
            / "artifacts"
            / "manifest-history"
            / "sha256"
            / digest[:2]
            / f"{digest}.json"
        )
        self.assertTrue(history.is_file())
        self.assertEqual(old_payload, history.read_bytes())
        return history

    def test_composer_import_failure_is_a_clean_exit_two(self) -> None:
        module = self.root / "broken_composer.py"
        module.write_text(
            "raise RuntimeError('fixture composer import failed')\n",
            encoding="utf-8",
        )
        completed = self.invoke(
            "module",
            "plan",
            self.root / "missing-project.json",
            "--workdir",
            self.root / "uncreated-attempt",
            "--composer",
            "broken_composer:compose",
            "--validate-only",
            expected=2,
        )
        self.assertIn("RED: could not load composer", completed.stderr)
        self.assertIn("fixture composer import failed", completed.stderr)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertFalse((self.root / "uncreated-attempt").exists())

    def test_module_and_console_complete_append_only_workflow(self) -> None:
        pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
        self.assertEqual(
            "xar_promo.cli:main",
            pyproject["project"]["scripts"]["xar-promo"],
        )
        module_version = self.invoke("module", "--version").stdout.strip()
        console_version = self.invoke("console", "--version").stdout.strip()
        self.assertEqual("xar-promo 0.1.0", module_version)
        self.assertEqual(module_version, console_version)

        initialized = self.invoke(
            "module",
            "init",
            self.project,
            "--project-id",
            "demo-promo",
            "--title",
            "Demo Promo",
            "--run-id",
            "initial",
            "--narration-locale",
            "zh-CN",
            "--subtitle-locale",
            "zh-CN",
            "--subtitle-locale",
            "en",
        )
        self.assertIn("INITIALIZED:", initialized.stdout)
        config_path = self.project / "promo-project.json"
        initial_run = self.project / "runs" / "initial" / "run-manifest.json"
        self.assertTrue(config_path.is_file())
        self.assertTrue(initial_run.is_file())
        initial_config_payload = config_path.read_bytes()
        initial_manifest = self.assert_config_binding(
            initial_run,
            initial_config_payload,
        )
        self.assertEqual([], initial_manifest["artifacts"])
        self.assertEqual([], initial_manifest["signoffs"])

        initial_validation = self.invoke(
            "console", "validate", initial_run, "--json"
        )
        initial_result = json.loads(initial_validation.stdout)
        self.assertEqual("GREEN", initial_result["status"])
        self.assertEqual("run-manifest-v1", initial_result["source_format"])

        config = read_json(config_path)
        config["project"]["title"] = "Demo Promo — production run"
        config["chapters"] = [
            {
                "id": "feature-overview",
                "type": "gameplay",
                "state": "ready",
                "title": {
                    "zh-CN": "功能总览",
                    "en": "Feature overview",
                },
                "cues": [],
                "artifact_ids": ["final-video"],
            }
        ]
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        production_config_payload = config_path.read_bytes()
        self.assertNotEqual(initial_config_payload, production_config_payload)

        # Editing checked-in intent cannot stale an already started run: the
        # run validates against its immutable content-addressed config copy.
        old_run_after_edit = self.invoke(
            "module", "validate", initial_run, "--json"
        )
        self.assertEqual("GREEN", json.loads(old_run_after_edit.stdout)["status"])
        self.assertEqual(
            initial_config_payload,
            (
                initial_run.parent
                / str(initial_manifest["project_config"]["path"])
            ).resolve().read_bytes(),
        )

        started = self.invoke(
            "console",
            "start-run",
            config_path,
            "--run-id",
            "production",
        )
        self.assertIn("STARTED:", started.stdout)
        production_run = (
            self.project / "runs" / "production" / "run-manifest.json"
        )
        production_manifest = self.assert_config_binding(
            production_run,
            production_config_payload,
        )
        self.assertEqual([], production_manifest["artifacts"])
        self.assertEqual([], production_manifest["signoffs"])

        # Both argparse failures and semantic/integrity failures are public
        # exit-code 2 contracts and must leave existing documents untouched.
        config_before_duplicate = config_path.read_bytes()
        production_before_duplicate = production_run.read_bytes()
        duplicate = self.invoke(
            "module",
            "init",
            self.project,
            "--run-id",
            "production",
            expected=2,
        )
        self.assertIn("RED:", duplicate.stderr)
        self.assertEqual(config_before_duplicate, config_path.read_bytes())
        self.assertEqual(
            production_before_duplicate,
            production_run.read_bytes(),
        )
        syntax_error = self.invoke(
            "console",
            "preserve",
            self.source,
            "--artifact-id",
            "incomplete",
            expected=2,
        )
        self.assertIn("usage: xar-promo preserve", syntax_error.stderr)

        before_preserve = production_run.read_bytes()
        preserved = self.invoke(
            "module",
            "preserve",
            self.source,
            "--run-manifest",
            production_run,
            "--artifact-id",
            "final-video",
            "--collection",
            "derived",
            "--role",
            "deliverable",
            "--label",
            "Final video",
            "--media-type",
            "video/mp4",
        )
        self.assertIn("PRESERVED: id=final-video", preserved.stdout)
        self.assert_source_unchanged()
        self.assert_history_copy(production_run, before_preserve)

        after_preserve = production_run.read_bytes()
        manifest = read_json(production_run)
        self.assertEqual([], manifest["signoffs"])
        self.assertEqual(1, len(manifest["artifacts"]))
        artifact = manifest["artifacts"][0]
        self.assertEqual("final-video", artifact["id"])
        self.assertEqual(self.source_contract["size"], artifact["bytes"])
        self.assertEqual(self.source_contract["sha256"], artifact["sha256"])
        preserved_path = production_run.parent / str(artifact["path"])
        self.assertEqual(self.source.read_bytes(), preserved_path.read_bytes())
        self.assertIn(str(artifact["sha256"]), str(artifact["path"]))

        # Re-preserving the same ID and exact bytes is idempotent: neither the
        # manifest nor its history grows, while the source remains untouched.
        self.invoke(
            "console",
            "preserve",
            self.source,
            "--run-manifest",
            production_run,
            "--artifact-id",
            "final-video",
            "--collection",
            "derived",
            "--role",
            "deliverable",
            "--label",
            "Final video",
            "--media-type",
            "video/mp4",
        )
        self.assertEqual(after_preserve, production_run.read_bytes())
        self.assert_source_unchanged()

        authoring = self.invoke(
            "module", "validate", production_run, "--json"
        )
        authoring_result = json.loads(authoring.stdout)
        self.assertEqual("GREEN", authoring_result["status"])
        self.assertEqual(1, authoring_result["chapters"])
        self.assertEqual(1, authoring_result["artifacts"])
        unsigned_release = self.invoke(
            "console",
            "validate",
            production_run,
            "--profile",
            "release",
            expected=2,
        )
        self.assertIn("explicitly approved deliverable", unsigned_release.stderr)

        before_signoff = production_run.read_bytes()
        signed = self.invoke(
            "module",
            "signoff",
            "--run-manifest",
            production_run,
            "--artifact-id",
            "final-video",
            "--reviewer",
            "XenoAmess",
            "--decision",
            "approved",
            "--note",
            "Watched once at 1x",
            "--reviewed-at",
            "2026-09-01T00:00:00Z",
        )
        self.assertIn("RECORDED: id=signoff-000001", signed.stdout)
        self.assert_history_copy(production_run, before_signoff)
        final_manifest = read_json(production_run)
        self.assertEqual(1, len(final_manifest["signoffs"]))
        signoff = final_manifest["signoffs"][0]
        self.assertEqual("approved", signoff["decision"])
        self.assertEqual("XenoAmess", signoff["reviewer"])
        self.assertEqual(artifact["bytes"], signoff["artifact_bytes"])
        self.assertEqual(artifact["sha256"], signoff["artifact_sha256"])
        self.assert_source_unchanged()

        history_files = list(
            (
                production_run.parent
                / "artifacts"
                / "manifest-history"
            ).rglob("*.json")
        )
        self.assertEqual(2, len(history_files))
        self.assertEqual(
            {sha256_bytes(before_preserve), sha256_bytes(before_signoff)},
            {path.stem for path in history_files},
        )

        release = self.invoke(
            "console",
            "validate",
            production_run,
            "--profile",
            "release",
            "--json",
        )
        release_result = json.loads(release.stdout)
        self.assertEqual("GREEN", release_result["status"])
        self.assertEqual("release", release_result["profile"])
        self.assertEqual("run-manifest-v1", release_result["source_format"])
        self.assertTrue(release_result["files_checked"])


if __name__ == "__main__":
    unittest.main()

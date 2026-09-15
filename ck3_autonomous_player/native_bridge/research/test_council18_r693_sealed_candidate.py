from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

from council18_candidate_runtime_identity import (
    MODULE_PATHS,
    SOURCE_COMMIT,
    SOURCE_ROOT_RELATIVE,
    TOOL_MODULE_PATHS,
    assert_imported_module,
    build_source_identity,
    isolated_import_probe_command,
    verify_candidate_source,
)
from prepare_council18_r693_sealed_candidate import (
    SOURCE_HARNESS_COMMIT,
    SOURCE_PIPE,
    advance_rounds,
    copy_runtime,
    copy_sealed_inputs,
    patch_python_entrypoints,
    patch_text_bindings,
    verify_harness_commit,
    verify_runtime_repository,
)
from validate_private_probe_readiness_contract import driver_snapshot_api_contract


class Council18CandidateTests(unittest.TestCase):
    def test_harness_commit_must_be_a_repository_commit(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        with self.assertRaisesRegex(RuntimeError, "not a Git commit"):
            verify_harness_commit(repo_root, "f" * 40)

    def make_candidate(self, root: Path) -> tuple[Path, dict[str, object]]:
        source_root = root / SOURCE_ROOT_RELATIVE
        for index, (name, relative) in enumerate(MODULE_PATHS.items()):
            path = source_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {name}\nVALUE = {index}\n", encoding="utf-8")
        tools_root = root / "source-repo/tools"
        for name, relative in TOOL_MODULE_PATHS.items():
            path = tools_root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {name}\n", encoding="utf-8")
        identity = build_source_identity(root / "source-repo")
        identity_path = root / "source-repo/source-identity.json"
        identity_path.parent.mkdir(parents=True, exist_ok=True)
        identity_path.write_text(json.dumps(identity) + "\n", encoding="utf-8")
        return source_root, identity

    def test_candidate_local_tree_and_commit_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            expected_root, expected_identity = self.make_candidate(root)
            source_root, identity = verify_candidate_source(root)
            self.assertEqual(source_root, expected_root.resolve())
            self.assertEqual(identity, expected_identity)
            self.assertEqual(
                identity["source_commit"],
                "41bd2d5d0c159676876f21adc3845cf0afeeaf97",
            )
            self.assertFalse(identity["external_workspace_root_allowed"])

    def test_source_byte_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root, _ = self.make_candidate(root)
            (source_root / MODULE_PATHS["xar_autoplayer.runtime"]).write_text(
                "changed\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(RuntimeError, "inventory differs"):
                verify_candidate_source(root)

    def test_imported_module_must_resolve_to_sealed_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_root, identity = self.make_candidate(root)
            name = "xar_autoplayer.bridge.native_driver"
            module = types.ModuleType(name)
            module.__file__ = str(source_root / MODULE_PATHS[name])
            assert_imported_module(
                module,
                expected_name=name,
                source_root=source_root,
                identity=identity,
            )
            module.__file__ = str(root / "external/native_driver.py")
            with self.assertRaisesRegex(RuntimeError, "escaped candidate source"):
                assert_imported_module(
                    module,
                    expected_name=name,
                    source_root=source_root,
                    identity=identity,
                )

    def test_round_pair_advances_without_cascading(self) -> None:
        self.assertEqual(
            advance_rounds("R691 -> R692; run_r692.py; live-r692"),
            "R692 -> R693; run_r693.py; live-r693",
        )

    def test_copy_uses_sealed_rows_without_live_or_control_extras(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            output = root / "output"
            kept = source / "fresh-profile-state/profile/input.json"
            kept.parent.mkdir(parents=True)
            kept.write_text("{}\n", encoding="utf-8")
            live = source / "live-r692/report.json"
            live.parent.mkdir(parents=True)
            live.write_text("red\n", encoding="utf-8")
            control = source / "fresh-profile-state/control/unsafe-cleanup.json"
            control.parent.mkdir(parents=True)
            control.write_text("unsafe\n", encoding="utf-8")
            copy_sealed_inputs(
                source,
                output,
                [
                    {
                        "path": "fresh-profile-state/profile/input.json",
                        "size_bytes": kept.stat().st_size,
                        "sha256": self.file_sha256(kept),
                    }
                ],
            )
            self.assertTrue(
                (output / "fresh-profile-state/profile/input.json").is_file()
            )
            self.assertFalse((output / "live-r692").exists())
            self.assertFalse((output / "fresh-profile-state/control").exists())

    def test_text_bindings_use_the_new_root_pipe_and_harness(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "g2-m4-council16-r692-source"
            output = root / "g2-m4-council18-r693-newhash"
            output.mkdir()
            target_commit = "1" * 40
            target_pipe = r"\\.\pipe\xar_ck3_bridge_g2_m4_council18_r693_1111111"
            python_template = (
                f"COUNCIL16 R691 R692 r692 {SOURCE_HARNESS_COMMIT} {SOURCE_PIPE}\n"
            )
            for name in ("run_r692.py", "invoke_r692.py", "verify_prep.py"):
                (output / name).write_text(python_template, encoding="utf-8")
            text_template = f"{source} R691 R692 r692 {SOURCE_HARNESS_COMMIT} {SOURCE_PIPE}\n"
            for name in (
                "execute-command.txt",
                "preflight-command.txt",
                "R692-start-checklist.md",
            ):
                (output / name).write_text(text_template, encoding="utf-8")

            patch_python_entrypoints(output, target_commit, target_pipe)
            patch_text_bindings(source, output, target_commit, target_pipe)

            for name in (
                "run_r693.py",
                "invoke_r693.py",
                "verify_prep.py",
                "execute-command.txt",
                "preflight-command.txt",
                "R693-start-checklist.md",
            ):
                text = (output / name).read_text(encoding="utf-8")
                self.assertIn(target_commit, text)
                self.assertIn(target_pipe, text)
                self.assertNotIn(SOURCE_PIPE, text)
            execute = (output / "execute-command.txt").read_text(encoding="utf-8")
            self.assertIn(str(output), execute)
            self.assertNotIn(str(source), execute)

    @staticmethod
    def file_sha256(path: Path) -> str:
        import hashlib

        return hashlib.sha256(path.read_bytes()).hexdigest().upper()

    def test_frozen_runtime_has_snapshot_api_and_pythoncom_fix(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        paths = verify_runtime_repository(repo_root)
        driver_relative = Path(
            "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
        )
        process_relative = Path(
            "ck3_autonomous_player/src/xar_autoplayer/windows_process.py"
        )
        self.assertIn(driver_relative, paths)
        self.assertIn(process_relative, paths)
        driver_source = subprocess.run(
            ["git", "show", f"{SOURCE_COMMIT}:{driver_relative.as_posix()}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        contract = driver_snapshot_api_contract(driver_source)
        self.assertEqual(contract["method"], "take_internal_semantic_snapshot")
        process_source = subprocess.run(
            ["git", "show", f"{SOURCE_COMMIT}:{process_relative.as_posix()}"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
        release = process_source.index("output = None")
        shutdown = process_source.rindex("pythoncom.CoUninitialize()")
        self.assertLess(release, shutdown)

    def test_isolated_import_closure_from_temporary_staging(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        research_root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temporary:
            candidate_root = Path(temporary)
            copy_runtime(
                repo_root,
                candidate_root,
                verify_runtime_repository(repo_root),
            )
            shutil.copyfile(
                research_root / "council18_candidate_runtime_identity.py",
                candidate_root / "candidate_runtime_identity.py",
            )
            shutil.copyfile(
                research_root / "council18_candidate_runtime_import_probe.py",
                candidate_root / "candidate_runtime_import_probe.py",
            )
            environment = os.environ.copy()
            environment.pop("PYTHONPATH", None)
            environment.pop("PYTHONHOME", None)
            result = subprocess.run(
                isolated_import_probe_command(
                    Path(sys.executable), candidate_root, optimized=not __debug__
                ),
                cwd=candidate_root,
                env=environment,
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "green")
            self.assertEqual(
                payload["mode"], "optimized" if not __debug__ else "normal"
            )
            for path in payload["module_files"].values():
                Path(path).resolve().relative_to(candidate_root.resolve())


if __name__ == "__main__":
    unittest.main()

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

from candidate_runtime_identity import (
    MODULE_PATHS,
    SOURCE_COMMIT,
    SOURCE_ROOT_RELATIVE,
    TOOL_MODULE_PATHS,
    assert_imported_module,
    build_source_identity,
    isolated_import_probe_command,
    verify_candidate_source,
)
from prepare_council14_r691_self_contained_runtime_candidate import (
    copy_runtime,
    verify_runtime_repository,
)
from validate_private_probe_readiness_contract import driver_snapshot_api_contract


class CandidateRuntimeIdentityTests(unittest.TestCase):
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
            self.assertEqual(identity["source_commit"], SOURCE_COMMIT)
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

    def test_source_commit_identity_drift_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.make_candidate(root)
            identity_path = root / "source-repo/source-identity.json"
            identity = json.loads(identity_path.read_text(encoding="utf-8"))
            identity["source_commit"] = "0" * 40
            identity_path.write_text(json.dumps(identity), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "source_commit differs"):
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

    def test_master_runtime_tree_has_internal_snapshot_api(self) -> None:
        repo_root = Path(__file__).resolve().parents[3]
        paths = verify_runtime_repository(repo_root)
        self.assertIn(
            Path("ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"),
            paths,
        )
        driver_source = (
            repo_root
            / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
        ).read_text(encoding="utf-8-sig")
        contract = driver_snapshot_api_contract(driver_source)
        self.assertEqual(contract["method"], "take_internal_semantic_snapshot")
        self.assertEqual(contract["positional_arguments"], [])

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
            for name in (
                "candidate_runtime_identity.py",
                "candidate_runtime_import_probe.py",
            ):
                shutil.copyfile(research_root / name, candidate_root / name)
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

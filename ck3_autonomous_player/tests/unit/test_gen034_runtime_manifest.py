"""Offline regressions for the GEN-034-D executing-source closure."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "native_bridge" / "research" / "gen034_runtime_manifest.py"
SPEC = importlib.util.spec_from_file_location("gen034_runtime_manifest_tested", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RUNTIME = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = RUNTIME
SPEC.loader.exec_module(RUNTIME)


def _minimal_runtime(root: Path) -> None:
    for relative in sorted(RUNTIME.REQUIRED_PATHS):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {relative}\n", encoding="utf-8")


class Gen034RuntimeManifestTests(unittest.TestCase):
    def test_manifest_binds_all_required_planning_and_action_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _minimal_runtime(root)
            manifest = RUNTIME.build_runtime_file_manifest(
                root, source_commit="fixture"
            )
            output = root / "runtime.json"
            RUNTIME._write_json_atomic(output, manifest)

            receipt = RUNTIME.verify_runtime_file_manifest(
                output,
                runtime_root=root,
                expected_manifest_sha256=RUNTIME.sha256_file(output),
            )

            self.assertEqual(receipt["status"], "verified")
            self.assertEqual(receipt["file_count"], len(RUNTIME.REQUIRED_PATHS))
            self.assertTrue(RUNTIME.REQUIRED_PATHS <= {
                row["path"] for row in manifest["files"]
            })

    def test_tampered_native_auto_run_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _minimal_runtime(root)
            output = root / "runtime.json"
            RUNTIME._write_json_atomic(
                output,
                RUNTIME.build_runtime_file_manifest(root, source_commit="fixture"),
            )
            target = root / (
                "ck3_autonomous_player/src/xar_autoplayer/native_auto_run.py"
            )
            target.write_text("# tampered\n", encoding="utf-8")

            with self.assertRaisesRegex(
                RUNTIME.RuntimeManifestError, "runtime source closure drifted"
            ):
                RUNTIME.verify_runtime_file_manifest(
                    output,
                    runtime_root=root,
                    expected_manifest_sha256=RUNTIME.sha256_file(output),
                )


if __name__ == "__main__":
    unittest.main()

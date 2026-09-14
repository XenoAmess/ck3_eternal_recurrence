"""Focused contract tests for the bounded private-probe wrapper generator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
MODULE_PATH = HERE / "generate_bounded_private_probe_wrapper.py"
SPEC = importlib.util.spec_from_file_location("bounded_wrapper", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("cannot load wrapper generator")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class BoundedWrapperTest(unittest.TestCase):
    def test_legacy_one_slash_prefix_is_rejected(self) -> None:
        legacy = r"\.\pipe\xar_ck3_bridge_g2_m4_r688_military_432545e"
        with self.assertRaisesRegex(ValueError, "must start"):
            MODULE.validate_named_pipe(legacy)

    def test_generated_dry_run_preserves_manifest_pipe(self) -> None:
        canonical = r"\\.\pipe\xar_ck3_bridge_test_123"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = {
                "source-save/save.ck3": b"save",
                "bin/bridge.dll": b"dll",
                "bin/injector.exe": b"injector",
                "game/binaries/ck3.exe": b"exe",
                "source-repo/tools/bootstrap.py": b"raise SystemExit(99)\n",
            }
            for relative, data in files.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            manifest = root / "candidate-manifest.json"
            manifest.write_text(
                json.dumps({"next_live": {"unique_pipe": canonical}}),
                encoding="utf-8",
            )
            wrapper = root / "run.ps1"
            wrapper.write_text(
                MODULE.render_wrapper(
                    manifest_relative="candidate-manifest.json",
                    bootstrap_relative="source-repo/tools/bootstrap.py",
                    save_relative="source-save/save.ck3",
                    dll_relative="bin/bridge.dll",
                    injector_relative="bin/injector.exe",
                    save_name="save.ck3",
                    expected_save_sha256=sha256(root / "source-save/save.ck3"),
                    expected_dll_sha256=sha256(root / "bin/bridge.dll"),
                    expected_injector_sha256=sha256(root / "bin/injector.exe"),
                    expected_game_exe_sha256=sha256(root / "game/binaries/ck3.exe"),
                    expected_character_id=29829,
                    old_round="R687",
                    new_round="R688",
                    candidate_revision="4" * 40,
                    publish_timeout=20,
                ),
                encoding="utf-8-sig",
            )
            completed = subprocess.run(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(wrapper),
                    "-Python",
                    sys.executable,
                    "-GameDir",
                    str(root / "game"),
                    "-ArtifactDir",
                    str(root / "artifact"),
                    "-StateDir",
                    str(root / "state"),
                    "-DryRun",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "green")
            self.assertFalse(payload["ck3_launched"])
            self.assertEqual(payload["manifest_pipe"], canonical)
            self.assertEqual(payload["argument_pipe"], canonical)
            self.assertEqual(
                payload["argument_pipe_utf16"], [ord(value) for value in canonical]
            )


if __name__ == "__main__":
    unittest.main()

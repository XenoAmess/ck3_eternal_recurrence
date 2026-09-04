from __future__ import annotations

from argparse import Namespace
import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("freeze_zg361_b3_b7_next_run.py")
SPEC = importlib.util.spec_from_file_location("b3_b7_freeze", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
freeze = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(freeze)


class B3B7NextRunFreezeTests(unittest.TestCase):
    def test_path_gate_uses_final_materialized_mount(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "b3k"
            verdict = freeze.verify_paths(
                artifacts,
                ["common/scripted_effects/short_effects.txt"],
            )
            self.assertTrue(verdict["green"])
            self.assertIn(
                "_native_state\\profile\\mod-content\\zhongguo_361",
                verdict["longest_mounted_path"],
            )

    def test_path_gate_rejects_250_characters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            artifacts = Path(temporary) / "b3k"
            mount_root = (
                Path(str(artifacts) + "_native_state")
                / "profile"
                / "mod-content"
                / "zhongguo_361"
            )
            relative = "x" * (freeze.MOUNT_PATH_LIMIT - len(str(mount_root)) - 1)
            with self.assertRaisesRegex(freeze.FreezeError, "not below 250"):
                freeze.verify_paths(artifacts, [relative])

    def test_pipe_token_is_strict_lowercase_hex(self) -> None:
        self.assertIsNotNone(freeze.PIPE_TOKEN.fullmatch("1" * 32))
        self.assertIsNone(freeze.PIPE_TOKEN.fullmatch("A" * 32))
        self.assertIsNone(freeze.PIPE_TOKEN.fullmatch("1" * 31))


if __name__ == "__main__":
    unittest.main()

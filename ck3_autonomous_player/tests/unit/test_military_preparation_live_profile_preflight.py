from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = (
    ROOT
    / "native_bridge"
    / "research"
    / "verify_military_preparation_live_profile.py"
)
SPEC = importlib.util.spec_from_file_location("military_profile_preflight", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class MilitaryPreparationLiveProfilePreflightTest(unittest.TestCase):
    def _profile(self, root: Path, *, stage_wrapper: bool) -> tuple[Path, Path]:
        profile = root / "profile"
        production = profile / "mod-content" / "xar-production"
        outer = profile / "mod" / "xar_autoplayer.mod"
        outer.parent.mkdir(parents=True)
        production.mkdir(parents=True)
        outer.write_text(
            f'path="{production.as_posix()}"\n', encoding="utf-8"
        )
        (profile / "dlc_load.json").write_text(
            json.dumps({"enabled_mods": ["mod/xar_autoplayer.mod"]}),
            encoding="utf-8",
        )
        expected = (
            ROOT
            / "mod_bridge"
            / MODULE.WRAPPER_RELATIVE_PATH
        )
        if stage_wrapper:
            target = production / MODULE.WRAPPER_RELATIVE_PATH
            target.parent.mkdir(parents=True)
            target.write_bytes(expected.read_bytes())
        return profile, expected

    def test_missing_wrapper_is_red(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, expected = self._profile(Path(temporary), stage_wrapper=False)
            result = MODULE.inspect_profile(profile, expected)
        self.assertEqual(result["status"], "red")
        self.assertFalse(result["checks"]["exactly_one_loaded_wrapper_provider"])

    def test_one_byte_identical_loaded_provider_is_green(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            profile, expected = self._profile(Path(temporary), stage_wrapper=True)
            result = MODULE.inspect_profile(profile, expected)
        self.assertEqual(result["status"], "green")
        self.assertTrue(result["checks"]["loaded_wrapper_byte_identical"])


if __name__ == "__main__":
    unittest.main()

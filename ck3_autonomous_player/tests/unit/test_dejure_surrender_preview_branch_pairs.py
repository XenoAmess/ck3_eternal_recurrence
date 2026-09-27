"""Replay the WAR31 static receipt against the exact installed executable."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_surrender_preview_branch_pairs.py"
FIXTURE = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_surrender_preview_branch_pairs_1_19_0_6.json"
EXE = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe")


def _load_extractor():
    spec = importlib.util.spec_from_file_location("dejure_preview_branch_pairs", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    importlib.util.find_spec("capstone") and importlib.util.find_spec("pefile"),
    "static reverse-engineering dependencies are unavailable",
)
class DeJureSurrenderPreviewBranchPairTests(unittest.TestCase):
    def test_wrong_build_fails_closed(self) -> None:
        extractor = _load_extractor()
        with tempfile.TemporaryDirectory() as temp:
            wrong = Path(temp) / "ck3.exe"
            wrong.write_bytes(b"not the frozen build")
            with self.assertRaisesRegex(ValueError, "differs from frozen"):
                extractor.extract(wrong)

    @unittest.skipUnless(EXE.is_file(), "exact CK3 executable is unavailable")
    def test_exact_exe_matches_frozen_branch_receipt(self) -> None:
        extractor = _load_extractor()
        observed = extractor.extract(EXE)
        expected = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        self.assertEqual(observed["status"], "STATIC_INTERMEDIATE_TUPLES_ONLY")
        self.assertFalse(observed["interpretation"]["ck3_launched"])


if __name__ == "__main__":
    unittest.main()

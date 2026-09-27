"""Replay the exact-build WAR31 resolve gate without loading CK3."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "ck3_autonomous_player/native_bridge/research/extract_dejure_resolve_prequeue_gate.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/dejure_resolve_prequeue_gate_1_19_0_6.json"
EXE = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe")


def load_extractor():
    spec = importlib.util.spec_from_file_location(SCRIPT.stem, SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("WAR31 extractor cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(
    importlib.util.find_spec("capstone") and importlib.util.find_spec("pefile"),
    "static reverse-engineering dependencies are unavailable",
)
class DeJureResolvePrequeueGateTests(unittest.TestCase):
    def test_wrong_executable_fails_closed(self) -> None:
        extractor = load_extractor()
        with tempfile.TemporaryDirectory() as temp:
            wrong = Path(temp) / "ck3.exe"
            wrong.write_bytes(b"not the exact executable")
            with self.assertRaisesRegex(ValueError, "differs from frozen"):
                extractor.extract(wrong)

    @unittest.skipUnless(EXE.is_file(), "exact CK3 executable is unavailable")
    def test_exact_executable_replays_receipt(self) -> None:
        observed = load_extractor().extract(EXE)
        expected = json.loads(RECEIPT.read_text(encoding="utf-8"))
        self.assertEqual(observed, expected)
        self.assertEqual(observed["status"], "STATIC_PREQUEUE_GATE_ONLY")
        self.assertEqual(observed["wrapper_0x27CD510"]["processor_call"]["target_rva"], "0x24CC9A0")
        self.assertFalse(observed["boundary"]["ck3_launched"])


if __name__ == "__main__":
    unittest.main()

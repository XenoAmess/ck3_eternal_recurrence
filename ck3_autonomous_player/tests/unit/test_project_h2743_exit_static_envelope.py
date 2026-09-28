"""Exact-source and H2743 identity gates for the static exit envelope."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "ck3_autonomous_player/native_bridge/research/project_h2743_exit_static_envelope.py"
RECEIPT = ROOT / "ck3_autonomous_player/native_bridge/research/h2743_exit_static_resource_envelope_1_19_0_6.json"
GAME = Path("C:/SteamLibrary/steamapps/common/Crusader Kings III")


def _module():
    spec = importlib.util.spec_from_file_location(SOURCE.stem, SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class H2743StaticEnvelopeTests(unittest.TestCase):
    def test_changed_exact_source_fails_closed(self) -> None:
        module = _module()
        with tempfile.TemporaryDirectory() as temporary:
            fake_game = Path(temporary)
            exe = fake_game / "binaries/ck3.exe"
            exe.parent.mkdir(parents=True)
            exe.write_bytes(b"not the exact build")
            with self.assertRaisesRegex(ValueError, "exact source SHA mismatch"):
                module.project(fake_game)

    @unittest.skipUnless((GAME / "binaries/ck3.exe").is_file(), "exact game unavailable")
    def test_changed_h2743_frame_fails_closed(self) -> None:
        module = _module()
        with tempfile.TemporaryDirectory() as temporary:
            altered = Path(temporary) / "h2743.json"
            payload = json.loads(module.FRAME.read_text(encoding="utf-8"))
            payload["frame"]["war_id"] += 1
            altered.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "exact source SHA mismatch"):
                module.project(GAME, altered)

    @unittest.skipUnless((GAME / "binaries/ck3.exe").is_file(), "exact game unavailable")
    def test_exact_projection_keeps_material_unknown(self) -> None:
        observed = _module().project()
        self.assertEqual(observed, json.loads(RECEIPT.read_text(encoding="utf-8")))
        self.assertEqual(observed["truce"]["script_direction"], {"owner": 30097, "toward": 29829})
        self.assertIsNone(observed["factor"]["actual_raw_q100000"])
        self.assertIsNone(observed["signed_total_resource_deltas"])
        self.assertIsNone(observed["truce"]["evaluated_days"])
        self.assertFalse(observed["comparison_ready"])


if __name__ == "__main__":
    unittest.main()

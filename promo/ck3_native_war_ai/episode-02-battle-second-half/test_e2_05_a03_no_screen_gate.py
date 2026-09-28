"""Fail-closed fixtures for the a03 no-screen source and post-save gates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import e2_05_a03_no_screen_gate as gate


def write(path: Path, data: bytes) -> str:
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest().upper()


def receipt(save: Path, date: int) -> dict:
    return {
        "result": "CALL_COMPLETED",
        "body": {
            "step": "save-checkpoint", "accepted": True,
            "submission": {"date_raw": date},
            "checkpoint": {
                "status": "saved", "name": "xar_checkpoint.ck3",
                "date_raw": date, "episode_character_id": gate.ACTOR,
                "path": "C:/isolated-profile/save games/xar_checkpoint.ck3",
                "size": save.stat().st_size,
                "sha256": gate._sha(save).lower(),
            },
        },
        "driver_state": {"hello": {
            "expected_ck3_sha256": gate.CK3_SHA,
            "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
            "ck3_build_match": True, "bridge_version": "0.1.0",
        }},
    }


class GateTests(unittest.TestCase):
    def test_old_dll_rejected_even_with_new_injector(self) -> None:
        with tempfile.TemporaryDirectory() as temp, \
                patch.object(gate, "SOURCE_SAVE_SHA", hashlib.sha256(b"source").hexdigest().upper()), \
                patch.object(gate, "OLD_DLL_SHA", hashlib.sha256(b"old-dll").hexdigest().upper()):
            root = Path(temp)
            save = root / "d26.ck3"
            source_sha = write(save, b"source")
            self.assertEqual(source_sha, gate.SOURCE_SAVE_SHA)
            source_receipt = root / "receipt.json"
            receipt_sha = write(source_receipt, json.dumps(receipt(save, gate.D26)).encode())
            with patch.object(gate, "SOURCE_RECEIPT_SHA", receipt_sha):
                dll = root / "old.dll"
                dll_sha = write(dll, b"old-dll")
                injector = root / "new.exe"
                injector_sha = write(injector, b"new-injector")
                with self.assertRaisesRegex(gate.GateRed, "predates selector ring"):
                    gate.source_gate(save, source_receipt, dll, injector,
                                     dll_sha, injector_sha)

    def test_d27_requires_paused_advance_and_exact_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            save = root / "d27.ck3"
            save_sha = write(save, b"new independent day27 bytes")
            response = root / "d27-save.json"
            receipt_sha = write(response, json.dumps(receipt(save, gate.D27)).encode())
            advance = root / "advance.json"
            step = {"mode": "advance", "track": "e2-05-d26",
                    "result": "ONE_DAY_ADVANCED_UNREVIEWED",
                    "post_values": {"date_raw": gate.D27, "paused": True,
                                    "actor": gate.ACTOR, "revision": 8},
                    "trace_finish": {"response": {"sha256": "A" * 64}},
                    "one_day": {"response": {"sha256": "B" * 64}}}
            advance_sha = write(advance, json.dumps(step).encode())
            result = gate.d27_checkpoint_gate(save, save_sha, response,
                                              receipt_sha, advance, advance_sha)
            self.assertTrue(result["saved_day27_bytes_verified"])
            self.assertFalse(result["character_status_proven"])
            self.assertFalse(result["live_admission"])
            step["post_values"]["paused"] = False
            advance_sha = write(advance, json.dumps(step).encode())
            with self.assertRaisesRegex(gate.GateRed, "paused d27"):
                gate.d27_checkpoint_gate(save, save_sha, response,
                                         receipt_sha, advance, advance_sha)
            step["post_values"]["paused"] = True
            advance_sha = write(advance, json.dumps(step).encode())
            bad = receipt(save, gate.D26)
            receipt_sha = write(response, json.dumps(bad).encode())
            with self.assertRaisesRegex(gate.StatusUnknown, "checkpoint receipt"):
                gate.d27_checkpoint_gate(save, save_sha, response,
                                         receipt_sha, advance, advance_sha)


if __name__ == "__main__":
    unittest.main()

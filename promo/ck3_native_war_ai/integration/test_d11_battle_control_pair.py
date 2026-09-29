"""No-launch regression for the R0107 old-DLL/current-validator mismatch."""

import json
from pathlib import Path
import runpy
import tempfile
import unittest

from capture_session import (
    A04_UI_TARGETS, BATTLE_CONTROL_PAIR_SCHEMA, BATTLE_CONTROL_WIRE_MARKERS,
    identity, validate_d11_battle_control_pair,
)


REPO = Path(__file__).resolve().parents[3]
NATIVE = REPO / "ck3_autonomous_player" / "native_bridge"
OLD_DLL = Path(
    "D:/wai/ck3_autonomous_player/native_bridge/"
    "build-fresh-20260927T025104Z-572e2125/xar_ck3_bridge.dll"
)
OLD_SHA = "1CC2AE965CD0EE897F918D50AF038F3DA874354DA7F3A57D2710B7BCCF44366F"


def fingerprint() -> str:
    return runpy.run_path(str(NATIVE / "tools" / "build_fresh.py"))[
        "native_bridge_source_fingerprint"
    ](NATIVE)


def d11_checkpoint() -> dict:
    return {"save": {"sha256": A04_UI_TARGETS["e2-06-d11"]["save"][2]}}


class D11BattleControlPairTest(unittest.TestCase):
    def pair(self, root: Path, dll: Path, injector: Path) -> Path:
        from xar_autoplayer.bridge import battle_control_contract

        report = root / "focused-build-report.json"
        report.write_text('{"status":"READY","ctest":"PASS"}\n', encoding="utf-8")
        manifest = root / "pair.json"
        row = {
            "schema": BATTLE_CONTROL_PAIR_SCHEMA,
            "build_status": "READY",
            "build_report": {"path": str(report), "sha256": identity(report)["sha256"]},
            "source_fingerprint_sha256": fingerprint(),
            "native_serializer_sha256": identity(
                NATIVE / "src" / "battle_control_snapshot_v1_mailbox.cpp"
            )["sha256"],
            "python_contract_sha256": identity(Path(battle_control_contract.__file__))["sha256"],
            "dll_sha256": identity(dll)["sha256"],
            "injector_sha256": identity(injector)["sha256"],
            "battle_control_ctest_passed": True,
        }
        manifest.write_text(json.dumps(row), encoding="utf-8")
        return manifest

    def test_current_wire_shape_and_source_pair_admitted_as_static_only(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll, injector = root / "current.dll", root / "injector.exe"
            dll.write_bytes(b"\0".join(BATTLE_CONTROL_WIRE_MARKERS))
            injector.write_bytes(b"fixture injector")
            pair = self.pair(root, dll, injector)
            result = validate_d11_battle_control_pair(d11_checkpoint(), pair, dll, injector)
            self.assertTrue(result["wire_markers_present"])
            self.assertFalse(result["native_query_verified"])
            manifest = json.loads(pair.read_text(encoding="utf-8"))
            manifest["python_contract_sha256"] = "0" * 64
            pair.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "source pair differs"):
                validate_d11_battle_control_pair(d11_checkpoint(), pair, dll, injector)

    def test_old_wire_rejected_even_with_matching_binary_hash(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            dll, injector = root / "legacy.dll", root / "injector.exe"
            dll.write_bytes(b"side_0_current_roll_points\0side_1_current_roll_points")
            injector.write_bytes(b"fixture injector")
            pair = self.pair(root, dll, injector)
            with self.assertRaisesRegex(RuntimeError, "lacks current battle-control"):
                validate_d11_battle_control_pair(d11_checkpoint(), pair, dll, injector)

    @unittest.skipUnless(OLD_DLL.is_file(), "R0107 exact old DLL is not present")
    def test_r0107_pinned_old_dll_rejected_before_launch(self) -> None:
        self.assertEqual(identity(OLD_DLL)["sha256"], OLD_SHA)
        self.assertIn(b"side_0_current_roll_points", OLD_DLL.read_bytes())
        self.assertNotIn(BATTLE_CONTROL_WIRE_MARKERS[0], OLD_DLL.read_bytes())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            injector = root / "injector.exe"
            injector.write_bytes(b"fixture injector")
            pair = self.pair(root, OLD_DLL, injector)
            with self.assertRaisesRegex(RuntimeError, "lacks current battle-control"):
                validate_d11_battle_control_pair(d11_checkpoint(), pair, OLD_DLL, injector)

    def test_d11_requires_manifest_and_other_tracks_reject_it(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "manifest is required"):
            validate_d11_battle_control_pair(d11_checkpoint(), None, Path("missing"), Path("missing"))
        with self.assertRaisesRegex(RuntimeError, "only for the exact d11"):
            validate_d11_battle_control_pair(None, Path("unused.json"), Path("missing"), Path("missing"))


if __name__ == "__main__":
    unittest.main()

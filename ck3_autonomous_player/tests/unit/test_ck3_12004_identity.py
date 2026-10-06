"""Offline whole-frame identity/provenance fixture; no native qualification."""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.nonwar_private_build import (
    private_native_provenance,
    private_native_readback_matches,
    private_native_schema,
)
from xar_autoplayer.bridge.version_identity import (
    CK3_11906, CK3_12002, CK3_12003, CK3_12004,
    require_exact_native_backend,
    require_exact_native_build,
)


class Ck3_12004IdentityTests(unittest.TestCase):
    def test_paused_native_frame_preserves_new_identity_and_private_provenance(self):
        # NativeProtocolState is an in-memory consumer, not a pipe endpoint.
        state = NativeProtocolState(r"\\.\pipe\xar_12004_offline_identity_fixture")
        state.ingest({
            "protocol_version": 1,
            "type": "hello",
            "pid": 1234,
            "connection_generation": 7,
            "capabilities": ["game.state.snapshot"],
            "game_adapter_status": "ready",
            "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": (
                "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"
            ),
        })
        state.ingest({
            "protocol_version": 1,
            "type": "state_snapshot",
            "snapshot_id": "12004-paused-identity-fixture",
            "revision": 23,
            "state": {
                "date_raw": 10660915,
                "speed": 1,
                "paused": True,
                "map_ready": True,
                "active_wars": [],
                "player_armies": [],
            },
        })
        snapshot = state.semantic_snapshot()
        self.assertIs(snapshot["paused"], True)
        self.assertEqual(snapshot["native_revision"], 23)
        self.assertEqual(snapshot["diagnostics"]["bridge_pid"], 1234)
        self.assertEqual(snapshot["diagnostics"]["connection_generation"], 7)
        provenance = private_native_provenance(snapshot)
        self.assertEqual(provenance, {
            "exact_ck3_build": "1.20.0.4",
            "exe_sha256": (
                "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
            ),
        })
        self.assertTrue(private_native_readback_matches(snapshot, provenance))
        for prefix in ("ck3_12002_", "ck3_12003_", "ck3_12004_"):
            self.assertEqual(
                private_native_schema(prefix + "private_query_v1", snapshot),
                "ck3_12004_private_query_v1",
            )
        backend = CK3_12004.backend_id("campaign-root-context-v1")
        self.assertEqual(require_exact_native_backend(
            "1.20.0.4", provenance["exe_sha256"], backend,
            suffix="campaign-root-context-v1",
        ), CK3_12004)

        for old in (CK3_11906, CK3_12002, CK3_12003):
            with self.subTest(old_version=old.game_version):
                self.assertEqual(require_exact_native_build(
                    old.game_version, old.executable_sha256.lower(),
                ), old)
                self.assertFalse(private_native_readback_matches(snapshot, {
                    "exact_ck3_build": old.game_version,
                    "exe_sha256": old.executable_sha256,
                }))
                with self.assertRaises(ValueError):
                    require_exact_native_build("1.20.0.4", old.executable_sha256)
                with self.assertRaises(ValueError):
                    require_exact_native_build(old.game_version, CK3_12004.executable_sha256)
        mixed = {"diagnostics": {"hello": {
            "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": CK3_12003.executable_sha256,
        }}}
        with self.assertRaises(BridgeUnavailableError):
            private_native_provenance(mixed)
        self.assertEqual(private_native_provenance({}), {
            "exact_ck3_build": "1.19.0.6",
        })


if __name__ == "__main__":
    unittest.main()

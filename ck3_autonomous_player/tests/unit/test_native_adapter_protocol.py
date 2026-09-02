from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState


class NativeAdapterProtocolCompatibilityTests(unittest.TestCase):
    def test_protocol_v1_legacy_hello_remains_accepted(self) -> None:
        state = NativeProtocolState(r"\\.\pipe\legacy-fixture")

        state.ingest(
            {
                "type": "hello",
                "protocol_version": 1,
                "bridge_version": "0.1.0",
                "pid": 101,
                "session_generation": 0,
                "capabilities": ["bridge.identity", "bridge.heartbeat"],
            }
        )

        capabilities = state.capabilities()
        self.assertEqual(
            capabilities["bridge_capabilities"],
            ["bridge.identity", "bridge.heartbeat"],
        )
        self.assertTrue(capabilities["diagnostics"]["connected"])
        self.assertEqual(capabilities["action_steps"], [])

    def test_adapter_metadata_extends_v1_without_changing_semantics(self) -> None:
        state = NativeProtocolState(r"\\.\pipe\adapter-fixture")

        state.ingest(
            {
                "type": "hello",
                "protocol_version": 1,
                "bridge_version": "0.1.0",
                "pid": 102,
                "session_generation": 0,
                "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                "game_adapter_status": "ready",
                "expected_ck3_version": "1.19.0.6",
                "expected_ck3_sha256": "2" * 64,
                "ck3_build_match": True,
                "capabilities": [
                    "bridge.identity",
                    "game.state.snapshot",
                    "game.command.pause-map",
                ],
            }
        )
        state.ingest(
            {
                "type": "state_snapshot",
                "protocol_version": 1,
                "snapshot_id": "native:1",
                "revision": 1,
                "state": {
                    "phase": "map_hud",
                    "history": [],
                    "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": None,
                    "active_wars": [],
                    "player_armies": [],
                },
            }
        )

        capabilities = state.capabilities()
        self.assertTrue(capabilities["snapshot"])
        self.assertEqual(capabilities["action_steps"], ["pause-map"])
        hello = capabilities["diagnostics"]["hello"]
        self.assertEqual(hello["game_adapter_id"], "ck3-1.19.0.6-msvc-x64")
        self.assertEqual(hello["game_adapter_status"], "ready")
        self.assertEqual(state.semantic_snapshot()["snapshot_id"], "native:1")

    def test_termination_terms_capability_expands_concrete_step_from_paused_war(
        self,
    ) -> None:
        """Keep the current Python advertisement boundary explicit.

        The old G2 evidence captured only the native ``-N`` capability and
        consequently failed its concrete action-step check.  The current
        protocol state must expand that parameterized capability only after a
        paused semantic frame with a positive full-generation WarID arrives;
        it must never expose the ``-N`` template as an executable literal.
        """
        state = NativeProtocolState(r"\\.\pipe\termination-terms-fixture")
        state.ingest(
            {
                "type": "hello",
                "protocol_version": 1,
                "bridge_version": "0.1.0",
                "pid": 104,
                "session_generation": 0,
                "capabilities": [
                    "bridge.identity",
                    "game.state.snapshot",
                    "game.command.query-war-termination-terms-v1-N",
                ],
            }
        )
        state.ingest(
            {
                "type": "state_snapshot",
                "protocol_version": 1,
                "snapshot_id": "native:40",
                "revision": 40,
                "state": {
                    "phase": "map_hud",
                    "date": "1066.9.15",
                    "date_raw": 53_171_400,
                    "speed": 1,
                    "paused": True,
                    "map_ready": True,
                    "history": [],
                    "active_event": None,
                    "pending_character_interaction": None,
                    "played_character": {
                        "character_id": 707,
                        "alive": True,
                    },
                    "active_wars": [
                        {
                            "war_id": 50_331_699,
                            "player_side": "attacker",
                            "primary_opponent_character_id": 808,
                            "player_is_primary_war_leader": True,
                            "enemy_primary_default_raise_province_id": None,
                            "targeted_title_ids": [],
                            "war_objective_province_ids": [],
                            "objective_province_states": [],
                            "player_relative_war_score": 41,
                            "allied_armies": [],
                            "enemy_armies": [],
                        }
                    ],
                    "player_armies": [],
                    "one_life_settlement": None,
                },
            }
        )

        capabilities = state.capabilities()
        self.assertTrue(capabilities["snapshot"])
        self.assertEqual(
            capabilities["action_steps"],
            ["query-war-termination-terms-v1-50331699"],
        )
        self.assertNotIn(
            "query-war-termination-terms-v1-N",
            capabilities["action_steps"],
        )

    def test_unknown_build_stays_transport_only(self) -> None:
        state = NativeProtocolState(r"\\.\pipe\unknown-build-fixture")
        state.ingest(
            {
                "type": "hello",
                "protocol_version": 1,
                "bridge_version": "0.1.0",
                "pid": 103,
                "session_generation": 0,
                "game_adapter_id": "ck3-1.19.0.6-msvc-x64",
                "game_adapter_status": "unsupported_build",
                "ck3_build_match": False,
                "capabilities": [
                    "bridge.identity",
                    "bridge.heartbeat",
                    "bridge.ping",
                ],
            }
        )

        capabilities = state.capabilities()
        self.assertFalse(capabilities["snapshot"])
        self.assertEqual(capabilities["action_steps"], [])
        self.assertEqual(
            capabilities["diagnostics"]["hello"]["game_adapter_status"],
            "unsupported_build",
        )
        with self.assertRaisesRegex(UnsupportedStepError, "did not advertise"):
            state.semantic_snapshot()


if __name__ == "__main__":
    unittest.main()

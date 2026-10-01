"""Actual current AI inputs packets through production ingest/wait/query."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_ai_reform_inputs_private_transport import (
    DOMAIN_KEY, STEP, query_player_religion_ai_reform_inputs_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002

FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_ai_reform_inputs"
CASES = ("multiple-controllers", "observed-no-ai")


def actual_packet(case: str = "multiple-controllers") -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class MailboxPacketDriver:
    """Replay actual complete packets; correlate only the request nonce."""

    allow_private_player_religion_ai_reform_inputs_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.frame = deepcopy(packet)
        result = packet["result"]
        native = result["player_religion_ai_reform_inputs"]
        self.snapshot = {
            "snapshot_id": f"native:{result['snapshot_revision']}",
            "revision": result["snapshot_revision"] + 1,
            "native_revision": result["snapshot_revision"], "date_raw": result["date_raw"],
            "played_character": {"character_id": native["played_character_id"], "alive": True},
            "paused": True, "map_ready": True,
            "diagnostics": {"hello": {
                "expected_ck3_version": CK3_12002.game_version,
                "expected_ck3_sha256": CK3_12002.executable_sha256,
            }},
        }
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:religion-ai-reform-inputs")
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionAIReformInputsWireTests(unittest.TestCase):
    def test_actual_context_members_and_known_no_ai_keep_native_schedule_inputs(self) -> None:
        outputs = {}
        for case in CASES:
            with self.subTest(case=case):
                packet = actual_packet(case)
                result = packet["result"]
                native = result["player_religion_ai_reform_inputs"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_ai_reform_inputs_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
                )
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["domain_key"], DOMAIN_KEY)
                self.assertEqual(actual["backend_id"], result["backend_id"])
                self.assertEqual(actual["snapshot_revision"], result["snapshot_revision"])
                self.assertEqual(actual["queried_revision"], driver.snapshot["revision"])
                self.assertEqual(actual["queried_native_revision"], result["snapshot_revision"])
                self.assertEqual(actual["query_date_raw"], result["date_raw"])
                self.assertEqual(actual["exact_ck3_build"], CK3_12002.game_version)
                self.assertEqual(actual["exe_sha256"], CK3_12002.executable_sha256)
                self.assertIs(actual["read_only"], True)
                self.assertIs(actual["advertised"], False)
                self.assertEqual(driver.ingested_types, ["command_result"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], STEP)
                self.assertEqual(request["expected_revision"], result["snapshot_revision"])
                self.assertEqual(request["expected_snapshot_revision"], result["snapshot_revision"])
                self.assertNotIn("character_id", request)
                self.assertNotIn("action", request)
                self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
                outputs[case] = actual

        multi = outputs["multiple-controllers"]
        self.assertEqual(multi["context_status"], "observed_controllers")
        self.assertEqual(multi["controller_count"], 3)
        self.assertEqual(multi["context"]["actual_holder_count"], 5)
        self.assertIs(multi["gate_inputs_observation_complete"], True)
        members = multi["controllers"]
        self.assertEqual([row["context_index"] for row in members], [0, 1, 2])
        self.assertEqual([row["kind"] for row in members], ["ordinary", "player_special", "ordinary"])
        self.assertEqual([row["active_raw"] for row in members], [1, 1, 0])
        self.assertEqual([row["schedule"]["ai_status"] for row in members], ["observed", "gates_only", "observed"])
        self.assertEqual([row["schedule"]["actual_ai_timer"]["rare_countdown_prepare_ticks"]
                          for row in members], [-4, None, 12])
        self.assertIs(members[0]["schedule"]["current_actor"]["current_independent_ruler"], False)
        self.assertIs(members[0]["schedule"]["actual_ai_cache"]["cached_independent_ruler"], True)
        self.assertIs(members[1]["schedule"]["actual_ai_cache"]["available"], True)
        self.assertIs(members[1]["schedule"]["actual_ai_cache"]["handler_cache_gates_pass"], False)
        self.assertIs(members[1]["schedule"]["actual_ai_timer"]["available"], False)
        self.assertIsNone(members[1]["schedule"]["actual_ai_timer"]["rare_selected_raw"])
        self.assertEqual(members[2]["schedule"]["actual_ai_timer"]["rare_selected_raw"], 0)

        no_ai = outputs["observed-no-ai"]
        self.assertIs(no_ai["available"], True)
        self.assertEqual(no_ai["context_status"], "observed_no_ai")
        self.assertEqual(no_ai["controller_count"], 0)
        self.assertEqual(no_ai["controller_absence"], "no_actual_controller")
        self.assertIs(no_ai["gate_inputs_observation_complete"], True)
        self.assertEqual(no_ai["controllers"], [])
        self.assertEqual(no_ai["context"]["controllers"], [])
        for actual in outputs.values():
            base = actual["schedule_base"]
            self.assertEqual(base["ai_status"], "not_supplied")
            self.assertEqual(base["current_actor"]["highest_tier"], 2)
            self.assertIs(base["native_globals"]["reformation_enabled"], False)
            self.assertEqual(base["native_globals"]["rare_period_prepare_ticks"], 360)
            self.assertIs(base["actual_ai_cache"]["available"], False)
            self.assertIsNone(base["actual_ai_cache"]["handler_cache_gates_pass"])
            self.assertIs(base["actual_ai_timer"]["available"], False)
            self.assertIsNone(base["actual_ai_timer"]["rare_countdown_prepare_ticks"])
            self.assertEqual(base["actual_ai_timer"]["units"], "prepare_invocations")


if __name__ == "__main__":
    unittest.main()

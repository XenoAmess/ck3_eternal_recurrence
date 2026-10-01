"""Actual native termination packets through production protocol ingest/wait."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_completion_termination_private_transport import (
    query_active_scheme_sway_completion_termination_private_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_sway_completion_termination"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ProtocolSwayTerminationDriver:
    """Fixture paused context; only request_id correlation changes in replay."""

    allow_private_active_scheme_sway_completion_termination_query = False
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object], *, enabled: bool = True) -> None:
        self.packet = deepcopy(packet)
        self.allow_private_active_scheme_sway_completion_termination_query = enabled
        self.state = NativeProtocolState("offline-sway-termination-fixture-replay")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        envelope = packet["result"]
        body = envelope["sway_completion_termination"]
        self.state.ingest({
            "type": "hello", "protocol_version": 1, "pid": 1,
            "capabilities": ["game.state.snapshot"],
            "expected_ck3_version": envelope["build_version"],
            "expected_ck3_sha256": envelope["executable_sha256"],
        })
        self.initial_ingest = self.state.ingest({
            "type": "state_snapshot", "protocol_version": 1,
            "snapshot_id": f"native:{envelope['snapshot_revision']}",
            "revision": envelope["snapshot_revision"],
            "state": {
                "date_raw": envelope["date_raw"], "speed": 1,
                "paused": True, "map_ready": True,
                "played_character": {"character_id": body["actor_character_id"], "alive": True},
                "active_event": None, "pending_character_interaction": None,
                "one_life_settlement": None, "active_wars": [], "player_armies": [], "history": [],
            },
        })

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


def query(driver: ProtocolSwayTerminationDriver, **overrides: object) -> dict[str, object]:
    native = driver.packet["result"]["sway_completion_termination"]
    arguments = {
        "expected_revision": driver.take_snapshot()["revision"],
        "target_character_id": native["target_character_id"],
        "scheme_instance_id": native["scheme_instance_id"],
        "after_sequence": native["after_sequence"],
    }
    arguments.update(overrides)
    return query_active_scheme_sway_completion_termination_private_v1(driver, **arguments)


class SwayCompletionTermination12002WireTest(unittest.TestCase):
    def test_actual_source_pre_post_terminal_and_absence_flags_survive_real_protocol_and_leaf(self) -> None:
        provenance = load_fixture("provenance.json")
        outputs = {}
        for name in provenance["command_result_fixtures"]:
            with self.subTest(packet=name):
                packet = load_fixture(name)
                driver = ProtocolSwayTerminationDriver(packet)
                self.assertEqual(driver.initial_ingest, "state_snapshot")
                before = driver.take_snapshot()
                native = packet["result"]["sway_completion_termination"]
                actual = query(driver)
                self.assertEqual(driver.last_ingest, "command_result")
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertIsNot(actual["records"], driver.packet["result"]["sway_completion_termination"]["records"])
                self.assertEqual(actual["queried_revision"], before["revision"])
                self.assertEqual(actual["queried_native_revision"], packet["result"]["snapshot_revision"])
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["exact_ck3_build"], provenance["game_version"])
                self.assertEqual(actual["exe_sha256"], provenance["executable_sha256"])
                self.assertTrue(actual["session_records_only"])
                self.assertFalse(actual["material_effect_observed"])
                self.assertNotIn("terminal_cause", actual)
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-sway-completion-termination-v1-private")
                self.assertEqual(request["expected_revision"], before["native_revision"])
                self.assertEqual(request["expected_snapshot_revision"], before["native_revision"])
                for key in ("actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence"):
                    self.assertEqual(request[key], native[key])
                for record in actual["records"]:
                    self.assertTrue(record["executing_source_observed"])
                    self.assertEqual(record["scheme_instance_generation"], 2)
                    self.assertEqual(record["pre_status"], 0)
                    self.assertEqual(record["pre_owner"], native["actor_character_id"])
                    self.assertFalse(record["material_effect_observed"])
                    self.assertIsNone(record["specific_invalidation_reason"])
                    self.assertNotIn("human_sender", record)
                    self.assertNotIn("completion_reason", record)
                outputs[name] = actual["records"][0]
        terminal = outputs["terminal-transition-wire.json"]
        unchanged = outputs["original-no-terminal-wire.json"]
        absent = outputs["absent-post-wire.json"]
        self.assertEqual(terminal["source_class"], "authored_end_scheme_false_execute")
        self.assertEqual(terminal["input_root_scope_kind"], 9)
        self.assertTrue(terminal["post_exact_instance_join_ready"])
        self.assertEqual(terminal["post_status"], 1)
        self.assertEqual(terminal["post_owner"], 0xFFFFFFFF)
        self.assertTrue(terminal["native_terminal_state_observed"])
        self.assertTrue(terminal["native_terminal_transition_observed"])
        self.assertEqual(unchanged["source_class"], "authored_end_scheme_true_execute")
        self.assertEqual(unchanged["post_status"], 0)
        self.assertFalse(unchanged["native_terminal_state_observed"])
        self.assertFalse(unchanged["native_terminal_transition_observed"])
        self.assertEqual(absent["source_class"], "end_scheme_command_execute")
        self.assertTrue(absent["post_read_succeeded"])
        self.assertFalse(absent["post_instance_present"])
        self.assertFalse(absent["post_exact_instance_join_ready"])
        self.assertIsNone(absent["post_status"])
        self.assertIsNone(absent["post_owner"])
        self.assertFalse(absent["native_terminal_state_observed"])
        self.assertFalse(absent["native_terminal_transition_observed"])

    def test_fixture_bytes_match_actual_native_release_outputs(self) -> None:
        for name, expected in load_fixture("provenance.json")["payload_sha256"].items():
            with self.subTest(fixture=name):
                self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), expected)

    def test_disabled_permission_and_native_argument_ranges_reject_before_send(self) -> None:
        driver = ProtocolSwayTerminationDriver(load_fixture("terminal-transition-wire.json"), enabled=False)
        with self.assertRaises(UnsupportedStepError):
            query(driver)
        self.assertEqual(driver.sent, [])
        driver.allow_private_active_scheme_sway_completion_termination_query = True
        for fields in (
            {"expected_revision": True}, {"expected_revision": 1 << 64},
            {"target_character_id": 0}, {"target_character_id": 1 << 31},
            {"target_character_id": 50331649}, {"scheme_instance_id": 0xFFFFFFFF},
            {"after_sequence": True}, {"after_sequence": -1}, {"after_sequence": 1 << 64},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                query(driver, **fields)
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()

"""Actual native Sway execution packets through production protocol ingest/wait."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.active_scheme_sway_completion_execution_private_transport import (
    normalize_active_scheme_sway_completion_execution_v1,
    query_active_scheme_sway_completion_execution_private_v1,
)
from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_sway_completion_execution"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class ProtocolSwayExecutionDriver:
    """Only the paused context and request correlation are fixture scaffolding."""

    allow_private_active_scheme_sway_completion_execution_query = False
    command_timeout_seconds = 30.0

    def __init__(self, packet: dict[str, object], *, enabled: bool = True) -> None:
        self.packet = deepcopy(packet)
        self.allow_private_active_scheme_sway_completion_execution_query = enabled
        self.state = NativeProtocolState("offline-sway-execution-fixture-replay")
        self.endpoint = self
        self.sent: list[dict[str, object]] = []
        envelope = packet["result"]
        body = envelope["sway_completion_execution"]
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
                "one_life_settlement": None, "active_wars": [], "player_armies": [],
                "history": [],
            },
        })

    def take_snapshot(self) -> dict[str, object]:
        return self.state.semantic_snapshot()

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.packet)
        packet["request_id"] = request["request_id"]
        self.last_ingest = self.state.ingest(packet)


def query(driver: ProtocolSwayExecutionDriver, **overrides: object) -> dict[str, object]:
    native = driver.packet["result"]["sway_completion_execution"]
    arguments = {
        "expected_revision": driver.take_snapshot()["revision"],
        "target_character_id": native["target_character_id"],
        "scheme_instance_id": native["scheme_instance_id"],
        "after_sequence": native["after_sequence"],
    }
    arguments.update(overrides)
    return query_active_scheme_sway_completion_execution_private_v1(driver, **arguments)


class SwayCompletionExecution12002WireTest(unittest.TestCase):
    def test_three_actual_command_results_survive_real_protocol_ingest_wait_and_leaf(self) -> None:
        provenance = load_fixture("provenance.json")
        outputs = {}
        for name in provenance["command_result_fixtures"]:
            with self.subTest(packet=name):
                packet = load_fixture(name)
                driver = ProtocolSwayExecutionDriver(packet)
                self.assertEqual(driver.initial_ingest, "state_snapshot")
                before = driver.take_snapshot()
                native = packet["result"]["sway_completion_execution"]
                actual = query(driver)
                self.assertEqual(driver.last_ingest, "command_result")
                self.assertEqual({key: actual[key] for key in native}, native)
                self.assertEqual(actual["status"], packet["result"]["status"])
                self.assertEqual(actual["queried_revision"], before["revision"])
                self.assertEqual(actual["queried_native_revision"], packet["result"]["snapshot_revision"])
                self.assertEqual(actual["exact_ck3_build"], provenance["game_version"])
                self.assertEqual(actual["exe_sha256"], provenance["executable_sha256"])
                self.assertEqual(len(driver.sent), 1)
                request = driver.sent[0]
                self.assertEqual(request["step"], "query-sway-completion-execution-v1-private")
                self.assertEqual(request["expected_revision"], before["native_revision"])
                self.assertEqual(request["expected_snapshot_revision"], before["native_revision"])
                for key in ("actor_character_id", "target_character_id", "scheme_instance_id", "after_sequence"):
                    self.assertEqual(request[key], native[key])
                self.assertFalse(actual["material_effect_observed"])
                self.assertFalse(actual["native_terminal_state_observed"])
                self.assertNotIn("terminal_cause", actual)
                outputs[name] = actual
        hidden = outputs["hidden-good-command-result.json"]
        unattached = outputs["not-attached-command-result.json"]
        generation = outputs["wrong-generation-command-result.json"]
        self.assertEqual(hidden["records"][0]["source_branch"], "hidden_phase_success_source")
        self.assertFalse(unattached["available"])
        self.assertFalse(unattached["observer_attached"])
        self.assertEqual(unattached["records"], [])
        self.assertTrue(generation["available"])
        self.assertEqual(generation["scheme_instance_id"], 33554443)
        self.assertEqual(generation["records"], [])

    def test_actual_bare_bodies_preserve_bad_branch_sequence_filter_retention_and_copied_records(self) -> None:
        provenance = load_fixture("provenance.json")
        outputs = {}
        for name in provenance["body_fixtures"]:
            with self.subTest(body=name):
                native = load_fixture(name)
                actual = normalize_active_scheme_sway_completion_execution_v1(
                    native, snapshot={"played_character": {"character_id": native["actor_character_id"]}},
                    target_character_id=native["target_character_id"],
                    scheme_instance_id=native["scheme_instance_id"], after_sequence=native["after_sequence"],
                )
                self.assertEqual(actual, native)
                self.assertIsNot(actual["records"], native["records"])
                for actual_record, original_record in zip(actual["records"], native["records"]):
                    self.assertIsNot(actual_record, original_record)
                    self.assertTrue(actual_record["executing_input_observed"])
                    self.assertTrue(actual_record["exact_scope_join_ready"])
                    self.assertFalse(actual_record["message_enqueue_observed"])
                    self.assertFalse(actual_record["material_effect_observed"])
                    self.assertFalse(actual_record["native_terminal_state_observed"])
                outputs[name] = actual
        branches = outputs["hidden-bad-unresolved-wire.json"]["records"]
        self.assertEqual([row["phase_result"] for row in branches], ["success", "failure"])
        self.assertEqual(branches[1]["stock_event"], "sway_outcome.0002")
        self.assertEqual(branches[1]["source_branch"], "hidden_phase_failure_source")
        filtered = outputs["sequence-filter-wire.json"]
        self.assertTrue(all(row["sequence"] > filtered["after_sequence"] for row in filtered["records"]))
        gap = outputs["bounded-retention-gap-wire.json"]
        self.assertTrue(gap["retention_gap"])
        self.assertEqual((gap["earliest_sequence"], gap["latest_sequence"]), (3, 130))
        self.assertEqual(len(gap["records"]), 128)
        self.assertFalse(outputs["detached-wire.json"]["available"])

    def test_fixtures_are_byte_identical_native_outputs(self) -> None:
        for name, expected in load_fixture("provenance.json")["payload_sha256"].items():
            with self.subTest(fixture=name):
                self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), expected)

    def test_permission_and_native_argument_ranges_reject_before_send(self) -> None:
        driver = ProtocolSwayExecutionDriver(load_fixture("hidden-good-command-result.json"), enabled=False)
        with self.assertRaises(UnsupportedStepError):
            query(driver)
        self.assertEqual(driver.sent, [])
        driver.allow_private_active_scheme_sway_completion_execution_query = True
        for fields in (
            {"expected_revision": True}, {"expected_revision": 1 << 64},
            {"target_character_id": True}, {"target_character_id": 0},
            {"target_character_id": 1 << 31}, {"target_character_id": 50331649},
            {"scheme_instance_id": -1}, {"scheme_instance_id": 0xFFFFFFFF},
            {"after_sequence": True}, {"after_sequence": -1}, {"after_sequence": 1 << 64},
        ):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                query(driver, **fields)
        self.assertEqual(driver.sent, [])


if __name__ == "__main__":
    unittest.main()

"""Frozen owned-fixture packet replay; explicit mutations test projection semantics.

Real Driver -> Service -> MCP boundary; only endpoint I/O, hello and snapshots
are simulated. This neither executes CK3 nor qualifies engine getter behavior.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "ck3_autonomous_player/src"))
from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.player_holy_site_relic_context_private_transport import (
    normalize_player_holy_site_relic_context_v1 as normalize,
)
from xar_autoplayer.bridge.version_identity import CK3_12004

FIXTURE = REPO / "ck3_autonomous_player/tests/fixtures/holy_site_relic_rarity/context-integration.json"
FIXTURE_SHA = "1a863e1a1baaa538cec35162d01c100e3c6034f5879bae9a11689f5401c4c9d1"
KEY = "player_holy_site_relic_context"
TOOL = "ck3_query_player_holy_site_relic_context_v1"
STEP = "query-player-holy-site-relic-context-v1"


def frozen_packet():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA:
        raise ValueError("frozen owned-fixture packet bytes changed")
    return json.loads(raw)


def normal_frame(value):
    return {"played_character": {"character_id": value["played_character_id"]},
        "date_raw": value["date_raw"], "diagnostics": {"hello": {
            "expected_ck3_version": CK3_12004.game_version,
            "expected_ck3_sha256": CK3_12004.executable_sha256}}}


def positive_derivative():
    """Explicit synthetic mutation: the original frozen packet reports count zero."""
    packet = frozen_packet()
    value = packet["result"][KEY]
    value["inventory"]["artifact_ids"] = [16777220]
    value["current_relic_evaluation"].update(available=True, inventory_artifact_count_raw=1,
        active_artifact_rarity_sum=2, is_active=True, cache_evaluation_disagreement=True,
        unavailable_reason=None)
    value["recognition_matrix"]["cells"][1]["value"] = True
    return packet


class ProjectionTests(unittest.TestCase):
    def output(self, value):
        return normalize(deepcopy(value), snapshot=normal_frame(value), holy_site_id=value["holy_site_id"])

    def test_legacy_absence_is_exactly_unchanged(self):
        value = frozen_packet()["result"][KEY]
        del value["recognition_matrix"]
        self.assertEqual(self.output(value), value)

    def test_duplicate_slots_and_owned_only_reference_are_not_miscounted(self):
        value = positive_derivative()["result"][KEY]
        value["inventory"]["artifact_ids"].append(33554437)
        owned_only = deepcopy(value["inventory"]["artifact_objects"][0])
        owned_only.update(artifact_id=33554437, rarity_level=9)
        value["inventory"]["artifact_objects"].append(owned_only)
        output = self.output(value)
        projected = output["rarity_decomposition"]
        self.assertEqual([row["contribution"] for row in projected["slots"]], [1, 1, 0])
        self.assertEqual([row["slot_index"] for row in projected["slots"]], [0, 1, 2])
        self.assertEqual(projected["projected_sum"], 2)
        self.assertTrue(projected["numerically_matches_reported_total"])
        self.assertFalse(projected["same_native_evaluation_as_total"])
        self.assertEqual(output["current_relic_evaluation"], value["current_relic_evaluation"])
        self.assertEqual(output["cached_world_state"], value["cached_world_state"])
        self.assertEqual(output["evaluation_context"], value["evaluation_context"])
        self.assertEqual(output["recognition_matrix"], value["recognition_matrix"])

    def test_count_zero_guard_is_distinct_from_an_empty_slot(self):
        output = self.output(frozen_packet()["result"][KEY])["rarity_decomposition"]
        self.assertEqual(output["projected_sum"], 0)
        self.assertEqual([row["reason"] for row in output["slots"]],
                         ["inventory_count_zero", "inventory_count_zero", "empty_slot"])
        self.assertIsNone(output["reported_native_sum"])
        self.assertIsNone(output["numerically_matches_reported_total"])

    def test_false_recognition_and_unknown_recognition_differ(self):
        value = positive_derivative()["result"][KEY]
        matrix = value["recognition_matrix"]
        matrix["cells"][1]["value"] = False
        self.assertEqual(self.output(value)["rarity_decomposition"]["projected_sum"], 0)
        matrix.update(complete=False, unavailable_reason="explicit_test_partial")
        matrix["cells"][1].update(available=False, value=None, unavailable_reason="explicit_test_missing")
        output = self.output(value)["rarity_decomposition"]
        self.assertFalse(output["available"])
        self.assertIsNone(output["projected_sum"])
        self.assertIsNone(output["slots"][0]["contribution"])
        self.assertEqual(output["slots"][2]["contribution"], 0)

    def test_unknown_rarity_stays_unknown(self):
        value = positive_derivative()["result"][KEY]
        obj = value["inventory"]["artifact_objects"][0]
        obj.update(available=False, rarity_level=None, native_holy_site_owner_id=None,
                   unavailable_reason="explicit_test_object_unavailable")
        output = self.output(value)["rarity_decomposition"]
        self.assertIsNone(output["projected_sum"])
        self.assertEqual(output["slots"][0]["reason"], "artifact_unavailable")

    def test_unknown_count_and_unknown_association_remain_unknown(self):
        value = positive_derivative()["result"][KEY]
        value["current_relic_evaluation"].update(available=False, inventory_artifact_count_raw=None,
            active_artifact_rarity_sum=None, is_active=None, cache_evaluation_disagreement=None,
            unavailable_reason="explicit_test_count_unavailable")
        output = self.output(value)["rarity_decomposition"]
        self.assertIsNone(output["projected_sum"])
        self.assertEqual(output["slots"][0]["reason"], "inventory_count_unavailable")
        value = positive_derivative()["result"][KEY]
        value.update(associated_faith_ids_available=False, associated_faith_ids=None)
        value["current_relic_evaluation"]["county_holder_faith_associated"] = None
        matrix = value["recognition_matrix"]
        matrix.update(complete=False, unavailable_reason="explicit_test_association_unavailable")
        matrix["faith_sources"].update(associated_available=False, associated_faith_ids=None)
        for row in matrix["faiths"]:
            row["source_associated"] = False
        output = self.output(value)["rarity_decomposition"]
        self.assertIsNone(output["projected_sum"])
        self.assertEqual(output["slots"][0]["reason"], "association_unavailable")

    def test_partial_irrelevant_candidates_do_not_hide_complete_equipped_subset(self):
        value = positive_derivative()["result"][KEY]
        matrix = value["recognition_matrix"]
        matrix.update(complete=False, unavailable_reason="explicit_test_irrelevant_candidate_missing")
        matrix["cells"][3].update(available=False, value=None, unavailable_reason="explicit_test_missing")
        output = self.output(value)["rarity_decomposition"]
        self.assertTrue(output["complete_for_equipped_slots"])
        self.assertEqual(output["projected_sum"], 2)

    def test_unassociated_holder_definitely_gates_zero(self):
        value = positive_derivative()["result"][KEY]
        holder = value["county_context"]["county_holder_faith_id"]
        matrix = value["recognition_matrix"]
        # Retain all known Faith rows but change only association sources.
        # Existing player must be the sole associated fullID to keep first-seen order.
        value["associated_faith_ids"] = [value["player_faith_id"]]
        matrix["faith_sources"]["associated_faith_ids"] = list(value["associated_faith_ids"])
        matrix["faiths"][1]["source_associated"] = False
        value["current_relic_evaluation"]["county_holder_faith_associated"] = False
        output = self.output(value)["rarity_decomposition"]
        self.assertEqual(output["projected_sum"], 0)
        self.assertEqual(output["slots"][0]["reason"], "holder_faith_not_associated")

    def test_matrix_drift_unavailability_and_identity_mismatch_do_not_replace_native_total(self):
        for mutation in ("unavailable", "mismatch"):
            with self.subTest(mutation=mutation):
                value = positive_derivative()["result"][KEY]
                matrix = value["recognition_matrix"]
                if mutation == "unavailable":
                    matrix.update(available=False, complete=False, source_arrays_stable=False,
                                  unavailable_reason="explicit_test_source_drift")
                    for cell in matrix["cells"]:
                        cell.update(available=False, value=None, unavailable_reason="explicit_test_source_drift")
                else:
                    value["inventory"]["slots"][1]["artifact_id"] = None
                output = self.output(value)
                self.assertFalse(output["rarity_decomposition"]["available"])
                self.assertIsNone(output["rarity_decomposition"]["projected_sum"])
                self.assertEqual(output["current_relic_evaluation"]["active_artifact_rarity_sum"], 2)

    def test_scalar_disagreement_and_overflow_do_not_invent_a_total(self):
        value = positive_derivative()["result"][KEY]
        value["current_relic_evaluation"]["active_artifact_rarity_sum"] = 7
        self.assertFalse(self.output(value)["rarity_decomposition"]["numerically_matches_reported_total"])
        value["inventory"]["artifact_objects"][0]["rarity_level"] = 2**31 - 1
        output = self.output(value)["rarity_decomposition"]
        self.assertIsNone(output["projected_sum"])
        self.assertEqual(output["unavailable_reason"], "projected_sum_outside_int32")


class Endpoint:
    pipe_name = r"\\.\pipe\rarity-projection-frozen-packet-only"

    def __init__(self, packet):
        self.packet, self.requests, self.on_frame = packet, [], None

    def start(self, on_frame, on_disconnect):
        self.on_frame = on_frame

    def publish(self, frame):
        self.on_frame(deepcopy(frame))

    def send(self, request):
        if request["type"] == "execute_step":
            if request["request_id"] != self.packet["request_id"] or request["step"] != STEP:
                raise ValueError("unexpected query at frozen endpoint")
            self.requests.append(deepcopy(request))
            self.publish(self.packet)

    def transport_error(self):
        return None

    def close(self):
        pass


class McpBoundaryTests(unittest.IsolatedAsyncioTestCase):
    actual_results = []

    async def test_frozen_and_explicit_derivative_cross_real_mcp_with_distinct_revisions(self):
        from mcp import Client, ClientSession
        legacy = frozen_packet()
        del legacy["result"][KEY]["recognition_matrix"]
        mismatch = positive_derivative()
        mismatch["result"][KEY]["inventory"]["slots"][1]["artifact_id"] = None
        for label, packet in (("unmodified_owned_native_fixture", frozen_packet()),
                              ("explicit_synthetic_positive_derivative", positive_derivative()),
                              ("explicit_legacy_extension_absence", legacy),
                              ("explicit_source_mismatch", mismatch)):
            with self.subTest(case=label):
                value = packet["result"][KEY]
                original = deepcopy(packet)
                endpoint = Endpoint(packet)
                driver = NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0)
                driver.allow_private_player_holy_site_relic_context_query = True
                endpoint.publish({"type": "hello", "protocol_version": 1, "bridge_version": "0.1.0", "pid": 4242,
                    "session_generation": 0, "expected_ck3_version": CK3_12004.game_version,
                    "expected_ck3_sha256": CK3_12004.executable_sha256,
                    "capabilities": ["game.state.snapshot", "game.command." + STEP]})
                endpoint.publish({"type": "state_snapshot", "protocol_version": 1,
                    "snapshot_id": "native:rarity-frozen", "revision": packet["result"]["snapshot_revision"], "state": {
                        "phase": "map_hud", "date": "synthetic_frame_only", "date_raw": value["date_raw"],
                        "speed": 1, "paused": True, "map_ready": True, "history": [], "active_event": None,
                        "pending_character_interaction": None, "player_armies": [], "active_wars": [],
                        "played_character": {"character_id": value["played_character_id"], "alive": True}}})
                try:
                    public_revision = driver.take_snapshot_without_native_command_history()["revision"]
                    arguments = {"expected_revision": public_revision, "holy_site_id": value["holy_site_id"]}
                    self.assertNotEqual(public_revision, packet["result"]["snapshot_revision"])
                    async with Client(create_server(driver)) as client:
                        self.assertIsInstance(client.session, ClientSession)
                        tool = next(item for item in (await client.session.list_tools()).tools if item.name == TOOL)
                        self.assertEqual(set(tool.input_schema["properties"]), {"expected_revision", "holy_site_id"})
                        with patch("xar_autoplayer.bridge.g2_private_query_transport.uuid.uuid4",
                                   return_value=SimpleNamespace(hex=packet["request_id"][len("g2-read-"):])):
                            reply = await client.session.call_tool(TOOL, arguments)
                    self.assertFalse(reply.is_error, reply.model_dump(mode="json"))
                    actual = reply.structured_content
                    if label == "explicit_legacy_extension_absence":
                        self.assertNotIn("rarity_decomposition", actual)
                    elif label == "explicit_source_mismatch":
                        self.assertIsNone(actual["rarity_decomposition"]["projected_sum"])
                        self.assertEqual(actual["rarity_decomposition"]["unavailable_reason"], "source_identity_mismatch")
                        self.assertEqual(actual["current_relic_evaluation"]["active_artifact_rarity_sum"], 2)
                    else:
                        self.assertEqual(actual["rarity_decomposition"]["projected_sum"], 0 if label.startswith("unmodified") else 2)
                    self.assertEqual(actual["queried_revision"], public_revision)
                    self.assertEqual(actual["queried_native_revision"], 9)
                    self.assertEqual(len(endpoint.requests), 1)
                    self.assertEqual(endpoint.requests[0]["expected_revision"], 9)
                    self.assertEqual(endpoint.requests[0]["expected_snapshot_revision"], 9)
                    self.assertEqual(packet, original)
                    self.assertEqual(actual["evaluation_context"], value["evaluation_context"])
                    self.actual_results.append({"case": label, "arguments": arguments,
                        "wire_requests": endpoint.requests, "response": actual})
                finally:
                    driver.close()


if __name__ == "__main__":
    unittest.main()

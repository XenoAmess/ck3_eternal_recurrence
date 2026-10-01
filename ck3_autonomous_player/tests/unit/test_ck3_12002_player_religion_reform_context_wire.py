"""Actual C++ reform envelopes through production ingest, wait and query."""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import UnsupportedStepError
from xar_autoplayer.bridge.native_driver import NativeProtocolState
from xar_autoplayer.bridge.player_religion_reform_context_private_transport import (
    DOMAIN_KEY, STEP, query_player_religion_reform_context_private_v1,
)
from xar_autoplayer.bridge.version_identity import CK3_12002


FIXTURES = ROOT / "native_bridge/research/fixtures/ck3_12002_player_religion_reform_context"


def actual_packet(case: str) -> dict[str, object]:
    return json.loads((FIXTURES / f"{case}.json").read_text(encoding="utf-8"))


class MailboxPacketDriver:
    """The only wire edit is correlation with the new request's nonce."""

    allow_private_player_religion_reform_context_query = True

    def __init__(self, packet: dict[str, object]) -> None:
        self.frame = deepcopy(packet)
        result = packet["result"]
        native = result["player_religion_reform_context"]
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
        self.sent: list[dict[str, object]] = []
        self.ingested_types: list[str] = []
        self.endpoint = self
        self.state = NativeProtocolState("offline-fixture:religion-reform")

    def take_snapshot(self) -> dict[str, object]:
        return deepcopy(self.snapshot)

    def send(self, request: dict[str, object]) -> None:
        self.sent.append(deepcopy(request))
        packet = deepcopy(self.frame)
        packet["request_id"] = request["request_id"]
        self.ingested_types.append(self.state.ingest(packet))


class PlayerReligionReformContextWireTests(unittest.TestCase):
    def observe(self, case: str) -> dict[str, object]:
        packet = actual_packet(case)
        result = packet["result"]
        native = result["player_religion_reform_context"]
        driver = MailboxPacketDriver(packet)
        actual = query_player_religion_reform_context_private_v1(
            driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
        )
        self.assertEqual({key: actual[key] for key in native}, native)
        self.assertEqual(actual["status"], result["status"])
        self.assertEqual(actual["domain_key"], DOMAIN_KEY)
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
        self.assertNotIn("target_id", request)
        self.assertIsNone(driver.state.wait_for_command_result(request["request_id"], 0))
        return actual

    def test_all_actual_cpp_packets_survive_the_production_cache_and_query(self) -> None:
        provenance = json.loads((FIXTURES / "provenance.json").read_text(encoding="utf-8"))
        cases = list(provenance["packets"])
        self.assertGreaterEqual(len(cases), 6)
        for case in cases:
            with self.subTest(case=case):
                actual = self.observe(case)
                self.assertIs(actual["readiness"]["final_choice_legality_readiness"], False)
                popup = actual["current_popup_choices"]
                if popup["available"]:
                    for row in popup["doctrines"] + popup["tenets"]:
                        self.assertIsNone(row["final_can_pick"])
                        self.assertIs(row["final_choice_legality_readiness"], False)
                else:
                    self.assertIsNone(popup["doctrines"])
                    self.assertIsNone(popup["tenets"])

    def test_actual_scope_absence_preserves_current_context_and_null_draft_values(self) -> None:
        actual = self.observe("absent-window")
        self.assertIs(actual["available"], True)
        self.assertIs(actual["current_creation_window"]["available"], True)
        self.assertIs(actual["current_creation_window"]["present"], False)
        self.assertIs(actual["current_creation_window"]["draft_observed"], False)
        self.assertIs(actual["current_context"]["available"], True)
        self.assertIsNone(actual["current_draft_costs"]["piety_cost_raw"])
        self.assertIsNone(actual["current_draft_eligibility"]["can_create_rite"])
        self.assertIsNone(actual["current_draft_eligibility"]["can_edit_rite"])
        self.assertIsNone(actual["current_popup_choices"]["doctrines"])

    def test_disabled_private_permission_sends_no_request(self) -> None:
        driver = MailboxPacketDriver(actual_packet("absent-window"))
        driver.allow_private_player_religion_reform_context_query = False
        with self.assertRaises(UnsupportedStepError):
            query_player_religion_reform_context_private_v1(
                driver, expected_revision=driver.snapshot["revision"],
            )
        self.assertEqual(driver.sent, [])
        self.assertEqual(driver.ingested_types, [])

    def test_actual_visible_quote_final_gates_and_partial_reads_stay_independent(self) -> None:
        for case, create, edit in (("visible-create", True, False),
                                   ("visible-denied", False, True)):
            with self.subTest(case=case):
                actual = self.observe(case)
                context = actual["current_context"]
                self.assertEqual(context["faith_fervor_raw"], 0)
                self.assertEqual(context["spiritual_fulfillment_raw"], -345678)
                costs = actual["current_draft_costs"]
                self.assertEqual(costs["piety_cost_raw"], 9000000)
                self.assertEqual(costs["piety_missing_signed_raw"], -2500000)
                self.assertIs(costs["has_enough_piety"], True)
                self.assertIs(actual["current_draft_eligibility"]["can_create_rite"], create)
                self.assertIs(actual["current_draft_eligibility"]["can_edit_rite"], edit)
        actual = self.observe("cost-unavailable")
        self.assertIs(actual["available"], True)
        self.assertIs(actual["readiness"]["current_draft_cost_ready"], False)
        self.assertIs(actual["readiness"]["current_draft_final_eligibility_ready"], True)
        self.assertIsNone(actual["current_draft_costs"]["piety_cost_raw"])
        actual = self.observe("choices-unavailable")
        self.assertIs(actual["available"], True)
        self.assertIs(actual["readiness"]["current_popup_collection_ready"], False)
        self.assertIsNone(actual["current_popup_choices"]["doctrines"])
        actual = self.observe("context-unavailable")
        self.assertIs(actual["available"], True)
        self.assertIs(actual["readiness"]["current_context_ready"], False)
        actual = self.observe("query-unavailable")
        self.assertIs(actual["available"], False)
        self.assertEqual(actual["status"], "unavailable")

    def test_actual_final_doctrine_selection_retains_its_independent_readiness(self) -> None:
        for case in ("visible-create", "visible-denied", "absent-window", "hidden-window",
                     "choices-unavailable", "query-unavailable", "doctrine-hidden-row",
                     "empty-popup", "cost-unavailable", "context-unavailable", "visible-zero-cost"):
            with self.subTest(case=case):
                packet = actual_packet(case)
                native = packet["result"]["player_religion_reform_context"]
                driver = MailboxPacketDriver(packet)
                actual = query_player_religion_reform_context_private_v1(
                    driver, expected_revision=driver.snapshot["revision"], timeout_seconds=1,
                )
                self.assertEqual(actual["current_doctrine_selection"],
                                 native["current_doctrine_selection"])
                self.assertEqual(actual["readiness"]["doctrine_final_selection_ready"],
                                 native["readiness"]["doctrine_final_selection_ready"])
                self.assertIs(actual["readiness"]["final_choice_legality_readiness"], False)
                selection = actual["current_doctrine_selection"]
                self.assertEqual(selection["selection_ready"], selection["available"])
                if case in ("visible-create", "visible-denied", "doctrine-hidden-row", "empty-popup",
                            "cost-unavailable", "context-unavailable", "visible-zero-cost"):
                    self.assertIs(selection["selection_ready"], True)
                    if case == "empty-popup":
                        self.assertEqual(selection["rows"], [])
                        self.assertEqual(selection["selectable_doctrine_keys"], [])
                    else:
                        self.assertGreater(len(selection["rows"]), 0)
                    if case == "doctrine-hidden-row":
                        self.assertIs(selection["rows"][0]["native_should_display"], False)
                        self.assertIs(selection["rows"][0]["selectable"], False)
                        self.assertEqual(selection["rows"][0]["selection_blocker"],
                                         "hidden_by_native_should_display")
                    if case == "visible-zero-cost":
                        self.assertEqual(actual["current_draft_costs"]["piety_cost_raw"], 0)
                        self.assertEqual(actual["current_draft_costs"]["piety_missing_signed_raw"], 0)
                        self.assertIs(actual["current_draft_costs"]["has_enough_piety"], True)
                else:
                    self.assertIs(selection["selection_ready"], False)
                    self.assertEqual(selection["selectable_doctrine_keys"], [])


if __name__ == "__main__":
    unittest.main()

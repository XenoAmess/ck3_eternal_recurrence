"""One FIRST consumer of seven synthetic, production-serialized native wires.

Run only after Root integrates the contract patch and both new source modules.
The transport is synthetic; NativeHeadlessGameplayDriver and
GameplayBridgeService are the actual production classes, without monkeypatches.
No fixture JSON is assembled or rewritten by this test.
"""

from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from xar_autoplayer.bridge.battle_reinforcement_assignment_contract import (
    normalize_battle_reinforcement_assignment_v1,
)
from xar_autoplayer.bridge.battle_reinforcement_arrival_assessment import (
    derive_battle_reinforcement_arrival_assessment,
)
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer.bridge.service import GameplayBridgeService


EXACT_EXE_SHA256 = "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
CASES = {
    "help_attacker_en_route": ("assigned_en_route", "eligible", "attacker", True),
    "help_defender_en_route": ("assigned_en_route", "eligible", "defender", True),
    "ordinary_last_compatible": ("ordinary_en_route", "eligible", None, True),
    "help_retreating_arrived": ("arrived_not_yet_participating", "ineligible", None, False),
    "help_empty_en_route": ("assigned_en_route", "ineligible", None, False),
    "already_participating": ("already_participating", "already_in_active_combat", None, False),
    "ordinary_no_compatible": ("ordinary_en_route", "eligible", "none", False),
}


class _FixtureWireEndpoint:
    """Replay an untouched native result through the driver's protocol seam."""

    def __init__(self, case_name: str, native_result: dict[str, object]) -> None:
        self.pipe_name = rf"\\.\pipe\xar_reinforcement_arrival_first_{case_name}"
        self.result = native_result
        self.on_frame = None
        self.on_disconnect = None
        self.sent_frames: list[dict[str, object]] = []

    def start(self, on_frame, on_disconnect) -> None:
        self.on_frame = on_frame
        self.on_disconnect = on_disconnect

    def publish(self, frame: dict[str, object]) -> None:
        if self.on_frame is None:
            raise AssertionError("fixture protocol endpoint was not started")
        self.on_frame(copy.deepcopy(frame))

    def send(self, frame: dict[str, object]) -> None:
        self.sent_frames.append(copy.deepcopy(frame))
        if frame.get("type") == "execute_step":
            if frame.get("step") != self.result["step"]:
                raise AssertionError("production driver changed the native fixture query")
            self.publish({
                "type": "command_result", "protocol_version": 1,
                "request_id": frame["request_id"], "ok": True,
                "result": self.result,
            })

    def transport_error(self) -> str | None:
        return None

    def close(self) -> None:
        return None


class BattleReinforcementArrivalFirstTests(unittest.TestCase):
    def test_native_whole_wires_through_real_service_and_immutable_assessment(self) -> None:
        wire_directory = os.environ.get("XAR_REINFORCEMENT_ARRIVAL_FIRST_WIRE_DIR")
        if not wire_directory:
            self.fail("Root must provide XAR_REINFORCEMENT_ARRIVAL_FIRST_WIRE_DIR")
        directory = Path(wire_directory)
        selected_cases = set(CASES)
        case_filter = os.environ.get("XAR_REINFORCEMENT_ARRIVAL_FIRST_CASE_FILTER")
        if case_filter:
            selected_cases = {item.strip() for item in case_filter.split(",") if item.strip()}
            self.assertTrue(selected_cases and selected_cases <= set(CASES))
        fixtures = {}
        for path in sorted(directory.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(payload, dict) and payload.get("case_name") in selected_cases:
                self.assertNotIn(payload["case_name"], fixtures)
                fixtures[payload["case_name"]] = payload
        self.assertEqual(set(fixtures), selected_cases)

        for case_name in CASES:
            if case_name not in selected_cases:
                continue
            with self.subTest(case_name=case_name):
                payload = fixtures[case_name]
                self.assertEqual(set(payload), {"case_name", "fixture", "hello", "semantic_snapshot", "result"})
                self.assertEqual(payload["fixture"], {
                    "synthetic": True, "source_baseline": "df87fd85",
                    "integration_baseline": "be06a134b9a5472275e08ea452a8e3542b192fb8",
                    "game_version": "1.20.0.3", "exe_sha256": EXACT_EXE_SHA256,
                })
                self.assertEqual(payload["hello"]["game_version"], "1.20.0.3")
                self.assertEqual(payload["hello"]["executable_sha256"].upper(), EXACT_EXE_SHA256)
                raw_result = payload["result"]
                raw_frame = raw_result["battle_reinforcement_assignment"]
                raw_copy = copy.deepcopy(raw_frame)
                strict = normalize_battle_reinforcement_assignment_v1(
                    raw_frame,
                    expected_selected_public_cunit_id=raw_frame["selected_public_cunit_id"],
                    expected_observed_date_raw=raw_frame["observed_date_raw"],
                    expected_snapshot_revision=raw_frame["snapshot_revision"],
                )
                self.assertEqual(strict, raw_copy)
                self.assertEqual(raw_frame["snapshot_revision"], 41)
                self.assertEqual(raw_frame["observed_date_raw"], 53_178_264)
                endpoint = _FixtureWireEndpoint(case_name, raw_result)
                driver = NativeHeadlessGameplayDriver(
                    endpoint.pipe_name, endpoint=endpoint, command_timeout_seconds=1.0,
                )
                try:
                    endpoint.publish(payload["hello"])
                    endpoint.publish(payload["semantic_snapshot"])
                    public_snapshot = driver.take_snapshot()
                    service_result = GameplayBridgeService(driver).query_battle_reinforcement_assignment_v1(
                        raw_frame["selected_public_cunit_id"],
                        expected_revision=public_snapshot["revision"],
                    )
                    self.assertEqual(service_result["battle_reinforcement_assignment"], raw_copy)
                    self.assertEqual(service_result["contact_projection"], raw_copy["contact_projection"])
                    self.assertEqual(service_result["source"]["native_revision"], 41)
                    self.assertEqual(service_result["source"]["date_raw"], 53_178_264)
                    self.assertTrue(service_result["source"]["paused"])
                    commands = [frame for frame in endpoint.sent_frames if frame.get("type") == "execute_step"]
                    self.assertEqual(len(commands), 1)
                    self.assertEqual(commands[0]["step"], raw_result["step"])

                    assessment = derive_battle_reinforcement_arrival_assessment(service_result["battle_reinforcement_assignment"])
                    lifecycle, eligibility, expected_side, has_conditional = CASES[case_name]
                    admission = raw_copy["contact_projection"]["arrival_admission"]
                    self.assertEqual(assessment.status, "available")
                    self.assertEqual(assessment.lifecycle, lifecycle)
                    self.assertEqual(assessment.eligibility_now, eligibility)
                    self.assertEqual(assessment.join_side_now, admission["join_side"])
                    if expected_side is not None:
                        self.assertEqual(assessment.join_side_now, expected_side)
                    self.assertEqual(assessment.target_provenance, admission["target"]["provenance"])
                    self.assertEqual(assessment.currently_selected_combat_id, admission["contact_if_now_selected_combat_id"])
                    self.assertEqual(assessment.current_attacker_public_cunit_ids_in_stored_order,
                                     tuple(admission["current_attacker_public_cunit_ids_in_stored_order"]))
                    self.assertEqual(assessment.current_defender_public_cunit_ids_in_stored_order,
                                     tuple(admission["current_defender_public_cunit_ids_in_stored_order"]))
                    self.assertFalse(assessment.future_binding)
                    self.assertEqual(assessment.conditional_arrival is not None, has_conditional)
                    if has_conditional:
                        conditional = assessment.conditional_arrival
                        native_eta = (raw_copy["route"]["assignment_eta_date_raw"]
                                      if assessment.target_provenance == "native_help_override"
                                      else raw_copy["route"]["arrival_date_raws"][-1])
                        self.assertEqual(conditional.native_eta_date_raw, native_eta)
                        self.assertEqual(conditional.currently_selected_combat_id, assessment.currently_selected_combat_id)
                        self.assertEqual(conditional.join_side_if_observed_state_persists, assessment.join_side_now)
                        self.assertFalse(conditional.future_binding)
                        with self.assertRaises(FrozenInstanceError):
                            setattr(conditional, "future_binding", True)
                    if case_name == "already_participating":
                        self.assertTrue(assessment.subject_current_participation_verified)
                        self.assertEqual(assessment.actual_active_combat_id, assessment.currently_selected_combat_id)
                    else:
                        self.assertFalse(assessment.subject_current_participation_verified)
                        compatible = admission["current_target_compatible_combat_ids_in_stored_order"]
                        self.assertEqual(assessment.currently_selected_combat_id, compatible[-1] if compatible else None)
                    with self.assertRaises(FrozenInstanceError):
                        setattr(assessment, "lifecycle", "no_arrival_target")
                    self.assertEqual(raw_frame, raw_copy)
                finally:
                    driver.close()


if __name__ == "__main__":
    unittest.main()

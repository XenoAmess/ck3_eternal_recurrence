"""One specified child/candidate value read stays bound to native legality."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.player_child_marriage_value_private_transport import (
    SCHEMA, STEP, query_player_child_marriage_value_private_v1,
)


def _frame() -> dict[str, object]:
    return {"native_revision": 3, "revision": 4, "date_raw": 53219928,
            "paused": True, "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def _legality() -> dict[str, object]:
    return {"schema": "xar.ck3.player-child-marriage-subject.v1",
            "status": "available", "player_child_verified": True,
            "read_only": True, "advertised": False,
            "exact_ck3_build": "1.19.0.6", "played_character_id": 29829,
            "subject_character_id": 37265, "native_revision": 3,
            "query_sequence": 1, "house_id": 174, "dynasty_id": 174,
            "native_legal_candidates": [{"candidate_character_id": 37267,
                                         "recipient_matchmaker_character_id": 32440}]}


def _reply() -> dict[str, object]:
    return {"ok": True, "result": {
        "step": STEP, "accepted": True, "private_build": True,
        "read_only": True, "advertised": False, "native_revision": 3,
        "legality_query_sequence": 1, "status": "available",
        "rows": [{"actor_character_id": 29829, "heir_character_id": 37265,
                  "candidate_character_id": 37267,
                  "recipient_character_id": 32440, "status": "available",
                  "failure": "none", "projection_failure": "none",
                  "outcome_failure": "none",
                  "predicted_outcome_if_accepted": "marriage",
                  "heir_sex_selector_raw": 1,
                  "candidate_sex_selector_raw": 0,
                  "matrilineal_option_selected": True,
                  "effective_matrilineal_if_accepted": True,
                  "heir_house_id": 174, "heir_dynasty_id": 174,
                  "candidate_house_id": 2052,
                  "candidate_dynasty_id": 2052,
                  "heir_native_fertility": {
                      "source": "native_marriage_fertility_input",
                      "extension_present": True,
                      "native_gate_evaluated": True,
                      "native_gate_allows": True,
                      "effective_raw": 75000},
                  "candidate_native_fertility": {
                      "source": "native_marriage_fertility_input",
                      "extension_present": True,
                      "native_gate_evaluated": True,
                      "native_gate_allows": True,
                      "effective_raw": 65000},
                  "candidate_betrothed_character_id": None,
                  "candidate_primary_spouse_character_id": None,
                  "candidate_spouse_character_ids": [],
                  "possible_alliance_pairs": [{"first_character_id": 29829,
                                               "second_character_id": 32440,
                                               "already_allied": False,
                                               "both_have_realm_data": True,
                                               "would_attempt_if_accepted": True}]}]}}


class _Driver:
    allow_private_player_child_marriage_subject_query = True

    def __init__(self, reply: dict[str, object],
                 frames: list[dict[str, object]]) -> None:
        self.reply = reply
        self.frames = frames
        self.request = None
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)

    def send(self, request: dict[str, object]) -> None:
        self.request = request

    def wait_for_command_result(self, request_id: str,
                                timeout_seconds: float) -> dict[str, object]:
        return self.reply


class PlayerChildMarriageValueTests(unittest.TestCase):
    def test_one_default_native_row_is_bound_to_child_and_candidate(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        value = query_player_child_marriage_value_private_v1(
            driver, legality=_legality(), candidate_character_id=37267)
        self.assertEqual(value["schema"], SCHEMA)
        self.assertEqual(driver.request["step"], STEP)
        self.assertEqual(driver.request["subject_character_id"], 37265)
        self.assertEqual(driver.request["candidate_character_id"], 37267)
        self.assertTrue(value["row"]["effective_matrilineal_if_accepted"])

    def test_changed_matchmaker_or_effective_option_is_rejected(self) -> None:
        reply = _reply()
        reply["result"]["rows"][0]["recipient_character_id"] = 32441
        with self.assertRaises(BridgeUnavailableError):
            query_player_child_marriage_value_private_v1(
                _Driver(reply, [_frame(), _frame()]),
                legality=_legality(), candidate_character_id=37267)
        reply = _reply()
        reply["result"]["rows"][0]["effective_matrilineal_if_accepted"] = False
        with self.assertRaises(BridgeUnavailableError):
            query_player_child_marriage_value_private_v1(
                _Driver(reply, [_frame(), _frame()]),
                legality=_legality(), candidate_character_id=37267)

    def test_selected_option_requires_its_own_final_answer(self) -> None:
        reply = _reply()
        row = reply["result"]["rows"][0]
        row.update({"requested_matrilineal_option": True,
                    "selected_option_readback": True,
                    "final_legality_sampled": True,
                    "complete_can_send": True,
                    "recipient_ai_accept_raw": 400000,
                    "recipient_answer_status_raw": 0})
        driver = _Driver(reply, [_frame(), _frame()])
        value = query_player_child_marriage_value_private_v1(
            driver, legality=_legality(), candidate_character_id=37267,
            request_matrilineal_option=True)
        self.assertTrue(driver.request["request_matrilineal_option"])
        self.assertTrue(value["row"]["matrilineal_option_selected"])
        row["recipient_answer_status_raw"] = 3
        with self.assertRaises(BridgeUnavailableError):
            query_player_child_marriage_value_private_v1(
                _Driver(reply, [_frame(), _frame()]), legality=_legality(),
                candidate_character_id=37267,
                request_matrilineal_option=True)

    def test_stale_paused_revision_is_rejected(self) -> None:
        later = deepcopy(_frame())
        later["native_revision"] = 4
        with self.assertRaises(BridgeUnavailableError):
            query_player_child_marriage_value_private_v1(
                _Driver(_reply(), [_frame(), later]),
                legality=_legality(), candidate_character_id=37267)

    def test_missing_or_inconsistent_native_fertility_is_rejected(self) -> None:
        for replacement in (None, {"source": "native_marriage_fertility_input",
                                   "extension_present": False,
                                   "native_gate_evaluated": False,
                                   "native_gate_allows": None,
                                   "effective_raw": 1}):
            reply = _reply()
            reply["result"]["rows"][0]["candidate_native_fertility"] = replacement
            with self.assertRaises(BridgeUnavailableError):
                query_player_child_marriage_value_private_v1(
                    _Driver(reply, [_frame(), _frame()]),
                    legality=_legality(), candidate_character_id=37267)


if __name__ == "__main__":
    unittest.main()

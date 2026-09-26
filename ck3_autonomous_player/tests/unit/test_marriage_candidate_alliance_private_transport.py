"""Focused transport contract for the unadvertised five-candidate read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.marriage_candidate_alliance_private_transport import (
    SCHEMA, STEP, query_first_heir_candidate_alliance_projection_private_v1,
)


IDS = [16778038, 16778252, 16778632, 16778730, 16778737]


def _frame() -> dict[str, object]:
    return {"native_revision": 3, "date_raw": 53350000, "paused": True,
            "map_ready": True,
            "played_character": {"character_id": 29829, "alive": True}}


def _legality() -> dict[str, object]:
    return {"schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
            "status": "available", "native_revision": 3,
            "query_sequence": 7, "observed_first_heir_character_id": 38822,
            "native_legal_candidates": [
                {"played_character_id": 29829,
                 "subject_character_id": 38822,
                 "candidate_character_id": candidate}
                for candidate in IDS]}


def _reply(*, unavailable_index: int | None = None) -> dict[str, object]:
    rows = []
    for index, candidate in enumerate(IDS):
        unavailable = index == unavailable_index
        rows.append({
            "actor_character_id": 29829, "heir_character_id": 38822,
            "candidate_character_id": candidate,
            "recipient_character_id": candidate,
            "status": "unavailable" if unavailable else "available",
            "failure": "projection_unavailable" if unavailable else "none",
            "projection_failure": "signature_mismatch" if unavailable else "none",
            "outcome_failure": "none",
            "predicted_outcome_if_accepted":
                None if unavailable else "marriage",
            "heir_betrothed_character_id": None,
            "heir_primary_spouse_character_id": None,
            "heir_spouse_character_ids": None if unavailable else [],
            "matrilineal_option_selected": None if unavailable else False,
            "possible_alliance_pairs": [] if unavailable else [{
                "first_character_id": 29829,
                "second_character_id": candidate,
                "already_allied": False,
                "both_have_realm_data": True,
                "would_attempt_if_accepted": True,
            }],
        })
    return {"ok": True, "result": {
        "step": STEP, "accepted": True, "private_build": True,
        "read_only": True, "advertised": False,
        "native_revision": 3, "legality_query_sequence": 7,
        "status": "unavailable" if unavailable_index is not None
                  else "available", "rows": rows,
    }}


class _Endpoint:
    def __init__(self) -> None:
        self.request: dict[str, object] | None = None

    def send(self, request: dict[str, object]) -> None:
        self.request = request


class _State:
    def __init__(self, reply: dict[str, object] | None) -> None:
        self.reply = reply

    def wait_for_command_result(self, request_id: str,
                                timeout_seconds: float) -> dict[str, object] | None:
        return self.reply


class _Driver:
    def __init__(self, reply: dict[str, object] | None,
                 frames: list[dict[str, object]]) -> None:
        self.endpoint = _Endpoint()
        self.state = _State(reply)
        self.frames = frames

    def take_snapshot(self) -> dict[str, object]:
        return self.frames.pop(0)


class MarriageCandidateAlliancePrivateTransportTests(unittest.TestCase):
    def test_five_dynamic_legal_ids_are_sent_and_read_without_advertising(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        result = query_first_heir_candidate_alliance_projection_private_v1(
            driver, legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["schema"], SCHEMA)
        self.assertEqual(result["status"], "available")
        self.assertFalse(result["advertised"])
        self.assertEqual(driver.endpoint.request["step"], STEP)
        self.assertEqual(driver.endpoint.request["candidate_id_4"], IDS[4])
        self.assertEqual(len(result["rows"]), 5)
        self.assertEqual(result["rows"][0]["predicted_outcome_if_accepted"],
                         "marriage")
        self.assertEqual(result["rows"][0]["heir_spouse_character_ids"], [])

    def test_one_unavailable_pair_does_not_become_false_or_success(self) -> None:
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(_reply(unavailable_index=2), [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["rows"][2]["matrilineal_option_selected"])
        self.assertIsNone(result["rows"][2]["predicted_outcome_if_accepted"])
        self.assertIsNone(result["rows"][2]["heir_spouse_character_ids"])
        self.assertEqual(result["rows"][2]["possible_alliance_pairs"], [])

    def test_same_heir_relationship_is_read_across_five_candidates(self) -> None:
        reply = _reply()
        for row in reply["result"]["rows"]:
            row["heir_primary_spouse_character_id"] = 456
            row["heir_spouse_character_ids"] = [456]
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["rows"][4]["heir_spouse_character_ids"], [456])
        reply["result"]["rows"][4]["heir_spouse_character_ids"] = []
        with self.assertRaisesRegex(BridgeUnavailableError, "relationship malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply["result"]["rows"][4]["heir_primary_spouse_character_id"] = None
        with self.assertRaisesRegex(BridgeUnavailableError, "changed between candidates"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)

    def test_unavailable_heir_relationship_stays_unknown(self) -> None:
        reply = _reply(unavailable_index=2)
        row = reply["result"]["rows"][2]
        row["failure"] = "heir_relationship_unavailable"
        row["projection_failure"] = "none"
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertIsNone(result["rows"][2]["heir_spouse_character_ids"])
        self.assertEqual(result["status"], "unavailable")

    def test_outcome_failure_does_not_become_a_marriage(self) -> None:
        reply = _reply(unavailable_index=2)
        row = reply["result"]["rows"][2]
        row["failure"] = "outcome_unavailable"
        row["projection_failure"] = "none"
        row["outcome_failure"] = "runtime_threshold_unavailable"
        result = query_first_heir_candidate_alliance_projection_private_v1(
            _Driver(reply, [_frame(), _frame()]),
            legality=_legality(), candidate_character_ids=IDS)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["rows"][2]["predicted_outcome_if_accepted"])

    def test_duplicate_or_not_legal_id_never_submits(self) -> None:
        driver = _Driver(_reply(), [_frame(), _frame()])
        with self.assertRaises(ValueError):
            query_first_heir_candidate_alliance_projection_private_v1(
                driver, legality=_legality(),
                candidate_character_ids=IDS[:4] + IDS[0:1])
        self.assertIsNone(driver.endpoint.request)
        with self.assertRaises(BridgeUnavailableError):
            query_first_heir_candidate_alliance_projection_private_v1(
                driver, legality=_legality(),
                candidate_character_ids=IDS[:4] + [999999])
        self.assertIsNone(driver.endpoint.request)

    def test_red_and_frame_drift_are_not_consumed(self) -> None:
        driver = _Driver({"ok": False, "error": "mailbox busy"}, [_frame()])
        with self.assertRaisesRegex(BridgeUnavailableError, "RED: mailbox busy"):
            query_first_heir_candidate_alliance_projection_private_v1(
                driver, legality=_legality(), candidate_character_ids=IDS)
        changed = deepcopy(_frame())
        changed["date_raw"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "frame changed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(_reply(), [_frame(), changed]),
                legality=_legality(), candidate_character_ids=IDS)

    def test_native_identity_or_value_mismatch_is_red(self) -> None:
        reply = _reply()
        reply["result"]["rows"][1]["candidate_character_id"] += 1
        with self.assertRaisesRegex(BridgeUnavailableError, "row identity"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][0]["possible_alliance_pairs"][0][
            "would_attempt_if_accepted"] = False
        with self.assertRaisesRegex(BridgeUnavailableError, "pair malformed"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)
        reply = _reply()
        reply["result"]["rows"][0]["predicted_outcome_if_accepted"] = None
        with self.assertRaisesRegex(BridgeUnavailableError, "lost native option"):
            query_first_heir_candidate_alliance_projection_private_v1(
                _Driver(reply, [_frame()]), legality=_legality(),
                candidate_character_ids=IDS)


if __name__ == "__main__":
    unittest.main()

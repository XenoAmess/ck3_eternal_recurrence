"""Static exact-build transport regression; no CK3 outcome is implied."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    ALLIANCE_RESULT_STEP, RESULT_STEP, SCHEMA, SUBMIT_STEP,
    query_observed_first_heir_marriage_alliance_result_private_v1,
    query_observed_first_heir_marriage_result_private_v1,
    query_observed_first_heir_marriage_cold_result_private_v1,
    submit_observed_first_heir_marriage_private_v1,
)


def frame(revision: int = 693) -> dict[str, object]:
    return {"native_revision": revision, "paused": True,
            "map_ready": True, "revision": revision, "date_raw": 53215920,
            "played_character": {"character_id": 29829, "alive": True}}


def legality() -> dict[str, object]:
    # R0082 frozen new-literal row, typed-result SHA D7C3FE9B...5A8B698A.
    return {
        "schema": "xar.ck3.observed-first-heir-marriage-legality.v1",
        "exact_ck3_build": "1.19.0.6", "read_only": True,
        "advertised": False, "status": "available", "native_revision": 693,
        "root_query_sequence": 1, "query_sequence": 2,
        "observed_first_heir_character_id": 38822,
        "native_legal_candidates": [{
            "played_character_id": 29829, "subject_character_id": 38822,
            "candidate_character_id": 16778038,
            "recipient_matchmaker_character_id": 38713,
            "intermediary_character_id": -1, "native_rank": None,
            "complete_can_send": True, "recipient_ai_accept_raw": 3_600_000,
            "recipient_answer_status_raw": 0,
            "recipient_answer_allows_send": True,
        }],
    }


class FakeDriver:
    def __init__(self, snapshots: list[dict[str, object]], result: dict[str, object]):
        self.snapshots = snapshots
        self.result = result
        self.requests: list[dict[str, object]] = []
        self.endpoint = self
        self.state = self

    def take_snapshot(self) -> dict[str, object]:
        return self.snapshots.pop(0)

    def send(self, request: dict[str, object]) -> None:
        self.requests.append(request)

    def wait_for_command_result(self, _id: str, _timeout: float) -> dict[str, object]:
        return {"ok": True, "result": self.result}

    def _execute_campaign_root_context_v1_query(self, *, expected_revision: int):
        return {"status": "available", "held_title_partition": [
            {"primary": True, "first_heir_character_id": 38822}]}


def submit_result() -> dict[str, object]:
    return {"step": SUBMIT_STEP, "accepted": True, "private_build": True,
            "advertised": False, "status": "receipt_pending",
            "material_result": False, "pre_native_revision": 693,
            "played_character_id": 29829, "heir_character_id": 38822,
            "candidate_character_id": 16778038}


class TransportTest(unittest.TestCase):
    def test_material_pair_reads_actual_alliance_in_both_directions(self) -> None:
        resolved = {"status": "betrothal", "material_result": True,
                    "heir_character_id": 38822,
                    "candidate_character_id": 38710,
                    "source_pending": {"schema": SCHEMA,
                                       "played_character_id": 29829,
                                       "heir_character_id": 38822,
                                       "candidate_character_id": 38710}}
        for status, directions in (("allied", (True, True)),
                                   ("not_allied", (False, False)),
                                   ("unknown", (None, None))):
            result = {"step": ALLIANCE_RESULT_STEP, "accepted": True,
                      "private_build": True, "advertised": False,
                      "read_only": True, "native_revision": 693,
                      "played_character_id": 29829,
                      "recipient_character_id": 32266,
                      "heir_character_id": 38822,
                      "candidate_character_id": 38710,
                      "relationship_status": "betrothal",
                      "alliance_status": status,
                      "played_has_recipient_alliance": directions[0],
                      "recipient_has_played_alliance": directions[1]}
            driver = FakeDriver([frame(), frame()], result)
            observed = query_observed_first_heir_marriage_alliance_result_private_v1(
                driver, resolved=resolved, recipient_character_id=32266)
            self.assertEqual(observed["alliance_status"], status)
            self.assertEqual(driver.requests[0]["played_character_id"], 29829)
            self.assertEqual(driver.requests[0]["recipient_character_id"], 32266)
        unresolved = {**resolved, "material_result": False}
        driver = FakeDriver([frame()], result)
        with self.assertRaises(BridgeUnavailableError):
            query_observed_first_heir_marriage_alliance_result_private_v1(
                driver, resolved=unresolved, recipient_character_id=32266)
        self.assertEqual(driver.requests, [])

    def test_projection_or_one_way_answer_cannot_claim_alliance(self) -> None:
        resolved = {"status": "betrothal", "material_result": True,
                    "heir_character_id": 38822,
                    "candidate_character_id": 38710,
                    "source_pending": {"schema": SCHEMA,
                                       "played_character_id": 29829,
                                       "heir_character_id": 38822,
                                       "candidate_character_id": 38710}}
        result = {"step": ALLIANCE_RESULT_STEP, "accepted": True,
                  "private_build": True, "advertised": False,
                  "read_only": True, "native_revision": 693,
                  "played_character_id": 29829,
                  "recipient_character_id": 32266,
                  "heir_character_id": 38822,
                  "candidate_character_id": 38710,
                  "relationship_status": "betrothal",
                  "alliance_status": "allied",
                  "played_has_recipient_alliance": True,
                  "recipient_has_played_alliance": False}
        driver = FakeDriver([frame(), frame()], result)
        with self.assertRaises(BridgeUnavailableError):
            query_observed_first_heir_marriage_alliance_result_private_v1(
                driver, resolved=resolved, recipient_character_id=32266)
        mismatch = {**result, "alliance_status": "unknown"}
        driver = FakeDriver([frame(), frame()], mismatch)
        observed = query_observed_first_heir_marriage_alliance_result_private_v1(
            driver, resolved=resolved, recipient_character_id=32266)
        self.assertEqual(observed["alliance_status"], "unknown")
        self.assertIs(observed["played_has_recipient_alliance"], True)
        self.assertIs(observed["recipient_has_played_alliance"], False)

    def test_submit_is_pending_only(self) -> None:
        driver = FakeDriver([frame(), frame()], submit_result())
        pending = submit_observed_first_heir_marriage_private_v1(
            driver, legality=legality(), candidate_character_id=16778038)
        self.assertEqual(pending["status"], "receipt_pending")
        self.assertFalse(pending["material_result"])
        self.assertEqual(pending["schema"], SCHEMA)
        self.assertEqual(driver.requests[0]["expected_revision"], 693)
        self.assertEqual(driver.requests[0]["query_sequence"], 2)

    def test_unbound_row_cannot_submit(self) -> None:
        for mutation in (
            {"intermediary_character_id": 1},
            {"recipient_answer_status_raw": 2},
            {"complete_can_send": False},
            {"native_rank": 1},
        ):
            candidate = legality()
            candidate["native_legal_candidates"][0].update(mutation)
            driver = FakeDriver([frame()], submit_result())
            with self.assertRaises(BridgeUnavailableError):
                submit_observed_first_heir_marriage_private_v1(
                    driver, legality=candidate, candidate_character_id=16778038)
            self.assertEqual(driver.requests, [])

    def test_later_mutual_relation_only_is_material(self) -> None:
        pending = {"schema": SCHEMA, **submit_result()}
        result = {"step": RESULT_STEP, "accepted": True,
                  "private_build": True, "advertised": False,
                  "status": "marriage", "material_result": True,
                  "cold_recovery": False,
                  "pre_native_revision": 693, "post_native_revision": 694,
                  "heir_character_id": 38822,
                  "candidate_character_id": 16778038}
        driver = FakeDriver([frame(694)], result)
        material = query_observed_first_heir_marriage_result_private_v1(
            driver, pending=pending)
        self.assertEqual(material["status"], "marriage")
        self.assertTrue(material["material_result"])
        self.assertEqual(driver.requests[0]["step"], RESULT_STEP)

    def test_ack_or_same_frame_never_proves_material(self) -> None:
        pending = {"schema": SCHEMA, **submit_result()}
        driver = FakeDriver([frame()], submit_result())
        with self.assertRaises(BridgeUnavailableError):
            query_observed_first_heir_marriage_result_private_v1(
                driver, pending=pending)
        self.assertEqual(driver.requests, [])
        driver = FakeDriver([frame(694)], {**submit_result(),
                             "step": RESULT_STEP, "status": "marriage",
                             "material_result": False,
                             "post_native_revision": 694})
        with self.assertRaises(BridgeUnavailableError):
            query_observed_first_heir_marriage_result_private_v1(
                driver, pending=pending)

    def test_later_unresolved_pair_remains_pending(self) -> None:
        pending = {"schema": SCHEMA, **submit_result()}
        result = {"step": RESULT_STEP, "accepted": True,
                  "private_build": True, "advertised": False,
                  "status": "pending", "material_result": False,
                  "cold_recovery": False,
                  "pre_native_revision": 693, "post_native_revision": 694,
                  "heir_character_id": 38822,
                  "candidate_character_id": 16778038}
        driver = FakeDriver([frame(694)], result)
        self.assertFalse(query_observed_first_heir_marriage_result_private_v1(
            driver, pending=pending)["material_result"])

    def test_native_refusal_is_terminal_without_material_marriage(self) -> None:
        pending = {"schema": SCHEMA, **submit_result()}
        result = {"step": RESULT_STEP, "accepted": True,
                  "private_build": True, "advertised": False,
                  "status": "refused", "material_result": False,
                  "cold_recovery": False, "pre_native_revision": 693,
                  "post_native_revision": 694, "heir_character_id": 38822,
                  "candidate_character_id": 16778038}
        driver = FakeDriver([frame(694)], result)
        observed = query_observed_first_heir_marriage_result_private_v1(
            driver, pending=pending)
        self.assertEqual(observed["status"], "refused")
        self.assertFalse(observed["material_result"])

    def test_schema_has_private_pending_and_material_branches(self) -> None:
        schema = json.loads((ROOT / "schemas" /
            "observed-first-heir-marriage-private-action-v1.schema.json").read_text())
        self.assertEqual(schema["properties"]["schema"]["const"], SCHEMA)
        self.assertEqual(schema["properties"]["advertised"]["const"], False)
        self.assertEqual(len(schema["oneOf"]), 3)

    def test_cold_result_reports_pair_without_claiming_rejection(self) -> None:
        pending = {"schema": SCHEMA, **submit_result(),
                   "source_date_raw": 53215920}
        cold = {"step": RESULT_STEP, "accepted": True,
                "private_build": True, "advertised": False,
                "status": "pending", "material_result": False,
                "cold_recovery": True, "pre_native_revision": 0,
                "post_native_revision": 1, "heir_character_id": 38822,
                "candidate_character_id": 16778038}
        driver = FakeDriver([frame(1), frame(1)], cold)
        result = query_observed_first_heir_marriage_cold_result_private_v1(
            driver, pending=pending)
        self.assertTrue(result["cold_absent_relation_unresolved"])
        self.assertEqual(driver.requests[0]["cold_recovery"], 1)
        self.assertEqual(driver.requests[0]["source_date_raw"], 53215920)


if __name__ == "__main__":
    unittest.main()

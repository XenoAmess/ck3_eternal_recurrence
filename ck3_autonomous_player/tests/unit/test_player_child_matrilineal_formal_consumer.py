"""A failed proposal call must leave an unresolved durable pair."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from xar_autoplayer import player_child_matrilineal_formal_consumer as consumer


def _frame() -> dict[str, object]:
    return {"paused": True, "map_ready": True, "native_revision": 3911,
            "date_raw": 53219928, "episode_run_id": "native-29829-test",
            "played_character": {"character_id": 29829, "alive": True}}


def _legality() -> dict[str, object]:
    return {"schema": "xar.ck3.player-child-marriage-subject.v1",
            "status": "available", "player_child_verified": True,
            "native_revision": 3911, "played_character_id": 29829,
            "subject_character_id": 37265, "query_sequence": 7,
            "house_id": 174, "dynasty_id": 174,
            "native_legal_candidates": [{"candidate_character_id": 37267,
                "recipient_matchmaker_character_id": 32440}]}


def _value() -> dict[str, object]:
    return {"schema": "xar.ck3.player-child-marriage-value.v1",
            "status": "available", "native_revision": 3911,
            "candidate_character_id": 37267,
            "request_matrilineal_option": True,
            "row": {"recipient_character_id": 32440,
                "selected_option_readback": True,
                "matrilineal_option_selected": True,
                "effective_matrilineal_if_accepted": True,
                "complete_can_send": True,
                "recipient_answer_status_raw": 0,
                "recipient_ai_accept_raw": 5300000,
                "predicted_outcome_if_accepted": "marriage",
                "heir_is_adult": True, "candidate_is_adult": True,
                "heir_sex_selector_raw": 1, "candidate_sex_selector_raw": 0,
                "grand_wedding_option_selected": False,
                "heir_house_id": 174, "heir_dynasty_id": 174,
                "played_dynasty_id": 174, "candidate_dynasty_id": 2052,
                "heir_betrothed_character_id": None,
                "heir_primary_spouse_character_id": None,
                "heir_spouse_character_ids": [],
                "candidate_betrothed_character_id": None,
                "candidate_primary_spouse_character_id": None,
                "candidate_spouse_character_ids": []}}


class Driver:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.calls = 0

    def query_player_child_marriage_subject_private_v1(self, **_: object) -> dict[str, object]:
        return _legality()

    def query_player_child_marriage_value_private_v1(self, **_: object) -> dict[str, object]:
        return _value()

    def submit_player_child_matrilineal_private_v1(self, **_: object) -> dict[str, object]:
        self.calls += 1
        raise TimeoutError("native command result unavailable")

    def query_player_child_matrilineal_result_private_v1(
        self, *, pending: dict[str, object], cold: bool,
    ) -> dict[str, object]:
        self.calls += 1
        return {"status": "pending" if self.calls == 1 else "marriage",
                "material_result": self.calls != 1,
                "post_native_revision": 2 if self.calls == 1 else 3,
                "heir_character_id": pending["heir_character_id"],
                "candidate_character_id": pending["candidate_character_id"],
                "cold_recovery": cold,
                "outbound_pending_state": "active" if self.calls == 1 else "not_applicable"}


class ConsumerTest(unittest.TestCase):
    def test_exact_read_only_war_query_can_be_deferred_once(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("XAR_TEST_TEMP_ROOT")) as folder:
            driver = Driver(Path(folder))
            frame = {**_frame(), "active_wars": [{"war_id": 16777231}]}
            allowed = {"plan": {"selected_step":
                               "query-war-termination-options-16777231"}}
            chosen = consumer.plan_child_matrilineal_private(
                driver, allowed, frame, subject_character_id=37265,
                candidate_character_id=37267)
            self.assertEqual(chosen["plan"]["selected_step"], consumer.SUBMIT_STEP)
            self.assertEqual(chosen["plan"]["child_matrilineal_deferred_step"],
                             "query-war-termination-options-16777231")
            unrelated = {"plan": {"selected_step": "query-declarable-wars"}}
            self.assertIs(consumer.plan_child_matrilineal_private(
                driver, unrelated, frame, subject_character_id=37265,
                candidate_character_id=37267), unrelated)
            action = {"plan": {"selected_step": "enforce-demands-16777231"}}
            self.assertIs(consumer.plan_child_matrilineal_private(
                driver, action, frame, subject_character_id=37265,
                candidate_character_id=37267), action)
            with patch.object(consumer, "bridge_process_identity", return_value=(123, "creation")):
                with self.assertRaises(TimeoutError):
                    consumer.submit_child_matrilineal_private(
                        driver, plan=chosen["plan"], snapshot=frame)
            pending = consumer.read_child_matrilineal_ledger(driver.state_dir)["pending"]
            self.assertEqual(pending["deferred_war_query"],
                             "query-war-termination-options-16777231")
            self.assertEqual(pending["claimed_character_ids"],
                             [29829, 37265, 37267, 32440])

    def test_selected_option_determines_action_and_ambiguous_send_stays_pending(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("XAR_TEST_TEMP_ROOT")) as folder:
            driver = Driver(Path(folder))
            planned = {"plan": {"selected_step": "life-advance"}}
            with patch.object(consumer, "bridge_process_identity", return_value=(123, "creation")):
                choice = consumer.plan_child_matrilineal_private(
                    driver, planned, _frame(), subject_character_id=37265,
                    candidate_character_id=37267)
                self.assertEqual(choice["plan"]["selected_step"], consumer.SUBMIT_STEP)
                default = _value()
                default["row"]["matrilineal_option_selected"] = False
                self.assertFalse(consumer._positive_value(_legality(), default))
                with self.assertRaises(TimeoutError):
                    consumer.submit_child_matrilineal_private(
                        driver, plan=choice["plan"], snapshot=_frame())
                ledger = consumer.read_child_matrilineal_ledger(driver.state_dir)
                self.assertEqual(ledger["pending"]["submission_state"],
                                 "may_have_submitted")
                self.assertEqual(ledger["pending"]["heir_character_id"], 37265)
                self.assertEqual(ledger["pending"]["candidate_character_id"], 37267)
                self.assertIs(ledger["pending"]["matrilineal_option_selected"], True)
                self.assertEqual(driver.calls, 1)
                repeat = consumer.plan_child_matrilineal_private(
                    driver, planned, _frame(), subject_character_id=37265,
                    candidate_character_id=37267)
                self.assertEqual(repeat["plan"]["selected_step"], "life-advance")
                self.assertEqual(driver.calls, 1)

    def test_cold_pending_read_is_not_replayed_and_later_marriage_resolves(self) -> None:
        with tempfile.TemporaryDirectory(dir=os.environ.get("XAR_TEST_TEMP_ROOT")) as folder:
            driver = Driver(Path(folder))
            pending = {"schema": consumer.SCHEMA,
                       "status": "receipt_pending", "material_result": False,
                       "submission_state": "receipt_pending",
                       "episode_run_id": "native-29829-test",
                       "played_character_id": 29829,
                       "heir_character_id": 37265,
                       "candidate_character_id": 37267,
                       "recipient_character_id": 32440,
                       "matrilineal_option_selected": True,
                       "pre_native_revision": 3911,
                       "source_date_raw": 53219928,
                       "source_bridge_pid": 100,
                       "source_bridge_creation_date": "prior"}
            consumer._write(driver.state_dir,
                            {"schema": consumer.SCHEMA,
                             "pending": pending, "resolved": None})
            frame = {**_frame(), "native_revision": 2}
            planned = {"plan": {"selected_step": "life-advance"}}
            with patch.object(consumer, "bridge_process_identity", return_value=(200, "new")):
                choice = consumer.plan_child_matrilineal_private(
                    driver, planned, frame, subject_character_id=37265,
                    candidate_character_id=37267)
                self.assertEqual(choice["plan"]["selected_step"], consumer.RESULT_STEP)
                self.assertIs(choice["plan"]["child_matrilineal_cold_recovery"], True)
                first = consumer.query_child_matrilineal_result_private(
                    driver, pending=pending, cold=True)
                self.assertEqual(first["status"], "pending")
                waiting = consumer.plan_child_matrilineal_private(
                    driver, planned, frame, subject_character_id=37265,
                    candidate_character_id=37267)
                self.assertEqual(waiting["plan"]["selected_step"], "life-advance")
                later = {**frame, "native_revision": 3}
                again = consumer.plan_child_matrilineal_private(
                    driver, planned, later, subject_character_id=37265,
                    candidate_character_id=37267)
                self.assertEqual(again["plan"]["selected_step"], consumer.RESULT_STEP)
                second = consumer.query_child_matrilineal_result_private(
                    driver, pending=again["plan"]["child_matrilineal_pending"], cold=True)
                self.assertEqual(second["status"], "marriage")
                ledger = consumer.read_child_matrilineal_ledger(driver.state_dir)
                self.assertIsNone(ledger["pending"])
                self.assertEqual(ledger["resolved"]["status"], "marriage")
                self.assertEqual(driver.calls, 2)
                repeat = consumer.plan_child_matrilineal_private(
                    driver, planned, _frame(), subject_character_id=37265,
                    candidate_character_id=37267)
                self.assertEqual(repeat["plan"]["selected_step"],
                                 consumer.ALLIANCE_RESULT_STEP)
                self.assertEqual(driver.calls, 2)


if __name__ == "__main__":
    unittest.main()

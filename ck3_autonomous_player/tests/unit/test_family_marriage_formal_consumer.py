"""Private formal first-heir choice and durable result transitions."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.family_marriage_formal_consumer import (
    choose_first_heir_marriage_candidate,
    plan_family_marriage_private,
    query_family_marriage_result_private,
    read_family_marriage_ledger,
    submit_family_marriage_private,
)
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    SCHEMA, RESULT_STEP, SUBMIT_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.native_auto_run import _verify_pending_family_marriage_checkpoint
from xar_autoplayer.errors import AgentError
from xar_autoplayer import cli


def scene() -> dict[str, object]:
    return {"paused": True, "map_ready": True, "active_event": None,
            "pending_character_interaction": None, "active_wars": [],
            "native_revision": 7, "date_raw": 53215920,
            "episode_run_id": "robert-test",
            "played_character": {"character_id": 101}}


def family_reads() -> tuple[dict[str, object], dict[str, object]]:
    legal = []
    projected = []
    for index in range(5):
        candidate_id = 300 + index
        legal.append({"candidate_character_id": candidate_id,
                      "played_character_id": 101,
                      "subject_character_id": 202,
                      "complete_can_send": True,
                      "recipient_answer_allows_send": True,
                      "recipient_answer_status_raw": 0,
                      "recipient_ai_accept_raw": 500 - index})
        projected.append({"status": "available", "actor_character_id": 101,
                          "heir_character_id": 202,
                          "candidate_character_id": candidate_id,
                          "predicted_outcome_if_accepted": "marriage",
                          "heir_betrothed_character_id": None,
                          "heir_primary_spouse_character_id": None,
                          "heir_spouse_character_ids": [],
                          "played_dynasty_id": 20, "heir_dynasty_id": 20,
                          "played_house_id": 21, "heir_house_id": 21,
                          "heir_sex_selector_raw": 0,
                          "candidate_sex_selector_raw": 1,
                          "effective_matrilineal_if_accepted": False})
    return ({"status": "available", "native_revision": 7,
             "query_sequence": 2,
             "observed_first_heir_character_id": 202,
             "native_legal_candidates": legal},
            {"status": "available", "native_revision": 7,
             "legality_query_sequence": 2, "rows": projected})


class FakeDriver:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.legality, self.projection = family_reads()
        self.calls: list[str] = []

    def query_observed_first_heir_marriage_legality_v1(self, *, expected_native_revision):
        self.calls.append("legality")
        return self.legality

    def query_first_heir_candidate_alliance_projection_private_v1(self, *, legality,
                                                                  candidate_character_ids):
        self.calls.append("projection")
        assert candidate_character_ids == [300, 301, 302, 303, 304]
        return self.projection

    def submit_observed_first_heir_marriage_private_v1(self, *, legality,
                                                       candidate_character_id):
        self.calls.append("submit")
        assert candidate_character_id == 300
        return {"schema": SCHEMA, "status": "receipt_pending",
                "material_result": False, "pre_native_revision": 7,
                "played_character_id": 101, "heir_character_id": 202,
                "candidate_character_id": 300}

    def query_observed_first_heir_marriage_result_private_v1(self, *, pending):
        self.calls.append("result")
        return {"status": "marriage", "material_result": True,
                "post_native_revision": 8}


class FamilyConsumerTest(unittest.TestCase):
    def test_bounded_opt_in_is_explicit(self):
        args = cli.parser().parse_args([
            "--bridge-mode", "native-headless", "native-auto-run",
            "--turns", "3", "--timeout", "900",
            "--allow-private-family-marriage-formal-trial"])
        self.assertTrue(args.allow_private_family_marriage_formal_trial)
        default = cli.parser().parse_args([
            "--bridge-mode", "native-headless", "native-auto-run",
            "--turns", "3", "--timeout", "900"])
        self.assertFalse(default.allow_private_family_marriage_formal_trial)

    def test_unpartnered_heir_has_one_bounded_marriage_opportunity(self):
        legal, projected = family_reads()
        choice = choose_first_heir_marriage_candidate(legal, projected)
        self.assertEqual(choice["candidate_character_id"], 300)
        self.assertIn("child_dynasty_result", choice["unpriced"])
        projected["rows"][0]["heir_spouse_character_ids"] = [888]
        projected["rows"][1]["heir_spouse_character_ids"] = [888]
        projected["rows"][2]["heir_spouse_character_ids"] = [888]
        projected["rows"][3]["heir_spouse_character_ids"] = [888]
        projected["rows"][4]["heir_spouse_character_ids"] = [888]
        self.assertIsNone(choose_first_heir_marriage_candidate(legal, projected))

    def test_prewar_requires_explicit_native_declaration_and_observed_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            query = {"plan": {"selected_step": "query-declarable-wars"}}
            self.assertIs(plan_family_marriage_private(driver, query, scene()), query)
            self.assertEqual(plan_family_marriage_private(
                driver, {"plan": {"selected_step": "resolve-current-event"}}, scene(),
                prewar_arbitration=True)["plan"]["selected_step"],
                "resolve-current-event")
            self.assertEqual(driver.calls, [])
            for step in ("query-declarable-wars", "declare-war-302-1--1"):
                planned = plan_family_marriage_private(
                    driver, {"plan": {"selected_step": step}}, scene(),
                    prewar_arbitration=True)
                self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
                self.assertEqual(planned["plan"]["family_marriage_choice"]
                                 ["candidate_character_id"], 300)
            self.assertEqual(driver.calls, ["legality", "projection"] * 2)
            war = {"plan": {"selected_step": "query-declarable-wars"}}
            self.assertIs(plan_family_marriage_private(
                driver, war, {**scene(), "active_wars": [16777231]},
                prewar_arbitration=True), war)
            driver.projection["rows"] = [
                {**row, "predicted_outcome_if_accepted": "betrothal"}
                for row in driver.projection["rows"]]
            no_value = plan_family_marriage_private(
                driver, war, scene(), prewar_arbitration=True)
            self.assertEqual(no_value["plan"]["selected_step"],
                             "query-declarable-wars")
            self.assertEqual(no_value["plan"]["family_marriage_status"],
                             "no_positive_observed_marriage_opportunity")

    def test_prewar_submission_keeps_pending_result_and_no_resend(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            war = {"plan": {"selected_step": "query-declarable-wars"}}
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                planned = plan_family_marriage_private(
                    driver, war, scene(), prewar_arbitration=True)
                submit_family_marriage_private(driver, plan=planned["plan"],
                                               snapshot=scene())
                next_scene = {**scene(), "native_revision": 8}
                result_plan = plan_family_marriage_private(
                    driver, war, next_scene, prewar_arbitration=True)
                self.assertEqual(result_plan["plan"]["selected_step"], RESULT_STEP)
                query_family_marriage_result_private(
                    driver, pending=result_plan["plan"]["family_marriage_pending"],
                    cold=False)
                consumed = plan_family_marriage_private(
                    driver, war, next_scene, prewar_arbitration=True)
            self.assertEqual(consumed["plan"]["selected_step"],
                             "query-declarable-wars")
            self.assertEqual(consumed["plan"]["family_marriage_result_consumed"]
                             ["status"], "marriage")
            self.assertEqual(driver.calls, ["legality", "projection", "submit", "result"])

    def test_submit_pending_result_next_turn_and_no_repeat(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            baseline = {"plan": {"selected_step": "life-advance"}}
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                planned = plan_family_marriage_private(driver, baseline, scene())
                self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
                pending = submit_family_marriage_private(
                    driver, plan=planned["plan"], snapshot=scene())
                self.assertEqual(pending["submission_state"], "receipt_pending")
                next_scene = {**scene(), "native_revision": 8}
                next_plan = plan_family_marriage_private(driver, baseline, next_scene)
                self.assertEqual(next_plan["plan"]["selected_step"], RESULT_STEP)
                result = query_family_marriage_result_private(
                    driver, pending=next_plan["plan"]["family_marriage_pending"],
                    cold=False)
                self.assertTrue(result["material_result"])
                consumed = plan_family_marriage_private(driver, baseline, next_scene)
            self.assertEqual(consumed["plan"]["family_marriage_result_consumed"]["status"],
                             "marriage")
            self.assertEqual(driver.calls, ["legality", "projection", "submit", "result"])
            self.assertIsNone(read_family_marriage_ledger(driver.state_dir)["pending"])

    def test_formal_auto_turn_routes_typed_first_heir_submit(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            planned = plan_family_marriage_private(
                driver, {"plan": {"selected_step": "life-advance"}}, scene())
            service = GameplayBridgeService(driver)
            service.plan_turn = lambda: {**planned, "snapshot_id": "native:7",
                                         "revision": 7}
            service.snapshot = scene
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                outcome = service.auto_turn()
            self.assertEqual(outcome["status"], "executed")
            self.assertEqual(outcome["selected_step"], SUBMIT_STEP)
            self.assertEqual(outcome["result"]["status"], "receipt_pending")
            self.assertEqual(driver.calls, ["legality", "projection", "submit"])

    def test_cold_absent_relation_stays_unresolved_and_never_resubmits(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            baseline = {"plan": {"selected_step": "life-advance"}}
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                planned = plan_family_marriage_private(driver, baseline, scene())
                submit_family_marriage_private(driver, plan=planned["plan"],
                                               snapshot=scene())
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(99, "new-created")):
                recovery = plan_family_marriage_private(driver, baseline,
                                                       {**scene(), "native_revision": 1})
                self.assertEqual(recovery["plan"]["selected_step"], RESULT_STEP)
                driver.query_observed_first_heir_marriage_cold_result_private_v1 = (
                    lambda *, pending: {"status": "pending", "material_result": False,
                                        "post_native_revision": 1})
                query_family_marriage_result_private(
                    driver, pending=recovery["plan"]["family_marriage_pending"],
                    cold=True)
                blocked = plan_family_marriage_private(driver, baseline,
                                                      {**scene(), "native_revision": 1})
            self.assertIsNone(blocked["plan"]["selected_step"])
            self.assertEqual(blocked["plan"]["phase"],
                             "first_heir_marriage_cold_resolution_unknown")
            self.assertEqual(driver.calls.count("submit"), 1)

    def test_pending_result_waits_for_new_frame_instead_of_query_loop(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            baseline = {"plan": {"selected_step": "life-advance"}}
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                planned = plan_family_marriage_private(driver, baseline, scene())
                submit_family_marriage_private(driver, plan=planned["plan"],
                                               snapshot=scene())
                first = plan_family_marriage_private(
                    driver, baseline, {**scene(), "native_revision": 8})
                driver.query_observed_first_heir_marriage_result_private_v1 = (
                    lambda *, pending: {"status": "pending", "material_result": False,
                                        "post_native_revision": 8})
                query_family_marriage_result_private(
                    driver, pending=first["plan"]["family_marriage_pending"],
                    cold=False)
                waiting = plan_family_marriage_private(
                    driver, baseline, {**scene(), "native_revision": 8})
                self.assertEqual(waiting["plan"]["selected_step"], "life-advance")
                later = plan_family_marriage_private(
                    driver, baseline, {**scene(), "native_revision": 9})
                self.assertEqual(later["plan"]["selected_step"], RESULT_STEP)

    def test_resolved_marriage_is_rechecked_on_cold_pid(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            baseline = {"plan": {"selected_step": "life-advance"}}
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                chosen = plan_family_marriage_private(driver, baseline, scene())
                submit_family_marriage_private(driver, plan=chosen["plan"],
                                               snapshot=scene())
                pending = read_family_marriage_ledger(driver.state_dir)["pending"]
                query_family_marriage_result_private(driver, pending=pending,
                                                     cold=False)
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(99, "new-created")):
                recheck = plan_family_marriage_private(
                    driver, baseline, {**scene(), "native_revision": 1})
                self.assertEqual(recheck["plan"]["selected_step"], RESULT_STEP)
                driver.query_observed_first_heir_marriage_cold_result_private_v1 = (
                    lambda *, pending: {"status": "marriage", "material_result": True,
                                        "post_native_revision": 1})
                query_family_marriage_result_private(
                    driver, pending=recheck["plan"]["family_marriage_pending"],
                    cold=True)
                consumed = plan_family_marriage_private(
                    driver, baseline, {**scene(), "native_revision": 1})
            self.assertTrue(consumed["plan"]["family_marriage_result_consumed"]
                            ["cold_recovery_verified"])

    def test_pending_checkpoint_needs_durable_pair_and_game_save(self):
        pending = {"submission_state": "receipt_pending", "status": "receipt_pending",
                   "material_result": False, "episode_run_id": "robert-test",
                   "source_date_raw": 53215920, "played_character_id": 101,
                   "heir_character_id": 202, "candidate_character_id": 300}
        checkpoint = {"episode_run_id": "robert-test", "date_raw": 53215920}
        fence = _verify_pending_family_marriage_checkpoint(
            checkpoint, snapshot=scene(), submitted_result=pending,
            ledger={"pending": pending})
        self.assertEqual(fence["material_postcondition"], "unobserved")
        with self.assertRaises(AgentError):
            _verify_pending_family_marriage_checkpoint(
                checkpoint, snapshot=scene(), submitted_result=pending,
                ledger={"pending": {**pending, "candidate_character_id": 301}})


if __name__ == "__main__":
    unittest.main()

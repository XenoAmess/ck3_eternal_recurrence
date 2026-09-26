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
from xar_autoplayer.native_auto_run import (
    _turn_record, _verify_pending_family_marriage_checkpoint,
)
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
                      "recipient_matchmaker_character_id": 400 + index,
                      "complete_can_send": True,
                      "recipient_answer_allows_send": True,
                      "recipient_answer_status_raw": 0,
                      "recipient_ai_accept_raw": 500 - index})
        legal[-1].update(heir_adult_measure_raw=16,
                         candidate_adult_measure_raw=16,
                         played_dynasty_id=20, heir_dynasty_id=20,
                         candidate_dynasty_id=30 + index,
                         realm_backed_actor_recipient=True)
        projected.append({"status": "available", "actor_character_id": 101,
                          "heir_character_id": 202,
                          "recipient_character_id": 400 + index,
                          "candidate_character_id": candidate_id,
                          "possible_alliance_pairs": [],
                          "predicted_outcome_if_accepted": "marriage",
                          "heir_is_adult": True,
                          "candidate_is_adult": True,
                          "heir_adult_measure_raw": 16,
                          "candidate_adult_measure_raw": 16,
                          "heir_adult_threshold_raw": 16,
                          "candidate_adult_threshold_raw": 16,
                          "grand_wedding_option_selected": False,
                          "heir_betrothed_character_id": None,
                          "heir_primary_spouse_character_id": None,
                          "heir_spouse_character_ids": [],
                          "played_dynasty_id": 20, "heir_dynasty_id": 20,
                          "played_house_id": 21, "heir_house_id": 21,
                          "candidate_dynasty_id": 30, "candidate_house_id": 31,
                          "heir_sex_selector_raw": 0,
                          "candidate_sex_selector_raw": 1,
                          "matrilineal_option_selected": False,
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
        assert len(candidate_character_ids) == 5
        by_id = {row["candidate_character_id"]: row
                 for row in self.projection["rows"]}
        assert len(set(candidate_character_ids)) == 5
        assert set(candidate_character_ids).issubset(by_id)
        return {**self.projection,
                "rows": [by_id[candidate_id]
                         for candidate_id in candidate_character_ids]}

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
    @staticmethod
    def _c9_rank_driver(state_dir: Path) -> FakeDriver:
        driver = FakeDriver(state_dir)
        for index, row in enumerate(driver.projection["rows"]):
            legal = driver.legality["native_legal_candidates"][index]
            row.update(heir_is_adult=False, heir_adult_measure_raw=6,
                       candidate_is_adult=False,
                       candidate_adult_measure_raw=5 if index == 0 else 2,
                       predicted_outcome_if_accepted="betrothal",
                       candidate_dynasty_id=20)
            legal.update(heir_adult_measure_raw=6,
                         candidate_adult_measure_raw=5 if index == 0 else 2,
                         candidate_dynasty_id=20)
        for index, age in ((5, 5), (6, 6)):
            candidate_id = 300 + index
            recipient_id = 400 + index
            driver.legality["native_legal_candidates"].append({
                "candidate_character_id": candidate_id,
                "played_character_id": 101, "subject_character_id": 202,
                "recipient_matchmaker_character_id": recipient_id,
                "complete_can_send": True, "recipient_answer_allows_send": True,
                "recipient_answer_status_raw": 0,
                "recipient_ai_accept_raw": 100 - index,
                "heir_adult_measure_raw": 6,
                "candidate_adult_measure_raw": age,
                "played_dynasty_id": 20, "heir_dynasty_id": 20,
                "candidate_dynasty_id": 30 + index,
                "realm_backed_actor_recipient": True})
            driver.projection["rows"].append({
                **driver.projection["rows"][0],
                "recipient_character_id": recipient_id,
                "candidate_character_id": candidate_id,
                "candidate_adult_measure_raw": age,
                "candidate_dynasty_id": 30 + index,
                "candidate_house_id": 30 + index,
                "possible_alliance_pairs": [{
                    "first_character_id": 101,
                    "second_character_id": recipient_id,
                    "already_allied": False,
                    "both_have_realm_data": True,
                    "would_attempt_if_accepted": True}]})
        return driver

    def test_c9_acceptance_top_five_yields_to_external_age_matched_candidates(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = self._c9_rank_driver(Path(temporary))
            planned = plan_family_marriage_private(
                driver, {"plan": {"selected_step": "life-advance"}}, scene())
            self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
            self.assertEqual(planned["plan"]["family_marriage_choice"]
                             ["candidate_character_id"], 306)
            diagnostic = planned["plan"]["family_marriage_private_diagnostic"]
            self.assertEqual([row["candidate_character_id"] for row in
                              diagnostic["rows"]][:2], [306, 305])
            self.assertEqual(diagnostic["ranking"]["prefilter_eligible_count"], 2)
            self.assertEqual(diagnostic["ranking"]["value_input_unavailable_count"], 0)

    def test_c9_no_external_age_matched_candidate_is_a_real_no_op(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = self._c9_rank_driver(Path(temporary))
            for index, age in ((5, 1), (6, 60)):
                driver.legality["native_legal_candidates"][index][
                    "candidate_adult_measure_raw"] = age
                driver.projection["rows"][index]["candidate_adult_measure_raw"] = age
                driver.projection["rows"][index]["candidate_is_adult"] = age >= 16
            planned = plan_family_marriage_private(
                driver, {"plan": {"selected_step": "life-advance"}}, scene())
            self.assertEqual(planned["plan"]["selected_step"], "life-advance")
            self.assertEqual(planned["plan"]["family_marriage_status"],
                             "no_positive_observed_marriage_opportunity")
            ranking = planned["plan"]["family_marriage_private_diagnostic"]["ranking"]
            self.assertEqual(ranking["prefilter_eligible_count"], 0)
            self.assertEqual(ranking["conclusion"],
                             "no_age_matched_external_realm_candidate")

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

    def test_private_five_row_diagnostic_explains_no_positive_choice(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            rows = driver.projection["rows"]
            rows[0]["predicted_outcome_if_accepted"] = "betrothal"
            rows[0]["candidate_is_adult"] = False
            rows[1]["candidate_sex_selector_raw"] = 0
            rows[2]["matrilineal_option_selected"] = True
            rows[2]["effective_matrilineal_if_accepted"] = True
            rows[3]["predicted_outcome_if_accepted"] = "betrothal"
            rows[3]["candidate_is_adult"] = False
            rows[3]["possible_alliance_pairs"] = [{
                "first_character_id": 101, "second_character_id": 403,
                "already_allied": False, "both_have_realm_data": True,
                "would_attempt_if_accepted": True,
            }]
            driver.legality["native_legal_candidates"][4]["recipient_ai_accept_raw"] = 0
            planned = plan_family_marriage_private(
                driver, {"plan": {"selected_step": "life-advance"}}, scene())
            plan = planned["plan"]
            self.assertEqual(plan["selected_step"], "life-advance")
            self.assertEqual(plan["family_marriage_status"],
                             "no_positive_observed_marriage_opportunity")
            diagnostic = plan["family_marriage_private_diagnostic"]
            self.assertFalse(diagnostic["advertised"])
            self.assertEqual(diagnostic["native_revision"], 7)
            self.assertEqual(diagnostic["legality_query_sequence"], 2)
            self.assertEqual(diagnostic["observed_first_heir_character_id"], 202)
            self.assertEqual(diagnostic["final_legal_candidate_count"], 5)
            self.assertIsNone(diagnostic["selected_candidate_character_id"])
            observed = diagnostic["rows"]
            self.assertEqual([row["candidate_character_id"] for row in observed],
                             [300, 301, 302, 303, 304])
            self.assertEqual(observed[0]["predicted_outcome_if_accepted"],
                             "betrothal")
            self.assertIs(observed[0]["heir_is_adult"], True)
            self.assertIs(observed[0]["candidate_is_adult"], False)
            self.assertIs(observed[0]["grand_wedding_option_selected"], False)
            self.assertIn("betrothal_age_gap_out_of_bounds",
                          observed[0]["rejection_reasons"])
            self.assertIn("same_selector_pair", observed[1]["rejection_reasons"])
            self.assertEqual(observed[1]["heir_spouse_count"], 0)
            self.assertIsNone(observed[1]["heir_betrothed_character_id"])
            self.assertIn("lineality_not_heir_aligned", observed[2]["rejection_reasons"])
            self.assertEqual(observed[2]["heir_house_id"], 21)
            self.assertEqual(observed[2]["candidate_dynasty_id"], 30)
            self.assertIn("betrothal_age_gap_out_of_bounds",
                          observed[3]["rejection_reasons"])
            self.assertEqual(observed[3]["recipient_character_id"], 403)
            self.assertEqual(observed[3]["recipient_matchmaker_character_id"], 403)
            self.assertEqual(observed[3]["possible_alliance_pairs"],
                             rows[3]["possible_alliance_pairs"])
            self.assertIn("recipient_accept_not_positive", observed[4]["rejection_reasons"])
            self.assertEqual(observed[4]["recipient_ai_accept_raw"], 0)
            formal_turn = _turn_record(
                3, "2026-09-26T00:00:00Z", turn_class="gameplay",
                outcome={"status": "executed", "selected_step": "life-advance",
                         "plan": plan, "result": {}},
                before={"native_revision": 7}, after={"native_revision": 8},
                evidence=["date_advanced"],
            )
            self.assertEqual(formal_turn["plan"]["family_marriage_private_diagnostic"],
                             diagnostic)
            self.assertEqual(formal_turn["plan"]["family_marriage_private_diagnostic"]
                             ["rows"][3]["possible_alliance_pairs"],
                             rows[3]["possible_alliance_pairs"])
            self.assertNotIn("family_marriage_legality", formal_turn["plan"])
            self.assertEqual(driver.calls, ["legality", "projection"])

    def test_minor_heir_chooses_bounded_external_betrothal_and_consumes_material_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            for index, row in enumerate(driver.projection["rows"]):
                row.update(heir_is_adult=False, heir_adult_measure_raw=13,
                           candidate_is_adult=index == 4,
                           candidate_adult_measure_raw=18 if index == 4 else 14,
                           predicted_outcome_if_accepted="betrothal")
                legal = driver.legality["native_legal_candidates"][index]
                legal["heir_adult_measure_raw"] = 13
                legal["candidate_adult_measure_raw"] = 18 if index == 4 else 14
                if index >= 3:
                    row["candidate_dynasty_id"] = 30 + index
                    row["candidate_house_id"] = 30 + index
                    legal["candidate_dynasty_id"] = 30 + index
                    row["possible_alliance_pairs"] = [{
                        "first_character_id": 101,
                        "second_character_id": 400 + index,
                        "already_allied": False,
                        "both_have_realm_data": True,
                        "would_attempt_if_accepted": True}]
                else:
                    row["candidate_dynasty_id"] = 20
                    legal["candidate_dynasty_id"] = 20
            driver.submit_observed_first_heir_marriage_private_v1 = (
                lambda *, legality, candidate_character_id: {
                    "schema": SCHEMA, "status": "receipt_pending",
                    "material_result": False, "pre_native_revision": 7,
                    "played_character_id": 101, "heir_character_id": 202,
                    "candidate_character_id": candidate_character_id})
            driver.query_observed_first_heir_marriage_result_private_v1 = (
                lambda *, pending: {"status": "betrothal", "material_result": True,
                                    "post_native_revision": 8})
            baseline = {"plan": {"selected_step": "query-declarable-wars"}}
            with patch("xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity",
                       return_value=(55, "created")):
                planned = plan_family_marriage_private(
                    driver, baseline, scene(), prewar_arbitration=True)
                self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
                self.assertEqual(planned["plan"]["family_marriage_choice"]
                                 ["candidate_character_id"], 303)
                self.assertEqual(planned["plan"]["family_marriage_choice"]
                                 ["predicted_outcome_if_accepted"], "betrothal")
                diagnostic = planned["plan"]["family_marriage_private_diagnostic"]
                rows_by_id = {row["candidate_character_id"]: row
                              for row in diagnostic["rows"]}
                self.assertEqual(rows_by_id[303]["rejection_reasons"], [])
                self.assertIn("betrothal_age_gap_out_of_bounds",
                              rows_by_id[304]["rejection_reasons"])
                pending = submit_family_marriage_private(
                    driver, plan=planned["plan"], snapshot=scene())
                self.assertEqual(pending["candidate_character_id"], 303)
                later = {**scene(), "native_revision": 8}
                result_plan = plan_family_marriage_private(
                    driver, baseline, later, prewar_arbitration=True)
                self.assertEqual(result_plan["plan"]["selected_step"], RESULT_STEP)
                result = query_family_marriage_result_private(
                    driver, pending=result_plan["plan"]["family_marriage_pending"],
                    cold=False)
                self.assertEqual(result["status"], "betrothal")
                consumed = plan_family_marriage_private(
                    driver, baseline, later, prewar_arbitration=True)
                self.assertEqual(consumed["plan"]["family_marriage_result_consumed"]
                                 ["status"], "betrothal")

    def test_private_diagnostic_retains_shared_heir_relationship_and_house_gate(self):
        with tempfile.TemporaryDirectory() as temporary:
            driver = FakeDriver(Path(temporary))
            for row in driver.projection["rows"]:
                row["heir_spouse_character_ids"] = [888]
                row["heir_primary_spouse_character_id"] = 888
                row["heir_house_id"] = 22
            planned = plan_family_marriage_private(
                driver, {"plan": {"selected_step": "life-advance"}}, scene())
            rows = planned["plan"]["family_marriage_private_diagnostic"]["rows"]
            self.assertEqual(len(rows), 5)
            self.assertTrue(all(row["heir_spouse_count"] == 1 for row in rows))
            self.assertTrue(all(row["heir_primary_spouse_character_id"] == 888
                                for row in rows))
            self.assertTrue(all("heir_spouse_list_not_empty" in row["rejection_reasons"]
                                and "heir_house_not_played_house" in row["rejection_reasons"]
                                for row in rows))

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
                {**row, "heir_is_adult": False,
                 "predicted_outcome_if_accepted": "betrothal"}
                for row in driver.projection["rows"]]
            no_value = plan_family_marriage_private(
                driver, war, scene(), prewar_arbitration=True)
            self.assertEqual(no_value["plan"]["selected_step"],
                             "query-declarable-wars")
            self.assertEqual(no_value["plan"]["family_marriage_status"],
                             "no_positive_observed_marriage_opportunity")
            self.assertTrue(all(row["heir_is_adult"] is False for row in
                                no_value["plan"]["family_marriage_private_diagnostic"]
                                ["rows"]))

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
                self.assertEqual(planned["plan"]["family_marriage_private_diagnostic"]
                                 ["selected_candidate_character_id"], 300)
                self.assertEqual(planned["plan"]["family_marriage_private_diagnostic"]
                                 ["rows"][0]["rejection_reasons"], [])
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

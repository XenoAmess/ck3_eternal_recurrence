"""Deterministic production binder/consumer paths; no CK3 action is claimed."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.current_first_heir_betrothal_private_action_v1 import SUBMIT_STEP
from xar_autoplayer.bridge.current_first_heir_relationship_private_transport import _COST_FIELDS
from xar_autoplayer.bridge.driver import BridgeUnavailableError
from xar_autoplayer.bridge.observed_heir_marriage_private_action_v1 import (
    RESULT_STEP, query_observed_first_heir_marriage_cold_result_private_v1,
    query_observed_first_heir_marriage_result_private_v1,
)
from xar_autoplayer.current_first_heir_betrothal_formal_consumer import (
    consume_current_first_heir_betrothal_result_checkpoint,
    evaluate_current_betrothal_fulfillment,
    plan_current_first_heir_betrothal_fulfillment_private,
    query_current_first_heir_betrothal_fulfillment_result_private,
    submit_current_first_heir_betrothal_fulfillment_private,
)
from xar_autoplayer.family_marriage_formal_consumer import (
    plan_family_marriage_private, read_family_marriage_ledger,
)


def scene(revision=7, date=53220000):
    return {"snapshot_id": f"paused-{revision}-{date}", "revision": revision,
            "native_revision": revision, "date_raw": date,
            "episode_run_id": "native-29829-2bc2d599f7f9",
            "episode_character_id": 29829, "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "active_wars": [], "played_character": {"character_id": 29829, "alive": True}}


def relation(revision=7):
    # Actual R0405 identities; adulthood/final legality are deterministic
    # positive fixtures, not claims about that live frame.
    return {"schema": "xar.ck3.current-first-heir-relationship.v1",
            "exact_ck3_build": "1.19.0.6", "status": "available", "read_only": True,
            "advertised": False, "native_revision": revision, "root_query_sequence": 1,
            "heir_character_id": 38822, "betrothed_character_id": 38718,
            "primary_spouse_character_id": None, "spouse_character_ids": [],
            "bilateral_verified": True, "betrothal_actionability": {
                "status": "available", "unavailable_reason": None,
                "actor_character_id": 29829, "heir_character_id": 38822,
                "partner_character_id": 38718, "recipient_character_id": 32897,
                "intermediary_character_id": None, "adult_readback_available": True,
                "heir_is_adult": True, "partner_is_adult": True,
                "heir_adult_measure_raw": 19, "partner_adult_measure_raw": 20,
                "heir_adult_threshold_raw": 19, "partner_adult_threshold_raw": 20,
                "ready_to_marry_betrothed": True,
                "final_legality_sampled": True, "complete_can_send": True,
                "recipient_acceptance_ready": True, "recipient_ai_accept_raw": 900000,
                "recipient_answer_status_raw": 0,
                "generic_costs": {"raw_scale": 100000, "payer_role": "actor",
                                  "application_timing": "on_send", **{k: 0 for k in _COST_FIELDS}},
                "effective_matrilineal_if_accepted": False,
                "predicted_outcome_if_accepted": "marriage"}}


class Driver:
    def __init__(self, state_dir):
        self.state_dir = state_dir
        self.allow_private_current_first_heir_betrothal_fulfillment = True
        self.allow_private_current_first_heir_relationship_query = True
        self.pid = 110424
        self.frame = scene()
        self.current_relation = relation()
        self.reads = 0
        self.requests = []
        self.result_status = "pending"
        self.mode = True
        self.fail_send = False
        self.pre = 7
        self.endpoint = self
        self.state = self

    def take_snapshot(self):
        return deepcopy(self.frame)

    def query_current_first_heir_relationship_private_v1(self, *, expected_native_revision):
        self.reads += 1
        assert expected_native_revision == self.frame["native_revision"]
        return deepcopy(self.current_relation)

    def send(self, request):
        self.requests.append(request)

    def wait_for_command_result(self, _request_id, _timeout):
        request = self.requests[-1]
        if self.fail_send:
            return None
        step = request["step"]
        cold = request.get("cold_recovery") == 1
        status = "receipt_pending" if step == SUBMIT_STEP else self.result_status
        material = status in {"marriage", "betrothal"}
        result = {"step": step, "accepted": True, "private_build": True,
                  "advertised": False, "status": status, "material_result": material,
                  "pre_native_revision": 0 if cold else self.pre,
                  "played_character_id": 29829, "heir_character_id": 38822,
                  "candidate_character_id": 38718, "recipient_character_id": 32897,
                  "matrilineal_option_selected": False,
                  "fulfill_existing_betrothal": self.mode}
        if step == RESULT_STEP:
            result.update(post_native_revision=self.frame["native_revision"], cold_recovery=cold)
            if cold:
                active = status == "pending"
                result.update(outbound_pending_state="active" if active else "not_applicable",
                              outbound_pending_id=-469762047 if active else None,
                              outbound_pending_age_days=1 if active else None,
                              outbound_pending_ai_reply_cutoff_days=7 if active else None)
        return {"ok": True, "result": result}

    def _execute_campaign_root_context_v1_query(self, *, expected_revision):
        return {"status": "available", "held_title_partition": [
            {"primary": True, "first_heir_character_id": 38822}]}

    def query_observed_first_heir_marriage_result_private_v1(self, *, pending):
        return query_observed_first_heir_marriage_result_private_v1(self, pending=pending)

    def query_observed_first_heir_marriage_cold_result_private_v1(self, *, pending):
        return query_observed_first_heir_marriage_cold_result_private_v1(self, pending=pending)


class FulfillmentProductionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=os.environ.get("XAR_TEST_TEMP_ROOT"))
        self.addCleanup(self.temp.cleanup)
        self.driver = Driver(Path(self.temp.name))
        identity = lambda d: (d.pid, f"created-{d.pid}")
        for name in ("xar_autoplayer.current_first_heir_betrothal_formal_consumer._identity",
                     "xar_autoplayer.family_marriage_formal_consumer.bridge_process_identity"):
            patcher = patch(name, side_effect=identity)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.planned = {"revision": 7, "plan": {"selected_step": "life-advance"}}

    def select_and_submit(self):
        planned = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        pending = submit_current_first_heir_betrothal_fulfillment_private(
            self.driver, plan=planned["plan"], snapshot=self.driver.take_snapshot())
        return planned, pending

    def test_old_partner_hold_becomes_fixed_pair_typed_pending_without_enumeration(self):
        old = plan_family_marriage_private(self.driver, self.planned, self.driver.take_snapshot())
        self.assertEqual(old["plan"]["family_marriage_status"], "current_first_heir_already_partnered")
        planned, pending = self.select_and_submit()
        self.assertEqual(planned["plan"]["selected_step"], SUBMIT_STEP)
        self.assertEqual(self.driver.requests[0]["candidate_character_id"], 38718)
        self.assertNotIn("query_sequence", self.driver.requests[0])
        self.assertEqual(pending["prior_betrothal_relationship"], relation())
        self.assertIs(pending["fulfill_existing_betrothal"], True)
        self.assertIs(pending["material_result"], False)
        self.assertEqual(pending["resource_proposal"], planned["plan"]["current_betrothal_choice"]["resource_proposal"])
        self.assertEqual(read_family_marriage_ledger(self.driver.state_dir)["pending"], pending)

    def test_same_betrothal_pending_checkpoint_next_turn_and_cold_read_do_not_resend(self):
        _, pending = self.select_and_submit()
        self.driver.frame = scene(8)
        result = query_current_first_heir_betrothal_fulfillment_result_private(
            self.driver, pending=pending, cold=False)
        self.assertEqual(result["status"], "pending")
        self.assertIs(self.driver.requests[-1]["fulfill_existing_betrothal"], True)
        before = self.driver.take_snapshot()
        self.driver.frame = scene(9)
        consume_current_first_heir_betrothal_result_checkpoint(
            self.driver, before=before, snapshot=self.driver.take_snapshot())
        ledger = read_family_marriage_ledger(self.driver.state_dir)
        self.assertEqual(ledger["pending"]["last_checked_native_revision"], 8)
        self.assertEqual(ledger["pending"]["last_consumed_checkpoint_native_revision"], 9)
        for selected in ("life-advance", "set-player-lifestyle-stock-focus-v1-private"):
            followup = plan_current_first_heir_betrothal_fulfillment_private(
                self.driver, {"plan": {"selected_step": selected}}, self.driver.take_snapshot())
            self.assertEqual(followup["plan"]["selected_step"], selected)
        self.driver.frame = scene(9, 53220001)
        later = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        self.assertEqual(later["plan"]["selected_step"], RESULT_STEP)
        self.driver.pid = 9524
        self.driver.frame = scene(1)
        cold = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        self.assertTrue(cold["plan"]["current_betrothal_cold_recovery"])
        result = query_current_first_heir_betrothal_fulfillment_result_private(
            self.driver, pending=cold["plan"]["current_betrothal_pending"], cold=True)
        self.assertEqual(result["status"], "pending")
        self.assertIs(self.driver.requests[-1]["fulfill_existing_betrothal"], True)
        self.assertEqual(self.driver.requests[-1]["cold_recovery"], 1)
        self.assertIs(self.driver.requests[-1]["matrilineal_option_selected"], False)
        self.assertEqual(sum(r["step"] == SUBMIT_STEP for r in self.driver.requests), 1)

    def test_existing_betrothal_or_missing_mode_cannot_clear_pending(self):
        _, pending = self.select_and_submit()
        self.driver.frame = scene(8)
        for status, mode in (("betrothal", True), ("pending", False)):
            self.driver.result_status, self.driver.mode = status, mode
            with self.assertRaises(BridgeUnavailableError):
                query_current_first_heir_betrothal_fulfillment_result_private(
                    self.driver, pending=pending, cold=False)
            self.assertEqual(read_family_marriage_ledger(self.driver.state_dir)["pending"], pending)

    def test_due_pending_or_cold_read_preserves_selected_lifestyle_action(self):
        _, pending = self.select_and_submit()
        action = {"plan": {"selected_step": "set-player-lifestyle-stock-focus-v1-private"}}
        self.driver.frame = scene(8)
        for pid in (110424, 9524):
            self.driver.pid = pid
            self.assertIs(plan_current_first_heir_betrothal_fulfillment_private(
                self.driver, action, self.driver.take_snapshot()), action)
        self.assertEqual(read_family_marriage_ledger(self.driver.state_dir)["pending"], pending)
        self.assertEqual(len(self.driver.requests), 1)
        later = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        self.assertEqual(later["plan"]["selected_step"], RESULT_STEP)
        self.assertTrue(later["plan"]["current_betrothal_cold_recovery"])

    def test_marriage_material_next_turn_and_new_pid_recovery_consume_without_submit(self):
        _, pending = self.select_and_submit()
        self.driver.frame = scene(8)
        self.driver.result_status = "marriage"
        query_current_first_heir_betrothal_fulfillment_result_private(
            self.driver, pending=pending, cold=False)
        ledger = read_family_marriage_ledger(self.driver.state_dir)
        self.assertIsNone(ledger["pending"])
        self.assertEqual(ledger["resolved"]["status"], "marriage")
        self.assertIs(ledger["resolved"]["fulfill_existing_betrothal"], True)
        next_turn = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        self.assertEqual(next_turn["plan"]["selected_step"], "life-advance")
        self.driver.pid = 9524
        self.driver.frame = scene(1)
        cold = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        self.assertTrue(cold["plan"]["current_betrothal_material_recheck"])
        query_current_first_heir_betrothal_fulfillment_result_private(
            self.driver, pending=cold["plan"]["current_betrothal_pending"], cold=True)
        self.assertTrue(read_family_marriage_ledger(self.driver.state_dir)["resolved"]["cold_recovery_verified"])
        self.assertEqual(sum(r["step"] == SUBMIT_STEP for r in self.driver.requests), 1)

    def test_off_existing_action_unknown_and_native_negative_preserve_strategy(self):
        self.driver.allow_private_current_first_heir_betrothal_fulfillment = False
        self.assertIs(plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot()), self.planned)
        self.assertEqual(self.driver.reads, 0)
        self.driver.allow_private_current_first_heir_betrothal_fulfillment = True
        action = {"plan": {"selected_step": "set-player-lifestyle-stock-focus-v1-private"}}
        self.assertIs(plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, action, self.driver.take_snapshot()), action)
        self.assertEqual(self.driver.reads, 0)
        for mutation in (None, {"complete_can_send": False},
                         {"generic_costs": {**relation()["betrothal_actionability"]["generic_costs"], "gold_raw": 100000}},
                         {"heir_is_adult": False, "heir_adult_measure_raw": 18,
                          "ready_to_marry_betrothed": False}):
            self.driver.current_relation = relation()
            if mutation is None:
                self.driver.current_relation.pop("betrothal_actionability")
            else:
                self.driver.current_relation["betrothal_actionability"].update(mutation)
            held = plan_current_first_heir_betrothal_fulfillment_private(
                self.driver, self.planned, self.driver.take_snapshot())
            self.assertEqual(held["plan"]["selected_step"], "life-advance")
            self.assertEqual(held["plan"]["current_betrothal_choice"]["status"], "held")
        self.assertEqual(self.driver.requests, [])

    def test_native_refusal_is_consumed_and_pair_is_not_retried(self):
        _, pending = self.select_and_submit()
        self.driver.frame = scene(8)
        self.driver.result_status = "refused"
        result = query_current_first_heir_betrothal_fulfillment_result_private(
            self.driver, pending=pending, cold=False)
        self.assertFalse(result["material_result"])
        planned = plan_current_first_heir_betrothal_fulfillment_private(
            self.driver, self.planned, self.driver.take_snapshot())
        self.assertEqual(planned["plan"]["current_betrothal_status"], "refused")
        self.assertEqual(planned["plan"]["selected_step"], "life-advance")
        self.assertEqual(sum(r["step"] == SUBMIT_STEP for r in self.driver.requests), 1)

    def test_typed_schema_accepts_fulfillment_ack_but_not_old_betrothal_as_new_material(self):
        from jsonschema import Draft202012Validator
        _, pending = self.select_and_submit()
        schema = json.loads((ROOT / "schemas" /
            "observed-first-heir-marriage-private-action-v1.schema.json").read_text())
        validator = Draft202012Validator(schema)
        validator.validate(pending)
        old_betrothal = {**pending, "step": RESULT_STEP, "status": "betrothal",
                         "material_result": True, "post_native_revision": 8}
        self.assertTrue(list(validator.iter_errors(old_betrothal)))


if __name__ == "__main__":
    unittest.main()

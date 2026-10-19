"""Real R19 adapter entry and finite economic/once policies; no native/game IO."""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import faith_e02_hof_queue as Q
from ck3_mod_acceptance_cases import faith_e02_r19_hof_adapter as A
from ck3_mod_acceptance_client import CaseClient, write_once


def frame(*, actor=31254, date=53144328, after=False):
    return {"source": "injected-dll-named-pipe", "backend_id": "native-headless",
        "episode_projection": "native_campaign", "snapshot_id": "synthetic-r19",
        "revision": 5, "native_revision": 4, "date_raw": date,
        "played_character": {"character_id": actor, "alive": True, "source": "native"},
        "played_character_gold": {"raw": 1800000 if after else 24300000, "scale": 100000},
        "played_character_piety": {"raw": 1450000000 if after else 1480000000, "scale": 100000},
        "paused": True, "map_ready": True, "active_event": None, "episode_run_id": None,
        "diagnostics": {"bridge_pid": 1234, "connection_generation": 4, "hello": {
            "pid": 1234, "connection_generation": 4, "expected_ck3_version": "1.20.0.4",
            "expected_ck3_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518",
            "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64"}}}


def context(root, *, confirm=False, output="output"):
    contract = {"schema": "faith-engine-e02-r19-spiritual-head-case-v1", "product": A.PRODUCT,
        "case": A.CASE, "machine_id": "4-8e1c2f1861",
        "saved_input": {"save": "not-read-by-run.ck3", "bytes": A.SAVE_BYTES,
            "sha256": A.SAVE_SHA256, "player_id": 31254, "date_raw": 53144328},
        "profile": {"enabled_mods": [], "product_files": []},
        "historical_expectation": {"actor": 31254, "faith": 103, "rite": 150,
            "date_raw": 53144328, "fresh_head_absence_not_yet_proven": True},
        "confirm_once_when_ready": confirm, "max_confirm_submissions": 1,
        "decision_key": Q.DECISION, "funds_may_not_be_fabricated": True,
        "once_ledger_root": str(root / "stable-ledger"),
        "prior_setup_disclosure": "Synthetic test; production discloses original R19 preparation"}
    spec = {"id": A.CASE, **{key: False for key in A.ACTION_OPT_INS},
        "required_mcp_tools": sorted(A.SCENE_TOOLS | A.LIFECYCLE_TOOLS | ({Q.CONFIRM} if confirm else set())),
        "opt_in_read_only_mcp_tools": sorted(A.READONLY_TOOLS)}
    target = root / output
    target.mkdir()
    return {"case_contract": contract, "case_spec": spec, "product": A.PRODUCT, "case": A.CASE,
        "run_id": "synthetic-r19", "output": str(target), "shared_source_root": str(ROOT)}


def selected(*, affordable=True, amount=22500000):
    return {"available": True, "decision_key": Q.DECISION, "matching_row_count": 1,
        "played_character_id": 31254, "date_raw": 53144328, "detail_actor_reference_key": 31254,
        **{key: True for key in ("detail_definition_matches_target", "detail_tree_complete",
            "detail_root_visible", "detail_actor_binding_verified")},
        "selected_terms": {"schema": "ck3-selected-decision-terms-v1", "available": True,
            "decision_key": Q.DECISION, "played_character_id": 31254, "date_raw": 53144328,
            "read_only": True, "action_ready": False, "decision_confirm_invoked": False,
            "context_verified": True, "named_parameter_count": 0,
            "context_adapter": "actual_empty_named_parameters_only",
            "requirements_bypass_observed": True, "requirements_bypass_raw": 0,
            "ordinary_legality_observed": True, "ordinary_can_confirm": affordable,
            "can_confirm": affordable, "requirements_description_available": True,
            "cost_description_available": True, "requirements_description": "Synthetic original conditions",
            "cost_description": "Synthetic gold and piety cost", "resource_quote_available": True,
            "resource_quote": {"raw_scale": 100000, "resource_vector_raw": [amount, 0, 30000000, 0, 0, 0, 0, 0, 0, 0],
                "native_affordable": affordable}}}


class Client(CaseClient):
    operator_reviewer = "synthetic-reviewer"

    def __init__(self, c, *, affordable=True, existing_head=False, row_absent=False,
                 creates_head=True, unknown=False, quote_changes=False, post_event=False):
        self.c = c
        self.manifest = {"game": {"version": "1.20.0.4",
            "exe_sha256": "98702f88a547cde2eaf29a85f93b85f68ee4cf8148336a4f7afaeb75319dd518"}}
        self._binding = None
        self.affordable, self.existing_head, self.row_absent = affordable, existing_head, row_absent
        self.creates_head, self.unknown, self.quote_changes = creates_head, unknown, quote_changes
        self.post_event, self.event_selected = post_event, False
        self.submitted = 0
        self.selected = False
        self.calls = []
        self.reviews = []

    def snapshot(self, *, require_event_free=True):
        value = frame(after=self.submitted > 0 and self.creates_head)
        if self.submitted and self.post_event and not self.event_selected:
            value["active_event"] = {"instance_id": 777, "definition_key": "synthetic.1",
                "options": [{"option_number": 3, "enabled": True}, {"option_number": 1, "enabled": True}]}
        return self.validate_frame(value, require_event_free=require_event_free)

    def checkpoint(self, key, value):
        pass

    def root_checkpoint(self, key, value, reserve):
        self.reviews.append(key)
        return {"run_id": self.c["run_id"], "reviewer": self.operator_reviewer, "status": "complete"}

    def execute_plan(self, steps, name, timeout=None, reserve=90):
        self.calls.append(steps[0]["tool"])
        tool = steps[0]["tool"]
        if tool == "ck3_query_player_religion_context_v1":
            value = {"available": True, "played_character_id": 31254,
                "faith_id": 103, "rite_id": 150, "faith_main_rite_id": 150}
        elif tool == "ck3_query_player_rite_governance_v1":
            has_head = self.existing_head or self.submitted and self.creates_head
            value = {"frame_available": True, "heads": {"available": True, "played_character_id": 31254,
                "faith_id": 103, "actor_rite_id": 150, "faith_main_rite_id": 150,
                "faith_religious_head_holder_character_id": 65865 if has_head else None,
                "faith_religious_head_title_id": 9001 if has_head else None}}
        elif tool == "ck3_query_player_holy_site_v1":
            value = {"current_faith_holy_site_ids": [0, 1, 3, 2, 4, 32]}
        elif tool == "ck3_select_ingame_decision_item_v1":
            self.selected = True
            value = {"accepted": True}
        elif tool == Q.QUERY:
            value = selected(affordable=self.affordable,
                amount=22600000 if self.quote_changes and name.endswith("quote-b") else 22500000)
            if not self.selected or self.row_absent:
                value.update(available=not self.row_absent, matching_row_count=0 if self.row_absent else 1)
                value.pop("selected_terms")
        elif tool == Q.EVENT_CONTEXT:
            value = {"accepted": True, "current_event_window_context_ready": True,
                "current_event_window_context": {"schema": "current-event-window-context-v1",
                    "status": "available", "current_event_instance_id": 777, "date_raw": 53144328,
                    "snapshot_revision": 4, "event_definition_key": "synthetic.1",
                    "readiness": {"option_presentation_ready": True}, "options": [
                        {"rendered_index": 0, "native_option_index": 2, "shown": True, "enabled": True},
                        {"rendered_index": 1, "native_option_index": 0, "shown": True, "enabled": True}]}}
        elif tool == Q.EVENT_SELECT:
            self.event_selected = True
            self.event_args = steps[0]["args"]
            value = {"accepted": True, "event_instance_id": 777, "option_number": 3, "option_index": 2}
        elif tool == Q.CONFIRM:
            self.submitted += 1
            if self.unknown:
                raise TimeoutError("synthetic unknown after a single queue submission")
            value = {"postcondition_verified": True, "outcome": "decision_closed",
                "business_outcome_observed": False}
        else:
            value = {"accepted": True}
        row = {"id": name, "ok": True, "error": None, "result": value}
        if tool == Q.EVENT_CONTEXT:
            row["before_snapshot"] = self.snapshot(require_event_free=False)
        write_once(Path(self.c["output"]) / (name + ".actual-results.json"), {"rows": [row]})
        return [row]


class R19EntryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_readonly_eligibility_executes_entry_without_world_confirm(self):
        c = context(self.root)
        client = Client(c)
        result = A.run_case(c, client)
        self.assertTrue(result["readonly_eligibility_observed"])
        self.assertFalse(result["business_pass"])
        self.assertEqual(client.submitted, 0)
        self.assertFalse((self.root / "stable-ledger").exists())

    def test_unaffordable_gold_records_rejection_without_topup_or_confirm(self):
        c = context(self.root, confirm=True)
        client = Client(c, affordable=False)
        result = A.run_case(c, client)
        self.assertFalse(result["readonly_eligibility_observed"])
        self.assertIn("ordinary legality rejected", result["rejection_reason"])
        self.assertEqual(client.submitted, 0)
        self.assertFalse((self.root / "stable-ledger").exists())

    def test_existing_head_stops_before_open_select_or_confirm(self):
        c = context(self.root, confirm=True)
        client = Client(c, existing_head=True)
        result = A.run_case(c, client)
        self.assertIn("already has a Faith head", result["rejection_reason"])
        self.assertNotIn("ck3_select_ingame_decision_item_v1", client.calls)
        self.assertEqual(client.submitted, 0)

    def test_absent_decision_never_selects(self):
        c = context(self.root, confirm=True)
        client = Client(c, row_absent=True)
        result = A.run_case(c, client)
        self.assertIn("row absent", result["rejection_reason"])
        self.assertNotIn("ck3_select_ingame_decision_item_v1", client.calls)

    def test_two_actual_quotes_one_confirm_independent_head_and_wallet(self):
        c = context(self.root, confirm=True)
        client = Client(c)
        result = A.run_case(c, client)
        self.assertTrue(result["head_creation_observed"])
        self.assertTrue(result["wallet_observation_complete"])
        self.assertEqual(result["wallet_delta_raw"], {"gold": -22500000, "piety": -30000000})
        self.assertTrue(result["business_pass"])
        self.assertFalse(result["quote_settlement_resource_index_join_verified"])
        self.assertEqual(client.submitted, 1)
        self.assertEqual(client.calls.count(Q.QUERY), 3)  # keyed + two selected quotes
        self.assertEqual(len(list((self.root / "stable-ledger").glob("*.submit-once.json"))), 1)

    def test_post_confirm_event_keeps_independent_head_wallet_then_native_first_displayed(self):
        c = context(self.root, confirm=True)
        client = Client(c, post_event=True)
        result = A.run_case(c, client)
        self.assertTrue(result["head_creation_observed"])
        self.assertTrue(result["business_pass"])
        self.assertEqual(result["post_active_event"]["instance_id"], 777)
        self.assertEqual(result["wallet_delta_raw"], {"gold": -22500000, "piety": -30000000})
        self.assertTrue((Path(c["output"]) / "r19-hof-independent-poststate.json").exists())
        self.assertEqual(result["event_policy"]["status"], "DRAINED")
        self.assertEqual(client.event_args, {"event_instance_id": 777, "option_number": 3})
        self.assertLess(client.calls.index("ck3_query_player_rite_governance_v1", 2),
                        client.calls.index(Q.EVENT_CONTEXT))
        self.assertEqual(client.calls.count(Q.EVENT_SELECT), 1)
        self.assertEqual(client.submitted, 1)
        event = result["event_policy"]["events"][0]
        self.assertTrue(event["old_instance_gone"])
        self.assertTrue(event["ack_accepted"])

    def test_window_closed_alone_is_not_head_creation(self):
        c = context(self.root, confirm=True)
        client = Client(c, creates_head=False)
        result = A.run_case(c, client)
        self.assertTrue(result["confirm_actual_row"]["result"]["postcondition_verified"])
        self.assertFalse(result["head_creation_observed"])
        self.assertFalse(result["business_pass"])

    def test_changed_second_quote_blocks_before_any_claim_or_submit(self):
        c = context(self.root, confirm=True)
        client = Client(c, quote_changes=True)
        with self.assertRaisesRegex(ValueError, "actual quotes changed"):
            A.run_case(c, client)
        self.assertEqual(client.submitted, 0)
        self.assertFalse(list((self.root / "stable-ledger").glob("*.submit-once.json")))

    def test_unknown_keeps_semantic_once_claim_and_new_run_cannot_resubmit(self):
        c = context(self.root, confirm=True)
        client = Client(c, unknown=True)
        result = A.run_case(c, client)
        self.assertTrue(result["head_creation_observed"])
        self.assertTrue(result["wallet_observation_complete"])
        self.assertTrue(result["business_pass"])
        self.assertIn("TimeoutError", result["submission_outcome_unknown"])
        self.assertEqual(client.calls.count("ck3_query_player_rite_governance_v1"), 3)
        self.assertIn("hof-r19-post-observation", client.reviews)
        self.assertEqual(client.submitted, 1)
        self.assertTrue((Path(c["output"]) / "r19-confirm-unknown.json").exists())
        other = context(self.root, confirm=True, output="other-run-output")
        other["run_id"] = "synthetic-new-run-does-not-reset-intent"
        again = Client(other)
        with self.assertRaises(FileExistsError):
            A.run_case(other, again)
        self.assertEqual(again.submitted, 0)

    def test_finite_queue_refuses_unclaimed_confirm_other_actions_and_bypass(self):
        for tool, args in ((Q.CONFIRM, {"decision_key": Q.DECISION, "expected_outcome": "decision_closed"}),
            ("ck3_start_activity_v1", {}), ("ck3_save_checkpoint", {}), ("ck3_set_speed", {}),
            (Q.QUERY, {"decision_key": "other_decision"})):
            with self.subTest(tool=tool), self.assertRaises(ValueError):
                Q.validate({"steps": [{"id": "bad", "tool": tool, "args": args,
                    "fresh_revision": True, "continue_on_error": True}]})
        row = {"ok": True, "result": selected()}
        row["result"]["selected_terms"]["requirements_bypass_raw"] = 1
        with self.assertRaises(ValueError):
            Q.quote_terms(row, 31254, 53144328)

    def test_contract_never_reuses_old_D1_save_or_unrelated_action_permission(self):
        c = context(self.root)
        c["case_contract"]["saved_input"]["sha256"] = "62d18fe254d658356671269f194319a316729394da6f38b32da0d503bae1cd58"
        with self.assertRaises(ValueError):
            A.validate_contract(c)
        c = context(self.root, output="another")
        c["case_spec"]["opt_in_player_pilgrimage_execution"] = True
        with self.assertRaises(ValueError):
            A.validate_contract(c)


if __name__ == "__main__":
    unittest.main(verbosity=2)

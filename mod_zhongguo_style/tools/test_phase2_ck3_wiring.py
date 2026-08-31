#!/usr/bin/env python3
"""Static CK3-wiring gates for the first v0.4 361 vertical slice.

These checks prove source wiring only.  They intentionally do not label any
path fixture-live or production-live; timed events, UI rendering and resource
deltas still require the later MCP-first CK3 batch.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

from zg361_readiness_data import CUMULATIVE_COUNTS


MOD_ROOT = Path(__file__).resolve().parent.parent


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


class Phase2Ck3WiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.values = read("common/script_values/zg361_values.txt")
        cls.effects = read("common/scripted_effects/zg361_effects.txt")
        cls.events = read("events/zg361_events.txt")
        cls.decisions = read("common/decisions/zg361_decisions.txt")
        cls.interactions = read("common/character_interactions/zg361_interactions.txt")
        cls.scripted_guis = read("common/scripted_guis/zg361_scoreboard_guis.txt")
        cls.bridge = read("gui/zg361_decision_bridge.gui")
        cls.scoreboard = read(
            "common/scripted_effects/zg361_generated_scoreboard_snapshots.txt"
        )

    def test_kpi_is_one_sum_of_eight_frozen_components(self) -> None:
        components = (
            "governance",
            "capability",
            "growth",
            "superior",
            "values",
            "collaboration",
            "jingcha",
            "organization",
        )
        for component in components:
            self.assertEqual(
                self.values.count(f"zg361_kpi_{component}_evidence_value = {{"), 1
            )
            self.assertIn(
                f"name = zg361_evidence_{component} "
                f"value = zg361_kpi_{component}_evidence_value",
                self.effects,
            )
            self.assertEqual(
                self.values.count(f"add = zg361_kpi_{component}_evidence_value"), 1
            )
        self.assertIn("name = zg361_absolute_grade value = 3", self.effects)
        self.assertIn("name = zg361_absolute_grade value = 2", self.effects)
        self.assertIn("name = zg361_absolute_grade value = 1", self.effects)

    def test_case_freezes_owner_cycle_case_facts_and_reason_before_grade(self) -> None:
        freeze = self.effects.index("zg361_freeze_result_case_effect = {")
        apply_grade = self.effects.index("zg361_apply_grade_effect = {")
        call = self.effects.index("zg361_freeze_result_case_effect = yes", apply_grade)
        branch = self.effects.index("zg361_grade_375_apply_effect = yes", apply_grade)
        self.assertLess(freeze, apply_grade)
        self.assertLess(call, branch)
        for variable in (
            "zg361_result_case_owner",
            "zg361_result_cycle_serial",
            "zg361_result_case_serial",
            "zg361_result_absolute_grade",
            "zg361_result_grade_reason",
            "zg361_result_kpi_frozen",
        ):
            self.assertIn(f"name = {variable}", self.effects)

    def test_frozen_values_score_has_reachable_statement_consumer(self) -> None:
        self.assertIn(
            "name = zg361_result_values_frozen value = var:zg361_values",
            self.effects,
        )
        statement = self.events.split("zg361.53 = {", 1)[1]
        self.assertIn(
            "name = zg361_stmt_values_score "
            "value = var:zg361_result_values_frozen",
            statement,
        )

    def test_refusal_only_changes_service_route_and_witness_must_settle(self) -> None:
        notice = self.events.split("zg361.50 = {", 1)[1].split("zg361.51 = {", 1)[0]
        witness = self.events.split("zg361.51 = {", 1)[1].split("zg361.52 = {", 1)[0]
        self.assertIn("name = zg361_result_case_state value = 2", notice)
        self.assertIn("trigger_event = { id = zg361.51 days = 7 }", notice)
        self.assertNotIn("remove_character_modifier = zg361_grade_325", notice)
        self.assertIn("var:zg361_result_case_state = 2", witness)
        self.assertIn("zg361_deliver_325_notice_effect = yes", witness)
        self.assertIn("stale witnessed-delivery token ignored", witness)

    def test_delivery_and_fourfold_settlement_are_idempotent(self) -> None:
        freeze = self.effects.split("zg361_freeze_result_case_effect = {", 1)[
            1
        ].split("zg361_apply_grade_effect = {", 1)[0]
        settlement = self.effects.split(
            "zg361_settle_delivered_325_effect = {", 1
        )[1].split("zg361_appeal_regrade_to_35_effect = {", 1)[0]
        self.assertIn(
            "set_variable = { name = zg361_result_settlement_posted_serial value = 0 }",
            freeze,
        )
        self.assertIn(
            "set_variable = { name = zg361_result_refund_posted_serial value = 0 }",
            freeze,
        )
        self.assertNotIn(
            "remove_variable = zg361_result_settlement_posted_serial", freeze
        )
        self.assertNotIn("remove_variable = zg361_result_refund_posted_serial", freeze)
        delivery = self.effects.split("zg361_deliver_325_notice_effect = {", 1)[
            1
        ].split("zg361_settle_delivered_325_effect = {", 1)[0]
        self.assertIn("var:zg361_result_settlement_posted_serial = 0", delivery)
        self.assertIn("var:zg361_result_settlement_posted_serial = 0", settlement)
        self.assertNotIn(
            "has_variable = zg361_result_settlement_posted_serial", delivery
        )
        self.assertNotIn(
            "has_variable = zg361_result_settlement_posted_serial",
            settlement.split("set_variable = { name = zg361_result_settlement_posted_serial", 1)[0],
        )
        self.assertNotIn(
            "NOT = {\n\t\t\t\thas_variable = zg361_result_settlement_posted_serial",
            delivery + settlement,
        )
        self.assertIn(
            "set_variable = { name = zg361_result_settlement_posted_serial "
            "value = var:zg361_result_case_serial }",
            settlement,
        )
        self.assertIn("name = zg361_result_treasury_before value = treasury", settlement)
        self.assertIn("subtract = treasury", settlement)
        self.assertIn("name = zg361_result_gold_before value = gold", settlement)
        self.assertIn("subtract = gold", settlement)
        self.assertIn("name = zg361_result_merit_before value = merit", settlement)
        self.assertIn("subtract = merit", settlement)
        self.assertIn("name = zg361_result_salary_cut_active value = 1", settlement)
        self.assertIn("id = zg361.52 days = 90", settlement)

    def test_ai_subject_auto_service_uses_same_settlement(self) -> None:
        grade = self.effects.split("zg361_grade_325_apply_effect = {", 1)[1].split(
            "zg361_deliver_325_notice_effect = {", 1
        )[0]
        self.assertIn("limit = { is_ai = yes }", grade)
        self.assertIn("name = zg361_result_delivery_method value = 4", grade)
        self.assertIn("zg361_deliver_325_notice_effect = yes", grade)
        self.assertIn("trigger_event = { id = zg361.50 days = 1 }", grade)

    def test_both_canonical_settlements_queue_the_signed_attribution_relay(self) -> None:
        freeze = self.effects.split("zg361_freeze_result_case_effect = {", 1)[1].split(
            "zg361_apply_grade_effect = {", 1
        )[0]
        delivered = self.effects.split("zg361_settle_delivered_325_effect = {", 1)[1].split(
            "zg361_appeal_regrade_to_35_effect = {", 1
        )[0]
        dispatch = "trigger_event = { id = zg361we.52747 days = 1 }"
        commit = "set_variable = { name = zg361_we_m269_result_relay_queued value = 1 }"
        for settlement in (freeze, delivered):
            posted = settlement.index(
                "set_variable = { name = zg361_result_settlement_posted_serial "
                "value = var:zg361_result_case_serial }"
            )
            dispatch_index = settlement.index(dispatch)
            commit_index = settlement.index(commit)
            self.assertLess(posted, dispatch_index)
            self.assertLess(dispatch_index, commit_index)
            for field in (
                "zg361_we_m269_outcome_pending", "zg361_we_m269_outcome_settled",
                "zg361_we_m269_receipt_choice", "zg361_we_m269_write_owner",
                "zg361_we_m269_write_subject", "zg361_we_m269_write_cycle",
                "zg361_we_m269_write_case",
                "zg361_workforce_attribution_fact_signature_committed",
                "zg361_workforce_attribution_fact_state",
                "zg361_workforce_attribution_fact_consumed",
            ):
                self.assertIn(f"has_variable = {field}", settlement)
            self.assertIn("var:zg361_we_m269_write_subject = this", settlement)
        self.assertEqual(2, self.effects.count(dispatch))
        self.assertEqual(2, self.effects.count(commit))

    def test_appeal_uses_frozen_case_and_refunds_once(self) -> None:
        appeal = self.effects.split("zg361_appeal_regrade_to_35_effect = {", 1)[1].split(
            "zg361_publish_scoreboard_effect = {", 1
        )[0]
        for token in (
            "var:zg361_last_penalty_reviewer = var:zg361_result_case_owner",
            "var:zg361_last_penalty_serial = var:zg361_result_cycle_serial",
            "name = zg361_result_refund_posted_serial value = var:zg361_result_case_serial",
            "add_treasury = var:zg361_result_treasury_paid",
            "add_gold = var:zg361_result_gold_paid",
            "change_merit = { value = var:zg361_result_merit_paid }",
            "name = zg361_result_case_state value = 5",
            "name = zg361_result_appeal_open value = 0",
        ):
            self.assertIn(token, appeal)
        self.assertIn("var:zg361_result_refund_posted_serial = 0", appeal)
        refund_gate = appeal.split(
            "zg361_apply_receipted_appeal_regrade_effect = yes", 1
        )[0]
        self.assertNotIn("has_variable = zg361_result_refund_posted_serial", refund_gate)
        self.assertNotIn(
            "NOT = {\n\t\t\t\thas_variable = zg361_result_refund_posted_serial",
            refund_gate,
        )

    def test_statement_reuses_decision_and_invisible_bridge_not_hud(self) -> None:
        self.assertIn("zg361_view_result_statement_decision = {", self.decisions)
        self.assertIn(
            "add_character_flag = zg361_view_result_statement_pending", self.decisions
        )
        self.assertIn("zg361_view_result_statement_bridge_gui = {", self.scripted_guis)
        self.assertIn("trigger_event = zg361.53", self.scripted_guis)
        self.assertIn('name = "zg361_view_result_statement"', self.bridge)
        self.assertNotIn("button", self.bridge.lower())

    def test_subject_interaction_is_bound_to_frozen_owner_and_open_clock(self) -> None:
        appeal = self.interactions.split("zg361_appeal_interaction = {", 1)[1].split(
            "zg361_review_talk_interaction = {", 1
        )[0]
        self.assertIn("var:zg361_result_case_owner = scope:recipient", appeal)
        self.assertIn("var:zg361_result_case_state = 3", appeal)
        self.assertIn("var:zg361_result_appeal_open = 1", appeal)
        self.assertIn("ai_will_do = { base = 0 }", appeal)

    def test_scoreboard_updates_only_frozen_owner_cycle_copies(self) -> None:
        phase2 = self.scoreboard.split(
            "zg361_update_settled_325_scoreboard_slots_effect = {", 1
        )[1]
        self.assertIn("var:zg361_result_case_owner = {", phase2)
        self.assertIn("zg361_scoreboard_managed_cycle_serial", phase2)
        self.assertIn("zg361_scoreboard_received_cycle_serial", phase2)
        self.assertNotIn("\tliege = {", phase2)
        self.assertNotIn("\tevery_vassal = {", phase2)

    def test_manifest_keeps_exactly_four_first_slice_contracts_live(self) -> None:
        manifest = json.loads(read("docs/361-mechanism-manifest.json"))
        live = {
            item["id"]
            for item in manifest["items"]
            if item["readiness"]["highest_level"] == "ck3-live"
        }
        contracts = {
            item["id"] for item in manifest["items"] if "runtime_contract" in item
        }
        self.assertEqual(live, {1, 18, 69, 357})
        self.assertEqual(contracts, {1, 18, 69, 357})
        self.assertEqual(
            manifest["phase2_static"]["count"],
            CUMULATIVE_COUNTS["ck3-static-ready"],
        )
        self.assertEqual(
            manifest["readiness"]["partial_live_notes"]["018"],
            "receipt/refund is fixture-live; reopening zg361.53 remains static-ready",
        )

    def test_all_product_script_files_keep_utf8_bom(self) -> None:
        paths = (
            "common/script_values/zg361_values.txt",
            "common/scripted_effects/zg361_effects.txt",
            "events/zg361_events.txt",
            "common/decisions/zg361_decisions.txt",
            "common/character_interactions/zg361_interactions.txt",
            "common/scripted_guis/zg361_scoreboard_guis.txt",
            "gui/zg361_decision_bridge.gui",
        )
        for relative in paths:
            with self.subTest(relative=relative):
                self.assertTrue((MOD_ROOT / relative).read_bytes().startswith(b"\xef\xbb\xbf"))


if __name__ == "__main__":
    unittest.main()

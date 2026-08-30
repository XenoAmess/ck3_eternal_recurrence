#!/usr/bin/env python3
"""Static contracts for the F032-036 / AK345-354 CK3 runtime.

These tests prove deterministic source wiring and semantic guards only.  They
must not be cited as MCP, fixture-live, or production-live CK3 evidence.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gen_361_manager_governance_runtime import (
    BINDINGS,
    MOD_ROOT,
    READINESS,
    TARGET_IDS,
    outputs,
)


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


def top_level_block(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", text)
    if match is None:
        raise AssertionError(f"missing top-level block {key}")
    opening = text.index("{", match.start(), match.end())
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[match.start() : index + 1]
    raise AssertionError(f"unterminated top-level block {key}")


def assert_balanced(test: unittest.TestCase, text: str, label: str) -> None:
    depth = 0
    quoted = False
    escaped = False
    for line_number, line in enumerate(text.splitlines(), 1):
        code = line.split("#", 1)[0]
        for char in code:
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
                continue
            if char == '"':
                quoted = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                test.assertGreaterEqual(depth, 0, f"{label}:{line_number}: extra close brace")
    test.assertFalse(quoted, f"{label}: unterminated quote")
    test.assertEqual(depth, 0, f"{label}: brace imbalance")


def localization_keys(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for match in re.finditer(r'^\s+([^\s:]+):\d+\s+"', text, flags=re.MULTILINE)
    )


class ManagerGovernanceRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(
            "common/scripted_effects/zg361_manager_governance_runtime_effects.txt"
        )
        cls.events = read("events/zg361_manager_governance_runtime_events.txt")
        cls.case_effects = read("common/scripted_effects/zg361_case_kernel_effects.txt")
        cls.case_triggers = read("common/scripted_triggers/zg361_case_kernel_triggers.txt")
        cls.triggers = read("common/scripted_triggers/zg361_triggers.txt")
        cls.activity = read("common/activities/activity_types/zg361_jingcha.txt")
        cls.jingcha_events = read("events/zg361_jingcha_events.txt")
        cls.jingcha_mandate = read(
            "common/scripted_effects/zg361_jingcha_mandate_effects.txt"
        )
        cls.core = read("common/scripted_effects/zg361_effects.txt")
        cls.values = read("common/script_values/zg361_values.txt")
        cls.loc_en = read(
            "localization/english/zg361_manager_governance_l_english.yml"
        )
        cls.loc_zh = read(
            "localization/simp_chinese/zg361_manager_governance_l_simp_chinese.yml"
        )
        cls.spec = read("docs/361-phase2-manager-governance-ck3-runtime-spec.md")

    def test_exact_owned_ids_and_explicit_operation_map(self) -> None:
        expected = (*range(32, 37), *range(345, 355))
        self.assertEqual(TARGET_IDS, expected)
        self.assertEqual(len(BINDINGS), 15)
        self.assertEqual({row.domain for row in BINDINGS}, {"F", "AK"})
        self.assertEqual(len({row.operation for row in BINDINGS}), 15)
        self.assertFalse(set(TARGET_IDS) & set(range(312, 334)))
        self.assertNotIn("zg361_mg_m312", self.effects)
        self.assertNotIn("zg361_mg_m333", self.effects)

    def test_readiness_is_honest(self) -> None:
        self.assertEqual(READINESS, "static-ready")
        self.assertIn("Readiness: `static-ready`", self.spec)
        self.assertIn("MCP evidence: `none`", self.spec)
        self.assertIn("CK3 live evidence: `none`", self.spec)
        self.assertNotIn("fixture-live", self.spec.split("## Readiness boundary", 1)[0])

    def test_generated_outputs_are_current_bom_and_isolated(self) -> None:
        rendered = outputs()
        self.assertEqual(len(rendered), 11)
        allowed_roots = {
            "common/scripted_effects/zg361_manager_governance_runtime_effects.txt",
            "events/zg361_manager_governance_runtime_events.txt",
        }
        for path, payload in rendered.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_bytes(), payload)
                self.assertTrue(payload.startswith(b"\xef\xbb\xbf"))
                relative = path.relative_to(MOD_ROOT).as_posix()
                self.assertTrue(
                    relative in allowed_roots
                    or relative.startswith("localization/")
                    and "zg361_manager_governance_l_" in relative
                )
        for source in (
            MOD_ROOT / "tools" / "gen_361_manager_governance_runtime.py",
            MOD_ROOT / "tools" / "test_zg361_manager_governance_runtime.py",
            MOD_ROOT / "docs" / "361-phase2-manager-governance-ck3-runtime-spec.md",
        ):
            self.assertTrue(source.read_bytes().startswith(b"\xef\xbb\xbf"), source)

    def test_ck3_files_are_balanced_and_top_level_keys_unique(self) -> None:
        assert_balanced(self, self.effects, "effects")
        assert_balanced(self, self.events, "events")
        for text, label in ((self.effects, "effects"), (self.events, "events")):
            keys = re.findall(r"(?m)^([A-Za-z0-9_.]+)\s*=\s*\{", text)
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            self.assertEqual(duplicates, [], label)

    def test_every_id_has_effect_receipt_consumer_and_caller(self) -> None:
        caller_surface = self.effects + "\n" + self.events
        for row in BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                block = top_level_block(self.effects, row.effect)
                receipt = f"zg361_mg_m{row.mechanism_id:03d}_receipt_case"
                self.assertIn(receipt, block)
                self.assertIn("zg361_case_kernel_record_operation_effect", block)
                self.assertIn("zg361_case_kernel_receipt_is_current_trigger", block)
                self.assertIn(row.consumer, self.effects + self.events + self.loc_en)
                self.assertGreaterEqual(caller_surface.count(row.effect), 2)

    def test_shared_kernel_domains_and_stage_transitions_are_reused(self) -> None:
        for key in (
            "zg361_case_f_open_effect",
            "zg361_case_f_advance_01_effect",
            "zg361_case_f_advance_02_effect",
            "zg361_case_f_advance_03_effect",
            "zg361_case_f_advance_04_effect",
            "zg361_case_ak_open_effect",
            "zg361_case_ak_advance_01_effect",
            "zg361_case_ak_advance_02_effect",
            "zg361_case_ak_advance_03_effect",
            "zg361_case_ak_advance_04_effect",
            "zg361_case_ak_advance_05_effect",
        ):
            self.assertIn(f"{key} = {{", self.case_effects)
            self.assertIn(f"{key} =", self.effects)
        self.assertIn("zg361_case_kernel_full_guard_trigger", self.case_triggers)
        self.assertIn("trigger_else = { always = no }", self.case_triggers)

    def test_permission_matrix_player_ai_duke_and_assessed_only(self) -> None:
        dispatcher = top_level_block(
            self.effects, "zg361_mg_dispatch_subordinate_managers_effect"
        )
        opener = top_level_block(
            self.effects, "zg361_mg_open_manager_governance_cases_effect"
        )
        self.assertIn("zg361_is_celestial_liege_trigger = yes", dispatcher)
        self.assertIn("zg361_is_celestial_liege_trigger = yes", opener)
        self.assertIn("liege = root", opener)
        self.assertNotIn("is_ai = no", dispatcher)
        self.assertIn("eligible AI manager report projected silently", self.effects)
        self.assertIn("eligible AI policy governance completed silently", self.effects)
        self.assertIn("is_ai = no", top_level_block(self.events, "zg361mg.120"))
        self.assertIn("is_ai = no", top_level_block(self.events, "zg361mg.220"))
        celestial = top_level_block(self.triggers, "zg361_is_celestial_liege_trigger")
        reviewed = top_level_block(self.triggers, "zg361_is_reviewable_vassal_trigger")
        self.assertIn("highest_held_title_tier >= tier_duchy", celestial)
        self.assertIn("liege = { zg361_is_celestial_liege_trigger = yes }", reviewed)
        self.assertNotIn("tier_county", reviewed)

    def test_manager_is_owned_and_assessed_by_direct_superior(self) -> None:
        opener = top_level_block(
            self.effects, "zg361_mg_open_manager_governance_cases_effect"
        )
        snapshot = top_level_block(
            self.effects, "zg361_mg_freeze_team_snapshot_effect"
        )
        self.assertIn("liege = root", opener)
        self.assertIn("zg361_case_f_open_effect = yes", opener)
        self.assertIn("zg361_case_ak_open_effect = yes", opener)
        self.assertIn("value = root.var:zg361_review_serial", snapshot)
        self.assertIn("value = var:zg361_review_serial", snapshot)
        self.assertIn("var:zg361_review_serial < root.var:zg361_review_serial", opener)

    def test_jingcha_is_free_default_mandatory_and_ai_silent(self) -> None:
        self.assertRegex(
            self.activity,
            r"cost\s*=\s*\{\s*treasury\s*=\s*\{\s*value\s*=\s*0",
        )
        self.assertRegex(
            self.activity,
            r"ui_predicted_cost\s*=\s*\{\s*treasury\s*=\s*\{\s*value\s*=\s*0",
        )
        mandate = top_level_block(self.jingcha_events, "zg361.40")
        self.assertLess(mandate.index("name = zg361.40.a"), mandate.index("name = zg361.40.b"))
        self.assertIn("open_view_data", mandate)
        self.assertIn("zg361_refuse_jingcha_effect = yes", mandate)
        self.assertIn("limit = { is_ai = yes }", self.jingcha_mandate)
        self.assertIn("AI jingcha duty entered the background performance season", self.jingcha_mandate)
        self.assertNotRegex(self.activity, r"remove_treasury|add_gold|remove_gold")

    def test_refusal_exact_minus_25_and_kpi_minus_50_once(self) -> None:
        adapter = top_level_block(
            self.effects, "zg361_mg_refuse_jingcha_exact_effect"
        )
        scorer = top_level_block(self.effects, "zg361_mg_m032_score_manager_effect")
        self.assertIn("opinion = -25", adapter)
        self.assertIn("remove_opinion", adapter)
        self.assertIn("zg361_mg_refusal_opinion_exact_superior", adapter)
        self.assertIn("value = -50", adapter)
        self.assertIn("opinion = -25", scorer)
        self.assertIn("remove_opinion", scorer)
        self.assertIn("zg361_mg_refusal_opinion_exact_match", scorer)
        self.assertIn("zg361_mg_refusal_score_consumed_cycle", scorer)
        self.assertIn("zg361_skipped_jingcha_kpi_malus_value = 50", self.values)
        evidence_write = self.core.index(
            "name = zg361_evidence_jingcha value = zg361_kpi_jingcha_evidence_value"
        )
        marker_remove = self.core.index("remove_variable = zg361_skipped_jingcha_superior")
        self.assertLess(evidence_write, marker_remove)
        kpi_evidence = top_level_block(self.values, "zg361_kpi_jingcha_evidence_value")
        self.assertIn("var:zg361_skipped_jingcha_superior = liege", kpi_evidence)
        self.assertIn("subtract = zg361_skipped_jingcha_kpi_malus_value", kpi_evidence)

    def test_player_manager_window_shows_the_score_and_reasons(self) -> None:
        event = top_level_block(self.events, "zg361mg.120")
        self.assertIn("desc = zg361mg.120.desc", event)
        for variable in (
            "zg361_mg_manager_score",
            "zg361_mg_snapshot_source_serial",
            "zg361_case_f_cycle_serial",
            "zg361_mg_reason_total",
            "zg361_mg_nine_box_code",
        ):
            self.assertIn(f"MakeScope.Var('{variable}').GetValue", self.loc_en)
            self.assertIn(f"MakeScope.Var('{variable}').GetValue", self.loc_zh)

    def test_f032_uses_only_strictly_prior_seven_metric_aggregate(self) -> None:
        snapshot = top_level_block(
            self.effects, "zg361_mg_freeze_team_snapshot_effect"
        )
        scorer = top_level_block(self.effects, "zg361_mg_m032_score_manager_effect")
        metrics = (
            "targets",
            "jingcha",
            "calibration",
            "pip_success",
            "appeal_overturn",
            "retention",
            "hc_efficiency",
        )
        for metric in metrics:
            self.assertIn(f"zg361_mg_team_{metric}", scorer)
        self.assertIn(
            "var:zg361_mg_snapshot_source_serial < var:zg361_case_f_cycle_serial",
            scorer,
        )
        self.assertIn("zg361_mg_snapshot_grandchild_id_count value = 0", snapshot)
        self.assertNotIn("add_to_variable_list", snapshot)

    def test_f033_reason_codes_are_bounded_and_relationship_is_explicit(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m033_reason_code_effect")
        for reason in ("calibration", "appeal", "pip", "delivery", "hc"):
            self.assertIn(f"zg361_mg_reason_{reason}", block)
        self.assertGreaterEqual(block.count("max = 25 min = -25"), 5)
        self.assertIn("zg361_mg_reason_relationship_once value = 5", block)
        self.assertIn("zg361_mg_reason_appeal_risk value = 5", block)
        self.assertNotIn("set_variable = { name = zg361_kpi", block)

    def test_f034_first_cycle_is_unclassified_but_nonblocking_and_read_only(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m034_freeze_nine_box_effect")
        self.assertIn("zg361_mg_history_count value = 1", block)
        self.assertIn("zg361_mg_history_count value = 2", block)
        self.assertIn("zg361_mg_nine_box_ready value = 0", block)
        self.assertIn("zg361_mg_nine_box_ready value = 1", block)
        self.assertIn("zg361_mg_nine_box_code value = 0", block)
        self.assertIn("zg361_mg_previous_manager_score_serial", block)
        self.assertIn("zg361_result_cycle_serial", block)
        self.assertIn("CODE = 6 MECHANISM = 34", block)
        self.assertLess(block.index("CODE = 6 MECHANISM = 34"), block.index("zg361_case_f_advance_03_effect"))
        for forbidden in (
            "name = zg361_kpi",
            "name = zg361_pending_grade",
            "add_gold",
            "remove_treasury",
            "zg361_mg_admin_capacity_available add",
        ):
            self.assertNotIn(forbidden, block)

    def test_f035_distribution_modes_and_conservation(self) -> None:
        block = top_level_block(
            self.effects, "zg361_mg_m035_freeze_distribution_effect"
        )
        self.assertIn("multiply = 0.10", block)
        self.assertIn("multiply = 0.05", block)
        self.assertIn("zg361_mg_distribution_bottom_slots value = 0", block)
        self.assertIn("var:zg361_mg_team_n >= 5", block)
        self.assertIn("zg361_mg_distribution_bottom_consequence value = 2", block)
        self.assertIn(
            "add = var:zg361_mg_distribution_middle_slots add = var:zg361_mg_distribution_bottom_slots",
            block,
        )
        scorer = top_level_block(self.effects, "zg361_mg_m032_score_manager_effect")
        self.assertIn(
            "var:zg361_mg_distribution_conserved = var:zg361_mg_team_n", scorer
        )

    def test_f036_decade_log_owner_year_and_net_flow(self) -> None:
        reset = top_level_block(self.effects, "zg361_mg_reset_decade_log_effect")
        block = top_level_block(self.effects, "zg361_mg_m036_append_decade_log_effect")
        for field in (
            "grade_top",
            "grade_middle",
            "grade_bottom",
            "appeal_overturns",
            "pip_successes",
            "promotions",
            "exits",
            "bonus_in",
            "bonus_out",
            "hc_efficiency",
            "talent_outflow",
            "governance_score",
            "manager_reputation",
        ):
            self.assertIn(f"zg361_mg_decade_{field}", reset + block)
        self.assertIn("NOT = { var:zg361_mg_decade_owner = var:zg361_case_f_owner }", block)
        self.assertIn("var:zg361_mg_expected_log_year = current_year", block)
        self.assertIn("var:zg361_mg_decade_log_count = 10", block)
        self.assertIn("value = var:zg361_mg_decade_bonus_in subtract = var:zg361_mg_decade_bonus_out", block)

    def test_ak345_calendar_is_future_exact_and_batched(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m345_freeze_calendar_effect")
        self.assertIn("value = var:zg361_case_ak_cycle_serial add = 1", block)
        for final_n in (1, 2, 4):
            self.assertIn(f"zg361_mg_calendar_final_n value = {final_n}", block)
        self.assertIn("zg361_mg_calendar_checkin_n value = 1", block)
        self.assertIn("zg361_mg_calendar_player_ai_batch value = 1", block)

    def test_ak346_material_signal_is_once_and_never_reruns_cohort(self) -> None:
        record = top_level_block(self.effects, "zg361_mg_record_offcycle_signal_effect")
        consume = top_level_block(
            self.effects, "zg361_mg_m346_consume_offcycle_signal_effect"
        )
        self.assertIn("$MATERIALITY$ >= 50", record)
        self.assertIn("NOT = { has_variable = zg361_mg_offcycle_pending }", record)
        self.assertIn("zg361_mg_offcycle_cohort_reruns value = 0", consume)
        self.assertIn("remove_variable = zg361_mg_offcycle_pending", consume)
        self.assertIn("zg361_mg_offcycle_consumed_cycle", consume)

    def test_ak347_override_has_three_part_receipt_and_quota_neutrality(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m347_consume_override_effect")
        for token in ("beneficiary", "bearer", "reason"):
            self.assertIn(f"zg361_mg_override_{token}", block)
        self.assertIn("var:zg361_mg_override_used < var:zg361_mg_override_budget", block)
        self.assertIn("zg361_mg_override_quota_before", block)
        self.assertIn("zg361_mg_override_quota_after", block)
        self.assertIn("zg361_mg_override_quota_neutral value = 1", block)
        stage = top_level_block(self.effects, "zg361_mg_ak_stage_2_effect")
        self.assertIn("var:zg361_mg_override_quota_neutral = 1", stage)

    def test_ak348_exception_deadline_is_fully_bound_and_stale_safe(self) -> None:
        bind = top_level_block(self.effects, "zg361_mg_m348_bind_exception_effect")
        due = top_level_block(self.events, "zg361mg.250")
        resolve = top_level_block(
            self.effects, "zg361_mg_resolve_exception_due_effect"
        )
        for token in ("owner", "subject", "cycle", "case", "state", "expiry"):
            self.assertIn(f"zg361_mg_exception_ticket_{token}", bind + due + resolve)
        self.assertIn("days = 365", bind)
        self.assertIn("zg361_mg_exception_default_restored value = 1", resolve)
        self.assertIn("zg361_mg_exception_new_evidence = 1", resolve)
        self.assertIn("stale policy-exception deadline ignored", due)

    def test_ak349_audit_is_reproducible_and_capacity_transactional(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m349_run_audit_effect")
        refund = top_level_block(self.effects, "zg361_mg_refund_audit_capacity_effect")
        self.assertIn("zg361_mg_audit_seed", block)
        self.assertIn("zg361_mg_audit_selection_fingerprint", block)
        self.assertIn("zg361_mg_audit_high_risk_n", block)
        self.assertIn("subtract = 5 max = 1", block)
        self.assertIn("zg361_case_kernel_reserve_transaction_effect", block)
        self.assertIn("zg361_case_kernel_settle_transaction_effect", block)
        self.assertIn("zg361_case_kernel_refund_transaction_effect", refund)
        self.assertIn("CODE = 5 MECHANISM = 349", block)
        self.assertIn("add = var:zg361_mg_audit_clean", block)

    def test_ak350_352_history_and_benchmark_are_append_only(self) -> None:
        benchmark = top_level_block(
            self.effects, "zg361_mg_m350_version_benchmark_effect"
        )
        mapping = top_level_block(self.effects, "zg361_mg_m352_map_history_effect")
        self.assertIn("zg361_mg_benchmark_history_value", benchmark)
        self.assertIn("zg361_mg_benchmark_history_formula", benchmark)
        self.assertIn("zg361_mg_benchmark_history_version", benchmark)
        self.assertIn("zg361_mg_calendar_effective_cycle", benchmark)
        for original in ("value", "formula", "policy_version"):
            self.assertIn(f"zg361_mg_history_original_{original}", mapping)
        self.assertIn("zg361_mg_history_mapped_value", mapping)
        self.assertIn("zg361_mg_history_new_series", mapping)
        self.assertNotIn("remove_variable = zg361_mg_history_original", mapping)

    def test_ak351_pilot_control_are_disjoint_and_complete_before_difference(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m351_measure_pilot_effect")
        self.assertIn("max = 2", block)
        self.assertIn("zg361_mg_pilot_region", block)
        self.assertIn("zg361_mg_control_region", block)
        self.assertIn("NOT = { var:zg361_mg_pilot_region = var:zg361_mg_control_region }", block)
        self.assertIn("has_variable = zg361_mg_pilot_outcome", block)
        self.assertIn("has_variable = zg361_mg_control_outcome", block)
        self.assertIn("zg361_mg_pilot_difference", block)
        stage = top_level_block(self.effects, "zg361_mg_ak_stage_4_effect")
        self.assertNotIn("var:zg361_mg_pilot_result_ready = 1", stage)
        self.assertIn("does not permanently deadlock", stage)

    def test_ak353_admin_components_charge_capacity_and_feed_next_manager_score(self) -> None:
        block = top_level_block(
            self.effects, "zg361_mg_m353_charge_admin_capacity_effect"
        )
        refund = top_level_block(self.effects, "zg361_mg_refund_admin_capacity_effect")
        for component in ("form", "meeting", "appeal", "calibration", "interruption"):
            self.assertIn(f"zg361_mg_admin_{component}_hours", block)
        self.assertIn("zg361_case_kernel_reserve_transaction_effect", block)
        self.assertIn("zg361_case_kernel_settle_transaction_effect", block)
        self.assertIn("zg361_case_kernel_refund_transaction_effect", refund)
        self.assertIn("zg361_mg_manager_score_delta", block)
        snapshot = top_level_block(
            self.effects, "zg361_mg_freeze_team_snapshot_effect"
        )
        self.assertIn("add = var:zg361_mg_manager_score_delta", snapshot)

    def test_ak354_recomputes_raw_rates_and_gates_long_term_trust(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m354_audit_fairness_effect")
        for raw in ("appeals", "overturns", "exits", "healthy_exits"):
            self.assertIn(f"zg361_mg_fairness_raw_{raw}", block)
        for gap in ("appeal", "overturn", "exit"):
            self.assertIn(f"zg361_mg_fairness_gap_{gap}", block)
        self.assertIn("zg361_mg_fairness_gaming value = 1", block)
        trust_branch = block.split("zg361_mg_fairness_trust_delta value = 0", 1)[1]
        self.assertIn("zg361_mg_fairness_self_disclosed = 1", trust_branch)
        self.assertIn("zg361_mg_fairness_remediation_completed = 1", trust_branch)
        self.assertIn("zg361_mg_fairness_trust_delta value = 5", trust_branch)

    def test_all_delayed_stage_events_bind_full_ticket_and_stale_noop(self) -> None:
        for event_id, domain, state in (
            (100, "f", 1),
            (101, "f", 2),
            (102, "f", 3),
            (103, "f", 4),
            (200, "ak", 1),
            (201, "ak", 2),
            (202, "ak", 3),
            (203, "ak", 4),
            (204, "ak", 5),
        ):
            with self.subTest(event=event_id):
                block = top_level_block(self.events, f"zg361mg.{event_id}")
                for token in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"zg361_mg_{domain}_ticket_{token}", block)
                self.assertIn(f"var:zg361_case_{domain}_state = {state}", block)
                self.assertIn("stale", block)
                self.assertIn("ignored", block)

    def test_no_gold_charge_in_non_gold_slice_and_capacity_refunds_exist(self) -> None:
        # Manifest/L0 contracts give these 15 IDs only capacity-hours.  The
        # user's dual-payer gold rule is therefore not spuriously applied here.
        for command in ("add_gold =", "remove_treasury =", "add_treasury =", "remove_gold ="):
            self.assertNotIn(command, self.effects)
        self.assertEqual(self.effects.count("zg361_case_kernel_reserve_transaction_effect"), 2)
        self.assertEqual(self.effects.count("zg361_case_kernel_settle_transaction_effect"), 2)
        self.assertEqual(self.effects.count("zg361_case_kernel_refund_transaction_effect"), 2)

    def test_no_new_top_level_gui_or_central_surface(self) -> None:
        rendered_paths = {path.relative_to(MOD_ROOT).as_posix() for path in outputs()}
        forbidden = {
            "common/scripted_effects/zg361_effects.txt",
            "events/zg361_events.txt",
            "common/character_interactions/zg361_interactions.txt",
            "gui/zg361_scoreboard.gui",
            "common/scripted_effects/zg361_b1_runtime_effects.txt",
            "common/scripted_effects/zg361_b2_runtime_effects.txt",
            "common/scripted_effects/zg361_case_kernel_effects.txt",
        }
        self.assertFalse(rendered_paths & forbidden)
        self.assertFalse(any(path.startswith("gui/") for path in rendered_paths))
        self.assertNotIn("button_", self.effects)

    def test_nine_localizations_have_key_parity_and_placeholders_are_honest(self) -> None:
        expected_keys = localization_keys(self.loc_en)
        self.assertEqual(expected_keys, localization_keys(self.loc_zh))
        self.assertEqual(len(expected_keys), 6)
        for language in (
            "french",
            "german",
            "japanese",
            "korean",
            "polish",
            "russian",
            "spanish",
        ):
            text = read(
                f"localization/{language}/zg361_manager_governance_l_{language}.yml"
            )
            self.assertEqual(expected_keys, localization_keys(text))
            self.assertEqual(
                text.replace(f"l_{language}:", "l_english:", 1), self.loc_en
            )
        self.assertIn("English structural placeholders", self.spec)
        self.assertIn("not release-grade translations", self.spec)


if __name__ == "__main__":
    unittest.main()

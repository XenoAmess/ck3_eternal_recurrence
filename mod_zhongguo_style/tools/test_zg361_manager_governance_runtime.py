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
    COLLECTIVE_COST_ORDINALS,
    INPUT_FINGERPRINT_GUARDS,
    INPUT_FINGERPRINT_OPAQUE_VARS,
    INPUT_FINGERPRINT_RAW_VALUES,
    INPUT_FINGERPRINT_VARS,
    MOD_ROOT,
    DISTRIBUTION_DUE_GUARD,
    ORGANIZATION_DUE_GUARD,
    Q_PROJECTION_IDS,
    READINESS,
    SHARED_HOOK_CONTRACT,
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
        cls.manager_triggers = read(
            "common/scripted_triggers/zg361_manager_governance_runtime_triggers.txt"
        )
        cls.events = read("events/zg361_manager_governance_runtime_events.txt")
        cls.case_effects = read("common/scripted_effects/zg361_case_kernel_effects.txt")
        cls.case_triggers = read("common/scripted_triggers/zg361_case_kernel_triggers.txt")
        cls.career_hc_effects = read(
            "common/scripted_effects/zg361_career_hc_runtime_effects.txt"
        )
        cls.triggers = read("common/scripted_triggers/zg361_triggers.txt")
        cls.activity = read("common/activities/activity_types/zg361_jingcha.txt")
        cls.jingcha_events = read("events/zg361_jingcha_events.txt")
        cls.jingcha_mandate = read(
            "common/scripted_effects/zg361_jingcha_mandate_effects.txt"
        )
        cls.core = read("common/scripted_effects/zg361_effects.txt")
        cls.values = read("common/script_values/zg361_values.txt")
        cls.manager_values = read(
            "common/script_values/zg361_manager_governance_runtime_values.txt"
        )
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
        self.assertEqual(len(rendered), 13)
        allowed_roots = {
            "common/scripted_effects/zg361_manager_governance_runtime_effects.txt",
            "common/scripted_triggers/zg361_manager_governance_runtime_triggers.txt",
            "common/script_values/zg361_manager_governance_runtime_values.txt",
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

    def test_manager_sources_models_tests_and_spec_keep_utf8_bom(self) -> None:
        for relative in (
            "tools/gen_361_manager_governance_runtime.py",
            "tools/zg361_manager_governance_model.py",
            "tools/test_zg361_manager_governance_model.py",
            "tools/test_zg361_manager_governance_runtime.py",
            "docs/361-phase2-manager-governance-ck3-runtime-spec.md",
        ):
            with self.subTest(path=relative):
                self.assertTrue((MOD_ROOT / relative).read_bytes().startswith(b"\xef\xbb\xbf"))
        for source in (
            MOD_ROOT / "tools" / "gen_361_manager_governance_runtime.py",
            MOD_ROOT / "tools" / "test_zg361_manager_governance_runtime.py",
            MOD_ROOT / "docs" / "361-phase2-manager-governance-ck3-runtime-spec.md",
        ):
            self.assertTrue(source.read_bytes().startswith(b"\xef\xbb\xbf"), source)

    def test_ck3_files_are_balanced_and_top_level_keys_unique(self) -> None:
        assert_balanced(self, self.effects, "effects")
        assert_balanced(self, self.manager_triggers, "manager_triggers")
        assert_balanced(self, self.events, "events")
        assert_balanced(self, self.manager_values, "manager_values")
        for text, label in (
            (self.effects, "effects"),
            (self.manager_triggers, "manager_triggers"),
            (self.events, "events"),
            (self.manager_values, "manager_values"),
        ):
            keys = re.findall(r"(?m)^([A-Za-z0-9_.]+)\s*=\s*\{", text)
            duplicates = sorted({key for key in keys if keys.count(key) > 1})
            self.assertEqual(duplicates, [], label)

    def test_calculated_numeric_equality_uses_ck3_value_comparison_grammar(self) -> None:
        # CK3 1.19.0.6 parses ``var:x = { value = ... add/multiply = ... }``
        # as a nested trigger block and reports value/add/multiply as unknown
        # triggers.  Exact numeric equality must instead be expressed as the
        # conjunction of the engine-supported calculated >= and <= forms.
        illegal = re.compile(
            r"\b(?:scope:[A-Za-z0-9_]+\.)?var:[A-Za-z0-9_.:]+\s+=\s+\{\s*value\s*="
        )
        for text, label in (
            (self.effects, "effects"),
            (self.manager_triggers, "manager_triggers"),
            (self.events, "events"),
            (self.manager_values, "manager_values"),
        ):
            with self.subTest(file=label):
                self.assertIsNone(illegal.search(text), label)

        due_expression = "value = var:zg361_mg_organization_input_source_cycle add = 1"
        exact_due = (
            "AND = { var:zg361_mg_organization_input_due_cycle >= { "
            f"{due_expression} }} var:zg361_mg_organization_input_due_cycle <= {{ "
            f"{due_expression} }} }}"
        )
        self.assertEqual(self.manager_values.count(exact_due), 1)
        self.assertEqual(self.effects.count(exact_due), 1)
        for ordinal in COLLECTIVE_COST_ORDINALS:
            expression = (
                "value = scope:zg361_we_m360_cost_subject.var:"
                f"zg361_we_al_external_collective_{ordinal}_cohort_id "
                "multiply = 1000 add = 360"
            )
            exact_receipt_id = (
                "AND = { var:zg361_mg_m360_cost_receipt_id >= { "
                f"{expression} }} var:zg361_mg_m360_cost_receipt_id <= {{ "
                f"{expression} }} }}"
            )
            self.assertGreaterEqual(self.manager_triggers.count(exact_receipt_id), 2)
            self.assertEqual(self.effects.count(exact_receipt_id), 1)

    def test_f032_is_due_once_inside_official_component_eight(self) -> None:
        official = top_level_block(self.values, "zg361_kpi_value")
        organization = top_level_block(
            self.values, "zg361_kpi_organization_evidence_value"
        )
        due_value = top_level_block(
            self.manager_values, "zg361_mg_due_organization_kpi_value"
        )
        scorer = top_level_block(self.effects, "zg361_mg_m032_score_manager_effect")
        settle = top_level_block(
            self.effects, "zg361_mg_settle_due_organization_kpi_effect"
        )
        official_addends = re.findall(r"(?m)^\s*add = (zg361_kpi_[a-z_]+_evidence_value)$", official)
        self.assertEqual(len(official_addends), 8)
        self.assertEqual(official_addends[-1], "zg361_kpi_organization_evidence_value")
        self.assertNotIn("zg361_mg_due_organization_kpi_value", official)
        self.assertIn("zg361_mg_organization_input_component value = 8", scorer)
        self.assertIn("zg361_mg_organization_input_due_cycle", scorer)
        self.assertIn("zg361_mg_organization_input_status value = 1", scorer)
        self.assertIn("var:zg361_mg_organization_input_status = 1", due_value)
        self.assertIn("add = var:zg361_mg_organization_input_value", due_value)
        self.assertIn("zg361_mg_organization_input_status value = 2", settle)
        self.assertIn("zg361_mg_organization_settlement_receipt", settle)
        # The shared file is root-owned.  Pin its unique insertion block without
        # requiring this isolated package to mutate it before integration.
        self.assertEqual(organization.count("zg361_team_mechanism_kpi_value"), 1)
        self.assertEqual(
            SHARED_HOOK_CONTRACT["organization_component"],
            ("common/script_values/zg361_values.txt", "zg361_kpi_organization_evidence_value"),
        )

    def test_f032_due_guard_matches_b1_precompute_and_legacy_postcompute_cycles(self) -> None:
        due_value = top_level_block(
            self.manager_values, "zg361_mg_due_organization_kpi_value"
        )
        settle = top_level_block(
            self.effects, "zg361_mg_settle_due_organization_kpi_effect"
        )
        canonical = ORGANIZATION_DUE_GUARD.strip()
        self.assertEqual(due_value.count(canonical), 1)
        self.assertEqual(settle.count(canonical), 1)
        for block in (due_value, settle):
            self.assertIn(
                "AND = { var:zg361_mg_organization_input_due_cycle >= { value = var:zg361_mg_organization_input_source_cycle add = 1 } var:zg361_mg_organization_input_due_cycle <= { value = var:zg361_mg_organization_input_source_cycle add = 1 } }",
                block,
            )
            self.assertIn(
                "var:zg361_b1_cycle_serial >= var:zg361_mg_organization_input_due_cycle",
                block,
            )
            self.assertIn(
                "var:zg361_review_serial >= var:zg361_mg_organization_input_source_cycle",
                block,
            )
            self.assertNotIn("organization_input_due_cycle <= liege.var:zg361_review_serial", block)
        self.assertIn(
            "zg361_mg_organization_settled_cycle value = var:zg361_mg_organization_input_due_cycle",
            settle,
        )
        self.assertIn(
            "zg361_mg_organization_settled_cycle value = var:zg361_b1_cycle_serial",
            settle,
        )

    def test_distribution_shared_adapter_is_exact_and_core_preserving(self) -> None:
        apply_due = top_level_block(
            self.effects, "zg361_mg_apply_due_distribution_policy_effect"
        )
        selector = top_level_block(self.effects, "zg361_mg_set_bottom_slots_effect")
        effective = top_level_block(
            self.manager_values, "zg361_mg_effective_bottom_slots_value"
        )
        self.assertIn("zg361_mg_distribution_policy_status = 1", apply_due)
        self.assertIn("zg361_mg_distribution_policy_status value = 2", apply_due)
        self.assertIn("zg361_mg_distribution_policy_settlement_receipt", apply_due)
        self.assertEqual(apply_due.count(DISTRIBUTION_DUE_GUARD.strip()), 1)
        self.assertIn("zg361_mg_distribution_policy_applied_this_rank value = 1", apply_due)
        self.assertNotIn("distribution_policy_due_cycle <= var:zg361_review_serial", apply_due)
        self.assertLess(
            selector.index("zg361_mg_distribution_policy_applied_this_rank value = 0"),
            selector.index("zg361_mg_apply_due_distribution_policy_effect = yes"),
        )
        self.assertLess(
            selector.index("zg361_mg_apply_due_distribution_policy_effect = yes"),
            selector.index("name = zg361_bottom_slots value = zg361_bottom_slots_value"),
        )
        self.assertIn("value = zg361_mg_effective_bottom_slots_value", selector)
        self.assertIn("remove_variable = zg361_mg_distribution_policy_applied_this_rank", selector)
        self.assertIn("multiply = 0.10", effective)
        self.assertIn("multiply = 0.05", effective)
        self.assertEqual(
            SHARED_HOOK_CONTRACT["distribution_settlement"][1],
            "set_variable = { name = zg361_bottom_slots value = zg361_bottom_slots_value }",
        )

    def test_shared_hooks_are_unmerged_or_atomically_match_the_contract(self) -> None:
        organization = top_level_block(
            self.values, "zg361_kpi_organization_evidence_value"
        )
        compute = top_level_block(self.core, "zg361_compute_kpi_effect")
        rank = top_level_block(self.core, "zg361_rank_cohort_effect")
        markers = (
            "add = zg361_mg_due_organization_kpi_value" in organization,
            "zg361_mg_settle_due_organization_kpi_effect = yes" in compute,
            "zg361_mg_set_bottom_slots_effect = yes" in rank,
        )
        self.assertIn(markers, ((False, False, False), (True, True, True)))
        if all(markers):
            self.assertLess(
                organization.index("add = zg361_manager_mechanism_kpi_value"),
                organization.index("add = zg361_mg_due_organization_kpi_value"),
            )
            self.assertLess(
                compute.index("zg361_b2_consume_management_debt_effect = yes"),
                compute.index("zg361_mg_settle_due_organization_kpi_effect = yes"),
            )
            self.assertNotIn(
                "set_variable = { name = zg361_bottom_slots value = zg361_bottom_slots_value }",
                rank,
            )

    def test_team_snapshot_uses_actual_receipts_and_exact_replay_wrapper(self) -> None:
        wrapper = top_level_block(self.effects, "zg361_mg_freeze_team_snapshot_effect")
        snapshot = top_level_block(self.effects, "zg361_mg_build_team_snapshot_effect")
        self.assertIn("zg361_mg_build_team_snapshot_effect = yes", wrapper)
        for identity in ("owner", "subject", "cycle", "case"):
            self.assertIn(f"zg361_mg_team_snapshot_{identity}", wrapper + snapshot)
        self.assertIn("zg361_mg_team_snapshot_revision add = 1", snapshot)
        for source in (
            "zg361_result_delivery_method",
            "zg361_result_appeal_outcome",
            "zg361_result_grade_reason",
            "zg361_b2_pip_state",
            "zg361_b2_pip_graduation_receipt",
            "zg361_b2_m075_state",
            "zg361_b2_m075_actual_exit",
            "zg361_b2_m075_neutral_record",
        ):
            self.assertIn(source, snapshot + self.effects)
        self.assertNotIn("zg361_result_regrade_delta", self.effects)
        self.assertNotIn("zg361_b2_m016_outcome", self.effects)

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

    def test_every_owned_id_freezes_owner_subject_object_and_real_c_debt(self) -> None:
        for row in BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                block = top_level_block(self.effects, row.effect)
                stem = f"zg361_mg_m{row.mechanism_id:03d}"
                domain = row.domain.lower()
                for identity_field in ("owner", "subject", "cycle", "case"):
                    self.assertIn(f"{stem}_route_{identity_field}", block)
                for object_field in ("id", "owner", "subject", "cycle", "case", "state", "revision", "route", "kind"):
                    self.assertIn(f"{stem}_object_{object_field}", block)
                self.assertIn(f"{stem}_object_input_fingerprint", block)
                self.assertIn(f"{stem}_business_object_created value = 1", block)
                self.assertIn(f"{stem}_business_object_created value = 0", block)
                self.assertIn(f"{stem}_debt_status value = 1", block)
                self.assertIn(f"{stem}_debt_owner value = var:zg361_case_{domain}_owner", block)
                self.assertIn(f"{stem}_debt_subject value = this", block)
                self.assertIn(f"{stem}_debt_state", block)
                self.assertIn(f"{stem}_debt_revision", block)
                self.assertIn(f"{stem}_debt_input_fingerprint", block)
                self.assertIn(f"{stem}_next_review_serial", block)
                self.assertIn("add = 1", block)

    def test_exact_replay_is_noop_and_route_or_input_change_is_stale_red(self) -> None:
        self.assertEqual(set(INPUT_FINGERPRINT_VARS), set(TARGET_IDS))
        self.assertEqual(set(INPUT_FINGERPRINT_OPAQUE_VARS), set(TARGET_IDS))
        self.assertEqual(set(INPUT_FINGERPRINT_RAW_VALUES), set(TARGET_IDS))
        known_fields = {
            (mechanism_id, variable)
            for mechanism_id, variables in INPUT_FINGERPRINT_VARS.items()
            for variable in variables
        }
        self.assertTrue(set(INPUT_FINGERPRINT_GUARDS) <= known_fields)
        for row in BINDINGS:
            with self.subTest(mechanism=row.mechanism_id):
                block = top_level_block(self.effects, row.effect)
                stem = f"zg361_mg_m{row.mechanism_id:03d}"
                self.assertIn(f"remove_variable = {stem}_replay_route_conflict", block)
                self.assertIn(
                    f"set_variable = {{ name = {stem}_requested_route value = 1 }}",
                    block,
                )
                self.assertIn(
                    f"name = {stem}_requested_route value = var:zg361_mechanism_{row.mechanism_id:03d}_choice",
                    block,
                )
                self.assertIn(
                    f"NOT = {{ var:{stem}_requested_route = var:{stem}_route }}",
                    block,
                )
                self.assertNotIn(
                    f"zg361_mechanism_{row.mechanism_id:03d}_input_revision",
                    block,
                )
                for variable in INPUT_FINGERPRINT_VARS[row.mechanism_id]:
                    self.assertIn(f"has_variable = {variable}", block)
                for variable in INPUT_FINGERPRINT_OPAQUE_VARS[row.mechanism_id]:
                    self.assertIn(f"has_variable = {variable}", block)
                for raw_value in INPUT_FINGERPRINT_RAW_VALUES[row.mechanism_id]:
                    self.assertIn(f"value = {raw_value}", block)
                self.assertIn(f"{stem}_requested_input_fingerprint", block)
                self.assertIn(
                    f"NOT = {{ var:{stem}_requested_input_fingerprint = var:{stem}_object_input_fingerprint }}",
                    block,
                )
                self.assertIn(
                    f"NOT = {{ var:{stem}_requested_input_fingerprint = var:{stem}_debt_input_fingerprint }}",
                    block,
                )
                self.assertIn(f"{stem}_replay_route_conflict value = 1", block)
                self.assertIn(
                    f"var:zg361_case_{row.domain.lower()}_cycle_serial < var:{stem}_route_cycle",
                    block,
                )
                self.assertIn(
                    f"NOT = {{ var:zg361_case_{row.domain.lower()}_owner = var:{stem}_route_owner }}",
                    block,
                )
                self.assertIn(
                    f"zg361_mg_set_red_effect = {{ CODE = 2 MECHANISM = {row.mechanism_id} }}",
                    block,
                )
                # The terminal failure branch is also receipt-not-current;
                # therefore an exact A/B receipt replay reaches no writer/RED.
                terminal = block[block.rfind("else_if = {") :]
                self.assertIn("zg361_case_kernel_receipt_is_current_trigger", terminal)
                self.assertIn(
                    f"NOT = {{ has_variable = {stem}_replay_route_conflict }}",
                    terminal,
                )

    def test_policy_debt_has_due_once_consumer_and_next_score_sink(self) -> None:
        consumer = top_level_block(
            self.effects, "zg361_mg_consume_due_policy_debts_effect"
        )
        opener = top_level_block(
            self.effects, "zg361_mg_open_manager_governance_cases_effect"
        )
        snapshot = top_level_block(self.effects, "zg361_mg_build_team_snapshot_effect")
        self.assertIn("zg361_mg_consume_due_policy_debts_effect = yes", opener)
        self.assertIn("liege = root", opener)
        self.assertIn(
            "root.var:zg361_review_serial >= var:zg361_mg_m032_next_review_serial",
            consumer,
        )
        self.assertNotRegex(consumer, r"(?<!root\.)var:zg361_review_serial\s*>=")
        for mechanism_id in TARGET_IDS:
            stem = f"zg361_mg_m{mechanism_id:03d}"
            with self.subTest(mechanism=mechanism_id):
                self.assertIn(f"{stem}_debt_status = 1", consumer)
                self.assertIn(f"{stem}_debt_subject = this", consumer)
                self.assertIn(f"{stem}_debt_status value = 2", consumer)
                self.assertIn(f"{stem}_debt_settled_by_owner value = root", consumer)
                self.assertIn(f"{stem}_debt_manager_score_delta value = -3", consumer)
                self.assertIn(f"{stem}_debt_remediation_code value = 1", consumer)
        self.assertEqual(consumer.count("change_variable = { name = zg361_mg_manager_score_delta add = -3 }"), len(TARGET_IDS))
        self.assertEqual(
            consumer.count("zg361_mg_manager_score_delta_due_cycle value = root.var:zg361_review_serial"),
            len(TARGET_IDS),
        )
        self.assertIn("add = var:zg361_mg_manager_score_delta", snapshot)
        self.assertIn("var:zg361_mg_manager_score_delta_due_cycle <= root.var:zg361_review_serial", snapshot)
        self.assertIn("remove_variable = zg361_mg_manager_score_delta", snapshot)
        self.assertIn("remove_variable = zg361_mg_manager_score_delta_due_cycle", snapshot)

    def test_q121_128_are_strict_read_only_career_hc_projections(self) -> None:
        adapter = top_level_block(
            self.effects, "zg361_mg_project_career_hc_q_receipts_effect"
        )
        opener = top_level_block(
            self.effects, "zg361_mg_open_manager_governance_cases_effect"
        )
        self.assertEqual(Q_PROJECTION_IDS, tuple(range(121, 129)))
        self.assertIn("zg361_mg_project_career_hc_q_receipts_effect = yes", opener)
        for mechanism_id in Q_PROJECTION_IDS:
            expected_state = 1 + (mechanism_id - 121) // 2
            stem = f"zg361_ch_m{mechanism_id:03d}"
            projection = f"zg361_mg_q{mechanism_id:03d}"
            with self.subTest(mechanism=mechanism_id):
                self.assertIn(f"{stem}_consumed = 1", adapter)
                self.assertIn(f"{stem}_business_consumed = 1", adapter)
                self.assertIn(f"{stem}_receipt_state = {expected_state}", adapter)
                self.assertIn(f"{stem}_receipt_route = 1 var:{stem}_value = 1", adapter)
                self.assertIn(f"{stem}_receipt_route = 2 var:{stem}_value = -1", adapter)
                self.assertIn(f"{stem}_receipt_route = 3 var:{stem}_value = 0", adapter)
                for field in ("id", "owner", "subject", "cycle", "case", "state", "revision"):
                    self.assertIn(f"var:{stem}_manager_object_{field}", adapter)
                    self.assertIn(f"name = {projection}_authoritative_object_{field}", adapter)
                    self.assertIn(f"name = {stem}_manager_object_{field}", self.career_hc_effects)
                for field in ("owner", "cycle", "case", "state", "route"):
                    self.assertIn(
                        f"var:{stem}_manager_object_{field} = var:{stem}_receipt_{field}",
                        adapter,
                    )
                self.assertIn(f"var:{stem}_manager_object_subject = this", adapter)
                self.assertIn(
                    f"var:{stem}_receipt_cycle < var:{projection}_cycle", adapter
                )
                self.assertIn(
                    f"var:{stem}_receipt_cycle > var:{projection}_cycle", adapter
                )

        # Career/HC owns every Q case, object and business consumer.  The
        # manager package may read zg361_ch_* but must never write or invoke it.
        forbidden_writer_patterns = (
            r"set_variable\s*=\s*\{\s*name\s*=\s*zg361_ch_",
            r"change_variable\s*=\s*\{\s*name\s*=\s*zg361_ch_",
            r"remove_variable\s*=\s*zg361_ch_",
            r"zg361_case_q_(?:open|advance|close)[A-Za-z0-9_]*\s*=",
            r"zg361_career_hc_m12[1-8]_(?:core|consume|business_consumer)_effect\s*=",
        )
        for pattern in forbidden_writer_patterns:
            self.assertNotRegex(self.effects, pattern)
        self.assertIn("Q 的对象与状态权威只属于", self.spec)
        self.assertIn("manager 自己的 `zg361_mg_qNNN_*` 只是只读缓存", self.spec)

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

    def test_route_c_receipts_advance_f_and_do_not_deadlock_ak_barriers(self) -> None:
        for mechanism_id, state, next_event in (
            (32, 1, 101),
            (33, 2, 102),
            (34, 3, 103),
            (36, 4, 120),
        ):
            row = next(row for row in BINDINGS if row.mechanism_id == mechanism_id)
            block = top_level_block(self.effects, row.effect)
            with self.subTest(mechanism=mechanism_id):
                self.assertIn(f"zg361_mg_m{mechanism_id:03d}_route = 3", block)
                self.assertGreaterEqual(
                    block.count(f"zg361_case_f_advance_{state:02d}_effect"), 2
                )
                self.assertIn(f"EVENT = zg361mg.{next_event}", block)

        stage_2 = top_level_block(self.effects, "zg361_mg_ak_stage_2_effect")
        stage_3 = top_level_block(self.effects, "zg361_mg_ak_stage_3_effect")
        self.assertIn("zg361_mg_m347_receipt_choice = 3", stage_2)
        self.assertIn("zg361_mg_override_quota_neutral = 1", stage_2)
        self.assertIn("zg361_mg_m349_receipt_choice = 3", stage_3)
        self.assertIn("zg361_mg_audit_settled = 1", stage_3)

    def test_mixed_upstream_c_downstream_ab_uses_explicit_empty_basis_not_old_values(self) -> None:
        scorer = top_level_block(self.effects, "zg361_mg_m032_score_manager_effect")
        reason = top_level_block(self.effects, "zg361_mg_m033_reason_code_effect")
        nine_box = top_level_block(self.effects, "zg361_mg_m034_freeze_nine_box_effect")
        report = top_level_block(self.effects, "zg361_mg_m036_append_decade_log_effect")
        benchmark = top_level_block(self.effects, "zg361_mg_m350_version_benchmark_effect")
        mapping = top_level_block(self.effects, "zg361_mg_m352_map_history_effect")
        admin = top_level_block(self.effects, "zg361_mg_m353_charge_admin_capacity_effect")
        fairness = top_level_block(self.effects, "zg361_mg_m354_audit_fairness_effect")

        # 035C is a valid upstream receipt for 032A/B; it never requires an
        # old distribution_conserved value to exist.
        self.assertIn("zg361_mg_m035_receipt_choice = 3", scorer)

        # 032C lets later F stages close, but the later business objects use a
        # visible unavailable/zero basis rather than a previous cycle's score.
        for block in (reason, nine_box):
            self.assertIn("zg361_mg_m032_receipt_choice = 3", block)
            self.assertIn("NOT = { var:zg361_mg_m032_receipt_choice = 3 }", block)
        self.assertIn("zg361_mg_reason_score_basis value = 0", reason)
        self.assertIn("var:zg361_mg_reason_score_basis < 40", reason)
        self.assertIn("zg361_mg_nine_box_score_basis value = 0", nine_box)
        self.assertIn("zg361_mg_nine_box_score_source_available = 1", nine_box)
        self.assertIn("zg361_mg_report_manager_score value = 0", report)
        self.assertIn("zg361_mg_report_reason_total value = 0", report)
        self.assertIn("zg361_mg_report_nine_box_code value = 0", report)
        self.assertIn(
            "add = var:zg361_mg_report_manager_score", report
        )
        self.assertIn("add = var:zg361_mg_report_reason_total", report)

        # 345C/346C produce explicit defaults for consumers; 350C creates a
        # new-series 352 object; 352C gives 354 mapping version 0.  Raw old
        # values remain archival and are never selected through these C gates.
        self.assertIn("zg361_mg_benchmark_effective_cycle_basis", benchmark)
        self.assertIn("NOT = { var:zg361_mg_m345_receipt_choice = 3 }", benchmark)
        self.assertIn(
            "zg361_mg_benchmark_effective_cycle value = var:zg361_mg_benchmark_effective_cycle_basis",
            benchmark,
        )
        self.assertIn("zg361_mg_m350_receipt_choice = 3", mapping)
        self.assertIn("zg361_mg_history_source_available value = 0", mapping)
        self.assertIn("zg361_mg_history_new_series value = 1", mapping)
        self.assertIn("zg361_mg_admin_calendar_basis value = 0", admin)
        self.assertIn("zg361_mg_admin_offcycle_basis value = 0", admin)
        self.assertIn("NOT = { var:zg361_mg_m345_receipt_choice = 3 }", admin)
        self.assertIn("NOT = { var:zg361_mg_m346_receipt_choice = 3 }", admin)
        self.assertIn(
            "zg361_mg_admin_meeting_hours value = var:zg361_mg_admin_calendar_basis",
            admin,
        )
        self.assertIn("zg361_mg_fairness_history_mapping_basis value = 0", fairness)
        self.assertIn("NOT = { var:zg361_mg_m352_receipt_choice = 3 }", fairness)
        self.assertIn(
            "zg361_mg_fairness_history_mapping_version value = var:zg361_mg_fairness_history_mapping_basis",
            fairness,
        )

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
        snapshot = top_level_block(self.effects, "zg361_mg_build_team_snapshot_effect")
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
        deadline = top_level_block(self.jingcha_events, "zg361.41")
        self.assertLess(mandate.index("name = zg361.40.a"), mandate.index("name = zg361.40.b"))
        self.assertIn("open_view_data", mandate)
        self.assertIn("zg361_mg_refuse_jingcha_exact_effect = yes", mandate)
        self.assertNotIn("zg361_refuse_jingcha_effect = yes", mandate)
        # The D+300 breach remains the pre-existing automatic failure path;
        # this test's new contract is the player's explicit option caller.
        self.assertIn("zg361_refuse_jingcha_effect = yes", deadline)
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
        for field in ("owner", "subject", "cycle", "case"):
            self.assertIn(f"zg361_mg_refusal_{field}", adapter)
        self.assertIn(
            "zg361_mg_refusal_owner value = var:zg361_jingcha_mandate_superior",
            adapter,
        )
        self.assertIn("zg361_mg_refusal_subject value = this", adapter)
        self.assertIn(
            "zg361_mg_refusal_cycle value = var:zg361_b1_cycle_serial", adapter
        )
        self.assertIn(
            "zg361_mg_refusal_case value = var:zg361_b1_case_serial", adapter
        )
        self.assertIn("zg361_mg_refusal_operation value = 32", adapter)
        self.assertIn("zg361_mg_refusal_opinion_delta value = -25", adapter)
        self.assertIn("zg361_mg_refusal_kpi_delta value = -50", adapter)
        self.assertIn("zg361_mg_refusal_reviewer_eligible value = 1", adapter)
        self.assertIn("zg361_mg_refusal_status value = 1", adapter)
        self.assertLess(
            adapter.index("zg361_mg_refusal_owner value"),
            adapter.index("zg361_clear_jingcha_mandate_effect = yes"),
        )
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
            "zg361_mg_report_manager_score",
            "zg361_mg_report_score_available",
            "zg361_mg_snapshot_source_serial",
            "zg361_case_f_cycle_serial",
            "zg361_mg_report_reason_total",
            "zg361_mg_report_reason_available",
            "zg361_mg_report_nine_box_code",
            "zg361_mg_report_nine_box_available",
        ):
            self.assertIn(f"MakeScope.Var('{variable}').GetValue", self.loc_en)
            self.assertIn(f"MakeScope.Var('{variable}').GetValue", self.loc_zh)

    def test_f032_uses_only_strictly_prior_seven_metric_aggregate(self) -> None:
        snapshot = top_level_block(self.effects, "zg361_mg_build_team_snapshot_effect")
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
            self.assertIn(f"zg361_mg_profile_weight_{reason}", block)
            self.assertIn(f"multiply = var:zg361_mg_profile_weight_{reason}", block)
        self.assertGreaterEqual(block.count("max = 25 min = -25"), 5)
        self.assertIn("zg361_mg_profile_code value = 1", block)
        for profile_code in range(2, 6):
            self.assertIn(f"zg361_mg_profile_code = {profile_code}", block)
        self.assertIn("zg361_mg_reason_relationship_once value = 5", block)
        self.assertIn("zg361_mg_reason_appeal_risk value = 10", block)
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
        self.assertLess(block.index("CODE = 6 MECHANISM = 34"), block.rindex("zg361_case_f_advance_03_effect"))
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
        self.assertIn("has_variable = zg361_ratio_override", block)
        for ratio in (10, 5, 0):
            self.assertIn(f"var:zg361_ratio_override = {ratio}", block)
        for rule in ("strict", "relaxed", "off"):
            self.assertIn(f"has_game_rule = zg361_ratio_{rule}", block)
        self.assertNotIn("has_variable = zg361_distribution_absolute_threshold", block)
        self.assertNotIn("has_variable = zg361_distribution_mode", block)
        self.assertIn("zg361_mg_distribution_rule_source", block)
        self.assertIn("zg361_mg_distribution_review_serial", block)
        self.assertIn("zg361_mg_distribution_bottom_consequence value = 0", block)
        self.assertIn("var:zg361_mg_team_n >= 5", block)
        self.assertNotIn("zg361_mg_distribution_bottom_consequence value = 2", block)
        self.assertIn(
            "add = var:zg361_mg_distribution_middle_slots add = var:zg361_mg_distribution_bottom_slots",
            block,
        )
        for field in (
            "status",
            "owner",
            "subject",
            "source_reviewer",
            "source_cycle",
            "source_case",
            "source_revision",
            "input_revision",
            "mode",
            "rule_source",
            "due_cycle",
        ):
            self.assertIn(f"zg361_mg_distribution_policy_{field}", block)
        scorer = top_level_block(self.effects, "zg361_mg_m032_score_manager_effect")
        self.assertIn("zg361_mg_m035_receipt_choice = 3", scorer)
        self.assertIn("var:zg361_mg_distribution_policy_available = 1", scorer)
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
        for final_n in (1, 4):
            self.assertIn(f"zg361_mg_calendar_final_n value = {final_n}", block)
        self.assertIn("zg361_mg_calendar_checkin_n value = 1", block)
        self.assertIn("zg361_mg_calendar_player_ai_batch value = 1", block)
        self.assertIn("zg361_mg_calendar_admin_hours value = 72", block)
        self.assertIn("zg361_mg_calendar_short_term_bias value = 25", block)
        self.assertIn("zg361_mg_calendar_fatigue value = 30", block)

    def test_ak346_material_signal_is_once_and_never_reruns_cohort(self) -> None:
        record = top_level_block(self.effects, "zg361_mg_produce_offcycle_signal_effect")
        consume = top_level_block(
            self.effects, "zg361_mg_m346_consume_offcycle_signal_effect"
        )
        for actual in ("zg361_mg_team_overturn_n", "zg361_mg_team_pip_success", "zg361_mg_team_calibration"):
            self.assertIn(actual, record)
        for identity in ("source_owner", "source_subject", "source_cycle", "source_case", "input_revision"):
            self.assertIn(f"zg361_mg_offcycle_{identity}", record + consume)
        self.assertNotIn("$MATERIALITY$", record)
        self.assertIn("zg361_mg_offcycle_input_status value = 1", record)
        self.assertIn("zg361_mg_offcycle_cohort_reruns value = 0", consume)
        self.assertIn("zg361_mg_offcycle_input_status value = 2", consume)
        self.assertIn("zg361_mg_offcycle_input_status value = 3", consume)
        self.assertIn("zg361_mg_offcycle_pending value = 0", consume)
        self.assertIn("zg361_mg_offcycle_consumed_cycle", consume)
        self.assertIn("zg361_mg_offcycle_settlement_receipt", consume)

    def test_ak347_override_has_three_part_receipt_and_quota_neutrality(self) -> None:
        producer = top_level_block(self.effects, "zg361_mg_produce_override_pair_effect")
        block = top_level_block(self.effects, "zg361_mg_m347_consume_override_effect")
        for reason in (1, 2, 3, 4):
            self.assertIn(f"var:zg361_result_grade_reason = {reason}", producer)
        self.assertEqual(producer.count("ordered_vassal = {"), 2)
        self.assertIn("zg361_mg_override_source_beneficiary_case", producer + block)
        self.assertIn("zg361_mg_override_source_bearer_case", producer + block)
        self.assertIn("zg361_mg_override_input_revision", producer + block)
        for token in ("beneficiary", "bearer", "reason"):
            self.assertIn(f"zg361_mg_override_{token}", block)
        self.assertIn("var:zg361_mg_override_used < var:zg361_mg_override_budget", block)
        self.assertIn("zg361_mg_override_quota_before", block)
        self.assertIn("zg361_mg_override_quota_after", block)
        self.assertIn("zg361_mg_override_quota_neutral value = 1", block)
        self.assertIn("zg361_mg_override_input_status value = 2", block)
        self.assertIn("zg361_mg_override_input_status value = 3", block)
        self.assertIn("zg361_mg_override_settlement_receipt", block)
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
        self.assertIn("save_scope_as = zg361_mg_pilot_manager", block)
        self.assertIn("position = 0", block)
        self.assertIn("position = 1", block)
        self.assertIn("scope:zg361_mg_pilot_manager", block)
        self.assertNotIn("root.var:zg361_mg_pilot_region_cursor", block)
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
        self.assertIn("zg361_mg_manager_score_delta_due_cycle", block)
        snapshot = top_level_block(self.effects, "zg361_mg_build_team_snapshot_effect")
        self.assertIn("add = var:zg361_mg_manager_score_delta", snapshot)
        self.assertIn("remove_variable = zg361_mg_manager_score_delta_due_cycle", snapshot)

    def test_ak354_recomputes_raw_rates_and_gates_long_term_trust(self) -> None:
        block = top_level_block(self.effects, "zg361_mg_m354_audit_fairness_effect")
        for raw in ("appeals", "overturns", "exits", "healthy_exits"):
            self.assertIn(f"zg361_mg_fairness_raw_{raw}", block)
        for gap in ("appeal", "overturn", "exit"):
            self.assertIn(f"zg361_mg_fairness_gap_{gap}", block)
        for raw in ("delivered", "appeals", "overturns", "exits", "healthy_exits"):
            self.assertIn(f"value = var:zg361_mg_fairness_input_{raw}", block)
        self.assertIn("zg361_mg_fairness_delivery_denominator", block)
        self.assertIn("zg361_mg_fairness_exit_denominator", block)
        self.assertIn("zg361_mg_fairness_gaming value = 1", block)
        trust_branch = block.split("zg361_mg_fairness_trust_delta value = 0", 1)[1]
        self.assertNotIn("zg361_mg_fairness_self_disclosed", trust_branch)
        self.assertNotIn("zg361_mg_fairness_remediation_completed = 1", trust_branch)
        self.assertIn("zg361_mg_fairness_remediation_status = 2", trust_branch)
        self.assertIn("zg361_mg_fairness_remediation_completion_receipt", trust_branch)
        self.assertIn("zg361_mg_fairness_trust_delta value = 5", trust_branch)
        self.assertIn("zg361_mg_fairness_input_status value = 2", block)
        self.assertIn("zg361_mg_fairness_input_status value = 3", block)
        self.assertIn("zg361_mg_fairness_settlement_receipt", block)
        audit = top_level_block(self.effects, "zg361_mg_m349_run_audit_effect")
        self.assertIn("zg361_mg_fairness_remediation_status value = 2", audit)

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

    def test_m360_snapshot_freezes_exact_b1_source_identity(self) -> None:
        snapshot = top_level_block(self.effects, "zg361_mg_build_team_snapshot_effect")
        self.assertIn("zg361_mg_team_snapshot_b1_available value = 0", snapshot)
        self.assertIn("var:zg361_b1_m360_source_available = 1", snapshot)
        self.assertIn("var:zg361_b1_m360_source_manager = this", snapshot)
        self.assertIn("var:zg361_b1_m360_source_state = 8", snapshot)
        for field in ("manager", "cycle", "case"):
            self.assertIn(
                f"zg361_mg_team_snapshot_b1_{field} value = var:zg361_b1_m360_source_{field}",
                snapshot,
            )
        for field in ("id", "hash"):
            self.assertIn(
                f"zg361_mg_team_snapshot_b1_{field} value = var:zg361_b1_m360_source_{field}",
                snapshot,
            )
        for token in ("status = 1", "sealed = 1", "id > 0", "hash > 0"):
            self.assertIn(f"var:zg361_b1_m360_source_{token}", snapshot)

    def test_m360_three_cohort_preflights_join_sealed_al_mg_and_b1(self) -> None:
        self.assertEqual(COLLECTIVE_COST_ORDINALS, (1, 2, 3))
        for ordinal in COLLECTIVE_COST_ORDINALS:
            with self.subTest(cohort=ordinal):
                block = top_level_block(
                    self.manager_triggers,
                    f"zg361_mg_m360_collective_cost_c{ordinal}_can_apply_trigger",
                )
                base = f"zg361_we_al_external_collective_{ordinal}"
                for token in (
                    "submission_owner",
                    "submission_subject",
                    "submission_cycle",
                    "submission_case",
                    "submission_state",
                    "submission_active",
                    "submission_sealed",
                    "submission_consumed",
                    "settlement_id",
                    "settlement_hash",
                    "route",
                ):
                    self.assertIn(f"zg361_we_al_external_collective_{token}", block)
                self.assertIn(
                    f"AND = {{ var:{base}_cohort_id >= {{ value = var:zg361_we_al_external_collective_settlement_id multiply = 10 add = {ordinal} }} var:{base}_cohort_id <= {{ value = var:zg361_we_al_external_collective_settlement_id multiply = 10 add = {ordinal} }} }}",
                    block,
                )
                for proof in (
                    "mg_cycle",
                    "mg_case",
                    "mg_snapshot_source_serial",
                    "b1_cycle",
                    "b1_case",
                ):
                    self.assertIn(f"{base}_{proof}", block)
                for source in (
                    "zg361_mg_team_snapshot_b1_available = 1",
                    "zg361_b1_m360_source_available = 1",
                    "zg361_b1_m360_source_status = 1",
                    "zg361_b1_m360_source_sealed = 1",
                    "zg361_b1_m360_source_state = 8",
                    "zg361_mg_m036_receipt_state = 4",
                    "zg361_mg_m036_object_state = 4",
                ):
                    self.assertIn(source, block)
                self.assertIn("var:zg361_mg_m036_receipt_choice = 1", block)
                self.assertIn("var:zg361_mg_m036_receipt_choice = 2", block)

    def test_m360_route_a_costs_real_score_and_route_b_needs_no_score(self) -> None:
        for ordinal in COLLECTIVE_COST_ORDINALS:
            with self.subTest(cohort=ordinal):
                base = f"zg361_we_al_external_collective_{ordinal}"
                preflight = top_level_block(
                    self.manager_triggers,
                    f"zg361_mg_m360_collective_cost_c{ordinal}_can_apply_trigger",
                )
                route_b, route_a = preflight.split("\n\t\tAND = {", 2)[1:]
                self.assertIn("zg361_we_al_external_collective_route = 2", route_b)
                self.assertIn(f"{base}_manager_cost = 0", route_b)
                self.assertNotIn("zg361_mg_manager_score", route_b)
                self.assertIn("zg361_we_al_external_collective_route = 1", route_a)
                self.assertIn("zg361_mg_report_score_available", route_a)
                self.assertIn("var:zg361_mg_manager_score = var:zg361_mg_report_manager_score", route_a)
                self.assertIn(
                    f"var:zg361_mg_manager_score >= scope:zg361_we_m360_cost_subject.var:{base}_manager_cost",
                    route_a,
                )
                effect = top_level_block(
                    self.effects,
                    f"zg361_mg_m360_apply_collective_cost_c{ordinal}_effect",
                )
                self.assertEqual(
                    effect.count("change_variable = { name = zg361_mg_manager_score add ="),
                    1,
                )
                route_b_effect = effect.split("\n\telse_if =", 1)[0]
                self.assertIn("manager cost is N/A on route B", route_b_effect)
                self.assertNotIn("zg361_mg_m360_cost_receipt_status value = 1", route_b_effect)
                self.assertNotIn("change_variable = { name = zg361_mg_manager_score", route_b_effect)
        self.assertNotIn("zg361_we_manager_score", self.effects + self.manager_triggers)

    def test_m360_receipt_is_product_minted_exact_and_idempotent(self) -> None:
        receipt_fields = {
            "status", "id", "hash", "owner", "al_subject", "al_cycle", "al_case",
            "settlement_id", "settlement_hash", "cohort_id", "ordinal", "manager",
            "mg_cycle", "mg_case", "mg_snapshot_source_serial", "mg_snapshot_revision",
            "b1_cycle", "b1_case", "b1_source_id", "b1_source_hash", "route",
            "quota", "exception_count", "cost",
            "score_before", "score_after", "score_delta",
        }
        for ordinal in COLLECTIVE_COST_ORDINALS:
            with self.subTest(cohort=ordinal):
                replay = top_level_block(
                    self.manager_triggers,
                    f"zg361_mg_m360_collective_cost_c{ordinal}_receipt_is_current_trigger",
                )
                for field in receipt_fields:
                    self.assertIn(f"zg361_mg_m360_cost_receipt_{field}", replay)
                self.assertIn("cohort_id multiply = 1000 add = 360", replay)
                self.assertIn("receipt_id multiply = 100", replay)
                self.assertIn("score_before subtract", replay)
                effect = top_level_block(
                    self.effects,
                    f"zg361_mg_m360_apply_collective_cost_c{ordinal}_effect",
                )
                replay_branch = effect.split("\n\telse_if =", 2)[1]
                self.assertIn("receipt_is_current_trigger = yes", replay_branch)
                self.assertIn("last_result value = 2", replay_branch)
                self.assertNotIn("change_variable = { name = zg361_mg_manager_score", replay_branch)
                self.assertIn("CODE = 2 MECHANISM = 360", effect)
                self.assertIn("CODE = 4 MECHANISM = 360", effect)

    def test_m360_cost_contract_is_documented_without_claiming_live(self) -> None:
        for token in (
            "zg361_mg_m360_collective_cost_c1_can_apply_trigger",
            "zg361_mg_m360_apply_collective_cost_c1_effect",
            "cost = exception_count = quota",
            "Route B",
            "N/A",
            "zg361_mg_manager_score",
            "static-ready",
        ):
            self.assertIn(token, self.spec)

    def test_no_gold_charge_in_non_gold_slice_and_capacity_refunds_exist(self) -> None:
        # Manifest/L0 contracts give these 15 IDs only capacity-hours.  The
        # user's dual-payer gold rule is therefore not spuriously applied here.
        for command in ("add_gold =", "remove_treasury =", "add_treasury =", "remove_gold ="):
            self.assertNotIn(command, self.effects)
        self.assertEqual(self.effects.count("zg361_case_kernel_reserve_transaction_effect"), 2)
        self.assertEqual(self.effects.count("zg361_case_kernel_settle_transaction_effect"), 2)
        self.assertEqual(self.effects.count("zg361_case_kernel_refund_transaction_effect"), 2)

    def test_dead_aggregate_ledgers_are_not_mutated(self) -> None:
        # Per-mechanism debt receipts, expiry years and manager-score deltas are
        # authoritative.  These three former totals had no reader and an
        # uninitialised change_variable write only.
        for dead in (
            "zg361_mg_exception_renewal_count",
            "zg361_mg_policy_debt",
            "zg361_mg_policy_debt_settled",
        ):
            self.assertNotIn(dead, self.effects + self.events)

    def test_no_new_top_level_gui_or_central_surface(self) -> None:
        rendered_paths = {path.relative_to(MOD_ROOT).as_posix() for path in outputs()}
        forbidden = {
            "common/scripted_effects/zg361_effects.txt",
            "events/zg361_events.txt",
            "common/character_interactions/zg361_interactions.txt",
            "gui/zg361_scoreboard.gui",
            "common/scripted_effects/zg361_b1_runtime_effects.txt",
            "common/scripted_effects/zg361_b1_runtime_effects_part2.txt",
            "common/scripted_effects/zg361_case_kernel_effects.txt",
        }
        self.assertFalse(rendered_paths & forbidden)
        self.assertFalse(
            any(
                path.startswith(
                    "common/scripted_effects/zg361_b2_"
                )
                and path.endswith(".txt")
                for path in rendered_paths
            )
        )
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

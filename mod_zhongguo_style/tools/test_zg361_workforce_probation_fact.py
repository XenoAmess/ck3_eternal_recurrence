#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for the isolated Workforce probation/PIP fact package.

The suite proves deterministic generation and static CK3 source contracts.  It
does not claim parser, loader, paused-snapshot or live-game evidence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock

import gen_zg361_workforce_probation_fact as generator


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECT_PATHS = tuple(
    MOD_ROOT / "common" / "scripted_effects" / group.filename
    for group in generator.EFFECT_GROUPS
)
EVENTS_PATH = MOD_ROOT / "events/zg361_workforce_probation_fact_events.txt"
SPEC_PATH = MOD_ROOT / "docs/zg361_workforce_probation_fact-ck3-runtime-spec.md"


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if match is None:
        raise AssertionError(f"missing block: {name}")
    start = match.start()
    brace = text.find("{", start)
    depth = 0
    quoted = False
    escaped = False
    for index in range(brace, len(text)):
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
                return text[start : index + 1]
    raise AssertionError(f"unclosed block: {name}")


def brace_balance(text: str) -> int:
    total = 0
    quoted = False
    escaped = False
    for line in text.splitlines():
        content = line.split("#", 1)[0]
        for char in content:
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
                total += 1
            elif char == "}":
                total -= 1
                if total < 0:
                    return total
    return total


class WorkforceProbationFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effect_parts = tuple(
            path.read_text(encoding="utf-8-sig") for path in EFFECT_PATHS
        )
        cls.effects = "\n\n".join(cls.effect_parts)
        cls.events = EVENTS_PATH.read_text(encoding="utf-8-sig")
        cls.spec = SPEC_PATH.read_text(encoding="utf-8-sig")

    def test_01_contract_owns_exactly_twelve_legacy_aliases(self) -> None:
        expected = {
            "attribution_bps_2",
            "attribution_bps_3",
            "outcome_dimension_1",
            "outcome_dimension_2",
            "outcome_dimension_3",
            "outcome_evidence_count",
            "outcome_evidence_hash",
            "outcome_evidence_id",
            "outcome_exclusion_reason",
            "outcome_id",
            "outcome_observed_cycle",
            "outcome_quality",
        }
        self.assertEqual(set(generator.LEGACY_ALIAS_TO_FACT), expected)
        self.assertEqual(len(generator.LEGACY_ALIAS_TO_FACT), 12)
        generator.validate_contract()

    def test_02_generated_outputs_are_current_bom_and_isolated(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(len(rendered), 13)
        effects_dir = MOD_ROOT / "common" / "scripted_effects"
        self.assertEqual(
            {group.filename for group in generator.EFFECT_GROUPS},
            {path.name for path in rendered if path.parent == effects_dir},
        )
        self.assertNotIn(generator.LEGACY_EFFECT_PATH, rendered)
        self.assertEqual(
            {path.parent.name for path in rendered if path.suffix == ".yml"},
            set(generator.LANGUAGES),
        )
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertTrue(path.name.startswith(generator.PREFIX))
                self.assertTrue(payload.startswith(generator.BOM))
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), payload)

    def test_02a_effect_shards_are_exact_historical_block_projection(self) -> None:
        aggregate = generator.render_effects()
        self.assertEqual(generator.HISTORICAL_EFFECT_BYTES, len(aggregate))
        self.assertEqual(
            generator.HISTORICAL_EFFECT_SHA256,
            hashlib.sha256(aggregate).hexdigest(),
        )
        source_blocks = generator.top_level_effect_blocks(aggregate)
        parts = generator.render_effect_parts()
        projected = tuple(
            row
            for group in generator.EFFECT_GROUPS
            for row in generator.top_level_effect_blocks(parts[group.filename])
        )
        self.assertEqual(generator.HISTORICAL_EFFECT_COUNT, len(source_blocks))
        self.assertEqual(source_blocks, projected)

    def test_02b_effect_shards_obey_the_preferred_boundary(self) -> None:
        self.assertEqual({}, generator.EFFECT_HARD_LIMIT_EXCEPTIONS)
        self.assertEqual((6, 5, 4), tuple(
            len(group.effect_names) for group in generator.EFFECT_GROUPS
        ))
        for group, path in zip(generator.EFFECT_GROUPS, EFFECT_PATHS, strict=True):
            with self.subTest(filename=group.filename):
                self.assertTrue(group.purpose.strip())
                self.assertLessEqual(len(group.effect_names), generator.EFFECT_TARGET_MAX)
                self.assertLessEqual(len(group.effect_names), generator.EFFECT_HARD_MAX)
                self.assertEqual(
                    len(group.effect_names),
                    len(generator.top_level_effect_blocks(path.read_bytes())),
                )

    def test_02c_legacy_effect_aggregate_is_rejected_independently_of_glob(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-probation-legacy-") as name:
            effects_dir = Path(name)
            legacy_path = effects_dir / generator.LEGACY_EFFECT_FILENAME
            legacy_path.write_bytes(b"legacy aggregate residue")
            with mock.patch.object(
                generator, "EFFECT_SHARD_GLOB", "future-narrow-shard-*.txt"
            ):
                self.assertEqual(
                    (legacy_path,),
                    generator.unexpected_effect_paths({}, effects_dir),
                )

    def test_03_generated_ck3_files_are_balanced_and_top_level_unique(self) -> None:
        self.assertEqual(brace_balance(self.effects), 0)
        self.assertEqual(brace_balance(self.events), 0)
        effects = re.findall(r"(?m)^(zg361_workforce_probation_fact_[a-z0-9_]+) = \{", self.effects)
        events = re.findall(r"(?m)^(zg361wpf\.[0-9]+) = \{", self.events)
        self.assertEqual(len(effects), len(set(effects)))
        self.assertEqual(set(events), {"zg361wpf.1", "zg361wpf.2"})
        self.assertGreaterEqual(len(effects), 8)
        illegal_arithmetic_rhs = re.compile(
            r"(?:\b(?:root\.)?var:[^\s{}=<>]+|\bscope:[^\s{}=<>]+|\$[A-Z0-9_]+\$)"
            r"\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*="
        )
        self.assertIsNone(illegal_arithmetic_rhs.search(self.effects))

    def test_04_arm_requires_the_real_hire_and_native_position_receipt(self) -> None:
        arm = block(self.effects, "zg361_workforce_probation_fact_arm_hire_effect")
        for token in (
            "$OWNER$ = { save_temporary_scope_as = zg361_workforce_probation_fact_arm_owner_scope }",
            "m274_write_owner = scope:zg361_workforce_probation_fact_arm_owner_scope",
            "m274_write_subject = this",
            "m274_write_state = 4",
            "m274_hired = 1",
            "m274_hire_case = var:zg361_we_m274_write_case",
            "m274_probation_due_cycle > var:zg361_we_m274_write_cycle",
            "m274_native_appointment_confirmed = 1",
            "m274_position_receipt_id > 0",
            "m274_position_receipt_hash > 0",
        ):
            self.assertIn(token, arm)
        self.assertIn("state value = 1", arm)
        self.assertNotIn("outcome_quality", arm)
        self.assertNotIn("ad_external_outcome", arm)

    def test_05_arm_replay_key_is_full_and_collision_is_red(self) -> None:
        arm = block(self.effects, "zg361_workforce_probation_fact_arm_hire_effect")
        for token in (
            "owner = scope:zg361_workforce_probation_fact_arm_owner_scope",
            "subject = this",
            "hire_cycle = var:zg361_we_m274_write_cycle",
            "hire_case = var:zg361_we_m274_write_case",
            "probation_due_cycle = var:zg361_we_m274_probation_due_cycle",
            "position_receipt_id = var:zg361_we_m274_position_receipt_id",
            "position_receipt_hash = var:zg361_we_m274_position_receipt_hash",
            "adapter_status value = 2",
            "red_code value = 1001",
        ):
            self.assertIn(token, arm)

    def test_06_public_hook_scope_contract_ignores_external_root(self) -> None:
        header = self.effects.split("zg361_workforce_probation_fact_arm_hire_effect", 1)[0]
        self.assertIn("current scope (this) = the real hired subject", header)
        self.assertIn("$OWNER$ = the real #274 owner", header)
        self.assertIn("ROOT is deliberately ignored", header)
        self.assertNotIn("root.", self.effects)
        for name in (
            "zg361_workforce_probation_fact_arm_hire_effect",
            "zg361_workforce_probation_fact_publish_from_result_effect",
            "zg361_workforce_probation_fact_publish_from_pip_settlement_effect",
        ):
            self.assertIn("$OWNER$ = { save_temporary_scope_as", block(self.effects, name))

    def test_07_result_hook_requires_a_real_settled_later_result(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        for token in (
            "has_variable = zg361_result_case_owner",
            "has_variable = zg361_result_cycle_serial",
            "has_variable = zg361_result_case_serial",
            "has_variable = zg361_result_case_state",
            "has_variable = zg361_result_settlement_posted_serial",
            "has_variable = zg361_result_grade",
            "has_variable = zg361_result_grade_reason",
            "has_variable = zg361_result_kpi_frozen",
            "has_variable = zg361_result_rank_frozen",
            "result_case_owner = scope:zg361_workforce_probation_fact_result_owner_scope",
            "result_cycle_serial >= var:zg361_workforce_probation_fact_probation_due_cycle",
            "result_cycle_serial > var:zg361_workforce_probation_fact_hire_cycle",
            "result_settlement_posted_serial = var:zg361_result_case_serial",
            "result_case_state = 3",
            "result_case_state = 5",
        ):
            self.assertIn(token, result)
        self.assertIn("m269_outcome_pending = 1", result)
        self.assertIn("m269_write_subject = this", result)
        self.assertIn("m269_write_case = var:zg361_workforce_probation_fact_hire_case", result)

    def test_08_result_dimensions_are_real_sealed_vote_evidence(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        for slot in (1, 2, 3):
            self.assertIn(f"has_variable = zg361_we_m267_interviewer_{slot}", result)
            self.assertIn(f"has_variable = zg361_we_m267_vote_evidence_{slot}", result)
            self.assertIn(f"m267_vote_evidence_{slot} > 0", result)
            self.assertIn(
                f"outcome_dimension_{slot} value = var:zg361_we_m267_vote_evidence_{slot}",
                result,
            )
        self.assertIn("m267_raw_votes_frozen = 1", result)
        self.assertIn("m267_candidate_frozen = this", result)
        self.assertGreaterEqual(result.count("NOT = { var:zg361_we_m267_interviewer_"), 3)
        self.assertGreaterEqual(result.count("NOT = { var:zg361_we_m267_vote_evidence_"), 3)

    def test_09_attribution_is_caller_fact_with_conservation_not_a_default(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        self.assertIn("subtract = $ATTRIBUTION_BPS_2$", result)
        self.assertIn("subtract = $ATTRIBUTION_BPS_3$", result)
        self.assertIn("$ATTRIBUTION_BPS_2$ >= 0", result)
        self.assertIn("$ATTRIBUTION_BPS_3$ >= 0", result)
        self.assertIn("expected_attribution_bps_1 >= 0", result)
        self.assertIn("attribution_bps_1 value = scope:zg361_workforce_probation_fact_expected_attribution_bps_1", result)
        self.assertNotIn("3333", result)
        self.assertNotIn("3334", result)

    def test_10_three_twenty_five_waits_without_publishing_aliases(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        low_start = result.index("limit = { var:zg361_result_grade = 1 }")
        low_end = result.index("else = {", low_start)
        low_branch = result[low_start:low_end]
        self.assertIn("awaiting_pip value = 1", low_branch)
        self.assertIn("state value = 2", low_branch)
        self.assertIn("adapter_status value = 3", low_branch)
        self.assertNotIn("publish_canonical_effect", low_branch)
        self.assertNotIn("ad_external_outcome", low_branch)
        self.assertIn("settled 3.25 frozen; real B2 PIP settlement is still required", result)

    def test_11_ordinary_pass_is_derived_only_from_grade_two_or_three(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        self.assertIn("var:zg361_result_grade = 1", result)
        self.assertIn("var:zg361_result_grade = 2", result)
        self.assertIn("var:zg361_result_grade = 3", result)
        pass_write = "outcome_quality value = 1 } # pass derived from grade 2/3"
        self.assertEqual(result.count(pass_write), 1)
        self.assertNotIn("outcome_quality value = 2", result)
        self.assertNotIn("outcome_quality value = 3", result)
        self.assertNotIn("outcome_quality value = 4", result)

    def test_12_pip_hook_requires_unique_underlying_and_workforce_receipts(self) -> None:
        pip = block(self.effects, "zg361_workforce_probation_fact_publish_from_pip_settlement_effect")
        for token in (
            "state = 2",
            "awaiting_pip = 1",
            "source_result_grade = 1",
            "b2_pip_owner = scope:zg361_workforce_probation_fact_pip_owner_scope",
            "b2_pip_subject = this",
            "b2_pip_cycle = var:zg361_workforce_probation_fact_source_result_cycle",
            "b2_pip_policy_route = 1",
            "b2_pip_policy_route = 2",
            "b2_pip_task_kind > 0",
            "b2_pip_settlement_receipt = var:zg361_b2_pip_case",
            "b2_pip_outcome_result_cycle > var:zg361_b2_pip_cycle",
            "b2_pip_outcome_result_case > 0",
            "b2_pip_outcome_result_grade >= 2",
            "b2_pip_outcome_result_grade <= 3",
            "b2_pip_outcome_result_grade = 1",
            "b2_workforce_pip_pending = 1",
            "b2_workforce_pip_consumed = 0",
            "b2_workforce_pip_owner = scope:zg361_workforce_probation_fact_pip_owner_scope",
            "b2_workforce_pip_subject = this",
            "name = zg361_workforce_probation_fact_expected_pip_case_receipt_id",
            "value = var:zg361_b2_pip_case",
            "multiply = 1000",
            "add = 15",
            "name = zg361_workforce_probation_fact_expected_pip_case_receipt_hash",
            "add = { value = var:zg361_b2_pip_policy_route multiply = 100 }",
            "add = { value = var:zg361_b2_pip_task_kind multiply = 10 }",
            "name = zg361_workforce_probation_fact_expected_pip_closure_receipt_id",
            "add = 17",
            "name = zg361_workforce_probation_fact_expected_pip_closure_receipt_hash",
            "add = { value = var:zg361_b2_pip_outcome_result_case multiply = 100000 }",
            "b2_workforce_pip_case_id = scope:zg361_workforce_probation_fact_expected_pip_case_receipt_id",
            "b2_workforce_pip_case_hash = scope:zg361_workforce_probation_fact_expected_pip_case_receipt_hash",
            "b2_workforce_pip_closure_receipt_id = scope:zg361_workforce_probation_fact_expected_pip_closure_receipt_id",
            "b2_workforce_pip_closure_receipt_hash = scope:zg361_workforce_probation_fact_expected_pip_closure_receipt_hash",
        ):
            self.assertIn(token, pip)
        for frozen in ("policy_route", "task_kind", "result_grade"):
            self.assertIn(
                f"source_pip_{frozen} = var:zg361_b2_pip_"
                + ("outcome_result_grade" if frozen == "result_grade" else frozen),
                pip,
            )

    def test_13_pip_graduation_and_failure_are_not_conflated_with_exit(self) -> None:
        pip = block(self.effects, "zg361_workforce_probation_fact_publish_from_pip_settlement_effect")
        self.assertIn("b2_pip_state = 3", pip)
        self.assertIn("b2_pip_outcome_code = 1", pip)
        self.assertIn("outcome_quality value = 1 } # graduated: pass", pip)
        self.assertIn("b2_pip_state = 4", pip)
        self.assertIn("b2_pip_outcome_code = 2", pip)
        self.assertIn("outcome_quality value = 2 } # failed: mismatch, not attrition", pip)
        self.assertNotIn("outcome_quality value = 3", pip)
        self.assertNotIn("outcome_quality value = 4", pip)
        self.assertNotIn("m277", pip)

    def test_14_normal_result_and_pip_cannot_publish_twice(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        pip = block(self.effects, "zg361_workforce_probation_fact_publish_from_pip_settlement_effect")
        publish = block(self.effects, "zg361_workforce_probation_fact_publish_canonical_effect")
        self.assertIn("var:zg361_workforce_probation_fact_state >= 2", result)
        self.assertIn("var:zg361_workforce_probation_fact_state = 1", result)
        self.assertIn("var:zg361_workforce_probation_fact_state >= 3", pip)
        self.assertIn("var:zg361_workforce_probation_fact_source_kind = 2", pip)
        self.assertIn("var:zg361_workforce_probation_fact_state = 2", pip)
        self.assertIn("NOT = { has_variable = zg361_workforce_probation_fact_outcome_id }", publish)
        self.assertIn("outcome_id = 0", publish)
        self.assertEqual(publish.count("owner_outcome_serial add = 1"), 1)

    def test_15_all_twelve_aliases_copy_only_from_canonical_fact(self) -> None:
        materialize = block(self.effects, "zg361_workforce_probation_fact_materialize_and_consume_effect")
        finalize = block(self.effects, "zg361_workforce_probation_fact_finalize_consumption_receipt_effect")
        for alias, fact in generator.LEGACY_ALIAS_TO_FACT.items():
            legacy = f"zg361_we_ad_external_{alias}"
            expected_set = (
                f"set_variable = {{ name = {legacy} "
                f"value = var:zg361_workforce_probation_fact_{fact} }}"
            )
            with self.subTest(alias=alias):
                self.assertIn(expected_set, materialize)
                self.assertEqual(self.effects.count(expected_set), 1)
                self.assertIn(f"remove_variable = {legacy}", finalize)
        self.assertIn("zg361_we_m269_future_consume_effect = yes", materialize)
        self.assertNotIn("ad_external_outcome_quality value = 1", materialize)
        self.assertNotIn("ad_external_outcome_quality value = 2", materialize)

    def test_16_partial_or_foreign_alias_envelope_is_rejected(self) -> None:
        materialize = block(self.effects, "zg361_workforce_probation_fact_materialize_and_consume_effect")
        finalize = block(self.effects, "zg361_workforce_probation_fact_finalize_consumption_receipt_effect")
        for alias, fact in generator.LEGACY_ALIAS_TO_FACT.items():
            legacy = f"zg361_we_ad_external_{alias}"
            canonical = f"zg361_workforce_probation_fact_{fact}"
            self.assertIn(f"has_variable = {legacy}", materialize)
            self.assertIn(f"var:{legacy} = var:{canonical}", materialize)
            self.assertGreaterEqual(materialize.count(f"var:{legacy} = var:{canonical}"), 2)
            self.assertIn(f"var:{legacy} = var:{canonical}", finalize)
        self.assertIn("NOT = {\n                    OR = {", materialize)
        self.assertIn("AND = {", materialize)
        self.assertIn("red_code value = 4001", materialize)

    def test_17_workforce_ack_precedes_independent_consumption_receipt(self) -> None:
        materialize = block(self.effects, "zg361_workforce_probation_fact_materialize_and_consume_effect")
        finalize = block(self.effects, "zg361_workforce_probation_fact_finalize_consumption_receipt_effect")
        ack_tokens = (
            "m269_outcome_settled = 1",
            "m269_outcome_pending = 0",
            "m269_last_outcome_id = var:zg361_workforce_probation_fact_outcome_id",
            "m269_consumed_hire_case = var:zg361_workforce_probation_fact_hire_case",
            "m269_consumed_candidate = this",
            "m269_outcome_evidence_id = var:zg361_workforce_probation_fact_outcome_evidence_id",
            "m269_outcome_evidence_hash = var:zg361_workforce_probation_fact_outcome_evidence_hash",
            "m269_final_quality = var:zg361_workforce_probation_fact_outcome_quality",
        )
        for token in ack_tokens:
            self.assertIn(token, materialize)
        self.assertLess(
            materialize.index("m269_final_quality = var:zg361_workforce_probation_fact_outcome_quality"),
            materialize.index("finalize_consumption_receipt_effect = yes"),
        )
        self.assertIn("consume_owner value = scope:zg361_workforce_probation_fact_receipt_owner_scope", finalize)
        self.assertIn("consume_subject value = this", finalize)
        self.assertIn("consume_hire_case value = var:zg361_workforce_probation_fact_hire_case", finalize)
        self.assertIn("consume_result_case value = var:zg361_workforce_probation_fact_source_result_case", finalize)
        self.assertIn("consume_outcome_id value = var:zg361_workforce_probation_fact_outcome_id", finalize)
        self.assertIn("m269_consumed_hire_case = var:zg361_workforce_probation_fact_hire_case", finalize)
        self.assertIn("m269_consumed_candidate = this", finalize)
        self.assertIn("m269_outcome_evidence_id = var:zg361_workforce_probation_fact_outcome_evidence_id", finalize)
        self.assertIn("m269_outcome_evidence_hash = var:zg361_workforce_probation_fact_outcome_evidence_hash", finalize)
        self.assertIn("m269_final_quality = var:zg361_workforce_probation_fact_outcome_quality", finalize)
        self.assertIn("has_variable = zg361_we_m269_receipt_choice", finalize)
        self.assertIn("m269_receipt_choice = 1", finalize)
        self.assertIn("m269_receipt_choice = 2", finalize)
        self.assertIn("consumed value = 1", finalize)
        self.assertIn("state value = 4", finalize)
        self.assertEqual(finalize.count("owner_consume_serial add = 1"), 1)

    def test_18_root_is_normalized_by_hidden_subject_event_before_consume(self) -> None:
        result = block(self.effects, "zg361_workforce_probation_fact_publish_from_result_effect")
        pip = block(self.effects, "zg361_workforce_probation_fact_publish_from_pip_settlement_effect")
        publish = block(self.effects, "zg361_workforce_probation_fact_publish_canonical_effect")
        schedule = block(self.effects, "zg361_workforce_probation_fact_schedule_consume_effect")
        hidden = block(self.events, "zg361wpf.1")
        for source in (result, pip, publish):
            self.assertNotIn("zg361_we_m269_future_consume_effect", source)
        self.assertIn("trigger_event = { id = zg361wpf.1 days = 1 }", schedule)
        self.assertIn("hidden = yes", hidden)
        self.assertIn("zg361_workforce_probation_fact_materialize_and_consume_effect = yes", hidden)
        self.assertNotIn("outcome_quality value", hidden)
        self.assertNotIn("ad_external_outcome", hidden)

    def test_19_retry_only_replays_consumer_and_never_publishes_truth(self) -> None:
        schedule = block(self.effects, "zg361_workforce_probation_fact_schedule_consume_retry_effect")
        hidden = block(self.events, "zg361wpf.1")
        self.assertIn("trigger_event = { id = zg361wpf.1 days = 90 }", schedule)
        self.assertIn("retry_pending value = 1", schedule)
        self.assertIn("retry_pending value = 0", hidden)
        self.assertNotIn("publish_from_result", schedule + hidden)
        self.assertNotIn("publish_from_pip", schedule + hidden)
        self.assertNotIn("set_variable = { name = zg361_workforce_probation_fact_outcome_", hidden)

    def test_20_subject_notice_is_player_only_and_grants_no_authority(self) -> None:
        notice = block(self.events, "zg361wpf.2")
        self.assertIn("type = character_event\n    theme = stewardship", notice)
        self.assertIn("is_ai = no", notice)
        self.assertIn("consume_subject = this", notice)
        self.assertIn("consumed = 1", notice)
        for forbidden in (
            "zg361_is_celestial_liege_trigger",
            "case_kernel",
            "publish_from_",
            "m269_future_consume",
            "add_gold",
        ):
            self.assertNotIn(forbidden, notice)

    def test_21_localization_has_zh_en_and_seven_structural_placeholders(self) -> None:
        english = (
            MOD_ROOT / "localization/english/zg361_workforce_probation_fact_l_english.yml"
        ).read_text(encoding="utf-8-sig")
        chinese = (
            MOD_ROOT / "localization/simp_chinese/zg361_workforce_probation_fact_l_simp_chinese.yml"
        ).read_text(encoding="utf-8-sig")
        for key in ("zg361wpf.2.t:0", "zg361wpf.2.desc:0", "zg361wpf.2.a:0"):
            self.assertIn(key, english)
            self.assertIn(key, chinese)
        self.assertIn("PIP、真实正常离职或岗位变更排除项", chinese)
        self.assertIn("consumed the same outcome once", english)
        for language in generator.LANGUAGES[2:]:
            with self.subTest(language=language):
                text = (
                    MOD_ROOT
                    / "localization"
                    / language
                    / f"zg361_workforce_probation_fact_l_{language}.yml"
                ).read_text(encoding="utf-8-sig")
                self.assertEqual(text.replace(f"l_{language}:", "l_english:", 1), english)

    def test_22_spec_freezes_scope_idempotency_and_core_wired_boundary(self) -> None:
        for token in (
            "CK3 script static-ready",
            "B2 PIP settlement、真实 #075 normal-exit attrition",
            "#274 post-consume D+1 arm",
            "ROOT=this=subject",
            "zg361_workforce_probation_fact_arm_hire_effect",
            "zg361_workforce_probation_fact_publish_from_result_effect",
            "zg361_workforce_probation_fact_publish_from_pip_settlement_effect",
            "zg361_workforce_probation_fact_publish_from_normal_exit_effect",
            "zg361_workforce_probation_fact_publish_from_role_failure_effect",
            "ATTRIBUTION_BPS_2",
            "ATTRIBUTION_BPS_3",
            "不传 3333/3333、全零、随机值或从档位反推的伪值",
            "zg361b2.101",
            "zg361b2.102",
            "zg361b2.103",
            "zg361b2.104",
            "不重新调用 B2 publisher",
            "幂等键",
            "quality 3/4 只由上述两个独立 producer 发布",
            "PIP failure 仍只能是 quality 2",
            "不再读取这 12 个名字",
            "新 loader",
            "MCP-first paused snapshot",
        ):
            self.assertIn(token, self.spec)
        self.assertIn(generator.READINESS, self.spec)
        self.assertIn("尚无变更后的 loader / paused snapshot / 实机证据", self.spec)
        self.assertIn("当前 scope (`this`) 必须是真实 hired subject", self.spec)
        self.assertIn("`OWNER` 参数必须是真实 #274 owner", self.spec)
        self.assertIn("`ROOT` 被明确\n忽略，不参与身份、权限或幂等键", self.spec)
        self.assertIn(
            "+ result cycle / case / state / settlement receipt / grade / reason / KPI / rank",
            self.spec,
        )
        self.assertIn("+ m267 vote_evidence_1..3 / attribution_bps_1..3", self.spec)
        self.assertIn(
            "+ pip owner / subject / cycle / case / state / policy route / task kind / settlement receipt / outcome code",
            self.spec,
        )
        self.assertIn("+ pip outcome result cycle / case / grade", self.spec)
        self.assertIn("部分/外来 envelope 永远不会被本包清除", self.spec)

    def test_23_no_religion_provider_runner_or_unrelated_system_is_added(self) -> None:
        lowered = (self.effects + self.events).lower()
        for forbidden in (
            "faith =",
            "religion =",
            "doctrine",
            "tenet",
            "holy_order",
            "native_bridge",
            "ocr",
            "start_process",
            "run_acceptance",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_24_three_generation_ledger_is_the_minimal_frozen_shape(self) -> None:
        self.assertEqual(generator.LEDGER_CAPACITY, 3)
        self.assertEqual(generator.LEDGER_ARCHIVE_SLOTS, (1, 2))
        self.assertEqual(len(generator.LEDGER_ENTRY_FIELDS), len(set(generator.LEDGER_ENTRY_FIELDS)))
        self.assertTrue(
            set(generator.LEDGER_TOMBSTONE_REQUIRED_FIELDS)
            <= set(generator.LEDGER_ENTRY_FIELDS)
        )
        for field in (
            "owner",
            "subject",
            "hire_cycle",
            "hire_case",
            "state",
            "arm_receipt_id",
            "arm_receipt_hash",
            "outcome_id",
            "outcome_receipt_hash",
            "consume_receipt_id",
            "consume_receipt_hash",
        ):
            self.assertIn(field, generator.LEDGER_ENTRY_FIELDS)

    def test_25_legacy_single_slot_is_adopted_without_rewriting_receipt(self) -> None:
        ensure = block(
            self.effects,
            "zg361_workforce_probation_fact_ensure_ledger_metadata_effect",
        )
        for token in (
            "ledger_version value = 1",
            "ledger_capacity value = 3",
            "ledger_generation value = 1",
            "ledger_entry_count value = 1",
            "ledger_current_generation value = 1",
            "has_variable = zg361_workforce_probation_fact_state",
            "var:zg361_workforce_probation_fact_state >= 1",
        ):
            self.assertIn(token, ensure)
        for field in generator.LEDGER_ENTRY_FIELDS:
            self.assertNotIn(
                f"remove_variable = zg361_workforce_probation_fact_{field}",
                ensure,
            )

    def test_26_each_archive_copies_full_tombstone_and_commits_active_last(self) -> None:
        for slot in generator.LEDGER_ARCHIVE_SLOTS:
            archive = block(
                self.effects,
                f"zg361_workforce_probation_fact_archive_current_to_slot_{slot}_effect",
            )
            for field in generator.LEDGER_ENTRY_FIELDS:
                with self.subTest(slot=slot, field=field):
                    self.assertIn(
                        "set_variable = { name = "
                        f"zg361_workforce_probation_fact_ledger_slot_{slot}_{field} "
                        f"value = var:zg361_workforce_probation_fact_{field} }}",
                        archive,
                    )
            active_write = (
                "set_variable = { name = "
                f"zg361_workforce_probation_fact_ledger_slot_{slot}_active value = 1 }}"
            )
            self.assertGreater(
                archive.rindex(active_write),
                archive.rindex(
                    "set_variable = { name = "
                    f"zg361_workforce_probation_fact_ledger_slot_{slot}_consume_workforce_case"
                ),
            )
            self.assertIn(
                f"ledger_slot_{slot}_archive_receipt_hash",
                archive,
            )

    def test_27_second_and_third_arm_append_but_fourth_is_capacity_red(self) -> None:
        prepare = block(
            self.effects,
            "zg361_workforce_probation_fact_prepare_ledger_arm_effect",
        )
        first_archive = prepare.index("archive_current_to_slot_1_effect = yes")
        first_retire = prepare.index("retire_current_projection_effect = yes", first_archive)
        second_archive = prepare.index("archive_current_to_slot_2_effect = yes")
        second_retire = prepare.index("retire_current_projection_effect = yes", second_archive)
        self.assertLess(first_archive, first_retire)
        self.assertLess(second_archive, second_retire)
        self.assertIn("ledger_generation = 1", prepare)
        self.assertIn("ledger_generation = 2", prepare)
        full = prepare[prepare.index("ledger_generation >= 3") :]
        self.assertIn("ledger_entry_count >= 3", full)
        self.assertIn("ledger_arm_red_code value = 1003", full)
        self.assertNotIn("retire_current_projection_effect", full.split("else =", 1)[0])

    def test_28_exact_current_and_archived_replays_use_full_arm_identity(self) -> None:
        arm = block(self.effects, "zg361_workforce_probation_fact_arm_hire_effect")
        self.assertEqual(arm.count("# exact archived arm replay"), 2)
        self.assertIn("# exact arm replay", arm)
        for slot in generator.LEDGER_ARCHIVE_SLOTS:
            for field in generator.LEDGER_ARM_IDENTITY_FIELDS:
                self.assertIn(
                    f"ledger_slot_{slot}_{field}",
                    arm,
                )
            self.assertIn(
                "ledger_replay_generation value = "
                f"var:zg361_workforce_probation_fact_ledger_slot_{slot}_generation",
                arm,
            )
        self.assertGreaterEqual(
            arm.count("NOT = { has_variable = zg361_workforce_probation_fact_ledger_arm_red_code }"),
            3,
        )

    def test_29_stale_collision_active_and_metadata_fail_closed_are_typed(self) -> None:
        prepare = block(
            self.effects,
            "zg361_workforce_probation_fact_prepare_ledger_arm_effect",
        )
        for code in (1001, 1002, 1003, 1004, 1005):
            self.assertIn(f"ledger_arm_red_code value = {code}", prepare)
        logical_start = prepare.index("ledger_arm_red_code value = 1002")
        self.assertIn("ledger_slot_1_hire_case", prepare[:logical_start])
        self.assertIn("ledger_slot_2_hire_case", prepare[:logical_start])
        self.assertIn("ledger_slot_1_arm_receipt_hash", prepare)
        self.assertIn("ledger_slot_2_arm_receipt_hash", prepare)

    def test_30_projection_retirement_never_cleans_immutable_archives(self) -> None:
        retire = block(
            self.effects,
            "zg361_workforce_probation_fact_retire_current_projection_effect",
        )
        for field in generator.LEDGER_ENTRY_FIELDS:
            self.assertIn(
                f"remove_variable = zg361_workforce_probation_fact_{field}",
                retire,
            )
        self.assertNotIn("ledger_slot_", retire)
        self.assertNotRegex(
            self.effects,
            r"remove_variable = zg361_workforce_probation_fact_ledger_slot_[12]_",
        )

    def test_31_ledger_state_is_persistent_character_data_not_temporary_truth(self) -> None:
        for name in (
            "ledger_version",
            "ledger_capacity",
            "ledger_generation",
            "ledger_entry_count",
            "ledger_current_generation",
            "ledger_slot_1_owner",
            "ledger_slot_1_arm_receipt_hash",
            "ledger_slot_1_consume_receipt_hash",
            "ledger_slot_2_owner",
            "ledger_slot_2_arm_receipt_hash",
            "ledger_slot_2_consume_receipt_hash",
        ):
            self.assertIn(f"name = zg361_workforce_probation_fact_{name}", self.effects)
            self.assertNotIn(
                "save_temporary_scope_value_as = {\n        name = "
                f"zg361_workforce_probation_fact_{name}",
                self.effects,
            )

    def test_32_spec_records_bounded_chain_and_separately_settled_hc(self) -> None:
        for token in (
            "三代有界 ledger",
            "活动投影 + 两个 append-only archive",
            "旧 owner → 不同 owner → 回旧 owner",
            "RED 1002",
            "RED 1003",
            "不删除任何 `ledger_slot_1_*` 或 `ledger_slot_2_*`",
            "HC partition",
            "occupied -> frozen",
            "hc_ledger_settled=1",
            "static-ready",
        ):
            self.assertIn(token, self.spec)

    def test_33_attrition_is_exact_normal_exit_not_failed_pip(self) -> None:
        normal = block(
            self.effects,
            "zg361_workforce_probation_fact_publish_from_normal_exit_effect",
        )
        for token in (
            "state = 2",
            "awaiting_pip = 1",
            "source_result_grade = 1",
            "normal_exit_fact_receipt_consumed_operation = 75",
            "normal_exit_fact_receipt_exit_class = 1",
            "normal_exit_fact_receipt_actual_exit = 1",
            "normal_exit_fact_receipt_hc_ledger_settled = 1",
            "normal_exit_fact_receipt_hc_conservation_verified = 1",
            "normal_exit_fact_receipt_formal_hc_active_after = 0",
            "normal_exit_fact_receipt_former_slot_hash > 0",
            "normal_exit_fact_receipt_prior_result_case = var:zg361_workforce_probation_fact_source_result_case",
            "source_kind value = 3",
            "outcome_quality value = 3",
            "outcome_exclusion_reason value = 0",
            "zg361_we_formal_hc_active = 0",
        ):
            self.assertIn(token, normal)
        self.assertNotIn("zg361_b2_workforce_pip_consumed = 1", normal)
        self.assertNotIn("m277", normal)

    def test_34_role_strategy_failure_is_native_invalidation_exclusion(self) -> None:
        role = block(
            self.effects,
            "zg361_workforce_probation_fact_publish_from_role_failure_effect",
        )
        for token in (
            "state = 2",
            "awaiting_pip = 1",
            "role_failure_receipt_active = 1",
            "role_failure_receipt_sealed = 1",
            "role_failure_receipt_consumed = 0",
            "role_failure_receipt_native_end_reason = 2",
            "role_failure_receipt_hc_conservation_verified = 1",
            "role_failure_receipt_formal_hc_active = 1",
            "source_kind value = 4",
            "outcome_quality value = 4",
            "outcome_exclusion_reason value = 1",
            "zg361_we_formal_hc_active = 1",
            "zg361_we_formal_hc_active_case = var:zg361_workforce_probation_fact_hire_case",
        ):
            self.assertIn(token, role)
        self.assertNotIn("actual_exit value = 1", role)
        self.assertNotIn("change_variable = { name = zg361_ch_hc_", role)

    def test_35_canonical_quality_domain_and_external_provenance_are_typed(self) -> None:
        publish = block(
            self.effects,
            "zg361_workforce_probation_fact_publish_canonical_effect",
        )
        materialize = block(
            self.effects,
            "zg361_workforce_probation_fact_materialize_and_consume_effect",
        )
        for quality in (1, 2, 3, 4):
            self.assertIn(f"outcome_quality = {quality}", publish)
        for source_kind in (1, 2, 3, 4):
            self.assertIn(f"source_kind = {source_kind}", publish)
        for field in (
            "source_external_owner",
            "source_external_subject",
            "source_external_cycle",
            "source_external_case",
            "source_external_receipt_id",
            "source_external_receipt_hash",
            "source_external_former_slot_id",
            "source_external_slot_hash",
            "source_external_appointment_receipt_id",
            "source_external_appointment_receipt_hash",
            "source_external_native_end_reason",
            "source_external_hc_conservation_verified",
        ):
            self.assertIn(field, generator.LEDGER_ENTRY_FIELDS)
            self.assertIn(field, publish)
        self.assertIn("outcome_quality = 3", materialize)
        self.assertIn("zg361_we_formal_hc_active = 0", materialize)
        self.assertIn("outcome_quality = 4", materialize)
        self.assertIn("zg361_we_formal_hc_active = 1", materialize)
        self.assertIn("normal_exit_fact_receipt_hc_conservation_verified = 1", materialize)
        self.assertIn("add = var:zg361_workforce_probation_fact_source_external_receipt_hash", publish)


if __name__ == "__main__":
    unittest.main()

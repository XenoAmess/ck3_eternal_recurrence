#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static L0 tests for the generated T/U/V/W CK3 runtime."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path

import gen_361_feedback_promotion_pip_runtime as gen
import zg361_b2_runtime_data as b2
import zg361_phase2_career_model as career


TOOLS = Path(__file__).resolve().parent
MOD_ROOT = TOOLS.parent
EVENTS = MOD_ROOT / "events" / "zg361_feedback_promotion_pip_runtime_events.txt"


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def effect_block(source: str, name: str) -> str:
    target = f"{name} = {{"
    depth = 0
    start = None
    offset = 0
    for line in source.splitlines(keepends=True):
        if depth == 0 and line.strip() == target:
            start = offset + line.index(name)
            break
        depth += line.count("{") - line.count("}")
        offset += len(line)
    if start is None:
        raise AssertionError(f"missing top-level block: {name}")
    depth = 0
    opened = False
    for index in range(start, len(source)):
        char = source[index]
        if char == "{":
            depth += 1
            opened = True
        elif char == "}":
            depth -= 1
            if opened and depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"unclosed block: {name}")


class FeedbackPromotionPipRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effect_parts = {
            group.filename: text(
                MOD_ROOT / "common" / "scripted_effects" / group.filename
            )
            for group in gen.EFFECT_GROUPS
        }
        cls.effects = "\n\n".join(cls.effect_parts.values())
        cls.events = text(EVENTS)

    def test_effects_are_complete_byte_identical_purpose_shards(self) -> None:
        self.assertEqual(len(gen.EFFECT_GROUPS), 39)
        self.assertEqual(gen.EFFECT_HARD_LIMIT_EXCEPTIONS, {})
        effects_dir = MOD_ROOT / "common" / "scripted_effects"
        self.assertFalse((effects_dir / gen.LEGACY_EFFECT_FILENAME).exists())

        historical = gen.render_effects()
        self.assertEqual(len(historical), 1_053_021)
        self.assertEqual(
            hashlib.sha256(historical).hexdigest(),
            "aa47969df504752690c74e31e693e2193773c6a7a458c096b17f48122ffabc44",
        )
        source_blocks = gen.top_level_effect_blocks(historical)
        source_names = tuple(name for name, _block in source_blocks)
        configured_names = tuple(
            name
            for group in gen.EFFECT_GROUPS
            for name in group.effect_names
        )
        self.assertEqual(len(source_names), 275)
        self.assertEqual(len(set(source_names)), 275)
        self.assertEqual(configured_names, source_names)
        source_by_name = dict(source_blocks)

        for group in gen.EFFECT_GROUPS:
            with self.subTest(filename=group.filename):
                count = len(group.effect_names)
                self.assertGreaterEqual(count, 1)
                self.assertLessEqual(count, gen.EFFECT_TARGET_MAX)
                self.assertLessEqual(count, gen.EFFECT_HARD_MAX)
                payload = (effects_dir / group.filename).read_bytes()
                self.assertTrue(payload.startswith(gen.BOM))
                visible_count = len(gen.flush_left_assignment_names(payload))
                self.assertGreaterEqual(visible_count, 1)
                self.assertLessEqual(visible_count, gen.EFFECT_TARGET_MAX)
                blocks = gen.top_level_effect_blocks(payload)
                self.assertEqual(
                    tuple(name for name, _block in blocks),
                    group.effect_names,
                )
                for name, block in blocks:
                    self.assertEqual(block, source_by_name[name])

        formerly_oversized_stage_counts = {
            "zg361_feedback_promotion_pip_003_t_stages_01_effects.txt": 5,
            "zg361_feedback_promotion_pip_004_t_stages_02_03_effects.txt": 8,
            "zg361_feedback_promotion_pip_005_t_stages_04_effects.txt": 5,
            "zg361_feedback_promotion_pip_006_u_stages_01_effects.txt": 5,
            "zg361_feedback_promotion_pip_007_u_stages_02_03_effects.txt": 8,
            "zg361_feedback_promotion_pip_008_u_stages_04_effects.txt": 5,
            "zg361_feedback_promotion_pip_009_v_stages_01_effects.txt": 5,
            "zg361_feedback_promotion_pip_010_v_stages_02_03_effects.txt": 8,
            "zg361_feedback_promotion_pip_011_v_stages_04_05_effects.txt": 9,
            "zg361_feedback_promotion_pip_012_w_stages_01_effects.txt": 5,
            "zg361_feedback_promotion_pip_013_w_stages_02_03_effects.txt": 8,
            "zg361_feedback_promotion_pip_014_w_stages_04_05_effects.txt": 9,
        }
        self.assertEqual(
            {
                filename: len(gen.flush_left_assignment_names(self.effect_parts[filename]))
                for filename in formerly_oversized_stage_counts
            },
            formerly_oversized_stage_counts,
        )

    def test_exact_146_191_coverage_and_domain_partition(self) -> None:
        self.assertEqual(tuple(row.mechanism_id for row in gen.MECHANISMS), tuple(range(146, 192)))
        self.assertEqual(len(gen.MECHANISMS), 46)
        self.assertEqual(
            {key: tuple(sorted(mid for mid, domain in gen.DOMAIN_BY_ID.items() if domain.key == key)) for key in "tuvw"},
            {
                "t": tuple(range(146, 157)),
                "u": tuple(range(157, 169)),
                "v": tuple(range(169, 181)),
                "w": tuple(range(181, 192)),
            },
        )

    def test_authoritative_reference_models_match_owned_ranges(self) -> None:
        b2_ids = {
            row.mechanism_id
            for row in b2.B2_BINDINGS
            if row.domain in {"T", "W"}
        }
        self.assertEqual(b2_ids, set(range(146, 157)) | set(range(181, 192)))
        self.assertTrue(set(range(157, 181)) <= set(career.MECHANISM_BEHAVIORS))
        self.assertEqual(
            {career.MECHANISM_BEHAVIORS[mid].domain for mid in range(157, 181)},
            {"U", "V"},
        )

    def test_every_mechanism_has_manager_core_consumer_and_unique_field(self) -> None:
        self.assertEqual(len({row.field for row in gen.MECHANISMS}), 46)
        for row in gen.MECHANISMS:
            mid = row.mechanism_id
            self.assertIn(f"zg361_pp_m{mid:03d}_manager_apply_effect = {{", self.effects)
            self.assertIn(f"zg361_pp_m{mid:03d}_core_effect = {{", self.effects)
            self.assertIn(f"zg361_pp_m{mid:03d}_consume_effect = {{", self.effects)
            self.assertIn(f"name = zg361_pp_m{mid:03d}_consumer_value", self.effects)
            self.assertIn(f"name = zg361_pp_m{mid:03d}_audit_1_consumer_value", self.events)

    def test_five_tuple_guard_and_idempotent_receipt_exist_per_mechanism(self) -> None:
        for row in gen.MECHANISMS:
            mid = row.mechanism_id
            block = effect_block(self.effects, f"zg361_pp_m{mid:03d}_core_effect")
            for token in (
                "zg361_case_kernel_full_guard_trigger",
                f"zg361_pp_m{mid:03d}_receipt_owner",
                f"zg361_pp_m{mid:03d}_receipt_subject",
                f"zg361_pp_m{mid:03d}_receipt_cycle",
                f"zg361_pp_m{mid:03d}_receipt_case",
                f"zg361_pp_m{mid:03d}_receipt_state",
                f"var:zg361_pp_m{mid:03d}_receipt_active = 0",
            ):
                self.assertIn(token, block, f"{mid}: missing {token}")
            for suffix in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"zg361_pp_m{mid:03d}_object_{suffix}", block)

    def test_m147_publishes_result_case_serial_and_post_record_revision(self) -> None:
        core = effect_block(self.effects, "zg361_pp_m147_core_effect")
        consumer = effect_block(self.effects, "zg361_pp_m147_consume_effect")
        opener = effect_block(self.effects, "zg361_pp_open_t_case_effect")
        self.assertIn(
            "name = zg361_pp_m147_receipt_serial value = var:zg361_pp_t_result_case",
            core,
        )
        self.assertIn(
            "name = zg361_pp_m147_receipt_revision value = var:zg361_case_t_revision",
            core,
        )
        self.assertIn(
            "name = zg361_pp_m147_receipt_revision value = var:zg361_case_t_revision",
            consumer,
        )
        self.assertLess(
            core.index("zg361_case_kernel_record_operation_effect"),
            core.index("name = zg361_pp_m147_receipt_serial"),
        )
        self.assertIn("remove_variable = zg361_pp_m147_receipt_serial", opener)
        self.assertIn("remove_variable = zg361_pp_m147_receipt_revision", opener)

    def test_c_route_is_policy_debt_only_not_business_operation(self) -> None:
        # The shared operation call is inside an explicit route != 3 branch;
        # the else branch writes only identity receipt fields and policy debt.
        for row in gen.MECHANISMS:
            mid = row.mechanism_id
            block = effect_block(self.effects, f"zg361_pp_m{mid:03d}_core_effect")
            call_at = block.index("zg361_case_kernel_record_operation_effect")
            route_guard_at = block.rfind("NOT = { scope:zg361_pp_route = 3 }", 0, call_at)
            self.assertGreaterEqual(route_guard_at, 0, f"{mid}: C can reach business operation")
            self.assertIn("Route C is a policy-debt receipt", block)
            self.assertIn(f"name = zg361_pp_m{mid:03d}_policy_debt_due_days", block)
            # Typed payload is assigned only inside A/B branches.
            payload = f"zg361_pp_m{mid:03d}_{row.field}"
            writes = re.findall(rf"name = {re.escape(payload)}(?=\s)", block)
            self.assertEqual(len(writes), 2, f"{mid}: C/default payload write leaked")

    def test_p1_p2_defer_deadlines_are_exact(self) -> None:
        for row in gen.MECHANISMS:
            block = effect_block(self.effects, f"zg361_pp_m{row.mechanism_id:03d}_schedule_audit_1_effect")
            expected = 180 if row.mechanism_id in gen.P2_DEFER_IDS else 90
            self.assertIn(f"var:zg361_pp_m{row.mechanism_id:03d}_route = 3", block)
            self.assertIn(f"days = {expected}", block)
        self.assertEqual(gen.P2_DEFER_IDS, {147, 149, 154, 155, 161, 162, 166, 170, 172, 173})

    def test_all_delayed_audits_have_five_tuple_stale_guards(self) -> None:
        expected_audits = sum(len(row.deadlines) for row in gen.MECHANISMS)
        self.assertEqual(expected_audits, 48)
        self.assertEqual(len(re.findall(r"^zg361pp\.(?:2|3)\d{3} = \{$", self.events, re.MULTILINE)), 48)
        for row in gen.MECHANISMS:
            for index, _ in enumerate(row.deadlines, start=1):
                event_id = 2000 + row.mechanism_id + (1000 if index > 1 else 0)
                block = effect_block(self.events, f"zg361pp.{event_id}")
                for suffix in ("owner", "subject", "cycle", "case", "expected_state"):
                    self.assertIn(f"zg361_pp_m{row.mechanism_id:03d}_audit_{index}_{suffix}", block)
                self.assertIn(
                    f"audit_{index}_expected_state = var:zg361_pp_m{row.mechanism_id:03d}_receipt_state",
                    block,
                )
                self.assertIn("stale", block)
                self.assertIn(f"audit_{index}_consumed = 0", block)
                revision = f"zg361_pp_{row.domain}_visible_receipt_revision"
                self.assertIn(f"NOT = {{ has_variable = {revision} }}", block)
                self.assertIn(f"name = {revision} value = 0", block)
                self.assertLess(
                    block.index(f"name = {revision} value = 0"),
                    block.index(f"change_variable = {{ name = {revision} add = 1 }}"),
                )

    def test_case_kernel_stage_deadlines_are_target_bound(self) -> None:
        stage_count = sum(len(domain.stages) for domain in gen.DOMAINS)
        self.assertEqual(stage_count, 18)
        for domain in gen.DOMAINS:
            for state in range(1, len(domain.stages) + 1):
                block = effect_block(self.effects, f"zg361_pp_schedule_{domain.key}_stage_{state:02d}_effect")
                self.assertIn("zg361_case_kernel_schedule_deadline_effect", block)
                for suffix in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE"):
                    self.assertIn(f"TICKET_{suffix}", block)
                event_id = 4000 + (ord(domain.key) - ord("t")) * 10 + state
                event = effect_block(self.events, f"zg361pp.{event_id}")
                self.assertIn("zg361_case_kernel_expire_deadline_effect", event)
                self.assertIn("has_variable = zg361_case_kernel_applied", event)
                self.assertIn("var:zg361_case_kernel_applied = 1", event)

        appeal_audit = effect_block(self.events, "zg361pp.3151")
        self.assertIn(
            "has_variable = zg361_pp_m151_appeal_filed "
            "var:zg361_pp_m151_appeal_filed = 1",
            appeal_audit,
        )

    def test_named_resources_are_atomic_and_not_generic_slot_spam(self) -> None:
        # The per-operation journal is deliberately separate from scarce
        # nomination/promotion/panel/PIP ledgers.
        self.assertEqual({domain.resource for domain in gen.DOMAINS}, {"operation_capacity"})
        self.assertEqual(gen.EXTRA_RESOURCES_BY_ID[157], ("nomination_slot",))
        self.assertEqual(gen.EXTRA_RESOURCES_BY_ID[162], ("tenure_exception_slot",))
        self.assertNotIn(160, gen.EXTRA_RESOURCES_BY_ID)
        self.assertNotIn(184, gen.EXTRA_RESOURCES_BY_ID)
        self.assertEqual(
            gen.ROUTE_A_EXTRA_RESOURCES_BY_ID,
            {160: ("promotion_slot",)},
        )
        self.assertNotIn("zg361_pp_w_pip_capacity", self.effects)
        self.assertNotIn("zg361_pp_m184_pip_capacity", self.effects)
        self.assertEqual(
            [mid for mid, resources in gen.EXTRA_RESOURCES_BY_ID.items() if "nomination_slot" in resources],
            [157],
        )
        self.assertEqual(
            gen.ROUTE_B_EXTRA_RESOURCES_BY_ID,
            {161: ("nomination_slot", "capacity_hours"), 189: ("exit_cost",)},
        )
        self.assertEqual(
            [mid for mid, resources in gen.ROUTE_A_EXTRA_RESOURCES_BY_ID.items() if "promotion_slot" in resources],
            [160],
        )
        for mid, resources in gen.EXTRA_RESOURCES_BY_ID.items():
            block = effect_block(self.effects, f"zg361_pp_m{mid:03d}_core_effect")
            for resource in resources:
                self.assertIn(f"zg361_pp_{gen.DOMAIN_BY_ID[mid].key}_{resource}_available >= 1", block)
                self.assertIn(f"zg361_pp_m{mid:03d}_{resource}_status = 1", block)
                self.assertIn(f"zg361_pp_m{mid:03d}_{resource}_status = 2", block)
        for route_map, route in (
            (gen.ROUTE_A_EXTRA_RESOURCES_BY_ID, 1),
            (gen.ROUTE_B_EXTRA_RESOURCES_BY_ID, 2),
        ):
            for mid, resources in route_map.items():
                block = effect_block(self.effects, f"zg361_pp_m{mid:03d}_core_effect")
                for resource in resources:
                    self.assertIn(f"limit = {{ scope:zg361_pp_route = {route} }}", block)
                    self.assertIn(f"zg361_pp_{gen.DOMAIN_BY_ID[mid].key}_{resource}_available >= 1", block)
                    self.assertIn(f"zg361_pp_m{mid:03d}_{resource}_status = {route}", block)

    def test_authoritative_u_v_stage_partition_and_resource_bindings(self) -> None:
        self.assertEqual(
            gen.DOMAIN_BY_KEY["u"].stages,
            ((157, 158, 159), (163, 164, 165), (161, 162, 166), (160, 167, 168)),
        )
        self.assertEqual(
            gen.DOMAIN_BY_KEY["v"].stages,
            ((169, 170, 171), (172, 173), (174, 175, 176), (177, 178), (179, 180)),
        )
        self.assertEqual(gen.mechanism_stage(166), 3)
        self.assertEqual(gen.mechanism_stage(160), 4)
        self.assertEqual(gen.mechanism_stage(176), 3)
        self.assertIn("capacity_hours", gen.EXTRA_RESOURCES_BY_ID[172])
        self.assertNotIn("panel_vote", gen.EXTRA_RESOURCES_BY_ID[172])
        self.assertIn("panel_vote", gen.EXTRA_RESOURCES_BY_ID[174])
        self.assertNotIn("capacity_hours", gen.EXTRA_RESOURCES_BY_ID[174])
        self.assertNotIn("nomination_slot", gen.EXTRA_RESOURCES_BY_ID[180])

    def test_frozen_prompt_ticket_reaches_wrapper_core_and_guard(self) -> None:
        required_event_args = (
            "TICKET_OWNER = scope:zg361_pp_prompt_owner",
            "TICKET_SUBJECT = scope:zg361_pp_prompt_subject",
            "TICKET_CYCLE = scope:zg361_pp_prompt_cycle",
            "TICKET_CASE = scope:zg361_pp_prompt_case",
            "TICKET_STATE = scope:zg361_pp_prompt_state",
        )
        for row in gen.MECHANISMS:
            event = effect_block(self.events, f"zg361pp.{row.mechanism_id}")
            for token in required_event_args:
                self.assertIn(token, event, f"{row.mechanism_id}: prompt ticket not forwarded")
            core = effect_block(self.effects, f"zg361_pp_m{row.mechanism_id:03d}_core_effect")
            for suffix in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE"):
                self.assertIn(f"EXPECTED_{suffix} = $TICKET_{suffix}$", core)
            self.assertNotIn("EXPECTED_SUBJECT = this", core)

    def test_cross_cycle_reset_covers_every_receipt_and_pending_audits_block_reopen(self) -> None:
        adapter = effect_block(self.effects, "zg361_pp_manager_portfolio_adapter_effect")
        for row in gen.MECHANISMS:
            domain = gen.DOMAIN_BY_ID[row.mechanism_id]
            opened = effect_block(self.effects, f"zg361_pp_open_{domain.key}_case_effect")
            resources = dict.fromkeys(
                (
                    domain.resource,
                    *gen.EXTRA_RESOURCES_BY_ID.get(row.mechanism_id, ()),
                    *gen.ROUTE_A_EXTRA_RESOURCES_BY_ID.get(row.mechanism_id, ()),
                    *gen.ROUTE_B_EXTRA_RESOURCES_BY_ID.get(row.mechanism_id, ()),
                )
            )
            for resource in resources:
                receipt = f"zg361_pp_m{row.mechanism_id:03d}_{resource}"
                self.assertIn(f"name = {receipt}_amount value = 0", opened)
                self.assertIn(f"name = {receipt}_status value = 0", opened)
                for suffix in ("owner", "cycle", "case"):
                    self.assertIn(f"remove_variable = {receipt}_{suffix}", opened)
            for index, _ in enumerate(row.deadlines, start=1):
                state = (
                    f"zg361_pp_m{row.mechanism_id:03d}_audit_{index}_state"
                )
                for target in (adapter, opened):
                    self.assertIn(f"has_variable = {state}", target)
                    self.assertIn(f"var:{state} = 1", target)
                self.assertIn(
                    f"name = zg361_pp_m{row.mechanism_id:03d}_audit_{index}_business_settled value = 0",
                    opened,
                )
                self.assertIn(
                    f"name = zg361_pp_m{row.mechanism_id:03d}_audit_{index}_policy_debt_settled value = 0",
                    opened,
                )
                self.assertIn(
                    f"remove_variable = zg361_pp_m{row.mechanism_id:03d}_audit_{index}_business_input",
                    opened,
                )
            for suffix in gen.AUDIT_ONLY_FIELDS_BY_ID.get(row.mechanism_id, ()):
                self.assertIn(f"remove_variable = zg361_pp_m{row.mechanism_id:03d}_{suffix}", opened)
            for suffix in gen.RESPONSE_ONLY_FIELDS_BY_ID.get(row.mechanism_id, ()):
                self.assertIn(f"remove_variable = zg361_pp_m{row.mechanism_id:03d}_{suffix}", opened)
        self.assertNotRegex(
            adapter,
            r"NOT = \{ var:zg361_pp_m\d{3}_audit_\d+_state = 1 \}",
        )

    def test_reset_does_not_read_nonexistent_subject_or_withdraw_fields(self) -> None:
        # CK3 reports remove_variable as a read.  Resetting a field with no real
        # producer therefore creates a loader RED rather than harmless cleanup.
        for row in gen.MECHANISMS:
            opened = effect_block(
                self.effects, f"zg361_pp_open_{row.domain}_case_effect"
            )
            response = f"zg361_pp_m{row.mechanism_id:03d}_subject_response"
            withdrawal = f"zg361_pp_m{row.mechanism_id:03d}_withdraw_intent"
            if row.mechanism_id in gen.SUBJECT_RESPONSE_IDS:
                self.assertIn(f"remove_variable = {response}", opened)
            else:
                self.assertNotIn(f"remove_variable = {response}\n", opened)
            if row.mechanism_id == 166:
                self.assertIn(f"remove_variable = {withdrawal}", opened)
            else:
                self.assertNotIn(f"remove_variable = {withdrawal}\n", opened)

    def test_every_case_local_write_is_cleared_before_cross_cycle_reuse(self) -> None:
        for row in gen.MECHANISMS:
            mid = row.mechanism_id
            prefix = f"zg361_pp_m{mid:03d}_"
            domain = gen.DOMAIN_BY_ID[mid]
            opened = effect_block(self.effects, f"zg361_pp_open_{domain.key}_case_effect")
            sources = [effect_block(self.effects, f"zg361_pp_m{mid:03d}_core_effect")]
            if mid in gen.SUBJECT_RESPONSE_IDS:
                sources.append(effect_block(self.effects, f"zg361_pp_m{mid:03d}_subject_response_effect"))
            for index, _ in enumerate(row.deadlines, start=1):
                sources.append(effect_block(self.events, f"zg361pp.{2000 + mid + (1000 if index > 1 else 0)}"))
            assigned = {
                name
                for source in sources
                for name in re.findall(rf"name = ({prefix}[A-Za-z0-9_]+)", source)
            }
            for name in assigned:
                self.assertTrue(
                    f"remove_variable = {name}" in opened
                    or re.search(rf"name = {re.escape(name)} value = (?:0|1)", opened),
                    f"{mid}: cross-cycle reset misses {name}",
                )

    def test_route_a_reserves_route_b_settles_and_c_spends_nothing(self) -> None:
        for row in gen.MECHANISMS:
            core = effect_block(self.effects, f"zg361_pp_m{row.mechanism_id:03d}_core_effect")
            self.assertIn("route A remains an exact reservation (status 1)", core)
            self.assertIn("route B settles at operation time (status 2)", core)
            self.assertIn("limit = { NOT = { scope:zg361_pp_route = 3 } }", core)
            self.assertIn("limit = { var:zg361_case_kernel_applied = 1 scope:zg361_pp_route = 2 }", core)

    def test_trigger_context_route_chains_use_trigger_branch_keywords(self) -> None:
        # A CK3 `limit` block is trigger context.  Its conditional chain must
        # use trigger_if/trigger_else_if/trigger_else; effect else_if/else are
        # rejected by the loader as Unknown trigger.  There is one dependency
        # chain per mechanism and one receipt-status chain per shared resource.
        expected_chains = len(gen.MECHANISMS) + sum(
            1 + len(gen.EXTRA_RESOURCES_BY_ID.get(row.mechanism_id, ()))
            for row in gen.MECHANISMS
        )
        self.assertEqual(expected_chains, 120)
        self.assertEqual(self.effects.count("trigger_else_if = {"), expected_chains)
        for row in gen.MECHANISMS:
            core = effect_block(self.effects, f"zg361_pp_m{row.mechanism_id:03d}_core_effect")
            dependency_guard = gen.routed_dependency_guard(row.mechanism_id)
            self.assertIn("trigger_else_if = {", dependency_guard)
            self.assertIn("trigger_else = { always = yes }", dependency_guard)
            self.assertNotIn("\nelse_if = {", dependency_guard)
            self.assertNotIn("\nelse = {", dependency_guard)
            expected_core_chains = 2 + len(gen.EXTRA_RESOURCES_BY_ID.get(row.mechanism_id, ()))
            self.assertEqual(
                core.count("trigger_else_if = {"),
                expected_core_chains,
                f"{row.mechanism_id}: trigger-context route chain count drifted",
            )
            resources = (
                gen.DOMAIN_BY_ID[row.mechanism_id].resource,
                *gen.EXTRA_RESOURCES_BY_ID.get(row.mechanism_id, ()),
            )
            for resource in resources:
                self.assertIn(
                    f"var:zg361_pp_m{row.mechanism_id:03d}_{resource}_status = 1\n"
                    "\t\t\t\t\t}\n"
                    "\t\t\t\t\ttrigger_else_if = {",
                    core,
                    f"{row.mechanism_id}/{resource}: status chain is not trigger grammar",
                )

    def test_u_packet_quota_withdrawal_and_matured_observation_chain(self) -> None:
        open_u = effect_block(self.effects, "zg361_pp_open_u_case_effect")
        for token in (
            "Persistent shelving obligations are consumed once per later review cycle",
            "zg361_pp_u_shelving_last_penalty_cycle",
            "zg361_pp_u_next_quota_pending",
            "zg361_pp_u_next_quota_consumed_cycle",
            "zg361_pp_m161_filler_candidate",
        ):
            self.assertIn(token, open_u)

        m157 = effect_block(self.effects, "zg361_pp_m157_core_effect")
        for token in (
            "zg361_pp_m157_packet_candidate",
            "zg361_pp_m157_packet_active",
            "zg361_pp_m157_nomination_slot_status",
        ):
            self.assertIn(token, m157)

        m159 = effect_block(self.effects, "zg361_pp_m159_core_effect")
        self.assertIn("#157 already nominated this subject", m159)
        self.assertIn("Political shelving persists on the manager", m159)

        m160 = effect_block(self.effects, "zg361_pp_m160_core_effect")
        for token in (
            "zg361_pp_m157_packet_active = 1",
            "zg361_pp_m158_quota_conserved = 1",
            "zg361_pp_m161_filler",
            "zg361_pp_m162_exception_admitted = 1",
            "zg361_pp_m163_window_cycles",
            "zg361_pp_m164_candidate_share",
            "zg361_pp_m165_authority_bound",
            "zg361_pp_m166_packet_active_after = 1",
        ):
            self.assertIn(token, m160)

        m161 = effect_block(self.effects, "zg361_pp_m161_core_effect")
        self.assertIn("NOT = { var:zg361_pp_m161_filler_candidate = this }", m161)
        self.assertIn("zg361_pp_m161_nomination_slot_status", m161)
        self.assertIn("zg361_pp_m161_capacity_hours_status", m161)
        self.assertIn("zg361_pp_m161_fairness_debt value = 1", m161)
        self.assertIn("zg361_pp_m161_filler_disclosed value = 1", m161)

        m166 = effect_block(self.effects, "zg361_pp_m166_core_effect")
        for token in (
            "zg361_pp_m166_withdraw_intent = 1",
            "NOT = { has_variable = zg361_pp_m160_prescreen_pass }",
            "zg361_pp_m157_nomination_slot_owner = var:zg361_case_u_owner",
            "zg361_pp_m166_nomination_slot_refunded",
            "zg361_pp_m157_packet_status value = 5",
        ):
            self.assertIn(token, m166)

        audit_167 = effect_block(self.events, "zg361pp.2167")
        audit_168 = effect_block(self.events, "zg361pp.2168")
        self.assertIn("has_variable = zg361_pp_m167_observation_settled", audit_167)
        self.assertIn("zg361_pp_m167_observation_settled = 0", audit_167)
        self.assertLess(
            audit_167.index("has_variable = zg361_pp_m167_observation_settled"),
            audit_167.index("var:zg361_pp_m167_observation_settled = 0"),
        )
        self.assertIn("zg361_pp_m167_sponsor_credit_delta", audit_167)
        self.assertIn("has_variable = zg361_pp_m168_sample_pending", audit_168)
        self.assertIn("has_variable = zg361_pp_m168_sample_settled", audit_168)
        self.assertIn("zg361_pp_m168_sample_pending = 1", audit_168)
        self.assertLess(
            audit_168.index("has_variable = zg361_pp_m168_sample_pending"),
            audit_168.index("var:zg361_pp_m168_sample_pending = 1"),
        )
        self.assertLess(
            audit_168.index("has_variable = zg361_pp_m168_sample_settled"),
            audit_168.index("var:zg361_pp_m168_sample_settled = 0"),
        )
        self.assertIn("zg361_pp_u_next_quota_pending value = 1", audit_168)

        dead_aggregate_ledgers = (
            "zg361_pp_fairness_credit",
            "zg361_pp_management_debt",
            "zg361_pp_management_talent_score",
            "zg361_pp_primary_packet_legitimacy",
            "zg361_pp_sponsor_credit",
            "zg361_pp_u_hit_denominator",
            "zg361_pp_u_hit_numerator",
        )
        for dead in dead_aggregate_ledgers:
            self.assertNotIn(dead, self.effects + self.events)

    def test_v_panel_blind_vote_feedback_and_retry_are_real_consumers(self) -> None:
        open_v = effect_block(self.effects, "zg361_pp_open_v_case_effect")
        for index in range(1, 4):
            self.assertIn(f"zg361_pp_v_panel_pool_{index}", open_v)
            self.assertIn(f"position = {index - 1}", open_v)

        m170 = effect_block(self.effects, "zg361_pp_m170_core_effect")
        for token in (
            "zg361_pp_m170_panelist_1",
            "zg361_pp_m170_panelist_2",
            "zg361_pp_m170_panelist_3",
            "zg361_pp_m170_panel_unique",
            "zg361_pp_m170_familiar_minority_ok",
            "zg361_pp_m170_selection_replay_ok",
        ):
            self.assertIn(token, m170)

        m178 = effect_block(self.effects, "zg361_pp_m178_core_effect")
        for token in (
            "zg361_pp_m173_blind_score",
            "zg361_pp_m172_expert_weight_consumed",
            "zg361_pp_m172_external_weight_consumed",
            "zg361_pp_m178_weighted_score",
            "zg361_pp_m178_dual_gate_pass",
            "zg361_pp_m178_vote_eligible",
            "zg361_pp_m178_votes_cast",
            "zg361_pp_m178_final_decision",
            "zg361_pp_m178_material_deferral",
        ):
            self.assertIn(token, m178)

        m179 = effect_block(self.effects, "zg361_pp_m179_core_effect")
        self.assertIn("zg361_pp_m179_feedback_owner value = var:zg361_pp_m171_active_panel_1", m179)
        self.assertIn("zg361_pp_m178_final_decision = 0", m179)

        m180 = effect_block(self.effects, "zg361_pp_m180_core_effect")
        self.assertIn("zg361_pp_m180_prior_gap_id value = var:zg361_pp_m179_gap_id", m180)
        self.assertIn("zg361_pp_m180_nomination_slot_consumed value = 0", m180)
        early = effect_block(self.events, "zg361pp.2180")
        normal = effect_block(self.events, "zg361pp.3180")
        self.assertIn("zg361_pp_m180_gap_completion = 1", early)
        self.assertIn("zg361_pp_m180_retry_unlock_reason value = 1", early)
        self.assertIn("zg361_pp_m180_retry_unlock_reason value = 2", normal)

    def test_withdrawal_refunds_exact_nomination_receipt_once(self) -> None:
        block = effect_block(self.effects, "zg361_pp_m166_core_effect")
        self.assertIn("zg361_case_kernel_refund_transaction_effect", block)
        self.assertIn("RECEIPT_AMOUNT_VAR = zg361_pp_m157_nomination_slot_amount", block)
        self.assertIn("RECEIPT_STATUS_VAR = zg361_pp_m157_nomination_slot_status", block)
        self.assertIn("name = zg361_pp_m166_nomination_slot_refunded", block)

    def test_dual_payer_money_moves_are_prechecked_and_conserved(self) -> None:
        self.assertEqual(gen.DUAL_COST_IDS, {149, 150, 165, 189, 191})
        for mid in gen.DUAL_COST_IDS:
            block = effect_block(self.effects, f"zg361_pp_m{mid:03d}_core_effect")
            for token in (
                "government_has_flag = government_has_treasury",
                "treasury >= 5",
                "gold >= 5",
                "remove_treasury = 5",
                "remove_short_term_gold = 5",
                "add_gold = 10",
                f"name = zg361_pp_m{mid:03d}_dual_payment_conserved value = 1",
            ):
                self.assertIn(token, block)
        self.assertEqual(self.effects.count("remove_short_term_gold = 5"), 5)
        self.assertIsNone(
            re.search(r"(?<!short_term_)\bremove_gold\s*=", self.effects),
            "CK3 1.19.0.6 does not register the bare remove_gold effect",
        )

    def test_only_manager_scope_portfolio_adapter_is_integration_seam(self) -> None:
        adapter = effect_block(self.effects, "zg361_pp_manager_portfolio_adapter_effect")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", adapter)
        self.assertIn("any_vassal = { zg361_is_reviewable_vassal_trigger = yes }", adapter)
        for token in (
            "has_variable = zg361_p2c_active",
            "var:zg361_p2c_active = 1",
            "has_variable = zg361_p2c_cycle",
            "var:zg361_p2c_cycle = var:zg361_review_serial",
            "has_variable = zg361_p2c_subject",
            "var:zg361_p2c_subject = { save_temporary_scope_as = zg361_pp_portfolio_subject }",
            "ZG361PP: central frozen portfolio subject selected",
        ):
            self.assertIn(token, adapter)
        self.assertIn("else = {", adapter)
        self.assertIn("position = 0", adapter)
        self.assertEqual(adapter.count("zg361_pp_open_"), 4)
        self.assertIn("if = {", adapter)
        self.assertGreaterEqual(adapter.count("else_if = {"), 4)
        self.assertEqual(adapter.count("is_ai = no"), 1)
        self.assertIn("trigger_event = { id = zg361pp.9100 days = 1 }", adapter)
        self.assertIn("zg361_pp_batch_strategy_cycle = var:zg361_review_serial", adapter)

    def test_dukes_or_higher_manage_counts_and_barons_only_receive(self) -> None:
        for domain in gen.DOMAINS:
            block = effect_block(self.effects, f"zg361_pp_open_{domain.key}_case_effect")
            self.assertIn("root = {", block)
            self.assertIn("zg361_is_celestial_liege_trigger = yes", block)
            self.assertIn("zg361_is_reviewable_vassal_trigger = yes", block)
            self.assertIn("liege = root", block)
        for mid in gen.SUBJECT_RESPONSE_IDS:
            block = effect_block(self.effects, f"zg361_pp_m{mid:03d}_subject_response_effect")
            self.assertIn("zg361_case_kernel_subject_self_guard_trigger", block)
            self.assertNotIn("zg361_is_celestial_liege_trigger", block)

    def test_second_ai_exception_is_background_only(self) -> None:
        for domain in gen.DOMAINS:
            block = effect_block(self.effects, f"zg361_pp_dispatch_{domain.key}_stage_01_effect")
            self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", block)
            self.assertIn("background resolver only, no GUI", block)
            self.assertIn("is_ai = no zg361_is_celestial_liege_trigger = yes", block)
        visible = [effect_block(self.events, f"zg361pp.{mid}") for mid in range(146, 192)]
        self.assertTrue(all("is_ai = no" in block for block in visible))
        subject_visible = [
            effect_block(self.events, f"zg361pp.{5000 + mid}")
            for mid in sorted(gen.SUBJECT_RESPONSE_IDS)
        ]
        self.assertTrue(all("is_ai = no" in block for block in subject_visible))

    def test_subject_response_is_exact_ticketed_and_never_manager_authored(self) -> None:
        self.assertEqual(gen.SUBJECT_RESPONSE_IDS, frozenset({151, 166, 190}))
        self.assertNotIn("zg361pp.5183 = {", self.events)
        self.assertNotIn("zg361_pp_m183_subject_response_effect", self.effects)
        for mid in sorted(gen.SUBJECT_RESPONSE_IDS):
            event = effect_block(self.events, f"zg361pp.{5000 + mid}")
            response = effect_block(
                self.effects, f"zg361_pp_m{mid:03d}_subject_response_effect"
            )
            resume = effect_block(
                self.effects, f"zg361_pp_m{mid:03d}_resume_after_subject_effect"
            )
            self.assertIn("is_ai = no", event)
            self.assertEqual(event.count("option = {"), 2)
            for suffix in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"zg361_pp_subject_prompt_{suffix}", event)
            self.assertIn("zg361_case_kernel_subject_self_guard_trigger", response)
            self.assertIn(f"zg361_pp_m{mid:03d}_subject_response", response)
            self.assertIn("zg361_case_kernel_subject_self_guard_trigger", resume)

    def test_manager_and_subject_copy_use_their_own_saved_scope_family(self) -> None:
        rows = gen.localization_rows("simp_chinese")
        loc: dict[str, str] = {}
        for row in rows:
            match = re.match(r'^\s*([^:]+):\d+\s+"(.*)"$', row)
            if match:
                loc[match.group(1)] = match.group(2)

        for mid in (166, 190):
            manager_event = effect_block(self.events, f"zg361pp.{mid}")
            subject_event = effect_block(self.events, f"zg361pp.{5000 + mid}")
            self.assertIn(f"desc = zg361pp.{mid}.desc", manager_event)
            self.assertIn(f"desc = zg361pp.{5000 + mid}.desc", subject_event)
            self.assertNotIn(f"desc = zg361pp.{mid}.desc", subject_event)

            manager_copy = loc[f"zg361pp.{mid}.desc"]
            subject_copy = loc[f"zg361pp.{5000 + mid}.desc"]
            self.assertIn("[zg361_pp_prompt_owner.GetShortUIName]", manager_copy)
            self.assertIn("[zg361_pp_prompt_subject.GetShortUIName]", manager_copy)
            self.assertNotIn("[zg361_pp_subject_prompt_", manager_copy)
            self.assertIn(
                "[zg361_pp_subject_prompt_owner.GetShortUIName]", subject_copy
            )
            self.assertIn(
                "[zg361_pp_subject_prompt_subject.GetShortUIName]", subject_copy
            )
            self.assertNotIn("[zg361_pp_prompt_", subject_copy)

    def test_visible_decisions_form_a_single_option_driven_queue(self) -> None:
        self.assertEqual(
            len(re.findall(r"^zg361pp\.(?:14[6-9]|1[5-8]\d|19[01]) = \{$", self.events, re.MULTILINE)),
            46,
        )
        for row in gen.MECHANISMS:
            block = effect_block(self.events, f"zg361pp.{row.mechanism_id}")
            expected_options = 4 if row.mechanism_id == 189 else (2 if row.mechanism_id == 166 else 3)
            self.assertEqual(block.count("option = {"), expected_options)
            self.assertNotIn("immediate = {", block)
            # Each selected option can schedule at most the one next card.
            for option in re.findall(r"option = \{.*?\n\t\}", block, re.DOTALL):
                visible_triggers = re.findall(r"trigger_event = \{ id = zg361pp\.(?:14[6-9]|1[5-8]\d|19[01])", option)
                self.assertLessEqual(len(visible_triggers), 1)
        adapter = effect_block(self.effects, "zg361_pp_manager_portfolio_adapter_effect")
        self.assertNotRegex(adapter, r"trigger_event = \{ id = zg361pp\.(?:14[6-9]|1[5-8]\d|19[01])")
        for domain_index, domain in enumerate(gen.DOMAINS, start=1):
            outcome = effect_block(self.effects, f"zg361_pp_resolve_{domain.key}_outcome_effect")
            completion = effect_block(self.events, f"zg361pp.{9000 + domain_index}")
            self.assertIn("Retain the queue lock through the visible completion card", outcome)
            self.assertIn("The authorized AI route has no visible card", outcome)
            self.assertIn("var:zg361_pp_portfolio_queue_active = 1", completion)
            self.assertIn("name = zg361_pp_portfolio_queue_active value = 0", completion)

    def test_m11_batch_strategy_reduces_only_the_safe_pp_subset(self) -> None:
        requested = {
            146, 147, 148, 152, 154, 156, 163, 164, 167, 168,
            169, 171, 172, 174, 176, 177, 179, 181, 186, 191,
        }
        safe = requested - {191}
        self.assertEqual(gen.REQUESTED_BACKGROUND_BATCH_IDS, requested)
        self.assertEqual(gen.BACKGROUND_BATCH_PROTECTED_IDS, {191})
        self.assertEqual(gen.BACKGROUND_BATCH_IDS, safe)
        self.assertEqual(len(gen.BACKGROUND_BATCH_IDS), 19)
        self.assertFalse(
            gen.BACKGROUND_BATCH_IDS
            & (
                gen.DUAL_COST_IDS
                | gen.SUBJECT_RESPONSE_IDS
                | gen.DELAYED_STAGE_GATE_IDS
                | {191}
            )
        )

        strategy = effect_block(self.events, "zg361pp.9100")
        self.assertEqual(strategy.count("option = {"), 4)
        for route, key in ((1, "a"), (2, "b"), (3, "c"), (4, "d")):
            self.assertIn(f"name = zg361pp.9100.{key}", strategy)
            self.assertIn(
                f"name = zg361_pp_batch_strategy_route value = {route}",
                strategy,
            )
        self.assertEqual(
            strategy.count(
                "name = zg361_pp_batch_strategy_cycle value = var:zg361_review_serial"
            ),
            4,
        )
        self.assertEqual(
            strategy.count("zg361_pp_manager_portfolio_adapter_effect = yes"),
            4,
        )

        for mid in sorted(safe):
            domain = gen.DOMAIN_BY_ID[mid]
            state = gen.mechanism_stage(mid)
            dispatch = effect_block(
                self.effects,
                f"zg361_pp_dispatch_{domain.key}_stage_{state:02d}_effect",
            )
            self.assertRegex(
                dispatch,
                rf"zg361_pp_m{mid:03d}_core_effect = \{{\n"
                r"\s+ROUTE = var:zg361_pp_batch_strategy_route_frozen",
                f"{mid}: safe item does not reuse its original core",
            )
            self.assertIn(
                "NOT = { has_variable = zg361_pp_runtime_applied }",
                dispatch,
                f"{mid}: failed core cannot reach the visible fallback",
            )
            self.assertGreaterEqual(
                dispatch.count(f"trigger_event = {{ id = zg361pp.{mid} days = 1 }}"),
                2,
                f"{mid}: dependency/resource failure or itemized mode can skip the card",
            )

        # The 46 original manager events stay generated as exact fallbacks.
        for mid in range(146, 192):
            self.assertIn(f"zg361pp.{mid} = {{", self.events)
        protected = effect_block(self.effects, "zg361_pp_dispatch_w_stage_05_effect")
        self.assertNotRegex(
            protected,
            r"zg361_pp_m191_core_effect = \{\n\s+ROUTE = "
            r"var:zg361_pp_batch_strategy_route_frozen",
        )
        self.assertIn("trigger_event = { id = zg361pp.191 days = 1 }", protected)
        # A/B/C replaces nineteen manager cards with one policy card; D keeps
        # the whole original itemized sequence and adds only that policy card.
        self.assertEqual(46 - len(safe) + 1, 28)
        self.assertEqual(46 + 1, 47)

    def test_player_copy_has_no_ui_or_implementation_meta_language(self) -> None:
        loc = text(
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / "zg361_feedback_promotion_pip_l_simp_chinese.yml"
        )
        for token in (
            "本卡", "玩家", "结算器", "回写", "下方按钮", "按钮及说明",
            "批处理", "闸门", "调用", "原裁定卡", "归档卡", "原始条件",
            "PPT",
        ):
            self.assertNotIn(token, loc, token)
        english = text(
            MOD_ROOT
            / "localization"
            / "english"
            / "zg361_feedback_promotion_pip_l_english.yml"
        ).lower()
        for token in (
            "this card", "player choices", "the settler", "write back",
            "buttons and their tooltips", "batch handling", "time gates",
            "invoke each original", "item's card",
        ):
            self.assertNotIn(token, english, token)

    def test_write_to_consumer_cross_links_are_present(self) -> None:
        for token in (
            "zg361_pp_m168_sponsor_observation_id",
            "zg361_pp_m169_observation_window_consumed",
            "zg361_pp_m169_cross_team_share_consumed",
            "zg361_pp_m169_trial_authority_consumed",
            "zg361_pp_m172_expert_weight_consumed",
            "zg361_pp_m172_external_weight_consumed",
            "zg361_pp_m172_active_panel_revision_consumed",
            "zg361_pp_m178_weighted_score",
            "zg361_pp_m178_coaching_hours_consumed",
            "zg361_pp_m178_candidate_share_consumed",
            "zg361_pp_m178_leverage_consumed",
            "zg361_pp_m179_feedback_owner value = var:zg361_pp_m171_active_panel_1",
            "zg361_pp_m180_prior_gap_id value = var:zg361_pp_m179_gap_id",
        ):
            self.assertIn(token, self.effects)

    def test_true_result_case_is_frozen_and_visible_without_last_grade_fallback(self) -> None:
        for domain in ("t", "w"):
            opened = effect_block(self.effects, f"zg361_pp_open_{domain}_case_effect")
            for suffix in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"name = zg361_pp_{domain}_result_{suffix}", opened)
            for token in (
                f"name = zg361_pp_{domain}_frozen_grade value = var:zg361_result_grade",
                f"name = zg361_pp_{domain}_frozen_reason value = var:zg361_result_grade_reason",
                f"name = zg361_pp_{domain}_frozen_kpi value = var:zg361_result_kpi_frozen",
                "var:zg361_result_case_owner = root",
                "var:zg361_result_cycle_serial = root.var:zg361_review_serial",
                "var:zg361_result_case_state >= 3",
            ):
                self.assertIn(token, opened)
            self.assertNotIn("zg361_last_grade", opened)
        open_u = effect_block(self.effects, "zg361_pp_open_u_case_effect")
        for suffix in ("owner", "subject", "cycle", "case", "state"):
            self.assertIn(f"name = zg361_pp_u_result_{suffix}", open_u)
        self.assertIn("name = zg361_pp_u_frozen_grade value = var:zg361_result_grade", open_u)
        self.assertIn("var:zg361_result_grade >= 2", open_u)
        adapter = effect_block(self.effects, "zg361_pp_manager_portfolio_adapter_effect")
        self.assertIn("zg361_pp_u_skipped_not_eligible_cycle", adapter)
        self.assertIn("zg361_pp_v_skipped_no_winner_cycle", adapter)
        self.assertIn("zg361_pp_w_skipped_not_applicable_cycle", adapter)
        open_w = effect_block(self.effects, "zg361_pp_open_w_case_effect")
        self.assertIn("var:zg361_result_grade = 1", open_w)
        self.assertIn("zg361_pp_w_evidence_component_count", open_w)
        self.assertIn(
            "zg361_pp_w_pip_gate_candidate value = var:zg361_b2_pip_gate_status",
            open_w,
        )
        self.assertIn(
            "zg361_pp_w_evidence_component_count value = var:zg361_b2_pip_gate_component_count",
            open_w,
        )
        self.assertIn(
            "zg361_pp_w_pip_gate_threshold value = var:zg361_b2_pip_gate_threshold",
            open_w,
        )
        for mid in (*range(146, 157), *range(181, 192)):
            event = effect_block(self.events, f"zg361pp.{mid}")
            self.assertIn("zg361pp.grade.375", event)
            self.assertIn("zg361pp.grade.350", event)
            self.assertIn("zg361pp.grade.325", event)

    def test_every_audit_consumes_its_typed_payload_not_only_route(self) -> None:
        self.assertEqual(set(gen.DELAYED_CONSUMER_FIELD_BY_ID), set(range(146, 192)))
        for row in gen.MECHANISMS:
            mid = row.mechanism_id
            field = gen.DELAYED_CONSUMER_FIELD_BY_ID[mid]
            for index, _ in enumerate(row.deadlines, start=1):
                event_id = 2000 + mid + (1000 if index > 1 else 0)
                event = effect_block(self.events, f"zg361pp.{event_id}")
                self.assertIn(
                    f"name = zg361_pp_m{mid:03d}_audit_{index}_business_input value = var:zg361_pp_m{mid:03d}_{field}",
                    event,
                )
                self.assertIn(f"zg361_pp_m{mid:03d}_audit_{index}_business_settled", event)
                self.assertIn(f"zg361_pp_m{mid:03d}_audit_{index}_policy_debt_settled", event)
                self.assertIn("NOT = { var:zg361_pp_m", event)

    def test_prescreen_rejection_never_burns_a_promotion_slot(self) -> None:
        core = effect_block(self.effects, "zg361_pp_m160_core_effect")
        self.assertIn("scope:zg361_pp_route = 1", core)
        self.assertIn("zg361_pp_u_promotion_slot_available >= 1", core)
        self.assertIn("zg361_pp_m160_promotion_slot_status = 1", core)
        self.assertNotIn("zg361_pp_m160_promotion_slot_status = 2", core)
        self.assertIn("scope:zg361_pp_route = 2", core)
        self.assertIn("name = zg361_pp_m160_prescreen_pass value = 0", core)
        open_v = effect_block(self.effects, "zg361_pp_open_v_case_effect")
        self.assertIn("var:zg361_pp_m160_promotion_slot_status = 1", open_v)
        self.assertIn("name = zg361_pp_m160_promotion_slot_status value = 2", open_v)

    def test_pip_gate_is_an_exact_b2_projection_without_grade_only_autostart(self) -> None:
        m182 = effect_block(self.effects, "zg361_pp_m182_core_effect")
        self.assertIn("var:zg361_pp_w_pip_gate_candidate = 1", m182)
        self.assertIn("zg361_pp_m182_evidence_component_count value = var:zg361_b2_pip_gate_component_count", m182)
        self.assertIn("zg361_pp_m182_threshold_required value = var:zg361_b2_pip_gate_threshold", m182)
        self.assertIn("zg361_pp_m182_gate_status value = var:zg361_b2_pip_gate_status", m182)
        self.assertIn("name = zg361_pp_m182_grade_only_autostart value = 0", m182)
        self.assertNotIn("name = zg361_pp_m182_grade_only_autostart value = 1", m182)
        self.assertNotIn("name = zg361_pp_m182_gate_status value = 2", m182)
        m183 = effect_block(self.effects, "zg361_pp_m183_core_effect")
        self.assertIn("var:zg361_pp_m182_gate_status = 1", m183)
        self.assertNotIn("var:zg361_pp_m182_gate_status = 2", m183)
        self.assertIn("acknowledgement_status value = var:zg361_b2_pip_subject_response", m183)
        self.assertIn("subject_statement_author value = var:zg361_b2_pip_subject_response_author", m183)
        self.assertNotIn("subject_signed value = scope:zg361_pp_route", m183)

    def test_pip_capacity_and_support_truth_are_owned_only_by_b2(self) -> None:
        m184 = effect_block(self.effects, "zg361_pp_m184_core_effect")
        for token in (
            "capacity_reserved value = var:zg361_b2_pip_support_reserved",
            "overload_liability value = var:zg361_b2_pip_support_absent",
            "support_hours value = var:zg361_b2_pip_support_hours",
            "support_budget_spent value = var:zg361_b2_pip_support_budget_spent",
            "support_case value = var:zg361_b2_m016_receipt_serial",
        ):
            self.assertIn(token, m184)
        for block in (
            effect_block(self.events, "zg361pp.2187"),
            effect_block(self.effects, "zg361_pp_m189_core_effect"),
        ):
            self.assertNotIn("zg361_case_kernel_refund_transaction_effect", block)
            self.assertNotIn("zg361_pp_m184_pip_capacity", block)
            self.assertNotIn("zg361_pp_w_capacity_released", block)

    def test_w_midpoint_and_graduation_project_b2_producer_truth(self) -> None:
        midpoint = effect_block(self.events, "zg361pp.2185")
        for token in (
            "zg361_pp_m185_progress_truth_status value = 0",
            "zg361_pp_m185_progress_red_code value = 1",
            "has_variable = zg361_b2_pip_midpoint_progress_delta",
            "var:zg361_b2_pip_midpoint_progress_owner = var:zg361_b2_pip_owner",
            "var:zg361_b2_pip_midpoint_progress_subject = this",
            "var:zg361_b2_pip_midpoint_progress_cycle = var:zg361_b2_pip_cycle",
            "var:zg361_b2_pip_midpoint_progress_case = var:zg361_b2_pip_case",
            "zg361_pp_m185_progress_snapshot value = var:zg361_b2_pip_midpoint_progress_delta",
            "zg361_pp_m185_progress_truth_status value = var:zg361_b2_pip_midpoint_progress_status",
            "zg361_pp_m185_progress_red_code value = var:zg361_b2_pip_midpoint_progress_red_code",
        ):
            self.assertIn(token, midpoint)
        self.assertNotIn(
            "zg361_pp_m185_progress_truth_status value = 1", midpoint
        )

        graduation = effect_block(self.events, "zg361pp.2187")
        for token in (
            "var:zg361_b2_pip_independent_review_status = 1",
            "var:zg361_b2_pip_independent_review_status = 2",
            "var:zg361_b2_pip_independent_review_red_code = 0",
            "var:zg361_b2_pip_independent_review_receipt = var:zg361_b2_pip_case",
            "zg361_pp_m187_independent_review_pass value = var:zg361_b2_pip_independent_review_status",
            "zg361_pp_m187_independent_review_red_code value = var:zg361_b2_pip_independent_review_red_code",
        ):
            self.assertIn(token, graduation)
        self.assertEqual(
            graduation.count(
                "zg361_pp_m187_independent_review_pass value = var:zg361_b2_pip_independent_review_status"
            ),
            2,
        )

    def test_midpoint_graduation_and_relapse_are_real_time_gates(self) -> None:
        self.assertEqual(gen.DELAYED_STAGE_GATE_IDS, {185, 187, 188})
        schedules = {185: 180, 187: 366, 188: 365}
        for mid, days in schedules.items():
            schedule = effect_block(self.effects, f"zg361_pp_m{mid:03d}_schedule_audit_1_effect")
            self.assertIn(f"days = {days}", schedule)
            event = effect_block(self.events, f"zg361pp.{2000 + mid}")
            self.assertIn(f"zg361_pp_m{mid:03d}_audit_1_consumed = 0", event)
        self.assertIn(
            "var:zg361_pp_m185_audit_1_consumed = 1",
            effect_block(self.effects, "zg361_pp_w_try_advance_02_effect"),
        )
        self.assertIn(
            "var:zg361_pp_m187_audit_1_consumed = 1",
            effect_block(self.effects, "zg361_pp_w_try_advance_03_effect"),
        )
        self.assertIn(
            "var:zg361_pp_m188_audit_1_consumed = 1",
            effect_block(self.effects, "zg361_pp_w_try_advance_04_effect"),
        )
        self.assertNotIn("zg361pp.189", effect_block(self.events, "zg361pp.188"))
        self.assertIn("zg361pp.189", effect_block(self.events, "zg361pp.2188"))
        stage4 = effect_block(self.effects, "zg361_pp_dispatch_w_stage_04_effect")
        self.assertIn("zg361_pp_m188_core_effect", stage4)
        self.assertIn("zg361_pp_m189_core_effect", stage4)
        self.assertIn("zg361_pp_m188_skip_first_failure_effect = yes", stage4)
        self.assertIn(
            "DAYS = 368",
            effect_block(self.effects, "zg361_pp_schedule_w_stage_04_effect"),
        )

    def test_first_pip_failure_skips_observation_and_reaches_terminal_fork(self) -> None:
        skip = effect_block(self.effects, "zg361_pp_m188_skip_first_failure_effect")
        for token in (
            "EXPECTED_STATE = 4",
            "var:zg361_pp_m187_graduation_status = 2",
            "var:zg361_b2_pip_state = 4",
            "var:zg361_b2_pip_failure_receipt = var:zg361_b2_pip_case",
            "var:zg361_pp_m188_receipt_active = 0",
            "name = zg361_pp_m188_receipt_route value = 0",
            "name = zg361_pp_m188_route value = 0",
            "name = zg361_pp_m188_relapse_window value = 0",
            "name = zg361_pp_m188_relapse_status value = 0",
            "name = zg361_pp_m188_skipped_first_failure value = 1",
            "name = zg361_pp_m188_audit_1_state value = 2",
            "name = zg361_pp_m188_audit_1_consumed value = 1",
            "zg361_pp_m188_consume_effect = yes",
        ):
            self.assertIn(token, skip)
        self.assertIn(
            "has_variable = zg361_pp_m188_relapse_window",
            effect_block(self.effects, "zg361_pp_m188_consume_effect"),
        )

        stage4 = effect_block(self.effects, "zg361_pp_dispatch_w_stage_04_effect")
        self.assertIn("zg361_pp_m188_skip_first_failure_effect = yes", stage4)
        self.assertIn("id = zg361pp.189 days = 1", stage4)
        self.assertIn("zg361_pp_m189_core_effect", stage4)
        self.assertIn("id = zg361pp.188 days = 1", stage4)

        m189 = effect_block(self.effects, "zg361_pp_m189_core_effect")
        for token in (
            "var:zg361_pp_m187_graduation_status = 2",
            "var:zg361_b2_pip_state = 4",
            "var:zg361_b2_pip_failure_receipt = var:zg361_b2_pip_case",
            "var:zg361_pp_m188_skipped_first_failure = 1",
            "var:zg361_pp_m188_audit_1_consumed = 1",
            "var:zg361_pp_m188_observation_closed = 1",
            "var:zg361_pp_m188_relapse_status = 1",
            "var:zg361_pp_m188_same_category_relapse = 1",
        ):
            self.assertIn(token, m189)
        self.assertIn(
            "remove_variable = zg361_pp_m188_skipped_first_failure",
            effect_block(self.effects, "zg361_pp_open_w_case_effect"),
        )

    def test_stage4_timeout_rechecks_barrier_after_delayed_observation_audit(self) -> None:
        timeout = effect_block(self.effects, "zg361_pp_w_timeout_stage_04_effect")
        self.assertLess(
            timeout.index("zg361_pp_m188_core_effect"),
            timeout.index("zg361_pp_m189_core_effect"),
        )
        audit = effect_block(self.events, "zg361pp.2188")
        retry = audit.rindex("zg361_pp_w_try_advance_04_effect = yes")
        self.assertGreater(retry, audit.rindex("zg361_pp_m189_core_effect"))
        barrier = effect_block(self.effects, "zg361_pp_w_try_advance_04_effect")
        for token in (
            "var:zg361_pp_m188_consumed = 1",
            "var:zg361_pp_m189_consumed = 1",
            "var:zg361_pp_m188_audit_1_consumed = 1",
        ):
            self.assertIn(token, barrier)

    def test_relapse_audit_is_same_category_and_skips_terminal_when_clean(self) -> None:
        m188 = effect_block(self.effects, "zg361_pp_m188_core_effect")
        audit = effect_block(self.events, "zg361pp.2188")
        skip = effect_block(self.effects, "zg361_pp_m189_skip_no_relapse_effect")
        self.assertIn("zg361_pp_m188_observation_due_cycle", m188)
        for token in (
            "var:zg361_result_cycle_serial = var:zg361_pp_m188_observation_due_cycle",
            "has_variable = zg361_result_grade_reason",
            "zg361_pp_m188_observed_result_reason value = var:zg361_result_grade_reason",
            "zg361_pp_m188_observed_category value = 0",
            "var:zg361_pp_m188_observed_category >= 1",
            "var:zg361_pp_m188_observed_category = var:zg361_pp_m188_category_snapshot",
            "name = zg361_pp_m188_same_category_relapse value = 1",
            "name = zg361_pp_m188_relapse_status value = 1",
            "zg361_pp_m189_skip_no_relapse_effect = yes",
        ):
            self.assertIn(token, audit)
        self.assertNotIn("var:zg361_result_grade_reason = 5", audit)
        for token in (
            "var:zg361_pp_m188_relapse_status = 2",
            "name = zg361_pp_m189_skipped_no_relapse value = 1",
            "name = zg361_pp_m189_route value = 0",
            "name = zg361_pp_m189_terminal_code value = 0",
            "zg361_pp_m189_consume_effect = yes",
        ):
            self.assertIn(token, skip)
        self.assertIn("zg361pp.terminal.graduated", effect_block(self.events, "zg361pp.9004"))

    def test_route_c_audits_never_create_midpoint_graduation_or_relapse_objects(self) -> None:
        checks = {
            185: "zg361_pp_m185_midpoint_status",
            187: "zg361_pp_m187_graduation_status",
            188: "zg361_pp_m188_observation_closed",
        }
        for mid, business_field in checks.items():
            event = effect_block(self.events, f"zg361pp.{2000 + mid}")
            guarded = re.compile(
                rf"limit = \{{ NOT = \{{ var:zg361_pp_m{mid:03d}_route = 3 \}} \}}.*?{business_field}",
                re.DOTALL,
            )
            self.assertRegex(event, guarded)
            self.assertIn(f"zg361_pp_m{mid:03d}_audit_1_policy_debt_settled", event)
        m189 = effect_block(self.effects, "zg361_pp_m189_core_effect")
        self.assertIn("var:zg361_pp_m188_relapse_status = 1", m189)
        self.assertIn("var:zg361_pp_m188_same_category_relapse = 1", m189)

    def test_terminal_fork_is_exclusive_and_exit_cost_is_route_bound(self) -> None:
        m189 = effect_block(self.effects, "zg361_pp_m189_core_effect")
        for token in (
            "zg361_pp_m189_second_pip value = 0",
            "zg361_pp_m189_transfer value = 0",
            "zg361_pp_m189_exit value = 0",
            "zg361_pp_m189_terminal_sum",
            "var:zg361_pp_m189_terminal_sum = 1",
            "name = zg361_pp_m189_exclusive_terminal value = 1",
            "name = zg361_pp_m189_terminal_code value = 1",
            "name = zg361_pp_m189_terminal_code value = 2",
            "name = zg361_pp_m189_terminal_code value = 3",
            "zg361_pp_w_exit_cost_available >= 1",
            "scope:zg361_pp_route = 2",
        ):
            self.assertIn(token, m189)
        self.assertEqual(gen.DUAL_COST_ROUTE_BY_ID[189], 2)
        self.assertEqual(gen.ROUTE_B_EXTRA_RESOURCES_BY_ID[189], ("exit_cost",))

    def test_terminal_fork_never_releases_b2_capacity(self) -> None:
        core = effect_block(self.effects, "zg361_pp_m189_core_effect")
        self.assertNotIn("zg361_case_kernel_refund_transaction_effect", gen.semantic_write(gen.MECHANISM_BY_ID[189]))
        self.assertNotIn("zg361_case_kernel_refund_transaction_effect", core)
        self.assertNotIn("zg361_pp_m184_pip_capacity_status", core)
        self.assertNotIn("zg361_pp_w_capacity_released", core)
        open_w = effect_block(self.effects, "zg361_pp_open_w_case_effect")
        self.assertNotIn("zg361_pp_w_capacity_release_reason", open_w)

    def test_filler_candidate_and_external_vacancy_are_freshly_bound(self) -> None:
        open_u = effect_block(self.effects, "zg361_pp_open_u_case_effect")
        self.assertLess(
            open_u.index("remove_variable = zg361_pp_m161_filler_candidate"),
            open_u.index("name = zg361_pp_m161_filler_candidate value = scope:zg361_pp_u_filler_candidate"),
        )
        open_w = effect_block(self.effects, "zg361_pp_open_w_case_effect")
        for token in (
            "has_variable = zg361_transfer_vacancy_id",
            "has_variable = zg361_transfer_vacancy_owner",
            "has_variable = zg361_transfer_vacancy_subject",
            "has_variable = zg361_transfer_vacancy_receiver",
            "has_variable = zg361_transfer_vacancy_source_cycle",
            "has_variable = zg361_transfer_vacancy_source_case",
            "has_variable = zg361_transfer_vacancy_title",
            "has_variable = zg361_transfer_vacancy_maturity_cycle",
            "has_variable = zg361_transfer_vacancy_position_kind",
            "var:zg361_transfer_vacancy_active = 1",
            "var:zg361_transfer_vacancy_status = 1",
            "var:zg361_transfer_vacancy_owner = root",
            "var:zg361_transfer_vacancy_subject = this",
            "var:zg361_transfer_vacancy_source_cycle < root.var:zg361_review_serial",
            "var:zg361_transfer_vacancy_maturity_cycle <= root.var:zg361_review_serial",
            "var:zg361_transfer_vacancy_position_kind = 1",
            "primary_title = var:zg361_transfer_vacancy_title",
            "var:zg361_transfer_vacancy_title = { holder = this }",
            "var:zg361_transfer_hc_reserved = 1",
            "var:zg361_transfer_hc_conserved = 1",
            "liege = root",
            "primary_title.tier > prev.primary_title.tier",
            "vassal_count < vassal_limit",
            "NOT = { is_at_war_with = var:zg361_transfer_vacancy_receiver }",
            "zg361_pp_w_transfer_vacancy_id value = var:zg361_transfer_vacancy_id",
            "zg361_pp_w_transfer_vacancy_receiver value = var:zg361_transfer_vacancy_receiver",
            "zg361_pp_w_transfer_source_cycle value = var:zg361_transfer_vacancy_source_cycle",
            "zg361_pp_w_transfer_source_case value = var:zg361_transfer_vacancy_source_case",
            "zg361_pp_w_transfer_vacancy_title value = var:zg361_transfer_vacancy_title",
            "zg361_pp_w_transfer_position_kind value = var:zg361_transfer_vacancy_position_kind",
            "name = zg361_pp_w_real_vacancy value = 1",
        ):
            self.assertIn(token, open_w)
        self.assertIn("trigger_if = {", open_w)
        self.assertIn("has_variable = zg361_transfer_hc_conserved", open_w)
        self.assertIn("trigger_else = { always = no }", open_w)
        self.assertNotIn(
            "limit = { has_variable = zg361_pp_w_receiving_manager } set_variable = { name = zg361_pp_w_real_vacancy value = 1 }",
            open_w,
        )

    def test_transfer_disclosure_has_receiver_and_subject_acl(self) -> None:
        m190 = effect_block(self.effects, "zg361_pp_m190_core_effect")
        for token in (
            "var:zg361_pp_m189_terminal_code = 2",
            "var:zg361_pp_m189_receiving_manager = var:zg361_pp_w_receiving_manager",
            "zg361_is_celestial_liege_trigger = yes",
            "NOT = { this = root }",
            "zg361_pp_m190_acl_subject value = this",
            "zg361_pp_m190_acl_receiver value = var:zg361_pp_m189_receiving_manager",
            "zg361_pp_m190_vacancy_id_snapshot value = var:zg361_pp_w_transfer_vacancy_id",
            "zg361_pp_m190_goal_snapshot value = var:zg361_b2_pip_case",
            "zg361_pp_m190_support_snapshot value = var:zg361_b2_pip_support_reserved",
            "zg361_pp_m190_completion_snapshot value = var:zg361_b2_pip_state",
            "zg361_pp_m190_subject_statement_snapshot value = var:zg361_pp_m190_subject_statement_code",
            "zg361_pp_m190_private_ids_excluded value = 1",
            "zg361_pp_m190_acl_pass value = 1",
            "zg361_career_hc_accept_pp_transfer_request_effect = yes",
            "zg361_pp_m190_external_request_status",
            "zg361_pp_m190_external_request_red_code",
            "zg361_pp_received_transfer_goal",
            "zg361_pp_received_transfer_support",
            "zg361_pp_received_transfer_completion",
            "zg361_pp_received_transfer_subject_statement",
            "zg361_pp_received_transfer_subject_statement_included value = 0",
            "zg361_pp_received_transfer_subject_statement_included value = 1",
        ):
            self.assertIn(token, m190)
        self.assertIn(
            "limit = { var:zg361_pp_m190_subject_response = 1 }", m190
        )
        manager_event = effect_block(self.events, "zg361pp.190")
        self.assertIn(
            "var:zg361_pp_m190_subject_response = 1", manager_event
        )
        self.assertIn(
            "var:zg361_pp_m190_subject_response = 2", manager_event
        )
        self.assertIn(
            "limit = { has_variable = zg361_transfer_adapter_applied has_variable = zg361_transfer_vacancy_status }",
            m190,
        )
        response = effect_block(self.effects, "zg361_pp_m190_subject_response_effect")
        self.assertIn("zg361_case_kernel_subject_self_guard_trigger", response)
        self.assertIn("zg361_pp_m190_subject_statement_author value = this", response)
        self.assertNotIn("zg361_pp_m190_subject_statement_receiver", response)
        audit = effect_block(self.events, "zg361pp.2190")
        self.assertIn("name = zg361_pp_m190_audit_delivery_acl_pass value = 0", audit)
        self.assertIn("name = zg361_pp_m190_audit_delivery_acl_pass value = 1", audit)
        self.assertIn(
            "name = zg361_pp_m190_audit_1_business_input value = var:zg361_pp_m190_audit_delivery_acl_pass",
            audit,
        )
        for token in (
            "var:zg361_transfer_vacancy_status = 2",
            "var:zg361_transfer_vacancy_active = 1",
            "var:zg361_transfer_request_pp_owner = root.var:zg361_case_w_owner",
            "var:zg361_transfer_request_pp_subject = root",
            "var:zg361_transfer_request_pp_cycle = root.var:zg361_case_w_cycle_serial",
            "var:zg361_transfer_request_pp_case = root.var:zg361_case_w_case_serial",
            "var:zg361_transfer_request_vacancy = root.var:zg361_pp_m190_vacancy_id_snapshot",
            "zg361_career_hc_settle_pp_transfer_effect = yes",
            "zg361_pp_m190_audit_external_status",
            "zg361_pp_m190_audit_external_red_code",
        ):
            self.assertIn(token, audit)

    def test_appeal_non_aggravation_is_snapshotted_and_never_writes_grade(self) -> None:
        m151 = effect_block(self.effects, "zg361_pp_m151_core_effect")
        response = effect_block(self.effects, "zg361_pp_m151_subject_response_effect")
        appeal_audit = effect_block(self.events, "zg361pp.3151")
        self.assertIn("zg361_pp_m151_non_aggravation_grade value = var:zg361_pp_t_frozen_grade", m151)
        self.assertIn("zg361_pp_m151_appeal_snapshot_grade", response)
        self.assertIn("var:zg361_result_grade >= var:zg361_pp_m151_appeal_snapshot_grade", appeal_audit)
        self.assertIn("zg361_pp_m151_appeal_closed_without_filing", appeal_audit)
        self.assertNotIn("zg361_pp_m151_agreed value = 1", m151)
        self.assertIn("zg361_pp_m151_receipt_acknowledged value = 1", m151)
        self.assertIn("zg361_pp_m151_coercion_attempted value = 1", m151)
        forbidden = re.compile(r"(?:set|change)_variable\s*=\s*\{\s*name\s*=\s*zg361_result_grade\b")
        self.assertIsNone(forbidden.search(self.effects))
        self.assertIsNone(forbidden.search(self.events))

    def test_pip_acknowledgement_options_match_the_subject_receipt(self) -> None:
        event = effect_block(self.events, "zg361pp.183")
        self.assertIn(
            "OR = { var:zg361_b2_pip_subject_response = 1 "
            "var:zg361_b2_pip_subject_response = 2 }",
            event,
        )
        self.assertIn("var:zg361_b2_pip_subject_response = 3", event)

    def test_completion_cards_expose_route_and_w_terminal_outcome(self) -> None:
        for event_id in range(9001, 9005):
            event = effect_block(self.events, f"zg361pp.{event_id}")
            self.assertIn("scope:zg361_pp_completion_subject", event)
            self.assertIn("zg361pp.outcome.evidence", event)
            self.assertIn("zg361pp.outcome.political", event)
            self.assertIn("zg361pp.outcome.mixed", event)
        w = effect_block(self.events, "zg361pp.9004")
        for key in (
            "zg361pp.terminal.graduated",
            "zg361pp.terminal.second_pip",
            "zg361pp.terminal.transfer",
            "zg361pp.terminal.exit",
        ):
            self.assertIn(key, w)

    def test_all_completion_titles_name_the_actual_subject(self) -> None:
        subject = "[zg361_pp_completion_subject.GetShortUIName]"
        expected = {
            "simp_chinese": {
                "zg361pp.9001.t": f"本轮选择已录入：{subject}的反馈谈判与承诺债",
                "zg361pp.9002.t": f"本轮选择已录入：{subject}的晋升提名与预审",
                "zg361pp.9003.t": f"本轮选择已录入：{subject}的晋升答辩与评委政治",
                "zg361pp.9004.t": f"本轮选择已录入：{subject}的绩效改进计划启动、毕业与复发",
            },
            "english": {
                "zg361pp.9001.t": f"Cycle Choices Recorded for {subject}: Feedback bargaining and promise debt",
                "zg361pp.9002.t": f"Cycle Choices Recorded for {subject}: Promotion nomination and prescreen",
                "zg361pp.9003.t": f"Cycle Choices Recorded for {subject}: Promotion panels and review politics",
                "zg361pp.9004.t": f"Cycle Choices Recorded for {subject}: PIP initiation, graduation and relapse",
            },
        }
        for language, titles in expected.items():
            loc = "\n".join(gen.localization_rows(language))
            for key, value in titles.items():
                with self.subTest(language=language, key=key):
                    self.assertIn(f' {key}:0 "{value}"', loc)

        english_payload = gen.render_localization("english")
        for language in (
            "french",
            "german",
            "japanese",
            "korean",
            "polish",
            "russian",
            "spanish",
        ):
            with self.subTest(language=language):
                self.assertEqual(
                    gen.render_localization(language).replace(
                        f"l_{language}:".encode(), b"l_english:", 1
                    ),
                    english_payload,
                )

    def test_grade_reason_never_manufactures_role_mismatch(self) -> None:
        m181 = effect_block(self.effects, "zg361_pp_m181_core_effect")
        for token in (
            "zg361_pp_m181_primary_category value = 0",
            "zg361_pp_m181_triage_truth_status value = 0",
            "zg361_pp_m181_triage_red_code value = 2",
            "zg361_pp_m181_current_rating_unchanged value = 1",
        ):
            self.assertIn(token, m181)
        self.assertNotIn("zg361_pp_m181_primary_category value = 3", m181)
        self.assertNotIn("zg361_pp_m181_result_reason_snapshot = 5", m181)

        m189 = effect_block(self.effects, "zg361_pp_m189_core_effect")
        self.assertIn("var:zg361_pp_m181_primary_category = 3", m189)
        self.assertIn("var:zg361_pp_w_real_vacancy = 1", m189)
        self.assertIn("zg361_pp_m189_second_pip value = 1", m189)

    def test_pp_copy_has_authored_scenes_and_self_explanatory_buttons(self) -> None:
        rows = gen.localization_rows("simp_chinese")
        loc: dict[str, str] = {}
        for row in rows:
            match = re.match(r'^\s*([^:]+):\d+\s+"(.*)"$', row)
            if match:
                loc[match.group(1)] = match.group(2)

        self.assertEqual(set(gen.PP_SCENES), set(range(146, 192)))
        descriptions = []
        for mechanism in gen.MECHANISMS:
            mid = mechanism.mechanism_id
            title = loc[f"zg361pp.{mid}.t"]
            desc = loc[f"zg361pp.{mid}.desc"]
            descriptions.append(desc)
            self.assertNotIn(title, desc, f"{mid}: body repeats title")
            self.assertNotRegex(desc, r"^[。！？；：，、.?!;:,\[]")
            self.assertNotRegex(desc, r"路线[甲乙丙]|按\s*[ABC]\s*(?:做|办|执行)")
            self.assertNotRegex(
                desc,
                r"当前需要你回应|你只是在决定|下方按钮|按钮及说明|本卡|玩家|结算器|回写",
            )
            letters = (
                ("transfer", "second_pip", "b", "c")
                if mid == 189
                else (("b", "c") if mid == 166 else ("a", "b", "c"))
            )
            for letter in letters:
                label = loc[f"zg361pp.{mid}.{letter}"]
                tooltip = loc[f"zg361pp.{mid}.{letter}.tt"]
                self.assertLessEqual(len(label), 40, f"{mid}.{letter}: overlong label")
                self.assertNotRegex(label, r"路线[甲乙丙]|按\s*[ABC]\s*(?:做|办|执行)")
                self.assertNotRegex(label, r"^(?:按|选择)\s*[ABC甲乙丙]|^照做$")
                self.assertNotIn(label, desc, f"{mid}.{letter}: body copies the decision")
                self.assertNotIn(label, tooltip, f"{mid}.{letter}: tooltip repeats button")
                self.assertNotRegex(
                    tooltip,
                    r"未出现外部回执|政策参数|计划核验日|本卡|玩家|结算器|回写",
                    f"{mid}.{letter}: implementation-facing tooltip",
                )
                if mid == 189 and letter in {"transfer", "second_pip"}:
                    self.assertIn("错岗事实", tooltip)
                else:
                    self.assertRegex(tooltip, r"(?:立即入卷|暂缓)")
        self.assertEqual(len(descriptions), len(set(descriptions)))

        # Audit every visible PP body, not only the 46 manager cards.  A body
        # must begin with authored facts, never punctuation or a dynamic scope,
        # and must not fall back to implementation/UI instructions.
        visible_desc = {
            key: value for key, value in loc.items() if key.endswith(".desc")
        }
        self.assertEqual(len(visible_desc), 54)
        for key, desc in visible_desc.items():
            self.assertNotRegex(desc, r"^[。！？；：，、.?!;:,\[]", key)
            self.assertNotRegex(
                desc,
                r"当前需要你回应|你只是在决定|下方按钮|按钮及说明|本卡|玩家|结算器|回写",
                key,
            )

        event_body_keys = set(
            re.findall(r"\bdesc = (zg361pp\.[A-Za-z0-9_.]+)", self.events)
        )
        self.assertEqual(len(event_body_keys), 78)
        for key in event_body_keys:
            self.assertIn(key, loc)
            self.assertNotRegex(loc[key], r"^[。！？；：，、.?!;:,\[]", key)

        option_keys = set(
            re.findall(r"\bname = (zg361pp\.[A-Za-z0-9_.]+)", self.events)
        )
        self.assertEqual(len(option_keys), 152)
        for key in option_keys:
            self.assertIn(key, loc)
            self.assertNotRegex(
                loc[key],
                r"^(?:按|选择)\s*[ABC甲乙丙](?:做|办|执行)?(?:。)?$|^照做(?:。)?$",
                key,
            )

        title_body_pairs = [
            ("zg361pp.9100.t", "zg361pp.9100.desc"),
            ("zg361pp.5151.t", "zg361pp.5151.desc"),
            ("zg361pp.5166.t", "zg361pp.5166.desc"),
            ("zg361pp.5190.t", "zg361pp.5190.desc"),
            *((f"zg361pp.{mid}.t", f"zg361pp.{mid}.desc") for mid in range(146, 192)),
            *((f"zg361pp.{mid}.t", f"zg361pp.{mid}.desc") for mid in range(9001, 9005)),
        ]
        for title_key, body_key in title_body_pairs:
            self.assertNotIn(loc[title_key], loc[body_key], body_key)

        self.assertIn("送达回执与申诉时钟已经进入案卷", loc["zg361pp.151.desc"])
        self.assertIn("候选本人已经选择继续参评", loc["zg361pp.166.desc"])
        self.assertEqual(
            loc["zg361pp.5166.t"], "晋升包：请本人决定是否继续参评"
        )
        self.assertEqual(loc["zg361pp.5190.t"], "调任案卷：是否附上本人陈述")
        self.assertNotEqual(loc["zg361pp.166.t"], loc["zg361pp.5166.t"])
        self.assertNotEqual(loc["zg361pp.190.t"], loc["zg361pp.5190.t"])
        self.assertIn(
            "title = zg361pp.5166.t", effect_block(self.events, "zg361pp.5166")
        )
        self.assertIn(
            "title = zg361pp.5190.t", effect_block(self.events, "zg361pp.5190")
        )
        self.assertIn("披露回应已经进入案卷", loc["zg361pp.190.desc"])
        self.assertIn("确认岗位不匹配", loc["zg361pp.189.desc.transfer"])
        terminal = effect_block(self.events, "zg361pp.189")
        self.assertIn("desc = zg361pp.189.desc.transfer", terminal)
        self.assertIn("var:zg361_pp_m181_primary_category = 3", terminal)
        self.assertIn("var:zg361_pp_w_real_vacancy = 1", terminal)
        self.assertIn("撤回权只属于", loc["zg361pp.5166.desc"])
        self.assertIn("本人陈述尚未附卷", loc["zg361pp.5190.desc"])
        self.assertNotIn("告身已经送达", loc["zg361pp.5151.desc"])
        completion_desc = []
        completion_options = []
        for domain_index, domain in enumerate(gen.DOMAINS, start=1):
            event_id = 9000 + domain_index
            expected = gen.COMPLETION_COPY[domain.key]
            completion_desc.append(loc[f"zg361pp.{event_id}.desc"])
            completion_options.append(loc[f"zg361pp.{event_id}.a"])
            self.assertEqual(loc[f"zg361pp.{event_id}.desc"], expected[0])
            self.assertEqual(loc[f"zg361pp.{event_id}.a"], expected[2])
        self.assertEqual(len(set(completion_desc)), 4)
        self.assertEqual(len(set(completion_options)), 4)

        english_rows = gen.localization_rows("english")
        english = "\n".join(english_rows)
        for stale in (
            "has not yet chosen between receipt alone",
            "must personally decide whether to withdraw",
            "now decides whether to attach a personal statement",
            "The notice has been served",
            "This cycle's institutional choices are now in the file",
        ):
            self.assertNotIn(stale, english)
        english_loc: dict[str, str] = {}
        for row in english_rows:
            match = re.match(r'^\s*([^:]+):\d+\s+"(.*)"$', row)
            if match:
                english_loc[match.group(1)] = match.group(2)
        self.assertEqual(
            len({english_loc[f"zg361pp.{event_id}.desc"] for event_id in range(9001, 9005)}),
            4,
        )
        self.assertEqual(
            len({english_loc[f"zg361pp.{event_id}.a"] for event_id in range(9001, 9005)}),
            4,
        )

    def test_all_manager_options_expose_cost_and_deadline_tooltips(self) -> None:
        for mechanism in gen.MECHANISMS:
            event = effect_block(self.events, f"zg361pp.{mechanism.mechanism_id}")
            letters = (
                ("transfer", "second_pip", "b", "c")
                if mechanism.mechanism_id == 189
                else (("b", "c") if mechanism.mechanism_id == 166 else ("a", "b", "c"))
            )
            for letter in letters:
                self.assertIn(
                    f"custom_tooltip = zg361pp.{mechanism.mechanism_id}.{letter}.tt",
                    event,
                )

        chinese = "\n".join(gen.localization_rows("simp_chinese"))
        for mid, route in gen.DUAL_COST_ROUTE_BY_ID.items():
            letter = "a" if route == 1 else "b"
            match = re.search(
                rf'^\s*zg361pp\.{mid}\.{letter}\.tt:\d+\s+"(.*)"$',
                chinese,
                re.MULTILINE,
            )
            self.assertIsNotNone(match)
            self.assertIn("公帑五金", match.group(1))
            self.assertIn("私库五金", match.group(1))
            if mid == 191:
                self.assertIn("另收十金", match.group(1))
            else:
                self.assertIn("实收十金", match.group(1))
        self.assertIn("团队成本估算为三、二、零、五，合计十", chinese)
        self.assertIn("退出终态及其首笔十金离案补偿已经登记", chinese)
        self.assertIn("另行扣除直属上司公帑五金与私库五金", chinese)

    def test_provisional_cross_team_attribution_does_not_claim_missing_review(self) -> None:
        chinese = "\n".join(gen.localization_rows("simp_chinese"))
        english = "\n".join(gen.localization_rows("english"))
        self.assertIn("按候选四成、同伴六成建立待复核归因", chinese)
        self.assertIn("共签或独立复核仍待后续回执", chinese)
        self.assertNotIn("由原负责人共签或独立复核后", chinese)
        self.assertIn("cosignature or independent review still awaits a later receipt", english)

    def test_delivery_uses_readable_reason_text_and_completion_is_not_closed(self) -> None:
        event = effect_block(self.events, "zg361pp.5151")
        self.assertEqual(set(gen.RESULT_REASON_TEXT), set(range(11)))
        for reason in range(11):
            self.assertIn(f"var:zg361_pp_t_frozen_reason = {reason}", event)
            self.assertIn(f"desc = zg361pp.5151.reason.{reason}", event)
        self.assertIn("desc = zg361pp.5151.reason.unknown", event)
        self.assertIn("desc = zg361pp.5151.evidence", event)

        chinese = "\n".join(gen.localization_rows("simp_chinese"))
        self.assertNotIn("冻结理由编号", chinese)
        self.assertIn("强制分布配额将其下调。这不构成错岗证据", chinese)
        self.assertNotIn("三六一案卷已结", chinese)
        self.assertIn("本轮选择已录入", chinese)

    def test_numeric_localization_uses_character_root_variable_values(self) -> None:
        expected_variables = (
            "zg361_pp_t_frozen_kpi",
            "zg361_pp_t_frozen_rank",
            "zg361_pp_t_evidence_component_count",
        )
        for language in gen.LANGUAGES:
            source = text(
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_feedback_promotion_pip_l_{language}.yml"
            )
            self.assertNotRegex(
                source,
                r"ROOT(?:\.Char)?\.MakeScope\.Var\('[^']+'\)\.GetValue",
                language,
            )
            for variable in expected_variables:
                self.assertIn(
                    f"[ROOT.Var('{variable}').GetValue|0]",
                    source,
                    language,
                )
        generated = "\n".join(gen.localization_rows("english"))
        self.assertEqual(generated.count("[ROOT.Var('"), len(expected_variables))

    def test_character_saved_scope_localization_uses_direct_saved_scope_names(self) -> None:
        expected_saved_scopes = (
            "zg361_pp_prompt_owner",
            "zg361_pp_prompt_subject",
            "zg361_pp_subject_prompt_owner",
            "zg361_pp_subject_prompt_subject",
        )
        for language in gen.LANGUAGES:
            source = text(
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_feedback_promotion_pip_l_{language}.yml"
            )
            self.assertNotRegex(
                source,
                r"\[scope:[A-Za-z0-9_]+(?:\.Char)?\.GetShortUIName\]",
                language,
            )
            for saved_scope in expected_saved_scopes:
                self.assertIn(
                    f"[{saved_scope}.GetShortUIName]",
                    source,
                    language,
                )
                self.assertNotIn(
                    f"[{saved_scope}.Char.GetShortUIName]",
                    source,
                    language,
                )

        generated = "\n".join(gen.localization_rows("english"))
        self.assertNotIn("[scope:", generated)

    def test_events_and_effects_have_balanced_braces(self) -> None:
        self.assertEqual(self.effects.count("{"), self.effects.count("}"))
        self.assertEqual(self.events.count("{"), self.events.count("}"))

    def test_all_outputs_have_bom_and_only_owned_paths(self) -> None:
        outputs = gen.outputs()
        self.assertEqual(len(outputs), 10 + len(gen.EFFECT_GROUPS))
        self.assertTrue(all(payload.startswith(gen.BOM) for payload in outputs.values()))
        self.assertTrue(all("gui" not in path.parts for path in outputs))
        self.assertTrue(all("zg361_feedback_promotion_pip" in path.name for path in outputs))

    def test_chinese_and_english_are_authored_and_seven_are_placeholders(self) -> None:
        english = text(MOD_ROOT / "localization" / "english" / "zg361_feedback_promotion_pip_l_english.yml")
        chinese = text(MOD_ROOT / "localization" / "simp_chinese" / "zg361_feedback_promotion_pip_l_simp_chinese.yml")
        self.assertIn("State the rating or soften the wording", english)
        self.assertIn("直报档位还是委婉转述", chinese)
        self.assertNotEqual(english.replace("l_english:", "", 1), chinese.replace("l_simp_chinese:", "", 1))
        for language in ("french", "german", "japanese", "korean", "polish", "russian", "spanish"):
            placeholder = text(
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_feedback_promotion_pip_l_{language}.yml"
            )
            self.assertEqual(
                placeholder.replace(f"l_{language}:", "", 1),
                english.replace("l_english:", "", 1),
            )

    def test_subject_owned_166_and_split_189_have_no_dead_generic_a_localization(self) -> None:
        for mid in (166, 189):
            mechanism = gen.MECHANISM_BY_ID[mid]
            self.assertIsNone(mechanism.a_cn)
            self.assertIsNone(mechanism.a_en)

        m166 = effect_block(self.events, "zg361pp.166")
        self.assertNotIn("name = zg361pp.166.a", m166)
        self.assertNotIn("custom_tooltip = zg361pp.166.a.tt", m166)
        self.assertIn("name = zg361pp.166.b", m166)
        self.assertIn("name = zg361pp.166.c", m166)

        event = effect_block(self.events, "zg361pp.189")
        self.assertNotIn("name = zg361pp.189.a", event)
        self.assertNotIn("custom_tooltip = zg361pp.189.a.tt", event)
        for expected in ("transfer", "second_pip", "b", "c"):
            self.assertIn(f"name = zg361pp.189.{expected}", event)
            self.assertIn(f"custom_tooltip = zg361pp.189.{expected}.tt", event)

        dead_keys = (
            "zg361pp.166.a",
            "zg361pp.166.a.tt",
            "zg361pp.189.a",
            "zg361pp.189.a.tt",
        )
        live_split_keys = (
            "zg361pp.189.transfer",
            "zg361pp.189.transfer.tt",
            "zg361pp.189.second_pip",
            "zg361pp.189.second_pip.tt",
        )
        for language in gen.LANGUAGES:
            source = text(
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_feedback_promotion_pip_l_{language}.yml"
            )
            keys = set(
                re.findall(r"^\s+([^\s:]+):\d+\s+\"", source, re.MULTILINE)
            )
            self.assertTrue(set(dead_keys).isdisjoint(keys), language)
            self.assertTrue(set(live_split_keys) <= keys, language)

    def test_generator_is_deterministic_and_all_nine_loc_keysets_match(self) -> None:
        first = gen.outputs()
        second = gen.outputs()
        self.assertEqual(first, second)
        self.assertTrue(all(payload.startswith(gen.BOM) for payload in first.values()))
        keysets: dict[str, set[str]] = {}
        for language in gen.LANGUAGES:
            source = text(
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_feedback_promotion_pip_l_{language}.yml"
            )
            keysets[language] = set(re.findall(r"^\s+([^\s:]+):\d+\s+\"", source, re.MULTILINE))
        self.assertTrue(keysets["english"])
        self.assertTrue(all(keys == keysets["english"] for keys in keysets.values()))

    def test_generator_check_is_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOLS / "gen_361_feedback_promotion_pip_runtime.py"), "--check"],
            cwd=MOD_ROOT.parent,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GREEN", result.stdout)

    def test_generator_check_rejects_legacy_effect_monolith(self) -> None:
        legacy = (
            MOD_ROOT
            / "common"
            / "scripted_effects"
            / gen.LEGACY_EFFECT_FILENAME
        )
        self.assertFalse(legacy.exists())
        try:
            legacy.write_bytes(gen.render_effects())
            result = subprocess.run(
                [
                    sys.executable,
                    str(TOOLS / "gen_361_feedback_promotion_pip_runtime.py"),
                    "--check",
                ],
                cwd=MOD_ROOT.parent,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("legacy monolith", result.stdout)
        finally:
            legacy.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()

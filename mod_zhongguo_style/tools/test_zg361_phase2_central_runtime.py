#!/usr/bin/env python3
"""Static contracts for the phase-two central serial dispatcher.

These tests prove generated source structure only.  They are not CK3 parser,
MCP, fixture-live, production-live, save/load, or release evidence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_phase2_central_runtime as generator
import gen_361_workforce_endgame_runtime as workforce_generator


MOD_ROOT = generator.MOD_ROOT


def read(relative: str) -> str:
    return (MOD_ROOT / relative).read_text(encoding="utf-8-sig")


def read_workforce_effect_shards() -> str:
    return "\n".join(
        read(f"common/scripted_effects/{group.filename}")
        for group in workforce_generator.EFFECT_GROUPS
    )


def read_central_effect_shards() -> str:
    return "\n".join(
        read(f"common/scripted_effects/{group.filename}")
        for group in generator.EFFECT_GROUPS
    )


def read_central_event_shards() -> str:
    return "\n".join(
        read(f"events/{group.filename}")
        for group in generator.EVENT_GROUPS
    )


def block(text: str, key: str) -> str:
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
                test.assertGreaterEqual(depth, 0, f"{label}:{line_number}: extra close")
    test.assertFalse(quoted, f"{label}: unterminated quote")
    test.assertEqual(depth, 0, f"{label}: brace imbalance")


class Phase2CentralRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read_central_effect_shards()
        cls.triggers = read("common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt")
        cls.events = read_central_event_shards()
        cls.core = read("common/scripted_effects/zg361_effects.txt")
        cls.b1 = "\n".join(
            read(f"common/scripted_effects/{filename}")
            for filename in (
                "zg361_b1_runtime_effects.txt",
                "zg361_b1_runtime_effects_part2.txt",
            )
        )
        cls.workforce = read_workforce_effect_shards()
        cls.spec = read("docs/361-phase2-central-runtime-spec.md")

    def test_stage_inventory_and_public_abis_are_exact(self) -> None:
        self.assertEqual(tuple(stage for stage, _, _ in generator.STAGES), tuple(range(1, 12)))
        self.assertEqual(len(generator.STAGES), 11)
        self.assertEqual(len({name for _, _, name in generator.STAGES}), 11)
        for _, _, opener in generator.STAGES:
            self.assertIn(opener, self.effects)
        self.assertNotIn("zg361_ip_open_portfolio_effect = yes", self.effects)

    def test_outputs_are_current_bom_and_isolated(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(len(rendered), 23)
        allowed = {
            *{
                f"common/scripted_effects/{group.filename}"
                for group in generator.EFFECT_GROUPS
            },
            "common/scripted_triggers/zg361_phase2_central_runtime_triggers.txt",
            *{f"events/{group.filename}" for group in generator.EVENT_GROUPS},
            "docs/361-phase2-central-runtime-spec.md",
            *{
                f"localization/{language}/zg361_phase2_central_l_{language}.yml"
                for language, _ in generator.LANGUAGES
            },
        }
        self.assertEqual({path.relative_to(MOD_ROOT).as_posix() for path in rendered}, allowed)
        for path, content in rendered.items():
            expected = generator.BOM + content.replace("\r\n", "\n").encode("utf-8")
            self.assertEqual(path.read_bytes(), expected, path)
            self.assertTrue(path.read_bytes().startswith(generator.BOM), path)

    def test_effect_aggregate_baseline_is_frozen(self) -> None:
        payload = generator.historical_effect_payload()
        self.assertEqual(generator.HISTORICAL_EFFECT_BYTES, len(payload))
        self.assertEqual(
            generator.HISTORICAL_EFFECT_SHA256,
            hashlib.sha256(payload).hexdigest().upper(),
        )
        self.assertEqual(
            generator.HISTORICAL_EFFECT_COUNT,
            len(generator.top_level_effect_blocks(payload)),
        )

    def test_effect_shards_are_exact_unique_block_projection(self) -> None:
        source_blocks = generator.top_level_effect_blocks(generator.render_effects())
        parts = generator.render_effect_parts()
        projected_blocks = tuple(
            block_row
            for group in generator.EFFECT_GROUPS
            for block_row in generator.top_level_effect_blocks(parts[group.filename])
        )
        self.assertEqual(source_blocks, projected_blocks)
        self.assertEqual(32, len(projected_blocks))
        self.assertEqual(32, len({name for name, _body in projected_blocks}))

    def test_effect_shards_obey_purpose_and_size_contract(self) -> None:
        self.assertEqual(10, len(generator.EFFECT_GROUPS))
        self.assertEqual({}, generator.EFFECT_HARD_LIMIT_EXCEPTIONS)
        for group in generator.EFFECT_GROUPS:
            with self.subTest(filename=group.filename):
                count = len(group.effect_names)
                self.assertGreaterEqual(count, 1)
                self.assertLessEqual(count, generator.EFFECT_TARGET_MAX)
                self.assertLessEqual(count, generator.EFFECT_HARD_MAX)
                payload = (
                    MOD_ROOT / "common" / "scripted_effects" / group.filename
                ).read_bytes()
                self.assertTrue(payload.startswith(generator.BOM))
                text = payload.decode("utf-8-sig")
                self.assertTrue(text.startswith(generator.HEADER))
                self.assertIn(f"# PURPOSE: {group.purpose}.", text)
                self.assertEqual(
                    count,
                    len(generator.top_level_effect_blocks(payload)),
                )

    def test_effect_hard_limit_exception_contract_keeps_11_to_20_reachable(self) -> None:
        source = generator.render_effects()
        source_blocks = generator.top_level_effect_blocks(source)
        names = tuple(name for name, _body in source_blocks)

        def groups(sizes: tuple[int, ...]) -> tuple[generator.EffectGroup, ...]:
            result: list[generator.EffectGroup] = []
            offset = 0
            for index, size in enumerate(sizes):
                result.append(
                    generator.EffectGroup(
                        f"synthetic_{index}_effects.txt",
                        f"synthetic purpose {index}",
                        names[offset : offset + size],
                    )
                )
                offset += size
            self.assertEqual(len(names), offset)
            return tuple(result)

        target_overages = groups((11, 11, 10))
        with (
            mock.patch.object(generator, "EFFECT_GROUPS", target_overages),
            mock.patch.object(generator, "EFFECT_HARD_LIMIT_EXCEPTIONS", {}),
        ):
            generator._validate_effect_groups(source, source_blocks)

        hard_overage = groups((21, 11))
        oversized_filename = hard_overage[0].filename
        with (
            mock.patch.object(generator, "EFFECT_GROUPS", hard_overage),
            mock.patch.object(generator, "EFFECT_HARD_LIMIT_EXCEPTIONS", {}),
            self.assertRaisesRegex(ValueError, "must exactly match"),
        ):
            generator._validate_effect_groups(source, source_blocks)

        valid_exception = {
            oversized_filename: (
                "one indivisible purpose boundary",
                "artifacts/ck3-live/report.json",
            )
        }
        with (
            mock.patch.object(generator, "EFFECT_GROUPS", hard_overage),
            mock.patch.object(
                generator,
                "EFFECT_HARD_LIMIT_EXCEPTIONS",
                valid_exception,
            ),
        ):
            generator._validate_effect_groups(source, source_blocks)

        empty_evidence = {
            oversized_filename: ("one indivisible purpose boundary", "")
        }
        with (
            mock.patch.object(generator, "EFFECT_GROUPS", hard_overage),
            mock.patch.object(
                generator,
                "EFFECT_HARD_LIMIT_EXCEPTIONS",
                empty_evidence,
            ),
            self.assertRaisesRegex(ValueError, "without reason and CK3 live evidence"),
        ):
            generator._validate_effect_groups(source, source_blocks)

    def test_event_aggregate_baseline_is_frozen(self) -> None:
        payload = generator.historical_event_payload()
        self.assertEqual(generator.HISTORICAL_EVENT_BYTES, len(payload))
        self.assertEqual(
            generator.HISTORICAL_EVENT_SHA256,
            hashlib.sha256(payload).hexdigest().upper(),
        )
        self.assertEqual(
            generator.HISTORICAL_EVENT_COUNT,
            len(generator.top_level_effect_blocks(payload)),
        )

    def test_event_shards_are_exact_purpose_projection(self) -> None:
        source_blocks = generator.top_level_effect_blocks(generator.render_events())
        parts = generator.render_event_parts()
        projected_blocks = tuple(
            block_row
            for group in generator.EVENT_GROUPS
            for block_row in generator.top_level_effect_blocks(parts[group.filename])
        )
        self.assertEqual(source_blocks, projected_blocks)
        self.assertEqual(
            ("zg361p2c.1", "zg361p2c.2", "zg361p2c.3"),
            generator.EVENT_GROUPS[0].event_names,
        )
        self.assertEqual(
            ("zg361p2c.4", "zg361p2c.5", "zg361p2c.6"),
            generator.EVENT_GROUPS[1].event_names,
        )
        for group in generator.EVENT_GROUPS:
            with self.subTest(filename=group.filename):
                self.assertLessEqual(len(group.event_names), 10)
                payload = (
                    MOD_ROOT / "events" / group.filename
                ).read_bytes()
                self.assertTrue(payload.startswith(generator.BOM))
                text = payload.decode("utf-8-sig")
                self.assertIn("namespace = zg361p2c", text)
                self.assertIn(f"# PURPOSE: {group.purpose}.", text)
                self.assertEqual(
                    len(group.event_names),
                    len(generator.top_level_effect_blocks(payload)),
                )

    def test_legacy_monoliths_are_absent(self) -> None:
        self.assertFalse(generator.LEGACY_EFFECT_PATH.exists())
        self.assertFalse(generator.LEGACY_EVENT_PATH.exists())
        self.assertEqual((), generator.unexpected_effect_paths(generator.outputs()))
        self.assertEqual((), generator.unexpected_event_paths(generator.outputs()))

    def test_generated_script_braces_and_event_namespace(self) -> None:
        assert_balanced(self, self.effects, "central effects")
        assert_balanced(self, self.triggers, "central triggers")
        assert_balanced(self, self.events, "central events")
        self.assertIn("namespace = zg361p2c", self.events)
        self.assertEqual(len(re.findall(r"(?m)^zg361p2c\.\d+\s*=", self.events)), 6)

    def test_publish_hook_is_after_b1_publish_and_flag_clear(self) -> None:
        annual = block(self.core, "zg361_apply_pending_grades_effect")
        published = annual.index("zg361_b1_mark_published_effect = yes")
        cleared = annual.index("remove_character_flag = zg361_review_in_progress", published)
        central = annual.index("zg361_p2c_on_review_published_effect = yes", cleared)
        self.assertLess(published, cleared)
        self.assertLess(cleared, central)
        self.assertNotIn("zg361_p2c_", block(self.b1, "zg361_b1_open_cycle_effect"))

    def test_delivery_hook_is_after_state_receipt_and_b2_delivery(self) -> None:
        settle = block(self.core, "zg361_settle_delivered_325_effect")
        state = settle.index("var:zg361_result_case_state = 3")
        receipt = settle.index("set_variable = { name = zg361_result_settlement_posted_serial")
        b2 = settle.index("zg361_b2_on_notice_delivered_effect = yes")
        central = settle.index("zg361_p2c_on_result_delivered_effect = yes")
        self.assertLess(state, receipt)
        self.assertLess(receipt, b2)
        self.assertLess(b2, central)

    def test_publish_initializes_only_and_defers_first_adapter_d2(self) -> None:
        hook = block(self.effects, "zg361_p2c_on_review_published_effect")
        self.assertIn("var:zg361_b1_cycle_state = 8", hook)
        self.assertIn("var:zg361_b1_closure_state = 4", hook)
        self.assertIn("position = 0", hook)
        self.assertIn("order_by = stewardship", hook)
        self.assertIn("zg361_p2c_schedule_pump_effect = { DAYS = 2 }", hook)
        for _, _, opener in generator.STAGES:
            self.assertNotIn(f"{opener} =", hook)

    def test_m013_publication_proofs_are_mode_selected_and_cannot_mix(self) -> None:
        hook = block(self.effects, "zg361_p2c_on_review_published_effect")
        exact_guard = """            OR = {
                AND = {
                    has_variable = zg361_b1_m013_mode
                    var:zg361_b1_m013_mode != 3
                    has_variable = zg361_b1_m013_receipt_serial
                    var:zg361_b1_m013_receipt_serial = var:zg361_b1_case_serial
                }
                AND = {
                    has_variable = zg361_b1_m013_mode
                    var:zg361_b1_m013_mode = 3
                    has_variable = zg361_b1_m013_policy_debt_serial
                    var:zg361_b1_m013_policy_debt_serial = var:zg361_b1_case_serial
                }
            }"""
        self.assertEqual(hook.count(exact_guard), 1)

        # Truth-table counterexamples for the exact generated guard: neither
        # proof may borrow the other route's current-case marker.
        accepts = lambda mode, receipt_current, debt_current: mode is not None and (
            (mode != 3 and receipt_current) or (mode == 3 and debt_current)
        )
        self.assertTrue(accepts(1, True, False))
        self.assertTrue(accepts(3, False, True))
        self.assertFalse(accepts(3, True, False))
        self.assertFalse(accepts(1, False, True))
        self.assertFalse(accepts(None, True, True))
        self.assertTrue(accepts(3, True, True))  # accepted by debt, never by receipt

    def test_manager_and_subject_permission_boundary(self) -> None:
        hook = block(self.effects, "zg361_p2c_on_review_published_effect")
        pump = block(self.effects, "zg361_p2c_pump_effect")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", hook)
        self.assertIn("zg361_is_celestial_liege_trigger = yes", pump)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", hook)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", pump)
        self.assertNotIn("is_ai = no", hook)
        stage11 = block(self.effects, "zg361_p2c_stage_11_workforce_endgame_effect")
        self.assertNotIn("$SUBJECT$ = { zg361_is_celestial_liege_trigger", stage11)
        self.assertIn("count/baron", self.spec)
        self.assertIn("公爵及以上", self.spec)

    def test_frozen_five_tuple_and_primary_stale_abort(self) -> None:
        hook = block(self.effects, "zg361_p2c_on_review_published_effect")
        for token in (
            "zg361_p2c_b1_owner",
            "zg361_p2c_b1_cycle",
            "zg361_p2c_b1_case",
            "zg361_p2c_subject",
            "zg361_p2c_result_owner",
            "zg361_p2c_result_subject",
            "zg361_p2c_result_cycle",
            "zg361_p2c_result_case",
        ):
            self.assertIn(token, hook)
        pump = block(self.effects, "zg361_p2c_pump_effect")
        self.assertIn("zg361_p2c_abort_stale_effect = { CODE = 9001 }", pump)
        abort = block(self.effects, "zg361_p2c_abort_stale_effect")
        self.assertIn("zg361_p2c_terminal_state value = 4", abort)
        self.assertNotIn("ordered_vassal", abort)

    def test_new_cycle_aborts_old_active_tuple_before_reinitializing(self) -> None:
        hook = block(self.effects, "zg361_p2c_on_review_published_effect")
        abort = hook.index("zg361_p2c_abort_stale_effect = { CODE = 9101 }")
        initialize = hook.index("set_variable = { name = zg361_p2c_started_cycle")
        self.assertLess(abort, initialize)
        self.assertIn("NOT = { var:zg361_p2c_cycle = var:zg361_review_serial }", hook[:initialize])
        self.assertIn("var:zg361_p2c_active = 0", hook)
        self.assertIn("zg361_p2c_deferred_reinit value = 1", hook)
        self.assertIn("trigger_event = { id = zg361p2c.3 days = 2 }", hook)
        deferred = block(self.events, "zg361p2c.3")
        self.assertIn("hidden = yes", deferred)
        self.assertIn("var:zg361_review_serial = var:zg361_p2c_deferred_reinit_cycle", deferred)
        self.assertIn("zg361_p2c_on_review_published_effect = yes", deferred)

    def test_delayed_ticket_is_exact_and_replay_is_noop(self) -> None:
        schedule = block(self.effects, "zg361_p2c_schedule_pump_effect")
        for token in (
            "zg361_p2c_ticket_manager",
            "zg361_p2c_ticket_cycle",
            "zg361_p2c_ticket_case",
            "zg361_p2c_ticket_stage",
            "zg361_p2c_ticket_identity",
        ):
            self.assertIn(token, schedule)
        poll = block(self.events, "zg361p2c.1")
        self.assertIn("hidden = yes", poll)
        self.assertIn("this = scope:zg361_p2c_ticket_manager", poll)
        self.assertIn("var:zg361_p2c_ticket_serial = scope:zg361_p2c_ticket_identity", poll)
        stale = poll.split("else =", 1)[1]
        self.assertNotIn("set_variable", stale)
        self.assertNotIn("change_variable", stale)

    def test_exact_325_wake_has_no_authority_or_business_opener(self) -> None:
        wake = block(self.effects, "zg361_p2c_on_result_delivered_effect")
        self.assertIn("var:zg361_result_case_state = 3", wake)
        self.assertIn("var:zg361_p2c_subject = scope:zg361_p2c_delivered_subject", wake)
        self.assertIn("var:zg361_p2c_result_case = scope:zg361_p2c_delivered_subject.var:zg361_result_case_serial", wake)
        self.assertIn("OR = { var:zg361_p2c_stage = 2 var:zg361_p2c_stage = 7 }", wake)
        self.assertIn("var:zg361_p2c_wait_reason = 325", wake)
        for _, _, opener in generator.STAGES:
            self.assertNotIn(opener, wake)

    def test_one_stage_and_at_most_one_opener_per_pump(self) -> None:
        pump = block(self.effects, "zg361_p2c_pump_effect")
        for stage in range(1, 12):
            self.assertEqual(
                len(re.findall(rf"var:zg361_p2c_stage = {stage}(?!\d)", pump)),
                1,
            )
        self.assertGreaterEqual(pump.count("else_if ="), 11)
        opener_names = [name for _, _, name in generator.STAGES]
        stage_keys = (
            "zg361_p2c_stage_01_career_hc_effect",
            "zg361_p2c_stage_02_compensation_effect",
            "zg361_p2c_stage_03_feedback_promotion_pip_effect",
            "zg361_p2c_stage_04_x_effect",
            "zg361_p2c_stage_05_y_effect",
            "zg361_p2c_stage_06_z_effect",
            "zg361_p2c_stage_07_metrics_delivery_effect",
            "zg361_p2c_stage_08_credit_project_effect",
            "zg361_p2c_stage_09_career_learning_effect",
            "zg361_p2c_stage_10_manager_governance_effect",
            "zg361_p2c_stage_11_workforce_endgame_effect",
        )
        for key in stage_keys:
            body = block(self.effects, key)
            calls = sum(body.count(f"{opener} =") for opener in opener_names)
            self.assertLessEqual(calls, 1, key)

    def test_compensation_and_pp_repeat_without_window_flood(self) -> None:
        comp = block(self.effects, "zg361_p2c_stage_02_compensation_effect")
        self.assertIn("zg361_comp_portfolio_completed_cycle", comp)
        self.assertIn("has_character_flag = zg361_comp_portfolio_active", comp)
        self.assertEqual(comp.count("zg361_p2c_call_compensation_adapter_effect = yes"), 1)
        self.assertIn("zg361_p2c_result_case", comp)
        comp_preflight = block(self.effects, "zg361_p2c_call_compensation_adapter_effect")
        self.assertEqual(comp_preflight.count("zg361_comp_portfolio_open_next_effect = yes"), 2)
        self.assertIn("var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject", comp_preflight)
        pp = block(self.effects, "zg361_p2c_stage_03_feedback_promotion_pip_effect")
        for domain in "tuvw":
            self.assertIn(f"zg361_pp_{domain}_portfolio_done_cycle", pp)
        self.assertIn("zg361_pp_portfolio_queue_active", pp)
        self.assertEqual(pp.count("zg361_p2c_call_pp_adapter_effect = yes"), 1)
        pp_preflight = block(self.effects, "zg361_p2c_call_pp_adapter_effect")
        self.assertEqual(pp_preflight.count("zg361_pp_manager_portfolio_adapter_effect = yes"), 1)
        self.assertIn("var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject", pp_preflight)
        career_preflight = block(self.effects, "zg361_p2c_call_career_hc_adapter_effect")
        self.assertEqual(career_preflight.count("zg361_career_hc_open_portfolio_effect = yes"), 1)
        self.assertIn("var:zg361_p2c_adapter_candidate = var:zg361_p2c_subject", career_preflight)

    def test_incident_is_strict_x_y_z_and_never_all_domain(self) -> None:
        pump = block(self.effects, "zg361_p2c_pump_effect")
        positions = [pump.index(f"zg361_p2c_stage_0{stage}_{domain}_effect") for stage, domain in ((4, "x"), (5, "y"), (6, "z"))]
        self.assertEqual(positions, sorted(positions))
        for stage, domain, terminal in ((4, "x", 8), (5, "y", 6), (6, "z", 6)):
            body = block(self.effects, f"zg361_p2c_stage_0{stage}_{domain}_effect")
            self.assertEqual(body.count(f"zg361_ip_open_{domain}_case_effect ="), 1)
            self.assertIn(f"var:zg361_ip_{domain}_final_state = {terminal}", body)
            self.assertIn(f"var:zg361_ip_{domain}_final_applicable = 1", body)
            self.assertIn(f"var:zg361_ip_{domain}_final_incident_serial > 0", body)
            self.assertIn(f"var:zg361_ip_{domain}_final_source_kind > 0", body)
            self.assertIn(f"var:zg361_ip_{domain}_final_consequence_kind > 0", body)
            self.assertIn(f"var:zg361_ip_{domain}_final_kpi_staged = 1", body)
            self.assertNotIn("zg361_ip_open_portfolio_effect", body)

    def test_incident_na_requires_the_full_zero_probe_and_receipt_tuple(self) -> None:
        for stage, domain in ((4, "x"), (5, "y"), (6, "z")):
            body = block(self.effects, f"zg361_p2c_stage_0{stage}_{domain}_effect")
            for token in (
                f"has_variable = zg361_ip_{domain}_final_na_owner",
                f"has_variable = zg361_ip_{domain}_final_na_subject",
                f"has_variable = zg361_ip_{domain}_final_na_cycle",
                f"has_variable = zg361_ip_{domain}_final_na_probe_serial",
                f"has_variable = zg361_ip_{domain}_final_na_receipt",
                f"has_variable = zg361_ip_{domain}_na_receipt_serial",
                f"var:zg361_ip_{domain}_final_applicable = 0",
                f"var:zg361_ip_{domain}_final_na_owner = root",
                f"var:zg361_ip_{domain}_final_na_subject = this",
                f"var:zg361_ip_{domain}_final_na_cycle = root.var:zg361_p2c_cycle",
                f"var:zg361_ip_{domain}_final_na_reason = 1",
                f"var:zg361_ip_{domain}_final_na_probe_serial = var:zg361_ip_probe_serial",
                f"var:zg361_ip_{domain}_final_na_receipt = var:zg361_ip_{domain}_na_receipt_serial",
                f"var:zg361_ip_{domain}_final_na_probe_serial > 0",
                f"var:zg361_ip_{domain}_final_na_receipt > 0",
                f"var:zg361_ip_{domain}_na_receipt_serial > 0",
                "var:zg361_ip_probe_result = 0",
                "var:zg361_ip_probe_source_kind = 0",
                "var:zg361_ip_probe_consequence_kind = 0",
                "var:zg361_ip_probe_serial > 0",
            ):
                self.assertIn(token, body, (stage, token))
            self.assertGreaterEqual(body.count("STATUS = 3"), 2)

        # Contract truth table: neither missing evidence nor an arbitrary zero
        # can be promoted to N/A. Only a complete, identity-bound zero probe is.
        required = {
            "applicable", "owner", "subject", "cycle", "reason",
            "probe_serial", "receipt", "receipt_serial", "probe_owner",
            "probe_subject", "probe_cycle", "probe_result", "source",
            "consequence",
        }
        accepts = lambda present, applicable, result, source, consequence, serial: (
            present == required
            and applicable == 0
            and result == source == consequence == 0
            and serial > 0
        )
        self.assertTrue(accepts(required, 0, 0, 0, 0, 1))
        self.assertFalse(accepts(required - {"receipt"}, 0, 0, 0, 0, 1))
        self.assertFalse(accepts(required, 1, 0, 0, 0, 1))
        self.assertFalse(accepts(required, 0, 1, 0, 0, 1))
        self.assertFalse(accepts(required, 0, 0, 1, 0, 1))
        self.assertFalse(accepts(required, 0, 0, 0, 0, 0))

    def test_p3_and_compensation_wait_for_delivered_result(self) -> None:
        for key in (
            "zg361_p2c_stage_02_compensation_effect",
            "zg361_p2c_stage_07_metrics_delivery_effect",
        ):
            body = block(self.effects, key)
            self.assertIn("OR = { var:zg361_result_case_state = 1 var:zg361_result_case_state = 2 }", body)
            self.assertIn("REASON = 325", body)
            self.assertIn("var:zg361_result_case_state >= 3", body)

    def test_cp_na_cl_digest_and_mg_strict_lag(self) -> None:
        cp = block(self.effects, "zg361_p2c_stage_08_credit_project_effect")
        self.assertIn("NOR =", cp)
        self.assertIn("NOT = { this = root.var:zg361_p2c_subject }", cp)
        self.assertIn("liege = { zg361_is_celestial_liege_trigger = yes }", cp)
        self.assertIn("STATUS = 3", cp)
        cl = block(self.effects, "zg361_p2c_stage_09_career_learning_effect")
        self.assertIn("zg361_cl_portfolio_ah_expected", cl)
        self.assertIn("zg361_cl_portfolio_ai_completed", cl)
        self.assertIn("NOT = { has_variable = zg361_cl_digest_pending }", cl)
        self.assertIn("zg361_p2c_cl_subjects", cl)
        self.assertIn("var:zg361_cl_portfolio_ah_expected = var:zg361_p2c_cl_frozen_count", cl)
        self.assertIn("var:zg361_cl_portfolio_ai_expected = var:zg361_p2c_cl_frozen_count", cl)
        self.assertIn("zg361_p2c_cl_partial_open", cl)
        self.assertIn("CODE = 910", cl)
        mg = block(self.effects, "zg361_p2c_stage_10_manager_governance_effect")
        self.assertIn("var:zg361_review_serial < root.var:zg361_p2c_cycle", mg)
        self.assertIn("zg361_p2c_mg_subjects", mg)
        self.assertIn("var:zg361_case_f_state = 5", mg)
        self.assertIn("var:zg361_case_ak_state = 6", mg)
        self.assertIn("var:zg361_p2c_mg_expected = 0", mg)
        self.assertIn("STATUS = 3", mg)
        self.assertIn("zg361_p2c_mg_started", mg)
        self.assertIn("zg361_p2c_mg_active", mg)
        self.assertIn("zg361_p2c_mg_open_failed", mg)
        self.assertIn("CODE = 1011", mg)

    def test_m360_stage10_freezes_ordered_manager_identity(self) -> None:
        mg = block(self.effects, "zg361_p2c_stage_10_manager_governance_effect")
        for token in (
            "zg361_p2c_mg_frozen_order_cursor",
            "zg361_p2c_mg_frozen_owner value = root",
            "zg361_p2c_mg_frozen_cycle value = root.var:zg361_p2c_cycle",
            "zg361_p2c_mg_frozen_case value = root.var:zg361_p2c_case_serial",
            "zg361_p2c_mg_frozen_order value = root.var:zg361_p2c_mg_frozen_order_cursor",
        ):
            self.assertIn(token, mg)

    def test_m360_candidate_requires_exact_b1_and_mg_sources(self) -> None:
        ready = block(self.triggers, "zg361_p2c_m360_candidate_ready_trigger")
        for token in (
            "var:zg361_b1_m360_source_status = 1",
            "var:zg361_b1_m360_source_available = 1",
            "var:zg361_b1_m360_source_sealed = 1",
            "var:zg361_b1_m360_source_id > 0",
            "var:zg361_b1_m360_source_hash > 0",
            "var:zg361_b1_m360_source_forced_count = var:zg361_b1_m360_source_quota",
            "var:zg361_mg_team_snapshot_owner = $EXPECTED_OWNER$",
            "var:zg361_mg_snapshot_source_serial = var:zg361_b1_m360_source_cycle",
            "var:zg361_mg_team_n = var:zg361_b1_m360_source_member_count",
            "var:zg361_mg_team_bottom_n = var:zg361_b1_m360_source_quota",
            "var:zg361_mg_m036_receipt_state = 4",
        ):
            self.assertIn(token, ready)
        for slot in range(1, 7):
            self.assertIn(f"var:zg361_b1_m360_source_quota >= {slot}", ready)
            self.assertIn(f"zg361_b1_m360_source_forced_{slot}_m357_receipt_id > 0", ready)
            self.assertIn(f"zg361_b1_m360_source_forced_{slot}_m357_receipt_hash > 0", ready)

    def test_m360_source_diagnostics_are_wait_na_red_not_interchangeable(self) -> None:
        prepare = block(self.effects, "zg361_p2c_prepare_m360_source_effect")
        self.assertIn("var:zg361_b1_m360_source_status = 3", prepare)
        self.assertIn("zg361_p2c_m360_probe_invalid_n add = 1", prepare)
        self.assertIn("var:zg361_b1_m360_source_status = 2", prepare)
        self.assertIn("zg361_p2c_m360_probe_structural_na_n add = 1", prepare)
        self.assertIn("var:zg361_p2c_m360_probe_wait_n > 0", prepare)
        self.assertIn("zg361_p2c_m360_source_status value = 5", prepare)
        self.assertIn("zg361_p2c_m360_source_status value = 7", prepare)
        self.assertIn("zg361_p2c_m360_source_status value = 4", prepare)
        self.assertIn("zg361_p2c_m360_source_reason value = 360492", prepare)
        self.assertIn("zg361_p2c_m360_source_reason value = 360424", prepare)
        self.assertIn("zg361_p2c_m360_source_reason value = 360410", prepare)
        self.assertNotEqual(generator.M360_SOURCE_STATUS["wait"], generator.M360_SOURCE_STATUS["structural_na"])
        self.assertNotEqual(generator.M360_SOURCE_STATUS["wait"], generator.M360_SOURCE_STATUS["red"])

    def test_m360_first_viable_pair_is_frozen_without_truncation_or_reselection(self) -> None:
        prepare = block(self.effects, "zg361_p2c_prepare_m360_source_effect")
        self.assertEqual(prepare.count("ordered_in_list = {"), 2)
        self.assertEqual(prepare.count("order_by = { value = var:zg361_p2c_mg_frozen_order multiply = -1 }"), 2)
        self.assertIn("var:zg361_b1_m360_source_quota <= scope:zg361_p2c_m360_remaining_quota", prepare)
        self.assertIn("value = 6 subtract = var:zg361_p2c_subject.var:zg361_b1_m360_source_quota", prepare)
        self.assertIn("zg361_p2c_m360_selection_found = 0", prepare)
        self.assertIn("zg361_p2c_m360_selection_found value = 1", prepare)
        self.assertIn("zg361_p2c_m360_source_c1_manager value = var:zg361_p2c_subject", prepare)
        self.assertNotIn("min = 6", prepare)
        self.assertNotIn("max = 6", prepare)
        terminal_prefix = prepare.split("# Consumed, RED and structural N/A are terminal", 1)[1]
        self.assertNotIn("ordered_in_list", terminal_prefix.split("else_if = {", 1)[0])

    def test_m360_ready_only_uses_gated_workforce_resume(self) -> None:
        body = block(self.effects, "zg361_p2c_stage_11_workforce_endgame_effect")
        prepared = body.index("zg361_p2c_prepare_m360_source_effect = yes")
        ready = body.index("var:zg361_p2c_m360_source_status = 1", prepared)
        resume = body.index("zg361_we_resume_m360_from_central_source_effect = {", ready)
        self.assertLess(prepared, ready)
        self.assertLess(ready, resume)
        self.assertNotIn("zg361_p2c_call_workforce_adapter_effect = yes", body[prepared:resume])
        self.assertIn("zg361_we_finalize_manager_collective_na_effect = {", body)
        self.assertIn("REASON = 360362", body)
        self.assertIn("REASON = 360410", body)

    def test_workforce_history_accruing_status8_is_legitimate_terminal(self) -> None:
        body = block(self.effects, "zg361_p2c_stage_11_workforce_endgame_effect")
        history = body.index("var:zg361_we_portfolio_status = 8")
        red = body.rindex("CODE = 1161")
        self.assertLess(history, red)
        for token in (
            "var:zg361_we_portfolio_terminal_history_accruing = 1",
            "var:zg361_we_portfolio_terminal_owned_operations = 39",
            "var:zg361_we_portfolio_terminal_skipped_charter = 1",
            "var:zg361_we_portfolio_terminal_success = 0",
            "var:zg361_case_al_state = 8",
            "STATUS = 2 STAGE_VAR = zg361_p2c_stage_11_status",
        ):
            self.assertIn(token, body[history:red])

    def test_m275_runner_requisition_is_central_owned_commit_then_consume_then_verify(self) -> None:
        schedule = block(self.effects, "zg361_p2c_schedule_m275_runner_requisition_effect")
        producer = block(self.effects, "zg361_p2c_open_m275_runner_requisition_effect")
        due = block(self.workforce, "zg361_we_m275_hold_due_effect")
        adapter = block(self.workforce, "zg361_we_consume_m275_runner_reopen_effect")
        ingress = block(self.events, "zg361p2c.4")
        dispatch = block(self.events, "zg361p2c.5")
        verify = block(self.events, "zg361p2c.6")

        self.assertIn("m275_hold_pending = 1", schedule)
        self.assertIn("m275_runner_reopen_pending = 1", schedule)
        self.assertIn("id = zg361p2c.4 days = 1", schedule)
        self.assertEqual(1, due.count("zg361_p2c_schedule_m275_runner_requisition_effect = {"))
        self.assertLess(
            due.index("m275_runner_reopen_pending value = 1"),
            due.index("zg361_p2c_schedule_m275_runner_requisition_effect = {"),
        )
        self.assertNotIn("candidate_active_case value = var:zg361_we_m275_write_case", due)
        self.assertNotIn("zg361_p2c_schedule_m275_runner_requisition_effect", block(self.workforce, "zg361_we_m275_route_c_effect"))

        self.assertIn("save_temporary_scope_as = zg361_p2c_m275_requisition_cursor_owner", producer)
        self.assertIn("change_variable = { name = zg361_p2c_m275_requisition_cursor add = 1 }", producer)
        self.assertNotIn("zg361_p2c_m275_requisition_cursor value = 0 } }\n            if", producer)
        self.assertNotIn("999999", producer)
        for field in (
            "owner", "original_subject", "source_cycle", "source_case", "source_state",
            "runner_up", "runner_evidence", "hc_lineage_receipt", "hc_flight_case",
            "serial", "new_case", "new_state", "receipt_id", "receipt_hash", "opened",
        ):
            self.assertIn(f"zg361_p2c_m275_requisition_{field}", producer)
        self.assertIn("NOT = { scope:zg361_p2c_m275_expected_new_case = $TICKET_CASE$ }", producer)
        receipt = producer.index("name = zg361_p2c_m275_requisition_receipt_hash value")
        opened = producer.index("name = zg361_p2c_m275_requisition_opened value", receipt)
        committed = producer.index("name = zg361_p2c_m275_requisition_committed value = 1", opened)
        queued = producer.index("trigger_event = { id = zg361p2c.5 days = 1 }", committed)
        self.assertLess(receipt, opened)
        self.assertLess(opened, committed)
        self.assertLess(committed, queued)
        for forbidden in ("zg361_ch_hc_reserved add", "zg361_ch_hc_available add", "add_gold", "remove_short_term_gold"):
            self.assertNotIn(forbidden, producer)
            self.assertNotIn(forbidden, adapter)

        self.assertIn("zg361_p2c_open_m275_runner_requisition_effect = {", ingress)
        self.assertNotIn("zg361_we_consume_m275_runner_reopen_effect", ingress)
        self.assertIn("zg361_we_consume_m275_runner_reopen_effect = {", dispatch)
        self.assertNotIn("$RUNNER_UP$", dispatch)
        self.assertIn("id = zg361p2c.6 days = 1", dispatch)
        self.assertIn("candidate_active_case = scope:zg361_p2c_m275_verify_new_case", verify)
        self.assertIn("ad_hc_flight_case = scope:zg361_p2c_m275_verify_new_case", verify)
        self.assertLess(
            verify.index("m275_requisition_pending value = 0"),
            verify.index("m275_requisition_consumed value = 1"),
        )

        self.assertNotIn("$NEW_REQUISITION_CASE$", adapter)
        self.assertNotIn("$REQUISITION_RECEIPT_ID$", adapter)
        self.assertNotIn("$REQUISITION_RECEIPT_HASH$", adapter)
        self.assertIn("candidate_active_case value = var:zg361_p2c_m275_requisition_new_case", adapter)
        self.assertIn("ad_hc_flight_case value = root.var:zg361_p2c_m275_requisition_new_case", adapter)
        self.assertLess(
            adapter.index("candidate_active_case value = var:zg361_p2c_m275_requisition_new_case"),
            adapter.index("m275_hold_pending value = 0"),
        )
        self.assertLess(
            adapter.index("m275_runner_reopen_pending value = 0"),
            adapter.index("m275_runner_reopen_consumed value = 1"),
        )

    def test_d1_transition_gaps_poll_same_tuple_instead_of_red(self) -> None:
        p3 = block(self.effects, "zg361_p2c_stage_07_metrics_delivery_effect")
        self.assertIn("var:zg361_p2c_stage_status = 1", p3)
        self.assertIn("var:zg361_p3_portfolio_closed = 0", p3)
        self.assertIn("var:zg361_p3_portfolio_result_case = root.var:zg361_p2c_result_case", p3)
        cp = block(self.effects, "zg361_p2c_stage_08_credit_project_effect")
        self.assertIn("var:zg361_p2c_stage_status = 1", cp)
        self.assertIn("var:zg361_cp_portfolio_closed = 0", cp)
        workforce = block(self.effects, "zg361_p2c_stage_11_workforce_endgame_effect")
        self.assertIn("var:zg361_p2c_stage_status = 1", workforce)
        self.assertIn("var:zg361_we_portfolio_closed = 0", workforce)

    def test_workforce_external_handoff_is_not_success(self) -> None:
        body = block(self.effects, "zg361_p2c_stage_11_workforce_endgame_effect")
        external = body.index("var:zg361_we_portfolio_status = 5")
        wait = body.index("REASON = 357359", external)
        success = body.index("STATUS = 2")
        self.assertLess(success, external)
        self.assertLess(external, wait)
        self.assertIn("var:zg361_we_portfolio_closed = 1", body[:external])
        self.assertIn("var:zg361_we_portfolio_status = 6", body[:external])
        self.assertIn("zg361_we_al_external_last_operation = 359", body)
        self.assertNotIn("STATUS = 2", body[external:wait])
        producer = body.index(
            "zg361_b2_submit_completed_al_receipts_effect = {",
            external,
        )
        verified = body.index(
            "var:zg361_we_al_external_stage_receipts_verified = 1",
            external,
        )
        prepared = body.index("zg361_p2c_prepare_m360_source_effect = yes", verified)
        resume = body.index(
            "zg361_we_resume_m360_from_central_source_effect = {",
            prepared,
        )
        self.assertLess(producer, verified)
        self.assertLess(verified, prepared)
        self.assertLess(prepared, resume)
        producer_prefix = body[external:producer]
        self.assertIn(
            "var:zg361_p2c_subject = { zg361_is_celestial_liege_trigger = yes }",
            producer_prefix,
        )
        self.assertIn("TICKET_OWNER = root TICKET_SUBJECT = this", body[producer:verified])
        self.assertIn(
            "TICKET_CASE = var:zg361_case_al_case_serial",
            body[producer:verified],
        )
        for token in (
            "var:zg361_we_portfolio_status = 7",
            "var:zg361_we_portfolio_terminal_na = 1",
            "var:zg361_we_portfolio_terminal_reason = 360361",
            "var:zg361_we_portfolio_terminal_owned_operations = 38",
            "var:zg361_we_portfolio_terminal_skipped_manager_only = 2",
            "var:zg361_we_portfolio_terminal_success = 0",
            "var:zg361_we_final_conservation_ok = 1",
            "var:zg361_case_al_active = 0",
            "STATUS = 3 STAGE_VAR = zg361_p2c_stage_11_status",
        ):
            self.assertIn(token, body)
        self.assertIn("NOT = { zg361_is_celestial_liege_trigger = yes }", body)
        self.assertIn("REASON = 360361 STAGE_VAR = zg361_p2c_stage_11_status", body)
        suspended = block(self.effects, "zg361_p2c_suspend_external_effect")
        self.assertIn("zg361_p2c_terminal_state value = 5", suspended)
        self.assertNotIn("zg361_p2c_completed_cycle", suspended)

    def test_player_and_ai_share_business_path(self) -> None:
        pump = block(self.effects, "zg361_p2c_pump_effect")
        self.assertNotIn("is_ai = no", pump)
        self.assertNotIn("is_ai = yes", pump)
        lane = block(self.effects, "zg361_p2c_mark_lane_busy_effect")
        self.assertIn("is_ai = no", lane)
        self.assertIn("else = { set_variable = { name = zg361_p2c_ui_lane_busy value = 0 } }", lane)
        summary = block(self.events, "zg361p2c.2")
        self.assertIn("is_ai = no", summary)
        self.assertEqual(self.events.count("hidden = yes"), 5)
        self.assertEqual(self.events.count("title = zg361_p2c_summary_title"), 1)

    def test_localization_keys_exist_in_all_nine_files(self) -> None:
        expected = {
            "zg361_p2c_summary_title",
            "zg361_p2c_summary_desc",
            "zg361_p2c_summary_ack",
        }
        for language, header in generator.LANGUAGES:
            text = read(f"localization/{language}/zg361_phase2_central_l_{language}.yml")
            self.assertTrue(text.startswith(f"{header}:\n"), language)
            keys = set(re.findall(r'^\s+([^\s:]+):\d+\s+"', text, flags=re.MULTILINE))
            self.assertEqual(keys, expected, language)

    def test_readiness_claim_is_honest(self) -> None:
        self.assertEqual(generator.READINESS, "static-ready")
        self.assertIn("Readiness: `static-ready`", self.spec)
        self.assertIn("MCP evidence: `none`", self.spec)
        self.assertIn("CK3 live evidence: `none`", self.spec)
        self.assertIn("尚未经过 MCP-first CK3", self.spec)
        boundary = self.spec.split("## 5.", 1)[0]
        self.assertNotIn("fixture-live", boundary)
        self.assertNotIn("production-live", boundary)


if __name__ == "__main__":
    unittest.main()

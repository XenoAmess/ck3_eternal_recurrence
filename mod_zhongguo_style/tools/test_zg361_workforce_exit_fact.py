#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contracts for the real Workforce #277 native-exit fact package."""

from __future__ import annotations

from contextlib import redirect_stdout
import hashlib
import io
import re
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_zg361_workforce_exit_fact as gen
import gen_361_workforce_endgame_runtime as workforce_gen


MOD_ROOT = Path(__file__).resolve().parent.parent


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def workforce_effect_owner_source(effect_name: str) -> str:
    owners = tuple(
        group.filename
        for group in workforce_gen.EFFECT_GROUPS
        if effect_name in group.effect_names
    )
    if len(owners) != 1:
        raise AssertionError(
            f"expected exactly one workforce shard owner for {effect_name}, found {owners}"
        )
    return text(MOD_ROOT / "common" / "scripted_effects" / owners[0])


def block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^\s*{re.escape(name)}\s*=", source)
    if match is None:
        raise AssertionError(f"missing block: {name}")
    start = match.start()
    opening = source.index("{", start)
    depth = 0
    quoted = False
    escaped = False
    for index in range(opening, len(source)):
        char = source[index]
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
                return source[start : index + 1]
    raise AssertionError(f"unclosed block: {name}")


def localization_keys(source: str) -> set[str]:
    return set(re.findall(r'^\s+([^\s:#]+):\d+\s+"', source, re.MULTILINE))


class WorkforceExitFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Semantic assertions retain the historical definition order so the
        # block helper cannot confuse an earlier call site with its provider.
        cls.effects = gen.render_effects().decode("utf-8-sig")
        cls.events = gen.render_events().decode("utf-8-sig")
        cls.position = text(gen.POSITION_PATH)
        cls.spec = text(gen.SPEC_PATH)

    def test_contract_constants_and_exact_output_package(self) -> None:
        gen.validate_contract()
        self.assertEqual(gen.M274_POSITION_TYPE_ID, 3_612_741)
        self.assertEqual(gen.POSITION_CARRIER_TYPE_ID, 3_612_771)
        self.assertNotEqual(gen.M274_POSITION_TYPE_ID, gen.POSITION_CARRIER_TYPE_ID)
        self.assertEqual(gen.REASON_KIND_PIP, 1)
        self.assertEqual(len(gen.outputs()), 20)
        expected = {
            *gen.effect_paths(),
            *gen.event_paths(),
            gen.POSITION_PATH,
            gen.SPEC_PATH,
            *(
                MOD_ROOT
                / "localization"
                / language
                / gen.LOC_BASENAME.format(language=language)
                for language in gen.LANGUAGES
            ),
        }
        self.assertEqual(set(gen.outputs()), expected)

    def test_all_generated_files_are_current_and_have_bom(self) -> None:
        for path, payload in gen.outputs().items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(path.read_bytes(), payload, path)
            self.assertTrue(payload.startswith(gen.BOM), path)
        for path in (*gen.effect_paths(), *gen.event_paths(), gen.POSITION_PATH):
            self.assertTrue(text(path).startswith(gen.HEADER.rstrip()), path)

    def test_effect_purpose_shards_preserve_frozen_aggregate_blocks(self) -> None:
        aggregate = gen.render_effects()
        self.assertEqual(gen.HISTORICAL_EFFECT_BYTES, len(aggregate))
        self.assertEqual(
            gen.HISTORICAL_EFFECT_SHA256,
            hashlib.sha256(aggregate).hexdigest(),
        )
        source_blocks = gen.top_level_blocks(aggregate)
        self.assertEqual(gen.HISTORICAL_EFFECT_COUNT, len(source_blocks))
        self.assertEqual(gen.HISTORICAL_EFFECT_COUNT, len(dict(source_blocks)))

        rendered = gen.render_effect_parts()
        self.assertEqual(
            [group.filename for group in gen.EFFECT_GROUPS],
            list(rendered),
        )
        shard_blocks: dict[str, str] = {}
        for group in gen.EFFECT_GROUPS:
            payload = rendered[group.filename]
            self.assertTrue(payload.startswith(gen.BOM))
            self.assertIn(f"# PURPOSE: {group.purpose}.", payload.decode("utf-8-sig"))
            rows = gen.top_level_blocks(payload)
            self.assertEqual(group.effect_names, tuple(name for name, _ in rows))
            self.assertGreaterEqual(len(rows), 1)
            self.assertLessEqual(len(rows), gen.EFFECT_TARGET_MAX)
            for name, body in rows:
                self.assertNotIn(name, shard_blocks)
                shard_blocks[name] = body
        self.assertEqual(dict(source_blocks), shard_blocks)
        self.assertEqual({}, gen.EFFECT_HARD_LIMIT_EXCEPTIONS)
        self.assertEqual(
            [],
            [
                group.filename
                for group in gen.EFFECT_GROUPS
                if len(group.effect_names) > gen.EFFECT_TARGET_MAX
            ],
        )
        self.assertEqual(
            [],
            [
                group.filename
                for group in gen.EFFECT_GROUPS
                if len(group.effect_names) > gen.EFFECT_HARD_MAX
            ],
        )

    def test_seed_product_closure_is_exact_four_shards_and_ten_effects(self) -> None:
        closure = set(gen.SEED_EFFECT_CLOSURE_NAMES)
        selected = [
            group
            for group in gen.EFFECT_GROUPS
            if closure.intersection(group.effect_names)
        ]
        selected_names = {
            name for group in selected for name in group.effect_names
        }
        self.assertEqual(10, len(closure))
        self.assertEqual(4, len(selected))
        self.assertEqual(closure, selected_names)
        self.assertTrue(
            all(set(group.effect_names).issubset(closure) for group in selected)
        )

    def test_seed_product_closure_accounts_for_court_position_callbacks(self) -> None:
        position = block(self.position, gen.POSITION_KEY)
        callback_names = {
            f"{gen.PREFIX}_on_native_slot_received_effect",
            f"{gen.PREFIX}_on_native_slot_ended_effect",
        }
        observed_callbacks = set(
            re.findall(rf"\b({re.escape(gen.PREFIX)}_[a-z0-9_]+_effect)\s*=", position)
        )
        self.assertEqual(callback_names, observed_callbacks)
        self.assertTrue(callback_names.issubset(set(gen.SEED_EFFECT_CLOSURE_NAMES)))

        ended = block(self.effects, f"{gen.PREFIX}_on_native_slot_ended_effect")
        self.assertIn(f"{gen.PREFIX}_capture_role_failure_effect = yes", ended)
        self.assertTrue(
            {
                f"{gen.PREFIX}_clear_role_failure_receipt_effect",
                f"{gen.PREFIX}_capture_role_failure_effect",
                f"{gen.PREFIX}_verify_role_failure_publish_effect",
            }.issubset(set(gen.SEED_EFFECT_CLOSURE_NAMES))
        )
        self.assertTrue(
            {
                gen.ROLE_FAILURE_PUBLISH_EVENT_ID,
                gen.ROLE_FAILURE_VERIFY_EVENT_ID,
            }.issubset(set(gen.SEED_EVENT_CLOSURE_IDS))
        )

    def test_event_purpose_shards_preserve_frozen_aggregate_blocks(self) -> None:
        aggregate = gen.render_events()
        self.assertEqual(gen.HISTORICAL_EVENT_BYTES, len(aggregate))
        self.assertEqual(
            gen.HISTORICAL_EVENT_SHA256,
            hashlib.sha256(aggregate).hexdigest(),
        )
        source_blocks = gen.top_level_blocks(aggregate)
        self.assertEqual(gen.HISTORICAL_EVENT_COUNT, len(source_blocks))
        self.assertEqual(gen.HISTORICAL_EVENT_COUNT, len(dict(source_blocks)))

        rendered = gen.render_event_parts()
        self.assertEqual(
            [group.filename for group in gen.EVENT_GROUPS],
            list(rendered),
        )
        shard_blocks: dict[str, str] = {}
        for group in gen.EVENT_GROUPS:
            payload = rendered[group.filename]
            self.assertTrue(payload.startswith(gen.BOM))
            self.assertIn(f"# PURPOSE: {group.purpose}.", payload.decode("utf-8-sig"))
            rows = gen.top_level_blocks(payload)
            expected_names = tuple(
                f"{gen.NAMESPACE}.{event_id}" for event_id in group.event_ids
            )
            self.assertEqual(expected_names, tuple(name for name, _ in rows))
            self.assertGreaterEqual(len(rows), 1)
            self.assertLessEqual(len(rows), gen.EVENT_TARGET_MAX)
            for name, body in rows:
                self.assertNotIn(name, shard_blocks)
                shard_blocks[name] = body
        self.assertEqual(dict(source_blocks), shard_blocks)
        self.assertEqual({}, gen.EVENT_HARD_LIMIT_EXCEPTIONS)
        self.assertEqual(
            [],
            [
                group.filename
                for group in gen.EVENT_GROUPS
                if len(group.event_ids) > gen.EVENT_TARGET_MAX
            ],
        )
        self.assertEqual(
            [],
            [
                group.filename
                for group in gen.EVENT_GROUPS
                if len(group.event_ids) > gen.EVENT_HARD_MAX
            ],
        )

    def test_seed_product_event_closure_is_two_exact_five_event_shards(self) -> None:
        closure = set(gen.SEED_EVENT_CLOSURE_IDS)
        selected = [
            group
            for group in gen.EVENT_GROUPS
            if closure.intersection(group.event_ids)
        ]
        selected_ids = {event_id for group in selected for event_id in group.event_ids}
        self.assertEqual(5, len(closure))
        self.assertEqual(2, len(selected))
        self.assertEqual(closure, selected_ids)
        self.assertTrue(
            all(set(group.event_ids).issubset(closure) for group in selected)
        )

    def test_legacy_monoliths_are_absent_and_check_rejects_them(self) -> None:
        self.assertFalse(gen.LEGACY_EFFECT_PATH.exists())
        self.assertFalse(gen.LEGACY_EVENT_PATH.exists())
        self.assertNotIn(gen.LEGACY_EFFECT_PATH, gen.outputs())
        self.assertNotIn(gen.LEGACY_EVENT_PATH, gen.outputs())
        with tempfile.TemporaryDirectory(prefix="zg361-exit-fact-split-") as temp:
            root = Path(temp)
            effects_dir = root / "common" / "scripted_effects"
            effects_dir.mkdir(parents=True)
            events_dir = root / "events"
            events_dir.mkdir(parents=True)
            expected_path = effects_dir / gen.EFFECT_GROUPS[0].filename
            expected_payload = gen.render_effect_parts()[gen.EFFECT_GROUPS[0].filename]
            expected_path.write_bytes(expected_payload)
            expected_event_path = events_dir / gen.EVENT_GROUPS[0].filename
            expected_event_payload = gen.render_event_parts()[gen.EVENT_GROUPS[0].filename]
            expected_event_path.write_bytes(expected_event_payload)
            legacy_path = effects_dir / gen.LEGACY_EFFECT_FILENAME
            legacy_path.write_bytes(gen.render_effects())
            legacy_event_path = events_dir / gen.LEGACY_EVENT_FILENAME
            legacy_event_path.write_bytes(gen.render_events())
            rendered = {
                expected_path: expected_payload,
                expected_event_path: expected_event_payload,
            }

            with (
                mock.patch.object(gen, "MOD_ROOT", root),
                mock.patch.object(gen, "outputs", return_value=rendered),
                mock.patch.object(sys, "argv", ["generator", "--check"]),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(1, gen.main())
            self.assertTrue(legacy_path.exists())
            self.assertTrue(legacy_event_path.exists())

            with (
                mock.patch.object(gen, "MOD_ROOT", root),
                mock.patch.object(gen, "outputs", return_value=rendered),
                mock.patch.object(sys, "argv", ["generator"]),
                redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(0, gen.main())
            self.assertFalse(legacy_path.exists())
            self.assertFalse(legacy_event_path.exists())
            self.assertEqual(expected_payload, expected_path.read_bytes())
            self.assertEqual(expected_event_payload, expected_event_path.read_bytes())

    def test_nine_language_structure_and_authored_zh_en(self) -> None:
        self.assertEqual(len(gen.LANGUAGES), 9)
        expected_keys = {gen.POSITION_KEY, f"{gen.POSITION_KEY}_desc"}
        english = text(
            MOD_ROOT
            / "localization"
            / "english"
            / gen.LOC_BASENAME.format(language="english")
        )
        chinese = text(
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / gen.LOC_BASENAME.format(language="simp_chinese")
        )
        self.assertEqual(localization_keys(english), expected_keys)
        self.assertEqual(localization_keys(chinese), expected_keys)
        self.assertIn("361 Formal Career Slot", english)
        self.assertIn("三六一正式在岗编制", chinese)
        for language in set(gen.LANGUAGES) - {"english", "simp_chinese"}:
            placeholder = text(
                MOD_ROOT
                / "localization"
                / language
                / gen.LOC_BASENAME.format(language=language)
            )
            self.assertEqual(localization_keys(placeholder), expected_keys)
            self.assertIn("361 Formal Career Slot", placeholder)

    def test_persistent_carrier_is_real_hidden_zero_salary_native_position(self) -> None:
        position = block(self.position, gen.POSITION_KEY)
        for needle in (
            "max_available_positions = 100",
            "minimum_rank = duchy",
            "salary = { gold = 0 }",
            "received_salary = { gold = 0 }",
            "ai_position_score = { value = -1000 }",
            "ai_candidate_score = { value = -1000 }",
            f"has_variable = {gen.PREFIX}_window_open",
            f"var:{gen.PREFIX}_slot_active = 1",
        ):
            self.assertIn(needle, position)
        self.assertIn("on_court_position_received = {", position)
        self.assertIn("on_court_position_revoked = {", position)
        self.assertIn("on_court_position_invalidated = {", position)
        self.assertIn("on_court_position_vacated = {", position)
        self.assertIn("END_REASON = 1", position)
        self.assertIn("END_REASON = 2", position)
        self.assertIn("END_REASON = 3", position)

    def test_arm_requires_complete_real_m274_lineage_and_old_carrier_gone(self) -> None:
        arm = block(self.effects, f"{gen.PREFIX}_arm_from_m274_effect")
        required = (
            "EXPECTED_STATE = 4",
            "zg361_we_m274_business_object_created = 1",
            "zg361_we_m274_object_consumed = 1",
            "zg361_we_m274_hired = 1",
            "zg361_we_m274_native_appointment_confirmed = 1",
            f"zg361_we_m274_position_type_id = {gen.M274_POSITION_TYPE_ID}",
            "zg361_workforce_appointment_fact_receipt_consumed = 1",
            "zg361_workforce_appointment_fact_receipt_consumed_operation = 274",
            "zg361_workforce_appointment_fact_receipt_native_callback_seen = 1",
            "zg361_workforce_appointment_fact_receipt_position_still_active = 0",
            "zg361_workforce_appointment_fact_receipt_position_released_by_package = 1",
            "zg361_workforce_appointment_fact_receipt_position_release_joined_by_consumer = 1",
            f"NOT = {{ has_court_position = {gen.M274_POSITION_KEY} }}",
            "zg361_we_formal_hc_active = 1",
            "zg361_ch_hc_occupied >= 1",
        )
        for needle in required:
            self.assertIn(needle, arm)

    def test_native_appointment_is_preflighted_and_not_sealed_same_effect(self) -> None:
        arm = block(self.effects, f"{gen.PREFIX}_arm_from_m274_effect")
        dispatch = block(self.effects, f"{gen.PREFIX}_dispatch_native_arm_effect")
        callback = block(self.effects, f"{gen.PREFIX}_on_native_slot_received_effect")
        audit = block(self.effects, f"{gen.PREFIX}_audit_arm_effect")
        self.assertEqual(self.effects.count("appoint_court_position = {"), 1)
        self.assertNotIn("can_appoint_char_to_court_position = {", arm)
        self.assertNotIn("appoint_court_position = {", arm)
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.ARM_DISPATCH_EVENT_ID} days = 1", arm
        )
        self.assertIn(f"var:{gen.PREFIX}_arm_request_authorized = 1", dispatch)
        self.assertIn("can_appoint_char_to_court_position = {", dispatch)
        self.assertLess(
            dispatch.index("can_appoint_char_to_court_position = {"),
            dispatch.index("appoint_court_position = {"),
        )
        self.assertIn(
            f"set_variable = {{ name = {gen.PREFIX}_arm_request_dispatched value = 1 }}",
            dispatch,
        )
        self.assertIn(f"var:{gen.PREFIX}_arm_request_authorized = 1", callback)
        self.assertNotIn(f"var:{gen.PREFIX}_arm_request_dispatched = 1", callback)
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_slot_active value = 1", arm)
        self.assertNotIn(
            f"set_variable = {{ name = {gen.PREFIX}_slot_active value = 1", dispatch
        )
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_slot_active value = 1", callback)
        self.assertIn(f"var:{gen.PREFIX}_arm_request_dispatched = 1", audit)
        self.assertIn(f"set_variable = {{ name = {gen.PREFIX}_slot_active value = 1", audit)
        self.assertNotIn(
            f"id = {gen.NAMESPACE}.{gen.ARM_AUDIT_EVENT_ID} days = 1", callback
        )
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.ARM_AUDIT_EVENT_ID} days = 1", dispatch
        )

    def test_failed_arm_cleanup_crosses_an_event_boundary(self) -> None:
        audit = block(self.effects, f"{gen.PREFIX}_audit_arm_effect")
        cleanup = block(
            self.effects, f"{gen.PREFIX}_dispatch_cleanup_revoke_effect"
        )
        self.assertNotIn(f"revoke_court_position = {gen.POSITION_KEY}", audit)
        self.assertIn(
            f"set_variable = {{ name = {gen.PREFIX}_cleanup_revoke_requested value = 1 }}",
            audit,
        )
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.CLEANUP_REVOKE_EVENT_ID} days = 1", audit
        )
        self.assertIn(f"var:{gen.PREFIX}_cleanup_revoke_requested = 1", cleanup)
        self.assertIn(
            f"var:{gen.PREFIX}_arm_owner = {{\n"
            "            revoke_court_position = {\n"
            "                recipient = root\n"
            f"                court_position = {gen.POSITION_KEY}\n"
            "            }\n"
            "        }",
            cleanup,
        )
        self.assertNotRegex(
            cleanup,
            rf"(?m)^\s*revoke_court_position\s*=\s*{re.escape(gen.POSITION_KEY)}\s*$",
        )

    def test_public_abi_has_no_caller_truth_material(self) -> None:
        public = "\n".join(
            block(self.effects, name)
            for name in (
                f"{gen.PREFIX}_arm_from_m274_effect",
                f"{gen.PREFIX}_request_closed_pip_exit_effect",
                f"{gen.PREFIX}_publish_to_workforce_m277_effect",
                f"{gen.PREFIX}_consume_after_m277_effect",
            )
        )
        for forbidden in (
            "$SUCCESS$",
            "$EXIT_CONFIRMED$",
            "$EXIT_RECEIPT_ID$",
            "$EXIT_RECEIPT_HASH$",
            "$FORMER_SLOT_ID$",
            "$DISPLACED_HOURS$",
            "$DISPLACED_COST_RECEIPT$",
            "$PIP_CASE_ID$",
            "$PIP_CLOSURE_RECEIPT_ID$",
        ):
            self.assertNotIn(forbidden, public)
        self.assertIn("TICKET_OWNER = var:", public)
        self.assertIn("EXIT_RECEIPT_ID = var:", public)

    def test_exit_request_joins_real_slot_b2_and_hc_before_revoke(self) -> None:
        request = block(self.effects, f"{gen.PREFIX}_request_closed_pip_exit_effect")
        dispatch = block(self.effects, f"{gen.PREFIX}_dispatch_native_exit_effect")
        for needle in (
            "EXPECTED_STATE = 6",
            f"has_court_position = {gen.POSITION_KEY}",
            "is_court_position_employer = {",
            "zg361_we_m269_outcome_settled = 1",
            "zg361_we_formal_hc_active = 1",
            "zg361_we_formal_hc_active_case = $TICKET_CASE$",
            "zg361_ch_hc_occupied >= 1",
            "zg361_b2_workforce_pip_pending = 1",
            "zg361_b2_workforce_pip_consumed = 0",
            "zg361_b2_workforce_pip_owner = $TICKET_OWNER$",
            "zg361_b2_workforce_pip_subject = $TICKET_SUBJECT$",
            "zg361_b2_workforce_pip_closure_receipt_id > 0",
            "zg361_b2_workforce_pip_closure_receipt_hash > 0",
            "zg361_b2_workforce_pip_state = 4",
            "zg361_b2_pip_outcome_code = 2",
            "zg361_b2_pip_outcome_result_grade = 1",
        ):
            self.assertIn(needle, request)
        pending_index = request.index(
            f"set_variable = {{ name = {gen.PREFIX}_exit_pending value = 1 }}"
        )
        authorized_index = request.index(
            f"set_variable = {{ name = {gen.PREFIX}_exit_request_authorized value = 1 }}"
        )
        self.assertLess(pending_index, authorized_index)
        self.assertNotIn(f"revoke_court_position = {gen.POSITION_KEY}", request)
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.EXIT_DISPATCH_EVENT_ID} days = 1", request
        )
        self.assertIn(f"var:{gen.PREFIX}_exit_request_authorized = 1", dispatch)
        self.assertIn("zg361_b2_workforce_pip_state = 4", dispatch)
        self.assertIn(
            f"set_variable = {{ name = {gen.PREFIX}_exit_request_dispatched value = 1 }}",
            dispatch,
        )
        self.assertIn(
            f"var:{gen.PREFIX}_exit_owner = {{\n"
            "            revoke_court_position = {\n"
            "                recipient = root\n"
            f"                court_position = {gen.POSITION_KEY}\n"
            "            }\n"
            "        }",
            dispatch,
        )
        self.assertNotRegex(
            dispatch,
            rf"(?m)^\s*revoke_court_position\s*=\s*{re.escape(gen.POSITION_KEY)}\s*$",
        )

    def test_only_new_native_revoke_callback_can_seal_exit(self) -> None:
        request = block(self.effects, f"{gen.PREFIX}_request_closed_pip_exit_effect")
        dispatch = block(self.effects, f"{gen.PREFIX}_dispatch_native_exit_effect")
        callback = block(self.effects, f"{gen.PREFIX}_on_native_slot_ended_effect")
        audit = block(self.effects, f"{gen.PREFIX}_audit_exit_effect")
        self.assertEqual(self.effects.count("revoke_court_position = {"), 2)
        self.assertNotRegex(
            self.effects,
            rf"(?m)^\s*revoke_court_position\s*=\s*{re.escape(gen.POSITION_KEY)}\s*$",
        )
        self.assertIn(f"native_exit_revoked_callback_seen value = 1", callback)
        self.assertIn(f"var:{gen.PREFIX}_exit_request_authorized = 1", callback)
        self.assertNotIn(f"var:{gen.PREFIX}_exit_request_dispatched = 1", callback)
        self.assertNotIn(
            f"id = {gen.NAMESPACE}.{gen.EXIT_AUDIT_EVENT_ID} days = 1", callback
        )
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.EXIT_AUDIT_EVENT_ID} days = 1", dispatch
        )
        self.assertIn(f"var:{gen.PREFIX}_exit_request_dispatched = 1", audit)
        self.assertIn(f"var:{gen.PREFIX}_native_exit_revoked_callback_seen = 1", audit)
        self.assertIn(f"NOT = {{ has_court_position = {gen.POSITION_KEY} }}", audit)
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_receipt_active", request)
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_receipt_active", dispatch)
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_receipt_active", callback)
        self.assertIn(f"set_variable = {{ name = {gen.PREFIX}_receipt_active", audit)
        self.assertIn(f"{gen.PREFIX}_clear_exit_pending_effect = yes", audit)

    def test_vacate_and_invalidation_are_observed_but_cannot_seal(self) -> None:
        callback = block(self.effects, f"{gen.PREFIX}_on_native_slot_ended_effect")
        audit = block(self.effects, f"{gen.PREFIX}_audit_exit_effect")
        self.assertIn("unexpected_native_end_seen value = 1", callback)
        self.assertIn("unexpected_native_end_reason value = $END_REASON$", callback)
        self.assertIn("cleanup_revoke_callback_seen value = 1", callback)
        self.assertIn("cleanup_revoke_callback_reason value = $END_REASON$", callback)
        for reason_name in ("revoked", "invalidated", "vacated"):
            self.assertIn(f"native_{reason_name}_seen value = 1", callback)
            self.assertIn(f"native_{reason_name}_owner value = scope:liege", callback)
            self.assertIn(f"native_{reason_name}_subject value = this", callback)
        self.assertIn(f"native_exit_revoked_callback_seen = 1", audit)
        self.assertNotIn(f"native_invalidated_seen = 1", audit)
        self.assertNotIn(f"native_vacated_seen = 1", audit)

    def test_normal_exit_revoke_is_authorized_not_unexpected(self) -> None:
        callback = block(self.effects, f"{gen.PREFIX}_on_native_slot_ended_effect")
        authorized = callback.index(
            "has_variable = zg361_workforce_normal_exit_fact_pending"
        )
        unexpected = callback.index(
            f"set_variable = {{ name = {gen.PREFIX}_unexpected_native_end_seen value = 1 }}"
        )
        self.assertLess(authorized, unexpected)
        for needle in (
            "zg361_workforce_normal_exit_fact_pending = 1",
            "zg361_workforce_normal_exit_fact_pending_subject = this",
            "zg361_workforce_normal_exit_fact_pending_owner = scope:liege",
            "zg361_workforce_normal_exit_fact_request_authorized = 1",
            "zg361_workforce_normal_exit_fact_request_dispatched = 1",
            "zg361_workforce_normal_exit_fact_native_revoke_callback_seen value = 1",
            "zg361_workforce_normal_exit_fact_native_revoke_callback_owner value = scope:liege",
            "zg361_workforce_normal_exit_fact_native_revoke_callback_subject value = this",
        ):
            self.assertIn(needle, callback)

    def test_native_invalidation_seals_distinct_role_failure_receipt(self) -> None:
        callback = block(self.effects, f"{gen.PREFIX}_on_native_slot_ended_effect")
        capture = block(self.effects, f"{gen.PREFIX}_capture_role_failure_effect")
        self.assertLess(
            callback.index(f"{gen.PREFIX}_capture_role_failure_effect = yes"),
            callback.index(f"set_variable = {{ name = {gen.PREFIX}_slot_active value = 0 }}"),
        )
        for needle in (
            "$END_REASON$ = 2",
            f"var:{gen.PREFIX}_slot_active = 1",
            f"var:{gen.PREFIX}_slot_owner = scope:liege",
            f"var:{gen.PREFIX}_slot_subject = this",
            "zg361_workforce_probation_fact_state = 2",
            "zg361_workforce_probation_fact_awaiting_pip = 1",
            "zg361_we_m269_outcome_pending = 1",
            "zg361_we_m269_outcome_settled = 0",
            "zg361_we_formal_hc_active = 1",
            "role_failure_receipt_native_end_reason value = 2",
            "role_failure_receipt_exclusion_reason value = 1",
            "role_failure_receipt_former_slot_hash value = var:",
            "role_failure_receipt_appointment_receipt_hash value = var:",
            "role_failure_receipt_hc_authorized value = var:zg361_ch_hc_authorized",
            "role_failure_receipt_hc_occupied value = var:zg361_ch_hc_occupied",
            "role_failure_receipt_hc_conservation_verified value = 1",
        ):
            self.assertIn(needle, callback if needle == "$END_REASON$ = 2" else capture)
        sealed = f"set_variable = {{ name = {gen.PREFIX}_role_failure_receipt_sealed value = 1 }}"
        self.assertGreater(capture.rindex(sealed), capture.rindex("role_failure_receipt_hash value"))
        self.assertGreater(capture.rindex(sealed), capture.rindex("role_failure_receipt_hc_conservation_verified value"))
        self.assertIn("var:zg361_ch_hc_authorized >= {", capture)
        self.assertIn("var:zg361_ch_hc_authorized <= {", capture)
        self.assertIn("add = var:zg361_ch_hc_reclaimed", capture)
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.ROLE_FAILURE_PUBLISH_EVENT_ID} days = 1",
            capture,
        )
        self.assertNotIn("receipt_actual_exit", capture)
        self.assertNotIn("change_variable = { name = zg361_ch_hc_", capture)

    def test_calculated_hc_guard_uses_comparison_rhs_not_trigger_equality(self) -> None:
        direct_computed_equality = (
            r"(?m)^\s*var:[A-Za-z0-9_]+\s*=\s*\{\s*value\s*="
        )
        capture = block(self.effects, f"{gen.PREFIX}_capture_role_failure_effect")
        consume = block(self.effects, f"{gen.PREFIX}_consume_after_m277_effect")
        for source in (capture, consume):
            self.assertNotRegex(source, direct_computed_equality)
        self.assertEqual(capture.count("var:zg361_ch_hc_authorized >= {"), 1)
        self.assertEqual(capture.count("var:zg361_ch_hc_authorized <= {"), 1)
        self.assertEqual(consume.count("var:zg361_we_m277_object_id >= {"), 1)
        self.assertEqual(consume.count("var:zg361_we_m277_object_id <= {"), 1)
        self.assertEqual(consume.count("var:zg361_ch_hc_occupied >= {"), 1)
        self.assertEqual(consume.count("var:zg361_ch_hc_occupied <= {"), 1)
        self.assertEqual(consume.count("var:zg361_ch_hc_frozen >= {"), 1)
        self.assertEqual(consume.count("var:zg361_ch_hc_frozen <= {"), 1)

    def test_role_failure_publish_and_verify_cross_two_hidden_frames(self) -> None:
        publish = block(self.events, f"{gen.NAMESPACE}.{gen.ROLE_FAILURE_PUBLISH_EVENT_ID}")
        verify_event = block(self.events, f"{gen.NAMESPACE}.{gen.ROLE_FAILURE_VERIFY_EVENT_ID}")
        verify = block(self.effects, f"{gen.PREFIX}_verify_role_failure_publish_effect")
        self.assertIn("hidden = yes", publish)
        self.assertIn(f"{gen.PROBATION_ROLE_FAILURE_EFFECT} = yes", publish)
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.ROLE_FAILURE_VERIFY_EVENT_ID} days = 1",
            publish,
        )
        self.assertIn("hidden = yes", verify_event)
        self.assertIn(f"{gen.PREFIX}_verify_role_failure_publish_effect = yes", verify_event)
        for needle in (
            "probation_fact_source_kind = 4",
            "probation_fact_outcome_quality = 4",
            "probation_fact_outcome_exclusion_reason = 1",
            "probation_fact_source_external_receipt_id = var:",
            "probation_fact_source_external_receipt_hash = var:",
            "role_failure_receipt_published value = 1",
            "role_failure_receipt_consumed value = 1",
        ):
            self.assertIn(needle, verify)

    def test_hours_and_cost_are_derived_from_real_ledgers(self) -> None:
        request = block(self.effects, f"{gen.PREFIX}_request_closed_pip_exit_effect")
        self.assertIn("zg361_we_hours_output >= 0", request)
        self.assertIn("zg361_we_hours_on_call >= 0", request)
        self.assertIn("zg361_we_hours_meeting >= 0", request)
        self.assertIn("zg361_we_hours_governance >= 0", request)
        self.assertIn(
            "exit_displaced_hours value = { value = var:zg361_we_hours_output "
            "add = var:zg361_we_hours_on_call add = var:zg361_we_hours_meeting "
            "add = var:zg361_we_hours_governance }",
            request,
        )
        self.assertIn("zg361_we_offer_gold_paid > 0", request)
        self.assertIn(
            "exit_displaced_cost_amount value = var:zg361_we_offer_gold_paid", request
        )
        self.assertIn("zg361_we_m274_position_receipt_id multiply = 1000", request)
        self.assertIn("zg361_we_m274_position_receipt_hash multiply = 100000", request)

    def test_receipt_freezes_full_abi_and_seal_is_last_receipt_write(self) -> None:
        audit = block(self.effects, f"{gen.PREFIX}_audit_exit_effect")
        required_fields = (
            "receipt_active",
            "receipt_consumed",
            "receipt_published",
            "receipt_owner",
            "receipt_subject",
            "receipt_cycle",
            "receipt_case",
            "receipt_state",
            "receipt_reason_kind",
            "receipt_misconduct_present",
            "receipt_position_type_id",
            "receipt_carrier_type_id",
            "receipt_appointment_receipt_id",
            "receipt_appointment_receipt_hash",
            "receipt_former_slot_id",
            "receipt_former_slot_hash",
            "receipt_pip_cycle",
            "receipt_pip_case",
            "receipt_pip_state",
            "receipt_pip_case_id",
            "receipt_pip_case_hash",
            "receipt_pip_closure_receipt_id",
            "receipt_pip_closure_receipt_hash",
            "receipt_pip_outcome_code",
            "receipt_pip_result_grade",
            "receipt_displaced_hours",
            "receipt_displaced_cost_amount",
            "receipt_displaced_cost_receipt",
            "receipt_displaced_cost_hash",
            "receipt_hc_occupied_before",
            "receipt_hc_frozen_before",
            "receipt_native_callback_seen",
            "receipt_native_end_reason",
            "receipt_id",
            "receipt_hash",
            "receipt_sealed",
        )
        for field in required_fields:
            self.assertIn(f"name = {gen.PREFIX}_{field}", audit)
        self.assertIn(f"receipt_reason_kind value = {gen.REASON_KIND_PIP}", audit)
        self.assertIn(
            f"receipt_carrier_type_id value = var:{gen.PREFIX}_exit_carrier_type_id",
            audit,
        )
        self.assertIn("receipt_misconduct_present value = 0", audit)
        self.assertNotIn("receipt_misconduct_case_id", audit)
        self.assertNotIn("receipt_misconduct_case_hash", audit)
        writes = [
            match.group(1)
            for match in re.finditer(
                rf"set_variable = \{{ name = ({re.escape(gen.PREFIX)}_receipt_[a-z0-9_]+)",
                audit,
            )
        ]
        self.assertEqual(writes[-1], f"{gen.PREFIX}_receipt_sealed")

    def test_exit_audit_requires_b2_and_hc_unchanged_before_seal(self) -> None:
        audit = block(self.effects, f"{gen.PREFIX}_audit_exit_effect")
        seal_index = audit.index(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_active value = 1 }}"
        )
        for needle in (
            "zg361_b2_workforce_pip_pending = 1",
            "zg361_b2_workforce_pip_consumed = 0",
            "zg361_we_formal_hc_active = 1",
            f"zg361_ch_hc_occupied = var:{gen.PREFIX}_exit_hc_occupied_before",
            f"zg361_ch_hc_frozen = var:{gen.PREFIX}_exit_hc_frozen_before",
        ):
            self.assertLess(audit.index(needle), seal_index)

    def test_legacy_adapter_receives_only_internal_sealed_values(self) -> None:
        publish = block(
            self.effects, f"{gen.PREFIX}_publish_to_workforce_m277_effect"
        )
        self.assertEqual(
            publish.count("zg361_we_submit_m277_closed_pip_exit_effect = {"), 1
        )
        self.assertIn("EXIT_CONFIRMED = 1", publish)
        self.assertNotIn("EXIT_CONFIRMED = $", publish)
        for parameter, field in (
            ("EXIT_RECEIPT_ID", "receipt_id"),
            ("EXIT_RECEIPT_HASH", "receipt_hash"),
            ("FORMER_SLOT_ID", "receipt_former_slot_id"),
            ("DISPLACED_HOURS", "receipt_displaced_hours"),
            ("DISPLACED_COST_RECEIPT", "receipt_displaced_cost_receipt"),
        ):
            self.assertIn(f"{parameter} = var:{gen.PREFIX}_{field}", publish)
        for alias in (
            "zg361_we_ad_external_exit_receipt_id",
            "zg361_we_ad_external_exit_receipt_hash",
            "zg361_we_ad_external_exit_former_slot_id",
            "zg361_we_ad_external_exit_displaced_hours",
            "zg361_we_ad_external_exit_displaced_cost_receipt",
        ):
            self.assertNotIn(f"set_variable = {{ name = {alias}", self.effects)

    def test_legacy_adapter_call_supplies_every_required_parameter(self) -> None:
        core = workforce_effect_owner_source(
            "zg361_we_submit_m277_closed_pip_exit_effect"
        )
        adapter = block(core, "zg361_we_submit_m277_closed_pip_exit_effect")
        required = set(re.findall(r"\$([A-Z][A-Z0-9_]*)\$", adapter))
        publish = block(
            self.effects, f"{gen.PREFIX}_publish_to_workforce_m277_effect"
        )
        call = block(publish, "zg361_we_submit_m277_closed_pip_exit_effect")
        supplied = set(
            re.findall(r"(?m)^\s+([A-Z][A-Z0-9_]*)\s*=", call)
        )
        self.assertEqual(required, supplied)

    def test_publish_and_verify_are_separate_events(self) -> None:
        publish = block(
            self.effects, f"{gen.PREFIX}_publish_to_workforce_m277_effect"
        )
        verify = block(self.effects, f"{gen.PREFIX}_verify_publish_effect")
        self.assertIn(
            f"id = {gen.NAMESPACE}.{gen.PUBLISH_VERIFY_EVENT_ID} days = 1", publish
        )
        self.assertNotIn(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_published value = 1 }}",
            publish,
        )
        self.assertIn("zg361_we_adapter_status = 1", verify)
        self.assertIn("zg361_we_ad_external_pip_exit_ready = 1", verify)
        self.assertIn("zg361_b2_workforce_pip_pending = 1", verify)
        self.assertIn("zg361_we_formal_hc_active = 1", verify)
        self.assertIn(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_published value = 1 }}",
            verify,
        )

    def test_consume_requires_exact_core_b2_and_hc_postconditions(self) -> None:
        consume = block(self.effects, f"{gen.PREFIX}_consume_after_m277_effect")
        for needle in (
            "zg361_we_ad_external_pip_exit_ready = 0",
            "zg361_we_ad_external_pip_exit_consumed = 1",
            "zg361_b2_workforce_pip_pending = 0",
            "zg361_b2_workforce_pip_consumed = 1",
            "zg361_case_kernel_receipt_is_current_trigger = {",
            "EXPECTED_CHOICE = 1",
            "EXPECTED_CHOICE = 2",
            "zg361_we_m277_business_object_created = 1",
            "zg361_we_m277_object_type_code = 277",
            "zg361_we_m277_object_pip_exit_vacancy = 1",
            "zg361_we_m277_object_consumed = 1",
            "zg361_we_m277_consumer_contract = 277",
            "zg361_we_m277_consumer_record_pip_exit_277 = 1",
            "zg361_we_record_pip_exit_277 = 1",
            "zg361_we_record_pip_exit_277 = 2",
            "zg361_we_m277_consumed_owner = $TICKET_OWNER$",
            "zg361_we_m277_consumed_subject = $TICKET_SUBJECT$",
            "zg361_we_m277_consumed_cycle = $TICKET_CYCLE$",
            "zg361_we_m277_consumed_case = $TICKET_CASE$",
            "zg361_we_m277_consumed_state = 6",
            f"zg361_we_m277_exit_receipt_id = var:{gen.PREFIX}_receipt_id",
            f"zg361_we_m277_exit_receipt_hash = var:{gen.PREFIX}_receipt_hash",
            f"zg361_we_m277_former_slot_id = var:{gen.PREFIX}_receipt_former_slot_id",
            f"zg361_we_m277_displaced_hours = var:{gen.PREFIX}_receipt_displaced_hours",
            f"zg361_we_m277_displaced_cost_provenance = var:{gen.PREFIX}_receipt_displaced_cost_receipt",
            "zg361_we_m277_vacant_frozen = 1",
            "zg361_we_m277_hc_minted = 0",
            "zg361_we_formal_hc_active = 0",
            f"var:zg361_ch_hc_occupied >= {{ value = var:{gen.PREFIX}_receipt_hc_occupied_before subtract = 1 }}",
            f"var:zg361_ch_hc_occupied <= {{ value = var:{gen.PREFIX}_receipt_hc_occupied_before subtract = 1 }}",
            f"var:zg361_ch_hc_frozen >= {{ value = var:{gen.PREFIX}_receipt_hc_frozen_before add = 1 }}",
            f"var:zg361_ch_hc_frozen <= {{ value = var:{gen.PREFIX}_receipt_hc_frozen_before add = 1 }}",
        ):
            self.assertIn(needle, consume)
        operation_index = consume.index("zg361_we_m277_exit_receipt_id = var:")
        consume_index = consume.rindex(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_consumed value = 1 }}"
        )
        self.assertLess(operation_index, consume_index)

    def test_package_never_releases_hc_or_mutates_resource_ledgers(self) -> None:
        forbidden = (
            "change_variable = { name = zg361_ch_hc_",
            "set_variable = { name = zg361_ch_hc_",
            "change_variable = { name = zg361_we_hours_",
            "change_variable = { name = zg361_we_gold_",
            "remove_short_term_gold",
            "add_gold =",
        )
        for needle in forbidden:
            self.assertNotIn(needle, self.effects)
        self.assertIn("revoke_court_position =", self.effects)

    def test_events_are_hidden_and_cover_all_delayed_boundaries(self) -> None:
        expectations = {
            gen.ARM_DISPATCH_EVENT_ID: f"{gen.PREFIX}_dispatch_native_arm_effect = yes",
            gen.ARM_AUDIT_EVENT_ID: f"{gen.PREFIX}_audit_arm_effect = yes",
            gen.EXIT_DISPATCH_EVENT_ID: f"{gen.PREFIX}_dispatch_native_exit_effect = yes",
            gen.EXIT_AUDIT_EVENT_ID: f"{gen.PREFIX}_audit_exit_effect = yes",
            gen.PUBLISH_EVENT_ID: f"{gen.PREFIX}_publish_to_workforce_m277_effect = yes",
            gen.PUBLISH_VERIFY_EVENT_ID: f"{gen.PREFIX}_verify_publish_effect = yes",
            gen.CLEANUP_REVOKE_EVENT_ID: f"{gen.PREFIX}_dispatch_cleanup_revoke_effect = yes",
            gen.ROLE_FAILURE_PUBLISH_EVENT_ID: gen.PROBATION_ROLE_FAILURE_EFFECT + " = yes",
            gen.ROLE_FAILURE_VERIFY_EVENT_ID: f"{gen.PREFIX}_verify_role_failure_publish_effect = yes",
        }
        for event_id, call in expectations.items():
            event = block(self.events, f"{gen.NAMESPACE}.{event_id}")
            self.assertIn("hidden = yes", event)
            self.assertIn(call, event)

    def test_spec_is_honest_about_scope_and_core_wired_status(self) -> None:
        for needle in (
            "CK3 script core-wired/static-ready; not loader-live or production-live",
            "不能复用 #274 的撤职回调",
            "长期存在",
            "只有本次 exact intent 之后的新 revoked callback",
            "misconduct_present=0",
            "不会伪造 misconduct ID/hash",
            "state=3 graduation 不会撤职",
            "不能冒充正常离职或外部成长",
            "native 岗位结束不等于先释放 HC",
            "core-wired / static-ready / not live",
            "exact normal-exit authorization branch",
        ):
            self.assertIn(needle, self.spec)

    def test_generated_paradox_files_have_balanced_braces(self) -> None:
        sources = [
            *((path, text(path)) for path in gen.effect_paths()),
            *((path, text(path)) for path in gen.event_paths()),
            (gen.POSITION_PATH, self.position),
        ]
        for path, source in sources:
            self.assertEqual(source.count("{"), source.count("}"), path)


if __name__ == "__main__":
    unittest.main()

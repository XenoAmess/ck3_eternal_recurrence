#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contracts for the native Workforce #274 appointment fact."""

from __future__ import annotations

import hashlib
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_zg361_workforce_appointment_fact as gen


MOD_ROOT = Path(__file__).resolve().parent.parent


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(source: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)}\s*=", source)
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


class AppointmentFactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = gen.render_effects().decode("utf-8-sig")
        cls.events = text(gen.EVENTS_PATH)
        cls.position = text(gen.POSITION_PATH)
        cls.spec = text(gen.SPEC_PATH)

    def test_contract_constants_and_exact_output_package(self) -> None:
        gen.validate_contract()
        self.assertEqual(gen.POSITION_TYPE_ID, 3_612_741)
        self.assertEqual(gen.SOURCE_KIND_COURT_POSITION, 1)
        self.assertEqual(len(gen.outputs()), 17)
        expected = {
            *gen.effect_paths(),
            gen.EVENTS_PATH,
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

    def test_all_generated_files_are_current_and_script_assets_have_bom(self) -> None:
        for path, payload in gen.outputs().items():
            self.assertTrue(path.exists(), path)
            self.assertEqual(path.read_bytes(), payload, path)
            self.assertTrue(payload.startswith(gen.BOM), path)
        for path in (*gen.effect_paths(), gen.EVENTS_PATH, gen.POSITION_PATH):
            self.assertTrue(text(path).startswith(gen.HEADER.rstrip()), path)
        self.assertFalse(gen.LEGACY_EFFECT_PATH.exists())

    def test_effect_purpose_shards_preserve_canonical_aggregate_blocks(self) -> None:
        aggregate = gen.render_effects()
        self.assertEqual(gen.CANONICAL_EFFECT_BYTES, len(aggregate))
        self.assertEqual(
            gen.CANONICAL_EFFECT_SHA256,
            hashlib.sha256(aggregate).hexdigest(),
        )
        source_blocks = gen.top_level_blocks(aggregate)
        self.assertEqual(gen.CANONICAL_EFFECT_COUNT, len(source_blocks))
        self.assertEqual(51_862, gen.RETIRED_MONOLITH_EFFECT_BYTES)
        self.assertEqual(
            "886bfd5ec9e15aa744f8bd39e55f9cb3dbd652f4d5b6c2e0eecfaa8197fecc4c",
            gen.RETIRED_MONOLITH_EFFECT_SHA256,
        )
        self.assertEqual(
            (5, 1, 1, 2, 1),
            tuple(len(group.effect_names) for group in gen.EFFECT_GROUPS),
        )
        self.assertTrue(
            all(
                1 <= len(group.effect_names) <= gen.EFFECT_TARGET_MAX
                for group in gen.EFFECT_GROUPS
            )
        )
        self.assertEqual({}, gen.EFFECT_HARD_LIMIT_EXCEPTIONS)
        source_by_name = dict(source_blocks)
        shard_blocks: dict[str, str] = {}
        for filename, payload in gen.render_effect_parts().items():
            self.assertTrue(payload.startswith(gen.BOM), filename)
            for name, body in gen.top_level_blocks(payload):
                self.assertNotIn(name, shard_blocks)
                shard_blocks[name] = body
        self.assertEqual(source_by_name, shard_blocks)

    def test_old_monolith_and_unknown_prefix_shards_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-appointment-shards-") as temp:
            effects_dir = Path(temp)
            declared = effects_dir / gen.EFFECT_GROUPS[0].filename
            legacy = effects_dir / gen.LEGACY_EFFECT_FILENAME
            unknown = effects_dir / f"{gen.PREFIX}_unknown_effects.txt"
            for path in (declared, legacy, unknown):
                path.write_bytes(gen.BOM + b"probe_effect = {}\n")
            unexpected = gen.unexpected_effect_paths(gen.outputs(), effects_dir)
            self.assertEqual((legacy, unknown), unexpected)

    def test_seal_and_publish_is_an_acyclic_two_phase_state_machine(self) -> None:
        seal_name = f"{gen.PREFIX}_seal_and_publish_effect"
        publisher = block(self.effects, seal_name)
        self.assertEqual(1, publisher.count(f"{seal_name} = {{"))
        self.assertEqual(5, self.effects.count(f"{seal_name} = {{"))
        ready_write = (
            f"set_variable = {{ name = {gen.PREFIX}_seal_continuation_ready value = 1 }}"
        )
        ready_remove = f"remove_variable = {gen.PREFIX}_seal_continuation_ready"
        self.assertEqual(2, publisher.count(ready_write))
        self.assertEqual(2, publisher.count(ready_remove))
        receipt_write = publisher.index(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_active value = 1 }}"
        )
        clear_pending = publisher.index(
            f"{gen.PREFIX}_clear_pending_intent_effect = yes", receipt_write
        )
        pending_ready = publisher.index(ready_write, clear_pending)
        continuation_remove = publisher.index(ready_remove, pending_ready)
        submit = publisher.index("zg361_we_submit_ad_appointment_receipt_effect = {")
        self.assertLess(receipt_write, clear_pending)
        self.assertLess(clear_pending, pending_ready)
        self.assertLess(pending_ready, continuation_remove)
        self.assertLess(continuation_remove, submit)
        second_pass = publisher[continuation_remove:submit]
        for needle in (
            f"has_variable = {gen.PREFIX}_receipt_active",
            f"var:{gen.PREFIX}_receipt_owner = $TICKET_OWNER$",
            f"var:{gen.PREFIX}_receipt_subject = $TICKET_SUBJECT$",
            f"var:{gen.PREFIX}_receipt_cycle = $TICKET_CYCLE$",
            f"var:{gen.PREFIX}_receipt_case = $TICKET_CASE$",
            f"var:{gen.PREFIX}_receipt_native_callback_seen = 1",
            f"var:{gen.PREFIX}_receipt_native_holder_postcondition_seen = 1",
        ):
            self.assertIn(needle, second_pass)

    def test_all_four_nonrecursive_publisher_calls_keep_the_frozen_tuple(self) -> None:
        seal_call = f"{gen.PREFIX}_seal_and_publish_effect = {{"
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        audit = block(self.effects, f"{gen.PREFIX}_audit_pending_effect")
        self.assertEqual(2, request.count(seal_call))
        self.assertEqual(2, audit.count(seal_call))
        for field in ("OWNER", "SUBJECT", "CYCLE", "CASE"):
            self.assertGreaterEqual(request.count(f"TICKET_{field} = $TICKET_{field}$"), 2)
        for prefix in ("pending", "receipt"):
            self.assertIn(
                f"TICKET_OWNER = var:{gen.PREFIX}_{prefix}_owner", audit
            )
            self.assertIn(
                f"TICKET_CYCLE = var:{gen.PREFIX}_{prefix}_cycle", audit
            )
            self.assertIn(
                f"TICKET_CASE = var:{gen.PREFIX}_{prefix}_case", audit
            )
        self.assertEqual(2, audit.count("TICKET_SUBJECT = this"))

    def test_nine_language_structure_and_only_zh_en_are_authored(self) -> None:
        self.assertEqual(len(gen.LANGUAGES), 9)
        english_path = (
            MOD_ROOT
            / "localization"
            / "english"
            / gen.LOC_BASENAME.format(language="english")
        )
        chinese_path = (
            MOD_ROOT
            / "localization"
            / "simp_chinese"
            / gen.LOC_BASENAME.format(language="simp_chinese")
        )
        english = text(english_path)
        chinese = text(chinese_path)
        expected_keys = {gen.POSITION_KEY, f"{gen.POSITION_KEY}_desc"}
        self.assertEqual(localization_keys(english), expected_keys)
        self.assertEqual(localization_keys(chinese), expected_keys)
        self.assertIn("361 Probationary Appointment", english)
        self.assertIn("三六一试任编制", chinese)
        for language in set(gen.LANGUAGES) - {"english", "simp_chinese"}:
            path = (
                MOD_ROOT
                / "localization"
                / language
                / gen.LOC_BASENAME.format(language=language)
            )
            placeholder = text(path)
            self.assertEqual(localization_keys(placeholder), expected_keys)
            self.assertIn("361 Probationary Appointment", placeholder)

    def test_real_native_action_has_vanilla_preflight_and_engine_callback(self) -> None:
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        callback = block(
            self.effects, f"{gen.PREFIX}_on_native_position_received_effect"
        )
        self.assertEqual(self.effects.count("appoint_court_position = {"), 1)
        self.assertIn("can_appoint_char_to_court_position = {", request)
        self.assertLess(
            request.index("can_appoint_char_to_court_position = {"),
            request.index("appoint_court_position = {"),
        )
        self.assertIn("on_native_position_received", self.position)
        self.assertIn("on_court_position_vacated = {", self.position)
        self.assertIn("END_REASON = 3", self.position)
        self.assertIn("scope:liege = var:", callback)
        self.assertIn(f"has_court_position = {gen.POSITION_KEY}", callback)
        self.assertIn("is_court_position_employer = {", callback)
        self.assertIn(f"native_callback_position_type_id value = {gen.POSITION_TYPE_ID}", callback)

    def test_public_abi_cannot_supply_success_or_receipt_material(self) -> None:
        wrapper = block(
            self.effects, f"{gen.PREFIX}_m274_appoint_and_consume_effect"
        )
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        for forbidden in (
            "$APPOINTMENT_CONFIRMED$",
            "$POSITION_TYPE_ID$",
            "$POSITION_RECEIPT_ID$",
            "$POSITION_RECEIPT_HASH$",
            "$POSITION_TITLE$",
            "$HC_SOURCE$",
        ):
            self.assertNotIn(forbidden, wrapper + request)
        self.assertEqual(self.effects.count("APPOINTMENT_CONFIRMED = 1"), 1)
        publisher = block(self.effects, f"{gen.PREFIX}_seal_and_publish_effect")
        self.assertIn("APPOINTMENT_CONFIRMED = 1", publisher)

    def test_intent_does_not_write_alias_or_receipt_before_callback(self) -> None:
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        callback = block(
            self.effects, f"{gen.PREFIX}_on_native_position_received_effect"
        )
        for alias in (
            "zg361_we_ad_external_position_type_id",
            "zg361_we_ad_external_position_receipt_id",
            "zg361_we_ad_external_position_receipt_hash",
        ):
            self.assertNotIn(f"set_variable = {{ name = {alias}", self.effects)
            self.assertNotIn(alias, request)
            self.assertNotIn(alias, callback)
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_receipt_active", request)
        self.assertNotIn(f"set_variable = {{ name = {gen.PREFIX}_receipt_active", callback)
        self.assertIn(f"set_variable = {{ name = {gen.PREFIX}_pending_open", request)

    def test_receipt_binds_five_tuple_result_position_title_hc_and_objects(self) -> None:
        publisher = block(self.effects, f"{gen.PREFIX}_seal_and_publish_effect")
        required = (
            f"native_callback_seen = 1",
            f"receipt_owner value = $TICKET_OWNER$",
            f"receipt_subject value = $TICKET_SUBJECT$",
            f"receipt_cycle value = $TICKET_CYCLE$",
            f"receipt_case value = $TICKET_CASE$",
            f"receipt_state value = 4",
            f"receipt_result value = 1",
            f"receipt_position_type_id value = {gen.POSITION_TYPE_ID}",
            f"receipt_position_source_kind value = {gen.SOURCE_KIND_COURT_POSITION}",
            "receipt_title value = var:",
            "receipt_title_tier value = var:",
            "receipt_title_holder value = $TICKET_SUBJECT$",
            "receipt_hc_case value = var:",
            "receipt_hc_reserved_source value = var:",
            "receipt_offer_object value = var:",
            "receipt_candidate_object value = var:",
            "receipt_native_employer value = $TICKET_OWNER$",
            "receipt_id value = { value = $TICKET_CASE$ multiply = 1000 add = 274 }",
            "receipt_hash value = { value = $TICKET_CASE$ multiply = 100000",
        )
        for needle in required:
            self.assertIn(needle, publisher)
        self.assertIn("primary_title = var:", publisher)
        self.assertIn("holder = $TICKET_SUBJECT$", publisher)
        self.assertIn("is_court_position_employer = {", publisher)

    def test_request_joins_real_266_272_273_sources_before_native_action(self) -> None:
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        for mechanism_id in (266, 272, 273):
            for field in ("owner", "subject", "cycle", "case", "consumed"):
                self.assertIn(f"zg361_we_m{mechanism_id}_{'object_' if field != 'consumed' else 'object_'}{field}", request)
        self.assertIn("zg361_we_m266_hc_reservation_active = 1", request)
        self.assertIn("zg361_we_m266_hc_receipt = $TICKET_CASE$", request)
        self.assertIn("zg361_ch_hc_reserved >= 1", request)
        self.assertIn("zg361_we_m272_offer_candidate = $TICKET_SUBJECT$", request)
        self.assertIn("zg361_we_m273_candidate_fingerprint = $TICKET_SUBJECT$", request)
        self.assertIn("is_landed = yes", request)
        self.assertIn("liege = $TICKET_OWNER$", request)
        self.assertIn("primary_title = { holder = $TICKET_SUBJECT$ }", request)

    def test_exact_dispatched_attempt_cannot_appoint_again_without_callback(self) -> None:
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        dispatch_index = request.index(
            f"set_variable = {{ name = {gen.PREFIX}_native_attempt_dispatched value = 1 }}"
        )
        appoint_index = request.index("appoint_court_position = {")
        self.assertLess(dispatch_index, appoint_index)
        for field in ("owner", "subject", "cycle", "case"):
            self.assertIn(
                f"native_attempt_{field} value = $TICKET_{field.upper()}$", request
            )
        self.assertIn(f"has_variable = {gen.PREFIX}_native_attempt_dispatched", request)
        self.assertIn(f"var:{gen.PREFIX}_pending_open = 1", request)
        self.assertEqual(request.count("appoint_court_position = {"), 1)

    def test_strict_existing_adapter_is_the_only_alias_publisher(self) -> None:
        publisher = block(self.effects, f"{gen.PREFIX}_seal_and_publish_effect")
        self.assertEqual(
            publisher.count("zg361_we_submit_ad_appointment_receipt_effect = {"), 1
        )
        for needle in (
            f"POSITION_TYPE_ID = {gen.POSITION_TYPE_ID}",
            f"POSITION_RECEIPT_ID = var:{gen.PREFIX}_receipt_id",
            f"POSITION_RECEIPT_HASH = var:{gen.PREFIX}_receipt_hash",
            "APPOINTING_OWNER = $TICKET_OWNER$",
            "APPOINTMENT_CONFIRMED = 1",
        ):
            self.assertIn(needle, publisher)

    def test_delayed_seal_revalidates_hc_and_all_three_source_objects(self) -> None:
        publisher = block(self.effects, f"{gen.PREFIX}_seal_and_publish_effect")
        receipt_write = publisher.index(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_active value = 1 }}"
        )
        for needle in (
            "zg361_we_m266_hc_reservation_active = 1",
            "pending_hc_case = var:zg361_we_m266_hc_receipt",
            "pending_hc_reserved <= var:zg361_ch_hc_reserved",
            "pending_offer_object = var:zg361_we_m272_object_id",
            "pending_candidate_object = var:zg361_we_m273_object_id",
            "zg361_we_m272_offer_candidate = $TICKET_SUBJECT$",
            "zg361_we_m273_candidate_fingerprint = $TICKET_SUBJECT$",
        ):
            self.assertLess(publisher.index(needle), receipt_write)
        for mechanism_id in (266, 272, 273):
            for field in ("owner", "subject", "cycle", "case", "consumed"):
                needle = f"zg361_we_m{mechanism_id}_object_{field}"
                self.assertLess(publisher.index(needle), receipt_write)

    def test_position_is_picker_bounded_single_slot_and_released_after_consumer(self) -> None:
        position = block(self.position, gen.POSITION_KEY)
        consume = block(
            self.effects, f"{gen.PREFIX}_consume_workforce_m274_effect"
        )
        self.assertIn("max_available_positions = 1", position)
        self.assertIn(f"has_variable = {gen.PREFIX}_window_open", position)
        self.assertIn(f"var:{gen.PREFIX}_window_open = 1", position)
        self.assertIn("ai_position_score = { value = -1000 }", position)
        self.assertIn("ai_candidate_score = { value = -1000 }", position)
        self.assertIn("salary = { gold = 0 }", position)
        self.assertIn("received_salary = { gold = 0 }", position)
        release = block(
            self.effects, f"{gen.PREFIX}_release_bounded_position_effect"
        )
        route_index = consume.index("zg361_we_m274_route_a_effect = {")
        release_index = consume.index(f"{gen.PREFIX}_release_bounded_position_effect = {{")
        consumed_index = consume.index(
            f"set_variable = {{ name = {gen.PREFIX}_receipt_consumed value = 1 }}"
        )
        self.assertLess(route_index, release_index)
        self.assertLess(release_index, consumed_index)
        self.assertIn(f"revoke_court_position = {gen.POSITION_KEY}", release)
        dispatch_index = release.index("release_command_dispatched value = 1")
        revoke_index = release.index(f"revoke_court_position = {gen.POSITION_KEY}")
        proof_index = release.index("receipt_position_released_by_package value = 1")
        self.assertLess(dispatch_index, revoke_index)
        self.assertLess(revoke_index, proof_index)
        self.assertIn("NOT = { has_court_position", consume)
        self.assertIn("receipt_position_release_joined_by_consumer value = 1", consume)
        self.assertIn("receipt_position_released_by_package = 1", consume)
        self.assertIn("workforce_consumer_ack = 1", consume)
        self.assertIn("zg361_we_m274_object_consumed = 1", consume)
        applied_write = "set_variable = { name = zg361_we_runtime_applied value = 1 }"
        self.assertEqual(consume.count(applied_write), 1)
        self.assertLess(consumed_index, consume.index(applied_write))
        self.assertGreaterEqual(
            consume.count("remove_variable = zg361_we_runtime_applied"), 3
        )
        persistent_ack = consume[:route_index]
        self.assertNotIn("zg361_we_runtime_applied = 1", persistent_ack)

    def test_replay_is_idempotent_and_never_reappoints(self) -> None:
        wrapper = block(
            self.effects, f"{gen.PREFIX}_m274_appoint_and_consume_effect"
        )
        clear_index = wrapper.index("remove_variable = zg361_we_runtime_applied")
        first_if_index = wrapper.index("if = {")
        self.assertLess(clear_index, first_if_index)
        duplicate_index = wrapper.index(f"receipt_consumed = 1")
        status_index = wrapper.index(f"status value = 2")
        request_index = wrapper.index(f"{gen.PREFIX}_request_native_appointment_effect")
        self.assertLess(duplicate_index, status_index)
        self.assertLess(status_index, request_index)
        self.assertNotIn("appoint_court_position = {", wrapper)

    def test_audit_is_fail_closed_and_cannot_consume_or_appoint(self) -> None:
        audit = block(self.effects, f"{gen.PREFIX}_audit_pending_effect")
        consumed_noop = audit.index(f"var:{gen.PREFIX}_receipt_consumed = 1")
        pending_branch = audit.index(f"var:{gen.PREFIX}_pending_open = 1")
        self.assertLess(consumed_noop, pending_branch)
        self.assertIn(f"var:{gen.PREFIX}_receipt_published = 1", audit)
        self.assertIn(f"{gen.PREFIX}_release_bounded_position_effect = {{", audit)
        self.assertIn("RELEASE_REASON = 2", audit)
        self.assertIn("RELEASE_REASON = 3", audit)
        self.assertGreaterEqual(audit.count("RELEASE_REASON = 3"), 2)
        self.assertIn(
            f"NOT = {{\n                    AND = {{\n                        has_variable = {gen.PREFIX}_receipt_active",
            audit,
        )
        self.assertIn("native_callback_seen = 1", audit)
        self.assertIn("has_court_position =", audit)
        self.assertIn("is_court_position_employer = {", audit)
        self.assertNotIn("appoint_court_position = {", audit)
        self.assertNotIn("zg361_we_m274_route_a_effect", audit)
        self.assertIn(f"red_code value = 27403", audit)
        event = block(self.events, f"{gen.NAMESPACE}.{gen.AUDIT_EVENT_ID}")
        self.assertIn("hidden = yes", event)
        self.assertIn(f"{gen.PREFIX}_audit_pending_effect = yes", event)
        self.assertIn("zg361_we_resume_m274_after_native_appointment_effect = {", event)
        for field in ("owner", "cycle", "case"):
            self.assertIn(
                f"TICKET_{field.upper()} = var:{gen.PREFIX}_receipt_{field}", event
            )
        self.assertIn("TICKET_SUBJECT = this", event)
        resume_index = event.index(
            "zg361_we_resume_m274_after_native_appointment_effect = {"
        )
        audit_index = event.index(f"{gen.PREFIX}_audit_pending_effect = yes")
        self.assertLess(audit_index, resume_index)
        self.assertIn(f"var:{gen.PREFIX}_status = 5", event[:resume_index])
        self.assertIn(f"var:{gen.PREFIX}_receipt_published = 1", event[:resume_index])
        self.assertIn(f"var:{gen.PREFIX}_receipt_consumed = 0", event[:resume_index])
        self.assertIn(f"var:{gen.PREFIX}_status = 5", event[resume_index:])
        self.assertIn(f"{gen.PREFIX}_schedule_audit_effect = yes", event[resume_index:])

    def test_wait_retry_is_single_flight_and_success_does_not_reappoint(self) -> None:
        schedule = block(self.effects, f"{gen.PREFIX}_schedule_audit_effect")
        callback = block(
            self.effects, f"{gen.PREFIX}_on_native_position_received_effect"
        )
        request = block(
            self.effects, f"{gen.PREFIX}_request_native_appointment_effect"
        )
        event = block(self.events, f"{gen.NAMESPACE}.{gen.AUDIT_EVENT_ID}")
        self.assertIn(f"has_variable = {gen.PREFIX}_audit_scheduled", schedule)
        self.assertIn(f"var:{gen.PREFIX}_audit_scheduled = 0", schedule)
        self.assertEqual(1, schedule.count("trigger_event = {"))
        self.assertNotIn("appoint_court_position", schedule)
        self.assertIn(f"{gen.PREFIX}_schedule_audit_effect = yes", callback)
        self.assertIn(f"{gen.PREFIX}_schedule_audit_effect = yes", request)
        self.assertNotIn("trigger_event = {", callback)
        self.assertNotIn("trigger_event = {", request)
        self.assertLess(
            event.index(f"name = {gen.PREFIX}_audit_scheduled value = 0"),
            event.index(f"{gen.PREFIX}_audit_pending_effect = yes"),
        )
        self.assertNotIn("appoint_court_position", event)
        self.assertNotIn("zg361_we_m274_route_a_effect", event)

    def test_typed_red_codes_cover_preflight_callback_adapter_consumer_release(self) -> None:
        for code in range(27401, 27408):
            self.assertIn(f"red_code value = {code}", self.effects)
        self.assertIn("status value = 4", self.effects)
        self.assertIn("status value = 5", self.effects)
        self.assertIn("status value = 6", self.effects)

    def test_spec_is_honest_about_static_readiness_ui_and_completed_wiring(self) -> None:
        self.assertIn("CK3 script static-ready; not loader-live or production-live", self.spec)
        self.assertIn("claim zero UI impact", self.spec)
        self.assertIn("both call this\npackage's wrapper", self.spec)
        self.assertIn("hidden event 9001 calls", self.spec)
        self.assertIn("exact continuation receipt", self.spec)
        self.assertIn("does not prove promotion to an unrelated vanilla title", self.spec)
        self.assertIn("shared ledger records these three fields as static-closed", self.spec)
        for alias in (
            "zg361_we_ad_external_position_type_id",
            "zg361_we_ad_external_position_receipt_id",
            "zg361_we_ad_external_position_receipt_hash",
        ):
            self.assertIn(alias, self.spec)

    def test_generated_paradox_files_have_balanced_braces(self) -> None:
        for path, source in (
            (gen.EFFECTS_PATH, self.effects),
            (gen.EVENTS_PATH, self.events),
            (gen.POSITION_PATH, self.position),
        ):
            self.assertEqual(source.count("{"), source.count("}"), path)


if __name__ == "__main__":
    unittest.main()

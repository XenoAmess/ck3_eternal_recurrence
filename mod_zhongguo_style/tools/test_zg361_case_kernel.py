#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 source-contract tests for the shared 361 CK3 case kernel."""

from __future__ import annotations

import hashlib
import re
import unittest

from gen_361_case_kernel import (
    EFFECT_GROUPS,
    EFFECT_HARD_MAX,
    EFFECT_PATHS,
    EFFECT_SHARD_GLOB,
    EFFECT_TARGET_MAX,
    HEADER,
    HISTORICAL_EFFECT_BYTES,
    HISTORICAL_EFFECT_COUNT,
    HISTORICAL_EFFECT_SHA256,
    LEGACY_EFFECT_PATH,
    SCRIPTED_EFFECTS_DIR,
    TRIGGERS_PATH,
    effect_outputs,
    outputs,
    render_legacy_effects,
    validate_effect_groups,
)
from zg361_domain_data import DOMAIN_SPECS


def _block(text: str, key: str) -> str:
    marker = f"{key} = {{"
    start = text.index(marker)
    cursor = start + len(marker)
    depth = 1
    while cursor < len(text) and depth:
        if text[cursor] == "{":
            depth += 1
        elif text[cursor] == "}":
            depth -= 1
        cursor += 1
    if depth:
        raise AssertionError(f"unbalanced block {key}")
    return text[start:cursor]


class CaseKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rendered = outputs()
        cls.effect_shards = effect_outputs()
        cls.effects = render_legacy_effects()
        cls.triggers = cls.rendered[TRIGGERS_PATH]

    def test_generated_files_are_current_and_bom_encoded(self) -> None:
        for path, expected in self.rendered.items():
            with self.subTest(path=path.name):
                self.assertTrue(path.exists())
                self.assertEqual(path.read_text(encoding="utf-8-sig"), expected)
                self.assertEqual(path.read_bytes()[:3], b"\xef\xbb\xbf")

        self.assertFalse(LEGACY_EFFECT_PATH.exists())
        self.assertEqual(set(SCRIPTED_EFFECTS_DIR.glob(EFFECT_SHARD_GLOB)), set(EFFECT_PATHS))

    def test_effects_are_purpose_split_within_file_boundaries(self) -> None:
        validate_effect_groups()
        self.assertEqual(len(EFFECT_GROUPS), 39)
        self.assertEqual(sum(len(group.effect_names) for group in EFFECT_GROUPS), HISTORICAL_EFFECT_COUNT)
        for group, path in zip(EFFECT_GROUPS, EFFECT_PATHS, strict=True):
            with self.subTest(path=path.name, purpose=group.purpose):
                count = len(group.effect_names)
                self.assertGreaterEqual(count, 1)
                self.assertLessEqual(count, EFFECT_TARGET_MAX)
                self.assertLessEqual(count, EFFECT_HARD_MAX)
                actual_names = tuple(
                    re.findall(r"(?m)^([a-z0-9_]+) = \{$", self.effect_shards[path])
                )
                self.assertEqual(actual_names, group.effect_names)

    def test_split_preserves_historical_effect_bodies_and_order(self) -> None:
        legacy = render_legacy_effects()
        legacy_bytes = legacy.encode("utf-8-sig")
        self.assertEqual(len(legacy_bytes), HISTORICAL_EFFECT_BYTES)
        self.assertEqual(hashlib.sha256(legacy_bytes).hexdigest().upper(), HISTORICAL_EFFECT_SHA256)

        reconstructed = self.effect_shards[EFFECT_PATHS[0]] + "".join(
            self.effect_shards[path][len(HEADER) :] for path in EFFECT_PATHS[1:]
        )
        self.assertEqual(reconstructed, legacy)

    def test_every_domain_has_one_open_and_all_stage_dispatchers(self) -> None:
        for domain in DOMAIN_SPECS:
            slug = domain.code.lower()
            self.assertEqual(self.effects.count(f"zg361_case_{slug}_open_effect = {{"), 1)
            for index, (_old, _new, hook) in enumerate(domain.transitions, start=1):
                block = _block(self.effects, f"zg361_case_{slug}_advance_{index:02d}_effect")
                self.assertIn(f"TICKET_STATE = {index}", block)
                self.assertIn(f"NEXT_STATE = {index + 1}", block)
                self.assertIn(f"on {hook}", self.effects)
            self.assertNotIn(f"zg361_case_{slug}_advance_{len(domain.transitions) + 1:02d}_effect", self.effects)

    def test_open_permission_is_duke_plus_celestial_for_player_or_ai(self) -> None:
        block = _block(self.triggers, "zg361_case_kernel_can_open_trigger")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", block)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", block)
        self.assertIn("liege = root", block)
        self.assertNotIn("is_ai = no", block)
        self.assertNotIn("is_ai = yes", block)

    def test_full_guard_binds_all_five_identity_fields_before_reads(self) -> None:
        block = _block(self.triggers, "zg361_case_kernel_full_guard_trigger")
        for token in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE"):
            self.assertIn(f"has_variable = ${token}_VAR$", block)
            self.assertIn(f"var:${token}_VAR$ = $EXPECTED_{token}$", block)
        self.assertLess(block.index("limit = {"), block.index("var:$OWNER_VAR$"))
        self.assertIn("var:$ACTIVE_VAR$ = 1", block)

    def test_subject_self_guard_grants_no_management_authority(self) -> None:
        block = _block(self.triggers, "zg361_case_kernel_subject_self_guard_trigger")
        self.assertIn("var:$SUBJECT_VAR$ = this", block)
        for forbidden in ("celestial_liege", "cohort", "calibr", "pip", "hc_slot"):
            self.assertNotIn(forbidden, block.lower())

    def test_operation_receipt_is_idempotent_and_does_not_transition(self) -> None:
        block = _block(self.effects, "zg361_case_kernel_record_operation_effect")
        self.assertIn("NOT = {", block)
        self.assertIn("zg361_case_kernel_receipt_is_current_trigger", block)
        for token in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE", "CHOICE"):
            self.assertIn(f"name = $RECEIPT_{token}_VAR$", block)
        self.assertNotIn("name = $STATE_VAR$ value = $NEXT_STATE$", block)
        self.assertIn("change_variable = { name = $REVISION_VAR$ add = 1 }", block)

    def test_only_stage_transition_changes_case_state(self) -> None:
        transition = _block(self.effects, "zg361_case_kernel_transition_effect")
        self.assertIn("name = $STATE_VAR$ value = $NEXT_STATE$", transition)
        self.assertIn("always = $CLOSE_CASE$", transition)
        self.assertIn("name = $ACTIVE_VAR$ value = 0", transition)
        before_wrappers = self.effects[: self.effects.index("# A:")]
        state_writers = re.findall(r"name = \$STATE_VAR\$ value = \$NEXT_STATE\$", before_wrappers)
        self.assertEqual(len(state_writers), 1)

    def test_deadline_binds_five_fields_and_schedules_real_event(self) -> None:
        schedule = _block(self.effects, "zg361_case_kernel_schedule_deadline_effect")
        for token in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE"):
            self.assertIn(f"name = $DEADLINE_{token}_VAR$ value = $TICKET_{token}$", schedule)
        self.assertIn("trigger_event = { id = $EVENT$ days = $DAYS$ }", schedule)
        expire = _block(self.effects, "zg361_case_kernel_expire_deadline_effect")
        self.assertIn("zg361_case_kernel_deadline_is_current_trigger", expire)
        self.assertIn("name = $DEADLINE_EXPIRED_VAR$ value = 1", expire)

    def test_transaction_is_atomic_receipt_bound_and_single_settlement(self) -> None:
        reserve = _block(self.effects, "zg361_case_kernel_reserve_transaction_effect")
        self.assertLess(reserve.index("var:$AVAILABLE_VAR$ >= $AMOUNT$"), reserve.index("change_variable = { name = $AVAILABLE_VAR$"))
        self.assertIn("zg361_case_kernel_positive_amount_trigger = { AMOUNT = $AMOUNT$ }", reserve)
        positive = _block(self.triggers, "zg361_case_kernel_positive_amount_trigger")
        self.assertIn("value = $AMOUNT$", positive)
        self.assertIn("scope:zg361_case_kernel_amount > 0", positive)
        self.assertIn("name = $RECEIPT_STATUS_VAR$ value = 1", reserve)
        settle = _block(self.effects, "zg361_case_kernel_settle_transaction_effect")
        self.assertIn("var:$RECEIPT_STATUS_VAR$ = 1", settle)
        self.assertIn("name = $RECEIPT_STATUS_VAR$ value = 2", settle)
        refund = _block(self.effects, "zg361_case_kernel_refund_transaction_effect")
        self.assertIn("var:$RECEIPT_STATUS_VAR$ = 1", refund)
        self.assertIn("var:$RECEIPT_STATUS_VAR$ = 2", refund)
        self.assertIn("name = $RECEIPT_STATUS_VAR$ value = 3", refund)

    def test_kernel_contains_no_gui_or_release_claim(self) -> None:
        joined = self.effects + self.triggers
        for forbidden in ("hud", "widget", "domain_runtime = complete", "fixture-live", "production-live"):
            self.assertNotIn(forbidden, joined.lower())


if __name__ == "__main__":
    unittest.main()

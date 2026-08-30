#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L0 contracts for the generated D/M/N/O/P/Q CK3 runtime.

These tests establish deterministic source, guards, receipts, state barriers
and resource projections.  They are not CK3 parsing or live-game evidence.
"""

from __future__ import annotations

from pathlib import Path
import re
import unittest

import gen_361_career_hc_runtime as generator
import zg361_phase2_career_model as model


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = MOD_ROOT / "common/scripted_effects/zg361_career_hc_runtime_effects.txt"
EVENTS_PATH = MOD_ROOT / "events/zg361_career_hc_runtime_events.txt"


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


class CareerHcRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = EFFECTS_PATH.read_text(encoding="utf-8-sig")
        cls.events = EVENTS_PATH.read_text(encoding="utf-8-sig")

    def test_exact_forty_four_numbered_mechanisms(self) -> None:
        expected = tuple((*range(19, 26), *range(92, 129)))
        self.assertEqual(generator.EXPECTED_IDS, expected)
        self.assertEqual(tuple(sorted(generator.DOMAIN_BY_ID)), expected)
        self.assertEqual(len(expected), 44)
        self.assertTrue(set(expected) <= set(model.MECHANISM_BEHAVIORS))

    def test_six_domain_stage_partitions_are_frozen(self) -> None:
        expected = {
            "d": ((19, 20), (21, 22), (23, 24), (25,)),
            "m": ((92, 93), (94,), (95, 96), (97,)),
            "n": ((98, 99), (100, 101), (102, 103), (104, 105)),
            "o": ((106, 107), (108, 109), (110, 111), (112,), (113,)),
            "p": ((114, 115), (116,), (117, 118), (119,), (120,)),
            "q": ((121, 122), (123, 124), (125, 126), (127, 128)),
        }
        self.assertEqual({row.key: row.stages for row in generator.DOMAINS}, expected)
        self.assertEqual(
            {mechanism_id: stage for mechanism_id, stage in generator.STAGE_BY_ID.items()},
            {
                mechanism_id: stage
                for domain in generator.DOMAINS
                for stage, ids in enumerate(domain.stages, start=1)
                for mechanism_id in ids
            },
        )

    def test_generated_outputs_are_current_bom_and_complete(self) -> None:
        rendered = generator.outputs()
        self.assertEqual(len(rendered), 11)
        self.assertEqual(
            {path.parent.name for path in rendered if path.suffix == ".yml"},
            {
                "english",
                "simp_chinese",
                "french",
                "german",
                "japanese",
                "korean",
                "polish",
                "russian",
                "spanish",
            },
        )
        for path, payload in rendered.items():
            with self.subTest(path=path.name):
                self.assertTrue(payload.startswith(generator.BOM))
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), payload)

    def test_generated_ck3_files_have_balanced_braces(self) -> None:
        self.assertEqual(brace_balance(self.effects), 0)
        self.assertEqual(brace_balance(self.events), 0)

    def test_top_level_effect_and_event_definitions_are_unique(self) -> None:
        manager_defs = re.findall(
            r"(?m)^zg361_career_hc_m\d{3}_manager_apply_effect = \{",
            self.effects,
        )
        self.assertEqual(len(manager_defs), 44)
        event_ids = re.findall(r"(?m)^zg361ch\.(\d+) = \{", self.events)
        expected_events = (
            44
            + sum(len(domain.stages) for domain in generator.DOMAINS)
            + 1
            + len(generator.QUEUE_EVENTS)
            + len(generator.DOMAINS)
        )
        self.assertEqual(len(event_ids), expected_events)
        self.assertEqual(len(event_ids), len(set(event_ids)))

    def test_every_domain_has_one_guarded_open_and_no_gui_surface(self) -> None:
        for domain in generator.DOMAINS:
            with self.subTest(domain=domain.key):
                source = block(self.effects, f"zg361_career_hc_open_{domain.key}_case_effect")
                self.assertIn("root = {", source)
                self.assertIn("zg361_is_celestial_liege_trigger = yes", source)
                self.assertIn("zg361_is_reviewable_vassal_trigger = yes", source)
                self.assertIn("liege = root", source)
                self.assertIn(f"zg361_case_{domain.key}_open_effect = yes", source)
                self.assertIn(f"zg361_ch_{domain.key}_authorized", source)
                self.assertIn(f"zg361_ch_{domain.key}_conserved", source)
        q_open = block(self.effects, "zg361_career_hc_open_q_case_effect")
        self.assertGreaterEqual(q_open.count("zg361_is_celestial_liege_trigger = yes"), 2)
        self.assertNotIn("gui/", self.effects.lower())
        self.assertNotIn("scripted_widget", self.effects.lower())

    def test_one_manager_scope_portfolio_adapter_opens_only_first_eligible_d_case(self) -> None:
        adapter = block(self.effects, "zg361_career_hc_open_portfolio_effect")
        self.assertEqual(
            len(
                re.findall(
                    r"(?m)^zg361_career_hc_open_portfolio_effect = \{",
                    self.effects,
                )
            ),
            1,
        )
        self.assertIn("has_game_rule = zg361_on", adapter)
        self.assertIn("zg361_is_celestial_liege_trigger = yes", adapter)
        self.assertIn("has_variable = zg361_review_serial", adapter)
        self.assertIn("any_vassal = {", adapter)
        self.assertEqual(adapter.count("ordered_vassal = {"), 1)
        self.assertIn("position = 0", adapter)
        self.assertIn("order_by = stewardship", adapter)
        self.assertEqual(
            adapter.count("zg361_career_hc_open_d_case_effect = yes"),
            1,
        )
        for domain in generator.DOMAIN_ORDER[1:]:
            self.assertNotIn(
                f"zg361_career_hc_open_{domain}_case_effect = yes",
                adapter,
            )
        self.assertIn("zg361_ch_manager_portfolio_cycle", adapter)
        self.assertIn(
            "NOT = { var:zg361_ch_manager_portfolio_cycle = var:zg361_review_serial }",
            adapter,
        )
        self.assertIn("zg361_ch_portfolio_cycle", adapter)
        for domain in generator.DOMAIN_ORDER:
            self.assertIn(f"has_variable = zg361_case_{domain}_active", adapter)
            self.assertIn(f"var:zg361_case_{domain}_active = 0", adapter)
        self.assertNotIn("is_ai = no", adapter)

    def test_open_launches_one_player_card_d_plus_one_or_ai_background(self) -> None:
        for domain in generator.DOMAINS:
            opened = block(
                self.effects,
                f"zg361_career_hc_open_{domain.key}_case_effect",
            )
            first = generator.domain_mechanisms(domain)[0]
            with self.subTest(domain=domain.key):
                self.assertIn(f"save_scope_as = zg361_ch_{domain.key}_event_owner", opened)
                self.assertIn(f"save_scope_as = zg361_ch_{domain.key}_event_subject", opened)
                self.assertIn(f"save_scope_value_as = {{ name = zg361_ch_{domain.key}_event_cycle", opened)
                self.assertEqual(
                    opened.count(f"trigger_event = {{ id = zg361ch.{first} days = 1 }}"),
                    1,
                )
                self.assertIn("is_ai = no", opened)
                self.assertIn("is_ai = yes", opened)
                self.assertIn(
                    f"zg361_career_hc_{domain.key}_run_authorized_ai_effect = yes",
                    opened,
                )

    def test_every_manager_entry_uses_canonical_duke_plus_guard(self) -> None:
        for mechanism_id in generator.EXPECTED_IDS:
            domain = generator.DOMAIN_BY_ID[mechanism_id].key
            state = generator.STAGE_BY_ID[mechanism_id]
            with self.subTest(mechanism=mechanism_id):
                source = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect",
                )
                self.assertIn("root = { zg361_is_celestial_liege_trigger = yes }", source)
                self.assertIn("zg361_is_reviewable_vassal_trigger = yes", source)
                self.assertIn("liege = root", source)
                self.assertIn("zg361_case_kernel_full_guard_trigger", source)
                self.assertIn("EXPECTED_OWNER = root", source)
                self.assertIn(f"EXPECTED_STATE = {state}", source)
                self.assertIn(
                    f"zg361_career_hc_m{mechanism_id:03d}_core_effect",
                    source,
                )
                if domain == "q":
                    self.assertGreaterEqual(
                        source.count("zg361_is_celestial_liege_trigger = yes"), 2
                    )

    def test_every_core_has_five_field_guard_and_single_use_receipt(self) -> None:
        for mechanism_id in generator.EXPECTED_IDS:
            domain = generator.DOMAIN_BY_ID[mechanism_id].key
            with self.subTest(mechanism=mechanism_id):
                source = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_core_effect",
                )
                for field in (
                    "OWNER_VAR",
                    "SUBJECT_VAR",
                    "CYCLE_VAR",
                    "CASE_VAR",
                    "STATE_VAR",
                ):
                    self.assertIn(field, source)
                self.assertIn("zg361_case_kernel_record_operation_effect", source)
                self.assertIn(f"OPERATION_ID = {mechanism_id}", source)
                self.assertIn(f"zg361_ch_m{mechanism_id:03d}_receipt_active", source)
                self.assertIn("CHOICE = $ROUTE$", source)
                self.assertIn("scope:zg361_ch_route = 1", source)
                self.assertIn("scope:zg361_ch_route = 2", source)
                self.assertIn("scope:zg361_ch_route = 3", source)
                self.assertIn(
                    f"zg361_career_hc_m{mechanism_id:03d}_consume_effect = yes",
                    source,
                )
                self.assertIn(f"zg361_case_{domain}_owner", source)

    def test_each_numbered_write_has_a_unique_consumer_projection(self) -> None:
        for mechanism_id in generator.EXPECTED_IDS:
            domain = generator.DOMAIN_BY_ID[mechanism_id].key
            state = generator.STAGE_BY_ID[mechanism_id]
            with self.subTest(mechanism=mechanism_id):
                source = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_consume_effect",
                )
                self.assertIn(f"zg361_ch_m{mechanism_id:03d}_value", source)
                self.assertIn(f"zg361_ch_m{mechanism_id:03d}_consumed value = 1", source)
                self.assertIn(f"zg361_ch_{domain}_completed", source)
                self.assertIn(f"zg361_ch_{domain}_capacity_partition", source)
                self.assertIn(f"zg361_ch_{domain}_conserved", source)
                self.assertIn(
                    f"zg361_career_hc_{domain}_try_advance_{state:02d}_effect",
                    source,
                )
                semantic_projection = generator.special_payload(mechanism_id).split("\n", 1)[0]
                self.assertIn(semantic_projection, source)

    def test_stage_barriers_consume_all_receipts_before_single_dispatch(self) -> None:
        for domain in generator.DOMAINS:
            for state, ids in enumerate(domain.stages, start=1):
                with self.subTest(domain=domain.key, state=state):
                    source = block(
                        self.effects,
                        f"zg361_career_hc_{domain.key}_try_advance_{state:02d}_effect",
                    )
                    for mechanism_id in ids:
                        self.assertIn(
                            f"var:zg361_ch_m{mechanism_id:03d}_consumed = 1",
                            source,
                        )
                    self.assertEqual(
                        source.count(f"zg361_case_{domain.key}_advance_{state:02d}_effect"),
                        1,
                    )
                    if state == len(domain.stages):
                        self.assertIn(
                            f"zg361_career_hc_resolve_{domain.key}_outcome_effect",
                            source,
                        )
                    else:
                        self.assertIn(
                            f"zg361_career_hc_schedule_{domain.key}_stage_{state + 1:02d}_effect",
                            source,
                        )

    def test_exact_deadline_tickets_and_route_c_timeout_are_total(self) -> None:
        expected_deadline_hidden = sum(
            len(domain.stages) for domain in generator.DOMAINS
        ) + 1
        expected_hidden = expected_deadline_hidden + len(generator.QUEUE_EVENTS)
        self.assertEqual(self.events.count("hidden = yes"), expected_hidden)
        self.assertEqual(
            self.events.count("zg361_case_kernel_expire_deadline_effect"),
            expected_deadline_hidden,
        )
        for domain in generator.DOMAINS:
            for state, ids in enumerate(domain.stages, start=1):
                with self.subTest(domain=domain.key, state=state):
                    timeout = block(
                        self.effects,
                        f"zg361_career_hc_{domain.key}_timeout_stage_{state:02d}_effect",
                    )
                    for mechanism_id in ids:
                        self.assertIn(
                            f"zg361_career_hc_m{mechanism_id:03d}_core_effect = {{ ROUTE = 3 }}",
                            timeout,
                        )
        self.assertIn("var:zg361_ch_release_days = 90", self.effects)
        self.assertIn("var:zg361_ch_release_days = 150", self.effects)
        self.assertIn("DAYS = 90", self.effects)
        self.assertIn("DAYS = 150", self.effects)

    def test_player_business_windows_are_serial_d_plus_one_with_five_field_guards(self) -> None:
        self.assertEqual(self.events.count("# Player manager business window #"), 44)
        self.assertEqual(self.events.count("theme = stewardship"), 44)
        for domain in generator.DOMAINS:
            mechanisms = generator.domain_mechanisms(domain)
            for index, mechanism_id in enumerate(mechanisms):
                event = block(self.events, f"zg361ch.{mechanism_id}")
                with self.subTest(domain=domain.key, mechanism=mechanism_id):
                    self.assertIn("is_ai = no", event)
                    self.assertIn("zg361_case_kernel_full_guard_trigger", event)
                    for field in (
                        "OWNER_VAR",
                        "SUBJECT_VAR",
                        "CYCLE_VAR",
                        "CASE_VAR",
                        "STATE_VAR",
                    ):
                        self.assertIn(field, event)
                    self.assertEqual(
                        event.count(f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect"),
                        3,
                    )
                    for route in (1, 2, 3):
                        self.assertIn(f"ROUTE = {route}", event)
                    if index + 1 < len(mechanisms):
                        successor = mechanisms[index + 1]
                        self.assertEqual(
                            event.count(
                                f"trigger_event = {{ id = zg361ch.{successor} days = 1 }}"
                            ),
                            3,
                        )
                    elif generator.NEXT_DOMAIN[domain.key] is not None:
                        queue_event = generator.QUEUE_EVENTS[domain.key]
                        self.assertEqual(
                            event.count(
                                f"trigger_event = {{ id = zg361ch.{queue_event} days = 1 }}"
                            ),
                            3,
                        )
                    else:
                        self.assertEqual(
                            event.count(
                                "zg361_career_hc_finalize_q_portfolio_effect = yes"
                            ),
                            3,
                        )

    def test_cross_domain_queue_edges_are_hidden_closed_identity_guards(self) -> None:
        for domain in generator.DOMAINS[:-1]:
            event_id = generator.QUEUE_EVENTS[domain.key]
            queued = block(self.events, f"zg361ch.{event_id}")
            next_domain = generator.NEXT_DOMAIN[domain.key]
            final_state = len(domain.stages) + 1
            with self.subTest(domain=domain.key):
                self.assertIn("hidden = yes", queued)
                self.assertIn(f"var:zg361_case_{domain.key}_owner", queued)
                self.assertIn(f"var:zg361_case_{domain.key}_subject", queued)
                self.assertIn(f"var:zg361_case_{domain.key}_cycle_serial", queued)
                self.assertIn(f"var:zg361_case_{domain.key}_case_serial", queued)
                self.assertIn(f"var:zg361_case_{domain.key}_state = {final_state}", queued)
                self.assertIn(f"var:zg361_case_{domain.key}_active = 0", queued)
                self.assertIn(
                    f"zg361_career_hc_open_{next_domain}_case_effect = yes",
                    queued,
                )
        p_queue = block(self.events, f"zg361ch.{generator.QUEUE_EVENTS['p']}")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", p_queue)
        self.assertIn("zg361_career_hc_finalize_p_portfolio_effect = yes", p_queue)

    def test_authorized_ai_consumes_receipts_without_visible_business_events(self) -> None:
        for domain in generator.DOMAINS:
            runner = block(
                self.effects,
                f"zg361_career_hc_{domain.key}_run_authorized_ai_effect",
            )
            with self.subTest(domain=domain.key):
                for mechanism_id in generator.domain_mechanisms(domain):
                    self.assertIn(
                        f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect",
                        runner,
                    )
                    self.assertIsNone(
                        re.search(rf"id = zg361ch\.{mechanism_id}(?:\s|\}})", runner)
                    )
                    if mechanism_id in generator.DUAL_COST_IDS:
                        self.assertIn(
                            f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = 3 }}",
                            runner,
                        )
                if generator.NEXT_DOMAIN[domain.key] is not None:
                    self.assertIn(
                        f"id = zg361ch.{generator.QUEUE_EVENTS[domain.key]} days = 1",
                        runner,
                    )
                else:
                    self.assertIn(
                        "zg361_career_hc_finalize_q_portfolio_effect = yes",
                        runner,
                    )

    def test_player_funded_routes_cannot_close_an_unpayable_business_card(self) -> None:
        for mechanism_id in generator.DUAL_COST_IDS:
            event = block(self.events, f"zg361ch.{mechanism_id}")
            with self.subTest(mechanism=mechanism_id):
                self.assertEqual(event.count("treasury >= 5"), 2)
                self.assertEqual(event.count("gold >= 5"), 2)
                self.assertEqual(
                    event.count("government_has_flag = government_has_treasury"),
                    4,
                )
                self.assertIn(
                    f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect = {{ ROUTE = 3 }}",
                    event,
                )

    def test_portfolio_finalizers_require_closed_frozen_identity(self) -> None:
        for domain in (generator.DOMAIN_BY_KEY["p"], generator.DOMAIN_BY_KEY["q"]):
            finalizer = block(
                self.effects,
                f"zg361_career_hc_finalize_{domain.key}_portfolio_effect",
            )
            with self.subTest(domain=domain.key):
                for field in ("owner", "subject", "cycle_serial", "case_serial"):
                    self.assertIn(f"zg361_case_{domain.key}_{field}", finalizer)
                self.assertIn(
                    f"var:zg361_case_{domain.key}_state = {len(domain.stages) + 1}",
                    finalizer,
                )
                self.assertIn(f"var:zg361_case_{domain.key}_active = 0", finalizer)
                self.assertIn("zg361_ch_manager_portfolio_active value = 0", finalizer)

    def test_new_case_resets_stage_deadline_latches(self) -> None:
        for domain in generator.DOMAINS:
            opened = block(
                self.effects,
                f"zg361_career_hc_open_{domain.key}_case_effect",
            )
            for state in range(1, len(domain.stages) + 1):
                suffixes = ("a", "b") if domain.key == "p" and state == 3 else ("x",)
                for suffix in suffixes:
                    with self.subTest(domain=domain.key, state=state, suffix=suffix):
                        self.assertIn(
                            f"zg361_ch_{domain.key}_s{state}_{suffix}_deadline_pending value = 0",
                            opened,
                        )
                        self.assertIn(
                            f"zg361_ch_{domain.key}_s{state}_{suffix}_deadline_expired value = 0",
                            opened,
                        )

    def test_defer_route_does_not_apply_business_success_payload(self) -> None:
        for mechanism_id in generator.EXPECTED_IDS:
            source = block(
                self.effects,
                f"zg361_career_hc_m{mechanism_id:03d}_consume_effect",
            )
            with self.subTest(mechanism=mechanism_id):
                if mechanism_id == 23:
                    self.assertIn("jingcha_treasury_delta value = 0", source)
                elif mechanism_id == 116:
                    self.assertIn(
                        f"NOT = {{ var:zg361_ch_m{mechanism_id:03d}_route = 3 }}",
                        source,
                    )
                    self.assertIn("release_days value = 90", source)
                    self.assertIn("release_extension_used value = 0", source)
                else:
                    semantic = generator.special_payload(mechanism_id).split("\n", 1)[0]
                    guard = (
                        f"NOT = {{ var:zg361_ch_m{mechanism_id:03d}_route = 3 }}"
                    )
                    self.assertIn(guard, source)
                    self.assertLess(source.find(guard), source.find(semantic))

    def test_dual_costs_use_two_shared_journals_and_real_ck3_transfer(self) -> None:
        for mechanism_id in generator.DUAL_COST_IDS:
            with self.subTest(mechanism=mechanism_id):
                source = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_core_effect",
                )
                self.assertEqual(
                    source.count("zg361_case_kernel_reserve_transaction_effect"), 2
                )
                self.assertEqual(
                    source.count("zg361_case_kernel_settle_transaction_effect"), 2
                )
                self.assertIn("treasury >= 5", source)
                self.assertIn("gold >= 5", source)
                self.assertIn("remove_treasury = 5", source)
                self.assertIn("add_gold = { value = 0 subtract = 5 }", source)
                self.assertIn("add_treasury = 5", source)
                self.assertIn("add_gold = 5", source)
                self.assertIn("dual_payment_settled", source)

    def test_jingcha_hc_defense_is_explicitly_free(self) -> None:
        core = block(self.effects, "zg361_career_hc_m023_core_effect")
        consumer = block(self.effects, "zg361_career_hc_m023_consume_effect")
        self.assertNotIn("remove_treasury", core)
        self.assertNotIn("subtract = 5", core)
        self.assertIn("zg361_ch_jingcha_treasury_delta value = 0", consumer)
        self.assertIn("zg361_ch_jingcha_personal_delta value = 0", consumer)
        self.assertIn("zg361_ch_hc_defense_year value = current_year", consumer)

    def test_hc_partition_is_eight_units_and_never_minted(self) -> None:
        opened = block(self.effects, "zg361_career_hc_open_n_case_effect")
        self.assertIn("zg361_ch_hc_authorized value = 8", opened)
        self.assertIn("zg361_ch_hc_available value = 8", opened)
        for name in ("reserved", "occupied", "frozen", "reclaimed"):
            self.assertIn(f"zg361_ch_hc_{name} value = 0", opened)
        for mechanism_id in range(98, 106):
            source = block(
                self.effects,
                f"zg361_career_hc_m{mechanism_id:03d}_consume_effect",
            )
            self.assertIn("zg361_ch_hc_partition", source)
            self.assertIn("zg361_ch_hc_conserved", source)
            self.assertIn("zg361_ch_hc_authorized", source)

    def test_mobility_privacy_release_and_once_only_protection_are_projected(self) -> None:
        m115 = block(self.effects, "zg361_career_hc_m115_consume_effect")
        m116 = block(self.effects, "zg361_career_hc_m116_consume_effect")
        m117 = block(self.effects, "zg361_career_hc_m117_consume_effect")
        m118 = block(self.effects, "zg361_career_hc_m118_consume_effect")
        self.assertIn("application_identity_visible value = 0", m115)
        self.assertIn("application_identity_visible value = 1", m115)
        self.assertIn("release_days value = 90", m116)
        self.assertIn("release_days value = 150", m116)
        self.assertIn("release_extension_used value = 1", m116)
        self.assertIn("ramp_protection_used_lifetime value = 1", m117)
        self.assertIn("probation_failures_separate value = 1", m118)

    def test_manager_scorecard_and_successor_gates_are_not_kpi_only(self) -> None:
        m122 = block(self.effects, "zg361_career_hc_m122_consume_effect")
        m123 = block(self.effects, "zg361_career_hc_m123_consume_effect")
        m124 = block(self.effects, "zg361_career_hc_m124_consume_effect")
        m128 = block(self.effects, "zg361_career_hc_m128_consume_effect")
        for value in (40, 30):
            self.assertIn(f"value = {value}", m122)
        self.assertIn("subordinate_survey_factors value = 6", m123)
        self.assertIn("subordinate_survey_credibility value = 100", m123)
        self.assertIn("successor_accepted value = 1", m124)
        self.assertIn("manager_promotion_released value = 1", m124)
        self.assertIn("next_cycle_quota_policy", m128)

    def test_q_authority_has_eight_named_business_consumers_and_real_hooks(self) -> None:
        definitions = set(
            re.findall(
                r"(?m)^zg361_career_hc_m(12[1-8])_business_consumer_effect = \{",
                self.effects,
            )
        )
        self.assertEqual(definitions, {str(item) for item in range(121, 129)})
        for mechanism_id in generator.Q_AUTHORITY_IDS:
            with self.subTest(mechanism=mechanism_id):
                consumer = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_consume_effect",
                )
                authority = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_business_consumer_effect",
                )
                hook = f"zg361_career_hc_m{mechanism_id:03d}_business_consumer_effect = yes"
                self.assertEqual(consumer.count(hook), 1)
                self.assertIn("zg361_case_kernel_full_guard_trigger", authority)
                self.assertIn(f"zg361_ch_m{mechanism_id:03d}_business_consumed = 0", authority)
                self.assertIn(
                    f"name = zg361_ch_m{mechanism_id:03d}_business_consumed value = 1",
                    authority,
                )
                self.assertIn("manager-governance is adapter-only", self.effects)
                self.assertNotIn("zg361_manager_governance_", authority)

    def test_q_business_receipts_freeze_all_five_case_dimensions_and_revision(self) -> None:
        for mechanism_id in generator.Q_AUTHORITY_IDS:
            state = generator.STAGE_BY_ID[mechanism_id]
            source = block(
                self.effects,
                f"zg361_career_hc_m{mechanism_id:03d}_business_consumer_effect",
            )
            prefix = f"zg361_ch_m{mechanism_id:03d}_business"
            with self.subTest(mechanism=mechanism_id):
                for field, value in (
                    ("owner", "var:zg361_case_q_owner"),
                    ("subject", "this"),
                    ("cycle", "var:zg361_case_q_cycle_serial"),
                    ("case", "var:zg361_case_q_case_serial"),
                    ("state", str(state)),
                    ("revision", "var:zg361_case_q_revision"),
                ):
                    self.assertIn(f"name = {prefix}_{field} value = {value}", source)
                self.assertIn(f"var:zg361_ch_m{mechanism_id:03d}_receipt_state = {state}", source)
                self.assertIn(f"var:zg361_ch_m{mechanism_id:03d}_route = 1", source)
                self.assertIn(f"var:zg361_ch_m{mechanism_id:03d}_route = 2", source)
                self.assertIn(f"name = {prefix}_deferred value = 1", source)
                self.assertIn(f"name = {prefix}_debt value = 1", source)
                self.assertIn(f"name = {prefix}_object_count value = 0", source)

    def test_q124_joins_distinct_vacancy_hc_candidate_incumbent_succession_backfill(self) -> None:
        source = block(
            self.effects,
            "zg361_career_hc_m124_business_consumer_effect",
        )
        kinds = ("vacancy", "hc_slot", "candidate", "incumbent", "succession", "backfill")
        for kind in kinds:
            prefix = f"zg361_ch_m124_{kind}_object"
            with self.subTest(kind=kind):
                for field in ("id", "owner", "subject", "cycle", "case", "state", "revision", "route", "active"):
                    self.assertIn(f"{prefix}_{field}", source)
        self.assertIn(
            "zg361_ch_m124_candidate_object_subject value = var:zg361_ch_q_named_successor_candidate",
            source,
        )
        self.assertIn("zg361_ch_m124_incumbent_object_subject value = this", source)
        self.assertIn("zg361_ch_m124_succession_object_incumbent value = this", source)
        self.assertIn(
            "zg361_ch_m124_succession_object_candidate value = var:zg361_ch_q_named_successor_candidate",
            source,
        )
        self.assertIn("zg361_ch_m124_backfill_object_vacancy_id", source)
        self.assertIn("zg361_ch_m124_backfill_object_hc_slot_id", source)

    def test_q_capacity_and_crisis_books_are_prechecked_and_conserved(self) -> None:
        opened = block(self.effects, "zg361_career_hc_open_q_case_effect")
        for needle in (
            "zg361_ch_q_manager_hc_authorized value = 4",
            "zg361_ch_q_manager_hc_available value = 4",
            "zg361_ch_q_crisis_hours_authorized value = 100",
            "zg361_ch_q_crisis_hours_available value = 100",
        ):
            self.assertIn(needle, opened)
        for mechanism_id in (121, 124, 127):
            source = block(
                self.effects,
                f"zg361_career_hc_m{mechanism_id:03d}_business_consumer_effect",
            )
            self.assertIn("zg361_ch_q_manager_hc_available >=", source)
            self.assertIn("zg361_ch_q_manager_hc_partition", source)
            self.assertIn("zg361_ch_q_manager_hc_conserved", source)
            self.assertIn("zg361_ch_q_manager_hc_authorized", source)
            self.assertLess(
                source.find("zg361_ch_q_manager_hc_available >="),
                source.find(f"zg361_ch_m{mechanism_id:03d}_manager_object_id"),
            )
            self.assertIn(
                f"name = zg361_ch_m{mechanism_id:03d}_business_object_count value = 0",
                source,
            )
        crisis = block(self.effects, "zg361_career_hc_m125_business_consumer_effect")
        self.assertIn("zg361_ch_q_crisis_hours_available >= 100", crisis)
        self.assertIn("zg361_ch_q_crisis_hours_partition", crisis)
        self.assertIn("zg361_ch_q_crisis_hours_conserved", crisis)
        self.assertIn("zg361_ch_crisis_manager_hours value = 40", crisis)
        self.assertIn("zg361_ch_crisis_delegated_hours value = 60", crisis)
        self.assertIn("zg361_ch_crisis_manager_hours value = 100", crisis)
        self.assertIn("zg361_ch_crisis_delegated_hours value = 0", crisis)
        self.assertLess(
            crisis.find("zg361_ch_q_crisis_hours_available >= 100"),
            crisis.find("zg361_ch_m125_manager_object_id"),
        )

    def test_q_routes_publish_distinct_score_survey_quadrant_span_and_future_policy(self) -> None:
        m122 = block(self.effects, "zg361_career_hc_m122_business_consumer_effect")
        self.assertIn("zg361_ch_manager_score_hard value = 70", m122)
        self.assertIn("zg361_ch_manager_score_hard value = 90", m122)
        self.assertIn("zg361_ch_manager_score_weight_total value = 100", m122)
        m123 = block(self.effects, "zg361_career_hc_m123_business_consumer_effect")
        self.assertIn("zg361_ch_subordinate_survey_factors value = 6", m123)
        self.assertIn("zg361_ch_subordinate_survey_factors value = 1", m123)
        self.assertIn("zg361_ch_subordinate_survey_credibility value = 100", m123)
        self.assertIn("zg361_ch_subordinate_survey_credibility value = 25", m123)
        m126 = block(self.effects, "zg361_career_hc_m126_business_consumer_effect")
        self.assertIn("zg361_ch_values_quadrant value = 1", m126)
        self.assertIn("zg361_ch_values_quadrant value = 2", m126)
        m127 = block(self.effects, "zg361_career_hc_m127_business_consumer_effect")
        self.assertIn("zg361_ch_span_direct_reports value = 11", m127)
        self.assertIn("zg361_ch_span_layer_inserted value = 1", m127)
        self.assertIn("zg361_ch_span_layer_inserted value = 0", m127)
        m128 = block(self.effects, "zg361_career_hc_m128_business_consumer_effect")
        self.assertIn("zg361_ch_climate_pressure value = 70", m128)
        self.assertIn("zg361_ch_next_cycle_quota_policy_effective_cycle", m128)
        self.assertIn("zg361_ch_current_cycle_quota_policy_unchanged value = 1", m128)

    def test_q_open_freezes_real_named_people_and_missing_candidate_skips_q_cleanly(self) -> None:
        opened = block(self.effects, "zg361_career_hc_open_q_case_effect")
        self.assertIn("ordered_vassal = {", opened)
        self.assertIn("order_by = stewardship", opened)
        self.assertIn("position = 0", opened)
        self.assertIn("zg361_ch_q_named_successor_candidate", opened)
        self.assertIn("zg361_ch_q_named_survey_respondent", opened)
        queue = block(self.events, f"zg361ch.{generator.QUEUE_EVENTS['p']}")
        self.assertIn("any_vassal = { zg361_is_reviewable_vassal_trigger = yes }", queue)
        self.assertIn("zg361_career_hc_open_q_case_effect = yes", queue)
        self.assertIn("zg361_career_hc_finalize_p_portfolio_effect = yes", queue)

    def test_assessed_subject_responses_never_gain_manager_authority(self) -> None:
        found = set(
            int(item)
            for item in re.findall(
                r"^zg361_career_hc_m(\d{3})_subject_response_effect = \{",
                self.effects,
                flags=re.MULTILINE,
            )
        )
        self.assertEqual(found, set(generator.SUBJECT_RESPONSE_IDS))
        for mechanism_id in found:
            with self.subTest(mechanism=mechanism_id):
                source = block(
                    self.effects,
                    f"zg361_career_hc_m{mechanism_id:03d}_subject_response_effect",
                )
                self.assertIn("zg361_case_kernel_subject_self_guard_trigger", source)
                self.assertIn("is_ai = no", source)
                self.assertNotIn("zg361_is_celestial_liege_trigger", source)
                self.assertNotIn("_open_effect", source)
                self.assertNotIn("_advance_", source)
                self.assertNotIn("_core_effect", source)

    def test_authorized_ai_manager_path_is_silent_and_player_feedback_exists(self) -> None:
        # Manager entries intentionally have no is_ai=no gate: the project
        # owner's second AI exception uses the same canonical duke+ guard.
        for mechanism_id in generator.EXPECTED_IDS:
            source = block(
                self.effects,
                f"zg361_career_hc_m{mechanism_id:03d}_manager_apply_effect",
            )
            self.assertNotIn("is_ai = no", source)
        for event_id in range(901, 907):
            source = block(self.events, f"zg361ch.{event_id}")
            self.assertIn("trigger = { is_ai = no }", source)
            self.assertNotIn("hidden = yes", source)
        self.assertIn("var:zg361_case_d_owner = { is_ai = no }", self.effects)

    def test_localization_has_all_mechanism_and_completion_keys(self) -> None:
        english = (
            MOD_ROOT / "localization/english/zg361_career_hc_l_english.yml"
        ).read_text(encoding="utf-8-sig")
        chinese = (
            MOD_ROOT / "localization/simp_chinese/zg361_career_hc_l_simp_chinese.yml"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("不是一张只会喊口号的制度卡", chinese)
        for mechanism_id in generator.EXPECTED_IDS:
            with self.subTest(mechanism=mechanism_id):
                for suffix in ("name", "desc", "a", "b", "c"):
                    key = f"zg361ch.m{mechanism_id:03d}.{suffix}:0"
                    self.assertIn(key, english)
                    self.assertIn(key, chinese)
        for event_id in range(901, 907):
            for suffix in ("t", "desc", "a"):
                self.assertIn(f"zg361ch.{event_id}.{suffix}:0", english)
                self.assertIn(f"zg361ch.{event_id}.{suffix}:0", chinese)

    def test_seven_daily_languages_are_structural_english_placeholders(self) -> None:
        english = (
            MOD_ROOT / "localization/english/zg361_career_hc_l_english.yml"
        ).read_text(encoding="utf-8-sig")
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
                text = (
                    MOD_ROOT
                    / "localization"
                    / language
                    / f"zg361_career_hc_l_{language}.yml"
                ).read_text(encoding="utf-8-sig")
                self.assertEqual(
                    text.replace(f"l_{language}:", "l_english:", 1),
                    english,
                )

    def test_no_religion_or_unrelated_top_level_system_is_introduced(self) -> None:
        lowered = self.effects.lower()
        for forbidden in (
            "faith =",
            "religion =",
            "doctrine",
            "tenet",
            "holy_order",
            "convert_faith",
        ):
            self.assertNotIn(forbidden, lowered)

    def test_source_contract_is_static_ready_not_live(self) -> None:
        spec = (
            MOD_ROOT / "docs/361-career-hc-ck3-runtime-spec.md"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("CK3 script static-ready", spec)
        self.assertIn("尚无实机", spec)
        self.assertIn("不得写成 fixture-live", spec)
        self.assertIn("44", spec)
        self.assertIn("zg361_career_hc_open_portfolio_effect", spec)


if __name__ == "__main__":
    unittest.main()

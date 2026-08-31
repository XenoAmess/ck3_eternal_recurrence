#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static L0 compiler tests for the workforce/endgame CK3 runtime slice."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gen_361_workforce_endgame_runtime as gen


MOD_ROOT = Path(__file__).resolve().parents[1]
EFFECTS_PATH = MOD_ROOT / "common" / "scripted_effects" / "zg361_workforce_endgame_runtime_effects.txt"
EVENTS_PATH = MOD_ROOT / "events" / "zg361_workforce_endgame_runtime_events.txt"
SPEC_PATH = MOD_ROOT / "docs" / "361-workforce-endgame-ck3-runtime-spec.md"
LEDGER_PATH = MOD_ROOT / "docs" / "361-workforce-external-producer-ledger-2026-08-31.md"
EXPECTED_IDS = set(range(242, 278)) | {355, 356, 360, 361}
ILLEGAL_TRIGGER_ARITHMETIC_RHS = re.compile(
    r"(?:\b(?:root\.)?var:[^\s{}=<>]+|\bscope:[^\s{}=<>]+|\$[A-Z0-9_]+\$)"
    r"\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*="
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if not match:
        raise AssertionError(f"missing top-level block {name}")
    start = match.start()
    depth = 0
    opened = False
    for index in range(match.end() - 1, len(text)):
        if text[index] == "{":
            depth += 1
            opened = True
        elif text[index] == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start:index + 1]
    raise AssertionError(f"unbalanced block {name}")


def loc_rows(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in read(path).splitlines()[1:]:
        match = re.match(r'^ ([^:]+):0 "(.*)"$', line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


class WorkforceEndgameRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effects = read(EFFECTS_PATH)
        cls.events = read(EVENTS_PATH)
        cls.spec_text = read(SPEC_PATH)
        cls.ledger_text = read(LEDGER_PATH)
        cls.specs = gen.by_id()

    def test_01_readiness_is_honest(self) -> None:
        self.assertEqual("ck3-script-static-ready-not-live", gen.READINESS)
        self.assertIn("No CK3 parser, paused snapshot or live evidence", self.effects)

    def test_trigger_arithmetic_never_uses_a_value_block_rhs(self) -> None:
        self.assertIsNone(
            ILLEGAL_TRIGGER_ARITHMETIC_RHS.search(self.effects),
            "CK3 scripted-effect loader treats RHS value/add/multiply/subtract as triggers",
        )
        debt = block(self.effects, "zg361_we_m242_consume_due_debt_effect")
        self.assertIn("debt_id = scope:zg361_we_m242_expected_debt_id", debt)
        collective = block(self.effects, "zg361_we_m360_route_a_effect")
        self.assertIn("name = zg361_we_expected_collective_total_quota", collective)
        self.assertIn(
            "external_collective_total_quota = scope:zg361_we_expected_collective_total_quota",
            collective,
        )

    def test_gold_debits_use_registered_short_term_effect(self) -> None:
        self.assertEqual(self.effects.count("remove_short_term_gold ="), 11)
        self.assertIsNone(
            re.search(r"(?<!short_term_)\bremove_gold\s*=", self.effects),
            "CK3 1.19.0.6 does not register the bare remove_gold effect",
        )

    def test_02_catalogue_is_exact_40(self) -> None:
        gen.validate_specs()
        self.assertEqual(EXPECTED_IDS, set(self.specs))
        self.assertEqual(40, len(gen.MECHANISMS))
        self.assertEqual(
            {"ab": 12, "ac": 12, "ad": 12, "al": 4},
            {domain: len(order) for domain, order in gen.DOMAIN_ORDER.items()},
        )

    def test_03_semantic_fields_are_model_bindings(self) -> None:
        self.assertEqual(40, len({spec.field for spec in gen.MECHANISMS}))
        for spec in gen.MECHANISMS:
            self.assertEqual(gen.MECHANISM_BINDINGS[spec.mid].behaviors[0], spec.field)

    def test_04_generator_outputs_exact_independent_allowlist(self) -> None:
        outputs = {path.relative_to(MOD_ROOT).as_posix() for path in gen.outputs()}
        self.assertEqual(11, len(outputs))
        self.assertIn("common/scripted_effects/zg361_workforce_endgame_runtime_effects.txt", outputs)
        self.assertIn("events/zg361_workforce_endgame_runtime_events.txt", outputs)
        self.assertFalse(any("on_action" in path or "gui/" in path or "scoreboard" in path for path in outputs))
        self.assertFalse(any("case_kernel" in path or "b1_" in path or "b2_" in path for path in outputs))

    def test_05_generator_check_is_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(Path(gen.__file__)), "--check"],
            cwd=MOD_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("GREEN: 11", result.stdout)

    def test_06_all_owned_text_files_have_bom(self) -> None:
        paths = [Path(gen.__file__), Path(__file__), SPEC_PATH, LEDGER_PATH, *gen.outputs()]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.read_bytes().startswith(gen.BOM))

    def test_07_generated_braces_balance(self) -> None:
        for text in (self.effects, self.events):
            self.assertEqual(text.count("{"), text.count("}"))

    def test_08_every_id_has_consumer_three_routes_and_player_event(self) -> None:
        for mid in sorted(EXPECTED_IDS):
            with self.subTest(mid=mid):
                self.assertIn(f"zg361_we_m{mid}_consume_effect = {{", self.effects)
                self.assertIn(f"zg361we.{mid} = {{", self.events)
                for letter in "abc":
                    self.assertIn(f"zg361_we_m{mid}_route_{letter}_effect = {{", self.effects)
                    self.assertIn(f"name = zg361we.{mid}.{letter}", block(self.events, f"zg361we.{mid}"))

    def test_09_definition_counts_are_exact(self) -> None:
        routes = re.findall(r"^zg361_we_m(\d+)_route_([abc])_effect = \{$", self.effects, re.MULTILINE)
        consumers = re.findall(r"^zg361_we_m(\d+)_consume_effect = \{$", self.effects, re.MULTILINE)
        visible = re.findall(r"^zg361we\.(\d+) = \{$", self.events, re.MULTILINE)
        self.assertEqual(120, len(routes))
        self.assertEqual(EXPECTED_IDS, {int(mid) for mid, _ in routes})
        self.assertEqual(EXPECTED_IDS, {int(mid) for mid in consumers})
        self.assertEqual(EXPECTED_IDS, {int(mid) for mid in visible if int(mid) in EXPECTED_IDS})

    def test_10_each_visible_event_is_player_only_and_exactly_three_options(self) -> None:
        for spec in gen.MECHANISMS:
            event = block(self.events, f"zg361we.{spec.mid}")
            with self.subTest(mid=spec.mid):
                self.assertIn("is_ai = no", event)
                self.assertEqual(3, event.count("\n\toption = {"))
                self.assertIn(f"EXPECTED_STATE = {spec.state}", event)

    def test_11_events_freeze_owner_subject_cycle_case(self) -> None:
        for spec in gen.MECHANISMS:
            event = block(self.events, f"zg361we.{spec.mid}")
            for name in ("owner", "subject", "cycle", "case"):
                self.assertIn(f"exists = scope:zg361_we_{spec.domain}_{name}", event)
            self.assertIn(f"this = scope:zg361_we_{spec.domain}_owner", event)

    def test_12_each_route_has_full_five_tuple_guard(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    self.assertIn("zg361_case_kernel_full_guard_trigger", route)
                    for token in ("OWNER_VAR", "SUBJECT_VAR", "CYCLE_VAR", "CASE_VAR", "STATE_VAR", "ACTIVE_VAR"):
                        self.assertIn(token, route)
                    for token in ("EXPECTED_OWNER", "EXPECTED_SUBJECT", "EXPECTED_CYCLE", "EXPECTED_CASE"):
                        self.assertIn(token, route)
                    self.assertIn(f"EXPECTED_STATE = {spec.state}", route)

    def test_13_cross_route_receipts_are_mutually_exclusive(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                for choice in (1, 2, 3):
                    self.assertIn(f"EXPECTED_CHOICE = {choice}", route)
                for name in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE", "CHOICE"):
                    self.assertIn(f"RECEIPT_{name}_VAR = zg361_we_m{spec.mid}_receipt_", route)

    def test_14_route_mutation_order_is_atomic(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                precheck = route.index("var:zg361_we_operation_used <")
                receipt = route.index("zg361_case_kernel_record_operation_effect")
                semantic = route.index(f"name = zg361_we_{spec.field}")
                consumer = route.index(f"zg361_we_m{spec.mid}_consume_effect = yes")
                self.assertLess(precheck, receipt)
                self.assertLess(receipt, semantic)
                self.assertLess(semantic, consumer)

    def test_15_typed_red_idempotent_and_stale_are_explicit(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("abc", 1):
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                self.assertIn(f"name = zg361_we_last_red_code value = {spec.mid * 10 + choice}", route)
                self.assertIn("value = 4 } # typed RED, no receipt or business write", route)
                self.assertIn("value = 2 } # idempotent no-op", route)
                self.assertIn("value = 3 } } # stale no-op", route)

    def test_16_every_write_and_consumer_freezes_provenance(self) -> None:
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_we_m{spec.mid}_consume_effect")
            for name in ("owner", "subject", "cycle", "case", "state"):
                self.assertIn(f"has_variable = zg361_we_m{spec.mid}_write_{name}", consumer)
                self.assertIn(f"name = zg361_we_m{spec.mid}_consumed_{name}", consumer)
            for choice, letter in enumerate("abc", 1):
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                self.assertIn(f"name = zg361_we_m{spec.mid}_provenance_choice value = {choice}", route)
                self.assertIn(f"zg361_we_m{spec.mid}_consume_effect = yes", route)

    def test_16a_exact_object_or_debt_envelope_is_consumed_per_id(self) -> None:
        self.assertEqual(40, len({spec.object_type for spec in gen.MECHANISMS}))
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_we_m{spec.mid}_consume_effect")
            self.assertIn(f"has_variable = zg361_we_m{spec.mid}_business_object_created", consumer)
            self.assertIn(f"has_variable = zg361_we_m{spec.mid}_object_{spec.object_type}", consumer)
            self.assertIn(f"var:zg361_we_m{spec.mid}_object_type_code = {spec.mid}", consumer)
            self.assertIn(f"name = zg361_we_m{spec.mid}_consumer_{spec.consumer_key} value = 1", consumer)
            for resource_book in spec.resource_books:
                self.assertIn(f"has_variable = zg361_we_m{spec.mid}_resource_{resource_book}", consumer)
            if spec.deadline_cycles:
                self.assertIn(f"has_variable = zg361_we_m{spec.mid}_object_due_cycle", consumer)
            for letter in "ab":
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                self.assertIn(f"name = zg361_we_m{spec.mid}_business_object_created value = 1", route)
                self.assertIn(f"name = zg361_we_m{spec.mid}_object_{spec.object_type} value = 1", route)
                for name in ("owner", "subject", "cycle", "case", "state", "id"):
                    self.assertIn(f"name = zg361_we_m{spec.mid}_object_{name}", route)
            route_c = block(self.effects, f"zg361_we_m{spec.mid}_route_c_effect")
            self.assertIn(f"name = zg361_we_m{spec.mid}_business_object_created value = 0", route_c)
            self.assertIn(f"name = zg361_we_m{spec.mid}_debt_due_cycle", route_c)
            self.assertNotIn(f"name = zg361_we_m{spec.mid}_object_{spec.object_type}", route_c)

    def test_17_only_stage_last_advances_after_full_barrier(self) -> None:
        for spec in gen.MECHANISMS:
            same_stage = [row.mid for row in gen.MECHANISMS if row.domain == spec.domain and row.state == spec.state]
            for letter in "abc":
                route = block(self.effects, f"zg361_we_m{spec.mid}_route_{letter}_effect")
                if spec.mid in gen.STAGE_LAST[spec.domain]:
                    edge = gen.STAGE_LAST[spec.domain][spec.mid]
                    expected_advance = 0 if (spec.mid == 263 and letter == "b") else 1
                    self.assertEqual(expected_advance, route.count(f"zg361_case_{spec.domain}_advance_{edge:02d}_effect"))
                    if not expected_advance:
                        self.assertIn("m263_extension_pending value = 1", route)
                        continue
                    before = route[:route.index(f"zg361_case_{spec.domain}_advance_{edge:02d}_effect")]
                    for mid in same_stage:
                        self.assertIn(f"zg361_we_m{mid}_receipt_choice", before)
                else:
                    self.assertNotIn(f"zg361_case_{spec.domain}_advance_", route)

    def test_18_al_357_359_edges_require_three_exact_external_receipts(self) -> None:
        bridge = block(self.effects, "zg361_we_submit_al_357_359_receipts_effect")
        self.assertEqual(1, self.effects.count("zg361_case_al_advance_02_effect"))
        self.assertEqual(1, self.effects.count("zg361_case_al_advance_03_effect"))
        self.assertIn("EXPECTED_STATE = 2", bridge)
        for mid, state in ((357, 2), (358, 3), (359, 3)):
            for field in ("OWNER", "SUBJECT", "CYCLE", "CASE"):
                self.assertIn(f"$M{mid}_{field}$ = $TICKET_{field}$", bridge)
            self.assertIn(f"$M{mid}_STATE$ = {state}", bridge)
            self.assertIn(f"$M{mid}_RECEIPT_ID$ > 0", bridge)
            self.assertIn(f"$M{mid}_RECEIPT_HASH$ > 0", bridge)
        self.assertLess(bridge.index("zg361_case_al_advance_02_effect"), bridge.index("zg361_case_al_advance_03_effect"))
        self.assertGreater(bridge.index("al_external_stage_receipts_verified value = 1"), bridge.index("var:zg361_case_al_state = 4"))
        self.assertIn("adapter_status value = 2", bridge)
        for letter in "abc":
            route = block(self.effects, f"zg361_we_m356_route_{letter}_effect")
            self.assertIn("zg361_we_awaiting_al_357_359", route)
            self.assertIn("portfolio_status value = 5", route)
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        self.assertIn("OR = { var:zg361_case_al_state = 4 var:zg361_case_al_state = 5 }", entry)
        self.assertNotIn("name = zg361_we_al_external_stage_receipts_verified", entry)
        for name in ("owner", "subject", "cycle", "case", "state", "count"):
            self.assertIn(f"has_variable = zg361_we_al_external_receipt_{name}", entry)
        self.assertIn("var:zg361_we_al_external_last_operation = 359", entry)

    def test_19_every_owned_stage_has_exact_kernel_deadline(self) -> None:
        expected = sum(len(states) for states in gen.STAGE_LAST.values())
        schedules = re.findall(r"^zg361_we_(ab|ac|ad|al)_schedule_stage_(\d+)_deadline_effect = \{$", self.effects, re.MULTILINE)
        self.assertEqual(expected, len(schedules))
        for domain, barriers in gen.STAGE_LAST.items():
            for state in sorted(set(barriers.values())):
                schedule = block(self.effects, f"zg361_we_{domain}_schedule_stage_{state:02d}_deadline_effect")
                due = block(self.events, f"zg361we.{gen.deadline_event_id(domain, state)}")
                relay = block(self.events, f"zg361we.{gen.deadline_relay_event_id(domain, state)}")
                self.assertIn("zg361_case_kernel_schedule_deadline_effect", schedule)
                self.assertIn(f"DAYS = {gen.DEADLINE_DAYS[domain]}", schedule)
                self.assertIn("zg361_case_kernel_expire_deadline_effect", due)
                self.assertIn(
                    f"trigger_event = {{ id = zg361we.{gen.deadline_relay_event_id(domain, state)} }}",
                    due,
                )
                self.assertLess(
                    due.index("zg361_case_kernel_expire_deadline_effect"),
                    due.index(f"trigger_event = {{ id = zg361we.{gen.deadline_relay_event_id(domain, state)} }}"),
                )
                for name in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"exists = scope:zg361_we_{domain}_s{state:02d}_relay_{name}", relay)
                self.assertIn(f"this = scope:zg361_we_{domain}_s{state:02d}_relay_owner", relay)
                self.assertIn("zg361_case_kernel_full_guard_trigger", relay)
                self.assertIn("EXPECTED_OWNER = root", relay)
                self.assertIn("EXPECTED_SUBJECT = this", relay)
                self.assertIn(f"zg361_we_{domain}_timeout_stage_{state:02d}_effect", relay)

    def test_19a_all_route_c_calls_bind_loader_required_ticket_state(self) -> None:
        bound_calls = 0
        for spec in gen.MECHANISMS:
            timeout = block(
                self.effects,
                f"zg361_we_{spec.domain}_timeout_stage_{spec.state:02d}_effect",
            )
            expected_call = f"""zg361_we_m{spec.mid}_route_c_effect = {{
\t\tTICKET_OWNER = var:zg361_case_{spec.domain}_owner
\t\tTICKET_SUBJECT = this
\t\tTICKET_CYCLE = var:zg361_case_{spec.domain}_cycle_serial
\t\tTICKET_CASE = var:zg361_case_{spec.domain}_case_serial
\t\tTICKET_STATE = {spec.state}
\t}}"""
            self.assertIn(expected_call, timeout, spec.mid)

            event = block(self.events, f"zg361we.{spec.mid}")
            expected_player_call = f"""zg361_we_m{spec.mid}_route_c_effect = {{
\t\t\t\tTICKET_OWNER = scope:zg361_we_{spec.domain}_owner
\t\t\t\tTICKET_SUBJECT = scope:zg361_we_{spec.domain}_subject
\t\t\t\tTICKET_CYCLE = scope:zg361_we_{spec.domain}_cycle
\t\t\t\tTICKET_CASE = scope:zg361_we_{spec.domain}_case
\t\t\t\tTICKET_STATE = {spec.state}
\t\t\t}}"""
            self.assertIn(expected_player_call, event, spec.mid)

            route_c = block(self.effects, f"zg361_we_m{spec.mid}_route_c_effect")
            self.assertIn(
                f"name = zg361_we_m{spec.mid}_debt_state value = $TICKET_STATE$",
                route_c,
                spec.mid,
            )
            bound_calls += 2

        call_pattern = re.compile(
            r"(?m)^[ \t]+zg361_we_m(\d+)_route_c_effect = \{$"
        )
        timeout_call_ids = [int(mid) for mid in call_pattern.findall(self.effects)]
        player_call_ids = [int(mid) for mid in call_pattern.findall(self.events)]
        expected_ids = sorted(EXPECTED_IDS)
        self.assertEqual(expected_ids, sorted(timeout_call_ids))
        self.assertEqual(expected_ids, sorted(player_call_ids))
        self.assertEqual(80, bound_calls)
        self.assertEqual(80, len(timeout_call_ids) + len(player_call_ids))

        all_route_c_rows: list[tuple[Path, str]] = []
        for path in MOD_ROOT.rglob("*.txt"):
            for line in read(path).splitlines():
                if re.match(r"^\s*zg361_we_m\d+_route_c_effect = \{$", line):
                    all_route_c_rows.append((path, line))
        self.assertEqual(120, len(all_route_c_rows))
        self.assertEqual(
            {EFFECTS_PATH.resolve(), EVENTS_PATH.resolve()},
            {path.resolve() for path, _ in all_route_c_rows},
        )

    def test_20_all_event_references_are_closed(self) -> None:
        referenced = {int(mid) for mid in re.findall(r"(?:id|EVENT) = zg361we\.(\d+)", self.effects + self.events)}
        defined = {int(mid) for mid in re.findall(r"^zg361we\.(\d+) = \{$", self.events, re.MULTILINE)}
        self.assertEqual(referenced, defined)

    def test_21_public_surface_is_one_manager_scope_adapter(self) -> None:
        public_defs = re.findall(r"^zg361_we_[a-z0-9_]*open_portfolio_effect = \{$", self.effects, re.MULTILINE)
        self.assertEqual(["zg361_we_open_portfolio_effect = {"], public_defs)
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        self.assertIn("zg361_is_celestial_liege_trigger = yes", entry)
        self.assertIn("$SUBJECT$ = { zg361_is_reviewable_vassal_trigger = yes liege = root }", entry)
        self.assertIn("$SUBJECT$ = { zg361_we_ab_launch_effect = yes }", entry)
        self.assertNotIn("on_action", entry)

    def test_22_shared_formal_hc_is_required_not_reset(self) -> None:
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        init = block(self.effects, "zg361_we_initialize_portfolio_effect")
        for name in ("authorized", "available", "reserved", "occupied", "frozen", "reclaimed"):
            self.assertIn(f"has_variable = zg361_ch_hc_{name}", entry)
            self.assertNotIn(f"name = zg361_ch_hc_{name}", init)

    def test_23_player_events_are_serial_and_ai_is_background_only(self) -> None:
        for spec in gen.MECHANISMS:
            event = block(self.events, f"zg361we.{spec.mid}")
            for option in event.split("\n\toption = {")[1:]:
                expected_max = 2 if spec.mid in (274, 275) else 1
                self.assertLessEqual(option.count("trigger_event = { id = zg361we."), expected_max)
        accepted = block(self.events, "zg361we.274")
        self.assertIn("m274_hired = 1", accepted)
        self.assertIn("zg361_we_m275_route_a_effect", accepted)
        self.assertIn("id = zg361we.269", accepted)
        self.assertIn("id = zg361we.275", accepted)
        refused = block(self.events, "zg361we.275")
        self.assertIn("m275_refusal = 1", refused)
        self.assertIn("zg361_we_m269_route_a_effect", refused)
        self.assertIn("id = zg361we.276", refused)
        for domain in gen.DOMAIN_ORDER:
            ai = block(self.effects, f"zg361_we_{domain}_run_authorized_ai_effect")
            self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", ai)
            self.assertNotIn("trigger_event", ai)

    def test_24_replay_cannot_reset_same_cycle_or_active_cases(self) -> None:
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        self.assertNotIn("zg361_we_manager_portfolio_cycle", entry)
        self.assertIn("has_variable = zg361_we_portfolio_cycle", entry)
        self.assertIn("NOT = { var:zg361_we_portfolio_cycle = root.var:zg361_review_serial }", entry)
        for domain in ("ab", "ac", "ad", "al"):
            self.assertIn(f"has_variable = zg361_case_{domain}_active", entry)
            self.assertIn(f"var:zg361_case_{domain}_active = 0", entry)

    def test_25_ab_authorized_hours_and_presence_are_separate(self) -> None:
        route = block(self.effects, "zg361_we_m242_route_a_effect")
        self.assertLess(route.index("hours_available >= 20"), route.index("record_operation"))
        self.assertIn("hours_available add = -20", route)
        self.assertIn("hours_output add = 20", route)
        self.assertIn("m242_presence_hours value = 30", route)
        self.assertIn("m242_presence_rewarded value = 0", route)

    def test_26_overtime_has_one_liability_and_one_settlement_route(self) -> None:
        overtime = block(self.effects, "zg361_we_m245_route_a_effect")
        gold = block(self.effects, "zg361_we_m246_route_a_effect")
        leave = block(self.effects, "zg361_we_m246_route_b_effect")
        self.assertIn("overtime_pending add = 5", overtime)
        self.assertIn("overtime_pending add = -5", gold)
        self.assertIn("remove_short_term_gold = 15", gold)
        self.assertIn("add_gold = 15", gold)
        self.assertIn("leave_bank add = 5", leave)

    def test_27_meeting_attendance_contribution_and_refusal_are_distinct(self) -> None:
        meeting = block(self.effects, "zg361_we_m249_route_a_effect")
        contribution = block(self.effects, "zg361_we_m250_route_a_effect")
        refusal = block(self.effects, "zg361_we_m251_route_a_effect")
        self.assertIn("m249_attendee_hours value = 6", meeting)
        self.assertIn("m250_attendee_count value = 3", contribution)
        self.assertIn("m250_contributor_count value = 1", contribution)
        self.assertIn("m251_representative_in_attendees value = 1", refusal)

    def test_28_ac_shadow_and_formal_hc_conversion_is_future_one_shot(self) -> None:
        contract = block(self.effects, "zg361_we_m254_route_a_effect")
        conversion = block(self.effects, "zg361_we_m257_route_a_effect")
        future = block(self.effects, "zg361_we_m257_future_consume_effect")
        self.assertIn("shadow_hc_available add = -1", contract)
        self.assertIn("m254_formal_hc_touched value = 0", contract)
        self.assertIn("zg361_ch_hc_available add = -1", conversion)
        self.assertIn("zg361_ch_hc_reserved add = 1", conversion)
        self.assertIn("days = 365", conversion)
        self.assertIn("zg361_ch_hc_reserved add = -1", future)
        self.assertIn("zg361_ch_hc_occupied add = 1", future)

    def test_29_ac_tco_pool_and_sla_do_not_write_formal_grade(self) -> None:
        self.assertIn("m255_formal_tco value = 120", block(self.effects, "zg361_we_m255_route_a_effect"))
        pool = block(self.effects, "zg361_we_m256_route_a_effect")
        sla = block(self.effects, "zg361_we_m259_route_a_effect")
        self.assertIn("m256_external_entries_in_formal_cohort value = 0", pool)
        self.assertIn("m259_responsibility_total_bps value = 10000", sla)
        self.assertIn("m259_formal_grade_written value = 0", sla)

    def test_30_secondment_uses_authoritative_due_cycle_and_nonterminal_extend(self) -> None:
        review = block(self.effects, "zg361_we_m262_route_a_effect")
        extend = block(self.effects, "zg361_we_m263_route_b_effect")
        self.assertIn("m262_weight_total value = 100", review)
        self.assertIn("m262_due_cycle value = { value = $TICKET_CYCLE$ add = 1 }", review)
        self.assertIn("m263_prior_identity_preserved value = 1", extend)
        self.assertIn("m263_extension_terminal value = 0", extend)

    def test_31_contract_payment_and_recovery_have_opposite_directions(self) -> None:
        handoff = block(self.effects, "zg361_we_m264_route_a_effect")
        recovery = block(self.effects, "zg361_we_m265_route_a_effect")
        self.assertIn("contract_gold_reserved add = -20", handoff)
        self.assertIn("remove_short_term_gold = 20", handoff)
        self.assertIn("add_gold = 20", handoff)
        self.assertIn("contract_gold_paid add = -5", recovery)
        self.assertIn("remove_short_term_gold = 5", recovery)
        self.assertIn("add_gold = 5", recovery)

    def test_32_ad_reserves_shared_hc_once_and_candidate_does_not_duplicate_it(self) -> None:
        vacancy = block(self.effects, "zg361_we_m266_route_a_effect")
        candidate = block(self.effects, "zg361_we_m273_route_a_effect")
        self.assertIn("zg361_ch_hc_available add = -1", vacancy)
        self.assertIn("zg361_ch_hc_reserved add = 1", vacancy)
        self.assertNotIn("zg361_ch_hc_available add", candidate)
        self.assertIn("m273_additional_hc_reserved value = 0", candidate)
        self.assertIn("m273_credit_total_bps value = 10000", candidate)

    def test_33_interview_raw_votes_survive_calibration(self) -> None:
        vote = block(self.effects, "zg361_we_m267_route_a_effect")
        calibration = block(self.effects, "zg361_we_m268_route_a_effect")
        policy = block(self.effects, "zg361_we_m270_route_a_effect")
        self.assertIn("m267_raw_votes_frozen value = 1", vote)
        self.assertIn("m268_raw_votes_preserved value = 1", calibration)
        self.assertIn("m268_adjustment_bound value = 20", calibration)
        self.assertIn("m270_raw_votes_rewritten value = 0", policy)

    def test_34_269_is_delayed_outcome_not_immediate_rewrite(self) -> None:
        route = block(self.effects, "zg361_we_m269_route_a_effect")
        future = block(self.effects, "zg361_we_m269_future_consume_effect")
        self.assertIn("m269_outcome_pending value = 1", route)
        self.assertIn("days = 365", route)
        self.assertNotIn("m269_final_quality", route)
        self.assertIn("m269_outcome_settled value = 1", future)
        self.assertIn("m269_original_votes_preserved value = 1", future)
        self.assertEqual(1, future.count("m269_outcome_pending value = 0"))

    def test_35_referral_reward_is_conditional_and_consumed_by_outcome(self) -> None:
        referral = block(self.effects, "zg361_we_m271_route_a_effect")
        undisclosed = block(self.effects, "zg361_we_m271_route_b_effect")
        future = block(self.effects, "zg361_we_m269_future_consume_effect")
        self.assertIn("referral_gold_reserved add = 5", referral)
        self.assertIn("m271_referrer_recused_before_vote value = 1", referral)
        self.assertIn("m271_referrer_voted value = var:zg361_we_ad_external_referrer_voted", referral)
        self.assertIn("m271_referral_id value = var:zg361_we_ad_external_referral_id", referral)
        self.assertLess(gen.DOMAIN_ORDER["ad"].index(271), gen.DOMAIN_ORDER["ad"].index(267))
        self.assertIn("m271_reward_due_after_probation value = 1", referral)
        self.assertIn("var:zg361_case_ad_owner = { remove_short_term_gold = 5 }", referral)
        self.assertIn("m271_reward_paid_before_probation value = 1", undisclosed)
        self.assertIn("var:zg361_we_m271_referrer = { add_gold = 5 }", undisclosed)
        self.assertIn("referral_gold_reserved add = -5", future)
        self.assertIn("var:zg361_we_m271_referrer = { add_gold = 5 }", future)
        self.assertIn("var:zg361_we_m269_write_owner = { add_gold = 5 }", future)

    def test_36_offer_refusal_hold_has_frozen_due_and_no_state_rollback(self) -> None:
        refusal = block(self.effects, "zg361_we_m275_route_a_effect")
        due = block(self.effects, "zg361_we_m275_hold_due_effect")
        self.assertIn("m275_hold_start_cycle value = $TICKET_CYCLE$", refusal)
        self.assertIn("m275_hold_due_cycle value = { value = $TICKET_CYCLE$ add = 1 }", refusal)
        self.assertIn("m275_hc_lineage_receipt value = $TICKET_CASE$", refusal)
        self.assertIn("days = 90", refusal)
        self.assertIn("zg361_ch_hc_reserved add = -1", due)
        self.assertIn("zg361_ch_hc_available add = 1", due)
        self.assertIn("m275_old_attempt_reopened value = 0", due)
        self.assertNotIn("zg361_case_ad_state", due)

    def test_37_rehire_preserves_history_and_pip_exit_never_mints_hc(self) -> None:
        rehire = block(self.effects, "zg361_we_m276_route_b_effect")
        pip = block(self.effects, "zg361_we_m277_route_b_effect")
        self.assertIn("m276_old_history_retained value = 1", rehire)
        self.assertIn("m276_history_wipe_attempt value = 1", rehire)
        self.assertIn("m276_hc_touched value = 0", rehire)
        self.assertIn("m277_automatic_refill value = 1", pip)
        self.assertIn("m277_hc_minted value = 0", pip)

    def test_38_target_ratchet_freezes_50_split_and_peak_risk(self) -> None:
        limited = block(self.effects, "zg361_we_m355_route_a_effect")
        peak = block(self.effects, "zg361_we_m355_route_b_effect")
        for route in (limited, peak):
            self.assertIn("m355_repeatable_excess value = 20", route)
            self.assertIn("m355_windfall_excess value = 30", route)
            self.assertIn("m355_excess_total value = 50", route)
            self.assertIn("m355_old_fact_hash_retained value = 1", route)
        self.assertIn("m355_new_target value = 120", limited)
        self.assertIn("target_gold_reserved add = 10", limited)
        self.assertIn("m355_new_target value = 150", peak)
        self.assertIn("m355_underproduction_risk value = 50", peak)
        self.assertNotIn("target_gold_reserved add = 10", peak)

    def test_39_cutoff_audit_uses_completion_provenance_and_net_credit(self) -> None:
        timely = block(self.effects, "zg361_we_m356_route_a_effect")
        hoard = block(self.effects, "zg361_we_m356_route_b_effect")
        audit = block(self.effects, "zg361_we_m356_cutoff_audit_effect")
        for route in (timely, hoard):
            self.assertIn("m356_actual_value value = 100", route)
            self.assertIn("m356_net_credit value = 100", route)
            self.assertIn("m356_timestamp_frozen value = 1", route)
        self.assertIn("days = 90", hoard)
        self.assertIn("m356_credited_cycle value = var:zg361_we_m356_completion_cycle", audit)
        self.assertIn("m356_duplicate_credit_reversed value = 1", audit)

    def test_40_collective_action_conserves_agenda_quota_and_cost_direction(self) -> None:
        exception = block(self.effects, "zg361_we_m360_route_a_effect")
        forced = block(self.effects, "zg361_we_m360_route_b_effect")
        for route in (exception, forced):
            self.assertIn("m360_cohort_count value = 3", route)
            self.assertIn("m360_cohort_size value = var:zg361_we_al_external_collective_total_members", route)
            self.assertIn("m360_agenda_size value = var:zg361_we_al_external_collective_total_members", route)
            self.assertIn("m360_quota value = var:zg361_we_al_external_collective_total_quota", route)
            self.assertIn("m360_quota_partition value = var:zg361_we_al_external_collective_total_quota", route)
            self.assertIn("m360_agenda_equals_authoritative_cohort value = 1", route)
            self.assertIn("m360_manager_cost_direction value = { value = 0 subtract = var:zg361_we_al_external_collective_manager_cost_total }", route)
            self.assertEqual(3, route.count("manager_score add = { value = 0 subtract = scope:zg361_we_al_subject.var:zg361_we_al_external_collective_"))
            for slot in (1, 2, 3):
                self.assertIn(
                    f"al_external_collective_{slot}_member_hash = var:zg361_we_al_external_collective_{slot}_agenda_hash",
                    route,
                )
                self.assertIn(f"m360_cohort_{slot}_manager value = var:zg361_we_al_external_collective_{slot}_manager", route)
                self.assertIn(f"m360_cohort_{slot}_quota value = var:zg361_we_al_external_collective_{slot}_quota", route)
            self.assertNotIn("m360_quota_partition value = 2", route)
            self.assertNotIn("set_variable = { name = zg361_we_al_external_collective_1_cohort_id", route)
            self.assertIn("al_external_collective_submission_consumed value = 1", route)
            self.assertIn("al_external_collective_submission_active value = 0", route)
        self.assertIn(
            "al_external_collective_reform_effective_cycle = scope:zg361_we_expected_ticket_next_cycle",
            exception,
        )
        self.assertIn("m360_reform_proposal_id value = var:zg361_we_al_external_collective_reform_proposal_id", exception)
        for slot in (1, 2, 3):
            self.assertIn(f"var:zg361_we_al_external_collective_{slot}_exception_count = 0", forced)
            self.assertIn(
                f"var:zg361_we_al_external_collective_{slot}_forced_count = var:zg361_we_al_external_collective_{slot}_quota",
                forced,
            )

    def test_41_charter_is_top_liege_versioned_and_future_only(self) -> None:
        event = block(self.events, "zg361we.361")
        evidence = block(self.effects, "zg361_we_m361_route_a_effect")
        competition = block(self.effects, "zg361_we_m361_route_b_effect")
        future = block(self.effects, "zg361_we_m361_future_default_install_effect")
        self.assertIn("NOT = { liege = { zg361_is_celestial_liege_trigger = yes } }", event)
        self.assertIn("al_external_completed_cycle_receipt_count >= 3", event)
        self.assertIn("has_variable = zg361_we_realm_charter_current_version", evidence)
        self.assertNotIn("realm_charter_current_version <", evidence)
        self.assertIn("m361_effective_cycle value = { value = $TICKET_CYCLE$ add = 1 }", evidence)
        self.assertIn("m361_history_reset value = 0", evidence)
        self.assertIn("m361_noncompetition_ahead value = 3", evidence)
        self.assertIn("m361_delivery_horizon value = 2", evidence)
        self.assertIn("m361_priority_competition value = 1", competition)
        self.assertIn("m361_priority_fairness value = 2", competition)
        self.assertIn("m361_priority_innovation value = 3", competition)
        self.assertIn("m361_priority_warmth value = 4", competition)
        self.assertIn("m361_delivery_horizon value = 1", competition)
        for name in ("quota", "appeal", "bonus", "hc", "manager_accountability", "transparency"):
            self.assertIn(f"realm_future_default_{name}", future)
        self.assertIn("charter_current_case_rewritten value = 0", future)

    def test_42_route_c_is_debt_only_with_due_cycle(self) -> None:
        for spec in gen.MECHANISMS:
            route = block(self.effects, f"zg361_we_m{spec.mid}_route_c_effect")
            with self.subTest(mid=spec.mid):
                self.assertIn(f"m{spec.mid}_business_object_created value = 0", route)
                self.assertIn(f"m{spec.mid}_debt_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }}", route)
                self.assertIn("policy_debt add = 1", route)

    def test_43_finalizer_checks_gold_hours_shadow_and_shared_formal_hc(self) -> None:
        final = block(self.effects, "zg361_we_finalize_portfolio_effect")
        self.assertIn("final_operation_check = 40", final)
        self.assertIn("final_gold_check = var:zg361_we_gold_total", final)
        self.assertIn("final_hours_check = var:zg361_we_hours_total", final)
        self.assertIn("final_shadow_hc_check = var:zg361_we_shadow_hc_total", final)
        self.assertIn("final_formal_hc_check = var:zg361_ch_hc_authorized", final)
        self.assertIn("final_conservation_ok value = 1", final)

    def test_44_future_events_are_hidden_and_tuple_guarded(self) -> None:
        for mid, event_id in gen.FUTURE_EVENT.items():
            event = block(self.events, f"zg361we.{event_id}")
            self.assertIn("hidden = yes", event)
            effect_name = re.search(r"immediate = \{ (zg361_we_[a-z0-9_]+) = yes \}", event).group(1)
            effect = block(self.effects, effect_name)
            for name in ("write_owner", "write_subject", "write_cycle", "write_case", "receipt_owner", "receipt_subject", "receipt_cycle", "receipt_case"):
                self.assertIn(f"has_variable = zg361_we_m{mid}_{name}", effect)

    def test_45_localization_has_nine_language_key_parity(self) -> None:
        rows = {
            language: loc_rows(MOD_ROOT / "localization" / language / f"zg361_workforce_endgame_l_{language}.yml")
            for language in gen.LANGUAGES
        }
        expected = {
            key
            for mid in EXPECTED_IDS
            for key in (f"zg361we.{mid}.t", f"zg361we.{mid}.desc", f"zg361we.{mid}.a", f"zg361we.{mid}.b", f"zg361we.{mid}.c")
        }
        expected.update(
            f"zg361we.handoff.{step}.{suffix}"
            for step in (1, 2, 3)
            for suffix in ("t", "desc", "complete", "refuse")
        )
        for language, mapping in rows.items():
            self.assertEqual(expected, set(mapping), language)
        self.assertNotEqual(rows["english"], rows["simp_chinese"])

    def test_46_seven_languages_are_exact_english_placeholders(self) -> None:
        english = loc_rows(MOD_ROOT / "localization" / "english" / "zg361_workforce_endgame_l_english.yml")
        for language in ("french", "german", "japanese", "korean", "polish", "russian", "spanish"):
            path = MOD_ROOT / "localization" / language / f"zg361_workforce_endgame_l_{language}.yml"
            self.assertEqual(f"l_{language}:", read(path).splitlines()[0])
            self.assertEqual(english, loc_rows(path))

    def test_47_spec_maps_40_ids_and_keeps_static_boundary(self) -> None:
        ids = [int(mid) for mid in re.findall(r"\| (?:AB|AC|AD|AL) \| (\d{3}) \|", self.spec_text)]
        self.assertEqual(EXPECTED_IDS, set(ids))
        self.assertEqual(40, len(ids))
        for phrase in (
            "CK3 script static-ready",
            "没有中央 `on_action`",
            "没有 CK3 parser/error.log",
            "paused snapshot",
            "没有 MCP named action/query",
            "357–359",
            "其余七语是英文结构占位",
        ):
            self.assertIn(phrase, self.spec_text)

    def test_48_al_resume_consumes_external_tuple_and_restores_player_scopes(self) -> None:
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        for comparison in (
            "al_external_receipt_owner = root",
            "al_external_receipt_subject = this",
            "al_external_receipt_cycle = var:zg361_case_al_cycle_serial",
            "al_external_receipt_case = var:zg361_case_al_case_serial",
            "al_external_receipt_state = 4",
            "al_external_receipt_count = 3",
            "al_external_last_operation = 359",
        ):
            self.assertIn(comparison, entry)
        for scope in ("al_owner", "al_subject", "al_cycle", "al_case"):
            self.assertIn(f"zg361_we_{scope}", entry)
        self.assertNotIn("set_variable = { name = zg361_we_al_external_stage_receipts_verified", entry)

    def test_49_delayed_consumers_are_single_flight_state_and_choice_bound(self) -> None:
        for mid, pending in gen.FUTURE_PENDING.items():
            choices = gen.FUTURE_CHOICES[mid]
            route = block(self.effects, f"zg361_we_m{mid}_route_{'a' if 1 in choices else 'b'}_effect")
            self.assertIn(f"has_variable = zg361_we_{pending}", route)
            effect_name = {
                257: "zg361_we_m257_future_consume_effect",
                262: "zg361_we_m262_secondment_due_effect",
                263: "zg361_we_m263_extension_due_effect",
                269: "zg361_we_m269_future_consume_effect",
                275: "zg361_we_m275_hold_due_effect",
                355: "zg361_we_m355_target_install_effect",
                356: "zg361_we_m356_cutoff_audit_effect",
                361: "zg361_we_m361_future_default_install_effect",
            }[mid]
            future = block(self.effects, effect_name)
            self.assertIn(f"m{mid}_write_state = var:zg361_we_m{mid}_receipt_state", future)
            self.assertIn(f"m{mid}_receipt_state = {self.specs[mid].state}", future)
            self.assertIn(f"has_variable = zg361_we_m{mid}_receipt_choice", future)

    def test_50_secondment_waits_for_authoritative_due_before_player_263(self) -> None:
        routes = [
            block(self.effects, "zg361_we_m262_route_a_effect"),
            block(self.effects, "zg361_we_m262_route_b_effect"),
        ]
        due = block(self.effects, "zg361_we_m262_secondment_due_effect")
        event = block(self.events, "zg361we.262")
        for route in routes:
            self.assertIn("m262_review_pending value = 1", route)
            self.assertIn("id = zg361we.5262 days = 365", route)
            self.assertIn("ac_s05_deadline_pending value = 0", route)
        options = event.split("\n\toption = {")[1:]
        self.assertEqual(3, len(options))
        self.assertNotIn("trigger_event = { id = zg361we.263 }", options[0])
        self.assertNotIn("trigger_event = { id = zg361we.263 }", options[1])
        self.assertIn("trigger_event = { id = zg361we.263 }", options[2])
        self.assertIn("zg361_review_serial >= root.var:zg361_we_m262_due_cycle", due)
        self.assertIn("var:zg361_case_ac_state = 5", due)
        self.assertIn("zg361_we_ac_schedule_stage_05_deadline_effect = yes", due)
        self.assertIn("trigger_event = { id = zg361we.263 }", due)

    def test_51_secondment_extension_is_nonterminal_then_advances_at_new_due(self) -> None:
        extend = block(self.effects, "zg361_we_m263_route_b_effect")
        due = block(self.effects, "zg361_we_m263_extension_due_effect")
        self.assertIn("m263_terminal_choice value = 0", extend)
        self.assertIn("m263_extension_pending value = 1", extend)
        self.assertNotIn("zg361_case_ac_advance_05_effect", extend)
        self.assertIn("zg361_review_serial >= root.var:zg361_we_m263_extension_due_cycle", due)
        self.assertIn("m263_terminal_choice value = 1", due)
        self.assertIn("zg361_case_ac_advance_05_effect", due)
        self.assertIn("zg361_we_m264_begin_handoff_effect", due)
        self.assertNotIn("id = zg361we.264", due)

    def test_52_handoff_a_pays_b_refunds_and_both_release_shadow_slot(self) -> None:
        pay = block(self.effects, "zg361_we_m264_route_a_effect")
        terminate = block(self.effects, "zg361_we_m264_route_b_effect")
        self.assertIn("m264_payee value = var:zg361_we_m254_vendor_id", pay)
        self.assertIn("m264_accepted_by value = $TICKET_OWNER$", pay)
        self.assertIn("m264_payment_settled value = 1", pay)
        self.assertIn("remove_short_term_gold = 20", pay)
        self.assertIn("add_gold = 20", pay)
        self.assertIn("m264_payment_settled value = 0", terminate)
        self.assertIn("m264_payment_refunded value = 20", terminate)
        self.assertNotIn("remove_short_term_gold = 20", terminate)
        for route in (pay, terminate):
            self.assertIn("shadow_hc_active add = -1", route)
            self.assertIn("shadow_hc_available add = 1", route)
            self.assertIn("m264_handoff_flow_consumed value = 1", route)
            self.assertIn("m264_handoff_flow_active value = 0", route)
        self.assertEqual(1, pay.count("remove_short_term_gold = 20"))
        self.assertEqual(1, pay.count("add_gold = 20"))
        self.assertEqual(1, terminate.count("m264_payment_refunded value = 20"))
        self.assertNotIn("add_gold = 20", terminate)

    def test_53_fraud_recovery_requires_prior_evidence_and_frozen_payee(self) -> None:
        audit = block(self.effects, "zg361_we_m265_route_a_effect")
        for evidence in (
            "m259_responsibility_total_bps = 10000",
            "m261_actual_executor_frozen = 1",
            "m264_payment_settled = 1",
            "m264_payee = $TICKET_SUBJECT$",
            "m264_accepted_by = $TICKET_OWNER$",
        ):
            self.assertIn(evidence, audit)
        self.assertIn("m265_recovery_source value = $TICKET_SUBJECT$", audit)
        self.assertIn("m265_recovery_payee value = $TICKET_OWNER$", audit)

    def test_54_offer_refusal_prechecks_exact_lineage_and_never_goes_negative(self) -> None:
        refusal = block(self.effects, "zg361_we_m275_route_a_effect")
        for check in (
            "m266_hc_reservation_active = 1",
            "m266_hc_receipt = $TICKET_CASE$",
            "offer_gold_reserved >= 15",
            "gold_reserved >= 15",
        ):
            self.assertIn(check, refusal)
            self.assertLess(refusal.index(check), refusal.index("offer_gold_reserved add = -15"))
        due = block(self.effects, "zg361_we_m275_hold_due_effect")
        self.assertIn("m266_hc_receipt = var:zg361_we_m275_hc_lineage_receipt", due)
        self.assertIn("zg361_review_serial >= root.var:zg361_we_m275_hold_due_cycle", due)
        self.assertIn("id = zg361we.5275 days = 90", due)

    def test_55_hire_settles_offer_and_hc_before_delayed_quality_writeback(self) -> None:
        hire = block(self.effects, "zg361_we_m274_route_a_effect")
        outcome = block(self.effects, "zg361_we_m269_future_consume_effect")
        self.assertIn("offer_gold_reserved add = -15", hire)
        self.assertIn("zg361_ch_hc_reserved add = -1", hire)
        self.assertIn("zg361_ch_hc_occupied add = 1", hire)
        self.assertIn("m274_hired value = 1", hire)
        self.assertIn("m274_hire_case = var:zg361_we_m269_write_case", outcome)
        self.assertIn("formal_hc_active_case = var:zg361_we_m269_write_case", outcome)
        self.assertIn("m269_requisition_released value = 0", outcome)
        self.assertNotIn("zg361_ch_hc_reserved add", outcome)
        self.assertNotIn("zg361_ch_hc_available add", outcome)
        self.assertIn("m269_attribution_total_bps value = 10000", outcome)
        self.assertIn("m271_reward_settled value = 1", outcome)
        self.assertEqual(1, outcome.count("m269_outcome_pending value = 0"))

    def test_56_candidate_and_formal_hc_identity_locks_are_global_on_subject(self) -> None:
        conversion = block(self.effects, "zg361_we_m257_route_a_effect")
        owner = block(self.effects, "zg361_we_m273_route_a_effect")
        settle = block(self.effects, "zg361_we_m257_future_consume_effect")
        for lock in ("candidate_active", "formal_hc_pending", "formal_hc_active"):
            self.assertIn(f"zg361_we_{lock}", conversion)
            self.assertIn(f"zg361_we_{lock}", owner)
        self.assertIn("formal_hc_pending_owner value = $TICKET_OWNER$", conversion)
        self.assertIn("formal_hc_pending_case value = $TICKET_CASE$", conversion)
        self.assertIn("formal_hc_pending value = 0", settle)
        self.assertIn("formal_hc_active value = 1", settle)

    def test_57_switching_route_is_collision_red_not_idempotent(self) -> None:
        for spec in gen.MECHANISMS:
            route = block(self.effects, f"zg361_we_m{spec.mid}_route_a_effect")
            self.assertIn(f"name = zg361_we_last_red_code value = {spec.mid * 10 + 9}", route)
            self.assertIn("route collision typed RED", route)
            idem = route.index("idempotent no-op")
            collision = route.index("route collision typed RED")
            self.assertLess(idem, collision)

    def test_58_fixed_resource_books_are_not_reset_or_minted_per_cycle(self) -> None:
        init = block(self.effects, "zg361_we_initialize_portfolio_effect")
        self.assertEqual(1, init.count("name = zg361_we_gold_total value = 200"))
        self.assertEqual(1, init.count("name = zg361_we_gold_available value = 200"))
        self.assertNotIn("name = zg361_we_gold_total add", init)
        self.assertNotIn("name = zg361_we_gold_available add = 200", init)
        self.assertEqual(1, init.count("name = zg361_we_shadow_hc_total value = 4"))

    def test_59_finalizer_only_closes_after_nonnegative_exact_conservation(self) -> None:
        final = block(self.effects, "zg361_we_finalize_portfolio_effect")
        self.assertLess(final.index("portfolio_closed value = 0"), final.index("final_conservation_ok value = 1"))
        self.assertGreater(final.index("portfolio_closed value = 1"), final.index("final_conservation_ok value = 1"))
        for component in ("gold_available", "gold_reserved", "gold_paid", "shadow_hc_available", "zg361_ch_hc_reserved"):
            self.assertIn(f"{component} >= 0", final)
        self.assertIn("last_red_code value = 9099", final)
        self.assertIn("portfolio remains open", final)

    def test_60_manager_gate_and_361_extra_top_gate_are_separate(self) -> None:
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        resume, initial = entry.split("# Start one new portfolio. Replay cannot reset an active/same-cycle book.")
        self.assertEqual(1, resume.count("$SUBJECT$ = { zg361_is_celestial_liege_trigger = yes }"))
        self.assertNotIn("$SUBJECT$ = { zg361_is_celestial_liege_trigger = yes }", initial)
        self.assertIn("$SUBJECT$ = { zg361_we_ab_launch_effect = yes }", initial)
        event360 = block(self.events, "zg361we.360")
        event361 = block(self.events, "zg361we.361")
        self.assertNotIn("NOT = { liege = { zg361_is_celestial_liege_trigger = yes } }", event360)
        self.assertIn("NOT = { liege = { zg361_is_celestial_liege_trigger = yes } }", event361)

    def test_61_pip_exit_moves_occupied_to_frozen_not_available(self) -> None:
        exit_route = block(self.effects, "zg361_we_m277_route_a_effect")
        self.assertIn("zg361_ch_hc_occupied add = -1", exit_route)
        self.assertIn("zg361_ch_hc_frozen add = 1", exit_route)
        self.assertNotIn("zg361_ch_hc_available add", exit_route)
        self.assertIn("m277_displaced_subject value = $TICKET_SUBJECT$", exit_route)
        self.assertIn("m277_displaced_cost_provenance value = var:zg361_we_ad_external_exit_displaced_cost_receipt", exit_route)
        self.assertIn("m277_pip_case_frozen value = var:zg361_we_ad_external_pip_case_id", exit_route)
        self.assertIn("ad_external_pip_exit_consumed value = 1", exit_route)

    def test_62_charter_future_defaults_are_read_by_later_portfolio_init(self) -> None:
        init = block(self.effects, "zg361_we_initialize_portfolio_effect")
        future = block(self.effects, "zg361_we_m361_future_default_install_effect")
        for name in ("quota", "appeal", "bonus", "hc", "manager_accountability", "transparency"):
            self.assertIn(f"realm_future_default_{name}", future)
            self.assertIn(f"realm_current_default_{name} value = var:zg361_we_realm_future_default_{name}", init)
            self.assertIn(f"portfolio_default_{name} value = root.var:zg361_we_realm_current_default_{name}", init)

    def test_63_secondment_official_may_be_count_but_host_manager_is_authorized(self) -> None:
        for mid in (262, 263):
            for letter in "ab":
                route = block(self.effects, f"zg361_we_m{mid}_route_{letter}_effect")
                self.assertNotIn("var:zg361_case_ac_subject = { zg361_is_celestial_liege_trigger = yes }", route)
                if mid == 262:
                    self.assertIn("has_variable = zg361_we_ac_external_secondment_host_manager", route)
                    self.assertIn("var:zg361_we_ac_external_secondment_host_manager = { zg361_is_celestial_liege_trigger = yes }", route)
                    self.assertIn("NOT = { var:zg361_we_ac_external_secondment_host_manager = $TICKET_SUBJECT$ }", route)
                    self.assertIn("m262_host_manager value = var:zg361_we_ac_external_secondment_host_manager", route)
            debt = block(self.effects, f"zg361_we_m{mid}_route_c_effect")
            self.assertNotIn("ac_external_secondment_host_manager", debt)

    def test_64_all_delayed_flights_block_tuple_overwrite_at_entry(self) -> None:
        entry = block(self.effects, "zg361_we_open_portfolio_effect")
        initial = entry.split("# Start one new portfolio. Replay cannot reset an active/same-cycle book.")[1]
        for pending in (*gen.FUTURE_PENDING.values(), "m275_runner_reopen_pending"):
            self.assertIn(f"has_variable = zg361_we_{pending}", initial)
            self.assertIn(f"var:zg361_we_{pending} = 0", initial)
        self.assertIn("has_variable = zg361_we_ad_hc_flight_pending", initial)
        self.assertIn("var:zg361_we_ad_hc_flight_pending = 0", initial)

    def test_65_suspicion_without_evidence_never_recovers_gold(self) -> None:
        proven = block(self.effects, "zg361_we_m265_route_a_effect")
        suspicion = block(self.effects, "zg361_we_m265_route_b_effect")
        self.assertIn("m265_evidence_count value = 2", proven)
        self.assertIn("remove_short_term_gold = 5", proven)
        self.assertIn("m265_investigation_pending value = 1", suspicion)
        self.assertIn("m265_suspicion_only value = 1", suspicion)
        self.assertIn("m265_recovery_gold value = 0", suspicion)
        self.assertNotIn("remove_short_term_gold", suspicion)
        self.assertNotIn("contract_gold_recovered add", suspicion)

    def test_66_interview_identity_votes_and_evidence_are_complete_before_seal(self) -> None:
        for letter, referrer_voted in (("a", 0), ("b", 1)):
            route = block(self.effects, f"zg361_we_m267_route_{letter}_effect")
            receipt = route.index("zg361_case_kernel_record_operation_effect")
            for slot in (1, 2, 3):
                self.assertLess(route.index(f"has_variable = zg361_we_ad_external_interviewer_{slot}"), receipt)
                self.assertLess(route.index(f"has_variable = zg361_we_ad_external_vote_evidence_{slot}"), receipt)
                self.assertIn(f"m267_interviewer_{slot} value = var:zg361_we_ad_external_interviewer_{slot}", route)
                self.assertIn(f"m267_vote_{slot} value = var:zg361_we_ad_external_vote_{slot}", route)
                self.assertIn(f"m267_vote_evidence_{slot} value = var:zg361_we_ad_external_vote_evidence_{slot}", route)
            self.assertIn(f"ad_external_referrer_voted = {referrer_voted}", route)
            self.assertGreater(route.index("m267_raw_votes_frozen value = 1"), route.index("m267_vote_evidence_3 value"))

    def test_67_outcome_is_evidence_bound_duplicate_safe_and_clears_pending_last(self) -> None:
        outcome = block(self.effects, "zg361_we_m269_future_consume_effect")
        for name in (
            "outcome_id", "outcome_hire_case", "outcome_candidate", "outcome_quality",
            "outcome_evidence_id", "outcome_evidence_hash", "outcome_evidence_count",
            "outcome_observed_cycle",
        ):
            self.assertIn(f"has_variable = zg361_we_ad_external_{name}", outcome)
        self.assertIn("NOT = { var:zg361_we_m269_last_outcome_id = var:zg361_we_ad_external_outcome_id }", outcome)
        self.assertIn("ad_external_outcome_quality >= 1", outcome)
        self.assertIn("ad_external_outcome_quality <= 4", outcome)
        self.assertLess(outcome.index("m269_outcome_settled value = 1"), outcome.index("m269_outcome_pending value = 0"))
        self.assertIn("future_red_code value = 2692", outcome)

    def test_68_refusal_hold_keeps_or_releases_exact_hc_lineage(self) -> None:
        refusal = block(self.effects, "zg361_we_m275_route_a_effect")
        indefinite = block(self.effects, "zg361_we_m275_route_b_effect")
        due = block(self.effects, "zg361_we_m275_hold_due_effect")
        for route in (refusal, indefinite):
            self.assertIn("m275_refusal_reason_id value = var:zg361_we_ad_external_refusal_reason_id", route)
            self.assertNotIn("m269_watch_cancelled_by_refusal value = 1", route)
            self.assertIn("m275_not_applicable_hired value = 1", route)
        self.assertIn("m275_runner_up value = var:zg361_we_ad_external_runner_up", refusal)
        self.assertIn("m275_runner_up_evidence value = var:zg361_we_ad_external_runner_up_evidence", refusal)
        self.assertIn("var:zg361_we_m275_receipt_choice = 1", due)
        self.assertIn("m275_runner_reopen_pending value = 1", due)
        self.assertIn("m275_hold_released value = 0", due)
        self.assertIn("ad_external_m275_remediation_receipt = 1", due)
        self.assertIn("ad_external_m275_remediated_reason_id = var:zg361_we_m275_refusal_reason_id", due)
        self.assertIn("zg361_ch_hc_reserved add = -1", due)
        self.assertIn("zg361_ch_hc_available add = 1", due)
        self.assertIn("ad_hc_flight_pending value = 0", due)

    def test_69_collective_precheck_is_complete_before_receipt_or_cost(self) -> None:
        route = block(self.effects, "zg361_we_m360_route_a_effect")
        receipt = route.index("zg361_case_kernel_record_operation_effect")
        first_cost = route.index("manager_score add")
        for slot in (1, 2, 3):
            base = f"zg361_we_al_external_collective_{slot}"
            for name in (
                "cohort_id", "manager", "member_count", "member_hash", "agenda_count",
                "agenda_hash", "quota", "all_meet_evidence_id", "forced_count",
                "exception_count", "approver", "manager_cost", "partition_verified",
                "approval_verified",
            ):
                self.assertLess(route.index(f"has_variable = {base}_{name}"), receipt)
            self.assertGreater(route.index(f"m360_cohort_{slot}_cohort_id value"), receipt)
        self.assertLess(receipt, first_cost)

    def test_70_charter_uses_rolling_chain_and_amendments_are_monotonic(self) -> None:
        route = block(self.effects, "zg361_we_m361_route_a_effect")
        prepare = block(self.effects, "zg361_we_prepare_m361_charter_evidence_effect")
        ledger = block(self.effects, "zg361_we_append_completed_cycle_receipt_effect")
        future = block(self.effects, "zg361_we_m361_future_default_install_effect")
        self.assertIn("realm_charter_history_count = var:zg361_we_realm_charter_current_version", route)
        self.assertIn("realm_charter_current_version > 0", route)
        self.assertIn("al_external_charter_adopted_day > var:zg361_case_al_owner.var:zg361_we_realm_charter_current_adopted_day", route)
        self.assertIn(
            "realm_charter_current_effective_cycle < scope:zg361_we_expected_ticket_next_cycle",
            route,
        )
        self.assertIn("if = { limit = { var:zg361_we_realm_charter_current_version = 0 } set_variable = { name = zg361_we_realm_charter_anchor_cycle_1", route)
        self.assertNotIn("remove_variable = zg361_we_realm_charter_anchor_", route)
        self.assertIn("completed_cycle_ledger_previous_hash_2 = var:zg361_we_completed_cycle_ledger_chain_hash_1", prepare)
        self.assertIn("completed_cycle_ledger_previous_hash_3 = var:zg361_we_completed_cycle_ledger_chain_hash_2", prepare)
        self.assertIn("completed_cycle_ledger_count >= 3", ledger)
        self.assertIn("completed_cycle_ledger_cycle_1 value = var:zg361_we_completed_cycle_ledger_cycle_2", ledger)
        self.assertNotIn("al_external_completed_cycle_1 = var:zg361_case_al_owner.var:zg361_we_realm_charter_anchor_cycle_1", route)
        self.assertIn("realm_charter_current_version = root.var:zg361_we_m361_adopted_version", future)
        self.assertIn("zg361_review_serial >= root.var:zg361_we_m361_effective_cycle", future)

    def test_71_collective_capacity_and_identity_slots_are_explicit(self) -> None:
        self.assertEqual(6, gen.MAX_COLLECTIVE_OUTCOMES)
        route = block(self.effects, "zg361_we_m360_route_a_effect")
        self.assertIn("al_external_collective_total_quota <= 6", route)
        for cohort in (1, 2, 3):
            base = f"zg361_we_al_external_collective_{cohort}"
            for kind in ("forced", "exception"):
                for slot in range(1, gen.MAX_COLLECTIVE_OUTCOMES + 1):
                    identity = f"{base}_{kind}_{slot}"
                    self.assertIn(f"var:{base}_{kind}_count >= {slot}", route)
                    self.assertIn(f"has_variable = {identity}_character", route)
                    self.assertIn(f"var:{identity}_cohort_id = var:{base}_cohort_id", route)
                    self.assertIn(f"m360_cohort_{cohort}_{kind}_{slot}_character", route)
                    self.assertIn(f"m360_cohort_{cohort}_{kind}_{slot}_cohort_id", route)
                    self.assertIn(f"m360_cohort_{cohort}_{kind}_{slot}_member_evidence_receipt", route)
        self.assertIn(
            "NOT = { var:zg361_we_al_external_collective_1_forced_1_character = var:zg361_we_al_external_collective_2_forced_1_character }",
            route,
        )
        self.assertIn(
            "NOT = { var:zg361_we_al_external_collective_1_forced_1_character = var:zg361_we_al_external_collective_1_exception_1_character }",
            route,
        )

    def test_72_bool_values_never_stand_in_for_numeric_slots_or_counts(self) -> None:
        for name in (
            "m360_cohort_count", "m360_cohort_size", "m360_agenda_size", "m360_quota",
            "m360_participating_manager_count", "m361_completed_evidence_count",
        ):
            self.assertNotRegex(self.effects, rf"name = zg361_we_{name} value = (?:yes|no)\b")

    def test_73_count_baron_closes_as_honest_na_without_360_361_success(self) -> None:
        self.assertEqual(38, gen.NONMANAGER_OPERATION_COUNT)
        for letter in "abc":
            route = block(self.effects, f"zg361_we_m356_route_{letter}_effect")
            self.assertIn("NOT = { zg361_is_celestial_liege_trigger = yes }", route)
            self.assertIn("zg361_we_finalize_nonmanager_na_effect = yes", route)
            self.assertIn("awaiting_al_357_359 value = 1", route)
        final = block(self.effects, "zg361_we_finalize_nonmanager_na_effect")
        self.assertIn("EXPECTED_STATE = 2", final)
        self.assertIn("NOT = { zg361_is_celestial_liege_trigger = yes }", final)
        self.assertIn("operation_total = 40", final)
        self.assertIn("operation_used = 38", final)
        for check in ("final_gold_check", "final_hours_check", "final_shadow_hc_check", "final_formal_hc_check"):
            self.assertIn(check, final)
        self.assertIn("zg361_case_kernel_transition_effect", final)
        self.assertIn("NEXT_STATE = 7", final)
        self.assertIn("CLOSE_CASE = yes", final)
        self.assertIn("var:zg361_case_al_active = 0", final)
        markers = {
            "portfolio_terminal_na": 1,
            "portfolio_terminal_reason": 360361,
            "portfolio_terminal_owned_operations": 38,
            "portfolio_terminal_skipped_manager_only": 2,
            "portfolio_terminal_success": 0,
            "final_conservation_ok": 1,
            "portfolio_closed": 1,
            "portfolio_status": 7,
        }
        for name, value in markers.items():
            self.assertIn(f"name = zg361_we_{name} value = {value}", final)
        transition = final.index("zg361_case_kernel_transition_effect")
        self.assertLess(transition, final.index("portfolio_terminal_na value = 1"))
        self.assertLess(transition, final.index("final_conservation_ok value = 1"))
        self.assertNotIn("m360_receipt_", final)
        self.assertNotIn("m361_receipt_", final)

    def test_74_semantic_order_matches_real_object_dependencies(self) -> None:
        self.assertEqual(
            (254, 255, 260, 261, 256, 258, 259, 257, 262, 263, 264, 265),
            gen.DOMAIN_ORDER["ac"],
        )
        self.assertEqual(
            (266, 273, 271, 267, 268, 270, 272, 274, 275, 269, 276, 277),
            gen.DOMAIN_ORDER["ad"],
        )
        for mid, sources in gen.CURRENT_OBJECT_DEPENDENCIES.items():
            order = gen.DOMAIN_ORDER[self.specs[mid].domain]
            for source_mid in sources:
                self.assertLess(order.index(source_mid), order.index(mid), (source_mid, mid))

    def test_75_ab_routes_require_consumed_current_case_objects_but_c_does_not(self) -> None:
        for mid, sources in gen.CURRENT_OBJECT_DEPENDENCIES.items():
            route_a = block(self.effects, f"zg361_we_m{mid}_route_a_effect")
            pre_a = route_a.split("zg361_case_kernel_record_operation_effect", 1)[0]
            route_c = block(self.effects, f"zg361_we_m{mid}_route_c_effect")
            pre_c = route_c.split("zg361_case_kernel_record_operation_effect", 1)[0]
            for source_mid in sources:
                source = self.specs[source_mid]
                for fragment in (
                    f"m{source_mid}_business_object_created = 1",
                    f"m{source_mid}_object_owner = $TICKET_OWNER$",
                    f"m{source_mid}_object_subject = $TICKET_SUBJECT$",
                    f"m{source_mid}_object_cycle = $TICKET_CYCLE$",
                    f"m{source_mid}_object_case = $TICKET_CASE$",
                    f"m{source_mid}_object_consumed = 1",
                    f"m{source_mid}_consumer_{source.consumer_key} = 1",
                ):
                    self.assertIn(fragment, pre_a, (source_mid, mid, fragment))
                    if not (mid == 263 and source_mid == 262 and fragment.endswith("business_object_created = 1")):
                        self.assertNotIn(fragment, pre_c, (source_mid, mid, fragment))

    def test_76_offer_outcomes_are_mutually_exclusive_and_hidden_when_inapplicable(self) -> None:
        counter = block(self.events, "zg361we.274")
        refusal = block(self.events, "zg361we.275")
        route_275 = block(self.effects, "zg361_we_m275_route_a_effect")
        route_269 = block(self.effects, "zg361_we_m269_route_a_effect")
        self.assertIn("m274_hired = 1", counter)
        self.assertIn("m274_business_object_created = 1", counter)
        self.assertIn("m274_object_cycle = scope:zg361_we_ad_cycle", counter)
        self.assertIn("m274_object_case = scope:zg361_we_ad_case", counter)
        self.assertIn("zg361_we_m275_route_a_effect", counter)
        self.assertIn("else = { trigger_event = { id = zg361we.275 } }", counter)
        self.assertIn("m275_not_applicable_hired value = 1", route_275)
        self.assertIn("m275_resources_touched value = 0", route_275)
        self.assertIn("m275_refusal = 1", refusal)
        self.assertIn("m275_business_object_created = 1", refusal)
        self.assertIn("m275_object_cycle = scope:zg361_we_ad_cycle", refusal)
        self.assertIn("m275_object_case = scope:zg361_we_ad_case", refusal)
        self.assertIn("zg361_we_m269_route_a_effect", refusal)
        self.assertIn("m269_not_applicable_no_hire value = 1", route_269)
        self.assertIn("m269_outcome_pending value = 0", route_269)

    def test_77_all_c_routes_create_consumable_open_debt(self) -> None:
        for mid in sorted(self.specs):
            route = block(self.effects, f"zg361_we_m{mid}_route_c_effect")
            consumer = block(self.effects, f"zg361_we_m{mid}_consume_effect")
            receipt = route.index("zg361_case_kernel_record_operation_effect")
            for fragment in (
                f"m{mid}_debt_owner value = $TICKET_OWNER$",
                f"m{mid}_debt_subject value = $TICKET_SUBJECT$",
                f"m{mid}_debt_cycle value = $TICKET_CYCLE$",
                f"m{mid}_debt_case value = $TICKET_CASE$",
                f"m{mid}_debt_due_cycle value = {{ value = $TICKET_CYCLE$ add = 1 }}",
                f"m{mid}_debt_open value = 1",
                f"m{mid}_business_object_created value = 0",
            ):
                self.assertIn(fragment, route, (mid, fragment))
                self.assertGreater(route.index(fragment), receipt, (mid, fragment))
            self.assertIn(f"m{mid}_debt_open = 1", consumer)
            self.assertIn(f"m{mid}_debt_visible_to_settlement value = 1", consumer)

    def test_78_real_269_waits_for_future_settlement_then_resumes_stage_6(self) -> None:
        route = block(self.effects, "zg361_we_m269_route_a_effect")
        future = block(self.effects, "zg361_we_m269_future_consume_effect")
        hired_branch = route[route.index("m269_not_applicable_no_hire value = 0"):]
        self.assertIn("m269_outcome_pending value = 1", hired_branch)
        self.assertIn("ad_s05_deadline_pending value = 0", hired_branch)
        self.assertLess(
            route.index("m269_not_applicable_no_hire value = 1"),
            route.index("zg361_case_ad_advance_05_effect"),
        )
        self.assertLess(
            future.index("m269_outcome_settled value = 1"),
            future.index("zg361_case_ad_advance_05_effect"),
        )
        self.assertLess(
            future.index("zg361_case_ad_advance_05_effect"),
            future.index("zg361_we_m276_route_a_effect"),
        )
        self.assertIn("else = { var:zg361_we_m269_write_owner = { trigger_event = { id = zg361we.276 } } }", future)

    def test_79_offer_and_pip_paths_reject_stale_branch_flags(self) -> None:
        counter_a = block(self.effects, "zg361_we_m274_route_a_effect")
        counter_b = block(self.effects, "zg361_we_m274_route_b_effect")
        pip_a = block(self.effects, "zg361_we_m277_route_a_effect")
        future = block(self.effects, "zg361_we_m269_future_consume_effect")
        self.assertLess(counter_a.index("m274_hired value = 0"), counter_a.index("m274_hired value = 1"))
        self.assertIn("m274_hired value = 0", counter_b)
        self.assertNotIn("m274_hired value = 1", counter_b)
        receipt = pip_a.index("zg361_case_kernel_record_operation_effect")
        for fragment in (
            "m269_business_object_created = 1",
            "m269_object_cycle = $TICKET_CYCLE$",
            "m269_object_case = $TICKET_CASE$",
            "m269_object_consumed = 1",
            "m269_consumer_write_back_hire_quality_269 = 1",
            "m269_outcome_settled = 1",
            "m269_not_applicable_no_hire = 0",
            "formal_hc_active_case = $TICKET_CASE$",
        ):
            self.assertIn(fragment, pip_a, fragment)
            self.assertLess(pip_a.index(fragment), receipt, fragment)
        self.assertNotIn("m269_watch_cancelled_by_refusal", future)
        self.assertNotIn("m269_cancel_receipt_consumed", future)

    def test_80_deferred_domains_release_abandoned_finite_resources(self) -> None:
        init = block(self.effects, "zg361_we_initialize_portfolio_effect")
        ac_release = block(self.effects, "zg361_we_release_abandoned_ac_resources_effect")
        ad_release = block(self.effects, "zg361_we_release_abandoned_ad_resources_effect")
        ac_last = block(self.effects, "zg361_we_m265_route_c_effect")
        ad_last = block(self.effects, "zg361_we_m277_route_c_effect")
        self.assertIn("NOT = { has_variable = zg361_we_overtime_pending }", init)
        self.assertIn("NOT = { has_variable = zg361_we_leave_bank }", init)
        self.assertNotIn("set_variable = { name = zg361_we_overtime_pending value = 0 }\n\tset_variable", init)
        for fragment in (
            "contract_gold_reserved > 0",
            "gold_reserved add = { value = var:zg361_we_ac_release_gold multiply = -1 }",
            "shadow_hc_available add = var:zg361_we_ac_release_shadow",
            "shadow_hc_active value = 0",
        ):
            self.assertIn(fragment, ac_release)
        for fragment in (
            "offer_gold_reserved > 0",
            "m271_reward_escrowed = 1",
            "m266_hc_reservation_active = 1",
            "zg361_we_m275_hold_pending",
            "zg361_ch_hc_reserved add = -1",
            "zg361_ch_hc_available add = 1",
            "ad_hc_flight_pending value = 0",
        ):
            self.assertIn(fragment, ad_release)
        self.assertLess(ac_last.index("zg361_we_release_abandoned_ac_resources_effect"), ac_last.index("zg361_we_ad_launch_effect"))
        self.assertLess(ad_last.index("zg361_we_release_abandoned_ad_resources_effect"), ad_last.index("zg361_we_al_launch_effect"))

    def test_81_every_c_debt_has_exact_due_consumer_conservation_and_bounded_escalation(self) -> None:
        for mid, spec in sorted(self.specs.items()):
            route = block(self.effects, f"zg361_we_m{mid}_route_c_effect")
            due = block(self.effects, f"zg361_we_m{mid}_consume_due_debt_effect")
            for field in (
                "owner", "subject", "cycle", "case", "state", "type_code", "id",
                "consumer_contract", "due_cycle", "open", "consumed", "escalation_count",
            ):
                self.assertIn(f"m{mid}_debt_{field}", route, (mid, field))
                self.assertIn(f"m{mid}_debt_{field}", due, (mid, field))
            self.assertIn(f"m{mid}_debt_state = var:zg361_we_m{mid}_write_state", due)
            self.assertIn(f"m{mid}_debt_type_code = {mid}", due)
            self.assertIn(f"m{mid}_debt_consumer_contract = {mid}", due)
            self.assertIn("hours_available add = -2", due)
            self.assertIn("hours_governance add = 2", due)
            self.assertIn("policy_debt add = -1", due)
            self.assertIn(f"m{mid}_debt_escalation_count < 2", due)
            self.assertIn("manager_score add = -2", due)
            self.assertIn(f"m{mid}_debt_open value = 0", due)
            self.assertIn(f"m{mid}_debt_consumed value = 1", due)
            self.assertIn("future_status value = 2", due)
            self.assertIn(f"debt_blocked_reason value = {70000 + mid}", due)
            self.assertIn(f"id = zg361we.{gen.DEBT_EVENT[mid]} days = 365", route)
            self.assertIn(f"zg361we.{gen.DEBT_EVENT[mid]}", self.events)

    def test_82_external_fact_adapters_freeze_real_274_275_276_277_objects(self) -> None:
        appointment = block(self.effects, "zg361_we_submit_ad_appointment_receipt_effect")
        runner = block(self.effects, "zg361_we_consume_m275_runner_reopen_effect")
        rehire = block(self.effects, "zg361_we_submit_m276_rehire_history_effect")
        pip_exit = block(self.effects, "zg361_we_submit_m277_closed_pip_exit_effect")
        self.assertNotIn("zg361_we_submit_m264_handoff_fact_effect", self.effects)
        self.assertIn("$APPOINTMENT_CONFIRMED$ = 1", appointment)
        self.assertIn("$APPOINTED_CHARACTER$ = $TICKET_SUBJECT$", appointment)
        self.assertIn("ad_external_position_receipt_hash", appointment)
        self.assertIn("$CENTRAL_REQUISITION_OPENED$ = 1", runner)
        self.assertIn("NOT = { $NEW_REQUISITION_CASE$ = $TICKET_CASE$ }", runner)
        self.assertIn("m275_runner_reopen_consumed value = 1", runner)
        self.assertIn("$HISTORICAL_CYCLE$ < $TICKET_CYCLE$", rehire)
        self.assertIn("NOT = { $HISTORICAL_CASE_ID$ = $TICKET_CASE$ }", rehire)
        self.assertIn("$PIP_CLOSED$ = 1", pip_exit)
        self.assertIn("$EXIT_CONFIRMED$ = 1", pip_exit)
        self.assertIn("$EXITED_CHARACTER$ = $TICKET_SUBJECT$", pip_exit)
        for code, adapter in ((2741, appointment), (2752, runner), (2761, rehire), (2771, pip_exit)):
            self.assertIn(f"adapter_blocked_reason value = {code}", adapter)

    def test_82a_m262_real_host_selector_accepts_count_subject_but_not_count_manager(self) -> None:
        selector = block(self.effects, "zg361_we_ac_freeze_m262_host_manager_effect")
        route_a = block(self.effects, "zg361_we_m262_route_a_effect")
        route_b = block(self.effects, "zg361_we_m262_route_b_effect")
        route_c = block(self.effects, "zg361_we_m262_route_c_effect")
        self.assertIn("$TICKET_SUBJECT$ = this", selector)
        self.assertNotIn("$TICKET_SUBJECT$ = { zg361_is_celestial_liege_trigger = yes }", selector)
        self.assertIn("$TICKET_OWNER$ = { zg361_is_celestial_liege_trigger = yes }", selector)
        self.assertIn("liege = { zg361_is_celestial_liege_trigger = yes", selector)
        self.assertIn("ordered_vassal = {", selector)
        self.assertIn("limit = { zg361_is_celestial_liege_trigger = yes", selector)
        self.assertIn("NOT = { this = scope:zg361_we_m262_host_subject_scope }", selector)
        self.assertIn("m262_host_selection_blocked_reason value = 2621", selector)
        for route in (route_a, route_b):
            self.assertIn("zg361_we_ac_freeze_m262_host_manager_effect", route)
        self.assertNotIn("zg361_we_ac_freeze_m262_host_manager_effect", route_c)

    def test_82b_m264_player_milestones_are_serial_real_receipts(self) -> None:
        begin = block(self.effects, "zg361_we_m264_begin_handoff_effect")
        documentation = block(self.effects, "zg361_we_m264_complete_documentation_effect")
        shadowing = block(self.effects, "zg361_we_m264_complete_shadowing_effect")
        practical = block(self.effects, "zg361_we_m264_complete_practical_effect")
        refusal = block(self.effects, "zg361_we_m264_refuse_handoff_effect")
        self.assertIn("EXPECTED_STATE = 6", begin)
        for mid in (254, 256, 261, 262, 263):
            self.assertIn(f"m{mid}_object_case = $TICKET_CASE$", begin)
            self.assertIn(f"m{mid}_object_consumed = 1", begin)
        self.assertIn("m264_handoff_step value = 1", begin)
        self.assertIn("m264_documentation_receipt_id value = { value = var:zg361_we_m264_handoff_case multiply = 10000 add = 2641 }", documentation)
        self.assertIn("m264_handoff_documentation_source_object value = var:zg361_we_m261_object_id", documentation)
        self.assertIn("id = zg361we.52650 days = 30", documentation)
        self.assertIn("m264_shadowing_receipt_id value = { value = var:zg361_we_m264_handoff_case multiply = 10000 add = 2642 }", shadowing)
        self.assertIn("m264_handoff_shadowing_source_object value = var:zg361_we_m263_object_id", shadowing)
        self.assertIn("id = zg361we.52651 days = 30", shadowing)
        self.assertIn("m264_practical_receipt_id value = { value = var:zg361_we_m264_handoff_case multiply = 10000 add = 2643 }", practical)
        self.assertIn("m264_handoff_practical_source_object value = var:zg361_we_m256_object_id", practical)
        self.assertIn("m264_handoff_response value = 1", practical)
        self.assertIn("m264_handoff_refusal_reason value = $EXPECTED_STEP$", refusal)
        self.assertNotIn("_hash", "\n".join((begin, documentation, shadowing, practical, refusal)))
        for step, event_id, effect_name in (
            (1, 52640, "zg361_we_m264_complete_documentation_effect"),
            (2, 52641, "zg361_we_m264_complete_shadowing_effect"),
            (3, 52642, "zg361_we_m264_complete_practical_effect"),
        ):
            event = block(self.events, f"zg361we.{event_id}")
            self.assertIn("option = {", event)
            self.assertIn("is_ai = no", event)
            self.assertIn("this = scope:zg361_we_m264_handoff_subject_scope", event)
            self.assertIn("this = scope:zg361_we_m264_handoff_owner_scope", event)
            self.assertIn(effect_name, event)
            self.assertIn(f"EXPECTED_STEP = {step}", event)

    def test_82c_m264_dispatch_never_sends_visible_event_to_ai(self) -> None:
        for step, event_id in ((1, 52640), (2, 52641), (3, 52642)):
            dispatch = block(self.effects, f"zg361_we_m264_dispatch_handoff_step_{step}_effect")
            self.assertIn(f"if = {{ limit = {{ is_ai = no }} trigger_event = {{ id = zg361we.{event_id} }} }}", dispatch)
            self.assertIn("else_if = { limit = { var:zg361_we_m264_handoff_owner = { is_ai = no } }", dispatch)
            self.assertIn(f"else = {{ zg361_we_m264_complete_", dispatch)
            self.assertLess(
                dispatch.index(f"if = {{ limit = {{ is_ai = no }} trigger_event = {{ id = zg361we.{event_id} }} }}"),
                dispatch.index("else_if = { limit = { var:zg361_we_m264_handoff_owner = { is_ai = no } }"),
                "a human assessed subject must receive their own event before any manager proxy branch",
            )
        owner_review = block(self.effects, "zg361_we_m264_queue_owner_review_effect")
        self.assertIn("limit = { var:zg361_we_m264_handoff_owner = { is_ai = yes } }", owner_review)
        self.assertIn("else = { var:zg361_we_m264_handoff_owner = { trigger_event = { id = zg361we.264 } } }", owner_review)

    def test_82d_all_old_ac_handoff_reads_are_eliminated(self) -> None:
        self.assertNotIn("zg361_we_ac_external_handoff_", self.effects)
        self.assertNotIn("zg361_we_ac_external_handoff_", self.events)

    def test_83_collective_submission_is_exact_three_cohorts_append_only_then_sealed(self) -> None:
        begin = block(self.effects, "zg361_we_begin_al_three_cohort_collective_effect")
        seal = block(self.effects, "zg361_we_seal_al_three_cohort_collective_effect")
        self.assertIn("EXPECTED_STATE = 4", begin)
        self.assertIn("al_external_collective_cohort_count value = 3", begin)
        self.assertIn("NOT = { $C1_COHORT_ID$ = $C2_COHORT_ID$ }", begin)
        self.assertIn("NOT = { $C1_MANAGER$ = $C2_MANAGER$ }", begin)
        self.assertIn("$TOTAL_QUOTA$ <= 6", begin)
        for cohort in (1, 2, 3):
            for kind in ("forced", "exception"):
                for slot in range(1, gen.MAX_COLLECTIVE_OUTCOMES + 1):
                    appender = block(self.effects, f"zg361_we_append_al_collective_{cohort}_{kind}_{slot}_effect")
                    identity = f"al_external_collective_{cohort}_{kind}_{slot}"
                    self.assertIn(f"{identity}_character value = $CHARACTER$", appender)
                    self.assertIn(f"{identity}_member_evidence_id value = $MEMBER_EVIDENCE_ID$", appender)
                    self.assertIn(f"{identity}_member_evidence_hash value = $MEMBER_EVIDENCE_HASH$", appender)
                    self.assertIn("adapter_status value = 2", appender)
        self.assertIn("al_external_collective_submission_sealed value = 1", seal)
        self.assertIn("adapter_blocked_reason value = 3603", seal)

    def test_84_three_cycle_ledger_is_identity_bound_idempotent_and_consumed_once(self) -> None:
        ledger = block(self.effects, "zg361_we_append_completed_cycle_receipt_effect")
        prepare = block(self.effects, "zg361_we_prepare_m361_charter_evidence_effect")
        route = block(self.effects, "zg361_we_m361_route_a_effect")
        for field in ("owner", "subject", "cycle_serial", "case_serial"):
            self.assertIn(f"zg361_case_al_{field}", ledger)
        self.assertIn("portfolio_closed = 1", ledger)
        self.assertIn("final_conservation_ok = 1", ledger)
        self.assertIn("completed_cycle_ledger_tail_hash = $PREVIOUS_CHAIN_HASH$", ledger)
        self.assertIn("NOT = { $NEW_CHAIN_HASH$ = $PREVIOUS_CHAIN_HASH$ }", ledger)
        self.assertIn("completed_cycle_ledger_last_subject = $TICKET_SUBJECT$", ledger)
        self.assertIn("completed_cycle_ledger_last_case = $TICKET_CASE$", ledger)
        self.assertIn("adapter_status value = 2", ledger)
        self.assertIn("completed_cycle_ledger_count = 3", prepare)
        self.assertIn("completed_cycle_ledger_cycle_3 < $TICKET_CYCLE$", prepare)
        self.assertIn("al_external_charter_evidence_ready value = 1", prepare)
        self.assertIn("al_external_long_report_hash value = $LONG_REPORT_HASH$", prepare)
        self.assertIn("al_external_charter_evidence_consumed value = 1", route)
        self.assertIn("al_external_charter_evidence_ready value = 0", route)

    def test_85_native_appointment_is_never_faked_by_the_recruitment_route(self) -> None:
        route = block(self.effects, "zg361_we_m274_route_a_effect")
        receipt = block(self.effects, "zg361_we_submit_ad_appointment_receipt_effect")
        self.assertIn("ad_external_appointment_consumed = 0", route)
        self.assertIn("m274_native_appointment_confirmed value = 1", route)
        self.assertIn("m274_position_receipt_hash value = var:zg361_we_ad_external_position_receipt_hash", route)
        self.assertIn("already-confirmed appointment receipt", self.effects)
        self.assertNotIn("appoint_court_position", route)
        self.assertIn("adapter_blocked_reason value = 2741", receipt)

    def test_86_loader_external_producer_ledger_is_exact_and_honest(self) -> None:
        self.assertIn("538134E409393CC1CAF7BC0736B385594D2344B55E2502C5D6D4A5BBDDBD9512", self.ledger_text)
        ac = set(re.findall(r"zg361_we_ac_external_[a-z0-9_]+", self.ledger_text))
        ad = set(re.findall(r"zg361_we_ad_external_[a-z0-9_]+", self.ledger_text))
        self.assertEqual(20, len(ac))
        self.assertEqual(80, len(ad))
        self.assertIn("3×(14+36)+17=167", self.ledger_text)
        self.assertIn("AD 80 + AL collective 167 +", self.ledger_text)
        self.assertIn("AL charter 28", self.ledger_text)
        self.assertIn("仍余 275", self.ledger_text)
        self.assertIn("尚无变更后的 loader/live 证据", self.ledger_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)

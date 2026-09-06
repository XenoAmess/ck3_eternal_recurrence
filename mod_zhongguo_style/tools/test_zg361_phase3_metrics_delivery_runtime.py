#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static contract tests for the phase-3 AA/AG/AJ CK3 runtime package.

Passing this suite proves deterministic generated structure only.  It is not a
CK3 parser result, paused snapshot, MCP result, or live gameplay evidence.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
MOD_ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

import gen_361_phase3_metrics_delivery_runtime as gen


EFFECTS_PATHS = tuple(
    MOD_ROOT / "common" / "scripted_effects" / filename
    for filename, _names in gen.EFFECT_GROUPS
)
EVENTS_PATH = MOD_ROOT / "events" / "zg361_phase3_metrics_delivery_runtime_events.txt"
SPEC_PATH = MOD_ROOT / "docs" / "361-phase3-metrics-delivery-runtime-spec.md"
EXPECTED_IDS = set(range(229, 242)) | set(range(301, 312)) | set(range(334, 345))
ILLEGAL_TRIGGER_ARITHMETIC_RHS = re.compile(
    r"(?:\b(?:root\.)?var:[^\s{}=<>]+|\bscope:[^\s{}=<>]+|\$[A-Z0-9_]+\$)"
    r"\s*(?:=|>=|<=|>|<)\s*\{\s*value\s*="
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def block(text: str, name: str) -> str:
    match = re.search(rf"(?m)^{re.escape(name)} = \{{", text)
    if match is None:
        raise AssertionError(f"missing block {name}")
    start = match.start()
    depth = 0
    opened = False
    for index in range(start, len(text)):
        if text[index] == "{":
            depth += 1
            opened = True
        elif text[index] == "}":
            depth -= 1
            if opened and depth == 0:
                return text[start : index + 1]
    raise AssertionError(f"unbalanced block {name}")


def loc_rows(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for line in read(path).splitlines()[1:]:
        match = re.match(r'\s*([^:]+):0\s+"(.*)"\s*$', line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


class GeneratorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.effect_parts = {
            filename: read(MOD_ROOT / "common" / "scripted_effects" / filename)
            for filename, _names in gen.EFFECT_GROUPS
        }
        cls.effects = "\n\n".join(cls.effect_parts.values())
        cls.historical_effects = gen.render_effects().decode("utf-8-sig")
        cls.events = read(EVENTS_PATH)
        cls.spec = read(SPEC_PATH)
        cls.specs = gen.by_id()

    def test_readiness_is_honest(self) -> None:
        self.assertEqual(gen.READINESS, "ck3-script-static-ready-not-live")
        self.assertIn("No CK3 parser/paused/live evidence is claimed", self.effects)

    def test_exact_id_coverage(self) -> None:
        self.assertEqual(set(self.specs), EXPECTED_IDS)
        self.assertEqual(len(gen.MECHANISMS), 35)
        self.assertEqual(sum(map(len, gen.DOMAIN_ORDER.values())), 35)
        self.assertEqual(gen.PLAYER_BACKGROUND_IDS | gen.PLAYER_VISIBLE_IDS, EXPECTED_IDS)
        self.assertFalse(gen.PLAYER_BACKGROUND_IDS & gen.PLAYER_VISIBLE_IDS)
        self.assertEqual(len(gen.PLAYER_BACKGROUND_IDS), 22)
        self.assertEqual(len(gen.PLAYER_VISIBLE_IDS), 13)

    def test_domain_ranges(self) -> None:
        self.assertEqual({mid for mid, spec in self.specs.items() if spec.domain == "aa"}, set(range(229, 242)))
        self.assertEqual({mid for mid, spec in self.specs.items() if spec.domain == "ag"}, set(range(301, 312)))
        self.assertEqual({mid for mid, spec in self.specs.items() if spec.domain == "aj"}, set(range(334, 345)))

    def test_unique_semantic_fields(self) -> None:
        self.assertEqual(len({spec.field for spec in gen.MECHANISMS}), 35)

    def test_outputs_are_exactly_independent_package(self) -> None:
        outputs = gen.outputs()
        self.assertEqual(len(outputs), 10 + len(gen.EFFECT_GROUPS))
        self.assertEqual({path.name for path in outputs}, {
            *(filename for filename, _names in gen.EFFECT_GROUPS),
            "zg361_phase3_metrics_delivery_runtime_events.txt",
            *(f"zg361_phase3_metrics_delivery_l_{language}.yml" for language in gen.LANGUAGES),
        })

    def test_generator_check_mode_is_green(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOLS / "gen_361_phase3_metrics_delivery_runtime.py"), "--check"],
            cwd=MOD_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("GREEN", result.stdout)

    def test_all_sources_and_outputs_have_bom(self) -> None:
        paths = [TOOLS / "gen_361_phase3_metrics_delivery_runtime.py", Path(__file__), SPEC_PATH, *gen.outputs()]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.read_bytes().startswith(gen.BOM))

    def test_generated_script_braces_balance(self) -> None:
        for path in (*EFFECTS_PATHS, EVENTS_PATH):
            with self.subTest(path=path):
                payload = read(path)
                self.assertEqual(payload.count("{"), payload.count("}"))

    def test_effects_are_complete_byte_identical_purpose_shards(self) -> None:
        self.assertEqual(len(gen.EFFECT_GROUPS), 40)
        self.assertEqual(gen.EFFECT_HARD_LIMIT_EXCEPTIONS, {})
        effects_dir = MOD_ROOT / "common" / "scripted_effects"
        self.assertFalse((effects_dir / gen.LEGACY_EFFECT_FILENAME).exists())

        historical_bytes = gen.render_effects()
        self.assertEqual(len(historical_bytes), 1_915_858)
        self.assertEqual(
            hashlib.sha256(historical_bytes).hexdigest(),
            "a06d8f47b10fab50989d7799c0d671fa67f3cd4912958152086551be006ade96",
        )
        historical = historical_bytes.decode("utf-8-sig")
        historical_names = re.findall(
            r"(?m)^(zg361_p3_[a-z0-9_]+_effect)\s*=\s*\{",
            historical,
        )
        configured_names = [
            name for _filename, names in gen.EFFECT_GROUPS for name in names
        ]
        self.assertEqual(len(historical_names), 195)
        self.assertEqual(len(set(historical_names)), 195)
        self.assertEqual(len(configured_names), 195)
        self.assertEqual(len(set(configured_names)), 195)
        self.assertEqual(set(configured_names), set(historical_names))

        for filename, expected_names in gen.EFFECT_GROUPS:
            with self.subTest(filename=filename):
                self.assertGreaterEqual(len(expected_names), 1)
                self.assertLessEqual(len(expected_names), gen.EFFECT_TARGET_MAX)
                self.assertLessEqual(len(expected_names), gen.EFFECT_HARD_MAX)
                self.assertNotIn("acceptance", filename)
                path = effects_dir / filename
                self.assertTrue(
                    path.read_bytes().startswith(
                        gen.BOM + gen.HEADER.encode("utf-8")
                    )
                )
                part = self.effect_parts[filename]
                actual_names = re.findall(
                    r"(?m)^(zg361_p3_[a-z0-9_]+_effect)\s*=\s*\{",
                    part,
                )
                self.assertEqual(actual_names, list(expected_names))
                for name in expected_names:
                    self.assertEqual(block(part, name), block(historical, name))

    def test_check_mode_rejects_generated_effect_residue(self) -> None:
        effects_dir = MOD_ROOT / "common" / "scripted_effects"
        cases = (
            (gen.LEGACY_EFFECT_FILENAME, "legacy monolith"),
            (
                "zg361_phase3_retired_purpose_effects.txt",
                "unexpected generated effect residue",
            ),
        )
        for filename, expected_label in cases:
            residue = effects_dir / filename
            with self.subTest(filename=filename):
                self.assertFalse(residue.exists())
                try:
                    residue.write_bytes(gen.render_effects())
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(
                                TOOLS
                                / "gen_361_phase3_metrics_delivery_runtime.py"
                            ),
                            "--check",
                        ],
                        cwd=MOD_ROOT,
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(expected_label, result.stdout)
                finally:
                    residue.unlink(missing_ok=True)

    def test_generated_triggers_never_use_inline_arithmetic_rhs(self) -> None:
        # CK3 1.19.0.6 reports this shape as wildcard value plus unknown
        # value/add triggers, so arithmetic must happen in effect statements.
        self.assertIsNone(
            ILLEGAL_TRIGGER_ARITHMETIC_RHS.search(self.effects),
            "CK3 scripted-effect loader treats RHS value arithmetic as triggers",
        )

    def test_every_id_has_consumer_three_routes_and_event(self) -> None:
        for mid in sorted(EXPECTED_IDS):
            with self.subTest(mid=mid):
                self.assertIn(f"zg361_p3_m{mid}_consume_effect = {{", self.effects)
                self.assertIn(f"zg361p3.{mid} = {{", self.events)
                for letter in "abc":
                    self.assertIn(f"zg361_p3_m{mid}_route_{letter}_effect = {{", self.effects)
                    self.assertIn(f"name = zg361p3.{mid}.{letter}", block(self.events, f"zg361p3.{mid}"))

    def test_route_count_is_exact(self) -> None:
        route_defs = re.findall(r"^zg361_p3_m(\d+)_route_([abc])_effect = \{$", self.effects, re.MULTILINE)
        consumer_defs = re.findall(r"^zg361_p3_m(\d+)_consume_effect = \{$", self.effects, re.MULTILINE)
        event_defs = re.findall(r"^zg361p3\.(\d+) = \{$", self.events, re.MULTILINE)
        self.assertEqual(len(route_defs), 105)
        self.assertEqual({int(mid) for mid, _ in route_defs}, EXPECTED_IDS)
        self.assertEqual({int(mid) for mid in consumer_defs}, EXPECTED_IDS)
        self.assertEqual(
            {int(mid) for mid in event_defs},
            EXPECTED_IDS | set(gen.QUEUE_EVENTS.values()) | {gen.PLAYER_MODE_EVENT},
        )

    def test_each_event_has_exactly_three_options(self) -> None:
        for mid in sorted(EXPECTED_IDS):
            with self.subTest(mid=mid):
                event = block(self.events, f"zg361p3.{mid}")
                self.assertEqual(event.count("\n\toption = {"), 3)
                self.assertIn("is_ai = no", event)
                self.assertIn(f"EXPECTED_STATE = {self.specs[mid].state}", event)

    def test_event_root_is_frozen_owner(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                event = block(self.events, f"zg361p3.{spec.mid}")
                self.assertIn(f"this = scope:zg361_p3_{spec.domain}_owner", event)
                for name in ("owner", "subject", "cycle", "case"):
                    self.assertIn(f"exists = scope:zg361_p3_{spec.domain}_{name}", event)

    def test_event_references_are_all_defined(self) -> None:
        referenced = {int(mid) for mid in re.findall(r"trigger_event = \{ id = zg361p3\.(\d+)", self.effects + self.events)}
        defined = {int(mid) for mid in re.findall(r"^zg361p3\.(\d+) = \{$", self.events, re.MULTILINE)}
        self.assertEqual(referenced, defined)

    def test_each_route_uses_full_five_tuple_guard(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "abc":
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                    self.assertIn("zg361_case_kernel_full_guard_trigger", route)
                    for token in ("OWNER_VAR", "SUBJECT_VAR", "CYCLE_VAR", "CASE_VAR", "STATE_VAR", "ACTIVE_VAR"):
                        self.assertIn(token, route)
                    for token in ("EXPECTED_OWNER", "EXPECTED_SUBJECT", "EXPECTED_CYCLE", "EXPECTED_CASE"):
                        self.assertIn(token, route)
                    self.assertIn(f"EXPECTED_STATE = {spec.state}", route)

    def test_cross_route_receipt_is_mutually_exclusive(self) -> None:
        for spec in gen.MECHANISMS:
            names_by_route = []
            for letter in "abc":
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                for choice in (1, 2, 3):
                    self.assertIn(f"EXPECTED_CHOICE = {choice}", route)
                names = tuple(
                    re.search(rf"RECEIPT_{kind}_VAR = (zg361_p3_m{spec.mid}_receipt_[a-z]+)", route).group(1)
                    for kind in ("OWNER", "SUBJECT", "CYCLE", "CASE", "STATE", "CHOICE")
                )
                names_by_route.append(names)
            with self.subTest(mid=spec.mid):
                self.assertEqual(len(set(names_by_route)), 1)

    def test_operation_order_is_atomic(self) -> None:
        for spec in gen.MECHANISMS:
            for letter in "ab":
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                    precheck = route.index(f"var:zg361_p3_{spec.domain}_operation_used <")
                    record = route.index("zg361_case_kernel_record_operation_effect")
                    semantic = route.index(f"name = zg361_p3_{spec.field}")
                    consumer = route.index(f"zg361_p3_m{spec.mid}_consume_effect = yes")
                    self.assertLess(precheck, record)
                    self.assertLess(record, semantic)
                    self.assertLess(semantic, consumer)
                    if spec.mid in gen.STAGE_LAST[spec.domain]:
                        self.assertLess(consumer, route.index(f"zg361_case_{spec.domain}_advance_"))

            with self.subTest(mid=spec.mid, route="c"):
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_c_effect")
                precheck = route.index(f"var:zg361_p3_{spec.domain}_operation_used <")
                record = route.index("zg361_case_kernel_record_operation_effect")
                debt = route.index(f"name = zg361_p3_m{spec.mid}_debt_owner")
                self.assertLess(precheck, record)
                self.assertLess(record, debt)
                self.assertNotIn(f"name = zg361_p3_{spec.field}", route)
                self.assertNotIn(f"zg361_p3_m{spec.mid}_consume_effect = yes", route)
                if spec.mid in gen.STAGE_LAST[spec.domain]:
                    self.assertLess(debt, route.index(f"zg361_case_{spec.domain}_advance_"))

    def test_m229_freezes_explicit_cp_receipt_lineage(self) -> None:
        initializer = block(self.effects, "zg361_p3_initialize_portfolio_effect")
        required = (
            "zg361_cp_m26_receipt_owner",
            "zg361_cp_m26_receipt_subject",
            "zg361_cp_m26_receipt_cycle",
            "zg361_cp_m26_receipt_case",
            "zg361_cp_m26_contribution_receipt_id",
            "zg361_cp_m26_contribution_receipt_revision",
            "zg361_cp_m26_visible_value",
        )
        for key in required:
            self.assertIn(f"has_variable = {key}", initializer)
        self.assertIn("var:zg361_cp_m26_receipt_owner = root", initializer)
        self.assertIn("var:zg361_cp_m26_receipt_subject = this", initializer)
        self.assertIn(
            "var:zg361_cp_m26_receipt_cycle = root.var:zg361_review_serial",
            initializer,
        )
        self.assertIn(
            "name = zg361_p3_project_source_contribution_receipt_id value = var:zg361_cp_m26_contribution_receipt_id",
            initializer,
        )
        self.assertIn(
            "name = zg361_p3_project_source_contribution_receipt_revision value = var:zg361_cp_m26_contribution_receipt_revision",
            initializer,
        )

        for letter in "ab":
            route = block(self.effects, f"zg361_p3_m229_route_{letter}_effect")
            with self.subTest(route=letter):
                self.assertIn("has_variable = zg361_p3_project_source_ready", route)
                self.assertIn("var:zg361_p3_project_source_ready = 1", route)
                self.assertIn(
                    "name = zg361_p3_m229_source_contribution_receipt_id value = var:zg361_p3_project_source_contribution_receipt_id",
                    route,
                )
                self.assertIn(
                    "name = zg361_p3_m229_source_contribution_receipt_revision value = var:zg361_p3_project_source_contribution_receipt_revision",
                    route,
                )
                self.assertIn(
                    "name = zg361_p3_m229_metrics_revision value = var:zg361_case_aa_revision",
                    route,
                )
                self.assertIn(
                    "name = zg361_p3_m229_dictionary_key_code value = var:zg361_p3_metric_dictionary_owner",
                    route,
                )

        route_c = block(self.effects, "zg361_p3_m229_route_c_effect")
        self.assertNotIn("zg361_p3_m229_source_contribution_receipt_id", route_c)
        self.assertNotIn("zg361_p3_m229_metrics_revision", route_c)

    def test_typed_red_idempotent_and_stale_are_explicit(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("abc", 1):
                with self.subTest(mid=spec.mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                    self.assertIn(f"name = zg361_p3_last_red_code value = {spec.mid * 10 + choice}", route)
                    self.assertIn("value = 4 } # typed RED; no receipt/business/resource write", route)
                    self.assertIn("value = 2 } # idempotent no-op", route)
                    self.assertIn("value = 3 } } # stale no-op", route)

    def test_every_write_has_frozen_tuple_and_provenance(self) -> None:
        for spec in gen.MECHANISMS:
            for choice, letter in enumerate("ab", 1):
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    for name in ("owner", "subject", "cycle", "case", "state"):
                        self.assertIn(f"name = zg361_p3_m{spec.mid}_write_{name}", route)
                    self.assertIn(f"name = zg361_p3_m{spec.mid}_provenance_case", route)
                    self.assertIn(f"name = zg361_p3_m{spec.mid}_provenance_choice value = {choice}", route)

    def test_every_route_c_is_pure_defer_and_freezes_one_debt(self) -> None:
        for spec in gen.MECHANISMS:
            route = block(self.effects, f"zg361_p3_m{spec.mid}_route_c_effect")
            prefix = f"zg361_p3_m{spec.mid}_debt_"
            with self.subTest(mid=spec.mid):
                self.assertIn(
                    f"# #{spec.mid:03d} route C: pure defer; no business object or resource write.",
                    self.historical_effects,
                )
                values = {
                    "owner": "$TICKET_OWNER$",
                    "subject": "$TICKET_SUBJECT$",
                    "cycle": "$TICKET_CYCLE$",
                    "case": "$TICKET_CASE$",
                    "state": str(spec.state),
                }
                for name, value in values.items():
                    self.assertEqual(route.count(f"set_variable = {{ name = {prefix}{name} value = {value} }}"), 1)
                self.assertEqual(
                    route.count(
                        f"set_variable = {{ name = {prefix}due_cycle "
                        "value = $TICKET_CYCLE$ }"
                    ),
                    1,
                )
                self.assertEqual(route.count(f"change_variable = {{ name = {prefix}due_cycle add = 1 }}"), 1)
                self.assertEqual(route.count(f"set_variable = {{ name = {prefix}status value = 1 }}"), 1)
                for name, value in {
                    "mechanism": spec.mid,
                    "audit_state": 1,
                    "business_object_created": 0,
                    "performance_sink": 0,
                    "consumer_status": 0,
                }.items():
                    self.assertEqual(
                        route.count(f"set_variable = {{ name = {prefix}{name} value = {value} }}"),
                        1,
                    )
                for name in ("portfolio_deferred", "deferred_cleanup_status"):
                    self.assertEqual(route.count(f"name = zg361_p3_{name} value = 1"), 1)
                self.assertEqual(route.count("name = zg361_p3_policy_debt_open_n add = 1"), 1)
                self.assertIn(f"remove_variable = {prefix}settled_by", route)
                self.assertIn(f"remove_variable = {prefix}settled_cycle", route)
                self.assertIn("CHOICE = 3", route)
                self.assertNotIn(f"name = zg361_p3_{spec.field}", route)
                self.assertNotIn(f"zg361_p3_m{spec.mid}_write_", route)
                self.assertNotIn(f"zg361_p3_m{spec.mid}_provenance_", route)
                self.assertNotIn(f"zg361_p3_m{spec.mid}_consume_effect = yes", route)

                writes = set(re.findall(r"(?:set|change)_variable = \{ name = ([a-z0-9_]+)", route))
                allowed_writes = {
                    "zg361_p3_runtime_applied",
                    "zg361_p3_runtime_status",
                    "zg361_p3_last_red_code",
                    f"zg361_p3_{spec.domain}_operation_used",
                    *(f"{prefix}{name}" for name in (
                        "owner",
                        "subject",
                        "cycle",
                        "case",
                        "state",
                        "mechanism",
                        "due_cycle",
                        "status",
                        "audit_state",
                        "business_object_created",
                        "performance_sink",
                        "consumer_status",
                    )),
                    "zg361_p3_portfolio_deferred",
                    "zg361_p3_deferred_cleanup_status",
                    "zg361_p3_policy_debt_open_n",
                }
                self.assertLessEqual(writes, allowed_writes)
                removed = set(re.findall(r"remove_variable = ([a-z0-9_]+)", route))
                self.assertLessEqual(
                    removed,
                    {
                        "zg361_p3_runtime_applied",
                        "zg361_p3_last_red_code",
                        f"{prefix}settled_by",
                        f"{prefix}settled_cycle",
                    },
                )
                for token in (
                    "zg361_p3_metric_object_",
                    "zg361_p3_reorg_object_",
                    "zg361_p3_demand_object_",
                    "zg361_p3_delivery_object_",
                    "zg361_p3_aa_sample_used",
                    "zg361_p3_ag_hc_",
                    "zg361_p3_ag_management_capacity_",
                    "zg361_p3_aj_capacity_",
                    "zg361_p3_aj_wip_",
                    "zg361_p3_aj_value_credit_",
                ):
                    self.assertNotIn(token, route)

    def test_due_debt_consumers_are_exact_next_cycle_and_fail_closed(self) -> None:
        definitions = re.findall(r"^zg361_p3_m(\d+)_consume_due_debt_effect = \{$", self.effects, re.MULTILINE)
        self.assertEqual(len(definitions), 35)
        self.assertEqual({int(mid) for mid in definitions}, EXPECTED_IDS)
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_p3_m{spec.mid}_consume_due_debt_effect")
            prefix = f"zg361_p3_m{spec.mid}"
            with self.subTest(mid=spec.mid):
                for name in ("owner", "subject", "cycle", "case", "state", "due_cycle", "status"):
                    self.assertIn(f"has_variable = {prefix}_debt_{name}", consumer)
                for name in ("mechanism", "audit_state", "business_object_created"):
                    self.assertIn(f"has_variable = {prefix}_debt_{name}", consumer)
                for name in ("owner", "subject", "cycle", "case", "state", "choice"):
                    self.assertIn(f"has_variable = {prefix}_receipt_{name}", consumer)
                self.assertIn(f"var:{prefix}_debt_status = 1", consumer)
                self.assertIn(f"var:{prefix}_debt_mechanism = {spec.mid}", consumer)
                self.assertIn(f"var:{prefix}_debt_audit_state = 1", consumer)
                self.assertIn(f"var:{prefix}_debt_business_object_created = 0", consumer)
                self.assertIn(f"var:{prefix}_debt_owner = root", consumer)
                self.assertIn(f"var:{prefix}_debt_subject = this", consumer)
                for name in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"var:{prefix}_debt_{name} = var:{prefix}_receipt_{name}", consumer)
                self.assertIn(f"var:{prefix}_receipt_choice = 3", consumer)
                self.assertIn(f"has_variable = {prefix}_debt_expected_due_cycle", consumer)
                self.assertIn(
                    f"name = {prefix}_debt_expected_due_cycle value = var:{prefix}_debt_cycle",
                    consumer,
                )
                self.assertIn(f"name = {prefix}_debt_expected_due_cycle add = 1", consumer)
                self.assertIn(
                    f"var:{prefix}_debt_due_cycle = var:{prefix}_debt_expected_due_cycle",
                    consumer,
                )
                self.assertIn(f"root.var:zg361_review_serial = var:{prefix}_debt_due_cycle", consumer)
                self.assertNotIn(f"var:{prefix}_debt_due_cycle <= root.var:zg361_review_serial", consumer)
                self.assertEqual(consumer.count("change_variable = { name = zg361_b2_management_debt add = 1 }"), 1)
                self.assertIn(f"var:{prefix}_debt_owner = {{", consumer)
                self.assertIn(f"name = {prefix}_debt_status value = 2", consumer)
                self.assertIn(f"name = {prefix}_debt_audit_state value = 3", consumer)
                self.assertIn(f"name = {prefix}_debt_settled_by value = root", consumer)
                self.assertIn(f"name = {prefix}_debt_settled_cycle value = root.var:zg361_review_serial", consumer)
                self.assertIn(f"name = {prefix}_debt_performance_sink value = 1", consumer)
                self.assertIn(f"name = {prefix}_debt_consumer_status value = 1", consumer)
                self.assertEqual(consumer.count("name = zg361_p3_policy_debt_open_n add = -1"), 1)
                self.assertEqual(consumer.count("name = zg361_p3_policy_debt_settled_n add = 1"), 1)
                for forbidden in (
                    "trigger_event",
                    "record_operation",
                    f"zg361_case_{spec.domain}_advance_",
                    f"name = zg361_p3_{spec.field}",
                    f"{prefix}_write_",
                ):
                    self.assertNotIn(forbidden, consumer)

    def test_each_consumer_is_guarded_and_idempotent(self) -> None:
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                consumer = block(self.effects, f"zg361_p3_m{spec.mid}_consume_effect")
                self.assertGreaterEqual(consumer.count("trigger_if = {"), 2)
                for name in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"has_variable = zg361_p3_m{spec.mid}_write_{name}", consumer)
                    self.assertIn(f"has_variable = zg361_p3_m{spec.mid}_consumed_{name}", consumer)
                    self.assertIn(f"name = zg361_p3_m{spec.mid}_consumed_{name}", consumer)
                self.assertIn(f"value = var:zg361_p3_{spec.field}", consumer)
                self.assertIn(f"name = zg361_p3_m{spec.mid}_visible_provenance_case", consumer)

    def test_only_stage_barriers_advance_and_require_complete_stage(self) -> None:
        for spec in gen.MECHANISMS:
            same_stage = [item.mid for item in gen.MECHANISMS if item.domain == spec.domain and item.state == spec.state]
            for letter in "abc":
                route = block(self.effects, f"zg361_p3_m{spec.mid}_route_{letter}_effect")
                with self.subTest(mid=spec.mid, route=letter):
                    if spec.mid in gen.STAGE_LAST[spec.domain]:
                        self.assertEqual(route.count(f"zg361_case_{spec.domain}_advance_{gen.STAGE_LAST[spec.domain][spec.mid]:02d}_effect"), 1)
                        advance_prefix = route[: route.index(f"zg361_case_{spec.domain}_advance_")]
                        for stage_mid in same_stage:
                            self.assertIn(f"zg361_p3_m{stage_mid}_receipt_choice", advance_prefix)
                    else:
                        self.assertNotIn(f"zg361_case_{spec.domain}_advance_", route)

    def test_stage_graphs_have_all_edges_once_per_route(self) -> None:
        for domain, barriers in gen.STAGE_LAST.items():
            for mid, edge in barriers.items():
                with self.subTest(domain=domain, mid=mid):
                    for letter in "abc":
                        route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                        self.assertIn(f"zg361_case_{domain}_advance_{edge:02d}_effect", route)

    def test_launch_freezes_owner_subject_cycle_and_case(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            with self.subTest(domain=domain):
                launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
                self.assertIn(f"zg361_case_{domain}_open_effect = yes", launch)
                self.assertIn(f"var:zg361_case_{domain}_owner = {{ save_scope_as = zg361_p3_{domain}_owner }}", launch)
                self.assertIn(f"save_scope_as = zg361_p3_{domain}_subject", launch)
                self.assertIn(f"name = zg361_p3_{domain}_cycle", launch)
                self.assertIn(f"name = zg361_p3_{domain}_case", launch)

    def test_only_public_entry_is_manager_scope_portfolio_adapter(self) -> None:
        self.assertEqual(len(re.findall(r"^zg361_p3_open_portfolio_effect = \{$", self.effects, re.MULTILINE)), 1)
        adapter = block(self.effects, "zg361_p3_open_portfolio_effect")
        self.assertIn("has_game_rule = zg361_on", adapter)
        self.assertIn("zg361_is_celestial_liege_trigger = yes", adapter)
        self.assertIn("has_variable = zg361_review_serial", adapter)
        self.assertIn("$SUBJECT$ = {", adapter)
        self.assertIn("zg361_is_reviewable_vassal_trigger = yes", adapter)
        self.assertIn("liege = root", adapter)
        self.assertEqual(adapter.count("zg361_p3_consume_due_policy_debts_effect = yes"), 1)
        self.assertEqual(adapter.count("zg361_p3_aa_launch_effect = yes"), 1)
        self.assertLess(
            adapter.index("zg361_p3_consume_due_policy_debts_effect = yes"),
            adapter.index("zg361_p3_aa_launch_effect = yes"),
        )
        self.assertNotIn("zg361_p3_ag_launch_effect", adapter)
        self.assertNotIn("zg361_p3_aj_launch_effect", adapter)
        self.assertNotIn("trigger_event", adapter)

    def test_due_debt_aggregate_has_one_call_per_id_and_one_caller(self) -> None:
        aggregate = block(self.effects, "zg361_p3_consume_due_policy_debts_effect")
        self.assertIn(
            "name = zg361_p3_deferred_cleanup_due_cycle value = var:zg361_p3_portfolio_cycle",
            aggregate,
        )
        self.assertIn("name = zg361_p3_deferred_cleanup_due_cycle add = 1", aggregate)
        cleanup = block(self.effects, "zg361_p3_settle_deferred_portfolio_effect")
        self.assertIn("has_variable = zg361_p3_deferred_cleanup_due_cycle", cleanup)
        self.assertIn(
            "root.var:zg361_review_serial = var:zg361_p3_deferred_cleanup_due_cycle",
            cleanup,
        )
        calls = re.findall(r"zg361_p3_m(\d+)_consume_due_debt_effect = yes", aggregate)
        self.assertEqual([int(mid) for mid in calls], [spec.mid for spec in gen.MECHANISMS])
        self.assertEqual(len(calls), 35)
        self.assertEqual(self.effects.count("zg361_p3_consume_due_policy_debts_effect = yes"), 1)
        for domain in gen.DOMAIN_ORDER:
            self.assertNotIn(
                "zg361_p3_consume_due_policy_debts_effect",
                block(self.effects, f"zg361_p3_{domain}_subject_read_effect"),
            )
            self.assertNotIn(
                "zg361_p3_consume_due_policy_debts_effect",
                block(self.effects, f"zg361_p3_{domain}_run_authorized_ai_effect"),
            )
        initializers = "\n".join(
            [block(self.effects, "zg361_p3_initialize_portfolio_effect")]
            + [block(self.effects, f"zg361_p3_{domain}_initialize_effect") for domain in gen.DOMAIN_ORDER]
        )
        for mid in EXPECTED_IDS:
            self.assertNotIn(f"zg361_p3_m{mid}_debt_", initializers)

    def test_portfolio_adapter_freezes_delivered_case_and_replay_is_noop(self) -> None:
        adapter = block(self.effects, "zg361_p3_open_portfolio_effect")
        initializer = block(self.effects, "zg361_p3_initialize_portfolio_effect")
        for name in ("owner", "cycle", "case", "state"):
            source = {
                "owner": "zg361_result_case_owner",
                "cycle": "zg361_result_cycle_serial",
                "case": "zg361_result_case_serial",
                "state": "zg361_result_case_state",
            }[name]
            self.assertIn(f"has_variable = {source}", adapter)
            self.assertIn(f"name = zg361_p3_portfolio_result_{name} value = var:{source}", initializer)
        self.assertIn("name = zg361_p3_portfolio_result_subject value = this", initializer)
        self.assertIn("var:zg361_result_case_owner = root", adapter)
        self.assertIn("var:zg361_result_cycle_serial = root.var:zg361_review_serial", adapter)
        self.assertIn("var:zg361_result_case_state >= 3", adapter)
        self.assertIn("has_variable = zg361_p3_manager_portfolio_cycle", adapter)
        self.assertIn("NOT = { var:zg361_p3_manager_portfolio_cycle = var:zg361_review_serial }", adapter)
        self.assertIn("has_variable = zg361_p3_portfolio_cycle", adapter)
        self.assertIn("NOT = { var:zg361_p3_portfolio_cycle = root.var:zg361_review_serial }", adapter)
        for domain in gen.DOMAIN_ORDER:
            self.assertIn(f"has_variable = zg361_case_{domain}_active", adapter)
            self.assertIn(f"var:zg361_case_{domain}_active = 0", adapter)

    def test_portfolio_subject_has_a_reachable_persistent_producer(self) -> None:
        initializer = block(self.effects, "zg361_p3_initialize_portfolio_effect")
        aa_launch = block(self.effects, "zg361_p3_aa_launch_effect")
        self.assertEqual(
            initializer.count("set_variable = { name = zg361_p3_portfolio_subject value = this }"),
            1,
        )
        self.assertIn("save_temporary_scope_as = zg361_p3_portfolio_subject_scope", initializer)
        self.assertNotIn("save_scope_as = zg361_p3_portfolio_subject\n", initializer)
        self.assertNotIn("scope:zg361_p3_portfolio_subject =", initializer)
        self.assertIn("scope:zg361_p3_portfolio_subject_scope =", initializer)
        self.assertIn("zg361_p3_initialize_portfolio_effect = yes", aa_launch)
        for event_id in (gen.QUEUE_EVENTS["aa"], gen.QUEUE_EVENTS["ag"]):
            queued = block(self.events, f"zg361p3.{event_id}")
            self.assertIn("has_variable = zg361_p3_portfolio_subject", queued)
            self.assertIn("var:zg361_p3_portfolio_subject = scope:", queued)

    def test_only_aa_launch_initializes_portfolio_after_successful_open(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
            with self.subTest(domain=domain):
                if domain == "aa":
                    self.assertEqual(launch.count("zg361_p3_initialize_portfolio_effect = yes"), 1)
                    self.assertLess(launch.index("var:zg361_case_kernel_applied = 1"), launch.index("zg361_p3_initialize_portfolio_effect = yes"))
                else:
                    self.assertNotIn("zg361_p3_initialize_portfolio_effect", launch)

    def test_player_visible_chain_is_d_plus_one_after_first_card(self) -> None:
        for domain, order in gen.DOMAIN_ORDER.items():
            for index, mid in enumerate(order):
                event = block(self.events, f"zg361p3.{mid}")
                with self.subTest(domain=domain, mid=mid):
                    if index + 1 < len(order):
                        next_mid = order[index + 1]
                        edge = f"trigger_event = {{ id = zg361p3.{next_mid} days = 1 }}"
                        self.assertEqual(event.count(edge), 3)
                        self.assertNotIn(f"trigger_event = {{ id = zg361p3.{next_mid} }}", event)
                    else:
                        retry_ids = {
                            int(event_id)
                            for event_id in re.findall(
                                r"trigger_event = \{ id = zg361p3\.(\d+) days = 1 \}",
                                event,
                            )
                        }
                        self.assertEqual(retry_ids, {mid})

    def test_closed_domain_queues_next_domain_and_aj_finalizes(self) -> None:
        final_by_domain = {domain: order[-1] for domain, order in gen.DOMAIN_ORDER.items()}
        for domain, queue_id in gen.QUEUE_EVENTS.items():
            final_mid = final_by_domain[domain]
            for letter in "abc":
                route = block(self.effects, f"zg361_p3_m{final_mid}_route_{letter}_effect")
                with self.subTest(domain=domain, route=letter):
                    self.assertEqual(route.count(f"trigger_event = {{ id = zg361p3.{queue_id} days = 1 }}"), 1)
                    self.assertNotIn(f"zg361_p3_{gen.NEXT_DOMAIN[domain]}_launch_effect", route)
        for letter in "abc":
            final = block(self.effects, f"zg361_p3_m{final_by_domain['aj']}_route_{letter}_effect")
            self.assertEqual(final.count("zg361_p3_finalize_portfolio_effect = yes"), 1)
            self.assertNotIn("trigger_event", final)

    def test_hidden_queue_revalidates_closed_case_and_frozen_portfolio(self) -> None:
        final_states = {domain: max(gen.STAGE_LAST[domain].values()) + 1 for domain in gen.QUEUE_EVENTS}
        for domain, queue_id in gen.QUEUE_EVENTS.items():
            queued = block(self.events, f"zg361p3.{queue_id}")
            next_domain = gen.NEXT_DOMAIN[domain]
            opened_domain = ("aa", "ag", "aj").index(next_domain) + 1
            with self.subTest(domain=domain):
                self.assertIn("hidden = yes", queued)
                self.assertNotIn("\ttitle =", queued)
                self.assertNotIn("\tdesc =", queued)
                self.assertNotIn("\toption =", queued)
                self.assertIn("zg361_is_celestial_liege_trigger = yes", queued)
                self.assertIn("var:zg361_p3_manager_portfolio_cycle = var:zg361_review_serial", queued)
                for name in ("owner", "subject", "cycle", "case"):
                    self.assertIn(f"exists = scope:zg361_p3_{domain}_{name}", queued)
                self.assertIn(f"var:zg361_case_{domain}_state = {final_states[domain]}", queued)
                self.assertIn(f"var:zg361_case_{domain}_active = 0", queued)
                for name in ("owner", "subject", "cycle", "case", "state"):
                    self.assertIn(f"has_variable = zg361_p3_portfolio_result_{name}", queued)
                for source in ("zg361_result_case_owner", "zg361_result_cycle_serial", "zg361_result_case_serial", "zg361_result_case_state"):
                    self.assertIn(f"has_variable = {source}", queued)
                self.assertIn("var:zg361_p3_portfolio_closed = 0", queued)
                self.assertIn(f"var:zg361_p3_portfolio_opened_domain = {opened_domain - 1}", queued)
                self.assertIn(f"name = zg361_p3_portfolio_opened_domain value = {opened_domain}", queued)
                self.assertEqual(queued.count(f"zg361_p3_{next_domain}_launch_effect = yes"), 1)

    def test_same_day_visible_entrypoints_are_bounded(self) -> None:
        direct = re.findall(r"trigger_event = \{ id = zg361p3\.(\d+) \}", self.effects + self.events)
        self.assertEqual(
            {int(mid) for mid in direct},
            {gen.PLAYER_MODE_EVENT, gen.DOMAIN_ORDER["ag"][0], gen.DOMAIN_ORDER["aj"][0]},
        )
        for domain, order in gen.DOMAIN_ORDER.items():
            launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
            expected = gen.PLAYER_MODE_EVENT if domain == "aa" else order[0]
            self.assertEqual(launch.count(f"trigger_event = {{ id = zg361p3.{expected} }}"), 1)
        adapter = block(self.effects, "zg361_p3_open_portfolio_effect")
        self.assertEqual(adapter.count("zg361_p3_aa_launch_effect = yes"), 1)
        self.assertNotIn("zg361_p3_ag_launch_effect", adapter)
        self.assertNotIn("zg361_p3_aj_launch_effect", adapter)

    def test_player_popup_split_is_frozen_at_twenty_two_background_thirteen_visible(self) -> None:
        self.assertEqual(
            gen.PLAYER_BACKGROUND_IDS,
            {
                230, 231, 232, 233, 234, 235, 236, 237, 238, 239,
                301, 302, 303, 304, 305, 306, 307, 308,
                334, 336, 339, 342,
            },
        )
        self.assertEqual(
            gen.PLAYER_VISIBLE_IDS,
            {
                229, 240, 241,
                309, 310, 311,
                335, 337, 338, 340, 341, 343, 344,
            },
        )
        # Batch A/B/C: one mode selector plus thirteen required rulings.
        self.assertEqual(1 + len(gen.PLAYER_VISIBLE_IDS), 14)
        # Mode D preserves all thirty-five original business cards, plus the
        # one explicit selector through which the player requests that path.
        self.assertEqual(1 + len(EXPECTED_IDS), 36)
        for domain, order in gen.DOMAIN_ORDER.items():
            self.assertIn(order[-1], gen.PLAYER_VISIBLE_IDS, domain)

    def test_player_mode_event_is_guarded_and_buttons_state_complete_actions(self) -> None:
        event = block(self.events, f"zg361p3.{gen.PLAYER_MODE_EVENT}")
        self.assertEqual(event.count("\n\toption = {"), 4)
        self.assertIn("is_ai = no", event)
        self.assertIn("zg361_case_kernel_full_guard_trigger", event)
        self.assertIn("EXPECTED_STATE = 1", event)
        self.assertNotRegex(event, r"zg361_p3_m\d+_route_[abc]_effect")
        for mode, letter in enumerate("abcd", 1):
            self.assertIn(f"name = zg361p3.{gen.PLAYER_MODE_EVENT}.{letter}", event)
            self.assertIn(f"name = zg361_p3_player_batch_mode value = {mode}", event)
        self.assertEqual(event.count("zg361_p3_aa_continue_player_effect = yes"), 4)

        chinese = loc_rows(
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_phase3_metrics_delivery_l_simp_chinese.yml"
        )
        self.assertEqual(chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.t"], "本轮办案方式")
        self.assertIn("二十二项", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.desc"])
        self.assertIn("十三项", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.desc"])
        self.assertIn("正式案卷、期限与回执", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.desc"])
        self.assertIn("证据完整、可复核", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.a"])
        self.assertIn("以迅速交付为先", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.b"])
        self.assertIn("每件各记一笔下周期制度债", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.c"])
        self.assertIn("全部三十五项逐案呈报", chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.d"])
        mode_copy = "\n".join(
            chinese[f"zg361p3.{gen.PLAYER_MODE_EVENT}.{key}"]
            for key in ("t", "desc", "a", "b", "c", "d")
        )
        for forbidden in (
            "后台", "首要处置", "备选处置", "失败项", "原案", "原始案卷", "弹窗", "批处理",
        ):
            self.assertNotIn(forbidden, mode_copy)
        english = loc_rows(
            MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml"
        )
        english_mode_copy = "\n".join(
            english[f"zg361p3.{gen.PLAYER_MODE_EVENT}.{key}"]
            for key in ("t", "desc", "a", "b", "c", "d")
        ).lower()
        for forbidden in ("background", "original card", "failed item", "batch"):
            self.assertNotIn(forbidden, english_mode_copy)

    def test_batch_dispatch_calls_original_cores_and_falls_back_to_exact_card(self) -> None:
        for domain, order in gen.DOMAIN_ORDER.items():
            dispatch = block(self.effects, f"zg361_p3_{domain}_continue_player_effect")
            domain_background = [mid for mid in order if mid in gen.PLAYER_BACKGROUND_IDS]
            domain_visible = [mid for mid in order if mid in gen.PLAYER_VISIBLE_IDS]
            with self.subTest(domain=domain):
                self.assertNotIn("record_operation", dispatch)
                self.assertNotIn("_advance_", dispatch)
                for mid in domain_background:
                    for letter, mode in zip("abc", (1, 2, 3)):
                        self.assertEqual(
                            dispatch.count(f"zg361_p3_m{mid}_route_{letter}_effect = {{"),
                            1,
                        )
                        self.assertIn(f"var:zg361_p3_player_batch_mode = {mode}", dispatch)
                    self.assertGreaterEqual(
                        dispatch.count(f"trigger_event = {{ id = zg361p3.{mid} days = 1 }}"),
                        2,
                    )
                    self.assertIn(
                        f"name = zg361_p3_player_batch_fallback_mid value = {mid}",
                        dispatch,
                    )
                for mid in domain_visible:
                    self.assertNotRegex(dispatch, rf"zg361_p3_m{mid}_route_[abc]_effect")
                    self.assertEqual(
                        dispatch.count(f"trigger_event = {{ id = zg361p3.{mid} days = 1 }}"),
                        1,
                    )
                self.assertEqual(
                    len(re.findall(
                        r"NOT = \{\s+AND = \{\s+has_variable = zg361_p3_runtime_applied",
                        dispatch,
                    )),
                    len(domain_background),
                )

    def test_batch_mode_c_and_manual_c_share_visible_policy_debt_counter(self) -> None:
        dispatches = "\n".join(
            block(self.effects, f"zg361_p3_{domain}_continue_player_effect")
            for domain in gen.DOMAIN_ORDER
        )
        self.assertEqual(
            dispatches.count(
                "change_variable = { name = zg361_p3_player_policy_debt_disclosed_n add = 1 }"
            ),
            len(gen.PLAYER_BACKGROUND_IDS),
        )
        for mid in EXPECTED_IDS:
            event = block(self.events, f"zg361p3.{mid}")
            self.assertEqual(
                event.count(
                    "change_variable = { name = zg361_p3_player_policy_debt_disclosed_n add = 1 }"
                ),
                1,
            )
        initializer = block(self.effects, "zg361_p3_initialize_portfolio_effect")
        self.assertIn(
            "name = zg361_p3_player_policy_debt_disclosed_n value = 0",
            initializer,
        )
        chinese = loc_rows(
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_phase3_metrics_delivery_l_simp_chinese.yml"
        )
        for mid in gen.PLAYER_VISIBLE_IDS:
            self.assertIn(
                "zg361_p3_player_policy_debt_disclosed_n",
                chinese[f"zg361p3.{mid}.desc"],
            )

    def test_batch_continuation_and_mode_d_original_chain_coexist(self) -> None:
        for domain, order in gen.DOMAIN_ORDER.items():
            launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
            if domain == "aa":
                self.assertIn(f"id = zg361p3.{gen.PLAYER_MODE_EVENT}", launch)
            else:
                self.assertIn("var:zg361_p3_player_batch_mode < 4", launch)
                self.assertIn(f"zg361_p3_{domain}_continue_player_effect = yes", launch)
                self.assertIn(f"id = zg361p3.{order[0]}", launch)

            for index, mid in enumerate(order[:-1]):
                next_mid = order[index + 1]
                event = block(self.events, f"zg361p3.{mid}")
                with self.subTest(domain=domain, mid=mid):
                    self.assertEqual(
                        event.count(f"zg361_p3_{domain}_continue_player_effect = yes"),
                        3,
                    )
                    self.assertEqual(
                        event.count(f"trigger_event = {{ id = zg361p3.{next_mid} days = 1 }}"),
                        3,
                    )
                    self.assertEqual(event.count("var:zg361_p3_player_batch_mode < 4"), 3)

    def test_every_manual_route_failure_returns_to_the_exact_original_event(self) -> None:
        for mid in EXPECTED_IDS:
            event = block(self.events, f"zg361p3.{mid}")
            with self.subTest(mid=mid):
                self.assertEqual(
                    event.count(f"trigger_event = {{ id = zg361p3.{mid} days = 1 }}"),
                    3,
                )
                self.assertEqual(
                    event.count(f"name = zg361_p3_player_batch_fallback_mid value = {mid}"),
                    3,
                )

    def test_ai_portfolio_stays_background_only(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            ai = block(self.effects, f"zg361_p3_{domain}_run_authorized_ai_effect")
            self.assertNotIn("trigger_event", ai)
        for queue_id in gen.QUEUE_EVENTS.values():
            queued = block(self.events, f"zg361p3.{queue_id}")
            self.assertIn("hidden = yes", queued)
            self.assertNotIn("is_ai = no", queued)

    def test_player_and_authorized_ai_paths_are_separate(self) -> None:
        for domain in gen.DOMAIN_ORDER:
            launch = block(self.effects, f"zg361_p3_{domain}_launch_effect")
            ai = block(self.effects, f"zg361_p3_{domain}_run_authorized_ai_effect")
            with self.subTest(domain=domain):
                self.assertIn("is_ai = no zg361_is_celestial_liege_trigger = yes", launch)
                self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", launch)
                self.assertIn("is_ai = yes zg361_is_celestial_liege_trigger = yes", ai)
                self.assertNotIn("trigger_event", ai)
                for mid in gen.DOMAIN_ORDER[domain]:
                    self.assertEqual(ai.count(f"zg361_p3_m{mid}_route_a_effect"), 1)
                    self.assertEqual(ai.count(f"zg361_p3_m{mid}_route_c_effect"), 1)
                    for letter in "ab":
                        route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                        self.assertIn("var:zg361_p3_portfolio_deferred = 0", route)
                    route_c = block(self.effects, f"zg361_p3_m{mid}_route_c_effect")
                    self.assertIn("name = zg361_p3_portfolio_deferred value = 1", route_c)
                self.assertIn("has_variable = zg361_p3_portfolio_deferred", ai)
                self.assertIn("var:zg361_p3_portfolio_deferred = 1", ai)

    def test_counts_and_barons_have_assessed_only_adapter(self) -> None:
        forbidden = ("_open_effect", "record_operation", "_advance_", "reserve", "PIP", "hc_slot", "calibrat")
        for domain in gen.DOMAIN_ORDER:
            with self.subTest(domain=domain):
                subject_read = block(self.effects, f"zg361_p3_{domain}_subject_read_effect")
                self.assertIn("zg361_case_kernel_subject_self_guard_trigger", subject_read)
                for token in forbidden:
                    self.assertNotIn(token, subject_read)

    def test_domain_operation_capacity_is_conserved(self) -> None:
        for domain, order in gen.DOMAIN_ORDER.items():
            init = block(self.effects, f"zg361_p3_{domain}_initialize_effect")
            with self.subTest(domain=domain):
                self.assertIn(f"name = zg361_p3_{domain}_operation_total value = {len(order)}", init)
                self.assertIn(f"name = zg361_p3_{domain}_operation_used value = 0", init)
                for mid in order:
                    for letter in "abc":
                        route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                        self.assertIn(f"change_variable = {{ name = zg361_p3_{domain}_operation_used add = 1 }}", route)

    def test_aa_sample_slot_precheck_precedes_record(self) -> None:
        for letter in "ab":
            route = block(self.effects, f"zg361_p3_m240_route_{letter}_effect")
            self.assertLess(route.index("var:zg361_p3_aa_sample_used <"), route.index("record_operation"))
            self.assertIn("zg361_p3_aa_sample_used add = 1", route)
        route_c = block(self.effects, "zg361_p3_m240_route_c_effect")
        self.assertNotIn("zg361_p3_aa_sample_used add = 1", route_c)
        self.assertNotIn("zg361_p3_aa_sample_queue", route_c)

    def test_basis_point_splits_are_conserved(self) -> None:
        for mid in (234, 235, 238, 241, 342, 344):
            for letter in "ab":
                with self.subTest(mid=mid, route=letter):
                    route = block(self.effects, f"zg361_p3_m{mid}_route_{letter}_effect")
                    self.assertRegex(route, rf"m{mid}_(?:share_total|blocker_total) value = 10000")
            self.assertNotRegex(
                block(self.effects, f"zg361_p3_m{mid}_route_c_effect"),
                rf"m{mid}_(?:share_total|blocker_total)",
            )

    def test_ag_matrix_weights_and_hc_are_conserved(self) -> None:
        for letter in "ab":
            dual = block(self.effects, f"zg361_p3_m304_route_{letter}_effect")
            hats = block(self.effects, f"zg361_p3_m306_route_{letter}_effect")
            hc = block(self.effects, f"zg361_p3_m308_route_{letter}_effect")
            self.assertIn("m304_parent_weight_total value = 10000", dual)
            self.assertIn("m304_goal_share_total value = 10000", dual)
            self.assertIn("m304_directive_issued value = 1", dual)
            self.assertIn("m306_weight_total value = 100", hats)
            self.assertIn("zg361_p3_ag_hc_total value = 100", hc)
        for mid, token in ((304, "m304_parent_weight_total"), (306, "m306_weight_total"), (308, "zg361_p3_ag_hc_total")):
            self.assertNotIn(token, block(self.effects, f"zg361_p3_m{mid}_route_c_effect"))

    def test_ag_visibility_consumes_only_management_capacity(self) -> None:
        for letter in "ab":
            route = block(self.effects, f"zg361_p3_m309_route_{letter}_effect")
            self.assertLess(route.index("management_capacity_remaining >= 10"), route.index("record_operation"))
            self.assertIn("management_capacity_remaining subtract = 10", route)
            self.assertIn("visibility_gain value = 10", route)
        route_c = block(self.effects, "zg361_p3_m309_route_c_effect")
        self.assertNotIn("visibility_debt", route_c)
        self.assertNotIn("management_capacity", route_c)
        self.assertNotIn("visibility_gain", route_c)

    def test_reorg_history_owner_does_not_drift(self) -> None:
        for letter in "ab":
            route = block(self.effects, f"zg361_p3_m310_route_{letter}_effect")
            self.assertIn("m310_historical_owner value = var:zg361_p3_portfolio_result_owner", route)
            self.assertIn("m310_mapped_owner value = var:zg361_p3_reorg_object_owner", route)
            self.assertIn("m310_bridge_owner_count value = 2", route)
            self.assertIn("m310_bridge_record_issued value = 1", route)
            self.assertNotIn("m310_historical_owner value = $TICKET_OWNER$", route)
        route_c = block(self.effects, "zg361_p3_m310_route_c_effect")
        self.assertNotIn("m310_historical_owner", route_c)
        self.assertNotIn("m310_mapped_owner", route_c)
        self.assertNotIn("reorg_object_version", route_c)
        self.assertIn("m311_old_target_locked value = 1", block(self.effects, "zg361_p3_m311_route_a_effect"))

    def test_aj_emergency_and_change_tax_prechecks_are_atomic(self) -> None:
        emergency = block(self.effects, "zg361_p3_m335_route_a_effect")
        self.assertLess(emergency.index("emergency_used <"), emergency.index("record_operation"))
        self.assertIn("emergency_used add = 1", emergency)
        for letter in "ab":
            change = block(self.effects, f"zg361_p3_m337_route_{letter}_effect")
            self.assertLess(change.index("capacity_remaining >= 10"), change.index("record_operation"))
            self.assertIn("capacity_remaining subtract = 10", change)
        waiver = block(self.effects, "zg361_p3_m337_route_c_effect")
        self.assertNotIn("disaster_waiver", waiver)
        self.assertNotIn("capacity_remaining", waiver)
        self.assertNotIn("zg361_p3_aj_policy_debt", waiver)
        self.assertNotIn("zg361_p3_m337_policy_debt", waiver)

    def test_aj_wip_and_capacity_conserve(self) -> None:
        normal = block(self.effects, "zg361_p3_m340_route_a_effect")
        self.assertLess(normal.index("wip_used < var:zg361_p3_aj_wip_limit"), normal.index("record_operation"))
        for letter, slots, capacity_source in (
            ("a", 1, "demand_estimated_hours"),
            ("b", 2, "demand_estimated_plus_exception"),
        ):
            route = block(self.effects, f"zg361_p3_m340_route_{letter}_effect")
            self.assertLess(route.index(f"capacity_remaining >= var:zg361_p3_{capacity_source}"), route.index("record_operation"))
            self.assertIn("capacity_remaining subtract = var:zg361_p3_demand_reserved_hours", route)
            self.assertIn("capacity_reserved add = var:zg361_p3_demand_reserved_hours", route)
            self.assertIn(f"wip_used add = {slots}", route)
            self.assertIn(f"delivery_wip_slots value = {slots}", route)
        self.assertIn("exception_signed value = 1", block(self.effects, "zg361_p3_m340_route_b_effect"))
        route_c = block(self.effects, "zg361_p3_m340_route_c_effect")
        for token in ("capacity_remaining", "capacity_reserved", "wip_used", "delivery_wip_slots", "hidden_wip_debt"):
            self.assertNotIn(token, route_c)

    def test_aj_carryover_is_net_zero_current_and_charges_next(self) -> None:
        expected = {"a": 10, "b": 5}
        for letter, carry_hours in expected.items():
            route = block(self.effects, f"zg361_p3_m341_route_{letter}_effect")
            with self.subTest(route=letter):
                self.assertLess(route.index("capacity_reserved >= var:zg361_p3_demand_reserved_hours"), route.index("record_operation"))
                self.assertIn("capacity_reserved subtract = var:zg361_p3_demand_reserved_hours", route)
                self.assertIn("capacity_remaining add = var:zg361_p3_demand_reserved_hours", route)
                self.assertIn(f"m341_transfer_hours value = {carry_hours}", route)
                if carry_hours:
                    self.assertIn(f"next_capacity_remaining subtract = {carry_hours}", route)
                    self.assertIn(f"next_capacity_reserved add = {carry_hours}", route)
                else:
                    self.assertNotIn("next_capacity_remaining subtract", route)
                    self.assertNotIn("next_capacity_reserved add", route)
        route_c = block(self.effects, "zg361_p3_m341_route_c_effect")
        for token in ("capacity_reserved", "capacity_remaining", "m341_transfer_hours", "next_capacity"):
            self.assertNotIn(token, route_c)

    def test_aj_signatures_and_value_credit(self) -> None:
        for letter in "ab":
            triangle = block(self.effects, f"zg361_p3_m338_route_{letter}_effect")
            accept = block(self.effects, f"zg361_p3_m343_route_{letter}_effect")
            value = block(self.effects, f"zg361_p3_m344_route_{letter}_effect")
            self.assertIn("m338_tradeoff_signed value = 1", triangle)
            for party in ("proposer", "executor", "acceptor"):
                self.assertIn(f"m343_{party}_served value = 1", accept)
            self.assertIn("m343_service_count value = 3", accept)
            self.assertLess(value.index("value_credit_remaining = 10000"), value.index("record_operation"))
            self.assertIn("m344_share_total value = 10000", value)
            self.assertIn("value_credit_remaining value = 0", value)
        for mid, tokens in (
            (338, ("m338_tradeoff_signed",)),
            (343, ("m343_proposer_served", "m343_executor_served", "m343_acceptor_served")),
            (344, ("value_credit_remaining", "m344_share_total")),
        ):
            route_c = block(self.effects, f"zg361_p3_m{mid}_route_c_effect")
            for token in tokens:
                self.assertNotIn(token, route_c)

    def test_stable_metric_reorg_demand_and_delivery_objects_are_not_receipts(self) -> None:
        creators = {
            229: ("metric", "zg361_p3_metric_object"),
            301: ("reorg", "zg361_p3_reorg_object"),
            334: ("demand", "zg361_p3_demand_object"),
            340: ("delivery", "zg361_p3_delivery_object"),
        }
        for mid, (name, prefix) in creators.items():
            route = block(self.effects, f"zg361_p3_m{mid}_route_a_effect")
            with self.subTest(object=name):
                for suffix in ("owner", "subject", "cycle", "case", "version"):
                    self.assertIn(f"name = {prefix}_{suffix}", route)
                self.assertNotIn(f"{prefix}_receipt", route)
        for mid in (342, 337, 341, 343, 344):
            route = block(self.effects, f"zg361_p3_m{mid}_route_a_effect")
            self.assertLess(route.index("delivery_object_case = $TICKET_CASE$"), route.index("record_operation"))
            self.assertIn("delivery_demand_case = var:zg361_p3_demand_object_case", route)

    def test_every_consumer_projects_concrete_business_fields(self) -> None:
        self.assertEqual(set(gen.CONSUMER_SOURCES), EXPECTED_IDS)
        for spec in gen.MECHANISMS:
            consumer = block(self.effects, f"zg361_p3_m{spec.mid}_consume_effect")
            with self.subTest(mid=spec.mid):
                self.assertGreaterEqual(len(gen.CONSUMER_SOURCES[spec.mid]), 4)
                for source in gen.consumer_fields(spec):
                    visible = source.removeprefix("zg361_p3_")
                    self.assertIn(f"has_variable = {source}", consumer)
                    self.assertIn(f"visible_{visible} value = var:{source}", consumer)

    def test_route_c_delivery_can_finalize_without_minting_value(self) -> None:
        deferred = block(self.effects, "zg361_p3_m344_route_c_effect")
        for token in (
            "demand_acceptance_outcome",
            "m344_unallocated_share",
            "m344_ledger_total",
            "m344_share_total",
            "m344_launch_order",
            "m344_adoption_order",
            "m344_value_order",
        ):
            self.assertNotIn(token, deferred)
        finalizer = block(self.effects, "zg361_p3_finalize_portfolio_effect")
        self.assertIn("has_variable = zg361_p3_m344_receipt_choice", finalizer)
        choice_c = finalizer.index("var:zg361_p3_m344_receipt_choice = 3")
        ledger_exists = finalizer.index("has_variable = zg361_p3_m344_ledger_total")
        ledger_value = finalizer.index("var:zg361_p3_m344_ledger_total = 10000")
        self.assertLess(choice_c, ledger_exists)
        self.assertLess(ledger_exists, ledger_value)

    def test_localization_has_nine_language_key_parity(self) -> None:
        rows = {
            language: loc_rows(MOD_ROOT / "localization" / language / f"zg361_phase3_metrics_delivery_l_{language}.yml")
            for language in gen.LANGUAGES
        }
        expected_keys = {
            key
            for mid in EXPECTED_IDS
            for key in (
                f"zg361p3.{mid}.t",
                f"zg361p3.{mid}.desc",
                f"zg361p3.{mid}.a",
                f"zg361p3.{mid}.b",
                f"zg361p3.{mid}.c",
                f"zg361p3.{mid}.c.tt",
            )
        }
        expected_keys.update(
            f"zg361p3.{gen.PLAYER_MODE_EVENT}.{key}"
            for key in ("t", "desc", "a", "b", "c", "d")
        )
        for language, mapping in rows.items():
            with self.subTest(language=language):
                self.assertEqual(set(mapping), expected_keys)
        self.assertNotEqual(rows["simp_chinese"], rows["english"])
        for mid in EXPECTED_IDS:
            with self.subTest(mid=mid, route="c"):
                event = block(read(EVENTS_PATH), f"zg361p3.{mid}")
                self.assertIn(f"custom_tooltip = zg361p3.{mid}.c.tt", event)
                self.assertEqual(rows["english"][f"zg361p3.{mid}.c"], gen.DEFER_ROUTE_EN)
                self.assertEqual(rows["simp_chinese"][f"zg361p3.{mid}.c"], gen.DEFER_ROUTE_CN)
                self.assertEqual(rows["english"][f"zg361p3.{mid}.c.tt"], gen.DEFER_TOOLTIP_EN)
                self.assertEqual(rows["simp_chinese"][f"zg361p3.{mid}.c.tt"], gen.DEFER_TOOLTIP_CN)

    def test_character_root_numeric_localization_uses_direct_variable_path(self) -> None:
        expected = "[ROOT.Var('zg361_p3_player_policy_debt_disclosed_n').GetValue|0]"
        forbidden = re.compile(r"ROOT(?:\.Char)?\.MakeScope\.Var\(")
        for language in gen.LANGUAGES:
            path = (
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_phase3_metrics_delivery_l_{language}.yml"
            )
            text = read(path)
            with self.subTest(language=language):
                self.assertIsNone(forbidden.search(text))
                self.assertEqual(text.count(expected), 14)

    def test_saved_scope_character_localization_uses_direct_scope_name(self) -> None:
        expected = "[zg361_p3_aa_subject.GetShortUIName]"
        forbidden = re.compile(r"\[scope:[A-Za-z0-9_]+\.GetShortUIName\]")
        for language in gen.LANGUAGES:
            path = (
                MOD_ROOT
                / "localization"
                / language
                / f"zg361_phase3_metrics_delivery_l_{language}.yml"
            )
            text = read(path)
            with self.subTest(language=language):
                self.assertIsNone(forbidden.search(text))
                self.assertEqual(text.count(expected), 1)

    def test_player_copy_separates_case_context_from_decision_buttons(self) -> None:
        chinese = loc_rows(
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_phase3_metrics_delivery_l_simp_chinese.yml"
        )
        english = loc_rows(
            MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml"
        )
        banned_cn = ("路线甲", "路线乙", "路线丙", "本卡承接", "按钮写明", "按A", "按B", "按C")
        banned_en = ("Routes A", "route C", "This card follows", "records its choice immediately")
        weak_options_cn = ("双方各半", "两边各半", "退回补全", "按此办理", "照此办理")
        descriptions_cn: set[str] = set()
        for spec in gen.MECHANISMS:
            with self.subTest(mid=spec.mid):
                desc_cn = chinese[f"zg361p3.{spec.mid}.desc"]
                desc_en = english[f"zg361p3.{spec.mid}.desc"]
                self.assertNotIn(desc_cn[0], "。！？，、；：.!?;:[$@")
                self.assertNotIn("是本案当事人", desc_cn)
                self.assertNotIn("将作裁决", desc_cn)
                descriptions_cn.add(desc_cn)
                self.assertTrue(desc_en.startswith(spec.desc_en))
                self.assertNotIn(gen.DEFER_ROUTE_CN, desc_cn)
                self.assertNotIn(gen.DEFER_ROUTE_EN, desc_en)
                for token in banned_cn:
                    self.assertNotIn(token, desc_cn)
                for token in banned_en:
                    self.assertNotIn(token, desc_en)
                for route in spec.routes_cn[:2]:
                    self.assertNotIn(route, desc_cn)
                    for weak in weak_options_cn:
                        self.assertNotIn(weak, route)
                for route in spec.routes_en[:2]:
                    self.assertNotIn(route, desc_en)
        self.assertEqual(len(descriptions_cn), len(gen.MECHANISMS))

    def test_reorg_and_admission_copy_uses_world_facing_terms(self) -> None:
        chinese = loc_rows(
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_phase3_metrics_delivery_l_simp_chinese.yml"
        )
        english = loc_rows(
            MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml"
        )
        self.assertEqual(chinese["zg361p3.336.t"], "开工条件尚未齐备")
        self.assertEqual(english["zg361p3.336.t"], "Ready to Begin?")
        self.assertIn("既有案卷的署名责任仍由原任承担", chinese["zg361p3.310.desc"])
        self.assertIn("原责任人与接任者", chinese["zg361p3.310.desc"])
        self.assertEqual(
            chinese["zg361p3.310.a"], "在旧案补记接任者，原责任仍归原任。"
        )
        self.assertNotIn(
            chinese["zg361p3.310.a"].rstrip("。"), chinese["zg361p3.310.desc"]
        )
        self.assertIn(
            "authorship of each existing case remains attached to its original author",
            english["zg361p3.310.desc"],
        )
        self.assertEqual(
            english["zg361p3.310.a"],
            "Add the successor to the old case without changing its original owner.",
        )
        self.assertIn("另立交接记录", chinese["zg361p3.310.b"])
        self.assertIn("核清新旧目标的贡献", chinese["zg361p3.311.b"])
        for key in ("zg361p3.310.desc", "zg361p3.310.b", "zg361p3.311.b"):
            for forbidden in ("映射", "桥接"):
                self.assertNotIn(forbidden, chinese[key])

    def test_resource_and_attribution_buttons_name_action_and_major_consequence(self) -> None:
        chinese = loc_rows(
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_phase3_metrics_delivery_l_simp_chinese.yml"
        )
        expected_tokens = {
            (229, "a"): ("唯一口径责任人", "共同维护"),
            (229, "b"): ("直属上司为口径责任人", "数据管家共同维护", "一笔口径债"),
            (232, "a"): ("全部十个缺失单元", "独立复核人批准"),
            (232, "b"): ("其中八个缺失单元", "误差带", "独立复核人批准"),
            (234, "a"): ("领先信号六成", "滞后结果四成"),
            (234, "b"): ("各五成", "进入校准"),
            (235, "a"): ("各五成", "不得获最高功劳"),
            (235, "b"): ("主指标六成", "质量护栏四成", "承担护栏失守"),
            (236, "a"): ("连续计分", "避免阈值附近", "骤然归零"),
            (236, "b"): ("保留达标阈值", "按接近程度", "部分得分"),
            (237, "a"): ("三百六十五日", "完整时间窗"),
            (237, "b"): ("三百六十五日完整窗", "九十日精选窗"),
            (238, "a"): ("声量一成", "已验证价值七成", "追回一成功劳"),
            (238, "b"): ("声量三成", "已验证价值五成", "追回三成功劳"),
            (239, "a"): ("学习证据七成功劳", "业务交付仍记失败"),
            (239, "b"): ("学习证据四成功劳", "业务交付分账"),
            (240, "a"): ("这批样本", "独占分配", "当前实验"),
            (240, "b"): ("独立复核人签字", "样本划分给两项实验"),
            (241, "a"): ("建设者五成", "运营者三成", "继任者两成", "功劳与成本"),
            (241, "b"): ("建设者三成三", "继任者三成四", "功劳与成本"),
            (301, "a"): ("扣除三十分继承势能", "个人功劳记九十分"),
            (301, "b"): ("扣除二十分继承势能", "个人功劳记一百分"),
            (303, "a"): ("一个周期保护", "恢复正常考核"),
            (303, "b"): ("签字里程碑", "最多持续两个周期"),
            (306, "a"): ("管理责任三成", "专业责任七成", "分配考核权"),
            (306, "b"): ("各五成", "分配考核权"),
            (308, "a"): ("百人编制", "二十名管理岗", "八十名专业岗"),
            (308, "b"): ("百人编制", "三十名管理岗", "七十名专业岗"),
            (309, "a"): ("十小时管理容量", "增加十点可见度", "不增加交付产出"),
            (309, "b"): ("十小时管理容量", "增加十点可见度", "不增加交付产出"),
            (335, "a"): ("唯一的紧急插单槽", "不削减原需求范围"),
            (335, "b"): ("十小时原需求范围", "保留紧急插单槽"),
            (336, "a"): ("不准入", "补齐收益、边界与依赖"),
            (336, "b"): ("有界探索准入", "十小时容量"),
            (338, "a"): ("削减十小时范围", "期限不变"),
            (338, "b"): ("期限延长一个周期", "范围不变"),
            (339, "a"): ("实际八小时", "不记灌水"),
            (339, "b"): ("四小时外部阻塞", "实际十二小时按八小时校准"),
            (340, "a"): ("一个在制任务槽", "按需求估算值预留容量"),
            (340, "b"): ("两个在制任务槽", "额外预留十小时容量"),
            (342, "a"): ("独立复核人解阻", "全归团队不可控阻碍", "团队不扣分"),
            (342, "b"): ("团队与外部原因各承担一半", "不作低产出扣分"),
            (341, "a"): ("结转十小时", "下期预占十小时容量"),
            (341, "b"): ("结转五小时", "下期预占五小时"),
            (343, "a"): ("提出人、执行人和验收人", "通过验收"),
            (343, "b"): ("提出人、执行人和验收人", "有条件验收"),
            (344, "a"): ("上线六成", "采用两成五", "已验证价值一成五"),
            (344, "b"): ("上线三成", "采用三成", "已验证价值四成"),
        }
        for (mid, letter), tokens in expected_tokens.items():
            value = chinese[f"zg361p3.{mid}.{letter}"]
            with self.subTest(mid=mid, letter=letter):
                for token in tokens:
                    self.assertIn(token, value)

        reviewed_keys = (
            "zg361p3.236.a", "zg361p3.236.b", "zg361p3.237.a",
            "zg361p3.239.desc", "zg361p3.239.a", "zg361p3.240.desc",
            "zg361p3.240.a", "zg361p3.240.b",
        )
        reviewed_copy = "\n".join(chinese[key] for key in reviewed_keys)
        for forbidden in ("预注册", "样本槽", "占用一个槽", "签字切分"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, reviewed_copy)

        english = loc_rows(
            MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml"
        )
        self.assertIn("near-threshold results do not collapse to zero", english["zg361p3.236.a"])
        self.assertIn("recorded before the review began", english["zg361p3.237.a"])
        self.assertIn("rules recorded in advance", english["zg361p3.239.desc"])
        self.assertIn("independent reviewer sign off", english["zg361p3.240.b"])
        reviewed_english = "\n".join(english[key] for key in reviewed_keys).lower()
        for forbidden in ("preregister", "sample slot", "partition one slot"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, reviewed_english)

        self.assertNotIn("亲自回应", chinese["zg361p3.304.desc"])

    def test_m342_external_blocker_button_names_action_and_exact_consequences(self) -> None:
        expected_cn = "指定独立复核人解阻；阻塞工时全归团队不可控阻碍，交付团队不扣分。"
        expected_en = (
            "Name the independent reviewer as unblock owner; assign all blocked time to "
            "obstacles beyond the delivery team's control and apply no team penalty."
        )
        chinese = loc_rows(
            MOD_ROOT / "localization" / "simp_chinese" / "zg361_phase3_metrics_delivery_l_simp_chinese.yml"
        )
        english = loc_rows(
            MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml"
        )
        self.assertEqual(self.specs[342].routes_cn[0], expected_cn)
        self.assertEqual(self.specs[342].routes_en[0], expected_en)
        self.assertEqual(chinese["zg361p3.342.a"], expected_cn)
        self.assertEqual(english["zg361p3.342.a"], expected_en)
        self.assertNotIn("计入外部依赖。", "\n".join(chinese.values()))
        self.assertNotIn("外部依赖", chinese["zg361p3.342.a"])
        self.assertNotIn("Charge the external dependency.", "\n".join(english.values()))
        self.assertNotIn("external", english["zg361p3.342.a"].lower())

        route = block(self.effects, "zg361_p3_m342_route_a_effect")
        self.assertIn(
            "name = zg361_p3_m342_blocker_owner value = var:zg361_p3_cross_reviewer",
            route,
        )
        self.assertIn("name = zg361_p3_m342_team_blocker_bps value = 0", route)
        self.assertIn("name = zg361_p3_m342_external_blocker_bps value = 10000", route)
        self.assertIn("name = zg361_p3_m342_executor_low_output_penalty value = 0", route)

    def test_seven_daily_languages_are_exact_english_placeholders(self) -> None:
        english = loc_rows(MOD_ROOT / "localization" / "english" / "zg361_phase3_metrics_delivery_l_english.yml")
        for language in ("french", "german", "japanese", "korean", "polish", "russian", "spanish"):
            with self.subTest(language=language):
                path = MOD_ROOT / "localization" / language / f"zg361_phase3_metrics_delivery_l_{language}.yml"
                self.assertEqual(read(path).splitlines()[0], f"l_{language}:")
                self.assertEqual(loc_rows(path), english)

    def test_spec_maps_all_ids_once_and_states_static_boundary(self) -> None:
        table_ids = [int(mid) for mid in re.findall(r"\| (?:AA|AG|AJ) \| (\d{3}) / \d", self.spec)]
        self.assertEqual(set(table_ids), EXPECTED_IDS)
        self.assertEqual(len(table_ids), 35)
        self.assertIn("CK3 script static-ready", self.spec)
        self.assertIn("唯一 manager-scope portfolio adapter", self.spec)
        self.assertIn("同一游戏日最多产生一个可见业务窗口", self.spec)
        self.assertIn("D+1 hidden queue", self.spec)
        self.assertIn("AI domain runner 不含 `trigger_event`", self.spec)
        self.assertIn("35 项 C 共用同一合同", self.spec)
        self.assertIn("`due_cycle = debt_cycle + 1 = ROOT.review_serial`", self.spec)
        self.assertIn("`zg361_b2_management_debt`", self.spec)
        self.assertIn("过期债", self.spec)
        self.assertIn("未来债", self.spec)
        self.assertIn("没有中央 `on_action`", self.spec)
        self.assertIn("没有 MCP named action/query", self.spec)
        self.assertIn("没有 CK3 parser/error.log", self.spec)
        self.assertIn("其余七语仍是英文结构占位", self.spec)


if __name__ == "__main__":
    unittest.main(verbosity=2)

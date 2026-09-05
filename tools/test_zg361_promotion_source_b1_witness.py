#!/usr/bin/env python3
"""Focused source-projection regression, not a CK3 or open_kaishek runtime.

Read the real opener's D0 flag/serial/state writes and evaluate only the
production witness's Boolean subset. No world, scheduled event, or subject
state is promoted into a played-owner manager cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mod_zhongguo_style"


def read(relative: str) -> str:
    return (MOD / relative).read_text(encoding="utf-8-sig")


def block(source: str, key: str) -> str:
    match = re.search(rf"\b{re.escape(key)}\s*=\s*\{{", source)
    if match is None:
        raise AssertionError(f"missing block: {key}")
    start = match.end()
    depth = 1
    for index in range(start, len(source)):
        depth += (source[index] == "{") - (source[index] == "}")
        if depth == 0:
            return source[start:index]
    raise AssertionError(f"unterminated block: {key}")


@dataclass
class OwnerProjection:
    flags: set[str] = field(default_factory=set)
    variables: dict[str, int] = field(default_factory=dict)
    is_ai: bool = False


def opened_owner_projection() -> OwnerProjection:
    """Project only writes preceding the first authored classification call."""
    opened = block(
        read("common/scripted_effects/zg361_b1_runtime_effects.txt"),
        "zg361_b1_open_cycle_effect",
    )
    prefix = opened.split("zg361_b1_classify_function_effect = yes", 1)[0]
    added = re.findall(r"add_character_flag\s*=\s*(\w+)", prefix)
    serial_initial = re.search(
        r"set_variable\s*=\s*\{\s*name = zg361_b1_manager_cycle_serial value = (\d+)\s*\}",
        prefix,
    )
    serial_add = re.search(
        r"change_variable\s*=\s*\{\s*name = zg361_b1_manager_cycle_serial add = (\d+)\s*\}",
        prefix,
    )
    state = re.search(
        r"set_variable\s*=\s*\{\s*name = zg361_b1_cycle_state value = (\d+)\s*\}",
        prefix,
    )
    if serial_initial is None or serial_add is None or state is None:
        raise AssertionError("D0 source projection no longer matches the opener")
    return OwnerProjection(
        flags=set(added),
        variables={
            "zg361_b1_manager_cycle_serial": int(serial_initial[1]) + int(serial_add[1]),
            "zg361_b1_cycle_state": int(state[1]),
        },
    )


def shown(source: str, owner: OwnerProjection) -> bool:
    """Evaluate this witness's small, explicit Boolean/flag/number subset."""
    source = re.sub(r"#[^\n]*", "", source)
    tokens = re.findall(r">=|<=|!=|[{}=<>]|[^\s{}=<>!]+", source)
    cursor = 0

    def clauses() -> list[bool]:
        nonlocal cursor
        results = []
        while cursor < len(tokens) and tokens[cursor] != "}":
            key, operator, value = tokens[cursor:cursor + 3]
            cursor += 3
            if value == "{":
                children = clauses()
                if tokens[cursor] != "}":
                    raise AssertionError("missing closing brace")
                cursor += 1
                if operator != "=" or key not in {"OR", "AND", "NOT"}:
                    raise AssertionError(f"outside focused witness subset: {key}")
                results.append(any(children) if key == "OR" else
                               not all(children) if key == "NOT" else all(children))
            elif key == "is_ai" and operator == "=":
                results.append(owner.is_ai == (value == "yes"))
            elif key == "has_character_flag" and operator == "=":
                results.append(value in owner.flags)
            elif key == "has_variable" and operator == "=":
                results.append(value in owner.variables)
            elif key.startswith("var:"):
                observed = owner.variables.get(key[4:])
                expected = int(value)
                results.append(observed is not None and {
                    "=": lambda: observed == expected,
                    ">": lambda: observed > expected,
                    ">=": lambda: observed >= expected,
                    "<=": lambda: observed <= expected,
                }[operator]())
            else:
                raise AssertionError(f"outside focused witness subset: {key}")
        return results

    result = all(clauses())
    if cursor != len(tokens):
        raise AssertionError("unexpected trailing witness tokens")
    return result


class B1WitnessSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.guis = read("common/scripted_guis/zg361_promotion_source_progress_guis.txt")
        cls.witness = block(block(cls.guis, "zg361_promotion_source_b1_active_gui"), "is_shown")
        cls.business = block(
            read("common/scripted_triggers/zg361_triggers.txt"),
            "zg361_review_now_business_valid_trigger",
        )

    def test_real_bridge_opener_d0_is_observable(self) -> None:
        bridge = block(read("common/scripted_guis/zg361_scoreboard_guis.txt"), "zg361_review_now_bridge_gui")
        self.assertIn("zg361_b1_open_cycle_effect = yes", bridge)
        owner = opened_owner_projection()
        self.assertEqual(owner.flags, {"zg361_b1_cycle_active"})
        self.assertEqual(owner.variables["zg361_b1_cycle_state"], 1)
        self.assertTrue(shown(self.witness, owner))
        # Exact historical predicate explains the real D0 observation mismatch.
        historical = re.sub(r"OR\s*=\s*\{[^{}]*\}",
                            "has_character_flag = zg361_review_in_progress", self.witness)
        self.assertFalse(shown(historical, owner))

    def test_existing_late_review_remains_observable(self) -> None:
        owner = opened_owner_projection()
        owner.flags = {"zg361_review_in_progress"}
        for state in (1, 8):
            owner.variables["zg361_b1_cycle_state"] = state
            self.assertTrue(shown(self.witness, owner))

    def test_frozen_old_save_uses_only_manager_review_witness(self) -> None:
        owner = OwnerProjection(
            flags={"zg361_b1_cycle_active"},
            variables={
                "zg361_b1_policy_next_review_serial": 20,
                "zg361_b1_cycle_state": 1,
            },
        )
        self.assertTrue(shown(self.witness, owner))
        owner.variables["zg361_b1_policy_next_review_serial"] = 1
        self.assertFalse(shown(self.witness, owner))
        owner.variables["zg361_b1_policy_next_review_serial"] = 20
        owner.flags.clear()
        self.assertFalse(shown(self.witness, owner))

    def test_idle_legacy_only_subject_only_and_ai_are_not_manager_evidence(self) -> None:
        self.assertFalse(shown(self.witness, OwnerProjection()))
        self.assertFalse(shown(self.witness, OwnerProjection(flags={"zg361_review_in_progress"})))
        subject_initializer = block(
            read("common/scripted_effects/zg361_b1_runtime_effects.txt"),
            "zg361_b1_initialize_subject_case_effect",
        )
        for assignment in (
            "name = zg361_b1_cycle_serial value = root.var:zg361_b1_manager_cycle_serial",
            "name = zg361_b1_case_state value = 1",
            "name = zg361_b1_case_active value = 1",
        ):
            self.assertIn(assignment, subject_initializer)
        self.assertFalse(shown(self.witness, OwnerProjection(variables={
            "zg361_b1_cycle_serial": 1,
            "zg361_b1_case_state": 1,
            "zg361_b1_case_active": 1,
        })))
        owner = opened_owner_projection()
        owner.is_ai = True
        self.assertFalse(shown(self.witness, owner))
        owner.is_ai = False
        for state in (0, 9):
            owner.variables["zg361_b1_cycle_state"] = state
            self.assertFalse(shown(self.witness, owner))

    def test_active_gate_matches_opener_and_both_action_paths_use_it(self) -> None:
        opened = block(read("common/scripted_effects/zg361_b1_runtime_effects.txt"), "zg361_b1_open_cycle_effect")
        active_gate = "NOT = { has_character_flag = zg361_b1_cycle_active }"
        self.assertIn(active_gate, block(opened, "limit"))
        self.assertIn(active_gate, self.business)
        gate = "NOT = {" + block(self.business, "NOT") + "}"
        self.assertFalse(shown(gate, opened_owner_projection()))
        self.assertTrue(shown(gate, OwnerProjection()))
        native_action = block(self.guis, "zg361_review_now_native_action_gui")
        for region in (block(native_action, "is_shown"), block(block(native_action, "effect"), "limit")):
            self.assertIn("zg361_review_now_business_valid_trigger = yes", region)
            self.assertIn("prestige >= 150", region)
        self.assertEqual(native_action.count("add_prestige = -150"), 1)
        self.assertEqual(native_action.count("add_character_flag = zg361_review_now_pending"), 1)
        decision = block(read("common/decisions/zg361_decisions.txt"), "zg361_review_now_decision")
        self.assertEqual(decision.count("zg361_review_now_business_valid_trigger = yes"), 2)


if __name__ == "__main__":
    unittest.main()

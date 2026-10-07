"""Exercise actual MCP validation before the typed gameplay facade is invoked."""
from __future__ import annotations

from contextlib import ExitStack
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.mcp_server import create_server
from xar_autoplayer.bridge.service import GameplayBridgeService


class NoGameplayDriver:
    """A validation test must never touch native transport or an actual game."""

    def take_snapshot(self):
        raise AssertionError("unexpected gameplay snapshot")

    def capabilities(self):
        raise AssertionError("unexpected gameplay capabilities")

    def execute_step(self, *args, **kwargs):
        raise AssertionError("unexpected gameplay transport")


class PublicCUnitMcpTests(unittest.IsolatedAsyncioTestCase):
    def _public_unit_integer_schema(self, schema):
        if schema.get("type") == "integer":
            return schema, False
        branches = schema["anyOf"]
        self.assertCountEqual([branch.get("type") for branch in branches], ["integer", "null"])
        return next(branch for branch in branches if branch.get("type") == "integer"), True

    async def test_all_public_unit_facades_preserve_zero_and_reject_coercion(self):
        from mcp import Client

        cases = [
            ("ck3_move_army", "army_id", False, {"target_province_id": 2635}),
            ("ck3_disband_army", "army_id", False, {}),
            ("ck3_query_army_strengths", "army_ids", True, {}),
            ("ck3_query_actual_contact_scope", "subject_army_id", False, {"target_province_id": 2635}),
            ("ck3_query_battle_control_snapshot_v1", "subject_army_id", False, {"expected_revision": 4}),
            ("ck3_query_battle_terminal_transition_v1", "subject_public_cunit_id", False, {"prior_combat_id": 1, "expected_revision": 4}),
            ("ck3_query_battle_reinforcement_assignment_v1", "selected_public_cunit_id", False, {"expected_revision": 4}),
            ("ck3_select_army_ui_v1", "subject_army_id", False, {"expected_revision": 4}),
            ("ck3_preview_active_combat_retreat_v1", "selected_public_cunit_id", False, {"target_province_id": 2635, "expected_revision": 4}),
            ("ck3_order_active_combat_retreat_v1", "selected_public_cunit_id", False, {
                "expected_revision": 4, "expected_combat_id": 1, "expected_side_index": 0,
                "expected_scope": "player", "target_province_id": 2635, "candidate_token": "offline-token",
            }),
            ("ck3_query_current_battle_knight_v1", "subject_public_cunit_id", False, {
                "character_id": 1, "regiment_id": 1, "expected_played_character_id": 1,
                "expected_war_id": 1, "expected_native_carmy_id": 1, "expected_combat_id": 1,
                "expected_province_id": 1, "expected_date_raw": 53146848,
                "expected_revision": 4, "expected_native_revision": 3, "expected_snapshot_id": "offline:3",
            }),
        ]
        for tool_name in ("ck3_query_combat_simulation_inputs", "ck3_query_combat_simulation_inputs_v3"):
            for name, other in (("attacker_army_ids", "defender_army_ids"), ("defender_army_ids", "attacker_army_ids")):
                cases.append((tool_name, name, True, {
                    "target_province_id": 2635, "attacker_entry_province_id": 2634, other: [18],
                }))
        methods = {tool_name.removeprefix("ck3_") for tool_name, _, _, _ in cases}
        with ExitStack() as stack:
            mocks = {
                name: stack.enter_context(patch.object(GameplayBridgeService, name, return_value={"validation_test": True}))
                for name in methods
            }
            server = create_server(NoGameplayDriver())
            async with Client(server) as client:
                tools = {tool.name: tool for tool in (await client.list_tools()).tools}
                for tool_name, name, is_list, base in cases:
                    method = mocks[tool_name.removeprefix("ck3_")]
                    schema = tools[tool_name].input_schema["properties"][name]
                    if is_list:
                        schema = schema["items"]
                    schema, nullable = self._public_unit_integer_schema(schema)
                    self.assertEqual(nullable, (tool_name, name) == (
                        "ck3_query_battle_terminal_transition_v1", "subject_public_cunit_id",
                    ))
                    self.assertEqual(schema["minimum"], 0)
                    self.assertEqual(schema["maximum"], 2**31-1)
                    valid_values = (0, 2**31-1, None) if nullable else (0, 2**31-1)
                    for value in valid_values:
                        argument = [value] if is_list else value
                        with self.subTest(tool=tool_name, name=name, value=value):
                            before = method.call_count
                            result = await client.call_tool(tool_name, {**base, name: argument})
                            self.assertFalse(result.is_error)
                            self.assertEqual(method.call_count, before+1)
                            call = method.call_args
                            forwarded = call.kwargs.get(name) if name in call.kwargs else next(
                                arg for arg in call.args if type(arg) is type(argument) and arg == argument
                            )
                            self.assertEqual(forwarded, argument)
                    if nullable:
                        with self.subTest(tool=tool_name, name=name, value=None):
                            before = method.call_count
                            result = await client.call_tool(tool_name, {
                                **base, "prior_combat_id": None, name: None, "character_ids": [1],
                            })
                            self.assertFalse(result.is_error)
                            self.assertEqual(method.call_count, before+1)
                            self.assertEqual(method.call_args.args[:2], (None, None))
                            self.assertEqual(method.call_args.kwargs["character_ids"], [1])
                    invalid_values = (True, False, -1, 2**31, 2**32-1, 0.0, "0")
                    if not nullable:
                        invalid_values += (None,)
                    for value in invalid_values:
                        argument = [value] if is_list else value
                        with self.subTest(tool=tool_name, name=name, invalid=value):
                            before = method.call_count
                            result = await client.call_tool(tool_name, {**base, name: argument})
                            self.assertTrue(result.is_error)
                            self.assertEqual(method.call_count, before)


if __name__ == "__main__":
    unittest.main()

"""Bounded ownership checks for a proposed per-call row cache, not its adoption.

These tests retain the current independent-list contract. Read-only dict/list
subclasses reject writes to caller inputs while permitting legitimate deepcopy
into private, mutable model state. No endpoint, daemon or native action is used.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import fields, is_dataclass, replace
import unittest
from unittest.mock import patch

from xar_autoplayer import strategy
from xar_autoplayer.simulation.battle_current_adapter import adapt_current_battle_condition
from xar_autoplayer.simulation.battle_current_phase_transition import _clear_loser
from xar_autoplayer.simulation.battle_current_normal_finalizer import (
    CurrentNormalFinalizerManagerInputs, project_current_normal_finalizer,
)
from xar_autoplayer.simulation.combat_core import _clear_nonretreating_entries
from test_battle_control_snapshot_v1_bridge import _battle_frame
import test_battle_current_normal_finalizer as finalizer_fixture
import test_battle_current_horizon_owner_qualified_hook as owner_fixture


def _deny(*args, **kwargs):
    raise AssertionError("caller-owned mutable input was written")


class _ReadOnlyDict(dict):
    __setitem__ = __delitem__ = clear = pop = popitem = setdefault = update = __ior__ = _deny

    def __deepcopy__(self, memo):
        result = {}
        memo[id(self)] = result
        result.update((deepcopy(k, memo), deepcopy(v, memo)) for k, v in self.items())
        return result


class _ReadOnlyList(list):
    __setitem__ = __delitem__ = append = clear = extend = insert = pop = remove = reverse = sort = __iadd__ = __imul__ = _deny

    def __deepcopy__(self, memo):
        result = []
        memo[id(self)] = result
        result.extend(deepcopy(v, memo) for v in self)
        return result


def _readonly(value, memo=None):
    memo = {} if memo is None else memo
    if id(value) in memo:
        return memo[id(value)]
    if isinstance(value, dict):
        result = _ReadOnlyDict((k, _readonly(v, memo)) for k, v in value.items())
    elif isinstance(value, list):
        result = _ReadOnlyList(_readonly(v, memo) for v in value)
    elif isinstance(value, tuple):
        result = tuple(_readonly(v, memo) for v in value)
    elif is_dataclass(value) and not isinstance(value, type):
        result = replace(value, **{f.name: _readonly(getattr(value, f.name), memo)
            for f in fields(value) if f.init})
    else:
        return value
    memo[id(value)] = result
    return result


def _mutable_ids(value, seen=None):
    seen = set() if seen is None else seen
    if id(value) in seen:
        return set()
    seen.add(id(value))
    result = {id(value)} if isinstance(value, (dict, list, set)) else set()
    if isinstance(value, dict):
        children = value.values()
    elif isinstance(value, (tuple, list, set)):
        children = value
    elif is_dataclass(value) and not isinstance(value, type):
        children = (getattr(value, f.name) for f in fields(value))
    else:
        children = ()
    for child in children:
        result |= _mutable_ids(child, seen)
    return result


def _history():
    frame = _battle_frame()
    subject, revision = frame["subject_public_cunit_id"], frame["snapshot_revision"]
    step = "query-battle-control-snapshot-v1-" + str(subject)
    return [{"command": step, "ok": True, "result": {
        "step": step, "accepted": True, "status": "available", "query_sequence": 1,
        "queried_snapshot_id": "native:" + str(revision), "queried_revision": 3,
        "queried_native_revision": revision, "snapshot_revision": revision,
        "battle_control_snapshot": frame}}]


class CommandRowCacheIsolationAuditTests(unittest.TestCase):
    def test_current_expansion_isolates_outer_rows_but_already_shares_payloads(self):
        payload = {"nested": [1]}
        raw = [{"command": "auto-run 1", "result": {"turns": [
            {"command": "sample", "ok": True, "result": payload}]}}]
        first, second = (strategy._expanded_command_rows(raw) for _ in range(2))
        self.assertIsNot(first, second)
        self.assertIsNot(first[0], second[0])
        self.assertIs(first[0]["result"], second[0]["result"])
        first[0]["index"] = 9
        first.clear()
        self.assertEqual(second[0]["index"], 1)
        self.assertEqual(len(second), 1)
        self.assertIs(second[0]["result"], payload)

    def test_battle_control_reads_readonly_rows_and_normalizes_into_private_frames(self):
        rows = _readonly(_history())
        before = deepcopy(rows)
        first = strategy._battle_control_query_records(rows)
        second = strategy._battle_control_query_records(rows)
        self.assertEqual(len(first), 1)
        self.assertEqual(first, second)
        self.assertFalse(_mutable_ids(first) & _mutable_ids(rows))
        first[0]["frame"]["attacker"]["ordered_armies"][0]["fixture_annotation"] = True
        self.assertNotIn("fixture_annotation", second[0]["frame"]["attacker"]["ordered_armies"][0])
        frame = rows[0]["result"]["battle_control_snapshot"]
        snapshot = {"paused": True, "snapshot_id": rows[0]["result"]["queried_snapshot_id"],
            "revision": 3, "native_revision": frame["snapshot_revision"],
            "date_raw": frame["observed_date_raw"]}
        current, records = strategy._current_battle_control_frames(rows, snapshot)
        self.assertIs(current[frame["subject_public_cunit_id"]], records[0])
        self.assertEqual(rows, before)

    def test_adapter_detaches_mutable_frame_before_clear_but_model_is_not_deeply_frozen(self):
        records = strategy._battle_control_query_records(_history())
        frame = _readonly(records[0]["frame"])
        condition = adapt_current_battle_condition(frame)
        self.assertFalse(_mutable_ids(condition) & _mutable_ids(frame))
        protected = _readonly(condition)
        before = deepcopy(protected)
        cleared, evidence = _clear_loser(protected, 1)
        self.assertEqual(cleared.phase_raw, 3)
        self.assertTrue(evidence)
        self.assertEqual(protected, before)
        self.assertIs(cleared.source_snapshot, protected.source_snapshot)
        self.assertIs(cleared.sides[1].entries[0].source_entry,
            protected.sides[1].entries[0].source_entry)
        raw = tuple(entry.state for entry in protected.sides[1].entries)
        after = _clear_nonretreating_entries(raw)
        self.assertTrue(all(entry.current_raw == 0 for entry in after))
        self.assertTrue(any(entry.current_raw != 0 for entry in raw))

    def test_selected_owner_withdrawal_accepts_readonly_inputs_without_writes(self):
        original = owner_fixture.horizon.apply_selected_owner_subset_retreats_12003
        calls = []

        def checked(carried, events, **kwargs):
            carried, events, kwargs = _readonly((carried, events, kwargs))
            before = deepcopy((carried, events, kwargs))
            result = original(carried, events, **kwargs)
            self.assertEqual((carried, events, kwargs), before)
            self.assertIsNot(result.carried.condition, carried.condition)
            calls.append(True)
            return result

        with patch.object(owner_fixture.horizon,
                "apply_selected_owner_subset_retreats_12003", side_effect=checked):
            case = owner_fixture.CurrentHorizonOwnerQualifiedHookTest()
            case.test_admitted_qualified_callback_keeps_backing_and_carries_q_once()
        self.assertEqual(calls, [True])

    def test_finalizer_accepts_readonly_condition_manager_and_backing(self):
        condition = _readonly(finalizer_fixture._condition())
        backing = _readonly(finalizer_fixture._carried_state())
        manager = _readonly(CurrentNormalFinalizerManagerInputs(
            entry_kind="daily_row", combat_manager_row_admitted=True,
            pending_suppression_sweep=False, primary_hostile=None,
            finalized=None, processing=None, result_present=None,
            source_context={"kind": "bounded_isolation_fixture"}))
        before = deepcopy((condition, manager, backing))
        result = project_current_normal_finalizer(condition, manager=manager,
            current_state_by_regiment=backing)
        self.assertEqual((condition, manager, backing), before)
        self.assertEqual(result["actual_game_days_advanced"], 0)
        self.assertFalse(result["actual_native_effects_executed"])

    def test_battle_transition_recursion_receives_a_distinct_reduced_history(self):
        commands = [{"command": "first", "ok": True}, {"command": "second", "ok": True}]
        rows = strategy._expanded_command_rows(commands)
        transition = {"status": "transition_recognized", "remaining_rows": rows[1:],
            "transitions": [{"status": "combat_replaced"}]}
        snapshot = {"paused": True, "played_character": {"character_id": 7, "alive": True},
            "active_wars": [], "player_armies": []}
        with patch.object(strategy, "_battle_control_turn_state", return_value=transition), \
                patch.object(strategy, "choose_one_life_turn", return_value={
                    "phase": "child", "selected_step": None}) as child:
            result = strategy._choose_one_life_turn_core(commands, snapshot=snapshot)
        self.assertEqual(result["phase"], "child")
        self.assertEqual(child.call_args.args[0], rows[1:])
        self.assertNotEqual(child.call_args.args[0], commands)
        self.assertEqual(commands, [{"command": "first", "ok": True},
            {"command": "second", "ok": True}])


if __name__ == "__main__":
    unittest.main()

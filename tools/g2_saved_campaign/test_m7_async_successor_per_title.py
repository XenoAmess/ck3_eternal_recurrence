"""Keep the real per-title reconciliation on the completed async Queue path."""
from __future__ import annotations

import asyncio
import copy
from pathlib import Path
import sys
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))
sys.path.insert(0, str(REPOSITORY_ROOT / "ck3_autonomous_player" / "src"))

from g2_saved_campaign.m7_ordinary_successor_async_queue import (
    AsyncOrdinarySuccessorQueue,
)
from xar_autoplayer.bridge.succession_transition_contract import (
    CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
    ORDINARY_CAMPAIGN_SUCCESSION,
    bind_succession_lifecycle_from_environment_v1,
    freeze_succession_expectation_v1,
    reconcile_succession_transition_v1,
)


def _available(value):
    return {"status": "available", "value": value, "unavailable_reason": None}


def _title(title_id, heir_id, *, primary=False):
    return {
        "title": {
            "title_id": title_id,
            "tier_raw": 4 if primary else 2,
            "tier_key": "kingdom" if primary else "county",
        },
        "first_heir_character_id": heir_id,
        "capital_province_id": None if primary else title_id + 1_000,
        "primary": primary,
    }


def _bundle(character_id, *, frame, rows, primary_heir):
    return {
        "schema": "xar.ck3.turn-bundle/v1",
        "status": "available",
        "binding": copy.deepcopy(frame),
        "ruler_state": _available({"character_id": character_id, "alive": True}),
        "succession_state": _available({
            "primary_title_heir_character_id": _available(primary_heir),
            "partition": _available({
                "title_heirs": rows,
                "risk_state": "split_successors" if character_id == 100 else "single_successor",
            }),
        }),
    }


def _goal(character_id, reconciled_successions):
    return {
        "format_version": 1,
        "goal_key": "dynasty_continuity",
        "campaign_id": "ordinary-per-title-fixture",
        "origin_character_id": 100,
        "current_character_id": character_id,
        "progress": {"reconciled_successions": reconciled_successions},
    }


def _completed_transition_inputs():
    lifecycle = bind_succession_lifecycle_from_environment_v1(
        {
            "environment_sha256": "a" * 64,
            "rules": {"profile": [{"rule": "xar_enabled", "setting": "xar_off"}]},
        },
        lifecycle=ORDINARY_CAMPAIGN_SUCCESSION,
        ordinary_campaign_no_pact=True,
    )
    living_frame = {
        "snapshot_id": "native:20", "revision": 7,
        "native_revision": 20, "date_raw": 53_180_000,
    }
    transition_frame = {
        "snapshot_id": "native:24", "revision": 8,
        "native_revision": 24, "date_raw": 53_180_720,
    }
    expectation = freeze_succession_expectation_v1(
        _bundle(100, frame=living_frame, rows=[
            _title(10, 200, primary=True),
            _title(11, 200),
            _title(12, 300),
            _title(13, None),
        ], primary_heir=200),
        episode_run_id="predecessor-run",
        episode_character_id=100,
    )
    terminal = {
        **transition_frame,
        "paused": True, "map_ready": True,
        "played_character": {"character_id": 200, "alive": True},
        "episode_character_id": 100, "episode_run_id": "predecessor-run",
        "one_life_terminal": True,
        "one_life_terminal_reason": "played_character_changed",
        "succession_lifecycle": lifecycle,
        "campaign_goal": _goal(100, 0),
        "diagnostics": {"bridge_pid": 4242, "connection_generation": 1},
    }
    reconciliation = reconcile_succession_transition_v1(
        expectation,
        terminal,
        _bundle(200, frame=transition_frame, rows=[
            _title(10, 400, primary=True), _title(11, 400), _title(99, 400),
        ], primary_heir=400),
    )
    successor = copy.deepcopy(terminal)
    successor.update({
        "episode_character_id": 200, "episode_run_id": "successor-run",
        "one_life_terminal": False, "one_life_terminal_reason": None,
        "campaign_goal": _goal(200, 1),
    })
    completed = {
        "status": "executed",
        "selected_step": CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
        "result": {
            **transition_frame,
            "step": CONTINUE_AS_RECONCILED_SUCCESSOR_STEP,
            "accepted": True, "status": "continued",
            "source": "native-played-character-transition",
            "lifecycle_intent": "natural_succession",
            "succession_lifecycle": lifecycle,
            "predecessor_character_id": 100, "successor_character_id": 200,
            "source_episode_run_id": "predecessor-run",
            "episode_run_id": "successor-run",
            "continue_as_heir_after_death": True, "heir_gameplay_actions": 0,
            "ck3_command_submitted": False, "process_restarted": False,
            "reconciliation": reconciliation,
        },
    }
    return completed, terminal, successor, reconciliation


class _ReadOnlyAsyncQueue:
    def __init__(self, successor):
        self.successor = successor
        self.calls = []
        self.events = []
        self.thin_rows = []

    async def call(self, tool, arguments, kind):
        self.calls.append((tool, copy.deepcopy(arguments), kind))
        self.events.append(("call", kind))
        await asyncio.sleep(0)
        if tool == "ck3_take_snapshot":
            body = copy.deepcopy(self.successor)
        elif tool == "ck3_get_capabilities":
            body = {
                "diagnostics": {"bridge_pid": 4242, "connection_generation": 1},
                "native_session_control": {
                    "episode_binding_state": "active_natural_successor",
                    "driver_state_restore_kind": "natural_succession",
                },
            }
        elif tool == "ck3_query_current_timeline_blocker_context_v1":
            body = {"current_timeline_blocker_context": {
                "status": "available", "identity": "none",
                "blocks_simulation": _available(False),
                "has_open_succession": _available(False),
            }}
        else:
            raise AssertionError("completed continuation must not submit " + tool)
        return body, Path(kind + ".json")

    def thin(self, kind, payload):
        # Keep the supplied reference so the test observes the adapter's own copy.
        self.events.append(("thin", kind))
        self.thin_rows.append((kind, payload))


class AsyncSuccessorPerTitleRetentionTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_keeps_real_per_title_reconciliation_without_resubmit(self):
        completed, terminal, successor, reconciliation = _completed_transition_inputs()
        expected = copy.deepcopy(reconciliation)
        queue = _ReadOnlyAsyncQueue(successor)
        transitions = []

        after, after_path, transition = await AsyncOrdinarySuccessorQueue(queue).consume_completed(
            completed, Path("original-completed.json"),
            terminal, Path("independent-terminal.json"), transitions,
        )

        self.assertEqual(expected["verdict"], "matched")
        self.assertEqual(expected["expected_inherited_title_ids"], [10, 11])
        self.assertEqual(expected["matched_inherited_title_ids"], [10, 11])
        self.assertEqual(expected["missing_expected_inherited_title_ids"], [])
        self.assertEqual(expected["unexpected_retained_predecessor_title_ids"], [])
        self.assertEqual(expected["expected_other_heir_title_ids"], [12])
        self.assertEqual(expected["expected_without_heir_title_ids"], [13])
        self.assertEqual(expected["observed_additional_successor_title_ids"], [99])
        self.assertEqual(after, successor)
        self.assertEqual(after_path, Path("m7-completed-successor-snapshot.json"))
        self.assertEqual(transitions, [transition])
        self.assertIs(transitions[0], transition)
        self.assertEqual(transition["reconciliation"], expected)
        self.assertEqual(transition["continuation_response"], "original-completed.json")
        self.assertEqual(transition["predecessor_context_response"], "independent-terminal.json")

        self.assertEqual([tool for tool, _, _ in queue.calls], [
            "ck3_take_snapshot", "ck3_get_capabilities",
            "ck3_query_current_timeline_blocker_context_v1",
        ])
        self.assertEqual(queue.calls[-1][1], {"expected_revision": 8})
        self.assertEqual([kind for kind, _ in queue.thin_rows], [
            "m7-natural-transition-pending", "m7-natural-transition",
        ])
        pending = queue.thin_rows[0][1]
        final = queue.thin_rows[1][1]
        self.assertLess(
            queue.events.index(("thin", "m7-natural-transition-pending")),
            queue.events.index(("call", "m7-timeline")),
        )
        self.assertEqual(pending["reconciliation"], expected)
        self.assertEqual(final["reconciliation"], expected)
        self.assertIsNot(pending, transition)
        self.assertIsNot(transition["reconciliation"], reconciliation)
        self.assertEqual(transition["timeline_blocker_continuation"]["status"], "already_clear")
        self.assertEqual(transition["successor_checkpoint"]["status"], "pending_actual_clear_successor_save")

        # The retained material result must survive reuse of the completed body.
        reconciliation["matched_inherited_title_ids"].clear()
        reconciliation["observed_additional_successor_title_ids"].append(123)
        reconciliation["successor_binding"]["date_raw"] += 24
        self.assertEqual(transition["reconciliation"], expected)
        self.assertEqual(pending["reconciliation"], expected)
        self.assertEqual(final["reconciliation"], expected)


if __name__ == "__main__":
    unittest.main()

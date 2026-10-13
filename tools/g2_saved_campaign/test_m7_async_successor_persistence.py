"""Verify retention of one completed continuation in the new async adapter."""
from __future__ import annotations

import copy
from pathlib import Path
import unittest

from tools.g2_saved_campaign.m7_ordinary_successor_async_queue import AsyncOrdinarySuccessorQueue


def completed_continuation_fixture() -> dict[str, object]:
    """One actual-contract shaped response; it does not simulate a CK3 death."""

    lifecycle = {
        "schema": "xar.ck3.succession-lifecycle-binding/v1",
        "lifecycle": "ordinary_campaign_succession",
        "xar_enabled": "xar_off",
        "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
        "source": "prepared-environment-manifest",
        "environment_sha256": "a" * 64,
    }
    frame = {
        "snapshot_id": "native:42",
        "revision": 6,
        "native_revision": 42,
        "date_raw": 53169360,
    }
    diagnostics = {"bridge_pid": 321, "connection_generation": 7}
    old_run, new_run = "native-100-predecessor", "native-200-successor"
    goal_before = {
        "format_version": 1,
        "goal_key": "dynasty_continuity",
        "campaign_id": "campaign-a",
        "origin_character_id": 100,
        "current_character_id": 100,
        "progress": {"reconciled_successions": 0},
    }
    goal_after = copy.deepcopy(goal_before)
    goal_after["current_character_id"] = 200
    goal_after["progress"]["reconciled_successions"] = 1
    goal_after["last_succession"] = {
        "predecessor_character_id": 100,
        "successor_character_id": 200,
        "date_raw": frame["date_raw"],
    }
    source = {
        **frame,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": 200, "alive": True},
        "episode_character_id": 100,
        "episode_run_id": old_run,
        "one_life_terminal": True,
        "one_life_terminal_reason": "played_character_changed",
        "succession_lifecycle": copy.deepcopy(lifecycle),
        "campaign_goal": copy.deepcopy(goal_before),
        "diagnostics": copy.deepcopy(diagnostics),
    }
    successor = {
        **copy.deepcopy(source),
        "episode_character_id": 200,
        "episode_run_id": new_run,
        "one_life_terminal": False,
        "one_life_terminal_reason": None,
        "campaign_goal": copy.deepcopy(goal_after),
        "active_event": None,
        "pending_character_interaction": None,
    }
    reconciliation = {
        "schema": "xar.ck3.succession-reconciliation/v1",
        "status": "available",
        "predecessor_binding": {
            "snapshot_id": "native:41",
            "revision": 5,
            "native_revision": 41,
            "date_raw": frame["date_raw"] - 24,
            "episode_character_id": 100,
            "episode_run_id": old_run,
        },
        "successor_binding": copy.deepcopy(frame),
        "predecessor_character_id": 100,
        "expected_successor_character_id": 200,
        "actual_successor_character_id": 200,
        "successor_match": True,
        "expected_inherited_title_ids": [11, 12],
        "matched_inherited_title_ids": [11, 12],
        "missing_expected_inherited_title_ids": [],
        "unexpected_retained_predecessor_title_ids": [],
        "expected_other_heir_title_ids": [13],
        "expected_without_heir_title_ids": [14],
        "observed_additional_successor_title_ids": [21],
        "title_distribution_match": True,
        "verdict": "matched",
        "unavailable_reason": None,
    }
    step = "continue-as-reconciled-successor"
    turn = {
        "status": "executed",
        "selected_step": step,
        "result": {
            **copy.deepcopy(frame),
            "step": step,
            "accepted": True,
            "status": "continued",
            "source": "native-played-character-transition",
            "lifecycle_intent": "natural_succession",
            "succession_lifecycle": copy.deepcopy(lifecycle),
            "predecessor_character_id": 100,
            "successor_character_id": 200,
            "source_episode_run_id": old_run,
            "episode_run_id": new_run,
            "reconciliation": reconciliation,
            "continue_as_heir_after_death": True,
            "heir_gameplay_actions": 0,
            "ck3_command_submitted": False,
            "process_restarted": False,
        },
    }
    capabilities = {
        "diagnostics": copy.deepcopy(diagnostics),
        "native_session_control": {
            "episode_binding_state": "active_natural_successor",
            "driver_state_restore_kind": "natural_succession",
        },
    }
    return {
        "source_snapshot": source,
        "source_path": Path("retained/terminal-before.json"),
        "turn": turn,
        "response_path": Path("retained/completed-auto.json"),
        "successor_snapshot": successor,
        "successor_path": Path("retained/successor-snapshot.json"),
        "capabilities": capabilities,
        "capabilities_path": Path("retained/successor-capabilities.json"),
    }


class TimelineFailureQueue:
    """Retain callback payloads while the next genuine queue read fails."""

    def __init__(self, fixture: dict[str, object]) -> None:
        self.fixture = fixture
        self.events: list[tuple[str, str]] = []
        self.retained: list[tuple[str, dict[str, object]]] = []

    async def call(self, tool, arguments, kind):
        self.events.append(("call", tool))
        if tool == "ck3_take_snapshot":
            return (copy.deepcopy(self.fixture["successor_snapshot"]),
                    self.fixture["successor_path"])
        if tool == "ck3_get_capabilities":
            return (copy.deepcopy(self.fixture["capabilities"]),
                    self.fixture["capabilities_path"])
        if tool == "ck3_query_current_timeline_blocker_context_v1":
            raise RuntimeError("timeline unavailable after completed continuation")
        raise AssertionError(f"unexpected queue call: {tool}")

    def thin(self, kind, payload):
        self.events.append(("thin", kind))
        self.retained.append((kind, copy.deepcopy(payload)))


class AsyncSuccessorPersistenceTests(unittest.IsolatedAsyncioTestCase):
    async def test_completed_result_is_retained_before_failed_timeline_read(self):
        fixture = completed_continuation_fixture()
        queue = TimelineFailureQueue(fixture)
        adapter = AsyncOrdinarySuccessorQueue(queue)
        transitions: list[dict[str, object]] = []

        with self.assertRaisesRegex(RuntimeError, "timeline unavailable"):
            await adapter.consume_completed(
                fixture["turn"], fixture["response_path"],
                fixture["source_snapshot"], fixture["source_path"],
                transitions,
            )

        self.assertEqual(len(transitions), 1)
        self.assertEqual(
            queue.events,
            [
                ("call", "ck3_take_snapshot"),
                ("call", "ck3_get_capabilities"),
                ("thin", "m7-natural-transition-pending"),
                ("call", "ck3_query_current_timeline_blocker_context_v1"),
            ],
        )
        self.assertEqual(len(queue.retained), 1)
        retained = queue.retained[0][1]
        self.assertEqual(retained["continuation_response"], str(fixture["response_path"]))
        self.assertEqual(retained["predecessor_context_response"], str(fixture["source_path"]))
        self.assertEqual(retained["successor_snapshot_response"], str(fixture["successor_path"]))
        self.assertEqual(retained["reconciliation"], fixture["turn"]["result"]["reconciliation"])
        self.assertEqual(retained["campaign_goal_before"], fixture["source_snapshot"]["campaign_goal"])
        self.assertEqual(retained["campaign_goal_after"], fixture["successor_snapshot"]["campaign_goal"])
        self.assertEqual(retained["episode_run_id"], "native-200-successor")
        self.assertEqual(retained["successor_checkpoint"]["status"], "pending_actual_clear_successor_save")
        self.assertFalse(retained["ck3_command_submitted"])
        self.assertFalse(retained["process_restarted"])
        self.assertEqual(transitions[0]["reconciliation"], retained["reconciliation"])


if __name__ == "__main__":
    unittest.main()

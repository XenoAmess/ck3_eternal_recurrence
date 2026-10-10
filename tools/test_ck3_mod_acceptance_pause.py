"""Portable running-to-paused regressions against actual canonical host methods."""
from __future__ import annotations

import asyncio
import ast
import copy
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

HOST = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"


def frame(*, paused=False, ready=False, revision=9):
    return {
        "snapshot_id": "native:" + str(revision), "revision": revision, "native_revision": revision,
        "date_raw": 100, "speed": 1, "paused": paused, "active_event": None,
        "map_ready": True, "format_version": 1, "complete_snapshot": True,
        "episode_projection": "native_campaign", "backend_id": "native-headless",
        "source": "injected-dll-named-pipe", "local_player_id": 1,
        "played_character": {"character_id": 22, "alive": True},
        "diagnostics": {
            "bridge_pid": 11, "connection_generation": 1, "connected": True,
            "semantic_state_available": True, "last_error": None, "transport_fatal_error": None,
            "pipe_name": r"\\.\pipe\synthetic-pause-only", "rejected_state_snapshot_count": 0,
            "hello": {"pid": 11, "connection_generation": 1,
                      "expected_ck3_version": "1.20.0.4",
                      "expected_ck3_sha256": "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518",
                      "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "ck3_build_match": True},
            "last_heartbeat": {"pid": 11, "main_thread_query_mailbox_v1": {
                "installed": True, "ready": ready, "stop": False, "failure": 0,
                "owner_tid": 33, "current_tid": 33, "owner_verified_pump_epochs": revision,
                "date_raw": 100, "paused": paused, "stamp_read_success": True,
                "application_main_observed": True, "paused_main_thread_observed": paused,
                "consecutive_verified": 5 if paused else 0,
            }},
        },
    }


class RunningPauseTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        cls.definitions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                           and node.name in {"campaign_pause_frame_binding", "require_campaign_pause_successor"}]
        client = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "PlanClient")
        cls.definitions.append(next(node for node in client.body
                                    if isinstance(node, ast.AsyncFunctionDef) and node.name == "pause_campaign_after_advance"))

    def client(self, frames, *, timeout=5, done=False):
        class Client:
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=timeout, poll_interval=0)
                self.report = {}
                self.managed_done = threading.Event()
                if done:
                    self.managed_done.set()
                self.clock = 0.0
                self.calls = []
                self.frames = iter(frames)
                self.last = frames[-1] if frames else None

            async def invoke(self, name, arguments, *, fresh_revision=True):
                self.calls.append((name, dict(arguments), fresh_revision))
                return {"step": "pause-map", "accepted": True, "status": "submitted"}

            async def fresh(self):
                self.clock += .5
                return copy.deepcopy(next(self.frames, self.last))

        value = Client()
        namespace = {"asyncio": asyncio, "time": SimpleNamespace(monotonic=lambda: value.clock)}
        module = ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[]))
        exec(compile(module, str(HOST), "exec"), namespace)
        value.pause = lambda starting: namespace["pause_campaign_after_advance"](value, starting)
        return value

    async def test_actual_running_stamp_precedes_one_pause_and_full_paused_readback(self):
        starting = frame()
        client = self.client([frame(revision=10), frame(paused=True, ready=True, revision=11)])
        result = await client.pause(starting)
        self.assertIs(result["paused"], True)
        self.assertIs(result["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["ready"], True)
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.report["campaign_pause_readbacks"][0]["status"], "FULL_PAUSED_FRAME_OBSERVED")
        # Preserve the already-qualified cached-unpaused/paused-owner path.
        cached = frame(ready=True, revision=10)
        mailbox = cached["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]
        mailbox["paused"] = True
        mailbox["paused_main_thread_observed"] = True
        client = self.client([cached, frame(paused=True, ready=True, revision=11)])
        result = await client.pause(starting)
        self.assertIs(result["paused"], True)
        self.assertEqual(len(client.calls), 1)

    async def test_invalid_running_identity_never_submits_pause(self):
        changes = [
            (("played_character", "alive"), False),
            (("diagnostics", "hello", "pid"), 12),
            (("diagnostics", "hello", "connection_generation"), 2),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "current_tid"), 34),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "date_raw"), 101),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "application_main_observed"), False),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "stamp_read_success"), False),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "paused_main_thread_observed"), True),
            (("active_event",), {"instance_id": 1}), (("complete_snapshot",), False),
            (("speed",), 2), (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "ready"), 0),
        ]
        for path, changed in changes:
            with self.subTest(field=path):
                starting = frame()
                target = starting
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = changed
                client = self.client([frame(paused=True, ready=True, revision=10)])
                with self.assertRaises(RuntimeError):
                    await client.pause(starting)
                self.assertEqual(client.calls, [])

    async def test_deadline_manager_and_post_submission_drift_never_award_paused_success(self):
        client = self.client([frame(revision=10)], timeout=.75)
        with self.assertRaises(TimeoutError):
            await client.pause(frame())
        self.assertEqual(len(client.calls), 1)
        client = self.client([frame(paused=True, ready=True, revision=10)], done=True)
        with self.assertRaises(RuntimeError):
            await client.pause(frame())
        self.assertEqual(client.calls, [])
        changes = [
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "ready"), False),
            (("played_character", "character_id"), 23),
            (("diagnostics", "connection_generation"), 2),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "owner_tid"), 34),
            (("diagnostics", "rejected_state_snapshot_count"), 1),
            (("active_event",), {"instance_id": 1}),
        ]
        for path, changed in changes:
            with self.subTest(successor_drift=path):
                successor = frame(paused=True, ready=True, revision=10)
                target = successor
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = changed
                client = self.client([successor])
                with self.assertRaises(RuntimeError):
                    await client.pause(frame())
                self.assertEqual(len(client.calls), 1)



    async def test_owner_paused_before_snapshot_is_only_waited_without_replay(self):
        pending = frame(revision=10)
        pending['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['paused'] = True
        client = self.client([pending] * 4 + [frame(paused=True, ready=True, revision=11)])
        result = await client.pause(frame())
        self.assertIs(result['paused'], True)
        self.assertEqual(len(client.calls), 1)
        evidence = client.report['campaign_pause_readbacks'][0]
        self.assertEqual(len(evidence['pending_owner_stamp_readbacks']), 4)
        self.assertTrue(all(row['business_credit'] is False for row in evidence['pending_owner_stamp_readbacks']))
        self.assertEqual(evidence['pause_attempt_count'], 1)

    async def test_pending_stamp_identity_and_original_deadline_remain_strict(self):
        pending = frame(revision=10)
        pending['diagnostics']['last_heartbeat']['main_thread_query_mailbox_v1']['paused'] = True
        changes = [
            (('diagnostics', 'connection_generation'), 2),
            (('diagnostics', 'last_heartbeat', 'main_thread_query_mailbox_v1', 'owner_tid'), 34),
            (('diagnostics', 'last_heartbeat', 'main_thread_query_mailbox_v1', 'date_raw'), 101),
            (('diagnostics', 'last_heartbeat', 'main_thread_query_mailbox_v1', 'stamp_read_success'), False),
            (('diagnostics', 'rejected_state_snapshot_count'), 1),
            (('played_character', 'character_id'), 23),
            (('active_event',), {'instance_id': 1}),
            (('complete_snapshot',), False),
        ]
        for path, changed in changes:
            with self.subTest(pending_drift=path):
                target_frame = copy.deepcopy(pending)
                target = target_frame
                for part in path[:-1]:
                    target = target[part]
                target[path[-1]] = changed
                client = self.client([target_frame, frame(paused=True, ready=True, revision=11)])
                with self.assertRaises(RuntimeError):
                    await client.pause(frame())
                self.assertEqual(len(client.calls), 1)
        client = self.client([pending], timeout=1.25)
        with self.assertRaises(TimeoutError):
            await client.pause(frame())
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.report['campaign_pause_readbacks'][0]['status'],
                         'FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED')


if __name__ == "__main__":
    unittest.main()

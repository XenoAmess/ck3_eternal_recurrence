"""Portable explicit campaign event-boundary tests against actual host methods."""
from __future__ import annotations

import asyncio
import ast
import copy
import json
import gc
import warnings
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

from test_ck3_mod_acceptance_pause import frame

HOST = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"


def campaign_frame(date, *, paused=False, event=None, actor=22, revision=9):
    value = frame(paused=paused, ready=paused, revision=revision)
    value["date_raw"] = date
    value["active_event"] = event
    value["played_character"].update(character_id=actor, source="native")
    value["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"]["date_raw"] = date
    return value


class CampaignEventTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        cls.definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                           and n.name in {"campaign_pause_frame_binding", "require_campaign_pause_successor", "campaign_event_instance"}]
        client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PlanClient")
        cls.definitions.extend(n for n in client.body if isinstance(n, ast.AsyncFunctionDef)
                               and n.name in {"advance", "advance_event_boundary", "advance_campaign_event_boundary", "pause_campaign_after_advance"})

    def client(self, observations, *, done=False, tick=.1, rejected_step=None, cancel=False):
        before = campaign_frame(100, paused=True, revision=4)
        class FakeIO:
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=5, poll_interval=0)
                self.report = {}
                self.tools = {name: {} for name in ("ck3_get_capabilities", "ck3_take_snapshot", "ck3_execute_step",
                                                     "ck3_query_current_event_window_context_v1")}
                self.episode_identity = None
                self.managed_done = threading.Event()
                if done:
                    self.managed_done.set()
                self.clock = 0.0
                self.calls = []
                self.waits = 0
                self.frames = iter([before] + observations)
                self.snapshot = before

            async def call(self, name):
                self.calls.append((name, {}))
                return {"snapshot": True, "action_steps": ["pause-map", "resume-map", "set-speed-1"],
                        "current_event_window_context_v1_query_supported": True,
                        "bridge_capabilities": ["game.command.query-current-event-window-context-v1"]}

            async def invoke(self, name, arguments, *, fresh_revision=True):
                self.calls.append((name, dict(arguments)))
                return {"step": arguments["step"], "accepted": arguments["step"] != rejected_step, "status": "submitted"}

            async def fresh(self):
                if cancel:
                    raise asyncio.CancelledError()
                self.clock += tick
                self.snapshot = copy.deepcopy(next(self.frames))
                return self.snapshot

            async def wait_snapshot(self, expected, timeout):
                self.waits += 1
                self.snapshot = copy.deepcopy(before)
                return self.snapshot

            async def set_campaign_speed_one_presubmission_once(self, starting):
                self.calls.append(("speed-preflight", {}))

        value = FakeIO()
        namespace = {"asyncio": asyncio, "json": json, "time": SimpleNamespace(monotonic=lambda: value.clock)}
        definitions = ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[]))
        exec(compile(definitions, str(HOST), "exec"), namespace)
        for name in ("advance", "advance_event_boundary", "advance_campaign_event_boundary", "pause_campaign_after_advance"):
            setattr(value, name, lambda *args, _name=name, **kwargs: namespace[_name](value, *args, **kwargs))
        value.binding = namespace["campaign_pause_frame_binding"]
        return value

    @staticmethod
    def step(**kwargs):
        return {"days": 1, "timeout": 5, "allow_event_boundary": True, **kwargs}

    async def test_campaign_without_episode_reaches_actual_full_paused_day(self):
        value = self.client([campaign_frame(124), campaign_frame(124, paused=True, revision=10)])
        result = await value.advance_event_boundary(self.step())
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIsNone(result["event_boundary"])
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["after"]["paused"], True)
        self.assertIs(result["actor_transition"]["predecessor_death_proved"], False)
        self.assertEqual([args["step"] for name, args in value.calls if name == "ck3_execute_step"],
                         ["pause-map", "resume-map", "pause-map"])
        self.assertIsNone(value.episode_identity)

    async def test_early_event_never_earns_day_even_if_pause_arrives_at_target(self):
        event = {"instance_id": 7}
        value = self.client([campaign_frame(112, event=event), campaign_frame(124, paused=True, event=event, revision=10)])
        result = await value.advance_event_boundary(self.step())
        self.assertEqual(result["progress_status"], "event_before_target")
        self.assertIs(result["requested_interval_complete"], False)
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertEqual(result["event_boundary"]["date_raw"], 112)
        self.assertEqual(result["selected_event_options"], 0)
        self.assertFalse(any("select" in name for name, _ in value.calls))

    async def test_event_at_target_or_during_pause_retains_actual_full_boundary(self):
        event = {"instance_id": 7}
        for observed in (campaign_frame(124, event=event), campaign_frame(124)):
            with self.subTest(event_before_pause=observed["active_event"] is not None):
                value = self.client([observed, campaign_frame(124, paused=True, event=event, revision=10)])
                result = await value.advance_event_boundary(self.step())
                self.assertIs(result["requested_interval_complete"], True)
                self.assertEqual(result["event_boundary"]["active_event"], event)
                self.assertEqual(result["after"]["active_event"], event)
                self.assertEqual(result["event_resolution"], "typed_query_required")

    async def test_actor_change_is_explicit_once_and_never_death_proof(self):
        frames = [campaign_frame(124, actor=23), campaign_frame(124, paused=True, actor=23, revision=10)]
        value = self.client(frames)
        with self.assertRaisesRegex(RuntimeError, "owner, clock or rejection"):
            await value.advance_event_boundary(self.step())
        value = self.client(frames)
        result = await value.advance_event_boundary(self.step(allow_actor_change=True))
        self.assertEqual(result["actor_transition"], {"allowed": True, "observed": True, "before": 22, "after": 23,
                                                    "predecessor_death_proved": False})
        value = self.client([campaign_frame(112, actor=23), campaign_frame(124, actor=24, revision=10)])
        with self.assertRaises(RuntimeError):
            await value.advance_event_boundary(self.step(allow_actor_change=True))
        for malformed in (1, "true", None):
            value = self.client(frames)
            with self.assertRaises(ValueError):
                await value.advance_event_boundary(self.step(allow_actor_change=malformed))
            self.assertEqual(value.calls, [])

    async def test_malformed_lost_event_owner_or_full_frame_is_rejected(self):
        event = {"instance_id": 7}
        for after_event in (None, {"instance_id": 8}, {"instance_id": True}, {"instance_id": 0}):
            value = self.client([campaign_frame(112, event=event), campaign_frame(112, paused=True, event=after_event, revision=10)])
            with self.subTest(after_event=after_event), self.assertRaises(RuntimeError):
                await value.advance_event_boundary(self.step())
        for field in ("generation", "owner", "ready", "date", "rejection"):
            after = campaign_frame(124, paused=True, revision=10)
            diag = after["diagnostics"]; mailbox = diag["last_heartbeat"]["main_thread_query_mailbox_v1"]
            if field == "generation": diag["hello"]["connection_generation"] = 2
            elif field == "owner": mailbox["owner_tid"] = 34
            elif field == "ready": mailbox["ready"] = False
            elif field == "date": after["date_raw"] = 123
            else: diag["rejected_state_snapshot_count"] = 1
            value = self.client([campaign_frame(124), after])
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                await value.advance_event_boundary(self.step())

    async def test_deadline_manager_cancel_and_rejected_ack_do_not_return_success(self):
        value = self.client([], tick=6)
        with self.assertRaises(TimeoutError):
            await value.advance_event_boundary(self.step())
        self.assertFalse(any(name == "ck3_execute_step" for name, _ in value.calls))
        value = self.client([], done=True)
        with warnings.catch_warnings(record=True) as emitted:
            warnings.simplefilter("always", RuntimeWarning)
            with self.assertRaises(RuntimeError):
                await value.advance_event_boundary(self.step())
            gc.collect()
        self.assertEqual(emitted, [], "The done gate must precede coroutine creation")
        self.assertEqual(value.calls, [])
        value = self.client([], cancel=True)
        with self.assertRaises(asyncio.CancelledError):
            await value.advance_event_boundary(self.step())
        for rejected in ("pause-map", "resume-map"):
            value = self.client([], rejected_step=rejected)
            with self.subTest(rejected=rejected), self.assertRaisesRegex(RuntimeError, "unadmitted"):
                await value.advance_event_boundary(self.step())

    async def test_one_life_still_requires_original_episode_and_does_not_dispatch_campaign(self):
        value = self.client([])
        value.snapshot["episode_projection"] = "one_life"
        with self.assertRaisesRegex(ValueError, "episode anchor"):
            await value.advance_event_boundary(self.step())
        self.assertEqual(value.calls, [])

    async def test_default_normal_day_and_default_event_rejection_are_preserved(self):
        value = self.client([campaign_frame(124), campaign_frame(124, paused=True, revision=10)])
        result = await value.advance({"days": 1, "timeout": 5})
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIsNone(result["event_boundary"])
        with self.assertRaises(RuntimeError):
            value.binding(campaign_frame(124, paused=True, event={"instance_id": 7}))


if __name__ == "__main__":
    unittest.main()

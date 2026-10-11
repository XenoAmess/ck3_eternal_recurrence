"""Portable pre-action readmission tests against actual canonical campaign methods."""
from __future__ import annotations

import asyncio
import ast
import copy
import json
from pathlib import Path
import threading
from types import SimpleNamespace
import unittest

from test_ck3_mod_acceptance_campaign_event import campaign_frame

HOST = Path(__file__).resolve().parents[1] / "ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py"


def rejected_frame():
    return {"snapshot_id": "native:5", "revision": 5, "date_raw": 100, "speed": 3,
            "paused": True, "map_ready": True, "error_type": "ValueError",
            "error": "native played_character stress_points is malformed"}


def paused_start(revision=4, count=0):
    value = campaign_frame(100, paused=True, revision=revision)
    value["speed"] = 3
    value["played_character"]["stress_points"] = 0
    value["diagnostics"]["rejected_state_snapshot_count"] = count
    value["diagnostics"]["last_rejected_state_snapshot"] = rejected_frame() if count else None
    return value


def successor(date, revision, *, paused=False, count=1):
    value = campaign_frame(date, paused=paused, revision=revision)
    value["played_character"]["stress_points"] = 0
    value["diagnostics"]["rejected_state_snapshot_count"] = count
    value["diagnostics"]["last_rejected_state_snapshot"] = rejected_frame() if count else None
    return value


def change(value, path, new):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = new
    return value


class CampaignPreactionTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse(HOST.read_text(encoding="utf-8-sig"))
        cls.definitions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in {
            "_campaign_pending_running_date", "_campaign_pause_pending_ready_successor", "_campaign_pause_frame_rejection_detail", "campaign_pause_frame_binding", "require_campaign_pause_successor", "campaign_event_instance"}]
        client = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "PlanClient")
        cls.method_names = {"advance_event_boundary", "advance_campaign_event_boundary",
                            "set_campaign_speed_one_presubmission_once", "pause_campaign_after_advance", "wait_campaign_running_successor"}
        cls.definitions.extend(n for n in client.body if isinstance(n, ast.AsyncFunctionDef) and n.name in cls.method_names)

    def client(self, recovery=None, *, first=None, readback=None, ack="already_paused", post_count=1,
               running_count=1, timeout=False, done=False, cancel=False, normal=False):
        initial = copy.deepcopy(first if first is not None else paused_start())
        readback = copy.deepcopy(readback if readback is not None else paused_start(count=1))
        count = 0 if normal else 1
        accepted = paused_start(revision=6, count=count)
        observations = [initial] + (list(recovery) if recovery is not None else [paused_start(count=1), accepted])
        if normal:
            observations = [initial]
        observations += [accepted, successor(124, 9, count=0 if normal else running_count),
                         successor(124, 10, paused=True, count=0 if normal else post_count)]
        if timeout:
            observations = [initial] + [paused_start(count=1)] * 70

        class IO:
            def __init__(self):
                self.args = SimpleNamespace(command_timeout=5, poll_interval=.05)
                self.report = {}
                self.tools = {n: {} for n in ("ck3_get_capabilities", "ck3_take_snapshot", "ck3_execute_step",
                                             "ck3_query_current_event_window_context_v1")}
                self.episode_identity = None
                self.managed_done = threading.Event()
                self.clock = 0.0
                self.calls = []
                self.frames = iter(observations)
                self.snapshot = initial
                self.fresh_calls = 0
                self.waits = 0

            async def call(self, name):
                self.clock += .02
                return {"snapshot": True, "action_steps": ["pause-map", "resume-map", "set-speed-1"],
                        "current_event_window_context_v1_query_supported": True,
                        "bridge_capabilities": ["game.command.query-current-event-window-context-v1"]}

            async def invoke(self, name, arguments, *, fresh_revision=True):
                self.clock += .02
                self.calls.append({"tool": name, "arguments": dict(arguments), "fresh_revision": fresh_revision})
                status = ack if len(self.calls) == 1 else "submitted"
                return {"step": arguments["step"], "accepted": True, "status": status}

            async def fresh(self):
                self.clock += .1
                self.fresh_calls += 1
                if self.fresh_calls == 2 and cancel:
                    raise asyncio.CancelledError()
                if self.fresh_calls == 2 and done:
                    self.managed_done.set()
                self.snapshot = copy.deepcopy(next(self.frames))
                return self.snapshot

            async def wait_snapshot(self, expected, timeout):
                self.clock += .02
                self.waits += 1
                if self.waits == 1:
                    self.snapshot = copy.deepcopy(initial if normal else readback)
                else:
                    self.snapshot = successor(100, 7, paused=True, count=count)
                return self.snapshot

            async def sleep(self, seconds):
                self.clock += seconds

        value = IO()
        namespace = {"asyncio": SimpleNamespace(wait_for=asyncio.wait_for, sleep=value.sleep),
                     "json": json, "copy": copy, "now": lambda: "SYNTHETIC_ONLY",
                     "time": SimpleNamespace(monotonic=lambda: value.clock),
                     "CampaignSpeedPreSubmissionRevisionError": type("UnexpectedSpeedRejection", (Exception,), {})}
        exec(compile(ast.fix_missing_locations(ast.Module(body=self.definitions, type_ignores=[])), str(HOST), "exec"), namespace)
        for name in self.method_names:
            setattr(value, name, lambda *args, _name=name, **kwargs: namespace[_name](value, *args, **kwargs))
        return value

    @staticmethod
    def step():
        return {"days": 1, "timeout": 5, "allow_event_boundary": True}

    @staticmethod
    def actions(client):
        return [row["arguments"]["step"] for row in client.calls]

    async def test_only_later_accepted_full_frame_rebinds_then_actual_day_is_proved(self):
        client = self.client()
        result = await client.advance_event_boundary(self.step())
        evidence = client.report["campaign_preaction_readmissions"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["poll_count"], 2)
        self.assertEqual(evidence[0]["initial_binding"]["rejections"], 0)
        self.assertEqual(evidence[0]["observed_rejection_binding"]["rejections"], 1)
        self.assertEqual(evidence[0]["recognized_rejected_frame"], rejected_frame())
        self.assertEqual(evidence[0]["original_strict_error"], "campaign pause readback owner, clock or rejection state changed")
        self.assertEqual(evidence[0]["status"], "ACCEPTED_COMPLETE_PAUSED_START_REBOUND")
        self.assertEqual(evidence[0]["recovered_binding"]["native_revision"], 6)
        self.assertEqual(result["before"]["snapshot_id"], "native:6")
        self.assertEqual(result["before"]["diagnostics"]["rejected_state_snapshot_count"], 1)
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIs(result["after"]["paused"], True)
        self.assertIs(evidence[0]["product_acceptance_proven"], False)
        self.assertEqual(self.actions(client), ["pause-map", "set-speed-1", "resume-map", "pause-map"])
        speed = next(row for row in client.calls if row["arguments"]["step"] == "set-speed-1")
        self.assertEqual(speed["arguments"]["expected_revision"], 6)
        self.assertIs(speed["fresh_revision"], False)

    async def test_unrecognized_rejections_or_submitted_pause_do_not_reanchor(self):
        variants = [
            ("submitted", None, None),
            ("already_paused", paused_start(count=1), paused_start(count=3)),
            ("already_paused", None, change(paused_start(count=1), ("diagnostics", "rejected_state_snapshot_count"), 2)),
        ]
        for path, changed in [
            (("error",), "another decoder error"), (("error_type",), "RuntimeError"),
            (("revision",), 6), (("revision",), True), (("snapshot_id",), "native:6"),
            (("date_raw",), 101), (("speed",), 1), (("paused",), False), (("map_ready",), False),
        ]:
            bad = paused_start(count=1)
            change(bad["diagnostics"]["last_rejected_state_snapshot"], path, changed)
            variants.append(("already_paused", None, bad))
        for ack, first, readback in variants:
            with self.subTest(ack=ack, first=first, readback=readback):
                client = self.client(first=first, readback=readback, ack=ack)
                with self.assertRaises(RuntimeError):
                    await client.advance_event_boundary(self.step())
                self.assertEqual(self.actions(client), ["pause-map"])
                self.assertNotIn("campaign_preaction_readmissions", client.report)

    async def test_recovery_identity_date_rejection_and_complete_frame_remain_strict(self):
        changes = [
            (("diagnostics", "bridge_pid"), 12), (("diagnostics", "connection_generation"), 2),
            (("diagnostics", "pipe_name"), "other-pipe"), (("played_character", "character_id"), 23),
            (("local_player_id",), 2), (("speed",), 2), (("paused",), False), (("date_raw",), 101),
            (("active_event",), {"instance_id": 1}), (("complete_snapshot",), False),
            (("diagnostics", "rejected_state_snapshot_count"), 2),
            (("diagnostics", "last_rejected_state_snapshot", "error"), "changed rejection"),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "owner_tid"), 34),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "ready"), False),
            (("diagnostics", "last_heartbeat", "main_thread_query_mailbox_v1", "owner_verified_pump_epochs"), 3),
        ]
        for path, changed in changes:
            with self.subTest(field=path):
                bad = change(paused_start(revision=6, count=1), path, changed)
                client = self.client([bad])
                with self.assertRaises(RuntimeError):
                    await client.advance_event_boundary(self.step())
                self.assertEqual(self.actions(client), ["pause-map"])
                self.assertEqual(client.report["campaign_preaction_readmissions"][0]["status"],
                                 "FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED")

    async def test_cache_never_earns_admission_and_timeout_done_cancel_never_submit_speed(self):
        for mode in ("timeout", "done", "cancel"):
            with self.subTest(mode=mode):
                client = self.client(**{mode: True})
                expected = asyncio.CancelledError if mode == "cancel" else TimeoutError if mode == "timeout" else RuntimeError
                with self.assertRaises(expected):
                    await client.advance_event_boundary(self.step())
                self.assertEqual(self.actions(client), ["pause-map"])
                evidence = client.report["campaign_preaction_readmissions"][0]
                self.assertEqual(evidence["refresh_attempt_count"], 1)
                self.assertEqual(evidence["status"], "FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED")
                self.assertNotIn("recovered_snapshot_id", evidence)
                self.assertLessEqual(client.clock, 5.2)

    async def test_after_resume_or_postpause_rejection_still_fails_without_second_readmission(self):
        for phase in ("running_count", "post_count"):
            with self.subTest(phase=phase):
                client = self.client(**{phase: 2})
                with self.assertRaisesRegex(RuntimeError, "owner, clock or rejection"):
                    await client.advance_event_boundary(self.step())
                self.assertEqual(len(client.report["campaign_preaction_readmissions"]), 1)
                actions = self.actions(client)
                self.assertEqual(actions.count("set-speed-1"), 1)
                self.assertEqual(actions.count("resume-map"), 1)
                self.assertEqual(actions.count("pause-map"), 1 if phase == "running_count" else 2)

    async def test_original_no_rejection_success_never_uses_readmission(self):
        client = self.client(normal=True)
        result = await client.advance_event_boundary(self.step())
        self.assertIs(result["requested_interval_complete"], True)
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertNotIn("campaign_preaction_readmissions", client.report)
        self.assertEqual(self.actions(client), ["pause-map", "set-speed-1", "resume-map", "pause-map"])


    def nonzero_baseline_client(self, *, count=1, observed_count=None, recovery_count=None,
                                running_count=None, rejected_revision=9, ack="already_paused",
                                observed_changes=()):
        """Use production methods with a later action's cumulative rejection base."""
        observed_count = count + 1 if observed_count is None else observed_count
        recovery_count = observed_count if recovery_count is None else recovery_count
        running_count = observed_count if running_count is None else running_count
        initial = paused_start(revision=8, count=count)
        observed = paused_start(revision=8, count=observed_count)
        rejected = rejected_frame()
        rejected.update(revision=rejected_revision, snapshot_id=f"native:{rejected_revision}")
        observed["diagnostics"]["last_rejected_state_snapshot"] = copy.deepcopy(rejected)
        for path, value in observed_changes:
            change(observed, path, value)

        def frame(date, revision, *, paused, total):
            value = successor(date, revision, paused=paused, count=total)
            value["speed"] = 3 if date == 100 and revision <= 10 else 1
            value["diagnostics"]["last_rejected_state_snapshot"] = copy.deepcopy(rejected)
            return value

        accepted = frame(100, 10, paused=True, total=recovery_count)
        speed = frame(100, 11, paused=True, total=observed_count)
        client = self.client(first=initial, readback=observed, ack=ack)
        client.frames = iter([initial, observed, accepted, accepted,
                             frame(124, 13, paused=False, total=running_count),
                             frame(124, 14, paused=True, total=running_count)])

        async def wait_snapshot(expected, timeout):
            client.clock += .02
            client.waits += 1
            client.snapshot = copy.deepcopy(observed if client.waits == 1 else speed)
            return client.snapshot

        client.wait_snapshot = wait_snapshot
        return client

    async def test_later_action_nonzero_counter_admits_only_new_complete_frame(self):
        client = self.nonzero_baseline_client()
        result = await client.advance_event_boundary(self.step())
        evidence = client.report["campaign_preaction_readmissions"]
        self.assertEqual(len(evidence), 1)
        self.assertEqual(evidence[0]["initial_binding"]["rejections"], 1)
        self.assertEqual(evidence[0]["observed_rejection_binding"]["rejections"], 2)
        self.assertEqual(evidence[0]["poll_count"], 2)
        self.assertEqual(evidence[0]["recognized_rejected_frame"]["revision"], 9)
        self.assertEqual(evidence[0]["recovered_binding"]["native_revision"], 10)
        self.assertEqual(evidence[0]["status"], "ACCEPTED_COMPLETE_PAUSED_START_REBOUND")
        self.assertEqual(result["before"]["snapshot_id"], "native:10")
        self.assertEqual(result["elapsed_hours"], 24)
        self.assertIs(result["requested_interval_complete"], True)
        self.assertIs(evidence[0]["product_acceptance_proven"], False)
        self.assertEqual(self.actions(client), ["pause-map", "set-speed-1", "resume-map", "pause-map"])
        speed = next(row for row in client.calls if row["arguments"]["step"] == "set-speed-1")
        self.assertEqual(speed["arguments"]["expected_revision"], 10)
        self.assertIs(speed["fresh_revision"], False)

    async def test_cumulative_nonzero_base_is_not_reset_or_limited_to_one_process_rejection(self):
        for count in (7, 2**64 - 2):
            with self.subTest(count=count):
                client = self.nonzero_baseline_client(count=count)
                result = await client.advance_event_boundary(self.step())
                evidence = client.report["campaign_preaction_readmissions"][0]
                self.assertEqual(evidence["initial_binding"]["rejections"], count)
                self.assertEqual(evidence["recovered_binding"]["rejections"], count + 1)
                self.assertEqual(evidence["refresh_attempt_count"], 1)
                self.assertEqual(result["elapsed_hours"], 24)

    async def test_nonzero_preflight_multiple_rollback_or_wrong_rejected_revision_never_admits(self):
        for changes in ({"observed_count": 3}, {"observed_count": 0},
                        {"rejected_revision": 10}, {"count": 2**64 - 1}):
            with self.subTest(changes=changes):
                client = self.nonzero_baseline_client(**changes)
                with self.assertRaises(RuntimeError):
                    await client.advance_event_boundary(self.step())
                self.assertEqual(self.actions(client), ["pause-map"])
                self.assertNotIn("campaign_preaction_readmissions", client.report)

    async def test_nonzero_readmission_new_rejection_keeps_original_failure_before_speed(self):
        client = self.nonzero_baseline_client(recovery_count=3)
        with self.assertRaisesRegex(RuntimeError, "owner, clock or rejection"):
            await client.advance_event_boundary(self.step())
        self.assertEqual(self.actions(client), ["pause-map"])
        self.assertEqual(len(client.report["campaign_preaction_readmissions"]), 1)
        self.assertEqual(client.report["campaign_preaction_readmissions"][0]["status"],
                         "FAILED_OR_CANCELLED_ORIGINAL_ERROR_PRESERVED")

    async def test_nonzero_unknown_payload_stale_id_and_original_owner_clock_guards_remain(self):
        variants = [
            {"ack": "submitted"},
            {"observed_changes": [(("diagnostics", "last_rejected_state_snapshot", "error"), "unknown payload")]},
            {"observed_changes": [(("diagnostics", "last_rejected_state_snapshot", "snapshot_id"), "native:5")]},
            {"observed_changes": [(("paused",), False)]},
            {"observed_changes": [(("diagnostics", "bridge_pid"), 12)]},
            {"observed_changes": [(("date_raw",), 101)]},
            {"observed_changes": [(("revision",), 7)]},
            {"observed_changes": [(("native_revision",), 7), (("snapshot_id",), "native:7")]},
        ]
        for changes in variants:
            with self.subTest(changes=changes):
                client = self.nonzero_baseline_client(**changes)
                with self.assertRaises(RuntimeError):
                    await client.advance_event_boundary(self.step())
                self.assertEqual(self.actions(client), ["pause-map"])
                self.assertNotIn("campaign_preaction_readmissions", client.report)

    async def test_nonzero_after_resume_rejection_never_restarts_action(self):
        client = self.nonzero_baseline_client(running_count=3)
        with self.assertRaisesRegex(RuntimeError, "owner, clock or rejection"):
            await client.advance_event_boundary(self.step())
        self.assertEqual(len(client.report["campaign_preaction_readmissions"]), 1)
        self.assertEqual(self.actions(client), ["pause-map", "set-speed-1", "resume-map"])


if __name__ == "__main__":
    unittest.main()

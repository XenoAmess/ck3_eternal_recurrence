from __future__ import annotations

import asyncio
import copy
import importlib.util
import json
from pathlib import Path
import time
import unittest


spec = importlib.util.spec_from_file_location("saved_campaign_retry_host", Path(__file__).with_name("run_ck3_12002_mcp_live.py"))
host = importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)
SHA = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518"
PIPE = "test-saved-campaign-pipe"
EXPECTED = {"actor_character_id": 31254, "date_raw": 53144712}


def snapshot(pump: int) -> dict:
    return {"map_ready": True, "paused": True, "date_raw": EXPECTED["date_raw"],
        "episode_projection": "native_campaign", "active_event": None,
        "played_character": {"character_id": 31254, "alive": True, "source": "native"},
        "local_player_id": 1, "snapshot_id": "native:1", "native_revision": 1, "revision": 2,
        "diagnostics": {"connected": True, "bridge_pid": 901, "connection_generation": 1,
            "hello": {"pid": 901, "connection_generation": 1, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                "expected_ck3_version": "1.20.0.4", "ck3_build_match": True,
                "expected_ck3_sha256": SHA, "capabilities": ["game.state.snapshot"]},
            "last_heartbeat": {"pid": 901, "main_thread_query_mailbox_v1": {
                "ready": True, "stamp_read_success": True, "pump_epochs": pump,
                "owner_verified_pump_epochs": pump, "owner_tid": 42, "current_tid": 42},
                "snapshot_observer_12002": {"read_in_progress": False, "started_ms": 1, "completed_ms": 2}}}}


def root_context() -> dict:
    return {"campaign_root_context_ready": True, "backend_id": "native-headless",
        "queried_snapshot_id": "native:1", "queried_revision": 2, "queried_native_revision": 1,
        "date_raw": EXPECTED["date_raw"], "player_character_id": 31254, "player_character_alive": True,
        "provenance": {"game_version": "1.20.0.4", "executable_sha256": SHA}}


def failure(**changes) -> RuntimeError:
    receipt = {"executor_enter": None, "executor_exception": {"code": 0, "image": "none", "rva": None},
        "executor_finish": None, "executor_typed_result": None, "final_equal": None,
        "final_read": None, "frame_stable": None, "query_type": "campaign", "stage": "wait",
        "typed_result": None, "wait_completed": False, "wait_result": "timeout_cancelled_before_execution"}
    receipt.update(changes)
    return RuntimeError("MCP tool ck3_query_campaign_root_context_v1 returned an error: "
        "Error executing tool ck3_query_campaign_root_context_v1: native gameplay step failed: "
        "application-main typed query failed or its snapshot changed; typed_query_failure_v1=" + json.dumps(receipt))


class Client:
    """Only MCP I/O is substituted; the real host guard and validators run unchanged."""
    def __init__(self, frames, outcomes, report, writes, delay=0):
        self.frames, self.outcomes = frames, outcomes
        self.report, self.writes, self.delay = report, writes, delay
        self.fresh_count, self.query_args, self.submission_pumps = 0, [], []

    async def fresh(self):
        await asyncio.sleep(0)
        frame = self.frames[min(self.fresh_count, len(self.frames)-1)]
        self.fresh_count += 1
        return copy.deepcopy(frame)

    async def call(self, name, arguments=None):
        if name == "ck3_migration_pipe_diagnostics":
            diagnostics = copy.deepcopy(self.frames[0]["diagnostics"])
            diagnostics.update(pipe_name=PIPE, protocol_version=1, transport_fatal_error=None,
                last_error=None, semantic_state_available=True, rejected_state_snapshot_count=0)
            return {"pipe": PIPE, "transport_error": None, "diagnostics": diagnostics}
        if name != "ck3_query_campaign_root_context_v1":
            raise AssertionError(name)
        # This must already be durable before the simulated asynchronous response.
        attempt = self.writes[-1]["saved_campaign_restore"]["campaign_root_query_attempts"][-1]
        if attempt["status"] != "CALL_PENDING" or attempt["expected_revision"] != arguments["expected_revision"]:
            raise AssertionError("pre-submit evidence was not written")
        self.query_args.append(arguments)
        self.submission_pumps.append(attempt["submitted_frame"]["pump_epoch"])
        if self.delay:
            await asyncio.sleep(self.delay)
        outcome = self.outcomes[min(len(self.query_args)-1, len(self.outcomes)-1)]
        if isinstance(outcome, BaseException):
            raise outcome
        return copy.deepcopy(outcome)


class SavedCampaignOwnerQueryRetryTests(unittest.IsolatedAsyncioTestCase):
    def client(self, pumps=(2, 4, 4, 6, 8), outcomes=None, frames=None, delay=0):
        report = {"pipe": PIPE, "saved_campaign_launch": {
            "status": "ACTUAL_SINGLE_CLI_RESTORE_LAUNCHED", "argv_admitted": True, "ck3_pid": 901}}
        writes = []
        client = Client(frames or [snapshot(p) for p in pumps], outcomes or [failure(), root_context()], report, writes, delay)
        return client, report, lambda: writes.append(copy.deepcopy(report))

    async def run_guard(self, client, report, write, duration=2.0):
        # The mandatory pre-existing deadline takes precedence over this larger timeout.
        return await host.wait_for_saved_campaign(client, EXPECTED, report=report, write=write,
            timeout=90, readiness_deadline=time.monotonic()+duration, managed_done=None, poll_interval=.001)

    async def test_cancelled_unentered_query_needs_fresh_stable_owner_pump_and_full_root(self):
        client, report, write = self.client()
        state = await self.run_guard(client, report, write)
        self.assertEqual(client.submission_pumps, [4, 6])
        self.assertEqual(client.query_args, [{"expected_revision": 2}]*2)
        self.assertTrue(state["binding"]["saved_campaign_identity_proven"])
        self.assertFalse(report["readiness_guard"]["product_acceptance_proven"])
        first, second = state["campaign_root_query_attempts"]
        self.assertEqual(first["status"], "FAILED")
        self.assertEqual(first["error"], str(failure()))
        self.assertEqual(first["submitted_frame"]["pump_epoch"], 4)
        self.assertTrue(second["retry_after_cancelled_wait"])
        self.assertEqual(second["status"], "BOUND")

    async def test_stale_pump_cannot_retry_or_extend_original_deadline(self):
        client, report, write = self.client(pumps=(2, 4, 4))
        with self.assertRaises(TimeoutError):
            await self.run_guard(client, report, write, .02)
        self.assertEqual(len(client.query_args), 1)
        self.assertNotIn("readiness", report)

    async def test_running_unknown_malformed_entered_or_incomplete_fail_closed(self):
        missing = str(failure()).replace('"executor_finish": null, ', '')
        errors = [failure(wait_result="timeout_executor_already_running"), failure(executor_enter=0),
            failure(query_type="event"), failure(wait_completed=True), RuntimeError(missing),
            failure(executor_exception={"code": False, "image": "none", "rva": None}),
            RuntimeError("unclassified MCP failure"), RuntimeError(str(failure())+" trailing")]
        for error in errors:
            with self.subTest(error=str(error)):
                client, report, write = self.client(outcomes=[error])
                with self.assertRaises(RuntimeError) as caught:
                    await self.run_guard(client, report, write)
                self.assertIs(caught.exception, error)
                self.assertEqual(len(client.query_args), 1)
                self.assertIsNone(report["saved_campaign_restore"]["campaign_root_query_attempts"][0]["typed_query_failure"])

    async def test_second_cancelled_wait_is_terminal_and_both_errors_remain(self):
        client, report, write = self.client(outcomes=[failure(), failure()])
        with self.assertRaises(RuntimeError):
            await self.run_guard(client, report, write)
        self.assertEqual(len(client.query_args), 2)
        attempts = report["saved_campaign_restore"]["campaign_root_query_attempts"]
        self.assertEqual([a["status"] for a in attempts], ["FAILED", "FAILED"])
        self.assertEqual([a["error"] for a in attempts], [str(failure())]*2)
        self.assertNotIn("readiness_guard", report)

    async def test_changed_process_generation_actor_date_or_owner_cannot_retry(self):
        for field in ("pid", "generation", "actor", "date", "owner"):
            with self.subTest(field=field):
                frames = [snapshot(p) for p in (2, 4, 6, 8, 10)]
                for frame in frames[2:]:
                    if field == "pid": frame["diagnostics"]["bridge_pid"] = 902
                    if field == "generation": frame["diagnostics"]["connection_generation"] = 2
                    if field == "actor": frame["played_character"]["character_id"] = 65865
                    if field == "date": frame["date_raw"] += 1
                    if field == "owner":
                        frame["diagnostics"]["last_heartbeat"]["main_thread_query_mailbox_v1"].update(owner_tid=43, current_tid=43)
                client, report, write = self.client(frames=frames)
                with self.assertRaises((ValueError, RuntimeError, TimeoutError)):
                    await self.run_guard(client, report, write, .02)
                self.assertEqual(len(client.query_args), 1)
                self.assertNotIn("readiness", report)

    async def test_recovery_does_not_relax_complete_native_root_identity(self):
        root = root_context()
        root["player_character_id"] = 65865
        client, report, write = self.client(outcomes=[failure(), root])
        with self.assertRaisesRegex(ValueError, "living actor"):
            await self.run_guard(client, report, write)
        self.assertEqual(len(client.query_args), 2)
        self.assertNotIn("readiness", report)

    async def test_inflight_query_is_bounded_by_original_deadline_without_retry(self):
        client, report, write = self.client(outcomes=[root_context()], delay=.08)
        with self.assertRaises(TimeoutError):
            await self.run_guard(client, report, write, .02)
        self.assertEqual(len(client.query_args), 1)
        self.assertIsNone(report["saved_campaign_restore"]["campaign_root_query_attempts"][0]["typed_query_failure"])

    async def test_first_query_success_keeps_existing_full_binding(self):
        client, report, write = self.client(pumps=(2, 4, 6), outcomes=[root_context()])
        state = await self.run_guard(client, report, write)
        self.assertEqual(client.submission_pumps, [4])
        self.assertTrue(state["actual_current_actor_bound"])
        self.assertNotIn("cancelled_campaign_wait_recovery", state)


if __name__ == "__main__":
    unittest.main()

"""Focused no-game tests for the bounded H3911 cold-load gate."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from h3911_readiness_gate import (
    probe_postread, remaining_snapshot_timeout, require_absent_prelaunch_log,
    wait_for_postread_grace,
)
import run_r0321_h3911_receiver_readonly as receiver


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    async def sleep(self, seconds: float) -> None:
        self.value += seconds


class ReadinessGateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "attempt-3-h3911-readonly-no-launch"
        self.log = self.root / "state" / "profile" / "logs" / "debug.log"
        self.log.parent.mkdir(parents=True)
        self.launch = datetime.now(timezone.utc)

    def write_log(self, text: str) -> None:
        self.log.write_text(text, encoding="utf-8")
        fresh = self.launch.timestamp() + 1
        os.utime(self.log, (fresh, fresh))

    async def test_missing_log_times_out_within_original_deadline(self) -> None:
        clock = FakeClock()
        probes = []
        with self.assertRaisesRegex(TimeoutError, "postread log gate timed out"):
            await wait_for_postread_grace(
                self.root, self.log, self.launch, deadline=12, clock=clock,
                sleep=clock.sleep, record_probe=probes.append,
            )
        self.assertEqual(clock.value, 12)
        self.assertTrue(all(row["stage"] == "missing" for row in probes))

    async def test_postread_then_vassals_observe_full_grace(self) -> None:
        self.write_log("[00:05:07] CGameState::InitPostRead\n")
        clock = FakeClock()
        probes = []

        async def advance(seconds: float) -> None:
            await clock.sleep(seconds)
            if clock.value == 10:
                self.write_log("[00:05:07] CGameState::InitPostRead\n"
                               "[00:05:12] Setup powerful vassals among [36065]\n")

        result = await wait_for_postread_grace(
            self.root, self.log, self.launch, deadline=1800,
            clock=clock, sleep=advance, record_probe=probes.append,
        )
        self.assertEqual(clock.value, 70)
        self.assertEqual(result["stage"], "postread_vassals_seen")
        self.assertEqual(result["grace_seconds"], 60)
        self.assertIn("postread_started", [row["stage"] for row in probes])
        self.assertEqual(probes[-1]["stage"], "postread_vassals_seen")

    async def test_grace_cannot_expand_deadline(self) -> None:
        self.write_log("CGameState::InitPostRead\nSetup powerful vassals among [36065]\n")
        clock = FakeClock()
        with self.assertRaises(TimeoutError):
            await wait_for_postread_grace(
                self.root, self.log, self.launch, deadline=30,
                clock=clock, sleep=clock.sleep,
            )
        self.assertEqual(clock.value, 30)

    async def test_prior_attempt_log_is_rejected(self) -> None:
        prior = Path(self.temp.name) / "attempt-2-h3911-readonly-no-launch"
        old_log = prior / "state" / "profile" / "logs" / "debug.log"
        old_log.parent.mkdir(parents=True)
        old_log.write_text("CGameState::InitPostRead\nSetup powerful vassals among\n")
        with self.assertRaisesRegex(ValueError, "outside this exact attempt"):
            probe_postread(self.root, old_log, self.launch)

    async def test_prelaunch_log_must_be_absent(self) -> None:
        self.assertFalse(require_absent_prelaunch_log(self.root, self.log)["exists_before_launch"])
        self.write_log("CGameState::InitPostRead\nSetup powerful vassals among\n")
        with self.assertRaisesRegex(RuntimeError, "already has a debug.log"):
            require_absent_prelaunch_log(self.root, self.log)

    async def test_marker_regression_during_grace_fails_closed(self) -> None:
        self.write_log("CGameState::InitPostRead\nSetup powerful vassals among\n")
        clock = FakeClock()

        async def truncate(seconds: float) -> None:
            await clock.sleep(seconds)
            if clock.value == 5:
                self.write_log("CGameState::InitPostRead\n")

        with self.assertRaisesRegex(RuntimeError, "regressed or was replaced"):
            await wait_for_postread_grace(
                self.root, self.log, self.launch, deadline=1800,
                clock=clock, sleep=truncate,
            )

    async def test_log_replacement_during_grace_fails_closed(self) -> None:
        self.write_log("CGameState::InitPostRead\nSetup powerful vassals among\n")
        clock = FakeClock()

        async def replace(seconds: float) -> None:
            await clock.sleep(seconds)
            if clock.value == 5:
                self.log.unlink()
                self.write_log("CGameState::InitPostRead\nSetup powerful vassals among\n")

        with self.assertRaisesRegex(RuntimeError, "regressed or was replaced"):
            await wait_for_postread_grace(
                self.root, self.log, self.launch, deadline=1800,
                clock=clock, sleep=replace,
            )

    async def test_probe_return_cannot_cross_deadline(self) -> None:
        values = iter((0.0, 12.0))
        async def no_sleep(_seconds: float) -> None:
            self.fail("gate slept after deadline")
        with self.assertRaisesRegex(TimeoutError, "after probe"):
            await wait_for_postread_grace(
                self.root, self.log, self.launch, deadline=10,
                clock=lambda: next(values), sleep=no_sleep,
            )

    async def test_single_snapshot_cannot_extend_readiness(self) -> None:
        self.assertAlmostEqual(remaining_snapshot_timeout(1800, 1799.5, 120), 0.5)
        with self.assertRaises(TimeoutError):
            remaining_snapshot_timeout(1800, 1800, 120)

    async def test_lost_screen_resource_rejects_synchronous_submission_gate(self) -> None:
        payload = {"ok": True, "tasks": [{"task_id": "this-attempt", "state": "running",
                                          "resources": [], "stale": False}]}
        fake = SimpleNamespace(stdout=json.dumps(payload).encode("utf-8"))
        with patch.object(receiver.subprocess, "run", return_value=fake):
            with self.assertRaisesRegex(RuntimeError, "exclusive live CK3 screen lease absent"):
                receiver.screen_lease("this-attempt")

    def test_source_strength_rows_are_three_exact_war_participants(self) -> None:
        driver = receiver.SOURCE / "R0321-H3911-source-driver-state.json"
        source_rows = json.loads(driver.read_text(encoding="utf-8"))["command_history"]
        result = source_rows[3913]["result"]
        rows = result["army_strengths"]
        self.assertEqual(receiver.require_h3911_strength_rows(rows), rows)
        missing_war = [dict(row) for row in rows]
        missing_war[0]["war_ids"] = []
        with self.assertRaisesRegex(RuntimeError, "WarID differs"):
            receiver.require_h3911_strength_rows(missing_war)
        with self.assertRaisesRegex(RuntimeError, "three-army strength roster missing"):
            receiver.require_h3911_strength_rows(rows[:2])
        frame = {"snapshot_id": result["queried_snapshot_id"],
                 "revision": result["queried_revision"],
                 "native_revision": result["queried_native_revision"],
                 "episode_run_id": receiver.EPISODE,
                 "connection_generation": source_rows[3915]["result"]["queried_connection_generation"]}
        receiver.require_query_result(result, receiver.STRENGTH_QUERY, frame)
        wrong_revision = dict(frame, revision=frame["revision"] + 1)
        with self.assertRaisesRegex(RuntimeError, "queried_revision differs"):
            receiver.require_query_result(result, receiver.STRENGTH_QUERY, wrong_revision)
        missing_revision = dict(result)
        missing_revision.pop("queried_revision")
        with self.assertRaisesRegex(RuntimeError, "queried_revision differs"):
            receiver.require_query_result(missing_revision, receiver.STRENGTH_QUERY, frame)

    async def test_old_same_path_bytes_cannot_unlock_gate(self) -> None:
        self.write_log("CGameState::InitPostRead\nSetup powerful vassals among\n")
        old = self.launch.timestamp() - 100
        os.utime(self.log, (old, old))
        self.assertEqual(probe_postread(self.root, self.log, self.launch)["stage"],
                         "stale_before_this_launch")
        clock = FakeClock()
        with self.assertRaises(TimeoutError):
            await wait_for_postread_grace(
                self.root, self.log, self.launch, deadline=10,
                clock=clock, sleep=clock.sleep,
            )
        self.assertEqual(clock.value, 10)


if __name__ == "__main__":
    unittest.main()

"""Focused no-game tests for the bounded H3911 cold-load gate."""

from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import tempfile
import unittest

from h3911_readiness_gate import probe_postread, wait_for_postread_grace


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

"""Offline tests for the optional H3937 cold-load diagnostic."""

from __future__ import annotations

import inspect
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.h3937_cold_load_observer import ColdLoadObserver  # noqa: E402
from xar_autoplayer.h3937_combined_paused_war_scope_run import (  # noqa: E402
    _ColdLoadProgressWatchdog,
    collect_h3937_combined_paused_war_scope_once,
)
from xar_autoplayer import h3937_combined_paused_war_scope_run as outer  # noqa: E402


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class FakeCapture:
    def __init__(self, *, running: bool = False) -> None:
        self.running = running
        self.killed = False

    def poll(self) -> int | None:
        return None if self.running else (-9 if self.killed else 0)

    def kill(self) -> None:
        self.killed = True
        self.running = False

    def wait(self, *, timeout: int) -> int:
        del timeout
        return self.poll() or 0


def capabilities(pid: int = 77) -> dict[str, object]:
    return {"diagnostics": {"bridge_pid": pid}}


def counters(pid: int, executable: Path) -> dict[str, object]:
    return {
        "pid": pid, "executable": str(executable),
        "creation_time_100ns": 12345,
        "cpu_kernel_100ns": 100, "cpu_user_100ns": 200,
        "read_ops": 1, "write_ops": 2,
        "read_bytes": 3, "write_bytes": 4,
    }


class ColdLoadObserverTests(unittest.TestCase):
    def make_observer(self, root: Path, *, clock: FakeClock,
                      lease=None, probe=counters, popen=None) -> ColdLoadObserver:
        return ColdLoadObserver(
            root / "cold-load-observation", Path("C:/game/ck3.exe"),
            lease or (lambda: None), clock=clock, process_probe=probe,
            window_probe=lambda pid: {"visible_window_count": 1,
                                      "windows": [{"pid": pid, "wm_null_responded": True}]},
            popen=popen or (lambda *args, **kwargs: FakeCapture()),
        )

    def test_default_off_and_successful_bounded_png(self) -> None:
        self.assertIsNone(inspect.signature(
            collect_h3937_combined_paused_war_scope_once
        ).parameters["cold_load_observation_dir"].default)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            clock = FakeClock()
            spawned = []

            def spawn(argv, **kwargs):
                del kwargs
                Image.new("RGB", (2, 2), "red").save(argv[-2], format="PNG")
                spawned.append(argv[-2])
                return FakeCapture()

            observer = self.make_observer(root, clock=clock, popen=spawn)
            self.assertIsNone(observer.tick(capabilities()))
            self.assertEqual(len(spawned), 1)
            clock.now = 1
            self.assertIsNone(observer.tick(capabilities()))
            report = observer.report()
            self.assertEqual(report["sample_count"], 1)
            self.assertEqual(report["frame_count"], 1)
            self.assertEqual(report["diagnostic_status"], "OBSERVED_UNREVIEWED")
            self.assertEqual(report["process_samples"], 1)
            self.assertEqual(report["window_samples"], 1)
            receipt = root / "cold-load-observation" / "frame-0000.json"
            self.assertIn("CAPTURED_UNREVIEWED", receipt.read_text(encoding="utf-8"))
            self.assertTrue((receipt.parent / "frame-0000.png").is_file())
            self.assertFalse((receipt.parent / "frame-0000.pending.png").exists())
            clock.now = 21
            observer.tick(capabilities())
            self.assertEqual(observer.report()["sample_count"], 2)
            self.assertEqual(len(spawned), 1)
            observer.close()
            self.assertTrue(observer.report()["closed"])

    def test_timeout_preserves_zero_byte_partial(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            clock = FakeClock()
            helper = FakeCapture(running=True)

            def spawn(argv, **kwargs):
                del kwargs
                Path(argv[-2]).touch(exist_ok=False)
                return helper

            observer = self.make_observer(root, clock=clock, popen=spawn)
            observer.tick(capabilities())
            clock.now = 13
            observer.tick(capabilities())
            self.assertTrue(helper.killed)
            partial = observer.output_dir / "frame-0000.pending.png"
            self.assertEqual(partial.stat().st_size, 0)
            receipt = (observer.output_dir / "frame-0000.json").read_text(encoding="utf-8")
            self.assertIn("RED_CAPTURE_FAILED", receipt)
            self.assertIn("capture helper timed out", receipt)
            self.assertIn('"capture_helper_alive": false', receipt)
            self.assertFalse((observer.output_dir / "frame-0000.png").exists())
            self.assertEqual(observer.report()["diagnostic_status"],
                             "RED_CAPTURE_UNAVAILABLE")
            observer.close()

    def test_changed_creation_time_and_lost_lease_refuse_capture(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            clock = FakeClock()
            spawned = []
            calls = 0

            def process(pid, executable):
                nonlocal calls
                calls += 1
                row = counters(pid, executable)
                if calls > 1:
                    row["creation_time_100ns"] = 54321
                return row

            def spawn(argv, **kwargs):
                del kwargs
                spawned.append(argv)
                return FakeCapture()

            observer = self.make_observer(root, clock=clock, probe=process, popen=spawn)
            observer.tick(capabilities())
            clock.now = 21
            self.assertIn("creation time changed", observer.tick(capabilities()))
            self.assertEqual(len(spawned), 1)
            observer.close()
        with tempfile.TemporaryDirectory() as temp:
            clock = FakeClock()

            def deny():
                raise ValueError("not owner")

            observer = self.make_observer(Path(temp), clock=clock, lease=deny,
                                          popen=lambda *args, **kwargs: self.fail(
                                              "capture helper started without lease"))
            self.assertIn("screen lease lost", observer.tick(capabilities()))
            self.assertEqual(observer.report()["frame_count"], 0)
            self.assertEqual(observer.report()["diagnostic_status"], "RED_FATAL")
            observer.close()

    def test_watchdog_propagates_lease_loss_and_bad_path_refuses_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            clock = FakeClock()

            def deny():
                raise ValueError("not owner")

            observer = self.make_observer(Path(temp), clock=clock, lease=deny)
            watchdog = _ColdLoadProgressWatchdog(Path(temp) / "shader", observer=observer)
            self.assertIn("screen lease lost", watchdog(capabilities()))
            observer.close()
            with patch.object(outer, "H3937_COMBINED_OUTER_LIVE_AUTHORIZED", True):
                with self.assertRaisesRegex(outer.AgentError, "fresh output and screen lease"):
                    outer.collect_h3937_combined_paused_war_scope_once(
                        object(), ownership_round_id="R999",
                        readiness_stall_watchdog=True,
                        readiness_timeout_screenshot_path=Path(temp) / "timeout.png",
                        readiness_timeout_screen_lease_check=lambda: None,
                        cold_load_observation_dir=Path(temp) / "different-dir",
                    )

    def test_completed_frame_is_rejected_if_lease_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            clock = FakeClock()
            lease_reads = 0

            def lease():
                nonlocal lease_reads
                lease_reads += 1
                if lease_reads > 1:
                    raise ValueError("lease changed")

            def spawn(argv, **kwargs):
                del kwargs
                Image.new("RGB", (2, 2), "blue").save(argv[-2], format="PNG")
                return FakeCapture()

            observer = self.make_observer(Path(temp), clock=clock, lease=lease,
                                          popen=spawn)
            observer.tick(capabilities())
            clock.now = 1
            self.assertIn("screen lease lost during capture", observer.tick(capabilities()))
            self.assertTrue((observer.output_dir / "frame-0000.pending.png").exists())
            self.assertFalse((observer.output_dir / "frame-0000.png").exists())
            self.assertIn("RED_CAPTURE_FAILED", (
                observer.output_dir / "frame-0000.json").read_text(encoding="utf-8"))
            observer.close()

    def test_executable_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            clock = FakeClock()

            def wrong_process(pid, executable):
                del pid, executable
                raise ValueError("CK3 PID executable identity mismatch")

            observer = self.make_observer(Path(temp), clock=clock,
                                          probe=wrong_process,
                                          popen=lambda *args, **kwargs: self.fail(
                                              "capture helper started for wrong executable"))
            self.assertEqual(observer.tick(capabilities()),
                             "CK3 executable identity mismatch")
            self.assertEqual(observer.report()["frame_count"], 0)
            observer.close()

    def test_frame_count_is_hard_bounded_and_spawn_failure_has_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            clock = FakeClock()
            launches = 0

            def spawn(argv, **kwargs):
                nonlocal launches
                del kwargs
                launches += 1
                Image.new("RGB", (1, 1), "green").save(argv[-2], format="PNG")
                return FakeCapture()

            observer = self.make_observer(Path(temp), clock=clock, popen=spawn)
            for index in range(16):
                clock.now = index * 120
                observer.tick(capabilities())
                clock.now += 1
                observer.tick(capabilities())
            self.assertEqual(launches, 15)
            self.assertEqual(observer.report()["frame_count"], 15)
            observer.close()
        with tempfile.TemporaryDirectory() as temp:
            clock = FakeClock()

            def fail_spawn(argv, **kwargs):
                del argv, kwargs
                raise OSError("synthetic spawn failure")

            observer = self.make_observer(Path(temp), clock=clock,
                                          popen=fail_spawn)
            self.assertIsNone(observer.tick(capabilities()))
            self.assertEqual(observer.report()["frame_count"], 1)
            self.assertIn("RED_CAPTURE_START", (
                observer.output_dir / "frame-0000.json").read_text(encoding="utf-8"))
            observer.close()


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.startup_slot0_probe import (  # noqa: E402
    STARTUP_SLOT0_GRAPHICS_GLOBAL_RVA,
    STARTUP_SLOT0_MANAGER_OFFSET,
    STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS,
    STARTUP_SLOT0_ROOT_GLOBAL_RVA,
    StartupSlot0ProbeController,
    StartupSlot0ProbePlan,
    StartupSlot0ModuleDiscoveryError,
    _retry_module_discovery,
    prepare_startup_slot0_probe,
)


class _Clock:
    def __init__(self) -> None:
        self.value = 100.0

    def monotonic(self) -> float:
        return self.value

    def sleep(self, seconds: float) -> None:
        self.value += seconds

    def wall(self) -> str:
        return f"clock-{self.value:.3f}"


class _Reader:
    def __init__(
        self,
        executable: Path,
        cycles: list[
            tuple[
                int | None,
                int | BaseException,
                int | BaseException,
                int,
            ]
        ],
    ) -> None:
        self.image_path = executable
        self.module_base = 0x00007FF700000000
        self._cycles = cycles
        self._cycle = -1
        self.closed = False
        self.addresses: list[int] = []

    def exit_code(self) -> int | None:
        self._cycle += 1
        return self._cycles[self._cycle][0]

    def read_pointer(self, address: int) -> int:
        self.addresses.append(address)
        _exit_code, graphics_global, manager, slot0 = self._cycles[self._cycle]
        root_address = self.module_base + STARTUP_SLOT0_ROOT_GLOBAL_RVA
        graphics_address = (
            self.module_base + STARTUP_SLOT0_GRAPHICS_GLOBAL_RVA
        )
        if address == graphics_address:
            if isinstance(graphics_global, BaseException):
                raise graphics_global
            return graphics_global
        if address == root_address:
            if isinstance(manager, BaseException):
                raise manager
            return manager
        if isinstance(manager, int) and address == manager + STARTUP_SLOT0_MANAGER_OFFSET:
            return slot0
        raise AssertionError(f"unexpected read address: {address:#x}")

    def close(self) -> None:
        self.closed = True


def _plan(root: Path) -> StartupSlot0ProbePlan:
    executable = root / "ck3.exe"
    executable.write_bytes(b"offline exact fixture")
    return StartupSlot0ProbePlan(
        game_exe=executable.resolve(),
        output_path=(root / "slot0.json").resolve(),
        executable_sha256="A" * 64,
        poll_interval_seconds=0.01,
        max_duration_seconds=1.0,
    )


class StartupSlot0AdmissionTests(unittest.TestCase):
    def test_exact_build_gate_and_new_output_are_prelaunch_requirements(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-admission-") as temporary:
            root = Path(temporary)
            executable = root / "ck3.exe"
            executable.write_bytes(b"fixture exact executable")
            output = root / "probe.json"
            digest = hashlib.sha256(executable.read_bytes()).hexdigest().upper()
            with mock.patch(
                "xar_autoplayer.startup_slot0_probe.EXPECTED_CK3_EXE_SHA256",
                digest,
            ):
                plan = prepare_startup_slot0_probe(executable, output)
                self.assertEqual(plan.executable_sha256, digest)
                output.write_text("occupied", encoding="utf-8")
                with self.assertRaisesRegex(AgentError, "output must be new"):
                    prepare_startup_slot0_probe(executable, output)

            output.unlink()
            with self.assertRaisesRegex(AgentError, "exact-build gate failed"):
                prepare_startup_slot0_probe(executable, output)


class StartupSlot0ModuleDiscoveryTests(unittest.TestCase):
    @staticmethod
    def _partial_copy() -> OSError:
        error = OSError(299, "partial copy")
        error.winerror = 299
        return error

    def test_partial_copy_retries_then_records_success_timing(self) -> None:
        clock = _Clock()
        attempts = 0

        def query() -> int:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise self._partial_copy()
            return 0x00007FF700000000

        result = _retry_module_discovery(
            query,
            lambda: None,
            timeout_seconds=0.1,
            poll_interval_seconds=0.005,
            sleeper=clock.sleep,
            monotonic=clock.monotonic,
        )

        self.assertEqual(
            STARTUP_SLOT0_MODULE_DISCOVERY_RETRY_WINERRORS, {24, 299}
        )
        self.assertEqual(result.module_base, 0x00007FF700000000)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(result.transient_error_count, 1)
        self.assertEqual(result.elapsed_seconds, 0.005)

    def test_persistent_partial_copy_stops_at_short_timeout(self) -> None:
        clock = _Clock()
        with self.assertRaises(StartupSlot0ModuleDiscoveryError) as raised:
            _retry_module_discovery(
                lambda: (_ for _ in ()).throw(self._partial_copy()),
                lambda: None,
                timeout_seconds=0.012,
                poll_interval_seconds=0.005,
                sleeper=clock.sleep,
                monotonic=clock.monotonic,
            )

        error = raised.exception
        self.assertEqual(error.reason, "timeout")
        self.assertEqual(error.attempts, 3)
        self.assertEqual(error.transient_error_count, 3)
        self.assertEqual(error.elapsed_seconds, 0.012)
        self.assertEqual(error.winerror, 299)

    def test_non_transient_module_error_is_not_retried(self) -> None:
        attempts = 0

        def query() -> int:
            nonlocal attempts
            attempts += 1
            error = OSError(5, "access denied")
            error.winerror = 5
            raise error

        with self.assertRaises(StartupSlot0ModuleDiscoveryError) as raised:
            _retry_module_discovery(query, lambda: None)

        self.assertEqual(attempts, 1)
        self.assertEqual(raised.exception.reason, "non_transient_error")
        self.assertEqual(raised.exception.transient_error_count, 0)
        self.assertEqual(raised.exception.winerror, 5)

    def test_persistent_partial_copy_process_exit_is_durable_red(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-module-exit-") as temporary:
            root = Path(temporary)
            plan = _plan(root)
            clock = _Clock()
            exit_codes = iter((None, None, 0xC0000005))

            def factory(_pid: int, _executable: Path) -> _Reader:
                _retry_module_discovery(
                    lambda: (_ for _ in ()).throw(self._partial_copy()),
                    lambda: next(exit_codes),
                    timeout_seconds=0.1,
                    poll_interval_seconds=0.005,
                    sleeper=clock.sleep,
                    monotonic=clock.monotonic,
                )
                raise AssertionError("persistent partial copy unexpectedly recovered")

            controller = StartupSlot0ProbeController(
                plan=plan,
                pid=4199,
                launch_role="frontend_warmup",
                timeline_origin_monotonic=clock.monotonic(),
                timeline_origin_at="origin",
                reader_factory=factory,
                sleeper=clock.sleep,
                monotonic=clock.monotonic,
                wall_clock=clock.wall,
            )
            controller.start()
            report = controller.finish()

        self.assertFalse(report["capture_ok"])
        self.assertEqual(report["status"], "module_discovery_process_exit")
        self.assertEqual(report["module_discovery"]["attempts"], 2)
        self.assertEqual(
            report["module_discovery"]["transient_error_count"], 2
        )
        self.assertEqual(
            report["process_exit"]["exit_code"], 0xC0000005
        )
        self.assertEqual(report["errors"][0]["stage"], "module_discovery")
        self.assertEqual(report["errors"][0]["winerror"], 299)


class StartupSlot0CaptureTests(unittest.TestCase):
    def test_records_both_first_nonzero_edges_and_process_exit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-capture-") as temporary:
            root = Path(temporary)
            plan = _plan(root)
            clock = _Clock()
            reader = _Reader(
                plan.game_exe,
                [
                    (None, 0, 0, 0),
                    (
                        None,
                        0x0000040000000000,
                        0x0000020000000000,
                        0,
                    ),
                    (
                        None,
                        0x0000040000000000,
                        0x0000020000000000,
                        0x0000030000000000,
                    ),
                    (0xC0000005, 0, 0, 0),
                ],
            )
            controller = StartupSlot0ProbeController(
                plan=plan,
                pid=4242,
                launch_role="frontend_warmup",
                timeline_origin_monotonic=clock.monotonic(),
                timeline_origin_at="origin",
                reader_factory=lambda _pid, _exe: reader,
                sleeper=clock.sleep,
                monotonic=clock.monotonic,
                wall_clock=clock.wall,
            )
            controller.start()
            report = controller.finish()

        self.assertTrue(report["capture_ok"])
        self.assertEqual(report["status"], "process_exit_observed")
        self.assertEqual(report["sample_count"], 3)
        self.assertEqual(report["successful_graphics_global_reads"], 3)
        self.assertEqual(
            report["first_graphics_global_nonzero"]["value"],
            "0x0000040000000000",
        )
        self.assertEqual(
            report["last_graphics_global"], "0x0000040000000000"
        )
        self.assertEqual(
            report["first_manager_nonzero"]["value"], "0x0000020000000000"
        )
        self.assertEqual(
            report["first_slot0_nonzero"]["value"], "0x0000030000000000"
        )
        self.assertEqual(report["process_exit"]["exit_code"], 0xC0000005)
        self.assertFalse(report["gameplay_functionality_claimed"])
        self.assertFalse(report["map_ready_claimed"])
        self.assertTrue(reader.closed)

    def test_read_error_is_durable_and_capture_remains_red(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-error-") as temporary:
            root = Path(temporary)
            plan = _plan(root)
            clock = _Clock()
            denied = OSError(5, "access denied")
            denied.winerror = 5
            reader = _Reader(
                plan.game_exe,
                [
                    (None, 0, denied, 0),
                    (None, 0, 0, 0),
                    (1, 0, 0, 0),
                ],
            )
            controller = StartupSlot0ProbeController(
                plan=plan,
                pid=4343,
                launch_role="initial",
                timeline_origin_monotonic=clock.monotonic(),
                timeline_origin_at="origin",
                reader_factory=lambda _pid, _exe: reader,
                sleeper=clock.sleep,
                monotonic=clock.monotonic,
                wall_clock=clock.wall,
            )
            controller.start()
            report = controller.finish()

        self.assertFalse(report["capture_ok"])
        self.assertEqual(report["status"], "process_exit_observed")
        self.assertEqual(report["errors"][0]["stage"], "read_manager_global")
        self.assertEqual(report["errors"][0]["winerror"], 5)
        self.assertEqual(report["successful_root_reads"], 1)

    def test_graphics_global_read_error_uses_the_same_red_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-graphics-") as temporary:
            root = Path(temporary)
            plan = _plan(root)
            clock = _Clock()
            failure = OSError(299, "partial copy")
            failure.winerror = 299
            reader = _Reader(
                plan.game_exe,
                [
                    (None, failure, 0, 0),
                    (None, 0x0000040000000000, 0, 0),
                    (0, 0, 0, 0),
                ],
            )
            controller = StartupSlot0ProbeController(
                plan=plan,
                pid=4399,
                launch_role="initial",
                timeline_origin_monotonic=clock.monotonic(),
                timeline_origin_at="origin",
                reader_factory=lambda _pid, _exe: reader,
                sleeper=clock.sleep,
                monotonic=clock.monotonic,
                wall_clock=clock.wall,
            )
            controller.start()
            report = controller.finish()

        self.assertFalse(report["capture_ok"])
        self.assertEqual(report["errors"][0]["stage"], "read_graphics_global")
        self.assertEqual(report["errors"][0]["winerror"], 299)
        self.assertEqual(report["successful_graphics_global_reads"], 1)
        self.assertEqual(
            report["first_graphics_global_nonzero"]["value"],
            "0x0000040000000000",
        )

    def test_exit_before_first_read_cannot_claim_a_complete_capture(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-slot0-early-exit-") as temporary:
            root = Path(temporary)
            plan = _plan(root)
            clock = _Clock()
            reader = _Reader(plan.game_exe, [(7, 0, 0, 0)])
            controller = StartupSlot0ProbeController(
                plan=plan,
                pid=4444,
                launch_role="initial",
                timeline_origin_monotonic=clock.monotonic(),
                timeline_origin_at="origin",
                reader_factory=lambda _pid, _exe: reader,
                sleeper=clock.sleep,
                monotonic=clock.monotonic,
                wall_clock=clock.wall,
            )
            controller.start()
            report = controller.finish()

        self.assertFalse(report["capture_ok"])
        self.assertEqual(report["sample_count"], 0)
        self.assertEqual(report["process_exit"]["exit_code"], 7)


if __name__ == "__main__":
    unittest.main()

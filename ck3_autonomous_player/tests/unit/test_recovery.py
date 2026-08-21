from __future__ import annotations

import contextlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


PACKAGE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(PACKAGE_ROOT))

from xar_autoplayer import cli  # noqa: E402
from xar_autoplayer import recovery  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    _contract_digest,
    EnvironmentSpec,
    sha256_file,
    write_json_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402


RUN_ID = "20260822T010203Z-crash-deadbeef"
PROBE_NONCE = "a" * 32
WATCHDOG_NONCE = "b" * 32


def _identity(
    executable: Path, pid: int, parent_pid: int, command_line: str
) -> dict[str, object]:
    return {
        "pid": pid,
        "parent_pid": parent_pid,
        "name": executable.name,
        "executable": str(executable.resolve()),
        "creation_date": f"20260822010{pid % 10}03.000000+000",
        "command_line": command_line,
    }


class RecoveryFixture:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.spec = EnvironmentSpec(self.root / "state", self.root / "game")
        self.run = self.spec.state_dir / "runs" / RUN_ID
        self.artifacts = self.run / "artifacts"
        self.control = self.spec.state_dir / "control"
        self.artifacts.mkdir(parents=True)
        self.control.mkdir(parents=True)
        self.spec.game_exe.parent.mkdir(parents=True)
        self.spec.game_exe.write_bytes(b"fixture ck3 executable")

        python = self.root / "python.exe"
        pythonw = self.root / "pythonw.exe"
        python.write_bytes(b"python")
        pythonw.write_bytes(b"pythonw")
        self.outer = _identity(python, 101, 1, "outer")
        self.bootstrap = _identity(python, 102, 101, "bootstrap")
        self.supervisor = _identity(python, 103, 102, "supervisor")
        self.ck3 = _identity(self.spec.game_exe, 104, 103, "ck3 -userdir=fixture")
        self.sentinel_parent = _identity(python, 105, 103, "sentinel-parent")
        self.sentinel_child = _identity(python, 106, 105, "sentinel-child")
        self.watchdog = _identity(pythonw, 107, 1, "watchdog")

        self.paths = {
            "record": self.control / "ck3.json",
            "ready": self.control / f"watchdog-{WATCHDOG_NONCE}.ready.json",
            "unsafe_marker": self.control / "unsafe-cleanup.json",
            "watchdog_error": self.control / "ck3.watchdog_error",
        }
        self.record = {
            "format_version": 1,
            "nonce": WATCHDOG_NONCE,
            "ck3_pid": self.ck3["pid"],
            "parent_pid": self.supervisor["pid"],
            "executable": self.ck3["executable"],
            "creation_date": self.ck3["creation_date"],
        }
        self.ready = {
            "nonce": WATCHDOG_NONCE,
            "parent_pid": self.supervisor["pid"],
            "parent_executable": self.supervisor["executable"],
            "parent_creation_date": self.supervisor["creation_date"],
            "watchdog_pid": self.watchdog["pid"],
        }
        self.marker = {
            "nonce": WATCHDOG_NONCE,
            "ck3_pid": self.ck3["pid"],
            "reason": "fixture remains unsafe until explicit recovery",
        }
        write_json_atomic(self.paths["record"], self.record)
        write_json_atomic(self.paths["ready"], self.ready)
        write_json_atomic(self.paths["unsafe_marker"], self.marker)
        self.errors = ["terminate:104:access-denied"]
        self.paths["watchdog_error"].write_text(
            ";".join(self.errors) + "\n", encoding="utf-8"
        )

        self.archived_control: dict[str, Path] = {}
        for label in ("record", "ready", "unsafe_marker"):
            archive = (
                self.artifacts
                / f"control-before-{label}-{PROBE_NONCE}.json"
            )
            archive.write_bytes(self.paths[label].read_bytes())
            self.archived_control[label] = archive

        self.environment = {
            "format_version": 1,
            "state_dir": str(self.spec.state_dir.resolve()),
            "profile_dir": str(self.spec.profile_dir.resolve()),
            "game": {
                "executable": str(self.spec.game_exe.resolve()),
                "executable_sha256": sha256_file(self.spec.game_exe),
            },
        }
        self.environment["environment_sha256"] = _contract_digest(
            self.environment
        )
        self.environment_path = self.run / "environment.json"
        write_json_atomic(self.environment_path, self.environment)

        self.owner_path = self.artifacts / f"owner-{PROBE_NONCE}.json"
        write_json_atomic(self.owner_path, {"probe_nonce": PROBE_NONCE})
        self.ready_archive = self.artifacts / f"supervisor-ready-{PROBE_NONCE}.json"
        self.ack_archive = self.artifacts / f"supervisor-ack-{PROBE_NONCE}.json"
        write_json_atomic(self.ready_archive, {"probe_nonce": PROBE_NONCE})
        write_json_atomic(self.ack_archive, {"probe_nonce": PROBE_NONCE})
        self.armed_path = self.artifacts / f"armed-{PROBE_NONCE}.json"
        self.watchdog_final_path = (
            self.artifacts / f"watchdog-final-{PROBE_NONCE}.json"
        )
        self.handoff_path = self.artifacts / f"handoff-{PROBE_NONCE}.json"

        self.armed = {
            "format_version": 1,
            "probe_nonce": PROBE_NONCE,
            "watchdog_nonce": WATCHDOG_NONCE,
            "job_name": f"XarAutoplayer-Crash-{PROBE_NONCE}",
            "job_active_processes": 3,
            "process_resumed": True,
            "supervisor": self.supervisor,
            "supervisor_bootstrap": self.bootstrap,
            "ck3": self.ck3,
            "sentinel_parent": self.sentinel_parent,
            "sentinel_child": self.sentinel_child,
            "watchdog": self.watchdog,
            "control": {
                **{key: str(value.resolve()) for key, value in self.paths.items()},
                "record_sha256": sha256_file(self.paths["record"]),
                "ready_sha256": sha256_file(self.paths["ready"]),
                "unsafe_marker_sha256": sha256_file(
                    self.paths["unsafe_marker"]
                ),
            },
            "visual_attestation": {},
            "load_attestation": {},
            "artifacts": {},
            "environment_sha256": self.environment["environment_sha256"],
            "armed_at": "2026-08-22T01:02:03+00:00",
            "armed_monotonic": 10.0,
        }
        write_json_atomic(self.armed_path, self.armed)
        write_json_atomic(
            self.watchdog_final_path,
            {
                "format_version": 1,
                "nonce": WATCHDOG_NONCE,
                "parent_pid": self.supervisor["pid"],
                "ok": False,
                "stage": "cleanup",
                "authenticated_candidates": [self.ck3["pid"]],
                "errors": self.errors,
            },
        )
        self.handoff = {
            "format_version": 1,
            "probe_nonce": PROBE_NONCE,
            "run_id": RUN_ID,
            "state_dir": str(self.spec.state_dir.resolve()),
            "game_dir": str(self.spec.game_dir.resolve()),
            "timeout_seconds": 180.0,
            "artifacts": str(self.artifacts.resolve()),
            "supervisor_ready": str(self.ready_archive.resolve()),
            "supervisor_ack": str(self.ack_archive.resolve()),
            "armed": str(self.armed_path.resolve()),
            "watchdog_final": str(self.watchdog_final_path.resolve()),
            "outer": self.outer,
            "environment_sha256": self.environment["environment_sha256"],
            "owner_sha256": sha256_file(self.owner_path),
        }
        write_json_atomic(self.handoff_path, self.handoff)

        self.report = {
            "format_version": 1,
            "kind": "crash_recovery_smoke",
            "run_id": RUN_ID,
            "run_dir": str(self.run.resolve()),
            "environment_sha256": self.environment["environment_sha256"],
            "valid_score_episode": False,
            "runtime_write_absence_proven": False,
            "unsafe_cleanup": True,
            "finalized": True,
            "ok": False,
            "error": "fixture watchdog cleanup failed",
            "artifacts": {},
        }
        for label, path in (
            ("environment", self.environment_path),
            ("owner", self.owner_path),
            ("handoff", self.handoff_path),
            ("armed", self.armed_path),
        ):
            self.report["artifacts"][label] = self.entry(path)
        for label, path in self.archived_control.items():
            self.report["artifacts"][f"control_before_{label}"] = self.entry(
                path
            )
        self.report_path = self.run / "report.json"
        write_json_atomic(self.report_path, self.report)
        self.original_report = self.report_path.read_bytes()

    def entry(self, path: Path) -> dict[str, str]:
        return {
            "path": path.resolve().relative_to(self.run.resolve()).as_posix(),
            "sha256": sha256_file(path),
        }

    def patches(self):
        stable = {
            "tasklist_returncode": 0,
            "tasklist_pids": [],
            "wmi_pids": [],
            "processes": [],
            "continuous_empty_seconds": 5,
            "poll_count": 2,
        }
        immediate = {
            "tasklist_returncode": 0,
            "tasklist_pids": [],
            "wmi_pids": [],
            "processes": [],
        }
        stack = contextlib.ExitStack()
        stack.enter_context(
            mock.patch(
                "xar_autoplayer.recovery._validate_recovery_source_report",
                return_value=(self.report, "legacy_watchdog_failure_red"),
            )
        )
        stack.enter_context(
            mock.patch("xar_autoplayer.recovery._process_identity", return_value=None)
        )
        stack.enter_context(
            mock.patch("xar_autoplayer.recovery._named_job_absent", return_value=True)
        )
        stack.enter_context(
            mock.patch(
                "xar_autoplayer.recovery._wait_global_ck3_quiet",
                return_value=stable,
            )
        )
        stack.enter_context(
            mock.patch(
                "xar_autoplayer.recovery.ck3_process_inventory",
                return_value=immediate,
            )
        )
        return stack

    def assert_source_unchanged(self, case: unittest.TestCase) -> None:
        case.assertEqual(self.report_path.read_bytes(), self.original_report)

    def rebind_marker(self, payload: dict[str, object]) -> None:
        write_json_atomic(self.paths["unsafe_marker"], payload)
        write_json_atomic(self.archived_control["unsafe_marker"], payload)
        digest = sha256_file(self.paths["unsafe_marker"])
        self.armed["control"]["unsafe_marker_sha256"] = digest
        write_json_atomic(self.armed_path, self.armed)
        self.report["artifacts"]["armed"] = self.entry(self.armed_path)
        self.report["artifacts"]["control_before_unsafe_marker"] = self.entry(
            self.archived_control["unsafe_marker"]
        )
        write_json_atomic(self.report_path, self.report)
        self.original_report = self.report_path.read_bytes()


class StaleControlRecoveryTests(unittest.TestCase):
    def _fixture(self, temporary: str) -> RecoveryFixture:
        return RecoveryFixture(Path(temporary))

    def test_success_archives_controls_marker_last_and_never_rewrites_crash(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            calls: list[str] = []
            commit_events: list[str] = []
            real_cas = recovery._cas_archive_control
            real_write = recovery.write_json_atomic

            def observe(
                source: Path,
                destination: Path,
                expected_sha256: str,
                expected_nonce: str | None,
            ) -> None:
                calls.append(source.name)
                if source.name == "unsafe-cleanup.json":
                    commit_events.append("marker_cas_start")
                real_cas(source, destination, expected_sha256, expected_nonce)
                if source.name == "unsafe-cleanup.json":
                    commit_events.append("marker_cas_return")

            def observe_write(path: Path, payload: object) -> None:
                if (
                    isinstance(payload, dict)
                    and payload.get("kind") == "stale_control_recovery"
                    and payload.get("ok") is True
                ):
                    commit_events.append("final_report_write")
                real_write(path, payload)

            immediate = {
                "tasklist_returncode": 0,
                "tasklist_pids": [],
                "wmi_pids": [],
                "processes": [],
            }

            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._cas_archive_control",
                side_effect=observe,
            ), mock.patch(
                "xar_autoplayer.recovery.write_json_atomic",
                side_effect=observe_write,
            ), mock.patch(
                "xar_autoplayer.recovery.ck3_process_inventory",
                side_effect=lambda: (
                    commit_events.append("instant_inventory") or immediate
                ),
            ), mock.patch(
                "xar_autoplayer.recovery._named_job_absent",
                side_effect=lambda _: (
                    commit_events.append("job_absent") or True
                ),
            ):
                result = recovery._recover_stale_control_locked(
                    fixture.spec, RUN_ID
                )

            self.assertTrue(result["ok"])
            self.assertTrue(result["finalized"])
            self.assertTrue(result["current_absence_proven"])
            self.assertFalse(result["historical_cleanup_proven"])
            self.assertFalse(result["valid_score_episode"])
            self.assertEqual(
                calls,
                [
                    "ck3.json",
                    f"watchdog-{WATCHDOG_NONCE}.ready.json",
                    "ck3.watchdog_error",
                    "unsafe-cleanup.json",
                ],
            )
            self.assertEqual(
                commit_events[-5:],
                [
                    "final_report_write",
                    "instant_inventory",
                    "job_absent",
                    "marker_cas_start",
                    "marker_cas_return",
                ],
            )
            self.assertEqual(commit_events[-1], "marker_cas_return")
            self.assertTrue(all(not path.exists() for path in fixture.paths.values()))
            recovery_dir = Path(str(result["recovery_dir"]))
            self.assertTrue((recovery_dir / "artifacts" / "unsafe-cleanup.json").is_file())
            on_disk = json.loads(
                (recovery_dir / "report.json").read_text(encoding="utf-8")
            )
            self.assertEqual(on_disk, result)
            self.assertEqual(recovery.validate_recovery_report(recovery_dir), result)
            fixture.assert_source_unchanged(self)

    def test_interrupt_after_marker_cas_performs_no_further_write_or_move(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-commit-") as temporary:
            fixture = self._fixture(temporary)
            committed = False
            post_commit_mutations: list[str] = []
            real_cas = recovery._cas_archive_control
            real_replace = recovery.os.replace
            real_write_json = recovery.write_json_atomic
            real_write_bytes = recovery.write_bytes_atomic
            real_restore = recovery._restore_controls
            real_finalize_failure = recovery._finalize_failure_report

            def interrupt_after_marker_cas(
                source: Path,
                destination: Path,
                expected_sha256: str,
                expected_nonce: str | None,
            ) -> None:
                nonlocal committed
                real_cas(source, destination, expected_sha256, expected_nonce)
                if source.name == "unsafe-cleanup.json":
                    committed = True
                    raise KeyboardInterrupt("injected after committed marker CAS")

            def observe_replace(source: object, destination: object) -> None:
                if committed:
                    post_commit_mutations.append("os.replace")
                real_replace(source, destination)

            def observe_json(path: Path, payload: object) -> None:
                if committed:
                    post_commit_mutations.append("write_json_atomic")
                real_write_json(path, payload)

            def observe_bytes(path: Path, payload: bytes) -> None:
                if committed:
                    post_commit_mutations.append("write_bytes_atomic")
                real_write_bytes(path, payload)

            def observe_restore(journal: object) -> dict[str, str]:
                if committed:
                    post_commit_mutations.append("restore_controls")
                return real_restore(journal)

            def observe_failure_report(*args: object, **kwargs: object) -> None:
                if committed:
                    post_commit_mutations.append("finalize_failure_report")
                real_finalize_failure(*args, **kwargs)

            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._cas_archive_control",
                side_effect=interrupt_after_marker_cas,
            ), mock.patch(
                "xar_autoplayer.recovery.os.replace",
                side_effect=observe_replace,
            ), mock.patch(
                "xar_autoplayer.recovery.write_json_atomic",
                side_effect=observe_json,
            ), mock.patch(
                "xar_autoplayer.recovery.write_bytes_atomic",
                side_effect=observe_bytes,
            ), mock.patch(
                "xar_autoplayer.recovery._restore_controls",
                side_effect=observe_restore,
            ), mock.patch(
                "xar_autoplayer.recovery._finalize_failure_report",
                side_effect=observe_failure_report,
            ):
                result = recovery._recover_stale_control_locked(
                    fixture.spec, RUN_ID
                )

            self.assertTrue(committed)
            self.assertEqual(post_commit_mutations, [])
            self.assertTrue(result["ok"])
            self.assertTrue(result["finalized"])
            self.assertFalse(fixture.paths["unsafe_marker"].exists())
            recovery_dir = Path(str(result["recovery_dir"]))
            self.assertEqual(recovery.validate_recovery_report(recovery_dir), result)
            fixture.assert_source_unchanged(self)

    def test_source_validator_failure_leaves_every_control_untouched(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._validate_recovery_source_report",
                side_effect=AgentError("tampered source"),
            ):
                with self.assertRaisesRegex(AgentError, "tampered source"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(all(path.is_file() for path in fixture.paths.values()))
            fixture.assert_source_unchanged(self)

    def test_active_marker_hash_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            fixture.paths["unsafe_marker"].write_text(
                '{"nonce":"drift"}\n', encoding="utf-8"
            )
            with fixture.patches():
                with self.assertRaisesRegex(AgentError, "active unsafe_marker"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())
            fixture.assert_source_unchanged(self)

    def test_internally_rehashed_wrong_marker_nonce_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            fixture.rebind_marker(
                {
                    **fixture.marker,
                    "nonce": "c" * 32,
                }
            )
            with fixture.patches():
                with self.assertRaisesRegex(AgentError, "marker identity differs"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())
            fixture.assert_source_unchanged(self)

    def test_missing_active_marker_is_restored_from_bound_archive(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            expected = fixture.paths["unsafe_marker"].read_bytes()
            fixture.paths["unsafe_marker"].unlink()
            with fixture.patches():
                with self.assertRaisesRegex(AgentError, "active control file"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertEqual(fixture.paths["unsafe_marker"].read_bytes(), expected)
            fixture.assert_source_unchanged(self)

    def test_live_or_ambiguous_recorded_identity_keeps_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)

            def live_supervisor(pid: int):
                if pid == fixture.supervisor["pid"]:
                    return dict(fixture.supervisor)
                return None

            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._process_identity",
                side_effect=live_supervisor,
            ):
                with self.assertRaisesRegex(AgentError, "still running"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())

            ambiguous = dict(fixture.supervisor)
            ambiguous["command_line"] = "different"
            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._process_identity",
                side_effect=lambda pid: (
                    ambiguous if pid == fixture.supervisor["pid"] else None
                ),
            ):
                with self.assertRaisesRegex(AgentError, "ambiguous"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())

    def test_identity_query_failure_keeps_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._process_identity",
                side_effect=OSError("WMI failed"),
            ):
                with self.assertRaisesRegex(AgentError, "identity is unknown"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())

    def test_existing_named_job_keeps_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._named_job_absent", return_value=False
            ):
                with self.assertRaisesRegex(AgentError, "Job still exists"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())

    def test_inventory_failure_or_pre_marker_reappearance_keeps_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._wait_global_ck3_quiet",
                side_effect=AgentError("dual-source disagreement"),
            ):
                with self.assertRaisesRegex(AgentError, "dual-source disagreement"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(fixture.paths["unsafe_marker"].is_file())

        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            reappeared = {
                "tasklist_returncode": 0,
                "tasklist_pids": [999],
                "wmi_pids": [999],
                "processes": [{"pid": 999}],
            }
            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery.ck3_process_inventory",
                return_value=reappeared,
            ):
                with self.assertRaisesRegex(AgentError, "pre-marker"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(all(path.is_file() for path in fixture.paths.values()))

    def test_marker_cas_failure_restores_prior_controls_and_keeps_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            calls: list[str] = []
            real_cas = recovery._cas_archive_control

            def fail_marker(
                source: Path,
                destination: Path,
                expected_sha256: str,
                expected_nonce: str | None,
            ) -> None:
                calls.append(source.name)
                if source.name == "unsafe-cleanup.json":
                    raise OSError("injected marker CAS failure")
                real_cas(source, destination, expected_sha256, expected_nonce)

            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._cas_archive_control",
                side_effect=fail_marker,
            ):
                with self.assertRaisesRegex(AgentError, "marker CAS failure"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertEqual(calls[-1], "unsafe-cleanup.json")
            self.assertTrue(all(path.is_file() for path in fixture.paths.values()))
            fixture.assert_source_unchanged(self)

    def test_async_interruption_after_move_restores_controls_and_marker(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            real_cas = recovery._cas_archive_control

            def interrupt_after_ready_move(
                source: Path,
                destination: Path,
                expected_sha256: str,
                expected_nonce: str | None,
            ) -> None:
                real_cas(source, destination, expected_sha256, expected_nonce)
                if source == fixture.paths["ready"]:
                    raise KeyboardInterrupt("injected interruption")

            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery._cas_archive_control",
                side_effect=interrupt_after_ready_move,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertTrue(all(path.is_file() for path in fixture.paths.values()))
            reports = list((fixture.spec.state_dir / "recoveries").glob("*/report.json"))
            red = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertTrue(red["finalized"])
            self.assertFalse(red["ok"])
            self.assertTrue(red["marker_present_after_failure"])
            self.assertFalse(red["current_absence_proven"])
            fixture.assert_source_unchanged(self)

    def test_success_report_write_failure_restores_marker_and_finalizes_red(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-") as temporary:
            fixture = self._fixture(temporary)
            real_write = recovery.write_json_atomic
            cas_calls: list[str] = []
            real_cas = recovery._cas_archive_control

            def fail_green(path: Path, payload: object) -> None:
                if (
                    isinstance(payload, dict)
                    and payload.get("kind") == "stale_control_recovery"
                    and payload.get("ok") is True
                ):
                    raise OSError("injected final report failure")
                real_write(path, payload)

            def observe_cas(
                source: Path,
                destination: Path,
                expected_sha256: str,
                expected_nonce: str | None,
            ) -> None:
                cas_calls.append(source.name)
                real_cas(source, destination, expected_sha256, expected_nonce)

            with fixture.patches(), mock.patch(
                "xar_autoplayer.recovery.write_json_atomic",
                side_effect=fail_green,
            ), mock.patch(
                "xar_autoplayer.recovery._cas_archive_control",
                side_effect=observe_cas,
            ):
                with self.assertRaisesRegex(AgentError, "final report failure"):
                    recovery._recover_stale_control_locked(fixture.spec, RUN_ID)
            self.assertNotIn("unsafe-cleanup.json", cas_calls)
            self.assertTrue(all(path.is_file() for path in fixture.paths.values()))
            reports = list((fixture.spec.state_dir / "recoveries").glob("*/report.json"))
            self.assertEqual(len(reports), 1)
            red = json.loads(reports[0].read_text(encoding="utf-8"))
            self.assertTrue(red["finalized"])
            self.assertFalse(red["ok"])
            self.assertTrue(red["marker_present_after_failure"])
            self.assertFalse(red["current_absence_proven"])
            fixture.assert_source_unchanged(self)


class RecoveryCliTests(unittest.TestCase):
    def test_cli_requires_and_routes_explicit_run_id(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-cli-") as temporary:
            root = Path(temporary)
            expected = {
                "kind": "stale_control_recovery",
                "ok": True,
                "source_run_id": RUN_ID,
            }
            with mock.patch(
                "xar_autoplayer.recovery.recover_stale_control",
                return_value=expected,
            ) as recover, mock.patch("builtins.print"):
                code = cli.main(
                    [
                        "--state-dir",
                        str(root / "state"),
                        "--game-dir",
                        str(root / "game"),
                        "recover-stale-control",
                        "--run-id",
                        RUN_ID,
                    ]
                )
            self.assertEqual(code, 0)
            self.assertEqual(recover.call_args.args[1], RUN_ID)

    def test_public_recovery_acquires_state_then_launch_locks(self) -> None:
        with tempfile.TemporaryDirectory(prefix="xar-recovery-locks-") as temporary:
            root = Path(temporary)
            spec = EnvironmentSpec(root / "state", root / "game")
            order: list[str] = []

            @contextlib.contextmanager
            def state_lock(state_dir: Path, purpose: str):
                order.append(f"state:{purpose}")
                yield

            @contextlib.contextmanager
            def launch_lock(game_exe: Path):
                order.append("launch")
                yield

            with mock.patch(
                "xar_autoplayer.recovery.ensure_state_path_safe"
            ), mock.patch(
                "xar_autoplayer.recovery.exclusive_state_lock",
                side_effect=state_lock,
            ), mock.patch(
                "xar_autoplayer.recovery.exclusive_launch_lock",
                side_effect=launch_lock,
            ), mock.patch(
                "xar_autoplayer.recovery._recover_stale_control_locked",
                return_value={"ok": True},
            ):
                recovery.recover_stale_control(spec, RUN_ID)
            self.assertEqual(order, ["state:recover-stale-control", "launch"])


if __name__ == "__main__":
    unittest.main()

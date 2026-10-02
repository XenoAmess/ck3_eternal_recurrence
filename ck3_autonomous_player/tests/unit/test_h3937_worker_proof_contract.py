"""Offline, synthetic evidence tests; no CK3, screen, or authoritative bus."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from xar_autoplayer import h3937_worker_proof_contract as contract


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _put(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


class WorkerProofContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="h3937-worker-proof-")
        self.addCleanup(self.temporary.cleanup)
        self.output = Path(self.temporary.name) / "fixture"
        worker_dir = self.output / "worker"
        worker_dir.mkdir(parents=True)
        self.executable = Path(sys.executable)
        self.actual_executable = Path(sys._base_executable)
        self.argv = (str(self.executable), str(self.output / "harmless_dummy.py"))
        self.frozen = contract.FrozenWorkerCommand(
            argv=self.argv, executable_sha256=_sha(self.executable),
            actual_argv=self.argv,
            actual_executable_path=str(self.actual_executable),
            actual_executable_sha256=_sha(self.actual_executable),
            expected_parent_pid=100,
            expected_parent_creation_filetime_100ns=133999999999999999,
            timeout_seconds=2.0,
        )
        (worker_dir / "worker.stdout.bin").write_bytes(b"dummy stdout\n")
        (worker_dir / "worker.stderr.bin").write_bytes(b"")
        (worker_dir / "unsafe-marker.json").write_bytes(b"historical worker marker\n")
        (self.output / "outer-unsafe-marker.json").write_bytes(b"outer marker\n")
        self.inner = {
            "schema": "xar.fixture.worker-process-proof.v1",
            "status": "RED",  # A read-only query may fail while the Job tree exits.
            "error": "worker returncode 1",
            "worker_pid": 123,
            "worker_identity": {
                "pid": 123, "parent_pid": 100,
                "parent_creation_filetime_100ns": 133999999999999999,
                "creation_filetime_100ns": 134000000000000000,
                "creation_utc": datetime.now(timezone.utc).isoformat(),
                "exe": str(self.executable), "argv": list(self.argv),
                "job_member": True,
            },
            "actual_worker_identity": {
                "pid": 124, "parent_pid": 123,
                "creation_filetime_100ns": 134000000000000100,
                "creation_utc": datetime.now(timezone.utc).isoformat(),
                "exe": str(self.actual_executable), "argv": list(self.argv),
                "observed_while_running": True,
                "wmi_toolhelp_cross_checked": True,
                "job_member": True,
            },
            "worker_returncode": 1, "worker_exited": True,
            "timeout": False, "watchdog_error": None,
            "watchdog_fired_at_elapsed": None, "watchdog_action": None,
            "child_survived_worker": False, "job_terminated": False,
            "unassigned_worker_killed": False, "job_closed": True,
            "job_zero_active": True,
            "job_before_resume": {"active": 1, "total": 1},
            "job_after_resume": {"active": 2, "total": 2},
            "job_after_cleanup": {"active": 0, "total": 2},
            "resumed_tid": 456, "elapsed_seconds_before_receipt": 0.4,
            "deadline_seconds_from_entry": 1.99,
            "unsafe_marker_path": str(worker_dir / "unsafe-marker.json"),
            "unsafe_marker_sha256": _sha(worker_dir / "unsafe-marker.json"),
            "stdout_path": str(worker_dir / "worker.stdout.bin"),
            "stdout_sha256": _sha(worker_dir / "worker.stdout.bin"),
            "stderr_path": str(worker_dir / "worker.stderr.bin"),
            "stderr_sha256": _sha(worker_dir / "worker.stderr.bin"),
        }
        self.outer = {
            "schema": "xar.fixture.worker-process-outer.v2",
            "status": "RED", "error": None,
            "inner_receipt_path": str(worker_dir / "receipt.json"),
            "inner_status": "RED", "elapsed_seconds_before_receipt": 0.5,
            "deadline_seconds_from_entry": 2.0,
            "outer_marker_sha256": _sha(self.output / "outer-unsafe-marker.json"),
        }
        self._write_receipts()

    def _write_receipts(self) -> None:
        inner_path = self.output / "worker" / "receipt.json"
        _put(inner_path, self.inner)
        self.outer["inner_receipt_sha256"] = _sha(inner_path)
        _put(self.output / "outer-receipt.json", self.outer)

    def _verify(self, *, now=None):
        return contract.verify_worker_exit(
            output=self.output, frozen=self.frozen,
            started_monotonic=100.0, now=now or (lambda: 100.8),
        )

    def test_query_red_with_contained_tree_is_process_only_proof(self) -> None:
        proof = self._verify()
        self.assertEqual(proof.launcher_pid, 123)
        self.assertEqual(proof.actual_worker_pid, 124)
        self.assertEqual(proof.returncode, 1)
        self.assertEqual(proof.argv, self.argv)

    def test_pid_creation_argv_or_executable_drift_rejected(self) -> None:
        for field, value in (
            ("pid", 124), ("creation_filetime_100ns", 0),
            ("parent_creation_filetime_100ns", 12),
            ("job_member", False),
            ("creation_utc", "2026-09-30T09:00:00"),
            ("exe", str(self.output / "wrong-python.exe")),
            ("argv", [self.argv[0], "other.py"]),
        ):
            with self.subTest(field=field):
                original = self.inner["worker_identity"][field]
                self.inner["worker_identity"][field] = value
                self._write_receipts()
                with self.assertRaises(contract.WorkerProofError):
                    self._verify()
                self.inner["worker_identity"][field] = original
        self._write_receipts()

    def test_missing_job_or_timeout_is_rejected(self) -> None:
        for field, value in (
            ("job_closed", False), ("job_zero_active", False),
            ("timeout", True), ("worker_exited", False),
            ("child_survived_worker", True), ("job_terminated", True),
        ):
            with self.subTest(field=field):
                original = self.inner[field]
                self.inner[field] = value
                self._write_receipts()
                with self.assertRaises(contract.WorkerProofError):
                    self._verify()
                self.inner[field] = original
        self.inner["job_after_cleanup"]["active"] = 1
        self._write_receipts()
        with self.assertRaises(contract.WorkerProofError):
            self._verify()

    def test_actual_child_unknown_or_unbound_is_rejected(self) -> None:
        for field, value in (
            ("pid", 0), ("pid", 123), ("parent_pid", 122),
            ("observed_while_running", "true"),
            ("wmi_toolhelp_cross_checked", False),
            ("job_member", False),
            ("creation_utc", "not-a-time"),
            ("argv", [str(self.executable), "other.py"]),
        ):
            with self.subTest(field=field):
                original = self.inner["actual_worker_identity"][field]
                self.inner["actual_worker_identity"][field] = value
                self._write_receipts()
                with self.assertRaises(contract.WorkerProofError):
                    self._verify()
                self.inner["actual_worker_identity"][field] = original
        self.inner["job_after_resume"]["total"] = 1
        self._write_receipts()
        with self.assertRaises(contract.WorkerProofError):
            self._verify()

    def test_receipt_marker_and_stdio_mutation_rejected(self) -> None:
        for path in (
            self.output / "worker" / "receipt.json",
            self.output / "worker" / "worker.stdout.bin",
            self.output / "outer-unsafe-marker.json",
        ):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(original + b"x")
                with self.assertRaises((contract.WorkerProofError, json.JSONDecodeError)):
                    self._verify()
                path.write_bytes(original)

    def test_late_hash_or_receipt_phase_rejected(self) -> None:
        self.outer["elapsed_seconds_before_receipt"] = 2.2
        self._write_receipts()
        with self.assertRaises(contract.WorkerProofError):
            self._verify()
        self.outer["elapsed_seconds_before_receipt"] = 0.5
        self._write_receipts()
        with self.assertRaises(contract.WorkerProofError):
            self._verify(now=lambda: 102.2)
        clock = [100.1]
        original_sha = contract._sha

        def slow_marker_hash(path: Path) -> str:
            result = original_sha(path)
            if path.name == "outer-unsafe-marker.json":
                clock[0] = 102.2
            return result

        with mock.patch.object(contract, "_sha", side_effect=slow_marker_hash):
            with self.assertRaises(contract.WorkerProofError):
                self._verify(now=lambda: clock[0])

    def test_wrong_frozen_executable_bytes_rejected(self) -> None:
        frozen = contract.FrozenWorkerCommand(
            argv=self.argv, executable_sha256="0" * 64,
            actual_argv=self.argv,
            actual_executable_path=str(self.actual_executable),
            actual_executable_sha256=_sha(self.actual_executable),
            expected_parent_pid=100,
            expected_parent_creation_filetime_100ns=133999999999999999,
            timeout_seconds=2.0,
        )
        with self.assertRaises(contract.WorkerProofError):
            contract.verify_worker_exit(
                output=self.output, frozen=frozen,
                started_monotonic=100.0, now=lambda: 100.1,
            )

    def test_actual_os_executable_is_separate_from_argv_zero(self) -> None:
        proof = self._verify()
        self.assertEqual(proof.actual_executable, str(self.actual_executable))
        self.assertEqual(proof.actual_argv[0], str(self.executable))
        wrong_path = contract.FrozenWorkerCommand(
            argv=self.argv, executable_sha256=_sha(self.executable),
            actual_argv=self.argv,
            actual_executable_path=str(self.executable),
            actual_executable_sha256=_sha(self.executable),
            expected_parent_pid=100,
            expected_parent_creation_filetime_100ns=133999999999999999,
            timeout_seconds=2.0,
        )
        if self.executable.resolve() != self.actual_executable.resolve():
            with self.assertRaises(contract.WorkerProofError):
                contract.verify_worker_exit(
                    output=self.output, frozen=wrong_path,
                    started_monotonic=100.0, now=lambda: 100.1,
                )

    def test_real_harmless_popen_without_job_receipt_is_unproven(self) -> None:
        command = [str(self.executable), "-c", "import os; print(os.getpid())"]
        child = subprocess.Popen(
            command, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        try:
            stdout, stderr = child.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate(timeout=5)
            raise
        self.assertEqual(child.returncode, 0, stderr)
        self.assertGreater(int(stdout.strip()), 0)
        # A successful Popen and matching PID alone never prove a Job tree.
        (self.output / "worker" / "receipt.json").unlink()
        with self.assertRaises(contract.WorkerProofError):
            self._verify()


if __name__ == "__main__":
    unittest.main()

"""No-launch contract tests for the isolated task-bus CAS patch."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


SOURCE = Path(__file__).with_name("codex_task_bus.py")
# The bus CLI needs only the standard library. Invoke the same-version base
# interpreter directly so the venv redirector cannot outlive a timed CLI test
# while its real child still holds the captured stdout pipe.
CLI_PYTHON = getattr(sys, "_base_executable", sys.executable)
SPEC = importlib.util.spec_from_file_location("codex_task_bus_patched", SOURCE)
assert SPEC and SPEC.loader
bus_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bus_module)

TASK = "war-h3937-cas-test"
OTHER = "war-other-cas-test"
RESOURCE = "ck3-screen:acquired"


class ScreenReleaseCasTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bus = Path(self.temp.name) / "bus"
        (self.bus / "tasks").mkdir(parents=True)
        (self.bus / ".lock").write_bytes(b"0")
        (self.bus / "sequence.txt").write_text("10\n", encoding="ascii")
        events = [
            {"schema": bus_module.SCHEMA, "sequence": sequence,
             "kind": "notification", "task_id": TASK}
            for sequence in range(1, 10)
        ]
        events.append({"schema": bus_module.SCHEMA, "sequence": 10,
                       "kind": "registered", "task_id": TASK,
                       "state": "running", "resources": [RESOURCE]})
        (self.bus / "events.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        installed = self.bus / "bin" / "codex_task_bus.py"
        installed.parent.mkdir()
        installed.write_bytes(SOURCE.read_bytes())
        self.cli_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper()
        self.seed(TASK)
        self.identity = mock.patch.object(
            bus_module, "git_identity",
            return_value={"repo": str(self.bus), "git": None},
        )
        self.identity.start()
        self.addCleanup(self.identity.stop)

    def screen_cli(self) -> list[str]:
        return [CLI_PYTHON, str(SOURCE), "--bus-dir", str(self.bus),
                "--expected-cli-sha256", self.cli_sha]

    def seed(self, task: str, *, sequence: int = 10,
             state: str = "running", resources: list[str] | None = None,
             updated: datetime | None = None) -> None:
        snapshot = {
            "schema": bus_module.SCHEMA,
            "task_id": task,
            "state": state,
            "summary": "owned",
            "next_step": "cleanup",
            "resources": [RESOURCE] if resources is None else resources,
            "last_sequence": sequence,
            "updated_at_utc": (updated or datetime.now(timezone.utc)).isoformat(),
            "pid": 1,
            "repo": str(self.bus),
            "git": None,
        }
        bus_module.write_json_atomic(bus_module.task_path(self.bus, task), snapshot)
        if task == TASK and sequence == 10:
            events = bus_module.read_events(self.bus)
            if len(events) >= 10 and events[9].get("task_id") == TASK:
                events[9]["state"] = state
                events[9]["resources"] = snapshot["resources"]
                (self.bus / "events.jsonl").write_text(
                    "".join(json.dumps(event) + "\n" for event in events),
                    encoding="utf-8",
                )

    def bytes_before(self) -> tuple[bytes, bytes, bytes]:
        return (
            bus_module.task_path(self.bus, TASK).read_bytes(),
            (self.bus / "sequence.txt").read_bytes(),
            (self.bus / "events.jsonl").read_bytes(),
        )

    def assert_conflict_without_write(self, *, expected_sequence: int = 10) -> None:
        before = self.bytes_before()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.release_screen_cas(
                self.bus, TASK, expected_sequence, summary="released",
            )
        self.assertEqual(self.bytes_before(), before)

    def test_success_writes_one_completed_event_and_exact_readback(self) -> None:
        task, event = bus_module.release_screen_cas(
            self.bus, TASK, 10, summary="released",
        )
        self.assertEqual(event["sequence"], 11)
        self.assertEqual(task["last_sequence"], event["sequence"])
        self.assertEqual(task["state"], "done")
        self.assertEqual(task["resources"], [])
        self.assertEqual(bus_module.read_json(bus_module.task_path(self.bus, TASK)), task)
        events = bus_module.read_events(self.bus)
        self.assertEqual(len(events), 11)
        self.assertEqual(events[-1]["event_id"], event["event_id"])

    def test_missing_event_sequence_refuses_release_without_write(self) -> None:
        events = bus_module.read_events(self.bus)
        events.pop(4)  # The tail still matches sequence.txt, but event 5 is gone.
        (self.bus / "events.jsonl").write_text(
            "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        self.assert_conflict_without_write()

    def test_snapshot_same_sequence_but_screen_resources_changed_refuses(self) -> None:
        task_path = bus_module.task_path(self.bus, TASK)
        snapshot = bus_module.read_json(task_path)
        snapshot["resources"] = []
        bus_module.write_json_atomic(task_path, snapshot)
        self.assert_conflict_without_write()

    def test_partial_screen_claim_event_without_snapshot_blocks_next_claim(self) -> None:
        self.seed(TASK, state="done", resources=[])
        with mock.patch.object(bus_module, "write_json_atomic", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                bus_module.update_task(
                    self.bus, OTHER, state="running", summary="claim", next_step="",
                    repo=None, resources=[RESOURCE], kind="registered",
                    expected_cli_sha256=self.cli_sha,
                )
        self.assertFalse(bus_module.task_path(self.bus, OTHER).exists())
        self.assertEqual(bus_module.read_events(self.bus)[-1]["task_id"], OTHER)
        self.assertEqual((self.bus / "sequence.txt").read_text(encoding="ascii").strip(), "11")
        before = self.bytes_before()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.update_task(
                self.bus, "war-third-cas-test", state="running", summary="claim",
                next_step="", repo=None, resources=[RESOURCE], kind="registered",
                expected_cli_sha256=self.cli_sha,
            )
        self.assertEqual(self.bytes_before(), before)
        self.assertFalse(bus_module.task_path(self.bus, "war-third-cas-test").exists())

    def test_heartbeat_sequence_race_rejects_without_write(self) -> None:
        bus_module.update_task(
            self.bus, TASK, state=None, summary=None, next_step=None,
            repo=None, resources=None, kind="heartbeat", expected_sequence=10,
        )
        self.assert_conflict_without_write(expected_sequence=10)

    def test_old_owner_status_register_and_unbound_heartbeat_cannot_change_lease(self) -> None:
        for command in (
            ["status", "--task", TASK, "--state", "done"],
            ["status", "--task", TASK, "--state", "running",
             "--resource", "ordinary-resource"],
            ["register", "--task", TASK, "--summary", "reset"],
            ["register", "--task", TASK, "--summary", "reset",
             "--resource", RESOURCE],
            ["heartbeat", "--task", TASK],
            ["heartbeat", "--task", TASK, "--expected-sequence", "9"],
        ):
            with self.subTest(command=command):
                before = self.bytes_before()
                completed = subprocess.run(
                    [*self.screen_cli(), *command],
                    capture_output=True, text=True, check=False, timeout=10,
                )
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertEqual(json.loads(completed.stdout)["code"], "CAS_CONFLICT")
                self.assertEqual(self.bytes_before(), before)

    def test_screen_heartbeat_needs_exact_sequence_and_current_owner(self) -> None:
        task, event = bus_module.update_task(
            self.bus, TASK, state=None, summary=None, next_step=None,
            repo=None, resources=None, kind="heartbeat", expected_sequence=10,
        )
        self.assertEqual(task["state"], "running")
        self.assertEqual(task["resources"], [RESOURCE])
        self.assertEqual(task["last_sequence"], event["sequence"])
        self.assertEqual(event["sequence"], 11)
        self.assert_conflict_without_write(expected_sequence=10)

    def test_stale_screen_heartbeat_cannot_revive_lease(self) -> None:
        self.seed(TASK, updated=datetime.now(timezone.utc) - timedelta(seconds=601))
        before = self.bytes_before()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.update_task(
                self.bus, TASK, state=None, summary=None, next_step=None,
                repo=None, resources=None, kind="heartbeat", expected_sequence=10,
            )
        self.assertEqual(self.bytes_before(), before)

    def test_missing_lock_conflict_does_not_create_lock_or_write(self) -> None:
        (self.bus / ".lock").unlink()
        before = self.bytes_before()
        self.assert_conflict_without_write()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.update_task(
                self.bus, TASK, state="done", summary=None, next_step=None,
                repo=None, resources=[], kind="completed",
            )
        self.assertFalse((self.bus / ".lock").exists())
        self.assertEqual(self.bytes_before(), before)

    def test_incomplete_bus_files_reject_before_event_or_snapshot_write(self) -> None:
        (self.bus / "sequence.txt").unlink()
        before_task = bus_module.task_path(self.bus, TASK).read_bytes()
        before_events = (self.bus / "events.jsonl").read_bytes()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.release_screen_cas(self.bus, TASK, 10, summary="released")
        self.assertFalse((self.bus / "sequence.txt").exists())
        self.assertEqual(bus_module.task_path(self.bus, TASK).read_bytes(), before_task)
        self.assertEqual((self.bus / "events.jsonl").read_bytes(), before_events)

    def test_owner_state_or_resource_change_rejects(self) -> None:
        for state, resources in (("waiting", [RESOURCE]), ("running", [])):
            with self.subTest(state=state, resources=resources):
                self.seed(TASK, state=state, resources=resources)
                self.assert_conflict_without_write()

    def test_other_fresh_owner_rejects_without_write(self) -> None:
        self.seed(OTHER)
        self.assert_conflict_without_write()

    def test_register_and_status_cannot_claim_another_screen_lease(self) -> None:
        before = self.bytes_before()
        for kind in ("registered", "status"):
            with self.subTest(kind=kind):
                with self.assertRaises(bus_module.CompareConflict):
                    bus_module.update_task(
                        self.bus, OTHER, state="running", summary="other",
                        next_step="", repo=None, resources=[RESOURCE], kind=kind,
                    )
                self.assertFalse(bus_module.task_path(self.bus, OTHER).exists())
                self.assertEqual(self.bytes_before(), before)

    def test_new_claim_rejects_extra_or_duplicate_screen_resources(self) -> None:
        self.seed(TASK, state="done", resources=[])
        for resources in ([RESOURCE, "ordinary-resource"], [RESOURCE, RESOURCE]):
            with self.subTest(resources=resources):
                before = self.bytes_before()
                command = [*self.screen_cli(), "register", "--task", OTHER,
                           "--summary", "claim"]
                for resource in resources:
                    command.extend(["--resource", resource])
                completed = subprocess.run(
                    command, capture_output=True, text=True, check=False, timeout=10,
                )
                self.assertEqual(completed.returncode, 3, completed.stderr)
                self.assertEqual(json.loads(completed.stdout)["code"], "CAS_CONFLICT")
                self.assertFalse(bus_module.task_path(self.bus, OTHER).exists())
                self.assertEqual(self.bytes_before(), before)

    def test_stale_or_done_screen_record_blocks_new_claim(self) -> None:
        old = datetime.now(timezone.utc) - timedelta(days=30)
        for state, updated in (("running", old), ("done", datetime.now(timezone.utc))):
            with self.subTest(state=state):
                self.seed(TASK, state=state, updated=updated)
                before = self.bytes_before()
                with self.assertRaises(bus_module.CompareConflict):
                    bus_module.update_task(
                        self.bus, OTHER, state="running", summary="new claim",
                        next_step="", repo=None, resources=[RESOURCE], kind="registered",
                    )
                self.assertFalse(bus_module.task_path(self.bus, OTHER).exists())
                self.assertEqual(self.bytes_before(), before)

    def test_old_screen_id_cannot_reregister_and_ordinary_id_can(self) -> None:
        self.seed(TASK, updated=datetime.now(timezone.utc) - timedelta(days=30))
        before = self.bytes_before()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.update_task(
                self.bus, TASK, state="running", summary="revive",
                next_step="", repo=None, resources=[RESOURCE], kind="registered",
            )
        self.assertEqual(self.bytes_before(), before)
        self.seed(TASK, resources=["ordinary-resource"])
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.update_task(
                self.bus, TASK, state="running", summary="screen conversion",
                next_step="", repo=None, resources=[RESOURCE], kind="registered",
            )
        task, event = bus_module.update_task(
            self.bus, TASK, state="running", summary="ordinary reuse",
            next_step="", repo=None, resources=["ordinary-resource"], kind="registered",
        )
        self.assertEqual(task["resources"], ["ordinary-resource"])
        self.assertEqual(task["last_sequence"], event["sequence"])

    def test_event_tail_and_global_sequence_must_match(self) -> None:
        with (self.bus / "events.jsonl").open("a", encoding="utf-8") as target:
            target.write(json.dumps({"sequence": 11, "kind": "notification",
                                     "task_id": OTHER}) + "\n")
        self.assert_conflict_without_write()
        (self.bus / "events.jsonl").write_text(
            json.dumps({"sequence": 10, "kind": "registered", "task_id": TASK}) + "\n",
            encoding="utf-8",
        )
        (self.bus / "sequence.txt").write_text("11\n", encoding="ascii")
        self.assert_conflict_without_write()

    def test_each_screen_cli_call_rechecks_installed_source_bytes(self) -> None:
        installed = self.bus / "bin" / "codex_task_bus.py"
        installed.write_bytes(b"outdated installed CLI")
        before = self.bytes_before()
        completed = subprocess.run(
            [*self.screen_cli(), "release-screen-cas", "--task", TASK,
             "--expected-sequence", "10", "--summary", "released"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(json.loads(completed.stdout)["code"], "CAS_CONFLICT")
        self.assertEqual(self.bytes_before(), before)

    def test_installed_bytes_drift_at_lock_boundary_rejects_all_screen_writes(self) -> None:
        installed = self.bus / "bin" / "codex_task_bus.py"
        original_lock = bus_module.bus_lock

        @contextmanager
        def drift_at_lock(bus: Path, *, require_existing: bool = False):
            with original_lock(bus, require_existing=require_existing):
                installed.write_bytes(b"changed after early pin")
                yield

        operations = (
            lambda: bus_module.release_screen_cas(
                self.bus, TASK, 10, summary="release",
                expected_cli_sha256=self.cli_sha,
            ),
            lambda: bus_module.update_task(
                self.bus, TASK, state=None, summary=None, next_step=None,
                repo=None, resources=None, kind="heartbeat", expected_sequence=10,
                expected_cli_sha256=self.cli_sha,
            ),
            lambda: bus_module.update_task(
                self.bus, OTHER, state="running", summary="claim", next_step="",
                repo=None, resources=[RESOURCE], kind="registered",
                expected_cli_sha256=self.cli_sha,
            ),
        )
        for index, operation in enumerate(operations):
            with self.subTest(operation=index):
                self.seed(TASK, state="done" if index == 2 else "running",
                          resources=[] if index == 2 else [RESOURCE])
                installed.write_bytes(SOURCE.read_bytes())
                before = self.bytes_before()
                bus_module._require_cli_pair(self.bus, self.cli_sha)
                with mock.patch.object(bus_module, "bus_lock", drift_at_lock):
                    with self.assertRaises(bus_module.CompareConflict):
                        operation()
                self.assertEqual(self.bytes_before(), before)
                self.assertFalse(bus_module.task_path(self.bus, OTHER).exists())

    def test_two_concurrent_screen_claims_have_one_winner(self) -> None:
        bus_module.task_path(self.bus, TASK).unlink()
        (self.bus / "sequence.txt").write_text("0\n", encoding="ascii")
        (self.bus / "events.jsonl").write_text("", encoding="utf-8")
        barrier = threading.Barrier(3)

        def claim(task: str) -> str:
            barrier.wait()
            try:
                bus_module.update_task(
                    self.bus, task, state="running", summary="claim",
                    next_step="", repo=None, resources=[RESOURCE], kind="registered",
                )
                return "claimed"
            except bus_module.CompareConflict:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(claim, task) for task in (TASK, OTHER)]
            barrier.wait()
            outcomes = [future.result(timeout=10) for future in futures]
        self.assertCountEqual(outcomes, ["claimed", "conflict"])
        self.assertEqual(len(bus_module.read_events(self.bus)), 1)
        owners = [task for task in (TASK, OTHER)
                  if bus_module.task_path(self.bus, task).is_file()]
        self.assertEqual(len(owners), 1)

    def test_stale_or_future_owner_rejects_without_write(self) -> None:
        now = datetime.now(timezone.utc)
        for updated in (now - timedelta(seconds=601), now + timedelta(seconds=11)):
            with self.subTest(updated=updated):
                self.seed(TASK, updated=updated)
                self.assert_conflict_without_write()

    def test_wrong_task_and_missing_bus_do_not_create_task(self) -> None:
        before = self.bytes_before()
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.release_screen_cas(self.bus, "wrong-task", 10, summary="released")
        missing = self.bus.parent / "wrong-bus"
        with self.assertRaises(bus_module.CompareConflict):
            bus_module.release_screen_cas(missing, TASK, 10, summary="released")
        self.assertFalse(missing.exists())
        self.assertEqual(self.bytes_before(), before)

    def test_two_concurrent_releases_have_one_winner(self) -> None:
        barrier = threading.Barrier(3)

        def attempt() -> str:
            barrier.wait()
            try:
                bus_module.release_screen_cas(self.bus, TASK, 10, summary="released")
                return "completed"
            except bus_module.CompareConflict:
                return "conflict"

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(attempt) for _ in range(2)]
            barrier.wait()
            outcomes = [future.result(timeout=10) for future in futures]
        self.assertCountEqual(outcomes, ["completed", "conflict"])
        self.assertEqual(len(bus_module.read_events(self.bus)), 11)
        self.assertEqual(bus_module.read_json(bus_module.task_path(self.bus, TASK))["last_sequence"], 11)

    def test_write_then_transport_error_requires_authoritative_readback(self) -> None:
        def transport() -> None:
            bus_module.release_screen_cas(self.bus, TASK, 10, summary="released")
            raise RuntimeError("transport failed after write")

        with self.assertRaises(RuntimeError):
            transport()
        task = bus_module.read_json(bus_module.task_path(self.bus, TASK))
        event = bus_module.read_events(self.bus)[-1]
        self.assertEqual(task["state"], "done")
        self.assertEqual(task["resources"], [])
        self.assertEqual(task["last_sequence"], event["sequence"])
        # The caller must still report RED because the command returned an error.

    def test_snapshot_write_error_leaves_partial_event_and_requires_red_readback(self) -> None:
        with mock.patch.object(bus_module, "write_json_atomic", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                bus_module.release_screen_cas(self.bus, TASK, 10, summary="released")
        task = bus_module.read_json(bus_module.task_path(self.bus, TASK))
        self.assertEqual(task["state"], "running")
        self.assertEqual(task["resources"], [RESOURCE])
        self.assertEqual(task["last_sequence"], 10)
        self.assertEqual(len(bus_module.read_events(self.bus)), 11)
        self.assertEqual((self.bus / "sequence.txt").read_text(encoding="ascii").strip(), "11")
        self.assert_conflict_without_write(expected_sequence=10)

    def test_install_to_temporary_bus_is_atomic_and_hash_pinned(self) -> None:
        installed = self.bus / "bin" / "codex_task_bus.py"
        before = installed.read_bytes()
        blocked = subprocess.run(
            [CLI_PYTHON, str(SOURCE), "--bus-dir", str(self.bus), "install"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(blocked.returncode, 3)
        self.assertEqual(json.loads(blocked.stdout)["code"], "CAS_CONFLICT")
        self.assertEqual(installed.read_bytes(), before)
        self.seed(TASK, state="done", resources=[])
        completed = subprocess.run(
            [CLI_PYTHON, str(SOURCE), "--bus-dir", str(self.bus), "install"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        receipt = json.loads(completed.stdout)
        source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest().upper()
        self.assertEqual(installed.read_bytes(), SOURCE.read_bytes())
        self.assertEqual(receipt["source_sha256"], source_sha)
        self.assertEqual(receipt["installed_sha256"], source_sha)

    def test_cli_conflict_has_nonzero_structured_result_and_zero_write(self) -> None:
        before = self.bytes_before()
        completed = subprocess.run(
            [*self.screen_cli(), "release-screen-cas", "--task", TASK,
             "--expected-sequence", "9", "--summary", "released"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(completed.returncode, 3)
        self.assertEqual(json.loads(completed.stdout)["code"], "CAS_CONFLICT")
        self.assertEqual(self.bytes_before(), before)

    def test_cli_register_conflict_and_legacy_non_screen_commands(self) -> None:
        before = self.bytes_before()
        blocked = subprocess.run(
            [*self.screen_cli(), "register", "--task", OTHER, "--summary", "other",
             "--resource", RESOURCE],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(blocked.returncode, 3)
        self.assertEqual(json.loads(blocked.stdout)["code"], "CAS_CONFLICT")
        self.assertEqual(self.bytes_before(), before)
        self.assertFalse(bus_module.task_path(self.bus, OTHER).exists())

        allowed = subprocess.run(
            [CLI_PYTHON, str(SOURCE), "--bus-dir", str(self.bus),
             "register", "--task", OTHER, "--summary", "ordinary",
             "--resource", "ordinary-resource"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        done = subprocess.run(
            [CLI_PYTHON, str(SOURCE), "--bus-dir", str(self.bus),
             "status", "--task", OTHER, "--state", "done"],
            capture_output=True, text=True, check=False, timeout=10,
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["task"]["resources"], [])


if __name__ == "__main__":
    unittest.main()

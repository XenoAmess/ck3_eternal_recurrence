"""RAM-only producer-to-consumer tests for normal saved-progress closure."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import unittest
from unittest.mock import patch

from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, evidence, parse_ref, record,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
from tools.g2_saved_campaign.test_current_saved_basis_v1 import pure_basis

UTC = "2026-10-22T03:00:00Z"
BIRTH = 134371098919795565


class MemoryReader:
    def __init__(self) -> None:
        self.raw: dict[str, bytes] = {}
        self.identities: dict[str, FileStatIdentityV1] = {}
        self.reads: list[str] = []

    def put(self, name: str, value: object) -> ExactRefV1:
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()
        ref = ExactRefV1("/synthetic/settled/" + name, len(raw), hashlib.sha256(raw).hexdigest())
        self.raw[ref.path] = raw
        self.identities[ref.path] = FileStatIdentityV1(len(raw), str(len(self.raw)), "1")
        return ref

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        if reference.path not in self.raw or reference.bytes > limit:
            raise ValueError("only bounded small metadata may be read")
        self.reads.append(reference.path)
        return self.raw[reference.path]

    def stat(self, path: str) -> FileStatIdentityV1:
        return self.identities[path]


class SettledFixture:
    def __init__(self) -> None:
        self.reader = r = MemoryReader()
        initial = pure_basis()
        machine = initial.machine_id
        processes: list[dict[str, object]] = [
            {"role": role, "pid": pid, "creation_filetime": BIRTH + pid,
             "executable": "/sdk/python.exe", "exit_code": 0,
             "kernel_exit_observed": True, "wait_result": 0, "observation_error": None}
            for role, pid in (("sdk_queue", 11), ("sdk_application", 12))]
        sdk = {"machine_id": machine, "status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED",
               "normal": True, "processes": processes}
        self.sdk = r.put("sdk.json", sdk)
        self.game = r.put("game.json", {"machine_id": machine, "pid": 10,
            "creation_filetime": BIRTH, "kernel_signaled": True, "exit_code": 1,
            "forced_owned_job_cleanup": True, "normal_wm_close_qualified": False})
        generation = {"pid": 10, "creation_filetime": BIRTH}
        self.supervisor = r.put("supervisor.json", {"machine_id": machine,
            "known_preload_phase": {"before": generation, "after": generation},
            "owned_cleanup": {"ck3_pid": 10, "ck3_creation_date": UTC, "ck3_exit_code": 1,
                "job_active_processes_final": 0, "tree_gone": True,
                "cleanup_proven": True, "ok": True, "contract_errors": []},
            "sdk_actual_exit": sdk,
            "keeper": {"task_id": "screen", "last_sequence": 20,
                       "thread_exited": True, "failure": None}})
        self.release = r.put("release.json", {"machine_id": machine, "returncode": 0,
            "stdout": json.dumps({"ok": True, "task": {"state": "done", "resources": [],
                "task_id": "screen", "last_sequence": 21}})})
        tasks: list[owner.SettledTaskClosureRefsV1] = []
        roles: tuple[owner.TaskRoleV1, ...] = ("supervisor", "display", "feeder")
        for role in roles:
            spec = r.put(role + "-spec.json", {"machine_id": machine, "nonce": role,
                "task_name": "XARG2ManagedOwner-" + role})
            closed = r.put(role + "-closed.json", {"machine_id": machine, "nonce": role,
                "spec_sha256": spec.sha256, "job_active_after_stage": 0,
                "forced_remaining_cleanup": False, "bootstrap_exit_code": 0, "child_exit_code": 0})
            unregistered = r.put(role + "-unregistered.json", {"machine_id": machine,
                "utc": UTC, "task_name": "XARG2ManagedOwner-" + role,
                "operation": "unregister", "actual": {"instances": 0,
                    "arguments": "python --spec-sha " + spec.sha256, "absent_after": True}})
            tasks.append(owner.SettledTaskClosureRefsV1(role, spec, closed, unregistered))
        self.tasks = tuple(tasks)
        self.review = self.review_value(owner.SETTLED_PROGRESS_REVIEW_SCHEMA)
        self.review_ref = r.put("review.json", self.review)
        self.closure = owner.SettledProgressClosureV1(machine, UTC,
            initial.completed_cycles, initial.frame.date_raw, initial.next_sequence,
            initial.origin.original_wall_origin_utc,
            owner.SettledProgressClosureRefsV1(self.sdk, self.supervisor, self.game,
                                              self.release, self.review_ref),
            self.tasks, 1, True, False)
        closure_ref = r.put("closure.json", self.closure.to_wire())
        self.basis = replace(initial, refs=replace(initial.refs,
            closure=closure_ref, driver_close=self.review_ref))
        r.identities[self.basis.refs.driver.path] = self.basis.driver_identity
        # Synthetic pure_basis uses one path for all original refs: distinguish the SAVE.
        save = replace(self.basis.refs.save, path="/synthetic/closed-save.ck3")
        self.basis = replace(self.basis, refs=replace(self.basis.refs, save=save),
                             checkpoint={**self.basis.checkpoint, "path": save.path})
        r.identities[save.path] = self.basis.save_identity
        self.review["SAVE"] = {"ref": save.to_wire(), "identity": self.basis.save_identity.to_wire()}
        self.reseal_review()

    def review_value(self, schema: str) -> dict[str, object]:
        basis = pure_basis()
        binding = {"pipe_name": "pipe", "bridge_pid": 10,
                   "episode_character_id": basis.frame.actor_character_id,
                   "episode_run_id": basis.frame.episode_run_id}
        return {"schema": schema, "status": "CLOSED_DRIVER_FINAL_SAVE_MATCH",
            "machine_id": basis.machine_id,
            "Driver": {"ref": basis.refs.driver.to_wire(), "identity": basis.driver_identity.to_wire(),
                "format_version": 2, "command_history_count": basis.checkpoint["history_index"],
                "recorded_identity": {**binding, "session_binding_observation":
                    {"present": True, "value": binding}}},
            "SAVE": {"ref": basis.refs.save.to_wire(), "identity": basis.save_identity.to_wire()},
            "frozen_settled_Queue": basis.refs.settled_state.to_wire(),
            "frozen_continuity_ledger": basis.refs.ledger.to_wire(),
            "actual_next": {"next_sequence": basis.next_sequence}}

    def reseal_review(self) -> None:
        self.review_ref = self.reader.put("review.json", self.review)
        self.closure = replace(self.closure,
            refs=replace(self.closure.refs, driver_review=self.review_ref))
        self.basis = replace(self.basis, refs=replace(self.basis.refs,
            driver_close=self.review_ref, closure=self.reader.put("closure.json", self.closure.to_wire())))

    def validate(self) -> owner.ClosedEpochV1:
        return owner._closed_epoch(self.basis, self.reader)


class SettledProgressClosureTests(unittest.TestCase):
    def test_copied_task_generation_at_distinct_paths_is_rejected(self) -> None:
        f = SettledFixture()
        original = f.tasks[0]
        copies: list[owner.SettledTaskClosureRefsV1] = []
        for task in f.tasks:
            copies.append(owner.SettledTaskClosureRefsV1(task.role,
                f.reader.put(task.role + "-copied-spec.json", evidence(f.reader, original.spec)),
                f.reader.put(task.role + "-copied-closed.json", evidence(f.reader, original.closed)),
                f.reader.put(task.role + "-copied-unregistered.json", evidence(f.reader, original.unregistered))))
        f.closure = replace(f.closure, tasks=tuple(copies))
        f.basis = replace(f.basis, refs=replace(f.basis.refs,
            closure=f.reader.put("closure.json", f.closure.to_wire())))
        self.assertEqual(len({task.spec.path for task in copies}), 3)
        self.assertEqual(len({task.spec.sha256 for task in copies}), 1)
        with self.assertRaisesRegex(ValueError, "three independent actual Task generations"):
            f.validate()

    def test_public_producer_json_closed_and_prepared_sdk_consumers(self) -> None:
        f = SettledFixture()
        parsed = owner.parse_settled_progress_closure_v1(
            json.loads(json.dumps(f.closure.to_wire())), expected_machine_id=f.basis.machine_id)
        self.assertEqual(parsed, f.closure)
        checked = f.validate()
        self.assertEqual(checked.old_game.creation_filetime, str(BIRTH))
        self.assertEqual({p.role: p.exit_code for p in checked.sdk_processes},
                         {"sdk_queue": 0, "sdk_application": 0})
        inputs = owner.CurrentSavedColdInputsV1(f.basis, {}, {}, {}, {}, checked,
                                               f.basis.refs.closure, f.basis.refs.closure)
        with patch.object(owner, "LocalBasisReaderV1", return_value=f.reader):
            result = owner.validate_current_saved_prepared_sdk_closure_v1(f.sdk.to_wire(), inputs=inputs)
        self.assertIs(result["normal"], True)
        self.assertTrue(f.closure.game_forced)
        self.assertFalse(f.closure.game_normal_close_qualified)
        self.assertNotIn(f.basis.refs.driver.path, f.reader.reads)
        self.assertNotIn(f.basis.refs.save.path, f.reader.reads)

    def test_exact_fields_missing_roles_and_wrong_scalar_types(self) -> None:
        f = SettledFixture()
        for key, value in (("completed_cycles", True), ("next_sequence", 103.0),
                           ("unknown_requests_replayed", None), ("machine_id", "wrong")):
            with self.subTest(key=key), self.assertRaises(ValueError):
                row: dict[str, object] = dict(f.closure.to_wire()); row[key] = value
                owner.parse_settled_progress_closure_v1(row, expected_machine_id=f.basis.machine_id)
        for key in f.closure.to_wire():
            row = dict(f.closure.to_wire()); del row[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                owner.parse_settled_progress_closure_v1(row, expected_machine_id=f.basis.machine_id)
        with self.assertRaises(ValueError):
            replace(f.closure, tasks=(f.tasks[0], f.tasks[0], f.tasks[2]))
        with self.assertRaises(ValueError):
            replace(f.closure, game_normal_close_qualified=True)

    def test_actual_sources_identity_and_progress_cannot_drift(self) -> None:
        for mutation in ("sdk", "driver", "save", "history", "next", "session", "task",
                         "task_bool", "task_machine", "task_nonce", "task_missing"):
            with self.subTest(mutation=mutation):
                f = SettledFixture()
                if mutation == "sdk":
                    value = evidence(f.reader, f.sdk)
                    process = record(value["processes"][0]) if isinstance(value["processes"], list) else {}
                    process["exit_code"] = 1
                    value["processes"] = [process, record(value["processes"][1])] if isinstance(value["processes"], list) else []
                    ref = f.reader.put("sdk.json", value)
                    f.closure = replace(f.closure, refs=replace(f.closure.refs, sdk_closed=ref))
                elif mutation in ("driver", "save"):
                    path = getattr(f.basis.refs, mutation).path
                    f.reader.identities[path] = replace(f.reader.identities[path], file_id="999")
                elif mutation == "history":
                    d = record(f.review["Driver"]); d["command_history_count"] = 2; f.review["Driver"] = d
                    f.reseal_review()
                elif mutation == "next":
                    f.closure = replace(f.closure, next_sequence=f.basis.next_sequence + 1)
                elif mutation == "session":
                    d = record(f.review["Driver"]); identity = record(d["recorded_identity"])
                    identity["session_binding_observation"] = {"present": True, "value": None}
                    d["recorded_identity"] = identity; f.review["Driver"] = d; f.reseal_review()
                else:
                    row = evidence(f.reader, f.tasks[0].unregistered)
                    if mutation == "task_machine": row["machine_id"] = "other-machine"
                    elif mutation == "task_nonce": row["task_name"] = "XARG2ManagedOwner-other"
                    elif mutation == "task_missing": del row["operation"]
                    else:
                        row["actual"] = {"instances": False if mutation == "task_bool" else 0.0,
                            "arguments": "--spec-sha " + f.tasks[0].spec.sha256, "absent_after": True}
                    task = replace(f.tasks[0], unregistered=f.reader.put("bad-unregistered.json", row))
                    f.closure = replace(f.closure, tasks=(task, *f.tasks[1:]))
                f.basis = replace(f.basis, refs=replace(f.basis.refs,
                    closure=f.reader.put("closure.json", f.closure.to_wire())))
                with self.assertRaises(ValueError): f.validate()

    def test_historical_a20_transport_keeps_original_guards(self) -> None:
        f = SettledFixture()
        sources: dict[str, object] = {"ROOT-P37C23-OWNER-CLOSED.json": f.sdk.to_wire(),
            "ROOT-FRESH-SUPERVISOR-CLOSED-C23-A15.json": f.supervisor.to_wire(),
            "ROOT-ACTUAL-GAME-EXIT-C23.json": f.game.to_wire(), "SCREEN-RELEASE.json": f.release.to_wire()}
        for task in f.tasks:
            sources[task.role + "_SPEC"] = task.spec.to_wire()
            sources[task.role + "_CLOSED"] = task.closed.to_wire()
            inner = evidence(f.reader, task.unregistered)
            outer = f.reader.put(task.role + "-legacy-unregister.json", {"machine_id": f.basis.machine_id,
                "returncode": 0, "command": ["python", "--spec", task.spec.path], "stdout": json.dumps(inner)})
            sources[task.role + "UNREGISTER01.json"] = outer.to_wire()
        f.review["schema"] = "xar.A20-final-Driver-SAVE-review/v2"
        for key in ("Driver", "SAVE"):
            row = record(f.review[key]); identity = record(row["identity"])
            row["identity"] = {**identity, "device": "1", "links": 1}; f.review[key] = row
        driver = record(f.review["Driver"]); recorded = record(driver["recorded_identity"])
        del recorded["session_binding_observation"]; driver["recorded_identity"] = recorded; f.review["Driver"] = driver
        f.reseal_review()
        legacy = {"schema": "xar.A20-actual-saved-progress-closure/v1", "machine_id": f.basis.machine_id,
            "observed_at_utc": UTC, "all_three_Tasks_actual_absent": True,
            "settled_cycles_after": f.basis.completed_cycles, "actual_final_date_raw": f.basis.frame.date_raw,
            "next_sequence": f.basis.next_sequence, "historical_unknown10565_replayed": False,
            "original_whole_wall_origin": f.basis.origin.original_wall_origin_utc,
            "sources": sources, "SDK_exit_codes": [0, 0], "SDK_normal": True,
            "Game_exit_code": 1, "Game_forced": True, "Game_normal_close_qualified": False,
            "Game_Job_active_final": 0}
        f.basis = replace(f.basis, refs=replace(f.basis.refs, closure=f.reader.put("legacy.json", legacy)))
        self.assertEqual(f.validate().old_game.pid, 10)
        recorded["session_binding"] = None; driver["recorded_identity"] = recorded
        f.review["Driver"] = driver
        review_ref = f.reader.put("review.json", f.review)
        f.basis = replace(f.basis, refs=replace(f.basis.refs, driver_close=review_ref))
        with self.assertRaises(ValueError): f.validate()


if __name__ == "__main__":
    unittest.main()

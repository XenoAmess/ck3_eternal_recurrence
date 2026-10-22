"""RAM-only producer-to-consumer tests for normal saved-progress closure."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest
from collections.abc import Callable
from unittest.mock import patch

from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, evidence, parse_ref, record, encode_current_saved_basis_v1,
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
        self.after_read: Callable[[str], None] | None = None

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
        if self.after_read is not None:
            self.after_read(reference.path)
        return self.raw[reference.path]

    def stat(self, path: str) -> FileStatIdentityV1:
        return self.identities[path]


class SettledFixture:
    def __init__(self, reader: MemoryReader | None = None) -> None:
        self.reader = r = MemoryReader() if reader is None else reader
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
        result = owner.validate_settled_progress_closure_v1(
            self.closure.to_wire(), basis=self.basis, reader=self.reader)
        if owner._closed_epoch(self.basis, self.reader) != result:
            raise AssertionError("closed consumer must retain the same historical evidence")
        return result


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
        self.assertEqual(owner._closed_epoch(f.basis, f.reader).old_game.pid, 10)
        recorded["session_binding"] = None; driver["recorded_identity"] = recorded
        f.review["Driver"] = driver
        review_ref = f.reader.put("review.json", f.review)
        f.basis = replace(f.basis, refs=replace(f.basis.refs, driver_close=review_ref))
        with self.assertRaises(ValueError): owner._closed_epoch(f.basis, f.reader)


class WarmMemoryReader(MemoryReader):
    def __init__(self) -> None:
        super().__init__()
        self.headers: dict[str, bytes] = {}
        self.processes: dict[int, JsonObject] = {}

    def read_driver_header(self, path: str, limit: int) -> bytes:
        if limit > 16384:
            raise ValueError("bounded current Driver header")
        return self.headers[path][:limit]

    def process_identity(self, pid: int) -> JsonObject:
        return self.processes[pid]


class NormalWarmFixture(SettledFixture):
    """Persist a new RAM Driver generation and feed the actual public warm consumer."""
    def __init__(self, *, persisted: bool = True) -> None:
        self.runtime_reader = r = WarmMemoryReader()
        super().__init__(r)
        life: JsonObject = {"schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "ordinary_campaign_succession", "xar_enabled": None,
            "pact_contract": "absent_by_verified_xar_mod_not_loaded",
            "source": "absent_by_verified_xar_mod_not_loaded", "environment_sha256": "e" * 64}
        self.basis = replace(self.basis, checkpoint={**self.basis.checkpoint, "succession_lifecycle": life})
        cp: JsonObject = {"status": "saved", "path": self.basis.refs.save.path,
            "name": "closed-save.ck3", "size": self.basis.refs.save.bytes,
            "sha256": self.basis.refs.save.sha256, "date_raw": self.basis.frame.date_raw,
            "history_index": 1, "episode_character_id": self.basis.frame.actor_character_id,
            "episode_run_id": self.basis.frame.episode_run_id, "succession_lifecycle": life}
        state: JsonObject = {"schema": "g2.queue.cumulative-loop/v1", "pending_cycle": None,
            "pending_checkpoint": None, "terminal": None, "completed_cycles": self.basis.completed_cycles,
            "start_date_raw": self.basis.origin.start_date_raw, "before": self.basis.frame.to_wire(),
            "campaign_goal_anchor": self.basis.campaign_goal_anchor, "actual_saved_checkpoint": cp,
            "counts": {"checkpoint_saved": self.basis.progress.checkpoint_count_after},
            "governance_result_state": None, "pending_focus": None}
        ledger: JsonObject = {"machine_id": self.basis.machine_id,
            "last_settled_cycles": self.basis.progress.ledger_cycles,
            "last_settled_date_raw": self.basis.progress.ledger_date_raw,
            "start_date_raw": self.basis.origin.start_date_raw, "target_date_raw": self.basis.origin.target_date_raw,
            "target_days": self.basis.origin.target_days}
        refs = replace(self.basis.refs, seed=r.put("seed.json", state),
            governance=r.put("governance.json", state), settled_state=r.put("state.json", state),
            ledger=r.put("ledger.json", ledger), checkpoint_validator=r.put("validator.json", {}))
        for name in ("semantic_response", "save_response", "settled_full_response", "origin_ledger", "wall_origin", "next"):
            refs = replace(refs, **{name: r.put(name + ".json", {})})
        self.basis = replace(self.basis, refs=refs)
        self.review["frozen_settled_Queue"] = refs.settled_state.to_wire()
        self.review["frozen_continuity_ledger"] = refs.ledger.to_wire()
        self.reseal_review()
        self.basis_ref = r.put("basis.json", json.loads(encode_current_saved_basis_v1(self.basis)))
        b = self.basis
        qualification = owner.BasisQualificationV1(b.machine_id, UTC, self.basis_ref,
            b.refs.driver, b.refs.save, b.driver_identity, b.driver_identity, b.save_identity,
            b.save_identity, b.refs.checkpoint_validator, 1, 1, 1, 1)
        self.validation_ref = r.put("qualification.json", qualification.to_wire())
        self.root = Path("/synthetic/settled")
        self.game_identity = owner.CurrentGameIdentityV1(30, str(BIRTH + 100), UTC)
        game_ref = r.put("ROOT-ACTUAL-GAME-LAUNCH-C23.json", {"machine_id": b.machine_id,
            **self.game_identity.to_wire(), "command": ["/game/ck3.exe"]})
        r.processes[30] = {"pid": 30, "creation_filetime": str(BIRTH + 100), "executable": "/game/ck3.exe"}
        pair_rows: list[JsonObject] = []
        for role, pid in (("sdk_queue", 31), ("sdk_application", 32)):
            row: JsonObject = {"role": role, "pid": pid, "creation_filetime": str(BIRTH + pid), "executable": "/sdk/python.exe"}
            pair_rows.append(row); r.processes[pid] = row
        pair_ref = r.put("ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json", {
            "machine_id": b.machine_id, "status": "SDK_PAIR_HANDLES_RETAINED", "rpc_started": False,
            "at_utc": UTC, "processes": pair_rows})
        diagnostics: JsonObject = {"bridge_pid": 30, "pipe_name": "pipe", "connection_generation": 1,
            "hello": {"pid": 30, "connection_generation": 1, "ck3_build_match": True,
                "game_adapter_id": "ck3-1.20.0.4-msvc-x64", "game_adapter_status": "ready"}}
        semantic: JsonObject = {**b.frame.to_wire(), "episode_character_id": b.frame.actor_character_id,
            "episode_run_id": b.frame.episode_run_id, "succession_lifecycle": life,
            "diagnostics": diagnostics, "map_ready": True, "paused": True,
            "campaign_goal": b.campaign_goal_anchor, "active_event": None, "pending_character_interaction": None}
        capability: JsonObject = {"episode_character_id": b.frame.actor_character_id,
            "episode_run_id": b.frame.episode_run_id, "episode_identity_pending": False,
            "one_life_terminal": False, "diagnostics": diagnostics,
            "native_session_control": {"configured": True, "restore_checkpoint": True,
                "driver_state_restored": True, "driver_state_restore_kind": "cold_checkpoint",
                "episode_binding_state": "active_resumed", "driver_state_error": None,
                "cold_candidate_rejection": None, "driver_state_path": b.refs.driver.path},
            "checkpoint_materialization": {"configured": True, "save_dir": str(Path(b.refs.save.path).parent),
                "filename": Path(b.refs.save.path).name}}
        sem_ref = self.response(b.next_sequence, "ck3_take_semantic_snapshot_private_v1", semantic)
        cap_ref = self.response(b.next_sequence + 1, "ck3_get_capabilities", capability)
        bound_ref = r.put("p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json", {
            "machine_id": b.machine_id, "schema": "xar.c23.normal-checkpoint-cold-bound/v1",
            "observed_at_utc": UTC, "opening_frame": b.frame.to_wire(), "checkpoint": cp,
            "completed_cycles": b.completed_cycles, "T0_date_raw": b.origin.start_date_raw,
            "new_ordinary_cycle_credit": 0, "AUTO_or_MET_replayed": False, "semantic_response": sem_ref.path})
        cold_ref = r.put("ROOT-P37C23-COLD-RESUME-ADMISSION.json", {"machine_id": b.machine_id,
            "basis_ref": self.basis_ref.to_wire(), "validation_ref": self.validation_ref.to_wire(),
            "new_Game": self.game_identity.to_wire()})
        self.sources = owner.WarmSourceRefsV1(game_ref, pair_ref, sem_ref, cap_ref, bound_ref, cold_ref)
        header: dict[str, object] = {"format_version": 2, "pipe_name": "pipe", "bridge_pid": 30,
            "episode_character_id": b.frame.actor_character_id, "episode_run_id": b.frame.episode_run_id,
            "last_checkpoint": cp, "command_history": []}
        raw = json.dumps(header, separators=(",", ":")).encode()
        r.headers[b.refs.driver.path] = raw
        if persisted:
            r.identities[b.refs.driver.path] = FileStatIdentityV1(len(raw), "999999", "2")

    def response(self, sequence: int, tool: str, body: JsonObject) -> ExactRefV1:
        return self.reader.put(f"p37-responses/{sequence:04d}-1-result.json", {
            "request": {"sequence": sequence, "tool": tool}, "started_at_utc": UTC,
            "ended_at_utc": UTC, "result": {"is_error": False, "result_type": "complete", "structured_content": body}})

    def warm(self) -> owner.WarmCurrentSavedFeederInputsV1:
        return owner.validate_current_saved_warm_inputs_v1(self.basis, basis_ref=self.basis_ref,
            validation_ref=self.validation_ref, sources=self.sources, reader=self.runtime_reader,
            runtime_root=self.root)


class NormalClosureWarmTests(unittest.TestCase):
    def test_cold_save_identity_is_rechecked_after_immutable_and_closure_reads(self) -> None:
        for last_read in ("seed", "task"):
            with self.subTest(last_read=last_read):
                f = NormalWarmFixture(persisted=False)
                trigger = f.basis.refs.seed.path if last_read == "seed" else f.tasks[-1].unregistered.path

                def changed_file(path: str) -> None:
                    if path == trigger:
                        f.reader.identities[f.basis.refs.save.path] = replace(f.basis.save_identity, file_id="777777")

                f.reader.after_read = changed_file
                with self.assertRaisesRegex(ValueError, "stable closed Driver/SAVE"):
                    owner.validate_current_saved_cold_inputs_v1(f.basis, basis_ref=f.basis_ref,
                        validation_ref=f.validation_ref, reader=f.runtime_reader)

    def test_actual_warm_consumer_accepts_new_driver_and_cold_rejects(self) -> None:
        f = NormalWarmFixture()
        with self.assertRaisesRegex(ValueError, "closed Driver"):
            owner.validate_current_saved_cold_inputs_v1(f.basis, basis_ref=f.basis_ref,
                validation_ref=f.validation_ref, reader=f.runtime_reader)
        result = f.warm()
        self.assertTrue(result.warm_proof.closed_driver_identity_replaced)
        self.assertEqual(result.warm_proof.sources, f.sources)
        self.assertNotEqual(result.warm_proof.driver_identity, f.basis.driver_identity)
        self.assertNotIn(f.basis.refs.driver.path, f.reader.reads)
        self.assertNotIn(f.basis.refs.save.path, f.reader.reads)

    def test_wrong_bound_source_or_current_header_is_rejected(self) -> None:
        for mutation in ("bound", "source", "header"):
            with self.subTest(mutation=mutation):
                f = NormalWarmFixture()
                if mutation == "bound":
                    row = evidence(f.reader, f.sources.cold_bound_ref)
                    row["completed_cycles"] = f.basis.completed_cycles + 1
                    f.sources = replace(f.sources, cold_bound_ref=f.reader.put("p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json", row))
                elif mutation == "source":
                    f.sources = replace(f.sources, semantic_response_ref=f.reader.put("wrong-response.json", {}))
                else:
                    f.runtime_reader.headers[f.basis.refs.driver.path] = f.runtime_reader.headers[f.basis.refs.driver.path].replace(b'"bridge_pid":30', b'"bridge_pid":31')
                with self.assertRaises(ValueError): f.warm()


if __name__ == "__main__":
    unittest.main()

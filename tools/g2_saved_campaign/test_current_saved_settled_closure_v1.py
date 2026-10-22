"""RAM-only producer-to-consumer tests for normal saved-progress closure."""
from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
from pathlib import Path
import unittest
from collections.abc import Callable, Iterator
from contextlib import contextmanager, nullcontext
from unittest.mock import Mock, patch
from functools import lru_cache

from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign import current_saved_continuity_v1 as continuity
from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, JsonValue, CurrentSavedBasisV1, MAX_ORIGINAL_RESPONSE_BYTES_V1,
    BasisReaderV1, ValidatedCurrentSavedBasisV1, text, need,
    evidence, parse_ref, record, rows, json_object, integer, encode_current_saved_basis_v1,
    decode_readonly_prefix_history_v1, _exact_native_json_v1, MAX_SDK_SOURCE_BYTES_V1,
    exact_sdk_source_bytes_v1,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
from tools.g2_saved_campaign.test_current_saved_basis_v1 import pure_basis

UTC = "2026-10-22T03:00:00Z"
BIRTH = 134371098919795565


@dataclass(frozen=True, slots=True)
class SavedBusinessPriorV1:
    """A real canonical fixture measurement with its original business evidence reader."""
    validated: ValidatedCurrentSavedBasisV1
    reader: BasisReaderV1
    pipe_name: str

    def __post_init__(self) -> None:
        text(self.pipe_name)


class MemoryReader:
    def __init__(self, metadata_root: Path | None = None, *, source_reader: BasisReaderV1 | None = None) -> None:
        self.source_reader = source_reader
        self.metadata_root = Path("/synthetic/settled") if metadata_root is None else metadata_root
        self.raw: dict[str, bytes] = {}
        self.identities: dict[str, FileStatIdentityV1] = {}
        self.reads: list[str] = []
        self.after_read: Callable[[str], None] | None = None

    def put(self, name: str, value: object) -> ExactRefV1:
        raw = json.dumps(value, sort_keys=True, allow_nan=False).encode()
        ref = ExactRefV1(str(self.metadata_root / name), len(raw), hashlib.sha256(raw).hexdigest())
        self.raw[ref.path] = raw
        self.identities[ref.path] = FileStatIdentityV1(len(raw), str(len(self.raw)), "1")
        return ref

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        if reference.bytes > limit:
            raise ValueError("only bounded small metadata may be read")
        if reference.path not in self.raw:
            if self.source_reader is None:
                raise ValueError("bounded fixture source missing")
            self.reads.append(reference.path)
            return self.source_reader.read(reference, limit)
        self.reads.append(reference.path)
        if self.after_read is not None:
            self.after_read(reference.path)
        return self.raw[reference.path]

    def read_response(self, reference: ExactRefV1, limit: int) -> bytes:
        if type(limit) is not int or not 0 < limit <= MAX_ORIGINAL_RESPONSE_BYTES_V1:
            raise ValueError("bounded original response")
        return self.read(reference, limit)

    def read_sdk_source(self, reference: ExactRefV1, limit: int) -> bytes:
        integer(limit, 1, MAX_SDK_SOURCE_BYTES_V1)
        if reference.bytes > limit:
            raise ValueError("bounded original SDK source")
        return self.read(reference, limit)

    def stat(self, path: str) -> FileStatIdentityV1:
        if path not in self.identities and self.source_reader is not None:
            return self.source_reader.stat(path)
        return self.identities[path]


class SettledFixture:
    def __init__(self, reader: MemoryReader | None = None, *, pipe_name: str = "pipe") -> None:
        self.pipe_name = text(pipe_name)
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
        save = (replace(self.basis.refs.save, path="/synthetic/closed-save.ck3")
                if self.basis.refs.save.path == self.basis.refs.driver.path else self.basis.refs.save)
        self.basis = replace(self.basis, refs=replace(self.basis.refs, save=save),
                             checkpoint={**self.basis.checkpoint, "path": save.path})
        r.identities[save.path] = self.basis.save_identity
        self.review["SAVE"] = {"ref": save.to_wire(), "identity": self.basis.save_identity.to_wire()}
        self.reseal_review()

    def review_value(self, schema: str) -> dict[str, object]:
        basis = pure_basis()
        binding = {"pipe_name": self.pipe_name, "bridge_pid": 10,
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
        self.assertEqual(owner.resolve_current_saved_closed_sdk_ref_v1(inputs, reader=f.reader), f.sdk)
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
        checked = owner._closed_epoch(f.basis, f.reader)
        self.assertEqual(checked.old_game.pid, 10)
        inputs = owner.CurrentSavedColdInputsV1(f.basis, {}, {}, {}, {}, checked,
                                               f.basis.refs.closure, f.basis.refs.closure)
        self.assertEqual(owner.resolve_current_saved_closed_sdk_ref_v1(inputs, reader=f.reader), f.sdk)
        recorded["session_binding"] = None; driver["recorded_identity"] = recorded
        f.review["Driver"] = driver
        review_ref = f.reader.put("review.json", f.review)
        f.basis = replace(f.basis, refs=replace(f.basis.refs, driver_close=review_ref))
        with self.assertRaises(ValueError): owner._closed_epoch(f.basis, f.reader)


class WarmMemoryReader(MemoryReader):
    def __init__(self, metadata_root: Path | None = None, *, source_reader: BasisReaderV1 | None = None) -> None:
        super().__init__(metadata_root, source_reader=source_reader)
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
    def __init__(self, *, persisted: bool = True, campaign_days: int | None = None,
                 metadata_root: Path | None = None, validator_source: ExactRefV1 | None = None,
                 saved_prior: SavedBusinessPriorV1 | None = None) -> None:
        self.runtime_reader = r = WarmMemoryReader(metadata_root,
            source_reader=None if saved_prior is None else saved_prior.reader)
        super().__init__(r, pipe_name="pipe" if saved_prior is None else saved_prior.pipe_name)
        life: JsonValue
        cp: JsonObject
        if saved_prior is None:
            if campaign_days is not None:
                days = integer(campaign_days, 1)
                self.basis = replace(self.basis, origin=replace(self.basis.origin,
                    target_days=days, target_date_raw=self.basis.origin.start_date_raw + days * 24))
            life = {"schema": "xar.ck3.succession-lifecycle-binding/v1",
                "lifecycle": "ordinary_campaign_succession", "xar_enabled": None,
                "pact_contract": "absent_by_verified_xar_mod_not_loaded",
                "source": "absent_by_verified_xar_mod_not_loaded", "environment_sha256": "e" * 64}
            self.basis = replace(self.basis, checkpoint={**self.basis.checkpoint, "succession_lifecycle": life})
            cp = {"status": "saved", "path": self.basis.refs.save.path,
                "name": Path(self.basis.refs.save.path).name, "size": self.basis.refs.save.bytes,
                "sha256": self.basis.refs.save.sha256, "date_raw": self.basis.frame.date_raw,
                "history_index": 1, "episode_character_id": self.basis.frame.actor_character_id,
                "episode_run_id": self.basis.frame.episode_run_id, "succession_lifecycle": life}
            state: JsonObject = {"schema": "g2.queue.cumulative-loop/v1", "pending_cycle": None,
                "pending_checkpoint": None, "terminal": None, "completed_cycles": self.basis.completed_cycles,
                "start_date_raw": self.basis.origin.start_date_raw, "before": self.basis.frame.to_wire(),
                "campaign_goal_anchor": self.basis.campaign_goal_anchor, "actual_saved_checkpoint": cp,
                "counts": {"checkpoint_saved": self.basis.progress.checkpoint_count_after},
                "governance_result_state": None, "pending_focus": None}
            ledger: JsonObject = {"schema": "root.ck3.continuity-window/v1",
                "sequence": 1, "window_id": 1, "status": "running", "machine_id": self.basis.machine_id,
                "game_binding": {"pid": 10, "creation_date": UTC}, "cold_handoff_count": 0,
                "manual_repair_count": 0, "automatic_recovery_count": 0, "binding_lineage_count": 0,
                "last_settled_cycles": self.basis.progress.ledger_cycles,
                "last_settled_date_raw": self.basis.progress.ledger_date_raw,
                "start_date_raw": self.basis.origin.start_date_raw, "target_date_raw": self.basis.origin.target_date_raw,
                "target_days": self.basis.origin.target_days}
            refs = replace(self.basis.refs, seed=r.put("seed.json", state),
                governance=r.put("governance.json", state), settled_state=r.put("state.json", state),
                ledger=r.put("ledger.json", ledger), checkpoint_validator=r.put("validator.json", {}) if validator_source is None else validator_source)
            for name in ("semantic_response", "save_response", "settled_full_response", "origin_ledger", "wall_origin", "next"):
                refs = replace(refs, **{name: r.put(name + ".json", {})})
            self.basis = replace(self.basis, refs=refs)
        else:
            if self.basis.origin.target_days != 10958:
                raise ValueError("complete saved prior must already have the original 30-year policy")
            cp = json_object(evidence(r, self.basis.refs.seed)["actual_saved_checkpoint"])
            life = cp.get("succession_lifecycle")
        refs = self.basis.refs
        self.review["frozen_settled_Queue"] = refs.settled_state.to_wire()
        self.review["frozen_continuity_ledger"] = refs.ledger.to_wire()
        self.reseal_review()
        self.basis_ref = r.put("basis.json", json.loads(encode_current_saved_basis_v1(self.basis)))
        b = self.basis
        qualification = (owner.BasisQualificationV1(b.machine_id, UTC, self.basis_ref,
            b.refs.driver, b.refs.save, b.driver_identity, b.driver_identity, b.save_identity,
            b.save_identity, b.refs.checkpoint_validator, 1, 1, 1, 1)
            if saved_prior is None else owner.build_basis_qualification_v1(
                replace(saved_prior.validated, basis=b), basis_ref=self.basis_ref,
                reader=r, observed_at_utc=UTC))
        self.validation_ref = r.put("qualification.json", qualification.to_wire())
        self.root = Path("/synthetic/settled") if metadata_root is None else metadata_root
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
        diagnostics: JsonObject = {"bridge_pid": 30, "pipe_name": self.pipe_name, "connection_generation": 1,
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
        header: dict[str, object] = {"format_version": 2, "pipe_name": self.pipe_name, "bridge_pid": 30,
            "episode_character_id": b.frame.actor_character_id, "episode_run_id": b.frame.episode_run_id,
            "last_checkpoint": cp, "command_history": []}
        raw = json.dumps(header, separators=(",", ":")).encode()
        r.headers[b.refs.driver.path] = raw
        if persisted:
            r.identities[b.refs.driver.path] = FileStatIdentityV1(len(raw), "999999", "2")

    def response(self, sequence: int, tool: str, body: JsonObject) -> ExactRefV1:
        return self.reader.put(f"p37-responses/{sequence:04d}-1-result.json", {
            "request": {"sequence": sequence, "tool": tool, "arguments": {}}, "started_at_utc": UTC,
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


class ReadinessOnlyFixture:
    """A saved normal epoch, a closed readiness epoch, then a fresh warm epoch."""
    def __init__(self, prior: NormalWarmFixture | None = None) -> None:
        self.prior = f = NormalWarmFixture() if prior is None else prior
        self.reader = r = f.runtime_reader
        old = f.basis
        cp = record(evidence(r, old.refs.seed)["actual_saved_checkpoint"])
        self.restore: dict[str, object] = {"index": 2, "command": "restore-checkpoint", "ok": True,
            "result": {"step": "restore-checkpoint", "accepted": True, "status": "restored",
                "backend_id": "native-headless", "source": "native-session-cold-start",
                "checkpoint": cp, "restored_date_raw": old.frame.date_raw, "map_ready": True,
                "lifecycle": {"previous_pid": 10, "pid": 30}}}
        payload = record(json.loads(r.headers[old.refs.driver.path]))
        payload['succession_lifecycle'] = cp['succession_lifecycle']
        payload["command_history"] = [{"index": 1, "command": "save-checkpoint", "ok": True,
            "result": {"checkpoint": cp}}, self.restore]
        raw = json.dumps(payload, sort_keys=False, separators=(",", ":")).encode()
        self.driver_ref = ExactRefV1(old.refs.driver.path, len(raw), hashlib.sha256(raw).hexdigest())
        r.raw[self.driver_ref.path] = raw
        r.headers[self.driver_ref.path] = raw
        driver_identity = FileStatIdentityV1(len(raw), "999999", "2")
        r.identities[self.driver_ref.path] = driver_identity
        sdk = {"machine_id": old.machine_id, "status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED", "normal": True,
            "processes": [{**process, "exit_code": 0, "kernel_exit_observed": True,
                "wait_result": 0, "observation_error": None}
                for process in (record(v) for v in rows(evidence(r, f.sources.sdk_pair_ref)["processes"]))]}
        sdk_ref = r.put("ready-sdk.json", sdk)
        game_ref = r.put("ready-game.json", {"machine_id": old.machine_id, **f.game_identity.to_wire(),
            "kernel_signaled": True, "exit_code": 1, "forced_owned_job_cleanup": True,
            "normal_wm_close_qualified": False})
        supervisor = evidence(r, f.supervisor)
        supervisor["known_preload_phase"] = {"before": f.game_identity.to_wire(), "after": f.game_identity.to_wire()}
        owned = record(supervisor["owned_cleanup"]); owned["ck3_pid"] = f.game_identity.pid
        supervisor["owned_cleanup"] = owned; supervisor["sdk_actual_exit"] = sdk
        supervisor_ref = r.put("ready-supervisor.json", supervisor)
        tasks: list[owner.SettledTaskClosureRefsV1] = []
        for task in f.tasks[:2]:
            nonce = "ready-" + task.role
            spec = r.put(nonce + "-spec.json", {"machine_id": old.machine_id,
                "nonce": nonce, "task_name": "XARG2ManagedOwner-" + nonce})
            closed = r.put(nonce + "-closed.json", {"machine_id": old.machine_id,
                "nonce": nonce, "spec_sha256": spec.sha256, "job_active_after_stage": 0,
                "forced_remaining_cleanup": False, "bootstrap_exit_code": 0, "child_exit_code": 0})
            unregistered = r.put(nonce + "-unregistered.json", {"machine_id": old.machine_id,
                "utc": UTC, "task_name": "XARG2ManagedOwner-" + nonce, "operation": "unregister",
                "actual": {"instances": 0, "arguments": "--spec-sha " + spec.sha256, "absent_after": True}})
            tasks.append(owner.SettledTaskClosureRefsV1(task.role, spec, closed, unregistered))
        next_ref = r.put("ready-NEXT.json", {"next_sequence": old.next_sequence + 2})
        entries: list[dict[str, object]] = []
        for sequence, tool, response_ref in (
                (old.next_sequence, "ck3_take_semantic_snapshot_private_v1", f.sources.semantic_response_ref),
                (old.next_sequence + 1, "ck3_get_capabilities", f.sources.capabilities_response_ref)):
            request_ref = r.put(f"p37-requests/{sequence:04d}-1-result.json", evidence(r, response_ref)["request"])
            after: dict[str, object] = {"at_utc": UTC, "request": request_ref.path,
                "response": response_ref.path, "tool": tool}
            if sequence == old.next_sequence:
                after.update(actual_status="cold_readiness_verified", loading_attempts=0, new_business_credit=0)
            else:
                after.update(actual_status=None, selected_step=None, checkpoint_status=None)
            after_ref = r.put(f"p37-queue/{sequence:04d}-after-result.json", after)
            entries.append({"sequence": sequence, "tool": tool, "request_ref": request_ref.to_wire(),
                "response_ref": response_ref.to_wire(), "after_ref": after_ref.to_wire()})
        self.inventory: dict[str, object] = {"schema": "xar.current-saved-readiness-request-inventory/v1",
            "machine_id": old.machine_id, "observed_at_utc": UTC, "runtime_root": str(f.root),
            "entries": entries, "unused_next": {"ref": next_ref.to_wire(), "sequence": old.next_sequence + 2,
                "request_absent": True, "response_absent": True}, "other_request_entries": [],
            "failure_flags": {"failed_flag_present": False, "halt_present": False, "first_exception_present": False}}
        self.tail: dict[str, object] = {"schema": "xar.current-saved-readiness-driver-tail/v1",
            "machine_id": old.machine_id, "observed_at_utc": UTC, "prior_driver_ref": old.refs.driver.to_wire(),
            "driver_ref": self.driver_ref.to_wire(), "prior_history_count": 1, "command_history_count": 2,
            "prior_post_checkpoint_sha256": hashlib.sha256(b"[]").hexdigest(), "post_prior_history": [self.restore]}
        prior_inputs = owner.validate_current_saved_warm_inputs_v1(old, basis_ref=f.basis_ref,
            validation_ref=f.validation_ref, sources=f.sources, reader=r, runtime_root=f.root).inputs
        state = owner.project_current_saved_opening_v1(prior_inputs, old.frame,
            semantic_response=f.sources.semantic_response_ref)
        self.proof = owner.ReadinessClosureProofV2(f.basis_ref, f.validation_ref, f.sources,
            r.put("readiness-state.json", state), r.put("inventory.json", self.inventory), r.put("tail.json", self.tail))
        self.review = f.review_value(owner.NORMAL_REVIEW_SCHEMA_V2)
        self.review.update(machine_id=old.machine_id,
            status="CLOSED_DRIVER_SAVED_CHECKPOINT_VALIDATED", phase="readiness_only")
        d = record(self.review["Driver"])
        d.update(ref=self.driver_ref.to_wire(), identity=driver_identity.to_wire(), command_history_count=2,
            last_checkpoint=cp, recorded_identity={"pipe_name": f.pipe_name, "bridge_pid": f.game_identity.pid,
                "episode_character_id": old.frame.actor_character_id, "episode_run_id": old.frame.episode_run_id,
                "session_binding_observation": {"present": False, "value": None}})
        self.review["Driver"] = d
        self.review["SAVE"] = {"ref": old.refs.save.to_wire(), "identity": old.save_identity.to_wire()}
        self.review["frozen_settled_Queue"] = self.proof.loop_state_ref.to_wire()
        self.review["frozen_continuity_ledger"] = old.refs.ledger.to_wire()
        self.review["actual_next"] = {"next_sequence": old.next_sequence + 2}
        self.closure = owner.NormalClosureV2(old.machine_id, UTC, old.completed_cycles,
            old.frame.date_raw, old.next_sequence + 2, old.origin.original_wall_origin_utc,
            owner.SettledProgressClosureRefsV1(sdk_ref, supervisor_ref, game_ref, f.release,
                r.put("ready-review.json", self.review)), tuple(tasks), 1, True, False, "readiness_only", self.proof)
        self.basis = replace(old, observed_at_utc=UTC, driver_identity=driver_identity,
            next_sequence=old.next_sequence + 2, refs=replace(old.refs, driver=self.driver_ref,
                driver_close=self.closure.refs.driver_review, closure=r.put("ready-closure.json", self.closure.to_wire()), next=next_ref))
        self.reseal()

    def reseal(self) -> None:
        r = self.reader
        self.proof = replace(self.proof, inventory_ref=r.put("inventory.json", self.inventory),
                             history_tail_ref=r.put("tail.json", self.tail))
        self.closure = replace(self.closure, readiness=self.proof,
            refs=replace(self.closure.refs, driver_review=r.put("ready-review.json", self.review)))
        self.basis = replace(self.basis, refs=replace(self.basis.refs,
            driver_close=self.closure.refs.driver_review, closure=r.put("ready-closure.json", self.closure.to_wire())))
        self.basis_ref = r.put("ready-basis.json", json.loads(encode_current_saved_basis_v1(self.basis)))
        b = self.basis
        qualification = owner.BasisQualificationV1(b.machine_id, UTC, self.basis_ref,
            b.refs.driver, b.refs.save, b.driver_identity, b.driver_identity, b.save_identity,
            b.save_identity, b.refs.checkpoint_validator, 2, 1, 1, 1)
        self.validation_ref = r.put("ready-qualification.json", qualification.to_wire())

    def cold(self) -> owner.CurrentSavedColdInputsV1:
        return owner.validate_current_saved_cold_inputs_v1(self.basis, basis_ref=self.basis_ref,
            validation_ref=self.validation_ref, reader=self.reader)

    def next_warm(self, game_pid: int = 40) -> owner.WarmCurrentSavedFeederInputsV1:
        r = self.reader
        root = self.prior.root / "next-runtime"
        game = replace(self.prior.game_identity, pid=game_pid, creation_filetime=str(BIRTH + game_pid + 200))
        game_ref = r.put("next-runtime/ROOT-ACTUAL-GAME-LAUNCH-C23.json", {
            "machine_id": self.basis.machine_id, **game.to_wire(), "command": ["/game/ck3.exe"]})
        r.processes[game_pid] = {"pid": game_pid, "creation_filetime": game.creation_filetime, "executable": "/game/ck3.exe"}
        pair = evidence(r, self.prior.sources.sdk_pair_ref)
        processes: list[JsonObject] = []
        for role, pid in (("sdk_queue", game_pid + 1), ("sdk_application", game_pid + 2)):
            process: JsonObject = {"role": role, "pid": pid, "creation_filetime": str(BIRTH + pid), "executable": "/sdk/python.exe"}
            processes.append(process); r.processes[pid] = process
        pair["processes"] = processes
        pair_ref = r.put("next-runtime/ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json", pair)
        responses: list[ExactRefV1] = []
        for index, source in enumerate((self.prior.sources.semantic_response_ref, self.prior.sources.capabilities_response_ref)):
            row = evidence(r, source)
            request = record(row["request"]); request["sequence"] = self.basis.next_sequence + index; row["request"] = request
            result = record(row["result"]); body = record(result["structured_content"])
            diag = record(body["diagnostics"]); hello = record(diag["hello"])
            diag["bridge_pid"] = game_pid; diag["connection_generation"] = 2
            hello["pid"] = game_pid; hello["connection_generation"] = 2
            diag["hello"] = hello; body["diagnostics"] = diag
            result["structured_content"] = body; row["result"] = result
            responses.append(r.put(f"next-runtime/p37-responses/{self.basis.next_sequence + index:04d}-1-result.json", row))
        marker = evidence(r, self.prior.sources.cold_bound_ref)
        marker["semantic_response"] = responses[0].path
        bound_ref = r.put("next-runtime/p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json", marker)
        cold_ref = r.put("next-runtime/ROOT-P37C23-COLD-RESUME-ADMISSION.json", {
            "machine_id": self.basis.machine_id, "basis_ref": self.basis_ref.to_wire(),
            "validation_ref": self.validation_ref.to_wire(), "new_Game": game.to_wire()})
        sources = owner.WarmSourceRefsV1(game_ref, pair_ref, responses[0], responses[1], bound_ref, cold_ref)
        payload = record(json.loads(r.headers[self.basis.refs.driver.path])); payload["bridge_pid"] = game_pid
        raw = json.dumps(payload, separators=(",", ":")).encode()
        r.headers[self.basis.refs.driver.path] = raw
        r.identities[self.basis.refs.driver.path] = FileStatIdentityV1(len(raw), "1000000", "3")
        return owner.validate_current_saved_warm_inputs_v1(self.basis, basis_ref=self.basis_ref,
            validation_ref=self.validation_ref, sources=sources, reader=r, runtime_root=root)


@lru_cache(maxsize=1)
def _full_failure_original_sdk_bytes_v1() -> bytes:
    import subprocess
    commit = '6f58f72a8ff29d85f8751d3bfb1667b38f9497df'
    tag = subprocess.run(['git', 'rev-parse', '--verify', 'refs/tags/archive/robert-source32-6f58f72a8-20261022'],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, check=False)
    need(tag.returncode == 0 and tag.stdout.strip() == commit.encode(), 'published exact original Source32 archive tag')
    with subprocess.Popen(['git', 'show', commit + ':ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'],
            cwd=Path(__file__).resolve().parents[2], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        if process.stdout is None: raise ValueError('bounded original SDK source pipe')
        raw = process.stdout.read(2097153)
        if len(raw) > 2097152:
            process.kill(); process.wait(); raise ValueError('original SDK source cap')
        need(process.wait(timeout=30) == 0 and len(raw) == 1648649 and hashlib.sha256(raw).hexdigest() ==
            '15a1eca3cee4f79be51a4144258650822e49146c93b7a87257319f848928d06b', 'complete original Source32 SDK source')
    return raw


class FullPreDispatchFailureFixture:
    """A closed original Queue map refusal after a genuine SEM/CAP prefix."""
    def __init__(self, prior: NormalWarmFixture | None = None) -> None:
        from tools.g2_saved_campaign.test_current_saved_campaign_cold_v1 import _actual_map_queue_whole_v1
        self.ready = f = ReadinessOnlyFixture(prior)
        self.reader = r = f.reader
        self.prior = owner._validated_immutable_inputs_v1(f.prior.basis,
            basis_ref=f.proof.prior_basis_ref, validation_ref=f.proof.prior_validation_ref, reader=r)
        root = Path(f.proof.sources.actual_game_ref.path).parent
        sequence = f.basis.next_sequence
        self.request: dict[str, object] = {'sequence': sequence, 'command': 'full_loop', 'arguments': {'max_turns': 30}}
        self.request_ref = r.put(str(root / f'p37-requests/{sequence:04d}-1-result.json'), self.request)
        self.message = 'Root must review the new actual map and overlay before initial SAVE'
        self.response: dict[str, object] = {'ended_at_utc': UTC, 'request': self.request,
            'client_error': self.message, 'replay_allowed': False, 'original_response': None,
            'full_rpc_rows_v1': {'schema': 'xar.ck3.full-existing-rpc-rows/v1', 'control_sequence': sequence,
                'row_count': 0, 'duplicate_rows_ignored': 0, 'invalid_elapsed_rows': 0,
                'elapsed_seconds_sum': 0.0, 'interval_union_seconds': 0, 'overlap_seconds': 0.0,
                'tools': {name: {'count': 0, 'elapsed_seconds_sum': 0.0,
                    'error_count': 0, 'client_error_count': 0} for name in ('AUTO', 'MET', 'SEM', 'SAVE')}}}
        self.response_ref = r.put(str(root / f'p37-responses/{sequence:04d}-1-result.json'), self.response)
        raw = _actual_map_queue_whole_v1()
        self.queue_ref = ExactRefV1(str(root / 'root_p37c23_sdk_queue.py'), len(raw), hashlib.sha256(raw).hexdigest())
        r.raw[self.queue_ref.path] = raw
        r.identities[self.queue_ref.path] = FileStatIdentityV1(len(raw), '2000000', '4')
        import ast
        raises = [node for node in ast.walk(ast.parse(raw)) if isinstance(node, ast.Raise)
            and isinstance(node.exc, ast.Call) and node.exc.args and isinstance(node.exc.args[0], ast.Constant)
            and node.exc.args[0].value == self.message]
        assert len(raises) == 1
        self.exception: dict[str, object] = {'at_utc': UTC, 'stage': 'request_dispatch', 'replay_allowed': False,
            'exception_tree': {'type': 'ValueError', 'message': self.message}, 'traceback_truncated': False,
            'locals_captured': False, 'request_identity': {'sequence': sequence, 'tool': None, 'command': 'full_loop'},
            'traceback': f'File "{self.queue_ref.path}", line {raises[0].lineno}, in require_camera_pixel_admission'}
        self.exception_ref = r.put('full-first-exception.json', self.exception)
        self.halt: dict[str, object] = {'error_type': 'ValueError', 'message': self.message,
            'replay_allowed': False, 'original_request': self.request, 'original_response': None,
            'first_exception_receipt': self.exception_ref.path, 'next_sequence': sequence + 1}
        self.halt_ref = r.put('full-halt.json', self.halt)
        self.next_ref = r.put('failed-full-NEXT.json', {'next_sequence': sequence + 1,
            'failed_request_registered_without_readmission': True})
        policy_ref = r.put(str(root / 'ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json'), {'entry_source_pins': [[self.queue_ref.path, self.queue_ref.sha256]]})
        freeze_ref = r.put(str(root / 'ROOT-FINAL-SDK-FREEZE-P37C23-A15.json'), {'canonical_preload_policy': policy_ref.to_wire()})
        cold = evidence(r, f.proof.sources.cold_admission_ref)
        cold.update(queue_source=self.queue_ref.to_wire(), sdk_freeze=freeze_ref.to_wire())
        native = _full_failure_original_sdk_bytes_v1()
        sdk_root = root / 'sdk'
        native_path = str(sdk_root / 'xar_autoplayer/bridge/native_driver.py')
        self.sdk_ref = ExactRefV1(native_path, len(native), hashlib.sha256(native).hexdigest())
        r.raw[native_path] = native
        r.identities[native_path] = FileStatIdentityV1(len(native), '2000100', '5')
        anchor_ref = r.put('failure-sdk-anchor.json', {'schema': 'xar.source32.canonical-git-anchor/v1',
            'machine_id': f.basis.machine_id, 'commit': '6f58f72a8ff29d85f8751d3bfb1667b38f9497df'})
        base_ref = r.put('failure-sdk-base.json', {'source_root': str(sdk_root),
            'business_source_commit': '6f58f72a8ff29d85f8751d3bfb1667b38f9497df',
            'source32_canonical_anchor': anchor_ref.to_wire(), 'files': [{'relative': 'xar_autoplayer/bridge/native_driver.py',
                'bytes': len(native), 'sha256': self.sdk_ref.sha256}]})
        cold.update(sdk_base_ref=base_ref.to_wire(), sdk_anchor_ref=anchor_ref.to_wire(), business_source_generation=32)
        cold_ref = r.put(f.proof.sources.cold_admission_ref.path, cold)
        f.proof = replace(f.proof, sources=replace(f.proof.sources, cold_admission_ref=cold_ref))
        self.inventory: dict[str, object] = {'schema': 'xar.current-saved-full-pre-dispatch-inventory/v1',
            'machine_id': f.basis.machine_id, 'observed_at_utc': UTC, 'runtime_root': str(root),
            'closed_directory_snapshot': True, 'prefix_entries': f.inventory['entries'],
            'full_request_ref': self.request_ref.to_wire(), 'full_response_ref': self.response_ref.to_wire(),
            'first_exception_ref': self.exception_ref.to_wire(), 'halt_ref': self.halt_ref.to_wire(),
            'unexpected_request_refs': [], 'unexpected_response_refs': [], 'generated_request_refs': [],
            'full_inflight_present': False, 'full_before_present': False, 'full_after_present': False,
            'next_ref': self.next_ref.to_wire()}
        sdk = evidence(r, f.closure.refs.sdk_closed); sdk['normal'] = False
        processes = [record(v) for v in rows(sdk['processes'])]
        for process in processes:
            if process['role'] == 'sdk_queue': process['exit_code'] = 1
        sdk['processes'] = processes
        sdk_ref = r.put('failed-full-sdk.json', sdk)
        supervisor = evidence(r, f.closure.refs.supervisor_closed); supervisor['sdk_actual_exit'] = sdk
        supervisor_ref = r.put('failed-full-supervisor.json', supervisor)
        self.review = dict(f.review)
        self.review.update(schema=owner.FULL_PRE_DISPATCH_REVIEW_SCHEMA_V1,
            frozen_observed_Queue=f.proof.loop_state_ref.to_wire())
        self.review.pop('phase'); self.review.pop('frozen_settled_Queue')
        self.review['actual_next'] = {'next_sequence': sequence + 1}
        self.tail = owner.build_full_pre_dispatch_driver_tail_v1(prior=self.prior,
            driver_ref=f.basis.refs.driver, driver_identity=f.basis.driver_identity,
            driver_bytes=r.raw[f.basis.refs.driver.path], reader=r, observed_at_utc=UTC)
        prefix = replace(f.proof, inventory_ref=r.put('failed-full-inventory.json', self.inventory),
            history_tail_ref=r.put('failed-full-tail.json', self.tail))
        self.proof = owner.FullPreDispatchFailureProofV1(prefix, self.request_ref, self.response_ref,
            self.exception_ref, self.halt_ref, self.queue_ref, policy_ref)
        bindings = owner.SettledProgressClosureV1(f.basis.machine_id, UTC, f.basis.completed_cycles,
            f.basis.frame.date_raw, sequence + 1, f.basis.origin.original_wall_origin_utc,
            replace(f.closure.refs, sdk_closed=sdk_ref, supervisor_closed=supervisor_ref,
                driver_review=r.put('failed-full-review.json', self.review)),
            (*f.closure.tasks, f.prior.tasks[2]), 1, True, False)
        self.closure = owner.FullPreDispatchFailureClosureV1(bindings, self.proof)
        self.reseal()

    def reseal(self) -> None:
        r = self.reader
        self.response_ref = r.put(self.response_ref.path, self.response)
        self.exception_ref = r.put(self.exception_ref.path, self.exception)
        self.inventory.update(full_response_ref=self.response_ref.to_wire(), first_exception_ref=self.exception_ref.to_wire())
        prefix = replace(self.proof.prefix, inventory_ref=r.put('failed-full-inventory.json', self.inventory),
            history_tail_ref=r.put('failed-full-tail.json', self.tail))
        self.proof = replace(self.proof, prefix=prefix, full_response_ref=self.response_ref, first_exception_ref=self.exception_ref)
        self.closure = replace(self.closure, proof=self.proof)
        self.closure_ref = r.put('failed-full-closure.json', self.closure.to_wire())
        self.basis = owner.build_full_pre_dispatch_failure_basis_v1(self.closure, closure_ref=self.closure_ref,
            driver_ref=self.ready.basis.refs.driver, driver_identity=self.ready.basis.driver_identity,
            next_ref=self.next_ref, reader=r)
        self.basis_ref = r.put('failed-full-basis.json', json.loads(encode_current_saved_basis_v1(self.basis)))
        qualification = owner.BasisQualificationV1(self.basis.machine_id, UTC, self.basis_ref,
            self.basis.refs.driver, self.basis.refs.save, self.basis.driver_identity, self.basis.driver_identity,
            self.basis.save_identity, self.basis.save_identity, self.basis.refs.checkpoint_validator, 2, 1, 1, 1)
        self.validation_ref = r.put('failed-full-qualification.json', qualification.to_wire())

    def cold(self) -> owner.CurrentSavedColdInputsV1:
        return owner.validate_current_saved_cold_inputs_v1(self.basis, basis_ref=self.basis_ref,
            validation_ref=self.validation_ref, reader=self.reader)


class FullPreDispatchFailureClosureTests(unittest.TestCase):
    def test_opaque_native_integer_roundtrip_does_not_admit_unproven_restore_fields(self) -> None:
        exact = 2**63 + 17
        opaque = {'native_filetime': exact, 'rows': [exact, 2**53 + 2]}
        self.assertEqual(json.loads(_exact_native_json_v1(opaque)), opaque)
        with self.assertRaises(ValueError): json_object(opaque)
        f = FullPreDispatchFailureFixture()
        payload = record(json.loads(f.reader.raw[f.basis.refs.driver.path]))
        history = rows(payload['command_history']); last = record(history[-1])
        result = record(last['result']); result['unproven_native_identity'] = exact; last['result'] = result
        history[-1] = last; payload['command_history'] = history
        raw = _exact_native_json_v1(payload)
        reference = replace(f.basis.refs.driver, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        identity = replace(f.basis.driver_identity, bytes=len(raw))
        f.reader.identities[reference.path] = identity
        tail = owner.build_full_pre_dispatch_driver_tail_v1(prior=f.prior, driver_ref=reference,
            driver_identity=identity, driver_bytes=raw, reader=f.reader, observed_at_utc=UTC)
        self.assertEqual(record(record(rows(tail['post_prior_history'])[-1])['result'])['unproven_native_identity'], exact)
        proof = replace(f.proof.prefix, history_tail_ref=f.reader.put('opaque-native-tail.json', tail))
        with self.assertRaises(ValueError):
            owner._validate_readiness_history_v2(proof, f.prior,
                replace(f.basis, refs=replace(f.basis.refs, driver=reference), driver_identity=identity),
                f.ready.prior.game_identity, reader=f.reader)

    def test_shared_producer_cold_and_prepared_sdk_classification(self) -> None:
        f = FullPreDispatchFailureFixture()
        self.assertEqual(owner.parse_full_pre_dispatch_failure_closure_v1(json.loads(json.dumps(f.closure.to_wire())),
            expected_machine_id=f.basis.machine_id), f.closure)
        inputs = f.cold()
        self.assertEqual({p.role: p.exit_code for p in inputs.closed_epoch.sdk_processes}, {'sdk_queue': 1, 'sdk_application': 0})
        with patch.object(owner, 'LocalBasisReaderV1', return_value=f.reader):
            self.assertIs(owner.validate_current_saved_prepared_sdk_closure_v1(
                f.closure.bindings.refs.sdk_closed.to_wire(), inputs=inputs)['normal'], False)
        self.assertNotIn(f.basis.refs.driver.path, f.reader.reads)
        self.assertNotIn(f.basis.refs.save.path, f.reader.reads)

    def test_rpc_result_dispatch_markers_source_and_identity_mutations_reject(self) -> None:
        for mutation in ('rpc', 'original', 'replay', 'inflight', 'before', 'after', 'generated', 'request',
                'missing_marker', 'source_position', 'identity', 'missing_prefix'):
            with self.subTest(mutation=mutation):
                f = FullPreDispatchFailureFixture()
                if mutation == 'rpc':
                    rpc = record(f.response['full_rpc_rows_v1']); rpc['row_count'] = 1; f.response['full_rpc_rows_v1'] = rpc
                elif mutation == 'original': f.response['original_response'] = 'not-null'
                elif mutation == 'replay': f.response['replay_allowed'] = True
                elif mutation in ('inflight', 'before', 'after'): f.inventory['full_' + mutation + '_present'] = True
                elif mutation == 'generated': f.inventory['generated_request_refs'] = [f.request_ref.to_wire()]
                elif mutation == 'request': f.response['request'] = {**f.request, 'sequence': f.basis.next_sequence}
                elif mutation == 'missing_marker': f.inventory['halt_ref'] = f.exception_ref.to_wire()
                elif mutation == 'missing_prefix': f.inventory['prefix_entries'] = []
                elif mutation == 'source_position':
                    raw = f.reader.raw[f.queue_ref.path].replace(
                        b'self.require_camera_pixel_admission()', b'self.consume_sequence(request)')
                    changed_ref = replace(f.queue_ref, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
                    f.reader.raw[changed_ref.path] = raw
                    policy_ref = f.reader.put(f.proof.queue_policy_ref.path, {'entry_source_pins': [[changed_ref.path, changed_ref.sha256]]})
                    cold = evidence(f.reader, f.proof.prefix.sources.cold_admission_ref)
                    freeze_ref = f.reader.put(Path(f.queue_ref.path).with_name('ROOT-FINAL-SDK-FREEZE-P37C23-A15.json').as_posix(), {'canonical_preload_policy': policy_ref.to_wire()})
                    cold.update(queue_source=changed_ref.to_wire(), sdk_freeze=freeze_ref.to_wire())
                    cold_ref = f.reader.put(f.proof.prefix.sources.cold_admission_ref.path, cold)
                    f.proof = replace(f.proof, prefix=replace(f.proof.prefix, sources=replace(f.proof.prefix.sources, cold_admission_ref=cold_ref)))
                    f.proof = replace(f.proof, queue_source_ref=changed_ref, queue_policy_ref=policy_ref)
                else:
                    f.reader.identities[f.basis.refs.driver.path] = replace(f.basis.driver_identity, file_id='77777777')
                with self.assertRaises(ValueError): f.reseal()


class ReadinessOnlyClosureTests(unittest.TestCase):
    def test_screen_cas_with_unrelated_global_event_and_exact_receipt_binding(self) -> None:
        f = ReadinessOnlyFixture()
        result: JsonObject = {"schema": "codex.task_bus.v1", "ok": True,
            "task": {"schema": "codex.task_bus.v1", "task_id": "screen", "state": "done",
                "resources": [], "last_sequence": 22},
            "event": {"schema": "codex.task_bus.v1", "task_id": "screen", "state": "done",
                "resources": [], "sequence": 22, "kind": "completed", "event_id": "actual-event",
                "timestamp_utc": UTC}}
        release: JsonObject = {"machine_id": f.basis.machine_id, "returncode": 0,
            "release_expected_sequence": 20, "release_actual_sequence": 22, "stdout": json.dumps(result)}
        proof = owner.parse_screen_release_cas_proof_v1(json.loads(json.dumps(release)),
            expected_task_id="screen", expected_sequence=20)
        self.assertEqual((proof.expected_sequence, proof.actual_sequence), (20, 22))
        ref = f.reader.put("screen-release-with-gap.json", release)
        f.closure = replace(f.closure, refs=replace(f.closure.refs, screen_release=ref))
        f.reseal()
        self.assertEqual(f.cold().closed_epoch.old_game.pid, 30)
        for mutation in ("expected", "bool", "float", "partial", "actual", "event_sequence", "event_task", "event_kind", "event_resources"):
            bad = json_object(json.loads(json.dumps(release)))
            response = json_object(json.loads(text(bad["stdout"])))
            event = record(response["event"])
            if mutation == "expected": bad["release_expected_sequence"] = 21
            elif mutation == "bool": bad["release_expected_sequence"] = True
            elif mutation == "float": bad["release_actual_sequence"] = 22.0
            elif mutation == "partial": del bad["release_actual_sequence"]
            elif mutation == "actual": bad["release_actual_sequence"] = 23
            elif mutation == "event_sequence": event["sequence"] = 21
            elif mutation == "event_task": event["task_id"] = "unrelated"
            elif mutation == "event_kind": event["kind"] = "status"
            else: event["resources"] = ["screen"]
            response["event"] = json_object(event); bad["stdout"] = json.dumps(response)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                owner.parse_screen_release_cas_proof_v1(bad, expected_task_id="screen", expected_sequence=20)

    def test_v2_producer_json_public_cold_and_sdk_consumers(self) -> None:
        f = ReadinessOnlyFixture()
        self.assertEqual(owner.parse_normal_closure_v2(json.loads(json.dumps(f.closure.to_wire())),
            expected_machine_id=f.basis.machine_id), f.closure)
        inputs = f.cold()
        self.assertEqual(inputs.closed_epoch.old_game.pid, 30)
        self.assertEqual(inputs.basis.frame, f.prior.basis.frame)
        self.assertEqual(inputs.basis.unknown_requests, f.prior.basis.unknown_requests)
        self.assertEqual(inputs.basis.completed_cycles, f.prior.basis.completed_cycles)
        self.assertEqual(owner.resolve_current_saved_closed_sdk_ref_v1(inputs, reader=f.reader), f.closure.refs.sdk_closed)
        with patch.object(owner, "LocalBasisReaderV1", return_value=f.reader):
            sdk = owner.validate_current_saved_prepared_sdk_closure_v1(f.closure.refs.sdk_closed.to_wire(), inputs=inputs)
        self.assertIs(sdk["normal"], True)
        self.assertNotIn(f.basis.refs.driver.path, f.reader.reads)
        self.assertNotIn(f.basis.refs.save.path, f.reader.reads)
        warm = f.next_warm()
        self.assertEqual(warm.warm_proof.game.pid, 40)
        self.assertTrue(warm.warm_proof.closed_driver_identity_replaced)
        self.assertEqual(warm.inputs.basis, f.basis)
        with self.assertRaisesRegex(ValueError, "closed Driver"):
            f.cold()

    def test_bad_phase_tail_request_binding_and_task_are_rejected(self) -> None:
        for mutation in ("command", "checkpoint", "prefix", "count", "request", "next", "bound", "task", "prior"):
            with self.subTest(mutation=mutation):
                f = ReadinessOnlyFixture()
                if mutation == "command": f.restore["command"] = "do-business"
                elif mutation == "checkpoint":
                    result = record(f.restore["result"]); result["checkpoint"] = {}; f.restore["result"] = result
                elif mutation == "prefix": f.tail["prior_post_checkpoint_sha256"] = "f" * 64
                elif mutation == "count": f.tail["command_history_count"] = True
                elif mutation == "request": f.inventory["other_request_entries"] = ["FULL"]
                elif mutation == "next":
                    unused = record(f.inventory["unused_next"]); unused["request_absent"] = False; f.inventory["unused_next"] = unused
                elif mutation == "bound":
                    row = evidence(f.reader, f.proof.sources.cold_bound_ref); row["completed_cycles"] = 999
                    bad = f.reader.put("bad-bound.json", row)
                    f.proof = replace(f.proof, sources=replace(f.proof.sources, cold_bound_ref=bad))
                elif mutation == "task":
                    with self.assertRaises(ValueError): replace(f.closure, tasks=f.prior.tasks)
                    continue
                else: f.proof = replace(f.proof, prior_validation_ref=f.prior.basis_ref)
                f.reseal()
                with self.assertRaises(ValueError): f.cold()



class CompletedUnsavedTailFixture:
    """Synthetic small-source producer fixture; no real canonical or Native credit."""
    def __init__(self, *, initial_basis: CurrentSavedBasisV1 | None = None,
                 metadata_root: Path | None = None, current_driver_ref: ExactRefV1 | None = None,
                 current_driver_identity: FileStatIdentityV1 | None = None,
                 saved_prior: SavedBusinessPriorV1 | None = None,
                 readiness_prefix: bool = False) -> None:
        if initial_basis is not None and saved_prior is not None:
            raise ValueError("one complete saved prior provider")
        if saved_prior is not None:
            initial_basis = saved_prior.validated.basis
        provider = nullcontext() if initial_basis is None else patch(__name__ + ".pure_basis", return_value=initial_basis)
        with provider:
            self.prior = f = NormalWarmFixture(persisted=False, campaign_days=10958, metadata_root=metadata_root,
                validator_source=None if initial_basis is None else initial_basis.refs.checkpoint_validator,
                saved_prior=saved_prior)
        self.reader = r = f.runtime_reader
        self.basis = b = f.basis
        self.prior_basis_ref = f.basis_ref
        self.prior_validation_ref = f.validation_ref
        self.root = (f.root / "tail-runtime").resolve()
        self.current_frame = replace(b.frame, snapshot_id="native:" + str(b.frame.native_revision + 2),
            revision=b.frame.revision + 2, native_revision=b.frame.native_revision + 2,
            date_raw=b.frame.date_raw + 48)
        self.current_cycles = b.completed_cycles + 2
        self.entries: list[dict[str, object]] = []
        self.plan_entries: list[dict[str, object]] = []
        self.requests: list[Path] = []
        self.responses: list[Path] = []
        self.state = evidence(r, b.refs.seed)
        self.state.update(completed_cycles=self.current_cycles,
            before=self.current_frame.to_wire(), checkpoint_dirty_since_save=True)
        self.raw_state = r.put("tail-runtime/raw-state.json", self.state)
        self.raw_governance = r.put("tail-runtime/raw-governance.json", self.state)
        self.readiness_sources: owner.WarmSourceRefsV1 | None = None
        first = b.next_sequence
        if readiness_prefix:
            references: list[ExactRefV1] = []
            for offset, source in enumerate((f.sources.semantic_response_ref, f.sources.capabilities_response_ref)):
                row = evidence(r, source); ready_request = record(row["request"])
                sequence = b.next_sequence + offset
                ready_request["sequence"] = sequence; row["request"] = ready_request
                ready_after: dict[str, object] = {"at_utc": UTC, "tool": ready_request["tool"],
                    "request": str(self.root / "p37-requests" / f"{sequence:04d}-1-result.json"),
                    "response": str(self.root / "p37-responses" / f"{sequence:04d}-1-result.json")}
                if offset == 0:
                    ready_after.update(actual_status="cold_readiness_verified", loading_attempts=0, new_business_credit=0)
                else:
                    ready_after.update(actual_status=None, selected_step=None, checkpoint_status=None)
                references.append(self._entry(sequence, ready_request, row, ready_after))
            marker = evidence(r, f.sources.cold_bound_ref)
            marker["semantic_response"] = references[0].path
            self.readiness_sources = owner.WarmSourceRefsV1(
                r.put("tail-runtime/ROOT-ACTUAL-GAME-LAUNCH-C23.json", evidence(r, f.sources.actual_game_ref)),
                r.put("tail-runtime/ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json", evidence(r, f.sources.sdk_pair_ref)),
                references[0], references[1],
                r.put("tail-runtime/p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json", marker),
                r.put("tail-runtime/ROOT-P37C23-COLD-RESUME-ADMISSION.json", evidence(r, f.sources.cold_admission_ref)))
            first += 2
        full_request: dict[str, object] = {"sequence": first, "command": "full_loop",
            "arguments": {"max_turns": 2}}
        tools = {key: {"count": count, "error_count": 0, "client_error_count": 0}
                 for key, count in (("AUTO", 2), ("MET", 2), ("SAVE", 0))}
        full_response: dict[str, object] = {"request": full_request,
            "started_at_utc": UTC, "ended_at_utc": UTC,
            "result": {"is_error": False, "structured_content": {
                "status": "bounded_loop_finished", "replay_allowed": False,
                "actual_turns": 2, "cumulative_cycles": self.current_cycles,
                "actual_end_frame": self.current_frame.to_wire(),
                "actual_end_date_raw": self.current_frame.date_raw,
                "full_rpc_rows_v1": {"tools": tools}}}}
        full_ref = self._entry(first, full_request, full_response, None)
        for offset in range(1, 5):
            sequence = first + offset
            tool = "ck3_auto_turn" if offset % 2 else "root_current_runtime_metrics"
            request: dict[str, object] = {"sequence": sequence, "tool": tool, "arguments": {}}
            response: dict[str, object] = {"request": request,
                "started_at_utc": UTC, "ended_at_utc": UTC,
                "result": {"is_error": False, "result_type": "complete",
                           "structured_content": {"status": "complete"}}}
            after: dict[str, object] = {"tool": tool, "at_utc": UTC,
                "request": str(self.root / "p37-requests" / f"{sequence:04d}-1-result.json"),
                "response": str(self.root / "p37-responses" / f"{sequence:04d}-1-result.json")}
            self._entry(sequence, request, response, after)
            if offset % 2:
                plan_ref = r.put(f"tail-runtime/p37-responses/{sequence:04d}-0-plan.json", {
                    "source": "actual GameplayBridgeService.before_submit callback", "game_pid": 30,
                    "request": {"tool": "root_before_auto_turn_submit", "parent_sequence": sequence,
                        "callback_protocol": "xar.ck3.decision-subdecision/v1", "callback_index": 1,
                        "actual_observation_sha256": "e" * 64},
                    "result": {"is_error": False, "structured_content": {"status": "planned",
                        "plan": {"selected_step": "synthetic-no-native-action"}}}})
                self.plan_entries.append({"sequence": sequence, "ref": plan_ref.to_wire()})
                self.responses.append(Path(plan_ref.path))
        failed = first + 5
        failed_request: dict[str, object] = {"sequence": failed,
            "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}}
        refused_response: dict[str, object] = {"request": failed_request,
            "client_error": "retained terminal evidence forbids new RPC: ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json",
            "replay_allowed": False, "original_response": str(self.root / "p37-responses" / f"{failed-1:04d}-1-result.json")}
        response_ref = self._entry(failed, failed_request, refused_response, None)
        request_ref = parse_ref(self.entries[-1]["request_ref"])
        context = {"sequence": failed, "tool": failed_request["tool"], "arguments": {},
            "request_file": request_ref.path, "at_utc": UTC, "replay_allowed": False}
        first_exception = r.put("tail-runtime/ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json",
            {"stage": "guard", "exception_tree": {"type": "RecordingPaused"}, "replay_allowed": False,
             "guard_observation": {"checking": "recording_terminal_flags", "reserve_reply": False,
                "error_type": "RecordingPaused", "next_sequence": failed,
                "terminal_flags": {"failed.json": False, "completed.json": False, "closed-file-probe.json": True}}})
        halt = r.put(f"tail-runtime/p37-queue/ROOT-REQUEST-HALTED-{failed}.json", {
            "error_type": "ValueError", "message": refused_response["client_error"],
            "first_exception_receipt": first_exception.path, "next_sequence": failed + 1, "replay_allowed": False,
            "original_request": evidence(r, parse_ref(self.entries[-2]["request_ref"])),
            "original_response": str(self.root / "p37-responses" / f"{failed-1:04d}-1-result.json")})
        self.next_ref = r.put("tail-runtime/p37-queue/NEXT-SEQUENCE-P37.json",
            {"next_sequence": failed + 1, "failed_request_registered_without_readmission": True})
        interruption = r.put("tail-runtime/interruption.json", {
            "schema": "xar.current-saved-local-recording-paused-refusal/v1",
            "machine_id": b.machine_id, "observed_at_utc": UTC, "runtime_root": str(self.root),
            "sequence": failed, "request_ref": request_ref.to_wire(),
            "response_ref": response_ref.to_wire(), "inflight_ref": None,
            "before_ref": None, "first_exception_ref": first_exception.to_wire(),
            "halt_ref": halt.to_wire(), "rejection_stage": "terminal_evidence_before_request_dispatch",
            "sdk_rpc_started": False, "native_submission_started": False})
        self.inventory: dict[str, object] = {
            "schema": "xar.current-saved-completed-unsaved-tail-inventory/v1",
            "machine_id": b.machine_id, "observed_at_utc": UTC, "runtime_root": str(self.root),
            "entries": self.entries, "other_request_entries": [], "unknown_native_entries": [],
            "new_save_entries": [], "next_ref": self.next_ref.to_wire(), "plan_entries": self.plan_entries}
        processes = [{"role": role, "pid": pid, "creation_filetime": BIRTH + pid,
            "executable": "/sdk/python.exe", "exit_code": exit_code,
            "kernel_exit_observed": True, "wait_result": 0, "observation_error": None}
            for role, pid, exit_code in (("sdk_queue", 31, 1), ("sdk_application", 32, 0))]
        sdk = {"machine_id": b.machine_id, "status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED",
               "normal": False, "processes": processes}
        self.sdk_ref = r.put("tail-runtime/sdk-closed.json", sdk)
        generation = {"pid": 30, "creation_filetime": BIRTH + 100}
        supervisor = {"machine_id": b.machine_id,
            "known_preload_phase": {"before": generation, "after": generation},
            "owned_cleanup": {"ck3_pid": 30, "ck3_creation_date": UTC, "ck3_exit_code": 1,
                "job_active_processes_final": 0, "tree_gone": True,
                "cleanup_proven": True, "ok": True, "contract_errors": []},
            "sdk_actual_exit": sdk,
            "keeper": {"task_id": "screen", "last_sequence": 20,
                       "thread_exited": True, "failure": None}}
        supervisor_ref = r.put("tail-runtime/supervisor-closed.json", supervisor)
        game_ref = r.put("tail-runtime/game-exit.json", {"machine_id": b.machine_id,
            "pid": 30, "creation_filetime": BIRTH + 100, "kernel_signaled": True,
            "exit_code": 1, "forced_owned_job_cleanup": True, "normal_wm_close_qualified": False})
        tasks: list[owner.SettledTaskClosureRefsV1] = []
        for role in ("supervisor", "display"):
            nonce = "tail-" + role
            spec = r.put(nonce + "-spec.json", {"machine_id": b.machine_id, "nonce": nonce,
                "task_name": "XARG2ManagedOwner-" + nonce})
            closed = r.put(nonce + "-closed.json", {"machine_id": b.machine_id, "nonce": nonce,
                "spec_sha256": spec.sha256, "job_active_after_stage": 0,
                "forced_remaining_cleanup": False, "bootstrap_exit_code": 0, "child_exit_code": 0})
            unregistered = r.put(nonce + "-unregistered.json", {"machine_id": b.machine_id,
                "utc": UTC, "task_name": "XARG2ManagedOwner-" + nonce, "operation": "unregister",
                "actual": {"instances": 0, "arguments": "python --spec-sha " + spec.sha256,
                           "absent_after": True}})
            task_role: owner.TaskRoleV1 = "supervisor" if role == "supervisor" else "display"
            tasks.append(owner.SettledTaskClosureRefsV1(task_role, spec, closed, unregistered))
        self.abnormal: dict[str, object] = {
            "schema": "xar.current-saved-observed-abnormal-epoch/v1", "machine_id": b.machine_id,
            "observed_at_utc": UTC, "runtime_root": str(self.root), "sdk_normal": False,
            "refs": {"sdk_closed": self.sdk_ref.to_wire(), "supervisor_closed": supervisor_ref.to_wire(),
                     "game_exit": game_ref.to_wire(), "screen_release": f.release.to_wire()},
            "tasks": [task.to_wire() for task in tasks]}
        if (current_driver_ref is None) != (current_driver_identity is None):
            raise ValueError("both physical current Driver source and identity are required")
        self.driver_ref = (replace(b.refs.driver, bytes=b.refs.driver.bytes + 1, sha256="d" * 64)
                           if current_driver_ref is None else current_driver_ref)
        self.driver_identity = (FileStatIdentityV1(self.driver_ref.bytes, "900001", "4")
                                if current_driver_identity is None else current_driver_identity)
        r.identities[self.driver_ref.path] = self.driver_identity
        self.review: dict[str, object] = {
            "schema": "xar.current-saved-unsaved-tail-driver-review/v1", "machine_id": b.machine_id,
            "observed_at_utc": UTC, "runtime_root": str(self.root),
            "raw_state_ref": self.raw_state.to_wire(), "raw_governance_ref": self.raw_governance.to_wire(),
            "actual_next_ref": self.next_ref.to_wire(), "canonical_qualification_performed": False,
            "Driver": {"ref": self.driver_ref.to_wire(), "identity": self.driver_identity.to_wire(),
                "format_version": 2, "command_history_count": 7,
                "last_checkpoint": record(evidence(r, b.refs.seed)["actual_saved_checkpoint"]),
                "history_scope": "complete_current_file", "history_truncated": False,
                "history_rewritten": False, "recorded_identity": {"pipe_name": f.pipe_name, "bridge_pid": 30,
                    "episode_character_id": self.current_frame.actor_character_id,
                    "episode_run_id": self.current_frame.episode_run_id,
                    "session_binding_observation": {"present": False, "value": None}}},
            "SAVE": {"ref": b.refs.save.to_wire(), "identity": b.save_identity.to_wire()}}
        canonical = continuity.RecoveryCheckpointQualificationV1(machine_id=b.machine_id,
            observed_at_utc=UTC, validator_source_ref=b.refs.checkpoint_validator,
            driver_ref=self.driver_ref, driver_identity=self.driver_identity,
            save_ref=b.refs.save, save_identity=b.save_identity,
            checkpoint=json_object(evidence(r, b.refs.seed)["actual_saved_checkpoint"]),
            pipe_name=f.pipe_name)
        self.proof = continuity.CompletedUnsavedTailV1(machine_id=b.machine_id,
            observed_at_utc=UTC, runtime_root=str(self.root),
            sources=continuity.CompletedUnsavedTailSourcesV1(prior_basis=f.basis_ref,
                prior_validation=f.validation_ref, successful_full_responses=(full_ref,),
                raw_state=self.raw_state, raw_governance=self.raw_governance,
                interruption=interruption, inventory=r.put("tail-runtime/inventory.json", self.inventory),
                abnormal_closed_epoch=r.put("tail-runtime/abnormal-closed.json", self.abnormal),
                current_driver_review=r.put("tail-runtime/current-review.json", self.review),
                actual_next=self.next_ref,
                canonical_checkpoint_qualification=r.put("tail-runtime/canonical.json", canonical.to_wire()),
                continuity_frontier=r.put("tail-runtime/frontier.json", {})))
        self.reseal()

    def _entry(self, sequence: int, request: object, response: object,
               after: object | None) -> ExactRefV1:
        r = self.reader
        req = r.put(f"tail-runtime/p37-requests/{sequence:04d}-1-result.json", request)
        res = r.put(f"tail-runtime/p37-responses/{sequence:04d}-1-result.json", response)
        self.requests.append(Path(req.path))
        self.responses.append(Path(res.path))
        marker = None if after is None else r.put(
            f"tail-runtime/p37-queue/{sequence:04d}-after-result.json", after).to_wire()
        self.entries.append({"sequence": sequence, "request_ref": req.to_wire(),
                             "response_ref": res.to_wire(), "after_ref": marker})
        return res

    @contextmanager
    def io_scope(self) -> Iterator[None]:
        def listed(path: Path, pattern: str) -> Iterator[Path]:
            if pattern != "*.json":
                raise ValueError("only the actual finite request census is virtualized")
            if path == self.root / "p37-requests":
                return iter(self.requests)
            if path == self.root / "p37-responses":
                return iter(self.responses)
            raise ValueError("unexpected physical source outside the finite fixture")
        with patch.object(Path, "glob", autospec=True, side_effect=listed):
            yield

    def validated(self, *, evidence_only: bool = False) -> continuity.ValidatedCompletedUnsavedTailV1:
        validator = continuity.validate_completed_unsaved_tail_evidence_v1 if evidence_only else continuity.validate_completed_unsaved_tail_v1
        with self.io_scope():
            return validator(self.proof_ref, expected_machine_id=self.basis.machine_id, reader=self.reader)

    def replace_frontier_v1(self, reference: ExactRefV1) -> None:
        self.proof = replace(self.proof, sources=replace(self.proof.sources, continuity_frontier=reference))
        self.reseal()

    def reseal(self) -> None:
        r = self.reader
        self.proof = replace(self.proof, sources=replace(self.proof.sources,
            inventory=r.put("tail-runtime/inventory.json", self.inventory),
            abnormal_closed_epoch=r.put("tail-runtime/abnormal-closed.json", self.abnormal),
            current_driver_review=r.put("tail-runtime/current-review.json", self.review)))
        self.proof_ref = r.put("tail-runtime/proof.json", self.proof.to_wire())

    def recovered(self) -> tuple[CurrentSavedBasisV1, ExactRefV1, ExactRefV1]:
        checked = self.validated()
        original = evidence(self.reader, self.basis.refs.ledger)
        original.update(last_settled_cycles=checked.current_cycles, last_settled_date_raw=checked.current_frame.date_raw)
        first = continuity.reduce_completed_unsaved_tail_history_v1(original, checked)
        last = continuity.reduce_saved_checkpoint_rollback_v1(first, checked)
        ledger = self.reader.put("tail-runtime/ledger.json", last)
        basis = replace(self.basis, driver_identity=self.driver_identity,
            next_sequence=checked.actual_next_sequence, refs=replace(self.basis.refs,
                driver=self.driver_ref, driver_close=self.proof.sources.current_driver_review,
                closure=self.proof_ref, next=self.next_ref, ledger=ledger))
        basis_ref = self.reader.put("tail-runtime/basis.json", json.loads(encode_current_saved_basis_v1(basis)))
        qualification = owner.BasisQualificationV1(basis.machine_id, UTC, basis_ref,
            basis.refs.driver, basis.refs.save, basis.driver_identity, basis.driver_identity,
            basis.save_identity, basis.save_identity, basis.refs.checkpoint_validator, 7, 1, 1, 1)
        validation_ref = self.reader.put("tail-runtime/qualification.json", qualification.to_wire())
        return basis, basis_ref, validation_ref

    def cold(self) -> owner.CurrentSavedColdInputsV1:
        basis, basis_ref, validation_ref = self.recovered()
        with self.io_scope():
            return owner.validate_current_saved_cold_inputs_v1(basis, basis_ref=basis_ref,
                validation_ref=validation_ref, reader=self.reader)

    def next_warm(self) -> owner.WarmCurrentSavedFeederInputsV1:
        basis, basis_ref, validation_ref = self.recovered()
        carrier = object.__new__(ReadinessOnlyFixture)
        carrier.prior = self.prior
        carrier.reader = self.reader
        carrier.basis = basis
        carrier.basis_ref = basis_ref
        carrier.validation_ref = validation_ref
        with self.io_scope():
            return carrier.next_warm()


class ReadinessRestoreProjectionFixture:
    """Nonempty historical business tail and a physically projected new Driver."""
    def __init__(self, saved_prior: SavedBusinessPriorV1 | None = None, *,
                 initial_basis: CurrentSavedBasisV1 | None = None, metadata_root: Path | None = None,
                 validator_bytes: bytes | None = None) -> None:
        import subprocess
        self.tail = tail = CompletedUnsavedTailFixture(readiness_prefix=True, saved_prior=saved_prior,
            initial_basis=initial_basis, metadata_root=metadata_root)
        self.reader = r = tail.reader
        if validator_bytes is not None:
            reference = tail.basis.refs.checkpoint_validator
            if (len(validator_bytes), hashlib.sha256(validator_bytes).hexdigest()) != (reference.bytes, reference.sha256):
                raise ValueError("exact fixture validator source")
            r.raw[reference.path] = validator_bytes
        self.prior = prior = tail.cold()
        current = tail.next_warm()
        f = object.__new__(NormalWarmFixture)
        f.__dict__.update(tail.prior.__dict__)
        f.basis = prior.basis; f.basis_ref = prior.basis_ref; f.validation_ref = prior.validation_ref
        f.sources = current.warm_proof.sources; f.game_identity = current.warm_proof.game
        f.root = Path(f.sources.actual_game_ref.path).parent
        r.metadata_root = f.root
        with tail.io_scope():
            self.ready = ready = ReadinessOnlyFixture(f)
        cp = prior.checkpoint
        def restore(index: int, previous: int, pid: int) -> JsonObject:
            return {"index": index, "command": "restore-checkpoint", "ok": True,
                "result": {"step": "restore-checkpoint", "accepted": True, "status": "restored",
                    "backend_id": "native-headless", "source": "native-session-cold-start",
                    "checkpoint": cp, "restored_date_raw": prior.basis.frame.date_raw, "map_ready": True,
                    "lifecycle": {"previous_pid": previous, "pid": pid}}}
        payload = record(json.loads(r.headers[prior.basis.refs.driver.path]))
        payload["succession_lifecycle"] = cp["succession_lifecycle"]
        payload["command_history"] = [{"index": 1, "command": "save-checkpoint", "ok": True,
            "result": {"checkpoint": cp}}, restore(2, 10, 30), restore(3, 30, 40)]
        payload["bridge_pid"] = 40
        raw = json.dumps(payload, separators=(",", ":")).encode()
        self.raw = raw
        self.driver_ref = ExactRefV1(prior.basis.refs.driver.path, len(raw), hashlib.sha256(raw).hexdigest())
        self.driver_identity = FileStatIdentityV1(len(raw), "900010", "10")
        r.raw[self.driver_ref.path] = raw; r.headers[self.driver_ref.path] = raw
        r.identities[self.driver_ref.path] = self.driver_identity
        source_commit = "6f58f72a8ff29d85f8751d3bfb1667b38f9497df"
        source_tag = "refs/tags/archive/robert-source32-6f58f72a8-20261022"
        tag = subprocess.run(["git", "rev-parse", "--verify", source_tag],
            cwd=Path(__file__).resolve().parents[2], capture_output=True, check=False)
        if tag.returncode != 0 or tag.stdout.strip() != source_commit.encode("ascii"):
            raise ValueError("published original Source32 archive tag required; checkout all tags, never skip")
        origin = source_commit + ":ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py"
        with subprocess.Popen(["git", "show", origin], cwd=Path(__file__).resolve().parents[2],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
            if process.stdout is None: raise ValueError("bounded original Git source pipe")
            native = process.stdout.read(2097153)
            if len(native) > 2097152:
                process.kill(); process.wait()
                raise ValueError("bounded complete original Source32 source")
            if process.wait(timeout=30) != 0:
                raise ValueError("original Source32 Git object required; never skip")
        if len(native) != 1648649 or hashlib.sha256(native).hexdigest() != "15a1eca3cee4f79be51a4144258650822e49146c93b7a87257319f848928d06b":
            raise ValueError("exact complete original Source32 source pin")
        native_path = str(r.metadata_root / "sdk/xar_autoplayer/bridge/native_driver.py")
        self.sdk_ref = ExactRefV1(native_path, len(native), hashlib.sha256(native).hexdigest())
        r.raw[native_path] = native
        anchor = r.put("sdk-anchor.json", {"schema": "xar.source32.canonical-git-anchor/v1",
            "machine_id": prior.basis.machine_id, "commit": origin.split(":", 1)[0]})
        base = r.put("sdk-base.json", {"source_root": str(r.metadata_root / "sdk"),
            "business_source_commit": origin.split(":", 1)[0], "source32_canonical_anchor": anchor.to_wire(),
            "files": [{"relative": "xar_autoplayer/bridge/native_driver.py", "bytes": len(native),
                "sha256": self.sdk_ref.sha256}]})
        cold = evidence(r, f.sources.cold_admission_ref)
        cold.update(sdk_base_ref=base.to_wire(), sdk_anchor_ref=anchor.to_wire(), business_source_generation=32)
        f.sources = replace(f.sources, cold_admission_ref=r.put("ROOT-P37C23-COLD-RESUME-ADMISSION.json", cold))
        if tail.readiness_sources is None: raise ValueError("explicit original readiness source")
        with tail.io_scope():
            self.card = owner.build_readiness_restore_projection_tail_v2(prior=prior,
                prior_readiness_sources=tail.readiness_sources, current_readiness_sources=f.sources,
                driver_ref=self.driver_ref, driver_identity=self.driver_identity, driver_bytes=raw,
                sdk_native_driver_ref=self.sdk_ref, reader=r, observed_at_utc=UTC)
        ready.tail = dict(self.card.to_wire())
        ready.proof = replace(ready.proof, sources=f.sources)
        ready.driver_ref = self.driver_ref
        driver = record(ready.review["Driver"])
        driver.update(ref=self.driver_ref.to_wire(), identity=self.driver_identity.to_wire(), command_history_count=3)
        ready.review["Driver"] = driver
        ready.basis = replace(ready.basis, driver_identity=self.driver_identity,
            refs=replace(ready.basis.refs, driver=self.driver_ref))
        ready.reseal()
        q = owner.BasisQualificationV1(ready.basis.machine_id, UTC, ready.basis_ref,
            ready.basis.refs.driver, ready.basis.refs.save, self.driver_identity, self.driver_identity,
            ready.basis.save_identity, ready.basis.save_identity, ready.basis.refs.checkpoint_validator, 3, 1, 1, 1)
        ready.validation_ref = r.put("ready-qualification.json", q.to_wire())


class ReadinessRestoreProjectionTests(unittest.TestCase):
    def test_explicit_sdk_source_capability_local_file_and_strict_boundaries(self) -> None:
        from tools.g2_saved_campaign.test_current_saved_continuity_v1 import _owned_continuity_case_v1
        f = ReadinessRestoreProjectionFixture()
        raw = f.reader.raw[f.sdk_ref.path]
        with contextmanager(_owned_continuity_case_v1)("sdk-source-capability") as root:
            path = root / "native_driver.py"
            path.write_bytes(raw)
            reference = replace(f.sdk_ref, path=str(path))
            reader = owner.LocalBasisReaderV1()
            with patch.object(reader, "read", side_effect=AssertionError("generic lane forbidden")), \
                    patch.object(reader, "read_response", side_effect=AssertionError("RPC lane forbidden")):
                self.assertEqual(exact_sdk_source_bytes_v1(reader, reference), raw)
                for wrong in (replace(reference, bytes=reference.bytes + 1),
                        replace(reference, sha256="f" * 64), replace(reference, bytes=2097153)):
                    with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                        exact_sdk_source_bytes_v1(reader, wrong)
                for limit in (True, 0, 2097153):
                    with self.subTest(limit=limit), self.assertRaises(ValueError):
                        reader.read_sdk_source(reference, limit)
                with self.assertRaises(ValueError):
                    Mock(wraps=reader.read_sdk_source)(reference, 2097152.0)
                for wrong_scalar in (True, 1.0):
                    malformed = object.__new__(ExactRefV1)
                    object.__setattr__(malformed, "path", reference.path)
                    object.__setattr__(malformed, "sha256", reference.sha256)
                    object.__setattr__(malformed, "bytes", wrong_scalar)
                    with self.subTest(bytes=wrong_scalar), self.assertRaises(ValueError):
                        exact_sdk_source_bytes_v1(reader, malformed)
            from tools.g2_saved_campaign.current_saved_campaign_feeder_v1 import LocalCurrentSavedFeederReaderV1
            feeder_reader = LocalCurrentSavedFeederReaderV1()
            with patch.object(feeder_reader, "read", side_effect=AssertionError("feeder generic SDK fallback forbidden")):
                self.assertEqual(exact_sdk_source_bytes_v1(feeder_reader, reference), raw)
                with self.assertRaises(ValueError):
                    Mock(wraps=feeder_reader.read_sdk_source)(reference, 2097152.0)
            class GenericOnly:
                def read(self, reference: ExactRefV1, limit: int) -> bytes:
                    raise AssertionError("generic SDK fallback forbidden")
                def read_response(self, reference: ExactRefV1, limit: int) -> bytes:
                    raise AssertionError("RPC SDK alias forbidden")
                def stat(self, path: str) -> FileStatIdentityV1:
                    raise AssertionError("missing capability must reject before I/O")
            with self.assertRaisesRegex(ValueError, "explicit SDK-source reader required"):
                exact_sdk_source_bytes_v1(GenericOnly(), reference)

    def test_complete_saved_producer_actual_native_qualification_and_new_cold(self) -> None:
        from datetime import datetime, timezone
        from tools.ck3_live_run_id import current_machine_id
        from tools.g2_saved_campaign import test_current_saved_basis_v1 as bf
        from tools.g2_saved_campaign.test_current_saved_continuity_v1 import _owned_continuity_case_v1
        from tools.g2_saved_campaign.current_saved_basis_v1 import (
            PinnedCheckpointValidatorV1, parse_json, qualify_current_saved_basis_v1,
            validate_current_saved_basis_files_v1)
        from xar_autoplayer.cold_checkpoint_validator import validate_cold_start_checkpoint_payload_for_pipe
        life: JsonObject = {"schema": "xar.ck3.succession-lifecycle-binding/v1",
            "lifecycle": "ordinary_campaign_succession", "xar_enabled": None,
            "pact_contract": "absent_by_verified_xar_mod_not_loaded",
            "source": "absent_by_verified_xar_mod_not_loaded", "environment_sha256": "e" * 64}
        class Producer(bf.CurrentSavedBasisTests):
            @classmethod
            def write(cls, name: str, value: object) -> ExactRefV1:
                row = record(json.loads(json.dumps(value).replace('"succession_lifecycle": null',
                    '"succession_lifecycle": ' + json.dumps(life))))
                if name == "driver.json":
                    row["bridge_pid"] = 10
                    cp = record(row["last_checkpoint"]); row["succession_lifecycle"] = cp["succession_lifecycle"]
                elif name == "governance.json": row.update(governance_result_state=None, pending_focus=None)
                elif name in ("stale-ledger.json", "origin-ledger.json"):
                    row.update(target_days=10958, target_date_raw=integer(row["start_date_raw"]) + 10958 * 24)
                    if name == "stale-ledger.json":
                        body = record(record(record(parse_json((cls.root / "full-100.json").read_bytes()))["result"])["structured_content"])
                        row.update(schema="root.ck3.continuity-window/v1", sequence=1, window_id=1,
                            status="running", last_settled_cycles=integer(body["cumulative_cycles"]),
                            last_settled_date_raw=integer(body["actual_end_date_raw"]),
                            game_binding={"pid": 10, "creation_date": UTC}, cold_handoff_count=0,
                            manual_repair_count=0, automatic_recovery_count=0, binding_lineage_count=0)
                return super().write(name, row)
        with contextmanager(_owned_continuity_case_v1)("readiness-projection") as root:
            Producer.root = root; Producer.reader = bf.DiskReader(); Producer.peak_upper = 4096
            with patch.object(bf, "MACHINE", current_machine_id()): Producer.make_inputs()
            inputs = replace(Producer.inputs, observed_at_utc=datetime.now(timezone.utc).isoformat(),
                origin=replace(Producer.inputs.origin, target_days=10958,
                    target_date_raw=Producer.inputs.origin.start_date_raw + 10958 * 24))
            original = qualify_current_saved_basis_v1(inputs, reader=Producer.reader,
                checkpoint_validator=Producer.validator)
            f = ReadinessRestoreProjectionFixture(SavedBusinessPriorV1(original, Producer.reader, "test-pipe"))
            validator = PinnedCheckpointValidatorV1(f.ready.basis.refs.checkpoint_validator,
                validate_cold_start_checkpoint_payload_for_pipe)
            with f.tail.io_scope():
                measured = validate_current_saved_basis_files_v1(f.ready.basis, reader=f.reader,
                    checkpoint_validator=validator)
                self.assertEqual(measured.driver_body_reads, 1)
                self.assertEqual(measured.canonical_checkpoint_validator_calls, 1)
                self.assertEqual(measured.driver_history_rows, 3)
                qualification = owner.build_basis_qualification_v1(measured, basis_ref=f.ready.basis_ref,
                    reader=f.reader, observed_at_utc=datetime.now(timezone.utc).isoformat())
                f.ready.validation_ref = f.reader.put("actual-new-qualification.json", qualification.to_wire())
                self.assertEqual(f.ready.cold().basis, f.ready.basis)
            with patch(__name__ + '.pure_basis', return_value=original.basis):
                failed_prior = NormalWarmFixture(persisted=False,
                    campaign_days=10958, metadata_root=root / 'full-pre-dispatch',
                    saved_prior=SavedBusinessPriorV1(original, Producer.reader, 'test-pipe'))
            failed = FullPreDispatchFailureFixture(failed_prior)
            measured_failure = owner.qualify_full_pre_dispatch_failure_basis_v1(failed.basis,
                driver_bytes=failed.reader.raw[failed.basis.refs.driver.path],
                checkpoint_validator=Producer.validator, reader=failed.reader)
            self.assertEqual((measured_failure.driver_body_reads,
                measured_failure.canonical_checkpoint_validator_calls), (1, 1))
            failed.validation_ref = failed.reader.put('actual-full-failure-qualification.json',
                owner.build_basis_qualification_v1(measured_failure, basis_ref=failed.basis_ref,
                    reader=failed.reader, observed_at_utc=UTC).to_wire())
            self.assertEqual(failed.cold().basis, failed.basis)

    def test_original_nonempty_tail_to_json_closed_basis_cold_sdk_and_next_warm(self) -> None:
        f = ReadinessRestoreProjectionFixture()
        wire = json.loads(json.dumps(f.card.to_wire()))
        self.assertEqual(owner.parse_readiness_restore_projection_tail_v2(wire,
            expected_machine_id=f.prior.basis.machine_id), f.card)
        self.assertEqual(wire["historical_post_checkpoint_count"], 6)
        self.assertEqual(wire["filtered_historical_count"], 5)
        self.assertFalse(wire["original_driver_body_available"])
        with f.tail.io_scope():
            cold = f.ready.cold()
            through_adapter = owner.validate_current_saved_cold_inputs_v1(f.ready.basis,
                basis_ref=f.ready.basis_ref, validation_ref=f.ready.validation_ref,
                reader=owner._TailOriginalResponseReaderV1(f.reader))
            self.assertEqual(through_adapter, cold)
            self.assertEqual(cold.closed_epoch.old_game.pid, 40)
            self.assertEqual(cold.basis.completed_cycles, f.prior.basis.completed_cycles)
            self.assertEqual(cold.basis.frame, f.prior.basis.frame)
            with patch.object(owner, "LocalBasisReaderV1", return_value=f.reader):
                sdk = owner.validate_current_saved_prepared_sdk_closure_v1(f.ready.closure.refs.sdk_closed.to_wire(), inputs=cold)
            self.assertIs(sdk["normal"], True)
            warm = f.ready.next_warm(50)
            self.assertEqual(warm.warm_proof.game.pid, 50)
            self.assertTrue(warm.warm_proof.closed_driver_identity_replaced)
        self.assertNotIn(f.driver_ref.path, f.reader.reads)
        self.assertNotIn(f.prior.basis.refs.save.path, f.reader.reads)

    def test_exact_contract_counts_types_and_actual_restore_mutations_rejected(self) -> None:
        f = ReadinessRestoreProjectionFixture()
        for field, value in (("command_history_count", True), ("prior_history_count", 7.0),
                ("historical_rows_reconstructed", True), ("original_driver_body_available", True),
                ("new_game_day_credit", 1), ("physical_history", None), ("extra", None)):
            row = dict(f.card.to_wire()); row[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                owner.parse_readiness_restore_projection_tail_v2(row, expected_machine_id=f.prior.basis.machine_id)
        for mutation in ("business", "missing", "result", "prior", "sdk_pin", "sdk_path"):
            row = dict(f.card.to_wire())
            physical = decode_readonly_prefix_history_v1(row["physical_history"])
            if mutation == "business": physical[0]["command"] = "do-business"
            elif mutation == "missing": physical.pop()
            elif mutation == "result":
                result = record(physical[0]["result"]); result["map_ready"] = False; physical[0]["result"] = result
            elif mutation == "prior": row["prior_validation_ref"] = f.prior.basis_ref.to_wire()
            elif mutation == "sdk_pin": row["sdk_native_driver_ref"] = replace(f.sdk_ref, sha256="f" * 64).to_wire()
            else: row["sdk_native_driver_ref"] = replace(f.sdk_ref, path=f.sdk_ref.path + "-other").to_wire()
            if mutation in ("business", "missing", "result"):
                import base64, zlib
                raw = _exact_native_json_v1(physical)
                row["physical_history"] = {"schema": "xar.raw-closed-driver-history-opaque/v1",
                    "encoding": "zlib+base64", "decoded_bytes": len(raw), "decoded_sha256": hashlib.sha256(raw).hexdigest(),
                    "row_count": len(physical), "payload": base64.b64encode(zlib.compress(raw)).decode("ascii")}
            with self.subTest(mutation=mutation), f.tail.io_scope(), self.assertRaises(ValueError):
                owner.validate_readiness_restore_projection_tail_v2(row, prior=f.prior,
                    basis=f.ready.basis, game=f.ready.prior.game_identity, reader=f.reader)


class CompletedUnsavedTailTests(unittest.TestCase):
    def test_public_proof_roundtrip_cold_sdk_and_warm_keep_saved_frontier(self) -> None:
        f = CompletedUnsavedTailFixture()
        parsed = continuity.parse_completed_unsaved_tail_v1(json.loads(json.dumps(f.proof.to_wire())),
            expected_machine_id=f.basis.machine_id)
        self.assertEqual(parsed, f.proof)
        checked = f.validated()
        self.assertEqual(checked.discarded_cycles, 2)
        inputs = f.cold()
        self.assertEqual(inputs.basis.completed_cycles, f.basis.completed_cycles)
        self.assertEqual(inputs.basis.frame, f.basis.frame)
        self.assertEqual(inputs.basis.unknown_requests, f.basis.unknown_requests)
        self.assertEqual(inputs.closed_epoch.next_sequence, checked.actual_next_sequence)
        self.assertEqual({p.role: p.exit_code for p in inputs.closed_epoch.sdk_processes},
                         {"sdk_queue": 1, "sdk_application": 0})
        with patch.object(owner, "LocalBasisReaderV1", return_value=f.reader):
            sdk = owner.validate_current_saved_prepared_sdk_closure_v1(f.sdk_ref.to_wire(), inputs=inputs)
        self.assertIs(sdk["normal"], False)
        warm = f.next_warm()
        self.assertEqual(warm.inputs.basis.completed_cycles, f.basis.completed_cycles)
        self.assertTrue(warm.warm_proof.closed_driver_identity_replaced)
        self.assertEqual(f.validated(evidence_only=True).driver_ref, f.driver_ref)
        with self.assertRaises(ValueError):
            f.validated()
        self.assertNotIn(f.driver_ref.path, f.reader.reads)
        self.assertNotIn(f.basis.refs.save.path, f.reader.reads)


    def test_historical_save_identity_may_advance_but_current_gates_remain_strict(self) -> None:
        f = CompletedUnsavedTailFixture()
        checked = f.validated()
        f.reader.identities[f.basis.refs.save.path] = replace(f.basis.save_identity, file_id="900005")
        self.assertEqual(f.validated(evidence_only=True), checked)
        with self.assertRaises(ValueError):
            f.validated()
        with self.assertRaises(ValueError):
            f.cold()

    def test_rejected_scalar_types_extra_fields_and_declared_unknowns(self) -> None:
        for name, value in (("new_ordinary_cycle_credit", True), ("new_game_day_credit", 0.0),
                            ("Driver_history_truncated", None), ("unknown_alias", None)):
            f = CompletedUnsavedTailFixture()
            wire: dict[str, object] = dict(f.proof.to_wire())
            wire[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                continuity.parse_completed_unsaved_tail_v1(wire, expected_machine_id=f.basis.machine_id)
        for name in ("other_request_entries", "unknown_native_entries", "new_save_entries"):
            f = CompletedUnsavedTailFixture()
            f.inventory[name] = ["unclassified"]
            f.reseal()
            with self.subTest(name=name), self.assertRaises(ValueError):
                f.validated()

    def test_real_sources_and_closed_stat_races_are_not_repaired(self) -> None:
        for mutation in ("sdk", "saved", "history", "task", "failed_flag", "request",
                         "first_exception", "canonical", "next_bool", "next_float", "save_race", "driver_race"):
            f = CompletedUnsavedTailFixture()
            if mutation == "sdk":
                row = evidence(f.reader, f.sdk_ref)
                processes = rows(row["processes"])
                first = record(processes[0]);first["exit_code"] = 0
                row["processes"] = [first, processes[1]]
                reference = f.reader.put("tail-runtime/bad-sdk.json", row)
                refs = record(f.abnormal["refs"]);refs["sdk_closed"] = reference.to_wire();f.abnormal["refs"] = refs
            elif mutation == "saved":
                f.reader.identities[f.basis.refs.save.path] = replace(f.basis.save_identity, file_id="999")
            elif mutation == "history":
                driver = record(f.review["Driver"]);driver["history_truncated"] = True;f.review["Driver"] = driver
            elif mutation == "task": f.abnormal["tasks"] = []
            elif mutation in ("failed_flag", "next_bool", "next_float"):
                row = evidence(f.reader, f.next_ref)
                if mutation == "failed_flag":row["failed_request_registered_without_readmission"] = False
                else:row["next_sequence"] = True if mutation == "next_bool" else float(integer(record(row)["next_sequence"], 1))
                ref = f.reader.put("tail-runtime/bad-next.json", row)
                f.proof = replace(f.proof, sources=replace(f.proof.sources, actual_next=ref))
            elif mutation == "request": f.entries[-1]["after_ref"] = f.prior.basis_ref.to_wire()
            elif mutation == "first_exception":
                stop = evidence(f.reader, f.proof.sources.interruption)
                ref = f.reader.put("tail-runtime/bad-exception.json", {"exception_tree": {"type": "UnknownNative"}, "replay_allowed": False})
                stop["first_exception_ref"] = ref.to_wire()
                f.proof = replace(f.proof, sources=replace(f.proof.sources,
                    interruption=f.reader.put("tail-runtime/bad-stop.json", stop)))
            elif mutation == "canonical":
                row = evidence(f.reader, f.proof.sources.canonical_checkpoint_qualification)
                row["ledger_write_already_performed"] = True
                f.proof = replace(f.proof, sources=replace(f.proof.sources,
                    canonical_checkpoint_qualification=f.reader.put("tail-runtime/bad-canonical.json", row)))
            else:
                target = f.driver_ref.path if mutation == "driver_race" else f.basis.refs.save.path
                def changed(path: str) -> None:
                    if path == f.proof.sources.inventory.path:
                        old = f.reader.identities[target]
                        f.reader.identities[target] = replace(old, file_id="777")
                f.reader.after_read = changed
            f.reseal()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                f.validated()

if __name__ == "__main__":
    unittest.main()

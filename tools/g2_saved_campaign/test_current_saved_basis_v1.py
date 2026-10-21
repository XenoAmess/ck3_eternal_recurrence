"""Basis."""
from __future__ import annotations

import copy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
SDK = REPO / "ck3_autonomous_player/src"
sys.path.insert(0, str(SDK))

from xar_autoplayer.cold_checkpoint_validator import validate_cold_start_checkpoint_payload_for_pipe
from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisRefsV1, CampaignOriginV1, CurrentSavedBasisInputsV1,
    CurrentSavedBasisV1, ExactRefV1, PinnedCheckpointValidatorV1, ProgressReconciliationV1, rows,
    UnknownHistoricalRequestV1, build_current_saved_basis_v1, decode_current_saved_basis_v1,
    encode_current_saved_basis_v1, parse_current_saved_basis_v1, parse_json,
    validate_current_saved_basis_files_v1,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import (
    FileStatIdentityV1, normalize_file_stat_identity_v1,
)

MACHINE = "synthetic-current-saved-basis"
FIXTURE = Path(os.environ.get("XAR_CURRENT_SAVED_BASIS_TEST_ROOT", "/synthetic/no-io"))
HARD = 4194304
SOFT = 3145728


def json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False).encode("utf-8")


def object_row(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("test object")
    out: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("test key")
        out[key] = item
    return out



def pure_basis() -> CurrentSavedBasisV1:
    ref = ExactRefV1("/synthetic/xar_checkpoint.ck3", 1, "a" * 64)
    refs = BasisRefsV1(*(ref for _ in range(15)))
    checkpoint = {"name": "xar_checkpoint.ck3", "load_save_name": "xar_checkpoint",
        "path": ref.path, "size": 1, "sha256": ref.sha256, "saved_date_raw": 148,
        "history_index": 1, "succession_lifecycle": None}
    goal = {"campaign_id": "campaign-1", "current_character_id": 2}
    from tools.g2_saved_campaign.current_saved_basis_v1 import parse_frame, checkpoint_anchor, json_object
    return CurrentSavedBasisV1(MACHINE, "2026-10-21T06:00:00Z",
        CampaignOriginV1(100, 340, 10, "2026-10-19T03:26:49.420926Z", "campaign-1"),
        parse_frame({"snapshot_id": "native:10", "revision": 11, "native_revision": 10,
            "date_raw": 148, "actor_character_id": 2, "episode_run_id": "episode-2"}),
        20, checkpoint_anchor(checkpoint), json_object(goal), refs,
        FileStatIdentityV1(1, "9007199254740993", "1792563000000000001"),
        FileStatIdentityV1(1, "9007199254740995", "1792563000000000003"), 103,
        ProgressReconciliationV1(18, 124, 20, 148, 100, 3, 4, False),
        (UnknownHistoricalRequestV1(7, ref),), ())


def reparse(path: Path) -> bool:
    attributes: object = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
    if type(attributes) is not int:
        raise RuntimeError("stat attributes")
    return path.is_symlink() or bool(attributes & 0x400)

class DiskReader:
    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        if reference.bytes > limit:
            raise ValueError("test bounded read")
        return Path(reference.path).read_bytes()

    def stat(self, path: str) -> FileStatIdentityV1:
        return normalize_file_stat_identity_v1(Path(path).stat())


class OverrideReader(DiskReader):
    def __init__(self, overrides: dict[str, bytes]) -> None:
        self.overrides = overrides

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        if reference.path in self.overrides:
            return self.overrides[reference.path]
        return super().read(reference, limit)


def file_ref(path: Path) -> ExactRefV1:
    raw = path.read_bytes()
    return ExactRefV1(str(path.resolve()), len(raw), hashlib.sha256(raw).hexdigest())


class CurrentSavedBasisTests(unittest.TestCase):
    root: Path
    fixture_enabled: bool
    reader: DiskReader
    inputs: CurrentSavedBasisInputsV1
    validator: PinnedCheckpointValidatorV1
    basis: CurrentSavedBasisV1
    before_env: dict[str, str | None]
    before_tempdir: str | None
    peak_upper: int
    root_identity: FileStatIdentityV1

    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture_enabled = "XAR_CURRENT_SAVED_BASIS_TEST_ROOT" in os.environ
        if not cls.fixture_enabled:
            cls.basis = pure_basis()
            return
        review = os.environ.get("XAR_CURRENT_SAVED_BASIS_TEST_REVIEW_UTC")
        if not review or not os.environ.get("XAR_CURRENT_SAVED_BASIS_MACHINE_ID"):
            raise RuntimeError("explicit finite fixture review and machine required")
        deadline = datetime.fromisoformat(review.replace("Z", "+00:00"))
        if deadline.tzinfo is None or datetime.now(timezone.utc) >= deadline:
            raise RuntimeError("finite fixture review expired")
        if FIXTURE.exists():
            raise RuntimeError("owned fixture must start absent")
        base = FIXTURE.parent.resolve(strict=True)
        for parent in (base, *base.parents):
            if reparse(parent):
                raise RuntimeError("fixture parent reparse")
        FIXTURE.mkdir()
        cls.root = FIXTURE.resolve(strict=True)
        cls.root_identity = normalize_file_stat_identity_v1(cls.root.stat())
        cls.before_env = {key: os.environ.get(key) for key in ("TMP", "TEMP", "TMPDIR")}
        cls.before_tempdir = tempfile.tempdir
        for key in cls.before_env:
            os.environ[key] = str(cls.root)
        tempfile.tempdir = str(cls.root)
        cls.peak_upper = 4096
        try:
            cls.reader = DiskReader()
            cls.make_inputs()
            cls.basis = build_current_saved_basis_v1(
                cls.inputs, reader=cls.reader, checkpoint_validator=cls.validator)
            cls.measure()
        except BaseException:
            cls.cleanup()
            raise

    @classmethod
    def write(cls, name: str, value: object) -> ExactRefV1:
        path = cls.root / name
        if not path.parent.resolve(strict=True).is_relative_to(cls.root):
            raise RuntimeError("fixture write containment")
        data = json_bytes(value)
        if len(data) > 65536:
            raise RuntimeError("fixture leaf cap")
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        cls.measure()
        return file_ref(path)

    @classmethod
    def measure(cls) -> None:
        total = 4096
        for path in cls.root.rglob("*"):
            stat = path.stat(follow_symlinks=False)
            if reparse(path) or not path.resolve(strict=True).is_relative_to(cls.root):
                raise RuntimeError("fixture reparse or escape")
            total += 4096 if path.is_dir() else ((stat.st_size + 4095) // 4096) * 4096
        cls.peak_upper = max(cls.peak_upper, total)
        if total > HARD or total >= SOFT:
            raise RuntimeError("owned fixture budget")

    @classmethod
    def make_inputs(cls) -> None:
        saves = cls.root / "save games"
        saves.mkdir()
        save_file = saves / "xar_checkpoint.ck3"
        with save_file.open("xb") as stream:
            stream.write(b"synthetic-real-save-bytes")
            stream.flush()
            os.fsync(stream.fileno())
        saved = file_ref(save_file)
        cp: dict[str, object] = {
            "status": "saved", "strategy": "native-autosave-command-v1",
            "name": "xar_checkpoint.ck3", "path": saved.path, "size": saved.bytes,
            "sha256": saved.sha256, "date_raw": 148, "history_index": 1,
            "episode_character_id": 2, "episode_run_id": "episode-2",
            "succession_lifecycle": None, "overwrite_confirmed": True,
        }
        frame = {"snapshot_id": "native:10", "revision": 11, "native_revision": 10,
                 "date_raw": 148, "actor_character_id": 2, "episode_run_id": "episode-2"}
        goal = {"format_version": 1, "goal_key": "dynasty_continuity", "campaign_id": "campaign-1",
                "origin_character_id": 1, "current_character_id": 2,
                "progress": {"reconciled_successions": 1}}
        old_cp = {**cp, "date_raw": 124, "sha256": "0" * 64}
        state: dict[str, object] = {
            "schema": "g2.queue.cumulative-loop/v1", "completed_cycles": 20, "start_date_raw": 100,
            "before": frame, "pending_cycle": None, "pending_checkpoint": None, "terminal": None,
            "campaign_goal_anchor": goal, "actual_saved_checkpoint": old_cp,
            "counts": {"checkpoint_saved": 3, "date_advanced_turns": 7},
            "checkpoint_dirty_since_save": True, "checkpoint_due_after_readonly_chain": True,
        }
        settled_ref = cls.write("settled-state.json", state)
        semantic_ref = cls.write("semantic-101.json", {
            "request": {"sequence": 101, "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}},
            "result": {"is_error": False, "result_type": "complete", "structured_content": {
                "date_raw": 148, "episode_character_id": 2, "episode_run_id": "episode-2",
                "revision": 12, "native_revision": 11, "snapshot_id": "native:11",
                "campaign_goal": goal, "map_ready": True, "succession_lifecycle": None}}})
        save_ref = cls.write("save-102.json", {
            "request": {"sequence": 102, "tool": "ck3_save_checkpoint", "arguments": {"expected_revision": 12}},
            "result": {"is_error": False, "result_type": "complete", "structured_content": {"checkpoint": cp}}})
        seed = copy.deepcopy(state)
        seed["actual_saved_checkpoint"] = cp
        seed["checkpoint_dirty_since_save"] = False
        seed["checkpoint_due_after_readonly_chain"] = False
        seed["counts"] = {"checkpoint_saved": 4, "date_advanced_turns": 7}
        seed["actual_saved_checkpoint_source"] = {
            "global_turn": 20, "semantic_response": semantic_ref.path, "save_response": save_ref.path,
            "source_kind": "typed_maintenance_save", "ordinary_cycle_credit": 0}
        seed_ref = cls.write("projected-seed.json", seed)
        gov = cls.write("governance.json", {"completed_cycles": 20, "pending_cycle": None})
        full = cls.write("full-100.json", {
            "request": {"sequence": 100, "command": "full_loop", "arguments": {"max_turns": 30}},
            "result": {"is_error": False, "structured_content": {"status": "bounded_loop_finished",
                "cumulative_cycles": 20, "actual_end_date_raw": 148,
                "actual_end_frame": frame, "replay_allowed": False}}})
        payload = {"format_version": 2, "pipe_name": "test-pipe", "episode_character_id": 2,
                   "episode_run_id": "episode-2", "last_checkpoint": cp,
                   "command_history": [{"index": 1, "command": "save-checkpoint", "ok": True,
                                        "result": {"checkpoint": cp}}]}
        driver = cls.write("driver.json", payload)
        close = cls.write("closed-driver.json", {"machine_id": MACHINE, "status": "closed"})
        closure = cls.write("closure.json", {
            "machine_id": MACHINE, "Game": {"exit_code": 1, "forced_owned_job_cleanup": True,
                                           "Job_active_final": 0},
            "SDK_actual_exits": {"sdk_queue": 0, "sdk_application": 0}})
        ledger = cls.write("stale-ledger.json", {"machine_id": MACHINE, "start_date_raw": 100,
            "target_date_raw": 340, "target_days": 10, "last_settled_cycles": 18,
            "last_settled_date_raw": 124})
        next_ref = cls.write("next.json", {"next_sequence": 103})
        origin = cls.write("origin-ledger.json", {"machine_id": MACHINE, "start_date_raw": 100,
                                                 "target_date_raw": 340, "target_days": 10})
        wall = cls.write("wall-origin.json", {"schema": "xar.c23.canonical-cold-prelaunch/v1",
            "machine_id": MACHINE, "original_wall_start_utc": "2026-10-19T03:26:49.420926Z"})
        unknown = cls.write("historical-unknown.json", {
            "pending_cycle": {"auto_sequence": 7, "stage": "auto_unsettled"}})
        sidecar = cls.write("sidecar.json", {"pending": None})
        validator_module = importlib.import_module("xar_autoplayer.cold_checkpoint_validator")
        validator_file: object = validator_module.__file__
        if not isinstance(validator_file, str):
            raise RuntimeError("real validator origin")
        validator_source = file_ref(Path(validator_file))
        cls.validator = PinnedCheckpointValidatorV1(
            validator_source, validate_cold_start_checkpoint_payload_for_pipe)
        refs = BasisRefsV1(settled_ref, seed_ref, gov, semantic_ref, save_ref, full, driver, saved,
                          close, closure, ledger, next_ref, origin, wall, validator_source)
        cls.inputs = CurrentSavedBasisInputsV1(
            MACHINE, "2026-10-21T06:00:00Z",
            CampaignOriginV1(100, 340, 10, "2026-10-19T03:26:49.420926Z", "campaign-1"),
            refs, cls.reader.stat(driver.path), cls.reader.stat(saved.path),
            (UnknownHistoricalRequestV1(7, unknown),), (sidecar,))

    @classmethod
    def cleanup(cls) -> None:
        if not cls.fixture_enabled:
            return
        try:
            if cls.root.exists():
                current = normalize_file_stat_identity_v1(cls.root.stat())
                if current.file_id != cls.root_identity.file_id or cls.root != FIXTURE.resolve(strict=True):
                    raise RuntimeError("owned fixture cleanup identity")
                cls.measure()
                shutil.rmtree(cls.root)
                if cls.root.exists():
                    raise RuntimeError("owned fixture cleanup incomplete")
        finally:
            tempfile.tempdir = cls.before_tempdir
            for key, value in cls.before_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    @classmethod
    def tearDownClass(cls) -> None:
        cls.cleanup()
        if not cls.fixture_enabled:
            return
        print("CURRENT_BASIS_FIXTURE_CLEANED machine_id=" + os.environ["XAR_CURRENT_SAVED_BASIS_MACHINE_ID"],
              "observed_at_utc=" + datetime.now(timezone.utc).isoformat(),
              "peak_allocation_upper_bytes=" + str(cls.peak_upper),
              "root_file_id=" + cls.root_identity.file_id)

    def require_fixture(self) -> None:
        if not self.fixture_enabled:
            self.skipTest("explicit owned fixture root, machine and finite review required")

    def wire(self) -> dict[str, object]:
        return object_row(parse_json(encode_current_saved_basis_v1(self.basis)))

    def reject(self, value: object) -> None:
        with self.assertRaises(ValueError):
            parse_current_saved_basis_v1(value, expected_machine_id=MACHINE)

    def test_real_sdk_producer_json_and_consumer(self) -> None:
        self.require_fixture()
        raw = encode_current_saved_basis_v1(self.basis)
        decoded = decode_current_saved_basis_v1(raw, expected_machine_id=MACHINE)
        result = validate_current_saved_basis_files_v1(
            decoded, reader=self.reader, checkpoint_validator=self.validator)
        self.assertEqual(result.basis, self.basis)
        self.assertEqual(result.driver_body_reads, 1)
        self.assertEqual(result.canonical_checkpoint_validator_calls, 1)
        self.assertEqual(decoded.progress.ledger_cycles, 18)
        self.assertEqual(decoded.progress.settled_cycles, 20)
        self.assertEqual(decoded.progress.checkpoint_count_before, 3)
        self.assertEqual(decoded.progress.checkpoint_count_after, 4)
        self.assertFalse(decoded.progress.maintenance_save_already_accounted)
        self.assertEqual(decoded.frame.revision, 11)
        self.assertEqual(decoded.next_sequence, 103)
        self.assertEqual(decoded.to_wire()["power_loss_durability"], "not_asserted")

    def test_wrong_extra_missing_and_null_fields(self) -> None:
        for key in self.wire():
            value = self.wire()
            del value[key]
            with self.subTest(missing=key):
                self.reject(value)
        for key in ("schema", "frame", "origin", "refs", "progress", "checkpoint",
                    "driver_identity", "sidecars", "unknown_requests"):
            value = self.wire()
            value[key] = None
            with self.subTest(null=key):
                self.reject(value)
        for key in ("saved_basis", "save10480", "loaded_cycles", "decision_overlay_visible"):
            value = self.wire()
            value[key] = False
            self.reject(value)

    def test_exact_integer_and_boolean_types(self) -> None:
        for key in ("completed_cycles", "next_sequence", "ordinary_cycle_credit", "game_day_credit"):
            for bad in (True, False, 20.0, "20", None):
                value = self.wire()
                value[key] = bad
                with self.subTest(key=key, bad=bad):
                    self.reject(value)
        for key in ("revision", "native_revision", "date_raw", "actor_character_id"):
            for bad in (True, 1.0, "1", None):
                value = self.wire()
                frame = object_row(value["frame"])
                frame[key] = bad
                value["frame"] = frame
                self.reject(value)

    def test_64_bit_identity_precision_roundtrip(self) -> None:
        value = self.wire()
        huge = str((1 << 127) + 17)
        identity = object_row(value["driver_identity"])
        identity["file_id"] = huge
        identity["mtime_ns"] = "1792563000000000001"
        value["driver_identity"] = identity
        model = parse_current_saved_basis_v1(value, expected_machine_id=MACHINE)
        restored = decode_current_saved_basis_v1(
            encode_current_saved_basis_v1(model), expected_machine_id=MACHINE)
        self.assertEqual(restored.driver_identity.file_id, huge)
        self.assertEqual(restored.driver_identity.mtime_ns, "1792563000000000001")
        for bad in (int(huge), float(huge), "0" + huge, "+1", "-0", True, None):
            broken = self.wire()
            entry = object_row(broken["driver_identity"])
            entry["file_id"] = bad
            broken["driver_identity"] = entry
            self.reject(broken)

    def test_serialization_type_domain_and_duplicate_keys(self) -> None:
        value = self.wire()
        value["sidecars"] = tuple(self.basis.sidecars)
        self.reject(value)
        for raw in (b'{"schema":"x","schema":"y"}', b'{"a":{"x":1,"x":2}}'):
            with self.assertRaises(ValueError):
                decode_current_saved_basis_v1(raw, expected_machine_id=MACHINE)
        value = self.wire()
        goal = object_row(value["campaign_goal_anchor"])
        goal["unsafe"] = 1 << 63
        value["campaign_goal_anchor"] = goal
        self.reject(value)

    def test_machine_episode_and_original_origin(self) -> None:
        value = self.wire()
        value["machine_id"] = "other-machine"
        self.reject(value)
        value = self.wire()
        frame = object_row(value["frame"])
        frame["actor_character_id"] = 99
        value["frame"] = frame
        self.reject(value)
        for key, number in (("start_date_raw", 124), ("target_date_raw", 364), ("target_days", 11)):
            value = self.wire()
            origin = object_row(value["origin"])
            origin[key] = number
            value["origin"] = origin
            self.reject(value)

    def test_unknown_lineage_cannot_be_replayed_or_credited(self) -> None:
        for key, bad in (("status", "completed"), ("replayed", True),
                         ("cycle_credit", True), ("cycle_credit", 1), ("day_credit", 1),
                         ("sequence", 103), ("sequence", 7.0)):
            value = self.wire()
            unknown = object_row(rows(value["unknown_requests"])[0])
            unknown[key] = bad
            value["unknown_requests"] = [unknown]
            self.reject(value)
        value = self.wire()
        value["unknown_requests"] = [self.basis.unknown_requests[0].to_wire()] * 2
        self.reject(value)

    def test_stale_ledger_progress_cannot_lead_actual(self) -> None:
        for key, bad in (("ledger_cycles", 21), ("ledger_date_raw", 172),
                         ("settled_cycles", 19), ("settled_date_raw", 124),
                         ("checkpoint_count_after", 5), ("maintenance_save_already_accounted", 0)):
            value = self.wire()
            progress = object_row(value["progress"])
            progress[key] = bad
            value["progress"] = progress
            self.reject(value)

    def test_corrupt_evidence_is_rejected_before_sdk(self) -> None:
        self.require_fixture()
        reference = self.inputs.refs.save_response
        reader = OverrideReader({reference.path: b"{}"})
        with self.assertRaisesRegex(ValueError, "evidence bytes/SHA drift"):
            validate_current_saved_basis_files_v1(
                self.basis, reader=reader, checkpoint_validator=self.validator)

    def test_optional_sidecar_and_null_lifecycle_retained(self) -> None:
        self.require_fixture()
        ref = self.write("sidecar-without-pending.json", {"actor_character_id": 2})
        value = build_current_saved_basis_v1(replace(self.inputs, sidecars=(ref,)),
            reader=self.reader, checkpoint_validator=self.validator)
        self.assertNotIn("pending", object_row(parse_json(Path(ref.path).read_bytes())))
        self.assertEqual(value.sidecars, (ref,))
        self.assertIsNone(value.checkpoint["succession_lifecycle"])

    def test_real_semantic_producer_rejects_wrong_types(self) -> None:
        self.require_fixture()
        for index, bad in enumerate((True, 2.0, None, "2")):
            row = object_row(parse_json(Path(self.inputs.refs.semantic_response.path).read_bytes()))
            result = object_row(row["result"])
            body = object_row(result["structured_content"])
            body["episode_character_id"] = bad
            result["structured_content"] = body
            row["result"] = result
            ref = self.write("bad-sem-" + str(index) + ".json", row)
            inputs = replace(self.inputs, refs=replace(self.inputs.refs, semantic_response=ref))
            with self.assertRaises(ValueError):
                build_current_saved_basis_v1(inputs, reader=self.reader, checkpoint_validator=self.validator)

    def test_request_sequence_floor_types_and_replay(self) -> None:
        self.require_fixture()
        cases: tuple[tuple[str, object], ...] = (
            ("semantic", None), ("semantic", True), ("semantic", 101.0),
            ("semantic", 100), ("save", 101), ("save", False),
            ("save", 102.0), ("next", 102), ("next", 100))
        for index, (kind, bad) in enumerate(cases):
            source = self.inputs.refs.semantic_response if kind == "semantic" else (
                self.inputs.refs.save_response if kind == "save" else self.inputs.refs.next)
            row = object_row(parse_json(Path(source.path).read_bytes()))
            request = row if kind == "next" else object_row(row["request"])
            key = "next_sequence" if kind == "next" else "sequence"
            if bad is None:
                request.pop(key)
            else:
                request[key] = bad
            if kind != "next":
                row["request"] = request
            ref = self.write("wrong-sequence-" + str(index) + ".json", row)
            refs = replace(self.inputs.refs, semantic_response=ref) if kind == "semantic" else (
                replace(self.inputs.refs, save_response=ref) if kind == "save" else
                replace(self.inputs.refs, next=ref))
            with self.assertRaises(ValueError):
                build_current_saved_basis_v1(replace(self.inputs, refs=refs),
                    reader=self.reader, checkpoint_validator=self.validator)



# Synthetic closed-epoch receipts exercise the real shared producer and consumer.
from tools.g2_saved_campaign import current_saved_basis_v1 as epoch_api


class EpochMemoryReader:
    def __init__(self) -> None:
        self.raw: dict[str, bytes] = {}
        self.identities: dict[str, FileStatIdentityV1] = {}
        self.read_paths: list[str] = []
        self.stat_paths: list[str] = []

    def put(self, name: str, value: object) -> ExactRefV1:
        path = "/epoch/" + name
        data = json_bytes(value)
        self.raw[path] = data
        return ExactRefV1(path, len(data), hashlib.sha256(data).hexdigest())

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        self.read_paths.append(reference.path)
        if reference.bytes > limit:
            raise ValueError("bounded fixture")
        return self.raw[reference.path]

    def stat(self, path: str) -> FileStatIdentityV1:
        self.stat_paths.append(path)
        return self.identities[path]


class FailureEpochFixture:
    def __init__(self) -> None:
        self.reader = r = EpochMemoryReader()
        old = pure_basis()
        old = replace(old, refs=replace(old.refs, driver=ExactRefV1("/epoch/driver-state.json", 1, "a" * 64)))
        self.checkpoint: dict[str, object] = {
            "history_index": 1, "date_raw": old.frame.date_raw,
            "path": old.refs.save.path, "sha256": old.refs.save.sha256,
        }
        original_review = r.put("business-review.json", {
            "Driver": {"recorded_identity": {"bridge_pid": 41}}})
        saved = r.put("saved-response.json", {
            "request": {"tool": "ck3_save_checkpoint"},
            "result": {"is_error": False, "result_type": "complete",
                "structured_content": {"checkpoint": self.checkpoint}}})
        old = replace(old, refs=replace(old.refs, driver_close=original_review, save_response=saved))
        self.old = old
        old_ref = r.put("business-basis.json", old.to_wire())
        launch = r.put("ROOT-ACTUAL-GAME-LAUNCH-C23.json", {
            "machine_id": MACHINE, "pid": 43, "creation_filetime": "134370454913277463",
            "creation_date": "20261021083811.327746+000", "old_save_loaded": True,
            "load_save_name": "xar_checkpoint", "nonwar_only": False})
        sem_request = {"sequence": 103, "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}}
        cap_request = {"sequence": 104, "tool": "ck3_get_capabilities", "arguments": {}}
        sem = r.put("p37-responses/0103-1-result.json", {
            "request": sem_request, "result": {"is_error": False, "result_type": "complete",
                "structured_content": {"date_raw": old.frame.date_raw,
                    "episode_character_id": old.frame.actor_character_id,
                    "episode_run_id": old.frame.episode_run_id, "paused": True,
                    "map_ready": True, "one_life_terminal": False,
                    "campaign_goal": old.campaign_goal_anchor}}})
        cap = r.put("p37-responses/0104-1-result.json", {
            "request": cap_request, "client_error": "C11 normal checkpoint cold denied: fresh cold SEM then CAP required",
            "replay_allowed": False, "original_response": sem.path})
        sem_req = r.put("p37-requests/0103-1-result.json", sem_request)
        cap_req = r.put("p37-requests/0104-1-result.json", cap_request)
        failure = r.put("first-exception.json", {
            "stage": "request_dispatch", "replay_allowed": False,
            "request_identity": {"sequence": 103, "tool": sem_request["tool"], "command": None},
            "exception_tree": {"type": "ValueError",
                "message": "founding score anchor requires actual paused1066 frame"}})
        inflight = r.put("inflight.json", {
            "sequence": 103, "tool": sem_request["tool"], "arguments": {},
            "scope": "cold-start-readiness-only", "outer_sequence_consumed": False,
            "business_credit": 0, "original_P01_response_replayed": False,
            "request_file": sem_req.path})
        inventory = r.put("inventory.json", {
            "schema": "xar.current-saved-closed-request-inventory/v1",
            "machine_id": MACHINE, "reviewer": "/root", "runtime_root": "/epoch",
            "observed_at_utc": "2026-10-21T06:02:00Z", "closed_directory_snapshot": True,
            "epoch_start_sequence": 103, "unmatched_new_request_files": [],
            "unmatched_new_response_files": [], "request_refs": [sem_req.to_wire(), cap_req.to_wire()],
            "response_refs": [sem.to_wire(), cap.to_wire()]})
        nxt = r.put("next.json", {"next_sequence": 105})
        processes = [{
            "role": role, "pid": pid, "creation_filetime": birth,
            "executable": "/base/python.exe", "exit_code": code,
            "kernel_exit_observed": True, "wait_result": 0, "observation_error": None,
        } for role, pid, birth, code in (
            ("sdk_queue", 47, "134370464192232765", 1),
            ("sdk_application", 53, "134370464225272880", 0))]
        sdk = r.put("sdk-closed.json", {"machine_id": MACHINE,
            "status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED", "processes": processes,
            "normal": False, "launcher_exit_code": 1})
        game = {"pid": 43, "creation_filetime": "134370454913277463"}
        supervisor = r.put("supervisor-closed.json", {
            "machine_id": MACHINE, "observed_at_utc": "2026-10-21T06:01:00Z",
            "cleanup_classification": "FORCED_OWNED_GAME_CLEANUP",
            "sdk_actual_exit": {"status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED",
                "processes": processes, "normal": False},
            "known_preload_phase": {"before": game, "after": game},
            "owned_cleanup": {"ck3_pid": 43, "ck3_exit_code": 1,
                "ck3_creation_date": "20261021083811.327746+000",
                "job_active_processes_final": 0, "tree_gone": True,
                "cleanup_proven": True, "ok": True, "contract_errors": []}})
        self.driver_id = FileStatIdentityV1(17, "9007199254740997", "1792563000000000005")
        driver_ref = ExactRefV1(old.refs.driver.path, 17, "b" * 64)
        def stat_wire(item: FileStatIdentityV1) -> dict[str, object]:
            return {**item.to_wire(), "device": "6505083400996699863", "links": 1}
        review = r.put("driver-review.json", {
            "schema": "xar.readonly-cold-epoch-Driver-SAVE-review/v1",
            "status": "CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_AFTER_READONLY_INIT",
            "machine_id": MACHINE, "original_business_review": original_review.to_wire(),
            "Driver": {"ref": driver_ref.to_wire(), "identity": stat_wire(self.driver_id),
                "format_version": 2, "command_history_count": 2, "last_checkpoint": self.checkpoint,
                "recorded_identity": {"bridge_pid": 43, "episode_character_id": 2,
                    "episode_run_id": old.frame.episode_run_id, "pipe_name": "pipe"},
                "absent_payload_fields": ["session_binding"]},
            "SAVE": {"ref": old.refs.save.to_wire(), "identity": stat_wire(old.save_identity)},
            "actual_saved_cycles": 20, "actual_saved_days": 2,
            "unknown10565_replayed": False,
            "original_whole_wall_origin": old.origin.original_wall_origin_utc})
        self.restore: dict[str, object] = {
            "index": 2, "command": "restore-checkpoint", "ok": True,
            "result": {"step": "restore-checkpoint", "accepted": True, "status": "restored",
                "backend_id": "native-headless", "source": "native-session-cold-start",
                "checkpoint": self.checkpoint, "restored_date_raw": 148, "map_ready": True,
                "lifecycle": {"previous_pid": 41, "pid": 43}}}
        tail = r.put("history-tail.json", {
            "schema": "xar.readonly-cold-epoch-history-tail/v1",
            "machine_id": MACHINE, "driver_review": review.to_wire(),
            "driver_identity": stat_wire(self.driver_id), "checkpoint_history_index": 1,
            "command_history_count": 2, "post_checkpoint_history": [self.restore]})
        validator = r.put("cold_checkpoint_validator.py", {"fixture_source": True})
        canonical = r.put("canonical-qualification.json", {
            "schema": "xar.closed-readonly-epoch-canonical-checkpoint-qualification/v1",
            "machine_id": MACHINE, "status": "ACTUAL_CLOSED_DRIVER_CANONICAL_SAVE_VALIDATED",
            "driver_review": review.to_wire(), "history_tail": tail.to_wire(),
            "checkpoint": old.checkpoint, "Driver_identity": stat_wire(self.driver_id),
            "SAVE_identity": stat_wire(old.save_identity), "Driver_full_read_count": 1,
            "SAVE_full_hash_count": 1, "Driver_full_read_bytes": 17,
            "SAVE_full_hash_bytes": 1, "original_checkpoint_unchanged": True,
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0,
            "actual_constructor_or_Game_RPC_calls": 0,
            "total_Root_A23_Driver_full_reads": 3, "total_Root_A23_SAVE_full_hashes": 2,
            "validator": validator.to_wire()})
        linked = dict(launch=launch, sdk_closed=sdk, supervisor_closed=supervisor,
            game_exit=supervisor, first_exception=failure, semantic_response=sem,
            capability_rejection=cap, inflight=inflight, next=nxt,
            driver_review=review, history_tail=tail)
        for name in ("sdk_pair", "supervisor_sdk_exits", "supervisor_spec", "display_spec",
                     "supervisor_task_closed", "display_task_closed", "supervisor_unregister",
                     "display_unregister", "screen_release", "recording_completed"):
            linked[name] = r.put(name + ".json", {"synthetic_closed_source": name})
        index = r.put("index.json", {
            "schema": "xar.readonly-cold-init-postcheck-abort-closure/v1",
            "status": "CLOSED_NO_BUSINESS_PROGRESS", "machine_id": MACHINE,
            "original_basis_ref": old_ref.to_wire(), "next_sequence": 105,
            "business_completed_cycles": 20, "business_date_raw": 148,
            "original_whole_wall_origin": old.origin.original_wall_origin_utc,
            "SDK_exit_codes": [1, 0], "SDK_normal": False, "Game_exit_code": 1,
            "Game_forced": True, "Game_Job_active_final": 0,
            "all_owned_Tasks_actual_absent": True, "owned_Task_count": 2,
            "original_requests_replayed": False, "new_ordinary_cycle_credit": 0,
            "new_game_day_credit": 0, "new_checkpoint_credit": 0,
            "refs": {key: value.to_wire() for key, value in linked.items()}})
        self.epoch = epoch_api.ReadonlyColdFailureEpochV1(
            MACHINE, "2026-10-21T06:03:00Z",
            epoch_api.ReadonlyColdFailureRefsV1(old_ref, review, tail, index, launch,
                sem, cap, failure, inflight, inventory, sdk, supervisor, supervisor, nxt, canonical),
            epoch_api.ReadonlyClosedDriverFlagsV1(None, None, None, False))
        r.identities[driver_ref.path] = self.driver_id
        r.identities[old.refs.save.path] = old.save_identity

    def validated(self) -> epoch_api.ValidatedReadonlyColdFailureEpochV1:
        return epoch_api.validate_readonly_cold_failure_evidence_v1(self.epoch, reader=self.reader)


class ReadonlyFailureEpochTests(unittest.TestCase):
    def test_historical_sdk_filetime_has_one_json_string_form(self) -> None:
        f = FailureEpochFixture()
        sdk = epoch_api.evidence(f.reader, f.epoch.refs.sdk_closed)
        expected = epoch_api.sdk_without_launcher_v1(sdk)
        processes = epoch_api.rows(sdk["processes"])
        converted: list[dict[str, object]] = []
        for item in processes:
            row = epoch_api.record(item)
            row["creation_filetime"] = int(epoch_api.text(row["creation_filetime"]))
            converted.append(row)
        sdk["processes"] = converted
        self.assertEqual(epoch_api.canonical_json_v1(epoch_api.sdk_without_launcher_v1(sdk)),
            epoch_api.canonical_json_v1(expected))
        for bad in (True, 1.0, "0134370454913277463", "18446744073709551616"):
            changed = copy.deepcopy(sdk)
            first = epoch_api.record(epoch_api.rows(changed["processes"])[0])
            first["creation_filetime"] = bad
            changed["processes"] = [first, epoch_api.rows(changed["processes"])[1]]
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                epoch_api.sdk_without_launcher_v1(changed)

    def test_real_evidence_basis_and_qualification_pipeline(self) -> None:
        f = FailureEpochFixture()
        checked = f.validated()
        self.assertEqual(f.reader.stat_paths, [])
        epoch_ref = f.reader.put("new-epoch.json", f.epoch.to_wire())
        basis = epoch_api.build_readonly_cold_failure_basis_v1(checked,
            epoch_ref=epoch_ref, observed_at_utc="2026-10-21T06:04:00Z",
            sidecars=(), reader=f.reader)
        basis_ref = f.reader.put("new-basis.json", basis.to_wire())
        qualification = epoch_api.build_readonly_cold_failure_qualification_v1(
            checked, basis, basis_ref=basis_ref, reader=f.reader,
            observed_at_utc="2026-10-21T06:04:01Z")
        parsed = epoch_api.parse_readonly_cold_failure_qualification_v1(
            json.loads(json.dumps(qualification.to_wire())), expected_machine_id=MACHINE)
        self.assertEqual(parsed, qualification)
        self.assertEqual((basis.completed_cycles, basis.frame, basis.checkpoint,
            basis.progress, basis.origin, basis.unknown_requests),
            (f.old.completed_cycles, f.old.frame, f.old.checkpoint,
            f.old.progress, f.old.origin, f.old.unknown_requests))
        self.assertEqual((basis.next_sequence, qualification.driver_history_rows), (105, 2))
        self.assertEqual((qualification.driver_body_reads, qualification.save_hash_reads,
            qualification.canonical_checkpoint_validator_calls), (0, 0, 0))
        self.assertEqual((qualification.root_driver_body_reads, qualification.root_save_hash_reads), (3, 2))
        self.assertNotIn(checked.driver_ref.path, f.reader.read_paths)
        self.assertNotIn(checked.save_ref.path, f.reader.read_paths)
        self.assertEqual([p.exit_code for p in checked.sdk_processes], [0, 1])

    def test_warm_evidence_is_immutable_but_cold_requires_current_stat(self) -> None:
        f = FailureEpochFixture()
        checked = f.validated()
        f.reader.identities[checked.driver_ref.path] = replace(f.driver_id, file_id="999")
        self.assertEqual(f.validated(), checked)
        with self.assertRaises(ValueError):
            epoch_api.validate_readonly_cold_failure_epoch_v1(f.epoch, reader=f.reader)

    def test_qualification_does_not_credit_a_forged_basis(self) -> None:
        f = FailureEpochFixture()
        checked = f.validated()
        epoch_ref = f.reader.put("new-epoch.json", f.epoch.to_wire())
        basis = epoch_api.build_readonly_cold_failure_basis_v1(checked,
            epoch_ref=epoch_ref, observed_at_utc="2026-10-21T06:04:00Z", sidecars=(), reader=f.reader)
        drifted = replace(basis, completed_cycles=basis.completed_cycles + 1,
            progress=replace(basis.progress, settled_cycles=basis.completed_cycles + 1))
        reference = f.reader.put("forged-basis.json", drifted.to_wire())
        with self.assertRaises(ValueError):
            epoch_api.build_readonly_cold_failure_qualification_v1(checked, drifted,
                basis_ref=reference, reader=f.reader, observed_at_utc="2026-10-21T06:04:01Z")
        forged = replace(checked, next_sequence=checked.next_sequence + 1)
        with self.assertRaises(ValueError):
            epoch_api.build_readonly_cold_failure_basis_v1(forged,
                epoch_ref=epoch_ref, observed_at_utc="2026-10-21T06:04:00Z", sidecars=(), reader=f.reader)

    def test_epoch_exact_fields_types_and_json(self) -> None:
        f = FailureEpochFixture()
        wire = f.epoch.to_wire()
        self.assertEqual(epoch_api.parse_readonly_cold_failure_epoch_v1(
            json.loads(json.dumps(wire)), expected_machine_id=MACHINE), f.epoch)
        for key in wire:
            for bad in (None, True, 1.0):
                with self.subTest(key=key, bad=bad):
                    changed = dict(wire); changed[key] = bad
                    with self.assertRaises(ValueError):
                        epoch_api.parse_readonly_cold_failure_epoch_v1(changed, expected_machine_id=MACHINE)
            changed = dict(wire); del changed[key]
            with self.assertRaises(ValueError):
                epoch_api.parse_readonly_cold_failure_epoch_v1(changed, expected_machine_id=MACHINE)
        for key in ("managed_restore_transaction", "rollback_war_failure", "succession_expectation", "session_binding_present"):
            flags = dict(epoch_api.record(wire["driver_payload_flags"]))
            del flags[key]
            with self.assertRaises(ValueError):
                epoch_api.parse_readonly_closed_driver_flags_v1(flags)

    def test_restore_is_not_general_permission_for_history(self) -> None:
        f = FailureEpochFixture()
        for key, bad in (("command", "advance-days"), ("ok", False), ("index", True),
                         ("index", 2.0), ("result", None)):
            changed = copy.deepcopy(f.restore); changed[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                epoch_api._readonly_restore_row_v1(changed, checkpoint=epoch_api.json_object(f.checkpoint),
                    previous_pid=41, current_pid=43)
        result_cases: tuple[tuple[str, object], ...] = (
            ("accepted", False), ("checkpoint", {}), ("restored_date_raw", 149),
            ("map_ready", False), ("source", "unknown"))
        for key, result_bad in result_cases:
            changed = copy.deepcopy(f.restore)
            result = epoch_api.record(changed["result"]); result[key] = result_bad; changed["result"] = result
            with self.subTest(key=key, bad=result_bad), self.assertRaises(ValueError):
                epoch_api._readonly_restore_row_v1(changed, checkpoint=epoch_api.json_object(f.checkpoint),
                    previous_pid=41, current_pid=43)

    def test_real_evidence_rejects_mutation_stale_proof_and_missing(self) -> None:
        f = FailureEpochFixture()
        changed: dict[str, object]
        for name in ("semantic_response", "capability_rejection", "history_tail",
                     "sdk_closed", "canonical_qualification", "request_inventory"):
            reference = dict(f.epoch.refs.items())[name]
            original = f.reader.raw[reference.path]
            f.reader.raw[reference.path] = b"{}"
            with self.subTest(name=name), self.assertRaises(ValueError):
                f.validated()
            f.reader.raw[reference.path] = original
        wire = f.epoch.to_wire()
        for name in epoch_api.record(wire["refs"]):
            refs = dict(epoch_api.record(wire["refs"])); del refs[name]
            changed = dict(wire); changed["refs"] = refs
            with self.subTest(name=name), self.assertRaises(ValueError):
                epoch_api.parse_readonly_cold_failure_epoch_v1(changed, expected_machine_id=MACHINE)

    def test_qualification_rejects_fake_read_counts_and_wire_identities(self) -> None:
        f = FailureEpochFixture()
        changed: dict[str, object]
        checked = f.validated()
        epoch_ref = f.reader.put("new-epoch.json", f.epoch.to_wire())
        basis = epoch_api.build_readonly_cold_failure_basis_v1(checked,
            epoch_ref=epoch_ref, observed_at_utc="2026-10-21T06:04:00Z", sidecars=(), reader=f.reader)
        br = f.reader.put("new-basis.json", basis.to_wire())
        q = epoch_api.build_readonly_cold_failure_qualification_v1(checked, basis,
            basis_ref=br, reader=f.reader, observed_at_utc="2026-10-21T06:04:01Z").to_wire()
        for key in ("driver_body_reads", "save_hash_reads", "driver_history_rows",
                    "root_driver_body_reads", "root_save_hash_reads"):
            for bad in (None, True, 1.0, -1):
                changed = dict(q); changed[key] = bad
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    epoch_api.parse_readonly_cold_failure_qualification_v1(changed, expected_machine_id=MACHINE)
        for bad_id in ("01", 9007199254740993, True, 1.0):
            changed = dict(q); identity = dict(epoch_api.record(q["driver_identity_after"]))
            identity["file_id"] = bad_id; changed["driver_identity_after"] = identity
            with self.subTest(bad_id=bad_id), self.assertRaises(ValueError):
                epoch_api.parse_readonly_cold_failure_qualification_v1(changed, expected_machine_id=MACHINE)


if __name__ == "__main__":
    unittest.main()


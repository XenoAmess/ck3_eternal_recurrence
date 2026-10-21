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

        self.checkpoint.update(status="saved",size=old.refs.save.bytes,name="xar_checkpoint.ck3",
            overwrite_confirmed=True,strategy="native-autosave-command-v1",
            episode_character_id=old.frame.actor_character_id,episode_run_id=old.frame.episode_run_id,
            succession_lifecycle=None)
        seed=r.put("original-seed.json",{"schema":"g2.queue.cumulative-loop/v1","pending_cycle":None,"pending_checkpoint":None,"terminal":None,"completed_cycles":old.completed_cycles,
            "before":old.frame.to_wire(),"start_date_raw":old.origin.start_date_raw,
            "campaign_goal_anchor":old.campaign_goal_anchor,"actual_saved_checkpoint":self.checkpoint,
            "counts":{"checkpoint_saved":old.progress.checkpoint_count_after}})
        ledger=r.put("original-ledger.json",{"machine_id":MACHINE,
            "last_settled_cycles":old.progress.ledger_cycles,"last_settled_date_raw":old.progress.ledger_date_raw,
            "start_date_raw":old.origin.start_date_raw,"target_date_raw":old.origin.target_date_raw,"target_days":old.origin.target_days})
        placeholders={name:r.put("original-"+name+".json",{}) for name,ref in old.refs.items()
            if name not in {"save","driver","seed","ledger"}}
        old=replace(old,refs=replace(old.refs,**placeholders,seed=seed,ledger=ledger))
        original_review = r.put("business-review.json", {
            "Driver": {"recorded_identity": {"bridge_pid": 41}}})
        saved = r.put("saved-response.json", {
            "request": {"tool": "ck3_save_checkpoint"},
            "result": {"is_error": False, "result_type": "complete",
                "structured_content": {"checkpoint": self.checkpoint}}})
        old = replace(old, refs=replace(old.refs, driver_close=original_review, save_response=saved, governance=r.put("saved-governance.json", {"governance_result_state":None,"pending_focus":None,"pending_cycle":None,"completed_cycles":old.completed_cycles})))
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


class CapPretransportFailureFixture:
    """Portable two-epoch evidence; all receipts and source snippets are synthetic."""

    def __init__(self) -> None:
        base = FailureEpochFixture()
        self.machine = MACHINE
        self.reader = r = base.reader
        prior = base.validated()
        prior_epoch_ref = r.put("prior-epoch.json", base.epoch.to_wire())
        self.previous_basis = old = epoch_api.build_readonly_cold_failure_basis_v1(prior,
            epoch_ref=prior_epoch_ref, observed_at_utc="2026-10-21T06:04:00Z", sidecars=(), reader=r)
        old_ref = r.put("prior-basis.json", old.to_wire())
        self.checkpoint = base.checkpoint

        def put(name: str, value: object) -> ExactRefV1:
            return r.put("cap/"+name, value)

        def put_source(name: str, source: str) -> ExactRefV1:
            path = "/epoch/cap/"+name
            raw = source.encode()
            r.raw[path] = raw
            return ExactRefV1(path, len(raw), hashlib.sha256(raw).hexdigest())

        def stat_wire(identity: FileStatIdentityV1) -> dict[str, object]:
            return dict(identity.to_wire())

        launch = put("ROOT-ACTUAL-GAME-LAUNCH-C23.json", {
            "machine_id": MACHINE, "pid": 61, "creation_filetime": 134370617141148601,
            "creation_date": "20261021130817.114860+000", "old_save_loaded": True,
            "load_save_name": "xar_checkpoint", "nonwar_only": False})
        semseq = old.next_sequence
        semrequest = {"sequence": semseq, "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}}
        caprequest = {"sequence": semseq+1, "tool": "ck3_get_capabilities", "arguments": {}}
        sem = put(f"p37-responses/{semseq:04d}-1-result.json", {
            "request": semrequest, "result": {"is_error": False, "result_type": "complete",
                "structured_content": {"date_raw": old.frame.date_raw,
                    "episode_character_id": old.frame.actor_character_id,
                    "episode_run_id": old.frame.episode_run_id, "paused": True,
                    "map_ready": True, "one_life_terminal": False, "campaign_goal": old.campaign_goal_anchor}}})
        cap = put(f"p37-responses/{semseq+1:04d}-1-result.json", {
            "request": caprequest, "client_error": "ValueError('object')", "replay_allowed": False})
        semreq = put(f"p37-requests/{semseq:04d}-1-result.json", semrequest)
        capreq = put(f"p37-requests/{semseq+1:04d}-1-result.json", caprequest)
        after = put(f"p37-queue/{semseq:04d}-after-result.json", {
            "at_utc": "2026-10-21T06:05:01Z", "request": semreq.path, "response": sem.path,
            "tool": semrequest["tool"], "actual_status": "cold_readiness_verified",
            "loading_attempts": 0, "new_business_credit": 0})
        flat = {"sequence": semseq+1, "tool": "ck3_get_capabilities", "arguments": {},
            "request_file": capreq.path, "at_utc": "2026-10-21T06:05:02Z", "replay_allowed": False}
        inflight = put(f"p37-queue/INFLIGHT-{semseq+1:04d}.json", flat)
        before = put(f"p37-queue/{semseq+1:04d}-before-action.json", flat)
        guard = put_source("tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py",
            'def _json_bytes(value: object) -> bytes:\n'
            '    return json.dumps(json_object(value)).encode()\n'
            'def _inflight_guard(context):\n'
            '    return _json_bytes(context.get("request"))\n'
            'class OriginalSession:\n'
            '    async def call_tool(self):\n'
            '        guard_current_saved_request_v1()\n'
            '        return await self._call()\n')
        queue = put_source("root_p37c23_sdk_queue.py", 'async def call():\n    return None\n')
        failure = put("first-exception.json", {"stage": "sdk_call", "replay_allowed": False,
            "request_identity": {"sequence": semseq+1, "tool": "ck3_get_capabilities", "command": None},
            "exception_tree": {"type": "ValueError", "message": "object"},
            "traceback_truncated": False, "locals_captured": False,
            "traceback": f'File "{queue.path}", line 1, in call\n'
                f'File "{guard.path}", line 7, in call_tool\n'
                f'File "{guard.path}", line 3, in guard_current_saved_request_v1\n'
                f'File "{guard.path}", line 4, in _inflight_guard\n'
                '    _json_bytes(context.get("request"))\nValueError: object'})
        halt = put("HALT.json", {"error_type": "RuntimeError",
            "message": "client outcome unknown; original request must not be resent",
            "first_exception_receipt": failure.path, "original_request": caprequest,
            "original_response": cap.path, "replay_allowed": False,
            "sdk_kept_alive_for_original_collection": True, "next_sequence": semseq+2})
        inventory = put("inventory.json", {"schema": "xar.current-saved-closed-request-inventory/v1",
            "machine_id": MACHINE, "reviewer": "/root", "runtime_root": "/epoch/cap",
            "observed_at_utc": "2026-10-21T06:06:00Z", "closed_directory_snapshot": True,
            "epoch_start_sequence": semseq, "unmatched_new_request_files": [], "unmatched_new_response_files": [],
            "request_refs": [semreq.to_wire(), capreq.to_wire()], "response_refs": [sem.to_wire(), cap.to_wire()]})
        nxt = put("next.json", {"next_sequence": semseq+2})
        processes = [{"role": role, "pid": pid, "creation_filetime": birth,
            "executable": "/base/python.exe", "exit_code": code, "kernel_exit_observed": True,
            "wait_result": 0, "observation_error": None} for role, pid, birth, code in (
                ("sdk_queue", 67, 134370617141148602, 1), ("sdk_application", 71, 134370617141148603, 0))]
        sdk = put("sdk-closed.json", {"machine_id": MACHINE, "status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED",
            "processes": processes, "normal": False, "launcher_exit_code": 1})
        game = {"pid": 61, "creation_filetime": 134370617141148601}
        supervisor = put("supervisor-closed.json", {"machine_id": MACHINE,
            "cleanup_classification": "FORCED_OWNED_GAME_CLEANUP",
            "sdk_actual_exit": {"status": "ACTUAL_BOTH_SDK_EXITS_OBSERVED", "processes": processes, "normal": False},
            "known_preload_phase": {"before": game, "after": game},
            "owned_cleanup": {"ck3_pid": 61, "ck3_exit_code": 1,
                "ck3_creation_date": "20261021130817.114860+000", "job_active_processes_final": 0,
                "tree_gone": True, "cleanup_proven": True, "ok": True, "contract_errors": []}})
        self.driver_id = FileStatIdentityV1(23, "9007199254741001", "1792563000000000011")
        driver_ref = ExactRefV1(old.refs.driver.path, 23, "c"*64)
        self.restore = copy.deepcopy(base.restore)
        self.restore["index"] = prior.history_count+1
        result = object_row(self.restore["result"])
        result["lifecycle"] = {"previous_pid": 43, "pid": 61}
        self.restore["result"] = result
        raw = put("raw-observation.json", {"schema": "xar.raw-closed-driver-observation/v1",
            "status": "OBSERVED_NOT_QUALIFIED", "machine_id": MACHINE,
            "Driver_ref": driver_ref.to_wire(), "Driver_identity": stat_wire(self.driver_id),
            "SAVE_identity": stat_wire(old.save_identity), "format_version": 2, "command_history_count": 3,
            "last_checkpoint": self.checkpoint, "post_checkpoint_history": [base.restore, self.restore],
            "recorded_identity": {"bridge_pid": 61, "episode_character_id": old.frame.actor_character_id,
                "episode_run_id": old.frame.episode_run_id, "pipe_name": "pipe"},
            "campaign_goal": old.campaign_goal_anchor, "session_binding_present": False,
            "session_binding_value": None, "payload_top_keys": ["command_history"],
            "driver_payload_flags": {"managed_restore_transaction": None, "rollback_war_failure": None,
                "succession_expectation": None, "rollback_war_failures": []}})
        review = put("driver-review.json", {"schema": "xar.readonly-cap-pretransport-Driver-SAVE-review/v2",
            "status": "CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_AFTER_CAP_GUARD_FAILURE", "machine_id": MACHINE,
            "original_business_review": old.refs.driver_close.to_wire(),
            "Driver": {"ref": driver_ref.to_wire(), "identity": stat_wire(self.driver_id),
                "format_version": 2, "command_history_count": 3, "last_checkpoint": self.checkpoint,
                "recorded_identity": {"bridge_pid": 61, "episode_character_id": old.frame.actor_character_id,
                    "episode_run_id": old.frame.episode_run_id, "pipe_name": "pipe"},
                "absent_payload_fields": ["session_binding"]},
            "SAVE": {"ref": old.refs.save.to_wire(), "identity": stat_wire(old.save_identity)},
            "raw_Driver_body_read_count": 2, "Driver_body_bytes_read": 46,
            "raw_observation": raw.to_wire(),
            "SAVE_full_hash_count": 0, "SAVE_body_bytes_read": 0,
            "actual_saved_cycles": old.completed_cycles, "actual_saved_days": 2,
            "unknown10565_replayed": False, "original_whole_wall_origin": old.origin.original_wall_origin_utc})
        tail = put("history-tail.json", {"schema": "xar.readonly-cap-pretransport-history-tail/v2",
            "machine_id": MACHINE, "driver_review": review.to_wire(), "driver_identity": stat_wire(self.driver_id),
            "checkpoint_history_index": 1, "command_history_count": 3,
            "post_checkpoint_history": [base.restore, self.restore]})
        reuse = put("canonical-reuse.json", {"schema": "xar.closed-cap-pretransport-save-identity-reuse/v2",
            "status": "PREVIOUS_CANONICAL_SAVE_IDENTITY_REUSED", "machine_id": MACHINE,
            "observed_at_utc": "2026-10-21T06:06:01Z",
            "validation_mode": "previous_canonical_save_identity_reuse", "current_canonical_API_executed": False,
            "previous_canonical_qualification": base.epoch.refs.canonical_qualification.to_wire(),
            "driver_review": review.to_wire(), "history_tail": tail.to_wire(), "checkpoint": old.checkpoint,
            "Driver_identity": stat_wire(self.driver_id), "SAVE_identity": stat_wire(old.save_identity),
            "Driver_full_read_count": 2, "Driver_full_read_bytes": 46,
            "SAVE_full_hash_count": 0, "SAVE_full_hash_bytes": 0, "SAVE_hash_reused_by_exact_identity": True,
            "original_checkpoint_unchanged": True, "validator": old.refs.checkpoint_validator.to_wire(),
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0, "actual_constructor_or_Game_RPC_calls": 0})
        linked = dict(launch=launch, sdk_closed=sdk, supervisor_closed=supervisor, game_exit=supervisor,
            first_exception=failure, semantic_response=sem, semantic_after=after, capability_rejection=cap,
            inflight=inflight, before_action=before, halt=halt, request_inventory=inventory, next=nxt,
            driver_review=review, history_tail=tail, guard_source=guard, queue_source=queue)
        for key in ("sdk_pair", "supervisor_sdk_exits", "supervisor_spec", "display_spec", "supervisor_task_closed",
            "display_task_closed", "supervisor_unregister", "display_unregister", "screen_release", "recording_completed"):
            linked[key] = put(key+".json", {"synthetic_closed_source": key})
        index = put("index.json", {"schema": "xar.readonly-cap-pretransport-abort-closure/v2",
            "status": "CLOSED_CAP_PRETRANSPORT_GUARD_FAILURE", "machine_id": MACHINE,
            "original_basis_ref": old_ref.to_wire(), "next_sequence": semseq+2,
            "business_completed_cycles": old.completed_cycles, "business_date_raw": old.frame.date_raw,
            "original_whole_wall_origin": old.origin.original_wall_origin_utc, "SDK_exit_codes": [1, 0],
            "SDK_normal": False, "Game_exit_code": 1, "Game_forced": True, "Game_Job_active_final": 0,
            "all_owned_Tasks_actual_absent": True, "owned_Task_count": 2, "original_requests_replayed": False,
            "new_ordinary_cycle_credit": 0, "new_game_day_credit": 0, "new_checkpoint_credit": 0,
            "refs": {key: value.to_wire() for key, value in linked.items()}})
        self.refs = epoch_api.CapPretransportFailureRefsV2(old_ref, review, tail, index, launch, sem, after,
            cap, failure, inflight, before, halt, inventory, sdk, supervisor, supervisor, nxt, reuse)
        self.epoch = epoch_api.CapPretransportFailureEpochV2(MACHINE, "2026-10-21T06:07:00Z", self.refs,
            epoch_api.ReadonlyClosedDriverFlagsV1(None, None, None, False))
        r.identities[driver_ref.path] = self.driver_id
        r.stat_paths.clear()
        r.read_paths.clear()

    def validated(self) -> epoch_api.ValidatedCapPretransportFailureEpochV2:
        return epoch_api.validate_cap_pretransport_failure_evidence_v2(self.epoch, reader=self.reader)

    def changed(self, name: str, value: object) -> epoch_api.CapPretransportFailureEpochV2:
        """Rebind a changed receipt and its closure row, so semantic guards run."""
        old_ref = dict(self.refs.items())[name]
        data = json_bytes(value)
        self.reader.raw[old_ref.path] = data
        new_ref = ExactRefV1(old_ref.path, len(data), hashlib.sha256(data).hexdigest())
        refs = replace(self.refs, **{name: new_ref})
        if name in object_row(epoch_api.evidence(self.reader, self.refs.closure_index)["refs"]):
            index = epoch_api.evidence(self.reader, self.refs.closure_index)
            linked = object_row(index["refs"]); linked[name] = new_ref.to_wire(); index["refs"] = linked
            index_ref = self.reader.put("cap/changed-index.json", index)
            refs = replace(refs, closure_index=index_ref)
        return replace(self.epoch, refs=refs)


class CapPretransportFailureTests(unittest.TestCase):
    def test_real_two_epoch_pipeline_and_json(self) -> None:
        f = CapPretransportFailureFixture()
        checked = f.validated()
        self.assertEqual(f.reader.stat_paths, [])
        self.assertEqual((checked.previous_history_count, checked.history_count, len(checked.history_rows)), (2, 3, 2))
        self.assertEqual(checked.old_game.creation_filetime, "134370617141148601")
        self.assertEqual([p.exit_code for p in checked.sdk_processes], [0, 1])
        er = f.reader.put("cap/new-epoch.json", f.epoch.to_wire())
        basis = epoch_api.build_cap_pretransport_failure_basis_v2(checked, epoch_ref=er,
            observed_at_utc="2026-10-21T06:08:00Z", sidecars=(), reader=f.reader)
        br = f.reader.put("cap/new-basis.json", basis.to_wire())
        qual = epoch_api.build_cap_pretransport_failure_qualification_v2(checked, basis,
            basis_ref=br, reader=f.reader, observed_at_utc="2026-10-21T06:08:01Z")
        self.assertEqual(epoch_api.parse_cap_pretransport_failure_qualification_v2(
            json.loads(json_bytes(qual.to_wire())), expected_machine_id=MACHINE), qual)
        self.assertEqual(epoch_api.parse_cap_pretransport_failure_epoch_v2(
            json.loads(json_bytes(f.epoch.to_wire())), expected_machine_id=MACHINE), f.epoch)
        for key in ("origin", "frame", "completed_cycles", "checkpoint", "campaign_goal_anchor", "progress", "unknown_requests"):
            self.assertEqual(getattr(basis, key), getattr(f.previous_basis, key))
        self.assertEqual((basis.next_sequence, qual.root_driver_body_reads, qual.root_save_hash_reads), (107, 2, 0))
        self.assertEqual((qual.driver_body_reads, qual.save_hash_reads, qual.canonical_checkpoint_validator_calls), (0, 0, 0))
        self.assertNotIn(checked.driver_ref.path, f.reader.read_paths)
        self.assertNotIn(checked.save_ref.path, f.reader.read_paths)

    def test_warm_history_does_not_mistake_sdk_persist_for_tampering(self) -> None:
        f = CapPretransportFailureFixture(); checked = f.validated()
        f.reader.identities[checked.driver_ref.path] = replace(checked.driver_identity, file_id="12345")
        self.assertEqual(f.validated(), checked)
        with self.assertRaises(ValueError):
            epoch_api.validate_cap_pretransport_failure_epoch_v2(f.epoch, reader=f.reader)

    def test_exact_fields_wrong_types_and_schema_branches(self) -> None:
        f = CapPretransportFailureFixture(); wire = f.epoch.to_wire()
        for key in wire:
            for bad in (None, True, 1.0):
                changed: dict[str, object] = dict(wire); changed[key] = bad
                with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                    epoch_api.parse_cap_pretransport_failure_epoch_v2(changed, expected_machine_id=MACHINE)
            missing = dict(wire); del missing[key]
            with self.assertRaises(ValueError):
                epoch_api.parse_cap_pretransport_failure_epoch_v2(missing, expected_machine_id=MACHINE)
        for key in epoch_api.record(wire["refs"]):
            missing_refs = dict(epoch_api.record(wire["refs"])); del missing_refs[key]
            changed = dict(wire); changed["refs"] = missing_refs
            with self.assertRaises(ValueError):
                epoch_api.parse_cap_pretransport_failure_epoch_v2(changed, expected_machine_id=MACHINE)
        with self.assertRaises(ValueError):
            epoch_api.parse_readonly_cold_failure_epoch_v1(wire, expected_machine_id=MACHINE)
        with self.assertRaises(ValueError):
            epoch_api.parse_cap_pretransport_failure_epoch_v2(FailureEpochFixture().epoch.to_wire(), expected_machine_id=MACHINE)

    def test_sem_cap_unknown_and_source_proofs_are_not_interchangeable(self) -> None:
        cases: tuple[tuple[str, str, object], ...] = (
            ("semantic_after", "actual_status", "complete"), ("semantic_after", "new_business_credit", 1),
            ("capability_rejection", "result", None), ("capability_rejection", "replay_allowed", True),
            ("first_exception", "stage", "request_dispatch"), ("first_exception", "traceback", "same error no source"),
            ("inflight", "sequence", True), ("inflight", "arguments", []),
            ("inflight", "request", {}), ("halt", "replay_allowed", True),
            ("halt", "next_sequence", 106), ("canonical_qualification", "current_canonical_API_executed", True),
            ("canonical_qualification", "SAVE_full_hash_count", 1),
            ("canonical_qualification", "Driver_full_read_count", 1),
            ("canonical_qualification", "SAVE_hash_reused_by_exact_identity", False))
        for name, key, bad in cases:
            f = CapPretransportFailureFixture()
            value = epoch_api.evidence(f.reader, dict(f.refs.items())[name]); value[key] = bad
            changed = f.changed(name, value)
            with self.subTest(name=name, key=key, bad=bad), self.assertRaises(ValueError):
                epoch_api.validate_cap_pretransport_failure_evidence_v2(changed, reader=f.reader)

    def test_previous_restore_prefix_and_single_new_row_are_mandatory(self) -> None:
        for kind in ("drop_prefix", "duplicate", "mutate_prefix", "action", "pid", "checkpoint", "float_index"):
            f = CapPretransportFailureFixture()
            tail = epoch_api.evidence(f.reader, f.refs.history_tail)
            history = copy.deepcopy(epoch_api.rows(tail["post_checkpoint_history"]))
            if kind == "drop_prefix": history = history[1:]
            elif kind == "duplicate": history.append(history[-1])
            elif kind == "mutate_prefix":
                first = object_row(history[0]); first["command"] = "advance-days"; history[0] = first
            else:
                last = object_row(history[-1])
                if kind == "action": last["command"] = "advance-days"
                elif kind == "float_index": last["index"] = 3.0
                else:
                    result = object_row(last["result"])
                    if kind == "pid": result["lifecycle"] = {"previous_pid": 41, "pid": 61}
                    else: result["checkpoint"] = {}
                    last["result"] = result
                history[-1] = last
            tail["post_checkpoint_history"] = epoch_api.json_value(history)
            changed = f.changed("history_tail", tail)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                epoch_api.validate_cap_pretransport_failure_evidence_v2(changed, reader=f.reader)

    def test_full_driver_validation_keeps_all_restore_rows_and_flags(self) -> None:
        f = CapPretransportFailureFixture(); checked = f.validated()
        payload: dict[str, object] = {"command_history": [{"prior": True}, *checked.history_rows],
            "managed_restore_transaction": None, "rollback_war_failure": None, "succession_expectation": None}
        epoch_api.validate_cap_pretransport_failure_driver_v2(checked, payload)
        for key in ("managed_restore_transaction", "rollback_war_failure", "succession_expectation"):
            bad = dict(payload); del bad[key]
            with self.assertRaises(ValueError):
                epoch_api.validate_cap_pretransport_failure_driver_v2(checked, bad)
        bad = dict(payload); bad["session_binding"] = None
        with self.assertRaises(ValueError): epoch_api.validate_cap_pretransport_failure_driver_v2(checked, bad)
        bad = dict(payload); bad["command_history"] = [{"prior": True}, checked.history_row, checked.history_row]
        with self.assertRaises(ValueError): epoch_api.validate_cap_pretransport_failure_driver_v2(checked, bad)

    def test_saved_business_source_references_cannot_be_replaced(self) -> None:
        f = CapPretransportFailureFixture()
        forged = replace(f.previous_basis, refs=replace(f.previous_basis.refs,
            seed=ExactRefV1("/foreign/seed.json", 1, "d"*64)))
        reference = f.reader.put("cap/forged-prior-basis.json", forged.to_wire())
        epoch = replace(f.epoch, refs=replace(f.refs, business_basis=reference))
        with self.assertRaisesRegex(ValueError, "prior immutable business references"):
            epoch_api.validate_cap_pretransport_failure_evidence_v2(epoch, reader=f.reader)



class CapPostresponseFailureFixture:
    """Three immutable epochs; no disk or Native transport is used."""
    def __init__(self) -> None:
        previous = CapPretransportFailureFixture()
        self.reader = r = previous.reader
        checked = previous.validated()
        er = r.put("v3-prior-epoch.json", previous.epoch.to_wire())
        self.previous_basis = old = epoch_api.build_cap_pretransport_failure_basis_v2(checked,
            epoch_ref=er, observed_at_utc="2026-10-21T07:00:00Z", sidecars=(), reader=r)
        old_ref = r.put("v3-prior-basis.json", old.to_wire())
        def put(name: str, value: object) -> ExactRefV1:
            return r.put("post/"+name, value)
        def source(name: str, value: str) -> ExactRefV1:
            path="/epoch/post/"+name; raw=value.encode(); r.raw[path]=raw
            return ExactRefV1(path,len(raw),hashlib.sha256(raw).hexdigest())
        def prior(name: str) -> dict[str,object]:
            return epoch_api.evidence(r,dict(previous.refs.items())[name])
        pid=83; birth=134370744784786913; seq=old.next_sequence; root="/epoch/post"
        launch=prior("launch"); launch.update(pid=pid,creation_filetime=birth,pipe="pipe-post")
        launch_ref=put("ROOT-ACTUAL-GAME-LAUNCH-C23.json",launch)
        semrequest={"sequence":seq,"tool":"ck3_take_semantic_snapshot_private_v1","arguments":{}}
        caprequest={"sequence":seq+1,"tool":"ck3_get_capabilities","arguments":{}}
        sr=put(f"p37-requests/{seq:04d}-1-result.json",semrequest)
        cr=put(f"p37-requests/{seq+1:04d}-1-result.json",caprequest)
        diag={"bridge_pid":pid,"pipe_name":"pipe-post","connection_generation":1,
            "hello":{"pid":pid,"connection_generation":1}}
        sem=prior("semantic_response"); sem["request"]=semrequest
        body=object_row(object_row(sem["result"])["structured_content"]); body["diagnostics"]=diag
        sem["result"]={"is_error":False,"result_type":"complete","structured_content":body}
        sem_ref=put(f"p37-responses/{seq:04d}-1-result.json",sem)
        capbody={"episode_run_id":old.frame.episode_run_id,"episode_character_id":old.frame.actor_character_id,
            "episode_identity_pending":False,"one_life_terminal":False,"diagnostics":diag,
            "native_session_control":{"driver_state_restored":True,"driver_state_restore_kind":"cold_checkpoint",
                "episode_binding_state":"active_resumed","driver_state_error":None,"cold_candidate_rejection":None}}
        cap_ref=put(f"p37-responses/{seq+1:04d}-1-result.json",{"request":caprequest,
            "result":{"is_error":False,"result_type":"complete","structured_content":capbody}})
        after=prior("semantic_after"); after.update(request=sr.path,response=sem_ref.path)
        after_ref=put(f"p37-queue/{seq:04d}-after-result.json",after)
        flat=prior("inflight"); flat.update(sequence=seq+1,request_file=cr.path)
        inflight=put(f"p37-queue/INFLIGHT-{seq+1:04d}.json",flat)
        before=put(f"p37-queue/{seq+1:04d}-before-action.json",flat)
        cold=source("root_p37c23_cold_resume.py",
            "class Cold:\n def check_after(self):\n  self.governance_result_state = copy.deepcopy(cold['governance']['state'])\n")
        owner=source("tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py",
            "def cold_inputs_v1():\n return (seed,_clone(inputs.governance),cp,ledger,epoch)\n")
        queue=source("root_p37c23_sdk_queue.py","async def call():\n return None\n")
        failure=prior("first_exception")
        failure.update(stage="request_dispatch",request_identity={"sequence":seq+1,"tool":"ck3_get_capabilities","command":None},
            exception_tree={"type":"KeyError","message":"'state'"},
            traceback=f'File "{Path(cold.path)}", line 3, in check_after\nKeyError: state')
        fail_ref=put("first-exception.json",failure)
        halt=prior("halt"); halt.update(error_type="KeyError",message="'state'",first_exception_receipt=fail_ref.path,
            original_request=caprequest,original_response=cap_ref.path,next_sequence=seq+2)
        halt_ref=put("HALT.json",halt)
        inv=prior("request_inventory"); inv.update(runtime_root=root,epoch_start_sequence=seq,
            request_refs=[sr.to_wire(),cr.to_wire()],response_refs=[sem_ref.to_wire(),cap_ref.to_wire()])
        inv_ref=put("inventory.json",inv); nxt=put("next.json",{"next_sequence":seq+2})
        sdk=prior("sdk_closed"); processes=epoch_api.rows(sdk["processes"])
        newprocesses=[]
        for item,newpid in zip(processes,(89,97)):
            process=object_row(item); process["pid"]=newpid; newprocesses.append(process)
        sdk["processes"]=newprocesses; sdk_ref=put("sdk-closed.json",sdk)
        supervisor=prior("supervisor_closed"); supervisor["sdk_actual_exit"]={k:v for k,v in sdk.items() if k!="launcher_exit_code"}
        supervisor["known_preload_phase"]={key:{"pid":pid,"creation_filetime":birth} for key in ("before","after")}
        cleanup=object_row(supervisor["owned_cleanup"]); cleanup["ck3_pid"]=pid; supervisor["owned_cleanup"]=cleanup
        supervisor_ref=put("supervisor-closed.json",supervisor)
        exit_ref=put("game-exit.json",{"machine_id":MACHINE,"pid":pid,"creation_filetime":birth,
            "kernel_signaled":True,"exit_code":1,"forced_owned_job_cleanup":True,"normal_wm_close_qualified":False,
            "sdk_actual_exit_status":"ACTUAL_BOTH_SDK_EXITS_OBSERVED"})
        driver_id=FileStatIdentityV1(29,"9007199254741017","1792563000000000033")
        driver_ref=ExactRefV1(old.refs.driver.path,29,"d"*64)
        history=[copy.deepcopy(row) for row in checked.history_rows]
        last=copy.deepcopy(history[-1]); last["index"]=checked.history_count+1
        result=object_row(last["result"]); result["lifecycle"]={"previous_pid":61,"pid":pid}; last["result"]=epoch_api.json_value(result)
        history.append(last)
        review=prior("driver_review"); driver=object_row(review["Driver"]); identity=object_row(driver["recorded_identity"])
        identity.update(bridge_pid=pid,pipe_name="pipe-post")
        driver.update(ref=driver_ref.to_wire(),identity=driver_id.to_wire(),command_history_count=4,recorded_identity=identity)
        raw=epoch_api.evidence(r,epoch_api.parse_ref(review["raw_observation"]))
        raw.update(Driver_ref=driver_ref.to_wire(),Driver_identity=driver_id.to_wire(),command_history_count=4,
            post_checkpoint_history=history,recorded_identity=identity)
        raw_ref=put("raw.json",raw)
        review.update(schema="xar.readonly-cap-postresponse-Driver-SAVE-review/v3",
            status="CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_AFTER_CAP_POSTCHECK_FAILURE",
            original_business_review=old.refs.driver_close.to_wire(),Driver=driver,
            raw_Driver_body_read_count=1,Driver_body_bytes_read=29,raw_observation=raw_ref.to_wire())
        review_ref=put("review.json",review)
        tail=prior("history_tail"); tail.update(schema="xar.readonly-cap-postresponse-history-tail/v3",
            driver_review=review_ref.to_wire(),driver_identity=driver_id.to_wire(),command_history_count=4,post_checkpoint_history=history)
        tail_ref=put("tail.json",tail)
        reuse=prior("canonical_qualification"); reuse.update(schema="xar.closed-cap-postresponse-save-identity-reuse/v3",
            previous_canonical_qualification=previous.refs.canonical_qualification.to_wire(),
            driver_review=review_ref.to_wire(),history_tail=tail_ref.to_wire(),Driver_identity=driver_id.to_wire(),
            Driver_full_read_count=1,Driver_full_read_bytes=29)
        reuse_ref=put("reuse.json",reuse)
        linked={key:epoch_api.parse_ref(value) for key,value in object_row(prior("closure_index")["refs"]).items()
            if key not in {"guard_source","capability_rejection"}}
        linked.update(launch=launch_ref,sdk_closed=sdk_ref,supervisor_closed=supervisor_ref,game_exit=exit_ref,
            semantic_response=sem_ref,semantic_after=after_ref,capability_response=cap_ref,first_exception=fail_ref,
            inflight=inflight,before_action=before,halt=halt_ref,request_inventory=inv_ref,next=nxt,
            driver_review=review_ref,history_tail=tail_ref,cold_resume_source=cold,owner_source=owner,queue_source=queue)
        index=prior("closure_index"); index.update(schema="xar.readonly-cap-postresponse-abort-closure/v3",
            status="CLOSED_CAP_POSTRESPONSE_LOCAL_FAILURE",original_basis_ref=old_ref.to_wire(),next_sequence=seq+2,
            failure_phase="CAP_POSTRESPONSE_LOCAL_CHECK_AFTER",capability_after_result_absent=True,
            normal_cold_bound_absent=True,Game_normal_wm_close_qualified=False,
            refs={key:ref.to_wire() for key,ref in linked.items()})
        index_ref=put("index.json",index)
        self.epoch=epoch_api.CapPostresponseFailureEpochV3(MACHINE,"2026-10-21T07:01:00Z",
            epoch_api.CapPostresponseFailureRefsV3(old_ref,review_ref,tail_ref,index_ref,launch_ref,sem_ref,after_ref,
                cap_ref,fail_ref,inflight,before,halt_ref,inv_ref,sdk_ref,supervisor_ref,exit_ref,nxt,reuse_ref),
            epoch_api.ReadonlyClosedDriverFlagsV1(None,None,None,False))
        self.refs=self.epoch.refs
        r.identities[driver_ref.path]=driver_id; r.read_paths.clear(); r.stat_paths.clear()
    def validated(self) -> epoch_api.ValidatedCapPostresponseFailureEpochV3:
        return epoch_api.validate_cap_postresponse_failure_evidence_v3(self.epoch,reader=self.reader)
    def changed(self,name:str,value:object) -> epoch_api.CapPostresponseFailureEpochV3:
        old_ref=dict(self.refs.items())[name]; raw=json_bytes(value); self.reader.raw[old_ref.path]=raw
        ref=ExactRefV1(old_ref.path,len(raw),hashlib.sha256(raw).hexdigest()); refs=replace(self.refs,**{name:ref})
        index=epoch_api.evidence(self.reader,self.refs.closure_index); linked=object_row(index["refs"])
        if name in linked:
            linked[name]=ref.to_wire(); index["refs"]=linked
            refs=replace(refs,closure_index=self.reader.put("post/changed-index.json",index))
        return replace(self.epoch,refs=refs)


class CapPostresponseFailureTests(unittest.TestCase):
    def test_three_epoch_public_builders_and_owner_consumers(self) -> None:
        from unittest.mock import patch
        from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
        f=CapPostresponseFailureFixture(); checked=f.validated()
        self.assertEqual((checked.previous_history_count,checked.history_count,checked.next_sequence),(3,4,109))
        er=f.reader.put("post/epoch.json",f.epoch.to_wire())
        basis=epoch_api.build_cap_postresponse_failure_basis_v3(checked,epoch_ref=er,
            observed_at_utc=f.epoch.observed_at_utc,sidecars=(),reader=f.reader)
        br=f.reader.put("post/basis.json",basis.to_wire())
        qual=epoch_api.build_cap_postresponse_failure_qualification_v3(checked,basis,basis_ref=br,
            reader=f.reader,observed_at_utc=f.epoch.observed_at_utc)
        qr=f.reader.put("post/qual.json",qual.to_wire())
        self.assertEqual(owner.parse_basis_qualification_v1(json.loads(json_bytes(qual.to_wire())),
            expected_machine_id=MACHINE),qual)
        self.assertEqual(epoch_api.parse_cap_postresponse_failure_epoch_v3(
            json.loads(json_bytes(f.epoch.to_wire())),expected_machine_id=MACHINE),f.epoch)
        for key in ("origin","frame","completed_cycles","checkpoint","progress","unknown_requests"):
            self.assertEqual(getattr(basis,key),getattr(f.previous_basis,key))
        closed=owner._closed_epoch(basis,f.reader)
        inputs=owner.CurrentSavedColdInputsV1(basis,{}, {}, {}, {},closed,br,qr)
        with patch.object(owner,"LocalBasisReaderV1",return_value=f.reader):
            proof=owner.validate_current_saved_prepared_sdk_closure_v1(f.refs.sdk_closed.to_wire(),inputs=inputs)
        self.assertEqual(proof["normal"],False)
        self.assertEqual((qual.driver_body_reads,qual.save_hash_reads,qual.root_driver_body_reads),(0,0,1))
        self.assertNotIn(checked.driver_ref.path,f.reader.read_paths)
        self.assertNotIn(checked.save_ref.path,f.reader.read_paths)
        f.reader.identities[checked.driver_ref.path]=replace(checked.driver_identity,file_id="123")
        self.assertEqual(f.validated(),checked)
        with self.assertRaises(ValueError):
            epoch_api.validate_cap_postresponse_failure_epoch_v3(f.epoch,reader=f.reader)

    def test_postresponse_and_pretransport_are_distinct(self) -> None:
        f=CapPostresponseFailureFixture()
        for parser in (epoch_api.parse_cap_pretransport_failure_epoch_v2,epoch_api.parse_readonly_cold_failure_epoch_v1):
            with self.assertRaises(ValueError): parser(f.epoch.to_wire(),expected_machine_id=MACHINE)
        for key in f.epoch.to_wire():
            for bad in (None,True,1.0):
                wire:dict[str,object]=dict(f.epoch.to_wire());wire[key]=bad
                with self.subTest(key=key,bad=bad),self.assertRaises(ValueError):
                    epoch_api.parse_cap_postresponse_failure_epoch_v3(wire,expected_machine_id=MACHINE)
            wire=dict(f.epoch.to_wire());del wire[key]
            with self.assertRaises(ValueError):
                epoch_api.parse_cap_postresponse_failure_epoch_v3(wire,expected_machine_id=MACHINE)
        for name,key,bad_receipt in (("first_exception","stage","sdk_call"),("capability_response","client_error","unknown"),
            ("halt","original_request",f.refs.capability_response.path),("halt","replay_allowed",True),
            ("history_tail","post_checkpoint_history",[]),("game_exit","kernel_signaled",False),
            ("canonical_qualification","current_canonical_API_executed",True)):
            f=CapPostresponseFailureFixture();row=epoch_api.evidence(f.reader,dict(f.refs.items())[name])
            if key=="client_error": row.pop("result")
            row[key]=bad_receipt
            with self.subTest(name=name,key=key),self.assertRaises(ValueError):
                epoch_api.validate_cap_postresponse_failure_evidence_v3(f.changed(name,row),reader=f.reader)



class ReadonlyPrefixUnknownFixture:
    """Synthetic receipts exercise real builders/owner; actual classifier sources are separately qualified."""
    def __init__(self,*,sidecar_payload:bytes|None=None)->None:
        import base64,zlib
        p=CapPostresponseFailureFixture();self.reader=r=p.reader
        prior=p.validated();pr=r.put("prefix-prior-epoch.json",p.epoch.to_wire())
        old_sidecars:tuple[ExactRefV1,...]=() if sidecar_payload is None else (r.put("previous-sidecar.json",{"pending":None}),)
        old=epoch_api.build_cap_postresponse_failure_basis_v3(prior,epoch_ref=pr,
            observed_at_utc="2026-10-21T08:00:00Z",sidecars=old_sidecars,reader=r)
        self.previous_basis=old;oldref=r.put("prefix-prior-basis.json",old.to_wire())
        root="/epoch/prefix";pid=127;birth=134370765451291729
        def put(name:str,value:object)->ExactRefV1:return r.put("prefix/"+name,value)
        def source(name:str,value:str)->ExactRefV1:
            raw=value.encode();path=root+"/"+name;r.raw[path]=raw
            return ExactRefV1(path,len(raw),hashlib.sha256(raw).hexdigest())
        launch=epoch_api.evidence(r,p.refs.launch)
        launch.update(pid=pid,creation_filetime=birth,pipe="pipe-prefix")
        launchref=put("ROOT-ACTUAL-GAME-LAUNCH-C23.json",launch)
        oldseed=epoch_api.evidence(r,old.refs.seed);cp=oldseed["actual_saved_checkpoint"]
        opening=old.frame.to_wire();semseq=old.next_sequence
        sem=epoch_api.evidence(r,p.refs.semantic_response)
        sb=object_row(object_row(sem["result"])["structured_content"])
        sb.update(episode_character_id=old.frame.actor_character_id,episode_run_id=old.frame.episode_run_id,
            paused=True,map_ready=True,date_raw=old.frame.date_raw)
        sem["request"]={"sequence":semseq,"tool":"ck3_take_semantic_snapshot_private_v1","arguments":{}}
        sem["result"]={"is_error":False,"result_type":"complete","structured_content":sb}
        semref=put(f"p37-responses/{semseq:04d}-1-result.json",sem)
        cap=epoch_api.evidence(r,p.refs.capability_response)
        cap["request"]={"sequence":semseq+1,"tool":"ck3_get_capabilities","arguments":{}}
        capref=put(f"p37-responses/{semseq+1:04d}-1-result.json",cap)
        bound=put("BOUND.json",{"schema":"xar.c23.normal-checkpoint-cold-bound/v1","machine_id":MACHINE,
            "opening_frame":opening,"completed_cycles":old.completed_cycles,"T0_date_raw":old.origin.start_date_raw,
            "checkpoint":cp,"new_ordinary_cycle_credit":0,"AUTO_or_MET_replayed":False,
            "semantic_response":semref.path})
        # Fixture classifier has a real executable module and source pin. The independent
        # actual-data qualification executes the original unmodified Native classifier.
        cls=source("classifier.py","def classify_auto_result_credit_v1(result,*,state,pending_focus,initial_frame,game_pid):\n return (result['fixture_observation'],state,pending_focus)\n")
        clspin=put("ROOT-P37C23-CLASSIFIER-PIN.json",{"source":cls.path,"sha256":cls.sha256,"machine_id":MACHINE})
        queue=source("root_p37c23_sdk_queue.py","def frame(value):\n return value\n")
        counts=copy.deepcopy(object_row(oldseed["counts"]));entries=[];requests=[]
        for seq,tool in ((semseq,"ck3_take_semantic_snapshot_private_v1"),(semseq+1,"ck3_get_capabilities")):
            requests.append(put(f"p37-requests/{seq:04d}-1-result.json",{"sequence":seq,"tool":tool,"arguments":{}}))
        control=semseq+2
        fullrequest={"sequence":control,"command":"full_loop","arguments":{"max_turns":30}}
        requests.append(put(f"p37-requests/{control:04d}-1-result.json",fullrequest))
        last_metrics=""
        for offset in (1,2):
            turn=old.completed_cycles+offset;seq=control+2*offset-1;step="query-war-results-window-v1"
            observation={"submitted_pending":False,"primitive_accepted":False,"business_success_inferred":False,
                "replay_allowed":False,"typed_nonmaterial_observation":True}
            arq={"sequence":seq,"tool":"ck3_auto_turn","arguments":{}}
            mrq={"sequence":seq+1,"tool":"root_current_runtime_metrics","arguments":{}}
            requests.extend((put(f"p37-requests/{seq:04d}-1-result.json",arq),put(f"p37-requests/{seq+1:04d}-1-result.json",mrq)))
            auto=put(f"p37-responses/{seq:04d}-1-result.json",{"request":arq,
                "result":{"is_error":False,"result_type":"complete","structured_content":{"selected_step":step,"fixture_observation":observation}}})
            metrics=put(f"p37-responses/{seq+1:04d}-1-result.json",{"request":mrq,
                "result":{"is_error":False,"result_type":"complete","structured_content":{
                    **opening,"paused":True,"map_ready":True,"actor_alive":True,"bridge_pid":pid}}})
            plan=put(f"plan-{seq}.json",{"source":"actual GameplayBridgeService.before_submit callback","game_pid":pid,
                "request":{"parent_sequence":seq},"result":{"structured_content":{"selected_step":step}}})
            aa=put(f"after-{seq}.json",{"response":auto.path,"tool":"ck3_auto_turn"})
            ma=put(f"after-{seq+1}.json",{"response":metrics.path,"tool":"root_current_runtime_metrics"})
            credit=put(f"credit-{seq}.json",{"source_response":auto.path,"observation":observation})
            counts["typed_nonmaterial_observation_turns"]=epoch_api.integer(counts.get("typed_nonmaterial_observation_turns",0))+1
            event=put(f"CUMULATIVE-TURN-{turn:06d}.json",{"observation":observation,"before":opening,"after":opening,
                "global_turn":turn,"auto_sequence":seq,"stage":"auto_verified","auto_response":auto.path,
                "after_metrics_response":metrics.path,"business_success_inferred":False,"date_delta_raw":0,
                "selected_step":step,"cumulative_observation_counts":copy.deepcopy(counts)})
            entries.append({name:ref.to_wire() for name,ref in {"event":event,"auto":auto,"metrics":metrics,
                "auto_plan":plan,"auto_after":aa,"metrics_after":ma,"ordinary_credit":credit}.items()}|{"readonly_save_skip":None})
            last_metrics=metrics.path
        unknown=control+5;count=old.completed_cycles+2
        request={"sequence":unknown,"tool":"ck3_auto_turn","arguments":{}}
        ur=put(f"p37-requests/{unknown:04d}-1-result.json",request);requests.append(ur)
        response=put(f"p37-responses/{unknown:04d}-1-result.json",{"request":request,"client_error":"JSON integer loses precision","replay_allowed":False})
        pending={"stage":"auto_unsettled","global_turn":count+1,"before":opening,"before_metrics_response":last_metrics,"auto_sequence":unknown}
        state=copy.deepcopy(oldseed);state.update(completed_cycles=count,before=opening,before_metrics_response=last_metrics,
            counts=counts,pending_cycle=pending,checkpoint_dirty_since_save=False)
        for key in ("pending_checkpoint","terminal","pending_natural_succession","pending_unsafe_route_halt"):state[key]=None
        state_ref=put("raw-state.json",state);self.raw_state=copy.deepcopy(state)
        oldgov=epoch_api.evidence(r,old.refs.governance)
        gov=put("raw-gov.json",{"schema":"g2.queue.governance-sidecar/v1","completed_cycles":count,
            "pending_cycle":pending,"state":oldgov["governance_result_state"],"pending_focus":oldgov["pending_focus"]})
        prefix=put("prefix.json",{"schema":"xar.readonly-settled-prefix-evidence/v1","machine_id":MACHINE,
            "business_basis":oldref.to_wire(),"cold_bound":bound.to_wire(),"semantic_response":semref.to_wire(),
            "capability_response":capref.to_wire(),"classifier_pin":clspin.to_wire(),"classifier_source":cls.to_wire(),"entries":entries})
        inf=put("FULL-INFLIGHT.json",{"request":fullrequest,"control_only":True,"original_action_replay_allowed":False})
        unknown_inf=put("unknown-INFLIGHT.json",{"sequence":unknown,"tool":"ck3_auto_turn","arguments":{},"request_file":ur.path,"replay_allowed":False})
        fail=put("exception.json",{"stage":"sdk_call","replay_allowed":False,"request_identity":{
            "sequence":unknown,"tool":"ck3_auto_turn","command":None},"traceback_truncated":False,"locals_captured":False})
        halt=put("HALT.json",{"original_request":request,"original_response":response.path,"replay_allowed":False,
            "sdk_kept_alive_for_original_collection":True,"first_exception_receipt":fail.path,"next_sequence":unknown+1})
        full=put("failed-full.json",{"request":fullrequest,"client_error":"unknown","replay_allowed":False})
        inv=put("inventory.json",{"machine_id":MACHINE,"all_owned_writers_closed":True,"next_sequence":unknown+1,
            "unknown_sequence":unknown,"original_unknown_replayed":False,"request_files":[x.to_wire() for x in requests]})
        nxt=put("next.json",{"next_sequence":unknown+1})
        sdk=epoch_api.evidence(r,p.refs.sdk_closed);ps=[]
        for value,newpid in zip(epoch_api.rows(sdk["processes"]),(131,137)):
            item=object_row(value);item["pid"]=newpid;ps.append(item)
        sdk["processes"]=ps;sdkref=put("sdkclosed.json",sdk)
        sup=epoch_api.evidence(r,p.refs.supervisor_closed)
        sup["sdk_actual_exit"]={k:v for k,v in sdk.items() if k!="launcher_exit_code"}
        cleanup=object_row(sup["owned_cleanup"]);cleanup["ck3_pid"]=pid;sup["owned_cleanup"]=cleanup
        supref=put("supervisorclosed.json",sup)
        gx=epoch_api.evidence(r,p.refs.game_exit);gx.update(pid=pid,creation_filetime=birth);gxref=put("gameexit.json",gx)
        di=FileStatIdentityV1(31,"9007199254741029","1792606189746283600")
        dr=ExactRefV1(old.refs.driver.path,31,"e"*64)
        history=[copy.deepcopy(x) for x in prior.history_rows];restore=copy.deepcopy(history[-1])
        restore["index"]=prior.history_count+1;res=object_row(restore["result"])
        res["lifecycle"]={"previous_pid":prior.old_game.pid,"pid":pid};restore["result"]=epoch_api.json_value(res)
        history.append(restore);history.append({"index":prior.history_count+2,"command":"query-campaign-root-context-v1","ok":True,
            "result":{"step":"query-campaign-root-context-v1","accepted":True,"date_raw":old.frame.date_raw,"native_uint64":18446744073709551615}})
        native_raw=json.dumps(history,sort_keys=True,separators=(",",":")).encode()
        opaque=put("opaque.json",{"schema":"xar.raw-closed-driver-history-opaque/v1","machine_id":MACHINE,
            "Driver_ref":dr.to_wire(),"Driver_identity":di.to_wire(),"encoding":"zlib+base64",
            "decoded_bytes":len(native_raw),"decoded_sha256":hashlib.sha256(native_raw).hexdigest(),"row_count":len(history),
            "checkpoint_history_index":object_row(cp)["history_index"],"command_history_count":prior.history_count+2,
            "payload":base64.b64encode(zlib.compress(native_raw)).decode()})
        expectation={"schema":"xar.ck3.succession-expectation/v1","status":"available",
            "binding":{**opening,"episode_character_id":old.frame.actor_character_id},"expectation_state":"successor_expected",
            "predecessor_character_id":old.frame.actor_character_id,"expected_successor_character_id":143,
            "title_expectations":[{"title":{"title_id":2,"tier_raw":2,"tier_key":"county"},"first_heir_character_id":143,"primary":True}],"risk_state":"single_successor","unavailable_reason":None}
        # Preserve exactly the SDK expectation wire, including its nullable unavailable_reason.
        expectation["binding"]={key:value for key,value in object_row(expectation["binding"]).items() if key!="actor_character_id"}
        flags:dict[str,object]={"managed_restore_transaction":None,"rollback_war_failure":None,"succession_expectation":expectation,
            "rollback_war_failures":[],"session_binding_present":False}
        oldreview=epoch_api.evidence(r,p.refs.driver_review);driver=object_row(oldreview["Driver"])
        identity=object_row(driver["recorded_identity"]);identity.update(bridge_pid=pid,pipe_name="pipe-prefix")
        driver.update(ref=dr.to_wire(),identity=di.to_wire(),command_history_count=prior.history_count+2,
            recorded_identity=identity,session_binding_present=False,payload_flags={k:v for k,v in flags.items() if k!="session_binding_present"})
        raw=put("raw.json",{"schema":"xar.raw-closed-driver-observation/v2","machine_id":MACHINE,
            "Driver_ref":dr.to_wire(),"Driver_identity":di.to_wire(),"SAVE_identity":old.save_identity.to_wire(),
            "command_history_count":prior.history_count+2,"last_checkpoint":cp,"recorded_identity":identity,
            "campaign_goal":old.campaign_goal_anchor,"driver_payload_flags":driver["payload_flags"],
            "post_checkpoint_history_opaque":opaque.to_wire(),"session_binding_present":False,"session_binding_value":None,"payload_top_keys":[]})
        review=put("review.json",{"schema":"xar.readonly-prefix-unknown-driver-save-review/v1",
            "status":"CLOSED_DRIVER_SAME_SAVED_CHECKPOINT_WITH_UNKNOWN_REQUEST","machine_id":MACHINE,
            "Driver":driver,"SAVE":oldreview["SAVE"],"post_checkpoint_history_opaque":opaque.to_wire(),
            "raw_observation":raw.to_wire(),"raw_Driver_body_read_count":1,"Driver_body_bytes_read":31,"SAVE_full_hash_count":0})
        reuse=epoch_api.evidence(r,p.refs.canonical_qualification)
        reuse.update(schema="xar.closed-readonly-prefix-save-identity-reuse/v1",previous_canonical_qualification=p.refs.canonical_qualification.to_wire(),
            driver_review=review.to_wire(),history_tail=opaque.to_wire(),Driver_identity=di.to_wire(),
            Driver_full_read_count=1,Driver_full_read_bytes=31)
        reuse_ref=put("reuse.json",reuse)
        linked={name:ref.to_wire() for name,ref in {"raw_state":state_ref,"raw_governance":gov,"unknown_request":ur,
            "unknown_response":response,"first_exception":fail,"inflight":inf,"halt":halt,"failed_full_response":full,
            "request_inventory":inv,"driver_review":review,"history_tail":opaque,"launch":launchref,"sdk_closed":sdkref,
            "supervisor_closed":supref,"game_exit":gxref,"next":nxt,"canonical_qualification":reuse_ref,"queue_source":queue}.items()}
        extra=put("closed-extra.json",{});linked.update({k:extra.to_wire() for k in (
            "screen_release","recording_shutdown","independent_recording_closed","sdk_pair")})
        tasks={}
        for role in ("supervisor","display","record02","feeder"):
            spec=put(role+"-SPEC.json",{"machine_id":MACHINE,"nonce":role})
            closed=put(role+"-CLOSED.json",{"machine_id":MACHINE,"nonce":role,"child_exit_code":1})
            unreg=put(role+"-UNREGISTER.json",{"returncode":0,"stdout":json.dumps({"machine_id":MACHINE,"actual":{"absent_after":True}})})
            tasks[role]={"spec":spec.to_wire(),"closed":closed.to_wire(),"unregistered":unreg.to_wire(),"child_exit_code":1}
        index=put("index.json",{"schema":"xar.readonly-prefix-unknown-abort-closure/v1",
            "status":"CLOSED_READONLY_SETTLED_PREFIX_WITH_UNKNOWN","machine_id":MACHINE,"original_basis_ref":oldref.to_wire(),
            "original_whole_wall_origin":old.origin.original_wall_origin_utc,"next_sequence":unknown+1,
            "last_saved_checkpoint_baseline_cycles":old.completed_cycles,"business_completed_cycles":count,
            "business_date_raw":old.frame.date_raw,"pending_unknown_cycle":pending,"unknown_side_effects_inferred":False,
            "failed_FULL_claimed_successful":False,"original_requests_replayed":False,"all_owned_Tasks_actual_absent":True,
            "Game_exit_code":1,"Game_forced":True,"Game_Job_active_final":0,"owned_Task_count":4,"tasks":tasks,"refs":linked,
            "new_ordinary_cycle_credit":0,"new_game_day_credit":0,"new_checkpoint_credit":0,"new_game_days":0})
        values={name:epoch_api.parse_ref(value) for name,value in linked.items()}
        values.update(business_basis=oldref,prefix=prefix,closure_index=index,unknown_inflight=unknown_inf)
        observations:tuple[epoch_api.ReadonlyUnknownSidecarV1,...]=()
        if sidecar_payload is not None:
            path=root+"/current-sidecar.json";r.raw[path]=sidecar_payload
            current=ExactRefV1(path,len(sidecar_payload),hashlib.sha256(sidecar_payload).hexdigest())
            observations=(epoch_api.ReadonlyUnknownSidecarV1(old_sidecars[0],current,"/live/formal-sidecar.json"),)
        self.epoch=epoch_api.ReadonlyPrefixUnknownEpochV1(MACHINE,"2026-10-21T08:01:00Z",
            epoch_api.ReadonlyPrefixUnknownRefsV1(*(values[k] for k in epoch_api._PREFIX_REF_NAMES)),
            epoch_api.parse_readonly_prefix_driver_flags_v1(flags),observations)
        r.identities[dr.path]=di;r.read_paths.clear();r.stat_paths.clear()
    def validated(self)->epoch_api.ValidatedReadonlyPrefixUnknownEpochV1:
        return epoch_api.validate_readonly_prefix_unknown_epoch_v1(self.epoch,reader=self.reader)
    def build(self)->tuple[CurrentSavedBasisV1,ExactRefV1,epoch_api.ReadonlyPrefixUnknownQualificationV1]:
        checked=self.validated();r=self.reader
        er=r.put("prefix-epoch.json",self.epoch.to_wire())
        projections=epoch_api.build_readonly_prefix_unknown_projections_v1(checked,reader=r)
        sr=r.put("prefix-seed.json",projections.seed);gr=r.put("prefix-governance.json",projections.governance)
        basis=epoch_api.build_readonly_prefix_unknown_basis_v1(checked,epoch_ref=er,seed_ref=sr,governance_ref=gr,
            observed_at_utc=self.epoch.observed_at_utc,sidecars=tuple(x.current_snapshot for x in self.epoch.sidecar_observations),reader=r)
        br=r.put("prefix-basis.json",basis.to_wire())
        q=epoch_api.build_readonly_prefix_unknown_qualification_v1(checked,basis,basis_ref=br,reader=r,
            observed_at_utc=self.epoch.observed_at_utc)
        return basis,br,q

class ReadonlyPrefixUnknownTests(unittest.TestCase):
    def test_real_builders_to_all_owner_consumers_preserve_unknown(self)->None:
        from unittest.mock import patch
        from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
        f=ReadonlyPrefixUnknownFixture();basis,br,q=f.build();r=f.reader
        self.assertEqual(basis.completed_cycles,f.previous_basis.completed_cycles+2)
        self.assertEqual(basis.frame.date_raw,f.previous_basis.frame.date_raw)
        self.assertEqual([x.sequence for x in basis.unknown_requests],
            [*(x.sequence for x in f.previous_basis.unknown_requests),basis.next_sequence-1])
        self.assertEqual(epoch_api.evidence(r,f.epoch.refs.raw_state),f.raw_state)
        self.assertIsNotNone(f.raw_state["pending_cycle"])
        self.assertIsNotNone(f.epoch.driver_payload_flags.succession_expectation)
        qr=r.put("prefix-qualification.json",q.to_wire())
        parsed=owner.parse_basis_qualification_v1(json.loads(json_bytes(q.to_wire())),expected_machine_id=MACHINE)
        self.assertIsInstance(parsed,epoch_api.ReadonlyPrefixUnknownQualificationV1)
        inputs=owner.validate_current_saved_cold_inputs_v1(basis,basis_ref=br,validation_ref=qr,reader=r)
        with patch.object(owner,"LocalBasisReaderV1",return_value=r):
            out=owner.validate_current_saved_prepared_sdk_closure_v1(f.epoch.refs.sdk_closed.to_wire(),inputs=inputs)
        self.assertEqual(out["normal"],False)
        r.identities[basis.refs.driver.path]=FileStatIdentityV1(basis.driver_identity.bytes,"9007199254741999",basis.driver_identity.mtime_ns)
        owner._closed_epoch(basis,r) # Historical warm evidence does not assert a mutable live Driver identity.
        with self.assertRaises(ValueError):f.validated()
        self.assertNotIn(basis.refs.driver.path,r.read_paths);self.assertNotIn(basis.refs.save.path,r.read_paths)
    def test_schema_types_unknown_and_opaque_integrity(self)->None:
        f=ReadonlyPrefixUnknownFixture()
        for field,bad in (("new_ordinary_cycle_credit",True),("new_game_day_credit",1.0),
            ("original_unknown_replayed",True),("unknown_side_effects_inferred",True),("schema",epoch_api.CAP_POSTRESPONSE_FAILURE_EPOCH_SCHEMA)):
            wire=f.epoch.to_wire();wire[field]=bad
            with self.subTest(field=field),self.assertRaises(ValueError):
                epoch_api.parse_readonly_prefix_unknown_epoch_v1(wire,expected_machine_id=MACHINE)
        opaque=epoch_api.evidence(f.reader,f.epoch.refs.history_tail)
        decoded=epoch_api.decode_readonly_prefix_history_v1(opaque)
        self.assertEqual(object_row(decoded[-1]["result"])["native_uint64"],18446744073709551615)
        for key,bad in (("payload",str(opaque["payload"])+"AAAA"),("decoded_sha256","f"*64),("decoded_bytes",True),("row_count",1.0)):
            row=copy.deepcopy(opaque);row[key]=bad
            with self.subTest(key=key),self.assertRaises((ValueError,TypeError)):
                epoch_api.decode_readonly_prefix_history_v1(row)
        invalid_epoch=replace(f.epoch,driver_payload_flags=replace(f.epoch.driver_payload_flags,managed_restore_transaction=None))
        wire=invalid_epoch.to_wire()
        wire["driver_payload_flags"]=epoch_api.json_object({**object_row(wire["driver_payload_flags"]),"rollback_war_failure":{}})
        with self.assertRaises(ValueError):epoch_api.parse_readonly_prefix_unknown_epoch_v1(wire,expected_machine_id=MACHINE)

    def test_raw_uint64_sidecar_survives_public_builder(self)->None:
        raw=b' {\n "pending":null,"source_creation_filetime":134370765451291729}\n'
        f=ReadonlyPrefixUnknownFixture(sidecar_payload=raw);obs=f.epoch.sidecar_observations[0]
        self.assertEqual(f.reader.raw[obs.current_snapshot.path],raw)
        basis,_,_=f.build()
        self.assertIn(obs.current_snapshot,basis.sidecars)
        self.assertEqual(f.reader.raw[obs.current_snapshot.path],raw)
        self.assertEqual(epoch_api.decode_current_saved_basis_v1(
            epoch_api.encode_current_saved_basis_v1(basis),expected_machine_id=MACHINE),basis)
        self.assertEqual(obs.to_wire()["attribution"],"UNKNOWN_REQUEST_EFFECT_NOT_INFERRED")
        with self.assertRaisesRegex(ValueError,"JSON integer loses precision"):
            epoch_api.json_object(json.loads(raw))

if __name__ == "__main__":
    unittest.main()


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


if __name__ == "__main__":
    unittest.main()


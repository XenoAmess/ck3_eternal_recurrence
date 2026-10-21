"""Typed producer/JSON/consumer cold boundary and finite SDK persistence fixtures."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from typing import Callable

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    ExactRefV1, JsonObject, JsonValue, SavedFrameV1, encode_current_saved_basis_v1,
    parse_json, record, json_object, json_value, qualify_current_saved_basis_v1,
)
from tools.g2_saved_campaign import test_current_saved_basis_v1 as basis_fixture
from tools.g2_saved_campaign.test_current_saved_basis_v1 import (
    DiskReader, MACHINE, file_ref, pure_basis,
)
from tools.g2_saved_campaign import prepare_current_saved_campaign_cold_v1 as producer
from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign import current_saved_campaign_feeder_v1 as feeder
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver

PIPE = r"\\.\pipe\synthetic-current-saved"
ROOT = "D:\\synthetic-current-saved\\new"
OLD = "D:\\synthetic-current-saved\\old"
LIFECYCLE: JsonObject = {"schema": "xar.ck3.succession-lifecycle-binding/v1",
    "lifecycle": "ordinary_campaign_succession", "xar_enabled": "xar_off",
    "pact_contract": "absent_by_fresh_campaign_xar_off_contract",
    "source": "synthetic_fixture", "environment_sha256": "b" * 64}


def wire(value: object) -> JsonObject:
    return json_object(parse_json(producer.encode_v1(value)))


def ref(name: str) -> ExactRefV1:
    return ExactRefV1("D:\\synthetic-current-saved\\" + name, 1, "a" * 64)


def plan() -> producer.ColdPlanV1:
    names = tuple(sorted(producer.CANONICAL_NAMES))
    source_rows = tuple(producer.SourceRowV1(ref(name),
        "tools/g2_saved_campaign/" + name) for name in sorted(producer.GENERIC_SOURCE_NAMES))
    source = next(row.source_ref for row in source_rows
        if row.relative_path.endswith("/prepare_current_saved_campaign_cold_v1.py"))
    return producer.ColdPlanV1(
        MACHINE, "2026-10-21T06:00:00Z", "2026-10-21T07:30:00Z", ROOT, OLD,
        ref("material.json"), ref("basis.json"), ref("qualification.json"), source,
        source_rows, names, names + tuple(row.relative_path for row in source_rows),
        (".",), ref("full.json"), ref("steam.json"), ref("screen.json").path,
        ref("spec.json").path, "1" * 32, "2" * 32, "3" * 32,
        business_source_generation=31, sdk_base_ref=ref("sdk-base.json"),
        sdk_anchor_ref=ref("sdk-anchor.json"))


def feeder_admission() -> feeder.CurrentSavedFeederAdmissionV1:
    return feeder.CurrentSavedFeederAdmissionV1(
        MACHINE, ref("basis.json"), ref("cold-admission.json"), ref("bound.json"),
        ref("game.json"), ref("map.json"), ref("first-frame.json"), ref("active.json"),
        ref("feeder.py"), ref("loop.py"), ref("owner.py"), ref("task.json"), ref("budget.json"),
        "4" * 32, 105, "2026-10-21T07:30:00Z",
        "D:\\synthetic-current-saved\\continue", "D:\\synthetic-current-saved\\stop")


def seed() -> JsonObject:
    basis = pure_basis()
    cp: JsonObject = {"status": "saved", "name": "xar_checkpoint.ck3",
        "path": basis.checkpoint["path"], "size": basis.checkpoint["size"],
        "sha256": basis.checkpoint["sha256"], "date_raw": basis.frame.date_raw,
        "history_index": basis.checkpoint["history_index"],
        "episode_character_id": basis.frame.actor_character_id,
        "episode_run_id": basis.frame.episode_run_id, "succession_lifecycle": None}
    return {"schema": "g2.queue.cumulative-loop/v1", "completed_cycles": 20,
        "start_date_raw": 100, "before": basis.frame.to_wire(), "pending_cycle": None,
        "pending_checkpoint": None, "terminal": None, "counts": {
            "checkpoint_saved": 3, "date_advanced_turns": 7, "unknown": 0},
        "actual_saved_checkpoint": cp, "campaign_goal_anchor": basis.campaign_goal_anchor,
        "checkpoint_dirty_since_save": True, "checkpoint_due_after_readonly_chain": True}


class TypedColdContractTests(unittest.TestCase):
    def test_plan_producer_json_consumer_roundtrip(self) -> None:
        item = plan()
        parsed = producer.parse_plan_v1(wire(item.to_wire()))
        self.assertEqual(parsed, item)
        self.assertIsInstance(parsed.source_rows, tuple)
        self.assertEqual(len(parsed.canonical_entry_paths), 8)

    def test_plan_rejects_missing_null_alias_and_wrong_types(self) -> None:
        item = plan().to_wire()
        for key, value in (("canonical_entry_paths", None), ("source_rows", []),
                ("review_at_utc", "2026-10-21T05:59:59Z"),
                ("display_nonce", "2" * 32), ("runtime_root", OLD),
                ("import_roots", ["../escape"]), ("business_source_generation", True),
                ("business_source_generation", 32.0), ("sdk_base_ref", None)):
            bad = copy.deepcopy(item)
            bad[key] = json_value(value)
            with self.subTest(key=key), self.assertRaises(ValueError):
                producer.parse_plan_v1(wire(bad))
        bad = copy.deepcopy(item)
        del bad["basis_ref"]
        with self.assertRaises(ValueError):
            producer.parse_plan_v1(wire(bad))
        bad = copy.deepcopy(item)
        bad["saved10480_alias"] = ref("bad").to_wire()
        with self.assertRaises(ValueError):
            producer.parse_plan_v1(wire(bad))

    def test_quote_serialization_count_guard_and_exact_allocation(self) -> None:
        item = plan()
        outputs = tuple(producer.OutputRowV1(producer.child_v1(ROOT, name), name,
            1, "a" * 64, "create-only", None) for name in item.closure_entry_paths)
        allocated = len(outputs) * 4096
        quote = producer.ColdQuoteV1(MACHINE, item.observed_at_utc, ref("plan.json"),
            item.basis_ref, item.validation_ref, item.producer_ref, ROOT, outputs,
            item.canonical_entry_paths, item.closure_entry_paths, item.import_roots,
            8, len(outputs), allocated, allocated + 1 + 131072)
        self.assertEqual(producer.parse_quote_v1(wire(quote.to_wire())), quote)
        for key, value in (("canonical_entry_limit", True), ("canonical_entry_limit", 8.0),
                ("canonical_entry_limit", 9), ("allocation_upper", allocated + 4096),
                ("ordinary_cycle_credit", True), ("original_actions_replayed", True)):
            bad = quote.to_wire()
            bad[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                producer.parse_quote_v1(wire(bad))

    def test_feeder_admission_roundtrip_and_no_progress_alias(self) -> None:
        item = feeder_admission()
        raw = feeder.encode_current_saved_feeder_admission_v1(item)
        self.assertEqual(feeder.decode_current_saved_feeder_admission_v1(
            raw, expected_machine_id=MACHINE), item)
        for key, value in (("first_control_sequence", True), ("first_control_sequence", 105.0),
                ("game_day_credit", True), ("ordinary_cycle_credit", 1),
                ("original_actions_replayed", True), ("window_origin_reset", True),
                ("cold_bound_ref", None)):
            bad = item.to_wire()
            bad[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                feeder.parse_current_saved_feeder_admission_v1(wire(bad),
                    expected_machine_id=MACHINE)
        bad = item.to_wire()
        del bad["basis_ref"]
        with self.assertRaises(ValueError):
            feeder.parse_current_saved_feeder_admission_v1(wire(bad), expected_machine_id=MACHINE)

    def test_maintenance_projection_preserves_ledger_and_is_idempotent(self) -> None:
        original = seed()
        saved = copy.deepcopy(original)
        save_response = {"result": {"is_error": False, "result_type": "complete",
            "structured_content": {"checkpoint": original["actual_saved_checkpoint"]}},
            "request": {"tool": "ck3_save_checkpoint", "arguments": {}}}
        projected = owner.project_completed_maintenance_save_v1(wire(original),
            wire(save_response), semantic_response=ref("sem.json"), save_response=ref("save.json"))
        self.assertEqual(original, saved)
        self.assertEqual(record(projected["counts"])["checkpoint_saved"], 4)
        self.assertEqual(record(projected["counts"])["date_advanced_turns"], 7)
        self.assertEqual(projected["completed_cycles"], 20)
        self.assertEqual(projected["before"], original["before"])
        self.assertEqual(owner.project_completed_maintenance_save_v1(wire(projected),
            wire(save_response), semantic_response=ref("sem.json"), save_response=ref("save.json")),
            projected)
        bad = copy.deepcopy(original)
        bad["counts"] = {"checkpoint_saved": True}
        with self.assertRaises(ValueError):
            owner.project_completed_maintenance_save_v1(wire(bad), wire(save_response),
                semantic_response=ref("sem.json"), save_response=ref("save.json"))

    def test_prelaunch_preserves_64_bit_ids_and_unknown_without_credit(self) -> None:
        basis = pure_basis()
        pre = owner.build_current_saved_prelaunch_v1(basis, basis_ref=ref("basis.json"),
            validation_ref=ref("qualification.json"), environment_sha256="b" * 64,
            pipe_name="synthetic-pipe")
        parsed = wire(pre)
        self.assertEqual(parsed["completed_cycles"], 20)
        self.assertEqual(parsed["ordinary_cycle_credit"], 0)
        self.assertEqual(parsed["game_day_credit"], 0)
        self.assertIs(parsed["original_actions_replayed"], False)
        self.assertEqual(parsed["power_loss_durability"], "not_asserted")
        raw = encode_current_saved_basis_v1(basis)
        self.assertIn(b'"9007199254740993"', raw)
        self.assertEqual(basis.unknown_requests[0].sequence, 7)

    def test_game_identity_canonical_decimal_and_legacy_are_distinct(self) -> None:
        item = {"pid": 123, "creation_filetime": "134370341656846441",
            "creation_date": "2026-10-21T06:00:00Z"}
        self.assertEqual(owner.parse_current_game_identity_v1(wire(item)).to_wire(), item)
        for bad_value in (True, 134370341656846441, 134370341656846440.0, "0134370341656846441"):
            bad = {**item, "creation_filetime": bad_value}
            with self.subTest(value=bad_value), self.assertRaises(ValueError):
                owner.parse_current_game_identity_v1(wire(bad))
        legacy = {**item, "creation_filetime": 134370341656846441}
        self.assertEqual(owner.parse_current_game_identity_v1(legacy, legacy_python=True).to_wire(),
            item)


class NoTransport:
    """The real SDK constructor is used with an offline transport test boundary."""
    pipe_name = PIPE

    def start(self, on_frame: Callable[[dict[str, object]], None],
            on_disconnect: Callable[[], None]) -> None:
        pass

    def send(self, frame: dict[str, object]) -> None:
        raise AssertionError("fixture must never issue a native command")

    def close(self) -> None:
        pass


class OwnedDriver(NativeHeadlessGameplayDriver):
    fixture_path: Path

    def _native_driver_state_path(self) -> Path:
        return self.fixture_path

class WarmFixtureReader(DiskReader):
    def __init__(self, identities: dict[int, JsonObject]) -> None:
        self.identities = identities

    def process_identity(self, pid: int) -> JsonObject:
        return self.identities[pid]

    def read_driver_header(self, path: str, limit: int) -> bytes:
        with Path(path).open("rb") as stream:
            return stream.read(limit)


def save_raw(fixture: type[basis_fixture.CurrentSavedBasisTests],
        name: str, raw: bytes) -> ExactRefV1:
    path = fixture.root / name
    if len(raw) > 65536 or path.parent.resolve() != fixture.root:
        raise RuntimeError("bounded owned raw fixture")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    fixture.measure()
    return file_ref(path)


class CurrentSavedSdkPersistenceTests(unittest.TestCase):
    fixture: type[basis_fixture.CurrentSavedBasisTests]

    @classmethod
    def setUpClass(cls) -> None:
        def ordinary(value: object) -> JsonValue:
            if isinstance(value, dict):
                return {key: PIPE if key == "pipe_name" else dict(LIFECYCLE)
                    if key == "succession_lifecycle" and item is None else ordinary(item)
                    for key, item in record(value).items()}
            if isinstance(value, list):
                return [ordinary(item) for item in value]
            return json_value(value)
        class OwnedFixture(basis_fixture.CurrentSavedBasisTests):
            @classmethod
            def write(cls, name: str, value: object) -> ExactRefV1:
                converted = ordinary(value)
                if name == "driver.json":
                    converted = json_object(converted)
                    checkpoint = record(converted["last_checkpoint"])
                    converted["succession_lifecycle"] = json_value(checkpoint["succession_lifecycle"])
                return super().write(name, converted)
        cls.fixture = OwnedFixture
        cls.fixture.setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fixture.tearDownClass()

    def test_sdk_persist_closed_rejection_warm_binding_and_wrong_generations(self) -> None:
        fixture = self.fixture
        if not fixture.fixture_enabled:
            self.skipTest("explicit owned fixture, machine and finite review required")
        driver = OwnedDriver(PIPE, endpoint=NoTransport(),
            state_dir=fixture.root, save_dir=fixture.root / "save games")
        driver.fixture_path = Path(fixture.inputs.refs.driver.path)
        driver._session_bridge_pid = 999
        driver._episode_character_id = fixture.basis.frame.actor_character_id
        driver._episode_run_id = fixture.basis.frame.episode_run_id
        saved_seed = record(parse_json(fixture.reader.read(fixture.inputs.refs.seed, 65536)))
        driver._last_checkpoint = record(saved_seed["actual_saved_checkpoint"])
        driver._campaign_goal = dict(fixture.basis.campaign_goal_anchor)
        driver._succession_lifecycle = record(driver._last_checkpoint["succession_lifecycle"])
        driver._command_history = [{"index": 1, "command": "save-checkpoint", "ok": True,
            "result": {"checkpoint": driver._last_checkpoint}}]
        validated = qualify_current_saved_basis_v1(fixture.inputs,
            reader=fixture.reader, checkpoint_validator=fixture.validator)
        basis = validated.basis
        basis_ref = save_raw(fixture, "warm-basis.json", encode_current_saved_basis_v1(basis))
        qualification = owner.build_basis_qualification_v1(validated, basis_ref=basis_ref,
            reader=fixture.reader, observed_at_utc="2026-10-21T06:00:00Z")
        validation_ref = fixture.write("warm-qualification.json", qualification.to_wire())
        old_game = owner.CurrentGameIdentityV1(111, "134370000000000000", "old-fixture")
        closed = owner.ClosedEpochV1(basis.refs.closure, old_game, basis.next_sequence, (),
            basis.observed_at_utc, PIPE)
        inputs = owner.CurrentSavedColdInputsV1(basis, json_object(saved_seed),
            {"completed_cycles": 20, "pending_cycle": None}, json_object(driver._last_checkpoint),
            {"machine_id": MACHINE, "last_settled_cycles": 18}, closed, basis_ref, validation_ref)
        pre = owner.build_current_saved_prelaunch_v1(basis, basis_ref=basis_ref,
            validation_ref=validation_ref, environment_sha256="b" * 64, pipe_name=PIPE)
        pre_ref = fixture.write("admission-prelaunch.json", pre)
        admission: JsonObject = {"machine_id": MACHINE, "basis_ref": basis_ref.to_wire(),
            "validation_ref": validation_ref.to_wire(), "next_sequence": basis.next_sequence,
            "cold_prelaunch": pre_ref.to_wire()}
        def closed_inputs(*, runtime_root: Path, expected_machine_id: str
                ) -> owner.CurrentSavedColdInputsV1:
            if runtime_root != fixture.root or expected_machine_id != MACHINE:
                raise ValueError("fixture exact loader boundary")
            return inputs
        # The closed-file loader has separate real graph coverage; isolate this
        # admission field while exercising the public production consumer.
        with patch.object(owner, "load_current_saved_inputs_v1", new=closed_inputs):
            self.assertEqual(owner.cold_inputs_v1(admission, runtime_root=fixture.root,
                expected_machine_id=MACHINE)[2], inputs.checkpoint)
            for bad_sequence in (None, True, float(basis.next_sequence), basis.next_sequence - 1):
                bad_admission = {**admission, "next_sequence": bad_sequence}
                with self.subTest(sequence=bad_sequence), self.assertRaises(ValueError):
                    owner.cold_inputs_v1(bad_admission, runtime_root=fixture.root,
                        expected_machine_id=MACHINE)
        self.assertLessEqual(len(driver._encode_driver_state_locked()), 65536)
        before = fixture.reader.stat(str(driver.fixture_path))
        driver._persist_driver_state(persistence_reason="playable_episode_binding")
        after = fixture.reader.stat(str(driver.fixture_path))
        self.assertIsNone(driver._driver_state_error)
        self.assertNotEqual(after.file_id, before.file_id)
        self.assertNotEqual(after, fixture.basis.driver_identity)
        self.assertEqual(fixture.reader.stat(fixture.basis.refs.save.path), fixture.basis.save_identity)

        with self.assertRaises(ValueError):
            owner.validate_current_saved_cold_inputs_v1(basis, basis_ref=basis_ref,
                validation_ref=validation_ref, reader=fixture.reader)
        root = fixture.root
        (root / "p37-responses").mkdir()
        (root / "p37-queue").mkdir()
        game: JsonObject = {"machine_id": MACHINE, "pid": 999, "creation_filetime": "134370000000000001",
            "creation_date": "fixture-new", "command": ["D:/fixture/ck3.exe"], "old_save_loaded": True, "load_save_name": "xar_checkpoint"}
        game_ref = fixture.write("ROOT-ACTUAL-GAME-LAUNCH-C23.json", game)
        identities: dict[int, JsonObject] = {999: {"pid": 999,
            "creation_filetime": game["creation_filetime"], "executable": "D:/fixture/ck3.exe"}}
        processes: list[JsonValue] = []
        for pid, role in ((301, "sdk_queue"), (302, "sdk_application")):
            identities[pid] = {"pid": pid, "creation_filetime": str(134370000000000000 + pid),
                "executable": "D:/fixture/python.exe"}
            processes.append({"role": role, **identities[pid]})
        pair_ref = fixture.write("ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json", {
            "machine_id": MACHINE, "status": "SDK_PAIR_HANDLES_RETAINED", "rpc_started": False,
            "at_utc": "2026-10-21T06:10:00Z", "processes": processes})
        diagnostics: JsonObject = {"bridge_pid": 999, "pipe_name": PIPE,
            "connection_generation": 2, "hello": {"pid": 999, "connection_generation": 2,
                "ck3_build_match": True, "game_adapter_id": "ck3-1.20.0.4-msvc-x64",
                "game_adapter_status": "ready"}}
        opening = SavedFrameV1("native:12", 13, 12, basis.frame.date_raw,
            basis.frame.actor_character_id, basis.frame.episode_run_id)
        semantic: JsonObject = {"snapshot_id": opening.snapshot_id, "revision": opening.revision,
            "native_revision": opening.native_revision, "date_raw": opening.date_raw,
            "episode_character_id": opening.actor_character_id, "episode_run_id": opening.episode_run_id,
            "succession_lifecycle": inputs.checkpoint["succession_lifecycle"],
            "campaign_goal": basis.campaign_goal_anchor, "map_ready": True, "paused": True,
            "active_event": None, "pending_character_interaction": None, "diagnostics": diagnostics}
        sem_ref = fixture.write("p37-responses/" + str(basis.next_sequence).zfill(4) + "-1-result.json", {
            "started_at_utc": "2026-10-21T06:10:01Z", "ended_at_utc": "2026-10-21T06:10:02Z",
            "request": {"sequence": basis.next_sequence,
                "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}},
            "result": {"is_error": False, "result_type": "complete", "structured_content": semantic}})
        capabilities = {"episode_character_id": opening.actor_character_id,
            "episode_run_id": opening.episode_run_id, "episode_identity_pending": False, "one_life_terminal": False,
            "diagnostics": diagnostics, "native_session_control": {"configured": True,
                "restore_checkpoint": True, "driver_state_path": basis.refs.driver.path,
                "driver_state_restored": True, "driver_state_restore_kind": "cold_checkpoint",
                "episode_binding_state": "active_resumed", "driver_state_error": None,
                "cold_candidate_rejection": None}, "checkpoint_materialization": {
                "configured": True, "save_dir": str(Path(basis.refs.save.path).parent),
                "filename": Path(basis.refs.save.path).name}}
        cap_ref = fixture.write("p37-responses/" + str(basis.next_sequence + 1).zfill(4) + "-1-result.json", {
            "started_at_utc": "2026-10-21T06:10:03Z", "ended_at_utc": "2026-10-21T06:10:04Z",
            "request": {"sequence": basis.next_sequence + 1, "tool": "ck3_get_capabilities", "arguments": {}},
            "result": {"is_error": False, "result_type": "complete", "structured_content": capabilities}})
        marker_ref = fixture.write("p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json", {
            "schema": "xar.c23.normal-checkpoint-cold-bound/v1", "machine_id": MACHINE,
            "opening_frame": opening.to_wire(), "checkpoint": inputs.checkpoint,
            "completed_cycles": basis.completed_cycles, "T0_date_raw": basis.origin.start_date_raw,
            "new_ordinary_cycle_credit": 0, "AUTO_or_MET_replayed": False,
            "semantic_response": sem_ref.path, "before_source_kind": "actual_cold_semantic_snapshot",
            "observed_at_utc": "2026-10-21T06:10:05Z"})
        admission_ref = fixture.write("ROOT-P37C23-COLD-RESUME-ADMISSION.json", {
            "machine_id": MACHINE, "basis_ref": basis_ref.to_wire(),
            "validation_ref": validation_ref.to_wire(), "new_Game": game})
        sources = owner.WarmSourceRefsV1(game_ref, pair_ref, sem_ref, cap_ref, marker_ref, admission_ref)
        reader = WarmFixtureReader(identities)
        proof = owner.validate_warm_binding_v1(inputs, sources=sources, reader=reader, runtime_root=root)
        self.assertEqual(proof.phase, "warm_bound")
        self.assertTrue(proof.closed_driver_identity_replaced)
        self.assertEqual(proof.closed_driver_identity, before)
        self.assertEqual(proof.driver_identity, after)
        self.assertEqual(wire(proof.to_wire())["closed_driver_ref"], basis.refs.driver.to_wire())
        for pid in (999, 301):
            original_identity = identities[pid]
            identities[pid] = {**original_identity, "creation_filetime": "134370000000009999"}
            with self.subTest(pid=pid), self.assertRaises(ValueError):
                owner.validate_warm_binding_v1(inputs, sources=sources, reader=reader, runtime_root=root)
            identities[pid] = original_identity
        game_identity = identities[999]
        identities[999] = {**game_identity, "executable": "D:/fixture/other.exe"}
        with self.assertRaises(ValueError):
            owner.validate_warm_binding_v1(inputs, sources=sources, reader=reader, runtime_root=root)
        identities[999] = game_identity
        actual_cp = dict(driver._last_checkpoint)
        driver._last_checkpoint = {**actual_cp, "date_raw": basis.frame.date_raw + 24}
        driver._persist_driver_state(persistence_reason="fixture_wrong_checkpoint")
        with self.assertRaises(ValueError):
            owner.validate_warm_binding_v1(inputs, sources=sources, reader=reader, runtime_root=root)
        driver._last_checkpoint = actual_cp
        driver._persist_driver_state(persistence_reason="fixture_restore_checkpoint")
        self.assertEqual(owner.validate_warm_binding_v1(inputs, sources=sources,
            reader=reader, runtime_root=root).phase, "warm_bound")
        fixture.measure()


if __name__ == "__main__":
    unittest.main()


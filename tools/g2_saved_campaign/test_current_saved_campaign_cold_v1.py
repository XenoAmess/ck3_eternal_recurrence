"""Typed producer/JSON/consumer cold boundary and finite SDK persistence fixtures."""
from __future__ import annotations

import copy
import ast
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from typing import Callable, Protocol, runtime_checkable

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, CurrentSavedBasisV1, ExactRefV1, JsonObject, JsonValue, SavedFrameV1,
    encode_current_saved_basis_v1, exact_read,
    parse_json, parse_ref, record, json_object, json_value, integer, text, qualify_current_saved_basis_v1,
)
from tools.g2_saved_campaign import test_current_saved_basis_v1 as basis_fixture
from tools.g2_saved_campaign.test_current_saved_basis_v1 import (
    DiskReader, MACHINE, file_ref, pure_basis,
)
from tools.g2_saved_campaign import prepare_current_saved_campaign_cold_v1 as producer
from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign import current_saved_campaign_feeder_v1 as feeder
from xar_autoplayer.bridge.native_driver import NativeHeadlessGameplayDriver
from xar_autoplayer import environment

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


def score_junction() -> owner.CampaignScoreJunctionV1:
    target = r"D:\synthetic-current-saved\canonical-score"
    return owner.CampaignScoreJunctionV1(path=producer.child_v1(ROOT, "campaign-score"),
        exact_target=target, must_verify_same_FileID=True,
        target_file_id="9007199254740993", target_device="9007199254740995",
        anchor_ref=ExactRefV1(producer.child_v1(target, "CAMPAIGN-ANCHOR.json"), 1, "a" * 64))


def plan() -> producer.ColdPlanV1:
    names = tuple(sorted(producer.CANONICAL_NAMES))
    source_rows = tuple(producer.SourceRowV1(ref(relative.replace("/", "\\")), relative)
        for relative in sorted(producer.GENERIC_SOURCE_PATHS))
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


@runtime_checkable
class FileDigestV1(Protocol):
    def __call__(self, path: Path) -> str: ...


@runtime_checkable
class ScreenParserV1(Protocol):
    def __call__(self, value: object, *, machine_id: str, repo: Path,
            git_head: str, at_utc: datetime) -> JsonObject: ...


@runtime_checkable
class ColdProfileVerifierV1(Protocol):
    def __call__(self, spec: environment.EnvironmentSpec) -> JsonObject: ...


class TypedColdContractTests(unittest.TestCase):
    def test_generated_supervisor_preserves_path_digest_and_screen_contract(self) -> None:
        material_path = os.environ.get("XAR_CURRENT_SAVED_SUPERVISOR_MATERIAL")
        import_root = os.environ.get("XAR_CURRENT_SAVED_SUPERVISOR_IMPORT_ROOT")
        if material_path is None:
            material = foreground_supervisor_material_v1()
        else:
            if import_root is None:
                raise RuntimeError("actual supervisor requires its exact companion import root")
            with Path(material_path).open("rb") as stream:
                material = stream.read(262145)
            self.assertLessEqual(len(material), 262144)
        generated = producer.emit_supervisor_v1(material, machine_id=MACHINE)
        namespace: dict[str, object] = {"__name__": "current_saved_supervisor_fixture",
            "__file__": str(Path(import_root) / "root_native30_supervisor_c23.py")
            if import_root is not None else __file__}
        search = ([import_root] if import_root is not None else []) + sys.path
        with patch.object(sys, "path", search):
            exec(compile(generated, "<actual emitted supervisor prefix>", "exec"), namespace)
        hasher = namespace.get("digest")
        parser = namespace.get("parse_screen_admission_v1")
        if not isinstance(hasher, FileDigestV1) or not isinstance(parser, ScreenParserV1):
            raise TypeError("generated file hasher and screen parser must be callable")
        for path in (Path(__file__), Path(producer.__file__)):
            self.assertEqual(hasher(path), hashlib.sha256(path.read_bytes()).hexdigest())
        repo = Path(ROOT)
        at = datetime(2026, 10, 21, 6, tzinfo=timezone.utc)
        screen: JsonObject = {"schema": "xar.C23-root-resource-screen-admission/v3",
            "machine_id": MACHINE, "observed_at_utc": at.isoformat(), "status": "ACQUIRED",
            "task_id": "synthetic-current-screen", "sequence": 23, "repo": str(repo),
            "git_head": "f" * 40, "reviewer": "/root", "provenance": [ref("proof.json").to_wire()]}
        parsed = parser(wire(screen), machine_id=MACHINE, repo=repo,
            git_head="f" * 40, at_utc=at)
        self.assertEqual(parsed["sequence"], 23)
        for sequence in (True, 23.0, None):
            with self.subTest(sequence=sequence), self.assertRaises(ValueError):
                parser({**screen, "sequence": sequence}, machine_id=MACHINE, repo=repo,
                    git_head="f" * 40, at_utc=at)

    def test_plan_producer_json_consumer_roundtrip(self) -> None:
        item = plan()
        parsed = producer.parse_plan_v1(wire(item.to_wire()))
        self.assertEqual(parsed, item)
        self.assertIsInstance(parsed.source_rows, tuple)
        self.assertEqual(len(parsed.canonical_entry_paths), 8)
        self.assertIn("tools/ck3_live_run_id.py", {row.relative_path for row in parsed.source_rows})
        self.assertIn("tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py",
            {row.relative_path for row in parsed.source_rows})
        bad = parsed.to_wire()
        source_rows = [row.to_wire() for row in parsed.source_rows]
        identity = next(row for row in source_rows if row["relative_path"] == "tools/ck3_live_run_id.py")
        identity["relative_path"] = "tools/g2_saved_campaign/ck3_live_run_id.py"
        bad["source_rows"] = [json_value(row) for row in source_rows]
        with self.assertRaises(ValueError):
            producer.parse_plan_v1(wire(bad))


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
            item.basis_ref, item.validation_ref, item.producer_ref, ROOT, outputs, score_junction(),
            item.canonical_entry_paths, item.closure_entry_paths, item.import_roots,
            8, len(outputs), allocated, allocated + 1 + 131072)
        self.assertEqual(producer.parse_quote_v1(wire(quote.to_wire())), quote)
        self.assertEqual(record(wire(quote.to_wire())["campaign_score_junction"])["target_file_id"],
            "9007199254740993")
        cases: list[tuple[str, JsonValue, bool]] = [(key, None, True)
            for key in ("target_file_id", "target_device", "anchor_ref")]
        cases += [(key, value, False) for key, value in (("target_file_id", True),
            ("target_file_id", 1.0), ("target_device", "01"),
            ("must_verify_same_FileID", 1), ("anchor_ref", None))]
        for key, value, missing in cases:
            bad = quote.to_wire()
            part = json_object(bad["campaign_score_junction"])
            if missing:
                del part[key]
            else:
                part[key] = json_value(value)
            bad["campaign_score_junction"] = part
            with self.subTest(key=key, missing=missing), self.assertRaises(ValueError):
                producer.parse_quote_v1(wire(bad))
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



    def test_cap_pretransport_basis_json_owner_and_sdk_closure_consumers(self) -> None:
        from tools.g2_saved_campaign import current_saved_basis_v1 as basis_model

        fixture = basis_fixture.CapPretransportFailureFixture()
        checked = basis_model.validate_cap_pretransport_failure_evidence_v2(
            fixture.epoch, reader=fixture.reader)
        epoch_ref = fixture.reader.put("cap-v2-owner-epoch.json", fixture.epoch.to_wire())
        basis = basis_model.build_cap_pretransport_failure_basis_v2(
            checked, epoch_ref=epoch_ref, observed_at_utc="2026-10-21T14:01:00Z",
            sidecars=(), reader=fixture.reader)
        basis_ref = fixture.reader.put("cap-v2-owner-basis.json", basis.to_wire())
        qualification = basis_model.build_cap_pretransport_failure_qualification_v2(
            checked, basis, basis_ref=basis_ref, reader=fixture.reader,
            observed_at_utc="2026-10-21T14:01:01Z")
        qualification_ref = fixture.reader.put(
            "cap-v2-owner-qualification.json", qualification.to_wire())
        parsed = owner.parse_basis_qualification_v1(
            json.loads(json.dumps(qualification.to_wire())),
            expected_machine_id=basis.machine_id)
        self.assertIsInstance(parsed, basis_model.CapPretransportFailureQualificationV2)
        self.assertEqual(parsed, qualification)
        closed = owner._closed_epoch(basis, fixture.reader)
        self.assertEqual(closed.next_sequence, checked.next_sequence)
        self.assertEqual(closed.old_game.pid, checked.old_game.pid)
        self.assertEqual(checked.history_count, checked.previous_history_count + 1)
        # This is the SDK-closure receiver's narrow input boundary, not a claim
        # that the synthetic fixture passed the entire immutable runtime graph.
        inputs = owner.CurrentSavedColdInputsV1(
            basis, {}, {}, json_object(basis.checkpoint), {}, closed,
            basis_ref, qualification_ref)
        with patch.object(owner, "LocalBasisReaderV1", return_value=fixture.reader):
            sdk = owner.validate_current_saved_prepared_sdk_closure_v1(
                fixture.epoch.refs.sdk_closed.to_wire(), inputs=inputs)
            self.assertIs(sdk["normal"], False)
            with self.assertRaises(ValueError):
                owner.validate_current_saved_prepared_sdk_closure_v1(
                    fixture.epoch.refs.first_exception.to_wire(), inputs=inputs)

        historical = basis_fixture.FailureEpochFixture()
        old_checked = historical.validated()
        old_epoch_ref = historical.reader.put(
            "legacy-v1-owner-epoch.json", historical.epoch.to_wire())
        old_basis = basis_model.build_readonly_cold_failure_basis_v1(
            old_checked, epoch_ref=old_epoch_ref,
            observed_at_utc="2026-10-21T14:02:00Z", sidecars=(),
            reader=historical.reader)
        old_basis_ref = historical.reader.put(
            "legacy-v1-owner-basis.json", old_basis.to_wire())
        old_qualification = basis_model.build_readonly_cold_failure_qualification_v1(
            old_checked, old_basis, basis_ref=old_basis_ref, reader=historical.reader,
            observed_at_utc="2026-10-21T14:02:01Z")
        old_parsed = owner.parse_basis_qualification_v1(
            json.loads(json.dumps(old_qualification.to_wire())),
            expected_machine_id=old_basis.machine_id)
        self.assertIsInstance(old_parsed, basis_model.ReadonlyColdFailureQualificationV1)
        self.assertNotIsInstance(old_parsed, basis_model.CapPretransportFailureQualificationV2)
        self.assertEqual(old_parsed, old_qualification)
        old_closed = owner._closed_epoch(old_basis, historical.reader)
        self.assertEqual(old_closed.next_sequence, old_checked.next_sequence)


def foreground_supervisor_material_v1() -> bytes:
    """Portable original supervisor shape; optional real material exercises the same renderer."""
    path = os.environ.get("XAR_CURRENT_SAVED_SUPERVISOR_MATERIAL")
    if path is not None:
        with Path(path).open("rb") as stream:
            raw = stream.read(262145)
        if len(raw) > 262144:
            raise ValueError("bounded original supervisor material")
        return raw
    return b'''from __future__ import annotations
from datetime import datetime, timedelta
import ctypes
import hashlib
from pathlib import Path
import re
PLACEMENT_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):
    return Path(path).read_bytes()
def main(args):
    placement = load_file("root_owned_generation", repo / "tools/g2_saved_campaign/managed_desktop1_placement.py", PLACEMENT_SHA)
    if True:
        _, desktop_after = placement.desktop_inventory()
        foreground_after = user.GetForegroundWindow()
        write(N / "ROOT-LAUNCH-USER-DESKTOP-OBSERVED-C23.json", {"foreground_before": foreground,
            "foreground_after": foreground_after, "desktop_before": desktop_before, "desktop_after": desktop_after,
            "game_pid": generation.pid, "game_creation_filetime": generation.creation_filetime,
            "gameplay_input": False, "desktop_switch_requested": False})
        if foreground_after != foreground or desktop_after != desktop_before:
            raise RuntimeError("user foreground/desktop changed during launch; stop without restoring user windows")
    return 0
'''


def rendered_foreground_nodes_v1() -> list[ast.stmt]:
    generated = producer.emit_supervisor_v1(foreground_supervisor_material_v1(), machine_id=MACHINE)
    tree = ast.parse(generated)
    imported = [node for node in tree.body if isinstance(node, ast.ImportFrom)
        and node.module == "tools.g2_saved_campaign"
        and any(alias.name == "background_foreground_contract_v1" for alias in node.names)]
    if len(imported) != 1:
        raise ValueError("generated consumer must import the standalone contract")
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    blocks = [main.body]
    for node in ast.walk(main):
        if isinstance(node, (ast.Try, ast.If, ast.While, ast.For, ast.With)):
            blocks.append(node.body)
    matches: list[list[ast.stmt]] = []
    for block in blocks:
        starts = [i for i, node in enumerate(block) if isinstance(node, ast.Assign)
            and any(isinstance(part, ast.Name) and part.id == "desktop_after" for part in ast.walk(node.targets[0]))]
        ends = [i for i, node in enumerate(block) if isinstance(node, ast.If)
            and isinstance(node.test, ast.UnaryOp) and isinstance(node.test.op, ast.Not)
            and isinstance(node.test.operand, ast.Attribute) and node.test.operand.attr == "permitted"]
        if len(starts) == len(ends) == 1 and starts[0] < ends[0]:
            matches.append(block[starts[0]:ends[0]+1])
    if len(matches) != 1:
        raise ValueError("one actual emitted foreground consumer block")
    return matches[0]


class ForegroundGetterV1:
    def __init__(self, windows: tuple[int, int]) -> None:
        self.windows = iter(windows)
        self.argtypes: object = None
        self.restype: object = None

    def __call__(self) -> int:
        return next(self.windows)


class ForegroundPidGetterV1:
    def __init__(self, pid: int, thread: int) -> None:
        self.pid = pid
        self.thread = thread
        self.argtypes: object = None
        self.restype: object = None

    def __call__(self, window: object, pointer: object) -> int:
        import ctypes
        if not isinstance(window, ctypes.c_void_p):
            raise TypeError("actual HWND pointer boundary")
        target: object = getattr(pointer, "_obj", None)
        if not isinstance(target, ctypes.c_ulong):
            raise TypeError("actual DWORD output pointer boundary")
        target.value = self.pid
        return self.thread


class ForegroundUserV1:
    def __init__(self, windows: tuple[int, int], pid: int, thread: int) -> None:
        self.GetForegroundWindow = ForegroundGetterV1(windows)
        self.GetWindowThreadProcessId = ForegroundPidGetterV1(pid, thread)


class LaunchForegroundContractTests(unittest.TestCase):
    DESKTOP = "11b2eee2-855d-4029-b35c-59adc9a19203"

    def _input(self) -> dict[str, object]:
        return {"foreground_before": 101, "foreground_after": 103,
            "foreground_after_pid": 71, "desktop_before": self.DESKTOP,
            "desktop_after": self.DESKTOP, "game_pid": 61, "owned_auxiliary_pids": []}

    def test_pure_contract_json_facts_and_all_classifications(self) -> None:
        from tools.g2_saved_campaign import background_foreground_contract_v1 as contract
        cases: tuple[tuple[int, int | None, str, list[int], str, bool], ...] = (
            (101, 71, self.DESKTOP, [], "FOREGROUND_UNCHANGED", True),
            (103, 71, self.DESKTOP, [], "NON_GAME_USER_FOREGROUND", True),
            (103, None, self.DESKTOP, [], "UNKNOWN_FOREGROUND_OWNER", False),
            (101, None, self.DESKTOP, [], "UNKNOWN_FOREGROUND_OWNER", False),
            (103, 61, self.DESKTOP, [], "OWNED_GAME_FOREGROUND", False),
            (101, 61, self.DESKTOP, [], "OWNED_GAME_FOREGROUND", False),
            (103, 71, self.DESKTOP, [71], "OWNED_AUXILIARY_FOREGROUND", False),
            (103, 71, "964b3ff9-3cf7-4ba9-881b-47444f31cfbe", [], "USER_DESKTOP_CHANGED", False))
        for window, pid, desktop, auxiliary, classification, allowed in cases:
            value = self._input(); value.update(foreground_after=window, foreground_after_pid=pid,
                desktop_after=desktop, owned_auxiliary_pids=auxiliary)
            with self.subTest(classification=classification, window=window):
                observed = contract.classify_current_saved_launch_foreground_v1(value)
                self.assertEqual(observed.classification, classification)
                self.assertIs(observed.permitted, allowed)
                self.assertIs(observed.foreground_unchanged, window == 101)
                self.assertEqual(contract.parse_current_saved_launch_foreground_v1(
                    json.loads(json.dumps(observed.to_wire()))), observed)
        changed = contract.classify_current_saved_launch_foreground_v1(self._input()).to_wire()
        changed["foreground_unchanged"] = True
        with self.assertRaises(ValueError): contract.parse_current_saved_launch_foreground_v1(changed)

    def test_entry_rejects_missing_alias_wrong_types_and_unproven_owners(self) -> None:
        from tools.g2_saved_campaign import background_foreground_contract_v1 as contract
        cases: tuple[tuple[str, object], ...] = (
            ("foreground_before", True), ("foreground_before", 101.0),
            ("foreground_after", 2**53), ("foreground_after", -1),
            ("foreground_after_pid", True), ("foreground_after_pid", 71.0),
            ("foreground_after_pid", 0), ("foreground_after_pid", 2**32),
            ("game_pid", True), ("game_pid", 61.0), ("game_pid", 0),
            ("desktop_before", None), ("desktop_after", "unknown"),
            ("owned_auxiliary_pids", None), ("owned_auxiliary_pids", (71,)),
            ("owned_auxiliary_pids", [True]), ("owned_auxiliary_pids", [71.0]),
            ("owned_auxiliary_pids", [71, 71]), ("owned_auxiliary_pids", [61]))
        for key, bad in cases:
            value = self._input(); value[key] = bad
            with self.subTest(key=key, bad=bad), self.assertRaises(ValueError):
                contract.classify_current_saved_launch_foreground_v1(value)
        for key in self._input():
            value = self._input(); del value[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                contract.classify_current_saved_launch_foreground_v1(value)
        value = self._input(); value["pid_alias"] = 71
        with self.assertRaises(ValueError): contract.classify_current_saved_launch_foreground_v1(value)
        value = self._input(); value["foreground_after"] = 0
        with self.assertRaises(ValueError): contract.classify_current_saved_launch_foreground_v1(value)

    def test_real_rendered_main_win32_boundary_and_receipt(self) -> None:
        import ctypes
        from types import SimpleNamespace
        from tools.g2_saved_campaign import background_foreground_contract_v1 as contract
        nodes = rendered_foreground_nodes_v1()
        other_desktop = "964b3ff9-3cf7-4ba9-881b-47444f31cfbe"
        cases: tuple[tuple[int, int, int, int, tuple[str, str], bool, str], ...] = (
            (101, 101, 71, 1, (self.DESKTOP, self.DESKTOP), True, "FOREGROUND_UNCHANGED"),
            (103, 103, 71, 1, (self.DESKTOP, self.DESKTOP), True, "NON_GAME_USER_FOREGROUND"),
            (103, 103, 61, 1, (self.DESKTOP, self.DESKTOP), False, "OWNED_GAME_FOREGROUND"),
            (103, 103, 0, 0, (self.DESKTOP, self.DESKTOP), False, "UNKNOWN_FOREGROUND_OWNER"),
            (103, 107, 71, 1, (self.DESKTOP, self.DESKTOP), False, "UNKNOWN_FOREGROUND_OWNER"),
            (103, 103, 71, 1, (other_desktop, other_desktop), False, "USER_DESKTOP_CHANGED"),
            (103, 103, 71, 1, (self.DESKTOP, other_desktop), False, "USER_DESKTOP_CHANGED"),
            (101, 101, 71, 1, (other_desktop, self.DESKTOP), False, "UNKNOWN_FOREGROUND_OWNER"))
        for first, final, pid, thread, desktops, expected, classification in cases:
            recorded: list[dict[str, object]] = []
            user = ForegroundUserV1((first, final), pid, thread)
            desktop_reads = iter(desktops)
            def write(path: Path, value: object) -> None:
                self.assertEqual(path.name, "ROOT-LAUNCH-USER-DESKTOP-OBSERVED-C23.json")
                recorded.append(record(value))
            namespace: dict[str, object] = {"ctypes": ctypes, "user": user,
                "placement": SimpleNamespace(desktop_inventory=lambda: ((), next(desktop_reads))),
                "foreground": 101, "desktop_before": self.DESKTOP,
                "generation": SimpleNamespace(pid=61, creation_filetime=134370617141148601),
                "N": Path(ROOT), "write": write, "_launch_foreground_contract_v1": contract}
            permitted = True
            try:
                exec(compile(ast.Module(body=nodes, type_ignores=[]), "<actual rendered launch consumer>", "exec"), namespace)
            except RuntimeError:
                permitted = False
            with self.subTest(classification=classification, final=final):
                self.assertIs(permitted, expected)
                self.assertEqual(len(recorded), 1)
                self.assertEqual(recorded[0]["classification"], classification)
                self.assertIs(recorded[0]["foreground_unchanged"], final == 101)
                self.assertIs(recorded[0]["gameplay_input"], False)
                self.assertIs(recorded[0]["desktop_switch_requested"], False)
                self.assertEqual(user.GetWindowThreadProcessId.argtypes,
                    [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)])
                self.assertIs(user.GetWindowThreadProcessId.restype, ctypes.c_ulong)
                self.assertEqual(user.GetForegroundWindow.argtypes, [])
        for node in nodes:
            self.assertFalse(any(isinstance(part, ast.Attribute) and part.attr in
                ("SetForegroundWindow", "ShowWindow", "SwitchDesktop", "SetWindowPos") for part in ast.walk(node)))

    def test_actual_compose_placement_source_seal_and_runtime_lookup(self) -> None:
        from types import SimpleNamespace
        tree = ast.parse(Path(producer.__file__).read_bytes())
        compose = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compose_v1")
        statements: list[ast.stmt] = [node for node in compose.body if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "put" and node.value.args
            and isinstance(node.value.args[0], ast.Constant)
            and node.value.args[0].value == "root_native30_supervisor_c23.py"]
        self.assertEqual(len(statements), 2)
        placement = b'"""Synthetic frozen placement source for pin derivation."""\n'
        values = {"root_native30_supervisor_c23.py": foreground_supervisor_material_v1(),
            "tools/g2_saved_campaign/managed_desktop1_placement.py": placement}
        def get(name: str) -> bytes:
            return values[name]
        def put(name: str, data: bytes) -> None:
            values[name] = data
        namespace: dict[str, object] = dict(vars(producer))
        namespace.update(p=SimpleNamespace(machine_id=MACHINE), get=get, put=put)
        exec(compile(ast.Module(body=statements, type_ignores=[]), "<actual compose placement seal>", "exec"), namespace)
        generated = ast.parse(values["root_native30_supervisor_c23.py"])
        pins = [node for node in generated.body if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "PLACEMENT_SHA" for target in node.targets)]
        self.assertEqual(len(pins), 1)
        self.assertEqual(ast.literal_eval(pins[0].value), hashlib.sha256(placement).hexdigest())
        loads = [node for node in ast.walk(generated) if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name) and node.func.id == "load_file"
            and node.args and isinstance(node.args[0], ast.Constant)
            and node.args[0].value == "root_owned_generation"]
        self.assertEqual(len(loads), 1)
        self.assertEqual(ast.unparse(loads[0].args[1]), "N / 'tools/g2_saved_campaign/managed_desktop1_placement.py'")
        self.assertIn("tools/g2_saved_campaign/managed_desktop1_placement.py", producer.GENERIC_SOURCE_PATHS)
        self.assertIn("tools/g2_saved_campaign/background_foreground_contract_v1.py", producer.GENERIC_SOURCE_PATHS)
        self.assertIn("tools/g2_saved_campaign/current_saved_background_display_v1.py", producer.GENERIC_SOURCE_PATHS)


def run_actual_supervisor_import_chain_regression_v1(runtime_root: Path) -> dict[str, str]:
    """Two fresh interpreters use a sealed runtime; only candidate source reads are overlaid.

    This explicit integration qualification is separate from portable unit tests.
    It never writes the runtime, changes module aliases, starts a process holder,
    or claims that the candidate bytes were deployed there.
    """
    script = r'''
import hashlib, importlib.machinery, importlib.util, io, json, sys
from pathlib import Path
from unittest.mock import patch
root=Path(sys.argv[1]).resolve(strict=True)
producer_path=Path(sys.argv[2]).resolve(strict=True)
candidate_path=Path(sys.argv[3]).resolve(strict=True)
mode=sys.argv[4]
sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('_candidate_cold_producer',producer_path)
assert spec is not None and spec.loader is not None
producer=importlib.util.module_from_spec(spec);sys.modules[spec.name]=producer;spec.loader.exec_module(producer)
import root_native30_supervisor_c23 as supervisor
from root_c23_canonical_outer import prepare_supervisor
canonical=prepare_supervisor(root,enabled=True)
source=(root/'root_native30_supervisor_c23.py').read_bytes()
placement=root/'tools/g2_saved_campaign/managed_desktop1_placement.py'
original=placement.read_bytes();candidate=candidate_path.read_bytes()
before=b'sys.path.insert(0, str(Path(__file__).resolve().parents[1]))\nimport ck3_live_run_id\nsys.path.insert(0, str(Path(__file__).resolve().parents[2]))\n'
after=b'sys.path.insert(0, str(Path(__file__).resolve().parents[2]))\nfrom tools import ck3_live_run_id\n'
assert original.count(before)==1 and original.replace(before,after,1)==candidate
open_path=Path.open;get_data=importlib.machinery.SourceFileLoader.get_data
def candidate_open(path,*args,**kwargs):
    if path.resolve()==placement:
        assert args==('rb',) and not kwargs
        return io.BytesIO(candidate)
    return open_path(path,*args,**kwargs)
def candidate_load(loader,path):
    return candidate if Path(path).resolve()==placement else get_data(loader,path)
if mode=='original':
    try:
        producer.probe_current_saved_supervisor_import_chain_v1(supervisor,canonical,
            supervisor_source=source,runtime_root=root)
    except ModuleNotFoundError as error:
        assert error.name=='g2_saved_campaign.canonical_native_provider_chain_v1'
        package=sys.modules['g2_saved_campaign']
        assert Path(package.__file__).resolve()==root/'tools/g2_saved_campaign/__init__.py'
        print(json.dumps({'result':'ORIGINAL_REJECTED','package':package.__file__}))
    else: raise AssertionError('original shadowing was not reproduced')
else:
    supervisor.PLACEMENT_SHA=hashlib.sha256(candidate).hexdigest()
    with patch.object(Path,'open',candidate_open),patch.object(importlib.machinery.SourceFileLoader,'get_data',candidate_load):
        observed=producer.probe_current_saved_supervisor_import_chain_v1(supervisor,canonical,
            supervisor_source=source,runtime_root=root)
    package=sys.modules['g2_saved_campaign']
    assert {Path(path).resolve() for path in package.__path__}=={root/'creator-tools/g2_saved_campaign'}
    assert Path(sys.modules['tools.g2_saved_campaign'].__file__).resolve()==root/'tools/g2_saved_campaign/__init__.py'
    assert all(Path(path).parent==root/'creator-tools/g2_saved_campaign' for path in observed.creator_sources)
    assert Path(observed.placement_source)==placement
    assert str(root/'tools') not in sys.path
    print(json.dumps({'result':'CANDIDATE_IMPORT_CHAIN_PASSED','creator':observed.creator_sources[0],
        'placement':observed.placement_source,'runtime_write_calls':0,'candidate_read_overlay':True}))
'''
    placement = Path(producer.__file__).with_name("managed_desktop1_placement.py")
    base_value: object = getattr(sys, "_base_executable", None)
    if not isinstance(base_value, str) or not base_value:
        raise ValueError("actual base interpreter path is required")
    base = Path(base_value).resolve(strict=True)
    if not base.is_file():
        raise ValueError("actual base interpreter must be a file")
    output: dict[str, str] = {}
    for mode in ("original", "candidate"):
        completed = subprocess.run([str(base), "-I", "-B", "-S", "-X", "utf8", "-c", script,
            str(runtime_root), producer.__file__, str(placement), mode],
            capture_output=True, text=True, check=True, timeout=60)
        result = record(json.loads(completed.stdout))
        output[mode] = text(result["result"])
    return output


class SupervisorImportChainTests(unittest.TestCase):
    def test_public_probe_requires_original_import_order_before_sdk(self) -> None:
        tree = ast.parse(Path(producer.__file__).read_bytes())
        probe = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name == "run_current_saved_startup_consumer_probe_v1")
        chain = [node for node in probe.body if isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "probe_current_saved_supervisor_import_chain_v1"]
        bootstrap = [node for node in probe.body if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "module_at" and len(node.value.args) > 1
            and isinstance(node.value.args[1], ast.Constant)
            and node.value.args[1].value == "root_checkpoint_bootstrap_c23.py"]
        self.assertEqual(len(chain), 1); self.assertEqual(len(bootstrap), 1)
        self.assertLess(probe.body.index(chain[0]), probe.body.index(bootstrap[0]))
        helper = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name == "probe_current_saved_supervisor_import_chain_v1")
        self.assertFalse(any(isinstance(node, ast.Attribute) and node.attr in
            ("clear", "reload", "start", "launch_game") for node in ast.walk(helper)))


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
    previous_fixture_machine: tuple[str, str]

    @classmethod
    def setUpClass(cls) -> None:
        global MACHINE
        cls.previous_fixture_machine = (MACHINE, basis_fixture.MACHINE)
        if "XAR_CURRENT_SAVED_BASIS_TEST_ROOT" in os.environ:
            from tools.ck3_live_run_id import current_machine_id
            execution_machine = current_machine_id()
            if os.environ.get("XAR_CURRENT_SAVED_BASIS_MACHINE_ID") != execution_machine:
                raise ValueError("explicit owned SDK fixture uses its actual execution machine")
            # Parameterize synthetic fixture records, never the production
            # current-machine provider or its environment override.
            MACHINE = execution_machine
            basis_fixture.MACHINE = execution_machine
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
        try:
            cls.fixture.setUpClass()
        except BaseException:
            MACHINE, basis_fixture.MACHINE = cls.previous_fixture_machine
            raise

    @classmethod
    def tearDownClass(cls) -> None:
        global MACHINE
        try:
            cls.fixture.tearDownClass()
        finally:
            MACHINE, basis_fixture.MACHINE = cls.previous_fixture_machine

    def test_campaign_score_junction_build_prepare_and_owner(self) -> None:
        fixture = self.fixture
        if not fixture.fixture_enabled:
            self.skipTest("explicit owned fixture, machine and finite review required")
        root = fixture.root / "score-case"
        state = root / "campaign-origin/state"
        save = state / "profile/save games/xar_checkpoint.ck3"
        old = fixture.basis
        basis = replace(old, refs=replace(old.refs,
            driver=replace(old.refs.driver, path=str(state / "native-session/driver-state.json")),
            save=replace(old.refs.save, path=str(save))),
            checkpoint={**old.checkpoint, "path": str(save)},
            campaign_goal_anchor={**old.campaign_goal_anchor, "origin_character_id": 1})
        attempt, target, other = root / "new", state.parent / "campaign-score", root / "other"
        attempt.mkdir(parents=True)
        target.mkdir(parents=True)
        other.mkdir()
        anchor: JsonObject = {"schema": "xar.ck3.campaign-score-fixed-anchor/v1",
            "machine_id": MACHINE, "campaign_id": "robert-first30-v20261019", "founder_character_id": 1,
            "observed_at_utc": "2026-10-19T03:04:29.665767+00:00",
            "start_date_raw": basis.origin.start_date_raw,
            "endpoint_date_raw": basis.origin.target_date_raw,
            "fixed_across_ruler_and_sdk_changes": True, "old_campaign_inputs_copied": 0}
        original = fixture.write("score-case/campaign-origin/campaign-score/CAMPAIGN-ANCHOR.json", anchor)
        material: JsonObject = {"schema": "xar.Source31-A20-complete-cold-quote/v1",
            "machine_id": MACHINE, "runtime_root": str(target.parent),
            "campaign_score_junction": {"path": str(target), "exact_target": str(target),
                "must_verify_same_FileID": True}}
        binding = owner.build_campaign_score_junction_v1(basis, material,
            runtime_root=attempt, anchor_ref=original, reader=fixture.reader)
        binding = owner.parse_campaign_score_junction_v1(wire(binding.to_wire()))
        self.assertEqual(binding.anchor_ref, original)
        no_origin = {key: value for key, value in basis.campaign_goal_anchor.items()
            if key != "origin_character_id"}
        with self.assertRaises(ValueError):
            owner.build_campaign_score_junction_v1(replace(basis, campaign_goal_anchor=no_origin),
                material, runtime_root=attempt, anchor_ref=original, reader=fixture.reader)
        link = Path(binding.path)
        try:
            with self.assertRaises((ValueError, FileNotFoundError)):
                owner.validate_campaign_score_junction_physical_v1(binding,
                    runtime_root=attempt, reader=fixture.reader)
            producer.prepare_campaign_score_junction_v1(binding, basis, approved_root=attempt)
            owner.validate_campaign_score_junction_physical_v1(binding,
                runtime_root=attempt, reader=fixture.reader)
            self.assertEqual(link.stat().st_ino, target.stat().st_ino)
            self.assertEqual(link.stat().st_dev, target.stat().st_dev)
            raw = Path(original.path).read_bytes()
            try:
                for key, value in (("machine_id", "other"),
                        ("start_date_raw", basis.origin.start_date_raw + 24),
                        ("founder_character_id", basis.frame.actor_character_id)):
                    Path(original.path).write_bytes(producer.encode_v1({**anchor, key: json_value(value)}))
                    changed = replace(binding, anchor_ref=file_ref(Path(original.path)))
                    with self.subTest(key=key), self.assertRaises(ValueError):
                        owner.validate_campaign_score_junction_source_v1(changed, basis,
                            runtime_root=attempt, reader=fixture.reader)
            finally:
                Path(original.path).write_bytes(raw)
            os.rmdir(link)
            subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(other)],
                check=True, capture_output=True)
            with self.assertRaises(ValueError):
                owner.validate_campaign_score_junction_physical_v1(binding,
                    runtime_root=attempt, reader=fixture.reader)
        finally:
            if link.is_junction():
                os.rmdir(link)
            fixture.measure()

    def test_shared_state_generated_make_spec_and_real_profile_consumer(self) -> None:
        fixture = self.fixture
        if not fixture.fixture_enabled:
            self.skipTest("explicit owned fixture, machine and finite review required")
        state = fixture.root / "shared-state"
        profile = state / "profile"
        profile.mkdir(parents=True)
        attempt = fixture.root / "new-attempt"
        attempt.mkdir()
        dlc = fixture.write("shared-state/profile/dlc_load.json", {"enabled_mods": [], "disabled_dlcs": []})
        manifest: JsonObject = {"machine_id": MACHINE, "state_dir": str(state), "profile_dir": str(profile),
            "load_profile": {"enabled_mods": [], "dlc_load_sha256": dlc.sha256},
            "mod": {"enabled": False, "mounted_mods": []}, "rules": {"profile": []}}
        env_sha = environment._contract_digest(dict(manifest))
        manifest["environment_sha256"] = env_sha
        fixture.write("shared-state/profile/xar-autoplayer-environment.json", manifest)
        driver_path = str(state / "native-session/driver-state.json")
        save_path = str(profile / "save games/xar_checkpoint.ck3")
        basis = replace(fixture.basis, refs=replace(fixture.basis.refs,
            driver=replace(fixture.basis.refs.driver, path=driver_path),
            save=replace(fixture.basis.refs.save, path=save_path)),
            checkpoint={**fixture.basis.checkpoint, "path": save_path,
                "succession_lifecycle": {**LIFECYCLE, "environment_sha256": env_sha}})
        paths = owner.derive_current_saved_state_paths_v1(basis)
        self.assertEqual(Path(paths.state_root), state)
        for bad in (replace(basis, refs=replace(basis.refs,
                driver=replace(basis.refs.driver, path=str(attempt / "native-session/driver-state.json")))),
                replace(basis, refs=replace(basis.refs, save=replace(basis.refs.save,
                    path=str(attempt / "wrong.ck3"))),
                    checkpoint={**basis.checkpoint, "path": str(attempt / "wrong.ck3")})):
            with self.assertRaises(ValueError):
                owner.derive_current_saved_state_paths_v1(bad)
        material_path = os.environ.get("XAR_CURRENT_SAVED_SUPERVISOR_MATERIAL")
        materials = {
            "root_native30_supervisor_c23.py": foreground_supervisor_material_v1().replace(b'def main(args):\n',
                b'def main(args):\n    spec = environment.make_spec(state_dir=N / "state", game_dir=game_dir)\n',1),
            "launch_sdk_p37c23_owner.py": b"args=['--environment-manifest',str(N/'state/profile/xar-autoplayer-environment.json')]\n",
            "root_p37c23_sdk_queue.py": b'STATE_DIR = N / "state"\n',
            "root_p37c23_mcp_entry.py": b'STATE_DIR=N/"state"\n',
        }
        if material_path is not None:
            materials = {name: (Path(material_path).parent / name).read_bytes()
                for name in producer.STATE_SOURCES_V1}
        materials["root_native30_supervisor_c23.py"] = producer.emit_supervisor_v1(
            materials["root_native30_supervisor_c23.py"], machine_id=MACHINE)
        generated = {name: producer.bind_current_saved_state_source_v1(name, materials[name], basis)
            for name in producer.STATE_SOURCES_V1}
        for name in ("root_p37c23_sdk_queue.py", "root_p37c23_mcp_entry.py"):
            state_nodes: list[ast.stmt] = [node for node in ast.parse(generated[name]).body
                if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                    and target.id == "STATE_DIR" for target in node.targets)]
            self.assertEqual(len(state_nodes), 1)
            state_scope: dict[str, object] = {"Path": Path, "N": attempt}
            exec(compile(ast.fix_missing_locations(ast.Module(body=state_nodes, type_ignores=[])), "<actual SDK state binding>", "exec"), state_scope)
            self.assertEqual(state_scope["STATE_DIR"], state)
        lists = [node for node in ast.walk(ast.parse(generated["launch_sdk_p37c23_owner.py"]))
            if isinstance(node, ast.List) and any(isinstance(item, ast.Constant)
                and item.value == "--environment-manifest" for item in node.elts)]
        self.assertEqual(len(lists), 1)
        index = next(i for i, node in enumerate(lists[0].elts)
            if isinstance(node, ast.Constant) and node.value == "--environment-manifest")
        self.assertEqual(ast.literal_eval(lists[0].elts[index+1]), paths.environment_manifest)
        tree = ast.parse(generated["root_native30_supervisor_c23.py"])
        calls: list[ast.stmt] = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "make_spec"]
        self.assertEqual(len(calls), 1)
        scope: dict[str, object] = {"Path": Path, "environment": environment, "game_dir": fixture.root}
        exec(compile(ast.fix_missing_locations(ast.Module(body=calls, type_ignores=[])), "<actual late make_spec>", "exec"), scope)
        spec = scope["spec"]
        if not isinstance(spec, environment.EnvironmentSpec):
            raise TypeError("real environment.make_spec result required")
        self.assertEqual(spec.manifest_path, Path(paths.environment_manifest))
        pre = owner.build_current_saved_prelaunch_v1(basis, basis_ref=ref("basis.json"),
            validation_ref=ref("qualification.json"), environment_sha256=env_sha, pipe_name=PIPE)
        fixture.write("new-attempt/ROOT-C23-COLD-PRELAUNCH.json", pre)
        bootstrap = (Path(material_path).with_name("root_checkpoint_bootstrap_c23.py").read_bytes()
            if material_path is not None else b'import hashlib,json\nfrom pathlib import Path\nN=Path(__file__).parent\nPRELAUNCH="ROOT-C23-COLD-PRELAUNCH.json"\nMACHINE="synthetic-current-saved-basis"\n'+b'\n'*20+b'def require(ok,why):\n assert ok,why\ndef sha(path):\n return hashlib.sha256(Path(path).read_bytes()).hexdigest()\ndef read(path):\n return json.loads(Path(path).read_bytes())\ndef checked(ref):\n return read(ref["path"])\ndef pin(path):\n return {}\ndef api():\n raise RuntimeError()\n')
        ns: dict[str, object] = {"__name__": "shared_state_bootstrap_fixture", "__file__": str(attempt / "bootstrap.py")}
        exec(compile(producer.emit_bootstrap_v1(bootstrap, machine_id=MACHINE), "<actual profile consumer>", "exec"), ns)
        ns["api"] = lambda: (environment, None, None)
        inputs = owner.CurrentSavedColdInputsV1(basis, {}, {}, {}, {},
            owner.ClosedEpochV1(basis.refs.closure, owner.CurrentGameIdentityV1(1,"1","fixture"),
                basis.next_sequence, (), basis.observed_at_utc, PIPE), ref("basis.json"), ref("qualification.json"))
        ns["load_current_saved_inputs_v1"] = lambda **kwargs: inputs
        verifier = ns["verify_cold_profile"]
        if not isinstance(verifier, ColdProfileVerifierV1):
            raise TypeError("generated actual profile consumer required")
        self.assertEqual(verifier(spec), manifest)
        wrong = environment.make_spec(state_dir=attempt / "state", game_dir=fixture.root)
        with self.assertRaises(FileNotFoundError):
            verifier(wrong)
        self.assertEqual(pre["closure_ref"], basis.refs.closure.to_wire())
        self.assertEqual(pre["driver_close_ref"], basis.refs.driver_close.to_wire())
        fixture.measure()

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
        basis_raw = json.dumps(parse_json(encode_current_saved_basis_v1(basis)),
            ensure_ascii=False, indent=2).encode("utf-8")
        self.assertNotEqual(basis_raw, encode_current_saved_basis_v1(basis))
        basis_ref = save_raw(fixture, "warm-basis.json", basis_raw)
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
        fixture.write("ROOT-CURRENT-SAVED-INPUTS01.json", {
            "schema": owner.CURRENT_INPUTS_SCHEMA, "machine_id": MACHINE,
            "basis_ref": basis_ref.to_wire(), "validation_ref": validation_ref.to_wire()})
        # Only the synthetic closed-epoch evidence shape is supplied here. The
        # public loader still executes its real immutable inputs, qualification,
        # seed/ledger, SAVE identity and warm native-header/kernel validators.
        def fixture_closed_epoch(actual_basis: CurrentSavedBasisV1,
                actual_reader: BasisReaderV1) -> owner.ClosedEpochV1:
            self.assertEqual(actual_basis, basis)
            self.assertIs(actual_reader, reader)
            return closed
        with patch.object(owner, "LocalBasisReaderV1", return_value=reader), \
                patch.object(owner, "_closed_epoch", new=fixture_closed_epoch):
            warm = owner.load_current_saved_warm_inputs_v1(runtime_root=root,
                expected_machine_id=MACHINE)
            self.assertEqual(warm.phase, "warm_bound")
            self.assertEqual(warm.inputs.seed, inputs.seed)
            self.assertTrue(warm.warm_proof.closed_driver_identity_replaced)
            self.assertEqual(warm.warm_proof.closed_driver_identity, before)
            self.assertEqual(warm.warm_proof.driver_identity, after)
            with self.assertRaises(ValueError):
                owner.load_current_saved_inputs_v1(runtime_root=root,
                    expected_machine_id=MACHINE)
        with self.assertRaises(ValueError):
            exact_read(reader, basis.refs.driver, 65536)
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
        self._exercise_live_checkpoint_continuation(driver, reader, warm, fixture_closed_epoch)

    def _exercise_live_checkpoint_continuation(self, driver: OwnedDriver,
            reader: WarmFixtureReader, warm: owner.WarmCurrentSavedFeederInputsV1,
            closed_epoch: Callable[[CurrentSavedBasisV1, BasisReaderV1], owner.ClosedEpochV1]) -> None:
        """Real SDK persistence and original cumulative SAVE producers, no native transport."""
        import base64
        import copy
        from contextlib import nullcontext
        from types import FunctionType, MethodType, ModuleType
        import zlib
        from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as gate
        root = self.fixture.root
        archive = record(parse_json((Path(__file__).parent / "test_data" /
            "current_saved_sem11373_postcheck_v1.json").read_bytes()))
        def original(name: str) -> bytes:
            item = record(record(archive["payloads"])[name])
            reference = parse_ref(item["source_ref"])
            encoded = item["encoded"]
            if type(encoded) is not str or not 0 < len(encoded) <= 131072:
                raise ValueError("bounded compressed original source")
            compressed = base64.b64decode(encoded, validate=True)
            decoder = zlib.decompressobj()
            raw = decoder.decompress(compressed, 1048577)
            if (len(raw) != reference.bytes or len(raw) > 1048576 or not decoder.eof
                    or decoder.unconsumed_tail or decoder.unused_data
                    or hashlib.sha256(raw).hexdigest() != reference.sha256):
                raise ValueError("exact original archived producer source")
            return raw
        def atomic_fixture(path: Path, value: object, *, replace: bool = False,
                limit: int = 65536) -> None:
            if not path.resolve().is_relative_to(root) or path.is_symlink():
                raise ValueError("contained original-producer fixture IO")
            raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            if len(raw) > limit:
                raise ValueError("bounded original-producer fixture IO")
            if path.exists() and not replace:
                raise FileExistsError(path)
            with path.open("r+b" if path.exists() else "xb") as stream:
                stream.seek(0); stream.write(raw); stream.truncate(); stream.flush(); os.fsync(stream.fileno())
            self.fixture.measure()
        cadence = ModuleType("_owned_original_checkpoint_cadence")
        cadence_tree = ast.parse(original("checkpoint_cadence"))
        cadence_nodes: list[ast.stmt] = [node for node in cadence_tree.body if
            isinstance(node, ast.FunctionDef) and node.name in {"checkpoint_saved", "_scope"}
            or isinstance(node, ast.Assign) and any(isinstance(target, ast.Name)
                and target.id == "STATE_KEY" for target in node.targets)]
        self.assertEqual(len(cadence_nodes), 3)
        exec(compile(ast.Module(body=cadence_nodes, type_ignores=[]),
            "<original checkpoint_saved and direct dependencies>", "exec"), vars(cadence))
        queue_tree = ast.parse(original("queue"))
        fresh = next(node for node in queue_tree.body if isinstance(node, ast.ClassDef) and node.name == "FreshQueue")
        selected: list[ast.stmt] = [node for node in fresh.body if isinstance(node, ast.FunctionDef)
            and node.name in {"checkpoint_lifecycle_matches", "finish_cumulative_checkpoint", "persist_loop_state"}]
        self.assertEqual(len(selected), 3)
        namespace: dict[str, object] = {"copy": copy, "Q": root / "p37-queue",
            "atomic": atomic_fixture, "checkpoint_saved": vars(cadence)["checkpoint_saved"],
            "_control_span_v1": lambda name: nullcontext()}
        exec(compile(ast.Module(body=selected, type_ignores=[]), "<original cumulative SAVE producers>", "exec"), namespace)
        class QueueFixture:
            halted: int | None = None
            next_sequence = warm.inputs.basis.next_sequence + 2
            launch = json_object(parse_json(reader.read(warm.warm_proof.sources.actual_game_ref, 65536)))
            _normal_cold: JsonObject = {"phase": "semantic", "admission": {"new_Game": launch}}
            full_loop_state = json_object(copy.deepcopy(warm.inputs.seed))
            governance_result_state: JsonValue = copy.deepcopy(warm.inputs.seed.get("governance_result_state"))
            lifestyle_pending_focus: JsonValue = None
            result_classifier_pin: JsonValue = None
            expected_lifecycle_binding = warm.inputs.checkpoint["succession_lifecycle"]
        queue = QueueFixture()
        for name, value in namespace.items():
            if name in {"checkpoint_lifecycle_matches", "finish_cumulative_checkpoint", "persist_loop_state"}:
                if not isinstance(value, FunctionType):
                    raise ValueError("original Queue producer must remain a Python function")
                setattr(queue, name, MethodType(value, queue))
        def invoke(name: str, *args: object) -> None:
            value: object = getattr(queue, name)
            if not isinstance(value, MethodType):
                raise ValueError("original bound Queue producer")
            result: object = value(*args)
            self.assertIsNone(result)
        self.fixture.write("ROOT-LAUNCH-CONFIG-C23-A15.json", {"cold_attempt": {
            "machine_id": MACHINE, "runtime_root": str(root), "attempt_nonce": "1" * 32,
            "task_nonce": "2" * 32}})
        pair = parse_json(reader.read(warm.warm_proof.sources.sdk_pair_ref, 65536))
        self.fixture.write("ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C23.json", pair)
        save_raw(self.fixture, "startup_readiness_v1.py", original("startup_readiness"))
        queue.full_loop_state["before"] = warm.warm_proof.opening.to_wire()
        calls = 0
        actual_loader = owner.load_current_saved_warm_inputs_v1
        def initial_loader(*, runtime_root: Path, expected_machine_id: str) -> owner.WarmCurrentSavedFeederInputsV1:
            nonlocal calls
            calls += 1
            return actual_loader(runtime_root=runtime_root, expected_machine_id=expected_machine_id)
        with patch.object(owner, "LocalBasisReaderV1", return_value=reader), \
                patch.object(owner, "_closed_epoch", new=closed_epoch), \
                patch.object(gate, "LocalBasisReaderV1", return_value=reader), \
                patch.object(gate, "load_current_saved_warm_inputs_v1", new=initial_loader):
            gate.bind_current_saved_request_epoch_v1(queue, runtime_root=root, expected_machine_id=MACHINE)
            queue._normal_cold["phase"] = "ready"
            first = gate.validate_current_saved_live_readiness_v1(queue=queue,
                runtime_root=root, expected_machine_id=MACHINE)
            self.assertEqual(first.phase, "initial_warm")
            invoke("persist_loop_state")
            unchanged = gate.validate_current_saved_live_readiness_v1(queue=queue,
                runtime_root=root, expected_machine_id=MACHINE)
            self.assertEqual(unchanged.phase, "same_epoch_continuation")
            saved_before = reader.stat(warm.inputs.basis.refs.save.path)
            new_bytes = b"owned synthetic SAVE materialization after five settled cycles"
            save_path = Path(warm.inputs.basis.refs.save.path)
            with save_path.open("wb") as stream:
                stream.write(new_bytes); stream.flush(); os.fsync(stream.fileno())
            saved_cp = {**warm.inputs.checkpoint, "status": "saved", "date_raw": warm.inputs.basis.frame.date_raw + 120,
                "size": len(new_bytes), "sha256": hashlib.sha256(new_bytes).hexdigest(), "history_index": 2}
            save_frame = {**warm.warm_proof.opening.to_wire(), "date_raw": saved_cp["date_raw"],
                "snapshot_id": "native:50", "revision": 51, "native_revision": 50}
            queue.full_loop_state.update(before=save_frame, completed_cycles=25,
                pending_checkpoint={"global_turn": 25, "semantic_response": str(root / "p37-responses/0110-1-result.json")})
            semantic = {"date_raw": saved_cp["date_raw"], "episode_character_id": saved_cp["episode_character_id"],
                "episode_run_id": saved_cp["episode_run_id"], "played_character": {"character_id": saved_cp["episode_character_id"]},
                "revision": 51, "succession_lifecycle": saved_cp["succession_lifecycle"]}
            self.fixture.write("p37-responses/0110-1-result.json", {"request": {"sequence": 110,
                "tool": "ck3_take_semantic_snapshot_private_v1", "arguments": {}},
                "result": {"is_error": False, "result_type": "complete", "structured_content": semantic}})
            save_response = self.fixture.write("p37-responses/0111-1-result.json", {"request": {"sequence": 111,
                "tool": "ck3_save_checkpoint", "arguments": {"expected_revision": 51}},
                "result": {"is_error": False, "result_type": "complete", "structured_content": {"checkpoint": saved_cp}}})
            queue.next_sequence = 112
            invoke("finish_cumulative_checkpoint", {"checkpoint": saved_cp}, Path(save_response.path))
            driver._last_checkpoint = record(saved_cp)
            driver._persist_driver_state(persistence_reason="fixture_actual_continuation_checkpoint")
            self.assertIsNone(driver._driver_state_error)
            self.assertNotEqual(reader.stat(str(save_path)), saved_before)
            second = gate.validate_current_saved_live_readiness_v1(queue=queue,
                runtime_root=root, expected_machine_id=MACHINE)
            self.assertEqual(second.phase, "same_epoch_continuation")
            self.assertEqual(second.checkpoint["sha256"], saved_cp["sha256"])
            self.assertEqual(calls, 1)
            with self.assertRaises(ValueError):
                owner.validate_current_saved_warm_inputs_v1(warm.inputs.basis,
                    basis_ref=warm.inputs.basis_ref, validation_ref=warm.inputs.validation_ref,
                    sources=warm.warm_proof.sources, reader=reader, runtime_root=root)
            current = {**save_frame, "date_raw": integer(saved_cp["date_raw"]) + 72,
                "actor_character_id": 3, "episode_run_id": "episode-3"}
            queue.full_loop_state.update(before=current, completed_cycles=28)
            driver._episode_character_id = 3; driver._episode_run_id = "episode-3"
            driver._persist_driver_state(persistence_reason="fixture_validated_successor_current_frame")
            invoke("persist_loop_state")
            self.assertEqual(gate.validate_current_saved_live_readiness_v1(queue=queue,
                runtime_root=root, expected_machine_id=MACHINE).phase, "same_epoch_continuation")
            original_identity = reader.identities[999]
            reader.identities[999] = {**original_identity, "creation_filetime": "134370000009999999"}
            with self.assertRaises(ValueError):
                gate.validate_current_saved_live_readiness_v1(queue=queue, runtime_root=root, expected_machine_id=MACHINE)
            reader.identities[999] = original_identity
            saved_row = parse_json(Path(save_response.path).read_bytes())
            atomic_fixture(Path(save_response.path), {"request": {"sequence": 111}, "client_error": "outcome unknown"}, replace=True)
            with self.assertRaises((ValueError, RuntimeError)):
                gate.validate_current_saved_live_readiness_v1(queue=queue, runtime_root=root, expected_machine_id=MACHINE)
            atomic_fixture(Path(save_response.path), saved_row, replace=True)
            driver._last_checkpoint = {**saved_cp, "sha256": "0" * 64}
            driver._persist_driver_state(persistence_reason="fixture_wrong_current_checkpoint")
            with self.assertRaises(ValueError):
                gate.validate_current_saved_live_readiness_v1(queue=queue, runtime_root=root, expected_machine_id=MACHINE)
            self.assertEqual(calls, 1)
        self.fixture.measure()


if __name__ == "__main__":
    unittest.main()


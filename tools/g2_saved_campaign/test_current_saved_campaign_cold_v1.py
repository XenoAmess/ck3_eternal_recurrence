"""Typed producer/JSON/consumer cold boundary and finite SDK persistence fixtures."""
from __future__ import annotations

import copy
import ast
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
import tempfile
from types import ModuleType
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from typing import Callable, Protocol, runtime_checkable

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, CurrentSavedBasisV1, ExactRefV1, JsonObject, JsonValue, SavedFrameV1,
    encode_current_saved_basis_v1, exact_read,
    original_response_evidence_v1, OriginalResponseReaderV1,
    parse_json, parse_ref, record, rows, json_object, json_value, integer, text, qualify_current_saved_basis_v1,
)
from tools.g2_saved_campaign import test_current_saved_basis_v1 as basis_fixture
from tools.g2_saved_campaign.test_current_saved_basis_v1 import (
    DiskReader, MACHINE, file_ref, pure_basis,
)
from tools.g2_saved_campaign import prepare_current_saved_campaign_cold_v1 as producer
from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as owner
from tools.g2_saved_campaign import current_saved_campaign_feeder_v1 as feeder
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
from tools.g2_saved_campaign import current_saved_continuity_v1 as continuity
from tools.g2_saved_campaign import test_current_saved_continuity_v1 as continuity_fixture
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
        (".", "presentation-c23", "creator-tools"), ref("full.json"), ref("steam.json"), ref("screen.json").path,
        ref("spec.json").path, "1" * 32, "2" * 32, "3" * 32,
        business_source_generation=31, sdk_base_ref=ref("sdk-base.json"),
        sdk_anchor_ref=ref("sdk-anchor.json"), native32_current_sdk_override=None,
        artifact_cap_bytes=1090519040, renderer_override_ref=None)


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
        for roots in ([".", "tools"], [".", "TOOLS"], [".", "./tools"], None, True, 1.0):
            bad = copy.deepcopy(item); bad["import_roots"] = json_value(roots)
            with self.subTest(roots=roots), self.assertRaises(ValueError):
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
            8, len(outputs), allocated, allocated + 1 + 131072, None, item.artifact_cap_bytes, renderer_override_ref=None)
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

        for roots in ([".", "tools"], [".", "TOOLS"], [".", "./tools"], None, True, 1.0):
            bad = quote.to_wire(); bad["import_roots"] = json_value(roots)
            with self.subTest(roots=roots), self.assertRaises(ValueError):
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
    config = {}
    _validate_a15_attempt(args, config)
    if any(name == "xar_autoplayer" or name.startswith("xar_autoplayer.") for name in sys.modules):
        raise ValueError("ambient project imports cannot select a different checkout")
    sys.path.insert(0, str(creator_source))
    from xar_autoplayer import environment, runtime
    if (Path(environment.__file__).resolve() != creator_source / "xar_autoplayer/environment.py"
            or Path(runtime.__file__).resolve() != creator_source / "xar_autoplayer/runtime.py"):
        raise ValueError("public prepare/launch imported a different project source")
    abort = threading.Event()
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
                if name == "governance.json":
                    converted = json_object(converted)
                    converted["governance_result_state"] = None
                    converted["pending_focus"] = None
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
            json_object(parse_json(fixture.reader.read(basis.refs.governance, 65536))),
            json_object(driver._last_checkpoint),
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



class SupervisorSdkGuardOrderingTests(unittest.TestCase):
    def test_emitted_main_preserves_ambient_and_origin_guards_before_authority(self)->None:
        import subprocess
        material=foreground_supervisor_material_v1()
        generated=producer.emit_supervisor_v1(material,machine_id=MACHINE).decode()
        child=r'''
import sys,json,types,importlib.util
from pathlib import Path
from importlib.abc import MetaPathFinder,Loader
class SDK(MetaPathFinder,Loader):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in ('xar_autoplayer','xar_autoplayer.environment','xar_autoplayer.runtime','root_checkpoint_bootstrap_c23'):
   return importlib.util.spec_from_loader(fullname,self,is_package=fullname=='xar_autoplayer')
 def create_module(self,spec):return None
 def exec_module(self,module):
  if module.__name__=='root_checkpoint_bootstrap_c23':
   module.api=lambda:__import__('xar_autoplayer',fromlist=['environment','runtime'])
  elif module.__name__=='xar_autoplayer':module.__path__=[]
  else:module.__file__=str(Path('/guarded/xar_autoplayer')/(module.__name__.split('.')[-1]+'.py'))
assert not any(n=='xar_autoplayer' or n.startswith('xar_autoplayer.') for n in sys.modules)
sys.meta_path.insert(0,SDK())
scope={'__name__':'_software_guard_fixture','__file__':'/fixture/supervisor.py'}
exec(compile(sys.stdin.read(),'<actual emitted fixture>','exec'),scope)
calls=[]
class StopBeforeKeeper(Exception):pass
def checked(*args,**kwargs):
 assert 'xar_autoplayer.environment' in sys.modules and 'xar_autoplayer.runtime' in sys.modules
 calls.append('checked')
def event():
 calls.append('stop');raise StopBeforeKeeper()
scope.update(creator_source=Path('/guarded').resolve(),N=Path('/fixture'),config={},sys=sys,
 threading=types.SimpleNamespace(Event=event),verify_current_saved_supervisor_attempt_v1=checked)
try:scope['main'](types.SimpleNamespace(attempt_nonce='a'*32,task_nonce='b'*32))
except StopBeforeKeeper:pass
assert calls==['checked','stop'],calls
print('ACTUAL_EMITTED_MAIN_GUARDS_THEN_AUTHORITY_PASS')
'''
        base:object=getattr(sys,"_base_executable",None)
        if not isinstance(base,str) or not Path(base).is_file():raise ValueError("actual base interpreter")
        result=subprocess.run([base,"-B","-c",child],input=generated,capture_output=True,text=True,
            cwd=Path(producer.__file__).resolve().parents[2],check=False)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("ACTUAL_EMITTED_MAIN_GUARDS_THEN_AUTHORITY_PASS",result.stdout)



class _ContinuityProbeMemoryReaderV1:
    def __init__(self, memory: continuity_fixture.MemoryReader) -> None:
        self.memory = memory

    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        document = self.memory.probe(reference.path, limit)
        if document is None or document.reference != reference:
            raise ValueError("exact in-memory continuity reference required")
        return document.payload

    def stat(self, path: str) -> FileStatIdentityV1:
        document = self.memory.probe(path, 65536)
        if document is None:
            raise FileNotFoundError(path)
        return document.identity


class ClosedContinuityPreparationTests(unittest.TestCase):
    def configured(self, *, exact_head: bool) -> tuple[
        producer.ColdPlanV1, continuity_fixture.MemoryReader, _ContinuityProbeMemoryReaderV1
    ]:
        memory, anchor, head = continuity_fixture.fixture()
        if exact_head:
            anchor = memory.put(continuity_fixture.ROOT / "closed228.json", head)
        original = pure_basis()
        count = integer(head["last_settled_cycles"])
        date = integer(head["last_settled_date_raw"])
        basis = replace(original,
            origin=replace(original.origin,
                start_date_raw=integer(head["start_date_raw"]),
                target_date_raw=integer(head["target_date_raw"]),
                target_days=integer(head["target_days"])),
            completed_cycles=count,
            refs=replace(original.refs, ledger=anchor),
            progress=replace(original.progress, ledger_cycles=count, ledger_date_raw=date,
                             settled_cycles=count, settled_date_raw=date))
        reference = memory.put(continuity_fixture.ROOT / "probe-basis.json", basis.to_wire())
        configured = replace(plan(), basis_ref=reference,
                             runtime_root=str(continuity_fixture.ROOT / "new-runtime"))
        return configured, memory, _ContinuityProbeMemoryReaderV1(memory)

    def test_prepared_gate_rejects_225_anchor_even_with_228_business_frontier(self) -> None:
        configured, memory, reader = self.configured(exact_head=False)
        before = dict(memory.documents)
        with self.assertRaisesRegex(ValueError, "closed basis still binds a stale continuity predecessor"):
            producer.probe_current_saved_continuity_v1(
                configured, reader=reader, continuity_reader=memory)
        self.assertEqual(memory.documents, before)

    def test_exact_head_binding_roundtrip_rechecks_actual_head(self) -> None:
        configured, memory, reader = self.configured(exact_head=True)
        before = dict(memory.documents)
        result = producer.probe_current_saved_continuity_v1(
            configured, reader=reader, continuity_reader=memory)
        view = continuity.validate_continuity_binding_v1(
            wire(result), expected_machine_id=MACHINE, reader=memory)
        self.assertTrue(view.ready)
        self.assertEqual(view.head_sequence, 228)
        self.assertEqual(view.anchor_sequence, 228)
        self.assertEqual(result["ledger_writes"], 0)
        self.assertEqual(memory.documents, before)
        changed = {**view.head_state, "sequence": 229}
        memory.put(continuity_fixture.CANONICAL, changed)
        with self.assertRaises(ValueError):
            continuity.validate_continuity_binding_v1(
                result, expected_machine_id=MACHINE, reader=memory)

    def test_recoverable_lag_does_not_publish_ready_or_repair_files(self) -> None:
        configured, memory, reader = self.configured(exact_head=False)
        memory.put(continuity_fixture.CANONICAL, continuity_fixture.state())
        before = dict(memory.documents)
        with self.assertRaisesRegex(ValueError, "metadata recovery required"):
            producer.probe_current_saved_continuity_v1(
                configured, reader=reader, continuity_reader=memory)
        self.assertEqual(memory.documents, before)


class SupervisorStandaloneSdkGuardTests(unittest.TestCase):
    def test_actual_sdk_fresh_child_reproduces_old_early_import_rejection(self) -> None:
        """Model material, real repo SDK and fresh BASE; stop before keeper authority."""
        from tools.g2_saved_campaign.owned_python_launch_v1 import owned_python_launch_v1
        generated = producer.emit_supervisor_v1(
            foreground_supervisor_material_v1(), machine_id=MACHINE).decode()
        program = r'''
import ast,json,sys,types
from pathlib import Path
payload=json.loads(sys.stdin.read())
repo=Path(payload["repo"]).resolve()
sdk=repo/"ck3_autonomous_player/src"
assert not any(n=="xar_autoplayer" or n.startswith("xar_autoplayer.") for n in sys.modules)
tree=ast.parse(payload["source"])
if payload["early"]:
 main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
 # Execute the old API's actual SDK import before the existing ambient guard.
 position=next(i for i,n in enumerate(main.body) if isinstance(n,ast.If)
               and any(isinstance(c,ast.Constant) and
                       c.value=="ambient project imports cannot select a different checkout"
                       for c in ast.walk(n)))
 main.body.insert(position,ast.ImportFrom(module="xar_autoplayer",
                  names=[ast.alias(name="environment"),ast.alias(name="runtime")],level=0))
ast.fix_missing_locations(tree)
scope={"__name__":"_standalone_guard_model","__file__":str(repo/"model-supervisor.py")}
exec(compile(tree,"<emitted model with real SDK>","exec"),scope)
calls=[]
class BeforeKeeper(Exception):pass
def checked(*args,**kwargs):
 for name in ("environment","runtime"):
  module=sys.modules["xar_autoplayer."+name]
  assert Path(module.__file__).resolve()==sdk/"xar_autoplayer"/(name+".py")
 calls.append("checked")
def stop():
 calls.append("stop")
 raise BeforeKeeper()
scope.update(creator_source=sdk.resolve(),N=repo/"model-no-write",config={},sys=sys,
 threading=types.SimpleNamespace(Event=stop),
 verify_current_saved_supervisor_attempt_v1=checked)
rejected=False
try:scope["main"](types.SimpleNamespace(attempt_nonce="a"*32,task_nonce="b"*32))
except BeforeKeeper:assert not payload["early"]
except ValueError as error:
 assert payload["early"] and str(error)=="ambient project imports cannot select a different checkout"
 rejected=True
assert calls==([] if payload["early"] else ["checked","stop"]),calls
assert rejected is payload["early"]
print(json.dumps({"early_rejected":rejected,"calls":calls,"sdk_source":str(sdk)}))
'''
        executable, env = owned_python_launch_v1()
        repo = Path(producer.__file__).resolve().parents[2]
        for early in (False, True):
            with self.subTest(old_early_import=early):
                result = subprocess.run([executable, "-B", "-X", "utf8", "-c", program],
                    input=json.dumps({"repo": str(repo), "source": generated, "early": early}),
                    env=env, cwd=repo, capture_output=True, text=True, timeout=20,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                observed = record(parse_json(result.stdout.encode()))
                self.assertIs(observed["early_rejected"], early)
                self.assertEqual(observed["calls"], [] if early else ["checked", "stop"])


class Native32CurrentSdkOverrideTests(unittest.TestCase):
    def enabled_plan(self) -> producer.ColdPlanV1:
        from tools.g2_saved_campaign.prepare_native32_current_sdk_binding_v1 import BINDING_NAME
        original = plan()
        override = producer.Native32CurrentSdkOverrideV1(
            ref("reviewed-reader.py"), ref("reviewed-extension.py"), ref("reviewed-binding.json"))
        return replace(original, business_source_generation=32,
            native32_current_sdk_override=override,
            closure_entry_paths=original.closure_entry_paths + (BINDING_NAME,))

    def test_required_null_and_source_bound_plan_roundtrip(self) -> None:
        plain = plan()
        self.assertIsNone(plain.to_wire()["native32_current_sdk_override"])
        self.assertEqual(producer.parse_plan_v1(wire(plain.to_wire())), plain)
        enabled = self.enabled_plan()
        self.assertEqual(producer.parse_plan_v1(wire(enabled.to_wire())), enabled)
        for altered in (
                {k: v for k, v in plain.to_wire().items() if k != "native32_current_sdk_override"},
                {**plain.to_wire(), "schema": "xar.current-saved-cold-plan/v1"},
                {**plain.to_wire(), "native32_current_sdk_override": {}},
                {**plain.to_wire(), "native32_current_sdk_override": False}):
            with self.subTest(wire=altered), self.assertRaises(ValueError):
                producer.parse_plan_v1(wire(altered))
        with self.assertRaises(ValueError):
            producer.parse_plan_v1(wire(replace(enabled, business_source_generation=31).to_wire()))

    def test_override_rejects_missing_null_wrong_typed_or_crossed_refs(self) -> None:
        override = self.enabled_plan().native32_current_sdk_override
        assert override is not None
        original = override.to_wire()
        for key in ("reader_ref", "extension_ref", "binding_ref"):
            wrong: list[object] = [None, True, [], {}, {**ref("bad").to_wire(), "bytes": True},
                     {**ref("bad").to_wire(), "bytes": 1.0}]
            for value in wrong:
                altered = dict(original); altered[key] = json_value(value)
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    producer.parse_native32_current_sdk_override_v1(wire(altered))
            missing = dict(original); del missing[key]
            with self.assertRaises(ValueError):
                producer.parse_native32_current_sdk_override_v1(wire(missing))
        crossed = {**original, "extension_ref": original["reader_ref"]}
        with self.assertRaises(ValueError):
            producer.parse_native32_current_sdk_override_v1(wire(crossed))

    def test_null_override_does_not_touch_ordinary_output_or_load_sources(self) -> None:
        output = {"ordinary.py": b"ordinary"}
        documents: dict[str, JsonObject] = {"ordinary.json": {"status": "unavailable"}}

        def unexpected(reference: ExactRefV1, limit: int) -> bytes:
            raise AssertionError("null optional binding must not load a source")

        producer.apply_native32_current_sdk_override_v1(
            plan(), output=output, documents=documents,
            historical_binding_ref=ref("old.json"), load=unexpected)
        self.assertEqual(output, {"ordinary.py": b"ordinary"})
        self.assertEqual(documents, {"ordinary.json": {"status": "unavailable"}})

    def test_quote_v4_pins_all_three_outputs_and_explicit_null(self) -> None:
        configured = self.enabled_plan()
        outputs = tuple(producer.OutputRowV1(producer.child_v1(ROOT, name), name,
            1, "a" * 64, "create-only", None) for name in configured.closure_entry_paths)
        allocated = len(outputs) * 4096
        quoted = producer.ColdQuoteV1(MACHINE, configured.observed_at_utc, ref("plan.json"),
            configured.basis_ref, configured.validation_ref, configured.producer_ref, ROOT,
            outputs, score_junction(), configured.canonical_entry_paths,
            configured.closure_entry_paths, configured.import_roots, 8, len(outputs),
            allocated, allocated + 1 + 131072, configured.native32_current_sdk_override, configured.artifact_cap_bytes, renderer_override_ref=None)
        self.assertEqual(producer.parse_quote_v1(wire(quoted.to_wire())), quoted)
        for value in ("xar.current-saved-cold-quote/v2", None):
            changed = quoted.to_wire(); changed["schema"] = value
            with self.assertRaises(ValueError):
                producer.parse_quote_v1(wire(changed))
        changed = quoted.to_wire(); del changed["native32_current_sdk_override"]
        with self.assertRaises(ValueError):
            producer.parse_quote_v1(wire(changed))
        changed = quoted.to_wire()
        override = record(changed["native32_current_sdk_override"])
        reader = record(override["reader_ref"]); reader["sha256"] = "b" * 64
        override["reader_ref"] = json_object(reader); changed["native32_current_sdk_override"] = json_object(override)
        with self.assertRaisesRegex(ValueError, "three Native32 override output pins"):
            producer.parse_quote_v1(wire(changed))

    def material(self) -> tuple[
        producer.ColdPlanV1, dict[str, bytes], dict[str, JsonObject], dict[str, bytes], ExactRefV1
    ]:
        from tools.g2_saved_campaign import prepare_native32_current_sdk_binding_v1 as native32
        from tools.g2_saved_campaign.test_native32_current_sdk_binding_v1 import portable_consumer_fixture_v1
        root = Path(producer.__file__).resolve().parents[2]
        frozen = root / "tools/g2_saved_campaign/candidates/native32_runtime_journal_adapter_20261021"
        configured = replace(plan(), business_source_generation=32)
        historical_raw = b"{}"
        historical_ref = producer.ref_for_bytes_v1(
            producer.child_v1(OLD, native32.HISTORICAL_BINDING_NAME), historical_raw)
        reader = (frozen / native32.READER_NAME).read_bytes()
        extension = (frozen / native32.EXTENSION_NAME).read_bytes()
        bundle = native32.compose_native32_current_sdk_binding_v1(
            reader, extension, historical_binding_ref=historical_ref,
            current_sdk_base_ref=configured.sdk_base_ref,
            current_sdk_anchor_ref=configured.sdk_anchor_ref, machine_id=MACHINE)
        fixture = portable_consumer_fixture_v1(bundle)
        refs = {name: producer.ref_for_bytes_v1(producer.child_v1(OLD, "reviewed/" + name), raw)
                for name, raw in bundle.files().items()}
        payloads = {refs[name].path: raw for name, raw in bundle.files().items()}
        payloads[historical_ref.path] = historical_raw
        configured = replace(configured,
            native32_current_sdk_override=producer.Native32CurrentSdkOverrideV1(
                refs[native32.READER_NAME], refs[native32.EXTENSION_NAME], refs[native32.BINDING_NAME]),
            closure_entry_paths=configured.closure_entry_paths + (native32.BINDING_NAME,))
        output = {producer.child_v1(ROOT, name): raw for name, raw in {
            native32.READER_NAME: reader, native32.EXTENSION_NAME: extension,
            native32.HISTORICAL_BINDING_NAME: historical_raw,
            "root_p37c23_mcp_entry.py": fixture.entry_bytes,
            "root_p37c23_sdk_queue.py": fixture.queue_bytes,
            "root_c23_canonical_outer.py": fixture.outer_bytes}.items()}
        native_path = producer.child_v1(ROOT, "ROOT-NATIVE30-NATIVE-PIN-C23-A15.json")
        documents: dict[str, JsonObject] = {native_path: {
            "native32_observer_binding": historical_ref.to_wire(),
            "source31_static_binding": {"kept": True}, "dll": "unchanged"}}
        return configured, output, documents, payloads, historical_ref

    def test_real_producer_applies_reviewed_bundle_and_reseals_output_pins(self) -> None:
        from tools.g2_saved_campaign import prepare_native32_current_sdk_binding_v1 as native32
        configured, output, documents, payloads, historical = self.material()
        original_documents = copy.deepcopy(documents)
        original_historical = output[producer.child_v1(ROOT, native32.HISTORICAL_BINDING_NAME)]

        def load(reference: ExactRefV1, limit: int) -> bytes:
            raw = payloads[reference.path]
            self.assertLessEqual(len(raw), limit)
            self.assertEqual(producer.ref_for_bytes_v1(reference.path, raw), reference)
            return raw

        producer.apply_native32_current_sdk_override_v1(configured,
            output=output, documents=documents, historical_binding_ref=historical, load=load)
        override = configured.native32_current_sdk_override
        assert override is not None
        for name, reference in ((native32.READER_NAME, override.reader_ref),
                                (native32.EXTENSION_NAME, override.extension_ref),
                                (native32.BINDING_NAME, override.binding_ref)):
            self.assertEqual(output[producer.child_v1(ROOT, name)], payloads[reference.path])
        native_path = producer.child_v1(ROOT, "ROOT-NATIVE30-NATIVE-PIN-C23-A15.json")
        current = dict(documents[native_path])
        binding_ref = parse_ref(current.pop("native32_current_sdk_binding"))
        self.assertEqual(current, original_documents[native_path])
        self.assertEqual(binding_ref, producer.ref_for_bytes_v1(
            producer.child_v1(ROOT, native32.BINDING_NAME), payloads[override.binding_ref.path]))
        self.assertEqual(output[producer.child_v1(ROOT, native32.HISTORICAL_BINDING_NAME)],
                         original_historical)
        self.assertEqual(len(configured.canonical_entry_paths), 8)
        self.assertNotEqual(output[producer.child_v1(ROOT, "root_c23_canonical_outer.py")],
                            self.material()[1][producer.child_v1(ROOT, "root_c23_canonical_outer.py")])

    def test_valid_ref_cannot_hide_unreviewed_bytes_or_wrong_binding_authority(self) -> None:
        from tools.g2_saved_campaign import prepare_native32_current_sdk_binding_v1 as native32
        for case in ("reader_body", "sdk_base", "historical_path", "binding_missing"):
            with self.subTest(case=case):
                configured, output, documents, payloads, historical = self.material()
                override = configured.native32_current_sdk_override
                assert override is not None
                changed = override
                if case == "reader_body":
                    raw = payloads[override.reader_ref.path] + b"\n"
                    reference = producer.ref_for_bytes_v1(override.reader_ref.path, raw)
                    payloads[reference.path] = raw
                    changed = replace(override, reader_ref=reference)
                else:
                    row = record(parse_json(payloads[override.binding_ref.path]))
                    if case == "sdk_base":
                        row["current_sdk_base_ref"] = configured.sdk_anchor_ref.to_wire()
                    elif case == "historical_path":
                        row["historical_binding_ref"] = {
                            **historical.to_wire(), "path": ref("same-hash-wrong-origin.json").path}
                    else:
                        del row["current_sdk_anchor_ref"]
                    raw = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
                    reference = producer.ref_for_bytes_v1(override.binding_ref.path, raw)
                    payloads[reference.path] = raw
                    changed = replace(override, binding_ref=reference)
                configured = replace(configured, native32_current_sdk_override=changed)
                before_output, before_documents = dict(output), copy.deepcopy(documents)

                def load(reference: ExactRefV1, limit: int) -> bytes:
                    raw = payloads[reference.path]
                    self.assertLessEqual(len(raw), limit)
                    self.assertEqual(producer.ref_for_bytes_v1(reference.path, raw), reference)
                    return raw

                with self.assertRaises(ValueError):
                    producer.apply_native32_current_sdk_override_v1(
                        configured, output=output, documents=documents,
                        historical_binding_ref=historical, load=load)
                self.assertEqual(output, before_output)
                self.assertEqual(documents, before_documents)




# Exact inherited N37 functions and constructor; software fixtures replace only
# their external resources. This is not Game/SDK/provider runtime qualification.
N37_CLOSURE_CONSUMER_SHA256_V1 = "cd13da5da23b3b9908b9cf2964ed17c6a999695e610636f40aefc48280f69b46"
N37_CLOSURE_CONSUMER_SOURCE_V1 = "def require(ok, why):\n    if not ok:\n        raise ValueError('C17 canonical outer binding denied: ' + why)\n\ndef checked(ref, limit=1048576):\n    path = Path(ref['path']).resolve(strict=True)\n    with path.open('rb') as stream:\n        raw = stream.read(limit + 1)\n    require(len(raw) <= limit and len(raw) == ref['bytes']\n        and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'frozen input changed: ' + str(path))\n    return json.loads(raw)\n\nclass OuterBindingV1:\n    def __init__(self, root):\n        self.root = Path(root).resolve(strict=True)\n        self.freeze = json.loads((self.root / 'ROOT-FINAL-SDK-FREEZE-P37C23-A15.json').read_bytes())\n        self.policy = checked(self.freeze['canonical_preload_policy'])\n        _check_c23_external_imports(self.root, self.policy)\n        require(self.freeze['machine_id'] == self.policy['machine_id'] == MACHINE\n            and self.policy['schema'] == 'xar.c23.canonical-preload-policy/v1'\n            and self.policy['generation'] == 'P37C23', 'source generation/machine differs')\n        self.sdk_root = Path(self.freeze['source_root']).resolve(strict=True)\n        require(self.sdk_root == Path(self.policy['sdk_source_root']).resolve(strict=True), 'immutable SDK root differs')\n        self.tools_root = Path(self.policy['creator_tools_root']).resolve(strict=True)\n        self.dependency_root = Path(self.policy['dependency_root']).resolve(strict=True)\n        self.direct_python = Path(self.policy['direct_python']['path']).resolve(strict=True)\n        checked_python = self.policy['direct_python']\n        with self.direct_python.open('rb') as stream:\n            raw = stream.read(16 * 1024**2 + 1)\n        require(len(raw) == checked_python['bytes'] and len(raw) <= 16 * 1024**2\n            and hashlib.sha256(raw).hexdigest() == checked_python['sha256'], 'direct Python source changed')\n        require(self.direct_python == Path(sys._base_executable).resolve(strict=True)\n            and Path(sys.executable).resolve(strict=True) == self.direct_python,\n            'the actual creator must already be the direct base Python image')\n        deps = checked(self.policy['dependency_sources'])\n        require(deps['machine_id'] == MACHINE and Path(deps['root']).resolve(strict=True) == self.dependency_root\n            and deps['mcp_version'] == '2.0.0', 'frozen dependency environment differs')\n        for ref in deps['files']:\n            path = Path(ref['path']).resolve(strict=True)\n            require(path.is_relative_to(self.dependency_root), 'dependency file escaped admitted root')\n            with path.open('rb') as stream:\n                raw = stream.read(1048577)\n            require(len(raw) <= 1048576 and len(raw) == ref['bytes']\n                and hashlib.sha256(raw).hexdigest() == ref['sha256'], 'dependency source changed')\n        site.addsitedir(str(self.dependency_root))\n        sys.path.insert(0, str(self.sdk_root))\n        sys.path.insert(0, str(self.tools_root))\n        self.result = self.io = self.control = self.factory = self.chain = self.plan = None\n        self.wal_enabled = self.policy.get('enable_driver_state_wal_v1', False)\n        require(type(self.wal_enabled) is bool, 'WAL policy requires an explicit boolean')\n        self.owner = self.server_thread = None\n        self.attempted = self.revoked = False\n        required = {'root_native30_supervisor_c23.py', 'root_checkpoint_bootstrap_c23.py',\n            'launch_sdk_p37c23_owner.py', 'root_p37c23_sdk_queue.py',\n            'root_p37c23_mcp_entry.py', 'root_c23_canonical_outer.py',\n            'observer_journal_runtime_v1.py','native32_mcp_extension_v1.py'}\n        require(required <= {Path(row[0]).name for row in self.policy['entry_source_pins']},\n            'all actual outer entry/helper sources must belong to the creator closure')\n\n\ndef _check_c23_external_imports(root, policy):\n    pins=policy.get('entry_source_pins')\n    require(isinstance(pins,(list,tuple)) and 0<len(pins)<=64, 'bounded complete source closure required')\n    paths=[]\n    for row in pins:\n        require(isinstance(row,(list,tuple)) and len(row)==2 and isinstance(row[0],str)\n            and Path(row[0]).is_absolute() and isinstance(row[1],str) and len(row[1])==64,\n            'exact complete source path/SHA required')\n        path=Path(row[0]).resolve(strict=True);paths.append(str(path))\n        with path.open('rb') as stream:raw=stream.read(1048577)\n        require(len(raw)<=1048576 and hashlib.sha256(raw).hexdigest()==row[1], 'complete source closure changed')\n    require(len(paths)==len(set(paths)), 'duplicate complete source path')\n    refs=policy.get('external_import_source_pins')\n    require(isinstance(refs,dict) and set(refs)==set(_C23_EXTERNAL_IMPORT_PINS), 'all frozen external algorithms must be explicitly pinned')\n    entries={str(Path(p).resolve(strict=True)):h for p,h in policy['entry_source_pins']}\n    for name,(size,digest) in _C23_EXTERNAL_IMPORT_PINS.items():\n        ref=refs[name];path=(root/(name+'.py')).resolve(strict=True)\n        require(Path(ref['path']).resolve(strict=True)==path and ref.get('bytes')==size\n            and ref.get('sha256')==digest and entries.get(str(path))==digest, 'external import pin differs: '+name)\n        with path.open('rb') as stream:raw=stream.read(1048577)\n        require(len(raw)==size and hashlib.sha256(raw).hexdigest()==digest, 'external algorithm changed: '+name)\n        module=sys.modules.get(name)\n        require(module is None or Path(module.__file__).resolve(strict=True)==path, 'foreign cached external algorithm: '+name)\n"
N37_EXTERNAL_NAMES_V1 = ('root_battle_epoch_credit', 'root_checkpoint_bootstrap_v2', 'root_committed_contact_credit', 'root_native22_supervisor', 'root_p37_checkpoint_bootstrap', 'root_p37_checkpoint_cadence', 'root_p37_clean_classifier_install', 'root_p37_halt_pending_watch', 'root_p37_known_owner_recovery', 'root_p37_known_pause_recovery_control', 'root_p37_loading_readiness', 'root_p37_pending_requests', 'root_p37_readonly_scope', 'root_p37_reinforcement_recovery', 'root_p37_robert_identity', 'root_prewar_v2_diagnostics', 'root_saved_campaign_preflight', 'root_zero_day_frontend', 'root_decision_text_api_c23', 'root_p37c23_overlay_relay', 'root_continuous_segment_auto_c23', 'root_p37c23_compact_decision_feed', 'p51_decision_text_shutdown_c23', 'decision_display_contract_v1', 'observer_journal_runtime_v1', 'native32_mcp_extension_v1')


class _ClosureSysV1:
    def __init__(self, image: Path) -> None:
        self.executable = self._base_executable = str(image)
        self.path: list[str] = []
        self.modules: dict[str, ModuleType] = {}


class _ClosureSiteV1:
    def __init__(self) -> None:
        self.added: list[str] = []

    def addsitedir(self, path: str) -> None:
        self.added.append(path)


@runtime_checkable
class _ClosureCheckV1(Protocol):
    def __call__(self, root: Path, policy: JsonObject) -> None: ...


@runtime_checkable
class _ClosureOuterV1(Protocol):
    root: Path
    attempted: bool
    revoked: bool


@runtime_checkable
class _ClosureConstructorV1(Protocol):
    def __call__(self, root: Path) -> _ClosureOuterV1: ...


class CurrentSavedCompleteClosureConsumerTests(unittest.TestCase):
    root: Path
    source_names: tuple[str, ...]
    image: Path
    peak_logical: int = 0
    peak_allocation_upper: int = 0

    @classmethod
    def setUpClass(cls) -> None:
        configured = os.environ.get("XAR_CURRENT_SAVED_CLOSURE_TEST_ROOT")
        if configured is None:
            raise ValueError("XAR_CURRENT_SAVED_CLOSURE_TEST_ROOT must explicitly name the owned fixture")
        cls.root = Path(configured)
        if not cls.root.is_absolute() or cls.root.exists() or cls.root.is_symlink():
            raise ValueError("closure fixture requires its explicit absent owned root")
        cls.root.mkdir()
        cls.root = cls.root.resolve(strict=True)
        cls.addClassCleanup(cls.cleanup_v1)
        names = sorted(set(producer.CANONICAL_NAMES) |
                       {name + ".py" for name in N37_EXTERNAL_NAMES_V1})
        names.extend(f"closure-extra-{i:02d}.py" for i in range(67 - len(names)))
        cls.source_names = tuple(names)
        for name in cls.source_names:
            (cls.root / name).write_bytes(b"")
        cls.image = cls.root / "python-fixture.exe"
        cls.image.write_bytes(b"software-fixture-not-executable")
        for name in ("sdk", "creator", "deps"):
            (cls.root / name).mkdir()
        cls.measure_v1()

    @classmethod
    def cleanup_v1(cls) -> None:
        if not cls.root.exists():
            return
        if cls.root.resolve(strict=True) != cls.root or cls.root.is_symlink():
            raise ValueError("fixture cleanup root identity changed")
        children = list(cls.root.iterdir())
        for child in children:
            if child.is_symlink() or getattr(child.lstat(), "st_file_attributes", 0) & 0x400:
                raise ValueError("fixture cleanup refuses reparse points")
            if child.is_dir():
                child.rmdir()
            else:
                child.unlink()
        cls.root.rmdir()
        if cls.root.exists():
            raise ValueError("fixture cleanup must finish ABSENT")

    @classmethod
    def measure_v1(cls) -> None:
        logical = 0
        upper = 0
        count = 1
        for path in cls.root.rglob("*"):
            count += 1
            if path.is_file():
                size = path.stat().st_size
                logical += size
                upper += ((size + 4095) // 4096) * 4096
        # Include per-entry metadata and directory headroom independently from
        # the native data allocation of zero-byte source fixtures.
        upper += count * 1024 + 16384
        cls.peak_logical = max(cls.peak_logical, logical)
        cls.peak_allocation_upper = max(cls.peak_allocation_upper, upper)
        if upper > 1048576:
            raise ValueError("closure consumer fixture exceeds its 1MiB quote")

    def policy_v1(self, count: int) -> JsonObject:
        digest = hashlib.sha256(b"").hexdigest()
        selected = list(self.source_names[:count])
        # Canonical and all 26 exact external refs must be included before extras.
        required = sorted(set(producer.CANONICAL_NAMES) |
                          {name + ".py" for name in N37_EXTERNAL_NAMES_V1})
        selected = required + [name for name in self.source_names if name not in required][:count-len(required)]
        entries: list[JsonValue] = [[str(self.root / name), digest] for name in selected]
        deps = {"machine_id": MACHINE, "root": str(self.root / "deps"),
                "mcp_version": "2.0.0", "files": []}
        deps_raw = producer.encode_v1(deps)
        deps_path = self.root / "dependencies.json"
        deps_path.write_bytes(deps_raw)
        image_raw = self.image.read_bytes()
        policy: JsonObject = {
            "schema": "xar.c23.canonical-preload-policy/v1",
            "generation": "P37C23", "machine_id": MACHINE,
            "entry_source_pins": entries,
            "external_import_source_pins": {
                name: {"path": str(self.root / (name + ".py")), "bytes": 0, "sha256": digest}
                for name in N37_EXTERNAL_NAMES_V1},
            "sdk_source_root": str(self.root / "sdk"),
            "creator_tools_root": str(self.root / "creator"),
            "dependency_root": str(self.root / "deps"),
            "direct_python": producer.ref_for_bytes_v1(str(self.image), image_raw).to_wire(),
            "dependency_sources": producer.ref_for_bytes_v1(str(deps_path), deps_raw).to_wire(),
            "enable_driver_state_wal_v1": False}
        self.persist_policy_v1(policy)
        return policy

    def persist_policy_v1(self, policy: JsonObject) -> None:
        raw = producer.encode_v1(policy)
        path = self.root / "policy.json"
        path.write_bytes(raw)
        freeze = {"machine_id": MACHINE, "source_root": str(self.root / "sdk"),
                  "canonical_preload_policy": producer.ref_for_bytes_v1(str(path), raw).to_wire()}
        (self.root / "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json").write_bytes(producer.encode_v1(freeze))
        self.measure_v1()

    def consumer_v1(self, raw: bytes) -> tuple[_ClosureConstructorV1, _ClosureCheckV1, _ClosureSysV1, _ClosureSiteV1]:
        fake_sys = _ClosureSysV1(self.image)
        fake_site = _ClosureSiteV1()
        digest = hashlib.sha256(b"").hexdigest()
        namespace: dict[str, object] = {
            "Path": Path, "json": json, "hashlib": hashlib, "MACHINE": MACHINE,
            "sys": fake_sys, "site": fake_site,
            "_C23_EXTERNAL_IMPORT_PINS": {name: (0, digest) for name in N37_EXTERNAL_NAMES_V1}}
        exec(compile(raw, "<exact N37 outer software consumer>", "exec"), namespace)
        constructor = namespace["OuterBindingV1"]
        check = namespace["_check_c23_external_imports"]
        if not isinstance(constructor, _ClosureConstructorV1) or not isinstance(check, _ClosureCheckV1):
            raise ValueError("exact inherited consumer definitions")
        return constructor, check, fake_sys, fake_site

    def test_original_constructor_rejects_new_null_and_enabled_closures(self) -> None:
        for count in (65, 66):
            with self.subTest(count=count):
                policy = self.policy_v1(count)
                constructor, check, _, _ = self.consumer_v1(N37_CLOSURE_CONSUMER_SOURCE_V1.encode())
                with self.assertRaisesRegex(ValueError, "bounded complete source closure"):
                    check(self.root, policy)
                with self.assertRaisesRegex(ValueError, "bounded complete source closure"):
                    constructor(self.root)

    def test_common_renderer_constructor_accepts_65_and_66_rejects_67(self) -> None:
        raw = producer.bind_current_saved_complete_closure_limit_v1(N37_CLOSURE_CONSUMER_SOURCE_V1.encode())
        for count in (65, 66, 67):
            with self.subTest(count=count):
                policy = self.policy_v1(count)
                constructor, check, fake_sys, fake_site = self.consumer_v1(raw)
                if count == 67:
                    with self.assertRaisesRegex(ValueError, "bounded complete source closure"):
                        check(self.root, policy)
                    with self.assertRaisesRegex(ValueError, "bounded complete source closure"):
                        constructor(self.root)
                else:
                    check(self.root, policy)
                    instance = constructor(self.root)
                    self.assertEqual(instance.root, self.root)
                    self.assertFalse(instance.attempted)
                    self.assertFalse(instance.revoked)
                    self.assertEqual(fake_site.added, [str(self.root / "deps")])
                    self.assertEqual(fake_sys.path, [str(self.root / "creator"), str(self.root / "sdk")])
        self.assertEqual(len(producer.CANONICAL_NAMES), 8)
        self.assertEqual(producer.MAX_CURRENT_SAVED_CLOSURE_V1, 66)

    def test_real_source_external_cached_origin_and_canonical_guards_remain(self) -> None:
        raw = producer.bind_current_saved_complete_closure_limit_v1(N37_CLOSURE_CONSUMER_SOURCE_V1.encode())
        policy = self.policy_v1(65)
        constructor, check, fake_sys, _ = self.consumer_v1(raw)
        changed = copy.deepcopy(policy)
        entries = rows(changed["entry_source_pins"])
        entries[0] = [rows(entries[0])[0], "0" * 64]
        changed["entry_source_pins"] = json_value(entries)
        self.persist_policy_v1(changed)
        with self.assertRaisesRegex(ValueError, "complete source closure changed"):
            constructor(self.root)
        changed = copy.deepcopy(policy)
        external = record(changed["external_import_source_pins"])
        item = record(external[N37_EXTERNAL_NAMES_V1[0]])
        item["bytes"] = 1
        external[N37_EXTERNAL_NAMES_V1[0]] = item
        changed["external_import_source_pins"] = json_value(external)
        self.persist_policy_v1(changed)
        with self.assertRaisesRegex(ValueError, "external import pin differs"):
            constructor(self.root)
        self.persist_policy_v1(policy)
        foreign = ModuleType(N37_EXTERNAL_NAMES_V1[0])
        foreign.__file__ = str(self.image)
        fake_sys.modules[N37_EXTERNAL_NAMES_V1[0]] = foreign
        with self.assertRaisesRegex(ValueError, "foreign cached external algorithm"):
            check(self.root, policy)
        fake_sys.modules.clear()
        changed = copy.deepcopy(policy)
        entries = rows(changed["entry_source_pins"])
        entries = [item for item in entries if Path(text(rows(item)[0])).name != "launch_sdk_p37c23_owner.py"]
        changed["entry_source_pins"] = json_value(entries)
        self.persist_policy_v1(changed)
        with self.assertRaisesRegex(ValueError, "all actual outer entry/helper sources"):
            constructor(self.root)


    def test_nonnull_renderer_reaches_inherited_constructor_and_final_source_checks(self) -> None:
        policy = self.policy_v1(66)
        reference, payload = CurrentSavedRendererOverrideTests().renderer()
        configured = replace(plan(), runtime_root=str(self.root), renderer_override_ref=reference)
        stub = b"# fixture\n"
        stub_digest = hashlib.sha256(stub).hexdigest()
        old_pins = {name: (len(stub), stub_digest) for name in N37_EXTERNAL_NAMES_V1}
        outer = ("_C23_EXTERNAL_IMPORT_PINS = " + repr(old_pins) + "\n" +
                 N37_CLOSURE_CONSUMER_SOURCE_V1).encode()
        outer = producer.bind_current_saved_complete_closure_limit_v1(outer)
        output = {producer.child_v1(str(self.root), name): stub
                  for name in producer.CURRENT_SAVED_RENDERER_PATHS_V1}
        outer_path = producer.child_v1(str(self.root), "root_c23_canonical_outer.py")
        output[outer_path] = outer
        original = dict(output)
        producer.apply_current_saved_renderer_override_v1(configured, output=output,
                                                         load=lambda ref, limit: payload)
        from tools.g2_saved_campaign.prepare_native32_current_sdk_binding_v1 import _outer_external_table_v1
        _, external = _outer_external_table_v1(output[outer_path])
        self.assertEqual(len(external), 26)
        self.assertEqual({k: v for k, v in external.items() if k != "decision_display_contract_v1"},
                         {k: v for k, v in old_pins.items() if k != "decision_display_contract_v1"})
        for name in producer.CURRENT_SAVED_RENDERER_PATHS_V1:
            self.assertEqual(output[producer.child_v1(str(self.root), name)], payload)
        contract_path = self.root / "decision_display_contract_v1.py"
        try:
            for name in N37_EXTERNAL_NAMES_V1:
                (self.root / (name + ".py")).write_bytes(stub)
            contract_path.write_bytes(payload)
            pins = record(policy["external_import_source_pins"])
            for name in N37_EXTERNAL_NAMES_V1:
                path = self.root / (name + ".py")
                pins[name] = producer.ref_for_bytes_v1(str(path), path.read_bytes()).to_wire()
            pins["decision_display_contract_v1"] = producer.ref_for_bytes_v1(str(contract_path), payload).to_wire()
            policy["external_import_source_pins"] = json_value(pins)
            entries = rows(policy["entry_source_pins"])
            policy["entry_source_pins"] = json_value([
                [rows(item)[0], hashlib.sha256(payload).hexdigest()]
                if Path(text(rows(item)[0])) == contract_path else
                [rows(item)[0], stub_digest] if Path(text(rows(item)[0])).stem in N37_EXTERNAL_NAMES_V1
                else item for item in entries])
            self.persist_policy_v1(policy)
            self.assertEqual(len(rows(policy["entry_source_pins"])), 66)
            self.assertEqual(len(producer.CANONICAL_NAMES), 8)
            constructor, check, fake_sys, _ = self.consumer_v1(output[outer_path])
            self.assertEqual(constructor(self.root).root, self.root)
            foreign = ModuleType("decision_display_contract_v1")
            foreign.__file__ = str(self.image)
            fake_sys.modules["decision_display_contract_v1"] = foreign
            with self.assertRaisesRegex(ValueError, "foreign cached external algorithm"):
                check(self.root, policy)
            fake_sys.modules.clear()
            contract_path.write_bytes(b"changed")
            with self.assertRaises(ValueError):
                constructor(self.root)
            unchanged = dict(original)
            producer.apply_current_saved_renderer_override_v1(replace(configured, renderer_override_ref=None),
                output=unchanged, load=lambda ref, limit: self.fail("null must not load"))
            self.assertEqual(unchanged, original)
        finally:
            for name in N37_EXTERNAL_NAMES_V1:
                (self.root / (name + ".py")).write_bytes(b"")

    def test_real_compose_reader_explicit_response_capability_keeps_source_cap(self) -> None:
        source = Path(producer.__file__).read_text("utf-8")
        tree = ast.parse(source)
        compose = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compose_v1")
        readers = [node for node in ast.walk(compose) if isinstance(node, ast.ClassDef) and node.name == "ComposeReaderV1"]
        self.assertEqual(len(readers), 1)
        payload = producer.encode_v1({"padding": "x" * 1154000, "ok": False})
        reference = producer.ref_for_bytes_v1(str(self.root / "original-response.json"), payload)
        calls: list[tuple[ExactRefV1, int]] = []
        load_calls: list[ExactRefV1] = []

        class ResponseLocalReader(owner.LocalBasisReaderV1):
            def read(self, ref: ExactRefV1, limit: int) -> bytes:
                calls.append((ref, limit))
                if (ref.path, ref.bytes) != (reference.path, reference.bytes):
                    raise ValueError("unexpected response reference")
                return payload

        def load(ref: ExactRefV1, limit: int) -> bytes:
            load_calls.append(ref)
            if ref.bytes > limit or limit > producer.MAX_FILE:
                raise ValueError("small bounded RAM input")
            return payload

        namespace: dict[str, object] = {
            "ExactRefV1": ExactRefV1, "FileStatIdentityV1": FileStatIdentityV1,
            "LocalBasisReaderV1": ResponseLocalReader, "load": load}
        exec(compile(ast.Module(body=[readers[0]], type_ignores=[]), "<actual nested ComposeReaderV1>", "exec"), namespace)
        constructor = namespace["ComposeReaderV1"]
        if not callable(constructor):
            raise ValueError("actual ComposeReaderV1 constructor")
        reader = constructor()
        if not isinstance(reader, OriginalResponseReaderV1):
            raise ValueError("actual reader exposes its explicit response capability")
        value = original_response_evidence_v1(reader, reference)
        self.assertEqual(value, {"padding": "x" * 1154000, "ok": False})
        self.assertEqual(calls, [(reference, 2097152)])
        self.assertEqual(load_calls, [])
        with self.assertRaisesRegex(ValueError, "small bounded RAM input"):
            reader.read(reference, producer.MAX_FILE)
        for wrong in (replace(reference, bytes=2097153), replace(reference, sha256="0" * 64)):
            with self.subTest(wrong=wrong), self.assertRaises(ValueError):
                original_response_evidence_v1(reader, wrong)
        with self.assertRaises(ValueError):
            reader.read_response(reference, True)
        self.assertEqual(producer.MAX_FILE, 1048576)

    def test_renderer_changes_only_exact_common_guard_and_refuses_drift(self) -> None:
        before = N37_CLOSURE_CONSUMER_SOURCE_V1.encode()
        after = producer.bind_current_saved_complete_closure_limit_v1(before)
        self.assertEqual(after.replace(b"0<len(pins)<=66", b"0<len(pins)<=64"), before)
        for value in (before.replace(b"0<len(pins)<=64", b"0<len(pins)<=65"),
                      before + before, b"def other(): pass\n"):
            with self.subTest(source_bytes=len(value)), self.assertRaises(ValueError):
                producer.bind_current_saved_complete_closure_limit_v1(value)
        tree = ast.parse(Path(producer.__file__).read_text("utf-8"))
        compose = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "compose_v1")
        calls = [node for node in compose.body if isinstance(node, ast.Expr)
                 and isinstance(node.value, ast.Call)
                 and isinstance(node.value.func, ast.Name) and node.value.func.id == "put"
                 and node.value.args and isinstance(node.value.args[0], ast.Constant)
                 and node.value.args[0].value == "root_c23_canonical_outer.py"]
        self.assertTrue(any(any(isinstance(part, ast.Call) and isinstance(part.func, ast.Name)
                         and part.func.id == "bind_current_saved_complete_closure_limit_v1"
                         for part in ast.walk(node)) for node in calls),
                        "the actual common compose path binds both nullable override branches")



# Original A20 launcher 6010/56beed721106281e0b37a81cf9d150c27aa7ce9cb531e799d7da00184a5aa537.
# Only its actual argv assignment is projected; no owner or process is launched.
ARTIFACT_CAP_ORIGINAL_ARGV_V1 = "argv=[str(TOOLS_PYTHON),'-B','-X','utf8',str(N/'root_p37c23_sdk_queue.py'),\n      '--environment-manifest',str(N/'state/profile/xar-autoplayer-environment.json'),\n      '--recording-job-root',requested['receipt_root'],\n      '--first-frame-admission',str(recording['first_path']),\n      '--artifact-cap-bytes','2147483648','--continuous']"


@runtime_checkable
class _ArtifactArgvMainV1(Protocol):
    def __call__(self) -> object: ...


class CurrentSavedArtifactBudgetTests(unittest.TestCase):
    def _quote(self, item: producer.ColdPlanV1, reference: ExactRefV1) -> producer.ColdQuoteV1:
        outputs = tuple(producer.OutputRowV1(producer.child_v1(ROOT, name), name,
            1, "a" * 64, "create-only", None) for name in item.closure_entry_paths)
        allocated = len(outputs) * 4096
        return producer.ColdQuoteV1(item.machine_id, item.observed_at_utc, reference,
            item.basis_ref, item.validation_ref, item.producer_ref, ROOT, outputs,
            score_junction(), item.canonical_entry_paths, item.closure_entry_paths,
            item.import_roots, 8, len(outputs), allocated, allocated + 1 + 131072,
            item.native32_current_sdk_override, item.artifact_cap_bytes, renderer_override_ref=None)

    def _material(self) -> bytes:
        from textwrap import indent
        return ("from pathlib import Path\ndef verify_prepared_inputs(): return {}\n"
            "def main():\n" + indent(ARTIFACT_CAP_ORIGINAL_ARGV_V1, "    ") +
            "\n    return argv\n").encode()

    def _argv(self, source: bytes) -> tuple[str, ...]:
        main = next(node for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef) and node.name == "main")
        scope: dict[str, object] = {"TOOLS_PYTHON": Path("D:/model/python.exe"),
            "N": Path("D:/model/runtime"), "requested": {"receipt_root": "D:/model/recording"},
            "recording": {"first_path": "D:/model/first.json"}}
        exec(compile(ast.Module(body=[main], type_ignores=[]), "<actual launcher argv>", "exec"), scope)
        function = scope.get("main")
        if not isinstance(function, _ArtifactArgvMainV1):
            raise TypeError("actual generated main must be callable")
        return tuple(text(value) for value in rows(function()))

    def test_required_budget_json_types_boundaries_and_old_wire_rejected(self) -> None:
        for cap in (128 * 1024**2, 1090519040, 16 * 1024**3):
            configured = replace(plan(), artifact_cap_bytes=cap)
            quoted = self._quote(configured, ref("plan.json"))
            self.assertEqual(producer.parse_plan_v1(wire(configured.to_wire())), configured)
            self.assertEqual(producer.parse_quote_v1(wire(quoted.to_wire())), quoted)
            self.assertEqual(configured.to_wire()["artifact_cap_bytes"], cap)
            self.assertEqual(quoted.to_wire()["artifact_cap_bytes"], cap)
        original = plan()
        parsers: tuple[tuple[JsonObject, Callable[[object], object]], ...] = (
            (original.to_wire(), producer.parse_plan_v1),
            (self._quote(original, ref("plan.json")).to_wire(), producer.parse_quote_v1))
        wrong: tuple[object, ...] = (None, True, False, 1090519040.0, "1090519040",
                                    128 * 1024**2 - 1, 16 * 1024**3 + 1)
        for row, parse in parsers:
            missing = dict(row); del missing["artifact_cap_bytes"]
            with self.assertRaises(ValueError):
                parse(wire(missing))
            for value in wrong:
                changed = {**row, "artifact_cap_bytes": json_value(value)}
                with self.subTest(value=value), self.assertRaises(ValueError):
                    parse(wire(changed))
                with self.assertRaises(ValueError):
                    producer.artifact_cap_bytes_v1(value)
        for schema in ("xar.current-saved-cold-plan/v1", "xar.current-saved-cold-plan/v2"):
            with self.assertRaises(ValueError):
                producer.parse_plan_v1(wire({**original.to_wire(), "schema": schema}))
        for schema in ("xar.current-saved-cold-quote/v1", "xar.current-saved-cold-quote/v2",
                       "xar.current-saved-cold-quote/v3"):
            with self.assertRaises(ValueError):
                producer.parse_quote_v1(wire({**parsers[1][0], "schema": schema}))

    def test_actual_launcher_argv_uses_plan_quote_budget_without_other_changes(self) -> None:
        configured = producer.parse_plan_v1(wire(plan().to_wire()))
        quoted = producer.parse_quote_v1(wire(self._quote(configured, ref("plan.json")).to_wire()))
        original = self._argv(self._material())
        current = self._argv(producer.emit_current_saved_sdk_launcher_v1(
            self._material(), artifact_cap_bytes=quoted.artifact_cap_bytes))
        index = original.index("--artifact-cap-bytes") + 1
        self.assertEqual(original[index], "2147483648")
        self.assertEqual(current[index], str(configured.artifact_cap_bytes))
        self.assertEqual(current[:index] + current[index+1:], original[:index] + original[index+1:])
        for material in (self._material().replace(b"'--artifact-cap-bytes'", b"'--unknown-budget'"),
                         self._material().replace(b"'2147483648'", b"'2147483647'"),
                         self._material().replace(b"'--continuous'",
                             b"'--artifact-cap-bytes','2147483648','--continuous'")):
            with self.assertRaises(ValueError):
                producer.emit_current_saved_sdk_launcher_v1(material,
                    artifact_cap_bytes=configured.artifact_cap_bytes)

    def test_real_preflight_refuses_plan_quote_budget_mismatch_before_owner(self) -> None:
        from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as core
        configured = replace(plan(), machine_id=core.current_execution_machine_id_v1())
        reader = continuity_fixture.MemoryReader()
        plan_ref = reader.put(Path(ref("artifact-plan.json").path), configured.to_wire())
        quoted = self._quote(configured, plan_ref)
        class StopAfterBudgetBinding(Exception):
            pass
        for cap, accepted in ((configured.artifact_cap_bytes, True),
                              (configured.artifact_cap_bytes + 1, False)):
            quote_ref = reader.put(Path(ref("artifact-quote.json").path),
                                  replace(quoted, artifact_cap_bytes=cap).to_wire())
            with patch.object(core, "validate_current_saved_cold_owner_v1",
                              side_effect=StopAfterBudgetBinding) as boundary:
                exception = StopAfterBudgetBinding if accepted else ValueError
                with self.assertRaises(exception):
                    core.preflight_current_saved_campaign_v1(plan_ref, quote_ref,
                        replay_ref=ref("unread-replay.json"), consumer_probe_ref=ref("unread-probe.json"),
                        expected_machine_id=configured.machine_id, expected_runtime_root=Path(ROOT),
                        expected_attempt_nonce=configured.attempt_nonce, expected_task_nonce=configured.task_nonce,
                        reader=reader)
                self.assertEqual(boundary.call_count, int(accepted))



class CurrentSavedRendererOverrideTests(unittest.TestCase):
    def renderer(self) -> tuple[ExactRefV1, bytes]:
        path = Path(__file__).with_name("decision_display_contract_v1.py")
        raw = path.read_bytes()
        reference = producer.ref_for_bytes_v1(producer.child_v1(OLD, "reviewed-renderer.py"), raw)
        return reference, raw

    def material(self) -> tuple[producer.ColdPlanV1, dict[str, bytes], bytes]:
        reference, raw = self.renderer()
        configured = replace(plan(), renderer_override_ref=reference)
        old = b"# original qualified rich renderer\n"
        pins = {"decision_display_contract_v1": (len(old), hashlib.sha256(old).hexdigest()),
                **{"retained_"+str(i): (1, "a"*64) for i in range(25)}}
        outer = ("_C23_EXTERNAL_IMPORT_PINS = " + repr(pins) + "\n").encode()
        output = {producer.child_v1(ROOT, name): old for name in producer.CURRENT_SAVED_RENDERER_PATHS_V1}
        output[producer.child_v1(ROOT, "root_c23_canonical_outer.py")] = outer
        return configured, output, raw

    def test_qualified_registry_and_required_nullable_plan(self) -> None:
        registry = ast.parse(Path(__file__).with_name("prepare_rich_decision_graph_v1.py").read_bytes())
        assignments = [node for node in registry.body if isinstance(node, ast.Assign)
                       and any(isinstance(key, ast.Name) and key.id == "QUALIFIED" for key in node.targets)]
        self.assertEqual(len(assignments), 1)
        registry_value = assignments[0].value
        if not isinstance(registry_value, ast.Call) or len(registry_value.args) != 1 or not isinstance(registry_value.args[0], ast.Dict):
            raise ValueError("actual unique qualified registry")
        table = registry_value.args[0]
        pins = [item for key, item in zip(table.keys, table.values, strict=True)
                if isinstance(key, ast.Name) and key.id == "CONTRACT"]
        self.assertEqual(len(pins), 1)
        actual_pin: object = ast.literal_eval(pins[0])
        reference, _ = self.renderer()
        self.assertEqual(producer.CURRENT_SAVED_RENDERER_PIN_V1, actual_pin)
        plain = plan()
        self.assertIsNone(plain.to_wire()["renderer_override_ref"])
        self.assertEqual(producer.parse_plan_v1(wire(plain.to_wire())), plain)
        enabled = replace(plain, renderer_override_ref=reference)
        self.assertEqual(producer.parse_plan_v1(wire(enabled.to_wire())), enabled)
        bad_values: tuple[object, ...] = (False, {}, [], reference.path,
            {**reference.to_wire(), "bytes": True}, {**reference.to_wire(), "bytes": 21038.0},
            {**reference.to_wire(), "sha256": "a"*64})
        for bad in bad_values:
            value = plain.to_wire(); value["renderer_override_ref"] = json_value(bad)
            with self.subTest(value=bad), self.assertRaises(ValueError):
                producer.parse_plan_v1(wire(value))
        value = plain.to_wire(); del value["renderer_override_ref"]
        with self.assertRaises(ValueError):
            producer.parse_plan_v1(wire(value))
        with self.assertRaises(ValueError):
            producer.parse_plan_v1(wire({**plain.to_wire(), "schema": "xar.current-saved-cold-plan/v3"}))

    def test_actual_intake_double_body_and_only_one_outer_tuple(self) -> None:
        from tools.g2_saved_campaign.prepare_native32_current_sdk_binding_v1 import _outer_external_table_v1
        configured, output, raw = self.material()
        before = dict(output)
        outer_path = producer.child_v1(ROOT, "root_c23_canonical_outer.py")
        _, old_pins = _outer_external_table_v1(output[outer_path])
        def load(reference: ExactRefV1, limit: int) -> bytes:
            self.assertEqual(reference, configured.renderer_override_ref)
            self.assertEqual(limit, 65536)
            return raw
        producer.apply_current_saved_renderer_override_v1(configured, output=output, load=load)
        for name in producer.CURRENT_SAVED_RENDERER_PATHS_V1:
            self.assertEqual(output[producer.child_v1(ROOT, name)], raw)
        _, new_pins = _outer_external_table_v1(output[outer_path])
        self.assertEqual(len(new_pins), 26)
        self.assertEqual([name for name in old_pins if old_pins[name] != new_pins[name]],
                         ["decision_display_contract_v1"])
        self.assertEqual(set(output), set(before))

    def test_null_preserves_all_old_bytes_without_loading(self) -> None:
        _, output, _ = self.material(); before = dict(output)
        def forbidden(reference: ExactRefV1, limit: int) -> bytes:
            raise AssertionError("null renderer must not load current source")
        producer.apply_current_saved_renderer_override_v1(plan(), output=output, load=forbidden)
        self.assertEqual(output, before)

    def test_bad_old_body_pin_or_new_body_fail_before_mutation(self) -> None:
        for mode in ("different_old_body", "wrong_outer_pin", "wrong_new_body"):
            configured, output, raw = self.material()
            if mode == "different_old_body":
                output[producer.child_v1(ROOT, producer.CURRENT_SAVED_RENDERER_PATHS_V1[1])] += b"changed"
            if mode == "wrong_outer_pin":
                path = producer.child_v1(ROOT, "root_c23_canonical_outer.py")
                output[path] = output[path].replace(hashlib.sha256(
                    output[producer.child_v1(ROOT, producer.CURRENT_SAVED_RENDERER_PATHS_V1[0])]).hexdigest().encode(), b"b"*64)
            before = dict(output)
            def load(reference: ExactRefV1, limit: int) -> bytes:
                return raw + b"x" if mode == "wrong_new_body" else raw
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                producer.apply_current_saved_renderer_override_v1(configured, output=output, load=load)
            self.assertEqual(output, before)

    def test_quote_v5_binds_both_outputs_and_required_renderer_ref(self) -> None:
        reference, _ = self.renderer()
        configured = replace(plan(), renderer_override_ref=reference)
        quoted = CurrentSavedArtifactBudgetTests()._quote(configured, ref("renderer-plan.json"))
        files = list(quoted.files)
        for name in producer.CURRENT_SAVED_RENDERER_PATHS_V1:
            files.append(producer.OutputRowV1(producer.child_v1(ROOT, name), name,
                reference.bytes, reference.sha256, "create-only", None))
        allocated = sum(producer.allocation_v1(item.bytes) for item in files)
        quoted = replace(quoted, files=tuple(files), renderer_override_ref=reference,
            logical_bytes=sum(item.bytes for item in files), allocation_upper=allocated,
            prepare_peak_upper=allocated+max(item.bytes for item in files)+131072)
        self.assertEqual(producer.parse_quote_v1(wire(quoted.to_wire())), quoted)
        value = quoted.to_wire(); del value["renderer_override_ref"]
        with self.assertRaises(ValueError):
            producer.parse_quote_v1(wire(value))
        wrong = [replace(item, sha256="a"*64) if item.relative_path ==
                 producer.CURRENT_SAVED_RENDERER_PATHS_V1[1] else item for item in files]
        with self.assertRaises(ValueError):
            producer.parse_quote_v1(wire(replace(quoted, files=tuple(wrong)).to_wire()))
        with self.assertRaises(ValueError):
            producer.parse_quote_v1(wire({**quoted.to_wire(), "schema": "xar.current-saved-cold-quote/v4"}))


if __name__ == "__main__":
    unittest.main()


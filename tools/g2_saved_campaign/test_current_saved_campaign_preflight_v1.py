"""Portable historical startup/dispatch regression; no Game or native RPC."""
from __future__ import annotations
import ast
import asyncio
import base64
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
import copy
import ctypes
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import traceback
import textwrap
from types import FrameType, FunctionType, ModuleType
from typing import Literal, Protocol, runtime_checkable
import unittest
import zlib

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisRefsV1, CampaignOriginV1, CurrentSavedBasisV1, ExactRefV1, JsonObject,
    JsonValue, ProgressReconciliationV1, digest, integer, json_object, json_value,
    need, parse_frame, parse_json, parse_ref, record, rows, text,
)
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as core
from tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1 import (
    CANONICAL_NAMES, ColdPlanV1, ColdQuoteV1, OutputRowV1, SourceRowV1,
    emit_current_saved_request_guards_v1,
)
from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
    CampaignScoreJunctionV1, LocalBasisReaderV1, campaign_score_directory_identity_v1,
    parse_campaign_score_junction_v1, validate_campaign_score_junction_source_v1,
    project_current_saved_governance_resume_v1,
    load_current_saved_inputs_v1, cold_inputs_v1,
)

from tools.g2_saved_campaign import current_saved_campaign_replay_v1 as replay
from tools.g2_saved_campaign.current_saved_campaign_replay_v1 import (
    CURRENT_SEQUENCE as CURRENT_SEQUENCE,
    DATA as DATA,
    FIRST_SEQUENCE as FIRST_SEQUENCE,
    REPO as REPO,
    SUBJECT as SUBJECT,
    _Corpus as _Corpus,
    _Harness as _Harness,
    _N28_RESPONSE_SOURCE as _N28_RESPONSE_SOURCE,
    _RecordedResult as _RecordedResult,
    _RecordedTransport as _RecordedTransport,
    _dispatch_actual_cap as _dispatch_actual_cap,
    _fixture_parent as _fixture_parent,
    _invoke as _invoke,
    _isolated_modules as _isolated_modules,
    _make_harness as _make_harness,
    _module as _module,
    _namespace as _namespace,
    _owned_workspace as _owned_workspace,
    _phase_value as _phase_value,
    _pin as _pin,
    _remove_owned_child as _remove_owned_child,
    _selected_source as _selected_source,
    _wire as _wire,
    run_historical_startup_dispatch_replay_v1 as run_historical_startup_dispatch_replay_v1,
    HistoricalReplaySdkSourcesV1,
)

def _test_sdk_sources() -> HistoricalReplaySdkSourcesV1:
    return HistoricalReplaySdkSourcesV1(
        sdk_result_contract=_pin(REPO / "ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_tool_result_contract_v1.py"),
        sdk_score_cadence=_pin(REPO / "ck3_autonomous_player/src/xar_autoplayer/campaign_score_cadence_v1.py"),
        sdk_score_model=_pin(REPO / "ck3_autonomous_player/src/xar_autoplayer/campaign_development_score_v1.py"))

def _load_corpus() -> _Corpus:
    return replay._load_corpus(historical_fixture_ref=_pin(DATA), sdk_sources=_test_sdk_sources())

HARD = 1048576










# Pinned original functions are untyped. This one boundary validates callable
# shape at runtime and returns object; callers validate every returned value.

class _HasFileno(Protocol):
    def fileno(self) -> int: ...





















class _LoadingTransport(_RecordedTransport):
    async def __call__(self, tool: str, arguments: JsonObject,
                       budget: float) -> _RecordedResult:
        if self.calls == 0:
            self.calls += 1
            loading = text(_namespace(sys.modules["startup_readiness_v1"])["LOADING_ERROR"])
            return _RecordedResult({"is_error": True, "result_type": "complete",
                "content": [{"type": "text", "text": loading}], "structured_content": None})
        return await super().__call__(tool, arguments, budget)


@dataclass(slots=True)
class _BlockingTransport:
    entered: asyncio.Event
    release: asyncio.Event
    result: JsonObject
    calls: int = 0
    async def __call__(self, tool: str, arguments: JsonObject,
                       budget: float) -> _RecordedResult:
        self.calls += 1
        self.entered.set()
        await self.release.wait()
        return _RecordedResult(copy.deepcopy(self.result))





# Actual A33 response, retained verbatim after bounded decoding. This is a
# historical software reply; its original request is not submitted or replayed.










def _replay(current_next_sequence: int = CURRENT_SEQUENCE) -> core.HistoricalStartupDispatchReplayV1:
    corpus = _load_corpus()
    governance_ref = corpus.sources["seed"]
    return run_historical_startup_dispatch_replay_v1(
        raw_governance=corpus.object("seed"), governance_source_ref=governance_ref,
        governance_source=corpus.payload("seed"),
        cold_receiver_source=corpus.payload("material_cold_resume"),
        cold_receiver_ref=corpus.sources["material_cold_resume"],
        fixture_root=_fixture_parent(), historical_fixture_ref=_pin(DATA),
        expected_execution_machine_id=core.current_execution_machine_id_v1(),
        current_next_sequence=current_next_sequence, sdk_sources=_test_sdk_sources())

class HistoricalStartupDispatchTests(unittest.TestCase):
    def test_original_factory_startup_dispatch_and_failed_followups(self) -> None:
        target = CURRENT_SEQUENCE + 100
        result = _replay(target)
        self.assertEqual(result.current_next_sequence, target)
        self.assertEqual(result.historical_sequence, FIRST_SEQUENCE)
        wire = result.to_wire()
        _verify_mandatory_archive_boundary(result, _load_corpus())
        restored = core.parse_historical_startup_dispatch_replay_v1(parse_json(_wire(wire)))
        self.assertEqual(restored, result)
        self.assertNotEqual(result.historical_subject_machine_id, "")
        self.assertEqual(result.execution_machine_id, core.current_execution_machine_id_v1())
        self.assertLessEqual(result.peak_allocation_upper_bytes, HARD)
        self.assertEqual(wire["actual_rpc_calls"], 0)
        self.assertTrue(wire["fixture_cleaned"])
        print("HISTORICAL_STARTUP_DISPATCH", json.dumps({
            "schema": wire["schema"], "execution_machine_id": result.execution_machine_id,
            "historical_subject_machine_id": result.historical_subject_machine_id,
            "cases": [item.to_wire() for item in result.cases],
            "blocked_tools": [item.kind for item in result.blocked_followups],
            "actual_rpc_calls": 0, "fixture_cleaned": True,
            "peak_allocation_upper_bytes": result.peak_allocation_upper_bytes,
            "proof_indent2_bytes": len(_wire(wire)),
            "proof_compact_bytes": len(json.dumps(wire, ensure_ascii=False, sort_keys=True,
                separators=(",", ":"), allow_nan=False).encode()) + 1,
        }, ensure_ascii=False, sort_keys=True))

    def test_portable_fixture_source_integrity_and_historical_identity(self) -> None:
        corpus = _load_corpus()
        self.assertEqual(corpus.subject, SUBJECT)
        self.assertEqual(len(corpus.originals), 15)
        self.assertEqual(corpus.object("anchor")["campaign_id"], "robert-first30-v20261019")
        self.assertNotEqual(record(corpus.object("seed")["campaign_goal_anchor"])["campaign_id"],
                            corpus.object("anchor")["campaign_id"])
        original = corpus.object("semantic_response")
        self.assertEqual(record(original["request"])["sequence"], FIRST_SEQUENCE)
        self.assertEqual(record(record(original["result"])["structured_content"])["date_raw"], 53279256)
        self.assertEqual(hashlib.sha256(corpus.payload("anchor")).hexdigest(),
                         corpus.sources["anchor"].sha256)

    def test_public_runner_rejects_noninteger_and_obsolete_target(self) -> None:
        corpus = _load_corpus()
        for invalid in (True, 11375.0, FIRST_SEQUENCE, FIRST_SEQUENCE - 1):
            with self.subTest(target=invalid), self.assertRaises(ValueError):
                _invoke(run_historical_startup_dispatch_replay_v1,
                    fixture_root=REPO / ".ci-current-saved-preflight-fixture",
                    historical_fixture_ref=_pin(DATA),
                    expected_execution_machine_id=core.current_execution_machine_id_v1(),
                    current_next_sequence=invalid, raw_governance=corpus.object("seed"),
                    governance_source_ref=corpus.sources["seed"], governance_source=corpus.payload("seed"),
                    cold_receiver_source=corpus.payload("material_cold_resume"),
                    cold_receiver_ref=corpus.sources["material_cold_resume"],
                    sdk_sources=_test_sdk_sources())

    def test_original_postcheck_source_is_pinned(self) -> None:
        corpus = _load_corpus()
        original = ast.parse(corpus.payload("material_cold_resume"))
        def method(tree: ast.AST, name: str) -> str:
            found = [node for node in ast.walk(tree)
                     if isinstance(node, ast.FunctionDef) and node.name == name]
            self.assertEqual(len(found), 1)
            return ast.dump(found[0], include_attributes=False)
        self.assertEqual(hashlib.sha256(method(original, "check_after").encode()).hexdigest(),
                         "1dd0cde982afa999e36f63e4afa0fc35974c47a50e0cc325ed59e8919ebc7ddf")

    def test_receipt_parser_rejects_wrong_missing_and_numeric_types(self) -> None:
        corpus = _load_corpus()
        reference = corpus.reference
        roles: tuple[Literal["original_halt", "original_inflight", "first_exception"], ...] = (
            "original_halt", "original_inflight", "first_exception")
        kinds: tuple[Literal["SEM", "CAP", "AUTO", "FULL"], ...] = ("SEM", "CAP", "AUTO", "FULL")
        preserved = tuple(core.HistoricalPreservedEvidenceV1(role, reference, reference)
                          for role in roles)
        negatives = tuple(core.HistoricalBlockedFollowupV1(
            kind, {"sequence": CURRENT_SEQUENCE,
                   **({"command": "full_loop"} if kind == "FULL" else {
                       "tool": {"SEM": core.SEMANTIC_TOOL, "CAP": core.CAPABILITIES_TOOL,
                                "AUTO": "ck3_auto_turn"}[kind], "arguments": {}})},
            1, 1, preserved) for kind in kinds)
        model = core.HistoricalStartupDispatchReplayV1(
            reference, reference, reference, reference, SUBJECT,
            core.current_execution_machine_id_v1(), datetime.now(timezone.utc).isoformat(),
            FIRST_SEQUENCE, CURRENT_SEQUENCE,
            (core.HistoricalReplayCaseV1("missing_anchor", "semantic", 1, "ValueError",
              "founding score anchor requires actual paused1066 frame", 1, False),
             core.HistoricalReplayCaseV1("original_anchor_copy", "capabilities", 1,
                                        None, None, 1, True)), negatives,
            core.CurrentSavedColdQueueReplayV1(reference, reference, core._A33_CAP_REF,
                {"state": None, "pending_focus": None, "completed_cycles": 0, "pending_cycle": None}, 0), 4096)
        wire = model.to_wire()
        self.assertEqual(core.parse_historical_startup_dispatch_replay_v1(
            parse_json(_wire(wire))), model)
        for key in ("historical_sequence", "current_next_sequence",
                    "actual_rpc_calls", "peak_allocation_upper_bytes"):
            for bad in (True, float(integer(wire[key]))):
                changed = copy.deepcopy(wire)
                changed[key] = bad
                with self.subTest(field=key, bad=bad), self.assertRaises(ValueError):
                    core.parse_historical_startup_dispatch_replay_v1(changed)
        for key in ("fixture_ref", "cases", "blocked_followups", "dispatch_installed"):
            changed = copy.deepcopy(wire)
            del changed[key]
            with self.subTest(missing=key), self.assertRaises(ValueError):
                core.parse_historical_startup_dispatch_replay_v1(changed)
        for key, value in (("fixture_cleaned", 1), ("actual_rpc_calls", 1),
                           ("historical_sequence", CURRENT_SEQUENCE),
                           ("unknown_field", None)):
            changed = copy.deepcopy(wire)
            changed[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                core.parse_historical_startup_dispatch_replay_v1(changed)

def _score_fixture_basis(corpus: _Corpus, root: Path) -> CurrentSavedBasisV1:
    seed = corpus.object("seed")
    frame = parse_frame(seed["before"])
    dummy = ExactRefV1(str(root / "synthetic-small-proof.json"), 1, "0" * 64)
    driver = ExactRefV1(str(root / "state" / "native-session" / "driver-state.json"), 1, "1" * 64)
    saved = ExactRefV1(str(root / "state" / "profile" / "save games" / "xar_checkpoint.ck3"), 1, "2" * 64)
    refs = BasisRefsV1(dummy, dummy, dummy, dummy, dummy, dummy, driver, saved,
                      dummy, dummy, dummy, dummy, dummy, dummy, dummy)
    goal = json_object(seed["campaign_goal_anchor"])
    return CurrentSavedBasisV1(
        SUBJECT, datetime.now(timezone.utc).isoformat(),
        CampaignOriginV1(53144328, 53407128, 10950,
                         "2026-10-19T00:00:00+00:00", text(goal["campaign_id"])),
        frame, 5143,
        {"name": "xar_checkpoint.ck3", "load_save_name": "xar_checkpoint",
         "path": saved.path, "size": 1, "sha256": saved.sha256,
         "saved_date_raw": frame.date_raw, "history_index": 5894,
         "succession_lifecycle": None}, goal, refs,
        FileStatIdentityV1(1, "1", "1"), FileStatIdentityV1(1, "2", "1"),
        CURRENT_SEQUENCE,
        ProgressReconciliationV1(5143, frame.date_raw, 5143, frame.date_raw,
                                  11310, 1, 1, True), (), ())


class ScoreSourceContractTests(unittest.TestCase):
    def test_original_anchor_identity_and_missing_mapping_are_validated(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace:
            root = workspace.root / "score-source"
            root.mkdir()
            target = root / "campaign-score"
            target.mkdir()
            runtime = root / "new-runtime"
            runtime.mkdir()
            path = target / "CAMPAIGN-ANCHOR.json"
            workspace.write(path, corpus.payload("anchor"))
            file_id, device = campaign_score_directory_identity_v1(target)
            binding = CampaignScoreJunctionV1(
                str(runtime / "campaign-score"), str(target), True,
                file_id, device, _pin(path))
            basis = _score_fixture_basis(corpus, root)
            validate_campaign_score_junction_source_v1(
                binding, basis, runtime_root=runtime, reader=LocalBasisReaderV1())
            self.assertEqual(parse_campaign_score_junction_v1(
                parse_json(_wire(binding.to_wire()))), binding)
            original = corpus.object("anchor")
            for key, bad in (("founder_character_id", 31255),
                             ("founder_character_id", True),
                             ("founder_character_id", 31254.0),
                             ("start_date_raw", 53144352),
                             ("endpoint_date_raw", 53407152),
                             ("campaign_id", text(basis.campaign_goal_anchor["campaign_id"]))):
                changed = copy.deepcopy(original)
                changed[key] = bad
                workspace.write(path, _wire(changed), replace_existing=True)
                current = replace(binding, anchor_ref=_pin(path))
                with self.subTest(field=key, bad=bad), self.assertRaises(ValueError):
                    validate_campaign_score_junction_source_v1(
                        current, basis, runtime_root=runtime, reader=LocalBasisReaderV1())
            workspace.write(path, corpus.payload("anchor"), replace_existing=True)
            for key in ("path", "exact_target", "anchor_ref", "must_verify_same_FileID"):
                wire = binding.to_wire()
                del wire[key]
                with self.subTest(missing=key), self.assertRaises(ValueError):
                    parse_campaign_score_junction_v1(wire)
            with self.assertRaises(ValueError):
                validate_campaign_score_junction_source_v1(
                    replace(binding, path=str(runtime / "wrong-score")), basis,
                    runtime_root=runtime, reader=LocalBasisReaderV1())
            path.unlink()
            with self.assertRaises((ValueError, OSError)):
                validate_campaign_score_junction_source_v1(
                    binding, basis, runtime_root=runtime, reader=LocalBasisReaderV1())


class RequestPermitTests(unittest.TestCase):
    def test_public_atomic_publisher_and_last_check_failure(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace:
            root = workspace.root / "publisher"
            root.mkdir()
            for name in ("p37-queue", "p37-requests", "p37-responses"):
                (root / name).mkdir()
            machine = core.current_execution_machine_id_v1()
            basis = replace(_score_fixture_basis(corpus, root), machine_id=machine)
            basis_path = root / "basis.json"
            workspace.write(basis_path, _wire(basis.to_wire()))
            basis_ref = _pin(basis_path)
            validation = root / "qualification.json"
            workspace.write(validation, b"{}")
            validation_ref = _pin(validation)
            workspace.write(root / "ROOT-CURRENT-SAVED-INPUTS01.json", _wire({
                "schema": "xar.current-saved-cold-inputs/v1", "machine_id": machine,
                "basis_ref": basis_ref.to_wire(), "validation_ref": validation_ref.to_wire()}))
            workspace.write(root / "ROOT-LAUNCH-CONFIG-C23-A15.json", _wire({
                "cold_attempt": {"machine_id": machine, "runtime_root": str(root),
                    "attempt_nonce": "a" * 32, "task_nonce": "b" * 32,
                    "basis_ref": basis_ref.to_wire(), "validation_ref": validation_ref.to_wire()}}))
            request: JsonObject = {"sequence": CURRENT_SEQUENCE, "tool": core.SEMANTIC_TOOL,
                                   "arguments": {}}
            submission = core.submit_readiness_request_v1(
                request, runtime_root=root, expected_machine_id=machine)
            destination = root / "p37-requests" / f"{CURRENT_SEQUENCE:04d}-1-result.json"
            self.assertEqual(record(parse_json(destination.read_bytes())), request)
            self.assertEqual(submission.request_ref, _pin(destination))
            before = _pin(destination)
            with self.assertRaises(ValueError):
                core.submit_readiness_request_v1(request, runtime_root=root, expected_machine_id=machine)
            self.assertEqual(_pin(destination), before)
            destination.unlink()  # Remove only this synthetic publisher fixture's request.
            real_fsync = os.fsync
            injected = False
            def mark_failed_after_pending_sync(fd: int | _HasFileno) -> None:
                nonlocal injected
                real_fsync(fd)
                if not injected:
                    injected = True
                    workspace.write(root / "NEXT-SEQUENCE-P37.json", _wire({
                        "next_sequence": CURRENT_SEQUENCE,
                        "failed_request_registered_without_readmission": True}))
            try:
                os.fsync = mark_failed_after_pending_sync
                with self.assertRaises(ValueError):
                    core.submit_readiness_request_v1(request, runtime_root=root,
                                                    expected_machine_id=machine)
            finally:
                os.fsync = real_fsync
            self.assertTrue(injected)
            self.assertFalse(destination.exists())
            self.assertEqual(list(destination.parent.iterdir()), [])

    def test_loading_marker_one_cannot_grant_the_third_call(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="loading-once", with_anchor=True)
            harness.transport = _LoadingTransport(harness.transport.result)
            request = harness.request("SEM")
            async def run() -> None:
                dispatch = asyncio.create_task(harness.dispatch(request))
                marker = harness.root / "p37-queue" / f"READINESS-{FIRST_SEQUENCE:04d}-000001-loading.json"
                try:
                    async def published() -> None:
                        while not marker.exists():
                            if dispatch.done():
                                dispatch.result()
                            await asyncio.sleep(.01)
                    await asyncio.wait_for(published(), 2)
                    active = getattr(harness.queue, "_current_saved_active_permit_v1")
                    need(isinstance(active, core.CurrentSavedRequestPermitV1), "actual active startup permit")
                    if not isinstance(active, core.CurrentSavedRequestPermitV1):
                        raise TypeError("typed startup permit required")
                    session = core.GuardedCurrentSavedSessionV1(
                        harness.queue, request, runtime_root=harness.root,
                        call=harness.transport, permit=active)
                    await session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0)
                    self.assertEqual(harness.transport.calls, 2)
                    # The first marker and result really came from unchanged
                    # startup_readiness_call. Reusing their bytes under a later
                    # ordinal cannot confer another transport permission.
                    original_row = marker.with_name(marker.name.replace("-loading", "-result"))
                    workspace.write(marker.with_name(marker.name.replace("000001", "000002")), marker.read_bytes())
                    workspace.write(original_row.with_name(original_row.name.replace("000001", "000002")),
                                    original_row.read_bytes())
                    with self.assertRaises(ValueError):
                        await session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0)
                    self.assertEqual(harness.transport.calls, 2)
                finally:
                    dispatch.cancel()
                    try:
                        await dispatch
                    except asyncio.CancelledError:
                        pass
            asyncio.run(run())

    def test_original_loading_marker_is_the_only_retry_authority(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="loading", with_anchor=True)
            harness.transport = _LoadingTransport(harness.transport.result)
            # The original startup helper owns its exact five-second delay.
            asyncio.run(harness.dispatch(harness.request("SEM")))
            self.assertEqual(harness.transport.calls, 2)
            self.assertEqual(_phase_value(harness), "capabilities")
            self.assertEqual(harness.score_calls, 1)
            self.assertEqual(harness.startup_calls, 1)
            self.assertIsNone(getattr(harness.queue, "halted"))
            self.assertTrue((harness.root / "p37-queue" /
                             f"READINESS-{FIRST_SEQUENCE:04d}-000001-loading.json").is_file())

    def test_parallel_session_calls_burn_before_await(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="parallel", with_anchor=False)
            request = harness.request("SEM")
            permit = core.guard_current_saved_request_v1(harness.queue, request, runtime_root=harness.root)
            async def run() -> None:
                call = _BlockingTransport(asyncio.Event(), asyncio.Event(), harness.transport.result)
                session = core.GuardedCurrentSavedSessionV1(
                    harness.queue, request, runtime_root=harness.root, call=call, permit=permit)
                first = asyncio.create_task(session.call_tool(
                    core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0))
                try:
                    await asyncio.wait_for(call.entered.wait(), 2)
                    with self.assertRaises(ValueError):
                        await session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0)
                    self.assertEqual(call.calls, 1)
                finally:
                    call.release.set()
                    await first
                with self.assertRaises(ValueError):
                    await session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0)
                self.assertEqual(call.calls, 1)
            asyncio.run(run())

    def test_permit_is_single_use_and_cannot_be_replaced(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="permit", with_anchor=False)
            cold = record(getattr(harness.queue, "_normal_cold"))
            cold["phase"] = "ready"
            setattr(harness.queue, "_normal_cold", cold)
            workspace.write(harness.root / "NEXT-SEQUENCE-P37.json",
                            _wire({"next_sequence": FIRST_SEQUENCE}))
            request = harness.request("AUTO")
            permit = core.guard_current_saved_request_v1(
                harness.queue, request, runtime_root=harness.root)
            forged = replace(permit)
            with self.assertRaises(ValueError):
                core.guard_current_saved_request_v1(
                    harness.queue, request, runtime_root=harness.root, active=forged)
            session = core.GuardedCurrentSavedSessionV1(
                harness.queue, request, runtime_root=harness.root,
                call=harness.transport, permit=permit)
            asyncio.run(session.call_tool("ck3_auto_turn", {}, read_timeout_seconds=1.0))
            self.assertEqual(harness.transport.calls, 1)
            with self.assertRaises(ValueError):
                asyncio.run(session.call_tool("ck3_auto_turn", {}, read_timeout_seconds=1.0))
            self.assertEqual(harness.transport.calls, 1)
            with self.assertRaises(ValueError):
                core.guard_current_saved_request_v1(harness.queue, request, runtime_root=harness.root)

    def test_transport_exception_burns_the_permit(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="exception", with_anchor=False)
            request = harness.request("SEM")
            permit = core.guard_current_saved_request_v1(harness.queue, request, runtime_root=harness.root)
            harness.transport.fail = True
            session = core.GuardedCurrentSavedSessionV1(
                harness.queue, request, runtime_root=harness.root,
                call=harness.transport, permit=permit)
            with self.assertRaisesRegex(RuntimeError, "controlled offline"):
                asyncio.run(session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0))
            with self.assertRaises(ValueError):
                asyncio.run(session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0))
            self.assertEqual(harness.transport.calls, 1)

    def test_missing_paths_wrong_fields_types_and_epoch_drift_reject_before_transport(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="types", with_anchor=False)
            request = harness.request("SEM")
            for bad in (True, float(FIRST_SEQUENCE), "11373", None):
                changed = copy.deepcopy(request)
                changed["sequence"] = bad
                with self.subTest(sequence=bad), self.assertRaises(ValueError):
                    core.guard_current_saved_request_v1(harness.queue, changed, runtime_root=harness.root)
            for field in ("sequence", "tool", "arguments"):
                changed = copy.deepcopy(request)
                del changed[field]
                with self.subTest(missing=field), self.assertRaises(ValueError):
                    core.guard_current_saved_request_v1(harness.queue, changed, runtime_root=harness.root)
            changed = copy.deepcopy(request)
            changed["arguments"] = []
            with self.assertRaises(ValueError):
                core.guard_current_saved_request_v1(harness.queue, changed, runtime_root=harness.root)
            for filename in ("ROOT-LAUNCH-CONFIG-C23-A15.json",
                             "ROOT-ACTUAL-GAME-LAUNCH-C23.json",
                             "ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json",
                             "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C23.json"):
                path = harness.root / filename
                raw = path.read_bytes()
                path.unlink()
                with self.subTest(missing_path=filename), self.assertRaises((ValueError, OSError)):
                    core.guard_current_saved_request_v1(harness.queue, request, runtime_root=harness.root)
                workspace.write(path, raw)
            config_path = harness.root / "ROOT-LAUNCH-CONFIG-C23-A15.json"
            permit = core.guard_current_saved_request_v1(harness.queue, request, runtime_root=harness.root)
            config = record(parse_json(config_path.read_bytes()))
            attempt = record(config["cold_attempt"])
            attempt["attempt_nonce"] = "c" * 32
            config["cold_attempt"] = attempt
            workspace.write(config_path, _wire(config), replace_existing=True)
            with self.assertRaises(ValueError):
                core.guard_current_saved_request_v1(harness.queue, request, runtime_root=harness.root)
            session = core.GuardedCurrentSavedSessionV1(
                harness.queue, request, runtime_root=harness.root,
                call=harness.transport, permit=permit)
            with self.assertRaises(ValueError):
                asyncio.run(session.call_tool(core.SEMANTIC_TOOL, {}, read_timeout_seconds=1.0))
            self.assertEqual(harness.transport.calls, 0)

    def test_unknown_phase_and_failed_next_never_publish(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="flags", with_anchor=False)
            request = harness.request("SEM")
            cold = record(getattr(harness.queue, "_normal_cold"))
            cold["phase"] = "unrecognized"
            setattr(harness.queue, "_normal_cold", cold)
            published: list[JsonObject] = []
            with self.assertRaises(ValueError):
                core.submit_queue_readiness_request_v1(
                    harness.queue, request, runtime_root=harness.root, publish=published.append)
            cold["phase"] = "semantic"
            setattr(harness.queue, "_normal_cold", cold)
            next_path = harness.root / "NEXT-SEQUENCE-P37.json"
            for bad in (True, 0, 0.0, None):
                workspace.write(next_path, _wire({"next_sequence": FIRST_SEQUENCE,
                    "failed_request_registered_without_readmission": bad}), replace_existing=next_path.exists())
                with self.subTest(flag=bad), self.assertRaises(ValueError):
                    core.submit_queue_readiness_request_v1(
                        harness.queue, request, runtime_root=harness.root, publish=published.append)
            self.assertEqual(published, [])
            self.assertEqual(harness.transport.calls, 0)



@dataclass(slots=True)
class _ArchiveReader:
    blobs: dict[str, bytes] = field(default_factory=dict)
    def put(self, path: str, raw: bytes) -> ExactRefV1:
        self.blobs[path] = raw
        return ExactRefV1(path, len(raw), hashlib.sha256(raw).hexdigest())
    def read(self, reference: ExactRefV1, limit: int) -> bytes:
        raw = self.blobs[reference.path]
        need(len(raw) <= limit, "bounded real archive qualification input")
        return raw
    def stat(self, path: str) -> FileStatIdentityV1:
        raise AssertionError("archive boundary must not inspect live Driver/SAVE")

def _verify_mandatory_archive_boundary(
    full: core.HistoricalStartupDispatchReplayV1, corpus: _Corpus,
) -> None:
    # This is the real mandatory archive stage, supplied actual replay evidence
    # and exact bytes in RAM. It does not qualify a physical runtime/owner.
    reader = _ArchiveReader()
    fixture = record(parse_json(DATA.read_bytes()))
    for name, reference in corpus.sources.items():
        reader.put(reference.path, corpus.payload(name))
    reader.put(full.fixture_ref.path, DATA.read_bytes())
    reader.put(full.harness_ref.path, Path(replay.__file__).read_bytes())
    reader.put(full.core_source_ref.path, Path(core.__file__).read_bytes())
    root = REPO / ".archive-boundary-not-created"
    basis = replace(_score_fixture_basis(corpus, root),
                    machine_id=full.execution_machine_id,
                    next_sequence=full.current_next_sequence,
                    refs=replace(_score_fixture_basis(corpus, root).refs,
                                 governance=full.cold_queue_contract.governance_ref))
    basis_ref = reader.put(str(root / "basis.json"), _wire(basis.to_wire()))
    replay_ref = reader.put(str(root / "actual-replay.json"), _wire(full.to_wire()))
    placeholder = reader.put(str(root / "unread-metadata.json"), b"{}")
    source_path = "tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py"
    names = tuple(sorted(CANONICAL_NAMES))
    plan = ColdPlanV1(
        full.execution_machine_id, full.observed_at_utc, full.observed_at_utc,
        str(root), str(root / "material"), placeholder, basis_ref, placeholder,
        placeholder, (
            SourceRowV1(source_ref=full.core_source_ref, relative_path=source_path),
            SourceRowV1(source_ref=full.harness_ref,
                        relative_path="tools/g2_saved_campaign/current_saved_campaign_replay_v1.py"),),
        names, names + (source_path, "tools/g2_saved_campaign/current_saved_campaign_replay_v1.py"), (".",), placeholder, placeholder,
        str(root / "screen.json"), str(root / "spec.json"), "a" * 32, "b" * 32,
        "c" * 32, 32, placeholder, placeholder, None, 1090519040)
    producer_path = Path(replay.__file__).with_name("prepare_current_saved_campaign_cold_v1.py")
    plan = replace(plan, producer_ref=reader.put(str(producer_path), producer_path.read_bytes()))
    plan_ref = reader.put(str(root / "plan.json"), _wire(plan.to_wire()))
    output: list[OutputRowV1] = []
    for key, name in (("material_cold_resume", "root_p37c23_cold_resume.py"),
                      ("score", "root_score_month_samples_c23.py")):
        current = reader.put(full.cold_queue_contract.receiver_ref.path if key == "material_cold_resume"
                             else str(root / name), corpus.payload(key))
        output.append(OutputRowV1(current.path, name, current.bytes, current.sha256,
                                  "create-only", None))
    for relative, raw in (
        ("tools/g2_saved_campaign/current_saved_campaign_replay_v1.py",
         Path(replay.__file__).read_bytes()),
        (replay.HISTORICAL_REPLAY_DATA_RELATIVE_PATH_V1, DATA.read_bytes())):
        current = reader.put(str(root / relative), raw)
        output.append(OutputRowV1(path=current.path, relative_path=relative,
            bytes=current.bytes, sha256=current.sha256, mode="create-only",
            source_ref=None))
    anchor = corpus.sources["anchor"]
    junction = CampaignScoreJunctionV1(
        str(root / "campaign-score"), str(Path(anchor.path).parent), True, "1", "1", anchor)
    quote = ColdQuoteV1(full.execution_machine_id, full.observed_at_utc,
        plan_ref, basis_ref, placeholder, placeholder, str(root), tuple(output),
        junction, names, names + (source_path,), (".",), 8, 1, 1, 1, None, plan.artifact_cap_bytes)
    direct = core._archive_historical_replay_v1(replay_ref, full, fixture, plan, quote, reader)
    restored, mandatory = core._full_historical_replay(
        replay_ref, plan, quote, full.core_source_ref, reader)
    need(restored == full and mandatory == direct
         and mandatory.historical_sequence == FIRST_SEQUENCE
         and mandatory.original_queue_ref == corpus.sources["queue"],
         "actual mandatory preflight archive stage binds original queue and sequence")

class HistoricalArchiveBoundaryTests(unittest.TestCase):
    def test_public_decoder_real_archive_and_malformed_inputs(self) -> None:
        fixture = record(parse_json(DATA.read_bytes()))
        payloads = record(fixture["payloads"])
        for name, payload_item in payloads.items():
            reference, raw = core.decode_current_saved_historical_payload_v1(payload_item)
            self.assertEqual(reference, parse_ref(record(payload_item)["source_ref"]))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), reference.sha256)
        queue = record(payloads["queue"])
        self.assertEqual(len(text(queue["encoding"])), 11)
        encoded = queue["encoded"]
        self.assertIsInstance(encoded, str)
        self.assertEqual(len(str(encoded)), 75964)
        with self.assertRaises(ValueError):
            text(encoded)  # The actual former 32-KiB consumer rejects this archive.
        reference, raw = core.decode_current_saved_historical_payload_v1(queue)
        self.assertEqual(len(raw), 279163)
        self.assertEqual(reference.sha256,
                         "6ef48e4e9285c6e7e00cc03fae815843c74a4adebdffd49ac13385131fa3d1cc")
        for key, invalid in (("encoded", True), ("encoded", None), ("encoded", "!!!!"),
                             ("encoded", "A" * 131076), ("encoding", "base64"),
                             ("unexpected", None)):
            changed = dict(queue)
            changed[key] = invalid
            with self.subTest(field=key), self.assertRaises(ValueError):
                core.decode_current_saved_historical_payload_v1(changed)
        for invalid_size in (True, 279163.0, 1048577, 279164):
            changed = dict(queue)
            changed_ref = record(queue["source_ref"])
            changed_ref["bytes"] = invalid_size
            changed["source_ref"] = changed_ref
            with self.subTest(bytes=invalid_size), self.assertRaises(ValueError):
                core.decode_current_saved_historical_payload_v1(changed)
        raw = b"ab"
        compressed = zlib.compress(raw)
        def item(packed: bytes, *, declared: int = 2, sha: str | None = None) -> JsonObject:
            return {"encoding": "zlib-base64",
                    "encoded": base64.b64encode(packed).decode(),
                    "source_ref": {"path": str(DATA), "bytes": declared,
                                  "sha256": hashlib.sha256(raw).hexdigest() if sha is None else sha}}
        for bad in (item(compressed + b"tail"), item(compressed[:-1]),
                    item(zlib.compress(b"x" * 1048577), declared=1),
                    item(compressed, sha="0" * 64),
                    item(b"x" * 98305)):
            with self.subTest(malformed=True), self.assertRaises((ValueError, zlib.error)):
                core.decode_current_saved_historical_payload_v1(bad)
        noncanonical = item(compressed)
        encoded = text(noncanonical["encoded"])
        self.assertTrue(encoded.endswith("=="))
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
        position = alphabet.index(encoded[-3])
        noncanonical["encoded"] = encoded[:-3] + alphabet[position + 1] + "=="
        with self.assertRaises(ValueError):
            core.decode_current_saved_historical_payload_v1(noncanonical)


_N28_CLASSIFIER_PROJECTION = """def classify_existing_typed_v1(body, *, state=None, initial_frame=None, game_pid=None):
    from root_c11_prisoner_cold_epoch_credit import classify
    return classify(body, state=state, initial_frame=initial_frame, game_pid=game_pid, namespace=globals())
"""

class OriginalFlatCapProducerTests(unittest.TestCase):
    def test_original_queue_flat_cap_session_and_bound(self) -> None:
        corpus = _load_corpus()
        with _owned_workspace() as workspace, _isolated_modules():
            harness = _make_harness(workspace, corpus, name="flat-cap", with_anchor=True)
            env = harness.namespace
            original_tree = ast.parse(corpus.payload("queue"))
            queue_class = next(node for node in original_tree.body
                               if isinstance(node, ast.ClassDef) and node.name == "FreshQueue")
            call = next(node for node in queue_class.body
                        if isinstance(node, ast.AsyncFunctionDef) and node.name == "call")
            self.assertEqual(hashlib.sha256(ast.dump(call, include_attributes=False).encode()).hexdigest(),
                             "a78999685638b5aaac3feb94e32f3968425d93be456c866fc73626b5f0c125f4")
            # The archived original Queue and actual frozen N28 call/atomic
            # producers have identical ASTs. Execute their original bodies.
            expected = {"atomic": "0d16a738759894f1181745cc9e81f7de2a0b969507b87ae9ddda5fbec61f147d",
                "atomic_payload_v1": "1f4e0703d0e7fb7021badf8f73401b6c474d6a27c2acb0bc392e5c8f28a7d60c",
                "persist_loop_state": "9724b320ff071ca0901059aabd74f632eaabed5ba42a0850f8603f807ad320aa"}
            projection = _selected_source(corpus.payload("queue"), {"atomic", "atomic_payload_v1"},
                                         {"FreshQueue": {"persist_loop_state"}})
            for node in ast.parse(projection).body:
                if isinstance(node, ast.FunctionDef):
                    self.assertEqual(hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
                                     expected[node.name])
            projection += "\n" + _N28_CLASSIFIER_PROJECTION
            source_path = harness.root / "n28_original_cap_projection.py"
            workspace.write(source_path, projection.encode())
            from contextlib import nullcontext
            import uuid
            def before_write(path: object) -> None:
                need(isinstance(path, Path), "original producer path")
                if not isinstance(path, Path):
                    raise ValueError("Path required")
                need(path.parent.resolve().is_relative_to(workspace.root), "owned original atomic path")
                workspace.measure()
            env.update(os=os, uuid=uuid, _control_span_v1=lambda name: nullcontext(),
                       _before_full_generated_write_v1=before_write)
            exec(compile(projection, str(source_path), "exec"), env)
            setattr(type(harness.queue), "persist_loop_state", env["persist_loop_state"])
            self.assertEqual(hashlib.sha256(_N28_RESPONSE_SOURCE).hexdigest(),
                             "895519ed2d403f87fa8740252909ca2d4e23d88940eca70833d945f333cc8b2c")
            response = _module("owner_response_json_once_v1", harness.root / "n28_response_original.py",
                               _N28_RESPONSE_SOURCE, workspace)
            env["_owner_response_success_row_once_v1"] = _namespace(response)["prepare_success_response_row_v1"]
            env["load_cold_result_classifier"] = lambda: env["classify_existing_typed_v1"]
            reviewed_path = harness.root / "classifier_projection_pin.json"
            workspace.write(reviewed_path, _wire({"source": str(source_path),
                "sha256": hashlib.sha256(projection.encode()).hexdigest()}))
            cold = record(getattr(harness.queue, "_normal_cold"))
            admission = record(cold["admission"])
            admission["classifier_pin"] = _pin(reviewed_path).to_wire()
            cold["admission"] = admission
            setattr(harness.queue, "_normal_cold", cold)
            negative_checks = 0
            original_atomic = env["atomic"]
            cap_sequence = FIRST_SEQUENCE + 1
            def atomic_observer(path: Path, value: object, *, replace: bool = False,
                                limit: int = 65536) -> object:
                nonlocal negative_checks
                outcome = _invoke(original_atomic, path, value, replace=replace, limit=limit)
                workspace.measure()
                if path.name != f"INFLIGHT-{cap_sequence:04d}.json":
                    return outcome
                raw = path.read_bytes()
                flat = record(parse_json(raw))
                self.assertEqual(set(flat), {"sequence", "tool", "arguments", "request_file",
                                            "at_utc", "replay_allowed"})
                self.assertNotIn("request", flat)
                parsed = core.parse_current_saved_queue_tool_inflight_v1(flat)
                self.assertEqual(core.parse_current_saved_queue_tool_inflight_v1(parse_json(_wire(flat))), parsed)
                active = getattr(harness.queue, "_current_saved_active_permit_v1")
                need(isinstance(active, core.CurrentSavedRequestPermitV1), "actual CAP permit")
                if not isinstance(active, core.CurrentSavedRequestPermitV1):
                    raise TypeError("typed permit required")
                request = json_object(parse_json(active.request_json))
                calls = harness.transport.calls
                def reject() -> None:
                    nonlocal negative_checks
                    with self.assertRaises(ValueError):
                        core.guard_current_saved_request_v1(harness.queue, request,
                            runtime_root=harness.root, active=active)
                    negative_checks += 1
                    self.assertEqual(harness.transport.calls, calls)
                variants: list[dict[str, object]] = []
                for key in flat:
                    changed = dict(flat)
                    del changed[key]
                    variants.append(changed)
                for key, invalid in (("sequence", True), ("sequence", float(cap_sequence)),
                    ("sequence", cap_sequence + 1), ("tool", core.SEMANTIC_TOOL),
                    ("arguments", []), ("arguments", {"unexpected": True}),
                    ("request_file", "relative.json"),
                    ("request_file", str(harness.root / "wrong-request.json")),
                    ("at_utc", None), ("replay_allowed", True), ("replay_allowed", 0),
                    ("request", request)):
                    changed = dict(flat)
                    changed[key] = invalid
                    variants.append(changed)
                variants.append({"request": request})
                for changed in variants:
                    workspace.write(path, _wire(changed), replace_existing=True)
                    reject()
                workspace.write(path, raw, replace_existing=True)
                request_path = Path(text(flat["request_file"]))
                request_raw = request_path.read_bytes()
                workspace.write(request_path, _wire({**request, "arguments": {"wrong": 1}}), replace_existing=True)
                reject()
                workspace.write(request_path, request_raw, replace_existing=True)
                # Unknown requests remain unknown across repeated checks. Only
                # these deliberately planted fixture files are removed.
                for filename in ("INFLIGHT-99999.json", f"INFLIGHT-0{cap_sequence}.json"):
                    unknown = path.with_name(filename)
                    workspace.write(unknown, raw)
                    before = _pin(unknown)
                    reject()
                    reject()
                    self.assertEqual(_pin(unknown), before)
                    unknown.unlink()
                core.guard_current_saved_request_v1(harness.queue, request,
                    runtime_root=harness.root, active=active)
                return outcome
            env["atomic"] = atomic_observer
            asyncio.run(harness.dispatch(harness.request("SEM")))
            self.assertEqual(_phase_value(harness), "capabilities")
            old_inflight = harness.root / "p37-queue" / f"INFLIGHT-{FIRST_SEQUENCE:04d}.json"
            old_pin = _pin(old_inflight)
            checkpoint = record(cold["checkpoint"])
            harness.transport.result = {"is_error": False, "result_type": "complete", "content": [],
                "structured_content": {"status": "ready",
                    "episode_run_id": text(checkpoint["episode_run_id"]),
                    "episode_character_id": integer(checkpoint["episode_character_id"], 1),
                    "episode_identity_pending": False, "one_life_terminal": False,
                    "native_session_control": {"driver_state_restored": True,
                        "driver_state_restore_kind": "cold_checkpoint", "episode_binding_state": "active_resumed",
                        "driver_state_error": None, "cold_candidate_rejection": None}}}
            cap = harness.request("CAP")
            asyncio.run(harness.dispatch(cap))
            self.assertEqual(harness.transport.calls, 2)
            self.assertEqual(_phase_value(harness), "ready")
            self.assertEqual(_pin(old_inflight), old_pin)
            self.assertIsNone(getattr(harness.queue, "halted"))
            self.assertTrue(getattr(harness.queue, "checkpoint_bootstrap_verified"))
            bound_path = harness.root / "p37-queue" / "ROOT-C23-NORMAL-COLD-BOUND.json"
            bound = record(parse_json(bound_path.read_bytes()))
            self.assertEqual(integer(bound["completed_cycles"]), integer(corpus.object("seed")["completed_cycles"]))
            self.assertEqual(bound["new_ordinary_cycle_credit"], 0)
            self.assertIs(bound["AUTO_or_MET_replayed"], False)
            before_calls = harness.transport.calls
            with self.assertRaises(ValueError):
                core.guard_current_saved_request_v1(harness.queue, cap, runtime_root=harness.root)
            self.assertEqual(harness.transport.calls, before_calls)
            self.assertGreaterEqual(negative_checks, 24)
            print("OFFLINE_ORIGINAL_CAP_BOUND", {"machine_id": core.current_execution_machine_id_v1(),
                "historical_source_machine_id": SUBJECT, "source_observed_at_utc": "2026-10-21T13:37:22.057697+00:00",
                "n28_queue_bytes": 279636,
                "n28_queue_sha256": "c5fc4bfc6eac11dc0d353f709be0cebe0dbf24c45e03ead5de5189b9ab71c7c0",
                "negative_checks": negative_checks, "recorded_reply_calls": harness.transport.calls,
                "actual_rpc_calls": 0, "ordinary_cycle_credit": 0,
                "peak_allocation_upper_bytes": workspace.peak})


class CompleteColdGovernanceContractTests(unittest.TestCase):
    def test_actual_raw_null_projection_and_report_json_contract(self) -> None:
        corpus = _load_corpus()
        raw = corpus.object("seed")
        self.assertNotIn("state", raw)
        projected = project_current_saved_governance_resume_v1(raw,
            expected_completed_cycles=integer(raw["completed_cycles"]))
        self.assertIsNone(projected.state)
        self.assertIsNone(projected.pending_focus)
        model = core.CurrentSavedColdQueueReplayV1(corpus.sources["seed"],
            corpus.sources["material_cold_resume"], core._A33_CAP_REF,
            projected.to_wire(), projected.completed_cycles)
        wire = model.to_wire()
        self.assertEqual(core.parse_current_saved_cold_queue_replay_v1(parse_json(_wire(wire))), model)
        for field in wire:
            changed = copy.deepcopy(wire)
            del changed[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                core.parse_current_saved_cold_queue_replay_v1(changed)
        for key, value in (("completed_cycles", True), ("recorded_cap_calls", 1.0),
                           ("original_postchecks", False), ("phase_after", "capabilities"),
                           ("original_persist_executed", 1), ("bound_after_original_persistence", False),
                           ("closed_inputs_reloaded_after_sem", True), ("extra", None)):
            changed = copy.deepcopy(wire)
            changed[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                core.parse_current_saved_cold_queue_replay_v1(changed)

    def test_raw_governance_errors_reject_before_any_recorded_transport(self) -> None:
        corpus = _load_corpus()
        original = corpus.object("seed")
        variants: list[dict[str, object]] = []
        for key in ("governance_result_state", "pending_focus", "pending_cycle", "completed_cycles"):
            changed = dict(original)
            del changed[key]
            variants.append(changed)
        for key, value in (("completed_cycles", True), ("completed_cycles", 5143.0),
                           ("governance_result_state", []), ("governance_result_state", False),
                           ("pending_focus", 1), ("pending_cycle", {})):
            changed = dict(original)
            changed[key] = value
            variants.append(changed)
        for changed in variants:
            with self.subTest(fields=list(changed)), self.assertRaises(ValueError):
                project_current_saved_governance_resume_v1(changed, expected_completed_cycles=5143)



_UINT64_REPLAY_BUNDLE = record(json.loads(zlib.decompress(base64.b64decode(
    "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", validate=True))))

@dataclass(frozen=True, slots=True)
class _CountedPythonResult(_RecordedResult):
    dumps: list[int]
    def model_dump(self, *, mode: Literal["json"]) -> JsonObject:
        self.dumps.append(1)
        return _RecordedResult.model_dump(self, mode=mode)

class _Int64RecordedTransport(_RecordedTransport):
    def __init__(self, result: JsonObject) -> None:
        super().__init__(result)
        self.dumps: list[int] = []
    async def __call__(self, tool: str, arguments: JsonObject,
                       budget: float) -> _CountedPythonResult:
        original = await super().__call__(tool, arguments, budget)
        return _CountedPythonResult(original.value, self.dumps)

def _install_original_auto_postcheck(harness: _Harness) -> None:
    sdk_root = REPO / "ck3_autonomous_player/src/xar_autoplayer"
    setattr(sys.modules["xar_autoplayer"], "__path__", [str(sdk_root)])
    setattr(sys.modules["xar_autoplayer.bridge"], "__path__", [str(sdk_root / "bridge")])
    package = sdk_root / "__init__.py"
    exec(compile(package.read_bytes(), str(package), "exec"), vars(sys.modules["xar_autoplayer"]))
    raw = harness.corpus.payload("queue")
    tree = ast.parse(raw)
    definitions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)
        and (node.name.startswith("classify_") or node.name in
             {"_war_optional_object_v1", "_war_optional_uint_v1"})}
    source = _selected_source(raw, definitions, {"FreshQueue": {"check_after"}})
    constants: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and all(
            isinstance(target, ast.Name) and target.id.isupper() for target in node.targets):
            try:
                ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
            constants.append(text(ast.get_source_segment(raw.decode(), node)))
    source += "\n" + "\n".join(constants) + "\n"
    path = harness.root / "ordinary_postcheck_original.py"
    exec(compile(source, str(path), "exec"), harness.namespace)
    original_base = next(cls for cls in type(harness.queue).__mro__
                         if cls.__name__ == "_OriginalQueueMethods")
    setattr(original_base, "check_after", harness.namespace["check_after"])
    setattr(harness.queue, "result_classifier", harness.namespace["classify_auto_result_credit_v1"])
    for name in ("root_p37c23_automatic_natural_succession_handoff.py",
                 "p51_resident_successor_adoption_c23.py",
                 "root_battle_epoch_credit.py", "root_committed_contact_credit.py"):
        item = record(_UINT64_REPLAY_BUNDLE[name])
        _module(name.removesuffix(".py"), harness.root / name,
                text(item["source"]).encode(), harness.workspace)
    harness.workspace.write(harness.root / "ROOT-ACTUAL-DRIVER-MODE-P37C23.json",
        _wire({"episode_projection": "one_life", "before_submit_observation": True}))

class PythonMcpResultDomainTests(unittest.TestCase):
    def test_original_queue_auto_encoder_postcheck_preserves_native_int64(self) -> None:
        from unittest.mock import patch
        corpus = _load_corpus()
        auto = record(_UINT64_REPLAY_BUNDLE["auto"])
        original = zlib.decompress(base64.b64decode(text(auto["encoded"]), validate=True))
        self.assertEqual(len(original), integer(auto["bytes"]))
        self.assertEqual(hashlib.sha256(original).hexdigest(), auto["sha256"])
        historical = record(parse_json(original))
        self.assertEqual(record(historical["request"])["sequence"], 11382)
        result = json_object(historical["result"])
        body = json_object(result["structured_content"])
        plan = json_object(body["plan"])
        plan["current_first_heir_reproductive_inputs_v1"] = {
            "conception_pair_inputs": {"pairs": [
                {"conditional_base_stage": {"base_raw": 2**53 + 1}},
                {"conditional_base_stage": {"base_raw": -(2**63)}}]}}
        body["plan"] = plan
        result["structured_content"] = body
        with self.assertRaisesRegex(ValueError, "JSON integer loses precision"):
            core._json_bytes(result)
        frozen_scope = dict(vars(core))
        exec("from __future__ import annotations\n" + text(_UINT64_REPLAY_BUNDLE["legacy"]),
             frozen_scope)
        legacy = frozen_scope["call_tool"]
        self.assertIsInstance(legacy, FunctionType)
        peaks: list[int] = []
        with _owned_workspace() as workspace:
            for legacy_enabled in (True, False):
                with _isolated_modules():
                    harness = _make_harness(workspace, corpus,
                        name="legacy-cache" if legacy_enabled else "opaque-result", with_anchor=True)
                    asyncio.run(harness.dispatch(harness.request("SEM")))
                    asyncio.run(_dispatch_actual_cap(harness))
                    self.assertEqual(_phase_value(harness), "ready")
                    _install_original_auto_postcheck(harness)
                    transport = _Int64RecordedTransport(result)
                    harness.transport = transport
                    request = harness.request("AUTO")
                    if legacy_enabled:
                        with patch.object(core.GuardedCurrentSavedSessionV1, "call_tool", legacy):
                            asyncio.run(harness.dispatch(request, submit=False))
                    else:
                        asyncio.run(harness.dispatch(request, submit=False))
                    self.assertEqual(transport.calls, 1)
                    self.assertEqual(transport.dumps, [1])
                    seq = integer(request["sequence"])
                    response = harness.root / "p37-responses" / f"{seq:04d}-1-result.json"
                    marker = harness.root / "p37-queue" / f"{seq:04d}-after-result.json"
                    row = record(parse_json(response.read_bytes()))
                    if legacy_enabled:
                        self.assertIn("JSON integer loses precision", str(row["client_error"]))
                        self.assertIsNotNone(getattr(harness.queue, "halted"))
                        self.assertFalse(marker.exists())
                        first = _pin(harness.root / "ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json")
                        before = transport.calls
                        with self.assertRaises(ValueError):
                            core.guard_current_saved_request_v1(harness.queue, request,
                                runtime_root=harness.root)
                        self.assertEqual(transport.calls, before)
                        self.assertEqual(_pin(Path(first.path)), first)
                    else:
                        self.assertIsNone(row.get("client_error"))
                        self.assertTrue(marker.is_file(), str(getattr(harness.queue, "halt_cause")))
                        self.assertIsNone(getattr(harness.queue, "halted"))
                        saved_body = record(record(row["result"])["structured_content"])
                        pair_values = rows(record(record(record(saved_body["plan"])[
                            "current_first_heir_reproductive_inputs_v1"])["conception_pair_inputs"])["pairs"])
                        values = [record(record(pair)["conditional_base_stage"])["base_raw"]
                                  for pair in pair_values]
                        self.assertEqual(values, [2**53 + 1, -(2**63)])
                        self.assertTrue(all(type(value) is int for value in values))
                        observation = record(getattr(harness.queue, "last_auto_observation"))
                        self.assertIs(observation["primitive_accepted"], True)
                        self.assertIs(observation["business_success_inferred"], False)
                        state = core._PERMIT_STATES[id(harness.queue)]
                        self.assertIsNone(state.last_semantic_result)
                    peaks.append(workspace.peak)
                    _remove_owned_child(workspace, harness.root)
        print("ORIGINAL_QUEUE_NATIVE_INT64", {"machine_id": core.current_execution_machine_id_v1(),
            "historical_subject_machine_id": SUBJECT, "historical_AUTO_sequence": 11382,
            "actual11386_result_recovered": False, "native_RPC_calls": 0,
            "legacy_cache_failed_after_one_return": True, "new_original_postcheck_passed": True,
            "ordinary_cycle_credit": 0, "peak_allocation_upper_bytes": max(peaks)})



class HistoricalReplaySourceBoundaryTests(unittest.TestCase):
    def test_resolver_uses_explicit_manifest_and_original_sources(self) -> None:
        sdk = _test_sdk_sources()
        root = REPO / "ck3_autonomous_player/src"
        reader = _ArchiveReader()
        files: list[JsonValue] = []
        for relative, ref in (
            ("xar_autoplayer/bridge/mcp_tool_result_contract_v1.py", sdk.sdk_result_contract),
            ("xar_autoplayer/campaign_score_cadence_v1.py", sdk.sdk_score_cadence),
            ("xar_autoplayer/campaign_development_score_v1.py", sdk.sdk_score_model)):
            reader.put(ref.path, Path(ref.path).read_bytes())
            files.append({"relative": relative, "bytes": ref.bytes, "sha256": ref.sha256})
        machine = core.current_execution_machine_id_v1()
        manifest: JsonObject = {"schema": "root.ck3.final-sdk-freeze/v1",
            "status": "FINAL_SOURCE_FROZEN", "machine_id": machine,
            "sdk_generation": "P37C23", "source_root": str(root), "files": files}
        def resolve(value: JsonObject) -> HistoricalReplaySdkSourcesV1:
            reference = reader.put(str(REPO / ".sdk-replay-manifest-not-created.json"), _wire(value))
            return replay.resolve_historical_replay_sdk_sources_v1(
                sdk_base_ref=reference, expected_machine_id=machine, reader=reader)
        resolved = resolve(manifest)
        self.assertEqual(resolved, sdk)
        self.assertEqual(replay._load_corpus(historical_fixture_ref=_pin(DATA),
            sdk_sources=resolved).originals, _load_corpus().originals)
        for key, invalid in (("machine_id", "wrong-machine"), ("status", "draft"),
                             ("files", []), ("sdk_generation", None)):
            changed = copy.deepcopy(manifest)
            changed[key] = invalid
            with self.subTest(field=key), self.assertRaises(ValueError):
                resolve(changed)
        for invalid_size in (True, 42.0):
            changed = copy.deepcopy(manifest)
            changed_files = rows(changed["files"])
            first = record(changed_files[0])
            first["bytes"] = invalid_size
            changed_files[0] = json_object(first)
            changed["files"] = json_value(changed_files)
            with self.subTest(bytes=invalid_size), self.assertRaises(ValueError):
                resolve(changed)

    def test_explicit_source_and_archive_pin_drift_are_rejected(self) -> None:
        sdk = _test_sdk_sources()
        with self.assertRaises(ValueError):
            replay._load_corpus(historical_fixture_ref=replace(_pin(DATA), sha256="0" * 64),
                                sdk_sources=sdk)
        wrong = replace(sdk, sdk_score_cadence=sdk.sdk_result_contract)
        with self.assertRaises(ValueError):
            replay._load_corpus(historical_fixture_ref=_pin(DATA), sdk_sources=wrong)

class QueueGuardInstallationTests(unittest.TestCase):
    """Execute the actual wrappers and admission parser without filesystem fixtures."""

    def test_guarded_base_then_child_override_cannot_bypass_request_guard(self) -> None:
        hits: list[str] = []

        class Base:
            next_sequence = False
            _current_saved_active_permit_v1 = None

            def check_before(self, tool: object, arguments: object) -> None:
                hits.append("base_check")

            async def call(self, session: core.CurrentSavedOriginalSessionV1,
                           request: object, path: Path) -> object:
                hits.append("base_call")
                return None

        class Session:
            async def call_tool(self, name: str, arguments: JsonObject, *,
                                read_timeout_seconds: float) -> core.CurrentSavedToolResultV1:
                raise AssertionError("transport must not run")

        core.install_current_saved_queue_guard_v1(Base, runtime_root=REPO)

        class Child(Base):
            def check_before(self, tool: object, arguments: object) -> None:
                hits.append("child_check")

            async def call(self, session: core.CurrentSavedOriginalSessionV1,
                           request: object, path: Path) -> object:
                hits.append("child_call")
                return None

        core.install_current_saved_queue_guard_v1(Child, runtime_root=REPO)
        child = Child()
        with self.assertRaises(ValueError):
            asyncio.run(child.call(Session(), {"sequence": False,
                "tool": core.CAPABILITIES_TOOL, "arguments": {}}, REPO / "never-written"))
        with self.assertRaises(ValueError):
            child.check_before(core.CAPABILITIES_TOOL, {})
        self.assertEqual(hits, [])

    def test_same_class_idempotence_rejects_new_runtime_and_method_override(self) -> None:
        class Queue:
            def check_before(self, tool: object, arguments: object) -> None:
                return None

            async def call(self, session: core.CurrentSavedOriginalSessionV1,
                           request: object, path: Path) -> object:
                return None

        core.install_current_saved_queue_guard_v1(Queue, runtime_root=REPO)
        original = (Queue.call, Queue.check_before)
        self.assertIs(core.install_current_saved_queue_guard_v1(
            Queue, runtime_root=REPO), Queue)
        self.assertEqual((Queue.call, Queue.check_before), original)
        with self.assertRaisesRegex(ValueError, "cannot rebind runtime root"):
            core.install_current_saved_queue_guard_v1(Queue, runtime_root=REPO / "tools")

        async def replacement(self: object, session: core.CurrentSavedOriginalSessionV1,
                              request: object, path: Path) -> object:
            raise AssertionError("modified method must be rejected before use")

        setattr(Queue, "call", replacement)
        with self.assertRaisesRegex(ValueError, "methods changed"):
            core.install_current_saved_queue_guard_v1(Queue, runtime_root=REPO)

    def test_partial_override_inherits_original_under_a_new_guard(self) -> None:
        class Base:
            next_sequence = False
            _current_saved_active_permit_v1 = None

            def check_before(self, tool: object, arguments: object) -> None:
                raise AssertionError("original check must not run")

            async def call(self, session: core.CurrentSavedOriginalSessionV1,
                           request: object, path: Path) -> object:
                raise AssertionError("original call must not run")

        core.install_current_saved_queue_guard_v1(Base, runtime_root=REPO)

        class Child(Base):
            def check_before(self, tool: object, arguments: object) -> None:
                raise AssertionError("child check must not run")

        core.install_current_saved_queue_guard_v1(Child, runtime_root=REPO / "tools")
        self.assertIsNot(Child.call, Base.call)
        with self.assertRaises(ValueError):
            Child().check_before(core.CAPABILITIES_TOOL, {})


class RecordingParentPreparationTests(unittest.TestCase):
  def case(self, w: replay._Workspace, mode: str = "valid") -> tuple[ColdPlanV1, ColdQuoteV1, Path]:
    from tools.g2_saved_campaign import test_current_saved_campaign_cold_v1 as f
    root = w.root / "runtime"; root.mkdir()
    selected = {"valid": str(root / "recordings"), "outside": str(w.root / "recordings"),
          "relative": "recordings", "parent": str(root / "recordings" / "..")}[mode]
    profile = root / "ROOT-OBS-PROFILE-C23.json"; w.write(profile, _wire({"recording_root": selected}))
    plan = replace(f.plan(), machine_id=core.current_execution_machine_id_v1(),
           runtime_root=str(root), supervisor_spec_path=str(root / "SPEC.json"))
    output = [OutputRowV1(str(root / name), name, 1, "a"*64, "create-only", None)
         for name in plan.closure_entry_paths]
    pin = _pin(profile)
    output.append(OutputRowV1(pin.path, profile.name, pin.bytes, pin.sha256, "create-only", None))
    allocated = len(output)*4096
    quote = replace(f.CurrentSavedArtifactBudgetTests()._quote(plan, f.ref("plan")),
      runtime_root=str(root), files=tuple(output),
      campaign_score_junction=replace(f.score_junction(), path=str(root / "campaign-score")),
      logical_bytes=sum(r.bytes for r in output), allocation_upper=allocated,
      prepare_peak_upper=allocated + max(r.bytes for r in output) + 131072)
    return plan, quote, root

  def check(self, plan: ColdPlanV1, quote: ColdQuoteV1, root: Path) -> core.CurrentSavedRecordingParentV1:
    return core.prepare_current_saved_recording_parent_v1(
      plan, quote, approved_runtime_root=root, reader=LocalBasisReaderV1())

  def test_public_prepare_creates_parent(self) -> None:
    from contextlib import ExitStack
    from unittest import mock
    with _owned_workspace() as w:
      plan, quote, root = self.case(w)
      metadata = w.root / "metadata"; metadata.mkdir()
      p = w.root / "plan.json"; w.write(p, _wire(plan.to_wire()))
      quote = replace(quote, plan_ref=_pin(p))
      q = w.root / "quote.json"; w.write(q, _wire(quote.to_wire()))
      class ReachedOwner(Exception): pass
      with ExitStack() as stack:
        if os.name != "nt":  # POSIX seam; actual Windows parsers.
          stack.enter_context(mock.patch.object(core, "parse_plan_v1", return_value=plan))
          stack.enter_context(mock.patch.object(core, "parse_quote_v1", return_value=quote))
        stack.enter_context(mock.patch.object(core, "validate_current_saved_cold_owner_v1", side_effect=ReachedOwner))
        with self.assertRaises(ReachedOwner):
          core.prepare_current_saved_offline_v1(_pin(p), _pin(q),
            approved_runtime_root=root, approved_metadata_root=metadata,
            historical_fixture_root=w.root / "unread", historical_fixture_ref=_pin(p),
            expected_machine_id=plan.machine_id, expected_attempt_nonce=plan.attempt_nonce,
            expected_task_nonce=plan.task_nonce, reader=LocalBasisReaderV1())
      self.assertTrue((root / "recordings").is_dir())
      self.assertEqual(self.check(plan, quote, root), self.check(plan, quote, root))
      self.assertFalse((root / "ROOT-CURRENT-SAVED-PREPARED01.json").exists())

  def test_wrong_parent(self) -> None:
    for mode in ("outside", "relative", "parent", "valid"):
      with self.subTest(mode=mode), _owned_workspace() as w:
        plan, quote, root = self.case(w, mode)
        with self.assertRaises(ValueError):
          self.check(plan, quote, root.parent if mode == "valid" else root)
        self.assertFalse((root / "recordings").exists())

  def test_file_and_old_sid_rejected(self) -> None:
    for mode in ("file", "SID"):
      with self.subTest(mode=mode), _owned_workspace() as w:
        plan, quote, root = self.case(w); path = root / "recordings"
        if mode == "file": w.write(path, b"x")
        else: path.mkdir(); (path / "old-SID").mkdir()
        with self.assertRaises(ValueError): self.check(plan, quote, root)

  def test_reparse_rejected(self) -> None:
    with _owned_workspace() as w:
      plan, quote, root = self.case(w)
      path = root / "recordings"; target = w.root / "target"; target.mkdir()
      try:
        try: path.symlink_to(target, target_is_directory=True)
        except OSError:
          if os.name != "nt": raise
          import subprocess
          done = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(path), str(target)],
            capture_output=True, check=False, creationflags=0x08000000)
          self.assertEqual(done.returncode, 0, done.stderr)
        with self.assertRaises(ValueError): self.check(plan, quote, root)
      finally:
        if path.is_symlink(): path.unlink()
        elif path.exists(): path.rmdir()

if __name__ == "__main__":
    unittest.main()

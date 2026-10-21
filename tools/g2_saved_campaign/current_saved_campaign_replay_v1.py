"""Pinned historical cold-replay production implementation; no live credit."""
from __future__ import annotations

import ast

import asyncio

import base64

from collections.abc import Awaitable, Iterator

from contextlib import contextmanager

import copy

import ctypes

from dataclasses import dataclass, field, replace

from datetime import datetime, timezone

import hashlib

import json

import os

from pathlib import Path

import shutil

import sys

import tempfile

import time

import traceback

import textwrap

from types import FrameType, FunctionType, ModuleType

from typing import Literal, Protocol, runtime_checkable

import zlib

from tools.g2_saved_campaign.current_saved_basis_v1 import (
    BasisReaderV1, ExactRefV1, JsonObject, digest, integer, json_object,
    need, exact_read, parse_json, parse_ref, record, rows, text,
)

from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as core

from tools.g2_saved_campaign.prepare_current_saved_campaign_cold_v1 import (
    emit_current_saved_request_guards_v1,
)

from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
    LocalBasisReaderV1,
    project_current_saved_governance_resume_v1,
    load_current_saved_inputs_v1, cold_inputs_v1,
)

REPO = Path(__file__).resolve().parents[2]

DATA = Path(__file__).with_name("test_data") / "current_saved_sem11373_postcheck_v1.json"

DATA_SHA = "083c39f875f6b8f8464971d194decd242257fa6013d15bfccf37d0f2c0567b26"

SOFT = 917504

SUBJECT = "xenoamess-full-tower-eb9d2c1186"

FIRST_SEQUENCE = 11373

CURRENT_SEQUENCE = 11375

def _wire(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode()

def _pin(path: Path, maximum: int = 135168) -> ExactRefV1:
    before = path.stat()
    need(before.st_size <= maximum, "bounded fixture input")
    raw = path.read_bytes()
    after = path.stat()
    need((before.st_ino, before.st_dev, before.st_size, before.st_mtime_ns) ==
         (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns),
         "fixture source changed")
    return ExactRefV1(str(path.resolve()), len(raw), hashlib.sha256(raw).hexdigest())

@dataclass(frozen=True, slots=True)
class _Corpus:
    subject: str
    reference: ExactRefV1
    originals: dict[str, bytes]
    sources: dict[str, ExactRefV1]
    def payload(self, name: str) -> bytes:
        return self.originals[name]
    def object(self, name: str) -> dict[str, object]:
        return record(parse_json(self.payload(name)))

HISTORICAL_REPLAY_DATA_RELATIVE_PATH_V1 = "tools/g2_saved_campaign/test_data/current_saved_sem11373_postcheck_v1.json"
HISTORICAL_REPLAY_DATA_BYTES_V1 = 133421
HISTORICAL_REPLAY_DATA_SHA256_V1 = DATA_SHA

@dataclass(frozen=True, slots=True, kw_only=True)
class HistoricalReplaySdkSourcesV1:
    sdk_result_contract: ExactRefV1
    sdk_score_cadence: ExactRefV1
    sdk_score_model: ExactRefV1

def resolve_historical_replay_sdk_sources_v1(
    *, sdk_base_ref: ExactRefV1, expected_machine_id: str, reader: BasisReaderV1,
) -> HistoricalReplaySdkSourcesV1:
    """Resolve software-only replay dependencies from the qualified SDK manifest."""
    base = record(parse_json(exact_read(reader, sdk_base_ref, 1048576)))
    need(base.get("schema") == "root.ck3.final-sdk-freeze/v1"
         and base.get("status") == "FINAL_SOURCE_FROZEN"
         and base.get("machine_id") == text(expected_machine_id)
         and base.get("sdk_generation") == "P37C23", "qualified SDK replay source manifest")
    root = Path(text(base.get("source_root")))
    need(root.is_absolute(), "absolute SDK source root")
    root = root.resolve(strict=True)
    files = tuple(record(item) for item in rows(base.get("files")))
    def source(relative: str) -> ExactRefV1:
        matching = tuple(item for item in files if item.get("relative") == relative)
        need(len(matching) == 1, "one declared SDK replay source")
        row = matching[0]
        path = (root / relative).resolve(strict=True)
        need(path.is_relative_to(root), "contained SDK replay source")
        ref = ExactRefV1(path=str(path), bytes=integer(row.get("bytes"), 1, 65536),
                         sha256=digest(row.get("sha256")))
        exact_read(reader, ref, 65536)
        return ref
    return HistoricalReplaySdkSourcesV1(
        sdk_result_contract=source("xar_autoplayer/bridge/mcp_tool_result_contract_v1.py"),
        sdk_score_cadence=source("xar_autoplayer/campaign_score_cadence_v1.py"),
        sdk_score_model=source("xar_autoplayer/campaign_development_score_v1.py"))

def _load_corpus(
    *, historical_fixture_ref: ExactRefV1, sdk_sources: HistoricalReplaySdkSourcesV1,
) -> _Corpus:
    need(isinstance(sdk_sources, HistoricalReplaySdkSourcesV1), "typed SDK replay inputs")
    reference = parse_ref(historical_fixture_ref.to_wire())
    need(reference.bytes == HISTORICAL_REPLAY_DATA_BYTES_V1
         and reference.sha256 == HISTORICAL_REPLAY_DATA_SHA256_V1,
         "qualified historical fixture pin")
    reader = LocalBasisReaderV1()
    row = record(parse_json(exact_read(reader, reference, 135168)))
    need(row.get("schema") == "xar.current-saved-historical-sem11373-fixture/v1"
         and row.get("historical_subject_machine_id") == SUBJECT
         and row.get("historical_payloads_modified") is False
         and row.get("fresh_native_qualification") is False,
         "explicit historical source, never fresh native qualification")
    for key in ("ordinary_cycle_credit", "game_day_credit"):
        integer(row.get(key), 0, 0)
    payloads = record(row.get("payloads"))
    expected = {"semantic_response", "launch", "anchor", "seed", "material_cold_resume",
                "queue", "score", "startup_readiness", "halted_observer",
                "pending_requests", "sdk_lifecycle_contract", "checkpoint_cadence"}
    need(set(payloads) == expected, "complete finite historical payload set")
    originals: dict[str, bytes] = {}
    sources: dict[str, ExactRefV1] = {}
    for name in sorted(payloads):
        item = record(payloads[name], {"source_ref", "encoding", "encoded"})
        reference_item = parse_ref(item["source_ref"])
        need(item["encoding"] == "zlib-base64" and reference_item.bytes <= 1048576,
             "finite lossless historical payload")
        encoded = item["encoded"]
        need(isinstance(encoded, str) and 0 < len(encoded) <= 131072,
             "bounded historical compressed source text")
        if not isinstance(encoded, str):
            raise ValueError("historical base64 text required")
        packed = base64.b64decode(encoded, validate=True)
        decoder = zlib.decompressobj()
        raw = decoder.decompress(packed, reference_item.bytes + 1)
        need(decoder.eof and not decoder.unused_data and not decoder.unconsumed_tail
             and len(raw) == reference_item.bytes
             and hashlib.sha256(raw).hexdigest() == reference_item.sha256,
             "original bytes and source digest")
        originals[name], sources[name] = raw, reference_item
    repository = record(row.get("repository_sources"),
                        {"sdk_result_contract", "sdk_score_cadence"})
    declared = {
        "sdk_result_contract": ("ck3_autonomous_player/src/xar_autoplayer/bridge/mcp_tool_result_contract_v1.py",
                                sdk_sources.sdk_result_contract),
        "sdk_score_cadence": ("ck3_autonomous_player/src/xar_autoplayer/campaign_score_cadence_v1.py",
                             sdk_sources.sdk_score_cadence),
    }
    for name in sorted(repository):
        item = record(repository[name], {"repository_relative_path", "source_ref"})
        relative, supplied = declared[name]
        actual = parse_ref(supplied.to_wire())
        need(item["repository_relative_path"] == relative, "canonical historical SDK source role")
        expected_ref = parse_ref(item["source_ref"])
        raw = exact_read(reader, actual, 65536)
        need((actual.bytes, actual.sha256) == (expected_ref.bytes, expected_ref.sha256),
             "explicit SDK source equals historical Source32 bytes")
        originals[name], sources[name] = raw, expected_ref
    model = parse_ref(sdk_sources.sdk_score_model.to_wire())
    model_raw = exact_read(reader, model, 65536)
    need(model.bytes == 22816 and model.sha256 ==
         "ba4421fdc66048852e3c7a158a461e8fa2dad5d96c75904e4077e8797652dd4d",
         "original SDK score-model dependency")
    originals["sdk_score_model"], sources["sdk_score_model"] = model_raw, model
    return _Corpus(SUBJECT, reference, originals, sources)

@dataclass(slots=True)
class _Workspace:
    root: Path
    cluster: int
    peak: int = 0
    def measure(self) -> None:
        need(self.root.is_dir() and not self.root.is_symlink()
             and not getattr(self.root.lstat(), "st_file_attributes", 0) & 0x400,
             "owned ordinary fixture root")
        total = self.cluster * 2
        for path in self.root.rglob("*"):
            need(not path.is_symlink()
                 and not getattr(path.lstat(), "st_file_attributes", 0) & 0x400
                 and path.resolve(strict=True).is_relative_to(self.root),
                 "fixture reparse or escape")
            total += (self.cluster * 2 if path.is_dir() else
                      (path.stat().st_size + self.cluster - 1) // self.cluster * self.cluster)
        self.peak = max(self.peak, total)
        need(total <= SOFT, "finite fixture soft allocation")
    def write(self, path: Path, raw: bytes, *, replace_existing: bool = False) -> None:
        need(path.parent.resolve(strict=True).is_relative_to(self.root)
             and len(raw) <= 65536, "bounded owned fixture write")
        if replace_existing:
            need(path.is_file() and not path.is_symlink(), "replace only owned existing file")
        with path.open("wb" if replace_existing else "xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        need(path.read_bytes() == raw, "owned fixture fsync and exact readback")
        self.measure()
    def atomic(self, path: object, value: object, *, replace: bool = False,
               limit: int | None = None) -> None:
        need(isinstance(path, Path), "original writer supplies a Path")
        if not isinstance(path, Path):
            raise TypeError("fixture Path required")
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        need(limit is None or len(raw) <= integer(limit, 1), "original bounded output")
        self.write(path, raw, replace_existing=replace and path.exists())

def _fixture_parent() -> Path:
    configured = os.environ.get("XAR_PREFLIGHT_FIXTURE_ROOT")
    if configured:
        root = Path(configured).resolve()
        need(root.is_absolute() and root.name ==
             "2026-10-21-current-saved-cap-pretransport-fixture01",
             "coordinator supplied exact owned fixture")
        return root
    need(os.environ.get("GITHUB_ACTIONS") == "true",
         "local fixture requires coordinator lease and XAR_PREFLIGHT_FIXTURE_ROOT")
    root = REPO / ".ci-current-saved-preflight-fixture"
    need(not root.exists(), "CI fixture is create-only")
    return root

def _allocation_unit(path: Path) -> int:
    if os.name != "nt":
        result = _invoke(getattr(os, "statvfs"), path)
        return integer(getattr(result, "f_frsize"), 1)
    library: object = ctypes.WinDLL("kernel32", use_last_error=True)
    function: object = getattr(library, "GetDiskFreeSpaceW")
    pointer = ctypes.POINTER(ctypes.c_uint32)
    setattr(function, "argtypes", [ctypes.c_wchar_p, pointer, pointer, pointer, pointer])
    setattr(function, "restype", ctypes.c_int)
    sectors, sector_bytes = ctypes.c_uint32(), ctypes.c_uint32()
    free, total = ctypes.c_uint32(), ctypes.c_uint32()
    result = _invoke(function, path.anchor, ctypes.byref(sectors),
                     ctypes.byref(sector_bytes), ctypes.byref(free), ctypes.byref(total))
    need(type(result) is int and result != 0, "actual fixture allocation unit")
    return integer(sectors.value, 1) * integer(sector_bytes.value, 1)

@contextmanager
def _owned_workspace(*, approved_root: Path | None = None) -> Iterator[_Workspace]:
    root = _fixture_parent() if approved_root is None else approved_root.resolve()
    need(root.is_absolute() and (root.name ==
         "2026-10-21-current-saved-cap-pretransport-fixture01"
         or root == REPO / ".ci-current-saved-preflight-fixture"),
         "exact coordinator-owned local or portable CI fixture")
    need(not root.exists(), "sole fixture coordinator; root must be absent")
    need(root.parent.is_dir() and not root.parent.is_symlink(), "ordinary owned parent")
    root.mkdir()
    previous = {key: os.environ.get(key) for key in ("TMP", "TEMP", "TMPDIR")}
    old_temp = tempfile.tempdir
    for key in previous:
        os.environ[key] = str(root)
    tempfile.tempdir = str(root)
    workspace = _Workspace(root, _allocation_unit(root))
    try:
        workspace.measure()
        yield workspace
    finally:
        try:
            workspace.measure()
        finally:
            try:
                need(root.resolve(strict=True) == root and root.is_dir()
                     and not getattr(root.lstat(), "st_file_attributes", 0) & 0x400,
                     "exact owned cleanup")
                shutil.rmtree(root)
                need(not root.exists(), "fixture finally absent")
            finally:
                tempfile.tempdir = old_temp
                for key, value in previous.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

@runtime_checkable
class _Function(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> object: ...

def _invoke(value: object, *args: object, **kwargs: object) -> object:
    need(isinstance(value, _Function), "original pinned callable")
    if not isinstance(value, _Function):
        raise TypeError("callable required")
    return value(*args, **kwargs)

@runtime_checkable
class _AsyncFunction(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> Awaitable[object]: ...

async def _await_invoke(value: object, *args: object, **kwargs: object) -> object:
    need(isinstance(value, _AsyncFunction), "original pinned async callable")
    if not isinstance(value, _AsyncFunction):
        raise TypeError("async callable required")
    return await value(*args, **kwargs)

def _namespace(module: ModuleType) -> dict[str, object]:
    return vars(module)

def _selected_source(raw: bytes, function_names: set[str],
                     class_methods: dict[str, set[str]] | None = None) -> str:
    source = raw.decode()
    tree = ast.parse(source)
    selected: list[str] = []
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.name in function_names:
                part = ast.get_source_segment(source, node)
                need(part is not None, "exact selected original source")
                if part is None:
                    raise ValueError("original source")
                selected.append(part)
                found.add(node.name)
            if isinstance(node, ast.ClassDef) and class_methods and node.name in class_methods:
                for method in node.body:
                    if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name in class_methods[node.name]:
                        part = ast.get_source_segment(source, method)
                        need(part is not None, "exact selected original method")
                        if part is None:
                            raise ValueError("original method")
                        selected.append(textwrap.dedent(' ' * method.col_offset + part))
                        found.add(node.name + "." + method.name)
    expected = set(function_names)
    if class_methods:
        expected |= {name + "." + method for name, methods in class_methods.items() for method in methods}
    need(found == expected, "all required original definitions selected")
    return "from __future__ import annotations\n\n" + "\n\n".join(selected) + "\n"

def _module(name: str, path: Path, source: bytes, workspace: _Workspace,
            bindings: dict[str, object] | None = None) -> ModuleType:
    workspace.write(path, source)
    module = ModuleType(name)
    module.__file__ = str(path)
    module.__package__ = name.rpartition(".")[0]
    namespace = _namespace(module)
    if bindings:
        namespace.update(bindings)
    sys.modules[name] = module
    exec(compile(source, str(path), "exec"), namespace)
    return module

@contextmanager
def _isolated_modules() -> Iterator[None]:
    names = ("root_", "p51_resident_", "startup_readiness_v1", "pending_requests_v1", "xar_autoplayer", "owner_response_")
    before = {key: value for key, value in sys.modules.items()
              if any(key.startswith(prefix) for prefix in names)}
    try:
        yield
    finally:
        for key in tuple(sys.modules):
            if any(key.startswith(prefix) for prefix in names):
                sys.modules.pop(key)
        sys.modules.update(before)

def _package(name: str, search: Path) -> ModuleType:
    module = ModuleType(name)
    module.__package__ = name
    module.__path__ = [str(search)]
    sys.modules[name] = module
    return module

def _subject_machine() -> str:
    # HistoricalSubjectIdentity is confined to isolated score replay imports.
    # The production core still reads its actual execution machine directly.
    return SUBJECT

def _noop(*args: object, **kwargs: object) -> None:
    return None

def _project(row: object, body: object) -> JsonObject:
    return {"historical_display_omitted": True}

def _control(label: object, function: object, *args: object, **kwargs: object) -> object:
    return _invoke(function, *args, **kwargs)

def _failed_fields(queue: object, request: object) -> object:
    # Pure receipt formatter from the repository, not a queue business guard.
    from tools.g2_saved_campaign import full_batch_timing_v1
    return _invoke(full_batch_timing_v1.failed_full_row_fields_v1, queue, request)

class _LoopClock:
    def __init__(self) -> None:
        self.completed = asyncio.Event()
    async def sleep(self, seconds: float) -> None:
        need(seconds == .25, "one unchanged dispatch poll")
        self.completed.set()
        await asyncio.Event().wait()

@dataclass(frozen=True, slots=True)
class _RecordedResult:
    value: JsonObject
    def model_dump(self, *, mode: Literal["json"]) -> JsonObject:
        need(mode == "json", "original transport JSON projection")
        return copy.deepcopy(self.value)

@dataclass(slots=True)
class _RecordedTransport:
    result: JsonObject
    calls: int = 0
    fail: bool = False
    async def __call__(self, tool: str, arguments: JsonObject,
                       budget: float) -> _RecordedResult:
        need(type(budget) is float and budget > 0 and arguments == {},
             "recorded transport receives exact bounded request")
        self.calls += 1
        if self.fail:
            raise RuntimeError("controlled offline transport failure")
        return _RecordedResult(copy.deepcopy(self.result))

class _ResourceBoundary:
    """Only disk/time/presentation boundaries; business methods are original AST."""
    def __init__(self, workspace: _Workspace, seed: JsonObject,
                 launch: dict[str, object], admission: JsonObject, governance: JsonObject) -> None:
        self.workspace = workspace
        self.next_sequence = FIRST_SEQUENCE
        self.launch = launch
        self._normal_cold: JsonObject = {
            "phase": "semantic", "admission": admission, "seed": seed,
            "checkpoint": json_object(seed["actual_saved_checkpoint"]),
            "governance": copy.deepcopy(governance), "prelaunch": {},
        }
        self.expected_lifecycle_binding = record(seed["actual_saved_checkpoint"]).get("succession_lifecycle")
        self.initial_camera: object = None
        self.initial_frame: object = None
        self.initial_save: object = None
        self.semantic: object = None
        self.current_attempt: object = None
        self.halted: object = None
        self.halt_cause: object = None
        self.held_control: object = None
        self.full_loop_state: object = None
        self.last_guard_observation: object = None
        self._current_saved_active_permit_v1: object = None
        self.checkpoint_bootstrap_verified = False
        self.capabilities_verified = False
        self.cold_readiness_verified = False
        self.recording_paused = False
        self.checkpoint_mode = True
        self.camera_attempted = False
        self.frontend_done = 3
        self.robert_key = "robert"
        self.zero_day_preparation = False
    def guard(self, *, reserve: bool = True) -> None:
        self.workspace.measure()
    def check_after(self, tool: object, arguments: object, body: object) -> None:
        raise ValueError("unexpected offline ordinary postcheck")
    def persist_loop_state(self) -> None:
        raise ValueError("historical replay does not persist live loop state")

@dataclass(slots=True)
class _Harness:
    workspace: _Workspace
    corpus: _Corpus
    root: Path
    current_next_sequence: int
    queue: object
    namespace: dict[str, object]
    transport: _RecordedTransport
    clock: _LoopClock
    cold_class: object
    score_function: object
    startup_function: object
    score_calls: int = 0
    check_after_calls: int = 0
    startup_calls: int = 0
    dispatch_calls: int = 0
    closed_input_calls: int = 0
    classifier_loader_calls: int = 0
    persistence_events: list[str] = field(default_factory=list)
    profile_frames: list[FrameType] = field(default_factory=list)
    def count_call(self, frame: FrameType, event: str, arg: object) -> None:
        if event != "call":
            return
        if frame.f_code in (load_current_saved_inputs_v1.__code__, cold_inputs_v1.__code__):
            self.closed_input_calls += 1
        if frame.f_code is getattr(self.namespace.get("load_cold_result_classifier"), "__code__", None):
            self.classifier_loader_calls += 1
        observed = (getattr(self.score_function, "__code__", None),
                    getattr(self.startup_function, "__code__", None),
                    getattr(getattr(self.cold_class, "check_after", None), "__code__", None))
        if frame.f_code not in observed or any(previous is frame for previous in self.profile_frames):
            return
        # Python profiles coroutine resumption as another call event. Retain
        # only these three bounded frames to count actual function entries.
        need(len(self.profile_frames) < 128, "finite original callable observations")
        self.profile_frames.append(frame)
        if frame.f_code is getattr(self.score_function, "__code__", None):
            self.score_calls += 1
        if frame.f_code is getattr(self.startup_function, "__code__", None):
            self.startup_calls += 1
        if frame.f_code is getattr(getattr(self.cold_class, "check_after", None), "__code__", None):
            self.check_after_calls += 1
    def request(self, kind: str, sequence: int | None = None) -> JsonObject:
        seq = integer(getattr(self.queue, "next_sequence"), 1) if sequence is None else sequence
        if kind == "FULL":
            return {"sequence": seq, "command": "full_loop", "arguments": {"max_turns": 1}}
        tools = {"SEM": core.SEMANTIC_TOOL, "CAP": core.CAPABILITIES_TOOL,
                 "AUTO": "ck3_auto_turn"}
        return {"sequence": seq, "tool": tools[kind], "arguments": {}}
    def publish(self, row: JsonObject) -> None:
        self.workspace.write(self.root / "p37-requests" /
                             f"{integer(row['sequence'], 1):04d}-1-result.json", _wire(row))
    async def dispatch(self, request: JsonObject, *, submit: bool = True) -> None:
        self.clock = _LoopClock()
        self.namespace["asyncio"] = self.clock
        if submit:
            permit = core.submit_queue_readiness_request_v1(
                self.queue, request, runtime_root=self.root, publish=self.publish)
        else:
            self.publish(request)
            # This is only a local recorded transport. Receiver hooks must
            # reject a direct inbox bypass before reaching this wrapper.
            permit = None
        session = _UnexpectedTransport(self.transport)
        loop = _await_invoke(self.namespace["run_request_loop"], self.queue, session)
        task = asyncio.create_task(loop)
        self.dispatch_calls += 1
        original_profile = sys.getprofile()
        sys.setprofile(self.count_call)
        try:
            completed = asyncio.create_task(self.clock.completed.wait())
            done, _ = await asyncio.wait({task, completed}, timeout=15,
                                         return_when=asyncio.FIRST_COMPLETED)
            need(bool(done), "one bounded original dispatch iteration")
            if task in done:
                task.result()
            else:
                need(completed.result(), "original dispatch reached poll boundary")
        finally:
            sys.setprofile(original_profile)
            if not task.done():
                task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            if not completed.done():
                completed.cancel()
            try:
                await completed
            except asyncio.CancelledError:
                pass
        self.workspace.measure()

@dataclass(slots=True)
class _UnexpectedTransport:
    recorded: _RecordedTransport
    async def call_tool(self, name: str, arguments: JsonObject, *,
                        read_timeout_seconds: float) -> _RecordedResult:
        return await self.recorded(name, arguments, float(read_timeout_seconds))

def _make_harness(workspace: _Workspace, corpus: _Corpus, *,
                  name: str, with_anchor: bool, current_next_sequence: int = CURRENT_SEQUENCE,
                  raw_governance: object | None = None,
                  cold_receiver_source: bytes | None = None) -> _Harness:
    current_next_sequence = integer(current_next_sequence, FIRST_SEQUENCE + 1)
    root = workspace.root / name
    root.mkdir()
    for directory in ("p37-queue", "p37-requests", "p37-responses",
                      "p37-display-responses", "campaign-score"):
        (root / directory).mkdir()
    workspace.measure()
    sdk_root = root / "isolated-sdk"
    _package("xar_autoplayer", sdk_root)
    _package("xar_autoplayer.bridge", sdk_root / "bridge")
    identity = ModuleType("xar_autoplayer.ck3_live_run_identity_v1")
    _namespace(identity)["current_machine_id"] = _subject_machine
    sys.modules[identity.__name__] = identity
    # Only explicit pinned SDK software inputs are visible to the isolated harness.
    _module("xar_autoplayer.bridge.mcp_tool_result_contract_v1",
            root / "result_contract.py", corpus.payload("sdk_result_contract"), workspace)
    lifecycle = corpus.payload("sdk_lifecycle_contract").decode()
    lifecycle_tree = ast.parse(lifecycle)
    constants = [node for node in lifecycle_tree.body if isinstance(node, (ast.Assign, ast.AnnAssign))
                 and node.lineno < 62]
    functions = [node for node in lifecycle_tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == "normalize_succession_lifecycle_binding_v1"]
    life_source = "from __future__ import annotations\nimport re\nfrom typing import Final\n" + "\n".join(
        text(ast.get_source_segment(lifecycle, node)) for node in constants + functions) + "\n"
    _module("xar_autoplayer.bridge.succession_transition_contract",
            root / "lifecycle_contract.py", life_source.encode(), workspace)
    _module("xar_autoplayer.campaign_development_score_v1",
            root / "score_model.py", corpus.payload("sdk_score_model"), workspace)
    _module("xar_autoplayer.campaign_score_cadence_v1",
            root / "score_cadence.py", corpus.payload("sdk_score_cadence"), workspace)
    score = _module("root_score_month_samples_c23", root / "score.py",
                    corpus.payload("score"), workspace)
    startup = _module("startup_readiness_v1", root / "startup_readiness_v1.py",
                      corpus.payload("startup_readiness"), workspace)
    _module("root_a10_observe_halted_state_v1", root / "halted_observer.py",
            corpus.payload("halted_observer"), workspace)
    pending = _module("pending_requests_v1", root / "pending_requests.py",
                      corpus.payload("pending_requests"), workspace)
    relay = ModuleType("root_p37c23_overlay_relay")
    _namespace(relay).update(relay_compact=_noop, error_projection=_project)
    sys.modules[relay.__name__] = relay
    from contextlib import nullcontext
    queue_material = emit_current_saved_request_guards_v1(corpus.payload("queue"), kind="queue")
    queue_source = _selected_source(queue_material, {
        "AdmissionEnded", "RecordingPaused", "now", "read", "decoded", "frame",
        "exception_evidence", "preserve_first_exception", "run_request_loop",
    }, {"FreshQueue": {"halt_request", "consume_sequence", "call_budget",
                        "check_before", "call", "full_loop"}})
    bindings: dict[str, object] = {
        "Path": Path, "json": json, "time": time, "traceback": traceback,
        "_current_saved_gate_v1": core, "JsonObject": JsonObject,
        "datetime": datetime, "timezone": timezone, "asyncio": asyncio,
        "N": root, "Q": root / "p37-queue", "INBOX": root / "p37-requests",
        "OUTBOX": root / "p37-responses", "atomic": workspace.atomic,
        "SEMANTIC": core.SEMANTIC_TOOL, "CAPABILITIES": core.CAPABILITIES_TOOL,
        "AUTO": "ck3_auto_turn", "METRICS": "root_current_runtime_metrics",
        "INITIAL_CAMERA": "ck3_set_camera", "SAVE": "ck3_save_checkpoint",
        "FRONTEND": ("f1", "f2", "f3"), "FRONTEND_TIMEOUT_SECONDS": 30,
        "FRONTEND_READ_RESERVE_SECONDS": 5, "REPLY_RESERVE": 65536,
        "ALLOWED": {core.SEMANTIC_TOOL, core.CAPABILITIES_TOOL, "ck3_auto_turn"},
        "READONLY_RESEARCH": (), "NODE_IDENTITY": "no-node",
        "_control_call_v1": _control, "_control_call_scope_v1": lambda value: nullcontext(),
        "_control_rpc_boundary_v1": _noop, "_record_full_rpc_row_v1": _noop,
        "display_projection": _project, "_failed_full_row_fields_v1": _failed_fields,
        "pending_request_paths": _namespace(pending)["pending_request_paths"],
    }
    module = _module("root_historical_queue", root / "queue_original_projection.py",
                     queue_source.encode(), workspace, bindings)
    env = _namespace(module)
    original_methods = {key: env[key] for key in
                        ("halt_request", "consume_sequence", "call_budget",
                         "check_before", "call", "full_loop")}
    base = type("_OriginalQueueMethods", (_ResourceBoundary,), original_methods)
    cold_source = _selected_source(corpus.payload("material_cold_resume")
                                   if cold_receiver_source is None else cold_receiver_source, {
        "require", "checked", "bind_opening", "project_opening",
        "make_normal_checkpoint_cold_queue_v1",
    })
    cold = _module("root_historical_cold", root / "cold_original_projection.py",
                   cold_source.encode(), workspace,
                   {"copy": copy, "json": json, "hashlib": hashlib, "Path": Path,
                    "MACHINE": SUBJECT, "_current_saved_gate_v1": core, "JsonObject": JsonObject})
    policy_path = root / "policy.json"
    workspace.write(policy_path, _wire({"entry_source_pins": [
        [str(root / "queue_original_projection.py"),
         hashlib.sha256(queue_source.encode()).hexdigest()]]}))
    freeze_path = root / "freeze.json"
    workspace.write(freeze_path, _wire({"canonical_preload_policy": _pin(policy_path).to_wire()}))
    launch = corpus.object("launch")
    admission: JsonObject = {
        "sdk_freeze": _pin(freeze_path).to_wire(), "next_sequence": FIRST_SEQUENCE,
        "new_Game": {"pid": integer(launch["pid"], 1),
                     "creation_filetime": str(launch["creation_filetime"]),
                     "creation_date": text(launch["creation_date"])},
    }
    admission_path = root / "admission.json"
    workspace.write(admission_path, _wire(admission))
    original_dispatch = env["run_request_loop"]
    cold_class = _invoke(_namespace(cold)["make_normal_checkpoint_cold_queue_v1"],
                         base, env, admission_path=admission_path)
    need(env["run_request_loop"] is not original_dispatch
         and isinstance(env["run_request_loop"], FunctionType),
         "actual factory installs original halted-observer dispatch")
    need(isinstance(cold_class, type), "actual factory returns a Queue class")
    if not isinstance(cold_class, type):
        raise TypeError("Queue type required")
    cold_class = core.install_current_saved_queue_guard_v1(cold_class, runtime_root=root)
    raw_governance = corpus.object("seed") if raw_governance is None else raw_governance
    raw_governance_record = record(raw_governance)
    governance = project_current_saved_governance_resume_v1(raw_governance_record,
        expected_completed_cycles=integer(raw_governance_record["completed_cycles"])).to_wire()
    queue = _invoke(cold_class, workspace, json_object(corpus.object("seed")), launch, admission, governance)
    machine = core.current_execution_machine_id_v1()
    workspace.write(root / "ROOT-LAUNCH-CONFIG-C23-A15.json", _wire({
        "historical_replay_context": {"historical_sequence": FIRST_SEQUENCE,
            "target_current_next_sequence": current_next_sequence, "ordinary_cycle_credit": 0},
        "cold_attempt": {"machine_id": machine, "attempt_nonce": "a" * 32,
                         "task_nonce": "b" * 32, "runtime_root": str(root)}}))
    workspace.write(root / "ROOT-ACTUAL-GAME-LAUNCH-C23.json", corpus.payload("launch"))
    pair = {"processes": [
        {"role": "sdk_queue", "pid": 101, "creation_filetime": "133000000000000001",
         "executable": "historical-not-started-queue"},
        {"role": "sdk_application", "pid": 102, "creation_filetime": "133000000000000002",
         "executable": "historical-not-started-application"}]}
    for filename in ("ROOT-ACTUAL-SDK-PROCESSES-PINNED-P37C23.json",
                     "ROOT-ACTUAL-SDK-PROCESS-GENERATIONS-P37C23.json"):
        workspace.write(root / filename, _wire(pair))
    if with_anchor:
        workspace.write(root / "campaign-score" / "CAMPAIGN-ANCHOR.json",
                        corpus.payload("anchor"))
    core.bind_current_saved_request_epoch_v1(queue, runtime_root=root,
                                           expected_machine_id=machine)
    result = json_object(corpus.object("semantic_response")["result"])
    return _Harness(workspace, corpus, root, current_next_sequence, queue, env, _RecordedTransport(result),
                    _LoopClock(), cold_class, _namespace(score)["observe_semantic"],
                    _namespace(startup)["startup_readiness_call"])

def _remove_owned_child(workspace: _Workspace, child: Path) -> None:
    workspace.measure()
    need(child.parent.resolve(strict=True) == workspace.root
         and child.resolve(strict=True).is_relative_to(workspace.root)
         and not child.is_symlink(), "exact finite fixture child cleanup")
    shutil.rmtree(child)
    workspace.measure()

def _phase_value(harness: _Harness) -> str:
    return text(record(getattr(harness.queue, "_normal_cold"))["phase"])

_A33_CAP_ENCODED = "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"

def _a33_capability_result() -> JsonObject:
    reference, raw = core.decode_current_saved_historical_payload_v1({
        "source_ref": core._A33_CAP_REF.to_wire(), "encoding": "zlib-base64",
        "encoded": _A33_CAP_ENCODED})
    need(reference == core._A33_CAP_REF, "actual CAP source identity")
    row = record(parse_json(raw))
    request = record(row.get("request"))
    result = record(row.get("result"))
    need(request == {"sequence": 11378, "tool": core.CAPABILITIES_TOOL, "arguments": {}}
         and row.get("client_error") is None and result.get("is_error") is False
         and result.get("result_type") == "complete", "actual successful historical CAP response")
    return json_object(result)

def _install_cap_persistence(harness: _Harness) -> None:
    """Execute the original Queue persistence/encoder with owned IO boundaries."""
    env = harness.namespace
    projection = _selected_source(harness.corpus.payload("queue"),
        {"atomic", "atomic_payload_v1", "load_cold_result_classifier", "classify_auto_result_credit_v1"},
        {"FreshQueue": {"persist_loop_state"}})
    source_path = harness.root / "original_cap_persistence.py"
    harness.workspace.write(source_path, projection.encode())
    from contextlib import nullcontext
    import uuid
    def before_write(path: object) -> None:
        need(isinstance(path, Path), "original producer path")
        if not isinstance(path, Path):
            raise ValueError("Path required")
        need(path.parent.resolve().is_relative_to(harness.workspace.root), "owned original atomic")
        harness.workspace.measure()
    env.update(os=os, uuid=uuid, ast=ast, hashlib=hashlib, _control_span_v1=lambda name: nullcontext(),
               _before_full_generated_write_v1=before_write)
    exec(compile(projection, str(source_path), "exec"), env)
    setattr(type(harness.queue), "persist_loop_state", env["persist_loop_state"])
    response = _module("owner_response_json_once_v1", harness.root / "response_original.py",
                       _N28_RESPONSE_SOURCE, harness.workspace)
    env["_owner_response_success_row_once_v1"] = _namespace(response)["prepare_success_response_row_v1"]
    original_atomic = env["atomic"]
    def observed_atomic(path: Path, value: object, *, replace: bool = False,
                        limit: int = 65536) -> object:
        outcome = _invoke(original_atomic, path, value, replace=replace, limit=limit)
        harness.persistence_events.append(path.name)
        return outcome
    env["atomic"] = observed_atomic
    reviewed_path = harness.root / "ROOT-P37C23-CLASSIFIER-PIN.json"
    harness.workspace.write(reviewed_path, _wire({"source": str(source_path),
        "sha256": hashlib.sha256(projection.encode()).hexdigest()}))
    cold = record(getattr(harness.queue, "_normal_cold"))
    admission = record(cold["admission"])
    admission["classifier_pin"] = _pin(reviewed_path).to_wire()
    cold["admission"] = admission
    setattr(harness.queue, "_normal_cold", cold)

async def _dispatch_actual_cap(harness: _Harness) -> None:
    _install_cap_persistence(harness)
    harness.transport.result = _a33_capability_result()
    await harness.dispatch(harness.request("CAP"))

async def _full_replay(workspace: _Workspace, corpus: _Corpus, *, current_next_sequence: int,
                       raw_governance: object, governance_source_ref: ExactRefV1,
                       cold_receiver_source: bytes, cold_receiver_ref: ExactRefV1,
                       ) -> core.HistoricalStartupDispatchReplayV1:
    followups: list[core.HistoricalBlockedFollowupV1] = []
    cases: list[core.HistoricalReplayCaseV1] = []
    with _isolated_modules():
        missing = _make_harness(workspace, corpus, name="missing", with_anchor=False, current_next_sequence=current_next_sequence,
            raw_governance=raw_governance, cold_receiver_source=cold_receiver_source)
        await missing.dispatch(missing.request("SEM"))
        cause = record(getattr(missing.queue, "halt_cause"))
        need(missing.current_next_sequence == current_next_sequence,
             "target basis sequence remains distinct from historical execution")
        need(_phase_value(missing) == "semantic" and missing.transport.calls == 1
             and missing.startup_calls == missing.check_after_calls == missing.score_calls == 1,
             "actual factory-installed dispatch/startup/postcheck/score failure")
        message = "founding score anchor requires actual paused1066 frame"
        need(cause.get("error_type") == "ValueError" and cause.get("message") == message,
             "original 1066-anchor postcheck failure reproduced")
        cases.append(core.HistoricalReplayCaseV1(
            "missing_anchor", "semantic", missing.transport.calls,
            "ValueError", message, missing.score_calls, False))
        evidence_paths: tuple[tuple[Literal["original_halt", "original_inflight", "first_exception"], Path], ...] = (
            ("original_halt", missing.root / "p37-queue" / f"ROOT-REQUEST-HALTED-{FIRST_SEQUENCE:04d}.json"),
            ("original_inflight", missing.root / "p37-queue" / f"INFLIGHT-{FIRST_SEQUENCE:04d}.json"),
            ("first_exception", missing.root / "ROOT-FIRST-QUEUE-EXCEPTION-P37C23.json"),
        )
        original = tuple((role, _pin(path)) for role, path in evidence_paths)
        halted_identity = getattr(missing.queue, "halted")
        for kind in ("SEM", "CAP", "AUTO", "FULL"):
            request = missing.request(kind)
            calls = missing.transport.calls
            published: list[JsonObject] = []
            try:
                core.submit_queue_readiness_request_v1(
                    missing.queue, request, runtime_root=missing.root, publish=published.append)
            except ValueError:
                pass
            else:
                raise ValueError("failed postcheck received another readiness permit")
            need(not published, "failed submit creates no new request")
            # Deliberately bypass publisher to exercise the actual installed
            # receiver, including FULL's separate dispatch branch.
            await missing.dispatch(request, submit=False)
            need(missing.transport.calls == calls and getattr(missing.queue, "halted") is halted_identity,
                 "postcheck failure cannot call transport or replace original halt")
            after = tuple((role, _pin(path)) for role, path in evidence_paths)
            need(original == after, "immutable original HALT/INFLIGHT/first exception")
            preserved = tuple(core.HistoricalPreservedEvidenceV1(role, before, actual)
                              for (role, before), (_, actual) in zip(original, after, strict=True))
            if kind == "SEM":
                label: Literal["SEM", "CAP", "AUTO", "FULL"] = "SEM"
            elif kind == "CAP":
                label = "CAP"
            elif kind == "AUTO":
                label = "AUTO"
            else:
                label = "FULL"
            followups.append(core.HistoricalBlockedFollowupV1(
                label, request, calls, missing.transport.calls, preserved))
        need((missing.root / "ROOT-CURRENT-HALT-P37.json").is_file()
             and record(parse_json((missing.root / "NEXT-SEQUENCE-P37.json").read_bytes())).get(
                 "failed_request_registered_without_readmission") is True,
             "failure flags remain, never erased for readmission")
        _remove_owned_child(workspace, missing.root)

        legacy = _make_harness(workspace, corpus, name="unprojected", with_anchor=True,
            current_next_sequence=current_next_sequence, raw_governance=raw_governance,
            cold_receiver_source=cold_receiver_source)
        raw = json_object(raw_governance)
        need("state" not in raw, "raw settled producer never supplies the legacy wrapper")
        cold = record(getattr(legacy.queue, "_normal_cold"))
        cold["governance"] = raw
        setattr(legacy.queue, "_normal_cold", cold)
        await legacy.dispatch(legacy.request("SEM"))
        need(_phase_value(legacy) == "capabilities", "original SEM consumer succeeds before the regression")
        await _dispatch_actual_cap(legacy)
        cause = record(getattr(legacy.queue, "halt_cause"))
        need(legacy.transport.calls == 2 and cause.get("error_type") == "KeyError"
             and cause.get("message") == "'state'" and _phase_value(legacy) == "capabilities"
             and not (legacy.root / "p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json").exists(),
             "actual raw governance reproduces CAP postresponse failure before BOUND")
        _remove_owned_child(workspace, legacy.root)
        positive = _make_harness(workspace, corpus, name="positive", with_anchor=True, current_next_sequence=current_next_sequence,
            raw_governance=raw_governance, cold_receiver_source=cold_receiver_source)
        anchor_path = positive.root / "campaign-score" / "CAMPAIGN-ANCHOR.json"
        anchor_before = _pin(anchor_path)
        await positive.dispatch(positive.request("SEM"))
        need(positive.current_next_sequence == missing.current_next_sequence == current_next_sequence,
             "both historical cases retain the caller target, never credit it as executed")
        need(_phase_value(positive) == "capabilities" and positive.transport.calls == 1
             and positive.startup_calls == positive.check_after_calls == positive.score_calls == 1
             and getattr(positive.queue, "halted") is None, "original ANCHOR copy reaches CAP phase")
        need(_pin(anchor_path) == anchor_before and not (anchor_path.parent / "months").exists(),
             "original anchor unchanged and no canonical score writes")
        cap = positive.request("CAP")
        core.guard_current_saved_request_v1(positive.queue, cap, runtime_root=positive.root)
        need(positive.transport.calls == 1, "settled SEM permits CAP without an extra probe call")
        cases.append(core.HistoricalReplayCaseV1(
            "original_anchor_copy", "capabilities", positive.transport.calls,
            None, None, positive.score_calls, True))
        await _dispatch_actual_cap(positive)
        need(positive.transport.calls == 2 and _phase_value(positive) == "ready"
             and positive.check_after_calls == 2 and positive.closed_input_calls == 0
             and positive.classifier_loader_calls == 1
             and getattr(positive.queue, "halted") is None,
             "original SEM and CAP transport, receiver postchecks and persistence complete")
        bound = record(parse_json((positive.root / "p37-queue/ROOT-C23-NORMAL-COLD-BOUND.json").read_bytes()))
        persisted = record(parse_json((positive.root / "p37-queue/ROOT-GOVERNANCE-RESULT-STATE.json").read_bytes()))
        projection = project_current_saved_governance_resume_v1(raw_governance,
            expected_completed_cycles=integer(record(raw_governance)["completed_cycles"]))
        need(persisted.get("state") == projection.state
             and persisted.get("pending_focus") == projection.pending_focus
             and bound.get("new_ordinary_cycle_credit") == 0
             and bound.get("AUTO_or_MET_replayed") is False,
             "original persisted null/object governance and zero-credit BOUND")
        events = positive.persistence_events
        need(events.index("ROOT-GOVERNANCE-RESULT-STATE.json")
             < events.index("ROOT-CUMULATIVE-LOOP-STATE.json")
             < events.index("ROOT-C23-NORMAL-COLD-BOUND.json"),
             "actual original atomic writes governance, loop state, then BOUND")
        contract = core.CurrentSavedColdQueueReplayV1(governance_source_ref, cold_receiver_ref,
            core._A33_CAP_REF, projection.to_wire(), projection.completed_cycles)
        _remove_owned_child(workspace, positive.root)
    semantic_postcheck = ExactRefV1(
        "D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/"
        "robert30-v20261019-campaign01/runtime-a24/diagnostics/offline-score-postcheck01/RESULT02.json",
        4987, "059511a61e3978c65551e8c0768a25970ec57dd96041725dc2980bf36148d65e")
    return core.HistoricalStartupDispatchReplayV1(
        corpus.reference, _pin(Path(__file__)), _pin(Path(core.__file__)),
        semantic_postcheck, corpus.subject, core.current_execution_machine_id_v1(),
        datetime.now(timezone.utc).isoformat(), FIRST_SEQUENCE, current_next_sequence,
        tuple(cases), tuple(followups), contract, workspace.peak)

def run_historical_startup_dispatch_replay_v1(
    *, fixture_root: Path, historical_fixture_ref: ExactRefV1,
    expected_execution_machine_id: str, current_next_sequence: int,
    raw_governance: object, governance_source_ref: ExactRefV1, governance_source: bytes,
    cold_receiver_source: bytes, cold_receiver_ref: ExactRefV1,
    sdk_sources: HistoricalReplaySdkSourcesV1,
) -> core.HistoricalStartupDispatchReplayV1:
    """Execute the pinned historical software path, never live qualification.

    The caller owns the finite fixture lease. The original subject identity is
    isolated from production identity; all public gates use the fresh executor.
    """
    need(expected_execution_machine_id == core.current_execution_machine_id_v1(),
         "historical runner execution machine is fresh and actual")
    current_next_sequence = integer(current_next_sequence, FIRST_SEQUENCE + 1)
    corpus = _load_corpus(historical_fixture_ref=historical_fixture_ref, sdk_sources=sdk_sources)
    need(corpus.reference == historical_fixture_ref, "runner binds exact historical corpus")
    raw = governance_source
    need(len(raw) <= 1048576 and hashlib.sha256(raw).hexdigest() == governance_source_ref.sha256
         and len(raw) == governance_source_ref.bytes
         and _wire(parse_json(raw)) == _wire(raw_governance), "exact original raw governance bytes")
    need(len(cold_receiver_source) == cold_receiver_ref.bytes
         and hashlib.sha256(cold_receiver_source).hexdigest() == cold_receiver_ref.sha256,
         "exact final quoted cold receiver bytes")
    project_current_saved_governance_resume_v1(raw_governance,
        expected_completed_cycles=integer(record(raw_governance).get("completed_cycles")))
    with _owned_workspace(approved_root=fixture_root) as workspace:
        result = asyncio.run(_full_replay(workspace, corpus,
            current_next_sequence=current_next_sequence, raw_governance=raw_governance,
            governance_source_ref=governance_source_ref,
            cold_receiver_source=cold_receiver_source, cold_receiver_ref=cold_receiver_ref))
    need(not workspace.root.exists(), "full historical fixture cleanup verified")
    return result

_N28_RESPONSE_SOURCE = b'"""Encode the full MCP result once while retaining the owner\'s exact row JSON."""\nfrom __future__ import annotations\n\nimport json\n\n\ndef json_utf8(value: object) -> bytes:\n    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")\n\n\ndef prepare_success_response_row_v1(*, started_at_utc: str, ended_at_utc: str,\n                                    elapsed_seconds: float, request: dict,\n                                    result: dict) -> tuple[dict, bytes]:\n    """Return the original row object plus exactly its existing compact UTF-8.\n\n    The full result is neither pruned nor normalized.  The original output-model\n    dump and downstream decoded/check_after functions remain the caller\'s work.\n    A text/JSON encoding error propagates to the caller\'s existing unknown-outcome\n    path, never to an RPC retry.  No file or backend operation occurs here.\n    """\n    encoded_result = json_utf8(result)\n    prefix = {"started_at_utc": started_at_utc, "ended_at_utc": ended_at_utc,\n              "elapsed_seconds": elapsed_seconds, "request": request}\n    count = len(encoded_result)\n    row = {**prefix, "result": result, "mcp_result_projection_json_utf8_bytes": count}\n    encoded_row = b"".join((json_utf8(prefix)[:-1], b\',"result":\', encoded_result,\n                           b\',"mcp_result_projection_json_utf8_bytes":\',\n                           str(count).encode("ascii"), b"}"))\n    return row, encoded_row\n'



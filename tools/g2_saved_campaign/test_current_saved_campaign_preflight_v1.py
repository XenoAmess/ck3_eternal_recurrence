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
)

REPO = Path(__file__).resolve().parents[2]
DATA = Path(__file__).with_name("test_data") / "current_saved_sem11373_postcheck_v1.json"
DATA_SHA = "083c39f875f6b8f8464971d194decd242257fa6013d15bfccf37d0f2c0567b26"
HARD = 1048576
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

def _load_corpus() -> _Corpus:
    reference = _pin(DATA)
    need(reference.bytes == 133421 and reference.sha256 == DATA_SHA,
         "qualified repository historical fixture pin")
    row = record(parse_json(DATA.read_bytes()))
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
    for name in sorted(repository):
        item = record(repository[name], {"repository_relative_path", "source_ref"})
        relative = Path(text(item["repository_relative_path"]))
        need(not relative.is_absolute() and ".." not in relative.parts,
             "contained portable repository source")
        path = (REPO / relative).resolve(strict=True)
        need(path.is_relative_to(REPO), "repository source escaped")
        expected_ref = parse_ref(item["source_ref"])
        actual = _pin(path)
        need((actual.bytes, actual.sha256) == (expected_ref.bytes, expected_ref.sha256),
             "repository source equals historical Source32 bytes")
        originals[name], sources[name] = path.read_bytes(), expected_ref
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

# Pinned original functions are untyped. This one boundary validates callable
# shape at runtime and returns object; callers validate every returned value.
@runtime_checkable
class _Function(Protocol):
    def __call__(self, *args: object, **kwargs: object) -> object: ...

class _HasFileno(Protocol):
    def fileno(self) -> int: ...

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
    names = ("root_", "startup_readiness_v1", "pending_requests_v1", "xar_autoplayer", "owner_response_")
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
                 launch: dict[str, object], admission: JsonObject) -> None:
        self.workspace = workspace
        self.next_sequence = FIRST_SEQUENCE
        self.launch = launch
        self._normal_cold: JsonObject = {
            "phase": "semantic", "admission": admission, "seed": seed,
            "checkpoint": json_object(seed["actual_saved_checkpoint"]),
            "governance": {"state": {}, "pending_focus": None}, "prelaunch": {},
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
    profile_frames: list[FrameType] = field(default_factory=list)
    def count_call(self, frame: FrameType, event: str, arg: object) -> None:
        if event != "call":
            return
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

def _make_harness(workspace: _Workspace, corpus: _Corpus, *,
                  name: str, with_anchor: bool, current_next_sequence: int = CURRENT_SEQUENCE) -> _Harness:
    current_next_sequence = integer(current_next_sequence, FIRST_SEQUENCE + 1)
    root = workspace.root / name
    root.mkdir()
    for directory in ("p37-queue", "p37-requests", "p37-responses",
                      "p37-display-responses", "campaign-score"):
        (root / directory).mkdir()
    workspace.measure()
    sdk_root = REPO / "ck3_autonomous_player" / "src" / "xar_autoplayer"
    _package("xar_autoplayer", sdk_root)
    _package("xar_autoplayer.bridge", sdk_root / "bridge")
    identity = ModuleType("xar_autoplayer.ck3_live_run_identity_v1")
    _namespace(identity)["current_machine_id"] = _subject_machine
    sys.modules[identity.__name__] = identity
    # Exact original SDK result/cadence bytes are loaded from repository pins.
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
    cold_source = _selected_source(corpus.payload("material_cold_resume"), {
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
    queue = _invoke(cold_class, workspace, json_object(corpus.object("seed")), launch, admission)
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

async def _full_replay(workspace: _Workspace, corpus: _Corpus, *, current_next_sequence: int) -> core.HistoricalStartupDispatchReplayV1:
    followups: list[core.HistoricalBlockedFollowupV1] = []
    cases: list[core.HistoricalReplayCaseV1] = []
    with _isolated_modules():
        missing = _make_harness(workspace, corpus, name="missing", with_anchor=False, current_next_sequence=current_next_sequence)
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
                raise AssertionError("failed postcheck received another readiness permit")
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
        positive = _make_harness(workspace, corpus, name="positive", with_anchor=True, current_next_sequence=current_next_sequence)
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
        _remove_owned_child(workspace, positive.root)
    semantic_postcheck = ExactRefV1(
        "D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep/"
        "robert30-v20261019-campaign01/runtime-a24/diagnostics/offline-score-postcheck01/RESULT02.json",
        4987, "059511a61e3978c65551e8c0768a25970ec57dd96041725dc2980bf36148d65e")
    return core.HistoricalStartupDispatchReplayV1(
        corpus.reference, _pin(Path(__file__)), _pin(Path(core.__file__)),
        semantic_postcheck, corpus.subject, core.current_execution_machine_id_v1(),
        datetime.now(timezone.utc).isoformat(), FIRST_SEQUENCE, current_next_sequence,
        tuple(cases), tuple(followups), workspace.peak)

def run_historical_startup_dispatch_replay_v1(
    *, fixture_root: Path, historical_fixture_ref: ExactRefV1,
    expected_execution_machine_id: str, current_next_sequence: int,
) -> core.HistoricalStartupDispatchReplayV1:
    """Execute the pinned historical software path, never live qualification.

    The caller owns the finite fixture lease. The original subject identity is
    isolated from production identity; all public gates use the fresh executor.
    """
    need(expected_execution_machine_id == core.current_execution_machine_id_v1(),
         "historical runner execution machine is fresh and actual")
    current_next_sequence = integer(current_next_sequence, FIRST_SEQUENCE + 1)
    corpus = _load_corpus()
    need(corpus.reference == historical_fixture_ref, "runner binds exact historical corpus")
    with _owned_workspace(approved_root=fixture_root) as workspace:
        result = asyncio.run(_full_replay(workspace, corpus, current_next_sequence=current_next_sequence))
    need(not workspace.root.exists(), "full historical fixture cleanup verified")
    return result


def _replay(current_next_sequence: int = CURRENT_SEQUENCE) -> core.HistoricalStartupDispatchReplayV1:
    return run_historical_startup_dispatch_replay_v1(
        fixture_root=_fixture_parent(), historical_fixture_ref=_pin(DATA),
        expected_execution_machine_id=core.current_execution_machine_id_v1(),
        current_next_sequence=current_next_sequence)

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
        self.assertEqual(len(corpus.originals), 14)
        self.assertEqual(corpus.object("anchor")["campaign_id"], "robert-first30-v20261019")
        self.assertNotEqual(record(corpus.object("seed")["campaign_goal_anchor"])["campaign_id"],
                            corpus.object("anchor")["campaign_id"])
        original = corpus.object("semantic_response")
        self.assertEqual(record(original["request"])["sequence"], FIRST_SEQUENCE)
        self.assertEqual(record(record(original["result"])["structured_content"])["date_raw"], 53279256)
        self.assertEqual(hashlib.sha256(corpus.payload("anchor")).hexdigest(),
                         corpus.sources["anchor"].sha256)

    def test_public_runner_rejects_noninteger_and_obsolete_target(self) -> None:
        for invalid in (True, 11375.0, FIRST_SEQUENCE, FIRST_SEQUENCE - 1):
            with self.subTest(target=invalid), self.assertRaises(ValueError):
                _invoke(run_historical_startup_dispatch_replay_v1,
                    fixture_root=REPO / ".ci-current-saved-preflight-fixture",
                    historical_fixture_ref=_pin(DATA),
                    expected_execution_machine_id=core.current_execution_machine_id_v1(),
                    current_next_sequence=invalid)

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
                                        None, None, 1, True)), negatives, 4096)
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
    reader.put(full.harness_ref.path, Path(__file__).read_bytes())
    reader.put(full.core_source_ref.path, Path(core.__file__).read_bytes())
    root = REPO / ".archive-boundary-not-created"
    basis = replace(_score_fixture_basis(corpus, root),
                    machine_id=full.execution_machine_id,
                    next_sequence=full.current_next_sequence)
    basis_ref = reader.put(str(root / "basis.json"), _wire(basis.to_wire()))
    replay_ref = reader.put(str(root / "actual-replay.json"), _wire(full.to_wire()))
    placeholder = reader.put(str(root / "unread-metadata.json"), b"{}")
    source_path = "tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py"
    names = tuple(sorted(CANONICAL_NAMES))
    plan = ColdPlanV1(
        full.execution_machine_id, full.observed_at_utc, full.observed_at_utc,
        str(root), str(root / "material"), placeholder, basis_ref, placeholder,
        placeholder, (SourceRowV1(full.core_source_ref, source_path),),
        names, names + (source_path,), (".",), placeholder, placeholder,
        str(root / "screen.json"), str(root / "spec.json"), "a" * 32, "b" * 32,
        "c" * 32, 32, placeholder, placeholder)
    plan_ref = reader.put(str(root / "plan.json"), _wire(plan.to_wire()))
    output: list[OutputRowV1] = []
    for key, name in (("material_cold_resume", "root_p37c23_cold_resume.py"),
                      ("score", "root_score_month_samples_c23.py")):
        current = reader.put(str(root / name), corpus.payload(key))
        output.append(OutputRowV1(current.path, name, current.bytes, current.sha256,
                                  "create-only", None))
    anchor = corpus.sources["anchor"]
    junction = CampaignScoreJunctionV1(
        str(root / "campaign-score"), str(Path(anchor.path).parent), True, "1", "1", anchor)
    quote = ColdQuoteV1(full.execution_machine_id, full.observed_at_utc,
        plan_ref, basis_ref, placeholder, placeholder, str(root), tuple(output),
        junction, names, names + (source_path,), (".",), 8, 1, 1, 1)
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


_N28_RESPONSE_SOURCE = b'"""Encode the full MCP result once while retaining the owner\'s exact row JSON."""\nfrom __future__ import annotations\n\nimport json\n\n\ndef json_utf8(value: object) -> bytes:\n    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")\n\n\ndef prepare_success_response_row_v1(*, started_at_utc: str, ended_at_utc: str,\n                                    elapsed_seconds: float, request: dict,\n                                    result: dict) -> tuple[dict, bytes]:\n    """Return the original row object plus exactly its existing compact UTF-8.\n\n    The full result is neither pruned nor normalized.  The original output-model\n    dump and downstream decoded/check_after functions remain the caller\'s work.\n    A text/JSON encoding error propagates to the caller\'s existing unknown-outcome\n    path, never to an RPC retry.  No file or backend operation occurs here.\n    """\n    encoded_result = json_utf8(result)\n    prefix = {"started_at_utc": started_at_utc, "ended_at_utc": ended_at_utc,\n              "elapsed_seconds": elapsed_seconds, "request": request}\n    count = len(encoded_result)\n    row = {**prefix, "result": result, "mcp_result_projection_json_utf8_bytes": count}\n    encoded_row = b"".join((json_utf8(prefix)[:-1], b\',"result":\', encoded_result,\n                           b\',"mcp_result_projection_json_utf8_bytes":\',\n                           str(count).encode("ascii"), b"}"))\n    return row, encoded_row\n'
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

if __name__ == "__main__":
    unittest.main()


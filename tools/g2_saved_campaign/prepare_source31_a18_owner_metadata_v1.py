"""Typed A18 owner metadata and Task boundary. Preparation only; no Task or RPC calls."""
from __future__ import annotations
import ast
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import json
from pathlib import Path
import re
import sys
from types import FunctionType, ModuleType
from typing import Callable, Literal, Protocol, TypedDict, cast

MACHINE = "xenoamess-full-tower-eb9d2c1186"
OWN = Path(__file__).resolve().parent
P = Path("D:/codex-ck3-demos/2026-10-14-robert-30year/continuation42-cold-prep")
O = P / "p51-fresh1066-v20261019-prepare01/c23-source23-native30-cold100"
TARGET = P / "robert30-v20261019-campaign01/runtime-a18"
PRIOR = TARGET.with_name("runtime-a17")
TASK = O / "tasks/spec-supervisor-a18"
ADAPTER_NAME = "prepare_source31_a18_cold_union_v1.py"
BINDING_NAME = "ROOT-NATIVE32-PRODUCTION-BINDING01.json"
FREEZE_NAME = "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json"
BOOT_NAME = "interactive_task_owner_a10_v1.py"
CONTRACT_NAME = "owner_prepare_contract_v1.py"
STAGE_NAME = "root_native30_supervisor_c23.py"
OUTPUT_NAMES = (
    "ROOT-C23-A18-ACTUAL-RECORDING-BINDING.json",
    "ROOT-P37C23-COLD-RESUME-ADMISSION.json",
    "ROOT-P37C23-OWNER-INPUT-PINS.json",
    "ROOT-C23-SDKOWNER-CREATE-ADMITTED.json",
)
BOOT_PIN = (30672, "7a36400ef563d05dcc309900e51970a87fcf5c01a09f6b92643c57ca3b2ec51b")
CONTRACT_PIN = (2615, "3d19624797c122960e52266a8bd5c89c6786cf3dfbdcdf0521e77228bcbb6c92")
LEGACY_PIN = (25193, "0e2befdca7cac51f13d9d7e4e85a5d66e5dad159eb127457207a3160072db004")
GENERIC_PIN = (20029, "0cc5041216bb50c0e79af4c41cae3844cce76dda5d888b91b37fe34bcde85b5e")
CLOSURE_PIN = (7191, "3ebbf5eb221814cab62bbef01ea0a6570a8da6a48420c064ca30155b5980aa53")
DLL_PIN = (19535872, "6c3a2e961c9c92225f1225252e08a73bd7fe67b1b280a1dd0132100b5e39c1cc")
PRODUCTION_PIN = (16886, "aace13ba74f871d7dd99c7b1b77bd2338f4f9a41c25402ef90e3f59b85dde81e")
Doc = dict[str, object]
Outputs = dict[Path, bytes]

class ExactRef(TypedDict):
    path: str
    bytes: int
    sha256: str

class RecordingRefsV1(TypedDict):
    request: ExactRef
    job: ExactRef
    started: ExactRef
    first_frame_admission: ExactRef
    publisher_started: ExactRef

class OwnerInputV1(TypedDict):
    schema: Literal["xar.C23-A18-cold-owner-metadata-input/v1"]
    machine_id: str
    execution_owner: Literal["Root"]
    root_direct_execution_release: Literal[True]
    observed_at_utc: str
    runtime_root: str
    cold_graph_plan: ExactRef
    cold_graph_quote: ExactRef
    full_storage_ref: ExactRef
    live_storage_ref: ExactRef
    actual_game: ExactRef
    sdk_freeze: ExactRef
    business_anchor: ExactRef
    mod_absence: ExactRef
    recording: RecordingRefsV1

class OwnerQuoteV1(TypedDict):
    schema: Literal["xar.C23-A18-owner-preparation/v1"]
    machine_id: str
    observed_at_utc: str
    status: Literal["RAM_READY_NOT_WRITTEN_NO_GATE_PUBLISHED"]
    producer: ExactRef
    adapter: ExactRef
    cold_graph_plan: ExactRef
    cold_graph_quote: ExactRef
    legacy_metadata_source: ExactRef
    outputs: list[ExactRef]
    publish_order: list[str]
    gate_must_be_last: Literal[True]
    runtime_graph_rows: Literal[145]
    next_sequence: Literal[10569]
    saved_cycles: Literal[4753]
    saved_days: Literal[5429]
    rollback_cycles: Literal[5]
    rollback_days: Literal[0]
    unknown10565_replayed: Literal[False]
    new_business_credit: Literal[0]
    original_wall_origin_reset: Literal[False]
    logical_bytes: int
    allocation_upper: int
    metadata_write_peak_upper: int
    legacy_quote: Doc

class MetadataAdapterV1(Protocol):
    __file__: str
    TARGET: Path
    MACHINE: str
    NATIVE32_OBSERVER_BINDING_NAME: str
    NATIVE32_ADAPTER_NAME: str
    def parse_plan(self, value: object) -> Mapping[str, object]: ...
    def metadata_source(self, plan_value: object, source: str) -> str: ...
    def metadata_scope(self, plan_value: object, namespace: Doc, runtime: Path) -> None: ...

class LegacyComposeV1(Protocol):
    def __call__(self, inputs: object) -> object: ...

class FileIdentityV1(TypedDict):
    volume_serial: str
    file_id: str

class SupervisorTaskV1(TypedDict):
    schema: Literal["xar.interactive-task-owner/v1"]
    role: Literal["supervisor"]
    machine_id: str
    nonce: str
    task_name: str
    sid: str
    session: int
    root: str
    cwd: str
    python: str
    pythonw: str
    python_file_id: FileIdentityV1
    pythonw_file_id: FileIdentityV1
    bootstrap: str
    bootstrap_sha256: str
    stage: str
    stage_sha256: str
    stage_args: list[str]
    stop_path: str
    env: dict[str, str]

class TaskCommandV1(TypedDict):
    machine_id: str
    operation: Literal["register", "inspect", "run"]
    argv: list[str]

def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError("A18 owner: " + message)

def record(value: object) -> Doc:
    if type(value) is not dict:
        raise ValueError("A18 owner: exact JSON object required")
    result: Doc = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("A18 owner: exact text keys required")
        result[key] = item
    return result

def text(value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError("A18 owner: nonempty text required")
    return value

def uint(value: object, maximum: int = 2**53 - 1, minimum: int = 0) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError("A18 owner: exact integer required")
    return value

def decimal(value: object, maximum: int = 2**64 - 1) -> str:
    result = text(value)
    need(re.fullmatch("(?:0|[1-9][0-9]*)", result) is not None and int(result) <= maximum,
         "canonical unsigned decimal identity")
    return result

def stamp(value: object) -> datetime:
    result = datetime.fromisoformat(text(value).replace("Z", "+00:00"))
    need(result.tzinfo is not None and result.utcoffset() == timedelta(0), "UTC timestamp")
    return result

def encode(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()

def parse_ref(value: object) -> ExactRef:
    row = record(value)
    need(set(row) == {"path", "bytes", "sha256"}, "one exact reference contract")
    path = text(row["path"])
    need(Path(path).is_absolute(), "absolute reference path")
    size = uint(row["bytes"], minimum=1)
    digest = text(row["sha256"])
    need(re.fullmatch("[0-9a-f]{64}", digest) is not None, "reference SHA")
    return {"path": path, "bytes": size, "sha256": digest}

def read_ref(value: object, limit: int = 1048576) -> bytes:
    reference = parse_ref(value)
    need(reference["bytes"] <= limit, "bounded exact input")
    path = Path(reference["path"])
    before = path.stat()
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
         "input identity changed during read")
    need(len(data) == reference["bytes"]
         and hashlib.sha256(data).hexdigest() == reference["sha256"], "exact input SHA")
    return data

def checked(value: object, limit: int = 1048576) -> Doc:
    return record(json.loads(read_ref(value, limit)))

def reference(path: Path, limit: int = 1048576) -> ExactRef:
    path = path.resolve(strict=True)
    before = path.stat()
    need(0 < before.st_size <= limit, "bounded existing leaf")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    after = path.stat()
    need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
         == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
         and len(data) == before.st_size, "leaf identity changed during pin")
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def fixed(path: Path, pin: tuple[int, str]) -> ExactRef:
    result = reference(path)
    need((result["bytes"], result["sha256"]) == pin, "historical source pin")
    return result

def parse_recording_refs_v1(value: object) -> RecordingRefsV1:
    row = record(value)
    need(set(row) == set(RecordingRefsV1.__annotations__), "five recording references")
    return {"request": parse_ref(row["request"]), "job": parse_ref(row["job"]),
            "started": parse_ref(row["started"]),
            "first_frame_admission": parse_ref(row["first_frame_admission"]),
            "publisher_started": parse_ref(row["publisher_started"])}

def parse_owner_inputs_v1(value: object, *, at_utc: datetime) -> OwnerInputV1:
    row = record(value)
    need(set(row) == set(OwnerInputV1.__annotations__), "one A18 owner input contract")
    need(row["schema"] == "xar.C23-A18-cold-owner-metadata-input/v1"
         and row["machine_id"] == MACHINE and row["execution_owner"] == "Root"
         and row["root_direct_execution_release"] is True, "explicit Root machine release")
    need(at_utc.tzinfo is not None and at_utc.utcoffset() == timedelta(0)
         and 0 <= (at_utc - stamp(row["observed_at_utc"])).total_seconds() <= 600,
         "fresh actual UTC observation")
    need(Path(text(row["runtime_root"])).resolve() == TARGET.resolve(), "A18 runtime")
    return {"schema": "xar.C23-A18-cold-owner-metadata-input/v1",
        "machine_id": MACHINE, "execution_owner": "Root",
        "root_direct_execution_release": True, "observed_at_utc": text(row["observed_at_utc"]),
        "runtime_root": str(TARGET), "cold_graph_plan": parse_ref(row["cold_graph_plan"]),
        "cold_graph_quote": parse_ref(row["cold_graph_quote"]),
        "full_storage_ref": parse_ref(row["full_storage_ref"]),
        "live_storage_ref": parse_ref(row["live_storage_ref"]),
        "actual_game": parse_ref(row["actual_game"]), "sdk_freeze": parse_ref(row["sdk_freeze"]),
        "business_anchor": parse_ref(row["business_anchor"]),
        "mod_absence": parse_ref(row["mod_absence"]),
        "recording": parse_recording_refs_v1(row["recording"])}

def metadata_adapter_v1(value: object, plan: Doc) -> MetadataAdapterV1:
    """One narrow dynamic boundary: verify module source and real callable signatures."""
    need(isinstance(value, ModuleType), "actual metadata adapter module")
    module = cast(ModuleType, value)
    source_ref = parse_ref(plan["union_producer"])
    need(Path(text(getattr(module, "__file__", None))).resolve() == Path(source_ref["path"]).resolve()
         and Path(source_ref["path"]).name == ADAPTER_NAME, "actual A18 adapter path")
    read_ref(source_ref, 65536)
    need(getattr(module, "TARGET", None) == TARGET and getattr(module, "MACHINE", None) == MACHINE
         and getattr(module, "NATIVE32_OBSERVER_BINDING_NAME", None) == BINDING_NAME,
         "adapter runtime/binding identity")
    signatures = {"parse_plan": ("value",),
                  "metadata_source": ("plan_value", "source"),
                  "metadata_scope": ("plan_value", "namespace", "runtime")}
    for name, arguments in signatures.items():
        function = getattr(module, name, None)
        need(isinstance(function, FunctionType)
             and tuple(inspect.signature(function).parameters) == arguments,
             "actual adapter callable signature: " + name)
    return cast(MetadataAdapterV1, module)

def validate_source31_owner_basis_v1(inputs: OwnerInputV1, adapter_value: object) -> tuple[MetadataAdapterV1, Doc]:
    initial = checked(inputs["cold_graph_plan"], 16384)
    adapter = metadata_adapter_v1(adapter_value, initial)
    plan = dict(adapter.parse_plan(initial))
    need(plan["schema"] == "xar.Source31-A18-complete-cold-input/v1"
         and plan["machine_id"] == MACHINE and plan["execution_owner"] == "Root"
         and plan["root_direct_execution_release"] is True, "actual Source31 plan")
    closed = checked(plan["closure_ref"], 16384)
    need(parse_ref(plan["closure_ref"]) == fixed(PRIOR / "ROOT-A17-ACTUAL-CLOSURE-INDEX01.json", CLOSURE_PIN),
         "actual A17 closed predecessor")
    game = record(closed["Game"])
    need(closed["schema"] == "xar.A17-clock-failure-closed/v1"
         and closed["machine_id"] == MACHINE
         and closed["status"] == "A17_CLOSED_UNKNOWN10565_NO_REPLAY"
         and game["forced_owned_job_cleanup"] is True and uint(game["exit_code"]) == 1
         and uint(game["Job_active_final"]) == 0 and closed["Tasks_absent"] is True
         and closed["screen116_released"] is True
         and record(closed["SDK_actual_exits"]) == {"sdk_queue": 1, "sdk_application": 0}
         and uint(closed["next_sequence"]) == 10569
         and uint(closed["saved_cycles"]) == 4753 and uint(closed["live_settled_cycles"]) == 4758
         and uint(closed["pending_cycle"]) == 4759 and uint(closed["saved_days"]) == 5429
         and uint(closed["new_day_credit"]) == 0 and uint(closed["late_native_scalar_day_credit"]) == 0
         and closed["current_failed_request_completion_proven"] is False
         and closed["old_request_replayed"] is False, "true forced/unknown predecessor")
    exits = record(closed["SDK_actual_exits"])
    need(uint(exits["sdk_queue"]) == 1 and uint(exits["sdk_application"]) == 0, "exact SDK exits")
    rollback = record(closed["next_cold_rollback"])
    need(uint(rollback["cycles"]) == 5 and uint(rollback["days"]) == 0
         and parse_ref(plan["ledger_ref"]) == parse_ref(closed["continuity_ledger"])
         and parse_ref(plan["current_driver_review_ref"]) == parse_ref(closed["current_driver_review"]),
         "five-cycle zero-day rollback")
    need(uint(checked(plan["current_next_ref"], 16384)["next_sequence"]) == 10569, "actual NEXT10569")
    base_ref = parse_ref(plan["sdk_base_ref"])
    anchor_ref = parse_ref(plan["canonical_anchor_ref"])
    base = checked(base_ref, 1048576)
    anchor = checked(anchor_ref, 65536)
    need(base["schema"] == "root.ck3.final-sdk-freeze/v1" and base["machine_id"] == MACHINE
         and base["status"] == "FINAL_SOURCE_FROZEN" and base["runtime_admitted"] is False
         and uint(base["source_file_count"]) == 1466
         and parse_ref(base["source31_canonical_anchor"]) == anchor_ref
         and anchor["schema"] == "xar.source31.canonical-git-anchor/v1"
         and anchor["status"] == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
         and anchor["machine_id"] == MACHINE and anchor["commit"] == base["business_source_commit"],
         "actual Source31 BASE/anchor, no Source30 alias")
    graph = checked(inputs["cold_graph_quote"], 262144)
    need(graph["schema"] == "xar.Source31-A18-complete-cold-quote/v1"
         and graph["machine_id"] == MACHINE and uint(graph["unique_files"]) == 145
         and parse_ref(graph["producer"]) == parse_ref(plan["union_producer"]), "actual complete145 quote")
    rows = graph["files"]
    need(type(rows) is list, "graph rows")
    names: set[str] = set()
    for item in cast(list[object], rows):
        row = record(item)
        name = text(row["path"])
        need(Path(name).is_absolute() and name not in names, "unique complete graph path")
        names.add(name)
        uint(row["bytes"], minimum=1)
        need(re.fullmatch("[0-9a-f]{64}", text(row["sha256"])) is not None, "graph leaf SHA")
    need(len(names) == 145 and str(TARGET / BINDING_NAME) in names
         and parse_ref(inputs["full_storage_ref"]) == parse_ref(plan["full_storage_ref"])
         and parse_ref(inputs["business_anchor"]) == anchor_ref,
         "current graph/Native32/owner storage basis")
    binding = checked(reference(TARGET / BINDING_NAME), 65536)
    need(binding["schema"] == "xar.native32.source31-production-observer-binding/v2"
         and binding["machine_id"] == MACHINE
         and binding["status"] == "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"
         and parse_ref(binding["sdk_base_ref"]) == base_ref
         and parse_ref(binding["sdk_anchor_ref"]) == anchor_ref, "Source31 Native32 observer basis")
    dll = parse_ref(binding["dll"])
    production_ref = parse_ref(binding["production_result_ref"])
    need((dll["bytes"], dll["sha256"]) == DLL_PIN
         and (production_ref["bytes"], production_ref["sha256"]) == PRODUCTION_PIN,
         "actual Native32 artifact provenance")
    production = checked(production_ref, 65536)
    need(production["schema"] == "xar.native32.offline-production-result/v1"
         and production["machine_id"] == MACHINE
         and production["status"] == "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
         and production["runtime_qualified"] is False and production["drain_fence"] is False
         and production["performance_goal_qualified"] is False, "Native32 is not prior runtime proof")
    qualify_actual_native32_v1(adapter, binding, graph, text(base["source_root"]))
    return adapter, plan


class QualifyNative32V1(Protocol):
    def __call__(self, value: object, *, machine_id: str) -> object: ...

def qualify_actual_native32_v1(adapter: MetadataAdapterV1, binding: Doc,
                              graph: Doc, sdk_root: str) -> None:
    name = adapter.NATIVE32_ADAPTER_NAME
    need(Path(name).name == name and name.endswith(".py"), "sealed Native32 runtime name")
    path = TARGET / name
    rows = graph["files"]
    need(type(rows) is list, "actual graph file rows")
    found = [record(row) for row in cast(list[object], rows)
             if record(row)["path"] == str(path)]
    need(len(found) == 1, "one actual sealed Native32 runtime row")
    item = found[0]
    ref = parse_ref({key: item[key] for key in ("path", "bytes", "sha256")})
    raw = read_ref(ref, 65536)
    module = ModuleType("_a18_sealed_native32_qualification")
    module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(raw, str(path), "exec"), vars(module))
    function = getattr(module, "qualify_native32_binding_v1", None)
    need(isinstance(function, FunctionType)
         and tuple(inspect.signature(function).parameters) == ("value", "machine_id"),
         "real Native32 qualifier signature")
    qualify = cast(QualifyNative32V1, function)
    result = qualify(binding, machine_id=MACHINE)
    need(getattr(result, "sdk_root", None) == Path(sdk_root).resolve()
         and record(getattr(result, "wire", None)) == binding,
         "actual Native32 qualification bound to Source31, no issuer or query")

def build_owner_inputs_v1(*, adapter_value: object, cold_graph_plan: ExactRef,
                         cold_graph_quote: ExactRef, mod_absence: ExactRef,
                         recording: RecordingRefsV1, at_utc: datetime) -> OwnerInputV1:
    plan = checked(cold_graph_plan, 16384)
    metadata_adapter_v1(adapter_value, plan)
    return parse_owner_inputs_v1({
        "schema": "xar.C23-A18-cold-owner-metadata-input/v1", "machine_id": MACHINE,
        "execution_owner": "Root", "root_direct_execution_release": True,
        "observed_at_utc": at_utc.isoformat(), "runtime_root": str(TARGET),
        "cold_graph_plan": cold_graph_plan, "cold_graph_quote": cold_graph_quote,
        "full_storage_ref": parse_ref(plan["full_storage_ref"]),
        "live_storage_ref": reference(TARGET / "STORAGE-ADMISSION.json", 32768),
        "actual_game": reference(TARGET / "ROOT-ACTUAL-GAME-LAUNCH-C23.json", 32768),
        "sdk_freeze": reference(TARGET / FREEZE_NAME),
        "business_anchor": parse_ref(plan["canonical_anchor_ref"]),
        "mod_absence": mod_absence, "recording": recording}, at_utc=at_utc)

def _load_legacy_v1() -> ModuleType:
    path = OWN / "prepare_c23_a05_union_v1.py"
    raw = read_ref(fixed(path, LEGACY_PIN), 65536)
    fixed(OWN / "prepare_c23_a03_cold_owner_metadata_v1.py", GENERIC_PIN)
    name = "_a18_verified_a05_owner_metadata"
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), vars(module))
    return module

def project_legacy_owner_v1(raw: bytes) -> str:
    """Modify only the selected real A05 function; retain every historical guard."""
    need((len(raw), hashlib.sha256(raw).hexdigest()) == LEGACY_PIN, "actual A05 producer")
    tree = ast.parse(raw)
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "cold_owner"]
    need(len(selected) == 1, "one original cold_owner")
    node = selected[0]
    class Literals(ast.NodeTransformer):
        def visit_Constant(self, item: ast.Constant) -> ast.AST:
            if type(item.value) is str:
                replacements = {
                    "C23-A05": "C23-A18",
                    "_a05_existing_cold_metadata_RAM": "_a18_existing_cold_metadata_RAM",
                    "A05-finite-cold-metadata-RAM": "A18-finite-cold-metadata-RAM",
                    "ROOT-FINAL-SDK-FREEZE-P37C23-A05.json": FREEZE_NAME,
                }
                if item.value in replacements:
                    return ast.copy_location(ast.Constant(replacements[item.value]), item)
            return item
    node = cast(ast.FunctionDef, Literals().visit(node))
    exec_positions = [i for i, part in enumerate(node.body)
                      if isinstance(part, ast.Expr) and isinstance(part.value, ast.Call)
                      and isinstance(part.value.func, ast.Name) and part.value.func.id == "exec"]
    returns = [i for i, part in enumerate(node.body) if isinstance(part, ast.Return)]
    need(len(exec_positions) == len(returns) == 1, "one original verified-exec/compose seam")
    node.body.insert(returns[0], ast.parse("metadata_scope(scope,T5)").body[0])
    node.body.insert(exec_positions[0], ast.parse("source=metadata_source(source)").body[0])
    result = ast.unparse(ast.fix_missing_locations(node))
    compile(result, "<A18 selected actual owner producer>", "exec")
    return result

def cold_owner(inputs_value: object, *, adapter_value: object) -> tuple[Outputs, OwnerQuoteV1]:
    inputs = parse_owner_inputs_v1(inputs_value, at_utc=datetime.now(timezone.utc))
    adapter, plan = validate_source31_owner_basis_v1(inputs, adapter_value)
    legacy = _load_legacy_v1()
    raw = read_ref(fixed(OWN / "prepare_c23_a05_union_v1.py", LEGACY_PIN), 65536)
    source = project_legacy_owner_v1(raw)
    def metadata_source(value: str) -> str:
        return adapter.metadata_source(plan, value)
    def metadata_scope(namespace: Doc, runtime: Path) -> None:
        adapter.metadata_scope(plan, namespace, runtime)
    namespace: Doc = dict(vars(legacy))
    namespace.update(T5=TARGET, metadata_source=metadata_source, metadata_scope=metadata_scope)
    exec(compile(source, "<A18 exact historical owner wrapper>", "exec"), namespace)
    function = namespace["cold_owner"]
    need(isinstance(function, FunctionType)
         and tuple(inspect.signature(function).parameters) == ("inputs",), "original owner callable")
    # Validated callable signature above; the untyped historical return is checked below.
    invoke = cast(LegacyComposeV1, function)
    projected = {key: value for key, value in inputs.items()
                 if key not in {"cold_graph_plan", "cold_graph_quote"}}
    result = invoke(projected)
    need(type(result) is tuple and len(cast(tuple[object, ...], result)) == 2, "metadata output pair")
    output_value, quote_value = cast(tuple[object, object], result)
    need(isinstance(output_value, dict), "metadata outputs")
    out: Outputs = {}
    for path, data in cast(dict[object, object], output_value).items():
        need(isinstance(path, Path) and type(data) is bytes, "typed metadata leaf")
        out[cast(Path, path)] = cast(bytes, data)
    need(set(out) == {TARGET / name for name in OUTPUT_NAMES}, "four exact new metadata leaves")
    legacy_quote = record(quote_value)
    need(legacy_quote["gate_must_be_last"] is True
         and legacy_quote["publish_order"] == list(OUTPUT_NAMES)
         and uint(legacy_quote["next_sequence"]) == 10569
         and uint(legacy_quote["completed_cycles"]) == 4753
         and uint(legacy_quote["saved_game_days"]) == 5429, "actual saved basis/gate order")
    admission = record(json.loads(out[TARGET / OUTPUT_NAMES[1]]))
    need(parse_ref(admission["source31_anchor"]) == parse_ref(plan["canonical_anchor_ref"])
         and parse_ref(admission["source31_base"]) == parse_ref(plan["sdk_base_ref"])
         and parse_ref(admission["business_anchor"]) == parse_ref(plan["canonical_anchor_ref"])
         and parse_ref(admission["native32_observer_binding"]) == reference(TARGET / BINDING_NAME)
         and uint(admission["new_ordinary_cycle_credit"]) == 0
         and uint(admission["new_game_day_credit"]) == 0, "source31/native32/no credit")
    # The old admission keeps its exact-int Game carrier; this new quote uses safe wire identity.
    game_quote = record(legacy_quote["new_Game"])
    game_quote["creation_filetime"] = str(uint(game_quote["creation_filetime"], 2**64 - 1, 1))
    legacy_quote["new_Game"] = game_quote
    allocation = sum((len(data) + 4095) // 4096 * 4096 for data in out.values())
    peak = allocation + max((len(data) + 4095) // 4096 * 4096 for data in out.values())
    rows: list[ExactRef] = [{"path": str(path), "bytes": len(data),
                             "sha256": hashlib.sha256(data).hexdigest()}
                            for path, data in out.items()]
    quote: OwnerQuoteV1 = {
        "schema": "xar.C23-A18-owner-preparation/v1", "machine_id": MACHINE,
        "observed_at_utc": inputs["observed_at_utc"],
        "status": "RAM_READY_NOT_WRITTEN_NO_GATE_PUBLISHED",
        "producer": reference(Path(__file__)), "adapter": parse_ref(plan["union_producer"]),
        "cold_graph_plan": inputs["cold_graph_plan"], "cold_graph_quote": inputs["cold_graph_quote"],
        "legacy_metadata_source": fixed(OWN / "prepare_c23_a03_cold_owner_metadata_v1.py", GENERIC_PIN),
        "outputs": rows, "publish_order": list(OUTPUT_NAMES), "gate_must_be_last": True,
        "runtime_graph_rows": 145, "next_sequence": 10569, "saved_cycles": 4753,
        "saved_days": 5429, "rollback_cycles": 5, "rollback_days": 0,
        "unknown10565_replayed": False, "new_business_credit": 0,
        "original_wall_origin_reset": False, "logical_bytes": sum(map(len, out.values())),
        "allocation_upper": allocation, "metadata_write_peak_upper": peak, "legacy_quote": legacy_quote}
    return out, quote

def parse_file_identity_v1(value: object) -> FileIdentityV1:
    row = record(value)
    need(set(row) == {"volume_serial", "file_id"}, "existing owner file identity contract")
    volume = decimal(row["volume_serial"])
    file_id = text(row["file_id"])
    need(re.fullmatch("[0-9a-f]{32}", file_id) is not None, "opaque native 128-bit file ID")
    return {"volume_serial": volume, "file_id": file_id}

def validate_supervisor_task_v1(spec_ref: ExactRef, *, cold_graph_plan: ExactRef,
                                adapter_value: object) -> SupervisorTaskV1:
    plan = checked(cold_graph_plan, 16384)
    adapter = metadata_adapter_v1(adapter_value, plan)
    plan = dict(adapter.parse_plan(plan))
    row = checked(spec_ref, 16384)
    need(set(row) == set(SupervisorTaskV1.__annotations__)
         and row["schema"] == "xar.interactive-task-owner/v1" and row["role"] == "supervisor"
         and row["machine_id"] == MACHINE, "one supervisor spec contract")
    nonce = text(row["nonce"])
    need(re.fullmatch("[0-9a-f]{32}", nonce) is not None and nonce == plan["task_nonce"]
         and row["task_name"] == "XARG2ManagedOwner-" + nonce, "original plan Task nonce")
    need(Path(spec_ref["path"]).resolve() == TASK / "SPEC.json"
         and Path(text(row["root"])).resolve() == TASK
         and Path(text(row["cwd"])).resolve() == TARGET
         and Path(text(row["bootstrap"])).resolve() == TARGET / BOOT_NAME
         and Path(text(row["stage"])).resolve() == TARGET / STAGE_NAME
         and Path(text(row["stop_path"])).resolve() == TARGET / "STOP-OWNED-GAME-C23",
         "exact new Task and stage paths")
    need((reference(TARGET / BOOT_NAME)["bytes"], text(row["bootstrap_sha256"])) == BOOT_PIN,
         "actual independent bootstrap")
    fixed(TARGET / BOOT_NAME, BOOT_PIN)
    fixed(TARGET / CONTRACT_NAME, CONTRACT_PIN)
    stage_ref = reference(TARGET / STAGE_NAME)
    need(stage_ref["sha256"] == text(row["stage_sha256"]), "actual supervisor stage")
    expected_args = ["--clean-source-freeze", str(TARGET / "ROOT-CLEAN-SOURCE-FROZEN-C23-A15.json"),
        "--screen-admission", str(TARGET / "ROOT-SCREEN-ADMISSION-C23-A15.json"),
        "--launch-config", str(TARGET / "ROOT-LAUNCH-CONFIG-C23-A15.json"),
        "--attempt", "a15", "--attempt-nonce", text(plan["attempt_nonce"]),
        "--task-nonce", nonce, "--steam-native-state", parse_ref(plan["steam_native_state_ref"])["path"]]
    need(type(row["stage_args"]) is list and row["stage_args"] == expected_args,
         "sole original A15 stage argument contract")
    environment = record(row["env"])
    need(set(environment) == {"PYTHONDONTWRITEBYTECODE", "PYTHONPATH"}
         and environment["PYTHONDONTWRITEBYTECODE"] == "1", "no ambient SDK or WAL env")
    pythonpath = text(environment["PYTHONPATH"])
    sid = text(row["sid"])
    need(re.fullmatch("S-[0-9]+(?:-[0-9]+)+", sid) is not None, "actual owner SID")
    python = text(row["python"])
    pythonw = text(row["pythonw"])
    need(Path(python).is_absolute() and Path(python).name.lower() == "python.exe"
         and Path(pythonw).is_absolute() and Path(pythonw).name.lower() == "pythonw.exe",
         "actual base Python interpreter pair")
    # Original source/identity-wire checks; CLI retains the actual caller identity guard.
    owner = ModuleType("_a18_exact_task_owner")
    owner.__file__ = str(OWN / "interactive_task_owner_v1.py")
    raw = read_ref(fixed(Path(owner.__file__), BOOT_PIN), 65536)
    sys.modules[owner.__name__] = owner
    exec(compile(raw, owner.__file__, "exec"), vars(owner))
    verify = getattr(owner, "checked_spec", None)
    need(isinstance(verify, FunctionType)
         and tuple(inspect.signature(verify).parameters) == ("path", "expected_sha"),
         "actual owner spec consumer signature")
    checked_spec = cast(Callable[[Path, str], object], verify)
    need(record(checked_spec(Path(spec_ref["path"]), spec_ref["sha256"])) == row,
         "unchanged original checked_spec result")
    result: SupervisorTaskV1 = {
        "schema": "xar.interactive-task-owner/v1", "role": "supervisor",
        "machine_id": MACHINE, "nonce": nonce, "task_name": text(row["task_name"]),
        "sid": sid, "session": uint(row["session"], 2**32 - 1, 1),
        "root": str(TASK), "cwd": str(TARGET), "python": python, "pythonw": pythonw,
        "python_file_id": parse_file_identity_v1(row["python_file_id"]),
        "pythonw_file_id": parse_file_identity_v1(row["pythonw_file_id"]),
        "bootstrap": str(TARGET / BOOT_NAME), "bootstrap_sha256": BOOT_PIN[1],
        "stage": str(TARGET / STAGE_NAME), "stage_sha256": stage_ref["sha256"],
        "stage_args": expected_args, "stop_path": str(TARGET / "STOP-OWNED-GAME-C23"),
        "env": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": pythonpath}}
    need(record(json.loads(encode(result))) == row, "exact Task JSON-domain roundtrip")
    return result

def supervisor_task_commands_v1(spec_ref: ExactRef, *, cold_graph_plan: ExactRef,
                                 adapter_value: object) -> list[TaskCommandV1]:
    spec = validate_supervisor_task_v1(spec_ref, cold_graph_plan=cold_graph_plan,
                                       adapter_value=adapter_value)
    prefix = [spec["python"], "-B", str(OWN / "interactive_task_owner_v1.py")]
    commands: list[TaskCommandV1] = []
    for operation in ("register", "inspect", "run"):
        argv = [*prefix, operation, "--spec", spec_ref["path"], "--spec-sha", spec_ref["sha256"]]
        if operation in {"register", "run"}:
            argv.append("--allow-production")
        commands.append({"machine_id": MACHINE, "operation": operation, "argv": argv})
    return commands

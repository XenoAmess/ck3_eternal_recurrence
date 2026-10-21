"""Source31 A18 cold graph. Preparation only; Root owns every runtime mutation."""
from __future__ import annotations
import ast
import copy
import hashlib
import importlib
import json
import re
import sys
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from types import FunctionType, ModuleType, SimpleNamespace
from typing import Callable, Literal, Protocol, TypedDict, cast
import prepare_source29_a17_cold_union_v1 as previous

Doc = dict[str, object]
Outputs = dict[Path, bytes]
class ExactRef(TypedDict):
    path:str
    bytes:int
    sha256:str
class Dynamic(Protocol):
    def __call__(self,*args:object,**kwargs:object)->object:...
def record(value:object)->Doc:
 if not isinstance(value,dict):raise ValueError("A17 object required")
 out:Doc={}
 for key,item in value.items():
  if type(key) is not str:raise ValueError("A17 text key required")
  out[key]=item
 return out
def text(value:object)->str:
 if type(value) is not str or not value:raise ValueError("A17 text required")
 return value
def uint(value:object,maximum:int=2**63-1)->int:
 if type(value) is not int or not 0<=value<=maximum:raise ValueError("A17 exact integer required")
 return value
def sha(raw:bytes)->str:return hashlib.sha256(raw).hexdigest()
def enc(value:object)->bytes:
 return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
def sequence(value:object)->list[object]:
 if type(value) is not list:raise ValueError("A17 JSON array required")
 return value
def refs(value:object)->ExactRef:
 r=record(value);need(set(r)=={"path","bytes","sha256"},"exact ref keys")
 path=text(r["path"]);size=uint(r["bytes"],2**53-1);digest=text(r["sha256"])
 need(Path(path).is_absolute() and size>0 and re.fullmatch("[0-9a-f]{64}",digest) is not None,"exact ref")
 return {"path":path,"bytes":size,"sha256":digest}
def read_ref(value:object,limit:int=1048576)->bytes:
 r=refs(value);p=Path(r["path"]);a=p.stat()
 with p.open("rb") as stream:raw=stream.read(limit+1)
 b=p.stat()
 need((len(raw),sha(raw))==(r["bytes"],r["sha256"]) and 0<len(raw)<=limit
  and (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(b.st_dev,b.st_ino,b.st_size,b.st_mtime_ns),"stable actual bytes")
 return raw
def checked(value:object,limit:int=1048576)->Doc:return record(json.loads(read_ref(value,limit)))
def ref(path:Path|str)->ExactRef:
 p=Path(path).resolve(strict=True)
 with p.open("rb") as stream:raw=stream.read(1048577)
 need(0<len(raw)<=1048576,"bounded ref")
 return {"path":str(p),"bytes":len(raw),"sha256":sha(raw)}
def one(source:str,before:str,after:str,count:int=1)->str:
 need(source.count(before)==count,"reviewed seam "+before[:80]);return source.replace(before,after)
def dynamic(module:ModuleType,name:str)->Dynamic:
 value:object=getattr(module,name,None);need(callable(value),"callable "+name)
 # This cast follows the explicit callable check at the isolated legacy-module boundary.
 return cast(Dynamic,value)
MACHINE = previous.MACHINE
P, O, OWN = previous.P, previous.O, Path(__file__).resolve().parent
PREVIOUS = previous.TARGET
TARGET = PREVIOUS.with_name("runtime-a18")
PREP = O / "source31-a18-prep01"
SCREEN = TARGET / "ROOT-SCREEN-ADMISSION-C23-A15.json"
NATIVE32_ADAPTER_NAME = "observer_journal_runtime_v1.py"
NATIVE32_EXTENSION_NAME = "native32_mcp_extension_v1.py"
NATIVE32_OBSERVER_BINDING_NAME = "ROOT-NATIVE32-PRODUCTION-BINDING01.json"
NATIVE32_LABEL = "Native32 passive time-command diagnostics"
M17_PIN = (44761, "e9bbb74abfd0481a9c4da145e76cb7db0135b6dcb9ba2591c4715cc7e3ce9d13")
A17_QUOTE_PIN = (212489, "250ae899c89098909ebfbbd12284d1fcb806aba482076303761c8f8bad5090aa")
A17_CLOSURE_PIN = (7191, "3ebbf5eb221814cab62bbef01ea0a6570a8da6a48420c064ca30155b5980aa53")
A17_REVIEW_PIN = (3592, "1698ba34820796d7852c5a9c0b11a7dc8347c9d2c7a122407c08100dfe309f78")
A17_LEDGER_PIN = (24682, "c857d8946729c121c426f06d4c6970b9e3073b0605929c5a01f922284a2e425d")
SOURCE30_BASE_REF: ExactRef = {
    "path": str(O / "source30-sdk-prep01/ROOT-FINAL-SDK-SOURCE30-BASE.json"),
    "bytes": 403040, "sha256": "5d159608105afa5ffe61169375158057a0fca84e707569bc08dbd0707bc8ed97"}
SOURCE30_COMMIT = "2fd0412acf2357e8ee08ed8355e2a4a816ebfaef"
CANDIDATE = OWN / "candidates/native32_runtime_journal_adapter_20261021"
SDK31_CHANGED = {
    "xar_autoplayer/bridge/native_driver.py",
    "xar_autoplayer/bridge/cached_native_clock_summary_v1.py",
    "xar_autoplayer/bridge/tactical_clock_diagnostics_v1.py",
    "xar_autoplayer/bridge/exact_clock_failure_diagnostic_v1.py",
    "xar_autoplayer/bridge/player_lifestyle_private_transport_v1.py",
    "xar_autoplayer/successor_ui_pending_ledger_v1.py"}


class PlanV1(TypedDict):
    schema: Literal["xar.Source31-A18-complete-cold-input/v1"]
    machine_id: str
    execution_owner: Literal["Root"]
    root_direct_execution_release: Literal[True]
    observed_at_utc: str
    attempt_nonce: str
    task_nonce: str
    full_storage_ref: ExactRef
    live_storage_ref: ExactRef
    steam_native_state_ref: ExactRef
    union_producer: ExactRef
    stage_producer: ExactRef
    sdk_base_ref: ExactRef
    canonical_anchor_ref: ExactRef
    native_binding_ref: ExactRef
    closure_ref: ExactRef
    current_driver_review_ref: ExactRef
    ledger_ref: ExactRef
    current_next_ref: ExactRef
    screen_admission_path: str
    runtime_adapter_ref: ExactRef
    runtime_extension_ref: ExactRef


def need(ok: bool, why: str) -> None:
    if not ok:
        raise ValueError("A18: " + why)


def parse_plan(value: object) -> PlanV1:
    row = record(value)
    need(set(row) == set(PlanV1.__annotations__), "one current plan field contract")
    need(row["schema"] == "xar.Source31-A18-complete-cold-input/v1"
         and row["machine_id"] == MACHINE and row["execution_owner"] == "Root"
         and row["root_direct_execution_release"] is True, "Root machine release")
    for name in ("attempt_nonce", "task_nonce"):
        need(re.fullmatch("[0-9a-f]{32}", text(row[name])) is not None, "fresh nonce")
    need(row["attempt_nonce"] != row["task_nonce"], "independent nonces")
    observed = datetime.fromisoformat(text(row["observed_at_utc"]))
    need(observed.utcoffset() is not None, "explicit observation timezone")
    need(Path(text(row["screen_admission_path"])).resolve() == SCREEN.resolve(), "one new root screen")
    result = dict(row)
    for name in set(row) - {"schema", "machine_id", "execution_owner",
            "root_direct_execution_release", "observed_at_utc", "attempt_nonce",
            "task_nonce", "screen_admission_path"}:
        result[name] = refs(row[name])
    # Every field and the complete closed state branch were validated above.
    return cast(PlanV1, result)


def history_view_v1(value: object) -> Doc:
    row = record(value)
    need(type(row.get("next_sequence")) is int and row["next_sequence"] == 10569,
         "current NEXT10569; never reinterpret historical10552")
    return {**row, "next_sequence": 10552}



def parse_sdk_rows_v1(value: object, *, expected_count: int) -> list[Doc]:
    """Exact shared SDK Row wire; integer/hash parsing uses the canonical writer."""
    from write_source27_canonical_ref_v1 import parse_pin
    rows=sequence(value)
    need(len(rows)==expected_count,"exact SDK row count")
    out:list[Doc]=[]
    names:set[str]=set()
    for value_row in rows:
        row=record(value_row)
        need(set(row)=={"relative","bytes","sha256","git_blob_sha1","git_mode"},"single SDK Row contract")
        name=text(row["relative"])
        need(not name.startswith(("/","\\")) and "\\" not in name
            and all(part not in ("",".","..") for part in name.split("/")) and name not in names,
            "safe unique SDK relative")
        pin=record(parse_pin({k:row[k] for k in ("bytes","sha256")}))
        need(type(row["git_blob_sha1"]) is str and re.fullmatch("[0-9a-f]{40}",text(row["git_blob_sha1"])) is not None
            and row["git_mode"]=="100644","ordinary git blob/mode")
        names.add(name);out.append({**row,**pin})
    return out


def parse_canonical_patch_rows_v1(value: object, before: Mapping[str,Doc],
        after: Mapping[str,Doc]) -> list[Doc]:
    from write_source27_canonical_ref_v1 import parse_pin
    rows=sequence(value)
    need(len(rows)==6,"six canonical patch rows")
    names:set[str]=set();out:list[Doc]=[];commits:set[str]=set()
    for item in rows:
        row=record(item)
        need(set(row)=={"relative","before_pin","output_pin","public_input","public_source_commit"},
             "single canonical patch row contract")
        relative=text(row["relative"]);prefix="ck3_autonomous_player/src/"
        need(relative.startswith(prefix),"canonical public source prefix")
        name=relative[len(prefix):]
        need(name in SDK31_CHANGED and name not in names,"unique finite SDK patch")
        output=record(parse_pin(row["output_pin"]))
        expected={k:after[name][k] for k in ("bytes","sha256")}
        need(output==expected,"SDK output pin matches row")
        prior={k:before[name][k] for k in ("bytes","sha256")} if name in before else None
        need((row["before_pin"] is None and prior is None) or
             (row["before_pin"] is not None and record(parse_pin(row["before_pin"]))==prior),
             "original parent pin or explicit new null")
        public=row["public_input"]
        helpers=SDK31_CHANGED-{"xar_autoplayer/bridge/native_driver.py","xar_autoplayer/successor_ui_pending_ledger_v1.py"}
        if name in helpers:
            public_row=record(public)
            need(set(public_row)=={"relative","pin"} and public_row["relative"]==name
                 and record(parse_pin(public_row["pin"]))==output,"one public helper input")
        else:
            need(public is None,"composite source explicit public null")
        commit=text(row["public_source_commit"])
        need(re.fullmatch("[0-9a-f]{40}",commit) is not None,"actual public source commit")
        names.add(name);commits.add(commit);out.append(row)
    need(names==SDK31_CHANGED and len(commits)==1,"one public source and finite6")
    return out


def source31_metadata_v1(base_value: object, anchor_value: object,
        parent_value: object, parent_anchor_ref: object, parent_base_ref: object,
        *, machine_id: str) -> Doc:
    from write_source27_canonical_ref_v1 import parse_pin
    base, anchor, parent = record(base_value), record(anchor_value), record(parent_value)
    need(base.get("schema") == "root.ck3.final-sdk-freeze/v1"
        and base.get("status") == "FINAL_SOURCE_FROZEN"
        and base.get("machine_id") == anchor.get("machine_id") == machine_id
        and base.get("runtime_admitted") is False and "canonical_preload_policy" not in base,
        "policy-free actual Source31 BASE")
    need(anchor.get("schema") == "xar.source31.canonical-git-anchor/v1"
        and anchor.get("status") == "CANONICAL_REF_CREATED_NOT_DEPLOYED"
        and anchor.get("parent") == SOURCE30_COMMIT
        and anchor.get("actual_Source30_anchor") == parent_anchor_ref
        and anchor.get("actual_Source30_BASE") == parent_base_ref,
        "exact Source31 parent30 provenance")
    parent_rows=parse_sdk_rows_v1(parent["files"],expected_count=1465)
    before = {text(record(r)["relative"]): record(r) for r in parent_rows}
    need(len(parent_rows)==len(before)==1465,"complete unique parent1465")
    rows = parse_sdk_rows_v1(base["files"],expected_count=1466)
    after = {text(record(r)["relative"]): record(r) for r in rows}
    new_name = "xar_autoplayer/bridge/cached_native_clock_summary_v1.py"
    need(len(before) == 1465 and len(after) == len(rows) == 1466
        and set(after) - set(before) == {new_name} and set(before) <= set(after),
        "exact Source31 1466 names")
    changed = {name for name in after if after[name] != before.get(name)}
    patches = parse_sdk_rows_v1(anchor["output_pins"],expected_count=6)
    parse_canonical_patch_rows_v1(anchor["canonical_patch_rows"],before,after)
    need(changed == SDK31_CHANGED == {text(record(r)["relative"]) for r in patches}
        and len(patches) == len(sequence(anchor["canonical_patch_rows"])) == 6
        and all(after[text(record(r)["relative"])] == record(r) for r in patches),
        "five modifications and one new cached helper")
    raw = json.dumps(rows, ensure_ascii=False, sort_keys=True,
                     separators=(",", ":"), allow_nan=False).encode()
    complete=record(parse_pin(anchor["complete_rows_JSON"]))
    need(set(complete)=={"bytes","sha256"} and type(complete["bytes"]) is int
        and type(complete["sha256"]) is str and re.fullmatch("[0-9a-f]{64}",text(complete["sha256"])) is not None,
        "typed complete row identity")
    need(complete == {"bytes": len(raw), "sha256": sha(raw)}
        and type(anchor.get("source_file_count")) is int and anchor["source_file_count"] == 1466
        and type(base.get("source_file_count")) is int and base["source_file_count"] == 1466
        and uint(anchor["source_bytes"]) == sum(uint(record(r)["bytes"]) for r in rows)
        and base.get("business_source_commit") == anchor.get("commit")
        and re.fullmatch("[0-9a-f]{40}", text(anchor.get("commit"))) is not None
        and base.get("source31_canonical_anchor") is not None,
        "complete Source31 row identity")
    return anchor


def load_registered_source_v1(name: str, raw: bytes) -> ModuleType:
    need(name == "observer_journal_runtime_v1", "one qualified preparation adapter")
    module = ModuleType(name)
    module.__file__ = str(CANDIDATE / (name + ".py"))
    sys.modules[name] = module
    exec(compile(raw, module.__file__, "exec"), vars(module))
    return module


def function_source_v1(module: ModuleType, name: str) -> str:
    raw = Path(text(module.__file__)).read_text(encoding="utf-8")
    nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == name]
    need(len(nodes) == 1, "one actual producer function")
    result = ast.get_source_segment(raw, nodes[0])
    need(result is not None, "exact actual function boundary")
    return text(result)


def native32_source_stage_v2(source: Mapping[str, bytes], *,
        adapters: Mapping[str, bytes], legacy_registration: str,
        native_label: str, dll: ExactRef, export_rvas: Mapping[str, int]) -> dict[str, bytes]:
    """Finite source projection only. Qualification/loaded custody remain separate."""
    out = dict(source)
    if len(out) != 113 or not native_label or type(native_label) is not str:
        raise ValueError("accepted113 and explicit Native32 label required")
    expected = {
        "observer_journal_runtime_v1.py": (43698, "2a3016363c9b3633611f3ba75d217c36f5bb30e733886db571a48138bf6a47f8"),
        "native32_mcp_extension_v1.py": (3082, "25d4b1c322f4bcaaf8382590c8ee95b6fd0277aa06bcf4a02391fba98630da18")}
    old = {"observer_journal_v1.py": (17063, "f77710b050f839da36c308a1da66a8aec79fa0ec8bec167100f62c688a029712"),
           "native31_mcp_extension_v1.py": (1876, "9c56a270f8029360de26560ded0cb3f7938749684f65921b9245f30ee49004a0")}
    for name, pin in old.items():
        if (len(out[name]), sha(out[name])) != pin:
            raise ValueError("original Native31 input differs")
        del out[name]
    for name, pin in expected.items():
        raw = adapters[name]
        if name in out or (len(raw), sha(raw)) != pin:
            raise ValueError("qualified Source31/Native32 adapter differs")
        out[name] = raw
    def swap(name: str, before: str, after: str, count: int = 1) -> None:
        out[name] = one(out[name].decode("utf-8"), before, after, count).encode()
    entry = "root_p37c23_mcp_entry.py"
    pins_literal = repr(tuple((n, pin[0], pin[1]) for n, pin in expected.items()))
    registration = (
        "    # Native32: exact two cold sources, inert registration, same original owner.\n"
        "    import hashlib as _n32_hashlib\n"
        "    for _n32_name, _n32_size, _n32_sha in " + pins_literal + ":\n"
        "        _n32_raw=(N/_n32_name).read_bytes()\n"
        "        if (len(_n32_raw),_n32_hashlib.sha256(_n32_raw).hexdigest())!=(_n32_size,_n32_sha):\n"
        "            raise RuntimeError('Native32 cold adapter source differs')\n"
        "    import native32_mcp_extension_v1 as _n32_extension\n"
        "    import observer_journal_runtime_v1 as _n32_reader\n"
        "    if (Path(_n32_extension.__file__).resolve()!=N/'native32_mcp_extension_v1.py'\n"
        "            or Path(_n32_reader.__file__).resolve()!=N/'observer_journal_runtime_v1.py'):\n"
        "        raise RuntimeError('Native32 adapters imported from another source')\n"
        "    _n32_owner=getattr(driver,'_player_heir_candidate_owner_v1',None)\n"
        "    if _canonical is None or _n32_owner is None:\n"
        "        raise RuntimeError('Native32 requires the original canonical owner')\n"
        "    _n32_native=_n32_reader._obj(json.loads((N/'ROOT-NATIVE30-NATIVE-PIN-C23-A15.json').read_bytes()))\n"
        "    _n32_ref=_n32_reader._ref32(_n32_native.get('native32_observer_binding'))\n"
        "    if Path(_n32_ref['path']).resolve()!=N/" + repr(NATIVE32_OBSERVER_BINDING_NAME) + ":\n"
        "        raise RuntimeError('Native32 observer binding path differs')\n"
        "    _n32_raw=(N/" + repr(NATIVE32_OBSERVER_BINDING_NAME) + ").read_bytes()\n"
        "    if (len(_n32_raw)>16384 or len(_n32_raw)!=_n32_ref['bytes']\n"
        "            or _n32_hashlib.sha256(_n32_raw).hexdigest()!=_n32_ref['sha256']):\n"
        "        raise RuntimeError('Native32 observer binding bytes differ')\n"
        "    _n32_binding:object=json.loads(_n32_raw)\n"
        "    from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import ensure_received_provider_v1\n"
        "    from xar_autoplayer.mcp_server import _forbid_unknown_tool_arguments_v1\n"
        "    from mcp.types import ToolAnnotations as _N32Annotations\n"
        "    _n32_extension.register_native32_journal_v1(\n"
        "        server.tool(annotations=_N32Annotations(readOnlyHint=True,destructiveHint=False,\n"
        "            idempotentHint=True,openWorldHint=False)),owner=_n32_owner,driver=driver,\n"
        "        machine_id=_n32_owner.machine,binding_value=_n32_binding,\n"
        "        existing_ensure=ensure_received_provider_v1)\n"
        "    _forbid_unknown_tool_arguments_v1(server,'ck3_observe_native32_time_command_journal_v1')\n")
    swap(entry, legacy_registration, registration)
    binder = "root_native_build_binding_p37c23.py"
    swap(binder, "NATIVE31_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
                 "NATIVE32_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED")
    swap(binder, "3d43cd01c908013f7bb2704aa1844acd518fa691ae96ef4e09413284dd59038d", dll["sha256"])
    swap(binder, "19528704", str(dll["bytes"]))
    # The actual qualified Native32 five executable RVAs currently equal the old five.
    parsed = ast.parse(out[binder])
    tests = [node for node in ast.walk(parsed) if isinstance(node, ast.Compare)
             and isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Attribute)
             and node.left.func.attr == "get" and node.left.args
             and isinstance(node.left.args[0], ast.Constant) and node.left.args[0].value == "export_rvas"]
    if len(tests) != 1 or len(tests[0].comparators) != 1:
        raise ValueError("one qualified executable-RVA comparison required")
    literal = ast.literal_eval(tests[0].comparators[0])
    if literal != dict(export_rvas) or len(export_rvas) != 5 or any(type(v) is not int or v <= 0 for v in export_rvas.values()):
        raise ValueError("actual five qualified Native32 executable RVAs differ")
    swap("root_p37c23_cold_resume.py",
        "freeze['native_build_label'] == 'Native31 passive time-command observation'",
        "freeze['native_build_label'] == " + repr(native_label))
    outer = "root_c23_canonical_outer.py"
    swap(outer, "'observer_journal_v1.py'", "'observer_journal_runtime_v1.py'", 2)
    swap(outer, "'native31_mcp_extension_v1.py'", "'native32_mcp_extension_v1.py'", 2)
    text = out[outer].decode()
    nodes = [n for n in ast.parse(text).body if isinstance(n, ast.Assign) and len(n.targets) == 1
             and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "_C23_EXTERNAL_IMPORT_PINS"]
    if len(nodes) != 1:
        raise ValueError("one original external26 map required")
    mapping = record(ast.literal_eval(nodes[0].value))
    for old_name, new_name in (("observer_journal_v1", "observer_journal_runtime_v1"),
                                ("native31_mcp_extension_v1", "native32_mcp_extension_v1")):
        if old_name not in mapping or new_name in mapping:
            raise ValueError("exact old-to-new external identity required")
        del mapping[old_name]
        raw = out[new_name + ".py"]
        mapping[new_name] = (len(raw), sha(raw))
    if len(mapping) != 26:
        raise ValueError("external source cardinality changed")
    segment = ast.get_source_segment(text, nodes[0])
    if segment is None:
        raise ValueError("external assignment boundary missing")
    out[outer] = one(text, segment, "_C23_EXTERNAL_IMPORT_PINS=" + repr(mapping)).encode()
    adapter = load_registered_source_v1("observer_journal_runtime_v1",
        adapters["observer_journal_runtime_v1.py"])
    function = dynamic(adapter, "patch_queue_control_v1")
    value = function(out["root_p37c23_sdk_queue.py"],
        production_binding_basename=NATIVE32_OBSERVER_BINDING_NAME)
    if type(value) is not bytes:
        raise ValueError("Native32 Queue byte projection required")
    out["root_p37c23_sdk_queue.py"] = value
    if len(out) != 113:
        raise ValueError("Native32 replaces exactly two runtime source slots")
    for name, raw in out.items():
        if name.endswith(".py"):
            compile(raw, name, "exec")
    return out


def _old_plan_v1() -> previous.PlanV1:
    return previous.parse_plan(checked(ref(previous.PREP / "A17-COLD-PLAN04.json"), 16384))


def _closed_v1(p: PlanV1) -> Doc:
    need(p["closure_ref"] == previous.fixed(PREVIOUS / "ROOT-A17-ACTUAL-CLOSURE-INDEX01.json", A17_CLOSURE_PIN),
         "exact actual A17 closure")
    closed = checked(p["closure_ref"], 65536)
    game, exits = record(closed["Game"]), record(closed["SDK_actual_exits"])
    need(closed["schema"] == "xar.A17-clock-failure-closed/v1"
        and closed["machine_id"] == MACHINE and closed["Tasks_absent"] is True
        and closed["screen116_released"] is True
        and uint(game["pid"], 2**32-1) == 83948 and game["creation_filetime"] == "134370118417378359"
        and uint(game["exit_code"]) == 1 and game["forced_owned_job_cleanup"] is True
        and uint(game["Job_active_final"]) == 0
        and uint(exits["sdk_queue"]) == 1 and uint(exits["sdk_application"]) == 0,
        "actual forced Game1 and SDK1/0; never normal0/0")
    need(uint(closed["next_sequence"]) == 10569 and uint(closed["saved_cycles"]) == 4753
        and uint(closed["live_settled_cycles"]) == 4758 and uint(closed["pending_cycle"]) == 4759
        and uint(closed["saved_days"]) == 5429 and uint(closed["new_day_credit"]) == 0
        and closed["next_cold_rollback"] == {"cycles": 5, "days": 0}
        and closed["current_failed_request_completion_proven"] is False
        and closed["old_request_replayed"] is False, "preserved unknown10565 and five-cycle rollback")
    sources = record(closed["sources"])
    need(len(sources) == 9, "actual nine small closed facts")
    for value in sources.values():
        read_ref(value, 131072)
    for key in ("FULL", "failed_AUTO", "rejected_CAP", "rejected_tool_journal",
                "actual_canonical_journal", "actual_rich_pixels", "media_completed"):
        read_ref(closed[key], 131072)
    # Completed media SHA is an inherited body fact. Never re-read the 1.3GB movie.
    need(p["current_driver_review_ref"] == closed["current_driver_review"]
        and p["ledger_ref"] == closed["continuity_ledger"], "current closure/review/ledger relation")
    need(p["current_driver_review_ref"] == previous.fixed(
        PREVIOUS / "ROOT-A17-CURRENT-DRIVER-SAVE-REVIEW01.json", A17_REVIEW_PIN)
        and p["ledger_ref"] == previous.fixed(
        PREVIOUS / "ROOT-A17-CONTINUITY-LEDGER-FROZEN01.json", A17_LEDGER_PIN),
        "actual frozen current inputs")
    next_value = checked(p["current_next_ref"], 16384)
    need(type(next_value.get("next_sequence")) is int and next_value["next_sequence"] == 10569,
         "current live NEXT10569")
    old = _old_plan_v1()
    need(p["attempt_nonce"] not in (old["attempt_nonce"], old["task_nonce"])
        and p["task_nonce"] not in (old["attempt_nonce"], old["task_nonce"]), "independent A18 nonces")
    return closed


def build_plan_v1(*, sdk_base_ref: ExactRef, canonical_anchor_ref: ExactRef,
        native_binding_ref: ExactRef, full_storage_ref: ExactRef,
        steam_native_state_ref: ExactRef, observed_at_utc: str,
        attempt_nonce: str, task_nonce: str) -> PlanV1:
    old = _old_plan_v1()
    closure = previous.fixed(PREVIOUS / "ROOT-A17-ACTUAL-CLOSURE-INDEX01.json", A17_CLOSURE_PIN)
    closed = checked(closure, 65536)
    return parse_plan({
        "schema": "xar.Source31-A18-complete-cold-input/v1", "machine_id": MACHINE,
        "execution_owner": "Root", "root_direct_execution_release": True,
        "observed_at_utc": observed_at_utc, "attempt_nonce": attempt_nonce, "task_nonce": task_nonce,
        "full_storage_ref": full_storage_ref, "live_storage_ref": full_storage_ref,
        "steam_native_state_ref": steam_native_state_ref, "union_producer": ref(__file__),
        "stage_producer": old["stage_producer"], "sdk_base_ref": sdk_base_ref,
        "canonical_anchor_ref": canonical_anchor_ref, "native_binding_ref": native_binding_ref,
        "closure_ref": closure, "current_driver_review_ref": closed["current_driver_review"],
        "ledger_ref": closed["continuity_ledger"], "current_next_ref": ref(PREVIOUS / "NEXT-SEQUENCE-P37.json"),
        "screen_admission_path": str(SCREEN),
        "runtime_adapter_ref": ref(CANDIDATE / NATIVE32_ADAPTER_NAME),
        "runtime_extension_ref": ref(CANDIDATE / NATIVE32_EXTENSION_NAME)})


def _source31_v1(p: PlanV1, historical: Doc) -> Doc:
    # Original Source29/28 history is checked with its actual old plan, never renamed.
    previous._source29(_old_plan_v1(), historical)
    base, anchor = checked(p["sdk_base_ref"], 524288), checked(p["canonical_anchor_ref"], 65536)
    parent = checked(SOURCE30_BASE_REF, 524288)
    parent_ref = refs(parent["source30_canonical_anchor"])
    need(base.get("source31_canonical_anchor") == p["canonical_anchor_ref"], "one current Source31 anchor")
    return source31_metadata_v1(base, anchor, parent, parent_ref, SOURCE30_BASE_REF, machine_id=MACHINE)


def _current_pre_v1(p: PlanV1) -> tuple[Doc, bytes]:
    from file_stat_identity_v1 import (
        SCHEMA, normalize_file_stat_identity_v1, parse_file_stat_identity_v1)
    _closed_v1(p)
    review = checked(p["current_driver_review_ref"], 16384)
    need(review["schema"] == "xar.A17-current-Driver-SAVE-review/v1"
        and review["machine_id"] == MACHINE and uint(review["Driver_history_rows"]) == 5281,
        "actual current A17 Driver review")
    current = checked(ref(PREVIOUS / "ROOT-C23-COLD-PRELAUNCH.json"), 32768)
    for name in ("Driver", "SAVE"):
        item = record(review[name])
        expected = parse_file_stat_identity_v1(item["identity"], schema=SCHEMA)
        need(item["stable_before_after"] is True
            and normalize_file_stat_identity_v1(Path(refs(item["ref"])["path"]).stat()) == expected,
            "fresh OS stat identity, excluding atime")
    driver_item = record(review["Driver"])
    driver = refs(driver_item["ref"])
    payload = record(json.loads(read_ref(driver, 41943040)))
    need(uint(payload["format_version"]) == 2 and len(sequence(payload["command_history"])) == 5281
        and payload["last_checkpoint"] == current["checkpoint"] == review["last_checkpoint"],
        "same original SAVE10480 checkpoint")
    base = checked(p["sdk_base_ref"], 524288)
    root = Path(text(base["source_root"])).resolve(strict=True)
    sys.path.insert(0, str(root))
    api = importlib.import_module("xar_autoplayer.cold_checkpoint_validator")
    origin = Path(text(api.__file__)).resolve()
    need(origin == root / "xar_autoplayer/cold_checkpoint_validator.py", "actual Source31 validator origin")
    matches = [record(row) for row in sequence(base["files"])
               if record(row)["relative"] == "xar_autoplayer/cold_checkpoint_validator.py"]
    need(len(matches) == 1, "one canonical Source31 validator row")
    read_ref({"path": str(origin), "bytes": matches[0]["bytes"], "sha256": matches[0]["sha256"]})
    historical = _old_plan_v1()
    old_review = checked(historical["current_driver_review_ref"], 16384)
    manifest = checked(old_review["environment_manifest"], 32768)
    validated = record(dynamic(api, "validate_cold_start_checkpoint_payload_for_pipe")(
        SimpleNamespace(profile_dir=Path(text(manifest["profile_dir"]))), text(payload["pipe_name"]), payload))
    need(validated == current["validation"], "unchanged canonical SAVE/ENV semantics")
    sidecars: list[ExactRef] = []
    for sidecar in sequence(current["sidecars"]):
        actual = ref(refs(sidecar)["path"])
        need(checked(actual, 65536).get("pending") is None, "current sidecar pending")
        sidecars.append(actual)
    need(len(sidecars) == 4, "four current sidecars")
    identity = record(driver_item["identity"])
    current.update(driver_state=driver, materialized_driver_review=p["current_driver_review_ref"],
        validation=validated, sidecars=sidecars, actual_A17_closure=p["closure_ref"],
        actual_next_sequence=10569, driver_stat_schema=SCHEMA,
        driver_stat={"size": identity["bytes"], "FileID": identity["file_id"], "mtime_ns": identity["mtime_ns"]},
        additional_rollback_cycles=5, additional_rollback_days=0, Driver_SAVE_body_reads=2,
        Driver_body_reads=1,SAVE_body_reads=1,SAVE_body_read_bytes=uint(validated["size"]))
    return current, enc(current)


def _accepted_v1() -> tuple[dict[str, bytes], Doc, Doc]:
    q = checked(previous.fixed(previous.PREP / "A17-COLD-QUOTE03.json", A17_QUOTE_PIN), 262144)
    names = [text(name) for name in sequence(record(q["sources"])["runtime_source_output_names"])]
    need(len(names) == len(set(names)) == 113, "actual accepted113 source names")
    profile = checked(ref(PREVIOUS / "ROOT-OBS-PROFILE-C23.json"), 16384)
    config, label = Path(text(profile["config_root"])), text(profile["profile_name"])
    mutable = {config / "basic/profiles" / label / "basic.ini",
               config / "basic/scenes" / (label + ".json")}
    known: Outputs = {}
    for item in sequence(q["files"]):
        row = record(item)
        actual = refs({k: row[k] for k in ("path", "bytes", "sha256")})
        path = Path(actual["path"])
        if path in mutable:
            ref(path)  # Observe current legal OBS configuration; do not pretend it is frozen.
        elif path != PREVIOUS / "NEXT-SEQUENCE-P37.json":
            known[path] = read_ref(actual)
    need(len(known) == 141, "141 original immutable outputs; OBS2/NEXT separately observed")
    source = {name: known[PREVIOUS / name] for name in names}
    freeze = record(json.loads(known[PREVIOUS / "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json"]))
    policy = checked(freeze["canonical_preload_policy"], 65536)
    need(len(previous.pairs(policy["entry_source_pins"])) == 47
         and len(previous.pairs(policy["canonical_entry_source_pins"])) == 8
         and len(record(policy["external_import_source_pins"])) == 26
         and len(sequence(policy["runtime_import_source_pins"])) == 23, "actual47/8/26/23")
    for source_path, digest in previous.pairs(policy["entry_source_pins"]):
        need(sha(known[Path(source_path)]) == digest, "actual source pin before any projection")
    return source, q, policy


def _native32_v1(p: PlanV1) -> tuple[Doc, Doc, dict[str, int]]:
    helper = load_registered_source_v1("observer_journal_runtime_v1", read_ref(p["runtime_adapter_ref"]))
    wire = checked(p["native_binding_ref"], 16384)
    need(wire["sdk_base_ref"] == p["sdk_base_ref"] and wire["sdk_anchor_ref"] == p["canonical_anchor_ref"],
         "Native32 exact current Source31 BASE/anchor")
    dynamic(helper, "qualify_native32_binding_v1")(wire, machine_id=MACHINE)
    dll = refs(wire["dll"])
    production = refs(wire["production_result_ref"])
    prod = checked(production, 65536)
    exports: dict[str, int] = {}
    for item in sequence(prod["exports"]):
        row = record(item)
        if row["executable"] is True:
            exports[text(row["name"])] = int(text(row["rva"]), 16)
    need(len(exports) == 5 and all(type(v) is int and 0 < v < 2**32 for v in exports.values()),
         "five executable Native32 exports; DATA excluded")
    old_launch = checked(ref(PREVIOUS / "ROOT-LAUNCH-CONFIG-C23-A15.json"), 16384)
    host_head = text(old_launch["git_head"])
    need(re.fullmatch("[0-9a-f]{40}", host_head) is not None, "actual runtime host checkout head")
    values: Doc = {"native_build_label": NATIVE32_LABEL, "dll_sha256": dll["sha256"],
                  "git_head": host_head, "dll": dll["path"], "build_receipt": production["path"]}
    return values, {"native_build_label": NATIVE32_LABEL, "dll": dll, "qualification": production}, exports


def _source31_runtime_v1(p: PlanV1) -> str:
    current = sys.modules[__name__]
    writer=importlib.import_module("write_source27_canonical_ref_v1")
    pin_names=("require","obj","keys","string","integer","hexstr","parse_pin")
    shared="class _A18Pin(TypedDict):\n    bytes:int\n    sha256:str\n"
    for name in pin_names:
        shared+=function_source_v1(writer,name)+"\n"
    for name in pin_names:
        shared=re.sub(r"\b"+name+r"\b","_a18_pin_"+name,shared)
    shared=re.sub(r"\bPin\b","_A18Pin",shared)
    fragment="from collections.abc import Mapping\n"+shared+"\n".join(function_source_v1(current,name) for name in
        ("parse_sdk_rows_v1","parse_canonical_patch_rows_v1","source31_metadata_v1"))+"\n"
    fragment=fragment.replace("    from write_source27_canonical_ref_v1 import parse_pin\n","")
    fragment=re.sub(r"\bparse_pin\b","_a18_pin_parse_pin",fragment)
    for name in ("parse_sdk_rows_v1","parse_canonical_patch_rows_v1"):
        fragment=re.sub(r"\b"+name+r"\b","_a18_"+name,fragment)
    for name in ("record", "text", "need", "uint", "sequence", "sha"):
        fragment = re.sub(r"\b" + name + r"\b", "_a17_" + name, fragment)
    fragment = fragment.replace("source31_metadata_v1", "_a18_source31_metadata_v1")
    constants: Doc = {"SOURCE30_COMMIT": SOURCE30_COMMIT, "SDK31_CHANGED": SDK31_CHANGED,
        "A18_BASE": p["sdk_base_ref"], "A18_ANCHOR": p["canonical_anchor_ref"],
        "A18_PARENT_BASE": SOURCE30_BASE_REF,
        "A18_PARENT_ANCHOR": checked(SOURCE30_BASE_REF, 524288)["source30_canonical_anchor"],
        "A18_HISTORY_BASE": _old_plan_v1()["sdk_base_ref"],
        "A18_HISTORY_ANCHOR": _old_plan_v1()["canonical_anchor_ref"],
        "A18_HISTORY_FREEZE": ref(PREVIOUS / "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")}
    fragment = "\n".join(key + "=" + repr(value) for key, value in constants.items()) + "\n" + fragment
    return fragment + '''
from types import FunctionType as _A18FunctionType
_A18_PRIOR_ANCHOR=_A18FunctionType(validate_source28_business_anchor.__code__,dict(globals()))
_A18_PRIOR_BUSINESS=_A18FunctionType(validate_source28_frozen_business.__code__,dict(globals()))
def validate_source28_business_anchor(anchor,checked):
    _A18_PRIOR_ANCHOR(checked(A18_HISTORY_ANCHOR,65536),checked)
    require(anchor==checked(A18_ANCHOR,65536),'actual Source31 anchor')
    return _a18_source31_metadata_v1(checked(A18_BASE,524288),anchor,
        checked(A18_PARENT_BASE,524288),A18_PARENT_ANCHOR,A18_PARENT_BASE,machine_id=MACHINE)
def validate_source28_frozen_business(admission,freeze,checked):
    history=checked(A18_HISTORY_FREEZE,524288)
    prior_anchor=checked(A18_HISTORY_ANCHOR,65536)
    _A18_PRIOR_BUSINESS({**admission,'business_anchor':A18_HISTORY_ANCHOR,
        'business_source_commit':prior_anchor['commit']},history,checked)
    base=checked(A18_BASE,524288)
    anchor=_a18_source31_metadata_v1(base,checked(A18_ANCHOR,65536),
        checked(A18_PARENT_BASE,524288),A18_PARENT_ANCHOR,A18_PARENT_BASE,machine_id=MACHINE)
    require(admission['business_anchor']==A18_ANCHOR and freeze['files']==base['files']
        and freeze['business_source_commit']==admission['business_source_commit']==anchor['commit'],
        'actual Source31 admission/freeze')
    return anchor
'''


def _bridge_v1(p: PlanV1, pre: Doc) -> str:
    constants: Doc = {"A18_CLOSURE_REF": p["closure_ref"],
        "A18_REVIEW_REF": p["current_driver_review_ref"],
        "A18_HISTORICAL_PRE": ref(PREVIOUS / "ROOT-C23-COLD-PRELAUNCH.json"),
        "A18_CURRENT_PRE": pre}
    return "\n".join(k + "=" + repr(v) for k, v in constants.items()) + "\n" + '''
from typing import Callable as _A18Callable
def validate_actual_A17_index_v1(reference:object,checked:_A18Callable[[object,int],dict[str,object]])->dict[str,object]:
    require(reference==A18_CLOSURE_REF,'actual A17 closed authority')
    x=checked(reference,16384)
    require(x['schema']=='xar.A17-clock-failure-closed/v1'
        and x['machine_id']==MACHINE and x['status']=='A17_CLOSED_UNKNOWN10565_NO_REPLAY'
        and x['Tasks_absent'] is True and x['screen116_released'] is True
        and x['Game']['exit_code']==1 and x['Game']['forced_owned_job_cleanup'] is True
        and x['Game']['Job_active_final']==0 and x['SDK_actual_exits']=={'sdk_queue':1,'sdk_application':0}
        and type(x['next_sequence']) is int and x['next_sequence']==10569
        and x['current_failed_request_completion_proven'] is False
        and x['old_request_replayed'] is False and x['next_cold_rollback']=={'cycles':5,'days':0},
        'true A17 forced/unknown closure')
    for value in x['sources'].values():_a14_verify_exact_fact(value)
    for key in ('FULL','failed_AUTO','rejected_CAP','rejected_tool_journal',
                'actual_canonical_journal','actual_rich_pixels','media_completed'):
        checked(x[key],131072)
    return x
_A18_PRIOR_POST=validate_post_sem_driver
_A18_PRIOR_VIEW=historical_saved_basis_view
_A18_PRIOR_SEED=validate_saved_seed_a10
def validate_post_sem_driver(pre:dict[str,object],close:dict[str,object],checked:_A18Callable[[object,int],dict[str,object]],verify_current_stat:bool=True)->bool:
    if pre.get('actual_A17_closure')!=A18_CLOSURE_REF:
        return _A18_PRIOR_POST(pre,close,checked,verify_current_stat)
    validate_actual_A17_index_v1(A18_CLOSURE_REF,checked)
    _A18_PRIOR_POST(checked(A18_HISTORICAL_PRE,32768),close,checked,False)
    r=checked(A18_REVIEW_REF,16384)
    require(pre==A18_CURRENT_PRE and type(r['Driver_history_rows']) is int
        and r['Driver_history_rows']==5281,'exact A18 current pre')
    if verify_current_stat:
        identity=r['Driver']['identity'];s=Path(pre['driver_state']['path']).stat()
        require((s.st_size,str(s.st_ino),str(s.st_mtime_ns))==
            (identity['bytes'],identity['file_id'],identity['mtime_ns']),'actual current Driver stat')
        for value in pre['sidecars']:require(checked(value,65536).get('pending') is None,'current sidecars')
    return True
def historical_saved_basis_view(admission:dict[str,object])->dict[str,object]:
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10569,
        'actual10569 not historical10552')
    return _A18_PRIOR_VIEW({**admission,'next_sequence':10552})
def validate_saved_seed_a10(admission:dict[str,object],seed:dict[str,object],original:dict[str,object],save:dict[str,object],semantic:dict[str,object],governance:dict[str,object],*,checked:_A18Callable[[object,int],dict[str,object]],projector:object=None)->bool:
    require(type(admission['next_sequence']) is int and admission['next_sequence']==10569,'actual10569 seed')
    return _A18_PRIOR_SEED({**admission,'next_sequence':10552},seed,original,save,semantic,governance,
        checked=checked,projector=projector)
'''


FEEDER_BASIS_V1 = '''
def old_basis(a:Admit)->Json:
 r=a['sources']['old_ledger']
 need(r==A18_LEDGER_REF and Path(r['path']).resolve()!=LEDGER.resolve(),'immutable A17 ledger')
 need(a['sources']['old_state']==A18_STATE_REF and a['prior_A17_index']==A18_CLOSURE_REF,'actual A17 basis')
 old=checked(r);state=checked(a['sources']['old_state']);pending=obj(state.get('pending_cycle'))
 need(integer(old.get('window_id'))==2 and old.get('status')=='repair_required'
  and integer(old.get('last_settled_cycles'))==4758 and integer(old.get('last_settled_date_raw'))==53274624
  and integer(state.get('completed_cycles'))==4758 and integer(obj(state.get('before')).get('date_raw'))==53274624
  and integer(pending.get('global_turn'))==4759 and integer(pending.get('auto_sequence'))==10565
  and pending.get('stage')=='auto_unsettled' and pending.get('before')==state.get('before')
  and all(state.get(k) is None for k in ('pending_checkpoint','terminal','pending_natural_succession','pending_unsafe_route_halt')),
  'actual unknown10565; five settled cycles discarded')
 bootstrap=cast(Bootstrap,importlib.import_module('root_checkpoint_bootstrap_c23'))
 bootstrap.validate_actual_A17_index_v1(a['prior_A17_index'],checked)
 proof=checked(a['prior_A17_index'])
 need(proof['continuity_ledger']==r and integer(proof.get('next_sequence'))==10569
  and proof.get('current_failed_request_completion_proven') is False and proof.get('old_request_replayed') is False
  and proof.get('next_cold_rollback')=={'cycles':5,'days':0},'unknown preserved; no journal credit')
 return old
'''


def _assign_v1(body: str, name: str, value: object) -> str:
    nodes = [n for n in ast.parse(body).body if isinstance(n, ast.Assign)
             and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id == name]
    need(len(nodes) == 1, "one literal assignment: " + name)
    segment = ast.get_source_segment(body, nodes[0])
    need(segment is not None, "assignment boundary")
    return one(body, text(segment), name + "=" + repr(value))


def patch_feeder_A17_basis_v1(source: bytes, p: PlanV1) -> bytes:
    body = source.decode("utf-8")
    nodes = [n for n in ast.parse(body).body if isinstance(n, ast.FunctionDef) and n.name == "old_basis"]
    need(len(nodes) == 1, "one actual predecessor feeder basis")
    segment = ast.get_source_segment(body, nodes[0])
    need(segment is not None, "actual feeder basis segment")
    body = one(body, text(segment), FEEDER_BASIS_V1.strip())
    body = one(body, "prior_retry02_index:Ref;", "prior_retry02_index:Ref;prior_A17_index:Ref;")
    body = one(body, '"prior_retry02_index","budget"', '"prior_retry02_index","prior_A17_index","budget"')
    body = one(body, "source29_anchor:Ref;", "source29_anchor:Ref;source31_base:Ref;source31_anchor:Ref;")
    body = one(body, '"source29_anchor","prior_A11_index"',
               '"source29_anchor","source31_base","source31_anchor","prior_A11_index"')
    body = one(body, 'base=checked(a["source29_base"])',
               'source29=checked(a["source29_base"]);need(source29.get("source29_canonical_anchor")==a["source29_anchor"],"historical Source29")\n    base=checked(a["source31_base"])')
    body = one(body, 'base.get("source29_canonical_anchor")==a["source29_anchor"]',
               'base.get("source31_canonical_anchor")==a["source31_anchor"]')
    body = one(body, "class Bootstrap(Protocol):", "class Bootstrap(Protocol):\n def validate_actual_A17_index_v1(self,r:Ref,checked:Callable[[Ref,int],Json])->object:...")
    body = one(body, '"prior_retry02_index":a["prior_retry02_index"],',
               '"prior_retry02_index":a["prior_retry02_index"],"prior_A17_index":a["prior_A17_index"],')
    body = one(body, "last_A17_SAVE10480_retry02_rollback", "last_A18_SAVE10480_A17_rollback")
    body = _assign_v1(body, "KIND", "A18_SAVE10480_A17_rollback_verified")
    body = _assign_v1(body, "ROLLBACK", {"saved_cycles":4753,"A17_settled_cycles":4758,
        "cycles_lost":5,"settled_days_lost":0,"unknown_AUTO":10565,"unknown_AUTO_credit":0,
        "prior_unknown_AUTO":10534,"post_failure_readonly_journal":10568,"pending_global_turn":4759})
    state = ref(PREVIOUS / "p37-queue/ROOT-CUMULATIVE-LOOP-STATE.json")
    ledger = checked(p["ledger_ref"], 65536)
    need(record(record(record(ledger["interruption"])["source"])["settled_state"])["sha256"] == state["sha256"],
         "actual closure frozen state hash")
    constants: Doc = {"A18_CLOSURE_REF":p["closure_ref"],"A18_LEDGER_REF":p["ledger_ref"],"A18_STATE_REF":state}
    body = "\n".join(k+"="+repr(v) for k,v in constants.items())+"\n"+body
    compile(body, "A18 actual feeder basis", "exec")
    return body.encode("utf-8")


def remap_policy_v1(policy: Doc) -> Doc:
    names = {"observer_journal_v1.py": NATIVE32_ADAPTER_NAME,
             "native31_mcp_extension_v1.py": NATIVE32_EXTENSION_NAME}
    def project(value: object) -> object:
        if isinstance(value, dict):
            return {names.get(str(k)+".py", str(k)+".py")[:-3] if str(k) in
                    ("observer_journal_v1", "native31_mcp_extension_v1") else str(k): project(v)
                    for k, v in value.items()}
        if isinstance(value, list):
            return [project(v) for v in value]
        if isinstance(value, tuple):
            return tuple(project(v) for v in value)
        if isinstance(value, str) and Path(value).name in names:
            return str(Path(value).with_name(names[Path(value).name]))
        return value
    return record(project(policy))


def _intake_v1() -> tuple[dict[str, bytes], Doc, Doc]:
    source, quote, policy = _accepted_v1()
    for old, new in (("observer_journal_v1.py", NATIVE32_ADAPTER_NAME),
                     ("native31_mcp_extension_v1.py", NATIVE32_EXTENSION_NAME)):
        del source[old]
        source[new] = read_ref(ref(CANDIDATE / new))
    return source, quote, remap_policy_v1(policy)


def _build_sources_v1(p: PlanV1, pre: Doc, historical: Doc) -> tuple[dict[str, bytes], Doc]:
    source, q, policy = _accepted_v1()
    stage_raw = read_ref(p["stage_producer"]).decode("utf-8")
    nodes = [n for n in ast.parse(stage_raw).body if isinstance(n, ast.Assign)
             and len(n.targets)==1 and isinstance(n.targets[0], ast.Name) and n.targets[0].id=="REG31"]
    need(len(nodes)==1, "one accepted Native31 registration literal")
    old_registration = ast.literal_eval(nodes[0].value)
    need(type(old_registration) is str, "literal original registration")
    wire = checked(p["native_binding_ref"], 16384)
    _, _, exports = _native32_v1(p)
    adapters = {NATIVE32_ADAPTER_NAME:read_ref(p["runtime_adapter_ref"]),
                NATIVE32_EXTENSION_NAME:read_ref(p["runtime_extension_ref"])}
    source = native32_source_stage_v2(source, adapters=adapters,
        legacy_registration=text(old_registration), native_label=NATIVE32_LABEL,
        dll=refs(wire["dll"]), export_rvas=exports)
    boot = source["root_checkpoint_bootstrap_c23.py"].decode("utf-8")
    boot = one(boot, "if __name__ == '__main__':",
               _source31_runtime_v1(p)+_bridge_v1(p,pre)+"\nif __name__ == '__main__':")
    source["root_checkpoint_bootstrap_c23.py"] = boot.encode("utf-8")
    body = source["root_native30_supervisor_c23.py"].decode("utf-8")
    body = one(body, "type(actual_next) is int and actual_next==10552",
                    "type(actual_next) is int and actual_next==10569")
    closure = _bridge_v1(p,pre).split("_A18_PRIOR_POST=")[0]
    body = one(body, "def main(args):", closure+'''
_A18_PRIOR_ATTEMPT=_validate_a15_attempt
def _validate_a15_attempt(args,config):
    value=_A18_PRIOR_ATTEMPT(args,config)
    closed=validate_actual_A17_index_v1(A18_CLOSURE_REF,_a03_checked)
    last=_a03_checked(closed['sources']['ROOT-FRESH-SUPERVISOR-CLOSED-C23-A15.json'],16384)
    used={last['attempt_nonce'],last['task_nonce'],last['owned_cleanup']['nonce']}
    require(args.attempt_nonce not in used and args.task_nonce not in used,'independent A18 nonces')
    return value
'''+"\ndef main(args):")
    source["root_native30_supervisor_c23.py"] = body.encode("utf-8")
    source["launch_a10_saved10480_feeder01.py"] = patch_feeder_A17_basis_v1(
        source["launch_a10_saved10480_feeder01.py"], p)
    for name, raw in source.items():
        if name.endswith(".py"):
            compile(raw, name, "exec")
    old_review = record(q["sources"])
    accepted_rows = [ref(PREVIOUS / name) for name in sorted(source)
                     if name not in (NATIVE32_ADAPTER_NAME,NATIVE32_EXTENSION_NAME)]
    review: Doc = {"schema":"xar.A18-accepted-source-carry/v1","machine_id":MACHINE,
        "runtime_source_output_names":sorted(source),"actual_source_rows":accepted_rows,
        "supplemental_import_rows":remap_policy_v1({"v":old_review["supplemental_import_rows"]})["v"],
        "staging_files":remap_policy_v1({"v":old_review["staging_files"]})["v"],
        "actual_A17_index":p["closure_ref"],"feeder":{},"accepted_policy":remap_policy_v1(policy),
        "new_day_credit":0,"replaced_native_sources":[p["runtime_adapter_ref"],p["runtime_extension_ref"]]}
    return source,review


def _native_compose_source_v1(source: str, p: PlanV1) -> str:
    source=one(source,'    recipe=function(a05,"compose")','    recipe=function(a05,"compose")\n    recipe=one(recipe,"    policy=checked(oldfreeze[\'canonical_preload_policy\'],32768)","    policy=checked(oldfreeze[\'canonical_preload_policy\'],32768)\\n    policy=json.loads(json.dumps(source_review[\'accepted_policy\']))")')
    source = one(source, '"xar.C23-Native31-compiled-cold-session/v1"',
                       '"xar.C23-Native32-compiled-cold-session/v1"')
    source = one(source, '"Native31_build_input_manifest"', '"Native32_build_input_manifest"')
    source = one(source, '"source_overlay":production_doc["source_overlay"]',
        '"source_overlay":{k:production_doc["sources"]["overlay"][k] for k in ("path","bytes","sha256")}')
    source = one(source, 'native31_binding=plan["native_binding_ref"]',
                       'native32_binding=plan["native_binding_ref"]')
    source = one(source, '"NATIVE31_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"',
                       '"NATIVE32_SDKC23_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"')
    marker = '    native_freeze={k:native_values[k] for k in ("native_build_label","dll_sha256","git_head")}'
    binding_raw = read_ref(p["native_binding_ref"],16384)
    binding_ref: ExactRef = {"path":str(TARGET/NATIVE32_OBSERVER_BINDING_NAME),
                            "bytes":len(binding_raw),"sha256":sha(binding_raw)}
    source = one(source, marker,
        "    native_metadata.update(native32_observer_binding="+repr(binding_ref)+
        ",git_head_role='runtime_host_checkout',production_input_manifest=build_input)\n"+marker)
    marker2 = '    oldconfig=checked(ref(U13/"ROOT-LAUNCH-CONFIG-C23-A13.json"),16384)'
    source = one(source, marker2, "    native_freeze.update(native32_observer_binding="+repr(binding_ref)+
                 ",git_head_role='runtime_host_checkout')\n"+marker2)
    return source


def _factory_v1(p: PlanV1, pre: Doc, pre_raw: bytes) -> tuple[ModuleType, Doc]:
    sys.path.insert(0,str(OWN.parent.parent))
    raw = read_ref(previous.fixed(OWN / "prepare_source29_a17_cold_union_v1.py", M17_PIN))
    clone = ModuleType("_a18_verified_a17_factory")
    clone.__file__ = str(OWN / "prepare_source29_a17_cold_union_v1.py")
    sys.modules[clone.__name__] = clone
    exec(compile(raw, clone.__file__, "exec"), vars(clone))
    factory_source = function_source_v1(clone, "_factory")
    factory_source = one(factory_source, '"new_first_sequence=10552"', '"new_first_sequence=10569"')
    factory_source = one(factory_source, '"spec-supervisor-a17"', '"spec-supervisor-a18"')
    factory_source = one(factory_source, '"source29_canonical_anchor"', '"source31_canonical_anchor"')
    factory_source = one(factory_source, '"xar.source29."', '"xar.source31."')
    factory_source = one(factory_source, '"source29_static_binding"', '"source31_static_binding"')
    marker = '   result=result.replace("source28_static_binding","source31_static_binding")'
    factory_source = one(factory_source, marker, marker+"\n   result=_native_compose_source_v1(result,p)")
    vars(clone).update(PREVIOUS=PREVIOUS,TARGET=TARGET,PREP=PREP,SCREEN=SCREEN,
        _source29=_source31_v1,_closed=_closed_v1,_accepted=_intake_v1,
        _build_sources=_build_sources_v1,_native_compose_source_v1=_native_compose_source_v1,
        __file__=__file__)
    exec(compile(factory_source, "<A18 finite verified factory>", "exec"), vars(clone))
    result = previous.pair(dynamic(clone,"_factory")(p,pre,pre_raw))
    need(isinstance(result[0],ModuleType), "actual complete cold factory")
    made = cast(ModuleType,result[0])
    function = getattr(made,"compose",None)
    need(isinstance(function,FunctionType), "real compose globals")
    cast(FunctionType,function).__globals__["_native"] = lambda unused:_native32_v1(p)
    return made,record(result[1])


def compose(plan_value: object, *, display_values: dict[str,bytes],
        display_review: Doc, companion_values: Outputs) -> tuple[Outputs,Doc]:
    p=parse_plan(plan_value)
    need(not TARGET.exists() and ref(__file__)==p["union_producer"], "absent new runtime and exact producer")
    pre,raw = _current_pre_v1(p)
    factory,projected = _factory_v1(p,pre,raw)
    result = previous.pair(dynamic(factory,"compose")(projected,display_values=display_values,
        display_review=display_review,companion_values=companion_values))
    out,quote=previous.outputs(result[0]),record(result[1])
    need(len(out)==uint(quote["unique_files"])==144, "original full144 postguard before extra binding")
    out[TARGET/"NEXT-SEQUENCE-P37.json"]=read_ref(p["current_next_ref"],16384)
    binding_raw=read_ref(p["native_binding_ref"],16384)
    out[TARGET/NATIVE32_OBSERVER_BINDING_NAME]=binding_raw
    rows: list[Doc]=[]
    for item in sequence(quote["files"]):
        row=record(item);path=Path(text(row["path"]));body=out[path]
        row.update(bytes=len(body),sha256=sha(body))
        if path==TARGET/"NEXT-SEQUENCE-P37.json":
            row.update(mode="hardlink",source=p["current_next_ref"],allocation_upper=0)
        rows.append(row)
    rows.append({"path":str(TARGET/NATIVE32_OBSERVER_BINDING_NAME),"bytes":len(binding_raw),
        "sha256":sha(binding_raw),"mode":"hardlink","source":p["native_binding_ref"],"allocation_upper":0})
    quote.update(schema="xar.Source31-A18-complete-cold-quote/v1",producer=p["union_producer"],
        unique_files=len(out),files=sorted(rows,key=lambda r:text(r["path"])),
        actual_A17_index=p["closure_ref"],current_driver_review=p["current_driver_review_ref"],
        continuity_ledger=p["ledger_ref"],new_first_sequence=10569,rollback_cycles=5,rollback_days=0,
        unknown10565_credit=0,consumed_readonly_journal=10568,original_wall_origin_reset=False,
        body_reads_Driver_SAVE_hash=2,body_read_bytes_Driver=refs(pre["driver_state"])["bytes"],
        Driver_full_read_bytes=refs(pre["driver_state"])["bytes"],SAVE_body_reads=1,
        SAVE_full_read_bytes=pre["SAVE_body_read_bytes"],copies_created=0,
        native32_runtime_qualified=False,native32_loaded_provider_issued=False,
        native32_observer_binding={"path":str(TARGET/NATIVE32_OBSERVER_BINDING_NAME),
            "bytes":len(binding_raw),"sha256":sha(binding_raw)})
    quote["preparation_contract_sources"]=[ref(OWN/"write_source27_canonical_ref_v1.py")]
    quote["campaign_score_junction"]={"path":str(TARGET/"campaign-score"),
        "exact_target":str(P/"robert30-v20261019-campaign01/runtime/campaign-score"),"must_verify_same_FileID":True}
    quote["prerequisite_directories"]=sorted({text(v) for v in sequence(quote["prerequisite_directories"])}
        |{str(TARGET/"campaign-score")})
    quote.update(logical_bytes=sum(map(len,out.values())),
        fresh_allocation_upper=sum(uint(r["allocation_upper"]) for r in rows),
        immutable_hardlinks=sum(r["mode"]=="hardlink" for r in rows),
        max_atomic_copy=max((len(b)+4095)//4096*4096 for b in out.values()))
    quote["prepare_peak_upper"]=sum(uint(quote[k]) for k in ("fresh_allocation_upper","max_atomic_copy",
        "future_owner_metadata_upper","control_probe_atomic_peak","intent_receipt_and_FS_upper"))
    need(len(out)==len(rows)==145 and len(set(out))==145,"actual unique145")
    return out,quote


def _metadata_clone_v1(p: PlanV1) -> ModuleType:
    raw=read_ref(previous.fixed(OWN/"prepare_source29_a17_cold_union_v1.py",M17_PIN))
    module=ModuleType("_a18_legacy_metadata_projection")
    module.__file__=str(OWN/"prepare_source29_a17_cold_union_v1.py")
    sys.modules[module.__name__]=module
    exec(compile(raw,module.__file__,"exec"),vars(module))
    vars(module).update(TARGET=TARGET,PREVIOUS=PREVIOUS,PREP=PREP,parse_plan=lambda unused:p)
    return module


def metadata_source(plan_value: object, source: str) -> str:
    p=parse_plan(plan_value)
    module=_metadata_clone_v1(p)
    value=text(dynamic(module,"metadata_source")(p,source))
    marker="'source29_anchor':A17_SOURCE29_ANCHOR,'source29_base':A17_SOURCE29_BASE"
    value=one(value,marker,marker+
        ",'source31_anchor':A18_SOURCE31_ANCHOR,'source31_base':A18_SOURCE31_BASE"+
        ",'native32_observer_binding':A18_NATIVE32_BINDING")
    value=one(value,"anchor_ref=freeze['source29_canonical_anchor']","anchor_ref=freeze['source31_canonical_anchor']")
    # Source29 stays a real historical input; the deployed bootstrap validates new31.
    value=one(value,"base.get('source29_canonical_anchor')==A17_SOURCE29_ANCHOR",
        "base.get('source31_canonical_anchor')==A18_SOURCE31_ANCHOR") if \
        "base.get('source29_canonical_anchor')==A17_SOURCE29_ANCHOR" in value else value
    value=value.replace("ROOT-FINAL-SDK-FREEZE-P37C23-A18.json",
                        "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")
    compile(value,"<A18 typed owner metadata projection>","exec")
    return value


def metadata_scope(plan_value: object, namespace: Doc, runtime: Path) -> None:
    p=parse_plan(plan_value)
    need(runtime.resolve()==TARGET.resolve(),"A18 deployed metadata namespace")
    module=_metadata_clone_v1(p)
    dynamic(module,"metadata_scope")(p,namespace,runtime)
    old=_old_plan_v1()
    namespace.update(A17_SOURCE29_BASE=old["sdk_base_ref"],A17_SOURCE29_ANCHOR=old["canonical_anchor_ref"],
        A18_SOURCE31_BASE=p["sdk_base_ref"],A18_SOURCE31_ANCHOR=p["canonical_anchor_ref"],
        A18_NATIVE32_BINDING=ref(TARGET/NATIVE32_OBSERVER_BINDING_NAME))
    # The actual runtime bootstrap is already pinned by the generic loader.
    # Its public A18 validator preserves the full historical Source29/28 chain.
    path=runtime/NATIVE32_ADAPTER_NAME
    candidate=read_ref(p["runtime_adapter_ref"])
    need(path.read_bytes()==candidate,"deployed Native32 adapter exact preparation bytes")
    helper=load_registered_source_v1("observer_journal_runtime_v1",candidate)
    binding=checked(ref(runtime/NATIVE32_OBSERVER_BINDING_NAME),16384)
    dynamic(helper,"qualify_native32_binding_v1")(binding,machine_id=MACHINE)


class RuntimeCapacityV1(TypedDict):
    D_free_floor_bytes: int
    Z_free_floor_bytes: int


class RuntimeAdmissionV1(TypedDict):
    schema: Literal["xar.Source31-A18-runtime-prepare-admission/v1"]
    machine_id: str
    owner: Literal["Root"]
    status: Literal["ADMITTED"]
    root_direct_execution_release: Literal[True]
    plan: ExactRef
    quote: ExactRef
    full_storage_ref: ExactRef
    canonical_capacity_review_passed: Literal[True]
    runtime_hard_bytes: int
    capacity: RuntimeCapacityV1


def _positive_safe_v1(value: object, field: str) -> int:
    need(type(value) is int and 0<value<=2**53-1,field+" exact positive safe integer")
    return cast(int,value)


def _admission_reference_v1(row: Doc, name: str) -> ExactRef:
    value=refs(row.get(name))
    _positive_safe_v1(value["bytes"],name+".bytes")
    need(Path(value["path"]).is_absolute(),name+" absolute source")
    return value


def parse_runtime_admission_v1(value: object, *, expected_machine_id: str) -> RuntimeAdmissionV1:
    """Pure A18 core. The adopter separately checks current refs, quotas and roots."""
    need(type(expected_machine_id) is str and bool(expected_machine_id),"explicit machine")
    row=record(value)
    need(row.get("schema")=="xar.Source31-A18-runtime-prepare-admission/v1","single current A18 schema")
    need(row.get("machine_id")==expected_machine_id and row.get("owner")=="Root"
        and row.get("status")=="ADMITTED" and row.get("root_direct_execution_release") is True
        and row.get("canonical_capacity_review_passed") is True,"actual Root admitted capacity review")
    need("hard_bytes" not in row,"no legacy hard_bytes alias")
    capacity=record(row.get("capacity"))
    need(not ({"D_conservative_floor_bytes","Z_conservative_floor_bytes"} & set(capacity)),
         "no legacy capacity aliases")
    return {"schema":"xar.Source31-A18-runtime-prepare-admission/v1",
        "machine_id":expected_machine_id,"owner":"Root","status":"ADMITTED",
        "root_direct_execution_release":True,"canonical_capacity_review_passed":True,
        "plan":_admission_reference_v1(row,"plan"),"quote":_admission_reference_v1(row,"quote"),
        "full_storage_ref":_admission_reference_v1(row,"full_storage_ref"),
        "runtime_hard_bytes":_positive_safe_v1(row.get("runtime_hard_bytes"),"runtime_hard_bytes"),
        "capacity":{"D_free_floor_bytes":_positive_safe_v1(capacity.get("D_free_floor_bytes"),"capacity.D_free_floor_bytes"),
                    "Z_free_floor_bytes":_positive_safe_v1(capacity.get("Z_free_floor_bytes"),"capacity.Z_free_floor_bytes")}}

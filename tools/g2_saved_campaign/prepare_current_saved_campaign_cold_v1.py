"""Independent current saved checkpoint cold composition; no runtime side effects."""
from __future__ import annotations
import ast
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import ntpath
from pathlib import Path
import re
from typing import Literal
from tools.g2_saved_campaign.current_saved_basis_v1 import (
 CurrentSavedBasisV1, ExactRefV1, JsonObject, JsonValue, digest, integer,
 json_object, json_value, need, parse_current_saved_basis_v1, parse_json,
 parse_ref, record, rows, text, utc,
)
PLAN_SCHEMA = "xar.current-saved-cold-plan/v1"
QUOTE_SCHEMA = "xar.current-saved-cold-quote/v1"
MAX_FILE = 1048576
MAX_GRAPH = 8 * MAX_FILE
CANONICAL_NAMES = frozenset((
 "launch_sdk_p37c23_owner.py", "native32_mcp_extension_v1.py",
 "observer_journal_runtime_v1.py", "root_c23_canonical_outer.py",
 "root_checkpoint_bootstrap_c23.py", "root_native30_supervisor_c23.py",
 "root_p37c23_mcp_entry.py", "root_p37c23_sdk_queue.py",
))
GENERIC_SOURCE_NAMES = frozenset((
 "current_saved_basis_v1.py", "file_stat_identity_v1.py",
 "root_current_saved_campaign_cold_owner_v1.py",
 "current_saved_campaign_feeder_v1.py",
 "prepare_current_saved_campaign_cold_v1.py", "root_saved_campaign_preflight.py",
))
def sha256_v1(raw: bytes) -> str:
 need(type(raw) is bytes, "exact source bytes")
 return hashlib.sha256(raw).hexdigest()
def encode_v1(value: object) -> bytes:
 return (json.dumps(json_value(value), ensure_ascii=False, sort_keys=True,
       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
def absolute_v1(value: object) -> str:
 result = text(value)
 need(ntpath.isabs(result) and ntpath.splitdrive(result)[0] != ""
   and ntpath.normpath(result) == result.replace("/", "\\"),
   "normalized absolute Windows path")
 return result
def relative_v1(value: object, *, allow_root: bool = False) -> str:
 result = text(value)
 need("\\" not in result and ":" not in result and not result.startswith("/")
   and (result == "." and allow_root or all(part not in ("", ".", "..")
    for part in result.split("/"))), "confined canonical relative path")
 return result
def paths_v1(value: object, *, allow_root: bool = False) -> tuple[str, ...]:
 result = tuple(relative_v1(item, allow_root=allow_root) for item in rows(value))
 need(bool(result) and len(result) <= 192 and len(set(result)) == len(result),
   "bounded unique path set")
 return result
def nonce_v1(value: object) -> str:
 result = text(value)
 need(re.fullmatch("[0-9a-f]{32}", result) is not None, "independent canonical nonce")
 return result
def child_v1(root: str, relative: str) -> str:
 absolute_v1(root)
 relative_v1(relative)
 return ntpath.join(root, *relative.split("/"))
def ref_for_bytes_v1(path: str, raw: bytes) -> ExactRefV1:
 return ExactRefV1(absolute_v1(path), len(raw), sha256_v1(raw))
def read_ref_v1(reference: ExactRefV1, limit: int = MAX_FILE) -> bytes:
 integer(limit, 1, MAX_GRAPH)
 need(reference.bytes <= limit, "bounded metadata/source reference")
 path = Path(reference.path)
 before = path.stat()
 need(before.st_size == reference.bytes, "source byte size drift")
 with path.open("rb") as stream:
  raw = stream.read(limit + 1)
 after = path.stat()
 need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
   (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
   and len(raw) == reference.bytes and sha256_v1(raw) == reference.sha256,
   "exact source identity/bytes/SHA drift")
 return raw
@dataclass(frozen=True, slots=True)
class SourceRowV1:
 source_ref: ExactRefV1
 relative_path: str
 def to_wire(self) -> JsonObject:
  return {"source_ref": self.source_ref.to_wire(), "relative_path": self.relative_path}
def parse_source_row_v1(value: object) -> SourceRowV1:
 row = record(value, {"source_ref", "relative_path"})
 result = SourceRowV1(parse_ref(row["source_ref"]), relative_v1(row["relative_path"]))
 need(result.source_ref.bytes <= MAX_FILE and result.relative_path.endswith(".py"),
   "bounded Python shared dependency")
 return result
@dataclass(frozen=True, slots=True)
class ColdPlanV1:
 machine_id: str
 observed_at_utc: str
 review_at_utc: str
 runtime_root: str
 material_runtime_root: str
 material_quote_ref: ExactRefV1
 basis_ref: ExactRefV1
 validation_ref: ExactRefV1
 producer_ref: ExactRefV1
 source_rows: tuple[SourceRowV1, ...]
 canonical_entry_paths: tuple[str, ...]
 closure_entry_paths: tuple[str, ...]
 import_roots: tuple[str, ...]
 full_storage_ref: ExactRefV1
 steam_native_state_ref: ExactRefV1
 screen_admission_path: str
 supervisor_spec_path: str
 display_nonce: str
 attempt_nonce: str
 task_nonce: str
 business_source_generation: Literal[31,32]
 sdk_base_ref: ExactRefV1
 sdk_anchor_ref: ExactRefV1
 def to_wire(self) -> JsonObject:
  return {"schema": PLAN_SCHEMA, "machine_id": self.machine_id,
   "observed_at_utc": self.observed_at_utc, "review_at_utc": self.review_at_utc,
   "runtime_root": self.runtime_root, "material_runtime_root": self.material_runtime_root,
   "material_quote_ref": self.material_quote_ref.to_wire(), "basis_ref": self.basis_ref.to_wire(),
   "validation_ref": self.validation_ref.to_wire(), "producer_ref": self.producer_ref.to_wire(),
   "source_rows": [item.to_wire() for item in self.source_rows],
   "canonical_entry_paths": list(self.canonical_entry_paths),
   "closure_entry_paths": list(self.closure_entry_paths), "import_roots": list(self.import_roots),
   "full_storage_ref": self.full_storage_ref.to_wire(),
   "steam_native_state_ref": self.steam_native_state_ref.to_wire(),
   "screen_admission_path": self.screen_admission_path, "supervisor_spec_path": self.supervisor_spec_path,
   "display_nonce": self.display_nonce, "attempt_nonce": self.attempt_nonce, "task_nonce": self.task_nonce,
   "business_source_generation":self.business_source_generation,"sdk_base_ref":self.sdk_base_ref.to_wire(),
   "sdk_anchor_ref":self.sdk_anchor_ref.to_wire()}
PLAN_FIELDS = {"schema", "machine_id", "observed_at_utc", "review_at_utc", "runtime_root",
 "material_runtime_root", "material_quote_ref", "basis_ref", "validation_ref", "producer_ref",
 "source_rows", "canonical_entry_paths", "closure_entry_paths", "import_roots", "full_storage_ref",
 "steam_native_state_ref", "screen_admission_path", "supervisor_spec_path", "display_nonce",
 "attempt_nonce", "task_nonce", "business_source_generation", "sdk_base_ref", "sdk_anchor_ref"}
def business_generation_v1(value: object) -> Literal[31,32]:
 number=integer(value,31,32)
 return 31 if number==31 else 32
def parse_plan_v1(value: object) -> ColdPlanV1:
 row = record(value, PLAN_FIELDS)
 need(row["schema"] == PLAN_SCHEMA, "current saved cold plan schema")
 result = ColdPlanV1(text(row["machine_id"]), utc(row["observed_at_utc"]), utc(row["review_at_utc"]),
  absolute_v1(row["runtime_root"]), absolute_v1(row["material_runtime_root"]),
  parse_ref(row["material_quote_ref"]), parse_ref(row["basis_ref"]), parse_ref(row["validation_ref"]),
  parse_ref(row["producer_ref"]), tuple(parse_source_row_v1(item) for item in rows(row["source_rows"])),
  paths_v1(row["canonical_entry_paths"]), paths_v1(row["closure_entry_paths"]),
  paths_v1(row["import_roots"], allow_root=True), parse_ref(row["full_storage_ref"]),
  parse_ref(row["steam_native_state_ref"]), absolute_v1(row["screen_admission_path"]),
  absolute_v1(row["supervisor_spec_path"]), nonce_v1(row["display_nonce"]),
  nonce_v1(row["attempt_nonce"]), nonce_v1(row["task_nonce"]),
  business_generation_v1(row["business_source_generation"]),parse_ref(row["sdk_base_ref"]),parse_ref(row["sdk_anchor_ref"]))
 need(result.runtime_root.casefold() != result.material_runtime_root.casefold()
   and len({result.display_nonce, result.attempt_nonce, result.task_nonce}) == 3,
   "fresh independent software/recording/Task namespace")
 need(datetime.fromisoformat(result.observed_at_utc.replace("Z", "+00:00")) <
   datetime.fromisoformat(result.review_at_utc.replace("Z", "+00:00")), "review follows observation")
 need(len(result.canonical_entry_paths) == 8 and set(result.canonical_entry_paths) == CANONICAL_NAMES
   and set(result.canonical_entry_paths) <= set(result.closure_entry_paths)
   and len(result.closure_entry_paths) <= 64, "canonical max8 and complete bounded closure")
 need(len(result.source_rows) == len(GENERIC_SOURCE_NAMES)
   and {ntpath.basename(item.relative_path) for item in result.source_rows} == GENERIC_SOURCE_NAMES
   and len({item.relative_path for item in result.source_rows}) == len(result.source_rows)
         and {item.relative_path for item in result.source_rows} <= set(result.closure_entry_paths)
         and all(item.relative_path == "tools/g2_saved_campaign/" + ntpath.basename(item.relative_path)
                 for item in result.source_rows),
   "all generic shared dependencies explicitly belong to complete closure")
 need(any(item.source_ref == result.producer_ref for item in result.source_rows),
   "actual producer source participates in closure")
 need(result.basis_ref.bytes <= 65536 and result.validation_ref.bytes <= 65536,
   "small qualified current basis")
 return result
@dataclass(frozen=True, slots=True)
class OutputRowV1:
 path: str
 relative_path: str | None
 bytes: int
 sha256: str
 mode: Literal["create-only", "hardlink"]
 source_ref: ExactRefV1 | None
 def to_wire(self) -> JsonObject:
  return {"path": self.path, "relative_path": self.relative_path, "bytes": self.bytes,
    "sha256": self.sha256, "mode": self.mode,
    "source_ref": None if self.source_ref is None else self.source_ref.to_wire()}
def parse_output_row_v1(value: object, *, runtime_root: str) -> OutputRowV1:
 row = record(value, {"path", "relative_path", "bytes", "sha256", "mode", "source_ref"})
 mode = row["mode"]
 need(mode in ("create-only", "hardlink") and type(mode) is str, "single output mode contract")
 if mode != "create-only" and mode != "hardlink":
  raise ValueError("output mode")
 relative = None if row["relative_path"] is None else relative_v1(row["relative_path"])
 reference = None if row["source_ref"] is None else parse_ref(row["source_ref"])
 result = OutputRowV1(absolute_v1(row["path"]), relative, integer(row["bytes"], 1, MAX_FILE),
                        digest(row["sha256"]), "hardlink" if mode == "hardlink" else "create-only", reference)
 need((result.mode == "hardlink") == (reference is not None), "explicit hardlink provenance")
 if reference is not None:
  need((result.bytes, result.sha256) == (reference.bytes, reference.sha256)
    and result.path.casefold() != reference.path.casefold(), "immutable source hardlink")
 if relative is not None:
  need(result.path == child_v1(runtime_root, relative), "exact runtime-relative output mapping")
 else:
  need(not ntpath.commonpath((runtime_root, result.path)).casefold() == runtime_root.casefold(),
    "external outputs explicitly outside runtime")
 return result
@dataclass(frozen=True, slots=True)
class ColdQuoteV1:
 machine_id: str
 observed_at_utc: str
 plan_ref: ExactRefV1
 basis_ref: ExactRefV1
 validation_ref: ExactRefV1
 producer_ref: ExactRefV1
 runtime_root: str
 files: tuple[OutputRowV1, ...]
 canonical_entry_paths: tuple[str, ...]
 closure_entry_paths: tuple[str, ...]
 import_roots: tuple[str, ...]
 canonical_entry_limit: Literal[8]
 logical_bytes: int
 allocation_upper: int
 prepare_peak_upper: int
 def to_wire(self) -> JsonObject:
  return {"schema": QUOTE_SCHEMA, "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
   "plan_ref": self.plan_ref.to_wire(), "basis_ref": self.basis_ref.to_wire(),
   "validation_ref": self.validation_ref.to_wire(), "producer_ref": self.producer_ref.to_wire(),
   "runtime_root": self.runtime_root, "files": [item.to_wire() for item in self.files],
   "canonical_entry_paths": list(self.canonical_entry_paths),
   "closure_entry_paths": list(self.closure_entry_paths), "import_roots": list(self.import_roots),
   "canonical_entry_limit": self.canonical_entry_limit, "logical_bytes": self.logical_bytes,
   "allocation_upper": self.allocation_upper, "prepare_peak_upper": self.prepare_peak_upper,
   "ordinary_cycle_credit": 0, "game_day_credit": 0, "original_actions_replayed": False}
QUOTE_FIELDS = {"schema", "machine_id", "observed_at_utc", "plan_ref", "basis_ref", "validation_ref",
 "producer_ref", "runtime_root", "files", "canonical_entry_paths", "closure_entry_paths",
 "import_roots", "canonical_entry_limit", "logical_bytes", "allocation_upper", "prepare_peak_upper",
 "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed"}
def allocation_v1(size: int) -> int:
 return ((integer(size, 1) + 4095) // 4096) * 4096
def parse_quote_v1(value: object) -> ColdQuoteV1:
 row = record(value, QUOTE_FIELDS)
 need(integer(row["canonical_entry_limit"],8,8) == 8 and row["schema"] == QUOTE_SCHEMA and integer(row["ordinary_cycle_credit"]) == 0
   and integer(row["game_day_credit"]) == 0 and row["original_actions_replayed"] is False,
   "cold software adds no progress/replay")
 root = absolute_v1(row["runtime_root"])
 result = ColdQuoteV1(text(row["machine_id"]), utc(row["observed_at_utc"]),
  parse_ref(row["plan_ref"]), parse_ref(row["basis_ref"]), parse_ref(row["validation_ref"]),
  parse_ref(row["producer_ref"]), root,
  tuple(parse_output_row_v1(item, runtime_root=root) for item in rows(row["files"])),
  paths_v1(row["canonical_entry_paths"]), paths_v1(row["closure_entry_paths"]),
  paths_v1(row["import_roots"], allow_root=True), 8,
  integer(row["logical_bytes"], 1, MAX_GRAPH), integer(row["allocation_upper"], 1, MAX_GRAPH),
  integer(row["prepare_peak_upper"], 1, MAX_GRAPH))
 paths = [item.path.casefold() for item in result.files]
 relative = {item.relative_path for item in result.files if item.relative_path is not None}
 need(1 <= len(result.files) <= 192 and len(paths) == len(set(paths))
   and set(result.canonical_entry_paths) == CANONICAL_NAMES
   and set(result.canonical_entry_paths) <= set(result.closure_entry_paths) <= relative
   and len(result.closure_entry_paths) <= 64, "unique outputs cover actual complete closure/max8")
 allocated = sum(allocation_v1(item.bytes) for item in result.files if item.mode == "create-only")
 need(result.logical_bytes == sum(item.bytes for item in result.files)
   and result.allocation_upper == allocated
   and result.prepare_peak_upper == allocated + max(item.bytes for item in result.files) + 131072,
   "exact bounded software allocation arithmetic")
 return result
@dataclass(frozen=True, slots=True)
class ColdComposeV1:
 files: dict[str, bytes]
 quote: ColdQuoteV1
def relocate_text_v1(value: str, plan: ColdPlanV1, old_nonce: str) -> str:
 result = value
 old = plan.material_runtime_root
 new = plan.runtime_root
 for before, after in ((old.replace("\\", "\\\\"), new.replace("\\", "\\\\")),
       (old, new), (old.replace("\\", "/"), new.replace("\\", "/"))):
  result = result.replace(before, after)
 return result.replace(old_nonce, plan.display_nonce)
def rewrite_json_v1(value: object, plan: ColdPlanV1, old_nonce: str,
     source_pins: dict[str, ExactRefV1]) -> JsonValue:
 if type(value) is str:
  return relocate_text_v1(value, plan, old_nonce)
 if type(value) is list:
  if not isinstance(value, list):
   raise ValueError("list")
  rewritten = [rewrite_json_v1(item, plan, old_nonce, source_pins) for item in value]
  if len(rewritten) == 2 and type(rewritten[0]) is str:
   target = rewritten[0]
   if isinstance(target, str) and target in source_pins:
    return [target, source_pins[target].sha256]
  return rewritten
 if type(value) is dict:
  original = record(value)
  rewritten_map: JsonObject = {
   key: rewrite_json_v1(item, plan, old_nonce, source_pins) for key, item in original.items()}
  mapped_target = rewritten_map.get("path")
  if isinstance(mapped_target, str) and mapped_target in source_pins and {"bytes", "sha256"} <= set(rewritten_map):
   pin = source_pins[mapped_target]
   rewritten_map.update(bytes=pin.bytes, sha256=pin.sha256)
  return rewritten_map
 return json_value(value)
def selected_source_v1(raw: bytes, *, names: set[str], prefix_end: int = 0) -> str:
 source = raw.decode("utf-8")
 lines = source.splitlines(keepends=True)
 tree = ast.parse(source)
 selected: list[str] = []
 found: set[str] = set()
 for node in tree.body:
  if prefix_end and node.lineno < prefix_end:
   selected.append("".join(lines[node.lineno - 1:node.end_lineno]))
  elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names:
   need(node.name not in found, "single selected immutable runtime definition")
   selected.append("".join(lines[node.lineno - 1:node.end_lineno]))
   found.add(node.name)
 need(found == names, "all selected static runtime definitions")
 return "\n".join(selected) + "\n"
def replace_definition_v1(raw: bytes, name: str, replacement: str) -> bytes:
 source = raw.decode("utf-8")
 nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == name]
 need(len(nodes) == 1, "one current runtime function seam: " + name)
 node = nodes[0]
 need(node.end_lineno is not None, "bounded AST function")
 lines = source.splitlines(keepends=True)
 result = "".join(lines[:node.lineno - 1]) + replacement.rstrip() + "\n" + "".join(lines[node.end_lineno:])
 compile(result, "<current saved " + name + ">", "exec")
 return result.encode("utf-8")
def assignment_v1(raw: bytes, name: str, value: object) -> bytes:
 source = raw.decode("utf-8")
 matches = [node for node in ast.parse(source).body if isinstance(node, ast.Assign)
     and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
 need(len(matches) == 1 and matches[0].end_lineno is not None, "single literal assignment: " + name)
 node = matches[0]
 need(node.end_lineno is not None, "assignment extent")
 lines = source.splitlines(keepends=True)
 changed = "".join(lines[:node.lineno - 1]) + name + " = " + repr(json_value(value)) + "\n" + "".join(lines[node.end_lineno:])
 compile(changed, "<current saved " + name + ">", "exec")
 return changed.encode("utf-8")
def literal_assignment_v1(raw: bytes, name: str) -> JsonObject:
 matches = [node for node in ast.parse(raw).body if isinstance(node, ast.Assign)
     and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)]
 need(len(matches) == 1, "one source-bound literal")
 return json_object(ast.literal_eval(matches[0].value))
StateSourceNameV1 = Literal["root_native30_supervisor_c23.py", "launch_sdk_p37c23_owner.py",
 "root_p37c23_sdk_queue.py", "root_p37c23_mcp_entry.py"]
STATE_SOURCES_V1: tuple[StateSourceNameV1,...] = ("root_native30_supervisor_c23.py",
 "launch_sdk_p37c23_owner.py", "root_p37c23_sdk_queue.py", "root_p37c23_mcp_entry.py")
def bind_current_saved_state_source_v1(name:StateSourceNameV1,material:bytes,basis:CurrentSavedBasisV1)->bytes:
 from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import derive_current_saved_state_paths_v1
 paths=derive_current_saved_state_paths_v1(basis)
 state="Path("+repr(paths.state_root)+")"
 seams:dict[StateSourceNameV1,tuple[str,str]]={
  "root_native30_supervisor_c23.py":('environment.make_spec(state_dir=N / "state", game_dir=game_dir)',
   'environment.make_spec(state_dir='+state+', game_dir=game_dir)'),
  "launch_sdk_p37c23_owner.py":("str(N/'state/profile/xar-autoplayer-environment.json')",
   repr(paths.environment_manifest)),
  "root_p37c23_sdk_queue.py":('STATE_DIR = N / "state"','STATE_DIR = '+state),
  "root_p37c23_mcp_entry.py":('STATE_DIR=N/"state"','STATE_DIR='+state),
 }
 before,after=seams[name];source=material.decode("utf-8")
 need(source.count(before)==1,"one active shared state binding: "+name)
 result=source.replace(before,after,1)
 compile(result,"<shared current saved state "+name+">","exec")
 return result.encode("utf-8")
def emit_bootstrap_v1(material: bytes, *, machine_id: str) -> bytes:
 keep = {"require", "sha", "read", "checked", "pin", "api"}
 source = selected_source_v1(material, names=keep, prefix_end=19)
 source += """
from typing import Protocol, runtime_checkable
from tools.g2_saved_campaign.current_saved_basis_v1 import JsonObject, JsonValue, json_object, need, record, rows, text
from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
 load_current_saved_inputs_v1, build_current_saved_prelaunch_v1,
 validate_current_saved_runtime_source_v1,
 validate_current_saved_state_manifest_v1,
)
class CurrentSavedProfileV1(Protocol):
 manifest_path: Path
 state_dir: Path
 profile_dir: Path
@runtime_checkable
class CurrentSavedEnvironmentV1(Protocol):
 def _contract_digest(self, manifest: object) -> str: ...
@runtime_checkable
class CurrentSavedRuntimeV1(Protocol):
 def NativeBridgeLaunchConfig(self, mode: str, pipe: str, dll: Path, injector: Path) -> object: ...
 def launch(self, spec: CurrentSavedProfileV1, *, native_bridge: object, continue_last_save: bool,
  load_save_name: str, verify_prepared_profile: bool, start_minimized: bool,
  native_bridge_after_saved_load: bool, before_process_create: object, pre_native_resume: object) -> object: ...
def verify_cold_profile(spec: CurrentSavedProfileV1) -> JsonObject:
 environment: object = api()[0]
 if not isinstance(environment,CurrentSavedEnvironmentV1): raise ValueError("source-bound environment API")
 inputs = load_current_saved_inputs_v1(runtime_root=N, expected_machine_id=MACHINE)
 manifest = record(read(spec.manifest_path))
 paths = validate_current_saved_state_manifest_v1(inputs.basis,manifest)
 need(spec.state_dir.resolve()==Path(paths.state_root).resolve()
  and spec.profile_dir.resolve()==Path(paths.profile_dir).resolve()
  and spec.manifest_path.resolve()==Path(paths.environment_manifest).resolve(),
  "actual shared state/profile/environment paths")
 pre = record(read(N / PRELAUNCH))
 load = record(manifest["load_profile"])
 need(pre == build_current_saved_prelaunch_v1(inputs.basis,
  basis_ref=inputs.basis_ref, validation_ref=inputs.validation_ref,
  environment_sha256=text(manifest["environment_sha256"]), pipe_name=text(pre["pipe_name"])),
  "current shared saved prelaunch differs")
 need(Path(text(manifest["state_dir"])).resolve() == spec.state_dir.resolve()
  and Path(text(manifest["profile_dir"])).resolve() == spec.profile_dir.resolve()
  and load["enabled_mods"] == []
  and manifest["mod"] == {"enabled": False, "mounted_mods": []}
  and read(spec.profile_dir / "dlc_load.json") == {"enabled_mods": [], "disabled_dlcs": []}
  and sha(spec.profile_dir / "dlc_load.json") == load["dlc_load_sha256"]
  and not any(text(record(row)["rule"]).startswith("xar_") for row in rows(record(manifest["rules"])["profile"]))
  and not ((spec.profile_dir / "mod").exists() and any((spec.profile_dir / "mod").iterdir()))
  and environment._contract_digest(manifest) == manifest["environment_sha256"] == pre["environment_sha256"],
  "current same-profile vanilla ordinary environment")
 return json_object(manifest)
def launch_prepared(spec: CurrentSavedProfileV1, dll: Path, injector: Path, *,
  before_process_create: object = None, pre_native_resume: object = None) -> object:
 runtime: object = api()[2]
 if not isinstance(runtime,CurrentSavedRuntimeV1): raise ValueError("source-bound runtime API")
 verify_cold_profile(spec)
 pre = record(read(N / PRELAUNCH))
 need(callable(pre_native_resume), "actual original pre-resume custody callback")
 bridge = runtime.NativeBridgeLaunchConfig("native-headless", text(pre["pipe_name"]), Path(dll), Path(injector))
 return runtime.launch(spec, native_bridge=bridge, continue_last_save=False,
  load_save_name="xar_checkpoint", verify_prepared_profile=False,
  start_minimized=True, native_bridge_after_saved_load=False,
  before_process_create=before_process_create, pre_native_resume=pre_native_resume)
def validate_source28_frozen_business(admission: object, freeze: object, checked: object = None) -> bool:
 validate_current_saved_runtime_source_v1(admission, freeze, runtime_root=N, expected_machine_id=MACHINE)
 return True
"""
 source = source.replace("MACHINE = 'xenoamess-full-tower-eb9d2c1186'", "MACHINE = " + repr(text(machine_id)))
 need(not any(token in source for token in ("_A20_PRIOR", "_A19_PRIOR", "10480", "4753")),
   "current bootstrap has no historical business authority")
 compile(source, "<independent current saved bootstrap>", "exec")
 return source.encode("utf-8")
def emit_supervisor_v1(material: bytes, *, machine_id: str) -> bytes:
 source = material.decode("utf-8")
 tree = ast.parse(source)
 lines = source.splitlines(keepends=True)
 parts: list[str] = []
 for node in tree.body:
  if node.lineno < 315 or isinstance(node, ast.FunctionDef) and node.name in ("known_preload_phase", "main"):
   parts.append("".join(lines[node.lineno - 1:node.end_lineno]))
  elif 683 <= node.lineno <= 687:
   parts.append("".join(lines[node.lineno - 1:node.end_lineno]))
 need(sum(isinstance(node, ast.FunctionDef) and node.name == "main" for node in tree.body) == 1,
   "one retained canonical supervisor main")
 result = "\n".join(parts).replace("_validate_a15_attempt(args, config)",
        "verify_current_saved_supervisor_attempt_v1("
  "{'machine_id':MACHINE,'attempt_nonce':args.attempt_nonce,'task_nonce':args.task_nonce,"
  "'runtime_root':str(N)},config,runtime_root=N,expected_machine_id=MACHINE)")
 result += """
from tools.g2_saved_campaign import current_saved_basis_v1 as _screen_basis_v1
from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
    verify_current_saved_supervisor_attempt_v1,
)
def parse_screen_admission_v1(value: object, *, machine_id: str,
    repo: Path, git_head: str, at_utc: datetime) -> _screen_basis_v1.JsonObject:
    row = _screen_basis_v1.record(value, {"schema","machine_id","observed_at_utc","status","task_id",
        "sequence","repo","git_head","reviewer","provenance"})
    _screen_basis_v1.need(row["schema"] == "xar.C23-root-resource-screen-admission/v3"
        and row["machine_id"] == machine_id and row["status"] == "ACQUIRED"
        and row["reviewer"] == "/root", "actual current screen authority")
    observed = datetime.fromisoformat(_screen_basis_v1.utc(row["observed_at_utc"]).replace("Z","+00:00"))
    _screen_basis_v1.need(at_utc.tzinfo is not None and at_utc.utcoffset() == timedelta(0)
        and 0 <= (at_utc-observed).total_seconds() <= 600, "fresh screen admission")
    _screen_basis_v1.need(Path(_screen_basis_v1.text(row["repo"])).resolve() == repo.resolve() and row["git_head"] == git_head
        and re.fullmatch("[0-9a-f]{40}",git_head) is not None, "screen actual checkout")
    provenance = tuple(_screen_basis_v1.parse_ref(item) for item in _screen_basis_v1.rows(row["provenance"]))
    _screen_basis_v1.need(1 <= len(provenance) <= 8, "bounded current screen provenance")
    return {"schema":"xar.C23-root-resource-screen-admission/v3","machine_id":machine_id,
        "observed_at_utc":_screen_basis_v1.utc(row["observed_at_utc"]),"status":"ACQUIRED","task_id":_screen_basis_v1.text(row["task_id"]),
        "sequence":_screen_basis_v1.integer(row["sequence"],1),"repo":str(repo),"git_head":git_head,"reviewer":"/root",
        "provenance":[item.to_wire() for item in provenance]}
"""
 result += "\nMACHINE = " + repr(text(machine_id)) + "\n"
 result += """
if __name__ == "__main__":
 parser = argparse.ArgumentParser(description=__doc__)
 for key in ("clean-source-freeze","screen-admission","launch-config","steam-native-state"):
  parser.add_argument("--"+key,type=Path,required=True)
 parser.add_argument("--attempt",choices=("current_saved",),required=True)
 parser.add_argument("--attempt-nonce",required=True)
 parser.add_argument("--task-nonce",required=True)
 raise SystemExit(main(parser.parse_args()))
"""
 need(not any(token in result for token in ("_A20_PRIOR", "_A19_PRIOR", "_validate_a15_attempt",
    "validate_actual_A19", "10480", "4753")), "independent supervisor current authority")
 compile(result, "<independent current saved supervisor>", "exec")
 return result.encode("utf-8")
def emit_cold_resume_v1(material: bytes, *, machine_id: str) -> bytes:
 source = material.decode("utf-8")
 historical = "from root_checkpoint_bootstrap_c23 import validate_post_sem_driver,historical_saved_basis_view,migration_checkpoint"
 need(source.count(historical) == 1, "one retired current-business import seam")
 source = source.replace(historical,
  "from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import "
        "CurrentSavedColdInputsV1,WarmCurrentSavedFeederInputsV1,cold_inputs_v1,validate_current_saved_runtime_source_v1,validate_current_saved_old_generations_v1\n"
        "from tools.g2_saved_campaign.current_saved_basis_v1 import JsonObject,JsonValue")
 changed = replace_definition_v1(source.encode("utf-8"), "cold_inputs",
        "def cold_inputs(admission: object) -> tuple[JsonObject,JsonObject,JsonObject,JsonObject,JsonObject]:\n"
  "    return cold_inputs_v1(admission,runtime_root=Path(__file__).resolve().parent,expected_machine_id=MACHINE)\n")
 source = changed.decode("utf-8")
 start = source.index("            require(admission['new_Game']")
 end = source.index("            self.job, self.record_started", start)
 source = source[:start] + (
  "            validate_current_saved_old_generations_v1(admission,self.launch,"
  "runtime_root=env['N'],expected_machine_id=MACHINE)\n") + source[end:]
 start = source.index("            from root_checkpoint_bootstrap_c23 import validate_source28_frozen_business")
 end = source.index("            self.frozen_head", start)
 source = source[:start] + (
  "            validate_current_saved_runtime_source_v1(admission,freeze,"
  "runtime_root=env['N'],expected_machine_id=MACHINE)\n") + source[end:]
 source = source.replace("MACHINE = 'xenoamess-full-tower-eb9d2c1186'", "MACHINE = " + repr(text(machine_id)))
 need(not any(token in source for token in ("SAVE10480", "validate_saved_seed_a10",
    "historical_saved_basis_view", "validate_post_sem_driver", "migration_checkpoint")),
   "current cold queue no longer routes through saved10480 authorities")
 compile(source, "<independent current saved queue binding>", "exec")
 return source.encode("utf-8")
def emit_source32_factory_v1(material:bytes,sdk_mcp:bytes,*,mcp_ref:ExactRefV1)->bytes:
 source=material.decode("utf-8")
 nodes=[node for node in ast.parse(sdk_mcp).body if isinstance(node,ast.FunctionDef) and node.name=="load_driver"]
 need(len(nodes)==1 and sha256_v1(sdk_mcp)==mcp_ref.sha256 and len(sdk_mcp)==mcp_ref.bytes,"actual frozen SDK factory")
 args=nodes[0].args
 names=[arg.arg for arg in args.kwonlyargs]
 need(args.vararg is None and args.kwarg is None and len(args.args)==1
  and args.args[0].arg=="factory" and all(arg.annotation is not None for arg in args.args+args.kwonlyargs)
  and names.count("route_window_clock_v1")==1,"finite typed actual factory signature")
 index=names.index("route_window_clock_v1")
 args.kwonlyargs.pop(index);args.kw_defaults.pop(index)
 call=",".join(arg.arg+"="+arg.arg for arg in args.kwonlyargs)
 wrapper="""
from xar_autoplayer.bridge.mcp_server import GameplayBridgeDriver,War31OneShotSurrenderGate
from xar_autoplayer.bridge.route_window_clock_v1 import RouteWindowClockConfigV1,validate_route_window_clock_v1,route_window_clock_json_v1
_source32_load_driver_v1=mcp_server.load_driver
"""
 wrapper+="if Path(_source32_load_driver_v1.__code__.co_filename).resolve()!=Path("+repr(mcp_ref.path)+").resolve(): raise ValueError('foreign current SDK factory')\n"
 wrapper+="def _current_source32_load_driver_v1("+ast.unparse(args)+") -> GameplayBridgeDriver:\n"
 wrapper+="    if factory!='native-headless' or type(route_contact_timeline_speed) is not int or route_contact_timeline_speed!=3 or allow_route_contact_high_speed_ab is not False: raise ValueError('scoped clock requires original global3/false')\n"
 wrapper+="    driver=_source32_load_driver_v1(factory,"+call+",route_window_clock_v1=RouteWindowClockConfigV1(4,True))\n"
 wrapper+="    cfg=validate_route_window_clock_v1(getattr(driver,\'route_window_clock_v1\',None))\n    speed:object=getattr(driver,\'route_contact_timeline_speed\',None)\n    if cfg.timeline_speed!=4 or cfg.research_high_speed_ab is not True or type(speed) is not int or speed!=3 or getattr(driver,\'allow_route_contact_high_speed_ab\',None) is not False: raise ValueError('actual driver scoped/global clock differs')\n    return driver\n"
 seam="mcp_server.create_server=create_with_observation"
 need(source.count(seam)==1,"owned factory installation seam")
 source=source.replace(seam,wrapper+"\nmcp_server.load_driver=_current_source32_load_driver_v1\n"+seam)
 seam="'hold_only_AB_request':hold_ab_adoption,"
 need(source.count(seam)==1,"actual Driver mode receipt seam")
 source=source.replace(seam,seam+"'route_window_clock_v1':route_window_clock_json_v1(validate_route_window_clock_v1(driver.route_window_clock_v1)),")
 compile(source,"<current source32 factory>","exec")
 return source.encode("utf-8")
def profile_companions_v1(profile: JsonObject) -> dict[str, bytes]:
 name = text(profile["profile_name"])
 root = text(profile["recording_root"]).replace("\\", "/")
 bitrate = integer(profile["bitrate_kbps"], 1)
 basic = ("[General]\nName=" + name + "\n[Output]\nMode=Simple\nFilenameFormatting=managed\n"
  "[SimpleOutput]\nRecFilePath=" + root + "\nRecFormat=mkv\nRecQuality=Stream\nStreamEncoder=nvenc\n"
  "VBitrate=" + str(bitrate) + "\nNVENCPreset2=p5\n[Video]\nBaseCX=2560\nBaseCY=1440\n"
  "OutputCX=2560\nOutputCY=1440\nFPSType=0\nFPSCommon=30\nColorFormat=NV12\nColorSpace=709\n"
  "ColorRange=Partial\n[Audio]\nSampleRate=48000\nChannelSetup=Stereo\nDesktopDevice1=disabled\n"
  "DesktopDevice2=disabled\nAuxDevice1=disabled\nAuxDevice2=disabled\nAuxDevice3=disabled\n")
 scene = {"name":name,"current_scene":name,"current_program_scene":name,"scene_order":[{"name":name}],
    "groups":[],"transitions":[],"sources":[{"name":name,"id":"scene","versioned_id":"scene","settings":{"items":[]}}]}
 config = text(profile["config_root"])
 return {ntpath.join(config,"basic","profiles",name,"basic.ini"):basic.encode("utf-8"),
   ntpath.join(config,"basic","scenes",name+".json"):
    json.dumps(scene,ensure_ascii=False,indent=2).encode("utf-8")}
def compose_v1(plan: ColdPlanV1, *, plan_ref: ExactRefV1,
     metadata_overlay: dict[str, bytes] | None = None) -> ColdComposeV1:
 """Rebuild every current byte from exact small inputs without filesystem mutation."""
 from tools.g2_saved_campaign.current_saved_campaign_feeder_v1 import (
  emit_current_saved_feeder_launcher_v1, transform_current_saved_feeder_v1,
 )
 from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
  build_current_saved_prelaunch_v1,
 )
 p = parse_plan_v1(plan.to_wire())
 overlay = {} if metadata_overlay is None else dict(metadata_overlay)
 def load(reference: ExactRefV1, limit: int = MAX_FILE) -> bytes:
  need(reference.bytes <= limit <= MAX_FILE, "small bounded RAM input")
  if reference.path not in overlay:
   return read_ref_v1(reference, limit)
  raw = overlay[reference.path]
  need(type(raw) is bytes and ref_for_bytes_v1(reference.path, raw) == reference,
    "exact RAM overlay reference")
  return raw
 need(parse_plan_v1(parse_json(load(plan_ref))).to_wire() == p.to_wire(), "exact complete plan source")
 basis = parse_current_saved_basis_v1(parse_json(load(p.basis_ref,65536)), expected_machine_id=p.machine_id)
 material = record(parse_json(load(p.material_quote_ref)))
 need(material.get("schema") == "xar.Source31-A20-complete-cold-quote/v1"
   and material.get("machine_id") == p.machine_id, "source-bound static A20 material quote")
 original_rows = [record(item) for item in rows(material["files"])]
 need(len(original_rows) == 145, "complete original static material inventory")
 old_profile_ref = next(parse_ref({key:item[key] for key in ("path","bytes","sha256")})
  for item in original_rows if ntpath.basename(text(item["path"])) == "ROOT-OBS-PROFILE-C23.json")
 old_profile = json_object(parse_json(load(old_profile_ref)))
 old_nonce = nonce_v1(old_profile["A15_display_nonce"])
 need(old_nonce not in (p.display_nonce,p.attempt_nonce,p.task_nonce), "fresh display namespace")
 old_companions = profile_companions_v1(old_profile)
 output: dict[str,bytes] = {}
 originals: dict[str,ExactRefV1] = {}
 external_spec: str | None = None
 for row in original_rows:
  reference = parse_ref({key:row[key] for key in ("path","bytes","sha256")})
  path = reference.path
  in_runtime = ntpath.commonpath((path,p.material_runtime_root)).casefold() == p.material_runtime_root.casefold()
  relative = ntpath.relpath(path,p.material_runtime_root).replace("\\","/") if in_runtime else None
  if path in old_companions:
   raw = old_companions[path]
   need(ref_for_bytes_v1(path,raw) == reference, "mechanically reconstructed immutable OBS profile recipe")
  elif relative == "NEXT-SEQUENCE-P37.json":
   raw = load(parse_ref(row["source"]))
  else:
   raw = load(reference)
  if relative is None and ntpath.basename(path) == "SPEC.json":
   target = p.supervisor_spec_path
   external_spec = target
  else:
   target = relocate_text_v1(path,p,old_nonce)
  need(target not in output, "unique source projection")
  output[target] = raw
  originals[target] = reference
 if external_spec is None: raise ValueError("one real supervisor SPEC")
 for target, raw in list(output.items()):
  if target.endswith(".py"):
   output[target] = relocate_text_v1(raw.decode("utf-8"),p,old_nonce).encode("utf-8")
 def get(name: str) -> bytes:
  return output[child_v1(p.runtime_root,name)]
 def put(name: str, raw: bytes) -> None:
  output[child_v1(p.runtime_root,name)] = raw
 for item in p.source_rows:
  put(item.relative_path,load(item.source_ref))
 put("root_checkpoint_bootstrap_c23.py",emit_bootstrap_v1(get("root_checkpoint_bootstrap_c23.py"),machine_id=p.machine_id))
 put("root_native30_supervisor_c23.py",emit_supervisor_v1(get("root_native30_supervisor_c23.py"),machine_id=p.machine_id))
 cold = emit_cold_resume_v1(get("root_p37c23_cold_resume.py"),machine_id=p.machine_id).decode("utf-8")
 cold += (
        "\ndef load_current_saved_feeder_inputs_v1() -> WarmCurrentSavedFeederInputsV1:\n"
  "    from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import load_current_saved_warm_inputs_v1\n"
  "    return load_current_saved_warm_inputs_v1(runtime_root=Path(__file__).resolve().parent,expected_machine_id=MACHINE)\n")
 put("root_p37c23_cold_resume.py",cold.encode("utf-8"))
 name = "root_p37c23_same_game_loop_feeder100.py"
 raw = get(name)
 put(name,transform_current_saved_feeder_v1(raw,basis,source_sha256=sha256_v1(raw)))
 put("launch_current_saved_feeder_v1.py",emit_current_saved_feeder_launcher_v1())
 for name in ("tools/__init__.py","tools/g2_saved_campaign/__init__.py"):
  put(name,b'"""Frozen current saved runtime package."""\n')
 material_policy = record(parse_json(get("ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json")))
 inherited = {ntpath.relpath(text(rows(row)[0]),p.material_runtime_root).replace("\\","/")
              for row in rows(material_policy["entry_source_pins"])}
 required = inherited | {row.relative_path for row in p.source_rows} | {
     "tools/__init__.py","tools/g2_saved_campaign/__init__.py",
     "launch_current_saved_feeder_v1.py","root_p37c23_same_game_loop_feeder100.py"}
 need(len(inherited) == 47 and set(p.closure_entry_paths) == required,
      "mechanical original source closure plus explicit current dependencies")
 shared = {"tools":"tools/__init__.py","tools.g2_saved_campaign":"tools/g2_saved_campaign/__init__.py",
           **{row.relative_path[:-3].replace("/","."):row.relative_path for row in p.source_rows}}
 guard = """
def verify_current_saved_shared_sources_v1(root: Path) -> None:
    def obj(value: object) -> dict[str,object]:
        if not isinstance(value,dict): raise ValueError("source object")
        out: dict[str,object] = {}
        for key,item in value.items():
            if not isinstance(key,str): raise ValueError("source key")
            out[key] = item
        return out
    frozen: object = json.loads((root / "ROOT-FINAL-SDK-FREEZE-P37C23-A15.json").read_bytes())
    policy = obj(checked(obj(frozen)["canonical_preload_policy"]))
    entries = policy["entry_source_pins"]
    if not isinstance(entries,list): raise ValueError("source pin array")
    pins: dict[str,str] = {}
    for row in entries:
        if not isinstance(row,list) or len(row)!=2: raise ValueError("source pin row")
        path_value: object = row[0]; hash_value: object = row[1]
        if not isinstance(path_value,str) or not isinstance(hash_value,str): raise ValueError("source pin text")
        pins[str(Path(path_value).resolve())] = hash_value
    for name,relative in CURRENT_SHARED_IMPORTS.items():
        path = (root / relative).resolve(strict=True)
        raw = path.read_bytes()
        require(len(raw) <= 1048576 and pins.get(str(path)) == hashlib.sha256(raw).hexdigest(),
            "current shared source exact origin/pin")
        module = sys.modules.get(name)
        if module is not None:
            filename = module.__file__
            require(isinstance(filename,str) and Path(filename).resolve(strict=True) == path,
                "foreign current shared module cache")
"""
 put("root_c23_canonical_outer.py",get("root_c23_canonical_outer.py") +
     ("\nCURRENT_SHARED_IMPORTS = " + repr(shared) + "\n" + guard).encode("utf-8"))
 for name in ("root_native30_supervisor_c23.py","root_checkpoint_bootstrap_c23.py",
              "root_p37c23_cold_resume.py","launch_current_saved_feeder_v1.py"):
  raw = get(name)
  seam = b"from pathlib import Path"
  need(seam in raw,"actual current consumer import seam")
  raw = raw.replace(seam,seam+b"\nfrom root_c23_canonical_outer import verify_current_saved_shared_sources_v1"
      b"\nverify_current_saved_shared_sources_v1(Path(__file__).resolve().parent)",1)
  put(name,raw)
 closure = record(parse_json(load(basis.refs.closure)))
 game_exit = record(parse_json(load(parse_ref(record(closure["sources"])["ROOT-ACTUAL-GAME-EXIT-C23.json"]))))
 need(game_exit.get("machine_id") == p.machine_id,"actual previous Game machine")
 display = "presentation-c23/start_new_game_display.py"
 display_spec = literal_assignment_v1(get(display),"SPEC")
 display_spec["previous_Game_tuple"] = [integer(game_exit["pid"],1,(1<<32)-1),
     str(integer(game_exit["creation_filetime"],1,(1<<64)-1))]
 put(display,assignment_v1(get(display),"SPEC",display_spec))
 put("ROOT-CURRENT-SAVED-INPUTS01.json",encode_v1({
  "schema":"xar.current-saved-cold-inputs/v1","machine_id":p.machine_id,
  "basis_ref":p.basis_ref.to_wire(),"validation_ref":p.validation_ref.to_wire()}))
 documents: dict[str,JsonObject] = {}
 for path, raw in output.items():
  if path.endswith(".json") and ntpath.basename(path) != "STORAGE-ADMISSION.json":
   documents[path] = json_object(rewrite_json_v1(parse_json(raw),p,old_nonce,{}))
 def doc(name: str) -> JsonObject:
  return documents[child_v1(p.runtime_root,name)]
 previous = doc("ROOT-C23-COLD-PRELAUNCH.json")
 pre = build_current_saved_prelaunch_v1(basis,basis_ref=p.basis_ref,validation_ref=p.validation_ref,
  environment_sha256=text(previous["environment_sha256"]),pipe_name=text(previous["pipe_name"]))
 documents[child_v1(p.runtime_root,"ROOT-C23-COLD-PRELAUNCH.json")] = pre
 storage_raw = load(p.full_storage_ref)
 storage = record(parse_json(storage_raw))
 output[child_v1(p.runtime_root,"STORAGE-ADMISSION.json")] = storage_raw
 documents[child_v1(p.runtime_root,"NEXT-SEQUENCE-P37.json")] = {
        "next_sequence":basis.next_sequence,"at_utc":p.observed_at_utc}
 freeze = doc("ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")
 base=json_object(parse_json(load(p.sdk_base_ref)))
 anchor=record(parse_json(load(p.sdk_anchor_ref,65536)))
 need(base.get("schema")=="root.ck3.final-sdk-freeze/v1" and base.get("status")=="FINAL_SOURCE_FROZEN"
  and base.get("machine_id")==anchor.get("machine_id")==p.machine_id
  and base.get("sdk_generation")=="P37C23" and anchor.get("schema")==f"xar.source{p.business_source_generation}.canonical-git-anchor/v1"
  and anchor.get("commit")==base.get("business_source_commit")
  and parse_ref(base.get(f"source{p.business_source_generation}_canonical_anchor"))==p.sdk_anchor_ref,
  "current SDK base/anchor exact lineage")
 kept={key:value for key,value in freeze.items() if key.startswith(("native","dll")) or
   key in ("canonical_preload_policy","runtime_source_repo","runtime_owner_generation","git_head_role")}
 freeze.clear();freeze.update(base);freeze.update(kept)
 freeze.update(base_freeze=p.sdk_base_ref.to_wire(),sdk_base_ref=p.sdk_base_ref.to_wire(),
  sdk_anchor_ref=p.sdk_anchor_ref.to_wire(),business_source_generation=p.business_source_generation)
 sdkroot=absolute_v1(freeze["source_root"])
 doc("ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json")["sdk_source_root"]=sdkroot
 doc("ROOT-NATIVE30-SDK-BINDING-C23-A15.json")["source_root"]=sdkroot
 if p.business_source_generation==32:
  candidates=[record(row) for row in rows(base["files"]) if record(row).get("relative")=="xar_autoplayer/bridge/mcp_server.py"]
  need(len(candidates)==1,"one frozen current SDK MCP factory")
  row=candidates[0]
  mcpref=ExactRefV1(child_v1(sdkroot,text(row["relative"])),integer(row["bytes"],1,MAX_FILE),digest(row["sha256"]))
  put("root_p37c23_mcp_entry.py",emit_source32_factory_v1(get("root_p37c23_mcp_entry.py"),load(mcpref),mcp_ref=mcpref))
 for state_name in STATE_SOURCES_V1:
  put(state_name,bind_current_saved_state_source_v1(state_name,get(state_name),basis))
 freeze.update(planned_saved_opening_date_raw=basis.frame.date_raw,
  continuation_basis={"basis_ref":p.basis_ref.to_wire(),"completed_cycles":basis.completed_cycles,
       "date_raw":basis.frame.date_raw,"ordinary_cycle_credit":0,"game_day_credit":0},
  attempt_id="current_saved",actual_native_loaded=False,runtime_admitted=False)
 config = doc("ROOT-LAUNCH-CONFIG-C23-A15.json")
 config["native32_current_sdk_status"]="unavailable_current_sdk_binding_pending" if p.business_source_generation==32 else "historical_source31_binding"
 config["status"] = "ADMITTED" if (storage.get("status") == "ADMITTED"
     and storage.get("review_at_utc") == p.review_at_utc) else "PREPARE_ONLY_NOT_LAUNCH_ADMITTED"
 config.update(observed_at_utc=p.observed_at_utc,review_at_utc=p.review_at_utc,
  basis_ref=p.basis_ref.to_wire(),validation_ref=p.validation_ref.to_wire(),
  business_source_generation=p.business_source_generation,sdk_base_ref=p.sdk_base_ref.to_wire(),sdk_anchor_ref=p.sdk_anchor_ref.to_wire(),
  storage_admission=child_v1(p.runtime_root,"STORAGE-ADMISSION.json"),
  storage_admission_sha256=p.full_storage_ref.sha256,full_storage_view=p.full_storage_ref.to_wire(),
        actual_checkpoint_response=basis.refs.save_response.to_wire(),
        cold_prelaunch=ref_for_bytes_v1(child_v1(p.runtime_root,"ROOT-C23-COLD-PRELAUNCH.json"),encode_v1(pre)).to_wire(),
  steam_native_state=p.steam_native_state_ref.to_wire(),
  cold_attempt={"machine_id":p.machine_id,"attempt_nonce":p.attempt_nonce,"task_nonce":p.task_nonce,
      "runtime_root":p.runtime_root,"basis_ref":p.basis_ref.to_wire(),
      "validation_ref":p.validation_ref.to_wire()})
 doc("ROOT-CLEAN-SOURCE-FROZEN-C23-A15.json")["business_source_commit"]=freeze["business_source_commit"]
 ready = doc("ROOT-PROMO-KEEPER-SOURCE-READY-C23-A15.json")
 ready.update(source_review_at_utc=p.review_at_utc)
 spec = documents[external_spec]
 spec.update(nonce=p.task_nonce,task_name="XARG2ManagedOwner-"+p.task_nonce,
    root=ntpath.dirname(external_spec),cwd=p.runtime_root)
 args = rows(spec["stage_args"])
 replacements: dict[str,JsonValue] = {"--attempt":"current_saved","--attempt-nonce":p.attempt_nonce,
  "--task-nonce":p.task_nonce,"--steam-native-state":p.steam_native_state_ref.path,
  "--screen-admission":p.screen_admission_path}
 for index,arg_item in enumerate(args[:-1]):
  if type(arg_item) is str and arg_item in replacements:
   args[index+1] = replacements[arg_item]
 spec["stage_args"] = [json_value(item) for item in args]
 profile = doc("ROOT-OBS-PROFILE-C23.json")
 profile.update(prepared_at_utc=p.observed_at_utc,storage_review_at_utc=p.review_at_utc)
 profile["storage"] = {"admission_path":child_v1(p.runtime_root,"STORAGE-ADMISSION.json"),
  "admission_sha256":p.full_storage_ref.sha256,
        **{key:json_value(storage[key]) for key in ("approved_output_roots","disk_reserve_bytes")}}
 for path,raw in profile_companions_v1(profile).items():
  output[path] = raw
 policy = doc("ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json")
 need(set(p.canonical_entry_paths) == CANONICAL_NAMES, "same actual max8 canonical entries")
 for iteration in range(8):
  pins = {path:ref_for_bytes_v1(path,raw) for path,raw in output.items()}
  for path,value in list(documents.items()):
    # The fresh basis packet cites the original closed epoch, not copied material.
    documents[path] = pre if path==child_v1(p.runtime_root,"ROOT-C23-COLD-PRELAUNCH.json") else json_object(rewrite_json_v1(value,p,old_nonce,pins))
  policy = doc("ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json")
  policy["canonical_entry_source_pins"] = [[child_v1(p.runtime_root,name),pins[child_v1(p.runtime_root,name)].sha256]
            for name in p.canonical_entry_paths]
  policy["entry_source_pins"] = [[child_v1(p.runtime_root,name),pins[child_v1(p.runtime_root,name)].sha256]
          for name in p.closure_entry_paths]
  imported: list[JsonValue] = []
  for row_value in rows(policy["runtime_import_source_pins"]):
   ref = parse_ref(row_value)
   target = ref.path
   if ntpath.basename(target) == "launch_a10_saved10480_feeder01.py":
    target = child_v1(p.runtime_root,"launch_current_saved_feeder_v1.py")
   imported.append(pins[target].to_wire() if target in pins else ref.to_wire())
  policy["runtime_import_source_pins"] = imported
  config = doc("ROOT-LAUNCH-CONFIG-C23-A15.json")
  config["SDK_freeze_sha256"] = pins[child_v1(p.runtime_root,"ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")].sha256
  doc("ROOT-NATIVE30-SDK-BINDING-C23-A15.json")["sdk_freeze_sha256"]=config["SDK_freeze_sha256"]
  spec = documents[external_spec]
  spec["stage_sha256"] = pins[child_v1(p.runtime_root,"root_native30_supervisor_c23.py")].sha256
  changes = {path:encode_v1(value) for path,value in documents.items()}
  if all(output.get(path) == raw for path,raw in changes.items()):
   break
  output.update(changes)
 else:
  raise ValueError("source/metadata graph did not stabilize within max8 passes")
 runtime = {ntpath.relpath(path,p.runtime_root).replace("\\","/"):raw for path,raw in output.items()
  if ntpath.commonpath((path,p.runtime_root)).casefold() == p.runtime_root.casefold()}
 for name,raw in runtime.items():
  if name.endswith(".py"):
   compile(raw,name,"exec")
 result_rows: list[OutputRowV1] = []
 for path,raw in sorted(output.items()):
  pin = ref_for_bytes_v1(path,raw)
  old = originals.get(path)
  unchanged = old is not None and (old.bytes,old.sha256) == (pin.bytes,pin.sha256)
  relative = ntpath.relpath(path,p.runtime_root).replace("\\","/") if path in {
   child_v1(p.runtime_root,name) for name in runtime} else None
  result_rows.append(OutputRowV1(path,relative,pin.bytes,pin.sha256,
   "hardlink" if unchanged else "create-only",old if unchanged else None))
 allocated = sum(allocation_v1(row.bytes) for row in result_rows if row.mode == "create-only")
 quote = ColdQuoteV1(p.machine_id,p.observed_at_utc,plan_ref,p.basis_ref,p.validation_ref,p.producer_ref,
  p.runtime_root,tuple(result_rows),p.canonical_entry_paths,p.closure_entry_paths,p.import_roots,
  8,sum(row.bytes for row in result_rows),allocated,allocated+max(len(raw) for raw in output.values())+131072)
 return ColdComposeV1(output,parse_quote_v1(quote.to_wire()))


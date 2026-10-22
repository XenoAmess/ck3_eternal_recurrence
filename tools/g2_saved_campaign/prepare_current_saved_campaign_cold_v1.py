"""Independent current saved checkpoint cold composition; no runtime side effects."""
from __future__ import annotations
import ast
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import ntpath
from pathlib import Path
from types import ModuleType
from tools.g2_saved_campaign.file_stat_identity_v1 import FileStatIdentityV1
import re
from typing import Callable, Literal
from tools.g2_saved_campaign.current_saved_basis_v1 import (
 BasisReaderV1, CurrentSavedBasisV1, ExactRefV1, JsonObject, JsonValue, digest, integer,
 decode_current_saved_basis_v1, exact_read,
 json_object, json_value, need, parse_current_saved_basis_v1, parse_json,
  parse_ref, record, rows, text, utc, MAX_FILE as MAX_FILE,
)
from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
 CampaignScoreJunctionV1, LocalBasisReaderV1, build_campaign_score_junction_v1,
 campaign_score_directory_identity_v1, derive_current_saved_state_paths_v1,
 parse_campaign_score_junction_v1, validate_campaign_score_junction_source_v1,
 validate_campaign_score_junction_physical_v1, validate_current_saved_cold_inputs_v1,
)
from tools.g2_saved_campaign.current_saved_continuity_v1 import (
 ContinuityReaderV1, LocalContinuityReaderV1, read_continuity_view_v1,
 validate_closed_continuity_frontier_v1,
)
PLAN_SCHEMA = "xar.current-saved-cold-plan/v4"
QUOTE_SCHEMA = "xar.current-saved-cold-quote/v5"
MAX_CURRENT_SAVED_CLOSURE_V1 = 67
MAX_GRAPH = 8 * MAX_FILE
CANONICAL_NAMES = frozenset((
 "launch_sdk_p37c23_owner.py", "native32_mcp_extension_v1.py",
 "observer_journal_runtime_v1.py", "root_c23_canonical_outer.py",
 "root_checkpoint_bootstrap_c23.py", "root_native30_supervisor_c23.py",
 "root_p37c23_mcp_entry.py", "root_p37c23_sdk_queue.py",
))
GENERIC_SOURCE_PATHS = frozenset(('tools/ck3_live_run_id.py', 'tools/g2_saved_campaign/background_foreground_contract_v1.py', 'tools/g2_saved_campaign/current_saved_background_display_v1.py', 'tools/g2_saved_campaign/current_saved_basis_v1.py', 'tools/g2_saved_campaign/current_saved_campaign_feeder_v1.py', 'tools/g2_saved_campaign/first_full_checkpoint_v1.py', 'tools/g2_saved_campaign/current_saved_campaign_preflight_v1.py', 'tools/g2_saved_campaign/current_saved_continuity_v1.py', 'tools/g2_saved_campaign/current_saved_campaign_replay_v1.py', 'tools/g2_saved_campaign/prepare_native32_current_sdk_binding_v1.py', 'tools/g2_saved_campaign/file_stat_identity_v1.py', 'tools/g2_saved_campaign/managed_desktop1_placement.py', 'tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py', 'tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py', 'tools/g2_saved_campaign/root_saved_campaign_preflight.py'))
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
def executable_import_roots_v1(value: object) -> tuple[str, ...]:
 result = paths_v1(value, allow_root=True)
 need(all(root.casefold() != "tools" for root in result),
      "tools must remain a qualified package, not a bare executable import root")
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
class FirstFullControlTimingAdmissionV1:
 machine_id: str
 control_sequence: int
 def to_wire(self) -> JsonObject:
  machine = text(self.machine_id)
  need(machine == machine.strip(), "canonical control timing machine ID")
  sequence = integer(self.control_sequence, 3, (1 << 53) - 1)
  return {"schema": "xar.ck3.queue-control-timing-admission/v1",
          "enabled": True, "machine_id": machine,
          "control_sequence": sequence, "cycle_budget": 30}

def build_current_saved_first_full_control_timing_v1(
 *, machine_id: object, next_sequence: object,
) -> FirstFullControlTimingAdmissionV1:
 """Validate external inputs for one existing first-FULL probe, without I/O.

 The caller binds the machine and the unchanged SEM/CAP opening sequence.
 This is measurement authority only; it grants no Game call or batch credit.
 """
 machine = text(machine_id)
 need(machine == machine.strip(), "canonical control timing machine ID")
 sequence = integer(next_sequence, 1, (1 << 53) - 3)
 return FirstFullControlTimingAdmissionV1(machine, sequence + 2)

@dataclass(frozen=True, slots=True)
class Native32CurrentSdkOverrideV1:
 reader_ref: ExactRefV1
 extension_ref: ExactRefV1
 binding_ref: ExactRefV1
 def to_wire(self) -> JsonObject:
  return {"reader_ref":self.reader_ref.to_wire(),
          "extension_ref":self.extension_ref.to_wire(),"binding_ref":self.binding_ref.to_wire()}

def parse_native32_current_sdk_override_v1(value:object) -> Native32CurrentSdkOverrideV1|None:
 if value is None:return None
 row=record(value,{"reader_ref","extension_ref","binding_ref"})
 result=Native32CurrentSdkOverrideV1(parse_ref(row["reader_ref"]),
  parse_ref(row["extension_ref"]),parse_ref(row["binding_ref"]))
 refs=(result.reader_ref,result.extension_ref,result.binding_ref)
 need(len({absolute_v1(item.path).casefold() for item in refs})==3,
      "three distinct exact Native32 current SDK source inputs")
 for reference,limit in zip(refs,(131072,16384,65536),strict=True):
  need(1<=reference.bytes<=limit,"bounded explicit Native32 override source")
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
 native32_current_sdk_override: Native32CurrentSdkOverrideV1|None
 artifact_cap_bytes: int
 renderer_override_ref: ExactRefV1 | None
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
   "sdk_anchor_ref":self.sdk_anchor_ref.to_wire(),
   "native32_current_sdk_override":None if self.native32_current_sdk_override is None else self.native32_current_sdk_override.to_wire(), "artifact_cap_bytes": self.artifact_cap_bytes, "renderer_override_ref": None if self.renderer_override_ref is None else self.renderer_override_ref.to_wire()}
PLAN_FIELDS = {"schema", "machine_id", "observed_at_utc", "review_at_utc", "runtime_root",
 "material_runtime_root", "material_quote_ref", "basis_ref", "validation_ref", "producer_ref",
 "source_rows", "canonical_entry_paths", "closure_entry_paths", "import_roots", "full_storage_ref",
 "steam_native_state_ref", "screen_admission_path", "supervisor_spec_path", "display_nonce",
 "attempt_nonce", "task_nonce", "business_source_generation", "sdk_base_ref", "sdk_anchor_ref", "native32_current_sdk_override", "artifact_cap_bytes", "renderer_override_ref"}
def artifact_cap_bytes_v1(value: object) -> int:
 return integer(value, 128 * 1024**2, 16 * 1024**3)

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
  executable_import_roots_v1(row["import_roots"]), parse_ref(row["full_storage_ref"]),
  parse_ref(row["steam_native_state_ref"]), absolute_v1(row["screen_admission_path"]),
  absolute_v1(row["supervisor_spec_path"]), nonce_v1(row["display_nonce"]),
  nonce_v1(row["attempt_nonce"]), nonce_v1(row["task_nonce"]),
  business_generation_v1(row["business_source_generation"]),parse_ref(row["sdk_base_ref"]),parse_ref(row["sdk_anchor_ref"]),
  parse_native32_current_sdk_override_v1(row["native32_current_sdk_override"]),
  artifact_cap_bytes_v1(row["artifact_cap_bytes"]),
  parse_current_saved_renderer_override_v1(row["renderer_override_ref"]))
 need(result.runtime_root.casefold() != result.material_runtime_root.casefold()
   and len({result.display_nonce, result.attempt_nonce, result.task_nonce}) == 3,
   "fresh independent software/recording/Task namespace")
 need(datetime.fromisoformat(result.observed_at_utc.replace("Z", "+00:00")) <
   datetime.fromisoformat(result.review_at_utc.replace("Z", "+00:00")), "review follows observation")
 need(len(result.canonical_entry_paths) == 8 and set(result.canonical_entry_paths) == CANONICAL_NAMES
   and set(result.canonical_entry_paths) <= set(result.closure_entry_paths)
   and len(result.closure_entry_paths) <= MAX_CURRENT_SAVED_CLOSURE_V1, "canonical max8 and complete bounded closure")
 need(len(result.source_rows) == len(GENERIC_SOURCE_PATHS)
   and {item.relative_path for item in result.source_rows} == GENERIC_SOURCE_PATHS
   and len({item.relative_path for item in result.source_rows}) == len(result.source_rows)
         and {item.relative_path for item in result.source_rows} <= set(result.closure_entry_paths),
   "all generic shared dependencies explicitly belong to complete closure")
 need(any(item.source_ref == result.producer_ref for item in result.source_rows),
   "actual producer source participates in closure")
 need(result.basis_ref.bytes <= 65536 and result.validation_ref.bytes <= 65536,
   "small qualified current basis")
 from tools.g2_saved_campaign.prepare_native32_current_sdk_binding_v1 import BINDING_NAME
 need((BINDING_NAME in result.closure_entry_paths)==(result.native32_current_sdk_override is not None),
      "Native32 current binding has one explicit active closure slot")
 need(result.native32_current_sdk_override is None or result.business_source_generation==32,
      "Native32 current SDK override requires explicit Source32")
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
 campaign_score_junction: CampaignScoreJunctionV1
 canonical_entry_paths: tuple[str, ...]
 closure_entry_paths: tuple[str, ...]
 import_roots: tuple[str, ...]
 canonical_entry_limit: Literal[8]
 logical_bytes: int
 allocation_upper: int
 prepare_peak_upper: int
 native32_current_sdk_override: Native32CurrentSdkOverrideV1|None
 artifact_cap_bytes: int
 renderer_override_ref: ExactRefV1 | None
 def to_wire(self) -> JsonObject:
  return {"schema": QUOTE_SCHEMA, "machine_id": self.machine_id, "observed_at_utc": self.observed_at_utc,
   "plan_ref": self.plan_ref.to_wire(), "basis_ref": self.basis_ref.to_wire(),
   "validation_ref": self.validation_ref.to_wire(), "producer_ref": self.producer_ref.to_wire(),
   "runtime_root": self.runtime_root, "files": [item.to_wire() for item in self.files],
   "campaign_score_junction":self.campaign_score_junction.to_wire(),
   "canonical_entry_paths": list(self.canonical_entry_paths),
   "closure_entry_paths": list(self.closure_entry_paths), "import_roots": list(self.import_roots),
   "canonical_entry_limit": self.canonical_entry_limit, "logical_bytes": self.logical_bytes,
   "allocation_upper": self.allocation_upper, "prepare_peak_upper": self.prepare_peak_upper,
   "native32_current_sdk_override":None if self.native32_current_sdk_override is None else self.native32_current_sdk_override.to_wire(), "artifact_cap_bytes": self.artifact_cap_bytes, "renderer_override_ref": None if self.renderer_override_ref is None else self.renderer_override_ref.to_wire(),
   "ordinary_cycle_credit": 0, "game_day_credit": 0, "original_actions_replayed": False}
QUOTE_FIELDS = {"schema", "machine_id", "observed_at_utc", "plan_ref", "basis_ref", "validation_ref",
 "producer_ref", "runtime_root", "files", "canonical_entry_paths", "closure_entry_paths",
 "import_roots", "canonical_entry_limit", "logical_bytes", "allocation_upper", "prepare_peak_upper",
 "ordinary_cycle_credit", "game_day_credit", "original_actions_replayed", "campaign_score_junction", "native32_current_sdk_override", "artifact_cap_bytes", "renderer_override_ref"}
def validate_native32_current_sdk_output_rows_v1(quote:ColdQuoteV1) -> None:
 from tools.g2_saved_campaign.prepare_native32_current_sdk_binding_v1 import (
  READER_NAME, EXTENSION_NAME, BINDING_NAME,
 )
 override=quote.native32_current_sdk_override
 need((BINDING_NAME in quote.closure_entry_paths)==(override is not None),
      "quoted Native32 current binding closure matches explicit override")
 if override is None:return
 for name,reference in ((READER_NAME,override.reader_ref),(EXTENSION_NAME,override.extension_ref),
                        (BINDING_NAME,override.binding_ref)):
  found=[row for row in quote.files if row.relative_path==name]
  need(len(found)==1 and (found[0].bytes,found[0].sha256)==(reference.bytes,reference.sha256),
       "exact three Native32 override output pins")

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
  parse_campaign_score_junction_v1(row["campaign_score_junction"]),
  paths_v1(row["canonical_entry_paths"]), paths_v1(row["closure_entry_paths"]),
  executable_import_roots_v1(row["import_roots"]), 8,
  integer(row["logical_bytes"], 1, MAX_GRAPH), integer(row["allocation_upper"], 1, MAX_GRAPH),
  integer(row["prepare_peak_upper"], 1, MAX_GRAPH),
  parse_native32_current_sdk_override_v1(row["native32_current_sdk_override"]),
  artifact_cap_bytes_v1(row["artifact_cap_bytes"]),
  parse_current_saved_renderer_override_v1(row["renderer_override_ref"]))
 need(result.campaign_score_junction.path==child_v1(root,"campaign-score"),"exact directory projection")
 score=ntpath.normcase(ntpath.normpath(result.campaign_score_junction.path))
 need(all(not (ntpath.normcase(ntpath.normpath(item.path))==score or
   ntpath.normcase(ntpath.normpath(item.path)).startswith(score+"\\")) for item in result.files),
  "score junction is an independent directory projection; never copied files")
 paths = [item.path.casefold() for item in result.files]
 relative = {item.relative_path for item in result.files if item.relative_path is not None}
 need(1 <= len(result.files) <= 192 and len(paths) == len(set(paths))
   and set(result.canonical_entry_paths) == CANONICAL_NAMES
   and set(result.canonical_entry_paths) <= set(result.closure_entry_paths) <= relative
   and len(result.closure_entry_paths) <= MAX_CURRENT_SAVED_CLOSURE_V1, "unique outputs cover actual complete closure/max8")
 validate_native32_current_sdk_output_rows_v1(result)
 validate_current_saved_renderer_output_rows_v1(result)
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

def bind_current_saved_complete_closure_limit_v1(raw: bytes) -> bytes:
 """Bind only the inherited complete-source bound to the common plan limit."""
 source = raw.decode("utf-8")
 functions = [node for node in ast.parse(source).body
              if isinstance(node, ast.FunctionDef) and node.name == "_check_c23_external_imports"]
 need(len(functions) == 1, "one inherited complete source guard")
 function = functions[0]
 expected = ast.parse("0<len(pins)<=64", mode="eval").body
 matches = [node for node in ast.walk(function) if isinstance(node, ast.Compare)
            and ast.dump(node) == ast.dump(expected)]
 need(len(matches) == 1, "one exact inherited complete source limit")
 compare = matches[0]
 need(compare.end_lineno == compare.lineno and compare.end_col_offset is not None,
      "single-line inherited complete source comparison")
 lines = source.splitlines(keepends=True)
 line = lines[compare.lineno - 1]
 lines[compare.lineno - 1] = (line[:compare.col_offset] +
     f"0<len(pins)<={MAX_CURRENT_SAVED_CLOSURE_V1}" + line[compare.end_col_offset:])
 result = "".join(lines).encode("utf-8")
 compile(result, "<current saved complete closure>", "exec")
 return result

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
_LAUNCH_FOREGROUND_BLOCK_V1 = '''        _, desktop_after = placement.desktop_inventory()
        foreground_after = user.GetForegroundWindow()
        write(N / "ROOT-LAUNCH-USER-DESKTOP-OBSERVED-C23.json", {"foreground_before": foreground,
            "foreground_after": foreground_after, "desktop_before": desktop_before, "desktop_after": desktop_after,
            "game_pid": generation.pid, "game_creation_filetime": generation.creation_filetime,
            "gameplay_input": False, "desktop_switch_requested": False})
        if foreground_after != foreground or desktop_after != desktop_before:
            raise RuntimeError("user foreground/desktop changed during launch; stop without restoring user windows")'''

_LAUNCH_FOREGROUND_REPLACEMENT_V1 = '''        _, desktop_after = placement.desktop_inventory()
        user.GetForegroundWindow.argtypes = []
        foreground_after = user.GetForegroundWindow()
        user.GetWindowThreadProcessId.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        user.GetWindowThreadProcessId.restype = ctypes.c_ulong
        foreground_pid = ctypes.c_ulong()
        foreground_thread = user.GetWindowThreadProcessId(ctypes.c_void_p(foreground_after), ctypes.byref(foreground_pid))
        foreground_after_pid = foreground_pid.value if type(foreground_thread) is int and 0 < foreground_thread < 2**32 and foreground_pid.value else None
        foreground_final = user.GetForegroundWindow()
        if foreground_final != foreground_after:
            foreground_after, foreground_after_pid = foreground_final, None
        _, desktop_final = placement.desktop_inventory()
        if desktop_final != desktop_after:
            desktop_after, foreground_after_pid = desktop_final, None
        foreground_observation = _launch_foreground_contract_v1.classify_current_saved_launch_foreground_v1({
            "foreground_before": 0 if foreground is None else foreground,
            "foreground_after": 0 if foreground_after is None else foreground_after, "foreground_after_pid": foreground_after_pid,
            "desktop_before": desktop_before, "desktop_after": desktop_after,
            "game_pid": generation.pid, "owned_auxiliary_pids": []})
        write(N / "ROOT-LAUNCH-USER-DESKTOP-OBSERVED-C23.json", {
            **foreground_observation.to_wire(), "game_creation_filetime": generation.creation_filetime,
            "gameplay_input": False, "desktop_switch_requested": False})
        if not foreground_observation.permitted:
            raise RuntimeError("launch foreground authority rejected: " + foreground_observation.classification
                + "; stop without restoring user windows")'''

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
 result = "\n".join(parts)
 early = "    _validate_a15_attempt(args, config)\n"
 need(result.count(early)==1,"one original early retired attempt validator")
 result = result.replace(early,"",1)
 guarded = """    if (Path(environment.__file__).resolve() != creator_source / "xar_autoplayer/environment.py"
            or Path(runtime.__file__).resolve() != creator_source / "xar_autoplayer/runtime.py"):
        raise ValueError("public prepare/launch imported a different project source")
    abort = threading.Event()"""
 authority = "    verify_current_saved_supervisor_attempt_v1(" + (
  "{'machine_id':MACHINE,'attempt_nonce':args.attempt_nonce,'task_nonce':args.task_nonce,"
  "'runtime_root':str(N)},config,runtime_root=N,expected_machine_id=MACHINE)\n")
 need(result.count(guarded)==1,"one original guarded SDK import before keeper admission")
 result = result.replace(guarded,guarded.replace("    abort = threading.Event()",
  authority+"    abort = threading.Event()"),1)
 need(result.count(_LAUNCH_FOREGROUND_BLOCK_V1) == 1, "one original launch foreground authority block")
 result = result.replace(_LAUNCH_FOREGROUND_BLOCK_V1, _LAUNCH_FOREGROUND_REPLACEMENT_V1, 1)
 placement_path = 'repo / "tools/g2_saved_campaign/managed_desktop1_placement.py"'
 need(result.count(placement_path) == 1, "one original host placement consumer")
 result = result.replace(placement_path, 'N / "tools/g2_saved_campaign/managed_desktop1_placement.py"', 1)
 result += """
from tools.g2_saved_campaign import current_saved_basis_v1 as _screen_basis_v1
from tools.g2_saved_campaign import background_foreground_contract_v1 as _launch_foreground_contract_v1
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
 return emit_current_saved_request_guards_v1(source.encode("utf-8"),kind="cold")

def emit_current_saved_request_guards_v1(material:bytes,*,kind:Literal["cold","queue"])->bytes:
 """Bind the shared halt-first request gate into the original cold and dispatch paths."""
 source=material.decode("utf-8")
 tree=ast.parse(source)
 need("_current_saved_gate_v1" not in source,"request gate is installed exactly once")
 lines=source.splitlines(keepends=True)
 imports=[node for node in tree.body if isinstance(node,ast.ImportFrom) and node.module=="__future__"]
 offset=max((node.end_lineno or node.lineno for node in imports),default=0)
 edits:list[tuple[int,int,str]]=[]
 shared="from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as _current_saved_gate_v1\n"
 if kind=="cold":
  factories=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="make_normal_checkpoint_cold_queue_v1"]
  need(len(factories)==1,"one actual cold queue factory")
  returns=[node for node in factories[0].body if isinstance(node,ast.Return) and isinstance(node.value,ast.Name) and node.value.id=="NormalCheckpointColdQueue"]
  need(len(returns)==1 and returns[0].end_lineno is not None,"one actual cold queue class return")
  cold_return=returns[0]
  if cold_return.end_lineno is None: raise ValueError("cold factory return extent")
  body=" "*cold_return.col_offset+"return _current_saved_gate_v1.install_current_saved_queue_guard_v1(NormalCheckpointColdQueue,runtime_root=env['N'])\n"
  edits.append((cold_return.lineno-1,cold_return.end_lineno,body))
 else:
  need(kind=="queue","known request guard source kind")
  loops=[node for node in tree.body if isinstance(node,ast.AsyncFunctionDef) and node.name=="run_request_loop"]
  need(len(loops)==1,"one actual request dispatch")
  assignments=[node for node in ast.walk(loops[0]) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=="command" for target in node.targets) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=="request" and node.value.func.attr=="get"]
  need(len(assignments)==1,"one dispatch command seam")
  dispatch_assignment=assignments[0]
  indent=" "*dispatch_assignment.col_offset
  guard=indent+'if "tool" in request or request.get("command")=="full_loop":\n'+indent+'    _current_saved_gate_v1.validate_current_saved_dispatch_v1(queue,request,runtime_root=N)\n'
  edits.append((dispatch_assignment.lineno-1,dispatch_assignment.lineno-1,guard))
  waits=[node for node in ast.walk(tree) if isinstance(node,ast.Expr) and isinstance(node.value,ast.Await) and isinstance(node.value.value,ast.Call) and isinstance(node.value.value.func,ast.Name) and node.value.value.func.id=="wait_for_sdk_pair_pin"]
  need(len(waits)==1 and waits[0].end_lineno is not None,"one actual pinned SDK pair before tools")
  wait_expression=waits[0]
  if wait_expression.end_lineno is None: raise ValueError("SDK wait extent")
  hook=" "*wait_expression.col_offset+'_current_saved_gate_v1.bind_current_saved_request_epoch_v1(queue,runtime_root=N,expected_machine_id=_current_saved_gate_v1.current_execution_machine_id_v1())\n'
  edits.append((wait_expression.end_lineno,wait_expression.end_lineno,hook))
 edits.append((offset,offset,shared))
 for start,end,text in sorted(edits,reverse=True):
  lines[start:end]=[text]
 result="".join(lines)
 compile(result,"<current saved shared request guards>","exec")
 return result.encode("utf-8")

def emit_current_saved_map_admission_guard_v1(material:bytes)->bytes:
 """Keep the inherited camera/FULL guard and bind its strict shared map parser."""
 source=material.decode("utf-8");tree=ast.parse(source)
 need("_current_saved_map_v1" not in source,"map parser installed once")
 classes=[node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=="CleanRobertMainMenuQueue"]
 need(len(classes)==1,"actual inherited campaign map queue")
 methods=[node for node in classes[0].body if isinstance(node,ast.FunctionDef) and node.name=="require_camera_pixel_admission"]
 need(len(methods)==1,"actual inherited campaign map guard")
 reads=[node for node in methods[0].body if isinstance(node,ast.Assign)
  and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=="receipt"
  and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=="read"
  and len(node.value.args)==2 and isinstance(node.value.args[0],ast.BinOp)
  and isinstance(node.value.args[0].left,ast.Name) and node.value.args[0].left.id=="N"
  and isinstance(node.value.args[0].op,ast.Div) and isinstance(node.value.args[0].right,ast.Constant)
  and node.value.args[0].right.value=="ROOT-CAMPAIGN-MAP-ADMITTED-C23.json"
  and isinstance(node.value.args[1],ast.Constant) and node.value.args[1].value==16384]
 need(len(reads)==1 and reads[0].end_lineno is not None,"actual bounded campaign map receipt seam")
 seam=reads[0]
 if seam.end_lineno is None: raise ValueError("campaign map read extent")
 indent=" "*seam.col_offset
 hook=(indent+"_current_saved_map_review_v1=_current_saved_map_v1.parse_campaign_map_admission_v1(receipt,expected_machine_id=_current_saved_map_machine_v1())\n"
  +indent+"_current_saved_map_review_v1.require_native_launch_v1(self.launch)\n")
 imports=[node for node in tree.body if isinstance(node,ast.ImportFrom) and node.module=="__future__"]
 offset=max((node.end_lineno or node.lineno for node in imports),default=0)
 shared=("from tools.g2_saved_campaign import root_current_saved_campaign_cold_owner_v1 as _current_saved_map_v1\n"
  "from tools.g2_saved_campaign.current_saved_campaign_preflight_v1 import current_execution_machine_id_v1 as _current_saved_map_machine_v1\n")
 lines=source.splitlines(keepends=True)
 for start,body in sorted(((seam.end_lineno,hook),(offset,shared)),reverse=True): lines[start:start]=[body]
 result="".join(lines);compile(result,"<current saved shared map guard>","exec")
 return result.encode("utf-8")

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
def emit_current_saved_sdk_launcher_v1(material:bytes,*,artifact_cap_bytes:int)->bytes:
 cap=artifact_cap_bytes_v1(artifact_cap_bytes)
 tree=ast.parse(material)
 values=[node.elts[index+1] for node in ast.walk(tree) if isinstance(node,(ast.List,ast.Tuple))
   for index,item in enumerate(node.elts[:-1])
   if isinstance(item,ast.Constant) and item.value=="--artifact-cap-bytes"]
 need(len(values)==1,"one actual launcher artifact budget argument")
 value=values[0]
 need(isinstance(value,ast.Constant) and value.value=="2147483648"
   and value.end_lineno is not None and value.end_col_offset is not None,
   "exact original launcher artifact budget source")
 if value.end_lineno is None or value.end_col_offset is None:raise ValueError("budget extent")
 lines=material.splitlines(keepends=True)
 start=sum(map(len,lines[:value.lineno-1]))+value.col_offset
 end=sum(map(len,lines[:value.end_lineno-1]))+value.end_col_offset
 source=(material[:start]+repr(str(cap)).encode("ascii")+material[end:]).decode("utf-8")
 seam="from pathlib import Path"
 need(source.count(seam)==1,"one launcher import seam")
 source=source.replace(seam,seam+"\nfrom tools.g2_saved_campaign.current_saved_basis_v1 import JsonObject,JsonValue,integer,need,record,text",1)
 replacement="""
def verify_prepared_inputs() -> JsonObject:
    from tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1 import (
        load_current_saved_inputs_v1,validate_current_saved_prepared_sdk_closure_v1)
    pins=record(read(N/'ROOT-P37C23-OWNER-INPUT-PINS.json'))
    for name,expected in record(pins['sources']).items():
        need(sha(N/name)==text(expected),'exact current owner source changed: '+name)
    admission=record(read(N/'ROOT-P37C23-COLD-RESUME-ADMISSION.json'))
    inputs=load_current_saved_inputs_v1(runtime_root=N,expected_machine_id=text(MACHINE_ID))
    proof=validate_current_saved_prepared_sdk_closure_v1(admission['old_closed'],inputs=inputs)
    need(not (N/'EXIT-SDK-P37C23').exists() and not (N/'REQUEST-ADMISSION-CLOSED-C23').exists(),
        'current SDK admission already closed')
    need(not (N/'p37-queue').exists(),'current Queue is create-only')
    next_sequence=integer(record(read(N/'NEXT-SEQUENCE-P37.json'))['next_sequence'],1)
    need(next_sequence==integer(admission['next_sequence'],1)==inputs.basis.next_sequence,
        'qualified current sequence required')
    return proof
"""
 return replace_definition_v1(source.encode("utf-8"),"verify_prepared_inputs",replacement)

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
def prepare_campaign_score_junction_v1(binding:CampaignScoreJunctionV1,basis:CurrentSavedBasisV1,*,approved_root:Path)->JsonObject:
 """Explicit Root-only mutation after file preparation; compose never calls this."""
 import os
 import subprocess
 from datetime import timezone
 item=parse_campaign_score_junction_v1(binding.to_wire())
 root=Path(absolute_v1(str(approved_root)))
 need(root.is_dir(),"approved runtime directory exists")
 for parent in (root,*root.parents):
  need(not getattr(parent.lstat(),"st_file_attributes",0)&0x400,"approved runtime parents have no reparse points")
 root=root.resolve(strict=True)
 path=Path(item.path);target=Path(item.exact_target)
 need(path==root/"campaign-score" and path.parent==root and not os.path.lexists(path),"exact create-only approved child")
 need(not any(c in str(path)+str(target) for c in '&|<>^%!"\r\n'),"literal cmd junction arguments")
 reader=LocalBasisReaderV1()
 validate_campaign_score_junction_source_v1(item,basis,runtime_root=root,reader=reader)
 expected=(item.target_file_id,item.target_device)
 need(campaign_score_directory_identity_v1(target)==expected,"qualified target directory identity")
 anchor=record(parse_json(read_ref_v1(item.anchor_ref,16384)))
 outcome=subprocess.run(["cmd.exe","/d","/c","mklink","/J",str(path),str(target)],
  check=False,capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
 need(outcome.returncode==0,"junction creation failed: "+outcome.stderr.decode("utf-8",errors="replace")[:2048])
 validate_campaign_score_junction_physical_v1(item,runtime_root=root,reader=reader)
 need(campaign_score_directory_identity_v1(target)==expected,"target directory identity stayed fixed")
 for parent in (root,*root.parents):
  need(not getattr(parent.lstat(),"st_file_attributes",0)&0x400,"approved runtime parents stayed ordinary")
 return {"schema":"xar.current-saved-campaign-score-junction-prepare/v1",
  "machine_id":text(anchor["machine_id"]),"observed_at_utc":datetime.now(timezone.utc).isoformat(),
  "status":"CREATED_AND_VERIFIED","campaign_score_junction":item.to_wire(),
  "copied_files":0,"ordinary_cycle_credit":0,"game_day_credit":0,"original_actions_replayed":False}

def compose_v1(plan: ColdPlanV1, *, plan_ref: ExactRefV1,
     metadata_overlay: dict[str, bytes] | None = None) -> ColdComposeV1:
 """Rebuild every current byte from exact small inputs without filesystem mutation."""
 from tools.g2_saved_campaign.current_saved_campaign_feeder_v1 import (
  emit_current_saved_feeder_launcher_v1, transform_current_saved_feeder_v1,
 )
 from tools.g2_saved_campaign.first_full_checkpoint_v1 import render_first_full_checkpoint_queue_v1
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
 score_anchor=Path(derive_current_saved_state_paths_v1(basis).state_root).parent/"campaign-score"/"CAMPAIGN-ANCHOR.json"
 before_anchor=score_anchor.stat()
 with score_anchor.open("rb") as stream:anchor_raw=stream.read(16385)
 after_anchor=score_anchor.stat()
 need(len(anchor_raw)<=16384 and (before_anchor.st_dev,before_anchor.st_ino,before_anchor.st_size,before_anchor.st_mtime_ns)==
  (after_anchor.st_dev,after_anchor.st_ino,after_anchor.st_size,after_anchor.st_mtime_ns),"stable bounded original score anchor")
 score_binding=build_campaign_score_junction_v1(basis,material,runtime_root=Path(p.runtime_root),
  anchor_ref=ref_for_bytes_v1(str(score_anchor),anchor_raw),reader=LocalBasisReaderV1())
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
 from tools.g2_saved_campaign.current_saved_campaign_replay_v1 import (
  HISTORICAL_REPLAY_DATA_RELATIVE_PATH_V1, HISTORICAL_REPLAY_DATA_BYTES_V1,
  HISTORICAL_REPLAY_DATA_SHA256_V1,
 )
 archive_source=ExactRefV1(str(Path(p.producer_ref.path).parent/"test_data"/
  "current_saved_sem11373_postcheck_v1.json"),HISTORICAL_REPLAY_DATA_BYTES_V1,
  HISTORICAL_REPLAY_DATA_SHA256_V1)
 archive_raw=load(archive_source,135168)
 put(HISTORICAL_REPLAY_DATA_RELATIVE_PATH_V1,archive_raw)
 put("root_checkpoint_bootstrap_c23.py",emit_bootstrap_v1(get("root_checkpoint_bootstrap_c23.py"),machine_id=p.machine_id))
 put("root_native30_supervisor_c23.py",emit_supervisor_v1(get("root_native30_supervisor_c23.py"),machine_id=p.machine_id))
 put("root_native30_supervisor_c23.py",assignment_v1(get("root_native30_supervisor_c23.py"),
  "PLACEMENT_SHA",sha256_v1(get("tools/g2_saved_campaign/managed_desktop1_placement.py"))))
 put("launch_sdk_p37c23_owner.py",emit_current_saved_sdk_launcher_v1(get("launch_sdk_p37c23_owner.py"),artifact_cap_bytes=p.artifact_cap_bytes))
 put("root_p37c23_sdk_queue.py",render_first_full_checkpoint_queue_v1(emit_current_saved_map_admission_guard_v1(emit_current_saved_request_guards_v1(get("root_p37c23_sdk_queue.py"),kind="queue"))))
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
 from tools.g2_saved_campaign import prepare_native32_current_sdk_binding_v1 as native32
 required = inherited | {row.relative_path for row in p.source_rows} | {
     "tools/__init__.py","tools/g2_saved_campaign/__init__.py",
     "launch_current_saved_feeder_v1.py","root_p37c23_same_game_loop_feeder100.py"}
 if p.native32_current_sdk_override is not None:required.add(native32.BINDING_NAME)
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
 put("root_c23_canonical_outer.py",bind_current_saved_complete_closure_limit_v1(
      get("root_c23_canonical_outer.py")) +
     ("\nCURRENT_SHARED_IMPORTS = " + repr(shared) + "\n" + guard).encode("utf-8"))
 for name in ("root_native30_supervisor_c23.py","root_checkpoint_bootstrap_c23.py",
              "root_p37c23_cold_resume.py","launch_current_saved_feeder_v1.py","launch_sdk_p37c23_owner.py"):
  raw = get(name)
  seam = b"from pathlib import Path"
  need(seam in raw,"actual current consumer import seam")
  raw = raw.replace(seam,seam+b"\nfrom root_c23_canonical_outer import verify_current_saved_shared_sources_v1"
      b"\nverify_current_saved_shared_sources_v1(Path(__file__).resolve().parent)",1)
  put(name,raw)
 class ComposeReaderV1:
  def read(self,reference:ExactRefV1,limit:int)->bytes:return load(reference,limit)
  def read_response(self,reference:ExactRefV1,limit:int)->bytes:
   return LocalBasisReaderV1().read_response(reference,limit)
  def read_sdk_source(self,reference:ExactRefV1,limit:int)->bytes:
   return LocalBasisReaderV1().read_sdk_source(reference,limit)
  def stat(self,path:str)->FileStatIdentityV1:return LocalBasisReaderV1().stat(path)
 current_inputs=validate_current_saved_cold_inputs_v1(basis,basis_ref=p.basis_ref,
  validation_ref=p.validation_ref,reader=ComposeReaderV1())
 old_game=current_inputs.closed_epoch.old_game
 display = "presentation-c23/start_new_game_display.py"
 display_spec = literal_assignment_v1(get(display),"SPEC")
 display_spec["previous_Game_tuple"] = [old_game.pid,old_game.creation_filetime]
 put(display,assignment_v1(get(display),"SPEC",display_spec))
 from tools.g2_saved_campaign.current_saved_background_display_v1 import render_current_saved_background_display_v1
 background = render_current_saved_background_display_v1(actor=get(display),
  obs_desktop=get("presentation-c23/obs_owned_desktop.py"),
  capture_worker=get("presentation-c23/ck3_obs_capture_png_retry_c23.py"),
  placement_sha256=sha256_v1(get("tools/g2_saved_campaign/managed_desktop1_placement.py")))
 put(display,background.actor)
 put("presentation-c23/obs_owned_desktop.py",background.obs_desktop)
 put("presentation-c23/ck3_obs_capture_png_retry_c23.py",background.capture_worker)
 put("ROOT-CURRENT-SAVED-INPUTS01.json",encode_v1({
  "schema":"xar.current-saved-cold-inputs/v1","machine_id":p.machine_id,
  "basis_ref":p.basis_ref.to_wire(),"validation_ref":p.validation_ref.to_wire()}))
 documents: dict[str,JsonObject] = {}
 for path, raw in output.items():
  if (path.endswith(".json") and ntpath.basename(path) != "STORAGE-ADMISSION.json"
      and path != child_v1(p.runtime_root,HISTORICAL_REPLAY_DATA_RELATIVE_PATH_V1)):
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
 if p.native32_current_sdk_override is not None:
  historical_binding_ref=originals[child_v1(p.runtime_root,native32.HISTORICAL_BINDING_NAME)]
  apply_native32_current_sdk_override_v1(p,output=output,documents=documents,
   historical_binding_ref=historical_binding_ref,load=load)
 apply_current_saved_renderer_override_v1(p, output=output, load=load)
 freeze.update(planned_saved_opening_date_raw=basis.frame.date_raw,
  continuation_basis={"basis_ref":p.basis_ref.to_wire(),"completed_cycles":basis.completed_cycles,
       "date_raw":basis.frame.date_raw,"ordinary_cycle_credit":0,"game_day_credit":0},
  attempt_id="current_saved",actual_native_loaded=False,runtime_admitted=False)
 config = doc("ROOT-LAUNCH-CONFIG-C23-A15.json")
 config["native32_current_sdk_status"]=("CURRENT_SDK_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"
  if p.native32_current_sdk_override is not None else
  "unavailable_current_sdk_binding_pending" if p.business_source_generation==32 else "historical_source31_binding")
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
      "validation_ref":p.validation_ref.to_wire(),"campaign_score_junction":score_binding.to_wire()})
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
 policy["current_saved_data_source_pins"]=[ref_for_bytes_v1(
  child_v1(p.runtime_root,HISTORICAL_REPLAY_DATA_RELATIVE_PATH_V1),archive_raw).to_wire()]
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
  p.runtime_root,tuple(result_rows),score_binding,p.canonical_entry_paths,p.closure_entry_paths,p.import_roots,
  8,sum(row.bytes for row in result_rows),allocated,allocated+max(len(raw) for raw in output.values())+131072,p.native32_current_sdk_override,p.artifact_cap_bytes,p.renderer_override_ref)
 return ColdComposeV1(output,parse_quote_v1(quote.to_wire()))

@dataclass(frozen=True, slots=True)
class SupervisorImportChainV1:
 placement_source: str
 keeper_source: str
 creator_sources: tuple[str, ...]
 custody_source: str

def probe_current_saved_supervisor_import_chain_v1(
 supervisor: ModuleType, canonical: object, *, supervisor_source: bytes, runtime_root: Path,
) -> SupervisorImportChainV1:
 """Run the original pre-ADMITTED import span before any bootstrap SDK import."""
 import sys
 root=runtime_root.resolve(strict=True)
 need(Path(text(supervisor.__file__)).resolve()==root/"root_native30_supervisor_c23.py",
      "actual supervisor import-chain origin")
 main=[node for node in ast.parse(supervisor_source).body
       if isinstance(node,ast.FunctionDef) and node.name=="main"]
 need(len(main)==1,"one actual supervisor main import chain")
 body=main[0].body
 def assignment(name:str)->ast.Assign:
  found=[node for node in body if isinstance(node,ast.Assign)
         and any(isinstance(target,ast.Name) and target.id==name for target in node.targets)
         and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name)
         and node.value.func.id=="load_file"]
  need(len(found)==1,"one original import assignment: "+name)
  return found[0]
 placement=assignment("placement");keeper=assignment("keeper_module")
 branches=[node for node in body if isinstance(node,ast.If)
           and ast.unparse(node.test)=="canonical is None"
           and any(isinstance(item,ast.Call) and isinstance(item.func,ast.Attribute)
                   and isinstance(item.func.value,ast.Name) and item.func.value.id=="canonical"
                   and item.func.attr=="tools" for item in ast.walk(node))]
 need(len(branches)==1,"one original canonical import-path branch")
 custody=[node for node in body if isinstance(node,ast.ImportFrom)
          and node.module=="g2_saved_campaign.sdk_process_custody"]
 need(len(custody)==1,"one original custody import")
 start=body.index(placement)
 need(start+1==body.index(keeper) and body.index(branches[0])+1==body.index(custody[0]),
      "retained supervisor import order")
 # Only the three import statements are executed; intervening live bus/OS checks
 # remain in the full main prefix and are not claimed by this offline probe.
 projection:list[ast.stmt]=[placement,keeper,branches[0],custody[0]]
 need(canonical is not None,"real canonical binding is required")
 scope:dict[str,object]=dict(vars(supervisor));scope.update(canonical=canonical,N=root)
 exec(compile(ast.Module(body=projection,type_ignores=[]),str(root/"root_native30_supervisor_c23.py"),"exec"),scope)
 def origin(name:str)->str:
  module=sys.modules.get(name)
  need(isinstance(module,ModuleType),"actual imported module: "+name)
  if not isinstance(module,ModuleType): raise ValueError("missing imported module")
  return str(Path(text(module.__file__)).resolve(strict=True))
 tools=root/"creator-tools/g2_saved_campaign"
 creators=tuple(origin("g2_saved_campaign."+name) for name in
   ("canonical_native_provider_chain_v1","sdk_process_custody"))
 need(all(Path(path).parent==tools for path in creators),"standalone creators retain their exact frozen namespace")
 need(Path(origin("root_owned_generation"))==root/"tools/g2_saved_campaign/managed_desktop1_placement.py"
      and Path(origin("root_retained_screen_keeper"))==root/"root_screen_bus_lease_c23.py",
      "original placement and keeper imports retain frozen origins")
 return SupervisorImportChainV1(origin("root_owned_generation"),origin("root_retained_screen_keeper"),
                                creators,origin("g2_saved_campaign.sdk_process_custody"))

CURRENT_SAVED_RENDERER_PIN_V1 = (21038, "fb5eaa7217da027770272784da0d725cc605953f2547c62636bc6188e1589feb")
CURRENT_SAVED_RENDERER_PATHS_V1 = (
 "decision_display_contract_v1.py",
 "presentation-c23/g2_saved_campaign/decision_display_contract_v1.py",
)

def parse_current_saved_renderer_override_v1(value: object) -> ExactRefV1 | None:
 if value is None:return None
 reference = parse_ref(value)
 absolute_v1(reference.path)
 need((reference.bytes, reference.sha256) == CURRENT_SAVED_RENDERER_PIN_V1,
      "exact currently qualified shared renderer source")
 return reference

def apply_current_saved_renderer_override_v1(
 plan: ColdPlanV1, *, output: dict[str, bytes],
 load: Callable[[ExactRefV1, int], bytes],
) -> None:
 """Replace one qualified formatter in its two already active source slots."""
 reference = plan.renderer_override_ref
 if reference is None:return
 need(parse_current_saved_renderer_override_v1(reference.to_wire()) == reference,
      "explicit qualified renderer override")
 current = load(reference, 65536)
 need((len(current), sha256_v1(current)) == CURRENT_SAVED_RENDERER_PIN_V1,
      "qualified renderer payload bytes")
 paths = tuple(child_v1(plan.runtime_root, name) for name in CURRENT_SAVED_RENDERER_PATHS_V1)
 old = output[paths[0]]
 need(old == output[paths[1]], "both inherited rich formatter bodies must agree")
 outer_path = child_v1(plan.runtime_root, "root_c23_canonical_outer.py")
 outer = output[outer_path]
 from tools.g2_saved_campaign.prepare_native32_current_sdk_binding_v1 import _outer_external_table_v1
 node, before = _outer_external_table_v1(outer)
 name = "decision_display_contract_v1"
 need(before.get(name) == (len(old), sha256_v1(old)), "inherited renderer external pin matches its body")
 table = node.value
 if not isinstance(table, ast.Dict):raise ValueError("literal external source table")
 matches = [value for key, value in zip(table.keys, table.values, strict=True)
            if isinstance(key, ast.Constant) and key.value == name]
 need(len(matches) == 1, "one renderer external tuple")
 value = matches[0]
 if not isinstance(value, ast.Tuple) or value.end_lineno is None or value.end_col_offset is None:
  raise ValueError("bounded literal renderer external tuple")
 lines = outer.splitlines(keepends=True)
 start = sum(map(len, lines[:value.lineno-1])) + value.col_offset
 end = sum(map(len, lines[:value.end_lineno-1])) + value.end_col_offset
 changed = outer[:start] + repr(CURRENT_SAVED_RENDERER_PIN_V1).encode("ascii") + outer[end:]
 compile(changed, "<current saved renderer external pin>", "exec")
 _, after = _outer_external_table_v1(changed)
 need(set(after) == set(before) and after[name] == CURRENT_SAVED_RENDERER_PIN_V1
      and all(after[key] == pin for key, pin in before.items() if key != name),
      "renderer changes only its one external pin")
 output.update({paths[0]: current, paths[1]: current, outer_path: changed})


def validate_current_saved_renderer_output_rows_v1(quote: ColdQuoteV1) -> None:
 reference = quote.renderer_override_ref
 if reference is None:return
 for name in CURRENT_SAVED_RENDERER_PATHS_V1:
  found = [row for row in quote.files if row.relative_path == name]
  need(len(found) == 1 and (found[0].bytes, found[0].sha256) == (reference.bytes, reference.sha256),
       "both qualified renderer outputs must match the explicit ref")

def apply_native32_current_sdk_override_v1(
 plan:ColdPlanV1,*,output:dict[str,bytes],documents:dict[str,JsonObject],
 historical_binding_ref:ExactRefV1,load:Callable[[ExactRefV1,int],bytes],
) -> None:
 """Install only the exact reviewed source-bound triplet; never grant runtime credit."""
 override=plan.native32_current_sdk_override
 if override is None:return
 need(plan.business_source_generation==32,"current Native32 override requires Source32")
 from tools.g2_saved_campaign import prepare_native32_current_sdk_binding_v1 as native32
 def get(name:str)->bytes:return output[child_v1(plan.runtime_root,name)]
 raw_reader=load(override.reader_ref,131072)
 raw_extension=load(override.extension_ref,16384)
 raw_binding=load(override.binding_ref,65536)
 binding=record(parse_json(raw_binding),{"schema","machine_id","status",
  "historical_binding_ref","current_sdk_base_ref","current_sdk_anchor_ref"})
 need(binding["schema"]==native32.SCHEMA and text(binding["machine_id"])==plan.machine_id
  and binding["status"]=="CURRENT_SDK_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"
  and parse_ref(binding["current_sdk_base_ref"])==plan.sdk_base_ref
  and parse_ref(binding["current_sdk_anchor_ref"])==plan.sdk_anchor_ref
  and parse_ref(binding["historical_binding_ref"])==historical_binding_ref,
  "exact material historical binding and current Source32 authority")
 load(historical_binding_ref,65536)
 expected=native32.compose_native32_current_sdk_binding_v1(
  get(native32.READER_NAME),get(native32.EXTENSION_NAME),
  historical_binding_ref=historical_binding_ref,current_sdk_base_ref=plan.sdk_base_ref,
  current_sdk_anchor_ref=plan.sdk_anchor_ref,machine_id=plan.machine_id)
 need((raw_reader,raw_extension,raw_binding)==(
  expected.reader_bytes,expected.extension_bytes,expected.current_binding_bytes),
  "Native32 override must equal the deterministic reviewed source composition")
 consumers=native32.patch_native32_current_sdk_consumers_v1(
  get("root_p37c23_mcp_entry.py"),get("root_p37c23_sdk_queue.py"),
  get("root_c23_canonical_outer.py"),expected)
 native_path=child_v1(plan.runtime_root,"ROOT-NATIVE30-NATIVE-PIN-C23-A15.json")
 native=json_object(documents[native_path])
 need("native32_current_sdk_binding" not in native,"one explicit new Native32 source binding")
 additions={child_v1(plan.runtime_root,name):raw for name,raw in expected.files().items()}
 additions.update({
  child_v1(plan.runtime_root,"root_p37c23_mcp_entry.py"):consumers.entry_bytes,
  child_v1(plan.runtime_root,"root_p37c23_sdk_queue.py"):consumers.queue_bytes,
  child_v1(plan.runtime_root,"root_c23_canonical_outer.py"):consumers.outer_bytes})
 native["native32_current_sdk_binding"]=ref_for_bytes_v1(
  child_v1(plan.runtime_root,native32.BINDING_NAME),raw_binding).to_wire()
 output.update(additions)
 documents[native_path]=native

def probe_current_saved_continuity_v1(
 plan:ColdPlanV1,*,reader:BasisReaderV1,continuity_reader:ContinuityReaderV1,
) -> JsonObject:
 """Read the real canonical head, including exact-next committed events, without repair."""
 basis=decode_current_saved_basis_v1(exact_read(reader,plan.basis_ref,65536),
                                    expected_machine_id=plan.machine_id)
 current=read_continuity_view_v1(
  canonical_path=Path(plan.runtime_root).parent/"ROOT-CONTINUITY-WINDOW.json",
  anchor_ref=basis.refs.ledger,expected_machine_id=plan.machine_id,reader=continuity_reader)
 need(current.ready,"continuity metadata recovery required before Prepared")
 validate_closed_continuity_frontier_v1(basis.to_wire(),current)
 return current.to_wire()

def run_current_saved_startup_consumer_probe_v1(
 plan_ref:ExactRefV1,quote_ref:ExactRefV1,*,expected_machine_id:str,
) -> JsonObject:
 """Execute frozen, read-only original consumers before publishing Prepared.

 This function requires a fresh process importing this module from the quoted
 runtime. It does not call supervisor.main, receive_entry or a Native constructor.
 """
 import importlib
 import sys
 from types import FunctionType, ModuleType
 from datetime import timezone
 from tools.g2_saved_campaign import current_saved_campaign_preflight_v1 as gate
 plan=parse_plan_v1(parse_json(read_ref_v1(plan_ref)))
 quote=parse_quote_v1(parse_json(read_ref_v1(quote_ref)))
 need(plan.machine_id==expected_machine_id==gate.current_execution_machine_id_v1(),
      "consumer probe uses the actual execution machine")
 need(quote.plan_ref==plan_ref and quote.runtime_root==plan.runtime_root,
      "consumer probe exact Plan and Quote")
 root=Path(plan.runtime_root).resolve(strict=True)
 need(Path(__file__).resolve(strict=True)==root/"tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py",
      "consumer probe must run from the frozen runtime, not an ambient checkout")
 need(Path(sys.path[0]).resolve()==root,"fresh probe first import root is this runtime")
 for name,module in tuple(sys.modules.items()):
  if name=="tools" or name.startswith("tools.g2_saved_campaign") or name=="tools.ck3_live_run_id":
   filename:object=getattr(module,"__file__",None)
   need(isinstance(filename,str) and Path(filename).resolve().is_relative_to(root),
        "consumer probe rejects ambient shared module caches")
 output={row.relative_path:row for row in quote.files if row.relative_path is not None}
 def source(relative:str)->tuple[ExactRefV1,bytes]:
  row=output.get(relative)
  need(row is not None,"quoted consumer source: "+relative)
  if row is None: raise ValueError("missing consumer source")
  reference=ExactRefV1(row.path,row.bytes,row.sha256)
  return reference,read_ref_v1(reference)
 def module_at(name:str,relative:str)->tuple[ModuleType,ExactRefV1,bytes]:
  reference,payload=source(relative)
  cached=sys.modules.get(name)
  if cached is not None:
   need(isinstance(cached.__file__,str) and Path(cached.__file__).resolve()==Path(reference.path).resolve(),
        "actual consumer module origin")
   return cached,reference,payload
  module=ModuleType(name);module.__file__=reference.path
  sys.modules[name]=module
  try: exec(compile(payload,reference.path,"exec"),vars(module))
  except BaseException:
   del sys.modules[name]
   raise
  return module,reference,payload
 def function(module:ModuleType,name:str)->FunctionType:
  value:object=vars(module).get(name)
  if not isinstance(value,FunctionType): raise ValueError("actual consumer function: "+name)
  return value
 def ast_function(payload:bytes,qualname:str)->ast.AST:
  current:list[ast.AST]=list(ast.parse(payload).body)
  result:ast.AST|None=None
  for part in qualname.split("."):
   found=[node for node in current if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==part]
   need(len(found)==1,"one original consumer callable "+qualname)
   result=found[0]
   current=list(result.body) if isinstance(result,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)) else []
  if result is None: raise ValueError("empty consumer callable")
  return result
 calls:list[gate.CurrentSavedConsumerProbeCallV1]=[]
 def evidence(operation:str,reference:ExactRefV1,payload:bytes,qualname:str,
              observed:JsonObject,projection:list[ast.stmt]|None=None)->None:
  parent=ast_function(payload,qualname)
  projected=ast.Module(body=projection,type_ignores=[]) if projection is not None else None
  calls.append(gate.CurrentSavedConsumerProbeCallV1(operation,
   "original_function" if projected is None else "original_ast_projection",reference,qualname,
   sha256_v1(ast.dump(parent,include_attributes=False).encode()),
   None if projected is None else sha256_v1(ast.dump(projected,include_attributes=False).encode()),
   None if projected is None else ast.unparse(projected),1,observed))
 config_ref,config_raw=source("ROOT-LAUNCH-CONFIG-C23-A15.json")
 config=json_object(parse_json(config_raw))
 _,policy_raw=source("ROOT-C23-CANONICAL-PRELOAD-POLICY-A05.json")
 policy=json_object(parse_json(policy_raw))
 dependency_root=Path(text(policy["dependency_root"])).resolve(strict=True)
 import_paths:list[str]=[]
 for relative in plan.import_roots:
  path=(root/relative).resolve(strict=True)
  need(path.is_relative_to(root),"frozen deployment import root")
  if path!=root: import_paths.append(str(path))
 import_paths.append(str(dependency_root))
 for relative in ("win32","win32/lib"):
  path=dependency_root/relative
  if path.is_dir(): import_paths.append(str(path))
 sys.path[1:1]=import_paths
 dll_handles:list[object]=[]
 if hasattr(__import__("os"),"add_dll_directory"):
  import os
  for path in (dependency_root/"pywin32_system32",Path(sys.executable).parent/"Lib/site-packages/pywin32_system32"):
   if path.is_dir(): dll_handles.append(os.add_dll_directory(str(path)))
 spec_raw=read_ref_v1(next(ExactRefV1(row.path,row.bytes,row.sha256) for row in quote.files
                         if row.path==plan.supervisor_spec_path))
 spec=json_object(parse_json(spec_raw))
 bootstrap=Path(text(spec["bootstrap"]))
 need(bootstrap.parent.resolve()==root,"Task bootstrap is in this frozen runtime")
 task,task_ref,task_raw=module_at("_current_saved_probe_task_owner_v1",bootstrap.name)
 checked:object=function(task,"checked_spec")(Path(plan.supervisor_spec_path),sha256_v1(spec_raw))
 need(json_object(checked)==spec,"original Task spec validation preserves exact document")
 evidence("task_spec_validation",task_ref,task_raw,"checked_spec",
          {"spec_path":plan.supervisor_spec_path,"spec_sha256":sha256_v1(spec_raw),
           "task_nonce":plan.task_nonce,"stage":text(spec["stage"])})
 outer,outer_ref,outer_raw=module_at("root_c23_canonical_outer","root_c23_canonical_outer.py")
 canonical:object=function(outer,"prepare_supervisor")(root,enabled=True)
 need(canonical is not None,"actual canonical constructor returned a binding")
 evidence("canonical_outer_constructor",outer_ref,outer_raw,"OuterBindingV1.__init__",
          {"runtime_root":str(root),"canonical_entry_count":len(plan.canonical_entry_paths)})
 supervisor,super_ref,super_raw=module_at("_current_saved_probe_supervisor_v1","root_native30_supervisor_c23.py")
 probe_current_saved_supervisor_import_chain_v1(supervisor,canonical,
  supervisor_source=super_raw,runtime_root=root)
 boot,_,_=module_at("root_checkpoint_bootstrap_c23","root_checkpoint_bootstrap_c23.py")
 api_result:object=function(boot,"api")()
 need(isinstance(api_result,tuple) and len(api_result)==3,"original bootstrap API result")
 if not isinstance(api_result,tuple) or len(api_result)!=3: raise ValueError("bootstrap API")
 environment:object=api_result[0];runtime:object=api_result[2]
 need(isinstance(environment,ModuleType) and isinstance(runtime,ModuleType),"actual SDK modules")
 owner_module=importlib.import_module("tools.g2_saved_campaign.root_current_saved_campaign_cold_owner_v1")
 owner_ref,owner_raw=source("tools/g2_saved_campaign/root_current_saved_campaign_cold_owner_v1.py")
 args:JsonObject={"machine_id":expected_machine_id,"attempt_nonce":plan.attempt_nonce,
                  "task_nonce":plan.task_nonce,"runtime_root":str(root)}
 business:object=function(owner_module,"validate_current_saved_supervisor_business_v1")(
  args,config,runtime_root=root,expected_machine_id=expected_machine_id)
 business_row=json_object(business)
 evidence("supervisor_prepared_business",owner_ref,owner_raw,
          "validate_current_saved_supervisor_business_v1",
          {"config_ref":config_ref.to_wire(),"basis_ref":plan.basis_ref.to_wire(),
           "validation_ref":plan.validation_ref.to_wire(),"business_schema":text(business_row["schema"])})
 main=ast_function(super_raw,"main")
 need(isinstance(main,ast.FunctionDef),"actual supervisor main definition")
 if not isinstance(main,ast.FunctionDef): raise ValueError("supervisor main")
 tries=[node for node in main.body if isinstance(node,ast.Try) and any(
  isinstance(item,ast.Expr) and isinstance(item.value,ast.Call) and
  isinstance(item.value.func,ast.Attribute) and item.value.func.attr=="start" and
  isinstance(item.value.func.value,ast.Name) and item.value.func.value.id=="keeper" for item in node.body)]
 need(len(tries)==1,"one original pre-CreateProcess consumer block")
 nodes=tries[0].body
 imports=[node for node in nodes if isinstance(node,ast.ImportFrom) and node.module=="root_checkpoint_bootstrap_c23"
          and any(item.name=="verify_cold_profile" for item in node.names)]
 make=[node for node in nodes if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call)
       and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=="make_spec"
       and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=="environment"]
 verify=[node for node in nodes if isinstance(node,ast.Assign) and isinstance(node.value,ast.Call)
         and isinstance(node.value.func,ast.Name) and node.value.func.id=="verify_cold_profile"]
 need(len(imports)==len(make)==len(verify)==1 and nodes.index(verify[0])==nodes.index(make[0])+1,
      "unique adjacent original make_spec and verify_cold_profile statements")
 projection:list[ast.stmt]=[imports[0],make[0],verify[0]]
 scope:dict[str,object]=dict(vars(supervisor))
 scope.update(environment=environment,runtime=runtime,config=config,game_dir=Path(text(config["game_dir"])).resolve())
 exec(compile(ast.Module(body=projection,type_ignores=[]),super_ref.path,"exec"),scope)
 checked_spec=scope["spec"];manifest=json_object(scope["manifest"])
 state_dir:object=getattr(checked_spec,"state_dir",None)
 manifest_path:object=getattr(checked_spec,"manifest_path",None)
 need(isinstance(state_dir,Path) and isinstance(manifest_path,Path),"actual environment spec paths")
 observed:JsonObject={"state_dir":str(state_dir),"manifest_path":str(manifest_path),
                     "environment_sha256":text(manifest["environment_sha256"]),"config_ref":config_ref.to_wire()}
 evidence("supervisor_make_spec",super_ref,super_raw,"main",observed,projection)
 evidence("supervisor_verify_cold_profile",super_ref,super_raw,"main",observed,projection)
 continuity_observed=probe_current_saved_continuity_v1(
  plan,reader=LocalBasisReaderV1(),continuity_reader=LocalContinuityReaderV1())
 continuity_ref,continuity_raw=source("tools/g2_saved_campaign/prepare_current_saved_campaign_cold_v1.py")
 evidence("canonical_continuity_frontier",continuity_ref,continuity_raw,
          "probe_current_saved_continuity_v1",continuity_observed)
 mcp_observed,mcp_ref,mcp_raw=probe_current_saved_mcp_factory_v1(plan,quote)
 evidence("frozen_mcp_safe_boundary",mcp_ref,mcp_raw,"load_driver",mcp_observed)
 result=gate.CurrentSavedConsumerProbeV1(expected_machine_id,datetime.now(timezone.utc).isoformat(),
  str(root),plan.attempt_nonce,plan.task_nonce,plan_ref,quote_ref,plan.producer_ref,tuple(calls))
 return gate.parse_current_saved_consumer_probe_v1(result.to_wire()).to_wire()

def probe_current_saved_mcp_factory_v1(
 plan:ColdPlanV1,quote:ColdQuoteV1,
)->tuple[JsonObject,ExactRefV1,bytes]:
 """Execute the generated wrapper and real SDK factory with one constructor seam."""
 import argparse
 import importlib
 import inspect
 import types
 import sys
 from dataclasses import dataclass
 need(plan.runtime_root==quote.runtime_root and plan.machine_id==quote.machine_id
      and plan.business_source_generation==32,"one current Source32 probe")
 def function(value:object)->types.FunctionType:
  if not isinstance(value,types.FunctionType): raise ValueError("actual Python factory function required")
  return value
 def quoted(name:str)->tuple[ExactRefV1,bytes]:
  found=[row for row in quote.files if row.relative_path==name]
  need(len(found)==1,"one quoted G4 input: "+name)
  row=found[0];reference=ExactRefV1(row.path,row.bytes,row.sha256)
  return reference,read_ref_v1(reference)
 entry_ref,entry_raw=quoted("root_p37c23_mcp_entry.py")
 _,freeze_raw=quoted("ROOT-FINAL-SDK-FREEZE-P37C23-A15.json")
 frozen=record(parse_json(freeze_raw))
 source_root=Path(absolute_v1(frozen["source_root"])).resolve(strict=True)
 policy=record(parse_json(read_ref_v1(parse_ref(frozen["canonical_preload_policy"]))))
 dependency=Path(absolute_v1(policy["dependency_root"])).resolve(strict=True)
 base=record(parse_json(read_ref_v1(plan.sdk_base_ref)))
 def sdk_ref(name:str)->ExactRefV1:
  found=[record(item) for item in rows(base["files"]) if record(item).get("relative")==name]
  need(len(found)==1,"one actual SDK source: "+name)
  row=found[0]
  return ExactRefV1(str(source_root/name),integer(row["bytes"],1),digest(row["sha256"]))
 sdk_mcp_ref=sdk_ref("xar_autoplayer/bridge/mcp_server.py")
 sdk_mcp_raw=read_ref_v1(sdk_mcp_ref)
 sys.path[1:1]=[str(source_root),str(dependency)]
 mcp=importlib.import_module("xar_autoplayer.bridge.mcp_server")
 original=function(vars(mcp).get("load_driver"))
 need(Path(original.__code__.co_filename).resolve()==Path(sdk_mcp_ref.path).resolve(),
      "actual SDK factory origin")
 tree=ast.parse(entry_raw)
 wrappers=[node for node in tree.body if isinstance(node,ast.FunctionDef)
           and node.name=="_current_source32_load_driver_v1"]
 need(len(wrappers)==1,"one frozen generated wrapper")
 wrapper_node=wrappers[0]
 previous=[node.end_lineno for node in tree.body if isinstance(node,ast.FunctionDef)
           and node.lineno<wrapper_node.lineno and node.end_lineno is not None]
 need(bool(previous),"bounded generated wrapper prelude")
 start=max(previous)
 selected=[node for node in tree.body if node.lineno>start and node.lineno<=wrapper_node.lineno]
 need(4<=len(selected)<=8 and selected[-1] is wrapper_node,"finite actual import/origin/wrapper span")
 need(all(isinstance(node,(ast.ImportFrom,ast.Assign,ast.If,ast.FunctionDef)) for node in selected),
      "no unreviewed generated execution")
 namespace:dict[str,object]={"__name__":"current_saved_G4_frozen_wrapper", "Path":Path,
                             "os":__import__("os"),"mcp_server":mcp}
 exec(compile(ast.Module(body=selected,type_ignores=[]),entry_ref.path,"exec"),namespace)
 wrapper=function(namespace.get("_current_source32_load_driver_v1"))
 need(namespace.get("_source32_load_driver_v1") is original,"real factory import")
 native_type:object=vars(mcp).get("NativeHeadlessGameplayDriver")
 if not isinstance(native_type,type): raise ValueError("actual Native driver class")
 native_signature=inspect.signature(native_type)
 @dataclass
 class ProbeDriverV1:
  route_window_clock_v1:object
  route_contact_timeline_speed:int
  allow_route_contact_high_speed_ab:bool
  require_initial_lifestyle_focus_before_date_advance:bool=False
  initial_lifestyle_focus_gate_stage:str=""
 calls:list[inspect.BoundArguments]=[]
 def constructor_seam(*args:object,**kwargs:object)->ProbeDriverV1:
  bound=native_signature.bind(*args,**kwargs);calls.append(bound)
  clock:object=bound.arguments["route_window_clock_v1"]
  speed=integer(bound.arguments["route_contact_timeline_speed"],3,3)
  permission:object=bound.arguments["allow_route_contact_high_speed_ab"]
  need(permission is False,"original global A/B remains false")
  return ProbeDriverV1(clock,speed,False)
 factory_scope:dict[str,object]={key:value for key,value in original.__globals__.items()}
 factory_scope["NativeHeadlessGameplayDriver"]=constructor_seam
 factory=types.FunctionType(original.__code__,factory_scope,original.__name__,
                            original.__defaults__,original.__closure__)
 factory.__kwdefaults__=original.__kwdefaults__
 namespace["_source32_load_driver_v1"]=factory
 basis=parse_current_saved_basis_v1(parse_json(read_ref_v1(plan.basis_ref,65536)),expected_machine_id=plan.machine_id)
 paths=derive_current_saved_state_paths_v1(basis)
 result:object=wrapper("native-headless",state_dir=paths.state_root,
                       pipe_name=r"\\.\pipe\G4-NEVER-OPENED",route_contact_timeline_speed=3,
                       allow_route_contact_high_speed_ab=False)
 need(isinstance(result,ProbeDriverV1) and len(calls)==1,"generated wrapper reached one software constructor")
 if not isinstance(result,ProbeDriverV1): raise ValueError("probe driver model")
 need(getattr(result.route_window_clock_v1,"timeline_speed",None)==4
      and getattr(result.route_window_clock_v1,"research_high_speed_ab",None) is True
      and result.route_contact_timeline_speed==3 and result.allow_route_contact_high_speed_ab is False,
      "actual scoped4/true plus global3/false")
 negative_cases:tuple[tuple[str,object,bool],...]=(("vision-report",3,False),
  ("native-headless",True,False),("native-headless",3.0,False),("native-headless",4,False),("native-headless",3,True))
 rejected=0
 for name,speed_value,permission_value in negative_cases:
  try: wrapper(name,route_contact_timeline_speed=speed_value,allow_route_contact_high_speed_ab=permission_value)
  except ValueError: rejected+=1
  else: raise ValueError("generated wrapper accepted forbidden mode")
 need(rejected==5 and len(calls)==1,"negative cases never reach constructor")
 parser:object=function(vars(mcp).get("parser"))()
 if not isinstance(parser,argparse.ArgumentParser): raise ValueError("actual SDK parser")
 queue_ref,queue_raw=quoted("root_p37c23_sdk_queue.py")
 queue_tree=ast.parse(queue_raw)
 argv_nodes=[node for node in ast.walk(queue_tree) if isinstance(node,ast.Assign)
             and any(isinstance(target,ast.Name) and target.id=="argv" for target in node.targets)]
 constant_nodes=[node for node in queue_tree.body if isinstance(node,ast.FunctionDef) and node.name=="source_constant"]
 flags_nodes=[node for node in queue_tree.body if isinstance(node,ast.Assign)
              and any(isinstance(target,ast.Name) and target.id=="FLAGS_SOURCE" for target in node.targets)]
 need(len(argv_nodes)==len(constant_nodes)==len(flags_nodes)==1,"unique original MCP argv and flag consumer")
 _,config_raw=quoted("ROOT-LAUNCH-CONFIG-C23-A15.json");config=json_object(parse_json(config_raw))
 argv_scope:dict[str,object]={"ast":ast,"Path":Path,"N":Path(plan.runtime_root),"STATE_DIR":Path(paths.state_root),
  "base_executable":text(record(policy["direct_python"])["path"])}
 exec(compile(ast.Module(body=[constant_nodes[0],flags_nodes[0]],type_ignores=[]),queue_ref.path,"exec"),argv_scope)
 flags_value:object=function(argv_scope.get("source_constant"))(argv_scope["FLAGS_SOURCE"],"PRIVATE_FLAGS")
 if type(flags_value) not in (tuple,list): raise ValueError("original source flags sequence")
 if not isinstance(flags_value,(tuple,list)): raise ValueError("unreachable source flags")
 flags=[text(item) for item in flags_value]
 argv_scope.update(queue=types.SimpleNamespace(launch={"pipe":text(config["pipe_name"])},flags=flags),
                   args=types.SimpleNamespace(environment_manifest=Path(paths.environment_manifest)))
 exec(compile(ast.Module(body=[argv_nodes[0]],type_ignores=[]),queue_ref.path,"exec"),argv_scope)
 argv=[text(item) for item in rows(argv_scope["argv"])]
 need(len(argv)>6 and Path(argv[5]).resolve()==Path(entry_ref.path).resolve(),"original final SDK entry argv")
 parsed=parser.parse_args(argv[6:])
 need(parsed.driver=="native-headless" and Path(parsed.state_dir).resolve()==Path(paths.state_root).resolve(),
      "real SDK parser accepted original generated queue argv")
 for key in ("war31_one_shot_authorization_receipt","war31_one_shot_source_checkpoint",
             "war31_one_shot_source_driver","war31_one_shot_submission_fence"):
  need(key in vars(parsed) and vars(parsed)[key] is None,
       "software-only G4 refuses one-shot gates that could read Driver or SAVE")
 sdk_tree=ast.parse(sdk_mcp_raw)
 mains=[node for node in sdk_tree.body if isinstance(node,ast.FunctionDef) and node.name=="main"]
 need(len(mains)==1,"one actual SDK main")
 driver_assignments=[node for node in mains[0].body if isinstance(node,ast.Assign)
  and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name)
  and node.value.func.id=="load_driver" and any(isinstance(target,ast.Name)
  and target.id=="driver" for target in node.targets)]
 need(len(driver_assignments)==1,"one actual SDK main factory call")
 driver_assignment=driver_assignments[0]
 driver_call=driver_assignment.value
 need(isinstance(driver_call,ast.Call),"SDK driver assignment remains a call")
 if not isinstance(driver_call,ast.Call): raise ValueError("unreachable SDK factory call")
 need(len(driver_call.args)+len(driver_call.keywords)==14,"complete actual SDK main factory argument contract")
 prerequisites=[node for node in mains[0].body if isinstance(node,ast.Assign)
  and any(isinstance(target,ast.Name) and target.id in {"war31_paths","war31_gate","selected_state_dir"}
          for target in node.targets)]
 need(len(prerequisites)==3,"original pure CLI-derived factory prerequisites")
 main_projection=ast.Module(body=[*prerequisites,driver_assignment],type_ignores=[])
 lifecycle_forwarding_marker:JsonObject={
  "schema":"xar.current-saved-preflight-unqualified-lifecycle-forwarding-marker/v1",
  "source_manifest_path":paths.environment_manifest,"fresh_native_qualification":False,
  "ordinary_cycle_credit":0,"game_day_credit":0}
 main_scope:dict[str,object]={key:value for key,value in original.__globals__.items()}
 main_scope.update(args=parsed,load_driver=wrapper,succession_lifecycle_binding=lifecycle_forwarding_marker)
 before_main=len(calls)
 exec(compile(main_projection,sdk_mcp_ref.path,"exec"),main_scope)
 need(len(calls)==before_main+1 and isinstance(main_scope.get("driver"),ProbeDriverV1),
      "original SDK main projection reaches the same single constructor seam")
 need(calls[-1].arguments.get("succession_lifecycle_binding") is lifecycle_forwarding_marker,
      "original main and factory preserve the exact unqualified lifecycle forwarding fixture")
 main_driver=main_scope["driver"]
 if not isinstance(main_driver,ProbeDriverV1): raise ValueError("SDK main software driver")
 need(getattr(main_driver.route_window_clock_v1,"timeline_speed",None)==4
  and getattr(main_driver.route_window_clock_v1,"research_high_speed_ab",None) is True
  and main_driver.route_contact_timeline_speed==3 and main_driver.allow_route_contact_high_speed_ab is False,
  "complete SDK main argument forwarding preserves scoped4 and global3")
 constructor_arguments:JsonObject={}
 for key,value in calls[-1].arguments.items():
  if key=="route_window_clock_v1":
   constructor_arguments[key]={"timeline_speed":4,"research_high_speed_ab":True}
  else:
   constructor_arguments[key]=str(value) if isinstance(value,Path) else json_value(value)
 runtime=importlib.import_module("xar_autoplayer.runtime")
 runtime_ref=sdk_ref("xar_autoplayer/runtime.py");runtime_raw=read_ref_v1(runtime_ref)
 actual_runtime=Path(str(vars(runtime).get("__file__"))).resolve(strict=True)
 host_root=Path(text(frozen["runtime_source_repo"]))/"ck3_autonomous_player/src"
 need(actual_runtime in {Path(runtime_ref.path).resolve(),(host_root/"xar_autoplayer/runtime.py").resolve()}
      and actual_runtime.read_bytes()==runtime_raw,"qualified SDK or same-byte Host runtime DTO origin")
 config_type:object=vars(runtime).get("NativeBridgeLaunchConfig")
 if not isinstance(config_type,type): raise ValueError("runtime owns NativeBridgeLaunchConfig")
 native_config:object=config_type("native-headless",r"\\.\pipe\G4-NEVER-OPENED",
                                  Path("G4-NO-DLL-LOAD"),Path("G4-NO-INJECTOR-RUN"))
 need(getattr(native_config,"mode",None)=="native-headless","actual native launch parameter DTO")
 return json_object({"machine_id":plan.machine_id,"runtime_root":plan.runtime_root,
  "entry_source_ref":entry_ref.to_wire(),"sdk_factory_source_ref":sdk_mcp_ref.to_wire(),
  "runtime_DTO_source_ref":runtime_ref.to_wire(),"actual_runtime_module_path":str(actual_runtime),
  "queue_source_ref":queue_ref.to_wire(),"queue_argv_AST_sha256":sha256_v1(ast.dump(argv_nodes[0],include_attributes=False).encode()),
  "actual_imports_executed":True,"actual_factory_code_executed":True,"factory_positive_calls":len(calls),
  "wrapper_negative_rejections":rejected,"actual_parser_executed":True,
  "actual_SDK_main_factory_projection_executed":True,"main_factory_positive_calls":len(calls)-before_main,
  "main_factory_argument_count":len(driver_call.args)+len(driver_call.keywords),
  "main_factory_AST_sha256":sha256_v1(ast.dump(driver_call,include_attributes=False).encode()),
  "main_factory_projection_AST_sha256":sha256_v1(ast.dump(main_projection,include_attributes=False).encode()),
  "actual_constructor_arguments":constructor_arguments,
  "lifecycle_binding_scope":"unqualified_software_forwarding_marker",
  "live_lifecycle_binding_qualified":False,
  "parser_argument_scope":"original_queue_argv_projection","parser_argv_sha256":sha256_v1(encode_v1(argv)),
  "actual_native_launch_DTO_constructed":True,"software_only":True,"native_constructor_replaced":True,
  "route_window_clock":{"timeline_speed":4,"research_high_speed_ab":True},
  "global_timeline_speed":result.route_contact_timeline_speed,"global_high_speed_ab":False,
  "Native_driver_or_endpoint_constructed":False,"Game_RPC_Native_pipe_process_launch_calls":0,
  "Driver_SAVE_body_reads":0}),sdk_mcp_ref,sdk_mcp_raw


"""Offline Native32 journal contract. No endpoint, provider issuance or Game calls."""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
import json
import re
from typing import Literal, TypedDict

SCHEMA = "xar.ck3.time-command-observer32/v1"
STEP = "observe-time-command-journal-v1"
_U64 = (1 << 64) - 1
_U32 = (1 << 32) - 1
LookupOutcomeV1 = Literal["not_applicable", "active", "missing", "retired_same_address"]


class KindV1(IntEnum):
    REQUEST = 1
    CLONE = 2
    QUEUE_ENTER = 3
    INSERT_ENTER = 4
    INSERT_RETURN = 5
    QUEUE_RETURN = 6
    EXECUTE_ENTER = 7
    EXECUTE_RETURN = 8
    DELETE_ENTER = 9
    DELETE_RETURN = 10


@dataclass(frozen=True, slots=True)
class ExpectedGameV1:
    machine_id: str
    pid: int
    creation_filetime: int


@dataclass(frozen=True, slots=True)
class TokenV1:
    pointer: int
    incarnation: int


@dataclass(frozen=True, slots=True)
class EventV1:
    seq: int
    qpc: int
    kind: KindV1
    role: int
    invocation: int
    identity_epoch: int
    connection: int
    request_id: str
    attributed: bool
    identity_qualified: bool
    token: TokenV1
    parent: TokenV1
    observed_object: int
    observed_secondary: int
    retired_at_sequence: int
    lookup_outcome: LookupOutcomeV1
    payload_valid: bool
    native_sequence: int
    player_bits: int
    command_paused: bool
    desired_paused: bool


@dataclass(frozen=True, slots=True)
class JournalV1:
    qpc_frequency: int
    newest: int
    coverage_gaps: int
    lost: int
    events: tuple[EventV1, ...]


@dataclass(frozen=True, slots=True)
class RequestedIdsV1:
    request_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AllNativeObservedHistoryV1:
    """Explicit historical observer namespace; never protocol attribution."""


SelectionV1 = RequestedIdsV1 | AllNativeObservedHistoryV1


@dataclass(frozen=True, slots=True)
class ExecutePairV1:
    enter: EventV1
    returned: EventV1
    elapsed_seconds: float | None


class RequestedIdsJSONV1(TypedDict):
    mode: Literal["request-ids"]
    request_ids: list[str]


class HistoryJSONV1(TypedDict):
    mode: Literal["all-native-observed-history"]


SelectionJSONV1 = RequestedIdsJSONV1 | HistoryJSONV1


class SummaryV1(TypedDict):
    schema: Literal["xar.native32.offline-observation-summary/v1"]
    machine_id: str
    selection: SelectionJSONV1
    native_observed_execute_pairs: list[dict[str, object]]
    credit_days: Literal[0]
    drain_fence: Literal[False]
    automatic_recovery_allowed: Literal[False]
    protocol_connection_binding_verified: Literal[False]
    current_failed_request_completion_proven: Literal[False]
    absence_is_nonexecution_proof: Literal[False]
    runtime_admission_granted: Literal[False]


def _obj(value: object, keys: set[str] | None = None) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    result: dict[str, object] = {}
    for key, item in value.items():
        if type(key) is not str:
            raise ValueError("text JSON key required")
        result[key] = item
    if keys is not None and set(result) != keys:
        raise ValueError("exact JSON fields required")
    return result


def _int(value: object, high: int = _U32, low: int = 0) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError("exact bounded integer required")
    return value


def _decimal(value: object, low: int = 0) -> int:
    if type(value) is not str or re.fullmatch(r"0|[1-9][0-9]{0,19}", value) is None:
        raise ValueError("canonical uint64 decimal text required")
    result = int(value)
    if not low <= result <= _U64:
        raise ValueError("uint64 outside range")
    return result


def _bit(value: object) -> bool:
    return bool(_int(value, 1))


def _id(value: object, empty: bool = False) -> str:
    if type(value) is not str:
        raise ValueError("text request id required")
    if empty and value == "":
        return value
    if re.fullmatch(r"[A-Za-z0-9_.:-]{1,63}", value) is None:
        raise ValueError("bounded request id required")
    return value


def _token(value: object) -> TokenV1:
    row = _obj(value, {"pointer", "incarnation"})
    token = TokenV1(_decimal(row["pointer"]), _decimal(row["incarnation"]))
    if bool(token.pointer) != bool(token.incarnation):
        raise ValueError("partial token")
    return token


def _lookup(value: object) -> LookupOutcomeV1:
    if type(value) is not str:
        raise ValueError("text lookup outcome required")
    if value == "not_applicable":
        return "not_applicable"
    if value == "active":
        return "active"
    if value == "missing":
        return "missing"
    if value == "retired_same_address":
        return "retired_same_address"
    raise ValueError("unknown lookup outcome")


_EVENT_FIELDS = {
    "seq", "qpc", "thread", "kind", "role", "invocation", "identity_epoch",
    "connection", "attributed", "request_id", "desired_paused", "token", "parent",
    "caller_rva", "aux", "identity_qualified", "queue_accepted", "payload_valid",
    "player_bits", "command_paused", "native_sequence", "scalar_valid", "game",
    "jomini", "date_bits", "paused", "observed_object", "observed_secondary",
    "retired_at_sequence", "lookup_outcome",
}


def _event(value: object) -> EventV1:
    row = _obj(value, _EVENT_FIELDS)
    for name in ("thread", "player_bits", "native_sequence", "date_bits"):
        _int(row[name])
    for name in ("caller_rva", "aux", "game", "jomini"):
        _decimal(row[name])
    for name in ("queue_accepted", "scalar_valid", "paused"):
        _bit(row[name])
    if _bit(row["scalar_valid"]) and (
            _decimal(row["game"]) == 0 or _decimal(row["jomini"]) == 0):
        raise ValueError("valid scalar lacks object identity")
    event = EventV1(
        _decimal(row["seq"], 1), _decimal(row["qpc"]),
        KindV1(_int(row["kind"], 10, 1)), _int(row["role"], 3),
        _decimal(row["invocation"]), _decimal(row["identity_epoch"]),
        _decimal(row["connection"]), _id(row["request_id"], True),
        _bit(row["attributed"]), _bit(row["identity_qualified"]),
        _token(row["token"]), _token(row["parent"]),
        _decimal(row["observed_object"]), _decimal(row["observed_secondary"]),
        _decimal(row["retired_at_sequence"]), _lookup(row["lookup_outcome"]),
        _bit(row["payload_valid"]), _int(row["native_sequence"]),
        _int(row["player_bits"]), _bit(row["command_paused"]),
        _bit(row["desired_paused"]))
    if event.attributed and (not event.request_id or not event.connection):
        raise ValueError("attribution lacks recorded key")
    if event.lookup_outcome in ("missing", "retired_same_address"):
        if (event.token != TokenV1(0, 0) or event.parent != TokenV1(0, 0)
                or event.role or event.identity_epoch or event.attributed
                or event.identity_qualified or event.connection or event.request_id):
            raise ValueError("address-only diagnostic grants identity")
    if event.lookup_outcome == "missing" and event.retired_at_sequence:
        raise ValueError("missing lookup claims retirement")
    if event.lookup_outcome == "retired_same_address" and (
            not event.retired_at_sequence or event.retired_at_sequence >= event.seq):
        raise ValueError("retirement diagnostic lacks prior observed sequence")
    if event.identity_qualified and (event.lookup_outcome != "active"
            or not event.token.pointer or not event.identity_epoch):
        raise ValueError("identity qualification lacks active token")
    if event.lookup_outcome == "active" and (
            not event.token.pointer or event.token.pointer != event.observed_object):
        raise ValueError("active lookup object differs")
    if event.kind in (KindV1.EXECUTE_ENTER, KindV1.EXECUTE_RETURN) and (
            not event.observed_secondary or event.observed_object > _U64 - 0x18
            or event.observed_secondary != event.observed_object + 0x18):
        raise ValueError("Execute object/secondary address differs")
    return event


_JOURNAL_FIELDS = {
    "step", "accepted", "status", "drain_fence", "observer_schema",
    "lifetime_coverage", "scalar_samples_are_snapshots", "query_is_tail",
    "retirement_diagnostics", "payload_samples", "qpc_frequency", "snapshot_qpc",
    "process_id", "process_birth", "image_base", "attached", "readable", "newest",
    "oldest_retained", "returned_count", "first_returned", "coverage_gaps", "lost",
    "live_registry", "events",
}


def parse_journal_v1(value: object, *, request_id: str, expected: ExpectedGameV1) -> JournalV1:
    """Validate a frozen offline frame. This does not admit a live Native32 DLL."""
    if (type(expected) is not ExpectedGameV1 or type(expected.machine_id) is not str
            or not expected.machine_id):
        raise ValueError("explicit machine expectation required")
    _int(expected.pid, low=1)
    if type(expected.creation_filetime) is not int or not 1 <= expected.creation_filetime <= _U64:
        raise ValueError("exact positive FILETIME required")
    _id(request_id)
    frame = _obj(value, {"type", "protocol_version", "request_id", "ok", "result"})
    if (frame["type"] != "command_result" or _int(frame["protocol_version"], 1, 1) != 1
            or frame["request_id"] != request_id or frame["ok"] is not True):
        raise ValueError("exact successful envelope required")
    row = _obj(frame["result"], _JOURNAL_FIELDS)
    if (row["step"] != STEP or row["observer_schema"] != SCHEMA
            or row["accepted"] is not True or row["status"] != "passive_observation_only"
            or row["drain_fence"] is not False or row["query_is_tail"] is not True
            or row["scalar_samples_are_snapshots"] is not False
            or row["lifetime_coverage"] != "observed_clone_and_primary_delete_slots_only"
            or row["retirement_diagnostics"] != "bounded_recent_addresses_only"
            or row["payload_samples"] != "entry_observation_not_return_readback"
            or _int(row["attached"], 1) != 1 or _int(row["readable"], 1) != 1):
        raise ValueError("Native32 passive contract differs")
    if (_int(row["process_id"], low=1) != expected.pid
            or _decimal(row["process_birth"], 1) != expected.creation_filetime):
        raise ValueError("Game PID/FILETIME differs")
    _decimal(row["image_base"], 1)
    _decimal(row["snapshot_qpc"])
    _int(row["live_registry"], 64)
    count = _int(row["returned_count"], 64)
    raw = row["events"]
    if not isinstance(raw, list) or len(raw) != count:
        raise ValueError("bounded event JSON array required")
    events = tuple(_event(item) for item in raw)
    newest = _decimal(row["newest"])
    first = _decimal(row["first_returned"], 1)
    oldest = _decimal(row["oldest_retained"], 1)
    if (first != newest - count + 1 or oldest > first or first > newest + 1
            or tuple(event.seq for event in events) != tuple(range(first, newest + 1))):
        raise ValueError("exact tail bounds required")
    return JournalV1(_decimal(row["qpc_frequency"], 1), newest,
        _int(row["coverage_gaps"]), _decimal(row["lost"]), events)


def parse_selection_v1(value: object) -> SelectionV1:
    """Empty request_ids selects nothing; history requires an explicit mode."""
    row = _obj(value)
    if row.get("mode") == "all-native-observed-history":
        _obj(value, {"mode"})
        return AllNativeObservedHistoryV1()
    if row.get("mode") != "request-ids":
        raise ValueError("explicit selection mode required")
    row = _obj(value, {"mode", "request_ids"})
    values = row["request_ids"]
    if not isinstance(values, list) or len(values) > 64:
        raise ValueError("bounded request id JSON array required")
    ids = tuple(_id(item) for item in values)
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate request selection")
    return RequestedIdsV1(ids)


def encode_selection_v1(selection: SelectionV1) -> SelectionJSONV1:
    if type(selection) is AllNativeObservedHistoryV1:
        return {"mode": "all-native-observed-history"}
    if type(selection) is not RequestedIdsV1 or type(selection.request_ids) is not tuple:
        raise ValueError("typed explicit selection required")
    result: RequestedIdsJSONV1 = {"mode": "request-ids", "request_ids": list(selection.request_ids)}
    parse_selection_v1(result)
    return result


def execute_pairs_v1(journal: JournalV1, selection: SelectionV1) -> tuple[ExecutePairV1, ...]:
    encode_selection_v1(selection)
    wanted = frozenset(selection.request_ids) if isinstance(selection, RequestedIdsV1) else None
    entries: dict[tuple[str, int, int, int, int, int, int], EventV1] = {}
    pairs: list[ExecutePairV1] = []
    for event in journal.events:
        if (not event.attributed or not event.identity_qualified or not event.payload_valid
                or event.lookup_outcome != "active"
                or (wanted is not None and event.request_id not in wanted)
                or not event.connection or not event.invocation or not event.identity_epoch
                or not event.token.pointer or not event.token.incarnation or event.role == 0):
            continue
        key = (event.request_id, event.connection, event.identity_epoch, event.invocation,
            event.token.pointer, event.token.incarnation, event.role)
        if event.kind is KindV1.EXECUTE_ENTER:
            entries[key] = event
        elif event.kind is KindV1.EXECUTE_RETURN and key in entries:
            enter = entries.pop(key)
            if (event.seq <= enter.seq or event.native_sequence != enter.native_sequence
                    or event.player_bits != enter.player_bits
                    or event.command_paused != enter.command_paused
                    or event.desired_paused != enter.desired_paused
                    or event.observed_secondary != enter.observed_secondary):
                continue
            seconds = ((event.qpc - enter.qpc) / journal.qpc_frequency
                if enter.qpc > 0 and event.qpc >= enter.qpc else None)
            pairs.append(ExecutePairV1(enter, event, seconds))
    return tuple(pairs)


def result_payload_v1(journal: JournalV1, selection: SelectionV1,
        expected: ExpectedGameV1) -> SummaryV1:
    pairs: list[dict[str, object]] = []
    for pair in execute_pairs_v1(journal, selection):
        enter, returned = pair.enter, pair.returned
        pairs.append({"native_recorded_request_id": enter.request_id,
            "observer_connection": str(enter.connection),
            "identity_epoch": str(enter.identity_epoch), "invocation": str(enter.invocation),
            "pointer": str(enter.token.pointer), "incarnation": str(enter.token.incarnation),
            "observed_object": str(enter.observed_object),
            "observed_secondary": str(enter.observed_secondary),
            "enter_seq": str(enter.seq), "return_seq": str(returned.seq),
            "elapsed_seconds": pair.elapsed_seconds})
    return {"schema": "xar.native32.offline-observation-summary/v1",
        "machine_id": expected.machine_id, "selection": encode_selection_v1(selection),
        "native_observed_execute_pairs": pairs, "credit_days": 0, "drain_fence": False,
        "automatic_recovery_allowed": False, "protocol_connection_binding_verified": False,
        "current_failed_request_completion_proven": False,
        "absence_is_nonexecution_proof": False, "runtime_admission_granted": False}


def encode_result_v1(value: SummaryV1) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"), allow_nan=False)


def require_runtime_qualification_v1() -> None:
    """No Native32 DLL SHA, ABI qualification or loaded-provider pin exists yet."""
    raise ValueError("Native32 runtime source/ABI/DLL/provider binding is unqualified")

# Independent production transport. The exact sealed offline parser above is
# unchanged, including its always-rejecting require_runtime_qualification_v1.
import ast
import hashlib
import importlib
from pathlib import Path
import sys
import time
from typing import Callable, Mapping, Protocol

SEALED_PARSER_BYTES = 15948
SEALED_PARSER_SHA256 = "97e1495f857f2562dc90dcbfea351362f6be9363372f1bc3ecd65e11ef22d6d6"
_HEADER = (4669, "e5534112bd49e9242f6d4ff6cbee7fcbbab38bb3628d006ffcd726c9baa6bf62")
_CORE = (16599, "5f8ee4ea50b3b2441978fea1e82a10792d5bcd59bd29fd39d7ff6229d57d0b5d")


class ExactRefV1(TypedDict):
    path: str
    bytes: int
    sha256: str


class ProductionBindingWireV2(TypedDict):
    schema: Literal["xar.native32.source31-production-observer-binding/v2"]
    machine_id: str
    status: Literal["COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"]
    sdk_base_ref: ExactRefV1
    sdk_anchor_ref: ExactRefV1
    production_result_ref: ExactRefV1
    production_input_manifest_ref: ExactRefV1
    dll: ExactRefV1
    sealed_parser_source: ExactRefV1


@dataclass(frozen=True)
class ProductionBindingV2:
    wire: ProductionBindingWireV2
    sdk_root: Path


class EndpointV1(Protocol):
    @property
    def pipe_name(self) -> str: ...
    def send(self, frame: dict[str, object]) -> None: ...


class StateV1(Protocol):
    def diagnostics(self) -> Mapping[str, object]: ...
    def wait_for_command_result(self, request_id: str,
                                timeout_seconds: float) -> object: ...


class DriverV1(Protocol):
    @property
    def endpoint(self) -> EndpointV1: ...
    @property
    def state(self) -> StateV1: ...
    @property
    def pipe_name(self) -> str: ...


@dataclass(frozen=True)
class RuntimeContextV1:
    binding: ProductionBindingV2
    game: ExpectedGameV1
    connection_generation: int
    pipe_name: str
    provider: object


class Native32ResultV1(TypedDict):
    schema: Literal["xar.native32.readonly-journal-result/v1"]
    status: Literal["positive_observations_only", "unavailable"]
    reason: str | None
    machine_id: str
    game_pid: int
    game_creation_filetime: str
    connection_generation: str
    native_dll_sha256: str
    production_result: ExactRefV1
    request_id: str
    elapsed_seconds: float
    actual_native_requests: Literal[0, 1]
    selection: SelectionJSONV1
    summary: SummaryV1 | None
    original_parsed_frame_json: str | None
    credit_days: Literal[0]
    ordinary_cycle_credit: Literal[0]
    drain_fence: Literal[False]
    automatic_recovery_allowed: Literal[False]
    protocol_connection_binding_verified: Literal[False]
    current_failed_request_completion_proven: Literal[False]
    absence_is_nonexecution_proof: Literal[False]
    loaded_provider_issued_by_reader: Literal[False]


def _text32(value: object) -> str:
    if type(value) is not str or not value or "\0" in value:
        raise ValueError("nonempty text required")
    return value


def _ref32(value: object) -> ExactRefV1:
    row = _obj(value, {"path", "bytes", "sha256"})
    path = _text32(row["path"])
    size = _int(row["bytes"], (1 << 53) - 1, 1)
    digest = _text32(row["sha256"])
    if not Path(path).is_absolute() or re.fullmatch("[0-9a-f]{64}", digest) is None:
        raise ValueError("exact absolute source reference required")
    return {"path": path, "bytes": size, "sha256": digest}


def _filepin32(value: object) -> ExactRefV1:
    row = _obj(value, {"path", "bytes", "sha256", "device", "file_id", "mtime_ns"})
    for key in ("device", "file_id", "mtime_ns"):
        _decimal(row[key])
    return _ref32({key: row[key] for key in ("path", "bytes", "sha256")})


def _read32(reference: ExactRefV1, limit: int) -> dict[str, object]:
    path = Path(reference["path"])
    before = path.stat()
    if not 0 < reference["bytes"] <= limit or before.st_size != reference["bytes"]:
        raise ValueError("bounded qualified reference required")
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    after = path.stat()
    if (len(raw) != reference["bytes"]
            or hashlib.sha256(raw).hexdigest() != reference["sha256"]
            or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
            != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)):
        raise ValueError("qualified source bytes or identity changed")
    decoded: object = json.loads(raw)
    return _obj(decoded)


def _rows32(value: object, count: int) -> list[object]:
    if type(value) is not list or len(value) != count:
        raise ValueError("exact qualified record count required")
    return list(value)


def qualify_native32_binding_v1(value: object, *,
                               machine_id: str) -> ProductionBindingV2:
    """Static production facts only. Never grant runtime or issue a provider."""
    row = _obj(value, {"schema", "machine_id", "status", "sdk_base_ref",
        "sdk_anchor_ref", "production_result_ref", "production_input_manifest_ref",
        "dll", "sealed_parser_source"})
    if (row["schema"] != "xar.native32.source31-production-observer-binding/v2"
            or row["machine_id"] != machine_id or not machine_id
            or row["status"] != "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED"):
        raise ValueError("explicit machine Native32 cold binding required")
    base_ref = _ref32(row["sdk_base_ref"])
    anchor_ref = _ref32(row["sdk_anchor_ref"])
    production_ref = _ref32(row["production_result_ref"])
    plan_ref = _ref32(row["production_input_manifest_ref"])
    dll = _ref32(row["dll"])
    parser_ref = _ref32(row["sealed_parser_source"])
    if (parser_ref["bytes"], parser_ref["sha256"]) != (
            SEALED_PARSER_BYTES, SEALED_PARSER_SHA256):
        raise ValueError("sealed Native32 parser provenance differs")
    with Path(__file__).open("rb") as stream:
        prefix = stream.read(SEALED_PARSER_BYTES)
    if hashlib.sha256(prefix).hexdigest() != SEALED_PARSER_SHA256:
        raise ValueError("embedded offline parser changed")
    production = _read32(production_ref, 65536)
    if (production.get("schema") != "xar.native32.offline-production-result/v1"
            or production.get("status") != "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
            or production.get("machine_id") != machine_id):
        raise ValueError("actual Native32 production qualification required")
    for key in ("original_807_overlay_preserved", "all_four_header_consumers_recompiled",
                "reused_inputs_before_after_stat_equal"):
        if production.get(key) is not True:
            raise ValueError("production qualification missing: " + key)
    for key in ("runtime_qualified", "drain_fence", "performance_goal_qualified",
                "old_commands_archive_member_extracted"):
        if production.get(key) is not False:
            raise ValueError("offline production boundary differs: " + key)
    for key in ("Game_calls", "DLL_loads", "deployment_changes"):
        if type(production.get(key)) is not int or production[key] != 0:
            raise ValueError("production record claims runtime work")
    if (production.get("qualification_mode") != "link_only_continuation_after_transient_leaf_cap"
            or production.get("original_production_attempt_failed") is not True
            or production.get("partial_bytes_unreadable_after_overwrite") is not True
            or type(production.get("recompiles_in_continuation")) is not int
            or production["recompiles_in_continuation"] != 0):
        raise ValueError("actual qualified link-continuation contract differs")
    for key in ("continuation_producer", "continuation_plan", "original_failure"):
        _filepin32(production.get(key))
    for partial in _rows32(production.get("partial_preimages"), 4):
        _filepin32(partial)  # Historical overwritten bytes must not be re-read.
    link = _read32(_filepin32(production.get("continuation_link_receipt")), 16384)
    if type(link.get("return_code")) is not int or link["return_code"] != 0:
        raise ValueError("actual continuation link must succeed")
    if _filepin32(production.get("plan")) != plan_ref:
        raise ValueError("production input manifest differs")
    plan = _read32(plan_ref, 262144)
    if plan.get("machine_id") != machine_id:
        raise ValueError("production plan machine differs")
    sources = _obj(production.get("sources"))
    if sources != _obj(plan.get("source_inputs")):
        raise ValueError("production source inputs differ from plan")
    for key, expected in (("header", _HEADER), ("core", _CORE)):
        reference = _filepin32(sources.get(key))
        if (reference["bytes"], reference["sha256"]) != expected:
            raise ValueError("Native32 header/core qualification differs")
    objects = [_filepin32(item) for item in _rows32(production.get("objects"), 4)]
    if {Path(item["path"]).name for item in objects} != {
            "native32-bridge.obj", "native32-commands.obj",
            "native32-core.obj", "native32-install.obj"}:
        raise ValueError("all four header consumers must be recompiled")
    outputs32 = [_filepin32(item) for item in _rows32(production.get("outputs"), 4)]
    if ({Path(item["path"]).suffix for item in outputs32} != {".dll", ".map", ".lib", ".exp"}
            or [item for item in outputs32 if Path(item["path"]).suffix == ".dll"] != [dll]):
        raise ValueError("actual qualified DLL differs")
    expected_exports = {"XarCk3BridgeIdentity", "XarCk3BridgePrepareStartup",
        "XarCk3BridgeStart", "XarCk3BridgeStartWithPipe", "XarCk3BridgeStop",
        "XarRefillCoreCarrier12004"}
    exports: set[str] = set()
    for item in _rows32(production.get("exports"), 6):
        export = _obj(item, {"name", "rva", "executable", "forwarded"})
        name = _text32(export["name"])
        rva = _text32(export["rva"])
        if (name in exports or re.fullmatch("0x[0-9a-f]+", rva) is None
                or not 0 < int(rva, 16) < 2**32 or export["forwarded"] is not False
                or type(export["executable"]) is not bool
                or export["executable"] is (name == "XarRefillCoreCarrier12004")):
            raise ValueError("qualified executable exports differ; DATA is not callable")
        exports.add(name)
    if exports != expected_exports:
        raise ValueError("exact six production exports required")
    functions: set[str] = set()
    for item in _rows32(production.get("core_link_proof"), 4):
        proof = _obj(item, {"function", "symbol", "bytes", "normalized_sha256",
            "linked_rva", "verified_target_relocations", "all_nonrelocation_bytes_equal"})
        function = _text32(proof["function"])
        if (function in functions or proof["all_nonrelocation_bytes_equal"] is not True
                or re.fullmatch("[0-9a-f]{64}", _text32(proof["normalized_sha256"])) is None):
            raise ValueError("linked core proof differs")
        _int(proof["bytes"], _U64, 1)
        _int(proof["verified_target_relocations"], _U64, 1)
        _decimal(proof["linked_rva"], 1)
        _text32(proof["symbol"])
        functions.add(function)
    if functions != {"ForwardExecute", "ForwardAppend", "Enter", "DiagnosticFrame"}:
        raise ValueError("four exact linked core proofs required")
    base = _read32(base_ref, 524288)
    anchor = _read32(anchor_ref, 65536)
    if (base.get("schema") != "root.ck3.final-sdk-freeze/v1"
            or base.get("status") != "FINAL_SOURCE_FROZEN"
            or base.get("runtime_admitted") is not False or base.get("machine_id") != machine_id
            or type(base.get("source_file_count")) is not int or base["source_file_count"] != 1466
            or base.get("source31_canonical_anchor") != anchor_ref
            or anchor.get("schema") != "xar.source31.canonical-git-anchor/v1"
            or anchor.get("status") != "CANONICAL_REF_CREATED_NOT_DEPLOYED"
            or anchor.get("machine_id") != machine_id
            or anchor.get("commit") != base.get("business_source_commit")
            or re.fullmatch("[0-9a-f]{40}", _text32(anchor.get("commit"))) is None):
        raise ValueError("actual Source31 BASE/anchor binding required")
    root = Path(_text32(base.get("source_root"))).resolve(strict=True)
    if not root.is_dir() or Path(dll["path"]).stat().st_size != dll["bytes"]:
        raise ValueError("actual SDK root or qualified DLL size differs")
    wire: ProductionBindingWireV2 = {
        "schema": "xar.native32.source31-production-observer-binding/v2",
        "machine_id": machine_id, "status": "COLD_SOURCE_BOUND_NOT_RUNTIME_ADMITTED",
        "sdk_base_ref": base_ref, "sdk_anchor_ref": anchor_ref,
        "production_result_ref": production_ref,
        "production_input_manifest_ref": plan_ref, "dll": dll,
        "sealed_parser_source": parser_ref}
    return ProductionBindingV2(wire, root)


def _same_holder32(owner: object, sdk_root: Path) -> None:
    from xar_autoplayer.bridge.native_loaded_provider_custody_v1 import (
        _PreloadCustodyV1, _RESOURCE_SEAL)
    from xar_autoplayer.bridge.native_loaded_provider_origin_v1 import _OriginSessionV1
    for name in ("native_loaded_provider_custody_v1", "native_loaded_provider_origin_v1"):
        module = importlib.import_module("xar_autoplayer.bridge." + name)
        if Path(_text32(getattr(module, "__file__", None))).resolve() != sdk_root / ("xar_autoplayer/bridge/" + name + ".py"):
            raise ValueError("custody/origin contract imported from another SDK")
    holder: object = getattr(owner, "_player_heir_loaded_custody_v1", None)
    if (not isinstance(holder, _PreloadCustodyV1)
            or getattr(holder, "seal", None) is not _RESOURCE_SEAL
            or getattr(holder, "closed", None) is not False
            or getattr(holder, "owner", None) is not owner):
        raise ValueError("same open original loaded Native custody required")
    session: object = getattr(holder, "_origin_session_v1", None)
    epoch: object = getattr(owner, "epoch", None)
    if (type(session) is not _OriginSessionV1
            or getattr(session, "holder", None) is not holder
            or type(epoch) is not str or not epoch
            or getattr(session, "epoch", None) != epoch):
        raise ValueError("same existing origin session and epoch required")


def ensure_existing_owner_v1(owner: object,
                             ensure: Callable[[object], object], *, sdk_root: Path) -> None:
    """Only an explicit read calls the existing issuer; never construct a DTO."""
    from xar_autoplayer.bridge.native_loaded_provider_custody_v1 import CustodyIssueResultV1
    outcome = ensure(owner)
    if outcome is not None and (not isinstance(outcome, CustodyIssueResultV1)
            or type(outcome.issued) is not bool or outcome.issued is not True):
        raise ValueError("existing loaded Native custody issuer unavailable")
    _same_holder32(owner, sdk_root)


def require_native32_context_v1(owner: object, driver: DriverV1, *,
        binding_value: object, machine_id: str) -> RuntimeContextV1:
    binding = qualify_native32_binding_v1(binding_value, machine_id=machine_id)
    from xar_autoplayer.bridge import player_heir_candidate_component_v1 as component
    if Path(component.__file__).resolve() != (
            binding.sdk_root / "xar_autoplayer/bridge/player_heir_candidate_component_v1.py"):
        raise ValueError("loaded-provider contract imported from another SDK")
    value: object = getattr(owner, "_player_heir_loaded_provider_v1", None)
    if not isinstance(value, component._LoadedNativeProviderV1):
        raise ValueError("actual original loaded-provider DTO required")
    if (value.seal is not component._LOADED_NATIVE_SEAL or value.owner is not owner
            or value.driver is not driver or value.machine_id != machine_id
            or value.native_dll_sha256 != binding.wire["dll"]["sha256"]
            or value.pipe_name != driver.pipe_name or driver.endpoint.pipe_name != driver.pipe_name
            or getattr(owner, "driver", None) is not driver
            or getattr(owner, "machine", None) != machine_id
            or getattr(driver, "_player_heir_candidate_owner_v1", None) is not owner):
        raise ValueError("actual Native32 owner/driver/provider binding differs")
    pid = _int(value.game_pid, (1 << 32) - 1, 1)
    birth = _int(value.game_creation_filetime, _U64, 1)
    generation = _int(value.connection_generation, _U64, 1)
    _same_holder32(owner, binding.sdk_root)
    return RuntimeContextV1(binding, ExpectedGameV1(machine_id, pid, birth),
                            generation, driver.pipe_name, value)


def _connected32(state: StateV1, context: RuntimeContextV1) -> bool:
    try:
        info = _obj(dict(state.diagnostics()))
        hello = _obj(info.get("hello"))
        return (info.get("connected") is True
            and _int(info.get("connection_generation"), _U64, 1) == context.connection_generation
            and _int(hello.get("pid"), (1 << 32) - 1, 1) == context.game.pid
            and _int(hello.get("connection_generation"), _U64, 1) == context.connection_generation)
    except ValueError:
        return False


def read_native32_once_v1(owner: object, driver: DriverV1, *,
        binding_value: object, machine_id: str, request_id: str,
        selection: SelectionV1, timeout_seconds: float = 2.0) -> Native32ResultV1:
    _id(request_id)
    selected = encode_selection_v1(selection)
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 5:
        raise ValueError("one bounded journal wait required")
    context = require_native32_context_v1(owner, driver,
        binding_value=binding_value, machine_id=machine_id)
    start = time.monotonic()
    result: Native32ResultV1 = {
        "schema": "xar.native32.readonly-journal-result/v1", "status": "unavailable",
        "reason": None, "machine_id": machine_id, "game_pid": context.game.pid,
        "game_creation_filetime": str(context.game.creation_filetime),
        "connection_generation": str(context.connection_generation),
        "native_dll_sha256": context.binding.wire["dll"]["sha256"],
        "production_result": context.binding.wire["production_result_ref"],
        "request_id": request_id, "elapsed_seconds": 0.0, "actual_native_requests": 0,
        "selection": selected, "summary": None, "original_parsed_frame_json": None,
        "credit_days": 0, "ordinary_cycle_credit": 0, "drain_fence": False,
        "automatic_recovery_allowed": False, "protocol_connection_binding_verified": False,
        "current_failed_request_completion_proven": False,
        "absence_is_nonexecution_proof": False, "loaded_provider_issued_by_reader": False}
    if not _connected32(driver.state, context):
        result["reason"] = "connection differs before read"
        return result
    driver.endpoint.send({"type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP, "expected_revision": 0})
    result["actual_native_requests"] = 1
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    result["elapsed_seconds"] = time.monotonic() - start
    if frame is None:
        result["reason"] = "exact journal result timed out; no retry"
        return result
    saved = json.dumps(frame, ensure_ascii=True, separators=(",", ":"), allow_nan=False)
    if len(saved.encode()) > 98304:
        raise ValueError("bounded Native32 frame exceeds source contract; no retry")
    result["original_parsed_frame_json"] = saved
    if (not _connected32(driver.state, context)
            or getattr(owner, "_player_heir_loaded_provider_v1", None) is not context.provider):
        result["reason"] = "connection or loaded provider changed after read"
        return result
    _same_holder32(owner, context.binding.sdk_root)
    parsed: object = json.loads(saved)
    try:
        journal = parse_journal_v1(parsed, request_id=request_id, expected=context.game)
        result["summary"] = result_payload_v1(journal, selection, context.game)
    except ValueError as error:
        result["reason"] = str(error)
        return result
    result["status"] = "positive_observations_only"
    return result


def parse_native32_result_v1(value: object, *, machine_id: str,
        game_pid: int, creation_filetime: int, native_dll_sha256: str) -> Native32ResultV1:
    """Consumer validation never converts a journal into completion or action credit."""
    _int(game_pid, (1 << 32) - 1, 1)
    _int(creation_filetime, _U64, 1)
    _text32(machine_id)
    _text32(native_dll_sha256)
    row = _obj(value, set(Native32ResultV1.__annotations__))
    pid = _int(row["game_pid"], (1 << 32) - 1, 1)
    birth = _decimal(row["game_creation_filetime"], 1)
    generation = _decimal(row["connection_generation"], 1)
    status = row["status"]
    if (row["schema"] != "xar.native32.readonly-journal-result/v1"
            or row["machine_id"] != machine_id or pid != game_pid or birth != creation_filetime
            or row["native_dll_sha256"] != native_dll_sha256
            or re.fullmatch("[0-9a-f]{64}", native_dll_sha256) is None
            or status not in ("positive_observations_only", "unavailable")):
        raise ValueError("current bound Native32 result required")
    for key in ("drain_fence", "automatic_recovery_allowed",
                "protocol_connection_binding_verified", "current_failed_request_completion_proven",
                "absence_is_nonexecution_proof", "loaded_provider_issued_by_reader"):
        if row[key] is not False:
            raise ValueError("journal grants forbidden inference")
    for key in ("credit_days", "ordinary_cycle_credit"):
        if type(row[key]) is not int or row[key] != 0:
            raise ValueError("journal grants credit")
    requests = _int(row["actual_native_requests"], 1)
    elapsed = row["elapsed_seconds"]
    if not (type(elapsed) is int or type(elapsed) is float) or not 0 <= elapsed < float("inf"):
        raise ValueError("finite elapsed seconds required")
    request_id = _id(row["request_id"])
    selection = parse_selection_v1(row["selection"])
    raw = row["original_parsed_frame_json"]
    summary: SummaryV1 | None = None
    if status == "positive_observations_only":
        if requests != 1 or row["reason"] is not None or type(raw) is not str or len(raw.encode()) > 98304:
            raise ValueError("positive observation needs its exact native frame")
        frame: object = json.loads(raw)
        journal = parse_journal_v1(frame, request_id=request_id,
            expected=ExpectedGameV1(machine_id, pid, birth))
        summary = result_payload_v1(journal, selection, ExpectedGameV1(machine_id, pid, birth))
        if row["summary"] != summary:
            raise ValueError("native result summary differs")
    elif (type(row["reason"]) is not str or not row["reason"] or row["summary"] is not None
            or (raw is not None and (type(raw) is not str or len(raw.encode()) > 98304))):
        raise ValueError("unavailable result must preserve reason and no positive summary")
    status32: Literal["positive_observations_only", "unavailable"] = "positive_observations_only" if status == "positive_observations_only" else "unavailable"
    return {
        "schema": "xar.native32.readonly-journal-result/v1", "status": status32,
        "reason": row["reason"] if isinstance(row["reason"], str) else None,
        "machine_id": machine_id, "game_pid": pid, "game_creation_filetime": str(birth),
        "connection_generation": str(generation), "native_dll_sha256": native_dll_sha256,
        "production_result": _ref32(row["production_result"]), "request_id": request_id,
        "elapsed_seconds": float(elapsed), "actual_native_requests": 1 if requests else 0,
        "selection": encode_selection_v1(selection), "summary": summary,
        "original_parsed_frame_json": raw if isinstance(raw, str) else None,
        "credit_days": 0, "ordinary_cycle_credit": 0, "drain_fence": False,
        "automatic_recovery_allowed": False, "protocol_connection_binding_verified": False,
        "current_failed_request_completion_proven": False,
        "absence_is_nonexecution_proof": False, "loaded_provider_issued_by_reader": False}


def patch_queue_control_v1(source: bytes, *, production_binding_basename: str) -> bytes:
    """Future-cold finite transform. No runtime file or existing Queue is changed."""
    if (type(production_binding_basename) is not str
            or not production_binding_basename.endswith(".json")
            or Path(production_binding_basename).name != production_binding_basename
            or "/" in production_binding_basename or "\\" in production_binding_basename):
        raise ValueError("one explicit cold production-binding basename required")
    text = source.decode("utf-8")
    protocol = 'def model_dump(self, *, mode: Literal["json"]) -> dict[str,object]: ...'
    if text.count(protocol) != 1:
        raise ValueError("one canonical MCP serialization protocol required")
    text = text.replace(protocol,
        'def model_dump(self, *, mode: Literal["json"], by_alias: Literal[False]) -> dict[str,object]: ...', 1)
    tree = ast.parse(text)
    names = ("observe_native31_journal_root_v1", "run_request_loop")
    nodes = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name in names]
    if len(nodes) != 2 or {n.name for n in nodes} != set(names):
        raise ValueError("two original Native31 control functions required")
    for node in reversed(nodes):
        part = ast.get_source_segment(text, node)
        if part is None:
            raise ValueError("exact Queue control source segment required")
        if node.name == names[0]:
            if (part.count("read_timeout_seconds=30.0") != 1
                    or part.count('"xar.native31.root-journal-observation/v1"') != 1):
                raise ValueError("original bounded journal contract differs")
        elif (part.count('command != "observe_native31_journal"') != 1
                or part.count('elif command == "observe_native31_journal"') != 1):
            raise ValueError("original dispatch/exclusion contract differs")
        changed = part.replace("native31", "native32").replace("_N31", "_N32")
        if node.name == names[0]:
            old_dump = '        row["result"] = result.model_dump(mode="json")'
            if changed.count(old_dump) != 1:
                raise ValueError("one canonical result consumer required")
            consumer = (
                '        row["result"] = result.model_dump(mode="json", by_alias=False)\n'
                '        from native32_mcp_extension_v1 import validate_native32_mcp_result_v1\n'
                '        validate_native32_mcp_result_v1(row["result"],\n'
                '            actual_game=read(N / "ROOT-ACTUAL-GAME-LAUNCH-C23.json", 65536),\n'
                '            binding_value=read(N / ' + repr(production_binding_basename) + ', 65536),\n'
                '            machine_id=MACHINE)\n'
                '        row["native32_result_validated"] = True')
            changed = changed.replace(old_dump, consumer, 1)
        if text.count(part) != 1:
            raise ValueError("one exact original Queue segment required")
        text = text.replace(part, changed, 1)
    # The protocols are annotations only, renamed together with both callers.
    for name in ("_N31ToolResultV1", "_N31SessionV1", "_N31QueueV1"):
        text = text.replace(name, name.replace("_N31", "_N32"))
    if "observe_native31_journal_root_v1" in text:
        raise ValueError("old journal Root consumer remains")
    compile(text, "<future-native32-Queue>", "exec")
    return text.encode("utf-8")

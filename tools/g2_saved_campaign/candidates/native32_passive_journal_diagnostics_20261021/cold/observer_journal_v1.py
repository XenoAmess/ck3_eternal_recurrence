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

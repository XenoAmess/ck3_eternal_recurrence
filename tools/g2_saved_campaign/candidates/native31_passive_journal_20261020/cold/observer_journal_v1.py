"""Fixed, passive Native31 journal read using an existing Source28 owner.
No lifecycle creation, provider issuance, Snapshot query, retry or Game action.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Protocol, Mapping, Literal, cast
import copy
import json
import re
import time

STEP = "observe-time-command-journal-v1"
SCHEMA = "xar.ck3.time-command-observer31/v1"
NATIVE31_SHA256 = "3d43cd01c908013f7bb2704aa1844acd518fa691ae96ef4e09413284dd59038d"
_U64 = (1 << 64) - 1

class EndpointV1(Protocol):
    @property
    def pipe_name(self) -> str: ...
    def send(self, frame: dict[str, object]) -> None: ...

class StateV1(Protocol):
    def diagnostics(self) -> dict[str, object]: ...
    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> dict[str, object] | None: ...

class DriverV1(Protocol):
    @property
    def pipe_name(self) -> str: ...
    @property
    def endpoint(self) -> EndpointV1: ...
    @property
    def state(self) -> StateV1: ...

class KindV1(IntEnum):
    REQUEST=1
    CLONE=2
    QUEUE_ENTER=3
    INSERT_ENTER=4
    INSERT_RETURN=5
    QUEUE_RETURN=6
    EXECUTE_ENTER=7
    EXECUTE_RETURN=8
    DELETE_ENTER=9
    DELETE_RETURN=10

@dataclass(frozen=True, slots=True)
class ExpectedGameV1:
    machine_id: str
    pid: int
    creation_filetime: int
    connection_generation: int
    pipe_name: str
    native_dll_sha256: str

@dataclass(frozen=True, slots=True)
class TokenV1:
    pointer: int
    incarnation: int

@dataclass(frozen=True, slots=True)
class ScalarSampleV1:
    game_pointer: int
    jomini_pointer: int
    date_bits: int
    paused: bool
    valid: bool

@dataclass(frozen=True, slots=True)
class EventV1:
    seq: int
    qpc: int
    thread: int
    kind: KindV1
    role: int
    invocation: int
    identity_epoch: int
    connection: int
    request_id: str
    attributed: bool
    qualified: bool
    desired_paused: bool
    token: TokenV1
    parent: TokenV1
    caller_rva: int
    aux: int
    native_sequence: int
    player_bits: int
    command_paused: bool
    payload_valid: bool
    queue_accepted: bool
    scalar: ScalarSampleV1

@dataclass(frozen=True, slots=True)
class JournalV1:
    process_id: int
    process_birth: str
    qpc_frequency: int
    snapshot_qpc: int
    image_base: int
    newest: int
    oldest_retained: int
    first_returned: int
    coverage_gaps: int
    lost: int
    live_registry: int
    events: tuple[EventV1, ...]

@dataclass(frozen=True, slots=True)
class ExecutePairV1:
    """Observed pair within the native observer namespace, not protocol binding."""
    enter: EventV1
    returned: EventV1
    elapsed_seconds: float | None

@dataclass(frozen=True, slots=True)
class ReadResultV1:
    status: Literal["unavailable", "positive_observations_only"]
    reason: str | None
    expected: ExpectedGameV1
    request_id: str
    elapsed_seconds: float
    journal: JournalV1 | None
    execute_pairs: tuple[ExecutePairV1, ...]
    original_parsed_frame: Mapping[str, object] | None
    actual_native_requests: int
    credit_days: Literal[0] = field(default=0, init=False)
    drain_fence: Literal[False] = field(default=False, init=False)
    automatic_recovery_allowed: Literal[False] = field(default=False, init=False)
    loaded_provider_issued: Literal[False] = field(default=False, init=False)
    absence_is_nonexecution_proof: Literal[False] = field(default=False, init=False)
    protocol_connection_binding_verified: Literal[False] = field(default=False, init=False)
    current_failed_request_completion_proven: Literal[False] = field(default=False, init=False)

def _obj(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("expected object")
    out: dict[str, object] = {}
    for key, item in cast(dict[object, object], value).items():
        if not isinstance(key, str):
            raise ValueError("object key is not text")
        out[key] = item
    return out

def _int(value: object, high: int = _U64, low: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise ValueError("integer outside native range")
    return value

def _text(value: object, high: int = 128, empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > high or (not value and not empty):
        raise ValueError("invalid bounded text")
    return value

def _bit(value: object) -> bool:
    return bool(_int(value, 1))

def _token(value: object) -> TokenV1:
    item = _obj(value)
    return TokenV1(_int(item.get("pointer")), _int(item.get("incarnation")))

def _event(value: object) -> EventV1:
    e = _obj(value)
    request_id = _text(e.get("request_id"), 63, True)
    attributed = _bit(e.get("attributed"))
    if request_id and re.fullmatch(r"[A-Za-z0-9_.:-]+", request_id) is None:
        raise ValueError("invalid recorded request id")
    if attributed and not request_id:
        raise ValueError("attributed request missing")
    scalar = ScalarSampleV1(_int(e.get("game")), _int(e.get("jomini")),
        _int(e.get("date_bits"), (1 << 32)-1), _bit(e.get("paused")),
        _bit(e.get("scalar_valid")))
    if scalar.valid and (not scalar.game_pointer or not scalar.jomini_pointer):
        raise ValueError("valid scalar lacks object identity")
    return EventV1(_int(e.get("seq"), low=1), _int(e.get("qpc")),
        _int(e.get("thread"), (1 << 32)-1), KindV1(_int(e.get("kind"), 10, 1)),
        _int(e.get("role"), 3), _int(e.get("invocation")),
        _int(e.get("identity_epoch")), _int(e.get("connection")), request_id,
        attributed, _bit(e.get("qualified")), _bit(e.get("desired_paused")),
        _token(e.get("token")), _token(e.get("parent")), _int(e.get("caller_rva")),
        _int(e.get("aux")), _int(e.get("native_sequence"), (1 << 32)-1),
        _int(e.get("player_bits"), (1 << 32)-1), _bit(e.get("command_paused")),
        _bit(e.get("payload_valid")), _bit(e.get("queue_accepted")), scalar)

def parse_journal_v1(frame: dict[str, object], *, request_id: str,
                     expected: ExpectedGameV1) -> JournalV1:
    if frame.get("type") != "command_result" or _int(frame.get("protocol_version"), 1, 1) != 1:
        raise ValueError("wrong command envelope")
    if frame.get("request_id") != request_id or frame.get("ok") is not True:
        raise ValueError("missing or rejected exact response")
    j = _obj(frame.get("result"))
    if (j.get("step") != STEP or j.get("observer_schema") != SCHEMA
        or j.get("status") != "passive_observation_only" or j.get("accepted") is not True
        or j.get("drain_fence") is not False
        or j.get("scalar_samples_are_snapshots") is not False
        or j.get("query_is_tail") is not True
        or j.get("lifetime_coverage") != "observed_clone_and_primary_delete_slots_only"
        or _int(j.get("attached"), 1) != 1 or _int(j.get("readable"), 1) != 1):
        raise ValueError("journal unavailable or observer contract differs")
    pid = _int(j.get("process_id"), (1 << 32)-1, 1)
    birth = _text(j.get("process_birth"), 20)
    if not birth.isdecimal() or birth != str(expected.creation_filetime) or pid != expected.pid:
        raise ValueError("exact Game PID/FILETIME differs")
    raw = j.get("events")
    if not isinstance(raw, list):
        raise ValueError("events are not an array")
    values = cast(list[object], raw)
    count = _int(j.get("returned_count"), 64)
    if len(values) != count:
        raise ValueError("journal count differs")
    events = tuple(_event(item) for item in values)
    newest = _int(j.get("newest"))
    oldest = _int(j.get("oldest_retained"), low=1)
    first = _int(j.get("first_returned"), low=1)
    if first != newest-count+1 or oldest > first or first > newest+1:
        raise ValueError("inconsistent tail bounds")
    if tuple(e.seq for e in events) != tuple(range(first, newest+1)):
        raise ValueError("journal sequence is not exact tail")
    return JournalV1(pid, birth, _int(j.get("qpc_frequency"), low=1),
        _int(j.get("snapshot_qpc")), _int(j.get("image_base"), low=1), newest,
        oldest, first, _int(j.get("coverage_gaps"), (1 << 32)-1),
        _int(j.get("lost")), _int(j.get("live_registry"), 64), events)

def execute_pairs_v1(journal: JournalV1, wanted: tuple[str, ...]) -> tuple[ExecutePairV1, ...]:
    wanted_set = frozenset(wanted)
    entries: dict[tuple[str, int, int, int, int, int, int], EventV1] = {}
    pairs: list[ExecutePairV1] = []
    for event in journal.events:
        if (not event.attributed or not event.qualified or not event.payload_valid
            or event.request_id not in wanted_set or not event.connection or not event.invocation
            or not event.token.pointer or not event.token.incarnation):
            continue
        key = (event.request_id, event.connection, event.identity_epoch,
            event.invocation, event.token.pointer, event.token.incarnation, event.role)
        if event.kind is KindV1.EXECUTE_ENTER:
            entries[key] = event
        elif event.kind is KindV1.EXECUTE_RETURN and key in entries:
            enter = entries.pop(key)
            if (event.seq <= enter.seq or event.native_sequence != enter.native_sequence
                or event.player_bits != enter.player_bits
                or event.command_paused != enter.command_paused
                or event.desired_paused != enter.desired_paused):
                continue
            seconds = ((event.qpc-enter.qpc)/journal.qpc_frequency
                if enter.qpc > 0 and event.qpc >= enter.qpc else None)
            pairs.append(ExecutePairV1(enter, event, seconds))
    return tuple(pairs)

def _connection(state: StateV1, expected: ExpectedGameV1) -> bool:
    info = state.diagnostics()
    hello = info.get("hello")
    if not isinstance(hello, dict):
        return False
    h = _obj(hello)
    try:
        return (info.get("connected") is True
            and _int(info.get("connection_generation"), low=1) == expected.connection_generation
            and _int(h.get("pid"), (1 << 32)-1, 1) == expected.pid
            and _int(h.get("connection_generation"), low=1) == expected.connection_generation)
    except ValueError:
        return False

def _query_once_v1(endpoint: EndpointV1, state: StateV1, *, expected: ExpectedGameV1,
                   request_id: str, wanted: tuple[str, ...], timeout_seconds: float) -> ReadResultV1:
    if (re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", request_id) is None
        or expected.native_dll_sha256 != NATIVE31_SHA256
        or endpoint.pipe_name != expected.pipe_name
        or not expected.machine_id or expected.pid <= 0
        or expected.creation_filetime <= 0 or expected.connection_generation <= 0
        or isinstance(timeout_seconds, bool) or not 0 < timeout_seconds <= 5):
        raise ValueError("invalid immutable Native31 read context")
    _int(expected.pid, (1 << 32)-1, 1)
    _int(expected.creation_filetime, low=1)
    _int(expected.connection_generation, low=1)
    if len(wanted) > 64 or any(re.fullmatch(r"[A-Za-z0-9_.:-]{1,63}", item) is None for item in wanted):
        raise ValueError("invalid bounded failed request ids")
    started = time.monotonic()
    if not _connection(state, expected):
        return ReadResultV1("unavailable", "connection differs", expected, request_id,
            0.0, None, (), None, 0)
    endpoint.send({"type":"execute_step", "protocol_version":1, "request_id":request_id,
        "step":STEP, "expected_revision":0})
    frame = state.wait_for_command_result(request_id, timeout_seconds)
    elapsed = time.monotonic()-started
    if frame is None:
        return ReadResultV1("unavailable", "exact result timed out; no retry", expected,
            request_id, elapsed, None, (), None, 1)
    saved = copy.deepcopy(frame)
    if not _connection(state, expected):
        return ReadResultV1("unavailable", "connection changed after read", expected,
            request_id, elapsed, None, (), saved, 1)
    try:
        journal = parse_journal_v1(frame, request_id=request_id, expected=expected)
    except ValueError as error:
        return ReadResultV1("unavailable", str(error), expected, request_id, elapsed,
            None, (), saved, 1)
    return ReadResultV1("positive_observations_only", None, expected, request_id,
        elapsed, journal, execute_pairs_v1(journal, wanted), saved, 1)

def read_from_source28_owner_once_v1(owner: object, driver: DriverV1, *,
        machine_id: str, request_id: str, failed_request_ids: tuple[str, ...] = (),
        timeout_seconds: float = 2.0) -> ReadResultV1:
    """Consume the issuer's actual cached DTO; never construct or mint one.

    Root must have completed the existing live cold custody/loaded-provider gate.
    This result grants no runtime admission or Game-action authority.
    """
    from xar_autoplayer.bridge import player_heir_candidate_component_v1 as component
    value: object = getattr(owner, "_player_heir_loaded_provider_v1", None)
    if not isinstance(value, component._LoadedNativeProviderV1):
        raise ValueError("actual canonical loaded-provider DTO required")
    if (value.seal is not component._LOADED_NATIVE_SEAL or value.owner is not owner
        or value.driver is not driver or value.machine_id != machine_id
        or value.native_dll_sha256 != NATIVE31_SHA256 or value.pipe_name != driver.pipe_name
        or getattr(owner, "driver", None) is not driver
        or getattr(owner, "machine", None) != machine_id):
        raise ValueError("actual owner/driver/Native31 provider binding differs")
    filetime = value.game_creation_filetime
    if not isinstance(filetime, int) or isinstance(filetime, bool) or filetime <= 0:
        raise ValueError("canonical FILETIME required; creation_date text is not FILETIME")
    expected = ExpectedGameV1(machine_id, value.game_pid, filetime,
        value.connection_generation, value.pipe_name, value.native_dll_sha256)
    result = _query_once_v1(driver.endpoint, driver.state, expected=expected,
        request_id=request_id, wanted=failed_request_ids, timeout_seconds=timeout_seconds)
    if getattr(owner, "_player_heir_loaded_provider_v1", None) is not value:
        raise ValueError("canonical provider changed during readonly observation")
    return result

def result_payload_v1(result: ReadResultV1) -> dict[str, object]:
    """Serialize integer identities as decimal text; retain the original JSON."""
    pairs: list[dict[str, object]] = []
    for pair in result.execute_pairs:
        enter, returned = pair.enter, pair.returned
        pairs.append({"native_recorded_request_id": enter.request_id,
            "observer_connection": str(enter.connection), "identity_epoch": str(enter.identity_epoch),
            "invocation": str(enter.invocation), "pointer": str(enter.token.pointer),
            "incarnation": str(enter.token.incarnation),
            "enter_seq": str(enter.seq), "return_seq": str(returned.seq),
            "enter_qpc": str(enter.qpc), "return_qpc": str(returned.qpc),
            "elapsed_seconds": pair.elapsed_seconds,
            "native_sequence": enter.native_sequence, "player_bits": enter.player_bits,
            "desired_paused": enter.desired_paused,
            "enter_scalar": {"valid": enter.scalar.valid, "paused": enter.scalar.paused,
                "date_bits": enter.scalar.date_bits},
            "return_scalar": {"valid": returned.scalar.valid, "paused": returned.scalar.paused,
                "date_bits": returned.scalar.date_bits}})
    journal = result.journal
    return {"schema": "xar.native31.readonly-journal-result/v1",
        "status": result.status, "reason": result.reason,
        "machine_id": result.expected.machine_id, "game_pid": result.expected.pid,
        "game_creation_filetime": str(result.expected.creation_filetime),
        "connection_generation": str(result.expected.connection_generation),
        "native_dll_sha256": result.expected.native_dll_sha256,
        "request_id": result.request_id, "elapsed_seconds": result.elapsed_seconds,
        "actual_native_requests": result.actual_native_requests,
        "credit_days": 0, "drain_fence": False, "automatic_recovery_allowed": False,
        "loaded_provider_issued": False, "absence_is_nonexecution_proof": False,
        "protocol_connection_binding_verified": False,
        "current_failed_request_completion_proven": False,
        "requested_id_matching": "recorded_text_only; not current protocol attribution",
        "coverage_gaps": journal.coverage_gaps if journal else None,
        "lost": str(journal.lost) if journal else None,
        "live_registry": journal.live_registry if journal else None,
        "native_observed_execute_pairs": pairs,
        "original_parsed_frame_json": (json.dumps(dict(result.original_parsed_frame),
            ensure_ascii=True, separators=(",", ":"), allow_nan=False)
            if result.original_parsed_frame is not None else None)}

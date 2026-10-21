"""Bounded diagnostic projections of already received Native31 clock cache."""
from __future__ import annotations
from typing import Callable, Literal, TypedDict, Protocol
from dataclasses import dataclass, field
import json

PhaseV1 = Literal["pre_resume", "wait_final", "pause_final", "cleanup_final"]
IssueV1 = Literal["missing", "null", "type", "range", "binding"]
SCHEMA = "xar.cached-native-clock-summary.v1"
MAX_BYTES = 8192
PHASES = ("pre_resume", "wait_final", "pause_final", "cleanup_final")
NumberReader = Callable[[object, str], str]


class UnavailableV1(TypedDict):
    status: Literal["unavailable"]
    field: str
    reason: IssueV1


class ObserverDataV1(TypedDict):
    started_ms: str
    completed_ms: str
    last_read_ms: str
    read_in_progress: bool
    last_read_available: bool
    snapshot_cached: bool


class ObserverAvailableV1(TypedDict):
    status: Literal["available"]
    value: ObserverDataV1


class MailboxDataV1(TypedDict):
    pump_epochs: str
    owner_verified_pump_epochs: str
    published_sequence: str
    completed_sequence: str
    executor_started_requests: str
    executor_started_sequence: str
    executor_started_pump_epoch: str
    executed_requests: str
    owner_tid: int
    current_tid: int
    failure: int
    stop: bool


class MailboxAvailableV1(TypedDict):
    status: Literal["available"]
    value: MailboxDataV1


class AvailableSampleV1(TypedDict):
    status: Literal["available"]
    phase: PhaseV1
    heartbeat_sequence: str
    heartbeat_monotonic_ms: str
    observer: ObserverAvailableV1 | UnavailableV1
    mailbox: MailboxAvailableV1 | UnavailableV1


class UnavailableSampleV1(UnavailableV1):
    phase: PhaseV1


SampleV1 = AvailableSampleV1 | UnavailableSampleV1


class CachedNativeClockSummaryV1(TypedDict):
    schema: Literal["xar.cached-native-clock-summary.v1"]
    bridge_pid: int | None
    connection_generation: int | None
    samples: list[SampleV1]
    not_on_wire: list[Literal["active_hook_calls", "state"]]
    cached_only: Literal[True]
    atomic_observation: Literal[False]
    native_event_time_verified: Literal[False]


class FieldErrorV1(ValueError):
    def __init__(self, field: str, reason: IssueV1) -> None:
        super().__init__(field + ":" + reason)
        self.field, self.reason = field, reason


def _get(source: object, key: str) -> object:
    if type(source) is not dict:
        raise FieldErrorV1(key, "type")
    if key not in source:
        raise FieldErrorV1(key, "missing")
    value: object = source[key]
    if value is None:
        raise FieldErrorV1(key, "null")
    return value


def _uint(source: object, key: str, maximum: int = (1 << 53) - 1) -> int:
    value = _get(source, key)
    if type(value) is not int:
        raise FieldErrorV1(key, "type")
    if not 0 <= value <= maximum:
        raise FieldErrorV1(key, "range")
    return value


def _boolean(source: object, key: str) -> bool:
    value = _get(source, key)
    if type(value) is not bool:
        raise FieldErrorV1(key, "type")
    return value


def _wire_decimal(source: object, key: str) -> str:
    return str(_uint(source, key))


def _json_decimal(source: object, key: str) -> str:
    value = _get(source, key)
    if type(value) is not str:
        raise FieldErrorV1(key, "type")
    if (not value or not value.isascii() or not value.isdecimal()
            or (len(value) > 1 and value[0] == "0") or len(value) > 20
            or int(value) >= 1 << 64):
        raise FieldErrorV1(key, "range")
    return value


def _observer(source: object, number: NumberReader) -> ObserverDataV1:
    return ObserverDataV1(
        started_ms=number(source, "started_ms"), completed_ms=number(source, "completed_ms"),
        last_read_ms=number(source, "last_read_ms"),
        read_in_progress=_boolean(source, "read_in_progress"),
        last_read_available=_boolean(source, "last_read_available"),
        snapshot_cached=_boolean(source, "snapshot_cached"))


def _mailbox(source: object, number: NumberReader) -> MailboxDataV1:
    return MailboxDataV1(
        pump_epochs=number(source, "pump_epochs"),
        owner_verified_pump_epochs=number(source, "owner_verified_pump_epochs"),
        published_sequence=number(source, "published_sequence"),
        completed_sequence=number(source, "completed_sequence"),
        executor_started_requests=number(source, "executor_started_requests"),
        executor_started_sequence=number(source, "executor_started_sequence"),
        executor_started_pump_epoch=number(source, "executor_started_pump_epoch"),
        executed_requests=number(source, "executed_requests"),
        owner_tid=_uint(source, "owner_tid", 0xffffffff),
        current_tid=_uint(source, "current_tid", 0xffffffff),
        failure=_uint(source, "failure", 0xffffffff), stop=_boolean(source, "stop"))


def _validated_scope(value: object) -> tuple[int, int] | None:
    if type(value) is not tuple or len(value) != 2:
        return None
    pid: object = value[0]
    generation: object = value[1]
    if (type(pid) is not int or not 0 < pid <= 0xffffffff
            or type(generation) is not int or not 0 < generation < 1 << 53):
        return None
    return pid, generation


def cache_scope_v1(snapshot: object) -> tuple[int, int] | None:
    try:
        diag = _get(snapshot, "diagnostics")
        pid, generation = _uint(diag, "bridge_pid", 0xffffffff), _uint(diag, "connection_generation")
        if not pid or not generation:
            return None
        return pid, generation
    except FieldErrorV1:
        return None


def capture_native_clock_cache_v1(
    diagnostics: object, scope: tuple[int, int] | None, phase: PhaseV1,
) -> SampleV1:
    if type(phase) is not str or phase not in PHASES:
        raise ValueError("invalid cached clock phase")
    scope = _validated_scope(scope)
    try:
        if scope is None:
            raise FieldErrorV1("scope", "missing")
        if (_uint(diagnostics, "bridge_pid", 0xffffffff) != scope[0]
                or _uint(diagnostics, "connection_generation") != scope[1]
                or not _boolean(diagnostics, "connected")):
            raise FieldErrorV1("scope", "binding")
        heartbeat = _get(diagnostics, "last_heartbeat")
        if (_get(heartbeat, "type") != "heartbeat" or _uint(heartbeat, "protocol_version") != 1
                or _uint(heartbeat, "pid", 0xffffffff) != scope[0]):
            raise FieldErrorV1("heartbeat", "binding")
        sequence = _wire_decimal(heartbeat, "sequence")
        monotonic = _wire_decimal(heartbeat, "monotonic_ms")
        observer: ObserverAvailableV1 | UnavailableV1
        mailbox: MailboxAvailableV1 | UnavailableV1
        try:
            observer = ObserverAvailableV1(status="available", value=_observer(
                _get(heartbeat, "snapshot_observer_12002"), _wire_decimal))
        except FieldErrorV1 as error:
            observer = UnavailableV1(status="unavailable", field=error.field, reason=error.reason)
        try:
            mailbox = MailboxAvailableV1(status="available", value=_mailbox(
                _get(heartbeat, "main_thread_query_mailbox_v1"), _wire_decimal))
        except FieldErrorV1 as error:
            mailbox = UnavailableV1(status="unavailable", field=error.field, reason=error.reason)
        return AvailableSampleV1(status="available", phase=phase, heartbeat_sequence=sequence,
            heartbeat_monotonic_ms=monotonic, observer=observer, mailbox=mailbox)
    except FieldErrorV1 as error:
        return UnavailableSampleV1(status="unavailable", phase=phase,
                                  field=error.field, reason=error.reason)


def build_cached_native_clock_summary_v1(
    scope: tuple[int, int] | None, samples: list[SampleV1],
) -> CachedNativeClockSummaryV1:
    scope = _validated_scope(scope)
    return CachedNativeClockSummaryV1(
        schema="xar.cached-native-clock-summary.v1",
        bridge_pid=None if scope is None else scope[0],
        connection_generation=None if scope is None else scope[1], samples=list(samples[:4]),
        not_on_wire=["active_hook_calls", "state"], cached_only=True,
        atomic_observation=False, native_event_time_verified=False)


def _keys(source: object, names: set[str]) -> None:
    if type(source) is not dict or set(source) != names:
        raise FieldErrorV1("fields", "type")


def _issue(value: object) -> IssueV1:
    if value == "missing": return "missing"
    if value == "null": return "null"
    if value == "type": return "type"
    if value == "range": return "range"
    if value == "binding": return "binding"
    raise FieldErrorV1("reason", "type")


def _phase(value: object) -> PhaseV1:
    if value == "pre_resume": return "pre_resume"
    if value == "wait_final": return "wait_final"
    if value == "pause_final": return "pause_final"
    if value == "cleanup_final": return "cleanup_final"
    raise FieldErrorV1("phase", "type")


def _unavailable(value: object, *, phased: bool = False) -> UnavailableV1:
    _keys(value, {"status", "field", "reason", "phase"} if phased else {"status", "field", "reason"})
    name = _get(value, "field")
    if _get(value, "status") != "unavailable" or type(name) is not str or len(name) > 128:
        raise FieldErrorV1("unavailable", "type")
    return UnavailableV1(status="unavailable", field=name, reason=_issue(_get(value, "reason")))


def parse_cached_native_clock_summary_v1(value: object) -> CachedNativeClockSummaryV1 | None:
    """Validate persisted JSON and reconstruct the shared internal field model."""
    try:
        _keys(value, set(CachedNativeClockSummaryV1.__annotations__))
        if (_get(value, "schema") != SCHEMA or not _boolean(value, "cached_only")
                or _boolean(value, "atomic_observation") or _boolean(value, "native_event_time_verified")):
            return None
        if _get(value, "not_on_wire") != ["active_hook_calls", "state"]:
            return None
        assert type(value) is dict
        pid_raw: object = value["bridge_pid"]
        generation_raw: object = value["connection_generation"]
        scope = None
        if pid_raw is not None or generation_raw is not None:
            scope = (_uint(value, "bridge_pid", 0xffffffff), _uint(value, "connection_generation"))
            if not scope[0] or not scope[1]:
                return None
        raw = _get(value, "samples")
        if type(raw) is not list or len(raw) > 4:
            return None
        samples: list[SampleV1] = []
        phases: list[PhaseV1] = []
        for item in raw:
            phase = _phase(_get(item, "phase"))
            if phase in phases:
                return None
            phases.append(phase)
            if _get(item, "status") == "unavailable":
                unavailable = _unavailable(item, phased=True)
                samples.append(UnavailableSampleV1(phase=phase, **unavailable))
                continue
            _keys(item, set(AvailableSampleV1.__annotations__))
            if _get(item, "status") != "available":
                return None
            observer_raw = _get(item, "observer")
            mailbox_raw = _get(item, "mailbox")
            observer: ObserverAvailableV1 | UnavailableV1
            mailbox: MailboxAvailableV1 | UnavailableV1
            if _get(observer_raw, "status") == "available":
                _keys(observer_raw, {"status", "value"})
                data = _get(observer_raw, "value")
                _keys(data, set(ObserverDataV1.__annotations__))
                observer = ObserverAvailableV1(status="available", value=_observer(data, _json_decimal))
            else:
                observer = _unavailable(observer_raw)
            if _get(mailbox_raw, "status") == "available":
                _keys(mailbox_raw, {"status", "value"})
                data = _get(mailbox_raw, "value")
                _keys(data, set(MailboxDataV1.__annotations__))
                mailbox = MailboxAvailableV1(status="available", value=_mailbox(data, _json_decimal))
            else:
                mailbox = _unavailable(mailbox_raw)
            samples.append(AvailableSampleV1(status="available", phase=phase,
                heartbeat_sequence=_json_decimal(item, "heartbeat_sequence"),
                heartbeat_monotonic_ms=_json_decimal(item, "heartbeat_monotonic_ms"),
                observer=observer, mailbox=mailbox))
        result = build_cached_native_clock_summary_v1(scope, samples)
        if len(json.dumps(result, separators=(",", ":"), allow_nan=False).encode()) > MAX_BYTES:
            return None
        return result
    except (FieldErrorV1, KeyError, TypeError, ValueError):
        return None


class CachedDiagnosticStateV1(Protocol):
    def diagnostics(self) -> dict[str, object]: ...


@dataclass(slots=True)
class CachedNativeClockCollectorV1:
    scope: tuple[int, int] | None
    samples: list[SampleV1] = field(default_factory=list)

    @classmethod
    def from_snapshot(cls, snapshot: object) -> CachedNativeClockCollectorV1:
        result = cls(cache_scope_v1(snapshot))
        try:
            result.capture("pre_resume", _get(snapshot, "diagnostics"))
        except FieldErrorV1:
            result.capture("pre_resume", None)
        return result

    def capture(self, phase: PhaseV1, diagnostics: object) -> None:
        sample = capture_native_clock_cache_v1(diagnostics, self.scope, phase)
        self.samples = [row for row in self.samples if row["phase"] != phase]
        self.samples.append(sample)

    def capture_current(self, phase: PhaseV1, state: CachedDiagnosticStateV1) -> None:
        try:
            self.capture(phase, state.diagnostics())
        except Exception:
            pass

    def summary(self) -> CachedNativeClockSummaryV1:
        return build_cached_native_clock_summary_v1(self.scope, self.samples)

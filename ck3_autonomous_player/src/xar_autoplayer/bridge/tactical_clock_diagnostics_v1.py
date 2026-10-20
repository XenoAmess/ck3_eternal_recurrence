"""Typed projections of existing clock evidence; no game queries or decisions."""
from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Literal, Protocol, TypedDict

from .clock_observation_timing_v1 import (
    ClockObservationV1, start_clock_observation_v1, finish_clock_observation_v1,
)
from .exact_clock_wait_progress_v1 import (
    WaitProgressV1, start_wait_progress_v1, finish_wait_progress_v1,
    project_wait_progress_v1, COLUMNS, BUCKET_COLUMNS, METRICS,
)
from .driver import StepPostconditionError
from .route_contact_window_contract import parse_advance_route_contact_window_step

SCHEMA: Literal["xar.tactical-clock-failure.v1"] = "xar.tactical-clock-failure.v1"
MAX_BYTES = 16384


class FullWaitProgressV1(TypedDict):
    schema: Literal["xar.exact-clock-wait-progress.v1"]
    arm_generation: int
    identity: list[int | str] | None
    flags: int
    heartbeats: int
    candidates: int
    elapsed_ms: int | None
    max_heartbeat_gap_ms: int
    candidate_first: list[int | bool | None] | None
    candidate_last: list[int | bool | None] | None
    columns: list[str]
    metrics: dict[str, list[int | None]]
    bucket_ms: Literal[5000]
    bucket_columns: list[str]
    buckets: list[list[int]]
    overflow: int
    seed_from_cached_snapshot: Literal[True]
    empty_bucket_means_unobserved: Literal[True]
    native_event_time_verified: Literal[False]
    source_heartbeat_ms: list[int | None]


class LimitExceededWaitProgressV1(TypedDict):
    schema: Literal["xar.exact-clock-wait-progress.v1"]
    limit_exceeded: Literal[True]
    native_event_time_verified: Literal[False]


WaitProgressSummaryV1 = FullWaitProgressV1 | LimitExceededWaitProgressV1


class ClockDiagnosticOwnerV1(Protocol):
    _exact_clock_wait_progress_v1: WaitProgressV1 | None
    _exact_clock_observation_v1: ClockObservationV1 | None


@dataclass(slots=True)
class TacticalClockObservationV1:
    progress: WaitProgressV1 | None = None
    clock: ClockObservationV1 | None = None
    summary: WaitProgressSummaryV1 | None = None

    def start(self, driver: ClockDiagnosticOwnerV1,
              snapshot: dict[str, object], generation: object) -> None:
        try:
            value = start_wait_progress_v1(driver, snapshot, generation)
            self.progress = value if isinstance(value, WaitProgressV1) else None
        except Exception:
            pass
        try:
            value = start_clock_observation_v1(driver, snapshot)
            self.clock = value if isinstance(value, ClockObservationV1) else None
        except Exception:
            pass

    def finish(self, driver: ClockDiagnosticOwnerV1,
               snapshot: dict[str, object]) -> None:
        # Outside the transport Condition. Detach before freeze or I/O.
        if self.progress is not None and driver._exact_clock_wait_progress_v1 is self.progress:
            driver._exact_clock_wait_progress_v1 = None
        if self.clock is not None and driver._exact_clock_observation_v1 is self.clock:
            driver._exact_clock_observation_v1 = None
        try:
            value: object = finish_wait_progress_v1(driver, self.progress, snapshot)
            self.summary = project_tactical_wait_progress_v1(value)
        except Exception:
            pass
        finally:
            try:
                finish_clock_observation_v1(driver, self.clock, snapshot)
            except Exception:
                pass


class SentinelStatusProjectionV1(TypedDict):
    state: str | None
    generation: int | None
    starting_date_raw: int | None
    target_date_raw: int | None
    last_observed_date_raw: int | None
    trigger_date_raw: int | None
    speed: int | None
    mode: str | None
    army_count: int | None
    combat_count: int | None
    completed_daily_ticks: int | None
    intermediate_pause_count: int | None
    trigger_flags: int | None
    signed_date_delta_from_target_raw: int | None
    overshoot_days: int | None
    pause_wrapper_called: bool | None
    pause_observed: bool | None
    terminal_observed: bool | None
    abnormal: bool | None


class NativeAckProjectionV1(TypedDict):
    step: str | None
    accepted: bool | None
    status: str | None
    request_id: int | str | None
    native_request_id: int | str | None


class TacticalActionProjectionV1(TypedDict):
    step: str | None
    purpose: str | None
    error: str | None
    result_observed: bool
    result: NativeAckProjectionV1


class CleanupProjectionV1(TypedDict):
    attempted: bool | None
    error: str | None


class CancelProjectionV1(TypedDict):
    step: str | None
    status: str | None
    generation: int | None


class TacticalStepFailureProjectionV1(TypedDict):
    step: str
    source: Literal["native-tactical-daily-sentinel-composite"]
    sentinel_scope: Literal["route_contact_window"]
    progress_status: Literal["postcondition_failed"]
    backend_id: str | None
    starting_date_raw: int | None
    target_date_raw: int | None
    ending_date_raw: int | None
    elapsed_days: int | None
    requested_horizon_days: int | None
    timeline_speed: int | None
    timeline_policy: str | None
    sentinel_mode: str | None
    sentinel_generation: int | None
    completed_daily_ticks: int | None
    intermediate_pause_count: int | None
    overshoot_days: int | None
    paused: bool | None
    snapshot_id: str | None
    revision: int | None
    native_revision: int | None
    bridge_pid: int | None
    connection_generation: int | None
    episode_character_id: int | None
    episode_run_id: str | None
    played_character_id: int | None
    played_character_alive: bool | None
    external_pause_count: int | None
    player_decision_boundary_pause_count: int | None
    armed_tactical_daily_sentinel: SentinelStatusProjectionV1 | None
    tactical_daily_sentinel: SentinelStatusProjectionV1 | None
    managed_failure_cleanup: CleanupProjectionV1 | None
    player_decision_boundary_cancel: CancelProjectionV1 | None
    watch_army_ids: list[int] | None
    actions: list[TacticalActionProjectionV1]
    actions_omitted_count: int | None


class TacticalClockFailureV1(TypedDict):
    schema: Literal["xar.tactical-clock-failure.v1"]
    is_error: Literal[True]
    never_replay: Literal[True]
    credit: Literal[0]
    selected_step: str
    primitive_step: str
    step_result: TacticalStepFailureProjectionV1
    wait_progress: WaitProgressSummaryV1 | None
    truncated: bool


def _get(source: object, key: str) -> object:
    if type(source) is dict:
        value: object = source.get(key)
        return value
    return None


def _integer(value: object) -> int | None:
    return value if type(value) is int and -(1 << 63) <= value < (1 << 64) else None


def _boolean(value: object) -> bool | None:
    return value if type(value) is bool else None


def _text(value: object) -> str | None:
    return value if type(value) is str and len(value) <= 1024 else None


def _request_id(value: object) -> int | str | None:
    if type(value) is str:
        return _text(value)
    return _integer(value)


def _require_uint(value: object) -> int:
    if type(value) is not int or not 0 <= value < (1 << 64):
        raise ValueError("unsigned clock scalar required")
    return value


def _optional_uint(value: object) -> int | None:
    return None if value is None else _require_uint(value)


def _optional_uints(value: object) -> list[int | None]:
    if type(value) is not list:
        raise ValueError("clock scalar row required")
    return [_optional_uint(item) for item in value]


def _candidate(value: object) -> list[int | bool | None] | None:
    if value is None:
        return None
    if type(value) is not list or len(value) != 4:
        raise ValueError("clock candidate required")
    paused: object = value[3]
    if paused is not None and type(paused) is not bool:
        raise ValueError("nullable paused scalar required")
    return [_optional_uint(value[0]), _optional_uint(value[1]),
            _optional_uint(value[2]), _boolean(paused)]


def project_tactical_wait_progress_v1(value: object) -> WaitProgressSummaryV1 | None:
    """Reuse the exact bounded validator before constructing the typed DTO."""
    try:
        projected: object = project_wait_progress_v1(value)
        if projected is None:
            return None
        if _get(projected, "limit_exceeded") is True:
            return LimitExceededWaitProgressV1(
                schema="xar.exact-clock-wait-progress.v1",
                limit_exceeded=True, native_event_time_verified=False)
        identity_value = _get(projected, "identity")
        identity: list[int | str] | None = None
        if identity_value is not None:
            if type(identity_value) is not list or len(identity_value) != 4:
                return None
            episode = _text(identity_value[3])
            if episode is None:
                return None
            identity = [_require_uint(identity_value[0]), _require_uint(identity_value[1]),
                        _require_uint(identity_value[2]), episode]
        buckets_value = _get(projected, "buckets")
        if type(buckets_value) is not list:
            return None
        buckets: list[list[int]] = []
        for row in buckets_value:
            if type(row) is not list:
                return None
            buckets.append([_require_uint(item) for item in row])
        return FullWaitProgressV1(
            schema="xar.exact-clock-wait-progress.v1",
            arm_generation=_require_uint(_get(projected, "arm_generation")),
            identity=identity, flags=_require_uint(_get(projected, "flags")),
            heartbeats=_require_uint(_get(projected, "heartbeats")),
            candidates=_require_uint(_get(projected, "candidates")),
            elapsed_ms=_optional_uint(_get(projected, "elapsed_ms")),
            max_heartbeat_gap_ms=_require_uint(_get(projected, "max_heartbeat_gap_ms")),
            candidate_first=_candidate(_get(projected, "candidate_first")),
            candidate_last=_candidate(_get(projected, "candidate_last")),
            columns=list(COLUMNS),
            metrics={name: _optional_uints(_get(_get(projected, "metrics"), name))
                     for name in METRICS},
            bucket_ms=5000, bucket_columns=list(BUCKET_COLUMNS), buckets=buckets,
            overflow=_require_uint(_get(projected, "overflow")),
            seed_from_cached_snapshot=True, empty_bucket_means_unobserved=True,
            native_event_time_verified=False,
            source_heartbeat_ms=_optional_uints(_get(projected, "source_heartbeat_ms")),
        )
    except Exception:
        return None


def _sentinel(source: object) -> SentinelStatusProjectionV1 | None:
    if type(source) is not dict:
        return None
    return SentinelStatusProjectionV1(
        state=_text(_get(source, "state")), generation=_integer(_get(source, "generation")),
        starting_date_raw=_integer(_get(source, "starting_date_raw")),
        target_date_raw=_integer(_get(source, "target_date_raw")),
        last_observed_date_raw=_integer(_get(source, "last_observed_date_raw")),
        trigger_date_raw=_integer(_get(source, "trigger_date_raw")),
        speed=_integer(_get(source, "speed")), mode=_text(_get(source, "mode")),
        army_count=_integer(_get(source, "army_count")),
        combat_count=_integer(_get(source, "combat_count")),
        completed_daily_ticks=_integer(_get(source, "completed_daily_ticks")),
        intermediate_pause_count=_integer(_get(source, "intermediate_pause_count")),
        trigger_flags=_integer(_get(source, "trigger_flags")),
        signed_date_delta_from_target_raw=_integer(_get(source, "signed_date_delta_from_target_raw")),
        overshoot_days=_integer(_get(source, "overshoot_days")),
        pause_wrapper_called=_boolean(_get(source, "pause_wrapper_called")),
        pause_observed=_boolean(_get(source, "pause_observed")),
        terminal_observed=_boolean(_get(source, "terminal_observed")),
        abnormal=_boolean(_get(source, "abnormal")),
    )


def _action(source: object) -> TacticalActionProjectionV1:
    ack = _get(source, "result")
    return TacticalActionProjectionV1(
        step=_text(_get(source, "step")), purpose=_text(_get(source, "purpose")),
        error=_text(_get(source, "error")), result_observed=type(ack) is dict,
        result=NativeAckProjectionV1(
            step=_text(_get(ack, "step")), accepted=_boolean(_get(ack, "accepted")),
            status=_text(_get(ack, "status")),
            request_id=_request_id(_get(ack, "request_id")),
            native_request_id=_request_id(_get(ack, "native_request_id")),
        ),
    )


def build_tactical_clock_failure_v1(
    selected_step: str, primitive_step: str, result: dict[str, object],
    wait_progress: object,
) -> TacticalClockFailureV1 | None:
    """Arm is the earlier reply; a null stopped STATUS remains unobserved."""
    if (type(selected_step) is not str or len(selected_step) > 1024
            or parse_advance_route_contact_window_step(primitive_step) is None
            or result.get("step") != primitive_step
            or result.get("source") != "native-tactical-daily-sentinel-composite"
            or result.get("sentinel_scope") != "route_contact_window"
            or result.get("progress_status") != "postcondition_failed"):
        return None
    armies_value = result.get("watch_army_ids")
    armies: list[int] | None = None
    if type(armies_value) is list and len(armies_value) <= 32:
        candidate = [_integer(item) for item in armies_value]
        if all(item is not None for item in candidate):
            armies = [item for item in candidate if item is not None]
    actions_value = result.get("actions")
    actions: list[TacticalActionProjectionV1] = []
    omitted: int | None = None
    if type(actions_value) is list:
        actions = [_action(item) for item in actions_value[:12]]
        omitted = len(actions_value) - len(actions)
    cleanup_value = result.get("managed_failure_cleanup")
    cleanup = None if type(cleanup_value) is not dict else CleanupProjectionV1(
        attempted=_boolean(_get(cleanup_value, "attempted")),
        error=_text(_get(cleanup_value, "error")))
    cancel_value = result.get("player_decision_boundary_cancel")
    cancel = None if type(cancel_value) is not dict else CancelProjectionV1(
        step=_text(_get(cancel_value, "step")), status=_text(_get(cancel_value, "status")),
        generation=_integer(_get(cancel_value, "generation")))
    projected = TacticalStepFailureProjectionV1(
        step=primitive_step, source="native-tactical-daily-sentinel-composite",
        sentinel_scope="route_contact_window", progress_status="postcondition_failed",
        backend_id=_text(result.get("backend_id")),
        starting_date_raw=_integer(result.get("starting_date_raw")),
        target_date_raw=_integer(result.get("target_date_raw")),
        ending_date_raw=_integer(result.get("ending_date_raw")),
        elapsed_days=_integer(result.get("elapsed_days")),
        requested_horizon_days=_integer(result.get("requested_horizon_days")),
        timeline_speed=_integer(result.get("timeline_speed")),
        timeline_policy=_text(result.get("timeline_policy")), sentinel_mode=_text(result.get("sentinel_mode")),
        sentinel_generation=_integer(result.get("sentinel_generation")),
        completed_daily_ticks=_integer(result.get("completed_daily_ticks")),
        intermediate_pause_count=_integer(result.get("intermediate_pause_count")),
        overshoot_days=_integer(result.get("overshoot_days")), paused=_boolean(result.get("paused")),
        snapshot_id=_text(result.get("snapshot_id")), revision=_integer(result.get("revision")),
        native_revision=_integer(result.get("native_revision")), bridge_pid=_integer(result.get("bridge_pid")),
        connection_generation=_integer(result.get("connection_generation")),
        episode_character_id=_integer(result.get("episode_character_id")),
        episode_run_id=_text(result.get("episode_run_id")),
        played_character_id=_integer(result.get("played_character_id")),
        played_character_alive=_boolean(result.get("played_character_alive")),
        external_pause_count=_integer(result.get("external_pause_count")),
        player_decision_boundary_pause_count=_integer(result.get("player_decision_boundary_pause_count")),
        armed_tactical_daily_sentinel=_sentinel(result.get("armed_tactical_daily_sentinel")),
        tactical_daily_sentinel=_sentinel(result.get("tactical_daily_sentinel")),
        managed_failure_cleanup=cleanup, player_decision_boundary_cancel=cancel,
        watch_army_ids=armies, actions=actions, actions_omitted_count=omitted,
    )
    diagnostic = TacticalClockFailureV1(
        schema=SCHEMA, is_error=True, never_replay=True, credit=0,
        selected_step=selected_step, primitive_step=primitive_step, step_result=projected,
        wait_progress=project_tactical_wait_progress_v1(wait_progress),
        truncated=armies is None or omitted is None or omitted > 0,
    )
    encoded = json.dumps(diagnostic, ensure_ascii=True, allow_nan=False,
                         separators=(",", ":"))
    return diagnostic if len(encoded.encode("utf-8")) <= MAX_BYTES else None


def tactical_clock_failure_v1(error: BaseException) -> TacticalClockFailureV1 | None:
    if not isinstance(error, StepPostconditionError):
        return None
    try:
        return build_tactical_clock_failure_v1(
            error.selected_step, error.primitive_step, error.step_result,
            error.step_result.get("tactical_clock_wait_progress_v1"),
        )
    except Exception:
        return None

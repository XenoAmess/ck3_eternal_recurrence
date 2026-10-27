"""Existing execute-step transport for the new G2 read-only native queries."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import math
import re
import time
from typing import Literal, Protocol, TypedDict, runtime_checkable
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import _binding
from .nonwar_private_build import private_native_build_identity


@runtime_checkable
class _QueryEndpoint(Protocol):
    def send(self, request: dict[str, object]) -> None: ...


@runtime_checkable
class _QueryState(Protocol):
    def wait_for_command_result(self, request_id: str, timeout_seconds: float) -> object: ...


@runtime_checkable
class _SnapshotDriver(Protocol):
    @property
    def endpoint(self) -> object: ...
    @property
    def state(self) -> object: ...
    def take_snapshot(self) -> dict[str, object]: ...


@runtime_checkable
class _PublicationWaiter(Protocol):
    def wait_for_change(self, after_revision: int, *, timeout_seconds: float) -> dict[str, object]: ...


class FrameChangedResponse(TypedDict):
    type: Literal["command_result"]
    protocol_version: Literal[1]
    request_id: str
    ok: Literal[False]
    error: Literal["player_religion_published_frame_changed"]


class ReadConsistencyReacquisition(TypedDict):
    schema: Literal["ck3-readonly-native-frame-reacquisition-v1"]
    original_expected_revision: int
    initial_snapshot_id: str
    initial_native_revision: int
    failed_request_id: str
    failed_response: FrameChangedResponse
    reacquired_snapshot_id: str
    reacquired_queried_revision: int
    reacquired_queried_native_revision: int
    reissued_request_id: str
    readonly_reissue_count: Literal[1]


@dataclass(frozen=True)
class _NativeRead:
    before: dict[str, object]
    result: dict[str, object]
    request_id: str


class _ReligionReadFrameChanged(BridgeUnavailableError):
    def __init__(self, before: dict[str, object], response: FrameChangedResponse) -> None:
        super().__init__(
            "private native observation returned RED: query-player-religion-context-v1; "
            f"request_id={response['request_id']}; native_revision={before.get('native_revision')}; "
            "error=player_religion_published_frame_changed")
        self.before = before
        self.response = response


def _positive_frame_integer(value: object, field: str) -> int:
    if type(value) is not int or value <= 0:
        raise BridgeUnavailableError("read-only reacquisition requires exact positive " + field)
    return value


def _frame_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise BridgeUnavailableError("read-only reacquisition requires actual " + field)
    return value


def _reacquisition_identity(snapshot: Mapping[str, object]) -> tuple[int, int, str, str, int, int, str]:
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    actor = snapshot.get("played_character")
    if (not isinstance(hello, Mapping) or not isinstance(actor, Mapping)
            or actor.get("alive") is not True or snapshot.get("paused") is not True
            or snapshot.get("map_ready") is not True):
        raise BridgeUnavailableError("read-only reacquisition lost its living paused native frame")
    build = private_native_build_identity(snapshot)
    run = snapshot.get("managed_campaign_run_binding")
    run_fields = {"run_id", "state_dir", "bridge_pipe", "host_path", "frozen_argv_sha256"}
    if not isinstance(run, Mapping) or set(run) != run_fields:
        raise BridgeUnavailableError("read-only reacquisition requires the actual managed run binding")
    for field in run_fields:
        _frame_string(run.get(field), "managed run " + field)
    frozen_sha = _frame_string(run.get("frozen_argv_sha256"), "managed frozen argv SHA")
    if re.fullmatch(r"[0-9a-f]{64}", frozen_sha) is None:
        raise BridgeUnavailableError("read-only reacquisition lost its frozen argv identity")
    boundaries: dict[str, object] = {"managed_campaign_run_binding": dict(run)}
    for field in ("active_event", "pending_character_interaction", "episode_projection", "one_life_terminal_reason", "local_player_id"):
        # Missing and explicit null remain distinct across reacquisition.
        value = snapshot.get(field)
        if field in ("active_event", "pending_character_interaction"):
            if field not in snapshot or (value is not None and not isinstance(value, Mapping)):
                raise BridgeUnavailableError("read-only reacquisition lost its event/pending boundary")
        boundaries[field] = {"present": field in snapshot, "value": value}
    try:
        boundary_json = json.dumps(boundaries, sort_keys=True, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise BridgeUnavailableError("read-only reacquisition boundary is not JSON") from error
    return (
        _positive_frame_integer(hello.get("pid"), "game PID"),
        _positive_frame_integer(hello.get("connection_generation"), "connection generation"),
        build.game_version, build.executable_sha256,
        _positive_frame_integer(actor.get("character_id"), "played character ID"),
        _positive_frame_integer(snapshot.get("date_raw"), "date"), boundary_json,
    )


def private_g2_query_snapshot_v1(
    driver: object, *, include_native_command_history: bool = True,
) -> dict[str, object]:
    """Read the semantic frame, optionally omitting an unused history export."""
    if include_native_command_history is False:
        finite_reader = getattr(driver, "take_snapshot_without_native_command_history", None)
        if callable(finite_reader):
            finite: object = finite_reader()
            if not isinstance(finite, dict) or any(not isinstance(key, str) for key in finite):
                raise BridgeUnavailableError("native finite observation snapshot is malformed")
            return {key: value for key, value in finite.items() if isinstance(key, str)}
    if not isinstance(driver, _SnapshotDriver):
        raise BridgeUnavailableError("native observation driver contract is unavailable")
    return driver.take_snapshot()


def _read_private_g2_native_query_v1(
    driver: object, *, permission: str, step: str, expected_revision: int,
    request_fields: Mapping[str, object] | None = None,
    timeout_seconds: float = 30.0,
    include_native_command_history: bool = True,
) -> _NativeRead:
    """Use the existing endpoint and frame binding; no gameplay action is sent."""
    if getattr(driver, permission, False) is not True:
        raise UnsupportedStepError(f"private native observation is disabled: {step}")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0):
        raise ValueError("timeout_seconds must be positive")
    if not isinstance(driver, _SnapshotDriver):
        raise BridgeUnavailableError("native observation driver contract is unavailable")
    endpoint, state = driver.endpoint, driver.state
    if not isinstance(endpoint, _QueryEndpoint) or not isinstance(state, _QueryState):
        raise BridgeUnavailableError("native observation transport contract is unavailable")
    before = private_g2_query_snapshot_v1(
        driver, include_native_command_history=include_native_command_history)
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision or before.get("paused") is not True
            or before.get("map_ready") is not True or not isinstance(actor, Mapping)
            or actor.get("alive") is not True or type(native_revision) is not int or native_revision <= 0):
        raise BridgeUnavailableError("private native observation requires a living paused player")
    request_id = "g2-read-" + uuid.uuid4().hex
    endpoint.send({
        **dict(request_fields or {}), "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
        "expected_snapshot_revision": native_revision,
    })
    frame = state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, Mapping) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id
            or frame.get("ok") is not True):
        if (step == "query-player-religion-context-v1" and request_fields is None
                and isinstance(frame, Mapping)
                and set(frame) == {"type", "protocol_version", "request_id", "ok", "error"}
                and frame.get("type") == "command_result"
                and type(frame.get("protocol_version")) is int and frame["protocol_version"] == 1
                and frame.get("request_id") == request_id and frame.get("ok") is False
                and frame.get("error") == "player_religion_published_frame_changed"):
            response: FrameChangedResponse = {
                "type": "command_result", "protocol_version": 1, "request_id": request_id,
                "ok": False, "error": "player_religion_published_frame_changed",
            }
            raise _ReligionReadFrameChanged(before, response)
        if isinstance(frame, Mapping):
            native_summary = "; ".join(
                f"{key}={str(frame[key])[:600]}"
                for key in (
                    "type", "protocol_version", "request_id", "ok",
                    "error", "reason", "status", "execution_code", "result",
                    "source_snapshot_id", "source_revision",
                    "source_connection_generation",
                )
                if key in frame
            )
        else:
            native_summary = f"frame={repr(frame)[:200]}"
        raise BridgeUnavailableError(
            f"private native observation returned RED: {step}; "
            f"request_id={request_id}; native_revision={native_revision}; "
            f"{native_summary or 'native command result has no failure details'}"
        )
    result = frame.get("result")
    if (not isinstance(result, dict) or result.get("step") != step
            or result.get("accepted") is not True or result.get("private_build") is not True
            or result.get("read_only") is not True or result.get("advertised") is not False):
        raise BridgeUnavailableError(f"private native observation envelope is malformed: {step}")
    after = private_g2_query_snapshot_v1(
        driver, include_native_command_history=include_native_command_history)
    if _binding(after) != _binding(before):
        raise BridgeUnavailableError(f"private native observation crossed its paused frame: {step}")
    return _NativeRead(before, result, request_id)


def read_private_g2_native_query_v1(
    driver: object, *, permission: str, step: str, expected_revision: int,
    request_fields: Mapping[str, object] | None = None,
    timeout_seconds: float = 30.0,
    include_native_command_history: bool = True,
) -> tuple[dict[str, object], dict[str, object]]:
    observed = _read_private_g2_native_query_v1(
        driver, permission=permission, step=step, expected_revision=expected_revision,
        request_fields=request_fields, timeout_seconds=timeout_seconds,
        include_native_command_history=include_native_command_history)
    return observed.before, observed.result


def read_player_religion_query_consistent_v1(
    driver: object, *, permission: str, expected_revision: int, timeout_seconds: float,
) -> tuple[dict[str, object], dict[str, object], ReadConsistencyReacquisition | None]:
    """Reacquire once after the exact rejected read, never replay an action.

    expected_revision admits the first read. After an explicit rejected frame,
    the result identifies the newer actual frame and carries both read IDs.
    """
    if permission != "allow_private_player_religion_context_query":
        raise ValueError("read-only reacquisition is limited to player religion context")
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0):
        raise ValueError("timeout_seconds must be finite and positive")
    deadline = time.monotonic() + timeout_seconds
    try:
        observed = _read_private_g2_native_query_v1(
            driver, permission=permission, step="query-player-religion-context-v1",
            expected_revision=expected_revision, timeout_seconds=timeout_seconds)
        return observed.before, observed.result, None
    except _ReligionReadFrameChanged as failed:
        initial = failed.before
        identity = _reacquisition_identity(initial)
        initial_public = _positive_frame_integer(initial.get("revision"), "public revision")
        initial_native = _positive_frame_integer(initial.get("native_revision"), "native revision")
        initial_id = _frame_string(initial.get("snapshot_id"), "snapshot ID")
        if not isinstance(driver, _PublicationWaiter):
            raise BridgeUnavailableError("read-only reacquisition publication waiter is unavailable") from failed
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeUnavailableError("read-only reacquisition original deadline expired") from failed
        current = driver.wait_for_change(initial_public, timeout_seconds=remaining)
        public = _positive_frame_integer(current.get("revision"), "new public revision")
        native = _positive_frame_integer(current.get("native_revision"), "new native revision")
        if public <= initial_public or native <= initial_native:
            raise BridgeUnavailableError("read-only reacquisition requires a newer native publication") from failed
        if _reacquisition_identity(current) != identity:
            raise BridgeUnavailableError("read-only reacquisition crossed native identity/date/event boundary") from failed
        current_id = _frame_string(current.get("snapshot_id"), "new snapshot ID")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeUnavailableError("read-only reacquisition original deadline expired") from failed
        # This second read is independent and still uses every original frame
        # guard. A second RED escapes; there is no loop or action submission.
        observed = _read_private_g2_native_query_v1(
            driver, permission=permission, step="query-player-religion-context-v1",
            expected_revision=public, timeout_seconds=remaining)
        if (time.monotonic() > deadline or _reacquisition_identity(observed.before) != identity
                or observed.before.get("revision") != public or observed.before.get("native_revision") != native
                or observed.before.get("snapshot_id") != current_id):
            raise BridgeUnavailableError("read-only reacquisition final deadline/identity changed")
        trace: ReadConsistencyReacquisition = {
            "schema": "ck3-readonly-native-frame-reacquisition-v1",
            "original_expected_revision": expected_revision, "initial_snapshot_id": initial_id,
            "initial_native_revision": initial_native,
            "failed_request_id": failed.response["request_id"], "failed_response": failed.response,
            "reacquired_snapshot_id": _frame_string(observed.before.get("snapshot_id"), "new snapshot ID"),
            "reacquired_queried_revision": public, "reacquired_queried_native_revision": native,
            "reissued_request_id": observed.request_id, "readonly_reissue_count": 1,
        }
        return observed.before, observed.result, trace


def private_g2_query_metadata_v1(snapshot: Mapping[str, object]) -> dict[str, object]:
    return {"queried_snapshot_id": snapshot.get("snapshot_id"),
            "queried_revision": snapshot.get("revision"),
            "queried_native_revision": snapshot.get("native_revision")}

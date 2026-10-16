"""One fixed popup request, actual TOP binding, and an owner-scoped close latch."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .prewar_force_coalition_transport import _frame_binding
from .war_results_window_contract import (
    ATTEMPT_SCHEMA, CLOSE_CAPABILITY, CLOSE_STEP, LEASE_KEYS, QUERY_CAPABILITY, QUERY_STEP,
    OWNER_RECEIPT_KEY, SOURCE_SCHEMA, _integer, normalize_war_results_window_v1,
    normalize_war_results_window_owner_receipt_v1,
)


def _generation(snapshot: Mapping[str, object]) -> int:
    diagnostics = snapshot.get("diagnostics")
    hello = diagnostics.get("hello") if isinstance(diagnostics, Mapping) else None
    if not isinstance(hello, Mapping):
        raise ValueError("war results lacks its current actual Native hello")
    return _integer(hello.get("connection_generation"), "hello.connection_generation", 1, (1 << 64) - 1)


def _lease(binding: Mapping[str, object]) -> dict[str, object]:
    return {key: binding[value] for key, value in LEASE_KEYS.items()}


def _top(frame: object, request_id: str) -> tuple[dict[str, object], Mapping[str, object]]:
    if not isinstance(frame, Mapping):
        raise BridgeUnavailableError("war results command_result is missing")
    if (frame.get("type") != "command_result" or type(frame.get("protocol_version")) is not int
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("war results actual TOP request binding differs")
    if frame.get("ok") is False:
        if set(frame) != {"type", "protocol_version", "request_id", "ok", "error"} or type(frame.get("error")) is not str:
            raise BridgeUnavailableError("war results refusal shape is malformed")
        raise BridgeUnavailableError(f"Native war results refused: {frame['error']}")
    if frame.get("ok") is not True or set(frame) != {"type", "protocol_version", "request_id", "ok", "result", OWNER_RECEIPT_KEY}:
        raise BridgeUnavailableError("war results command_result success shape is malformed")
    try:
        receipt = normalize_war_results_window_owner_receipt_v1(frame[OWNER_RECEIPT_KEY], request_id=request_id)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {**{key: frame[key] for key in ("type", "protocol_version", "request_id", "ok")}, OWNER_RECEIPT_KEY: receipt}, frame["result"]


def _result(frame: object, request_id: str, operation: str, binding: Mapping[str, object], generation: int) -> dict[str, object]:
    top, leaf = _top(frame, request_id)
    try:
        normalized = normalize_war_results_window_v1(
            leaf, operation=operation, binding=binding, native_generation=generation,
            owner_receipt=top[OWNER_RECEIPT_KEY],
        )
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    return {
        **normalized, "step": QUERY_STEP if operation == "query" else CLOSE_STEP,
        "backend_id": "native-headless", "sdk_validation_schema": SOURCE_SCHEMA,
        "native_request_id": request_id, "native_command_result": top, **_lease(binding),
    }


def _war_signature(snapshot: Mapping[str, object]) -> tuple[int, ...] | None:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return None
    ids = [war.get("war_id") for war in wars if isinstance(war, Mapping)]
    if len(ids) != len(wars) or any(type(war_id) is not int or war_id <= 0 for war_id in ids):
        return None
    return tuple(sorted(ids))


def _publish(driver: object, result: Mapping[str, object], token: int,
             snapshot: Mapping[str, object] | None = None) -> bool:
    entry = {"validation_schema": SOURCE_SCHEMA, "result": deepcopy(dict(result))}
    with driver._driver_state_lock:
        if driver._war_results_window_attempt != token:
            return False
        driver._war_results_window_observation = entry
        if (snapshot is not None and result.get("available") is True
                and result.get("post_observed") is True
                and result.get("post_effective_visible") is False):
            signature = _war_signature(snapshot)
            if signature is not None:
                driver._war_results_window_last_clear = {
                    "episode_run_id": snapshot.get("episode_run_id"),
                    "connection_generation": result.get("connection_generation"),
                    "actor_character_id": result.get("played_character_id"),
                    "date_raw": result.get("date_raw"),
                    "war_signature": signature,
                }
        return True


def collect_pending_war_results_window_close(driver: object) -> None:
    """Consume an already arrived original response; never send another close."""
    with driver._driver_state_lock:
        pending = deepcopy(driver._war_results_window_close_pending)
    if not isinstance(pending, Mapping) or pending.get("collectable") is not True:
        return
    frame = driver.state.wait_for_command_result(pending["native_request_id"], 0.0)
    if frame is None:
        return
    try:
        result = _result(frame, pending["native_request_id"], "close", pending["binding"], pending["native_generation"])
    except BridgeUnavailableError as error:
        with driver._driver_state_lock:
            active = driver._war_results_window_close_pending
            if isinstance(active, dict) and active.get("native_request_id") == pending["native_request_id"]:
                active.update(status="unknown", error=str(error)[:2048], collectable=False)
        return
    with driver._driver_state_lock:
        active = driver._war_results_window_close_pending
        if not isinstance(active, dict) or active.get("native_request_id") != pending["native_request_id"]:
            return
        if result["available"] is True:
            driver._war_results_window_close_pending = None
            driver._war_results_window_observation = None
            driver._war_results_window_query_attempt = None
            driver._war_results_window_attempt += 1
        else:
            active.update(status=result["status"], error=result["unavailable_reason"], collectable=False)
    # This is the actual late response to the first command, not a retry.
    driver._record_command(CLOSE_STEP, ok=result["accepted"], result={**result, "late_original_response": True})


def execute_war_results_window_v1(
    driver: object, *, operation: str, expected_revision: int,
) -> dict[str, object]:
    _integer(expected_revision, "expected_revision", 1, (1 << 64) - 1)
    if operation not in {"query", "close"}:
        raise ValueError("war results operation must be query or close")
    collect_pending_war_results_window_close(driver)
    before = driver.take_internal_semantic_snapshot()
    try:
        binding = _frame_binding(before)
        generation = _generation(before)
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error
    if binding["revision"] != expected_revision:
        raise PreSubmissionRevisionMismatchError("war results public revision is stale")
    step, capability = (QUERY_STEP, QUERY_CAPABILITY) if operation == "query" else (CLOSE_STEP, CLOSE_CAPABILITY)
    capabilities = driver.state.capabilities().get("bridge_capabilities")
    if not isinstance(capabilities, list) or capability not in capabilities:
        raise UnsupportedStepError("Native does not advertise this fixed war results operation")
    request_id = "war-overview-" + operation + "-" + uuid.uuid4().hex
    with driver._driver_state_lock:
        if operation == "close" and driver._war_results_window_close_pending is not None:
            raise BridgeUnavailableError("war results previous close remains unresolved; no close was resent")
        driver._war_results_window_attempt += 1
        token = driver._war_results_window_attempt
        driver._war_results_window_observation = None
        if operation == "query":
            driver._war_results_window_query_attempt = {
                "validation_schema": ATTEMPT_SCHEMA, "step": step, "native_request_id": request_id,
                "status": "pending", "error": None, **_lease(binding),
            }
        else:
            driver._war_results_window_query_attempt = None
            driver._war_results_window_close_pending = {
                "native_request_id": request_id, "step": step, "status": "pending", "error": None,
                "binding": dict(binding), "native_generation": generation, "collectable": False,
                **_lease(binding),
            }
    frame = None
    try:
        driver.endpoint.send({"type": "execute_step", "protocol_version": 1, "request_id": request_id,
                              "step": step, "expected_revision": binding["native_revision"]})
        frame = driver.state.wait_for_command_result(request_id, max(driver.command_timeout_seconds, 35.0))
        if frame is None:
            raise BridgeUnavailableError("war results original command_result timed out")
        result = _result(frame, request_id, operation, binding, generation)
        after = driver.take_internal_semantic_snapshot()
        try:
            callback_pending = (
                operation == "close" and result.get("available") is False
                and result.get("status") == "verification_pending"
                and result.get("dismiss_stage") == "callback_returned"
                and result.get("dismiss_exception_code") == 0
                and result.get("dispatch_attempted") is True
                and result.get("dispatch_invoked") is True
                and result.get("native_handled") is True
                and str(result.get("unavailable_reason", "")).startswith("war_results_ui_scope_transition;")
            )
            if not callback_pending and (_frame_binding(after) != binding or _generation(after) != generation):
                raise ValueError("war results crossed its actual paused actor/date/session lease")
        except ValueError as error:
            raise BridgeUnavailableError(str(error)) from error
        if operation == "query" and not _publish(driver, result, token, after):
            raise BridgeUnavailableError("war results query was superseded by a newer operation")
        with driver._driver_state_lock:
            if operation == "query" and driver._war_results_window_attempt == token:
                driver._war_results_window_query_attempt.update(status="observed")
            elif operation == "close":
                active = driver._war_results_window_close_pending
                if isinstance(active, dict) and active.get("native_request_id") == request_id:
                    if result["available"] is True:
                        driver._war_results_window_close_pending = None
                        driver._war_results_window_observation = None
                        driver._war_results_window_query_attempt = None
                        driver._war_results_window_attempt += 1
                        token = driver._war_results_window_attempt
                    else:
                        active.update(status=result["status"], error=result["unavailable_reason"])
        if operation == "close":
            _publish(driver, result, token, after)
        return result
    except Exception as error:
        with driver._driver_state_lock:
            if operation == "query" and driver._war_results_window_attempt == token:
                driver._war_results_window_query_attempt.update(status="failed", error=str(error)[:2048])
            elif operation == "close":
                active = driver._war_results_window_close_pending
                if isinstance(active, dict) and active.get("native_request_id") == request_id:
                    active.update(status="unknown", error=str(error)[:2048], collectable=frame is None)
        raise


def _current(driver: object, snapshot: Mapping[str, object], field: str, schema: str) -> dict[str, object] | None:
    try:
        binding = _frame_binding(snapshot)
        generation = _generation(snapshot)
    except ValueError:
        return None
    with driver._driver_state_lock:
        entry = getattr(driver, field)
        result = entry.get("result") if field == "_war_results_window_observation" and isinstance(entry, Mapping) else entry
        if (not isinstance(entry, Mapping) or entry.get("validation_schema") != schema
                or not isinstance(result, Mapping) or any(result.get(key) != binding[value] for key, value in LEASE_KEYS.items())
                or field == "_war_results_window_observation" and result.get("connection_generation") != generation):
            return None
        return deepcopy(dict(result))


def war_results_window_snapshot_fields(driver: object, snapshot: Mapping[str, object]) -> dict[str, object]:
    collect_pending_war_results_window_close(driver)
    with driver._driver_state_lock:
        pending = driver._war_results_window_close_pending
        last_clear = deepcopy(driver._war_results_window_last_clear)
        public_pending = ({key: deepcopy(value) for key, value in pending.items()
                           if key not in {"binding", "native_generation", "collectable"}}
                          if isinstance(pending, Mapping) else None)
    date_raw = snapshot.get("date_raw")
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None
    signature = _war_signature(snapshot)
    elapsed = (date_raw - last_clear["date_raw"] if isinstance(last_clear, Mapping)
               and type(date_raw) is int and type(last_clear.get("date_raw")) is int else None)
    current_clear = (isinstance(last_clear, Mapping) and elapsed is not None and 0 <= elapsed < 6 * 24
                     and signature is not None and signature == last_clear.get("war_signature")
                     and snapshot.get("episode_run_id") == last_clear.get("episode_run_id")
                     and generation == last_clear.get("connection_generation")
                     and isinstance(played, Mapping)
                     and played.get("character_id") == last_clear.get("actor_character_id"))
    return {
        "war_results_window_v1_observation": _current(driver, snapshot, "_war_results_window_observation", SOURCE_SCHEMA),
        "war_results_window_v1_query_attempt": _current(driver, snapshot, "_war_results_window_query_attempt", ATTEMPT_SCHEMA),
        "war_results_window_v1_close_pending": public_pending,
        "war_results_window_v1_check_due": not current_clear,
        "war_results_window_v1_next_check_date_raw": (
            last_clear["date_raw"] + 6 * 24 if current_clear else date_raw),
    }


def get_current_war_results_window_v1(driver: object, snapshot: Mapping[str, object]) -> dict[str, object] | None:
    return _current(driver, snapshot, "_war_results_window_observation", SOURCE_SCHEMA)


def get_current_war_results_window_v1_query_attempt(driver: object, snapshot: Mapping[str, object]) -> dict[str, object] | None:
    return _current(driver, snapshot, "_war_results_window_query_attempt", ATTEMPT_SCHEMA)

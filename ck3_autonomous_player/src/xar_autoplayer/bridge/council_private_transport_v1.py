"""Read the private council mailbox and consume its completed native result.

A queued private query returns pending. The status step consumes that same
mailbox operation; it neither queues another query nor advances the game.
"""

from __future__ import annotations

import time
from typing import Mapping
import uuid

from .council_composition_candidates_contract import (
    COUNCIL_COMPOSITION_CANDIDATES_V1_SCHEMA,
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY,
    QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP,
    STEWARD_POSITION_KEY,
    build_council_composition_candidates_request_v1,
    normalize_council_composition_candidates_v1,
)
from .council_assign_councillor_action_contract import (
    ASSIGN_COUNCILLOR_V1_STEP,
    QUERY_ASSIGN_COUNCILLOR_RECEIPT_V1_STEP,
    build_assign_councillor_request_v1,
    normalize_assign_councillor_ack_v1,
    normalize_assign_councillor_receipt_v1,
)
from .driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
)
from .version_identity import CK3_12002, require_exact_native_build


PRIVATE_QUERY_STEP = "private-query-council-composition-candidates-v1"
PRIVATE_STATUS_STEP = "private-council-application-main-status-v1"
PRIVATE_GATES_STEP = "private-query-council-final-gates-v1"
PRIVATE_ASSIGN_STEP = "private-assign-councillor-v1"
PRIVATE_RECEIPT_STEP = "private-query-assign-councillor-receipt-v1"
_PAYLOAD_FIELDS = {
    "snapshot", "owner_character_id", "position",
    "candidate_collection_complete", "candidates", "readiness",
}
_GATE_BOOLEAN_FIELDS = {
    "final_gate_available", "candidate_already_councillor",
    "candidate_is_guest", "pending_character_interaction",
    "incumbent_fireability_evaluated", "incumbent_can_be_fired",
}


def normalize_council_private_query_result_v1(
    value: object, *, expected_request: Mapping[str, object],
    expected_game_version: object = CK3_12002.game_version,
    expected_executable_sha256: object = CK3_12002.executable_sha256,
    query_step: str = PRIVATE_QUERY_STEP,
) -> dict[str, object]:
    """Project a terminal native query without promoting a pending result."""
    semantic_step = (QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_STEP
                     if query_step == PRIVATE_QUERY_STEP else PRIVATE_GATES_STEP)
    if query_step not in {PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP}:
        raise ValueError("unsupported private council read step")
    if not (
        isinstance(value, dict)
        and value.get("schema") == "xar.ck3.council-application-main/v1"
        and value.get("step") == semantic_step
        and value.get("accepted") is True
        and value.get("backend_id") == "native-headless"
        and type(value.get("query_sequence")) is int
        and value["query_sequence"] > 0
        and value.get("snapshot_revision") == expected_request["public_revision"]
    ):
        raise ValueError("private council result is not a completed native query")
    gates = value.get("council_final_gates") if query_step == PRIVATE_GATES_STEP else None
    payload = (gates.get("council_composition_candidates")
               if isinstance(gates, Mapping)
               else value.get("council_composition_candidates"))
    if not isinstance(payload, dict):
        raise ValueError("private council result lacks a candidate payload")
    exact = payload.get("exact_build")
    if not isinstance(exact, Mapping):
        raise ValueError("private council candidates lack exact-build metadata")
    observed_build = require_exact_native_build(
        exact.get("game_version"), exact.get("executable_sha256")
    )
    expected_build = require_exact_native_build(
        expected_game_version, expected_executable_sha256
    )
    if observed_build != expected_build:
        raise ValueError("private council source does not match the connected exact build")
    if not (
        payload.get("schema") == COUNCIL_COMPOSITION_CANDIDATES_V1_SCHEMA
        and payload.get("schema_version") == 1
        and payload.get("capability") == QUERY_COUNCIL_COMPOSITION_CANDIDATES_V1_CAPABILITY
        and value.get("status") in {"available", "unavailable"}
        and payload.get("status") == value.get("status")
    ):
        raise ValueError("private council status or schema is inconsistent")
    result = {
        **value, "step": query_step, "native_step": semantic_step,
        "private_build": True, "advertised": False,
        "read_only": True, "exact_build": dict(exact),
    }
    if value["status"] == "unavailable":
        return result
    if payload.get("unavailable_reason") is not None or payload.get("source_unavailable_reason") is not None:
        raise ValueError("available private council payload carries an unavailable reason")
    normalized = normalize_council_composition_candidates_v1(
        {key: payload.get(key) for key in _PAYLOAD_FIELDS},
        expected_snapshot_id=expected_request["expected_snapshot_id"],
        expected_public_revision=expected_request["public_revision"],
        expected_native_revision=expected_request["native_revision"],
        expected_date_raw=expected_request["date_raw"],
        expected_owner_character_id=expected_request["owner_character_id"],
        expected_position_key=expected_request["position_key"],
    )
    result["council_composition_candidates"] = normalized
    if query_step == PRIVATE_GATES_STEP:
        rows = gates.get("rows")
        if not (
            gates.get("status") == "available"
            and gates.get("unavailable_reason") == "none"
            and isinstance(rows, list)
            and gates.get("candidate_count") == len(normalized["candidates"])
            and len(rows) == len(normalized["candidates"])
        ):
            raise ValueError("private council final gates are incomplete")
        for row, candidate in zip(rows, normalized["candidates"]):
            if not (
                isinstance(row, dict)
                and row.get("character_id") == candidate["character_id"]
                and row.get("native_collection_ordinal") == candidate["native_collection_ordinal"]
                and all(type(row.get(key)) is bool for key in _GATE_BOOLEAN_FIELDS)
            ):
                raise ValueError("private council final-gate row does not match its candidate")
        result["council_final_gates"] = {
            **gates, "council_composition_candidates": normalized,
        }
    return result


def _binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    played = snapshot.get("played_character")
    return (
        snapshot.get("snapshot_id"), snapshot.get("revision"),
        snapshot.get("native_revision"), snapshot.get("date_raw"),
        snapshot.get("paused"), snapshot.get("map_ready"),
        played.get("character_id") if isinstance(played, Mapping) else None,
        played.get("alive") if isinstance(played, Mapping) else None,
    )


def _take_snapshot(driver: object) -> Mapping[str, object]:
    take_snapshot = (getattr(driver, "take_internal_semantic_snapshot", None)
                     or getattr(driver, "take_snapshot"))
    return take_snapshot()


class _CouncilReadStaleFrameError(BridgeUnavailableError):
    """A read was rejected before submission because its native frame expired."""


def _read_operation(
    driver: object, step: str, fields: Mapping[str, object],
    *, timeout_seconds: float | None = None, action_request_id: str | None = None,
) -> dict[str, object]:
    timeout = (getattr(driver, "command_timeout_seconds", 30.0)
               if timeout_seconds is None else timeout_seconds)
    if type(timeout) not in {int, float} or timeout <= 0:
        raise ValueError("private council operation timeout must be positive")
    deadline = time.monotonic() + timeout

    def send(current_step: str, current_fields: Mapping[str, object],
             request_id: str | None = None) -> dict[str, object]:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeUnavailableError("private council operation result timed out")
        request_id = request_id or "council-read-" + uuid.uuid4().hex
        driver.endpoint.send({
            "type": "execute_step", "protocol_version": 1,
            "request_id": request_id, "step": current_step, **current_fields,
        })
        frame = driver.state.wait_for_command_result(request_id, remaining)
        if (
            current_step in {PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP}
            and isinstance(frame, Mapping) and frame.get("type") == "command_result"
            and frame.get("protocol_version") == 1
            and frame.get("request_id") == request_id and frame.get("ok") is False
            and frame.get("error") == "nonwar private snapshot revision is stale or malformed"
        ):
            raise _CouncilReadStaleFrameError(str(frame["error"]))
        if not (
            isinstance(frame, Mapping) and frame.get("type") == "command_result"
            and frame.get("protocol_version") == 1
            and frame.get("request_id") == request_id and frame.get("ok") is True
            and isinstance(frame.get("result"), dict)
        ):
            raise BridgeUnavailableError("private council operation command_result is unavailable")
        return frame["result"]

    result = send(step, fields, action_request_id)
    while result.get("private_council_transport") is True:
        if result.get("advertised") is not False or result.get("status") != "pending":
            raise BridgeUnavailableError("private council mailbox has no completed operation")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise BridgeUnavailableError("private council operation result timed out")
        time.sleep(min(0.01, remaining))
        result = send(PRIVATE_STATUS_STEP, {})
    return result


def _wait_for_new_read_frame(
    driver: object, before: Mapping[str, object], *, deadline: float,
    rejection: _CouncilReadStaleFrameError,
) -> Mapping[str, object]:
    while True:
        fresh = _take_snapshot(driver)
        if _binding(fresh) != _binding(before):
            return fresh
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise rejection
        time.sleep(min(0.01, remaining))


def _source_frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    played = snapshot.get("played_character")
    return {
        "snapshot_id": snapshot.get("snapshot_id"), "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"), "date_raw": snapshot.get("date_raw"),
        "player_character_id": played.get("character_id") if isinstance(played, Mapping) else None,
        "paused": snapshot.get("paused"),
    }


def query_council_private_v1(
    driver: object, *, expected_revision: int | None = None,
    position_key: str = STEWARD_POSITION_KEY,
    query_step: str = PRIVATE_QUERY_STEP,
    timeout_seconds: float | None = None,
    expected_game_version: object = CK3_12002.game_version,
    expected_executable_sha256: object = CK3_12002.executable_sha256,
) -> dict[str, object]:
    """Wait for the queued read's terminal result on the existing driver pipe."""
    if query_step not in {PRIVATE_QUERY_STEP, PRIVATE_GATES_STEP}:
        raise ValueError("unsupported private council read step")
    before = _take_snapshot(driver)
    started = time.monotonic()
    attempt_timeout = timeout_seconds
    for attempt in range(2):
        played = before.get("played_character")
        player_id = played.get("character_id") if isinstance(played, Mapping) else None
        native_revision = before.get("native_revision")
        public_revision = before.get("revision")
        if not (
            before.get("paused") is True and before.get("map_ready") is True
            and isinstance(played, Mapping) and played.get("alive") is True
            and type(player_id) is int and player_id > 0
            and type(native_revision) is int and native_revision > 0
            and type(public_revision) is int and public_revision > 0
        ):
            raise BridgeUnavailableError("private council query requires a paused living-player map frame")
        if attempt == 0 and expected_revision is not None and expected_revision != public_revision:
            raise BridgeUnavailableError("private council query revision mismatch")
        request = build_council_composition_candidates_request_v1(
            expected_snapshot_id=f"native:{native_revision}",
            public_revision=native_revision, native_revision=native_revision,
            date_raw=before.get("date_raw"), owner_character_id=player_id,
            position_key=position_key, allow_chancellor_read_only=True,
            allow_spymaster_read_only=True,
        )
        try:
            result = _read_operation(
                driver, query_step, {
                    "expected_revision": native_revision,
                    "position_key": request["position_key"],
                },
                timeout_seconds=attempt_timeout,
            )
            break
        except _CouncilReadStaleFrameError as error:
            if attempt != 0:
                raise
            timeout = (getattr(driver, "command_timeout_seconds", 30.0)
                       if timeout_seconds is None else timeout_seconds)
            deadline = started + timeout
            before = _wait_for_new_read_frame(driver, before, deadline=deadline, rejection=error)
            attempt_timeout = deadline - time.monotonic()
            if attempt_timeout <= 0:
                raise error
    try:
        projected = normalize_council_private_query_result_v1(
            result, expected_request=request, query_step=query_step,
            expected_game_version=expected_game_version,
            expected_executable_sha256=expected_executable_sha256,
        )
    except ValueError as error:
        raise BridgeUnavailableError(f"private council query result is malformed: {error}") from error
    if _binding(_take_snapshot(driver)) != _binding(before):
        raise BridgeUnavailableError("private council query crossed its paused frame")
    return {
        **projected,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": public_revision,
        "queried_native_revision": native_revision,
        "source_frame": _source_frame(before),
    }


def submit_council_assign_private_v1(
    driver: object, *, query: Mapping[str, object],
    candidate_character_id: object, expected_revision: int,
    action_request_id: str | None = None, timeout_seconds: float | None = None,
    expected_game_version: object = CK3_12002.game_version,
    expected_executable_sha256: object = CK3_12002.executable_sha256,
) -> dict[str, object]:
    """Submit the cached native candidate once and return its typed pending ACK."""
    before = _take_snapshot(driver)
    if before.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("private council submit revision changed")
    source = query.get("source_frame")
    exact = query.get("exact_build")
    played = before.get("played_character")
    if not (
        isinstance(source, Mapping) and source == _source_frame(before)
        and before.get("paused") is True and before.get("map_ready") is True
        and isinstance(played, Mapping) and played.get("alive") is True
        and query.get("status") == "available"
        and query.get("private_build") is True and query.get("advertised") is False
        and isinstance(exact, Mapping)
        and require_exact_native_build(exact.get("game_version"), exact.get("executable_sha256"))
        == require_exact_native_build(expected_game_version, expected_executable_sha256)
    ):
        raise BridgeUnavailableError("private council assignment lacks its current native query")
    request = build_assign_councillor_request_v1(
        query.get("council_composition_candidates"),
        candidate_character_id=candidate_character_id,
        request_id=action_request_id or "council-assign-" + uuid.uuid4().hex,
    )
    try:
        result = _read_operation(
            driver, PRIVATE_ASSIGN_STEP,
            {"expected_revision": before["native_revision"],
             "candidate_character_id": request.candidate_character_id},
            timeout_seconds=timeout_seconds, action_request_id=request.request_id,
        )
    except BridgeUnavailableError as error:
        raise StepPostconditionError(
            "private council submission result unavailable; action state unknown",
            selected_step=PRIVATE_ASSIGN_STEP,
            step_result={"request": request.as_wire_fields(), "source_frame": _source_frame(before)},
        ) from error
    if not (
        result.get("schema") == "xar.ck3.council-application-main/v1"
        and result.get("step") == ASSIGN_COUNCILLOR_V1_STEP
        and result.get("accepted") is True
    ):
        raise BridgeUnavailableError("private council submit lacks its native ACK")
    try:
        ack = normalize_assign_councillor_ack_v1(
            result.get("council_assign_councillor_ack"), expected_request=request,
        )
    except ValueError as error:
        raise BridgeUnavailableError(f"private council submit ACK is malformed: {error}") from error
    if result.get("status") != ack["status"]:
        raise BridgeUnavailableError("private council submit status disagrees with its ACK")
    return {
        **result, "step": PRIVATE_ASSIGN_STEP, "native_step": ASSIGN_COUNCILLOR_V1_STEP,
        "private_build": True, "advertised": False,
        "action_request_id": request.request_id,
        "council_assign_councillor_ack": ack,
        "request": request.as_wire_fields(), "source_frame": _source_frame(before),
        "exact_build": dict(exact),
    }


def query_council_assign_receipt_private_v1(
    driver: object, *, pending: Mapping[str, object], expected_revision: int,
    timeout_seconds: float | None = None,
    expected_game_version: object = CK3_12002.game_version,
    expected_executable_sha256: object = CK3_12002.executable_sha256,
) -> dict[str, object]:
    """Read an independent later incumbent receipt for the existing action."""
    before = _take_snapshot(driver)
    if before.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("private council receipt revision changed")
    ack = pending.get("council_assign_councillor_ack")
    exact = pending.get("exact_build")
    played = before.get("played_character")
    native_revision = before.get("native_revision")
    if not (
        isinstance(ack, dict)
        and ack.get("status") == "native_helper_invoked_verification_pending"
        and type(native_revision) is int
        and type(ack.get("pre_native_revision")) is int
        and native_revision > ack["pre_native_revision"]
        and before.get("paused") is True and before.get("map_ready") is True
        and isinstance(played, Mapping) and played.get("alive") is True
        and played.get("character_id") == ack.get("owner_character_id")
        and isinstance(exact, Mapping)
        and require_exact_native_build(exact.get("game_version"), exact.get("executable_sha256"))
        == require_exact_native_build(expected_game_version, expected_executable_sha256)
    ):
        raise BridgeUnavailableError("private council receipt lacks an independent later owner frame")
    result = _read_operation(
        driver, PRIVATE_RECEIPT_STEP, {"expected_revision": native_revision},
        timeout_seconds=timeout_seconds,
    )
    if not (
        result.get("schema") == "xar.ck3.council-application-main/v1"
        and result.get("step") == QUERY_ASSIGN_COUNCILLOR_RECEIPT_V1_STEP
        and result.get("accepted") is True
    ):
        raise BridgeUnavailableError("private council result lacks an incumbent receipt")
    try:
        receipt = normalize_assign_councillor_receipt_v1(
            result.get("council_assign_councillor_receipt"), expected_ack=ack,
        )
    except ValueError as error:
        raise BridgeUnavailableError(f"private council receipt is malformed: {error}") from error
    if _binding(_take_snapshot(driver)) != _binding(before):
        raise BridgeUnavailableError("private council receipt crossed its paused frame")
    if receipt["status"] == "applied" and not (
        receipt["post_snapshot_id"] == f"native:{native_revision}"
        and receipt["post_public_revision"] == native_revision
        and receipt["post_native_revision"] == native_revision
        and receipt["post_date_raw"] == before.get("date_raw")
    ):
        raise BridgeUnavailableError("private council receipt does not match its current native frame")
    if result.get("status") != receipt["status"]:
        raise BridgeUnavailableError("private council status disagrees with its incumbent receipt")
    return {
        **result, "step": PRIVATE_RECEIPT_STEP,
        "native_step": QUERY_ASSIGN_COUNCILLOR_RECEIPT_V1_STEP,
        "private_build": True, "advertised": False,
        "action_request_id": ack["action_request_id"],
        "council_assign_councillor_receipt": receipt,
        "source_frame": _source_frame(before), "exact_build": dict(exact),
    }

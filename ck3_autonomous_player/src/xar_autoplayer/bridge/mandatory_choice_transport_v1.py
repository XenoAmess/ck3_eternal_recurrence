"""Exact-frame Native transport for a one-time unknown top-modal choice."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import uuid

QUERY_STEP = "query-mandatory-choice-v1"
SELECT_STEP = "select-mandatory-choice-v1"
CAPABILITY = "game.state.native-mandatory-choice-window-v1"
FRAME_KEYS = ("game_pid", "connection_generation", "revision",
              "native_revision", "date_raw", "actor_character_id",
              "episode_run_id", "snapshot_id")
NATIVE_OWNER_KEYS = ("game_pid", "connection_generation", "native_revision",
                     "date_raw", "actor_character_id", "episode_run_id")


def frame_from_snapshot(snapshot: dict) -> dict:
    from .native_driver import BridgeUnavailableError
    if not isinstance(snapshot, dict):
        raise BridgeUnavailableError("mandatory choice lacks a snapshot")
    played, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    if not isinstance(played, dict) or not isinstance(diagnostics, dict):
        raise BridgeUnavailableError("mandatory choice lacks actor or bridge diagnostics")
    frame = {"game_pid": diagnostics.get("bridge_pid"),
             "connection_generation": diagnostics.get("connection_generation"),
             "revision": snapshot.get("revision"),
             "native_revision": snapshot.get("native_revision"),
             "date_raw": snapshot.get("date_raw"),
             "actor_character_id": played.get("character_id"),
             "episode_run_id": snapshot.get("episode_run_id"),
             "snapshot_id": snapshot.get("snapshot_id")}
    if (any(type(frame[k]) is not int or frame[k] < 1 for k in (
            "game_pid", "connection_generation", "native_revision", "actor_character_id"))
            or type(frame["revision"]) is not int or frame["revision"] < 0
            or type(frame["date_raw"]) is not int
            or not isinstance(frame["episode_run_id"], str) or not frame["episode_run_id"]
            or not isinstance(frame["snapshot_id"], str) or not frame["snapshot_id"]):
        raise BridgeUnavailableError("mandatory choice has incomplete owner frame")
    return frame


def require_binding(source: dict, expected: dict, keys=FRAME_KEYS) -> None:
    from .native_driver import BridgeUnavailableError
    if (not isinstance(source, dict) or not isinstance(expected, dict)
            or any(source.get(k) != expected.get(k) for k in keys)):
        raise BridgeUnavailableError("mandatory choice owner or frame binding changed")


def query_native(driver, *, expected_revision: int, frame_binding: dict | None = None,
                 record: bool = True) -> dict:
    from .native_driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError
    starting = driver.take_snapshot_without_native_command_history()
    native_frame = frame_from_snapshot(starting)
    if type(expected_revision) is not int or native_frame["revision"] != expected_revision:
        raise PreSubmissionRevisionMismatchError("mandatory choice native query revision changed")
    frame = native_frame if frame_binding is None else frame_binding
    require_binding(native_frame, frame, NATIVE_OWNER_KEYS)
    evidence_dir = Path(driver._native_driver_state_path()).parent / "mandatory-choice-native-results"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    request_id = f"mandatory-choice-query-{uuid.uuid4().hex}"
    request_path = evidence_dir / f"{request_id}.request.json"
    result_path = evidence_dir / f"{request_id}.result.json"
    raw_receipt = {"native_request_id": request_id,
                   "native_request_path": str(request_path),
                   "native_result_path": str(result_path)}
    try:
        result = driver._execute_primitive_step(
            QUERY_STEP, expected_revision=expected_revision,
            required_capability=CAPABILITY,
            request_fields={"mandatory_choice_frame_binding": frame},
            include_native_command_history=False,
            protocol_request_id=request_id,
            protocol_packet_evidence_path=request_path,
            protocol_result_evidence_path=result_path)
        ending = driver.take_snapshot_without_native_command_history()
        require_binding(frame_from_snapshot(ending), native_frame)
        if not isinstance(result, dict) or result.get("step") != QUERY_STEP:
            raise BridgeUnavailableError("mandatory choice query returned malformed envelope")
        dto = result.get("mandatory_choice")
        if isinstance(dto, dict):
            require_binding(dto.get("frame_binding"), frame)
        result = {**result, **raw_receipt,
                  "queried_snapshot_id": frame["snapshot_id"],
                  "queried_revision": frame["revision"],
                  "queried_native_revision": frame["native_revision"]}
    except Exception as error:
        if record:
            driver._record_command(QUERY_STEP, ok=False, result=raw_receipt,
                                   error=f"{type(error).__name__}: {error}")
        raise
    if record:
        driver._record_command(QUERY_STEP, ok=result.get("accepted") is True, result=result)
    return result


def select_native(driver, *, query_id: str, action_token: str, frame_binding: dict,
                  window_instance_id: str | int, expected_revision: int) -> dict:
    from .native_driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError
    if (not isinstance(query_id, str) or not query_id
            or not isinstance(action_token, str) or not action_token
            or type(window_instance_id) not in (str, int)
            or isinstance(window_instance_id, str) and not window_instance_id):
        raise BridgeUnavailableError("mandatory choice token or window identity is missing")
    starting = driver.take_snapshot_without_native_command_history()
    native_frame = frame_from_snapshot(starting)
    if type(expected_revision) is not int or native_frame["revision"] != expected_revision:
        raise PreSubmissionRevisionMismatchError("mandatory choice native select revision changed")
    require_binding(native_frame, frame_binding, NATIVE_OWNER_KEYS)
    identity = {"game_pid": frame_binding["game_pid"],
                "episode_run_id": frame_binding["episode_run_id"],
                "window_instance_id": window_instance_id}
    digest = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
    directory = Path(driver._native_driver_state_path()).parent / "mandatory-choice-once-claims"
    directory.mkdir(parents=True, exist_ok=True)
    claim = directory / f"{digest}.claim.json"
    request_id = f"mandatory-choice-{uuid.uuid4().hex}"
    request_path = directory / f"{request_id}.request.json"
    result_path = directory / f"{request_id}.result.json"
    try:
        with claim.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump({"schema": "xar.native-mandatory-choice-once-claim/v1",
                       "request_id": request_id, "identity": identity,
                       "query_id": query_id, "frame_binding": frame_binding,
                       "status": "claimed_result_unknown_no_retry"}, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise BridgeUnavailableError(
            "mandatory choice instance already has an unresolved token claim; no replay") from error
    try:
        result = driver._execute_primitive_step(
            SELECT_STEP, expected_revision=expected_revision,
            required_capability=CAPABILITY,
            request_fields={"mandatory_choice_selection": {
                "query_id": query_id, "action_token": action_token,
                "frame_binding": frame_binding,
                "window_instance_id": window_instance_id}},
            protocol_request_id=request_id,
            protocol_packet_evidence_path=request_path,
            protocol_result_evidence_path=result_path,
            include_native_command_history=False)
        if not isinstance(result, dict) or result.get("step") != SELECT_STEP:
            raise BridgeUnavailableError("mandatory choice select returned malformed envelope")
    except Exception as error:
        error.mandatory_choice_raw_receipt = {
            "claim_path": str(claim), "request_id": request_id,
            "native_request_path": str(request_path),
            "native_result_path": str(result_path) if result_path.is_file() else None}
        driver._record_command(SELECT_STEP, ok=False,
                               result=error.mandatory_choice_raw_receipt,
                               error=f"{type(error).__name__}: {error}")
        raise
    result = {**result, "claim_path": str(claim), "request_id": request_id,
              "native_request_path": str(request_path),
              "native_result_path": str(result_path)}
    driver._record_command(SELECT_STEP, ok=result.get("accepted") is True, result=result)
    return result

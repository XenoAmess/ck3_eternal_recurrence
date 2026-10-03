"""Existing execute-step transport for the new G2 read-only native queries."""

from __future__ import annotations

from collections.abc import Mapping
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import _binding


def read_private_g2_native_query_v1(
    driver: object, *, permission: str, step: str, expected_revision: int,
    request_fields: Mapping[str, object] | None = None,
    timeout_seconds: float = 30.0,
) -> tuple[dict[str, object], dict[str, object]]:
    """Use the existing endpoint and frame binding; no gameplay action is sent."""
    if getattr(driver, permission, False) is not True:
        raise UnsupportedStepError(f"private native observation is disabled: {step}")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision or before.get("paused") is not True
            or before.get("map_ready") is not True or not isinstance(actor, Mapping)
            or actor.get("alive") is not True or type(native_revision) is not int or native_revision <= 0):
        raise BridgeUnavailableError("private native observation requires a living paused player")
    request_id = "g2-read-" + uuid.uuid4().hex
    driver.endpoint.send({
        **dict(request_fields or {}), "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": native_revision,
        "expected_snapshot_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, Mapping) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id
            or frame.get("ok") is not True):
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
    if _binding(driver.take_snapshot()) != _binding(before):
        raise BridgeUnavailableError(f"private native observation crossed its paused frame: {step}")
    return before, result


def private_g2_query_metadata_v1(snapshot: Mapping[str, object]) -> dict[str, object]:
    return {"queried_snapshot_id": snapshot.get("snapshot_id"),
            "queried_revision": snapshot.get("revision"),
            "queried_native_revision": snapshot.get("native_revision")}

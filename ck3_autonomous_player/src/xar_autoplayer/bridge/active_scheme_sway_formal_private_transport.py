"""Default-off typed sway submit and independent paused native receipt."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import (
    private_native_provenance, private_native_readback_matches,
)


SCHEMA = "active-scheme-sway-formal-private-v1"
SUBMIT_PREFIX = "submit-active-scheme-sway-v1-private-"
RECEIPT_PREFIX = "receipt-active-scheme-sway-v1-private-"
_ENVELOPE_KEYS = {
    "step", "accepted", "status", "private_build", "advertised",
    "active_scheme_sway_formal", "backend_id",
}


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _send(driver: object, *, step: str, action_id: str,
          expected_revision: int, stage: str,
          extra: Mapping[str, object] | None = None,
          source_readback: Mapping[str, object] | None = None,
          ) -> dict[str, object]:
    if getattr(driver, "allow_private_active_scheme_sway_action", False) is not True:
        raise UnsupportedStepError("private active-scheme sway action is disabled")
    if not _positive(expected_revision):
        raise ValueError("expected_revision must be positive")
    if not (isinstance(action_id, str) and action_id.startswith("sway-")
            and len(action_id) <= 64 and all(ch.isalnum() or ch in "-_"
                                      for ch in action_id)):
        raise ValueError("action_id is invalid")
    before = driver.take_snapshot()
    if (before.get("native_revision") != expected_revision
            or before.get("paused") is not True
            or before.get("map_ready") is not True):
        raise BridgeUnavailableError("private sway action requires its paused native frame")
    provenance = private_native_provenance(before)
    if (source_readback is not None
            and ("exe_sha256" in provenance or "exact_ck3_build" in source_readback)
            and not private_native_readback_matches(before, source_readback)):
        raise BridgeUnavailableError("private sway readback belongs to another native build")
    request_id = "sway-formal-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step,
        "expected_revision": expected_revision, "action_id": action_id,
        **dict(extra or {}),
    })
    frame = driver.state.wait_for_command_result(request_id, 30.0)
    if (not isinstance(frame, dict)
            or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private sway action result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("private sway native RED: " +
                                     str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict) or set(envelope) != _ENVELOPE_KEYS
            or envelope.get("step") != step
            or envelope.get("accepted") is not True
            or envelope.get("status") != stage
            or envelope.get("private_build") is not True
            or envelope.get("advertised") is not False
            or envelope.get("backend_id") != "native-headless"):
        raise BridgeUnavailableError("private sway action envelope malformed")
    result = envelope.get("active_scheme_sway_formal")
    if (not isinstance(result, dict) or result.get("schema") != SCHEMA
            or result.get("stage") != stage
            or result.get("action_id") != action_id):
        raise BridgeUnavailableError("private sway action payload malformed")
    after = driver.take_snapshot()
    if (before.get("played_character") != after.get("played_character")
            or before.get("date_raw") != after.get("date_raw")
            or after.get("paused") is not True
            or after.get("map_ready") is not True):
        raise BridgeUnavailableError("private sway action crossed actor/date frame")
    return {**result, **provenance}


def submit_active_scheme_sway_private_v1(
    driver: object, *, readback: Mapping[str, object],
    action_id: str,
) -> dict[str, object]:
    target = readback.get("target_character_id")
    opinion = readback.get("target_opinion_of_actor")
    epoch = readback.get("capture_epoch")
    generation = readback.get("container_generation")
    revision = readback.get("queried_native_revision")
    if (not all(_positive(value) for value in
                (target, epoch, generation, revision))
            or type(opinion) is not int or not -100 <= opinion <= 100
            or readback.get("native_complete_can_send") is not True
            or readback.get("native_legal_now") is not True
            or readback.get("matching_sway_active") is not False
            or readback.get("active_scheme_count") != 0):
        raise ValueError("private sway submit lacks a legal empty-slot readback")
    result = _send(
        driver, step=f"{SUBMIT_PREFIX}{target}", action_id=action_id,
        expected_revision=revision, stage="submitted_verification_pending",
        extra={"expected_capture_epoch": epoch,
               "expected_container_generation": generation,
               "expected_target_opinion_of_actor": str(opinion)},
        source_readback=readback,
    )
    if (result.get("actor_character_id") != readback.get("actor_character_id")
            or result.get("target_character_id") != target
            or not _positive(result.get("pre_capture_epoch"))
            or result["pre_capture_epoch"] <= epoch
            or result.get("pre_container_generation") != generation
            or result.get("pre_date_raw") != readback.get("date_raw")
            or result.get("submit_call_count") != 1
            or result.get("receipt_pending") is not True):
        raise BridgeUnavailableError("private sway submit ACK identity malformed")
    return result


def query_active_scheme_sway_receipt_private_v1(
    driver: object, *, target_character_id: int, action_id: str,
    expected_revision: int, pre_capture_epoch: int,
) -> dict[str, object]:
    if not _positive(target_character_id) or not _positive(pre_capture_epoch):
        raise ValueError("private sway receipt identity is invalid")
    result = _send(
        driver, step=f"{RECEIPT_PREFIX}{target_character_id}",
        action_id=action_id, expected_revision=expected_revision,
        stage="applied",
    )
    if (not _positive(result.get("post_capture_epoch"))
            or result["post_capture_epoch"] <= pre_capture_epoch
            or not _positive(result.get("scheme_instance_id"))
            or type(result.get("scheme_instance_generation")) is not int
            or not 0 <= result["scheme_instance_generation"] <= 255
            or result.get("postcondition_verified") is not True):
        raise BridgeUnavailableError("private sway receipt postcondition malformed")
    return result

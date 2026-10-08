"""One actual4 selected Stop command; its queue result remains pending."""
from __future__ import annotations

from collections.abc import Mapping
import uuid

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity, private_native_readback_matches
from .version_identity import CK3_12004

STEP = "stop-active-scheme-sway-v1-private"
SCHEMA = "xar.ck3.selected-sway-stop.v1"


def stop_active_scheme_sway_private_v1(
    driver: object, *, expected_revision: int, target_character_id: int,
    scheme_instance_id: int, scheme_instance_generation: int, action_id: str,
) -> dict[str, object]:
    if getattr(driver, "allow_private_active_scheme_sway_action", False) is not True:
        raise UnsupportedStepError("private active-scheme Sway action is disabled")
    if (type(expected_revision) is not int or expected_revision <= 0
            or type(target_character_id) is not int or target_character_id <= 0
            or type(scheme_instance_id) is not int or not 0 <= scheme_instance_id < 0xFFFFFFFF
            or type(scheme_instance_generation) is not int
            or not 0 <= scheme_instance_generation <= 255
            or scheme_instance_id >> 24 != scheme_instance_generation
            or not isinstance(action_id, str) or not action_id.startswith("stop-sway-")
            or len(action_id) > 64
            or not all(ch.isascii() and (ch.isalnum() or ch in "-_") for ch in action_id)):
        raise ValueError("selected Sway Stop identity is invalid")
    before = driver.take_snapshot()
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision or before.get("paused") is not True
            or before.get("map_ready") is not True
            or not isinstance(actor, Mapping) or actor.get("alive") is not True
            or type(actor.get("character_id")) is not int or actor["character_id"] <= 0
            or actor["character_id"] == target_character_id
            or type(native_revision) is not int or native_revision <= 0
            or private_native_build_identity(before) != CK3_12004):
        raise BridgeUnavailableError("selected Sway Stop requires the current actual4 player frame")
    request_id = "sway-stop-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": STEP, "expected_revision": native_revision, "action_id": action_id,
        "actor_character_id": actor["character_id"], "target_character_id": target_character_id,
        "scheme_instance_id": scheme_instance_id,
        "scheme_instance_generation": scheme_instance_generation,
    })
    frame = driver.state.wait_for_command_result(request_id, driver.command_timeout_seconds)
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id
            or frame.get("ok") is not True):
        raise BridgeUnavailableError("selected Sway Stop native result unavailable: " +
                                     str(frame.get("error", "unknown") if isinstance(frame, dict) else "unknown"))
    envelope = frame.get("result")
    body = envelope.get("sway_stop") if isinstance(envelope, dict) else None
    if (not isinstance(envelope, dict) or envelope.get("step") != STEP
            or envelope.get("accepted") is not True or envelope.get("read_only") is not False
            or envelope.get("private_build") is not True or envelope.get("advertised") is not False
            or envelope.get("backend_id") != "native-headless"
            or envelope.get("status") != "submitted_verification_pending"
            or not isinstance(body, dict) or body.get("schema") != SCHEMA
            or body.get("action_id") != action_id
            or body.get("status") != "submitted_verification_pending"
            or body.get("actor_character_id") != actor["character_id"]
            or body.get("target_character_id") != target_character_id
            or body.get("scheme_instance_id") != scheme_instance_id
            or body.get("scheme_instance_generation") != scheme_instance_generation
            or body.get("snapshot_revision") != native_revision
            or body.get("date_raw") != before.get("date_raw")
            or body.get("submit_call_count") != 1
            or body.get("postcondition_verified") is not False
            or body.get("terminal_observed") is not False
            or body.get("terminal_cause_observed") is not False
            or body.get("terminal_cause") != "unknown"
            or not private_native_readback_matches(before, body)):
        raise BridgeUnavailableError("selected Sway Stop pending ACK identity malformed")
    return dict(body)

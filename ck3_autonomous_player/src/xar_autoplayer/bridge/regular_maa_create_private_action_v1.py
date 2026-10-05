"""Submit one true regular personal MAA command; retain native pending/rejection."""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import uuid

from .driver import BridgeUnavailableError
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12003

STEP = "maa-regular-personal-create-private-v1"
ACTION_SCHEMA = "xar.ck3.regular-maa-create-private-action.v1"
STATUSES = {"unavailable", "rejected", "queued_pending"}


def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value <= high


def submit_regular_maa_create_private_v1(
    driver: object, *, expected_revision: int, type_index: int, action_id: str,
    timeout_seconds: float = 30.0,
) -> dict[str, object]:
    """Send once; a native AL1 is queued_pending, never a created/payment result."""
    if not _integer(expected_revision, 1, (1 << 64) - 1):
        raise ValueError("expected_revision must identify the current public snapshot")
    if not _integer(type_index, 0, (1 << 31) - 1):
        raise ValueError("type_index must be an observed native registry index")
    if not isinstance(action_id, str) or not 0 < len(action_id.encode("utf-8")) <= 63:
        raise ValueError("action_id must be a nonempty caller identity of at most63 UTF-8 bytes")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    actor = before.get("played_character")
    if (before.get("revision") != expected_revision or before.get("paused") is not True
            or before.get("map_ready") is not True or not isinstance(actor, Mapping)
            or actor.get("alive") is not True
            or not _integer(actor.get("character_id"), -(1 << 31), (1 << 31) - 1)
            or actor.get("character_id") == -1
            or not _integer(before.get("native_revision"), 1, (1 << 64) - 1)
            or type(before.get("date_raw")) is not int
            or private_native_build_identity(before) != CK3_12003):
        raise BridgeUnavailableError("regular MAA Create requires its current paused Crozier player frame")
    request_id = "maa-create-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1, "request_id": request_id, "step": STEP,
        "expected_revision": before["native_revision"],
        "expected_snapshot_revision": before["native_revision"],
        "expected_public_revision": before["revision"],
        "expected_date_raw": before["date_raw"],
        "expected_player_character_id": actor["character_id"],
        "type_index": type_index, "action_id": action_id,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("regular MAA command_result unresolved; do not automatically resubmit")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("regular MAA native RED: " + str(frame.get("error", "unknown")))
    value = frame.get("result")
    build = private_native_build_identity(before)
    if (not isinstance(value, dict) or value.get("step") != STEP
            or value.get("accepted") is not True or value.get("private_build") is not True
            or value.get("advertised") is not False or value.get("backend_id") != "native-headless"
            or value.get("game_version") != build.game_version
            or value.get("executable_sha256") != build.executable_sha256
            or value.get("read_only") is not False
            or value.get("snapshot_revision") != before["native_revision"]
            or value.get("public_revision") != before["revision"]
            or value.get("date_raw") != before["date_raw"] or value.get("action_id") != action_id
            or not _integer(value.get("capture_epoch"), 1, (1 << 64) - 1)):
        raise BridgeUnavailableError("regular MAA envelope differs from its actual build/player frame")
    submission = value.get("submission")
    if (not isinstance(submission, dict) or submission.get("schema_version") != 1
            or submission.get("status") not in STATUSES or value.get("status") != submission.get("status")
            or not isinstance(submission.get("reason"), str)
            or submission.get("command_class") != "CCreateMAARegimentCommand"
            or submission.get("owner_character_id") != actor["character_id"]
            or submission.get("type_index") != type_index):
        raise BridgeUnavailableError("regular MAA native submission is malformed")
    for key in ("native_can_create", "native_submit_accepted", "command_pointer_consumed"):
        if key not in submission or (submission[key] is not None and type(submission[key]) is not bool):
            raise BridgeUnavailableError("regular MAA native nullable bool is malformed: " + key)
    after = driver.take_snapshot()
    after_actor = after.get("played_character")
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"] or not isinstance(after_actor, Mapping)
            or after_actor.get("alive") is not True or after_actor.get("character_id") != actor["character_id"]
            or private_native_build_identity(after) != build):
        raise BridgeUnavailableError("regular MAA transport crossed its current player/date frame")
    queued = submission["status"] == "queued_pending"
    return {
        "schema": ACTION_SCHEMA, **private_native_provenance(before),
        "status": submission["status"], "reason": submission["reason"],
        "request_id": request_id, "action_id": action_id,
        "player_character_id": actor["character_id"], "type_index": type_index,
        "submitted": queued, "verification_pending": queued,
        "material_result": False, "created_observed": False, "payment_observed": False,
        "native_submission": deepcopy(submission),
        "capture_epoch": value["capture_epoch"], "automatic_retry": False, "advertised": False,
    }

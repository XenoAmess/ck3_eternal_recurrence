"""Current-player pilgrimage hosted identities; no planning or mutation."""
from __future__ import annotations

import uuid
from collections.abc import Mapping

from .activity_feast_stage5_start_private_transport import _source_snapshot, _same_frame
from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_build_identity, private_native_provenance
from .version_identity import CK3_12004

TOOL = "ck3_query_player_pilgrimage_activities_v1"
STEP = "query-player-pilgrimage-activities-v1-private"
SCHEMA = "ck3_12004_player_pilgrimage_activities_v1"


def normalize_player_pilgrimage_activities_v1(
    value: object, *, source: Mapping[str, object],
) -> dict[str, object]:
    keys = {"schema", "read_only", "snapshot_revision", "date_raw",
            "played_character_id", "scope", "activity_type_key", "activity_count",
            "activities", "absence_is_completion", "raw_pointer_fields_persisted"}
    actor = source["played_character"]["character_id"]
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != SCHEMA or value["read_only"] is not True
            or type(value["snapshot_revision"]) is not int
            or value["snapshot_revision"] != source["native_revision"]
            or type(value["date_raw"]) is not int or value["date_raw"] != source["date_raw"]
            or type(value["played_character_id"]) is not int
            or value["played_character_id"] != actor
            or value["scope"] != "currently-hosted-by-current-player"
            or value["activity_type_key"] != "activity_pilgrimage"
            or value["absence_is_completion"] is not False
            or value["raw_pointer_fields_persisted"] is not False
            or not isinstance(value["activities"], list)
            or len(value["activities"]) > 64
            or type(value["activity_count"]) is not int
            or value["activity_count"] != len(value["activities"])):
        raise BridgeUnavailableError("native pilgrimage activity identities malformed")
    rows = []
    seen = set()
    row_keys = {"activity_id", "host_character_id", "type_key", "terminal_flags_observed",
                "native_completed", "native_invalidated", "native_completion_stamp_observed",
                "native_completion_stamp_raw"}
    for row in value["activities"]:
        if (not isinstance(row, dict) or set(row) != row_keys
                or type(row["activity_id"]) is not int
                or not 0 <= row["activity_id"] < 2**32 - 1
                or row["activity_id"] in seen
                or type(row["host_character_id"]) is not int
                or row["host_character_id"] != actor
                or row["type_key"] != "activity_pilgrimage"
                or type(row["terminal_flags_observed"]) is not bool
                or type(row["native_completion_stamp_observed"]) is not bool):
            raise BridgeUnavailableError("native pilgrimage activity row malformed")
        for key in ("native_completed", "native_invalidated"):
            if ((row["terminal_flags_observed"] and type(row[key]) is not bool)
                    or (not row["terminal_flags_observed"] and row[key] is not None)):
                raise BridgeUnavailableError("native pilgrimage terminal availability malformed")
        stamp = row["native_completion_stamp_raw"]
        if ((row["native_completion_stamp_observed"]
             and (type(stamp) is not int or not 0 <= stamp < 2**64))
                or (not row["native_completion_stamp_observed"] and stamp is not None)):
            raise BridgeUnavailableError("native pilgrimage raw completion stamp malformed")
        seen.add(row["activity_id"])
        rows.append(dict(row))
    return {**value, "activities": rows}


def query_player_pilgrimage_activities_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    declared = getattr(driver, "case_declared_read_only_mcp_tools", ())
    if (getattr(driver, "allow_private_player_pilgrimage_activities_query", False) is not True
            and TOOL not in declared):
        raise UnsupportedStepError("private player pilgrimage identities query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = _source_snapshot(driver)
    if before["revision"] != expected_revision:
        raise BridgeUnavailableError("pilgrimage identities query revision changed")
    if private_native_build_identity(before) != CK3_12004:
        raise BridgeUnavailableError("pilgrimage identities require exact CK3 1.20.0.4")
    provenance = private_native_provenance(before)
    request_id = "player-pilgrimage-identities-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1, "request_id": request_id,
        "step": STEP, "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_actor_character_id": before["played_character"]["character_id"],
        "expected_activity_key": "activity_pilgrimage",
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("pilgrimage identities command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError("pilgrimage identities native RED: " + str(frame.get("error", "unknown")))
    envelope = frame.get("result")
    if (not isinstance(envelope, dict) or set(envelope) != {
            "step", "accepted", "status", "private_build", "read_only",
            "advertised", "player_pilgrimage_activities", "backend_id"}
            or envelope["step"] != STEP or envelope["accepted"] is not True
            or envelope["status"] != "available" or envelope["private_build"] is not True
            or envelope["read_only"] is not True or envelope["advertised"] is not False
            or envelope["backend_id"] != "native-headless"):
        raise BridgeUnavailableError("pilgrimage identities native envelope malformed")
    value = normalize_player_pilgrimage_activities_v1(
        envelope["player_pilgrimage_activities"], source=before)
    after = _source_snapshot(driver)
    if not _same_frame(before, after):
        raise BridgeUnavailableError("pilgrimage identities query crossed paused frame")
    return {**value, **provenance, "queried_snapshot_id": before["snapshot_id"],
            "queried_revision": before["revision"],
            "queried_native_revision": before["native_revision"],
            "post_snapshot_id": after["snapshot_id"]}

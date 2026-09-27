"""Unadvertised paused native prisoner collection and narrow lineage values."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .timeline_blocker_private_transport import _binding


STEP = "query-player-prisoner-collection-private-v1"
SCHEMA = "player-prisoner-collection-private-v1"
_ENVELOPE_KEYS = {
    "step", "accepted", "status", "query_sequence", "observation_revision",
    "snapshot_revision", "player_prisoner_collection", "private_build",
    "read_only", "advertised", "backend_id",
}
_VALUE_KEYS = {
    "schema", "schema_version", "snapshot_revision", "status",
    "unavailable_reason", "date_raw", "played_character_id", "total_count",
    "returned_count", "collection_complete", "prisoners",
}
_VALUE_KEYS_V3 = _VALUE_KEYS | {"played_house_id", "played_dynasty_id"}
_ROW_KEYS = {"source_ordinal", "prisoner_character_id", "collection_owner_character_id", "jailer_character_id", "custody_relation_verified"}
_LINEAGE_KEYS = {"house_id", "dynasty_id", "same_house", "same_dynasty"}


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _lineage_id(value: object) -> bool:
    return value is None or (isinstance(value, int) and not isinstance(value, bool) and value >= 0)


def query_player_prisoner_collection_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_prisoner_collection_query", False) is not True:
        raise UnsupportedStepError("private prisoner collection query is disabled")
    if not _positive_int(expected_revision):
        raise ValueError("expected_revision must be a positive integer")
    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    native_revision = before.get("native_revision")
    date_raw = before.get("date_raw")
    played = before.get("played_character")
    if (
        before.get("revision") != expected_revision
        or before.get("paused") is not True
        or before.get("map_ready") is not True
        or not _positive_int(native_revision)
        or isinstance(date_raw, bool)
        or not isinstance(date_raw, int)
        or not isinstance(played, Mapping)
        or played.get("alive") is not True
        or not _positive_int(played.get("character_id"))
    ):
        raise BridgeUnavailableError("prisoner collection requires a living player on a paused map frame")
    request_id = "prisoner-collection-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if not isinstance(frame, dict) or frame.get("type") != "command_result" or frame.get("protocol_version") != 1 or frame.get("request_id") != request_id or frame.get("ok") is not True:
        raise BridgeUnavailableError("private prisoner collection query returned RED or timed out")
    envelope = frame.get("result")
    if (
        not isinstance(envelope, dict) or set(envelope) != _ENVELOPE_KEYS
        or envelope.get("step") != STEP or envelope.get("accepted") is not True
        or envelope.get("snapshot_revision") != native_revision
        or envelope.get("private_build") is not True
        or envelope.get("read_only") is not True
        or envelope.get("advertised") is not False
        or envelope.get("backend_id") != "native-headless"
        or not _positive_int(envelope.get("query_sequence"))
        or not _positive_int(envelope.get("observation_revision"))
    ):
        raise BridgeUnavailableError("private prisoner collection envelope is malformed")
    value = envelope.get("player_prisoner_collection")
    if (
        not isinstance(value, dict) or set(value) != (_VALUE_KEYS_V3 if value.get("schema_version") == 3 else _VALUE_KEYS)
        or value.get("schema") != SCHEMA
        or value.get("schema_version") not in (1, 2, 3)
        or value.get("snapshot_revision") != native_revision
        or value.get("status") != envelope.get("status")
    ):
        raise BridgeUnavailableError("private prisoner collection payload is malformed")
    if value["status"] == "available":
        preview_version = value["schema_version"] in (2, 3)
        lineage_version = value["schema_version"] == 3
        count = value.get("total_count")
        rows = value.get("prisoners")
        if (
            value.get("unavailable_reason") is not None
            or value.get("date_raw") != date_raw
            or value.get("played_character_id") != played["character_id"]
            or not isinstance(count, int) or isinstance(count, bool)
            or not 0 <= count <= 64 or value.get("returned_count") != count
            or value.get("collection_complete") is not True
            or not isinstance(rows, list) or len(rows) != count
            or (lineage_version and (
                not _lineage_id(value.get("played_house_id"))
                or not _lineage_id(value.get("played_dynasty_id"))
                or (value.get("played_house_id") is None and value.get("played_dynasty_id") is not None)
            ))
        ):
            raise BridgeUnavailableError("private prisoner collection count or binding is malformed")
        seen: set[int] = set()
        for ordinal, row in enumerate(rows):
            if (
                not isinstance(row, dict)
                or set(row) != (_ROW_KEYS | ({"unconditional_release_preview"} if preview_version else set()) | (_LINEAGE_KEYS if lineage_version else set()))
                or row.get("source_ordinal") != ordinal
                or not _positive_int(row.get("prisoner_character_id"))
                or row["prisoner_character_id"] > 0xFFFFFFFF
                or row["prisoner_character_id"] == played["character_id"]
                or row["prisoner_character_id"] in seen
                or row.get("collection_owner_character_id") != played["character_id"]
                or row.get("jailer_character_id") != played["character_id"]
                or row.get("custody_relation_verified") is not True
            ):
                raise BridgeUnavailableError("private prisoner collection row is malformed")
            if lineage_version:
                house_id = row.get("house_id")
                dynasty_id = row.get("dynasty_id")
                if (
                    not _lineage_id(house_id)
                    or not _lineage_id(dynasty_id)
                    or (house_id is None and dynasty_id is not None)
                    or type(row.get("same_house")) is not bool
                    or type(row.get("same_dynasty")) is not bool
                    or row["same_house"] != (house_id is not None and house_id == value["played_house_id"])
                    or row["same_dynasty"] != (dynasty_id is not None and dynasty_id == value["played_dynasty_id"])
                ):
                    raise BridgeUnavailableError("private prisoner lineage is malformed")
            if preview_version:
                preview = row["unconditional_release_preview"]
                if (
                    not isinstance(preview, dict)
                    or preview.get("private_build") is not True
                    or preview.get("read_only") is not True
                    or preview.get("advertised") is not False
                    or preview.get("action_surface_present") is not False
                ):
                    raise BridgeUnavailableError("private release preview envelope is malformed")
                if preview.get("status") == "available":
                    definition = preview.get("definition")
                    roles = preview.get("roles")
                    acceptance = preview.get("acceptance")
                    costs = preview.get("costs")
                    readiness = preview.get("readiness")
                    if (
                        preview.get("snapshot_id") != f"native:{native_revision}"
                        or preview.get("public_revision") != native_revision
                        or preview.get("native_revision") != native_revision
                        or preview.get("date_raw") != date_raw
                        or not isinstance(definition, dict)
                        or definition.get("canonical_key") != "release_from_prison_interaction"
                        or preview.get("payload_shape") != "two_role_all_release_options_off"
                        or not isinstance(roles, dict)
                        or roles.get("actor_character_id") != played["character_id"]
                        or roles.get("recipient_character_id") != row["prisoner_character_id"]
                        or preview.get("unconditional_prisoner_release") is not True
                        or type(preview.get("can_send")) is not bool
                        or not isinstance(acceptance, dict)
                        or acceptance.get("kind") != "auto_accept"
                        or acceptance.get("auto_accept") is not True
                        or acceptance.get("would_accept_now") is not True
                        or not isinstance(costs, dict)
                        or costs.get("raw_scale") != 100_000
                        or not isinstance(costs.get("entries"), list)
                        or len(costs["entries"]) != 10
                        or not isinstance(readiness, dict)
                        or readiness.get("same_frame_ready") is not True
                    ):
                        raise BridgeUnavailableError("private release final preview is malformed")
                elif preview.get("status") == "unavailable":
                    if set(preview) != {"private_build", "read_only", "advertised", "action_surface_present", "status", "unavailable_reason"} or not isinstance(preview.get("unavailable_reason"), str) or not preview["unavailable_reason"]:
                        raise BridgeUnavailableError("private release unavailable preview is malformed")
                else:
                    raise BridgeUnavailableError("private release preview status is malformed")
            seen.add(row["prisoner_character_id"])
    elif value["status"] == "unavailable":
        if (
            not isinstance(value.get("unavailable_reason"), str)
            or not value["unavailable_reason"]
            or any(value.get(key) is not None for key in (
                "date_raw", "played_character_id", "total_count", "returned_count",
                "played_house_id", "played_dynasty_id",
            ))
            or value.get("collection_complete") is not False
            or value.get("prisoners") != []
        ):
            raise BridgeUnavailableError("private prisoner collection unavailable result is malformed")
    else:
        raise BridgeUnavailableError("private prisoner collection status is malformed")
    if _binding(driver.take_snapshot()) != _binding(before):
        raise BridgeUnavailableError("private prisoner collection crossed its paused frame")
    return {**envelope, "queried_snapshot_id": before.get("snapshot_id"),
            "queried_revision": before.get("revision"),
            "queried_native_revision": native_revision}

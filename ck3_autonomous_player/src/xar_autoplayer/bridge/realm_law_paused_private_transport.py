"""Default-off native final realm-law read on one paused current-player frame."""

from __future__ import annotations

import uuid
from collections.abc import Mapping

from .driver import BridgeUnavailableError, UnsupportedStepError
from .nonwar_private_build import private_native_provenance


STEP = "query-realm-law-final-terms-v1-private"
SCHEMA = "realm-law-final-terms-private-read-v1"
SLOTS = (
    "gold", "prestige", "piety", "renown", "influence", "herd",
    "treasury", "treasury_or_gold", "merit", "barter_goods",
)
GROUPS = ("crown_authority", "succession_order_laws")
STATUSES = {
    "candidate_kind_rejected", "already_active", "engine_blocked", "can_enact",
}


def _valid_payload(value: object, *, revision: int, date_raw: int,
                   actor_id: int) -> bool:
    if not isinstance(value, dict) or set(value) != {
        "schema", "snapshot_revision", "date_raw", "actor_character_id",
        "cost_scale", "cost_slots", "groups",
    }:
        return False
    if (value["schema"] != SCHEMA or value["snapshot_revision"] != revision
            or value["date_raw"] != date_raw
            or value["actor_character_id"] != actor_id
            or value["cost_scale"] != 100000
            or value["cost_slots"] != list(SLOTS)):
        return False
    groups = value["groups"]
    if not isinstance(groups, list) or len(groups) != 2:
        return False
    for group, expected_key in zip(groups, GROUPS, strict=True):
        if not isinstance(group, dict) or set(group) != {
            "group_key", "active_law_key", "candidates",
        } or group["group_key"] != expected_key:
            return False
        rows = group["candidates"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
            return False
        keys: set[str] = set()
        active: list[str] = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {
                "law_key", "active", "final_status", "final_can_enact",
                "native_reason", "cost_raw",
            }:
                return False
            key = row["law_key"]
            if not isinstance(key, str) or not key or key in keys:
                return False
            keys.add(key)
            if type(row["active"]) is not bool or row["final_status"] not in STATUSES:
                return False
            if (type(row["final_can_enact"]) is not bool
                    or row["final_can_enact"] != (row["final_status"] == "can_enact")
                    or not isinstance(row["native_reason"], str)
                    or len(row["native_reason"]) > 4096):
                return False
            costs = row["cost_raw"]
            if (not isinstance(costs, list) or len(costs) != 10
                    or any(type(cost) is not int or not -(1 << 63) <= cost < (1 << 63)
                           for cost in costs)):
                return False
            if row["active"]:
                active.append(key)
                if row["final_status"] != "already_active":
                    return False
        if len(active) > 1 or group["active_law_key"] != (active[0] if active else None):
            return False
    return True


def query_realm_law_final_terms_private_v1(
    driver: object, *, expected_revision: int, timeout_seconds: float = 30.0,
) -> dict[str, object]:
    if getattr(driver, "allow_private_realm_law_paused_query", False) is not True:
        raise UnsupportedStepError("private realm-law query is disabled")
    if type(expected_revision) is not int or expected_revision <= 0:
        raise ValueError("expected_revision must be positive")
    if type(timeout_seconds) not in (int, float) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    before = driver.take_snapshot()
    actor = before.get("played_character")
    native_revision = before.get("native_revision")
    if (before.get("revision") != expected_revision
            or before.get("paused") is not True
            or before.get("map_ready") is not True
            or not isinstance(actor, Mapping)
            or actor.get("alive") is not True
            or type(actor.get("character_id")) is not int
            or actor["character_id"] <= 0
            or type(native_revision) is not int or native_revision <= 0
            or type(before.get("date_raw")) is not int):
        raise BridgeUnavailableError("private realm-law query requires a living paused actor")
    provenance = private_native_provenance(before)
    request_id = "realm-law-read-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": STEP,
        "expected_revision": native_revision,
    })
    frame = driver.state.wait_for_command_result(request_id, float(timeout_seconds))
    if (not isinstance(frame, dict) or frame.get("type") != "command_result"
            or frame.get("protocol_version") != 1
            or frame.get("request_id") != request_id):
        raise BridgeUnavailableError("private realm-law command_result unavailable")
    if frame.get("ok") is not True:
        raise BridgeUnavailableError(
            "private realm-law native RED: " + str(frame.get("error", "unknown"))
        )
    envelope = frame.get("result")
    envelope_keys = {
        "step", "accepted", "status", "private_build", "read_only",
        "advertised", "realm_law_final_terms", "backend_id",
    }
    allowed_envelope_keys = (envelope_keys,)
    if provenance["exact_ck3_build"] in {"1.20.0.2", "1.20.0.3"}:
        # The new common ReadOnlyFrame repeats the owning revision outside
        # the unchanged DTO. Legacy eight-key envelopes remain supported.
        allowed_envelope_keys += (envelope_keys | {"snapshot_revision"},)
    if (not isinstance(envelope, dict) or set(envelope) not in allowed_envelope_keys
            or ("snapshot_revision" in envelope and (
                type(envelope["snapshot_revision"]) is not int
                or envelope["snapshot_revision"] != native_revision))
            or envelope.get("step") != STEP or envelope.get("accepted") is not True
            or envelope.get("status") != "available"
            or envelope.get("private_build") is not True
            or envelope.get("read_only") is not True
            or envelope.get("advertised") is not False
            or envelope.get("backend_id") != "native-headless"
            or not _valid_payload(envelope.get("realm_law_final_terms"),
                                  revision=native_revision,
                                  date_raw=before["date_raw"],
                                  actor_id=actor["character_id"])):
        raise BridgeUnavailableError("private realm-law native payload malformed")
    after = driver.take_snapshot()
    if (after.get("paused") is not True or after.get("map_ready") is not True
            or after.get("date_raw") != before["date_raw"]
            or after.get("played_character") != actor):
        raise BridgeUnavailableError("private realm-law read crossed the paused actor/date frame")
    return {
        **envelope["realm_law_final_terms"],
        **provenance,
        "queried_snapshot_id": before.get("snapshot_id"),
        "queried_revision": expected_revision,
        "queried_native_revision": native_revision,
        "post_snapshot_id": after.get("snapshot_id"),
    }

"""Strict shape check for a future native physical CUnit inventory receipt.

This module is intentionally not wired into formal date/action admission. A
matching JSON object is not proof of native provenance until the bridge binds
the receipt to its main-thread mailbox and same-frame snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_MAILBOX_NATIVE_KEYS = frozenset({
    "source_build", "status", "date_raw", "war_id", "subject_army_id",
    "native_revision", "query_sequence", "mailbox_pump_epoch",
    "mailbox_thread_id", "mailbox_date_raw", "mailbox_paused",
    "same_source_across_route", "storage_capacity", "slots_scanned",
    "empty_slots", "canonical_units", "invalid_id_slots",
    "noncanonical_slots", "unresolved_slots", "player_army_ids",
    "allied_army_ids", "hostile_army_ids", "contact_hostile_army_ids",
    "retreating_hostile_army_ids", "units",
})
_MAILBOX_UNIT_KEYS = frozenset({
    "army_id", "owner_character_id", "current_province_id",
    "route_province_ids", "route_read_status", "route_source_count",
    "army_state_code", "in_combat", "retreating", "controllable",
    "war_side",
})
_H3937_EPISODE_RUN_ID = "native-29829-2bc2d599f7f9"
_H3937_ACTOR_CHARACTER_ID = 29_829


@dataclass(frozen=True)
class InventoryShapeCheck:
    valid: bool
    reason: str
    hostile_army_ids: tuple[int, ...] = ()
    contact_hostile_army_ids: tuple[int, ...] = ()
    date_or_action_authorized: bool = False


def _integer(value: Any, *, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _ids(value: Any) -> tuple[int, ...] | None:
    if not isinstance(value, list) or not all(_integer(v, minimum=1) for v in value):
        return None
    result = tuple(value)
    return result if result == tuple(sorted(set(result))) else None


def _route_complete(value: Any) -> bool:
    return type(value) is str and value in ("complete_empty", "complete_nonempty")


def _route_shape_complete(row: Mapping[str, Any]) -> bool:
    status = row.get("route_read_status")
    count = row.get("route_source_count")
    provinces = row.get("route_province_ids")
    if (not _route_complete(status) or not _integer(count) or
            not isinstance(provinces, list) or
            not all(_integer(province, minimum=1) for province in provinces) or
            len(provinces) != count):
        return False
    return (status == "complete_empty" and count == 0 or
            status == "complete_nonempty" and count > 0)


def validate_physical_army_inventory_shape_v1(
    receipt: Mapping[str, Any] | None,
    *,
    expected_date_raw: int,
    expected_war_id: int,
    expected_subject_army_id: int,
    expected_snapshot_id: str,
    expected_revision: int,
    expected_native_revision: int,
    expected_episode_run_id: str,
    expected_connection_generation: int,
    published_player_ids: list[int],
    published_allied_ids: list[int],
    published_enemy_ids: list[int],
    contact_request_ids: list[int],
    contact_result_ids: list[int],
) -> InventoryShapeCheck:
    def red(reason: str) -> InventoryShapeCheck:
        return InventoryShapeCheck(False, reason)

    if not isinstance(receipt, Mapping) or receipt.get("status") != "complete":
        return red("inventory_unavailable_or_partial")
    if receipt.get("source_build") != "CK3 1.19.0.6":
        return red("source_build_mismatch")
    exact = {
        "date_raw": expected_date_raw,
        "war_id": expected_war_id,
        "subject_army_id": expected_subject_army_id,
        "snapshot_id": expected_snapshot_id,
        "revision": expected_revision,
        "native_revision": expected_native_revision,
        "episode_run_id": expected_episode_run_id,
        "connection_generation": expected_connection_generation,
    }
    for key, expected in exact.items():
        actual = receipt.get(key)
        if type(actual) is not type(expected) or actual != expected:
            return red(f"{key}_mismatch")
    counts = (
        "storage_capacity", "slots_scanned", "empty_slots",
        "canonical_units", "invalid_id_slots", "noncanonical_slots",
        "unresolved_slots",
    )
    if any(not _integer(receipt.get(key)) for key in counts):
        return red("scan_counts_invalid")
    capacity = receipt["storage_capacity"]
    if (capacity <= 0 or capacity > 1_000_000 or
            receipt["slots_scanned"] != capacity or
            receipt["empty_slots"] + receipt["canonical_units"] +
            receipt["invalid_id_slots"] + receipt["noncanonical_slots"] != capacity or
            receipt["invalid_id_slots"] or receipt["noncanonical_slots"] or
            receipt["unresolved_slots"]):
        return red("scan_incomplete_or_unresolved")
    rows = receipt.get("units")
    if not isinstance(rows, list) or len(rows) != receipt["canonical_units"]:
        return red("unit_rows_incomplete")
    seen: set[int] = set()
    players: list[int] = []
    allies: list[int] = []
    physical: list[int] = []
    contact: list[int] = []
    retreating: list[int] = []
    subject_found = False
    for row in rows:
        if not isinstance(row, Mapping):
            return red("unit_row_invalid")
        army_id = row.get("army_id")
        if not _integer(army_id, minimum=1) or army_id in seen:
            return red("unit_id_invalid_or_duplicate")
        seen.add(army_id)
        side = row.get("war_side")
        if type(side) is not str or side not in {"allied", "hostile", "neutral"}:
            return red("war_side_unclassified")
        if not _integer(row.get("owner_character_id"), minimum=1) or not _integer(
            row.get("current_province_id"), minimum=1
        ):
            return red("owner_or_province_unresolved")
        if type(row.get("retreating")) is not bool:
            return red("retreat_state_unresolved")
        if type(row.get("controllable")) is not bool:
            return red("control_state_unresolved")
        state_code = row.get("army_state_code")
        if not _integer(state_code, minimum=1) or state_code > 9:
            return red("army_state_unresolved")
        if type(row.get("in_combat")) is not bool:
            return red("combat_state_unresolved")
        if side != "neutral" and (row["in_combat"] or
                                  (state_code == 6 and not row["retreating"])):
            return red("army_state_risk_unproven")
        if army_id == expected_subject_army_id:
            subject_found = side == "allied" and _route_shape_complete(row) and row["controllable"]
        if row["controllable"]:
            players.append(army_id)
        if side == "allied":
            allies.append(army_id)
        if side == "hostile":
            physical.append(army_id)
            if not _route_shape_complete(row):
                return red("hostile_route_incomplete")
            if row["retreating"] is False:
                contact.append(army_id)
            else:
                retreating.append(army_id)
    if not subject_found:
        return red("subject_unresolved")
    observed_players = _ids(receipt.get("player_army_ids"))
    observed_allies = _ids(receipt.get("allied_army_ids"))
    published_players = _ids(published_player_ids)
    published_allies = _ids(published_allied_ids)
    if any(value is None for value in (
        observed_players, observed_allies, published_players, published_allies
    )):
        return red("friendly_set_noncanonical")
    if observed_players != tuple(sorted(players)) or observed_players != published_players:
        return red("player_army_set_mismatch")
    if observed_allies != tuple(sorted(allies)) or observed_allies != published_allies:
        return red("allied_army_set_mismatch")
    hostile = _ids(receipt.get("hostile_army_ids"))
    requested = _ids(receipt.get("contact_hostile_army_ids"))
    excluded = _ids(receipt.get("retreating_hostile_army_ids"))
    published = _ids(published_enemy_ids)
    contact_request = _ids(contact_request_ids)
    contact_result = _ids(contact_result_ids)
    if any(value is None for value in (
        hostile, requested, excluded, published, contact_request, contact_result
    )):
        return red("hostile_set_noncanonical")
    if hostile != tuple(sorted(physical)) or hostile != published:
        return red("physical_published_set_mismatch")
    if not hostile:
        return red("hostile_set_empty")
    if excluded != tuple(sorted(retreating)) or excluded:
        return red("retreating_hostile_risk_unproven")
    if requested != tuple(sorted(contact)) or requested != contact_request or requested != contact_result:
        return red("contact_set_mismatch")
    # Shape-only validation cannot grant gameplay. Native provenance and the
    # formal risk/cash consumer are separate mandatory gates.
    return InventoryShapeCheck(True, "shape_valid_only", hostile, requested)


def validate_native_physical_inventory_mailbox_v1(
    native_receipt: Mapping[str, Any] | None,
    *,
    starting: Mapping[str, Any],
    current: Mapping[str, Any],
    horizon: Mapping[str, Any],
    query_sequence: int,
    subject_army_id: int,
    requested_hostiles: tuple[int, ...],
) -> InventoryShapeCheck:
    """Check the typed native mailbox payload against the driver-held frame.

    The caller must obtain native_receipt from its own accepted native pipe
    response. This is a read-only candidate check, never date admission.
    """
    def red(reason: str) -> InventoryShapeCheck:
        return InventoryShapeCheck(False, reason)

    if not isinstance(native_receipt, Mapping) or set(native_receipt) != _MAILBOX_NATIVE_KEYS:
        return red("mailbox_receipt_missing_or_extra_fields")
    rows = native_receipt.get("units")
    if not isinstance(rows, list) or any(
        not isinstance(row, Mapping) or set(row) != _MAILBOX_UNIT_KEYS
        for row in rows
    ):
        return red("mailbox_unit_rows_malformed")
    if not (
        starting.get("map_ready") is True
        and current.get("map_ready") is True
        and starting.get("paused") is True
        and current.get("paused") is True
        and type(native_receipt.get("mailbox_pump_epoch")) is int
        and native_receipt["mailbox_pump_epoch"] > 0
        and type(native_receipt.get("mailbox_thread_id")) is int
        and native_receipt["mailbox_thread_id"] > 0
        and native_receipt.get("mailbox_paused") is True
        and native_receipt.get("same_source_across_route") is True
        and type(native_receipt.get("mailbox_date_raw")) is int
        and native_receipt.get("mailbox_date_raw") == starting.get("date_raw")
        and type(query_sequence) is int
        and type(native_receipt.get("query_sequence")) is int
        and native_receipt.get("query_sequence") == query_sequence
        and type(native_receipt.get("native_revision")) is int
        and native_receipt.get("native_revision") == starting.get("native_revision")
    ):
        return red("mailbox_source_or_frame_mismatch")
    identity_keys = (
        "snapshot_id", "revision", "native_revision", "date_raw",
        "episode_run_id", "played_character", "active_wars", "player_armies",
        "map_ready", "paused", "episode_character_id", "active_event",
        "pending_character_interaction", "route_contact_horizon_supported",
    )
    if (any(key not in starting or key not in current for key in identity_keys) or
            any(starting[key] != current[key] for key in identity_keys)):
        return red("public_frame_changed")
    capability_keys = {key for key in set(starting) | set(current)
                       if key.endswith("_supported") or key == "capabilities"}
    if any(key not in starting or key not in current or
           starting[key] != current[key] for key in capability_keys):
        return red("capability_frame_changed")
    actor = starting.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    if type(actor_id) is not int or actor_id <= 0:
        return red("played_character_missing")
    if (starting.get("episode_run_id") == _H3937_EPISODE_RUN_ID and
            actor_id != _H3937_ACTOR_CHARACTER_ID):
        return red("h3937_actor_binding_mismatch")
    if starting.get("episode_character_id") != actor_id:
        return red("episode_actor_binding_mismatch")
    player_rows = starting.get("player_armies")
    subject_rows = [row for row in player_rows if isinstance(row, Mapping)
                    and row.get("army_id") == subject_army_id] if isinstance(player_rows, list) else []
    if (len(subject_rows) != 1 or
            subject_rows[0].get("owner_character_id") != actor_id or
            subject_rows[0].get("controllable") is not True):
        return red("played_character_subject_mismatch")
    start_diag = starting.get("diagnostics")
    current_diag = current.get("diagnostics")
    if not isinstance(start_diag, Mapping) or not isinstance(current_diag, Mapping):
        return red("connection_generation_missing")
    connection_generation = start_diag.get("connection_generation")
    if (type(connection_generation) is not int or connection_generation <= 0 or
            current_diag.get("connection_generation") != connection_generation):
        return red("connection_generation_mismatch")
    snapshot_id = starting.get("snapshot_id")
    episode_run_id = starting.get("episode_run_id")
    revision = starting.get("revision")
    native_revision = starting.get("native_revision")
    if not (
        type(snapshot_id) is str and snapshot_id and
        type(episode_run_id) is str and episode_run_id and
        type(revision) is int and revision > 0 and
        type(native_revision) is int and native_revision > 0
    ):
        return red("public_frame_token_missing")
    wars = starting.get("active_wars")
    if not isinstance(wars, list) or len(wars) != 1 or not isinstance(wars[0], Mapping):
        return red("war_scope_ambiguous")
    war = wars[0]
    war_id = war.get("war_id")
    if type(war_id) is not int or war_id <= 0:
        return red("war_id_missing")

    def ids_from_rows(value: Any) -> list[int] | None:
        if not isinstance(value, list):
            return None
        ids = [row.get("army_id") for row in value if isinstance(row, Mapping)]
        if len(ids) != len(value) or any(type(i) is not int or i <= 0 for i in ids):
            return None
        result = sorted(ids)
        return result if len(result) == len(set(result)) else None

    players = ids_from_rows(starting.get("player_armies"))
    allies = ids_from_rows(war.get("allied_armies"))
    enemies = ids_from_rows(war.get("enemy_armies"))
    if players is None or allies is None or enemies is None:
        return red("published_army_roster_malformed")
    contact_result = horizon.get("hostile_army_ids")
    if not isinstance(contact_result, list):
        return red("route_contact_result_missing")
    enriched = {
        **native_receipt,
        "snapshot_id": snapshot_id,
        "revision": revision,
        "episode_run_id": episode_run_id,
        "connection_generation": connection_generation,
    }
    return validate_physical_army_inventory_shape_v1(
        enriched,
        expected_date_raw=starting.get("date_raw"),
        expected_war_id=war_id,
        expected_subject_army_id=subject_army_id,
        expected_snapshot_id=snapshot_id,
        expected_revision=revision,
        expected_native_revision=native_revision,
        expected_episode_run_id=episode_run_id,
        expected_connection_generation=connection_generation,
        published_player_ids=players,
        published_allied_ids=allies,
        published_enemy_ids=enemies,
        contact_request_ids=list(requested_hostiles),
        contact_result_ids=contact_result,
    )

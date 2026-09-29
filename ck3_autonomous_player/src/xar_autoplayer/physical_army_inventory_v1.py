"""Strict shape check for a future native physical CUnit inventory receipt.

This module is intentionally not wired into formal date/action admission. A
matching JSON object is not proof of native provenance until the bridge binds
the receipt to its main-thread mailbox and same-frame snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


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

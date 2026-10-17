"""Factual same-realm refuge seeds; Native still decides route and contact."""

from __future__ import annotations


def _id(value: object) -> int | None:
    return value if type(value) is int and 0 < value <= 2**31 - 1 else None


def _unit_id(value: object) -> int | None:
    return value if type(value) is int and 0 <= value <= 2**31 - 1 else None


def direct_vassal_capital_province_ids(root: object) -> list[int] | None:
    """Return the complete observed direct-vassal *capital* set, never a map guess.

    A capital is only a destination seed.  This does not prove adjacency,
    movement legality, route safety, allegiance in the current war, or combat.
    """
    if not isinstance(root, dict) or root.get("status") != "available":
        return None
    readiness = root.get("readiness")
    actor = _id(root.get("player_character_id"))
    top_liege = _id(root.get("top_liege_character_id"))
    ids = root.get("direct_landed_vassal_character_ids")
    rows = root.get("related_character_contexts")
    if not (
        isinstance(readiness, dict)
        and readiness.get("direct_landed_vassals_ready") is True
        and readiness.get("related_character_contexts_ready") is True
        and actor is not None and top_liege is not None
        and isinstance(ids, list) and isinstance(rows, list)
    ):
        return None
    direct_ids = [_id(value) for value in ids]
    if None in direct_ids or len(direct_ids) != len(set(direct_ids)):
        return None
    found: dict[int, int | None] = {}
    for row in rows:
        if not isinstance(row, dict):
            return None
        if row.get("relationship_role") != "direct_landed_vassal":
            continue
        character_id = _id(row.get("character_id"))
        if (
            character_id not in direct_ids
            or character_id in found
            or row.get("immediate_liege_character_id") != actor
            or row.get("top_liege_character_id") != top_liege
        ):
            return None
        title = row.get("primary_title")
        if not (
            isinstance(title, dict)
            and _id(title.get("title_id")) is not None
            and type(title.get("tier_raw")) is int
            and 1 <= title["tier_raw"] <= 6
        ):
            return None
        raw_province = row.get("capital_province_id")
        province = _id(raw_province) if raw_province is not None else None
        if raw_province is not None and province is None:
            return None
        found[character_id] = province
    if set(found) != set(direct_ids):
        return None
    provinces = [province for province in found.values() if province is not None]
    if len(provinces) != len(set(provinces)):
        return None
    return sorted(provinces)


def same_frame_direct_vassal_refuge_scope(
    snapshot: object, cached_query: object,
) -> dict[str, object] | None:
    """Authorize only bounded capability advertisement from an exact cache."""
    if not isinstance(snapshot, dict) or not isinstance(cached_query, dict):
        return None
    diagnostics = snapshot.get("diagnostics")
    binding = cached_query.get("cache_binding")
    root = cached_query.get("campaign_root_context")
    actor = snapshot.get("actor_character_id")
    if actor is None and isinstance(snapshot.get("played_character"), dict):
        actor = snapshot["played_character"].get("character_id")
    if not (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and isinstance(diagnostics, dict)
        and isinstance(binding, dict)
        and all(binding.get(name) == snapshot.get(name) for name in (
            "snapshot_id", "revision", "native_revision", "date_raw"
        ))
        and binding.get("actor_character_id") == actor
        and binding.get("bridge_pid") == diagnostics.get("bridge_pid")
        and binding.get("connection_generation") == diagnostics.get("connection_generation")
        and isinstance(root, dict)
        and root.get("status") == "available"
        and root.get("snapshot_revision") == snapshot.get("native_revision")
        and root.get("date_raw") == snapshot.get("date_raw")
        and root.get("player_character_id") == actor
    ):
        return None
    candidates = direct_vassal_capital_province_ids(root)
    wars = snapshot.get("active_wars")
    armies = snapshot.get("player_armies")
    if not (
        candidates
        and isinstance(wars, list) and len(wars) == 1
        and isinstance(wars[0], dict)
        and wars[0].get("player_side") == "defender"
        and wars[0].get("player_is_primary_war_leader") is True
        and wars[0].get("war_objective_province_ids") == []
        and isinstance(armies, list)
    ):
        return None
    controlled = [row for row in armies if isinstance(row, dict) and row.get("controllable") is True]
    if len(controlled) != 1:
        return None
    army = controlled[0]
    army_id = _unit_id(army.get("army_id"))
    current = _id(army.get("current_province_id"))
    partition = root.get("held_title_partition")
    direct_counties = [
        row.get("capital_province_id") for row in partition
        if isinstance(row, dict)
        and isinstance(row.get("title"), dict)
        and row["title"].get("tier_raw") == 2
    ] if isinstance(partition, list) else []
    if not (
        army_id is not None and current is not None
        and direct_counties == [current]
        and army.get("owner_character_id") == actor
        and army.get("army_state") == "regular"
        and army.get("in_combat") is False
        and army.get("retreating") is False
        and army.get("route_province_ids") == []
        and army.get("move_target_province_id") is None
    ):
        return None
    enemies = wars[0].get("enemy_armies")
    if not isinstance(enemies, list):
        return None
    if not all(isinstance(row, dict) for row in enemies):
        return None
    hostile_ids = [_unit_id(row.get("army_id")) for row in enemies if row.get("retreating") is not True]
    if (
        not hostile_ids or len(hostile_ids) > 64
        or None in hostile_ids or len(hostile_ids) != len(set(hostile_ids))
    ):
        return None
    return {
        "army_id": army_id,
        "current_province_id": current,
        "candidate_province_ids": [value for value in candidates if value != current],
        "hostile_army_ids": sorted(hostile_ids),
    }

"""Consume current occupation-query siege rows without inventing objectives."""

from __future__ import annotations

from .war_contract import (
    START_ASSAULT_CAPABILITY, STOP_ASSAULT_CAPABILITY,
    WAR_OBJECTIVE_ASSAULT_CAPABILITY, start_assault_step, stop_assault_step,
)
from .war_occupation_targets_contract import (
    QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY,
    parse_query_war_occupation_targets_v1_step, war_occupation_query_scope,
)


def fresh_holding_siege_states(
    snapshot: dict[str, object], history: list[dict[str, object]],
) -> list[dict[str, object]]:
    """Reuse the existing occupation route consumer's same-frame binding."""
    if snapshot.get("paused") is not True:
        return []
    diagnostics = snapshot.get("diagnostics")
    generation = (diagnostics.get("connection_generation")
                  if isinstance(diagnostics, dict) else None)
    states: list[dict[str, object]] = []
    seen: set[int] = set()
    for row in reversed(history):
        war_id = parse_query_war_occupation_targets_v1_step(row.get("command"))
        if war_id is None or war_id in seen:
            continue
        seen.add(war_id)
        result = row.get("result")
        if row.get("ok") is not True or not isinstance(result, dict):
            continue
        try:
            actor_id, player_side = war_occupation_query_scope(snapshot, war_id)
        except ValueError:
            continue
        value = result.get("war_occupation_targets_v1")
        if not (
            isinstance(value, dict)
            and value.get("available") is True
            and value.get("collection_complete") is True
            and value.get("war_id") == war_id
            and value.get("actor_character_id") == actor_id
            and value.get("player_side") == player_side
            and value.get("snapshot_revision") == snapshot.get("native_revision")
            and value.get("date_raw") == snapshot.get("date_raw")
            and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and result.get("queried_revision") == snapshot.get("revision")
            and result.get("queried_native_revision") == snapshot.get("native_revision")
            and result.get("queried_connection_generation") == generation
            and result.get("queried_episode_run_id") == snapshot.get("episode_run_id")
        ):
            continue
        for holding in value["rows"]:
            states.append({
                "war_id": war_id, "province_id": holding["province_id"],
                "siege_observable": holding["siege_observable"],
                "active_siege": holding["active_siege"],
                "observation_source": "war_occupation_query",
            })
    return states


def holding_assault_steps(
    snapshot: dict[str, object], states: list[dict[str, object]],
    capabilities: set[str],
) -> set[str]:
    if (snapshot.get("paused") is not True
            or not {WAR_OBJECTIVE_ASSAULT_CAPABILITY,
                    QUERY_WAR_OCCUPATION_TARGETS_V1_CAPABILITY} <= capabilities):
        return set()
    steps: set[str] = set()
    for state in states:
        siege = state.get("active_siege")
        if (state.get("siege_observable") is not True
                or not isinstance(siege, dict)
                or siege.get("assault_observable") is not True
                or siege.get("player_army_besieging") is not True):
            continue
        if ({START_ASSAULT_CAPABILITY, STOP_ASSAULT_CAPABILITY} <= capabilities
                and siege.get("assault_in_progress") is False
                and siege.get("can_start_assault") is True):
            steps.add(start_assault_step(siege["siege_id"]))
        if (STOP_ASSAULT_CAPABILITY in capabilities
                and siege.get("assault_in_progress") is True
                and siege.get("can_stop_assault") is True):
            steps.add(stop_assault_step(siege["siege_id"]))
    return steps


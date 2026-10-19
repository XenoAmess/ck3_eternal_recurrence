"""Facts about opponents in the already published participating-war scope.

This projection makes no query and grants no procurement, movement or peace
permission. Published membership excludes wars which the native reader did not
identify as player-participant wars, and says nothing about unraised reserves.
"""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.war_contract import public_cunit_id
from .m5_observed_opportunity_selector import observed_frame
from .war_reinforcement_tradeoff_v1 import _count


def observe_participating_war_threats_v1(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Aggregate all published wars, preserving unknown counts and leadership.

    The Driver owns native-source qualification and current-frame strength
    cache validation. This consumer reuses those detached fields and retains
    each full ArmyID's WarIDs while counting the army at most once.
    """
    result: dict[str, object] = {
        "schema": "xar.participating-war-threat-observation.v1",
        "read_only": True,
        "status": "unavailable",
        "source_frame": None,
        "scope": "opposing armies in published player-participant wars only",
        "participating_war_ids": None,
        "primary_war_ids": None,
        "non_primary_war_ids": None,
        "leadership_unknown_war_ids": None,
        "enemy_army_memberships": None,
        "unique_enemy_army_ids": None,
        "observed_enemy_raised_soldiers": None,
        "unraised_or_future_enemy_reserves_bounded": False,
        "unpublished_liege_wars_covered": False,
        "defeat_title_transfer_verified": False,
        "battle_win_probability": None,
        "action_authorized": False,
    }

    def unavailable(reason: str) -> dict[str, object]:
        return {**result, "reason": reason}

    try:
        frame = observed_frame(snapshot)
    except (TypeError, ValueError):
        return unavailable("current_frame_identity_unavailable")
    result["source_frame"] = frame
    player = snapshot.get("played_character")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(player, Mapping) or player.get("alive") is not True):
        return unavailable("current_paused_living_player_required")
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return unavailable("published_active_war_array_unavailable")
    war_ids: list[int] = []
    primary: list[int] = []
    non_primary: list[int] = []
    unknown: list[int] = []
    memberships: dict[int, list[int]] = {}
    enemies: list[Mapping[str, object]] = []
    for war in wars:
        if (not isinstance(war, Mapping) or war.get("source") != "native"
                or type(war.get("war_id")) is not int or not 0 < war["war_id"] < 2**31
                or war["war_id"] in war_ids or war.get("player_side") not in {"attacker", "defender"}
                or (war.get("player_is_primary_war_leader") is not None
                    and type(war.get("player_is_primary_war_leader")) is not bool)):
            return unavailable("distinct_native_participating_war_identity_unavailable")
        identity = war["war_id"]
        war_ids.append(identity)
        leadership = war.get("player_is_primary_war_leader")
        (primary if leadership is True else non_primary if leadership is False else unknown).append(identity)
        rows = war.get("enemy_armies")
        if not isinstance(rows, list):
            return unavailable("published_enemy_army_array_unavailable")
        for army in rows:
            if not isinstance(army, Mapping):
                return unavailable("published_enemy_army_identity_unavailable")
            try:
                army_id = public_cunit_id(army.get("army_id"), "participating enemy army_id")
            except ValueError:
                return unavailable("published_enemy_army_identity_unavailable")
            if identity not in memberships.setdefault(army_id, []):
                memberships[army_id].append(identity)
            enemies.append(army)
    count = _count(enemies, snapshot=snapshot, role="active_war_enemy")
    return {
        **result, "status": "observed", "reason": "published_participating_war_scope_aggregated",
        "participating_war_ids": war_ids, "primary_war_ids": primary,
        "non_primary_war_ids": non_primary, "leadership_unknown_war_ids": unknown,
        "enemy_army_memberships": [{"army_id": army_id, "war_ids": ids}
                                   for army_id, ids in memberships.items()],
        "unique_enemy_army_ids": list(memberships),
        "observed_enemy_raised_soldiers": count,
        "strength_status": "available" if count is not None else "unavailable_or_conflicting",
        "leadership_scope_complete": not unknown,
    }

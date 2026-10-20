"""Recognize a current Native siege in the player's realm, without war authority.

This admits an observation/forecast candidate only. It does not authorize a move,
contact, spending, surrender, or a claim about the eventual transfer of titles.
"""
from __future__ import annotations


def _positive(value):
    return type(value) is int and value > 0


def nonleading_player_realm_siege_v1(snapshot, war, enemy):
    """Require the actual members of one complete current semantic frame.

    Identity membership deliberately rejects a detached historical War/Army row.
    The ordinary planner retains these objects when filtering active_wars. No
    missing subrealm fact is inferred from targets, army counts, or a CB name.
    """
    if not all(isinstance(row, dict) for row in (snapshot, war, enemy)):
        return False
    native = snapshot.get("native_revision")
    played = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    if not isinstance(played, dict) or not isinstance(diagnostics, dict):
        return False
    actor = played.get("character_id")
    if not (
        snapshot.get("source") == "injected-dll-named-pipe"
        and _positive(native) and snapshot.get("snapshot_id") == f"native:{native}"
        and type(snapshot.get("revision")) is int and snapshot["revision"] >= 0
        and type(snapshot.get("date_raw")) is int
        and isinstance(snapshot.get("episode_run_id"), str) and snapshot["episode_run_id"]
        and snapshot.get("paused") is True and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and played.get("source") == "native" and _positive(actor)
        and played.get("alive") is True
        and diagnostics.get("connected") is True
        and _positive(diagnostics.get("bridge_pid"))
        and type(diagnostics.get("connection_generation")) is int
        and diagnostics["connection_generation"] >= 0
    ):
        return False
    wars = snapshot.get("active_wars")
    enemies = war.get("enemy_armies")
    score = war.get("player_relative_war_score")
    return bool(
        isinstance(wars, list) and any(row is war for row in wars)
        and isinstance(enemies, list) and any(row is enemy for row in enemies)
        and war.get("source") == "native" and _positive(war.get("war_id"))
        and war.get("player_side") == "defender"
        and war.get("player_is_primary_war_leader") is False
        and type(score) is int and -100 < score < 100
        and enemy.get("source") == "native" and _positive(enemy.get("army_id"))
        and _positive(enemy.get("owner_character_id"))
        and enemy["owner_character_id"] != actor and enemy.get("controllable") is False
        and enemy.get("army_state") == "sieging"
        and type(enemy.get("army_state_code")) is int and enemy["army_state_code"] == 3
        and enemy.get("in_combat") is False and enemy.get("retreating") is False
        and _positive(enemy.get("current_province_id"))
        and enemy.get("siege_province_in_player_subrealm") is True
        and "move_target_province_id" in enemy and enemy["move_target_province_id"] is None
        and enemy.get("route_province_ids") == []
        and enemy.get("route_read_status") == "complete_empty"
    )


def nonleading_player_realm_siege_war_v1(snapshot, war):
    if not isinstance(war, dict) or not isinstance(war.get("enemy_armies"), list):
        return False
    return any(nonleading_player_realm_siege_v1(snapshot, war, enemy)
               for enemy in war["enemy_armies"])

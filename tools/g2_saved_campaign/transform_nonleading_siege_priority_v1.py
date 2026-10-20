"""Exact reversible future Strategy splice; the large candidate stays in RAM."""
from __future__ import annotations

import hashlib

BASE_SHA256 = "45c164297b90b32203e7860b4a7735cfa65c5ca1db7141e898d15395d2e47e78"
IMPORT_OLD = "from .war_termination_query_cadence_v1 import war_termination_query_policy_defer_v1\n"
IMPORT_NEW = IMPORT_OLD + (
    "from .nonleading_player_realm_siege_v1 import (\n"
    "    nonleading_player_realm_siege_v1, nonleading_player_realm_siege_war_v1,\n)\n"
)
MOVING_OLD = '''                war.get("player_side") == "defender"
                and war.get("player_is_primary_war_leader") is True
                and isinstance(war.get("enemy_armies"), list)
'''
MOVING_NEW = '''                war.get("player_side") == "defender"
                and (war.get("player_is_primary_war_leader") is True
                     or nonleading_player_realm_siege_war_v1(snapshot, war))
                and isinstance(war.get("enemy_armies"), list)
'''
SCOPE_OLD = '''    """Require a native tie to the defended objective or player realm."""
    province_id = _native_int(enemy.get("current_province_id"))
'''
SCOPE_NEW = '''    """Require a native tie to the defended objective or player realm."""
    if war.get("player_is_primary_war_leader") is False:
        return nonleading_player_realm_siege_v1(snapshot, war, enemy)
    province_id = _native_int(enemy.get("current_province_id"))
'''
RELIEF_OLD = '''            and war.get("player_side") == "defender"
            and war.get("player_is_primary_war_leader") is True
            and _native_int(war.get("war_id")) is not None
'''
RELIEF_NEW = '''            and war.get("player_side") == "defender"
            and (war.get("player_is_primary_war_leader") is True
                 or nonleading_player_realm_siege_war_v1(snapshot, war))
            and _native_int(war.get("war_id")) is not None
'''
REASON_OLD = '"an enemy siege is visible in a primary defensive war, "'
REASON_NEW = '"an enemy siege is visible in a qualifying defensive war, "'
PREVIEW_OLD = '''        if preview_target != target:
            return baseline
    if phase in {"native_war_pursuit", "native_war_pursuit_progress"}:
'''
PREVIEW_NEW = '''        if preview_target != target:
            candidate_war = next(
                (war for war in active_wars if isinstance(war, dict)
                 and war.get("war_id") == war_id), None
            )
            if not (
                nonleading_player_realm_siege_war_v1(snapshot, candidate_war)
                and (
                    (phase == "native_war_route_preview"
                     and type(preview_target) is int and preview_target > 0
                     and baseline.get("selected_step")
                     == preview_move_army_step(army_id, preview_target))
                    or (phase == "native_war_route_preview_unsupported"
                        and baseline.get("selected_step") is None)
                )
            ):
                return baseline
    if phase in {"native_war_pursuit", "native_war_pursuit_progress"}:
'''
HUNKS = ((IMPORT_OLD, IMPORT_NEW), (MOVING_OLD, MOVING_NEW),
         (SCOPE_OLD, SCOPE_NEW), (RELIEF_OLD, RELIEF_NEW),
         (REASON_OLD, REASON_NEW), (PREVIEW_OLD, PREVIEW_NEW))


def transform_strategy_bytes(source, *, inverse=False):
    if not isinstance(source, bytes):
        raise ValueError("Strategy input must be raw bytes")
    if not inverse and hashlib.sha256(source).hexdigest() != BASE_SHA256:
        raise ValueError("Strategy is not the frozen reviewed preimage")
    text = source.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    for before, after in reversed(HUNKS) if inverse else HUNKS:
        old, new = (after, before) if inverse else (before, after)
        old, new = old.replace("\n", newline), new.replace("\n", newline)
        if text.count(old) != 1:
            raise ValueError("Strategy exact hunk occurrence differs")
        text = text.replace(old, new, 1)
    result = text.encode("utf-8")
    if inverse and hashlib.sha256(result).hexdigest() != BASE_SHA256:
        raise ValueError("Strategy inverse does not restore the original bytes")
    return result

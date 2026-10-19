"""Source-bound independence semantics; title enumeration and outcomes stay unknown.

These pure adapters consume existing query results. They neither evaluate an
engine effect nor choose or authorize a response, peace offer or expenditure.
"""
from __future__ import annotations

from collections.abc import Mapping

from .bridge.version_identity import CK3_12004
from .bridge.war_occupation_targets_contract import normalize_war_occupation_targets_v1
from .m5_observed_opportunity_selector import observed_frame

SOURCE_HASHES = {
    "common/casus_belli_types/00_civil_war.txt": "a9f5d844413bd7acfd4d4b1611877ac34e78eb293f309c0e7a41f27aca3a0047",
    "common/scripted_effects/00_war_effects.txt": "f811d12ccb11f3aae2f61b234e930e20880be9b7c065bb9f4557400bd711722b",
    "common/character_interactions/00_character_interactions.txt": "e66fc0ccaa69e84bb6b36c2c3a4cac1e8f8d871d70cf7234724a0150e2ff8a4b",
}
_CIVIL, _HELPER, _INTERACTION = SOURCE_HASHES


def reviewed_independence_rule_v1(definition_key: str, source_hashes: Mapping[str, str]) -> dict[str, object]:
    """Return reviewed conditional script semantics, not current legality."""
    if not isinstance(definition_key, str):
        return {"status": "unavailable", "reason": "definition_not_reviewed"}
    if definition_key in {"independence_war", "independence_faction_war"}:
        required = (_CIVIL, _HELPER)
        selector = ("primary_attacker" if definition_key == "independence_war" else
                    "current_joined_faction_members_else_flagged_war_attackers")
        effect = "change_liege_or_become_independent"
        trigger = "attacker_victory"
    elif definition_key == "grant_independence_interaction":
        required = (_INTERACTION,)
        selector, effect, trigger = "recipient", "becomes_independent", "on_accept"
    else:
        return {"status": "unavailable", "reason": "definition_not_reviewed"}
    contract = {path: SOURCE_HASHES[path] for path in required}
    if not isinstance(source_hashes, Mapping) or any(source_hashes.get(path) != sha for path, sha in contract.items()):
        return {"status": "unavailable", "reason": "reviewed_source_contract_not_matched"}
    return {"status": "source_reviewed", "definition_key": definition_key,
            "source_contract": contract, "effect_trigger": trigger,
            "affected_principal_selector": selector, "territorial_effect": effect,
            "targeted_title_ids_are_effect_enumeration": False,
            "helper_branch": ("independent_current_liege: becomes_independent; otherwise: change_liege to current_liege.liege"
                              if effect == "change_liege_or_become_independent" else None),
            "loaded_definition_verified": False, "current_legality_verified": False,
            "actual_title_or_vassal_change_verified": False, "action_authorized": False}


def _positive(value):
    return type(value) is int and value > 0


def _occupation_roles(snapshot, war, result, frame, generation):
    if (not isinstance(result, Mapping) or result.get("accepted") is not True
            or result.get("read_only") is not True or result.get("status") != "available"
            or result.get("step") != f"query-war-occupation-targets-v1-{war['war_id']}"
            or not _positive(result.get("query_sequence"))
            or result.get("queried_snapshot_id") != frame["snapshot_id"]
            or result.get("queried_revision") != frame["revision"]
            or result.get("queried_native_revision") != frame["native_revision"]
            or result.get("queried_connection_generation") != generation
            or result.get("queried_episode_run_id") != frame["episode_run_id"]):
        return None
    try:
        value = normalize_war_occupation_targets_v1(result.get("war_occupation_targets_v1"),
            expected_war_id=war["war_id"], expected_actor_character_id=frame["played_character_id"],
            expected_snapshot_revision=frame["native_revision"], expected_date_raw=frame["date_raw"],
            expected_player_side=war["player_side"])
    except (TypeError, ValueError):
        return None
    if (value.get("available") is not True or value.get("collection_complete") is not True
            or value.get("game_version") != CK3_12004.game_version
            or value.get("executable_sha256") != CK3_12004.executable_sha256.lower()):
        return None
    attacker, defender = value["primary_attacker_character_id"], value["primary_defender_character_id"]
    leader = attacker if war["player_side"] == "attacker" else defender
    opponent = defender if war["player_side"] == "attacker" else attacker
    if (not _positive(attacker) or not _positive(defender) or attacker == defender
            or war.get("primary_opponent_character_id") != opponent
            or (frame["played_character_id"] == leader) is not war.get("player_is_primary_war_leader")):
        return None
    return {"primary_attacker_character_id": attacker, "primary_defender_character_id": defender,
            "query_sequence": result["query_sequence"]}


def observe_current_independence_war_consequences_v1(snapshot: Mapping[str, object], *, war_id: int,
        source_hashes: Mapping[str, str], occupation_result=None, campaign_root=None) -> dict[str, object]:
    """Bind reviewed selectors to a current native CB; retain missing extent.

    A source-known effect selector can be established while the current faction
    membership, selected subrealm titles and eventual engine result remain unknown.
    """
    out = {"schema": "xar.independence-territorial-consequences.v1", "status": "unavailable",
           "source_frame": None, "war_id": war_id, "action_authorized": False,
           "affected_title_ids": None, "title_extent_complete": False,
           "title_holder_transfer_verified": False, "war_resolution_verified": False,
           "postwar_material_verified": False}

    def unavailable(reason):
        return {**out, "reason": reason}

    try:
        frame = observed_frame(snapshot)
    except (TypeError, ValueError):
        return unavailable("current_frame_identity_unavailable")
    out["source_frame"] = frame
    player, diagnostics = snapshot.get("played_character"), snapshot.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, Mapping) else None
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(player, Mapping) or player.get("alive") is not True or not _positive(generation)):
        return unavailable("current_paused_living_actor_and_connection_required")
    wars = snapshot.get("active_wars")
    matches = [w for w in wars if isinstance(w, Mapping) and w.get("war_id") == war_id] if isinstance(wars, list) else []
    if (len(matches) != 1 or type(war_id) is not int or not 0 <= war_id < 2**31
            or matches[0].get("source") != "native" or matches[0].get("player_side") not in {"attacker", "defender"}
            or type(matches[0].get("player_is_primary_war_leader")) is not bool):
        return unavailable("unique_current_native_war_required")
    war = matches[0]
    options = snapshot.get("war_termination_options")
    matches = [r for r in options if isinstance(r, Mapping) and r.get("war_id") == war_id] if isinstance(options, list) else []
    if len(matches) != 1:
        return unavailable("unique_current_cb_query_required")
    cb_result = matches[0]
    if (cb_result.get("source") != "native" or not _positive(cb_result.get("query_sequence"))
            or cb_result.get("queried_snapshot_id") != frame["snapshot_id"]
            or cb_result.get("queried_revision") != frame["revision"]
            or cb_result.get("queried_native_revision") != frame["native_revision"]
            or cb_result.get("queried_connection_generation") != generation
            or cb_result.get("episode_run_id") != frame["episode_run_id"]
            or any(cb_result.get(key) != war.get(key) for key in
                   ("player_side", "player_is_primary_war_leader", "player_relative_war_score"))
            or cb_result.get("active_casus_belli_present") is not True):
        return unavailable("cb_query_not_bound_to_current_participant_frame")
    cb = cb_result.get("active_casus_belli_identity")
    if not isinstance(cb, Mapping) or type(cb.get("database_index")) is not int or cb["database_index"] < 0:
        return unavailable("native_cb_identity_unavailable")
    rule = reviewed_independence_rule_v1(cb.get("canonical_key"), source_hashes)
    if rule.get("status") != "source_reviewed" or rule["effect_trigger"] != "attacker_victory":
        return unavailable("current_war_cb_source_profile_unavailable")
    roles = _occupation_roles(snapshot, war, occupation_result, frame, generation)
    normal = cb["canonical_key"] == "independence_war"
    principals = [roles["primary_attacker_character_id"]] if normal and roles else None
    root = campaign_root
    if (not isinstance(root, Mapping) or root.get("status") != "available"
            or root.get("player_character_id") != frame["played_character_id"]
            or root.get("snapshot_revision") != frame["native_revision"] or root.get("date_raw") != frame["date_raw"]):
        root = None
    targets = war.get("targeted_title_ids")
    targets = list(targets) if isinstance(targets, list) and all(type(t) is int and t >= 0 for t in targets) else None
    held = root.get("held_title_partition") if root else None
    held_ids = {r["title"]["title_id"] for r in held if isinstance(r, Mapping)
                and isinstance(r.get("title"), Mapping) and type(r["title"].get("title_id")) is int} if isinstance(held, list) else None
    return {**out, "status": "source_bound_current_war_observed", "source_rule": rule,
            "native_cb_identity": dict(cb), "cb_query_sequence": cb_result["query_sequence"],
            "observed_primary_roles": roles, "selected_principal_character_ids": principals,
            "principal_selection_complete": normal and roles is not None,
            "targeted_title_ids": targets,
            "directly_held_target_identity_overlap": sorted(held_ids.intersection(targets)) if held_ids is not None and targets is not None else None,
            "loss_extent_is_targeted_title_list": False,
            "conditional_effect_scope": ("selected primary attacker's liege/subrealm relation; exact title set unobserved" if normal else
                                         "current joined-faction members, otherwise flagged war attackers; selector inputs unobserved"),
            "unresolved": ["exact_affected_subrealm_title_ids", "actual_engine_resolution", "loaded_definition_identity"]
                + ([] if normal and roles else ["current_affected_principal_selection"]),
            "defender_realm_shrinkage_verified": False,
            "direct_title_holder_loss_inferred_from_target_overlap": False}

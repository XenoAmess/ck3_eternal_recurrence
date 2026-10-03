"""Read-only comparison of the currently observed populist ultimatum."""

from __future__ import annotations

import copy
from collections.abc import Mapping

from ..bridge.event_window_context_contract import normalize_current_event_window_context_v1
from ..bridge.player_faction_alerts_contract import normalize_player_faction_alerts_v1
from .builds import SUPPORTED_CK3_EXE_SHA256, event_context_build
from .records_faction_demand1001_12003 import EVENT_KEY, SAVED_SCOPE_TYPES, SOURCE_HASHES


def _identity(scope: object, kind: str, field: str) -> int | None:
    if not isinstance(scope, Mapping):
        return None
    identity = scope.get("typed_identity")
    if not isinstance(identity, Mapping):
        return None
    value = identity.get(field)
    if (scope.get("status") == "available" and identity.get("status") == "available"
            and identity.get("kind") == kind and isinstance(value, int)
            and not isinstance(value, bool)):
        return value
    return None


def recognize_faction_demand1001_projection_v1(
    event_context: Mapping[str, object], *, played_character_id: object,
    snapshot_option_count: object,
) -> dict[str, object]:
    """Recognize seven saved roles and observed native2/3 without choosing."""
    raw_scopes = event_context.get("saved_scopes")
    scopes = {row.get("name"): row.get("scope") for row in raw_scopes
              if isinstance(row, Mapping)} if isinstance(raw_scopes, list) else {}
    raw_options = event_context.get("options")
    options = [row for row in raw_options if isinstance(row, Mapping)] if isinstance(raw_options, list) else []
    root = _identity(event_context.get("root_scope"), "character", "character_id")
    leader = _identity(scopes.get("peasant_leader"), "character", "character_id")
    target = _identity(scopes.get("faction_target"), "character", "character_id")
    named_leader = _identity(scopes.get("faction_leader"), "character", "character_id")
    actor_valid = isinstance(played_character_id, int) and not isinstance(played_character_id, bool) and played_character_id > 0
    checks = {
        "exact_build": event_context_build(dict(event_context)) == "1.20.0.3",
        "event_definition": event_context.get("status") == "available" and event_context.get("event_definition_key") == EVENT_KEY,
        "player_root_target": actor_valid and root == target == played_character_id,
        "leader_roles": leader is not None and leader > 0 and leader == named_leader and leader != root,
        "saved_role_names": len(scopes) == 7 and set(scopes) == set(SAVED_SCOPE_TYPES),
        "saved_role_types": all(isinstance(scopes.get(name), Mapping)
            and scopes[name].get("type_key") == type_key for name, type_key in SAVED_SCOPE_TYPES.items()),
        "authored_option_count": type(snapshot_option_count) is int and snapshot_option_count == 4,
        "visible_native_options": len(options) == 2 and {row.get("native_option_index") for row in options} == {2, 3}
            and all(row.get("shown") is True and row.get("enabled") is True for row in options),
    }
    return {
        "status": "recognized" if all(checks.values()) else "blocked",
        "checks": checks, "failed_checks": sorted(key for key, value in checks.items() if not value),
        "native_option_mapping": [{"native_option_index": row.get("native_option_index"),
            "api_option_number": row.get("native_option_index") + 1,
            "rendered_index": row.get("rendered_index"), "resolved_name": row.get("resolved_name")}
            for row in options if type(row.get("native_option_index")) is int and row.get("native_option_index") in {2, 3}],
        "selected_option_number": None, "selected_native_option_index": None,
        "automatic_selection": False,
    }


def build_faction_demand1001_decision_context_v1(
    event_context: Mapping[str, object], faction_alerts: Mapping[str, object], *,
    played_character_id: int, expected_event_instance_id: int,
    expected_date_raw: int, expected_event_snapshot_revision: int,
    expected_faction_snapshot_revision: int,
) -> dict[str, object]:
    """Bind separately revised observations of one paused date and compare.

    Each read has its own native revision. The caller supplies both expected
    revisions; equality between the sequential read revisions is not assumed.
    No option is selected or submitted, including when county losses are ready.
    """
    context: dict[str, object] = {
        "schema": "xar.ck3.faction-demand1001-decision-context/v1", "status": "blocked",
        "event_definition_key": EVENT_KEY, "ck3_build": "1.20.0.3",
        "ck3_exe_sha256": SUPPORTED_CK3_EXE_SHA256["1.20.0.3"],
        "source_sha256": dict(SOURCE_HASHES),
        "binding": {"actor_character_id": played_character_id,
            "event_instance_id": expected_event_instance_id, "date_raw": expected_date_raw,
            "event_snapshot_revision": expected_event_snapshot_revision,
            "faction_snapshot_revision": expected_faction_snapshot_revision},
        "binding_ready": False, "readonly_review_ready": False,
        "complete_acceptance_outcome_ready": False, "action_execution_ready": False,
        "selected_option_number": None, "selected_native_option_index": None,
        "automatic_selection": False, "war_execution_authorized": False,
        "missing_observations": [], "unavailable_reason": None,
        "acceptance": None, "refusal": None,
    }
    try:
        event = normalize_current_event_window_context_v1(dict(event_context),
            expected_event_instance_id=expected_event_instance_id,
            expected_date_raw=expected_date_raw,
            expected_snapshot_revision=expected_event_snapshot_revision)
        factions = normalize_player_faction_alerts_v1(dict(faction_alerts),
            expected_date_raw=expected_date_raw,
            expected_snapshot_revision=expected_faction_snapshot_revision,
            expected_game_version="1.20.0.3",
            expected_executable_sha256=SUPPORTED_CK3_EXE_SHA256["1.20.0.3"])
    except ValueError as error:
        context.update(unavailable_reason="input_frame_contract_invalid", input_error=str(error))
        return context
    recognition = recognize_faction_demand1001_projection_v1(event,
        played_character_id=played_character_id, snapshot_option_count=4)
    context["recognition"] = recognition
    if recognition["status"] != "recognized":
        context["unavailable_reason"] = "current_populist_projection_does_not_match"
        return context
    options = {row["native_option_index"]: row for row in recognition["native_option_mapping"]}
    context["refusal"] = {**options[3], "effect": "faction_start_war",
        "source_outcome": "Saved faction requests a war against faction_target using target_title",
        "war_execution_authorized": False, "actual_war_id": None, "exact_cb_key": None,
        "notification": "Conditional popular_faction_vassal_targets recipients receive faction_demand.0099",
        "execution_ready": False, "stress_effect": "none_explicit_in_reviewed_native3_or_common_after"}
    scopes = {row["name"]: row["scope"] for row in event["saved_scopes"]}
    faction_id = _identity(scopes["faction"], "faction", "faction_id")
    leader = _identity(scopes["peasant_leader"], "character", "character_id")
    titles = {name: _identity(scopes[name], "landed_title", "title_id")
              for name in ("peasant_county", "target_title", "new_title")}
    missing = []
    if faction_id is None:
        missing.append("saved_faction_full_id")
    for name, title_id in titles.items():
        identity = scopes[name]["typed_identity"]
        named_null = identity == {"status": "unavailable", "reason": "landed_title_scope_is_null"}
        if title_id is None and not (name == "new_title" and named_null):
            missing.append(f"saved_{name}_full_id")
    context["binding"].update(faction_id=faction_id, leader_character_id=leader,
        target_character_id=played_character_id, title_ids=titles,
        new_title_native_null=titles["new_title"] is None and "saved_new_title_full_id" not in missing)
    context["refusal"]["target_title_id"] = titles["target_title"]
    if missing:
        context.update(status="partial", unavailable_reason="saved_scope_identity_observations_pending",
            missing_observations=missing)
        return context
    rows = factions.get("targeting_factions")
    matches = [row for row in rows if row["faction_id"] == faction_id] if isinstance(rows, list) else []
    if len(matches) != 1:
        context.update(unavailable_reason="saved_full_faction_id_not_in_observed_targeting_rows")
        return context
    faction = matches[0]
    matches_roles = (factions["player_character_id"] == played_character_id
        and faction["target_character_id"] == played_character_id
        and faction["leader_character_id"] == leader
        and faction["faction_type_key"] == "populist_faction"
        and titles["peasant_county"] in faction["county_member_title_ids"])
    if not matches_roles:
        context["unavailable_reason"] = "saved_faction_actor_leader_or_member_county_mismatch"
        return context
    context["binding_ready"] = True
    context["faction_material"] = {name: copy.deepcopy(faction[name]) for name in (
        "power", "power_threshold", "discontent", "faction_at_war", "county_member_title_ids")}
    impact = faction.get("surrender_impact")
    context["acceptance"] = {**options[2], "effect": "successful_popular_revolt_outcome_effect",
        "prestige_level_delta": -1,
        "dread": {"condition": "current_dread_gt_zero", "script_delta": -20, "observed_net_delta": None},
        "ordinary_transfer_parameters": {"add_claim_on_loss": True, "take_baronies": False},
        "stress_effect": "none_explicit_in_reviewed_native2_or_common_after",
        "execution_ready": False, "loss_observation": copy.deepcopy(impact),
        "county_loss_ready": False,
        "kingdom_outcome_boundary": "Receiver, its capital and existing direct counties are not final post-transfer observations"}
    if not isinstance(impact, Mapping) or impact.get("status") != "available":
        context.update(status="partial", unavailable_reason="current_surrender_impact_observation_pending",
            missing_observations=["matched_faction_surrender_impact"])
        return context
    loss_ready = (impact["government_allows_state_faith"] is False
        and impact["ordinary_branch_title_sets_ready"] is True
        and impact["county_loss_complete"] is True)
    context["acceptance"].update(county_loss_ready=loss_ready,
        realm_county_loss_ids=[row["title_id"] for row in impact["seized_counties"]] if loss_ready else None,
        realm_duchy_loss_ids=[row["title_id"] for row in impact["seized_duchies"]] if loss_ready else None,
        player_direct_county_and_duchy_loss_ids=list(impact["player_direct_title_loss_ids"]) if loss_ready else None,
        player_remaining_direct_county_title_ids=list(impact["player_remaining_direct_county_title_ids"]) if loss_ready else None,
        conditional_kingdom_candidates=copy.deepcopy(impact["kingdoms"]) if loss_ready else None)
    context.update(status="available" if loss_ready else "partial",
        readonly_review_ready=loss_ready,
        complete_acceptance_outcome_ready=loss_ready and impact["kingdom_outcome_complete"],
        unresolved_branches=list(impact["unresolved_branches"]))
    if not loss_ready:
        context.update(unavailable_reason="surrender_branch_or_county_observation_pending",
            missing_observations=["state_faith_transfer_outcome" if impact["government_allows_state_faith"] is True
                else "ordinary_branch_complete_county_loss"])
    return context

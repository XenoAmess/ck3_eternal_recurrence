"""Canonical native CK3 war and army state shared by MCP and the planner."""

from __future__ import annotations

from .native_maa_recruitment_inputs_contract import normalize_native_maa_recruitment_inputs_v1
from .owned_regiments_v1 import normalize_owned_regiments_v1
from .siege_membership_contract import normalize_siege_province_unit_occurrences

from .army_replenishment_records_contract import normalize_regiment_replenishment_records_v1
from .army_fixed_chunk0_preparation_contract import normalize_fixed_chunk0_preparation_inputs_v1

from .army_update_clock_contract import normalize_army_update_clock_v1
from .army_monthly_loss_budget_inputs_contract import normalize_monthly_loss_budget_inputs_v1
from .army_monthly_caller_effect_inputs_contract import normalize_monthly_caller_effect_inputs_v1
from .army_daily_queue_inputs_contract import normalize_monthly_daily_queue_inputs_v1
from .army_manager_cleanup_inputs_contract import normalize_monthly_first_removal_cleanup_inputs_v1
from .army_current_helper_domain_inputs_contract import normalize_monthly_current_helper_domain_inputs_v1
from .army_current_helper_point_store_inputs_contract import normalize_monthly_current_helper_point_store_inputs_v1
from .army_current_province_supply_contributors_contract import normalize_current_province_supply_contributors_v1
from .army_province_besieging_contributors_contract import normalize_current_province_besieging_contributors_v1
from .army_current_land_resupply_contract import normalize_current_land_resupply_v1
from .army_current_land_supply_rate_contract import normalize_current_land_supply_rate_inputs_v1
from .army_current_fleet_supply_tick_inputs_contract import normalize_current_fleet_supply_tick_inputs_v1
from .army_current_daily_supply_dispatch_inputs_contract import normalize_current_daily_supply_dispatch_inputs_v1
from .army_current_month_first_refill_call_inputs_contract import normalize_current_month_first_refill_call_inputs_v1
from .army_scoped_ordered_refill_contract import normalize_scoped_ordered_refill_inputs_v1
from .army_daily_assault_active_table_contract import normalize_current_daily_assault_table_v1
from .army_daily_assault_roster_admission_contract import normalize_current_daily_assault_roster_admission_v1
from .army_pre_date_dated_append_contract import normalize_current_pre_date_dated_append_inputs_v1
from .army_pre_date_character_prefix_contract import normalize_current_pre_date_character_prefix_inputs_v1
from .army_current_post_admission_refresh_contract import normalize_current_post_admission_refresh_inputs_v1
from .army_current_condition30_inputs_contract import normalize_current_army_condition30_inputs_v1
from .army_current_flag20_inputs_contract import normalize_current_army_flag20_inputs_v1
from .army_current_disembark_penalty_contract import normalize_current_disembark_penalty_v1
from .army_current_flag21_inputs_contract import normalize_current_army_flag21_inputs_v1
from .army_current_selected_title_holder_owner_relation_contract import (
    normalize_current_selected_title_holder_owner_relation_v1,
)
from .army_current_flag31_inputs_contract import normalize_current_army_flag31_inputs_v1
from .army_current_combat_roles_phase_inputs_contract import normalize_current_army_combat_roles_phase_inputs_v1
from .army_current_candidate_detachment_mapper_contract import normalize_current_candidate_detachment_mapper_inputs_v1
from .army_current_detachment_data_contract import normalize_current_detachment_data_inputs_v1
from .army_future_daily_supply_schedule_contract import normalize_future_daily_supply_schedule_inputs_v1
from .army_source_derived_next_daily_supply_frame_contract import normalize_source_derived_next_daily_supply_frame_inputs_v1
from .army_current_unit_new_date_schedule_inputs_contract import normalize_current_unit_new_date_schedule_inputs_v1
from .army_current_unit_new_date_entry_normalization_projection import normalize_current_unit_new_date_callback_entry_inputs_v1
from .army_current_detachment_callback_inputs_contract import normalize_current_detachment_callback_inputs_v1
from .army_current_detachment_store_inputs_contract import normalize_current_detachment_store_inputs_v1
from .army_current_character_detachment_inputs_contract import normalize_current_character_detachment_inputs_v1
from .army_pre_date_pending_update_contract import normalize_current_pre_date_pending_update_inputs_v1
from .army_ordered_besieging_refill_contract import normalize_ordered_besieging_refill_inputs_v1
from .army_daily_assault_loss_inputs_contract import normalize_current_daily_assault_loss_inputs_v1
from .army_current_assault_removal_reference_contract import normalize_current_assault_removal_reference_inputs_v1
from .army_ordered_besieging_fixed_chunk0_preparation_contract import normalize_ordered_besieging_fixed_chunk0_preparation_inputs_v1
from .army_county_entry_inputs_contract import normalize_army_county_entry_inputs_v1
from .battle_native_owner_recall_inputs_contract import (
    normalize_battle_native_owner_recall_inputs_v1,
)

from .public_unit_contract import (
    canonical_public_cunit_decimal,
    optional_public_cunit_id,
    public_cunit_id,
)

from .player_claims_contract import (
    QUERY_PLAYER_CLAIMS_V1_CAPABILITY,
    QUERY_PLAYER_CLAIMS_V1_STEP_PREFIX,
    normalize_player_claims_v1,
    parse_query_player_claims_v1_step,
    player_claims_query_actor,
    player_claims_title_ids,
    query_player_claims_v1_step,
)
from .title_holder_contract import (
    QUERY_TITLE_HOLDER_V1_CAPABILITY,
    QUERY_TITLE_HOLDER_V1_STEP_PREFIX,
    parse_query_title_holder_v1_step,
    query_title_holder_v1_step,
)

from collections.abc import Iterable

from .version_identity import (
    CK3_11906, CK3_12002, CK3_12003, CK3_12004, NativeBuildIdentity, require_exact_native_build,
)

from xar_autoplayer.bridge.raiktor_war_bound_regiment_contract import (
    normalize_raiktor_war_bound_regiment,
)


MOVE_ARMY_CAPABILITY = "game.command.move-army-N-to-N"
HALT_ARMY_CAPABILITY = "game.command.halt-army-N"
PREVIEW_MOVE_ARMY_CAPABILITY = "game.command.preview-move-army-N-to-N"
QUERY_ROUTE_CONTACT_HORIZON_CAPABILITY = (
    "game.command.query-route-contact-horizon-v1-N"
)
ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX = (
    "advance-route-contact-horizon-v1-"
)
DISBAND_ARMY_CAPABILITY = "game.command.disband-army-N"
SPLIT_ARMY_HALF_CAPABILITY = "game.command.split-army-half-N"
MERGE_ARMIES_CAPABILITY = "game.command.merge-armies-N-with-N"
START_ASSAULT_CAPABILITY = "game.command.start-assault-N"
STOP_ASSAULT_CAPABILITY = "game.command.stop-assault-N"
ENFORCE_DEMANDS_CAPABILITY = "game.command.enforce-demands-N"
QUERY_WAR_TERMINATION_OPTIONS_CAPABILITY = (
    "game.command.query-war-termination-options-N"
)
QUERY_WAR_PRISONER_RELEASE_PAIRS_V1_CAPABILITY = (
    "game.command.query-war-prisoner-release-pairs-v1-N"
)
QUERY_OUTBOUND_WAR_WHITE_PEACE_STATUS_CAPABILITY = (
    "game.command.query-outbound-war-white-peace-status-v1-N"
)
QUERY_WAR_TERMINATION_TERMS_CAPABILITY = (
    "game.command.query-war-termination-terms-v1-N"
)
QUERY_ARMY_STRENGTHS_CAPABILITY = (
    "game.command.query-army-strengths-v1"
)
QUERY_ARMY_STRENGTHS_STEP = "query-army-strengths-v1"
QUERY_PROVINCE_LOCAL_SIEGE_CAPABILITY = (
    "game.command.query-province-local-siege-v1-N"
)
QUERY_PROVINCE_LOCAL_SIEGE_STEP_PREFIX = "query-province-local-siege-v1-"
MAX_NATIVE_ROUTE_SOURCE_COUNT = 4096
SURRENDER_WAR_CAPABILITY = "game.command.surrender-war-N"
OFFER_WHITE_PEACE_CAPABILITY = "game.command.offer-white-peace-N"
ARMY_ROUTES_CAPABILITY = "game.state.army-routes"
WAR_PRIMARY_OPPONENT_CAPABILITY = "game.state.war-primary-opponent"
WAR_OBJECTIVES_CAPABILITY = "game.state.war-objectives"
WAR_OBJECTIVE_OCCUPATION_CAPABILITY = (
    "game.state.war-objective-occupation"
)
WAR_OBJECTIVE_FORT_LEVEL_CAPABILITY = (
    "game.state.war-objective-fort-level"
)
WAR_OBJECTIVE_GARRISON_CAPABILITY = "game.state.war-objective-garrison"
WAR_OBJECTIVE_SIEGE_PROGRESS_CAPABILITY = (
    "game.state.war-objective-siege-progress"
)
WAR_OBJECTIVE_ASSAULT_CAPABILITY = "game.state.war-objective-assault"
RAISE_TROOPS_STEP = "raise-troops-default"
HIRE_MERCENARY_V1_STEP = "hire-mercenary-v1"
HIRE_MERCENARY_V1_CAPABILITY = "game.command." + HIRE_MERCENARY_V1_STEP
HIRE_HOLY_ORDER_V1_STEP = "hire-holy-order-v1"
HIRE_HOLY_ORDER_V1_CAPABILITY = "game.command." + HIRE_HOLY_ORDER_V1_STEP
BATTLE_DECISION_EPOCH_ADVANCE_STEP = "battle-decision-epoch-advance"
BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX = (
    BATTLE_DECISION_EPOCH_ADVANCE_STEP + "-to-"
)
COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP = (
    "committed-route-sentinel-advance"
)
COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX = (
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP + "-army-"
)
WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP = (
    "war-objective-hold-sentinel-advance"
)
WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX = (
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP + "-war-"
)
BATTLE_TERMINAL_CRUISE_STEP = "battle-terminal-cruise"
BATTLE_SENTINEL_ADVANCE_STEPS = frozenset(
    {
        BATTLE_DECISION_EPOCH_ADVANCE_STEP,
        BATTLE_TERMINAL_CRUISE_STEP,
    }
)

CK3_FIXED_POINT_SCALE = 100_000
MAX_ARMY_STRENGTH_REQUEST_IDS = 64
MAX_ROUTE_CONTACT_HOSTILE_IDS = 64

_TERMINATION_TERMS_GAME_VERSION = "1.19.0.6"
_TERMINATION_TERMS_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
_TERMINATION_TERMS_CLAIM_SCRIPT_SHA256 = (
    "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
)
_TERMINATION_TERMS_RAIKTOR_EVENT_WAR_SCRIPT_SHA256 = (
    "BD202AE41EBA3A0E1E7E4277D09ED1E8D8C7E66B378308BB417D974331F9C707"
)
_TERMINATION_TERMS_CASUS_BELLI_EFFECTS_SCRIPT_SHA256 = (
    "9F7C77CC9342B1197B1C802A2D465E56F7521458B103DEC84F5EB7222E45F18C"
)
_TERMINATION_TERMS_WAR_EFFECTS_SCRIPT_SHA256 = (
    "A936E09F448EF715580A918165EAB89A9368AD2D3014E425C998CD9D4F0E8D7D"
)
_TERMINATION_TERMS_WAR_INTERACTIONS_SCRIPT_SHA256 = (
    "5C99B8F14893929A9BC2DBB5B258CDD2D4233D5805091952209413DE876EE09F"
)
_TERMINATION_TERMS_BOOKMARK_EVENTS_SCRIPT_SHA256 = (
    "75CF485E379E522D4AAED9EF889FCC411A0D9DFCC28BCFB250ABDCC93A757EFF"
)
_TERMINATION_TERMS_NATIVE_READER = "CWar+0x270/+0x290;0x28B1AA0"
_TERMINATION_TERMS_RAIKTOR_TRUCE_OBSERVER = (
    "ck3-1.19.0.6-native-raiktor-surrender-truce-v1"
)
_TERMINATION_TERMS_CLAIM_LIFECYCLE = (
    "present_only_vtable_slot_0_delete_flags_0"
)
_TERMINATION_TERMS_CLAIM_SLICE = "claim_cb_claim_disposition"
_TERMINATION_TERMS_RAIKTOR_SLICE = (
    "raiktor_claim_cb_attacker_defeat_disposition"
)
_TERMINATION_TERMS_OUTCOMES = {
    "attacker_victory": {
        "declared_title_disposition": (
            "transfer_to_claimant_via_conquest_claim"
        ),
        "claim_disposition": "resolve_with_add_claim_on_loss",
    },
    "white_peace": {
        "declared_title_disposition": "unchanged",
        "claim_disposition": "retain_and_strengthen_weak",
    },
    "attacker_defeat": {
        "declared_title_disposition": "unchanged",
        "claim_disposition": "remove_declared_target_claims",
    },
}
_TERMINATION_TERMS_RAIKTOR_UNOBSERVED_DYNAMIC_EFFECTS = [
    "actual_gold_transfer",
    "actual_prestige_delta",
    "actual_truce_expiry",
    "actual_prisoner_release_pairs",
    "conditional_favor_hook_application",
    "targeting_faction_discontent_delta",
    "glory_hound_vassal_opinion_rows",
    "antagonistic_clan_vassal_opinion_rows",
    "existing_house_feud_score_delta",
    "attacker_mandala_piety_experience_delta",
    "defender_mandala_serenity",
    "defender_accolade_glory",
    "laamp_actual_settlement_outside_cb_effect",
    "war_bound_army_losses",
]
_TERMINATION_TERMS_RAIKTOR_ATTACKER_DEFEAT = {
    "declared_title_disposition": "unchanged",
    "claim_disposition": "remove_declared_target_claims",
}
_TERMINATION_TERMS_RAIKTOR_GOLD_REPARATIONS = {
    "direction": "primary_attacker_to_primary_defender",
    "factor": 3,
    "positive_income_basis": "primary_attacker_yearly_income",
    "fallback_condition": (
        "landless_adventurer_or_nonpositive_monthly_income"
    ),
    "fallback_basis": "primary_attacker_medium_gold_value",
    "defender_culture_multiplier": (
        "2_if_primary_defender_has_more_gold_for_successful_defensive_wars_else_1"
    ),
    "actual_amount_observable": False,
    "attacker_current_gold": None,
    "defender_current_gold": None,
    "attacker_authoritative_monthly_gold_income": None,
    "defender_authoritative_monthly_gold_income": None,
    "actual_transfer": None,
}
_TERMINATION_TERMS_RAIKTOR_ATTACKER_FAME = {
    "resource": "prestige",
    "base": "cb_prestige_factor",
    "scale": -10,
    "limit_rule": "loss_capped_at_1000",
    "actual_delta_observable": False,
    "attacker_current_prestige": None,
    "cb_prestige_factor": None,
    "attacker_prestige_delta": None,
}
_TERMINATION_TERMS_RAIKTOR_TRUCE = {
    "direction": "primary_attacker_toward_primary_defender",
    "result": "defeat",
    "evaluated_days_observable": False,
    "evaluated_days": None,
    "actual_expiry_observable": False,
    "expiry_date_raw": None,
}
_TERMINATION_TERMS_RAIKTOR_PRISONER_RELEASE = {
    "rule": "war_result_primary_and_first_three_heirs",
    "actual_pairs_observable": False,
    "attacker_participant_ids": None,
    "defender_participant_ids": None,
    "attacker_release_candidate_ids": None,
    "defender_release_candidate_ids": None,
    "release_pairs": None,
    "full_participant_scan": None,
    "primary_and_first_three_successors_scanned": None,
}
_TERMINATION_TERMS_RAIKTOR_CONDITIONAL_FAVOR_HOOK = {
    "rule": "attacker_on_claimant_if_distinct_and_can_add_favor_hook",
    "actual_applies_observable": False,
    "claimant_distinct_from_attacker": None,
    "original_visible_root_traversed": None,
    "will_apply": None,
}

_ARMY_STRENGTH_ROW_KEYS = {
    "status",
    "army_id",
    "native_carmy_id",
    "scope_role",
    "war_ids",
    "regiment_count",
    "current_soldiers",
    "maximum_soldiers",
    "ai_base_power_raw",
    "ai_base_power_scale",
    "unavailable_reason",
}
_ARMY_STRENGTH_SUPPLY_FIELD_PAIRS = (
    ("current_supply_raw", "current_supply_scale"),
    ("merge_supply_destination_weight_raw", "merge_supply_destination_weight_scale"),
    ("current_supply_capacity_raw", "current_supply_capacity_scale"),
    ("current_attrition_fraction_raw", "current_attrition_fraction_scale"),
    ("current_supply_change_monthly_raw", "current_supply_change_monthly_scale"),
)
_ARMY_STRENGTH_GATHERING_DAYS_KEYS = {
    "gathering_days_left",
    "gathering_days_status",
    "gathering_days_ready",
}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS = _ARMY_STRENGTH_ROW_KEYS | {
    key for pair in _ARMY_STRENGTH_SUPPLY_FIELD_PAIRS for key in pair
} | {"regiment_replenishment", "regiment_strengths", "regiment_replenishment_records_v1", "fixed_chunk0_preparation_inputs_v1", "current_movement_progress",
     "army_update_clock_v1", "native_owner_recall_inputs_v1", "native_maa_recruitment_inputs_v1", "owned_regiments_v1",
     "loss_application_inputs_v1", "monthly_loss_budget_inputs_v1", "monthly_caller_effect_inputs_v1", "monthly_daily_queue_inputs_v1", "monthly_first_removal_cleanup_inputs_v1", "monthly_current_helper_domain_inputs_v1", "monthly_current_helper_point_store_inputs_v1", "current_province_supply_contributors_v1", "current_province_besieging_contributors_v1", "current_land_resupply_v1", "current_land_supply_rate_inputs_v1", "scoped_ordered_refill_inputs_v1", "current_daily_assault_table_v1", "current_daily_assault_roster_admission_v1", "county_entry_inputs_v1", "native_army_resolution_v1"} | _ARMY_STRENGTH_GATHERING_DAYS_KEYS
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"ordered_besieging_refill_inputs_v1", "current_daily_assault_loss_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"ordered_besieging_fixed_chunk0_preparation_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_assault_removal_reference_inputs_v1", "current_pre_date_pending_update_inputs_v1", "current_pre_date_dated_append_inputs_v1", "current_post_admission_refresh_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_candidate_detachment_mapper_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_detachment_data_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {
    "future_daily_supply_schedule_inputs_v1", "current_detachment_callback_inputs_v1",
    "current_detachment_store_inputs_v1", "current_character_detachment_inputs_v1",
}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_pre_date_character_prefix_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_army_condition30_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"source_derived_next_daily_supply_frame_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_unit_new_date_schedule_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_unit_new_date_callback_entry_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_army_flag20_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_disembark_penalty_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_army_flag21_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_selected_title_holder_owner_relation_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_army_flag31_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_army_combat_roles_phase_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_fleet_supply_tick_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_daily_supply_dispatch_inputs_v1"}
_ARMY_STRENGTH_SUPPLY_ROW_KEYS |= {"current_month_first_refill_call_inputs_v1"}
_ARMY_STRENGTH_SCOPE_ROLES = {
    "player",
    "active_war_ally",
    "active_war_enemy",
}


def normalize_active_wars(value: object) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("native active_wars must be an array")
    result: list[dict[str, object]] = []
    for index, raw_war in enumerate(value):
        if not isinstance(raw_war, dict):
            raise ValueError(f"native active_wars[{index}] must be an object")
        war_id = _non_negative_id(raw_war.get("war_id"), "war_id")
        player_side = raw_war.get("player_side")
        if player_side not in {"attacker", "defender"}:
            raise ValueError(
                f"native active_wars[{index}].player_side is malformed"
            )
        score = raw_war.get("player_relative_war_score")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError(
                "native active_wars"
                f"[{index}].player_relative_war_score is malformed"
            )
        primary_opponent_character_id = raw_war.get(
            "primary_opponent_character_id"
        )
        if primary_opponent_character_id is not None:
            primary_opponent_character_id = _non_negative_id(
                primary_opponent_character_id,
                "primary_opponent_character_id",
            )
        player_is_primary_war_leader = raw_war.get(
            "player_is_primary_war_leader"
        )
        if (
            player_is_primary_war_leader is not None
            and not isinstance(player_is_primary_war_leader, bool)
        ):
            raise ValueError(
                "native active_wars"
                f"[{index}].player_is_primary_war_leader is malformed"
            )
        enemy_primary_default_raise_province_id = raw_war.get(
            "enemy_primary_default_raise_province_id"
        )
        if enemy_primary_default_raise_province_id is not None:
            enemy_primary_default_raise_province_id = _non_negative_id(
                enemy_primary_default_raise_province_id,
                "enemy_primary_default_raise_province_id",
            )
        objective_province_ids = _non_negative_id_list(
            raw_war.get("war_objective_province_ids"),
            f"active_wars[{index}].war_objective_province_ids",
        )
        result.append(
            {
                "war_id": war_id,
                "player_side": player_side,
                "primary_opponent_character_id": (
                    primary_opponent_character_id
                ),
                "player_is_primary_war_leader": (
                    player_is_primary_war_leader
                ),
                "enemy_primary_default_raise_province_id": (
                    enemy_primary_default_raise_province_id
                ),
                "targeted_title_ids": _non_negative_id_list(
                    raw_war.get("targeted_title_ids"),
                    f"active_wars[{index}].targeted_title_ids",
                ),
                "war_objective_province_ids": objective_province_ids,
                "objective_province_states": (
                    normalize_objective_province_states(
                        raw_war.get("objective_province_states"),
                        objective_province_ids=objective_province_ids,
                        name=(
                            f"active_wars[{index}]"
                            ".objective_province_states"
                        ),
                    )
                ),
                "player_relative_war_score": score,
                "allied_armies": normalize_armies(
                    raw_war.get("allied_armies"),
                    name=f"active_wars[{index}].allied_armies",
                ),
                "enemy_armies": normalize_armies(
                    raw_war.get("enemy_armies"),
                    name=f"active_wars[{index}].enemy_armies",
                ),
                "source": "native",
            }
        )
    return result


def war_termination_active_war_signature(
    value: object,
) -> list[dict[str, object]] | None:
    """Return stable planner inputs for a bounded negative-query lease.

    The signature deliberately excludes daily tactical state and any duration
    counter: those values advance while the seven-day lease is useful.  A
    full-generation WarID binds the active CB for the lifetime of that war;
    the CB itself is recorded separately in the query signature below.
    """
    if not isinstance(value, list):
        return None
    signature: list[dict[str, object]] = []
    for war in value:
        if not isinstance(war, dict):
            return None
        war_id = war.get("war_id")
        score = war.get("player_relative_war_score")
        player_side = war.get("player_side")
        is_primary = war.get("player_is_primary_war_leader")
        opponent_id = war.get("primary_opponent_character_id")
        target_ids = war.get("targeted_title_ids")
        if (
            isinstance(war_id, bool)
            or not isinstance(war_id, int)
            or war_id <= 0
            or isinstance(score, bool)
            or not isinstance(score, int)
            or player_side not in {"attacker", "defender"}
            or (
                is_primary is not None
                and not isinstance(is_primary, bool)
            )
            or (
                opponent_id is not None
                and (
                    isinstance(opponent_id, bool)
                    or not isinstance(opponent_id, int)
                    or opponent_id < 0
                )
            )
            or not isinstance(target_ids, list)
            or any(
                isinstance(target_id, bool)
                or not isinstance(target_id, int)
                or target_id < 0
                for target_id in target_ids
            )
        ):
            return None
        signature.append(
            {
                "war_id": war_id,
                "player_side": player_side,
                "player_is_primary_war_leader": is_primary,
                "primary_opponent_character_id": opponent_id,
                "player_relative_war_score": score,
                "targeted_title_ids": list(target_ids),
            }
        )
    return sorted(signature, key=lambda row: int(row["war_id"]))


def war_termination_negative_query_signature(
    options: object,
) -> dict[str, object] | None:
    """Canonicalize the exact inputs used to classify a negative query.

    ``war_duration_days`` is provenance rather than an equality key.  The
    seven-day expiry bounds all date-dependent legality, while including a
    monotonically increasing duration here would defeat reuse after one day.
    """
    if not isinstance(options, dict):
        return None
    option_rows = options.get("options")
    if not isinstance(option_rows, dict):
        return None
    option_signature: dict[str, object] = {}
    for name in ("surrender", "white_peace", "victory"):
        option = option_rows.get(name)
        response = (
            option.get("recipient_response")
            if isinstance(option, dict)
            else None
        )
        if not isinstance(option, dict) or not isinstance(response, dict):
            return None
        option_signature[name] = {
            "outcome": option.get("outcome"),
            "hostage_variant": option.get("hostage_variant"),
            "context_constructed": option.get("context_constructed"),
            "native_validator_passed": option.get(
                "native_validator_passed"
            ),
            "available": option.get("available"),
            "recipient_response": {
                "status": response.get("status"),
                "decision_status_raw": response.get(
                    "decision_status_raw"
                ),
                "would_accept_now": response.get("would_accept_now"),
            },
        }
    active_cb = options.get("active_casus_belli_identity")
    score_breakdown = options.get("war_score_breakdown")
    if active_cb is not None and not isinstance(active_cb, dict):
        return None
    if score_breakdown is not None and not isinstance(score_breakdown, dict):
        return None
    return {
        "war_id": options.get("war_id"),
        "player_side": options.get("player_side"),
        "player_is_primary_war_leader": options.get(
            "player_is_primary_war_leader"
        ),
        "player_relative_war_score": options.get(
            "player_relative_war_score"
        ),
        "absolute_war_scores_observable": options.get(
            "absolute_war_scores_observable"
        ),
        "attacker_war_score": options.get("attacker_war_score"),
        "defender_war_score": options.get("defender_war_score"),
        "war_score_breakdown": (
            dict(score_breakdown)
            if isinstance(score_breakdown, dict)
            else None
        ),
        "active_casus_belli_present": options.get(
            "active_casus_belli_present"
        ),
        "active_casus_belli_identity": (
            dict(active_cb) if isinstance(active_cb, dict) else None
        ),
        "cb_allows_white_peace": options.get("cb_allows_white_peace"),
        "options": option_signature,
    }


def normalize_objective_province_states(
    value: object,
    *,
    objective_province_ids: list[int],
    name: str = "objective_province_states",
) -> list[dict[str, object]]:
    """Normalize the paused-only rich state for exact war objectives.

    An empty array is a valid unavailable projection: older adapters do not
    publish this additive field, and the native reader atomically suppresses
    a war whose rows exceed its shared snapshot budget.  A non-empty array is
    complete and must exactly follow the objective ID order.
    """
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    normalized = [
        _normalize_objective_province_state(
            row,
            name=f"{name}[{index}]",
        )
        for index, row in enumerate(value)
    ]
    if normalized and [
        int(row["province_id"]) for row in normalized
    ] != objective_province_ids:
        raise ValueError(
            f"native {name} must completely match war_objective_province_ids"
        )
    return normalized


def _normalize_objective_province_state(
    value: object, *, name: str
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"native {name} must be an object")
    province_id = _positive_int32_id(
        value.get("province_id"), f"{name}.province_id"
    )
    occupation_observable = _strict_bool(
        value.get("occupation_observable"),
        f"{name}.occupation_observable",
    )
    is_occupied = value.get("is_occupied")
    occupying_character_id = value.get("occupying_character_id")
    if not occupation_observable:
        if is_occupied is not None or occupying_character_id is not None:
            raise ValueError(
                f"native {name} cannot publish an unobservable occupation"
            )
    else:
        is_occupied = _strict_bool(is_occupied, f"{name}.is_occupied")
        if is_occupied:
            occupying_character_id = _positive_int32_id(
                occupying_character_id,
                f"{name}.occupying_character_id",
            )
        elif occupying_character_id is not None:
            raise ValueError(
                f"native {name} cannot publish an occupant when unoccupied"
            )

    fort_level = _optional_non_negative_int32(
        value.get("fort_level"), f"{name}.fort_level"
    )
    garrison_size = _optional_non_negative_int32(
        value.get("garrison_size"), f"{name}.garrison_size"
    )
    besieging_strength = _optional_non_negative_int32(
        value.get("besieging_strength"), f"{name}.besieging_strength"
    )
    siege_observable = _strict_bool(
        value.get("siege_observable"), f"{name}.siege_observable"
    )
    raw_active_siege = value.get("active_siege")
    if not siege_observable:
        if raw_active_siege is not None:
            raise ValueError(
                f"native {name} cannot publish an unobservable active siege"
            )
        active_siege = None
    elif raw_active_siege is None:
        active_siege = None
    else:
        active_siege = _normalize_active_siege(
            raw_active_siege, name=f"{name}.active_siege"
        )
    return {
        "province_id": province_id,
        "occupation_observable": occupation_observable,
        "is_occupied": is_occupied,
        "occupying_character_id": occupying_character_id,
        "fort_level": fort_level,
        "garrison_size": garrison_size,
        "besieging_strength": besieging_strength,
        "siege_observable": siege_observable,
        "active_siege": active_siege,
    }


def query_province_local_siege_step(province_id: int) -> str:
    """Build one canonical read-only local Province query literal."""
    return (
        QUERY_PROVINCE_LOCAL_SIEGE_STEP_PREFIX
        + str(_positive_int32_id(province_id, "province_id"))
    )


def parse_query_province_local_siege_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        QUERY_PROVINCE_LOCAL_SIEGE_STEP_PREFIX
    ):
        return None
    suffix = step.removeprefix(QUERY_PROVINCE_LOCAL_SIEGE_STEP_PREFIX)
    if not suffix or not suffix.isascii() or not suffix.isdecimal():
        return None
    try:
        province_id = _positive_int32_id(int(suffix), "province_id")
    except ValueError:
        return None
    return province_id if str(province_id) == suffix else None


def normalize_province_local_siege_result(
    value: object,
    *,
    expected_step: str,
    expected_province_id: int,
    expected_snapshot_revision: int,
    expected_date_raw: int,
) -> dict[str, object]:
    """Keep partial native fields typed; this never proves hostile scope."""
    if not isinstance(value, dict) or set(value) != {
        "step", "accepted", "status", "query_sequence",
        "snapshot_revision", "date_raw", "province_state", "backend_id",
    }:
        raise ValueError("native province-local-siege result schema is malformed")
    if (
        value.get("step") != expected_step
        or value.get("accepted") is not True
        or value.get("backend_id") != "native-headless"
    ):
        raise ValueError("native province-local-siege query identity changed")
    sequence = value.get("query_sequence")
    revision = value.get("snapshot_revision")
    date_raw = value.get("date_raw")
    if (
        isinstance(sequence, bool) or not isinstance(sequence, int)
        or not 1 <= sequence <= 2**64 - 1
        or revision != expected_snapshot_revision
        or isinstance(revision, bool)
        or date_raw != expected_date_raw
        or isinstance(date_raw, bool)
    ):
        raise ValueError("native province-local-siege frame binding changed")
    state = _normalize_objective_province_state(
        value.get("province_state"), name="province_state"
    )
    if state["province_id"] != expected_province_id:
        raise ValueError("native province-local-siege ProvinceID changed")
    complete = bool(
        state["occupation_observable"]
        and state["fort_level"] is not None
        and state["garrison_size"] is not None
        and state["besieging_strength"] is not None
        and state["siege_observable"]
    )
    if value.get("status") != ("available" if complete else "partial"):
        raise ValueError("native province-local-siege status disagrees with fields")
    return {**value, "province_state": state}


def _normalize_active_siege(
    value: object, *, name: str
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"native {name} must be an object or null")
    progress = _fixed_point(
        value.get("progress_fraction"),
        f"{name}.progress_fraction",
        fraction=True,
    )
    current = _fixed_point(
        value.get("current_work"), f"{name}.current_work"
    )
    total = _fixed_point(value.get("total_work"), f"{name}.total_work")
    phase_event_state = value.get("phase_event_state")
    if phase_event_state is not None:
        if not isinstance(phase_event_state, dict):
            raise ValueError(f"native {name}.phase_event_state must be an object or null")
        phase_event_state = {
            field: _optional_non_negative_int32(
                phase_event_state.get(field), f"{name}.phase_event_state.{field}"
            )
            for field in (
                "breach_level", "starvation_level", "disease_level",
                "desertion_count", "stalemate_count",
            )
        }
    prepared_event = _optional_non_negative_int32(
        value.get("prepared_selected_phase_event_enum"),
        f"{name}.prepared_selected_phase_event_enum",
    )
    if prepared_event is not None and prepared_event > 5:
        raise ValueError(f"native {name}.prepared_selected_phase_event_enum must be in range 0..5")
    assault_observable = value.get("assault_observable", False)
    if not isinstance(assault_observable, bool):
        raise ValueError(
            f"native {name}.assault_observable must be a boolean"
        )
    assault_fields = (
        "breach_level",
        "assault_in_progress",
        "can_start_assault",
        "can_stop_assault",
        "assault_daily_progress",
        "assault_daily_casualties",
    )
    if not assault_observable:
        if any(value.get(field) is not None for field in assault_fields):
            raise ValueError(
                f"native {name} cannot publish an unobservable assault"
            )
        breach_level = None
        assault_in_progress = None
        can_start_assault = None
        can_stop_assault = None
        assault_daily_progress = None
        assault_daily_casualties = None
    else:
        breach_level = _optional_non_negative_int32(
            value.get("breach_level"), f"{name}.breach_level"
        )
        if breach_level is None or breach_level > 2:
            raise ValueError(
                f"native {name}.breach_level must be in range 0..2"
            )
        assault_in_progress = _strict_bool(
            value.get("assault_in_progress"),
            f"{name}.assault_in_progress",
        )
        can_start_assault = _strict_bool(
            value.get("can_start_assault"), f"{name}.can_start_assault"
        )
        can_stop_assault = _strict_bool(
            value.get("can_stop_assault"), f"{name}.can_stop_assault"
        )
        assault_daily_progress = _fixed_point(
            value.get("assault_daily_progress"),
            f"{name}.assault_daily_progress",
        )
        assault_daily_casualties = _optional_non_negative_int32(
            value.get("assault_daily_casualties"),
            f"{name}.assault_daily_casualties",
        )
        if assault_daily_casualties is None:
            raise ValueError(
                f"native {name}.assault_daily_casualties is required"
            )
    result = {
        "siege_id": _positive_int32_id(
            value.get("siege_id"), f"{name}.siege_id"
        ),
        "besieging_army_id": optional_public_cunit_id(
            value.get("besieging_army_id"),
            f"{name}.besieging_army_id",
        ),
        "player_army_besieging": _strict_bool(
            value.get("player_army_besieging"),
            f"{name}.player_army_besieging",
        ),
        "progress_fraction": progress,
        "current_work": current,
        "total_work": total,
        "remaining_work": {
            "raw": max(int(total["raw"]) - int(current["raw"]), 0),
            "scale": CK3_FIXED_POINT_SCALE,
        },
        "days_left": _optional_non_negative_int32(
            value.get("days_left"), f"{name}.days_left"
        ),
        "ordinary_daily_progress": (
            _fixed_point(value["ordinary_daily_progress"], f"{name}.ordinary_daily_progress")
            if value.get("ordinary_daily_progress") is not None else None
        ),
        "current_phase_length": (
            _fixed_point(value["current_phase_length"], f"{name}.current_phase_length")
            if value.get("current_phase_length") is not None else None
        ),
        "prepared_phase_length": (
            _fixed_point(value["prepared_phase_length"], f"{name}.prepared_phase_length")
            if value.get("prepared_phase_length") is not None else None
        ),
        "phase_counter": _optional_non_negative_int32(
            value.get("phase_counter"), f"{name}.phase_counter"
        ),
        "can_advance": _optional_strict_bool(
            value.get("can_advance"), f"{name}.can_advance"
        ),
        "phase_event_state": phase_event_state,
        "prepared_selected_phase_event_enum": prepared_event,
        "assault_observable": assault_observable,
        "breach_level": breach_level,
        "walls_breached": (
            breach_level > 0 if breach_level is not None else None
        ),
        "assault_in_progress": assault_in_progress,
        "can_start_assault": can_start_assault,
        "can_stop_assault": can_stop_assault,
        "assault_daily_progress": assault_daily_progress,
        "assault_daily_casualties": assault_daily_casualties,
    }
    # Preserve legacy key absence, failed-read null, and native measured zero
    # as three distinct observations of the eligible regiment inputs.
    if "eligible_regiment_siege_work" in value:
        work = value["eligible_regiment_siege_work"]
        result["eligible_regiment_siege_work"] = (
            _fixed_point(work, f"{name}.eligible_regiment_siege_work")
            if work is not None else None
        )
    if "highest_eligible_siege_tier" in value:
        result["highest_eligible_siege_tier"] = _optional_non_negative_int32(
            value["highest_eligible_siege_tier"],
            f"{name}.highest_eligible_siege_tier",
        )
    if "province_unit_occurrences" in value:
        result["province_unit_occurrences"] = normalize_siege_province_unit_occurrences(
            value["province_unit_occurrences"], name=f"{name}.province_unit_occurrences"
        )
    return result


def _fixed_point(
    value: object, name: str, *, fraction: bool = False
) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"native {name} must contain raw and scale")
    raw = value.get("raw")
    scale = value.get("scale")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or raw < 0
        or raw > 2**63 - 1
        or scale != CK3_FIXED_POINT_SCALE
    ):
        raise ValueError(f"native {name} fixed value is malformed")
    if fraction and raw > CK3_FIXED_POINT_SCALE:
        raise ValueError(f"native {name} fraction is out of range")
    return {"raw": raw, "scale": CK3_FIXED_POINT_SCALE}


def normalize_armies(
    value: object, *, name: str = "player_armies"
) -> list[dict[str, object]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[dict[str, object]] = []
    for index, raw_army in enumerate(value):
        if not isinstance(raw_army, dict):
            raise ValueError(f"native {name}[{index}] must be an object")
        soldiers = raw_army.get("soldiers")
        # One early reverse-engineering fixture used this spelling.  Accept it
        # on input, but never expose it through the canonical MCP snapshot.
        if soldiers is None:
            soldiers = raw_army.get("soldier_count")
        if (
            soldiers is not None
            and (
                isinstance(soldiers, bool)
                or not isinstance(soldiers, int)
                or soldiers < 0
            )
        ):
            raise ValueError(f"native {name}[{index}].soldiers is malformed")
        current_province_id = raw_army.get("current_province_id")
        if current_province_id is not None:
            current_province_id = _non_negative_id(
                current_province_id, "current_province_id"
            )
        move_target = raw_army.get("move_target_province_id")
        explicit_observable = raw_army.get("move_target_observable")
        if explicit_observable is not None and not isinstance(
            explicit_observable, bool
        ):
            raise ValueError(
                f"native {name}[{index}].move_target_observable is malformed"
            )
        move_target_observable = (
            explicit_observable
            if isinstance(explicit_observable, bool)
            else "move_target_province_id" in raw_army
        )
        if move_target is not None:
            move_target = _non_negative_id(
                move_target, "move_target_province_id"
            )
        route_province_ids = raw_army.get("route_province_ids")
        if "route_province_ids" in raw_army and not isinstance(
            route_province_ids, list
        ):
            raise ValueError(
                f"native {name}[{index}].route_province_ids must be an array"
            )
        controllable = raw_army.get("controllable")
        if not isinstance(controllable, bool):
            raise ValueError(f"native {name}[{index}].controllable is malformed")
        normalized: dict[str, object] = {
                "army_id": public_cunit_id(raw_army.get("army_id"), "army_id"),
                "owner_character_id": _non_negative_id(
                    raw_army.get("owner_character_id"), "owner_character_id"
                ),
                "soldiers": soldiers,
                "current_province_id": current_province_id,
                "move_target_province_id": move_target,
                "move_target_observable": move_target_observable,
                "controllable": controllable,
                "source": "native",
            }
        if "route_province_ids" in raw_army:
            normalized["route_province_ids"] = [
                _positive_int32_id(
                    province_id,
                    f"{name}[{index}].route_province_ids",
                )
                for province_id in (
                    route_province_ids
                    if isinstance(route_province_ids, list)
                    else []
                )
            ]
        has_route_status = "route_read_status" in raw_army
        has_route_count = "route_source_count" in raw_army
        if has_route_status != has_route_count:
            raise ValueError(
                f"native {name}[{index}] route status/count must appear together"
            )
        if has_route_status:
            status = raw_army["route_read_status"]
            count = raw_army["route_source_count"]
            if not isinstance(status, str) or status not in {
                "not_attempted", "complete_empty", "complete_nonempty",
                "target_only", "invalid_header", "unresolved_entry",
            }:
                raise ValueError(
                    f"native {name}[{index}].route_read_status is malformed"
                )
            if count is not None and (
                isinstance(count, bool)
                or not isinstance(count, int)
                or not 0 <= count <= MAX_NATIVE_ROUTE_SOURCE_COUNT
            ):
                raise ValueError(
                    f"native {name}[{index}].route_source_count is malformed"
                )
            route = normalized.get("route_province_ids")
            if not isinstance(route, list):
                raise ValueError(
                    f"native {name}[{index}] route status requires route array"
                )
            valid = (
                (status == "complete_empty" and count == 0
                 and not route and not move_target_observable
                 and move_target is None)
                or (status == "complete_nonempty" and isinstance(count, int)
                    and count > 0 and len(route) == count
                    and move_target_observable and move_target == route[-1])
                or (status == "target_only" and isinstance(count, int)
                    and count > 0 and not route
                    and move_target_observable and move_target is not None)
                or (status == "unresolved_entry" and isinstance(count, int)
                    and count > 0 and not route and not move_target_observable
                    and move_target is None)
                or (status in {"not_attempted", "invalid_header"}
                    and count is None and not route
                    and not move_target_observable and move_target is None)
            )
            if not valid:
                raise ValueError(
                    f"native {name}[{index}] route status/count disagrees with fields"
                )
            normalized["route_read_status"] = status
            normalized["route_source_count"] = count
        for optional_flag in ("in_combat", "retreating"):
            flag = raw_army.get(optional_flag)
            if flag is not None and not isinstance(flag, bool):
                raise ValueError(
                    f"native {name}[{index}].{optional_flag} is malformed"
                )
            if isinstance(flag, bool):
                normalized[optional_flag] = flag
        army_state = raw_army.get("army_state")
        if army_state is not None and (
            not isinstance(army_state, str) or not army_state
        ):
            raise ValueError(f"native {name}[{index}].army_state is malformed")
        if isinstance(army_state, str):
            normalized["army_state"] = army_state
        army_state_code = raw_army.get("army_state_code")
        if army_state_code is not None:
            normalized["army_state_code"] = _non_negative_id(
                army_state_code, "army_state_code"
            )
        if "siege_days_left" in raw_army:
            days_left = raw_army["siege_days_left"]
            normalized["siege_days_left"] = (
                _non_negative_id(days_left, "siege_days_left")
                if days_left is not None
                else None
            )
        if "siege_province_holder_character_id" in raw_army:
            holder_id = raw_army["siege_province_holder_character_id"]
            normalized["siege_province_holder_character_id"] = (
                _positive_int32_id(holder_id, "siege_province_holder_character_id")
                if holder_id is not None
                else None
            )
        if "siege_province_in_player_subrealm" in raw_army:
            in_subrealm = raw_army["siege_province_in_player_subrealm"]
            if in_subrealm is not None and not isinstance(in_subrealm, bool):
                raise ValueError("native siege province subrealm relation is malformed")
            if in_subrealm is not None and normalized.get(
                "siege_province_holder_character_id"
            ) is None:
                raise ValueError("native siege province relation has no holder")
            normalized["siege_province_in_player_subrealm"] = in_subrealm
        result.append(normalized)
    return result


_ROUTE_CONTACT_HORIZON_KEYS = {
    "status",
    "date_raw",
    "snapshot_revision",
    "subject_army_id",
    "target_province_id",
    "hostile_army_ids",
    "subject_route",
    "hostile_routes",
    "horizon_start_date_raw",
    "horizon_end_date_raw",
    "one_day_contact_free",
    "conflicts",
}
_TIMED_ROUTE_KEYS = {
    "timeline_observable",
    "army_id",
    "current_province_id",
    "effective_origin_province_id",
    "route_province_ids",
    "arrival_date_raws",
}
_SAME_PROVINCE_CONFLICT_KEYS = {
    "kind",
    "hostile_army_id",
    "province_id",
    "overlap_start_date_raw",
    "overlap_end_date_raw",
}
_OPPOSING_EDGE_CONFLICT_KEYS = {
    "kind",
    "hostile_army_id",
    "subject_from_province_id",
    "subject_to_province_id",
    "hostile_from_province_id",
    "hostile_to_province_id",
    "overlap_start_date_raw",
    "overlap_end_date_raw",
}


def normalize_route_contact_horizon(
    value: object,
    *,
    expected_subject_army_id: int,
    expected_target_province_id: int,
    expected_hostile_army_ids: Iterable[int],
    expected_date_raw: int,
    expected_snapshot_revision: int,
) -> dict[str, object]:
    """Validate the atomic one-day native route/contact proof."""
    if not isinstance(value, dict) or set(value) != _ROUTE_CONTACT_HORIZON_KEYS:
        raise ValueError("native route_contact_horizon has a malformed schema")
    if value.get("status") != "available":
        raise ValueError("native route_contact_horizon is not available")
    subject = public_cunit_id(
        value.get("subject_army_id"), "route_contact_horizon.subject_army_id"
    )
    target = _positive_int32_id(
        value.get("target_province_id"),
        "route_contact_horizon.target_province_id",
    )
    date_raw = _signed_int32(
        value.get("date_raw"), "route_contact_horizon.date_raw"
    )
    revision = value.get("snapshot_revision")
    if (
        isinstance(revision, bool)
        or not isinstance(revision, int)
        or not 1 <= revision <= 2**64 - 1
    ):
        raise ValueError(
            "route_contact_horizon.snapshot_revision must be positive uint64"
        )
    expected_hostiles = sorted(
        {
            public_cunit_id(army_id, "expected_hostile_army_ids")
            for army_id in expected_hostile_army_ids
        }
    )
    hostile_ids = [
        public_cunit_id(
            army_id, "route_contact_horizon.hostile_army_ids"
        )
        for army_id in _required_list(
            value.get("hostile_army_ids"),
            "route_contact_horizon.hostile_army_ids",
        )
    ]
    if (
        subject != expected_subject_army_id
        or target != expected_target_province_id
        or date_raw != expected_date_raw
        or revision != expected_snapshot_revision
        or hostile_ids != expected_hostiles
        or not hostile_ids
        or subject in hostile_ids
    ):
        raise ValueError("native route_contact_horizon scope binding disagrees")

    subject_route = _normalize_timed_route(
        value.get("subject_route"),
        expected_army_id=subject,
        date_raw=date_raw,
        name="route_contact_horizon.subject_route",
    )
    if not (
        subject_route["route_province_ids"]
        and subject_route["route_province_ids"][-1] == target
        or not subject_route["route_province_ids"]
        and subject_route["current_province_id"] == target
    ):
        raise ValueError("native route_contact_horizon subject route misses target")
    raw_hostile_routes = _required_list(
        value.get("hostile_routes"),
        "route_contact_horizon.hostile_routes",
    )
    hostile_routes = [
        _normalize_timed_route(
            route,
            expected_army_id=hostile_ids[index],
            date_raw=date_raw,
            name=f"route_contact_horizon.hostile_routes[{index}]",
        )
        for index, route in enumerate(raw_hostile_routes)
    ] if len(raw_hostile_routes) == len(hostile_ids) else []
    if len(hostile_routes) != len(hostile_ids):
        raise ValueError("native route_contact_horizon hostile scope is incomplete")

    horizon_start = _signed_int32(
        value.get("horizon_start_date_raw"),
        "route_contact_horizon.horizon_start_date_raw",
    )
    horizon_end = _signed_int32(
        value.get("horizon_end_date_raw"),
        "route_contact_horizon.horizon_end_date_raw",
    )
    contact_free = _strict_bool(
        value.get("one_day_contact_free"),
        "route_contact_horizon.one_day_contact_free",
    )
    if horizon_start != date_raw or horizon_end != date_raw + 24:
        raise ValueError("native route_contact_horizon is not a one-day window")
    raw_conflicts = _required_list(
        value.get("conflicts"), "route_contact_horizon.conflicts"
    )
    conflicts: list[dict[str, object]] = []
    for index, conflict in enumerate(raw_conflicts):
        if not isinstance(conflict, dict):
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] is malformed"
            )
        kind = conflict.get("kind")
        expected_keys = (
            _SAME_PROVINCE_CONFLICT_KEYS
            if kind == "same_province"
            else _OPPOSING_EDGE_CONFLICT_KEYS
            if kind == "opposing_edge"
            else None
        )
        if expected_keys is None or set(conflict) != expected_keys:
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] has an unknown shape"
            )
        hostile_id = public_cunit_id(
            conflict.get("hostile_army_id"),
            f"route_contact_horizon.conflicts[{index}].hostile_army_id",
        )
        if hostile_id not in hostile_ids:
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] lacks scope"
            )
        normalized_conflict: dict[str, object] = {
            "kind": kind,
            "hostile_army_id": hostile_id,
        }
        id_fields = (
            ("province_id",)
            if kind == "same_province"
            else (
                "subject_from_province_id",
                "subject_to_province_id",
                "hostile_from_province_id",
                "hostile_to_province_id",
            )
        )
        for field in id_fields:
            normalized_conflict[field] = _positive_int32_id(
                conflict.get(field),
                f"route_contact_horizon.conflicts[{index}].{field}",
            )
        overlap_start = _signed_int32(
            conflict.get("overlap_start_date_raw"),
            f"route_contact_horizon.conflicts[{index}].overlap_start_date_raw",
        )
        overlap_end = _signed_int32(
            conflict.get("overlap_end_date_raw"),
            f"route_contact_horizon.conflicts[{index}].overlap_end_date_raw",
        )
        if not (
            horizon_start <= overlap_start <= overlap_end <= horizon_end
        ):
            raise ValueError(
                f"native route_contact_horizon.conflicts[{index}] is outside the horizon"
            )
        normalized_conflict["overlap_start_date_raw"] = overlap_start
        normalized_conflict["overlap_end_date_raw"] = overlap_end
        conflicts.append(normalized_conflict)
    if contact_free == bool(conflicts):
        raise ValueError("native route_contact_horizon predicate disagrees")
    return {
        "status": "available",
        "date_raw": date_raw,
        "snapshot_revision": revision,
        "subject_army_id": subject,
        "target_province_id": target,
        "hostile_army_ids": hostile_ids,
        "subject_route": subject_route,
        "hostile_routes": hostile_routes,
        "horizon_start_date_raw": horizon_start,
        "horizon_end_date_raw": horizon_end,
        "one_day_contact_free": contact_free,
        "conflicts": conflicts,
    }


def _normalize_timed_route(
    value: object,
    *,
    expected_army_id: int,
    date_raw: int,
    name: str,
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != _TIMED_ROUTE_KEYS:
        raise ValueError(f"native {name} has a malformed schema")
    if value.get("timeline_observable") is not True:
        raise ValueError(f"native {name} timeline is not observable")
    army_id = public_cunit_id(value.get("army_id"), f"{name}.army_id")
    current = _positive_int32_id(
        value.get("current_province_id"), f"{name}.current_province_id"
    )
    effective_origin = _positive_int32_id(
        value.get("effective_origin_province_id"),
        f"{name}.effective_origin_province_id",
    )
    route = [
        _positive_int32_id(province_id, f"{name}.route_province_ids")
        for province_id in _required_list(
            value.get("route_province_ids"), f"{name}.route_province_ids"
        )
    ]
    arrivals = [
        _signed_int32(arrival, f"{name}.arrival_date_raws")
        for arrival in _required_list(
            value.get("arrival_date_raws"), f"{name}.arrival_date_raws"
        )
    ]
    if (
        army_id != expected_army_id
        or len(route) != len(arrivals)
        or not route
        and effective_origin != current
        or route
        and effective_origin not in {current, route[0]}
        or any(arrival < date_raw for arrival in arrivals)
        or any(left > right for left, right in zip(arrivals, arrivals[1:]))
    ):
        raise ValueError(f"native {name} timeline is malformed")
    return {
        "timeline_observable": True,
        "army_id": army_id,
        "current_province_id": current,
        "effective_origin_province_id": effective_origin,
        "route_province_ids": route,
        "arrival_date_raws": arrivals,
    }


def stationary_province_contact_free_in_horizon(
    value: object,
    province_id: int,
) -> bool:
    """Project one stationary Province against a validated hostile timeline.

    The route-contact query is subject-bound, but its hostile route array is
    complete for the exact paused frame.  A stationary friendly army can
    therefore reuse that array: contact exists when a hostile already occupies
    its Province at the closed-window start, or arrives there on/before the
    closed-window end.
    """
    province = _positive_int32_id(
        province_id, "stationary route-contact province_id"
    )
    if not isinstance(value, dict):
        raise ValueError("stationary route-contact horizon must be an object")
    subject = public_cunit_id(
        value.get("subject_army_id"),
        "stationary route-contact subject_army_id",
    )
    target = _positive_int32_id(
        value.get("target_province_id"),
        "stationary route-contact target_province_id",
    )
    date_raw = _signed_int32(
        value.get("date_raw"), "stationary route-contact date_raw"
    )
    revision = value.get("snapshot_revision")
    hostile_ids = _required_list(
        value.get("hostile_army_ids"),
        "stationary route-contact hostile_army_ids",
    )
    normalized = normalize_route_contact_horizon(
        value,
        expected_subject_army_id=subject,
        expected_target_province_id=target,
        expected_hostile_army_ids=hostile_ids,
        expected_date_raw=date_raw,
        expected_snapshot_revision=revision,
    )
    horizon_start = int(normalized["horizon_start_date_raw"])
    horizon_end = int(normalized["horizon_end_date_raw"])
    routes = normalized["hostile_routes"]
    if not isinstance(routes, list):
        raise ValueError("stationary route-contact hostile routes are malformed")
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("stationary route-contact hostile route is malformed")
        if route.get("current_province_id") == province:
            return False
        provinces = route.get("route_province_ids")
        arrivals = route.get("arrival_date_raws")
        if not isinstance(provinces, list) or not isinstance(arrivals, list):
            raise ValueError("stationary route-contact timeline is malformed")
        for route_province, arrival in zip(provinces, arrivals, strict=True):
            if (
                route_province == province
                and horizon_start <= arrival <= horizon_end
            ):
                return False
    return True


def unavoidable_current_province_contact_in_horizon(
    value: object,
) -> bool:
    """Recognize a proof-bound one-day current-Province contact transition.

    This is deliberately stricter than ``one_day_contact_free is False``.  A
    moving subject is accepted only when its first timed arrival is after the
    closed one-day window.  A stationary subject is accepted only for the
    explicit ``target == current`` hold shape with empty route/timeline.  In
    both cases every conflict must be a same-Province overlap at the subject's
    current Province.  The planner must still exhaust alternate exact
    objectives before choosing the stationary hold transition.
    """
    if not isinstance(value, dict):
        return False
    if (
        value.get("status") != "available"
        or value.get("one_day_contact_free") is not False
    ):
        return False
    subject_route = value.get("subject_route")
    conflicts = value.get("conflicts")
    horizon_end = value.get("horizon_end_date_raw")
    if (
        not isinstance(subject_route, dict)
        or not isinstance(conflicts, list)
        or not conflicts
        or isinstance(horizon_end, bool)
        or not isinstance(horizon_end, int)
    ):
        return False
    current_province_id = subject_route.get("current_province_id")
    route = subject_route.get("route_province_ids")
    arrivals = subject_route.get("arrival_date_raws")
    if (
        isinstance(current_province_id, bool)
        or not isinstance(current_province_id, int)
        or current_province_id <= 0
        or not isinstance(route, list)
        or not isinstance(arrivals, list)
        or len(arrivals) != len(route)
    ):
        return False
    moving_edge_cannot_clear = bool(
        route
        and not isinstance(arrivals[0], bool)
        and isinstance(arrivals[0], int)
        and arrivals[0] > horizon_end
    )
    stationary_hold = bool(
        not route
        and not arrivals
        and value.get("target_province_id") == current_province_id
        and subject_route.get("effective_origin_province_id")
        == current_province_id
    )
    if not (moving_edge_cannot_clear or stationary_hold):
        return False
    return all(
        isinstance(conflict, dict)
        and conflict.get("kind") == "same_province"
        and conflict.get("province_id") == current_province_id
        and isinstance(conflict.get("overlap_start_date_raw"), int)
        and not isinstance(conflict.get("overlap_start_date_raw"), bool)
        and conflict["overlap_start_date_raw"] <= horizon_end
        for conflict in conflicts
    )


def player_armies_from_state(
    active_wars: Iterable[dict[str, object]],
    explicit_player_armies: object,
) -> list[dict[str, object]]:
    """Merge the postwar top-level list with armies embedded in active wars."""
    explicit = (
        normalize_armies(explicit_player_armies)
        if explicit_player_armies is not None
        else []
    )
    allied: list[dict[str, object]] = []
    for war in active_wars:
        rows = war.get("allied_armies")
        if isinstance(rows, list):
            allied.extend(
                row
                for row in rows
                if isinstance(row, dict) and row.get("controllable") is True
            )
    return deduplicate_armies([*explicit, *allied])


def enemy_armies_from_wars(
    active_wars: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    enemies: list[dict[str, object]] = []
    for war in active_wars:
        rows = war.get("enemy_armies")
        if isinstance(rows, list):
            enemies.extend(row for row in rows if isinstance(row, dict))
    return deduplicate_armies(enemies)


def enemy_primary_default_raise_province_ids(
    active_wars: Iterable[dict[str, object]],
) -> list[int]:
    """Return stable fallback objectives published for active wars."""
    province_ids: list[int] = []
    seen: set[int] = set()
    for war in active_wars:
        province_id = war.get("enemy_primary_default_raise_province_id")
        if (
            isinstance(province_id, int)
            and not isinstance(province_id, bool)
            and province_id not in seen
        ):
            seen.add(province_id)
            province_ids.append(province_id)
    return province_ids


def war_objective_province_ids(
    active_wars: Iterable[dict[str, object]],
) -> list[int]:
    """Return exact objectives in the adapter's stable traversal order."""
    province_ids: list[int] = []
    seen: set[int] = set()
    for war in active_wars:
        raw = war.get("war_objective_province_ids")
        if isinstance(raw, list):
            for province_id in raw:
                if (
                    isinstance(province_id, int)
                    and not isinstance(province_id, bool)
                    and province_id not in seen
                ):
                    seen.add(province_id)
                    province_ids.append(province_id)
    return province_ids


def controllable_armies(
    armies: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    return [army for army in armies if army.get("controllable") is True]


def deduplicate_armies(
    armies: Iterable[dict[str, object]],
) -> list[dict[str, object]]:
    by_id: dict[int, dict[str, object]] = {}
    for army in armies:
        army_id = army.get("army_id")
        if isinstance(army_id, bool) or not isinstance(army_id, int):
            continue
        by_id.setdefault(army_id, dict(army))
    return list(by_id.values())


def army_strength_scope(
    snapshot: dict[str, object],
) -> list[dict[str, object]]:
    """Derive the exact public-CUnit scope of one paused strength query.

    Membership, ordering, and roles come only from the already published
    snapshot.  Character ownership is deliberately irrelevant: it cannot
    safely reconstruct a war relation lane.
    """
    raw_player_armies = snapshot.get("player_armies")
    raw_active_wars = snapshot.get("active_wars")
    if not isinstance(raw_player_armies, list):
        raise ValueError("army-strength scope requires player_armies")
    if not isinstance(raw_active_wars, list):
        raise ValueError("army-strength scope requires active_wars")

    rows: list[dict[str, object]] = []
    by_id: dict[int, dict[str, object]] = {}

    def admit(raw_army: object, role: str) -> None:
        if not isinstance(raw_army, dict):
            raise ValueError("army-strength scope contains a malformed army")
        army_id = public_cunit_id(
            raw_army.get("army_id"), "army-strength scope army_id"
        )
        current = by_id.get(army_id)
        if current is None:
            current = {
                "army_id": army_id,
                "scope_role": role,
                "war_ids": [],
            }
            by_id[army_id] = current
            rows.append(current)
            return
        precedence = {
            "active_war_enemy": 0,
            "active_war_ally": 1,
            "player": 2,
        }
        if precedence[role] > precedence[str(current["scope_role"])]:
            current["scope_role"] = role

    for raw_army in raw_player_armies:
        admit(raw_army, "player")

    wars: list[tuple[int, list[object], list[object]]] = []
    for raw_war in raw_active_wars:
        if not isinstance(raw_war, dict):
            raise ValueError("army-strength scope contains a malformed war")
        war_id = _positive_int32_id(
            raw_war.get("war_id"), "army-strength scope war_id"
        )
        allied = raw_war.get("allied_armies")
        enemy = raw_war.get("enemy_armies")
        if not isinstance(allied, list) or not isinstance(enemy, list):
            raise ValueError(
                "army-strength scope requires allied and enemy army arrays"
            )
        wars.append((war_id, allied, enemy))
        for raw_army in allied:
            admit(raw_army, "active_war_ally")
        for raw_army in enemy:
            admit(raw_army, "active_war_enemy")

    for war_id, allied, enemy in wars:
        members: set[int] = set()
        for raw_army in [*allied, *enemy]:
            if not isinstance(raw_army, dict):
                raise ValueError(
                    "army-strength scope contains a malformed war army"
                )
            members.add(
                public_cunit_id(
                    raw_army.get("army_id"),
                    "army-strength scope war army_id",
                )
            )
        for army_id in members:
            row = by_id[army_id]
            war_ids = row["war_ids"]
            if isinstance(war_ids, list) and war_id not in war_ids:
                war_ids.append(war_id)
    return rows


def normalize_army_strength_request_ids(value: object) -> list[int]:
    """Validate the explicit MCP subset without silently deduplicating it."""
    if not isinstance(value, list):
        raise ValueError("army_ids must be an array")
    if not 1 <= len(value) <= MAX_ARMY_STRENGTH_REQUEST_IDS:
        raise ValueError(
            "army_ids must contain between 1 and "
            f"{MAX_ARMY_STRENGTH_REQUEST_IDS} IDs"
        )
    result: list[int] = []
    seen: set[int] = set()
    for index, raw_army_id in enumerate(value):
        army_id = public_cunit_id(
            raw_army_id, f"army_ids[{index}]"
        )
        if army_id in seen:
            raise ValueError("army_ids must not contain duplicates")
        seen.add(army_id)
        result.append(army_id)
    return result


def normalize_army_strengths(
    value: object,
    *,
    expected_scope: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """Normalize one exact-build, row-atomic army strength result."""
    if not isinstance(value, list):
        raise ValueError("native army_strengths must be an array")
    rows = [
        _normalize_army_strength_row(
            raw_row, name=f"army_strengths[{index}]"
        )
        for index, raw_row in enumerate(value)
    ]
    ids = [int(row["army_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("native army_strengths contains duplicate ArmyIDs")
    if expected_scope is not None:
        expected_identity = [
            {
                "army_id": public_cunit_id(
                    row.get("army_id"), "expected army-strength scope army_id"
                ),
                "scope_role": row.get("scope_role"),
                "war_ids": row.get("war_ids"),
            }
            for row in expected_scope
        ]
        actual_identity = [
            {
                "army_id": row["army_id"],
                "scope_role": row["scope_role"],
                "war_ids": row["war_ids"],
            }
            for row in rows
        ]
        if actual_identity != expected_identity:
            raise ValueError(
                "native army_strengths does not match the paused snapshot scope"
            )
    return rows


def army_strength_query_status(
    rows: Iterable[dict[str, object]],
) -> str:
    return (
        "available"
        if all(row.get("status") == "available" for row in rows)
        else "partial"
    )


def _normalize_native_army_resolution_v1(
    value: object, *, name: str
) -> dict[str, object]:
    keys = {"status", "ready", "branch", "raw_reference", "reference_index",
            "storage_capacity", "entry_full_id"}
    if not isinstance(value, dict) or value.keys() != keys:
        raise ValueError(f"native {name} schema is malformed")
    status = value["status"]
    if status not in {"available", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    if type(value["ready"]) is not bool or value["ready"] != (status == "available"):
        raise ValueError(f"native {name}.ready is malformed")
    branch = value["branch"]
    if branch not in {"unavailable", "reference_absent", "storage_unavailable",
                      "index_out_of_range", "entry_empty", "full_id_mismatch", "resolved"}:
        raise ValueError(f"native {name}.branch is malformed")
    result = {"status": status, "ready": value["ready"], "branch": branch}
    for key in ("raw_reference", "reference_index", "storage_capacity", "entry_full_id"):
        result[key] = _optional_signed_int32(value[key], f"{name}.{key}")
    return result


def _normalize_army_strength_row(
    value: object, *, name: str
) -> dict[str, object]:
    if (not isinstance(value, dict)
            or not _ARMY_STRENGTH_ROW_KEYS <= value.keys()
            or not value.keys() <= _ARMY_STRENGTH_SUPPLY_ROW_KEYS):
        raise ValueError(f"native {name} schema is malformed")
    observed_supply = {}
    for raw_key, scale_key in _ARMY_STRENGTH_SUPPLY_FIELD_PAIRS:
        if (raw_key in value) != (scale_key in value):
            raise ValueError(f"native {name}.{raw_key} requires its scale")
        if raw_key not in value:
            continue
        raw = value[raw_key]
        if raw is not None and (
            isinstance(raw, bool) or not isinstance(raw, int)
            or not -(2**63) <= raw <= 2**63 - 1
        ):
            raise ValueError(f"native {name}.{raw_key} must be signed int64 or null")
        if value[scale_key] != CK3_FIXED_POINT_SCALE:
            raise ValueError(f"native {name}.{scale_key} must be {CK3_FIXED_POINT_SCALE}")
        if value.get("status") != "available" and raw is not None:
            raise ValueError(f"native unavailable {name}.{raw_key} must be null")
        if raw_key == "merge_supply_destination_weight_raw" and raw is not None and raw < 0:
            raise ValueError(f"native {name}.{raw_key} must be nonnegative")
        observed_supply[raw_key] = raw
        observed_supply[scale_key] = CK3_FIXED_POINT_SCALE
    status = value.get("status")
    if status not in {"available", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    scope_role = value.get("scope_role")
    if scope_role not in _ARMY_STRENGTH_SCOPE_ROLES:
        raise ValueError(f"native {name}.scope_role is malformed")
    war_ids = _strict_positive_int32_id_list(
        value.get("war_ids"), f"{name}.war_ids"
    )
    # This strength DTO reports a generation-checked CArmy database handle.
    # Generation zero/slot zero is valid; null means it was not resolved.
    native_carmy_id = _optional_non_negative_int32(
        value.get("native_carmy_id"), f"{name}.native_carmy_id"
    )
    regiment_count = _optional_non_negative_int32(
        value.get("regiment_count"), f"{name}.regiment_count"
    )
    current_soldiers = _optional_non_negative_int32(
        value.get("current_soldiers"), f"{name}.current_soldiers"
    )
    maximum_soldiers = _optional_non_negative_int32(
        value.get("maximum_soldiers"), f"{name}.maximum_soldiers"
    )
    ai_base_power_raw = value.get("ai_base_power_raw")
    if ai_base_power_raw is not None and (
        isinstance(ai_base_power_raw, bool)
        or not isinstance(ai_base_power_raw, int)
        or ai_base_power_raw < -(2**63)
        or ai_base_power_raw > 2**63 - 1
    ):
        raise ValueError(
            f"native {name}.ai_base_power_raw must be signed int64 or null"
        )
    if value.get("ai_base_power_scale") != CK3_FIXED_POINT_SCALE:
        raise ValueError(
            f"native {name}.ai_base_power_scale must be "
            f"{CK3_FIXED_POINT_SCALE}"
        )
    unavailable_reason = value.get("unavailable_reason")
    aggregates = (
        regiment_count,
        current_soldiers,
        maximum_soldiers,
        ai_base_power_raw,
    )
    if status == "available":
        if native_carmy_id is None or any(item is None for item in aggregates):
            raise ValueError(f"native available {name} is incomplete")
        if unavailable_reason is not None:
            raise ValueError(
                f"native available {name} cannot have unavailable_reason"
            )
    else:
        if any(item is not None for item in aggregates):
            raise ValueError(
                f"native unavailable {name} must null every aggregate"
            )
        if not isinstance(unavailable_reason, str) or not unavailable_reason:
            raise ValueError(
                f"native unavailable {name} requires a reason"
            )
    result = {
        "status": status,
        "army_id": public_cunit_id(value.get("army_id"), f"{name}.army_id"),
        "native_carmy_id": native_carmy_id,
        "scope_role": scope_role,
        "war_ids": war_ids,
        "regiment_count": regiment_count,
        "current_soldiers": current_soldiers,
        "maximum_soldiers": maximum_soldiers,
        "ai_base_power_raw": ai_base_power_raw,
        "ai_base_power_scale": CK3_FIXED_POINT_SCALE,
        "unavailable_reason": unavailable_reason,
    }
    result.update(observed_supply)
    if "native_army_resolution_v1" in value:
        result["native_army_resolution_v1"] = _normalize_native_army_resolution_v1(
            value["native_army_resolution_v1"], name=f"{name}.native_army_resolution_v1"
        )
    if "regiment_replenishment_records_v1" in value:
        result["regiment_replenishment_records_v1"] = normalize_regiment_replenishment_records_v1(
            value["regiment_replenishment_records_v1"]
        )
    result["fixed_chunk0_preparation_inputs_v1"] = normalize_fixed_chunk0_preparation_inputs_v1(
        value.get("fixed_chunk0_preparation_inputs_v1"), expected_army_id=result["army_id"],
        expected_carmy_id=result["native_carmy_id"],
    )
    if "army_update_clock_v1" in value:
        result["army_update_clock_v1"] = normalize_army_update_clock_v1(value["army_update_clock_v1"])
    if "monthly_loss_budget_inputs_v1" in value:
        result["monthly_loss_budget_inputs_v1"] = normalize_monthly_loss_budget_inputs_v1(
            value["monthly_loss_budget_inputs_v1"]
        )
    if "monthly_caller_effect_inputs_v1" in value:
        result["monthly_caller_effect_inputs_v1"] = normalize_monthly_caller_effect_inputs_v1(
            value["monthly_caller_effect_inputs_v1"]
        )
    if "monthly_daily_queue_inputs_v1" in value:
        result["monthly_daily_queue_inputs_v1"] = normalize_monthly_daily_queue_inputs_v1(
            value["monthly_daily_queue_inputs_v1"]
        )
    if "monthly_first_removal_cleanup_inputs_v1" in value:
        result["monthly_first_removal_cleanup_inputs_v1"] = normalize_monthly_first_removal_cleanup_inputs_v1(
            value["monthly_first_removal_cleanup_inputs_v1"]
        )
    if "monthly_current_helper_domain_inputs_v1" in value:
        result["monthly_current_helper_domain_inputs_v1"] = normalize_monthly_current_helper_domain_inputs_v1(
            value["monthly_current_helper_domain_inputs_v1"]
        )
    if "monthly_current_helper_point_store_inputs_v1" in value:
        result["monthly_current_helper_point_store_inputs_v1"] = normalize_monthly_current_helper_point_store_inputs_v1(
            value["monthly_current_helper_point_store_inputs_v1"]
        )
    if "current_province_besieging_contributors_v1" in value:
        result["current_province_besieging_contributors_v1"] = normalize_current_province_besieging_contributors_v1(
            value["current_province_besieging_contributors_v1"]
        )
    if "current_province_supply_contributors_v1" in value:
        result["current_province_supply_contributors_v1"] = normalize_current_province_supply_contributors_v1(
            value["current_province_supply_contributors_v1"]
        )
    if "current_land_resupply_v1" in value:
        result["current_land_resupply_v1"] = normalize_current_land_resupply_v1(
            value["current_land_resupply_v1"]
        )
    if "current_land_supply_rate_inputs_v1" in value:
        result["current_land_supply_rate_inputs_v1"] = normalize_current_land_supply_rate_inputs_v1(
            value["current_land_supply_rate_inputs_v1"]
        )
    if "current_fleet_supply_tick_inputs_v1" in value:
        result["current_fleet_supply_tick_inputs_v1"] = normalize_current_fleet_supply_tick_inputs_v1(
            value["current_fleet_supply_tick_inputs_v1"])
    if "current_daily_supply_dispatch_inputs_v1" in value:
        result["current_daily_supply_dispatch_inputs_v1"] = normalize_current_daily_supply_dispatch_inputs_v1(
            value["current_daily_supply_dispatch_inputs_v1"],
            expected_army_id=result["army_id"], expected_carmy_id=result.get("native_carmy_id"))
    if "future_daily_supply_schedule_inputs_v1" in value:
        result["future_daily_supply_schedule_inputs_v1"] = normalize_future_daily_supply_schedule_inputs_v1(
            value["future_daily_supply_schedule_inputs_v1"],
            expected_army_id=result["army_id"], expected_carmy_id=result.get("native_carmy_id"))
    if "source_derived_next_daily_supply_frame_inputs_v1" in value:
        result["source_derived_next_daily_supply_frame_inputs_v1"] = normalize_source_derived_next_daily_supply_frame_inputs_v1(
            value["source_derived_next_daily_supply_frame_inputs_v1"],
            expected_army_id=result["army_id"], expected_carmy_id=result.get("native_carmy_id"))
    if "current_unit_new_date_schedule_inputs_v1" in value:
        result["current_unit_new_date_schedule_inputs_v1"] = normalize_current_unit_new_date_schedule_inputs_v1(
            value["current_unit_new_date_schedule_inputs_v1"],
            expected_army_id=result["army_id"], expected_carmy_id=result.get("native_carmy_id"))
    if "current_unit_new_date_callback_entry_inputs_v1" in value:
        result["current_unit_new_date_callback_entry_inputs_v1"] = normalize_current_unit_new_date_callback_entry_inputs_v1(
            value["current_unit_new_date_callback_entry_inputs_v1"],
            expected_army_id=result["army_id"], expected_carmy_id=result.get("native_carmy_id"))
    if "current_month_first_refill_call_inputs_v1" in value:
        result["current_month_first_refill_call_inputs_v1"] = normalize_current_month_first_refill_call_inputs_v1(
            value["current_month_first_refill_call_inputs_v1"])
    if "current_daily_assault_loss_inputs_v1" in value:
        result["current_daily_assault_loss_inputs_v1"] = normalize_current_daily_assault_loss_inputs_v1(
            value["current_daily_assault_loss_inputs_v1"])
    if "current_assault_removal_reference_inputs_v1" in value:
        result["current_assault_removal_reference_inputs_v1"] = normalize_current_assault_removal_reference_inputs_v1(
            value["current_assault_removal_reference_inputs_v1"])
    if "current_daily_assault_table_v1" in value:
        result["current_daily_assault_table_v1"] = normalize_current_daily_assault_table_v1(
            value["current_daily_assault_table_v1"])
    if "current_candidate_detachment_mapper_inputs_v1" in value:
        result["current_candidate_detachment_mapper_inputs_v1"] = normalize_current_candidate_detachment_mapper_inputs_v1(
            value["current_candidate_detachment_mapper_inputs_v1"])
    if "current_detachment_data_inputs_v1" in value:
        result["current_detachment_data_inputs_v1"] = normalize_current_detachment_data_inputs_v1(
            value["current_detachment_data_inputs_v1"])
    if "current_detachment_callback_inputs_v1" in value:
        result["current_detachment_callback_inputs_v1"] = normalize_current_detachment_callback_inputs_v1(
            value["current_detachment_callback_inputs_v1"])
    if "current_detachment_store_inputs_v1" in value:
        result["current_detachment_store_inputs_v1"] = normalize_current_detachment_store_inputs_v1(
            value["current_detachment_store_inputs_v1"])
    if "current_character_detachment_inputs_v1" in value:
        result["current_character_detachment_inputs_v1"] = normalize_current_character_detachment_inputs_v1(
            value["current_character_detachment_inputs_v1"])
    if "current_army_condition30_inputs_v1" in value:
        result["current_army_condition30_inputs_v1"] = normalize_current_army_condition30_inputs_v1(
            value["current_army_condition30_inputs_v1"])
    if "current_disembark_penalty_v1" in value:
        if status != "available":
            raise ValueError(f"native unavailable {name} cannot publish current_disembark_penalty_v1")
        result["current_disembark_penalty_v1"] = normalize_current_disembark_penalty_v1(
            value["current_disembark_penalty_v1"])
    if "current_army_flag20_inputs_v1" in value:
        result["current_army_flag20_inputs_v1"] = normalize_current_army_flag20_inputs_v1(
            value["current_army_flag20_inputs_v1"])
    if "current_army_flag21_inputs_v1" in value:
        result["current_army_flag21_inputs_v1"] = normalize_current_army_flag21_inputs_v1(
            value["current_army_flag21_inputs_v1"])
    if "current_selected_title_holder_owner_relation_v1" in value:
        result["current_selected_title_holder_owner_relation_v1"] = normalize_current_selected_title_holder_owner_relation_v1(
            value["current_selected_title_holder_owner_relation_v1"])
    if "current_army_flag31_inputs_v1" in value:
        result["current_army_flag31_inputs_v1"] = normalize_current_army_flag31_inputs_v1(
            value["current_army_flag31_inputs_v1"])
    if "current_army_combat_roles_phase_inputs_v1" in value:
        result["current_army_combat_roles_phase_inputs_v1"] = normalize_current_army_combat_roles_phase_inputs_v1(
            value["current_army_combat_roles_phase_inputs_v1"])
    if "current_post_admission_refresh_inputs_v1" in value:
        result["current_post_admission_refresh_inputs_v1"] = normalize_current_post_admission_refresh_inputs_v1(
            value["current_post_admission_refresh_inputs_v1"])
    if "current_pre_date_character_prefix_inputs_v1" in value:
        result["current_pre_date_character_prefix_inputs_v1"] = normalize_current_pre_date_character_prefix_inputs_v1(
            value["current_pre_date_character_prefix_inputs_v1"])
    if "current_pre_date_dated_append_inputs_v1" in value:
        result["current_pre_date_dated_append_inputs_v1"] = normalize_current_pre_date_dated_append_inputs_v1(
            value["current_pre_date_dated_append_inputs_v1"])
    if "current_daily_assault_roster_admission_v1" in value:
        result["current_daily_assault_roster_admission_v1"] = normalize_current_daily_assault_roster_admission_v1(
            value["current_daily_assault_roster_admission_v1"])
    if "current_pre_date_pending_update_inputs_v1" in value:
        result["current_pre_date_pending_update_inputs_v1"] = normalize_current_pre_date_pending_update_inputs_v1(
            value["current_pre_date_pending_update_inputs_v1"])
    if "scoped_ordered_refill_inputs_v1" in value:
        result["scoped_ordered_refill_inputs_v1"] = normalize_scoped_ordered_refill_inputs_v1(
            value["scoped_ordered_refill_inputs_v1"]
        )
    if "ordered_besieging_refill_inputs_v1" in value:
        result["ordered_besieging_refill_inputs_v1"] = normalize_ordered_besieging_refill_inputs_v1(
            value["ordered_besieging_refill_inputs_v1"]
        )
    result["ordered_besieging_fixed_chunk0_preparation_inputs_v1"] = normalize_ordered_besieging_fixed_chunk0_preparation_inputs_v1(
        value.get("ordered_besieging_fixed_chunk0_preparation_inputs_v1"),
        expected_army_id=result["army_id"], expected_carmy_id=result["native_carmy_id"])
    if "loss_application_inputs_v1" in value:
        result["loss_application_inputs_v1"] = _normalize_loss_application_inputs_v1(
            value["loss_application_inputs_v1"], name=f"{name}.loss_application_inputs_v1"
        )
    if "county_entry_inputs_v1" in value:
        if status != "available":
            raise ValueError(f"native unavailable {name} cannot publish county_entry_inputs_v1")
        result["county_entry_inputs_v1"] = normalize_army_county_entry_inputs_v1(
            value["county_entry_inputs_v1"], current_soldiers=current_soldiers,
            name=f"{name}.county_entry_inputs_v1",
        )
    if "native_owner_recall_inputs_v1" in value:
        result["native_owner_recall_inputs_v1"] = normalize_battle_native_owner_recall_inputs_v1(
            value["native_owner_recall_inputs_v1"], lifecycle_status="available"
        )
    if "native_maa_recruitment_inputs_v1" in value:
        result["native_maa_recruitment_inputs_v1"] = normalize_native_maa_recruitment_inputs_v1(
            value["native_maa_recruitment_inputs_v1"]
        )
    if "owned_regiments_v1" in value:
        result["owned_regiments_v1"] = normalize_owned_regiments_v1(value["owned_regiments_v1"])
    if "regiment_strengths" in value:
        if status != "available":
            raise ValueError(f"native unavailable {name} cannot publish regiment_strengths")
        result["regiment_strengths"] = _normalize_regiment_strengths(
            value["regiment_strengths"], name=f"{name}.regiment_strengths",
            regiment_count=regiment_count, current_soldiers=current_soldiers,
            maximum_soldiers=maximum_soldiers,
        )
    result.update(_normalize_army_gathering_days(value, name=name))
    if "current_movement_progress" in value:
        result["current_movement_progress"] = _normalize_current_movement_progress(
            value["current_movement_progress"], name=f"{name}.current_movement_progress"
        )
    if "regiment_replenishment" in value:
        if status != "available":
            raise ValueError(f"native unavailable {name} cannot publish regiment_replenishment")
        result["regiment_replenishment"] = _normalize_regiment_replenishment(
            value["regiment_replenishment"], name=f"{name}.regiment_replenishment"
        )
    return result


def _normalize_loss_application_inputs_v1(
    value: object, *, name: str
) -> dict[str, object]:
    """Preserve observed native budgets, distinct filtered counts and rate scalars."""
    integer_fields = (
        "raid_association_id", "whole_soldiers", "definition_le_zero_soldiers",
        "supply_eligible_soldiers", "definition_le_zero_supply_eligible_soldiers",
        "current_supply_loss_budget", "siege_loss_budget", "raid_loss_budget",
    )
    rate_fields = ("siege_rate_raw", "raid_rate_raw")
    boolean_fields = ("siege_active", "raid_active")
    data_fields = (*integer_fields, *rate_fields, *boolean_fields)
    if not isinstance(value, dict) or set(value) != {
        "status", "unavailable_reason", "fraction_scale", "soldier_scale", *data_fields,
    }:
        raise ValueError(f"native {name} schema is malformed")
    status = value["status"]
    if type(status) is not str or status not in {"available", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    if type(value["fraction_scale"]) is not int or value["fraction_scale"] != CK3_FIXED_POINT_SCALE:
        raise ValueError(f"native {name}.fraction_scale must be {CK3_FIXED_POINT_SCALE}")
    if type(value["soldier_scale"]) is not int or value["soldier_scale"] != 1:
        raise ValueError(f"native {name}.soldier_scale must be whole soldiers (1)")
    reason = value["unavailable_reason"]
    result = dict(value)
    if status == "unavailable":
        if not isinstance(reason, str) or not reason or any(value[field] is not None for field in data_fields):
            raise ValueError(f"native unavailable {name} requires a reason and null observation fields")
        return result
    if reason is not None:
        raise ValueError(f"native available {name} cannot have unavailable_reason")
    for field in integer_fields:
        result[field] = _signed_int32(value[field], f"{name}.{field}")
    for field in rate_fields:
        raw = value[field]
        if type(raw) is not int or not -(2**63) <= raw <= 2**63 - 1:
            raise ValueError(f"native {name}.{field} must be signed int64")
    for field in boolean_fields:
        result[field] = _strict_bool(value[field], f"{name}.{field}")
    return result


def _normalize_regiment_strengths(
    value: object, *, name: str, regiment_count: int,
    current_soldiers: int, maximum_soldiers: int,
) -> list[dict[str, object]]:
    if not isinstance(value, list) or len(value) != regiment_count:
        raise ValueError(f"native {name} must cover the observed regiment_count")
    result = []
    for index, row in enumerate(value):
        item_name = f"{name}[{index}]"
        core_keys = {
            "army_regiment_id", "current_soldiers", "maximum_soldiers", "scale",
        }
        composition_keys = {
            "maa_type_status", "maa_type_key", "siege_tier_observable",
            "siege_tier", "composition_unavailable_reason",
        }
        supply_eligibility_keys = {
            "native_supply_loss_eligible", "supply_loss_eligibility_unavailable_reason",
        }
        if not isinstance(row, dict) or set(row) not in (
            core_keys, core_keys | composition_keys, core_keys | supply_eligibility_keys,
            core_keys | composition_keys | supply_eligibility_keys,
        ):
            raise ValueError(f"native {item_name} schema is malformed")
        fields = {
            key: _optional_non_negative_int32(row[key], f"{item_name}.{key}")
            for key in ("army_regiment_id", "current_soldiers", "maximum_soldiers")
        }
        if any(number is None for number in fields.values()):
            raise ValueError(f"native {item_name} requires observed integer values")
        if type(row["scale"]) is not int or row["scale"] != 1:
            raise ValueError(f"native {item_name}.scale must be whole soldiers (1)")
        normalized: dict[str, object] = {**fields, "scale": 1}
        if composition_keys <= row.keys():
            status = row["maa_type_status"]
            if not isinstance(status, str) or status not in {
                "available", "absent", "unavailable"
            }:
                raise ValueError(f"native {item_name}.maa_type_status is malformed")
            key = row["maa_type_key"]
            if status == "available":
                if not isinstance(key, str) or not key:
                    raise ValueError(f"native {item_name}.maa_type_key must be observed")
            elif key is not None:
                raise ValueError(f"native {item_name}.maa_type_key must be null")
            tier = _optional_signed_int32(row["siege_tier"], f"{item_name}.siege_tier")
            tier_observable = _strict_bool(
                row["siege_tier_observable"], f"{item_name}.siege_tier_observable"
            )
            if tier_observable is not (tier is not None):
                raise ValueError(f"native {item_name}.siege_tier_observable disagrees with tier")
            reason = row["composition_unavailable_reason"]
            if reason is not None and (not isinstance(reason, str) or not reason):
                raise ValueError(f"native {item_name}.composition_unavailable_reason is malformed")
            normalized.update(
                maa_type_status=status, maa_type_key=key,
                siege_tier_observable=tier_observable, siege_tier=tier,
                composition_unavailable_reason=reason,
            )
        if supply_eligibility_keys <= row.keys():
            eligible = _optional_strict_bool(
                row["native_supply_loss_eligible"], f"{item_name}.native_supply_loss_eligible"
            )
            reason = row["supply_loss_eligibility_unavailable_reason"]
            if ((eligible is None and (not isinstance(reason, str) or not reason))
                    or (eligible is not None and reason is not None)):
                raise ValueError(f"native {item_name} supply eligibility reason disagrees with observation")
            normalized.update(
                native_supply_loss_eligible=eligible,
                supply_loss_eligibility_unavailable_reason=reason,
            )
        result.append(normalized)
    if (sum(row["current_soldiers"] for row in result) != current_soldiers
            or sum(row["maximum_soldiers"] for row in result) != maximum_soldiers):
        raise ValueError(f"native {name} does not match the same-frame strength aggregate")
    return result


def _normalize_current_movement_progress(
    value: object, *, name: str
) -> dict[str, object] | None:
    """Keep native edge observations and an optional whole committed prediction."""
    if value is None:
        return None
    required = {
        "status", "source", "unit_state_raw", "accumulated_movement_weight_raw",
        "cached_edge_speed_raw", "normalized_edge_progress",
        "first_route_edge_remaining_duration", "unavailable_reason",
    }
    if (not isinstance(value, dict) or not required <= value.keys()
            or set(value) - required - {"committed_route_timeline", "current_edge_movement_rate_raw", "native_army_movement_admission", "first_route_edge_weight_cost_raw", "first_edge_arrival_provider_byte_e_u8"}):
        raise ValueError(f"native {name} schema is malformed")
    if value["status"] not in {"available", "not_applicable", "partial", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    if value["source"] != "native_current_route_edge":
        raise ValueError(f"native {name}.source is malformed")
    reason = value["unavailable_reason"]
    if reason is not None and (not isinstance(reason, str) or not reason):
        raise ValueError(f"native {name}.unavailable_reason must be a non-empty string or null")
    normalized = dict(value)
    normalized["unit_state_raw"] = _optional_signed_int32(
        value["unit_state_raw"], f"{name}.unit_state_raw"
    )
    for field in ("accumulated_movement_weight_raw", "cached_edge_speed_raw", "current_edge_movement_rate_raw", "first_route_edge_weight_cost_raw"):
        if field not in value:
            continue
        raw = value[field]
        if raw is not None and (
            type(raw) is not int or not -(2**63) <= raw <= 2**63 - 1
        ):
            raise ValueError(f"native {name}.{field} must be signed int64 or null")
        normalized[field] = raw
    if "native_army_movement_admission" in value:
        admission = value["native_army_movement_admission"]
        if admission is not None and type(admission) is not bool:
            raise ValueError(f"native {name}.native_army_movement_admission must be bool or null")
        normalized["native_army_movement_admission"] = admission
    if "first_edge_arrival_provider_byte_e_u8" in value:
        provider = value["first_edge_arrival_provider_byte_e_u8"]
        if provider is not None and (type(provider) is not int or not 0 <= provider <= 255):
            raise ValueError(f"native {name}.first_edge_arrival_provider_byte_e_u8 must be uint8 or null")
        normalized["first_edge_arrival_provider_byte_e_u8"] = provider
    for field in ("normalized_edge_progress", "first_route_edge_remaining_duration"):
        amount = value[field]
        normalized[field] = (
            None if amount is None else _signed_fixed_point(amount, f"{name}.{field}")
        )
    if "committed_route_timeline" in value:
        normalized["committed_route_timeline"] = _normalize_committed_route_timeline(
            value["committed_route_timeline"], name=f"{name}.committed_route_timeline"
        )
    return normalized


def _normalize_committed_route_timeline(
    value: object, *, name: str
) -> dict[str, object]:
    """Preserve signed native Q100000 days separately from rounded dates."""
    arrays = (
        "committed_route_province_ids", "native_route_prefix_remaining_days_q100000",
        "projected_route_arrival_date_raws",
    )
    final = "native_full_route_remaining_days_q100000"
    if not isinstance(value, dict) or set(value) != {
        "status", "source", "native_duration_scale", "unavailable_reason", final, *arrays,
    }:
        raise ValueError(f"native {name} schema is malformed")
    status = value["status"]
    if status not in {"available", "not_applicable", "unavailable"}:
        raise ValueError(f"native {name}.status is malformed")
    if value["source"] != "native_committed_route" or value["native_duration_scale"] != CK3_FIXED_POINT_SCALE:
        raise ValueError(f"native {name} source or duration scale is malformed")
    reason = value["unavailable_reason"]
    if status == "unavailable":
        if any(value[field] is not None for field in (*arrays, final)):
            raise ValueError(f"native unavailable {name} must null its predictions")
        if not isinstance(reason, str) or not reason:
            raise ValueError(f"native unavailable {name} requires a reason")
        return dict(value)
    if reason is not None or any(not isinstance(value[field], list) for field in arrays):
        raise ValueError(f"native observable {name} arrays or reason are malformed")
    if len({len(value[field]) for field in arrays}) != 1:
        raise ValueError(f"native {name} prefixes are not aligned")
    for province in value[arrays[0]]:
        if type(province) is not int or not 0 < province <= 2**31 - 1:
            raise ValueError(f"native {name} province must be positive int32")
    for raw in value[arrays[1]]:
        if type(raw) is not int or not -(2**63) <= raw <= 2**63 - 1:
            raise ValueError(f"native {name} duration must be signed int64")
    for raw in value[arrays[2]]:
        _signed_int32(raw, f"{name}.projected_route_arrival_date_raws")
    prefixes = value[arrays[1]]
    if status == "available":
        if not prefixes or type(value[final]) is not int or value[final] != prefixes[-1]:
            raise ValueError(f"native available {name} final must equal its last prefix")
    elif prefixes or value[final] is not None:
        raise ValueError(f"native empty {name} must retain empty arrays and null final")
    return dict(value)


def _normalize_army_gathering_days(
    value: dict[str, object], *, name: str
) -> dict[str, object]:
    if not _ARMY_STRENGTH_GATHERING_DAYS_KEYS.intersection(value):
        return {}
    if not _ARMY_STRENGTH_GATHERING_DAYS_KEYS <= value.keys():
        raise ValueError(f"native {name} gathering-days fields are incomplete")
    status = value["gathering_days_status"]
    if status not in {"available", "not_gathering", "unavailable"}:
        raise ValueError(f"native {name}.gathering_days_status is malformed")
    days = _optional_non_negative_int32(
        value["gathering_days_left"], f"{name}.gathering_days_left"
    )
    ready = _strict_bool(value["gathering_days_ready"], f"{name}.gathering_days_ready")
    if (status == "available") != (days is not None):
        raise ValueError(f"native {name}.gathering_days_left disagrees with its status")
    if ready is not (status != "unavailable"):
        raise ValueError(f"native {name}.gathering_days_ready disagrees with its status")
    return {"gathering_days_left": days, "gathering_days_status": status,
            "gathering_days_ready": ready}


def _normalize_regiment_replenishment(
    value: object, *, name: str
) -> list[dict[str, object]]:
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[dict[str, object]] = []
    for index, regiment in enumerate(value):
        item_name = f"{name}[{index}]"
        if not isinstance(regiment, dict) or set(regiment) != {
            "army_regiment_id", "native_data_record_count", "status", "source",
            "unavailable_reason", "chunks"
        }:
            raise ValueError(f"native {item_name} schema is malformed")
        army_regiment_id = _optional_non_negative_int32(
            regiment["army_regiment_id"], f"{item_name}.army_regiment_id"
        )
        if army_regiment_id is None:
            raise ValueError(f"native {item_name}.army_regiment_id is required")
        native_data_record_count = _optional_non_negative_int32(
            regiment["native_data_record_count"], f"{item_name}.native_data_record_count"
        )
        status = regiment["status"]
        if not isinstance(status, str) or status not in {"available", "unavailable"}:
            raise ValueError(f"native {item_name}.status is malformed")
        if regiment["source"] != "native_first_record":
            raise ValueError(f"native {item_name}.source must be native_first_record")
        chunks = regiment["chunks"]
        reason = regiment["unavailable_reason"]
        if not isinstance(chunks, list):
            raise ValueError(f"native {item_name}.chunks must be an array")
        if status == "available":
            if (reason is not None or not chunks
                    or native_data_record_count is None or native_data_record_count < 1):
                raise ValueError(f"native available {item_name} is incomplete")
        elif (chunks or not isinstance(reason, str) or not reason):
            raise ValueError(f"native unavailable {item_name} requires empty chunks and a reason")
        result.append({
            "army_regiment_id": army_regiment_id,
            "native_data_record_count": native_data_record_count,
            "status": status,
            "source": "native_first_record",
            "unavailable_reason": reason,
            "chunks": [
                _normalize_regiment_replenishment_chunk(
                    chunk, name=f"{item_name}.chunks[{chunk_index}]"
                )
                for chunk_index, chunk in enumerate(chunks)
            ],
        })
    return result


def _normalize_regiment_replenishment_chunk(
    value: object, *, name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {
        "persistent_regiment_id", "chunk_index", "current_soldiers",
        "maximum_soldiers", "state_raw", "native_can_replenish",
        "native_chunk_can_replenish",
        "persistent_monthly_replenishment_fraction_raw",
        "persistent_monthly_replenishment_fraction_scale",
    }:
        raise ValueError(f"native {name} schema is malformed")
    result: dict[str, object] = {}
    for key in ("persistent_regiment_id", "chunk_index", "current_soldiers", "maximum_soldiers"):
        number = _optional_non_negative_int32(value[key], f"{name}.{key}")
        if number is None:
            raise ValueError(f"native {name}.{key} is required")
        result[key] = number
    if int(result["chunk_index"]) > 6:
        raise ValueError(f"native {name}.chunk_index must be in range 0..6")
    result["state_raw"] = _signed_int32(value["state_raw"], f"{name}.state_raw")
    for key in ("native_can_replenish", "native_chunk_can_replenish"):
        result[key] = _strict_bool(value[key], f"{name}.{key}")
    raw_key = "persistent_monthly_replenishment_fraction_raw"
    raw = value[raw_key]
    if (isinstance(raw, bool) or not isinstance(raw, int)
            or not -(2**63) <= raw <= 2**63 - 1):
        raise ValueError(f"native {name}.{raw_key} must be signed int64")
    scale_key = "persistent_monthly_replenishment_fraction_scale"
    scale = value[scale_key]
    if (isinstance(scale, bool) or not isinstance(scale, int)
            or scale != CK3_FIXED_POINT_SCALE):
        raise ValueError(f"native {name}.{scale_key} must be {CK3_FIXED_POINT_SCALE}")
    result[raw_key] = raw
    result[scale_key] = CK3_FIXED_POINT_SCALE
    return result


def halt_army_step(army_id: int) -> str:
    return f"halt-army-{public_cunit_id(army_id, 'army_id')}"


def parse_halt_army_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("halt-army-"):
        return None
    text = step.removeprefix("halt-army-")
    if not canonical_public_cunit_decimal(text):
        return None
    value = int(text)
    return value if 0 <= value <= 2**31 - 1 else None


def move_army_step(army_id: int, province_id: int) -> str:
    return (
        f"move-army-{public_cunit_id(army_id, 'army_id')}"
        f"-to-{_positive_int32_id(province_id, 'province_id')}"
    )


def preview_move_army_step(army_id: int, province_id: int) -> str:
    return (
        f"preview-move-army-{public_cunit_id(army_id, 'army_id')}"
        f"-to-{_positive_int32_id(province_id, 'province_id')}"
    )


def query_route_contact_horizon_step(
    subject_army_id: int,
    target_province_id: int,
    hostile_army_ids: Iterable[int],
) -> str:
    """Build the canonical exact-build route/contact query literal."""
    subject = public_cunit_id(subject_army_id, "subject_army_id")
    target = _positive_int32_id(target_province_id, "target_province_id")
    hostiles = sorted(
        {
            public_cunit_id(army_id, "hostile_army_ids")
            for army_id in hostile_army_ids
        }
    )
    if not hostiles or len(hostiles) > MAX_ROUTE_CONTACT_HOSTILE_IDS:
        raise ValueError(
            "hostile_army_ids must contain 1..64 unique public CUnit int32 IDs"
        )
    if subject in hostiles:
        raise ValueError("subject army cannot also be hostile")
    suffix = "-".join(str(army_id) for army_id in hostiles)
    return (
        f"query-route-contact-horizon-v1-{subject}-to-{target}"
        f"-h-{len(hostiles)}-{suffix}"
    )


def advance_route_contact_horizon_step(
    subject_army_id: int,
    target_province_id: int,
    hostile_army_ids: Iterable[int],
) -> str:
    """Build the proof-bound one-day composite step literal."""
    query = query_route_contact_horizon_step(
        subject_army_id, target_province_id, hostile_army_ids
    )
    return ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX + query.removeprefix(
        "query-route-contact-horizon-v1-"
    )


def disband_army_step(army_id: int) -> str:
    return f"disband-army-{public_cunit_id(army_id, 'army_id')}"


def split_army_half_step(army_id: int) -> str:
    return f"split-army-half-{public_cunit_id(army_id, 'army_id')}"


def merge_armies_step(
    destination_army_id: int, source_army_id: int
) -> str:
    destination = public_cunit_id(
        destination_army_id, "destination_army_id"
    )
    source = public_cunit_id(source_army_id, "source_army_id")
    if destination == source:
        raise ValueError("merge army IDs must be distinct")
    return f"merge-armies-{destination}-with-{source}"


def start_assault_step(siege_id: int) -> str:
    return f"start-assault-{_positive_int32_id(siege_id, 'siege_id')}"


def stop_assault_step(siege_id: int) -> str:
    return f"stop-assault-{_positive_int32_id(siege_id, 'siege_id')}"


def enforce_demands_step(war_id: int) -> str:
    return f"enforce-demands-{_non_negative_id(war_id, 'war_id')}"


def query_war_termination_options_step(war_id: int) -> str:
    return (
        "query-war-termination-options-"
        f"{_positive_int32_id(war_id, 'war_id')}"
    )


def query_war_prisoner_release_pairs_v1_step(war_id: int) -> str:
    return (
        "query-war-prisoner-release-pairs-v1-"
        f"{_positive_int32_id(war_id, 'war_id')}"
    )


def query_outbound_war_white_peace_status_step(war_id: int) -> str:
    return (
        "query-outbound-war-white-peace-status-v1-"
        f"{_positive_int32_id(war_id, 'war_id')}"
    )


def query_war_termination_terms_step(war_id: int) -> str:
    return (
        "query-war-termination-terms-v1-"
        f"{_positive_int32_id(war_id, 'war_id')}"
    )


def surrender_war_step(war_id: int) -> str:
    return f"surrender-war-{_positive_int32_id(war_id, 'war_id')}"


def offer_white_peace_step(war_id: int) -> str:
    return f"offer-white-peace-{_positive_int32_id(war_id, 'war_id')}"


def parse_move_army_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith("move-army-"):
        return None
    payload = step.removeprefix("move-army-")
    army_text, separator, province_text = payload.partition("-to-")
    if (
        not separator
        or not canonical_public_cunit_decimal(army_text)
        or not province_text.isascii()
        or not province_text.isdigit()
        or province_text.startswith("0")
    ):
        return None
    army_id = int(army_text)
    province_id = int(province_text)
    if not (0 <= army_id <= 2**31 - 1 and 0 < province_id <= 2**31 - 1):
        return None
    return army_id, province_id


def parse_preview_move_army_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith("preview-move-army-"):
        return None
    payload = step.removeprefix("preview-move-army-")
    army_text, separator, province_text = payload.partition("-to-")
    if (
        not separator
        or not canonical_public_cunit_decimal(army_text)
        or not province_text.isascii()
        or not province_text.isdigit()
        or province_text.startswith("0")
    ):
        return None
    army_id = int(army_text)
    province_id = int(province_text)
    if not (0 <= army_id <= 2**31 - 1 and 0 < province_id <= 2**31 - 1):
        return None
    return army_id, province_id


def parse_query_route_contact_horizon_step(
    step: object,
) -> tuple[int, int, tuple[int, ...]] | None:
    prefix = "query-route-contact-horizon-v1-"
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    payload = step.removeprefix(prefix)
    subject_text, to_separator, tail = payload.partition("-to-")
    target_text, hostile_separator, hostile_tail = tail.partition("-h-")
    if (
        not to_separator
        or not hostile_separator
        or not canonical_public_cunit_decimal(subject_text)
        or not target_text.isascii()
        or not target_text.isdigit()
    ):
        return None
    count_text, count_separator, ids_text = hostile_tail.partition("-")
    if not count_separator or not count_text.isdigit() or not ids_text:
        return None
    subject = int(subject_text)
    target = int(target_text)
    count = int(count_text)
    id_tokens = ids_text.split("-")
    if (
        not 0 <= subject <= 2**31 - 1
        or not 0 < target <= 2**31 - 1
        or not 0 < count <= MAX_ROUTE_CONTACT_HOSTILE_IDS
        or len(id_tokens) != count
        or any(not canonical_public_cunit_decimal(token) for token in id_tokens)
    ):
        return None
    hostiles = tuple(int(token) for token in id_tokens)
    if (
        any(not 0 <= army_id <= 2**31 - 1 for army_id in hostiles)
        or tuple(sorted(set(hostiles))) != hostiles
        or subject in hostiles
    ):
        return None
    return subject, target, hostiles


def parse_advance_route_contact_horizon_step(
    step: object,
) -> tuple[int, int, tuple[int, ...]] | None:
    if not isinstance(step, str) or not step.startswith(
        ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX
    ):
        return None
    query = "query-route-contact-horizon-v1-" + step.removeprefix(
        ADVANCE_ROUTE_CONTACT_HORIZON_STEP_PREFIX
    )
    return parse_query_route_contact_horizon_step(query)


def battle_decision_epoch_advance_step(target_date_raw: int) -> str:
    if (
        isinstance(target_date_raw, bool)
        or not isinstance(target_date_raw, int)
        or not 0 < target_date_raw <= 2**63 - 1
    ):
        raise ValueError("target_date_raw must be a positive signed int64")
    return f"{BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX}{target_date_raw}"


def parse_battle_decision_epoch_advance_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith(
        BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX
    ):
        return None
    target_text = step.removeprefix(
        BATTLE_DECISION_EPOCH_ADVANCE_STEP_PREFIX
    )
    if (
        not target_text.isascii()
        or not target_text.isascii()
        or not target_text.isdigit()
        or target_text.startswith("0")
    ):
        return None
    target_date_raw = int(target_text)
    return target_date_raw if 0 < target_date_raw <= 2**63 - 1 else None


def committed_route_sentinel_advance_step(
    subject_army_id: int,
    target_province_id: int,
    target_date_raw: int,
    *,
    timeline_speed: int = 3,
) -> str:
    for name, value, maximum in (
        ("target_province_id", target_province_id, 2**31 - 1),
        ("target_date_raw", target_date_raw, 2**63 - 1),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 < value <= maximum
        ):
            raise ValueError(f"{name} must be a positive signed integer")
    public_cunit_id(subject_army_id, "subject_army_id")
    speed_suffix = _war_sentinel_speed_suffix(timeline_speed)
    return (
        f"{COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX}"
        f"{subject_army_id}-to-{target_province_id}-until-{target_date_raw}"
        f"{speed_suffix}"
    )


def parse_committed_route_sentinel_advance_step(
    step: object,
) -> tuple[int, int, int] | None:
    parsed = _parse_committed_route_sentinel_advance_step(step)
    return parsed[:3] if parsed is not None else None


def parse_committed_route_sentinel_advance_speed(
    step: object,
) -> int | None:
    parsed = _parse_committed_route_sentinel_advance_step(step)
    return parsed[3] if parsed is not None else None


def _parse_committed_route_sentinel_advance_step(
    step: object,
) -> tuple[int, int, int, int] | None:
    if not isinstance(step, str) or not step.startswith(
        COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX
    ):
        return None
    payload = step.removeprefix(
        COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP_PREFIX
    )
    subject_text, to_separator, remainder = payload.partition("-to-")
    target_text, until_separator, date_payload = remainder.partition("-until-")
    parsed_date = _parse_war_sentinel_date_and_speed(date_payload)
    date_text, timeline_speed = (
        parsed_date if parsed_date is not None else ("", 0)
    )
    if (
        not to_separator
        or not until_separator
        or not canonical_public_cunit_decimal(subject_text)
        or not target_text.isascii()
        or not target_text.isdigit()
        or target_text.startswith("0")
        or not date_text.isascii()
        or not date_text.isdigit()
        or date_text.startswith("0")
    ):
        return None
    subject_army_id = int(subject_text)
    target_province_id = int(target_text)
    target_date_raw = int(date_text)
    if (
        not 0 <= subject_army_id <= 2**31 - 1
        or not 0 < target_province_id <= 2**31 - 1
        or not 0 < target_date_raw <= 2**63 - 1
    ):
        return None
    return (
        subject_army_id,
        target_province_id,
        target_date_raw,
        timeline_speed,
    )


def war_objective_hold_sentinel_advance_step(
    war_id: int,
    subject_army_id: int,
    objective_province_id: int,
    target_date_raw: int,
    *,
    timeline_speed: int = 3,
) -> str:
    for name, value, maximum in (
        ("war_id", war_id, 2**31 - 1),
        ("objective_province_id", objective_province_id, 2**31 - 1),
        ("target_date_raw", target_date_raw, 2**63 - 1),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or not 0 < value <= maximum
        ):
            raise ValueError(f"{name} must be a positive signed integer")
    public_cunit_id(subject_army_id, "subject_army_id")
    speed_suffix = _war_sentinel_speed_suffix(timeline_speed)
    return (
        f"{WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX}{war_id}"
        f"-army-{subject_army_id}-at-{objective_province_id}"
        f"-until-{target_date_raw}{speed_suffix}"
    )


def parse_war_objective_hold_sentinel_advance_step(
    step: object,
) -> tuple[int, int, int, int] | None:
    parsed = _parse_war_objective_hold_sentinel_advance_step(step)
    return parsed[:4] if parsed is not None else None


def parse_war_objective_hold_sentinel_advance_speed(
    step: object,
) -> int | None:
    parsed = _parse_war_objective_hold_sentinel_advance_step(step)
    return parsed[4] if parsed is not None else None


def _parse_war_objective_hold_sentinel_advance_step(
    step: object,
) -> tuple[int, int, int, int, int] | None:
    if not isinstance(step, str) or not step.startswith(
        WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX
    ):
        return None
    payload = step.removeprefix(
        WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP_PREFIX
    )
    war_text, army_separator, remainder = payload.partition("-army-")
    subject_text, objective_separator, remainder = remainder.partition("-at-")
    objective_text, date_separator, date_payload = remainder.partition("-until-")
    parsed_date = _parse_war_sentinel_date_and_speed(date_payload)
    date_text, timeline_speed = (
        parsed_date if parsed_date is not None else ("", 0)
    )
    tokens = (war_text, subject_text, objective_text, date_text)
    if (
        not army_separator
        or not objective_separator
        or not date_separator
        or any(
            not token.isascii()
            or not token.isdigit()
            or (token.startswith("0") and not (token == subject_text == "0"))
            for token in tokens
        )
    ):
        return None
    war_id, subject_army_id, objective_province_id, target_date_raw = (
        int(token) for token in tokens
    )
    if (
        not 0 < war_id <= 2**31 - 1
        or not 0 <= subject_army_id <= 2**31 - 1
        or not 0 < objective_province_id <= 2**31 - 1
        or not 0 < target_date_raw <= 2**63 - 1
    ):
        return None
    return (
        war_id,
        subject_army_id,
        objective_province_id,
        target_date_raw,
        timeline_speed,
    )


def _war_sentinel_speed_suffix(timeline_speed: object) -> str:
    if (
        isinstance(timeline_speed, bool)
        or not isinstance(timeline_speed, int)
        or timeline_speed not in {1, 2, 3, 4, 5}
    ):
        raise ValueError("timeline_speed must be an integer from 1 through 5")
    return "" if timeline_speed == 3 else f"-speed-{timeline_speed}"


def _parse_war_sentinel_date_and_speed(
    payload: str,
) -> tuple[str, int] | None:
    date_text, speed_separator, speed_text = payload.partition("-speed-")
    if not speed_separator:
        return date_text, 3
    # Speed 3 has one canonical spelling: the legacy unsuffixed production
    # literal.  Other speeds are explicit A/B bindings in the step itself.
    if speed_text not in {"1", "2", "4", "5"}:
        return None
    return date_text, int(speed_text)


def is_life_advance_step(step: object) -> bool:
    return bool(
        step == "life-advance"
        or step == "life-advance-one-day"
        or (
            isinstance(step, str)
            and step in BATTLE_SENTINEL_ADVANCE_STEPS
        )
        or parse_battle_decision_epoch_advance_step(step) is not None
        or parse_committed_route_sentinel_advance_step(step) is not None
        or parse_war_objective_hold_sentinel_advance_step(step) is not None
        or parse_advance_route_contact_horizon_step(step) is not None
    )


def parse_disband_army_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("disband-army-"):
        return None
    army_text = step.removeprefix("disband-army-")
    if not canonical_public_cunit_decimal(army_text):
        return None
    army_id = int(army_text)
    return army_id if 0 <= army_id <= 2**31 - 1 else None


def parse_split_army_half_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("split-army-half-"):
        return None
    army_text = step.removeprefix("split-army-half-")
    if not canonical_public_cunit_decimal(army_text):
        return None
    army_id = int(army_text)
    return army_id if 0 <= army_id <= 2**31 - 1 else None


def parse_merge_armies_step(step: object) -> tuple[int, int] | None:
    if not isinstance(step, str) or not step.startswith("merge-armies-"):
        return None
    payload = step.removeprefix("merge-armies-")
    destination_text, separator, source_text = payload.partition("-with-")
    if (
        not separator
        or not destination_text.isascii()
        or not canonical_public_cunit_decimal(destination_text)
        or not source_text.isascii()
        or not canonical_public_cunit_decimal(source_text)
    ):
        return None
    destination = int(destination_text)
    source = int(source_text)
    if not (
        0 <= destination <= 2**31 - 1
        and 0 <= source <= 2**31 - 1
        and destination != source
    ):
        return None
    return destination, source


def observe_merge_armies_postcondition_v1(
    step: object,
    result: object,
    snapshot: object,
) -> dict[str, object]:
    """Classify one merge receipt against a later paused public frame.

    A native queue ACK is not proof that CK3 removed the source army.  The
    receipt therefore carries the exact pre-submit army set and, for new
    producers, the paused frame/identity binding.  Only an independently
    published frame with the exact source-removal delta may consume a
    ``merge_submitted`` receipt.  Older unbound receipts remain pending
    instead of being guessed from a later army set.
    """
    parsed = parse_merge_armies_step(step)
    action = result.get("war_action") if isinstance(result, dict) else None
    if parsed is None or not isinstance(action, dict):
        return {
            "status": "receipt_invalid",
            "reason": "merge receipt is absent or malformed",
        }
    destination_army_id, source_army_id = parsed
    receipt_status = action.get("status")
    before_raw = action.get("player_army_ids_before")
    if not (
        receipt_status in {"merge_submitted", "merge_applied"}
        and action.get("destination_army_id") == destination_army_id
        and action.get("source_army_id") == source_army_id
        and isinstance(before_raw, list)
    ):
        return {
            "status": "receipt_invalid",
            "reason": "merge receipt identity or status is malformed",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
        }
    before_ids = [
        int(army_id)
        for army_id in before_raw
        if isinstance(army_id, int)
        and not isinstance(army_id, bool)
        and 0 <= army_id <= 2**31 - 1
    ]
    if (
        len(before_ids) != len(before_raw)
        or len(set(before_ids)) != len(before_ids)
        or before_ids != sorted(before_ids)
        or destination_army_id not in before_ids
        or source_army_id not in before_ids
    ):
        return {
            "status": "receipt_invalid",
            "reason": "merge receipt pre-submit army set is malformed",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
        }
    submitted_date_raw = action.get("submitted_date_raw")
    if (
        isinstance(submitted_date_raw, bool)
        or not isinstance(submitted_date_raw, int)
        or submitted_date_raw < 0
    ):
        return {
            "status": "receipt_invalid",
            "reason": "merge receipt submitted date is malformed",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
        }
    submitted_snapshot_id = action.get("submitted_snapshot_id")
    submitted_revision = action.get("submitted_public_revision")
    submitted_native_revision = action.get("submitted_native_revision")
    submitted_episode_run_id = action.get("submitted_episode_run_id")
    observed_snapshot_id = action.get("observed_snapshot_id")
    observed_revision = action.get("observed_public_revision")
    observed_native_revision = action.get("observed_native_revision")
    observed_date_raw = action.get("observed_date_raw")
    observed_episode_run_id = action.get("observed_episode_run_id")
    after_raw = action.get("player_army_ids_after")
    durable_applied = bool(
        receipt_status == "merge_applied"
        and action.get("postcondition_verified") is True
        and action.get("source_army_id_absent") is True
        and isinstance(submitted_snapshot_id, str)
        and submitted_snapshot_id
        and isinstance(submitted_revision, int)
        and not isinstance(submitted_revision, bool)
        and submitted_revision >= 0
        and isinstance(submitted_native_revision, int)
        and not isinstance(submitted_native_revision, bool)
        and submitted_native_revision >= 0
        and isinstance(submitted_episode_run_id, str)
        and submitted_episode_run_id
        and isinstance(observed_snapshot_id, str)
        and observed_snapshot_id
        and observed_snapshot_id != submitted_snapshot_id
        and isinstance(observed_revision, int)
        and not isinstance(observed_revision, bool)
        and observed_revision > submitted_revision
        and isinstance(observed_native_revision, int)
        and not isinstance(observed_native_revision, bool)
        and observed_native_revision > submitted_native_revision
        and isinstance(observed_date_raw, int)
        and not isinstance(observed_date_raw, bool)
        and observed_date_raw >= submitted_date_raw
        and observed_episode_run_id == submitted_episode_run_id
        and isinstance(after_raw, list)
        and after_raw == sorted(set(before_ids) - {source_army_id})
    )
    if durable_applied:
        return {
            "status": "applied",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
            "receipt_status": receipt_status,
            "receipt_bound": True,
            "independently_published": True,
            "postcondition_consumed": True,
            "submitted_snapshot_id": submitted_snapshot_id,
            "submitted_public_revision": submitted_revision,
            "submitted_native_revision": submitted_native_revision,
            "observed_snapshot_id": observed_snapshot_id,
            "observed_public_revision": observed_revision,
            "observed_native_revision": observed_native_revision,
            "player_army_ids_before": before_ids,
            "current_player_army_ids": list(after_raw),
        }
    if not isinstance(snapshot, dict):
        return {
            "status": "postcondition_unavailable",
            "reason": "merge postcondition snapshot is unavailable",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
        }
    armies_raw = snapshot.get("player_armies")
    if not isinstance(armies_raw, list):
        return {
            "status": "postcondition_unavailable",
            "reason": "merge postcondition lacks player armies",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
        }
    controllable = [
        army
        for army in armies_raw
        if isinstance(army, dict) and army.get("controllable") is True
    ]
    current_ids = [
        int(army["army_id"])
        for army in controllable
        if isinstance(army.get("army_id"), int)
        and not isinstance(army.get("army_id"), bool)
        and 0 <= int(army["army_id"]) <= 2**31 - 1
    ]
    if len(current_ids) != len(controllable) or len(set(current_ids)) != len(
        current_ids
    ):
        return {
            "status": "postcondition_inconsistent",
            "reason": "merge postcondition army identity set is malformed",
            "destination_army_id": destination_army_id,
            "source_army_id": source_army_id,
        }
    current_set = set(current_ids)
    destination = next(
        (
            army
            for army in controllable
            if army.get("army_id") == destination_army_id
        ),
        None,
    )
    source = next(
        (
            army
            for army in controllable
            if army.get("army_id") == source_army_id
        ),
        None,
    )
    destination_owner_character_id = action.get(
        "destination_owner_character_id"
    )
    destination_province_id = action.get("destination_province_id")
    source_owner_character_id = action.get("source_owner_character_id")
    source_province_id = action.get("source_province_id")
    receipt_bound = bool(
        isinstance(submitted_snapshot_id, str)
        and submitted_snapshot_id
        and isinstance(submitted_revision, int)
        and not isinstance(submitted_revision, bool)
        and submitted_revision >= 0
        and isinstance(submitted_native_revision, int)
        and not isinstance(submitted_native_revision, bool)
        and submitted_native_revision >= 0
        and isinstance(submitted_episode_run_id, str)
        and submitted_episode_run_id
        and isinstance(destination_owner_character_id, int)
        and not isinstance(destination_owner_character_id, bool)
        and destination_owner_character_id > 0
        and isinstance(destination_province_id, int)
        and not isinstance(destination_province_id, bool)
        and destination_province_id > 0
        and isinstance(source_owner_character_id, int)
        and not isinstance(source_owner_character_id, bool)
        and source_owner_character_id > 0
        and isinstance(source_province_id, int)
        and not isinstance(source_province_id, bool)
        and source_province_id > 0
    )
    observed_revision = snapshot.get("revision")
    observed_native_revision = snapshot.get("native_revision")
    independently_published = bool(
        receipt_bound
        and snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("episode_run_id") == submitted_episode_run_id
        and isinstance(observed_revision, int)
        and not isinstance(observed_revision, bool)
        and observed_revision > submitted_revision
        and isinstance(observed_native_revision, int)
        and not isinstance(observed_native_revision, bool)
        and observed_native_revision > submitted_native_revision
        and snapshot.get("snapshot_id") != submitted_snapshot_id
        and isinstance(snapshot.get("date_raw"), int)
        and not isinstance(snapshot.get("date_raw"), bool)
        and int(snapshot["date_raw"]) >= submitted_date_raw
    )

    def same_bound_army(
        army: object, *, owner_character_id: object, province_id: object
    ) -> bool:
        return bool(
            isinstance(army, dict)
            and (
                not receipt_bound
                or (
                    army.get("owner_character_id") == owner_character_id
                    and army.get("current_province_id") == province_id
                )
            )
        )

    exact_applied = bool(
        current_set == set(before_ids) - {source_army_id}
        and same_bound_army(
            destination,
            owner_character_id=destination_owner_character_id,
            province_id=destination_province_id,
        )
        and source is None
    )
    exact_unchanged = bool(
        current_set == set(before_ids)
        and same_bound_army(
            destination,
            owner_character_id=destination_owner_character_id,
            province_id=destination_province_id,
        )
        and same_bound_army(
            source,
            owner_character_id=source_owner_character_id,
            province_id=source_province_id,
        )
    )
    common = {
        "destination_army_id": destination_army_id,
        "source_army_id": source_army_id,
        "receipt_status": receipt_status,
        "receipt_bound": receipt_bound,
        "independently_published": independently_published,
        "submitted_snapshot_id": submitted_snapshot_id,
        "submitted_public_revision": submitted_revision,
        "submitted_native_revision": submitted_native_revision,
        "observed_snapshot_id": snapshot.get("snapshot_id"),
        "observed_public_revision": observed_revision,
        "observed_native_revision": observed_native_revision,
        "player_army_ids_before": before_ids,
        "current_player_army_ids": sorted(current_set),
    }
    if exact_applied:
        return {
            "status": "postcondition_observed_unconsumed",
            "reason": "source removal was not persisted in the merge command receipt",
            **common,
        }
    if exact_unchanged:
        return {
            "status": (
                "pending_observed"
                if independently_published
                else "pending_same_frame"
            ),
            **common,
        }
    if not receipt_bound and receipt_status == "merge_submitted":
        return {
            "status": "postcondition_unbound",
            "reason": "legacy merge ACK lacks an independent-frame binding",
            **common,
        }
    return {
        "status": "postcondition_inconsistent",
        "reason": "paused army set is neither the exact pre-submit nor source-removal set",
        **common,
    }


def parse_start_assault_step(step: object) -> int | None:
    return _parse_assault_step(step, prefix="start-assault-")


def parse_stop_assault_step(step: object) -> int | None:
    return _parse_assault_step(step, prefix="stop-assault-")


def _parse_assault_step(step: object, *, prefix: str) -> int | None:
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    siege_text = step.removeprefix(prefix)
    if not siege_text.isascii() or not siege_text.isdecimal():
        return None
    siege_id = int(siege_text)
    return siege_id if 0 < siege_id <= 2**31 - 1 else None


def parse_enforce_demands_step(step: object) -> int | None:
    if not isinstance(step, str) or not step.startswith("enforce-demands-"):
        return None
    war_text = step.removeprefix("enforce-demands-")
    return int(war_text) if war_text.isdigit() else None


def parse_query_war_termination_options_step(step: object) -> int | None:
    return _parse_generation_war_step(
        step, prefix="query-war-termination-options-"
    )


def parse_query_war_prisoner_release_pairs_v1_step(step: object) -> int | None:
    return _parse_generation_war_step(
        step, prefix="query-war-prisoner-release-pairs-v1-"
    )


def parse_query_outbound_war_white_peace_status_step(
    step: object,
) -> int | None:
    return _parse_generation_war_step(
        step, prefix="query-outbound-war-white-peace-status-v1-"
    )


def parse_query_war_termination_terms_step(step: object) -> int | None:
    return _parse_generation_war_step(
        step, prefix="query-war-termination-terms-v1-"
    )


def parse_surrender_war_step(step: object) -> int | None:
    return _parse_generation_war_step(step, prefix="surrender-war-")


def parse_offer_white_peace_step(step: object) -> int | None:
    return _parse_generation_war_step(step, prefix="offer-white-peace-")


def _parse_generation_war_step(step: object, *, prefix: str) -> int | None:
    """Parse only the canonical spelling of a full-generation WarID step."""
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    war_text = step.removeprefix(prefix)
    if (
        not war_text
        or not war_text.isascii()
        or not war_text.isdecimal()
        or war_text.startswith("0")
    ):
        return None
    war_id = int(war_text)
    return war_id if 0 < war_id <= 2**31 - 1 else None


def _normalize_raiktor_character_fixed_point(
    value: object, name: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"character_id", "value"}:
        raise ValueError(f"native {name} schema is malformed")
    return {
        "character_id": _positive_int32_id(
            value.get("character_id"), f"{name}.character_id"
        ),
        "value": _signed_fixed_point(value.get("value"), f"{name}.value"),
    }


def _normalize_raiktor_gold_reparations(
    value: object,
) -> dict[str, object]:
    name = "war_termination_terms.gold_reparations"
    if not isinstance(value, dict) or set(value) != set(
        _TERMINATION_TERMS_RAIKTOR_GOLD_REPARATIONS
    ):
        raise ValueError(f"native {name} schema is malformed")
    for field in (
        "direction",
        "factor",
        "positive_income_basis",
        "fallback_condition",
        "fallback_basis",
        "defender_culture_multiplier",
    ):
        if value.get(field) != _TERMINATION_TERMS_RAIKTOR_GOLD_REPARATIONS[field]:
            raise ValueError(f"native {name}.{field} drifted")
    observable = _strict_bool(
        value.get("actual_amount_observable"),
        f"{name}.actual_amount_observable",
    )
    dynamic_fields = (
        "attacker_current_gold",
        "defender_current_gold",
        "attacker_authoritative_monthly_gold_income",
        "defender_authoritative_monthly_gold_income",
        "actual_transfer",
    )
    if not observable:
        if any(value.get(field) is not None for field in dynamic_fields):
            raise ValueError(f"native {name} unavailable values are malformed")
        return dict(_TERMINATION_TERMS_RAIKTOR_GOLD_REPARATIONS)

    attacker = _normalize_raiktor_character_fixed_point(
        value.get("attacker_current_gold"), f"{name}.attacker_current_gold"
    )
    defender = _normalize_raiktor_character_fixed_point(
        value.get("defender_current_gold"), f"{name}.defender_current_gold"
    )
    attacker_income = _normalize_raiktor_character_fixed_point(
        value.get("attacker_authoritative_monthly_gold_income"),
        f"{name}.attacker_authoritative_monthly_gold_income",
    )
    defender_income = _normalize_raiktor_character_fixed_point(
        value.get("defender_authoritative_monthly_gold_income"),
        f"{name}.defender_authoritative_monthly_gold_income",
    )
    transfer = value.get("actual_transfer")
    if not isinstance(transfer, dict) or set(transfer) != {
        "from_character_id",
        "to_character_id",
        "value",
    }:
        raise ValueError(f"native {name}.actual_transfer schema is malformed")
    normalized_transfer = {
        "from_character_id": _positive_int32_id(
            transfer.get("from_character_id"),
            f"{name}.actual_transfer.from_character_id",
        ),
        "to_character_id": _positive_int32_id(
            transfer.get("to_character_id"),
            f"{name}.actual_transfer.to_character_id",
        ),
        "value": _signed_fixed_point(
            transfer.get("value"), f"{name}.actual_transfer.value"
        ),
    }
    attacker_id = attacker["character_id"]
    defender_id = defender["character_id"]
    if (
        attacker_id == defender_id
        or attacker_income["character_id"] != attacker_id
        or defender_income["character_id"] != defender_id
        or normalized_transfer["from_character_id"] != attacker_id
        or normalized_transfer["to_character_id"] != defender_id
        or normalized_transfer["value"]["raw"] < 0
    ):
        raise ValueError(f"native {name} primary identities/direction are malformed")
    return {
        **{
            field: _TERMINATION_TERMS_RAIKTOR_GOLD_REPARATIONS[field]
            for field in (
                "direction",
                "factor",
                "positive_income_basis",
                "fallback_condition",
                "fallback_basis",
                "defender_culture_multiplier",
            )
        },
        "actual_amount_observable": True,
        "attacker_current_gold": attacker,
        "defender_current_gold": defender,
        "attacker_authoritative_monthly_gold_income": attacker_income,
        "defender_authoritative_monthly_gold_income": defender_income,
        "actual_transfer": normalized_transfer,
    }


def _normalize_raiktor_attacker_fame(value: object) -> dict[str, object]:
    name = "war_termination_terms.attacker_fame"
    if not isinstance(value, dict) or set(value) != set(
        _TERMINATION_TERMS_RAIKTOR_ATTACKER_FAME
    ):
        raise ValueError(f"native {name} schema is malformed")
    for field in ("resource", "base", "scale", "limit_rule"):
        if value.get(field) != _TERMINATION_TERMS_RAIKTOR_ATTACKER_FAME[field]:
            raise ValueError(f"native {name}.{field} drifted")
    observable = _strict_bool(
        value.get("actual_delta_observable"),
        f"{name}.actual_delta_observable",
    )
    dynamic_fields = (
        "attacker_current_prestige",
        "cb_prestige_factor",
        "attacker_prestige_delta",
    )
    if not observable:
        if any(value.get(field) is not None for field in dynamic_fields):
            raise ValueError(f"native {name} unavailable values are malformed")
        return dict(_TERMINATION_TERMS_RAIKTOR_ATTACKER_FAME)

    current = _normalize_raiktor_character_fixed_point(
        value.get("attacker_current_prestige"),
        f"{name}.attacker_current_prestige",
    )
    factor = _signed_fixed_point(
        value.get("cb_prestige_factor"), f"{name}.cb_prestige_factor"
    )
    delta = _normalize_raiktor_character_fixed_point(
        value.get("attacker_prestige_delta"),
        f"{name}.attacker_prestige_delta",
    )
    expected_delta = max(
        -10 * factor["raw"], -1000 * CK3_FIXED_POINT_SCALE
    )
    if (
        factor["raw"] < 0
        or delta["character_id"] != current["character_id"]
        or delta["value"]["raw"] != expected_delta
    ):
        raise ValueError(f"native {name} factor/delta formula is malformed")
    return {
        **{
            field: _TERMINATION_TERMS_RAIKTOR_ATTACKER_FAME[field]
            for field in ("resource", "base", "scale", "limit_rule")
        },
        "actual_delta_observable": True,
        "attacker_current_prestige": current,
        "cb_prestige_factor": factor,
        "attacker_prestige_delta": delta,
    }


def _normalize_raiktor_prisoner_release(value: object) -> dict[str, object]:
    name = "war_termination_terms.prisoner_release"
    if not isinstance(value, dict) or set(value) != set(
        _TERMINATION_TERMS_RAIKTOR_PRISONER_RELEASE
    ):
        raise ValueError(f"native {name} schema is malformed")
    if value.get("rule") != _TERMINATION_TERMS_RAIKTOR_PRISONER_RELEASE["rule"]:
        raise ValueError(f"native {name}.rule drifted")
    observable = _strict_bool(
        value.get("actual_pairs_observable"),
        f"{name}.actual_pairs_observable",
    )
    dynamic_fields = (
        "attacker_participant_ids",
        "defender_participant_ids",
        "attacker_release_candidate_ids",
        "defender_release_candidate_ids",
        "release_pairs",
        "full_participant_scan",
        "primary_and_first_three_successors_scanned",
    )
    if not observable:
        if any(value.get(field) is not None for field in dynamic_fields):
            raise ValueError(f"native {name} unavailable values are malformed")
        return dict(_TERMINATION_TERMS_RAIKTOR_PRISONER_RELEASE)

    attacker_participants = _strict_positive_int32_id_list(
        value.get("attacker_participant_ids"),
        f"{name}.attacker_participant_ids",
    )
    defender_participants = _strict_positive_int32_id_list(
        value.get("defender_participant_ids"),
        f"{name}.defender_participant_ids",
    )
    attacker_candidates = _strict_positive_int32_id_list(
        value.get("attacker_release_candidate_ids"),
        f"{name}.attacker_release_candidate_ids",
    )
    defender_candidates = _strict_positive_int32_id_list(
        value.get("defender_release_candidate_ids"),
        f"{name}.defender_release_candidate_ids",
    )
    if (
        not attacker_participants
        or not defender_participants
        or not attacker_candidates
        or not defender_candidates
        or set(attacker_participants) & set(defender_participants)
        or set(attacker_candidates) & set(defender_candidates)
        or _strict_bool(
            value.get("full_participant_scan"),
            f"{name}.full_participant_scan",
        )
        is not True
        or _strict_bool(
            value.get("primary_and_first_three_successors_scanned"),
            f"{name}.primary_and_first_three_successors_scanned",
        )
        is not True
    ):
        raise ValueError(f"native {name} complete-scan identity is malformed")
    raw_pairs = value.get("release_pairs")
    if not isinstance(raw_pairs, list):
        raise ValueError(f"native {name}.release_pairs must be an array")
    pairs: list[dict[str, object]] = []
    seen_pairs: set[tuple[int, int]] = set()
    for index, raw_pair in enumerate(raw_pairs):
        pair_name = f"{name}.release_pairs[{index}]"
        if not isinstance(raw_pair, dict) or set(raw_pair) != {
            "jailer_character_id",
            "prisoner_character_id",
            "reason",
        }:
            raise ValueError(f"native {pair_name} schema is malformed")
        jailer = _positive_int32_id(
            raw_pair.get("jailer_character_id"),
            f"{pair_name}.jailer_character_id",
        )
        prisoner = _positive_int32_id(
            raw_pair.get("prisoner_character_id"),
            f"{pair_name}.prisoner_character_id",
        )
        if (
            raw_pair.get("reason")
            != "opposite_primary_or_first_three_successors"
            or (jailer, prisoner) in seen_pairs
            or not (
                (
                    jailer in defender_participants
                    and prisoner in attacker_candidates
                )
                or (
                    jailer in attacker_participants
                    and prisoner in defender_candidates
                )
            )
        ):
            raise ValueError(f"native {pair_name} direction/reason is malformed")
        seen_pairs.add((jailer, prisoner))
        pairs.append(
            {
                "jailer_character_id": jailer,
                "prisoner_character_id": prisoner,
                "reason": "opposite_primary_or_first_three_successors",
            }
        )
    return {
        "rule": _TERMINATION_TERMS_RAIKTOR_PRISONER_RELEASE["rule"],
        "actual_pairs_observable": True,
        "attacker_participant_ids": attacker_participants,
        "defender_participant_ids": defender_participants,
        "attacker_release_candidate_ids": attacker_candidates,
        "defender_release_candidate_ids": defender_candidates,
        "release_pairs": pairs,
        "full_participant_scan": True,
        "primary_and_first_three_successors_scanned": True,
    }


def _normalize_raiktor_favor_hook(value: object) -> dict[str, object]:
    name = "war_termination_terms.conditional_favor_hook"
    if not isinstance(value, dict) or set(value) != set(
        _TERMINATION_TERMS_RAIKTOR_CONDITIONAL_FAVOR_HOOK
    ):
        raise ValueError(f"native {name} schema is malformed")
    if value.get("rule") != (
        _TERMINATION_TERMS_RAIKTOR_CONDITIONAL_FAVOR_HOOK["rule"]
    ):
        raise ValueError(f"native {name}.rule drifted")
    observable = _strict_bool(
        value.get("actual_applies_observable"),
        f"{name}.actual_applies_observable",
    )
    dynamic_fields = (
        "claimant_distinct_from_attacker",
        "original_visible_root_traversed",
        "will_apply",
    )
    if not observable:
        if any(value.get(field) is not None for field in dynamic_fields):
            raise ValueError(f"native {name} unavailable values are malformed")
        return dict(_TERMINATION_TERMS_RAIKTOR_CONDITIONAL_FAVOR_HOOK)
    distinct = _strict_bool(
        value.get("claimant_distinct_from_attacker"),
        f"{name}.claimant_distinct_from_attacker",
    )
    traversed = _strict_bool(
        value.get("original_visible_root_traversed"),
        f"{name}.original_visible_root_traversed",
    )
    will_apply = _strict_bool(value.get("will_apply"), f"{name}.will_apply")
    if (not distinct and (traversed or will_apply)) or (
        distinct and not traversed
    ):
        raise ValueError(f"native {name} authored outer gate is malformed")
    return {
        "rule": _TERMINATION_TERMS_RAIKTOR_CONDITIONAL_FAVOR_HOOK["rule"],
        "actual_applies_observable": True,
        "claimant_distinct_from_attacker": distinct,
        "original_visible_root_traversed": traversed,
        "will_apply": will_apply,
    }


def _normalize_raiktor_truce(value: object) -> dict[str, object]:
    name = "war_termination_terms.truce"
    if not isinstance(value, dict) or set(value) != set(
        _TERMINATION_TERMS_RAIKTOR_TRUCE
    ):
        raise ValueError(f"native {name} schema is malformed")
    if (
        value.get("direction")
        != _TERMINATION_TERMS_RAIKTOR_TRUCE["direction"]
        or value.get("result") != _TERMINATION_TERMS_RAIKTOR_TRUCE["result"]
    ):
        raise ValueError(f"native {name} authored rule drifted")
    evaluated_observable = _strict_bool(
        value.get("evaluated_days_observable"),
        f"{name}.evaluated_days_observable",
    )
    evaluated_days = _optional_non_negative_int32(
        value.get("evaluated_days"), f"{name}.evaluated_days"
    )
    if evaluated_observable != (evaluated_days is not None):
        raise ValueError(f"native {name} evaluated duration gate is malformed")
    if _strict_bool(
        value.get("actual_expiry_observable"),
        f"{name}.actual_expiry_observable",
    ):
        raise ValueError(f"native {name} persisted expiry is unavailable")
    if value.get("expiry_date_raw") is not None:
        raise ValueError(f"native {name} invented persisted expiry")
    return {
        "direction": _TERMINATION_TERMS_RAIKTOR_TRUCE["direction"],
        "result": _TERMINATION_TERMS_RAIKTOR_TRUCE["result"],
        "evaluated_days_observable": evaluated_observable,
        "evaluated_days": evaluated_days,
        "actual_expiry_observable": False,
        "expiry_date_raw": None,
    }


def _normalize_raiktor_generic_war_bound_current(
    value: object,
    *,
    expected_war_id: int,
    expected_casus_belli_database_index: int,
) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(
            "native war_termination_terms.generic_war_bound_current "
            "must be an object or null"
        )
    active = value.get("active_frame")
    if not isinstance(active, dict):
        raise ValueError(
            "native generic war-bound active frame is malformed"
        )
    if (
        active.get("active_casus_belli_database_index")
        != expected_casus_belli_database_index
    ):
        raise ValueError("native generic war-bound CB identity drifted")
    try:
        return normalize_raiktor_war_bound_regiment(
            value,
            expected_war_id=expected_war_id,
            expected_attacker_character_id=active.get(
                "primary_attacker_character_id"
            ),
            expected_defender_character_id=active.get(
                "primary_defender_character_id"
            ),
            expected_snapshot_revision=active.get("snapshot_revision"),
            expected_native_revision=active.get("native_revision"),
            expected_date_raw=active.get("date_raw"),
        )
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(
            "native generic war-bound payload is malformed"
        ) from error


def normalize_war_termination_terms(
    value: object,
    *,
    expected_war_id: int | None = None,
) -> dict[str, object]:
    """Normalize one strict claim or Raiktor narrow terms union."""
    if not isinstance(value, dict):
        raise ValueError("native war_termination_terms must be an object")
    status = value.get("status")
    common_keys = {
        "schema_version",
        "status",
        "war_id",
        "casus_belli",
        "supported_slice",
        "readiness",
        "provenance",
    }
    optional_keys: set[str] = set()
    supported_slice = value.get("supported_slice")
    if status == "available" and supported_slice == (
        _TERMINATION_TERMS_CLAIM_SLICE
    ):
        expected_keys = common_keys | {
            "claimant_character_id",
            "target_title_ids",
            "claims",
            "outcomes",
        }
    elif status == "available" and supported_slice == (
        _TERMINATION_TERMS_RAIKTOR_SLICE
    ):
        expected_keys = common_keys | {
            "claimant_character_id",
            "target_title_ids",
            "claims",
            "attacker_defeat",
            "gold_reparations",
            "attacker_fame",
            "truce",
            "prisoner_release",
            "conditional_favor_hook",
            "attacker_legitimacy_delta",
            "attacker_influence_delta",
            "hostages_allowed",
            "unobserved_dynamic_effects",
        }
        optional_keys = {"generic_war_bound_current"}
    elif status == "unsupported":
        expected_keys = common_keys | {"reason"}
    else:
        raise ValueError("native war_termination_terms.status is malformed")
    if set(value) not in {
        frozenset(expected_keys),
        frozenset(expected_keys | optional_keys),
    } or value.get("schema_version") != 1:
        raise ValueError(
            "native war_termination_terms top-level schema is malformed"
        )

    war_id = _positive_int32_id(
        value.get("war_id"), "war_termination_terms.war_id"
    )
    if expected_war_id is not None and war_id != _positive_int32_id(
        expected_war_id, "expected_war_id"
    ):
        raise ValueError("native war_termination_terms WarID mismatch")
    casus_belli = value.get("casus_belli")
    if not isinstance(casus_belli, dict) or set(casus_belli) != {
        "database_index",
        "canonical_key",
    }:
        raise ValueError("native war_termination_terms.casus_belli malformed")
    database_index = _optional_non_negative_int32(
        casus_belli.get("database_index"),
        "war_termination_terms.casus_belli.database_index",
    )
    if database_index is None:
        raise ValueError(
            "native war_termination_terms CB database index is required"
        )
    canonical_key = casus_belli.get("canonical_key")
    if not isinstance(canonical_key, str) or not canonical_key:
        raise ValueError(
            "native war_termination_terms CB canonical key is malformed"
        )
    if supported_slice not in {
        _TERMINATION_TERMS_CLAIM_SLICE,
        _TERMINATION_TERMS_RAIKTOR_SLICE,
    }:
        raise ValueError(
            "native war_termination_terms supported slice drifted"
        )
    provenance = _normalize_war_termination_terms_provenance(
        value.get("provenance"),
        supported_slice=(
            _TERMINATION_TERMS_CLAIM_SLICE
            if status == "unsupported"
            else supported_slice
        ),
    )

    if status == "unsupported":
        if (
            supported_slice != _TERMINATION_TERMS_CLAIM_SLICE
            or canonical_key in {"claim_cb", "raiktor_claim_cb"}
            or value.get("reason") != "casus_belli_not_claim_cb"
        ):
            raise ValueError(
                "native war_termination_terms unsupported branch malformed"
            )
        readiness = value.get("readiness")
        if not isinstance(readiness, dict) or readiness != {"ready": False}:
            raise ValueError(
                "native war_termination_terms unsupported readiness malformed"
            )
        return {
            "schema_version": 1,
            "status": "unsupported",
            "war_id": war_id,
            "casus_belli": {
                "database_index": database_index,
                "canonical_key": canonical_key,
            },
            "supported_slice": _TERMINATION_TERMS_CLAIM_SLICE,
            "reason": "casus_belli_not_claim_cb",
            "readiness": {"ready": False},
            "provenance": provenance,
        }

    if supported_slice == _TERMINATION_TERMS_CLAIM_SLICE and (
        canonical_key != "claim_cb"
    ):
        raise ValueError(
            "native war_termination_terms available branch is not claim_cb"
        )
    if supported_slice == _TERMINATION_TERMS_RAIKTOR_SLICE and (
        canonical_key != "raiktor_claim_cb"
    ):
        raise ValueError(
            "native war_termination_terms available branch is not "
            "raiktor_claim_cb"
        )
    claimant_character_id = _positive_int32_id(
        value.get("claimant_character_id"),
        "war_termination_terms.claimant_character_id",
    )
    target_title_ids = _strict_positive_int32_id_list(
        value.get("target_title_ids"),
        "war_termination_terms.target_title_ids",
    )
    if not target_title_ids:
        raise ValueError(
            "native war_termination_terms target titles must be nonempty"
        )
    raw_claims = value.get("claims")
    if not isinstance(raw_claims, list) or len(raw_claims) != len(
        target_title_ids
    ):
        raise ValueError(
            "native war_termination_terms claims must match target titles"
        )
    claims: list[dict[str, object]] = []
    for index, (raw_claim, title_id) in enumerate(
        zip(raw_claims, target_title_ids, strict=True)
    ):
        name = f"war_termination_terms.claims[{index}]"
        if not isinstance(raw_claim, dict):
            raise ValueError(f"native {name} must be an object")
        present = _strict_bool(raw_claim.get("present"), f"{name}.present")
        expected_claim_keys = (
            {"title_id", "present", "strong", "implicit", "state"}
            if present
            else {"title_id", "present", "state"}
        )
        if set(raw_claim) != expected_claim_keys or _positive_int32_id(
            raw_claim.get("title_id"), f"{name}.title_id"
        ) != title_id:
            raise ValueError(f"native {name} schema/title order is malformed")
        if not present:
            if raw_claim.get("state") != "absent":
                raise ValueError(f"native {name} absent state is malformed")
            claims.append(
                {"title_id": title_id, "present": False, "state": "absent"}
            )
            continue
        strong = _strict_bool(raw_claim.get("strong"), f"{name}.strong")
        implicit = _strict_bool(
            raw_claim.get("implicit"), f"{name}.implicit"
        )
        expected_state = (
            ("strong_" if strong else "weak_")
            + ("implicit" if implicit else "explicit")
        )
        if raw_claim.get("state") != expected_state:
            raise ValueError(f"native {name} claim state is inconsistent")
        claims.append(
            {
                "title_id": title_id,
                "present": True,
                "strong": strong,
                "implicit": implicit,
                "state": expected_state,
            }
        )

    if supported_slice == _TERMINATION_TERMS_RAIKTOR_SLICE:
        gold_reparations = _normalize_raiktor_gold_reparations(
            value.get("gold_reparations")
        )
        attacker_fame = _normalize_raiktor_attacker_fame(
            value.get("attacker_fame")
        )
        prisoner_release = _normalize_raiktor_prisoner_release(
            value.get("prisoner_release")
        )
        conditional_favor_hook = _normalize_raiktor_favor_hook(
            value.get("conditional_favor_hook")
        )
        truce = _normalize_raiktor_truce(value.get("truce"))
        generic_war_bound_current = (
            _normalize_raiktor_generic_war_bound_current(
                value.get("generic_war_bound_current"),
                expected_war_id=war_id,
                expected_casus_belli_database_index=database_index,
            )
        )
        gold_ready = bool(gold_reparations["actual_amount_observable"])
        prestige_ready = bool(attacker_fame["actual_delta_observable"])
        prisoner_ready = bool(prisoner_release["actual_pairs_observable"])
        favor_ready = bool(
            conditional_favor_hook["actual_applies_observable"]
        )
        truce_ready = bool(truce["evaluated_days_observable"])
        generic_war_bound_current_ready = (
            generic_war_bound_current is not None
        )
        observed_any = (
            gold_ready
            or prestige_ready
            or prisoner_ready
            or favor_ready
            or truce_ready
            or generic_war_bound_current_ready
        )
        expected_readiness = {
            "identity_ready": True,
            "targets_ready": True,
            "claim_rows_ready": True,
            "attacker_defeat_rule_ready": True,
            "static_formula_ready": True,
            "finance_ready": gold_ready,
            "gold_ready": gold_ready,
            "fame_factor_ready": prestige_ready,
            "attacker_prestige_delta_ready": prestige_ready,
            "truce_ready": truce_ready,
            "prisoner_release_ready": prisoner_ready,
            "favor_hook_ready": favor_ready,
            "war_bound_armies_ready": False,
            "same_frame_stable": observed_any,
            "dynamic_deltas_ready": False,
            "decision_ready": False,
            "automatic_surrender_ready": False,
            "ready": False,
        }
        observed_effects = {
            "actual_gold_transfer": gold_ready,
            "actual_prestige_delta": prestige_ready,
            "actual_prisoner_release_pairs": prisoner_ready,
            "conditional_favor_hook_application": favor_ready,
        }
        expected_unobserved = [
            effect
            for effect in _TERMINATION_TERMS_RAIKTOR_UNOBSERVED_DYNAMIC_EFFECTS
            if not observed_effects.get(effect, False)
        ]
        exact_fields: tuple[tuple[str, object], ...] = (
            (
                "attacker_defeat",
                _TERMINATION_TERMS_RAIKTOR_ATTACKER_DEFEAT,
            ),
            ("truce", truce),
            (
                "attacker_legitimacy_delta",
                {"raw": 0, "scale": 100_000},
            ),
            (
                "attacker_influence_delta",
                {"raw": 0, "scale": 100_000},
            ),
            (
                "unobserved_dynamic_effects",
                expected_unobserved,
            ),
            ("readiness", expected_readiness),
        )
        for field, expected in exact_fields:
            if value.get(field) != expected:
                raise ValueError(
                    "native raiktor war_termination_terms "
                    f"{field} drifted"
                )
        if value.get("hostages_allowed") is not False:
            raise ValueError(
                "native raiktor war_termination_terms hostages drifted"
            )
        attacker_character_id: int | None = None
        defender_character_id: int | None = None
        if gold_ready:
            attacker_character_id = int(
                gold_reparations["attacker_current_gold"]["character_id"]
            )
            defender_character_id = int(
                gold_reparations["defender_current_gold"]["character_id"]
            )
        if prestige_ready:
            prestige_attacker_id = int(
                attacker_fame["attacker_current_prestige"]["character_id"]
            )
            if (
                attacker_character_id is not None
                and prestige_attacker_id != attacker_character_id
            ):
                raise ValueError(
                    "native raiktor war_termination_terms attacker identity "
                    "drifted across resource domains"
                )
            attacker_character_id = prestige_attacker_id
        if prisoner_ready:
            attacker_participants = set(
                prisoner_release["attacker_participant_ids"]
            )
            defender_participants = set(
                prisoner_release["defender_participant_ids"]
            )
            prisoner_attacker_id = int(
                prisoner_release["attacker_release_candidate_ids"][0]
            )
            prisoner_defender_id = int(
                prisoner_release["defender_release_candidate_ids"][0]
            )
            if (
                prisoner_attacker_id not in attacker_participants
                or prisoner_defender_id not in defender_participants
                or (
                    attacker_character_id is not None
                    and attacker_character_id != prisoner_attacker_id
                )
                or (
                    defender_character_id is not None
                    and defender_character_id != prisoner_defender_id
                )
            ):
                raise ValueError(
                    "native raiktor war_termination_terms participant "
                    "identity drifted across domains"
                )
            attacker_character_id = prisoner_attacker_id
            defender_character_id = prisoner_defender_id
        if favor_ready and attacker_character_id is not None:
            expected_distinct = claimant_character_id != attacker_character_id
            if conditional_favor_hook[
                "claimant_distinct_from_attacker"
            ] is not expected_distinct:
                raise ValueError(
                    "native raiktor war_termination_terms favor claimant "
                    "identity drifted"
                )
        if generic_war_bound_current is not None:
            active_war_bound = generic_war_bound_current["active_frame"]
            war_bound_attacker_id = int(
                active_war_bound["primary_attacker_character_id"]
            )
            war_bound_defender_id = int(
                active_war_bound["primary_defender_character_id"]
            )
            if (
                attacker_character_id is not None
                and attacker_character_id != war_bound_attacker_id
            ) or (
                defender_character_id is not None
                and defender_character_id != war_bound_defender_id
            ):
                raise ValueError(
                    "native raiktor war_termination_terms war-bound "
                    "identity drifted across domains"
                )
        return {
            "schema_version": 1,
            "status": "available",
            "war_id": war_id,
            "casus_belli": {
                "database_index": database_index,
                "canonical_key": "raiktor_claim_cb",
            },
            "supported_slice": _TERMINATION_TERMS_RAIKTOR_SLICE,
            "claimant_character_id": claimant_character_id,
            "target_title_ids": target_title_ids,
            "claims": claims,
            "attacker_defeat": dict(
                _TERMINATION_TERMS_RAIKTOR_ATTACKER_DEFEAT
            ),
            "gold_reparations": gold_reparations,
            "attacker_fame": attacker_fame,
            "truce": truce,
            "prisoner_release": prisoner_release,
            "conditional_favor_hook": conditional_favor_hook,
            "generic_war_bound_current": generic_war_bound_current,
            "attacker_legitimacy_delta": {
                "raw": 0,
                "scale": CK3_FIXED_POINT_SCALE,
            },
            "attacker_influence_delta": {
                "raw": 0,
                "scale": CK3_FIXED_POINT_SCALE,
            },
            "hostages_allowed": False,
            "unobserved_dynamic_effects": expected_unobserved,
            "readiness": expected_readiness,
            "provenance": provenance,
        }

    outcomes = value.get("outcomes")
    if not isinstance(outcomes, dict) or set(outcomes) != set(
        _TERMINATION_TERMS_OUTCOMES
    ):
        raise ValueError("native war_termination_terms outcomes malformed")
    normalized_outcomes: dict[str, dict[str, str]] = {}
    for outcome, expected_disposition in _TERMINATION_TERMS_OUTCOMES.items():
        disposition = outcomes.get(outcome)
        if not isinstance(disposition, dict) or disposition != (
            expected_disposition
        ):
            raise ValueError(
                f"native war_termination_terms outcome {outcome} drifted"
            )
        normalized_outcomes[outcome] = dict(expected_disposition)
    readiness = value.get("readiness")
    expected_readiness = {
        "identity_ready": True,
        "targets_ready": True,
        "claim_rows_ready": True,
        "claim_disposition_ready": True,
        "ready": True,
    }
    if not isinstance(readiness, dict) or readiness != expected_readiness:
        raise ValueError(
            "native war_termination_terms available readiness malformed"
        )
    return {
        "schema_version": 1,
        "status": "available",
        "war_id": war_id,
        "casus_belli": {
            "database_index": database_index,
            "canonical_key": "claim_cb",
        },
        "supported_slice": _TERMINATION_TERMS_CLAIM_SLICE,
        "claimant_character_id": claimant_character_id,
        "target_title_ids": target_title_ids,
        "claims": claims,
        "outcomes": normalized_outcomes,
        "readiness": expected_readiness,
        "provenance": provenance,
    }


def _normalize_war_termination_terms_provenance(
    value: object,
    *,
    supported_slice: str,
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError("native war_termination_terms provenance is malformed")
    try:
        build = require_exact_native_build(
            value.get("game_version"), value.get("executable_sha256"),
        )
    except ValueError as error:
        raise ValueError("native war_termination_terms provenance is malformed") from error
    common = {
        "game_version": build.game_version,
        "executable_sha256": build.executable_sha256,
        "native_reader": (
            "CWar+0x270/+0x290;0x2B9ECB0" if build == CK3_12004 else
            "CWar+0x270/+0x290;0x2B9ECD0"
            if build in (CK3_12002, CK3_12003) else _TERMINATION_TERMS_NATIVE_READER
        ),
        "present_claim_lifecycle": _TERMINATION_TERMS_CLAIM_LIFECYCLE,
    }
    if supported_slice == _TERMINATION_TERMS_CLAIM_SLICE:
        expected = {
            **common,
            "claim_script_sha256": (
                "887BF0197401CB17CB4588978ADD556AB6B429BF55CB482E3E5F2D0E8351CFD4"
                # .4 retains the authored script pin by equal frozen game-data
                # depot metadata; its native getter has a separate paired proof.
                if build in (CK3_12002, CK3_12003, CK3_12004) else _TERMINATION_TERMS_CLAIM_SCRIPT_SHA256
            ),
        }
    elif supported_slice == _TERMINATION_TERMS_RAIKTOR_SLICE:
        if build != CK3_11906:
            raise ValueError("native event-war terms are not closed for this build")
        expected = {
            **common,
            "event_war_script_sha256": (
                _TERMINATION_TERMS_RAIKTOR_EVENT_WAR_SCRIPT_SHA256
            ),
            "casus_belli_effects_script_sha256": (
                _TERMINATION_TERMS_CASUS_BELLI_EFFECTS_SCRIPT_SHA256
            ),
            "war_effects_script_sha256": (
                _TERMINATION_TERMS_WAR_EFFECTS_SCRIPT_SHA256
            ),
            "war_interactions_script_sha256": (
                _TERMINATION_TERMS_WAR_INTERACTIONS_SCRIPT_SHA256
            ),
            "bookmark_events_script_sha256": (
                _TERMINATION_TERMS_BOOKMARK_EVENTS_SCRIPT_SHA256
            ),
            "truce_observer": _TERMINATION_TERMS_RAIKTOR_TRUCE_OBSERVER,
        }
    else:
        raise ValueError(
            "native war_termination_terms provenance slice is malformed"
        )
    if not isinstance(value, dict) or value != expected:
        raise ValueError(
            "native war_termination_terms provenance is malformed"
        )
    return dict(expected)


def normalize_outbound_war_white_peace_status(
    value: object,
    *,
    expected_war_id: int | None = None,
) -> dict[str, object]:
    """Normalize one exact sender-side white-peace pending receipt."""
    if not isinstance(value, dict) or set(value) != {
        "schema_version",
        "war_id",
        "actor_character_id",
        "recipient_character_id",
        "state",
        "present",
        "pending_interaction_id",
    }:
        raise ValueError(
            "native outbound_war_white_peace_status schema is malformed"
        )
    if value.get("schema_version") != 1:
        raise ValueError(
            "native outbound_war_white_peace_status version is unsupported"
        )
    war_id = _positive_int32_id(value.get("war_id"), "war_id")
    if expected_war_id is not None and war_id != _positive_int32_id(
        expected_war_id, "expected_war_id"
    ):
        raise ValueError(
            "native outbound_war_white_peace_status WarID mismatch"
        )
    actor = _signed_int32(
        value.get("actor_character_id"), "actor_character_id"
    )
    recipient = _signed_int32(
        value.get("recipient_character_id"), "recipient_character_id"
    )
    if actor == -1 or recipient == -1 or actor == recipient:
        raise ValueError(
            "native outbound_war_white_peace_status roles are malformed"
        )
    present = _strict_bool(
        value.get("present"), "outbound_war_white_peace_status.present"
    )
    state = value.get("state")
    expected_state = "exact_present" if present else "exact_absent"
    if state != expected_state:
        raise ValueError(
            "native outbound_war_white_peace_status state is inconsistent"
        )
    pending_id = _signed_int32(
        value.get("pending_interaction_id"), "pending_interaction_id"
    )
    if (present and pending_id == -1) or (not present and pending_id != -1):
        raise ValueError(
            "native outbound_war_white_peace_status pending ID is "
            "inconsistent"
        )
    return {
        "schema_version": 1,
        "war_id": war_id,
        "actor_character_id": actor,
        "recipient_character_id": recipient,
        "state": expected_state,
        "present": present,
        "pending_interaction_id": pending_id,
    }


def normalize_war_termination_options(
    value: object,
    *,
    expected_war_id: int | None = None,
    source_build: NativeBuildIdentity | None = None,
) -> dict[str, object]:
    """Normalize one atomic native war-termination query.

    The exact-build reader publishes each context, native validator, opponent
    answer score, and auto-accept result atomically.  CB-specific terms remain
    explicit unavailable data and may not be inferred from those values.
    """
    if not isinstance(value, dict):
        raise ValueError("native war_termination_options must be an object")
    expected_keys = {
        "war_id",
        "player_side",
        "player_is_primary_war_leader",
        "player_relative_war_score",
        "war_duration_days",
        "absolute_war_scores_observable",
        "attacker_war_score",
        "defender_war_score",
        "war_score_breakdown",
        "active_casus_belli_present",
        "active_casus_belli_identity",
        "cb_allows_white_peace",
        "options",
    }
    allowed_keys = {
        frozenset(expected_keys),
        frozenset(expected_keys | {"source"}),
    }
    if frozenset(value) not in allowed_keys:
        raise ValueError(
            "native war_termination_options top-level schema is malformed"
        )
    if "source" in value and value.get("source") != "native":
        raise ValueError(
            "native war_termination_options.source is malformed"
        )
    war_id = _positive_int32_id(value.get("war_id"), "war_id")
    if expected_war_id is not None and war_id != _positive_int32_id(
        expected_war_id, "expected_war_id"
    ):
        raise ValueError("native war_termination_options WarID mismatch")
    player_side = value.get("player_side")
    if player_side not in {"attacker", "defender"}:
        raise ValueError(
            "native war_termination_options.player_side is malformed"
        )
    is_primary = _strict_bool(
        value.get("player_is_primary_war_leader"),
        "war_termination_options.player_is_primary_war_leader",
    )
    score = value.get("player_relative_war_score")
    if (
        isinstance(score, bool)
        or not isinstance(score, int)
        or score < -(2**31)
        or score > 2**31 - 1
    ):
        raise ValueError(
            "native war_termination_options.player_relative_war_score "
            "must be a signed int32"
        )
    war_duration_days = _optional_non_negative_int32(
        value.get("war_duration_days"),
        "war_termination_options.war_duration_days",
    )
    active_cb = _optional_strict_bool(
        value.get("active_casus_belli_present"),
        "war_termination_options.active_casus_belli_present",
    )
    white_peace_allowed = _optional_strict_bool(
        value.get("cb_allows_white_peace"),
        "war_termination_options.cb_allows_white_peace",
    )
    if white_peace_allowed is not None and active_cb is not True:
        raise ValueError(
            "native war_termination_options cannot publish white-peace "
            "permission without an active casus belli"
        )
    active_cb_identity = _normalize_active_casus_belli_identity(
        value.get("active_casus_belli_identity"),
        active_casus_belli_present=active_cb,
    )
    absolute_scores_observable = _strict_bool(
        value.get("absolute_war_scores_observable"),
        "war_termination_options.absolute_war_scores_observable",
    )
    attacker_score = _optional_signed_int32(
        value.get("attacker_war_score"),
        "war_termination_options.attacker_war_score",
    )
    defender_score = _optional_signed_int32(
        value.get("defender_war_score"),
        "war_termination_options.defender_war_score",
    )
    if absolute_scores_observable:
        if attacker_score is None or defender_score is None:
            raise ValueError(
                "native observable absolute war scores must both be present"
            )
        if defender_score != -attacker_score:
            raise ValueError(
                "native defender_war_score must negate attacker_war_score"
            )
        expected_player_score = (
            attacker_score if player_side == "attacker" else defender_score
        )
        if score != expected_player_score:
            raise ValueError(
                "native absolute war scores disagree with player-relative score"
            )
    elif attacker_score is not None or defender_score is not None:
        raise ValueError(
            "native unobservable absolute war scores must both be null"
        )
    war_score_breakdown = _normalize_war_score_breakdown(
        value.get("war_score_breakdown")
    )
    raw_options = value.get("options")
    if not isinstance(raw_options, dict) or set(raw_options) != {
        "surrender",
        "white_peace",
        "victory",
    }:
        raise ValueError(
            "native war_termination_options.options must contain exactly "
            "surrender, white_peace, and victory"
        )
    surrender_outcome = (
        "attacker_defeat" if player_side == "attacker" else "attacker_victory"
    )
    victory_outcome = (
        "attacker_victory" if player_side == "attacker" else "attacker_defeat"
    )
    options = {
        "surrender": _normalize_war_termination_option(
            raw_options.get("surrender"),
            name="surrender",
            expected_outcome=surrender_outcome,
            legacy_recipient_unavailable=source_build in (CK3_12002, CK3_12003),
        ),
        "white_peace": _normalize_war_termination_option(
            raw_options.get("white_peace"),
            name="white_peace",
            expected_outcome="white_peace",
            legacy_recipient_unavailable=source_build in (CK3_12002, CK3_12003),
        ),
        "victory": _normalize_war_termination_option(
            raw_options.get("victory"),
            name="victory",
            expected_outcome=victory_outcome,
            legacy_recipient_unavailable=source_build in (CK3_12002, CK3_12003),
        ),
    }
    if not is_primary and any(
        option["context_constructed"] for option in options.values()
    ):
        raise ValueError(
            "native war_termination_options constructed a context for a "
            "non-primary participant"
        )
    if (
        white_peace_allowed is not True
        and options["white_peace"]["context_constructed"]
    ):
        raise ValueError(
            "native war_termination_options constructed white peace for a "
            "casus belli that forbids it"
        )
    return {
        "war_id": war_id,
        "player_side": player_side,
        "player_is_primary_war_leader": is_primary,
        "player_relative_war_score": score,
        "war_duration_days": war_duration_days,
        "active_casus_belli_present": active_cb,
        "active_casus_belli_identity": active_cb_identity,
        "cb_allows_white_peace": white_peace_allowed,
        "absolute_war_scores_observable": absolute_scores_observable,
        "attacker_war_score": attacker_score,
        "defender_war_score": defender_score,
        "war_score_breakdown": war_score_breakdown,
        "options": options,
        "source": "native",
    }


def _normalize_active_casus_belli_identity(
    value: object,
    *,
    active_casus_belli_present: bool | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    if active_casus_belli_present is not True or not isinstance(value, dict) or set(
        value
    ) != {"database_index", "canonical_key"}:
        raise ValueError(
            "native active_casus_belli_identity is malformed"
        )
    database_index = _optional_non_negative_int32(
        value.get("database_index"),
        "war_termination_options.active_casus_belli_identity.database_index",
    )
    canonical_key = value.get("canonical_key")
    if database_index is None or not isinstance(canonical_key, str) or not (
        canonical_key
    ):
        raise ValueError(
            "native active_casus_belli_identity is incomplete"
        )
    return {
        "database_index": database_index,
        "canonical_key": canonical_key,
    }


def _normalize_war_score_breakdown(
    value: object,
) -> dict[str, int] | None:
    if value is None:
        return None
    fields = {"imprisonment", "battles", "occupation", "ticking"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError(
            "native war_score_breakdown must be null or contain all four fields"
        )
    return {
        field: _signed_int32(
            value.get(field),
            f"war_termination_options.war_score_breakdown.{field}",
        )
        for field in sorted(fields)
    }


def _normalize_war_termination_option(
    value: object,
    *,
    name: str,
    expected_outcome: str,
    legacy_recipient_unavailable: bool = False,
) -> dict[str, object]:
    if (
        legacy_recipient_unavailable and isinstance(value, dict)
        and "recipient_response" not in value
    ):
        value = {
            **value,
            "recipient_response": {
                "status": "unavailable", "decision_status_raw": None,
                "would_accept_now": None,
            },
        }
    if not isinstance(value, dict) or set(value) != {
        "outcome",
        "hostage_variant",
        "context_constructed",
        "native_validator_passed",
        "available",
        "terms_observable",
        "terms",
        "ai_acceptance_observable",
        "ai_acceptance",
        "auto_accept_observable",
        "auto_accept",
        "recipient_response",
    }:
        raise ValueError(
            f"native war_termination_options.options.{name} is malformed"
        )
    if value.get("outcome") != expected_outcome:
        raise ValueError(
            f"native war_termination_options.options.{name}.outcome is "
            "inconsistent with player_side"
        )
    if value.get("hostage_variant") != "none":
        raise ValueError(
            "native war_termination_options only supports the no-hostage "
            f"variant for {name}"
        )
    context_constructed = _strict_bool(
        value.get("context_constructed"),
        f"war_termination_options.options.{name}.context_constructed",
    )
    validator = value.get("native_validator_passed")
    if validator is not None and not isinstance(validator, bool):
        raise ValueError(
            "native war_termination_options.options."
            f"{name}.native_validator_passed must be boolean or null"
        )
    if not context_constructed and validator is not None:
        raise ValueError(
            "native war_termination_options.options."
            f"{name} cannot publish a validator result without a context"
        )
    available = _strict_bool(
        value.get("available"),
        f"war_termination_options.options.{name}.available",
    )
    if available is not (context_constructed and validator is True):
        raise ValueError(
            "native war_termination_options.options."
            f"{name}.available is inconsistent with context and validator"
        )
    terms_observable = _strict_bool(
        value.get("terms_observable"),
        f"war_termination_options.options.{name}.terms_observable",
    )
    terms = value.get("terms")
    if terms_observable or terms != {
        "status": "unavailable",
        "reason": "cb_specific_terms_not_observable",
    }:
        raise ValueError(
            "native war_termination_options option terms must remain "
            "explicitly unavailable"
        )
    acceptance_observable = _strict_bool(
        value.get("ai_acceptance_observable"),
        f"war_termination_options.options.{name}.ai_acceptance_observable",
    )
    acceptance = (
        _signed_fixed_point(
            value.get("ai_acceptance"),
            f"war_termination_options.options.{name}.ai_acceptance",
        )
        if acceptance_observable
        else None
    )
    if not acceptance_observable and value.get("ai_acceptance") is not None:
        raise ValueError(
            "native war_termination_options cannot publish an unobservable "
            f"AI acceptance score for {name}"
        )
    auto_accept_observable = _strict_bool(
        value.get("auto_accept_observable"),
        f"war_termination_options.options.{name}.auto_accept_observable",
    )
    auto_accept = value.get("auto_accept")
    if auto_accept_observable:
        auto_accept = _strict_bool(
            auto_accept,
            f"war_termination_options.options.{name}.auto_accept",
        )
    elif auto_accept is not None:
        raise ValueError(
            "native war_termination_options cannot publish an unobservable "
            f"auto-accept result for {name}"
        )
    if not context_constructed and (
        acceptance_observable or auto_accept_observable
    ):
        raise ValueError(
            "native war_termination_options cannot evaluate acceptance "
            f"without a constructed {name} context"
        )
    recipient_response = _normalize_war_termination_recipient_response(
        value.get("recipient_response"),
        name=name,
        context_constructed=context_constructed,
        validator=validator,
    )
    return {
        "outcome": expected_outcome,
        "hostage_variant": "none",
        "context_constructed": context_constructed,
        # Null is an observed unknown and must never be coerced to false.
        "native_validator_passed": validator,
        "available": available,
        "terms_observable": False,
        "terms": terms,
        "ai_acceptance_observable": acceptance_observable,
        "ai_acceptance": acceptance,
        "auto_accept_observable": auto_accept_observable,
        "auto_accept": auto_accept,
        "recipient_response": recipient_response,
    }


def _normalize_war_termination_recipient_response(
    value: object,
    *,
    name: str,
    context_constructed: bool,
    validator: bool | None,
) -> dict[str, object]:
    path = f"war_termination_options.options.{name}.recipient_response"
    if not isinstance(value, dict) or set(value) != {
        "status",
        "decision_status_raw",
        "would_accept_now",
    }:
        raise ValueError(f"native {path} is malformed")
    status = value.get("status")
    decision_status_raw = value.get("decision_status_raw")
    would_accept_now = value.get("would_accept_now")
    if status == "unavailable":
        if decision_status_raw is not None or would_accept_now is not None:
            raise ValueError(
                f"native {path} unavailable branch must contain null values"
            )
        return {
            "status": "unavailable",
            "decision_status_raw": None,
            "would_accept_now": None,
        }
    if status != "available":
        raise ValueError(f"native {path}.status is malformed")
    if not context_constructed or validator is not True:
        raise ValueError(
            f"native {path} cannot be available without a valid context"
        )
    if (
        isinstance(decision_status_raw, bool)
        or not isinstance(decision_status_raw, int)
        or decision_status_raw not in {0, 1, 2}
    ):
        raise ValueError(
            f"native {path}.decision_status_raw must be one of 0, 1, 2"
        )
    would_accept = _strict_bool(
        would_accept_now, f"{path}.would_accept_now"
    )
    if would_accept is not (decision_status_raw != 2):
        raise ValueError(
            f"native {path}.would_accept_now disagrees with final status"
        )
    return {
        "status": "available",
        "decision_status_raw": decision_status_raw,
        "would_accept_now": would_accept,
    }


def is_native_war_step(step: object) -> bool:
    return (
        step == RAISE_TROOPS_STEP
        or step == HIRE_MERCENARY_V1_STEP
        or step == HIRE_HOLY_ORDER_V1_STEP
        or step == QUERY_ARMY_STRENGTHS_STEP
        or parse_query_province_local_siege_step(step) is not None
        or parse_preview_move_army_step(step) is not None
        or parse_query_route_contact_horizon_step(step) is not None
        or parse_move_army_step(step) is not None
        or parse_halt_army_step(step) is not None
        or parse_disband_army_step(step) is not None
        or parse_split_army_half_step(step) is not None
        or parse_merge_armies_step(step) is not None
        or parse_start_assault_step(step) is not None
        or parse_stop_assault_step(step) is not None
        or parse_enforce_demands_step(step) is not None
        or parse_query_war_termination_options_step(step) is not None
        or parse_query_war_prisoner_release_pairs_v1_step(step) is not None
        or parse_query_outbound_war_white_peace_status_step(step) is not None
        or parse_query_war_termination_terms_step(step) is not None
        or parse_query_player_claims_v1_step(step) is not None
        or parse_query_title_holder_v1_step(step) is not None
        or parse_surrender_war_step(step) is not None
        or parse_offer_white_peace_step(step) is not None
    )


def _non_negative_id(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _positive_int32_id(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _optional_positive_int32_id(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _positive_int32_id(value, name)


def _optional_non_negative_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 0
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a non-negative int32 or null")
    return value


def _signed_int32(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < -(2**31)
        or value > 2**31 - 1
    ):
        raise ValueError(f"{name} must be a signed int32")
    return value


def _optional_signed_int32(value: object, name: str) -> int | None:
    if value is None:
        return None
    return _signed_int32(value, name)


def _signed_fixed_point(value: object, name: str) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"native {name} must contain raw and scale")
    raw = value.get("raw")
    scale = value.get("scale")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or raw < -(2**63)
        or raw > 2**63 - 1
        or scale != CK3_FIXED_POINT_SCALE
    ):
        raise ValueError(f"native {name} fixed value is malformed")
    return {"raw": raw, "scale": CK3_FIXED_POINT_SCALE}


def _strict_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{name} must be boolean")
    return value


def _required_list(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    return value


def _optional_strict_bool(value: object, name: str) -> bool | None:
    if value is None:
        return None
    return _strict_bool(value, name)


def _non_negative_id_list(value: object, name: str) -> list[int]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[int] = []
    seen: set[int] = set()
    for item in value:
        normalized = _non_negative_id(item, name)
        if normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _strict_positive_int32_id_list(value: object, name: str) -> list[int]:
    if not isinstance(value, list):
        raise ValueError(f"native {name} must be an array")
    result: list[int] = []
    seen: set[int] = set()
    for index, item in enumerate(value):
        normalized = _positive_int32_id(item, f"{name}[{index}]")
        if normalized in seen:
            raise ValueError(f"native {name} must not contain duplicates")
        seen.add(normalized)
        result.append(normalized)
    return result

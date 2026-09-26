from __future__ import annotations

import copy
import json
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from xar_autoplayer.bridge.driver import (
    BridgeUnavailableError,
    BridgeGameplayStepExecutor,
    CallbackGameplayDriver,
    DevelopmentReportDriver,
    HybridGameplayDriver,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
    UnsupportedStepError,
)
from xar_autoplayer.bridge.service import (
    GameplayBridgeService,
    _route_plan_to_available_step,
)
from xar_autoplayer.bridge.battle_terminal_transition_contract import (
    QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY,
    query_battle_terminal_transition_v1_step,
)
from xar_autoplayer.bridge.combat_phase_contract import (
    QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY,
    query_combat_simulation_inputs_v3_step,
)
from xar_autoplayer.bridge.settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
)
from xar_autoplayer.bridge.war_contract import (
    BATTLE_DECISION_EPOCH_ADVANCE_STEP,
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
    QUERY_ARMY_STRENGTHS_STEP,
    WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
    advance_route_contact_horizon_step,
    battle_decision_epoch_advance_step,
    committed_route_sentinel_advance_step,
    parse_committed_route_sentinel_advance_step,
    war_objective_hold_sentinel_advance_step,
    normalize_active_wars,
    query_route_contact_horizon_step,
    query_war_termination_options_step,
    war_objective_province_ids,
    war_termination_active_war_signature,
    war_termination_negative_query_signature,
)
from xar_autoplayer.strategy import (
    _accepted_native_move_arrival,
    _audit_war_route,
    _battle_control_turn_state,
    _enemy_endpoint_epochs,
    _latest_accepted_native_move_row,
    _moving_route_contact_horizon_conjunction,
    _negative_war_termination_reuse,
    _primary_defender_siege_relief_assessment,
    _primary_defender_siege_forecast_ingress,
    _preoffensive_army_consolidation,
    _outnumbered_attacker_regroup_input_ready,
    _outnumbered_primary_defender_regroup_input_ready,
    _recent_war_tactics,
    choose_one_life_turn,
    record_one_life_episode,
)


def _snapshot(revision: int = 0, history: list[dict[str, object]] | None = None):
    return {
        "format_version": 1,
        "snapshot_id": f"session:{revision}",
        "revision": revision,
        "source": "fixture",
        "history": history or [],
        "phase": "map_hud",
    }


def _pending_context_result(
    *,
    pending_id: int,
    revision: int,
    native_revision: int,
    date_raw: int,
    definition_key: str = "spar_with_knight_interaction",
    actor_character_id: int = 501,
    recipient_character_id: int = 707,
    legality: dict[str, dict[str, object]] | None = None,
    special_data_present: bool = False,
    special_war_binding: dict[str, object] | None = None,
) -> dict[str, object]:
    if legality is None:
        legality = {
            "accept": {"status": "available", "allowed": True, "reason": None},
            "reject": {"status": "available", "allowed": True, "reason": None},
            "block": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "ordinary_interaction_not_notification",
            },
        }
    if special_war_binding is None:
        special_war_binding = {
            "status": "unavailable",
            "value": None,
            "reason": "special_war_binding_not_applicable",
        }
    return {
        "step": "query-pending-character-interaction-context-v1",
        "accepted": True,
        "status": "available",
        "snapshot_revision": native_revision,
        "queried_snapshot_id": f"session:{revision}",
        "queried_revision": revision,
        "queried_native_revision": native_revision,
        "pending_character_interaction_context": {
            "status": "available",
            "reason": None,
            "snapshot_revision": native_revision,
            "date_raw": date_raw,
            "pending_interaction_id": pending_id,
            "definition": {
                "canonical_key": definition_key,
                "deterministic_key_hash": 12345,
                "runtime_ordinal": 17,
            },
            "roles": {
                "actor_character_id": actor_character_id,
                "recipient_character_id": recipient_character_id,
                "secondary_actor_character_id": -1,
                "secondary_recipient_character_id": -1,
                "intermediary_character_id": -1,
            },
            "routing": {
                "kind": 0,
                "played_character_id": recipient_character_id,
                "current_responder_role": "recipient",
                "reply_execution_channel": "recipient",
                "local_route": True,
                "auto_accept_notification": False,
            },
            "deadline": {
                "age_days": 2,
                "expiration_days": 60,
                "remaining_days": 58,
                "expiry_boundary_status": "not_reached",
            },
            "legality": legality,
            "terms": {
                "special_data_present": special_data_present,
                "special_war_binding": special_war_binding,
                "structured_exchanges": {
                    "status": "unavailable",
                    "value": None,
                    "reason": "structured_exchanges_unavailable",
                },
                "structured_effect_preview": {
                    "status": "unavailable",
                    "value": None,
                    "reason": "structured_effect_preview_unavailable",
                },
                "recipient_ai_acceptance_score": {
                    "status": "unavailable",
                    "value": None,
                    "reason": "human_responder_not_applicable",
                },
                "recipient_ai_final_decision": {
                    "status": "unavailable",
                    "value": None,
                    "reason": "human_responder_not_applicable",
                },
            },
            "readiness": {
                "generic_costs_ready": True,
                "interaction_semantic_decision_ready": False,
                "not_ready_reasons": [
                    "structured_exchanges_unavailable",
                    "structured_effect_preview_unavailable",
                ],
            },
        },
    }


def _arrange_marriage_context_result(
    *,
    legality: dict[str, dict[str, object]] | None = None,
    secondary_actor_character_id: int = 38_993,
    secondary_recipient_character_id: int = 38_293,
    intermediary_character_id: int = -1,
    selected_option_index: int | None = None,
    age_days: object = 0,
    expiration_days: object = 60,
    remaining_days: object = 60,
    expiry_boundary_status: object = "not_reached",
) -> dict[str, object]:
    if legality is None:
        legality = {
            action: {"status": "available", "allowed": True, "reason": None}
            for action in ("accept", "reject", "block")
        }
        legality["acknowledge"] = {
            "status": "available",
            "allowed": False,
            "reason": "normal_reply_channel",
        }
    result = _pending_context_result(
        pending_id=-2_013_265_918,
        revision=7,
        native_revision=6,
        date_raw=53_211_504,
        definition_key="arrange_marriage_interaction",
        actor_character_id=30_287,
        recipient_character_id=29_829,
        legality=legality,
        special_data_present=True,
        special_war_binding={
            "status": "unavailable",
            "value": None,
            "reason": "special_interaction_subtype_opaque",
        },
    )
    context = result["pending_character_interaction_context"]
    assert isinstance(context, dict)
    roles = context["roles"]
    assert isinstance(roles, dict)
    roles.update(
        {
            "secondary_actor_character_id": secondary_actor_character_id,
            "secondary_recipient_character_id": (
                secondary_recipient_character_id
            ),
            "intermediary_character_id": intermediary_character_id,
        }
    )
    context["deadline"] = {
        "age_days": age_days,
        "expiration_days": expiration_days,
        "remaining_days": remaining_days,
        "expiry_boundary_status": expiry_boundary_status,
    }
    context["send_options"] = {
        "exclusive": False,
        "definition_count": 6,
        "context_count": 6,
        "rows": [
            {
                "native_index": index,
                "selected": index == selected_option_index,
                "is_shown": index == 1,
                "is_valid": index in {1, 2},
            }
            for index in range(6)
        ],
    }
    return result


def _grant_vassal_context_result(
    *, legality: dict[str, dict[str, object]] | None = None
) -> dict[str, object]:
    if legality is None:
        legality = {
            action: {"status": "available", "allowed": True, "reason": None}
            for action in ("accept", "reject", "block")
        }
        legality["acknowledge"] = {
            "status": "available",
            "allowed": False,
            "reason": "normal_reply_channel",
        }
    result = _pending_context_result(
        pending_id=1_744_830_474,
        revision=32,
        native_revision=31,
        date_raw=53_285_904,
        definition_key="grant_vassal_interaction",
        actor_character_id=32_718,
        recipient_character_id=31_853,
        legality=legality,
    )
    context = result["pending_character_interaction_context"]
    assert isinstance(context, dict)
    definition = context["definition"]
    assert isinstance(definition, dict)
    definition["deterministic_key_hash"] = 1_006_648_858
    definition["runtime_ordinal"] = 277
    roles = context["roles"]
    assert isinstance(roles, dict)
    roles["secondary_actor_character_id"] = 31_506
    context["deadline"] = {
        "age_days": 7,
        "expiration_days": 60,
        "remaining_days": 53,
        "expiry_boundary_status": "not_reached",
    }
    context["send_options"] = {
        "exclusive": True,
        "definition_count": 0,
        "context_count": 0,
        "rows": [],
    }
    return result


def _negotiate_alliance_context_result(
    *,
    legality: dict[str, dict[str, object]] | None = None,
    selected_option_index: int | None = None,
    intermediary_character_id: int = -1,
) -> dict[str, object]:
    if legality is None:
        legality = {
            action: {"status": "available", "allowed": True, "reason": None}
            for action in ("accept", "reject", "block")
        }
        legality["acknowledge"] = {
            "status": "available",
            "allowed": False,
            "reason": "normal_reply_channel",
        }
    result = _pending_context_result(
        pending_id=-234_881_021,
        revision=2_299,
        native_revision=2_298,
        date_raw=53_247_096,
        definition_key="negotiate_alliance_interaction",
        actor_character_id=34_867,
        recipient_character_id=29_829,
        legality=legality,
        special_data_present=False,
    )
    context = result["pending_character_interaction_context"]
    assert isinstance(context, dict)
    roles = context["roles"]
    assert isinstance(roles, dict)
    roles["intermediary_character_id"] = intermediary_character_id
    context["deadline"] = {
        "age_days": 0,
        "expiration_days": 60,
        "remaining_days": 60,
        "expiry_boundary_status": "not_reached",
    }
    context["send_options"] = {
        "exclusive": False,
        "definition_count": 2,
        "context_count": 2,
        "rows": [
            {
                "native_index": 0,
                "numeric_flag_identifier": 49,
                "selected": selected_option_index == 0,
                "is_shown": False,
                "is_valid": True,
            },
            {
                "native_index": 1,
                "numeric_flag_identifier": 7_218,
                "selected": selected_option_index == 1,
                "is_shown": False,
                "is_valid": False,
            },
        ],
    }
    return result


def _perk_alliance_context_result() -> dict[str, object]:
    """R0127 pending context, retaining the native IDs and option vector."""

    legality = {
        action: {"status": "available", "allowed": True, "reason": None}
        for action in ("accept", "reject", "block")
    }
    legality["acknowledge"] = {
        "status": "available",
        "allowed": False,
        "reason": "normal_reply_channel",
    }
    result = _pending_context_result(
        pending_id=-268_435_437,
        revision=159,
        native_revision=158,
        date_raw=53_388_120,
        definition_key="perk_alliance_interaction",
        actor_character_id=31_506,
        recipient_character_id=36_403,
        legality=legality,
    )
    context = result["pending_character_interaction_context"]
    assert isinstance(context, dict)
    definition = context["definition"]
    assert isinstance(definition, dict)
    definition["deterministic_key_hash"] = 328_040_944
    definition["runtime_ordinal"] = 4
    context["deadline"] = {
        "age_days": 3,
        "expiration_days": 60,
        "remaining_days": 57,
        "expiry_boundary_status": "not_reached",
    }
    context["send_options"] = {
        "exclusive": False,
        "definition_count": 2,
        "context_count": 2,
        "rows": [
            {"native_index": 0, "numeric_flag_identifier": 49,
             "selected": False, "is_shown": False, "is_valid": True},
            {"native_index": 1, "numeric_flag_identifier": 6_918,
             "selected": False, "is_shown": False, "is_valid": False},
        ],
    }
    return result


def _call_ally_context_result(
    *,
    legality: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    if legality is None:
        legality = {
            action: {"status": "available", "allowed": True, "reason": None}
            for action in ("accept", "reject", "block")
        }
        legality["acknowledge"] = {
            "status": "available",
            "allowed": False,
            "reason": "normal_reply_channel",
        }
    result = _pending_context_result(
        pending_id=-1_811_939_304,
        revision=327,
        native_revision=326,
        date_raw=53_223_096,
        definition_key="call_ally_interaction",
        actor_character_id=30_287,
        recipient_character_id=29_829,
        legality=legality,
        special_data_present=False,
    )
    context = result["pending_character_interaction_context"]
    assert isinstance(context, dict)
    definition = context["definition"]
    assert isinstance(definition, dict)
    definition["deterministic_key_hash"] = 936_306_703
    context["build"] = {
        "version": "1.19.0.6",
        "exe_sha256": (
            "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
        ),
    }
    context["provenance"] = {
        "backend_id": (
            "ck3-1.19.0.6-native-pending-character-interaction-context-v1"
        )
    }
    context["target"] = {
        "present": True,
        "raw_type_index": 16,
        "raw_16_bytes_hex": "10000000000000005200000400000000",
        "type_key_status": "available",
        "type_key": "war",
        "type_key_reason": None,
        "typed_identity_status": "available",
        "typed_identity": "war:67108946",
        "typed_identity_reason": None,
    }
    context["send_options"] = {
        "exclusive": True,
        "definition_count": 0,
        "context_count": 0,
        "rows": [],
    }
    context["deadline"] = {
        "age_days": 0,
        "expiration_days": 60,
        "remaining_days": 60,
        "expiry_boundary_status": "not_reached",
    }
    readiness = context["readiness"]
    assert isinstance(readiness, dict)
    readiness["target_typed_identity_ready"] = True
    return result


def _raiktor_inbound_white_peace_context_result(
    *,
    legality: dict[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    return _pending_context_result(
        pending_id=-268_435_441,
        revision=437,
        native_revision=437,
        date_raw=53_216_352,
        definition_key="end_war_attacker_white_peace_interaction",
        actor_character_id=36_769,
        recipient_character_id=29_829,
        legality=legality,
        special_data_present=True,
        special_war_binding={
            "status": "available",
            "value": {
                "special_interaction_kind": (
                    "end_war_white_peace_interaction"
                ),
                "absolute_outcome": "white_peace",
                "war_id": 33_554_527,
                "actor_war_role": "primary_defender",
                "recipient_war_role": "primary_attacker",
                "binding_source": "native_common_war_relation",
            },
            "reason": None,
        },
    )


def _plan_for_pending_context(
    context_result: dict[str, object],
    *,
    action_steps: tuple[str, ...],
    active_wars: list[dict[str, object]] | None = None,
    termination_options: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    context = context_result["pending_character_interaction_context"]
    assert isinstance(context, dict)
    roles = context.get("roles")
    assert isinstance(roles, dict)
    pending_id = context["pending_interaction_id"]
    revision = context_result["queried_revision"]
    native_revision = context_result["queried_native_revision"]
    date_raw = context["date_raw"]
    history = [
        {
            "command": "query-pending-character-interaction-context-v1",
            "ok": True,
            "result": context_result,
        }
    ]
    episode_run_id = "native-707-pending-fixture"
    connection_generation = 3
    bound_termination_options = [
        {
            **copy.deepcopy(row),
            "queried_snapshot_id": f"session:{revision}",
            "queried_revision": revision,
            "queried_native_revision": native_revision,
            "queried_connection_generation": connection_generation,
            "episode_run_id": episode_run_id,
        }
        for row in (termination_options or [])
    ]
    driver = CallbackGameplayDriver(
        backend_id="native-headless",
        snapshot=lambda: {
            **_snapshot(int(revision), history),
            "paused": True,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "episode_run_id": episode_run_id,
            "diagnostics": {
                "connection_generation": connection_generation,
            },
            "played_character": {
                "character_id": roles["recipient_character_id"],
                "alive": True,
            },
            "pending_character_interaction": {
                "instance_id": pending_id,
                "sender_character_id": roles["actor_character_id"],
                "auto_accept_notification": False,
            },
            "war_termination_options": bound_termination_options,
            **(
                {
                    "active_wars": active_wars,
                    "player_armies": [],
                }
                if active_wars is not None
                else {}
            ),
        },
        execute=lambda _step, _revision: {},
        action_steps=action_steps,
    )
    return GameplayBridgeService(driver).plan_turn()["plan"]


def _army(
    army_id: int,
    *,
    soldiers: int | None,
    province_id: int,
    controllable: bool,
    move_target_province_id: int | None = None,
    **state: object,
) -> dict[str, object]:
    if (
        not controllable
        and move_target_province_id is not None
        and state.get("army_state") == "moving"
        and "route_province_ids" not in state
    ):
        # A normal paused moving hostile fixture carries a complete remaining
        # route.  Evidence-gap tests opt out explicitly with ``None``.
        state["route_province_ids"] = [move_target_province_id]
    return {
        "army_id": army_id,
        "owner_character_id": 707 if controllable else 808,
        "soldiers": soldiers,
        "current_province_id": province_id,
        "move_target_province_id": move_target_province_id,
        "controllable": controllable,
        **state,
    }


def _active_siege(
    *,
    siege_id: int = 901,
    army_id: int | None = 11,
    player: bool = True,
    progress_raw: int = 25_000,
    current_work_raw: int = 2_500_000,
    total_work_raw: int = 10_000_000,
    days_left: int | None = 12,
    assault_observable: bool = False,
    breach_level: int | None = None,
    assault_in_progress: bool | None = None,
    can_start_assault: bool | None = None,
    can_stop_assault: bool | None = None,
    assault_daily_progress_raw: int | None = None,
    assault_daily_casualties: int | None = None,
) -> dict[str, object]:
    return {
        "siege_id": siege_id,
        "besieging_army_id": army_id,
        "player_army_besieging": player,
        "progress_fraction": {"raw": progress_raw, "scale": 100_000},
        "current_work": {"raw": current_work_raw, "scale": 100_000},
        "total_work": {"raw": total_work_raw, "scale": 100_000},
        "days_left": days_left,
        "assault_observable": assault_observable,
        "breach_level": breach_level,
        "assault_in_progress": assault_in_progress,
        "can_start_assault": can_start_assault,
        "can_stop_assault": can_stop_assault,
        "assault_daily_progress": (
            {
                "raw": assault_daily_progress_raw,
                "scale": 100_000,
            }
            if assault_daily_progress_raw is not None
            else None
        ),
        "assault_daily_casualties": assault_daily_casualties,
    }


def _objective_state(
    province_id: int,
    *,
    occupant: int | None = None,
    occupation_observable: bool = True,
    fort_level: int | None = 2,
    garrison_size: int | None = 500,
    besieging_strength: int | None = 650,
    siege_observable: bool = True,
    active_siege: dict[str, object] | None = None,
) -> dict[str, object]:
    return {
        "province_id": province_id,
        "occupation_observable": occupation_observable,
        "is_occupied": (
            occupant is not None if occupation_observable else None
        ),
        "occupying_character_id": (
            occupant if occupation_observable else None
        ),
        "fort_level": fort_level,
        "garrison_size": garrison_size,
        "besieging_strength": besieging_strength,
        "siege_observable": siege_observable,
        "active_siege": active_siege if siege_observable else None,
    }


def _war(
    *,
    war_id: int = 88,
    allied_armies: list[dict[str, object]],
    enemy_armies: list[dict[str, object]],
    score: int = 17,
    player_side: str = "attacker",
    player_is_primary_war_leader: bool | None = True,
    enemy_primary_default_raise_province_id: int | None = None,
    war_objective_province_ids: list[int] | None = None,
    objective_province_states: list[dict[str, object]] | None = None,
    targeted_title_ids: list[int] | None = None,
    war_duration_days: int = 203,
) -> dict[str, object]:
    return {
        "war_id": war_id,
        "player_side": player_side,
        "primary_opponent_character_id": 808,
        "player_is_primary_war_leader": player_is_primary_war_leader,
        "enemy_primary_default_raise_province_id": (
            enemy_primary_default_raise_province_id
        ),
        "player_relative_war_score": score,
        "war_duration_days": war_duration_days,
        "allied_armies": allied_armies,
        "enemy_armies": enemy_armies,
        "war_objective_province_ids": war_objective_province_ids or [],
        "objective_province_states": objective_province_states or [],
        "targeted_title_ids": targeted_title_ids or [],
    }


def _termination_options(
    war_id: int = 88,
    *,
    score: int = 17,
    claim_cb_ready: bool = False,
    war_duration_days: int = 203,
    recipient_decision_status_raw: int = 0,
) -> dict[str, object]:
    return {
        "war_id": war_id,
        "player_side": "attacker",
        "player_is_primary_war_leader": True,
        "player_relative_war_score": score,
        "war_duration_days": war_duration_days,
        "active_casus_belli_present": True,
        "active_casus_belli_identity": {
            "database_index": 0 if claim_cb_ready else 17,
            "canonical_key": (
                "claim_cb" if claim_cb_ready else "county_conquest_cb"
            ),
        },
        "cb_allows_white_peace": True,
        "absolute_war_scores_observable": True,
        "attacker_war_score": score,
        "defender_war_score": -score,
        "war_score_breakdown": None,
        "options": {
            "surrender": {
                "outcome": "attacker_defeat",
                "hostage_variant": "none",
                "context_constructed": True,
                "native_validator_passed": True,
                "available": True,
                "terms_observable": False,
                "terms": {
                    "status": "unavailable",
                    "reason": "cb_specific_terms_not_observable",
                },
                "ai_acceptance_observable": True,
                "ai_acceptance": {
                    "raw": -2_900_000,
                    "scale": 100_000,
                },
                "auto_accept_observable": True,
                "auto_accept": True,
                "recipient_response": {
                    "status": "available",
                    "decision_status_raw": 0,
                    "would_accept_now": True,
                },
            },
            "white_peace": {
                "outcome": "white_peace",
                "hostage_variant": "none",
                "context_constructed": True,
                "native_validator_passed": True if claim_cb_ready else None,
                "available": claim_cb_ready,
                "terms_observable": False,
                "terms": {
                    "status": "unavailable",
                    "reason": "cb_specific_terms_not_observable",
                },
                "ai_acceptance_observable": True,
                "ai_acceptance": {
                    "raw": -1_300_000,
                    "scale": 100_000,
                },
                "auto_accept_observable": True,
                "auto_accept": False,
                "recipient_response": (
                    {
                        "status": "available",
                        "decision_status_raw": (
                            recipient_decision_status_raw
                        ),
                        "would_accept_now": (
                            recipient_decision_status_raw != 2
                        ),
                    }
                    if claim_cb_ready
                    else {
                        "status": "unavailable",
                        "decision_status_raw": None,
                        "would_accept_now": None,
                    }
                ),
            },
            "victory": {
                "outcome": "attacker_victory",
                "hostage_variant": "none",
                "context_constructed": True,
                "native_validator_passed": False,
                "available": False,
                "terms_observable": False,
                "terms": {
                    "status": "unavailable",
                    "reason": "cb_specific_terms_not_observable",
                },
                "ai_acceptance_observable": True,
                "ai_acceptance": {
                    "raw": -8_200_000,
                    "scale": 100_000,
                },
                "auto_accept_observable": True,
                "auto_accept": False,
                "recipient_response": {
                    "status": "unavailable",
                    "decision_status_raw": None,
                    "would_accept_now": None,
                },
            },
        },
        "source": "native",
    }


def _de_jure_white_peace_options(
    war_id: int = 88,
    *,
    score: int = 47,
    duration_days: int = 224,
) -> dict[str, object]:
    options = _termination_options(
        war_id, score=score, war_duration_days=duration_days
    )
    options["active_casus_belli_identity"] = {
        "database_index": 17,
        "canonical_key": "individual_county_de_jure_cb",
    }
    white_peace = options["options"]["white_peace"]
    assert isinstance(white_peace, dict)
    white_peace.update(
        {
            "native_validator_passed": True,
            "available": True,
            "ai_acceptance_observable": True,
            "ai_acceptance": {"raw": 1_100_000, "scale": 100_000},
            "auto_accept_observable": True,
            "auto_accept": False,
            "recipient_response": {
                "status": "available",
                "decision_status_raw": 0,
                "would_accept_now": True,
            },
        }
    )
    return options


def _raiktor_inbound_white_peace_options(
    war_id: int = 88,
    *,
    score: int = 7,
    war_duration_days: int = 937,
) -> dict[str, object]:
    options = _termination_options(
        war_id,
        score=score,
        war_duration_days=war_duration_days,
    )
    options["active_casus_belli_identity"] = {
        "database_index": 409,
        "canonical_key": "raiktor_claim_cb",
    }
    white_peace = options["options"]["white_peace"]
    assert isinstance(white_peace, dict)
    # This event CB cannot be offered outbound in the observed frame.  The
    # inbound pending and its reply legality are the responder-path authority.
    white_peace["native_validator_passed"] = False
    white_peace["available"] = False
    return options


def _termination_terms(
    war_id: int = 88,
    *,
    claimant_character_id: int = 29_829,
    strong: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "status": "available",
        "war_id": war_id,
        "casus_belli": {"database_index": 0, "canonical_key": "claim_cb"},
        "supported_slice": "claim_cb_claim_disposition",
        "claimant_character_id": claimant_character_id,
        "target_title_ids": [2_388],
        "claims": [
            {
                "title_id": 2_388,
                "present": True,
                "strong": strong,
                "implicit": False,
                "state": "strong_explicit" if strong else "weak_explicit",
            }
        ],
        "outcomes": {
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
        },
        "readiness": {
            "identity_ready": True,
            "targets_ready": True,
            "claim_rows_ready": True,
            "claim_disposition_ready": True,
            "ready": True,
        },
        "provenance": {
            "game_version": "1.19.0.6",
            "executable_sha256": (
                "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
            ),
            "native_reader": "CWar+0x270/+0x290;0x28B1AA0",
            "present_claim_lifecycle": (
                "present_only_vtable_slot_0_delete_flags_0"
            ),
            "claim_script_sha256": (
                "D9AA37BDC45F81B4F6185B2697A3EBD09404084EA0D3CF77BBE3C1D2C962E8B1"
            ),
        },
    }


def _ready_white_peace_snapshot(
    *,
    revision: int = 11,
    date_raw: int = 53_177_976,
    score: int = 37,
    options: dict[str, object] | None = None,
    terms: dict[str, object] | None = None,
    history: list[dict[str, object]] | None = None,
    include_terms: bool = True,
) -> dict[str, object]:
    war_id = 88
    snapshot = {
        **_snapshot(revision),
        "paused": True,
        "native_revision": 7,
        "date_raw": date_raw,
        "episode_run_id": "native-29829-ready",
        "diagnostics": {"connection_generation": 3},
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": [
            _war(
                war_id=war_id,
                allied_armies=[
                    _army(
                        11,
                        soldiers=900,
                        province_id=20,
                        controllable=True,
                    )
                ],
                enemy_armies=[],
                score=score,
                targeted_title_ids=[2_388],
            )
        ],
        "player_armies": [
            _army(
                11,
                soldiers=900,
                province_id=20,
                controllable=True,
            )
        ],
        "native_command_history": history or [],
    }
    binding = {
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": revision,
        "queried_native_revision": 7,
        "queried_connection_generation": 3,
        "episode_run_id": "native-29829-ready",
    }
    snapshot["war_termination_options"] = [
        {
            **(
                options
                if options is not None
                else _termination_options(
                    score=score,
                    claim_cb_ready=True,
                    war_duration_days=436,
                )
            ),
            **binding,
        }
    ]
    snapshot["war_termination_terms"] = (
        [
            {
                **(terms if terms is not None else _termination_terms()),
                **binding,
            }
        ]
        if include_terms
        else []
    )
    return snapshot


def _termination_reuse_snapshot(
    *,
    date_raw: int = 53_177_976,
    wars: list[dict[str, object]] | None = None,
    history: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    player = _army(
        11,
        soldiers=900,
        province_id=20,
        controllable=True,
        move_target_province_id=77,
        army_state="moving",
        route_province_ids=[77],
    )
    active_wars = wars or [
        _war(
            war_id=88,
            allied_armies=[player],
            enemy_armies=[],
            score=17,
            war_objective_province_ids=[77],
            targeted_title_ids=[2_388],
        )
    ]
    return {
        **_snapshot(12),
        "paused": True,
        "map_ready": True,
        "native_revision": 12,
        "date_raw": date_raw,
        "episode_run_id": "native-29829-reuse",
        "diagnostics": {"connection_generation": 3},
        "played_character": {"character_id": 29_829, "alive": True},
        "active_wars": active_wars,
        "player_armies": [player],
        "army_routes_supported": True,
        "move_route_preview_supported": True,
        "route_contact_horizon_supported": False,
        "war_termination_options": [],
        "native_command_history": history or [],
    }


def _termination_query_row(
    index: int,
    snapshot: dict[str, object],
    *,
    war_id: int = 88,
    options: dict[str, object] | None = None,
    decorated: bool = False,
) -> dict[str, object]:
    query_options = copy.deepcopy(
        options if options is not None else _termination_options(war_id)
    )
    active_signature = war_termination_active_war_signature(
        snapshot["active_wars"]
    )
    decision_signature = war_termination_negative_query_signature(
        query_options
    )
    assert active_signature is not None
    assert decision_signature is not None
    step = query_war_termination_options_step(war_id)
    result: dict[str, object] = {
        "step": step,
        "accepted": True,
        "status": "available",
        "query_sequence": index,
        "war_termination_options": query_options,
        "queried_snapshot_id": snapshot["snapshot_id"],
        "queried_revision": snapshot["revision"],
        "queried_native_revision": snapshot["native_revision"],
        "queried_connection_generation": snapshot["diagnostics"][
            "connection_generation"
        ],
        "queried_episode_run_id": snapshot["episode_run_id"],
        "termination_query_context": {
            "schema_version": 1,
            "queried_date_raw": snapshot["date_raw"],
            "queried_connection_generation": snapshot["diagnostics"][
                "connection_generation"
            ],
            "queried_episode_run_id": snapshot["episode_run_id"],
            "queried_character_id": snapshot["played_character"][
                "character_id"
            ],
            "active_war_signature": active_signature,
            "negative_decision_signature": decision_signature,
            "queried_war_duration_days": query_options[
                "war_duration_days"
            ],
        },
    }
    command = step
    if decorated:
        command = "auto-turn"
        result.update(
            {
                "requested_step": "auto-turn",
                "auto_turn": {"selected_step": step},
            }
        )
    return {
        "index": index,
        "command": command,
        "ok": True,
        "result": result,
    }


def _termination_exit_terms_v2() -> dict[str, object]:
    fixture = (
        ROOT
        / "tests"
        / "fixtures"
        / "war_termination_exit_terms_v2_synthetic.json"
    )
    return json.loads(fixture.read_text(encoding="utf-8"))


def _army_strength(
    army_id: int,
    role: str,
    war_ids: list[int],
    *,
    current: int = 1_200,
    maximum: int = 1_500,
    regiment_count: int = 3,
    base_power_raw: int = 180_000_000,
) -> dict[str, object]:
    return {
        "status": "available",
        "army_id": army_id,
        "native_carmy_id": army_id + 1_000,
        "scope_role": role,
        "war_ids": war_ids,
        "regiment_count": regiment_count,
        "current_soldiers": current,
        "maximum_soldiers": maximum,
        "ai_base_power_raw": base_power_raw,
        "ai_base_power_scale": 100_000,
        "unavailable_reason": None,
    }


def _war_progress(
    date_raw: int,
    *,
    player: dict[str, object],
    enemies: list[dict[str, object]],
    score: int,
    war_id: int = 88,
    objectives: list[int] | None = None,
    objective_states: list[dict[str, object]] | None = None,
    fallback: int | None = None,
) -> dict[str, object]:
    keys = (
        "army_id",
        "current_province_id",
        "soldiers",
        "move_target_province_id",
        "army_state",
        "army_state_code",
        "in_combat",
        "retreating",
        "route_province_ids",
    )

    def compact(army: dict[str, object]) -> dict[str, object]:
        return {key: army.get(key) for key in keys if key in army}

    return {
        "date_raw": date_raw,
        "wars": [
            {
                "war_id": war_id,
                "player_relative_war_score": score,
                "war_objective_province_ids": objectives or [],
                "objective_province_states": objective_states or [],
                "enemy_primary_default_raise_province_id": fallback,
                "player_armies": [compact(player)],
                "enemy_armies": [compact(enemy) for enemy in enemies],
            }
        ],
    }


def _advance_row(
    index: int,
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, object]:
    return {
        "index": index,
        "command": "life-advance",
        "ok": True,
        "result": {
            "elapsed_days": (
                int(after["date_raw"]) - int(before["date_raw"])
            )
            // 24,
            "war_progress_before": before,
            "war_progress_after": after,
        },
    }


def _raise_troops_row(
    index: int, army: dict[str, object]
) -> dict[str, object]:
    army_id = int(army["army_id"])
    return {
        "index": index,
        "command": "raise-troops-default",
        "ok": True,
        "result": {
            "step": "raise-troops-default",
            "accepted": True,
            "status": "submitted",
            "war_action": {
                "status": "raised",
                "raised_army_ids": [army_id],
            },
            "player_armies": [copy.deepcopy(army)],
            "snapshot_id": "session:91",
            "revision": 91,
        },
    }


def _restore_checkpoint_row(
    index: int,
    *,
    checkpoint_history_index: int,
    actor_character_id: int = 707,
    episode_run_id: str | None = None,
) -> dict[str, object]:
    return {
        "index": index,
        "command": "restore-checkpoint",
        "ok": True,
        "result": {
            "step": "restore-checkpoint",
            "accepted": True,
            "status": "restored",
            "checkpoint": {
                "status": "saved",
                "history_index": checkpoint_history_index,
                "episode_character_id": actor_character_id,
                "episode_run_id": episode_run_id,
            },
        },
    }


def _assault_action_row(
    index: int,
    *,
    status: str,
    siege_id: int = 901,
    war_id: int = 88,
    province_id: int = 2585,
    decorated: bool = False,
) -> dict[str, object]:
    step = (
        f"start-assault-{siege_id}"
        if status == "assault_started"
        else f"stop-assault-{siege_id}"
    )
    action = {
        "status": status,
        "siege_id": siege_id,
        "war_id": war_id,
        "province_id": province_id,
    }
    result: dict[str, object] = {
        "assault_action": dict(action),
        "war_action": dict(action),
    }
    command = step
    if decorated:
        command = "auto-turn"
        result.update(
            {
                "requested_step": "auto-turn",
                "auto_turn": {"selected_step": step},
            }
        )
    return {
        "index": index,
        "command": command,
        "ok": True,
        "result": result,
    }


def _failed_life_advance_row(
    index: int, *, decorated: bool = False
) -> dict[str, object]:
    result: dict[str, object] = {}
    command = "life-advance"
    if decorated:
        command = "auto-turn"
        result = {"auto_turn": {"selected_step": "life-advance"}}
    return {
        "index": index,
        "command": command,
        "ok": False,
        "result": result,
        "error": "fixture composite postcondition failed",
    }


def _preview_row(
    index: int,
    *,
    army_id: int = 11,
    origin: int,
    target: int,
    date_raw: int,
    route: list[int],
) -> dict[str, object]:
    return {
        "index": index,
        "command": f"preview-move-army-{army_id}-to-{target}",
        "ok": True,
        "result": {
            "accepted": True,
            "status": "available",
            "route_preview": {
                "status": "available",
                "army_id": army_id,
                "origin_province_id": origin,
                "target_province_id": target,
                "route_province_ids": list(route),
                "previewed_date_raw": date_raw,
            },
        },
    }


def _campaign_root_row(
    index: int,
    *,
    date_raw: int,
    capital_province_id: int,
    actor_character_id: int = 707,
    held_county_capital_province_ids: tuple[int, ...] | None = None,
) -> dict[str, object]:
    partition = (
        [
            {
                "title": {
                    "title_id": 70_000 + rank,
                    "tier_raw": 2,
                    "tier_key": "county",
                },
                "first_heir_character_id": None,
                "capital_province_id": province_id,
                "primary": rank == 1,
            }
            for rank, province_id in enumerate(
                held_county_capital_province_ids or (), start=1
            )
        ]
        if held_county_capital_province_ids is not None
        else None
    )
    return {
        "index": index,
        "command": "query-campaign-root-context-v1",
        "ok": True,
        "result": {
            "campaign_root_context": {
                "status": "available",
                "snapshot_revision": 90,
                "date_raw": date_raw,
                "player_character_id": actor_character_id,
                "capital_province_id": capital_province_id,
                **(
                    {"held_title_partition": partition}
                    if partition is not None
                    else {}
                ),
                "readiness": {
                    "ready": True,
                    "held_title_partition_ready": partition is not None,
                },
            }
        },
    }


def _route_contact_row(
    index: int,
    *,
    army_id: int = 11,
    origin: int,
    target: int,
    date_raw: int,
    route: list[int],
    hostile_ids: tuple[int, ...],
    contact_free: bool,
    episode_run_id: str | None = None,
) -> dict[str, object]:
    step = (
        f"query-route-contact-horizon-v1-{army_id}-to-{target}"
        f"-h-{len(hostile_ids)}-"
        + "-".join(str(value) for value in hostile_ids)
    )
    return {
        "index": index,
        "command": step,
        "ok": True,
        "result": {
            "step": step,
            "accepted": True,
            "status": "available",
            "query_sequence": index,
            "snapshot_revision": 90,
            "route_contact_horizon": {
                "status": "available",
                "date_raw": date_raw,
                "snapshot_revision": 90,
                "subject_army_id": army_id,
                "target_province_id": target,
                "hostile_army_ids": list(hostile_ids),
                "subject_route": {
                    "timeline_observable": True,
                    "army_id": army_id,
                    "current_province_id": origin,
                    "effective_origin_province_id": (
                        route[0] if route else origin
                    ),
                    "route_province_ids": list(route),
                    "arrival_date_raws": [
                        date_raw + 24 * (offset + 1)
                        for offset in range(len(route))
                    ],
                },
                "hostile_routes": [
                    {
                        "timeline_observable": True,
                        "army_id": hostile_id,
                        "current_province_id": 99,
                        "effective_origin_province_id": 99,
                        "route_province_ids": [],
                        "arrival_date_raws": [],
                    }
                    for hostile_id in hostile_ids
                ],
                "horizon_start_date_raw": date_raw,
                "horizon_end_date_raw": date_raw + 24,
                "one_day_contact_free": contact_free,
                "conflicts": (
                    []
                    if contact_free
                    else [
                        {
                            "kind": "same_province",
                            "hostile_army_id": hostile_ids[0],
                            "province_id": target,
                            "overlap_start_date_raw": date_raw + 24,
                            "overlap_end_date_raw": date_raw + 24,
                        }
                    ]
                ),
            },
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "queried_episode_run_id": episode_run_id,
        },
    }


def _native_war_plan(
    *,
    player: dict[str, object],
    players: list[dict[str, object]] | None = None,
    allied_armies: list[dict[str, object]] | None = None,
    enemies: list[dict[str, object]],
    score: int,
    date_raw: int,
    war_id: int = 88,
    history: list[dict[str, object]] | None = None,
    objective: int | None = None,
    objectives: list[int] | None = None,
    fallback: int | None = None,
    steps: tuple[str, ...] = (),
    paused: bool = True,
    army_routes_supported: bool | None = None,
    move_route_preview_supported: bool | None = None,
    route_contact_horizon_supported: bool = False,
    objective_states: list[dict[str, object]] | None = None,
    occupation_supported: bool = False,
    fort_level_supported: bool = False,
    garrison_supported: bool = False,
    siege_progress_supported: bool = False,
    assault_supported: bool = False,
    rollback_war_failure: dict[str, object] | None = None,
    rollback_war_failures: list[dict[str, object]] | None = None,
    battle_speed_readiness: dict[str, object] | None = None,
    negative_reuse_expires_date_raw: int | None = None,
    additional_wars: list[dict[str, object]] | None = None,
    termination_options: list[dict[str, object]] | None = None,
    targeted_title_ids: list[int] | None = None,
    player_side: str = "attacker",
    player_is_primary_war_leader: bool | None = True,
    war_duration_days: int = 203,
    army_strengths: list[dict[str, object]] | None = None,
    army_strengths_status: str | None = None,
) -> dict[str, object]:
    controlled = list(players) if players is not None else [player]
    route_field_present = "route_province_ids" in player
    driver = CallbackGameplayDriver(
        backend_id="native-headless",
        snapshot=lambda: {
            **_snapshot(90),
            "paused": paused,
            "map_ready": True,
            "army_routes_supported": (
                route_field_present
                if army_routes_supported is None
                else army_routes_supported
            ),
            "move_route_preview_supported": (
                route_field_present
                if move_route_preview_supported is None
                else move_route_preview_supported
            ),
            "route_contact_horizon_supported": (
                route_contact_horizon_supported
            ),
            "native_revision": 90,
            "diagnostics": {"connection_generation": 1},
            "episode_run_id": None,
            "played_character": {"character_id": 707, "alive": True},
            "war_objective_occupation_supported": occupation_supported,
            "war_objective_fort_level_supported": fort_level_supported,
            "war_objective_garrison_supported": garrison_supported,
            "war_objective_siege_progress_supported": (
                siege_progress_supported
            ),
            "war_objective_assault_supported": assault_supported,
            "date_raw": date_raw,
            "native_command_history": history or [],
            "native_rollback_war_failure": rollback_war_failure,
            **(
                {"native_rollback_war_failures": rollback_war_failures}
                if rollback_war_failures is not None
                else {}
            ),
            "active_wars": [
                {
                    **_war(
                        war_id=war_id,
                        allied_armies=(
                            allied_armies
                            if allied_armies is not None
                            else controlled
                        ),
                        enemy_armies=enemies,
                        score=score,
                        player_side=player_side,
                        player_is_primary_war_leader=(
                            player_is_primary_war_leader
                        ),
                        enemy_primary_default_raise_province_id=fallback,
                        war_objective_province_ids=(
                            list(objectives)
                            if objectives is not None
                            else [objective]
                            if objective is not None
                            else []
                        ),
                        objective_province_states=objective_states,
                        targeted_title_ids=targeted_title_ids,
                        war_duration_days=war_duration_days,
                    ),
                    **(
                        {
                            "war_termination_negative_reuse": {
                                "status": "negative_assessment_reused",
                                "war_id": war_id,
                                "expires_date_raw": (
                                    negative_reuse_expires_date_raw
                                )
                            }
                        }
                        if negative_reuse_expires_date_raw is not None
                        else {}
                    ),
                },
                *(additional_wars or []),
            ],
            "player_armies": controlled,
            "war_termination_options": termination_options or [],
            "army_strengths": army_strengths or [],
            "army_strengths_status": army_strengths_status,
        },
        execute=lambda _step, _revision: {},
        action_steps=steps,
    )
    if isinstance(battle_speed_readiness, dict):
        base_capabilities = driver.capabilities
        driver.capabilities = lambda: {
            **base_capabilities(),
            "battle_speed_readiness": dict(battle_speed_readiness),
        }
    return GameplayBridgeService(driver).plan_turn()["plan"]


class GameplayBridgeTests(unittest.TestCase):
    def test_construction_source_red_still_checks_independent_marriage(self) -> None:
        state = {**_snapshot(7), "paused": True, "map_ready": True,
                 "active_event": None, "pending_character_interaction": None,
                 "active_wars": []}
        driver = CallbackGameplayDriver(
            backend_id="native-headless", snapshot=lambda: state,
            execute=lambda _step, _revision: {},
            action_steps=("life-advance",),
        )
        driver.allow_private_construction_formal_trial = True
        driver.allow_private_family_marriage_formal_trial = True
        base_plan = {"policy": "one-life-turn-v1", "selected_step": "life-advance"}

        def construction(_driver, planned, _snapshot, _history, _steps,
                         *, prewar_arbitration):
            self.assertFalse(prewar_arbitration)
            return {**planned, "plan": {**planned["plan"],
                "selected_step": None,
                "construction_private_query": {"status": "source_red"},
                "reason": "private construction source unavailable; preserve RED"}}

        def marriage(_driver, planned, _snapshot, *, prewar_arbitration):
            self.assertFalse(prewar_arbitration)
            self.assertEqual(planned["plan"]["selected_step"], "life-advance")
            return {**planned, "plan": {**planned["plan"],
                "selected_step": "private-submit-first-heir-marriage-v1"}}

        with (
            mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=base_plan),
            mock.patch("xar_autoplayer.bridge.service.plan_construction_private", side_effect=construction),
            mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private", side_effect=marriage) as family,
        ):
            chosen = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(chosen["selected_step"], "private-submit-first-heir-marriage-v1")
        self.assertEqual(chosen["construction_private_query"]["status"], "source_red")
        family.assert_called_once()

        with (
            mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=base_plan),
            mock.patch("xar_autoplayer.bridge.service.plan_construction_private", side_effect=construction),
            mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private", side_effect=lambda _driver, planned, _snapshot, *, prewar_arbitration: planned),
        ):
            blocked = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertIsNone(blocked["selected_step"])
        self.assertEqual(blocked["reason"], "private construction source unavailable; preserve RED")

    def test_peaceful_declaration_queries_private_nonwar_before_war(self) -> None:
        state = {
            **_snapshot(7),
            "paused": True,
            "map_ready": True,
            "active_event": None,
            "pending_character_interaction": None,
            "active_wars": [],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: state,
            execute=lambda _step, _revision: {},
            action_steps=("query-declarable-wars", "life-advance"),
        )
        driver.allow_private_construction_formal_trial = True
        driver.allow_private_family_marriage_formal_trial = True
        war_plan = {"policy": "one-life-turn-v1", "selected_step": "query-declarable-wars"}

        def construction(_driver, planned, _snapshot, _history, _steps, *, prewar_arbitration):
            self.assertTrue(prewar_arbitration)
            return {**planned, "plan": {**planned["plan"],
                "selected_step": "private-submit-player-construction-v1"}}

        with (
            mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=war_plan),
            mock.patch("xar_autoplayer.bridge.service.plan_construction_private", side_effect=construction) as econ,
            mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private", side_effect=lambda _driver, planned, _snapshot, *, prewar_arbitration: planned) as family,
        ):
            chosen = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(chosen["selected_step"], "private-submit-player-construction-v1")
        econ.assert_called_once()
        family.assert_called_once()

        def no_construction(_driver, planned, _snapshot, _history, _steps, *, prewar_arbitration):
            self.assertTrue(prewar_arbitration)
            return planned
        def marriage(_driver, planned, _snapshot, *, prewar_arbitration):
            self.assertTrue(prewar_arbitration)
            return {**planned, "plan": {**planned["plan"],
                "selected_step": "private-submit-first-heir-marriage-v1"}}
        with (
            mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=war_plan),
            mock.patch("xar_autoplayer.bridge.service.plan_construction_private", side_effect=no_construction),
            mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private", side_effect=marriage),
        ):
            chosen = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(chosen["selected_step"], "private-submit-first-heir-marriage-v1")

        with (
            mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=war_plan),
            mock.patch("xar_autoplayer.bridge.service.plan_construction_private", side_effect=no_construction),
            mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private", side_effect=lambda _driver, planned, _snapshot, *, prewar_arbitration: planned),
        ):
            retained = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(retained["selected_step"], "query-declarable-wars")

        state["active_wars"] = [{"war_id": 4}]
        def no_prewar_construction(_driver, planned, _snapshot, _history, _steps, *, prewar_arbitration):
            self.assertFalse(prewar_arbitration)
            return planned
        with (
            mock.patch("xar_autoplayer.bridge.service.choose_one_life_turn", return_value=war_plan),
            mock.patch("xar_autoplayer.bridge.service.plan_construction_private", side_effect=no_prewar_construction) as econ,
            mock.patch("xar_autoplayer.bridge.service.plan_family_marriage_private", side_effect=lambda _driver, planned, _snapshot, *, prewar_arbitration: planned),
        ):
            retained = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(retained["selected_step"], "query-declarable-wars")
        self.assertFalse(econ.call_args.kwargs["prewar_arbitration"])

    def test_plan_turn_routes_only_advertised_production_v3_readonly_query(
        self,
    ) -> None:
        selected = query_combat_simulation_inputs_v3_step(
            32, 31, [11], [21]
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(7),
            execute=lambda _step, _revision: {},
            action_steps=("life-advance",),
        )
        original_capabilities = driver.capabilities
        driver.capabilities = lambda: {
            **original_capabilities(),
            "bridge_capabilities": [
                QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY
            ],
        }
        planned = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_siege_forecast_inputs_query",
            "selected_step": selected,
        }
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=planned,
        ):
            routed = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertEqual(routed["selected_step"], selected)

        driver.capabilities = original_capabilities
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=planned,
        ):
            missing = GameplayBridgeService(driver).plan_turn()["plan"]
        self.assertIsNone(missing["selected_step"])
        self.assertEqual(missing["required_step"], selected)

    def test_plan_turn_passes_battle_readiness_and_routes_dynamic_journal_query(
        self,
    ) -> None:
        readiness = {
            "decision_sentinel_live_ready": True,
            "terminal_sentinel_live_ready": False,
            "overwhelming_matrix_live_ready": False,
        }
        terminal_step = query_battle_terminal_transition_v1_step(
            335_544_325, 101, 40
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(7),
            execute=lambda _step, _revision: {},
            action_steps=("life-advance",),
        )
        driver.capabilities = lambda: {
            **CallbackGameplayDriver.capabilities(driver),
            "bridge_capabilities": [
                QUERY_BATTLE_TERMINAL_TRANSITION_V1_CAPABILITY
            ],
            "battle_speed_readiness": readiness,
        }
        planned = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_battle_terminal_journal_query",
            "selected_step": terminal_step,
        }

        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=planned,
        ) as choose:
            result = GameplayBridgeService(driver).plan_turn()

        self.assertEqual(result["plan"]["selected_step"], terminal_step)
        self.assertEqual(
            choose.call_args.kwargs["battle_speed_readiness"], readiness
        )

    def test_plan_turn_routes_parameterized_decision_epoch_target(self) -> None:
        selected = battle_decision_epoch_advance_step(53_179_344)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(7),
            execute=lambda _step, _revision: {},
            action_steps=(
                "life-advance",
                BATTLE_DECISION_EPOCH_ADVANCE_STEP,
            ),
        )
        planned = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_global_battle_decision_epoch",
            "selected_step": selected,
        }

        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=planned,
        ):
            result = GameplayBridgeService(driver).plan_turn()

        self.assertEqual(result["plan"]["selected_step"], selected)

    def test_irreversible_war_steps_never_fallback_to_life_advance(self) -> None:
        for step in (
            "declare-war-808-17-0",
            "war-declare-palermo",
            "offer-white-peace-88",
            "surrender-war-88",
            "query-war-termination-options-88",
            "query-combat-simulation-inputs-v2-2596-2597-a-1-357-d-1-83886341",
            "query-combat-simulation-inputs-v3-2596-2597-a-1-357-d-1-83886341",
            "enforce-demands-88",
        ):
            with self.subTest(step=step):
                routed = _route_plan_to_available_step(
                    {"phase": "fixture", "selected_step": step},
                    {"life-advance"},
                )
                self.assertIsNone(routed["selected_step"])
                self.assertEqual(routed["required_step"], step)

    def test_auto_turn_attaches_plan_to_unsupported_pre_send_failure(
        self,
    ) -> None:
        step = "merge-armies-101-with-303"
        planned = {
            "policy": "one-life-turn-v1",
            "phase": "native_war_preoffensive_army_consolidation",
            "selected_step": step,
        }

        def reject(_step: str, _revision: int | None) -> dict[str, object]:
            raise UnsupportedStepError(
                "native DLL does not implement gameplay step " + step
            )

        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(7),
            execute=reject,
            action_steps=(step,),
        )
        with mock.patch(
            "xar_autoplayer.bridge.service.choose_one_life_turn",
            return_value=planned,
        ):
            with self.assertRaises(UnsupportedStepError) as raised:
                GameplayBridgeService(driver).auto_turn()

        self.assertEqual(raised.exception.selected_step, step)
        self.assertEqual(raised.exception.plan, planned)

    def test_war_contract_preserves_adapter_objective_order(self) -> None:
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    targeted_title_ids=[2388, 2200, 2388],
                    war_objective_province_ids=[2585, 2510, 2548, 2585],
                )
            ]
        )

        self.assertEqual(normalized[0]["targeted_title_ids"], [2388, 2200])
        self.assertEqual(
            normalized[0]["war_objective_province_ids"],
            [2585, 2510, 2548],
        )
        self.assertEqual(
            war_objective_province_ids(normalized),
            [2585, 2510, 2548],
        )

    def test_war_contract_normalizes_exact_objective_state(self) -> None:
        state = _objective_state(
            2585,
            active_siege=_active_siege(
                current_work_raw=2_500_001,
                total_work_raw=10_000_000,
            ),
        )
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    war_objective_province_ids=[2585],
                    objective_province_states=[state],
                )
            ]
        )[0]["objective_province_states"]

        self.assertEqual(len(normalized), 1)
        siege = normalized[0]["active_siege"]
        self.assertEqual(
            siege["remaining_work"],
            {"raw": 7_499_999, "scale": 100_000},
        )
        self.assertEqual(normalized[0]["garrison_size"], 500)

    def test_war_contract_normalizes_assault_subdomain_all_or_none(self) -> None:
        active = _active_siege(
            assault_observable=True,
            breach_level=2,
            assault_in_progress=False,
            can_start_assault=True,
            can_stop_assault=False,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    war_objective_province_ids=[2585],
                    objective_province_states=[
                        _objective_state(2585, active_siege=active)
                    ],
                )
            ]
        )[0]["objective_province_states"][0]["active_siege"]

        self.assertTrue(normalized["assault_observable"])
        self.assertEqual(normalized["breach_level"], 2)
        self.assertTrue(normalized["walls_breached"])
        self.assertEqual(
            normalized["assault_daily_progress"],
            {"raw": 340_000, "scale": 100_000},
        )
        self.assertEqual(normalized["assault_daily_casualties"], 16)

        partial = _active_siege()
        partial["breach_level"] = 1
        with self.assertRaisesRegex(ValueError, "unobservable assault"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=partial)
                        ],
                    )
                ]
            )

        malformed = dict(active)
        malformed["breach_level"] = 3
        with self.assertRaisesRegex(ValueError, "range 0..2"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[
                            _objective_state(2585, active_siege=malformed)
                        ],
                    )
                ]
            )

    def test_war_contract_distinguishes_unknown_from_zero(self) -> None:
        unknown = _objective_state(
            2585,
            occupation_observable=False,
            fort_level=None,
            garrison_size=None,
            besieging_strength=None,
            siege_observable=False,
        )
        zero = _objective_state(
            2510,
            fort_level=0,
            garrison_size=0,
            besieging_strength=0,
            active_siege=None,
        )
        states = normalize_active_wars(
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    war_objective_province_ids=[2585, 2510],
                    objective_province_states=[unknown, zero],
                )
            ]
        )[0]["objective_province_states"]

        self.assertIsNone(states[0]["is_occupied"])
        self.assertIsNone(states[0]["garrison_size"])
        self.assertFalse(states[0]["siege_observable"])
        self.assertFalse(states[1]["is_occupied"])
        self.assertEqual(states[1]["garrison_size"], 0)
        self.assertTrue(states[1]["siege_observable"])
        self.assertIsNone(states[1]["active_siege"])

    def test_war_contract_rejects_partial_or_malformed_objective_state(self) -> None:
        with self.assertRaisesRegex(ValueError, "completely match"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585, 2510],
                        objective_province_states=[_objective_state(2585)],
                    )
                ]
            )

        malformed = _objective_state(
            2585, active_siege=_active_siege()
        )
        malformed["active_siege"]["progress_fraction"]["scale"] = 1_000
        with self.assertRaisesRegex(ValueError, "fixed value is malformed"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[malformed],
                    )
                ]
            )

        contradictory = _objective_state(2585)
        contradictory["occupation_observable"] = False
        with self.assertRaisesRegex(ValueError, "unobservable occupation"):
            normalize_active_wars(
                [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        war_objective_province_ids=[2585],
                        objective_province_states=[contradictory],
                    )
                ]
            )

    def test_war_contract_preserves_route_order_and_repetition(self) -> None:
        normalized = normalize_active_wars(
            [
                _war(
                    allied_armies=[
                        _army(
                            11,
                            soldiers=900,
                            province_id=20,
                            controllable=True,
                            route_province_ids=[20, 31, 31, 2585],
                        )
                    ],
                    enemy_armies=[],
                )
            ]
        )

        self.assertEqual(
            normalized[0]["allied_armies"][0]["route_province_ids"],
            [20, 31, 31, 2585],
        )

    def test_enemy_endpoint_ledger_keeps_multi_stack_endpoints_separate(
        self,
    ) -> None:
        enemies = [
            _army(
                357,
                soldiers=800,
                province_id=2581,
                controllable=False,
                move_target_province_id=2596,
                army_state="moving",
                route_province_ids=[2596],
            ),
            _army(
                33_554_657,
                soldiers=2_400,
                province_id=2581,
                controllable=False,
                move_target_province_id=2587,
                army_state="moving",
                route_province_ids=[2587],
            ),
        ]

        epochs = _enemy_endpoint_epochs(
            [],
            {
                "date_raw": 53_175_984,
                "active_wars": [
                    _war(
                        war_id=16_777_290,
                        allied_armies=[],
                        enemy_armies=enemies,
                    )
                ],
            },
        )

        self.assertEqual(
            [
                (epoch["enemy_army_id"], epoch["endpoint_province_id"])
                for epoch in epochs
            ],
            [(357, 2596), (33_554_657, 2587)],
        )

    def test_enemy_endpoint_ledger_keeps_natural_route_suffix_epoch(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2596, controllable=True
        )
        before_enemy = _army(
            357,
            soldiers=800,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2581, 2587, 2596],
        )
        after_enemy = _army(
            357,
            soldiers=None,
            province_id=2587,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2587, 2596],
        )
        before = _war_progress(
            53_175_984,
            player=player,
            enemies=[before_enemy],
            score=12,
            war_id=16_777_290,
        )
        after = _war_progress(
            53_176_152,
            player=player,
            enemies=[after_enemy],
            score=12,
            war_id=16_777_290,
        )
        final = _war_progress(
            53_176_320,
            player=player,
            enemies=[after_enemy],
            score=12,
            war_id=16_777_290,
        )

        epochs = _enemy_endpoint_epochs(
            [
                _advance_row(1, before, after),
                _advance_row(2, after, final),
            ],
            {
                "date_raw": 53_176_320,
                "active_wars": [
                    _war(
                        war_id=16_777_290,
                        allied_armies=[player],
                        enemy_armies=[after_enemy],
                    )
                ],
            },
        )

        self.assertEqual(len(epochs), 1)
        self.assertEqual(epochs[0]["epoch_sequence"], 1)
        self.assertEqual(epochs[0]["observed_span_days"], 14)
        self.assertEqual(epochs[0]["milestones_crossed_days"], [7, 14])
        self.assertEqual(epochs[0]["route_province_ids"], [2596])

    def test_enemy_endpoint_ledger_reopens_on_nonprefix_reroute(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2596, controllable=True
        )
        before_enemy = _army(
            357,
            soldiers=800,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2587, 2596],
        )
        after_enemy = {
            **before_enemy,
            "route_province_ids": [2589, 2596],
        }
        before = _war_progress(
            53_175_984,
            player=player,
            enemies=[before_enemy],
            score=12,
            war_id=16_777_290,
        )
        after = _war_progress(
            53_176_056,
            player=player,
            enemies=[after_enemy],
            score=12,
            war_id=16_777_290,
        )

        epochs = _enemy_endpoint_epochs(
            [_advance_row(1, before, after)],
            {
                "date_raw": 53_176_056,
                "active_wars": [
                    _war(
                        war_id=16_777_290,
                        allied_armies=[player],
                        enemy_armies=[after_enemy],
                    )
                ],
            },
        )

        self.assertEqual([epoch["epoch_sequence"] for epoch in epochs], [1, 2])
        self.assertFalse(epochs[0]["active"])
        self.assertEqual(epochs[0]["closed_reason"], "intent_changed")
        self.assertTrue(epochs[1]["active"])

    def test_exact_route_previews_first_then_moves_with_fresh_safe_route(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        steps = (
            "preview-move-army-11-to-2585",
            "move-army-11-to-2585",
            "life-advance",
        )

        preview = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=steps,
        )
        self.assertEqual(preview["phase"], "native_war_route_preview")
        self.assertEqual(
            preview["selected_step"], "preview-move-army-11-to-2585"
        )

        move = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 31, 2585],
                )
            ],
            objective=2585,
            steps=steps,
        )
        self.assertEqual(move["selected_step"], "move-army-11-to-2585")
        self.assertEqual(
            move["pursuit"]["route_audit"]["route_province_ids"],
            [31, 31, 2585],
        )

    def test_war_route_queries_post_declaration_army_strengths_first(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            army_state="regular",
            route_province_ids=[],
        )

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=(
                QUERY_ARMY_STRENGTHS_STEP,
                "preview-move-army-11-to-2585",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_army_strength_query")
        self.assertEqual(plan["selected_step"], QUERY_ARMY_STRENGTHS_STEP)
        self.assertEqual(plan["army_strength_scope"]["enemy_army_ids"], [21])

    def test_war_route_consumes_exact_post_declaration_force_balance(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=1_600,
            province_id=99,
            controllable=False,
            army_state="regular",
            route_province_ids=[],
        )
        strength_rows = [
            {
                "status": "available",
                "army_id": 11,
                "scope_role": "player",
                "war_ids": [88],
                "current_soldiers": 900,
                "maximum_soldiers": 1_000,
                "ai_base_power_raw": 900_000,
            },
            {
                "status": "available",
                "army_id": 21,
                "scope_role": "active_war_enemy",
                "war_ids": [88],
                "current_soldiers": 1_600,
                "maximum_soldiers": 1_700,
                "ai_base_power_raw": 1_600_000,
            },
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=(
                QUERY_ARMY_STRENGTHS_STEP,
                "preview-move-army-11-to-2585",
                "life-advance",
            ),
            army_strengths=strength_rows,
            army_strengths_status="available",
        )

        self.assertEqual(plan["phase"], "native_war_route_preview")
        balance = plan["active_wars"][0]["army_strength_balance"]
        self.assertEqual(balance["friendly_current_soldiers"], 900)
        self.assertEqual(balance["enemy_current_soldiers"], 1_600)
        self.assertTrue(balance["hostile_operational_overmatch"])
        self.assertEqual(
            balance["interpretation"],
            "operational_routing_risk_not_battle_win_odds",
        )

    def test_outnumbered_regroup_allows_one_moving_subject_with_idle_siblings(
        self,
    ) -> None:
        subject = _army(
            11,
            soldiers=900,
            province_id=31,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[40, 2585],
        )
        siblings = [
            _army(
                army_id,
                soldiers=250,
                province_id=20,
                controllable=True,
                army_state="regular",
                route_province_ids=[],
            )
            for army_id in (12, 13, 14)
        ]
        war = _war(
            allied_armies=[subject, *siblings],
            enemy_armies=[
                _army(
                    21,
                    soldiers=2_500,
                    province_id=40,
                    controllable=False,
                    army_state="regular",
                    route_province_ids=[],
                )
            ],
            score=0,
            war_objective_province_ids=[2585],
        )

        ready = _outnumbered_attacker_regroup_input_ready(
            {
                "paused": True,
                "map_ready": True,
                "active_event": None,
                "pending_character_interaction": None,
            },
            active_wars=[war],
            controlled_armies=[subject, *siblings],
            tactical_war=war,
            current_province_id=31,
            route_rejections=[{"status": "unsafe", "target_province_id": 2585}],
            strength_balance={"hostile_operational_overmatch": True},
        )

        self.assertTrue(ready)

    def test_r0101_defender_regroup_requires_rejected_active_route(
        self,
    ) -> None:
        subject = _army(
            11, soldiers=534, province_id=8747, controllable=True,
            move_target_province_id=46, army_state="moving",
            route_province_ids=[23, 46], in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21, soldiers=1209, province_id=46, controllable=False,
            move_target_province_id=8747, army_state="moving",
            route_province_ids=[23, 8747],
        )
        war = _war(
            allied_armies=[subject], enemy_armies=[enemy], score=-28,
            player_side="defender", war_objective_province_ids=[46],
        )
        kwargs = {
            "active_wars": [war],
            "controlled_armies": [subject],
            "tactical_war": war,
            "current_province_id": 8747,
            "exact_objective_province_ids": [46],
            "route_rejections": [
                {"target_province_id": 46, "status": "blocked"}
            ],
            "strength_balance": {"hostile_operational_overmatch": True},
            "active_route_unsafe": True,
        }
        snapshot = {
            "paused": True, "map_ready": True, "active_event": None,
            "pending_character_interaction": None,
        }
        self.assertTrue(
            _outnumbered_primary_defender_regroup_input_ready(
                snapshot, **kwargs
            )
        )
        self.assertFalse(
            _outnumbered_primary_defender_regroup_input_ready(
                snapshot, **{**kwargs, "active_route_unsafe": False}
            )
        )
        self.assertFalse(
            _outnumbered_primary_defender_regroup_input_ready(
                snapshot, **{**kwargs, "route_rejections": []}
            )
        )
        self.assertFalse(
            _outnumbered_primary_defender_regroup_input_ready(
                snapshot, **{**kwargs, "strength_balance": None}
            )
        )

    def test_r0101_defender_only_queries_capital_before_safe_reroute(
        self,
    ) -> None:
        date_raw = 53_368_176
        player = _army(
            11, soldiers=534, province_id=8747, controllable=True,
            move_target_province_id=46, army_state="moving",
            route_province_ids=[23, 46], in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21, soldiers=1209, province_id=46, controllable=False,
            move_target_province_id=8747, army_state="moving",
            route_province_ids=[23, 8747],
        )
        strength_rows = [
            {
                "status": "available", "army_id": 11,
                "scope_role": "player", "war_ids": [88],
                "current_soldiers": 534, "maximum_soldiers": 842,
                "ai_base_power_raw": 1_497_200_000,
            },
            {
                "status": "available", "army_id": 21,
                "scope_role": "active_war_enemy", "war_ids": [88],
                "current_soldiers": 1209, "maximum_soldiers": 1320,
                "ai_base_power_raw": 3_512_500_000,
            },
        ]
        unsafe_original = _route_contact_row(
            1, army_id=11, origin=8747, target=46,
            date_raw=date_raw, route=[23, 46],
            hostile_ids=(21,), contact_free=False,
        )
        base = {
            "player": player, "enemies": [enemy], "score": -28,
            "date_raw": date_raw, "objective": 46,
            "player_side": "defender", "army_strengths": strength_rows,
            "army_strengths_status": "available",
            "route_contact_horizon_supported": True,
            "negative_reuse_expires_date_raw": date_raw + 24,
            "objective_states": [_objective_state(46)],
            "occupation_supported": True,
        }
        query = _native_war_plan(
            **base, history=[unsafe_original],
            steps=("query-campaign-root-context-v1", "life-advance"),
        )
        self.assertEqual(query["phase"], "native_war_capital_regroup_context", query)
        self.assertEqual(query["selected_step"], "query-campaign-root-context-v1")

        root = _campaign_root_row(
            2, date_raw=date_raw, capital_province_id=45,
            held_county_capital_province_ids=(45, 46),
        )
        preview = _native_war_plan(
            **base, history=[unsafe_original, root],
            steps=("preview-move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(preview["phase"], "native_war_capital_regroup_preview", preview)
        self.assertEqual(preview["selected_step"], "preview-move-army-11-to-45")

        unowned_root = _campaign_root_row(
            2, date_raw=date_raw, capital_province_id=45,
            held_county_capital_province_ids=(46,),
        )
        no_ownership = _native_war_plan(
            **base, history=[unsafe_original, unowned_root],
            steps=("preview-move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(
            no_ownership["phase"],
            "native_war_defender_capital_regroup_ownership_blocked",
        )
        self.assertIsNone(no_ownership["selected_step"])

        capital_route = _preview_row(
            3, army_id=11, origin=8747, target=45,
            date_raw=date_raw, route=[23, 45],
        )
        contact_step = query_route_contact_horizon_step(11, 45, (21,))
        contact = _native_war_plan(
            **base, history=[unsafe_original, root, capital_route],
            steps=(contact_step, "life-advance"),
        )
        self.assertEqual(
            contact["phase"], "native_war_capital_regroup_contact_horizon",
            contact,
        )
        self.assertEqual(contact["selected_step"], contact_step)

        safe_capital = _route_contact_row(
            4, army_id=11, origin=8747, target=45,
            date_raw=date_raw, route=[23, 45],
            hostile_ids=(21,), contact_free=True,
        )
        reroute = _native_war_plan(
            **base,
            history=[unsafe_original, root, capital_route, safe_capital],
            steps=("move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(reroute["selected_step"], "move-army-11-to-45", reroute)
        self.assertEqual(reroute["pursuit"]["objective_kind"], "regroup")

        unsafe_capital = _route_contact_row(
            4, army_id=11, origin=8747, target=45,
            date_raw=date_raw, route=[23, 45],
            hostile_ids=(21,), contact_free=False,
        )
        blocked = _native_war_plan(
            **base,
            history=[unsafe_original, root, capital_route, unsafe_capital],
            steps=("move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(blocked["phase"], "native_war_no_safe_exact_route", blocked)
        self.assertIsNone(blocked["selected_step"])

        geometrically_clear = _preview_row(
            3, army_id=11, origin=8747, target=45,
            date_raw=date_raw, route=[47, 45],
        )
        still_queries = _native_war_plan(
            **base, history=[unsafe_original, root, geometrically_clear],
            steps=(contact_step, "move-army-11-to-45"),
        )
        self.assertEqual(
            still_queries["phase"],
            "native_war_capital_regroup_contact_horizon",
            still_queries,
        )
        unsafe_clear_route = _route_contact_row(
            4, army_id=11, origin=8747, target=45,
            date_raw=date_raw, route=[47, 45],
            hostile_ids=(21,), contact_free=False,
        )
        still_blocked = _native_war_plan(
            **base,
            history=[unsafe_original, root, geometrically_clear,
                     unsafe_clear_route],
            steps=("move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(
            still_blocked["phase"], "native_war_no_safe_exact_route",
            still_blocked,
        )

    def test_r0118_overmatched_enemy_at_exact_objective_rejects_one_day_free(
        self,
    ) -> None:
        date_raw = 53_370_552
        player = _army(
            419_430_662, soldiers=354, province_id=1684,
            controllable=True, army_state="regular", route_province_ids=[],
            in_combat=False, retreating=False,
        )
        enemy = _army(
            419_430_684, soldiers=759, province_id=45,
            controllable=False, army_state="sieging", route_province_ids=[],
            in_combat=False, retreating=False,
        )
        route = [699, 700, 714, 975, 715, 45]
        strengths = [
            {
                "status": "available", "army_id": 419_430_662,
                "scope_role": "player", "war_ids": [88],
                "current_soldiers": 354, "maximum_soldiers": 842,
                "ai_base_power_raw": 1_068_500_000,
            },
            {
                "status": "available", "army_id": 419_430_684,
                "scope_role": "active_war_enemy", "war_ids": [88],
                "current_soldiers": 759, "maximum_soldiers": 765,
                "ai_base_power_raw": 2_075_900_000,
            },
        ]
        history = [
            _campaign_root_row(
                1, date_raw=date_raw, capital_province_id=45,
                held_county_capital_province_ids=(45,),
            ),
            _preview_row(
                2, army_id=419_430_662, origin=1684, target=45,
                date_raw=date_raw, route=route,
            ),
            _route_contact_row(
                3, army_id=419_430_662, origin=1684, target=45,
                date_raw=date_raw, route=route,
                hostile_ids=(419_430_684,), contact_free=True,
            ),
        ]
        plan = _native_war_plan(
            player=player, enemies=[enemy], player_side="defender",
            score=0, date_raw=date_raw, objective=45,
            objective_states=[
                _objective_state(
                    45, fort_level=3, garrison_size=400,
                    besieging_strength=759,
                    active_siege=_active_siege(
                        army_id=419_430_684, player=False, days_left=296,
                    ),
                ),
            ],
            occupation_supported=True,
            negative_reuse_expires_date_raw=date_raw + 24,
            route_contact_horizon_supported=True,
            army_strengths=strengths, army_strengths_status="available",
            history=history,
            steps=("move-army-419430662-to-45", "life-advance"),
        )
        self.assertNotEqual(plan.get("selected_step"), "move-army-419430662-to-45")
        self.assertEqual(
            plan["phase"], "native_war_no_safe_route_defensive_hold_progress", plan,
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["route_rejections"][0]["one_day_contact_horizon_rejected"],
            "hostile_operational_overmatch_enemy_current_on_exact_route",
        )
        balanced = _native_war_plan(
            player=player, enemies=[enemy], player_side="defender",
            score=0, date_raw=date_raw, objective=45,
            objective_states=[_objective_state(45)],
            occupation_supported=True,
            negative_reuse_expires_date_raw=date_raw + 24,
            route_contact_horizon_supported=True,
            army_strengths=[
                {**strengths[0], "current_soldiers": 900,
                 "ai_base_power_raw": 2_500_000_000},
                strengths[1],
            ],
            army_strengths_status="available", history=history,
            steps=("move-army-419430662-to-45", "life-advance"),
        )
        self.assertIn(
            {
                "kind": "enemy_current_on_route",
                "enemy_army_id": 419_430_684,
                "province_id": 45,
            },
            _audit_war_route(
                route, origin_province_id=1684,
                target_province_id=45, enemies=[enemy],
            )["conflicts"],
        )
        # 900/759 is below the old relief ratio. A one-day-free contact
        # horizon covers only the first of six hops. Province 45 remains
        # the observed hostile siege at this route's endpoint.
        self.assertIsNone(balanced["selected_step"])
        self.assertEqual(
            balanced["phase"], "native_war_siege_forecast_observation_blocked"
        )
        self.assertIn(
            "query-combat-simulation-inputs-v3-45-715-a-1-419430662",
            balanced["required_observation"],
        )

    def test_outnumbered_armies_consolidate_strongest_idle_stack_first(
        self,
    ) -> None:
        armies = [
            _army(
                army_id,
                soldiers=soldiers,
                province_id=20,
                controllable=True,
                army_state="regular",
                route_province_ids=[],
            )
            for army_id, soldiers in ((51, 1_209), (79, 250), (80, 250), (81, 250))
        ]
        strengths = [
            {
                "status": "available",
                "army_id": army_id,
                "scope_role": "player",
                "war_ids": [7],
                "current_soldiers": soldiers,
            }
            for army_id, soldiers in ((51, 1_209), (79, 250), (80, 250), (81, 250))
        ]

        result = _preoffensive_army_consolidation(
            {"paused": True, "army_strengths": strengths},
            controlled_armies=armies,
            war_id=7,
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["destination_army_id"], 51)
        self.assertEqual(result["source_army_id"], 79)
        self.assertEqual(result["step"], "merge-armies-51-with-79")

        enemy = _army(
            65,
            soldiers=3_000,
            province_id=99,
            controllable=False,
            army_state="regular",
            route_province_ids=[],
        )
        full_strengths = [
            *[
                {
                    "status": "available",
                    "army_id": row["army_id"],
                    "scope_role": "player",
                    "war_ids": [88],
                    "current_soldiers": row["soldiers"],
                    "maximum_soldiers": row["soldiers"],
                    "ai_base_power_raw": int(row["soldiers"]) * 100_000,
                }
                for row in armies
            ],
            {
                "status": "available",
                "army_id": 65,
                "scope_role": "active_war_enemy",
                "war_ids": [88],
                "current_soldiers": 3_000,
                "maximum_soldiers": 3_000,
                "ai_base_power_raw": 300_000_000,
            },
        ]
        plan = _native_war_plan(
            player=armies[0],
            players=armies,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=(
                QUERY_ARMY_STRENGTHS_STEP,
                "merge-armies-51-with-79",
                "preview-move-army-51-to-2585",
                "life-advance",
            ),
            army_strengths=full_strengths,
            army_strengths_status="available",
        )
        self.assertEqual(
            plan["phase"], "native_war_preoffensive_army_consolidation"
        )
        self.assertEqual(plan["selected_step"], "merge-armies-51-with-79")

    def test_generic_merge_ack_fences_resubmit_and_time_advance(self) -> None:
        armies = [
            _army(
                army_id,
                soldiers=soldiers,
                province_id=20,
                controllable=True,
                army_state="regular",
                route_province_ids=[],
            )
            for army_id, soldiers in ((51, 1_209), (79, 250))
        ]
        history = [
            {
                "index": 9,
                "command": "merge-armies-51-with-79",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "merge_submitted",
                        "destination_army_id": 51,
                        "source_army_id": 79,
                        "submitted_date_raw": 24_000,
                        "player_army_ids_before": [51, 79],
                    }
                },
            }
        ]

        plan = _native_war_plan(
            player=armies[0],
            players=armies,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=history,
            objective=2585,
            steps=("merge-armies-51-with-79", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_merge_result_pending")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["merge_result_lifecycle"]["status"],
            "pending_same_frame",
        )
        self.assertEqual(
            plan["merge_result_lifecycle"]["history_index"], 1
        )

        duplicate_history = [
            history[0],
            {
                "index": 10,
                "command": "merge-armies-51-with-79",
                "ok": False,
                "error": (
                    "UnsupportedStepError: native DLL does not implement "
                    "gameplay step merge-armies-51-with-79"
                ),
            },
            {
                "index": 11,
                "command": "merge-armies-51-with-79",
                "ok": False,
                "error": (
                    "UnsupportedStepError: repeated pre-send capability "
                    "rejection for merge-armies-51-with-79"
                ),
            },
        ]
        duplicate = _native_war_plan(
            player=armies[0],
            players=armies,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=duplicate_history,
            objective=2585,
            steps=("merge-armies-51-with-79", "life-advance"),
        )
        lifecycle = duplicate["merge_result_lifecycle"]
        self.assertEqual(duplicate["phase"], "native_war_merge_result_pending")
        self.assertIsNone(duplicate["selected_step"])
        self.assertEqual(lifecycle["status"], "pending_same_frame")
        self.assertEqual(lifecycle["history_index"], 1)
        self.assertEqual(
            lifecycle["duplicate_attempt"]["status"], "submission_failed"
        )
        self.assertEqual(len(lifecycle["duplicate_attempts"]), 2)

    def test_generic_merge_receipt_before_restore_does_not_poison_branch(
        self,
    ) -> None:
        armies = [
            _army(
                army_id,
                soldiers=soldiers,
                province_id=20,
                controllable=True,
                army_state="regular",
                route_province_ids=[],
            )
            for army_id, soldiers in ((51, 1_209), (79, 250))
        ]
        history = [
            {
                "index": 1,
                "command": "merge-armies-51-with-79",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "merge_submitted",
                        "destination_army_id": 51,
                        "source_army_id": 79,
                        "submitted_date_raw": 23_999,
                        "player_army_ids_before": [51, 79],
                    }
                },
            },
            {
                "index": 2,
                "command": "restore-checkpoint",
                "ok": True,
                "result": {"status": "restored"},
            },
        ]
        strengths = [
            {
                "status": "available",
                "army_id": army_id,
                "scope_role": "player",
                "war_ids": [88],
                "current_soldiers": soldiers,
                "maximum_soldiers": soldiers,
                "ai_base_power_raw": soldiers * 100_000,
            }
            for army_id, soldiers in ((51, 1_209), (79, 250))
        ]

        plan = _native_war_plan(
            player=armies[0],
            players=armies,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=history,
            objective=2585,
            steps=(
                QUERY_ARMY_STRENGTHS_STEP,
                "merge-armies-51-with-79",
                "life-advance",
            ),
            army_strengths=strengths,
            army_strengths_status="available",
        )

        self.assertNotEqual(plan["phase"], "native_war_merge_result_pending")

    def test_consumed_merge_receipt_stays_closed_after_future_army_changes(
        self,
    ) -> None:
        current_armies = [
            _army(
                901,
                soldiers=1_500,
                province_id=31,
                controllable=True,
                army_state="regular",
                route_province_ids=[],
            )
        ]
        history = [
            {
                "index": 1,
                "command": "merge-armies-51-with-79",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "merge_applied",
                        "destination_army_id": 51,
                        "source_army_id": 79,
                        "submitted_date_raw": 23_900,
                        "submitted_snapshot_id": "native:40",
                        "submitted_public_revision": 40,
                        "submitted_native_revision": 40,
                        "submitted_episode_run_id": "native-707-old-war",
                        "destination_owner_character_id": 707,
                        "destination_province_id": 20,
                        "source_owner_character_id": 707,
                        "source_province_id": 20,
                        "player_army_ids_before": [51, 79],
                        "postcondition_verified": True,
                        "source_army_id_absent": True,
                        "player_army_ids_after": [51],
                        "observed_snapshot_id": "native:41",
                        "observed_public_revision": 41,
                        "observed_native_revision": 41,
                        "observed_date_raw": 23_900,
                        "observed_episode_run_id": "native-707-old-war",
                    }
                },
            }
        ]

        plan = _native_war_plan(
            player=current_armies[0],
            players=current_armies,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=history,
            objective=2585,
            steps=("life-advance",),
        )

        self.assertNotEqual(plan["phase"], "native_war_merge_result_pending")

    def test_route_audit_preserves_a_later_return_to_physical_origin(
        self,
    ) -> None:
        enemy = _army(
            21,
            soldiers=800,
            province_id=90,
            controllable=False,
            move_target_province_id=99,
            army_state="moving",
            route_province_ids=[52, 8759, 99],
        )

        audit = _audit_war_route(
            [2602, 8759, 2604],
            origin_province_id=8759,
            target_province_id=2604,
            enemies=[enemy],
        )

        self.assertEqual(audit["status"], "unsafe")
        self.assertEqual(
            audit["route_province_ids"], [2602, 8759, 2604]
        )
        self.assertIn(
            {
                "kind": "enemy_route_intersection",
                "enemy_army_id": 21,
                "province_id": 8759,
                "player_hop": 2,
                "enemy_hop": 2,
            },
            audit["conflicts"],
        )

    def test_route_audit_strips_only_the_enemy_leading_current_province(
        self,
    ) -> None:
        enemy = _army(
            21,
            soldiers=800,
            province_id=90,
            controllable=False,
            move_target_province_id=99,
            army_state="moving",
            route_province_ids=[90, 52, 90, 99],
        )

        audit = _audit_war_route(
            [31, 90],
            origin_province_id=20,
            target_province_id=90,
            enemies=[enemy],
        )

        self.assertEqual(audit["status"], "unsafe")
        self.assertIn(
            {
                "kind": "enemy_route_intersection",
                "enemy_army_id": 21,
                "province_id": 90,
                "player_hop": 2,
                "enemy_hop": 2,
            },
            audit["conflicts"],
        )

    def test_decorated_auto_turn_preview_is_fresh_from_root_result(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        direct = _preview_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
        )
        decorated = {
            **direct,
            "command": "auto-turn",
            "result": {
                **direct["result"],
                "requested_step": "auto-turn",
                "auto_turn": {
                    "selected_step": "preview-move-army-11-to-2585"
                },
            },
        }

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=[decorated],
            objective=2585,
            steps=(
                "preview-move-army-11-to-2585",
                "move-army-11-to-2585",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_exact_route_rejects_only_observable_convergence_kinds(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        cases = {
            "enemy_current_on_route": _army(
                21, soldiers=800, province_id=31, controllable=False
            ),
            "enemy_target_on_route": _army(
                21,
                soldiers=800,
                province_id=90,
                controllable=False,
                move_target_province_id=31,
                army_state="moving",
            ),
            "shared_next_hop": _army(
                21,
                soldiers=800,
                province_id=90,
                controllable=False,
                move_target_province_id=99,
                army_state="moving",
                route_province_ids=[31, 99],
            ),
            "enemy_route_intersection": _army(
                21,
                soldiers=800,
                province_id=90,
                controllable=False,
                move_target_province_id=99,
                army_state="moving",
                route_province_ids=[52, 31, 99],
            ),
        }
        for conflict_kind, enemy in cases.items():
            with self.subTest(conflict_kind=conflict_kind):
                plan = _native_war_plan(
                    player=player,
                    enemies=[enemy],
                    score=0,
                    date_raw=24_000,
                    history=[
                        _preview_row(
                            1,
                            origin=20,
                            target=2585,
                            date_raw=24_000,
                            route=[20, 31, 2585],
                        )
                    ],
                    objectives=[2585, 2510],
                    steps=(
                        "move-army-11-to-2585",
                        "preview-move-army-11-to-2510",
                        "move-army-11-to-2510",
                        "life-advance",
                    ),
                )
                self.assertEqual(
                    plan["selected_step"],
                    "preview-move-army-11-to-2510",
                )
                self.assertEqual(
                    plan["route_rejections"][0]["conflicts"][0]["kind"],
                    conflict_kind,
                )

    def test_exact_route_rejects_opposite_enemy_edge(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=90,
            controllable=False,
            move_target_province_id=99,
            army_state="moving",
            route_province_ids=[52, 31, 99],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 52, 2585],
                )
            ],
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        kinds = {
            conflict["kind"]
            for conflict in plan["route_rejections"][0]["conflicts"]
        }
        self.assertIn("enemy_route_intersection", kinds)
        self.assertIn("opposite_edge_intersection", kinds)

    def test_exact_route_ignores_retreating_enemy(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        retreating = _army(
            21,
            soldiers=800,
            province_id=31,
            controllable=False,
            move_target_province_id=2585,
            army_state="retreating",
            route_province_ids=[31, 2585],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[retreating],
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 2585],
                )
            ],
            objective=2585,
            steps=(
                "preview-move-army-11-to-2585",
                "move-army-11-to-2585",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_passive_route_rejects_enemy_at_nonobjective_destination(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=31,
            army_state="moving",
            route_province_ids=[20, 52, 31],
        )
        target_enemy = _army(
            21, soldiers=800, province_id=31, controllable=False
        )
        safe = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            steps=("life-advance",),
        )
        self.assertEqual(
            safe["phase"],
            "native_war_active_route_contact_horizon_unsupported",
        )
        self.assertIsNone(safe["selected_step"])

        destination_blocked = _native_war_plan(
            player=player,
            enemies=[target_enemy],
            score=0,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=31,
                    date_raw=24_000,
                    route=[20, 52, 31],
                    hostile_ids=(21,),
                    contact_free=False,
                )
            ],
            steps=("life-advance",),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            destination_blocked["phase"], "native_war_no_safe_exact_route"
        )
        self.assertIsNone(destination_blocked["selected_step"])

        intermediate_enemy = _army(
            22, soldiers=700, province_id=52, controllable=False
        )
        blocked = _native_war_plan(
            player=player,
            enemies=[target_enemy, intermediate_enemy],
            score=0,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=31,
                    date_raw=24_000,
                    route=[20, 52, 31],
                    hostile_ids=(21, 22),
                    contact_free=False,
                )
            ],
            steps=("life-advance",),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(blocked["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(blocked["selected_step"])

    def test_all_exact_routes_unsafe_never_uses_fallback_or_advances(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemies = [
            _army(21, soldiers=800, province_id=31, controllable=False),
            _army(22, soldiers=700, province_id=52, controllable=False),
        ]
        plan = _native_war_plan(
            player=player,
            enemies=enemies,
            score=0,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                ),
                _preview_row(
                    2,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[52, 2510],
                ),
            ],
            objectives=[2585, 2510],
            fallback=2543,
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2510",
                "move-army-11-to-2543",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "safe-exact-war-route")

    def test_r767_de_jure_route_exhaustion_selects_one_native_surrender(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemies = [
            _army(21, soldiers=800, province_id=31, controllable=False),
            _army(22, soldiers=700, province_id=52, controllable=False),
        ]
        options = _termination_options(
            score=-44, war_duration_days=216
        )
        options["active_casus_belli_identity"] = {
            "database_index": 17,
            "canonical_key": "individual_county_de_jure_cb",
        }
        options.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )

        plan = _native_war_plan(
            player=player,
            enemies=enemies,
            score=-44,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                ),
                _preview_row(
                    2,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[52, 2510],
                ),
            ],
            objectives=[2585, 2510],
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2510",
                "surrender-war-88",
                "life-advance",
            ),
            termination_options=[options],
        )

        self.assertEqual(
            plan["phase"], "native_war_de_jure_no_safe_route_surrender"
        )
        self.assertEqual(plan["selected_step"], "surrender-war-88")
        self.assertEqual(
            plan["decision"]["selected_outcome"], "surrender"
        )
        self.assertFalse(
            plan["decision"]["candidates"]["continue"]["executable"]
        )
        self.assertFalse(
            plan["decision"]["candidates"]["white_peace"]["legal"]
        )
        self.assertTrue(
            plan["decision"]["candidates"]["surrender"]["legal"]
        )

    def test_terminal_minus_one_hundred_submits_explicit_defeat_receipt(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            move_target_province_id=52,
            army_state="moving",
            route_province_ids=[52],
        )
        options = _termination_options(score=-100, war_duration_days=329)
        options["active_casus_belli_identity"] = {
            "database_index": 40,
            "canonical_key": "minor_religious_war",
        }
        options.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=-100,
            date_raw=24_000,
            objective=52,
            steps=("surrender-war-88", "life-advance"),
            termination_options=[options],
        )

        self.assertEqual(plan["phase"], "native_war_terminal_score_surrender")
        self.assertEqual(plan["selected_step"], "surrender-war-88")
        self.assertEqual(
            plan["decision"]["policy"],
            "terminal-score-defeat-receipt-v1",
        )

    def test_r851_negative_score_insufficient_siege_selects_surrender(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=52,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemies = [
            _army(
                21,
                soldiers=None,
                province_id=45,
                controllable=False,
                army_state="sieging",
                route_province_ids=[],
            ),
            _army(
                22,
                soldiers=None,
                province_id=45,
                controllable=False,
                army_state="sieging",
                route_province_ids=[],
            ),
        ]
        options = _termination_options(score=-9, war_duration_days=266)
        options["active_casus_belli_identity"] = {
            "database_index": 17,
            "canonical_key": "individual_county_de_jure_cb",
        }
        options.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )

        plan = _native_war_plan(
            player=player,
            enemies=enemies,
            score=-9,
            date_raw=53_157_360,
            objectives=[52],
            objective_states=[
                _objective_state(
                    52,
                    garrison_size=400,
                    besieging_strength=396,
                    active_siege=_active_siege(
                        siege_id=6, army_id=11, days_left=None
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            targeted_title_ids=[537],
            steps=("surrender-war-88", "life-advance"),
            termination_options=[options],
        )

        self.assertEqual(
            plan["phase"], "native_war_de_jure_no_safe_route_surrender"
        )
        self.assertEqual(plan["selected_step"], "surrender-war-88")
        self.assertEqual(plan["decision"]["selected_outcome"], "surrender")
        self.assertFalse(
            plan["decision"]["candidates"]["continue"]["executable"]
        )
        self.assertFalse(
            plan["decision"]["candidates"]["white_peace"]["legal"]
        )
        self.assertTrue(
            plan["decision"]["candidates"]["surrender"]["executable"]
        )
        self.assertEqual(
            plan["route_rejections"],
            [
                {
                    "target_province_id": 52,
                    "status": "current_exact_siege_rejected",
                    "siege_status": "insufficient_strength",
                }
            ],
        )

    def test_r794_de_jure_route_exhaustion_prefers_white_peace(self) -> None:
        player = _army(
            11,
            soldiers=396,
            province_id=52,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=400,
            province_id=54,
            controllable=False,
            move_target_province_id=52,
            army_state="moving",
            route_province_ids=[16, 52],
        )
        options = _de_jure_white_peace_options()
        options.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=47,
            date_raw=53_150_016,
            objectives=[52],
            objective_states=[
                _objective_state(
                    52,
                    garrison_size=400,
                    besieging_strength=396,
                    active_siege=_active_siege(
                        siege_id=6, army_id=11, days_left=None
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            targeted_title_ids=[537],
            steps=(
                "offer-white-peace-88",
                "surrender-war-88",
                "life-advance",
            ),
            termination_options=[options],
        )

        self.assertEqual(
            plan["phase"], "native_war_de_jure_no_safe_route_white_peace"
        )
        self.assertEqual(plan["selected_step"], "offer-white-peace-88")
        self.assertEqual(plan["decision"]["selected_outcome"], "white_peace")
        self.assertFalse(
            plan["decision"]["candidates"]["continue"]["executable"]
        )
        self.assertTrue(
            plan["decision"]["candidates"]["white_peace"]["executable"]
        )
        self.assertTrue(
            plan["decision"]["candidates"]["surrender"]["executable"]
        )

    def test_r796_no_safe_route_observes_one_white_peace_reply_window(
        self,
    ) -> None:
        submitted_date_raw = 53_150_016
        player = _army(
            11,
            soldiers=396,
            province_id=52,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=400,
            province_id=54,
            controllable=False,
            move_target_province_id=52,
            army_state="moving",
            route_province_ids=[16, 52],
        )
        history = [
            {
                "index": 267,
                "command": "offer-white-peace-88",
                "ok": True,
                "result": {
                    "war_termination_result": {
                        "status": "submitted_pending",
                        "war_id": 88,
                        "outcome": "white_peace",
                        "episode_run_id": None,
                        "submitted_date_raw": submitted_date_raw,
                    }
                },
            }
        ]

        for elapsed_raw in (24, 9 * 24):
            with self.subTest(elapsed_raw=elapsed_raw):
                plan = _native_war_plan(
                    player=player,
                    enemies=[enemy],
                    score=47,
                    date_raw=submitted_date_raw + elapsed_raw,
                    history=history,
                    objectives=[52],
                    objective_states=[
                        _objective_state(
                            52,
                            garrison_size=400,
                            besieging_strength=396,
                            active_siege=_active_siege(
                                siege_id=6, army_id=11, days_left=None
                            ),
                        )
                    ],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    targeted_title_ids=[537],
                    steps=("offer-white-peace-88", "life-advance"),
                )
                self.assertEqual(
                    plan["phase"],
                    "native_war_white_peace_response_window_advance",
                )
                self.assertEqual(plan["selected_step"], "life-advance")

        expired = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=47,
            date_raw=submitted_date_raw + 10 * 24,
            history=history,
            objectives=[52],
            objective_states=[
                _objective_state(
                    52,
                    garrison_size=400,
                    besieging_strength=396,
                    active_siege=_active_siege(
                        siege_id=6, army_id=11, days_left=None
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            targeted_title_ids=[537],
            steps=("offer-white-peace-88", "life-advance"),
        )

        self.assertEqual(
            expired["phase"],
            "native_war_white_peace_postcondition_unresolved",
        )
        self.assertIsNone(expired["selected_step"])
        self.assertEqual(expired["required_step"], "old-WarID-disappearance")

    def test_r794_de_jure_white_peace_rejects_nonexact_inputs(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemies = [
            _army(21, soldiers=800, province_id=31, controllable=False),
            _army(22, soldiers=700, province_id=52, controllable=False),
        ]
        base = _de_jure_white_peace_options()
        base.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        mutations = {
            "zero_score": lambda row: row.update(
                {"player_relative_war_score": 0}
            ),
            "wrong_cb_index": lambda row: row[
                "active_casus_belli_identity"
            ].update({"database_index": 18}),
            "unknown_acceptance": lambda row: row["options"][
                "white_peace"
            ].update({"ai_acceptance_observable": False}),
            "nonpositive_acceptance": lambda row: row["options"][
                "white_peace"
            ]["ai_acceptance"].update({"raw": 0}),
            "recipient_rejects": lambda row: row["options"]["white_peace"][
                "recipient_response"
            ].update({"would_accept_now": False}),
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                options = copy.deepcopy(base)
                mutate(options)
                score = int(options["player_relative_war_score"])
                plan = _native_war_plan(
                    player=player,
                    enemies=enemies,
                    score=score,
                    date_raw=24_000,
                    history=[
                        _preview_row(
                            1,
                            origin=20,
                            target=2585,
                            date_raw=24_000,
                            route=[31, 2585],
                        ),
                        _preview_row(
                            2,
                            origin=20,
                            target=2510,
                            date_raw=24_000,
                            route=[52, 2510],
                        ),
                    ],
                    objectives=[2585, 2510],
                    targeted_title_ids=[537],
                    steps=(
                        "offer-white-peace-88",
                        "surrender-war-88",
                        "life-advance",
                    ),
                    termination_options=[options],
                )
                self.assertEqual(plan["phase"], "native_war_no_safe_exact_route")
                self.assertIsNone(plan["selected_step"])

        multi_target = _native_war_plan(
            player=player,
            enemies=enemies,
            score=47,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                ),
                _preview_row(
                    2,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[52, 2510],
                ),
            ],
            objectives=[2585, 2510],
            targeted_title_ids=[537, 538],
            steps=("offer-white-peace-88", "life-advance"),
            termination_options=[copy.deepcopy(base)],
        )
        self.assertEqual(
            multi_target["phase"], "native_war_no_safe_exact_route"
        )
        self.assertIsNone(multi_target["selected_step"])

    def test_r794_de_jure_positive_query_bypasses_negative_lease(self) -> None:
        queried = _termination_reuse_snapshot()
        queried["active_wars"][0]["player_relative_war_score"] = 47
        queried["active_wars"][0]["targeted_title_ids"] = [537]
        options = _de_jure_white_peace_options()
        history = [_termination_query_row(1, queried, options=options)]
        current = _termination_reuse_snapshot(
            date_raw=int(queried["date_raw"]) + 6 * 24,
            wars=copy.deepcopy(queried["active_wars"]),
            history=history,
        )

        plan = choose_one_life_turn(
            history,
            snapshot=current,
            action_steps=(
                "query-war-termination-options-88",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_termination_query")
        self.assertEqual(
            plan["selected_step"], "query-war-termination-options-88"
        )

    def test_r794_de_jure_white_peace_does_not_override_safe_route(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        options = _de_jure_white_peace_options()
        options.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=47,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[30, 2585],
                )
            ],
            objectives=[2585],
            targeted_title_ids=[537],
            steps=(
                "move-army-11-to-2585",
                "offer-white-peace-88",
                "life-advance",
            ),
            termination_options=[options],
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertNotEqual(
            plan["phase"], "native_war_de_jure_no_safe_route_white_peace"
        )

    def test_intersecting_candidate_requires_then_consumes_contact_horizon(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        preview = _preview_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
        )
        query_step = (
            "query-route-contact-horizon-v1-11-to-2585-h-1-21"
        )
        required = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[preview],
            objective=2585,
            steps=(query_step, "move-army-11-to-2585", "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(required["phase"], "native_war_candidate_contact_horizon")
        self.assertEqual(required["selected_step"], query_step)

        proven = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                preview,
                _route_contact_row(
                    2,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                    hostile_ids=(21,),
                    contact_free=True,
                ),
            ],
            objective=2585,
            steps=(query_step, "move-army-11-to-2585", "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(proven["selected_step"], "move-army-11-to-2585")
        self.assertEqual(
            proven["pursuit"]["route_audit"]["status"],
            "safe_one_day_contact_horizon",
        )

        unavailable = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                preview,
                {
                    "index": 2,
                    "command": query_step,
                    "ok": False,
                    "error": "CK3 route arrival timeline is unavailable",
                },
            ],
            objective=2585,
            steps=(query_step, "move-army-11-to-2585", "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertNotEqual(unavailable.get("selected_step"), query_step)
        self.assertIn("contact_timeline_unavailable", str(unavailable))

    def test_intersecting_active_route_advances_only_with_fresh_horizon(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        query_step = (
            "query-route-contact-horizon-v1-11-to-2585-h-1-21"
        )
        advance_step = advance_route_contact_horizon_step(11, 2585, (21,))
        required = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            steps=(query_step, advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(required["phase"], "native_war_route_contact_horizon")
        self.assertEqual(required["selected_step"], query_step)

        proven = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                    hostile_ids=(21,),
                    contact_free=True,
                )
            ],
            steps=(query_step, advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            proven["phase"], "native_war_route_contact_horizon_progress"
        )
        self.assertEqual(proven["selected_step"], advance_step)

        unavailable = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                {
                    "index": 1,
                    "command": query_step,
                    "ok": False,
                    "error": "CK3 route arrival timeline is unavailable",
                }
            ],
            steps=(query_step, advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertNotEqual(unavailable.get("selected_step"), query_step)
        self.assertEqual(
            unavailable.get("phase"),
            "native_war_active_route_contact_horizon_unavailable",
        )
        self.assertIsNone(unavailable.get("selected_step"))

    def test_committed_route_requires_fresh_daily_horizon_even_when_sentinel_live(
        self,
    ) -> None:
        date_raw = 53_256_000
        player = _army(
            201_326_874,
            soldiers=4_100,
            province_id=8_753,
            controllable=True,
            move_target_province_id=2_635,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2_626, 2_627, 2_633, 2_634, 2_635],
        )
        enemy = _army(
            167_772_577,
            soldiers=3_300,
            province_id=8_648,
            controllable=False,
            move_target_province_id=2_635,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[1_034, 2_644, 2_645, 2_635],
        )
        query_step = query_route_contact_horizon_step(
            201_326_874, 2_635, (167_772_577,)
        )
        advance_step = advance_route_contact_horizon_step(
            201_326_874, 2_635, (167_772_577,)
        )
        steps = (
            COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
            query_step,
            advance_step,
            "life-advance",
        )
        readiness = {
            "decision_sentinel_live_ready": True,
            "committed_route_sentinel_live_ready": True,
            "committed_route_sentinel_speed_5_live_ready": True,
            "noncombat_sentinel_timeline_speed": 5,
            "terminal_sentinel_live_ready": False,
            "overwhelming_matrix_live_ready": False,
        }

        required = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness=readiness,
        )
        self.assertEqual(
            required["phase"], "native_war_route_contact_horizon"
        )
        self.assertEqual(required["selected_step"], query_step)
        self.assertFalse(
            str(required["selected_step"]).startswith(
                "committed-route-sentinel-advance"
            )
        )

        proof = _route_contact_row(
            1,
            army_id=201_326_874,
            origin=8_753,
            target=2_635,
            date_raw=date_raw,
            route=[2_626, 2_627, 2_633, 2_634, 2_635],
            hostile_ids=(167_772_577,),
            contact_free=True,
        )
        proven = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            history=[proof],
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness=readiness,
        )
        self.assertEqual(
            proven["phase"], "native_war_route_contact_horizon_progress"
        )
        self.assertEqual(proven["selected_step"], advance_step)

        next_frame = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw + 24,
            history=[
                proof,
                {
                    "index": 2,
                    "command": advance_step,
                    "ok": True,
                    "result": {"step": advance_step, "elapsed_days": 1},
                },
            ],
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness=readiness,
        )
        self.assertEqual(
            next_frame["phase"], "native_war_route_contact_horizon"
        )
        self.assertEqual(next_frame["selected_step"], query_step)

    def test_geometrically_safe_committed_route_still_requires_fresh_horizon(
        self,
    ) -> None:
        date_raw = 53_256_000
        player = _army(
            201_326_874,
            soldiers=4_100,
            province_id=8_753,
            controllable=True,
            move_target_province_id=2_635,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2_626, 2_627, 2_635],
        )
        enemy = _army(
            167_772_577,
            soldiers=3_300,
            province_id=99,
            controllable=False,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        query_step = query_route_contact_horizon_step(
            201_326_874, 2_635, (167_772_577,)
        )
        advance_step = advance_route_contact_horizon_step(
            201_326_874, 2_635, (167_772_577,)
        )
        steps = (
            COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
            query_step,
            advance_step,
            "life-advance",
        )
        required = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "committed_route_sentinel_live_ready": True,
            },
        )
        self.assertEqual(required["route_audit"]["status"], "safe")
        self.assertEqual(required["selected_step"], query_step)

        proven = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            history=[
                _route_contact_row(
                    1,
                    army_id=201_326_874,
                    origin=8_753,
                    target=2_635,
                    date_raw=date_raw,
                    route=[2_626, 2_627, 2_635],
                    hostile_ids=(167_772_577,),
                    contact_free=True,
                )
            ],
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "committed_route_sentinel_live_ready": True,
            },
        )
        self.assertEqual(proven["selected_step"], advance_step)
        self.assertEqual(
            proven["phase"], "native_war_route_contact_horizon_progress"
        )

    def test_committed_route_contact_blocks_even_above_two_to_one_base_power(
        self,
    ) -> None:
        date_raw = 53_215_920
        player = _army(
            83_886_367,
            soldiers=2_327,
            province_id=2_610,
            controllable=True,
            move_target_province_id=2_628,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2_628],
        )
        enemy = _army(
            50_331_920,
            soldiers=1_000,
            province_id=2_628,
            controllable=False,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        query_step = query_route_contact_horizon_step(
            83_886_367, 2_628, (50_331_920,)
        )
        advance_step = advance_route_contact_horizon_step(
            83_886_367, 2_628, (50_331_920,)
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            history=[
                _route_contact_row(
                    1,
                    army_id=83_886_367,
                    origin=2_610,
                    target=2_628,
                    date_raw=date_raw,
                    route=[2_628],
                    hostile_ids=(50_331_920,),
                    contact_free=False,
                )
            ],
            steps=(
                COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
                query_step,
                advance_step,
                "life-advance",
            ),
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "committed_route_sentinel_live_ready": True,
            },
            army_strengths=[
                {
                    "status": "available",
                    "army_id": 83_886_367,
                    "scope_role": "player",
                    "war_ids": [88],
                    "current_soldiers": 2_327,
                    "maximum_soldiers": 2_461,
                    "ai_base_power_raw": 10_000_000_000,
                },
                {
                    "status": "available",
                    "army_id": 50_331_920,
                    "scope_role": "active_war_enemy",
                    "war_ids": [88],
                    "current_soldiers": 1_000,
                    "maximum_soldiers": 1_100,
                    "ai_base_power_raw": 4_000_000_000,
                },
            ],
            army_strengths_status="available",
        )

        self.assertEqual(
            plan["phase"], "native_war_no_safe_exact_route"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_step"],
            "safe-exact-war-route",
        )
        self.assertEqual(
            plan["route_rejections"][0]["contact_policy"],
            "blocked_without_qualified_combat_permission",
        )
        balance = plan["active_wars"][0]["army_strength_balance"]
        self.assertFalse(balance["hostile_operational_overmatch"])
        self.assertEqual(
            balance["interpretation"],
            "operational_routing_risk_not_battle_win_odds",
        )

    def test_embarked_committed_route_uses_same_daily_proof_gate(
        self,
    ) -> None:
        date_raw = 53_218_080
        route = [1_038, 1_037, 8_658, 1_017, 942, 1_111, 5_715]
        player = _army(
            150_995_107,
            soldiers=4_100,
            province_id=8_652,
            controllable=True,
            move_target_province_id=5_715,
            army_state="embarked",
            army_state_code=4,
            in_combat=False,
            retreating=False,
            route_province_ids=route,
        )
        enemy = _army(
            83_886_281,
            soldiers=3_300,
            province_id=5_935,
            controllable=False,
            move_target_province_id=2_619,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[5_910, 945, 946, 2_619],
        )
        query_step = query_route_contact_horizon_step(
            150_995_107, 5_715, (83_886_281,)
        )
        advance_step = advance_route_contact_horizon_step(
            150_995_107, 5_715, (83_886_281,)
        )
        steps = (
            COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
            query_step,
            advance_step,
            "life-advance",
        )
        required = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=-37,
            date_raw=date_raw,
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "committed_route_sentinel_live_ready": True,
            },
        )
        self.assertEqual(required["selected_step"], query_step)

        proven = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=-37,
            date_raw=date_raw,
            history=[
                _route_contact_row(
                    1,
                    army_id=150_995_107,
                    origin=8_652,
                    target=5_715,
                    date_raw=date_raw,
                    route=route,
                    hostile_ids=(83_886_281,),
                    contact_free=True,
                )
            ],
            steps=steps,
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "committed_route_sentinel_live_ready": True,
            },
        )
        self.assertEqual(proven["selected_step"], advance_step)
        self.assertEqual(
            proven["phase"], "native_war_route_contact_horizon_progress"
        )

    def test_stationary_objective_hold_production_replaces_same_baseline_step(
        self,
    ) -> None:
        date_raw = 53_256_000
        player = _army(
            201_326_874,
            soldiers=4_100,
            province_id=2_635,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        target_date_raw = date_raw + 7 * 24
        other_war_without_objective_states = _war(
            war_id=77,
            allied_armies=[player],
            enemy_armies=[],
            score=10,
            player_is_primary_war_leader=False,
            war_objective_province_ids=[2_631],
            objective_province_states=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            additional_wars=[other_war_without_objective_states],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=(
                WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
                "life-advance",
            ),
            battle_speed_readiness={
                "decision_sentinel_live_ready": True,
                "committed_route_sentinel_live_ready": True,
                "stationary_objective_hold_sentinel_live_ready": True,
                "terminal_sentinel_live_ready": True,
                "overwhelming_matrix_live_ready": False,
            },
        )

        self.assertEqual(
            plan["phase"],
            "native_war_stationary_objective_hold_sentinel",
        )
        self.assertEqual(
            plan["selected_step"],
            war_objective_hold_sentinel_advance_step(
                88, 201_326_874, 2_635, target_date_raw
            ),
        )
        self.assertEqual(plan["sentinel_scope"], "stationary_objective_hold")
        self.assertEqual(plan["timeline_speed"], 3)
        self.assertEqual(
            plan["baseline_decision"],
            {
                "phase": "native_war_pursuit_progress",
                "selected_step": "life-advance",
                "war_id": 88,
                "subject_army_id": 201_326_874,
                "objective_province_id": 2_635,
            },
        )
        self.assertEqual(plan["pursuit"]["war_id"], 88)
        self.assertEqual(plan["pursuit"]["target_province_id"], 2_635)
        self.assertEqual(plan["watch_army_ids"], [201_326_874])
        self.assertFalse(plan["exact_war_terminal_watch"])
        self.assertFalse(plan["exact_active_war_set_watch"])
        self.assertEqual(plan["maximum_omitted_state_detection_lag_days"], 7)

        default_closed = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            additional_wars=[other_war_without_objective_states],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=(
                WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
                "life-advance",
            ),
            battle_speed_readiness={
                "decision_sentinel_live_ready": True,
                "committed_route_sentinel_live_ready": True,
                "stationary_objective_hold_sentinel_live_ready": False,
                "stationary_objective_hold_sentinel_canary_ready": False,
                "terminal_sentinel_live_ready": True,
                "overwhelming_matrix_live_ready": False,
            },
        )
        self.assertNotEqual(
            default_closed["phase"],
            "native_war_stationary_objective_hold_sentinel",
        )
        self.assertNotEqual(
            default_closed.get("selected_step"),
            war_objective_hold_sentinel_advance_step(
                88, 201_326_874, 2_635, target_date_raw
            ),
        )
        self.assertEqual(default_closed["phase"], "native_war_pursuit_progress")
        self.assertEqual(default_closed["selected_step"], "life-advance")
        self.assertEqual(default_closed["pursuit"]["war_id"], 88)
        self.assertEqual(
            default_closed["pursuit"]["target_province_id"], 2_635
        )

    def test_stationary_hold_cannot_intercept_another_tactical_war(self) -> None:
        date_raw = 53_256_000
        player = _army(
            501,
            soldiers=4_100,
            province_id=2_635,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        preferred_lower_war = _war(
            war_id=77,
            allied_armies=[player],
            enemy_armies=[],
            score=10,
            war_objective_province_ids=[2_631],
            objective_province_states=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            additional_wars=[preferred_lower_war],
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness={
                "stationary_objective_hold_sentinel_live_ready": True,
            },
        )

        self.assertNotEqual(
            plan["phase"], "native_war_stationary_objective_hold_sentinel"
        )
        self.assertFalse(
            str(plan.get("selected_step", "")).startswith(
                "war-objective-hold-sentinel-advance-"
            )
        )
        self.assertEqual(plan["phase"], "native_war_route_preview_unsupported")
        self.assertIn("2631", str(plan["required_step"]))

    def test_r0160_primary_defender_requires_forecast_for_overmatched_siege(
        self,
    ) -> None:
        date_raw = 53_184_000
        player = _army(
            83_886_367,
            soldiers=None,
            province_id=2_638,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy_95 = _army(
            50_331_863,
            soldiers=None,
            province_id=2_635,
            controllable=False,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy_16777250 = _army(
            83_886_252,
            soldiers=None,
            province_id=2_627,
            controllable=False,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        war_95 = _war(
            war_id=95,
            allied_armies=[player],
            enemy_armies=[enemy_95],
            score=9,
            player_side="defender",
            player_is_primary_war_leader=True,
            war_objective_province_ids=[2_638],
        )
        strengths = [
            _army_strength(
                83_886_367,
                "player",
                [16_777_250, 95],
                current=2_329,
                maximum=2_461,
                base_power_raw=7_578_100_000,
            ),
            _army_strength(
                83_886_252,
                "active_war_enemy",
                [16_777_250],
                current=565,
                maximum=585,
                base_power_raw=1_283_600_000,
            ),
            _army_strength(
                50_331_863,
                "active_war_enemy",
                [95],
                current=267,
                maximum=371,
                base_power_raw=1_140_800_000,
            ),
        ]

        def options(war_id: int, score: int) -> dict[str, object]:
            result = _termination_options(war_id=war_id, score=score)
            result.update(
                {
                    "player_side": "defender",
                    "player_is_primary_war_leader": True,
                    "queried_snapshot_id": "session:90",
                    "queried_revision": 90,
                    "queried_native_revision": 90,
                    "queried_connection_generation": 1,
                    "episode_run_id": None,
                }
            )
            return result

        base = {
            "player": player,
            "enemies": [enemy_16777250],
            "score": 10,
            "date_raw": date_raw,
            "war_id": 16_777_250,
            "objective": 2_638,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
            "additional_wars": [war_95],
            "termination_options": [options(16_777_250, 10), options(95, 9)],
            "army_strengths": strengths,
            "army_strengths_status": "available",
            "route_contact_horizon_supported": True,
            "battle_speed_readiness": {
                "stationary_objective_hold_sentinel_live_ready": True,
            },
        }
        preview_step = "preview-move-army-83886367-to-2635"
        contact_step = query_route_contact_horizon_step(
            83_886_367, 2_635, (50_331_863, 83_886_252)
        )
        move_step = "move-army-83886367-to-2635"

        preview = _native_war_plan(
            **base,
            steps=(
                preview_step,
                WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
                "life-advance",
            ),
        )
        self.assertEqual(preview["phase"], "native_war_siege_forecast_route_preview")
        self.assertEqual(preview["selected_step"], preview_step)
        self.assertNotIn("hold-sentinel", preview["selected_step"])

        preview_row = _preview_row(
            1,
            army_id=83_886_367,
            origin=2_638,
            target=2_635,
            date_raw=date_raw,
            route=[2_636, 2_635],
        )
        contact = _native_war_plan(
            **base,
            history=[preview_row],
            steps=(contact_step, move_step, "life-advance"),
        )
        self.assertEqual(contact["phase"], "native_war_siege_forecast_contact_query")
        self.assertEqual(contact["selected_step"], contact_step)

        unsafe_contact_row = _route_contact_row(
            2,
            army_id=83_886_367,
            origin=2_638,
            target=2_635,
            date_raw=date_raw,
            route=[2_636, 2_635],
            hostile_ids=(50_331_863, 83_886_252),
            contact_free=False,
        )
        unsafe = _native_war_plan(
            **base,
            history=[preview_row, unsafe_contact_row],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(unsafe["phase"], "native_war_siege_forecast_observation_blocked")
        self.assertIsNone(unsafe["selected_step"])

        contact_row = _route_contact_row(
            2,
            army_id=83_886_367,
            origin=2_638,
            target=2_635,
            date_raw=date_raw,
            route=[2_636, 2_635],
            hostile_ids=(50_331_863, 83_886_252),
            contact_free=True,
        )
        move = _native_war_plan(
            **base,
            history=[preview_row, contact_row],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(move["phase"], "native_war_siege_forecast_observation_blocked")
        self.assertIsNone(move["selected_step"])
        self.assertEqual(move["required_observation"],
                         query_combat_simulation_inputs_v3_step(
                             2_635, 2_636, [83_886_367], [50_331_863]
                         ))
        self.assertEqual(move["siege_relief"]["candidate_count"], 2)
        self.assertEqual(move["siege_relief"]["war_id"], 95)

        # After War 95's siege completes, the same army is assigned once to
        # the remaining War 16777250 siege instead of resuming the hold.
        war_95_regular = copy.deepcopy(war_95)
        war_95_regular["enemy_armies"] = [
            {**enemy_95, "army_state": "regular", "army_state_code": 1}
        ]
        second = _native_war_plan(
            **{
                **base,
                "additional_wars": [war_95_regular],
                "steps": ("preview-move-army-83886367-to-2627", "life-advance"),
            }
        )
        self.assertEqual(second["phase"], "native_war_siege_forecast_route_preview")
        self.assertEqual(
            second["selected_step"], "preview-move-army-83886367-to-2627"
        )

    def test_r0160_siege_relief_missing_strength_blocks_hold_advance(self) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2_638,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21,
            soldiers=None,
            province_id=2_635,
            controllable=False,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=9,
            date_raw=53_184_000,
            objective=2_638,
            player_side="defender",
            player_is_primary_war_leader=True,
            army_strengths_status="available",
            army_strengths=[],
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness={
                "stationary_objective_hold_sentinel_live_ready": True,
            },
        )

        self.assertEqual(
            plan["phase"],
            "native_war_defender_siege_relief_observation_blocked",
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_observation"],
            "complete-same-frame-siege-position-and-war-strength",
        )

    def test_r0161_active_and_r0162_arrived_relief_use_existing_progress(
        self,
    ) -> None:
        date_raw = 53_189_208
        army_id = 83_886_367
        target = 2_627
        route = [2_643, 2_639, 2_633, target]
        moving = _army(
            army_id,
            soldiers=None,
            province_id=2_638,
            controllable=True,
            move_target_province_id=target,
            move_target_observable=True,
            army_state="moving",
            army_state_code=7,
            route_province_ids=route,
            in_combat=False,
            retreating=False,
        )
        siege_enemy = _army(
            50_331_863,
            soldiers=None,
            province_id=target,
            controllable=False,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        other_enemy = _army(
            83_886_252,
            soldiers=None,
            province_id=2_617,
            controllable=False,
            move_target_province_id=2_619,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2_618, 2_619],
            in_combat=False,
            retreating=False,
        )
        other_war = _war(
            war_id=16_777_250,
            allied_armies=[moving],
            enemy_armies=[other_enemy],
            score=-11,
            player_side="defender",
            player_is_primary_war_leader=True,
            war_objective_province_ids=[2_638],
        )
        strengths = [
            _army_strength(
                army_id,
                "player",
                [16_777_250, 95],
                current=2_345,
                maximum=2_461,
                base_power_raw=7_610_100_000,
            ),
            _army_strength(
                83_886_252,
                "active_war_enemy",
                [16_777_250],
                current=577,
                maximum=585,
                base_power_raw=1_314_000_000,
            ),
            _army_strength(
                50_331_863,
                "active_war_enemy",
                [95],
                current=320,
                maximum=371,
                base_power_raw=1_258_000_000,
            ),
        ]

        def options(war_id: int, score: int) -> dict[str, object]:
            result = _termination_options(war_id=war_id, score=score)
            result.update(
                {
                    "player_side": "defender",
                    "player_is_primary_war_leader": True,
                    "queried_snapshot_id": "session:90",
                    "queried_revision": 90,
                    "queried_native_revision": 90,
                    "queried_connection_generation": 1,
                    "episode_run_id": None,
                }
            )
            return result

        preview = _preview_row(
            1,
            army_id=army_id,
            origin=2_638,
            target=target,
            date_raw=date_raw,
            route=route,
        )
        stale_contact = _route_contact_row(
            2,
            army_id=army_id,
            origin=2_638,
            target=target,
            date_raw=date_raw,
            route=route,
            hostile_ids=(50_331_863, 83_886_252),
            contact_free=True,
        )
        stale_contact["result"]["queried_native_revision"] = 89
        move_step = f"move-army-{army_id}-to-{target}"
        move = {
            "index": 3,
            "command": move_step,
            "ok": True,
            "result": {
                "accepted": True,
                "status": "submitted",
                "war_action": {
                    "status": "moving",
                    "army_id": army_id,
                    "target_province_id": target,
                    "submitted_date_raw": date_raw,
                },
                "player_armies": [copy.deepcopy(moving)],
            },
        }
        persisted_checkpoint = {
            "index": 4,
            "command": "save-checkpoint",
            "ok": True,
            "result": {
                "status": "submitted",
                "checkpoint": {
                    "history_index": 5,
                    "date_raw": date_raw,
                    "sha256": "a" * 64,
                },
            },
        }
        cold_restore = {
            "index": 5,
            "command": "restore-checkpoint",
            "ok": True,
            "result": {
                "status": "restored",
                "source": "native-session-cold-start",
                "checkpoint": {
                    "history_index": 5,
                    "date_raw": date_raw,
                    "sha256": "a" * 64,
                },
            },
        }
        query_step = query_route_contact_horizon_step(
            army_id, target, (50_331_863, 83_886_252)
        )
        advance_step = advance_route_contact_horizon_step(
            army_id, target, (50_331_863, 83_886_252)
        )
        base = {
            "player": moving,
            "enemies": [siege_enemy],
            "score": -12,
            "date_raw": date_raw,
            "war_id": 95,
            "objective": 2_638,
            "player_side": "defender",
            "player_is_primary_war_leader": True,
            "additional_wars": [other_war],
            "termination_options": [options(95, -12), options(16_777_250, -11)],
            "army_strengths": strengths,
            "army_strengths_status": "available",
            "route_contact_horizon_supported": True,
        }

        query = _native_war_plan(
            **base,
            history=[preview, stale_contact, move],
            steps=(query_step, advance_step, move_step, "life-advance"),
        )
        self.assertEqual(
            query["phase"], "native_war_route_contact_horizon"
        )
        self.assertEqual(query["selected_step"], query_step)
        self.assertNotEqual(query["selected_step"], move_step)

        fresh_contact = _route_contact_row(
            4,
            army_id=army_id,
            origin=2_638,
            target=target,
            date_raw=date_raw,
            route=route,
            hostile_ids=(50_331_863, 83_886_252),
            contact_free=True,
        )
        progress = _native_war_plan(
            **base,
            history=[preview, stale_contact, move, fresh_contact],
            steps=(query_step, advance_step, move_step, "life-advance"),
        )
        self.assertEqual(
            progress["phase"], "native_war_route_contact_horizon_progress"
        )
        self.assertEqual(progress["selected_step"], advance_step)
        self.assertEqual(progress["move_intent"]["status"], "active")
        self.assertNotEqual(progress["selected_step"], move_step)

        restored_progress = _native_war_plan(
            **base,
            history=[
                preview,
                stale_contact,
                move,
                persisted_checkpoint,
                cold_restore,
            ],
            steps=(query_step, advance_step, move_step, "life-advance"),
        )
        self.assertNotEqual(restored_progress["selected_step"], move_step)
        self.assertNotEqual(
            restored_progress["phase"],
            "native_war_defender_siege_relief_observation_blocked",
        )

        unknown = _native_war_plan(
            **base,
            history=[preview, stale_contact],
            steps=(query_step, advance_step, move_step, "life-advance"),
        )
        self.assertEqual(
            unknown["phase"],
            "native_war_defender_siege_relief_observation_blocked",
        )
        self.assertIsNone(unknown["selected_step"])
        self.assertEqual(
            unknown["required_observation"],
            "complete-matching-active-native-move-intent-route",
        )

        missing_route = _native_war_plan(
            **{
                **base,
                "player": {**moving, "route_province_ids": []},
            },
            history=[preview, stale_contact, move],
            steps=(query_step, advance_step, move_step, "life-advance"),
        )
        self.assertEqual(
            missing_route["phase"], "native_war_route_evidence_blocked"
        )
        self.assertIsNone(missing_route["selected_step"])

        arrived = _army(
            army_id,
            soldiers=None,
            province_id=target,
            controllable=True,
            move_target_province_id=None,
            move_target_observable=True,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        departed_enemy = _army(
            50_331_863,
            soldiers=None,
            province_id=2_626,
            controllable=False,
            move_target_province_id=8_753,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[8_753],
            in_combat=False,
            retreating=False,
        )
        concurrent_siege = _army(
            83_886_252,
            soldiers=None,
            province_id=2_619,
            controllable=False,
            move_target_province_id=None,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        arrival_other_war = _war(
            war_id=16_777_250,
            allied_armies=[arrived],
            enemy_armies=[concurrent_siege],
            score=-8,
            player_side="defender",
            player_is_primary_war_leader=True,
            war_objective_province_ids=[2_638],
        )
        arrival_base = {
            **base,
            "player": arrived,
            "enemies": [departed_enemy],
            "score": -9,
            "additional_wars": [arrival_other_war],
        }
        arrived_progress = _native_war_plan(
            **arrival_base,
            history=[preview, stale_contact, move],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(
            arrived_progress["phase"], "native_war_siege_progress"
        )
        self.assertEqual(arrived_progress["selected_step"], "life-advance")

        restored_arrival_progress = _native_war_plan(
            **arrival_base,
            history=[
                preview,
                stale_contact,
                move,
                persisted_checkpoint,
                cold_restore,
            ],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(
            restored_arrival_progress["phase"],
            "native_war_siege_progress",
        )
        self.assertEqual(
            restored_arrival_progress["selected_step"], "life-advance"
        )

        second_checkpoint = copy.deepcopy(persisted_checkpoint)
        second_checkpoint["result"]["checkpoint"] = {
            "history_index": 7,
            "date_raw": date_raw,
            "sha256": "b" * 64,
        }
        second_restore = copy.deepcopy(cold_restore)
        second_restore["result"]["checkpoint"] = copy.deepcopy(
            second_checkpoint["result"]["checkpoint"]
        )
        twice_restored = _native_war_plan(
            **arrival_base,
            history=[
                preview,
                stale_contact,
                move,
                persisted_checkpoint,
                cold_restore,
                second_checkpoint,
                second_restore,
            ],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(twice_restored["phase"], "native_war_siege_progress")
        self.assertEqual(twice_restored["selected_step"], "life-advance")

        second_restore["result"]["checkpoint"]["sha256"] = "c" * 64
        unmatched_restore = _native_war_plan(
            **arrival_base,
            history=[
                preview,
                stale_contact,
                move,
                persisted_checkpoint,
                cold_restore,
                second_checkpoint,
                second_restore,
            ],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(
            unmatched_restore["phase"],
            "native_war_defender_siege_relief_observation_blocked",
        )

        arrived_without_move_proof = _native_war_plan(
            **arrival_base,
            history=[preview, stale_contact],
            steps=(move_step, "life-advance"),
        )
        self.assertEqual(
            arrived_without_move_proof["phase"],
            "native_war_defender_siege_relief_observation_blocked",
        )
        self.assertIsNone(arrived_without_move_proof["selected_step"])
        self.assertEqual(
            arrived_without_move_proof["required_observation"],
            "accepted-native-move-arrival-for-current-siege",
        )

    def test_r0176_siege_stance_with_active_route_keeps_typed_move(self) -> None:
        army_id = 83_886_367
        target = 2_638
        route = [8_651, 1_038, 1_036, 8_653, target]
        army = _army(
            army_id,
            soldiers=None,
            province_id=2_619,
            controllable=True,
            move_target_province_id=target,
            move_target_observable=True,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=route,
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            50_331_920,
            soldiers=None,
            province_id=2_604,
            controllable=False,
            move_target_province_id=None,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        war = _war(
            war_id=16_777_231,
            allied_armies=[army],
            enemy_armies=[enemy],
            score=-13,
            player_side="defender",
            player_is_primary_war_leader=True,
        )
        snapshot = {
            "paused": True,
            "map_ready": True,
            "active_event": None,
            "pending_character_interaction": None,
            "date_raw": 53_195_592,
            "player_armies": [army],
        }
        accepted_move = {
            "index": 1_376,
            "command": f"move-army-{army_id}-to-{target}",
            "ok": True,
            "result": {
                "accepted": True,
                "war_action": {
                    "status": "moving",
                    "army_id": army_id,
                    "target_province_id": target,
                    "submitted_date_raw": 53_195_256,
                },
            },
        }

        def relief(
            subject: dict[str, object],
            rows: list[dict[str, object]],
        ) -> dict[str, object]:
            return _primary_defender_siege_relief_assessment(
                {**snapshot, "player_armies": [subject]},
                commands=rows,
                active_wars=[war],
                controlled_armies=[subject],
                pursuit_army=subject,
            )

        active = relief(army, [accepted_move])
        self.assertEqual(active["status"], "active_move_intent")
        self.assertEqual(active["target_province_id"], target)
        self.assertEqual(active["move_intent"]["elapsed_days"], 14)
        self.assertEqual(active["route_province_ids"], route)

        for subject in (
            {**army, "move_target_province_id": None, "route_province_ids": []},
            {**army, "route_province_ids": [8_651, 2_637]},
            {**army, "route_province_ids": []},
        ):
            with self.subTest(subject=subject):
                self.assertEqual(
                    relief(subject, [accepted_move])["status"],
                    "observation_unavailable",
                )
        self.assertEqual(
            relief(army, [])["required_observation"],
            "complete-matching-active-native-move-intent-route",
        )

    def test_r0168_combat_hands_off_only_with_current_exact_battle_frame(
        self,
    ) -> None:
        army = _army(
            83_886_367,
            soldiers=None,
            province_id=2_638,
            controllable=True,
            move_target_province_id=None,
            move_target_observable=True,
            army_state="combat",
            army_state_code=2,
            route_province_ids=[],
            in_combat=True,
            retreating=False,
        )
        siege_enemy = _army(
            83_886_252,
            soldiers=None,
            province_id=2_619,
            controllable=False,
            move_target_province_id=None,
            move_target_observable=True,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        war = _war(
            war_id=16_777_250,
            allied_armies=[army],
            enemy_armies=[siege_enemy],
            score=29,
            player_side="defender",
            player_is_primary_war_leader=True,
        )
        snapshot = {
            "paused": True,
            "map_ready": True,
            "active_event": None,
            "pending_character_interaction": None,
            "date_raw": 53_192_304,
        }
        frame = {
            "status": "available",
            "battle_control_ready": True,
            "subject_public_cunit_id": 83_886_367,
            "province_id": 2_638,
            "observed_date_raw": 53_192_304,
            "combat_id": 738_197_508,
        }

        def relief(
            subject: dict[str, object],
            current_frame: dict[str, object] | None,
        ) -> dict[str, object]:
            return _primary_defender_siege_relief_assessment(
                snapshot,
                commands=[],
                active_wars=[war],
                controlled_armies=[subject],
                pursuit_army=subject,
                battle_control_state=(
                    {"status": "ready", "full_frames": [current_frame]}
                    if current_frame is not None
                    else {"status": "query_required"}
                ),
            )

        exact = relief(army, frame)
        self.assertEqual(exact["status"], "active_combat")
        self.assertEqual(exact["combat_id"], 738_197_508)
        for changed in (
            {**frame, "observed_date_raw": 53_192_280},
            {**frame, "subject_public_cunit_id": 83_886_368},
            {**frame, "province_id": 2_637},
            {**frame, "combat_id": None},
        ):
            with self.subTest(changed=changed):
                self.assertEqual(
                    relief(army, changed)["required_observation"],
                    "same-frame-active-combat-binding",
                )
        self.assertEqual(
            relief(army, None)["required_observation"],
            "same-frame-active-combat-binding",
        )
        noncombat = {**army, "in_combat": False, "army_state": "sieging"}
        self.assertEqual(
            relief(noncombat, frame)["required_observation"],
            "accepted-native-move-arrival-for-current-siege",
        )

    def test_arrived_relief_outlives_travel_window_with_continuous_siege(self) -> None:
        army_id = 83_886_367
        target = 2_627
        date_raw = 53_189_208
        moving = _army(
            army_id,
            soldiers=None,
            province_id=2_638,
            controllable=True,
            move_target_province_id=target,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2_643, target],
            in_combat=False,
            retreating=False,
        )
        arrived = _army(
            army_id,
            soldiers=None,
            province_id=target,
            controllable=True,
            move_target_province_id=None,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )

        def summary(day: int, army: dict[str, object]) -> dict[str, object]:
            return {
                "date_raw": date_raw + day * 24,
                "wars": [{"war_id": 95, "player_armies": [copy.deepcopy(army)]}],
            }

        history: list[dict[str, object]] = [
            {
                "command": f"move-army-{army_id}-to-{target}",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "moving",
                        "army_id": army_id,
                        "target_province_id": target,
                        "submitted_date_raw": date_raw,
                    },
                },
            }
        ]
        for day in range(1, 92):
            history.append(
                {
                    "command": "life-advance",
                    "ok": True,
                    "result": {
                        "war_progress_before": summary(
                            day - 1, moving if day == 1 else arrived
                        ),
                        "war_progress_after": summary(day, arrived),
                    },
                }
            )
            if day in {1, 91}:
                checkpoint = {
                    "history_index": len(history) + 1,
                    "date_raw": date_raw + day * 24,
                    "sha256": ("a" if day == 1 else "b") * 64,
                }
                history.extend(
                    [
                        {
                            "command": "save-checkpoint",
                            "ok": True,
                            "result": {"checkpoint": copy.deepcopy(checkpoint)},
                        },
                        {
                            "command": "restore-checkpoint",
                            "ok": True,
                            "result": {
                                "status": "restored",
                                "source": "native-session-cold-start",
                                "checkpoint": copy.deepcopy(checkpoint),
                            },
                        },
                    ]
                )
        snapshot = {
            "date_raw": date_raw + 91 * 24,
            "player_armies": [arrived],
        }
        arrival = _accepted_native_move_arrival(
            history, snapshot, army_id=army_id, target_province_id=target
        )
        self.assertIsNotNone(arrival)
        self.assertEqual(arrival["elapsed_days"], 91)

        broken = copy.deepcopy(history)
        broken[46]["result"]["war_progress_after"]["wars"][0][
            "player_armies"
        ][0]["current_province_id"] = 2_628
        self.assertIsNone(
            _accepted_native_move_arrival(
                broken, snapshot, army_id=army_id, target_province_id=target
            )
        )

    def test_r0169_arrival_after_target_combat_requires_contiguous_progress(
        self,
    ) -> None:
        army_id = 83_886_367
        target = 2_619
        date_raw = 53_192_544
        moving = _army(
            army_id,
            soldiers=None,
            province_id=2_638,
            controllable=True,
            move_target_province_id=target,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2_643, target],
            in_combat=False,
            retreating=False,
        )
        approach = {**moving, "current_province_id": 2_624}
        combat = _army(
            army_id,
            soldiers=None,
            province_id=target,
            controllable=True,
            move_target_province_id=None,
            army_state="combat",
            army_state_code=2,
            route_province_ids=[],
            in_combat=True,
            retreating=False,
        )
        siege = {
            **combat,
            "army_state": "sieging",
            "army_state_code": 3,
            "in_combat": False,
        }

        def summary(day: int, army: dict[str, object]) -> dict[str, object]:
            return {
                "date_raw": date_raw + day * 24,
                "wars": [
                    {"war_id": 16_777_250, "player_armies": [copy.deepcopy(army)]}
                ],
            }

        def progress(
            command: str,
            start_day: int,
            end_day: int,
            before: dict[str, object],
            after: dict[str, object],
        ) -> dict[str, object]:
            return {
                "command": command,
                "ok": True,
                "result": {
                    "war_progress_before": summary(start_day, before),
                    "war_progress_after": summary(end_day, after),
                },
            }

        history = [
            {
                "command": f"move-army-{army_id}-to-{target}",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "moving",
                        "army_id": army_id,
                        "target_province_id": target,
                        "submitted_date_raw": date_raw,
                    },
                },
            },
            progress("committed-route-sentinel-advance", 0, 88, moving, approach),
            progress("committed-route-sentinel-advance", 88, 89, approach, combat),
            progress("battle-decision-epoch-advance", 89, 96, combat, siege),
        ]
        snapshot = {
            "date_raw": date_raw + 96 * 24,
            "player_armies": [siege],
        }
        arrival = _accepted_native_move_arrival(
            history, snapshot, army_id=army_id, target_province_id=target
        )
        self.assertIsNotNone(arrival)
        self.assertEqual(arrival["elapsed_days"], 96)

        for row_index, key, value in (
            (2, "current_province_id", 2_618),
            (2, "in_combat", False),
            (3, "current_province_id", 2_618),
            (3, "army_state", "regular"),
        ):
            with self.subTest(row_index=row_index, key=key):
                broken = copy.deepcopy(history)
                broken[row_index]["result"]["war_progress_after"]["wars"][0][
                    "player_armies"
                ][0][key] = value
                self.assertIsNone(
                    _accepted_native_move_arrival(
                        broken,
                        snapshot,
                        army_id=army_id,
                        target_province_id=target,
                    )
                )

        gap = copy.deepcopy(history)
        gap[3]["result"]["war_progress_before"]["date_raw"] += 24
        self.assertIsNone(
            _accepted_native_move_arrival(
                gap, snapshot, army_id=army_id, target_province_id=target
            )
        )
        self.assertIsNone(
            _accepted_native_move_arrival(
                history[:-1],
                snapshot,
                army_id=army_id,
                target_province_id=target,
            )
        )

    def test_r0170_battle_transition_preserves_persisted_move_history(
        self,
    ) -> None:
        army_id = 83_886_367
        target = 2_619
        checkpoint = {
            "history_index": 3,
            "date_raw": 53_194_440,
            "sha256": "a" * 64,
        }
        rows = [
            {
                "command": f"move-army-{army_id}-to-{target}",
                "ok": True,
                "result": {"accepted": True},
            },
            {
                "command": "save-checkpoint",
                "ok": True,
                "result": {"checkpoint": copy.deepcopy(checkpoint)},
            },
            {
                "command": "restore-checkpoint",
                "ok": True,
                "result": {
                    "status": "restored",
                    "source": "native-session-cold-start",
                    "checkpoint": copy.deepcopy(checkpoint),
                },
            },
            {
                "command": f"query-battle-control-snapshot-v1-{army_id}",
                "ok": True,
                "result": {"status": "available"},
            },
            {
                "command": "battle-decision-epoch-advance-to-53195016",
                "ok": True,
                "result": {},
            },
        ]
        siege = _army(
            army_id,
            soldiers=None,
            province_id=target,
            controllable=True,
            move_target_province_id=None,
            army_state="sieging",
            army_state_code=3,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        frame_record = {
            "position": 1,
            "subject_army_id": army_id,
            "frame": {
                "combat_id": 872_415_232,
                "snapshot_revision": 13,
                "phase": "maneuver",
                "phase_day": 1,
            },
        }
        with (
            mock.patch(
                "xar_autoplayer.strategy._current_battle_control_frames",
                return_value=({}, [frame_record]),
            ),
            mock.patch(
                "xar_autoplayer.strategy._battle_sentinel_advance_validation",
                return_value=None,
            ),
        ):
            state = _battle_control_turn_state(
                rows, {"paused": True, "player_armies": [siege]}, [siege]
            )

        self.assertEqual(state["status"], "transition_recognized")
        remaining = state["remaining_rows"]
        self.assertEqual(
            [row["command"] for row in remaining],
            [row["command"] for row in rows if row is not rows[3]],
        )
        self.assertEqual(
            len(
                [
                    row
                    for row in remaining
                    if row["command"] == f"move-army-{army_id}-to-{target}"
                ]
            ),
            1,
        )
        self.assertIsNotNone(
            _latest_accepted_native_move_row(remaining, army_id=army_id)
        )

        invalid_restore = copy.deepcopy(remaining)
        invalid_restore[2]["result"]["checkpoint"]["sha256"] = "b" * 64
        self.assertIsNone(
            _latest_accepted_native_move_row(
                invalid_restore, army_id=army_id
            )
        )

    def test_r0174_same_checkpoint_adjacent_restores_keep_saved_move_only(self) -> None:
        army_id = 83_886_367
        checkpoint = {
            "history_index": 1333,
            "date_raw": 53_194_440,
            "sha256": "2b8933" + "a" * 57,
            "size": 71_839_122,
            "name": "xar_checkpoint.ck3",
            "episode_character_id": 29_829,
            "episode_run_id": "native-29829-fixture",
        }
        rows = [
            {
                "index": 1267,
                "command": f"move-army-{army_id}-to-2619",
                "ok": True,
                "result": {"accepted": True},
            },
            {
                "index": 1333,
                "command": "save-checkpoint",
                "ok": True,
                "result": {"checkpoint": copy.deepcopy(checkpoint)},
            },
        ]
        rows.extend(
            {
                "index": index,
                "command": "restore-checkpoint",
                "ok": True,
                "result": {
                    "status": "restored",
                    "source": "native-session-cold-start",
                    "checkpoint": copy.deepcopy(checkpoint),
                },
            }
            for index in (1334, 1335, 1336)
        )
        self.assertEqual(
            _latest_accepted_native_move_row(rows, army_id=army_id),
            (0, rows[0]),
        )

        for field, replacement in (
            ("history_index", 1334),
            ("date_raw", checkpoint["date_raw"] + 24),
            ("sha256", "b" * 64),
            ("size", checkpoint["size"] + 1),
            ("name", "other.ck3"),
            ("episode_character_id", 29_830),
            ("episode_run_id", "native-other-fixture"),
        ):
            with self.subTest(changed_field=field):
                changed = copy.deepcopy(rows)
                changed[3]["result"]["checkpoint"][field] = replacement
                self.assertIsNone(
                    _latest_accepted_native_move_row(changed, army_id=army_id)
                )
        for intervening in ("life-advance", "save-checkpoint", "query-army-strengths-v1"):
            with self.subTest(intervening=intervening):
                changed = copy.deepcopy(rows)
                changed.insert(3, {"index": 1334, "command": intervening, "ok": True})
                self.assertIsNone(
                    _latest_accepted_native_move_row(changed, army_id=army_id)
                )
        missing_save = copy.deepcopy(rows)
        missing_save[1]["result"]["checkpoint"]["sha256"] = "c" * 64
        self.assertIsNone(
            _latest_accepted_native_move_row(missing_save, army_id=army_id)
        )
        nonofficial = copy.deepcopy(rows)
        nonofficial[3]["result"]["source"] = "same-process-reload"
        self.assertIsNone(
            _latest_accepted_native_move_row(nonofficial, army_id=army_id)
        )

    def test_stationary_hold_never_preempts_full_enforcement(self) -> None:
        date_raw = 53_256_000
        player = _army(
            501,
            soldiers=4_100,
            province_id=2_635,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=100,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            steps=(
                "enforce-demands-88",
                WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP,
                "life-advance",
            ),
            battle_speed_readiness={
                "stationary_objective_hold_sentinel_live_ready": True,
            },
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")

    def test_stationary_speed_five_does_not_inherit_route_live_gate(self) -> None:
        date_raw = 53_256_000
        target_date_raw = date_raw + 7 * 24
        player = _army(
            501,
            soldiers=4_100,
            province_id=2_635,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        readiness = {
            "stationary_objective_hold_sentinel_live_ready": True,
            "noncombat_sentinel_timeline_speed": 5,
            "noncombat_sentinel_high_speed_ab": False,
            "committed_route_sentinel_speed_5_live_ready": True,
            "stationary_objective_hold_sentinel_speed_5_live_ready": False,
        }
        guarded = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness=readiness,
        )
        self.assertEqual(guarded["timeline_speed"], 3)
        self.assertEqual(
            guarded["selected_step"],
            war_objective_hold_sentinel_advance_step(
                88, 501, 2_635, target_date_raw
            ),
        )

        ab_plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness={
                **readiness,
                "noncombat_sentinel_high_speed_ab": True,
            },
        )
        self.assertEqual(ab_plan["timeline_speed"], 5)
        self.assertEqual(
            ab_plan["selected_step"],
            war_objective_hold_sentinel_advance_step(
                88,
                501,
                2_635,
                target_date_raw,
                timeline_speed=5,
            ),
        )
        self.assertTrue(ab_plan["research_high_speed_ab"])

    def test_stationary_objective_hold_respects_existing_query_lease_expiry(
        self,
    ) -> None:
        date_raw = 53_256_000
        player = _army(
            501,
            soldiers=4_100,
            province_id=2_635,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        readiness = {
            "decision_sentinel_live_ready": True,
            "committed_route_sentinel_live_ready": True,
            "stationary_objective_hold_sentinel_live_ready": True,
            "terminal_sentinel_live_ready": True,
            "overwhelming_matrix_live_ready": False,
        }
        age_six_plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            negative_reuse_expires_date_raw=date_raw + 24,
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness=readiness,
        )
        self.assertEqual(
            age_six_plan["selected_step"],
            war_objective_hold_sentinel_advance_step(
                88, 501, 2_635, date_raw + 24
            ),
        )

        later_reuse = {
            **_war(
                war_id=89,
                allied_armies=[player],
                enemy_armies=[],
                score=10,
                war_objective_province_ids=[2_631],
                objective_province_states=[],
            ),
            "war_termination_negative_reuse": {
                "expires_date_raw": date_raw + 5 * 24
            },
        }
        earlier_reuse = {
            **_war(
                war_id=90,
                allied_armies=[player],
                enemy_armies=[],
                score=10,
                war_objective_province_ids=[2_632],
                objective_province_states=[],
            ),
            "war_termination_negative_reuse": {
                "expires_date_raw": date_raw + 2 * 24
            },
        }
        earliest_plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=date_raw,
            objective=2_635,
            objective_states=[],
            negative_reuse_expires_date_raw=date_raw + 6 * 24,
            additional_wars=[later_reuse, earlier_reuse],
            steps=(WAR_OBJECTIVE_HOLD_SENTINEL_ADVANCE_STEP, "life-advance"),
            battle_speed_readiness=readiness,
        )
        self.assertEqual(
            earliest_plan["selected_step"],
            war_objective_hold_sentinel_advance_step(
                88, 501, 2_635, date_raw + 2 * 24
            ),
        )

    def test_contact_horizon_false_never_authorizes_time(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        advance_step = advance_route_contact_horizon_step(11, 2585, (21,))
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                    hostile_ids=(21,),
                    contact_free=False,
                )
            ],
            steps=(advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )

        self.assertNotEqual(plan.get("selected_step"), advance_step)
        self.assertNotEqual(plan.get("selected_step"), "life-advance")

    def test_unqualified_current_province_contact_prefers_safe_reroute(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=31,
            controllable=False,
            move_target_province_id=20,
            army_state="moving",
            route_province_ids=[20],
        )
        advance_step = advance_route_contact_horizon_step(11, 2585, (21,))
        proof = _route_contact_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
            hostile_ids=(21,),
            contact_free=False,
        )
        horizon = proof["result"]["route_contact_horizon"]
        horizon["subject_route"]["arrival_date_raws"] = [24_264, 24_312]
        horizon["conflicts"][0]["province_id"] = 20
        horizon["hostile_routes"][0].update(
            {
                "current_province_id": 31,
                "effective_origin_province_id": 20,
                "route_province_ids": [20],
                "arrival_date_raws": [24_024],
            }
        )

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[proof],
            objectives=[2585, 2510],
            steps=(
                advance_step,
                "preview-move-army-11-to-2510",
                "life-advance",
            ),
            route_contact_horizon_supported=True,
        )

        self.assertEqual(plan["phase"], "native_war_route_preview")
        self.assertEqual(
            plan["selected_step"], "preview-move-army-11-to-2510"
        )
        self.assertNotEqual(plan["selected_step"], advance_step)
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_moving_sibling_requires_own_fresh_contact_horizon(
        self,
    ) -> None:
        primary = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        secondary = _army(
            12,
            soldiers=700,
            province_id=22,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        advance_step = advance_route_contact_horizon_step(11, 2585, (21,))
        sibling_query = query_route_contact_horizon_step(
            12, 2585, (21,)
        )
        sibling_advance = advance_route_contact_horizon_step(
            12, 2585, (21,)
        )
        primary_proof = _route_contact_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
            hostile_ids=(21,),
            contact_free=True,
        )
        plan = _native_war_plan(
            player=primary,
            players=[primary, secondary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[primary_proof],
            steps=(sibling_query, advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )

        self.assertEqual(
            plan["phase"],
            "native_war_sibling_route_contact_horizon",
        )
        self.assertEqual(plan["selected_step"], sibling_query)

        sibling_proof = _route_contact_row(
            2,
            army_id=12,
            origin=22,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
            hostile_ids=(21,),
            contact_free=True,
        )
        proven = _native_war_plan(
            player=primary,
            players=[primary, secondary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[primary_proof, sibling_proof],
            steps=(sibling_query, advance_step, sibling_advance),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            proven["phase"], "native_war_route_contact_horizon_progress"
        )
        self.assertEqual(proven["selected_step"], advance_step)

        unavailable = {
            "index": 2,
            "command": sibling_query,
            "ok": False,
            "error": "fixture route unavailable",
        }
        blocked = _native_war_plan(
            player=primary,
            players=[primary, secondary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[primary_proof, unavailable],
            steps=(sibling_query, advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            blocked["phase"],
            "native_war_sibling_route_contact_horizon_unavailable",
        )
        self.assertIsNone(blocked["selected_step"])

        malformed_success = copy.deepcopy(sibling_proof)
        malformed_success["result"]["route_contact_horizon"][
            "subject_route"
        ]["route_province_ids"] = [32, 2585]
        malformed = _native_war_plan(
            player=primary,
            players=[primary, secondary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[primary_proof, malformed_success],
            steps=(sibling_query, advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            malformed["phase"],
            "native_war_sibling_route_contact_horizon_unavailable",
        )
        self.assertIsNone(malformed["selected_step"])
        self.assertNotEqual(malformed.get("selected_step"), sibling_query)

        unavoidable_proof = _route_contact_row(
            2,
            army_id=12,
            origin=22,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
            hostile_ids=(21,),
            contact_free=False,
        )
        unavoidable_horizon = unavoidable_proof["result"][
            "route_contact_horizon"
        ]
        unavoidable_horizon["subject_route"]["arrival_date_raws"] = [
            24_048,
            24_072,
        ]
        unavoidable_horizon["conflicts"][0]["province_id"] = 22
        unavoidable_horizon["hostile_routes"][0].update(
            {
                "current_province_id": 99,
                "effective_origin_province_id": 22,
                "route_province_ids": [22],
                "arrival_date_raws": [24_024],
            }
        )
        transition = _native_war_plan(
            player=primary,
            players=[primary, secondary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[primary_proof, unavoidable_proof],
            steps=(sibling_query, sibling_advance, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            transition["phase"],
            "native_war_active_route_contact_blocked",
        )
        self.assertIsNone(transition["selected_step"])
        self.assertNotEqual(transition["selected_step"], sibling_advance)
        self.assertNotEqual(transition["selected_step"], advance_step)

    def test_combat_sibling_with_stale_route_is_not_a_moving_conflict(
        self,
    ) -> None:
        primary = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        combat_sibling = _army(
            12,
            soldiers=700,
            province_id=31,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[2585],
            in_combat=True,
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        proof = _route_contact_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
            hostile_ids=(21,),
            contact_free=True,
        )["result"]["route_contact_horizon"]
        snapshot = {
            "date_raw": 24_000,
            "native_revision": 1,
            "snapshot_id": "session:1",
            "revision": 1,
        }

        conjunction = _moving_route_contact_horizon_conjunction(
            [],
            snapshot,
            controlled_armies=[primary, combat_sibling],
            subject_army_id=11,
            subject_contact_horizon=proof,
            hostile_army_ids=(21,),
            enemies=[enemy],
        )

        self.assertEqual(conjunction["conflicting"], [])
        self.assertEqual(conjunction["missing"], [])

    def test_moving_proof_hostile_timelines_cover_stationary_army(
        self,
    ) -> None:
        primary = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[31, 2585],
        )
        stationary = _army(
            12,
            soldiers=700,
            province_id=22,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=99,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[22, 31, 2585],
        )
        advance_step = advance_route_contact_horizon_step(11, 2585, (21,))
        moving_proof = _route_contact_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
            hostile_ids=(21,),
            contact_free=True,
        )
        hostile_route = moving_proof["result"]["route_contact_horizon"][
            "hostile_routes"
        ][0]
        hostile_route.update(
            {
                "effective_origin_province_id": 22,
                "route_province_ids": [22, 31, 2585],
                "arrival_date_raws": [24_048, 24_072, 24_096],
            }
        )
        proven = _native_war_plan(
            player=primary,
            players=[primary, stationary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[moving_proof],
            steps=(advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            proven["phase"], "native_war_route_contact_horizon_progress"
        )
        self.assertEqual(proven["selected_step"], advance_step)
        self.assertEqual(
            [row["army_id"] for row in proven["stationary_contact_horizons"]],
            [12],
        )

        hostile_route["arrival_date_raws"] = [24_024, 24_048, 24_072]
        blocked = _native_war_plan(
            player=primary,
            players=[primary, stationary],
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[moving_proof],
            steps=(advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            blocked["phase"],
            "native_war_route_contact_horizon_global_blocked",
        )
        self.assertIsNone(blocked["selected_step"])

    def test_stationary_objective_uses_own_one_day_contact_horizon(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2619,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2604,
            controllable=False,
            move_target_province_id=2619,
            army_state="moving",
            route_province_ids=[2605, 8757, 2615, 2616, 2617, 2618, 2619],
        )
        query_step = query_route_contact_horizon_step(11, 2619, (21,))
        advance_step = advance_route_contact_horizon_step(11, 2619, (21,))

        query = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objective=2619,
            steps=(query_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            query["phase"], "native_war_stationary_contact_horizon"
        )
        self.assertEqual(query["selected_step"], query_step)

        proof = _route_contact_row(
            1,
            origin=2619,
            target=2619,
            date_raw=24_000,
            route=[],
            hostile_ids=(21,),
            contact_free=True,
        )
        hostile_route = proof["result"]["route_contact_horizon"][
            "hostile_routes"
        ][0]
        hostile_route.update(
            {
                "current_province_id": 2604,
                "effective_origin_province_id": 2605,
                "route_province_ids": [
                    2605,
                    8757,
                    2615,
                    2616,
                    2617,
                    2618,
                    2619,
                ],
                "arrival_date_raws": [
                    24_048,
                    24_072,
                    24_096,
                    24_120,
                    24_144,
                    24_168,
                    24_192,
                ],
            }
        )
        progress = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[proof],
            objective=2619,
            steps=(advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            progress["phase"],
            "native_war_stationary_contact_horizon_progress",
        )
        self.assertEqual(progress["selected_step"], advance_step)
        self.assertEqual(
            progress["route_audit"]["status"],
            "safe_one_day_stationary_contact_horizon",
        )

        conflict_proof = _route_contact_row(
            2,
            origin=2619,
            target=2619,
            date_raw=24_000,
            route=[],
            hostile_ids=(21,),
            contact_free=False,
        )
        contact = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[conflict_proof],
            objective=2619,
            steps=(advance_step, "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            contact["phase"], "native_war_unavoidable_contact_transition"
        )
        self.assertEqual(contact["selected_step"], advance_step)
        self.assertEqual(
            contact["route_audit"]["status"],
            "stationary_current_province_contact",
        )

    def test_blocked_stationary_objective_still_queries_contact_horizon(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=52,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        local_enemy = _army(
            21,
            soldiers=800,
            province_id=52,
            controllable=False,
            army_state="regular",
            route_province_ids=[],
        )
        converging_enemy = _army(
            21,
            soldiers=800,
            province_id=53,
            controllable=False,
            move_target_province_id=52,
            army_state="moving",
            route_province_ids=[52],
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[local_enemy],
                    score=0,
                    objectives=[52],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[converging_enemy],
                    score=-44,
                    objectives=[52],
                ),
            )
        ]
        query_step = query_route_contact_horizon_step(11, 52, (21,))

        plan = _native_war_plan(
            player=player,
            enemies=[converging_enemy],
            score=-44,
            date_raw=24_024,
            history=history,
            objective=52,
            steps=(query_step, "life-advance"),
            route_contact_horizon_supported=True,
        )

        self.assertEqual(plan["phase"], "native_war_stationary_contact_horizon")
        self.assertEqual(plan["selected_step"], query_step)

    def test_route_preview_freshness_uses_date_origin_and_latest_restore(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        fresh = _preview_row(
            1,
            origin=20,
            target=2585,
            date_raw=24_000,
            route=[31, 2585],
        )
        histories = {
            "stale_date": [
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=23_976,
                    route=[31, 2585],
                )
            ],
            "stale_origin": [
                _preview_row(
                    1,
                    origin=19,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                )
            ],
            "pre_restore": [
                fresh,
                {
                    "index": 2,
                    "command": "restore-checkpoint",
                    "ok": True,
                    "result": {"status": "restored"},
                },
            ],
        }
        for stale_kind, history in histories.items():
            with self.subTest(stale_kind=stale_kind):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=0,
                    date_raw=24_000,
                    history=history,
                    objective=2585,
                    steps=(
                        "preview-move-army-11-to-2585",
                        "move-army-11-to-2585",
                    ),
                )
                self.assertEqual(
                    plan["selected_step"],
                    "preview-move-army-11-to-2585",
                )

    def test_gathering_or_same_date_deferred_preview_advances_once(self) -> None:
        gathering = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="gathering",
            route_province_ids=[],
        )
        gathering_plan = _native_war_plan(
            player=gathering,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
        )
        self.assertEqual(
            gathering_plan["phase"], "native_war_gathering_progress"
        )
        self.assertEqual(gathering_plan["selected_step"], "life-advance")

        regular = {**gathering, "army_state": "regular"}
        deferred = {
            "index": 1,
            "command": "preview-move-army-11-to-2585",
            "ok": True,
            "result": {
                "accepted": False,
                "status": "deferred",
                "route_preview": {
                    "status": "deferred",
                    "reason": "army_not_move_ready",
                    "army_id": 11,
                    "origin_province_id": 20,
                    "target_province_id": 2585,
                    "route_province_ids": [],
                    "previewed_date_raw": 24_000,
                },
            },
        }
        same_date = _native_war_plan(
            player=regular,
            enemies=[],
            score=0,
            date_raw=24_000,
            history=[deferred],
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
        )
        self.assertEqual(
            same_date["phase"], "native_war_route_preview_deferred"
        )
        self.assertEqual(same_date["selected_step"], "life-advance")

        next_date = _native_war_plan(
            player=regular,
            enemies=[],
            score=0,
            date_raw=24_024,
            history=[deferred],
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
        )
        self.assertEqual(
            next_date["selected_step"],
            "preview-move-army-11-to-2585",
        )

    def test_passive_route_is_reaudited_before_every_advance(self) -> None:
        safe_player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 31, 2585],
        )
        safe = _native_war_plan(
            player=safe_player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=("life-advance",),
        )
        self.assertEqual(
            safe["phase"],
            "native_war_active_route_contact_horizon_unsupported",
        )
        self.assertIsNone(safe["selected_step"])

        enemy = _army(21, soldiers=800, province_id=31, controllable=False)
        reroute = _native_war_plan(
            player=safe_player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 2585],
                    hostile_ids=(21,),
                    contact_free=False,
                )
            ],
            objectives=[2585, 2510],
            steps=(
                "preview-move-army-11-to-2510",
                "move-army-11-to-2510",
                "life-advance",
            ),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(reroute["phase"], "native_war_route_preview")
        self.assertEqual(
            reroute["selected_step"], "preview-move-army-11-to-2510"
        )
        self.assertNotEqual(reroute["selected_step"], "life-advance")

    def test_sieging_army_with_unsafe_active_route_reroutes_first(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="sieging",
            route_province_ids=[20, 31, 2585],
        )
        enemy = _army(21, soldiers=800, province_id=31, controllable=False)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 2585],
                    hostile_ids=(21,),
                    contact_free=False,
                )
            ],
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
            route_contact_horizon_supported=True,
        )

        self.assertEqual(plan["phase"], "native_war_route_preview")
        self.assertEqual(
            plan["selected_step"], "preview-move-army-11-to-2510"
        )

    def test_stationary_siege_threat_previews_next_exact_before_advance(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2585,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        approaching_enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[2596, 2585],
        )

        reroute = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(reroute["phase"], "native_war_route_preview")
        self.assertEqual(
            reroute["selected_step"], "preview-move-army-11-to-2510"
        )
        self.assertNotEqual(reroute["selected_step"], "life-advance")

        blocked = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            steps=("life-advance",),
            move_route_preview_supported=False,
        )
        self.assertEqual(blocked["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(blocked["selected_step"])

        deferred = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            history=[
                {
                    "index": 1,
                    "command": "preview-move-army-11-to-2510",
                    "ok": True,
                    "result": {
                        "route_preview": {
                            "status": "deferred",
                            "army_id": 11,
                            "origin_province_id": 2585,
                            "target_province_id": 2510,
                            "previewed_date_raw": 24_000,
                        }
                    },
                }
            ],
            objectives=[2585, 2510],
            steps=("life-advance",),
        )
        self.assertEqual(
            deferred["phase"],
            "native_war_move_readiness_observation_required",
        )
        self.assertIsNone(deferred["selected_step"])
        self.assertEqual(
            deferred["required_step"], "query-native-army-move-readiness"
        )
        self.assertEqual(len(deferred["route_rejections"]), 2)
        self.assertEqual(
            deferred["route_rejections"][-1]["target_province_id"], 2510
        )

    def test_production_shape_187_objectives_stops_after_first_safe_preview(
        self,
    ) -> None:
        player = _army(
            33_554_797,
            soldiers=900,
            province_id=5598,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        approaching_enemy = _army(
            117_440_838,
            soldiers=800,
            province_id=496,
            controllable=False,
            move_target_province_id=5598,
            army_state="moving",
            route_province_ids=[
                5565,
                5566,
                5567,
                5568,
                5576,
                5577,
                753,
                5684,
                5683,
                5596,
                5597,
                5598,
            ],
        )
        objectives = [3708, *range(10_000, 10_184), 5598, 2638]
        self.assertEqual(len(objectives), 187)
        objective_states = [
            _objective_state(
                province_id,
                occupant=707 if province_id == 2638 else None,
                fort_level=1 if province_id == 3708 else 4,
                garrison_size=250 if province_id == 3708 else 625,
            )
            for province_id in objectives
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=53_208_648,
            history=[
                _preview_row(
                    2578,
                    army_id=33_554_797,
                    origin=5598,
                    target=3708,
                    date_raw=53_208_648,
                    route=[
                        738,
                        951,
                        950,
                        8668,
                        947,
                        8665,
                        8666,
                        3788,
                        3796,
                        3703,
                        3704,
                        3708,
                    ],
                )
            ],
            objectives=objectives,
            objective_states=objective_states,
            occupation_supported=True,
            fort_level_supported=True,
            garrison_supported=True,
            steps=(
                "move-army-33554797-to-3708",
                "preview-move-army-33554797-to-10000",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-33554797-to-3708")
        self.assertEqual(
            plan["pursuit"]["route_audit"]["selection"],
            {
                "policy": "first_safe_ranked_exact_objective",
                "route_hops": 12,
                "objective_rank": 0,
                "evaluated_candidate_count": 1,
                "unevaluated_candidate_count": 185,
            },
        )

    def test_first_safe_exact_routing_continues_after_unsafe_candidate(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2585,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        approaching_enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[2596, 2585],
        )

        plan = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2585,
                    target=2510,
                    date_raw=24_000,
                    route=[2596, 2510],
                ),
                _preview_row(
                    2,
                    origin=2585,
                    target=2548,
                    date_raw=24_000,
                    route=[2587, 2548],
                ),
            ],
            objectives=[2510, 2548],
            steps=("move-army-11-to-2548", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2548")
        self.assertEqual(
            plan["pursuit"]["route_audit"]["selection"],
            {
                "policy": "first_safe_ranked_exact_objective",
                "route_hops": 2,
                "objective_rank": 1,
                "evaluated_candidate_count": 2,
                "unevaluated_candidate_count": 0,
            },
        )

    def test_ordinary_exact_routing_keeps_first_safe_rank_without_full_scan(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[31, 52, 2510],
                )
            ],
            objectives=[2510, 2548],
            steps=(
                "move-army-11-to-2510",
                "preview-move-army-11-to-2548",
                "move-army-11-to-2548",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")

    def test_restore_failure_memory_rejects_same_target_outside_fact_history(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2598,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2598,
            army_state="moving",
            route_province_ids=[2596, 2598],
        )
        failure = {
            "status": "rolled_back_active_route",
            "episode_run_id": "native-707-test",
            "war_id": 88,
            "army_id": 11,
            "restored_origin_province_id": 2598,
            "target_province_id": 2568,
            "route_origin_province_id": 2598,
            "route_province_ids": [2599, 2587, 2585, 2572, 2568],
            "terminal_failure_target_province_id": 2568,
            "terminal_failure_route_origin_province_id": 2604,
            "terminal_failure_route_province_ids": [
                8759,
                2602,
                2591,
                2589,
                2579,
                2574,
                2572,
                2568,
            ],
        }
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2598,
                    target=2568,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2568],
                ),
                _preview_row(
                    2,
                    origin=2598,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2548],
                ),
            ],
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
            rollback_war_failure=failure,
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2548")
        without_memory = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2598,
                    target=2568,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2568],
                ),
                _preview_row(
                    2,
                    origin=2598,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2548],
                ),
            ],
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
        )
        self.assertEqual(
            without_memory["selected_step"], "move-army-11-to-2568"
        )
        changed_route = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=2598,
                    target=2568,
                    date_raw=24_000,
                    route=[2587, 2585, 2572, 2568],
                ),
                _preview_row(
                    2,
                    origin=2598,
                    target=2548,
                    date_raw=24_000,
                    route=[2599, 2587, 2585, 2572, 2548],
                ),
            ],
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
            rollback_war_failure=failure,
        )
        self.assertEqual(changed_route["selected_step"], "move-army-11-to-2568")

    def test_two_rollback_memories_block_both_exact_routes_but_not_new_route(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2598,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2600,
            controllable=False,
            move_target_province_id=2598,
            army_state="moving",
            route_province_ids=[2596, 2598],
        )

        def failure(target: int, route: list[int]) -> dict[str, object]:
            return {
                "status": "rolled_back_active_route",
                "episode_run_id": "native-707-test",
                "war_id": 88,
                "army_id": 11,
                "restored_origin_province_id": 2598,
                "target_province_id": target,
                "route_origin_province_id": 2598,
                "route_province_ids": list(route),
            }

        newest = failure(2568, [2599, 2587, 2572, 2568])
        older = failure(2548, [2599, 2587, 2572, 2548])
        history = [
            _preview_row(
                1,
                origin=2598,
                target=2568,
                date_raw=24_000,
                route=[2599, 2587, 2572, 2568],
            ),
            _preview_row(
                2,
                origin=2598,
                target=2548,
                date_raw=24_000,
                route=[2599, 2587, 2572, 2548],
            ),
        ]
        blocked = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=history,
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
            rollback_war_failure=newest,
            rollback_war_failures=[newest, older],
        )

        self.assertIsNone(blocked["selected_step"])
        self.assertEqual(
            [
                rejection["target_province_id"]
                for rejection in blocked["route_rejections"]
                if rejection.get("status") == "rolled_back_route_failure"
            ],
            [2568, 2548],
        )

        changed_route_history = [
            history[0],
            _preview_row(
                2,
                origin=2598,
                target=2548,
                date_raw=24_000,
                route=[2587, 2572, 2548],
            ),
        ]
        changed_route = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=changed_route_history,
            objectives=[2598, 2568, 2548],
            steps=(
                "move-army-11-to-2568",
                "move-army-11-to-2548",
                "life-advance",
            ),
            rollback_war_failure=newest,
            rollback_war_failures=[newest, older],
        )
        self.assertEqual(changed_route["selected_step"], "move-army-11-to-2548")

    def test_stationary_threat_blocks_nonobjective_recovery_advance(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2598,
            controllable=True,
            army_state="regular",
        )
        approaching_enemy = _army(
            21,
            soldiers=800,
            province_id=2585,
            controllable=False,
            move_target_province_id=2598,
            army_state="moving",
        )

        plan = _native_war_plan(
            player=player,
            enemies=[approaching_enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            steps=("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_target")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["route_rejections"][0]["kind"],
            "enemy_targeting_stationary_province",
        )

    def test_stationary_army_chooses_route_without_enemy_route_overlap(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2604,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2597,
            controllable=False,
            move_target_province_id=2604,
            army_state="moving",
            route_province_ids=[2596, 2595, 2603, 2604],
        )
        history = [
            _preview_row(
                1,
                origin=2604,
                target=2585,
                date_raw=24_000,
                route=[2603, 2595, 2598, 2599, 2587, 2585],
            ),
            _preview_row(
                2,
                origin=2604,
                target=2568,
                date_raw=24_000,
                route=[8759, 2602, 2591, 2589, 2579, 2574, 2572, 2568],
            ),
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=38,
            date_raw=24_000,
            history=history,
            objectives=[2585, 2568],
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2568",
                "life-advance",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2568")

    def test_preview_without_passive_routes_is_explicitly_unsupported(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("preview-move-army-11-to-2585", "life-advance"),
            army_routes_supported=False,
            move_route_preview_supported=True,
        )

        self.assertEqual(
            plan["phase"], "native_war_route_monitoring_unsupported"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "game.state.army-routes")

    def test_unsafe_route_never_advances_for_deferred_or_current_reroute(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 31, 2585],
        )
        enemy = _army(21, soldiers=800, province_id=31, controllable=False)
        deferred = {
            "index": 2,
            "command": "move-army-11-to-2510",
            "ok": True,
            "result": {
                "accepted": False,
                "war_action": {
                    "status": "move_deferred",
                    "army_id": 11,
                    "target_province_id": 2510,
                    "submitted_date_raw": 24_000,
                },
            },
        }
        blocked = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2510,
                    date_raw=24_000,
                    route=[52, 2510],
                ),
                deferred,
                _route_contact_row(
                    3,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 2585],
                    hostile_ids=(21,),
                    contact_free=False,
                ),
            ],
            objectives=[2585, 2510],
            steps=("move-army-11-to-2510", "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(blocked["phase"], "native_war_unsafe_route_blocked")
        self.assertIsNone(blocked["selected_step"])

        current_only = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _route_contact_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[20, 31, 2585],
                    hostile_ids=(21,),
                    contact_free=False,
                )
            ],
            objectives=[2585, 20],
            steps=("move-army-11-to-20", "life-advance"),
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            current_only["phase"], "native_war_no_safe_exact_route"
        )
        self.assertIsNone(current_only["selected_step"])

        r885_player = _army(
            184_549_472,
            soldiers=2,
            province_id=8750,
            controllable=True,
            move_target_province_id=45,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[45],
        )
        r885_enemy = _army(
            184_549_393,
            soldiers=2_000,
            province_id=45,
            controllable=False,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
        )
        r886_no_pseudo_cancel = _native_war_plan(
            player=r885_player,
            enemies=[r885_enemy],
            score=-50,
            date_raw=53_282_952,
            history=[
                _route_contact_row(
                    1,
                    army_id=184_549_472,
                    origin=8750,
                    target=45,
                    date_raw=53_282_952,
                    route=[45],
                    hostile_ids=(184_549_393,),
                    contact_free=False,
                )
            ],
            objectives=[],
            steps=("move-army-184549472-to-8750",),
            player_side="defender",
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            r886_no_pseudo_cancel["phase"],
            "native_war_no_safe_exact_route",
        )
        self.assertIsNone(r886_no_pseudo_cancel["selected_step"])

        r885_without_literal = _native_war_plan(
            player=r885_player,
            enemies=[r885_enemy],
            score=-50,
            date_raw=53_282_952,
            history=[
                _route_contact_row(
                    1,
                    army_id=184_549_472,
                    origin=8750,
                    target=45,
                    date_raw=53_282_952,
                    route=[45],
                    hostile_ids=(184_549_393,),
                    contact_free=False,
                )
            ],
            objectives=[],
            steps=(),
            player_side="defender",
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            r885_without_literal["phase"], "native_war_no_safe_exact_route"
        )
        self.assertIsNone(r885_without_literal["selected_step"])

        submitted_date_raw = 53_282_928
        pending_white_peace = _native_war_plan(
            player=r885_player,
            enemies=[r885_enemy],
            score=-50,
            date_raw=53_282_952,
            history=[
                {
                    "index": 1449,
                    "command": "offer-white-peace-88",
                    "ok": True,
                    "result": {
                        "war_termination_result": {
                            "status": "submitted_pending",
                            "war_id": 88,
                            "outcome": "white_peace",
                            "episode_run_id": None,
                            "submitted_date_raw": submitted_date_raw,
                        }
                    },
                }
            ],
            objectives=[],
            steps=("move-army-184549472-to-8750", "life-advance"),
            player_side="defender",
        )
        self.assertEqual(
            pending_white_peace["phase"],
            "native_war_active_route_contact_horizon_unsupported",
        )
        self.assertIsNone(pending_white_peace["selected_step"])

        surrender_options = _termination_options(
            score=-44, war_duration_days=216
        )
        surrender_options["active_casus_belli_identity"] = {
            "database_index": 17,
            "canonical_key": "individual_county_de_jure_cb",
        }
        surrender_options.update(
            {
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        terminal_comparison = _native_war_plan(
            player=r885_player,
            enemies=[r885_enemy],
            score=-44,
            date_raw=53_282_952,
            history=[
                _route_contact_row(
                    1,
                    army_id=184_549_472,
                    origin=8750,
                    target=45,
                    date_raw=53_282_952,
                    route=[45],
                    hostile_ids=(184_549_393,),
                    contact_free=False,
                )
            ],
            objectives=[],
            steps=(
                "move-army-184549472-to-8750",
                "surrender-war-88",
            ),
            termination_options=[surrender_options],
            route_contact_horizon_supported=True,
        )
        self.assertEqual(
            terminal_comparison["phase"],
            "native_war_de_jure_no_safe_route_surrender",
        )
        self.assertEqual(
            terminal_comparison["selected_step"], "surrender-war-88"
        )

        idle = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=None,
            army_state="regular",
            route_province_ids=[],
        )
        strength_rows = [
            {
                "status": "available",
                "army_id": 11,
                "scope_role": "player",
                "war_ids": [88],
                "current_soldiers": 900,
                "maximum_soldiers": 900,
                "ai_base_power_raw": 900_000,
            },
            {
                "status": "available",
                "army_id": 21,
                "scope_role": "active_war_enemy",
                "war_ids": [88],
                "current_soldiers": 1_600,
                "maximum_soldiers": 1_600,
                "ai_base_power_raw": 1_600_000,
            },
        ]
        defensive_hold = _native_war_plan(
            player=idle,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            history=[
                _preview_row(
                    1,
                    origin=20,
                    target=2585,
                    date_raw=24_000,
                    route=[31, 2585],
                ),
                _campaign_root_row(
                    2, date_raw=24_000, capital_province_id=45
                ),
                _preview_row(
                    3,
                    origin=20,
                    target=45,
                    date_raw=24_000,
                    route=[31, 45],
                ),
            ],
            objective=2585,
            steps=("life-advance",),
            army_strengths=strength_rows,
            army_strengths_status="available",
        )
        self.assertEqual(
            defensive_hold["phase"],
            "native_war_no_safe_route_defensive_hold_progress",
        )
        self.assertEqual(defensive_hold["selected_step"], "life-advance")

    def test_all_controllable_routes_and_all_wars_are_audited(self) -> None:
        strong = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 52, 2585],
        )
        weak = _army(
            12,
            soldiers=500,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 31, 2585],
        )
        selected_war_enemy = _army(
            21, soldiers=700, province_id=90, controllable=False
        )
        other_war_enemy = _army(
            22, soldiers=600, province_id=31, controllable=False
        )
        snapshot = {
            **_snapshot(90),
            "paused": True,
            "army_routes_supported": True,
            "move_route_preview_supported": True,
            "date_raw": 24_000,
            "native_command_history": [],
            "active_wars": [
                _war(
                    war_id=88,
                    allied_armies=[strong, weak],
                    enemy_armies=[selected_war_enemy],
                    score=24,
                    war_objective_province_ids=[2585, 2510],
                ),
                _war(
                    war_id=99,
                    allied_armies=[strong, weak],
                    enemy_armies=[other_war_enemy],
                    score=10,
                    war_objective_province_ids=[2600],
                ),
            ],
            "player_armies": [strong, weak],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: snapshot,
            execute=lambda _step, _revision: {},
            action_steps=("preview-move-army-12-to-2510", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["phase"],
            "native_war_active_route_contact_horizon_unsupported",
        )
        self.assertIsNone(plan["selected_step"])
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_safe_active_route_does_not_hide_stationary_army_threat(
        self,
    ) -> None:
        moving = _army(
            11,
            soldiers=1_500,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[20, 52, 2585],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2587, 2597, 2596],
        )
        for stationary_state in ("regular", "sieging"):
            with self.subTest(stationary_state=stationary_state):
                stationary = _army(
                    12,
                    soldiers=500,
                    province_id=2596,
                    controllable=True,
                    army_state=stationary_state,
                    route_province_ids=[],
                )
                snapshot = {
                    **_snapshot(90),
                    "paused": True,
                    "army_routes_supported": True,
                    "move_route_preview_supported": True,
                    "date_raw": 24_000,
                    "native_command_history": [],
                    "active_wars": [
                        _war(
                            allied_armies=[moving, stationary],
                            enemy_armies=[enemy],
                            score=24,
                            war_objective_province_ids=[2596, 2510, 2585],
                        )
                    ],
                    "player_armies": [moving, stationary],
                }
                driver = CallbackGameplayDriver(
                    backend_id="native-headless",
                    snapshot=lambda: snapshot,
                    execute=lambda _step, _revision: {},
                    action_steps=(
                        "preview-move-army-12-to-2510",
                        "life-advance",
                    ),
                )
                safe_snapshot = {
                    **snapshot,
                    "active_wars": [
                        {**snapshot["active_wars"][0], "enemy_armies": []}
                    ],
                }
                safe_driver = CallbackGameplayDriver(
                    backend_id="native-headless",
                    snapshot=lambda: safe_snapshot,
                    execute=lambda _step, _revision: {},
                    action_steps=(
                        "preview-move-army-12-to-2510",
                        "life-advance",
                    ),
                )

                safe_plan = GameplayBridgeService(safe_driver).plan_turn()[
                    "plan"
                ]
                plan = GameplayBridgeService(driver).plan_turn()["plan"]

                self.assertEqual(
                    safe_plan["phase"],
                    "native_war_active_route_contact_horizon_unsupported",
                )
                self.assertIsNone(safe_plan["selected_step"])
                self.assertEqual(plan["phase"], "native_war_route_preview")
                self.assertEqual(
                    plan["selected_step"],
                    "preview-move-army-12-to-2510",
                )
                self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_safe_active_assault_does_not_hide_stationary_army_threat(
        self,
    ) -> None:
        assaulting = _army(
            11,
            soldiers=1_500,
            province_id=2585,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        stationary = _army(
            12,
            soldiers=500,
            province_id=2596,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=800,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            route_province_ids=[2587, 2597, 2596],
        )
        snapshot = {
            **_snapshot(90),
            "paused": True,
            "army_routes_supported": True,
            "move_route_preview_supported": True,
            "war_objective_garrison_supported": True,
            "war_objective_siege_progress_supported": True,
            "war_objective_assault_supported": True,
            "date_raw": 24_000,
            "native_command_history": [],
            "active_wars": [
                _war(
                    allied_armies=[assaulting, stationary],
                    enemy_armies=[enemy],
                    score=24,
                    war_objective_province_ids=[2585, 2596, 2510],
                    objective_province_states=[
                        _objective_state(
                            2585,
                            garrison_size=500,
                            besieging_strength=1_500,
                            active_siege=_active_siege(
                                army_id=11,
                                assault_observable=True,
                                breach_level=1,
                                assault_in_progress=True,
                                can_start_assault=False,
                                can_stop_assault=True,
                                assault_daily_progress_raw=340_000,
                                assault_daily_casualties=16,
                            ),
                        )
                    ],
                )
            ],
            "player_armies": [assaulting, stationary],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: snapshot,
            execute=lambda _step, _revision: {},
            action_steps=(
                "preview-move-army-12-to-2585",
                "life-advance",
            ),
        )
        safe_snapshot = {
            **snapshot,
            "active_wars": [
                {**snapshot["active_wars"][0], "enemy_armies": []}
            ],
        }
        safe_driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: safe_snapshot,
            execute=lambda _step, _revision: {},
            action_steps=(
                "preview-move-army-12-to-2585",
                "life-advance",
            ),
        )

        safe_plan = GameplayBridgeService(safe_driver).plan_turn()["plan"]
        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            safe_plan["phase"], "native_war_assault_daily_progress"
        )
        self.assertEqual(safe_plan["selected_step"], "life-advance")
        self.assertEqual(plan["phase"], "native_war_route_preview")
        self.assertEqual(
            plan["selected_step"],
            "preview-move-army-12-to-2585",
        )
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_unpaused_active_route_is_paused_before_route_audit(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            move_target_province_id=2585,
            army_state="moving",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("pause-map", "preview-move-army-11-to-2585"),
            paused=False,
        )

        self.assertEqual(
            plan["phase"], "native_war_route_wait_for_pause"
        )
        self.assertEqual(plan["selected_step"], "pause-map")

    def test_assault_only_capability_requires_pause_before_rich_state(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            steps=("pause-map", "life-advance"),
            paused=False,
            assault_supported=True,
        )

        self.assertEqual(plan["phase"], "native_war_route_wait_for_pause")
        self.assertEqual(plan["selected_step"], "pause-map")

    def test_route_field_without_capabilities_keeps_legacy_direct_move(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=0,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
            army_routes_supported=False,
            move_route_preview_supported=False,
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_cross_run_plan_changes_native_opening_order_and_is_exposed(self) -> None:
        plans = {
            "war": [
                {"priority": 100, "action": "reassess_first_low_cost_expansion"},
                {"priority": 80, "action": "seek_current_life_marriage_alliance"},
            ],
            "marriage": [
                {"priority": 100, "action": "seek_current_life_marriage_alliance"},
                {"priority": 80, "action": "reassess_first_low_cost_expansion"},
            ],
        }
        selected: dict[str, str | None] = {}
        for label, priorities in plans.items():
            with tempfile.TemporaryDirectory() as temporary:
                state_dir = Path(temporary)
                strategy_path = state_dir / "strategy" / "one-life-history.json"
                strategy_path.parent.mkdir(parents=True)
                strategy_path.write_text(
                    json.dumps(
                        {
                            "format_version": 1,
                            "mode": "one_life_roguelike",
                            "continue_as_heir_after_death": False,
                            "episodes": [{"run_id": "previous"}],
                            "next_run_plan": {
                                "policy": "fixture",
                                "continue_as_heir_after_death": False,
                                "priorities": priorities,
                            },
                        }
                    ),
                    encoding="utf-8",
                )
                driver = CallbackGameplayDriver(
                    backend_id="native-headless",
                    snapshot=lambda: {
                        **_snapshot(7),
                        "played_character": {
                            "character_id": 707,
                            "alive": True,
                            "betrothed_id": None,
                            "primary_spouse_id": None,
                            "spouse_ids": [],
                        },
                        "native_command_history": [
                            {"index": 1, "command": "save-checkpoint", "ok": True}
                        ],
                    },
                    execute=lambda step, revision: {"step": step},
                    action_steps=(
                        "query-arrange-marriage-choices",
                        "query-declarable-wars",
                        "life-advance",
                    ),
                )
                driver.state_dir = state_dir
                plan = GameplayBridgeService(driver).plan_turn()["plan"]
                selected[label] = plan["selected_step"]
                self.assertEqual(
                    plan["cross_run_plan_used"]["priorities"], priorities
                )

        self.assertEqual(selected["war"], "query-declarable-wars")
        self.assertEqual(selected["marriage"], "query-arrange-marriage-choices")

    def test_legal_native_declaration_defers_without_bypassing_evidence(self) -> None:
        snapshot = {
            **_snapshot(7),
            "played_character": {
                "character_id": 707,
                "alive": True,
                "betrothed_id": None,
                "primary_spouse_id": None,
                "spouse_ids": [],
            },
            "active_wars": [],
            "player_armies": [],
            "declarable_wars": [
                {
                    "declaration_id": "808-17-0",
                    "target_character_id": 808,
                    "casus_belli_index": 17,
                    "casus_belli_key": "conquer_county_cb",
                    "configuration_index": 0,
                    "claimant_character_id": 707,
                    "target_title_ids": [9001],
                }
            ],
        }
        plan = choose_one_life_turn(
            [{"index": 1, "command": "save-checkpoint", "ok": True}],
            snapshot=snapshot,
            action_steps=(
                "declare-war-808-17-0",
                "query-declarable-wars",
                "life-advance",
            ),
            next_run_plan={
                "policy": "fixture",
                "continue_as_heir_after_death": False,
                "priorities": [
                    {
                        "priority": 100,
                        "action": "reassess_first_low_cost_expansion",
                    },
                    {
                        "priority": 80,
                        "action": "seek_current_life_marriage_alliance",
                    },
                ],
            },
        )

        self.assertEqual(plan["phase"], "native_war_entry_no_declare")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["decision"]["outcome"], "NO_DECLARE")
        self.assertFalse(plan["decision"]["automatic_declaration_enabled"])
        self.assertEqual(plan["declaration"]["declaration_id"], "808-17-0")
        self.assertIn(
            "game.command.query-combat-simulation-inputs-v3-N",
            plan["required_capabilities"],
        )
        self.assertIn(
            "game.forecast.combat-monte-carlo-v1",
            plan["required_capabilities"],
        )

    def test_hybrid_propagates_semantic_settlement_without_visual_action(
        self,
    ) -> None:
        fast = mock.Mock()
        fast.capabilities.return_value = {
            "snapshot": True,
            "wait_for_change": True,
            "action_steps": ["death-terminal"],
            "bridge_capabilities": ["game.state.snapshot"],
        }
        fast.take_snapshot.return_value = {
            **_snapshot(4, history=[{"command": "life-advance", "ok": True}]),
            "backend_id": "native-headless",
            "episode_character_id": 707,
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
            "one_life_settlement": None,
        }
        baseline = mock.Mock()
        baseline.capabilities.return_value = {
            "snapshot": True,
            "wait_for_change": True,
            "action_steps": [],
            "bridge_capabilities": [
                "game.state.snapshot",
                ONE_LIFE_SETTLEMENT_CAPABILITY,
            ],
        }
        baseline.take_snapshot.return_value = {
            **_snapshot(7),
            "backend_id": "data-mod",
            "one_life_settlement": {
                "ready": True,
                "source_character_id": 707,
            },
        }
        hybrid = HybridGameplayDriver(fast, baseline)

        capabilities = hybrid.capabilities()
        snapshot = hybrid.take_snapshot()

        self.assertIn(
            ONE_LIFE_SETTLEMENT_CAPABILITY,
            capabilities["bridge_capabilities"],
        )
        self.assertEqual(
            snapshot["one_life_settlement"]["source_character_id"], 707
        )
        self.assertEqual(
            snapshot["one_life_settlement_backend"], "data-mod"
        )
        self.assertEqual(snapshot["one_life_settlement_status"], "ready")
        baseline.execute_step.assert_not_called()

    def test_hybrid_routes_supported_steps_to_fast_backend(self) -> None:
        calls: list[tuple[str, str]] = []
        fast = CallbackGameplayDriver(
            backend_id="native",
            snapshot=lambda: _snapshot(3),
            execute=lambda step, revision: calls.append(("fast", step))
            or {"step": step, "expected_revision": revision},
            action_steps=("life-advance",),
            source="injected-dll",
            latency="realtime",
        )
        vision = CallbackGameplayDriver(
            backend_id="vision",
            snapshot=lambda: _snapshot(3),
            execute=lambda step, revision: calls.append(("vision", step))
            or {"step": step, "expected_revision": revision},
            action_steps=("life-advance", "marriage-review"),
            source="ocr-keyboard-mouse",
        )
        hybrid = HybridGameplayDriver(fast, vision)
        revision = int(hybrid.take_snapshot()["revision"])

        self.assertEqual(
            hybrid.execute_step(
                "life-advance", expected_revision=revision
            )["backend_id"],
            "native",
        )
        self.assertEqual(
            hybrid.execute_step(
                "marriage-review", expected_revision=revision
            )["backend_id"],
            "vision",
        )
        self.assertEqual(calls, [("fast", "life-advance"), ("vision", "marriage-review")])

    def test_hybrid_does_not_replay_a_failed_supported_fast_action(self) -> None:
        vision_calls: list[str] = []

        def fail(_step: str, _revision: int | None):
            raise RuntimeError("native action failed after dispatch")

        fast = CallbackGameplayDriver(
            backend_id="native",
            snapshot=lambda: _snapshot(),
            execute=fail,
            action_steps=("life-advance",),
        )
        vision = CallbackGameplayDriver(
            backend_id="vision",
            snapshot=lambda: _snapshot(),
            execute=lambda step, _revision: vision_calls.append(step) or {},
            action_steps=("life-advance",),
        )

        with self.assertRaisesRegex(RuntimeError, "after dispatch"):
            HybridGameplayDriver(fast, vision).execute_step("life-advance")
        self.assertEqual(vision_calls, [])

    def test_hybrid_merges_fast_state_with_baseline_history_and_revisions(self) -> None:
        calls: list[tuple[str, int | None]] = []
        history = [
            {
                "command": "save-checkpoint",
                "ok": True,
                "result": {"final_screen": "map_hud"},
            }
        ]
        fast = CallbackGameplayDriver(
            backend_id="data-mod",
            snapshot=lambda: {
                **_snapshot(7, []),
                "phase": None,
                "total_days": 389_742,
            },
            execute=lambda step, revision: calls.append((step, revision)) or {},
            action_steps=(),
        )
        vision = CallbackGameplayDriver(
            backend_id="vision-session",
            snapshot=lambda: _snapshot(3, history),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("dynasty-review",),
        )
        hybrid = HybridGameplayDriver(fast, vision)

        snapshot = hybrid.take_snapshot()
        self.assertEqual(snapshot["backend_id"], "hybrid")
        self.assertEqual(snapshot["total_days"], 389_742)
        self.assertEqual(snapshot["history"], history)
        self.assertEqual(snapshot["phase"], "map_hud")
        self.assertEqual(snapshot["backend_revisions"], {"fast": 7, "baseline": 3})

        result = hybrid.execute_step(
            "dynasty-review", expected_revision=int(snapshot["revision"])
        )
        self.assertEqual(result["backend_id"], "vision-session")
        self.assertEqual(calls, [("dynasty-review", 3)])

    def test_service_reuses_existing_one_life_planner(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="fixture",
            snapshot=lambda: _snapshot(),
            execute=lambda _step, _revision: {},
            action_steps=(),
        )
        plan = GameplayBridgeService(driver).plan_turn()
        self.assertIsNone(plan["plan"]["selected_step"])
        self.assertEqual(plan["plan"]["required_step"], "save-checkpoint")
        self.assertEqual(plan["snapshot_id"], "session:0")

    def test_partial_native_backend_keeps_advancing_at_capability_gap(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(
                4,
                [
                    {
                        "command": "save-checkpoint",
                        "ok": True,
                        "result": {"checkpoint": {"status": "saved"}},
                    }
                ],
            ),
            execute=lambda _step, _revision: {},
            action_steps=("save-checkpoint", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["required_step"], "dynasty-review")
        self.assertEqual(plan["deferred_phase"], "current_life_family")

    def test_planner_queries_pending_native_character_interaction_before_reply(
        self,
    ) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(6),
                "pending_character_interaction": {
                    "instance_id": -2_130_706_360,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "query-pending-character-interaction-context-v1",
                "accept-pending-character-interaction",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["selected_step"],
            "query-pending-character-interaction-context-v1",
        )
        self.assertEqual(plan["phase"], "pending_character_interaction_query")
        self.assertEqual(
            plan["pending_character_interaction"]["instance_id"],
            -2_130_706_360,
        )

    def test_planner_acknowledges_auto_accept_notification(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(6),
                "pending_character_interaction": {
                    "instance_id": 73,
                    "sender_character_id": 501,
                    "auto_accept_notification": True,
                },
            },
            execute=lambda _step, _revision: {},
            action_steps=("acknowledge-pending-character-interaction",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["phase"], "pending_character_interaction_acknowledge"
        )
        self.assertEqual(
            plan["selected_step"],
            "acknowledge-pending-character-interaction",
        )
        self.assertTrue(
            plan["pending_character_interaction"][
                "auto_accept_notification"
            ]
        )

    def test_planner_does_not_treat_notification_as_ordinary_reply(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(6),
                "pending_character_interaction": {
                    "instance_id": 73,
                    "sender_character_id": 501,
                    "auto_accept_notification": True,
                },
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["phase"],
            "pending_character_interaction_acknowledge_unsupported",
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_step"],
            "acknowledge-pending-character-interaction",
        )

    def test_planner_rejects_ordinary_pending_after_typed_observation(self) -> None:
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=-2_130_706_360,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
            ),
            action_steps=(
                "query-pending-character-interaction-context-v1",
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_reject"
        )
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        self.assertEqual(
            plan["pending_character_interaction"]["interaction_key"],
            "spar_with_knight_interaction",
        )
        self.assertFalse(
            plan["pending_character_interaction"][
                "context_semantic_decision_ready"
            ]
        )
        self.assertEqual(
            plan["pending_character_interaction"]["instance_id"],
            -2_130_706_360,
        )
        self.assertEqual(
            plan["pending_character_interaction"]["roles"][
                "recipient_character_id"
            ],
            707,
        )
        self.assertEqual(
            plan["pending_character_interaction"]["deadline"]["remaining_days"],
            58,
        )
        self.assertEqual(
            plan["pending_character_interaction"]["special_war_binding"][
                "reason"
            ],
            "special_war_binding_not_applicable",
        )
        decision = plan["decision"]
        self.assertEqual(decision["rule_id"], "ordinary-reject-unique-accept-v1")
        self.assertEqual(decision["classification"], "ordinary_non_war")
        self.assertEqual(
            decision["definition_classification"],
            {
                "policy": "ck3-1.19.0.6-explicit-ordinary-nonreligious-v1",
                "definition_key": "spar_with_knight_interaction",
                "allowlisted": True,
                "evidence": {
                    "classification": "ordinary_non_war_nonreligious",
                    "source": (
                        "common/character_interactions/"
                        "00_tradition_interactions.txt"
                    ),
                    "source_sha256": (
                        "E3B7330D8DFD9C82522D65629B6DD991D319B76B41C388CE4"
                        "83E351D829391E3"
                    ),
                },
            },
        )
        self.assertEqual(decision["selected_action"], "reject")
        self.assertFalse(decision["native_ai_equivalent"])
        self.assertFalse(decision["semantic_decision_ready"])
        self.assertIn(
            "structured_effect_preview_unavailable",
            decision["missing_semantics"],
        )
        self.assertEqual(
            [row["action"] for row in decision["candidate_replies"]],
            ["accept", "reject", "block", "acknowledge"],
        )

    def test_planner_rejects_exact_build_pay_ransom_pending(self) -> None:
        context_result = _pending_context_result(
            pending_id=855_638_016,
            revision=8,
            native_revision=7,
            date_raw=53_178_336,
            definition_key="pay_ransom_interaction",
            actor_character_id=30_629,
            recipient_character_id=29_829,
            legality={
                "accept": {"status": "available", "allowed": True, "reason": None},
                "reject": {"status": "available", "allowed": True, "reason": None},
                "block": {"status": "available", "allowed": True, "reason": None},
                "acknowledge": {
                    "status": "available",
                    "allowed": False,
                    "reason": "normal_reply_channel",
                },
            },
        )
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        roles = context["roles"]
        assert isinstance(roles, dict)
        roles["secondary_recipient_character_id"] = 34_250
        context["send_options"] = {
            "exclusive": False,
            "definition_count": 8,
            "context_count": 8,
            "rows": [
                {
                    "native_index": index,
                    "selected": index == 2,
                    "canonical_flag_status": "unavailable",
                }
                for index in range(8)
            ],
        }

        plan = _plan_for_pending_context(
            context_result,
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_reject"
        )
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        self.assertEqual(
            plan["pending_character_interaction"]["roles"],
            {
                "actor_character_id": 30_629,
                "recipient_character_id": 29_829,
                "secondary_actor_character_id": -1,
                "secondary_recipient_character_id": 34_250,
                "intermediary_character_id": -1,
            },
        )
        self.assertTrue(
            plan["pending_character_interaction"]["send_options"]["rows"][2][
                "selected"
            ]
        )
        decision = plan["decision"]
        self.assertEqual(decision["classification"], "ordinary_non_war")
        self.assertEqual(decision["selected_action"], "reject")
        self.assertFalse(decision["native_ai_equivalent"])
        self.assertFalse(decision["semantic_optimal"])
        self.assertEqual(
            decision["definition_classification"],
            {
                "policy": "ck3-1.19.0.6-explicit-ordinary-nonreligious-v1",
                "definition_key": "pay_ransom_interaction",
                "allowlisted": True,
                "evidence": {
                    "classification": "ordinary_non_war_nonreligious",
                    "domain": "prison_ransom",
                    "war_sensitive": True,
                    "source": (
                        "common/character_interactions/"
                        "00_prison_interactions.txt"
                    ),
                    "source_sha256": (
                        "3E05C94CDCE4D42CCE8256D2D79CD78FEB1C9D5B79DAA64A"
                        "A8243AA0C658F22B"
                    ),
                },
            },
        )

    def test_planner_rejects_exact_build_ransom_pending(self) -> None:
        context_result = _pending_context_result(
            pending_id=-1_845_493_753,
            revision=207,
            native_revision=206,
            date_raw=53_395_584,
            definition_key="ransom_interaction",
            actor_character_id=34_676,
            recipient_character_id=31_853,
            legality={
                "accept": {
                    "status": "available",
                    "allowed": True,
                    "reason": None,
                },
                "reject": {
                    "status": "available",
                    "allowed": True,
                    "reason": None,
                },
                "block": {
                    "status": "available",
                    "allowed": True,
                    "reason": None,
                },
                "acknowledge": {
                    "status": "available",
                    "allowed": False,
                    "reason": "normal_reply_channel",
                },
            },
        )
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        roles = context["roles"]
        assert isinstance(roles, dict)
        roles["secondary_recipient_character_id"] = 36_843
        context["send_options"] = {
            "exclusive": True,
            "definition_count": 8,
            "context_count": 8,
            "rows": [
                {
                    "native_index": index,
                    "selected": index == 2,
                    "is_shown": index in (2, 4),
                    "is_valid": index in (2, 4),
                    "canonical_flag_status": "unavailable",
                }
                for index in range(8)
            ],
        }

        plan = _plan_for_pending_context(
            context_result,
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_reject"
        )
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(decision["classification"], "ordinary_non_war")
        self.assertEqual(decision["selected_action"], "reject")
        self.assertFalse(decision["native_ai_equivalent"])
        self.assertFalse(decision["semantic_optimal"])
        self.assertEqual(
            decision["definition_classification"],
            {
                "policy": "ck3-1.19.0.6-explicit-ordinary-nonreligious-v1",
                "definition_key": "ransom_interaction",
                "allowlisted": True,
                "evidence": {
                    "classification": "ordinary_non_war_nonreligious",
                    "domain": "prison_ransom",
                    "war_sensitive": True,
                    "authored_special_interaction": "ransom_interaction",
                    "source": (
                        "common/character_interactions/"
                        "00_prison_interactions.txt"
                    ),
                    "source_sha256": (
                        "3E05C94CDCE4D42CCE8256D2D79CD78FEB1C9D5B79DAA64A"
                        "A8243AA0C658F22B"
                    ),
                    "known_decline_effects": [
                        "secondary_recipient:"
                        "character_ransom_refused_by_player:10y",
                        "actor:char_interaction.0131",
                    ],
                },
            },
        )

    def test_grant_vassal_r0059_exact_shape_reject_only(self) -> None:
        plan = _plan_for_pending_context(
            _grant_vassal_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
            active_wars=[],
        )

        self.assertEqual(plan["phase"], "pending_grant_vassal_reject_only")
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(decision["rule_id"], "grant-vassal-reject-only-v1")
        self.assertEqual(
            decision["classification"], "known_grant_vassal_reject_only"
        )
        self.assertEqual(decision["grant_vassal_contract_gaps"], [])
        self.assertEqual(decision["selected_action"], "reject")
        self.assertFalse(decision["semantic_optimal"])
        evidence = decision["definition_classification"]
        self.assertTrue(evidence["allowlisted"])
        self.assertEqual(
            evidence["evidence"]["supported_scope"],
            "frozen_standard_feudal_profile_not_frame_attested",
        )
        self.assertEqual(
            evidence["evidence"]["source_sha256"],
            "1249CAC40138D48210A07245746C4A6683C5F58F3141C04A20DB2C00B6375BF8",
        )

    def test_grant_vassal_reject_only_fails_closed_on_shape_or_unknown_wars(self) -> None:
        mutations = (
            (
                "definition_hash",
                lambda c: c["definition"].__setitem__(
                    "deterministic_key_hash", 1
                ),
                "grant_vassal_exact_definition_mismatch",
            ),
            (
                "secondary_actor",
                lambda c: c["roles"].__setitem__(
                    "secondary_actor_character_id", -1
                ),
                "grant_vassal_direct_three_role_binding_mismatch",
            ),
            (
                "routing",
                lambda c: c["routing"].__setitem__(
                    "reply_execution_channel", "intermediary"
                ),
                "grant_vassal_direct_local_reply_mismatch",
            ),
            (
                "deadline",
                lambda c: c["deadline"].__setitem__("remaining_days", 52),
                "grant_vassal_unexpired_deadline_mismatch",
            ),
            (
                "options",
                lambda c: c["send_options"].__setitem__(
                    "definition_count", 1
                ),
                "grant_vassal_zero_send_options_mismatch",
            ),
            (
                "special_binding",
                lambda c: c["terms"].__setitem__(
                    "special_data_present", True
                ),
                "grant_vassal_nonwar_special_binding_mismatch",
            ),
            (
                "notification_channel",
                lambda c: c["legality"]["acknowledge"].__setitem__(
                    "allowed", True
                ),
                "grant_vassal_normal_reply_channel_mismatch",
            ),
        )
        for name, mutate, expected_gap in mutations:
            with self.subTest(name=name):
                result = _grant_vassal_context_result()
                context = result["pending_character_interaction_context"]
                mutate(context)
                plan = _plan_for_pending_context(
                    result,
                    action_steps=(
                        "accept-pending-character-interaction",
                        "reject-pending-character-interaction",
                    ),
                    active_wars=[],
                )
                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    expected_gap, plan["decision"]["grant_vassal_contract_gaps"]
                )

        for active_wars in (None, [None]):
            with self.subTest(active_wars=active_wars):
                plan = _plan_for_pending_context(
                    _grant_vassal_context_result(),
                    action_steps=(
                        "accept-pending-character-interaction",
                        "reject-pending-character-interaction",
                    ),
                    active_wars=active_wars,
                )
                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    "grant_vassal_active_war_or_war_scope_unknown",
                    plan["decision"]["grant_vassal_contract_gaps"],
                )

    def test_grant_vassal_reject_only_with_observed_active_war(self) -> None:
        war = _war(
            war_id=301_989_950,
            allied_armies=[],
            enemy_armies=[],
            score=-28,
            player_side="defender",
        )
        war["primary_opponent_character_id"] = 34_676
        plan = _plan_for_pending_context(
            _grant_vassal_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
            active_wars=[war],
        )

        self.assertEqual(plan["phase"], "pending_grant_vassal_reject_only")
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(decision["rule_id"], "grant-vassal-reject-only-v1")
        self.assertEqual(decision["grant_vassal_contract_gaps"], [])
        self.assertEqual(decision["selected_action"], "reject")
        self.assertFalse(decision["semantic_optimal"])

    def test_grant_vassal_reject_only_never_falls_back_to_accept(self) -> None:
        for allowed, steps, blocked in (
            (
                False,
                (
                    "accept-pending-character-interaction",
                    "reject-pending-character-interaction",
                ),
                "grant_vassal_reject_not_native_legal",
            ),
            (
                True,
                ("accept-pending-character-interaction",),
                "grant_vassal_reject_command_unavailable",
            ),
        ):
            with self.subTest(allowed=allowed, steps=steps):
                legality = {
                    action: {
                        "status": "available",
                        "allowed": action == "accept" or (
                            action == "reject" and allowed
                        ),
                        "reason": (
                            "normal_reply_channel"
                            if action == "acknowledge"
                            else None
                        ),
                    }
                    for action in ("accept", "reject", "block", "acknowledge")
                }
                plan = _plan_for_pending_context(
                    _grant_vassal_context_result(legality=legality),
                    action_steps=steps,
                    active_wars=[],
                )
                self.assertIsNone(plan["selected_step"])
                self.assertIsNone(plan["decision"]["selected_action"])
                self.assertIn(blocked, plan["decision"]["blocked_reasons"])

    def test_planner_rejects_exact_direct_zero_option_marriage_pending(
        self,
    ) -> None:
        plan = _plan_for_pending_context(
            _arrange_marriage_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(plan["phase"], "pending_arrange_marriage_reject_only")
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(decision["rule_id"], "arrange-marriage-reject-only-v1")
        self.assertEqual(decision["classification"], "known_marriage_special")
        self.assertEqual(decision["selected_action"], "reject")
        self.assertEqual(decision["marriage_contract_gaps"], [])
        self.assertFalse(decision["native_ai_equivalent"])
        self.assertFalse(decision["semantic_optimal"])
        self.assertEqual(
            decision["definition_classification"],
            {
                "policy": (
                    "ck3-1.19.0.6-explicit-marriage-special-reject-only-v1"
                ),
                "definition_key": "arrange_marriage_interaction",
                "allowlisted": True,
                "evidence": {
                    "classification": "marriage_special_reject_only",
                    "domain": "marriage_alliance",
                    "source": (
                        "common/character_interactions/"
                        "00_marriage_interactions.txt"
                    ),
                    "source_sha256": (
                        "681A9B669E5A16642A197B6FE16085193DFBB99A398D0E20E8"
                        "6173F5AC6DE219"
                    ),
                    "required_send_option_count": 6,
                    "known_decline_effects": [
                        "marriage_interaction.0011",
                        "secondary_actor:player_declined_marriage:5y",
                    ],
                },
            },
        )

    def test_planner_rejects_unexpired_aged_marriage_pending(self) -> None:
        plan = _plan_for_pending_context(
            _arrange_marriage_context_result(
                age_days=2,
                expiration_days=60,
                remaining_days=58,
            ),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(plan["phase"], "pending_arrange_marriage_reject_only")
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(decision["selected_action"], "reject")
        self.assertEqual(decision["marriage_contract_gaps"], [])

    def test_marriage_reject_only_requires_consistent_unexpired_deadline(
        self,
    ) -> None:
        for deadline, expected_gap in (
            (
                {"age_days": None, "expiration_days": 60, "remaining_days": 58},
                "marriage_unexpired_deadline_shape_mismatch",
            ),
            (
                {"age_days": True, "expiration_days": 60, "remaining_days": 59},
                "marriage_unexpired_deadline_shape_mismatch",
            ),
            (
                {"age_days": 2, "expiration_days": 60, "remaining_days": 57},
                "marriage_unexpired_deadline_shape_mismatch",
            ),
            (
                {"age_days": 60, "expiration_days": 60, "remaining_days": 0},
                "marriage_unexpired_deadline_shape_mismatch",
            ),
            (
                {"age_days": 2, "expiration_days": 61, "remaining_days": 59},
                "marriage_unexpired_deadline_shape_mismatch",
            ),
        ):
            with self.subTest(deadline=deadline):
                result = _arrange_marriage_context_result(
                    age_days=deadline["age_days"],
                    expiration_days=deadline["expiration_days"],
                    remaining_days=deadline["remaining_days"],
                )
                plan = _plan_for_pending_context(
                    result,
                    action_steps=(
                        "accept-pending-character-interaction",
                        "reject-pending-character-interaction",
                    ),
                )
                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    expected_gap, plan["decision"]["marriage_contract_gaps"]
                )

        result = _arrange_marriage_context_result(
            age_days=2,
            expiration_days=60,
            remaining_days=58,
            expiry_boundary_status="reached",
        )
        plan = _plan_for_pending_context(
            result,
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )
        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "marriage_unexpired_deadline_shape_mismatch",
            plan["decision"]["marriage_contract_gaps"],
        )

    def test_marriage_reject_only_never_falls_through_to_unique_accept(
        self,
    ) -> None:
        legality = {
            "accept": {"status": "available", "allowed": True, "reason": None},
            "reject": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "block": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "normal_reply_channel",
            },
        }
        plan = _plan_for_pending_context(
            _arrange_marriage_context_result(legality=legality),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_blocked"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertIsNone(plan["decision"]["selected_action"])
        self.assertIn(
            "marriage_reject_not_native_legal",
            plan["decision"]["blocked_reasons"],
        )

    def test_marriage_reject_only_requires_complete_direct_roles(self) -> None:
        for result, expected_gap in (
            (
                _arrange_marriage_context_result(
                    secondary_actor_character_id=-1
                ),
                "marriage_secondary_actor_character_id_unavailable",
            ),
            (
                _arrange_marriage_context_result(intermediary_character_id=41_001),
                "marriage_direct_recipient_route_required",
            ),
        ):
            with self.subTest(expected_gap=expected_gap):
                plan = _plan_for_pending_context(
                    result,
                    action_steps=(
                        "accept-pending-character-interaction",
                        "reject-pending-character-interaction",
                    ),
                )
                self.assertIsNone(plan["selected_step"])
                self.assertEqual(
                    plan["decision"]["classification"],
                    "known_marriage_special",
                )
                self.assertIn(
                    expected_gap, plan["decision"]["marriage_contract_gaps"]
                )

    def test_marriage_reject_only_blocks_selected_send_option(self) -> None:
        plan = _plan_for_pending_context(
            _arrange_marriage_context_result(selected_option_index=1),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "marriage_zero_option_vector_mismatch",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_accepts_exact_zero_option_inbound_alliance_in_defense(
        self,
    ) -> None:
        defensive_war = {
            **_war(
                war_id=134_217_738,
                allied_armies=[],
                enemy_armies=[],
                score=-23,
                player_side="defender",
            ),
            "primary_opponent_character_id": 32_309,
        }
        plan = _plan_for_pending_context(
            _negotiate_alliance_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "block-pending-character-interaction",
            ),
            active_wars=[defensive_war],
        )

        self.assertEqual(plan["phase"], "pending_negotiate_alliance_accept")
        self.assertEqual(
            plan["selected_step"], "accept-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(
            decision["classification"], "known_negotiate_alliance_inbound"
        )
        self.assertEqual(
            decision["rule_id"], "negotiate-alliance-inbound-accept-v1"
        )
        self.assertEqual(decision["selected_action"], "accept")
        self.assertFalse(decision["semantic_optimal"])
        assessment = decision["negotiate_alliance_inbound"]
        self.assertEqual(assessment["status"], "ready")
        self.assertEqual(
            assessment["evidence"]["active_defensive_war_ids"],
            [134_217_738],
        )
        self.assertEqual(assessment["evidence"]["selected_option_count"], 0)
        self.assertFalse(
            assessment["evidence"]["alliance_semantic_postcondition_ready"]
        )

    def test_inbound_alliance_accept_blocks_selected_option(self) -> None:
        plan = _plan_for_pending_context(
            _negotiate_alliance_context_result(selected_option_index=0),
            action_steps=("accept-pending-character-interaction",),
            active_wars=[
                _war(
                    war_id=134_217_738,
                    allied_armies=[],
                    enemy_armies=[],
                    score=-23,
                    player_side="defender",
                )
            ],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "negotiate_alliance_zero_option_vector_mismatch",
            plan["decision"]["blocked_reasons"],
        )

    def test_inbound_alliance_accept_requires_active_defensive_war(self) -> None:
        for active_wars in (
            [],
            [
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    player_side="attacker",
                )
            ],
        ):
            with self.subTest(active_wars=active_wars):
                plan = _plan_for_pending_context(
                    _negotiate_alliance_context_result(),
                    action_steps=("accept-pending-character-interaction",),
                    active_wars=active_wars,
                )
                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    "negotiate_alliance_active_defensive_war_required",
                    plan["decision"]["blocked_reasons"],
                )

    def test_inbound_alliance_accept_blocks_actor_war_opponent(self) -> None:
        war = _war(
            allied_armies=[],
            enemy_armies=[],
            player_side="defender",
        )
        war["primary_opponent_character_id"] = 34_867
        plan = _plan_for_pending_context(
            _negotiate_alliance_context_result(),
            action_steps=("accept-pending-character-interaction",),
            active_wars=[war],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "negotiate_alliance_actor_is_active_war_opponent",
            plan["decision"]["blocked_reasons"],
        )

    def test_inbound_alliance_accept_requires_native_accept_legality(self) -> None:
        legality = {
            "accept": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "reject": {"status": "available", "allowed": True, "reason": None},
            "block": {"status": "available", "allowed": True, "reason": None},
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "normal_reply_channel",
            },
        }
        plan = _plan_for_pending_context(
            _negotiate_alliance_context_result(legality=legality),
            action_steps=("accept-pending-character-interaction",),
            active_wars=[
                _war(
                    allied_armies=[],
                    enemy_armies=[],
                    player_side="defender",
                )
            ],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "negotiate_alliance_accept_not_native_legal",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_accepts_r0127_perk_alliance_only_as_bounded_reply(self) -> None:
        plan = _plan_for_pending_context(
            _perk_alliance_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
            active_wars=[],
        )

        self.assertEqual(plan["phase"], "pending_perk_alliance_accept")
        self.assertEqual(
            plan["selected_step"], "accept-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(
            decision["classification"], "known_perk_alliance_inbound"
        )
        self.assertEqual(
            decision["rule_id"], "perk-alliance-inbound-accept-v1"
        )
        self.assertFalse(decision["semantic_decision_ready"])
        evidence = decision["perk_alliance_inbound"]["evidence"]
        self.assertEqual(evidence["selected_option_count"], 0)
        self.assertEqual(evidence["active_war_count"], 0)
        self.assertFalse(evidence["alliance_semantic_postcondition_ready"])

    def test_perk_alliance_rejects_changed_cost_identity_or_legality(
        self,
    ) -> None:
        cases = (
            ("selected_option", "perk_alliance_zero_option_vector_mismatch"),
            ("definition_identity", "perk_alliance_definition_identity_mismatch"),
            ("expired", "perk_alliance_unexpired_deadline_mismatch"),
            ("accept_illegal", "perk_alliance_accept_not_native_legal"),
        )
        for changed, expected_reason in cases:
            with self.subTest(changed=changed):
                result = _perk_alliance_context_result()
                context = result["pending_character_interaction_context"]
                assert isinstance(context, dict)
                if changed == "selected_option":
                    context["send_options"]["rows"][0]["selected"] = True
                elif changed == "definition_identity":
                    context["definition"]["deterministic_key_hash"] = 0
                elif changed == "expired":
                    context["deadline"]["remaining_days"] = 0
                else:
                    context["legality"]["accept"]["allowed"] = False
                plan = _plan_for_pending_context(
                    result,
                    action_steps=(
                        "accept-pending-character-interaction",
                        "reject-pending-character-interaction",
                    ),
                    active_wars=[],
                )
                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    expected_reason, plan["decision"]["blocked_reasons"]
                )

        war_plan = _plan_for_pending_context(
            _perk_alliance_context_result(),
            action_steps=("accept-pending-character-interaction",),
            active_wars=[_war(allied_armies=[], enemy_armies=[])],
        )
        self.assertIsNone(war_plan["selected_step"])
        self.assertIn(
            "perk_alliance_no_active_war_required",
            war_plan["decision"]["blocked_reasons"],
        )
        missing_war_observation = _plan_for_pending_context(
            _perk_alliance_context_result(),
            action_steps=("accept-pending-character-interaction",),
        )
        self.assertIsNone(missing_war_observation["selected_step"])
        self.assertIn(
            "perk_alliance_active_war_observation_unavailable",
            missing_war_observation["decision"]["blocked_reasons"],
        )

    def test_planner_rejects_exact_busy_player_call_ally_shape(self) -> None:
        active_war = _war(
            war_id=50_331_699,
            allied_armies=[],
            enemy_armies=[],
            score=-48,
            player_side="attacker",
        )
        plan = _plan_for_pending_context(
            _call_ally_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "block-pending-character-interaction",
            ),
            active_wars=[active_war],
        )

        self.assertEqual(plan["phase"], "pending_call_ally_busy_reject")
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(
            decision["classification"], "known_call_ally_busy_reject"
        )
        self.assertEqual(decision["rule_id"], "call-ally-busy-reject-v1")
        self.assertEqual(decision["selected_action"], "reject")
        self.assertFalse(decision["native_ai_equivalent"])
        self.assertFalse(decision["semantic_optimal"])
        self.assertFalse(decision["interaction_semantic_decision_ready"])
        assessment = decision["call_ally_busy_reject"]
        self.assertEqual(assessment["status"], "ready")
        evidence = assessment["evidence"]
        self.assertEqual(evidence["active_war_ids_before_reply"], [50_331_699])
        self.assertFalse(evidence["target_raw_token_consumed"])
        self.assertFalse(evidence["target_typed_identity_consumed"])
        self.assertFalse(evidence["target_war_id_resolved"])
        self.assertFalse(evidence["native_ai_equivalent"])
        self.assertFalse(evidence["semantic_optimal"])
        self.assertFalse(evidence["interaction_semantic_decision_ready"])

    def test_call_ally_busy_reject_requires_frozen_definition_identity(
        self,
    ) -> None:
        for mutation, expected_reason in (
            (
                lambda context: context["build"].update(
                    {"version": "1.19.0.7"}
                ),
                "call_ally_frozen_exact_build_mismatch",
            ),
            (
                lambda context: context["definition"].update(
                    {"deterministic_key_hash": 12345}
                ),
                "call_ally_definition_identity_mismatch",
            ),
        ):
            with self.subTest(expected_reason=expected_reason):
                context_result = _call_ally_context_result()
                context = context_result[
                    "pending_character_interaction_context"
                ]
                assert isinstance(context, dict)
                mutation(context)
                plan = _plan_for_pending_context(
                    context_result,
                    action_steps=("reject-pending-character-interaction",),
                    active_wars=[
                        _war(allied_armies=[], enemy_armies=[], score=-48)
                    ],
                )

                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    expected_reason, plan["decision"]["blocked_reasons"]
                )

    def test_call_ally_busy_reject_requires_exact_roles_and_war_target_shape(
        self,
    ) -> None:
        mutations = (
            (
                lambda context: context["roles"].update(
                    {"secondary_actor_character_id": 40_001}
                ),
                "call_ally_direct_roles_mismatch",
            ),
            (
                lambda context: context["routing"].update({"kind": 1}),
                "call_ally_direct_local_route_mismatch",
            ),
            (
                lambda context: context["target"].update(
                    {"type_key": "title"}
                ),
                "call_ally_stable_war_target_type_mismatch",
            ),
            (
                lambda context: context["send_options"].update(
                    {"definition_count": 1}
                ),
                "call_ally_zero_option_vector_mismatch",
            ),
            (
                lambda context: context["send_options"].update(
                    {"exclusive": False}
                ),
                "call_ally_zero_option_vector_mismatch",
            ),
            (
                lambda context: context["terms"].update(
                    {"special_data_present": True}
                ),
                "call_ally_non_special_shape_mismatch",
            ),
        )
        for mutation, expected_reason in mutations:
            with self.subTest(expected_reason=expected_reason):
                context_result = _call_ally_context_result()
                context = context_result[
                    "pending_character_interaction_context"
                ]
                assert isinstance(context, dict)
                mutation(context)
                plan = _plan_for_pending_context(
                    context_result,
                    action_steps=("reject-pending-character-interaction",),
                    active_wars=[
                        _war(allied_armies=[], enemy_armies=[], score=-48)
                    ],
                )

                self.assertIsNone(plan["selected_step"])
                self.assertIn(
                    expected_reason, plan["decision"]["blocked_reasons"]
                )

    def test_call_ally_busy_reject_requires_existing_war_and_legal_reply(
        self,
    ) -> None:
        no_war = _plan_for_pending_context(
            _call_ally_context_result(),
            action_steps=("reject-pending-character-interaction",),
            active_wars=[],
        )
        self.assertIsNone(no_war["selected_step"])
        self.assertIn(
            "call_ally_existing_active_war_required",
            no_war["decision"]["blocked_reasons"],
        )

        legality = {
            "accept": {"status": "available", "allowed": True, "reason": None},
            "reject": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "block": {"status": "available", "allowed": True, "reason": None},
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "normal_reply_channel",
            },
        }
        illegal = _plan_for_pending_context(
            _call_ally_context_result(legality=legality),
            action_steps=("reject-pending-character-interaction",),
            active_wars=[_war(allied_armies=[], enemy_armies=[], score=-48)],
        )
        self.assertIsNone(illegal["selected_step"])
        self.assertIn(
            "call_ally_reject_not_native_legal",
            illegal["decision"]["blocked_reasons"],
        )

    def test_call_ally_busy_reject_requires_unexpired_deadline(self) -> None:
        context_result = _call_ally_context_result()
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        context["deadline"] = {
            "age_days": 60,
            "expiration_days": 60,
            "remaining_days": 0,
            "expiry_boundary_status": "at_or_past_daily_expiry_queue_threshold",
        }
        plan = _plan_for_pending_context(
            context_result,
            action_steps=("reject-pending-character-interaction",),
            active_wars=[_war(allied_armies=[], enemy_armies=[], score=-48)],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "call_ally_unexpired_deadline_required",
            plan["decision"]["blocked_reasons"],
        )

    def test_call_ally_busy_reject_does_not_decode_raw_target_token(self) -> None:
        context_result = _call_ally_context_result()
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        target = context["target"]
        assert isinstance(target, dict)
        raw = bytearray.fromhex(target["raw_16_bytes_hex"])
        raw[2] ^= 0xFF
        target["raw_16_bytes_hex"] = raw.hex()
        plan = _plan_for_pending_context(
            context_result,
            action_steps=("reject-pending-character-interaction",),
            active_wars=[_war(allied_armies=[], enemy_armies=[], score=-48)],
        )

        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        evidence = plan["decision"]["call_ally_busy_reject"]["evidence"]
        self.assertFalse(evidence["target_raw_token_consumed"])
        self.assertNotIn("raw_16_bytes_hex", evidence)

    def test_other_call_ally_definition_does_not_enter_busy_fallback(self) -> None:
        context_result = _call_ally_context_result()
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        definition = context["definition"]
        assert isinstance(definition, dict)
        definition["canonical_key"] = "call_ally_by_house_member_interaction"
        plan = _plan_for_pending_context(
            context_result,
            action_steps=("reject-pending-character-interaction",),
            active_wars=[_war(allied_armies=[], enemy_armies=[], score=-48)],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["decision"]["classification"], "definition_unclassified"
        )
        self.assertNotEqual(
            plan["decision"]["rule_id"], "call-ally-busy-reject-v1"
        )

    def test_enforce_demands_precedes_call_ally_busy_reject(self) -> None:
        plan = _plan_for_pending_context(
            _call_ally_context_result(),
            action_steps=(
                "reject-pending-character-interaction",
                "enforce-demands-88",
            ),
            active_wars=[_war(allied_armies=[], enemy_armies=[], score=100)],
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")
        self.assertNotIn("decision", plan)

    def test_enforce_demands_precedes_marriage_reject_only(self) -> None:
        plan = _plan_for_pending_context(
            _arrange_marriage_context_result(),
            action_steps=(
                "reject-pending-character-interaction",
                "enforce-demands-88",
            ),
            active_wars=[_war(allied_armies=[], enemy_armies=[], score=100)],
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")
        self.assertNotIn("decision", plan)

    def test_planner_never_accepts_because_reject_command_is_missing(self) -> None:
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
            ),
            action_steps=("accept-pending-character-interaction",),
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_blocked"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_step"], "reject-pending-character-interaction"
        )
        self.assertEqual(plan["decision"]["recommended_action"], "reject")
        self.assertIsNone(plan["decision"]["selected_action"])
        self.assertIn(
            "legal_reject_command_unavailable",
            plan["decision"]["blocked_reasons"],
        )

    def test_allowlisted_pending_replies_after_nonterminal_active_war_checks(
        self,
    ) -> None:
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
            ),
            action_steps=(
                "reject-pending-character-interaction",
                "enforce-demands-88",
                "raise-troops-default",
            ),
            active_wars=[
                _war(allied_armies=[], enemy_armies=[], score=40)
            ],
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_reject"
        )
        self.assertEqual(
            plan["selected_step"], "reject-pending-character-interaction"
        )
        self.assertEqual(plan["decision"]["classification"], "ordinary_non_war")

    def test_enforce_demands_precedes_allowlisted_ordinary_pending(self) -> None:
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
            ),
            action_steps=(
                "reject-pending-character-interaction",
                "enforce-demands-88",
            ),
            active_wars=[
                _war(allied_armies=[], enemy_armies=[], score=100)
            ],
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")
        self.assertNotIn("decision", plan)

    def test_nonallowlisted_definitions_fail_closed_without_special_data(
        self,
    ) -> None:
        for definition_key in (
            "blackmail_interaction",
            "demand_conversion_interaction",
            "fixture_nonreligious_interaction",
            "invite_to_activity_interaction",
            "ransom_me_interaction",
        ):
            with self.subTest(definition_key=definition_key):
                plan = _plan_for_pending_context(
                    _pending_context_result(
                        pending_id=72,
                        revision=6,
                        native_revision=41,
                        date_raw=53_175_816,
                        definition_key=definition_key,
                    ),
                    action_steps=(
                        "accept-pending-character-interaction",
                        "reject-pending-character-interaction",
                    ),
                )

                self.assertIsNone(plan["selected_step"])
                self.assertEqual(
                    plan["decision"]["classification"],
                    "definition_unclassified",
                )
                self.assertFalse(
                    plan["decision"]["definition_classification"][
                        "allowlisted"
                    ]
                )
                self.assertIn(
                    "interaction_definition_not_explicitly_classified_"
                    "nonwar_nonreligious",
                    plan["decision"]["blocked_reasons"],
                )

    def test_planner_accepts_only_the_unique_legal_ordinary_reply(self) -> None:
        legality = {
            "accept": {"status": "available", "allowed": True, "reason": None},
            "reject": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "block": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "ordinary_interaction_not_notification",
            },
        }
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
                legality=legality,
            ),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(
            plan["phase"],
            "pending_character_interaction_degraded_unique_accept",
        )
        self.assertEqual(
            plan["selected_step"], "accept-pending-character-interaction"
        )
        self.assertEqual(plan["decision"]["selected_action"], "accept")

    def test_planner_blocks_accept_when_block_is_also_native_legal(self) -> None:
        legality = {
            "accept": {"status": "available", "allowed": True, "reason": None},
            "reject": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "block": {"status": "available", "allowed": True, "reason": None},
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "ordinary_interaction_not_notification",
            },
        }
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
                legality=legality,
            ),
            action_steps=(
                "accept-pending-character-interaction",
                "block-pending-character-interaction",
            ),
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIsNone(plan["decision"]["selected_action"])
        self.assertIn(
            "accept_not_unique_legal_reply",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_blocks_unclassified_special_interaction(self) -> None:
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
                definition_key="fixture_opaque_special_interaction",
                special_data_present=True,
                special_war_binding={
                    "status": "unavailable",
                    "value": None,
                    "reason": "special_interaction_subtype_opaque",
                },
            ),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertEqual(
            plan["phase"], "pending_character_interaction_degraded_blocked"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["decision"]["classification"], "unclassified_or_special"
        )
        self.assertIn(
            "interaction_war_or_special_semantics_unclassified",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_blocks_same_frame_responder_identity_mismatch(self) -> None:
        context_result = _pending_context_result(
            pending_id=72,
            revision=6,
            native_revision=41,
            date_raw=53_175_816,
        )
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        routing = context["routing"]
        assert isinstance(routing, dict)
        routing["played_character_id"] = 999

        plan = _plan_for_pending_context(
            context_result,
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
            ),
        )

        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["decision"]["classification"], "evidence_invalid")
        self.assertIn(
            "local_responder_identity_mismatch",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_queries_same_frame_terms_for_raiktor_inbound_white_peace(
        self,
    ) -> None:
        war = {
            **_war(
                war_id=33_554_527,
                allied_armies=[],
                enemy_armies=[],
                score=7,
                player_side="attacker",
            ),
            "primary_opponent_character_id": 36_769,
        }
        query_step = query_war_termination_options_step(33_554_527)
        plan = _plan_for_pending_context(
            _raiktor_inbound_white_peace_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                query_step,
                "raise-troops-default",
            ),
            active_wars=[war],
        )

        self.assertEqual(
            plan["phase"], "pending_raiktor_white_peace_termination_query"
        )
        self.assertEqual(plan["selected_step"], query_step)
        decision = plan["decision"]
        self.assertEqual(decision["rule_id"], "raiktor-inbound-white-peace-v1")
        self.assertEqual(
            decision["selected_action"], "observe_war_termination"
        )
        self.assertEqual(
            decision["raiktor_inbound_white_peace"]["status"],
            "query_required",
        )

    def test_planner_accepts_exact_raiktor_inbound_white_peace(self) -> None:
        war = {
            **_war(
                war_id=33_554_527,
                allied_armies=[],
                enemy_armies=[],
                score=7,
                player_side="attacker",
            ),
            "primary_opponent_character_id": 36_769,
        }
        plan = _plan_for_pending_context(
            _raiktor_inbound_white_peace_context_result(),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "block-pending-character-interaction",
            ),
            active_wars=[war],
            termination_options=[
                _raiktor_inbound_white_peace_options(33_554_527)
            ],
        )

        self.assertEqual(plan["phase"], "pending_raiktor_white_peace_accept")
        self.assertEqual(
            plan["selected_step"], "accept-pending-character-interaction"
        )
        decision = plan["decision"]
        self.assertEqual(decision["rule_id"], "raiktor-inbound-white-peace-v1")
        self.assertEqual(decision["selected_action"], "accept")
        self.assertFalse(decision["semantic_optimal"])
        self.assertFalse(decision["semantic_decision_ready"])
        assessment = decision["raiktor_inbound_white_peace"]
        self.assertEqual(assessment["status"], "ready")
        self.assertFalse(
            assessment["evidence"]["outbound_white_peace_available"]
        )
        self.assertEqual(
            assessment["evidence"]["postcondition"],
            "old_pending_full_id_and_bound_war_id_absent",
        )

    def test_planner_blocks_raiktor_white_peace_on_cb_mismatch(self) -> None:
        war = {
            **_war(
                war_id=33_554_527,
                allied_armies=[],
                enemy_armies=[],
                score=7,
                player_side="attacker",
            ),
            "primary_opponent_character_id": 36_769,
        }
        options = _raiktor_inbound_white_peace_options(33_554_527)
        options["active_casus_belli_identity"] = {
            "database_index": 0,
            "canonical_key": "claim_cb",
        }
        plan = _plan_for_pending_context(
            _raiktor_inbound_white_peace_context_result(),
            action_steps=("accept-pending-character-interaction",),
            active_wars=[war],
            termination_options=[options],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "raiktor_white_peace_termination_terms_mismatch",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_blocks_raiktor_white_peace_with_hostage_role(self) -> None:
        context_result = _raiktor_inbound_white_peace_context_result()
        context = context_result["pending_character_interaction_context"]
        assert isinstance(context, dict)
        roles = context["roles"]
        assert isinstance(roles, dict)
        roles["secondary_actor_character_id"] = 40_001
        war = {
            **_war(
                war_id=33_554_527,
                allied_armies=[],
                enemy_armies=[],
                score=7,
                player_side="attacker",
            ),
            "primary_opponent_character_id": 36_769,
        }
        plan = _plan_for_pending_context(
            context_result,
            action_steps=("accept-pending-character-interaction",),
            active_wars=[war],
            termination_options=[
                _raiktor_inbound_white_peace_options(33_554_527)
            ],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "raiktor_white_peace_hostage_or_intermediary_present",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_blocks_raiktor_white_peace_when_accept_is_illegal(
        self,
    ) -> None:
        legality = {
            "accept": {
                "status": "available",
                "allowed": False,
                "reason": "native_reply_not_allowed",
            },
            "reject": {"status": "available", "allowed": True, "reason": None},
            "block": {"status": "available", "allowed": True, "reason": None},
            "acknowledge": {
                "status": "available",
                "allowed": False,
                "reason": "normal_reply_channel",
            },
        }
        war = {
            **_war(
                war_id=33_554_527,
                allied_armies=[],
                enemy_armies=[],
                score=7,
                player_side="attacker",
            ),
            "primary_opponent_character_id": 36_769,
        }
        plan = _plan_for_pending_context(
            _raiktor_inbound_white_peace_context_result(legality=legality),
            action_steps=("accept-pending-character-interaction",),
            active_wars=[war],
            termination_options=[
                _raiktor_inbound_white_peace_options(33_554_527)
            ],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "raiktor_white_peace_accept_not_native_legal",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_keeps_bound_known_war_exit_blocked_without_terms(self) -> None:
        special_binding = {
            "status": "available",
            "value": {
                "special_interaction_kind": "end_war_white_peace_interaction",
                "absolute_outcome": "white_peace",
                "war_id": 88,
                "actor_war_role": "primary_attacker",
                "recipient_war_role": "primary_defender",
                "binding_source": "native_common_war_relation",
            },
            "reason": None,
        }
        war = {
            **_war(
                allied_armies=[],
                enemy_armies=[],
                player_side="defender",
            ),
            "primary_opponent_character_id": 501,
        }
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
                definition_key="end_war_attacker_white_peace_interaction",
                special_data_present=True,
                special_war_binding=special_binding,
            ),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "raise-troops-default",
            ),
            active_wars=[war],
        )

        self.assertEqual(plan["phase"], "pending_war_interaction_evidence_required")
        self.assertIsNone(plan["selected_step"])
        decision = plan["decision"]
        self.assertEqual(decision["classification"], "known_war_exit")
        self.assertIn(
            "special_outcome_terms_unavailable", decision["blocked_reasons"]
        )
        self.assertNotIn(
            "special_war_snapshot_binding_mismatch",
            decision["blocked_reasons"],
        )
        binding = decision["special_war_snapshot_binding"]
        self.assertEqual(binding["war_id"], 88)
        self.assertEqual(binding["snapshot_revision"], 41)
        self.assertEqual(binding["recipient_war_role"], "primary_defender")
        self.assertTrue(binding["active_war_id_match"])
        self.assertTrue(binding["active_war_roles_match"])

    def test_planner_blocks_known_war_exit_on_snapshot_role_mismatch(self) -> None:
        special_binding = {
            "status": "available",
            "value": {
                "special_interaction_kind": "end_war_white_peace_interaction",
                "absolute_outcome": "white_peace",
                "war_id": 88,
                "actor_war_role": "primary_attacker",
                "recipient_war_role": "primary_defender",
                "binding_source": "native_common_war_relation",
            },
            "reason": None,
        }
        mismatched_war = {
            **_war(allied_armies=[], enemy_armies=[], player_side="attacker"),
            "primary_opponent_character_id": 501,
        }
        plan = _plan_for_pending_context(
            _pending_context_result(
                pending_id=72,
                revision=6,
                native_revision=41,
                date_raw=53_175_816,
                definition_key="end_war_attacker_white_peace_interaction",
                special_data_present=True,
                special_war_binding=special_binding,
            ),
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "raise-troops-default",
            ),
            active_wars=[mismatched_war],
        )

        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "special_war_snapshot_binding_mismatch",
            plan["decision"]["blocked_reasons"],
        )

    def test_planner_requeries_stale_pending_context_identity(self) -> None:
        history = [
            {
                "command": "query-pending-character-interaction-context-v1",
                "ok": True,
                "result": _pending_context_result(
                    pending_id=71,
                    revision=6,
                    native_revision=41,
                    date_raw=53_175_816,
                ),
            }
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(6, history),
                "paused": True,
                "native_revision": 41,
                "date_raw": 53_175_816,
                "pending_character_interaction": {
                    "instance_id": 72,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "query-pending-character-interaction-context-v1",
                "accept-pending-character-interaction",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "pending_character_interaction_query")
        self.assertEqual(
            plan["selected_step"],
            "query-pending-character-interaction-context-v1",
        )

    def test_active_war_queries_pending_context_after_enforce_priority(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="regular",
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(7),
                "pending_character_interaction": {
                    "instance_id": 72,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[])
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "query-pending-character-interaction-context-v1",
                "accept-pending-character-interaction",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "pending_war_interaction_query")
        self.assertEqual(
            plan["selected_step"],
            "query-pending-character-interaction-context-v1",
        )

    def test_active_war_does_not_accept_unclassified_pending_interaction(self) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="regular",
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(7),
                "pending_character_interaction": {
                    "instance_id": 72,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[])
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["phase"], "pending_war_interaction_evidence_required"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertIn(
            "game.command.query-war-termination-options-N",
            plan["required_capabilities"],
        )

    def test_enforce_demands_precedes_unclassified_pending_war_interaction(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="regular",
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(7),
                "pending_character_interaction": {
                    "instance_id": 72,
                    "sender_character_id": 501,
                    "auto_accept_notification": False,
                },
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        score=100,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "accept-pending-character-interaction",
                "enforce-demands-88",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")

    def test_native_war_planner_raises_when_no_player_army_exists(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(7),
                "active_wars": [_war(allied_armies=[], enemy_armies=[])],
                "player_armies": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=("raise-troops-default",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_raise")
        self.assertEqual(plan["selected_step"], "raise-troops-default")

    def test_two_army_partial_route_blocks_before_other_unsafe_route(self) -> None:
        unsafe = _army(
            101,
            soldiers=None,
            province_id=20,
            controllable=True,
            move_target_province_id=2604,
            army_state="moving",
            route_province_ids=[31, 2604],
        )
        unavailable = _army(
            202,
            soldiers=None,
            province_id=20,
            controllable=True,
            move_target_province_id=2600,
            army_state="moving",
            route_province_ids=None,
        )
        enemy = _army(
            357, soldiers=None, province_id=31, controllable=False
        )

        plan = _native_war_plan(
            player=unsafe,
            players=[unsafe, unavailable],
            enemies=[enemy],
            score=12,
            date_raw=53_175_984,
            objectives=[2604, 2600],
            steps=(
                "move-army-101-to-2600",
                "merge-armies-101-with-202",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_route_evidence_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["route_evidence_issues"][0]["army_id"], 202)

    def test_hostile_partial_moving_route_blocks_global_matrix(self) -> None:
        player = _army(
            101,
            soldiers=None,
            province_id=2596,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        hostile = _army(
            357,
            soldiers=None,
            province_id=2581,
            controllable=False,
            move_target_province_id=2596,
            army_state="moving",
            army_state_code=7,
            route_province_ids=None,
        )

        plan = _native_war_plan(
            player=player,
            enemies=[hostile],
            score=12,
            date_raw=53_175_984,
            objective=2604,
            steps=("move-army-101-to-2604", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_evidence_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["route_evidence_issues"][0]["role"], "enemy")

    def test_global_route_matrix_catches_nonselected_fourth_cell(self) -> None:
        main = _army(
            101,
            soldiers=2_000,
            province_id=2596,
            controllable=True,
            move_target_province_id=2604,
            army_state="moving",
            route_province_ids=[2604],
        )
        sibling = _army(
            202,
            soldiers=500,
            province_id=2596,
            controllable=True,
            move_target_province_id=2600,
            army_state="moving",
            route_province_ids=[2587, 2600],
        )
        enemies = [
            _army(
                357,
                soldiers=800,
                province_id=2581,
                controllable=False,
                move_target_province_id=2596,
                army_state="moving",
                route_province_ids=[2596],
            ),
            _army(
                33_554_657,
                soldiers=2_400,
                province_id=2581,
                controllable=False,
                move_target_province_id=2587,
                army_state="moving",
                route_province_ids=[2587],
            ),
        ]

        plan = _native_war_plan(
            player=main,
            players=[main, sibling],
            enemies=enemies,
            score=12,
            date_raw=53_175_984,
            objectives=[2604, 2600],
            steps=("preview-move-army-202-to-2604", "life-advance"),
        )

        self.assertNotEqual(plan["selected_step"], "life-advance")
        self.assertIn(
            plan["phase"],
            {
                "native_war_active_route_contact_horizon_unsupported",
                "native_war_route_preview",
                "native_war_no_safe_exact_route",
            },
        )

    def test_live_split_receipt_recovers_original_main_with_unique_delta(
        self,
    ) -> None:
        main = _army(
            83_886_341,
            soldiers=None,
            province_id=2596,
            controllable=True,
            move_target_province_id=2604,
            army_state="moving",
            route_province_ids=[2604],
        )
        sibling = _army(
            16_777_558,
            soldiers=None,
            province_id=2596,
            controllable=True,
            move_target_province_id=2600,
            army_state="moving",
            route_province_ids=[2600],
        )
        enemies = [
            _army(
                357,
                soldiers=None,
                province_id=2581,
                controllable=False,
                move_target_province_id=2596,
                army_state="moving",
                route_province_ids=[2596],
            ),
            _army(
                33_554_657,
                soldiers=None,
                province_id=2581,
                controllable=False,
                move_target_province_id=2587,
                army_state="moving",
                route_province_ids=[2587],
            ),
        ]
        split = {
            "index": 109,
            "command": "split-army-half-83886341",
            "ok": True,
            "result": {
                "war_action": {
                    "status": "split_submitted",
                    "source_army_id": 83_886_341,
                    "submitted_date_raw": 53_175_840,
                    "player_army_ids_before": [83_886_341],
                }
            },
        }

        plan = _native_war_plan(
            player=main,
            players=[main, sibling],
            enemies=enemies,
            score=12,
            date_raw=53_175_984,
            history=[split],
            objectives=[2604, 2600],
            steps=(
                "merge-armies-83886341-with-16777558",
                "split-army-half-83886341",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_merge_recovery")
        self.assertEqual(
            plan["selected_step"],
            "merge-armies-83886341-with-16777558",
        )
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_merge_submission_waits_without_resubmit_or_time(self) -> None:
        main = _army(
            101,
            soldiers=None,
            province_id=20,
            controllable=True,
            route_province_ids=[],
        )
        sibling = _army(
            202,
            soldiers=None,
            province_id=20,
            controllable=True,
            route_province_ids=[],
        )
        history = [
            {
                "index": 1,
                "command": "split-army-half-101",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "split_submitted",
                        "source_army_id": 101,
                        "player_army_ids_before": [101],
                    }
                },
            },
            {
                "index": 2,
                "command": "merge-armies-101-with-202",
                "ok": True,
                "result": {"war_action": {"status": "merge_submitted"}},
            },
        ]

        plan = _native_war_plan(
            player=main,
            players=[main, sibling],
            enemies=[],
            score=12,
            date_raw=24_000,
            history=history,
            objective=77,
            steps=("merge-armies-101-with-202", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_merge_recovery_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["merge_recovery"]["status"], "merge_pending")

        failed_history = [
            history[0],
            {
                **history[1],
                "ok": False,
                "error": "fixture validator rejected merge",
            },
        ]
        failed = _native_war_plan(
            player=main,
            players=[main, sibling],
            enemies=[],
            score=12,
            date_raw=24_000,
            history=failed_history,
            objective=77,
            steps=("merge-armies-101-with-202", "life-advance"),
        )
        self.assertEqual(failed["phase"], "native_war_merge_recovery_blocked")
        self.assertIsNone(failed["selected_step"])
        self.assertEqual(failed["merge_recovery"]["status"], "merge_failed")

    def test_separated_exact_split_pair_requires_safe_rendezvous(self) -> None:
        main = _army(
            101,
            soldiers=None,
            province_id=20,
            controllable=True,
            route_province_ids=[],
        )
        sibling = _army(
            202,
            soldiers=None,
            province_id=31,
            controllable=True,
            route_province_ids=[],
        )
        split = {
            "index": 1,
            "command": "split-army-half-101",
            "ok": True,
            "result": {
                "war_action": {
                    "status": "split_submitted",
                    "source_army_id": 101,
                    "player_army_ids_before": [101],
                }
            },
        }

        plan = _native_war_plan(
            player=main,
            players=[main, sibling],
            enemies=[],
            score=12,
            date_raw=24_000,
            history=[split],
            objective=77,
            steps=("move-army-101-to-77", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_merge_rendezvous_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["merge_recovery"]["status"], "merge_requires_rendezvous"
        )

    def test_post_merge_requires_fresh_preview_and_matching_route(self) -> None:
        main = _army(
            101,
            soldiers=None,
            province_id=20,
            controllable=True,
            move_target_province_id=77,
            army_state="moving",
            route_province_ids=[77],
        )
        split = {
            "index": 2,
            "command": "split-army-half-101",
            "ok": True,
            "result": {
                "war_action": {
                    "status": "split_submitted",
                    "source_army_id": 101,
                    "player_army_ids_before": [101],
                }
            },
        }
        merge = {
            "index": 3,
            "command": "merge-armies-101-with-202",
            "ok": True,
            "result": {"war_action": {"status": "merge_submitted"}},
        }
        old_preview = _preview_row(
            1, army_id=101, origin=20, target=77, date_raw=24_000, route=[77]
        )

        preview_required = _native_war_plan(
            player=main,
            enemies=[],
            score=12,
            date_raw=24_000,
            history=[old_preview, split, merge],
            objective=77,
            steps=("preview-move-army-101-to-77", "life-advance"),
        )
        self.assertEqual(
            preview_required["phase"], "native_war_merge_route_preview"
        )
        self.assertEqual(
            preview_required["selected_step"],
            "preview-move-army-101-to-77",
        )

        fresh = _preview_row(
            4, army_id=101, origin=20, target=77, date_raw=24_000, route=[77]
        )
        progress = _native_war_plan(
            player=main,
            enemies=[],
            score=12,
            date_raw=24_000,
            history=[old_preview, split, merge, fresh],
            objective=77,
            steps=("preview-move-army-101-to-77", "life-advance"),
        )
        self.assertEqual(progress["phase"], "native_war_merge_route_progress")
        self.assertEqual(progress["selected_step"], "life-advance")

        mismatched = _preview_row(
            4,
            army_id=101,
            origin=20,
            target=77,
            date_raw=24_000,
            route=[31, 77],
        )
        blocked = _native_war_plan(
            player=main,
            enemies=[],
            score=12,
            date_raw=24_000,
            history=[old_preview, split, merge, mismatched],
            objective=77,
            steps=("preview-move-army-101-to-77", "life-advance"),
        )
        self.assertEqual(
            blocked["phase"], "native_war_merge_route_refresh_blocked"
        )
        self.assertIsNone(blocked["selected_step"])

    def test_merge_barrier_discards_old_deferred_move_backoff(self) -> None:
        main = _army(
            101,
            soldiers=None,
            province_id=20,
            controllable=True,
            route_province_ids=[],
        )
        history = [
            {
                "index": 1,
                "command": "move-army-101-to-77",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "move_deferred",
                        "submitted_date_raw": 24_000,
                    }
                },
            },
            {
                "index": 2,
                "command": "split-army-half-101",
                "ok": True,
                "result": {
                    "war_action": {
                        "status": "split_submitted",
                        "source_army_id": 101,
                        "player_army_ids_before": [101],
                    }
                },
            },
            {
                "index": 3,
                "command": "merge-armies-101-with-202",
                "ok": True,
                "result": {"war_action": {"status": "merge_submitted"}},
            },
        ]

        plan = _native_war_plan(
            player=main,
            enemies=[],
            score=12,
            date_raw=24_024,
            history=history,
            objective=77,
            move_route_preview_supported=False,
            steps=("move-army-101-to-77", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-101-to-77")

    def test_all_army_battle_query_precedes_stronger_safe_route(self) -> None:
        stronger = _army(
            101,
            soldiers=2_000,
            province_id=20,
            controllable=True,
            move_target_province_id=77,
            army_state="moving",
            route_province_ids=[77],
        )
        weaker = _army(
            202,
            soldiers=500,
            province_id=31,
            controllable=True,
            army_state="combat",
            army_state_code=2,
            route_province_ids=[],
        )

        plan = _native_war_plan(
            player=stronger,
            players=[stronger, weaker],
            enemies=[],
            score=12,
            date_raw=24_000,
            objective=77,
            steps=(
                "move-army-101-to-77",
                "query-battle-control-snapshot-v1-202",
                "life-advance",
            ),
        )

        self.assertEqual(
            plan["phase"], "native_war_battle_control_query"
        )
        self.assertEqual(
            plan["selected_step"],
            "query-battle-control-snapshot-v1-202",
        )
        self.assertEqual(plan["battle_subject_army_id"], 202)

    def test_cross_war_enforce_precedes_active_combat_query(self) -> None:
        combat = _army(
            202,
            soldiers=500,
            province_id=31,
            controllable=True,
            army_state="combat",
            army_state_code=2,
            route_province_ids=[],
        )
        enemy = _army(
            303, soldiers=450, province_id=31, controllable=False
        )
        snapshot = {
            **_snapshot(8),
            "active_wars": [
                _war(
                    war_id=88,
                    allied_armies=[combat],
                    enemy_armies=[enemy],
                    score=12,
                ),
                _war(
                    war_id=99,
                    allied_armies=[],
                    enemy_armies=[],
                    score=100,
                ),
            ],
            "player_armies": [combat],
        }

        plan = choose_one_life_turn(
            [],
            snapshot=snapshot,
            action_steps=(
                "enforce-demands-99",
                "query-battle-control-snapshot-v1-202",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-99")

    def test_missing_cross_war_enforce_literal_blocks_combat_query(self) -> None:
        combat = _army(
            202,
            soldiers=500,
            province_id=31,
            controllable=True,
            army_state="combat",
            army_state_code=2,
            route_province_ids=[],
        )
        enemy = _army(
            303, soldiers=450, province_id=31, controllable=False
        )
        snapshot = {
            **_snapshot(8),
            "active_wars": [
                _war(
                    war_id=88,
                    allied_armies=[combat],
                    enemy_armies=[enemy],
                    score=12,
                ),
                _war(
                    war_id=99,
                    allied_armies=[],
                    enemy_armies=[],
                    score=100,
                ),
            ],
            "player_armies": [combat],
        }

        plan = choose_one_life_turn(
            [],
            snapshot=snapshot,
            action_steps=(
                "query-battle-control-snapshot-v1-202",
                "life-advance",
            ),
        )

        self.assertEqual(
            plan["phase"], "native_war_enforce_demands_unsupported"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["required_step"], "enforce-demands-99")
        self.assertNotEqual(
            plan.get("required_step"),
            "query-battle-control-snapshot-v1-202",
        )

    def test_battle_query_precedes_other_armys_urgent_reroute(self) -> None:
        stronger = _army(
            101,
            soldiers=2_000,
            province_id=20,
            controllable=True,
            move_target_province_id=77,
            army_state="moving",
            route_province_ids=[31, 77],
        )
        weaker = _army(
            202,
            soldiers=500,
            province_id=40,
            controllable=True,
            army_state="combat",
            army_state_code=2,
            route_province_ids=[],
        )
        enemy = _army(
            357, soldiers=None, province_id=31, controllable=False
        )

        plan = _native_war_plan(
            player=stronger,
            players=[stronger, weaker],
            enemies=[enemy],
            score=12,
            date_raw=24_000,
            objectives=[77, 88],
            steps=(
                "preview-move-army-101-to-88",
                "query-battle-control-snapshot-v1-202",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_battle_control_query")
        self.assertEqual(
            plan["selected_step"],
            "query-battle-control-snapshot-v1-202",
        )
        self.assertNotEqual(plan["selected_step"], "life-advance")

    def test_native_war_planner_does_not_chase_largest_visible_enemy(self) -> None:
        player = _army(
            11, soldiers=1_700, province_id=20, controllable=True
        )
        smaller = _army(
            21, soldiers=800, province_id=31, controllable=False
        )
        larger = _army(
            22, soldiers=2_400, province_id=32, controllable=False
        )
        step = "move-army-11-to-32"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(8),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[smaller, larger],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(step,),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])
        self.assertNotIn("pursuit", plan)

    def test_native_war_planner_never_uses_soldiers_as_combat_prediction(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy_22 = _army(
            22, soldiers=None, province_id=42, controllable=False
        )
        enemy_21 = _army(
            21, soldiers=None, province_id=41, controllable=False
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy_22, enemy_21],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_zero_score_attacker_holds_without_exact_objective(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=0,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-41",
                "move-army-11-to-77",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_zero_score_attacker_uses_exact_objective_before_enemy(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            steps=(
                "move-army-11-to-41",
                "move-army-11-to-2585",
                "move-army-11-to-2543",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["objective_kind"], "siege")
        self.assertEqual(plan["pursuit"]["target_source"], "war_objective_province")

    def test_positive_score_attacker_does_not_infer_same_province_battle(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-77", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_positive_score_attacker_does_not_use_rally_as_exact_objective(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-41",
                "move-army-11-to-77",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_attacker_at_rally_fallback_holds_without_exact_objective(self) -> None:
        player = _army(11, soldiers=900, province_id=77, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=42, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-42", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_exact_war_objective_precedes_legacy_rally_fallback(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            steps=("move-army-11-to-2585", "move-army-11-to-2543"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["target_source"], "war_objective_province")

    def test_exact_war_objectives_preserve_native_dfs_order(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510, 2548, 2585],
            fallback=2543,
            steps=(
                "move-army-11-to-2585",
                "move-army-11-to-2510",
                "move-army-11-to-2548",
            ),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2585)

    def test_completed_exact_objective_does_not_rotate_to_legacy_fallback(self) -> None:
        sieging = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        idle = _army(11, soldiers=900, province_id=2585, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        before = _war_progress(
            24_000, player=sieging, enemies=[enemy], score=24,
            objectives=[2585], fallback=2543,
        )
        after = _war_progress(
            24_168, player=idle, enemies=[enemy], score=30,
            objectives=[2585], fallback=2543,
        )

        plan = _native_war_plan(
            player=idle, enemies=[enemy], score=30, date_raw=24_168,
            history=[_advance_row(1, before, after)],
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "move-army-11-to-2543"),
        )

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_completed_objectives_do_not_rotate_to_enemy_or_rally(self) -> None:
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        exact_siege = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        exact_done = _army(11, soldiers=900, province_id=2585, controllable=True)
        fallback_siege = _army(
            11, soldiers=900, province_id=2543, controllable=True,
            army_state="sieging",
        )
        fallback_done = _army(11, soldiers=900, province_id=2543, controllable=True)
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000, player=exact_siege, enemies=[enemy], score=24,
                    objectives=[2585], fallback=2543,
                ),
                _war_progress(
                    24_168, player=exact_done, enemies=[enemy], score=30,
                    objectives=[2585], fallback=2543,
                ),
            ),
            _advance_row(
                2,
                _war_progress(
                    24_168, player=fallback_siege, enemies=[enemy], score=30,
                    objectives=[2585], fallback=2543,
                ),
                _war_progress(
                    24_336, player=fallback_done, enemies=[enemy], score=36,
                    objectives=[2585], fallback=2543,
                ),
            ),
        ]

        plan = _native_war_plan(
            player=fallback_done, enemies=[enemy], score=36, date_raw=24_336,
            history=history, objective=2585, fallback=2543,
            steps=("move-army-11-to-41", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

        waiting = _native_war_plan(
            player=fallback_done,
            enemies=[],
            score=36,
            date_raw=24_336,
            history=history,
            objective=2585,
            fallback=2543,
            steps=("life-advance",),
        )
        self.assertEqual(waiting["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(waiting["selected_step"])

    def test_exact_siege_state_keeps_advancing_current_objective(self) -> None:
        player = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player, enemies=[], score=24, date_raw=24_000,
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_siege_progress")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_exact_player_siege_uses_authoritative_progress_state(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=650,
                    besieging_strength=650,
                    active_siege=_active_siege(),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_siege_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["status"], "progressing")

    def test_breached_safe_exact_siege_starts_assault(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        active_siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=False,
            can_start_assault=True,
            can_stop_assault=False,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=active_siege,
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("start-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_assault_start")
        self.assertEqual(plan["selected_step"], "start-assault-901")
        self.assertTrue(plan["assault_state"]["one_day_safe"])
        self.assertEqual(
            plan["assault_state"]["projection_horizon_days"], 1
        )
        self.assertNotIn("eta", str(plan).casefold())

    def test_assault_start_is_blocked_by_unsafe_active_siege_route(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            move_target_province_id=2600,
            army_state="sieging",
            route_province_ids=[2590, 2600],
        )
        enemy = _army(
            21,
            soldiers=700,
            province_id=2590,
            controllable=False,
            army_state="regular",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=False,
                        can_start_assault=True,
                        can_stop_assault=False,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            army_routes_supported=True,
            move_route_preview_supported=False,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=(
                "start-assault-901",
                "move-army-11-to-2590",
                "life-advance",
            ),
        )

        self.assertNotEqual(plan["phase"], "native_war_assault_start")
        self.assertNotEqual(plan["selected_step"], "start-assault-901")

    def test_moving_army_without_route_target_blocks_assault_and_time(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="moving",
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=False,
                        can_start_assault=True,
                        can_stop_assault=False,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            army_routes_supported=True,
            move_route_preview_supported=False,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("start-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_evidence_blocked")
        self.assertIsNone(plan["selected_step"])

    def test_moving_state_code_without_route_target_blocks_assault_and_time(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state_code=7,
            route_province_ids=[],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=False,
                        can_start_assault=True,
                        can_stop_assault=False,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            army_routes_supported=True,
            move_route_preview_supported=False,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("start-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_route_evidence_blocked")
        self.assertIsNone(plan["selected_step"])

    def test_started_assault_lifecycle_blocks_missing_rich_row_direct_and_decorated(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        for decorated in (False, True):
            with self.subTest(decorated=decorated):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_000,
                    history=[
                        _assault_action_row(
                            1,
                            status="assault_started",
                            decorated=decorated,
                        )
                    ],
                    objective=2585,
                    objective_states=[],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("life-advance",),
                )

                self.assertEqual(
                    plan["phase"], "native_war_assault_lifecycle_blocked"
                )
                self.assertIsNone(plan["selected_step"])
                self.assertEqual(
                    plan["assault_lifecycles"][0]["reason"],
                    "objective_row_unavailable_after_start",
                )

    def test_enforce_demands_precedes_unobservable_started_assault_lifecycle(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=100,
            date_raw=24_000,
            history=[_assault_action_row(1, status="assault_started")],
            objective=2585,
            objective_states=[],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("enforce-demands-88", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")

    def test_started_assault_lifecycle_closes_on_exact_no_siege_stop_or_restore(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        cases = {
            "exact_no_siege": {
                "history": [
                    _assault_action_row(1, status="assault_started")
                ],
                "states": [_objective_state(2585, active_siege=None)],
            },
            "stopped": {
                "history": [
                    _assault_action_row(1, status="assault_started"),
                    _assault_action_row(2, status="assault_stopped"),
                ],
                "states": [],
            },
            "restored": {
                "history": [
                    _assault_action_row(1, status="assault_started"),
                    {
                        "index": 2,
                        "command": "restore-checkpoint",
                        "ok": True,
                        "result": {"status": "restored"},
                    },
                ],
                "states": [],
            },
        }
        for name, case in cases.items():
            with self.subTest(case=name):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_000,
                    history=case["history"],
                    objective=2585,
                    objective_states=case["states"],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("life-advance",),
                )

                self.assertNotEqual(
                    plan["phase"], "native_war_assault_lifecycle_blocked"
                )

    def test_failed_assault_slice_stops_direct_and_decorated_history(self) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        active_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=_active_siege(
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=16,
            ),
        )
        for decorated in (False, True):
            with self.subTest(decorated=decorated):
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_024,
                    history=[
                        _assault_action_row(
                            1,
                            status="assault_started",
                            decorated=decorated,
                        ),
                        _failed_life_advance_row(
                            2, decorated=decorated
                        ),
                    ],
                    objective=2585,
                    objective_states=[active_state],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("stop-assault-901", "life-advance"),
                )

                self.assertEqual(plan["selected_step"], "stop-assault-901")
                self.assertIn(
                    "previous_assault_slice_failed_unknown",
                    plan["assault_state"]["one_day_rejection_reasons"],
                )

    def test_assault_start_requires_breach_native_gate_and_one_day_budget(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        cases = (
            {
                "name": "intact",
                "breach_level": 0,
                "can_start": True,
                "casualties": 16,
            },
            {
                "name": "validator",
                "breach_level": 1,
                "can_start": False,
                "casualties": 16,
            },
            {
                "name": "casualties",
                "breach_level": 1,
                "can_start": True,
                "casualties": 151,
            },
        )
        for case in cases:
            with self.subTest(case=case["name"]):
                active_siege = _active_siege(
                    assault_observable=True,
                    breach_level=int(case["breach_level"]),
                    assault_in_progress=False,
                    can_start_assault=bool(case["can_start"]),
                    can_stop_assault=False,
                    assault_daily_progress_raw=340_000,
                    assault_daily_casualties=int(case["casualties"]),
                )
                plan = _native_war_plan(
                    player=player,
                    enemies=[],
                    score=24,
                    date_raw=24_000,
                    objective=2585,
                    objective_states=[
                        _objective_state(
                            2585,
                            garrison_size=500,
                            besieging_strength=650,
                            active_siege=active_siege,
                        )
                    ],
                    occupation_supported=True,
                    garrison_supported=True,
                    siege_progress_supported=True,
                    assault_supported=True,
                    steps=("start-assault-901", "life-advance"),
                )

                self.assertNotEqual(
                    plan["selected_step"], "start-assault-901"
                )

    def test_active_assault_advances_one_day_then_stops_when_unsafe(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )

        def assault(casualties: int) -> dict[str, object]:
            return _active_siege(
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=casualties,
            )

        safe = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=assault(16),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )
        self.assertEqual(safe["phase"], "native_war_assault_daily_progress")
        self.assertEqual(safe["selected_step"], "life-advance")
        self.assertEqual(safe["assault_state"]["projection_horizon_days"], 1)

        unsafe = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=assault(151),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )
        self.assertEqual(unsafe["phase"], "native_war_assault_stop")
        self.assertEqual(unsafe["selected_step"], "stop-assault-901")
        self.assertIn(
            "projected_strength_below_garrison",
            unsafe["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_stops_before_observed_enemy_convergence(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        enemy = _army(
            21,
            soldiers=900,
            province_id=2600,
            controllable=False,
            move_target_province_id=2585,
            route_province_ids=[2590, 2585],
            army_state="moving",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=650,
                    active_siege=_active_siege(
                        assault_observable=True,
                        breach_level=1,
                        assault_in_progress=True,
                        can_start_assault=False,
                        can_stop_assault=True,
                        assault_daily_progress_raw=340_000,
                        assault_daily_casualties=16,
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertIn(
            "enemy_convergence_observed",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_rechecks_realized_daily_progress_and_losses(
        self,
    ) -> None:
        before_player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        after_player = _army(
            11,
            soldiers=634,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        active_siege = _active_siege(
            assault_observable=True,
            breach_level=1,
            assault_in_progress=True,
            can_start_assault=False,
            can_stop_assault=True,
            assault_daily_progress_raw=340_000,
            assault_daily_casualties=16,
        )
        state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=active_siege,
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=before_player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[state],
                ),
                _war_progress(
                    24_024,
                    player=after_player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[state],
                ),
            )
        ]
        plan = _native_war_plan(
            player=after_player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertEqual(
            plan["assault_state"]["previous_assault_day"]["soldier_loss"],
            16,
        )
        self.assertEqual(
            plan["assault_state"]["previous_assault_day"]["strength_loss"],
            0,
        )
        self.assertIn(
            "previous_assault_day_no_work_progress",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_continues_from_realized_strength_with_null_soldiers(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=650,
            active_siege=_active_siege(
                current_work_raw=2_500_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            ),
        )
        after_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=_active_siege(
                current_work_raw=2_840_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=16,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_assault_daily_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        previous_day = plan["assault_state"]["previous_assault_day"]
        self.assertEqual(previous_day["strength_loss"], 16)
        self.assertIsNone(previous_day["soldier_loss"])
        self.assertTrue(plan["assault_state"]["one_day_safe"])

    def test_active_assault_stops_when_realized_strength_is_unavailable(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=None,
            active_siege=_active_siege(
                current_work_raw=2_500_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            ),
        )
        after_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=634,
            active_siege=_active_siege(
                current_work_raw=2_840_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=16,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertIn(
            "previous_assault_day_strength_change_unavailable",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_active_assault_stops_after_strength_falls_below_garrison(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=650,
            active_siege=_active_siege(
                current_work_raw=2_500_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=340_000,
                assault_daily_casualties=16,
            ),
        )
        after_state = _objective_state(
            2585,
            garrison_size=500,
            besieging_strength=499,
            active_siege=_active_siege(
                current_work_raw=2_840_000,
                assault_observable=True,
                breach_level=1,
                assault_in_progress=True,
                can_start_assault=False,
                can_stop_assault=True,
                assault_daily_progress_raw=330_000,
                assault_daily_casualties=4,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_024,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_024,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("stop-assault-901", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "stop-assault-901")
        self.assertEqual(
            plan["assault_state"]["previous_assault_day"]["strength_loss"],
            151,
        )
        self.assertIn(
            "projected_strength_below_garrison",
            plan["assault_state"]["one_day_rejection_reasons"],
        )

    def test_advertised_but_unobservable_assault_state_blocks_time(self) -> None:
        player = _army(
            11,
            soldiers=650,
            province_id=2585,
            controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objective=2585,
            objective_states=[
                _objective_state(
                    2585,
                    active_siege=_active_siege(
                        assault_observable=False
                    ),
                )
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(
            plan["phase"], "native_war_assault_observation_blocked"
        )
        self.assertIsNone(plan["selected_step"])

    def test_occupation_only_capability_keeps_legacy_siege_stickiness(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(2585, fort_level=3),
                _objective_state(2510, fort_level=1),
            ],
            occupation_supported=True,
            fort_level_supported=True,
            siege_progress_supported=False,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_siege_progress")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_insufficient_exact_siege_strength_moves_to_next_objective(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=499,
                    active_siege=_active_siege(),
                ),
                _objective_state(
                    2510,
                    garrison_size=300,
                    besieging_strength=0,
                ),
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_insufficient_only_siege_uses_fresh_safe_capital_regroup(
        self,
    ) -> None:
        date_raw = 24_000
        player = _army(
            11,
            soldiers=None,
            province_id=52,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemies = [
            _army(
                21,
                soldiers=600,
                province_id=54,
                controllable=False,
                move_target_province_id=52,
                army_state="moving",
                route_province_ids=[16, 52],
            ),
            _army(
                22,
                soldiers=700,
                province_id=16,
                controllable=False,
                move_target_province_id=52,
                army_state="moving",
                route_province_ids=[52],
            ),
        ]
        objective_state = _objective_state(
            52,
            garrison_size=400,
            besieging_strength=399,
            active_siege=_active_siege(
                army_id=11,
                assault_observable=True,
                breach_level=2,
                assault_in_progress=False,
                can_start_assault=False,
                can_stop_assault=False,
            ),
        )
        base = {
            "player": player,
            "enemies": enemies,
            "score": 10,
            "date_raw": date_raw,
            "objective": 52,
            "objective_states": [objective_state],
            "occupation_supported": True,
            "garrison_supported": True,
            "siege_progress_supported": True,
            "assault_supported": True,
        }

        query = _native_war_plan(
            **base,
            steps=("query-campaign-root-context-v1", "life-advance"),
        )
        self.assertEqual(query["phase"], "native_war_capital_regroup_context")
        self.assertEqual(
            query["selected_step"], "query-campaign-root-context-v1"
        )

        root = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=45
        )
        preview = _native_war_plan(
            **base,
            history=[root],
            steps=("preview-move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(preview["phase"], "native_war_capital_regroup_preview")
        self.assertEqual(
            preview["selected_step"], "preview-move-army-11-to-45"
        )

        preview_row = _preview_row(
            2,
            army_id=11,
            origin=52,
            target=45,
            date_raw=date_raw,
            route=[51, 45],
        )
        move = _native_war_plan(
            **base,
            history=[root, preview_row],
            steps=("move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(move["selected_step"], "move-army-11-to-45")
        self.assertEqual(
            move["pursuit"]["target_source"], "player_capital_regroup"
        )
        self.assertEqual(move["pursuit"]["objective_kind"], "regroup")

    def test_capital_regroup_stale_or_unsafe_evidence_fails_closed(
        self,
    ) -> None:
        date_raw = 24_000
        player = _army(
            11,
            soldiers=None,
            province_id=52,
            controllable=True,
            army_state="sieging",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=600,
            province_id=51,
            controllable=False,
            move_target_province_id=45,
            army_state="moving",
            route_province_ids=[45],
        )
        objective_state = _objective_state(
            52,
            garrison_size=400,
            besieging_strength=399,
            active_siege=_active_siege(
                army_id=11,
                assault_observable=True,
                assault_in_progress=False,
                can_start_assault=False,
                can_stop_assault=False,
            ),
        )
        base = {
            "player": player,
            "enemies": [enemy],
            "score": 10,
            "date_raw": date_raw,
            "objective": 52,
            "objective_states": [objective_state],
            "occupation_supported": True,
            "garrison_supported": True,
            "siege_progress_supported": True,
            "assault_supported": True,
            "route_contact_horizon_supported": True,
        }
        stale_root = _campaign_root_row(
            1, date_raw=date_raw - 24, capital_province_id=45
        )
        stale = _native_war_plan(
            **base,
            history=[stale_root],
            steps=("query-campaign-root-context-v1", "life-advance"),
        )
        self.assertEqual(stale["phase"], "native_war_capital_regroup_context")
        self.assertEqual(
            stale["selected_step"], "query-campaign-root-context-v1"
        )

        root = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=45
        )
        preview = _preview_row(
            2,
            army_id=11,
            origin=52,
            target=45,
            date_raw=date_raw,
            route=[51, 45],
        )
        horizon_step = query_route_contact_horizon_step(11, 45, (21,))
        query_horizon = _native_war_plan(
            **base,
            history=[root, preview],
            steps=(horizon_step, "life-advance"),
        )
        self.assertEqual(
            query_horizon["phase"],
            "native_war_capital_regroup_contact_horizon",
        )
        self.assertEqual(query_horizon["selected_step"], horizon_step)

        unsafe_horizon = _route_contact_row(
            3,
            army_id=11,
            origin=52,
            target=45,
            date_raw=date_raw,
            route=[51, 45],
            hostile_ids=(21,),
            contact_free=False,
        )
        blocked = _native_war_plan(
            **base,
            history=[root, preview, unsafe_horizon],
            steps=("move-army-11-to-45", "life-advance"),
        )
        self.assertEqual(blocked["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(blocked["selected_step"])

    def test_capital_regroup_arrival_holds_before_turning_back(self) -> None:
        date_raw = 24_024
        player = _army(
            11,
            soldiers=399,
            province_id=45,
            controllable=True,
            army_state="regular",
            route_province_ids=[],
        )
        enemy = _army(
            21,
            soldiers=600,
            province_id=54,
            controllable=False,
            move_target_province_id=52,
            army_state="moving",
            route_province_ids=[16, 52],
        )
        root = _campaign_root_row(
            1, date_raw=24_000, capital_province_id=45
        )
        preview = _preview_row(
            2,
            army_id=11,
            origin=52,
            target=45,
            date_raw=24_000,
            route=[51, 45],
        )
        move = {
            "index": 3,
            "command": "move-army-11-to-45",
            "ok": True,
            "result": {
                "accepted": True,
                "war_action": {
                    "status": "moving",
                    "army_id": 11,
                    "target_province_id": 45,
                    "submitted_date_raw": 24_000,
                },
            },
        }
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=10,
            date_raw=date_raw,
            history=[root, preview, move],
            objective=52,
            objective_states=[_objective_state(52, active_siege=None)],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            assault_supported=True,
            steps=("preview-move-army-11-to-52", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_capital_regroup_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["regroup_intent"]["capital_province_id"], 45
        )

    def test_exhausted_attacker_already_at_capital_waits_for_war_end(
        self,
    ) -> None:
        date_raw = 24_000
        players = [
            _army(
                army_id,
                soldiers=None,
                province_id=45,
                controllable=True,
                army_state="regular",
                route_province_ids=[],
            )
            for army_id in (11, 12, 13, 14)
        ]
        enemies = [
            _army(
                army_id,
                soldiers=600,
                province_id=52,
                controllable=False,
                army_state="regular",
                route_province_ids=[],
            )
            for army_id in (21, 22, 23, 24)
        ]
        root = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=45
        )
        objective_state = _objective_state(
            52,
            garrison_size=900,
            besieging_strength=0,
            active_siege=None,
        )
        active_war = _war(
            allied_armies=players,
            enemy_armies=enemies,
            score=-47,
            war_objective_province_ids=[52],
            objective_province_states=[objective_state],
        )
        queried_snapshot = {
            **_snapshot(90),
            "paused": True,
            "map_ready": True,
            "army_routes_supported": True,
            "move_route_preview_supported": True,
            "route_contact_horizon_supported": False,
            "native_revision": 90,
            "date_raw": date_raw,
            "episode_run_id": None,
            "diagnostics": {"connection_generation": 1},
            "played_character": {"character_id": 707, "alive": True},
            "active_wars": [active_war],
            "player_armies": players,
            "war_objective_occupation_supported": True,
            "war_objective_fort_level_supported": False,
            "war_objective_garrison_supported": True,
            "war_objective_siege_progress_supported": True,
            "war_objective_assault_supported": True,
            "war_termination_options": [],
        }
        negative_options = _termination_options(score=-47)
        for option in negative_options["options"].values():
            option["available"] = False
            option["native_validator_passed"] = False
            option["auto_accept"] = False
        queried_snapshot["war_termination_options"] = [{
            **negative_options,
            "queried_snapshot_id": queried_snapshot["snapshot_id"],
            "queried_revision": queried_snapshot["revision"],
            "queried_native_revision": queried_snapshot["native_revision"],
            "queried_connection_generation": 1,
            "episode_run_id": queried_snapshot["episode_run_id"],
        }]
        blocked_preview = _preview_row(
            2,
            army_id=11,
            origin=45,
            target=52,
            date_raw=date_raw,
            route=[],
        )
        history = [root, blocked_preview]
        queried_snapshot["history"] = history
        queried_snapshot["native_command_history"] = history
        plan = choose_one_life_turn(
            history,
            snapshot=queried_snapshot,
            action_steps=("query-war-termination-options-88", "life-advance"),
        )

        self.assertEqual(
            plan["phase"], "native_war_capital_regroup_hold_progress", plan
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["capital_province_id"], 45)

    def test_rejected_exact_siege_does_not_advance_deferred_preview(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging", route_province_ids=[],
        )
        states = [
            _objective_state(
                2585,
                garrison_size=500,
                besieging_strength=499,
                active_siege=_active_siege(),
            ),
            _objective_state(2510, besieging_strength=0),
        ]
        deferred_preview = {
            "index": 1,
            "command": "preview-move-army-11-to-2510",
            "ok": True,
            "result": {
                "accepted": True,
                "route_preview": {
                    "status": "deferred",
                    "army_id": 11,
                    "origin_province_id": 2585,
                    "target_province_id": 2510,
                    "previewed_date_raw": 24_000,
                },
            },
        }
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            history=[deferred_preview],
            objectives=[2585, 2510],
            objective_states=states,
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("preview-move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["route_rejections"][-1]["status"],
            "deferred_while_exact_siege_rejected",
        )

    def test_rejected_exact_siege_does_not_advance_move_backoff(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        deferred_move = {
            "index": 1,
            "command": "move-army-11-to-2510",
            "ok": True,
            "result": {
                "accepted": False,
                "war_action": {
                    "status": "move_deferred",
                    "army_id": 11,
                    "target_province_id": 2510,
                    "submitted_date_raw": 24_000,
                },
            },
        }
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_000,
            history=[deferred_move],
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(
                    2585,
                    garrison_size=500,
                    besieging_strength=499,
                    active_siege=_active_siege(),
                ),
                _objective_state(2510, besieging_strength=0),
            ],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_siege_exit_blocked")
        self.assertIsNone(plan["selected_step"])
        self.assertFalse(plan["move_backoff"]["retry_due"])

    def test_seven_day_exact_siege_stall_moves_to_next_objective(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        active = _objective_state(
            2585,
            active_siege=_active_siege(),
        )
        other = _objective_state(2510, besieging_strength=0)
        before = _war_progress(
            24_000,
            player=player,
            enemies=[],
            score=24,
            objectives=[2585, 2510],
            objective_states=[active, other],
        )
        after = _war_progress(
            24_168,
            player=player,
            enemies=[],
            score=24,
            objectives=[2585, 2510],
            objective_states=[active, other],
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_168,
            history=[_advance_row(1, before, after)],
            objectives=[2585, 2510],
            objective_states=[active, other],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_exact_siege_work_progress_resets_stall(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        before_state = _objective_state(
            2585,
            active_siege=_active_siege(),
        )
        after_state = _objective_state(
            2585,
            active_siege=_active_siege(
                progress_raw=32_000,
                current_work_raw=3_200_000,
            ),
        )
        history = [
            _advance_row(
                1,
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[before_state],
                ),
                _war_progress(
                    24_168,
                    player=player,
                    enemies=[],
                    score=24,
                    objectives=[2585],
                    objective_states=[after_state],
                ),
            )
        ]
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_168,
            history=history,
            objective=2585,
            objective_states=[after_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["stall_days"], 0)

    def test_exact_siege_stall_requires_uninterrupted_player_control(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        player_state = _objective_state(
            2585, active_siege=_active_siege()
        )
        ally_state = _objective_state(
            2585,
            active_siege=_active_siege(army_id=12, player=False),
        )

        def progress(
            date_raw: int,
            states: list[dict[str, object]],
        ) -> dict[str, object]:
            return _war_progress(
                date_raw,
                player=player,
                enemies=[],
                score=24,
                objectives=[2585, 2510],
                objective_states=states,
            )

        history = [
            _advance_row(1, progress(24_000, [player_state]),
                         progress(24_096, [player_state])),
            _advance_row(2, progress(24_096, []), progress(24_120, [])),
            _advance_row(3, progress(24_120, [ally_state]),
                         progress(24_216, [ally_state])),
            _advance_row(4, progress(24_216, [player_state]),
                         progress(24_312, [player_state])),
        ]
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_312,
            history=history,
            objectives=[2585, 2510],
            objective_states=[player_state, _objective_state(2510)],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["stall_days"], 4)

    def test_exact_siege_combat_interrupt_resets_stall(self) -> None:
        siege_army = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        combat_army = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="combat",
        )
        siege_state = _objective_state(
            2585, active_siege=_active_siege()
        )

        def progress(
            date_raw: int, player: dict[str, object]
        ) -> dict[str, object]:
            return _war_progress(
                date_raw,
                player=player,
                enemies=[],
                score=24,
                objectives=[2585],
                objective_states=[siege_state],
            )

        history = [
            _advance_row(
                1,
                progress(24_000, siege_army),
                progress(24_192, siege_army),
            ),
            _advance_row(
                2,
                progress(24_192, combat_army),
                progress(24_336, siege_army),
            ),
        ]
        plan = _native_war_plan(
            player=siege_army,
            enemies=[],
            score=47,
            date_raw=24_336,
            history=history,
            objective=2585,
            objective_states=[siege_state],
            occupation_supported=True,
            garrison_supported=True,
            siege_progress_supported=True,
            steps=("life-advance",),
        )

        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["siege_state"]["stall_days"], 0)

    def test_player_occupied_exact_objective_is_skipped(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="regular",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=24_000,
            objectives=[2585, 2510],
            objective_states=[
                _objective_state(2585, occupant=707),
                _objective_state(2510),
            ],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2510", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_mixed_exact_occupation_overrides_legacy_per_province(
        self,
    ) -> None:
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        siege_2585 = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        siege_2510 = _army(
            11, soldiers=900, province_id=2510, controllable=True,
            army_state="sieging",
        )
        idle_2585 = _army(
            11, soldiers=900, province_id=2585, controllable=True
        )
        idle_2510 = _army(
            11, soldiers=900, province_id=2510, controllable=True
        )
        current = _army(
            11, soldiers=900, province_id=2600, controllable=True,
            army_state="regular",
        )
        history = [
            _advance_row(
                1,
                _war_progress(24_000, player=siege_2585, enemies=[enemy],
                              score=24, objectives=[2585, 2510]),
                _war_progress(24_168, player=idle_2585, enemies=[enemy],
                              score=30, objectives=[2585, 2510]),
            ),
            _advance_row(
                2,
                _war_progress(24_168, player=siege_2510, enemies=[enemy],
                              score=30, objectives=[2585, 2510]),
                _war_progress(24_336, player=idle_2510, enemies=[enemy],
                              score=36, objectives=[2585, 2510]),
            ),
        ]
        unknown = _objective_state(
            2585,
            occupation_observable=False,
            fort_level=None,
            garrison_size=None,
            besieging_strength=None,
            siege_observable=False,
        )
        lost = _objective_state(
            2510,
            fort_level=None,
            garrison_size=None,
            besieging_strength=None,
            siege_observable=False,
        )

        plan = _native_war_plan(
            player=current,
            enemies=[enemy],
            score=36,
            date_raw=24_336,
            history=history,
            objectives=[2585, 2510],
            objective_states=[unknown, lost],
            occupation_supported=True,
            steps=("move-army-11-to-2585", "move-army-11-to-2510"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2510")
        self.assertEqual(plan["pursuit"]["target_province_id"], 2510)

    def test_all_exact_objectives_occupied_does_not_use_rally_fallback(
        self,
    ) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="regular",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            objective_states=[_objective_state(2585, occupant=707)],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(
            plan["phase"], "native_war_objective_settlement_progress"
        )
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_completed_exact_objective_ignores_stale_siege_state(self) -> None:
        player = _army(
            11, soldiers=None, province_id=2585, controllable=True,
            army_state="sieging",
        )
        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=30,
            date_raw=24_000,
            objective=2585,
            fallback=2543,
            objective_states=[
                _objective_state(2585, occupant=707, active_siege=None)
            ],
            occupation_supported=True,
            siege_progress_supported=True,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(
            plan["phase"], "native_war_objective_settlement_progress"
        )
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_exact_siege_state_leaves_unrelated_province_for_objective(self) -> None:
        player = _army(
            11, soldiers=900, province_id=2598, controllable=True,
            army_state="sieging",
        )
        retreating_enemy = _army(
            21, soldiers=800, province_id=2598, controllable=False,
            army_state="retreating", army_state_code=6,
        )
        plan = _native_war_plan(
            player=player, enemies=[retreating_enemy], score=41, date_raw=24_000,
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")
        self.assertEqual(plan["pursuit"]["target_source"], "war_objective_province")

    def test_exact_siege_retargets_when_enemy_marches_to_objective(self) -> None:
        player = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging", army_state_code=3,
        )
        approaching_enemy = _army(
            21, soldiers=800, province_id=2572, controllable=False,
            move_target_province_id=2585,
            army_state="moving", army_state_code=7,
        )
        plan = _native_war_plan(
            player=player, enemies=[approaching_enemy], score=41, date_raw=24_000,
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2543", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(plan["selected_step"])

    def test_safe_observed_fallback_route_finishes_before_retargeting(self) -> None:
        moving = _army(
            11, soldiers=900, province_id=2564, controllable=True,
            move_target_province_id=2543,
            army_state="moving", army_state_code=7,
            route_province_ids=[2543],
        )
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-2543",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 2543,
                        "submitted_date_raw": 24_000,
                    },
                },
            }
        ]
        plan = _native_war_plan(
            player=moving, enemies=[], score=41, date_raw=24_240,
            history=history, objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
        )

        self.assertEqual(
            plan["phase"],
            "native_war_active_route_contact_horizon_unsupported",
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(plan["move_intent"]["target_province_id"], 2543)

    def test_observable_cleared_route_releases_old_move_intent(self) -> None:
        idle = _army(
            11, soldiers=900, province_id=2564, controllable=True,
            move_target_province_id=None,
            move_target_observable=False,
            army_state="regular", army_state_code=1,
        )
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-2543",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 2543,
                        "submitted_date_raw": 24_000,
                    },
                },
            }
        ]
        plan = _native_war_plan(
            player=idle, enemies=[], score=41, date_raw=24_240,
            history=history, objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_siege_exit_without_score_gain_does_not_complete_objective(self) -> None:
        sieging = _army(
            11, soldiers=900, province_id=2585, controllable=True,
            army_state="sieging",
        )
        idle = _army(11, soldiers=900, province_id=20, controllable=True)
        before = _war_progress(
            24_000, player=sieging, enemies=[], score=24,
            objectives=[2585], fallback=2543,
        )
        after = _war_progress(
            24_168, player=idle, enemies=[], score=24,
            objectives=[2585], fallback=2543,
        )

        plan = _native_war_plan(
            player=idle, enemies=[], score=24, date_raw=24_168,
            history=[_advance_row(1, before, after)],
            objective=2585, fallback=2543,
            steps=("move-army-11-to-2585", "move-army-11-to-2543"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-2585")

    def test_multiwar_planner_keeps_enemy_objective_and_progress_on_one_war(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        old_collision = _army(11, soldiers=900, province_id=2585, controllable=True)
        enemy_a = _army(21, soldiers=2_000, province_id=2585, controllable=False)
        enemy_b = _army(22, soldiers=800, province_id=42, controllable=False)
        war_a = _war(
            war_id=10,
            allied_armies=[player],
            enemy_armies=[enemy_a],
            score=15,
            player_side="defender",
            player_is_primary_war_leader=False,
        )
        war_b = _war(
            war_id=20,
            allied_armies=[player],
            enemy_armies=[enemy_b],
            score=24,
            war_objective_province_ids=[2585],
        )
        before = {
            "date_raw": 24_000,
            "wars": [
                _war_progress(
                    24_000,
                    player=old_collision,
                    enemies=[enemy_a],
                    score=41,
                    war_id=10,
                )["wars"][0],
                _war_progress(
                    24_000,
                    player=player,
                    enemies=[enemy_b],
                    score=24,
                    war_id=20,
                )["wars"][0],
            ],
        }
        after = {
            "date_raw": 24_432,
            "wars": [
                _war_progress(
                    24_432,
                    player=old_collision,
                    enemies=[enemy_a],
                    score=15,
                    war_id=10,
                )["wars"][0],
                _war_progress(
                    24_432,
                    player=player,
                    enemies=[enemy_b],
                    score=24,
                    war_id=20,
                )["wars"][0],
            ],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(91),
                "date_raw": 24_432,
                "native_command_history": [_advance_row(1, before, after)],
                "active_wars": [war_a, war_b],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-2585",
                "move-army-11-to-42",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_restore_discards_pre_restore_collision_and_move_backoff(self) -> None:
        player = _army(11, soldiers=800, province_id=20, controllable=True)
        collision = _army(11, soldiers=900, province_id=77, controllable=True)
        enemy = _army(21, soldiers=800, province_id=77, controllable=False)
        history = [
            _advance_row(
                1,
                _war_progress(24_000, player=collision, enemies=[enemy], score=41),
                _war_progress(24_432, player=collision, enemies=[enemy], score=15),
            ),
            {
                "index": 2,
                "command": "move-army-11-to-77",
                "ok": True,
                "result": {
                    "accepted": False,
                    "war_action": {
                        "status": "move_deferred",
                        "submitted_date_raw": 24_432,
                    },
                },
            },
            {
                "index": 3,
                "command": "restore-checkpoint",
                "ok": True,
                "result": {"status": "restored"},
            },
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[],
            score=15,
            date_raw=24_456,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-77")

    def test_same_province_contact_stales_then_escapes_to_safe_objective(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        before = _war_progress(24_000, player=player, enemies=[enemy], score=24)
        after = _war_progress(24_432, player=player, enemies=[enemy], score=24)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_432,
            history=[_advance_row(1, before, after)],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )

        self.assertEqual(plan["selected_step"], "move-army-11-to-77")
        self.assertEqual(plan["pursuit"]["objective_kind"], "siege")

    def test_global_score_drop_needs_local_nonretreating_enemy_to_block(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=2635,
            controllable=True,
            army_state="regular",
        )
        local_enemy = _army(
            21,
            soldiers=800,
            province_id=2635,
            controllable=False,
            army_state="regular",
        )
        retreating_enemy = {
            **local_enemy,
            "army_state": "retreating",
            "army_state_code": 6,
            "retreating": True,
        }

        for label, enemies, expected_blocked in (
            ("remote_score_change", [], False),
            ("local_contact", [local_enemy], True),
            ("retreating_local", [retreating_enemy], False),
        ):
            with self.subTest(label=label):
                before = _war_progress(
                    53_263_584,
                    player=player,
                    enemies=enemies,
                    score=50,
                )
                after = _war_progress(
                    53_263_632,
                    player=player,
                    enemies=enemies,
                    score=16,
                )
                tactics = _recent_war_tactics(
                    [_advance_row(1, before, after)],
                    {"date_raw": 53_263_632},
                    army_id=11,
                    war_id=88,
                )

                self.assertEqual(
                    2635 in tactics["blocked_province_ids"],
                    expected_blocked,
                )
                self.assertEqual(
                    21 in tactics["blocked_enemy_ids"],
                    expected_blocked,
                )

    def test_large_war_score_defeat_blacklists_collision_for_ninety_days(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        before = _war_progress(24_000, player=player, enemies=[enemy], score=41)
        after = _war_progress(24_432, player=player, enemies=[enemy], score=15)

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=15,
            date_raw=24_432,
            history=[_advance_row(1, before, after)],
            objective=41,
            steps=("life-advance",),
        )

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])
        self.assertIn(21, plan["tactical_state"]["blocked_enemy_ids"])
        self.assertIn(41, plan["tactical_state"]["blocked_province_ids"])

    def test_ninety_day_move_then_deferred_marks_target_as_retreat_collision(self) -> None:
        player = _army(
            11,
            soldiers=900,
            province_id=20,
            controllable=True,
            army_state="retreating",
            army_state_code=6,
        )
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            _advance_row(
                2,
                _war_progress(24_000, player=player, enemies=[enemy], score=0),
                _war_progress(26_184, player=player, enemies=[enemy], score=0),
            ),
            {
                "index": 3,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": False,
                    "war_action": {
                        "status": "move_deferred",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 26_184,
                    },
                },
            },
        ]

        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=26_184,
            history=history,
            steps=("move-army-11-to-41", "life-advance"),
        )

        self.assertEqual(
            plan["phase"], "native_war_global_combat_retreat_progress"
        )
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_forced_retreat_after_deferred_move_submits_safe_objective_once(self) -> None:
        at_collision = _army(11, soldiers=900, province_id=41, controllable=True)
        retreated = _army(11, soldiers=850, province_id=42, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        history: list[dict[str, object]] = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": False,
                    "war_action": {
                        "status": "move_deferred",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            _advance_row(
                2,
                _war_progress(24_000, player=at_collision, enemies=[enemy], score=24),
                _war_progress(24_168, player=retreated, enemies=[enemy], score=24),
            ),
        ]
        plan = _native_war_plan(
            player=retreated,
            enemies=[enemy],
            score=24,
            date_raw=24_168,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )
        self.assertEqual(plan["selected_step"], "move-army-11-to-77")

        history.append(
            {
                "index": 3,
                "command": "move-army-11-to-77",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 77,
                        "submitted_date_raw": 24_168,
                    },
                },
            }
        )
        accepted = _native_war_plan(
            player=retreated,
            enemies=[enemy],
            score=24,
            date_raw=24_192,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )
        self.assertEqual(accepted["selected_step"], "life-advance")
        self.assertEqual(accepted["move_intent"]["target_province_id"], 77)

    def test_deferred_move_retries_use_seven_fourteen_thirty_day_backoff(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        history: list[dict[str, object]] = []
        dates = (24_000, 24_168, 24_504)
        for index, submitted in enumerate(dates, start=1):
            history.append(
                {
                    "index": index,
                    "command": "move-army-11-to-77",
                    "ok": True,
                    "result": {
                        "accepted": False,
                        "war_action": {
                            "status": "move_deferred",
                            "army_id": 11,
                            "target_province_id": 77,
                            "submitted_date_raw": submitted,
                        },
                    },
                }
            )
            required = (7, 14, 30)[index - 1]
            waiting = _native_war_plan(
                player=player,
                enemies=[],
                score=24,
                date_raw=submitted + (required - 1) * 24,
                history=history,
                objective=77,
                steps=("move-army-11-to-77", "life-advance"),
            )
            self.assertEqual(waiting["selected_step"], "life-advance")
            self.assertEqual(waiting["move_backoff"]["required_days"], required)
            due = _native_war_plan(
                player=player,
                enemies=[],
                score=24,
                date_raw=submitted + required * 24,
                history=history,
                objective=77,
                steps=("move-army-11-to-77", "life-advance"),
            )
            self.assertEqual(due["selected_step"], "move-army-11-to-77")

    def test_occupied_blacklisted_objective_has_no_safe_target(self) -> None:
        collision = _army(11, soldiers=900, province_id=77, controllable=True)
        retreated = _army(11, soldiers=800, province_id=42, controllable=True)
        enemy = _army(21, soldiers=800, province_id=77, controllable=False)
        history = [
            _advance_row(
                1,
                _war_progress(24_000, player=collision, enemies=[enemy], score=41),
                _war_progress(24_432, player=retreated, enemies=[enemy], score=15),
            )
        ]

        plan = _native_war_plan(
            player=retreated,
            enemies=[enemy],
            score=15,
            date_raw=24_432,
            history=history,
            objective=77,
            steps=("move-army-11-to-77", "life-advance"),
        )

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_score_gain_and_enemy_disappearance_clear_stale_contact(self) -> None:
        player = _army(11, soldiers=900, province_id=41, controllable=True)
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        first = _advance_row(
            1,
            _war_progress(24_000, player=player, enemies=[enemy], score=24),
            _war_progress(24_168, player=player, enemies=[enemy], score=24),
        )
        improved = _advance_row(
            2,
            _war_progress(24_168, player=player, enemies=[enemy], score=24),
            _war_progress(24_336, player=player, enemies=[enemy], score=25),
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=25,
            date_raw=24_336,
            history=[first, improved],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )
        self.assertEqual(plan["selected_step"], "move-army-11-to-77")

        stale = _advance_row(
            2,
            _war_progress(24_168, player=player, enemies=[enemy], score=24),
            _war_progress(24_504, player=player, enemies=[enemy], score=24),
        )
        disappeared = _advance_row(
            3,
            _war_progress(24_504, player=player, enemies=[enemy], score=24),
            _war_progress(24_528, player=player, enemies=[], score=24),
        )
        cleared = _native_war_plan(
            player=player,
            enemies=[],
            score=24,
            date_raw=24_528,
            history=[first, stale, disappeared],
            objective=77,
            steps=("life-advance", "move-army-11-to-77"),
        )
        self.assertEqual(cleared["selected_step"], "move-army-11-to-77")

    def test_exact_army_states_require_battle_frame_before_combat_advance(self) -> None:
        combat = _army(
            11,
            soldiers=900,
            province_id=41,
            controllable=True,
            army_state="combat",
            army_state_code=2,
        )
        enemy = _army(21, soldiers=800, province_id=41, controllable=False)
        first = _native_war_plan(
            player=combat,
            enemies=[enemy],
            score=15,
            date_raw=24_000,
            objective=41,
            steps=(
                "query-battle-control-snapshot-v1-11",
                "life-advance",
            ),
        )
        self.assertEqual(
            first["selected_step"],
            "query-battle-control-snapshot-v1-11",
        )

        bounded = _native_war_plan(
            player=combat,
            enemies=[enemy],
            score=15,
            date_raw=24_360,
            history=[
                _advance_row(
                    1,
                    _war_progress(24_000, player=combat, enemies=[enemy], score=15),
                    _war_progress(24_360, player=combat, enemies=[enemy], score=15),
                )
            ],
            objective=77,
            steps=(
                "query-battle-control-snapshot-v1-11",
                "life-advance",
                "move-army-11-to-77",
            ),
        )
        self.assertEqual(
            bounded["phase"], "native_war_battle_control_query"
        )
        self.assertEqual(
            bounded["selected_step"],
            "query-battle-control-snapshot-v1-11",
        )

        unsupported = _native_war_plan(
            player=combat,
            enemies=[enemy],
            score=15,
            date_raw=24_360,
            history=[
                _advance_row(
                    1,
                    _war_progress(24_000, player=combat, enemies=[enemy], score=15),
                    _war_progress(24_360, player=combat, enemies=[enemy], score=15),
                )
            ],
            objective=77,
            steps=("move-army-11-to-77",),
        )
        self.assertEqual(
            unsupported["phase"],
            "native_war_battle_control_query_unsupported",
        )
        self.assertIsNone(unsupported["selected_step"])
        self.assertEqual(
            unsupported["required_step"],
            "query-battle-control-snapshot-v1-11",
        )

        retreating = {**combat, "army_state": "retreating", "army_state_code": 6}
        retreat = _native_war_plan(
            player=retreating,
            enemies=[enemy],
            score=15,
            date_raw=24_000,
            objective=77,
            steps=("life-advance",),
        )
        self.assertEqual(
            retreat["phase"], "native_war_global_combat_retreat_progress"
        )

        sieging = {**combat, "army_state": "sieging", "army_state_code": 3}
        siege = _native_war_plan(
            player=sieging,
            enemies=[],
            score=15,
            date_raw=24_000,
            objective=41,
            steps=("life-advance",),
        )
        self.assertEqual(siege["phase"], "native_war_siege_progress")

    def test_defender_continues_to_tactical_hold_without_exit_forecast(
        self,
    ) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=24,
                        player_side="defender",
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "move-army-11-to-41",
                "move-army-11-to-77",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["active_wars"][0]["war_exit_assessment"]["status"],
            "unavailable",
        )

    def test_primary_defender_without_objective_holds_exact_capital(
        self,
    ) -> None:
        date_raw = 53_280_864
        player = _army(
            234_881_216,
            soldiers=399,
            province_id=45,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            184_549_393,
            soldiers=400,
            province_id=28,
            controllable=False,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        termination = _termination_options(score=0)
        termination.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            history=[
                _campaign_root_row(
                    1, date_raw=date_raw, capital_province_id=45
                )
            ],
            fallback=1741,
            steps=("life-advance",),
            termination_options=[termination],
            player_side="defender",
        )

        self.assertEqual(
            plan["phase"], "native_war_defender_capital_hold_progress"
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["defensive_hold"]["war_id"], 88)
        self.assertEqual(
            plan["defensive_hold"]["army_id"], 234_881_216
        )
        self.assertEqual(plan["defensive_hold"]["capital_province_id"], 45)
        self.assertEqual(
            plan["defensive_hold"]["termination_evidence"]["status"],
            "same_frame_no_authorized_exit",
        )
        continued_options = copy.deepcopy(termination)
        continued_options["player_relative_war_score"] = 1
        continued = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=1,
            date_raw=date_raw,
            history=[
                _campaign_root_row(
                    1, date_raw=date_raw, capital_province_id=45
                )
            ],
            fallback=1741,
            steps=("life-advance",),
            termination_options=[continued_options],
            player_side="defender",
        )
        self.assertEqual(
            continued["phase"], "native_war_defender_capital_hold_progress"
        )
        self.assertEqual(continued["selected_step"], "life-advance")

    def test_primary_defender_capital_hold_consumes_negative_exit_lease(
        self,
    ) -> None:
        queried_date_raw = 53_280_744
        current_date_raw = 53_280_864
        player = _army(
            234_881_216,
            soldiers=399,
            province_id=45,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            184_549_393,
            soldiers=400,
            province_id=28,
            controllable=False,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        war = _war(
            war_id=150_994_969,
            allied_armies=[player],
            enemy_armies=[enemy],
            score=0,
            player_side="defender",
            player_is_primary_war_leader=True,
            enemy_primary_default_raise_province_id=1741,
        )
        queried = _termination_reuse_snapshot(
            date_raw=queried_date_raw,
            wars=[copy.deepcopy(war)],
        )
        queried["player_armies"] = [copy.deepcopy(player)]
        options = _termination_options(war_id=150_994_969, score=0)
        options.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
            }
        )
        termination_row = _termination_query_row(
            1,
            queried,
            war_id=150_994_969,
            options=options,
        )
        root_row = _campaign_root_row(
            2,
            date_raw=current_date_raw,
            capital_province_id=45,
            actor_character_id=29_829,
        )
        root_row["result"]["campaign_root_context"][
            "snapshot_revision"
        ] = 12
        history = [termination_row, root_row]
        current = _termination_reuse_snapshot(
            date_raw=current_date_raw,
            wars=[copy.deepcopy(war)],
            history=history,
        )
        current["player_armies"] = [copy.deepcopy(player)]

        plan = choose_one_life_turn(
            history,
            snapshot=current,
            action_steps=(
                "query-war-termination-options-150994969",
                "query-campaign-root-context-v1",
                "life-advance",
            ),
        )

        self.assertEqual(
            plan["phase"], "native_war_defender_capital_hold_progress"
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["defensive_hold"]["termination_evidence"]["status"],
            "negative_assessment_reused",
        )

    def test_primary_defender_capital_hold_requires_fresh_exact_root(
        self,
    ) -> None:
        date_raw = 24_000
        player = _army(
            11,
            soldiers=900,
            province_id=45,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21,
            soldiers=1_100,
            province_id=28,
            controllable=False,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        termination = _termination_options(score=0)
        termination.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        base = {
            "player": player,
            "enemies": [enemy],
            "score": 0,
            "date_raw": date_raw,
            "fallback": 77,
            "steps": ("query-campaign-root-context-v1", "life-advance"),
            "termination_options": [termination],
            "player_side": "defender",
        }

        missing = _native_war_plan(**base)
        stale = _native_war_plan(
            **base,
            history=[
                _campaign_root_row(
                    1, date_raw=date_raw - 24, capital_province_id=45
                )
            ],
        )

        for plan in (missing, stale):
            self.assertEqual(
                plan["phase"], "native_war_defender_capital_hold_context"
            )
            self.assertEqual(
                plan["selected_step"], "query-campaign-root-context-v1"
            )

    def test_primary_defender_capital_hold_routes_threat_to_exact_horizon(
        self,
    ) -> None:
        date_raw = 24_000
        player = _army(
            11,
            soldiers=900,
            province_id=45,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21,
            soldiers=1_100,
            province_id=28,
            controllable=False,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        termination = _termination_options(score=0)
        termination.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        base = {
            "player": player,
            "score": 0,
            "date_raw": date_raw,
            "fallback": 77,
            "steps": ("life-advance",),
            "termination_options": [termination],
            "player_side": "defender",
        }
        noncapital = _native_war_plan(
            **base,
            enemies=[enemy],
            history=[
                _campaign_root_row(
                    1, date_raw=date_raw, capital_province_id=46
                )
            ],
        )
        query_step = query_route_contact_horizon_step(11, 45, (21,))
        threat = _native_war_plan(
            **{
                **base,
                "steps": (query_step, "life-advance"),
                "route_contact_horizon_supported": True,
            },
            enemies=[
                {
                    **enemy,
                    "army_state": "moving",
                    "army_state_code": 7,
                    "move_target_province_id": 45,
                    "route_province_ids": [45],
                }
            ],
            history=[
                _campaign_root_row(
                    1, date_raw=date_raw, capital_province_id=45
                )
            ],
        )
        route_away = _native_war_plan(
            **base,
            enemies=[
                {
                    **enemy,
                    "army_state": "moving",
                    "army_state_code": 7,
                    "move_target_province_id": 29,
                    "route_province_ids": [29],
                }
            ],
            history=[
                _campaign_root_row(
                    1, date_raw=date_raw, capital_province_id=45
                )
            ],
        )

        self.assertEqual(noncapital["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(noncapital["selected_step"])
        self.assertEqual(
            threat["phase"],
            "native_war_defender_capital_contact_horizon",
        )
        self.assertEqual(threat["selected_step"], query_step)
        self.assertEqual(
            route_away["phase"], "native_war_counterpolicy_hold"
        )
        self.assertIsNone(route_away["selected_step"])

    def test_primary_defender_capital_contact_requires_fresh_exact_proof(
        self,
    ) -> None:
        date_raw = 24_000
        player = _army(
            11,
            soldiers=900,
            province_id=45,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21,
            soldiers=1_100,
            province_id=8_745,
            controllable=False,
            army_state="moving",
            army_state_code=7,
            move_target_province_id=45,
            route_province_ids=[8_747, 23, 8_749, 45],
            in_combat=False,
            retreating=False,
        )
        termination = _termination_options(score=0)
        termination.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        root = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=45
        )
        query_step = query_route_contact_horizon_step(11, 45, (21,))
        advance_step = advance_route_contact_horizon_step(11, 45, (21,))
        base = {
            "player": player,
            "enemies": [enemy],
            "score": 0,
            "date_raw": date_raw,
            "fallback": 77,
            "termination_options": [termination],
            "player_side": "defender",
            "route_contact_horizon_supported": True,
        }

        proof = _route_contact_row(
            2,
            origin=45,
            target=45,
            date_raw=date_raw,
            route=[],
            hostile_ids=(21,),
            contact_free=True,
        )
        progress = _native_war_plan(
            **base,
            history=[root, proof],
            steps=(advance_step, "life-advance"),
        )
        self.assertEqual(
            progress["phase"],
            "native_war_defender_capital_contact_horizon_progress",
        )
        self.assertEqual(progress["selected_step"], advance_step)

        unavoidable = _route_contact_row(
            2,
            origin=45,
            target=45,
            date_raw=date_raw,
            route=[],
            hostile_ids=(21,),
            contact_free=False,
        )
        contact = _native_war_plan(
            **base,
            history=[root, unavoidable],
            steps=(advance_step, "life-advance"),
        )
        self.assertEqual(
            contact["phase"],
            "native_war_defender_capital_contact_transition",
        )
        self.assertEqual(contact["selected_step"], advance_step)

        stale = _route_contact_row(
            2,
            origin=45,
            target=45,
            date_raw=date_raw - 24,
            route=[],
            hostile_ids=(21,),
            contact_free=True,
        )
        stale_plan = _native_war_plan(
            **base,
            history=[root, stale],
            steps=(query_step, advance_step, "life-advance"),
        )
        self.assertEqual(
            stale_plan["phase"],
            "native_war_defender_capital_contact_horizon_unavailable",
        )
        self.assertIsNone(stale_plan["selected_step"])

        unavailable = copy.deepcopy(proof)
        unavailable["result"]["status"] = "route_unavailable"
        unavailable["result"]["route_contact_horizon"] = {
            "status": "route_unavailable"
        }
        unavailable_plan = _native_war_plan(
            **base,
            history=[root, unavailable],
            steps=(query_step, advance_step, "life-advance"),
        )
        self.assertEqual(
            unavailable_plan["phase"],
            "native_war_defender_capital_contact_horizon_unavailable",
        )
        self.assertIsNone(unavailable_plan["selected_step"])

    def test_primary_defender_capital_contact_rejects_wrong_scope(
        self,
    ) -> None:
        date_raw = 24_000
        player = _army(
            11,
            soldiers=900,
            province_id=45,
            controllable=True,
            army_state="regular",
            army_state_code=1,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        enemy = _army(
            21,
            soldiers=1_100,
            province_id=8_745,
            controllable=False,
            army_state="moving",
            army_state_code=7,
            move_target_province_id=45,
            route_province_ids=[8_747, 45],
            in_combat=False,
            retreating=False,
        )
        termination = _termination_options(score=0)
        termination.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
                "queried_snapshot_id": "session:90",
                "queried_revision": 90,
                "queried_native_revision": 90,
                "queried_connection_generation": 1,
                "episode_run_id": None,
            }
        )
        root = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=45
        )
        query_step = query_route_contact_horizon_step(11, 45, (21,))
        base = {
            "enemies": [enemy],
            "score": 0,
            "date_raw": date_raw,
            "history": [root],
            "fallback": 77,
            "steps": (query_step, "life-advance"),
            "termination_options": [termination],
            "route_contact_horizon_supported": True,
        }
        cases = {
            "attacker": {
                "player": player,
                "player_side": "attacker",
            },
            "unknown_primary": {
                "player": player,
                "player_side": "defender",
                "player_is_primary_war_leader": None,
            },
            "noncapital": {
                "player": {**player, "current_province_id": 46},
                "player_side": "defender",
            },
            "combat": {
                "player": {
                    **player,
                    "army_state": "combat",
                    "army_state_code": 2,
                    "in_combat": True,
                },
                "player_side": "defender",
            },
            "retreat": {
                "player": {
                    **player,
                    "army_state": "retreating",
                    "army_state_code": 6,
                    "retreating": True,
                },
                "player_side": "defender",
            },
        }
        for name, overrides in cases.items():
            with self.subTest(name=name):
                plan = _native_war_plan(**{**base, **overrides})
                self.assertNotEqual(plan.get("selected_step"), query_step)
                self.assertNotEqual(
                    plan.get("phase"),
                    "native_war_defender_capital_contact_horizon",
                )

    def test_primary_defender_native_rally_hold_binds_r867_tail_and_restore(
        self,
    ) -> None:
        queried_date_raw = 53_282_400
        current_date_raw = 53_282_424
        gathering = _army(
            184_549_472,
            soldiers=None,
            province_id=8_750,
            controllable=True,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        regular = {
            **gathering,
            "army_state": "regular",
            "army_state_code": 1,
        }
        enemies = [
            _army(
                184_549_393,
                soldiers=None,
                province_id=45,
                controllable=False,
                army_state="sieging",
                army_state_code=3,
                route_province_ids=[],
                in_combat=False,
                retreating=False,
            ),
            *[
                _army(
                    army_id,
                    soldiers=None,
                    province_id=45,
                    controllable=False,
                    move_target_province_id=46,
                    army_state="moving",
                    army_state_code=7,
                    route_province_ids=[46],
                    in_combat=False,
                    retreating=False,
                )
                for army_id in (201_326_661, 234_881_097, 301_989_919)
            ],
        ]
        queried_war = _war(
            allied_armies=[gathering],
            enemy_armies=copy.deepcopy(enemies),
            score=-50,
            player_side="defender",
            player_is_primary_war_leader=True,
            enemy_primary_default_raise_province_id=1_741,
            war_duration_days=69,
        )
        queried_snapshot = {
            **_snapshot(90),
            "paused": True,
            "map_ready": True,
            "native_revision": 90,
            "date_raw": queried_date_raw,
            "episode_run_id": None,
            "diagnostics": {"connection_generation": 1},
            "played_character": {"character_id": 707, "alive": True},
            "active_wars": [queried_war],
            "player_armies": [gathering],
        }
        options = _termination_options(
            score=-50, war_duration_days=69
        )
        options.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
            }
        )
        current_options = {
            **copy.deepcopy(options),
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "episode_run_id": None,
        }
        termination_row = _termination_query_row(
            1, queried_snapshot, options=options
        )
        before = _war_progress(
            queried_date_raw,
            player=gathering,
            enemies=enemies,
            score=-50,
            fallback=1_741,
        )
        after = _war_progress(
            current_date_raw,
            player=regular,
            enemies=enemies,
            score=-50,
            fallback=1_741,
        )
        root = _campaign_root_row(
            4, date_raw=current_date_raw, capital_province_id=45
        )
        history = [
            termination_row,
            _raise_troops_row(2, gathering),
            _advance_row(3, before, after),
            root,
        ]
        base = {
            "player": regular,
            "enemies": enemies,
            "score": -50,
            "date_raw": current_date_raw,
            "fallback": 1_741,
            "steps": (
                "query-war-termination-options-88",
                "query-campaign-root-context-v1",
                "life-advance",
            ),
            "player_side": "defender",
            "war_duration_days": 69,
            "termination_options": [current_options],
            "army_strengths": [
                _army_strength(
                    184_549_472,
                    "player",
                    [88],
                    current=2,
                    maximum=2,
                    base_power_raw=200_000,
                ),
                *[
                    _army_strength(
                        army_id,
                        "active_war_enemy",
                        [88],
                        current=1_000,
                        maximum=1_000,
                        base_power_raw=100_000_000,
                    )
                    for army_id in (
                        184_549_393,
                        201_326_661,
                        234_881_097,
                        301_989_919,
                    )
                ],
            ],
            "army_strengths_status": "available",
        }

        plan = _native_war_plan(**base, history=history)

        self.assertEqual(
            plan["phase"],
            "native_war_defender_native_rally_hold_progress",
        )
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["native_rally_hold_binding"],
            {
                "status": "ready",
                "war_id": 88,
                "army_id": 184_549_472,
                "owner_character_id": 707,
                "rally_province_id": 8_750,
                "raise_history_index": 2,
                "raise_snapshot_id": "session:91",
                "raise_revision": 91,
                "war_query_history_index": 1,
                "war_query_date_raw": queried_date_raw,
                "crossed_restore_history_indices": [],
            },
        )
        self.assertEqual(plan["defensive_hold"]["capital_province_id"], 45)

        restored_snapshot = copy.deepcopy(queried_snapshot)
        restored_snapshot["date_raw"] = current_date_raw
        restored_snapshot["active_wars"] = [
            _war(
                allied_armies=[regular],
                enemy_armies=copy.deepcopy(enemies),
                score=-50,
                player_side="defender",
                player_is_primary_war_leader=True,
                enemy_primary_default_raise_province_id=1_741,
                war_duration_days=69,
            )
        ]
        restored_snapshot["player_armies"] = [regular]
        restored_history = [
            *history,
            _restore_checkpoint_row(5, checkpoint_history_index=4),
            _termination_query_row(6, restored_snapshot, options=options),
            _campaign_root_row(
                7, date_raw=current_date_raw, capital_province_id=45
            ),
        ]

        restored = _native_war_plan(**base, history=restored_history)

        self.assertEqual(
            restored["phase"],
            "native_war_defender_native_rally_hold_progress",
        )
        self.assertEqual(
            restored["native_rally_hold_binding"][
                "crossed_restore_history_indices"
            ],
            [5],
        )

    def test_threatened_native_rally_uses_observed_county_route_or_exact_hold(
        self,
    ) -> None:
        queried_date_raw = 53_282_400
        current_date_raw = 53_282_424
        army_id = 184_549_472
        rally_province_id = 8_750
        gathering = _army(
            army_id,
            soldiers=2,
            province_id=rally_province_id,
            controllable=True,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        regular = {
            **gathering,
            "army_state": "regular",
            "army_state_code": 1,
        }
        enemy = _army(
            301_989_919,
            soldiers=7_833,
            province_id=46,
            controllable=False,
            army_state="moving",
            army_state_code=7,
            move_target_province_id=rally_province_id,
            route_province_ids=[45, rally_province_id],
            in_combat=False,
            retreating=False,
        )
        queried_war = _war(
            allied_armies=[gathering],
            enemy_armies=[enemy],
            score=-50,
            player_side="defender",
            player_is_primary_war_leader=True,
            war_duration_days=69,
        )
        queried_snapshot = {
            **_snapshot(90),
            "paused": True,
            "map_ready": True,
            "native_revision": 90,
            "date_raw": queried_date_raw,
            "episode_run_id": None,
            "diagnostics": {"connection_generation": 1},
            "played_character": {"character_id": 707, "alive": True},
            "active_wars": [queried_war],
            "player_armies": [gathering],
        }
        options = _termination_options(score=-50, war_duration_days=69)
        options.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
            }
        )
        current_options = {
            **copy.deepcopy(options),
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "episode_run_id": None,
        }
        base_history = [
            _termination_query_row(1, queried_snapshot, options=options),
            _raise_troops_row(2, gathering),
            _advance_row(
                3,
                _war_progress(
                    queried_date_raw,
                    player=gathering,
                    enemies=[enemy],
                    score=-50,
                ),
                _war_progress(
                    current_date_raw,
                    player=regular,
                    enemies=[enemy],
                    score=-50,
                ),
            ),
        ]
        unsafe_preview_step = f"preview-move-army-{army_id}-to-45"
        preview_step = f"preview-move-army-{army_id}-to-47"
        move_step = f"move-army-{army_id}-to-47"
        base = {
            "player": regular,
            "enemies": [enemy],
            "score": -50,
            "date_raw": current_date_raw,
            "fallback": 1_741,
            "steps": (
                "query-campaign-root-context-v1",
                unsafe_preview_step,
                preview_step,
                move_step,
                "life-advance",
            ),
            "player_side": "defender",
            "war_duration_days": 69,
            "termination_options": [current_options],
            "move_route_preview_supported": True,
        }
        overmatch_strengths = [
            {
                "status": "available",
                "army_id": army_id,
                "scope_role": "player",
                "war_ids": [88],
                "current_soldiers": 2,
                "maximum_soldiers": 2,
                "ai_base_power_raw": 1_200,
            },
            {
                "status": "available",
                "army_id": 301_989_919,
                "scope_role": "active_war_enemy",
                "war_ids": [88],
                "current_soldiers": 7_833,
                "maximum_soldiers": 7_833,
                "ai_base_power_raw": 259_207,
            },
        ]

        legacy_root = _campaign_root_row(
            4, date_raw=current_date_raw, capital_province_id=45
        )
        observation = _native_war_plan(
            **base, history=[*base_history, legacy_root]
        )
        self.assertEqual(
            observation["phase"], "native_war_safe_objective_context"
        )
        self.assertEqual(
            observation["selected_step"],
            "query-campaign-root-context-v1",
        )

        complete_root = _campaign_root_row(
            4,
            date_raw=current_date_raw,
            capital_province_id=45,
            held_county_capital_province_ids=(
                rally_province_id,
                45,
                47,
            ),
        )
        preview = _native_war_plan(
            **base, history=[*base_history, complete_root]
        )
        self.assertEqual(preview["phase"], "native_war_route_preview")
        self.assertEqual(preview["selected_step"], unsafe_preview_step)

        next_preview = _native_war_plan(
            **base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
            ],
        )
        self.assertEqual(next_preview["phase"], "native_war_route_preview")
        self.assertEqual(next_preview["selected_step"], preview_step)

        move = _native_war_plan(
            **base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                _preview_row(
                    6,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[47],
                ),
            ],
        )
        self.assertEqual(move["phase"], "native_war_pursuit")
        self.assertEqual(move["selected_step"], move_step)
        self.assertEqual(
            move["pursuit"]["target_source"],
            "player_held_county_capital",
        )
        self.assertEqual(move["pursuit"]["objective_kind"], "regroup")

        hostile_ids = (301_989_919,)
        contact_query_step = query_route_contact_horizon_step(
            army_id, 45, hostile_ids
        )
        contact_query_47_step = query_route_contact_horizon_step(
            army_id, 47, hostile_ids
        )
        stationary_contact_query_step = query_route_contact_horizon_step(
            army_id, rally_province_id, hostile_ids
        )
        stationary_contact_advance_step = (
            advance_route_contact_horizon_step(
                army_id, rally_province_id, hostile_ids
            )
        )
        move_45_step = f"move-army-{army_id}-to-45"
        contact_free_45 = _route_contact_row(
            6,
            army_id=army_id,
            origin=rally_province_id,
            target=45,
            date_raw=current_date_raw,
            route=[45],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        overmatch_base = {
            **base,
            "steps": (
                *base["steps"],
                contact_query_step,
                contact_query_47_step,
                stationary_contact_query_step,
                stationary_contact_advance_step,
                move_45_step,
            ),
            "route_contact_horizon_supported": True,
            "army_strengths": overmatch_strengths,
            "army_strengths_status": "available",
        }

        r881_guard = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                _campaign_root_row(
                    4,
                    date_raw=current_date_raw,
                    capital_province_id=45,
                    held_county_capital_province_ids=(
                        rally_province_id,
                        45,
                    ),
                ),
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
            ],
        )
        self.assertEqual(
            r881_guard["phase"],
            "native_war_defender_native_rally_contact_horizon",
        )
        self.assertEqual(
            r881_guard["selected_step"], stationary_contact_query_step
        )
        self.assertNotEqual(r881_guard.get("selected_step"), move_45_step)
        self.assertEqual(
            r881_guard["route_rejections"][0][
                "one_day_contact_horizon_rejected"
            ],
            "hostile_operational_overmatch_player_held_county_fallback",
        )

        contact_free_47 = _route_contact_row(
            8,
            army_id=army_id,
            origin=rally_province_id,
            target=47,
            date_raw=current_date_raw,
            route=[45, 47],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        r0018_guard_query = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
                _preview_row(
                    7,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[45, 47],
                ),
                contact_free_47,
            ],
        )
        self.assertEqual(
            r0018_guard_query["phase"],
            "native_war_defender_native_rally_contact_horizon",
        )
        self.assertEqual(
            r0018_guard_query["selected_step"],
            stationary_contact_query_step,
        )
        self.assertEqual(
            [
                rejection["target_province_id"]
                for rejection in r0018_guard_query["route_rejections"]
            ],
            [45, 47],
        )
        self.assertTrue(
            all(
                rejection["one_day_contact_horizon_rejected"]
                == (
                    "hostile_operational_overmatch_"
                    "player_held_county_fallback"
                )
                for rejection in r0018_guard_query["route_rejections"]
            )
        )

        unavailable_47 = copy.deepcopy(contact_free_47)
        unavailable_47["result"]["status"] = "route_unavailable"
        unavailable_47["result"]["route_contact_horizon"] = {
            "status": "route_unavailable"
        }
        incomplete_guard_set = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
                _preview_row(
                    7,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[45, 47],
                ),
                unavailable_47,
            ],
        )
        self.assertEqual(
            incomplete_guard_set["phase"],
            "native_war_no_safe_player_held_county_route",
        )
        self.assertIsNone(incomplete_guard_set["selected_step"])
        self.assertEqual(
            len(incomplete_guard_set["route_rejections"]), 2
        )
        self.assertEqual(
            incomplete_guard_set["route_rejections"][1]["status"],
            "contact_timeline_unavailable",
        )

        timed_conflict_45 = _route_contact_row(
            6,
            army_id=army_id,
            origin=rally_province_id,
            target=45,
            date_raw=current_date_raw,
            route=[45],
            hostile_ids=hostile_ids,
            contact_free=False,
        )
        timed_conflict_47 = _route_contact_row(
            8,
            army_id=army_id,
            origin=rally_province_id,
            target=47,
            date_raw=current_date_raw,
            route=[45, 47],
            hostile_ids=hostile_ids,
            contact_free=False,
        )
        r0044_timed_conflicts_still_query_rally = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                timed_conflict_45,
                _preview_row(
                    7,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[45, 47],
                ),
                timed_conflict_47,
            ],
        )
        self.assertEqual(
            r0044_timed_conflicts_still_query_rally["phase"],
            "native_war_defender_native_rally_contact_horizon",
        )
        self.assertEqual(
            r0044_timed_conflicts_still_query_rally["selected_step"],
            stationary_contact_query_step,
        )
        self.assertTrue(
            all(
                rejection["status"] == "unsafe"
                for rejection in r0044_timed_conflicts_still_query_rally[
                    "route_rejections"
                ]
            )
        )
        self.assertTrue(
            all(
                "one_day_contact_horizon_rejected" not in rejection
                for rejection in r0044_timed_conflicts_still_query_rally[
                    "route_rejections"
                ]
            )
        )

        stationary_contact_free = _route_contact_row(
            9,
            army_id=army_id,
            origin=rally_province_id,
            target=rally_province_id,
            date_raw=current_date_raw,
            route=[],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        r0018_guard_hold = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
                _preview_row(
                    7,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[45, 47],
                ),
                contact_free_47,
                stationary_contact_free,
            ],
        )
        self.assertEqual(
            r0018_guard_hold["phase"],
            "native_war_defender_native_rally_contact_horizon_progress",
        )
        self.assertEqual(
            r0018_guard_hold["selected_step"],
            stationary_contact_advance_step,
        )
        self.assertTrue(
            r0018_guard_hold["contact_horizon"]["one_day_contact_free"]
        )

        stationary_contact_unavoidable = _route_contact_row(
            9,
            army_id=army_id,
            origin=rally_province_id,
            target=rally_province_id,
            date_raw=current_date_raw,
            route=[],
            hostile_ids=hostile_ids,
            contact_free=False,
        )
        r0018_guard_transition = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
                _preview_row(
                    7,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[45, 47],
                ),
                contact_free_47,
                stationary_contact_unavoidable,
            ],
        )
        self.assertEqual(
            r0018_guard_transition["phase"],
            "native_war_defender_native_rally_contact_transition",
        )
        self.assertEqual(
            r0018_guard_transition["selected_step"],
            stationary_contact_advance_step,
        )

        safe_withdrawal = _native_war_plan(
            **overmatch_base,
            history=[
                *base_history,
                complete_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
                _preview_row(
                    7,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=47,
                    date_raw=current_date_raw,
                    route=[47],
                ),
            ],
        )
        self.assertEqual(safe_withdrawal["phase"], "native_war_pursuit")
        self.assertEqual(safe_withdrawal["selected_step"], move_step)
        self.assertEqual(
            safe_withdrawal["pursuit"]["route_audit"]["status"], "safe"
        )

        balanced_strengths = copy.deepcopy(overmatch_strengths)
        balanced_strengths[0].update(
            {
                "current_soldiers": 8_000,
                "maximum_soldiers": 8_000,
                "ai_base_power_raw": 300_000,
            }
        )
        horizon_preserved = _native_war_plan(
            **{
                **overmatch_base,
                "army_strengths": balanced_strengths,
            },
            history=[
                *base_history,
                _campaign_root_row(
                    4,
                    date_raw=current_date_raw,
                    capital_province_id=45,
                    held_county_capital_province_ids=(
                        rally_province_id,
                        45,
                    ),
                ),
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
                contact_free_45,
            ],
        )
        self.assertEqual(horizon_preserved["phase"], "native_war_pursuit")
        self.assertEqual(horizon_preserved["selected_step"], move_45_step)
        self.assertEqual(
            horizon_preserved["pursuit"]["route_audit"]["status"],
            "safe_one_day_contact_horizon",
        )

        current_only_root = _campaign_root_row(
            4,
            date_raw=current_date_raw,
            capital_province_id=45,
            held_county_capital_province_ids=(rally_province_id,),
        )
        no_alternate = _native_war_plan(
            **base, history=[*base_history, current_only_root]
        )
        self.assertEqual(
            no_alternate["phase"],
            "native_war_no_alternate_player_held_county",
        )
        self.assertIsNone(no_alternate["selected_step"])

        unsafe_root = _campaign_root_row(
            4,
            date_raw=current_date_raw,
            capital_province_id=45,
            held_county_capital_province_ids=(rally_province_id, 45),
        )
        no_safe_route = _native_war_plan(
            **base,
            history=[
                *base_history,
                unsafe_root,
                _preview_row(
                    5,
                    army_id=army_id,
                    origin=rally_province_id,
                    target=45,
                    date_raw=current_date_raw,
                    route=[45],
                ),
            ],
        )
        self.assertEqual(
            no_safe_route["phase"],
            "native_war_no_safe_player_held_county_route",
        )
        self.assertIsNone(no_safe_route["selected_step"])

    def test_r0018_restore_requires_fresh_four_hostile_rally_horizon(
        self,
    ) -> None:
        queried_date_raw = 53_282_400
        stale_date_raw = 53_282_712
        current_date_raw = 53_282_736
        army_id = 184_549_472
        rally_province_id = 8_750
        hostile_ids = (
            184_549_393,
            201_326_661,
            234_881_097,
            301_989_919,
        )
        gathering = _army(
            army_id,
            soldiers=2,
            province_id=rally_province_id,
            controllable=True,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        regular = {
            **gathering,
            "army_state": "regular",
            "army_state_code": 1,
        }
        enemies = [
            _army(
                hostile_ids[0],
                soldiers=1,
                province_id=45,
                controllable=False,
                army_state="regular",
                army_state_code=1,
                route_province_ids=[],
                in_combat=False,
                retreating=False,
            ),
            _army(
                hostile_ids[1],
                soldiers=1,
                province_id=46,
                controllable=False,
                army_state="moving",
                army_state_code=7,
                move_target_province_id=8_749,
                route_province_ids=[8_749],
                in_combat=False,
                retreating=False,
            ),
            _army(
                hostile_ids[2],
                soldiers=1,
                province_id=46,
                controllable=False,
                army_state="regular",
                army_state_code=1,
                route_province_ids=[],
                in_combat=False,
                retreating=False,
            ),
            _army(
                hostile_ids[3],
                soldiers=7_830,
                province_id=46,
                controllable=False,
                army_state="moving",
                army_state_code=7,
                move_target_province_id=rally_province_id,
                route_province_ids=[45, rally_province_id],
                in_combat=False,
                retreating=False,
            ),
        ]
        queried_war = _war(
            allied_armies=[gathering],
            enemy_armies=copy.deepcopy(enemies),
            score=-50,
            player_side="defender",
            player_is_primary_war_leader=True,
            war_duration_days=69,
        )
        queried_snapshot = {
            **_snapshot(90),
            "paused": True,
            "map_ready": True,
            "native_revision": 90,
            "date_raw": queried_date_raw,
            "episode_run_id": None,
            "diagnostics": {"connection_generation": 1},
            "played_character": {"character_id": 707, "alive": True},
            "active_wars": [queried_war],
            "player_armies": [gathering],
        }
        options = _termination_options(score=-50, war_duration_days=69)
        options.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
            }
        )
        current_options = {
            **copy.deepcopy(options),
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "episode_run_id": None,
        }
        base_history = [
            _termination_query_row(1_336, queried_snapshot, options=options),
            _raise_troops_row(1_337, gathering),
            _advance_row(
                1_338,
                _war_progress(
                    queried_date_raw,
                    player=gathering,
                    enemies=copy.deepcopy(enemies),
                    score=-50,
                ),
                _war_progress(
                    stale_date_raw,
                    player=regular,
                    enemies=copy.deepcopy(enemies),
                    score=-50,
                ),
            ),
        ]
        old_root = _campaign_root_row(
            1_389,
            date_raw=stale_date_raw,
            capital_province_id=45,
            held_county_capital_province_ids=(
                rally_province_id,
                45,
                46,
            ),
        )
        old_preview_45 = _preview_row(
            1_390,
            army_id=army_id,
            origin=rally_province_id,
            target=45,
            date_raw=stale_date_raw,
            route=[45],
        )
        old_horizon_45 = _route_contact_row(
            1_390,
            army_id=army_id,
            origin=rally_province_id,
            target=45,
            date_raw=stale_date_raw,
            route=[45],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        old_preview_46 = _preview_row(
            1_392,
            army_id=army_id,
            origin=rally_province_id,
            target=46,
            date_raw=stale_date_raw,
            route=[45, 46],
        )
        old_horizon_46 = _route_contact_row(
            1_392,
            army_id=army_id,
            origin=rally_province_id,
            target=46,
            date_raw=stale_date_raw,
            route=[45, 46],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        old_stationary_horizon = _route_contact_row(
            1_392,
            army_id=army_id,
            origin=rally_province_id,
            target=rally_province_id,
            date_raw=stale_date_raw,
            route=[],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        restore = _restore_checkpoint_row(
            1_393, checkpoint_history_index=1_392
        )
        current_root = _campaign_root_row(
            1_394,
            date_raw=current_date_raw,
            capital_province_id=45,
            held_county_capital_province_ids=(
                rally_province_id,
                45,
                46,
            ),
        )
        fresh_preview_45 = _preview_row(
            1_395,
            army_id=army_id,
            origin=rally_province_id,
            target=45,
            date_raw=current_date_raw,
            route=[45],
        )
        fresh_horizon_45 = _route_contact_row(
            1_396,
            army_id=army_id,
            origin=rally_province_id,
            target=45,
            date_raw=current_date_raw,
            route=[45],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        fresh_preview_46 = _preview_row(
            1_397,
            army_id=army_id,
            origin=rally_province_id,
            target=46,
            date_raw=current_date_raw,
            route=[45, 46],
        )
        fresh_horizon_46 = _route_contact_row(
            1_398,
            army_id=army_id,
            origin=rally_province_id,
            target=46,
            date_raw=current_date_raw,
            route=[45, 46],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        stationary_query_step = query_route_contact_horizon_step(
            army_id, rally_province_id, hostile_ids
        )
        stationary_advance_step = advance_route_contact_horizon_step(
            army_id, rally_province_id, hostile_ids
        )
        self.assertEqual(
            stationary_query_step,
            "query-route-contact-horizon-v1-184549472-to-8750-h-4-"
            "184549393-201326661-234881097-301989919",
        )
        steps = (
            "query-campaign-root-context-v1",
            f"preview-move-army-{army_id}-to-45",
            f"preview-move-army-{army_id}-to-46",
            query_route_contact_horizon_step(army_id, 45, hostile_ids),
            query_route_contact_horizon_step(army_id, 46, hostile_ids),
            stationary_query_step,
            stationary_advance_step,
            "life-advance",
        )
        army_strengths = [
            {
                "status": "available",
                "army_id": army_id,
                "scope_role": "player",
                "war_ids": [88],
                "current_soldiers": 2,
                "maximum_soldiers": 2,
                "ai_base_power_raw": 1_200,
            },
            *[
                {
                    "status": "available",
                    "army_id": hostile_id,
                    "scope_role": "active_war_enemy",
                    "war_ids": [88],
                    "current_soldiers": enemy["soldiers"],
                    "maximum_soldiers": enemy["soldiers"],
                    "ai_base_power_raw": (
                        259_204 if hostile_id == hostile_ids[-1] else 1
                    ),
                }
                for hostile_id, enemy in zip(hostile_ids, enemies)
            ],
        ]
        history_without_fresh_stationary = [
            *base_history,
            old_root,
            old_preview_45,
            old_horizon_45,
            old_preview_46,
            old_horizon_46,
            old_stationary_horizon,
            restore,
            current_root,
            fresh_preview_45,
            fresh_horizon_45,
            fresh_preview_46,
            fresh_horizon_46,
        ]
        base = {
            "player": regular,
            "enemies": enemies,
            "score": -50,
            "date_raw": current_date_raw,
            "fallback": 1_741,
            "steps": steps,
            "player_side": "defender",
            "war_duration_days": 69,
            "termination_options": [current_options],
            "move_route_preview_supported": True,
            "route_contact_horizon_supported": True,
            "army_strengths": army_strengths,
            "army_strengths_status": "available",
        }

        query = _native_war_plan(
            **base,
            history=history_without_fresh_stationary,
        )

        self.assertEqual(
            query["phase"],
            "native_war_defender_native_rally_contact_horizon",
        )
        self.assertEqual(query["selected_step"], stationary_query_step)
        self.assertNotEqual(query["selected_step"], stationary_advance_step)
        self.assertEqual(
            query["native_rally_hold_binding"][
                "crossed_restore_history_indices"
            ],
            [10],
        )
        self.assertEqual(
            [
                rejection["target_province_id"]
                for rejection in query["route_rejections"]
            ],
            [45, 46],
        )

        fresh_stationary_horizon = _route_contact_row(
            1_399,
            army_id=army_id,
            origin=rally_province_id,
            target=rally_province_id,
            date_raw=current_date_raw,
            route=[],
            hostile_ids=hostile_ids,
            contact_free=True,
        )
        advance = _native_war_plan(
            **base,
            history=[
                *history_without_fresh_stationary,
                fresh_stationary_horizon,
            ],
        )

        self.assertEqual(
            advance["phase"],
            "native_war_defender_native_rally_contact_horizon_progress",
        )
        self.assertEqual(advance["selected_step"], stationary_advance_step)
        self.assertEqual(
            advance["contact_horizon"]["hostile_army_ids"],
            list(hostile_ids),
        )
        self.assertTrue(
            advance["contact_horizon"]["one_day_contact_free"]
        )

        # R0050: a score of -100 is not permission to surrender or to use an
        # ordinary life advance. A threatened two-soldier primary defender
        # may re-observe only through the exact four-hostile contact proof.
        r0050_options = copy.deepcopy(current_options)
        r0050_options.update(
            {
                "player_relative_war_score": -100,
                "war_duration_days": 153,
                "attacker_war_score": 100,
                "defender_war_score": -100,
                "active_casus_belli_identity": {
                    "database_index": 17,
                    "canonical_key": "vassalization_cb",
                },
            }
        )
        r0050_options["options"]["surrender"]["outcome"] = (
            "attacker_victory"
        )
        r0050_enemies = copy.deepcopy(enemies)
        r0050_enemies[-1]["soldiers"] = 7_756
        r0050_strengths = copy.deepcopy(army_strengths)
        r0050_strengths[-1]["current_soldiers"] = 7_756
        r0050_strengths[-1]["maximum_soldiers"] = 7_756
        r0050 = {
            **base,
            "score": -100,
            "war_duration_days": 153,
            "enemies": r0050_enemies,
            "army_strengths": r0050_strengths,
            "termination_options": [r0050_options],
        }
        r0050_missing_root = _native_war_plan(
            **r0050,
            history=[
                *base_history,
                old_root,
                old_preview_45,
                old_horizon_45,
                old_preview_46,
                old_horizon_46,
                old_stationary_horizon,
                restore,
            ],
        )
        self.assertEqual(
            r0050_missing_root["selected_step"],
            "query-campaign-root-context-v1",
        )
        r0050_query = _native_war_plan(
            **r0050,
            history=history_without_fresh_stationary,
        )
        self.assertEqual(
            r0050_query["phase"],
            "native_war_defender_native_rally_contact_horizon",
        )
        self.assertEqual(r0050_query["selected_step"], stationary_query_step)
        self.assertNotIn("contact_horizon", r0050_query)

        r0050_advance = _native_war_plan(
            **r0050,
            history=[
                *history_without_fresh_stationary,
                fresh_stationary_horizon,
            ],
        )
        self.assertEqual(
            r0050_advance["phase"],
            "native_war_defender_native_rally_contact_horizon_progress",
        )
        self.assertEqual(r0050_advance["selected_step"], stationary_advance_step)
        self.assertEqual(
            r0050_advance["contact_horizon"]["hostile_army_ids"],
            list(hostile_ids),
        )
        wrong_scope = _route_contact_row(
            1_399,
            army_id=army_id,
            origin=rally_province_id,
            target=rally_province_id,
            date_raw=current_date_raw,
            route=[],
            hostile_ids=hostile_ids[:-1],
            contact_free=True,
        )
        r0050_partial = _native_war_plan(
            **r0050,
            history=[*history_without_fresh_stationary, wrong_scope],
        )
        self.assertNotIn(
            r0050_partial["selected_step"],
            (stationary_advance_step, "life-advance", "surrender-war-88"),
        )
        self.assertEqual(r0050_partial["selected_step"], stationary_query_step)

    def test_primary_defender_native_rally_hold_fails_closed_outside_receipt(
        self,
    ) -> None:
        queried_date_raw = 53_282_400
        current_date_raw = 53_282_424
        gathering = _army(
            11,
            soldiers=None,
            province_id=8_750,
            controllable=True,
            army_state="gathering",
            army_state_code=5,
            route_province_ids=[],
            in_combat=False,
            retreating=False,
        )
        regular = {
            **gathering,
            "army_state": "regular",
            "army_state_code": 1,
        }
        enemy = _army(
            21,
            soldiers=None,
            province_id=45,
            controllable=False,
            move_target_province_id=46,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[46],
            in_combat=False,
            retreating=False,
        )
        queried_war = _war(
            allied_armies=[gathering],
            enemy_armies=[enemy],
            score=-50,
            player_side="defender",
            player_is_primary_war_leader=True,
            war_duration_days=69,
        )
        queried_snapshot = {
            **_snapshot(90),
            "paused": True,
            "map_ready": True,
            "native_revision": 90,
            "date_raw": queried_date_raw,
            "episode_run_id": None,
            "diagnostics": {"connection_generation": 1},
            "played_character": {"character_id": 707, "alive": True},
            "active_wars": [queried_war],
            "player_armies": [gathering],
        }
        options = _termination_options(
            score=-50, war_duration_days=69
        )
        options.update(
            {
                "player_side": "defender",
                "player_is_primary_war_leader": True,
            }
        )
        current_options = {
            **copy.deepcopy(options),
            "queried_snapshot_id": "session:90",
            "queried_revision": 90,
            "queried_native_revision": 90,
            "queried_connection_generation": 1,
            "episode_run_id": None,
        }
        termination_row = _termination_query_row(
            1, queried_snapshot, options=options
        )
        before = _war_progress(
            queried_date_raw,
            player=gathering,
            enemies=[enemy],
            score=-50,
        )
        after = _war_progress(
            current_date_raw,
            player=regular,
            enemies=[enemy],
            score=-50,
        )
        valid_history = [
            termination_row,
            _raise_troops_row(2, gathering),
            _advance_row(3, before, after),
            _campaign_root_row(
                4, date_raw=current_date_raw, capital_province_id=45
            ),
        ]
        base = {
            "player": regular,
            "enemies": [enemy],
            "score": -50,
            "date_raw": current_date_raw,
            "fallback": 1_741,
            "steps": (
                "query-war-termination-options-88",
                "query-campaign-root-context-v1",
                "life-advance",
            ),
            "player_side": "defender",
            "war_duration_days": 69,
            "termination_options": [current_options],
        }

        missing_root = _native_war_plan(
            **base, history=valid_history[:-1]
        )
        stale_root = copy.deepcopy(valid_history)
        stale_root[-1]["result"]["campaign_root_context"][
            "date_raw"
        ] -= 24
        stale_root_plan = _native_war_plan(**base, history=stale_root)
        for plan in (missing_root, stale_root_plan):
            self.assertEqual(
                plan["phase"],
                "native_war_defender_native_rally_hold_context",
            )
            self.assertEqual(
                plan["selected_step"], "query-campaign-root-context-v1"
            )

        moved_history = [
            *valid_history[:-1],
            {
                "index": 4,
                "command": "move-army-11-to-45",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 45,
                    },
                },
            },
            _campaign_root_row(
                5, date_raw=current_date_raw, capital_province_id=45
            ),
        ]
        stale_restore = [
            *valid_history[:-1],
            _restore_checkpoint_row(4, checkpoint_history_index=1),
            _termination_query_row(5, queried_snapshot, options=options),
            _campaign_root_row(
                6, date_raw=current_date_raw, capital_province_id=45
            ),
        ]
        wrong_army = {**regular, "army_id": 12}
        wrong_province = {**regular, "current_province_id": 8_751}
        route_to_rally = {
            **enemy,
            "move_target_province_id": 8_750,
            "route_province_ids": [8_750],
        }
        cases = {
            "missing_raise": {**base, "history": [valid_history[0], valid_history[-1]]},
            "intervening_move": {**base, "history": moved_history},
            "restore_before_raise": {**base, "history": stale_restore},
            "wrong_army": {
                **base,
                "player": wrong_army,
                "history": valid_history,
            },
            "wrong_province": {
                **base,
                "player": wrong_province,
                "history": valid_history,
            },
            "enemy_route_hits_rally": {
                **base,
                "enemies": [route_to_rally],
                "history": valid_history,
            },
            "attacker": {
                **base,
                "player_side": "attacker",
                "history": valid_history,
            },
            "unknown_primary": {
                **base,
                "player_is_primary_war_leader": None,
                "history": valid_history,
            },
            "terminal_score": {
                **base,
                "score": -100,
                "history": valid_history,
            },
        }
        for name, arguments in cases.items():
            with self.subTest(name=name):
                plan = _native_war_plan(**arguments)
                self.assertNotEqual(
                    plan.get("phase"),
                    "native_war_defender_native_rally_hold_progress",
                )
                self.assertNotEqual(plan.get("selected_step"), "life-advance")

    def test_termination_query_is_projected_for_eu_without_auto_surrender(
        self,
    ) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        termination = _termination_options(score=17)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=17,
                    )
                ],
                "player_armies": [player],
                "war_termination_options": [termination],
            },
            execute=lambda _step, _revision: {},
            action_steps=("surrender-war-88", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]
        assessment = plan["active_wars"][0]["war_exit_assessment"]

        self.assertEqual(assessment["status"], "evidence_partial")
        self.assertEqual(
            assessment["eu_inputs"]["war_score_breakdown"],
            termination["war_score_breakdown"],
        )
        self.assertTrue(
            assessment["eu_inputs"]["legal_options"]["surrender"]
        )
        self.assertEqual(
            assessment["eu_inputs"]["option_evidence"]["white_peace"][
                "ai_acceptance"
            ],
            {"raw": -1_300_000, "scale": 100_000},
        )
        self.assertNotIn("opponent_acceptance", assessment["unknown_fields"])
        self.assertIn("termination_terms", assessment["unknown_fields"])
        self.assertFalse(assessment["automatic_termination_enabled"])
        self.assertNotEqual(plan.get("selected_step"), "surrender-war-88")

    def test_planner_collects_native_termination_evidence_before_war_action(
        self,
    ) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=17,
                    )
                ],
                "player_armies": [player],
                "war_termination_options": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "query-war-termination-options-88",
                "move-army-11-to-41",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_termination_query")
        self.assertEqual(
            plan["selected_step"], "query-war-termination-options-88"
        )

    def test_negative_termination_query_is_reused_for_less_than_seven_days(
        self,
    ) -> None:
        queried = _termination_reuse_snapshot()
        history = [_termination_query_row(1, queried, decorated=True)]
        current = _termination_reuse_snapshot(
            date_raw=int(queried["date_raw"]) + 24,
            wars=copy.deepcopy(queried["active_wars"]),
            history=history,
        )
        current["active_wars"][0]["war_duration_days"] = 204

        plan = choose_one_life_turn(
            history,
            snapshot=current,
            action_steps=(
                "query-war-termination-options-88",
                "life-advance",
            ),
        )

        self.assertNotEqual(
            plan.get("selected_step"),
            "query-war-termination-options-88",
        )
        reuse = plan["active_wars"][0][
            "war_termination_negative_reuse"
        ]
        self.assertEqual(reuse["status"], "negative_assessment_reused")
        self.assertEqual(reuse["age_game_days"], 1)
        self.assertNotIn(
            "war_termination_options", plan["active_wars"][0]
        )

    def test_negative_termination_query_requeries_on_day_seven(self) -> None:
        queried = _termination_reuse_snapshot()
        history = [_termination_query_row(1, queried)]
        current = _termination_reuse_snapshot(
            date_raw=int(queried["date_raw"]) + 7 * 24,
            wars=copy.deepcopy(queried["active_wars"]),
            history=history,
        )

        plan = choose_one_life_turn(
            history,
            snapshot=current,
            action_steps=(
                "query-war-termination-options-88",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_termination_query")
        self.assertEqual(
            plan["selected_step"], "query-war-termination-options-88"
        )

    def test_claim_cb_negative_lease_clamps_to_day_365_gate(self) -> None:
        steps = ("query-war-termination-options-88", "life-advance")
        for queried_duration, elapsed_days, expected_query in (
            (364, 1, True),
            (363, 1, False),
            (363, 2, True),
        ):
            with self.subTest(
                queried_duration=queried_duration,
                elapsed_days=elapsed_days,
            ):
                queried = _termination_reuse_snapshot()
                queried["active_wars"][0][
                    "player_relative_war_score"
                ] = 37
                options = _termination_options(
                    score=37,
                    claim_cb_ready=True,
                    war_duration_days=queried_duration,
                )
                history = [
                    _termination_query_row(1, queried, options=options)
                ]
                current = _termination_reuse_snapshot(
                    date_raw=(
                        int(queried["date_raw"]) + elapsed_days * 24
                    ),
                    wars=copy.deepcopy(queried["active_wars"]),
                    history=history,
                )
                current["active_wars"][0]["war_duration_days"] = (
                    queried_duration + elapsed_days
                )

                plan = choose_one_life_turn(
                    history, snapshot=current, action_steps=steps
                )

                self.assertEqual(
                    plan.get("selected_step")
                    == "query-war-termination-options-88",
                    expected_query,
                )
                if not expected_query:
                    self.assertEqual(
                        plan["active_wars"][0][
                            "war_termination_negative_reuse"
                        ]["expires_date_raw"],
                        int(queried["date_raw"]) + 2 * 24,
                    )

    def test_negative_termination_reuse_invalidates_every_bound_epoch(
        self,
    ) -> None:
        queried = _termination_reuse_snapshot()
        base_row = _termination_query_row(1, queried)

        def current() -> dict[str, object]:
            return _termination_reuse_snapshot(
                date_raw=int(queried["date_raw"]) + 24,
                wars=copy.deepcopy(queried["active_wars"]),
                history=[copy.deepcopy(base_row)],
            )

        cases: list[tuple[str, dict[str, object], list[dict[str, object]]]] = []
        score_changed = current()
        score_changed["active_wars"][0]["player_relative_war_score"] = 18
        cases.append(("score", score_changed, [copy.deepcopy(base_row)]))
        side_changed = current()
        side_changed["active_wars"][0]["player_side"] = "defender"
        cases.append(("side", side_changed, [copy.deepcopy(base_row)]))
        role_changed = current()
        role_changed["active_wars"][0][
            "player_is_primary_war_leader"
        ] = False
        cases.append(("primary_role", role_changed, [copy.deepcopy(base_row)]))
        cb_changed = current()
        cb_rows = [copy.deepcopy(base_row)]
        cb_rows[0]["result"]["war_termination_options"][
            "active_casus_belli_identity"
        ] = {"database_index": 22, "canonical_key": "holy_war_cb"}
        cases.append(("cb_identity", cb_changed, cb_rows))
        option_changed = current()
        option_rows = [copy.deepcopy(base_row)]
        option_rows[0]["result"]["war_termination_options"]["options"][
            "white_peace"
        ]["recipient_response"]["would_accept_now"] = True
        cases.append(("option_shape", option_changed, option_rows))
        war_set_changed = current()
        extra_war = copy.deepcopy(war_set_changed["active_wars"][0])
        extra_war["war_id"] = 99
        war_set_changed["active_wars"].append(extra_war)
        cases.append(("war_set", war_set_changed, [copy.deepcopy(base_row)]))
        episode_changed = current()
        episode_changed["episode_run_id"] = "native-29829-other"
        cases.append(("episode", episode_changed, [copy.deepcopy(base_row)]))
        connection_changed = current()
        connection_changed["diagnostics"]["connection_generation"] = 4
        cases.append(
            ("connection", connection_changed, [copy.deepcopy(base_row)])
        )
        character_changed = current()
        character_changed["played_character"]["character_id"] = 29_830
        cases.append(
            ("character", character_changed, [copy.deepcopy(base_row)])
        )
        dead = current()
        dead["played_character"]["alive"] = False
        cases.append(("death", dead, [copy.deepcopy(base_row)]))
        terminal = current()
        terminal["one_life_terminal_reason"] = "played_character_dead"
        cases.append(("terminal", terminal, [copy.deepcopy(base_row)]))
        for label, command in (
            ("event", "select-event-option-1"),
            (
                "pending_interaction",
                "query-pending-character-interaction-context-v1",
            ),
        ):
            snapshot = current()
            rows = [
                copy.deepcopy(base_row),
                {"index": 2, "command": command, "ok": True, "result": {}},
            ]
            cases.append((label, snapshot, rows))

        for label, snapshot, rows in cases:
            with self.subTest(label=label):
                reuse = _negative_war_termination_reuse(
                    rows,
                    snapshot,
                    active_wars=snapshot["active_wars"],
                    war=snapshot["active_wars"][0],
                )
                self.assertIsNone(reuse)

    def test_negative_termination_reuse_is_independent_per_active_war(
        self,
    ) -> None:
        initial = _termination_reuse_snapshot()
        second_war = copy.deepcopy(initial["active_wars"][0])
        second_war["war_id"] = 99
        second_war["targeted_title_ids"] = [2_399]
        queried = _termination_reuse_snapshot(
            wars=[copy.deepcopy(initial["active_wars"][0]), second_war]
        )
        both_rows = [
            _termination_query_row(1, queried, war_id=88),
            _termination_query_row(
                2, queried, war_id=99, options=_termination_options(99)
            ),
        ]
        current = _termination_reuse_snapshot(
            date_raw=int(queried["date_raw"]) + 24,
            wars=copy.deepcopy(queried["active_wars"]),
            history=both_rows,
        )
        steps = (
            "query-war-termination-options-88",
            "query-war-termination-options-99",
            "life-advance",
        )

        all_reused = choose_one_life_turn(
            both_rows, snapshot=current, action_steps=steps
        )
        self.assertNotIn(
            all_reused.get("selected_step"),
            {
                "query-war-termination-options-88",
                "query-war-termination-options-99",
            },
        )
        self.assertTrue(
            all(
                "war_termination_negative_reuse" in war
                for war in all_reused["active_wars"]
            )
        )

        only_first = choose_one_life_turn(
            both_rows[:1], snapshot=current, action_steps=steps
        )
        self.assertEqual(
            only_first["selected_step"],
            "query-war-termination-options-99",
        )

    def test_historical_positive_termination_result_only_triggers_fresh_query(
        self,
    ) -> None:
        queried = _termination_reuse_snapshot()
        queried["active_wars"][0]["player_relative_war_score"] = 37
        positive = _termination_options(
            score=37,
            claim_cb_ready=True,
            war_duration_days=436,
        )
        history = [_termination_query_row(1, queried, options=positive)]
        current = _termination_reuse_snapshot(
            date_raw=int(queried["date_raw"]) + 24,
            wars=copy.deepcopy(queried["active_wars"]),
            history=history,
        )

        plan = choose_one_life_turn(
            history,
            snapshot=current,
            action_steps=(
                "query-war-termination-options-88",
                "query-war-termination-terms-v1-88",
                "offer-white-peace-88",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_termination_query")
        self.assertEqual(
            plan["selected_step"], "query-war-termination-options-88"
        )
        self.assertNotEqual(plan["selected_step"], "offer-white-peace-88")

    def test_r767_positive_surrender_row_never_enters_negative_lease(
        self,
    ) -> None:
        queried = _termination_reuse_snapshot()
        queried["active_wars"][0]["player_relative_war_score"] = -44
        positive = _termination_options(score=-44, war_duration_days=216)
        positive["active_casus_belli_identity"] = {
            "database_index": 17,
            "canonical_key": "individual_county_de_jure_cb",
        }
        history = [_termination_query_row(1, queried, options=positive)]
        current = _termination_reuse_snapshot(
            date_raw=int(queried["date_raw"]) + 24,
            wars=copy.deepcopy(queried["active_wars"]),
            history=history,
        )

        plan = choose_one_life_turn(
            history,
            snapshot=current,
            action_steps=(
                "query-war-termination-options-88",
                "surrender-war-88",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_termination_query")
        self.assertEqual(
            plan["selected_step"], "query-war-termination-options-88"
        )

    def test_claim_cb_white_peace_planner_queries_terms_then_offers(self) -> None:
        without_terms = _ready_white_peace_snapshot(include_terms=False)

        terms_plan = choose_one_life_turn(
            [],
            snapshot=without_terms,
            action_steps=(
                "query-war-termination-options-88",
                "query-war-termination-terms-v1-88",
                "offer-white-peace-88",
                "life-advance",
            ),
        )

        self.assertEqual(
            terms_plan["phase"], "native_war_termination_terms_v1_query"
        )
        self.assertEqual(
            terms_plan["selected_step"],
            "query-war-termination-terms-v1-88",
        )

        weak_terms = _termination_terms(strong=False)
        ready = _ready_white_peace_snapshot(terms=weak_terms)
        offer_plan = choose_one_life_turn(
            [],
            snapshot=ready,
            action_steps=(
                "query-war-termination-options-88",
                "query-war-termination-terms-v1-88",
                "offer-white-peace-88",
                "life-advance",
            ),
        )

        self.assertEqual(
            offer_plan["phase"],
            "native_war_claim_cb_minimal_white_peace",
        )
        self.assertEqual(
            offer_plan["selected_step"], "offer-white-peace-88"
        )
        self.assertTrue(offer_plan["decision"]["weak_claims_allowed"])
        self.assertFalse(offer_plan["decision"]["native_ai_equivalent"])

    def test_claim_cb_white_peace_rejects_stale_final_no_and_other_cb(self) -> None:
        rejected_options = _termination_options(
            score=37,
            claim_cb_ready=True,
            war_duration_days=436,
            recipient_decision_status_raw=2,
        )
        rejected_options["options"]["white_peace"]["ai_acceptance"] = {
            "raw": 1_279_120,
            "scale": 100_000,
        }
        rejected = _ready_white_peace_snapshot(options=rejected_options)
        stale = _ready_white_peace_snapshot()
        stale["war_termination_options"][0][
            "queried_native_revision"
        ] = 6
        holy = _ready_white_peace_snapshot()
        holy["war_termination_options"][0]["active_casus_belli_identity"] = {
            "database_index": 22,
            "canonical_key": "holy_war_cb",
        }
        steps = (
            "query-war-termination-options-88",
            "query-war-termination-terms-v1-88",
            "offer-white-peace-88",
            "life-advance",
        )

        for name, snapshot in (
            ("final_rejection", rejected),
            ("stale", stale),
            ("holy_war", holy),
        ):
            with self.subTest(name=name):
                plan = choose_one_life_turn(
                    [], snapshot=snapshot, action_steps=steps
                )
                self.assertNotEqual(
                    plan.get("selected_step"), "offer-white-peace-88"
                )

    def test_enforce_demands_cross_war_precedes_minimal_white_peace(self) -> None:
        snapshot = _ready_white_peace_snapshot()
        snapshot["active_wars"].append(
            _war(
                war_id=99,
                score=100,
                allied_armies=[],
                enemy_armies=[],
            )
        )

        plan = choose_one_life_turn(
            [],
            snapshot=snapshot,
            action_steps=(
                "enforce-demands-99",
                "offer-white-peace-88",
                "life-advance",
            ),
        )

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-99")

    def test_white_peace_history_advances_once_and_honors_720_raw_cooldown(
        self,
    ) -> None:
        submitted_date_raw = 53_177_976
        history = [
            {
                "index": 1,
                "command": "offer-white-peace-88",
                "ok": True,
                "result": {
                    "war_termination_result": {
                        "status": "submitted_pending",
                        "war_id": 88,
                        "outcome": "white_peace",
                        "episode_run_id": "native-29829-ready",
                        "submitted_date_raw": submitted_date_raw,
                    }
                },
            }
        ]
        steps = ("offer-white-peace-88", "life-advance")
        same_day = _ready_white_peace_snapshot(
            date_raw=submitted_date_raw, history=history
        )

        same_day_plan = choose_one_life_turn(
            history, snapshot=same_day, action_steps=steps
        )

        self.assertEqual(
            same_day_plan["phase"],
            "native_war_white_peace_response_advance",
        )
        self.assertEqual(same_day_plan["selected_step"], "life-advance")

        response_window = _ready_white_peace_snapshot(
            date_raw=submitted_date_raw + 24,
            history=history,
        )
        response_window["war_termination_options"] = []
        response_window["war_termination_terms"] = []
        response_plan = choose_one_life_turn(
            history,
            snapshot=response_window,
            action_steps=(
                "query-war-termination-options-88",
                "offer-white-peace-88",
                "life-advance",
            ),
        )
        self.assertNotEqual(
            response_plan.get("selected_step"),
            "query-war-termination-options-88",
        )
        self.assertNotEqual(
            response_plan.get("selected_step"), "offer-white-peace-88"
        )

        for elapsed_raw, expected_offer in ((719, False), (720, True)):
            restored = _ready_white_peace_snapshot(
                date_raw=submitted_date_raw + elapsed_raw,
                history=history,
            )
            plan = choose_one_life_turn(
                history, snapshot=restored, action_steps=steps
            )
            self.assertEqual(
                plan.get("selected_step") == "offer-white-peace-88",
                expected_offer,
            )

    def test_planner_does_not_select_crash_disabled_exit_terms_v2(
        self,
    ) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=17,
                    )
                ],
                "player_armies": [player],
                "war_termination_options": [_termination_options()],
                "war_termination_exit_terms": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "query-war-termination-exit-terms-v2-88",
                "move-army-11-to-41",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_complete_exit_terms_still_require_campaign_forecast(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        exit_terms = _termination_exit_terms_v2()
        exit_terms["war_id"] = 88
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=17,
                    )
                ],
                "player_armies": [player],
                "war_termination_options": [_termination_options()],
                "war_termination_exit_terms": [exit_terms],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "surrender-war-88",
                "offer-white-peace-88",
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]
        assessment = plan["active_wars"][0]["war_exit_assessment"]

        self.assertNotIn("termination_terms", assessment["unknown_fields"])
        self.assertNotIn(
            "primary_resource_balances", assessment["unknown_fields"]
        )
        self.assertIn("campaign_outcome_forecast", assessment["unknown_fields"])
        self.assertFalse(assessment["automatic_termination_enabled"])
        self.assertNotIn(
            plan.get("selected_step"),
            {"surrender-war-88", "offer-white-peace-88"},
        )

    def test_decorated_query_history_never_recreates_a_termination_cache(
        self,
    ) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        decorated_query = {
            "command": "auto-turn",
            "ok": True,
            "result": {
                "selected_step": "query-war-termination-options-88",
                "result": {
                    "war_termination_options": _termination_options(),
                    "query_sequence": 7,
                },
            },
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(12),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=17,
                    )
                ],
                "player_armies": [player],
                "native_command_history": [decorated_query],
                "war_termination_options": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=("surrender-war-88", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertNotEqual(plan.get("selected_step"), "surrender-war-88")
        self.assertNotIn(
            "war_termination_options", plan["active_wars"][0]
        )

    def test_primary_defender_may_raise_before_exit_evidence_gate(self) -> None:
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[],
                        enemy_armies=[],
                        score=-10,
                        player_side="defender",
                    )
                ],
                "player_armies": [],
            },
            execute=lambda _step, _revision: {},
            action_steps=("raise-troops-default", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_raise")
        self.assertEqual(plan["selected_step"], "raise-troops-default")

    def test_defender_with_unknown_primary_identity_still_fails_closed(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="regular",
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        score=-10,
                        player_side="defender",
                        player_is_primary_war_leader=None,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("life-advance",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(
            plan["phase"], "defensive_war_primary_identity_required"
        )
        self.assertIsNone(plan["selected_step"])
        self.assertEqual(
            plan["required_capabilities"], ["game.state.active-wars"]
        )

    def test_primary_defender_gathering_progresses_without_exit_forecast(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="gathering",
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        score=0,
                        player_side="defender",
                        war_objective_province_ids=[77],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("life-advance",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_gathering_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(
            plan["active_wars"][0]["war_exit_assessment"]["status"],
            "unavailable",
        )

    def test_primary_defender_enforces_victory_before_exit_evidence_gate(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="regular",
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        score=100,
                        player_side="defender",
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("enforce-demands-88", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_enforce_demands")
        self.assertEqual(plan["selected_step"], "enforce-demands-88")

    def test_score_zero_primary_defender_never_enforces_from_bad_query_label(
        self,
    ) -> None:
        player = _army(
            11,
            soldiers=None,
            province_id=20,
            controllable=True,
            army_state="gathering",
        )
        bad_options = _termination_options(score=0)
        bad_options["player_side"] = "defender"
        bad_options["attacker_war_score"] = 0
        bad_options["defender_war_score"] = 0
        bad_options["options"]["victory"]["available"] = True
        bad_options["options"]["victory"][
            "native_validator_passed"
        ] = True
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        score=0,
                        player_side="defender",
                    )
                ],
                "player_armies": [player],
                "war_termination_options": [bad_options],
            },
            execute=lambda _step, _revision: {},
            action_steps=("enforce-demands-88", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_gathering_progress")
        self.assertEqual(plan["selected_step"], "life-advance")

    def test_native_war_planner_holds_on_primary_opponent_fallback(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        step = "move-army-11-to-77"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        enemy_primary_default_raise_province_id=77,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(step,),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_non_primary_war_participant_does_not_enforce_at_100(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        move_step = "move-army-11-to-41"
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9),
                "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[enemy],
                        score=100,
                        player_is_primary_war_leader=False,
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=(
                "enforce-demands-88",
                move_step,
                "life-advance",
            ),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(plan["selected_step"])

    def test_r0088_nonprimary_ally_requires_stationary_one_day_contact_proof(
        self,
    ) -> None:
        date_raw = 53_350_080
        war_id = 201_326_601
        army_id = 452_985_015
        hostile_ids = (402_653_375, 436_207_652)
        player = _army(
            army_id, soldiers=932, province_id=45, controllable=True,
            army_state="regular", in_combat=False, retreating=False,
            route_province_ids=[],
        )
        ally = _army(
            369_099_182, soldiers=1_310, province_id=46,
            controllable=False, army_state="regular",
            route_province_ids=[],
        )
        enemies = [
            _army(
                hostile_ids[0], soldiers=837, province_id=1_741,
                controllable=False, army_state="regular",
                route_province_ids=[],
            ),
            _army(
                hostile_ids[1], soldiers=0, province_id=1_741,
                controllable=False, army_state="gathering",
                route_province_ids=[],
            ),
        ]
        query_step = query_route_contact_horizon_step(
            army_id, 45, hostile_ids
        )
        advance_step = advance_route_contact_horizon_step(
            army_id, 45, hostile_ids
        )
        root = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=45,
            held_county_capital_province_ids=(45, 46),
        )
        strengths = [
            _army_strength(
                army_id, "player", [war_id], current=932, maximum=932,
                base_power_raw=2_360_000_000,
            ),
            _army_strength(
                369_099_182, "active_war_ally", [war_id],
                current=1_310, maximum=1_346,
                base_power_raw=4_071_600_000,
            ),
            _army_strength(
                hostile_ids[0], "active_war_enemy", [war_id],
                current=837, maximum=837,
                base_power_raw=2_720_800_000,
            ),
            _army_strength(
                hostile_ids[1], "active_war_enemy", [war_id],
                current=0, maximum=0, base_power_raw=0,
            ),
        ]
        base = {
            "player": player,
            "allied_armies": [player, ally],
            "enemies": enemies,
            "war_id": war_id,
            "score": 0,
            "date_raw": date_raw,
            "fallback": 1_741,
            "player_is_primary_war_leader": False,
            "negative_reuse_expires_date_raw": date_raw + 48,
            "army_strengths": strengths,
            "army_strengths_status": "available",
            "route_contact_horizon_supported": True,
            "steps": (
                "query-campaign-root-context-v1",
                query_step, advance_step, "life-advance",
            ),
        }

        query = _native_war_plan(**base, history=[root])
        self.assertEqual(
            query["phase"], "native_war_attacker_ally_capital_contact_query"
        )
        self.assertEqual(query["selected_step"], query_step)

        safe_proof = _route_contact_row(
            2, army_id=army_id, origin=45, target=45,
            date_raw=date_raw, route=[], hostile_ids=hostile_ids,
            contact_free=True,
        )
        progress = _native_war_plan(**base, history=[root, safe_proof])
        self.assertEqual(
            progress["phase"], "native_war_attacker_ally_capital_contact_progress"
        )
        self.assertEqual(progress["selected_step"], advance_step)
        self.assertNotEqual(progress["selected_step"], "life-advance")

        conflict = _route_contact_row(
            2, army_id=army_id, origin=45, target=45,
            date_raw=date_raw, route=[], hostile_ids=hostile_ids,
            contact_free=False,
        )
        blocked = _native_war_plan(**base, history=[root, conflict])
        self.assertEqual(
            blocked["phase"], "native_war_attacker_ally_capital_contact_blocked"
        )
        self.assertIsNone(blocked["selected_step"])

        stale_proof = _route_contact_row(
            2, army_id=army_id, origin=45, target=45,
            date_raw=date_raw - 24, route=[], hostile_ids=hostile_ids,
            contact_free=True,
        )
        stale = _native_war_plan(**base, history=[root, stale_proof])
        self.assertIsNone(stale["selected_step"])

        incomplete_enemies = copy.deepcopy(enemies)
        del incomplete_enemies[1]["route_province_ids"]
        incomplete = _native_war_plan(
            **{**base, "enemies": incomplete_enemies},
            history=[root, safe_proof],
        )
        self.assertNotEqual(incomplete["selected_step"], advance_step)

        no_termination_negative = _native_war_plan(
            **{**base, "negative_reuse_expires_date_raw": None},
            history=[root, safe_proof],
        )
        self.assertNotEqual(no_termination_negative["selected_step"], advance_step)

        unsupported = _native_war_plan(
            **{**base, "route_contact_horizon_supported": False},
            history=[root],
        )
        self.assertEqual(
            unsupported["phase"],
            "native_war_attacker_ally_capital_contact_unsupported",
        )
        self.assertIsNone(unsupported["selected_step"])

        other_capital = _campaign_root_row(
            1, date_raw=date_raw, capital_province_id=46,
            held_county_capital_province_ids=(45, 46),
        )
        off_capital = _native_war_plan(**base, history=[other_capital])
        self.assertEqual(off_capital["phase"], "native_war_counterpolicy_hold")
        self.assertIsNone(off_capital["selected_step"])

    def test_native_war_planner_does_not_advance_unobservable_enemy_move_ack(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            {
                "index": 2,
                "command": "life-advance",
                "ok": True,
                "result": {"elapsed_days": 5},
            },
            {
                "index": 3,
                "command": "life-advance",
                "ok": True,
                "result": {"elapsed_days": 5},
            },
        ]
        state = {
            **_snapshot(9),
            "date_raw": 24_240,
            "native_command_history": history,
            "active_wars": [
                _war(
                    allied_armies=[player],
                    enemy_armies=[],
                    war_objective_province_ids=[41],
                )
            ],
            "player_armies": [player],
        }
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: dict(state),
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["move_intent"]["elapsed_days"], 10)

        state["date_raw"] = 26_160
        expired = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(expired["phase"], "native_war_pursuit")
        self.assertEqual(expired["selected_step"], "move-army-11-to-41")

    def test_native_move_intent_ends_when_enemy_target_changes(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=42, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            }
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "date_raw": 24_024,
                "native_command_history": history,
            "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        war_objective_province_ids=[42],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-42", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-42")

    def test_native_move_intent_does_not_cross_checkpoint_restore(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "accepted": True,
                    "war_action": {
                        "status": "move_submitted",
                        "army_id": 11,
                        "target_province_id": 41,
                        "submitted_date_raw": 24_000,
                    },
                },
            },
            {
                "index": 2,
                "command": "restore-checkpoint",
                "ok": True,
                "result": {"status": "restored"},
            },
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(11),
                "date_raw": 23_976,
                "native_command_history": history,
            "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        war_objective_province_ids=[41],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-41")

    def test_native_war_planner_retries_date_less_legacy_deferred_move(self) -> None:
        player = _army(11, soldiers=900, province_id=20, controllable=True)
        enemy = _army(21, soldiers=1_100, province_id=41, controllable=False)
        history = [
            {
                "index": 1,
                "command": "move-army-11-to-41",
                "ok": True,
                "result": {
                    "war_action": {"status": "move_deferred"}
                },
            }
        ]
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(9, history),
            "active_wars": [
                    _war(
                        allied_armies=[player],
                        enemy_armies=[],
                        war_objective_province_ids=[41],
                    )
                ],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("move-army-11-to-41", "life-advance"),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_war_pursuit")
        self.assertEqual(plan["selected_step"], "move-army-11-to-41")

    def test_native_war_planner_disbands_residual_postwar_army(self) -> None:
        player = _army(
            71, soldiers=1_100, province_id=50, controllable=True
        )
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(10),
                "active_wars": [],
                "player_armies": [player],
            },
            execute=lambda _step, _revision: {},
            action_steps=("disband-army-71",),
        )

        plan = GameplayBridgeService(driver).plan_turn()["plan"]

        self.assertEqual(plan["phase"], "native_postwar_disband")
        self.assertEqual(plan["selected_step"], "disband-army-71")

    def test_native_war_planner_checkpoints_verified_postwar_cleanup(self) -> None:
        history = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
            {"index": 2, "command": "disband-army-71", "ok": True},
        ]
        plan = choose_one_life_turn(
            history,
            snapshot={
                **_snapshot(10, history),
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [],
            },
            action_steps=("save-checkpoint", "query-declarable-wars"),
        )

        self.assertEqual(plan["phase"], "native_postwar_checkpoint")
        self.assertEqual(plan["selected_step"], "save-checkpoint")
        self.assertEqual(plan["postwar_disband_history_index"], 2)

        residual = choose_one_life_turn(
            history,
            snapshot={
                **_snapshot(10, history),
                "active_wars": [],
                "player_armies": [
                    _army(
                        72,
                        soldiers=250,
                        province_id=50,
                        controllable=False,
                    )
                ],
                "declarable_wars": [],
            },
            action_steps=("save-checkpoint", "query-declarable-wars"),
        )
        self.assertNotEqual(
            residual["phase"], "native_postwar_checkpoint"
        )

        history.append(
            {"index": 3, "command": "save-checkpoint", "ok": True}
        )
        after_save = choose_one_life_turn(
            history,
            snapshot={
                **_snapshot(11, history),
                "active_wars": [],
                "player_armies": [],
                "declarable_wars": [],
            },
            action_steps=("save-checkpoint", "query-declarable-wars"),
        )
        self.assertEqual(after_save["phase"], "native_war_discovery")
        self.assertEqual(after_save["selected_step"], "query-declarable-wars")

    def test_native_war_planner_holds_peace_after_material_white_peace(self) -> None:
        history = [
            {"index": 1, "command": "save-checkpoint", "ok": True},
            {
                "index": 2,
                "command": "offer-white-peace-88",
                "ok": True,
                "result": {
                    "war_termination_result": {
                        "status": "submitted_pending",
                        "war_id": 88,
                        "outcome": "white_peace",
                        "submitted_date_raw": 1_000,
                        "episode_run_id": "ordinary-episode",
                    }
                },
            },
            {"index": 3, "command": "disband-army-71", "ok": True},
            {"index": 4, "command": "save-checkpoint", "ok": True},
        ]
        snapshot = {
            **_snapshot(11, history),
            "date_raw": 1_168,
            "episode_run_id": "ordinary-episode",
            "active_wars": [],
            "player_armies": [],
            "declarable_wars": [{"declaration_id": 1}],
        }

        plan = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps=("life-advance", "query-declarable-wars"),
        )

        self.assertEqual(plan["phase"], "native_postwar_reentry_cooldown")
        self.assertEqual(plan["selected_step"], "life-advance")
        self.assertEqual(plan["postwar_reentry"]["war_id"], 88)
        self.assertEqual(plan["postwar_reentry"]["remaining_raw"], 552)

        snapshot["date_raw"] = 1_720
        expired = choose_one_life_turn(
            history,
            snapshot=snapshot,
            action_steps=("life-advance", "query-declarable-wars"),
        )
        self.assertNotEqual(expired["phase"], "native_postwar_reentry_cooldown")

    def test_typed_war_service_routes_exact_native_commands(self) -> None:
        player = _army(
            81, soldiers=1_300, province_id=50, controllable=True
        )
        enemy = _army(
            91, soldiers=1_900, province_id=60, controllable=False
        )
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(14),
                "active_wars": [
                    _war(allied_armies=[player], enemy_armies=[enemy])
                ],
                "player_armies": [player],
                "war_termination_options": [_termination_options()],
            },
            execute=lambda step, revision: calls.append((step, revision))
            or {"status": "submitted"},
            action_steps=(
                "raise-troops-default",
                "move-army-81-to-60",
                "disband-army-81",
                "enforce-demands-88",
            ),
        )
        service = GameplayBridgeService(driver)

        state = service.war_state()
        self.assertEqual(state["status"], "active")
        self.assertEqual(state["active_wars"][0]["war_id"], 88)
        self.assertEqual(
            state["war_termination_options"][0]["war_id"], 88
        )
        service.raise_troops_default(expected_revision=14)
        service.move_army(81, 60, expected_revision=14)
        service.disband_army(81, expected_revision=14)
        service.enforce_demands(88, expected_revision=14)

        self.assertEqual(
            calls,
            [
                ("raise-troops-default", 14),
                ("move-army-81-to-60", 14),
                ("disband-army-81", 14),
                ("enforce-demands-88", 14),
            ],
        )

    def test_service_auto_turn_plans_and_executes_one_supported_step(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(11),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("save-checkpoint",),
        )

        result = GameplayBridgeService(driver).auto_turn()

        self.assertEqual(result["status"], "executed")
        self.assertEqual(result["selected_step"], "save-checkpoint")
        self.assertEqual(calls, [("save-checkpoint", 11)])

    def test_service_auto_turn_can_intercept_before_submission(self) -> None:
        calls: list[tuple[str, int | None]] = []
        intercepted: list[dict[str, object]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(11),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("save-checkpoint",),
        )

        def before_submit(frame: dict[str, object]) -> dict[str, object]:
            intercepted.append(frame)
            return {"reason": "candidate-terminal-boundary"}

        result = GameplayBridgeService(driver).auto_turn(
            before_submit=before_submit
        )

        self.assertEqual(result["status"], "intercepted")
        self.assertEqual(result["selected_step"], "save-checkpoint")
        self.assertEqual(result["interception"]["reason"], "candidate-terminal-boundary")
        self.assertEqual(intercepted[0]["revision"], 11)
        self.assertEqual(calls, [])

    def test_service_auto_turn_binds_pre_submission_revision_context(
        self,
    ) -> None:
        calls: list[tuple[str, int | None]] = []

        def execute(
            step: str, revision: int | None
        ) -> dict[str, object]:
            calls.append((step, revision))
            raise PreSubmissionRevisionMismatchError(
                "native gameplay revision mismatch: expected 517, current 518"
            )

        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(517),
            execute=execute,
            action_steps=("save-checkpoint",),
        )

        with self.assertRaises(PreSubmissionRevisionMismatchError) as observed:
            GameplayBridgeService(driver).auto_turn()

        self.assertEqual(calls, [("save-checkpoint", 517)])
        self.assertEqual(observed.exception.replan_count, 0)
        self.assertEqual(observed.exception.selected_step, "save-checkpoint")
        self.assertIsInstance(observed.exception.plan, dict)
        assert observed.exception.plan is not None
        self.assertEqual(
            observed.exception.plan["selected_step"], "save-checkpoint"
        )

    def test_service_auto_turn_does_not_retry_unknown_bridge_failure(self) -> None:
        calls: list[tuple[str, int | None]] = []

        def execute(
            step: str, revision: int | None
        ) -> dict[str, object]:
            calls.append((step, revision))
            raise BridgeUnavailableError("fixture transport failed")

        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(517),
            execute=execute,
            action_steps=("save-checkpoint",),
        )

        with self.assertRaises(BridgeUnavailableError) as observed:
            GameplayBridgeService(driver).auto_turn()

        self.assertEqual(calls, [("save-checkpoint", 517)])
        self.assertEqual(observed.exception.selected_step, "save-checkpoint")
        self.assertIsInstance(observed.exception.plan, dict)
        assert observed.exception.plan is not None
        self.assertEqual(
            observed.exception.plan["selected_step"], "save-checkpoint"
        )

    def test_service_auto_turn_binds_plan_to_postcondition_failure(self) -> None:
        partial_result = {
            "step": "save-checkpoint",
            "ending_date_raw": 53_216_448,
            "snapshot_id": "native:9",
            "revision": 10,
        }
        failure = StepPostconditionError(
            "fixture postcondition failed",
            step_result=partial_result,
            selected_step="driver-placeholder",
        )

        def fail_postcondition(
            _step: str, _revision: int | None
        ) -> dict[str, object]:
            raise failure

        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: _snapshot(11),
            execute=fail_postcondition,
            action_steps=("save-checkpoint",),
        )

        with self.assertRaises(StepPostconditionError) as observed:
            GameplayBridgeService(driver).auto_turn()

        self.assertIs(observed.exception, failure)
        self.assertEqual(failure.selected_step, "save-checkpoint")
        self.assertIsInstance(failure.plan, dict)
        assert failure.plan is not None
        self.assertEqual(failure.plan["selected_step"], "save-checkpoint")
        self.assertEqual(failure.step_result, partial_result)

    def test_service_auto_turn_ends_native_one_life_on_player_death(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="native-headless",
            snapshot=lambda: {
                **_snapshot(12),
                "played_character": {"character_id": 707, "alive": False},
            },
            execute=lambda step, revision: calls.append((step, revision))
            or {"terminal": True, "continue_as_heir_after_death": False},
            action_steps=("death-terminal",),
        )

        result = GameplayBridgeService(driver).auto_turn()

        self.assertEqual(result["selected_step"], "death-terminal")
        self.assertTrue(result["result"]["terminal"])
        self.assertEqual(calls, [("death-terminal", 12)])

    def test_service_exposes_and_finalizes_matching_one_life_settlement(
        self,
    ) -> None:
        settlement = {
            "ready": True,
            "commit_serial": 1,
            "source_character_id": 707,
            "final_score": 405.25,
            "score_before_reject": 410,
            "record_candidate": 405,
            "old_record": 405,
            "record_delta": 0,
            "blessing_count": 3,
            "refusal_count": 1,
            "contract_progress": 7,
            "record_written": False,
        }
        snapshot = {
            **_snapshot(12),
            "played_character": {"character_id": 808, "alive": True},
            "episode_character_id": 707,
            "one_life_terminal": True,
            "one_life_terminal_reason": "played_character_changed",
            "one_life_settlement": settlement,
        }
        driver = mock.Mock()
        driver.take_snapshot.return_value = snapshot
        driver.capabilities.return_value = {
            "action_steps": ["death-terminal"],
            "bridge_capabilities": [ONE_LIFE_SETTLEMENT_CAPABILITY],
        }
        driver.execute_step.return_value = {
            "terminal": True,
            "settlement_status": "complete",
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": 405.25,
        }
        service = GameplayBridgeService(driver)

        projected = service.one_life_settlement()
        finalized = service.settle_one_life(expected_revision=12)

        self.assertEqual(projected["status"], "ready")
        self.assertEqual(projected["episode_character_id"], 707)
        self.assertEqual(finalized["score"], 405.25)
        self.assertFalse(finalized["continue_as_heir_after_death"])
        self.assertEqual(finalized["heir_gameplay_actions"], 0)
        driver.execute_step.assert_called_once_with(
            "death-terminal", expected_revision=12
        )

    def test_cross_run_achievements_accept_native_war_prefixes_only(self) -> None:
        commands = [
            {
                "command": "enforce-demands-88",
                "ok": True,
                "result": {
                    "war_victory": {
                        "status": "victory_enforced",
                        "war_id": 88,
                    }
                },
            },
            {
                "command": "disband-army-81",
                "ok": True,
                "result": {
                    "war_action": {"status": "disbanded", "army_id": 81}
                },
            },
            {
                "command": "arrange-marriage-707-809",
                "ok": True,
                "result": {
                    "marriage_action": {
                        "status": "proposal_submitted",
                        "candidate_character_id": 809,
                    }
                },
            },
        ]
        terminal = {
            "terminal": True,
            "terminal_reason": "played_character_dead",
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": 405.25,
        }
        with tempfile.TemporaryDirectory() as temporary:
            recorded = record_one_life_episode(
                Path(temporary),
                run_id="native-707-settlement",
                commands=commands,
                terminal=terminal,
            )

        achievements = recorded["recorded_episode"]["achievements"]
        self.assertTrue(achievements["palermo_holy_war_won"])
        self.assertTrue(achievements["armies_disbanded"])
        self.assertFalse(achievements["danish_betrothal_accepted"])

    def test_cross_run_marriage_requires_native_relationship_confirmation(self) -> None:
        commands = [
            {
                "command": "arrange-marriage-707-809",
                "ok": True,
                "result": {
                    "marriage_action": {
                        "status": "proposal_submitted",
                        "played_character_id": 707,
                        "candidate_character_id": 809,
                    },
                    "marriage_result": {
                        "status": "accepted_betrothal",
                        "played_character_id": 707,
                        "candidate_character_id": 809,
                        "source": "native_relationship_snapshot",
                    },
                },
            }
        ]
        terminal = {
            "terminal": True,
            "terminal_reason": "played_character_dead",
            "continue_as_heir_after_death": False,
            "heir_gameplay_actions": 0,
            "score": 405.25,
        }
        with tempfile.TemporaryDirectory() as temporary:
            recorded = record_one_life_episode(
                Path(temporary),
                run_id="native-707-married",
                commands=commands,
                terminal=terminal,
            )

        self.assertTrue(
            recorded["recorded_episode"]["achievements"][
                "danish_betrothal_accepted"
            ]
        )

    def test_bridge_driver_adapts_to_backend_neutral_runner(self) -> None:
        calls: list[tuple[str, int | None]] = []
        driver = CallbackGameplayDriver(
            backend_id="mcp",
            snapshot=lambda: _snapshot(12),
            execute=lambda step, revision: calls.append((step, revision))
            or {"step": step},
            action_steps=("life-advance",),
        )
        executor = BridgeGameplayStepExecutor(driver, expected_revision=lambda: 12)
        self.assertEqual(executor.execute_step("life-advance")["backend_id"], "mcp")
        self.assertEqual(calls, [("life-advance", 12)])

    def test_development_report_driver_reads_without_starting_ck3(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state = Path(temporary)
            run = state / "runs" / "20260823T000000Z-dev-session-fixture"
            run.mkdir(parents=True)
            (run / "report.json").write_text(
                json.dumps(
                    {
                        "run_id": run.name,
                        "process": {"pid": 123},
                        "finalized": False,
                        "commands": [
                            {
                                "command": "life-advance",
                                "ok": True,
                                "result": {"final_screen": "map_hud"},
                            },
                            {
                                "command": "auto-run 2",
                                "ok": True,
                                "result": {
                                    "final_screen": "unchanged",
                                    "turns": [
                                        {
                                            "command": "auto-turn",
                                            "ok": True,
                                            "result": {"final_screen": "map_running"},
                                        },
                                        {
                                            "command": "auto-turn",
                                            "ok": False,
                                            "error": "fixture stop",
                                        },
                                    ],
                                },
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )
            driver = DevelopmentReportDriver(state)

            snapshot = driver.take_snapshot()
            self.assertEqual(snapshot["revision"], 2)
            self.assertEqual(snapshot["phase"], "map_running")
            self.assertEqual(snapshot["backend_id"], "vision-report")
            with self.assertRaises(UnsupportedStepError):
                driver.execute_step("life-advance")

    def test_native_mcp_driver_receives_isolated_profile_save_dir(self) -> None:
        from xar_autoplayer.bridge.mcp_server import load_driver

        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary)
            with mock.patch(
                "xar_autoplayer.bridge.mcp_server.NativeHeadlessGameplayDriver"
            ) as factory:
                driver = load_driver(
                    "native-headless",
                    state_dir=state_dir,
                    pipe_name=r"\\.\pipe\xar_save_fixture",
                )

        self.assertIs(driver, factory.return_value)
        factory.assert_called_once_with(
            r"\\.\pipe\xar_save_fixture",
            state_dir=state_dir,
            save_dir=state_dir / "profile" / "save games",
        )

@unittest.skipIf(importlib.util.find_spec("mcp") is None, "optional MCP SDK not installed")
class GameplayMcpServerTests(unittest.IsolatedAsyncioTestCase):
    async def test_mcp_terms_query_preserves_session_binding_wrapper(
        self,
    ) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        wrapper = {
            "schema_version": 1,
            "backend_id": (
                "ck3-1.19.0.6-raiktor-six-domain-session-binding-v1"
            ),
            "status": "unavailable",
            "failure": {
                "code": "aggregate_frame_unavailable",
                "fields": ["aggregate.frame"],
            },
            "binding": None,
            "aggregate": None,
            "observed_binding": {},
            "readiness": {
                "snapshot_binding_ready": False,
                "query_receipt_binding_ready": False,
                "same_frame_revision_ready": False,
                "episode_owner_ready": False,
                "process_binding_ready": False,
                "aggregate_session_binding_ready": False,
            },
        }
        driver = CallbackGameplayDriver(
            backend_id="native-fixture",
            snapshot=lambda: _snapshot(4),
            execute=lambda step, revision: {
                "step": step,
                "expected_revision": revision,
                "query_sequence": 10,
                "war_termination_terms": _termination_terms(),
                "raiktor_surrender_aggregate_session": wrapper,
            },
            action_steps=("query-war-termination-terms-v1-88",),
        )
        server = create_server(driver)

        async with Client(server) as client:
            terms = await client.call_tool(
                "ck3_query_war_termination_terms",
                {"war_id": 88, "expected_revision": 4},
            )

        self.assertFalse(terms.is_error)
        self.assertEqual(
            terms.structured_content[
                "raiktor_surrender_aggregate_session"
            ],
            wrapper,
        )

    async def test_mcp_settle_one_life_returns_final_score(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        driver = CallbackGameplayDriver(
            backend_id="terminal-fixture",
            snapshot=lambda: {
                **_snapshot(14),
                "played_character": {"character_id": 707, "alive": False},
                "one_life_terminal": True,
                "one_life_terminal_reason": "played_character_dead",
            },
            execute=lambda step, revision: {
                "step": step,
                "terminal": True,
                "settlement_status": "complete",
                "continue_as_heir_after_death": False,
                "heir_gameplay_actions": 0,
                "score": 405.25,
                "expected_revision": revision,
            },
            action_steps=("death-terminal",),
        )
        server = create_server(driver)

        async with Client(server) as client:
            settled = await client.call_tool(
                "ck3_settle_one_life", {"expected_revision": 14}
            )

        self.assertFalse(settled.is_error)
        self.assertEqual(settled.structured_content["score"], 405.25)
        self.assertFalse(
            settled.structured_content["continue_as_heir_after_death"]
        )
        self.assertEqual(settled.structured_content["heir_gameplay_actions"], 0)

    async def test_official_mcp_client_lists_and_calls_ck3_tools(self) -> None:
        from mcp import Client
        from xar_autoplayer.bridge.mcp_server import create_server

        def execute_fixture(step: str, revision: int) -> dict[str, object]:
            result: dict[str, object] = {
                "step": step,
                "expected_revision": revision,
            }
            if step == "query-war-termination-options-88":
                result.update(
                    {
                        "war_termination_options": _termination_options(),
                        "query_sequence": 8,
                    }
                )
            elif step == "query-war-termination-terms-v1-88":
                result.update(
                    {
                        "war_termination_terms": _termination_terms(),
                        "query_sequence": 10,
                    }
                )
            elif step == (
                "query-war-termination-exit-terms-v2-16777300"
            ):
                result.update(
                    {
                        "war_termination_exit_terms": (
                            _termination_exit_terms_v2()
                        ),
                        "query_sequence": 11,
                    }
                )
            elif step == "query-army-strengths-v1":
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 9,
                        "army_strengths": [
                            _army_strength(81, "player", [88]),
                            _army_strength(82, "active_war_ally", [88]),
                            _army_strength(91, "active_war_enemy", [88]),
                        ],
                    }
                )
            elif step == "query-actual-contact-scope-v1-81-at-50":
                result.update(
                    {
                        "status": "available",
                        "query_sequence": 12,
                        "snapshot_revision": 4,
                        "actual_contact_scope": {
                            "schema_version": 1,
                            "contract_stage": (
                                "production_exact_current_province"
                            ),
                            "status": "available",
                            "scope_kind": "post_contact_observation",
                            "snapshot_revision": 4,
                            "date_raw": 53_171_424,
                            "subject_army_id": 81,
                            "subject_native_carmy_id": 181,
                            "subject_owner_character_id": 707,
                            "target_province_id": 50,
                            "province_unit_army_ids": [81, 82, 91],
                            "province_combat_ids": [700],
                            "stored_order_policy": "numeric_full_id",
                            "transition_kind": "in_combat",
                            "selected_combat_id": 700,
                            "selected_combat_array_index": 0,
                            "join_side": None,
                            "defender_seed_character_id": None,
                            "initiator_is_defender": False,
                            "adjacency_kind_raw": 0,
                            "loser_excluded_native_carmy_ids": [],
                            "opponent_army_ids": [],
                            "attacker_army_ids": [81, 82],
                            "defender_army_ids": [91],
                            "actual_contact_scope_ready": True,
                            "combat_v3_participant_scope_ready": True,
                        },
                    }
                )
            elif step == "query-arrange-marriage-choices":
                result.update(
                    {
                        "arrange_marriage_choices": [
                            {
                                "choice_id": "707-809",
                                "played_character_id": 707,
                                "candidate_character_id": 809,
                            }
                        ],
                        "query_sequence": 2,
                    }
                )
            elif step == "query-declarable-wars":
                result.update(
                    {
                        "declarable_wars": [
                            {
                                "declaration_id": "808-17-0",
                                "target_character_id": 808,
                                "casus_belli_index": 17,
                                "casus_belli_key": "county_conquest_cb",
                                "configuration_index": 0,
                                "claimant_character_id": -1,
                                "target_title_ids": [91],
                            }
                        ],
                        "query_sequence": 1,
                    }
                )
            elif step == "save-checkpoint":
                result["checkpoint"] = {
                    "status": "saved",
                    "name": "xar_checkpoint.ck3",
                    "path": "C:/fixture/xar_checkpoint.ck3",
                    "size": 123,
                    "sha256": "a" * 64,
                    "date_raw": 53_171_424,
                }
            elif step == "restore-checkpoint":
                result.update(
                    {
                        "checkpoint": {
                            "status": "restored",
                            "name": "xar_checkpoint.ck3",
                            "path": "C:/fixture/xar_checkpoint.ck3",
                            "size": 123,
                            "sha256": "a" * 64,
                            "date_raw": 53_171_424,
                        },
                        "restored_date": {"date_raw": 53_171_424},
                    }
                )
            return result

        driver = CallbackGameplayDriver(
            backend_id="native-fixture",
            snapshot=lambda: {
                **_snapshot(4),
                "paused": True,
                "active_event": {"instance_id": 44, "option_count": 2},
                "pending_character_interaction": {
                    "instance_id": 52,
                    "sender_character_id": 901,
                    "auto_accept_notification": False,
                },
                "active_wars": [
                    _war(
                        allied_armies=[
                            _army(
                                81,
                                soldiers=1_300,
                                province_id=50,
                                controllable=True,
                            ),
                            _army(
                                82,
                                soldiers=700,
                                province_id=51,
                                controllable=False,
                            ),
                        ],
                        enemy_armies=[
                            _army(
                                91,
                                soldiers=1_900,
                                province_id=60,
                                controllable=False,
                            )
                        ],
                    )
                ],
                "player_armies": [
                    _army(
                        81,
                        soldiers=1_300,
                        province_id=50,
                        controllable=True,
                    )
                ],
                "declarable_wars": [
                    {
                        "declaration_id": "808-17-0",
                        "target_character_id": 808,
                        "casus_belli_index": 17,
                        "casus_belli_key": "county_conquest_cb",
                        "configuration_index": 0,
                        "claimant_character_id": -1,
                        "target_title_ids": [91],
                    }
                ],
                "arrange_marriage_choices": [
                    {
                        "choice_id": "707-809",
                        "played_character_id": 707,
                        "candidate_character_id": 809,
                    }
                ],
            },
            execute=execute_fixture,
            action_steps=(
                "life-advance",
                "save-checkpoint",
                "restore-checkpoint",
                "accept-pending-character-interaction",
                "reject-pending-character-interaction",
                "raise-troops-default",
                "move-army-81-to-60",
                "merge-armies-81-with-82",
                "start-assault-901",
                "stop-assault-901",
                "disband-army-81",
                "enforce-demands-88",
                "query-army-strengths-v1",
                "query-actual-contact-scope-v1-81-at-50",
                "query-war-termination-options-88",
                "query-war-termination-terms-v1-88",
                "query-war-termination-exit-terms-v2-16777300",
                "query-declarable-wars",
                "declare-war-808-17-0",
                "query-arrange-marriage-choices",
                "arrange-marriage-707-809",
                "select-event-option-1",
                "select-event-option-2",
            ),
            source="named-pipe",
            latency="realtime",
        )
        server = create_server(driver)
        async with Client(server) as client:
            listed = await client.list_tools()
            self.assertEqual(
                {tool.name for tool in listed.tools},
                {
                    "ck3_get_capabilities",
                    "ck3_get_bridge_diagnostics",
                    "ck3_take_snapshot",
                    "ck3_get_one_life_settlement",
                    "ck3_settle_one_life",
                    "ck3_plan_turn",
                    "ck3_auto_turn",
                    "ck3_execute_step",
                    "ck3_save_checkpoint",
                    "ck3_restore_checkpoint",
                    "ck3_start_next_episode",
                    "ck3_reply_pending_character_interaction",
                    "ck3_acknowledge_pending_character_interaction",
                    "ck3_get_war_state",
                    "ck3_query_arrange_marriage_choices",
                    "ck3_arrange_marriage",
                    "ck3_query_declarable_wars",
                    "ck3_declare_war",
                    "ck3_raise_troops_default",
                    "ck3_move_army",
                    "ck3_start_assault",
                    "ck3_stop_assault",
                    "ck3_disband_army",
                    "ck3_enforce_demands",
                    "ck3_query_army_strengths",
                    "ck3_query_actual_contact_scope",
                    "ck3_query_battle_control_snapshot_v1",
                    "ck3_query_battle_transition_v1",
                    "ck3_query_battle_terminal_transition_v1",
                    "ck3_query_battle_reinforcement_assignment_v1",
                    "ck3_query_campaign_root_context_v1",
                    "ck3_query_council_composition_candidates_v1",
                    "ck3_query_player_faction_alerts_v1",
                    "ck3_query_steward_develop_county_candidates_v1",
                    "ck3_change_steward_develop_county_task_v1",
                    "ck3_set_played_character_v1",
                    "ck3_query_vanilla_event_knowledge_v1",
                    "ck3_list_vanilla_event_knowledge_v1",
                    "ck3_list_vanilla_event_evidence_v1",
                    "ck3_read_vanilla_event_evidence_v1",
                    "ck3_query_vanilla_event_source_provenance_v1",
                    "ck3_query_zhongguo_case_snapshot_v1",
                    "ck3_query_zhongguo_b1_cycle_snapshot_v1",
                    "ck3_query_zhongguo_ai_owned_case_snapshot_v1",
                    "ck3_query_zhongguo_result_case_snapshot_v1",
                    "ck3_query_zhongguo_b2_pip_snapshot_v1",
                    "ck3_query_zhongguo_promotion_compensation_postcondition_v1",
                    "ck3_query_zhongguo_compensation_af5_snapshot_v1",
                    "ck3_query_zhongguo_workforce_owner_snapshot_v1",
                    "ck3_query_zhongguo_projects_metrics_postcondition_v1",
                    "ck3_query_zhongguo_career_hc_workforce_postcondition_v1",
                    "ck3_activate_zhongguo_scoreboard_v1",
                    "ck3_query_zhongguo_incident_snapshot_v1",
                    "ck3_query_zhongguo_manager_governance_snapshot_v1",
                    "ck3_query_zhongguo_manager_subordinate_selector_v1",
                    "ck3_query_zhongguo_scoreboard_state_v1",
                    "ck3_query_zhongguo_workforce_collective_snapshot_v1",
                    "ck3_query_zhongguo_workforce_normal_exit_snapshot_v1",
                    "ck3_center_map_on_landed_title_v1",
                    "ck3_set_played_character_v1",
                    "ck3_probe_coat_of_arms_source_v1",
                    "ck3_export_coat_of_arms_source_v1",
                    "ck3_query_coat_of_arms_load_configuration_v1",
                    "ck3_query_coat_of_arms_installed_dlc_sources_v1",
                    "ck3_query_coat_of_arms_resource_catalog_v1",
                    "ck3_read_coat_of_arms_resource_asset_v1",
                    "ck3_query_coat_of_arms_configured_resource_catalog_v1",
                    "ck3_read_coat_of_arms_configured_resource_asset_v1",
                    "ck3_project_coat_of_arms_vfs_asset_winner_v1",
                    "ck3_query_coat_of_arms_definition_catalog_v1",
                    "ck3_read_coat_of_arms_definition_v1",
                    "ck3_begin_coat_of_arms_source_upload_v2",
                    "ck3_append_coat_of_arms_source_chunk_v2",
                    "ck3_commit_coat_of_arms_source_upload_v2",
                    "ck3_abort_coat_of_arms_source_upload_v2",
                    "ck3_inspect_frontend_gui_tree_v1",
                    "ck3_activate_frontend_new_game_v1",
                    "ck3_activate_frontend_pick_any_character_v1",
                    "ck3_activate_frontend_ruler_designer_v1",
                    "ck3_activate_frontend_prepare_custom_ruler_v1",
                    "ck3_activate_frontend_coat_of_arms_designer_v1",
                    "ck3_inspect_frontend_coat_of_arms_tree_v1",
                    "ck3_activate_frontend_coat_of_arms_custom_mode_v1",
                    "ck3_inspect_frontend_coat_of_arms_pattern_grid_v1",
                    "ck3_commit_frontend_dynasty_coat_of_arms_v1",
                    "ck3_read_coat_of_arms_render_support_v1",
                    "ck3_prepare_frontend_coat_of_arms_framebuffer_v1",
                    "ck3_capture_frontend_coat_of_arms_framebuffer_v1",
                    "ck3_compare_frontend_coat_of_arms_framebuffer_v1",
                    "ck3_compare_frontend_coat_of_arms_framebuffer_v2",
                    "ck3_calibrate_frontend_coat_of_arms_framebuffer_v2",
                    "ck3_compare_frontend_coat_of_arms_framebuffer_v3",
                    "ck3_calibrate_frontend_coat_of_arms_framebuffer_v3",
                    "ck3_query_frontend_gui_route_v1",
                    "ck3_activate_frontend_start_1066_bookmark_character_v1",
                    "ck3_query_loaded_feature_manifest_v1",
                    "ck3_query_pending_character_interaction_context_v1",
                    "ck3_query_current_event_window_context_v1",
                    "ck3_preview_active_combat_retreat_v1",
                    "ck3_order_active_combat_retreat_v1",
                    "ck3_query_combat_simulation_inputs",
                    "ck3_query_combat_simulation_inputs_v3",
                    "ck3_query_war_entry_assessments",
                    "ck3_query_war_termination_options",
                    "ck3_query_outbound_war_white_peace_status",
                    "ck3_query_war_termination_terms",
                    "ck3_surrender_war",
                    "ck3_offer_white_peace",
                    "ck3_select_event_option",
                    "ck3_resolve_active_event",
                    "ck3_query_turn_bundle_v1",
                    "ck3_search_entities_v1",
                    "ck3_wait_for_change",
                },
            )
            snapshot = await client.call_tool("ck3_take_snapshot", {})
            self.assertFalse(snapshot.is_error)
            self.assertEqual(snapshot.structured_content["revision"], 4)
            settlement = await client.call_tool(
                "ck3_get_one_life_settlement", {}
            )
            self.assertFalse(settlement.is_error)
            self.assertEqual(
                settlement.structured_content["status"], "not_terminal"
            )
            action = await client.call_tool(
                "ck3_execute_step",
                {"step": "life-advance", "expected_revision": 4},
            )
            self.assertFalse(action.is_error)
            self.assertEqual(action.structured_content["backend_id"], "native-fixture")
            self.assertEqual(action.structured_content["expected_revision"], 4)
            merged = await client.call_tool(
                "ck3_execute_step",
                {
                    "step": "merge-armies-81-with-82",
                    "expected_revision": 4,
                },
            )
            self.assertFalse(merged.is_error)
            self.assertEqual(
                merged.structured_content["step"],
                "merge-armies-81-with-82",
            )
            automatic = await client.call_tool("ck3_auto_turn", {})
            self.assertFalse(automatic.is_error)
            self.assertEqual(
                automatic.structured_content["selected_step"],
                "select-event-option-1",
            )
            checkpoint = await client.call_tool(
                "ck3_save_checkpoint",
                {"expected_revision": 4},
            )
            self.assertFalse(checkpoint.is_error)
            self.assertEqual(
                checkpoint.structured_content["checkpoint"]["name"],
                "xar_checkpoint.ck3",
            )
            self.assertEqual(
                checkpoint.structured_content["checkpoint"]["date_raw"],
                53_171_424,
            )
            restored = await client.call_tool(
                "ck3_restore_checkpoint",
                {"expected_revision": 4},
            )
            self.assertFalse(restored.is_error)
            self.assertEqual(
                restored.structured_content["checkpoint"]["status"],
                "restored",
            )
            self.assertEqual(
                restored.structured_content["restored_date"]["date_raw"],
                53_171_424,
            )
            interaction = await client.call_tool(
                "ck3_reply_pending_character_interaction",
                {
                    "accept": True,
                    "interaction_instance_id": 52,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(interaction.is_error)
            self.assertTrue(interaction.structured_content["accepted"])
            self.assertEqual(
                interaction.structured_content["sender_character_id"], 901
            )
            war_state = await client.call_tool("ck3_get_war_state", {})
            self.assertFalse(war_state.is_error)
            self.assertEqual(war_state.structured_content["status"], "active")
            marriage_choices = await client.call_tool(
                "ck3_query_arrange_marriage_choices",
                {"expected_revision": 4},
            )
            self.assertFalse(marriage_choices.is_error)
            self.assertEqual(
                marriage_choices.structured_content[
                    "arrange_marriage_choices"
                ][0]["candidate_character_id"],
                809,
            )
            marriage = await client.call_tool(
                "ck3_arrange_marriage",
                {"choice_id": "707-809", "expected_revision": 4},
            )
            self.assertFalse(marriage.is_error)
            declarations = await client.call_tool(
                "ck3_query_declarable_wars", {"expected_revision": 4}
            )
            self.assertFalse(declarations.is_error)
            self.assertEqual(
                declarations.structured_content["declarable_wars"][0][
                    "casus_belli_key"
                ],
                "county_conquest_cb",
            )
            declared = await client.call_tool(
                "ck3_declare_war",
                {"declaration_id": "808-17-0", "expected_revision": 4},
            )
            self.assertFalse(declared.is_error)
            raised = await client.call_tool(
                "ck3_raise_troops_default", {"expected_revision": 4}
            )
            self.assertFalse(raised.is_error)
            moved = await client.call_tool(
                "ck3_move_army",
                {
                    "army_id": 81,
                    "target_province_id": 60,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(moved.is_error)
            self.assertEqual(moved.structured_content["army_id"], 81)
            started_assault = await client.call_tool(
                "ck3_start_assault",
                {"siege_id": 901, "expected_revision": 4},
            )
            self.assertFalse(started_assault.is_error)
            self.assertEqual(started_assault.structured_content["siege_id"], 901)
            stopped_assault = await client.call_tool(
                "ck3_stop_assault",
                {"siege_id": 901, "expected_revision": 4},
            )
            self.assertFalse(stopped_assault.is_error)
            self.assertEqual(stopped_assault.structured_content["siege_id"], 901)
            disbanded = await client.call_tool(
                "ck3_disband_army",
                {"army_id": 81, "expected_revision": 4},
            )
            self.assertFalse(disbanded.is_error)
            enforced = await client.call_tool(
                "ck3_enforce_demands",
                {"war_id": 88, "expected_revision": 4},
            )
            self.assertFalse(enforced.is_error)
            self.assertEqual(enforced.structured_content["war_id"], 88)
            strengths = await client.call_tool(
                "ck3_query_army_strengths",
                {"army_ids": [91, 81], "expected_revision": 4},
            )
            self.assertFalse(strengths.is_error)
            self.assertEqual(strengths.structured_content["status"], "available")
            self.assertEqual(
                [
                    row["army_id"]
                    for row in strengths.structured_content["army_strengths"]
                ],
                [91, 81],
            )
            self.assertNotIn(
                "win_probability", strengths.structured_content
            )
            actual_contact = await client.call_tool(
                "ck3_query_actual_contact_scope",
                {
                    "subject_army_id": 81,
                    "target_province_id": 50,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(actual_contact.is_error)
            actual_scope = actual_contact.structured_content[
                "actual_contact_scope"
            ]
            self.assertEqual(
                actual_scope["scope_kind"], "post_contact_observation"
            )
            self.assertEqual(actual_scope["selected_combat_id"], 700)
            self.assertEqual(actual_scope["attacker_army_ids"], [81, 82])
            self.assertEqual(actual_scope["defender_army_ids"], [91])
            termination = await client.call_tool(
                "ck3_query_war_termination_options",
                {"war_id": 88, "expected_revision": 4},
            )
            self.assertFalse(termination.is_error)
            self.assertEqual(
                termination.structured_content["war_termination_options"][
                    "war_id"
                ],
                88,
            )
            self.assertEqual(
                termination.structured_content["query_sequence"], 8
            )
            terms = await client.call_tool(
                "ck3_query_war_termination_terms",
                {"war_id": 88, "expected_revision": 4},
            )
            self.assertFalse(terms.is_error)
            self.assertEqual(
                terms.structured_content["war_termination_terms"]["claims"]
                [0]["state"],
                "strong_explicit",
            )
            self.assertEqual(terms.structured_content["query_sequence"], 10)
            event_action = await client.call_tool(
                "ck3_select_event_option",
                {
                    "option_number": 2,
                    "event_instance_id": 44,
                    "expected_revision": 4,
                },
            )
            self.assertFalse(event_action.is_error)
            self.assertEqual(event_action.structured_content["option_number"], 2)
            self.assertEqual(event_action.structured_content["option_index"], 1)


class SiegeForecastIngressTests(unittest.TestCase):
    def test_any_strength_reads_exact_route_contact_and_v3_once(self) -> None:
        date_raw = 53_215_920
        player = _army(
            11, soldiers=2_327, province_id=30, controllable=True,
            army_state="regular", army_state_code=1,
            route_province_ids=[], in_combat=False, retreating=False,
        )
        enemy = _army(
            21, soldiers=1_488, province_id=32, controllable=False,
            army_state="sieging", army_state_code=3,
            route_province_ids=[], in_combat=False, retreating=False,
        )
        war = _war(
            war_id=95, allied_armies=[player], enemy_armies=[enemy],
            score=-12, player_side="defender",
            player_is_primary_war_leader=True,
            war_objective_province_ids=[30],
        )
        snapshot = {
            **_snapshot(90), "paused": True, "map_ready": True,
            "active_event": None, "pending_character_interaction": None,
            "native_revision": 90, "date_raw": date_raw,
            "diagnostics": {"connection_generation": 1},
            "episode_run_id": None, "active_wars": [war],
            "player_armies": [player], "army_strengths_status": "available",
            "army_strengths": [
                _army_strength(11, "player", [95], current=2_327,
                               base_power_raw=2_327_000_000),
                _army_strength(21, "active_war_enemy", [95], current=1_488,
                               base_power_raw=1_488_000_000),
            ],
        }
        candidate = _primary_defender_siege_relief_assessment(
            snapshot, commands=[], active_wars=[war],
            controlled_armies=[player], pursuit_army=player,
        )
        self.assertEqual(candidate["status"], "forecast_required")
        baseline = {
            "phase": "native_war_no_safe_exact_route", "selected_step": None
        }
        preview_step = "preview-move-army-11-to-32"
        contact_step = query_route_contact_horizon_step(11, 32, (21,))
        query_step = query_combat_simulation_inputs_v3_step(32, 31, [11], [21])
        steps = {preview_step, contact_step, "life-advance", "move-army-11-to-32"}
        capabilities = {QUERY_COMBAT_SIMULATION_INPUTS_V3_CAPABILITY}

        def ingest(
            history: list[dict[str, object]],
            *, frame: dict[str, object] | None = None,
            plan: dict[str, object] | None = None,
        ) -> dict[str, object]:
            return _primary_defender_siege_forecast_ingress(
                plan or baseline, commands=history,
                snapshot=frame or snapshot, action_steps=steps,
                bridge_capabilities=capabilities,
            )

        preview = ingest([])
        self.assertEqual(preview["selected_step"], preview_step)
        self.assertFalse(preview["active_attack_allowed"])
        holding_another_objective = {
            "phase": "native_war_pursuit_progress",
            "selected_step": "life-advance",
            "pursuit": {"war_id": 95, "target_province_id": 30},
        }
        self.assertEqual(
            ingest([], plan=holding_another_objective)["selected_step"],
            preview_step,
        )
        preview_row = _preview_row(
            1, army_id=11, origin=30, target=32,
            date_raw=date_raw, route=[31, 32],
        )
        contact = ingest([preview_row])
        self.assertEqual(contact["selected_step"], contact_step)
        contact_row = _route_contact_row(
            2, army_id=11, origin=30, target=32,
            date_raw=date_raw, route=[31, 32],
            hostile_ids=(21,), contact_free=True,
        )
        inputs = ingest([preview_row, contact_row])
        self.assertEqual(inputs["selected_step"], query_step)
        self.assertEqual(inputs["phase"], "native_war_siege_forecast_inputs_query")
        adjacent_preview = _preview_row(
            1, army_id=11, origin=30, target=32,
            date_raw=date_raw, route=[32],
        )
        adjacent_contact = _route_contact_row(
            2, army_id=11, origin=30, target=32,
            date_raw=date_raw, route=[32],
            hostile_ids=(21,), contact_free=False,
        )
        self.assertEqual(
            ingest([adjacent_preview, adjacent_contact])["selected_step"],
            query_combat_simulation_inputs_v3_step(32, 30, [11], [21]),
        )
        intermediate_contact = copy.deepcopy(contact_row)
        intermediate_contact["result"]["route_contact_horizon"]["one_day_contact_free"] = False
        intermediate_contact["result"]["route_contact_horizon"]["conflicts"] = [
            {"kind": "same_province", "hostile_army_id": 21,
             "province_id": 31}
        ]
        self.assertIsNone(
            ingest([preview_row, intermediate_contact])["selected_step"]
        )
        queried_frame = {
            **snapshot,
            "combat_simulation_inputs_v3": {
                "completeness": {
                    "phase_event_inputs_ready": True,
                    "monte_carlo_ready": False,
                    "planner_usable": False,
                    "active_attack_allowed": False,
                }
            },
            "combat_simulation_inputs_v3_status": "available",
            "combat_simulation_inputs_v3_target_province_id": 32,
            "combat_simulation_inputs_v3_attacker_entry_province_id": 31,
            "combat_simulation_inputs_v3_attacker_army_ids": [11],
            "combat_simulation_inputs_v3_defender_army_ids": [21],
            "combat_simulation_inputs_v3_queried_snapshot_id": "session:90",
            "combat_simulation_inputs_v3_queried_revision": 90,
        }
        query_row = {
            "index": 3, "command": query_step, "ok": True,
            "result": {
                "step": query_step, "accepted": True, "status": "available",
                "queried_snapshot_id": "session:90",
                "queried_revision": 90, "queried_native_revision": 90,
            },
        }
        observed = ingest(
            [preview_row, contact_row, query_row], frame=queried_frame
        )
        self.assertEqual(observed["phase"], "native_war_siege_forecast_inputs_observed")
        self.assertIsNone(observed["selected_step"])
        self.assertEqual(observed["qualified_forecast"]["status"], "producer_unavailable")
        self.assertFalse(observed["combat_inputs_v3_query"]["planner_usable"])
        self.assertNotEqual(observed["selected_step"], "life-advance")
        with mock.patch(
            "xar_autoplayer.strategy._qualified_siege_forecast_move",
            return_value={"status": "ready", "assessment_sha256": "E" * 64},
        ):
            qualified = ingest([preview_row, contact_row, query_row], frame=queried_frame)
        self.assertEqual(qualified["phase"], "native_war_siege_forecast_move")
        self.assertEqual(qualified["selected_step"], "move-army-11-to-32")
        self.assertTrue(qualified["active_attack_allowed"])
        stale = ingest([preview_row, contact_row, query_row])
        self.assertIsNone(stale["selected_step"])
        self.assertEqual(stale["required_observation"], "fresh-v3-cache-readback")
        self.assertEqual(
            ingest([], plan={"phase": "native_war_defender_capital_hold_progress",
                             "selected_step": "life-advance"})["selected_step"],
            "life-advance",
        )

        no_entry = _preview_row(
            1, army_id=11, origin=30, target=32,
            date_raw=date_raw, route=[],
        )
        blocked = ingest([no_entry])
        self.assertIsNone(blocked["selected_step"])
        self.assertEqual(
            blocked["required_observation"],
            "fresh-complete-siege-route-preview",
        )
        overmatch = {**snapshot, "army_strengths": [
            _army_strength(11, "player", [95], current=3_000,
                           base_power_raw=3_000_000_000),
            _army_strength(21, "active_war_enemy", [95], current=1_000,
                           base_power_raw=1_000_000_000),
        ]}
        self.assertEqual(
            _primary_defender_siege_relief_assessment(
                overmatch, commands=[], active_wars=[war],
                controlled_armies=[player], pursuit_army=player,
            )["status"], "forecast_required",
        )
        overmatch_preview = _primary_defender_siege_forecast_ingress(
            baseline, commands=[], snapshot=overmatch,
            action_steps=steps, bridge_capabilities=capabilities,
        )
        self.assertEqual(overmatch_preview["selected_step"], preview_step)
        self.assertFalse(overmatch_preview["active_attack_allowed"])
        self.assertEqual(
            _primary_defender_siege_forecast_ingress(
                holding_another_objective, commands=[], snapshot=overmatch,
                action_steps=steps, bridge_capabilities=capabilities,
            )["selected_step"],
            preview_step,
        )
        overmatch_readback = _primary_defender_siege_forecast_ingress(
            baseline, commands=[preview_row, contact_row, query_row],
            snapshot={**queried_frame, "army_strengths": overmatch["army_strengths"]},
            action_steps=steps, bridge_capabilities=capabilities,
        )
        self.assertEqual(overmatch_readback["phase"],
                         "native_war_siege_forecast_inputs_observed")
        self.assertIsNone(overmatch_readback["selected_step"])
        self.assertEqual(overmatch_readback["qualified_forecast"]["status"],
                         "producer_unavailable")
        with mock.patch(
            "xar_autoplayer.strategy._qualified_siege_forecast_move",
            return_value={"status": "ready", "assessment_sha256": "E" * 64},
        ):
            overmatch_qualified = _primary_defender_siege_forecast_ingress(
                baseline, commands=[preview_row, contact_row, query_row],
                snapshot={**queried_frame, "army_strengths": overmatch["army_strengths"]},
                action_steps=steps, bridge_capabilities=capabilities,
            )
        self.assertEqual(overmatch_qualified["selected_step"], "move-army-11-to-32")


if __name__ == "__main__":
    unittest.main()

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
from xar_autoplayer.bridge.settlement_contract import (
    ONE_LIFE_SETTLEMENT_CAPABILITY,
)
from xar_autoplayer.bridge.war_contract import (
    BATTLE_DECISION_EPOCH_ADVANCE_STEP,
    COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
    advance_route_contact_horizon_step,
    battle_decision_epoch_advance_step,
    committed_route_sentinel_advance_step,
    normalize_active_wars,
    query_route_contact_horizon_step,
    war_objective_province_ids,
)
from xar_autoplayer.strategy import (
    _audit_war_route,
    _enemy_endpoint_epochs,
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
        "age_days": 0,
        "expiration_days": 60,
        "remaining_days": 60,
        "expiry_boundary_status": "not_reached",
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


def _plan_for_pending_context(
    context_result: dict[str, object],
    *,
    action_steps: tuple[str, ...],
    active_wars: list[dict[str, object]] | None = None,
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
    driver = CallbackGameplayDriver(
        backend_id="native-headless",
        snapshot=lambda: {
            **_snapshot(int(revision), history),
            "paused": True,
            "native_revision": native_revision,
            "date_raw": date_raw,
            "pending_character_interaction": {
                "instance_id": pending_id,
                "sender_character_id": roles["actor_character_id"],
                "auto_accept_notification": False,
            },
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
    player_is_primary_war_leader: bool = True,
    enemy_primary_default_raise_province_id: int | None = None,
    war_objective_province_ids: list[int] | None = None,
    objective_province_states: list[dict[str, object]] | None = None,
    targeted_title_ids: list[int] | None = None,
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
        "war_duration_days": 203,
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
    enemies: list[dict[str, object]],
    score: int,
    date_raw: int,
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
                _war(
                    allied_armies=controlled,
                    enemy_armies=enemies,
                    score=score,
                    enemy_primary_default_raise_province_id=fallback,
                    war_objective_province_ids=(
                        list(objectives)
                        if objectives is not None
                        else [objective]
                        if objective is not None
                        else []
                    ),
                    objective_province_states=objective_states,
                )
            ],
            "player_armies": controlled,
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
        self.assertEqual(safe["phase"], "native_war_route_progress")
        self.assertEqual(safe["selected_step"], "life-advance")

        destination_blocked = _native_war_plan(
            player=player,
            enemies=[target_enemy],
            score=0,
            date_raw=24_000,
            steps=("life-advance",),
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
            steps=("life-advance",),
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

    def test_intersecting_committed_route_uses_speed_three_native_sentinel(
        self,
    ) -> None:
        date_raw = 53_256_000
        player = _army(
            201_326_874,
            soldiers=4_100,
            province_id=8753,
            controllable=True,
            move_target_province_id=2635,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[2626, 2627, 2633, 2634, 2635],
        )
        enemy = _army(
            167_772_577,
            soldiers=3_300,
            province_id=8648,
            controllable=False,
            move_target_province_id=2635,
            army_state="moving",
            army_state_code=7,
            route_province_ids=[1034, 2644, 2645, 2635],
        )
        query_step = query_route_contact_horizon_step(
            201_326_874, 2635, (167_772_577,)
        )
        target_date_raw = date_raw + 45 * 24
        plan = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            steps=(
                COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
                query_step,
                "life-advance",
            ),
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "decision_sentinel_live_ready": True,
                "committed_route_sentinel_live_ready": True,
                "terminal_sentinel_live_ready": False,
                "overwhelming_matrix_live_ready": False,
            },
        )

        self.assertEqual(
            plan["phase"],
            "native_war_committed_route_sentinel_progress",
        )
        self.assertEqual(
            plan["selected_step"],
            committed_route_sentinel_advance_step(
                201_326_874, 2635, target_date_raw
            ),
        )
        self.assertNotEqual(plan["selected_step"], query_step)
        self.assertEqual(plan["timeline_speed"], 3)
        self.assertEqual(plan["sentinel_scope"], "committed_route")
        self.assertEqual(plan["watch_army_ids"], [201_326_874])
        self.assertEqual(
            plan["hostile_route_change_detection"],
            "not_watched_until_combat_id_transition",
        )

        default_closed = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=0,
            date_raw=date_raw,
            steps=(
                COMMITTED_ROUTE_SENTINEL_ADVANCE_STEP,
                query_step,
                "life-advance",
            ),
            route_contact_horizon_supported=True,
            battle_speed_readiness={
                "decision_sentinel_live_ready": True,
                "committed_route_sentinel_live_ready": False,
                "terminal_sentinel_live_ready": True,
                "overwhelming_matrix_live_ready": False,
            },
        )
        self.assertEqual(
            default_closed["phase"], "native_war_route_contact_horizon"
        )
        self.assertEqual(default_closed["selected_step"], query_step)

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

    def test_unavoidable_current_province_contact_skips_candidate_sweep(
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

        self.assertEqual(
            plan["phase"], "native_war_unavoidable_contact_transition"
        )
        self.assertEqual(plan["selected_step"], advance_step)
        self.assertEqual(
            plan["route_audit"]["status"],
            "unavoidable_current_province_contact",
        )

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
            "native_war_unavoidable_contact_transition",
        )
        self.assertEqual(transition["selected_step"], sibling_advance)
        self.assertNotEqual(transition["selected_step"], advance_step)

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
        self.assertEqual(safe["phase"], "native_war_route_progress")
        self.assertEqual(safe["selected_step"], "life-advance")

        enemy = _army(21, soldiers=800, province_id=31, controllable=False)
        reroute = _native_war_plan(
            player=safe_player,
            enemies=[enemy],
            score=0,
            date_raw=24_000,
            objectives=[2585, 2510],
            steps=(
                "preview-move-army-11-to-2510",
                "move-army-11-to-2510",
                "life-advance",
            ),
        )
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
            objectives=[2585, 2510],
            steps=("preview-move-army-11-to-2510", "life-advance"),
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
            ],
            objectives=[2585, 2510],
            steps=("move-army-11-to-2510", "life-advance"),
        )
        self.assertEqual(blocked["phase"], "native_war_unsafe_route_blocked")
        self.assertIsNone(blocked["selected_step"])

        current_only = _native_war_plan(
            player=player,
            enemies=[enemy],
            score=24,
            date_raw=24_000,
            objectives=[2585, 20],
            steps=("move-army-11-to-20", "life-advance"),
        )
        self.assertEqual(current_only["phase"], "native_war_no_safe_exact_route")
        self.assertIsNone(current_only["selected_step"])

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

        self.assertEqual(plan["phase"], "native_war_route_preview")
        self.assertEqual(
            plan["selected_step"], "preview-move-army-12-to-2510"
        )
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
                    safe_plan["phase"], "native_war_route_progress"
                )
                self.assertEqual(safe_plan["selected_step"], "life-advance")
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
            {"native_war_route_preview", "native_war_no_safe_exact_route"},
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

        self.assertEqual(plan["phase"], "native_war_route_progress")
        self.assertEqual(plan["selected_step"], "life-advance")
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
                    "ck3_query_loaded_feature_manifest_v1",
                    "ck3_query_pending_character_interaction_context_v1",
                    "ck3_query_current_event_window_context_v1",
                    "ck3_preview_active_combat_retreat_v1",
                    "ck3_order_active_combat_retreat_v1",
                    "ck3_query_combat_simulation_inputs",
                    "ck3_query_combat_simulation_inputs_v3",
                    "ck3_query_war_entry_assessments",
                    "ck3_query_war_termination_options",
                    "ck3_query_war_termination_terms",
                    "ck3_surrender_war",
                    "ck3_offer_white_peace",
                    "ck3_select_event_option",
                    "ck3_resolve_active_event",
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


if __name__ == "__main__":
    unittest.main()

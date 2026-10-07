"""Decision-facing, explicitly approximate whole-battle forecast.

The research envelope is useful before exact native parity.  This adapter
keeps its provenance and missing domains visible while allowing a strategy to
make a bounded decision from the distribution it actually computed.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from hashlib import sha256
import json
from typing import Any, Mapping

from .battle_v2_constructor_advantage import (
    V2_CONSTRUCTOR_ADVANTAGE_SOURCE,
    read_v2_constructor_advantage,
)
from .combat_core import CombatExperiment
from .combat_input import CombatInputError, FrozenCombatSimulationInput, freeze_combat_simulation_input
from .research_envelope import ResearchEnvelopeAssumptions, run_research_envelope_experiment


def _native_precontact_advantage(
    payload: Mapping[str, Any], frozen: FrozenCombatSimulationInput,
) -> tuple[int, int, int, tuple[int | None, int | None], str] | None:
    """Bind the same v3 query's zero-roll helper and native-selected commanders.

    An unavailable optional phase slice permits the declared generic fallback.
    A malformed *available* slice is an identity error, never a silent fallback.
    """
    phase = payload.get("phase_event_inputs")
    if phase is None and payload.get("schema_version") != 3:
        return None
    if (isinstance(phase, dict) and phase.get("status") == "unavailable"
            and phase.get("advantage_model") is None):
        return None
    if (not isinstance(phase, dict) or payload.get("schema_version") != 3
            or payload.get("contract_stage") != "production_exact_132_refs"):
        raise CombatInputError("native phase slice has no v3 identity")
    model = phase.get("advantage_model")
    resolved = model.get("resolved_dynamic") if isinstance(model, dict) else None
    if not (
        isinstance(model, dict) and isinstance(resolved, dict)
        and model.get("status") == "available"
        and model.get("scale") == 100_000
        and model.get("scenario_policy") == frozen.encounter.participant_policy
        and model.get("observation_origin") == "native_exact_build_production"
        and resolved.get("status") == "available"
        and resolved.get("helper_status") == "original_helpers_matched"
        and resolved.get("roll_policy") == "zero_in_query_sampled_offline"
        and resolved.get("original_total_helper_match") is True
    ):
        raise CombatInputError("native phase advantage provenance is unavailable")
    base = model.get("base_static_accumulator_raw")
    total = resolved.get("resolved_advantage_at_zero_roll_raw")
    original = resolved.get("original_total_helper_raw")
    sides = resolved.get("sides")
    side_inputs = model.get("side_inputs")
    if (any(type(value) is not int or not -(2**63) <= value < 2**63
            for value in (base, total, original))
            or not isinstance(sides, list) or len(sides) != 2
            or not isinstance(side_inputs, list) or len(side_inputs) != 2):
        raise CombatInputError("native phase advantage numbers are malformed")
    leaders = []
    selected_ids = []
    side_totals = []
    for index, role in enumerate(("attacker", "defender")):
        side = sides[index]
        source = side_inputs[index]
        armies = tuple(army for army in frozen.armies if army.encounter_role == role)
        expected_ids = tuple(army.public_army_id for army in armies)
        if (not isinstance(side, dict) or not isinstance(source, dict)
                or side.get("side") != role or source.get("side") != role
                or not armies
                or source.get("ordered_army_ids") != list(expected_ids)
                or source.get("primary_army_id") != expected_ids[0]
                or side.get("battle_commander_selection") != "native_0x23C8A60"
                or type(side.get("battle_commander_selected")) is not bool):
            raise CombatInputError("native phase side identity differs")
        selected = side["battle_commander_selected"]
        character_id = side.get("battle_commander_character_id")
        if selected:
            if type(character_id) is not int or character_id <= 0:
                raise CombatInputError("native selected commander ID is malformed")
            candidates = tuple(
                army for army in armies
                if army.commander.character_id == character_id
            )
            if len(candidates) != 1:
                raise CombatInputError("native selected commander army is not unique in same-frame armies")
            leader = candidates[0]
        elif character_id is None:
            leader = armies[0]  # placeholder only; no commander roll is drawn
        else:
            raise CombatInputError("native absent commander has a character ID")
        operands = (
            side.get("roll_raw"), side.get("target_conditionals_residual_raw"),
            side.get("commander_dynamic_raw"), side.get("side_dynamic_raw"),
            side.get("side_total_raw"),
        )
        if (any(type(value) is not int or not -(2**63) <= value < 2**63
                for value in operands)
                or side.get("roll_points") != 0 or operands[0] != 0
                or sum(operands[:4]) != operands[4]):
            raise CombatInputError("native phase side helper arithmetic differs")
        leaders.append(leader.public_army_id)
        selected_ids.append(character_id)
        side_totals.append(operands[4])
    if (total != original or total != base + side_totals[0] - side_totals[1]
            or resolved.get("side_0_dynamic_raw") != side_totals[0]
            or resolved.get("side_1_dynamic_raw") != side_totals[1]):
        raise CombatInputError("native zero-roll advantage arithmetic differs")
    model_sha256 = sha256(json.dumps(
        model, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest().upper()
    return leaders[0], leaders[1], total, (selected_ids[0], selected_ids[1]), model_sha256


def _positive_ids(value: object) -> tuple[int, ...] | None:
    if not isinstance(value, list) or not value:
        return None
    if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in value):
        return None
    return tuple(value) if len(value) == len(set(value)) else None


@lru_cache(maxsize=24)
def _run_cached(
    frozen: FrozenCombatSimulationInput,
    attacker_commander_id: int,
    defender_commander_id: int,
    native_zero_roll_advantage_raw: int | None,
    native_selected_commander_ids: tuple[int | None, int | None] | None,
    sample_count: int,
    horizon_days: int,
):
    return run_research_envelope_experiment(
        frozen,
        CombatExperiment(
            input_sha256=frozen.input_sha256,
            seed_u64=int(frozen.input_sha256[:16], 16),
            sample_count=sample_count,
            horizon_days=horizon_days,
        ),
        ResearchEnvelopeAssumptions(
            attacker_commander_army_id=attacker_commander_id,
            defender_commander_army_id=defender_commander_id,
            precontact_zero_roll_advantage_raw=native_zero_roll_advantage_raw,
            precontact_selected_commander_character_ids=native_selected_commander_ids,
        ),
        max_workers=1,
    )


def forecast_fixed_contact(
    payload: Mapping[str, Any],
    *,
    target_province_id: int,
    attacker_entry_province_id: int,
    attacker_army_ids: tuple[int, ...],
    defender_army_ids: tuple[int, ...],
    capture: Mapping[str, Any],
    sample_count: int = 256,
    horizon_days: int = 120,
) -> dict[str, object]:
    """Simulate a same-frame explicit contact, including unresolved outcomes.

    This is a bounded model estimate, never a claim of calibrated native odds.
    Missing input or an identity mismatch is reported instead of replaced with
    an unrelated power ratio.
    """

    if not 1 <= sample_count <= 4096 or not 1 <= horizon_days <= 365:
        raise ValueError("forecast budget outside bounded strategy range")
    completeness = payload.get("completeness")
    base = payload.get("base_inputs")
    scenario = base.get("scenario") if isinstance(base, dict) else None
    base_completeness = base.get("completeness") if isinstance(base, dict) else None
    ready = bool(
        isinstance(completeness, dict)
        and completeness.get("input_observation_ready") is True
    )
    # Production v3 can preserve a complete v2 base while an optional phase
    # slice is unavailable. Keep the bounded generic forecast usable then.
    ready = ready or bool(
        payload.get("schema_version") == 3
        and payload.get("contract_stage") == "production_exact_132_refs"
        and isinstance(base_completeness, dict)
        and base_completeness.get("input_observation_ready") is True
    )
    if not (
        ready and isinstance(base, dict)
        and isinstance(scenario, dict)
        and base.get("target_province_id") == target_province_id
        and scenario.get("attacker_entry_province_id") == attacker_entry_province_id
        and _positive_ids(scenario.get("attacker_army_ids")) == attacker_army_ids
        and _positive_ids(scenario.get("defender_army_ids")) == defender_army_ids
        and scenario.get("actual_route_dependency") is False
    ):
        return {"status": "input_or_encounter_mismatch"}
    ongoing_combats = base.get("ongoing_combats")
    if not isinstance(ongoing_combats, list):
        return {"status": "input_or_encounter_mismatch"}
    if ongoing_combats:
        return {"status": "active_combat_requires_resume_input"}
    try:
        frozen = freeze_combat_simulation_input(base, capture=dict(capture))
        native_advantage = _native_precontact_advantage(payload, frozen)
        advantage_source = (
            "same_frame_v3_native_zero_roll_frozen_future"
            if native_advantage is not None else None
        )
        if native_advantage is None and payload.get("schema_version") == 2:
            constructor_advantage = read_v2_constructor_advantage(payload, frozen)
            if constructor_advantage is not None:
                native_advantage = constructor_advantage[:5]
                advantage_source = constructor_advantage[5]
        if native_advantage is not None:
            leader_ids = native_advantage[:2]
            native_raw, selected_ids, native_model_sha256 = native_advantage[2:]
        else:
            leaders = []
            for role in ("attacker", "defender"):
                armies = tuple(army for army in frozen.armies if army.encounter_role == role)
                if not armies:
                    return {"status": "participant_role_unavailable"}
                leaders.append(max(armies, key=lambda army: (army.current_soldiers, -army.public_army_id)))
            leader_ids = tuple(army.public_army_id for army in leaders)
            native_raw = None
            selected_ids = None
            native_model_sha256 = None
        summary = _run_cached(
            frozen, leader_ids[0], leader_ids[1], native_raw, selected_ids,
            sample_count, horizon_days,
        )
    except (CombatInputError, ValueError, RuntimeError, TypeError) as error:
        return {"status": "model_unavailable", "error_type": type(error).__name__}
    resolved = summary.player_wins + summary.player_losses
    wilson = summary.player_win_wilson95
    player_soldiers = sum(
        army.current_soldiers for army in frozen.armies
        if army.coalition_side == "player_or_allied"
    )
    p90_loss = summary.player_hard_losses_raw.p90
    return {
        "status": "estimated",
        "model_fidelity": summary.model_fidelity,
        "native_parity": summary.fidelity_gate,
        "input_sha256": frozen.input_sha256.upper(),
        "simulator_build": summary.simulator_build,
        "sample_count": summary.sample_count,
        "horizon_days": horizon_days,
        "advantage_input": {
            "source": (
                advantage_source if native_raw is not None
                else "generic_commander_and_stock_static_approximation"
            ),
            **({
                "scope": "hypothetical_constructor_context",
                "complete_encounter_advantage_ready": False,
            } if advantage_source == V2_CONSTRUCTOR_ADVANTAGE_SOURCE else {}),
            "zero_roll_raw": native_raw,
            "model_sha256": native_model_sha256,
            "fallback_reason": (
                None if native_raw is not None else
                "phase_event_inputs_unavailable"
                if isinstance(payload.get("phase_event_inputs"), dict) else
                "native_phase_not_in_payload"
            ),
            "selected_commander_character_ids": list(selected_ids) if selected_ids is not None else None,
            "selected_commander_army_ids": list(leader_ids),
            "future_daily_refresh_modeled": False,
        },
        "player_wins": summary.player_wins,
        "player_losses": summary.player_losses,
        "no_resolution": summary.no_resolution,
        "player_win_probability_resolved": (
            summary.player_wins / resolved if resolved else None
        ),
        "player_win_probability_unconditional_lower": summary.player_wins / sample_count,
        "player_win_probability_unconditional_upper": (
            summary.player_wins + summary.no_resolution
        ) / sample_count,
        "resolved_win_wilson95": asdict(wilson) if wilson else None,
        "player_p90_hard_loss_raw": p90_loss,
        "player_p90_hard_loss_fraction": (
            p90_loss / (player_soldiers * 100_000)
            if p90_loss is not None and player_soldiers > 0 else None
        ),
        "player_stack_wipe_probability": summary.player_stack_wipe_probability,
        # The active envelope disables loaded phase events, so its zero death
        # count is not evidence of zero character risk in the actual battle.
        "commander_or_knight_death_probability": None,
        "character_death_risk_status": "unmodeled_phase_events",
        "missing_required_domains": list(summary.missing_required_domains),
        "assumptions": [
            "phase_events_disabled", "no_voluntary_retreat",
            "fixed_participants", "unobserved_modifiers_omitted",
            "future_daily_effective_stat_refresh_unmodeled",
            "future_daily_combat_width_refresh_unmodeled",
            "future_daily_non_roll_advantage_refresh_unmodeled",
            *(["same_frame_native_advantage_frozen_for_future_days"] if native_raw is not None else []),
        ],
        "capture": dict(capture),
    }


def contact_admission(forecast: Mapping[str, Any], *, defensive_relief: bool = False) -> dict[str, object]:
    """Risk-budget rule; it accepts imperfect model evidence explicitly."""

    if forecast.get("status") != "estimated":
        return {"admitted": False, "reason": "no_contact_estimate"}
    interval = forecast.get("resolved_win_wilson95")
    lower = interval.get("lower") if isinstance(interval, dict) else None
    loss = forecast.get("player_p90_hard_loss_fraction")
    wipe = forecast.get("player_stack_wipe_probability")
    death = forecast.get("commander_or_knight_death_probability")
    unresolved = forecast.get("no_resolution")
    count = forecast.get("sample_count")
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (lower, loss, wipe, unresolved, count)):
        return {"admitted": False, "reason": "incomplete_distribution"}
    death_risk_modeled = isinstance(death, (int, float)) and not isinstance(death, bool)
    if death is not None and not death_risk_modeled:
        return {"admitted": False, "reason": "invalid_character_death_risk"}
    limits = (
        {"win_lower": 0.70, "hard_loss": 0.20, "wipe": 0.02, "death": 0.02}
        if defensive_relief else
        {"win_lower": 0.65, "hard_loss": 0.25, "wipe": 0.05, "death": 0.05}
    )
    admitted = bool(
        count > 0 and unresolved / count <= 0.10
        and lower >= limits["win_lower"]
        and loss <= limits["hard_loss"]
        and wipe <= limits["wipe"]
        and (death <= limits["death"] if death_risk_modeled else True)
    )
    return {
        "admitted": admitted,
        "reason": "within_bounded_model_risk_budget" if admitted else "bounded_model_risk_budget_exceeded",
        "risk_limits": {**limits, "death": limits["death"] if death_risk_modeled else None},
        "character_death_risk_modeled": death_risk_modeled,
        "unquantified_risks": [
            *([] if death_risk_modeled else ["commander_or_knight_death"]),
            "future_reinforcement_and_participant_exit",
            "voluntary_retreat",
            "future_daily_effective_stat_refresh",
            "future_daily_combat_width_refresh",
            "future_daily_non_roll_advantage_refresh",
        ],
        "native_parity_required": False,
    }

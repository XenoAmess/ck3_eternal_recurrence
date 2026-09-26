"""Decision-facing, explicitly approximate whole-battle forecast.

The research envelope is useful before exact native parity.  This adapter
keeps its provenance and missing domains visible while allowing a strategy to
make a bounded decision from the distribution it actually computed.
"""

from __future__ import annotations

from dataclasses import asdict
from functools import lru_cache
from typing import Any, Mapping

from .combat_core import CombatExperiment
from .combat_input import CombatInputError, FrozenCombatSimulationInput, freeze_combat_simulation_input
from .research_envelope import ResearchEnvelopeAssumptions, run_research_envelope_experiment


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
    if not (
        isinstance(completeness, dict)
        and completeness.get("input_observation_ready") is True
        and isinstance(base, dict)
        and isinstance(scenario, dict)
        and base.get("target_province_id") == target_province_id
        and scenario.get("attacker_entry_province_id") == attacker_entry_province_id
        and _positive_ids(scenario.get("attacker_army_ids")) == attacker_army_ids
        and _positive_ids(scenario.get("defender_army_ids")) == defender_army_ids
        and scenario.get("actual_route_dependency") is False
    ):
        return {"status": "input_or_encounter_mismatch"}
    try:
        frozen = freeze_combat_simulation_input(base, capture=dict(capture))
        leaders = []
        for role in ("attacker", "defender"):
            armies = tuple(army for army in frozen.armies if army.encounter_role == role)
            if not armies:
                return {"status": "participant_role_unavailable"}
            leaders.append(max(armies, key=lambda army: (army.current_soldiers, -army.public_army_id)))
        summary = _run_cached(
            frozen, leaders[0].public_army_id, leaders[1].public_army_id,
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
        "commander_or_knight_death_probability": summary.commander_or_knight_death_probability,
        "missing_required_domains": list(summary.missing_required_domains),
        "assumptions": [
            "phase_events_disabled", "no_voluntary_retreat",
            "fixed_participants", "unobserved_modifiers_omitted",
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
    if not all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (lower, loss, wipe, death, unresolved, count)):
        return {"admitted": False, "reason": "incomplete_distribution"}
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
        and death <= limits["death"]
    )
    return {
        "admitted": admitted,
        "reason": "within_bounded_model_risk_budget" if admitted else "bounded_model_risk_budget_exceeded",
        "risk_limits": limits,
        "native_parity_required": False,
    }

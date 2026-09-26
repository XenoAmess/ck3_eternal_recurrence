"""Low-fidelity battle trials from the native prewar power assessment.

Prewar CRegiment participants do not exist in the current query contract.  We
still run a reproducible aggregate attrition model instead of treating missing
per-regiment detail as a permanent veto.  Its result is a decision prior, not
the fixed-contact combat simulator or a calibrated CK3 probability.
"""

from __future__ import annotations

import hashlib
import json
from typing import Mapping

from .combat_core import (
    advantage_damage_multiplier_raw,
    derive_trial_random_streams,
    fixed_mul,
    wilson_interval_95,
)


SCALE = 100_000
SAMPLE_COUNT = 256
HORIZON_DAYS = 120


def _positive_raw(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def forecast_prewar_power_battle(
    assessment: Mapping[str, object], *, declaration_id: str,
) -> dict[str, object]:
    """Stress-test a legal candidate's own base power against all target power."""

    actor = _positive_raw(assessment.get("actor_power_base_raw"))
    target = _positive_raw(assessment.get("target_power_total_raw"))
    if actor is None or target is None or not declaration_id:
        return {"status": "native_power_input_unavailable"}
    source = {
        "declaration_id": declaration_id,
        "actor_power_base_raw": actor,
        "target_power_total_raw": target,
        "actor_network_contribution_raw": assessment.get("actor_network_contribution_raw"),
        "target_network_contribution_raw": assessment.get("target_network_contribution_raw"),
    }
    digest = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    seed = int(digest[:16], 16)
    wins = losses = unresolved = 0
    for trial in range(SAMPLE_COUNT):
        state = derive_trial_random_streams(seed, trial).global_state
        draws = []
        for _ in range(4):
            draw, state = state.draw31()
            draws.append(draw)
        # Mobilization/arrival and unknown composition vary by trial.  These
        # bounds are policy assumptions, not native defines or observed odds.
        actor_fraction_raw = 65_000 + draws[0] % 35_001
        enemy_fraction_raw = 110_000 + draws[1] % 35_001
        actor_roll = draws[2] % 21
        enemy_roll = draws[3] % 21
        attacker_start = fixed_mul(actor, actor_fraction_raw)
        defender_start = fixed_mul(target, enemy_fraction_raw)
        attacker_health = attacker_start
        defender_health = defender_start
        advantage = actor_roll - enemy_roll
        attacker_advantage = advantage_damage_multiplier_raw(advantage) if advantage > 0 else SCALE
        defender_advantage = advantage_damage_multiplier_raw(-advantage) if advantage < 0 else SCALE
        result = "unresolved"
        for _ in range(HORIZON_DAYS):
            # Aggregate power stands in for both remaining force and output.
            # Keep both sides' outgoing damage frozen before applying either.
            attacker_damage = fixed_mul(attacker_health, attacker_advantage) * 3 // 100
            defender_damage = fixed_mul(defender_health, defender_advantage) * 3 // 100
            next_attacker = attacker_health - defender_damage
            next_defender = defender_health - attacker_damage
            if next_attacker <= 0 or next_defender <= 0:
                if next_attacker <= 0 and next_defender <= 0:
                    result = "unresolved"
                elif next_defender <= 0:
                    result = "win"
                else:
                    result = "loss"
                break
            attacker_health, defender_health = next_attacker, next_defender
        if result == "win":
            wins += 1
        elif result == "loss":
            losses += 1
        else:
            unresolved += 1
    resolved = wins + losses
    interval = wilson_interval_95(wins, resolved)
    return {
        "status": "estimated",
        "model_fidelity": "aggregate-prewar-surrogate-not-native-parity",
        "calibrated_probability": False,
        "source_sha256": digest.upper(),
        "sample_count": SAMPLE_COUNT,
        "horizon_days": HORIZON_DAYS,
        "wins": wins,
        "losses": losses,
        "no_resolution": unresolved,
        "resolved_win_fraction": wins / resolved if resolved else None,
        "resolved_win_wilson95_lower": interval.lower if interval else None,
        "assumptions": {
            "actor_mobilized_power_fraction_raw": [65_000, 100_000],
            "enemy_power_fraction_raw": [110_000, 145_000],
            "roll_range_each": [0, 20],
            "daily_damage_fraction_raw": 3_000,
            "missing": ["prewar_regiment_roster", "terrain", "reinforcement_timing", "phase_events", "casualty_types"],
        },
    }


def prewar_declaration_admission(forecast: Mapping[str, object]) -> dict[str, object]:
    """Permit decisive candidate battles without pretending the prior is exact."""

    lower = forecast.get("resolved_win_wilson95_lower")
    count = forecast.get("sample_count")
    unresolved = forecast.get("no_resolution")
    admitted = bool(
        forecast.get("status") == "estimated"
        and isinstance(lower, (int, float)) and lower >= 0.95
        and isinstance(count, int) and count > 0
        and isinstance(unresolved, int) and unresolved <= count // 20
    )
    return {
        "admitted": admitted,
        "reason": "decisive_aggregate_battle_prior" if admitted else "aggregate_battle_prior_risk_too_high",
        "minimum_wilson_lower": 0.95,
        "maximum_unresolved_fraction": 0.05,
        "native_parity_required": False,
    }

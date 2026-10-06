"""Strict current loaded warscore caps and explicit current winner membership.

The loaded pair is observed independently. Selection uses the frame's actual
native winner and an explicit same-invocation War-attacker membership condition.
Combat-side index, player identity and subject side do not determine membership.
"""

from __future__ import annotations

from collections.abc import Mapping


CURRENT_WARSCORE_CAPS_V1_KEY = "current_warscore_caps_v1"
_KEYS = {
    "source_combat_id",
    "war_attacker_winner_cap_raw_q100000",
    "war_defender_winner_cap_raw_q100000",
}


def _signed(value: object, bits: int, field: str) -> int:
    if type(value) is not int or not -(2 ** (bits - 1)) <= value < 2 ** (bits - 1):
        raise ValueError(f"{field} must be a signed int{bits}")
    return value


def normalize_current_warscore_caps_v1(
    value: object,
    *,
    expected_combat_id: int,
    field: str = "battle_control_snapshot.current_warscore_caps_v1",
) -> dict[str, int] | None:
    """Retain both observed signed64 operands, including zero, without rounding."""
    expected = _signed(expected_combat_id, 32, "expected_combat_id")
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != _KEYS:
        raise ValueError(f"{field} has a malformed schema")
    combat_id = _signed(value["source_combat_id"], 32, f"{field}.source_combat_id")
    if combat_id != expected:
        raise ValueError(f"{field}.source_combat_id disagrees with battle frame")
    return {
        "source_combat_id": combat_id,
        "war_attacker_winner_cap_raw_q100000": _signed(
            value["war_attacker_winner_cap_raw_q100000"],
            64,
            f"{field}.war_attacker_winner_cap_raw_q100000",
        ),
        "war_defender_winner_cap_raw_q100000": _signed(
            value["war_defender_winner_cap_raw_q100000"],
            64,
            f"{field}.war_defender_winner_cap_raw_q100000",
        ),
    }


def select_current_warscore_cap_v1(
    frame: Mapping[str, object], *, winner_is_war_attacker: bool | None
) -> dict[str, object]:
    """Select the current observed winner's cap under explicit War membership.

    The current battle-control frame does not observe winner War membership.
    This argument is a same-invocation caller condition. A native unknown winner
    (-1), missing membership or absent/null caps leaves selection partial while
    retaining independently observed caps. No future winner or row is predicted.
    """
    if winner_is_war_attacker is not None and type(winner_is_war_attacker) is not bool:
        raise ValueError("winner_is_war_attacker must be a boolean or null")
    combat_id = _signed(frame.get("combat_id"), 32, "battle_control_snapshot.combat_id")
    winner_raw = _signed(frame.get("winner_raw"), 32, "battle_control_snapshot.winner_raw")
    if winner_raw not in (-1, 0, 1):
        raise ValueError("battle_control_snapshot.winner_raw must be -1, 0 or 1")
    caps = normalize_current_warscore_caps_v1(
        frame.get(CURRENT_WARSCORE_CAPS_V1_KEY), expected_combat_id=combat_id
    )
    missing = []
    if caps is None:
        missing.append(CURRENT_WARSCORE_CAPS_V1_KEY)
    if winner_raw == -1:
        missing.append("current_native_winner")
    if winner_is_war_attacker is None:
        missing.append("current_invocation_winner_is_war_attacker")
    selected_key = None
    if not missing:
        selected_key = (
            "war_attacker_winner_cap_raw_q100000" if winner_is_war_attacker
            else "war_defender_winner_cap_raw_q100000"
        )
    selected = None if selected_key is None else caps[selected_key]
    return {
        "scope_kind": "conditional_current_observed_winner_loaded_battle_warscore_cap",
        "status": "partial" if missing else "ready",
        "observed_frame": {
            "combat_id": combat_id,
            "snapshot_revision": frame.get("snapshot_revision"),
            "observed_date_raw": frame.get("observed_date_raw"),
            "winner_raw": winner_raw,
            "winner_side": frame.get("winner_side"),
        },
        "observed_caps": caps,
        "winner_is_war_attacker": winner_is_war_attacker,
        "winner_membership_context": "explicit_same_invocation_condition",
        "native_winner_war_membership_observed": False,
        "selected_cap_raw_q100000": selected,
        "selected_source_field": selected_key,
        "scale": 100000,
        "unavailable_inputs": missing,
        "row_admission_predicted": False,
        "future_battle_score_predicted": False,
        "whole_war_outcome_predicted": False,
    }

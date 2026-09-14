"""Same-frame player-vitals projection for the realm-survival planner."""

from __future__ import annotations

import copy
from typing import Final


PLAYER_VITALS_V1_SCHEMA: Final = "xar.ck3.player-vitals/v1"


def _component(
    status: str,
    value: object = None,
    *,
    reason: str | None = None,
) -> dict[str, object]:
    if status not in {"available", "unavailable", "not_applicable"}:
        raise ValueError("player-vitals component status is invalid")
    if status == "available":
        if value is None or reason is not None:
            raise ValueError("available player-vitals component is malformed")
    elif value is not None or not isinstance(reason, str) or not reason:
        raise ValueError("non-available player-vitals component is malformed")
    return {
        "status": status,
        "value": copy.deepcopy(value),
        "unavailable_reason": reason,
    }


def _positive_int(value: object, field: str, *, maximum: int) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= maximum
    ):
        raise ValueError(f"{field} must be a positive integer")
    return value


def _date_raw(value: object) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not -(2**31) <= value <= 2**31 - 1
    ):
        raise ValueError("date_raw must be a signed int32")
    return value


def _binding(value: object, character_id: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("player-vitals binding must be an object")
    snapshot_id = value.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise ValueError("player-vitals snapshot_id is invalid")
    return {
        "character_id": _positive_int(
            character_id, "character_id", maximum=2**31 - 1
        ),
        "snapshot_id": snapshot_id,
        "snapshot_revision": _positive_int(
            value.get("native_revision"),
            "snapshot_revision",
            maximum=2**64 - 1,
        ),
        "date_raw": _date_raw(value.get("date_raw")),
    }


def _health(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("health-band component must be an object")
    status = value.get("status")
    if status == "unavailable":
        return _component(
            "unavailable", reason=_reason(value, "health-band component")
        )
    if status != "available" or value.get("unavailable_reason") is not None:
        raise ValueError("health-band component status is invalid")
    payload = value.get("value")
    if not isinstance(payload, dict):
        raise ValueError("health-band value is malformed")
    health = payload.get("health")
    if not isinstance(health, dict) or set(health) != {"raw", "scale"}:
        raise ValueError("health fixed-point value is malformed")
    raw = health.get("raw")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or not -(2**63) <= raw <= 2**63 - 1
        or health.get("scale") != 100_000
    ):
        raise ValueError("health fixed-point value is malformed")
    expected_band = (
        "dying_or_worse"
        if raw <= 150_000
        else "below_fine"
        if raw < 300_000
        else "fine_or_better"
    )
    if (
        payload.get("key") != expected_band
        or payload.get("below_fine") is not (raw < 300_000)
        or payload.get("at_or_below_death_chance_dying")
        is not (raw <= 150_000)
    ):
        raise ValueError("health-band projection disagrees with frozen cutoffs")
    return _component(
        "available",
        {
            "raw": raw,
            "scale": 100_000,
            "band": expected_band,
            "below_fine": raw < 300_000,
            "at_or_below_death_chance_dying": raw <= 150_000,
        },
    )


def _stress(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("stress component must be an object")
    status = value.get("status")
    if status == "unavailable":
        return _component(
            "unavailable", reason=_reason(value, "stress component")
        )
    points = value.get("value")
    if (
        status != "available"
        or value.get("unavailable_reason") is not None
        or isinstance(points, bool)
        or not isinstance(points, int)
        or not 0 <= points <= 2**31 - 1
    ):
        raise ValueError("stress component is malformed")
    return _component(
        "available",
        {
            "points": points,
            "at_or_above_first_break_threshold": points >= 100,
        },
    )


def _reason(value: dict[str, object], field: str) -> str:
    reason = value.get("unavailable_reason")
    if not isinstance(reason, str) or not reason or value.get("value") is not None:
        raise ValueError(f"{field} unavailable reason is invalid")
    return reason


def _legitimacy(value: object | None) -> dict[str, object]:
    if value is None:
        return _component(
            "unavailable", reason="player_legitimacy_state_unavailable"
        )
    if not isinstance(value, dict):
        raise ValueError("legitimacy component must be an object")
    status = value.get("status")
    if status == "unavailable":
        return _component(
            "unavailable", reason=_reason(value, "legitimacy component")
        )
    if status == "not_applicable":
        reason = _reason(value, "legitimacy component")
        if reason != "no_applicable_legitimacy_type":
            raise ValueError("legitimacy not-applicable reason is invalid")
        return _component("not_applicable", reason=reason)
    payload = value.get("value")
    if (
        status != "available"
        or value.get("unavailable_reason") is not None
        or not isinstance(payload, dict)
        or set(payload)
        != {"raw", "scale", "type_key", "current_level", "at_floor_level"}
    ):
        raise ValueError("legitimacy component is malformed")
    raw = payload.get("raw")
    type_key = payload.get("type_key")
    current_level = payload.get("current_level")
    at_floor = payload.get("at_floor_level")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or not 0 <= raw <= 2**63 - 1
        or payload.get("scale") != 100_000
        or not isinstance(type_key, str)
        or not type_key
        or isinstance(current_level, bool)
        or not isinstance(current_level, int)
        or not 0 <= current_level <= 2**31 - 1
        or not isinstance(at_floor, bool)
        or at_floor is not (current_level == 0)
    ):
        raise ValueError("legitimacy component is malformed")
    return _component("available", payload)


def _succession_risk(value: object) -> bool | None:
    if not isinstance(value, dict):
        raise ValueError("succession state must be an object")
    no_heir = value.get("no_primary_title_heir_alert")
    partition = value.get("partition")
    if not isinstance(no_heir, dict) or not isinstance(partition, dict):
        raise ValueError("succession risk components are missing")
    risk = False
    if no_heir.get("status") == "available":
        if not isinstance(no_heir.get("value"), bool):
            raise ValueError("no-heir alert is malformed")
        risk = bool(no_heir["value"])
    elif no_heir.get("status") != "not_applicable":
        return None
    if partition.get("status") == "available":
        payload = partition.get("value")
        if not isinstance(payload, dict) or not isinstance(
            payload.get("split_risk"), bool
        ):
            raise ValueError("partition risk is malformed")
        risk = risk or bool(payload["split_risk"])
    elif partition.get("status") != "not_applicable":
        return None
    return risk


def _planner_signals(
    health: dict[str, object],
    stress: dict[str, object],
    legitimacy: dict[str, object],
    succession_state: object,
) -> dict[str, object]:
    succession_risk = _succession_risk(succession_state)
    if health["status"] != "available" or succession_risk is None:
        succession_priority = _component(
            "unavailable", reason="succession_preparation_inputs_unavailable"
        )
    else:
        band = health["value"]["band"]
        priority = (
            "critical"
            if band == "dying_or_worse" and succession_risk
            else "elevated"
            if band == "below_fine" and succession_risk
            else "normal"
        )
        succession_priority = _component("available", priority)

    avoid_stress = (
        _component(
            "available",
            bool(stress["value"]["at_or_above_first_break_threshold"]),
        )
        if stress["status"] == "available"
        else _component(
            "unavailable", reason=str(stress["unavailable_reason"])
        )
    )
    if legitimacy["status"] == "available":
        protect_legitimacy = _component(
            "available", bool(legitimacy["value"]["at_floor_level"])
        )
    elif legitimacy["status"] == "not_applicable":
        protect_legitimacy = _component("available", False)
    else:
        protect_legitimacy = _component(
            "unavailable", reason=str(legitimacy["unavailable_reason"])
        )
    return {
        "succession_preparation_priority": succession_priority,
        "avoid_discretionary_stress_gain": avoid_stress,
        "protect_legitimacy_floor": protect_legitimacy,
    }


def build_player_vitals_v1(
    *,
    turn_bundle_binding: object,
    character_id: object,
    health_band: object,
    stress_points: object,
    succession_state: object,
    legitimacy: object | None = None,
) -> dict[str, object]:
    """Build local-readiness vitals without inventing legitimacy state."""

    binding = _binding(turn_bundle_binding, character_id)
    health = _health(health_band)
    stress = _stress(stress_points)
    legitimacy_value = _legitimacy(legitimacy)
    identity_ready = True
    health_ready = health["status"] == "available"
    stress_ready = stress["status"] == "available"
    legitimacy_balance_ready = legitimacy_value["status"] == "available"
    legitimacy_classification_ready = legitimacy_value["status"] in {
        "available",
        "not_applicable",
    }
    vitals_ready = (
        identity_ready
        and health_ready
        and stress_ready
        and legitimacy_balance_ready
        and legitimacy_classification_ready
    )
    observed_component = (
        health_ready or stress_ready or legitimacy_classification_ready
    )
    return {
        "schema": PLAYER_VITALS_V1_SCHEMA,
        "status": (
            "available"
            if health_ready and stress_ready and legitimacy_classification_ready
            else "partial"
            if observed_component
            else "unavailable"
        ),
        "binding": binding,
        "health": health,
        "stress": stress,
        "legitimacy": legitimacy_value,
        "readiness": {
            "identity_ready": identity_ready,
            "health_ready": health_ready,
            "stress_ready": stress_ready,
            "legitimacy_balance_ready": legitimacy_balance_ready,
            "legitimacy_classification_ready": (
                legitimacy_classification_ready
            ),
            "vitals_ready": vitals_ready,
        },
        "planner_signals": _planner_signals(
            health,
            stress,
            legitimacy_value,
            succession_state,
        ),
    }

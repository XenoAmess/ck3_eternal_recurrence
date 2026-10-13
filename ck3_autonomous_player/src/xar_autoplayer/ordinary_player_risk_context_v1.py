"""Compact current-player risk evidence from an already observed root result.

This pure projection performs no query and chooses no action. Native history
results may omit the Service ``binding`` rendering; in that case the binding
is copied only from their actual queried fields and the root's observed date.
"""

from __future__ import annotations

import copy

from .bridge.turn_bundle_contract import build_turn_bundle_v1


ORDINARY_PLAYER_RISK_CONTEXT_V1_SCHEMA = "xar.ck3.ordinary-player-risk-context/v1"
_ALERT_KEYS = (
    "ruler_health_below_fine", "ruler_stress_at_or_above_100",
    "no_primary_title_heir", "succession_partition_split",
)


def _unavailable(reason: str) -> dict[str, object]:
    component = {"status": "unavailable", "value": None, "unavailable_reason": reason}
    return {
        "schema": ORDINARY_PLAYER_RISK_CONTEXT_V1_SCHEMA,
        "status": "unavailable", "binding": None, "source": None,
        "current_scope": None,
        "health": copy.deepcopy(component), "stress": copy.deepcopy(component),
        "alerts": {key: copy.deepcopy(component) for key in _ALERT_KEYS},
        "planner_signals": {
            key: copy.deepcopy(component) for key in (
                "succession_preparation_priority", "avoid_discretionary_stress_gain",
                "protect_legitimacy_floor",
            )
        },
        "readiness": {
            "health_ready": False, "stress_ready": False,
            "succession_priority_ready": False, "legitimacy_protection_ready": False,
        },
        "unavailable_reason": reason,
    }


def _observed_root_result(snapshot: dict, result: dict) -> dict:
    root = result.get("campaign_root_context")
    if not isinstance(root, dict):
        raise ValueError("missing campaign root")
    fields = {
        "queried_snapshot_id": "snapshot_id", "queried_revision": "revision",
        "queried_native_revision": "native_revision",
    }
    for observed, current in fields.items():
        if observed in result and result[observed] != snapshot.get(current):
            raise ValueError("queried frame changed")
    diagnostics = snapshot.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None
    # CampaignRoot's production response does not publish a connection
    # generation. Its Driver cache/history owns that binding. Do not turn
    # current diagnostics into an invented response witness or required field.
    if "queried_connection_generation" in result:
        observed_generation = result["queried_connection_generation"]
        if (type(observed_generation) is not int or observed_generation <= 0
                or type(generation) is not int or generation <= 0
                or observed_generation != generation):
            raise ValueError("connection generation changed")
    if not isinstance(result.get("binding"), dict):
        # These values come from the actual response, never from a current
        # snapshot default. Missing wire metadata cannot become an observation.
        if not all(field in result for field in fields):
            raise ValueError("missing observed binding")
        result = {
            **result,
            "binding": {
                current: result[observed] for observed, current in fields.items()
            } | {"date_raw": root.get("date_raw")},
        }
    binding = result["binding"]
    if (not isinstance(binding.get("snapshot_id"), str)
            or not binding["snapshot_id"]
            or type(binding.get("revision")) is not int
            or binding["revision"] < 0
            or type(binding.get("native_revision")) is not int
            or binding["native_revision"] <= 0
            or type(binding.get("date_raw")) is not int):
        raise ValueError("invalid observed binding")
    return result


def build_ordinary_player_risk_context_v1(
    snapshot: object, campaign_root_result: object = None,
) -> dict[str, object]:
    """Reuse one genuine same-frame root result, retaining partial risk inputs.

    Missing or rejected observations stay typed unavailable. The caller may
    attach this evidence to any existing plan without changing its priority.
    """
    if campaign_root_result is None:
        return _unavailable("same_frame_campaign_root_result_unavailable")
    if not isinstance(snapshot, dict) or not isinstance(campaign_root_result, dict):
        return _unavailable("same_frame_player_risk_inputs_invalid")
    try:
        result = _observed_root_result(snapshot, campaign_root_result)
        bundle = build_turn_bundle_v1(snapshot, result)
    except (ValueError, KeyError, TypeError):
        return _unavailable("same_frame_player_risk_inputs_invalid")
    ruler = bundle["ruler_state"]
    if ruler["status"] != "available":
        return _unavailable(str(bundle["unavailable_reason"]))
    vitals = ruler["value"]["vitals"]
    signals = vitals["planner_signals"]
    binding = {
        key: bundle["binding"][key]
        for key in ("snapshot_id", "revision", "native_revision", "date_raw")
    }
    binding["character_id"] = ruler["value"]["character_id"]
    diagnostics = snapshot.get("diagnostics")
    generation = diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None
    return {
        "schema": ORDINARY_PLAYER_RISK_CONTEXT_V1_SCHEMA,
        "status": vitals["status"], "binding": binding,
        "source": copy.deepcopy(bundle["source"]),
        "current_scope": {
            "connection_generation": generation if type(generation) is int and generation > 0 else None,
            "source": "current_snapshot_diagnostics",
            "response_connection_generation_observed": "queried_connection_generation" in result,
        },
        "health": copy.deepcopy(vitals["health"]),
        "stress": copy.deepcopy(vitals["stress"]),
        "alerts": {key: copy.deepcopy(bundle["alerts"]["value"][key]) for key in _ALERT_KEYS},
        "planner_signals": copy.deepcopy(signals),
        "readiness": {
            "health_ready": vitals["readiness"]["health_ready"],
            "stress_ready": vitals["readiness"]["stress_ready"],
            "succession_priority_ready": signals["succession_preparation_priority"]["status"] == "available",
            "legitimacy_protection_ready": signals["protect_legitimacy_floor"]["status"] == "available",
        },
        "unavailable_reason": None,
    }

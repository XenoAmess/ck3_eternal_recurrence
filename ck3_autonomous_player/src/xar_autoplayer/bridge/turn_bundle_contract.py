"""Planner-facing same-frame aggregate over current read-only primitives."""

from __future__ import annotations

import copy
from typing import Final

from .campaign_root_context_contract import (
    QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
)


TURN_BUNDLE_V1_SCHEMA: Final = "xar.ck3.turn-bundle/v1"
QUERY_TURN_BUNDLE_V1_TOOL: Final = "ck3_query_turn_bundle_v1"


def _component(
    status: str,
    value: object = None,
    *,
    reason: str | None = None,
) -> dict[str, object]:
    if status not in {"available", "unavailable", "not_applicable"}:
        raise ValueError("turn-bundle component status is invalid")
    if status == "available":
        if value is None or reason is not None:
            raise ValueError("available component must carry only a value")
    elif value is not None or not isinstance(reason, str) or not reason:
        raise ValueError("non-available component must carry only a reason")
    return {
        "status": status,
        "value": copy.deepcopy(value),
        "unavailable_reason": reason,
    }


def _positive_int(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        raise ValueError(f"{name} must be a positive int32")
    return value


def _fixed_point_component(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != {"raw", "scale"}:
        raise ValueError(f"{name} is malformed")
    raw = value.get("raw")
    if (
        isinstance(raw, bool)
        or not isinstance(raw, int)
        or not -(2**63) <= raw <= 2**63 - 1
        or value.get("scale") != 100_000
    ):
        raise ValueError(f"{name} is malformed")
    return _component("available", {"raw": raw, "scale": 100_000})


def _binding(
    snapshot: object,
    campaign_root_result: object,
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    if not isinstance(snapshot, dict) or not isinstance(
        campaign_root_result, dict
    ):
        raise ValueError("turn-bundle inputs must be objects")
    root = campaign_root_result.get("campaign_root_context")
    binding = campaign_root_result.get("binding")
    if not isinstance(root, dict) or not isinstance(binding, dict):
        raise ValueError("campaign-root result lacks context binding")
    for key in ("snapshot_id", "revision", "native_revision", "date_raw"):
        if binding.get(key) != snapshot.get(key):
            raise ValueError("turn-bundle inputs do not share one frame")
    if snapshot.get("paused") is not True:
        raise ValueError("turn-bundle requires a paused frame")
    if root.get("snapshot_revision") != snapshot.get("native_revision"):
        raise ValueError("campaign-root native revision binding changed")
    if root.get("date_raw") != snapshot.get("date_raw"):
        raise ValueError("campaign-root date binding changed")
    query_sequence = campaign_root_result.get("query_sequence")
    if (
        isinstance(query_sequence, bool)
        or not isinstance(query_sequence, int)
        or not 1 <= query_sequence <= 2**64 - 1
    ):
        raise ValueError("campaign-root query sequence is invalid")
    return snapshot, campaign_root_result, root


def _unavailable_bundle(
    snapshot: dict[str, object],
    result: dict[str, object],
    root: dict[str, object],
) -> dict[str, object]:
    reason = root.get("unavailable_reason")
    if not isinstance(reason, str) or not reason:
        raise ValueError("unavailable campaign root lacks a reason")
    unavailable = _component("unavailable", reason=reason)
    readiness = {
        "root_identity_ready": False,
        "ruler_alive_alert_ready": False,
        "ruler_stress_alert_ready": False,
        "ruler_health_alert_ready": False,
        "ruler_resources_ready": False,
        "realm_relationship_alerts_ready": False,
        "realm_domain_ready": False,
        "realm_council_ready": False,
        "realm_faction_alert_ready": False,
        "succession_primary_title_alert_ready": False,
        "succession_partition_ready": False,
        "event_pending_ready": False,
        "war_summary_ready": False,
        "minimum_alerts_ready": False,
        "ready": False,
    }
    return {
        "schema": TURN_BUNDLE_V1_SCHEMA,
        "status": "unavailable",
        "binding": copy.deepcopy(result["binding"]),
        "ruler_state": unavailable,
        "realm_state": copy.deepcopy(unavailable),
        "succession_state": copy.deepcopy(unavailable),
        "pending_state": copy.deepcopy(unavailable),
        "war_state": copy.deepcopy(unavailable),
        "alerts": copy.deepcopy(unavailable),
        "readiness": readiness,
        "unavailable_reason": reason,
        "source": {
            "capability": QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
            "query_sequence": result["query_sequence"],
            "backend_id": snapshot.get("backend_id"),
        },
    }


def _optional_snapshot_components(
    snapshot: dict[str, object],
    *,
    character_id: int,
    alive: bool,
) -> tuple[dict[str, object], dict[str, object]]:
    played = snapshot.get("played_character")
    if played is not None:
        if not isinstance(played, dict):
            raise ValueError("snapshot played_character is malformed")
        if (
            played.get("character_id") != character_id
            or played.get("alive") is not alive
        ):
            raise ValueError("snapshot and campaign-root character disagree")
    stress = played.get("stress_points") if isinstance(played, dict) else None
    stress_component = (
        _component("available", stress)
        if isinstance(stress, int)
        and not isinstance(stress, bool)
        and 0 <= stress <= 2**31 - 1
        else _component(
            "unavailable", reason="played_character_stress_unavailable"
        )
    )
    gold = snapshot.get("played_character_gold")
    gold_component = _component(
        "unavailable", reason="played_character_gold_unavailable"
    )
    if isinstance(gold, dict):
        raw = gold.get("raw")
        scale = gold.get("scale")
        if (
            isinstance(raw, int)
            and not isinstance(raw, bool)
            and -(2**63) <= raw <= 2**63 - 1
            and scale == 100_000
        ):
            gold_component = _component(
                "available", {"raw": raw, "scale": 100_000}
            )
        elif gold is not None:
            raise ValueError("snapshot played_character_gold is malformed")
    return stress_component, gold_component


def _pending_state(snapshot: dict[str, object]) -> tuple[dict[str, object], bool]:
    if (
        "active_event" not in snapshot
        or "pending_character_interaction" not in snapshot
    ):
        return (
            {
                "active_event": _component(
                    "unavailable", reason="active_event_observation_unavailable"
                ),
                "pending_character_interaction": _component(
                    "unavailable",
                    reason="pending_character_interaction_observation_unavailable",
                ),
            },
            False,
        )
    active_event = snapshot.get("active_event")
    pending = snapshot.get("pending_character_interaction")
    if active_event is not None and not isinstance(active_event, dict):
        raise ValueError("active_event is malformed")
    if pending is not None and not isinstance(pending, dict):
        raise ValueError("pending_character_interaction is malformed")
    return (
        {
            "active_event": (
                _component("available", active_event)
                if active_event is not None
                else _component("not_applicable", reason="no_active_event")
            ),
            "pending_character_interaction": (
                _component("available", pending)
                if pending is not None
                else _component(
                    "not_applicable", reason="no_pending_character_interaction"
                )
            ),
        },
        True,
    )


def _war_state(snapshot: dict[str, object]) -> tuple[dict[str, object], bool]:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return (
            {"active_war_count": None, "wars": []},
            False,
        )
    summaries: list[dict[str, object]] = []
    seen: set[int] = set()
    for index, war in enumerate(wars):
        if not isinstance(war, dict):
            raise ValueError(f"active_wars[{index}] is malformed")
        war_id = _positive_int(war.get("war_id"), f"active_wars[{index}].war_id")
        if war_id in seen:
            raise ValueError("active_wars contains duplicate WarIDs")
        seen.add(war_id)
        side = war.get("player_side")
        score = war.get("player_relative_war_score")
        opponent = war.get("primary_opponent_character_id")
        if side not in {"attacker", "defender"}:
            raise ValueError("active war player_side is malformed")
        if isinstance(score, bool) or not isinstance(score, int):
            raise ValueError("active war score is malformed")
        if opponent is not None:
            opponent = _positive_int(opponent, "primary opponent")
        summaries.append(
            {
                "war_id": war_id,
                "player_side": side,
                "primary_opponent_character_id": opponent,
                "player_relative_war_score": score,
            }
        )
    summaries.sort(key=lambda row: int(row["war_id"]))
    return {"active_war_count": len(summaries), "wars": summaries}, True


def build_turn_bundle_v1(
    snapshot: object,
    campaign_root_result: object,
) -> dict[str, object]:
    """Build one truthful planner aggregate without additional native RPCs."""

    snapshot, result, root = _binding(snapshot, campaign_root_result)
    if result.get("status") != root.get("status"):
        raise ValueError("campaign-root envelope and context disagree")
    if root.get("status") == "unavailable":
        return _unavailable_bundle(snapshot, result, root)
    if root.get("status") != "available":
        raise ValueError("campaign-root status is invalid")

    character_id = _positive_int(
        root.get("player_character_id"), "player_character_id"
    )
    alive = root.get("player_character_alive")
    if not isinstance(alive, bool):
        raise ValueError("player_character_alive is malformed")
    stress, gold = _optional_snapshot_components(
        snapshot, character_id=character_id, alive=alive
    )
    income = _fixed_point_component(
        root.get("player_monthly_gold_income"),
        "player_monthly_gold_income",
    )

    primary_title = root.get("primary_title")
    primary_title_component = (
        _component("available", primary_title)
        if isinstance(primary_title, dict)
        else _component(
            "not_applicable", reason="no_primary_landed_title"
        )
    )
    capital = root.get("capital_province_id")
    capital_component = (
        _component("available", _positive_int(capital, "capital_province_id"))
        if capital is not None
        else _component("not_applicable", reason="no_current_capital")
    )
    government = root.get("government")
    government_component = (
        _component("available", government)
        if isinstance(government, dict)
        else _component("not_applicable", reason="no_current_government")
    )
    ruler_state = {
        "character_id": character_id,
        "alive": alive,
        "primary_title": primary_title_component,
        "capital_province_id": capital_component,
        "government": government_component,
        "gold": gold,
        "income": income,
        "stress_points": stress,
        "health_band": _component(
            "unavailable", reason="ruler_health_observation_not_implemented"
        ),
    }

    direct_vassals = root.get("direct_landed_vassal_character_ids")
    adjacent_holders = root.get(
        "adjacent_external_province_holder_character_ids"
    )
    related = root.get("related_character_contexts")
    if not isinstance(direct_vassals, list) or not isinstance(
        adjacent_holders, list
    ) or not isinstance(related, list):
        raise ValueError("campaign-root relationship vectors are malformed")
    related_by_id = {
        _positive_int(row.get("character_id"), "related character_id"): row
        for row in related
        if isinstance(row, dict)
    }
    if len(related_by_id) != len(related):
        raise ValueError("related character contexts are malformed")
    adjacent_top_lieges = sorted(
        {
            _positive_int(
                related_by_id[_positive_int(holder, "adjacent holder")].get(
                    "top_liege_character_id"
                ),
                "adjacent holder top liege",
            )
            for holder in adjacent_holders
        }
    )
    realm_state = {
        "top_liege_character_id": _positive_int(
            root.get("top_liege_character_id"), "top_liege_character_id"
        ),
        "independent": root.get("independent"),
        "direct_landed_vassal_character_ids": copy.deepcopy(direct_vassals),
        "adjacent_external_province_holder_character_ids": copy.deepcopy(
            adjacent_holders
        ),
        "adjacent_holder_top_liege_character_ids": adjacent_top_lieges,
        "domain": _component(
            "unavailable", reason="realm_domain_observation_not_implemented"
        ),
        "council": _component(
            "unavailable", reason="realm_council_observation_not_implemented"
        ),
        "faction_alert": _component(
            "unavailable", reason="realm_faction_observation_not_implemented"
        ),
    }
    if not isinstance(realm_state["independent"], bool):
        raise ValueError("campaign-root independent state is malformed")

    successors = root.get("primary_title_succession_character_ids")
    if not isinstance(successors, list) or any(
        isinstance(value, bool) or not isinstance(value, int) or value <= 0
        for value in successors
    ):
        raise ValueError("primary-title succession vector is malformed")
    if primary_title is None and successors:
        raise ValueError("landless root exposes title successors")
    heir = (
        _component("available", successors[0])
        if successors
        else _component(
            "not_applicable",
            reason=(
                "no_primary_landed_title"
                if primary_title is None
                else "no_observed_primary_title_successor"
            ),
        )
    )
    no_heir_alert = (
        _component("not_applicable", reason="no_primary_landed_title")
        if primary_title is None
        else _component("available", not successors)
    )
    succession_state = {
        "primary_title": primary_title_component,
        "ordered_primary_title_successor_character_ids": copy.deepcopy(
            successors
        ),
        "primary_title_heir_character_id": heir,
        "no_primary_title_heir_alert": no_heir_alert,
        "partition": _component(
            "unavailable", reason="succession_partition_observation_not_implemented"
        ),
    }

    pending_state, pending_ready = _pending_state(snapshot)
    war_state, war_ready = _war_state(snapshot)
    high_stress = (
        _component("available", int(stress["value"]) >= 100)
        if stress["status"] == "available"
        else _component(
            "unavailable", reason=str(stress["unavailable_reason"])
        )
    )
    alerts = {
        "ruler_dead": _component("available", not alive),
        "ruler_landless": _component("available", primary_title is None),
        "ruler_stress_at_or_above_100": high_stress,
        "realm_has_no_direct_landed_vassals": _component(
            "available", not direct_vassals
        ),
        "realm_has_adjacent_external_holders": _component(
            "available", bool(adjacent_holders)
        ),
        "no_primary_title_heir": no_heir_alert,
        "faction_threat": _component(
            "unavailable", reason="realm_faction_observation_not_implemented"
        ),
    }
    gold_ready = gold["status"] == "available"
    income_ready = income["status"] == "available"
    stress_ready = stress["status"] == "available"
    readiness = {
        "root_identity_ready": True,
        "ruler_alive_alert_ready": True,
        "ruler_stress_alert_ready": stress_ready,
        "ruler_health_alert_ready": False,
        "ruler_resources_ready": gold_ready and income_ready,
        "realm_relationship_alerts_ready": True,
        "realm_domain_ready": False,
        "realm_council_ready": False,
        "realm_faction_alert_ready": False,
        "succession_primary_title_alert_ready": True,
        "succession_partition_ready": False,
        "event_pending_ready": pending_ready,
        "war_summary_ready": war_ready,
        "minimum_alerts_ready": True,
        "ready": False,
    }
    assert not readiness["ruler_resources_ready"] or (
        gold_ready and income_ready
    )
    return {
        "schema": TURN_BUNDLE_V1_SCHEMA,
        "status": "partial",
        "binding": copy.deepcopy(result["binding"]),
        "ruler_state": _component("available", ruler_state),
        "realm_state": _component("available", realm_state),
        "succession_state": _component("available", succession_state),
        "pending_state": _component("available", pending_state),
        "war_state": (
            _component("available", war_state)
            if war_ready
            else _component("unavailable", reason="active_wars_unavailable")
        ),
        "alerts": _component("available", alerts),
        "readiness": readiness,
        "unavailable_reason": None,
        "source": {
            "capability": QUERY_CAMPAIGN_ROOT_CONTEXT_V1_CAPABILITY,
            "query_sequence": result["query_sequence"],
            "backend_id": snapshot.get("backend_id"),
        },
    }

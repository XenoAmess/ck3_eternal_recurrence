"""Consume the current native government profile for an ordinary goal plan."""

from __future__ import annotations

from collections.abc import Mapping

from .bridge.driver import BridgeUnavailableError
from .bridge.government_runtime_adapter_private_transport import (
    normalize_government_runtime_adapter_v1,
)
from .bridge.succession_transition_contract import ORDINARY_CAMPAIGN_SUCCESSION


SCHEMA = "ordinary-campaign-government-context-v1"


def build_ordinary_campaign_government_context_v1(
    snapshot: Mapping[str, object], *, government_observation: object = None,
    query_permitted: bool = False,
) -> dict[str, object]:
    """Publish observed adapter readiness without changing the bounded policy.

    The service owns the optional fresh query. This pure consumer performs no
    query, persists no profile and never infers a government from the goal or
    a predecessor. The existing normalizer binds the native observation to
    the current build, player, date and revision.
    """
    goal = snapshot.get("campaign_goal")
    lifecycle = snapshot.get("succession_lifecycle")
    result: dict[str, object] = {
        "schema": SCHEMA,
        "schema_version": 1,
        "status": "not_queried",
        "query_permitted": query_permitted is True,
        "identity_observation_ready": False,
        "core_adapter_ready": False,
        "ordinary_goal_context_ready": False,
        "unavailable_reason": None,
        "campaign_id": goal.get("campaign_id") if isinstance(goal, Mapping) else None,
        "current_character_id": goal.get("current_character_id") if isinstance(goal, Mapping) else None,
        "snapshot_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "government_key": None,
        "adapter_family": None,
        "adapter_status": None,
        "government_runtime_adapter": None,
    }
    if not isinstance(lifecycle, Mapping) or lifecycle.get("lifecycle") != ORDINARY_CAMPAIGN_SUCCESSION:
        return {**result, "status": "inactive", "unavailable_reason": "not_ordinary_campaign"}
    if query_permitted is not True:
        return {**result, "unavailable_reason": "government_query_not_permitted"}
    if not isinstance(goal, dict):
        return {**result, "unavailable_reason": "ordinary_campaign_goal_unavailable"}

    from .strategy import normalize_ordinary_campaign_goal_v1

    try:
        goal = normalize_ordinary_campaign_goal_v1(goal)
    except ValueError as error:
        return {**result, "status": "unavailable", "unavailable_reason": str(error)}
    if government_observation is None:
        return {**result, "status": "unavailable", "unavailable_reason": "government_observation_unavailable"}
    try:
        observed = normalize_government_runtime_adapter_v1(
            government_observation, snapshot=snapshot,
        )
    except (ValueError, BridgeUnavailableError) as error:
        return {**result, "status": "unavailable", "unavailable_reason": str(error)}

    readiness = observed["readiness"]
    government = observed.get("government")
    adapter = observed.get("adapter")
    identity_ready = observed["status"] == "available" and readiness["same_frame_ready"] is True
    core_ready = identity_ready and readiness["core_adapter_ready"] is True
    played = snapshot.get("played_character")
    goal_matches_player = isinstance(played, Mapping) and goal["current_character_id"] == played.get("character_id")
    reason = observed.get("unavailable_reason")
    if identity_ready and not goal_matches_player:
        reason = "ordinary_goal_current_ruler_not_matched"
    elif identity_ready and not core_ready:
        reason = adapter.get("status") if isinstance(adapter, Mapping) else "government_adapter_unavailable"
    return {
        **result,
        "status": observed["status"],
        "identity_observation_ready": identity_ready,
        "core_adapter_ready": core_ready,
        "ordinary_goal_context_ready": core_ready and goal_matches_player,
        "unavailable_reason": reason,
        "government_key": government.get("key") if isinstance(government, Mapping) else None,
        "adapter_family": adapter.get("family") if isinstance(adapter, Mapping) else None,
        "adapter_status": adapter.get("status") if isinstance(adapter, Mapping) else None,
        "government_runtime_adapter": observed,
    }

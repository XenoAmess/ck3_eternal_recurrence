"""Join a current stock faction alert to an already legal gift proposal.

The existing public observer owns native metrics and the dangerous predicate.
This consumer adds no ultimatum estimate and does not choose a different member.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping, Sequence

from .bridge.driver import BridgeUnavailableError, UnsupportedStepError
from .bridge.player_faction_alerts_contract import (
    QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY,
    QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
)


def _same_frame(raw: object, snapshot: Mapping[str, object]) -> bool:
    actor = snapshot.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    return bool(isinstance(raw, Mapping)
                and raw.get("snapshot_revision") == snapshot.get("native_revision")
                and raw.get("date_raw") == snapshot.get("date_raw")
                and raw.get("player_character_id") == actor_id)


def observe_faction_gift_stock_threat_v1(
    driver: object, *, snapshot: Mapping[str, object],
    history: Sequence[Mapping[str, object]], candidate: Mapping[str, object],
    expected_revision: int,
) -> dict[str, object]:
    """Reuse a same-frame alert or make one existing read-only observer call.

    An unavailable alert leaves the independently legal gift and building
    candidates intact. Only an observed matching stock danger gets preference.
    """
    unavailable = {"status": "unavailable", "dangerous_response_ready": False,
                   "exact_ultimatum_timing_ready": False}
    choice = candidate.get("choice")
    if candidate.get("status") != "selected" or not isinstance(choice, Mapping):
        return {**unavailable, "reason": "no_selected_gift"}
    result = None
    for row in reversed(history):
        if (row.get("command") == QUERY_PLAYER_FACTION_ALERTS_V1_STEP
                and row.get("ok") is True
                and isinstance(row.get("result"), Mapping)
                and _same_frame(row["result"].get("player_faction_alerts"), snapshot)):
            result = row["result"]
            break
    reused = result is not None
    if result is None:
        execute = getattr(driver, "execute_step", None)
        capabilities = getattr(driver, "capabilities", None)
        caps = capabilities() if callable(capabilities) else {}
        bridge = caps.get("bridge_capabilities") if isinstance(caps, Mapping) else None
        if (not callable(execute) or not isinstance(bridge, list)
                or QUERY_PLAYER_FACTION_ALERTS_V1_CAPABILITY not in bridge):
            return {**unavailable, "reason": "existing_alert_observer_unavailable"}
        try:
            result = execute(QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
                             expected_revision=expected_revision)
        except (BridgeUnavailableError, UnsupportedStepError) as error:
            return {**unavailable, "reason": "existing_alert_read_unavailable",
                    "observer_error": str(error)}
    raw = result.get("player_faction_alerts") if isinstance(result, Mapping) else None
    readiness = raw.get("readiness") if isinstance(raw, Mapping) else None
    if (not _same_frame(raw, snapshot) or raw.get("status") != "available"
            or not isinstance(readiness, Mapping)
            or readiness.get("targeting_rows_ready") is not True
            or readiness.get("stock_dangerous_predicate_ready") is not True
            or readiness.get("same_frame_ready") is not True):
        return {**unavailable, "reason": "same_frame_stock_threat_not_observed"}
    rows = raw.get("targeting_factions")
    if not isinstance(rows, list):
        return {**unavailable, "reason": "current_targeting_rows_unavailable"}
    matched = [row for row in rows if isinstance(row, Mapping)
               and row.get("faction_id") == choice.get("source_faction_id")]
    if len(matched) != 1:
        return {**unavailable, "reason": "selected_faction_not_in_current_alert"}
    row = matched[0]
    recipient = choice.get("recipient_character_id")
    if (row.get("target_character_id") != raw["player_character_id"]
            or (recipient != row.get("leader_character_id")
                and recipient not in row.get("character_member_ids", []))):
        return {**unavailable, "reason": "selected_recipient_not_in_current_faction"}
    return {
        "status": "observed", "observer_step": QUERY_PLAYER_FACTION_ALERTS_V1_STEP,
        "same_frame_history_reused": reused,
        "source_faction_id": choice["source_faction_id"],
        "recipient_character_id": recipient,
        "snapshot_revision": raw["snapshot_revision"], "date_raw": raw["date_raw"],
        "player_character_id": raw["player_character_id"],
        "dangerous_response_ready": (row.get("dangerous_by_stock_rule") is True
                                     and row.get("faction_at_war") is False),
        "native_row": deepcopy(dict(row)),
        "exact_ultimatum_timing_ready": False,
        "faction_departure_or_threat_resolution": "not_inferred",
    }

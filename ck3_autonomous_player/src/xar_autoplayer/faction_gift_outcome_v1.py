"""Observe a resolved gift's original faction and recipient without replaying it.

The existing native independent-pair reader also works after pending is retired.
Its historical cold-recovery name does not turn this read into cold recovery:
this consumer never calls a pending resolver or changes the gift ledger.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Mapping, Sequence

from .bridge.driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .bridge.faction_gift_formal_route_v1 import COLD_RECOVERY_STEP, RECEIPT_STEP, SUBMIT_STEP, _send
from .bridge.faction_gift_private_transport_v1 import _binding
from .bridge.player_faction_alerts_contract import QUERY_PLAYER_FACTION_ALERTS_V1_STEP


STEP = "query-resolved-faction-gift-outcome-v1"
SCHEMA = "xar.ck3.resolved_faction_gift_outcome.v1"


def _object(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _entry(row: Mapping[str, object]) -> tuple[object, Mapping[str, object]]:
    result = _object(row.get("result"))
    if row.get("command") == "auto-turn":
        turn = _object(result.get("auto_turn"))
        return turn.get("selected_step"), _object(turn.get("result"))
    return row.get("command"), result


def _history_original(
    history: Sequence[Mapping[str, object]], request_id: str,
    episode: object, actor: object,
) -> dict[str, object] | None:
    pending: Mapping[str, object] = {}
    receipt: Mapping[str, object] = {}
    for row in reversed(history):
        if row.get("ok") is not True:
            continue
        step, result = _entry(row)
        if step == RECEIPT_STEP and not receipt:
            item = _object(result.get("receipt"))
            if (item.get("request_id") == request_id
                    and item.get("schema_version") == 1
                    and item.get("status") in {"mitigated", "left"}
                    and item.get("postcondition_verified") is True
                    and item.get("mitigation_applied") is True):
                receipt = item
        if step == SUBMIT_STEP and not pending:
            item = _object(_object(result.get("pending_ledger")).get("pending"))
            if item.get("request_id") == request_id:
                pending = item
        if pending and receipt:
            break
    if (not pending or not receipt or pending.get("episode_run_id") != episode
            or pending.get("pre_player_character_id") != actor
            or receipt.get("player_character_id") != actor
            or receipt.get("source_faction_id") != pending.get("source_faction_id")
            or receipt.get("recipient_character_id") != pending.get("recipient_character_id")
            or any(type(receipt.get(key)) is not int or receipt[key] <= 0
                   for key in ("source_faction_id", "recipient_character_id"))
            or type(receipt.get("post_observed_date_raw")) is not int):
        return None
    return {
        "request_id": request_id, "episode_run_id": episode,
        "player_character_id": actor,
        "source_faction_id": receipt["source_faction_id"],
        "recipient_character_id": receipt["recipient_character_id"],
        "action_date_raw": pending.get("pre_date_raw"),
        "material_date_raw": receipt["post_observed_date_raw"],
        "gold_cost_raw": pending.get("gold_cost_raw"),
        "opinion_delta": pending.get("opinion_delta"),
        "pre_recipient_opinion_of_player": pending.get("pre_recipient_opinion_of_player"),
        "pre_source_faction_power_raw": pending.get("pre_source_faction_power_raw"),
        "pre_source_faction_discontent_raw": pending.get("pre_source_faction_discontent_raw"),
        "receipt": deepcopy(dict(receipt)),
    }


def _same_frame(raw: Mapping[str, object], snapshot: Mapping[str, object]) -> bool:
    return (raw.get("snapshot_revision") == snapshot.get("native_revision")
            and raw.get("date_raw") == snapshot.get("date_raw")
            and raw.get("player_character_id")
            == _object(snapshot.get("played_character")).get("character_id"))


def _alert(
    driver: object, history: Sequence[Mapping[str, object]],
    snapshot: Mapping[str, object], expected_revision: int, source: int,
) -> dict[str, object]:
    raw: Mapping[str, object] = {}
    for row in reversed(history):
        step, result = _entry(row)
        candidate = _object(result.get("player_faction_alerts"))
        if row.get("ok") is True and step == QUERY_PLAYER_FACTION_ALERTS_V1_STEP and _same_frame(candidate, snapshot):
            raw = candidate
            break
    if not raw:
        try:
            result = driver.execute_step(QUERY_PLAYER_FACTION_ALERTS_V1_STEP, expected_revision=expected_revision)
            raw = _object(_object(result).get("player_faction_alerts"))
        except (BridgeUnavailableError, UnsupportedStepError) as error:
            return {"status": "unavailable", "reason": str(error), "row": None}
    ready = _object(raw.get("readiness"))
    rows = raw.get("targeting_factions")
    if (raw.get("status") != "available" or not _same_frame(raw, snapshot)
            or ready.get("same_frame_ready") is not True
            or ready.get("targeting_rows_ready") is not True
            or ready.get("stock_dangerous_predicate_ready") is not True
            or not isinstance(rows, list)):
        return {"status": "unavailable", "reason": "current_alert_not_observed", "row": None}
    matches = [row for row in rows if isinstance(row, Mapping) and row.get("faction_id") == source]
    if not matches:
        return {"status": "not_in_current_targeting_vector", "row": None}
    if len(matches) != 1:
        return {"status": "unavailable", "reason": "current_alert_identity_ambiguous", "row": None}
    return {"status": "observed", "row": deepcopy(dict(matches[0]))}


def query_resolved_faction_gift_outcome_v1(
    driver: object, *, request_id: str, expected_revision: int,
) -> dict[str, object]:
    """Read original applied gift identities and their current independent facts."""
    if not isinstance(request_id, str) or not request_id:
        raise ValueError("resolved gift request_id is required")
    before = driver.take_internal_semantic_snapshot()
    if before.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("resolved gift outcome revision changed")
    actor = _object(before.get("played_character"))
    base: dict[str, object] = {
        "schema": SCHEMA, "request_id": request_id,
        "status": "unavailable", "attributed_to_gift": False,
        "observed_date_raw": before.get("date_raw"),
        "snapshot_revision": before.get("native_revision"),
        "episode_run_id": before.get("episode_run_id"),
    }
    if (before.get("paused") is not True or before.get("map_ready") is not True
            or actor.get("alive") is not True
            or type(before.get("native_revision")) is not int
            or type(before.get("date_raw")) is not int):
        return {**base, "reason": "current_paused_player_unavailable"}
    # Scan only under the existing driver lock, then copy the small original
    # material. Full Army/native history is never duplicated for this query.
    with driver._history_lock:
        original = _history_original(driver._command_history, request_id,
                                     before.get("episode_run_id"), actor.get("character_id"))
        alert_history = [deepcopy(row) for row in driver._command_history
                         if row.get("command") == QUERY_PLAYER_FACTION_ALERTS_V1_STEP]
    if original is None:
        return {**base, "reason": "original_applied_gift_not_in_current_episode_history"}
    base["original"] = original
    if before["date_raw"] < original["material_date_raw"]:
        return {**base, "reason": "current_date_precedes_original_material"}
    try:
        result = _send(driver, COLD_RECOVERY_STEP, {
            "expected_revision": before["native_revision"],
            "expected_date_raw": before["date_raw"],
            "expected_player_character_id": actor["character_id"],
            "source_faction_id": original["source_faction_id"],
            "recipient_character_id": original["recipient_character_id"],
        })
    except BridgeUnavailableError as error:
        return {**base, "reason": "independent_pair_unavailable", "observer_error": str(error)}
    native = _object(result.get("native"))
    observation = _object(native.get("observation"))
    if (result.get("step") != COLD_RECOVERY_STEP
            or result.get("accepted") is not True
            or result.get("status") != "independent_read_complete"
            or native.get("failure_flags") != 0
            or observation.get("available") is not True
            or observation.get("paused") is not True
            or observation.get("snapshot_revision") != before["native_revision"]
            or observation.get("native_snapshot_revision") != before["native_revision"]
            or observation.get("observed_date_raw") != before["date_raw"]
            or observation.get("player_character_id") != actor["character_id"]
            or observation.get("source_faction_requery_complete") is not True
            or observation.get("queried_source_faction_id") != original["source_faction_id"]
            or observation.get("recipient_identity_resolved") is not True
            or observation.get("recipient_character_id") != original["recipient_character_id"]
            or observation.get("recipient_opinion_query_complete") is not True
            or type(observation.get("recipient_opinion_of_player")) is not int
            or type(observation.get("gift_opinion_present")) is not bool
            or type(observation.get("source_faction_present")) is not bool):
        return {**base, "reason": "independent_pair_incomplete"}
    present = observation["source_faction_present"]
    members = observation.get("source_faction_member_character_ids")
    if present and (observation.get("source_faction_metrics_available") is not True
                    or not isinstance(members, list)):
        return {**base, "reason": "current_faction_material_incomplete"}
    member = (present and (observation.get("source_faction_leader_character_id")
                          == original["recipient_character_id"]
                          or original["recipient_character_id"] in members))
    alert = _alert(driver, alert_history, before, expected_revision, original["source_faction_id"])
    if _binding(driver.take_internal_semantic_snapshot()) != _binding(before):
        return {**base, "reason": "current_paused_frame_changed"}
    outcome = {**base, "status": "observed",
               "faction_outcome": ("faction_known_absent" if not present
                                   else "still_member" if member else "recipient_left"),
               "current_observation": deepcopy(dict(observation)), "current_alert": alert,
               "followup_date_advanced": before["date_raw"] > original["material_date_raw"],
               "gift_submit_performed": False, "pending_resolution_performed": False}
    driver._record_command(STEP, ok=True, result=outcome)
    return outcome

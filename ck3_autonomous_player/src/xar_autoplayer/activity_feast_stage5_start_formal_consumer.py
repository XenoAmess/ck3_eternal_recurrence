"""Default-off feast Start decision, durable pending intent and independent poststate."""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from pathlib import Path

from .activity_feast_stage5_value_policy import assess_feast_stage5_start
from .bridge.activity_feast_stage5_start_private_transport import (
    INPUT_SCHEMA, POST_SCHEMA, RESOURCE_KEYS,
    query_activity_feast_hosted_post_private_v1,
    submit_activity_feast_stage5_start_private_v1,
)
from .bridge.driver import BridgeUnavailableError
from .bridge.activity_feast_terminal_outcome_v1 import (
    normalize_activity_feast_terminal_outcome_v1,
)
from .environment import write_json_atomic


LEDGER_FILE = "activity-feast-stage5-start-private-v1.json"
LEDGER_SCHEMA = "xar.ck3.activity-feast-stage5-start-private.v1"
_TERMINAL_STATUSES = {"completed", "invalidated", "completed_and_invalidated"}
_OUTCOME_COUNTER_KEYS = ("prestige_raw", "stress_points", "reveler_present", "reveler_xp_raw")


def read_feast_start_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / LEDGER_FILE
    if not path.exists():
        return {"schema": LEDGER_SCHEMA, "pending": None, "resolved": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or set(data) != {"schema", "pending", "resolved"}
            or data["schema"] != LEDGER_SCHEMA
            or any(data[key] is not None and not isinstance(data[key], dict)
                   for key in ("pending", "resolved"))):
        raise ValueError("private feast Start ledger malformed")
    return data


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / LEDGER_FILE, dict(ledger))


def _hold(reason: str, *, status: str = "missing_input") -> dict[str, object]:
    return {"decision": "hold", "status": status, "reason": reason,
            "positive_value_supported": False, "postcondition_verified": False}


def assess_feast_start_private_v1(
    inputs: Mapping[str, object], *, guest: Mapping[str, object] | None,
    budget: Mapping[str, object] | None,
) -> dict[str, object]:
    """Require a qualified same-frame guest route and explicit budget inputs."""
    if inputs.get("schema") != INPUT_SCHEMA:
        raise ValueError("private feast Start inputs malformed")
    if inputs.get("final_can_start") is not True:
        return _hold("native_final_start_unavailable", status="not_actionable")
    if inputs.get("native_guest_route_qualified") is not True:
        return _hold("native_guest_route_unqualified")
    ordinary = inputs.get("ordinary_guest_route")
    if (guest is None and isinstance(ordinary, Mapping)
            and ordinary.get("status") == "observed"
            and ordinary.get("qualified") is True
            and isinstance(ordinary.get("candidate"), Mapping)):
        candidate = ordinary["candidate"]
        # One current native-filtered member of an active authored category.
        # Selected/special guest counts remain exactly as observed, including 0.
        guest = {
            "status": "observed", "arrival_time_observed": True,
            "same_frame": True,
            "snapshot_revision": candidate["snapshot_revision"],
            "date_raw": candidate["date_raw"],
            "actor_character_id": candidate["actor_character_id"],
            "timely_positive_join_count": 1,
        }
    if guest is None and "guest_join_status" in inputs:
        guest = {
            "status": inputs["guest_join_status"],
            "arrival_time_observed": inputs.get("arrival_time_observed"),
            "same_frame": True,
            "snapshot_revision": inputs.get("snapshot_revision"),
            "date_raw": inputs.get("date_raw"),
            "actor_character_id": inputs.get("actor_character_id"),
            "timely_positive_join_count": inputs.get("timely_positive_join_count"),
        }
    if (not isinstance(guest, Mapping)
            or guest.get("status") != "observed"
            or guest.get("arrival_time_observed") is not True
            or guest.get("same_frame") is not True
            or guest.get("snapshot_revision") != inputs.get("snapshot_revision")
            or guest.get("date_raw") != inputs.get("date_raw")
            or guest.get("actor_character_id") != inputs.get("actor_character_id")
            or type(guest.get("timely_positive_join_count")) is not int
            or guest["timely_positive_join_count"] <= 0):
        return _hold("guest_arrival_or_join_unobserved")
    if (not isinstance(budget, Mapping)
            or not isinstance(budget.get("reserved_raw"), Mapping)
            or set(budget["reserved_raw"]) != set(RESOURCE_KEYS)
            or any(type(budget["reserved_raw"][key]) is not int
                   or budget["reserved_raw"][key] < 0 for key in RESOURCE_KEYS)
            or budget.get("peaceful_spend_allowed") is None
            or budget.get("active_war_count") is None):
        return _hold("resource_commitments_or_spend_policy_unobserved")
    resources = inputs.get("resources")
    balances = inputs.get("balances")
    if (not isinstance(resources, Mapping) or not isinstance(balances, Mapping)
            or set(resources) != set(RESOURCE_KEYS)
            or set(balances) != set(RESOURCE_KEYS)):
        raise ValueError("private feast Start resources malformed")
    costs = [resources[key]["configured_cost_raw"] for key in RESOURCE_KEYS]
    # Unknown balances remain unknown.  The value policy consults each balance
    # only when its corresponding native configured cost is positive.
    available = [balances[key]["available"] for key in RESOURCE_KEYS]
    raw = [balances[key]["raw"] if available[i] and costs[i] else 0
           for i, key in enumerate(RESOURCE_KEYS)]
    try:
        return assess_feast_stage5_start(
            activity_key=inputs["activity_key"],
            selected_option_key=inputs["selected_option_key"],
            planning_stage=inputs["planning_stage"],
            final_can_start=inputs["final_can_start"],
            configured_cost_raw=costs,
            balance_available=available,
            balance_raw=raw,
            reserved_raw=[budget["reserved_raw"][key] for key in RESOURCE_KEYS],
            expected_nonhost_guest_count=guest["timely_positive_join_count"],
            peaceful_spend_allowed=budget["peaceful_spend_allowed"],
            gold_floor_raw=budget.get("gold_floor_raw"),
            active_war_count=budget["active_war_count"],
            war_cash_reserve_raw=budget.get("war_cash_reserve_raw"),
        )
    except ValueError as exc:
        return _hold("invalid_value_input:" + str(exc))


def _material_post(pending: Mapping[str, object], post: Mapping[str, object]) -> bool:
    if (post.get("schema") != POST_SCHEMA
            or post.get("actor_character_id") != pending.get("actor_character_id")
            or post.get("date_raw") != pending.get("date_raw")):
        return False
    # The private query validates the current connection's paused frame. Native
    # revisions restart in a new PID; the recorded old revision is provenance,
    # while actor/date, exact hosted identity and debit prove the saved action.
    pre_ids = pending["pre_hosted_activities"]
    post_ids = post["hosted_activities"]
    if (not isinstance(pre_ids, list) or not isinstance(post_ids, list)
            or not isinstance(pending.get("pre_balances"), Mapping)
            or not isinstance(post.get("balances"), Mapping)):
        return False
    old = {row["activity_id"] for row in pre_ids}
    current = {row["activity_id"] for row in post_ids}
    if not old.issubset(current):
        return False
    added = [row for row in post_ids if row["activity_id"] not in old]
    if (len(added) != 1
            or added[0].get("host_character_id") != pending["actor_character_id"]
            or added[0].get("activity_type_key") != "activity_feast"):
        return False
    for key in RESOURCE_KEYS:
        cost = pending["configured_cost_raw"][key]
        before = pending["pre_balances"][key]
        after = post["balances"][key]
        if cost > 0:
            if (before.get("available") is not True
                    or after.get("available") is not True
                    or before.get("raw") - after.get("raw") != cost):
                return False
        elif (before.get("available") is True and after.get("available") is True
              and before.get("raw") != after.get("raw")):
            return False
    return True


def _record_lifecycle_observation(
    state_dir: Path, ledger: Mapping[str, object], resolved: Mapping[str, object],
    post: Mapping[str, object],
) -> dict[str, object]:
    """Retain an explicit terminal result without assigning the Feast a gain."""
    current_outcome = normalize_activity_feast_terminal_outcome_v1(
        post, activity_id=resolved["activity_id"],
        actor_character_id=resolved["actor_character_id"],
    )
    previous = resolved.get("lifecycle")
    outcome = (previous["outcome"]
               if (isinstance(previous, Mapping)
                   and previous.get("terminal_observed") is True
                   and current_outcome["status"] not in _TERMINAL_STATUSES)
               else current_outcome)
    baseline = resolved["post"]["balances"]
    changes = {
        key: (post["balances"][key]["raw"] - baseline[key]["raw"]
              if (baseline[key].get("available") is True
                  and post["balances"][key].get("available") is True)
              else None)
        for key in RESOURCE_KEYS
    }
    lifecycle = {
        "activity_id": resolved["activity_id"],
        "actor_character_id": resolved["actor_character_id"],
        "activity_type_key": "activity_feast",
        "outcome": outcome,
        "latest_identity_observation": current_outcome,
        "terminal_observed": outcome["status"] in _TERMINAL_STATUSES,
        "balances": post["balances"],
        "value_observation": {
            "status": "unobserved", "benefit_verified": False,
            "resource_changes_raw": changes,
            "resource_changes_attributed_to_feast": False,
            "opinion_change_raw": None,
        },
    }
    before_values = resolved["source_pending"].get("pre_outcome_values")
    after_values = post.get("outcome_values")
    before_values = before_values if isinstance(before_values, Mapping) else {}
    after_values = after_values if isinstance(after_values, Mapping) else {}
    changes = {
        key: (after_values[key] - before_values[key]
              if (type(before_values.get(key)) is int
                  and type(after_values.get(key)) is int) else None)
        for key in ("prestige_raw", "stress_points", "reveler_xp_raw")
    }
    before_reveler = before_values.get("reveler_present")
    after_reveler = after_values.get("reveler_present")
    presence_observed = type(before_reveler) is bool and type(after_reveler) is bool
    post_terminal_counters_observed = bool(
        lifecycle["terminal_observed"]
        and post["date_raw"] >= outcome["date_raw"]
        and type(after_values.get("prestige_raw")) is int
        and type(after_values.get("stress_points")) is int
    )
    lifecycle["value_observation"].update({
        "status": "observed_counters" if post_terminal_counters_observed else "unobserved",
        "pre_start_outcome_values": {key: before_values.get(key) for key in _OUTCOME_COUNTER_KEYS},
        "outcome_values": {key: after_values.get(key) for key in _OUTCOME_COUNTER_KEYS},
        "counter_changes": changes,
        "reveler_presence_transition": (
            {"before": before_reveler, "after": after_reveler} if presence_observed else None),
        "counter_values_observed": {key: after_values.get(key) is not None
                                    for key in _OUTCOME_COUNTER_KEYS},
        "post_terminal_counters_observed": post_terminal_counters_observed,
        "counter_changes_attributed_to_feast": False,
        "counter_snapshot_revision": post["snapshot_revision"],
        "counter_date_raw": post["date_raw"],
        "counter_native_provenance": {
            key: post[key] for key in ("exact_ck3_build", "exe_sha256", "queried_snapshot_id")
            if key in post},
    })
    # Completion callbacks, conclusion-event choices, income and other effects
    # are separate sources. These balance differences are observations only.
    updated = {**resolved, "lifecycle": lifecycle}
    _write(state_dir, {**ledger, "resolved": updated})
    return updated


def _terminal_counter_read_pending(resolved: Mapping[str, object]) -> bool:
    """A new-profile receipt needs one independent post-terminal counter read."""
    pending = resolved.get("source_pending")
    lifecycle = resolved.get("lifecycle")
    if not isinstance(pending, Mapping) or not isinstance(lifecycle, Mapping):
        return False
    value = lifecycle.get("value_observation")
    return (isinstance(pending.get("pre_outcome_values"), Mapping)
            and isinstance(value, Mapping)
            and value.get("post_terminal_counters_observed") is not True)


def _lifecycle_result(resolved: Mapping[str, object], *, recorded: bool = False) -> dict[str, object]:
    lifecycle = resolved["lifecycle"]
    outcome = lifecycle["outcome"]
    return {
        "status": "lifecycle_terminal_recorded" if recorded else "lifecycle_observed",
        "activity_id": resolved["activity_id"],
        "actor_character_id": resolved["actor_character_id"],
        "start_postcondition_verified": resolved["postcondition_verified"],
        "lifecycle_status": outcome["status"],
        "lifecycle_terminal_observed": lifecycle["terminal_observed"],
        "lifecycle_completed": outcome["native_completed"],
        "lifecycle_invalidated": outcome["native_invalidated"],
        "value_observation": lifecycle["value_observation"],
        "observation": lifecycle,
    }


def reconcile_feast_start_private_v1(driver: object) -> dict[str, object]:
    """Read a new native poststate; an unresolved intent never resubmits."""
    state_dir = driver.state_dir
    if not isinstance(state_dir, Path):
        raise ValueError("private feast Start requires managed state_dir")
    ledger = read_feast_start_ledger(state_dir)
    pending = ledger["pending"]
    if not isinstance(pending, dict):
        return {"status": "no_pending", "postcondition_verified": False}
    snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or actor.get("character_id") != pending.get("actor_character_id")
            or snapshot.get("paused") is not True):
        return {"status": "pending_other_actor_or_frame", "postcondition_verified": False}
    try:
        post = query_activity_feast_hosted_post_private_v1(
            driver, expected_revision=snapshot["revision"])
    except BridgeUnavailableError as exc:
        return {"status": "pending_post_read_red", "postcondition_verified": False,
                "error": str(exc)}
    if not _material_post(pending, post):
        return {"status": "pending_post_unresolved", "postcondition_verified": False,
                "post": post}
    resolved = {"status": "applied", "postcondition_verified": True,
                "actor_character_id": pending["actor_character_id"],
                "date_raw": post["date_raw"],
                "post_native_revision": post["snapshot_revision"],
                "next_turn_consumed": False,
                "activity_id": next(row["activity_id"] for row in post["hosted_activities"]
                                    if row["activity_id"] not in {
                                        item["activity_id"] for item in pending["pre_hosted_activities"]}),
                "source_pending": pending,
                "native_ack": pending.get("native_ack"),
                "post": post}
    resolved = _record_lifecycle_observation(
        state_dir, {**ledger, "pending": None}, resolved, post)
    return resolved


def reconcile_feast_lifecycle_private_v1(
    driver: object, *, snapshot: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Follow the material Start identity across turns and a restored process.

    The caller owns the existing default-off observation switch. This helper
    performs no submit, does not infer a terminal outcome from absence, and
    continues after the existing following-turn receipt has been consumed.
    """
    state_dir = driver.state_dir
    if not isinstance(state_dir, Path):
        raise ValueError("private feast lifecycle requires managed state_dir")
    ledger = read_feast_start_ledger(state_dir)
    resolved = ledger["resolved"]
    if isinstance(ledger["pending"], dict):
        result = reconcile_feast_start_private_v1(driver)
        if result.get("status") != "applied":
            return {"status": "start_pending", "start_observation": result,
                    "lifecycle_terminal_observed": False}
        return _lifecycle_result(result)
    if not isinstance(resolved, dict):
        return {"status": "no_tracking", "lifecycle_terminal_observed": False}
    if snapshot is None:
        snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or actor.get("character_id") != resolved.get("actor_character_id")
            or snapshot.get("paused") is not True):
        return {"status": "lifecycle_other_actor_or_frame",
                "lifecycle_terminal_observed": False,
                "activity_id": resolved.get("activity_id")}
    lifecycle = resolved.get("lifecycle")
    if (isinstance(lifecycle, Mapping) and lifecycle.get("terminal_observed") is True
            and not _terminal_counter_read_pending(resolved)):
        # The exact retained terminal source survives subsequent object release
        # and cold restoration. It is a historical observation, not a new read.
        return _lifecycle_result(resolved, recorded=True)
    try:
        post = query_activity_feast_hosted_post_private_v1(
            driver, expected_revision=snapshot["revision"])
    except BridgeUnavailableError as exc:
        if isinstance(lifecycle, Mapping) and lifecycle.get("terminal_observed") is True:
            return {**_lifecycle_result(resolved, recorded=True),
                    "counter_read_status": "post_read_red", "error": str(exc)}
        return {"status": "lifecycle_post_read_red",
                "lifecycle_terminal_observed": False,
                "activity_id": resolved.get("activity_id"), "error": str(exc)}
    resolved = _record_lifecycle_observation(state_dir, ledger, resolved, post)
    return _lifecycle_result(resolved)


def read_feast_start_resolved_private_v1(driver: object) -> dict[str, object]:
    """Read the recorded feast identity before consuming a restored intent."""
    ledger = read_feast_start_ledger(driver.state_dir)
    resolved = ledger["resolved"]
    if not isinstance(resolved, dict):
        return {"status": "no_resolved", "postcondition_verified": False}
    snapshot = driver.take_snapshot()
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or actor.get("character_id") != resolved.get("actor_character_id")
            or snapshot.get("paused") is not True):
        return {"status": "resolved_other_actor_or_frame", "postcondition_verified": False}
    lifecycle = resolved.get("lifecycle")
    if (isinstance(lifecycle, Mapping) and lifecycle.get("terminal_observed") is True
            and not _terminal_counter_read_pending(resolved)):
        return {"status": "already_applied", "postcondition_verified": True,
                "restored_activity_observed": False,
                "lifecycle_observation": _lifecycle_result(resolved, recorded=True),
                "resolved": resolved}
    try:
        post = query_activity_feast_hosted_post_private_v1(
            driver, expected_revision=snapshot["revision"])
    except BridgeUnavailableError as exc:
        if isinstance(lifecycle, Mapping) and lifecycle.get("terminal_observed") is True:
            return {"status": "already_applied", "postcondition_verified": True,
                    "restored_activity_observed": False,
                    "lifecycle_observation": _lifecycle_result(resolved, recorded=True),
                    "counter_read_status": "post_read_red", "error": str(exc),
                    "resolved": resolved}
        return {"status": "resolved_post_read_red", "postcondition_verified": False,
                "error": str(exc)}
    activity_id = resolved.get("activity_id")
    if (not (isinstance(lifecycle, Mapping) and lifecycle.get("terminal_observed") is True)
            and (type(activity_id) is not int or not any(
            row["activity_id"] == activity_id
            and row["host_character_id"] == resolved["actor_character_id"]
            and row["activity_type_key"] == "activity_feast"
            for row in post["hosted_activities"]))):
        return {"status": "resolved_activity_unobserved", "postcondition_verified": False,
                "post": post, "resolved": resolved}
    resolved = _record_lifecycle_observation(driver.state_dir, ledger, resolved, post)
    return {"status": "already_applied", "postcondition_verified": True,
            "restored_activity_observed": True, "restored_post": post,
            "lifecycle_observation": _lifecycle_result(resolved),
            "resolved": resolved}


def consume_feast_start_private_v1(
    driver: object, *, inputs: Mapping[str, object],
    guest: Mapping[str, object] | None = None,
    budget: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Use only qualified sources; persist an intent before one native submit."""
    state_dir = driver.state_dir
    if not isinstance(state_dir, Path):
        raise ValueError("private feast Start requires managed state_dir")
    ledger = read_feast_start_ledger(state_dir)
    if isinstance(ledger["pending"], dict):
        return reconcile_feast_start_private_v1(driver)
    if isinstance(ledger["resolved"], dict):
        return read_feast_start_resolved_private_v1(driver)
    decision = assess_feast_start_private_v1(inputs, guest=guest, budget=budget)
    if decision["decision"] != "start":
        return {**decision, "status": decision["status"]}
    reserves = dict(zip(RESOURCE_KEYS, decision["submit_reserve_raw"]))
    pending = {
        "intent_id": "feast-start-" + uuid.uuid4().hex,
        "actor_character_id": inputs["actor_character_id"],
        "native_revision": inputs["snapshot_revision"],
        "date_raw": inputs["date_raw"],
        "configured_cost_raw": {
            key: inputs["resources"][key]["configured_cost_raw"]
            for key in RESOURCE_KEYS},
        "pre_balances": inputs["balances"],
        "pre_hosted_activities": inputs["hosted_activities"],
        "pre_outcome_values": inputs.get("outcome_values"),
        "ordinary_guest_route": inputs.get("ordinary_guest_route"),
        "reserved_raw": reserves, "stage": "submission_unresolved",
    }
    _write(state_dir, {**ledger, "pending": pending})
    try:
        ack = submit_activity_feast_stage5_start_private_v1(
            driver, inputs=inputs, reserve_raw=reserves)
    except BridgeUnavailableError as exc:
        return {"status": "submission_unresolved", "postcondition_verified": False,
                "error": str(exc), "pending": pending}
    pending = {**pending, "stage": "post_pending", "native_ack": ack}
    _write(state_dir, {**ledger, "pending": pending})
    return reconcile_feast_start_private_v1(driver)


def consume_feast_start_following_turn(state_dir: Path,
                                       snapshot: Mapping[str, object]) -> dict[str, object] | None:
    ledger = read_feast_start_ledger(state_dir)
    resolved = ledger["resolved"]
    if not isinstance(resolved, dict) or resolved.get("next_turn_consumed") is True:
        return None
    actor = snapshot.get("played_character")
    if (not isinstance(actor, Mapping)
            or actor.get("character_id") != resolved.get("actor_character_id")
            or snapshot.get("paused") is not True
            or type(snapshot.get("date_raw")) is not int
            or snapshot["date_raw"] <= resolved["date_raw"]):
        return None
    resolved = {**resolved, "next_turn_consumed": True,
                "following_native_revision": snapshot["native_revision"],
                "following_date_raw": snapshot["date_raw"]}
    _write(state_dir, {**ledger, "resolved": resolved})
    return resolved

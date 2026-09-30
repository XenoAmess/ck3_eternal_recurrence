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
from .environment import write_json_atomic


LEDGER_FILE = "activity-feast-stage5-start-private-v1.json"
LEDGER_SCHEMA = "xar.ck3.activity-feast-stage5-start-private.v1"


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
    raw = [balances[key]["raw"] if available[i] else 0
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
            or post.get("date_raw") != pending.get("date_raw")
            or post.get("snapshot_revision", 0) < pending.get("native_revision", 0)):
        return False
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
    _write(state_dir, {**ledger, "pending": None, "resolved": resolved})
    return resolved


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
    try:
        post = query_activity_feast_hosted_post_private_v1(
            driver, expected_revision=snapshot["revision"])
    except BridgeUnavailableError as exc:
        return {"status": "resolved_post_read_red", "postcondition_verified": False,
                "error": str(exc)}
    activity_id = resolved.get("activity_id")
    if (type(activity_id) is not int or not any(
            row["activity_id"] == activity_id
            and row["host_character_id"] == resolved["actor_character_id"]
            and row["activity_type_key"] == "activity_feast"
            for row in post["hosted_activities"])):
        return {"status": "resolved_activity_unobserved", "postcondition_verified": False,
                "post": post, "resolved": resolved}
    return {"status": "already_applied", "postcondition_verified": True,
            "restored_activity_observed": True, "restored_post": post,
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

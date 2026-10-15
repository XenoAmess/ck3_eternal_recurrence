"""Low-frequency ordinary Sway work from existing paused inputs.

This counter-policy fairly nominates one observed direct landed vassal in the
native frontier order. It neither computes native AI rank nor sends an action.
The existing formal consumer owns native legality, opinion<=50, durable intent,
receipt and independent active-instance verification. No signal provider is
invented: only an observed frontier, actor, or retained terminal change resets cooldown.
"""

from __future__ import annotations

from collections.abc import Mapping

RAW_PER_DAY = 24
MONTH_RAW = 30 * RAW_PER_DAY


def _id(value: object) -> bool:
    return type(value) is int and 0 < value <= 0xFFFFFFFF


def _state(value: Mapping[str, object] | None, actor: int) -> dict[str, object]:
    if not isinstance(value, Mapping) or value.get("actor_character_id") != actor:
        return {
            "actor_character_id": actor, "last_target_character_id": None,
            "no_operation_count": 0, "last_check_date_raw": None,
            "next_check_date_raw": None, "frontier_membership": None,
            "last_observation_attempt_action_id": None, "last_terminal_action_id": None,
            "last_job_kind": None,
        }
    result = dict(value)
    members = result.get("frontier_membership")
    if isinstance(members, list):
        result["frontier_membership"] = list(members)
    return result


def _due(state: Mapping[str, object], date: int) -> bool:
    previous = state.get("last_check_date_raw")
    if type(previous) is int and date <= previous:
        return False
    deadline = state.get("next_check_date_raw")
    return type(deadline) is not int or date >= deadline


def plan_ordinary_sway_schedule_v1(
    snapshot: Mapping[str, object], *,
    selected_step: str | None,
    root: Mapping[str, object] | None = None,
    ledger: Mapping[str, object] | None = None,
    state: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Plan optional work; every none result leaves the ordinary turn runnable."""
    unchanged = dict(state) if isinstance(state, Mapping) else {}
    if selected_step != "life-advance":
        return {"job": None, "reason": "preserve_selected_step", "state": unchanged}
    played = snapshot.get("played_character")
    date = snapshot.get("date_raw")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(played, Mapping) or played.get("alive") is not True
            or not _id(played.get("character_id")) or type(date) is not int
            or type(snapshot.get("native_revision")) is not int
            or snapshot["native_revision"] <= 0):
        return {"job": None, "reason": "frame_unavailable", "state": unchanged}
    context = snapshot.get("active_context")
    if (not isinstance(context, Mapping) or context.get("active_event") is not None
            or context.get("pending_character_interaction") is not None):
        return {"job": None, "reason": "preserve_mandatory_context", "state": unchanged}
    actor = played["character_id"]
    current = _state(state, actor)
    pending = ledger.get("pending") if isinstance(ledger, Mapping) else None
    resolved = ledger.get("resolved") if isinstance(ledger, Mapping) else None
    if isinstance(pending, Mapping):
        if pending.get("actor_character_id") != actor or not _id(pending.get("target_character_id")):
            return {"job": None, "reason": "unresolved_other_actor", "state": current}
        if current.get("last_job_kind") == "reconcile_pending" and not _due(current, date):
            return {"job": None, "reason": "pending_read_not_due", "state": current}
        return {
            "job": "reconcile_pending", "target_character_id": pending["target_character_id"],
            "action_id": pending.get("action_id"), "submit_allowed": False,
            "reason": "existing_pending_read_only", "state": current,
        }
    if (isinstance(resolved, Mapping) and resolved.get("status") == "applied"
            and resolved.get("postcondition_verified") is True
            and resolved.get("actor_character_id") == actor):
        terminal = resolved.get("terminal_intervention")
        terminal_observed = (isinstance(terminal, Mapping)
                             and terminal.get("instance_terminal_outcome_observed") is True)
        if not terminal_observed:
            target = resolved.get("target_character_id")
            if not _id(target):
                return {"job": None, "reason": "resolved_identity_unavailable", "state": current}
            new_action = current.get("last_observation_attempt_action_id") != resolved.get("action_id")
            if not new_action and not _due(current, date):
                return {"job": None, "reason": "monthly_observation_not_due", "state": current}
            return {
                "job": "observe_applied", "target_character_id": target,
                "action_id": resolved.get("action_id"), "submit_allowed": False,
                "reason": "new_identity_or_monthly_observation", "state": current,
            }
        if current.get("last_terminal_action_id") != resolved.get("action_id"):
            # This is an existing observed terminal fact, not a new signal API.
            current.update(last_terminal_action_id=resolved.get("action_id"),
                           no_operation_count=0, next_check_date_raw=None)
    if (not isinstance(root, Mapping) or root.get("status") != "available"
            or root.get("player_character_id") != actor
            or root.get("player_character_alive") is not True
            or root.get("snapshot_revision") != snapshot["native_revision"]
            or root.get("date_raw") != date):
        return {"job": None, "reason": "same_frame_root_unavailable", "state": current}
    targets = root.get("direct_landed_vassal_character_ids")
    if (not isinstance(targets, list) or any(not _id(x) or x == actor for x in targets)
            or len(set(targets)) != len(targets)):
        return {"job": None, "reason": "frontier_unavailable", "state": current}
    # Sorting is only a membership fingerprint. Target order remains native.
    membership = sorted(targets)
    if current.get("frontier_membership") != membership:
        current.update(frontier_membership=membership, no_operation_count=0,
                       next_check_date_raw=None)
    if not _due(current, date):
        return {"job": None, "reason": "opportunity_check_not_due", "state": current}
    if not targets:
        return {"job": "complete_no_relation", "reason": "observed_empty_frontier",
                "submit_allowed": False, "state": current}
    previous_target = current.get("last_target_character_id")
    index = targets.index(previous_target) + 1 if previous_target in targets else 0
    target = targets[index % len(targets)]
    return {
        "job": "query_selected_target", "target_character_id": target,
        "submit_allowed": False, "reason": "round_robin_direct_landed_vassal",
        "native_ai_rank_claimed": False, "state": current,
    }


def complete_ordinary_sway_check_v1(
    state: Mapping[str, object], *, date_raw: int, job_kind: str,
    outcome: str, target_character_id: int | None = None,
    action_id: str | None = None,
) -> dict[str, object]:
    """Record an actual completed check, never a plan/ACK as an applied action.

    no_operation requires complete current native terms or observed empty Root.
    pending/observed/unavailable never increment the true no-operation streak.
    Applied means the original consumer independently verified the new instance.
    """
    if type(date_raw) is not int:
        raise ValueError("date_raw must be an actual integer game date")
    if outcome not in {"no_operation", "applied", "pending", "observed", "unavailable"}:
        raise ValueError("unknown Sway check outcome")
    result = dict(state)
    previous = result.get("last_check_date_raw")
    if type(previous) is int and date_raw < previous:
        return result
    if (type(previous) is int and date_raw == previous
            and job_kind not in {"observe_applied", "reconcile_pending"}):
        return result
    count = result.get("no_operation_count", 0)
    if type(count) is not int or not 0 <= count <= 2:
        raise ValueError("Sway no-operation state is invalid")
    if outcome == "no_operation":
        count = min(2, count + 1)
        delay = MONTH_RAW if count == 2 else RAW_PER_DAY
    elif outcome == "applied":
        count, delay = 0, MONTH_RAW
    else:
        delay = MONTH_RAW
    if outcome in {"no_operation", "applied"} and target_character_id is not None:
        if not _id(target_character_id):
            raise ValueError("target must be an actual full character ID")
        result["last_target_character_id"] = target_character_id
    if job_kind == "observe_applied" and outcome in {"observed", "unavailable"}:
        result["last_observation_attempt_action_id"] = action_id
    result.update(
        no_operation_count=count, last_check_date_raw=date_raw,
        next_check_date_raw=date_raw + delay, last_job_kind=job_kind,
    )
    return result

"""Bounded feedback from a normal completed faction query, with zero reads.

Service owns the original planning snapshot reference and the existing complete
planning-source-frame. NativeDriver has already checked the readonly query's
before/after frame. No snapshot, history search, retry, command or file I/O is
performed here. Prospective source only; current Native27 is not adopted here.
"""
from collections.abc import Mapping
from copy import deepcopy
from contextvars import ContextVar
from threading import Lock

from ..realm_membership_feedback_v1 import project_realm_membership_feedback_v1
from ..campaign_score_existing_inputs_v1 import _frame_reason

QUERY = "query-player-faction-alerts-v1"
_PLANNING = ContextVar("realm_membership_private_planning_v1", default=None)


def _guard(service):
    # One private execution slot, not a history or a public identity. setdefault
    # picks one lock if two callers first enter concurrently under CPython.
    state = vars(service)
    lock = state.get("_realm_membership_guard_v1")
    return lock if lock is not None else state.setdefault("_realm_membership_guard_v1", Lock())


def begin_realm_membership_plan_v1(service):
    """Invalidate a former plan before the next planning attempt can fail."""
    with _guard(service):
        epoch = getattr(service, "_realm_membership_plan_epoch_v1", 0) + 1
        service._realm_membership_plan_epoch_v1 = epoch
        service._realm_membership_query_slot_v1 = None
        return epoch


def enter_realm_membership_planning_v1(service):
    """Private synchronous plan scope; no method signature or public marker."""
    epoch = begin_realm_membership_plan_v1(service)
    return epoch, _PLANNING.set((service, epoch))


def leave_realm_membership_planning_v1(token):
    _PLANNING.reset(token)


def bind_current_realm_membership_plan_v1(service, planned, snapshot):
    current = _PLANNING.get()
    if current is None or current[0] is not service:
        return False
    return bind_realm_membership_plan_v1(service, current[1], planned, snapshot)


def bind_realm_membership_plan_v1(service, epoch, planned, snapshot):
    """Privately retain the original snapshot for this exact faction plan only."""
    with _guard(service):
        if epoch != getattr(service, "_realm_membership_plan_epoch_v1", None):
            return False
        if epoch == getattr(service, "_realm_membership_bound_epoch_v1", None):
            return False
        service._realm_membership_bound_epoch_v1 = epoch
        service._realm_membership_query_slot_v1 = None
        plan, frame = planned.get("plan"), planned.get("planning_source_frame")
        if (not isinstance(plan, Mapping) or plan.get("selected_step") != QUERY
                or not isinstance(snapshot, Mapping) or _frame_reason(snapshot, frame) is not None):
            return False
        service._realm_membership_query_slot_v1 = {"plan": planned, "epoch": epoch,
            "source_frame": deepcopy(frame), "snapshot": snapshot, "finalized": False}
        return True


def finalize_realm_membership_plan_v1(service, epoch, public_plan):
    """Bind the actual detached plan after public deepcopy and priority routing."""
    with _guard(service):
        slot = getattr(service, "_realm_membership_query_slot_v1", None)
        if not (isinstance(slot, Mapping) and slot["epoch"] == epoch
                and epoch == getattr(service, "_realm_membership_plan_epoch_v1", None)):
            return False
        plan = public_plan.get("plan")
        if (slot["finalized"] or not isinstance(plan, Mapping) or plan.get("selected_step") != QUERY
                or public_plan.get("planning_source_frame") != slot["source_frame"]):
            service._realm_membership_query_slot_v1 = None
            return False
        slot["plan"] = public_plan
        slot["finalized"] = True
        return True


def cancel_realm_membership_plan_v1(service, planned=None, *, epoch=None):
    """Release a failed query's original snapshot without cancelling a newer plan."""
    with _guard(service):
        slot = getattr(service, "_realm_membership_query_slot_v1", None)
        if isinstance(slot, Mapping) and (
                planned is not None and slot.get("plan") is planned
                or epoch is not None and slot.get("epoch") == epoch):
            service._realm_membership_query_slot_v1 = None


def observe_realm_membership_after_query_v1(service, planned, outcome):
    """Retain one qualified observation only after the original query completed."""
    if outcome.get("selected_step") != QUERY or outcome.get("status") != "executed":
        cancel_realm_membership_plan_v1(service, planned)
        return outcome
    with _guard(service):
        slot = getattr(service, "_realm_membership_query_slot_v1", None)
        valid = (isinstance(slot, Mapping) and slot.get("plan") is planned
            and slot.get("finalized") is True
            and slot["epoch"] == getattr(service, "_realm_membership_plan_epoch_v1", None)
            and slot["source_frame"] == planned.get("planning_source_frame"))
        if isinstance(slot, Mapping) and slot.get("plan") is planned:
            service._realm_membership_query_slot_v1 = None  # one-shot, even on unknown
        if not valid:
            feedback = {"status": "unavailable", "observation": None, "difference": None,
                "unavailable_reason": "original_query_plan_slot_unavailable", "new_RPC_calls": 0}
        else:
            feedback = project_realm_membership_feedback_v1(slot["snapshot"],
                faction_result=outcome.get("result"), source_frame=slot["source_frame"],
                previous=getattr(service, "_realm_membership_observation_v1", None))
        if feedback["status"] == "available":
            service._realm_membership_observation_v1 = feedback["observation"]
            service._realm_membership_feedback_v1 = feedback
    # Unknown cannot erase the last qualified observation or replay the query.
    return {**outcome, "realm_membership_feedback_v1": feedback}


def realm_membership_summary_for_plan_v1(service, current_source_frame):
    """Expose a small dated planner fact, never a cached set as current state."""
    with _guard(service):
        feedback = getattr(service, "_realm_membership_feedback_v1", None)
        # Retained feedback is replaced, never mutated; use the stable reference
        # outside the guard and expose only the bounded summary below.
    if not isinstance(feedback, Mapping) or feedback.get("status") != "available":
        return {"status": "unavailable", "current_realm_county_count": None,
                "loss_observed": None, "unavailable_reason": "no_qualified_realm_observation"}
    observed, delta = feedback["observation"], feedback.get("difference")
    source = observed["source_frame"]
    same_frame = isinstance(current_source_frame, Mapping) and dict(current_source_frame) == source
    count = len(observed["component"]["county_title_ids"])
    comparable = isinstance(delta, Mapping) and delta.get("status") == "available"
    lost, gained = (delta["lost_county_title_ids"], delta["gained_county_title_ids"]) if comparable else (None, None)
    return {"status": "current" if same_frame else "historical",
            "current_realm_county_count": count if same_frame else None,
            "last_observed_realm_county_count": count,
            "source_frame": deepcopy(source), "query_sequence": observed["query_sequence"],
            "loss_observed": bool(lost) if comparable else None,
            "lost_county_count": len(lost) if comparable else None,
            "gained_county_count": len(gained) if comparable else None,
            "lost_county_title_ids_first8": list(lost[:8]) if comparable else None,
            "loss_list_truncated": len(lost) > 8 if comparable else False,
            "before_source_frame": deepcopy(delta.get("before_source_frame")) if comparable else None,
            "cause": None, "new_RPC_calls": 0}

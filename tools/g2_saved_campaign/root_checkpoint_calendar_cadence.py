"""Game-date checkpoint cadence; queries never advance the save clock."""

from collections.abc import Mapping

try:
    from .root_checkpoint_cadence import (
        checkpoint_cycle_may_change_game,
        checkpoint_step_is_readonly,
    )
except ImportError:  # The frozen queue loads these two standalone helper leaves.
    from root_checkpoint_cadence import (
        checkpoint_cycle_may_change_game,
        checkpoint_step_is_readonly,
    )


PEACE_DAYS = 90
WAR_DAYS = 90
STATE_KEY = "checkpoint_calendar_v1"
MATERIAL_FLAGS = (
    "lifestyle_material_verified", "council_material_verified",
    "construction_start_verified", "construction_completion_verified",
    "crown_material_verified", "existing_typed_material_verified",
)


def _scope(frame):
    return {key: frame.get(key) for key in ("actor_character_id", "episode_run_id")}


def _wars(value):
    if not isinstance(value, list):
        return None
    ids = [row.get("war_id") for row in value if isinstance(row, Mapping)]
    if (len(ids) != len(value) or any(type(wid) is not int or wid <= 0 for wid in ids)
            or len(set(ids)) != len(ids)):
        return None
    return sorted(ids)


def checkpoint_context_from_auto(body):
    """Project only an already accepted paused advancement, adding no query."""
    try:
        source, result = body["planning_source_frame"], body["result"]
        start, end = result["starting_date_raw"], result["ending_date_raw"]
        before, after = result["war_progress_before"], result["war_progress_after"]
        first, last = _wars(before.get("wars")), _wars(after.get("wars"))
        if (body["status"] != "executed" or body["selected_step"] != "life-advance"
                or result["step"] != "life-advance" or result["backend_id"] != "native-headless"
                or result["source"] != "native-composite" or result["paused"] is not True
                or result["final_screen"] != "map_hud" or source["status"] != "complete"
                or type(start) is not int or type(end) is not int or end < start
                or end - start != result["elapsed_days"] * 24
                or source["date_raw"] != start or before["date_raw"] != start
                or after["date_raw"] != end or first is None or last is None):
            return None
        return {
            "schema": "g2.queue.calendar-checkpoint-context/v1",
            "before": {"date_raw": start, **_scope(source)},
            "after": {"date_raw": end, **_scope(source),
                      "snapshot_id": result["snapshot_id"], "revision": result["revision"]},
            "war_ids": last,
            "war_ended": bool(set(first) - set(last)),
        }
    except (KeyError, TypeError, ValueError):
        return None


def _context(pending, after):
    value = pending.get("checkpoint_context")
    if not isinstance(value, Mapping) or value.get("schema") != "g2.queue.calendar-checkpoint-context/v1":
        return None
    before, end = value.get("before"), value.get("after")
    if not isinstance(before, Mapping) or not isinstance(end, Mapping):
        return None
    if (any(before.get(key) != pending["before"].get(key) for key in before)
            or any(end.get(key) != after.get(key) for key in end)):
        return None
    return value


def checkpoint_saved(state, checkpoint):
    """Called only by the queue after its existing actual SAVE validation."""
    current = state["before"]
    if (checkpoint.get("status") != "saved"
            or type(checkpoint.get("date_raw")) is not int
            or checkpoint["date_raw"] != current["date_raw"]
            or checkpoint.get("episode_run_id") != current["episode_run_id"]):
        raise ValueError("calendar checkpoint must bind the actual saved frame")
    # The queue already validates the Driver/SAVE origin binding. A campaign's
    # episode origin can differ from its currently played natural successor.
    previous = state.get(STATE_KEY) or {}
    state[STATE_KEY] = {"last_saved_date_raw": checkpoint["date_raw"],
                        **_scope(current), "war_ids": previous.get("war_ids")}
    state["checkpoint_dirty_since_save"] = False
    state["checkpoint_due_after_readonly_chain"] = False


def checkpoint_after_settled_cycle(state, pending, after):
    was_dirty = state.get("checkpoint_dirty_since_save", False)
    dirty = bool(was_dirty or checkpoint_cycle_may_change_game(pending, after))
    clock = state.get(STATE_KEY)
    if not isinstance(clock, dict) and not was_dirty:
        clock = {"last_saved_date_raw": pending["before"]["date_raw"],
                 **_scope(pending["before"]), "war_ids": None}
        state[STATE_KEY] = clock
    bound = (isinstance(clock, dict) and type(clock.get("last_saved_date_raw")) is int
             and all(clock.get(key) == value for key, value in _scope(after).items())
             and after["date_raw"] >= clock["last_saved_date_raw"])
    context = _context(pending, after)
    ended_since_last_frame = False
    if bound and context is not None:
        ended_since_last_frame = bool(set(clock.get("war_ids") or ()) - set(context["war_ids"]))
        clock["war_ids"] = list(context["war_ids"])
    regime = ("unknown" if not bound or clock.get("war_ids") is None
              else "war" if clock["war_ids"] else "peace")
    interval = PEACE_DAYS if regime == "peace" else WAR_DAYS
    elapsed = (after["date_raw"] - clock["last_saved_date_raw"]) / 24 if bound else None
    observation = pending.get("observation") or {}
    critical = any(observation.get(key) is True for key in MATERIAL_FLAGS)
    critical = bool(critical or ended_since_last_frame
                    or context is not None and context["war_ended"])
    calendar_due = bound and elapsed >= interval
    # An old dirty state without a saved date needs one reconciliation SAVE;
    # it never installs a second recurring schedule based on query counts.
    fallback_due = not bound and dirty
    carried = was_dirty and state.get("checkpoint_due_after_readonly_chain", False)
    due_pending = bool(dirty and (calendar_due or fallback_due or carried or critical))
    readonly = (checkpoint_step_is_readonly(pending.get("selected_step"))
                and not checkpoint_cycle_may_change_game(pending, after))
    due = bool(due_pending and not readonly and not state.get("terminal"))
    state["checkpoint_dirty_since_save"] = dirty
    state["checkpoint_due_after_readonly_chain"] = due_pending
    state["checkpoint_last_decision"] = {
        "reason": ("critical_outcome_checkpoint" if due and critical else
                   "calendar_checkpoint_due" if due else
                   "dirty_checkpoint_due_deferred_readonly_chain" if due_pending and readonly else
                   "unchanged_readonly_evidence_chain" if not dirty else
                   "calendar_checkpoint_not_due"),
        "regime": regime, "interval_game_days": interval if bound else None,
        "interval_settled_cycles": None,
        "elapsed_since_actual_save_days": elapsed, "dirty": dirty, "due": due,
    }
    return due

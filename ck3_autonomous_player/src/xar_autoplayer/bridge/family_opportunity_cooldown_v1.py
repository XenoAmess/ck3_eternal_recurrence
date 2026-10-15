"""Pace only a fully observed, repeatedly empty ordinary family opportunity.

This is a deliberate 30-game-day polling interval for a low-priority read. It
never asserts that a different date's family facts are unchanged.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4


SCHEMA = "xar.ck3.family-opportunity-cooldown/v1"
FILENAME = "family-opportunity-cooldown-v1.json"
PERIOD_RAW = 30 * 24
HELD_REASONS = [
    "actual_pair_not_ready", "native_final_can_send_not_true",
    "native_outcome_not_marriage",
]


def _owner(frame: dict) -> tuple[int, str, int]:
    actor, episode, date = (frame.get("actor_character_id"),
                            frame.get("episode_run_id"), frame.get("date_raw"))
    if (type(actor) is not int or actor <= 0 or not isinstance(episode, str)
            or not episode or type(date) is not int or date <= 0):
        raise ValueError("family cooldown requires a bound actor, episode and date")
    return actor, episode, date


def _empty(frame: dict) -> dict:
    actor, episode, _ = _owner(frame)
    return {"schema": SCHEMA, "actor_character_id": actor,
            "episode_run_id": episode, "consecutive_noop_dates": 0,
            "cooldown_until_date_raw": None, "last_noop_date_raw": None,
            "last_observed_end_date_raw": None,
            "last_query_identity": None, "last_pair": None}


def _file(state_dir) -> Path:
    return Path(state_dir) / FILENAME


def _read(state_dir, frame: dict) -> dict:
    path = _file(state_dir)
    if not path.exists():
        return _empty(frame)
    state = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(state, dict) or state.get("schema") != SCHEMA
            or type(state.get("consecutive_noop_dates")) is not int
            or state["consecutive_noop_dates"] not in (0, 1)
            or state.get("cooldown_until_date_raw") is not None
            and type(state["cooldown_until_date_raw"]) is not int
            or state.get("last_noop_date_raw") is not None
            and type(state["last_noop_date_raw"]) is not int
            or state.get("last_observed_end_date_raw") is not None
            and type(state["last_observed_end_date_raw"]) is not int):
        raise ValueError("family cooldown state is malformed")
    actor, episode, date = _owner(frame)
    if (state.get("actor_character_id"), state.get("episode_run_id")) != (actor, episode):
        cleared = _empty(frame)
        _write(state_dir, cleared)
        return cleared
    last_date = state.get("last_observed_end_date_raw")
    if type(last_date) is int and date < last_date:
        # A cold load rolled back before the saved observation. Never carry a
        # future query's conclusion across that rollback.
        cleared = _empty(frame)
        _write(state_dir, cleared)
        return cleared
    return state


def _write(state_dir, state: dict) -> None:
    path = _file(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def view(state_dir, frame: dict) -> dict:
    state = _read(state_dir, frame)
    date = _owner(frame)[2]
    until = state["cooldown_until_date_raw"]
    active = type(until) is int and date < until
    return {"schema": SCHEMA, "status": "active" if active else "inactive",
            "actor_character_id": state["actor_character_id"],
            "episode_run_id": state["episode_run_id"],
            "consecutive_noop_dates": state["consecutive_noop_dates"],
            "cooldown_until_date_raw": until,
            "remaining_days": (until - date + 23) // 24 if active else 0,
            "last_pair": state["last_pair"]}


def _known_noop(plan: dict, frame: dict) -> tuple[list[int], list[int]] | None:
    relation = plan.get("current_betrothal_relationship")
    choice = plan.get("current_betrothal_choice")
    education = plan.get("family_education_needs")
    focus = plan.get("family_child_education_focus")
    if not all(isinstance(row, dict) for row in (relation, choice, education, focus)):
        return None
    heir, partner = relation.get("heir_character_id"), relation.get("betrothed_character_id")
    sequence = relation.get("root_query_sequence")
    if not (plan.get("current_betrothal_fulfillment") is True
            and plan.get("current_betrothal_status") == "held"
            and choice.get("status") == "held"
            and choice.get("selected_step") is None
            and choice.get("reasons") == HELD_REASONS
            and relation.get("schema") == "xar.ck3.current-first-heir-relationship.v1"
            and relation.get("status") == "available"
            and relation.get("read_only") is True
            and relation.get("advertised") is False
            and relation.get("bilateral_verified") is True
            and relation.get("native_revision") == frame.get("native_revision")
            and type(sequence) is int and sequence > 0
            and type(heir) is int and heir > 0
            and type(partner) is int and partner > 0
            and relation.get("primary_spouse_character_id") is None
            and relation.get("spouse_character_ids") == []
            and education.get("roster_complete") is True
            and education.get("living_child_classification_complete") is True
            and education.get("known_empty") is True
            and education.get("rows") == []
            and focus.get("observations") == []
            and focus.get("pending") is None
            and focus.get("receipt") is None):
        return None
    return [heir, partner], [frame["native_revision"], sequence]


def observe_after_turn(state_dir, frame: dict, plan: dict, outcome: dict) -> dict:
    """Count one complete no-op date, or reset after an actual family result."""
    state = _read(state_dir, frame)
    result = outcome.get("result") if isinstance(outcome, dict) else None
    if (isinstance(result, dict) and outcome.get("status") == "executed"
            and (outcome.get("selected_step")
                 == "query-observed-first-heir-marriage-result-v1-private"
                 and result.get("status") in {"marriage", "betrothal"}
                 and result.get("material_result") is True
                 or outcome.get("selected_step")
                 == "private-query-child-education-focus-receipt-v1"
                 and result.get("status") == "observed_applied"
                 and result.get("observed_applied") is True)):
        state = _empty(frame)
        _write(state_dir, state)
        return view(state_dir, frame)
    if not (isinstance(plan, dict) and isinstance(result, dict)
            and outcome.get("status") == "executed"
            and outcome.get("selected_step") == "life-advance"
            and result.get("step") == "life-advance"
            and result.get("progress_status") == "postcondition"
            and result.get("paused") is True
            and result.get("starting_date_raw") == frame.get("date_raw")
            and type(result.get("ending_date_raw")) is int
            and result["ending_date_raw"] > frame["date_raw"]
            and result.get("active_event") is None
            and result.get("pending_character_interaction") is None):
        return view(state_dir, frame)
    ending_frame = {**frame, "date_raw": result["ending_date_raw"]}
    if state.get("cooldown_until_date_raw") is not None and (
            frame["date_raw"] < state["cooldown_until_date_raw"]):
        # A bypassed critical planner may still perform a full family read.
        # That read is not a new ordinary opportunity round during the CD.
        return view(state_dir, ending_frame)
    observed = (_known_noop(plan, frame)
                if plan.get("_family_cooldown_ordinary_review_v1") is True
                else None)
    if observed is None:
        if plan.get("current_betrothal_relationship") is not None:
            state["consecutive_noop_dates"] = 0
            _write(state_dir, state)
        return view(state_dir, ending_frame)
    pair, query_identity = observed
    if (state.get("last_noop_date_raw") == frame["date_raw"]
            or state.get("last_query_identity") == query_identity):
        return view(state_dir, ending_frame)
    state["consecutive_noop_dates"] = (
        state["consecutive_noop_dates"] + 1
        if state.get("last_pair") == pair else 1)
    state["last_pair"] = pair
    state["last_noop_date_raw"] = frame["date_raw"]
    state["last_observed_end_date_raw"] = result["ending_date_raw"]
    state["last_query_identity"] = query_identity
    if state["consecutive_noop_dates"] >= 2:
        state["consecutive_noop_dates"] = 0
        state["cooldown_until_date_raw"] = result["ending_date_raw"] + PERIOD_RAW
    _write(state_dir, state)
    return view(state_dir, ending_frame)

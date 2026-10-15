"""Persist the bounded pause after two completed, unproductive war-query rounds.

Only an actual completed query followed by a verified date advance at peace
counts.  The native declaration continuity remains the authority for war credit.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4


SCHEMA = "xar.ck3.declaration-opportunity-cooldown/v1"
FILENAME = "declaration-opportunity-cooldown-v1.json"
COOLDOWN_RAW_DAYS = 30 * 24


def _owner(frame: dict) -> tuple[int, str, int] | None:
    actor = frame.get("actor_character_id")
    episode = frame.get("episode_run_id")
    date = frame.get("date_raw")
    if (type(actor) is int and actor > 0 and isinstance(episode, str)
            and episode and type(date) is int and date > 0):
        return actor, episode, date
    return None


def _new(frame: dict) -> dict:
    owner = _owner(frame)
    if owner is None:
        raise ValueError("declaration cooldown requires a bound actor, episode and date")
    return {
        "schema": SCHEMA,
        "actor_character_id": owner[0],
        "episode_run_id": owner[1],
        "consecutive_no_war_rounds": 0,
        "cooldown_until_date_raw": None,
        "pending_query": None,
        "last_closed_query_sequence": None,
        "last_confirmed_war_id": None,
    }


def _path(state_dir) -> Path:
    if state_dir is None:
        raise ValueError("declaration cooldown requires a persistent state directory")
    return Path(state_dir) / FILENAME


def _load(state_dir, frame: dict) -> dict:
    path = _path(state_dir)
    if not path.exists():
        return _new(frame)
    state = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(state, dict) or state.get("schema") != SCHEMA:
        raise ValueError("declaration cooldown state has an unknown schema")
    if (type(state.get("consecutive_no_war_rounds")) is not int
            or state["consecutive_no_war_rounds"] not in (0, 1, 2)
            or state.get("cooldown_until_date_raw") is not None
            and type(state["cooldown_until_date_raw"]) is not int
            or state.get("pending_query") is not None
            and not isinstance(state["pending_query"], dict)):
        raise ValueError("declaration cooldown state is malformed")
    owner = _owner(frame)
    if owner is None:
        raise ValueError("declaration cooldown frame is unbound")
    if (state.get("actor_character_id"), state.get("episode_run_id")) != owner[:2]:
        return _new(frame)
    if state["cooldown_until_date_raw"] is not None:
        # Earlier v1 writers reset the streak when setting this deadline.
        # Its presence proves the threshold was reached, even after expiry.
        state["consecutive_no_war_rounds"] = 2
    return state


def _save(state_dir, state: dict) -> None:
    path = _path(state_dir)
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


def _verified_war_id(snapshot: dict) -> int | str | None:
    continuity = snapshot.get("war_declaration_continuity_v1")
    wars = snapshot.get("active_wars")
    if not (isinstance(continuity, dict)
            and continuity.get("schema") == "war-declaration-continuity-v1"
            and continuity.get("status") == "war_started"
            and continuity.get("native_response") == "accepted"
            and continuity.get("postcondition_verified") is True
            and isinstance(wars, list)):
        return None
    war_id = continuity.get("war_id")
    if type(war_id) not in (int, str) or not war_id:
        return None
    if not any(isinstance(war, dict) and war.get("war_id") == war_id
               and war.get("player_side") == "attacker" for war in wars):
        return None
    return war_id


def view(state_dir, snapshot: dict, frame: dict) -> dict:
    """Read cooldown and reconcile only a uniquely verified real declaration."""
    state = _load(state_dir, frame)
    pending = state["pending_query"]
    bridge_pid = frame.get("bridge_pid")
    if (isinstance(pending, dict) and type(bridge_pid) is int
            and type(pending.get("source_bridge_pid")) is int
            and pending["source_bridge_pid"] != bridge_pid):
        # A cold Game load may roll back to a save. Retain the streak/deadline,
        # but never settle a query from the former process as a new round.
        state["pending_query"] = None
        _save(state_dir, state)
    war_id = _verified_war_id(snapshot)
    if war_id is not None and war_id != state["last_confirmed_war_id"]:
        state.update(consecutive_no_war_rounds=0, cooldown_until_date_raw=None,
                     pending_query=None, last_confirmed_war_id=war_id)
        _save(state_dir, state)
    elif (isinstance(snapshot.get("active_wars"), list)
          and snapshot["active_wars"] and state["pending_query"] is not None):
        # A defensive or otherwise unrelated war interrupts the peaceful
        # opportunity round without proving an offensive declaration.
        state["pending_query"] = None
        _save(state_dir, state)
    date = frame["date_raw"]
    until = state["cooldown_until_date_raw"]
    return {
        "schema": SCHEMA,
        "status": "active" if type(until) is int and date < until else "inactive",
        "consecutive_no_war_rounds": state["consecutive_no_war_rounds"],
        "cooldown_until_date_raw": until,
        "remaining_days": (until - date + 23) // 24 if type(until) is int and date < until else 0,
        "pending_query_sequence": (state["pending_query"].get("query_sequence")
                                   if isinstance(state["pending_query"], dict) else None),
        "actor_character_id": state["actor_character_id"],
        "episode_run_id": state["episode_run_id"],
    }


def observe_completed_query(state_dir, source_frame: dict, result: dict) -> dict:
    """Open one completed native query round; a pending collect has no credit."""
    state = _load(state_dir, source_frame)
    sequence = result.get("query_sequence") if isinstance(result, dict) else None
    if not (isinstance(result, dict) and result.get("step") == "query-declarable-wars"
            and result.get("accepted") is True and result.get("status") == "available"
            and isinstance(result.get("declarable_wars"), list)
            and type(sequence) is int and sequence > 0
            and type(source_frame.get("native_revision")) is int
            and source_frame["native_revision"] > 0
            and type(source_frame.get("bridge_pid")) is int
            and source_frame["bridge_pid"] > 0):
        return view(state_dir, {}, source_frame)
    pending = state["pending_query"]
    if (sequence == state["last_closed_query_sequence"]
            or isinstance(pending, dict) and sequence == pending.get("query_sequence")):
        return view(state_dir, {}, source_frame)
    state["pending_query"] = {
        "query_sequence": sequence,
        "source_snapshot_id": source_frame.get("snapshot_id"),
        "source_native_revision": source_frame["native_revision"],
        "source_date_raw": source_frame["date_raw"],
        "source_bridge_pid": source_frame.get("bridge_pid"),
    }
    _save(state_dir, state)
    return view(state_dir, {}, source_frame)


def observe_after_turn(
    state_dir, source_frame: dict, outcome: dict, post_snapshot: dict,
    post_frame: dict,
) -> dict:
    """Settle only a verified later advance; submitted war remains pending."""
    state = _load(state_dir, source_frame)
    if _owner(post_frame) is None or _owner(post_frame)[:2] != _owner(source_frame)[:2]:
        raise ValueError("declaration cooldown post-frame changed actor or episode")
    war_id = _verified_war_id(post_snapshot)
    if war_id is not None and war_id != state["last_confirmed_war_id"]:
        state.update(consecutive_no_war_rounds=0, cooldown_until_date_raw=None,
                     pending_query=None, last_confirmed_war_id=war_id)
        _save(state_dir, state)
        return view(state_dir, post_snapshot, post_frame)
    pending = state["pending_query"]
    result = outcome.get("result") if isinstance(outcome, dict) else None
    continuity = post_snapshot.get("war_declaration_continuity_v1")
    unresolved_declaration = (isinstance(continuity, dict)
                              and continuity.get("status") not in
                              {"war_started", "native_rejected", "not_submitted"})
    if not (isinstance(pending, dict) and outcome.get("status") == "executed"
            and outcome.get("selected_step") == "life-advance"
            and isinstance(result, dict) and result.get("step") == "life-advance"
            and result.get("progress_status") == "postcondition"
            and result.get("paused") is True
            and type(result.get("starting_date_raw")) is int
            and type(result.get("ending_date_raw")) is int
            and result["starting_date_raw"] == source_frame["date_raw"]
            and result["ending_date_raw"] > result["starting_date_raw"]
            and result["ending_date_raw"] == post_frame["date_raw"]
            and post_snapshot.get("paused") is True
            and isinstance(post_snapshot.get("active_wars"), list)
            and not post_snapshot["active_wars"]
            and not isinstance(post_snapshot.get("active_event"), dict)
            and not isinstance(post_snapshot.get("pending_character_interaction"), dict)
            and not unresolved_declaration
            and source_frame["date_raw"] >= pending["source_date_raw"]
            and source_frame.get("bridge_pid") == pending.get("source_bridge_pid")
            and post_frame.get("bridge_pid") == pending.get("source_bridge_pid")
            and post_frame["native_revision"] > pending["source_native_revision"]):
        return view(state_dir, post_snapshot, post_frame)
    state["last_closed_query_sequence"] = pending["query_sequence"]
    state["pending_query"] = None
    state["consecutive_no_war_rounds"] = min(2, state["consecutive_no_war_rounds"] + 1)
    if state["consecutive_no_war_rounds"] == 2:
        state["cooldown_until_date_raw"] = post_frame["date_raw"] + COOLDOWN_RAW_DAYS
    _save(state_dir, state)
    return view(state_dir, post_snapshot, post_frame)

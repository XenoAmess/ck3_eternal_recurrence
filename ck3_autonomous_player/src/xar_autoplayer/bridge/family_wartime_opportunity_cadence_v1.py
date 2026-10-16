"""Pace a repeatedly observed empty wartime family opportunity.

Only complete, actual read-only/game-day receipts may count.  A cooldown is a
30-day polling tradeoff, not a claim that family facts remain unchanged.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

SCHEMA = "xar.ck3.family-wartime-opportunity-cadence/v1"
FILENAME = "family-wartime-opportunity-cadence-v1.json"
PERIOD_RAW = 30 * 24
RELATION_SCHEMA = "xar.ck3.current-first-heir-relationship.v1"
DIAGNOSTIC_SCHEMA = "xar.ck3.first-heir-marriage-private-diagnostic.v1"


def _identity(frame: dict) -> tuple[int, str, int, int]:
    actor = frame.get("actor_character_id")
    episode = frame.get("episode_run_id")
    date = frame.get("date_raw")
    native = frame.get("native_revision")
    if (frame.get("status") != "complete" or type(actor) is not int or actor <= 0
            or not isinstance(episode, str) or not episode
            or type(date) is not int or date <= 0
            or type(native) is not int or native <= 0):
        raise ValueError("wartime family cadence needs a complete bound frame")
    return actor, episode, date, native


def _empty(frame: dict) -> dict:
    actor, episode, _, _ = _identity(frame)
    return {"schema": SCHEMA, "actor_character_id": actor,
            "episode_run_id": episode, "consecutive_noop_dates": 0,
            "qualified_source": False,
            "cooldown_until_date_raw": None, "last_noop_date_raw": None,
            "last_observed_end_date_raw": None, "last_query_identity": None,
            "heir_character_id": None, "player_spouse_signature": None,
            "expected_successor_character_id": None}


def _write(state_dir: Path, value: dict) -> None:
    path = Path(state_dir) / FILENAME
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    try:
        with temporary.open("x", encoding="utf-8") as output:
            json.dump(value, output, sort_keys=True, separators=(",", ":"))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _read(state_dir: Path, frame: dict) -> dict:
    path = Path(state_dir) / FILENAME
    if not path.exists():
        return _empty(frame)
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or value.get("schema") != SCHEMA
            or type(value.get("consecutive_noop_dates")) is not int
            or value["consecutive_noop_dates"] not in (0, 1)
            or type(value.get("qualified_source", False)) is not bool
            or any(value.get(key) is not None and type(value[key]) is not int
                   for key in ("cooldown_until_date_raw", "last_noop_date_raw",
                               "last_observed_end_date_raw", "heir_character_id",
                               "expected_successor_character_id"))
            or value.get("last_query_identity") is not None
            and not isinstance(value["last_query_identity"], list)
            or value.get("player_spouse_signature") is not None
            and not isinstance(value["player_spouse_signature"], list)):
        raise ValueError("wartime family cadence state is malformed")
    actor, episode, date, _ = _identity(frame)
    if ((value.get("actor_character_id"), value.get("episode_run_id"))
            != (actor, episode)
            or (type(value.get("last_observed_end_date_raw")) is int
                and date < value["last_observed_end_date_raw"])):
        value = _empty(frame)
        _write(state_dir, value)
    return value


def view(state_dir: Path, frame: dict) -> dict:
    value = _read(state_dir, frame)
    date = _identity(frame)[2]
    until = value["cooldown_until_date_raw"]
    active = type(until) is int and date < until
    return {"schema": SCHEMA, "status": "active" if active else "inactive",
            "consecutive_noop_dates": value["consecutive_noop_dates"],
            "qualified_source": value.get("qualified_source", False),
            "cooldown_until_date_raw": until,
            "remaining_days": (until - date + 23) // 24 if active else 0,
            "heir_character_id": value["heir_character_id"],
            "player_spouse_signature": value["player_spouse_signature"],
            "expected_successor_character_id": value["expected_successor_character_id"]}


def clear(state_dir: Path, frame: dict) -> dict:
    _write(state_dir, _empty(frame))
    return view(state_dir, frame)


def player_spouse_signature(snapshot: dict) -> list | None:
    player = snapshot.get("played_character")
    if not isinstance(player, dict) or player.get("alive") is not True:
        return None
    spouses = player.get("spouse_ids")
    if not isinstance(spouses, list) or any(type(x) is not int for x in spouses):
        return None
    return [player.get("betrothed_id"), player.get("primary_spouse_id"), list(spouses)]


def expected_successor(snapshot: dict) -> int | None:
    row = snapshot.get("succession_expectation")
    value = row.get("expected_successor_character_id") if isinstance(row, dict) else None
    return (value if isinstance(row, dict) and row.get("status") == "available"
            and type(value) is int and value > 0 else None)


def complete_noop(frame: dict, plan: dict, source: dict) -> tuple[int, list[int]] | None:
    _, _, date, native = _identity(frame)
    relation = plan.get("family_marriage_current_relationship")
    diagnostic = plan.get("family_marriage_private_diagnostic")
    if (source.get("status") != "reviewed" or source.get("date_raw") != date
            or source.get("native_revision") != native
            or source.get("actor_character_id") != frame["actor_character_id"]
            or source.get("episode_run_id") != frame["episode_run_id"]
            or plan.get("family_marriage_status")
            != "no_positive_observed_marriage_opportunity"
            or not isinstance(relation, dict) or not isinstance(diagnostic, dict)
            or relation.get("schema") != RELATION_SCHEMA
            or relation.get("status") != "available"
            or relation.get("bilateral_verified") is not True
            or relation.get("read_only") is not True
            or relation.get("advertised") is not False
            or relation.get("native_revision") != native
            or relation.get("betrothed_character_id") is not None
            or relation.get("primary_spouse_character_id") is not None
            or relation.get("spouse_character_ids") != []
            or diagnostic.get("schema") != DIAGNOSTIC_SCHEMA
            or diagnostic.get("read_only") is not True
            or diagnostic.get("advertised") is not False
            or diagnostic.get("date_raw") != date
            or diagnostic.get("native_revision") != native
            or diagnostic.get("episode_run_id") != frame["episode_run_id"]
            or diagnostic.get("selected_candidate_character_id") is not None
            or not isinstance(diagnostic.get("rows"), list)
            or len(diagnostic["rows"]) != 5
            or any(not isinstance(row, dict) or row.get("status") != "available"
                   or not isinstance(row.get("rejection_reasons"), list)
                   or not row["rejection_reasons"] for row in diagnostic["rows"])):
        return None
    heir = relation.get("heir_character_id")
    root_sequence = relation.get("root_query_sequence")
    legal_sequence = diagnostic.get("legality_query_sequence")
    if (any(type(x) is not int or x <= 0 for x in
            (heir, root_sequence, legal_sequence))
            or diagnostic.get("observed_first_heir_character_id") != heir
            or source.get("heir_character_id") != heir
            or source.get("player_spouse_signature") is None
            or source.get("expected_successor_character_id") != heir):
        return None
    return heir, [native, root_sequence, legal_sequence]


def _completed_review(frame: dict, plan: dict, outcome: dict) -> int | None:
    result = outcome.get("result")
    selected = plan.get("selected_step")
    if not isinstance(result, dict) or outcome.get("status") != "executed":
        return None
    if (selected == "query-army-strengths-v1"
            or isinstance(selected, str)
            and selected.startswith("query-war-termination-options-")):
        if (outcome.get("selected_step") == selected
                and result.get("accepted") is True
                and result.get("status") in ("available", "partial")
                and result.get("material_result") is not True):
            return frame["date_raw"]
    if (selected == "life-advance"
            and outcome.get("selected_step") in ("life-advance", "life-advance-one-day")
            and result.get("step") in ("life-advance", "life-advance-one-day")
            and result.get("progress_status") == "postcondition"
            and result.get("paused") is True
            and result.get("starting_date_raw") == frame["date_raw"]
            and type(result.get("ending_date_raw")) is int
            and result["ending_date_raw"] > frame["date_raw"]
            and result.get("active_event") is None
            and result.get("pending_character_interaction") is None):
        return result["ending_date_raw"]
    return None


def observe_after_turn(state_dir: Path, frame: dict, plan: dict, outcome: dict) -> dict:
    value = _read(state_dir, frame)
    result = outcome.get("result") if isinstance(outcome, dict) else None
    if (isinstance(result, dict) and outcome.get("status") == "executed"
            and ((outcome.get("selected_step")
                  == "query-observed-first-heir-marriage-result-v1-private"
                  and result.get("status") in ("marriage", "betrothal")
                  and result.get("material_result") is True)
                 or (outcome.get("selected_step")
                     == "private-query-child-education-focus-receipt-v1"
                     and result.get("status") == "observed_applied"
                     and result.get("observed_applied") is True))):
        _write(state_dir, _empty(frame))
        return view(state_dir, frame)
    if not isinstance(plan, dict) or not isinstance(outcome, dict):
        return view(state_dir, frame)
    end_date = _completed_review(frame, plan, outcome)
    source = plan.get("_family_wartime_review_v1")
    if end_date is None or not isinstance(source, dict):
        return view(state_dir, frame)
    if (type(value.get("cooldown_until_date_raw")) is int
            and frame["date_raw"] < value["cooldown_until_date_raw"]):
        return view(state_dir, {**frame, "date_raw": end_date})
    noop = complete_noop(frame, plan, source)
    if noop is None:
        if value["consecutive_noop_dates"] or value.get("qualified_source", False):
            value["consecutive_noop_dates"] = 0
            value["qualified_source"] = False
            _write(state_dir, value)
        return view(state_dir, {**frame, "date_raw": end_date})
    heir, query_identity = noop
    if (value.get("last_noop_date_raw") == frame["date_raw"]
            or value.get("last_query_identity") == query_identity):
        return view(state_dir, {**frame, "date_raw": end_date})
    same_source = (value.get("heir_character_id") == heir
                   and value.get("player_spouse_signature")
                   == source["player_spouse_signature"]
                   and value.get("expected_successor_character_id")
                   == source["expected_successor_character_id"])
    # The first lease still requires two distinct complete empty reviews. Once
    # qualified, each expiry must perform one fresh complete review; it may
    # renew only while the same heir/household source remains empty. Unknown or
    # changed material above clears qualification and requires two reviews.
    renew_qualified = same_source and value.get("qualified_source", False)
    value["consecutive_noop_dates"] = value["consecutive_noop_dates"] + 1 if same_source else 1
    value["heir_character_id"] = heir
    value["player_spouse_signature"] = source["player_spouse_signature"]
    value["expected_successor_character_id"] = source["expected_successor_character_id"]
    value["last_noop_date_raw"] = frame["date_raw"]
    value["last_observed_end_date_raw"] = end_date
    value["last_query_identity"] = query_identity
    if renew_qualified or value["consecutive_noop_dates"] >= 2:
        value["consecutive_noop_dates"] = 0
        value["qualified_source"] = True
        value["cooldown_until_date_raw"] = end_date + PERIOD_RAW
    else:
        value["qualified_source"] = False
    _write(state_dir, value)
    return view(state_dir, {**frame, "date_raw": end_date})

"""Private bounded player-child marriage consumer with durable pair identity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .bridge.domain_construction_private_transport_v1 import (
    _identity as bridge_process_identity,
)
from .bridge.player_child_matrilineal_private_action_v1 import (
    ALLIANCE_RESULT_STEP, RESULT_STEP, SCHEMA, SUBMIT_STEP,
)
from .environment import write_json_atomic
from .family_marriage_formal_consumer import read_family_marriage_ledger


_LEDGER = "player-child-matrilineal-formal-v1.json"


def _positive(value: object) -> bool:
    return type(value) is int and 0 < value < 2**31


def _deferrable_war_query(selected: object,
                          snapshot: Mapping[str, object]) -> bool:
    wars = snapshot.get("active_wars")
    return (isinstance(selected, str) and isinstance(wars, list)
            and any(isinstance(war, dict) and _positive(war.get("war_id"))
                    and selected == f"query-war-termination-options-{war['war_id']}"
                    for war in wars))


def read_child_matrilineal_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.is_file():
        return {"schema": SCHEMA, "pending": None, "resolved": None}
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict) or record.get("schema") != SCHEMA
            or "pending" not in record or "resolved" not in record
            or any(record[key] is not None and not isinstance(record[key], dict)
                   for key in ("pending", "resolved"))):
        raise ValueError("player-child marriage ledger malformed")
    return record


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(ledger))


def _positive_value(legality: Mapping[str, object],
                    value: Mapping[str, object]) -> bool:
    row = value.get("row")
    if not isinstance(row, dict):
        return False
    return (
        value.get("status") == "available"
        and value.get("request_matrilineal_option") is True
        and row.get("selected_option_readback") is True
        and row.get("matrilineal_option_selected") is True
        and row.get("effective_matrilineal_if_accepted") is True
        and row.get("complete_can_send") is True
        and row.get("recipient_answer_status_raw") in {0, 1}
        and type(row.get("recipient_ai_accept_raw")) is int
        and row["recipient_ai_accept_raw"] > 0
        and row.get("predicted_outcome_if_accepted") == "marriage"
        and row.get("heir_is_adult") is True
        and row.get("candidate_is_adult") is True
        and row.get("heir_sex_selector_raw") == 1
        and row.get("candidate_sex_selector_raw") == 0
        and row.get("grand_wedding_option_selected") is False
        and row.get("heir_house_id") == legality.get("house_id")
        and row.get("heir_dynasty_id") == legality.get("dynasty_id")
        and row.get("played_dynasty_id") == legality.get("dynasty_id")
        and _positive(row.get("candidate_dynasty_id"))
        and row["candidate_dynasty_id"] != legality.get("dynasty_id")
        and row.get("heir_betrothed_character_id") is None
        and row.get("heir_primary_spouse_character_id") is None
        and row.get("heir_spouse_character_ids") == []
        and row.get("candidate_betrothed_character_id") is None
        and row.get("candidate_primary_spouse_character_id") is None
        and row.get("candidate_spouse_character_ids") == []
    )


def plan_child_matrilineal_private(
    driver: object, planned: dict[str, object],
    snapshot: Mapping[str, object], *, subject_character_id: int,
    candidate_character_id: int,
) -> dict[str, object]:
    """Select only a specified, freshly valued dynasty-preserving adult pair."""
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    if (not _positive(subject_character_id) or not _positive(candidate_character_id)
            or subject_character_id == candidate_character_id):
        raise ValueError("player-child marriage target IDs invalid")
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise ValueError("player-child marriage needs durable state_dir")
    ledger = read_child_matrilineal_ledger(state_dir)
    if (isinstance(snapshot.get("active_event"), dict)
            or isinstance(snapshot.get("pending_character_interaction"), dict)):
        return planned
    pending = ledger["pending"]
    if isinstance(pending, dict):
        selected = plan.get("selected_step")
        if (pending.get("episode_run_id") != snapshot.get("episode_run_id")
                or pending.get("heir_character_id") != subject_character_id
                or pending.get("candidate_character_id") != candidate_character_id):
            raise ValueError("unresolved child proposal belongs to a different target")
        pid, creation = bridge_process_identity(driver)
        last = pending.get("last_checked_native_revision",
                           pending.get("pre_native_revision"))
        already_checked_cold = (pending.get("last_checked_bridge_pid") == pid
                                and pending.get("last_checked_bridge_creation_date") == creation)
        cold = ((pid, creation) != (pending.get("source_bridge_pid"),
                                    pending.get("source_bridge_creation_date"))
                and not already_checked_cold)
        if (cold or (_positive(snapshot.get("native_revision"))
                    and type(last) is int and snapshot["native_revision"] > last)):
            return {**planned, "plan": {**plan,
                "selected_step": RESULT_STEP, "phase": "child_marriage_result_read",
                "child_matrilineal_pending": dict(pending),
                "child_matrilineal_cold_recovery": cold,
                "child_matrilineal_deferred_step": selected,
                "reason": "read bilateral proposal result before another send"}}
        if (selected not in {None, "life-advance"}
                and not _deferrable_war_query(selected, snapshot)):
            return planned
        return {**planned, "plan": {**plan,
            "child_matrilineal_pending": dict(pending),
            "reason": "await later paused child proposal result"}}
    if isinstance(ledger["resolved"], dict):
        resolved = ledger["resolved"]
        if (resolved.get("status") in {"marriage", "betrothal"}
                and "actual_alliance_result" not in resolved):
            return {**planned, "plan": {**plan,
                "selected_step": ALLIANCE_RESULT_STEP,
                "child_matrilineal_resolved": dict(resolved),
                "reason": "read actual bilateral alliance after child marriage"}}
        return planned
    if read_family_marriage_ledger(state_dir)["pending"] is not None:
        return planned
    selected = plan.get("selected_step")
    wartime_wait = _deferrable_war_query(selected, snapshot)
    if selected != "life-advance" and not wartime_wait:
        return planned
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not _positive(snapshot.get("native_revision"))):
        return planned
    legality = driver.query_player_child_marriage_subject_private_v1(
        expected_native_revision=snapshot["native_revision"],
        subject_character_id=subject_character_id)
    if legality.get("status") != "available" or legality.get("player_child_verified") is not True:
        return planned
    value = driver.query_player_child_marriage_value_private_v1(
        legality=legality, candidate_character_id=candidate_character_id,
        request_matrilineal_option=True)
    if not _positive_value(legality, value):
        return {**planned, "plan": {**plan,
            "child_matrilineal_observation": value,
            "reason": "specified child pair lacks positive native selected value"}}
    return {**planned, "plan": {**plan,
        "selected_step": SUBMIT_STEP, "phase": "child_matrilineal_submit",
        "child_matrilineal_legality": legality,
        "child_matrilineal_value": value,
        "child_matrilineal_deferred_step": selected if wartime_wait else None,
        "child_matrilineal_wartime_source": ({
            "date_raw": snapshot.get("date_raw"),
            "native_revision": snapshot.get("native_revision"),
            "active_war_ids": [war.get("war_id") for war in snapshot["active_wars"]
                               if isinstance(war, dict)],
        } if wartime_wait else None),
        "reason": "submit native-final selected maternal-line marriage"}}


def submit_child_matrilineal_private(driver: object, *,
                                    plan: Mapping[str, object],
                                    snapshot: Mapping[str, object]) -> dict[str, object]:
    legality = plan.get("child_matrilineal_legality")
    value = plan.get("child_matrilineal_value")
    if not isinstance(legality, dict) or not isinstance(value, dict) or not _positive_value(legality, value):
        raise ValueError("child proposal lacks selected positive value")
    if (legality.get("native_revision") != snapshot.get("native_revision")
            or value.get("native_revision") != snapshot.get("native_revision")
            or snapshot.get("date_raw") is None):
        raise ValueError("child proposal source frame changed")
    deferred = plan.get("child_matrilineal_deferred_step")
    if deferred is not None and (
            not _deferrable_war_query(deferred, snapshot)
            or plan.get("child_matrilineal_wartime_source") != {
                "date_raw": snapshot.get("date_raw"),
                "native_revision": snapshot.get("native_revision"),
                "active_war_ids": [war.get("war_id") for war in snapshot["active_wars"]
                                   if isinstance(war, dict)],
            }):
        raise ValueError("deferred read-only war query changed before child proposal")
    state_dir = driver.state_dir
    ledger = read_child_matrilineal_ledger(state_dir)
    if ledger["pending"] is not None or ledger["resolved"] is not None:
        raise ValueError("child proposal already submitted or resolved")
    row = value["row"]
    pid, creation = bridge_process_identity(driver)
    pending = {
        "schema": SCHEMA, "status": "receipt_pending", "material_result": False,
        "submission_state": "may_have_submitted",
        "pre_native_revision": snapshot["native_revision"],
        "source_date_raw": snapshot["date_raw"],
        "played_character_id": snapshot["played_character"]["character_id"],
        "heir_character_id": legality["subject_character_id"],
        "candidate_character_id": value["candidate_character_id"],
        "recipient_character_id": row["recipient_character_id"],
        "matrilineal_option_selected": True,
        "claimed_character_ids": [snapshot["played_character"]["character_id"],
                                  legality["subject_character_id"],
                                  value["candidate_character_id"],
                                  row["recipient_character_id"]],
        "deferred_war_query": plan.get("child_matrilineal_deferred_step"),
        "selected_value_projection": dict(row),
        "episode_run_id": snapshot.get("episode_run_id"),
        "source_bridge_pid": pid, "source_bridge_creation_date": creation,
    }
    _write(state_dir, {**ledger, "pending": pending})
    receipt = driver.submit_player_child_matrilineal_private_v1(
        legality=legality, value=value)
    pending.update(receipt)
    pending["submission_state"] = "receipt_pending"
    _write(state_dir, {**ledger, "pending": pending})
    return pending


def query_child_matrilineal_result_private(driver: object, *,
                                           pending: Mapping[str, object],
                                           cold: bool) -> dict[str, object]:
    state_dir = driver.state_dir
    ledger = read_child_matrilineal_ledger(state_dir)
    if ledger["pending"] != dict(pending):
        raise ValueError("child proposal pending identity changed")
    result = driver.query_player_child_matrilineal_result_private_v1(
        pending=dict(pending), cold=cold)
    status = result["status"]
    pid, creation = bridge_process_identity(driver)
    if status in {"marriage", "betrothal", "refused", "invalidated"}:
        resolved = {**result, "source_pending": dict(pending),
                    "episode_run_id": pending["episode_run_id"],
                    "post_bridge_pid": pid,
                    "post_bridge_creation_date": creation}
        _write(state_dir, {**ledger, "pending": None, "resolved": resolved})
    else:
        _write(state_dir, {**ledger, "pending": {**pending,
            "last_checked_native_revision": result["post_native_revision"],
            "last_checked_bridge_pid": pid,
            "last_checked_bridge_creation_date": creation,
            "last_outbound_pending_state": result.get("outbound_pending_state")}})
    return result


def query_child_matrilineal_alliance_private(driver: object, *,
                                             resolved: Mapping[str, object]) -> dict[str, object]:
    state_dir = driver.state_dir
    ledger = read_child_matrilineal_ledger(state_dir)
    if ledger["pending"] is not None or ledger["resolved"] != dict(resolved):
        raise ValueError("child marriage alliance source changed")
    result = driver.query_player_child_matrilineal_alliance_private_v1(
        resolved=dict(resolved))
    _write(state_dir, {**ledger, "resolved": {**resolved,
        "actual_alliance_result": result}})
    return result

"""Bounded default-lineality proposal for an observed split-successor child."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from .bridge.domain_construction_private_transport_v1 import (
    _identity as bridge_process_identity,
)
from .bridge.player_child_matrilineal_private_action_v1 import (
    DEFAULT_ALLIANCE_RESULT_STEP as ALLIANCE_RESULT_STEP,
    DEFAULT_RESULT_STEP as RESULT_STEP,
    DEFAULT_SCHEMA as ACTION_SCHEMA,
    DEFAULT_SUBMIT_STEP as SUBMIT_STEP,
)
from .environment import write_json_atomic
from .family_marriage_formal_consumer import read_family_marriage_ledger
from .guy_default_marriage_policy import (
    choose_specified_child_default_value,
    shortlist_specified_child_default_candidates,
)
from .player_child_matrilineal_formal_consumer import read_child_matrilineal_ledger


LEDGER_SCHEMA = "xar.ck3.player-child-default-formal.v1"
_LEDGER = "player-child-default-formal-v1.json"


def _positive(value: object) -> bool:
    return type(value) is int and 0 < value < 2**31


def _child_aligned_default_lineality(row: object) -> bool:
    return (isinstance(row, dict)
            and row.get("heir_sex_selector_raw") == 0
            and row.get("candidate_sex_selector_raw") == 1
            and row.get("requested_matrilineal_option") is False
            and row.get("matrilineal_option_selected") is False
            and row.get("effective_matrilineal_if_accepted") is
                bool(row["heir_sex_selector_raw"]))


def read_child_default_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.is_file():
        return {"schema": LEDGER_SCHEMA, "pending": None, "resolved": None}
    record = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(record, dict) or record.get("schema") != LEDGER_SCHEMA
            or any(key not in record for key in ("pending", "resolved"))
            or any(record[key] is not None and not isinstance(record[key], dict)
                   for key in ("pending", "resolved"))):
        raise ValueError("player-child default ledger malformed")
    return record


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(ledger))


def _split_successor(driver: object, snapshot: Mapping[str, object]
                     ) -> dict[str, object] | None:
    root = driver._execute_campaign_root_context_v1_query(
        expected_revision=snapshot["revision"])
    context = root.get("campaign_root_context")
    if (root.get("status") != "available"
            or root.get("queried_revision") != snapshot.get("revision")
            or root.get("queried_native_revision") != snapshot.get("native_revision")
            or root.get("queried_snapshot_id") != snapshot.get("snapshot_id")
            or not isinstance(context, dict)
            or context.get("player_character_id") !=
                snapshot["played_character"]["character_id"]):
        raise ValueError("split-successor root crossed the paused player frame")
    rows = context.get("held_title_partition")
    if not isinstance(rows, list):
        return None
    primary = [row for row in rows if isinstance(row, dict)
               and row.get("primary") is True]
    secondary = [row for row in rows if isinstance(row, dict)
                 and row.get("primary") is False
                 and _positive(row.get("first_heir_character_id"))
                 and isinstance(row.get("title"), dict)
                 and _positive(row["title"].get("title_id"))]
    if len(primary) != 1 or not _positive(primary[0].get("first_heir_character_id")):
        return None
    # This first narrow policy handles one split-successor child. More than one
    # distinct successor requires a value comparison that is not present here.
    subject_ids = {row["first_heir_character_id"] for row in secondary}
    if (len(subject_ids) != 1
            or primary[0]["first_heir_character_id"] in subject_ids):
        return None
    subject_id = next(iter(subject_ids))
    return {
        "subject_character_id": subject_id,
        "split_title_ids": sorted(
            row["title"]["title_id"] for row in secondary
            if row["first_heir_character_id"] == subject_id),
        "primary_heir_character_id": primary[0]["first_heir_character_id"],
        "source_revision": snapshot["revision"],
        "source_native_revision": snapshot["native_revision"],
        "source_date_raw": snapshot["date_raw"],
    }


def _eligible_base_step(plan: Mapping[str, object],
                        snapshot: Mapping[str, object]) -> bool:
    selected = plan.get("selected_step")
    if selected == "life-advance":
        return True
    if selected is not None:
        return False
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or not wars:
        return False
    return (isinstance(plan.get("phase"), str)
            and plan["phase"].startswith("native_war")
            and isinstance(plan.get("reason"), str)
            and bool(plan["reason"]))


def plan_child_default_private(driver: object, planned: dict[str, object],
                               snapshot: Mapping[str, object]
                               ) -> dict[str, object]:
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise ValueError("player-child default proposal needs durable state_dir")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not _positive(snapshot.get("native_revision"))
            or not isinstance(snapshot.get("played_character"), dict)
            or not _positive(snapshot["played_character"].get("character_id"))
            or isinstance(snapshot.get("active_event"), dict)
            or isinstance(snapshot.get("pending_character_interaction"), dict)):
        return planned
    ledger = read_child_default_ledger(state_dir)
    pending = ledger["pending"]
    if isinstance(pending, dict):
        pid, creation = bridge_process_identity(driver)
        if pending.get("episode_run_id") != snapshot.get("episode_run_id"):
            return planned
        cold = (pid, creation) != (
            pending.get("source_bridge_pid"),
            pending.get("source_bridge_creation_date"))
        last = pending.get("last_checked_native_revision",
                           pending.get("pre_native_revision"))
        checked_here = (
            pending.get("last_checked_bridge_pid") == pid
            and pending.get("last_checked_bridge_creation_date") == creation)
        if ((cold and not checked_here)
                or (type(last) is int and snapshot["native_revision"] > last)):
            return {**planned, "plan": {**plan,
                "selected_step": RESULT_STEP,
                "phase": "child_default_result_read",
                "child_default_pending": dict(pending),
                "child_default_cold_recovery": cold,
                "reason": "read bound child proposal before another action"}}
        return {**planned, "plan": {**plan,
            "child_default_pending": dict(pending),
            "child_default_status": "await_later_paused_frame"}}
    resolved = ledger["resolved"]
    if isinstance(resolved, dict):
        pid, creation = bridge_process_identity(driver)
        if resolved.get("episode_run_id") != snapshot.get("episode_run_id"):
            return planned
        if resolved.get("status") in {"marriage", "betrothal"}:
            if (pid, creation) != (
                    resolved.get("post_bridge_pid"),
                    resolved.get("post_bridge_creation_date")):
                source = resolved.get("source_pending")
                if not isinstance(source, dict):
                    raise ValueError("child default material pair lacks cold source")
                return {**planned, "plan": {**plan,
                    "selected_step": RESULT_STEP,
                    "phase": "child_default_cold_material_recheck",
                    "child_default_pending": dict(source),
                    "child_default_cold_recovery": True,
                    "child_default_material_recheck": True,
                    "reason": "re-read actual child pair in new PID"}}
            if ((pid, creation) != (
                    resolved.get("alliance_bridge_pid"),
                    resolved.get("alliance_bridge_creation_date"))):
                return {**planned, "plan": {**plan,
                    "selected_step": ALLIANCE_RESULT_STEP,
                    "phase": "child_default_actual_alliance_read",
                    "child_default_resolved": dict(resolved),
                    "reason": "read actual player-recipient alliance"}}
        return planned
    if not _eligible_base_step(plan, snapshot):
        return planned
    if (read_family_marriage_ledger(state_dir)["pending"] is not None
            or read_child_matrilineal_ledger(state_dir)["pending"] is not None):
        return planned
    split = _split_successor(driver, snapshot)
    if split is None:
        return planned
    subject = driver.query_player_child_marriage_subject_private_v1(
        expected_native_revision=snapshot["native_revision"],
        subject_character_id=split["subject_character_id"])
    if (subject.get("status") != "available"
            or subject.get("player_child_verified") is not True
            or subject.get("subject_character_id") !=
                split["subject_character_id"]
            or subject.get("played_character_id") !=
                snapshot["played_character"]["character_id"]
            or subject.get("native_revision") != snapshot["native_revision"]
            or subject.get("betrothed_character_id") is not None
            or subject.get("primary_spouse_character_id") is not None
            or subject.get("spouse_character_ids") != []):
        return planned
    # The bounded comparison is the two youngest future partners in the
    # compact native-final ranking. Both receive a full same-frame value read.
    shortlist = shortlist_specified_child_default_candidates(subject, limit=2)
    values: list[dict[str, object]] = []
    for candidate_id in shortlist:
        value = driver.query_player_child_marriage_value_private_v1(
            legality=subject, candidate_character_id=candidate_id,
            request_matrilineal_option=False)
        values.append(value)
    if ([value.get("candidate_character_id") for value in values] != shortlist
            or len(set(shortlist)) != len(shortlist)):
        raise ValueError("child default comparator set is incomplete")
    decision = choose_specified_child_default_value(
        subject, values, split_successor_verified=True)
    observation = {
        "split_successor": split,
        "shortlist_candidate_ids": shortlist,
        "full_value_candidate_ids": [
            row.get("candidate_character_id") for row in values],
        "stop_reason": "complete_shortlist_compared",
        "policy_decision": decision,
    }
    candidate_id = decision.get("selected_candidate_character_id")
    matches = [value for value in values
               if value.get("candidate_character_id") == candidate_id]
    if (decision.get("status") != "selected" or len(matches) != 1
            or not _child_aligned_default_lineality(matches[0].get("row"))):
        return {**planned, "plan": {**plan,
            "child_default_observation": observation}}
    return {**planned, "plan": {**plan,
        "selected_step": SUBMIT_STEP,
        "phase": "child_default_typed_submit",
        "child_default_legality": subject,
        "child_default_value": matches[0],
        "child_default_full_values": values,
        "child_default_observation": observation,
        "child_default_displaced_plan": {
            "selected_step": plan.get("selected_step"),
            "phase": plan.get("phase"), "reason": plan.get("reason")},
        "reason": "submit one native-final split-successor child proposal"}}


def submit_child_default_private(driver: object, *,
                                 plan: Mapping[str, object],
                                 snapshot: Mapping[str, object]
                                 ) -> dict[str, object]:
    legality = plan.get("child_default_legality")
    value = plan.get("child_default_value")
    full_values = plan.get("child_default_full_values")
    observation = plan.get("child_default_observation")
    if (not isinstance(legality, dict) or not isinstance(value, dict)
            or not isinstance(full_values, list)
            or not isinstance(observation, dict)
            or legality.get("native_revision") != snapshot.get("native_revision")
            or value.get("native_revision") != snapshot.get("native_revision")
            or value.get("legality_query_sequence") != legality.get("query_sequence")
            or value.get("request_matrilineal_option") is not False):
        raise ValueError("child default selected value crossed its source frame")
    split = _split_successor(driver, snapshot)
    chosen = observation.get("policy_decision")
    shortlist = observation.get("shortlist_candidate_ids")
    if (split != observation.get("split_successor")
            or not isinstance(chosen, dict)
            or not isinstance(shortlist, list)
            or shortlist != shortlist_specified_child_default_candidates(
                legality, limit=2)
            or [row.get("candidate_character_id") for row in full_values
                if isinstance(row, dict)] != shortlist
            or len(full_values) != len(shortlist)
            or len(set(shortlist)) != len(shortlist)
            or chosen.get("status") != "selected"
            or chosen.get("selected_candidate_character_id") !=
                value.get("candidate_character_id")
            ):
        raise ValueError("child default split or value changed before submission")
    fresh_values = [
        driver.query_player_child_marriage_value_private_v1(
            legality=legality, candidate_character_id=candidate_id,
            request_matrilineal_option=False)
        for candidate_id in shortlist
    ]
    if (fresh_values != full_values
            or choose_specified_child_default_value(
                legality, fresh_values, split_successor_verified=True
            ).get("selected_candidate_character_id") !=
                value.get("candidate_character_id")):
        raise ValueError("child default full comparator changed before submission")
    # The native selected-proof cache holds one pair. Re-reading the selected
    # full value last binds that exact pair for the typed submit.
    selected_fresh = driver.query_player_child_marriage_value_private_v1(
        legality=legality,
        candidate_character_id=value["candidate_character_id"],
        request_matrilineal_option=False)
    if selected_fresh != value:
        raise ValueError("child default selected native proof changed")
    row = value.get("row")
    if (not isinstance(row, dict)
            or row.get("heir_character_id") != split["subject_character_id"]
            or row.get("actor_character_id") !=
                snapshot["played_character"]["character_id"]
            or not _child_aligned_default_lineality(row)
            or not _positive(row.get("recipient_character_id"))):
        raise ValueError("child default selected pair identity changed")
    state_dir = driver.state_dir
    ledger = read_child_default_ledger(state_dir)
    if (ledger["pending"] is not None or ledger["resolved"] is not None
            or read_family_marriage_ledger(state_dir)["pending"] is not None
            or read_child_matrilineal_ledger(state_dir)["pending"] is not None):
        raise ValueError("child default proposal already committed or resource busy")
    pid, creation = bridge_process_identity(driver)
    pending = {
        "schema": ACTION_SCHEMA, "status": "receipt_pending",
        "submission_state": "may_have_submitted",
        "material_result": False,
        "pre_native_revision": snapshot["native_revision"],
        "source_date_raw": snapshot["date_raw"],
        "episode_run_id": snapshot["episode_run_id"],
        "played_character_id": snapshot["played_character"]["character_id"],
        "heir_character_id": split["subject_character_id"],
        "candidate_character_id": value["candidate_character_id"],
        "recipient_character_id": row["recipient_character_id"],
        "matrilineal_option_selected": False,
        "split_title_ids": split["split_title_ids"],
        "claimed_character_ids": [
            snapshot["played_character"]["character_id"],
            split["subject_character_id"],
            value["candidate_character_id"],
            row["recipient_character_id"]],
        "selected_value_projection": dict(row),
        "deferred_prior_plan": dict(
            plan.get("child_default_displaced_plan", {})),
        "source_bridge_pid": pid,
        "source_bridge_creation_date": creation,
    }
    _write(state_dir, {**ledger, "pending": pending})
    receipt = driver.submit_player_child_default_private_v1(
        legality=legality, value=value)
    if (receipt.get("schema") != ACTION_SCHEMA
            or receipt.get("status") != "receipt_pending"
            or receipt.get("material_result") is not False
            or receipt.get("played_character_id") != pending["played_character_id"]
            or receipt.get("heir_character_id") != pending["heir_character_id"]
            or receipt.get("candidate_character_id") !=
                pending["candidate_character_id"]
            or receipt.get("recipient_character_id") !=
                pending["recipient_character_id"]
            or receipt.get("matrilineal_option_selected") is not False):
        raise ValueError("child default ACK identity changed; proposal remains pending")
    pending.update(receipt)
    pending["submission_state"] = "receipt_pending"
    _write(state_dir, {**ledger, "pending": pending})
    return pending


def query_child_default_result_private(
    driver: object, *, pending: Mapping[str, object], cold: bool,
    material_recheck: bool = False,
) -> dict[str, object]:
    state_dir = driver.state_dir
    ledger = read_child_default_ledger(state_dir)
    prior = ledger["resolved"]
    if material_recheck:
        if (not cold or ledger["pending"] is not None
                or not isinstance(prior, dict)
                or prior.get("source_pending") != dict(pending)
                or prior.get("status") not in {"marriage", "betrothal"}):
            raise ValueError("child default cold material source changed")
    elif ledger["pending"] != dict(pending):
        raise ValueError("child default pending pair changed")
    result = driver.query_player_child_default_result_private_v1(
        pending=dict(pending), cold=cold)
    status = result.get("status")
    pid, creation = bridge_process_identity(driver)
    if material_recheck:
        if (status not in {prior["status"], "marriage"}
                or result.get("material_result") is not True
                or (prior["status"] == "marriage" and status != "marriage")):
            raise ValueError("cold restore lost child default material pair")
        updated = {**prior, "status": status,
                   "post_bridge_pid": pid,
                   "post_bridge_creation_date": creation,
                   "cold_recovery_verified": True}
        updated.pop("actual_alliance_result", None)
        updated.pop("alliance_bridge_pid", None)
        updated.pop("alliance_bridge_creation_date", None)
        _write(state_dir, {**ledger, "resolved": updated})
        return result
    if status in {"marriage", "betrothal", "refused", "invalidated"}:
        resolved = {
            **result, "source_pending": dict(pending),
            "episode_run_id": pending["episode_run_id"],
            "post_bridge_pid": pid,
            "post_bridge_creation_date": creation}
        _write(state_dir, {**ledger, "pending": None, "resolved": resolved})
    elif status in {"pending", "accepted_pending"}:
        _write(state_dir, {**ledger, "pending": {
            **pending,
            "last_checked_native_revision": result["post_native_revision"],
            "last_checked_bridge_pid": pid,
            "last_checked_bridge_creation_date": creation,
            "last_outbound_pending_state": result.get("outbound_pending_state")}})
    else:
        raise ValueError("child default result status unavailable")
    return result


def query_child_default_alliance_private(
    driver: object, *, resolved: Mapping[str, object],
) -> dict[str, object]:
    state_dir = driver.state_dir
    ledger = read_child_default_ledger(state_dir)
    if ledger["pending"] is not None or ledger["resolved"] != dict(resolved):
        raise ValueError("child default alliance source changed")
    result = driver.query_player_child_default_alliance_private_v1(
        resolved=dict(resolved))
    pid, creation = bridge_process_identity(driver)
    _write(state_dir, {**ledger, "resolved": {
        **resolved, "actual_alliance_result": result,
        "alliance_bridge_pid": pid,
        "alliance_bridge_creation_date": creation}})
    return result

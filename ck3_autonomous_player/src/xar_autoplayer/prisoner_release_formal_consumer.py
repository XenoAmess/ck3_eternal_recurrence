"""Consume an observed player release offer and retain its pending-only ACK."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from pathlib import Path

from .environment import write_json_atomic
from .prisoner_ransom_formal_consumer import (
    _frame, _fresh_private_pump, _positive, _war_uncommitted, read_ransom_ledger,
)
from .bridge.driver import BridgeUnavailableError
from .bridge.prisoner_release_action_private_12004 import _selected_ordinal
from .bridge.prisoner_negotiated_preview_contract_12003 import (
    normalize_prisoner_negotiated_preview_12003, release_option_mask_12003,
)
from .bridge.prisoner_release_preview_contract_12003 import (
    normalize_prisoner_release_preview_12003,
)
from .bridge.war_contract import query_war_prisoner_release_pairs_v1_step


SUBMIT_STEP = "submit-player-prisoner-release-v1"
_LEDGER = "player-prisoner-release-formal-v1.json"
_QUERY_STEP = "query-player-prisoner-collection-private-v1"
_DISCOVERY_STEPS = {
    "query-campaign-root-context-v1",
    "query-declarable-wars",
    "query-arrange-marriage-choices",
}


def read_release_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.exists():
        return {"pending": None}
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict) or set(value) != {"pending"}
            or value["pending"] is not None and not isinstance(value["pending"], dict)):
        raise ValueError("prisoner release pending record is malformed")
    return value


def _observed_inputs(
    driver: object, snapshot: dict[str, object],
) -> tuple[dict[str, object] | None, list[dict[str, object]]]:
    def collect(view: dict[str, object], native_history: list[dict[str, object]]):
        history = [row for row in view.get("history", []) if isinstance(row, dict)]
        history.extend(row for row in native_history if isinstance(row, dict))
        collection = None
        war_results: dict[str, dict[str, object]] = {}
        for row in history:
            result = row.get("result")
            command = row.get("command")
            if row.get("ok") is not True or not isinstance(result, dict):
                continue
            if (isinstance(command, str) and command.startswith(_QUERY_STEP)
                    and result.get("queried_revision") == snapshot.get("revision")
                    and result.get("queried_snapshot_id") == snapshot.get("snapshot_id")
                    and result.get("snapshot_revision") == snapshot.get("native_revision")):
                collection = result
            elif isinstance(command, str):
                war_results[command] = result
        wars = snapshot.get("active_wars")
        war_reads = [war_results.get(query_war_prisoner_release_pairs_v1_step(
            war["war_id"]), {}) for war in wars] if isinstance(wars, list) else []
        return {"collection": collection, "war_reads": war_reads}

    planning_view = getattr(driver, "_with_internal_planning_view", None)
    observed = (planning_view(snapshot, collect) if callable(planning_view)
                else collect(snapshot, snapshot.get("native_command_history", [])))
    return observed["collection"], observed["war_reads"]


def _positive_ransom_has_priority(
    snapshot: Mapping[str, object], row: Mapping[str, object],
) -> bool:
    # Preserve the existing outgoing ransom leaf's gold and prisoner eligibility.
    quote = row.get("ransom_quote_preview")
    actor, native, date = _frame(snapshot)
    tier = row.get("primary_title_tier_raw")
    return (isinstance(quote, Mapping) and quote.get("status") == "available"
            and quote.get("definition_key") == "ransom_interaction"
            and quote.get("jailer_character_id") == actor
            and quote.get("prisoner_character_id") == row.get("prisoner_character_id")
            and quote.get("native_revision") == native and quote.get("date_raw") == date
            and quote.get("selected_option") in ("gold", "current_gold")
            and quote.get("amount_is_acceptance_time_quote") is (
                quote.get("selected_option") == "current_gold")
            and quote.get("can_send") is True and quote.get("would_accept_now") is True
            and quote.get("recipient_answer_status_raw") in (0, 1)
            and _positive(quote.get("quoted_gold_raw")) and quote.get("raw_scale") == 100_000
            and "primary_title_tier_raw" in row
            and (tier is None or type(tier) is int and tier == 1)
            and row.get("same_dynasty") is False
            and row.get("is_child_of_played_character") is False)


def _observed_choice(
    snapshot: Mapping[str, object], collection: Mapping[str, object],
    war_reads: list[dict[str, object]],
) -> tuple[dict[str, object] | None, dict[str, object]]:
    actor, native, date = _frame(snapshot)
    value = collection.get("player_prisoner_collection")
    rows = value.get("prisoners") if isinstance(value, Mapping) else None
    if (collection.get("status") != "available"
            or collection.get("snapshot_revision") != native
            or not _positive(collection.get("query_sequence"))
            or not isinstance(value, Mapping) or value.get("status") != "available"
            or value.get("played_character_id") != actor or value.get("date_raw") != date
            or value.get("collection_complete") is not True or not isinstance(rows, list)):
        raise ValueError("release observation differs from the complete current collection")
    if not rows:
        return None, {"status": "no_prisoners"}
    ordinal = _selected_ordinal(collection.get("step"))
    if ordinal >= len(rows) or not isinstance(rows[ordinal], Mapping):
        raise ValueError("release observation lacks its selected prisoner")
    row = rows[ordinal]
    prisoner_id = row.get("prisoner_character_id")
    if (not _positive(prisoner_id) or row.get("source_ordinal") != ordinal
            or row.get("collection_owner_character_id") != actor
            or row.get("jailer_character_id") != actor
            or row.get("custody_relation_verified") is not True):
        raise ValueError("release observation lacks current player custody")
    keys = collection.get("queried_release_option_keys")
    if keys is not None:
        mask = release_option_mask_12003(keys)
        if collection.get("queried_release_option_mask_bits") != mask:
            raise ValueError("release query keys differ from the observed mask")
        preview = normalize_prisoner_negotiated_preview_12003(
            row.get("negotiated_release_preview"), native_revision=native, date_raw=date,
            player_character_id=actor, prisoner_character_id=prisoner_id,
            requested_option_mask_bits=mask)
    else:
        if "queried_release_option_mask_bits" in collection:
            raise ValueError("release observation lacks its selected option keys")
        keys, mask = [], 0
        preview = normalize_prisoner_release_preview_12003(
            row.get("unconditional_release_preview"), native_revision=native, date_raw=date,
            player_character_id=actor, prisoner_character_id=prisoner_id)
    observation = {"status": "not_selected", "prisoner_character_id": prisoner_id,
                   "release_option_keys": list(keys), "release_option_mask_bits": mask,
                   "preview": preview}
    if preview.get("status") != "available":
        return None, {**observation, "status": "input_unavailable"}
    if preview.get("proof_epoch") != collection.get("observation_revision"):
        raise ValueError("release preview differs from its collection observation")
    if preview["can_send"] is not True:
        return None, {**observation, "status": "native_unsendable"}
    if preview["acceptance"].get("would_accept_now") is not True:
        return None, {**observation, "status": "native_refused"}
    if not _war_uncommitted(snapshot, prisoner_id, war_reads):
        return None, {**observation, "status": "war_retention_not_resolved"}
    if _positive_ransom_has_priority(snapshot, row):
        return None, {**observation, "status": "positive_ransom_has_priority"}
    choice = {"source_ordinal": ordinal, "prisoner_character_id": prisoner_id,
              "release_option_keys": list(keys), "release_option_mask_bits": mask,
              "preview": preview, "collection": copy.deepcopy(dict(collection))}
    return choice, {**observation, "status": "actionable"}


def plan_release_formal(
    driver: object, planned: dict[str, object], snapshot: dict[str, object],
) -> dict[str, object]:
    """Use the latest actual selected offer after ransom and urgent actions."""
    plan = planned.get("plan")
    if (not isinstance(plan, dict)
            or getattr(driver, "allow_private_prisoner_ransom_action", False) is not True):
        return planned
    selected = plan.get("selected_step")
    idle = (selected == "life-advance" or isinstance(selected, str)
            and selected.startswith("advance-route-contact-horizon-v1-"))
    generic_discovery = selected in _DISCOVERY_STEPS and snapshot.get("active_wars") == []
    if (not (idle or generic_discovery) or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise ValueError("formal release requires managed state_dir")
    pending = read_release_ledger(state_dir)["pending"]
    if isinstance(pending, dict):
        return {**planned, "plan": {**plan, "prisoner_release_pending": pending}}
    if isinstance(read_ransom_ledger(state_dir)["pending"], dict):
        return planned
    try:
        collection, war_reads = _observed_inputs(driver, snapshot)
        if collection is None:
            return planned
        choice, observation = _observed_choice(snapshot, collection, war_reads)
    except (BridgeUnavailableError, KeyError, TypeError, ValueError) as error:
        return {**planned, "plan": {**plan, "prisoner_release_observation": {
            "status": "input_unavailable", "reason": str(error)}}}
    if choice is None:
        return {**planned, "plan": {**plan, "prisoner_release_observation": observation}}
    return {**planned, "plan": {**plan, "phase": "prisoner_release_typed_submit",
        "selected_step": SUBMIT_STEP, "prisoner_release_choice": choice,
        "prisoner_release_war_reads": copy.deepcopy(war_reads),
        "prisoner_release_deferred_step": selected,
        "prisoner_release_deferred_phase": plan.get("phase"),
        "reason": "submit the current accepted native release terms after positive ransom priority"}}


def submit_release_formal(driver: object, *, plan: Mapping[str, object]) -> dict[str, object]:
    choice = plan.get("prisoner_release_choice")
    if not isinstance(choice, Mapping) or not isinstance(choice.get("collection"), Mapping):
        raise BridgeUnavailableError("formal release lacks its observed selected offer")
    state_dir = driver.state_dir
    if read_release_ledger(state_dir)["pending"] is not None:
        raise BridgeUnavailableError("another prisoner release is unresolved")
    before = driver.take_snapshot()
    actor, native, date = _frame(before)
    refreshed, _ = _observed_choice(before, choice["collection"],
                                     plan.get("prisoner_release_war_reads", []))
    if refreshed != choice:
        raise BridgeUnavailableError("formal release terms differ from the current frame")
    _fresh_private_pump(driver, date)
    pending = {"stage": "submission_unresolved", "material_result": False,
               "pre_public_revision": before["revision"],
               "pre_native_revision": native, "pre_date_raw": date,
               "player_character_id": actor,
               "prisoner_character_id": choice["prisoner_character_id"],
               "release_query_sequence": choice["collection"]["query_sequence"],
               "release_option_keys": choice["release_option_keys"],
               "release_option_mask_bits": choice["release_option_mask_bits"],
               "costs": choice["preview"]["costs"],
               "acceptance": choice["preview"]["acceptance"]}
    write_json_atomic(state_dir / _LEDGER, {"pending": pending})
    ack = driver.submit_player_prisoner_release_private_v1(
        collection=choice["collection"], prisoner_character_id=choice["prisoner_character_id"])
    if (ack.get("status") != "submitted_verification_pending"
            or ack.get("material_result") is not False
            or ack.get("pre_native_revision") != native
            or ack.get("pre_date_raw") != date):
        raise BridgeUnavailableError("native release submit lacks a pending-only ACK")
    pending.update(stage="receipt_pending", status="submitted_verification_pending",
                   action_ack=ack)
    write_json_atomic(state_dir / _LEDGER, {"pending": pending})
    return pending

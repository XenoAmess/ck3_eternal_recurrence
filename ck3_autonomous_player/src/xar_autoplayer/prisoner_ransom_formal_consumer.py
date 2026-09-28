"""Bounded private prisoner ransom policy and material recovery ledger."""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping
from pathlib import Path

from .environment import write_json_atomic
from .bridge.war_contract import query_war_prisoner_release_pairs_v1_step


SUBMIT_STEP = "private-submit-player-prisoner-ransom-v1"
RECEIPT_STEP = "private-read-player-prisoner-ransom-receipt-v1"
_LEDGER = "player-prisoner-ransom-formal-v1.json"


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def read_ransom_ledger(state_dir: Path) -> dict[str, object]:
    path = state_dir / _LEDGER
    if not path.exists():
        return {"schema": "xar.ck3.prisoner-ransom-formal.v1",
                "pending": None, "resolved": None}
    value = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(value, dict)
            or value.get("schema") != "xar.ck3.prisoner-ransom-formal.v1"
            or set(value) != {"schema", "pending", "resolved"}
            or any(value[key] is not None and not isinstance(value[key], dict)
                   for key in ("pending", "resolved"))):
        raise ValueError("prisoner ransom ledger is malformed")
    return value


def _write(state_dir: Path, ledger: Mapping[str, object]) -> None:
    write_json_atomic(state_dir / _LEDGER, dict(ledger))


def _frame(snapshot: Mapping[str, object]) -> tuple[int, int, int]:
    player = snapshot.get("played_character")
    native = snapshot.get("native_revision")
    date = snapshot.get("date_raw")
    if (snapshot.get("paused") is not True or snapshot.get("map_ready") is not True
            or not isinstance(player, Mapping)
            or not _positive(player.get("character_id"))
            or not _positive(native) or not _positive(date)):
        raise ValueError("ransom requires a living player in a paused map frame")
    return int(player["character_id"]), int(native), int(date)


def _collections(
    snapshot: Mapping[str, object], reads: list[dict[str, object]],
) -> list[tuple[int, dict[str, object], dict[str, object]]]:
    actor, native, date = _frame(snapshot)
    expected_ids: list[int] | None = None
    result: list[tuple[int, dict[str, object], dict[str, object]]] = []
    for index, read in enumerate(reads):
        value = read.get("player_prisoner_collection")
        if (read.get("status") != "available"
                or read.get("snapshot_revision") != native
                or not _positive(read.get("query_sequence"))
                or not isinstance(value, dict)
                or value.get("status") != "available"
                or value.get("played_character_id") != actor
                or not _positive(value.get("played_dynasty_id"))
                or value.get("date_raw") != date
                or value.get("collection_complete") is not True
                or not isinstance(value.get("prisoners"), list)):
            raise ValueError("prisoner collection does not match current frame")
        rows = value["prisoners"]
        ids = [row.get("prisoner_character_id") for row in rows]
        if (any(not _positive(identity) for identity in ids)
                or len(set(ids)) != len(ids)
                or expected_ids is not None and ids != expected_ids
                or index >= len(rows)):
            raise ValueError("prisoner collection identity drifted")
        expected_ids = ids
        row = rows[index]
        if (row.get("source_ordinal") != index
                or row.get("jailer_character_id") != actor
                or row.get("custody_relation_verified") is not True):
            raise ValueError("prisoner custody did not bind to the player")
        result.append((index, read, row))
    if expected_ids is None or len(reads) != len(expected_ids):
        raise ValueError("ransom requires one exact quote read per prisoner")
    return result


def _war_uncommitted(
    snapshot: Mapping[str, object], prisoner_id: int,
    war_reads: list[dict[str, object]],
) -> bool:
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or len(wars) != len(war_reads):
        return False
    _, native, date = _frame(snapshot)
    for war, read in zip(wars, war_reads, strict=True):
        proof = read.get("war_prisoner_release_pairs_proof")
        if (not isinstance(war, Mapping) or not isinstance(proof, Mapping)
                or read.get("snapshot_revision") != native
                or proof.get("war_id") != war.get("war_id")
                or proof.get("date_raw") != date
                or proof.get("same_frame_stable") is not True
                or proof.get("full_participant_scan") is not True
                or proof.get("primary_and_first_three_successors_scanned") is not True
                or proof.get("active_casus_belli_key") == "fp3_free_house_member_cb"
                or not isinstance(proof.get("release_pairs"), list)
                or not isinstance(proof.get("attacker_release_candidate_ids"), list)
                or not isinstance(proof.get("defender_release_candidate_ids"), list)):
            return False
        if (prisoner_id in proof["attacker_release_candidate_ids"]
                or prisoner_id in proof["defender_release_candidate_ids"]
                or any(isinstance(pair, Mapping)
                       and pair.get("prisoner_character_id") == prisoner_id
                       for pair in proof["release_pairs"])):
            return False
    return True


def select_ransom_candidate(
    snapshot: Mapping[str, object], reads: list[dict[str, object]],
    war_reads: list[dict[str, object]],
) -> dict[str, object] | None:
    """Prefer a positive ordinary-gold offer for a landless outside-dynasty prisoner."""
    actor, native, date = _frame(snapshot)
    choices: list[dict[str, object]] = []
    for ordinal, read, row in _collections(snapshot, reads):
        quote = row.get("ransom_quote_preview")
        prisoner_id = row["prisoner_character_id"]
        if (not isinstance(quote, Mapping)
                or quote.get("status") != "available"
                or quote.get("definition_key") != "ransom_interaction"
                or quote.get("jailer_character_id") != actor
                or quote.get("prisoner_character_id") != prisoner_id
                or quote.get("native_revision") != native
                or quote.get("date_raw") != date
                or quote.get("selected_option") != "gold"
                or quote.get("can_send") is not True
                or quote.get("would_accept_now") is not True
                or quote.get("recipient_answer_status_raw") not in (0, 1)
                or not _positive(quote.get("quoted_gold_raw"))
                or quote.get("raw_scale") != 100_000
                or row.get("primary_title_tier_raw") is not None
                or row.get("same_dynasty") is not False
                or row.get("is_child_of_played_character") is not False
                or not _war_uncommitted(snapshot, prisoner_id, war_reads)):
            continue
        choices.append({"source_ordinal": ordinal,
                        "prisoner_character_id": prisoner_id,
                        "payer_character_id": quote["payer_character_id"],
                        "quoted_gold_raw": quote["quoted_gold_raw"],
                        "selected_option": "gold", "collection": read})
    return max(choices, key=lambda row: (row["quoted_gold_raw"],
                                          -row["prisoner_character_id"])) if choices else None


def plan_ransom_private(
    driver: object, planned: dict[str, object],
    snapshot: Mapping[str, object],
) -> dict[str, object]:
    plan = planned.get("plan")
    if not isinstance(plan, dict):
        return planned
    if getattr(driver, "allow_private_prisoner_ransom_action", False) is not True:
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise ValueError("formal ransom requires managed state_dir")
    ledger = read_ransom_ledger(state_dir)
    pending = ledger["pending"]
    _, native, date = _frame(snapshot)
    if isinstance(pending, dict):
        if (pending.get("last_checked_native_revision") != native
                and (native != pending.get("pre_native_revision")
                     or date != pending.get("pre_date_raw"))):
            return {**planned, "plan": {**plan,
                "phase": "prisoner_ransom_material_read",
                "selected_step": RECEIPT_STEP,
                "prisoner_ransom_pending": pending}}
        return planned
    baseline_step = plan.get("selected_step")
    if (not (baseline_step == "life-advance"
             or isinstance(baseline_step, str)
             and baseline_step.startswith("advance-route-contact-horizon-v1-"))
            or snapshot.get("active_event") is not None
            or snapshot.get("pending_character_interaction") is not None):
        return planned
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list):
        return planned
    try:
        war_reads = [driver.execute_step(
            query_war_prisoner_release_pairs_v1_step(war["war_id"]),
            expected_revision=snapshot["revision"])
            for war in wars]
        first = driver.query_player_prisoner_collection_private_v1(
            expected_revision=snapshot["revision"], ransom_ordinal=0)
        value = first["player_prisoner_collection"]
        count = value["returned_count"]
        if type(count) is not int or not 0 <= count <= 64:
            raise ValueError("prisoner collection count is invalid")
        reads = [first] + [driver.query_player_prisoner_collection_private_v1(
            expected_revision=snapshot["revision"], ransom_ordinal=i)
            for i in range(1, count)]
        choice = select_ransom_candidate(snapshot, reads, war_reads)
        if choice is None:
            return planned
        # The native bridge stores only its most recent quote. Re-read the
        # chosen ordinal immediately before exposing the typed submit step.
        latest = driver.query_player_prisoner_collection_private_v1(
            expected_revision=snapshot["revision"],
            ransom_ordinal=choice["source_ordinal"])
        current_reads = list(reads)
        current_reads[choice["source_ordinal"]] = latest
        refreshed = select_ransom_candidate(snapshot, current_reads, war_reads)
        if (refreshed is None
                or refreshed["prisoner_character_id"] != choice["prisoner_character_id"]
                or refreshed["quoted_gold_raw"] != choice["quoted_gold_raw"]):
            raise ValueError("chosen ransom offer changed before submit")
    except (KeyError, TypeError, ValueError) as error:
        return {**planned, "plan": {**plan,
            "prisoner_ransom_observation": {"status": "unavailable",
                                            "reason": str(error)}}}
    return {**planned, "plan": {**plan,
        "phase": "prisoner_ransom_typed_submit",
        "selected_step": SUBMIT_STEP,
        "prisoner_ransom_choice": refreshed,
        "prisoner_ransom_war_reads": copy.deepcopy(war_reads)}}


def submit_ransom_private(driver: object, *, plan: Mapping[str, object]) -> dict[str, object]:
    choice = plan.get("prisoner_ransom_choice")
    if not isinstance(choice, Mapping):
        raise ValueError("formal ransom lacks a typed chosen offer")
    state_dir = driver.state_dir
    ledger = read_ransom_ledger(state_dir)
    if ledger["pending"] is not None:
        raise ValueError("another prisoner ransom is unresolved")
    before = driver.take_snapshot()
    actor, native, date = _frame(before)
    gold = before.get("played_character_gold")
    if (not isinstance(gold, Mapping) or type(gold.get("raw")) is not int
            or gold.get("scale") != 100_000):
        raise ValueError("player gold baseline is unavailable")
    collection = choice.get("collection")
    if not isinstance(collection, dict):
        raise ValueError("chosen ransom collection is missing")
    pending = {"stage": "submission_unresolved",
               "pre_native_revision": native, "pre_date_raw": date,
               "player_character_id": actor,
               "prisoner_character_id": choice["prisoner_character_id"],
               "payer_character_id": choice["payer_character_id"],
               "selected_option": choice["selected_option"],
               "quoted_gold_raw": choice["quoted_gold_raw"],
               "pre_player_gold_raw": gold["raw"],
               "last_checked_native_revision": None}
    _write(state_dir, {**ledger, "pending": pending})
    result = driver.submit_player_prisoner_ransom_private_v1(
        collection=collection, prisoner_character_id=choice["prisoner_character_id"])
    if (result.get("status") != "submitted_verification_pending"
            or result.get("material_result") is not False
            or result.get("pre_native_revision") != native):
        raise ValueError("native ransom submit lacks pending-only ACK")
    pending.update({"stage": "receipt_pending", "action_ack": result})
    _write(state_dir, {**ledger, "pending": pending})
    return pending


def read_ransom_receipt_private(driver: object, *, pending: Mapping[str, object]) -> dict[str, object]:
    state_dir = driver.state_dir
    ledger = read_ransom_ledger(state_dir)
    if ledger["pending"] != dict(pending):
        raise ValueError("ransom pending identity differs from ledger")
    now = driver.take_snapshot()
    actor, native, date = _frame(now)
    if actor != pending.get("player_character_id"):
        raise ValueError("ransom recovery changed played character")
    collection = driver.query_player_prisoner_collection_private_v1(
        expected_revision=now["revision"])
    value = collection.get("player_prisoner_collection")
    rows = value.get("prisoners") if isinstance(value, Mapping) else None
    gold = now.get("played_character_gold")
    if (not isinstance(rows, list)
            or value.get("collection_complete") is not True
            or value.get("played_character_id") != actor
            or value.get("date_raw") != date
            or collection.get("snapshot_revision") != native
            or not isinstance(gold, Mapping)
            or type(gold.get("raw")) is not int
            or gold.get("scale") != 100_000):
        raise ValueError("independent prisoner or gold postcondition is unavailable")
    held = any(row.get("prisoner_character_id") ==
               pending["prisoner_character_id"] for row in rows)
    gain = gold["raw"] - pending["pre_player_gold_raw"]
    applied = not held and gain >= pending["quoted_gold_raw"]
    result = {"status": "applied" if applied else "pending" if held else "ambiguous",
              "material_result": applied,
              "postcondition_verified": applied,
              "prisoner_no_longer_held": not held,
              "observed_player_gold_gain_raw": gain,
              "quoted_gold_raw": pending["quoted_gold_raw"],
              "post_native_revision": native,
              "post_date_raw": date,
              "source_pending": dict(pending)}
    if applied:
        _write(state_dir, {**ledger, "pending": None, "resolved": result})
    else:
        updated = {**pending, "last_checked_native_revision": native}
        _write(state_dir, {**ledger, "pending": updated})
    return result

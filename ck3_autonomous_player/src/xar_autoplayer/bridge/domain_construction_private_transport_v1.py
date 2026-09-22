"""Private exact-build construction query, one-shot submit, material read.

The native step is intentionally neither registered nor advertised publicly.
The Python pre-submit ledger is written before touching the native receiver.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping
import uuid

from ..construction_formal_consumer import (
    read_construction_ledger, write_construction_ledger,
)
from ..runtime import _process_identity
from .driver import BridgeUnavailableError, StepPostconditionError


QUERY_NATIVE = "g2_player_construction_view_probe_v1"
ACTION_NATIVE = "g2_player_world_building_action_private_v1"
SUBMIT_STEP = "private-submit-player-construction-v1"
RECEIPT_STEP = "private-query-player-construction-receipt-v1"
RESERVE_RAW = 20_000_000
TUPLE_KEYS = ("barony_title_id", "province_id", "building_type_id", "slot_index")


def _positive(value: object) -> bool:
    return type(value) is int and value > 0


def _identity(driver: object) -> tuple[int, str]:
    pid = getattr(driver, "_session_bridge_pid", None)
    identity = _process_identity(pid) if _positive(pid) else None
    creation = identity.get("creation_date") if isinstance(identity, Mapping) else None
    if not isinstance(creation, str) or not creation:
        raise BridgeUnavailableError("construction trial lacks a live exact process identity")
    return pid, creation


def _binding(driver: object, *, expected_revision: int) -> dict[str, object]:
    snapshot = driver.take_snapshot()
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    if not (snapshot.get("paused") is True
            and snapshot.get("map_ready") is True
            and snapshot.get("active_event") is None
            and snapshot.get("pending_character_interaction") is None
            and snapshot.get("active_wars") == []
            and snapshot.get("player_armies") == []
            and _positive(actor) and played.get("alive") is True
            and _positive(snapshot.get("native_revision"))
            and snapshot.get("snapshot_id") == f"native:{snapshot['native_revision']}"
            and snapshot.get("revision") == expected_revision
            and type(snapshot.get("date_raw")) is int
            and isinstance(snapshot.get("episode_run_id"), str)):
        raise BridgeUnavailableError("construction trial lacks a stable peaceful paused actor frame")
    return snapshot


def _send(driver: object, step: str, revision: int, request_id: str) -> dict[str, object]:
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step, "expected_revision": revision,
    })
    frame = driver.state.wait_for_command_result(
        request_id, driver.command_timeout_seconds
    )
    if not (isinstance(frame, Mapping)
            and frame.get("type") == "command_result"
            and frame.get("protocol_version") == 1
            and frame.get("request_id") == request_id
            and frame.get("ok") is True
            and isinstance(frame.get("result"), Mapping)):
        raise BridgeUnavailableError(f"{step} native result missing/rejected; keep action pending if submitted")
    return dict(frame["result"])


def _candidate(world: Mapping[str, object]) -> dict[str, object] | None:
    gold = world.get("player_gold_raw")
    active = world.get("active_constructions")
    samples = world.get("legal_samples")
    if not (type(gold) is int and isinstance(active, list)
            and isinstance(samples, list)):
        return None
    idle = {(row.get("barony_title_id"), row.get("province_id"))
            for row in active if isinstance(row, Mapping) and row.get("active") is False}
    choices = []
    for row in samples:
        if not isinstance(row, Mapping) or not all(_positive(row.get(k)) for k in TUPLE_KEYS[:3]):
            continue
        costs = row.get("cost_raw_native")
        if not (type(row.get("slot_index")) is int and row["slot_index"] >= 0
                and row.get("native_cost_observed") is True
                and isinstance(costs, list) and len(costs) == 10
                and all(type(cost) is int for cost in costs)
                and costs[0] > 0 and all(cost == 0 for cost in costs[1:])
                and (row["barony_title_id"], row["province_id"]) in idle
                and costs[0] < gold and gold - costs[0] >= RESERVE_RAW):
            continue
        choices.append((costs[0], *(row[k] for k in TUPLE_KEYS)))
    if not choices:
        return None
    cost, *identifiers = min(choices)
    return {**dict(zip(TUPLE_KEYS, identifiers)), "stock_gold_cost_raw": cost,
            "gold_before_raw": gold}


def query_construction_private(driver: object, *, expected_revision: int,
                               material_receipt: bool = False) -> dict[str, object]:
    starting = _binding(driver, expected_revision=expected_revision)
    revision = starting["native_revision"]
    request_id = f"construction-read-{uuid.uuid4().hex}"
    result = _send(driver, QUERY_NATIVE, revision, request_id)
    probe = result.get("private_probe")
    world = probe.get("player_world_building_sources") if isinstance(probe, Mapping) else None
    ending = driver.take_snapshot()
    if not (result.get("step") == QUERY_NATIVE and result.get("accepted") is True
            and isinstance(probe, Mapping) and probe.get("advertised") is False
            and probe.get("snapshot_revision") == revision
            and probe.get("date_raw") == starting["date_raw"]
            and isinstance(world, Mapping) and world.get("status") == "source_available"
            and world.get("snapshot_revision") == revision
            and world.get("date_raw") == starting["date_raw"]
            and world.get("player_character_id") == starting["played_character"]["character_id"]
            and world.get("native_final_legality_evaluated") is True
            and (world.get("native_cost_evaluated") is True
                 or (material_receipt and world.get("native_cost_evaluated") is False))
            and type(world.get("player_gold_raw")) is int
            and world["player_gold_raw"] >= 0
            and isinstance(world.get("active_constructions"), list)
            and isinstance(world.get("legal_samples"), list)
            and all(isinstance(row, Mapping)
                    and row.get("native_cost_observed") is True
                    and isinstance(row.get("cost_raw_native"), list)
                    and len(row["cost_raw_native"]) == 10
                    for row in world["legal_samples"])
            and _positive(probe.get("proof_epoch"))
            and ending.get("snapshot_id") == starting["snapshot_id"]
            and ending.get("revision") == starting["revision"]
            and ending.get("episode_run_id") == starting["episode_run_id"]):
        return {"status": "source_red", "native_result": result,
                "native_query_request_id": request_id,
                "source_frame": {"snapshot_id": starting["snapshot_id"],
                                 "revision": starting["revision"],
                                 "native_revision": revision,
                                 "date_raw": starting["date_raw"],
                                 "episode_run_id": starting["episode_run_id"],
                                 "actor_character_id": starting["played_character"]["character_id"]},
                "ending_frame": {"snapshot_id": ending.get("snapshot_id"),
                                 "revision": ending.get("revision"),
                                 "episode_run_id": ending.get("episode_run_id")}}
    if material_receipt:
        # A submitted building can remove every legal new candidate.  Its
        # independent active-construction row is material evidence even when
        # this frame has no new cost sample; never use this mode to submit.
        return {"status": "material_source", "world": dict(world),
                "proof_epoch": probe["proof_epoch"],
                "source_frame": {"snapshot_id": starting["snapshot_id"],
                                 "revision": expected_revision,
                                 "native_revision": revision,
                                 "date_raw": starting["date_raw"],
                                 "episode_run_id": starting["episode_run_id"],
                                 "actor_character_id": starting["played_character"]["character_id"]}}
    selected = _candidate(world)
    if selected is None:
        return {"status": "no_legal_budgeted_building", "world": dict(world),
                "proof_epoch": probe["proof_epoch"], "source_frame": {
            "revision": expected_revision, "native_revision": revision,
            "episode_run_id": starting["episode_run_id"]}}
    return {"status": "selected", "candidate": selected, "world": dict(world),
            "proof_epoch": probe["proof_epoch"],
            "source_frame": {"snapshot_id": starting["snapshot_id"],
                             "revision": expected_revision, "native_revision": revision,
                             "date_raw": starting["date_raw"],
                             "episode_run_id": starting["episode_run_id"],
                             "actor_character_id": starting["played_character"]["character_id"]}}


def submit_construction_private(driver: object, *, query: Mapping[str, object],
                                expected_revision: int) -> dict[str, object]:
    source = query.get("source_frame")
    candidate = query.get("candidate")
    starting = _binding(driver, expected_revision=expected_revision)
    state_dir = getattr(driver, "state_dir", None)
    if not (isinstance(state_dir, Path) and isinstance(source, Mapping)
            and isinstance(candidate, Mapping) and query.get("status") == "selected"
            and source.get("snapshot_id") == starting["snapshot_id"]
            and source.get("revision") == expected_revision
            and source.get("native_revision") == starting["native_revision"]
            and source.get("episode_run_id") == starting["episode_run_id"]
            and source.get("date_raw") == starting["date_raw"]
            and source.get("actor_character_id") == starting["played_character"]["character_id"]):
        raise BridgeUnavailableError("construction pre-submit frame changed; no native send")
    ledger = read_construction_ledger(state_dir)
    if ledger["pending"] is not None or (isinstance(ledger["applied"], dict)
                                         and ledger["applied"].get("episode_run_id") == starting["episode_run_id"]):
        raise BridgeUnavailableError("construction already pending or applied; no duplicate send")
    pid, creation = _identity(driver)
    request_id = f"construction-submit-{uuid.uuid4().hex}"
    pending = {"status": "action_state_unknown", "action_request_id": request_id,
               "episode_run_id": starting["episode_run_id"],
               "actor_character_id": source["actor_character_id"],
               "pre_native_revision": source["native_revision"],
               "pre_public_revision": expected_revision,
               "pre_date_raw": source["date_raw"],
               "pre_proof_epoch": query["proof_epoch"],
               "source_bridge_pid": pid, "source_bridge_creation_date": creation,
               "candidate": dict(candidate)}
    write_construction_ledger(state_dir, {**ledger, "pending": pending})
    driver._record_command(SUBMIT_STEP, ok=True, result=pending)
    if getattr(driver, "_driver_state_error", None) is not None:
        raise BridgeUnavailableError("construction intent not durable; no native send")
    try:
        result = _send(driver, ACTION_NATIVE, source["native_revision"], request_id)
    except Exception as error:
        raise StepPostconditionError("construction native submit uncertain; query state before retry",
                                     selected_step=SUBMIT_STEP, step_result=pending) from error
    probe = result.get("private_probe")
    ack = probe.get("private_action") if isinstance(probe, Mapping) else None
    if not (result.get("step") == ACTION_NATIVE and result.get("accepted") is True
            and isinstance(ack, Mapping) and ack.get("status") == "pending_receipt"
            and ack.get("applied") is False and ack.get("advertised") is False
            and ack.get("production_native_path") is True
            and ack.get("validator_calls") == ack.get("materialize_calls")
            == ack.get("receiver_calls") == 1
            and _positive(ack.get("receiver_command_sequence"))
            and _positive(ack.get("proof_epoch"))
            and ack["proof_epoch"] > pending["pre_proof_epoch"]
            and ack.get("actor_character_id") == pending["actor_character_id"]
            and all(ack.get(key) == candidate.get(key) for key in (*TUPLE_KEYS,
                                                                   "stock_gold_cost_raw", "gold_before_raw"))):
        raise StepPostconditionError("construction ACK unknown; preserve pending action",
                                     selected_step=SUBMIT_STEP, step_result=pending)
    pending = {**pending, "status": "submitted_verification_pending",
               "pre_proof_epoch": ack["proof_epoch"],
               "native_ack": dict(ack)}
    write_construction_ledger(state_dir, {**ledger, "pending": pending})
    driver._record_command(SUBMIT_STEP, ok=True, result=pending)
    return pending


def query_construction_receipt(driver: object, *, pending: Mapping[str, object],
                               expected_revision: int) -> dict[str, object]:
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        raise BridgeUnavailableError("construction receipt lacks durable state_dir")
    ledger = read_construction_ledger(state_dir)
    unresolved = isinstance(ledger["pending"], dict) and (
        ledger["pending"].get("action_request_id") == pending.get("action_request_id"))
    cold_recheck = ledger["pending"] is None and isinstance(ledger["applied"], dict) and (
        ledger["applied"].get("action_request_id") == pending.get("action_request_id"))
    if not (unresolved or cold_recheck):
        raise BridgeUnavailableError("construction receipt lacks matching pending action")
    starting = _binding(driver, expected_revision=expected_revision)
    pid, creation = _identity(driver)
    same_process = ((pid, creation) == (pending.get("source_bridge_pid"),
                                       pending.get("source_bridge_creation_date")))
    if cold_recheck and (pid, creation) == (
            pending.get("post_bridge_pid"), pending.get("post_bridge_creation_date")):
        raise BridgeUnavailableError("construction cold requery requires a replacement process")
    if (starting.get("episode_run_id") != pending.get("episode_run_id")
            or starting["played_character"]["character_id"] != pending.get("actor_character_id")
            or starting["date_raw"] < pending.get("pre_date_raw", 0)
            or (same_process and starting["native_revision"] <= pending["pre_native_revision"])):
        raise BridgeUnavailableError("construction receipt requires a later paused actor frame")
    query = query_construction_private(
        driver, expected_revision=expected_revision, material_receipt=True)
    if query.get("status") != "material_source":
        driver._record_command(RECEIPT_STEP, ok=False, result={
            "status": "receipt_source_unavailable",
            "stage": "construction_receipt_native_source_query",
            "action_request_id": pending["action_request_id"],
            "episode_run_id": pending["episode_run_id"],
            "native_query_status": query.get("status"),
            "native_query_request_id": query.get("native_query_request_id"),
            "native_result": query.get("native_result"),
            "source_frame": query.get("source_frame"),
            "ending_frame": query.get("ending_frame"),
        })
        raise BridgeUnavailableError("construction material source unavailable; keep pending")
    # A candidate need not remain legal once construction is active. Read the
    # material source directly below via the query's private world projection.
    world = query.get("world")
    epoch = query.get("proof_epoch")
    candidate = pending.get("candidate")
    if not (isinstance(world, Mapping) and isinstance(candidate, Mapping)
            and _positive(epoch) and (not same_process or epoch > pending["pre_proof_epoch"])):
        raise BridgeUnavailableError("construction material proof unavailable; keep pending")
    active = world.get("active_constructions")
    matches = [row for row in active if isinstance(row, Mapping)
               and row.get("active") is True
               and all(row.get(key) == candidate.get(key) for key in TUPLE_KEYS)
               and row.get("initiator_character_id") == pending["actor_character_id"]] if isinstance(active, list) else []
    if not matches and cold_recheck and (
            starting["date_raw"] <= pending.get("post_date_raw", -1)
            and world.get("player_gold_raw") == candidate.get("gold_before_raw")):
        # A saved game from before the action has the original resources and
        # no matching construction. This is a real rollback, not a license
        # to resubmit an action with unknown native effect.
        classification = {"status": "restored_before_action",
            "postcondition_verified": True,
            "action_request_id": pending["action_request_id"],
            "episode_run_id": pending["episode_run_id"],
            "post_snapshot_id": starting["snapshot_id"],
            "post_public_revision": expected_revision}
        write_construction_ledger(state_dir, {**ledger, "applied": None})
        driver._record_command(RECEIPT_STEP, ok=True, result=classification)
        return classification
    if not matches:
        raise BridgeUnavailableError("construction material not yet observed; keep pending")
    receipt = {"status": "applied", "postcondition_verified": True,
               "action_request_id": pending["action_request_id"],
               "episode_run_id": pending["episode_run_id"],
               "actor_character_id": pending["actor_character_id"],
               "pre_native_revision": pending["pre_native_revision"],
               "pre_date_raw": pending["pre_date_raw"],
               "pre_proof_epoch": pending["pre_proof_epoch"],
               "source_bridge_pid": pending["source_bridge_pid"],
               "source_bridge_creation_date": pending["source_bridge_creation_date"],
               "post_snapshot_id": starting["snapshot_id"],
               "post_public_revision": expected_revision,
               "post_native_revision": starting["native_revision"],
               "post_date_raw": starting["date_raw"],
               "post_proof_epoch": epoch, "post_player_gold_raw": world.get("player_gold_raw"),
               "post_bridge_pid": pid, "post_bridge_creation_date": creation,
               "candidate": dict(candidate)}
    write_construction_ledger(state_dir, {**ledger, "pending": None, "applied": receipt})
    driver._record_command(RECEIPT_STEP, ok=True, result=receipt)
    return receipt

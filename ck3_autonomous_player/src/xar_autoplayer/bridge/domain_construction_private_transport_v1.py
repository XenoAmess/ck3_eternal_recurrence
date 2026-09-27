"""Private exact-build construction query, one-shot submit, material read.

The native step is intentionally neither registered nor advertised publicly.
The Python pre-submit ledger is written before touching the native receiver.
"""

from __future__ import annotations

from pathlib import Path
from typing import Mapping
import uuid

from ..construction_formal_consumer import (
    COMPLETION_WATCH_INTERVAL_RAW, read_construction_ledger, write_construction_ledger,
    same_frame_construction_income,
)
from ..environment import sha256_file, write_json_atomic
from ..runtime import _process_identity
from .driver import BridgeUnavailableError, StepPostconditionError
from .construction_economic_value_v1 import authored_monthly_income_hundredths


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


def _binding(driver: object, *, expected_revision: int,
             material_receipt: bool = False,
             wartime_observation: bool = False) -> dict[str, object]:
    snapshot = driver.take_snapshot()
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    if not (snapshot.get("paused") is True
            and snapshot.get("map_ready") is True
            and snapshot.get("active_event") is None
            and snapshot.get("pending_character_interaction") is None
            and isinstance(snapshot.get("active_wars"), list)
            and isinstance(snapshot.get("player_armies"), list)
            and (material_receipt or wartime_observation
                 or snapshot["active_wars"] == [])
            and (material_receipt or wartime_observation
                 or snapshot["player_armies"] == [])
            and _positive(actor) and played.get("alive") is True
            and _positive(snapshot.get("native_revision"))
            and snapshot.get("snapshot_id") == f"native:{snapshot['native_revision']}"
            and snapshot.get("revision") == expected_revision
            and type(snapshot.get("date_raw")) is int
            and isinstance(snapshot.get("episode_run_id"), str)):
        raise BridgeUnavailableError(
            "construction trial lacks a stable admitted paused actor frame")
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
        income = authored_monthly_income_hundredths(row.get("building_key"))
        if income is None or income <= 0:
            continue
        choices.append((-income, costs[0], *(row[k] for k in TUPLE_KEYS),
                        row["building_key"]))
    if not choices:
        return None
    negative_income, cost, *identity_and_key = min(choices)
    *identifiers, building_key = identity_and_key
    return {**dict(zip(TUPLE_KEYS, identifiers)), "stock_gold_cost_raw": cost,
            "gold_before_raw": gold, "building_key": building_key,
            "authored_monthly_income_hundredths": -negative_income}


def query_construction_private(driver: object, *, expected_revision: int,
                               material_receipt: bool = False,
                               wartime_observation: bool = False) -> dict[str, object]:
    if material_receipt and wartime_observation:
        raise ValueError("construction source modes cannot be combined")
    starting = _binding(driver, expected_revision=expected_revision,
                        material_receipt=material_receipt,
                        wartime_observation=wartime_observation)
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
            and ((world.get("completed_buildings_observed") is True
                  and isinstance(world.get("completed_buildings"), list))
                 or (world.get("completed_buildings_observed") is False
                     and world.get("completed_buildings") is None))
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
                "native_query_request_id": request_id,
                "proof_epoch": probe["proof_epoch"],
                "source_frame": {"snapshot_id": starting["snapshot_id"],
                                 "revision": expected_revision,
                                 "native_revision": revision,
                                 "date_raw": starting["date_raw"],
                                 "episode_run_id": starting["episode_run_id"],
                                 "actor_character_id": starting["played_character"]["character_id"]}}
    selected = _candidate(world)
    if selected is None:
        covered = world.get("positive_income_coverage_complete") is True
        return {"status": ("no_legal_budgeted_building" if covered
                           else "evidence_insufficient"),
                **({} if covered else {
                    "reason": "positive_income_candidate_coverage_incomplete"}),
                "world": dict(world),
                "native_query_request_id": request_id,
                "proof_epoch": probe["proof_epoch"], "source_frame": {
            "snapshot_id": starting["snapshot_id"],
            "revision": expected_revision, "native_revision": revision,
            "date_raw": starting["date_raw"],
            "episode_run_id": starting["episode_run_id"],
            "actor_character_id": starting["played_character"]["character_id"]}}
    return {"status": "selected", "candidate": selected, "world": dict(world),
            "native_query_request_id": request_id,
            "proof_epoch": probe["proof_epoch"],
            "source_frame": {"snapshot_id": starting["snapshot_id"],
                             "revision": expected_revision, "native_revision": revision,
                             "date_raw": starting["date_raw"],
                             "episode_run_id": starting["episode_run_id"],
                             "actor_character_id": starting["played_character"]["character_id"]}}


def query_construction_wartime_observation_private(
        driver: object, *, expected_revision: int) -> dict[str, object]:
    """Observe one native building choice while war spend remains unassessed.

    The distinct result is never a construction submit query. Native budget
    and authored income are observations; future war cash remains unknown.
    """
    snapshot = driver.take_snapshot()
    wars = snapshot.get("active_wars")
    if not isinstance(wars, list) or not wars:
        raise BridgeUnavailableError("wartime construction observation needs active war")
    source = query_construction_private(
        driver, expected_revision=expected_revision, wartime_observation=True)
    world = source.get("world")
    public_gold = snapshot.get("played_character_gold")
    gold_raw = public_gold.get("raw") if isinstance(public_gold, Mapping) else None
    source_frame = source.get("source_frame")
    played = snapshot.get("played_character")
    actor = played.get("character_id") if isinstance(played, Mapping) else None
    frame_matches = (
        isinstance(source_frame, Mapping)
        and source_frame.get("revision") == snapshot.get("revision")
        and source_frame.get("native_revision") == snapshot.get("native_revision")
        and source_frame.get("date_raw") == snapshot.get("date_raw")
        and source_frame.get("episode_run_id") == snapshot.get("episode_run_id")
        and _positive(actor)
        and source_frame.get("actor_character_id") == actor
    )
    cash_matches = (
        isinstance(world, Mapping)
        and type(gold_raw) is int and gold_raw >= 0
        and public_gold.get("scale") == 100_000
        and world.get("player_gold_raw") == gold_raw
    )
    source_status = source.get("status")
    bound = frame_matches and cash_matches
    reason = (
        "native_construction_source_validation_failed"
        if source_status == "source_red" else
        "same_frame_binding_mismatch" if not frame_matches else
        "same_frame_cash_mismatch" if not cash_matches else
        source.get("reason")
    )
    candidate = source.get("candidate") if source_status == "selected" else None
    raw_artifact: dict[str, object] = {}
    native_diagnostic: dict[str, object] | None = None
    if source_status == "source_red":
        native_result = source.get("native_result")
        probe = (native_result.get("private_probe")
                 if isinstance(native_result, Mapping) else None)
        native_world = (probe.get("player_world_building_sources")
                        if isinstance(probe, Mapping) else None)
        native_diagnostic = {
            "step": native_result.get("step") if isinstance(native_result, Mapping) else None,
            "accepted": (native_result.get("accepted")
                         if isinstance(native_result, Mapping) else None),
            "probe_status": probe.get("status") if isinstance(probe, Mapping) else None,
            "probe_snapshot_revision": (probe.get("snapshot_revision")
                                        if isinstance(probe, Mapping) else None),
            "world_status": (native_world.get("status")
                             if isinstance(native_world, Mapping) else None),
            "world_failure": (native_world.get("failure")
                              if isinstance(native_world, Mapping) else None),
            "world_snapshot_revision": (
                native_world.get("snapshot_revision")
                if isinstance(native_world, Mapping) else None),
            "world_date_raw": (native_world.get("date_raw")
                               if isinstance(native_world, Mapping) else None),
            "world_player_character_id": (
                native_world.get("player_character_id")
                if isinstance(native_world, Mapping) else None),
        }
        state_dir = getattr(driver, "state_dir", None)
        if not isinstance(state_dir, Path):
            raise BridgeUnavailableError(
                "wartime construction RED lacks durable raw artifact directory")
        request_id = source.get("native_query_request_id")
        if not isinstance(request_id, str) or not request_id.startswith("construction-read-"):
            raise BridgeUnavailableError(
                "wartime construction RED lacks native query identity")
        artifact = state_dir / "evidence" / f"{request_id}-wartime-source-red.json"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        write_json_atomic(artifact, dict(source))
        raw_artifact = {"raw_artifact_path": str(artifact.resolve()),
                        "raw_artifact_sha256": sha256_file(artifact)}
    return {
        "status": ("observed" if bound and source_status in {
            "selected", "no_legal_budgeted_building", "evidence_insufficient"}
            else "source_red"),
        "native_source_status": source_status,
        "read_only": True,
        "advertised": False,
        "formal_action_ready": False,
        "candidate": dict(candidate) if isinstance(candidate, Mapping) and bound else None,
        "native_budgeted_positive_income_candidate": (
            source_status == "selected" and bound),
        "observed_player_gold_raw": gold_raw,
        "observed_active_war_count": len(wars),
        "observed_player_army_count": (
            len(snapshot["player_armies"])
            if isinstance(snapshot.get("player_armies"), list) else None),
        "existing_shared_gold_commitment_raw": None,
        "war_future_gold_cost_raw": None,
        "joint_budget_affordability": "unassessed",
        "positive_income_coverage_complete": (
            world.get("positive_income_coverage_complete")
            if isinstance(world, Mapping) else None),
        "source_frame": dict(source_frame) if isinstance(source_frame, Mapping) else None,
        "native_query_request_id": source.get("native_query_request_id"),
        "native_proof_epoch": source.get("proof_epoch"),
        "reason": reason,
        **({"native_validation_diagnostic": native_diagnostic,
            "ending_frame": source.get("ending_frame"),
            **raw_artifact} if source_status == "source_red" else {}),
    }


def query_construction_province_income_private(
        driver: object, *, expected_revision: int,
        barony_title_id: int, province_id: int) -> dict[str, object]:
    """Read the exact paused-frame province aggregate, including after construction.

    This carries the original trigger's raw scalar without converting it to
    building-exclusive income or changing the formal construction selector.
    """
    if not (_positive(barony_title_id) and _positive(province_id)):
        raise ValueError("construction province identity must be positive integers")
    source = query_construction_private(
        driver, expected_revision=expected_revision, material_receipt=True)
    if source.get("status") != "material_source":
        return source
    world = source["world"]
    rows = [row for row in world["active_constructions"]
            if isinstance(row, Mapping)
            and row.get("barony_title_id") == barony_title_id
            and row.get("province_id") == province_id]
    if len(rows) != 1:
        return {"status": "source_red", "reason": "province_row_missing_or_duplicate",
                "source_frame": source["source_frame"]}
    row = rows[0]
    observed = row.get("native_province_monthly_income_observed")
    raw = row.get("native_province_monthly_income_raw")
    if observed is False and raw is None:
        status = "observation_unavailable"
    elif observed is True and type(raw) is int:
        status = "observed"
    else:
        return {"status": "source_red", "reason": "province_income_shape_mismatch",
                "source_frame": source["source_frame"]}
    return {"status": status, "barony_title_id": barony_title_id,
            "province_id": province_id,
            "native_province_monthly_income_observed": observed,
            "native_province_monthly_income_raw": raw,
            "source_frame": source["source_frame"]}


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
    pid, creation = _identity(driver)
    if ledger["pending"] is not None:
        raise BridgeUnavailableError("construction already pending; no duplicate send")
    applied = ledger["applied"]
    if isinstance(applied, dict) and applied.get("episode_run_id") == starting["episode_run_id"]:
        if not isinstance(applied.get("action_request_id"), str):
            raise BridgeUnavailableError(
                "construction prior receipt lacks a durable action identity")
        # The previous action is durable evidence, not a lifetime limit on
        # economic construction.  Only a later game day in the verified
        # process may spend again; a cold process is rechecked by the planner.
        if not (applied.get("status") == "applied"
                and applied.get("postcondition_verified") is True
                and applied.get("actor_character_id") == source["actor_character_id"]
                and (pid, creation) == (applied.get("post_bridge_pid"),
                                        applied.get("post_bridge_creation_date"))
                and type(applied.get("post_native_revision")) is int
                and type(applied.get("post_date_raw")) is int
                and source["native_revision"] > applied["post_native_revision"]
                and source["date_raw"] > applied["post_date_raw"]):
            raise BridgeUnavailableError("construction receipt not yet consumed on a later game day")
    request_id = f"construction-submit-{uuid.uuid4().hex}"
    history = starting.get("native_command_history")
    _, pre_income = same_frame_construction_income(
        starting, history if isinstance(history, list) else [])
    pending = {"status": "action_state_unknown", "action_request_id": request_id,
               "episode_run_id": starting["episode_run_id"],
               "actor_character_id": source["actor_character_id"],
               "pre_native_revision": source["native_revision"],
               "pre_public_revision": expected_revision,
               "pre_date_raw": source["date_raw"],
               "pre_proof_epoch": query["proof_epoch"],
               "source_bridge_pid": pid, "source_bridge_creation_date": creation,
               "pre_player_monthly_gold_income_raw": pre_income,
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
    prior = ledger.get("applied_prior", [])
    cold_recheck = ledger["pending"] is None and (
        (isinstance(ledger["applied"], dict)
         and ledger["applied"].get("action_request_id") == pending.get("action_request_id"))
        or any(isinstance(row, dict) and row.get("action_request_id") ==
               pending.get("action_request_id") for row in prior))
    if not (unresolved or cold_recheck):
        raise BridgeUnavailableError("construction receipt lacks matching pending action")
    starting = _binding(driver, expected_revision=expected_revision,
                        material_receipt=True)
    pid, creation = _identity(driver)
    same_process = ((pid, creation) == (pending.get("source_bridge_pid"),
                                       pending.get("source_bridge_creation_date")))
    completion_watch = (cold_recheck and (pid, creation) == (
        pending.get("post_bridge_pid"), pending.get("post_bridge_creation_date"))
        and starting.get("date_raw", -1) > pending.get("post_date_raw", -1))
    if completion_watch and pending.get("completion_status") != "completed" and not (
            type(starting.get("date_raw")) is int
            and starting["date_raw"] > pending.get("post_date_raw", 0)
            and starting["date_raw"] >= pending.get(
                "completion_last_check_date_raw", pending.get("post_date_raw", 0))
            + COMPLETION_WATCH_INTERVAL_RAW):
        raise BridgeUnavailableError("construction completion watch needs a later monthly frame")
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
    built = world.get("completed_buildings")
    completed = [row for row in built if isinstance(row, Mapping)
                 and all(row.get(key) == candidate.get(key) for key in TUPLE_KEYS)] if isinstance(built, list) else []
    if matches and completed:
        raise BridgeUnavailableError("construction active and completed tuple conflict")
    if matches and starting["date_raw"] == pending["pre_date_raw"]:
        # On the action date, the native active row and exact gold spend are
        # independent material postconditions. Completed slots can remain
        # unreadable without weakening this start receipt.
        before = candidate.get("gold_before_raw")
        cost = candidate.get("stock_gold_cost_raw")
        if (type(before) is not int or type(cost) is not int or cost <= 0
                or world["player_gold_raw"] != before - cost):
            raise BridgeUnavailableError(
                "construction same-date gold spend not verified; keep pending")
    if not matches and not completed and cold_recheck and (
            world.get("completed_buildings_observed") is True
            and starting["date_raw"] <= pending.get("post_date_raw", -1)
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
        if (isinstance(ledger["applied"], dict)
                and ledger["applied"].get("action_request_id") ==
                pending["action_request_id"]):
            write_construction_ledger(state_dir, {**ledger, "applied": None})
        else:
            write_construction_ledger(state_dir, {**ledger,
                "applied_prior": [row for row in prior
                                  if row.get("action_request_id") !=
                                  pending["action_request_id"]]})
        driver._record_command(RECEIPT_STEP, ok=True, result=classification)
        return classification
    if not matches and not completed:
        raise BridgeUnavailableError("construction material not yet observed; keep pending")
    # The native row carries work and divisor on this same paused material
    # frame. Keep the raw values with the receipt so a later paired run can
    # compare progress without inferring a finish date from authored time.
    progress_row = matches[0] if matches else None
    remaining_work = (progress_row.get("native_remaining_work_raw")
                      if progress_row is not None else None)
    progress_divisor = (progress_row.get("native_progress_divisor_raw")
                        if progress_row is not None else None)
    progress_observation = {
        "status": ("observed" if type(remaining_work) is int
                   and type(progress_divisor) is int else
                   "unavailable" if progress_row is not None else "not_active"),
        "snapshot_id": starting["snapshot_id"],
        "native_revision": starting["native_revision"],
        "date_raw": starting["date_raw"],
        "native_remaining_work_raw": (remaining_work
                                       if type(remaining_work) is int else None),
        "native_progress_divisor_raw": (progress_divisor
                                        if type(progress_divisor) is int else None),
    }
    history = starting.get("native_command_history")
    _, observed_income = same_frame_construction_income(
        starting, history if isinstance(history, list) else [])
    pre_income = pending.get("pre_player_monthly_gold_income_raw")
    income_observed_date = starting["date_raw"] if type(observed_income) is int else None
    if (cold_recheck and completed and observed_income is None
            and pending.get("completion_status") == "completed"):
        # A cold material recheck must not erase a previously observed income
        # just because this paused frame has not queried the public root yet.
        observed_income = pending.get("observed_player_monthly_gold_income_raw")
        if type(observed_income) is int:
            income_observed_date = pending.get(
                "income_observed_date_raw", pending.get("post_date_raw"))
    receipt = {"status": "applied", "postcondition_verified": True,
               "completion_status": "completed" if completed else "in_progress",
               "construction_progress_observation": progress_observation,
               "completion_last_check_date_raw": starting["date_raw"],
               "completion_observed_date_raw": (
                   starting["date_raw"] if completed else None),
               "pre_player_monthly_gold_income_raw": pre_income,
               "observed_player_monthly_gold_income_raw": observed_income,
               "income_observed_date_raw": income_observed_date,
               "observed_player_monthly_income_delta_raw": (
                   observed_income - pre_income if completed and
                   type(observed_income) is int and type(pre_income) is int
                   else None),
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
    if cold_recheck:
        # Preserve the original action proof, including its earlier active
        # receipt. A completed slot is a distinct later material observation.
        receipt = {**dict(pending), **receipt,
                   "start_receipt": pending.get("start_receipt", dict(pending)),
                   "completion_observed_date_raw": (
                       pending.get("completion_observed_date_raw") or starting["date_raw"]
                       if completed else pending.get("completion_observed_date_raw"))}
    prior = list(ledger.get("applied_prior", []))
    if cold_recheck:
        current = ledger["applied"]
        if isinstance(current, dict) and current.get("action_request_id") == (
                pending["action_request_id"]):
            write_construction_ledger(state_dir, {**ledger, "pending": None,
                                                  "applied": receipt})
        else:
            match_indices = [index for index, row in enumerate(prior)
                             if row.get("action_request_id") ==
                             pending["action_request_id"]]
            if len(match_indices) != 1:
                raise BridgeUnavailableError(
                    "construction prior receipt identity changed; keep pending")
            prior[match_indices[0]] = receipt
            write_construction_ledger(state_dir, {**ledger, "pending": None,
                                                  "applied_prior": prior})
    else:
        previous = ledger["applied"]
        if isinstance(previous, dict) and (
                previous.get("completion_status") != "completed"
                or previous.get("observed_player_monthly_gold_income_raw") is None):
            prior.append(previous)
        write_construction_ledger(state_dir, {**ledger, "pending": None,
                                              "applied": receipt,
                                              "applied_prior": prior})
    driver._record_command(RECEIPT_STEP, ok=True, result=receipt)
    return receipt

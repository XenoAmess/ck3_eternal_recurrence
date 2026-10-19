"""Controlled formal route for one exact-build faction mitigation gift.

This module owns the durable pending identity before native submit, then
routes a same-process receipt or an independent cold-process fact read. The
opt-in private MCP tools reuse these functions; ordinary planning keeps its
existing separate opt-in. Missing facts never authorize a duplicate gift.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Mapping, Sequence
import uuid

from ..faction_gift_formal_candidate_v1 import (
    ROOT_STEP,
    latest_same_frame_faction_root_v1,
)
from ..faction_gift_pending_v1 import (
    begin_faction_gift_submission_v1,
    complete_faction_gift_after_independent_receipt_v1,
    mark_faction_gift_ack_pending_v1,
    mark_faction_gift_restore_requery_v1,
    read_faction_gift_ledger_v1,
    resolve_faction_gift_after_cold_native_query_v1,
)
from ..faction_threat_response_inputs_v1 import (
    observe_faction_gift_stock_threat_v1,
)
from ..runtime import _process_identity
from ..environment import process_creation_utc, same_process_creation_time
from .driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
)


SUBMIT_STEP = "private-submit-faction-gift-member-v1"
RECEIPT_STEP = "private-query-faction-gift-receipt-v1"
COLD_RECOVERY_STEP = "private-query-faction-gift-cold-recovery-v1"
MINIMUM_GOLD_RESERVE_RAW = 10_000_000


class FactionGiftPendingFrameReadyError(PreSubmissionRevisionMismatchError):
    """A receipt-only planner wait observed a fresh, still-owned paused frame."""

    def __init__(self, proof: Mapping[str, object]) -> None:
        super().__init__("private faction pending receipt has a newer same-date paused frame")
        self.readonly_faction_pending_frame_v1 = copy.deepcopy(dict(proof))


def _pending_receipt_frame(snapshot: Mapping[str, object]) -> dict[str, object]:
    actor = snapshot.get("played_character")
    diagnostics = snapshot.get("diagnostics")
    return {
        "public_revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "episode_run_id": snapshot.get("episode_run_id"),
        "actor_character_id": actor.get("character_id") if isinstance(actor, Mapping) else None,
        "actor_alive": actor.get("alive") if isinstance(actor, Mapping) else None,
        "paused": snapshot.get("paused"), "map_ready": snapshot.get("map_ready"),
        "active_event_absent": snapshot.get("active_event") is None,
        "pending_interaction_absent": snapshot.get("pending_character_interaction") is None,
        "bridge_pid": diagnostics.get("bridge_pid") if isinstance(diagnostics, Mapping) else None,
        "connection_generation": (diagnostics.get("connection_generation")
                                  if isinstance(diagnostics, Mapping) else None),
    }


def _positive(value: object) -> int | None:
    return value if type(value) is int and value > 0 else None


def _runtime_identity(driver: object) -> tuple[int, str]:
    pid = getattr(driver, "_session_bridge_pid", None)
    if _positive(pid) is None:
        raise BridgeUnavailableError("private faction route lacks a live bridge PID")
    identity = _process_identity(pid)
    creation = identity.get("creation_date") if isinstance(identity, Mapping) else None
    if not isinstance(creation, str) or not creation or creation in {"None", "null"}:
        raise BridgeUnavailableError("private faction route lacks exact CK3 process identity")
    return pid, creation


def _same_pending_process(pid: int, creation: str, pending: Mapping[str, object]) -> bool:
    """Keep raw evidence while comparing supported Windows birth encodings.

    Exact historic spellings remain compatible. Unequal, unparseable birth
    strings are unknown: they cannot authorize the cold recovery path.
    """
    source_pid, source_creation = pending.get("source_bridge_pid"), pending.get("source_bridge_creation_date")
    if (not isinstance(creation, str) or not creation or creation in {"None", "null"}
            or not isinstance(source_creation, str) or not source_creation
            or source_creation in {"None", "null"}):
        raise BridgeUnavailableError("private faction process birth comparison is unknown")
    if (pid == source_pid and isinstance(source_creation, str) and source_creation
            and creation == source_creation):
        return True
    if same_process_creation_time(creation, source_creation):
        return pid == source_pid
    try:
        process_creation_utc(creation)
        process_creation_utc(source_creation)
    except (TypeError, ValueError, OverflowError) as error:
        raise BridgeUnavailableError("private faction process birth comparison is unknown") from error
    return False


def _current_checkpoint(driver: object, snapshot: Mapping[str, object]) -> dict[str, object] | None:
    lock = getattr(driver, "_driver_state_lock", None)
    if lock is None:
        return None
    with lock:
        candidate = copy.deepcopy(getattr(driver, "_last_checkpoint", None))
    if not isinstance(candidate, dict):
        return None
    digest = candidate.get("sha256")
    if not (
        candidate.get("status") == "saved"
        and isinstance(digest, str) and len(digest) == 64
        and candidate.get("date_raw") == snapshot.get("date_raw")
        and candidate.get("episode_run_id") == snapshot.get("episode_run_id")
    ):
        return None
    return candidate


def _send(driver: object, step: str, fields: Mapping[str, object], timeout_seconds: float = 30.0) -> dict[str, object]:
    request_id = fields.get("request_id")
    if not isinstance(request_id, str) or not request_id:
        request_id = "faction-gift-" + uuid.uuid4().hex
    driver.endpoint.send({
        "type": "execute_step", "protocol_version": 1,
        "request_id": request_id, "step": step, **dict(fields),
    })
    frame = driver.state.wait_for_command_result(request_id, timeout_seconds)
    if frame is None:
        raise BridgeUnavailableError(f"{step} command_result timed out")
    if not (
        frame.get("type") == "command_result"
        and frame.get("protocol_version") == 1
        and frame.get("request_id") == request_id
        and frame.get("ok") is True
        and isinstance(frame.get("result"), Mapping)
    ):
        error = str(frame.get("error") or "malformed private command result")
        failure = BridgeUnavailableError(f"{step} failed: {error}")
        failure.native_error = error
        raise failure
    return dict(frame["result"])


def _wait_for_pending_paused_revision_v1(
    driver: object, snapshot: Mapping[str, object], pending: Mapping[str, object],
) -> None:
    """Use the native driver's existing bounded snapshot wait, then replan."""
    waiter = getattr(driver, "_wait_for_snapshot", None)
    if not callable(waiter):
        raise BridgeUnavailableError("private faction pending frame has no bounded native wait")
    old_revision = snapshot.get("revision")
    pre_revision = pending.get("pre_native_snapshot_revision")
    source_actor = snapshot.get("played_character")
    source_diagnostics = snapshot.get("diagnostics")
    if not (
        type(old_revision) is int and old_revision > 0
        and type(pre_revision) is int and pre_revision > 0
        and type(snapshot.get("native_revision")) is int
        and 0 < snapshot["native_revision"] <= pre_revision
        and snapshot.get("date_raw") == pending.get("pre_date_raw")
        and snapshot.get("episode_run_id") == pending.get("episode_run_id")
        and isinstance(source_actor, Mapping)
        and source_actor.get("character_id") == pending.get("pre_player_character_id")
        and source_actor.get("alive") is True
        and snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and snapshot.get("active_event") is None
        and snapshot.get("pending_character_interaction") is None
        and isinstance(source_diagnostics, Mapping)
        and source_diagnostics.get("bridge_pid") == pending.get("source_bridge_pid")
        and _positive(source_diagnostics.get("connection_generation")) is not None
    ):
        raise BridgeUnavailableError("private faction pending frame changed before receipt")

    def changed_or_ready(current: Mapping[str, object]) -> bool:
        revision = current.get("native_revision")
        old_actor = snapshot.get("played_character")
        new_actor = current.get("played_character")
        actor_changed = (
            not isinstance(old_actor, Mapping)
            or not isinstance(new_actor, Mapping)
            or (new_actor.get("character_id"), new_actor.get("alive"))
               != (old_actor.get("character_id"), old_actor.get("alive"))
        )
        return bool(
            (type(revision) is int and revision > pre_revision)
            or current.get("date_raw") != pending.get("pre_date_raw")
            or current.get("episode_run_id") != pending.get("episode_run_id")
            # Gold/opinion may publish before native_revision. They are not a
            # different owner and must not end the bounded wait prematurely.
            or actor_changed
            or current.get("paused") is not True
            or current.get("map_ready") is not True
            or current.get("active_event") is not None
            or current.get("pending_character_interaction") is not None
        )

    fresh = waiter(dict(snapshot), changed_or_ready, timeout_seconds=5.0)
    fresh_actor = fresh.get("played_character") if isinstance(fresh, Mapping) else None
    fresh_diagnostics = fresh.get("diagnostics") if isinstance(fresh, Mapping) else None
    if not (
        isinstance(fresh, Mapping)
        and type(fresh.get("revision")) is int
        and fresh["revision"] > old_revision
        and type(fresh.get("native_revision")) is int
        and fresh["native_revision"] > pre_revision
        and fresh.get("date_raw") == pending.get("pre_date_raw")
        and fresh.get("episode_run_id") == pending.get("episode_run_id")
        and isinstance(source_actor, Mapping)
        and isinstance(fresh_actor, Mapping)
        and (fresh_actor.get("character_id"), fresh_actor.get("alive"))
            == (source_actor.get("character_id"), source_actor.get("alive"))
        and fresh.get("paused") is True
        and fresh.get("map_ready") is True
        and fresh.get("active_event") is None
        and fresh.get("pending_character_interaction") is None
        and isinstance(fresh_diagnostics, Mapping)
        and fresh_diagnostics.get("bridge_pid") == source_diagnostics["bridge_pid"]
        and fresh_diagnostics.get("connection_generation") == source_diagnostics["connection_generation"]
    ):
        raise BridgeUnavailableError(
            "private faction pending same-date paused revision did not arrive"
        )
    # The ordinary Service planning wrapper also consumes this typed proof.
    # Replan the whole turn once; never relabel this old plan with fresh IDs.
    # This wait has not sent either a gift submission or its receipt query.
    raise FactionGiftPendingFrameReadyError({
        "schema": "xar.faction-gift-pending-frame-ready/v1",
        "phase": "planning_before_dispatch",
        "pending_request_id": pending.get("request_id"),
        "pending_status": pending.get("status"),
        "source_bridge_pid": pending.get("source_bridge_pid"),
        "source_bridge_creation_date": pending.get("source_bridge_creation_date"),
        "pre_native_revision": pre_revision,
        "source_frame": _pending_receipt_frame(snapshot),
        "fresh_frame": _pending_receipt_frame(fresh),
        "business_submission_attempted": False, "receipt_query_attempted": False,
        "gift_submission_replayed": False,
    })


def plan_faction_gift_private_v1(
    driver: object, planned: dict[str, object], snapshot: Mapping[str, object],
    history: Sequence[Mapping[str, object]], available_steps: set[str],
) -> dict[str, object]:
    """Augment an ordinary peaceful turn with one durable private route."""
    plan = planned.get("plan")
    if not isinstance(plan, dict) or plan.get("selected_step") != "life-advance":
        return planned
    state_dir = getattr(driver, "state_dir", None)
    if not isinstance(state_dir, Path):
        return {**planned, "plan": {**plan, "selected_step": None,
                    "reason": "private faction route lacks managed state_dir"}}
    ledger = read_faction_gift_ledger_v1(state_dir)
    pending = ledger.get("pending")
    if isinstance(pending, dict):
        pid, creation = _runtime_identity(driver)
        same_process = _same_pending_process(pid, creation, pending)
        step = RECEIPT_STEP if same_process else COLD_RECOVERY_STEP
        if same_process and not (
            type(snapshot.get("native_revision")) is int
            and snapshot["native_revision"]
            > pending.get("pre_native_snapshot_revision", 0)
        ):
            _wait_for_pending_paused_revision_v1(driver, snapshot, pending)
        return {**planned, "plan": {**plan,
            "phase": "faction_gift_pending_verification",
            "selected_step": step,
            "faction_gift_pending_action": dict(pending),
            "reason": ("confirm gift on an independent paused frame"
                       if same_process else
                       "classify unresolved gift from independent cold-process facts"),
        }}
    root_view = latest_same_frame_faction_root_v1(snapshot, history)
    if root_view.get("status") == "same_frame_root_not_observed":
        if ROOT_STEP not in available_steps:
            return {**planned, "plan": {**plan,
                "phase": "faction_gift_root_query_unavailable",
                "selected_step": None,
                "reason": "private faction route lacks its same-frame public root query",
            }}
        return {**planned, "plan": {**plan,
            "phase": "faction_gift_root_query",
            "selected_step": ROOT_STEP,
            "reason": "refresh current feudal faction count before any private gift query",
        }}
    if root_view.get("status") == "known_empty":
        return {**planned, "plan": {**plan,
            "faction_gift_private_candidate_v1": {
                "status": "known_empty", "gift_submission_enabled": False,
                "public_capability_advertised": False,
                "faction_dissolved_or_gift_applied": "not_inferred",
            },
        }}
    if root_view.get("status") != "targeting_present":
        return planned
    root = root_view.get("root")
    reader = getattr(driver, "query_faction_gift_private_candidate_v1", None)
    if not isinstance(root, dict) or not callable(reader):
        return planned
    candidate = reader(
        snapshot=snapshot, same_frame_root=root,
        minimum_gold_reserve_raw=MINIMUM_GOLD_RESERVE_RAW,
    )
    if not isinstance(candidate, dict):
        raise BridgeUnavailableError("private faction candidate query returned a non-object")
    traced = {**plan, "faction_gift_private_candidate_v1": candidate}
    if candidate.get("status") != "selected":
        return {**planned, "plan": traced}
    # A legal gift is an optional spend, not evidence of faction danger.
    # Preserve pending/readback above; only a fresh, matched stock threat
    # may create a new automatic spending intent or its checkpoint.
    threat = observe_faction_gift_stock_threat_v1(
        driver, snapshot=snapshot, history=history, candidate=candidate,
        expected_revision=int(planned["revision"]),
    )
    traced["faction_gift_stock_threat_v1"] = threat
    if (threat.get("status") != "observed"
            or threat.get("dangerous_response_ready") is not True):
        return {**planned, "plan": {**traced,
            "faction_gift_spending_deferred_v1": {
                "reason": "selected_faction_not_observed_stock_dangerous",
                "new_gift_spending_authorized": False,
            }}}
    from ..faction_gift_wartime_cash_v1 import observe_faction_gift_wartime_cash_v1
    cash = observe_faction_gift_wartime_cash_v1(
        driver, snapshot, candidate, root=root, history=history)
    traced["faction_gift_wartime_cash_v1"] = cash
    if cash.get("new_gift_spending_allowed") is not True:
        # Keep the ordinary war/clock choice. A legal but deferred gift must
        # not create a checkpoint/intent or turn the whole planner into RED.
        return {**planned, "plan": {**traced,
            "faction_gift_spending_deferred_v1": {
                "reason": cash.get("reason"),
                "new_gift_spending_authorized": False,
            }}}
    checkpoint = _current_checkpoint(driver, snapshot)
    if checkpoint is None:
        if "save-checkpoint" not in available_steps:
            return {**planned, "plan": {**traced, "selected_step": None,
                        "reason": "faction gift requires an exact pre-submit checkpoint"}}
        return {**planned, "plan": {**traced, "selected_step": "save-checkpoint",
                    "reason": "freeze exact pre-submit faction gift checkpoint"}}
    return {**planned, "plan": {**traced,
        "phase": "faction_gift_typed_submit",
        "selected_step": SUBMIT_STEP,
        "faction_gift_action": candidate,
        "faction_gift_pre_submit_checkpoint": checkpoint,
        "reason": "submit one native-legal budgeted faction mitigation gift",
    }}


def submit_faction_gift_private_v1(
    driver: object, *, candidate: Mapping[str, object], checkpoint: Mapping[str, object],
    expected_revision: int,
) -> dict[str, object]:
    choice = candidate.get("choice")
    observation = candidate.get("observation")
    if not (isinstance(choice, Mapping) and isinstance(observation, Mapping)):
        raise BridgeUnavailableError("private faction submit lacks typed candidate facts")
    before = driver.take_internal_semantic_snapshot()
    if before.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("private faction submit revision changed")
    state_dir = getattr(driver, "state_dir", None)
    round_id = getattr(driver, "private_faction_round_id", None)
    episode = before.get("episode_run_id")
    digest = checkpoint.get("sha256")
    if not (
        isinstance(state_dir, Path) and isinstance(round_id, str)
        and isinstance(episode, str) and episode
        and isinstance(digest, str) and len(digest) == 64
        and checkpoint.get("date_raw") == before.get("date_raw")
        and checkpoint.get("episode_run_id") == episode
    ):
        raise BridgeUnavailableError("private faction submit lacks its exact durable checkpoint")
    pid, creation = _runtime_identity(driver)
    request_id = "faction-gift-" + uuid.uuid4().hex
    begin_faction_gift_submission_v1(
        state_dir, request_id=request_id, episode_run_id=episode,
        source_round_id=round_id, source_bridge_pid=pid,
        source_bridge_creation_date=creation, observation=observation,
        minimum_gold_reserve_raw=choice["minimum_gold_reserve_raw"],
        checkpoint_sha256_before_submit=digest,
    )
    result = _send(driver, SUBMIT_STEP, {
        "request_id": request_id,
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_player_character_id": choice["player_character_id"],
        "expected_native_revision": choice["native_snapshot_revision"],
        "source_faction_id": choice["source_faction_id"],
        "recipient_character_id": choice["recipient_character_id"],
        "membership_role": choice["membership_role"],
        "definition_stable_hash": choice["definition_stable_hash"],
        "gold_cost_raw": choice["gold_cost_raw"],
        "opinion_delta": choice["opinion_delta"],
        "minimum_gold_reserve_raw": choice["minimum_gold_reserve_raw"],
    })
    native = result.get("native")
    ack = native.get("ack") if isinstance(native, Mapping) else None
    if not (
        result.get("step") == SUBMIT_STEP
        and result.get("private_build") is True
        and result.get("advertised") is False
        and result.get("status") == "submitted_verification_pending"
        and isinstance(ack, Mapping)
    ):
        raise StepPostconditionError(
            "private faction submit lacks its pending typed ACK",
            step_result=result, selected_step=SUBMIT_STEP,
        )
    mark_faction_gift_ack_pending_v1(state_dir, request_id=request_id, ack=ack)
    projected = {**result, "pending_ledger": read_faction_gift_ledger_v1(state_dir)}
    driver._record_command(SUBMIT_STEP, ok=True, result=projected)
    return projected


def query_faction_gift_receipt_private_v1(
    driver: object, *, pending: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    pid, creation = _runtime_identity(driver)
    if not _same_pending_process(pid, creation, pending):
        raise BridgeUnavailableError("same-process faction receipt cannot cross CK3 process identity")
    before = driver.take_internal_semantic_snapshot()
    if before.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("private faction receipt revision changed")
    result = _send(driver, RECEIPT_STEP, {
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_player_character_id": pending["pre_player_character_id"],
    })
    receipt = result.get("receipt")
    if not (result.get("status") == "applied" and isinstance(receipt, Mapping)):
        raise StepPostconditionError(
            "private faction receipt did not prove material application",
            step_result=result, selected_step=RECEIPT_STEP,
        )
    state_dir = getattr(driver, "state_dir")
    ledger = complete_faction_gift_after_independent_receipt_v1(
        state_dir, request_id=str(pending["request_id"]), receipt=receipt,
    )
    projected = {**result, "pending_ledger": ledger}
    driver._record_command(RECEIPT_STEP, ok=True, result=projected)
    return projected


def query_faction_gift_cold_recovery_private_v1(
    driver: object, *, pending: Mapping[str, object], expected_revision: int,
) -> dict[str, object]:
    pid, creation = _runtime_identity(driver)
    if _same_pending_process(pid, creation, pending):
        raise BridgeUnavailableError("cold faction recovery requires a replaced CK3 process")
    before = driver.take_internal_semantic_snapshot()
    if before.get("revision") != expected_revision:
        raise PreSubmissionRevisionMismatchError("cold faction recovery revision changed")
    state_dir = getattr(driver, "state_dir")
    mark_faction_gift_restore_requery_v1(
        state_dir, request_id=str(pending["request_id"])
    )
    result = _send(driver, COLD_RECOVERY_STEP, {
        "expected_revision": before["native_revision"],
        "expected_date_raw": before["date_raw"],
        "expected_player_character_id": pending["pre_player_character_id"],
        "source_faction_id": pending["source_faction_id"],
        "recipient_character_id": pending["recipient_character_id"],
    })
    native = result.get("native")
    observation = native.get("observation") if isinstance(native, Mapping) else None
    round_id = getattr(driver, "private_faction_round_id", None)
    checkpoint = _current_checkpoint(driver, before)
    recovery = {
        "schema_version": 1, "status": result.get("status"),
        "private_build": result.get("private_build"),
        "advertised": result.get("advertised"),
        "new_process_confirmed": True, "new_round_id": round_id,
        "new_bridge_pid": pid, "new_bridge_creation_date": creation,
        "episode_run_id": before.get("episode_run_id"),
        "paused": before.get("paused"), "map_ready": before.get("map_ready"),
        "independent_faction_storage_lookup_complete": (
            isinstance(native, Mapping) and native.get("failure_flags") == 0
            and isinstance(observation, Mapping)
            and observation.get("source_faction_requery_complete") is True
        ),
        "independent_recipient_lookup_complete": (
            isinstance(observation, Mapping)
            and observation.get("recipient_identity_resolved") is True
            and observation.get("recipient_opinion_query_complete") is True
        ),
        "selected_from_current_targeting_vector": False,
        "save_is_pre_action_checkpoint": bool(
            isinstance(checkpoint, dict)
            and checkpoint.get("sha256") == pending.get("checkpoint_sha256_before_submit")
        ),
        "selected_save_sha256": checkpoint.get("sha256") if isinstance(checkpoint, dict) else None,
        "post_observation": dict(observation) if isinstance(observation, Mapping) else None,
    }
    classification = resolve_faction_gift_after_cold_native_query_v1(
        state_dir, request_id=str(pending["request_id"]), recovery=recovery,
    )
    projected = {**result, "cold_recovery": recovery,
                 "cold_recovery_classification": classification}
    if classification.get("status") not in {"applied", "unchanged"}:
        driver._record_command(COLD_RECOVERY_STEP, ok=False, result=projected,
                               error="material_outcome_not_distinguishable")
        raise StepPostconditionError(
            "cold faction recovery remains materially unresolved",
            step_result=projected, selected_step=COLD_RECOVERY_STEP,
        )
    driver._record_command(COLD_RECOVERY_STEP, ok=True, result=projected)
    return projected

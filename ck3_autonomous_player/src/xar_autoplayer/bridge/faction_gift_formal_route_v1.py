"""Controlled formal route for one exact-build faction mitigation gift.

This module deliberately stays outside public capabilities and MCP.  It owns
the durable pending identity before the one-shot native submit, then routes a
same-process receipt or an independent cold-process fact read.  Missing facts
remain unresolved and never authorize a duplicate gift.
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
from ..runtime import _process_identity
from .driver import (
    BridgeUnavailableError,
    PreSubmissionRevisionMismatchError,
    StepPostconditionError,
)


SUBMIT_STEP = "private-submit-faction-gift-member-v1"
RECEIPT_STEP = "private-query-faction-gift-receipt-v1"
COLD_RECOVERY_STEP = "private-query-faction-gift-cold-recovery-v1"
MINIMUM_GOLD_RESERVE_RAW = 10_000_000


def _positive(value: object) -> int | None:
    return value if type(value) is int and value > 0 else None


def _runtime_identity(driver: object) -> tuple[int, str]:
    pid = getattr(driver, "_session_bridge_pid", None)
    if _positive(pid) is None:
        raise BridgeUnavailableError("private faction route lacks a live bridge PID")
    identity = _process_identity(pid)
    creation = identity.get("creation_date") if isinstance(identity, Mapping) else None
    if not isinstance(creation, str) or not creation:
        raise BridgeUnavailableError("private faction route lacks exact CK3 process identity")
    return pid, creation


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
        same_process = (
            pid == pending.get("source_bridge_pid")
            and creation == pending.get("source_bridge_creation_date")
        )
        step = RECEIPT_STEP if same_process else COLD_RECOVERY_STEP
        if same_process and not (
            type(snapshot.get("native_revision")) is int
            and snapshot["native_revision"]
            > pending.get("pre_snapshot_revision", 0)
        ):
            return planned
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
        minimum_gold_reserve_raw=MINIMUM_GOLD_RESERVE_RAW,
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
    if (pid, creation) != (
        pending.get("source_bridge_pid"), pending.get("source_bridge_creation_date")
    ):
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
    if (pid, creation) == (
        pending.get("source_bridge_pid"), pending.get("source_bridge_creation_date")
    ):
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

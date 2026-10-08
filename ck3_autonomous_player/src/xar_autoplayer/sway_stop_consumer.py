"""Explicitly finish the original selected player Sway, preserving its material.

The native typed Stop entry binds Root's actual4 paired642B profile. No Start
is sent here; a later/cold call only observes the retained original full ID.
"""
from __future__ import annotations

from collections.abc import Mapping
import uuid

from .bridge.driver import BridgeUnavailableError
from .sway_formal_consumer import _identity, _read_matches, _write, read_sway_ledger
from .sway_lifecycle_consumer import record_sway_terminal_observation


def finish_selected_sway_private_v1(service: object, *, expected_revision: int,
                                   target_character_id: int, scheme_instance_id: int,
                                   scheme_instance_generation: int) -> dict[str, object]:
    """Registered selected operation stages its current independent input reads."""
    driver = service.driver
    snapshot = service.snapshot(include_native_command_history=False)
    if snapshot.get("revision") != expected_revision:
        raise BridgeUnavailableError("selected Sway Finish expected revision is stale")
    ledger = read_sway_ledger(driver.state_dir)
    resolved = ledger["resolved"]
    receipt = resolved.get("native_receipt") if isinstance(resolved, Mapping) else None
    if (not isinstance(receipt, Mapping)
            or type(scheme_instance_id) is not int
            or type(scheme_instance_generation) is not int
            or scheme_instance_id != receipt.get("scheme_instance_id")
            or scheme_instance_generation != receipt.get("scheme_instance_generation")):
        raise ValueError("selected Sway Finish differs from the original episode")
    # A cold pending Stop uses only the original independent read, never Start/Stop again.
    if isinstance(resolved.get("stop_intervention"), Mapping):
        return consume_sway_stop_private_once(
            driver, target_character_id=target_character_id, snapshot=snapshot, readback={})
    readback = driver.query_active_scheme_sway_target_private_v1(
        expected_revision=expected_revision, target_character_id=target_character_id)
    service.query_active_scheme_sway_completion_private_v1(
        expected_revision=expected_revision, target_character_id=target_character_id,
        scheme_instance_id=scheme_instance_id)
    opinion_read = service.query_active_scheme_sway_outcome_opinion_private_v1(
        expected_revision=expected_revision, target_character_id=target_character_id)
    return consume_sway_stop_private_once(
        driver, target_character_id=target_character_id, snapshot=snapshot,
        readback=readback, opinion_read=opinion_read)


def should_finish_sway(snapshot: Mapping[str, object], readback: Mapping[str, object],
                       resolved: Mapping[str, object], target_character_id: int,
                       opinion_read: Mapping[str, object] | None = None) -> bool:
    """Player relation objective after useful benefit, not native continuation."""
    if not _read_matches(snapshot, readback, target_character_id):
        raise ValueError("Sway Stop target read differs from the paused frame")
    actor, _, native_revision, date = _identity(snapshot, target_character_id)
    receipt = resolved.get("native_receipt")
    instance = resolved.get("latest_instance_observation")
    material = resolved.get("material_intervention")
    if (resolved.get("postcondition_verified") is not True
            or resolved.get("actor_character_id") != actor
            or resolved.get("target_character_id") != target_character_id
            or not isinstance(receipt, Mapping)
            or not isinstance(instance, Mapping)
            or not isinstance(material, Mapping)):
        return False
    native = instance.get("native_observation")
    if opinion_read is None:
        current_positive = bool(material.get("source_date_raw") == date
                                and material.get("dedicated_benefit_observed") is True)
    else:
        modifier = opinion_read.get("scheme_sway_opinion")
        # Identical material observations are intentionally deduplicated in the
        # old ledger. Consume this fresh independent read as present benefit;
        # neither updating an observation date nor Stop creates a named gain.
        current_positive = bool(
            opinion_read.get("available") is True
            and opinion_read.get("actor_character_id") == actor
            and opinion_read.get("target_character_id") == target_character_id
            and opinion_read.get("snapshot_revision") == native_revision
            and opinion_read.get("date_raw") == date
            and opinion_read.get("target_opinion_of_actor") == readback["target_opinion_of_actor"]
            and isinstance(modifier, Mapping) and modifier.get("observed") is True
            and modifier.get("present") is True and type(modifier.get("value")) is int
            and modifier["value"] > 0)
    return bool(
        isinstance(native, Mapping)
        and all(instance.get(key) == receipt.get(key) for key in (
            "scheme_instance_id", "scheme_instance_generation"))
        and instance.get("source_date_raw") == date
        and native.get("exact_instance_join_ready") is True
        and native.get("owner_matches_actor") is True
        and native.get("native_owner_raw") == actor
        and native.get("native_status_observed") is True
        and native.get("native_status_raw") == 0
        and readback["matching_sway_active"] is True
        and readback["target_opinion_of_actor"] > 50
        and current_positive
    )


def _observe_stop(driver: object, resolved: Mapping[str, object],
                  stop: Mapping[str, object]) -> dict[str, object]:
    """Fresh original full-ID read; an ACK or disappearance never resolves Stop."""
    snapshot = driver.take_snapshot()
    actor, revision, _, _ = _identity(snapshot, resolved["target_character_id"])
    receipt = resolved["native_receipt"]
    if actor != resolved["actor_character_id"]:
        return {"status": "stop_pending_other_actor", "stop_intervention": dict(stop)}
    try:
        completion = driver.query_active_scheme_sway_completion_private_v1(
            expected_revision=revision, target_character_id=resolved["target_character_id"],
            scheme_instance_id=receipt["scheme_instance_id"])
    except BridgeUnavailableError as error:
        return {"status": "stop_postcondition_pending", "stop_intervention": dict(stop),
                "read_error": str(error), "postcondition_verified": False}
    observation = record_sway_terminal_observation(
        driver.state_dir, completion_read=completion)
    terminal = bool(observation and observation[
        "instance_terminal_outcome_observed"] is True)
    result = {**stop,
              "status": ("terminal_observed_after_stop_request" if terminal
                         else "stop_postcondition_pending"),
              "postcondition_verified": terminal,
              "independent_instance_observation": dict(completion)}
    if terminal:
        result.update(source_native_revision=completion["snapshot_revision"],
                      source_date_raw=completion["date_raw"],
                      terminal_cause_observed=completion["terminal_cause_observed"],
                      terminal_cause=completion["terminal_cause"],
                      next_turn_consumed=False)
    current = read_sway_ledger(driver.state_dir)
    _write(driver.state_dir, {**current, "resolved": {
        **current["resolved"], "stop_intervention": result,
    }})
    return result


def consume_sway_stop_private_once(driver: object, *, target_character_id: int,
                                   snapshot: Mapping[str, object],
                                   readback: Mapping[str, object],
                                   opinion_read: Mapping[str, object] | None = None) -> dict[str, object]:
    """One selected-instance Stop; a later/cold call only observes pending state."""
    ledger = read_sway_ledger(driver.state_dir)
    resolved = ledger["resolved"]
    if not isinstance(resolved, Mapping):
        return {"status": "no_original_sway_episode"}
    if ledger["pending"] is not None:
        return {"status": "start_pending_recovery", "pending": ledger["pending"]}
    actor, _, _, _ = _identity(snapshot, target_character_id)
    if (resolved.get("actor_character_id") != actor
            or resolved.get("target_character_id") != target_character_id):
        return {"status": "stop_other_actor_or_target"}
    previous = resolved.get("stop_intervention")
    if isinstance(previous, Mapping):
        if previous.get("postcondition_verified") is True:
            return {"status": "already_terminal_observed", "stop_intervention": dict(previous)}
        return _observe_stop(driver, resolved, previous)
    if not should_finish_sway(snapshot, readback, resolved, target_character_id, opinion_read):
        return {"status": "retain_existing_sway", "postcondition_verified": False}
    receipt = resolved["native_receipt"]
    submit = getattr(driver, "stop_active_scheme_sway_private_v1", None)
    if not callable(submit):
        return {"status": "native_stop_entry_required", "required_operation": {
            "target_character_id": target_character_id,
            "scheme_instance_id": receipt["scheme_instance_id"],
            "scheme_instance_generation": receipt["scheme_instance_generation"],
            "native_provider": "SubmitSelectedSwayStop12004",
            "profile_source": "Root actual paired CEndSchemeCommand operands and slots",
        }, "postcondition_verified": False}
    stop = {
        "status": "stop_submission_unresolved", "action_id": "stop-sway-" + uuid.uuid4().hex,
        "original_action_id": resolved["action_id"], "actor_character_id": actor,
        "target_character_id": target_character_id,
        "scheme_instance_id": receipt["scheme_instance_id"],
        "scheme_instance_generation": receipt["scheme_instance_generation"],
        "pre_native_revision": snapshot["native_revision"],
        "pre_date_raw": snapshot["date_raw"],
        "pre_target_opinion_of_actor": readback["target_opinion_of_actor"],
        "pre_material_opinion_read": dict(opinion_read) if isinstance(opinion_read, Mapping) else None,
        "decision": "finish_selected_active_relation", "postcondition_verified": False,
    }
    _write(driver.state_dir, {**ledger, "resolved": {**resolved, "stop_intervention": stop}})
    try:
        ack = submit(expected_revision=snapshot["revision"],
                     target_character_id=target_character_id,
                     scheme_instance_id=receipt["scheme_instance_id"],
                     scheme_instance_generation=receipt["scheme_instance_generation"],
                     action_id=stop["action_id"])
    except BridgeUnavailableError as error:
        return {**stop, "submit_error": str(error)}
    stop = {**stop, "status": "stop_postcondition_pending", "ack": ack}
    _write(driver.state_dir, {**ledger, "resolved": {**resolved, "stop_intervention": stop}})
    return _observe_stop(driver, resolved, stop)

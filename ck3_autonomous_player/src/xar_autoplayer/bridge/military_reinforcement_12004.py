"""Set the fixed original military checkbox once, then independently observe it."""
from __future__ import annotations

import hashlib
import json
import os
import time
import uuid

from .driver import BridgeUnavailableError, PreSubmissionRevisionMismatchError, UnsupportedStepError
from .ingame_decision_outcome_contract import reject_unresolved_claims, preserve_verified_claim
from .military_reinforcement_12004_contract import (
    normalize_reinforcement_ack, observe_fixed_reinforcement, reinforcement_binding,
    require_same_frame, step_for_desired,
)

VERIFICATION_TIMEOUT_SECONDS = 5.0


def _preserve(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _observe(driver, starting, binding):
    before = driver.take_snapshot()
    require_same_frame(starting, before, binding)
    tree = driver.inspect_gui_window_tree_v1("military")
    after = driver.take_snapshot()
    require_same_frame(starting, after, binding)
    return observe_fixed_reinforcement(tree, before, after)


def set_fixed_military_reinforcement_12004(driver, *, desired_enabled, expected_revision=None):
    """Unknown submission blocks both directions; only later same-owner bytes verify."""
    step = step_for_desired(desired_enabled)
    capability = "game.command." + step
    starting = driver.take_snapshot()
    try:
        binding = reinforcement_binding(starting)
        revision = starting["revision"]
        if type(revision) is not int or revision <= 0:
            raise ValueError("reinforcement requires a positive public revision")
        if expected_revision is not None:
            if type(expected_revision) is not int or expected_revision < 0:
                raise ValueError("expected_revision must be a nonnegative integer")
            if expected_revision != revision:
                raise PreSubmissionRevisionMismatchError("reinforcement public revision changed")
        if capability not in set(driver.capabilities().get("bridge_capabilities", [])):
            raise UnsupportedStepError("native DLL lacks this exact .4 stock reinforcement action")
        directory = driver._native_driver_state_path().parent / "military-reinforcement-actions"
        identity = {"game_pid": binding["game_pid"], "actor_id": binding["played_character_id"],
                    "episode_run_id": binding["episode_run_id"], "decision_key": "",
                    "action": "military_reinforcement", "public_revision": revision,
                    "desired_enabled": desired_enabled}
        # Both desired values use the same semantic action identity when
        # rejecting unknown claims. Neither reconnect nor revision can replay it.
        reject_unresolved_claims(directory, identity)
        before = _observe(driver, starting, binding)
        directory.mkdir(parents=True, exist_ok=True)
        key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode("utf-8")).hexdigest()
        claim = directory / (key + ".claim.json")
        request_id = "military-refill-" + uuid.uuid4().hex
        try:
            _preserve(claim, {"schema": "ck3-military-reinforcement-once-claim-v1", "request_id": request_id,
                              "binding": binding, "action_identity": identity, "before_observation": before,
                              "status": "claimed_result_unknown_no_retry"})
        except FileExistsError as error:
            raise BridgeUnavailableError("reinforcement action already claimed at this frame; no retry") from error
        raw = driver._execute_primitive_step(
            step, expected_revision=revision, required_capability=capability,
            protocol_request_id=request_id,
            request_fields={"expected_player_character_id": binding["played_character_id"],
                            "expected_game_pid": binding["game_pid"],
                            "expected_connection_generation": binding["connection_generation"]},
        )
        _preserve(claim.with_suffix(".result.json"), {"request_id": request_id, "raw": raw})
        result = normalize_reinforcement_ack(raw, binding, desired_enabled, before)
        deadline = time.monotonic() + VERIFICATION_TIMEOUT_SECONDS
        while True:
            later = _observe(driver, starting, binding)
            if later["source_child_path"] != before["source_child_path"]:
                raise ValueError("reinforcement later census changed the admitted stock source")
            if (later["frame"]["ticket_sequence"] <= before["frame"]["ticket_sequence"]
                    or later["frame"]["pump_epoch"] < before["frame"]["pump_epoch"]
                    or later["frame"]["thread_id"] != before["frame"]["thread_id"]):
                raise ValueError("reinforcement later census is not a fresh owner-thread observation")
            verified = later["switch"]["enabled"] is desired_enabled
            remaining = deadline - time.monotonic()
            if verified or remaining <= 0:
                break
            time.sleep(min(0.1, remaining))
        result.update({"postcondition_verified": verified, "verification_pending": not verified,
                       "status": ("verified_already_desired" if not raw["dispatch_attempted"] else "verified_desired")
                                 if verified else "acknowledged_verification_pending",
                       "later_observation": later, "before_observation": before, "native_ack": dict(raw),
                       "action_request_id": request_id, "action_claim_path": str(claim),
                       "episode_run_id": binding["episode_run_id"], "queried_revision": revision,
                       "uses_mouse": False, "uses_keyboard": False, "uses_ocr": False})
        if verified:
            preserve_verified_claim(claim, request_id, result)
        else:
            _preserve(claim.with_suffix(".pending.json"), {"request_id": request_id, "result": result})
        return result
    except ValueError as error:
        raise BridgeUnavailableError(str(error)) from error

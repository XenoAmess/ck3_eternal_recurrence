"""Attach a source-proved Sway end to the already admitted original action."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .bridge.sway_completion_causal_private_12004 import COMPLETE_BRANCH, consume_sway_end_causal_12004
from .bridge.version_identity import CK3_12004, require_exact_native_build


def retain_sway_end_causal_terminal_12004(
    previous: object, observation: Mapping[str, object],
) -> dict[str, object]:
    """Keep an admitted historical cause beside an honest later status1 read."""
    current = dict(observation)
    if (not isinstance(previous, Mapping)
            or previous.get("instance_terminal_outcome_observed") is not True
            or previous.get("terminal_cause_observed") is not True
            or observation.get("instance_terminal_outcome_observed") is not True
            or observation.get("terminal_cause_observed") is not False):
        return current
    cause = previous.get("causal_observation")
    native = observation.get("native_observation")
    identity = ("action_id", "actor_character_id", "target_character_id",
                "scheme_instance_id", "scheme_instance_generation",
                "exact_ck3_build", "exe_sha256")
    if (not isinstance(cause, Mapping) or not isinstance(native, Mapping)
            or any(key not in previous or previous[key] != observation.get(key)
                   or cause.get(key) != previous[key] for key in identity)
            or cause.get("schema") != "xar.ck3.sway-end-causal-observation.12004.v1"
            or previous.get("terminal_cause") != COMPLETE_BRANCH
            or cause.get("cause_key") != COMPLETE_BRANCH
            or cause.get("terminal_cause_observed") is not True
            or cause.get("native_terminal_transition_observed") is not True
            or type(cause.get("native_status_raw")) is not int
            or cause["native_status_raw"] != 1):
        return current
    try:
        if require_exact_native_build(
                observation.get("exact_ck3_build"), observation.get("exe_sha256")) != CK3_12004:
            return current
    except ValueError:
        return current
    if (native.get("schema") != "xar.ck3.sway_completion.v1"
            or native.get("available") is not True
            or any(native.get(key) != observation.get(key) for key in identity[1:])
            or any(native.get(key) is not True for key in (
                "instance_source_observed", "instance_present", "exact_instance_join_ready",
                "native_status_observed", "native_terminal_state_observed"))
            or native.get("storage_slot_reused") is not False
            or type(native.get("native_status_raw")) is not int
            or native["native_status_raw"] != 1
            or type(native.get("native_owner_raw")) is not int
            or native["native_owner_raw"] not in (observation["actor_character_id"], 0xFFFFFFFF)):
        return current
    # This retains a previously validated intervention. It never attributes the
    # fresh read, replays native evidence, or resets consumption after a cold load.
    return dict(previous)


def record_sway_end_causal_observation(
    state_dir: Path, *, execution_read: Mapping[str, object], termination_read: Mapping[str, object],
) -> dict[str, object] | None:
    from .sway_lifecycle_consumer import _resolved_for_read, _write

    observation = consume_sway_end_causal_12004(
        execution_read=execution_read, termination_read=termination_read)
    if observation is None:
        return None
    matched = _resolved_for_read(state_dir, termination_read)
    if matched is None:
        return None
    ledger, resolved, receipt = matched
    # The original action may predate migration and retain its build only in
    # native_receipt. Bind current query provenance here; keep that origin intact.
    try:
        current_build = require_exact_native_build(
            termination_read.get("exact_ck3_build"), termination_read.get("exe_sha256"))
    except ValueError:
        return None
    if current_build != CK3_12004:
        return None
    if any(receipt.get(key) != observation[key] for key in (
            "scheme_instance_id", "scheme_instance_generation")):
        return None
    observation.update({
        "action_id": resolved["action_id"],
        "exact_ck3_build": termination_read["exact_ck3_build"],
        "exe_sha256": termination_read["exe_sha256"],
        "source_native_revision": termination_read["snapshot_revision"],
        "source_date_raw": termination_read["date_raw"],
    })
    previous = resolved.get("end_causal_observation")
    if (isinstance(previous, Mapping) and all(previous.get(key) == observation[key] for key in (
            "action_id", "observer_session_identity", "owner_thread_id", "end_original_invocation_id"))):
        observation = dict(previous)
    terminal = resolved.get("terminal_intervention")
    if (isinstance(terminal, Mapping)
            and terminal.get("instance_terminal_outcome_observed") is True
            and all(terminal.get(key) == observation[key] for key in (
                "action_id", "actor_character_id", "target_character_id", "scheme_instance_id",
                "scheme_instance_generation", "exact_ck3_build", "exe_sha256"))):
        terminal = {**terminal, "terminal_cause_observed": True,
                    "terminal_cause": observation["cause_key"],
                    "causal_observation": observation}
        # Keep the existing terminal classification and consumption/material
        # fields. Causal evidence enriches an observed terminal, never fabricates
        # or rearms a gameplay intervention.
        resolved = {**resolved, "terminal_intervention": terminal}
    elif not isinstance(terminal, Mapping) or terminal.get("instance_terminal_outcome_observed") is not True:
        # The independently copied exact pre0/post1 end observation can stage
        # the existing terminal intervention even when no later retained-status
        # query has run. The existing next-turn consumer receives the same shape.
        terminal = {
            **{key: observation[key] for key in (
                "action_id", "actor_character_id", "target_character_id", "scheme_instance_id",
                "scheme_instance_generation", "exact_ck3_build", "exe_sha256",
                "source_native_revision", "source_date_raw")},
            "tracked_instance_active": False,
            "instance_terminal_outcome_observed": True,
            "native_status_key": "terminated_attributed",
            "terminal_cause_observed": True,
            "terminal_cause": observation["cause_key"],
            "native_observation": dict(termination_read),
            "causal_observation": observation,
            "next_turn_consumed": False,
        }
        resolved = {**resolved, "terminal_intervention": terminal}
    _write(state_dir, {**ledger, "resolved": {**resolved, "end_causal_observation": observation}})
    return observation

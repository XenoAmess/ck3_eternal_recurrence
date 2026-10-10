"""Attach a source-proved Sway end to the already admitted original action."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .bridge.sway_completion_causal_private_12004 import consume_sway_end_causal_12004


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
    if any(resolved.get(key) != termination_read.get(key) for key in (
            "exact_ck3_build", "exe_sha256")):
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

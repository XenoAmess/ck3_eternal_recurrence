"""Observe the retained Sway through existing Service readers before planning.

The original target runner and ordinary turns share this orchestration. Readers
own normalization and durable staging; this helper neither submits nor consumes.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .bridge.driver import BridgeUnavailableError, UnsupportedStepError
from .sway_formal_consumer import LEDGER_FILE, _resolved_instance_identity, read_sway_ledger


READERS = (
    ("completion", "allow_private_active_scheme_sway_completion_query",
     "query_active_scheme_sway_completion_private_v1"),
    ("termination", "allow_private_active_scheme_sway_completion_termination_query",
     "query_active_scheme_sway_completion_termination_private_v1"),
    ("opinion", "allow_private_active_scheme_sway_outcome_opinion_query",
     "query_active_scheme_sway_outcome_opinion_private_v1"),
)


def _actor(snapshot: Mapping[str, object]) -> tuple[object, object]:
    played = snapshot.get("played_character")
    if isinstance(played, Mapping):
        return played.get("character_id"), played.get("alive")
    # The existing explicit-target runner carries this flattened frame.
    return snapshot.get("played_character_id"), snapshot.get("played_character_alive")


def _binding(snapshot: Mapping[str, object]) -> tuple[object, ...]:
    return tuple(snapshot.get(key) for key in (
        "snapshot_id", "revision", "native_revision", "date_raw", "paused",
        "map_ready", "episode_run_id", "episode_character_id",
        "one_life_terminal_reason",
    )) + _actor(snapshot)


def observe_resolved_sway_lifecycle_v1(
    service: object, *, snapshot: Mapping[str, object] | None = None,
    target_character_id: int | None = None,
) -> dict[str, object] | None:
    """Read one original instance; leave all ordinary action priorities intact."""
    driver = service.driver
    enabled = [row for row in READERS if getattr(driver, row[1], False) is True]
    state_dir = getattr(driver, "state_dir", None)
    if not enabled or not isinstance(state_dir, Path) or not (state_dir / LEDGER_FILE).is_file():
        return None
    resolved = read_sway_ledger(state_dir).get("resolved")
    if (not isinstance(resolved, Mapping) or resolved.get("status") != "applied"
            or resolved.get("postcondition_verified") is not True):
        return None
    identity = _resolved_instance_identity(resolved)
    receipt = resolved.get("native_receipt")
    if (not isinstance(identity, Mapping)
            or (receipt is not None and (
                receipt.get("schema") != "active-scheme-sway-formal-private-v1"
                or receipt.get("stage") != "applied"
                or receipt.get("postcondition_verified") is not True))
            or not isinstance(resolved.get("action_id"), str) or not resolved["action_id"]
            or identity.get("action_id") != resolved["action_id"]
            or any(type(identity.get(key)) is not int or identity[key] != resolved.get(key)
                   for key in ("actor_character_id", "target_character_id"))):
        return None
    target = resolved.get("target_character_id")
    full_id, generation = identity.get("scheme_instance_id"), identity.get("scheme_instance_generation")
    if (type(target) is not int or not 0 < target < 2**31
            or (target_character_id is not None and target != target_character_id)
            or type(full_id) is not int or not 0 <= full_id < 0xFFFFFFFF
            or type(generation) is not int or not 0 <= generation <= 255
            or generation != full_id >> 24):
        return None
    before = snapshot if snapshot is not None else service.snapshot(include_native_command_history=False)
    actor, alive = _actor(before)
    if (before.get("paused") is not True or before.get("map_ready") is not True
            or alive is not True or actor != resolved.get("actor_character_id") or actor == target
            or before.get("one_life_terminal_reason") is not None
            or any(type(before.get(key)) is not int or before[key] <= 0
                   for key in ("revision", "native_revision"))):
        return None
    reads: dict[str, object] = {}
    failure = None
    for name, permission, method in READERS:
        if getattr(driver, permission, False) is not True:
            reads[name] = {"requested": False, "status": "not_requested"}
            continue
        arguments = {"expected_revision": before["revision"], "target_character_id": target}
        if name != "opinion":
            arguments["scheme_instance_id"] = full_id
        if name == "termination":
            arguments["after_sequence"] = 0
        try:
            observation = getattr(service, method)(**arguments)
        except (BridgeUnavailableError, UnsupportedStepError, ValueError) as error:
            failure = f"{type(error).__name__}: {error}"
            reads[name] = {"requested": True, "status": "query_failed", "error": failure}
            break
        reads[name] = {
            "requested": True, "status": observation.get("status"),
            "queried_snapshot_id": observation.get("queried_snapshot_id"),
            "queried_revision": observation.get("queried_revision"),
            "queried_native_revision": observation.get("queried_native_revision"),
            "read_date_raw": observation.get("date_raw"),
        }
    after = service.snapshot(include_native_command_history=False)
    same_frame = _binding(before) == _binding(after)
    for name, _, _ in READERS:
        reads.setdefault(name, {"requested": False, "status": "not_requested"})
    return {
        "status": "query_failed" if failure else "observed" if same_frame else "frame_changed",
        "original_action_id": resolved["action_id"], "actor_character_id": actor,
        "target_character_id": target, "scheme_instance_id": full_id,
        "scheme_instance_generation": generation, "same_frame": same_frame,
        "reads": reads, "request_retried": False,
    }

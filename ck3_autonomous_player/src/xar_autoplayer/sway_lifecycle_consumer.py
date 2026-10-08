"""Stage existing normalized Sway reads for the original once-start ledger.

No native read or command is issued here. Retained termination and named
relation material remain independent observations; status1 supplies no cause.
"""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from .sway_formal_consumer import LEDGER_FILE, _write, read_sway_ledger
from .sway_material_consumer import _record_sway_material


def _resolved_for_read(state_dir: Path, read: Mapping[str, object]):
    if not (state_dir / LEDGER_FILE).is_file():
        return None
    ledger = read_sway_ledger(state_dir)
    resolved = ledger["resolved"]
    if (not isinstance(resolved, dict)
            or resolved.get("postcondition_verified") is not True
            or any(resolved.get(key) != read.get(key) for key in (
                "actor_character_id", "target_character_id"))):
        return None
    receipt = resolved.get("native_receipt")
    if not isinstance(receipt, Mapping) or any(type(receipt.get(key)) is not int
            for key in ("scheme_instance_id", "scheme_instance_generation")):
        return None
    return ledger, resolved, receipt


def record_sway_terminal_observation(
    state_dir: Path, *, completion_read: Mapping[str, object],
) -> dict[str, object] | None:
    """Attach the exact requested instance, including honest absent/reused facts."""
    if (completion_read.get("schema") != "xar.ck3.sway_completion.v1"
            or completion_read.get("available") is not True):
        return None
    matched = _resolved_for_read(state_dir, completion_read)
    if matched is None:
        return None
    ledger, resolved, receipt = matched
    if any(receipt[key] != completion_read.get(key) for key in (
            "scheme_instance_id", "scheme_instance_generation")):
        return None
    terminal = completion_read["native_terminal_state_observed"] is True
    observation = {
        "action_id": resolved["action_id"],
        "actor_character_id": resolved["actor_character_id"],
        "target_character_id": resolved["target_character_id"],
        "scheme_instance_id": receipt["scheme_instance_id"],
        "scheme_instance_generation": receipt["scheme_instance_generation"],
        "exact_ck3_build": completion_read["exact_ck3_build"],
        "exe_sha256": completion_read["exe_sha256"],
        "source_native_revision": completion_read["snapshot_revision"],
        "source_date_raw": completion_read["date_raw"],
        "tracked_instance_active": (
            completion_read["exact_instance_join_ready"] is True
            and completion_read["owner_matches_actor"] is True
            and completion_read["native_status_observed"] is True
            and completion_read["native_status_raw"] == 0),
        "instance_terminal_outcome_observed": terminal,
        "native_status_key": completion_read["native_status_key"],
        "terminal_cause_observed": completion_read["terminal_cause_observed"],
        "terminal_cause": completion_read["terminal_cause"],
        "native_observation": dict(completion_read),
        "next_turn_consumed": False,
    }
    previous = resolved.get("terminal_intervention")
    # Repeating the same semantic read must not rearm an already consumed row.
    facts = ("tracked_instance_active", "instance_terminal_outcome_observed",
             "native_status_key", "terminal_cause_observed", "terminal_cause")
    native_facts = ("instance_source_observed", "instance_present",
                    "storage_slot_reused", "exact_instance_join_ready",
                    "native_owner_raw", "native_status_raw")
    if (isinstance(previous, Mapping)
            and all(previous.get(key) == observation[key] for key in facts)
            and isinstance(previous.get("native_observation"), Mapping)
            and all(previous["native_observation"].get(key)
                    == completion_read[key] for key in native_facts)):
        # Keep current provenance for a later opinion join; consumption is stable.
        observation.update({key: value for key, value in previous.items()
                            if key.startswith("following_")
                            or key == "next_turn_consumed"})
    # A later purge/reuse cannot erase an independently observed retained end.
    retained = (previous if isinstance(previous, Mapping)
                and previous.get("instance_terminal_outcome_observed") is True
                and not terminal else observation)
    _write(state_dir, {**ledger, "resolved": {
        **resolved, "latest_instance_observation": observation,
        "terminal_intervention": dict(retained),
    }})
    return observation


def record_sway_material_from_completion(
    state_dir: Path, *, opinion_read: Mapping[str, object],
) -> dict[str, object] | None:
    """Join existing opinion material with the stored exact-instance read."""
    if (opinion_read.get("schema") != "xar.ck3.sway-outcome-opinion-v1"
            or opinion_read.get("available") is not True):
        return None
    matched = _resolved_for_read(state_dir, opinion_read)
    if matched is None:
        return None
    ledger, resolved, _ = matched
    completion = resolved.get("latest_instance_observation")
    if (not isinstance(completion, Mapping)
            or any(completion.get(key) != opinion_read.get(key) for key in (
                "actor_character_id", "target_character_id",
                "exact_ck3_build", "exe_sha256"))
            or completion.get("source_date_raw") != opinion_read.get("date_raw")):
        return None
    return _record_sway_material(
        state_dir, ledger=ledger, resolved=resolved, opinion_read=opinion_read,
        tracked_active=completion["tracked_instance_active"],
        terminal_observation=resolved.get("terminal_intervention"),
    )


def has_pending_sway_following_turn(state_dir: Path) -> bool:
    """Avoid an additional snapshot when no original Sway observation is due."""
    if not (state_dir / LEDGER_FILE).is_file():
        return False
    resolved = read_sway_ledger(state_dir)["resolved"]
    if not isinstance(resolved, Mapping):
        return False
    return any(
        episode.get("next_turn_consumed") is not True
        or any(isinstance(episode.get(key), Mapping)
               and episode[key].get("next_turn_consumed") is not True
               and (key != "stop_intervention"
                    or episode[key].get("postcondition_verified") is True)
               for key in ("material_intervention", "terminal_intervention", "stop_intervention"))
        for episode in [resolved, *resolved.get("previous_interventions", [])]
    )

"""Stage existing normalized Sway reads for the original once-start ledger.

No native read or command is issued here. Retained termination and named
relation material remain independent observations; status1 supplies no cause.
"""
from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
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


def _same_sway_terminal_identity(previous: object, observation: Mapping[str, object]) -> bool:
    return isinstance(previous, Mapping) and all(
        previous.get(key) == observation.get(key) for key in (
            "action_id", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation"))


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
    from .sway_end_causal_consumer_12004 import retain_sway_end_causal_terminal_12004

    retained_common = (
        isinstance(previous, Mapping)
        and isinstance(previous.get("common_native_end_observation"), Mapping)
        and _same_sway_terminal_identity(previous, observation)
        and observation["terminal_cause_observed"] is False)
    retained = (previous if isinstance(previous, Mapping)
                and previous.get("instance_terminal_outcome_observed") is True
                and (not terminal or retained_common)
                else retain_sway_end_causal_terminal_12004(previous, observation))
    _write(state_dir, {**ledger, "resolved": {
        **resolved, "latest_instance_observation": observation,
        "terminal_intervention": dict(retained),
    }})
    return observation


def record_sway_common_native_end_observation(
    state_dir: Path, *, composition: Mapping[str, object],
) -> dict[str, object] | None:
    """Stage a copied normal return, independently of current storage and cause."""
    if composition.get("schema") != "xar.ck3.sway-terminal-source-composition.12004.v1":
        return None
    original = composition.get("original_instance")
    common = composition.get("retained_common_end_observation")
    if (not isinstance(original, Mapping) or not isinstance(common, Mapping)
            or common.get("original_instance") != original
            or common.get("source_kind") != "copied_common_native_end_original_return"
            or common.get("native_status_raw") != 1
            or common.get("native_terminal_state_observed") is not True
            or common.get("terminal_cause_observed") is not False):
        return None
    matched = _resolved_for_read(state_dir, original)
    if matched is None:
        return None
    ledger, resolved, _ = matched
    from .bridge.sway_terminal_source_producer_12004 import _original
    from .bridge.version_identity import CK3_12004, require_exact_native_build

    source_read = common.get("source_read")
    if not isinstance(source_read, Mapping):
        return None
    try:
        if (dict(original) != _original(resolved)
                or require_exact_native_build(
                    source_read.get("exact_ck3_build"), source_read.get("exe_sha256")) != CK3_12004):
            return None
    except ValueError:
        return None
    record = common.get("copied_common_native_end_record")
    if not isinstance(record, Mapping):
        return None
    entry, returned = record.get("entry"), record.get("returned")
    if (not isinstance(entry, Mapping) or not isinstance(returned, Mapping)
            or record.get("original_forwarded_once") is not True
            or record.get("original_returned") is not True
            or any(frame.get("scheme_full_id_observed") is not True
                   or frame.get("scheme_full_id_raw_u32") != original["scheme_instance_id"]
                   or frame.get("scheme_instance_generation_u8") != original["scheme_instance_generation"]
                   for frame in (entry, returned))
            or returned.get("status_observed") is not True
            or returned.get("status_raw_i32") != 1
            or returned.get("owner_observed") is not True
            or returned.get("owner_character_full_id_raw_u32") not in (
                original["actor_character_id"], 0xFFFFFFFF)):
        return None
    revision, date = source_read.get("snapshot_revision"), source_read.get("date_raw")
    if (type(revision) is not int or not 0 < revision < 1 << 64
            or type(date) is not int or not -(1 << 31) <= date < 1 << 31):
        # Retain the known end without inventing numeric next-turn provenance.
        _write(state_dir, {**ledger, "resolved": {
            **resolved, "common_native_end_observation": deepcopy(dict(common))}})
        return None
    captured_event_frame = (
        deepcopy(dict(returned["core_frame"]))
        if returned.get("core_frame_observed") is True
        and isinstance(returned.get("core_frame"), Mapping) else None)
    terminal = {
        **{key: original[key] for key in (
            "action_id", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation")},
        "exact_ck3_build": source_read["exact_ck3_build"],
        "exe_sha256": source_read["exe_sha256"],
        # These stamp the copied QUERY receipt, never the native end event.
        "source_native_revision": revision, "source_date_raw": date,
        "source_provenance_kind": "common_native_end_read_receipt",
        # Event provenance is the actually copied returned Core, when observed.
        "event_date_raw": (captured_event_frame["date_raw"]
                           if captured_event_frame is not None else None),
        "captured_event_frame": captured_event_frame,
        "tracked_instance_active": False, "instance_terminal_outcome_observed": True,
        "native_status_key": "terminated_unattributed",
        "terminal_cause_observed": False, "terminal_cause": "unknown",
        "native_observation": deepcopy(dict(record)),
        "common_native_end_observation": deepcopy(dict(common)),
        "next_turn_consumed": False,
    }
    previous = resolved.get("terminal_intervention")
    if (_same_sway_terminal_identity(previous, terminal)
            and previous.get("instance_terminal_outcome_observed") is True):
        # Enrich an existing end without replacing its cause, date or consumption.
        terminal = dict(previous)
        terminal.setdefault("common_native_end_observation", deepcopy(dict(common)))
    updated = {**resolved, "terminal_intervention": terminal}
    updated.pop("common_native_end_observation", None)
    _write(state_dir, {**ledger, "resolved": updated})
    return terminal


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
        current_terminal_observed=completion["instance_terminal_outcome_observed"],
    )


def record_sway_phase_observation(
    state_dir: Path, *, execution_read: Mapping[str, object],
) -> dict[str, object] | None:
    """Retain a hidden executing branch independently of opinion or terminal facts."""
    if (execution_read.get("schema") != "xar.ck3.sway-completion-execution.v1"
            or execution_read.get("available") is not True
            or not execution_read.get("records")):
        return None
    matched = _resolved_for_read(state_dir, execution_read)
    if matched is None:
        return None
    ledger, resolved, receipt = matched
    if receipt["scheme_instance_id"] != execution_read.get("scheme_instance_id"):
        return None
    record = execution_read["records"][-1]
    if record["scheme_instance_generation"] != receipt["scheme_instance_generation"]:
        return None
    observation = {
        "action_id": resolved["action_id"],
        "actor_character_id": resolved["actor_character_id"],
        "target_character_id": resolved["target_character_id"],
        "scheme_instance_id": receipt["scheme_instance_id"],
        "scheme_instance_generation": receipt["scheme_instance_generation"],
        "exact_ck3_build": execution_read["exact_ck3_build"],
        "exe_sha256": execution_read["exe_sha256"],
        "source_native_revision": execution_read["snapshot_revision"],
        "source_date_raw": execution_read["date_raw"],
        "source_sequence": record["sequence"],
        "execution_date_raw": record["date_raw"],
        "source_branch": record["source_branch"],
        "stock_event": record["stock_event"],
        "phase_result": record["phase_result"],
        "executing_input_observed": True,
        "material_effect_observed": False,
        "native_terminal_state_observed": False,
        "native_observation": dict(execution_read),
        "next_turn_consumed": False,
    }
    previous = resolved.get("phase_intervention")
    if (isinstance(previous, Mapping)
            and all(previous.get(key) == observation[key] for key in (
                "source_sequence", "execution_date_raw", "source_branch"))):
        return dict(previous)
    _write(state_dir, {**ledger, "resolved": {
        **resolved, "phase_intervention": observation,
    }})
    return observation


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
               for key in ("phase_intervention", "material_intervention",
                           "terminal_intervention", "stop_intervention"))
        for episode in [resolved, *resolved.get("previous_interventions", [])]
    )

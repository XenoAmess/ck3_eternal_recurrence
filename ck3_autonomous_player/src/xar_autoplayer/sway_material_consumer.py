"""Consume named Sway relation material independently of its start receipt.

Inputs are the existing normalized native readbacks.  This module sends no
command and never derives a terminal cause from an absent active instance.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


def _points(value: Mapping[str, object]) -> int | None:
    if value.get("observed") is not True:
        return None
    if value.get("present") is False and value.get("value") is None:
        return 0
    points = value.get("value")
    return points if value.get("present") is True and type(points) is int else None


def record_sway_material_intervention(
    state_dir: Path, *, sway_read: Mapping[str, object],
    opinion_read: Mapping[str, object],
) -> dict[str, object]:
    """Attach current native material to the original resolved once-start.

    Call after the two existing registered read tools, then use the ordinary
    gameplay turn.  The following-turn consumer already lives on that path.
    """
    from .sway_formal_consumer import read_sway_ledger

    if (sway_read.get("schema") != "active-scheme-sway-private-read-v1"
            or opinion_read.get("schema") != "xar.ck3.sway-outcome-opinion-v1"
            or opinion_read.get("available") is not True):
        raise ValueError("Sway material requires available normalized native reads")
    for key in ("actor_character_id", "target_character_id", "date_raw",
                "exact_ck3_build", "exe_sha256"):
        if sway_read.get(key) is None or sway_read[key] != opinion_read.get(key):
            raise ValueError("Sway material native read pair differs: " + key)
    ledger = read_sway_ledger(state_dir)
    resolved = ledger["resolved"]
    if (not isinstance(resolved, dict)
            or resolved.get("postcondition_verified") is not True
            or any(resolved.get(key) != sway_read[key]
                   for key in ("actor_character_id", "target_character_id"))):
        raise ValueError("Sway material does not belong to the resolved player intervention")
    receipt = resolved.get("native_receipt")
    if not isinstance(receipt, Mapping):
        raise ValueError("Sway material requires the original full-instance receipt")
    instance_id = receipt.get("scheme_instance_id")
    generation = receipt.get("scheme_instance_generation")
    if type(instance_id) is not int or type(generation) is not int:
        raise ValueError("Sway material lacks the original full-instance identity")
    rows = sway_read.get("active_sway_instances")
    if not isinstance(rows, list):
        raise ValueError("Sway material requires the current native instance census")
    tracked_active = any(
        isinstance(row, Mapping)
        and row.get("scheme_instance_id") == instance_id
        and row.get("scheme_instance_generation") == generation
        and row.get("target_character_id") == resolved["target_character_id"]
        for row in rows
    )
    return _record_sway_material(
        state_dir, ledger=ledger, resolved=resolved, opinion_read=opinion_read,
        tracked_active=tracked_active,
    )


def _record_sway_material(
    state_dir: Path, *, ledger: Mapping[str, object],
    resolved: Mapping[str, object], opinion_read: Mapping[str, object],
    tracked_active: bool, terminal_observation: Mapping[str, object] | None = None,
) -> dict[str, object]:
    """Share the named-material projection across census and exact-instance reads."""
    from .sway_formal_consumer import _write

    receipt = resolved["native_receipt"]
    instance_id = receipt["scheme_instance_id"]
    generation = receipt["scheme_instance_generation"]
    terminal = bool(terminal_observation and terminal_observation.get(
        "instance_terminal_outcome_observed") is True)
    sway = opinion_read.get("scheme_sway_opinion")
    blocker = opinion_read.get("sway_blocker_opinion")
    if not isinstance(sway, Mapping) or not isinstance(blocker, Mapping):
        raise ValueError("Sway material lacks the two named modifier measurements")
    sway_points, blocker_points = _points(sway), _points(blocker)
    if sway_points is None or blocker_points is None:
        raise ValueError("Sway material named modifiers are not observed")
    previous = resolved.get("material_intervention")
    previous = previous if isinstance(previous, Mapping) else None
    old_sway = previous.get("scheme_sway_opinion") if previous else None
    old_points = _points(old_sway) if isinstance(old_sway, Mapping) else None
    gain = bool(previous and old_points is not None and tracked_active
                and previous.get("tracked_instance_active") is True
                and opinion_read["date_raw"] > previous["source_date_raw"]
                and sway_points > old_points)
    if (previous and previous.get("tracked_instance_active") is tracked_active
            and previous.get("instance_terminal_outcome_observed") is terminal
            and previous.get("scheme_sway_opinion") == sway
            and previous.get("sway_blocker_opinion") == blocker
            and previous.get("target_opinion_of_actor")
            == opinion_read.get("target_opinion_of_actor")):
        return dict(previous)
    material = {
        "action_id": resolved["action_id"],
        "actor_character_id": resolved["actor_character_id"],
        "target_character_id": resolved["target_character_id"],
        "scheme_instance_id": instance_id,
        "scheme_instance_generation": generation,
        "exact_ck3_build": opinion_read["exact_ck3_build"],
        "exe_sha256": opinion_read["exe_sha256"],
        "source_native_revision": opinion_read["snapshot_revision"],
        "source_date_raw": opinion_read["date_raw"],
        "target_opinion_of_actor": opinion_read["target_opinion_of_actor"],
        "scheme_sway_opinion": dict(sway),
        "sway_blocker_opinion": dict(blocker),
        "tracked_instance_active": tracked_active,
        "dedicated_benefit_observed": sway_points > 0,
        "dedicated_setback_observed": blocker_points < 0,
        "incremental_named_gain_observed": gain,
        "previous_scheme_sway_opinion": dict(old_sway)
        if isinstance(old_sway, Mapping) else None,
        "decision": ("retain_existing_sway" if tracked_active else
                     "consume_retained_termination" if terminal else
                     "observe_tracked_instance_end"),
        "instance_terminal_outcome_observed": terminal,
        "next_turn_consumed": False,
    }
    if terminal_observation is not None:
        material["completion_source_native_revision"] = terminal_observation[
            "source_native_revision"]
        material["native_status_key"] = terminal_observation["native_status_key"]
        material["terminal_cause_observed"] = terminal_observation[
            "terminal_cause_observed"]
        material["terminal_cause"] = terminal_observation["terminal_cause"]
    _write(state_dir, {**ledger, "resolved": {
        **resolved, "material_intervention": material,
    }})
    return material


def consume_sway_material_following_turn(
    material: object, *, actor_character_id: int,
    native_revision: int, date_raw: int,
) -> dict[str, object] | None:
    """Used by the existing real gameplay-turn callback, without another read."""
    if (not isinstance(material, Mapping)
            or material.get("next_turn_consumed") is True
            or material.get("actor_character_id") != actor_character_id
            or (native_revision <= material["source_native_revision"]
                and date_raw <= material["source_date_raw"])):
        return None
    return {**material, "next_turn_consumed": True,
            "following_native_revision": native_revision,
            "following_date_raw": date_raw}

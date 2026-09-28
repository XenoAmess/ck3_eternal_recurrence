"""Offline admission for a proposed full WarManager border-raid scan.

This pure function does not read CK3 memory. A structurally complete scan is
only a candidate: the native producer must separately prove that its scan
matches stock any_character_war semantics on the exact paused frame.
"""

from __future__ import annotations

from typing import Any

from xar_autoplayer.formal_defender_exit_comparison import _frame


SCHEMA = "xar.ck3.h2743-border-raid-full-war-storage.v1"
EXE_SHA256 = "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
WAR_VALUES_SHA256 = "ED1CDB6E8BC887CF1FFFE010F1E9CA642DFD6DAF241E81F23E6B4736F7AFDF3B"
MAXIMUM_COMPONENT_CAPACITY = 1_000_000


def _integer(value: object, *, positive: bool = False) -> bool:
    return type(value) is int and -(2**31) <= value < 2**31 and (
        not positive or value > 0
    )


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        "status": "unavailable",
        "reason": reason,
        "border_raid_pair_candidate": None,
        "native_condition_observed": False,
        "evaluated_days": None,
        "persisted_expiry_date_raw": None,
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
    }


def _scan(sample: object, frame: dict[str, Any]) -> tuple[list[dict[str, Any]], int] | None:
    if not isinstance(sample, dict) or set(sample) != {
        "schema", "frame", "exe_sha256", "war_values_sha256",
        "storage_capacity", "slots",
    }:
        return None
    capacity = sample["storage_capacity"]
    slots = sample["slots"]
    if (
        sample["schema"] != SCHEMA or sample["frame"] != frame
        or sample["exe_sha256"] != EXE_SHA256
        or sample["war_values_sha256"] != WAR_VALUES_SHA256
        or not _integer(capacity, positive=True)
        or capacity > MAXIMUM_COMPONENT_CAPACITY
        or not isinstance(slots, list) or len(slots) != capacity
    ):
        return None
    active_ids: set[int] = set()
    target_rows = 0
    matches = 0
    for index, row in enumerate(slots):
        if (not isinstance(row, dict)
                or type(row.get("slot_index")) is not int
                or row["slot_index"] != index):
            return None
        state = row.get("state")
        if state == "empty":
            if set(row) != {"slot_index", "state"}:
                return None
            continue
        if state == "ended":
            if (set(row) != {"slot_index", "state", "war_id"}
                    or not _integer(row["war_id"], positive=True)
                    or (row["war_id"] & 0xFFFFFF) != index):
                return None
            continue
        if state != "active" or set(row) != {
            "slot_index", "state", "war_id", "primary_attacker_character_id",
            "primary_defender_character_id", "casus_belli_database_index",
            "casus_belli_key", "primary_attacker_in_participants",
        }:
            return None
        war_id = row["war_id"]
        attacker = row["primary_attacker_character_id"]
        defender = row["primary_defender_character_id"]
        if (
            not _integer(war_id, positive=True)
            or (war_id & 0xFFFFFF) != index or war_id in active_ids
            or not _integer(attacker, positive=True)
            or not _integer(defender, positive=True) or attacker == defender
            or not _integer(row["casus_belli_database_index"])
            or not 0 <= row["casus_belli_database_index"] < 10_000
            or not isinstance(row["casus_belli_key"], str)
            or not row["casus_belli_key"]
            or row["primary_attacker_in_participants"] is not True
        ):
            return None
        active_ids.add(war_id)
        if war_id == frame["war_id"]:
            target_rows += 1
            if (
                attacker != frame["primary_attacker_character_id"]
                or defender != frame["primary_defender_character_id"]
                or row["casus_belli_database_index"] != frame["casus_belli_database_index"]
                or row["casus_belli_key"] != frame["casus_belli_key"]
            ):
                return None
        if (
            attacker == frame["primary_attacker_character_id"]
            and defender == frame["primary_defender_character_id"]
            and row["casus_belli_key"] == "fp2_border_raid"
        ):
            matches += 1
    if target_rows != 1:
        return None
    return slots, matches


def project_border_raid_pair_from_full_war_storage(
    frame: object, first: object, second: object,
) -> dict[str, Any]:
    """Require two complete identical slot scans; never publish a native bool."""
    if not _frame(frame):
        return _unavailable("frame_invalid")
    first_scan = _scan(first, frame)
    second_scan = _scan(second, frame)
    if first_scan is None or second_scan is None:
        return _unavailable("full_war_storage_scan_incomplete_or_unbound")
    if first_scan != second_scan:
        return _unavailable("full_war_storage_scan_drift")
    return {
        "status": "structural_candidate_only",
        "reason": "stock_any_character_war_equivalence_unproven",
        "border_raid_pair_candidate": first_scan[1] > 0,
        "native_condition_observed": False,
        "evaluated_days": None,
        "persisted_expiry_date_raw": None,
        "material_complete": False,
        "recommended_outcome": None,
        "action_literal": None,
    }


__all__ = ["project_border_raid_pair_from_full_war_storage"]

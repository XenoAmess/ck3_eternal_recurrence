"""Optional current-heir roster validation and explicitly derived observations.

Native order and every occurrence remain intact. Summaries describe known
current family records; they do not infer a birth, its cause or succession.
"""

from __future__ import annotations

from copy import deepcopy

from .driver import BridgeUnavailableError


LEAF = "current_first_heir_descendants_v1"
SUMMARY = "current_first_heir_descendants_summary_v1"


def _integer(value: object, low: int, high: int) -> bool:
    return type(value) is int and low <= value < high


def _lineage(value: object) -> None:
    if not isinstance(value, dict) or value.get("status") not in {"available", "unavailable"}:
        raise BridgeUnavailableError("current heir descendant lineage is malformed")
    available = value["status"] == "available"
    reason = value.get("unavailable_reason")
    if ((reason is not None if available else not isinstance(reason, str) or not reason)
            or any((not _integer(value.get(key), -2**31, 2**31)
                    if available else value.get(key) is not None)
                   for key in ("house_id_raw", "dynasty_id_raw"))):
        raise BridgeUnavailableError("current heir descendant lineage values are malformed")


def validate_current_first_heir_descendants_v1(
    value: object, *, actor: int, heir: int | None,
    native_revision: int, date_raw: int,
) -> dict[str, object] | None:
    """Keep an absent legacy leaf optional and bind observed data to this heir."""
    if value is None:
        return None
    if not isinstance(value, dict):
        raise BridgeUnavailableError("current heir descendant observation is malformed")
    status = value.get("status")
    reason = value.get("unavailable_reason")
    unavailable = status == "unavailable"
    if (status not in {"available", "partial", "unavailable"}
            or (reason is not None if status == "available"
                else not isinstance(reason, str) or not reason)
            or type(value.get("native_revision")) is not int
            or value["native_revision"] != native_revision
            or any((value.get(key) not in (None, expected) if unavailable
                    else value.get(key) != expected or expected is None)
                   or (value.get(key) is not None and
                       not _integer(value[key], 1, 2**31))
                   for key, expected in (("played_character_id", actor),
                                         ("heir_character_id", heir)))
            or (value.get("date_raw") is not None and (
                not _integer(value["date_raw"], -2**63, 2**63)
                or value["date_raw"] != date_raw))
            or (not unavailable and value.get("date_raw") is None)
            or any(value.get(key) is not None and type(value[key]) is not bool
                   for key in ("family_present", "data_pointer_present"))
            or (value.get("native_child_count_raw") is not None and
                not _integer(value["native_child_count_raw"], -2**31, 2**31))
            or type(value.get("roster_complete")) is not bool
            or not isinstance(value.get("rows"), list)):
        raise BridgeUnavailableError("current heir descendant frame or roster is malformed")
    complete = value["roster_complete"]
    rows = value["rows"]
    count = value.get("native_child_count_raw")
    if ((status == "available") is not complete
            or (complete and (
                value.get("family_present") is not True
                or not _integer(count, 0, 2**31) or len(rows) != count
                or type(value.get("data_pointer_present")) is not bool
                or (count > 0 and value["data_pointer_present"] is not True)))
            or (not complete and rows)):
        raise BridgeUnavailableError("current heir descendant whole roster is malformed")
    _lineage(value.get("played_lineage"))
    _lineage(value.get("heir_lineage"))
    for index, row in enumerate(rows):
        if (not isinstance(row, dict)
                or type(row.get("occurrence_index")) is not int
                or row["occurrence_index"] != index
                or not _integer(row.get("raw_character_id"), 0, 2**32)
                or type(row.get("generation_valid")) is not bool
                or any(row.get(key) is not None and type(row[key]) is not bool
                       for key in ("alive", "parent_family_present", "child_of_heir"))):
            raise BridgeUnavailableError("current heir descendant occurrence is malformed")
        parents = (row.get("parent_0_character_id_raw"),
                   row.get("parent_4_character_id_raw"))
        if row.get("parent_family_present") is True:
            if (any(not _integer(parent, 0, 2**32) for parent in parents)
                    or row.get("child_of_heir") is not (heir in parents)):
                raise BridgeUnavailableError("current heir descendant parent values are malformed")
        elif row.get("parent_family_present") is False:
            if any(parent is not None for parent in parents) or row.get("child_of_heir") is not False:
                raise BridgeUnavailableError("absent current heir descendant family is malformed")
        elif any(parent is not None for parent in parents) or row.get("child_of_heir") is not None:
            raise BridgeUnavailableError("unobserved current heir descendant parents are malformed")
        _lineage(row.get("lineage"))
        if row["generation_valid"] is False and (
                any(row.get(key) is not None for key in (
                    "alive", "parent_family_present", "child_of_heir"))
                or row["lineage"]["status"] != "unavailable"):
            raise BridgeUnavailableError("unresolved current heir descendant values are malformed")
    return deepcopy(value)


def summarize_current_first_heir_descendants_v1(
    value: dict[str, object] | None,
) -> dict[str, object] | None:
    """Count known occurrences; deduplicate only explicitly named summary IDs."""
    if value is None:
        return None
    rows = value["rows"]
    direct = [row for row in rows if row.get("child_of_heir") is True]
    living = [row for row in direct if row.get("alive") is True]
    direct_complete = value["roster_complete"] and all(
        type(row.get("child_of_heir")) is bool for row in rows)
    living_complete = direct_complete and all(type(row.get("alive")) is bool for row in direct)

    def distinct_ids(known: list[dict[str, object]]) -> list[int]:
        return list(dict.fromkeys(row["raw_character_id"] for row in known))

    def dynasty_matches(reference: dict[str, object]) -> dict[str, object]:
        dynasty = reference.get("dynasty_id_raw")
        if reference["status"] != "available" or dynasty == -1:
            return {"status": "unavailable" if reference["status"] != "available"
                    else "not_applicable", "reference_dynasty_id_raw": dynasty,
                    "unavailable_reason": reference.get("unavailable_reason"),
                    "known_living_direct_child_occurrence_count": None,
                    "known_living_direct_child_character_ids": None,
                    "all_living_direct_children_classified": False,
                    "living_direct_child_exists": None}
        matched = [row for row in living if row["lineage"]["status"] == "available"
                   and row["lineage"]["dynasty_id_raw"] == dynasty]
        classified = living_complete and all(
            row["lineage"]["status"] == "available" for row in living)
        return {"status": "available" if classified else "partial",
                "reference_dynasty_id_raw": dynasty, "unavailable_reason": None,
                "known_living_direct_child_occurrence_count": len(matched),
                "known_living_direct_child_character_ids": distinct_ids(matched),
                "all_living_direct_children_classified": classified,
                "living_direct_child_exists": True if matched else False if classified else None}

    return {
        "source": "derived_native_descendant_roster",
        "native_roster_status": value["status"],
        "roster_complete": value["roster_complete"],
        "known_direct_child_occurrence_count": len(direct),
        "known_direct_child_character_ids": distinct_ids(direct),
        "direct_child_count_complete": direct_complete,
        "actual_direct_child_exists": True if direct else False if direct_complete else None,
        "known_living_direct_child_occurrence_count": len(living),
        "known_living_direct_child_character_ids": distinct_ids(living),
        "living_direct_child_count_complete": living_complete,
        "living_actual_direct_child_exists": True if living else False if living_complete else None,
        "current_heir_dynasty_matches": dynasty_matches(value["heir_lineage"]),
        "played_dynasty_matches": dynasty_matches(value["played_lineage"]),
    }

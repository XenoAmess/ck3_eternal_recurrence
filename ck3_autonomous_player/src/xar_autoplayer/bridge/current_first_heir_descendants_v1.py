"""Optional current-heir roster validation and explicitly derived observations.

Native order and every occurrence remain intact. Summaries describe known
current family records; they do not infer a birth, its cause or succession.
"""

from __future__ import annotations

from copy import deepcopy

from .driver import BridgeUnavailableError


LEAF = "current_first_heir_descendants_v1"
SUMMARY = "current_first_heir_descendants_summary_v1"
CHILD_INPUTS = "child_inputs"
TYPED_WINDOWS = "typed_windows"
CHARACTER_WINDOW_IDENTITY = "character_window_identity"
CHILDHOOD_TRAIT_KEYS = ("curious", "rowdy", "bossy", "pensive", "charming")
EDUCATION_POINT_TRAIT_KEYS = (
    "intellect_good_1", "intellect_good_2", "intellect_good_3",
    "intellect_bad_1", "intellect_bad_2", "intellect_bad_3",
    "shrewd", "dull", "inbred",
)


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


def _child_values(value: object) -> None:
    if (not isinstance(value, dict)
            or value.get("source") != "native_character_age_and_sex"
            or value.get("status") not in {"available", "unavailable"}):
        raise BridgeUnavailableError("current heir child values are malformed")
    available = value["status"] == "available"
    reason = value.get("unavailable_reason")
    if ((reason is not None if available else not isinstance(reason, str) or not reason)
            or (not _integer(value.get("age_measure_raw"), -2**15, 2**15)
                or not _integer(value.get("sex_selector_raw"), 0, 2)
                if available else value.get("age_measure_raw") is not None
                or value.get("sex_selector_raw") is not None)):
        raise BridgeUnavailableError("current heir child age or sex values are malformed")


def _childhood_traits(value: object) -> None:
    if (not isinstance(value, dict)
            or value.get("source") != "native_character_has_trait"
            or value.get("status") not in {"available", "unavailable"}
            or value.get("queried_trait_keys") != list(CHILDHOOD_TRAIT_KEYS)):
        raise BridgeUnavailableError("current heir childhood trait observation is malformed")
    available = value["status"] == "available"
    reason = value.get("unavailable_reason")
    present = value.get("present_trait_keys")
    if ((reason is not None if available else not isinstance(reason, str) or not reason)
            or (not isinstance(present, list)
                or present != [key for key in CHILDHOOD_TRAIT_KEYS if key in present]
                if available else present is not None)):
        raise BridgeUnavailableError("current heir childhood trait values are malformed")


def _education_point_traits(value: object) -> None:
    """Validate the child's active predicates used by the stock point effect."""
    if (not isinstance(value, dict)
            or not {"source", "status", "unavailable_reason", "queried_trait_keys",
                    "present_trait_keys"}.issubset(value)
            or value.get("source") != "native_character_has_trait"
            or value.get("status") not in ("available", "unavailable")
            or value.get("queried_trait_keys") != list(EDUCATION_POINT_TRAIT_KEYS)):
        raise BridgeUnavailableError("current heir education-point trait observation is malformed")
    reason, present = value["unavailable_reason"], value["present_trait_keys"]
    if value["status"] == "unavailable":
        if not isinstance(reason, str) or not reason or present is not None:
            raise BridgeUnavailableError("unavailable current heir education-point traits are malformed")
    elif (reason is not None or not isinstance(present, list)
          or present != [key for key in EDUCATION_POINT_TRAIT_KEYS if key in present]):
        raise BridgeUnavailableError("available current heir education-point traits are malformed")


def _native_focus(value: object) -> None:
    """Keep native focus presence independent of the other child subreads."""
    if (not isinstance(value, dict)
            or not {"source", "status", "unavailable_reason", "presence", "key"}.issubset(value)
            or value.get("source") != "native_character_current_focus"
            or value.get("status") not in ("available", "unavailable")):
        raise BridgeUnavailableError("current heir child focus observation is malformed")
    reason, presence, key = (value["unavailable_reason"], value["presence"], value["key"])
    if value["status"] == "unavailable":
        if not isinstance(reason, str) or not reason or presence is not None or key is not None:
            raise BridgeUnavailableError("unavailable current heir child focus values are malformed")
    elif (reason is not None or presence not in ("present", "absent")
          or (not isinstance(key, str) or not key if presence == "present" else key is not None)):
        raise BridgeUnavailableError("available current heir child focus values are malformed")


def _typed_windows(value: object, *, native_revision: int) -> None:
    """Keep fixed-window diagnostics independent of the child observations."""
    required = {"source", "native_revision", "window_handler_status",
                "window_handler_unavailable_reason", "rows"}
    if (not isinstance(value, dict) or not required.issubset(value)
            or value["source"] != "native_fixed_window_type_diagnostic"
            or type(value["native_revision"]) is not int
            or value["native_revision"] != native_revision
            or value["window_handler_status"] not in ("available", "unavailable")
            or not isinstance(value["rows"], list) or len(value["rows"]) != 7):
        raise BridgeUnavailableError("current heir typed-window diagnostic is malformed")
    handler_available = value["window_handler_status"] == "available"
    reason = value["window_handler_unavailable_reason"]
    if (reason is not None if handler_available
            else not isinstance(reason, str) or not reason):
        raise BridgeUnavailableError("current heir typed-window handler is malformed")
    fixed_rows = ((0, 152, 13092), (1, 160, 11010), (2, 168, 11399),
                  (3, 176, 14350), (4, 184, 14351), (5, 192, 15450),
                  (6, 200, 10602))
    rva_keys = ("object_vtable_rva", "object_col_rva", "object_type_descriptor_rva")
    row_keys = {"slot_index", "handler_member_offset", "type_identifier",
                "registered_name_status", "registered_name",
                "registered_name_unavailable_reason", "window_presence",
                "object_type_status", *rva_keys, "object_type_decorated_name",
                "object_type_unavailable_reason"}
    for row, fixed in zip(value["rows"], fixed_rows):
        if (not isinstance(row, dict) or not row_keys.issubset(row)
                or any(type(row[key]) is not int or row[key] != expected
                       for key, expected in zip(
                           ("slot_index", "handler_member_offset", "type_identifier"), fixed))
                or row["registered_name_status"] not in ("available", "unavailable")
                or row["window_presence"] not in ("present", "absent", "unavailable")
                or row["object_type_status"] not in
                    ("available", "unavailable", "not_applicable")
                or any(row[key] is not None and not _integer(row[key], 0, 2**64)
                       for key in rva_keys)
                or (row["object_type_decorated_name"] is not None
                    and not isinstance(row["object_type_decorated_name"], str))):
            raise BridgeUnavailableError("current heir typed-window row is malformed")
        name_available = row["registered_name_status"] == "available"
        name, name_reason = row["registered_name"], row["registered_name_unavailable_reason"]
        if ((name_reason is not None if name_available
             else not isinstance(name_reason, str) or not name_reason)
                or (not isinstance(name, str) if name_available else name is not None)):
            raise BridgeUnavailableError("current heir typed-window registered name is malformed")
        presence, status = row["window_presence"], row["object_type_status"]
        object_reason = row["object_type_unavailable_reason"]
        if (not handler_available and presence != "unavailable"
                or (presence == "absent" and status != "not_applicable")
                or (presence == "unavailable" and status != "unavailable")
                or (presence == "present" and status == "not_applicable")
                or (not isinstance(object_reason, str) or not object_reason
                    if status == "unavailable" else object_reason is not None)):
            raise BridgeUnavailableError("current heir typed-window object status is malformed")
        if status == "available":
            if (any(row[key] is None for key in rva_keys)
                    or not isinstance(row["object_type_decorated_name"], str)):
                raise BridgeUnavailableError("available current heir typed-window RTTI is malformed")
        elif presence != "present" and (
                any(row[key] is not None for key in rva_keys)
                or row["object_type_decorated_name"] is not None):
            raise BridgeUnavailableError("unobserved current heir typed-window RTTI is malformed")


def _character_window_identity(value: object) -> None:
    """Admit the proved native window subject without rebinding a family child."""
    required = {"receiver_available", "receiver_unavailable_reason",
                "raw_character_id", "character_available",
                "character_unavailable_reason", "character_id"}
    if (not isinstance(value, dict) or not required.issubset(value)
            or type(value["receiver_available"]) is not bool
            or type(value["character_available"]) is not bool
            or any(not isinstance(value[key], str)
                   for key in ("receiver_unavailable_reason", "character_unavailable_reason"))
            or any(value[key] is not None and not _integer(value[key], -2**31, 2**31)
                   for key in ("raw_character_id", "character_id"))):
        raise BridgeUnavailableError("current heir CharacterWindow identity is malformed")
    receiver, character = value["receiver_available"], value["character_available"]
    if (bool(value["receiver_unavailable_reason"]) == receiver
            or bool(value["character_unavailable_reason"]) == character
            or (not receiver and (value["raw_character_id"] is not None or character))
            or (character and (value["character_id"] is None
                               or value["character_id"] == -1
                               or value["raw_character_id"] != value["character_id"]))
            or (not character and value["character_id"] is not None)):
        raise BridgeUnavailableError("current heir CharacterWindow identity states are malformed")


def _child_inputs(value: object, descendants: dict[str, object]) -> None:
    """Bind distinct living-child inputs to their full native occurrence groups."""
    if (not isinstance(value, dict)
            or value.get("source") != "native_current_heir_child_inputs"
            or value.get("status") not in {"available", "partial", "unavailable"}):
        raise BridgeUnavailableError("current heir child input observation is malformed")
    status = value["status"]
    reason = value.get("unavailable_reason")
    if ((reason is not None if status == "available"
         else not isinstance(reason, str) or not reason)
            or any(type(value.get(key)) is not type(descendants.get(key))
                   or value.get(key) != descendants.get(key)
                   for key in ("native_revision", "played_character_id",
                               "heir_character_id", "date_raw"))
            or not isinstance(value.get("rows"), list)):
        raise BridgeUnavailableError("current heir child input frame is malformed")
    if TYPED_WINDOWS in value:
        _typed_windows(value[TYPED_WINDOWS], native_revision=value["native_revision"])
    if CHARACTER_WINDOW_IDENTITY in value:
        _character_window_identity(value[CHARACTER_WINDOW_IDENTITY])
    rows = value["rows"]
    if status == "unavailable":
        if rows:
            raise BridgeUnavailableError("unavailable current heir child inputs contain rows")
        return
    if descendants["roster_complete"] is not True:
        raise BridgeUnavailableError("current heir child inputs need a complete native roster")
    groups: dict[int, list[int]] = {}
    for occurrence in descendants["rows"]:
        if (occurrence["generation_valid"] is True
                and occurrence.get("alive") is True
                and occurrence.get("child_of_heir") is True):
            raw = occurrence["raw_character_id"]
            character = raw if raw < 2**31 else raw - 2**32
            groups.setdefault(character, []).append(occurrence["occurrence_index"])
    if len(rows) != len(groups):
        raise BridgeUnavailableError("current heir child input roster is incomplete")
    all_available = True
    for row, (character, indices) in zip(rows, groups.items()):
        if (not isinstance(row, dict)
                or not _integer(row.get("character_id"), -2**31, 2**31)
                or row["character_id"] != character
                or not isinstance(row.get("occurrence_indices"), list)
                or any(type(index) is not int for index in row["occurrence_indices"])
                or row["occurrence_indices"] != indices):
            raise BridgeUnavailableError("current heir child input occurrence group is malformed")
        _child_values(row.get("values"))
        _childhood_traits(row.get("childhood_traits"))
        if "education_point_traits" in row:
            _education_point_traits(row["education_point_traits"])
        if "native_focus" in row:
            _native_focus(row["native_focus"])
        all_available = (all_available and row["values"]["status"] == "available"
                         and row["childhood_traits"]["status"] == "available")
    if (status == "available") is not all_available:
        raise BridgeUnavailableError("current heir child input status disagrees with its subreads")


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
    if CHILD_INPUTS in value:
        _child_inputs(value[CHILD_INPUTS], value)
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

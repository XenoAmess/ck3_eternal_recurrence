"""Project one validated current-heir roster into current education inputs.

The caller supplies the existing strict relationship query's optional
``current_first_heir_descendants_v1`` leaf. This module performs no query,
action, age admission or native legality evaluation. The owning descendant
leaf retains its complete raw roster; these rows name distinct living actual
children and preserve their complete occurrence groups and full ID bits.
"""

from __future__ import annotations

from copy import deepcopy


SCHEMA = "family_generation_education_inputs_v1"
_FRAME_KEYS = (
    "native_revision", "played_character_id", "heir_character_id", "date_raw",
)
_INPUT_LEAVES = (
    "values", "childhood_traits", "native_focus", "education_point_traits",
)


def _availability(
    observation: dict[str, object] | None, *, missing_status: str, reason: str,
) -> dict[str, object]:
    if observation is None:
        return {"status": missing_status, "unavailable_reason": reason}
    return {"status": observation["status"],
            "unavailable_reason": observation["unavailable_reason"]}


def derive_family_generation_education_inputs_v1(
    descendants: dict[str, object] | None,
) -> dict[str, object]:
    """Reuse qualified same-query child reads without discarding partial rows.

    Available focus absence and available empty trait subsets remain known
    observations. Missing legacy optional leaves remain ``not_observed``.
    A missing value read never becomes age zero or a default sex. Readiness
    describes only these four observations, not authority to educate a child.
    """
    result: dict[str, object] = {
        "schema": SCHEMA,
        "source": "derived_current_first_heir_child_education_inputs",
        "status": "unavailable",
        "unavailable_reason": "descendants_not_observed",
        "frame": None,
        "native_roster_status": "not_observed",
        "roster_complete": False,
        "living_child_classification_complete": False,
        "raw_occurrence_count": None,
        "known_living_actual_child_count": 0,
        "living_actual_child_count": None,
        "living_actual_child_exists": None,
        "known_empty": None,
        "child_inputs_status": "not_observed",
        "observed_inputs_complete": False,
        "rows": [],
    }
    if descendants is None:
        return result

    result["frame"] = {key: descendants.get(key) for key in _FRAME_KEYS}
    result["native_roster_status"] = descendants["status"]
    result["roster_complete"] = descendants["roster_complete"]
    sidecar = descendants.get("child_inputs")
    if isinstance(sidecar, dict):
        result["child_inputs_status"] = sidecar["status"]
    if descendants["status"] != "available" or descendants["roster_complete"] is not True:
        result["unavailable_reason"] = (
            descendants["unavailable_reason"] or "descendant_roster_incomplete")
        return result

    groups: dict[int, list[int]] = {}
    raw_by_id: dict[int, int] = {}
    classified = True
    raw_rows = descendants["rows"]
    result["raw_occurrence_count"] = len(raw_rows)
    for occurrence in raw_rows:
        if occurrence["generation_valid"] is not True:
            continue
        alive, child = occurrence.get("alive"), occurrence.get("child_of_heir")
        if alive is False or child is False:
            continue
        if alive is not True or child is not True:
            classified = False
            continue
        raw_id = occurrence["raw_character_id"]
        character_id = raw_id if raw_id < 2**31 else raw_id - 2**32
        groups.setdefault(character_id, []).append(occurrence["occurrence_index"])
        raw_by_id[character_id] = raw_id

    result["living_child_classification_complete"] = classified
    result["known_living_actual_child_count"] = len(groups)
    result["living_actual_child_count"] = len(groups) if classified else None
    result["living_actual_child_exists"] = True if groups else False if classified else None
    result["known_empty"] = False if groups else True if classified else None

    # Identity and frame joins supplement the existing strict validator's
    # contract. They do not silently rebind a read from another child or query.
    by_id: dict[int, dict[str, object]] = {}
    missing_status, missing_reason = "not_observed", "child_inputs_not_observed"
    if isinstance(sidecar, dict):
        missing_status = "unavailable"
        missing_reason = sidecar["unavailable_reason"] or "child_input_row_unavailable"
        if any(type(sidecar.get(key)) is not type(descendants[key])
               or sidecar.get(key) != descendants[key] for key in _FRAME_KEYS):
            missing_reason = "child_inputs_frame_mismatch"
        elif sidecar["status"] != "unavailable":
            by_id = {row["character_id"]: row for row in sidecar["rows"]}
            if len(by_id) != len(sidecar["rows"]):
                by_id = {}
                missing_reason = "child_input_identity_duplicate"

    rows = []
    for character_id, indices in groups.items():
        observed = by_id.get(character_id)
        row_missing_reason = missing_reason
        if observed is not None and observed["occurrence_indices"] != indices:
            observed = None
            row_missing_reason = "child_input_occurrence_group_mismatch"
        row: dict[str, object] = {
            "character_id": character_id,
            "raw_character_id": raw_by_id[character_id],
            "occurrence_indices": list(indices),
            "leaf_availability": {},
        }
        availability = row["leaf_availability"]
        for key in _INPUT_LEAVES:
            leaf = observed.get(key) if observed is not None else None
            row[key] = deepcopy(leaf)
            availability[key] = _availability(
                leaf,
                missing_status="not_observed" if observed is not None else missing_status,
                reason=f"{key}_not_observed" if observed is not None else row_missing_reason,
            )
        if observed is not None and "court_owner_source" in observed:
            row["court_owner_source"] = deepcopy(observed["court_owner_source"])
        complete = all(availability[key]["status"] == "available" for key in _INPUT_LEAVES)
        row["observed_inputs_complete"] = complete
        row["status"] = "available" if complete else "partial"
        rows.append(row)

    result["rows"] = rows
    complete = classified and all(row["observed_inputs_complete"] for row in rows)
    result["observed_inputs_complete"] = complete
    result["status"] = "available" if complete else "partial"
    result["unavailable_reason"] = (
        None if complete else "living_child_classification_incomplete" if not classified
        else "one_or_more_child_inputs_not_available")
    return result

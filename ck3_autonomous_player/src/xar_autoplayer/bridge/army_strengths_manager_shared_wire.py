"""Lossless query-level wire sharing for complete ArmyManager input families.

Only the transport representation changes. Internal consumers expand before
the existing family normalizers; those normalizers still own nested semantics.
External callers can use the default detached expansion for mutable full rows.
"""

from __future__ import annotations

from copy import deepcopy
from typing import cast

from .public_unit_contract import public_cunit_ids


SHARED_KEY = "army_manager_inputs_shared_v1"
FIELD_NAMES = (
    "current_daily_assault_roster_admission_v1",
    "current_pre_date_pending_update_inputs_v1",
    "current_post_admission_refresh_inputs_v1",
    "current_selected_title_holder_owner_relation_v1",
    "current_army_combat_roles_phase_inputs_v1",
    "current_army_flag31_inputs_v1",
)
_FIELD_SET = frozenset(FIELD_NAMES)
_BUNDLE_KEYS = frozenset({"schema_version", "army_ids", "fields"})


def pack_army_strengths_manager_inputs(
    payload: dict[str, object],
) -> dict[str, object]:
    """Hoist equal complete manager inputs without copying their nested values.

    The full semantic input remains untouched. Legacy empty, single-row,
    absent-field or divergent results retain their existing inline shape.
    """
    if SHARED_KEY in payload:
        return payload
    raw_rows = payload.get("army_strengths")
    if (
        not isinstance(raw_rows, list)
        or len(raw_rows) < 2
        or any(not isinstance(row, dict) for row in raw_rows)
    ):
        return payload
    rows = cast(list[dict[str, object]], raw_rows)
    first = rows[0]
    present = [name for name in FIELD_NAMES if name in first]
    if not present:
        return payload
    if any(first[name] is not None and not isinstance(first[name], dict) for name in present):
        return payload
    for row in rows[1:]:
        if any(
            (name in row) != (name in first)
            or (name in first and row[name] != first[name])
            for name in FIELD_NAMES
        ):
            return payload
    try:
        army_ids = public_cunit_ids(
            [row.get("army_id") for row in rows], "army_strengths.army_ids",
            nonempty=True,
        )
    except ValueError:
        return payload
    return {
        **payload,
        "army_strengths": [
            {name: value for name, value in row.items() if name not in _FIELD_SET}
            for row in rows
        ],
        SHARED_KEY: {
            "schema_version": 1,
            "army_ids": army_ids,
            "fields": {name: first[name] for name in present},
        },
    }


def expand_army_strengths_manager_inputs(
    payload: dict[str, object], *, detached: bool = True,
) -> dict[str, object]:
    """Restore full rows from shared wire or accept the legacy inline form.

    ``detached=False`` is for the native Driver immediately before its existing
    normalizers, avoiding a redundant copy of these large complete families.
    The default gives external consumers independent mutable per-row values.
    """
    if SHARED_KEY not in payload:
        return deepcopy(payload) if detached else payload
    bundle = payload[SHARED_KEY]
    if not isinstance(bundle, dict) or set(bundle) != _BUNDLE_KEYS:
        raise ValueError(f"{SHARED_KEY} must contain exactly schema_version, army_ids and fields")
    if type(bundle["schema_version"]) is not int or bundle["schema_version"] != 1:
        raise ValueError(f"{SHARED_KEY}.schema_version must be integer 1")
    raw_rows = payload.get("army_strengths")
    if not isinstance(raw_rows, list) or any(not isinstance(row, dict) for row in raw_rows):
        raise ValueError("army_strengths must be an array of objects")
    rows = cast(list[dict[str, object]], raw_rows)
    army_ids = public_cunit_ids(
        bundle["army_ids"], f"{SHARED_KEY}.army_ids", nonempty=True,
    )
    row_ids = public_cunit_ids(
        [row.get("army_id") for row in rows], "army_strengths.army_ids",
        nonempty=True,
    )
    if army_ids != row_ids:
        raise ValueError(f"{SHARED_KEY}.army_ids must exactly match ordered Army rows")
    fields = bundle["fields"]
    if (
        not isinstance(fields, dict)
        or not fields
        or not set(fields) <= _FIELD_SET
        or any(value is not None and not isinstance(value, dict) for value in fields.values())
    ):
        raise ValueError(f"{SHARED_KEY}.fields must be a nonempty subset of the six object-or-null families")
    if any(name in row for row in rows for name in fields):
        raise ValueError(f"{SHARED_KEY} fields collide with inline Army fields")
    result = {
        name: value for name, value in payload.items()
        if name not in {SHARED_KEY, "army_strengths"}
    }
    if detached:
        result = deepcopy(result)
    result["army_strengths"] = [
        {
            **(deepcopy(row) if detached else row),
            **(deepcopy(fields) if detached else fields),
        }
        for row in rows
    ]
    return result

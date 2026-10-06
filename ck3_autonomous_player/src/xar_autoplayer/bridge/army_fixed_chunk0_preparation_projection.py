"""Source-defined262C6A0 result for a captured persistent fixed-chunk0 entry."""
from __future__ import annotations

from collections.abc import Mapping, Sequence

_DEFINITION_MAGIC = 0x4744624F
_OPERANDS = (
    "containing_guard_138_raw", "containing_definition_magic_38",
    "native_fixed_chunk0_can_replenish", "fresh_fraction_raw",
)


def _persistent_preparation(row: Mapping[str, object]) -> dict[str, object]:
    guard = row["containing_guard_138_raw"]
    magic = row["containing_definition_magic_38"]
    permission = row["native_fixed_chunk0_can_replenish"]
    fresh = row["fresh_fraction_raw"]
    branch = "unknown"
    missing = []
    raw = None
    # Special magic closes the permission branch independently of guard.
    # A known nonzero guard never demands the definition magic.
    if (guard is not None and guard != 0) or magic == _DEFINITION_MAGIC:
        needs_permission = True
    elif guard == 0 and magic is not None:
        needs_permission = False
    else:
        needs_permission = None
        if guard is None:
            missing.append("containing_guard_138_raw")
        if magic is None:
            missing.append("containing_definition_magic_38")
    if needs_permission is False:
        branch = "ordinary_guard_bypass"
        if fresh is None:
            missing.append("fresh_fraction_raw")
        else:
            raw = fresh
    elif needs_permission is True:
        if permission is None:
            missing.append("native_fixed_chunk0_can_replenish")
        elif permission is False:
            branch = "fixed_chunk0_permission_false"
            raw = 0
        else:
            branch = "fixed_chunk0_permission_true"
            if fresh is None:
                missing.append("fresh_fraction_raw")
            else:
                raw = fresh
    ready = raw is not None
    result = {
        "persistent_regiment_id": row["persistent_regiment_id"],
        "fixed_chunk_index": 0,
        "status": "available" if ready else "partial" if any(
            row[key] is not None for key in _OPERANDS) else "unavailable",
        "native_input_status": row["status"], "native_input_ready": row["ready"],
        "preparation_ready": ready,
        "conditional_prepared_fraction_raw": raw,
        "fraction_scale": 100000,
        "preparation_branch": branch,
        "missing_inputs": missing,
        "actual_preparation": False, "cache_write": False,
        "full_ordered_regular_refill": False,
    }
    result.update({key: row[key] for key in _OPERANDS})
    return result


def project_fixed_chunk0_preparation_family_v1(
    family: Mapping[str, object] | None, *, army_id: object, native_carmy_id: object,
    coverage_key: str = "referenced_persistent_ids_complete",
    input_name: str = "fixed_chunk0_preparation_inputs_v1",
    projection_kind: str = "conditional_fixed_chunk0_preparation",
) -> dict[str, object]:
    """Reuse native preparation branches directly for a declared captured family."""
    rows = []
    complete = False
    missing = []
    if isinstance(family, Mapping):
        complete = family[coverage_key]
        rows = [_persistent_preparation(row) for row in family["persistent_regiments"]]
        if not complete:
            missing.append({"persistent_regiment_id": None, "inputs": [coverage_key]})
        missing.extend({"persistent_regiment_id": row["persistent_regiment_id"],
                        "inputs": list(row["missing_inputs"])}
                       for row in rows if not row["preparation_ready"])
    else:
        missing.append({"persistent_regiment_id": None, "inputs": [input_name]})
    ready = bool(complete and all(row["preparation_ready"] for row in rows))
    return {
        "projection_kind": projection_kind, "source_contract_game_version": "1.20.0.3",
        "input_basis": "current_frozen_context_preparation",
        "army_id": army_id, "native_carmy_id": native_carmy_id,
        "status": "available" if ready else "partial" if rows or complete else "unavailable",
        "preparation_ready": ready, coverage_key: complete,
        "persistent_regiments": rows, "missing_inputs": missing,
        "actual_preparation": False, "cache_write": False, "full_ordered_regular_refill": False,
    }


def project_fixed_chunk0_preparations_v1(
    selected_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Project normalized Strength rows without changing DATA or observed prepared148."""
    return [project_fixed_chunk0_preparation_family_v1(
        army.get("fixed_chunk0_preparation_inputs_v1"),
        army_id=army.get("army_id"), native_carmy_id=army.get("native_carmy_id"))
        for army in selected_rows]

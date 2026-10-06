"""Conditional preparation for the actual same-query target physical union."""
from collections.abc import Mapping, Sequence

from .army_fixed_chunk0_preparation_projection import project_fixed_chunk0_preparation_family_v1


def project_ordered_besieging_fixed_chunk0_preparations_v1(
    selected_rows: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    results = []
    for row in selected_rows:
        family = row.get("ordered_besieging_fixed_chunk0_preparation_inputs_v1")
        result = project_fixed_chunk0_preparation_family_v1(
            family, army_id=row.get("army_id"), native_carmy_id=row.get("native_carmy_id"),
            coverage_key="target_persistent_ids_complete",
            input_name="ordered_besieging_fixed_chunk0_preparation_inputs_v1",
            projection_kind="conditional_ordered_B_fixed_chunk0_preparation")
        result.update(
            scope_kind="actual_ordered_besieging_target_physical_union",
            province_id=family["province_id"] if isinstance(family, Mapping) else None,
            source_scope_status=family["source_scope_status"] if isinstance(family, Mapping) else None)
        results.append(result)
    return results

"""Add the independently replayed current DATA prefix to an Army query."""
from __future__ import annotations

from typing import Mapping

from .army_current_detachment_data_projection import project_current_detachment_data_prefix


def build_same_input_current_detachment_data_prefix(
        army_strength_or_family: Mapping | None, *, current_date_storage_raw64: int | None = None) -> dict:
    """Accept a normalized Army row or the normalized optional family itself."""
    row = army_strength_or_family if isinstance(army_strength_or_family, Mapping) else {}
    is_family = row.get("source") == "native_current_detachment_data_inputs"
    family = row if is_family else row.get("current_detachment_data_inputs_v1")
    if current_date_storage_raw64 is None and not is_family:
        monthly = row.get("monthly_caller_effect_inputs_v1")
        if isinstance(monthly, Mapping):
            current_date_storage_raw64 = monthly.get("current_date_storage_raw64")
    result = project_current_detachment_data_prefix(
        family, current_date_storage_raw64=current_date_storage_raw64)
    if not is_family:
        result["subject_army_id"] = row.get("army_id")
        result["subject_native_carmy_id"] = row.get("native_carmy_id")
    return result

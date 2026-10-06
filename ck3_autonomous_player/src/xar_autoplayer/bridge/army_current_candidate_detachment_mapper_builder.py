"""Build the additive current candidate mapper preview from a normalized Army row."""
from __future__ import annotations

from typing import Mapping

from .army_current_candidate_detachment_mapper_projection import project_current_candidate_detachment_mapper


def build_current_candidate_detachment_mapper_preview(army_strength: Mapping) -> dict:
    """Keep current candidate observation independent of conditional future queues."""
    result = project_current_candidate_detachment_mapper(
        army_strength.get("current_candidate_detachment_mapper_inputs_v1"))
    result["subject_army_id"] = army_strength.get("army_id")
    result["subject_native_carmy_id"] = army_strength.get("native_carmy_id")
    return result

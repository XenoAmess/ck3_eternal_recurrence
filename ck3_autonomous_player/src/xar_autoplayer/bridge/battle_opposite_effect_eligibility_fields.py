"""Independent current retained-row eligibility diagnostic in the same query."""

from __future__ import annotations

import copy
from typing import Mapping

from ..simulation.battle_actual_opposite_effect_eligibility import (
    adapt_actual_opposite_effect_eligibility, evaluate_actual_opposite_effect_eligibility,
)


def opposite_effect_eligibility_fields(
    snapshot: Mapping[str, object], source: Mapping[str, object], qualified: bool,
) -> dict[str, object]:
    geometry = snapshot.get('actual_geography_v1')
    stored = geometry.get('stored_advantage_sources_v1') if geometry is not None else None
    if stored is None:
        return {}
    diagnostic = {'schema_version': 1, 'current_frame_qualified': qualified,
                  'source': copy.deepcopy(source), 'stored_inputs': copy.deepcopy(stored)}
    inputs = adapt_actual_opposite_effect_eligibility(diagnostic)
    diagnostic['current_eligibility'] = evaluate_actual_opposite_effect_eligibility(inputs) if inputs is not None else None
    return {'opposite_effect_eligibility_v1': diagnostic}

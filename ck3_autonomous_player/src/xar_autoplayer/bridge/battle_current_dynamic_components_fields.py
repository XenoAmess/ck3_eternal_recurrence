"""Independent service diagnostic for the optional same-frame component leaf."""

from __future__ import annotations

import copy
from typing import Mapping

from ..simulation.battle_actual_current_dynamic_components import (
    adapt_actual_current_dynamic_components, evaluate_actual_current_dynamic_components,
)


def current_dynamic_component_fields(
    snapshot: Mapping[str, object], source: Mapping[str, object], qualified: bool,
) -> dict[str, object]:
    geometry = snapshot.get('actual_geography_v1')
    current = geometry.get('current_dynamic_components_v1') if geometry is not None else None
    if current is None:
        return {}
    diagnostic = {'schema_version': 1, 'current_frame_qualified': qualified,
                  'source': copy.deepcopy(source), 'current_inputs': copy.deepcopy(current),
                  'direct_inputs': copy.deepcopy(geometry.get('current_dynamic_advantage_v1'))}
    inputs = adapt_actual_current_dynamic_components(diagnostic)
    diagnostic['current_components'] = evaluate_actual_current_dynamic_components(inputs) if inputs is not None else None
    return {'current_dynamic_components_v1': diagnostic}

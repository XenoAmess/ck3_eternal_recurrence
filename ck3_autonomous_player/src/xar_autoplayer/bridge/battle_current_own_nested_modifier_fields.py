"""Publish independent current scoped amounts and source-bound nested terms."""

from __future__ import annotations

import copy
from typing import Mapping

from ..simulation.battle_actual_own_nested_modifier import (
    adapt_actual_own_nested_modifier, evaluate_actual_own_nested_modifier,
)


def current_own_nested_modifier_fields(
    snapshot: Mapping[str, object], source: Mapping[str, object], qualified: bool,
) -> dict[str, object]:
    geometry = snapshot.get('actual_geography_v1')
    own = geometry.get('current_own_nested_modifier_v1') if geometry is not None else None
    if own is None:
        return {}
    diagnostic = {'schema_version': 1, 'current_frame_qualified': qualified,
                  'source': copy.deepcopy(source), 'own_inputs': copy.deepcopy(own),
                  'stored_inputs': copy.deepcopy(geometry.get('stored_advantage_sources_v1'))}
    inputs = adapt_actual_own_nested_modifier(diagnostic)
    diagnostic['current_nested_contributions'] = evaluate_actual_own_nested_modifier(inputs) if inputs is not None else None
    return {'current_own_nested_modifier_v1': diagnostic}

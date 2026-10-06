"""Load only the ten new compiled whole ArmyStrength sample wires."""
from __future__ import annotations

import json
from pathlib import Path

SAMPLE_NAMES = (
    'invalid-first-province-undemanded', 'direct-equal', 'native-false-owner-zero',
    'native-true-holder-zero', 'native-true-highbit-fullgen', 'requested-generation-fallbacks',
    'missing-holder-parent-tier-one', 'missing-holder-other-tier',
    'null-inner-stores-undemanded', 'missing-callable',
)


def load_compiled_selected_title_holder_owner_relation_wire(path: str) -> dict:
    wire = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if (type(wire) is not dict or type(wire.get('samples')) is not dict
            or tuple(wire['samples']) != SAMPLE_NAMES
            or any(type(row) is not dict for row in wire['samples'].values())):
        raise ValueError('FIRST selected-holder consumer requires exactly its ten new compiled whole samples')
    return wire

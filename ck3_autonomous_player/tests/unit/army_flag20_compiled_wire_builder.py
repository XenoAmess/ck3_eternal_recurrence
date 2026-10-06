"""Load only the six new compiled whole ArmyStrength wires, no baseline builder."""
from __future__ import annotations
import json
from pathlib import Path

SAMPLE_NAMES = (
    'zero-1d4-undemanded', 'native-false-fullgen', 'native-true-highbit-fullgen',
    'native-true-generation-fallback', 'missing-getter', 'missing-army-materialization',
)


def load_compiled_flag20_wire(path: str) -> dict:
    wire = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if tuple(wire['samples']) != SAMPLE_NAMES:
        raise ValueError('FIRST flag20 consumer requires exactly its six new compiled whole samples')
    return wire

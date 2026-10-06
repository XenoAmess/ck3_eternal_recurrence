"""Load only nine NEW compiled whole-query rows; no synthetic native leaf builder."""
from __future__ import annotations
import json
from pathlib import Path

SAMPLE_NAMES = (
    'source-zero-1ec-undemanded', 'positive-qword-native-false', 'positive-qword-native-true',
    'native-static-header-zero-fullgen0', 'carrier-negative-header-native-true',
    'null-stores-fallback-header-native-false', 'missing-shared-tail-callable',
    'missing-demanded-header-count', 'missing-army-materialization',
)


def load_compiled_flag21_wire(path: str) -> dict:
    wire = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if tuple(wire['samples']) != SAMPLE_NAMES:
        raise ValueError('FIRST flag21 consumer requires exactly nine NEW compiled whole samples')
    return wire

"""Synthetic Service envelope around a genuine compiled NEW condition30 leaf.

The snapshot/public Army fields are scaffolding and carry no native/live credit.
No old numeric/Core samples or fallback native leaf are constructed here.
"""
from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path

SAMPLE_NAMES = (
    'zero-1d4-undemanded', 'native-true-returned-context-repeats',
    'native-false-invalid-root-is-verdict', 'high-bit-owner-zeroextends',
    'zero-full-unit-and-owner', 'unit-generation-fallback', 'unit-store-null-fallback',
    'missing-condition-receiver', 'constructor-null-return-paired-destroy',
)


def load_compiled_condition30_wire(path: str) -> dict:
    wire = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    if tuple(wire['samples']) != SAMPLE_NAMES:
        raise ValueError('FIRST condition30 consumer needs exactly its nine new compiled samples')
    return wire


def service_source_row(leaf: dict) -> dict:
    return {
        'status': 'available', 'army_id': 11, 'native_carmy_id': 12, 'scope_role': 'player',
        'war_ids': [], 'regiment_count': 0, 'current_soldiers': 160, 'maximum_soldiers': 240,
        'ai_base_power_raw': 0, 'ai_base_power_scale': 100000, 'unavailable_reason': None,
        'current_army_condition30_inputs_v1': deepcopy(leaf),
    }

"""Actual4 person PC arithmetic from 2303100 and 2303380.

The large-operand path decomposes the signed maximum, as observed at
23031C7/23031D3/23031D7 and 230340F/230341B/230341F. This module does not
substitute current Model values for a historical pre-six-stage aggregate.
Parallel insertion is a logical-container projection of the observed
reallocation postimage. No physical allocator or uncaptured spare-capacity
path equivalence is claimed.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping


Q_12004 = 100000
_MASK64 = (1 << 64) - 1
_BOUND = 0xB504F333
_DOUBLE_BOUND = 0x16A09E666
_DIV_MAGIC = 0x29F16B11C6D1E109


def _signed64(value: int) -> int:
    value &= _MASK64
    return value - (1 << 64) if value & (1 << 63) else value


def _divide_q_from_instructions(value: int) -> int:
    """Signed IMUL high half, SAR14, SHR63 and ADD; no unbounded-product shortcut."""
    high = (_signed64(value) * _DIV_MAGIC) >> 64
    shifted = high >> 14
    return _signed64(shifted + ((shifted & _MASK64) >> 63))


def native_fixed_mul_q_12004(value: int, weight: int) -> int:
    """Return the actual wrapped signed64 Q100000 product, including its max split."""
    value, weight = _signed64(value), _signed64(weight)
    if (((value + _BOUND) & _MASK64) <= _DOUBLE_BOUND
            and ((weight + _BOUND) & _MASK64) <= _DOUBLE_BOUND):
        return _divide_q_from_instructions(_signed64(value * weight))
    maximum, minimum = (value, weight) if value >= weight else (weight, value)
    quotient = _divide_q_from_instructions(maximum)
    remainder = _signed64(maximum - _signed64(quotient * Q_12004))
    integral = _signed64(quotient * minimum)
    fractional = _divide_q_from_instructions(_signed64(remainder * minimum))
    return _signed64(integral + fractional)


def _native_key_rank(keys: list[int], key: int) -> int:
    """Preserve 2303930..230394F, including physical input order."""
    first, remaining = 0, len(keys)
    while remaining:
        half = remaining >> 1
        if keys[first + half] < key:
            first += remaining - half
        remaining = half
    return first


def fold_ordered_pc_contribution_12004(
        requests: Iterable[Mapping[str, object]]) -> dict:
    """Compose supplied requests against an explicitly empty aggregate.

    This is a conditional contribution, not a captured historical postimage.
    Callers use the original emitted order and weights; no skill or feedback
    recomputation occurs. Inputs are the existing normalized property blocks.
    """
    keys: list[int] = []
    values: list[int] = []
    ordinals: list[int] = []
    for request in requests:
        ordinals.append(request["source_ordinal"])
        block = request["property_block"]
        count = block["keys_count"]
        if count == 0:
            continue
        source_keys, source_values = block["keys_u16"], block["values_q64"]
        weight = request["weight_q100000"]
        if not keys:
            keys[:] = source_keys[:count]
            values[:] = (source_values[:count] if weight == Q_12004 else
                         [native_fixed_mul_q_12004(value, weight)
                          for value in source_values[:count]])
            continue
        for index in range(count):
            term = native_fixed_mul_q_12004(source_values[index], weight)
            key = source_keys[index]
            if key == 0xFFFF:
                continue
            rank = _native_key_rank(keys, key)
            if rank == len(keys) or keys[rank] != key:
                keys.insert(rank, key)
                values.insert(rank, 0)
            values[rank] = _signed64(values[rank] + term)
    return {
        "keys_u16": keys,
        "values_q64": values,
        "source_ordinals": ordinals,
        "composition_kind": "explicit_empty_baseline_contribution",
        "merger_source_rva": "0x2303100",
        "scaling_source_rva": "0x2303380",
        "index_source_rva": "0x2303900",
        "pre_six_baseline_observed": False,
        "historical_postimage_ready": False,
        "actual_model_write_performed": False,
        "full_helper_ready": False,
        "full_person_ready": False,
        "entry_ready": False,
    }


def compose_captured_six_stage_contribution_12004(section: object) -> dict:
    """Use Native62's ready request emitter, retaining its captured feedback."""
    from ..bridge.battle_person_six_stage_capture_12004 import (
        emit_captured_person_six_stage_requests_12004,
    )

    return fold_ordered_pc_contribution_12004(
        emit_captured_person_six_stage_requests_12004(section))

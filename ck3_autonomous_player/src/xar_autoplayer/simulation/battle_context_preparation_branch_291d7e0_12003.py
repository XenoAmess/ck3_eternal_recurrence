"""Ordered current 291D7E0 contribution prefix from actual native inputs.

Admission/first-ID selection and token/classifier observations are upstream.
Unit-Q logical copy/merge follows the adopted materialized-prefix contract
7a10be17 (a65fd887). No prestage baseline, native writer or Entry is inferred.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .battle_trait_numeric_inputs_12003 import (
    PropertyContainer12003,
    native_fixed_mul_q_12003,
    native_wrap64_12003,
)


UNIT_WEIGHT_Q_12003 = 100000
UNIT_MERGE_CONTRACT_SHA256_12003 = (
    "7a10be179170eae2226f878a97e731cb138455332aaa3816963d0fc134d30c83"
)


@dataclass(frozen=True, slots=True)
class NativePreparationBContribution12003:
    native_source_index: int
    source_identity: str
    properties: PropertyContainer12003
    weight_q64: int = UNIT_WEIGHT_Q_12003


@dataclass(frozen=True, slots=True)
class NativePreparationBResult12003:
    character_id: int | None
    contributions: tuple[NativePreparationBContribution12003, ...]
    contributions_ready: bool
    status: str
    missing_inputs: tuple[str, ...]
    verified_source_count: int
    stopped_source_native_index: int | None
    deferred_source_native_indices: tuple[int, ...]
    source_results: tuple[Mapping[str, object], ...]
    source_provenance: Mapping[str, object] | None
    full_future_context_ready: bool = False
    native_write_performed: bool = False
    actual_game_days_advanced: int = 0

    @property
    def ready(self) -> bool:
        return self.contributions_ready


def _gap(gaps: list[str], path: str) -> None:
    if path not in gaps:
        gaps.append(path)


def _array(value: object) -> list | None:
    return list(value) if isinstance(value, (tuple, list)) else None


def _base_copy(raw: object, path: str, gaps: list[str]) -> tuple[list[int], list[int]] | None:
    if not isinstance(raw, Mapping):
        _gap(gaps, path)
        return None
    copied = []
    for count_key, array_key in (("keys_count", "keys_u16"), ("values_count", "values_q64")):
        count, values = raw.get(count_key), _array(raw.get(array_key))
        if type(count) is not int or count < 0:
            _gap(gaps, path + "." + count_key)
            continue
        if values is None or len(values) < count:
            _gap(gaps, path + "." + array_key)
            continue
        values = values[:count]
        for i, value in enumerate(values):
            if type(value) is not int or (array_key == "keys_u16" and not 0 <= value <= 65535):
                _gap(gaps, f"{path}.{array_key}[{i}]")
        copied.append(values if array_key == "keys_u16" else [native_wrap64_12003(v) for v in values if type(v) is int])
    return (copied[0], copied[1]) if len(copied) == 2 and not gaps else None


def _lower_bound(keys: list[int], key: int) -> int:
    low, high = 0, len(keys)
    while low < high:
        middle = (low + high) // 2
        if keys[middle] < key:
            low = middle + 1
        else:
            high = middle
    return low


def _merge_unit(
    keys: list[int], values: list[int], raw: object, path: str, gaps: list[str],
) -> tuple[list[int], list[int]] | None:
    if not isinstance(raw, Mapping):
        _gap(gaps, path)
        return None
    count = raw.get("keys_count")
    if type(count) is not int or count < 0:
        _gap(gaps, path + ".keys_count")
        return None
    if count == 0:
        # No numerical key contribution. Empty-source auxiliary copy effects
        # are outside this logical result, which never exposes a physical PC.
        return keys, values
    source_keys, source_values = _array(raw.get("keys_u16")), _array(raw.get("values_q64"))
    for name, array in (("keys_u16", source_keys), ("values_q64", source_values)):
        if array is None or len(array) < count:
            _gap(gaps, path + "." + name)
        elif any(type(v) is not int or (name == "keys_u16" and not 0 <= v <= 65535) for v in array[:count]):
            _gap(gaps, path + "." + name)
    if gaps:
        return None
    if not keys:
        # The source-closed empty destination clones full paired arrays,
        # including FFFF; unit scaling is identity. +74 is needed here.
        if raw.get("values_count") != count:
            _gap(gaps, path + ".empty_copy_paired_values_count")
            return None
        return source_keys[:count], [native_wrap64_12003(v) for v in source_values[:count]]
    if len(values) != len(keys):
        _gap(gaps, "temporary_property_container.nonempty_paired_active_arrays")
        return None
    for i in range(count):
        key = source_keys[i]
        term = native_fixed_mul_q_12003(source_values[i], UNIT_WEIGHT_Q_12003)
        if key == 65535:
            continue
        position = _lower_bound(keys, key)
        if position == len(keys) or keys[position] != key:
            keys.insert(position, key)
            values.insert(position, 0)
        values[position] = native_wrap64_12003(values[position] + term)
    return keys, values


def compose_291d7e0_current_contributions_12003(
    normalized_current_context_source_inputs: Mapping[str, object] | None,
    *, source_provenance: Mapping[str, object] | None = None,
) -> NativePreparationBResult12003:
    """Return the verified source prefix, stopping at its first unknown source.

    Base headers/arrays are copied independently. Actual admitted booleans
    select A, then B, then C blocks in stored order. A false admission never
    reads its PC. Zero final keys skip a weighted request. An unknown source
    stops installation of all later sources, preserving the earlier prefix.
    """
    section = normalized_current_context_source_inputs or {}
    branch = section.get("branch_291d7e0")
    character_id = section.get("character_id")
    character_id = character_id if type(character_id) is int else None
    gaps: list[str] = []
    output: list[NativePreparationBContribution12003] = []
    ledger: list[Mapping[str, object]] = []
    verified = 0
    stopped = None
    source_count = branch.get("source_count") if isinstance(branch, Mapping) else None
    source_rows = _array(branch.get("source_rows")) if isinstance(branch, Mapping) else None
    if type(source_count) is not int:
        _gap(gaps, "branch_291d7e0.source_count")
    elif source_count > 0:
        for source_index in range(source_count):
            path = f"branch_291d7e0.source_rows[{source_index}]"
            local: list[str] = []
            steps: list[Mapping[str, object]] = []
            source = source_rows[source_index] if source_rows is not None and source_index < len(source_rows) else None
            if not isinstance(source, Mapping):
                _gap(local, path)
                copied = None
            else:
                identity = source.get("source_identity")
                if type(identity) is not str or not identity:
                    _gap(local, path + ".source_identity")
                copied = _base_copy(source.get("base_properties"), path + ".base_properties", local)
            if copied is not None:
                keys, values = copied
                for kind in ("a", "b", "c"):
                    count = source.get(f"conditional_{kind}_count")
                    rows = _array(source.get(f"conditional_{kind}_rows"))
                    group_path = path + f".conditional_{kind}_rows"
                    if type(count) is not int:
                        _gap(local, path + f".conditional_{kind}_count")
                        break
                    if count <= 0:
                        continue
                    for row_index in range(count):
                        row = rows[row_index] if rows is not None and row_index < len(rows) else None
                        row_path = f"{group_path}[{row_index}]"
                        admitted = row.get("admitted") if isinstance(row, Mapping) else None
                        if type(admitted) is not bool:
                            _gap(local, row_path + ".admitted")
                            steps.append({"kind": kind, "native_index": row_index, "status": "unknown_admission", "reason": row.get("reason") if isinstance(row, Mapping) else None})
                            break
                        steps.append({"kind": kind, "native_index": row_index, "admitted": admitted, "property_source": row.get("property_source"), "token_origin": row.get("token_origin")})
                        if admitted:
                            merged = _merge_unit(keys, values, row.get("property_block"), row_path + ".property_block", local)
                            if merged is None:
                                break
                            keys, values = merged
                    if local:
                        break
                if not local and keys and len(values) < len(keys):
                    _gap(local, path + ".temporary_property_container.consumed_values_q64")
            if local:
                gaps.extend(local)
                stopped = source_index
                ledger.append({"native_source_index": source_index, "status": "partial_frontier", "steps": tuple(steps), "missing_inputs": tuple(local)})
                break
            verified += 1
            if not keys:
                ledger.append({"native_source_index": source_index, "status": "zero_key_count_skip", "steps": tuple(steps)})
                continue
            properties = PropertyContainer12003(tuple(keys), tuple(values), len(keys))
            output.append(NativePreparationBContribution12003(source_index, source["source_identity"], properties))
            ledger.append({"native_source_index": source_index, "status": "emitted", "steps": tuple(steps), "weight_q64": UNIT_WEIGHT_Q_12003})
    deferred = tuple(range(stopped + 1, source_count)) if stopped is not None else ()
    ready = not gaps
    return NativePreparationBResult12003(
        character_id, tuple(output), ready, "computed" if ready else "partial", tuple(gaps),
        verified, stopped, deferred, tuple(ledger), source_provenance,
    )

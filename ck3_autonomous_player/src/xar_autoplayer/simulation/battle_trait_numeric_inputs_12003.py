"""Exact .3 six-skill arithmetic from supplied actual native operands.

The carrier is current_person_state.raw_numeric_inputs. This pure primitive
never constructs modifier context from a trait flag, updates a Character or
Entry, or advances a horizon. Future calculations need explicit updated native
operands. Source: v77 cached-writer-role and numeric-chain, frozen EXE 94B55397.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Mapping


Q_12003 = 100000
SKILL_NAMES_12003 = (
    "diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess",
)
CAP_RVAS_12003 = (
    "5C6A0D8", "5C6A0D4", "5C6A0BC", "5C6A0B8", "5C6A0C0", "5C6A0C4",
)
SOURCE_EXE_SHA256_12003 = (
    "94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6"
)


@dataclass(frozen=True, slots=True)
class PropertyContainer12003:
    keys_u16: tuple[int | None, ...] | None = None
    values_q64: tuple[int | None, ...] | None = None
    count: int | None = None


@dataclass(frozen=True, slots=True)
class WeightedModifierRow12003:
    properties: PropertyContainer12003 | None = None
    weight_q64: int | None = None
    native_index: int | None = None


@dataclass(frozen=True, slots=True)
class NativeModifierContext12003:
    aggregate_properties: PropertyContainer12003 | None = None
    weighted_rows: tuple[WeightedModifierRow12003 | None, ...] | None = None
    weighted_count: int | None = None


@dataclass(frozen=True, slots=True)
class CategoryOperands12003:
    metric_raw: int | None = None
    override_raw: int | None = None
    thresholds_raw: tuple[int | None, ...] | None = None
    threshold_count: int | None = None


@dataclass(frozen=True, slots=True)
class NativeSkillCacheInputs12003:
    base_points: tuple[int | None, ...] | None = None
    context: NativeModifierContext12003 | None = None
    scratch_present: bool | None = None
    category_counts: tuple[int | None, ...] | None = None
    category_operands: tuple[CategoryOperands12003 | None, ...] | None = None
    scratch_factor_numerator: int | None = None
    scratch_factor_denominator: int | None = None
    caps: tuple[int | None, ...] | None = None
    prowess_adjustment: int | None = None
    character_id: int | None = None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class NativeSkillCacheResult12003:
    character_id: int | None
    raw_points: tuple[int | None, ...]
    first_clipped_points: tuple[int | None, ...]
    final_cache_points: tuple[int | None, ...]
    missing_inputs: tuple[str, ...]
    calculation_ready: bool
    status: str
    ledger: Mapping[str, object]
    native_write_performed: bool = False
    full_native_callback_ready: bool = False
    trait_to_context_constructed: bool = False
    actual_game_days_advanced: int = 0


def native_wrap32_12003(value: int) -> int:
    value &= (1 << 32) - 1
    return value - (1 << 32) if value & (1 << 31) else value


def native_wrap64_12003(value: int) -> int:
    value &= (1 << 64) - 1
    return value - (1 << 64) if value & (1 << 63) else value


def _trunc_div(numerator: int, denominator: int) -> int:
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def _trunc_q(value: int) -> int:
    # Source magic signed high-multiply/SAR14/sign correction implements /Q.
    return _trunc_div(native_wrap64_12003(value), Q_12003)


def _fixed_mul_q(a: int, b: int) -> tuple[int, str]:
    a = native_wrap64_12003(a)
    b = native_wrap64_12003(b)
    bound = 3037000499
    mask = (1 << 64) - 1
    a_in_range = ((a + bound) & mask) <= bound * 2
    b_in_range = ((b + bound) & mask) <= bound * 2
    if a_in_range and b_in_range:
        return _trunc_q(native_wrap64_12003(a * b)), "fast"
    lo, hi = (a, b) if a <= b else (b, a)
    quotient = _trunc_q(lo)
    remainder = native_wrap64_12003(
        lo - native_wrap64_12003(quotient * Q_12003))
    integral = native_wrap64_12003(quotient * hi)
    fractional = _trunc_q(native_wrap64_12003(remainder * hi))
    return native_wrap64_12003(integral + fractional), "decomposed"


def native_fixed_mul_q_12003(a: int, b: int) -> int:
    """Preserve native signed64 fast/decomposed product and truncation."""
    return _fixed_mul_q(a, b)[0]


def _scratch_factor(numerator: int, denominator: int) -> tuple[int, str]:
    n = native_wrap32_12003(numerator)
    d = native_wrap32_12003(denominator)
    value = n * Q_12003
    divisor = d * Q_12003
    if divisor == 0:
        # MOV R11D,FFFFFFFF zero-extends to 4294967295 before final /Q.
        return native_wrap32_12003(_trunc_q(0xFFFFFFFF)), "zero_denominator"
    bound = 92233720368547
    if ((value + bound) & ((1 << 64) - 1)) <= 2 * bound:
        scaled = _trunc_div(
            native_wrap64_12003(value * Q_12003), divisor)
        branch = "fast_divide"
    elif abs(divisor) >= Q_12003 * Q_12003:
        scaled = _trunc_div(value, _trunc_q(divisor))
        branch = "large_denominator"
    else:
        quotient = _trunc_q(value)
        integral_value = native_wrap64_12003(quotient * Q_12003)
        remainder = native_wrap64_12003(value - integral_value)
        integral_quotient = _trunc_div(integral_value, divisor)
        integral_remainder = (
            integral_value - integral_quotient * divisor)
        scaled = _trunc_div(
            native_wrap64_12003(remainder * Q_12003), divisor)
        scaled = native_wrap64_12003(scaled + _trunc_div(
            native_wrap64_12003(integral_remainder * Q_12003), divisor))
        scaled = native_wrap64_12003(
            scaled + native_wrap64_12003(integral_quotient * Q_12003))
        branch = "small_denominator_decomposition"
    return native_wrap32_12003(_trunc_q(scaled)), branch


def native_scratch_factor_multiplier_12003(
    numerator: int, denominator: int,
) -> int:
    """Exact 28BC5A0 result in the actual 9450 signed32 operand domain."""
    return _scratch_factor(numerator, denominator)[0]


class _Calculation:
    def __init__(self) -> None:
        self.missing: dict[str, None] = {}
        self.lookups: list[Mapping[str, object]] = []
        self.weighted_terms: list[Mapping[str, object]] = []
        self.components: list[Mapping[str, object]] = []

    def gap(self, path: str) -> None:
        self.missing[path] = None

    def i32(self, value: object, path: str) -> int | None:
        if type(value) is not int:
            self.gap(path)
            return None
        return native_wrap32_12003(value)

    def i64(self, value: object, path: str) -> int | None:
        if type(value) is not int:
            self.gap(path)
            return None
        return native_wrap64_12003(value)

    def item(self, values: object, index: int, path: str) -> object:
        if isinstance(values, (tuple, list)) and index < len(values):
            return values[index]
        self.gap(path)
        return None

    def property_value(
        self, container: PropertyContainer12003 | None, key: int, path: str,
    ) -> int | None:
        key &= 0xFFFF
        if key == 0xFFFF:
            self.lookups.append({"path": path, "key": key,
                                 "status": "native_sentinel_zero", "value_q64": 0})
            return 0
        if container is None:
            self.gap(path)
            return None
        count = self.i32(container.count, path + ".count")
        if count is None:
            return None
        if count == 0:
            self.lookups.append({"path": path, "key": key,
                                 "status": "native_empty_zero", "value_q64": 0})
            return 0
        if count < 0:
            self.gap(path + ".negative_count_address_view")
            return None
        keys = container.keys_u16
        if keys is None:
            self.gap(path + ".keys_u16")
            return None
        # 2303700's source lower_bound over materialized native U16 keys.
        offset, remaining = 0, count
        while remaining > 0:
            half = remaining >> 1
            probe = offset + half
            raw_key = self.item(keys, probe, path + ".keys_u16[" + str(probe) + "]")
            if type(raw_key) is not int:
                self.gap(path + ".keys_u16[" + str(probe) + "]")
                return None
            if (raw_key & 0xFFFF) < key:
                offset += remaining - half
            remaining = half
        if offset == count:
            self.lookups.append({"path": path, "key": key,
                                 "status": "native_missing_key_zero", "value_q64": 0})
            return 0
        raw_key = self.item(keys, offset, path + ".keys_u16[" + str(offset) + "]")
        if type(raw_key) is not int:
            self.gap(path + ".keys_u16[" + str(offset) + "]")
            return None
        if key < (raw_key & 0xFFFF):
            self.lookups.append({"path": path, "key": key,
                                 "status": "native_missing_key_zero", "value_q64": 0})
            return 0
        value = self.i64(self.item(
            container.values_q64, offset, path + ".values_q64[" + str(offset) + "]"),
            path + ".values_q64[" + str(offset) + "]")
        self.lookups.append({"path": path, "key": key, "index": offset,
                             "status": "value" if value is not None else "partial",
                             "value_q64": value})
        return value

    def context_value(
        self, context: NativeModifierContext12003 | None, key: int, mode: int,
    ) -> int | None:
        if context is None:
            self.gap("context")
            return None
        if mode == 0:
            return self.property_value(
                context.aggregate_properties, key, "context.aggregate_properties")
        count = self.i32(context.weighted_count, "context.weighted_count")
        if count is None:
            return None
        if count == 0:
            return 0
        if count < 0:
            self.gap("context.weighted_rows.negative_count_address_view")
            return None
        total = 0
        complete = True
        for index in range(count):
            path = "context.weighted_rows[" + str(index) + "]"
            row = self.item(context.weighted_rows, index, path)
            if not isinstance(row, WeightedModifierRow12003):
                self.gap(path)
                complete = False
                continue
            weight = self.i64(row.weight_q64, path + ".weight_q64")
            value = self.property_value(row.properties, key, path + ".properties")
            if weight is None or value is None:
                complete = False
                continue
            term, branch = _fixed_mul_q(weight, value)
            admitted = ((mode == 1 and term > 0)
                        or (mode == 2 and term < 0)
                        or mode not in (1, 2))
            if admitted:
                total = native_wrap64_12003(total + term)
            self.weighted_terms.append({
                "key": key, "mode": mode, "native_index": row.native_index,
                "row_index": index, "weight_q64": weight,
                "property_q64": value, "product_q64": term,
                "fixed_multiply_branch": branch, "admitted": admitted,
            })
        return total if complete else None

    def component(
        self, context: NativeModifierContext12003 | None, key: int,
        multiplier: int | None, mode: int,
    ) -> int | None:
        value = self.context_value(context, key, mode)
        if multiplier is None or value is None:
            result = None
            product = None
        else:
            product = native_wrap64_12003(
                native_wrap32_12003(multiplier) * value)
            result = native_wrap32_12003(_trunc_q(product))
        self.components.append({
            "key": key, "mode": mode, "multiplier": multiplier,
            "property_q64": value, "plain_wrap64_product": product,
            "points": result, "source": "2BA9290",
        })
        return result

    def component_sum(
        self, context: NativeModifierContext12003 | None, skill: int,
        mode: int, categories: tuple[int | None, ...], factor: int | None,
    ) -> int | None:
        terms = [self.component(context, skill, 1, mode)]
        for category, key_base in zip(categories, (20, 26, 32, 38)):
            terms.append(self.component(context, key_base + skill, category, mode))
        terms.append(self.component(context, 48 + skill, factor, mode))
        if skill == 5:
            terms.append(self.component(context, 6, 1, mode))
        total = 0
        for term in terms:
            if term is None:
                return None
            total = native_wrap32_12003(total + term)
        return total


def _category_count(
    calc: _Calculation, operand: CategoryOperands12003 | None, index: int,
) -> int | None:
    path = "category_operands[" + str(index) + "]"
    if operand is None:
        calc.gap(path)
        return None
    count = calc.i32(operand.threshold_count, path + ".threshold_count")
    if count is None:
        return None
    if count <= 0:
        return 0
    metric = calc.i64(operand.metric_raw, path + ".metric_raw")
    override = calc.i32(operand.override_raw, path + ".override_raw")
    if metric is None or override is None:
        return None
    prefix = 0
    for offset in range(count):
        threshold = calc.i64(calc.item(
            operand.thresholds_raw, offset,
            path + ".thresholds_raw[" + str(offset) + "]"),
            path + ".thresholds_raw[" + str(offset) + "]")
        if threshold is None:
            return None
        if metric < threshold:
            break
        prefix = native_wrap32_12003(prefix + 1)
    return prefix if override < 0 else min(prefix, override)


def _raw_skill(
    calc: _Calculation, inputs: NativeSkillCacheInputs12003, skill: int,
    categories: tuple[int | None, ...], factor: int | None,
) -> tuple[int | None, Mapping[str, object]]:
    base = calc.i32(calc.item(
        inputs.base_points, skill, "base_points[" + str(skill) + "]"),
        "base_points[" + str(skill) + "]")
    context = inputs.context
    absolute_q64 = calc.context_value(context, 13 + skill, 0)
    absolute_points = (
        native_wrap32_12003(_trunc_q(absolute_q64))
        if absolute_q64 is not None else None)
    mode = None
    modifier = None
    negative_tail = None
    if absolute_points is not None:
        if absolute_points <= 0:
            mode = "aggregate"
            modifier = calc.component_sum(context, skill, 0, categories, factor)
        else:
            mode = "positive_plus_negative_tail"
            positive = calc.component_sum(context, skill, 1, categories, factor)
            negative = calc.component_sum(context, skill, 2, categories, factor)
            if negative is not None:
                negative_tail = min(
                    native_wrap32_12003(negative + absolute_points), 0)
            if positive is not None and negative_tail is not None:
                modifier = native_wrap32_12003(positive + negative_tail)
    combined = (native_wrap32_12003(base + modifier)
                if base is not None and modifier is not None else None)
    percent_q64 = calc.context_value(context, 7 + skill, 0)
    fixed_branch = None
    scaled_q64 = None
    if percent_q64 is None:
        points = None
    elif percent_q64 == 0:
        points = combined
        fixed_branch = "percent_zero"
    elif percent_q64 <= -Q_12003:
        points = 0
        fixed_branch = "percent_at_or_below_minus_Q"
    elif combined is None:
        points = None
    else:
        scaled_q64, fixed_branch = _fixed_mul_q(
            native_wrap64_12003(combined * Q_12003),
            native_wrap64_12003(percent_q64 + Q_12003))
        points = native_wrap32_12003(_trunc_q(scaled_q64))
    return points, {
        "skill": SKILL_NAMES_12003[skill], "index": skill,
        "base_points": base, "absolute_q64": absolute_q64,
        "absolute_points_low32": absolute_points, "component_choice": mode,
        "negative_tail_points": negative_tail, "component_points": modifier,
        "base_plus_component_low32": combined, "percent_q64": percent_q64,
        "percent_fixed_multiply_branch": fixed_branch,
        "scaled_points_q64": scaled_q64, "raw_points": points,
    }


def _tuple_value(value: object) -> tuple[object, ...] | None:
    return tuple(value) if isinstance(value, (tuple, list)) else None


def _mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _container_from_mapping(value: object) -> PropertyContainer12003 | None:
    mapping = _mapping(value)
    if mapping is None:
        return None
    return PropertyContainer12003(
        keys_u16=_tuple_value(mapping.get("keys_u16")),
        values_q64=_tuple_value(mapping.get("values_q64")),
        count=mapping.get("count"),
    )


def from_raw_numeric_inputs_12003(
    payload: Mapping[str, object] | None, *,
    source_provenance: Mapping[str, object] | None = None,
) -> NativeSkillCacheInputs12003:
    """Consume C's normalized raw_numeric_inputs leaf without an adapter.

    A carrier absence/null is retained in provenance. Its status flags describe
    observation; actual missing operands determine the bounded calculation.
    Source metadata is diagnostic and does not introduce a frame gate.
    """
    mapping = _mapping(payload)
    raw = mapping if mapping is not None else {}
    context_raw = _mapping(raw.get("context"))
    context = None
    if context_raw is not None:
        rows_raw = _tuple_value(context_raw.get("weighted_rows"))
        rows = None
        if rows_raw is not None:
            rows = tuple(
                WeightedModifierRow12003(
                    properties=_container_from_mapping(row.get("properties")),
                    weight_q64=row.get("weight_q64"),
                    native_index=row.get("native_index"),
                ) if isinstance(row, Mapping) else None
                for row in rows_raw
            )
        context = NativeModifierContext12003(
            aggregate_properties=_container_from_mapping(
                context_raw.get("aggregate_properties")),
            weighted_rows=rows,
            weighted_count=context_raw.get("weighted_count"),
        )
    operands_raw = _tuple_value(raw.get("category_operands"))
    operands = None
    if operands_raw is not None:
        operands = tuple(
            CategoryOperands12003(
                metric_raw=operand.get("metric_raw"),
                override_raw=operand.get("override_raw"),
                thresholds_raw=_tuple_value(operand.get("thresholds_raw")),
                threshold_count=operand.get("threshold_count"),
            ) if isinstance(operand, Mapping) else None
            for operand in operands_raw
        )
    provenance = {
        "carrier_presence": "value" if mapping is not None else "null_or_absent",
        "character_id": raw.get("character_id"),
        "status": raw.get("status"),
        "raw_numeric_inputs_ready": raw.get("raw_numeric_inputs_ready"),
        "context_source": raw.get("context_source"),
        "unavailable_reason": raw.get("unavailable_reason"),
        "external_source": deepcopy(source_provenance),
    }
    return NativeSkillCacheInputs12003(
        base_points=_tuple_value(raw.get("base_points")),
        context=context,
        scratch_present=raw.get("scratch_present"),
        category_counts=_tuple_value(raw.get("category_counts")),
        category_operands=operands,
        scratch_factor_numerator=raw.get("scratch_factor_numerator"),
        scratch_factor_denominator=raw.get("scratch_factor_denominator"),
        caps=_tuple_value(raw.get("caps")),
        prowess_adjustment=raw.get("prowess_adjustment"),
        character_id=raw.get("character_id"),
        source_provenance=provenance,
    )


def compute_six_skill_cache_from_native_inputs_12003(
    inputs: NativeSkillCacheInputs12003 | Mapping[str, object] | None,
) -> NativeSkillCacheResult12003:
    """Compute conditional six-skill results from actual native operands.

    Unknown operands remain partial. Legal property-key absence is native zero.
    Null scratch is the source D80 no-op and produces no new cache values.
    """
    if not isinstance(inputs, NativeSkillCacheInputs12003):
        inputs = from_raw_numeric_inputs_12003(inputs)
    calc = _Calculation()
    empty = (None,) * 6
    ledger: dict[str, object] = {
        "source_exe_sha256": SOURCE_EXE_SHA256_12003,
        "source_scope": "actual_native_input_numeric_primitive",
        "input_source": deepcopy(inputs.source_provenance),
        "character_id": inputs.character_id,
        "scratch_present": inputs.scratch_present,
        "units": {"points": "signed32_integer", "properties": "signed64_Q100000"},
        "native_cache_path": "28C3D80",
        "native_write_performed": False,
        "trait_context_constructed": False,
        "full_native_callbacks": False,
        "future_context_requirement": "explicit actual refreshed operands",
        "Entry_refresh_timing_closed": False,
        "actual_game_days_advanced": 0,
    }
    if inputs.scratch_present is False:
        ledger["native_cache_branch"] = "null_scratch_noop"
        ledger["recompute_performed"] = False
        return NativeSkillCacheResult12003(
            inputs.character_id, empty, empty, empty, (), True, "source_noop", ledger)
    if inputs.scratch_present is not True:
        calc.gap("scratch_present")
        ledger["native_cache_branch"] = "scratch_presence_unknown"
        ledger["recompute_performed"] = False
        return NativeSkillCacheResult12003(
            inputs.character_id, empty, empty, empty,
            tuple(calc.missing), False, "partial", ledger)

    category_values: list[int | None] = []
    for index in range(4):
        supplied = (inputs.category_counts[index]
                    if inputs.category_counts is not None
                    and index < len(inputs.category_counts) else None)
        if type(supplied) is int:
            value = native_wrap32_12003(supplied)
        else:
            operand = (inputs.category_operands[index]
                       if inputs.category_operands is not None
                       and index < len(inputs.category_operands) else None)
            value = _category_count(calc, operand, index)
            if operand is None:
                calc.gap("category_counts[" + str(index) + "]")
        category_values.append(value)
    categories = tuple(category_values)
    numerator = calc.i32(
        inputs.scratch_factor_numerator, "scratch_factor_numerator")
    denominator = calc.i32(
        inputs.scratch_factor_denominator, "scratch_factor_denominator")
    factor = None
    factor_branch = None
    if denominator == 0:
        factor, factor_branch = _scratch_factor(0, 0)
    elif numerator is not None and denominator is not None:
        factor, factor_branch = _scratch_factor(numerator, denominator)
    ledger["category_counts"] = categories
    ledger["scratch_factor"] = {
        "numerator": numerator, "denominator": denominator,
        "multiplier": factor, "branch": factor_branch, "denominator_rva": "5C68CE8",
    }
    raw_points: list[int | None] = []
    first_points: list[int | None] = []
    skill_ledger: list[Mapping[str, object]] = []
    for skill in range(6):
        raw, details = _raw_skill(calc, inputs, skill, categories, factor)
        raw_points.append(raw)
        cap = calc.i32(calc.item(
            inputs.caps, skill, "caps[" + str(skill) + "]"),
            "caps[" + str(skill) + "]")
        if raw is None:
            clipped = None
        elif raw < 0:
            clipped = 0
        else:
            clipped = min(raw, cap) if cap is not None else None
        first_points.append(clipped)
        skill_ledger.append({
            **details, "cap_rva": CAP_RVAS_12003[skill],
            "loaded_cap": cap, "first_clipped_points": clipped,
            "clip_branch": ("negative_raw_zero" if raw is not None and raw < 0
                            else "signed_min_cap" if raw is not None else "partial"),
        })
    final_points = list(first_points)
    adjustment = calc.i32(inputs.prowess_adjustment, "prowess_adjustment")
    prowess_sum = None
    second_cap = None
    if adjustment is None:
        final_points[5] = None
        prowess_branch = "partial_adjustment"
    elif adjustment == 0:
        prowess_branch = "zero_adjustment_skip"
    elif first_points[5] is None:
        final_points[5] = None
        prowess_branch = "partial_first_clamp"
    else:
        prowess_sum = native_wrap32_12003(first_points[5] + adjustment)
        if prowess_sum < 0:
            final_points[5] = 0
            prowess_branch = "negative_sum_zero"
        else:
            second_cap = calc.i32(calc.item(
                inputs.caps, 5, "caps[5]"), "caps[5]")
            final_points[5] = (
                min(prowess_sum, second_cap) if second_cap is not None else None)
            prowess_branch = "second_signed_min_cap"
    ledger.update({
        "native_cache_branch": "nonnull_scratch_conditional_recompute",
        "recompute_performed": True,
        "skill_math": tuple(skill_ledger),
        "property_lookups": tuple(calc.lookups),
        "weighted_terms": tuple(calc.weighted_terms),
        "components": tuple(calc.components),
        "prowess_second_clamp": {
            "adjustment_points": adjustment, "first_clipped_points": first_points[5],
            "wrapped_sum": prowess_sum, "loaded_cap": second_cap,
            "branch": prowess_branch, "final_points": final_points[5],
        },
        "conditional_writeback": {
            "fields": ("D8", "DC", "E0", "E4", "E8", "EC"),
            "source": "reusedF60 scratch408/418 copies; includes424→CharacterEC",
            "executed": False, "ready440_and_outer_caller_not_replayed": True,
        },
    })
    ready = not calc.missing and all(value is not None for value in final_points)
    return NativeSkillCacheResult12003(
        inputs.character_id, tuple(raw_points), tuple(first_points),
        tuple(final_points), tuple(calc.missing), ready,
        "computed" if ready else "partial", ledger)

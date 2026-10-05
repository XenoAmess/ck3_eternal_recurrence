"""Adapt explicit evaluated context contributions to the exact .3 skill kernel.

291B4F0 retains each emitted modifier and calls2438850 with weight100000.
The caller supplies the genuine prefix before the branch and the explicit
post-branch aggregate. This module does not implement generic new-key storage,
evaluate ScriptContext, or append to an already complete current context.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, Sequence

from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003,
    NativeSkillCacheInputs12003,
    NativeSkillCacheResult12003,
    PropertyContainer12003,
    WeightedModifierRow12003,
    compute_six_skill_cache_from_native_inputs_12003,
)


CONTEXT_WEIGHT_Q_12003 = 100000


@dataclass(frozen=True, slots=True)
class EvaluatedContextModifier12003:
    """An already evaluated/scaled emitted modifier; native gates are upstream."""

    properties: PropertyContainer12003 | None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class EvaluatedContextRowsProjection12003:
    context: NativeModifierContext12003
    contribution_ledger: tuple[Mapping[str, object], ...]
    missing_inputs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EvaluatedContextSkillResult12003:
    projection: EvaluatedContextRowsProjection12003
    skill_result: NativeSkillCacheResult12003
    native_context_write_performed: bool = False
    native_script_evaluation_performed: bool = False
    native_future_observation_performed: bool = False


def append_evaluated_context_rows_12003(
    prefix_before_branch: NativeModifierContext12003 | None,
    emitted_modifiers: Sequence[EvaluatedContextModifier12003] | None,
    *,
    aggregate_properties_after: PropertyContainer12003 | None,
) -> EvaluatedContextRowsProjection12003:
    """Append Q1 rows in supplied native order using an explicit aggregate.

    Unknown nonempty prefix/rows stay partial. A complete empty emitted vector
    is the native no-contribution case and retains the prefix exactly. The
    aggregate argument is a caller-supplied operand, not computed by this leaf.
    """
    gaps: list[str] = []
    if prefix_before_branch is None:
        gaps.append("prefix_before_branch")
    prefix = prefix_before_branch or NativeModifierContext12003()
    if emitted_modifiers is None:
        gaps.append("emitted_modifiers")
        return EvaluatedContextRowsProjection12003(
            NativeModifierContext12003(aggregate_properties_after, None, None),
            (), tuple(gaps),
        )
    if not emitted_modifiers:
        return EvaluatedContextRowsProjection12003(prefix, (), tuple(gaps))

    prefix_count = prefix.weighted_count
    if prefix_count is None:
        gaps.append("prefix_before_branch.weighted_count")
    if prefix.weighted_rows is not None:
        prior_rows = prefix.weighted_rows
    elif prefix_count == 0:
        prior_rows = ()
    else:
        prior_rows = None
        gaps.append("prefix_before_branch.weighted_rows")

    rows: list[WeightedModifierRow12003] = []
    ledger: list[Mapping[str, object]] = []
    for index, modifier in enumerate(emitted_modifiers):
        if modifier.properties is not None and modifier.properties.count == 0:
            continue
        appended_index = len(rows)
        native_index = prefix_count + appended_index if prefix_count is not None else None
        rows.append(WeightedModifierRow12003(
            modifier.properties, CONTEXT_WEIGHT_Q_12003, native_index,
        ))
        if modifier.properties is None:
            gaps.append("emitted_modifiers[" + str(index) + "].properties")
        ledger.append({
            "emitted_native_index": appended_index,
            "context_native_index": native_index,
            "context_weight_raw": CONTEXT_WEIGHT_Q_12003,
            "source_provenance": modifier.source_provenance,
            "property_stage": "already_evaluated_and_scaled",
            "aggregate_source": "caller_supplied_explicit_postbranch_operand",
        })
    if not rows:
        return EvaluatedContextRowsProjection12003(prefix, (), tuple(gaps))
    if aggregate_properties_after is None:
        gaps.append("aggregate_properties_after")
    context = NativeModifierContext12003(
        aggregate_properties_after,
        prior_rows + tuple(rows) if prior_rows is not None else None,
        prefix_count + len(rows) if prefix_count is not None else None,
    )
    return EvaluatedContextRowsProjection12003(context, tuple(ledger), tuple(gaps))


def compute_evaluated_context_skills_12003(
    inputs_before_branch: NativeSkillCacheInputs12003,
    emitted_modifiers: Sequence[EvaluatedContextModifier12003] | None,
    *,
    aggregate_properties_after: PropertyContainer12003 | None,
) -> EvaluatedContextSkillResult12003:
    """Use the adopted six-skill kernel once with the explicit context projection.

    A/B native role and freeze gates select the emitted modifiers upstream.
    All base/category/factor/cap/F0 inputs retain their supplied provenance.
    Missing operands use the kernel's existing partial result behavior.
    """
    projection = append_evaluated_context_rows_12003(
        inputs_before_branch.context,
        emitted_modifiers,
        aggregate_properties_after=aggregate_properties_after,
    )
    result = compute_six_skill_cache_from_native_inputs_12003(
        replace(inputs_before_branch, context=projection.context),
    )
    return EvaluatedContextSkillResult12003(projection, result)

"""Ordered logical person context through291F940 from an explicit stage prior.

See battle-person-stage-chain-12003.md. Unknown stages stop the coherent fold;
later independently observed requests remain exposed. No game access occurs.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from importlib import import_module
from typing import Mapping

from ..bridge.battle_context_source_inputs_contract import (
    emit_291e210_requests_from_current_source_inputs_12003,
    emit_post_291d7e0_requests_from_current_source_inputs_12003,
    emit_pre_291e210_1640_requests_from_current_source_inputs_12003,
)
from ..bridge.battle_person_helper_291f0a0_contract import (
    FAMILIES_291F0A0,
    emit_helper_291f0a0_family_requests_from_current_source_inputs_12003,
)
from ..bridge.battle_person_later_direct_contract import (
    emit_later_direct_requests_from_current_source_inputs_12003,
)
from ..bridge.battle_person_remaining_helpers_contract import (
    FAMILIES_291F550,
    emit_helper_291f550_family_requests_from_current_source_inputs_12003,
    emit_helper_291f940_requests_from_current_source_inputs_12003,
)
from ..bridge.battle_task_position_context_contract import parse_task_position_branch_inputs_12003
from .battle_context_preparation_branch_291d7e0_12003 import compose_291d7e0_current_contributions_12003
from .battle_context_preparation_branch_291e210_12003 import NativeWeightedContributionRequest12003
from .battle_trait_materialized_prefix_12003 import (
    PersonStageContextAssemblyResult12003, _block_arrays, _fold_property_request,
)
from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, NativeSkillCacheInputs12003, NativeSkillCacheResult12003,
    PropertyContainer12003, WeightedModifierRow12003, SOURCE_EXE_SHA256_12003,
    compute_six_skill_cache_from_native_inputs_12003, from_raw_numeric_inputs_12003,
    native_wrap64_12003,
)

START_STAGE_12003 = "post291D1D0_pre291C209"
STOP_STAGE_12003 = "post291F940_pre291C467"


@dataclass(frozen=True, slots=True)
class PersonStageChainStart12003:
    character_full_id: int | None
    context: NativeModifierContext12003 | Mapping | None
    stage: str = START_STAGE_12003
    source_provenance: Mapping | None = None


@dataclass(frozen=True, slots=True)
class PersonStageChainResult12003:
    character_full_id: int | None
    stage: str
    context: NativeModifierContext12003 | None
    ready: bool
    missing_inputs: tuple[str, ...]
    source_ledger: Mapping
    stage_contexts: Mapping[str, NativeModifierContext12003]
    independent_stage_outputs: Mapping[str, tuple[NativeWeightedContributionRequest12003, ...]]
    full_person_preparation_ready: bool = False
    full_entry_ready: bool = False
    native_write_performed: bool = False


def stage_chain_start_from_prefix_12003(result: PersonStageContextAssemblyResult12003) -> PersonStageChainStart12003:
    """Explicitly hand over the adopted prefix result; partial stays unknown."""
    return PersonStageChainStart12003(
        result.character_full_id, result.post291D1D0_context if result.ready else None,
        source_provenance={"input": "explicit_person_prefix_result", "prefix_ledger": result.ledger})


def _property_input(block: object) -> PropertyContainer12003 | None:
    if isinstance(block, PropertyContainer12003):
        return block
    if not isinstance(block, Mapping):
        return None
    count = block.get("keys_count", block.get("count"))
    keys, values = block.get("keys_u16"), block.get("values_q64")
    return PropertyContainer12003(None if keys is None else tuple(keys),
                                 None if values is None else tuple(values), count)


def _trait_requests(section: Mapping | None) -> tuple:
    # Same-query native owner supplies this source-closed observer. Import is
    # deferred so a missing new capability preserves the useful earlier fold.
    module = import_module("xar_autoplayer.bridge.battle_person_trait_stage_291d460_contract")
    return module.emit_trait_291d460_requests_from_current_source_inputs_12003(section)


def _task_requests(section: Mapping | None, branch: str) -> tuple:
    inputs = parse_task_position_branch_inputs_12003(section, branch=branch)
    if not inputs.branch_vectors_ready or inputs.emitted_modifiers is None:
        raise ValueError("Required native input unavailable: " + branch + ".evaluated_rows")
    return tuple(NativeWeightedContributionRequest12003(
        i, branch, i, 1, branch + ":" + str(i), row.properties, 100000)
        for i, row in enumerate(inputs.emitted_modifiers))


def assemble_person_stage_chain_12003(
    *, start_baseline: PersonStageChainStart12003,
    source_inputs: Mapping | None, task_position_inputs: Mapping | None,
) -> PersonStageChainResult12003:
    """Consume normalized same-person sections and preserve a contiguous prior.

    An available evaluated task vector is sufficient even if the older causal
    observer lacks its historical before/after aggregate. Its declaration scale
    was already applied by native evaluation and must not be applied again.
    """
    missing: list[str] = []
    actor = start_baseline.character_full_id
    if type(actor) is not int:
        missing.append("start_baseline.character_full_id")
    if start_baseline.stage != START_STAGE_12003:
        missing.append("start_baseline.stage_post291D1D0_pre291C209")
    initial = start_baseline.context
    if isinstance(initial, Mapping):
        initial = from_raw_numeric_inputs_12003({"context": initial}).context
    keys: list[int] = []
    values: list[int] = []
    weighted: list[WeightedModifierRow12003] = []
    if not isinstance(initial, NativeModifierContext12003):
        missing.append("start_baseline.context")
    else:
        arrays = None if initial.aggregate_properties is None else _block_arrays(
            initial.aggregate_properties, "start_baseline.aggregate_properties", missing)
        if initial.aggregate_properties is None:
            missing.append("start_baseline.aggregate_properties")
        count, rows = initial.weighted_count, initial.weighted_rows
        if type(count) is int and count == 0:
            pass  # Native zero count consumes no prior row array.
        elif type(count) is not int or count < 0 or rows is None or len(rows) < count:
            missing.append("start_baseline.weighted_rows")
        else:
            for i, row in enumerate(rows[:count]):
                if row is None or type(row.weight_q64) is not int or row.properties is None:
                    missing.append(f"start_baseline.weighted_rows[{i}]")
                elif _block_arrays(row.properties, f"start_baseline.weighted_rows[{i}]", missing) is not None:
                    weighted.append(row)
        if arrays is not None:
            keys, values = list(arrays[0]), list(arrays[1])

    baseline_ready = not missing
    identities = {}
    for name, section in (("source_inputs", source_inputs), ("task_position_inputs", task_position_inputs)):
        identities[name] = section is not None and section.get("character_id") == actor
        if section is not None and not identities[name]:
            missing.append(name + ".character_id_matches_baseline")

    emitters = [
        ("preA1640", "postPreA1640_pre291C282", emit_pre_291e210_1640_requests_from_current_source_inputs_12003),
        ("291E210", "post291E210_pre291C28D", emit_291e210_requests_from_current_source_inputs_12003),
        ("291D460", "post291D460_pre291C298", _trait_requests),
        ("291D7E0", "post291D7E0_pre291C2A3", None),
        ("291DED0", "post291DED0_pre291C2AE", "owned_passive"),
        ("291DCE0", "post291DCE0_pre291C2B3", "councillor_position_task"),
        ("postB_sources", "postOrderedD8_pre291C377", emit_post_291d7e0_requests_from_current_source_inputs_12003),
    ]
    emitters.extend(("291F0A0." + family, "post291F0A0_" + family,
                     lambda section, family=family: emit_helper_291f0a0_family_requests_from_current_source_inputs_12003(section, family))
                    for family in FAMILIES_291F0A0)
    emitters.append(("later_direct", "postAA0_pre291C457", emit_later_direct_requests_from_current_source_inputs_12003))
    emitters.extend(("291F550." + family, "post291F550_" + family,
                     lambda section, family=family: emit_helper_291f550_family_requests_from_current_source_inputs_12003(section, family))
                    for family in FAMILIES_291F550)
    emitters.append(("291F940", STOP_STAGE_12003, emit_helper_291f940_requests_from_current_source_inputs_12003))

    def snapshot():
        return NativeModifierContext12003(PropertyContainer12003(tuple(keys), tuple(values), len(keys)),
                                         tuple(weighted), len(weighted))

    contiguous = baseline_ready
    stage = START_STAGE_12003
    contexts = {stage: snapshot()} if baseline_ready else {}
    outputs, stages, updates = {}, [], []
    for name, after_stage, emit in emitters:
        is_task = isinstance(emit, str)
        section_name = "task_position_inputs" if is_task else "source_inputs"
        section = task_position_inputs if is_task else source_inputs
        ready, requests, gaps, detail = True, (), [], None
        try:
            if not identities[section_name]:
                raise ValueError("Required native input unavailable: " + section_name + ".matching_character")
            if name == "291D7E0":
                result = compose_291d7e0_current_contributions_12003(section)
                ready, gaps, detail = result.ready, list(result.missing_inputs), result.source_results
                requests = tuple(NativeWeightedContributionRequest12003(
                    item.native_source_index, "291D7E0", item.native_source_index, 1,
                    item.source_identity, item.properties, item.weight_q64) for item in result.contributions)
            elif is_task:
                requests = _task_requests(section, emit)
            else:
                requests = emit(section)
        except (ValueError, ModuleNotFoundError) as error:
            ready, gaps = False, [str(error)]

        validated = []
        for i, request in enumerate(requests):
            local = []
            pc = _property_input(request.base_property_block)
            arrays = None if pc is None else _block_arrays(pc, f"{name}.request[{i}]", local)
            if pc is None:
                local.append(f"{name}.request[{i}].properties")
            if type(request.weight_q64) is not int:
                local.append(f"{name}.request[{i}].weight_q64")
            if local:
                ready = False
                gaps.extend(local)
                break
            validated.append((request, pc, arrays))
        outputs[name] = tuple(item[0] for item in validated)
        applied = []
        if contiguous:
            for request, pc, arrays in validated:
                if not arrays[0]:
                    applied.append("source_count_zero_skip")
                    continue
                weight = native_wrap64_12003(request.weight_q64)
                weighted.append(WeightedModifierRow12003(pc, weight, len(weighted)))
                applied.append(_fold_property_request(keys, values, arrays[0], arrays[1], weight,
                    {"stage": name, "definition_identity": request.definition_identity,
                     "source_ordinal": request.source_ordinal, "first_row_index": request.first_row_index}, updates))
            if ready:
                stage = after_stage
            elif validated:
                stage = "verified_partial_" + name
            contexts[stage] = snapshot()
        for gap in gaps:
            path = name + ":" + gap
            if path not in missing:
                missing.append(path)
        stages.append({"stage": name, "after_stage": after_stage, "requests_ready": ready,
                       "request_count": len(validated), "folded_into_contiguous_context": contiguous,
                       "merge_branches": tuple(applied), "missing_inputs": tuple(gaps), "detail": detail})
        contiguous = contiguous and ready

    ledger = {"source_exe_sha256": SOURCE_EXE_SHA256_12003,
              "start_stage": START_STAGE_12003, "bounded_stop_stage": STOP_STAGE_12003,
              "explicit_baseline_provenance": deepcopy(start_baseline.source_provenance),
              "ordered_stages": tuple(stages), "aggregate_updates": tuple(updates),
              "task_properties_are_already_evaluated_scaled": True,
              "task_declaration_scale_reapplied": False,
              "current_final_context_used_as_default": False,
              "later_unknown_stages_assumed_empty": False,
              "remaining_caller_frontier": "291C467", "full_person_preparation_ready": False,
              "full_entry_ready": False, "game_operations": 0}
    return PersonStageChainResult12003(actor, stage, contexts.get(stage), contiguous and not missing,
                                      tuple(missing), ledger, contexts, outputs)


def assemble_current_person_stage_chain_12003(
    person_state: Mapping, *, start_baseline: PersonStageChainStart12003,
    character_full_id: int,
) -> PersonStageChainResult12003:
    """Reach the assembler from the existing normalized query person result."""
    if character_full_id != start_baseline.character_full_id:
        raise ValueError("current person and explicit stage baseline characters disagree")
    return assemble_person_stage_chain_12003(start_baseline=start_baseline,
        source_inputs=person_state.get("current_context_source_inputs"),
        task_position_inputs=person_state.get("current_context_task_position_inputs"))


def project_stage_chain_six_skills_12003(
    result: PersonStageChainResult12003, numeric_inputs: NativeSkillCacheInputs12003,
) -> NativeSkillCacheResult12003:
    """Conditional skill projection at the explicitly returned frontier stage."""
    if numeric_inputs.character_id != result.character_full_id:
        raise ValueError("six-skill operands and assembled stage characters disagree")
    projected = compute_six_skill_cache_from_native_inputs_12003(replace(numeric_inputs, context=result.context))
    return replace(projected, ledger={**projected.ledger, "assembled_context_stage": result.stage,
        "bounded_chain_ready": result.ready, "full_person_preparation_ready": False,
        "full_entry_ready": False, "conditional_stage_projection": True})

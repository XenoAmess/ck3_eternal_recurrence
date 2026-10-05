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


def _tail_emit(section: Mapping | None, module_name: str, function: str, family: str | int | tuple | None = None):
    module = import_module("xar_autoplayer.bridge." + module_name)
    emit = getattr(module, function)
    if isinstance(family, tuple):
        return emit(section, *family)
    return emit(section) if family is None else emit(section, family)


def _provider192_prefix(section: Mapping, module: str, outputs: dict):
    """Retain each source slot while folding only the verified ordered prefix."""
    name = "provider192_and2920850"
    api = "emit_provider192_and2920850_"
    suffix = "_requests_from_current_source_inputs_12003"
    families = ("provider_192", "list_168", "list_180")
    frontiers = ("postProviderCharacter192_pre2920850", "post2920850_list168_preList180",
                 "postProviderCharacter192_and2920850_pre291CB70")
    leaf = section.get(name)
    prefix, ledger, missing, frontier, contiguous = (), [], [], None, True

    def emit(kind, indices):
        try:
            return tuple(_tail_emit(section, module, api + kind + suffix, indices)), ()
        except (ValueError, ModuleNotFoundError, AttributeError) as error:
            return (), (str(error),)

    for family, after in zip(families, frontiers):
        requests, gaps = emit("family", family)
        parts = []
        family_prefix, family_frontier = (), None
        family_contiguous = True
        if gaps and family != "provider_192":
            branch = leaf.get(family) if isinstance(leaf, Mapping) else None
            rows = branch.get("rows") if isinstance(branch, Mapping) else None
            count = branch.get("numeric_count") if isinstance(branch, Mapping) else None
            family_contiguous = (type(count) is int and count >= 0 and isinstance(rows, list)
                and branch.get("header_selection") is not None
                and (count == 0 or branch.get("array_present") is True))
            for occurrence in rows or ():
                occurrence_index = occurrence["native_index"]
                for slot in range(8):
                    label = f"{family}.occurrence{occurrence_index}.slot{slot}"
                    slot_requests, slot_gaps = emit("slot", (family, occurrence_index, slot))
                    outputs[name + "." + label] = slot_requests
                    if not slot_gaps:
                        if family_contiguous:
                            family_prefix += slot_requests
                            family_frontier = f"post2920850_{label.replace('.', '_')}_preSlot{slot + 1}"
                    elif slot >= 4:
                        nested_rows = occurrence.get("nested_rows")
                        header = None if nested_rows is None else nested_rows[slot - 4]["mapped_family"]
                        descriptors = header.get("rows") if isinstance(header, Mapping) else None
                        descriptor_count = header.get("count") if isinstance(header, Mapping) else None
                        descriptor_contiguous = (family_contiguous and type(descriptor_count) is int
                            and descriptor_count >= 0 and isinstance(descriptors, list)
                            and header.get("admitted") is True
                            and (descriptor_count == 0 or header.get("array_present") is True))
                        for descriptor in descriptors or ():
                            descriptor_index = descriptor["native_index"]
                            descriptor_label = f"{family}.occurrence{occurrence_index}.nested{slot - 4}.descriptor{descriptor_index}"
                            descriptor_requests, descriptor_gaps = emit("descriptor",
                                (family, occurrence_index, slot - 4, descriptor_index))
                            outputs[name + "." + descriptor_label] = descriptor_requests
                            descriptor_contiguous = descriptor_contiguous and not descriptor_gaps
                            if descriptor_contiguous:
                                family_prefix += descriptor_requests
                                family_frontier = f"post2920850_{descriptor_label.replace('.', '_')}_preDescriptor{descriptor_index + 1}"
                            parts.append({"part": descriptor_label, "requests_ready": not descriptor_gaps,
                                "request_count": len(descriptor_requests),
                                "in_contiguous_family_prefix": descriptor_contiguous,
                                "missing_inputs": descriptor_gaps})
                    parts.append({"part": label, "requests_ready": not slot_gaps,
                        "request_count": len(slot_requests),
                        "in_contiguous_family_prefix": family_contiguous and not slot_gaps,
                        "missing_inputs": slot_gaps})
                    family_contiguous = family_contiguous and not slot_gaps
            requests = family_prefix
        outputs[name + "." + family] = requests
        if contiguous:
            prefix += requests
            frontier = after if not gaps else (family_frontier or frontier)
        ledger.append({"family": family, "requests_ready": not gaps,
            "request_count": len(requests), "in_contiguous_family_prefix": contiguous and not gaps,
            "verified_parts": tuple(parts), "missing_inputs": gaps})
        missing.extend(family + ":" + gap for gap in gaps)
        contiguous = contiguous and not gaps
    return prefix, ledger, missing, frontier


def continue_person_stage_chain_tail_12003(
    previous: PersonStageChainResult12003, source_inputs: Mapping | None, *,
    through_stage: str = "2753860",
) -> PersonStageChainResult12003:
    """Extend a requested contiguous bound and expose later sparse inputs.

    Default completes the independently useful actual275 stage. Requesting
    later stages requires every intervening source/observer; they are not
    synthetic empty contributions. A prior partial chain cannot jump to tail.
    """
    prefix_module = "battle_person_tail_prefix_contract"
    conference_module = "battle_person_conference_24b1d00_contract"
    middle_module = "battle_person_middle_helpers_contract"
    direct_module = "battle_person_tail_direct_contract"
    provider_module = "battle_person_provider_bucket_contract"
    qualifier_module = "battle_person_qualifier_28bc0d0_contract"
    list_module = "battle_person_list_predicate_2530dd0_contract"
    gated_module = "battle_person_gated_temporary_tail_contract"
    after_gated_module = "battle_person_after_gated_tail_contract"
    provider192_module = "battle_person_provider192_and2920850_contract"
    stages = (
        ("2753860", "post2753860_pre291C4D2", prefix_module,
         "emit_helper_2753860_requests_from_current_source_inputs_12003", None),
        ("2922070", "post2922070_pre291C4DD", prefix_module,
         "emit_helper_2922070_requests_from_current_source_inputs_12003", None),
        ("2922530", "post2922530_pre291C4E2", prefix_module,
         "emit_helper_2922530_requests_from_current_source_inputs_12003", None),
        ("conference24B1D00", "post24B1D00_pre291C553", conference_module,
         "emit_conference_24b1d00_requests_from_current_source_inputs_12003", None),
        ("291F260", "post291F260_pre291C558", middle_module,
         "emit_helper_291f260_requests_from_current_source_inputs_12003", None),
        ("signed2F8_provider_bucket", "postProvider2F8_pre291C5B7", provider_module,
         "emit_provider_bucket_requests_from_current_source_inputs_12003", None),
        ("government_870_a30", "postGovernmentA30_pre291C620", direct_module,
         "emit_tail_direct_family_requests_from_current_source_inputs_12003", "government_870_a30"),
        ("qualifier_repeated_contribution", "postQualifierContribution_pre291C6CF", qualifier_module,
         "emit_qualifier_28bc0d0_requests_from_current_source_inputs_12003", None),
        ("291FB10", "post291FB10_pre291C6D4", middle_module,
         "emit_helper_291fb10_requests_from_current_source_inputs_12003", None),
        ("list2530DD0", "postList2530DD0_pre291C7A7", list_module,
         "emit_list_predicate_2530dd0_requests_from_current_source_inputs_12003", None),
        ("gated_temporary_tail", "postGatedTemporaryAndList_pre291C9D8", gated_module,
         "emit_gated_temporary_tail_requests_from_current_source_inputs_12003", None),
        ("after_gated_tail", "post326A8E0_and2920310_pre291CB14", after_gated_module,
         "emit_after_gated_tail_requests_from_current_source_inputs_12003", None),
        ("provider192_and2920850", "postProviderCharacter192_and2920850_pre291CB70", provider192_module,
         "emit_provider192_and2920850_requests_from_current_source_inputs_12003", None),
        ("carrier_weighted630", "postCarrierWeighted630_pre291CC71", direct_module,
         "emit_tail_direct_family_requests_from_current_source_inputs_12003", "carrier_weighted630"),
        ("remaining_later_preparation", "remaining_caller_unclosed", None, None, None),
    )
    names = tuple(item[0] for item in stages)
    if through_stage not in names:
        raise ValueError("Unknown requested person tail bound: " + through_stage)
    bound_index = names.index(through_stage)
    gaps = list(previous.missing_inputs)
    keys, values, weighted = [], [], []
    context = previous.context
    context_valid = isinstance(context, NativeModifierContext12003)
    local = []
    if context_valid:
        arrays = None if context.aggregate_properties is None else _block_arrays(
            context.aggregate_properties, "previous.context.aggregate_properties", local)
        if arrays is None:
            context_valid = False
        else:
            keys, values = list(arrays[0]), list(arrays[1])
        count, rows = context.weighted_count, context.weighted_rows
        if type(count) is int and count == 0:
            pass
        elif type(count) is not int or count < 0 or rows is None or len(rows) < count:
            context_valid = False
            local.append("previous.context.weighted_rows")
        else:
            weighted = list(rows[:count])
    if not context_valid:
        local.append("previous.context")
    if not previous.ready or previous.stage != STOP_STAGE_12003:
        local.append("previous.completed_post291F940_pre291C467")
    actor_matches = source_inputs is not None and source_inputs.get("character_id") == previous.character_full_id
    if not actor_matches:
        local.append("source_inputs.character_id_matches_previous")
    gaps.extend(item for item in local if item not in gaps)
    contiguous = context_valid and previous.ready and previous.stage == STOP_STAGE_12003 and actor_matches
    reached = False
    stage = previous.stage
    contexts = dict(previous.stage_contexts)
    outputs = dict(previous.independent_stage_outputs)
    ledger_rows, updates, future_missing = [], [], []

    def snapshot():
        return NativeModifierContext12003(PropertyContainer12003(tuple(keys), tuple(values), len(keys)),
                                         tuple(weighted), len(weighted))

    for index, (name, after_stage, module, function, family) in enumerate(stages):
        required = index <= bound_index
        missing, requests, ready = [], (), True
        conference_family_ledger = []
        gated_family_ledger = []
        after_gated_family_ledger = []
        provider192_family_ledger = []
        provider192_frontier = None
        qualifier_definition_ledger = []
        list_row_ledger = []
        try:
            if not actor_matches:
                raise ValueError("matching_character_source_unavailable")
            if module is None:
                raise ValueError("native_source_stage_unclosed")
            if name == "provider192_and2920850":
                requests, provider192_family_ledger, missing, provider192_frontier = _provider192_prefix(
                    source_inputs, module, outputs)
                ready = not missing
            elif name in ("conference24B1D00", "gated_temporary_tail", "after_gated_tail"):
                is_gated = name == "gated_temporary_tail"
                is_after_gated = name == "after_gated_tail"
                if is_after_gated:
                    family_names = ("composition_326a8e0", "current_1b8_court_positions",
                                    "current_1c0_court_positions", "related_court_positions")
                    family_emitter = "emit_after_gated_tail_family_requests_from_current_source_inputs_12003"
                    family_ledger = after_gated_family_ledger
                elif is_gated:
                    family_names = ("prefix_1398", "delta_prefix_1420_14a8", "list")
                    family_emitter = "emit_gated_temporary_tail_family_requests_from_current_source_inputs_12003"
                    family_ledger = gated_family_ledger
                else:
                    family_names = ("classified_owner", "classified_common", "owner_common", "unconditional")
                    family_emitter = "emit_conference_24b1d00_family_requests_from_current_source_inputs_12003"
                    family_ledger = conference_family_ledger
                family_contiguous = True
                for family_name in family_names:
                    family_requests, family_missing = (), []
                    try:
                        family_requests = _tail_emit(source_inputs, module, family_emitter, family_name)
                    except (ValueError, ModuleNotFoundError, AttributeError) as error:
                        family_missing.append(str(error))
                    family_ready = not family_missing
                    outputs[name + "." + family_name] = tuple(family_requests)
                    family_contiguous = family_contiguous and family_ready
                    if family_contiguous:
                        requests += tuple(family_requests)
                    missing.extend(family_name + ":" + item for item in family_missing)
                    family_ledger.append({"family": family_name, "requests_ready": family_ready,
                        "request_count": len(family_requests), "in_contiguous_family_prefix": family_contiguous,
                        "missing_inputs": tuple(family_missing)})
                ready = not missing
            elif name in ("qualifier_repeated_contribution", "list2530DD0"):
                try:
                    requests = _tail_emit(source_inputs, module, function)
                except (ValueError, ModuleNotFoundError, AttributeError) as error:
                    ready, missing = False, [str(error)]
                is_qualifier = name == "qualifier_repeated_contribution"
                leaf = source_inputs.get("qualifier_28bc0d0" if is_qualifier else "list_predicate_2530dd0")
                parts = leaf.get("definitions" if is_qualifier else "rows") if isinstance(leaf, Mapping) else None
                part_ledger = qualifier_definition_ledger if is_qualifier else list_row_ledger
                prefix_key = "in_contiguous_definition_prefix" if is_qualifier else "in_contiguous_row_prefix"
                part_emitter = ("emit_qualifier_28bc0d0_definition_requests_from_current_source_inputs_12003"
                                if is_qualifier else "emit_list_predicate_2530dd0_row_requests_from_current_source_inputs_12003")
                part_contiguous = True
                for part in parts or ():
                    native_index = part["native_index"]
                    part_requests, part_missing = (), []
                    if ready:
                        part_requests = tuple(row for row in requests if row.first_row_index == native_index)
                    else:
                        try:
                            part_requests = _tail_emit(source_inputs, module, part_emitter, native_index)
                        except (ValueError, ModuleNotFoundError, AttributeError) as error:
                            part_missing.append(str(error))
                    part_ready = not part_missing
                    outputs[name + "." + str(native_index)] = tuple(part_requests)
                    part_contiguous = part_contiguous and part_ready
                    if not ready and part_contiguous:
                        requests += tuple(part_requests)
                    part_ledger.append({"native_index": native_index, "requests_ready": part_ready,
                        "request_count": len(part_requests), prefix_key: part_contiguous,
                        "missing_inputs": tuple(part_missing)})
            else:
                requests = _tail_emit(source_inputs, module, function, family)
        except (ValueError, ModuleNotFoundError, AttributeError) as error:
            ready, missing = False, [str(error)]
        validated = []
        for request_index, request in enumerate(requests):
            request_gaps = []
            pc = _property_input(request.base_property_block)
            arrays = None if pc is None else _block_arrays(pc, f"{name}.request[{request_index}]", request_gaps)
            if arrays is None:
                request_gaps.append(f"{name}.request[{request_index}].properties")
            if type(request.weight_q64) is not int:
                request_gaps.append(f"{name}.request[{request_index}].weight_q64")
            if request_gaps:
                ready = False
                missing.extend(request_gaps)
                break
            validated.append((request, pc, arrays))
        outputs[name] = tuple(item[0] for item in validated)
        folded = contiguous and required
        if folded:
            for request, pc, arrays in validated:
                if arrays[0]:
                    weight = native_wrap64_12003(request.weight_q64)
                    weighted.append(WeightedModifierRow12003(pc, weight, len(weighted)))
                    _fold_property_request(keys, values, arrays[0], arrays[1], weight,
                        {"stage": name, "definition_identity": request.definition_identity,
                         "source_ordinal": request.source_ordinal, "first_row_index": request.first_row_index}, updates)
            if ready:
                stage = after_stage
            elif name == "provider192_and2920850" and provider192_frontier is not None:
                stage = provider192_frontier
            elif name == "qualifier_repeated_contribution" and any(
                    row["in_contiguous_definition_prefix"] for row in qualifier_definition_ledger):
                completed = sum(row["in_contiguous_definition_prefix"] for row in qualifier_definition_ledger)
                stage = "postQualifierDefinition" + str(completed - 1) + "_pre291C655"
            elif name == "list2530DD0" and any(row["in_contiguous_row_prefix"] for row in list_row_ledger):
                completed = sum(row["in_contiguous_row_prefix"] for row in list_row_ledger)
                stage = "postList2530DD0Row" + str(completed - 1) + "_preRow" + str(completed)
            elif name == "gated_temporary_tail" and any(
                    row["in_contiguous_family_prefix"] for row in gated_family_ledger):
                completed = sum(row["in_contiguous_family_prefix"] for row in gated_family_ledger)
                stage = ("postGatedPrefix1398_pre291C892",
                         "postGatedDeltaPrefix_pre291C8AE")[completed - 1]
            elif name == "after_gated_tail" and any(
                    row["in_contiguous_family_prefix"] for row in after_gated_family_ledger):
                completed = sum(row["in_contiguous_family_prefix"] for row in after_gated_family_ledger)
                stage = ("post326A8E0_pre291CB0F", "post2920310_current1B8_preCurrent1C0",
                         "post2920310_current1C0_preRelated")[completed - 1]
            elif validated:
                if name == "conference24B1D00":
                    completed = sum(row["in_contiguous_family_prefix"] for row in conference_family_ledger)
                    stage = ("post24B1D00_classified_owner_pre24B1E67",
                             "post24B1E67_pre24B1E87", "post24B1E87_pre24B1E9C")[completed - 1]
                else:
                    stage = "verified_partial_" + name
            contexts[stage] = snapshot()
        destination = gaps if required else future_missing
        destination.extend(name + ":" + missing_item for missing_item in missing)
        ledger_rows.append({"stage": name, "after_stage": after_stage, "required_for_requested_bound": required,
            "requests_ready": ready, "request_count": len(validated),
            "folded_into_contiguous_context": folded, "missing_inputs": tuple(missing),
            "conference_family_stages": tuple(conference_family_ledger),
            "gated_temporary_family_stages": tuple(gated_family_ledger),
            "after_gated_family_stages": tuple(after_gated_family_ledger),
            "provider192_family_stages": tuple(provider192_family_ledger),
            "qualifier_definition_stages": tuple(qualifier_definition_ledger),
            "list_predicate_row_stages": tuple(list_row_ledger)})
        if required:
            contiguous = contiguous and ready
            if index == bound_index:
                reached = contiguous

    ledger = {"source_exe_sha256": SOURCE_EXE_SHA256_12003,
        "prior_chain_ledger": previous.source_ledger, "requested_tail_bound": through_stage,
        "ordered_tail_stages": tuple(ledger_rows), "tail_aggregate_updates": tuple(updates),
        "future_tail_missing_inputs": tuple(future_missing),
        "first_contiguous_observation_dependency": next(
            (row["stage"] for row in ledger_rows if not row["requests_ready"]), None),
        "next_native_source_leaf": "291CC71_2920B50", "all_tail_source_stream_ready": False,
        "next_native_source_leaf_status": "source_closed_minimum_contract_pending",
        "provider_291c5b2_operand_scope": "held_current_character_1b0_2f8",
        "provider_291c5b2_return_edges": "all selection branches rejoin291C5B7",
        "qualifier_28bc0d0_operand_scope": "held_current_character_1b0_scratch_object_relationships",
        "list_predicate_2530dd0_operand_scope": "held_current_character_1b0_458_list_and_scope_inputs",
        "gated_temporary_tail_operand_scope": "held_current_selected_inputs_and_source_closed_raw_named_literals",
        "gated_temporary_rank_source": "slot168_literal_or_known_zero_then_native_clamp_and_first_LE_threshold",
        "gated_temporary_cached_FC_used": False,
        "gated_temporary_native_evaluation_equivalence_claimed": False,
        "gated_temporary_empty_PC_source_occurrences_preserved": True,
        "after_gated_tail_operand_scope": "held_current_court_position_sources_and_source_closed_literal_calendar_inputs",
        "after_gated_empty_default_scope": "actual_header_or_explicit_numeric_model_without_initializer_execution",
        "after_gated_native_evaluation_equivalence_claimed": False,
        "provider192_and2920850_operand_scope": "held_current_signed_192_rite_membership_and_list_sources",
        "provider192_list_order": "each_occurrence_four_direct_slots_then_four_nested_headers",
        "provider192_mapped_default_guard_scope": "unused_default_guard_does_not_invalidate_actual_mapped_PC",
        "provider192_native_evaluation_equivalence_claimed": False,
        "source_operand_scope": "held_current_same_query_inputs",
        "conditional_on_observed_source_values": True,
        "291f260_weight_source_scope": "held_current_evaluated_values",
        "291f260_weights_recomputed_from_assembled_context": False,
        "291f260_preceding_stage_weight_input_seam": "28C3AE0 receiver/model10 source proof required",
        "current_final_context_used_as_default": False, "unknown_stages_assumed_empty": False,
        "full_person_preparation_ready": False, "full_entry_ready": False, "game_operations": 0}
    return PersonStageChainResult12003(previous.character_full_id, stage,
        contexts.get(stage, context if context_valid else None), reached and not gaps,
        tuple(gaps), ledger, contexts, outputs)


def continue_current_person_stage_chain_tail_12003(
    person_state: Mapping, previous: PersonStageChainResult12003, *, character_full_id: int,
    through_stage: str = "2753860",
) -> PersonStageChainResult12003:
    """Consume the actual optional tail source fields from the same query."""
    if character_full_id != previous.character_full_id:
        raise ValueError("current person and previous stage characters disagree")
    return continue_person_stage_chain_tail_12003(previous,
        person_state.get("current_context_source_inputs"), through_stage=through_stage)

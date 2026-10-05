"""Conditional numeric caches from explicitly supplied person-stage contexts.

The skill/auxiliary context and scratch258-model aggregate have independent
source selections. Neither defaults to the current observation or the other.
All non-context operands are held as supplied; no native writer is executed.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, replace
from typing import Mapping

from .battle_person_auxiliary_scratch_12003 import (
    AuxiliaryScratchResult12003, compute_auxiliary_scratch_from_native_inputs_12003,
)
from .battle_person_nine_cache_bytes_12003 import (
    NineCacheByteResult12003, compute_nine_cache_bytes_from_native_inputs_12003,
)
from .battle_trait_numeric_inputs_12003 import (
    NativeModifierContext12003, NativeSkillCacheResult12003,
    compute_six_skill_cache_from_native_inputs_12003,
)


@dataclass(frozen=True, slots=True)
class ExplicitPersonCacheStage12003:
    character_full_id: int
    stage: str
    context: NativeModifierContext12003 | Mapping[str, object] | None
    source_provenance: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class ConditionalPersonCacheStageResult12003:
    character_full_id: int | None
    six_skills: NativeSkillCacheResult12003
    auxiliary: AuxiliaryScratchResult12003
    nine_bytes: NineCacheByteResult12003
    ready: bool
    missing_inputs: tuple[str, ...]
    source_ledger: Mapping[str, object]
    native_write_performed: bool = False
    historical_stage_observed: bool = False
    full_native_callback_ready: bool = False
    entry_refresh_ready: bool = False
    actual_game_days_advanced: int = 0


def _stage_context(raw: Mapping[str, object], stage: ExplicitPersonCacheStage12003 | None,
                   family: str) -> tuple[Mapping[str, object] | None, tuple[str, ...]]:
    if raw.get("scratch_present") is False:
        return None, ()
    if stage is None or stage.context is None:
        return None, (family + ".explicit_stage_context",)
    if type(raw.get("character_id")) is not int or stage.character_full_id != raw["character_id"]:
        return None, (family + ".queried_actor_association",)
    context = stage.context
    if isinstance(context, NativeModifierContext12003):
        return asdict(context), ()
    if isinstance(context, Mapping):
        return deepcopy(dict(context)), ()
    return None, (family + ".explicit_stage_context",)


def _conditional_result(result, stage: ExplicitPersonCacheStage12003 | None,
                        family: str, extra_missing: tuple[str, ...]):
    missing = tuple(dict.fromkeys((*extra_missing, *result.missing_inputs)))
    ready = result.calculation_ready and not extra_missing
    ledger = deepcopy(dict(result.ledger))
    ledger.update({
        "scope": "explicit_logical_" + family,
        "source_scope": "explicit_logical_" + family,
        "conditional_stage": stage.stage if stage is not None else None,
        "explicit_stage_character_full_id": stage.character_full_id if stage is not None else None,
        "explicit_stage_provenance": deepcopy(stage.source_provenance) if stage is not None else None,
        "context_supplied_explicitly": stage is not None and stage.context is not None,
        "current_final_context_used_as_default": False,
        "changed_stage_context_constructed": False,
        "historical_stage_observed": False,
        "other_native_operands_held_as_supplied": True,
        "full_native_callback_ready": False,
        "Entry_refresh_claim": False,
    })
    status = ("conditional_computed" if ready and result.status not in ("native_noop", "source_noop")
              else result.status if ready else "partial")
    return replace(result, ledger=ledger, missing_inputs=missing,
                   calculation_ready=ready, status=status)


def project_person_cache_stage_12003(
    raw_numeric_inputs: Mapping[str, object] | None, *,
    skill_stage: ExplicitPersonCacheStage12003 | None = None,
    scratch_model_stage: ExplicitPersonCacheStage12003 | None = None,
) -> ConditionalPersonCacheStageResult12003:
    """Reuse qualified numeric kernels on two independently tagged contexts.

    Raw input is the existing production-normalized current query section.
    Supplied stages are logical conditional inputs. The current cache evidence,
    carrier/definition guards and other operands remain independently observed.
    A source null-scratch no-op requires neither stage. Family readiness is
    independent; this interface does not create or advance a person context.
    """
    raw = deepcopy(dict(raw_numeric_inputs)) if isinstance(raw_numeric_inputs, Mapping) else {}
    skill_context, skill_missing = _stage_context(raw, skill_stage, "skill_auxiliary_stage")
    model_context, model_missing = _stage_context(raw, scratch_model_stage, "scratch258_model_stage")
    skill_view = deepcopy(raw)
    skill_view["context"] = skill_context
    six = _conditional_result(compute_six_skill_cache_from_native_inputs_12003(skill_view),
                              skill_stage, "skill_stage", skill_missing)
    auxiliary = _conditional_result(compute_auxiliary_scratch_from_native_inputs_12003(skill_view),
                                    skill_stage, "auxiliary_stage", skill_missing)

    nine_view = deepcopy(raw)
    observed_nine = raw.get("nine_cache_byte_inputs")
    nine = deepcopy(dict(observed_nine)) if isinstance(observed_nine, Mapping) else {}
    nine["model_present"] = model_context is not None
    nine["aggregate_properties"] = (deepcopy(model_context.get("aggregate_properties"))
                                    if model_context is not None else None)
    nine_view["nine_cache_byte_inputs"] = nine
    nine_result = _conditional_result(compute_nine_cache_bytes_from_native_inputs_12003(nine_view),
                                      scratch_model_stage, "scratch258_model_stage", model_missing)
    nine_ledger = dict(nine_result.ledger)
    nine_ledger["observed_current_model_present"] = (observed_nine.get("model_present")
                                                    if isinstance(observed_nine, Mapping) else None)
    nine_result = replace(nine_result, ledger=nine_ledger)

    missing = tuple(dict.fromkeys((*six.missing_inputs, *auxiliary.missing_inputs,
                                 *nine_result.missing_inputs)))
    ledger = {
        "source_rvas": ("28C3D80", "2948DF0", "2948F00", "2949010"),
        "conditional_numeric_projection": True,
        "skill_context_defaulted_from_nine_model": False,
        "nine_model_defaulted_from_skill_context": False,
        "current_final_context_used_as_default": False,
        "skill_stage": skill_stage.stage if skill_stage is not None else None,
        "scratch258_model_stage": scratch_model_stage.stage if scratch_model_stage is not None else None,
        "observed_current_auxiliary": deepcopy(raw.get("auxiliary_scratch_inputs")),
        "observed_current_nine_inputs": deepcopy(observed_nine),
        "copied_auxiliary_values_produced": False,
        "actual_cache_write_produced": False,
        "full_future_context_ready": False,
        "actual_game_days_advanced": 0,
    }
    character_id = raw.get("character_id")
    return ConditionalPersonCacheStageResult12003(
        character_id if type(character_id) is int else None, six, auxiliary, nine_result,
        six.calculation_ready and auxiliary.calculation_ready and nine_result.calculation_ready,
        missing, ledger)

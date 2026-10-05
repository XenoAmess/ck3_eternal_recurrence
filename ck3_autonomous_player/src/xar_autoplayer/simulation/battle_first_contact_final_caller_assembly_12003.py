"""Join explicit ordinary/MAA getter results to the closed final caller.

247AB27/37 loads Combat+6B8;247AB32/41 calls2651070 side0 then side1.
The existing setter supplies stored levy/MAA order and the six cache writes.
No getter arithmetic, person preparation or constructor mutation is duplicated.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, replace
from typing import Literal

from .battle_current_adapter import CurrentBattleCondition
from .battle_first_contact_final_stat_refresh_12003 import (
    FinalEntryStatInput12003, FirstContactFinalStatRefreshResult12003,
    apply_first_contact_final_stat_refresh_12003,
)
from .battle_maa_regiment_stats_12003 import (
    MaaSixStatStageResult12003, maa_six_stats_to_final_stat_input_12003,
)
from .battle_ordinary_regiment_stats_12003 import (
    OrdinarySixStatStageResult12003, ordinary_six_stats_to_final_stat_input_12003,
)


@dataclass(frozen=True, slots=True)
class FinalCallerGetterOccurrence12003:
    side_index: int
    bucket: str
    bucket_index: int
    native_carmy_id: int
    regiment_id: int
    source_combat_province_id: int
    getter_kind: Literal["ordinary", "maa"]
    getter_result: OrdinarySixStatStageResult12003 | MaaSixStatStageResult12003
    input_mode: Literal["explicit_named_stage", "declared_held_current_source"]


def assemble_closed_final_caller_12003(
    post2586ed0_condition: CurrentBattleCondition,
    occurrences: tuple[FinalCallerGetterOccurrence12003, ...], *,
    additional_final_inputs: tuple[FinalEntryStatInput12003, ...] = (),
) -> FirstContactFinalStatRefreshResult12003:
    """Refresh supplied occurrences at the caller-owned entered stage.

    Explicit named stages and held-current assumptions keep their original
    getter stage names. Missing rows remain partial in the existing setter.
    Optional already-closed inputs support the separate special-knight path.
    """
    converted, sources = [], []
    for binding in occurrences:
        result = binding.getter_result
        arguments = dict(
            side_index=binding.side_index, bucket_index=binding.bucket_index,
            native_carmy_id=binding.native_carmy_id, regiment_id=binding.regiment_id,
            # Preserve the source Province; do not relabel a tuple from another
            # Province as the final Combat tuple.
            target_province_id=binding.source_combat_province_id)
        if binding.getter_kind == "ordinary":
            entry_input = ordinary_six_stats_to_final_stat_input_12003(
                result, bucket=binding.bucket, **arguments)
        elif binding.getter_kind == "maa":
            if binding.bucket != "men_at_arms":
                raise ValueError("MAA getter result requires its actual MAA occurrence")
            entry_input = maa_six_stats_to_final_stat_input_12003(result, **arguments)
        else:
            raise ValueError("Special knights use their separate closed primitive")
        if binding.input_mode not in (
                "explicit_named_stage", "declared_held_current_source"):
            raise ValueError("An explicit getter input mode is required")
        source = {
            **deepcopy(entry_input.source_provenance),
            "caller_source": "247AB27->247AB32;247AB37->247AB41",
            "entered_stage": "caller_owned_post2586ED0",
            "getter_input_mode": binding.input_mode,
            "getter_real_stage": result.stage,
            "getter_result_ready": result.ready,
            "getter_missing_inputs": tuple(result.missing_inputs),
            "held_current_is_conditional": binding.input_mode == "declared_held_current_source",
            "future_or_historical_stage_observed": False,
        }
        entry_input = replace(
            entry_input, stat_cache=result.stat_cache if result.ready else None,
            source_provenance=source)
        converted.append(entry_input)
        sources.append({
            "identity": (binding.side_index, binding.bucket, binding.bucket_index,
                         binding.native_carmy_id, binding.regiment_id),
            "source_combat_province_id": binding.source_combat_province_id,
            "getter_kind": binding.getter_kind,
            "input_mode": binding.input_mode, "getter_real_stage": result.stage,
            "ready": result.ready, "missing_inputs": tuple(result.missing_inputs),
        })
    refreshed = apply_first_contact_final_stat_refresh_12003(
        post2586ed0_condition, (*converted, *additional_final_inputs))
    return replace(refreshed, ledger={
        **refreshed.ledger,
        "entered_stage": "caller_owned_post2586ED0",
        "source_call_sites": ("247AB32", "247AB41"),
        "final_getter_occurrence_sources": tuple(sources),
        "additional_closed_input_count": len(additional_final_inputs),
        "getter_math_duplicated": False,
        "earlier_constructor_reconstructed": False,
    })

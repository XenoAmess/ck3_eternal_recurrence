"""Actual same-query MAA operands to the existing six-stat/final-input APIs.

Only the frozen current getter is reconstructed here. Future person, extra,
script-value, culture and environment stages remain explicit caller operands.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Mapping

from .battle_maa_regiment_stats_12003 import MaaSixStatStageResult12003, finish_maa_environment_stage_12003
from .battle_maa_source_stages_12003 import (
    MaaCultureContribution12003, MaaExtraSourceStage12003,
    add_maa_culture_contributions_12003, construct_maa_baseline_stage_12003,
    apply_maa_accolade_aggregate_stage_12003,
)

STAGE_12003 = "frozen_current_source_derived_MAA_getter"
STAT_NAMES_12003 = ("max_size", "siege_raw", "damage_raw", "toughness_raw", "pursuit_raw", "screen_raw")


def _cache(row):
    from .battle_first_contact_final_stat_refresh_12003 import EntrySixStatCache12003
    return EntrySixStatCache12003(*(row[key] for key in STAT_NAMES_12003)) if isinstance(row, Mapping) else None


def _context(properties):
    return {"aggregate_properties": properties}


def _keys(value):
    return tuple(value) if isinstance(value, (tuple, list)) else None


def _culture(rows):
    if not isinstance(rows, (tuple, list)):
        return None
    return tuple(MaaCultureContribution12003(row["definition_is_gdbo"],
        row["definition_matches_selected_type"], row["class_filter"], _cache(row["stats"]),
        {"definition_index": row["definition_index"], "row_index": row["row_index"]}) for row in rows)


def maa_six_stats_from_combat_regiment_12003(
    regiment: Mapping[str, object], *, source_provenance: Mapping[str, object] | None = None,
) -> MaaSixStatStageResult12003:
    """Consume normalized real sources, never effective_stats as a base."""
    from .battle_first_contact_final_stat_refresh_12003 import PersonStatStage12003
    from .battle_ordinary_regiment_stats_12003 import calculate_ordinary_six_stat_stage_12003
    from .battle_trait_materialized_prefix_12003 import _fold_property_request

    leaf = regiment.get("maa_stat_inputs_v1")
    if not isinstance(leaf, Mapping) or leaf.get("status") != "available":
        return MaaSixStatStageResult12003(STAGE_12003, None, False, ("maa_stat_inputs_v1.available",),
            {"source": "optional actual MAA source leaf", "source_status": leaf.get("status") if isinstance(leaf, Mapping) else "omitted",
             "unavailable_reason": leaf.get("unavailable_reason") if isinstance(leaf, Mapping) else None})
    character = leaf["selected_character_full_id"]
    identity = {"source_regiment_full_id": leaf["source_regiment_full_id"],
        "selected_character_full_id": character, "character_resolution": leaf["character_resolution"],
        "source_target_province_id": leaf["source_target_province_id"],
        "source_provenance": deepcopy(source_provenance)}
    if leaf["inner_type_is_gdbo"] is False:
        ordinary = calculate_ordinary_six_stat_stage_12003(selected_character_full_id=character,
            stage=STAGE_12003 + ".inner_nonGDbo_ordinary_fallback",
            context=_context(leaf["selected_properties"]), loaded_bases=leaf["fallback_ordinary_bases"])
        cache = ordinary.stat_cache
        if cache is not None:
            cache = replace(cache, effective_damage_raw=max(100000, cache.effective_damage_raw),
                effective_toughness_raw=max(100000, cache.effective_toughness_raw))
        return MaaSixStatStageResult12003(STAGE_12003, cache, ordinary.ready, ordinary.missing_inputs,
            {**identity, "source": "30C4360 inner nonGDbo->30C3BA0->outer MAA floors",
                "ordinary_ledger": deepcopy(ordinary.ledger), "historical_stage_observed": False},
            full_getter_construction_ready=ordinary.ready)
    culture = add_maa_culture_contributions_12003(_cache(leaf["type_bases"]),
        selected_type_class=leaf["selected_type_class"], government_rows=_culture(leaf["government_rows"]),
        global_rows=_culture(leaf["global_rows"]), stage=STAGE_12003 + ".type_culture_baseline")
    selected_stage = PersonStatStage12003(character, STAGE_12003 + ".selected_Character_aggregate",
        _context(leaf["selected_properties"]), identity)
    extra = MaaExtraSourceStage12003(STAGE_12003 + ".extra120_aggregate",
        _context(leaf["extra_properties"]), leaf["holder_piety_rank"],
        _keys(leaf["extra_add_keys_u16"]), _keys(leaf["extra_mult_keys_u16"]),
        {"source_title_full_id": leaf["extra_title_full_id"], "native_holder_full_id": leaf["extra_holder_full_id"]})
    args = {"class_row_present": leaf["class_row_present"],
        "class_add_keys_u16": _keys(leaf["class_add_keys_u16"]),
        "class_mult_keys_u16": _keys(leaf["class_mult_keys_u16"])}
    baseline = construct_maa_baseline_stage_12003(culture, person_stage=selected_stage,
        extra_source=extra if leaf["class_row_present"] else None,
        selector_mode=leaf["selector_mode"], selected_government_byte_4d6=leaf["selected_government_byte_4d6"],
        selected_script_value_4e_q64=leaf["selector_factor_q64"],
        stage=STAGE_12003 + ".combined_baseline", **args)
    # Same closed logical unit-Q fold as2303120. Empty context here is the
    # constructor11E1350 scratch in30C473F, not a fabricated person reset.
    keys, values, updates = [], [], []
    for index, row in enumerate(leaf["accolade_blocks"]):
        properties = row["properties"]
        _fold_property_request(keys, values, tuple(properties["keys_u16"]), tuple(properties["values_q64"]),
            100000, {"source_block_index": index, "linked_index": row["linked_index"],
                "character_full_id": row["character_full_id"], "accolade_full_id": row["accolade_full_id"],
                "row_index": row["row_index"], "level": row["level"]}, updates)
    accolade_stage = PersonStatStage12003(character, STAGE_12003 + ".ordered_accolade_scratch",
        _context({"count": len(keys), "keys_u16": keys, "values_q64": values}),
        {"source": "30C4360 fresh11E1350 scratch then2438850 unitQ tier390 blocks",
            "updates": tuple(updates), "person_reset_performed": False})
    after = apply_maa_accolade_aggregate_stage_12003(baseline, accolade_person_stage=accolade_stage,
        stage=STAGE_12003 + ".after_accolade_apply", **args)
    result = finish_maa_environment_stage_12003(after, stage=STAGE_12003,
        definition620_present=leaf["definition620_present"],
        components={key: _cache(value) for key, value in leaf["environment_components"].items()},
        source_province_id=leaf["source_target_province_id"],
        linked_character_full_ids=tuple(leaf["linked_character_full_ids"]), source_provenance=identity)
    return replace(result, full_getter_construction_ready=result.ready,
        ledger={**result.ledger, **identity, "observed_source_kind": "frozen_current_native_operands",
            "accolade_fold_updates": tuple(updates), "person_preparation_performed": False,
            "future_final_cache_observed": False})

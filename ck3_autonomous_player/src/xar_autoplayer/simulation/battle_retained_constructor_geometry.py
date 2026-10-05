"""Immutable operands for diagnostics of this actual Combat's geometry.

This input does not describe a new contact or recreate the entire constructor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True, slots=True)
class RetainedConstructorSide:
    side_index: int
    role: str
    public_cunit_ids_in_stored_order: tuple[int, ...]
    primary_participant_character_id: int | None


@dataclass(frozen=True, slots=True)
class RetainedConstructorGeometryInput:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    terrain_key: str
    terrain_width_multiplier_raw: int
    constructor_adjacency_kind_raw: int
    crossing_kind: str
    holding_defender: bool
    adjacency_source: str
    holding_source: str
    sides: tuple[RetainedConstructorSide, RetainedConstructorSide]
    attacker_adjacency_rules_pointer_offset: int
    defender_adjacency_rules_pointer_offset: int
    holding_defender_rules_pointer_offset: int
    game_version: str
    executable_sha256: str


def adapt_retained_constructor_geometry(
    diagnostic: Mapping[str, object],
) -> RetainedConstructorGeometryInput | None:
    """Consume an existing service diagnostic at its independent ready boundary."""
    if diagnostic.get("retained_geometry_ready") is not True:
        return None
    source = diagnostic["source"]
    terrain = diagnostic["terrain"]
    plan = diagnostic["constructor_rule_plan"]
    sides = tuple(RetainedConstructorSide(
        side_index=row["side_index"], role=row["role"],
        public_cunit_ids_in_stored_order=tuple(row["public_cunit_ids_in_stored_order"]),
        primary_participant_character_id=row.get("primary_participant_character_id"),
    ) for row in diagnostic["actual_sides_in_stored_order"])
    return RetainedConstructorGeometryInput(
        combat_id=source["combat_id"], province_id=source["province_id"],
        snapshot_revision=source["snapshot_revision"], observed_date_raw=source["observed_date_raw"],
        terrain_key=terrain["key"],
        terrain_width_multiplier_raw=terrain["combat_width_multiplier_raw"],
        constructor_adjacency_kind_raw=diagnostic["constructor_adjacency_kind_raw"],
        crossing_kind=diagnostic["crossing_kind"], holding_defender=diagnostic["holding_defender"],
        adjacency_source=diagnostic["adjacency_source"], holding_source=diagnostic["holding_source"],
        sides=(sides[0], sides[1]),
        attacker_adjacency_rules_pointer_offset=plan["attacker_adjacency"]["rules_pointer_offset"],
        defender_adjacency_rules_pointer_offset=plan["defender_adjacency"]["rules_pointer_offset"],
        holding_defender_rules_pointer_offset=plan["holding_defender"]["rules_pointer_offset"],
        game_version=source["game_version"], executable_sha256=source["executable_sha256"],
    )


@dataclass(frozen=True, slots=True)
class CurrentLoadedRetainedRuleEffect:
    stage: str
    side_index: int
    rules_pointer_offset: int
    status: str
    key: str | None
    advantage_points: int | None


@dataclass(frozen=True, slots=True)
class CurrentLoadedRetainedRuleEffectsInput:
    combat_id: int
    province_id: int
    snapshot_revision: int
    observed_date_raw: int
    constructor_adjacency_kind_raw: int
    holding_defender: bool
    points_scale: int
    rows: tuple[CurrentLoadedRetainedRuleEffect, ...]
    source: str
    selection_scope: str


def adapt_current_loaded_retained_rule_effects(
    diagnostic: Mapping[str, object],
) -> CurrentLoadedRetainedRuleEffectsInput | None:
    """Independent loaded-value input, without requiring full geometry readiness."""
    if diagnostic.get("loaded_selected_rule_effects_ready") is not True:
        return None
    source = diagnostic["source"]
    effects = diagnostic["current_loaded_rule_effects"]
    return CurrentLoadedRetainedRuleEffectsInput(
        combat_id=source["combat_id"], province_id=source["province_id"],
        snapshot_revision=source["snapshot_revision"], observed_date_raw=source["observed_date_raw"],
        constructor_adjacency_kind_raw=diagnostic["constructor_adjacency_kind_raw"],
        holding_defender=diagnostic["holding_defender"], points_scale=effects["points_scale"],
        rows=tuple(CurrentLoadedRetainedRuleEffect(
            stage=row["stage"], side_index=row["side_index"],
            rules_pointer_offset=row["rules_pointer_offset"], status=row["status"],
            key=row["key"], advantage_points=row["advantage_points"],
        ) for row in effects["rows"]),
        source=diagnostic["loaded_effect_source"],
        selection_scope=diagnostic["loaded_effect_selection_scope"],
    )

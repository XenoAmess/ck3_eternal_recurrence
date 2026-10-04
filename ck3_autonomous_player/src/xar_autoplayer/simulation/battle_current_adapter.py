"""Map normalized actual battle observations to current-condition kernels.

This adapter preserves native bucket order and Q100000 quantities. It does
not select future participants, refresh their stats, or infer component
soldiers from an entry's fractional troop accounts.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Mapping

from .combat_core import (
    BackingComponent,
    CombatRegimentState,
    CommanderRollRequest,
    RegimentKind,
)


@dataclass(frozen=True, slots=True)
class CurrentLossSideInputs:
    side_index: int
    outgoing_advantage_factor_raw: int
    own_hard_conversion_modifier_raw: int
    opposing_hard_conversion_modifier_raw: int
    primary_participant_character_id: int | None = None
    levy_damage_raw: int | None = None


@dataclass(frozen=True, slots=True)
class CurrentLossInputs:
    scale: int
    source_combat_id: int
    source_target_province_id: int
    stored_advantage_damage_factor_raw: int
    runtime_damage_scaling_raw: int
    runtime_main_hard_conversion_raw: int
    runtime_pursuit_hard_conversion_raw: int
    province_has_holding: bool
    province_winter_hard_conversion_modifier_raw: int
    sides: tuple[CurrentLossSideInputs, CurrentLossSideInputs]


@dataclass(frozen=True, slots=True)
class CurrentBattleEntry:
    state: CombatRegimentState
    bucket: str
    bucket_index: int
    native_carmy_id: int
    public_cunit_id: int
    owner_character_id: int
    starting_raw: int
    effective_damage_raw: int
    fights_in_main_phase: bool
    hard_casualties_raw: int | None
    knight_character_id_raw: int | None
    backing_components: tuple[BackingComponent, ...] | None
    source_entry: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CurrentBattleSide:
    side_index: int
    role: str
    primary_participant_character_id: int
    selected_commander_character_id: int
    current_roll_points: int
    roll_request: CommanderRollRequest | None
    entries: tuple[CurrentBattleEntry, ...]
    ordered_armies: tuple[Mapping[str, object], ...]
    stored_current_fighting_raw: int
    stored_levy_current_fighting_raw: int
    derived_current_fighting_raw: int
    derived_soft_casualties_raw: int
    derived_main_fighting_entry_hard_casualties_raw: int
    non_main_start_minus_current_minus_soft_raw: int
    participant_hard_ledger: tuple[Mapping[str, object], ...]
    participant_hard_total_raw: int
    loss_inputs: CurrentLossSideInputs | None
    levy_damage_raw: int | None
    levy_damage_source: str
    levy_damage_native_observed: bool
    levy_damage_primary_participant_character_id: int | None

    @property
    def states(self) -> tuple[CombatRegimentState, ...]:
        return tuple(entry.state for entry in self.entries)


@dataclass(frozen=True, slots=True)
class CurrentBattleCondition:
    snapshot_revision: int
    observed_date_raw: int
    combat_id: int
    province_id: int
    subject_side_index: int
    side_scope: str
    phase: str
    phase_raw: int
    phase_day: int
    base_combat_width: int
    final_combat_width: int
    roll_cadence_counter: int
    base_advantage_raw: int
    resolved_advantage_raw: int
    sides: tuple[CurrentBattleSide, CurrentBattleSide]
    loss_inputs: CurrentLossInputs | None
    active_counter_inputs: Mapping[str, object] | None
    pursuit_modifier_sides: Mapping[str, object] | None
    missing_inputs: tuple[str, ...]
    source_snapshot: Mapping[str, object]


def _loss_inputs(value: object) -> CurrentLossInputs | None:
    if value is None:
        return None
    # The production normalizer already validates the complete shape, units,
    # native side order and source Combat/Province identities.
    return CurrentLossInputs(
        scale=value["scale"],
        source_combat_id=value["source_combat_id"],
        source_target_province_id=value["source_target_province_id"],
        stored_advantage_damage_factor_raw=value["stored_advantage_damage_factor_raw"],
        runtime_damage_scaling_raw=value["runtime_damage_scaling_raw"],
        runtime_main_hard_conversion_raw=value["runtime_main_hard_conversion_raw"],
        runtime_pursuit_hard_conversion_raw=value["runtime_pursuit_hard_conversion_raw"],
        province_has_holding=value["province_has_holding"],
        province_winter_hard_conversion_modifier_raw=value["province_winter_hard_conversion_modifier_raw"],
        sides=tuple(CurrentLossSideInputs(
            side_index=row["side_index"],
            outgoing_advantage_factor_raw=row["outgoing_advantage_factor_raw"],
            own_hard_conversion_modifier_raw=row["own_hard_conversion_modifier_raw"],
            opposing_hard_conversion_modifier_raw=row["opposing_hard_conversion_modifier_raw"],
            primary_participant_character_id=row.get("primary_participant_character_id"),
            levy_damage_raw=row.get("levy_damage_raw"),
        ) for row in value["sides"]),
    )


def _roll_request(
    side: Mapping[str, object], side_index: int,
    resume: Mapping[str, object] | None,
) -> CommanderRollRequest | None:
    previous = side["current_roll_points"]
    if side["selected_commander_character_id"] == -1:
        return CommanderRollRequest(False, 0, 0, previous)
    observed = resume.get("observed") if resume is not None else None
    bounds = (
        observed.get(f"side_{side_index}_selected_commander_next_roll_bounds")
        if isinstance(observed, Mapping) else None
    )
    if not isinstance(bounds, Mapping) or bounds.get("status") != "available":
        return None
    return CommanderRollRequest(
        True, bounds["effective_min_roll"], bounds["effective_max_roll"], previous,
    )


def adapt_current_battle_condition(
    snapshot: Mapping[str, object], *,
    backing_components_by_regiment_id: Mapping[int, tuple[BackingComponent, ...]] | None = None,
    active_resume_inputs: Mapping[str, object] | None = None,
    levy_damage_raw_by_side: Mapping[int, int] | None = None,
) -> CurrentBattleCondition:
    """Adapt an available normalized ``battle_control_snapshot_v1`` leaf.

    Native primary levy damage is copied unchanged from the loss side.
    Optional backing tuples and fallback levy values must be caller-observed
    operands. Missing backing tuples remain None; the core state's empty
    tuple only permits Q casualty arithmetic, and its integer allocation
    output must not be reported as observed. Optional roll bounds come from
    the existing normalized active-resume leaf for the same observation.
    """
    if snapshot.get("status") != "available":
        raise ValueError("an available normalized battle-control leaf is required")
    source = copy.deepcopy(dict(snapshot))
    loss = _loss_inputs(source.get("current_loss_inputs_v1"))
    missing: list[str] = []
    if loss is None:
        missing.append("current_loss_inputs_v1")
    counter = source.get("active_counter_inputs_v1")
    if not isinstance(counter, Mapping) or counter.get("status") != "available":
        missing.append("active_counter_inputs_v1")
    resume = active_resume_inputs
    if resume is not None:
        resume_source = resume.get("source")
        same_frame = isinstance(resume_source, Mapping) and all(
            resume_source.get(key) == source[key]
            for key in ("snapshot_revision", "observed_date_raw", "combat_id", "province_id")
        )
        if not same_frame:
            resume = None
            missing.append("active_resume_inputs_same_frame")

    sides: list[CurrentBattleSide] = []
    for index, key in enumerate(("attacker", "defender")):
        side = source[key]
        entries: list[CurrentBattleEntry] = []
        for bucket, kind in (
            ("levy", RegimentKind.LEVY),
            ("men_at_arms", RegimentKind.MEN_AT_ARMS),
        ):
            for row in side[f"{bucket}_entries"]:
                regiment_id = row["regiment_id"]
                backing = (
                    backing_components_by_regiment_id.get(regiment_id)
                    if backing_components_by_regiment_id is not None else None
                )
                if backing is not None:
                    backing = tuple(backing)
                else:
                    missing.append(f"backing_components.{regiment_id}")
                # Retained MAA entries participate using their actual current
                # quantity. Main eligibility describes hard-account semantics;
                # it is not a replacement for the current native MAA loop.
                state = CombatRegimentState(
                    regiment_id=regiment_id,
                    kind=kind,
                    current_raw=row["current_fighting_raw"],
                    soft_casualties_raw=row["soft_casualties_raw"],
                    toughness_raw=row["effective_toughness_raw"],
                    pursuit_raw=row["effective_pursuit_raw"],
                    screen_raw=row["effective_screen_raw"],
                    components=backing if backing is not None else (),
                )
                entries.append(CurrentBattleEntry(
                    state=state, bucket=bucket, bucket_index=row["bucket_index"],
                    native_carmy_id=row["native_carmy_id"],
                    public_cunit_id=row["public_cunit_id"],
                    owner_character_id=row["owner_character_id"],
                    starting_raw=row["starting_raw"],
                    effective_damage_raw=row["effective_damage_raw"],
                    fights_in_main_phase=row["fights_in_main_phase"],
                    hard_casualties_raw=row["hard_casualties_raw"],
                    knight_character_id_raw=row.get("knight_character_id_raw"),
                    backing_components=backing, source_entry=row,
                ))
        roll = _roll_request(side, index, resume)
        if roll is None:
            missing.append(f"selected_commander_next_roll_bounds.{index}")
        side_loss = loss.sides[index] if loss is not None else None
        native_levy_damage = (
            side_loss.levy_damage_raw if side_loss is not None else None
        )
        caller_levy_damage = (
            levy_damage_raw_by_side.get(index)
            if levy_damage_raw_by_side is not None else None
        )
        if native_levy_damage is not None:
            levy_damage = native_levy_damage
            levy_source = f"current_loss_inputs_v1.sides[{index}].levy_damage_raw"
            levy_actor = side_loss.primary_participant_character_id
        elif caller_levy_damage is not None:
            levy_damage = caller_levy_damage
            levy_source = "caller_observed_primary_participant_operand"
            levy_actor = side["primary_participant_character_id"]
        else:
            levy_damage = None
            levy_source = "unavailable"
            levy_actor = (
                side_loss.primary_participant_character_id
                if side_loss is not None else None
            )
        sides.append(CurrentBattleSide(
            side_index=index, role=side["role"],
            primary_participant_character_id=side["primary_participant_character_id"],
            selected_commander_character_id=side["selected_commander_character_id"],
            current_roll_points=side["current_roll_points"], roll_request=roll,
            entries=tuple(entries), ordered_armies=tuple(side["ordered_armies"]),
            stored_current_fighting_raw=side["stored_current_fighting_raw"],
            stored_levy_current_fighting_raw=side["stored_levy_current_fighting_raw"],
            derived_current_fighting_raw=side["derived_current_fighting_raw"],
            derived_soft_casualties_raw=side["derived_soft_casualties_raw"],
            derived_main_fighting_entry_hard_casualties_raw=side["derived_main_fighting_entry_hard_casualties_raw"],
            non_main_start_minus_current_minus_soft_raw=side["non_main_start_minus_current_minus_soft_raw"],
            participant_hard_ledger=tuple(side["participant_hard_ledger"]),
            participant_hard_total_raw=side["participant_hard_total_raw"],
            loss_inputs=side_loss, levy_damage_raw=levy_damage,
            levy_damage_source=levy_source,
            levy_damage_native_observed=native_levy_damage is not None,
            levy_damage_primary_participant_character_id=levy_actor,
        ))
    return CurrentBattleCondition(
        snapshot_revision=source["snapshot_revision"],
        observed_date_raw=source["observed_date_raw"],
        combat_id=source["combat_id"], province_id=source["province_id"],
        subject_side_index=source["side_index"], side_scope=source["side_scope"],
        phase=source["phase"], phase_raw=source["phase_raw"], phase_day=source["phase_day"],
        base_combat_width=source["base_combat_width"],
        final_combat_width=source["final_combat_width"],
        roll_cadence_counter=source["roll_cadence_counter"],
        base_advantage_raw=source["base_advantage_raw"],
        resolved_advantage_raw=source["resolved_advantage_raw"],
        sides=(sides[0], sides[1]), loss_inputs=loss,
        active_counter_inputs=counter,
        pursuit_modifier_sides=source.get("pursuit_modifier_sides"),
        missing_inputs=tuple(missing), source_snapshot=source,
    )

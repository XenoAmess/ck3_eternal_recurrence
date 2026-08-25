"""Immutable adapter for normalized combat-simulation-inputs-v2 payloads."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .combat_core import (
    FIXED_SCALE,
    CombatRegimentState,
    RegimentKind,
    TransitionFidelityManifest,
    fixed_div,
    fixed_mul,
)


class CombatInputError(ValueError):
    pass


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise CombatInputError(f"{name} must be an object")
    return value


def _array(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise CombatInputError(f"{name} must be an array")
    return value


def _integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CombatInputError(f"{name} must be an integer")
    return value


def _positive(value: object, name: str) -> int:
    result = _integer(value, name)
    if result <= 0:
        raise CombatInputError(f"{name} must be positive")
    return result


def _available(row: dict[str, object], name: str) -> None:
    if row.get("status") != "available":
        raise CombatInputError(f"{name} is not available")


def _scale(row: dict[str, object], name: str) -> None:
    if _integer(row.get("scale"), f"{name}.scale") != FIXED_SCALE:
        raise CombatInputError(f"{name}.scale is not Q100000")


def _ids(value: object, name: str) -> tuple[int, ...]:
    result = tuple(
        _positive(item, f"{name}[{index}]")
        for index, item in enumerate(_array(value, name))
    )
    if len(result) != len(set(result)):
        raise CombatInputError(f"{name} repeats an ID")
    return result


@dataclass(frozen=True, slots=True)
class CounterTargetInput:
    class_index: int
    effectiveness_raw: int


@dataclass(frozen=True, slots=True)
class RegimentCounterInput:
    class_index: int
    current_chunk_raw: int
    stack_size_soldiers: int
    targets: tuple[CounterTargetInput, ...]


@dataclass(frozen=True, slots=True)
class EffectiveRegimentStats:
    max_size: int
    siege_value_raw: int
    damage_raw: int
    toughness_raw: int
    pursuit_raw: int
    screen_raw: int


@dataclass(frozen=True, slots=True)
class FixedContactRegimentInput:
    regiment_id: int
    kind: RegimentKind
    maa_type_key: str | None
    current_soldiers: int
    maximum_soldiers: int
    fights_in_main_phase: bool
    stats: EffectiveRegimentStats
    counter: RegimentCounterInput | None

    def to_initial_combat_state(self) -> CombatRegimentState:
        current_raw = self.current_soldiers * FIXED_SCALE
        return CombatRegimentState(
            regiment_id=self.regiment_id,
            kind=self.kind,
            current_raw=current_raw if self.fights_in_main_phase else 0,
            soft_casualties_raw=0 if self.fights_in_main_phase else current_raw,
            toughness_raw=self.stats.toughness_raw,
            pursuit_raw=self.stats.pursuit_raw,
            screen_raw=self.stats.screen_raw,
        )


@dataclass(frozen=True, slots=True)
class FixedContactCommanderInput:
    character_id: int | None
    generic_advantage_points: int | None
    effective_min_roll: int
    effective_max_roll: int


@dataclass(frozen=True, slots=True)
class FixedContactKnightInput:
    character_id: int
    source_regiment_id: int
    native_army_id: int
    prowess: int
    effectiveness_raw: int
    damage_raw: int
    toughness_raw: int


@dataclass(frozen=True, slots=True)
class FixedContactArmyInput:
    public_army_id: int
    native_army_id: int
    encounter_role: str
    coalition_side: str
    scope_role: str
    owner_character_id: int
    current_province_id: int
    commander: FixedContactCommanderInput
    regiments: tuple[FixedContactRegimentInput, ...]
    knights: tuple[FixedContactKnightInput, ...]

    @property
    def current_soldiers(self) -> int:
        return sum(regiment.current_soldiers for regiment in self.regiments)

    @property
    def main_phase_soldiers(self) -> int:
        return sum(
            regiment.current_soldiers
            for regiment in self.regiments
            if regiment.fights_in_main_phase
        )


@dataclass(frozen=True, slots=True)
class CounterResolutionInput:
    countered_side: str
    countering_side: str
    countered_owner_character_id: int
    countering_owner_character_id: int
    context_scale_raw: int
    damage_retention_by_class_raw: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class FixedContactEncounterInput:
    target_province_id: int
    attacker_entry_province_id: int
    attacker_side: str
    defender_side: str
    attacker_army_ids: tuple[int, ...]
    defender_army_ids: tuple[int, ...]
    participant_policy: str
    terrain_key: str
    terrain_width_multiplier_raw: int
    crossing_kind: str
    holding_defender: bool
    base_width: int
    final_width: int


@dataclass(frozen=True, slots=True)
class FrozenCombatSimulationInput:
    input_sha256: str
    encounter: FixedContactEncounterInput
    armies: tuple[FixedContactArmyInput, ...]
    counter_resolutions: tuple[CounterResolutionInput, ...]
    input_observation_ready: bool
    native_monte_carlo_ready: bool
    native_missing_required_domains: tuple[str, ...]
    capture_snapshot_id: str | None = None
    capture_revision: int | None = None
    capture_native_revision: int | None = None
    capture_date_raw: int | None = None

    def armies_for_side(self, coalition_side: str) -> tuple[FixedContactArmyInput, ...]:
        return tuple(
            army for army in self.armies if army.coalition_side == coalition_side
        )

    def initial_entries_for_side(
        self, coalition_side: str
    ) -> tuple[CombatRegimentState, ...]:
        return tuple(
            regiment.to_initial_combat_state()
            for army in self.armies_for_side(coalition_side)
            for regiment in army.regiments
        )

    def dynamic_counter_retention_by_class_raw(
        self,
        countered_side: str,
        countered_entries: tuple[CombatRegimentState, ...],
        countering_entries: tuple[CombatRegimentState, ...],
    ) -> tuple[int, ...]:
        """Recompute ``0x23CF1B0`` from the current combat-entry pools.

        The live v2 wire publishes the initial native chunk. For the pinned
        stock rows it is exactly invertible to the inner-type integer stack;
        the parser rejects a row where that denominator cannot be recovered.
        Subsequent depleted chunks are therefore evaluated from each current
        Q100000 entry instead of freezing the pre-contact retention vector.
        """

        resolution = next(
            (
                row
                for row in self.counter_resolutions
                if row.countered_side == countered_side
            ),
            None,
        )
        if resolution is None:
            raise CombatInputError(f"no counter resolution for {countered_side}")
        countered_regiments = tuple(
            regiment
            for army in self.armies_for_side(countered_side)
            for regiment in army.regiments
        )
        countering_regiments = tuple(
            regiment
            for army in self.armies_for_side(resolution.countering_side)
            for regiment in army.regiments
        )
        _validate_entry_census(countered_regiments, countered_entries)
        _validate_entry_census(countering_regiments, countering_entries)

        class_count = len(resolution.damage_retention_by_class_raw)
        pressure = [0] * class_count
        own_chunks = [0] * class_count
        context_scale_raw = max(0, resolution.context_scale_raw)

        for regiment, entry in zip(
            countered_regiments, countered_entries, strict=True
        ):
            if regiment.counter is None or entry.current_raw <= 0:
                continue
            class_index = regiment.counter.class_index
            if not 0 <= class_index < class_count:
                raise CombatInputError("countered class is outside resolution")
            own_chunks[class_index] += fixed_div(
                entry.current_raw,
                regiment.counter.stack_size_soldiers * FIXED_SCALE,
            )

        for regiment, entry in zip(
            countering_regiments, countering_entries, strict=True
        ):
            if regiment.counter is None or entry.current_raw <= 0:
                continue
            chunk_raw = fixed_div(
                entry.current_raw,
                regiment.counter.stack_size_soldiers * FIXED_SCALE,
            )
            for target in regiment.counter.targets:
                if not 0 <= target.class_index < class_count:
                    raise CombatInputError("counter target is outside resolution")
                pressure[target.class_index] += fixed_mul(
                    fixed_mul(chunk_raw, target.effectiveness_raw),
                    context_scale_raw,
                )

        retention: list[int] = []
        for class_index in range(class_count):
            if own_chunks[class_index] <= 0:
                retention.append(FIXED_SCALE)
                continue
            counter_ratio_raw = fixed_div(
                fixed_div(pressure[class_index], own_chunks[class_index]),
                200_000,
            )
            retention.append(
                FIXED_SCALE
                - fixed_mul(min(FIXED_SCALE, counter_ratio_raw), 90_000)
            )
        return tuple(retention)

    def counter_adjusted_damage_raw(self, coalition_side: str) -> int:
        resolution = next(
            (
                row
                for row in self.counter_resolutions
                if row.countered_side == coalition_side
            ),
            None,
        )
        if resolution is None:
            raise CombatInputError(f"no counter resolution for {coalition_side}")
        total = 0
        for army in self.armies_for_side(coalition_side):
            for regiment in army.regiments:
                if not regiment.fights_in_main_phase:
                    continue
                damage_raw = regiment.stats.damage_raw
                if regiment.counter is not None:
                    class_index = regiment.counter.class_index
                    if not 0 <= class_index < len(
                        resolution.damage_retention_by_class_raw
                    ):
                        raise CombatInputError("counter class is outside resolution")
                    damage_raw = fixed_mul(
                        damage_raw,
                        resolution.damage_retention_by_class_raw[class_index],
                    )
                total += fixed_mul(
                    damage_raw, regiment.current_soldiers * FIXED_SCALE
                )
        return total


def _validate_entry_census(
    regiments: tuple[FixedContactRegimentInput, ...],
    entries: tuple[CombatRegimentState, ...],
) -> None:
    if len(regiments) != len(entries):
        raise CombatInputError("entry/input census drifted")
    if any(
        regiment.regiment_id != entry.regiment_id
        for regiment, entry in zip(regiments, entries, strict=True)
    ):
        raise CombatInputError("entry/input stored order drifted")


@dataclass(frozen=True, slots=True)
class EngagementReadiness:
    input_observation_ready: bool
    transition_fidelity_gate: bool
    planner_usable: bool
    active_attack_allowed: bool
    forecast_status: str
    sample_count: int
    reasons: tuple[str, ...]


def engagement_readiness(
    combat_input: FrozenCombatSimulationInput,
    manifest: TransitionFidelityManifest,
) -> EngagementReadiness:
    reasons: list[str] = []
    if not combat_input.input_observation_ready:
        reasons.append("combat_input_observation_not_ready")
    if not manifest.fidelity_gate:
        reasons.extend(manifest.missing_required_domains)
    ready_for_kernel = combat_input.input_observation_ready and manifest.fidelity_gate
    if ready_for_kernel:
        reasons.append("monte_carlo_experiment_not_run")
    return EngagementReadiness(
        input_observation_ready=combat_input.input_observation_ready,
        transition_fidelity_gate=manifest.fidelity_gate,
        planner_usable=False,
        active_attack_allowed=False,
        forecast_status=(
            "ready-for-exact-kernel" if ready_for_kernel else "unavailable"
        ),
        sample_count=0,
        reasons=tuple(dict.fromkeys(reasons)),
    )


def _parse_regiment(row_value: object, *, target_id: int, name: str) -> FixedContactRegimentInput:
    row = _object(row_value, name)
    _available(row, name)
    if row.get("identity_valid") is not True:
        raise CombatInputError(f"{name} identity is not valid")
    regiment_id = _positive(row.get("regiment_id"), f"{name}.regiment_id")
    current = _integer(row.get("current_soldiers"), f"{name}.current_soldiers")
    maximum = _integer(row.get("maximum_soldiers"), f"{name}.maximum_soldiers")
    if current < 0 or maximum < 0:
        raise CombatInputError(f"{name} soldier counts must be nonnegative")
    kind_row = _object(row.get("kind"), f"{name}.kind")
    _available(kind_row, f"{name}.kind")
    try:
        kind = RegimentKind(kind_row.get("value"))
    except ValueError as exc:
        raise CombatInputError(f"{name}.kind is unsupported") from exc
    fights = row.get("fights_in_main_phase")
    if not isinstance(fights, bool):
        raise CombatInputError(f"{name}.fights_in_main_phase must be boolean")

    maa_row = _object(row.get("maa_type"), f"{name}.maa_type")
    maa_status = maa_row.get("status")
    maa_key: str | None
    if maa_status == "available":
        maa_key = maa_row.get("key")
        if not isinstance(maa_key, str) or not maa_key:
            raise CombatInputError(f"{name}.maa_type.key is invalid")
    elif maa_status == "absent":
        maa_key = None
    else:
        raise CombatInputError(f"{name}.maa_type is not available/absent")

    stats_row = _object(row.get("effective_stats"), f"{name}.effective_stats")
    _available(stats_row, f"{name}.effective_stats")
    _scale(stats_row, f"{name}.effective_stats")
    if _positive(
        stats_row.get("source_target_province_id"),
        f"{name}.effective_stats.source_target_province_id",
    ) != target_id:
        raise CombatInputError(f"{name} effective target drifted")
    stats = EffectiveRegimentStats(
        max_size=_integer(stats_row.get("max_size"), f"{name}.stats.max_size"),
        siege_value_raw=_integer(
            stats_row.get("siege_value_raw"), f"{name}.stats.siege_value_raw"
        ),
        damage_raw=_integer(stats_row.get("damage_raw"), f"{name}.stats.damage_raw"),
        toughness_raw=_integer(
            stats_row.get("toughness_raw"), f"{name}.stats.toughness_raw"
        ),
        pursuit_raw=_integer(stats_row.get("pursuit_raw"), f"{name}.stats.pursuit_raw"),
        screen_raw=_integer(stats_row.get("screen_raw"), f"{name}.stats.screen_raw"),
    )

    counter_row = _object(row.get("counter"), f"{name}.counter")
    counter: RegimentCounterInput | None
    if counter_row.get("status") == "absent":
        counter = None
    elif counter_row.get("status") == "available":
        _scale(counter_row, f"{name}.counter")
        current_chunk_raw = _positive(
            counter_row.get("current_chunk_raw"),
            f"{name}.counter.current_chunk_raw",
        )
        if current <= 0:
            raise CombatInputError(
                f"{name}.counter cannot recover stack from a nonpositive current"
            )
        stack_numerator = current * FIXED_SCALE
        stack_size_soldiers, stack_remainder = divmod(
            stack_numerator, current_chunk_raw
        )
        if stack_size_soldiers <= 0 or stack_remainder != 0:
            raise CombatInputError(
                f"{name}.counter initial chunk is not exactly stack-invertible"
            )
        if fixed_div(
            current * FIXED_SCALE, stack_size_soldiers * FIXED_SCALE
        ) != current_chunk_raw:
            raise CombatInputError(
                f"{name}.counter recovered stack does not reproduce native chunk"
            )
        targets = tuple(
            CounterTargetInput(
                class_index=_integer(
                    _object(target, f"{name}.counter.targets[{index}]").get("class_index"),
                    f"{name}.counter.targets[{index}].class_index",
                ),
                effectiveness_raw=_integer(
                    _object(target, f"{name}.counter.targets[{index}]").get("effectiveness_raw"),
                    f"{name}.counter.targets[{index}].effectiveness_raw",
                ),
            )
            for index, target in enumerate(
                _array(counter_row.get("targets"), f"{name}.counter.targets")
            )
        )
        counter = RegimentCounterInput(
            class_index=_integer(
                counter_row.get("class_index"), f"{name}.counter.class_index"
            ),
            current_chunk_raw=current_chunk_raw,
            stack_size_soldiers=stack_size_soldiers,
            targets=targets,
        )
    else:
        raise CombatInputError(f"{name}.counter is not available/absent")
    return FixedContactRegimentInput(
        regiment_id=regiment_id,
        kind=kind,
        maa_type_key=maa_key,
        current_soldiers=current,
        maximum_soldiers=maximum,
        fights_in_main_phase=fights,
        stats=stats,
        counter=counter,
    )


def _parse_army(row_value: object, *, target_id: int, name: str) -> FixedContactArmyInput:
    row = _object(row_value, name)
    _available(row, name)
    role = row.get("encounter_role")
    if role not in {"attacker", "defender"}:
        raise CombatInputError(f"{name}.encounter_role is invalid")
    scope_role = row.get("scope_role")
    if not isinstance(scope_role, str):
        raise CombatInputError(f"{name}.scope_role is invalid")
    coalition = "enemy" if scope_role == "active_war_enemy" else "player_or_allied"
    native_army_id = _positive(row.get("native_carmy_id"), f"{name}.native_carmy_id")

    owner_row = _object(row.get("owner"), f"{name}.owner")
    _available(owner_row, f"{name}.owner")
    _scale(owner_row, f"{name}.owner")

    commander_row = _object(row.get("commander"), f"{name}.commander")
    commander_status = commander_row.get("status")
    battle_row = _object(
        commander_row.get("battle_context"), f"{name}.commander.battle_context"
    )
    _available(battle_row, f"{name}.commander.battle_context")
    if _positive(
        battle_row.get("source_target_province_id"),
        f"{name}.commander.battle_context.source_target_province_id",
    ) != target_id:
        raise CombatInputError(f"{name} commander target drifted")
    if commander_status == "available":
        commander_id = _positive(
            commander_row.get("character_id"), f"{name}.commander.character_id"
        )
        generic_advantage = _integer(
            commander_row.get("generic_advantage_points"),
            f"{name}.commander.generic_advantage_points",
        )
    elif commander_status == "absent":
        commander_id = None
        generic_advantage = None
    else:
        raise CombatInputError(f"{name}.commander is unavailable")
    commander = FixedContactCommanderInput(
        character_id=commander_id,
        generic_advantage_points=generic_advantage,
        effective_min_roll=_integer(
            battle_row.get("effective_min_roll"),
            f"{name}.commander.effective_min_roll",
        ),
        effective_max_roll=_integer(
            battle_row.get("effective_max_roll"),
            f"{name}.commander.effective_max_roll",
        ),
    )

    regiments = tuple(
        _parse_regiment(item, target_id=target_id, name=f"{name}.regiments[{index}]")
        for index, item in enumerate(_array(row.get("regiments"), f"{name}.regiments"))
    )
    regiment_ids = {regiment.regiment_id for regiment in regiments}
    if len(regiment_ids) != len(regiments):
        raise CombatInputError(f"{name} repeats a RegimentID")

    knights_row = _object(row.get("knights"), f"{name}.knights")
    _available(knights_row, f"{name}.knights")
    knights: list[FixedContactKnightInput] = []
    for index, item in enumerate(_array(knights_row.get("members"), f"{name}.knights.members")):
        member_name = f"{name}.knights.members[{index}]"
        member = _object(item, member_name)
        _scale(member, member_name)
        if member.get("eligible") is not True or member.get(
            "participant_army_membership_verified"
        ) is not True:
            raise CombatInputError(f"{member_name} is not eligible/membership-safe")
        source_regiment = _positive(
            member.get("source_regiment_id"), f"{member_name}.source_regiment_id"
        )
        if source_regiment not in regiment_ids:
            raise CombatInputError(f"{member_name} is outside army regiments")
        if _positive(member.get("army_id"), f"{member_name}.army_id") != native_army_id:
            raise CombatInputError(f"{member_name} native army drifted")
        knights.append(
            FixedContactKnightInput(
                character_id=_positive(
                    member.get("character_id"), f"{member_name}.character_id"
                ),
                source_regiment_id=source_regiment,
                native_army_id=native_army_id,
                prowess=_integer(member.get("prowess"), f"{member_name}.prowess"),
                effectiveness_raw=_integer(
                    member.get("knight_effectiveness_raw"),
                    f"{member_name}.knight_effectiveness_raw",
                ),
                damage_raw=_integer(
                    member.get("effective_damage_raw"),
                    f"{member_name}.effective_damage_raw",
                ),
                toughness_raw=_integer(
                    member.get("effective_toughness_raw"),
                    f"{member_name}.effective_toughness_raw",
                ),
            )
        )
    return FixedContactArmyInput(
        public_army_id=_positive(row.get("army_id"), f"{name}.army_id"),
        native_army_id=native_army_id,
        encounter_role=str(role),
        coalition_side=coalition,
        scope_role=scope_role,
        owner_character_id=_positive(
            owner_row.get("character_id"), f"{name}.owner.character_id"
        ),
        current_province_id=_positive(
            row.get("current_province_id"), f"{name}.current_province_id"
        ),
        commander=commander,
        regiments=regiments,
        knights=tuple(knights),
    )


def freeze_combat_simulation_input(
    payload_value: object,
    *,
    capture: object | None = None,
) -> FrozenCombatSimulationInput:
    """Freeze a bridge-normalized v2 payload into immutable simulation input."""

    payload = _object(payload_value, "combat_simulation_inputs")
    policy = payload.get("participant_policy")
    if policy != "explicit_hypothetical_fixed_at_contact_no_reinforcements":
        raise CombatInputError("participant_policy is not fixed-contact v2")
    target_id = _positive(
        payload.get("target_province_id"), "combat_simulation_inputs.target_province_id"
    )
    scenario = _object(payload.get("scenario"), "combat_simulation_inputs.scenario")
    if scenario.get("kind") != "explicit_hypothetical_contact":
        raise CombatInputError("scenario kind is not explicit hypothetical contact")
    attackers = _ids(
        scenario.get("attacker_army_ids"), "scenario.attacker_army_ids"
    )
    defenders = _ids(
        scenario.get("defender_army_ids"), "scenario.defender_army_ids"
    )
    if set(attackers) & set(defenders):
        raise CombatInputError("scenario repeats an army across sides")
    attacker_side = scenario.get("attacker_side")
    defender_side = scenario.get("defender_side")
    if {attacker_side, defender_side} != {"player_or_allied", "enemy"}:
        raise CombatInputError("scenario coalition orientation is invalid")
    if scenario.get("actual_route_dependency") is not False:
        raise CombatInputError("fixed-contact scenario unexpectedly depends on route")

    raw_armies = _array(payload.get("armies"), "combat_simulation_inputs.armies")
    armies = tuple(
        _parse_army(item, target_id=target_id, name=f"armies[{index}]")
        for index, item in enumerate(raw_armies)
    )
    public_ids = tuple(army.public_army_id for army in armies)
    if public_ids != attackers + defenders:
        raise CombatInputError("army ordering/partition drifted from scenario")
    for army in armies:
        expected_side = attacker_side if army.encounter_role == "attacker" else defender_side
        if army.coalition_side != expected_side:
            raise CombatInputError("army role and coalition side disagree")

    target = _object(payload.get("target_province"), "target_province")
    _available(target, "target_province")
    if _positive(target.get("province_id"), "target_province.province_id") != target_id:
        raise CombatInputError("target ProvinceID drifted")
    terrain = _object(target.get("terrain"), "target_province.terrain")
    _available(terrain, "target_province.terrain")
    _scale(terrain, "target_province.terrain")
    terrain_key = terrain.get("key")
    if not isinstance(terrain_key, str) or not terrain_key:
        raise CombatInputError("terrain key is invalid")
    crossing = _object(target.get("crossing"), "target_province.crossing")
    _available(crossing, "target_province.crossing")
    crossing_kind = crossing.get("kind")
    if crossing_kind not in {"none", "strait", "river", "large_river"}:
        raise CombatInputError("crossing kind is invalid")
    defender_context = _object(
        target.get("defender_context"), "target_province.defender_context"
    )
    _available(defender_context, "target_province.defender_context")
    if defender_context.get("holding_defender_status") != "available" or not isinstance(
        defender_context.get("holding_defender"), bool
    ):
        raise CombatInputError("holding defender observation is unavailable")
    if defender_context.get("defender_side") != defender_side:
        raise CombatInputError("defender context coalition drifted")
    width = _object(target.get("precontact_width"), "target_province.precontact_width")
    _available(width, "target_province.precontact_width")

    counter_resolutions: list[CounterResolutionInput] = []
    for index, item in enumerate(
        _array(payload.get("counter_resolutions"), "counter_resolutions")
    ):
        name = f"counter_resolutions[{index}]"
        row = _object(item, name)
        _available(row, name)
        _scale(row, name)
        countered_side = row.get("countered_side")
        countering_side = row.get("countering_side")
        if {countered_side, countering_side} != {"player_or_allied", "enemy"}:
            raise CombatInputError(f"{name} side orientation is invalid")
        class_count = _integer(row.get("class_count"), f"{name}.class_count")
        retention = tuple(
            _integer(value, f"{name}.damage_retention_by_class_raw[{item_index}]")
            for item_index, value in enumerate(
                _array(
                    row.get("damage_retention_by_class_raw"),
                    f"{name}.damage_retention_by_class_raw",
                )
            )
        )
        if len(retention) != class_count:
            raise CombatInputError(f"{name} class count disagrees")
        counter_resolutions.append(
            CounterResolutionInput(
                countered_side=str(countered_side),
                countering_side=str(countering_side),
                countered_owner_character_id=_positive(
                    row.get("countered_modifier_owner_character_id"),
                    f"{name}.countered_owner",
                ),
                countering_owner_character_id=_positive(
                    row.get("countering_modifier_owner_character_id"),
                    f"{name}.countering_owner",
                ),
                context_scale_raw=_integer(
                    row.get("context_scale_raw"), f"{name}.context_scale_raw"
                ),
                damage_retention_by_class_raw=retention,
            )
        )
    if tuple(row.countered_side for row in counter_resolutions) != (
        "player_or_allied",
        "enemy",
    ):
        raise CombatInputError("counter resolutions are not in canonical side order")

    completeness = _object(payload.get("completeness"), "completeness")
    input_ready = completeness.get("input_observation_ready")
    monte_carlo_ready = completeness.get("monte_carlo_ready")
    if not isinstance(input_ready, bool) or not isinstance(monte_carlo_ready, bool):
        raise CombatInputError("completeness booleans are malformed")
    if not input_ready:
        raise CombatInputError("combat input observation is not ready")
    missing = tuple(
        item
        for item in _array(
            completeness.get("missing_required_domains"),
            "completeness.missing_required_domains",
        )
        if isinstance(item, str)
    )
    if len(missing) != len(
        _array(
            completeness.get("missing_required_domains"),
            "completeness.missing_required_domains",
        )
    ):
        raise CombatInputError("missing_required_domains contains non-string")

    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    capture_row = _object(capture, "capture") if capture is not None else {}
    snapshot_id = capture_row.get("snapshot_id")
    if snapshot_id is not None and not isinstance(snapshot_id, str):
        raise CombatInputError("capture.snapshot_id must be string/null")

    return FrozenCombatSimulationInput(
        input_sha256=hashlib.sha256(canonical).hexdigest(),
        encounter=FixedContactEncounterInput(
            target_province_id=target_id,
            attacker_entry_province_id=_positive(
                scenario.get("attacker_entry_province_id"),
                "scenario.attacker_entry_province_id",
            ),
            attacker_side=str(attacker_side),
            defender_side=str(defender_side),
            attacker_army_ids=attackers,
            defender_army_ids=defenders,
            participant_policy=str(policy),
            terrain_key=terrain_key,
            terrain_width_multiplier_raw=_integer(
                terrain.get("combat_width_multiplier_raw"),
                "target_province.terrain.combat_width_multiplier_raw",
            ),
            crossing_kind=str(crossing_kind),
            holding_defender=bool(defender_context["holding_defender"]),
            base_width=_positive(width.get("base"), "target_province.width.base"),
            final_width=_positive(width.get("final"), "target_province.width.final"),
        ),
        armies=armies,
        counter_resolutions=tuple(counter_resolutions),
        input_observation_ready=input_ready,
        native_monte_carlo_ready=monte_carlo_ready,
        native_missing_required_domains=missing,
        capture_snapshot_id=snapshot_id,
        capture_revision=(
            _integer(capture_row.get("revision"), "capture.revision")
            if "revision" in capture_row
            else None
        ),
        capture_native_revision=(
            _integer(capture_row.get("native_revision"), "capture.native_revision")
            if "native_revision" in capture_row
            else None
        ),
        capture_date_raw=(
            _integer(capture_row.get("date_raw"), "capture.date_raw")
            if "date_raw" in capture_row
            else None
        ),
    )


def load_live_combat_fixture(path: str | Path) -> FrozenCombatSimulationInput:
    fixture_path = Path(path)
    fixture = _object(
        json.loads(fixture_path.read_text(encoding="utf-8")), "fixture"
    )
    if fixture.get("fixture_kind") != "paused-live-combat-simulation-inputs-v2":
        raise CombatInputError("fixture kind is not paused live combat v2")
    if fixture.get("game_version") != "1.19.0.6" or fixture.get(
        "executable_sha256"
    ) != "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86":
        raise CombatInputError("fixture exact-build provenance mismatch")
    capture = _object(fixture.get("capture"), "fixture.capture")
    if capture.get("status") != "available":
        raise CombatInputError("fixture capture was not available")
    return freeze_combat_simulation_input(
        fixture.get("combat_simulation_inputs"), capture=capture
    )

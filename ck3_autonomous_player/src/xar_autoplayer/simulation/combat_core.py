"""Exact-build CK3 1.19.0.6 combat primitives and research-only MC shell.

Only transitions marked ``static-confirmed`` in the native-AI documentation live
here.  The loaded phase-effect evaluator and battle-end/retreat transitions are
deliberately injected through :class:`BattleTransitionKernel`; until an exact
manifest closes those gates, summaries are never planner-usable.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, IntEnum
import math
from typing import Protocol, TypeVar, runtime_checkable


FIXED_SCALE = 100_000
UINT32_MASK = (1 << 32) - 1
UINT64_MASK = (1 << 64) - 1
INT64_SIGN = 1 << 63
INT64_MODULUS = 1 << 64

_DRAW_STEP = 0x4AD685B3
_DRAW_BASE = 0x5EA6BA9F
_COMMANDER_SEED_STEP = 0xB5297A4D


def trunc_div_toward_zero(numerator: int, denominator: int) -> int:
    """Return signed integer division with x64/C++ truncation semantics."""

    if denominator == 0:
        raise ZeroDivisionError("integer division by zero")
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def fixed_mul(left_raw: int, right_raw: int) -> int:
    """Multiply two signed Q100000 values, truncating each operation."""

    return trunc_div_toward_zero(left_raw * right_raw, FIXED_SCALE)


def fixed_div(numerator_raw: int, denominator_raw: int) -> int:
    """Divide two signed Q100000 values.

    The generic native fixed-point helper writes ``-1`` for a zero denominator.
    Callers whose native branch rejects zero should still reject it before this
    function, rather than treating this sentinel as a valid ratio.
    """

    if denominator_raw == 0:
        return -1
    return trunc_div_toward_zero(numerator_raw * FIXED_SCALE, denominator_raw)


def wrap_int64(value: int) -> int:
    """Wrap an integer exactly as an x64 signed 64-bit result."""

    wrapped = value & UINT64_MASK
    return wrapped - INT64_MODULUS if wrapped & INT64_SIGN else wrapped


def clamp(value: int, lower: int, upper: int) -> int:
    return max(lower, min(upper, value))


class RegimentKind(str, Enum):
    LEVY = "levy"
    MEN_AT_ARMS = "men_at_arms"


@dataclass(frozen=True, slots=True)
class BackingComponent:
    """Integer soldier component backing a combat regiment."""

    maximum_soldiers: int
    current_soldiers: int
    kind: int = 0


@dataclass(frozen=True, slots=True)
class ComponentAllocation:
    components: tuple[BackingComponent, ...]
    whole_soldier_losses: tuple[int, ...]
    requested_hard_raw: int
    unallocated_raw: int

    @property
    def total_whole_soldier_loss(self) -> int:
        return sum(self.whole_soldier_losses)


def _component_selected_count(component: BackingComponent) -> int:
    if component.kind == 3 and component.current_soldiers == 0:
        return component.maximum_soldiers
    return component.current_soldiers


def _component_setter_base(component: BackingComponent) -> int:
    if component.kind == 3 and component.current_soldiers == 0:
        return 0
    return component.current_soldiers


def allocate_hard_casualties_to_components(
    components: tuple[BackingComponent, ...], hard_raw: int
) -> ComponentAllocation:
    """Mirror ``0x239C840`` stored-order component allocation.

    Fractional Q100000 remainder changes the combat entry/ledgers but is not
    backfilled into another integer component.
    """

    mutable = list(components)
    losses = [0 for _ in components]
    original_hard_raw = hard_raw
    remaining_raw = hard_raw

    for index, component in enumerate(tuple(mutable)):
        if remaining_raw <= 0:
            break
        selected_count = _component_selected_count(component)
        if selected_count == 0:
            continue
        cap_raw = selected_count * FIXED_SCALE
        native_product = wrap_int64(selected_count * original_hard_raw)
        candidate_raw = fixed_div(native_product, cap_raw)
        candidate_raw = min(candidate_raw, cap_raw)
        allocated_raw = min(remaining_raw, candidate_raw)
        whole_soldiers = trunc_div_toward_zero(allocated_raw, FIXED_SCALE)
        setter_base = _component_setter_base(component)
        mutable[index] = replace(
            component, current_soldiers=setter_base - whole_soldiers
        )
        losses[index] += whole_soldiers
        remaining_raw -= allocated_raw

    # The native helper enters this pass even when remaining is exactly zero.
    if remaining_raw >= 0:
        for index, component in enumerate(tuple(mutable)):
            if remaining_raw <= 0:
                break
            selected_count = _component_selected_count(component)
            if selected_count == 0:
                continue
            allocated_raw = min(remaining_raw, selected_count * FIXED_SCALE)
            whole_soldiers = trunc_div_toward_zero(allocated_raw, FIXED_SCALE)
            setter_base = _component_setter_base(component)
            mutable[index] = replace(
                component, current_soldiers=setter_base - whole_soldiers
            )
            losses[index] += whole_soldiers
            remaining_raw -= allocated_raw

    return ComponentAllocation(
        components=tuple(mutable),
        whole_soldier_losses=tuple(losses),
        requested_hard_raw=hard_raw,
        unallocated_raw=remaining_raw,
    )


@dataclass(frozen=True, slots=True)
class CombatRegimentState:
    regiment_id: int
    kind: RegimentKind
    current_raw: int
    soft_casualties_raw: int
    toughness_raw: int
    pursuit_raw: int = 0
    screen_raw: int = 0
    components: tuple[BackingComponent, ...] = ()


@dataclass(frozen=True, slots=True)
class MainCasualtyRow:
    regiment_id: int
    total_raw: int
    hard_raw: int
    soft_raw: int
    component_whole_soldier_loss: int


@dataclass(frozen=True, slots=True)
class MainCasualtyResult:
    entries: tuple[CombatRegimentState, ...]
    rows: tuple[MainCasualtyRow, ...]
    conversion_raw: int
    total_hard_raw: int
    total_soft_raw: int


def hard_casualty_conversion_raw(
    *,
    base_conversion_raw: int = 30_000,
    defending_hard_modifier_raw: int = 0,
    attacking_enemy_hard_modifier_raw: int = 0,
    combat_hard_winter_raw: int = 0,
) -> int:
    return fixed_mul(
        base_conversion_raw,
        FIXED_SCALE
        + defending_hard_modifier_raw
        + attacking_enemy_hard_modifier_raw
        + combat_hard_winter_raw,
    )


def apply_main_phase_casualties(
    entries: tuple[CombatRegimentState, ...],
    *,
    incoming_damage_raw: int,
    defending_total_fighting_men_raw: int,
    base_conversion_raw: int = 30_000,
    defending_hard_modifier_raw: int = 0,
    attacking_enemy_hard_modifier_raw: int = 0,
    combat_hard_winter_raw: int = 0,
) -> MainCasualtyResult:
    """Apply one side's frozen outgoing damage to the defending entries."""

    conversion_raw = hard_casualty_conversion_raw(
        base_conversion_raw=base_conversion_raw,
        defending_hard_modifier_raw=defending_hard_modifier_raw,
        attacking_enemy_hard_modifier_raw=attacking_enemy_hard_modifier_raw,
        combat_hard_winter_raw=combat_hard_winter_raw,
    )
    updated: list[CombatRegimentState] = []
    rows: list[MainCasualtyRow] = []

    for entry in entries:
        total_raw = 0
        if entry.current_raw > 0 and defending_total_fighting_men_raw != 0:
            if entry.kind is RegimentKind.LEVY:
                if entry.toughness_raw != 0:
                    share_raw = fixed_div(
                        incoming_damage_raw, defending_total_fighting_men_raw
                    )
                    levy_ratio_raw = fixed_div(share_raw, entry.toughness_raw)
                    total_raw = clamp(
                        fixed_mul(entry.current_raw, levy_ratio_raw),
                        0,
                        entry.current_raw,
                    )
            elif entry.toughness_raw > 0:
                weighted_damage_raw = fixed_mul(
                    entry.current_raw, incoming_damage_raw
                )
                side_share_raw = fixed_div(
                    weighted_damage_raw, defending_total_fighting_men_raw
                )
                total_raw = min(
                    entry.current_raw,
                    fixed_div(side_share_raw, entry.toughness_raw),
                )

        hard_raw = fixed_mul(total_raw, conversion_raw)
        soft_raw = total_raw - hard_raw
        allocation = allocate_hard_casualties_to_components(
            entry.components, hard_raw
        )
        updated_entry = replace(
            entry,
            current_raw=entry.current_raw - soft_raw - hard_raw,
            soft_casualties_raw=entry.soft_casualties_raw + soft_raw,
            components=allocation.components,
        )
        updated.append(updated_entry)
        rows.append(
            MainCasualtyRow(
                regiment_id=entry.regiment_id,
                total_raw=total_raw,
                hard_raw=hard_raw,
                soft_raw=soft_raw,
                component_whole_soldier_loss=allocation.total_whole_soldier_loss,
            )
        )

    return MainCasualtyResult(
        entries=tuple(updated),
        rows=tuple(rows),
        conversion_raw=conversion_raw,
        total_hard_raw=sum(row.hard_raw for row in rows),
        total_soft_raw=sum(row.soft_raw for row in rows),
    )


def allocate_attacker_hard_credit(
    contribution_rows_raw: tuple[int, ...],
    *,
    hard_raw: int,
    incoming_damage_raw: int,
) -> tuple[int, ...]:
    """Mirror per-attribution-row hard credit without remainder refill."""

    if incoming_damage_raw == 0:
        return tuple(0 for _ in contribution_rows_raw)
    return tuple(
        fixed_div(fixed_mul(contribution, hard_raw), incoming_damage_raw)
        for contribution in contribution_rows_raw
    )


def advantage_damage_multiplier_raw(
    resolved_advantage: int, *, scaling_factor: int = 5
) -> int:
    return FIXED_SCALE + abs(resolved_advantage) * scaling_factor * 1_000


def outgoing_damage_raw(
    effective_attack_after_counter_raw: int,
    *,
    advantage_multiplier_raw: int,
    final_combat_width: int,
    side_current_fighting_men_raw: int,
    damage_scaling_raw: int = 3_000,
) -> int:
    """Closed main outgoing-damage envelope, preserving operation order."""

    if side_current_fighting_men_raw <= 0:
        return 0
    width_fraction_raw = min(
        FIXED_SCALE,
        fixed_div(final_combat_width * FIXED_SCALE, side_current_fighting_men_raw),
    )
    result = fixed_mul(effective_attack_after_counter_raw, damage_scaling_raw)
    result = fixed_mul(result, advantage_multiplier_raw)
    return fixed_mul(result, width_fraction_raw)


@dataclass(frozen=True, slots=True)
class PursuitInitialPools:
    levy_soft_raw: int
    men_at_arms_soft_raw: int

    @classmethod
    def from_entries(
        cls, entries: tuple[CombatRegimentState, ...]
    ) -> "PursuitInitialPools":
        return cls(
            levy_soft_raw=sum(
                entry.soft_casualties_raw
                for entry in entries
                if entry.kind is RegimentKind.LEVY
            ),
            men_at_arms_soft_raw=sum(
                entry.soft_casualties_raw
                for entry in entries
                if entry.kind is RegimentKind.MEN_AT_ARMS
            ),
        )


@dataclass(frozen=True, slots=True)
class PursuitDomainBudget:
    kind: RegimentKind
    current_soft_raw: int
    extra_daily_raw: int
    floor_daily_raw: int
    hard_raw: int
    allocation_remainder_raw: int


@dataclass(frozen=True, slots=True)
class PursuitDayResult:
    entries: tuple[CombatRegimentState, ...]
    hard_by_regiment_raw: tuple[tuple[int, int], ...]
    total_hard_raw: int
    toughness_soft_raw: int
    pursuit_damage_raw: int
    screen_raw: int
    base_raw: int
    minimum_raw: int
    extra_raw: int
    floor_component_raw: int
    domains: tuple[PursuitDomainBudget, ...]


@dataclass(frozen=True, slots=True)
class ThreeDayPursuitResult:
    entries: tuple[CombatRegimentState, ...]
    days: tuple[PursuitDayResult, ...]
    total_hard_raw: int


def _pursuit_daily_budget(
    *,
    initial_domain_soft_raw: int,
    component_raw: int,
    toughness_soft_raw: int,
    pursuit_modifier_raw: int,
    pursuit_phase_days: int,
) -> int:
    ratio_raw = fixed_div(component_raw, toughness_soft_raw)
    daily_raw = fixed_mul(initial_domain_soft_raw, ratio_raw)
    daily_raw = fixed_mul(daily_raw, pursuit_modifier_raw)
    return fixed_div(daily_raw, pursuit_phase_days * FIXED_SCALE)


def _apply_pursuit_domain(
    entries: tuple[CombatRegimentState, ...],
    *,
    kind: RegimentKind,
    budget_a_raw: int,
    budget_b_raw: int,
    conversion_raw: int,
) -> tuple[
    tuple[CombatRegimentState, ...],
    dict[int, int],
    int,
    int,
    int,
    int,
]:
    indices = [index for index, entry in enumerate(entries) if entry.kind is kind]
    current_domain_soft_raw = sum(
        entries[index].soft_casualties_raw for index in indices
    )
    if current_domain_soft_raw <= 0:
        return entries, {}, 0, 0, budget_a_raw, budget_b_raw

    total_budget_raw = budget_a_raw + budget_b_raw
    if total_budget_raw > current_domain_soft_raw:
        budget_a_raw = fixed_mul(
            budget_a_raw,
            fixed_div(current_domain_soft_raw, total_budget_raw),
        )
        budget_b_raw = current_domain_soft_raw - budget_a_raw
        total_budget_raw = budget_a_raw + budget_b_raw

    mutable = list(entries)
    hard_by_index: dict[int, int] = {index: 0 for index in indices}
    expected_sum_raw = 0

    for index in indices:
        entry = entries[index]
        if entry.soft_casualties_raw <= 0:
            continue

        def proportional(budget_raw: int) -> int:
            return min(
                entry.soft_casualties_raw,
                fixed_div(
                    fixed_mul(budget_raw, entry.soft_casualties_raw),
                    current_domain_soft_raw,
                ),
            )

        proportional_a_raw = proportional(budget_a_raw)
        proportional_b_raw = proportional(budget_b_raw)
        hard_raw = fixed_mul(proportional_a_raw, conversion_raw) + fixed_mul(
            proportional_b_raw, conversion_raw
        )
        expected_sum_raw += proportional(total_budget_raw)
        allocation = allocate_hard_casualties_to_components(
            entry.components, hard_raw
        )
        mutable[index] = replace(
            entry,
            soft_casualties_raw=entry.soft_casualties_raw - hard_raw,
            components=allocation.components,
        )
        hard_by_index[index] += hard_raw

    remainder_raw = total_budget_raw - expected_sum_raw
    initial_remainder_raw = remainder_raw
    if remainder_raw > 0:
        for index in indices:
            if remainder_raw <= 0:
                break
            entry = mutable[index]
            if entry.soft_casualties_raw <= 0:
                continue
            take_raw = min(remainder_raw, entry.soft_casualties_raw)
            hard_raw = fixed_mul(take_raw, conversion_raw)
            allocation = allocate_hard_casualties_to_components(
                entry.components, hard_raw
            )
            mutable[index] = replace(
                entry,
                soft_casualties_raw=entry.soft_casualties_raw - hard_raw,
                components=allocation.components,
            )
            hard_by_index[index] += hard_raw
            remainder_raw -= take_raw

    return (
        tuple(mutable),
        hard_by_index,
        sum(hard_by_index.values()),
        initial_remainder_raw,
        budget_a_raw,
        budget_b_raw,
    )


def apply_pursuit_day(
    retreater_entries: tuple[CombatRegimentState, ...],
    pursuer_entries: tuple[CombatRegimentState, ...],
    *,
    initial_pools: PursuitInitialPools,
    pursuer_efficiency_modifier_raw: int = 0,
    retreater_loss_modifier_raw: int = 0,
    pursuit_phase_days: int = 3,
    pursuit_conversion_raw: int = FIXED_SCALE,
    pursuit_stat_multiplier_raw: int = 50_000,
    base_toughness_multiplier_raw: int = 5_000,
    minimum_pursuit_multiplier_raw: int = 1_000,
) -> PursuitDayResult:
    """Apply one of the native three pursuit casualty ticks."""

    toughness_soft_raw = sum(
        fixed_mul(entry.toughness_raw, entry.soft_casualties_raw)
        for entry in retreater_entries
    )
    if toughness_soft_raw > 0:
        toughness_soft_raw = max(toughness_soft_raw, FIXED_SCALE)
    if toughness_soft_raw <= 0:
        return PursuitDayResult(
            entries=retreater_entries,
            hard_by_regiment_raw=tuple(
                (entry.regiment_id, 0) for entry in retreater_entries
            ),
            total_hard_raw=0,
            toughness_soft_raw=toughness_soft_raw,
            pursuit_damage_raw=0,
            screen_raw=0,
            base_raw=0,
            minimum_raw=0,
            extra_raw=0,
            floor_component_raw=0,
            domains=(),
        )

    pursuit_stat_sum_raw = sum(
        fixed_mul(entry.pursuit_raw, entry.current_raw)
        for entry in pursuer_entries
    )
    pursuit_damage_raw = fixed_mul(
        pursuit_stat_sum_raw, pursuit_stat_multiplier_raw
    )
    screen_raw = sum(
        fixed_mul(entry.screen_raw, entry.soft_casualties_raw)
        for entry in retreater_entries
    )
    pursuit_modifier_raw = max(
        0,
        FIXED_SCALE
        + pursuer_efficiency_modifier_raw
        + retreater_loss_modifier_raw,
    )
    base_raw = fixed_mul(base_toughness_multiplier_raw, toughness_soft_raw)
    minimum_raw = fixed_mul(
        minimum_pursuit_multiplier_raw, toughness_soft_raw
    )
    proposed_raw = base_raw - screen_raw + pursuit_damage_raw
    extra_raw = max(0, pursuit_damage_raw - screen_raw)
    floor_component_raw = max(
        base_raw if extra_raw > 0 else proposed_raw,
        minimum_raw,
    )

    mutable = retreater_entries
    hard_by_regiment = {entry.regiment_id: 0 for entry in retreater_entries}
    domain_results: list[PursuitDomainBudget] = []
    for kind, initial_soft_raw in (
        (RegimentKind.LEVY, initial_pools.levy_soft_raw),
        (RegimentKind.MEN_AT_ARMS, initial_pools.men_at_arms_soft_raw),
    ):
        current_soft_raw = sum(
            entry.soft_casualties_raw
            for entry in mutable
            if entry.kind is kind
        )
        budget_a_raw = _pursuit_daily_budget(
            initial_domain_soft_raw=initial_soft_raw,
            component_raw=extra_raw,
            toughness_soft_raw=toughness_soft_raw,
            pursuit_modifier_raw=pursuit_modifier_raw,
            pursuit_phase_days=pursuit_phase_days,
        )
        budget_b_raw = _pursuit_daily_budget(
            initial_domain_soft_raw=initial_soft_raw,
            component_raw=floor_component_raw,
            toughness_soft_raw=toughness_soft_raw,
            pursuit_modifier_raw=pursuit_modifier_raw,
            pursuit_phase_days=pursuit_phase_days,
        )
        (
            mutable,
            hard_by_index,
            domain_hard_raw,
            allocation_remainder_raw,
            budget_a_raw,
            budget_b_raw,
        ) = _apply_pursuit_domain(
            mutable,
            kind=kind,
            budget_a_raw=budget_a_raw,
            budget_b_raw=budget_b_raw,
            conversion_raw=pursuit_conversion_raw,
        )
        for index, hard_raw in hard_by_index.items():
            regiment_id = mutable[index].regiment_id
            hard_by_regiment[regiment_id] += hard_raw
        domain_results.append(
            PursuitDomainBudget(
                kind=kind,
                current_soft_raw=current_soft_raw,
                extra_daily_raw=budget_a_raw,
                floor_daily_raw=budget_b_raw,
                hard_raw=domain_hard_raw,
                allocation_remainder_raw=allocation_remainder_raw,
            )
        )

    ordered_hard = tuple(
        (entry.regiment_id, hard_by_regiment[entry.regiment_id])
        for entry in mutable
    )
    return PursuitDayResult(
        entries=mutable,
        hard_by_regiment_raw=ordered_hard,
        total_hard_raw=sum(hard_by_regiment.values()),
        toughness_soft_raw=toughness_soft_raw,
        pursuit_damage_raw=pursuit_damage_raw,
        screen_raw=screen_raw,
        base_raw=base_raw,
        minimum_raw=minimum_raw,
        extra_raw=extra_raw,
        floor_component_raw=floor_component_raw,
        domains=tuple(domain_results),
    )


def apply_three_day_pursuit(
    retreater_entries: tuple[CombatRegimentState, ...],
    pursuer_entries: tuple[CombatRegimentState, ...],
    *,
    initial_pools: PursuitInitialPools | None = None,
    pursuer_efficiency_modifier_raw: int = 0,
    retreater_loss_modifier_raw: int = 0,
) -> ThreeDayPursuitResult:
    """Run the stock day 1/2/3 pursuit ticks with frozen initial soft pools."""

    frozen_pools = initial_pools or PursuitInitialPools.from_entries(
        retreater_entries
    )
    current = retreater_entries
    days: list[PursuitDayResult] = []
    for _ in range(3):
        day = apply_pursuit_day(
            current,
            pursuer_entries,
            initial_pools=frozen_pools,
            pursuer_efficiency_modifier_raw=pursuer_efficiency_modifier_raw,
            retreater_loss_modifier_raw=retreater_loss_modifier_raw,
            pursuit_phase_days=3,
        )
        days.append(day)
        current = day.entries
    return ThreeDayPursuitResult(
        entries=current,
        days=tuple(days),
        total_hard_raw=sum(day.total_hard_raw for day in days),
    )


class CombatPhase(IntEnum):
    MANEUVER = 0
    MAIN = 1
    PURSUIT = 2
    DONE = 3


def winner_at_main_tick_start(
    *,
    forced_side_field: int | None,
    side_0_total_raw: int,
    side_1_total_raw: int,
) -> int | None:
    """Mirror the pre-damage winner checks in ``0x2309E80``.

    The forced field wins first. Native then checks side 0 before side 1 and
    does not repeat these checks after applying that tick's two damage pools.
    Consequently, damage that empties both sides resolves on the next main
    tick as a side-1 victory.
    """

    if forced_side_field not in (None, 0, 1):
        raise ValueError("forced_side_field must be null, 0, or 1")
    if forced_side_field is not None:
        return forced_side_field
    if side_0_total_raw <= 0:
        return 1
    if side_1_total_raw <= 0:
        return 0
    return None


class RetreatBlockReason(str, Enum):
    DISALLOWED = "disallowed"
    MINIMUM_DAYS = "minimum_days"
    PHASE = "phase"
    LANDLESS = "landless"


@dataclass(frozen=True, slots=True)
class RetreatGateInput:
    disallow_retreat: bool
    allow_early_retreat: bool
    elapsed_whole_days: int
    phase: CombatPhase
    landless_blocked: bool
    minimum_days_before_manual_retreat: int = 14


@dataclass(frozen=True, slots=True)
class RetreatGateResult:
    can_retreat: bool
    blocked_by: RetreatBlockReason | None


def evaluate_can_retreat(gate: RetreatGateInput) -> RetreatGateResult:
    """Mirror ``0x2308250`` in its exact short-circuit order."""

    if gate.disallow_retreat:
        return RetreatGateResult(False, RetreatBlockReason.DISALLOWED)
    if (
        not gate.allow_early_retreat
        and gate.elapsed_whole_days <= gate.minimum_days_before_manual_retreat
    ):
        return RetreatGateResult(False, RetreatBlockReason.MINIMUM_DAYS)
    if gate.phase >= CombatPhase.PURSUIT:
        return RetreatGateResult(False, RetreatBlockReason.PHASE)
    if gate.landless_blocked:
        return RetreatGateResult(False, RetreatBlockReason.LANDLESS)
    return RetreatGateResult(True, None)


class BattleEndBranch(str, Enum):
    NON_RETREATING_CLEAR = "non_retreating_clear"
    ENTER_PURSUIT = "enter_pursuit"
    SKIP_PURSUIT = "skip_pursuit"


@dataclass(frozen=True, slots=True)
class BattleEndCoreResult:
    winner_side: int
    loser_side: int
    phase: CombatPhase
    loser_entries: tuple[CombatRegimentState, ...]
    pursuit_initial_pools: PursuitInitialPools | None
    branch: BattleEndBranch
    retreat_gate: RetreatGateResult


def _clear_nonretreating_entries(
    entries: tuple[CombatRegimentState, ...]
) -> tuple[CombatRegimentState, ...]:
    """Mirror the observed entry/component clear; this is not a casualty label."""

    return tuple(
        replace(
            entry,
            current_raw=0,
            soft_casualties_raw=0,
            components=tuple(
                replace(component, current_soldiers=0)
                for component in entry.components
            ),
        )
        for entry in entries
    )


def transition_after_winner_is_known(
    loser_entries: tuple[CombatRegimentState, ...],
    *,
    winner_side: int,
    retreat_gate_input: RetreatGateInput,
    skip_pursuit: bool,
) -> BattleEndCoreResult:
    """Mirror ``0x230A010`` after a main-tick-start or forced winner."""

    if winner_side not in (0, 1):
        raise ValueError("winner_side must be 0 or 1")
    gate = evaluate_can_retreat(retreat_gate_input)
    loser_side = 1 - winner_side
    if not gate.can_retreat:
        return BattleEndCoreResult(
            winner_side=winner_side,
            loser_side=loser_side,
            phase=CombatPhase.DONE,
            loser_entries=_clear_nonretreating_entries(loser_entries),
            pursuit_initial_pools=None,
            branch=BattleEndBranch.NON_RETREATING_CLEAR,
            retreat_gate=gate,
        )

    initial_pools = PursuitInitialPools.from_entries(loser_entries)
    if skip_pursuit:
        return BattleEndCoreResult(
            winner_side=winner_side,
            loser_side=loser_side,
            phase=CombatPhase.DONE,
            loser_entries=loser_entries,
            pursuit_initial_pools=initial_pools,
            branch=BattleEndBranch.SKIP_PURSUIT,
            retreat_gate=gate,
        )
    return BattleEndCoreResult(
        winner_side=winner_side,
        loser_side=loser_side,
        phase=CombatPhase.PURSUIT,
        loser_entries=loser_entries,
        pursuit_initial_pools=initial_pools,
        branch=BattleEndBranch.ENTER_PURSUIT,
        retreat_gate=gate,
    )


def forced_winner_side(*, scoped_side: int, scoped_yes: bool) -> int:
    """Map the force-win field value; only phase 0/1 consumes it as winner."""

    if scoped_side not in (0, 1):
        raise ValueError("scoped_side must be 0 or 1")
    return scoped_side if scoped_yes else 1 - scoped_side


@dataclass(frozen=True, slots=True)
class ForcedWinnerEffectResult:
    forced_side_field: int
    winner_side: int | None
    synchronously_advanced: bool


def apply_forced_winner_effect(
    *,
    phase: CombatPhase,
    current_winner_side: int | None,
    scoped_side: int,
    scoped_yes: bool,
) -> ForcedWinnerEffectResult:
    """Project the phase-sensitive force effect without rewriting pursuit winner."""

    mapped = forced_winner_side(scoped_side=scoped_side, scoped_yes=scoped_yes)
    if current_winner_side not in (None, 0, 1):
        raise ValueError("current_winner_side must be null, 0, or 1")
    if phase in (CombatPhase.MANEUVER, CombatPhase.MAIN):
        return ForcedWinnerEffectResult(mapped, mapped, True)
    # Phase 2 calls the pursuit tick, which consumes the already-recorded +0x6E0.
    if phase is CombatPhase.PURSUIT:
        return ForcedWinnerEffectResult(mapped, current_winner_side, True)
    return ForcedWinnerEffectResult(mapped, current_winner_side, False)


def avalanche32(value: int) -> int:
    """Exact 32-bit avalanche reused by CK3's combat RNG paths."""

    value &= UINT32_MASK
    value ^= value >> 8
    value = (value + 0x68E31DA4) & UINT32_MASK
    value ^= (value << 8) & UINT32_MASK
    value = (value * 0x1B56C4E9) & UINT32_MASK
    value ^= value >> 8
    value = (value * 0x92D68CA2) & UINT32_MASK
    value ^= value >> 8
    return value & UINT32_MASK


@dataclass(frozen=True, slots=True)
class DrawState:
    counter: int
    salt: int

    def __post_init__(self) -> None:
        if not 0 <= self.counter <= UINT32_MASK:
            raise ValueError("counter must be uint32")
        if not 0 <= self.salt <= UINT32_MASK:
            raise ValueError("salt must be uint32")

    def draw31(self) -> tuple[int, "DrawState"]:
        value = (
            self.salt - ((self.counter * _DRAW_STEP) & UINT32_MASK)
        ) & UINT32_MASK
        draw = avalanche32(value) & 0x7FFFFFFF
        return draw, DrawState((self.counter + 1) & UINT32_MASK, self.salt)


@dataclass(frozen=True, slots=True)
class BattleResultEnvelopeSchedule:
    normal_result_generated: bool
    terminal_no_resolution: bool
    winner_envelope_draw: int | None
    loser_envelope_draw: int | None
    state: DrawState


def schedule_battle_result_envelopes(
    state: DrawState, *, teardown: bool
) -> BattleResultEnvelopeSchedule:
    """Mirror normal finalizer W→L draws vs teardown-without-envelopes."""

    if teardown:
        return BattleResultEnvelopeSchedule(
            normal_result_generated=False,
            terminal_no_resolution=True,
            winner_envelope_draw=None,
            loser_envelope_draw=None,
            state=state,
        )
    winner_draw, state = state.draw31()
    loser_draw, state = state.draw31()
    return BattleResultEnvelopeSchedule(
        normal_result_generated=True,
        terminal_no_resolution=False,
        winner_envelope_draw=winner_draw,
        loser_envelope_draw=loser_draw,
        state=state,
    )


def phase_schedule_state(update_seed: int) -> DrawState:
    counter = avalanche32(
        (_DRAW_BASE - ((update_seed & UINT32_MASK) * _DRAW_STEP))
        & UINT32_MASK
    )
    return DrawState(counter=counter, salt=0)


def weighted_choice_index(
    weights: tuple[int, ...], random31: int, *, fallback: int = -1
) -> int:
    """Mirror ``0x3BB6DD0`` positive-weight, binary64 selection."""

    positive_sum = sum(weight for weight in weights if weight > 0)
    if positive_sum == 0:
        return fallback
    target = int(math.ldexp(float(abs(random31)), -31) * float(positive_sum))
    cumulative = 0
    for index, weight in enumerate(weights):
        if weight <= 0:
            continue
        cumulative += weight
        if target < cumulative:
            return index
    # The 31-bit native input makes this unreachable, but preserve fallback.
    return fallback


def phase_event_due(character_id: int, day_index: int, *, cadence: int = 5) -> bool:
    total = ((character_id & UINT32_MASK) + (day_index & UINT32_MASK)) & UINT32_MASK
    return total % cadence == 0


@dataclass(frozen=True, slots=True)
class PhaseEventCandidate:
    key: str
    valid: bool
    int_weight: int
    empty_effect: bool = False


@dataclass(frozen=True, slots=True)
class PhaseEventSelection:
    selected_candidate_key: str | None
    executable_event_key: str | None
    random31: int | None
    state: DrawState
    trigger_valid_count: int


def select_phase_event(
    candidates: tuple[PhaseEventCandidate, ...], state: DrawState
) -> PhaseEventSelection:
    valid = tuple(candidate for candidate in candidates if candidate.valid)
    if not valid:
        return PhaseEventSelection(None, None, None, state, 0)
    random31, next_state = state.draw31()
    selected = weighted_choice_index(
        tuple(candidate.int_weight for candidate in valid),
        random31,
        fallback=-1,
    )
    if selected < 0:
        return PhaseEventSelection(None, None, random31, next_state, len(valid))
    candidate = valid[selected]
    return PhaseEventSelection(
        selected_candidate_key=candidate.key,
        executable_event_key=None if candidate.empty_effect else candidate.key,
        random31=random31,
        state=next_state,
        trigger_valid_count=len(valid),
    )


@dataclass(frozen=True, slots=True)
class FirePhaseEventSeeds:
    base: int
    knight_effect_seeds: tuple[int, ...]
    commander_effect_seed: int | None


def fire_phase_event_seeds(
    global_draw: int,
    *,
    executed_knight_count: int,
    commander_executes: bool,
) -> FirePhaseEventSeeds:
    base = avalanche32(
        (_DRAW_BASE - ((global_draw & UINT32_MASK) * _DRAW_STEP))
        & UINT32_MASK
    )
    knight_seeds = tuple(
        avalanche32(-(((base + ordinal) & UINT32_MASK) * _DRAW_STEP))
        & 0x7FFFFFFF
        for ordinal in range(executed_knight_count)
    )
    commander_seed = None
    if commander_executes:
        commander_seed = (
            avalanche32(
                (((base + executed_knight_count) & UINT32_MASK)
                 * _COMMANDER_SEED_STEP)
                & UINT32_MASK
            )
            & 0x7FFFFFFF
        )
    return FirePhaseEventSeeds(base, knight_seeds, commander_seed)


@dataclass(frozen=True, slots=True)
class CommanderRollRequest:
    draw_enabled: bool
    effective_min: int
    effective_max: int
    previous_roll: int = 0


@dataclass(frozen=True, slots=True)
class MainDayRandomResult:
    side_0_fire_draw: int
    side_1_fire_draw: int
    side_0_roll_draw: int | None
    side_1_roll_draw: int | None
    side_0_roll: int
    side_1_roll: int
    next_roll_cadence: int
    state: DrawState


def _sample_commander_roll(
    request: CommanderRollRequest, state: DrawState
) -> tuple[int, int | None, DrawState]:
    if not request.draw_enabled:
        return request.previous_roll, None, state
    draw, state = state.draw31()
    lower = min(request.effective_min, request.effective_max)
    span = abs(request.effective_max - request.effective_min) + 1
    return lower + (draw % span), draw, state


def schedule_main_day_randomness(
    state: DrawState,
    *,
    roll_cadence: int,
    side_0_roll: CommanderRollRequest,
    side_1_roll: CommanderRollRequest,
) -> MainDayRandomResult:
    """Consume main-day draws in native side0/side1/event/roll order."""

    side_0_fire_draw, state = state.draw31()
    side_1_fire_draw, state = state.draw31()
    side_0_value = side_0_roll.previous_roll
    side_1_value = side_1_roll.previous_roll
    side_0_roll_draw: int | None = None
    side_1_roll_draw: int | None = None
    if roll_cadence == 0:
        side_0_value, side_0_roll_draw, state = _sample_commander_roll(
            side_0_roll, state
        )
        side_1_value, side_1_roll_draw, state = _sample_commander_roll(
            side_1_roll, state
        )
    return MainDayRandomResult(
        side_0_fire_draw=side_0_fire_draw,
        side_1_fire_draw=side_1_fire_draw,
        side_0_roll_draw=side_0_roll_draw,
        side_1_roll_draw=side_1_roll_draw,
        side_0_roll=side_0_value,
        side_1_roll=side_1_value,
        next_roll_cadence=(roll_cadence + 1) % 3,
        state=state,
    )


@dataclass(frozen=True, slots=True)
class TransitionFidelityManifest:
    """Explicit gate for the RE transitions not implemented in this module."""

    simulator_build: str
    loaded_phase_effects_exact: bool
    battle_end_exact: bool
    retreat_and_forced_result_exact: bool
    original_trace_fixture_sha256: str | None
    closed_numeric_domains: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.original_trace_fixture_sha256 is not None:
            if len(self.original_trace_fixture_sha256) != 64:
                raise ValueError("original trace SHA-256 must contain 64 characters")
            try:
                int(self.original_trace_fixture_sha256, 16)
            except ValueError as exc:
                raise ValueError("original trace SHA-256 must be hexadecimal") from exc

    @property
    def fidelity_gate(self) -> bool:
        return (
            self.loaded_phase_effects_exact
            and self.battle_end_exact
            and self.retreat_and_forced_result_exact
            and isinstance(self.original_trace_fixture_sha256, str)
            and len(self.original_trace_fixture_sha256) == 64
        )

    @property
    def missing_required_domains(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.loaded_phase_effects_exact:
            missing.append("loaded_phase_event_effect_transition")
        if not self.battle_end_exact:
            missing.append("battle_end_transition")
        if not self.retreat_and_forced_result_exact:
            missing.append("manual_ai_retreat_and_forced_result")
        if not self.original_trace_fixture_sha256:
            missing.append("exact_build_original_trace_fixture")
        return tuple(missing)


CURRENT_BOUNDED_CORE_MANIFEST = TransitionFidelityManifest(
    simulator_build="ck3-1.19.0.6-bounded-core-v1",
    loaded_phase_effects_exact=False,
    battle_end_exact=True,
    retreat_and_forced_result_exact=True,
    original_trace_fixture_sha256=None,
    closed_numeric_domains=(
        "signed_q100000_fixed_point",
        "main_damage_to_soft_hard_casualties",
        "backing_component_allocation",
        "three_day_pursuit",
        "commander_roll_and_phase_rng_scheduler",
        "battle_end_core_and_result_envelope_order",
        "retreat_skip_pursuit_and_forced_winner",
    ),
)


class TrialResult(str, Enum):
    PLAYER_WIN = "player_win"
    PLAYER_LOSS = "player_loss"
    NO_RESOLUTION = "no_resolution"


@dataclass(frozen=True, slots=True)
class TrialOutcome:
    result: TrialResult
    battle_days: int
    player_hard_loss_raw: int
    enemy_hard_loss_raw: int
    player_stack_wipe: bool = False
    commander_or_knight_death: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.result, TrialResult):
            raise TypeError("result must be TrialResult")
        if self.battle_days < 0:
            raise ValueError("battle_days must be nonnegative")
        if self.player_hard_loss_raw < 0 or self.enemy_hard_loss_raw < 0:
            raise ValueError("hard losses must be nonnegative")


@dataclass(frozen=True, slots=True)
class TrialRandomStreams:
    global_state: DrawState
    phase_schedule_state: DrawState


def _splitmix64(value: int) -> int:
    value = (value + 0x9E3779B97F4A7C15) & UINT64_MASK
    value = ((value ^ (value >> 30)) * 0xBF58476D1CE4E5B9) & UINT64_MASK
    value = ((value ^ (value >> 27)) * 0x94D049BB133111EB) & UINT64_MASK
    return (value ^ (value >> 31)) & UINT64_MASK


def derive_trial_random_streams(seed_u64: int, trial_index: int) -> TrialRandomStreams:
    """Derive independent reproducible states; this is not timeline replay."""

    first = _splitmix64((seed_u64 + trial_index * 2) & UINT64_MASK)
    second = _splitmix64((seed_u64 + trial_index * 2 + 1) & UINT64_MASK)
    return TrialRandomStreams(
        global_state=DrawState(first & UINT32_MASK, first >> 32),
        phase_schedule_state=DrawState(second & UINT32_MASK, second >> 32),
    )


@dataclass(frozen=True, slots=True)
class CombatExperiment:
    input_sha256: str
    seed_u64: int
    sample_count: int
    horizon_days: int

    def __post_init__(self) -> None:
        if len(self.input_sha256) != 64:
            raise ValueError("input_sha256 must contain 64 hexadecimal characters")
        try:
            int(self.input_sha256, 16)
        except ValueError as exc:
            raise ValueError("input_sha256 must be hexadecimal") from exc
        if not 0 <= self.seed_u64 <= UINT64_MASK:
            raise ValueError("seed_u64 must be uint64")
        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive")
        if self.horizon_days <= 0:
            raise ValueError("horizon_days must be positive")


InitialStateT = TypeVar("InitialStateT")


@runtime_checkable
class BattleTransitionKernel(Protocol[InitialStateT]):
    """Future exact transition boundary supplied by the ongoing RE work."""

    @property
    def manifest(self) -> TransitionFidelityManifest: ...

    def simulate_trial(
        self,
        initial_state: InitialStateT,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
    ) -> TrialOutcome: ...


@dataclass(frozen=True, slots=True)
class WilsonInterval:
    lower: float
    upper: float


def wilson_interval_95(successes: int, trials: int) -> WilsonInterval | None:
    if trials <= 0:
        return None
    if successes < 0 or successes > trials:
        raise ValueError("successes must be within trials")
    z = 1.959963984540054
    probability = successes / trials
    z2 = z * z
    denominator = 1.0 + z2 / trials
    center = (probability + z2 / (2.0 * trials)) / denominator
    half = (
        z
        * math.sqrt(
            probability * (1.0 - probability) / trials
            + z2 / (4.0 * trials * trials)
        )
        / denominator
    )
    return WilsonInterval(max(0.0, center - half), min(1.0, center + half))


def _nearest_rank(values: tuple[int, ...], quantile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil(quantile * len(ordered)))
    return ordered[rank - 1]


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    mean: float | None
    p10: int | None
    p50: int | None
    p90: int | None


def summarize_distribution(values: tuple[int, ...]) -> DistributionSummary:
    return DistributionSummary(
        mean=(sum(values) / len(values)) if values else None,
        p10=_nearest_rank(values, 0.10),
        p50=_nearest_rank(values, 0.50),
        p90=_nearest_rank(values, 0.90),
    )


@dataclass(frozen=True, slots=True)
class CombatMonteCarloSummary:
    input_sha256: str
    simulator_build: str
    sampler: str
    seed_u64: int
    sample_count: int
    player_wins: int
    player_losses: int
    no_resolution: int
    player_win_probability_resolved: float | None
    player_win_wilson95: WilsonInterval | None
    battle_days: DistributionSummary
    player_hard_losses_raw: DistributionSummary
    enemy_hard_losses_raw: DistributionSummary
    player_stack_wipe_probability: float
    commander_or_knight_death_probability: float
    fidelity_gate: bool
    planner_usable: bool
    model_fidelity: str
    missing_required_domains: tuple[str, ...]


def summarize_trial_outcomes(
    outcomes: tuple[TrialOutcome, ...],
    *,
    experiment: CombatExperiment,
    manifest: TransitionFidelityManifest,
) -> CombatMonteCarloSummary:
    if len(outcomes) != experiment.sample_count:
        raise ValueError("outcome count must equal experiment.sample_count")
    wins = sum(outcome.result is TrialResult.PLAYER_WIN for outcome in outcomes)
    losses = sum(outcome.result is TrialResult.PLAYER_LOSS for outcome in outcomes)
    no_resolution = sum(
        outcome.result is TrialResult.NO_RESOLUTION for outcome in outcomes
    )
    resolved = wins + losses
    fidelity_gate = manifest.fidelity_gate
    return CombatMonteCarloSummary(
        input_sha256=experiment.input_sha256.lower(),
        simulator_build=manifest.simulator_build,
        sampler="splitmix64-derived-independent-draw31-v1",
        seed_u64=experiment.seed_u64,
        sample_count=experiment.sample_count,
        player_wins=wins,
        player_losses=losses,
        no_resolution=no_resolution,
        player_win_probability_resolved=(wins / resolved) if resolved else None,
        player_win_wilson95=wilson_interval_95(wins, resolved),
        battle_days=summarize_distribution(
            tuple(outcome.battle_days for outcome in outcomes)
        ),
        player_hard_losses_raw=summarize_distribution(
            tuple(outcome.player_hard_loss_raw for outcome in outcomes)
        ),
        enemy_hard_losses_raw=summarize_distribution(
            tuple(outcome.enemy_hard_loss_raw for outcome in outcomes)
        ),
        player_stack_wipe_probability=(
            sum(outcome.player_stack_wipe for outcome in outcomes)
            / experiment.sample_count
        ),
        commander_or_knight_death_probability=(
            sum(outcome.commander_or_knight_death for outcome in outcomes)
            / experiment.sample_count
        ),
        fidelity_gate=fidelity_gate,
        planner_usable=fidelity_gate,
        model_fidelity=(
            "exact-native-parity" if fidelity_gate else "research-only-bounded-core"
        ),
        missing_required_domains=manifest.missing_required_domains,
    )


def run_combat_experiment(
    initial_state: InitialStateT,
    experiment: CombatExperiment,
    kernel: BattleTransitionKernel[InitialStateT],
) -> CombatMonteCarloSummary:
    """Run reproducible independent trials through an explicit transition kernel."""

    outcomes = tuple(
        kernel.simulate_trial(
            initial_state,
            streams=derive_trial_random_streams(experiment.seed_u64, trial_index),
            horizon_days=experiment.horizon_days,
        )
        for trial_index in range(experiment.sample_count)
    )
    return summarize_trial_outcomes(
        outcomes,
        experiment=experiment,
        manifest=kernel.manifest,
    )

"""Explicitly non-planner CK3 combat envelope with phase events disabled."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
import os

from .combat_core import (
    CURRENT_BOUNDED_CORE_MANIFEST,
    BattleTransitionKernel,
    CombatPhase,
    CombatExperiment,
    CombatMonteCarloSummary,
    CombatRegimentState,
    CommanderRollRequest,
    RetreatGateInput,
    TrialOutcome,
    TrialRandomStreams,
    TrialResult,
    TransitionFidelityManifest,
    advantage_damage_multiplier_raw,
    apply_main_phase_casualties,
    apply_three_day_pursuit,
    fixed_mul,
    outgoing_damage_raw,
    schedule_battle_result_envelopes,
    schedule_main_day_randomness,
    transition_after_winner_is_known,
    derive_trial_random_streams,
    summarize_trial_outcomes,
    winner_at_main_tick_start,
)
from .combat_input import (
    CombatInputError,
    FixedContactArmyInput,
    FrozenCombatSimulationInput,
)


_STOCK_DEFENDER_TERRAIN_ADVANTAGE = {
    "hills": 5,
    "terraced_hills": 5,
    "mountains": 12,
    "desert_mountains": 12,
    "jungle": 6,
    "forest": 3,
    "taiga": 4,
    "wetlands": 5,
}
_STOCK_DEFENDER_CROSSING_ADVANTAGE = {
    "none": 0,
    "river": 10,
    "large_river": 20,
    "strait": 30,
}


RESEARCH_ENVELOPE_MANIFEST = TransitionFidelityManifest(
    simulator_build="ck3-1.19.0.6-phase-events-disabled-envelope-v2",
    loaded_phase_effects_exact=False,
    battle_end_exact=True,
    retreat_and_forced_result_exact=True,
    original_trace_fixture_sha256=None,
    closed_numeric_domains=CURRENT_BOUNDED_CORE_MANIFEST.closed_numeric_domains
    + (
        "per_main_tick_dynamic_counter_retention",
        "next_main_tick_winner_check_side0_first",
        "generic_commander_plus_stock_static_advantage_research_assumption",
        "phase_events_disabled_research_assumption",
        "no_voluntary_or_partial_retreat_research_assumption",
    ),
)

ACTIVE_MAIN_RESUME_MANIFEST = TransitionFidelityManifest(
    simulator_build="ck3-1.19.0.6-active-main-resume-research-v1",
    loaded_phase_effects_exact=False,
    battle_end_exact=True,
    retreat_and_forced_result_exact=True,
    original_trace_fixture_sha256=None,
    closed_numeric_domains=RESEARCH_ENVELOPE_MANIFEST.closed_numeric_domains
    + ("observed_main_phase_entry_and_roll_resume",),
)


@dataclass(frozen=True, slots=True)
class ActiveMainResumeState:
    """Declared active-combat input; no current production producer exists.

    ``combat_input`` supplies the static regiment/counter and commander operands.
    Its distinct participant policy and capture fields reject an unmodified
    pre-contact v3 request. Only a future native producer can establish that
    the CombatID, operands, and ordered battle entries truly share one frame.
    """

    combat_input: FrozenCombatSimulationInput
    combat_id: int
    snapshot_id: str
    phase: CombatPhase
    phase_day: int
    elapsed_whole_days: int
    roll_cadence_counter: int
    side_0_roll_points: int
    side_1_roll_points: int
    side_0_non_roll_advantage_points: int
    side_1_non_roll_advantage_points: int
    side_0_commander_character_id: int | None
    side_1_commander_character_id: int | None
    final_combat_width: int
    side_0_entries: tuple[CombatRegimentState, ...]
    side_1_entries: tuple[CombatRegimentState, ...]
    side_0_effective_damage_raw: tuple[tuple[int, int], ...]
    side_1_effective_damage_raw: tuple[tuple[int, int], ...]

    def __post_init__(self) -> None:
        combat_input = self.combat_input
        if type(self.combat_id) is not int or self.combat_id <= 0:
            raise CombatInputError("active combat_id must be a positive integer")
        if (
            combat_input.encounter.participant_policy
            != "observed_active_combat_resume_fixed_future_participants"
        ):
            raise CombatInputError("active resume requires observed participant policy")
        if (
            not self.snapshot_id
            or combat_input.capture_snapshot_id != self.snapshot_id
            or type(combat_input.capture_revision) is not int
            or type(combat_input.capture_native_revision) is not int
            or type(combat_input.capture_date_raw) is not int
            or not combat_input.input_observation_ready
        ):
            raise CombatInputError("active resume requires complete same-frame capture")
        if self.phase is not CombatPhase.MAIN:
            raise CombatInputError("only active main-phase resume is supported")
        if (
            type(self.phase_day) is not int or self.phase_day < 0
            or type(self.elapsed_whole_days) is not int
            or self.elapsed_whole_days < self.phase_day
            or self.elapsed_whole_days < 3
            or type(self.roll_cadence_counter) is not int
            or not 0 <= self.roll_cadence_counter < 3
            or type(self.final_combat_width) is not int
            or self.final_combat_width <= 0
        ):
            raise CombatInputError("active phase, cadence, or width is invalid")
        for value in (
            self.side_0_roll_points, self.side_1_roll_points,
            self.side_0_non_roll_advantage_points,
            self.side_1_non_roll_advantage_points,
        ):
            if type(value) is not int:
                raise CombatInputError("active advantage operands must be integers")
        for side, entries, damages in (
            (combat_input.encounter.attacker_side, self.side_0_entries,
             self.side_0_effective_damage_raw),
            (combat_input.encounter.defender_side, self.side_1_entries,
             self.side_1_effective_damage_raw),
        ):
            regiments = tuple(
                regiment for army in combat_input.armies_for_side(side)
                for regiment in army.regiments
            )
            if not regiments or len(regiments) != len(entries):
                raise CombatInputError("active entry census is incomplete")
            if any(
                regiment.regiment_id != entry.regiment_id
                or regiment.kind is not entry.kind
                or entry.current_raw < 0
                or entry.soft_casualties_raw < 0
                or entry.toughness_raw < 0
                for regiment, entry in zip(regiments, entries, strict=True)
            ):
                raise CombatInputError("active entry identity or state drifted")
            expected_damage_ids = tuple(
                regiment.regiment_id for regiment in regiments
                if regiment.fights_in_main_phase
            )
            if (
                len(damages) != len(expected_damage_ids)
                or tuple(row[0] for row in damages) != expected_damage_ids
                or any(type(row[1]) is not int or row[1] < 0 for row in damages)
            ):
                raise CombatInputError("active effective-damage census drifted")



@dataclass(frozen=True, slots=True)
class ResearchEnvelopeAssumptions:
    attacker_commander_army_id: int
    defender_commander_army_id: int
    phase_events_disabled: bool = True
    no_voluntary_retreat: bool = True
    omit_unobserved_hard_casualty_modifiers: bool = True
    omit_unobserved_pursuit_modifiers: bool = True
    unmodeled_advantage_sources: tuple[str, ...] = (
        "supply_state",
        "debt_tier",
        "recently_disembarked",
        "unreformed_faith",
        "dynamic_combat_effects",
        "dynamic_advantage_helper_0x2307CB0",
        "non_generic_commander_or_owner_contributions",
    )

    def __post_init__(self) -> None:
        if not (
            self.phase_events_disabled
            and self.no_voluntary_retreat
            and self.omit_unobserved_hard_casualty_modifiers
            and self.omit_unobserved_pursuit_modifiers
        ):
            raise ValueError("research envelope v2 assumptions are fixed")


class PhaseEventsDisabledResearchKernel(
    BattleTransitionKernel[FrozenCombatSimulationInput]
):
    """Exercise the numeric pipeline without claiming native model fidelity."""

    manifest = RESEARCH_ENVELOPE_MANIFEST

    def __init__(self, assumptions: ResearchEnvelopeAssumptions) -> None:
        self.assumptions = assumptions

    @staticmethod
    def _army_by_public_id(
        combat_input: FrozenCombatSimulationInput, army_id: int
    ) -> FixedContactArmyInput:
        for army in combat_input.armies:
            if army.public_army_id == army_id:
                return army
        raise CombatInputError(f"commander army {army_id} is outside encounter")

    def _selected_commanders(
        self, combat_input: FrozenCombatSimulationInput
    ) -> tuple[FixedContactArmyInput, FixedContactArmyInput]:
        attacker = self._army_by_public_id(
            combat_input, self.assumptions.attacker_commander_army_id
        )
        defender = self._army_by_public_id(
            combat_input, self.assumptions.defender_commander_army_id
        )
        if attacker.encounter_role != "attacker":
            raise CombatInputError("selected attacker commander army is not attacker")
        if defender.encounter_role != "defender":
            raise CombatInputError("selected defender commander army is not defender")
        return attacker, defender

    @staticmethod
    def _static_defender_advantage(combat_input: FrozenCombatSimulationInput) -> int:
        encounter = combat_input.encounter
        return (
            _STOCK_DEFENDER_TERRAIN_ADVANTAGE.get(encounter.terrain_key, 0)
            + _STOCK_DEFENDER_CROSSING_ADVANTAGE[encounter.crossing_kind]
            + (1 if encounter.holding_defender else 0)
        )

    @staticmethod
    def _outgoing_attack_raw(
        armies: tuple[FixedContactArmyInput, ...],
        entries: tuple[CombatRegimentState, ...],
        retention_by_class_raw: tuple[int, ...],
        effective_damage_raw: tuple[tuple[int, int], ...] | None = None,
    ) -> int:
        regiment_inputs = tuple(
            regiment for army in armies for regiment in army.regiments
        )
        if len(regiment_inputs) != len(entries):
            raise CombatInputError("entry/input census drifted")
        total = 0
        current_damage = dict(effective_damage_raw) if effective_damage_raw is not None else None
        for regiment, entry in zip(regiment_inputs, entries, strict=True):
            if entry.current_raw <= 0 or not regiment.fights_in_main_phase:
                continue
            damage_raw = (
                current_damage[regiment.regiment_id]
                if current_damage is not None else regiment.stats.damage_raw
            )
            if regiment.counter is not None:
                class_index = regiment.counter.class_index
                if not 0 <= class_index < len(retention_by_class_raw):
                    raise CombatInputError("counter class is outside retention vector")
                damage_raw = fixed_mul(
                    damage_raw, retention_by_class_raw[class_index]
                )
            total += fixed_mul(damage_raw, entry.current_raw)
        return total

    def simulate_trial(
        self,
        initial_state: FrozenCombatSimulationInput,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
    ) -> TrialOutcome:
        return self._simulate_trial(
            initial_state, streams=streams, horizon_days=horizon_days, resume=None
        )

    def simulate_resumed_trial(
        self,
        resume: ActiveMainResumeState,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
    ) -> TrialOutcome:
        """Simulate future main ticks only; historical casualties never enter totals."""
        if not isinstance(resume, ActiveMainResumeState):
            raise CombatInputError("active resume requires a typed main-phase state")
        return self._simulate_trial(
            resume.combat_input, streams=streams, horizon_days=horizon_days,
            resume=resume,
        )

    def _simulate_trial(
        self,
        initial_state: FrozenCombatSimulationInput,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
        resume: ActiveMainResumeState | None,
    ) -> TrialOutcome:
        if horizon_days <= 0:
            raise ValueError("horizon_days must be positive")
        attacker_commander_army, defender_commander_army = (
            self._selected_commanders(initial_state)
        )
        if resume is not None and (
            attacker_commander_army.commander.character_id
            != resume.side_0_commander_character_id
            or defender_commander_army.commander.character_id
            != resume.side_1_commander_character_id
        ):
            raise CombatInputError("active selected commander identity drifted")
        attacker_coalition = initial_state.encounter.attacker_side
        defender_coalition = initial_state.encounter.defender_side
        attacker_armies = initial_state.armies_for_side(attacker_coalition)
        defender_armies = initial_state.armies_for_side(defender_coalition)
        attacker_entries = (
            resume.side_0_entries if resume is not None
            else initial_state.initial_entries_for_side(attacker_coalition)
        )
        defender_entries = (
            resume.side_1_entries if resume is not None
            else initial_state.initial_entries_for_side(defender_coalition)
        )
        attacker_generic = (
            attacker_commander_army.commander.generic_advantage_points or 0
        )
        defender_generic = (
            defender_commander_army.commander.generic_advantage_points or 0
        )
        defender_static = self._static_defender_advantage(initial_state)
        attacker_roll = resume.side_0_roll_points if resume is not None else 0
        defender_roll = resume.side_1_roll_points if resume is not None else 0
        roll_cadence = resume.roll_cadence_counter if resume is not None else 0
        global_state = streams.global_state
        attacker_hard_raw = 0
        defender_hard_raw = 0
        maneuver_days = resume.elapsed_whole_days if resume is not None else 3
        main_days = 0
        winner_side_index: int | None = None

        # A pre-contact horizon includes its three maneuver days. A resumed
        # horizon counts only days after the observed active-combat snapshot.
        while (main_days if resume is not None else maneuver_days + main_days) < horizon_days:
            # 0x2309E80 performs these checks at the start of a main tick. It
            # deliberately does not recheck after applying the day's damage.
            main_days += 1
            attacker_total_raw = sum(
                entry.current_raw for entry in attacker_entries
            )
            defender_total_raw = sum(
                entry.current_raw for entry in defender_entries
            )
            winner_side_index = winner_at_main_tick_start(
                forced_side_field=None,
                side_0_total_raw=attacker_total_raw,
                side_1_total_raw=defender_total_raw,
            )
            if winner_side_index is not None:
                break

            random_day = schedule_main_day_randomness(
                global_state,
                roll_cadence=roll_cadence,
                side_0_roll=CommanderRollRequest(
                    attacker_commander_army.commander.character_id is not None,
                    attacker_commander_army.commander.effective_min_roll,
                    attacker_commander_army.commander.effective_max_roll,
                    attacker_roll,
                ),
                side_1_roll=CommanderRollRequest(
                    defender_commander_army.commander.character_id is not None,
                    defender_commander_army.commander.effective_min_roll,
                    defender_commander_army.commander.effective_max_roll,
                    defender_roll,
                ),
            )
            global_state = random_day.state
            roll_cadence = random_day.next_roll_cadence
            attacker_roll = random_day.side_0_roll
            defender_roll = random_day.side_1_roll
            resolved_advantage = (
                resume.side_0_non_roll_advantage_points
                + attacker_roll
                - resume.side_1_non_roll_advantage_points
                - defender_roll
                if resume is not None else
                attacker_generic + attacker_roll
                - defender_generic - defender_roll - defender_static
            )
            attacker_advantage_raw = (
                advantage_damage_multiplier_raw(resolved_advantage)
                if resolved_advantage > 0
                else 100_000
            )
            defender_advantage_raw = (
                advantage_damage_multiplier_raw(resolved_advantage)
                if resolved_advantage < 0
                else 100_000
            )

            attacker_retention = (
                initial_state.dynamic_counter_retention_by_class_raw(
                    attacker_coalition,
                    attacker_entries,
                    defender_entries,
                )
            )
            defender_retention = (
                initial_state.dynamic_counter_retention_by_class_raw(
                    defender_coalition,
                    defender_entries,
                    attacker_entries,
                )
            )
            attacker_attack_raw = self._outgoing_attack_raw(
                attacker_armies, attacker_entries, attacker_retention,
                resume.side_0_effective_damage_raw if resume is not None else None,
            )
            defender_attack_raw = self._outgoing_attack_raw(
                defender_armies, defender_entries, defender_retention,
                resume.side_1_effective_damage_raw if resume is not None else None,
            )
            attacker_damage_raw = outgoing_damage_raw(
                attacker_attack_raw,
                advantage_multiplier_raw=attacker_advantage_raw,
                final_combat_width=(
                    resume.final_combat_width if resume is not None
                    else initial_state.encounter.final_width
                ),
                side_current_fighting_men_raw=attacker_total_raw,
            )
            defender_damage_raw = outgoing_damage_raw(
                defender_attack_raw,
                advantage_multiplier_raw=defender_advantage_raw,
                final_combat_width=(
                    resume.final_combat_width if resume is not None
                    else initial_state.encounter.final_width
                ),
                side_current_fighting_men_raw=defender_total_raw,
            )
            attacker_result = apply_main_phase_casualties(
                attacker_entries,
                incoming_damage_raw=defender_damage_raw,
                defending_total_fighting_men_raw=attacker_total_raw,
            )
            defender_result = apply_main_phase_casualties(
                defender_entries,
                incoming_damage_raw=attacker_damage_raw,
                defending_total_fighting_men_raw=defender_total_raw,
            )
            attacker_entries = attacker_result.entries
            defender_entries = defender_result.entries
            attacker_hard_raw += attacker_result.total_hard_raw
            defender_hard_raw += defender_result.total_hard_raw

        battle_days = maneuver_days + main_days
        if winner_side_index is None:
            return TrialOutcome(
                TrialResult.NO_RESOLUTION,
                battle_days=(main_days if resume is not None else min(battle_days, horizon_days)),
                player_hard_loss_raw=(
                    attacker_hard_raw
                    if attacker_coalition == "player_or_allied"
                    else defender_hard_raw
                ),
                enemy_hard_loss_raw=(
                    defender_hard_raw
                    if attacker_coalition == "player_or_allied"
                    else attacker_hard_raw
                ),
            )

        loser_entries = defender_entries if winner_side_index == 0 else attacker_entries
        winner_entries = attacker_entries if winner_side_index == 0 else defender_entries
        end = transition_after_winner_is_known(
            loser_entries,
            winner_side=winner_side_index,
            retreat_gate_input=RetreatGateInput(
                disallow_retreat=False,
                allow_early_retreat=False,
                elapsed_whole_days=battle_days,
                phase=CombatPhase.MAIN,
                landless_blocked=False,
            ),
            skip_pursuit=False,
        )
        pursuit_hard_raw = 0
        if end.phase is CombatPhase.PURSUIT:
            pursuit = apply_three_day_pursuit(
                end.loser_entries,
                winner_entries,
                initial_pools=end.pursuit_initial_pools,
            )
            pursuit_hard_raw = pursuit.total_hard_raw
            battle_days += 3
        if winner_side_index == 0:
            defender_hard_raw += pursuit_hard_raw
            winning_coalition = attacker_coalition
        else:
            attacker_hard_raw += pursuit_hard_raw
            winning_coalition = defender_coalition

        # Normal finalization consumes winner then loser envelope draws even
        # though this research kernel disables their loaded scripted effects.
        schedule_battle_result_envelopes(global_state, teardown=False)
        player_won = winning_coalition == "player_or_allied"
        player_was_loser = not player_won
        return TrialOutcome(
            TrialResult.PLAYER_WIN if player_won else TrialResult.PLAYER_LOSS,
            battle_days=(battle_days - resume.elapsed_whole_days if resume is not None else battle_days),
            player_hard_loss_raw=(
                attacker_hard_raw
                if attacker_coalition == "player_or_allied"
                else defender_hard_raw
            ),
            enemy_hard_loss_raw=(
                defender_hard_raw
                if attacker_coalition == "player_or_allied"
                else attacker_hard_raw
            ),
            player_stack_wipe=(
                player_was_loser
                and end.branch.value == "non_retreating_clear"
            ),
            commander_or_knight_death=False,
        )


class ActiveMainResumeResearchKernel(BattleTransitionKernel[ActiveMainResumeState]):
    """Research-only continuation kernel with its own visible model identity."""

    manifest = ACTIVE_MAIN_RESUME_MANIFEST

    def __init__(self, assumptions: ResearchEnvelopeAssumptions) -> None:
        self._base = PhaseEventsDisabledResearchKernel(assumptions)

    def simulate_trial(
        self,
        initial_state: ActiveMainResumeState,
        *,
        streams: TrialRandomStreams,
        horizon_days: int,
    ) -> TrialOutcome:
        return self._base.simulate_resumed_trial(
            initial_state, streams=streams, horizon_days=horizon_days
        )


def _simulate_chunk(
    args: tuple[
        FrozenCombatSimulationInput,
        ResearchEnvelopeAssumptions,
        int,
        int,
        int,
        int,
    ]
) -> tuple[tuple[str, int, int, int, bool, bool], ...]:
    combat_input, assumptions, seed_u64, start, stop, horizon_days = args
    kernel = PhaseEventsDisabledResearchKernel(assumptions)
    compact: list[tuple[str, int, int, int, bool, bool]] = []
    for trial_index in range(start, stop):
        outcome = kernel.simulate_trial(
            combat_input,
            streams=derive_trial_random_streams(seed_u64, trial_index),
            horizon_days=horizon_days,
        )
        compact.append(
            (
                outcome.result.value,
                outcome.battle_days,
                outcome.player_hard_loss_raw,
                outcome.enemy_hard_loss_raw,
                outcome.player_stack_wipe,
                outcome.commander_or_knight_death,
            )
        )
    return tuple(compact)


def run_research_envelope_experiment(
    combat_input: FrozenCombatSimulationInput,
    experiment: CombatExperiment,
    assumptions: ResearchEnvelopeAssumptions,
    *,
    max_workers: int | None = None,
    chunks_per_worker: int = 2,
) -> CombatMonteCarloSummary:
    """Run the research envelope in deterministic trial-index chunks."""

    workers = max_workers or min(24, os.cpu_count() or 1)
    workers = max(1, min(workers, experiment.sample_count))
    chunk_count = min(
        experiment.sample_count, max(workers, workers * chunks_per_worker)
    )
    chunk_size = (experiment.sample_count + chunk_count - 1) // chunk_count
    ranges = tuple(
        (start, min(experiment.sample_count, start + chunk_size))
        for start in range(0, experiment.sample_count, chunk_size)
    )
    args = tuple(
        (
            combat_input,
            assumptions,
            experiment.seed_u64,
            start,
            stop,
            experiment.horizon_days,
        )
        for start, stop in ranges
    )
    if workers == 1:
        compact_chunks = tuple(_simulate_chunk(item) for item in args)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            compact_chunks = tuple(pool.map(_simulate_chunk, args))
    outcomes = tuple(
        TrialOutcome(
            result=TrialResult(result),
            battle_days=days,
            player_hard_loss_raw=player_hard,
            enemy_hard_loss_raw=enemy_hard,
            player_stack_wipe=stack_wipe,
            commander_or_knight_death=character_death,
        )
        for chunk in compact_chunks
        for result, days, player_hard, enemy_hard, stack_wipe, character_death in chunk
    )
    return summarize_trial_outcomes(
        outcomes,
        experiment=experiment,
        manifest=RESEARCH_ENVELOPE_MANIFEST,
    )

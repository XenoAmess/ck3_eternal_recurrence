from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest import mock

import pytest

from xar_autoplayer.simulation.combat_core import (
    CombatPhase,
    TrialResult,
    apply_pursuit_day,
    apply_three_day_pursuit,
    derive_trial_random_streams,
)
from xar_autoplayer.simulation.combat_input import (
    CombatInputError,
    load_live_combat_fixture,
)
from xar_autoplayer.simulation.research_envelope import (
    ActiveMainResumeResearchKernel,
    ActiveMainResumeState,
    ActiveRouteSideState,
    ResearchEnvelopeAssumptions,
)


FIXTURE = (
    Path(__file__).parents[1]
    / "fixtures" / "combat" / "live_rev4_player_attacks_357.json"
)


def _research_state() -> tuple[ActiveMainResumeState, ActiveMainResumeResearchKernel]:
    # This is a synthetic interface test based on a frozen pre-contact fixture;
    # it is not evidence that an active-combat native producer exists yet.
    source = load_live_combat_fixture(FIXTURE)
    active = replace(
        source,
        encounter=replace(
            source.encounter,
            participant_policy="observed_active_combat_resume_fixed_future_participants",
        ),
    )
    side_0 = active.encounter.attacker_side
    side_1 = active.encounter.defender_side
    leader_0 = active.armies_for_side(side_0)[0]
    leader_1 = active.armies_for_side(side_1)[0]

    def damage_rows(side: str) -> tuple[tuple[int, int], ...]:
        return tuple(
            (regiment.regiment_id, regiment.stats.damage_raw)
            for army in active.armies_for_side(side)
            for regiment in army.regiments
            if regiment.fights_in_main_phase
        )

    state = ActiveMainResumeState(
        combat_input=active,
        combat_id=16_777_218,
        snapshot_id=active.capture_snapshot_id,
        phase=CombatPhase.MAIN,
        phase_day=2,
        elapsed_whole_days=5,
        roll_cadence_counter=1,
        side_0_roll_points=4,
        side_1_roll_points=7,
        side_0_non_roll_advantage_points=leader_0.commander.generic_advantage_points or 0,
        side_1_non_roll_advantage_points=leader_1.commander.generic_advantage_points or 0,
        side_0_commander_character_id=leader_0.commander.character_id,
        side_1_commander_character_id=leader_1.commander.character_id,
        final_combat_width=active.encounter.final_width,
        side_0_entries=active.initial_entries_for_side(side_0),
        side_1_entries=active.initial_entries_for_side(side_1),
        side_0_effective_damage_raw=damage_rows(side_0),
        side_1_effective_damage_raw=damage_rows(side_1),
        side_0_route=ActiveRouteSideState(
            first_stored_public_cunit_id=leader_0.public_army_id,
            disallow_retreat=False,
            allow_early_retreat=False,
            skip_pursuit=False,
            landless_blocked=False,
            retreat_elapsed_whole_days=5,
            pursuit_efficiency_modifier_raw=0,
            retreat_losses_modifier_raw=0,
        ),
        side_1_route=ActiveRouteSideState(
            first_stored_public_cunit_id=leader_1.public_army_id,
            disallow_retreat=False,
            allow_early_retreat=False,
            skip_pursuit=False,
            landless_blocked=False,
            retreat_elapsed_whole_days=5,
            pursuit_efficiency_modifier_raw=0,
            retreat_losses_modifier_raw=0,
        ),
    )
    kernel = ActiveMainResumeResearchKernel(
        ResearchEnvelopeAssumptions(
            attacker_commander_army_id=leader_0.public_army_id,
            defender_commander_army_id=leader_1.public_army_id,
        )
    )
    return state, kernel


def test_resume_state_rejects_precontact_and_incomplete_active_binding() -> None:
    state, _ = _research_state()
    with pytest.raises(CombatInputError, match="observed participant policy"):
        replace(
            state,
            combat_input=replace(
                state.combat_input,
                encounter=replace(
                    state.combat_input.encounter,
                    participant_policy="explicit_hypothetical_fixed_at_contact_no_reinforcements",
                ),
            ),
        )
    with pytest.raises(CombatInputError, match="same-frame capture"):
        replace(state, snapshot_id="other-snapshot")
    with pytest.raises(CombatInputError, match="same-frame capture"):
        replace(state, combat_input=replace(state.combat_input, capture_native_revision=None))
    with pytest.raises(CombatInputError, match="only active main-phase"):
        replace(state, phase=CombatPhase.PURSUIT)
    with pytest.raises(CombatInputError, match="advantage operands"):
        replace(state, side_0_roll_points=None)
    with pytest.raises(CombatInputError, match="effective-damage census"):
        replace(state, side_0_effective_damage_raw=state.side_0_effective_damage_raw[:-1])
    with pytest.raises(CombatInputError, match="route first-army identity"):
        replace(state, side_0_route=replace(state.side_0_route, first_stored_public_cunit_id=999))
    with pytest.raises(CombatInputError, match="observed booleans"):
        replace(state.side_0_route, skip_pursuit=0)
    with pytest.raises(CombatInputError, match="observed pursuit modifiers"):
        replace(state.side_0_route, retreat_losses_modifier_raw=None)


def test_resume_uses_current_entries_and_counts_future_days_only() -> None:
    state, kernel = _research_state()
    streams = derive_trial_random_streams(871, 0)
    ordinary = kernel.simulate_trial(state, streams=streams, horizon_days=1)
    assert ordinary.result is TrialResult.NO_RESOLUTION
    assert ordinary.battle_days == 1
    assert kernel.manifest.fidelity_gate is False
    assert ordinary.player_hard_loss_raw + ordinary.enemy_hard_loss_raw > 0

    zero_damage = replace(
        state,
        side_0_effective_damage_raw=tuple(
            (regiment_id, 0) for regiment_id, _ in state.side_0_effective_damage_raw
        ),
        side_1_effective_damage_raw=tuple(
            (regiment_id, 0) for regiment_id, _ in state.side_1_effective_damage_raw
        ),
    )
    no_new_losses = kernel.simulate_trial(
        zero_damage, streams=derive_trial_random_streams(871, 0), horizon_days=1
    )
    assert no_new_losses.player_hard_loss_raw == 0
    assert no_new_losses.enemy_hard_loss_raw == 0

    # Native side 0 already emptied at the observed boundary: the next main
    # tick resolves before applying any more main damage. Pre-contact soldiers
    # cannot be reintroduced from the static operand fixture.
    emptied = replace(
        state,
        side_0_entries=tuple(
            replace(entry, current_raw=0) for entry in state.side_0_entries
        ),
    )
    resolved = kernel.simulate_trial(
        emptied, streams=derive_trial_random_streams(871, 0), horizon_days=1
    )
    expected_result = (
        TrialResult.PLAYER_LOSS
        if state.combat_input.encounter.attacker_side == "player_or_allied"
        else TrialResult.PLAYER_WIN
    )
    assert resolved.result is expected_result
    assert resolved.player_hard_loss_raw == 0
    assert resolved.enemy_hard_loss_raw == 0
    assert resolved.battle_days >= 1


def test_resume_does_not_recount_past_soft_wounds_as_new_hard_losses() -> None:
    state, kernel = _research_state()
    wounded = replace(
        state,
        side_0_entries=(
            replace(
                state.side_0_entries[0],
                soft_casualties_raw=state.side_0_entries[0].soft_casualties_raw + 8_000_000,
            ),
            *state.side_0_entries[1:],
        ),
    )
    original = kernel.simulate_trial(
        state, streams=derive_trial_random_streams(42, 0), horizon_days=1
    )
    after_wounds = kernel.simulate_trial(
        wounded, streams=derive_trial_random_streams(42, 0), horizon_days=1
    )
    assert after_wounds == original


def test_resume_uses_loser_route_flags_and_native_day_baseline() -> None:
    state, kernel = _research_state()
    emptied = replace(
        state,
        side_0_entries=tuple(replace(entry, current_raw=0) for entry in state.side_0_entries),
        side_0_route=replace(state.side_0_route, retreat_elapsed_whole_days=14),
    )
    def trial(candidate: ActiveMainResumeState):
        return kernel.simulate_trial(
            candidate, streams=derive_trial_random_streams(871, 0), horizon_days=1
        )

    # The next main tick advances native elapsed days from 14 to 15. Its
    # loser is side 0; changing only the winner-side flags must do nothing.
    ordinary = trial(emptied)
    winner_flag_only = trial(replace(
        emptied, side_1_route=replace(emptied.side_1_route, disallow_retreat=True)
    ))
    assert ordinary == winner_flag_only
    assert ordinary.result is TrialResult.NO_RESOLUTION
    assert ordinary.battle_days == 1
    assert ordinary.player_hard_loss_raw == 0
    assert ordinary.enemy_hard_loss_raw == 0
    route_finished = kernel.simulate_trial(
        emptied, streams=derive_trial_random_streams(871, 0), horizon_days=5
    )
    assert route_finished.result is not TrialResult.NO_RESOLUTION
    assert route_finished.battle_days == 5
    assert route_finished.player_hard_loss_raw == 49_992

    blocked = trial(replace(
        emptied, side_0_route=replace(emptied.side_0_route, disallow_retreat=True)
    ))
    assert blocked.battle_days == 1
    skipped = trial(replace(
        emptied, side_0_route=replace(emptied.side_0_route, skip_pursuit=True)
    ))
    assert skipped.battle_days == 1
    too_early = replace(
        emptied, side_0_route=replace(emptied.side_0_route, retreat_elapsed_whole_days=13)
    )
    assert trial(too_early).battle_days == 1
    early_override = replace(
        too_early, side_0_route=replace(too_early.side_0_route, allow_early_retreat=True)
    )
    assert trial(early_override).result is TrialResult.NO_RESOLUTION


@pytest.mark.parametrize("horizon,partial_ticks,resolved", (
    (1, 0, False), (2, 1, False), (3, 2, False),
    (4, 3, False), (5, 0, True),
))
def test_resume_horizon_waits_for_fourth_pursuit_finalizer_day(
    horizon: int, partial_ticks: int, resolved: bool,
) -> None:
    state, kernel = _research_state()
    losing = (
        replace(state.side_0_entries[0], current_raw=0, soft_casualties_raw=8_000_000),
        *(replace(entry, current_raw=0) for entry in state.side_0_entries[1:]),
    )
    state = replace(
        state, side_0_entries=losing,
        side_0_route=replace(state.side_0_route, retreat_elapsed_whole_days=14),
    )
    with mock.patch(
        "xar_autoplayer.simulation.research_envelope.apply_pursuit_day",
        wraps=apply_pursuit_day,
    ) as partial, mock.patch(
        "xar_autoplayer.simulation.research_envelope.apply_three_day_pursuit",
        wraps=apply_three_day_pursuit,
    ) as full:
        outcome = kernel.simulate_trial(
            state, streams=derive_trial_random_streams(871, 0),
            horizon_days=horizon,
        )
    assert partial.call_count == partial_ticks
    assert full.call_count == int(resolved)
    assert (outcome.result is not TrialResult.NO_RESOLUTION) is resolved
    assert outcome.battle_days == horizon


@pytest.mark.parametrize("loser_side", (0, 1))
def test_resume_routes_observed_winner_and_loser_pursuit_modifiers(loser_side: int) -> None:
    state, kernel = _research_state()
    losing_entries = state.side_0_entries if loser_side == 0 else state.side_1_entries
    losing_entries = (
        replace(losing_entries[0], current_raw=0, soft_casualties_raw=8_000_000),
        *(replace(entry, current_raw=0) for entry in losing_entries[1:]),
    )
    state = replace(
        state,
        side_0_entries=losing_entries if loser_side == 0 else state.side_0_entries,
        side_1_entries=losing_entries if loser_side == 1 else state.side_1_entries,
        side_0_route=replace(
            state.side_0_route,
            retreat_elapsed_whole_days=14,
            retreat_losses_modifier_raw=-25_000 if loser_side == 0 else 7_000,
            pursuit_efficiency_modifier_raw=11_000 if loser_side == 0 else 15_000,
        ),
        side_1_route=replace(
            state.side_1_route,
            retreat_elapsed_whole_days=14,
            retreat_losses_modifier_raw=-25_000 if loser_side == 1 else 9_000,
            pursuit_efficiency_modifier_raw=11_000 if loser_side == 1 else 15_000,
        ),
    )
    with mock.patch(
        "xar_autoplayer.simulation.research_envelope.apply_three_day_pursuit",
        wraps=apply_three_day_pursuit,
    ) as pursuit:
        observed = kernel.simulate_trial(
            state, streams=derive_trial_random_streams(871, 0), horizon_days=5
        )
    assert pursuit.call_count == 1
    assert pursuit.call_args.kwargs["pursuer_efficiency_modifier_raw"] == 15_000
    assert pursuit.call_args.kwargs["retreater_loss_modifier_raw"] == -25_000
    assert observed.player_hard_loss_raw + observed.enemy_hard_loss_raw > 0

    without_observed_loss = replace(
        state,
        side_0_route=replace(state.side_0_route, retreat_losses_modifier_raw=0),
        side_1_route=replace(state.side_1_route, retreat_losses_modifier_raw=0),
    )
    no_modifier = kernel.simulate_trial(
        without_observed_loss,
        streams=derive_trial_random_streams(871, 0),
        horizon_days=5,
    )
    if loser_side == 0:
        assert no_modifier != observed

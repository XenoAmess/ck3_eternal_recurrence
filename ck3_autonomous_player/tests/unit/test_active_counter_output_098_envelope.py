"""Regression for the post-join counter state observed in stock CK3 attempt 098."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import replace
import json
from pathlib import Path
from unittest import mock

from xar_autoplayer.simulation.combat_core import (
    CombatPhase, CombatRegimentState, RegimentKind, derive_trial_random_streams,
)
from xar_autoplayer.simulation.combat_input import (
    CounterResolutionInput, CounterTargetInput, EffectiveRegimentStats,
    FixedContactArmyInput, FixedContactCommanderInput, FixedContactEncounterInput,
    FixedContactRegimentInput, FrozenCombatSimulationInput, RegimentCounterInput,
)
from xar_autoplayer.simulation.research_envelope import (
    ActiveMainResumeResearchKernel, ActiveMainResumeState, ActiveRouteSideState,
    ResearchEnvelopeAssumptions,
)


FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "src/xar_autoplayer/simulation/data/ck3_1_19_0_6_episode01_counter_output_098_projection.json"
)


def _fixture_state() -> tuple[
    dict, FrozenCombatSimulationInput,
    dict[str, tuple[CombatRegimentState, ...]],
    dict[str, tuple[CombatRegimentState, ...]],
    dict[str, tuple[tuple[int, int], ...]],
]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert fixture["source"]["attempt"] == 98
    assert fixture["source"]["exe_sha256"] == (
        "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
    )
    assert fixture["source"]["bridge_sha256"] == (
        "ABEE0A5AD16347A9EA2F10454D111A769CEDB84E343010792619CBB27A4CD858"
    )
    rows = fixture["counter"]["sides"]
    side_name = {0: "enemy", 1: "player_or_allied"}
    armies = []
    before = {}
    joined = {}
    effective_damage = {}
    for side in (0, 1):
        grouped: OrderedDict[int, list[dict]] = OrderedDict()
        for row in rows[side]["entry_mapping"]:
            grouped.setdefault(row["army_id"], []).append(row)
        side_before = []
        side_joined = []
        side_damage = []
        for army_id, entries in grouped.items():
            regiments = []
            for row in entries:
                counter = (
                    RegimentCounterInput(
                        class_index=row["class_index"],
                        current_chunk_raw=0,
                        stack_size_soldiers=row["stack_size_soldiers"],
                        targets=tuple(
                            CounterTargetInput(**target)
                            for target in row["counter_targets"]
                        ),
                    )
                    if row["class_status"] == "available" else None
                )
                regiments.append(FixedContactRegimentInput(
                    regiment_id=row["regiment_id"],
                    kind=RegimentKind.MEN_AT_ARMS,
                    maa_type_key=None,
                    current_soldiers=row["post_join_current_raw"] // 100_000,
                    maximum_soldiers=100,
                    fights_in_main_phase=True,
                    stats=EffectiveRegimentStats(
                        max_size=100, siege_value_raw=0,
                        damage_raw=row["effective_damage_raw"],
                        toughness_raw=row["effective_toughness_raw"],
                        pursuit_raw=0, screen_raw=0,
                    ),
                    counter=counter,
                ))
                side_damage.append((row["regiment_id"], row["effective_damage_raw"]))
                for target, current_raw in (
                    (side_before, row["before_current_raw"] or 0),
                    (side_joined, row["post_join_current_raw"]),
                ):
                    target.append(CombatRegimentState(
                        regiment_id=row["regiment_id"],
                        kind=RegimentKind.MEN_AT_ARMS,
                        current_raw=current_raw,
                        soft_casualties_raw=0,
                        toughness_raw=row["effective_toughness_raw"],
                    ))
            armies.append(FixedContactArmyInput(
                public_army_id=army_id, native_army_id=army_id,
                encounter_role="attacker" if side == 0 else "defender",
                coalition_side=side_name[side], scope_role="included",
                owner_character_id=entries[0]["owner_character_id"],
                current_province_id=2633,
                commander=FixedContactCommanderInput(None, None, 0, 0),
                regiments=tuple(regiments), knights=(),
            ))
        before[side_name[side]] = tuple(side_before)
        joined[side_name[side]] = tuple(side_joined)
        effective_damage[side_name[side]] = tuple(side_damage)
    side_armies = {
        side: tuple(army.public_army_id for army in armies
                    if army.coalition_side == side_name[side])
        for side in (0, 1)
    }
    resolutions = tuple(
        CounterResolutionInput(
            countered_side=side_name[side],
            countering_side=side_name[1 - side],
            countered_owner_character_id=rows[side]["primary_owner_character_id"],
            countering_owner_character_id=rows[1 - side]["primary_owner_character_id"],
            context_scale_raw=rows[side]["context_raw"],
            # Deliberately stale pre-join vector: the dynamic path must ignore it.
            damage_retention_by_class_raw=tuple(rows[side]["before_model_retention_raw"]),
        )
        for side in (1, 0)
    )
    state = FrozenCombatSimulationInput(
        input_sha256="098-test-only-projection",
        encounter=FixedContactEncounterInput(
            target_province_id=2633, attacker_entry_province_id=2633,
            attacker_side="enemy", defender_side="player_or_allied",
            attacker_army_ids=side_armies[0], defender_army_ids=side_armies[1],
            participant_policy="observed_active_combat_resume_fixed_future_participants",
            terrain_key="plains", terrain_width_multiplier_raw=100_000,
            crossing_kind="none", holding_defender=False,
            base_width=2220, final_width=2220,
        ),
        armies=tuple(armies), counter_resolutions=resolutions,
        input_observation_ready=False, native_monte_carlo_ready=False,
        native_missing_required_domains=(
            "active_regiment_counter_class_stack_context",
            "next_day_non_roll_advantage_sources",
            "battle_knight_participation_and_dynamic_entry_transitions",
        ),
    )
    return fixture, state, before, joined, effective_damage


def test_098_joined_entries_replace_stale_player_class_one_retention() -> None:
    fixture, state, before, joined, _ = _fixture_state()
    observed = fixture["counter"]["sides"]
    for side, name, enemy in (
        (0, "enemy", "player_or_allied"),
        (1, "player_or_allied", "enemy"),
    ):
        pre = state.dynamic_counter_retention_by_class_raw(
            name, before[name], before[enemy]
        )
        post_join = state.dynamic_counter_retention_by_class_raw(
            name, joined[name], joined[enemy]
        )
        assert pre == tuple(observed[side]["before_model_retention_raw"])
        assert post_join == tuple(observed[side]["native_retention_raw"])
    assert observed[1]["before_model_retention_raw"][1] == 54_257
    assert observed[1]["native_retention_raw"][1] == 10_000
    assert state.counter_resolutions[0].damage_retention_by_class_raw[1] == 54_257


def test_active_research_kernel_consumes_joined_dynamic_vector() -> None:
    fixture, incomplete, _, joined, damage = _fixture_state()
    # The real 098 receipt is incomplete. This typed state exists only to
    # exercise the research kernel's call path, not to certify a live forecast.
    state = replace(
        incomplete, input_observation_ready=True,
        capture_snapshot_id="synthetic-098-test",
        capture_revision=8, capture_native_revision=7,
        capture_date_raw=fixture["source"]["after_date_raw"],
    )
    side0 = "enemy"
    side1 = "player_or_allied"
    resume = ActiveMainResumeState(
        combat_input=state, combat_id=fixture["source"]["combat_id"],
        snapshot_id="synthetic-098-test", phase=CombatPhase.MAIN,
        phase_day=8, elapsed_whole_days=8, roll_cadence_counter=2,
        side_0_roll_points=0, side_1_roll_points=0,
        side_0_non_roll_advantage_points=0,
        side_1_non_roll_advantage_points=0,
        side_0_commander_character_id=None,
        side_1_commander_character_id=None,
        final_combat_width=2220,
        side_0_entries=joined[side0], side_1_entries=joined[side1],
        side_0_effective_damage_raw=damage[side0],
        side_1_effective_damage_raw=damage[side1],
        side_0_route=ActiveRouteSideState(
            first_stored_public_cunit_id=state.encounter.attacker_army_ids[0],
            disallow_retreat=False, allow_early_retreat=False,
            skip_pursuit=False, landless_blocked=False,
            retreat_elapsed_whole_days=8,
            pursuit_efficiency_modifier_raw=0,
            retreat_losses_modifier_raw=0,
        ),
        side_1_route=ActiveRouteSideState(
            first_stored_public_cunit_id=state.encounter.defender_army_ids[0],
            disallow_retreat=False, allow_early_retreat=False,
            skip_pursuit=False, landless_blocked=False,
            retreat_elapsed_whole_days=8,
            pursuit_efficiency_modifier_raw=0,
            retreat_losses_modifier_raw=0,
        ),
    )
    assumptions = ResearchEnvelopeAssumptions(
        attacker_commander_army_id=state.encounter.attacker_army_ids[0],
        defender_commander_army_id=state.encounter.defender_army_ids[0],
    )
    observed_calls = {}
    original = FrozenCombatSimulationInput.dynamic_counter_retention_by_class_raw

    def capture(self, side, current, opponent):
        result = original(self, side, current, opponent)
        observed_calls[side] = result
        return result

    with mock.patch.object(
        FrozenCombatSimulationInput,
        "dynamic_counter_retention_by_class_raw",
        capture,
    ):
        ActiveMainResumeResearchKernel(assumptions).simulate_trial(
            resume, streams=derive_trial_random_streams(98, 0), horizon_days=1,
        )
    assert observed_calls[side0] == tuple(fixture["counter"]["sides"][0]["native_retention_raw"])
    assert observed_calls[side1] == tuple(fixture["counter"]["sides"][1]["native_retention_raw"])
    assert observed_calls[side1][1] == 10_000

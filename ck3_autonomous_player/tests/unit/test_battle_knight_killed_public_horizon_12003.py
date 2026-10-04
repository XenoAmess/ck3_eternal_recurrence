"""One source-closed knight_killed request fixture through the public horizon.

The enemy satisfies the prowess filter but is dead. Growth precedes the failed
bothalive guard; root accolade tail still runs. Requests do not commit writes.
This fixture does not cover the allalive death branch or native callbacks.
"""
from __future__ import annotations

import dataclasses
import unittest
from copy import deepcopy

from xar_autoplayer.simulation import battle_phase_events_12003 as pe
from xar_autoplayer.simulation import battle_phase_event_feedback_12003 as fb
from xar_autoplayer.simulation.combat_core import DrawState
from test_battle_current_conditional_horizon import _initial_condition, _day, DATE

Q, ROOT, ENEMY, ACCOLADE = 100000, 29829, 900001, 771337


def require(value, label):
    if not value:
        raise AssertionError(label)


def bm():
    return {'education_martial': [False] * 5, 'education_martial_prowess': [False] * 4,
            'intellect_good': [False] * 3, 'lifestyle_blademaster': False,
            'lifestyle_blademaster_xp_raw': 0, 'shrewd': False, 'physique_good': False,
            'culture_blademaster_traits_more_common': False}



class KnightKilledPublicHorizonFixtureTests(unittest.TestCase):
    def test_guard_false_growth_and_root_tail_are_requests_only(self):
        manifest = pe.load_stock_phase_events_12003()
        initial = _initial_condition(damage_scaling=25000)
        day = dataclasses.replace(_day(0), phase_events=({'event_key': 'knight_killed'},))
        native = {
            'root.exists': True, 'root.alive': True, 'root.skills.prowess_raw': 12 * Q,
            'root.traits.wounded.rank_raw': 0, 'root.traits.fragile_bones.rank_raw': 0,
            'root.traits.fragile_bones.xp_raw': 0, 'root.traits.one_legged': False,
            'root.traits.disfigured': False, 'root.traits.one_eyed': False,
            'root.traits.maimed': False, 'root.court_positions.garuda': False,
            'root.traits_and_culture_for_blademaster': bm(),
            'combat_side.character_membership': [ROOT, 900002],
            'enemy_side.character_membership': [ENEMY],
            'combat_side.ordered_enemy_knights': [ENEMY], 'combat_side.commander': ROOT,
            'derived.root_hold_court_8050_promise_matches': False,
            'root.primary_title.exists': False, 'root.is_lowborn': False,
            'root.is_acclaimed': True, 'root.accolade_id': ACCOLADE,
            'root.liege.exists': False, 'root.house.exists': False,
            'enemy_side.primary_participant_character_id': 36109,
            'combat_side.primary_participant_character_id': ROOT, 'combat.location': 2586,
        }
        enemy_refs = {
            'selected_enemy_knight.alive': False, 'selected_enemy_knight.skills.prowess_raw': 20 * Q,
            'selected_enemy_knight.skills.learning_raw': 10 * Q,
            'selected_enemy_knight.dynasty.perks.warfare_legacy_3': False,
            'selected_enemy_knight.traits_and_culture_for_blademaster': bm(),
            'selected_enemy_knight.is_acclaimed': False, 'selected_enemy_knight.liege.exists': False,
            'selected_enemy_knight.rite.killing_bestows_heads': False,
            'selected_enemy_knight.personal_tenet.killing_bestows_heads': False,
        }
        context = {'root_character_id': ROOT, 'root_source_army_id': 101, 'root_source_regiment_id': 81,
            'phase_roles': ['knight'], 'combat_side_index': 0, 'enemy_side_index': 1,
            'native_state_refs': native, 'offline_state_refs': {}, 'candidate_rows': [{
                'character_id': ENEMY, 'candidate_refs': {'candidate.alive': False,
                    'candidate.skills.prowess_raw': 20 * Q}, 'selected_enemy_knight_refs': enemy_refs}]}
        source = {'combat_id': initial.combat_id, 'snapshot_revision': initial.snapshot_revision,
            'observed_date_raw': initial.observed_date_raw, 'modeled_dispatch_date_raw': DATE + 24,
            'modeled_phase_day': initial.phase_day + 1,
            'provenance': 'synthetic_caller_condition_not_an_actual_game_sample'}
        tape = (pe.PhaseEventScriptOutcome12003('knight_killed:enemy_knight', character_id=ENEMY),
                pe.PhaseEventScriptOutcome12003('knight_increase_prowess:source_order', branch_index=2))
        selected = (fb.SelectedPhaseEventInput12003(context=context, event_key='knight_killed',
            script_outcomes=tape, source_context=source, manifest=manifest),)
        context_before = deepcopy(context)
        draw = DrawState(13, 17)
        result = fb.run_selected_phase_feedback_horizon_12003(initial, day=day, selected=selected,
            draw_state=draw, caller_seed_provenance={'kind': 'synthetic_caller_seed', 'native_rng_observed': False})
        require(result.feedback is not None and result.event_tape_consumed, 'one accepted main boundary consumes selected tape')
        f, h = result.feedback, result.horizon
        require(h.status == 'partial' and h.stop_reason == 'selected_phase_event_feedback_pending', 'public horizon stops at pending selected feedback')
        require(h.modeled_accepted_invocations == 1 and h.modeled_date_raw == DATE + 24, 'one modeled accepted calendar invocation advances exactly one modeled date')
        require(h.trace[0]['stages'] == ['calendar', 'main_pre_event_exit_check', 'selected_phase_feedback'], 'stop occurs before commander roll and main damage stages')
        require(h.final_state.simulated_main_ticks == 0 and h.final_state.draw_state == draw, 'no main damage tick or commander draw consumed')
        require(h.final_state.condition.sides == initial.sides, 'all Entry, backing, ordered armies and owner hard ledgers unchanged')
        require(h.final_state.condition.source_snapshot == initial.source_snapshot and
                h.final_state.condition.snapshot_revision == initial.snapshot_revision and
                h.final_state.condition.observed_date_raw == initial.observed_date_raw,
                'original source snapshot coordinate retained')
        require(h.final_state.condition.phase_day == initial.phase_day + 1, 'only modeled calendar phase-day update carried')
        require(not f.feedback_ready and not result.ledger['phase_events_cleared'], 'pending callbacks prevent clearing phase events')
        require(not f.character_numeric_deltas and not f.cached_stat_refreshes, 'request-only effects produce no character numeric or cached-stat writeback')
        require(context == context_before, 'caller context remains unchanged')
        e = f.executions[0]
        require(e is not None and e['event']['global_load_index'] == 11 and e['event']['type_load_index'] == 7, 'current source-selected knight_killed indices retained')
        requests = e['effect_requests']
        require([r['operation'] for r in requests] == ['set_variable', 'set_variable', 'set_variable', 'add_prestige', 'add_trait', 'add_glory'], 'source order preserves variables, reward, growth, then root accolade tail')
        require(requests[4]['target_character_id'] == ENEMY and requests[4]['payload']['trait'] == 'lifestyle_blademaster', 'eligible dead enemy still receives pre-guard trait request')
        require(requests[5]['target_scope'] == 'root.accolade' and requests[5]['payload']['accolade_id'] == ACCOLADE and requests[5]['payload']['value_raw'] == 25 * Q, 'root accolade tail survives failed bothalive guard')
        require(not any(r['operation'] in {'death', 'battle_event', 'add_to_variable_list'} for r in requests), 'failed bothalive guard has no death, slain record or no-enemy fallback')
        require(all(r['stage'] == 'requested' and r['committed'] is False and r['queue_admission_observed'] is False and r['native_callback_admission_observed'] is False for r in requests), 'selected requests are neither queued native callbacks nor committed writes')
        require(e['requested_effects_committed'] is False and e['native_queue_admission_observed'] is False, 'execution admission and commitment flags remain false')
        require(len(f.ledger['effect_requests']) == len(requests) and
                all(r['selected_index'] == 0 for r in f.ledger['effect_requests']), 'public feedback ledger forwards the ordered request list')
        after = e['after_state']
        require(after['selected_enemy_character_id'] == ENEMY, 'prowess-only enemy selection admits alive-false candidate')
        require(after['root']['alive'] is True and after['root']['prowess_raw'] == 12 * Q and after['root']['variable_updates'] == {}, 'root living, prowess and committed variables unchanged')
        require(after['enemy_candidates'][0]['alive'] is False and after['enemy_candidates'][0]['prowess_raw'] == 20 * Q and
                after['enemy_candidates'][0]['lifestyle_blademaster'] is False and after['enemy_candidates'][0]['in_enemy_membership'] is True,
                'enemy current life, prowess, trait and roster retained despite trait request')
        require(after['sides']['enemy_membership'] == [ENEMY] and after['sides']['combat_membership'] == [ROOT, 900002], 'selected requests retain both rosters')
        require(all(not after['recompute'][key] for key in ('character_stat_ids', 'participant_detach_ids', 'side_strength_indices')) and
                after['recompute']['advantage']['recompute_required'] is False, 'no committed detach, side-strength or stat refresh requested')
        require(e['script_outcomes']['provided_count'] == 2 and e['script_outcomes']['consumed_count'] == 2 and
                e['script_outcomes']['native_rng_trace_claimed'] is False, 'two caller script choices consumed without native RNG claim')
        require(e['data_provenance']['knight_killed_source_api_sha256'] == '8120F8760091DE225CACF0FED2EFBEC0AB0A09E111EF823CC139FBD62FBE4FA7', 'execution binds signed full-source API')
        require(not e['full_script_feedback_ready'] and not e['planner_usable'] and not h.complete_native_transition and
                not h.complete_monte_carlo and h.actual_game_days_advanced == 0 and f.actual_game_days_advanced == 0,
                'focused request visibility does not claim complete or live battle simulation')


if __name__ == "__main__":
    unittest.main()

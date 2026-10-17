"""Completed actual130 prediction and actual170 combat observation, date only.

FULL149 is their subsequent successful batch summary, not an AUTO DTO. Native
strict followup fixtures remain separately labelled synthetic in the archive.
"""
import copy
import importlib.util
import json
from pathlib import Path

import pytest

from tools.g2_saved_campaign.route_contact_exact_day_outcome import (
    classify_route_contact_horizon_one_day_v1,
)

FIXTURES = Path(__file__).with_name('fixtures')
spec = importlib.util.spec_from_file_location('reviewed_start_binding',
    FIXTURES / 'reviewed_gameplay_start_binding_v1.py')
binder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binder)


def actual(sequence=170):
    return json.loads((FIXTURES / f'route_unavoidable_actual{sequence}.json').read_bytes())


def classify(fixture):
    return classify_route_contact_horizon_one_day_v1(fixture['body'],
        initial_frame=fixture['initial_frame'], game_pid=fixture['game_pid'],
        bind_gameplay_frame=binder.classify_gameplay_start_binding_v1)


@pytest.mark.parametrize('sequence,status', [(130, 'predicted_only'), (170, 'observed')])
def test_actual_transition_keeps_only_exact_day_credit(sequence, status):
    fixture = actual(sequence)
    unchanged = copy.deepcopy(fixture)
    credit = classify(fixture)
    assert fixture == unchanged
    assert credit['actual_date_delta_raw'] == 24
    assert credit['paired_after_metrics_still_required'] is True
    assert credit['contact_free_claimed'] is False
    assert credit['unavoidable_contact_transition']['status'] == status
    for key in ('action_credit', 'primitive_accepted', 'ui_action_credit',
                'material_verified', 'business_success_inferred', 'replay_allowed'):
        assert credit[key] is False


def transition(f): return f['body']['result']['contact_transition']
def inner(f): return f['body']['result']
def horizon(f): return f['body']['plan']['route_audit']['contact_horizon']


MUTATIONS = {
    'wrong_phase': lambda f: f['body']['plan'].update(phase='unqualified_contact'),
    'wrong_policy': lambda f: inner(f).update(timeline_policy='exact_one_day_contact_free_speed_3'),
    'wrong_speed': lambda f: inner(f).update(timeline_speed=3),
    'unpaused': lambda f: inner(f).update(paused=False),
    'missing_horizon': lambda f: f['body']['plan']['route_audit'].update(contact_horizon=None),
    'fake_contact_free': lambda f: horizon(f).update(one_day_contact_free=True),
    'missing_conflicts': lambda f: horizon(f).update(conflicts=[]),
    'wrong_native': lambda f: horizon(f).update(snapshot_revision=1),
    'unknown_transition': lambda f: transition(f).update(status='success'),
    'fake_victory': lambda f: transition(f).update(postcondition='battle_won'),
    'wrong_subject': lambda f: transition(f).update(subject_army_id=1),
    'wrong_end': lambda f: transition(f).update(ending_date_raw=1),
    'unknown_proof': lambda f: transition(f).update(proof_kind='assumed_contact'),
    'failed_strict_followup': lambda f: inner(f).update(contact_followup={'error': 'synthetic failure'}),
    'unobserved_combat': lambda f: inner(f)['war_progress_after']['wars'][0]['player_armies'][0].update(
        in_combat=False, army_state='regular', army_state_code=1),
    'clock_overshoot': lambda f: inner(f)['exact_day_native_clock']['stopped'].update(overshoot_days=1),
    'wrong_Game': lambda f: f['body']['planning_source_frame'].update(bridge_pid=1),
    'wrong_actor': lambda f: f['body']['planning_source_frame'].update(actor_character_id=1),
}


@pytest.mark.parametrize('name', sorted(MUTATIONS))
def test_actual_observed_contract_negatives(name):
    fixture = actual()
    MUTATIONS[name](fixture)
    with pytest.raises(ValueError):
        classify(fixture)


def test_prediction_requires_independent_refresh_and_never_infers_combat():
    fixture = actual(130)
    assert transition(fixture)['contact_observed'] is False
    inner(fixture).pop('contact_refresh')
    with pytest.raises(ValueError):
        classify(fixture)

"""Actual P09 no-op plus bounded negative/service checks; no Game access."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from xar_autoplayer.bridge import family_wartime_opportunity_cadence_v1 as cadence
from xar_autoplayer.bridge import service
from xar_autoplayer.bridge import current_first_heir_relationship_private_transport as transport

ACTUAL = json.loads((Path(__file__).resolve().parents[1] / 'fixtures' /
                     'family_wartime_noop_0210.json').read_text(encoding='utf-8'))
HEIR = 39979


def review(day=0, sequence=0, *, source_status='reviewed'):
    frame = copy.deepcopy(ACTUAL['frame'])
    plan = copy.deepcopy(ACTUAL['plan'])
    outcome = copy.deepcopy(ACTUAL['outcome'])
    frame['date_raw'] += day * 24
    frame['native_revision'] += sequence
    relation = plan['family_marriage_current_relationship']
    diagnostic = plan['family_marriage_private_diagnostic']
    relation['native_revision'] = frame['native_revision']
    relation['root_query_sequence'] += sequence
    diagnostic['date_raw'] = frame['date_raw']
    diagnostic['native_revision'] = frame['native_revision']
    diagnostic['legality_query_sequence'] += sequence
    source = {'status': source_status, 'date_raw': frame['date_raw'],
              'native_revision': frame['native_revision'],
              'actor_character_id': frame['actor_character_id'],
              'episode_run_id': frame['episode_run_id'],
              'heir_character_id': HEIR,
              'player_spouse_signature': [None, 30887, [30887]],
              'expected_successor_character_id': HEIR}
    plan['_family_wartime_review_v1'] = source
    return frame, plan, outcome


def active_after_two(tmp_path):
    frame, plan, outcome = review()
    first = cadence.observe_after_turn(tmp_path, frame, plan, outcome)
    assert first['status'] == 'inactive' and first['consecutive_noop_dates'] == 1
    assert cadence.observe_after_turn(tmp_path, frame, plan, outcome)['consecutive_noop_dates'] == 1
    later, plan2, outcome2 = review(day=1, sequence=1)
    second = cadence.observe_after_turn(tmp_path, later, plan2, outcome2)
    assert second['status'] == 'active' and second['remaining_days'] == 30
    return later, second


def test_actual_noop_two_distinct_dates_then_exact_30_day_expiry(tmp_path):
    frame, active = active_after_two(tmp_path)
    until = active['cooldown_until_date_raw']
    assert cadence.view(tmp_path, {**frame, 'connection_generation': 999})['status'] == 'active'
    assert cadence.view(tmp_path, {**frame, 'date_raw': until - 24})['status'] == 'active'
    assert cadence.view(tmp_path, {**frame, 'date_raw': until})['status'] == 'inactive'
    assert cadence.view(tmp_path, {**frame, 'actor_character_id': 1})['status'] == 'inactive'


@pytest.mark.parametrize('mutation', [
    lambda f,p,o: p['family_marriage_current_relationship'].update(status='unavailable'),
    lambda f,p,o: p['family_marriage_private_diagnostic'].update(selected_candidate_character_id=39969),
    lambda f,p,o: p['family_marriage_private_diagnostic']['rows'][0].update(rejection_reasons=[]),
    lambda f,p,o: p['_family_wartime_review_v1'].update(expected_successor_character_id=1),
    lambda f,p,o: o.update(status='pending'),
    lambda f,p,o: o['result'].update(accepted=False),
    lambda f,p,o: o.update(selected_step='declare-war-1'),
])
def test_unknown_or_business_unverified_never_counts(tmp_path, mutation):
    frame, plan, outcome = review()
    mutation(frame, plan, outcome)
    receipt = cadence.observe_after_turn(tmp_path, frame, plan, outcome)
    assert receipt['consecutive_noop_dates'] == 0
    assert receipt['status'] == 'inactive'


def test_unknown_complete_round_breaks_consecutive_noop(tmp_path):
    frame, plan, outcome = review()
    cadence.observe_after_turn(tmp_path, frame, plan, outcome)
    unknown, plan2, outcome2 = review(day=1, sequence=1, source_status='unknown')
    assert cadence.observe_after_turn(tmp_path, unknown, plan2, outcome2)['consecutive_noop_dates'] == 0
    third, plan3, outcome3 = review(day=2, sequence=2)
    assert cadence.observe_after_turn(tmp_path, third, plan3, outcome3)['consecutive_noop_dates'] == 1


def test_actual_family_material_resets_cd(tmp_path):
    frame, _ = active_after_two(tmp_path)
    material = {'status': 'executed', 'selected_step':
                'query-observed-first-heir-marriage-result-v1-private',
                'result': {'status': 'marriage', 'material_result': True}}
    receipt = cadence.observe_after_turn(tmp_path, frame, {}, material)
    assert receipt['status'] == 'inactive'


def _snapshot(frame, *, heir=HEIR):
    return {'snapshot_id': frame['snapshot_id'], 'revision': frame['revision'],
            'native_revision': frame['native_revision'], 'date_raw': frame['date_raw'],
            'episode_run_id': frame['episode_run_id'], 'paused': True, 'map_ready': True,
            'played_character': {'character_id': frame['actor_character_id'],
                                 'alive': True, 'betrothed_id': None,
                                 'primary_spouse_id': 30887, 'spouse_ids': [30887]},
            'active_wars': [{'war_id': 1}], 'active_event': None,
            'pending_character_interaction': None, 'one_life_terminal_reason': None,
            'succession_lifecycle': {'lifecycle': 'ordinary_campaign_succession'},
            'succession_expectation': {'status': 'available',
                                       'expected_successor_character_id': heir}}


def test_service_skips_only_when_fresh_heir_same_and_no_pending(tmp_path, monkeypatch):
    frame, _ = active_after_two(tmp_path)
    snapshot = _snapshot(frame)
    reads = []
    def relation(driver, *, expected_native_revision):
        reads.append(expected_native_revision)
        return {'status': 'available', 'read_only': True,
                'bilateral_verified': True, 'native_revision': expected_native_revision,
                'heir_character_id': HEIR, 'betrothed_character_id': None,
                'primary_spouse_character_id': None, 'spouse_character_ids': []}
    monkeypatch.setattr(transport, 'query_current_first_heir_relationship_private_v1', relation)
    driver = SimpleNamespace(allow_private_current_first_heir_relationship_query=True,
                             take_internal_semantic_snapshot=lambda: snapshot,
                             _with_internal_planning_view=lambda *_: {'pending': None})
    fake = SimpleNamespace(driver=driver,
                           _strategy_state_dir=lambda: tmp_path,
                           _observed_planning_source_frame=lambda _: frame,
                           _unresolved_family_child_focus_v1=lambda *_: {'pending': None})
    monkeypatch.setattr(service, 'read_family_marriage_ledger',
                        lambda _: {'pending': None, 'resolved': None})
    planned = {'plan': {'selected_step': 'query-army-strengths-v1'}}
    skip = service.GameplayBridgeService._skip_private_family_wartime_during_cooldown_v1
    result = skip(fake, planned, snapshot)
    assert result['plan']['selected_step'] == 'query-army-strengths-v1'
    assert result['plan']['family_wartime_opportunity_cooldown_v1']['status'] == 'active'
    assert reads == [frame['native_revision']]
    snapshot['pending_character_interaction'] = {'instance_id': 3}
    assert skip(fake, planned, snapshot) is None
    assert reads == [frame['native_revision']]
    snapshot['pending_character_interaction'] = None
    monkeypatch.setattr(service, 'read_family_marriage_ledger',
                        lambda _: {'pending': {'request_id': 'prior'}, 'resolved': None})
    assert skip(fake, planned, snapshot) is None
    assert reads == [frame['native_revision']]


def test_prior_heir_resolved_is_evidence_not_current_pending(tmp_path, monkeypatch):
    frame, _ = active_after_two(tmp_path)
    snapshot = _snapshot(frame)
    monkeypatch.setattr(service, 'read_family_marriage_ledger', lambda _: {
        'pending': None,
        'resolved': {'episode_run_id': frame['episode_run_id'],
                     'heir_character_id': 40695,
                     'status': 'marriage', 'material_result': True}})
    calls = []
    monkeypatch.setattr(transport, 'query_current_first_heir_relationship_private_v1',
                        lambda driver, *, expected_native_revision: calls.append(1) or {
                            'status': 'available', 'read_only': True,
                            'bilateral_verified': True,
                            'native_revision': expected_native_revision,
                            'heir_character_id': HEIR,
                            'betrothed_character_id': None,
                            'primary_spouse_character_id': None,
                            'spouse_character_ids': []})
    driver = SimpleNamespace(allow_private_current_first_heir_relationship_query=True,
                             take_internal_semantic_snapshot=lambda: snapshot,
                             _with_internal_planning_view=lambda *_: {'pending': None})
    fake = SimpleNamespace(driver=driver, _strategy_state_dir=lambda: tmp_path,
                           _observed_planning_source_frame=lambda _: frame,
                           _unresolved_family_child_focus_v1=lambda *_: {'pending': None})
    skip = service.GameplayBridgeService._skip_private_family_wartime_during_cooldown_v1
    planned = {'plan': {'selected_step': 'query-army-strengths-v1'}}
    result = skip(fake, planned, snapshot)
    assert result['plan']['family_wartime_opportunity_cooldown_v1']['status'] == 'active'
    assert calls == [1]
    monkeypatch.setattr(service, 'read_family_marriage_ledger', lambda _: {
        'pending': None,
        'resolved': {'episode_run_id': frame['episode_run_id'],
                     'heir_character_id': HEIR,
                     'status': 'marriage', 'material_result': True}})
    assert skip(fake, planned, snapshot) is None
    assert calls == [1]
    monkeypatch.setattr(service, 'read_family_marriage_ledger', lambda _: {
        'pending': None,
        'resolved': {'episode_run_id': 'native-prior-actor-old-episode',
                     'heir_character_id': HEIR,
                     'status': 'marriage', 'material_result': True}})
    assert skip(fake, planned, snapshot)['plan'][
        'family_wartime_opportunity_cooldown_v1']['status'] == 'active'
    assert calls == [1, 1]


def test_changed_heir_or_player_spouse_clears_cd(tmp_path, monkeypatch):
    frame, _ = active_after_two(tmp_path)
    snapshot = _snapshot(frame)
    monkeypatch.setattr(service, 'read_family_marriage_ledger',
                        lambda _: {'pending': None, 'resolved': None})
    monkeypatch.setattr(transport, 'query_current_first_heir_relationship_private_v1',
                        lambda driver, *, expected_native_revision: {
                            'status': 'available', 'read_only': True,
                            'bilateral_verified': True,
                            'native_revision': expected_native_revision,
                            'heir_character_id': HEIR + 1,
                            'betrothed_character_id': None,
                            'primary_spouse_character_id': None, 'spouse_character_ids': []})
    driver = SimpleNamespace(allow_private_current_first_heir_relationship_query=True,
                             take_internal_semantic_snapshot=lambda: snapshot,
                             _with_internal_planning_view=lambda *_: {'pending': None})
    fake = SimpleNamespace(driver=driver, _strategy_state_dir=lambda: tmp_path,
                           _observed_planning_source_frame=lambda _: frame,
                           _unresolved_family_child_focus_v1=lambda *_: {'pending': None})
    skip = service.GameplayBridgeService._skip_private_family_wartime_during_cooldown_v1
    assert skip(fake, {'plan': {'selected_step': 'life-advance'}}, snapshot) is None
    assert cadence.view(tmp_path, frame)['status'] == 'inactive'
    active_after_two(tmp_path)
    snapshot['played_character']['primary_spouse_id'] = None
    assert skip(fake, {'plan': {'selected_step': 'life-advance'}}, snapshot) is None
    assert cadence.view(tmp_path, frame)['status'] == 'inactive'


def test_war_action_and_unknown_relation_never_suppressed(tmp_path, monkeypatch):
    frame, _ = active_after_two(tmp_path)
    snapshot = _snapshot(frame)
    monkeypatch.setattr(service, 'read_family_marriage_ledger',
                        lambda _: {'pending': None, 'resolved': None})
    calls = []
    monkeypatch.setattr(transport, 'query_current_first_heir_relationship_private_v1',
                        lambda driver, *, expected_native_revision: calls.append(1) or {
                            'status': 'unavailable', 'native_revision': expected_native_revision})
    driver = SimpleNamespace(allow_private_current_first_heir_relationship_query=True,
                             take_internal_semantic_snapshot=lambda: snapshot,
                             _with_internal_planning_view=lambda *_: {'pending': None})
    fake = SimpleNamespace(driver=driver, _strategy_state_dir=lambda: tmp_path,
                           _observed_planning_source_frame=lambda _: frame,
                           _unresolved_family_child_focus_v1=lambda *_: {'pending': None})
    skip = service.GameplayBridgeService._skip_private_family_wartime_during_cooldown_v1
    assert skip(fake, {'plan': {'selected_step': 'move-army-1-to-2'}}, snapshot) is None
    assert calls == []
    assert skip(fake, {'plan': {'selected_step': 'query-army-strengths-v1'}}, snapshot) is None
    assert calls == [1]
    assert cadence.view(tmp_path, frame)['status'] == 'active'


def test_service_full_review_marks_bound_source_and_observes_completed_query(tmp_path):
    frame, plan, outcome = review()
    snapshot = _snapshot(frame)
    planned = {'plan': {'selected_step': plan['selected_step']}}
    driver = SimpleNamespace(allow_private_family_marriage_formal_trial=True)
    fake = SimpleNamespace(driver=driver, _last_war_family_observation=None,
                           _skip_private_family_wartime_during_cooldown_v1=lambda *_: None,
                           _plan_private_family_opportunity_v1=lambda *_args, **_kwargs: {
                               'plan': {**planned['plan'], **{
                                   k: v for k, v in plan.items()
                                   if k != '_family_wartime_review_v1'}}},
                           _strategy_state_dir=lambda: tmp_path)
    result = service.GameplayBridgeService._plan_private_family_wartime_v1(
        fake, planned, snapshot)
    source = result['plan']['_family_wartime_review_v1']
    assert source['actor_character_id'] == frame['actor_character_id']
    assert source['episode_run_id'] == frame['episode_run_id']
    assert source['heir_character_id'] == HEIR
    assert source['player_spouse_signature'] == [None, 30887, [30887]]
    assert source['expected_successor_character_id'] == HEIR
    receipt = service.GameplayBridgeService._observe_wartime_family_cadence_after_turn_v1(
        fake, {'plan': result['plan'], 'planning_source_frame': frame}, outcome)
    assert receipt['status'] == 'inactive'
    assert receipt['consecutive_noop_dates'] == 1

"""Synthetic normalized reads; real Service composer, durable ledger and following consumer."""
from copy import deepcopy
import json

import pytest

from test_sway_causal_terminal_retention_12004 import fresh_source_frames, IDENTITY
from xar_autoplayer.bridge.service import GameplayBridgeService
from xar_autoplayer.sway_formal_consumer import (
    LEDGER_FILE, SCHEMA, consume_sway_following_turn, read_sway_ledger,
)


def setup(tmp_path, *, gen0=False):
    _, termination = fresh_source_frames()
    termination.update(snapshot_revision=1000, date_raw=53290155)
    termination['records'][0].pop('cause_relation')
    ids = dict(IDENTITY)
    if gen0:
        ids.update(scheme_instance_id=IDENTITY['scheme_instance_id'] & 0xFFFFFF,
                   scheme_instance_generation=0)
        for key in ('scheme_instance_id', 'scheme_instance_generation'):
            termination[key] = termination['records'][0][key] = ids[key]
    gain = {**ids, 'next_turn_consumed': True, 'source_native_revision': 70,
            'source_date_raw': 53290100, 'incremental_named_gain_observed': True}
    resolved = {
        'status': 'applied', 'postcondition_verified': True,
        'action_id': IDENTITY['action_id'], 'actor_character_id': IDENTITY['actor_character_id'],
        'target_character_id': IDENTITY['target_character_id'],
        'post_native_revision': 69, 'post_date_raw': 53290099, 'next_turn_consumed': True,
        'native_receipt': {**ids, 'schema': 'active-scheme-sway-formal-private-v1',
                           'stage': 'applied', 'postcondition_verified': True},
        'material_intervention': {'historical_marker': 'unchanged'},
        'first_named_gain_intervention': gain,
    }
    (tmp_path / LEDGER_FILE).write_text(json.dumps(
        {'schema': SCHEMA, 'pending': None, 'resolved': resolved}), encoding='utf-8')

    class Driver:
        state_dir = tmp_path
        allow_private_active_scheme_sway_completion_execution_query = False
        calls = 0
        requested_full_id = ids['scheme_instance_id']
        def query_active_scheme_sway_completion_termination_private_v1(self, **kwargs):
            self.calls += 1
            return deepcopy(termination)

    service = GameplayBridgeService(Driver())
    service._auto_camera_worker.close_without_wait()
    return service, termination, resolved


def query(service):
    return service.query_active_scheme_sway_completion_termination_private_v1(
        expected_revision=1000, target_character_id=IDENTITY['target_character_id'],
        scheme_instance_id=service.driver.requested_full_id)


@pytest.mark.parametrize('gen0', [False, True])
def test_current_legal_wrapper_read_persists_without_execution_or_common_then_consumes(tmp_path, gen0):
    service, termination, original = setup(tmp_path, gen0=gen0)
    returned = query(service)
    composition = returned['sway_terminal_sources_12004']
    assert composition['retained_end_observation'] is not None
    assert composition['retained_common_end_observation'] is None
    assert composition['cause_input_pair'] is None
    saved = read_sway_ledger(tmp_path)['resolved']
    terminal = saved['terminal_intervention']
    assert terminal['instance_terminal_outcome_observed'] is True
    assert terminal['terminal_cause_observed'] is False and terminal['terminal_cause'] == 'unknown'
    assert terminal['source_native_revision'] == 1000
    assert terminal['source_date_raw'] == 53290155
    assert terminal['event_date_raw'] == termination['records'][0]['native_invocation']['post_date_raw']
    assert terminal['native_observation'] == termination['records'][0]
    assert terminal['next_turn_consumed'] is False
    assert saved['first_named_gain_intervention'] == original['first_named_gain_intervention']
    assert saved['material_intervention'] == original['material_intervention']
    followed = consume_sway_following_turn(tmp_path, {
        'paused': True, 'map_ready': True, 'played_character_id': IDENTITY['actor_character_id'],
        'played_character_alive': True, 'revision': 1001, 'native_revision': 1001,
        'date_raw': 53290179})
    assert followed['terminal_intervention']['next_turn_consumed'] is True
    consumed = deepcopy(followed['terminal_intervention'])
    query(service)  # Same original event cannot rearm consumption.
    assert read_sway_ledger(tmp_path)['resolved']['terminal_intervention'] == consumed
    termination['records'] = []  # New empty session/purge never invents or erases an end.
    query(service)
    assert read_sway_ledger(tmp_path)['resolved']['terminal_intervention'] == consumed
    assert service.driver.calls == 3  # Exactly the three supplied existing reads.


@pytest.mark.parametrize('change', ['empty', 'unavailable', 'gap', 'foreign_id', 'foreign_actor', 'generation',
                                   'pre_status', 'post_status', 'owner', 'not_returned',
                                   'no_transition', 'no_query_stamp'])
def test_unqualified_or_foreign_wrapper_never_stages_a_terminal(tmp_path, change):
    service, termination, _ = setup(tmp_path)
    row = termination['records'][0]
    if change == 'empty': termination['records'] = []
    elif change == 'unavailable': termination['available'] = False
    elif change == 'gap': termination['retention_gap'] = True
    elif change == 'foreign_id': row['scheme_instance_id'] += 1
    elif change == 'foreign_actor': row['actor_character_id'] += 1
    elif change == 'generation': row['scheme_instance_generation'] += 1
    elif change == 'pre_status': row['pre_status'] = 1
    elif change == 'post_status': row['post_status'] = 0
    elif change == 'owner': row['post_owner'] += 1
    elif change == 'not_returned': row['native_invocation']['original_returned'] = False
    elif change == 'no_transition': row['native_terminal_transition_observed'] = False
    elif change == 'no_query_stamp': termination.pop('snapshot_revision')
    before = (tmp_path / LEDGER_FILE).read_bytes()
    try:
        query(service)
    except ValueError:
        pass  # Existing strict source normalizers may reject earlier.
    assert (tmp_path / LEDGER_FILE).read_bytes() == before


def test_existing_qualified_cause_and_following_are_not_replaced_by_neutral_wrapper(tmp_path):
    from xar_autoplayer.sway_end_causal_consumer_12004 import record_sway_end_causal_observation
    service, _, _ = setup(tmp_path)
    execution, termination = fresh_source_frames()
    assert record_sway_end_causal_observation(
        tmp_path, execution_read=execution, termination_read=termination) is not None
    consume_sway_following_turn(tmp_path, {
        'paused': True, 'map_ready': True, 'played_character_id': IDENTITY['actor_character_id'],
        'played_character_alive': True, 'revision': 1001, 'native_revision': 1001,
        'date_raw': 53290179})
    previous = read_sway_ledger(tmp_path)['resolved']['terminal_intervention']
    query(service)
    current = read_sway_ledger(tmp_path)['resolved']['terminal_intervention']
    assert previous['terminal_cause_observed'] is True and previous['next_turn_consumed'] is True
    assert all(current[k] == v for k, v in previous.items())

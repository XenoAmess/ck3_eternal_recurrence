"""Reuse only an already computed list from the same locked history read."""
import copy
from unittest.mock import patch

import pytest

from xar_autoplayer.bridge import native_driver as native


def _started(*, decorated=False):
    result = {'assault_action': {'status': 'assault_started', 'siege_id': 901,
                                'war_id': 61, 'province_id': 2585}}
    if decorated:
        result['auto_turn'] = {'selected_step': 'start-assault-901'}
    return {'command': 'auto-turn' if decorated else 'start-assault-901',
            'ok': True, 'result': result}


@pytest.mark.parametrize('mode', ['open', 'stopped', 'failed_stop', 'restored',
                                  'failed_restore', 'decorated', 'failed_slice', 'empty'])
def test_reused_lifecycles_preserve_unknown_assault_restore_and_failure_semantics(mode):
    history = [] if mode == 'empty' else [_started(decorated=mode == 'decorated')]
    if mode in ('stopped', 'failed_stop'):
        history.append({'command': 'stop-assault-901', 'ok': mode == 'stopped',
            'result': {'assault_action': {'status': 'assault_stopped', 'siege_id': 901,
                                         'war_id': 61, 'province_id': 2585}}})
    if mode in ('restored', 'failed_restore'):
        history.append({'command': native._RESTORE_CHECKPOINT_STEP, 'ok': mode == 'restored'})
    if mode == 'failed_slice':
        history.append({'command': 'life-advance', 'ok': False})
    state = {'province_id': 2585, 'siege_observable': False}
    if mode == 'failed_slice':
        state.update(siege_observable=True, active_siege={
            'siege_id': 901, 'assault_observable': True,
            'assault_in_progress': True, 'player_army_besieging': True})
    snapshot = {'paused': True, 'war_objective_assault_supported': True,
                'active_wars': [{'war_id': 61, 'objective_province_states': [state]}]}
    before = copy.deepcopy((snapshot, history))
    original = native._native_open_assault_lifecycles
    opened = original(history)
    saved_opened = copy.deepcopy(opened)
    with patch.object(native, '_native_open_assault_lifecycles', wraps=original) as recover:
        expected = native._native_unobservable_started_assaults(snapshot, history)
        assert recover.call_count == 1
        recover.reset_mock()
        observed = native._native_unobservable_started_assaults(
            snapshot, history, open_lifecycles=opened)
        recover.assert_not_called()
    assert observed == expected
    if mode in ('stopped', 'restored', 'empty'):
        assert observed == []
    else:
        assert len(observed) == 1
        assert observed[0]['reason'] == ('previous_assault_slice_failed_unknown'
                                        if mode == 'failed_slice' else 'siege_unobservable_after_start')
    assert (snapshot, history) == before
    assert opened == saved_opened

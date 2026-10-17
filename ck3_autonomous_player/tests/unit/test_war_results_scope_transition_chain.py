"""Real Service/Native transport/primitive/history; Native I/O is synthetic.

The initial close plan is preselected. This tests its execution, not ordinary
planner selection. Delayed calendar drift is an explicit counterfactual input.
"""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_native_bridge_driver import FakeEndpoint
from tools.g2_saved_campaign.war_results_scope_transition_outcome import (
    classify_paused_war_results_scope_transition_v1,
)
from xar_autoplayer.bridge import native_driver as native
from xar_autoplayer.bridge import war_results_window_contract as contract
from xar_autoplayer.bridge.service import GameplayBridgeService


FIXTURE = json.loads((Path(__file__).parents[1] / 'fixtures' /
                     'p47_war_results_scope_transition_projection.json').read_text(encoding='utf-8'))


@pytest.mark.parametrize('drift_days,pause_ok', [(0, True), (105, True), (0, False)])
def test_real_close_then_pause_preserves_pending_and_zero_credit(drift_days, pause_ok):
    close = FIXTURE['result']
    source = deepcopy(FIXTURE['body_projection']['planning_source_frame'])
    snapshot = {
        'snapshot_id': source['snapshot_id'], 'revision': source['revision'],
        'native_revision': source['native_revision'], 'date_raw': source['date_raw'],
        'episode_run_id': source['episode_run_id'], 'paused': True, 'map_ready': True,
        'speed': 5, 'active_event': None, 'pending_character_interaction': None,
        'played_character': {'character_id': source['actor_character_id'], 'alive': True},
        'active_wars': [], 'player_armies': [],
        'diagnostics': {'bridge_pid': source['bridge_pid'],
                        'connection_generation': source['connection_generation'],
                        'hello': {'pid': source['bridge_pid'],
                                  'connection_generation': source['connection_generation'],
                                  'expected_ck3_version': close['game_version'],
                                  'expected_ck3_sha256': close['executable_sha256']}},
    }
    endpoint = FakeEndpoint()
    driver = native.NativeHeadlessGameplayDriver(endpoint.pipe_name, endpoint=endpoint,
                                                 episode_projection='native_campaign')
    driver.state.semantic_snapshot = lambda **kwargs: deepcopy(snapshot)
    base_caps = driver.state.capabilities()
    driver.state.capabilities = lambda: {
        **deepcopy(base_caps), 'action_steps': ['pause-map'],
        'bridge_capabilities': [contract.QUERY_CAPABILITY, contract.CLOSE_CAPABILITY],
    }
    sent = []

    def publish(request):
        sent.append(deepcopy(request))
        if request['step'] == contract.CLOSE_STEP:
            assert request['expected_revision'] == source['native_revision']
            leaf = {key: close[key] for key in contract._B15_FIELDS}
            leaf['request_id'] = request['request_id']
            owner = deepcopy(close['native_command_result'][contract.OWNER_RECEIPT_KEY])
            owner['request_id'] = request['request_id']
            snapshot.update(paused=False, revision=source['revision'] + 1,
                            native_revision=source['native_revision'] + 1,
                            snapshot_id='native:' + str(source['native_revision'] + 1),
                            date_raw=source['date_raw'] + drift_days * 24,
                            active_event={'instance_id': 69})
            frame = {'type': 'command_result', 'protocol_version': 1,
                     'request_id': request['request_id'], 'ok': True, 'result': leaf,
                     contract.OWNER_RECEIPT_KEY: owner}
        elif request['step'] == 'pause-map':
            assert request['expected_revision'] == source['native_revision'] + 1
            if pause_ok:
                snapshot.update(paused=True, revision=source['revision'] + 2,
                                native_revision=source['native_revision'] + 2,
                                snapshot_id='native:' + str(source['native_revision'] + 2))
                frame = {'type': 'command_result', 'protocol_version': 1,
                         'request_id': request['request_id'], 'ok': True,
                         'result': {'step': 'pause-map', 'accepted': True, 'status': 'paused'}}
            else:
                frame = {'type': 'command_result', 'protocol_version': 1,
                         'request_id': request['request_id'], 'ok': False,
                         'error': 'synthetic pause rejected'}
        else:
            raise AssertionError(('Unexpected Native request', request))
        endpoint.publish(frame)

    endpoint.send_hook = publish
    service = GameplayBridgeService(driver)
    service.plan_turn = lambda: {
        'plan': deepcopy(FIXTURE['body_projection']['plan']),
        'snapshot_id': source['snapshot_id'], 'revision': source['revision'],
        'planning_source_frame': deepcopy(source),
    }
    try:
        body = service.auto_turn()
        pause = body['result']['scope_transition_pause']
        assert source['revision'] == 870 and source['native_revision'] == 7550
        assert [row['step'] for row in sent] == [contract.CLOSE_STEP, 'pause-map']
        assert [row['expected_revision'] for row in sent] == [7550, 7551]
        assert body['status'] == 'pending' and body['ui_action_credit'] is False
        assert body['result']['accepted'] is False and body['result']['closure_verified'] is False
        assert pause['close_replayed'] is False and pause['close_action_credit'] is False
        assert snapshot['active_event'] == {'instance_id': 69}
        assert driver._execute_primitive_step.__func__ is native.NativeHeadlessGameplayDriver._execute_primitive_step
        assert driver._record_command.__func__ is native.NativeHeadlessGameplayDriver._record_command
        assert len(driver._command_history) == 2
        assert driver._war_results_window_close_pending is not None
        if pause_ok:
            assert pause['status'] == 'paused_same_owner_requery_required'
            credit = classify_paused_war_results_scope_transition_v1(
                body, binding=source, game_pid=source['bridge_pid'])
            assert credit['typed_nonmaterial_observation'] is True
            assert credit['war_results_window_closed_verified'] is False
            assert credit['date_advance_observed'] is False
            assert credit['actual_elapsed_days_uncredited'] == drift_days
            assert credit['new_close_retry_authorized'] is False
        else:
            assert pause['status'] == 'pause_unverified'
            assert snapshot['paused'] is False
            with pytest.raises(ValueError, match='same-owner paused requery proof'):
                classify_paused_war_results_scope_transition_v1(
                    body, binding=source, game_pid=source['bridge_pid'])
    finally:
        driver.close()

"""Actual old close shape and an explicitly synthetic later SDK connection."""
from copy import deepcopy
from types import SimpleNamespace

from test_war_results_scope_transition_pause import RESULT
from xar_autoplayer.bridge.war_results_window_transport import _resolve_completed_close_query
from xar_autoplayer.ordinary_war_results_window_v1 import plan_ordinary_war_results_window_v1


def fresh_frame():
    return {
        'snapshot_id': 'native:7681', 'revision': 1001, 'native_revision': 7681,
        'date_raw': 53317032, 'paused': True, 'map_ready': True,
        'active_event': {'instance_id': 69},
        'episode_run_id': RESULT['queried_episode_run_id'],
        'played_character': {'character_id': RESULT['queried_actor_character_id'], 'alive': True},
        'diagnostics': {'connection_generation': 9},
        'war_results_window_v1_observation': None,
        'war_results_window_v1_query_attempt': None,
        'war_results_window_v1_close_pending': None,
        'war_results_window_v1_check_due': True,
    }


def test_later_connection_query_cannot_retire_original_close():
    driver = SimpleNamespace(_war_results_window_close_pending={
        'status': 'verification_pending', 'step': 'close-war-results-window-v1',
        'native_request_id': RESULT['native_request_id'],
        'completed_response': deepcopy(RESULT),
        'binding': {'native_revision': RESULT['queried_native_revision'],
                    'date_raw': RESULT['queried_date_raw']},
        'native_generation': 8, 'collectable': False,
    })
    query = {
        'operation': 'query', 'available': True, 'post_observed': True,
        'scope_unchanged': True, 'post_window_present': False,
        'post_effective_visible': False, 'connection_generation': 9,
        'queried_actor_character_id': RESULT['queried_actor_character_id'],
        'queried_connection_generation': 9,
        'queried_episode_run_id': RESULT['queried_episode_run_id'],
        'queried_native_revision': 7681, 'queried_date_raw': 53317032,
    }
    _resolve_completed_close_query(driver, query)
    assert driver._war_results_window_close_pending['native_request_id'] == RESULT['native_request_id']
    assert 'prior_close_execution_observation' not in query


def test_new_sdk_queries_ui_independently_before_resuming_event():
    fresh = fresh_frame()
    steps = ('query-war-results-window-v1', 'close-war-results-window-v1', 'pause-map')
    caps = ('game.command.query-war-results-window-v1', 'game.command.close-war-results-window-v1')
    plan = plan_ordinary_war_results_window_v1(fresh, action_steps=steps, bridge_capabilities=caps)
    assert plan['selected_step'] == 'query-war-results-window-v1'
    assert plan['war_results_window']['close_pending'] is False
    fresh['war_results_window_v1_observation'] = {
        'sdk_validation_schema': 'war-results-window-source-v1',
        'queried_snapshot_id': fresh['snapshot_id'], 'queried_revision': fresh['revision'],
        'queried_native_revision': fresh['native_revision'], 'queried_date_raw': fresh['date_raw'],
        'queried_actor_character_id': fresh['played_character']['character_id'],
        'queried_connection_generation': 9, 'queried_episode_run_id': fresh['episode_run_id'],
        'available': True, 'post_observed': True, 'scope_unchanged': True,
        'post_window_present': False, 'post_effective_visible': False,
    }
    assert plan_ordinary_war_results_window_v1(fresh, action_steps=steps, bridge_capabilities=caps) is None
    assert fresh['active_event'] == {'instance_id': 69}

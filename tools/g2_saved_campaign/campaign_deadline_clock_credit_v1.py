"""Pure exact Native deadline observation; a rejected redundant pause stays rejected."""
from __future__ import annotations

import copy


def classify_deadline_clock_v1(body, *, initial_frame, game_pid, bind):
    plan = body.get('plan') if isinstance(body.get('plan'), dict) else {}
    step = body.get('selected_step', plan.get('selected_step'))
    inner = body.get('result')
    if step not in {'life-advance', 'life-advance-one-day'} or not isinstance(inner, dict):
        return None
    clock = inner.get('campaign_deadline_native_clock_v1')
    if not isinstance(clock, dict):
        return None
    # A wholly accepted sequence keeps the original classifier behavior.
    actions = inner.get('actions')
    if isinstance(actions, list) and actions and all(isinstance(a, dict)
            and isinstance(a.get('result'), dict) and a['result'].get('accepted') is True for a in actions):
        return None

    def require(ok, reason):
        if not ok:
            raise ValueError('Native campaign deadline: ' + reason)

    start, end = inner.get('starting_date_raw'), inner.get('ending_date_raw')
    elapsed, horizon = inner.get('elapsed_days'), inner.get('requested_horizon_days')
    binding = bind(body, initial_frame=initial_frame, game_pid=game_pid)
    # Every original clock outer/source/date requirement remains required.
    require(body.get('status') == 'executed' and plan.get('selected_step') == step
        and inner.get('step') == step and inner.get('backend_id') == 'native-headless'
        and inner.get('source') == 'native-composite' and inner.get('paused') is True
        and inner.get('progress_status') == 'postcondition'
        and type(start) is int and type(end) is int and end > start
        and inner.get('starting_date', {}).get('date_raw') == start
        and inner.get('ending_date', {}).get('date_raw') == end
        and type(elapsed) is int and elapsed > 0 and end - start == elapsed * 24
        and type(horizon) is int and 1 <= horizon <= 30
        and (step != 'life-advance-one-day' or horizon == elapsed == 1)
        and isinstance(initial_frame, dict)
        and binding.get('episode_run_id') == initial_frame.get('episode_run_id')
        and binding.get('date_raw') == start, 'original composite/date/source postcondition differs')
    require(type(game_pid) is int and game_pid == 214568 and binding.get('bridge_pid') == game_pid
        and binding.get('connection_generation') == 4
        and inner.get('final_screen') == 'map_hud' and inner.get('active_event') is None
        and inner.get('pending_character_interaction') is None
        and inner.get('event_resolution') == 'none' and inner.get('ordinary_events') == []
        and type(inner.get('revision')) is int and inner['revision'] > binding['revision']
        and isinstance(inner.get('snapshot_id'), str)
        and inner['snapshot_id'].startswith('native:')
        and inner['snapshot_id'][7:].isdecimal()
        and int(inner['snapshot_id'][7:]) > binding['native_revision'], 'C3 final map or owner differs')
    require(clock.get('schema') == 'xar.ck3.campaign-native-date-clock/v1'
        and clock.get('scope') == 'campaign_date_deadline'
        and clock.get('starting_date_raw') == start and clock.get('target_date_raw') == end
        and clock.get('early_boundary_cancel') is None
        and clock.get('exact_one_day_qualification_claimed') is False
        and elapsed == horizon and inner.get('timeline_speed') == 5
        and inner.get('timeline_policy') == 'bounded_non_tactical', 'clock scope or exact horizon differs')
    deadline = inner.get('campaign_deadline_v1', {})
    requested = plan.get('campaign_deadline_v1', {})
    require(isinstance(deadline, dict) and isinstance(requested, dict)
        and deadline.get('schema') == requested.get('schema') == 'xar.ck3.campaign-clock-deadline/v1'
        and deadline.get('campaign_id') == requested.get('campaign_id') == 'robert-first30-v20261019'
        and deadline.get('calendar_profile') == requested.get('calendar_profile') == 'ck3-1.20.0.4-cdate-fixed365-raw24/v1'
        and deadline.get('starting_date_raw') == requested.get('starting_date_raw') == start
        and deadline.get('requested_target_date_raw') == deadline.get('target_date_raw') == end
        and deadline.get('status') == requested.get('status') == 'advance'
        and deadline.get('policy_choices_changed') is requested.get('policy_choices_changed') is False
        and type(deadline.get('boundary_date_raw')) is int
        and type(deadline.get('endpoint_date_raw')) is int
        and deadline['boundary_date_raw'] == requested.get('boundary_date_raw')
        and deadline['endpoint_date_raw'] == requested.get('endpoint_date_raw')
        and end <= deadline['boundary_date_raw'] <= deadline['endpoint_date_raw'], 'campaign deadline binding differs')
    actions = inner.get('actions')
    require(isinstance(actions, list) and len(actions) == 4
        and all(isinstance(a, dict) and isinstance(a.get('result'), dict) for a in actions),
        'exact Arm/resume/redundant-pause/Status sequence absent')
    arm, resume, pause, status = actions
    arm_step = f'research-arm-tactical-daily-sentinel-v1-{start}-to-{end}-speed-5-mode-terminal-a-0'
    require([a.get('step') for a in actions] == [arm_step, 'resume-map', 'pause-map', 'research-query-tactical-daily-sentinel-v1']
        and all(a['result'].get('step') == a['step'] for a in actions), 'action order or inner step differs')
    require(all(a['result'].get('accepted') is True and a['result'].get('status') == 'available'
        and a['result'].get('backend_id') == 'native-headless' for a in (arm, status))
        and resume['result'].get('accepted') is True and resume['result'].get('status') == 'submitted'
        and resume['result'].get('backend_id') == 'native-headless', 'Arm/resume/Status rejected or unknown')
    require(pause['result'] == {'step': 'pause-map', 'accepted': False, 'status': 'rejected',
        'error': 'CK3 map state is unavailable'}, 'only the observed redundant pause diagnostic is admitted')
    armed, stopped = clock.get('armed'), clock.get('stopped')
    require(isinstance(armed, dict) and isinstance(stopped, dict)
        and armed == arm['result'].get('tactical_daily_sentinel')
        and stopped == status['result'].get('tactical_daily_sentinel'), 'Arm/Status original proof differs')
    from xar_autoplayer.bridge.native_driver import (
        _validate_tactical_daily_sentinel_arm, _validate_tactical_daily_sentinel_stop)
    _validate_tactical_daily_sentinel_arm(arm['result'], armed, arm_step=arm_step,
        starting_date_raw=start, target_date_raw=end, speed=5,
        mode='terminal_or_sentinel', watch_army_ids=(), sentinel_scope='campaign_date_deadline')
    _validate_tactical_daily_sentinel_stop(stopped, arm_status=armed, starting_date_raw=start,
        target_date_raw=end, ending_date_raw=end, elapsed_days=elapsed,
        speed=5, mode='terminal_or_sentinel', watch_army_ids=())
    require(type(armed.get('generation')) is int and armed['generation'] > 0
        and stopped.get('generation') == armed['generation']
        and armed.get('state') == 'armed' and stopped.get('state') == 'triggered'
        and all(s.get('starting_date_raw') == start and s.get('target_date_raw') == end
                and s.get('speed') == 5 and s.get('mode') == 'terminal_or_sentinel'
                and s.get('army_count') == s.get('combat_count') == 0 for s in (armed, stopped))
        and stopped.get('last_observed_date_raw') == stopped.get('trigger_date_raw') == end
        and stopped.get('completed_daily_ticks') == elapsed
        and stopped.get('intermediate_pause_count') == 0
        and stopped.get('trigger_flags') == 1 and stopped.get('trigger_reasons') == ['date_deadline']
        and stopped.get('signed_date_delta_from_target_raw') == stopped.get('overshoot_days') == 0
        and stopped.get('pause_wrapper_called') is stopped.get('pause_observed') is True
        and stopped.get('terminal_observed') is stopped.get('abnormal') is False, 'exact Native deadline/pause proof differs')
    speed = clock.get('speed_configuration', {})
    require(speed == {'status': 'already_observed', 'submitted': False, 'observed_speed': 5,
        'source_snapshot_id': binding['snapshot_id'], 'source_native_revision': binding['native_revision'],
        'source_date_raw': start}, 'speed source differs')
    return {'schema': 'g2.queue.ordinary-result-credit/v1', 'selected_step': step,
        'service_status': body['status'], 'result_status': inner['progress_status'],
        'category': 'existing_clock_advance_observed', 'typed_nonmaterial_observation': True,
        'submitted_pending': False, 'primitive_accepted': False,
        'actual_date_delta_raw': end - start, 'actual_elapsed_days': elapsed,
        'paired_after_metrics_still_required': True, 'business_success_inferred': False,
        'replay_allowed': False, 'native_deadline_observed': True,
        'rejected_redundant_pause_action': copy.deepcopy(pause),
        'rejected_pause_command_succeeded': False,
        'native_deadline_proof': copy.deepcopy(clock)}

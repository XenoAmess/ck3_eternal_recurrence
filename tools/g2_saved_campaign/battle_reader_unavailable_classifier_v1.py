"""Self-contained queue branch: AST-installable without the app SDK namespace.

Prepend classify_battle_reader_unavailable_v1 to the existing result classifier;
None delegates to its prior branches. This module never submits an action.
"""

def classify_battle_reader_gameplay_start_binding_v1(body, *, initial_frame=None, game_pid=None):
    """Bind gameplay evidence to the observed plan frame, independently of presentation."""
    plan = body.get('plan') if isinstance(body.get('plan'), dict) else {}
    inner = body.get('result') if isinstance(body.get('result'), dict) else {}
    if 'planning_source_frame' in body:
        source = body['planning_source_frame']
        if not isinstance(source, dict) or source.get('status') != 'complete':
            raise ValueError('actual planning source frame is partial')
        binding = dict(source)
    elif 'starting_frame' in inner:
        source = inner['starting_frame']
        if not isinstance(source, dict):
            raise ValueError('actual composite starting frame is malformed')
        binding = dict(source)
    elif 'query_source' in plan:
        source = plan['query_source']
        if not isinstance(source, dict):
            raise ValueError('actual plan query source is malformed')
        binding = dict(source)
    else:
        risk = plan.get('player_risk_context')
        goal = plan.get('campaign_goal_plan_used')
        if not isinstance(risk, dict) or not isinstance(goal, dict):
            raise ValueError('independent legacy gameplay frame is absent')
        source = risk.get('binding')
        scope = risk.get('current_scope')
        if not isinstance(source, dict) or not isinstance(scope, dict):
            raise ValueError('independent legacy gameplay frame is malformed')
        binding = dict(source)
        binding['actor_character_id'] = source.get('character_id')
        binding['episode_run_id'] = goal.get('campaign_id')
        binding['connection_generation'] = scope.get('connection_generation')
        if goal.get('current_character_id') != binding['actor_character_id']:
            raise ValueError('legacy gameplay actor sources differ')
    if not isinstance(initial_frame, dict) or type(initial_frame.get('actor_character_id')) is not int or (not isinstance(initial_frame.get('episode_run_id'), str)) or (not initial_frame['episode_run_id']) or (type(binding.get('actor_character_id')) is not int) or (binding['actor_character_id'] != initial_frame['actor_character_id']) or (binding.get('episode_run_id') != initial_frame['episode_run_id']) or any((type(binding.get(k)) is not int or binding[k] <= 0 for k in ('revision', 'native_revision', 'date_raw', 'connection_generation'))) or (binding.get('snapshot_id') != 'native:' + str(binding['native_revision'])):
        raise ValueError('gameplay starting actor/episode/frame binding differs')
    pid = binding.get('bridge_pid')
    if pid is not None and (type(pid) is not int or pid <= 0 or (game_pid is not None and pid != game_pid)):
        raise ValueError('gameplay starting process binding differs')
    return binding

def classify_battle_reader_unavailable_v1(body, *, initial_frame=None, game_pid=None):
    if not isinstance(body, dict):
        return None
    inner = body.get('result')
    if not isinstance(inner, dict) or inner.get('schema') != 'xar.battle-control-readonly-unavailable.v1':
        return None
    binding = classify_battle_reader_gameplay_start_binding_v1(body, initial_frame=initial_frame, game_pid=game_pid)
    step, plan = (body.get('selected_step'), body.get('plan'))
    if body.get('status') != 'executed' or not isinstance(plan, dict) or plan.get('selected_step') != step or (inner.get('step') != step) or (type(game_pid) is not int) or (binding.get('bridge_pid') != game_pid):
        raise ValueError('battle unavailable public source differs')
    classify_validate_battle_reader_unavailable_v1(inner, planning_source=binding)
    return {'schema': 'g2.queue.ordinary-result-credit/v1', 'selected_step': step, 'service_status': 'executed', 'result_status': 'unavailable', 'category': 'readonly_battle_control_unavailable_observed', 'source_gameplay_frame': dict(binding), 'original_readonly_unavailable': inner, 'native_request_id': inner['native_request']['request_id'], 'submitted_pending': False, 'primitive_accepted': False, 'typed_nonmaterial_observation': True, 'date_advance_observed': False, 'actual_date_delta_raw': 0, 'actual_elapsed_days': 0, 'material_verified': False, 'ui_action_credit': False, 'action_credit': False, 'lifestyle_material_verified': False, 'existing_focus_verified': False, 'council_material_verified': False, 'construction_material_verified': False, 'construction_start_verified': False, 'construction_completion_verified': False, 'crown_material_verified': False, 'crown_receipt_nonmaterial': False, 'existing_typed_material_verified': False, 'business_success_inferred': False, 'paired_after_metrics_still_required': True, 'replay_allowed': False}

def classify_parse_battle_reader_public_step_v1(step):
    prefix = 'query-battle-control-snapshot-v1-'
    if not isinstance(step, str) or not step.startswith(prefix):
        return None
    number = step[len(prefix):]
    if not number or not number.isascii() or (not number.isdecimal()) or (len(number) > 10):
        return None
    value = int(number)
    return value if str(value) == number and 0 <= value <= 2 ** 31 - 1 else None
BATTLE_READER_SCHEMA_V1 = 'xar.battle-control-readonly-unavailable.v1'
BATTLE_READER_NATIVE_ERROR_V1 = 'application-main typed query failed or its snapshot changed'
BATTLE_READER_TYPED_FAILURE_V1 = {'executor_enter': True, 'executor_exception': {'code': 0, 'image': 'none', 'rva': None}, 'executor_finish': True, 'executor_typed_result': False, 'final_equal': None, 'final_read': None, 'frame_stable': True, 'query_type': 'battle_control', 'stage': 'typed_result', 'typed_result': False, 'wait_completed': True, 'wait_result': 'completed'}
BATTLE_READER_FRAME_KEYS_V1 = ('snapshot_id', 'revision', 'native_revision', 'date_raw', 'actor_character_id', 'episode_run_id', 'bridge_pid', 'connection_generation', 'paused', 'map_ready')

def classify_battle_reader_exact_json_v1(a, b):
    if type(a) is not type(b):
        return False
    if isinstance(b, dict):
        return a.keys() == b.keys() and all((classify_battle_reader_exact_json_v1(a[k], v) for k, v in b.items()))
    if isinstance(b, list):
        return len(a) == len(b) and all((classify_battle_reader_exact_json_v1(x, y) for x, y in zip(a, b)))
    return a == b

def classify_battle_reader_terminal_failure_v1(error, step, native_revision):
    request, result = (getattr(error, 'native_request_frame', None), getattr(error, 'native_command_result_frame', None))
    rid = getattr(error, 'native_request_id', None)
    return bool(classify_parse_battle_reader_public_step_v1(step) is not None and isinstance(rid, str) and rid and isinstance(request, dict) and isinstance(result, dict) and classify_battle_reader_exact_json_v1(request, {'type': 'execute_step', 'protocol_version': 1, 'request_id': rid, 'step': step, 'expected_revision': native_revision}) and classify_battle_reader_exact_json_v1(result, {'type': 'command_result', 'protocol_version': 1, 'request_id': rid, 'ok': False, 'error': BATTLE_READER_NATIVE_ERROR_V1, 'typed_query_failure_v1': BATTLE_READER_TYPED_FAILURE_V1}))

def classify_validate_battle_reader_unavailable_v1(result, *, planning_source=None):
    if not isinstance(result, dict) or set(result) != {'schema', 'step', 'accepted', 'status', 'read_only', 'business_submission', 'replay_allowed', 'backend_id', 'battle_control_snapshot', 'diagnostic_reason', 'prediction_ready', 'retreat_authorized', 'scope_key', 'source_frame', 'same_frame_readback', 'native_request', 'native_command_result'}:
        raise ValueError('battle unavailable shape differs')
    subject = classify_parse_battle_reader_public_step_v1(result['step'])
    source, scope = (result['source_frame'], result['scope_key'])
    if result['schema'] != BATTLE_READER_SCHEMA_V1 or subject is None or result['accepted'] is not False or (result['status'] != 'unavailable') or (result['read_only'] is not True) or (result['business_submission'] is not False) or (result['replay_allowed'] is not False) or (result['backend_id'] != 'native-headless') or (result['battle_control_snapshot'] is not None) or (result['diagnostic_reason'] != 'native_battle_control_typed_read_failed') or (result['prediction_ready'] is not False) or (result['retreat_authorized'] is not False) or (not isinstance(source, dict)) or (set(source) != set(BATTLE_READER_FRAME_KEYS_V1)) or (not classify_battle_reader_exact_json_v1(source, result['same_frame_readback'])) or any((type(source[k]) is not int or source[k] <= 0 for k in ('revision', 'native_revision', 'date_raw', 'actor_character_id', 'bridge_pid', 'connection_generation'))) or (source['snapshot_id'] != 'native:' + str(source['native_revision'])) or (not isinstance(source['episode_run_id'], str)) or (not source['episode_run_id']) or (source['paused'] is not True) or (source['map_ready'] is not True) or (not isinstance(scope, dict)) or (set(scope) != {'subject_army_id', 'province_id', 'actor_character_id', 'episode_run_id', 'bridge_pid', 'connection_generation', 'active_war_ids', 'observed_combat_army_ids'}) or (scope['subject_army_id'] != subject) or (type(scope['province_id']) is not int) or (scope['province_id'] <= 0) or any((not classify_battle_reader_exact_json_v1(scope[k], source[k]) for k in ('actor_character_id', 'episode_run_id', 'bridge_pid', 'connection_generation'))):
        raise ValueError('battle unavailable source/scope differs')
    for key in ('active_war_ids', 'observed_combat_army_ids'):
        ids = scope[key]
        minimum = 1 if key == 'active_war_ids' else 0
        if not isinstance(ids, list) or not ids or any((type(v) is not int or not minimum <= v <= 2 ** 31 - 1 for v in ids)) or (ids != sorted(set(ids))):
            raise ValueError('battle unavailable scope IDs malformed')
    if subject not in scope['observed_combat_army_ids']:
        raise ValueError('battle unavailable subject absent')

    class Evidence:
        pass
    error = Evidence()
    error.native_request_frame, error.native_command_result_frame = (result['native_request'], result['native_command_result'])
    error.native_request_id = error.native_request_frame.get('request_id') if isinstance(error.native_request_frame, dict) else None
    if not classify_battle_reader_terminal_failure_v1(error, result['step'], source['native_revision']):
        raise ValueError('battle unavailable original terminal read differs')
    if planning_source is not None:
        if not isinstance(planning_source, dict) or any((not classify_battle_reader_exact_json_v1(planning_source.get(k), source[k]) for k in BATTLE_READER_FRAME_KEYS_V1 if k not in {'paused', 'map_ready'})):
            raise ValueError('battle unavailable public planning frame differs')
    return result

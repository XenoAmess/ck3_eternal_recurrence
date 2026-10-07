"""File-only R24 typed normal-close v3 author/verifier; no live calls."""
import argparse
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
RUN = BASE / 'live-attempt-024'
HEAD = 'e0e017da1ad84eea9cf623728d38d29d55d8bbdf'
TASK = 'ck3-lyd-r24-runtime-20261008-001'
IDENTITY = {'pid': 18364, 'process_create_time': 1791390903.2912388,
            'process_creation_filetime_100ns': 134358645032912387}
NATIVE_SID = '01bc16ca823f4c84b3804823a4f2c6dc'
CLIENT_SID = '55cacd243abb467d97c465617c787375'
PROFILE_SHA = 'a8f2c881ae8a94453b75985c239e00e4228624b83283ba45ea5e3ca4946bebca'
CLI_SHA = 'b3c44b42f7bdf401b593d863e3210106a46412dcd7d89f8596c74f4c27392dee'
KEYS = {'schema', 'status', 'source_head', 'root_screen_task', 'original_process',
        'launch', 'original_handle_observation', 'original_native_observation',
        'helpers_closed', 'process_absence', 'keeper_final', 'release_receipt',
        'after_list', 'consumer_closed', 'consumer_session', 'consumer_close_result'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def ref(path):
    path = Path(path)
    need(path.is_absolute() and path.suffix.lower() != '.ck3', 'Absolute bounded non-save input required')
    for item in (path, *path.parents):
        need(not item.is_symlink() and not item.is_junction(), 'Linked input refused')
    need(path.stat().st_size <= 8 * 1024 * 1024, 'Bounded evidence only')
    raw = path.read_bytes()
    return {'path': path.resolve().as_posix(), 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest()}


def raw(row):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'Complete actual ref3 required; NULL refused')
    actual = ref(row['path'])
    need(type(row['bytes']) is int and actual['bytes'] == row['bytes'] and
         actual['sha256'] == row['sha256'].lower(), 'Actual bytes/SHA changed')
    return Path(row['path']).read_bytes()


def read(row):
    return json.loads(raw(row))


def stamp(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(value.tzinfo is not None, 'Aware actual timestamp required')
    return value


def same_path(a, b):
    return Path(a).resolve() == Path(b).resolve()


def pins():
    return json.loads((HERE / 'DEPENDENCIES.json').read_bytes())


def execution(row):
    value = read(row)
    need(type(value['exit_code']) is int and value['exit_code'] == 0 and
         value['automatic_retry'] is False, 'Original once-only execution completion0 required')
    raw(value['stdout']); raw(value['stderr'])
    argv = read(value['argv_input'])
    need((argv['argv'] if type(argv) is dict else argv) == value['argv'], 'Original frozen argv differs')
    need(stamp(value['finished_at_utc']) >= stamp(value['started_at_utc']), 'Original completion time order differs')
    return value


def contract(p):
    raw(p['contract_source']); raw(p['observer_source'])
    for name in ('normal_exit_contract_v1.py', 'normal_exit_process_observer_v1.py'):
        need(ref(HERE / 'exact-source' / name)['sha256'] ==
             p['contract_source' if name.startswith('normal_exit_contract') else 'observer_source']['sha256'],
             'Exact frozen pure validator source changed')
    sys.path.insert(0, str(HERE / 'exact-source'))
    spec = importlib.util.spec_from_file_location('r24_exact_normal_exit_contract', HERE / 'exact-source/normal_exit_contract_v1.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def checked(p):
    d = {name: read(row) for name, row in p.items() if name not in ('contract_source', 'observer_source')}
    launch, session = d['launch'], d['consumer_session']
    need(launch['schema'] == 'lyd.r24.root-launch-profile-helper.v1' and launch['source_revision'] == HEAD and
         launch['game_started'] is True and launch['status'] == 'GAME_CREATED_REQUIRES_NATIVE_LOAD_READBACK' and
         (launch['pid'], launch['process_create_time']) == (IDENTITY['pid'], IDENTITY['process_create_time']),
         'Original R24 launch/source identity differs')
    need(session['client_session_id'] == CLIENT_SID and session['source_revision'] == HEAD and
         session['profile_sha256'] == PROFILE_SHA and session['target'] ==
         {'pid': IDENTITY['pid'], 'process_create_time': IDENTITY['process_create_time']}, 'Original SDK session/profile identity differs')
    native, sdk = d['game_native'], d['game_sdk']
    need(sdk['resultType'] == 'complete' and sdk['isError'] is False and sdk['structuredContent'] == native and
         json.loads(sdk['content'][0]['text']) == native, 'Official SDK/native/text exact join required')
    need(native['schema'] == 'ck3.native-profile-receipt.v1' and native['session_id'] == NATIVE_SID and
         native['profile_sha256'] == PROFILE_SHA and d['original_game_native'] == native and
         same_path(native['receipt_path'], p['original_game_native']['path']) and
         p['original_game_native']['sha256'] == p['game_native']['sha256'], 'Actual original native receipt differs')
    response, request = d['game_response'], d['game_request']
    need(response['status'] == 'MCP_RESULT_RECORDED' and response.get('is_error') in (None, False) and
         response['sdk_result'] == Path(p['game_sdk']['path']).name and
         response['sdk_result_sha256'] == p['game_sdk']['sha256'] and
         response['request_sha256'] == p['game_request']['sha256'] and
         same_path(response['request_path'], p['game_request']['path']) and
         request['request_id'] == response['request_id'] and request['operation'] == 'call_tool' and
         request['name'] == 'ck3_observe_profile_normal_exit_v1' and request['arguments'] == {}, 'Actual normal observer route differs')
    copies = [x for x in response['native_receipts'] if x.get('copy') == Path(p['game_native']['path']).name]
    need(len(copies) == 1 and copies[0]['sha256'] == p['game_native']['sha256'] and
         same_path(copies[0]['path'], native['receipt_path']), 'Original dispatch native copy binding differs')
    result = contract(p).normalize_public_exit_observation_result(native['result'])
    before, after = result['process_preconfirm_pin'], result['process_observation']
    need(native['status'] == result['status'] == 'process_exit_observed_zero' and
         result['typed_normal_exit_observed'] is True and result['process_exit_observed'] is True and
         type(result['exit_code']) is int and result['exit_code'] == 0 and result['autosave_verified'] is False,
         'Actual typed normal exit plus original HANDLE exit0 required')
    need(before['pid'] == after['pid'] == IDENTITY['pid'] and before['creation_filetime_100ns'] ==
         after['creation_filetime_100ns'] == IDENTITY['process_creation_filetime_100ns'] and
         before['wait_result'] == 258 and before['retained_handle_token'] == after['retained_handle_token'] and
         after['wait_result'] == 0 and after['wait_state'] == 'signaled' and after['errors'] == [] and
         after['observed_monotonic_ns'] >= result['driver_dispatch_receipt_observed_monotonic_ns'] >= before['verified_monotonic_ns'],
         'Same original driver HANDLE/time/identity required')
    need(result['native_observation']['connection_generation'] == 1 and
         result['native_observation']['played_character_id'] == 31254 and result['native_observation']['native_revision'] == 32,
         'Actual same generation/actor/terminal revision differs')
    passive, capture = d['passive_game_exit'], d['passive_game_capture']
    need(passive['capture'] == p['passive_game_capture'] and passive['reopened_process'] is False and
         passive['external_passive_handle'] is True and passive['native_driver_handle'] is False and
         passive['typed_normal_exit_observed'] is False and passive['forced_exit'] is False,
         'Independent passive observer authority must remain separate from typed native result')
    original, observed = capture['original_identity'], passive['observation']
    need(capture['status'] == 'ORIGINAL_GAME_HANDLE_CAPTURED_ALIVE_BEFORE_UI_CLOSE' and original['wait_result'] == 258 and
         capture['initial_exit_code'] == 259 and capture['pid'] == IDENTITY['pid'] and
         capture['process_create_time'] == IDENTITY['process_create_time'] and passive['status'] == 'ORIGINAL_GAME_HANDLE_EXIT_OBSERVED' and
         all(observed[k] == original[k] for k in ('pid', 'creation_filetime_100ns', 'retained_handle_token')) and
         observed['creation_filetime_100ns'] == IDENTITY['process_creation_filetime_100ns'] and observed['wait_result'] == 0 and
         observed['wait_state'] == 'signaled' and observed['exit_code'] == 0 and observed['errors'] == [] and
         observed['process_identity_verified'] is True and observed['process_exit_observed'] is True, 'Independent original passive HANDLE exit0 required')
    helpers, holder = d['helper_capture'], d['holder_final']
    need(helpers['source_revision'] == HEAD and helpers['screen_task'] == TASK and helpers['client_session_id'] == CLIENT_SID and
         helpers['native_session_id'] == NATIVE_SID and helpers['holder_pid'] == 19748 and
         set(x['role'] for x in helpers['results']) == {'client', 'keeper'}, 'Original retained helper capture identity differs')
    roles = {x['role']: x for x in helpers['results']}
    for role, pid in (('client', 12236), ('keeper', 12940)):
        pin, row = roles[role], d[role + '_exit']
        need(pin['pid'] == pid and pin['handle_retained_before_close'] is True and pin['initial_wait_result'] == 258 and
             pin['initial_exit_code'] == 259 and all(row.get(k) == v for k, v in pin.items()) and
             row['status'] == 'ORIGINAL_PROCESS_EXIT_OBSERVED' and row['observation'] == 'ORIGINAL_RETAINED_HANDLE' and
             row['wait_result'] == row['exit_code'] == 0 and row['close_requested_by_observer'] is False,
             'Original ' + role + ' retained HANDLE exit0 required')
    need(holder['capture'] == p['helper_capture'] and holder['all_wait0_exit0'] is True and
         holder['results'] == [d['client_exit'], d['keeper_exit']], 'Holder FINAL must preserve both original exits')
    closed, close_response, close_request = d['consumer_closed'], d['consumer_close_result'], d['consumer_close_request']
    need(closed['attach_requested'] is True and close_response['status'] == 'CLIENT_CLOSE_REQUESTED' and
         close_request['operation'] == 'close' and close_request['request_id'] == close_response['request_id'] and
         close_response['request_sha256'] == p['consumer_close_request']['sha256'] and
         same_path(close_response['request_path'], p['consumer_close_request']['path']) and
         Path(p['consumer_close_request']['path']).name in closed['claimed_requests'], 'Original Client terminal close required')
    need(stamp(close_response['finished_at_utc']) <= stamp(closed['closed_at_utc']) <=
         stamp(d['client_exit']['observed_at_utc']) <= stamp(d['keeper_exit']['observed_at_utc']), 'Actual helper close order differs')
    executions = {role: execution(p[role + '_original_exec']) for role in ('client', 'keeper', 'holder', 'game_observer')}
    for role in ('client', 'keeper'):
        need(executions[role]['argv'] == roles[role]['cmdline'], 'Original ' + role + ' executed argv differs from retained capture')
    need(same_path(executions['holder']['argv'][-1], Path(p['helper_capture']['path']).parent) and
         same_path(executions['game_observer']['argv'][-1], Path(p['passive_game_capture']['path']).parent), 'Original observer output binding differs')
    final = d['keeper_final']
    need(final['task_id'] == TASK and final['last_sequence'] == 3706 and final['failure'] is None and final['entry_error'] is None and
         final['thread_exited'] is True and final['screen_released'] is False and final['game_actions'] is False, 'Actual clean keeper FINAL3706 required')
    release_exec, list_exec = execution(p['release_original_exec']), execution(p['after_list_original_exec'])
    release, listing = read(release_exec['stdout']), read(list_exec['stdout'])
    need(release['schema'] == 'codex.task_bus.v1' and release['ok'] is True and
         release['task']['task_id'] == release['event']['task_id'] == TASK and
         release['task']['resources'] == release['event']['resources'] == [] and release['task']['state'] == 'done' and
         release['event']['sequence'] == release['task']['last_sequence'] == 3707 and
         release['event']['sequence'] > final['last_sequence'] and release['event']['git']['head'] == HEAD, 'Actual R24 CAS3707 release required')
    argv = release_exec['argv']
    need('release-screen-cas' in argv and argv[argv.index('--task') + 1] == TASK and
         int(argv[argv.index('--expected-sequence') + 1]) == final['last_sequence'] and
         argv[argv.index('--expected-cli-sha256') + 1].lower() == CLI_SHA, 'Original CAS argv identity/pin differs')
    need(listing['schema'] == 'codex.task_bus.v1' and listing['ok'] is True and type(listing['tasks']) is list, 'Actual complete after-list required')
    own = [x for x in listing['tasks'] if x['task_id'] == TASK]
    need(len(own) == 1 and own[0]['resources'] == [] and own[0]['state'] == 'done' and own[0]['last_sequence'] == 3707,
         'After-list must retain genuine same released task')
    # Same existing 900-second fresh-owner definition, evaluated at original list time; no bus call.
    at = stamp(list_exec['finished_at_utc'])
    need(not any(x['state'] not in ('done', 'failed', 'cancelled') and 'ck3-screen:acquired' in x['resources'] and
                 at - stamp(x['updated_at_utc']) <= timedelta(seconds=900) for x in listing['tasks']), 'A fresh screen owner remains')
    census = d['process_absence']
    need(census['processes'] == census['errors'] == [] and set(census['known_pid_presence']) ==
         {'18364', '12236', '11356', '12940', '19748', '19048'} and
         all(x is False for x in census['known_pid_presence'].values()) and census['forced_termination'] is False and
         census['process_signals'] == census['SDK_calls'] == 0 and census['original_game_HANDLE_reopened'] is False,
         'Actual original six processes and managed-game absence required')
    need(stamp(census['observed_at_utc']) >= stamp(release['event']['timestamp_utc']) and
         all(stamp(census['observed_at_utc']) >= stamp(x['finished_at_utc']) for x in executions.values()) and
         stamp(list_exec['started_at_utc']) >= stamp(release['event']['timestamp_utc']), 'Actual postrelease evidence order differs')
    visual = d['final_offline_review']
    need(visual['schema'] == 'lyd.root.visual-offline-review.v1' and visual['steam_offline_confirmed'] is True and
         visual['game_launch_credit'] is False and type(visual['direct_original_image_review']) is str and
         stamp(visual['reviewed_at_utc']) >= stamp(release['event']['timestamp_utc']), 'ROOT final offline visual review required; no future launch credit')
    raw(visual['image']); frame = read(visual['fresh_frame_receipt'])
    need(frame['moving_edge_changed'] is True and frame['before_sha256'].lower() != frame['moved_sha256'].lower() and
         frame['moved_sha256'].lower() == visual['image']['sha256'] and same_path(frame['moved_path'], visual['image']['path']),
         'Actual reviewed moved-image freshness binding differs')
    limits = {'game_original_HANDLE_exit0_observed': True, 'game_exit_code': 0,
              'typed_normal_exit_observed': True, 'normal_exit_typed_green': True,
              'terminal_native_ack_observed': True, 'normal_exit_callback_verified': True,
              'closure_credit': 'TYPED_NORMAL_EXIT_AND_ORIGINAL_PROCESS_HANDLE_EXIT0',
              'client_exit_code': 0, 'keeper_exit_code': 0, 'client_OS_exit0_observed': True,
              'keeper_OS_exit0_observed': True, 'holder_original_exec_process_exit0_observed': True,
              'all_original_helper_exec_exit0_observed': True, 'screen_released_and_vacant': True,
              'fresh_no_game_or_original_owned_helpers_absence_verified': True,
              'native_session_id': NATIVE_SID, 'consumer_session_id': CLIENT_SID,
              'autosave_verified': False, 'business_GREEN': False,
              'independent_passive_game_HANDLE_exit0_observed': True,
              'independent_passive_observer_typed_credit': False}
    return {'actual_prior_identity': IDENTITY, 'actual_prior_source_head': HEAD, 'actual_prior_task': TASK,
            'operational_absence': True, 'normal_exit_typed_green': True,
            'actual_exit_observation_limits': limits, 'actual_release_sequence': 3707,
            'actual_original_exec_process_results': {role: p[role + '_original_exec'] for role in executions},
            'final_offline_review': p['final_offline_review'], 'refs': p}


def validate_previous_boundary_limits(value):
    limits = value['actual_exit_observation_limits']
    need(value['actual_prior_identity'] == IDENTITY and value['actual_prior_source_head'] == HEAD and
         value['actual_prior_task'] == TASK and value['operational_absence'] is True and
         value['normal_exit_typed_green'] is True, 'Exact genuine R24 predecessor required')
    need(all(limits[k] is True for k in ('game_original_HANDLE_exit0_observed', 'typed_normal_exit_observed',
         'normal_exit_typed_green', 'client_OS_exit0_observed', 'keeper_OS_exit0_observed',
         'all_original_helper_exec_exit0_observed', 'screen_released_and_vacant',
         'fresh_no_game_or_original_owned_helpers_absence_verified')) and
         limits['autosave_verified'] is False and limits['business_GREEN'] is False,
         'Typed lifecycle success cannot grant B4/B5 or autosave credit')


def helpers_value(p):
    return {'results': [read(p['client_exit']), read(p['keeper_exit'])],
            'original_capture': p['helper_capture'], 'retained_holder_final': p['holder_final'],
            'original_process_results': {role: p[role + '_original_exec'] for role in ('client', 'keeper', 'holder', 'game_observer')}}


def review_value(p, helpers):
    return {'schema': 'lyd.root.previous-cold-boundary-review.v3',
            'status': 'ROOT_REVIEWED_ACTUAL_CLOSED_RELEASED_BOUNDARY', 'source_head': HEAD,
            'root_screen_task': TASK, 'original_process': IDENTITY, 'launch': p['launch'],
            'original_handle_observation': p['game_sdk'], 'original_native_observation': p['game_native'],
            'helpers_closed': helpers, 'process_absence': p['process_absence'], 'keeper_final': p['keeper_final'],
            'release_receipt': read(p['release_original_exec'])['stdout'],
            'after_list': read(p['after_list_original_exec'])['stdout'], 'consumer_closed': p['consumer_closed'],
            'consumer_session': p['consumer_session'], 'consumer_close_result': p['consumer_close_result']}


def verify_previous_boundary_v3(item, legacy_context=None):
    need(type(item) is dict and set(item) == {'review'}, 'Existing review ref entry required')
    p = pins(); review = read(item['review'])
    need(set(review) == KEYS, 'Existing v3 exact16fields required')
    need(review == review_value(p, review['helpers_closed']) and read(review['helpers_closed']) == helpers_value(p),
         'Actual original review values/refs differ')
    value = checked(p); validate_previous_boundary_limits(value)
    refs = {k: review[k] for k in KEYS if type(review[k]) is dict and k != 'original_process'}
    for row in refs.values(): raw(row)
    return {'review': item['review'], **refs, **value}


def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review', type=Path); parser.add_argument('--sha256')
    parser.add_argument('--pins-sha256'); parser.add_argument('--output', type=Path)
    modes = parser.add_mutually_exclusive_group(); modes.add_argument('--check', action='store_true'); modes.add_argument('--create', action='store_true')
    args = parser.parse_args()
    if args.review:
        row = ref(args.review); need(args.sha256 and row['sha256'] == args.sha256.lower(), 'Actual review SHA required')
        print(json.dumps(verify_previous_boundary_v3({'review': row}), ensure_ascii=False)); return 0
    need((args.check or args.create) and args.pins_sha256 and
         ref(HERE / 'DEPENDENCIES.json')['sha256'] == args.pins_sha256.lower(), 'Explicit exact frozen actual pins and check/create required')
    p = pins(); value = checked(p); validate_previous_boundary_limits(value)
    if args.check:
        print(json.dumps({'status': 'ACTUAL_R24_TYPED_CLOSED_RELEASED_FACTS_VERIFIED', **value,
                          'SDK_calls': 0, 'OS_queries': 0, 'bus_calls': 0, 'body_reads': 0}, ensure_ascii=False)); return 0
    need(args.output is not None, 'Fresh boundary output required')
    out = args.output.resolve(); need(out.is_relative_to(BASE) and not out.exists(), 'Append-only external output required')
    out.mkdir(); put(out / 'HELPERS-CLOSED.actual.json', helpers_value(p))
    put(out / 'PREVIOUS-BOUNDARY.actual.json', review_value(p, ref(out / 'HELPERS-CLOSED.actual.json')))
    put(out / 'VERIFIED.actual.json', verify_previous_boundary_v3({'review': ref(out / 'PREVIOUS-BOUNDARY.actual.json')}))
    put(out / 'INDEX.json', {'status': 'ACTUAL_R24_TYPED_CLOSED_RELEASED_BOUNDARY_BUSINESS_NOT_GREEN',
         'review': ref(out / 'PREVIOUS-BOUNDARY.actual.json'), 'verifier': ref(__file__),
         'source_pins': ref(HERE / 'DEPENDENCIES.json'), 'closure_function': 'verify_previous_boundary_v3',
         'limits_function': 'validate_previous_boundary_limits', 'normal_exit_typed_green': True,
         'business_GREEN': False, 'autosave_verified': False, 'SDK_calls': 0, 'OS_queries': 0, 'bus_calls': 0, 'body_reads': 0})
    print(json.dumps({'review': ref(out / 'PREVIOUS-BOUNDARY.actual.json'), 'verifier': ref(__file__), 'index': ref(out / 'INDEX.json')})); return 0


if __name__ == '__main__':
    raise SystemExit(main())

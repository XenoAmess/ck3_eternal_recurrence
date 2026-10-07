"""R17 root-only post-game-exit close candidate. No SDK/game calls or PID reopen.

Without --execute-root-authorized this only validates existing facts. The root
must first complete B4/B5 and preserve the actual checkpoint. This program never
performs normal exit; it consumes the official original-HANDLE exit receipt.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib
import json
import subprocess
import sys
import time
import uuid
sys.dont_write_bytecode = True
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
RUN = Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017').resolve()
PYTHON = Path('C:/Users/Administrator/AppData/Local/Programs/Python/Python313/python.exe').resolve()
CLIENT = Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017/mcp-client-001').resolve()
QUEUE = Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017/queue-001').resolve()
CAPTURE_DIR = Path('C:/workspace/ck3_lyd_runtime_20261004/r17-retained-helper-handles-20261007-001/capture-001').resolve()
KEEPER = Path('C:/workspace/ck3_lyd_runtime_20261004/screen-lease-live-r0017').resolve()
HEAD = 'c706a74f9d00dd842b7edce8901fb3417344fd9c'
TASK = 'ck3-lyd-r17-original0240-formal-20261007-001'
GAME_PID = 14608
GAME_CREATE_TIME = 1791332614.2963333
CLIENT_SESSION = 'd0ce9f8302bb4ff8a474e9f091c4f1bd'
NATIVE_SESSION = '42abe9df32d34dd1840c23cb5246623d'
PROFILE_SHA = '80fa0ed760a7ea201bdff0347afde62d2a94ed333d5e21b8e87e4f20af0fb0a6'
CONTRACT = Path('C:/lr17s1/ck3_autonomous_player/src/xar_autoplayer/bridge/normal_exit_contract_v1.py')
CONTRACT_SHA = 'b794d7176c4928c5c74c22ce0cbb6894d18d74e787f3418512fec11b5ba5b942'
QUEUE_HELPER = Path('C:/workspace/ck3_lyd_runtime_20261004/r17-actual-consumer-source-20261007-001/persistent_native_mcp_queue_28.py')
QUEUE_HELPER_SHA = '56e53b3b3be226b5f22538d0bebc19ff5b7b3a7427fbc263d383cbbee8e4b25d'
BUS_CLI = Path('C:/workspace/ck3_eternal_recurrence/tools/codex_task_bus.py')
BUS_CLI_SHA = 'b3c44b42f7bdf401b593d863e3210106a46412dcd7d89f8596c74f4c27392dee'
BUS = Path('C:/workspace/.codex-task-bus')
PINS = {'capture':(Path('C:/workspace/ck3_lyd_runtime_20261004/r17-retained-helper-handles-20261007-001/capture-001/CAPTURED.actual.json'),'97fb74b5379953a1e8200f022a413cc93245ee629669311bba31fe81073a5b40'),'session':(Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017/mcp-client-001/session.json'),'fc65f8c218d722c6b12a29d25c3398cd1695f7c9d70cf41b0d55b4138f0965bd'),'keeper_ready':(Path('C:/workspace/ck3_lyd_runtime_20261004/screen-lease-live-r0017/READY.json'),'b7497e81d22e7be5e52f9d8a66c55146ad7d78b035d90471d90d333e4bfff974'),'runtime_bindings':(Path('C:/workspace/ck3_lyd_runtime_20261004/r17-helper-identity-holder-inputs-20261007-001/RUNTIME.actual.json'),'16a4ab8c15b9ff4be82b53d1394856cc0c2f8c139165f23f333d02d387ed540e')}

def need(ok, message):
    if not ok:
        raise ValueError(message)

def now():
    return datetime.now(timezone.utc).isoformat()

def stamp(value):
    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
    need(value.tzinfo is not None, 'Aware actual timestamp required')
    return value

def plain(path):
    path = Path(path).absolute()
    for parent in (path, *path.parents):
        need(not parent.is_symlink() and (not parent.is_junction()), 'Linked input/output refused')
    return path.resolve()

def ref(path):
    path = plain(path)
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def read(path, sha=None):
    row = ref(path)
    if sha is not None:
        need(row['sha256'] == sha.lower(), 'Actual bytes/SHA changed: ' + str(path))
    return (json.loads(Path(row['path']).read_bytes()), row)

def verify_byte_ref(row):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'Exact existing ref3 required')
    actual = ref(row['path'])
    need(actual['sha256'] == row['sha256'].lower() and actual['bytes'] == row['bytes'], 'Actual ref3 bytes/SHA changed')
    return Path(actual['path']).read_bytes()

def read_ref(row):
    return json.loads(verify_byte_ref(row))

def put(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def fixed():
    need(Path(sys.executable).resolve() == PYTHON, 'Verified Python313 required')
    values, refs = ({}, {})
    for key, (path, sha) in PINS.items():
        values[key], refs[key] = read(path, sha)
    capture, session = (values['capture'], values['session'])
    need(capture['status'] == 'ORIGINAL_CLIENT_AND_KEEPER_HANDLES_CAPTURED_ALIVE_BEFORE_CLOSE' and capture['holder_pid'] == 14208 and (capture['holder_create_time'] == 1791333766.1629004) and (capture['source_revision'] == HEAD) and (capture['screen_task'] == TASK) and (capture['client_session_id'] == CLIENT_SESSION) and (capture['native_session_id'] == NATIVE_SESSION) and (capture['game_handle_opened'] is False), 'Actual retained-helper capture differs')
    verify_byte_ref(capture['holder_source'])
    read_ref(capture['request'])
    need(session['client_session_id'] == CLIENT_SESSION and session['source_revision'] == HEAD and (session['profile_sha256'] == PROFILE_SHA) and (session['target'] == {'pid': GAME_PID, 'process_create_time': GAME_CREATE_TIME}) and (plain(session['queue']) == QUEUE) and (session['automatic_attach'] is False) and (session['automatic_retry'] is False) and (session['cache'] is None), 'Original Client session differs')
    _, refs['profile'] = read(session['profile'], PROFILE_SHA)
    need(not (CAPTURE_DIR / 'FAILURE.actual.json').exists(), 'Passive original HANDLE holder failed; stop')
    need(not (CLIENT / 'session-terminated.json').exists(), 'Client transport terminated; stop')
    return (values, refs)

def live_identity(pid, creation_time, argv):
    import psutil
    process = psutil.Process(pid)
    need(process.create_time() == creation_time and plain(process.exe()) == PYTHON and (process.cmdline() == argv), 'Original helper identity no longer alive or differs; never reopen/replace: ' + str(pid))

def holder_alive(values):
    import psutil
    capture = values['capture']
    process = psutil.Process(capture['holder_pid'])
    argv = process.cmdline()
    need(process.create_time() == capture['holder_create_time'] and plain(process.exe()) == PYTHON, 'Original passive holder identity differs')
    need(len(argv) == 12 and plain(argv[0]) == PYTHON and (argv[1:4] == ['-B', '-X', 'utf8']) and (plain(argv[4]) == plain(capture['holder_source']['path'])) and (argv[5] == 'hold') and (argv[6] == '--request') and (plain(argv[7]) == plain(capture['request']['path'])) and (argv[8] == '--sha256') and (argv[9].lower() == capture['request']['sha256'].lower()) and (argv[10] == '--output') and (plain(argv[11]) == CAPTURE_DIR), 'Existing holder must retain its original source/request/output; never restart it')

def role_pin(values, role):
    rows = [row for row in values['capture']['results'] if row['role'] == role]
    need(len(rows) == 1, 'Exactly one original helper role required')
    row = rows[0]
    expected = (13408, 1791333031.5885065) if role == 'client' else (20436, 1791332451.9545596)
    need((row['pid'], row['create_time']) == expected and row['handle_local_to_holder_pid'] == 14208 and (row['handle_retained_before_close'] is True) and (row['initial_wait_result'] == 258) and (row['initial_exit_code'] == 259), 'Original helper capture pin differs')
    return row

def game_exit_observation_limits(result):
    typed = result['typed_normal_exit_observed']
    need(type(typed) is bool, 'Actual typed observation must remain an exact boolean')
    if typed is False:
        need(result['schema'] == 'ck3-normal-exit-process-observation-result-v1' and result['native_observation'] is None and result['driver_dispatch_receipt_observed_monotonic_ns'] is None and result['native_submission_count'] == 0, 'Untyped closure admits only the existing read-only original-HANDLE observer with missing terminal native ACK; no semantic callback credit')
    return {'typed_normal_exit_observed': typed, 'terminal_native_ack_observed': result['native_observation'] is not None, 'normal_exit_callback_verified': typed, 'closure_credit': 'ORIGINAL_PROCESS_HANDLE_EXIT0_ONLY' if not typed else 'TYPED_NORMAL_EXIT_AND_ORIGINAL_PROCESS_HANDLE_EXIT0'}

def game_exit(args, values):
    sdk, sdk_ref = read(args.game_sdk, args.game_sdk_sha256)
    native, native_ref = read(args.game_native, args.game_native_sha256)
    need(plain(args.game_sdk).parent == CLIENT and plain(args.game_native).parent == CLIENT, 'Consume original current Client SDK and its preserved native copy')
    need(sdk.get('resultType') == 'complete' and sdk.get('isError') is False and (sdk.get('structuredContent') == native) and (type(sdk.get('content')) is list) and (len(sdk['content']) >= 1) and (json.loads(sdk['content'][0]['text']) == native), 'Complete official SDK/native/text result must agree exactly')
    need(native.get('schema') == 'ck3.native-profile-receipt.v1' and native.get('session_id') == NATIVE_SESSION and (native.get('profile_sha256') == PROFILE_SHA), 'Original native session/profile differs')
    original, original_ref = read(native['receipt_path'])
    need(RUN / 'native-evidence' in plain(native['receipt_path']).parents and original == native and (original_ref['sha256'] == native_ref['sha256']), 'Original native receipt and Client copy differ')
    prefix = plain(args.game_sdk).name.removesuffix('.sdk-result.json')
    response, response_ref = read(CLIENT / (prefix + '.response.json'))
    need(response['status'] == 'MCP_RESULT_RECORDED' and (response.get('is_error') is None or response.get('is_error') is False) and (response['sdk_result'] == sdk_ref['path'].split('/')[-1]) and (response['sdk_result_sha256'] == sdk_ref['sha256']), 'Actual dispatch did not record this SDK result')
    copies = [row for row in response['native_receipts'] if row.get('copy') == native_ref['path'].split('/')[-1]]
    need(len(copies) == 1 and copies[0]['sha256'] == native_ref['sha256'] and (plain(copies[0]['path']) == plain(native['receipt_path'])), 'Actual dispatch native copy/source/SHA differs')
    packet, packet_ref = read(response['request_path'], response['request_sha256'])
    need(plain(response['request_path']).parent == QUEUE and packet['operation'] == 'call_tool' and (packet['request_id'] == response['request_id']), 'Original queue request differs')
    result = native['result']
    need(ref(CONTRACT)['sha256'] == CONTRACT_SHA, 'Exact source typed validator changed')
    sys.path.insert(0, str(CONTRACT.parent))
    contract = importlib.import_module('normal_exit_contract_v1')
    if result.get('schema') == 'ck3-normal-exit-request-result-v1':
        need(packet['name'] == 'ck3_request_normal_exit_v1' and packet['arguments']['action'] == 'confirm_desktop' and (result.get('native_submission_count') == 1), 'Actual one terminal submission required')
        contract.normalize_public_exit_result(result, action='confirm_desktop', expected_revision=packet['arguments']['expected_revision'])
    elif result.get('schema') == 'ck3-normal-exit-process-observation-result-v1':
        need(packet['name'] == 'ck3_observe_profile_normal_exit_v1' and packet['arguments'] == {}, 'Actual retained observer request required')
        contract.normalize_public_exit_observation_result(result)
    else:
        raise ValueError('Only named actual terminal request/observation schemas admitted')
    before, observed = (result['process_preconfirm_pin'], result['process_observation'])
    need(native['status'] == result['status'] == 'process_exit_observed_zero' and (result['process_exit_observed'] is True) and (result['exit_code'] == 0) and (result['claim_consumed'] is True) and (result['retry_authorized'] is False) and (result['autosave_verified'] is False) and (result['snapshot_after_required'] is False), 'Actual original game HANDLE exit0 required; preserve typed/native ACK limits and grant no retry or autosave credit')
    need(before['pid'] == observed['pid'] == GAME_PID and before['wait_result'] == 258 and (before['creation_filetime_100ns'] == observed['creation_filetime_100ns']) and (before['retained_handle_token'] == observed['retained_handle_token']) and (observed['wait_result'] == 0) and (observed['wait_state'] == 'signaled') and (observed['exit_code'] == 0) and (observed['process_identity_verified'] is True) and (observed['process_exit_observed'] is True) and (observed['errors'] == []), 'Original game same HANDLE exit0 proof missing')
    limits = game_exit_observation_limits(result)
    return {**limits, 'game_sdk': sdk_ref, 'game_native': native_ref, 'original_game_native': original_ref, 'game_dispatch': response_ref, 'game_request': packet_ref, 'game_result_schema': result['schema'], 'game_original_pid': GAME_PID, 'game_original_creation_filetime_100ns': before['creation_filetime_100ns'], 'game_original_create_time': GAME_CREATE_TIME, 'autosave_verified': False, 'dispatch_is_error_original': response.get('is_error'), 'SDK_isError_original': sdk['isError']}

def role_exit(values, role):
    pin = role_pin(values, role)
    row, row_ref = read(CAPTURE_DIR / ('EXIT-' + role + '.actual.json'))
    need(all((row.get(key) == value for key, value in pin.items())), 'Passive original HANDLE facts differ from capture')
    need(row['status'] == 'ORIGINAL_PROCESS_EXIT_OBSERVED' and row['observation'] == 'ORIGINAL_RETAINED_HANDLE' and (row['wait_result'] == 0) and (row['exit_code'] == 0) and (row['close_requested_by_observer'] is False), 'Original helper HANDLE exit0 not observed; preserve unknown/nonzero and stop')
    return (row, row_ref)

def closed_client(values):
    row, handle_ref = role_exit(values, 'client')
    closed, closed_ref = read(CLIENT / 'session-closed.json')
    need(closed['attach_requested'] is True and (not (CLIENT / 'session-terminated.json').exists()), 'Actual normal Client completion required')
    matches = []
    for path in CLIENT.glob('*.response.json'):
        response, _ = read(path)
        if response.get('status') == 'CLIENT_CLOSE_REQUESTED':
            matches.append(path)
    need(len(matches) == 1, 'Exactly one actual claimed Client close required')
    response, response_ref = read(matches[0])
    request, request_ref = read(response['request_path'], response['request_sha256'])
    need(set(request) == {'schema', 'request_id', 'operation'} and request['schema'] == 'ck3.lyd.mcp-request.v1' and (request['operation'] == 'close') and (request['request_id'] == response['request_id']) and (plain(response['request_path']).parent == QUEUE) and (Path(response['request_path']).name in closed['claimed_requests']), 'Actual terminal Client close differs')
    need(stamp(values['session']['started_at_utc']) <= stamp(response['started_at_utc']) <= stamp(response['finished_at_utc']) <= stamp(closed['closed_at_utc']) <= stamp(row['observed_at_utc']), 'Actual Client/HANDLE close timestamp order differs')
    return {'consumer_closed': closed_ref, 'consumer_close_result': response_ref, 'consumer_close_request': request_ref, 'client_original_handle_exit': handle_ref}

def keeper_closed(values):
    client_facts = closed_client(values)
    client, _ = role_exit(values, 'client')
    keeper, keeper_ref = role_exit(values, 'keeper')
    holder_final, holder_ref = read(CAPTURE_DIR / 'FINAL.actual.json')
    need(holder_final['capture'] == ref(PINS['capture'][0]) and holder_final['all_wait0_exit0'] is True and (holder_final['results'] == [client, keeper]), 'Original passive holder final does not preserve both exits')
    final, final_ref = read(KEEPER / 'FINAL.json')
    need(final['task_id'] == TASK and final['failure'] is None and (final['entry_error'] is None) and (final['thread_exited'] is True) and (final['screen_released'] is False) and (final['game_actions'] is False) and (type(final['last_sequence']) is int), 'Actual keeper clean FINAL required; it does not release screen')
    need(stamp(keeper['observed_at_utc']) >= stamp(read_ref(client_facts['consumer_closed'])['closed_at_utc']), 'Keeper exit predates Client close')
    request = read_ref(values['capture']['request'])
    declared = request['processes']['keeper']
    need(declared['pid'] == keeper['pid'] and declared['create_time'] == keeper['create_time'] and (declared['cmdline'] == keeper['cmdline']), 'Original keeper request identity differs')
    need(values['keeper_ready']['lease']['task_id'] == TASK and values['keeper_ready']['lease']['checkout_head'] == HEAD, 'Original keeper READY differs')
    rows = [client, {**keeper, 'source': ref(PINS['keeper_ready'][0])}]
    return {**client_facts, 'keeper_original_handle_exit': keeper_ref, 'retained_holder_final': holder_ref, 'keeper_final': final_ref, 'keeper_last_sequence': final['last_sequence'], 'helpers_closed_value': {'results': rows}}

def wait_file(path, timeout):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if (CAPTURE_DIR / 'FAILURE.actual.json').exists() or (CLIENT / 'session-terminated.json').exists():
            raise RuntimeError('Original holder/Client failure detected; stop without next action')
        if Path(path).exists():
            try:
                return read(path)
            except json.JSONDecodeError:
                pass
        time.sleep(0.25)
    raise TimeoutError('Original fact not yet available; no retry or next action: ' + str(path))

def run_record(out, name, argv):
    put(out / (name + '.argv.json'), {'argv': argv, 'started_at_utc': now()})
    proc = subprocess.run(argv, cwd=BASE, capture_output=True)
    with (out / (name + '.stdout')).open('xb') as stream:
        stream.write(proc.stdout)
    with (out / (name + '.stderr')).open('xb') as stream:
        stream.write(proc.stderr)
    put(out / (name + '.actual.json'), {'argv': argv, 'exit_code': proc.returncode, 'finished_at_utc': now(), 'stdout': ref(out / (name + '.stdout')), 'stderr': ref(out / (name + '.stderr'))})
    need(proc.returncode == 0, 'Actual helper command failed; originals retained, no retry/next action: ' + name)
    return json.loads(proc.stdout)

def prepare_action(args, values):
    if args.command == 'close-client':
        holder_alive(values)
        pin = role_pin(values, 'client')
        live_identity(pin['pid'], pin['create_time'], pin['cmdline'])
        pin = role_pin(values, 'keeper')
        live_identity(pin['pid'], pin['create_time'], pin['cmdline'])
        need(not (CAPTURE_DIR / 'EXIT-client.actual.json').exists() and (not (KEEPER / 'STOP.request').exists()), 'Close or stop already happened; do not replay')
        need(not (CLIENT / 'session-closed.json').exists(), 'Original Client already closed; do not replay')
        for path in QUEUE.glob('*.request.json'):
            packet, _ = read(path)
            need(packet['operation'] != 'close', 'Close already published; do not retry')
            need(len(list(CLIENT.glob('*-' + packet['request_id'] + '.response.json'))) == 1, 'An explicit SDK request is still pending; root owns queue')
        need(ref(QUEUE_HELPER)['sha256'] == QUEUE_HELPER_SHA, 'Pinned formal consumer28 enqueue source changed')
        return {}
    if args.command == 'stop-keeper':
        facts = closed_client(values)
        holder_alive(values)
        pin = role_pin(values, 'keeper')
        live_identity(pin['pid'], pin['create_time'], pin['cmdline'])
        need(not (KEEPER / 'STOP.request').exists() and (not (CAPTURE_DIR / 'EXIT-keeper.actual.json').exists()), 'Keeper stop/exit already happened; do not replay')
        return facts
    if args.command == 'release-screen':
        facts = keeper_closed(values)
        need(ref(BUS_CLI)['sha256'] == BUS_CLI_SHA, 'Pinned task bus CLI changed')
        return facts
    return {}

def execute(args, values, out):
    if args.command == 'close-client':
        request_id = 'r17-root-close-' + uuid.uuid4().hex
        packet = {'schema': 'ck3.lyd.mcp-request.v1', 'request_id': request_id, 'operation': 'close'}
        source = out / 'CLIENT-CLOSE.request.json'
        put(source, packet)
        run_record(out, 'enqueue-client-close', [str(PYTHON), '-B', '-X', 'utf8', str(QUEUE_HELPER), 'enqueue', '--queue', str(QUEUE), '--request', str(source)])
        wait_file(CLIENT / 'session-closed.json', args.wait_seconds)
        wait_file(CAPTURE_DIR / 'EXIT-client.actual.json', args.wait_seconds)
        return closed_client(values)
    if args.command == 'stop-keeper':
        put(KEEPER / 'STOP.request', {'requested_at_utc': now(), 'requested_by': 'explicit root-authorized R17 helper', 'client_handle_exit': ref(CAPTURE_DIR / 'EXIT-client.actual.json')})
        put(out / 'KEEPER-STOP.publication.json', {'path': (KEEPER / 'STOP.request').as_posix(), 'request': ref(KEEPER / 'STOP.request'), 'published_at_utc': now()})
        wait_file(CAPTURE_DIR / 'EXIT-keeper.actual.json', args.wait_seconds)
        wait_file(CAPTURE_DIR / 'FINAL.actual.json', args.wait_seconds)
        facts = keeper_closed(values)
        put(out / 'HELPERS-CLOSED.actual.json', facts.pop('helpers_closed_value'))
        return {**facts, 'helpers_closed': ref(out / 'HELPERS-CLOSED.actual.json')}
    facts = keeper_closed(values)
    argv = [str(PYTHON), '-B', '-X', 'utf8', str(BUS_CLI), '--bus-dir', str(BUS), '--expected-cli-sha256', BUS_CLI_SHA.upper(), 'release-screen-cas', '--task', TASK, '--expected-sequence', str(facts['keeper_last_sequence']), '--summary', args.summary]
    release = run_record(out, 'release-screen-cas', argv)
    put(out / 'RELEASE.actual.json', release)
    need(release.get('ok') is True and release['task']['task_id'] == release['event']['task_id'] == TASK and (release['task']['resources'] == release['event']['resources'] == []) and (release['task']['state'] == 'done') and (release['event']['sequence'] > facts['keeper_last_sequence']), 'Actual CAS not done/released; preserve waiting/conflict/unknown and stop, never relabel/retry')
    listing = run_record(out, 'after-list', [str(PYTHON), '-B', '-X', 'utf8', str(BUS_CLI), '--bus-dir', str(BUS), '--expected-cli-sha256', BUS_CLI_SHA.upper(), 'list'])
    put(out / 'BUS-AFTER-RELEASE.parsed.json', listing)
    need(listing.get('ok') is True and (not any(('ck3-screen:acquired' in row['resources'] for row in listing['tasks']))), 'Actual screen vacancy not observed')
    return {'release_receipt': ref(out / 'RELEASE.actual.json'), 'after_list': ref(out / 'BUS-AFTER-RELEASE.parsed.json'), 'remaining_boundary_work': 'root actual post-release process absence, actual checkpoint review and original-ref boundary verifier'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check-source', 'check-game-exit', 'close-client', 'stop-keeper', 'release-screen'])
    parser.add_argument('--game-sdk', required=False, type=Path)
    parser.add_argument('--game-sdk-sha256', required=False)
    parser.add_argument('--game-native', required=False, type=Path)
    parser.add_argument('--game-native-sha256', required=False)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--execute-root-authorized', action='store_true', help='Only root may explicitly select this after actual B5/checkpoint preservation; never sends normal-exit tools')
    parser.add_argument('--wait-seconds', type=int, default=90)
    parser.add_argument('--summary', default='R17 actual original HANDLE game/helper exit0, normal Client closure, keeper stopped; release retained screen')
    args = parser.parse_args()
    need(1 <= args.wait_seconds <= 300, 'Bounded actual observation wait required')
    values, pins = fixed()
    if args.command == 'check-source':
        need(not args.execute_root_authorized, 'Source check has no mutation mode')
        for path, sha in [(CONTRACT, CONTRACT_SHA), (QUEUE_HELPER, QUEUE_HELPER_SHA), (BUS_CLI, BUS_CLI_SHA)]:
            need(ref(path)['sha256'] == sha, 'Exact existing source changed: ' + str(path))
        profile, profile_ref = read(values['session']['profile'], PROFILE_SHA)
        inventory, inventory_ref = read(profile['normal_exit_source_inventory']['path'], profile['normal_exit_source_inventory']['sha256'])
        print(json.dumps({'status': 'ACTUAL_R17_SOURCE_AND_CAPTURE_REFS_BOUND_NO_ACTION', 'pins': pins, 'profile': profile_ref, 'normal_exit_inventory': inventory_ref, 'original_client_handle': role_pin(values, 'client'), 'original_keeper_handle': role_pin(values, 'keeper'), 'future_game_exit0': None, 'future_client_exit0': None, 'future_keeper_exit0': None, 'future_CAS_release': None, 'SDK_calls': 0, 'game_calls': 0, 'process_identity_lookups': 0, 'OpenProcess_calls': 0, 'main_writes': 0}, ensure_ascii=False, indent=2))
        return 0
    need(all((args.game_sdk, args.game_sdk_sha256, args.game_native, args.game_native_sha256)), 'Actual game SDK/native refs and SHA are mandatory; future NULL rejected')
    game = game_exit(args, values)
    phase = prepare_action(args, values)
    if not args.execute_root_authorized:
        print(json.dumps({'status': 'EXISTING_FACTS_VALIDATED_NO_ACTION', 'command': args.command, 'game': game, 'pins': pins, 'phase': phase, 'SDK_calls': 0, 'game_calls': 0, 'close_requested': False, 'stop_requested': False, 'release_requested': False}, ensure_ascii=False, indent=2))
        return 0
    need(args.command != 'check-game-exit', 'Pure game-exit check has no execution mode')
    need(args.output is not None, 'Fresh explicit external output required')
    out = plain(args.output)
    need(BASE in out.parents and (not out.exists()), 'Fresh external output required; old failures stay unchanged')
    out.mkdir()
    put(out / 'INPUTS.actual.json', {'command': args.command, 'authorized_by': 'explicit root --execute-root-authorized', 'candidate': ref(__file__), 'game': game, 'pins': pins, 'phase': phase, 'started_at_utc': now()})
    try:
        result = execute(args, values, out)
        put(out / 'RESULT.actual.json', {'status': 'ACTUAL_REQUESTED_PHASE_COMPLETE', 'command': args.command, 'result': result, 'SDK_calls': 0, 'game_calls': 0, 'finished_at_utc': now(), 'autosave_verified': False})
        print(json.dumps({'result': ref(out / 'RESULT.actual.json'), 'value': result}, ensure_ascii=False, indent=2))
        return 0
    except BaseException as error:
        put(out / 'FAILURE.actual.json', {'status': 'ERROR_STOP_NO_RETRY_NO_NEXT_ACTION', 'command': args.command, 'error': type(error).__name__ + ': ' + str(error), 'observed_at_utc': now(), 'SDK_calls': 0, 'game_calls': 0})
        raise
if __name__ == '__main__':
    raise SystemExit(main())

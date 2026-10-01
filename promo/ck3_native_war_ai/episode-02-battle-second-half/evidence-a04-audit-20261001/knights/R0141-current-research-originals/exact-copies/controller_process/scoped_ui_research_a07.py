"""One source-bound research day and independently read original UI frames.

This is a research consumer, not a video renderer or a human review signer.
Each request and output is exclusive-create. Ambiguous mutations are never retried.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import time

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def write(path, body):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

BOUND_NATIVE_SESSION = None

def bind(config):
    global BOUND_NATIVE_SESSION
    source = Path(config['source_root']).resolve()
    live = Path(config['live_root']).resolve()
    output = live / 'ck3-output'
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    require(head == config['source_commit'], 'Research source HEAD differs')
    require(not subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=source, text=True).strip(), 'Frozen research source is dirty')
    for pin in config['pins']:
        actual = identity(pin['path'])
        require(actual['bytes'] == pin['bytes'] and actual['sha256'] == pin['sha256'].upper(), 'Changed research input: ' + str(pin['path']))
    live_id = read(output / 'live-run-identity.json')
    require(len(live_id['identities']) == 1 and live_id['identities'][0]['run_id'] == config['run_id'], 'Wrong live run')
    preflight = read(output / 'preflight.json')
    require(preflight['checkpoint_source']['date_raw'] == config['before_date_raw'] and
            preflight['checkpoint_source']['actor'] == config['actor_id'], 'Wrong checkpoint scope')
    for key in ('bridge_dll', 'bridge_injector'):
        actual = identity(config[key])
        require(preflight[key]['sha256'].upper() == actual['sha256'] and preflight[key]['bytes'] == actual['bytes'], 'Runtime binary pairing differs: ' + key)
    BOUND_NATIVE_SESSION = config['native_session_binding']
    sys.path.insert(0, str(source / 'promo/ck3_native_war_ai/episode-02-battle-second-half'))
    transport = importlib.import_module('pursuit_live_step')
    steps = importlib.import_module('remaining_live_step')
    evidence = live / 'scoped-ui-research-attempt-01'
    evidence.mkdir(exist_ok=True)
    return live, output, evidence, transport, steps

def snapshot(output, transport, steps, label, date_raw):
    body, receipt = transport.call(output, label, 'ck3_take_snapshot', {}, 120)
    ok, values = steps.snapshot_case(body, date_raw, require_combat=True)
    require(ok, 'Research paused snapshot identity/date/combat differs')
    diagnostics = body.get('diagnostics', {})
    hello = diagnostics.get('hello', {})
    observed_session = {'episode_run_id': body.get('episode_run_id'), 'connection_generation': diagnostics.get('connection_generation'), 'bridge_pid': diagnostics.get('bridge_pid'), 'native_hello_session_generation': hello.get('session_generation')}
    require(BOUND_NATIVE_SESSION is not None and observed_session == BOUND_NATIVE_SESSION, 'Current native session differs from actual admitted start snapshot')
    require(type(values['native_revision']) is int and values['native_revision'] > 0 and isinstance(values['snapshot_id'], str) and values['snapshot_id'] == 'native:' + str(values['native_revision']), 'Native snapshot ID/revision unavailable or inconsistent')
    values.update(observed_session)
    return body, receipt, values

def capture_window(live, evidence, label):
    import psutil
    import win32gui
    import win32process
    sys.path.insert(0, 'D:/workspace/ck3_native_war_ai_promo_work/desktop-capture-freeze-static-20260927/wgc-lib')
    from windows_capture import WindowsCapture, Frame, InternalCaptureControl
    games = [p for p in psutil.process_iter(['name', 'cmdline']) if (p.info['name'] or '').lower() == 'ck3.exe']
    require(len(games) == 1, 'CK3 process count differs')
    game = games[0]
    require(BOUND_NATIVE_SESSION is not None and game.pid == BOUND_NATIVE_SESSION['bridge_pid'], 'Original WGC process is not this admitted native PID')
    require(str(live / 'ck3-state/profile').replace('\\', '/').lower() in
            ' '.join(game.info['cmdline']).replace('\\', '/').lower(), 'Not this isolated userdir')
    windows = []
    def enum(hwnd, unused):
        if win32gui.IsWindowVisible(hwnd) and win32process.GetWindowThreadProcessId(hwnd)[1] == game.pid:
            rect = win32gui.GetWindowRect(hwnd)
            if rect[2] - rect[0] > 500 and rect[3] - rect[1] > 300:
                windows.append(hwnd)
    win32gui.EnumWindows(enum, None)
    require(len(windows) == 1, 'Original CK3 HWND ambiguous')
    hwnd = windows[0]
    path = evidence / (label + '-window.png')
    require(not path.exists(), 'Original frame already exists')
    frames = []
    capture = WindowsCapture(cursor_capture=False, draw_border=None, window_hwnd=hwnd)
    @capture.event
    def on_frame_arrived(frame: Frame, control: InternalCaptureControl):
        if not path.exists():
            frame.save_as_image(str(path))
            frames.append({'at_utc': datetime.now(timezone.utc).isoformat(), 'width': frame.width, 'height': frame.height})
        control.stop()
    @capture.event
    def on_closed():
        pass
    control = capture.start_free_threaded()
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and not path.exists() and not control.is_finished():
        time.sleep(.1)
    control.stop()
    if control.is_finished():
        control.wait()
    require(path.is_file(), 'No original CK3 window frame')
    receipt = {'kind': 'original WGC HWND frame', 'pid': game.pid, 'creation_time': game.create_time(), 'hwnd': hwnd,
               'title': win32gui.GetWindowText(hwnd), 'rect': win32gui.GetWindowRect(hwnd), 'frames': frames,
               'image': identity(path), 'mouse_inputs': 0, 'keyboard_inputs': 0, 'visual_review': 'pending root original-pixel inspection'}
    write(evidence / (label + '-window-receipt.json'), receipt)
    return receipt

def original_gui_owner_identity(body):
    require(body.get('application_owner_thread_verified') is True and body.get('gui_owner_binding_verified') is True,
            'Original application thread or GUI object binding not verified')
    require(body.get('rng_owner_is_ui_admission_gate') is False, 'RNG ownership cannot substitute for UI ownership')
    for key in ('gui_context_address', 'gui_owner_address'):
        require(type(body.get(key)) is int and 0 < body[key] < 2**64, 'No actual original GUI pointer: ' + key)
    require(type(body.get('thread_id')) is int and 0 < body['thread_id'] < 2**32, 'No actual original application owner thread')
    require(type(body.get('rng_owner_thread_id')) is int and 0 <= body['rng_owner_thread_id'] < 2**32,
            'Missing actual RNG diagnostic; zero must remain zero')
    return (body['thread_id'], body['gui_context_address'], body['gui_owner_address'])

def verify_window(body, kind, subject_id, values, config):
    original_gui_owner_identity(body)
    expected = {'schema': 'ck3-ingame-ui-window-v1', 'accepted': True, 'available': True, 'status': 'observed',
                'window_kind': kind, 'window_exists': True, 'effective_visible': True, 'subject_id_available': True,
                'current_subject_id': subject_id, 'date_raw': values['date_raw'], 'paused': True,
                'played_character_id': config['actor_id'], 'queried_revision': values['revision'],
                'queried_native_revision': values['native_revision'], 'native_revision': values['native_revision'],
                'queried_snapshot_id': values['snapshot_id'], 'requested_subject_id': 0,
                'episode_run_id': values['episode_run_id'], 'queried_connection_generation': values['connection_generation'],
                'dispatch_invoked': False, 'verification_pending': False}
    for key, value in expected.items():
        require(type(body.get(key)) is type(value) and body.get(key) == value, 'Window postcondition differs: ' + key)
    require(type(body.get('thread_id')) is int and 0 < body['thread_id'] < 2**32 and type(body.get('pump_epoch')) is int and 0 < body['pump_epoch'] < 2**64, 'No strict UI owner execution stamp')
    if kind == 'knights':
        require(body.get('owner_character_id') == config['actor_id'], 'Knights eligible-list owner differs')

def original_ui(args, config, bound):
    live, output, evidence, transport, steps = bound
    date = config['before_date_raw'] if args.phase == 'before' else config['after_date_raw']
    kind = args.window_kind
    tools = {'character': ('ck3_open_character_window_v1', {'character_id': config[args.character_role + '_id']}, config[args.character_role + '_id']),
             'army': ('ck3_select_army_ui_v1', {'subject_army_id': config['public_unit_id']}, config['public_unit_id']),
             'combat': ('ck3_open_combat_window_v1', {'combat_id': config['combat_id']}, config['combat_id']),
             'knights': ('ck3_open_knights_window_v1', {}, config['actor_id'])}
    name, parameters, subject = tools[kind]
    before, br, values = snapshot(output, transport, steps, args.label + '-source-snapshot', date)
    action, ar = transport.call(output, args.label + '-open', name, {**parameters, 'expected_revision': values['revision']}, 120)
    require(action.get('accepted') is True and action.get('verification_pending') is True, 'Typed presentation action was not admitted')
    fresh, fr, fv = snapshot(output, transport, steps, args.label + '-query-source-snapshot', date)
    require(fv == values, 'Presentation action changed the admitted paused source/session')
    result, qr = transport.call(output, args.label + '-readback', 'ck3_query_ingame_ui_window_v1',
                                {'window_kind': kind, 'expected_revision': fv['revision']}, 120)
    verify_window(result, kind, subject, fv, config)
    image = capture_window(live, evidence, args.label)
    post, pr, pv = snapshot(output, transport, steps, args.label + '-post-pixels-snapshot', date)
    require(pv == fv, 'Paused source changed while capturing pixels')
    again, gr = transport.call(output, args.label + '-post-pixels-window-readback', 'ck3_query_ingame_ui_window_v1',
                               {'window_kind': kind, 'expected_revision': pv['revision']}, 120)
    verify_window(again, kind, subject, pv, config)
    require(original_gui_owner_identity(result) == original_gui_owner_identity(again), 'Original GUI owner changed around the character/army/window frame')
    record = {'at_utc': datetime.now(timezone.utc).isoformat(), 'source_binding': identity(args.bindings), 'phase': args.phase,
              'source_snapshot': br, 'source_values': values, 'action': ar, 'action_body': action, 'query_snapshot': fr,
              'query_values': fv, 'readback': qr, 'readback_body': result, 'image': image, 'post_pixels_snapshot': pr,
              'post_pixels_values': pv, 'post_pixels_readback': gr, 'post_pixels_readback_body': again,
              'visual_review': 'pending', 'human_movie_signoff': False,
              'knights_scope': 'eligible military list, not active combat roster' if kind == 'knights' else None}
    write(evidence / (args.label + '-original-ui-binding.json'), record)
    print(json.dumps({'result': 'ORIGINAL_UI_CAPTURED_PENDING_VISUAL_REVIEW', 'record': str(evidence / (args.label + '-original-ui-binding.json'))}))

def knight_hover(args, config, bound):
    live, output, evidence, transport, steps = bound
    date = config['before_date_raw'] if args.phase == 'before' else config['after_date_raw']
    before, br, values = snapshot(output, transport, steps, args.label + '-source-snapshot', date)
    action, ar = transport.call(output, args.label + '-native-hover', 'ck3_hover_combat_knights_v1',
              {'combat_id': config['combat_id'], 'ui_side': args.ui_side, 'expected_revision': values['revision']}, 120)
    require(action.get('accepted') is True and action.get('verification_pending') is True, 'Original knight hover not admitted')
    # Let the stock tooltip use its own dwell timing. This is not a game-day step.
    time.sleep(1)
    fresh, fr, fv = snapshot(output, transport, steps, args.label + '-query-source-snapshot', date)
    require(fv == values, 'Native hover changed the admitted paused source/session')
    result, qr, stable_observations = stable_combat_window(output, transport, steps, args.label, fv, config)
    def hover_gate(body, current_values):
        verify_window(body, 'combat', config['combat_id'], current_values, config)
        require(body.get('combat_knights_read_available') is True and body.get('hover_state_available') is True,
                'Original knight getter or current hover state unavailable')
        require(body.get('hovered_widget_name') == args.ui_side + '_knights' and body.get('hovered_ui_side') == args.ui_side and
                body.get('hovered_combat_id') == config['combat_id'], 'Current hover target is not this battle side')
        require(body.get('hover_readback_is_pixels') is False and body.get('combat_roster_full_ids_available') is False,
                'Do not upgrade UI markup/counts into pixel inspection or native full roster IDs')
    hover_gate(result, fv)
    geometry_gate(result, config, True)
    image = capture_window(live, evidence, args.label)
    post, pr, pv = snapshot(output, transport, steps, args.label + '-post-pixels-snapshot', date)
    require(pv == fv, 'Paused source changed during tooltip pixels')
    again, gr = transport.call(output, args.label + '-post-pixels-window-readback', 'ck3_query_ingame_ui_window_v1',
                              {'window_kind': 'combat', 'expected_revision': pv['revision']}, 120)
    hover_gate(again, pv)
    require(original_gui_owner_identity(result) == original_gui_owner_identity(again), 'Original GUI owner changed around the knight tooltip frame')
    require(geometry_gate(again, config, True) == geometry_gate(result, config, True), 'Knight tooltip geometry changed around original frame')
    require(all(result.get(field) == again.get(field) for field in
                ('left_knight_count', 'right_knight_count', 'left_knight_breakdown', 'right_knight_breakdown')),
            'Original counts or breakdown changed around the frame')
    record = {'at_utc': datetime.now(timezone.utc).isoformat(), 'source_binding': identity(args.bindings), 'phase': args.phase,
              'ui_side': args.ui_side, 'source_snapshot': br, 'source_values': values, 'action': ar, 'action_body': action,
              'query_snapshot': fr, 'query_values': fv, 'readback': qr, 'readback_body': result, 'image': image,
              'post_pixels_snapshot': pr, 'post_pixels_values': pv, 'post_pixels_readback': gr,
              'post_pixels_readback_body': again, 'visual_review': 'pending root original tooltip pixel inspection',
              'stable_read_only_observations': stable_observations,
              'full_id_ordered_roster_source': 'same-run managed phase ring, independently bound',
              'mouse_inputs': 0, 'keyboard_inputs': 0, 'human_movie_signoff': False}
    write(evidence / (args.label + '-original-knights-tooltip-binding.json'), record)
    print(json.dumps({'result': 'ORIGINAL_KNIGHTS_TOOLTIP_CAPTURED_PENDING_VISUAL_REVIEW',
                     'record': str(evidence / (args.label + '-original-knights-tooltip-binding.json'))}))




def stable_combat_window(output, transport, steps, label, values, config):
    previous = None
    previous_epoch = None
    original_thread = None
    observations = []
    for index in range(8):
        body, receipt = transport.call(output, label + '-stable-query-' + str(index), 'ck3_query_ingame_ui_window_v1',
                      {'window_kind': 'combat', 'expected_revision': values['revision']}, 120)
        verify_window(body, 'combat', config['combat_id'], values, config)
        if original_thread is None:
            original_thread = body['thread_id']
        require(body['thread_id'] == original_thread, 'Original GUI owner thread changed during stable read')
        require(previous_epoch is None or body['pump_epoch'] > previous_epoch, 'Original GUI owner epoch repeated or regressed')
        geometry = geometry_gate(body, config, False)
        observations.append({'native_receipt': receipt, 'body': body})
        comparable = {key: body.get(key) for key in ('combat_geometry', 'left_knight_count', 'right_knight_count',
                       'left_knight_breakdown', 'right_knight_breakdown', 'hovered_widget_name', 'hovered_ui_side', 'hovered_combat_id', 'gui_context_address', 'gui_owner_address')}
        if geometry.get('content_inside_viewport') is True and geometry.get('fit_required') is False and previous == comparable and previous_epoch is not None and body['pump_epoch'] > previous_epoch:
            geometry_gate(body, config, True)
            return body, receipt, observations
        previous = comparable
        previous_epoch = body['pump_epoch']
        time.sleep(.2)
    raise RuntimeError('Original combat layout did not converge in bounded read-only queries; no repeated action')

def geometry_gate(body, config, require_inside):
    import math
    geometry = body.get('combat_geometry', {})
    require(geometry.get('available') is True and geometry.get('combat_id') == config['combat_id'] and
            geometry.get('coordinate_space') == 'native_gui_absolute', 'No current original combat geometry')
    require(geometry.get('stock_margin_source_verified') is True and
            geometry.get('stock_margin_source_sha256') == '7FEE98B7341E21607ED3BB9089C51EF890D229DB6C16865C88133C3BA3579236',
            'Stock combat background margin source not verified')
    require(geometry.get('readback_is_pixels') is False and geometry.get('full_panel_pixels_proven') is False,
            'Geometry is not actual full-panel pixel review')
    require(body.get('tree', {}).get('truncated') is False, 'Combat subtree is truncated')
    for name in ('viewport', 'window_rect', 'content_union'):
        rectangle = geometry.get(name, {})
        require(all(type(rectangle.get(axis)) in (int, float) and math.isfinite(rectangle[axis]) for axis in
                    ('x', 'y', 'width', 'height')), 'Invalid original rectangle: ' + name)
        require(rectangle['width'] > 0 and rectangle['height'] > 0, 'Empty original rectangle: ' + name)
    if require_inside:
        viewport, content = geometry['viewport'], geometry['content_union']
        require(geometry.get('content_inside_viewport') is True and geometry.get('fit_required') is False,
                'Full native visible-content union still exceeds viewport')
        epsilon = 0.01
        require(content['x'] >= viewport['x'] - epsilon and content['y'] >= viewport['y'] - epsilon and
                content['x'] + content['width'] <= viewport['x'] + viewport['width'] + epsilon and
                content['y'] + content['height'] <= viewport['y'] + viewport['height'] + epsilon,
                'Independent original geometry bounds disagree')
    return geometry

def fit_combat_panel(args, config, bound):
    live, output, evidence, transport, steps = bound
    date = config['before_date_raw'] if args.phase == 'before' else config['after_date_raw']
    before, br, values = snapshot(output, transport, steps, args.label + '-source-snapshot', date)
    initial, ir = transport.call(output, args.label + '-initial-geometry', 'ck3_query_ingame_ui_window_v1',
                    {'window_kind': 'combat', 'expected_revision': values['revision']}, 120)
    verify_window(initial, 'combat', config['combat_id'], values, config)
    geometry_gate(initial, config, False)
    action, ar = transport.call(output, args.label + '-native-fit-once', 'ck3_fit_combat_window_v1',
                    {'combat_id': config['combat_id'], 'expected_revision': values['revision']}, 120)
    require(action.get('accepted') is True and action.get('verification_pending') is True, 'Original combat layout action not admitted')
    fresh, fr, fv = snapshot(output, transport, steps, args.label + '-query-source-snapshot', date)
    require(fv == values, 'UI layout action changed the paused gameplay snapshot')
    result, qr, stable_observations = stable_combat_window(output, transport, steps, args.label, fv, config)
    verify_window(result, 'combat', config['combat_id'], fv, config)
    actual = geometry_gate(result, config, True)
    image = capture_window(live, evidence, args.label)
    post, pr, pv = snapshot(output, transport, steps, args.label + '-post-pixels-snapshot', date)
    require(pv == fv, 'Paused source changed during full-panel original frame')
    again, gr = transport.call(output, args.label + '-post-pixels-readback', 'ck3_query_ingame_ui_window_v1',
                    {'window_kind': 'combat', 'expected_revision': pv['revision']}, 120)
    verify_window(again, 'combat', config['combat_id'], pv, config)
    require(original_gui_owner_identity(result) == original_gui_owner_identity(again), 'Original GUI owner changed around the full combat panel frame')
    require(geometry_gate(again, config, True) == actual, 'Original combat geometry changed around frame')
    target = evidence / (args.label + '-full-combat-panel-binding.json')
    write(target, {'source_binding': identity(args.bindings), 'phase': args.phase, 'source_snapshot': br,
          'source_values': values, 'initial_geometry_receipt': ir, 'initial_geometry_body': initial,
          'action': ar, 'action_body': action, 'query_snapshot': fr, 'query_values': fv,
          'readback': qr, 'readback_body': result, 'stable_read_only_observations': stable_observations,
          'image': image, 'post_pixels_snapshot': pr,
          'post_pixels_values': pv, 'post_pixels_readback': gr, 'post_pixels_readback_body': again,
          'mouse_inputs': 0, 'keyboard_inputs': 0, 'visual_review': 'pending actual original-pixel review of all panel rows',
          'human_movie_signoff': False})
    print(json.dumps({'result': 'ORIGINAL_FULL_PANEL_CAPTURED_PENDING_PIXEL_REVIEW', 'record': identity(target)}))

def monitor_payload(envelope):
    found = []
    def visit(value, path):
        if isinstance(value, dict):
            if 'scoped_variable_monitor' in value:
                found.append((path + ['scoped_variable_monitor'], value['scoped_variable_monitor']))
            for key, child in value.items():
                if key != 'scoped_variable_monitor':
                    visit(child, path + [key])
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + [index])
    visit(envelope, [])
    require(len(found) == 1 and isinstance(found[0][1], dict), 'One exact scoped_variable_monitor payload required')
    return found[0]

def variable_monitor(args, config, bound):
    live, output, evidence, transport, steps = bound
    beginning = args.mode == 'monitor-begin'
    prefix = 'variable-monitor-begin' if beginning else 'variable-monitor-finish'
    require(not (evidence / (prefix + '-intent.json')).exists(), 'Monitor request already submitted; never retry')
    if beginning:
        require(not (evidence / 'one-day-intent.json').exists(), 'Monitor must precede UI and the day')
    else:
        require((evidence / 'variable-monitor-begin.json').is_file(), 'No bound monitor begin')
        require((evidence / 'one-day-finished.json').is_file() and (evidence / 'after-saved-pair.json').is_file(), 'Finish after day, UI and immutable save')
        reviewed = read(evidence / 'after-ui-root-review.json')
        require(reviewed.get('original_pixels_actually_reviewed') is True, 'After-day original pixels not reviewed')
        for image in reviewed['reviewed_images']:
            require(identity(image['path']) == image, 'Reviewed after-day bytes changed')
    date = config['before_date_raw'] if beginning else config['after_date_raw']
    source, sr, values = snapshot(output, transport, steps, prefix + '-snapshot', date)
    token = config['monitor_sequence_token']
    require(type(token) is int and 0 < token < 2**64 and token != config['managed_daily_sequence_token'], 'Independent fresh monitor token required')
    parameters = {'action': 'private_phase_trace',
                  'step': 'experimental-scoped-character-variable-monitor-' + ('begin' if beginning else 'finish') + '-v1',
                  'expected_revision': values['revision'], 'monitor_sequence_token': token}
    if beginning:
        parameters.update(scoped_character_id=config['victim_id'], scoped_related_character_id=config['killer_id'])
    write(evidence / (prefix + '-intent.json'), {'source_binding': identity(args.bindings), 'source_snapshot': sr,
          'source_values': values, 'request_parameters': parameters, 'no_gameplay_write': True})
    body, receipt = steps.private_call(output, prefix + '-once', parameters, 120)
    require(body.get('accepted') is True and body.get('status') == ('armed' if beginning else 'drained'), 'Independent monitor not accepted in the required lifecycle stage')
    path, payload = monitor_payload(body)
    expected = {'schema_version': 1, 'monitor_sequence_token': token,
                'character_ids': [config['victim_id'], config['killer_id']],
                'begin_date_raw': config['before_date_raw'], 'failure_flags': 0, 'truncated': False,
                'whole_game_mutable_bundle_complete': False, 'battle_event_causality_inferred_from_endpoint': False}
    for key, value in expected.items():
        require(type(payload.get(key)) is type(value) and payload.get(key) == value, 'Monitor binding differs: ' + key)
    require(payload.get('detours_uninstalled') is (not beginning), 'Monitor hook lifecycle differs')
    require(isinstance(payload.get('records'), list) and all(record.get('failure_flags') == 0 for record in payload['records']), 'Monitor records contain failure')
    result_path = evidence / (prefix + '.json')
    write(result_path, {'source_binding': identity(args.bindings), 'source_snapshot': sr, 'source_values': values,
          'native_receipt': receipt, 'native_envelope': body, 'exact_payload_path': path, 'scoped_variable_monitor': payload,
          'status': 'ARMED_BEFORE_UI' if beginning else 'DRAINED_PENDING_INDEPENDENT_SEMANTIC_VERIFICATION',
          'human_movie_signoff': False})
    print(json.dumps({'result': 'MONITOR_ARMED' if beginning else 'MONITOR_DRAINED_SEMANTICS_PENDING', 'record': identity(result_path)}))

def save(args, config, bound):
    live, output, evidence, transport, steps = bound
    date = config['before_date_raw'] if args.phase == 'before' else config['after_date_raw']
    body, br, values = snapshot(output, transport, steps, args.label + '-save-source', date)
    saved, sr = transport.call(output, args.label + '-save', 'ck3_save_checkpoint', {'expected_revision': values['revision']}, 120)
    checkpoint = saved.get('checkpoint', {})
    require(saved.get('accepted') is True and checkpoint.get('status') == 'saved' and checkpoint.get('date_raw') == date, 'Native checkpoint refused')
    original = identity(checkpoint['path'])
    require(original['bytes'] == checkpoint['size'] and original['sha256'] == checkpoint['sha256'].upper(), 'Checkpoint bytes differ')
    target = evidence / (args.phase + '-immutable.ck3')
    require(not target.exists(), 'Saved pair phase already exists')
    shutil.copyfile(original['path'], target)
    require(identity(target)['sha256'] == original['sha256'], 'Save copy changed bytes')
    write(evidence / (args.phase + '-saved-pair.json'), {'phase': args.phase, 'source_values': values, 'snapshot': br,
          'save': sr, 'save_body': saved, 'immutable': identity(target), 'source_binding': identity(args.bindings)})
    print(json.dumps({'result': 'CHECKPOINT_PRESERVED', 'phase': args.phase, 'immutable': identity(target)}))

def advance(args, config, bound):
    live, output, evidence, transport, steps = bound
    require((evidence / 'before-saved-pair.json').is_file(), 'Before immutable save missing')
    require((evidence / 'variable-monitor-begin.json').is_file() and not (evidence / 'variable-monitor-finish-intent.json').exists(), 'Independent monitor must remain armed across day')
    review = read(evidence / 'before-ui-root-review.json')
    require(review.get('original_pixels_actually_reviewed') is True, 'Original pre-day UI pixels not reviewed')
    for reviewed in review['reviewed_images']:
        require(identity(reviewed['path']) == reviewed, 'Reviewed original bytes changed')
    require(not (evidence / 'one-day-intent.json').exists(), 'One day already submitted; never retry')
    start, br, values = snapshot(output, transport, steps, 'scoped-day-source-snapshot', config['before_date_raw'])
    token = config['managed_daily_sequence_token']
    require(type(token) is int and 0 < token < 2**64, 'Declared positive unique token missing')
    parameters = {'action': 'private_phase_trace', 'step': 'experimental-combat-phase-event-trace-begin-v1',
                  'expected_revision': values['revision'], 'combat_id': config['combat_id'],
                  'managed_daily_sequence_token': token, 'checkpoint_sequence': 1,
                  'capture_runtime_scoped_chain': True, 'scoped_character_id': config['victim_id'],
                  'scoped_related_character_id': config['killer_id'], 'scoped_event_load_index': config['event_load_index']}
    begun, bgr = steps.private_call(output, 'scoped-chain-begin', parameters, 120)
    require(begun.get('accepted') is True and begun.get('managed_daily_sequence_token') == token, 'Scoped trace begin refused; no day')
    write(evidence / 'one-day-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'source_values': values,
          'source_snapshot': br, 'token': token, 'trace_begin': bgr, 'trace_begin_body': begun, 'at_most_one_day': True})
    changed, adr = transport.call(output, 'scoped-one-day', 'ck3_execute_step', {'step': 'life-advance', 'expected_revision': values['revision']}, 150)
    require(changed.get('ending_date_raw') == config['after_date_raw'], 'Single submitted day ambiguous; no retry')
    # Proven trace ordering: snapshot only while armed, FINISH once, then queries/UI/saves.
    end, er, ev = snapshot(output, transport, steps, 'scoped-post-day-snapshot-only', config['after_date_raw'])
    finished, tr = steps.private_call(output, 'scoped-chain-finish-once', {'action': 'private_phase_trace',
                'step': 'experimental-combat-phase-event-trace-finish-v1', 'expected_revision': ev['revision'],
                'combat_id': config['combat_id'], 'managed_daily_sequence_token': token}, 120)
    write(evidence / 'one-day-finished.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'one_day': adr,
          'one_day_body': changed, 'post_day_snapshot': er, 'post_day_values': ev, 'trace_finish': tr,
          'trace_finish_body': finished, 'source_binding': identity(args.bindings),
          'complete_causal_chain': 'pending independent records/save verification'})
    print(json.dumps({'result': 'ONE_DAY_AND_TRACE_FINISH_RETURNED_PENDING_VERIFICATION', 'values': ev}))

def finish(args, config, bound):
    live, output, evidence, transport, steps = bound
    pending = output / 'interactive-requests/scoped-research-owner-finish.json.pending'
    target = pending.with_suffix('')
    require(not target.exists() and not pending.exists(), 'Owner finish already submitted')
    write(pending, {'action': 'finish'})
    os.rename(pending, target)
    print(json.dumps({'finish_submitted': str(target), 'cleanup_pending': True}))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bindings', required=True, type=Path)
    parser.add_argument('--mode', required=True, choices=['ui', 'hover', 'fit', 'save', 'advance', 'monitor-begin', 'monitor-finish', 'finish'])
    parser.add_argument('--phase', choices=['before', 'after'])
    parser.add_argument('--window-kind', choices=['character', 'army', 'combat', 'knights'])
    parser.add_argument('--character-role', choices=['victim', 'killer'], default='victim')
    parser.add_argument('--ui-side', choices=['left', 'right'])
    parser.add_argument('--label', default='scoped-research')
    args = parser.parse_args()
    if args.mode in {'ui', 'hover', 'fit', 'save'}:
        require(args.phase is not None, 'Phase required')
    if args.mode == 'ui':
        require(args.window_kind is not None, 'Typed window kind required')
    if args.mode == 'hover':
        require(args.ui_side is not None, 'Explicit combat UI side required')
    require(args.label and all(c.isalnum() or c in '-_' for c in args.label), 'Invalid exclusive request label')
    config = read(args.bindings)
    bound = bind(config)
    if args.mode in {'ui', 'hover', 'fit', 'save'}:
        evidence = bound[2]
        require((evidence / 'variable-monitor-begin.json').is_file() and not (evidence / 'variable-monitor-finish-intent.json').exists(), 'Observe variable writers before UI/save getters')
    {'ui': original_ui, 'hover': knight_hover, 'fit': fit_combat_panel, 'save': save, 'advance': advance, 'monitor-begin': variable_monitor, 'monitor-finish': variable_monitor, 'finish': finish}[args.mode](args, config, bound)

if __name__ == '__main__':
    main()

"""Independent decision text process. No window creation, Game input or OBS API.

TEXT_PUBLISHED proves an exact file publication by this process, never OBS draw.
The source-qualification mode is explicit and can never pass a recording gate.
"""
from __future__ import annotations
import argparse
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

SCHEMA = 'xar.ck3.decision-text-publisher/v1'
ACK_SCHEMA = 'xar.ck3.decision-text-published/v1'
TITLE = '智能体实时决策'
LIMIT = 32768

def utc(): return datetime.now(timezone.utc).isoformat()

def read(path, limit=LIMIT):
    with Path(path).open('rb') as stream: raw = stream.read(limit + 1)
    if len(raw) > limit: raise ValueError('Decision metadata exceeds its finite limit')
    return json.loads(raw)

def pin(path, limit=LIMIT):
    path = Path(path).resolve(strict=True)
    with path.open('rb') as stream: raw = stream.read(limit + 1)
    if len(raw) > limit: raise ValueError('Only bounded decision metadata may be pinned')
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def checked(reference, limit=LIMIT):
    if pin(reference['path'], limit) != reference: raise ValueError('Exact decision metadata pin differs')
    return read(reference['path'], limit)

def atomic(path, value, *, new=False):
    path = Path(path)
    data = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
    if len(data) > LIMIT: raise ValueError('Decision metadata exceeds32KiB')
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    with temp.open('xb') as stream: stream.write(data)
    try:
        if new: os.link(temp, path)
        else: os.replace(temp, path)
    finally: temp.unlink(missing_ok=True)

def process_identity(pid):
    """Read a live Windows process generation without enumerating windows."""
    if os.name != 'nt': raise RuntimeError('Production process custody requires Windows')
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    k.OpenProcess.restype = ctypes.c_void_p
    k.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(ctypes.c_uint64)] * 4
    k.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    k.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    k.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = k.OpenProcess(0x1000 | 0x100000, False, int(pid))
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    try:
        stamps = [ctypes.c_uint64() for _ in range(4)]
        if k.WaitForSingleObject(handle, 0) != 258: raise RuntimeError('Publisher/Game process is not live')
        if not k.GetProcessTimes(handle, *(ctypes.byref(x) for x in stamps)): raise ctypes.WinError(ctypes.get_last_error())
        size = ctypes.c_uint32(32768); image = ctypes.create_unicode_buffer(size.value)
        if not k.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(size)): raise ctypes.WinError(ctypes.get_last_error())
        return {'pid': int(pid), 'creation_filetime': stamps[0].value, 'executable': str(Path(image.value).resolve())}
    finally: k.CloseHandle(handle)

def source_pin(): return pin(Path(__file__), 128 * 1024)

def source_pins():
    return {'publisher': source_pin(), 'view': pin(Path(__file__).with_name('decision_text_view.py'))}

def validate_config(config):
    if config.get('schema') != SCHEMA or not isinstance(config.get('machine_id'), str): raise ValueError('Explicit publisher configuration required')
    session = Path(config['session']).resolve(strict=True)
    for key in ('state_root', 'decision_text_file', 'current_request_path', 'feed_root'):
        if not Path(config[key]).resolve().is_relative_to(session): raise ValueError('Publisher path escaped session: ' + key)
    fixture = config.get('qualification_only') is True
    if type(config.get('qualification_only')) is not bool: raise ValueError('Explicit qualification mode required')
    if not fixture:
        game = config.get('game') or {}
        if any(type(game.get(key)) is not int or game[key] <= 0 for key in ('pid', 'creation_filetime', 'hwnd')) or not game.get('desktop_id') or not game.get('creation_date'):
            raise ValueError('Exact Game/desktop generation binding required')
        launch = checked(config['game_launch_receipt'])
        if launch.get('pid') != game['pid'] or launch.get('creation_filetime') != game['creation_filetime'] or launch.get('creation_date') != game['creation_date']:
            raise ValueError('Actual Game launch differs from publisher configuration')
    return session

def validate_started(reference, *, game=None, machine_id=None, identity_reader=process_identity, recording=True):
    started = checked(reference)
    if (started.get('schema') != SCHEMA or started.get('status') != 'DECISION_TEXT_PUBLISHER_STARTED'
            or started.get('publisher_sources') != source_pins() or started.get('creates_legacy_window') is not False
            or started.get('OBS_draw_ack') is not False): raise ValueError('Actual independent publisher STARTED required')
    config = checked(started['configuration']); validate_config(config)
    if recording and (started.get('qualified_for_game_recording') is not True or config.get('qualification_only') is not False):
        raise ValueError('A software fixture cannot qualify Game recording')
    if machine_id is not None and started['machine_id'] != machine_id: raise ValueError('Publisher machine differs')
    if started['game'] != config.get('game'): raise ValueError('Publisher Game binding differs from its configuration')
    if game is not None and any(started['game'].get(k) != game.get(k) for k in ('pid', 'creation_filetime', 'hwnd', 'desktop_id')):
        raise ValueError('Publisher belongs to another actual Game or desktop')
    if identity_reader(started['publisher']['pid']) != started['publisher']: raise ValueError('Live publisher PID/creation time/executable differs')
    if any(started[k] != config[k] for k in ('session', 'state_root', 'decision_text_file')): raise ValueError('Publisher paths differ')
    return started

def ack_path(started, source_reference):
    return Path(started['state_root']) / ('TEXT-PUBLISHED-' + source_reference['sha256'] + '.json')

def enqueue_observation(source, started):
    source = Path(source).resolve(strict=True); session = Path(started['session']).resolve()
    if not source.is_relative_to(session): raise ValueError('Observation escaped actual publisher session')
    reference = pin(source)
    root = Path(started['state_root']); destination = root / ('INPUT-' + reference['sha256'] + '.json')
    lock = root / 'INPUT-PUBLISH.lock'
    lock_stream = lock.open('x')
    try:
        with lock_stream:
            current = root / 'CURRENT-INPUT.json'
            if current.exists():
                prior = checked(read(current)['input'])
                if prior['source_observation'] != reference and not ack_path(started, prior['source_observation']).exists():
                    raise RuntimeError('An earlier exact text input is still pending; no overwrite')
            if not destination.exists(): atomic(destination, {'source_observation': reference}, new=True)
            atomic(current, {'input': pin(destination)})
    finally: lock.unlink(missing_ok=True)
    return reference

def wait_text_published(source, publisher_started_pin, *, timeout_seconds=5, identity_reader=process_identity, recording=True):
    """Call after the real before_submit source is written, before returning to SDK."""
    if not 0 < timeout_seconds <= 30: raise ValueError('Finite text ACK timeout required')
    started = validate_started(publisher_started_pin, identity_reader=identity_reader, recording=recording)
    reference = enqueue_observation(source, started); target = ack_path(started, reference)
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if target.exists():
            ack = read(target)
            if (ack.get('schema') != ACK_SCHEMA or ack.get('status') != 'TEXT_PUBLISHED'
                    or ack.get('source_observation') != reference or ack.get('publisher') != started['publisher']
                    or ack.get('publisher_started') != publisher_started_pin or ack.get('OBS_draw_ack') is not False
                    or ack.get('machine_id') != started['machine_id']): raise ValueError('Exact publisher text ACK differs')
            if identity_reader(started['publisher']['pid']) != started['publisher']: raise RuntimeError('Publisher exited before ACK consumption')
            return ack
        time.sleep(.02)
    raise TimeoutError('Exact text publication not observed; no OBS drawn or business-submitted claim')

def validate_observation(row, source, config):
    request = row.get('request') or {}; tool = request.get('tool')
    if tool != 'root_before_auto_turn_submit':
        origin = Path(row.get('source_ref', '')).resolve()
        context = read(config['current_request_path'])
        sequence = request.get('sequence')
        if (Path(source).parent != Path(config['feed_root']).resolve() or not origin.is_relative_to(Path(config['session']).resolve())
                or origin.parent.name != row.get('source_namespace') or not origin.is_file()
                or type(sequence) is not int or origin.name != f'{sequence:04d}-1-result.json'
                or context.get('sequence') != sequence or context.get('tool') != tool
                or not isinstance(row.get('result'), dict)):
            raise ValueError('Actual bounded result projection and its explicit origin required')
        return row['result'].get('structured_content') or {}
    result = row.get('result') or {}; body = result.get('structured_content') or {}
    if result.get('is_error') is not False or body.get('status') != 'planned': raise ValueError('Actual planned observation required')
    plan = body.get('plan') or {}
    if body.get('selected_step') != plan.get('selected_step'): raise ValueError('Selected display step differs from actual plan')
    callback = row.get('source') == 'actual GameplayBridgeService.before_submit callback'
    if callback:
        context = read(config['current_request_path'])
        sequence = request.get('parent_sequence')
        if type(sequence) is not int or context.get('sequence') != sequence or context.get('tool') != 'ck3_auto_turn':
            raise ValueError('Before-submit observation is not the currently held auto-turn request')
        if Path(source).name != f'{sequence:04d}-0-plan.json': raise ValueError('Actual callback source filename differs')
        game = config['game']
        if row.get('game_pid') != game['pid'] or row.get('game_creation_date') != game['creation_date']:
            raise ValueError('Actual callback belongs to another Game')
    elif not (row.get('actual_auto_turn_call') is False and row.get('actual_Service_callback') is False
              and row.get('business_submitted') is False and row.get('display_protocol_alias_only') is True
              and isinstance(row.get('origin'), str)):
        raise ValueError('Manual notice must truthfully identify its non-Service origin')
    return body

def read_text_binding(reference, *, game, identity_reader=process_identity):
    started = validate_started(reference, game=game, identity_reader=identity_reader)
    path = Path(started['decision_text_file'])
    binding = read(path.with_name(path.name + '.binding.json'))
    if (binding.get('schema') != SCHEMA or binding.get('publisher') != started['publisher']
            or binding.get('game') != started['game'] or binding.get('decision_text_file') != str(path)
            or binding.get('configuration') != started['configuration'] or binding.get('publisher_sources') != started['publisher_sources']
            or binding.get('binding_hidden_from_video') is not True): raise ValueError('Exact hidden text publisher binding differs')
    with path.open('rb') as stream: raw = stream.read(LIMIT + 1)
    if len(raw) > LIMIT or not raw.decode('utf-8').startswith(TITLE + '\n'): raise ValueError('Bounded generic decision text is absent')
    return started

def publish_text(path, text):
    raw = text.encode('utf-8')
    if not text.startswith(TITLE + '\n') or len(raw) > LIMIT: raise ValueError('Generic bounded decision text required')
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.pending')
    with temp.open('xb') as stream: stream.write(raw)
    try: os.replace(temp, path)
    finally: temp.unlink(missing_ok=True)
    return hashlib.sha256(raw).hexdigest()

def run(config_path):
    config = read(config_path); session = validate_config(config)
    state = Path(config['state_root']); started_path = state / 'STARTED.json'
    if started_path.exists(): raise FileExistsError('Publisher generation already started; no replay')
    actual = process_identity(os.getpid())
    if not config['qualification_only'] and process_identity(config['game']['pid'])['creation_filetime'] != config['game']['creation_filetime']:
        raise ValueError('Game birth changed before publisher start')
    from decision_text_view import AudienceState
    view = AudienceState(); text_path = Path(config['decision_text_file'])
    if text_path.exists(): raise FileExistsError('A new publisher requires its own text file')
    publish_text(text_path, view.render())
    binding = {'schema': SCHEMA, 'machine_id': config['machine_id'], 'game': config.get('game'), 'publisher': actual,
               'decision_text_file': str(text_path), 'configuration': pin(config_path), 'publisher_sources': source_pins(), 'binding_hidden_from_video': True}
    atomic(text_path.with_name(text_path.name + '.binding.json'), binding, new=True)
    started = {'schema': SCHEMA, 'status': 'DECISION_TEXT_PUBLISHER_STARTED', 'machine_id': config['machine_id'], 'at_utc': utc(),
               'publisher': actual, 'publisher_sources': source_pins(), 'configuration': pin(config_path), 'game': config.get('game'),
               'session': str(session), 'state_root': str(state), 'decision_text_file': str(text_path),
               'qualified_for_game_recording': not config['qualification_only'], 'creates_legacy_window': False, 'OBS_draw_ack': False}
    atomic(started_path, started, new=True); started_pin = pin(started_path)
    signature = None; first_error = None
    try:
        while not (state / 'STOP').exists():
            if not config['qualification_only']:
                identity = process_identity(config['game']['pid'])
                if identity['creation_filetime'] != config['game']['creation_filetime']: raise RuntimeError('Exact Game generation changed')
            pointer = state / 'CURRENT-INPUT.json'
            if pointer.exists():
                current = read(pointer); key = current['input']['sha256']
                if key != signature:
                    input_row = checked(current['input']); reference = input_row['source_observation']; target = ack_path(started, reference)
                    if not target.exists():
                        row = checked(reference); validate_observation(row, reference['path'], config)
                        request = row.get('request') or {}
                        sequence = request.get('sequence', request.get('parent_sequence'))
                        key_order = (sequence, 0 if request.get('tool') == 'root_before_auto_turn_submit' else 1)
                        if type(sequence) is not int or key_order < view.last_key:
                            raise ValueError('Out-of-order decision would be ignored; do not acknowledge it as published')
                        view.consume(row); digest = publish_text(text_path, view.render())
                        atomic(target, {'schema': ACK_SCHEMA, 'status': 'TEXT_PUBLISHED', 'machine_id': config['machine_id'], 'at_utc': utc(),
                          'publisher': actual, 'publisher_started': started_pin, 'source_observation': reference,
                          'text_sha256': digest, 'decision_text_file': str(text_path), 'OBS_draw_ack': False,
                          'publication_scope': 'bounded_actual_observation_only',
                          'qualification_only': config['qualification_only'], 'business_submission_or_outcome_inferred': False}, new=True)
                    signature = key
            time.sleep(.02)
    except BaseException as error:
        first_error = {'type': type(error).__name__, 'message': str(error)}
        raise
    finally:
        atomic(state / 'CLOSED.json', {'schema': SCHEMA, 'machine_id': config['machine_id'], 'publisher': actual,
          'publisher_started': started_pin, 'at_utc': utc(), 'first_error': first_error,
          'normal_STOP_observed': (state / 'STOP').exists(), 'kernel_exit_not_self_observable': True}, new=True)

class PublisherOwner:
    """Retain the real original Popen handle. No terminate/kill or blind retry."""
    def __init__(self, config_path):
        self.config_path = Path(config_path).resolve(); self.config = read(self.config_path); validate_config(self.config)
        self.root = Path(self.config['state_root']); self.process = None

    def start(self):
        self.root.mkdir(parents=True, exist_ok=True)
        intent = self.root / 'LAUNCH-INTENT.json'
        if intent.exists(): raise RuntimeError('Publisher launch intent exists; outcome unknown, do not launch again')
        # On Windows a venv python.exe may be a redirector that creates another
        # PID. Launch the actual engine already executing this owner so the
        # original retained Popen handle identifies the publisher itself.
        actual_owner = process_identity(os.getpid())
        worker_python = actual_owner['executable']
        atomic(intent, {'configuration': pin(self.config_path), 'publisher_sources': source_pins(), 'at_utc': utc(),
            'owner_process': actual_owner, 'requested_sys_executable': sys.executable,
            'actual_worker_python': worker_python, 'worker_dependencies': 'stdlib_and_pinned_pure_view'}, new=True)
        self.stdout = (self.root / 'stdout.txt').open('xb'); self.stderr = (self.root / 'stderr.txt').open('xb')
        self.process = subprocess.Popen([worker_python, '-B', '-X', 'utf8', str(Path(__file__).resolve()), '--config', str(self.config_path)],
            stdin=subprocess.DEVNULL, stdout=self.stdout, stderr=self.stderr, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.identity = process_identity(self.process.pid)
        atomic(self.root / 'OWNER-PROCESS.json', {'publisher': self.identity, 'Popen_original_kernel_handle_retained': True,
            'owner_process': actual_owner, 'actual_worker_python': worker_python, 'at_utc': utc()}, new=True)
        return self.identity

    def started(self, *, timeout_seconds=5):
        end = time.monotonic() + timeout_seconds
        while time.monotonic() < end:
            path = self.root / 'STARTED.json'
            if path.exists():
                ref = pin(path); row = validate_started(ref, recording=not self.config['qualification_only'])
                if row['publisher'] != self.identity: raise ValueError('Actual child STARTED differs from original retained owner')
                return ref
            if self.process.poll() is not None: raise RuntimeError('Actual publisher exited before STARTED')
            time.sleep(.02)
        raise TimeoutError('Actual publisher STARTED not observed; preserve intent')

    def stop(self):
        target = self.root / 'STOP'
        if not target.exists(): atomic(target, {'reason': 'owner_normal_stop', 'publisher': self.identity, 'at_utc': utc()}, new=True)

    def seal_binding(self, path):
        reference = self.started()
        value = {'schema': 'xar.ck3.decision-text-publisher-binding/v1', 'machine_id': self.config['machine_id'],
                 'publisher_started': reference, 'publisher_sources': source_pins(), 'OBS_draw_ack': False}
        atomic(path, value, new=True)
        return pin(path)

    def close(self, *, timeout_seconds=5):
        code = self.process.wait(timeout=timeout_seconds)
        closed = read(self.root / 'CLOSED.json')
        if code != 0 or closed['publisher'] != self.identity or closed['first_error'] is not None or closed['normal_STOP_observed'] is not True:
            raise RuntimeError('Publisher did not prove normal STOP and original retained exit0')
        self.stdout.close(); self.stderr.close()
        proof = {'schema': SCHEMA, 'status': 'PUBLISHER_NORMAL_KERNEL_EXIT_ZERO', 'machine_id': self.config['machine_id'],
                 'publisher': self.identity, 'kernel_exit_observed': True, 'exit_code': code, 'forced_process_calls': 0,
                 'Popen_original_kernel_handle_retained': True, 'child_closed': pin(self.root / 'CLOSED.json'), 'at_utc': utc()}
        atomic(self.root / 'OWNER-CLOSED.json', proof, new=True)
        return proof

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--owner', action='store_true', help='Retain the original publisher child handle until its normal STOP')
    parser.add_argument('--binding', type=Path, help='New create-only provider binding receipt for the SDK callback adapter')
    args = parser.parse_args()
    if args.owner:
        if args.binding is None: parser.error('--owner requires --binding')
        owner = PublisherOwner(args.config);owner.start();owner.seal_binding(args.binding)
        while owner.process.poll() is None: time.sleep(.1)
        owner.close()
    else:
        if args.binding is not None: parser.error('--binding belongs to --owner')
        run(args.config)

from pathlib import Path
from datetime import datetime, timezone
import ctypes as c
import ctypes.wintypes as w
import hashlib
import json
import os
import sys

MESSAGES = ((0x0200, 0), (0x0201, 1), (0x0202, 0))


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_record(directory, name, value):
    # Create-only records: a failed later write cannot truncate a prior prefix.
    with (directory / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())


def require_window_owner(query_owner, expected_pid):
    thread_id, pid = query_owner()
    if not thread_id or pid != expected_pid:
        raise RuntimeError('owned HWND process query failed or owner changed')


def post_sequence(state, verify, post, persist, stamp):
    """Actual main consumes this same DATA seam; it never retries a message."""
    state['sequence_status'] = 'IN_PROGRESS'
    state['in_flight'] = None
    state['durable_result_count'] = 0
    for index, (message, wparam) in enumerate(MESSAGES, 1):
        state['phase'] = 'PRECHECK'
        state['next_message_index'] = index
        verify()
        state['phase'] = 'INTENT_WRITE'
        intent = {'index': index, 'message': message, 'wparam': wparam,
                  'hwnd': state['hwnd'], 'lparam': state['lparam'],
                  'status': 'POST_MAY_HAVE_BEGUN_OUTCOME_UNKNOWN', 'at_utc': stamp()}
        persist('MESSAGE-%02d-INTENT.json' % index, intent)
        # A hard stop from this point leaves a conservative durable pending intent.
        state['in_flight'] = dict(intent)
        state['phase'] = 'POST_CALL'
        accepted, error = post(message, wparam)
        if type(accepted) is not bool or type(error) is not int:
            raise TypeError('post callback must return actual bool acceptance and integer last error')
        result = {'index': index, 'message': message, 'wparam': wparam,
                  'accepted': accepted, 'error': error, 'at_utc': stamp()}
        state['messages'].append(dict(result))
        state['phase'] = 'RESULT_WRITE'
        persist('MESSAGE-%02d-RESULT.json' % index, result)
        state['durable_result_count'] = index
        state['in_flight'] = None
        if not accepted:
            state['sequence_status'] = 'POST_REJECTED'
            return
    state['sequence_status'] = 'ALL_POSTS_ACCEPTED_EFFECT_UNKNOWN'


def error_data(error):
    try:
        text = str(error)
    except BaseException:
        text = '<exception message unavailable>'
    return {'type': type(error).__name__, 'message': text}


def classify(state):
    queued = (state.get('sequence_status') == 'ALL_POSTS_ACCEPTED_EFFECT_UNKNOWN'
              and len(state['messages']) == 3 and all(row['accepted'] for row in state['messages']))
    state['classification'] = ('WINDOW_MESSAGES_QUEUED_EFFECT_UNKNOWN_DO_NOT_REPEAT' if queued
                               else 'WINDOW_MESSAGES_PARTIAL_OR_UNKNOWN_DO_NOT_REPEAT')
    state['effect_verified'] = False
    state['do_not_repeat'] = True


def finish_attempt(state, work, final_check, persist, stamp):
    """Retain the original failure, even when terminal evidence cannot be written."""
    terminal_attempted = False
    try:
        work()
        state['phase'] = 'FINAL_VERIFY'
        state.update(final_check())
        state['terminal_status'] = 'RECORDED_ATTEMPT_EFFECT_UNKNOWN'
        state['end_utc'] = stamp()
        classify(state)
        state['phase'] = 'TERMINAL_WRITE'
        terminal_attempted = True
        persist('ACTUAL.json', state)
        return state
    except BaseException as primary:
        state['failure_phase'] = state.get('phase', 'UNKNOWN')
        state['terminal_status'] = 'FAILED'
        state['failure'] = error_data(primary)
        classify(state)
        if not terminal_attempted:
            try:
                state['end_utc'] = stamp()
                terminal_attempted = True
                persist('ACTUAL.json', state)
            except BaseException as secondary:
                # Never mask primary; a partial create-only ACTUAL is not overwritten.
                state['terminal_record_error'] = error_data(secondary)
        raise


def main(spec_path):
    B = Path('D:/ck3-state/resume91-runtime/current-resume268')
    S = json.loads(Path(spec_path).read_bytes())
    O = Path(S['output'])
    assert O.resolve().is_relative_to(B.resolve())
    O.mkdir(exist_ok=False)
    assert not (B.parent / 'USER-OFFLINE-ONLY.json').exists()
    assert (S['selected_label'] == 'They grow up fast.'
            and sha(S['image']) == S['image_sha256']
            and sha(S['owner_review']) == S['owner_review_sha256'])
    cap = json.loads(Path(S['capture_receipt']).read_bytes())
    age = (datetime.now(timezone.utc) - datetime.fromisoformat(cap['end_utc'])).total_seconds()
    assert 0 <= age <= 60
    H = Path('D:/ck3-state/ck3-java-resume91-business268/continuity/continuity.json')
    F = Path('D:/ck3-state/resume91-runtime/quarkus-dev307-runtime/persistent783-r2-runtime/failure108/HEAD2066.frozen.json')
    assert sha(H) == sha(F) == S['canonical_sha256']
    p = B / 'inspect-owned-game-window278.py'
    prefix = p.read_text(encoding='utf8').split("if len(sys.argv)==3 and sys.argv[1]=='--render':")[0]
    ns = {'__name__': 'owned_window_definitions', '__file__': str(p)}
    exec(compile(prefix, str(p), 'exec'), ns)
    u = ns['u']
    game = ns['verify_game']()
    hwnd = 16324062
    u.GetWindowThreadProcessId.restype = w.DWORD

    def query_owner():
        pid = w.DWORD()  # New output storage for every actual query.
        thread_id = u.GetWindowThreadProcessId(hwnd, c.byref(pid))
        return thread_id, pid.value

    require_window_owner(query_owner, 77132)
    assert not u.IsIconic(hwnd) and not u.IsHungAppWindow(hwnd)
    u.SetProcessDpiAwarenessContext.argtypes = [w.HANDLE]
    u.SetProcessDpiAwarenessContext.restype = w.BOOL
    dpi = bool(u.SetProcessDpiAwarenessContext(c.c_void_p(-4)))
    r = w.RECT()
    assert u.GetClientRect(hwnd, c.byref(r)) and [r.right, r.bottom] == [2560, 1440]
    x, y = S['client_x'], S['client_y']
    assert 700 <= x <= 1250 and 1025 <= y <= 1060
    lp = (y << 16) | (x & 65535)
    u.PostMessageW.argtypes = [w.HWND, w.UINT, w.WPARAM, w.LPARAM]
    u.PostMessageW.restype = w.BOOL
    state = {'begin_utc': now(), 'game': game, 'hwnd': hwnd,
             'selected_label': S['selected_label'], 'image': S['image'],
             'image_sha256': S['image_sha256'], 'client_point': [x, y],
             'owner_review': S['owner_review'], 'dpi_set': dpi,
             'scope': 'Single exact-owned HWND-targeted WM_MOUSEMOVE+WM_LBUTTONDOWN+WM_LBUTTONUP. No global mouse/keyboard input, cursor movement, activation, other-window message, ARM/resume/replay or ledger write.',
             'global_SendInput_calls': 0, 'messages': [], 'lparam': lp,
             'schema': 'owned-window-message-custody/v1'}

    def persist(name, value):
        write_record(O, name, value)

    def verify():
        ns['verify_game']()
        require_window_owner(query_owner, 77132)
        assert sha(H) == S['canonical_sha256']

    def post(message, wparam):
        c.set_last_error(0)
        accepted = bool(u.PostMessageW(hwnd, message, wparam, lp))
        error = c.get_last_error()
        return accepted, error

    def final_check():
        return {'final_game': ns['verify_game'](),
                'ledger_unchanged': sha(H) == S['canonical_sha256']}

    ns['verify_game']()
    assert sha(H) == S['canonical_sha256']
    persist('INTENT.json', state)
    result = finish_attempt(state,
                            lambda: post_sequence(state, verify, post, persist, now),
                            final_check, persist, now)
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    main(sys.argv[1])

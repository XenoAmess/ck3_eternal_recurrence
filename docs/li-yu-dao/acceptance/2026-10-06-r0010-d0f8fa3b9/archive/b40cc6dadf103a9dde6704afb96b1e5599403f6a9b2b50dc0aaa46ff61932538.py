from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = BASE / 'live-attempt-010'
OUT = BASE / 'r10-log-preterminal-cut244-readonly-review-20261006-001'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def write_new(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def dump_new(path, value):
    write_new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def stat(path):
    value = path.stat()
    return {'bytes': value.st_size, 'mtime_ns': value.st_mtime_ns,
            'ctime_ns': value.st_ctime_ns}

assert not OUT.exists(), 'Refusing to overwrite an existing package'
OUT.mkdir()
rows = []
for name in ['error.log', 'debug.log']:
    path = RUN / 'userdir/logs' / name
    started = datetime.now(timezone.utc).isoformat()
    if not path.is_file():
        rows.append({'source_path': str(path), 'exists_at_check': False,
                     'capture_started_utc': started,
                     'capture_finished_utc': datetime.now(timezone.utc).isoformat(),
                     'read_count': 0, 'bytes': None, 'sha256': None})
        continue
    before = stat(path)
    data = path.read_bytes()  # Exactly one read of this live log.
    after = stat(path)
    ended = datetime.now(timezone.utc).isoformat()
    write_new(OUT / 'raw' / name, data)
    rows.append({'source_path': str(path), 'exists_at_check': True,
                 'copy_path': 'raw/' + name, 'bytes': len(data), 'sha256': sha(data),
                 'capture_started_utc': started, 'capture_finished_utc': ended,
                 'read_count': 1, 'source_stat_before': before,
                 'source_stat_after': after, 'source_stat_unchanged_during_read': before == after,
                 'captured_ends_with_linebreak': data.endswith((b'\r', b'\n'))})
capture = {'schema': 'lyd.r10.preterminal-cut244.readonly-log-capture.v1',
           'snapshot_kind': 'FINITE_CAPTURED_BYTES_NOT_TERMINAL_WHOLE_LOG',
           'ROOT_parent_reported_context': {
               'business_cutoff_SDK': 244, 'public_revision': 112, 'native_revision': 111,
               'active_event_present': False, 'wallet': {'gold': 1043, 'piety': 3150, 'prestige': 2200},
               'normal_exit_in_progress_final_cutoff_unknown': True,
               'actual_state_at_capture_independently_queried': False},
           'logs': rows,
           'game_MCP_pipe_Client_native_process_handles_desktop_bus_Git_main_operations': False,
           'live_log_write_operations': False, 'old_tests_or_AST_runs': False,
           'normal_exit_credit': False, 'whole_final_log_credit': False, 'overall_PASS': False}
dump_new(OUT / 'CAPTURE.json', capture)
write_new(OUT / 'source' / Path(__file__).name, Path(__file__).read_bytes())
print(json.dumps({'out': str(OUT), 'logs': rows}, ensure_ascii=False))

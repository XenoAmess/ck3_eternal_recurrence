"""Start one metadata-only EDL collector after an actual decision recording.

This adapter neither controls the Game/OBS nor reads media. A child launch is
reported as requested, not healthy. Failed collector setup is preserved as a
separate metadata failure and must not stop an already active recording.
"""
import json
from pathlib import Path
import subprocess
import sys


def start_collector(job, started, *, python=None, popen=None):
    if job.get('capture_mode') != 'game_decision':
        return {'status': 'not_applicable', 'reason': 'decision overlay is required', 'child_launched': False}
    if __package__:
        from . import ck3_stall_edl as engine
        from .collect_stall_edl import launch_spec
    else:
        import ck3_stall_edl as engine
        from collect_stall_edl import launch_spec
    root = Path(job['receipt_root']).resolve(strict=True)
    overlay = job.get('overlay') or {}
    session = Path(overlay['session']).resolve(strict=True)
    if (root.name != job['session_id'] or started.get('state') != 'recording'
            or started.get('game_pid') != job['pid']
            or started.get('game_creation_filetime') != job.get('game_creation_filetime')
            or type(started.get('game_creation_filetime')) is not int
            or started['game_creation_filetime'] <= 0
            or started.get('decision_source') is not True
            or started.get('capture_mode') != 'game_decision'
            or overlay.get('game_pid') != job['pid']
            or overlay.get('game_creation_filetime') != started['game_creation_filetime']):
        raise ValueError('Actual started Game/decision overlay generation differs')
    engine.stamp(started['at_utc'])
    seed = engine.build({'segments': [{
        'session_id': job['session_id'], 'started_at_utc': started['at_utc'],
        'duration_seconds': None, 'state': 'ACTIVE_NOT_PROBED',
        'game_pid': job['pid'], 'game_creation_filetime': started['game_creation_filetime'],
        'video_path': str(Path(job['recording_root']).resolve() / (job['session_id'] + '.mkv')),
        'source_decision_overlay_retained': True,
        'job_pin': engine.pin(root / 'job.json'), 'started_pin': engine.pin(root / 'started.json'),
    }], 'intervals': [], 'wait_end_basis': 'first_verified_CK3_calendar_progress_receipt'})
    store = root / 'stall-edits'
    store.mkdir()
    policy = store / 'policy.json'
    policy.write_bytes(Path(__file__).with_name('recording-stall-policy.json').read_bytes())
    seed_path = store / 'seed.json'
    engine.create(seed_path, seed)
    status = session / 'runtime-repair-status' / 'CURRENT.json'
    spec = launch_spec(python or sys.executable, policy, seed_path, status, store,
                       store / 'STOP-COLLECTOR')
    requested = {'schema': 'xar.ck3.stall-edl-collector-launch/v1', 'status': 'requested',
        'session_id': job['session_id'], 'Game_pid': job['pid'],
        'Game_creation_filetime': started['game_creation_filetime'], 'spec': spec,
        'policy_pin': engine.pin(policy), 'seed_pin': engine.pin(seed_path),
        'runtime_qualified': False, 'new_Game_OBS_calls': 0, 'media_body_bytes_read': 0}
    engine.create(store / 'launch-requested.json', requested)
    launch = popen or subprocess.Popen
    with (store / 'stdout.txt').open('x') as stdout, (store / 'stderr.txt').open('x') as stderr:
        child = launch(spec['argv'], stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    result = {**requested, 'child_pid': child.pid}
    engine.create(store / 'child-requested.json', result)
    return result


def request_stop(job):
    """Graceful metadata writer stop only; never stop a Game or recorder."""
    store = Path(job['receipt_root']) / 'stall-edits'
    if not (store / 'launch-requested.json').is_file():
        return False
    path = store / 'STOP-COLLECTOR'
    if not path.exists():
        with path.open('x', encoding='utf-8') as stream:
            json.dump({'reason': 'recording worker cleanup reached', 'Game_OBS_control_calls': 0}, stream)
    return True

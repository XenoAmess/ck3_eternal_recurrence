"""Root-only no-launch preflight, exact seal and profile preparation; no SDK launch."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CANDIDATE = Path('C:\\Users\\1\\ck3-a04-mechanism-evidence-20261001\\reinforcement-attempt-12-R0129-native-center-diagnostic')
SOURCE = CANDIDATE / 'source'
PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
HEAD = '1901473429deb1297be7d5d4451169082629858b'
NO_LAUNCH = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-06-d11-recap-preflight-20261001-layout-repair-a01')
SEAL = ROOT / 'seal'
CONFIG = ROOT / 'ui-controller-config.frozen-layout-repair-a01.json'
LOCALE = {'PYTHONUTF8': '0', 'PYTHONIOENCODING': 'utf-8'}

def identity(path):
    raw = path.read_bytes()
    return {'path': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest().upper()}

def write(path, row):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(row, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--live-root', type=Path, required=True)
    parser.add_argument('--offline-receipt', type=Path, required=True)
    parser.add_argument('--screen-task-id', required=True)
    parser.add_argument('--screen-expected-sequence', type=int, required=True)
    parser.add_argument('--latest-release-readback', type=Path, required=True)
    args = parser.parse_args()
    assert Path(sys.executable).resolve() == PYTHON.resolve()
    assert not args.output_dir.exists() and not args.live_root.exists() and not SEAL.exists() and not NO_LAUNCH.exists()
    process = ROOT / 'bootstrap-attempt-01'
    process.mkdir()
    frozen = json.loads((ROOT / 'variant-freeze.json').read_text(encoding='utf-8'))
    for row in [frozen['config'], frozen['no_launch_runner'], *frozen['consumer_files'], *frozen['helper_files']]:
        assert identity(Path(row['path'])) == row
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == HEAD

    def phase(name, argv):
        write(process / (name + '-argv.json'), {'argv': argv, 'cwd': str(SOURCE), 'at': datetime.now(timezone.utc).isoformat(), 'environment_overrides': LOCALE})
        with (process / (name + '-stdout.bin')).open('xb') as out, (process / (name + '-stderr.bin')).open('xb') as err:
            result = subprocess.run(argv, cwd=SOURCE, env=dict(os.environ, **LOCALE), stdout=out, stderr=err)
        write(process / (name + '-result.json'), {'exit_code': result.returncode, 'stdout': identity(process / (name + '-stdout.bin')), 'stderr': identity(process / (name + '-stderr.bin'))})
        if result.returncode:
            raise RuntimeError(name + ' failed; do not launch SDK; exact failure preserved')
        print(name + ' exit 0', flush=True)

    phase('no-launch', [str(PYTHON), '-X', 'utf8=0', '-B', str(ROOT / 'run_no_launch_candidate.py'), '--expected-source-head', HEAD, '--checkout', str(SOURCE), '--controller-config', str(CONFIG), '--attempt-directory', str(NO_LAUNCH)])
    SEAL.mkdir()
    lock = SEAL / 'admission-lock.json'
    phase('admission-seal', [str(PYTHON), '-X', 'utf8=0', '-B', str(SOURCE / 'promo/ck3_native_war_ai/integration/d11_admission.py'), 'seal', '--attempt', str(NO_LAUNCH), '--lock', str(lock)])
    binding = json.loads(lock.read_text(encoding='utf-8'))
    old_gate = json.loads(Path('C:/Users/1/AppData/Local/ck3-capture-preparation/jd11-fixed-source-seal-20260930-a04/gate-report.json').read_text(encoding='utf-8'))
    sources = {}
    for relative in old_gate['selected_sources']:
        path = SOURCE / relative
        preserved = SEAL / 'source-snapshot' / relative
        preserved.parent.mkdir(parents=True, exist_ok=True)
        with preserved.open('xb') as stream:
            stream.write(path.read_bytes())
        sources[relative] = {'selected': identity(path), 'preserved': identity(preserved)}
    cli = identity(SOURCE / 'tools/codex_task_bus.py')
    argv = list(binding['run_argv'])
    argv += ['--capture', '--d11-admission-lock', str(lock), '--steam-offline-receipt', '<ROOT_CURRENT_REVIEWED_OFFLINE_RECEIPT>', '--screen-task-id', '<ROOT_EXCLUSIVE_TASK_ON_THIS_SOURCE>', '--screen-expected-sequence', '<LATEST_CAS_SEQUENCE>', '--screen-cli-sha256', cli['sha256']]
    write(SEAL / 'gate-report.json', {'schema': 'xar.promo.jd11-center-diagnostic-source-preparation/v1', 'source_head': HEAD, 'source_checkout': str(SOURCE), 'on_latest_master': False, 'selected_sources': sources, 'candidate_pair': identity(CANDIDATE / 'sealed-native/battle-control-pair.json'), 'native_candidate_provenance': identity(CANDIDATE / 'sealed-native/candidate-manifest.json'), 'historical_pair_provenance_only': identity(Path('C:/Users/1/ck3-jd11-native-pair-20260930/attempt-01/battle-control-pair.json')), 'actual_new_native_epoch': 'NOT_STARTED', 'native_query_verified': False, 'date_action_authorized_by_seal': False, 'recording_authorized_by_seal': False})
    write(SEAL / 'live-argv-plan.json', {'argv': argv, 'state': 'NOT_RUN', 'source_head': HEAD})
    phase('profile-prepare', [str(PYTHON), '-X', 'utf8=0', '-B', str(ROOT / 'entry_reentry.py'), 'prepare', '--output-dir', str(args.output_dir), '--live-root', str(args.live_root), '--offline-receipt', str(args.offline_receipt), '--screen-task-id', args.screen_task_id, '--screen-expected-sequence', str(args.screen_expected_sequence), '--latest-release-readback', str(args.latest_release_readback), '--frame-backend', 'desktop-gdi'])
    write(process / 'result.json', {'result': 'PROFILE_PREPARED_NOT_LAUNCHED', 'source_head': HEAD, 'profile': identity(args.output_dir / 'operator-profile.json'), 'admission_lock': identity(lock), 'sdk_generation': identity(args.output_dir / 'sdk-generation.json'), 'no_game_sdk_screen_operation_by_bootstrap': True, 'root_sdk_entry': str(ROOT / 'entry_reentry.py'), 'root_sdk_mode': 'sdk', 'actual_native_epoch': 'NOT_STARTED'})
    print(json.dumps({'result': 'PROFILE_PREPARED_NOT_LAUNCHED', 'profile_preparation': str(args.output_dir), 'sdk_entry': str(ROOT / 'entry_reentry.py'), 'sdk_entry_mode': 'sdk', 'admission': identity(lock)}, indent=2))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()

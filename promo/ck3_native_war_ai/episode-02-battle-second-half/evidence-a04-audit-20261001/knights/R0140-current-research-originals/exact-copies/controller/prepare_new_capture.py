"""Create one explicitly bound no-launch preflight/profile for the new native candidate."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parent
BUS = Path('D:/workspace/.codex-task-bus/bin/codex_task_bus.py')
BUS_SHA = 'B3C44B42F7BDF401B593D863E3210106A46412DCD7D89F8596C74F4C27392DEE'
PLAN = Path('C:/w/e2gold1001/promo/ck3_native_war_ai/episode-02-battle-second-half/evidence-a04-audit-20261001/knights/capture-nextday-plan.json')

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def identity(path):
    path = Path(path).resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}

def write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate-manifest', required=True, type=Path)
    parser.add_argument('--offline-receipt', required=True, type=Path)
    parser.add_argument('--screen-task-id', required=True)
    parser.add_argument('--live-root', required=True, type=Path)
    parser.add_argument('--static-root', required=True, type=Path)
    args = parser.parse_args()
    candidate = read(args.candidate_manifest)
    require(candidate['status'] == 'RELEASE_BUILD_OFFLINE_CHECKS_PASSED_LIVE_PENDING', 'Reviewed frozen build not ready')
    source = Path(candidate['source']).resolve()
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() == candidate['source_commit'], 'Source changed')
    require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=source, text=True).strip(), 'Frozen source dirty')
    for key in ('dll', 'injector'):
        require(identity(candidate[key]['path']) == candidate[key], 'Native candidate bytes changed')
    offline = read(args.offline_receipt)
    require(offline.get('current_offline_ui_observed') is True, 'Fresh original Steam offline pixels must be reviewed first')
    require(identity(offline['screenshot']['path']) == offline['screenshot'], 'Reviewed offline pixels changed')
    task = read(Path('D:/workspace/.codex-task-bus/tasks') / (args.screen_task_id + '.json'))
    require(task['state'] == 'running' and task.get('resources') == ['ck3-screen:acquired'], 'No exclusive screen owner')
    require(Path(task['repo']).resolve() == source, 'Screen task checkout differs from actual capture source')
    require(not args.live_root.exists() and not args.static_root.exists(), 'New capture path already exists')
    query = subprocess.run(['gh', 'api', 'repos/XenoAmess/xar_promo_toolchain/releases/latest'], capture_output=True,
                           text=True, encoding='utf-8', timeout=30)
    write(ROOT / 'capture-toolchain-release-query.json', {'at_utc': datetime.now(timezone.utc).isoformat(), 'argv': query.args,
          'returncode': query.returncode, 'stdout': query.stdout, 'stderr': query.stderr})
    require(query.returncode == 0, 'Latest formal toolchain release query failed')
    release = json.loads(query.stdout)
    wheel = next(asset for asset in release['assets'] if asset['name'].endswith('.whl'))
    installed = importlib.metadata.version('xar-promo-toolchain')
    direct = json.loads(importlib.metadata.distribution('xar-promo-toolchain').read_text('direct_url.json'))
    require(not release['draft'] and not release['prerelease'] and release['tag_name'].removeprefix('v') == installed and
            direct['archive_info']['hashes']['sha256'].upper() == wheel['digest'].removeprefix('sha256:').upper(),
            'Latest formal wheel must be installed and pinned before a new capture run')
    probes = []
    for flags in [['--version'], ['--help']]:
        result = subprocess.run([sys.executable, '-m', 'xar_promo', *flags], capture_output=True, text=True, encoding='utf-8')
        probes.append({'argv': result.args, 'returncode': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
        require(result.returncode == 0, 'Verified interpreter toolchain probe failed')
    write(ROOT / 'capture-toolchain-interpreter-probe.json', {'purpose': 'Required capture dependency, no video revision',
          'version': installed, 'wheel': wheel, 'interpreter': identity(sys.executable), 'python': sys.version, 'probes': probes})
    plan = read(PLAN)
    live = args.live_root.resolve()
    static = args.static_root.resolve()
    command = [sys.executable, '-X', 'utf8=0', '-B', str(source / 'promo/ck3_native_war_ai/integration/capture_session.py'),
        '--game-dir', 'C:/SteamLibrary/steamapps/common/CRUSAD~1', '--bridge-dll', candidate['dll']['path'],
        '--bridge-injector', candidate['injector']['path'], '--state-dir', str(live / 'ck3-state'), '--output-dir', str(live / 'ck3-output'),
        '--pipe-name', r'\\.\pipe\xar_ck3_e2_scoped_ui_' + uuid.uuid4().hex,
        '--checkpoint-save', plan['exact_input']['save']['path'], '--checkpoint-receipt', plan['exact_input']['receipt']['path'],
        '--frontend-timeout', '900', '--gui-scale', '1.0', '--import-a04-ui-gui-100',
        '--a04-ui-settings-snapshot', plan['source_reuse']['gui_settings_snapshot']['path'],
        '--a04-ui-preservation-receipt', plan['source_reuse']['gui_preservation_receipt']['path'],
        '--interactive-seconds', '3600', '--recovery-seconds', '180', '--hold-seconds', '30', '--enable-private-phase-trace',
        '--steam-offline-receipt', str(args.offline_receipt.resolve()), '--screen-task-id', args.screen_task_id,
        '--screen-expected-sequence', str(task['last_sequence']), '--screen-cli-sha256', BUS_SHA]
    static_command = [a.replace(str(live), str(static)) for a in command]
    write(ROOT / 'new-no-launch-argv.json', static_command)
    result = subprocess.run(static_command, cwd=source, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    for suffix, content in [('stdout', result.stdout), ('stderr', result.stderr)]:
        with (ROOT / ('new-no-launch-' + suffix + '.txt')).open('x', encoding='utf-8', newline='\n') as stream:
            stream.write(content)
    write(ROOT / 'new-no-launch-process.json', {'argv': static_command, 'returncode': result.returncode,
          'stdout': identity(ROOT / 'new-no-launch-stdout.txt'), 'stderr': identity(ROOT / 'new-no-launch-stderr.txt')})
    require(result.returncode == 0, 'No-launch preflight RED, originals retained')
    required = []
    for path in [command[4], candidate['dll']['path'], candidate['injector']['path'], plan['exact_input']['save']['path'],
                 plan['exact_input']['receipt']['path'], plan['source_reuse']['gui_settings_snapshot']['path'],
                 plan['source_reuse']['gui_preservation_receipt']['path'], args.offline_receipt, offline['screenshot']['path'],
                 ROOT / 'capture-toolchain-interpreter-probe.json', ROOT / 'new-no-launch-process.json', static / 'ck3-output/preflight.json',
                 args.candidate_manifest]:
        pin = identity(path)
        required.append({'path': pin['path'], 'kind': 'file', 'size': pin['bytes'], 'sha256': pin['sha256']})
    profile = {'schema_version': 1, 'target': {'id': 'ck3-e2-scoped-ui-20261001-a03',
        'display_name': 'Episode02 full knight mechanism and original UI research',
        'expected': {'token_user': '1', 'desktop': 'WinSta0\\Default', 'machine': 'DESKTOP-3FEVHD2'}},
        'endpoint': {'transport': 'stdio'}, 'state_directory': str(ROOT / 'operator-state-a01'),
        'jobs': {'scoped-ui-research-capture': {'command': command + ['--capture'], 'working_directory': str(source),
          'exclusive_process_names': ['ck3.exe', 'xar_ck3_bridge_injector.exe', 'ffmpeg.exe', 'obs64.exe', 'dowser.exe'],
          'required_paths': required, 'absent_paths': [str(live)], 'controls': {}}}}
    write(ROOT / 'operator-profile-a01.json', profile)
    write(ROOT / 'new-capture-launch-plan.json', {'created_at_utc': datetime.now(timezone.utc).isoformat(),
          'args': command + ['--capture'], 'profile': identity(ROOT / 'operator-profile-a01.json'), 'candidate': identity(args.candidate_manifest),
          'source_commit': candidate['source_commit'], 'source_root': str(source), 'live_root': str(live),
          'screen_task_id': args.screen_task_id, 'screen_sequence': task['last_sequence'], 'new_live_run_id': None,
          'scope': 'New source/build-bound typed original UI and scoped knight state chain, before any video revision',
          'before_date_raw': 53146848, 'after_date_raw': 53146872, 'master_intake': False})
    # Check the separately declared sampling question before the SDK can launch.
    # The actual new live ID and fresh token are bound later, without changing this draft.
    prelaunch = read(ROOT.parent / 'root-attempt-02/native-research-plan.json')
    prelaunch['topic'] = 'episode02-six-gap-new-build-prelaunch'
    prelaunch['observation']['runtime_window_ref'] = str(ROOT / 'new-capture-launch-plan.json')
    prelaunch['observation']['expected_signal'] = ('Current original character/combat/knight tooltip UI; all candidate and ordered roster identities; '
        'scoped effect/death/queue/commit/casualty boundaries; independent two-character signature-weapon and house-guard monitor; same-run full save deltas')
    prelaunch['evidence'] = []
    for ident, path, support in [('candidate', args.candidate_manifest, 'Exact frozen new Release build and focused offline checks'),
                                 ('profile', ROOT / 'operator-profile-a01.json', 'Explicit new process/source/DLL/save/screen lease admission'),
                                 ('launch', ROOT / 'new-capture-launch-plan.json', 'Separate authorized bounded new observation window')]:
        pin = identity(path)
        prelaunch['evidence'].append({'id': ident, 'layer': 'source-contract', 'path': pin['path'], 'sha256': pin['sha256'],
            'exe_sha256': prelaunch['build']['exe_sha256'], 'supports': support})
    write(ROOT / 'prelaunch-native-research-plan.json', prelaunch)
    check_argv = [sys.executable, str(source / 'tools/native_research_plan.py'), 'check',
                  str(ROOT / 'prelaunch-native-research-plan.json'), '--for-observation', '--output',
                  str(ROOT / 'prelaunch-native-research-plan-check.json')]
    checked = subprocess.run(check_argv, capture_output=True, text=True, encoding='utf-8')
    write(ROOT / 'prelaunch-native-research-plan-check-process.json', {'argv': check_argv, 'returncode': checked.returncode,
          'stdout': checked.stdout, 'stderr': checked.stderr})
    require(checked.returncode == 0, 'Prelaunch sampling plan inconsistent; no SDK handoff')
    print(json.dumps({'result': 'NO_LAUNCH_PREFLIGHT_PASSED_NOT_LAUNCHED', 'profile': str(ROOT / 'operator-profile-a01.json')}))

if __name__ == '__main__':
    main()

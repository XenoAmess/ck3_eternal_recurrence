"""Create-only J-d11 preparation and root-owned, one-day paused UI evidence.

Import, describe and prepare never touch the desktop or start CK3/MCP. The
controller is called only by run_paused_join_sdk.py after actual MCP admission.
It uses frozen a15 focus/layout primitives, never its recording continuation.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

REPO = Path('C:/w/jdcap0930')
HEAD = '475bdbffd2c0fc96b4188c394eeea80a780b672a'
PYTHON = Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
SEAL = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/jd11-fixed-source-seal-20260930-a04')
A15 = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/jd11-a15-preparation-20260930-a01')
BASE = Path('C:/Users/1/ck3-screen-authority-resume-20260930/attempt-02/operator-readonly-stdio-profile.json')
CONFIG = A15 / 'ui-controller-config.frozen-a01.json'
JOB = 'episode02-jd11-paused-pair'
DATE = 53146488
ACTOR, WAR, ARMY, COMBAT, JOIN_ARMY = 29829, 4, 18, 16777218, 22
EXE_SHA = '2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86'
LOCALE_OVERRIDES = {'PYTHONUTF8': '0', 'PYTHONIOENCODING': 'utf-8'}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8-sig'))


def identity(path: Path) -> dict:
    path = path.resolve()
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest().upper()
    return {'path': str(path), 'bytes': path.stat().st_size, 'sha256': digest}


def check_identity(row: dict) -> Path:
    path = Path(row['path'])
    require(identity(path) == row, 'frozen bytes changed: ' + str(path))
    return path


def write_new(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def locale_environment() -> dict:
    return dict(os.environ, **LOCALE_OVERRIDES)


def execution_command(argv: list[str]) -> list[str]:
    # Interpreter flags are not in sys.argv and therefore do not alter the
    # sealed capture intent verified by d11_admission.
    return [argv[0], '-X', 'utf8=0', '-B', *argv[1:]]


def module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    item = importlib.util.module_from_spec(spec)
    sys.modules[name] = item
    spec.loader.exec_module(item)
    return item


def pinned_inputs() -> tuple[dict, dict, dict]:
    plan, lock, config = load(SEAL / 'live-argv-plan.json'), load(SEAL / 'admission-lock.json'), load(CONFIG)
    require(plan.get('source_head') == lock.get('checkout_head') == config.get('source_head') == HEAD,
            'fixed source head differs')
    actual = subprocess.run(['git', '-C', str(REPO), 'rev-parse', 'HEAD'], capture_output=True,
                            text=True, check=True, timeout=15).stdout.strip()
    require(actual == HEAD, 'execution checkout changed; no master intake allowed')
    for key in ('canonical_camera_guard', 'hot_controller', 'root_window_focus_helper'):
        check_identity(config[key])
    check_identity(config['pointer_and_focus']['mapper_source'])
    for row in lock['files'].values():
        check_identity(row)
    gate = load(SEAL / 'gate-report.json')
    for pair in gate['selected_sources'].values():
        check_identity(pair['selected'])
    native_path = 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py'
    clean = subprocess.run(['git', '-C', str(REPO), 'diff', '--quiet', 'HEAD', '--', native_path], timeout=15)
    require(clean.returncode == 0, 'fixed one-day executor has working-tree changes')
    return plan, lock, config


def substituted_argv(plan: dict, live_root: Path, offline: Path, task: str, sequence: int, pipe: str) -> list[str]:
    argv = list(plan['argv'])
    replacements = {'--state-dir': str((live_root / 'ck3-state').resolve()),
                    '--output-dir': str((live_root / 'ck3-output').resolve()),
                    '--pipe-name': pipe, '--steam-offline-receipt': str(offline.resolve()),
                    '--screen-task-id': task, '--screen-expected-sequence': str(sequence)}
    for flag, value in replacements.items():
        require(argv.count(flag) == 1, 'missing or duplicate sealed flag: ' + flag)
        argv[argv.index(flag) + 1] = value
    require(not any('<' in value or '>' in value for value in argv), 'unfilled argv placeholder')
    # Same production admission operation; only explicitly permitted live variants.
    integration = REPO / 'promo/ck3_native_war_ai/integration'
    sys.path.insert(0, str(integration))
    from d11_admission import strip_live_variants
    require(strip_live_variants(argv) == strip_live_variants(plan['argv']), 'non-variable sealed argv changed')
    require('--record-debug-desktop' not in argv and '--capture' in argv, 'unexpected recorder option')
    return argv


def open_kaishek_assessment(lock: dict) -> dict:
    # This operation uses game callback timing, native handles and Win32 pixels;
    # the existing parser/IR/replay subset cannot model those observables.
    checkout = Path('Z:/workspace/open_kaishek')
    commit = None
    if checkout.is_dir():
        found = subprocess.run(['git', '-C', str(checkout), 'rev-parse', 'HEAD'],
                               capture_output=True, text=True, timeout=15)
        commit = found.stdout.strip() if found.returncode == 0 else None
    return {'schema': 'xar.open-kaishek.prevalidation-assessment/v1',
            'assessed_at': utc(), 'result': 'not-applicable',
            'checkout': str(checkout), 'checkout_available': checkout.is_dir(),
            'commit': commit, 'profile': None, 'version': None,
            'game_exe_sha256': EXE_SHA,
            'fixture_inputs': {key: row for key, row in lock['files'].items()
                               if key in ('save', 'receipt', 'pair')},
            'command': None, 'offline_engine_execution_performed': False,
            'unsupported': ['managed native join callback/detour state',
                            'game one-day executor and paused native revisions',
                            'Win32 foreground/PID/HWND and original tooltip pixels'],
            'reason': 'No applicable parser/IR/finite-runtime/replay semantics for this native bridge + desktop evidence operation. Python boundary checks below are separate; unavailable checkout is recorded, not treated as an engine pass.'}


def validate_frozen_ui_binding(argv: list[str]) -> dict:
    """Call the actual frozen read-only source/target gates before profile write."""
    def value(flag):
        require(argv.count(flag) == 1, 'missing or duplicate UI-binding flag: ' + flag)
        return argv[argv.index(flag) + 1]

    args = argparse.Namespace(state_dir=Path(value('--state-dir')), output_dir=Path(value('--output-dir')),
        checkpoint_save=Path(value('--checkpoint-save')), checkpoint_receipt=Path(value('--checkpoint-receipt')),
        import_a04_ui_gui_100='--import-a04-ui-gui-100' in argv, gui_scale=value('--gui-scale'),
        a04_ui_settings_snapshot=Path(value('--a04-ui-settings-snapshot')),
        a04_ui_preservation_receipt=Path(value('--a04-ui-preservation-receipt')),
        record_debug_desktop='--record-debug-desktop' in argv)
    integration = REPO / 'promo/ck3_native_war_ai/integration'
    sys.path.insert(0, str(integration))
    frozen = module(integration / 'capture_session.py', '_paused_pair_frozen_ui_binding')
    checkpoint = frozen.checkpoint_source(args.checkpoint_save, args.checkpoint_receipt)
    target = frozen.bind_a04_ui_target(args, checkpoint)
    binding = frozen.validate_a04_ui_gui_source_binding(args, checkpoint)
    require(binding is not None and target['track'] == 'e2-06-d11', 'actual frozen d11 UI source binding missing')
    return {'status': 'ACTUAL_FROZEN_UI_BINDING_PASSED_NO_LAUNCH',
            'capture_source': identity(integration / 'capture_session.py'), 'target': target,
            'source_binding': binding, 'state_or_output_directory_created': False,
            'mcp_started': False, 'screen_accessed': False, 'game_started': False}


def describe(args: argparse.Namespace) -> None:
    plan, lock, config = pinned_inputs()
    value = {'schema': 'xar.jd11.paused-pair.minimum-plan/v1', 'created_at': utc(),
             'state': 'NOT_RUN', 'source_head': HEAD, 'source': str(REPO),
             'consumer': identity(Path(__file__)),
             'sdk_client': identity(Path(__file__).with_name('run_paused_join_sdk.py')),
             'sealed_plan': identity(SEAL / 'live-argv-plan.json'),
             'admission_lock': identity(SEAL / 'admission-lock.json'), 'a15_config': identity(CONFIG),
             'at_most_native_days': 1, 'recorder_request': False,
             'native_action': {'tool': 'ck3_execute_step', 'arguments': {'step': 'life-advance', 'expected_revision': '<actual after-save revision>'}},
             'before_after_inputs': {'actor': ACTOR, 'war': WAR, 'subject_army': ARMY, 'combat': COMBAT,
                                     'candidate_joining_army': JOIN_ARMY, 'starting_date_raw': DATE, 'ending_date_raw': DATE + 24},
             'same_pause_binding': 'snapshot -> control -> original panel + width-tooltip PNG -> snapshot; equal revision/native_revision/snapshot_id/date; explicit root visual readback',
             'trace': ['capture_runtime_join_width', 'capture_runtime_join_full_entries'],
             'historical_numbers_used_as_acceptance_oracles': False,
             'open_kaishek': open_kaishek_assessment(lock),
             'scope': {'mcp_started': False, 'game_started': False, 'screen_accessed': False,
                       'screen_acquired': False, 'date_advanced': False, 'historical_assets_modified': False}}
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=False)
        write_new(args.output_dir / 'minimum-plan.json', value)
    print(json.dumps(value, ensure_ascii=False))


def prepare(args: argparse.Namespace) -> None:
    plan, lock, config = pinned_inputs()
    old_prepare = module(A15 / 'prepare_jd11_a15_operator.py', '_paused_pair_old_prepare')
    old_prepare.check_review(args.offline_receipt)
    require(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', args.screen_task_id) is not None
            and args.screen_expected_sequence > 0, 'actual root screen CAS required')
    require(not args.live_root.exists(), 'live root already exists; preserve attempt and use a new root')
    release = formal_release(load(args.latest_release_readback))
    require(0 <= time.time() - args.latest_release_readback.stat().st_mtime <= 86400,
            'latest formal Release readback must be from this task/day')
    probe = subprocess.run([str(PYTHON), '-X', 'utf8=0', '-B', '-m', 'xar_promo', '--version'],
                           env=locale_environment(), capture_output=True, text=True, encoding='utf-8', timeout=30)
    version = release['tag_name'].removeprefix('v')
    require(probe.returncode == 0 and version in probe.stdout, 'verified interpreter must use the latest formal promo wheel')
    env_probe = subprocess.run([str(PYTHON), '-X', 'utf8=0', '-B', str(Path(__file__)), 'environment-probe'],
                              env=locale_environment(), capture_output=True, text=True, encoding='utf-8', timeout=30)
    require(env_probe.returncode == 0, 'verified interpreter dependency probe failed: ' + env_probe.stderr)
    environment = json.loads(env_probe.stdout)
    require(environment['packages']['xar-promo-toolchain'] == version,
            'installed wheel version differs from formal Release')
    direct = environment['installed_direct_url'] or {}
    wheel_hash = (direct.get('archive_info') or {}).get('hashes', {}).get('sha256')
    require(isinstance(wheel_hash, str) and len(wheel_hash) == 64, 'installed wheel SHA receipt missing')
    require(wheel_hash.upper() == release['wheel_sha256'].upper(), 'installed wheel SHA differs from current formal Release receipt')
    require(all(value is None for value in environment['promo_source_environment'].values()),
            'source override cannot identify the admitted formal wheel')
    pipe = r'\\.\pipe\xar_ck3_jd11_paused_' + uuid.uuid4().hex
    argv = substituted_argv(plan, args.live_root, args.offline_receipt,
                            args.screen_task_id, args.screen_expected_sequence, pipe)
    ui_binding = validate_frozen_ui_binding(argv)
    server = REPO / 'ck3_autonomous_player/operator_mcp_server.py'
    self_path = Path(__file__).resolve()
    client = self_path.with_name('run_paused_join_sdk.py')
    wgc_library = None
    if args.frame_backend == 'hwnd-wgc':
        window_module = module(self_path.with_name('hwnd_wgc_frame.py'), '_paused_pair_wgc_prepare')
        wgc_library = window_module.library_identity()
    paths = [PYTHON, SEAL / 'admission-lock.json', SEAL / 'live-argv-plan.json', BASE, CONFIG,
             self_path, client, self_path.with_name('hwnd_wgc_frame.py'), args.offline_receipt,
             Path(load(args.offline_receipt)['screenshot']['path']), args.latest_release_readback,
             server, REPO / 'ck3_autonomous_player/src/xar_autoplayer/operator_mcp.py',
             REPO / 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
             Path(config['canonical_camera_guard']['path']), Path(config['hot_controller']['path']),
             Path(config['root_window_focus_helper']['path']), Path(config['pointer_and_focus']['mapper_source']['path'])]
    if wgc_library is not None:
        paths.extend(Path(row['path']) for row in wgc_library.values())
    required = [{'path': row['path'], 'kind': 'file', 'size': row['bytes'], 'sha256': row['sha256']}
                for row in lock['files'].values()]
    for pair in load(SEAL / 'gate-report.json')['selected_sources'].values():
        row = pair['selected']
        required.append({'path': row['path'], 'kind': 'file', 'size': row['bytes'], 'sha256': row['sha256']})
    for path in paths:
        row = identity(path)
        required.append({'path': row['path'], 'kind': 'file', 'size': row['bytes'], 'sha256': row['sha256']})
    args.output_dir.mkdir(parents=True, exist_ok=False)
    profile_path = args.output_dir / 'operator-profile.json'
    target = deepcopy(load(BASE)['target'])
    target['display_name'] = 'J-d11 paused before/after + native join trace, at most one day'
    write_new(profile_path, {'schema_version': 1, 'target': target, 'endpoint': {'transport': 'stdio'},
                            'state_directory': str((args.output_dir / 'operator-state').resolve()),
                            'jobs': {JOB: {'command': execution_command(argv), 'working_directory': str(REPO.resolve()),
                            'exclusive_process_names': ['ck3.exe', 'xar_ck3_bridge_injector.exe', 'bridge_injector.exe',
                                                        'dll_injector.exe', 'ffmpeg.exe', 'obs64.exe', 'dowser.exe'],
                            'required_paths': required, 'absent_paths': [str(args.live_root.resolve())], 'controls': {}}}})
    write_new(args.output_dir / 'live-argv-adoption.json', {
        'state': 'NOT_RUN', 'argv': argv, 'source_head': HEAD, 'on_latest_master': False,
        'frozen_plan': identity(SEAL / 'live-argv-plan.json'), 'admission_lock': identity(SEAL / 'admission-lock.json'),
        'ui_controller_config': identity(CONFIG), 'root_offline_review': identity(args.offline_receipt),
        'latest_release_readback': identity(args.latest_release_readback), 'environment': environment,
        'operator_command': execution_command(argv), 'python_startup_options': ['-X', 'utf8=0', '-B'],
        'process_environment_overrides': LOCALE_OVERRIDES,
        'version_command': [str(PYTHON), '-X', 'utf8=0', '-B', '-m', 'xar_promo', '--version'],
        'version_stdout': probe.stdout, 'version_stderr': probe.stderr,
        'installed_wheel_sha256': wheel_hash.upper(), 'at_most_native_days': 1,
        'root_requested_paused_before_after_supplement': True, 'recorder_authorized': False,
        'cas_owner_verified_by_generator': False, 'open_kaishek': open_kaishek_assessment(lock),
        'ui_frame_backend': args.frame_backend, 'wgc_library': wgc_library,
        'actual_frozen_a04_ui_binding': ui_binding,
        'wgc_consumer': identity(self_path.with_name('hwnd_wgc_frame.py')),
        'window_image_is_desktop_full_frame': False, 'hwnd_image_mouse_fallback_authorized': False})
    write_new(args.output_dir / 'sdk-generation.json', {
        'schema': 'xar.jd11.paused-pair.sdk-generation/v1', 'status': 'PROFILE_FROZEN_MCP_NOT_STARTED',
        'profile_path': str(profile_path.resolve()), 'profile_sha256': identity(profile_path)['sha256'],
        'source_head': HEAD, 'target_id': target['id'], 'job_name': JOB,
        'root_sdk_client': identity(client), 'hot_controller': identity(self_path),
        'server_command_for_local_sdk_stdio': [str(PYTHON), '-X', 'utf8=0', '-B', str(server), '--profile', str(profile_path.resolve())],
        'server_environment_overrides': LOCALE_OVERRIDES, 'capture_environment_inherited_from_operator': True,
        'server_cwd': str(REPO), 'maximum_native_days': 1,
        'local_sdk_required_sequence': ['operator_get_capabilities', 'operator_get_status',
                                        'operator_preflight_job', 'operator_handoff_job'],
        'scope': {'mcp_started': False, 'game_started': False, 'screen_accessed': False, 'run_id_allocated': False}})
    print(json.dumps({'profile': identity(profile_path), 'generation': identity(args.output_dir / 'sdk-generation.json'),
                      'processes_started': False, 'date_advanced': False}, ensure_ascii=False))


def formal_release(receipt: dict) -> dict:
    release = receipt.get('latest_formal_release', receipt)
    if 'tagName' in release:
        require(release.get('isPrerelease') is False and bool(release.get('publishedAt'))
                and bool(release.get('query_argv')), 'actual root latest formal Release readback required')
        normalized = {'tag_name': release['tagName'], 'published_at': release['publishedAt'],
                      'wheel_sha256': release.get('wheel_sha256')}
    else:
        require(release.get('draft') is False and release.get('prerelease') is False
                and bool(release.get('tag_name')) and bool(release.get('published_at')), 'latest formal Release API readback required')
        wheel = next((item for item in release.get('assets', [])
                      if item.get('name', '').endswith('.whl')), {})
        normalized = {'tag_name': release['tag_name'], 'published_at': release['published_at'],
                      'wheel_sha256': release.get('wheel_sha256') or wheel.get('digest', '').removeprefix('sha256:')}
    require(isinstance(normalized['wheel_sha256'], str)
            and re.fullmatch(r'[a-fA-F0-9]{64}', normalized['wheel_sha256']), 'formal wheel SHA missing')
    return normalized


def same_paused_frame(first: dict, second: dict) -> bool:
    keys = ('revision', 'native_revision', 'snapshot_id', 'date_raw', 'paused', 'actor', 'army_id', 'army_state')
    return first.get('paused') is True and all(first.get(key) == second.get(key) for key in keys)


def trace_contract(body: dict, token: int) -> dict:
    require(body.get('accepted') is True and body.get('combat_id') == COMBAT
            and body.get('managed_daily_sequence_token') == token, 'trace finish binding failed')
    managed = body.get('managed_trace') or {}
    checkpoint = managed.get('managed_checkpoint') or {}
    trace = managed.get('trace') or {}
    require(trace.get('status') == 'captured' and trace.get('failure_flags') == 0
            and trace.get('record_count') == len(trace.get('records') or []) == 7,
            'native phase trace incomplete or failed')
    require(checkpoint.get('exact_one_day_observed') is True, 'native trace did not prove exact one paused day')
    require(checkpoint.get('recoverable_checkpoint_created') is True
            and checkpoint.get('boundary_dates_match_checkpoint') is True
            and checkpoint.get('detours_uninstalled') is True, 'trace checkpoint/callback/cleanup proof missing')
    width, entries = trace.get('runtime_join_width') or {}, trace.get('runtime_join_full_entries') or {}
    require(width.get('status') == 'captured' and entries.get('status') == 'captured',
            'join width/full entries not captured; preserve new attempt without historical substitution')
    wb, eb = width.get('boundaries') or [], entries.get('boundaries') or []
    require(width.get('count') == len(wb) == 3 and entries.get('count') == len(eb) == 2,
            'unexpected join hook boundary count')
    require([item.get('boundary') for item in wb] == [0, 1, 2]
            and [item.get('boundary') for item in eb] == [0, 1], 'join boundary order differs')
    require(all(item.get('combat_id') == COMBAT and item.get('army_id') == JOIN_ARMY
                and item.get('native_date_raw') == DATE + 24 for item in wb), 'width hook battle/army/date differs')
    require(all(item.get('combat_id') == COMBAT and item.get('incoming_army_id') == JOIN_ARMY
                and item.get('native_date_raw') == DATE + 24 for item in eb), 'entries hook battle/army/date differs')
    require(len({item.get('thread_id') for item in [*wb, *eb]}) == 1,
            'join hook records are not one native thread')
    return {'checkpoint': checkpoint, 'runtime_join_width': width, 'runtime_join_full_entries': entries}


def trace_observation(body: dict | None, token: int, error: str | None = None) -> dict:
    """Report actual availability; never promote failed phase/join captures."""
    body = body or {}
    managed = body.get('managed_trace') or {}
    trace = managed.get('trace') or {}
    checkpoint = managed.get('managed_checkpoint') or {}
    report = {'schema': 'xar.jd11.paused-pair.independent-trace-observation/v1',
              'finish_call_error': error, 'finish_accepted': body.get('accepted'),
              'finish_status': body.get('status'), 'finish_combat_id': body.get('combat_id'),
              'finish_sequence_token': body.get('managed_daily_sequence_token'),
              'checkpoint': checkpoint,
              'phase': {'status': trace.get('status', 'unavailable'), 'failure_flags': trace.get('failure_flags'),
                        'record_count': trace.get('record_count'), 'expected_record_count': 7,
                        'records_available': len(trace.get('records') or []),
                        'boundaries_available': [{key: item.get(key) for key in ('boundary', 'native_date_raw',
                                                 'combat_id', 'managed_daily_sequence_token', 'capture_failure_flags',
                                                 'full_mutable_transition_bundle_complete')}
                                                 for item in trace.get('records') or [] if isinstance(item, dict)]},
              'all_phase_and_join_boundaries_closed': False, 'missing_or_invalid': []}
    for name, expected, army_field in (('runtime_join_width', 3, 'army_id'),
                                       ('runtime_join_full_entries', 2, 'incoming_army_id')):
        source = trace.get(name) or {}
        rows = source.get('boundaries') or []
        metadata = [{key: item.get(key) for key in ('boundary', 'thread_id', 'native_date_raw',
                    'combat_id', army_field, 'side_index', 'joined_side_index', 'phase_day')}
                    for item in rows if isinstance(item, dict)]
        expected_boundaries = set(range(expected))
        actual_boundaries = {item.get('boundary') for item in metadata}
        valid = (source.get('status') == 'captured' and source.get('count') == len(metadata) == expected
                 and actual_boundaries == expected_boundaries
                 and all(item.get('combat_id') == COMBAT and item.get(army_field) == JOIN_ARMY
                         and item.get('native_date_raw') == DATE + 24 for item in metadata))
        report[name] = {'status': source.get('status', 'unavailable'), 'count': source.get('count'),
                        'first_failure_code': source.get('first_failure_code'),
                        'expected_boundary_count': expected, 'boundaries_available': metadata,
                        'missing_boundary_numbers': sorted(expected_boundaries - actual_boundaries),
                        'individual_capture_complete_and_bound': valid,
                        'entry_columns': source.get('entry_columns') if name.endswith('full_entries') else None}
        if not valid:
            report['missing_or_invalid'].append(name)
    try:
        trace_contract(body, token)
    except (ValueError, KeyError, TypeError) as failure:
        report['strict_contract_failure'] = str(failure)
        report['missing_or_invalid'].append('strict_phase_join_checkpoint_contract')
    else:
        report['all_phase_and_join_boundaries_closed'] = True
    return report


def collect_after_independent_of_trace(probe_after, finish_trace, collect_after,
                                      recover_finish, token: int) -> dict:
    """A verified paused next day is preserved even when FINISH fails.

    probe_after must validate native actor/date/control. None of these callbacks
    may request a second date action. Tests exercise this failure branch offline.
    """
    result = {'after_native_probe': probe_after()}
    body, receipt, error = None, None, None
    try:
        body, receipt = finish_trace(result['after_native_probe']['values']['revision'])
    except (OSError, RuntimeError, TimeoutError, ValueError) as failure:
        error = repr(failure)
        try:
            body, receipt = recover_finish()
        except (OSError, RuntimeError, KeyError, TypeError, ValueError) as recovery_failure:
            receipt = {'failure_readback_error': repr(recovery_failure)}
    # This deliberately precedes every phase/join completeness assessment.
    result['after'] = collect_after()
    result['trace_finish'] = receipt
    result['trace_finish_error'] = error
    result['trace_status'] = trace_observation(body, token, error)
    return result


def center_once_after_focus(paused, call, camera, config):
    """Bind one typed camera call to a newly observed post-focus paused state.

    R0128 returned native state_changed after foreground activation. The public
    revision is deliberately retained: the frozen driver maps it to the native
    revision. An error is not retried and is not treated as a missing capability.
    """
    snapshot, control, values, observation = paused('post-focus', DATE)
    selection = camera.select_bound_hotspot(snapshot, control, Path(config['game_dir']),
                                           config['landed_title_input_files'])
    centered, receipt = call('center', 'ck3_center_map_on_landed_title_v1',
                            {'title_key': selection['title_key'], 'expected_revision': values['revision']})
    camera.verify_center_result(centered, selection, snapshot)
    return snapshot, control, values, observation, receipt


def run_controller(args: argparse.Namespace) -> int:
    evidence, output, helpers = args.evidence_dir, None, None
    evidence.mkdir(parents=True, exist_ok=False)
    row = {'schema': 'xar.jd11.paused-pair.controller-result/v1', 'started_at': utc(),
           'source_head': HEAD, 'maximum_native_days': 1, 'recorder_requested': False,
           'date_advance_requested': False, 'human_video_1x_review': False,
           'screen_claimed_by_controller': False, 'samples_completed': 0}
    error = None
    try:
        adoption = load(args.profile_preparation / 'live-argv-adoption.json')
        argv = adoption['argv']
        output = Path(argv[argv.index('--output-dir') + 1])
        require(adoption.get('source_head') == HEAD and adoption.get('at_most_native_days') == 1
                and adoption.get('root_requested_paused_before_after_supplement') is True
                and adoption.get('recorder_authorized') is False, 'root paused-pair adoption missing')
        config = load(check_identity(adoption['ui_controller_config']))
        helpers = module(check_identity(config['hot_controller']), '_paused_pair_a15_primitives')
        helpers._DESKTOP_EVIDENCE = evidence
        mapper_path = check_identity(config['pointer_and_focus']['mapper_source'])
        mapper = module(mapper_path, '_paused_pair_mapper')
        focus_path = check_identity(config['root_window_focus_helper'])
        focus = module(focus_path, '_paused_pair_focus')
        backend = adoption.get('ui_frame_backend', 'desktop-gdi')
        require(backend in ('desktop-gdi', 'hwnd-wgc'), 'unknown explicitly frozen image backend')
        row['ui_frame_backend'] = backend
        row['locale_environment_overrides'] = adoption.get('process_environment_overrides')
        window_capture = module(check_identity(adoption['wgc_consumer']), '_paused_pair_wgc_run') if backend == 'hwnd-wgc' else None
        if window_capture is not None:
            require(window_capture.library_identity() == adoption['wgc_library'], 'WGC library bytes changed')
        camera = module(check_identity(config['canonical_camera_guard']), '_paused_pair_camera')
        sys.path.insert(0, str(REPO / 'promo/ck3_native_war_ai/episode-02-battle-second-half'))
        import remaining_live_step as native
        until = time.monotonic() + args.ready_timeout
        while not (output / 'interactive-requests-responses/service.json').is_file():
            require(not any((output / name).exists() for name in ('entry-failure.json', 'hot-failure-state.json', 'capture-report.json')),
                    'managed source failed or terminated before readiness')
            require(time.monotonic() < until, 'paused source service readiness timeout')
            time.sleep(0.25)
        actual = load(output / 'command.json')
        require([actual['python'], *actual['argv']] == argv, 'actual capture command differs')
        lock = check_identity(adoption['admission_lock'])
        row['binding'] = native.bind_session(output, 'e2-06-d11', lock)
        prefix = 'p1-paused-' + uuid.uuid4().hex[:12]

        def call(label, tool, arguments):
            return native.call(output, prefix + '-' + label, tool, arguments, 90)

        def paused(label, date):
            snapshot, sr = call(label + '-snapshot', 'ck3_take_snapshot', {})
            okay, values = native.snapshot_case(snapshot, date, require_combat=True)
            require(okay, 'wrong paused actor/war/army/date at ' + label)
            control, cr = call(label + '-control', 'ck3_query_battle_control_snapshot_v1',
                               {'subject_army_id': ARMY, 'expected_revision': values['revision']})
            okay, cv = native.battle_control_case(control, values, date)
            require(okay, 'unbound paused battle control at ' + label)
            return snapshot, control, values, {'snapshot': sr, 'control': cr, 'values': values, 'control_values': cv}

        layout_deadline = time.monotonic() + 180
        snapshot, control, values, observation = paused('layout', DATE)
        pid = snapshot.get('diagnostics', {}).get('bridge_pid')
        require(type(pid) is int and pid > 0, 'actual bridge PID missing')

        def original(name, *, enforce_focus=True):
            if window_capture is not None:
                return window_capture.capture(evidence, name, pid, focus, output, enforce_focus=enforce_focus)
            return helpers.original_frame(evidence, name, mapper, pid, enforce_focus=enforce_focus,
                                          state_provider=focus.capture_state if not enforce_focus else None)

        frame = original('00-pre-focus', enforce_focus=False)
        if window_capture is None:
            row['focus'] = helpers.wait_root_focus(evidence, frame, focus, focus_path,
                                observation['snapshot'], observation['control'], output, pid, layout_deadline)
        elif frame['after']['focus']['foreground_hwnd'] == frame['target_hwnd'] and frame['after']['focus']['foreground_pid'] == pid:
            row['focus'] = {'already_current_foreground': True, 'actual_readback': frame['after'],
                            'frame': frame['screenshot'], 'mouse_inputs': 0, 'keyboard_inputs': 0}
        else:
            review = helpers.root_review(evidence, '00-wgc-semantic-focus', [frame], layout_deadline)
            row['focus'] = window_capture.semantic_focus(evidence, frame, review, focus,
                                  lambda: original('00-after-semantic-focus'))
        snapshot, control, values, observation, receipt = center_once_after_focus(paused, call, camera, config)
        row['post_focus_native_binding'] = observation
        row['native_center'] = receipt
        frame = original('01-centered')
        if window_capture is None:
            review = helpers.root_review(evidence, '01-pointer-move', [frame], layout_deadline)
            helpers.mapped_action(evidence, '01-pointer-move', 'move', frame, review, mapper, mapper_path, pid)
            frame = original('02-pointer-safe')
        review = helpers.root_review(evidence, '02-battle-panel', [frame], layout_deadline)
        if review.get('battle_panel_already_open') is not True:
            require(window_capture is None,
                    'WGC window image cannot authorize mouse click; no existing native battle-panel open semantic entry')
            helpers.mapped_action(evidence, '02-battle-open', 'click', frame, review, mapper, mapper_path, pid)
        first = original('03-stability-start')
        require(layout_deadline - time.monotonic() >= 10, 'layout stability budget missing')
        time.sleep(10)
        second = original('04-stability-end')
        review = helpers.root_review(evidence, '03-final-layout', [first, second], layout_deadline)
        for gate in ('camera_stable', 'full_battle_panel', 'date_actor_army_battle_readable', 'overlay_free'):
            require(review.get(gate) is True, 'actual layout gate failed: ' + gate)
        row['layout_review'] = review

        def sample(label, date):
            _, bc, sv, receipts = paused(label, date)
            panel = original(label + '-panel')
            hover, tooltip = None, None
            if window_capture is None:
                hover_review = helpers.root_review(evidence, label + '-width-hover', [panel], time.monotonic() + 180)
                require(hover_review.get('relative_soldiers_tooltip_target_reviewed') is True,
                        'root must identify CV_TT_RELATIVE_SOLDIERS target from current original image')
                hover = helpers.mapped_action(evidence, label + '-width-hover', 'move', panel, hover_review, mapper, mapper_path, pid)
                time.sleep(1)
                tooltip = original(label + '-width')
            frames = [panel, tooltip] if tooltip is not None else [panel]
            visual = helpers.root_review(evidence, label + '-readback', frames, time.monotonic() + 180)
            for gate in ('full_battle_panel', 'date_actor_army_battle_readable', 'battle_width_tooltip_readable',
                         'this_battle_top_counts_readable', 'counts_sources_bound_to_this_battle'):
                if window_capture is not None and gate == 'battle_width_tooltip_readable':
                    continue
                require(visual.get(gate) is True, 'root readback missing: ' + gate)
            shown = visual.get('visible_values') or {}
            width_visible = visual.get('battle_width_tooltip_readable') is True
            if width_visible or window_capture is None:
                require(type(shown.get('battle_width')) is int and shown['battle_width'] ==
                        (bc.get('battle_control_snapshot') or {}).get('final_combat_width'), 'UI width and native width differ')
            require(type(shown.get('player_soldiers')) is int and type(shown.get('opponent_soldiers')) is int,
                    'actual counts must be transcribed, not inferred')
            after, after_receipt = call(label + '-after-pixels', 'ck3_take_snapshot', {})
            okay, av = native.snapshot_case(after, date, require_combat=True)
            require(okay and same_paused_frame(sv, av), 'pause/revision changed around original UI pixels')
            result = {'schema': 'xar.jd11.paused-pair.sample/v1', 'created_at': utc(), 'stage': label,
                      'receipts': receipts, 'after_pixels_snapshot': after_receipt, 'after_pixels_values': av,
                      'panel': panel, 'tooltip': tooltip, 'pointer_hover': hover,
                      'actual_visual_review': visual, 'same_paused_frame_verified': True,
                      'image_kind': panel.get('image_kind', 'original-desktop-gdi'),
                      'battle_width_ui_observed': width_visible, 'battle_width_ui_gap': not width_visible,
                      'mouse_inputs': 0 if window_capture is not None else 'explicit desktop-gated mapper receipts',
                      'hook_instant_same_frame_claimed': False,
                      'native_side_cache_and_entries_distinct': True, 'historical_number_substitution': False}
            write_new(evidence / (label + '-sample.json'), result)
            row['samples_completed'] += 1
            return result

        row['before'] = sample('before', DATE)
        before, before_receipt = call('pre-advance', 'ck3_take_snapshot', {})
        okay, sv = native.snapshot_case(before, DATE, require_combat=True)
        require(okay and same_paused_frame(row['before']['after_pixels_values'], sv), 'before source changed; no day request')
        # The fixed executor uses a 1-day horizon only for a controllable combat
        # army. Check its actual input, not merely the war's allied-army listing.
        require(any(isinstance(item, dict) and item.get('army_id') == ARMY and item.get('controllable') is True
                    and item.get('army_state') == 'combat' for item in before.get('player_armies', [])),
                'fixed native executor one-day combat horizon precondition missing')
        token = 1 + uuid.uuid4().int % (2**31 - 1)
        intent = {'schema': 'xar.jd11.paused-pair.advance-intent/v1', 'created_at': utc(),
                  'binding': row['binding'], 'before_sample': identity(evidence / 'before-sample.json'),
                  'pre_advance_snapshot': before_receipt, 'sequence_token': token, 'maximum_days': 1,
                  'retry_allowed': False, 'recorder_requested': False}
        write_new(evidence / 'advance-intent.json', intent)
        saved, row['checkpoint'] = call('before-save', 'ck3_save_checkpoint', {'expected_revision': sv['revision']})
        require(saved.get('accepted') is True and (saved.get('checkpoint') or {}).get('status') == 'saved'
                and (saved.get('checkpoint') or {}).get('date_raw') == DATE, 'pre-day recoverable checkpoint missing')
        _, _, saved_values, row['after_save'] = paused('after-save', DATE)
        begin_args = {'action': 'private_phase_trace', 'step': 'experimental-combat-phase-event-trace-begin-v1',
                      'expected_revision': saved_values['revision'], 'combat_id': COMBAT,
                      'managed_daily_sequence_token': token, 'checkpoint_sequence': 1,
                      'candidate_joining_army_id': JOIN_ARMY, 'capture_runtime_join_width': True,
                      'capture_runtime_join_full_entries': True}
        begun, row['trace_begin'] = native.private_call(output, prefix + '-trace-begin', begin_args, 90)
        require(begun.get('accepted') is True and begun.get('combat_id') == COMBAT
                and begun.get('managed_daily_sequence_token') == token, 'trace begin refused; no advance')
        row['date_advance_requested'] = True
        advanced = None
        try:
            advanced, row['one_day'] = call('one-day', 'ck3_execute_step',
                                          {'step': 'life-advance', 'expected_revision': saved_values['revision']})
            row['advance_returned_ending_date_raw'] = advanced.get('ending_date_raw')
        except (OSError, RuntimeError, TimeoutError, ValueError) as failure:
            row['one_day_call_error'] = repr(failure)
            row['one_day_reply_missing_or_ambiguous'] = True
        # Whether the ACK arrives or times out, only a fresh native +24 paused
        # actor/date/control readback permits after-frame collection. No resubmit.
        def probe_after():
            _, _, _, observation = paused('after-day-readback', DATE + 24)
            return observation

        def finish_trace(revision):
            return native.private_call(output, prefix + '-trace-finish',
                {'action': 'private_phase_trace', 'step': 'experimental-combat-phase-event-trace-finish-v1',
                 'expected_revision': revision, 'combat_id': COMBAT,
                 'managed_daily_sequence_token': token}, 90)

        def recover_finish():
            request = output / 'interactive-requests' / (prefix + '-trace-finish.json')
            response = output / 'interactive-requests-responses' / request.name
            raw = load(response) if response.is_file() else {}
            receipt = {'request': identity(request) if request.is_file() else None,
                       'response': identity(response) if response.is_file() else None,
                       'result': raw.get('result'), 'error': raw.get('error'),
                       'read_from_preserved_reply_after_finish_failure': True}
            body = raw.get('body') if isinstance(raw.get('body'), dict) else None
            return body, receipt

        row.update(collect_after_independent_of_trace(probe_after, finish_trace,
                                                      lambda: sample('after', DATE + 24), recover_finish, token))
        row['one_day_proven_by_actual_paused_native_readback'] = True
        require(row['before']['panel']['screenshot']['sha256'] != row['after']['panel']['screenshot']['sha256'],
                'same UI image bytes after native day change; preserve as stale/unproven frame pair')
    except Exception as exc:
        error = repr(exc)
        row['error'] = error
    try:
        if output is None:
            adoption = load(args.profile_preparation / 'live-argv-adoption.json')
            argv = adoption['argv']
            output = Path(argv[argv.index('--output-dir') + 1])
        if helpers is None:
            config = load(CONFIG)
            helpers = module(check_identity(config['hot_controller']), '_paused_pair_cleanup')
        row['finish'] = helpers.managed_finish(output, evidence, args.cleanup_timeout)
        deadline = time.monotonic() + args.cleanup_timeout
        while not (output / 'capture-report.json').is_file():
            require(time.monotonic() < deadline, 'managed cleanup report missing')
            time.sleep(0.25)
        report = load(output / 'capture-report.json')
        inventory = report.get('cleanup_process_inventory') or {}
        require(isinstance(inventory.get('processes'), list) and not inventory['processes'], 'cleanup inventory not empty')
        require(report.get('result') != 'RED', 'capture report retained RED')
        row.update(capture_report=identity(output / 'capture-report.json'), actual_run_id=report.get('run_id'),
                   cleanup_inventory=inventory, cleanup_inventory_empty=True,
                   result='PAUSED_PAIR_JOIN_EVIDENCE_OBTAINED_UNREVIEWED' if error is None else 'RED_PRESERVED_CLEANUP_REPORTED')
        if error is None:
            row['remaining_ui_gap'] = {'battle_width_tooltip': row['before']['battle_width_ui_gap'] or row['after']['battle_width_ui_gap']}
            if not row['trace_status']['all_phase_and_join_boundaries_closed']:
                row['result'] = 'PAUSED_PAIR_OBTAINED_TRACE_INCOMPLETE_UNREVIEWED'
    except Exception as cleanup:
        row.update(result='RED_PRESERVED_ROOT_MANAGED_CLEANUP_REQUIRED', cleanup_error=repr(cleanup))
    write_new(evidence / 'controller-result.json', row)
    print(json.dumps({'controller_result': identity(evidence / 'controller-result.json'), 'result': row['result'],
                      'date_advance_requested': row['date_advance_requested'], 'samples_completed': row['samples_completed']}, ensure_ascii=False), flush=True)
    return 0 if row['result'] in ('PAUSED_PAIR_JOIN_EVIDENCE_OBTAINED_UNREVIEWED',
                                 'PAUSED_PAIR_OBTAINED_TRACE_INCOMPLETE_UNREVIEWED') else 2


def environment_probe() -> None:
    from importlib import metadata
    import locale
    packages = {name: metadata.version(name) for name in ('mcp', 'Pillow', 'pywin32', 'pyautogui', 'psutil', 'xar-promo-toolchain')}
    direct_text = metadata.distribution('xar-promo-toolchain').read_text('direct_url.json')
    print(json.dumps({'interpreter': identity(Path(sys.executable)), 'python_version': sys.version,
                      'packages': packages, 'installed_direct_url': json.loads(direct_text) if direct_text else None,
                      'locale': {'utf8_mode': sys.flags.utf8_mode, 'locale_encoding': locale.getencoding(),
                                 'preferred_encoding': locale.getpreferredencoding(False), 'stdout_encoding': sys.stdout.encoding,
                                 'process_environment_overrides': {key: os.environ.get(key) for key in LOCALE_OVERRIDES}},
                      'promo_source_environment': {name: os.environ.get(name) for name in ('XAR_PROMO_SOURCE', 'XAR_PROMO_TOOLCHAIN_SOURCE')}}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    d = modes.add_parser('describe', help='read pins and optionally freeze minimum plan; no desktop/MCP/game access')
    d.add_argument('--output-dir', type=Path)
    p = modes.add_parser('prepare', help='freeze a new root profile; does not launch it')
    p.add_argument('--offline-receipt', type=Path, required=True)
    p.add_argument('--latest-release-readback', type=Path, required=True)
    p.add_argument('--screen-task-id', required=True)
    p.add_argument('--screen-expected-sequence', type=int, required=True)
    p.add_argument('--live-root', type=Path, required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    p.add_argument('--frame-backend', choices=('hwnd-wgc', 'desktop-gdi'), default='desktop-gdi',
                   help='HWND WGC is an original window image and never authorizes mouse coordinates; desktop GDI requires its separate real desktop gate')
    modes.add_parser('environment-probe', help='package metadata only; no desktop or MCP initialization')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')
    {'describe': describe, 'prepare': prepare, 'environment-probe': lambda unused: environment_probe()}[args.mode](args)


if __name__ == '__main__':
    main()

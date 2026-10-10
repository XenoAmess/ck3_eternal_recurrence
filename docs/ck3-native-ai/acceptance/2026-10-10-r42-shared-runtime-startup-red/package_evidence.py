"""Archive existing R42 evidence without reading saved-campaign bodies or changing runtime."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

RUN_ID = 'bf-202609141645-5434332d4d--li-yu-dao--R0042'
COMMON = Path('C:/workspace/ck3-common-runtime')
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = COMMON / 'runs' / RUN_ID
KEEPER = COMMON / 'keepers/20261010-a04'
CASE = COMMON / 'cases/lyd-transaction-control-20261010-004'
PROFILE = CASE / 'state/profile'
COMPARISON = BASE / 'r42-single-variable-input-comparison-20261010-001'
ACTIVITY = BASE / 'r42-process-activity-readonly-20261010-001'
SOURCE_GRAPH = BASE / 'r42-prior-fixture-startup-hook-sourceonly-20261010-001'
SEPARATE_PACKAGES = [
    'docs/ck3-native-ai/2026-10-10-shared-saved-debug-source05.md',
    'docs/ck3-native-ai/2026-10-10-exact-b0e5119-ci.md',
    'docs/ck3-native-ai/2026-10-10-common-cache-reviewer-ci-fixture.md',
    'docs/ck3-native-ai/2026-10-10-r41-shared-runtime-startup-red.md',
]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pin(path: Path) -> dict:
    return {'source_path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def load(path: Path):
    return json.loads(path.read_bytes())


def write(path: Path, value: dict) -> None:
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def checked_ref(row: dict) -> None:
    path = Path(row['path'])
    assert path.suffix.lower() != '.ck3', path
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path


def checked_command(root: Path, expected: int) -> dict:
    value = load(root / 'RESULT.actual.json')
    assert value['exit_code'] == expected, root
    for channel in ['stdout', 'stderr']:
        checked_ref(value[channel])
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    admission = load(RUN / 'predecessor-admission.json')
    admission_root = Path(admission['machine_admission'])
    roots = {
        'run': RUN,
        'keeper': KEEPER,
        'case/prepared': CASE / 'prepared',
        'case/allocation-bus-preflight-audit': CASE / 'allocation-bus-preflight-audit',
        'case/single-use-ledger': CASE / 'single-use-ledger',
        'case/state/control': CASE / 'state/control',
        'profile/logs': PROFILE / 'logs',
        'diagnostic/single-variable-input-comparison': COMPARISON,
        'diagnostic/process-activity': ACTIVITY,
        'diagnostic/prior-fixture-source-graph': SOURCE_GRAPH,
        'root-command/prepare': BASE / 'r42-root-case-prepare-20261010-001',
        'root-command/preflight': BASE / 'r42-root-case-preflight-20261010-001',
        'root-command/allocate': BASE / 'r42-root-case-allocate-20261010-001',
        'machine-admission/current': admission_root,
    }
    selected = {}
    counts = {}
    for prefix, root in roots.items():
        assert root.is_dir(), root
        paths = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files': len(paths)}
        for path in paths:
            assert path.suffix.lower() not in {'.ck3', '.dll', '.exe', '.zip', '.dmp'}, path
            assert path.stat().st_size < 64 * 1024 * 1024, path
            selected[prefix + '/' + path.relative_to(root).as_posix()] = path
    selected['case/state/preparation.json'] = CASE / 'state/preparation.json'
    selected['machine-admission/machine.json'] = admission_root.parent / 'machine.json'
    selected['producer/package_evidence.py'] = Path(__file__).resolve()
    # Preserve actual small ROOT producers/derivations; Source05 and CI packages stay separate.
    for path in sorted(BASE.glob('r42-root-*.py')):
        selected['producer/root/' + path.name] = path
    for pattern in ['r42*derivation*.json', 'r42_*startup*.py']:
        for path in sorted(BASE.glob(pattern)):
            selected['producer/root/' + path.name] = path
    for name in [
        'root-record-command-20261010-001.py',
        'r42_single_variable_input_comparison_20261010_001.py',
        'r42_process_activity_readonly_20261010_001.py',
        'r42_read_prior_script_entrypoints_20261010.py',
        'r42_append_observer_deferred_event_20261010.py',
    ]:
        selected['producer/diagnostic/' + name] = BASE / name
    for item in load(BASE / 'r42-root-display-tools-derivation-20261010-001.json')['derivations']:
        for role in ['original', 'derived']:
            path = Path(item[role])
            assert sha(path) == item[role + '_sha256']
            selected['producer/derivation-source/' + path.name] = path
    for record_name, old_name, new_name in [
        ('r42-root-closeout-derivation-20261010-001.json', 'r41-root-closeout-20261010-002.py', 'r42-root-closeout-20261010-001.py'),
        ('r42-retained-observer002-derivation-20261010-001.json', 'r42-root-observe-retained-process-20261010-001.py', 'r42-root-observe-retained-process-20261010-002.py'),
    ]:
        record = load(BASE / record_name)
        for field, name in [('original_sha256', old_name), ('derived_sha256', new_name)]:
            path = BASE / name
            assert sha(path) == record[field]
            selected['producer/derivation-source/' + path.name] = path

    prepared = load(CASE / 'prepared/prepared-case.json')
    seed = prepared['startup']['saved_campaign']
    assert seed['bytes'] == 91711686
    assert seed['sha256'] == 'a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c'
    # Reuse the actual preparation's seed pin. Stat only: no original or copied seed body is read.
    pinned_only = []
    for path in [Path(seed['save']), PROFILE / 'save games/restored_campaign.ck3']:
        assert path.stat().st_size == seed['bytes']
        pinned_only.append({'source_path': str(path), 'bytes': seed['bytes'], 'sha256': seed['sha256'],
            'reason': 'saved campaign body remains external; declared preparation pin, stat-size checked only',
            'body_read_by_archiver': False, 'hash_recomputed_by_archiver': False,
            'pin_source': 'case/prepared/prepared-case.json#/startup/saved_campaign'})

    report = load(RUN / 'native-report.json')
    startup = report['saved_campaign_restore']['startup_observations']
    assert len(startup) == 1022
    assert all(row['status'] == 'WAITING_FOR_INITIAL_NATIVE_CONNECTION'
        and row['connected'] is False and row['semantic_state_available'] is False
        and row['connection_generation'] == 0 and row['bridge_pid'] is None for row in startup)
    assert report['saved_campaign_restore']['observations'] == []
    assert report['status'] == 'RED' and report['steps'] == []
    assert report['cleanup_ok'] is False and report['session']['report'] is None
    assert report['managed_session_thread_finished'] is True
    assert not (RUN / 'native-report.native-wire.jsonl').exists()
    assert not (CASE / 'state/injector-attempt').exists()
    parent = load(RUN / 'host-original-process-exit.json')
    observer = load(RUN / 'observer-retained-handle-exit.json')
    observer_ready = load(RUN / 'observer-retained-handle-ready.json')
    keeper_parent = load(RUN / 'keeper-actual-parent-exit.json')
    current = load(RUN / 'ACTUAL-CURRENT-CLOSEOUT.json')
    release = load(RUN / 'release-command-001/stdout.log')
    verify = load(RUN / 'verify-command-001/stdout.log')
    offline = load(RUN / 'steam-final-recovery-001/OFFLINE-REVIEW.actual.json')
    display = load(RUN / 'display-restore-001.json')
    launch = load(RUN / 'launch-intent.json')
    argv = load(RUN / 'frozen-argv.json')['argv']
    comparison = load(COMPARISON / 'REPORT.actual.json')
    activity = load(ACTIVITY / 'SAMPLES.actual.json')
    debug_lines = (PROFILE / 'logs/debug.log').read_text(encoding='utf-8-sig').splitlines()
    assert argv[argv.index('--readiness-timeout') + 1] == '600'
    assert argv.count('--saved-campaign-inject-after-load') == 1
    assert argv.count('--saved-campaign-debug-mode') == 1
    assert observer_ready['process']['cmdline'].count('-debug_mode') == 1
    assert parent['actual_original_popen_wait'] is True and parent['returncode'] == 1
    assert parent['normal_ck3_exit_inferred'] is False
    assert observer['pid'] == 9988 and observer['wait_result'] == 0 and observer['actual_exit_code'] == 1
    assert observer['independent_observer_handle'] is True and observer['original_createprocess_handle'] is False
    assert observer['process_signals_sent'] is False and observer['typed_normal_exit_inferred'] is False
    assert observer_ready['handle_identity_matches'] is True
    assert observer_ready['psutil_to_raw_filetime_delta_100ns'] == -2
    assert current['ck3_inventory']['processes'] == [] and current['case_processes'] == []
    assert current['process_read_errors'] == [] and all(row['exists'] is False for row in current['control_files'])
    assert current['historical_host_cleanup_ok'] is False and current['normal_exit_zero_claimed'] is False
    assert current['historical_ck3_exit_code'] is None and current['historical_job_final_active_count'] is None
    assert keeper_parent['keeper_actual_exit_code'] == 0 and keeper_parent['keeper_report']['thread_exited'] is True
    assert keeper_parent['keeper_report']['last_sequence'] == 4302
    assert release['ok'] is True and release['event']['sequence'] == 4303 and release['task']['resources'] == []
    assert display['change_result'] == 0 and display['after']['width'] == 1024 and display['after']['height'] == 768
    assert offline['steam_offline_confirmed'] is True and offline['direct_original_image_review'] is True
    assert sha(Path(offline['path'])) == offline['sha256']
    assert verify['status'] == 'NOT_RUN_OR_PRESERVED_FAILURE' and verify['business_pass'] is False
    assert admission['closure']['mode'] == 'previous-shared-failed-launch'
    assert admission['closure']['run_id'].endswith('--R0041')
    assert comparison['status'] == 'MATCH_EXCEPT_EXPLICIT_SHARED_DEBUG_MODE'
    assert comparison['all_file_hashes_match'] is True and comparison['normalized_other_argv_equal'] is True
    assert len(activity) == 3 and all(row['errors'][0]['type'] == 'NoSuchProcess' for row in activity)
    assert all('cpu_times' not in row for row in activity)
    assert not any('Setup completion (history loaded)' in line for line in debug_lines)
    assert any('Setup powerful vassals' in line for line in debug_lines)
    command_codes = {}
    for label, root, expected in [
        ('prepare', BASE / 'r42-root-case-prepare-20261010-001', 0),
        ('preflight', BASE / 'r42-root-case-preflight-20261010-001', 0),
        ('allocate', BASE / 'r42-root-case-allocate-20261010-001', 0),
        ('run', RUN / 'run-command-001', 2),
        ('verify', RUN / 'verify-command-001', 2),
        ('release', RUN / 'release-command-001', 0),
        ('independent-observer001', RUN / 'observer-retained-command-001', 1),
        ('independent-observer002', RUN / 'observer-retained-command-002', 0),
    ]:
        command = checked_command(root, expected)
        command_codes[label] = command['exit_code']
        if label == 'release':
            assert command['argv'][command['argv'].index('--expected-sequence') + 1] == '4302'
    assert b'AssertionError' in (RUN / 'observer-retained-command-001/stderr.log').read_bytes()

    archive = args.output / 'RAW-EVIDENCE.zip'
    entries = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for label, path in sorted(selected.items()):
            row = {'path': label, **pin(path)}
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == row['sha256']
            info = zipfile.ZipInfo(label, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, raw)
            entries.append(row)
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None and set(check.namelist()) == {row['path'] for row in entries}
        for row in entries:
            raw = check.read(row['path'])
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
            assert sha(Path(row['source_path'])) == row['sha256']
    for prefix, root in roots.items():
        assert len([path for path in root.rglob('*') if path.is_file()]) == counts[prefix]['files']
    facts = {'schema': 'ck3-r42-shared-runtime-startup-red-actual-v1', 'run_id': RUN_ID,
        'checkout_head': launch['admitted_lease']['checkout_head'], 'agent_source_root': report['agent_source_root'],
        'started_at': report['started_at'], 'finished_at': report['finished_at'], 'readiness_timeout_seconds': 600,
        'delayed_injection_requested': True, 'debug_mode_requested': True, 'actual_game_debug_mode_count': 1,
        'injection_admitted': False, 'startup_observation_count': len(startup),
        'startup_first_last': [startup[0], startup[-1]], 'saved_native_frame_count': 0,
        'command_exit_codes': command_codes, 'native_status': report['status'], 'native_error': report['error'],
        'session_error': report['session']['error'], 'steps': report['steps'],
        'host_original_parent_exit_code': parent['returncode'], 'historical_host_cleanup_ok': False,
        'historical_session_report': None, 'historical_original_createprocess_handle_exit_code': None,
        'historical_job_final_active_count': None, 'independent_observer_handle_exit': observer,
        'independent_observer_identity': observer_ready, 'normal_exit_zero_proven': False,
        'actual_current_closeout': current, 'keeper_original_parent_exit_code': keeper_parent['keeper_actual_exit_code'],
        'actual_release_sequence': release['event']['sequence'], 'actual_release_resources': release['task']['resources'],
        'final_steam_offline_review': offline, 'restored_display': display['after'], 'public_verify_result': verify,
        'predecessor_closure_mode': admission['closure']['mode'], 'predecessor_run_id': admission['closure']['run_id'],
        'bootstrap_reused': False, 'input_comparison_summary': {key: comparison[key] for key in
            ['status', 'file_counts', 'all_file_hashes_match', 'seed_pin_equal', 'budgets', 'baseline_cache_count',
             'political_AST_baseline_count', 'saved_startup_contract_equal_ignoring_state_path',
             'debug_flag_counts', 'delayed_injection_flag_counts', 'normalized_other_argv_equal']},
        'debug_log_last_line': debug_lines[-1], 'setup_completion_marker_seen': False,
        'activity_samples': {'source': str(ACTIVITY), 'count': 3,
            'actual_times': [row['observed_at_utc'] for row in activity], 'errors': [row['errors'] for row in activity],
            'cpu_values_obtained': False, 'deadlock_inference': None},
        'source_graph_boundary': 'Static fixture-entry and callgraph evidence only; no R42 loading cause or business credit.',
        'separate_permanent_packages': SEPARATE_PACKAGES, 'game_actions_by_this_producer': 0,
        'saved_campaign_body_reads_by_this_producer': 0, 'business_pass': False, 'case_acceptance_pass': False}
    write(args.output / 'FACTS.actual.json', facts)
    index = {'schema': 'ck3-raw-evidence-index-v1', 'run_id': RUN_ID,
        'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
        'source_roots': counts, 'entries': entries, 'pinned_only': pinned_only,
        'separate_permanent_packages': SEPARATE_PACKAGES, 'producer': pin(Path(__file__).resolve())}
    write(args.output / 'INDEX.json', index)
    validation = {'schema': 'ck3-r42-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'archive_members_exact': True, 'archive_crc_valid': True, 'all_archived_bytes_sha256_rechecked': True,
        'all_source_bytes_sha256_rechecked': True, 'source_root_file_counts_rechecked': True,
        'actual_command_stdout_stderr_pins_rechecked': True, 'script_derivation_pins_rechecked': True,
        'saved_campaign_bodies_archived': False, 'saved_campaign_bodies_read': False,
        'seed_hash_recomputed': False, 'seed_pin_source': 'actual prepared-case startup contract',
        'source05_or_ci_archives_repacked': False, 'entries': len(entries), 'archive_bytes': archive.stat().st_size,
        'archive_sha256': sha(archive), 'facts_sha256': sha(args.output / 'FACTS.actual.json'),
        'index_sha256': sha(args.output / 'INDEX.json'), 'producer_sha256': sha(Path(__file__).resolve()),
        'evidence_valid': True, 'business_pass': False, 'case_acceptance_pass': False, 'normal_exit_zero_proven': False}
    write(args.output / 'VALIDATION.actual.json', validation)
    print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'source_roots': counts,
        'facts': pin(args.output / 'FACTS.actual.json'), 'index': pin(args.output / 'INDEX.json'),
        'validation': pin(args.output / 'VALIDATION.actual.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

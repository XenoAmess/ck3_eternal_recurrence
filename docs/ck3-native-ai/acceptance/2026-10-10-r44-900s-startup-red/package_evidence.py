"""Preserve existing R44 startup samples and RED closure; no runtime operations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
COMMON = Path('C:/workspace/ck3-common-runtime')
RUN_ID = 'bf-202609141645-5434332d4d--li-yu-dao--R0044'
RUN = COMMON / 'runs' / RUN_ID
CASE = COMMON / 'cases/lyd-transaction-control-20261010-006'
KEEPER = COMMON / 'keepers/20261010-a06'
PROFILE = CASE / 'state/profile'
METRICS = BASE / 'r44-written-startup-samples-readonly-20261010-001'
COMPARISON = BASE / 'r44-actual-frozen-input-comparison-20261010-001'
CI = BASE / 'r44-exact-97d16f9b1-ci-20261010-001'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def pin(path):
    return {'source_path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def load(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def command(root, expected):
    value = load(root / 'RESULT.actual.json')
    assert value['exit_code'] == expected, root
    for channel in ['stdout', 'stderr']:
        item = value[channel]
        path = Path(item['path'])
        assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    admission = load(RUN / 'predecessor-admission.json')
    admission_root = Path(admission['machine_admission'])
    roots = {
        'run': RUN, 'keeper': KEEPER, 'case/prepared': CASE / 'prepared',
        'case/allocation-bus-preflight-audit': CASE / 'allocation-bus-preflight-audit',
        'case/single-use-ledger': CASE / 'single-use-ledger', 'case/state/control': CASE / 'state/control',
        'profile/logs': PROFILE / 'logs', 'diagnostic/written-startup-samples': METRICS,
        'diagnostic/actual-frozen-input-comparison': COMPARISON,
        'ci/exact-97d16f9b1': CI,
        'root-command/prepare': BASE / 'r44-root-case-prepare-20261010-001',
        'root-command/preflight': BASE / 'r44-root-case-preflight-20261010-001',
        'root-command/allocate': BASE / 'r44-root-case-allocate-20261010-001',
        'sourceonly/prepare-inputs': BASE / 'r44-transaction-control-prepare-sourceonly-20261010-001',
        'machine-admission/current': admission_root,
    }
    for root in sorted(BASE.glob('r44-root-*')):
        if root.is_dir() and root not in roots.values():
            roots['root-command/' + root.name] = root
    selected, counts = {}, {}
    for prefix, root in roots.items():
        assert root.is_dir(), root
        files = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files': len(files)}
        for path in files:
            assert path.suffix.lower() not in {'.ck3', '.exe', '.dll', '.dmp'}, path
            assert path.suffix.lower() != '.zip' or prefix.startswith('ci/'), path
            assert path.stat().st_size < 16 * 1024 * 1024, path
            selected[prefix + '/' + path.relative_to(root).as_posix()] = path
    selected['case/state/preparation.json'] = CASE / 'state/preparation.json'
    selected['machine-admission/machine.json'] = admission_root.parent / 'machine.json'
    selected['producer/package_evidence.py'] = Path(__file__).resolve()
    for pattern in ['r44-root-*.py', 'r44-root-*derivation*.json', 'r44-root-derive-*.actual.json',
                    'r44_*startup*.py', 'r44_*cache*.py', 'r44_*written*.py', 'r44-agent-*.py']:
        for path in sorted(BASE.glob(pattern)):
            selected['producer/root/' + path.name] = path
    for name in ['root-record-command-20261010-001.py', 'r44_prepare_sourceonly_20261010_001.py']:
        selected['producer/root/' + name] = BASE / name
    derivations = load(BASE / 'r44-transaction-control-prepare-sourceonly-20261010-001/SCRIPT-DERIVATIONS.actual.json')
    for row in derivations:
        for role in ['original', 'candidate', 'diff']:
            item = row[role]
            path = Path(item['path'])
            assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256']
            selected['producer/derivation-source/' + path.name] = path
    for name in ['r44-root-derive-closeout-20261010-001.actual.json', 'r44-root-derive-observation-reader-20261010-001.actual.json']:
        derivation = load(BASE / name)
        for role in ['source', 'target']:
            path = Path(derivation[role])
            assert sha(path) == derivation[role + '_sha256']
            selected['producer/derivation-source/' + path.name] = path

    prepared = load(CASE / 'prepared/prepared-case.json')
    seed = prepared['startup']['saved_campaign']
    assert seed['bytes'] == 91711686 and seed['sha256'] == 'a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c'
    pinned_only = []
    for path in [Path(seed['save']), PROFILE / 'save games/restored_campaign.ck3']:
        assert path.stat().st_size == seed['bytes']
        pinned_only.append({'source_path': str(path), 'bytes': seed['bytes'], 'sha256': seed['sha256'],
            'pin_source': 'actual prepared-case startup saved_campaign',
            'stat_size_checked': True, 'body_read': False, 'hash_recomputed': False})
    report = load(RUN / 'native-report.json')
    startup = report['saved_campaign_restore']['startup_observations']
    assert len(startup) == 1422
    assert all(item['status'] == 'WAITING_FOR_INITIAL_NATIVE_CONNECTION' and item['connected'] is False
        and item['semantic_state_available'] is False and item['bridge_pid'] is None
        and item['connection_generation'] == 0 for item in startup)
    assert report['saved_campaign_restore']['observations'] == [] and report['steps'] == []
    assert report['status'] == 'RED' and report['cleanup_ok'] is False
    assert report['session']['report'] is None and report['managed_session_thread_finished'] is True
    assert not (RUN / 'native-report.native-wire.jsonl').exists()
    parent = load(RUN / 'host-original-process-exit.json')
    observer = load(RUN / 'startup-observer-001/EXIT.actual.json')
    observer_ready = load(RUN / 'startup-observer-001/HANDLE-READY.actual.json')
    keeper = load(RUN / 'keeper-actual-parent-exit.json')
    current = load(RUN / 'ACTUAL-CURRENT-CLOSEOUT.json')
    release = load(RUN / 'release-command-001/stdout.log')
    offline = load(RUN / 'steam-final-recovery-001/OFFLINE-REVIEW.actual.json')
    display = load(RUN / 'display-restore-001.json')
    verify = load(RUN / 'verify-command-001/stdout.log')
    launch = load(RUN / 'launch-intent.json')
    argv = load(RUN / 'frozen-argv.json')['argv']
    metrics = load(METRICS / 'REPORT.actual.json')
    comparison = load(COMPARISON / 'COMPARISON.actual.json')
    ci = load(CI / 'FINAL.actual.json')
    ci_terminal = load(CI / 'TERMINAL-EVIDENCE.actual.json')
    assert argv[argv.index('--readiness-timeout') + 1] == '900'
    assert argv.count('--saved-campaign-inject-after-load') == 1 and argv.count('--saved-campaign-debug-mode') == 1
    assert observer_ready['process']['cmdline'].count('-debug_mode') == 1
    assert parent['actual_original_popen_wait'] is True and parent['returncode'] == 1
    assert observer['pid'] == 14012 and observer['wait_result'] == 0 and observer['actual_exit_code'] == 1
    assert observer['independent_observer_handle'] is True and observer['original_createprocess_handle'] is False
    assert observer['signals_sent'] is False
    assert current['ck3_inventory']['processes'] == [] and current['case_processes'] == []
    assert current['process_read_errors'] == [] and all(not item['exists'] for item in current['control_files'])
    assert current['historical_host_cleanup_ok'] is False and current['normal_exit_zero_claimed'] is False
    assert current['historical_ck3_exit_code'] is None and current['historical_job_final_active_count'] is None
    assert keeper['keeper_actual_exit_code'] == 0 and keeper['keeper_report']['thread_exited'] is True
    assert keeper['keeper_report']['last_sequence'] == 4339
    assert release['ok'] is True and release['event']['sequence'] == 4340 and release['task']['resources'] == []
    assert offline['steam_offline_confirmed'] is True and offline['direct_original_image_review'] is True
    assert sha(Path(offline['path'])) == offline['sha256']
    assert display['change_result'] == 0 and display['after']['width'] == 1024 and display['after']['height'] == 768
    assert verify['status'] == 'NOT_RUN_OR_PRESERVED_FAILURE' and verify['business_pass'] is False
    assert admission['closure']['mode'] == 'previous-shared-failed-launch' and admission['closure']['run_id'].endswith('--R0043')
    samples = sorted((RUN / 'startup-observer-001').glob('sample-*.actual.json'))
    images = sorted((RUN / 'startup-observer-001').glob('desktop-*.png'))
    assert len(samples) == metrics['sample_count'] == 30 and len(images) == 3
    assert metrics['sample_error_count'] == 0 and metrics['after600_zero_cpu_interval_count'] == 0
    assert metrics['after600_complete_interval_count'] == 9
    assert metrics['sdl_window_count'] == metrics['sdl_foreground_count'] == 29
    assert metrics['last_sample_to_exit_gap_seconds'] > 28
    assert comparison['actions']['seed_body_reads'] == 0
    assert comparison['normalized_argv_differences'] == [{'path': '$/29', 'r43': '600', 'r44': '900'}]
    assert ci['head_sha'] == launch['admitted_lease']['checkout_head'] == '97d16f9b1f3c91887549c987291c2435087e1025'
    assert ci['triggered_workflows_success'] is True
    assert ci['workflow_status']['Li Yu Dao static checks']['status'] == 'NOT_TRIGGERED'
    assert ci_terminal['original_query_pairs_byte_hash_verified'] == 51
    codes = {}
    for label, root, expected in [
        ('prepare', BASE / 'r44-root-case-prepare-20261010-001', 0),
        ('preflight', BASE / 'r44-root-case-preflight-20261010-001', 0),
        ('allocate', BASE / 'r44-root-case-allocate-20261010-001', 0),
        ('run', RUN / 'run-command-001', 2), ('verify', RUN / 'verify-command-001', 2),
        ('observer', RUN / 'observer-command-001', 0), ('release', RUN / 'release-command-001', 0)]:
        item = command(root, expected)
        codes[label] = item['exit_code']
        if label == 'release':
            release_expected = int(item['argv'][item['argv'].index('--expected-sequence') + 1])
            assert release_expected == 4339
    log_lines = (PROFILE / 'logs/debug.log').read_text(encoding='utf-8-sig').splitlines()
    assert not any('Setup completion (history loaded)' in line for line in log_lines)

    archive = args.output / 'RAW-EVIDENCE.zip'
    entries = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, path in sorted(selected.items()):
            item = {'path': name, **pin(path)}
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item['sha256']
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, raw)
            entries.append(item)
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None and set(check.namelist()) == {item['path'] for item in entries}
        for item in entries:
            raw = check.read(item['path'])
            assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
            assert sha(Path(item['source_path'])) == item['sha256']
    for prefix, root in roots.items():
        assert len([path for path in root.rglob('*') if path.is_file()]) == counts[prefix]['files']
    facts = {'schema': 'ck3-r44-observed-startup-red-actual-v1', 'run_id': RUN_ID,
        'checkout_head': launch['admitted_lease']['checkout_head'], 'source_root': report['agent_source_root'],
        'started_at': report['started_at'], 'finished_at': report['finished_at'], 'readiness_timeout_seconds': 900,
        'delayed_injection_requested': True, 'debug_mode_requested': True, 'injection_admitted': False,
        'startup_observation_count': len(startup), 'startup_first_last': [startup[0], startup[-1]],
        'saved_native_frame_count': 0, 'steps': [], 'business_pass': False, 'case_acceptance_pass': False,
        'native_status': report['status'], 'native_error': report['error'], 'session_error': report['session']['error'],
        'historical_cleanup_ok': False, 'historical_session_report': None,
        'historical_original_createprocess_handle_exit_code': None, 'historical_job_final_active_count': None,
        'host_original_parent_exit_code': parent['returncode'], 'independent_observer_handle_exit': observer,
        'independent_observer_handle_identity': observer_ready, 'normal_exit_zero_proven': False,
        'actual_current_closeout': current, 'keeper_original_parent_exit_code': keeper['keeper_actual_exit_code'],
        'keeper_final_task_sequence': keeper['keeper_report']['last_sequence'],
        'release_expected_task_sequence': release_expected, 'release_global_event_sequence': release['event']['sequence'],
        'release_resources': release['task']['resources'], 'command_exit_codes': codes,
        'final_steam_offline_review': offline, 'restored_display': display['after'], 'public_verify_result': verify,
        'predecessor_closure_mode': admission['closure']['mode'], 'bootstrap_reused': False,
        'startup_metrics': metrics, 'actual_frozen_input_comparison': comparison,
        'foreground_is_not_controlled_trial_variable': True, 'actual_debug_log_last_line': log_lines[-1],
        'setup_completion_marker_seen': False, 'exact_ci_final': ci,
        'ci_prior_original_query_pairs_verification_reused': 51, 'ci_tests_rerun': 0,
        'source05_large_package_repacked': False, 'save_bodies_read_or_archived': False,
        'cause_inference': None, 'game_actions_by_archiver': 0}
    write(args.output / 'FACTS.actual.json', facts)
    index = {'schema': 'ck3-raw-evidence-index-v1', 'run_id': RUN_ID,
        'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
        'source_roots': counts, 'entries': entries, 'pinned_only': pinned_only,
        'producer': pin(Path(__file__).resolve()),
        'separate_permanent_packages': ['docs/ck3-native-ai/2026-10-10-shared-saved-debug-source05.md',
            'docs/ck3-native-ai/2026-10-10-r43-observed-startup-red.md']}
    write(args.output / 'INDEX.json', index)
    validation = {'schema': 'ck3-r44-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'archive_members_exact': True, 'archive_crc_valid': True, 'all_archived_bytes_sha256_rechecked': True,
        'all_source_bytes_sha256_rechecked': True, 'source_root_counts_rechecked': True,
        'actual_command_pins_checked': True, 'script_derivation_pins_checked': True,
        'ci_existing_original_query_validation_reused': 51, 'ci_logs_nested_revalidated': False,
        'saved_campaign_body_reads': 0, 'saved_campaign_hashes_recomputed': 0, 'cache_bodies_read': 0,
        'old_large_STATE_or_sourceZIP_archived': False, 'new_sampling': False, 'runtime_operations': 0,
        'entries': len(entries), 'archive': index['archive'], 'facts_sha256': sha(args.output / 'FACTS.actual.json'),
        'index_sha256': sha(args.output / 'INDEX.json'), 'evidence_valid': True,
        'business_pass': False, 'normal_exit_zero_proven': False}
    write(args.output / 'VALIDATION.actual.json', validation)
    print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'facts': pin(args.output / 'FACTS.actual.json'),
        'index': pin(args.output / 'INDEX.json'), 'validation': pin(args.output / 'VALIDATION.actual.json')}, ensure_ascii=False))


if __name__ == '__main__':
    main()

"""Archive existing R41 evidence; preserve RED and missing historical shutdown operands."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

RUN_ID = 'bf-202609141645-5434332d4d--li-yu-dao--R0041'
COMMON = Path('C:/workspace/ck3-common-runtime')
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = COMMON / 'runs' / RUN_ID
KEEPER = COMMON / 'keepers/20261010-a03'
CASE = COMMON / 'cases/lyd-transaction-control-20261010-003'
PROFILE = CASE / 'state/profile'
DIAGNOSTIC = BASE / 'r41-startup-and-cleanup-diagnostic-20261010-001'
ADMISSIONS = Path('C:/Users/Administrator/AppData/Local/XarCk3Acceptance/live-run-ids-v1/bf-202609141645-5434332d4d/.shared-runtime-admissions-v1')
AUTHOR_FILES = [
    'root-record-command-20261010-001.py',
    'r41-root-observe-shared-run-20261010-001.py',
    'r41-root-derive-display-tools-20261010-001.py',
    'r41-root-display-tools-derivation-20261010-001.json',
    'r41-root-fit-desktop-20261010-001.py',
    'r41-root-fit-steam-window-20261010-001.py',
    'r41-root-write-direct-review-20261010-001.py',
    'r41-root-closeout-20261010-001.py',
    'r41-root-derive-closeout002-20261010-001.py',
    'r41-root-closeout002-derivation-20261010-001.json',
    'r41-root-closeout-20261010-002.py',
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


def declared_pins(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            yield value
        for child in value.values():
            yield from declared_pins(child)
    elif isinstance(value, list):
        for child in value:
            yield from declared_pins(child)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    roots = {'run': RUN, 'keeper': KEEPER, 'profile/logs': PROFILE / 'logs',
             'profile/crashes': PROFILE / 'crashes', 'profile/exceptions': PROFILE / 'exceptions',
             'profile/dumps': PROFILE / 'dumps', 'diagnostic/startup-and-cleanup': DIAGNOSTIC,
             'case/allocate-command-001': CASE / 'allocate-command-001',
             'case/allocation-bus-preflight-audit': CASE / 'allocation-bus-preflight-audit',
             'case/single-use-ledger': CASE / 'single-use-ledger',
             'case/state/control': CASE / 'state/control'}
    selected = {}
    counts = {}
    for prefix, root in roots.items():
        assert root.is_dir(), root
        paths = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files': len(paths)}
        for path in paths:
            assert path.suffix.lower() != '.ck3' and path.stat().st_size < 64 * 1024 * 1024, path
            selected[prefix + '/' + path.relative_to(root).as_posix()] = path
    selected['producer/package_evidence.py'] = Path(__file__).resolve()
    for name in AUTHOR_FILES:
        selected['producer/runtime-author/' + name] = BASE / name
    for row in load(BASE / 'r41-root-display-tools-derivation-20261010-001.json'):
        old, new = Path(row['old']), Path(row['new'])
        assert sha(old) == row['old_sha256'] and sha(new) == row['new_sha256']
        selected['producer/derivation-source/' + old.name] = old
    derivation = load(BASE / 'r41-root-closeout002-derivation-20261010-001.json')
    assert sha(Path(derivation['source'])) == derivation['source_sha256']
    assert sha(Path(derivation['new'])) == derivation['new_sha256']
    diagnostic_pin_count = 0
    for row in declared_pins(load(DIAGNOSTIC / 'INDEX.json')):
        path = Path(row['path'])
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path
        diagnostic_pin_count += 1
        if path.suffix.lower() == '.py':
            selected['producer/diagnostic-author/' + path.name] = path
    for suffix in ['machine.json', '000003/allocation.json', '000003/intent.json']:
        selected['machine-admission/' + suffix] = ADMISSIONS / suffix

    seed = BASE / 'live-attempt-034/checkpoints/D2a/checkpoint.ck3'
    save_copy = PROFILE / 'save games/restored_campaign.ck3'
    pinned_only = []
    for path in [seed, save_copy]:
        row = pin(path)
        assert row['bytes'] == 91711686 and row['sha256'] == 'a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c'
        pinned_only.append({'reason': 'saved campaign body pinned only', **row})
    # Source04 and exact CI are already separate permanent packages. Do not copy them here.
    separate_packages = [
        'docs/ck3-native-ai/2026-10-10-shared-delayed-injection-source04.md',
        'docs/ck3-native-ai/2026-10-10-common-poll-reporting-ci-fixture.md',
    ]
    report = load(RUN / 'native-report.json')
    diagnostic = load(DIAGNOSTIC / 'REPORT.actual.json')
    startup = report['saved_campaign_restore']['startup_observations']
    assert len(startup) == 714
    assert all(row['status'] == 'WAITING_FOR_INITIAL_NATIVE_CONNECTION'
               and row['connected'] is False and row['semantic_state_available'] is False
               and row['connection_generation'] == 0 and row['bridge_pid'] is None for row in startup)
    assert report['saved_campaign_restore']['observations'] == []
    assert report['status'] == 'RED' and report['steps'] == []
    assert report['cleanup_ok'] is False and report['session']['report'] is None
    assert report['managed_session_thread_finished'] is True
    assert diagnostic['startup_observation_count'] == len(startup)
    assert diagnostic['injector_attempt_directory_exists'] is False and diagnostic['native_wire_exists'] is False
    assert diagnostic['launch_failed_receipt_present'] is False
    assert not (RUN / 'native-report.native-wire.jsonl').exists()
    assert diagnostic['cleanup_findings']['historical_game_exit_code'] is None
    assert diagnostic['cleanup_findings']['historical_job_count_raw_receipt'] is None
    parent = load(RUN / 'host-original-process-exit.json')
    keeper_parent = load(RUN / 'keeper-actual-parent-exit.json')
    current = load(RUN / 'ACTUAL-CURRENT-CLOSEOUT.json')
    release = load(RUN / 'release-command-001/stdout.log')
    release_command = load(RUN / 'release-command-001/RESULT.actual.json')
    verify = load(RUN / 'verify-command-001/stdout.log')
    offline = load(RUN / 'steam-final-recovery-001/OFFLINE-REVIEW.actual.json')
    display = load(RUN / 'display-restore-001.json')
    launch = load(RUN / 'launch-intent.json')
    frozen = load(RUN / 'frozen-argv.json')
    argv = frozen['argv']
    assert argv[argv.index('--readiness-timeout') + 1] == '600'
    assert '--saved-campaign-inject-after-load' in argv
    assert parent['actual_original_popen_wait'] is True and parent['returncode'] == 1
    assert parent['normal_ck3_exit_inferred'] is False
    assert current['ck3_inventory']['processes'] == [] and current['case_processes'] == []
    assert current['process_read_errors'] == [] and all(row['exists'] is False for row in current['control_files'])
    assert current['historical_host_cleanup_ok'] is False
    assert current['historical_ck3_exit_code'] is None and current['historical_job_final_active_count'] is None
    assert current['normal_exit_zero_claimed'] is False
    assert keeper_parent['keeper_actual_exit_code'] == 0 and keeper_parent['keeper_report']['thread_exited'] is True
    assert release_command['exit_code'] == 0 and release['ok'] is True
    assert release['event']['sequence'] == 4277 and release['task']['resources'] == []
    assert release_command['argv'][release_command['argv'].index('--expected-sequence') + 1] == '4276'
    assert display['change_result'] == 0 and display['after']['width'] == 1024 and display['after']['height'] == 768
    assert offline['steam_offline_confirmed'] is True and sha(Path(offline['path'])) == offline['sha256']
    assert verify['status'] == 'NOT_RUN_OR_PRESERVED_FAILURE' and verify['business_pass'] is False
    command_results = {}
    for label, root, expected in [('allocate', CASE, 0), ('run', RUN, 2), ('verify', RUN, 2), ('release', RUN, 0)]:
        actual = load(root / (label + '-command-001/RESULT.actual.json'))
        assert actual['exit_code'] == expected
        for channel in ['stdout', 'stderr']:
            row = actual[channel]
            assert Path(row['path']).stat().st_size == row['bytes'] and sha(Path(row['path'])) == row['sha256']
        command_results[label] = actual['exit_code']

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
    facts = {'schema': 'ck3-r41-shared-runtime-startup-red-actual-v1', 'run_id': RUN_ID,
        'checkout_head': launch['admitted_lease']['checkout_head'], 'agent_source_root': report['agent_source_root'],
        'started_at': report['started_at'], 'finished_at': report.get('finished_at'), 'readiness_timeout_seconds': 600,
        'delayed_injection_requested': True, 'injection_admitted': False, 'startup_observation_count': len(startup),
        'startup_first_last': [startup[0], startup[-1]], 'saved_native_frame_count': 0,
        'command_exit_codes': command_results, 'native_status': report['status'], 'native_error': report.get('error'),
        'steps': report['steps'], 'host_original_parent_exit_code': parent['returncode'],
        'historical_host_cleanup_ok': report['cleanup_ok'], 'historical_session_report': None,
        'historical_ck3_exit_code': None, 'historical_job_final_active_count': None,
        'normal_exit_zero_proven': False, 'source_qualified_cleanup_findings': diagnostic['cleanup_findings'],
        'actual_current_closeout': current, 'keeper_original_parent_exit_code': keeper_parent['keeper_actual_exit_code'],
        'actual_release_sequence': release['event']['sequence'], 'actual_release_resources': release['task']['resources'],
        'final_steam_offline_review': offline, 'restored_display': display['after'], 'public_verify_result': verify,
        'closeout001': {'source': str(BASE / 'r41-root-closeout-20261010-001.py'),
            'correction_derivation': derivation, 'separate_actual_stdout_stderr_preserved': False,
            'boundary': 'Original producer and source-derived correction preserved; no retrospective failure stdout/stderr is fabricated.'},
        'separate_permanent_packages': separate_packages, 'game_actions_by_this_producer': 0,
        'business_pass': False, 'case_acceptance_pass': False}
    write(args.output / 'FACTS.actual.json', facts)
    index = {'schema': 'ck3-raw-evidence-index-v1', 'run_id': RUN_ID,
        'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
        'source_roots': counts, 'entries': entries, 'pinned_only': pinned_only,
        'separate_permanent_packages': separate_packages, 'producer': pin(Path(__file__).resolve())}
    write(args.output / 'INDEX.json', index)
    validation = {'schema': 'ck3-r41-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'archive_members_exact': True, 'archive_crc_valid': True, 'all_archived_bytes_sha256_rechecked': True,
        'all_source_bytes_sha256_rechecked': True, 'source_root_file_counts_rechecked': True,
        'diagnostic_original_index_pins_rechecked': True, 'diagnostic_original_index_pin_count': diagnostic_pin_count,
        'actual_command_stdout_stderr_pins_rechecked': True, 'script_derivation_pins_rechecked': True,
        'saved_campaign_bodies_archived': False, 'entries': len(entries), 'archive_bytes': archive.stat().st_size,
        'archive_sha256': sha(archive), 'facts_sha256': sha(args.output / 'FACTS.actual.json'),
        'index_sha256': sha(args.output / 'INDEX.json'), 'producer_sha256': sha(Path(__file__).resolve()),
        'evidence_valid': True, 'business_pass': False, 'case_acceptance_pass': False, 'normal_exit_zero_proven': False}
    write(args.output / 'VALIDATION.actual.json', validation)
    print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'source_roots': counts}, indent=2))


if __name__ == '__main__':
    main()

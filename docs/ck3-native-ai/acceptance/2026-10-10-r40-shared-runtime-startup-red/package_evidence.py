"""Seal existing R40 files and actual closeout; no runtime or settings actions."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

RUN_ID = 'bf-202609141645-5434332d4d--li-yu-dao--R0040'
COMMON = Path('C:/workspace/ck3-common-runtime')
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
RUN = COMMON / 'runs' / RUN_ID
KEEPER = COMMON / 'keepers/20261010-a02'
CASE = COMMON / 'cases/lyd-transaction-control-20261010-002'
PROFILE = CASE / 'state/profile'
ADMISSIONS = Path('C:/Users/Administrator/AppData/Local/XarCk3Acceptance/live-run-ids-v1/bf-202609141645-5434332d4d/.shared-runtime-admissions-v1')
AUTHOR_FILES = [
    'r40-root-observe-shared-run-20261010-001.py',
    'r40-root-observe-shared-run-20261010-002.py',
    'r40-root-observe-shared-run-20261010-003.py',
    'r40-root-derive-display-tools-20261010-001.py',
    'r40-root-display-tools-derivation-20261010-001.json',
    'r40-root-fit-desktop-20261010-001.py',
    'r40-root-fit-steam-window-20261010-001.py',
    'r40-root-write-direct-review-20261010-001.py',
    'r40-root-derive-closeout-20261010-001.py',
    'r40-root-closeout-derivation-20261010-001.json',
    'r40-root-restore-display-stop-20261010-001.py',
    'r40-root-prepare-successor-inputs-20261010-001.py',
]


def sha(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def pin(path: Path) -> dict:
    return {'source_path': str(path), 'bytes': path.stat().st_size, 'sha256': sha(path)}


def load(path: Path):
    return json.loads(path.read_bytes())


def write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


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
    parser.add_argument('--diagnostic-root', required=True, action='append', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    roots = {'run': RUN, 'keeper': KEEPER, 'profile/logs': PROFILE / 'logs',
             'profile/crashes': PROFILE / 'crashes', 'profile/exceptions': PROFILE / 'exceptions',
             'profile/dumps': PROFILE / 'dumps'}
    for number, root in enumerate(args.diagnostic_root, 1):
        roots[f'diagnostic/{number:03d}'] = root
    selected = {}
    pinned_only = []
    counts = {}
    for prefix, root in roots.items():
        assert root.is_dir(), root
        paths = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files': len(paths)}
        for path in paths:
            assert path.suffix.lower() != '.ck3' and path.stat().st_size < 64 * 1024 * 1024, path
            selected[prefix + '/' + path.relative_to(root).as_posix()] = path
    case_paths = sorted(path for path in CASE.rglob('*') if path.is_file()
                        and not path.is_relative_to(PROFILE)
                        and not path.relative_to(CASE).parts[0].startswith('rebase-check-'))
    counts['case/receipts-and-inputs'] = {'source_root': str(CASE), 'files': len(case_paths),
        'selection': 'All non-profile files except rebase-check; profile logs are separately archived. CI/rebase tests have a separate permanent package.'}
    for path in case_paths:
        selected['case/' + path.relative_to(CASE).as_posix()] = path
    for path in sorted((PROFILE / 'save games').rglob('*')):
        if path.is_file():
            pinned_only.append({'reason': 'saved campaign body pinned only', **pin(path)})
    selected['producer/package_evidence.py'] = Path(__file__).resolve()
    for name in AUTHOR_FILES:
        selected['producer/runtime-author/' + name] = BASE / name
    for row in load(BASE / 'r40-root-display-tools-derivation-20261010-001.json'):
        old, new = Path(row['old']), Path(row['new'])
        assert sha(old) == row['old_sha256'] and sha(new) == row['new_sha256']
        selected['producer/derivation-source/' + old.name] = old
    closeout = load(BASE / 'r40-root-closeout-derivation-20261010-001.json')
    assert sha(Path(closeout['source'])) == closeout['source_sha256']
    assert sha(Path(closeout['destination'])) == closeout['sha256']
    selected['producer/derivation-source/' + Path(closeout['source']).name] = Path(closeout['source'])
    diagnostic_pin_count = 0
    for root in args.diagnostic_root:
        for row in declared_pins(load(root / 'INDEX.json')):
            path = Path(row['path'])
            assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path
            diagnostic_pin_count += 1
            if path.suffix.lower() == '.py':
                selected['producer/diagnostic-author/' + path.name] = path
    for suffix in ['machine.json', '000002/allocation.json', '000002/intent.json']:
        selected['machine-admission/' + suffix] = ADMISSIONS / suffix
    report = load(RUN / 'native-report.json')
    shutdown = report['session']['report']['shutdown']
    parent = load(RUN / 'host-original-process-exit.json')
    keeper_parent = load(RUN / 'keeper-actual-parent-exit.json')
    release = load(RUN / 'release-command-001/stdout.log')
    release_command = load(RUN / 'release-command-001/RESULT.actual.json')
    verify = load(RUN / 'public-verify-command-001/stdout.log')
    offline = load(RUN / 'steam-final-recovery-001/OFFLINE-REVIEW.actual.json')
    display = load(RUN / 'display-restore-001.json')
    launch = load(RUN / 'launch-intent.json')
    frozen = load(RUN / 'frozen-argv.json')
    argv = frozen['argv']
    assert argv[argv.index('--readiness-timeout') + 1] == '600'
    assert report['status'] == 'RED' and report['steps'] == []
    assert parent['actual_original_popen_wait'] is True and parent['returncode'] == 1
    assert parent['normal_ck3_exit_inferred'] is False and shutdown['ck3_exit_code'] == 1
    assert shutdown['tree_gone'] is True and shutdown['cleanup_proven'] is True
    assert shutdown['job_active_processes_final'] == 0 and shutdown['final_ck3_inventory']['processes'] == []
    assert all(shutdown['control_files_absent'].values())
    assert keeper_parent['keeper_actual_exit_code'] == 0 and keeper_parent['keeper_report']['thread_exited'] is True
    assert release_command['exit_code'] == 0 and release['ok'] is True
    assert release['event']['sequence'] == 4235 and release['task']['resources'] == []
    assert release_command['argv'][release_command['argv'].index('--expected-sequence') + 1] == '4234'
    assert display['change_result'] == 0 and display['after']['width'] == 1024 and display['after']['height'] == 768
    assert offline['steam_offline_confirmed'] is True and sha(Path(offline['path'])) == offline['sha256']
    assert verify['status'] == 'NOT_RUN_OR_PRESERVED_FAILURE' and verify['business_pass'] is False
    command_results = {}
    for label, root, expected in [('prepare', CASE, 0), ('preflight', CASE, 0), ('allocate', CASE, 0),
                                   ('public-run', RUN, 2), ('public-verify', RUN, 2)]:
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
    facts = {'schema': 'ck3-r40-shared-runtime-startup-red-actual-v1', 'run_id': RUN_ID,
        'checkout_head': launch['admitted_lease']['checkout_head'], 'agent_source_root': report['agent_source_root'],
        'started_at': report['started_at'], 'finished_at': report.get('finished_at'), 'readiness_timeout_seconds': 600,
        'command_exit_codes': command_results, 'native_status': report['status'], 'native_error': report.get('error'),
        'steps': report['steps'], 'host_original_parent_exit_code': parent['returncode'],
        'managed_ck3_exit_code': shutdown['ck3_exit_code'], 'normal_exit_zero_proven': False,
        'tree_gone': shutdown['tree_gone'], 'final_ck3_inventory_empty': True,
        'control_files_absent': shutdown['control_files_absent'], 'keeper_original_parent_exit_code': keeper_parent['keeper_actual_exit_code'],
        'actual_release_sequence': release['event']['sequence'], 'actual_release_resources': release['task']['resources'],
        'final_steam_offline_review': offline, 'restored_display': display['after'], 'public_verify_result': verify,
        'failed_monitor001': {'source': str(BASE / AUTHOR_FILES[0]), 'separate_actual_stdout_stderr_preserved': False,
            'boundary': 'Original producer preserved; no retrospective stdout/stderr is fabricated.'},
        'game_actions_by_this_producer': 0}
    write(args.output / 'FACTS.actual.json', facts)
    index = {'schema': 'ck3-raw-evidence-index-v1', 'run_id': RUN_ID,
        'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
        'source_roots': counts, 'entries': entries, 'pinned_only': pinned_only, 'producer': pin(Path(__file__).resolve())}
    write(args.output / 'INDEX.json', index)
    validation = {'schema': 'ck3-r40-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'archive_members_exact': True, 'archive_crc_valid': True, 'all_archived_bytes_sha256_rechecked': True,
        'all_source_bytes_sha256_rechecked': True, 'source_root_file_counts_rechecked': True,
        'diagnostic_original_index_pins_rechecked': True, 'diagnostic_original_index_pin_count': diagnostic_pin_count,
        'actual_command_stdout_stderr_pins_rechecked': True, 'script_derivation_pins_rechecked': True,
        'saved_campaign_bodies_archived': False, 'entries': len(entries), 'archive_bytes': archive.stat().st_size,
        'archive_sha256': sha(archive), 'facts_sha256': sha(args.output / 'FACTS.actual.json'),
        'index_sha256': sha(args.output / 'INDEX.json'), 'producer_sha256': sha(Path(__file__).resolve()),
        'evidence_valid': True, 'business_pass': False, 'case_acceptance_pass': False, 'normal_exit_zero_proven': False}
    write(args.output / 'VALIDATION.actual.json', validation)
    print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'pinned_only': pinned_only, 'source_roots': counts}, indent=2))


if __name__ == '__main__':
    main()

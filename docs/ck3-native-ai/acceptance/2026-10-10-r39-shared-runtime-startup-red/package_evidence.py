"""Freeze existing R39 evidence; never launch, repair, or modify the runtime."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

RUN_ID = 'bf-202609141645-5434332d4d--li-yu-dao--R0039'
COMMON = Path('C:/workspace/ck3-common-runtime')
RUN = COMMON / 'runs' / RUN_ID
KEEPER = COMMON / 'keepers/20261010-a01'
PROFILE = COMMON / 'cases/lyd-transaction-control-20261010-001/state/profile'
DIAGNOSTIC = Path('C:/workspace/ck3_lyd_runtime_20261004/r39-saved-startup-readiness-diagnostic-20261010-001')
DIAGNOSTIC_SCRIPT = Path('C:/workspace/ck3_lyd_runtime_20261004/r39_saved_readiness_diagnostic_20261010_001.py')
ADMISSIONS = Path('C:/Users/Administrator/AppData/Local/XarCk3Acceptance/live-run-ids-v1/bf-202609141645-5434332d4d/.shared-runtime-admissions-v1')


def digest(path: Path) -> str:
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def pin(path: Path) -> dict:
    return {'source_path': str(path), 'bytes': path.stat().st_size, 'sha256': digest(path)}


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
    parser.add_argument('--supplement-root', action='append', default=[], type=Path)
    parser.add_argument('--supplement-script', action='append', default=[], type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    roots = {'run': RUN, 'keeper': KEEPER, 'profile/logs': PROFILE / 'logs',
             'profile/crashes': PROFILE / 'crashes', 'profile/exceptions': PROFILE / 'exceptions',
             'profile/dumps': PROFILE / 'dumps', 'diagnostic/readiness': DIAGNOSTIC}
    for number, root in enumerate(args.supplement_root, 1):
        roots[f'diagnostic/supplement-{number:03d}'] = root
    selected = {}
    excluded = []
    counts = {}
    for prefix, root in roots.items():
        assert root.is_dir(), root
        paths = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files': len(paths)}
        for path in paths:
            label = prefix + '/' + path.relative_to(root).as_posix()
            if path.suffix.lower() == '.ck3' or path.stat().st_size > 64 * 1024 * 1024:
                excluded.append({'reason': 'save/large body pinned only', **pin(path)})
            else:
                selected[label] = path
    save_root = PROFILE / 'save games'
    for path in sorted(save_root.rglob('*')):
        if path.is_file():
            excluded.append({'reason': 'saved campaign body pinned only', **pin(path)})
    extras = {'producer/package_evidence.py': Path(__file__).resolve(),
              'producer/readiness_diagnostic.py': DIAGNOSTIC_SCRIPT,
              'machine-admission/machine.json': ADMISSIONS / 'machine.json',
              'machine-admission/000001/allocation.json': ADMISSIONS / '000001/allocation.json',
              'machine-admission/000001/intent.json': ADMISSIONS / '000001/intent.json'}
    for number, path in enumerate(args.supplement_script, 1):
        extras[f'producer/supplement-{number:03d}.py'] = path
    known_producers = {path.resolve() for path in extras.values()}
    diagnostic_pin_count = 0
    for root in [DIAGNOSTIC, *args.supplement_root]:
        index_path = root / 'INDEX.json'
        if index_path.is_file():
            for row in declared_pins(load(index_path)):
                path = Path(row['path'])
                assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], path
                diagnostic_pin_count += 1
                if path.suffix.lower() == '.py' and path.resolve() not in known_producers:
                    extras['producer/' + path.name] = path
                    known_producers.add(path.resolve())
    selected.update(extras)
    report = load(RUN / 'native-report.json')
    session = report['session']['report']
    shutdown = session['shutdown']
    public = load(RUN / 'public-run-command-001/RESULT.actual.json')
    verify_command = load(RUN / 'public-verify-command-001/RESULT.actual.json')
    verify = load(RUN / 'public-verify-command-001/stdout.log')
    parent = load(RUN / 'host-original-process-exit.json')
    keeper_parent = load(RUN / 'keeper-actual-parent-exit.json')
    first_release = load(RUN / 'release-command-001/RESULT.actual.json')
    first_rejection = load(RUN / 'release-command-001/stdout.log')
    release = load(RUN / 'release-command-002/stdout.log')
    second_release = load(RUN / 'release-command-002/RESULT.actual.json')
    display = load(RUN / 'display-restore-001.json')
    offline = load(RUN / 'steam-final-recovery-001/OFFLINE-REVIEW.actual.json')
    launch = load(RUN / 'launch-intent.json')
    diagnostic = load(DIAGNOSTIC / 'REPORT.actual.json')
    diagnostic_index = load(DIAGNOSTIC / 'INDEX.json')
    allocation = load(ADMISSIONS / '000001/allocation.json')
    admission_intent = load(ADMISSIONS / '000001/intent.json')
    assert report['status'] == 'RED' and report['steps'] == []
    assert public['exit_code'] == 2 and verify_command['exit_code'] == 2
    assert verify['status'] == 'NOT_RUN_OR_PRESERVED_FAILURE' and verify['business_pass'] is False
    assert parent['actual_original_popen_wait'] is True and parent['returncode'] == 1
    assert parent['normal_ck3_exit_inferred'] is False and shutdown['ck3_exit_code'] == 1
    assert shutdown['tree_gone'] is True and shutdown['cleanup_proven'] is True
    assert shutdown['job_active_processes_final'] == 0
    assert shutdown['final_ck3_inventory']['processes'] == []
    assert all(shutdown['control_files_absent'].values())
    assert keeper_parent['keeper_actual_exit_code'] == 0
    assert keeper_parent['keeper_report']['thread_exited'] is True
    assert first_release['exit_code'] == 3 and first_rejection['code'] == 'CAS_CONFLICT'
    assert first_rejection['reason'] == 'screen operation requires exact bus CLI SHA-256 pin'
    assert second_release['exit_code'] == 0 and release['ok'] is True
    assert release['event']['sequence'] == 4222 and release['task']['resources'] == []
    assert display['change_result'] == 0
    assert display['after']['width'] == 1024 and display['after']['height'] == 768
    assert offline['steam_offline_confirmed'] is True
    assert digest(Path(offline['path'])) == offline['sha256']
    assert launch['admitted_lease']['checkout_head'] == '00b88fc4df0b8b4cea8b15ff85de8f244825a329'
    assert diagnostic['observation_count'] == 146
    assert allocation['run_id'] == RUN_ID
    assert admission_intent['closure']['mode'] == 'first-machine-legacy-profile-mcp-closure'
    for value in diagnostic_index.values():
        if isinstance(value, dict) and {'path', 'bytes', 'sha256'} <= value.keys():
            path = Path(value['path'])
            assert path.stat().st_size == value['bytes'] and digest(path) == value['sha256']
    archive = args.output / 'RAW-EVIDENCE.zip'
    entries = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for label, path in sorted(selected.items()):
            record = {'path': label, **pin(path)}
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == record['sha256']
            info = zipfile.ZipInfo(label, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, raw)
            entries.append(record)
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None
        assert set(check.namelist()) == {row['path'] for row in entries}
        for row in entries:
            raw = check.read(row['path'])
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
            assert digest(Path(row['source_path'])) == row['sha256']
    for prefix, root in roots.items():
        assert len([path for path in root.rglob('*') if path.is_file()]) == counts[prefix]['files']
    facts = {'schema': 'ck3-r39-shared-runtime-startup-red-actual-v1', 'run_id': RUN_ID,
             'checkout_head': launch['admitted_lease']['checkout_head'], 'agent_source_root': report['agent_source_root'],
             'started_at': report['started_at'], 'finished_at': report.get('finished_at'),
             'public_run_exit_code': public['exit_code'], 'native_status': report['status'], 'native_error': report.get('error'),
             'steps': report['steps'], 'host_original_parent_exit_code': parent['returncode'],
             'managed_ck3_exit_code': shutdown['ck3_exit_code'], 'normal_exit_zero_proven': False,
             'tree_gone': shutdown['tree_gone'], 'final_ck3_inventory_empty': shutdown['final_ck3_inventory']['processes'] == [],
             'control_files_absent': shutdown['control_files_absent'], 'keeper_original_parent_exit_code': keeper_parent['keeper_actual_exit_code'],
             'first_release_exit_code': first_release['exit_code'], 'first_release_rejection': first_rejection,
             'actual_release_sequence': release['event']['sequence'], 'actual_release_resources': release['task']['resources'],
             'final_steam_offline_review': offline, 'restored_display': display['after'],
             'public_verify_exit_code': verify_command['exit_code'], 'public_verify_result': verify,
             'first_machine_bootstrap_admitted_run': allocation['run_id'],
             'readiness_diagnostic': {'observations': diagnostic['observation_count'], 'report_sha256': digest(DIAGNOSTIC / 'REPORT.actual.json')},
             'game_actions_by_this_producer': 0}
    write(args.output / 'FACTS.actual.json', facts)
    index = {'schema': 'ck3-raw-evidence-index-v1', 'run_id': RUN_ID,
             'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': digest(archive)},
             'source_roots': counts, 'entries': entries, 'pinned_only': excluded,
             'producer': pin(Path(__file__).resolve())}
    write(args.output / 'INDEX.json', index)
    validation = {'schema': 'ck3-r39-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
                  'archive_members_exact': True, 'archive_crc_valid': True, 'all_archived_bytes_sha256_rechecked': True,
                  'all_source_bytes_sha256_rechecked': True, 'source_root_file_counts_rechecked': True,
                  'diagnostic_original_index_pins_rechecked': True, 'diagnostic_original_index_pin_count': diagnostic_pin_count,
                  'saved_campaign_bodies_archived': False,
                  'entries': len(entries), 'archive_bytes': archive.stat().st_size, 'archive_sha256': digest(archive),
                  'facts_sha256': digest(args.output / 'FACTS.actual.json'), 'index_sha256': digest(args.output / 'INDEX.json'),
                  'producer_sha256': digest(Path(__file__).resolve()),
                  'evidence_valid': True, 'business_pass': False, 'case_acceptance_pass': False, 'normal_exit_zero_proven': False}
    write(args.output / 'VALIDATION.actual.json', validation)
    print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'pinned_only': excluded, 'source_roots': counts}, indent=2))


if __name__ == '__main__':
    main()

"""Preserve existing R45 actual records only after ROOT supplies completed closure; no runtime operations."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
COMMON = Path('C:/workspace/ck3-common-runtime')
RUN_ID = 'bf-202609141645-5434332d4d--li-yu-dao--R0045'
RUN = COMMON / 'runs' / RUN_ID
CASE = COMMON / 'cases/lyd-transaction-control-20261010-007'
KEEPER = COMMON / 'keepers/20261010-a07'
PROFILE = CASE / 'state/profile'

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


def read_ref(row):
    assert isinstance(row, dict) and set(row) >= {'path', 'bytes', 'sha256'}, 'Actual ref3 required'
    path = Path(row['path'])
    assert path.suffix.lower() != '.ck3' and path.stat().st_size < 16 * 1024 * 1024
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path
    return load(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--closed-inputs', type=Path, required=True)
    parser.add_argument('--closed-inputs-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert sha(args.closed_inputs) == args.closed_inputs_sha256
    inputs = load(args.closed_inputs)
    assert inputs['run_id'] == RUN_ID
    assert inputs['checkout_head'] == 'fde5fb0a03d24ba00b8a09ce0a52462a50882671'
    assert inputs['root_authorized_after_actual_closeout_and_release'] is True
    assert inputs['actual_result'] is not None and inputs['release_event_sequence'] is not None
    assert all(row['status'] != 'PENDING' for row in inputs['supplements'])
    current = read_ref(inputs['actual_current_closeout'])
    release = read_ref(inputs['actual_release'])
    assert current['ck3_inventory']['processes'] == [] and current['case_processes'] == []
    assert current['process_read_errors'] == [] and all(not row['exists'] for row in current['control_files'])
    assert release['ok'] is True and release['task']['resources'] == [] and release['task']['state'] == 'done'
    assert release['event']['sequence'] == inputs['release_event_sequence']
    assert release['task']['task_id'] == 'common-acceptance-12004-20261010-a07'
    keeper = load(RUN/'keeper-actual-parent-exit.json')
    assert keeper['keeper_actual_exit_code'] == 0 and keeper['keeper_report']['thread_exited'] is True
    assert keeper['keeper_report']['last_sequence'] == inputs['release_expected_sequence']
    report = load(RUN/'native-report.json')
    assert report['managed_session_thread_finished'] is True
    launch = load(RUN/'launch-intent.json')
    assert launch['admitted_lease']['checkout_head'] == inputs['checkout_head']
    argv = load(RUN/'frozen-argv.json')['argv']
    assert argv[argv.index('--readiness-timeout') + 1] == '900'
    assert argv.count('--saved-campaign-inject-after-load') == argv.count('--saved-campaign-debug-mode') == 1

    admission = load(RUN/'predecessor-admission.json')
    admission_root = Path(admission['machine_admission'])
    roots = {
        'run': RUN, 'keeper': KEEPER, 'case/prepared': CASE/'prepared',
        'case/allocation-bus-preflight-audit': CASE/'allocation-bus-preflight-audit',
        'case/single-use-ledger': CASE/'single-use-ledger', 'case/state/control': CASE/'state/control',
        'profile/logs': PROFILE/'logs',
        'sourceonly/prepare-inputs': BASE/'r45-transaction-control-prepare-sourceonly-20261010-001',
        'synthetic/etw-preparation': BASE/'r45-etw-cpu-observation-preparation-20261010-001',
        'synthetic/cpu-proof': BASE/'r45-root-etw-synthetic-20261010-001',
        'machine-admission/current': admission_root,
    }
    for root in sorted(BASE.glob('r45-root-*')):
        if root.is_dir() and root not in roots.values() and 'etw' not in root.name:
            roots['root-command/' + root.name] = root
    for row in inputs['supplements']:
        if row['status'] == 'AVAILABLE':
            root = Path(row['root'])
            assert root.is_dir(), root
            roots[row['role']] = root
        else:
            assert row.get('reason') and row.get('actual_failure_ref'), row
            read_ref(row['actual_failure_ref'])

    selected, omitted, counts = {}, [], {}
    binary_suffixes = {'.ck3', '.etl', '.exe', '.dll', '.pdb', '.dmp', '.csv'}
    export_names = {'process.txt', 'profile.txt', 'stack.txt'}
    for prefix, root in roots.items():
        assert root.is_dir(), root
        files = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files_present': len(files)}
        for path in files:
            relative = path.relative_to(root)
            excluded = (path.suffix.lower() in binary_suffixes or path.name.lower() in export_names
                        or 'temp' in relative.parts or path.stat().st_size >= 16*1024*1024
                        or path.suffix.lower() == '.zip' and not prefix.startswith('ci/'))
            if excluded:
                omitted.append({'source_path': str(path), 'bytes': path.stat().st_size,
                                'body_read': False, 'reason': 'large/binary/body/prior archive remains external'})
                continue
            selected[prefix + '/' + relative.as_posix()] = path
    selected['case/state/preparation.json'] = CASE/'state/preparation.json'
    selected['machine-admission/machine.json'] = admission_root.parent/'machine.json'
    selected['producer/package_evidence.py'] = Path(__file__).resolve()
    selected['producer/CLOSED-INPUTS.actual.json'] = args.closed_inputs
    for pattern in ['r45-root-*.py', 'r45-root-*derivation*.json', 'r45-root-derive-*.actual.json',
                    'r45-agent-*.py', 'r45_prepare*.py', 'r45_read*.py', 'r45_summarize*.py', 'r45_seal*.py']:
        for path in sorted(BASE.glob(pattern)):
            selected['producer/root/' + path.name] = path
    for row in inputs['small_file_refs']:
        path = Path(row['path'])
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
        assert path.stat().st_size < 16*1024*1024 and path.suffix.lower() not in binary_suffixes
        selected['supplement-files/' + path.name] = path
    references = list(inputs['external_reference_only'])
    prepared = load(CASE/'prepared/prepared-case.json')
    seed = prepared['startup']['saved_campaign']
    for path in [Path(seed['save']), PROFILE/'save games/restored_campaign.ck3']:
        assert path.stat().st_size == seed['bytes']
        references.append({'path': str(path), 'bytes': seed['bytes'], 'sha256': seed['sha256'],
                           'pin_source': 'actual prepared-case startup', 'body_read': False, 'hash_recomputed': False})
    for row in references:
        assert set(row) >= {'path', 'bytes', 'sha256'} and len(row['sha256']) == 64
        assert Path(row['path']).stat().st_size == row['bytes']

    args.output.mkdir(parents=True, exist_ok=False)
    archive = args.output/'RAW-EVIDENCE.zip'
    entries = []
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
        for name, path in sorted(selected.items()):
            item = {'path': name, **pin(path)}
            raw = path.read_bytes()
            assert hashlib.sha256(raw).hexdigest() == item['sha256']
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)); info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, raw); entries.append(item)
    with zipfile.ZipFile(archive) as check:
        assert check.testzip() is None and set(check.namelist()) == {row['path'] for row in entries}
        for row in entries:
            raw = check.read(row['path'])
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
            assert sha(Path(row['source_path'])) == row['sha256']
    facts = {
        'schema': 'ck3-r45-runtime-actual-evidence-v1', 'run_id': RUN_ID,
        'checkout_head': inputs['checkout_head'], 'actual_result': inputs['actual_result'],
        'readiness_timeout_seconds': 900, 'native_report_status': report['status'],
        'native_report_error': report.get('error'), 'historical_cleanup_ok': report.get('cleanup_ok'),
        'historical_session': report.get('session'), 'actual_step_count': len(report['steps']),
        'actual_current_closeout': current, 'actual_release': release,
        'keeper_original_parent_exit': keeper, 'root_observed_transcript': inputs['root_observed_transcript'],
        'identity_issue': inputs['identity_issue'], 'supplements': inputs['supplements'],
        'synthetic_semantic_or_business_credit': False, 'actual_cpu_cause_credit': None,
        'seed_or_large_body_reads': 0, 'runtime_operations': 0,
        'whole_product_pass_claimed': False,
    }
    write(args.output/'FACTS.actual.json', facts)
    index = {'schema': 'ck3-raw-evidence-index-v1', 'run_id': RUN_ID,
             'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
             'source_roots': counts, 'entries': entries, 'pinned_only': references,
             'omitted_without_body_reads': omitted, 'producer': pin(Path(__file__).resolve())}
    write(args.output/'INDEX.json', index)
    write(args.output/'VALIDATION.actual.json', {
        'schema': 'ck3-r45-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
        'archive_crc_members_and_bytes': True, 'source_bytes_verified': True,
        'seed_or_large_body_reads': 0, 'runtime_operations': 0, 'new_sampling': False,
        'ci_requeried_or_retested': False, 'business_pass_claimed': False,
        'entries': len(entries), 'archive': index['archive']})
    print(json.dumps({'archive': index['archive'], 'entries': len(entries)}, ensure_ascii=False))


if __name__ == '__main__':
    main()

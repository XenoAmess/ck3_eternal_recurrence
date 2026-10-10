"""Seal Source05 source-only receipts. No build, test, game or repository mutation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import zipfile

BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
META = Path('C:/workspace/ck3-common-runtime/20261010-004')
OLD = Path('C:/workspace/ck3-common-runtime/20261010-003')
SOURCE = Path('C:/csr5')
OUT = Path(__file__).resolve().parent
CANDIDATE = BASE / 'shared-saved-campaign-debug-mode-sourceonly-20261010-002'
INTEGRATION = BASE / 'shared-saved-debug-main-integration-20261010-001'
STATIC_REVIEW = BASE / 'r42-source05-freezer-binder-review-20261010-001'
ACTUAL_REVIEW = BASE / 'r42-source05-actual-review-20261010-001'
AUTHOR_NAMES = [
    'prepare_shared_saved_debug_mode_candidate_20261010.py',
    'freeze_shared_saved_debug_attempt002_20261010.py',
    'r42-root-derive-source05-tools-20261010-001.py',
    'r42-root-source05-tools-derivation-20261010-001.json',
    'r42-root-freeze-source05-20261010-001.py',
    'r42-root-derive-freezer002-20261010-001.py',
    'r42-root-freezer002-derivation-20261010-001.json',
    'r42-root-freeze-source05-20261010-002.py',
    'r42-root-bind-runtime-20261010-001.py',
    'r42-root-frozen-python-checks-20261010-001.py',
    'r42_source05_freezer_binder_review_20261010_001.py',
    'r42_source05_actual_review_20261010_001.py',
    'root-record-command-20261010-001.py',
    'r42-source05-derive-compact-evidence-20261010-001.py',
    'r42-source05-compact-producer-derivation-20261010-001.json',
]

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

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

def rows(value):
    if isinstance(value, dict):
        if {'path', 'bytes', 'sha256'} <= value.keys():
            yield value
        for child in value.values():
            yield from rows(child)
    elif isinstance(value, list):
        for child in value:
            yield from rows(child)

def verify(row):
    path = Path(row['path'])
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path

roots = {
    'author/sourceonly002': CANDIDATE,
    'author/main-integration': INTEGRATION,
    'review/static': STATIC_REVIEW,
    'review/actual': ACTUAL_REVIEW,
    'root/freeze-command': BASE / 'r42-root-source05-freeze-20261010-001',
    'root/bind-command': BASE / 'r42-root-source05-bind-20261010-001',
    'root/python-check-command': BASE / 'r42-root-source05-python-checks-20261010-001',
}
selected = {}
counts = {}
for prefix, root in roots.items():
    paths = sorted(path for path in root.rglob('*') if path.is_file())
    assert root.is_dir() and paths, root
    counts[prefix] = {'source_root': str(root), 'files': len(paths)}
    archived_paths = paths
    if root == CANDIDATE:
        owned = set(load(ACTUAL_REVIEW / 'REVIEW.actual.json')['changed_paths_exact'])
        archived_paths = [path for path in paths if path.relative_to(root).parts[0] != 'source'
                          or path.relative_to(root / 'source').as_posix() in owned]
        counts[prefix]['selection'] = 'All candidate receipts, before bytes and five owned source files; copied unchanged package dependencies stay external with original manifest pins.'
    counts[prefix]['archived_files'] = len(archived_paths)
    for path in archived_paths:
        assert path.stat().st_size < 8 * 1024 * 1024 and path.suffix.lower() not in ['.ck3', '.zip']
        selected[prefix + '/' + path.relative_to(root).as_posix()] = path
metadata_files = sorted(path for path in META.rglob('*') if path.is_file() and path.name not in ['shared-source05.zip', 'freeze.index'])
counts['runtime/source05'] = {'source_root': str(META), 'files': len(metadata_files),
    'selection': 'All actual Source05 metadata and frozen checks except the full source ZIP and temporary whole-repository Git index, which are pinned only.'}
for path in metadata_files:
    assert path.stat().st_size < 8 * 1024 * 1024
    selected['runtime/source05/' + path.relative_to(META).as_posix()] = path
selected['author/prior001/FAILURE.authoring.json'] = BASE / 'shared-saved-campaign-debug-mode-sourceonly-20261010-001/FAILURE.authoring.json'
selected['producer/package_evidence.py'] = Path(__file__).resolve()
for name in AUTHOR_NAMES:
    selected['producer/' + name] = BASE / name
declared_count = 0
for index in [CANDIDATE / 'INDEX.json', INTEGRATION / 'INDEX.json', STATIC_REVIEW / 'INDEX.json', ACTUAL_REVIEW / 'INDEX.json']:
    for row in rows(load(index)):
        verify(row)
        declared_count += 1
        path = Path(row['path'])
        if path.suffix.lower() == '.py' and path.parent == BASE:
            selected['producer/' + path.name] = path

actual = load(ACTUAL_REVIEW / 'REVIEW.actual.json')
static = load(STATIC_REVIEW / 'REVIEW.actual.json')
reuse = load(META / 'SOURCE05-NATIVE-REUSE.actual.json')
manifest = load(META / 'manifest.json')
runtime = load(META / 'runtime.local.json')
assert actual['status'] == 'FROZEN_SOURCE_AND_BINDING_PASS_NOT_LIVE'
assert static['status'] == 'STATIC_REVIEW_PASS_ACTUAL_SOURCE05_NOT_ASSESSED'
assert actual['source_commit'] == reuse['source05_commit'] == '27644fdc18e693990e43794af62ebf13db523aef'
for row in [actual['manifest'], actual['runtime'], actual['source05_index'], actual['source05_native_index'],
            actual['source05_archive_pinned_only'], actual['actual_build_result_inherited'], actual['actual_build_inputs_unchanged']]:
    verify(row)
for relative in actual['changed_paths_exact']:
    selected['source05-owned/' + relative] = SOURCE / relative
for label, row in [('BUILD-INPUTS.actual.json', actual['actual_build_inputs_unchanged']),
                   ('BUILD-RESULT.actual.json', actual['actual_build_result_inherited'])]:
    selected['provenance/original-source02/' + label] = Path(row['path'])
for name in ['SOURCE04-NATIVE-REUSE.actual.json', 'manifest.json', 'runtime.local.json']:
    selected['provenance/source04/' + name] = OLD / name

commands = {}
for label, root in [('freeze', roots['root/freeze-command']), ('bind', roots['root/bind-command']), ('frozen-checks', roots['root/python-check-command'])]:
    result = load(root / 'RESULT.actual.json')
    assert result['exit_code'] == 0
    for channel in ['stdout', 'stderr']:
        verify(result[channel])
    commands[label] = 0
frozen_checks = load(META / 'frozen-python-checks-001/RESULT.actual.json')
for result in frozen_checks['commands']:
    assert result['exit_code'] == 0
    verify(result['stdout'])
    verify(result['stderr'])
assert re.search(r'Ran 14 tests', (META / 'frozen-python-checks-001/saved-lifecycle.stderr.log').read_text())
assert re.search(r'Ran 4 tests', (META / 'frozen-python-checks-001/global-routing.stderr.log').read_text())
full = load(INTEGRATION / 'FULL-AFFECTED-TESTS.actual.json')
assert full['actual_tests'] == 93 and full['all_returncodes_zero'] is False
assert [row['returncode'] for row in full['checks']] == [0, 1, 0, 0]
for row in full['checks']:
    verify(row['stdout'])
    verify(row['stderr'])
corrected = load(INTEGRATION / 'delayed14-fresh-fixture-002/RESULT.actual.json')
assert corrected['returncode'] == 0 and corrected['actual_tests'] == 14
for row in [corrected['source'], corrected['stdout'], corrected['stderr']]:
    verify(row)

archive = OUT / 'RAW-EVIDENCE.zip'
entries = []
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as output:
    for label, path in sorted(selected.items()):
        row = {'path': label, **pin(path)}
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        info = zipfile.ZipInfo(label, (1980, 1, 1, 0, 0, 0))
        output.writestr(info, raw, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        entries.append(row)
with zipfile.ZipFile(archive) as check:
    assert check.testzip() is None
    assert len(check.namelist()) == len(set(check.namelist())) == len(entries)
    assert set(check.namelist()) == {row['path'] for row in entries}
    for row in entries:
        raw = check.read(row['path'])
        assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
        assert sha(Path(row['source_path'])) == row['sha256']
for prefix, root in roots.items():
    assert len([path for path in root.rglob('*') if path.is_file()]) == counts[prefix]['files']

facts = {'schema': 'ck3-common-source05-source-only-actual-v1', 'source_commit': reuse['source05_commit'],
    'fixed_single_parent': reuse['source04_commit'], 'author_commit': reuse['author_commit'],
    'author_single_parent': reuse['author_parent'], 'archive_tag': reuse['archive_tag'],
    'independent_static_review': static, 'independent_actual_review': actual,
    'manifest_host_features': manifest['host_features'], 'source05_root': runtime['paths']['source_root'],
    'runtime_metadata_root': str(META), 'root_recorded_exit_codes': commands,
    'frozen_existing_check_exit_codes': {row['name']: row['exit_code'] for row in frozen_checks['commands']},
    'frozen_lifecycle_test_count': 14, 'frozen_global_routing_test_count': 4,
    'original_main_affected_tests': {'tests': 93, 'all_returncodes_zero': False,
        'checks': [{'name': row['name'], 'tests': row['actual_test_count'], 'returncode': row['returncode']} for row in full['checks']]},
    'corrected_delayed_fixture': {'tests': 14, 'returncode': 0, 'production_change_since_first_tests': False},
    'final_applicable_main_test_coverage': 93,
    'original_failures_preserved': ['source-only001 authoring failure', 'main delayed14 old lease-mtime fixture failure'],
    'new_native_build_performed': False, 'no_tests_repeated_for_this_archive': True,
    'actual_live_qualified': False, 'business_pass': False, 'future_r42_result_included': False,
    'separate_permanent_reports': [
        'docs/ck3-native-ai/2026-10-10-shared-delayed-injection-source04.md',
        'docs/ck3-native-ai/2026-10-10-common-cache-reviewer-ci-fixture.md',
        'docs/ck3-native-ai/2026-10-10-r41-shared-runtime-startup-red.md'],
    'game_actions_by_this_producer': 0}
put(OUT / 'FACTS.actual.json', facts)
index = {'schema': 'ck3-source-only-evidence-index-v1', 'archive': {'path': archive.name, **{key: value for key, value in pin(archive).items() if key != 'source_path'}},
    'source_roots': counts, 'entries': entries, 'pinned_only': [
        {'reason': 'Full source ZIP retained externally; not repeated in compact permanent archive', **reuse['source05_archive']},
        {'reason': 'Temporary whole-repository Git index retained externally; actual frozen commit and source indexes are separately checked', **pin(META / 'freeze.index')}],
    'separate_permanent_reports': facts['separate_permanent_reports'], 'producer': pin(Path(__file__).resolve())}
put(OUT / 'INDEX.json', index)
validation = {'schema': 'ck3-source05-evidence-validation-v1', 'checked_utc': datetime.now(timezone.utc).isoformat(),
    'archive_members_exact': True, 'archive_crc_valid': True, 'all_archived_bytes_sha256_rechecked': True,
    'all_original_bytes_sha256_rechecked': True, 'source_root_file_counts_rechecked': True,
    'original_declared_pins_rechecked': declared_count, 'actual_source05_review_archived': True,
    'recorded_command_stdout_stderr_pins_rechecked': True, 'saved_campaign_bodies_archived': False,
    'full_source_zips_repeated': False, 'old_ci_or_runtime_full_zips_repeated': False,
    'entries': len(entries), 'archive_bytes': archive.stat().st_size, 'archive_sha256': sha(archive),
    'index_sha256': sha(OUT / 'INDEX.json'), 'facts_sha256': sha(OUT / 'FACTS.actual.json'),
    'producer_sha256': sha(Path(__file__).resolve()), 'evidence_valid': True,
    'live_qualified': False, 'business_pass': False, 'future_r42_result_included': False}
put(OUT / 'VALIDATION.actual.json', validation)
print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'declared_pins_checked': declared_count,
    'fact_status': actual['status']}, indent=2))

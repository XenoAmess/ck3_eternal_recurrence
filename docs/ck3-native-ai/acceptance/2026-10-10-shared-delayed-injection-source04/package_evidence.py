"""Read-only Source04/shared-Python evidence seal. Never touches live run files."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

REPO = Path('C:/workspace/ck3_eternal_recurrence')
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004')
META = Path('C:/workspace/ck3-common-runtime/20261010-003')
CASE = Path('C:/workspace/ck3-common-runtime/cases/lyd-transaction-control-20261010-003')
SOURCE = Path('C:/csr4')
OLD = Path('C:/workspace/ck3-common-runtime/20261010-002')
HEAD = '6a3affdb87f03f01bdc9f4dc43aeff15960200db'
FROZEN = '919bae0f42def04e6398eb2de4b4afe20dcfc106'
PARENT = '13d063c81ff706d8bc3f9a8bf81f60c283338042'
AUTHOR = '1d4468fc35361be5126acd84402ef27b87d71254'
PATHS = ['ck3_autonomous_player/native_bridge/research/run_ck3_12002_mcp_live.py',
         'ck3_autonomous_player/src/xar_autoplayer/runtime.py',
         'ck3_autonomous_player/tests/unit/test_saved_campaign_delayed_injection.py',
         'tools/ck3_mod_acceptance.py', 'tools/test_ck3_mod_acceptance.py']
ROOT_DIRS = ['r40-delayed-saved-injection-author-handoff-20261010-001',
    'r40-delayed-saved-injection-validation-20261010-001',
    'r40-delayed-saved-injection-validation-20261010-002',
    'r40-delayed-saved-injection-validation-20261010-003',
    'r41-delayed-injection-independent-review-20261010-001',
    'r41-root-rebased-entry-20261010-001', 'r41-root-rebased-delayed-20261010-001',
    'r41-root-rebased-failure-shutdown-20261010-001', 'r41-root-rebased-normal-close-20261010-001',
    'r41-root-rebased-operator-quit-20261010-001', 'r41-root-rebase-20261010-001',
    'r41-root-push-20261010-001', 'r41-root-push-source04-tag-20261010-001']
PRODUCERS = ['r41-root-freeze-source04-20261010-001.py',
    'r41-root-bind-runtime-20261010-001.py', 'r41-root-frozen-python-checks-20261010-001.py',
    'r41-independent-readiness-remainder-probe-20261010-001.py',
    'r41-close-independent-review-20261010-001.py', 'r41-root-prepare-inputs-20261010-001.py']


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


def put(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')


def git(*args) -> bytes:
    result = subprocess.run(['git', *args], cwd=REPO, capture_output=True, check=True)
    return result.stdout


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
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    before = {'head': git('rev-parse', 'HEAD').decode().strip(), 'status': git('status', '--porcelain').decode()}
    assert before == {'head': HEAD, 'status': ''}
    assert git('rev-list', '--parents', '-n', '1', FROZEN).decode().strip().split() == [FROZEN, PARENT]
    changed = git('diff-tree', '--no-commit-id', '--name-only', '-r', FROZEN).decode().splitlines()
    assert sorted(changed) == sorted(PATHS)
    selected = {'producer/package_evidence.py': Path(__file__).resolve()}
    pinned_only = []
    counts = {}
    roots = {'source04-metadata': META}
    roots.update({'author-and-review/' + name: BASE / name for name in ROOT_DIRS})
    for label in ['prepare-command-001', 'preflight-command-001', 'prepared']:
        roots['case-prelive/' + label] = CASE / label
    for prefix, root in roots.items():
        paths = sorted(path for path in root.rglob('*') if path.is_file())
        counts[prefix] = {'source_root': str(root), 'files': len(paths)}
        for path in paths:
            if path.name == 'shared-source04.zip' or path.suffix.lower() == '.ck3':
                pinned_only.append({'reason': 'full source archive or seed body pinned only', **pin(path)})
            else:
                assert path.stat().st_size < 64 * 1024 * 1024, path
                selected[prefix + '/' + path.relative_to(root).as_posix()] = path
    for name in ['prepare-inputs.json', 'INPUT-PROVENANCE.actual.json']:
        selected['case-prelive/' + name] = CASE / name
    for name in PRODUCERS:
        selected['producer/root-and-review/' + name] = BASE / name
    for relative in PATHS:
        selected['source04-files/' + relative] = SOURCE / relative
    ci_root = BASE / 'r41-exact-6a3affdb8-ci-20261010-001'
    for name in ['FINAL.actual.json', 'TERMINAL-EVIDENCE.actual.json']:
        selected['ci-terminal-boundary/' + name] = ci_root / name
    ci = load(ci_root / 'FINAL.actual.json')
    assert ci['head_sha'] == HEAD and ci['triggered_workflows_terminal'] is True
    assert ci['workflow_status']['Official Runner CI']['conclusion'] == 'failure'
    assert ci['workflow_status']['Linear history']['conclusion'] == 'success'
    assert ci['workflow_status']['Li Yu Dao static checks']['status'] == 'NOT_TRIGGERED'
    reuse = load(META / 'SOURCE04-NATIVE-REUSE.actual.json')
    assert reuse['source04_commit'] == FROZEN and reuse['source03_commit'] == PARENT
    assert reuse['author_commit'] == AUTHOR and reuse['native_compiled_inputs_unchanged'] is True
    current = load(META / 'source04-index.json')['files']
    previous = load(OLD / 'source03-index.json')['files']
    delta = sorted(key for key in set(previous) | set(current) if previous.get(key) != current.get(key))
    assert delta == sorted(PATHS)
    assert [key for key in delta if key.startswith('ck3_autonomous_player/native_bridge/')] == [PATHS[0]]
    for path in PATHS:
        assert (SOURCE / path).stat().st_size == current[path]['bytes'] and sha(SOURCE / path) == current[path]['sha256']
        assert git('show', FROZEN + ':' + path) == (SOURCE / path).read_bytes()
    assert git('diff', '--binary', AUTHOR + '^', AUTHOR, '--', *PATHS) == (META / 'shared-delayed-injection-author.patch').read_bytes()
    manifest = load(META / 'manifest.json')
    runtime = load(META / 'runtime.local.json')
    assert manifest['host_features']['saved_campaign_inject_after_load'] is True
    assert manifest['qualification'] == 'PYTHON_FIX_NATIVE_INPUTS_EQUAL_NOT_LIVE_NOT_PRODUCT_PASS'
    for key in ['dll', 'injector']:
        path = Path(runtime['paths'][key])
        row = manifest['native'][key]
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
        pinned_only.append({'reason': 'original Source02 compiled artifact reused, no new build', **pin(path)})
    seed = BASE / 'live-attempt-034/checkpoints/D2a/checkpoint.ck3'
    assert seed.stat().st_size == 91711686 and sha(seed) == 'a6db85e38ba0648eca4b7e835c79d867b96ca26099698f4d4ee5269b818d822c'
    pinned_only.append({'reason': 'fixed R34 D2a seed body pinned only', **pin(seed)})
    review_root = BASE / 'r41-delayed-injection-independent-review-20261010-001'
    review = load(review_root / 'RESULT.actual.json')
    assert review['status'] == 'STATIC_REVIEW_PASS_LIVE_UNPROVEN'
    assert review['positive_readiness_remainder_probe']['status'] == 'PASS'
    review_index = load(review_root / 'REVIEW-INDEX.actual.json')
    for row in review_index['files']:
        path = review_root / row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
    handoff_root = BASE / 'r40-delayed-saved-injection-author-handoff-20261010-001'
    handoff_index = load(handoff_root / 'INDEX.json')
    historical_author_sources = []
    for row in declared_pins(handoff_index):
        path = Path(row['path'])
        if path.is_relative_to(REPO):
            relative = path.relative_to(REPO).as_posix()
            raw = git('show', AUTHOR + ':' + relative)
            assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], relative
            frozen_copy = review_root / 'author-final-source' / relative
            assert frozen_copy.read_bytes() == raw
            historical_author_sources.append({'original_path': str(path), 'resolution': 'exact author Git blob and preserved independent-review author-final-source',
                'author_commit': AUTHOR, 'preserved_copy': str(frozen_copy), 'sha256': row['sha256']})
        else:
            assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], path
    suite_counts = {}
    for name in ROOT_DIRS:
        if '-root-rebased-' in name:
            root = BASE / name
            assert load(root / 'RESULT.actual.json')['exit_code'] == 0
            text = (root / 'stderr.log').read_text(encoding='utf-8')
            match = re.search(r'Ran (\d+) tests', text)
            assert match and text.rstrip().endswith('OK')
            suite_counts[name] = int(match.group(1))
    assert sum(suite_counts.values()) == 48
    frozen_checks = load(META / 'frozen-python-checks-001/RESULT.actual.json')
    assert [row['exit_code'] for row in frozen_checks['commands']] == [0, 1]
    missing = (META / 'frozen-python-checks-001/entry.stderr.log').read_text(encoding='utf-8')
    assert 'workshop' in missing and 'products.json' in missing and 'FileNotFoundError' in missing
    assert 'Ran 15 tests' in missing and 'FAILED (errors=1)' in missing
    for relative in ['frozen-entry-flag-001/RESULT.actual.json', 'host-help-001/RESULT.actual.json']:
        assert load(META / relative)['exit_code'] == 0
    for name in ['prepare-command-001', 'preflight-command-001']:
        assert load(CASE / name / 'RESULT.actual.json')['exit_code'] == 0
    archive = args.output / 'EVIDENCE.zip'
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
    after = {'head': git('rev-parse', 'HEAD').decode().strip(), 'status': git('status', '--porcelain').decode()}
    assert before == after
    facts = {'schema': 'ck3-shared-delayed-load-source04-evidence-v1', 'sealed_utc': datetime.now(timezone.utc).isoformat(),
        'author_commit': AUTHOR, 'master_head': HEAD, 'source04_commit': FROZEN, 'source04_parent': PARENT,
        'source04_changed_paths': delta, 'native_compiled_inputs_unchanged': True,
        'historical_author_source_pins': historical_author_sources,
        'source04_global_manifest_feature_enabled': True, 'implementation_default_off': True,
        'original_total_readiness_budget_seconds': 600, 'two_native_owner_frame_guard_unchanged': True,
        'main_rebased_test_counts': suite_counts, 'main_rebased_test_total': 48,
        'source04_lifecycle_tests': '8 PASS', 'source04_entry_suite': '15 tests, 1 ERROR: missing exported workshop/products.json',
        'source04_global_flag_target': '1 PASS', 'source04_host_help_exit_code': 0,
        'case_prepare_exit_code': 0, 'case_preflight_exit_code': 0,
        'ci_terminal_boundary': ci['workflow_status'], 'ci_full_evidence_external_root': str(ci_root),
        'r41_live_files_followed_or_archived': False, 'r41_live_result_assessed': False,
        'build_invoked': False, 'native_binaries_rebuilt': False, 'business_pass': False,
        'tracked_changes': False, 'repo_before': before, 'repo_after': after}
    put(args.output / 'FACTS.actual.json', facts)
    index = {'schema': 'ck3-static-evidence-index-v1', 'archive': {'path': archive.name, 'bytes': archive.stat().st_size, 'sha256': sha(archive)},
        'source_roots': counts, 'entries': entries, 'pinned_only': pinned_only, 'producer': pin(Path(__file__).resolve())}
    put(args.output / 'INDEX.json', index)
    put(args.output / 'VALIDATION.actual.json', {'schema': 'ck3-source04-evidence-validation-v1',
        'checked_utc': datetime.now(timezone.utc).isoformat(), 'archive_entries': len(entries),
        'archive_crc_valid': True, 'archive_and_original_bytes_sha256_rechecked': True,
        'author_handoff_index_pins_rechecked': True, 'independent_review_index_pins_rechecked': True,
        'source04_git_single_parent_and_author_delta_checked': True, 'five_frozen_source_git_blobs_checked': True,
        'every_other_native_directory_file_equal': True, 'original_native_binary_pins_rechecked': True,
        'repo_head_and_clean_status_unchanged': True, 'r41_live_result_assessed': False,
        'archive_sha256': sha(archive), 'index_sha256': sha(args.output / 'INDEX.json'),
        'facts_sha256': sha(args.output / 'FACTS.actual.json'), 'producer_sha256': sha(Path(__file__).resolve()),
        'validation_pass': True, 'business_pass': False})
    print(json.dumps({'archive': index['archive'], 'entries': len(entries), 'pinned_only': pinned_only, 'test_total': 48}, indent=2))


if __name__ == '__main__':
    main()

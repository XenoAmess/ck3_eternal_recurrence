"""Read-only --check; root invokes --apply for the exact reviewed archive plan."""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

REPO = Path('C:/workspace/ck3_eternal_recurrence').resolve()
BASE = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
DEST = 'docs/li-yu-dao/acceptance/2026-10-07-r0014-19e6601'
RUNTIME_HEAD = '19e660105e05395caa6cc95e76c299312ee89d51'
INDEX_TARGETS = {'docs/li-yu-dao/README.md', 'docs/li-yu-dao/2026-10-06-progress.md', 'docs/autonomous-agent-progress/README.md'}
DAILY = 'docs/autonomous-agent-progress/daily/2026-10-07.md'

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def desc(p, raw=None):
    raw = p.read_bytes() if raw is None else raw
    return {'path': p.as_posix(), 'bytes': len(raw), 'sha256': digest(raw)}

def checked_source(ref):
    p = Path(ref['path']).resolve()
    require(p.is_relative_to(BASE) and not p.is_relative_to(REPO), 'Source must stay in the external task base: ' + str(p))
    require(p.suffix.lower() != '.ck3', 'Full save body is forbidden in this archive publisher')
    raw = p.read_bytes()
    require(len(raw) == ref['bytes'] and digest(raw) == ref['sha256'], 'Source byte/SHA mismatch: ' + str(p))
    return raw

def target_path(rel):
    require(isinstance(rel, str) and '\\' not in rel and ':' not in rel, 'Invalid target path')
    parts = PurePosixPath(rel).parts
    require(parts and not PurePosixPath(rel).is_absolute() and all(x not in ('.', '..') for x in parts), 'Target path escape: ' + rel)
    p = REPO.joinpath(*parts)
    require(p.resolve().is_relative_to(REPO), 'Resolved target path escape: ' + rel)
    return p

def git(*args, input_bytes=None):
    proc = subprocess.run(['git', '-C', str(REPO), *args], input=input_bytes, capture_output=True, check=True)
    return proc.stdout

def text_attributes(targets):
    raw = git('check-attr', '-z', '--stdin', 'text', input_bytes=b'\0'.join(t.encode('utf-8') for t in targets) + b'\0')
    fields = raw.decode('utf-8').split('\0')
    require(fields[-1] == '' and (len(fields) - 1) % 3 == 0, 'Malformed actual git check-attr response')
    result = {fields[i]: fields[i + 2] for i in range(0, len(fields) - 1, 3)}
    require(set(result) == set(targets), 'Missing actual git attributes for archive byte copies')
    require(all(result[t] == 'unset' for t in targets), 'Acceptance raw must be covered by actual -text gitattributes')
    return result

def validate_plan(manifest_path, expected_sha, repo_arg):
    require(Path(repo_arg).resolve() == REPO, 'Repository must be the exact primary root')
    require(re.fullmatch('[0-9a-fA-F]{64}', expected_sha) is not None, 'Manifest SHA must be exact 64 hex')
    p = Path(manifest_path).resolve()
    require(p.is_relative_to(BASE), 'Manifest is outside external task base')
    raw = p.read_bytes()
    require(digest(raw) == expected_sha.lower(), 'Manifest actual SHA mismatch')
    plan = json.loads(raw.decode('utf-8-sig'))
    require(plan['schema'] == 'lyd.r14.reviewed-archive-publisher-plan.v1', 'Unsupported plan schema')
    require(Path(plan['repository']).resolve() == REPO and plan['archive_root'] == DEST, 'Plan root mismatch')
    require(plan['actual_R14_runtime_HEAD'] == RUNTIME_HEAD and plan['business_GREEN'] is False, 'Frozen R14 runtime/RED contract changed')
    require(not target_path(DEST).exists(), 'Acceptance archive root already exists; stop without retry')
    require(plan['original_raw_CAS_file_count'] == 230, 'Original finalclosed raw set must contain exactly 230 files')
    original_proposal = json.loads(checked_source(plan['original_proposal']).decode('utf-8-sig'))
    original_index = json.loads(checked_source(plan['original_final_closed_index']).decode('utf-8-sig'))
    require(original_index['actual_source_HEAD'] == RUNTIME_HEAD and original_index['business_GREEN'] is False and original_index['full_run_closed'] is True, 'Original final closed RED index mismatch')
    original_append = {op['target']: op for op in original_proposal['operations'] if op['target'] in INDEX_TARGETS}
    require(set(original_append) == INDEX_TARGETS, 'Original proposal must bind all three indexes')
    original_raw = {op['target']: op['source'] for op in original_proposal['operations'] if op['target'].startswith(DEST + '/raw/')}
    require(len(original_raw) == 230, 'Original proposal raw count mismatch')
    writes = []
    seen = set()
    actual_index_targets = set()
    raw_targets = []
    for op in plan['operations']:
        rel = op['target']
        require(rel not in seen, 'Duplicate target, including Windows case aliases: ' + rel)
        require(rel.casefold() not in {x.casefold() for x in seen}, 'Case-alias duplicate target: ' + rel)
        seen.add(rel)
        dest = target_path(rel)
        archive = rel.startswith(DEST + '/')
        require(archive or rel in INDEX_TARGETS or rel == DAILY, 'Target is outside the explicit archive/index allowlist: ' + rel)
        payload = checked_source(op['source'])
        require(digest(payload) == op['after_payload_sha256'] and len(payload) == op['after_payload_bytes'], 'Payload descriptor mismatch: ' + rel)
        if archive:
            require(op['operation'] == 'ADD' and op['before'] is None and not dest.exists(), 'Archive target must be absent/create-only: ' + rel)
            require(op.get('raw_exact') or rel.endswith(('.md', '.json')), 'Unexpected archive artifact')
            if op.get('raw_exact'):
                raw_targets.append(rel)
        elif rel in INDEX_TARGETS:
            require(op['operation'] == 'APPEND' and op['before'] == original_append[rel]['before'], 'Index beforeHash differs from original reviewed proposal: ' + rel)
            require(dest.is_file(), 'Required existing index is absent: ' + rel)
            prefix = dest.read_bytes()
            require(desc(dest, prefix) == op['before'], 'Actual index beforeHash mismatch: ' + rel)
            actual_index_targets.add(rel)
        else:
            require(op['operation'] == 'ADD' and op['before'] is None and not dest.exists(), 'New daily target must be absent: ' + rel)
        if op.get('new_markdown_LF'):
            require(b'\r' not in payload, 'New Markdown must have canonical LF: ' + rel)
        if rel in original_raw:
            require(op.get('raw_exact') and op['source']['sha256'] == original_raw[rel]['sha256'] and op['source']['bytes'] == original_raw[rel]['bytes'], 'Original raw CAS bytes changed: ' + rel)
        writes.append((op, dest, payload))
    require(actual_index_targets == INDEX_TARGETS and DAILY in seen, 'Missing index or daily operation')
    require(set(original_raw).issubset(seen), 'Original raw artifact omitted')
    require(DEST + '/INDEX.json' in seen and DEST + '/AFTERCLOSE-INTEGRATION.md' in seen and DEST + '/source_inputs/INDEX.json' in seen, 'Missing derived index or afterclose inputs')
    archived_index = json.loads(next(payload for op, _, payload in writes if op['target'] == DEST + '/INDEX.json'))
    require(archived_index['original_final_closed_index'] == plan['original_final_closed_index'], 'Derived index lost original index SHA')
    mapped = {item['archive_relative_path']: item for item in archived_index['files']}
    expected_mapping = {op['target'][len(DEST) + 1:]: op for op, _, _ in writes if op['target'].startswith(DEST + '/') and op['target'] != DEST + '/INDEX.json'}
    require(set(mapped) == set(expected_mapping), 'Derived archive_relative_path index does not cover exact archive writes')
    for rel, op in expected_mapping.items():
        item = mapped[rel]
        require(item['archive_bytes'] == op['after_payload_bytes'] and item['archive_sha256'] == op['after_payload_sha256'], 'Derived index artifact SHA mismatch: ' + rel)
    attrs = text_attributes(raw_targets)
    return plan, writes, {'original_raw_CAS_files_SHA_bytes_verified': len(original_raw), 'exact_index_beforeHashes_verified': sorted(actual_index_targets), 'archive_payloads': len(expected_mapping) + 1, 'raw_byte_copy_targets_with_actual_git_text_unset': len(attrs), 'derived_archive_relative_paths_verified': len(mapped), 'operation_count': len(writes), 'manifest': desc(p, raw), 'repository_HEAD': git('rev-parse', 'HEAD').decode().strip(), 'git_status_porcelain_branch': git('status', '--porcelain', '--branch').decode().strip()}

def apply_plan(writes, completed):
    for op, target, payload in writes:
        # Resolve again immediately before each write. No move/delete/rollback.
        require(target_path(op['target']) == target and target.resolve().is_relative_to(REPO), 'Target resolution changed before mutation')
        if op['operation'] == 'APPEND':
            with target.open('r+b') as f:
                prefix = f.read()
                require(desc(target, prefix) == op['before'], 'Actual index changed before append: ' + op['target'])
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            expected = prefix + payload
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            expected = payload
        actual = target.read_bytes()
        completed.append({'operation': op['operation'], 'target': op['target'], 'after': desc(target, actual), 'readback_matches_expected': actual == expected, 'original_prefix_preserved': op['operation'] == 'APPEND'})
        require(actual == expected, 'Actual write readback mismatch: ' + op['target'])
    return completed

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--apply', action='store_true')
    parser.add_argument('--repo', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--expected-manifest-sha256', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    report_path = Path(args.report).resolve()
    require(report_path.is_relative_to(BASE) and not report_path.is_relative_to(REPO) and not report_path.exists(), 'Report must be fresh and outside primary repository')
    result = {'schema': 'lyd.r14.archive-publisher.actual-execution.v1', 'mode': 'APPLY_ROOT_ONLY' if args.apply else 'READONLY_CHECK', 'started_at_utc': datetime.now(timezone.utc).isoformat(), 'publisher': desc(Path(__file__).resolve()), 'main_writes': 0, 'actual_R14_runtime_HEAD': RUNTIME_HEAD, 'business_GREEN': False, 'game_calls': 0, 'SDK_calls': 0, 'lease_changes': 0, 'new_tests': 0, 'new_builds': 0}
    exit_code = 0
    try:
        plan, writes, validation = validate_plan(args.manifest, args.expected_manifest_sha256, args.repo)
        result['validation'] = validation
        result['afterclose_source_commit_HEAD_credit'] = None
        result['new_cold_runtime_credit'] = None
        if args.apply:
            result['mutation_started'] = True
            result['completed_writes'] = []
            apply_plan(writes, result['completed_writes'])
            result['main_writes'] = len(result['completed_writes'])
            result['status'] = 'ACTUAL_ROOT_ARCHIVE_APPLY_COMPLETE_EXACT_READBACK'
        else:
            result['mutation_started'] = False
            result['status'] = 'ACTUAL_READONLY_ARCHIVE_CHECK_PASS_NO_MAIN_WRITES'
            result['planned_targets'] = [{'operation': op['operation'], 'target': op['target'], 'payload_bytes': len(payload), 'payload_sha256': digest(payload), 'before': op['before']} for op, _, payload in writes]
    except Exception as exc:
        exit_code = 1
        result['main_writes'] = len(result.get('completed_writes', []))
        result['status'] = 'FAILED_PARTIAL_APPLY_STOP_NO_RETRY' if result.get('mutation_started') else 'FAILED_BEFORE_ANY_MAIN_MUTATION'
        result['error'] = type(exc).__name__ + ': ' + str(exc)
        result['automatic_retry_authorized'] = False
    result['exit_code'] = exit_code
    result['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with report_path.open('xb') as f:
        f.write((json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    print(json.dumps({'status': result['status'], 'exit_code': exit_code, 'report': desc(report_path), 'main_writes': result['main_writes']}, ensure_ascii=False, indent=2))
    return exit_code

if __name__ == '__main__':
    sys.exit(main())

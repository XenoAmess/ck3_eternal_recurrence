"""Root-owned candidate. This preparation agent does not execute the importer.

Every input and closure reference must be hash-bound. The closure report is a
root review of actual evidence, not a generated approval or a test conclusion.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

sys.dont_write_bytecode = True
EXTERNAL = Path('C:/workspace/ck3_lyd_runtime_20261004').resolve()
REPO = Path('C:/workspace/ck3_eternal_recurrence').resolve()
SOURCE = '3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
TARGET_RELATIVE = 'docs/li-yu-dao/acceptance/2026-10-05-R0006-representative-c2-pending'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def inside(path, root):
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError('Path outside designated root: ' + str(path))
    return resolved

def relpath(value):
    text = str(value).replace('\\', '/')
    posix = PurePosixPath(text)
    if posix.is_absolute() or not text or any(x in {'', '.', '..'} for x in posix.parts) or ':' in text:
        raise ValueError('Unsafe relative path: ' + text)
    return Path(*posix.parts)

def bound_file(row):
    path = inside(Path(row['path']), EXTERNAL)
    if not path.is_file() or path.is_symlink():
        raise ValueError('Missing or symbolic evidence: ' + str(path))
    if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
        raise ValueError('Evidence hash mismatch: ' + str(path))
    return path

def package_files(row):
    source = inside(Path(row['source']), EXTERNAL)
    index_path = inside(source/relpath(row['index_name']), source)
    if sha(index_path) != row['index_sha256']:
        raise ValueError('Package index changed: ' + str(source))
    index = read(index_path)
    files = []
    expected = set()
    for entry in index['files']:
        relative = relpath(entry['path'])
        path = inside(source/relative, source)
        if path.is_symlink() or not path.is_file():
            raise ValueError('Not an ordinary package file: ' + str(path))
        if path.suffix.lower() == '.ck3' or entry['bytes'] > 50_000_000:
            raise ValueError('Raw save or bulk asset cannot enter tracked evidence: ' + str(path))
        if path.stat().st_size != entry['bytes'] or sha(path) != entry['sha256']:
            raise ValueError('Package content changed: ' + str(path))
        key = relative.as_posix()
        if key.casefold() in {x.casefold() for x in expected}:
            raise ValueError('Duplicate indexed path: ' + key)
        expected.add(key)
        files.append((relative, path, entry['sha256'], entry['bytes']))
    actual = {p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file()}
    index_rel = index_path.relative_to(source).as_posix()
    if {x.casefold() for x in actual} != {x.casefold() for x in expected | {index_rel}}:
        raise ValueError('Unindexed or missing files: ' + str(source))
    files.append((index_path.relative_to(source), index_path, sha(index_path), index_path.stat().st_size))
    return files

def closure_gate(report, evidence):
    if report.get('schema') != 'lyd.r6.closure-review.v1' or report.get('attempt') != 'live-attempt-006' or report.get('source_revision') != SOURCE:
        raise ValueError('Wrong closure review identity')
    required = {
        'normal_exit': 'OBSERVED_NORMAL_EXIT',
        'process_absence': 'OBSERVED_PROCESS_ABSENCE',
        'sdk_close': 'OBSERVED_SESSION_CLOSED',
        'screen_lease_release': 'OBSERVED_RELEASED',
        'source_freeze_release': 'OBSERVED_RELEASED',
    }
    for key, expected in required.items():
        item = report.get('lifecycle', {}).get(key, {})
        if item.get('status') != expected or not item.get('evidence'):
            raise ValueError('Closure still pending or unbound: ' + key)
        for row in item['evidence']:
            p = bound_file(row)
            if str(p).casefold() not in evidence:
                raise ValueError('Closure evidence absent from indexed closure package: ' + str(p))
    if report.get('overall_native_acceptance') != 'NOT_GREEN':
        raise ValueError('Historical qualification RED/capped log cannot be relabeled GREEN')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--plan-sha256', required=True)
    parser.add_argument('--closure-package', type=Path, required=True)
    parser.add_argument('--closure-index-sha256', required=True)
    parser.add_argument('--closure-report', type=Path, required=True)
    parser.add_argument('--closure-report-sha256', required=True)
    parser.add_argument('--audit-output', type=Path, required=True)
    parser.add_argument('--execute', action='store_true', help='Root executes only after real closure evidence was reviewed')
    args = parser.parse_args()
    plan_path = inside(args.plan, EXTERNAL)
    report_path = inside(args.closure_report, EXTERNAL)
    if sha(plan_path) != args.plan_sha256 or sha(report_path) != args.closure_report_sha256:
        raise ValueError('Frozen plan/closure report hash mismatch')
    plan = read(plan_path)
    if plan.get('source_revision') != SOURCE or plan.get('target_relative') != TARGET_RELATIVE:
        raise ValueError('Import plan source or target changed')
    closure_row = {'source': str(inside(args.closure_package, EXTERNAL)), 'index_name': 'INDEX.json', 'index_sha256': args.closure_index_sha256, 'target_prefix': 'lifecycle-closure'}
    packages = list(plan['packages']) + [closure_row]
    copies = []
    closure_files = package_files(closure_row)
    closure_evidence = {str(path.resolve()).casefold() for _, path, _, _ in closure_files}
    if str(report_path).casefold() not in closure_evidence:
        raise ValueError('Closure report must be in closure index')
    closure_gate(read(report_path), closure_evidence)
    for row in packages:
        prefix = relpath(row['target_prefix'])
        for relative, source, digest, size in package_files(row):
            copies.append({'source': source, 'relative': prefix/relative, 'sha256': digest, 'bytes': size})
    keys = [row['relative'].as_posix() for row in copies]
    if len(keys) != len({key.casefold() for key in keys}):
        raise ValueError('Target file collision')
    target = inside(REPO/relpath(TARGET_RELATIVE), REPO)
    if target.exists():
        raise FileExistsError('Refuse overwrite existing tracked report: ' + str(target))
    audit = inside(args.audit_output, EXTERNAL)
    if args.execute and audit.exists():
        raise FileExistsError('Refuse overwrite existing external import audit')
    receipt = {'schema': 'lyd.r6.report-import.v1', 'utc': datetime.now(timezone.utc).isoformat(), 'source_revision': SOURCE, 'target': str(target), 'files': len(copies), 'bytes': sum(x['bytes'] for x in copies), 'plan_sha256': args.plan_sha256, 'closure_report_sha256': args.closure_report_sha256, 'overall_native_acceptance': 'NOT_GREEN', 'game_native_git_ci_calls': 0, 'execute_requested': args.execute}
    if args.execute:
        target.mkdir(parents=True, exist_ok=False)
        for row in copies:
            output = inside(target/row['relative'], target)
            output.parent.mkdir(parents=True, exist_ok=True)
            with row['source'].open('rb') as src, output.open('xb') as dst:
                shutil.copyfileobj(src, dst)
            if output.stat().st_size != row['bytes'] or sha(output) != row['sha256']:
                raise ValueError('Imported byte verification failed: ' + str(output))
        audit.mkdir(parents=True, exist_ok=False)
        with (audit/'receipt.json').open('x', encoding='utf-8') as stream:
            json.dump(receipt, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    print(json.dumps(receipt, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    main()

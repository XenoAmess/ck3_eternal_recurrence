"""Read exact GitHub jobs and immutable rebase input objects; external receipts only."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path('C:/workspace/ck3_lyd_runtime_20261004')
REPO = Path('C:/workspace/ck3_eternal_recurrence')
BEFORE = 'da6f77c43e5a8bbdb393bebc50970c46c4a6260d'
AFTER = '588492d3dbf473226664220b722a04b66ae54bae'
RUNS = {'lyd': 37178012389, 'official': 37178012410}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if ROOT.resolve() not in output.parents:
        raise SystemExit('Output must remain in the external runtime tree')
    output.mkdir(parents=True, exist_ok=False)

    def query(item):
        name, run_id = item
        argv = ['gh', 'run', 'view', str(run_id), '--repo', 'XenoAmess/ck3_eternal_recurrence',
                '--json', 'databaseId,headSha,status,conclusion,url,workflowName,jobs']
        completed = subprocess.run(argv, capture_output=True, timeout=30, check=False)
        record = {'name': name, 'argv': argv, 'returncode': completed.returncode}
        for kind, data in [('stdout', completed.stdout), ('stderr', completed.stderr)]:
            path = output / f'{name}.{kind}.txt'
            path.write_bytes(data)
            record[kind] = {'path': path.name, 'bytes': len(data), 'sha256': sha(data)}
        if completed.returncode == 0:
            record['json'] = json.loads(completed.stdout.decode('utf-8-sig'))
        return record

    with ThreadPoolExecutor(max_workers=2) as executor:
        run_records = list(executor.map(query, RUNS.items()))
    for record in run_records:
        if record['returncode'] == 0:
            assert record['json']['headSha'] == AFTER, record['name']
            assert record['json']['databaseId'] == RUNS[record['name']], record['name']

    source_records = []
    sources = ['.github/workflows/li-yu-dao-static.yml', 'tools/extract_auto_upgrade_buildings.py',
               'mod_li_yu_dao/tools/build_release.py', 'mod_li_yu_dao/tools/run_acceptance.py']
    source_root = output / 'source'
    source_root.mkdir()
    for local in [Path(__file__), ROOT / 'query_lyd_ci_readonly.py', ROOT / 'persistent_native_mcp_queue.py']:
        data = local.read_bytes()
        destination = source_root / local.name
        destination.write_bytes(data)
        source_records.append({'path': destination.relative_to(output).as_posix(), 'original_path': local.as_posix(),
                               'bytes': len(data), 'sha256': sha(data), 'source_kind': 'exact_existing_helper'})

    comparisons = []
    for path in ['mod_li_yu_dao', '.github/workflows/li-yu-dao-static.yml', 'tools/extract_auto_upgrade_buildings.py']:
        argv = ['git', '-C', str(REPO), 'rev-parse', f'{BEFORE}:{path}', f'{AFTER}:{path}']
        completed = subprocess.run(argv, capture_output=True, timeout=15, check=False)
        objects = completed.stdout.decode('utf-8').splitlines()
        comparisons.append({'path': path, 'argv': argv, 'returncode': completed.returncode,
                            'objects': objects, 'equal': completed.returncode == 0 and len(objects) == 2 and objects[0] == objects[1]})
    for path in sources:
        argv = ['git', '-C', str(REPO), 'show', f'{AFTER}:{path}']
        completed = subprocess.run(argv, capture_output=True, timeout=15, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f'Immutable Git input read failed: {path}')
        destination = source_root / 'commit-588492d' / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(completed.stdout)
        source_records.append({'path': destination.relative_to(output).as_posix(), 'git_ref': AFTER,
                               'git_path': path, 'bytes': len(completed.stdout), 'sha256': sha(completed.stdout),
                               'source_kind': 'immutable_git_blob', 'argv': argv})

    diff_argv = ['git', '-C', str(REPO), 'diff', '--name-status', BEFORE, AFTER]
    diff = subprocess.run(diff_argv, capture_output=True, timeout=15, check=False)
    (output / 'rebase-name-status.raw.txt').write_bytes(diff.stdout)
    changed = [line.split('\t')[-1] for line in diff.stdout.decode('utf-8').splitlines()]
    lyk_changed = [path for path in changed if path.startswith('mod_li_yu_dao/') or path in sources[:2]]

    report = {'schema': 'ck3.lyd.exact-master-ci-jobs-readonly.v1',
              'queried_at_utc': datetime.now(timezone.utc).isoformat(), 'commit': AFTER,
              'run_records': run_records, 'source_records': source_records,
              'rebase_comparison': {'before': BEFORE, 'after': AFTER, 'objects': comparisons,
                                    'raw_diff': {'path': 'rebase-name-status.raw.txt', 'sha256': sha(diff.stdout),
                                                 'argv': diff_argv, 'returncode': diff.returncode},
                                    'lyd_static_inputs_changed': lyk_changed,
                                    'all_relevant_objects_equal': all(c['equal'] for c in comparisons),
                                    'local_lyd_l0_repeat_required_by_rebase': bool(lyk_changed) or not all(c['equal'] for c in comparisons),
                                    'boundary': 'LYD-only equivalence; unrelated upstream product/native changes exist. Manifest commit metadata changes, so no assertion that all build artifacts are byte-identical.'},
              'git_mutated': False, 'tracked_written': False, 'game_called': False}
    (output / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'commit': AFTER,
                      'runs': [{k: r.get('json', {}).get(k) for k in ['databaseId', 'workflowName', 'status', 'conclusion', 'url']} for r in run_records],
                      'lyd_static_input_objects_equal': report['rebase_comparison']['all_relevant_objects_equal'],
                      'local_lyd_l0_repeat_required_by_rebase': report['rebase_comparison']['local_lyd_l0_repeat_required_by_rebase'],
                      'report': (output / 'report.json').as_posix(), 'report_sha256': sha((output / 'report.json').read_bytes())}, ensure_ascii=False))


if __name__ == '__main__':
    main()

from __future__ import annotations

import gzip
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TRANSFER = ROOT.with_name(ROOT.name + '-transfer')
SHA = 'a2f09421a1cfcd8a0cbe480933864edfd575d352'


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def write(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(body)


def dump(path: Path, value: object) -> None:
    write(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def compressed(path: Path, body: bytes) -> dict:
    packed = gzip.compress(body, compresslevel=9, mtime=0)
    assert gzip.decompress(packed) == body
    write(path, packed)
    return {'path': path.relative_to(ROOT).as_posix(), 'gzip_bytes': len(packed),
            'gzip_sha256': digest(packed), 'source_bytes': len(body), 'source_sha256': digest(body),
            'decompressed_exact_match': True}


def tree_difference(before: dict, after: dict) -> list[str]:
    old = {item['path']: item['sha'] for item in before['tree']}
    new = {item['path']: item['sha'] for item in after['tree']}
    return sorted(path for path in set(old) | set(new) if old.get(path) != new.get(path))


def main() -> None:
    observations = {}
    for path in sorted(TRANSFER.glob('incoming-observations-*.json')):
        incoming = json.loads(path.read_text(encoding='utf-8'))
        assert incoming['commit'] == SHA
        for item in incoming['observations']:
            assert item['key'] not in observations or observations[item['key']] == item
            observations[item['key']] = item

    def data(key: str) -> object:
        return json.loads(observations[key]['result']['structuredContent']['content'])

    run_key = sorted(key for key in observations if key.startswith('a2-runs-'))[-1]
    runs = data(run_key)
    assert runs['total_count'] == len(runs['workflow_runs']) == 1
    run = runs['workflow_runs'][0]
    assert run['head_sha'] == SHA and run['event'] == 'push' and run['status'] == 'completed'
    assert run['path'] == '.github/workflows/static-ci.yml'
    jobs_key = sorted(key for key in observations if key.startswith(f"a2-jobs-{run['id']}-"))[-1]
    jobs = data(jobs_key)
    assert jobs['total_count'] == len(jobs['jobs']) == 1
    job = jobs['jobs'][0]
    assert job['status'] == 'completed' and job['conclusion'] == run['conclusion']
    assert all(step['status'] == 'completed' for step in job['steps'])
    log_key = f"a2-logs-{job['id']}"
    log = observations[log_key]['result']['structuredContent']['content']
    assert SHA in log
    counts = dict(Counter(step['conclusion'] for step in job['steps']))
    if run['conclusion'] == 'success':
        assert counts == {'success': 60, 'skipped': 20}
        assert 'PYTHON-ONLY GREEN' in log

    head, parent, baseline = data('a2-head-tree'), data('a2-parent-tree'), data('a2-baseline-c40-tree')
    root_diff = tree_difference(parent, head)
    assert root_diff == ['docs']
    product_shas = [next(x['sha'] for x in tree['tree'] if x['path'] == 'mod_li_yu_dao')
                    for tree in (head, parent, baseline)]
    assert len(set(product_shas)) == 1
    doc_h, doc_p = data('a2-head-docs-tree'), data('a2-parent-docs-tree')
    docs_diff = tree_difference(doc_p, doc_h)
    assert docs_diff == ['li-yu-dao']
    lyd_h, lyd_p = data('a2-head-docs-li-yu-dao-tree'), data('a2-parent-docs-li-yu-dao-tree')
    lyd_diff = tree_difference(lyd_p, lyd_h)
    assert lyd_diff == ['acceptance']
    acc_h, acc_p = data('a2-head-acceptance-tree'), data('a2-parent-acceptance-tree')
    acc_diff = tree_difference(acc_p, acc_h)
    watched = '2026-10-04-R0002-native-cycles-formal-red'
    r2_h = next(x['sha'] for x in acc_h['tree'] if x['path'] == watched)
    r2_p = next(x['sha'] for x in acc_p['tree'] if x['path'] == watched)
    assert r2_h == r2_p
    for tree in (head, parent, baseline, doc_h, doc_p, lyd_h, lyd_p, acc_h, acc_p):
        assert not tree['truncated']
    definitions = []
    for item in data('a2-workflow-directory'):
        body = observations['a2-definition-' + item['name']]['result']['structuredContent']['content'].encode('utf-8')
        assert len(body) == item['size']
        blob_sha = hashlib.sha1(b'blob ' + str(len(body)).encode('ascii') + b'\0' + body).hexdigest()
        assert blob_sha == item['sha']
        definitions.append({'path': item['path'], 'bytes': len(body), 'sha256': digest(body),
                            'git_blob_sha1': blob_sha, 'verified': True})
    definition = observations['a2-definition-li-yu-dao-static.yml']['result']['structuredContent']['content']
    watched_paths = ['mod_li_yu_dao/**', 'tools/extract_auto_upgrade_buildings.py',
                     'docs/li-yu-dao/acceptance/2026-10-04-R0002-native-cycles-formal-red/**',
                     '.github/workflows/li-yu-dao-static.yml']
    assert all(f"- '{path}'" in definition for path in watched_paths)
    artifacts_key = sorted(key for key in observations if key.startswith(f"a2-artifacts-{run['id']}-"))[-1]
    artifacts = data(artifacts_key)
    assert artifacts['total_count'] == len(artifacts['artifacts'])
    preservation = []
    for key, item in observations.items():
        encoded = (json.dumps(item, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
        response_map = compressed(ROOT / f'responses/{key}.json.gz', encoded)
        entry = {'key': key, 'observed_at': item['observed_at'], 'request': item['request'],
                 'complete_tool_response': response_map, 'is_error': item['result'].get('isError', False)}
        body = item['result'].get('structuredContent', {}).get('content')
        if isinstance(body, str):
            suffix = '.yml' if '-definition-' in key else '.log' if '-logs-' in key else '.json'
            entry['exposed_body'] = compressed(ROOT / f'bodies/{key}{suffix}.gz', body.encode('utf-8'))
        preservation.append(entry)
    dump(ROOT / 'PRESERVATION.json', preservation)
    failed_steps = [step for step in job['steps'] if step['conclusion'] == 'failure']
    if failed_steps:
        compressed(ROOT / 'derived/failure-detail.json.gz', (json.dumps(failed_steps, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    report = {'schema': 'lyd-ci-evidence/v1', 'repository': 'XenoAmess/ck3_eternal_recurrence', 'commit': SHA,
              'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'read_only': True,
              'dispatch_rerun_or_publication': False, 'used_pr_filtered_wrapper': False,
              'actual_general_ci': {'run_id': run['id'], 'run_url': run['html_url'], 'job_id': job['id'],
                                    'event': run['event'], 'run_attempt': run['run_attempt'], 'head_sha': run['head_sha'],
                                    'status': run['status'], 'conclusion': run['conclusion'],
                                    'created_at': run['created_at'], 'updated_at': run['updated_at'],
                                    'step_conclusions': counts, 'steps': job['steps'],
                                    'log_observation_key': log_key, 'log_body_sha256': digest(log.encode('utf-8')),
                                    'artifact_metadata': artifacts},
              'lyd_specific_ci': {'status': 'NOT_TRIGGERED_DOCS_ONLY', 'observed_runs': 0,
                                 'conclusion': 'NOT_RUN', 'configured_push_paths': watched_paths,
                                 'root_changed_paths': root_diff, 'docs_changed_paths': docs_diff,
                                 'lyd_docs_changed_paths': lyd_diff, 'acceptance_changed_paths': acc_diff,
                                 'watched_r2_tree_sha_before': r2_p, 'watched_r2_tree_sha_after': r2_h,
                                 'product_tree_sha_a2': product_shas[0], 'product_tree_sha_parent': product_shas[1],
                                 'product_tree_sha_c40': product_shas[2],
                                 'inference': 'Exact new commit changes only LYD acceptance archives; no configured workflow path changed.'},
              'workflow_definitions': definitions, 'raw_projection': 'LOSSLESS_GZIP_ONLY',
              'overall': 'GENERAL_CI_PASS_LYD_NOT_TRIGGERED' if run['conclusion'] == 'success' else 'GENERAL_CI_RED_LYD_NOT_TRIGGERED',
              'limits': ['Exact target remains a2f09421a; later master heads are not substituted.',
                         'Complete combined job logs are preserved. GitHub does not expose separate output streams.',
                         'Bodies are exact UTF-8 bytes exposed by the connector, not unavailable HTTP wire bytes or headers.',
                         'Raw responses, definitions and logs are projected with lossless gzip; compressed and decompressed bytes each have SHA-256.',
                         'No new product-specific CI ran. Product tree equality to c40 is a source binding, not a new test execution.',
                         'General CI and source equality do not prove CK3 runtime, union/split, leaders, save/reload or release acceptance.',
                         'No repository mutation, rerun, dispatch, game, native bridge or main-tree write was performed.']}
    dump(ROOT / 'REPORT.json', report)
    text = f'''目标提交：{SHA}。实际通用 CI run {run['id']}、job {job['id']}，completed/{run['conclusion']}；步骤结论：{counts}。

实际专题儒家 CI 没有 run，为 NOT_TRIGGERED_DOCS_ONLY。9 个未截断 Git trees 证明本次变更仅在儒家验收归档；4 条 workflow push 路径无变化，受监控 R0002 子树未变。产品树 a2、其 parent、c40 均为 {product_shas[0]}。树相同仅证明源字节一致，不等于重新执行专题测试。

完整真实响应、5 份精确 workflow、job 步骤与合并日志均以 lossless gzip 保全。PRESERVATION.json 绑定每份压缩字节和解压字节的大小、SHA-256，并已逐一核验完全相等。外置 transfer 原始输入保留，不改旧 c40 或 bfe 证据。

本包不证明实机、合流/分裂、领袖、重载或发布通过。无 dispatch/rerun、Git、主树、游戏或 native 写操作。

实际 run：{run['html_url']}
'''
    write(ROOT / 'REPORT.md', text.encode('utf-8'))
    index = {'schema': 'lyd-external-evidence-index/v1', 'index_excludes_self': True,
             'created_at_utc': datetime.now(timezone.utc).isoformat(), 'files': []}
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and path.name != 'INDEX.json':
            body = path.read_bytes()
            index['files'].append({'path': path.relative_to(ROOT).as_posix(), 'bytes': len(body), 'sha256': digest(body)})
    dump(ROOT / 'INDEX.json', index)
    print(json.dumps({'files': len(index['files']), 'index_sha256': digest((ROOT / 'INDEX.json').read_bytes()),
                      'report_sha256': digest((ROOT / 'REPORT.json').read_bytes()), 'overall': report['overall']}))


if __name__ == '__main__':
    main()

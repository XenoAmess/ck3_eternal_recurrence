from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def raw(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)


def main() -> None:
    incoming = json.loads((ROOT / 'incoming-tool-responses.json').read_text(encoding='utf-8'))
    observations = {item['key']: item for item in incoming['observations']}
    response_index = []
    for key, item in observations.items():
        response_rel = f'responses/{key}.json'
        dump(ROOT / response_rel, item)
        body = item['result'].get('structuredContent', {}).get('content')
        entry = {'key': key, 'observed_at': item['observed_at'], 'request': item['request'],
                 'response_path': response_rel, 'is_error': item['result'].get('isError', False)}
        if isinstance(body, str):
            extension = '.yml' if key.startswith('definition-') else '.log' if key.startswith('logs-') else '.json'
            body_rel = f'bodies/{key}{extension}'
            encoded = body.encode('utf-8')
            raw(ROOT / body_rel, encoded)
            entry.update(body_path=body_rel, body_bytes=len(encoded), body_sha256=sha(encoded))
        response_index.append(entry)
    dump(ROOT / 'observations.json', response_index)

    def data(key: str) -> object:
        return json.loads(observations[key]['result']['structuredContent']['content'])

    head = data('head-tree')
    parent = data('parent-tree')
    root_diff = [item['path'] for item in head['tree']
                 if next((x['sha'] for x in parent['tree'] if x['path'] == item['path']), None) != item['sha']]
    assert root_diff == ['docs'] and not head['truncated'] and not parent['truncated']
    docs_h, docs_p = data('head-docs-tree'), data('parent-docs-tree')
    docs_diff = [item['path'] for item in docs_h['tree']
                 if next((x['sha'] for x in docs_p['tree'] if x['path'] == item['path']), None) != item['sha']]
    assert docs_diff == ['li-yu-dao'] and not docs_h['truncated'] and not docs_p['truncated']
    lyd_h, lyd_p = data('head-docs-li-yu-dao-tree'), data('parent-docs-li-yu-dao-tree')
    lyd_diff = [item['path'] for item in lyd_h['tree']
               if next((x['sha'] for x in lyd_p['tree'] if x['path'] == item['path']), None) != item['sha']]
    assert set(lyd_diff) == {'README.md', 'acceptance'}
    acceptance_h, acceptance_p = data('head-acceptance-tree'), data('parent-acceptance-tree')
    acceptance_diff = [item['path'] for item in acceptance_h['tree']
                      if next((x['sha'] for x in acceptance_p['tree'] if x['path'] == item['path']), None) != item['sha']]
    assert acceptance_diff == ['2026-10-05-R0006-closed-not-green']
    r2 = '2026-10-04-R0002-native-cycles-formal-red'
    r2_h = next(x['sha'] for x in acceptance_h['tree'] if x['path'] == r2)
    r2_p = next(x['sha'] for x in acceptance_p['tree'] if x['path'] == r2)
    assert r2_h == r2_p
    for tree in [head, parent, docs_h, docs_p, lyd_h, lyd_p, acceptance_h, acceptance_p]:
        assert not tree['truncated']
    product_h = next(x['sha'] for x in head['tree'] if x['path'] == 'mod_li_yu_dao')
    product_p = next(x['sha'] for x in parent['tree'] if x['path'] == 'mod_li_yu_dao')
    assert product_h == product_p

    definition = observations['definition-li-yu-dao-static.yml']['result']['structuredContent']['content']
    paths = ['mod_li_yu_dao/**', 'tools/extract_auto_upgrade_buildings.py',
             'docs/li-yu-dao/acceptance/2026-10-04-R0002-native-cycles-formal-red/**',
             '.github/workflows/li-yu-dao-static.yml']
    assert all(f"- '{path}'" in definition for path in paths)
    registry_error = observations['workflow-registry']['result']
    runs = data('runs-001')
    assert runs['total_count'] == 1 and len(runs['workflow_runs']) == 1
    run = runs['workflow_runs'][0]
    assert run['head_sha'] == incoming['commit'] and run['event'] == 'push'
    assert run['status'] == 'completed' and run['conclusion'] == 'success'
    jobs = data('jobs-37228194002')
    assert jobs['total_count'] == 1 and len(jobs['jobs']) == 1
    job = jobs['jobs'][0]
    assert job['status'] == 'completed' and job['conclusion'] == 'success'
    counts = Counter(step['conclusion'] for step in job['steps'])
    assert counts == {'success': 60, 'skipped': 20}
    log_body = observations['logs-111512127603']['result']['structuredContent']['content']
    assert 'bfe0514650dbb446f6cab2a8543d3e4bf1582aff' in log_body
    assert data('artifacts-37228194002')['total_count'] == 0
    workflow_sizes = []
    for item in data('workflow-directory'):
        body = observations['definition-' + item['name']]['result']['structuredContent']['content'].encode('utf-8')
        assert len(body) == item['size']
        blob_hash = hashlib.sha1(b'blob ' + str(len(body)).encode('ascii') + b'\0' + body).hexdigest()
        assert blob_hash == item['sha']
        workflow_sizes.append({'path': item['path'], 'bytes': len(body), 'sha256': sha(body),
                               'git_blob_sha1': blob_hash, 'verified_against_github_blob': True})

    report = {
        'schema': 'lyd-ci-evidence/v1', 'repository': incoming['repository'], 'commit': incoming['commit'],
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'read_only': True, 'dispatch_rerun_or_publication': False,
        'workflow_runs_api_query': observations['runs-001']['request']['url'],
        'query_used_pr_filtered_wrapper': False,
        'exact_commit_ci': {'status': 'PASS', 'run_id': run['id'], 'run_url': run['html_url'],
                            'workflow': run['path'], 'event': run['event'], 'run_attempt': run['run_attempt'],
                            'job_id': job['id'], 'job_conclusion': job['conclusion'],
                            'step_conclusions': dict(counts), 'artifact_count': 0},
        'lyd_specific_workflow': {
            'status': 'NOT_TRIGGERED_DOCS_ONLY', 'observed_run_count': 0,
            'conclusion': 'NOT_RUN', 'inference': 'Actual commit trees changed only LYD README and new R0006 report subtree; no configured path changed.',
            'push_paths_from_exact_commit_definition': paths,
            'root_changed_paths': root_diff, 'docs_changed_paths': docs_diff,
            'lyd_docs_changed_paths': lyd_diff, 'acceptance_changed_paths': acceptance_diff,
            'r2_watched_tree_sha_before': r2_p, 'r2_watched_tree_sha_after': r2_h,
            'product_tree_sha_before': product_p, 'product_tree_sha_after': product_h},
        'workflow_definitions': workflow_sizes,
        'limits': [
            'GitHub tool exposes UTF-8 body strings, not HTTP wire bytes or response headers. Exact exposed body UTF-8 bytes and complete serialized connector result are preserved.',
            'Commit detail API response includes 300 file records and is not used as an exhaustive changed-file list. Eight untruncated Git trees prove all top-level and relevant nested changes.',
            'Workflow registry endpoint was rejected by connector allowlist; original error is preserved. Runs and exact-commit workflow directory/definitions were retrieved successfully.',
            'General CI success does not prove LYD-specific workflow execution, new 70-file source CI, CK3 runtime correctness, or formal union/leadership/reload acceptance.',
            'Twenty skipped steps are actual optional release/manual steps; they are not counted as passed tests.',
            'Prior 3d3305e CI is not used as exact-commit proof for this commit.'
        ]
    }
    dump(ROOT / 'REPORT.json', report)
    text = f'''本包只读采集 GitHub，并仅写入外置目录。目标提交：{incoming['commit']}。

实际 push CI：Official Runner CI，run {run['id']}，job {job['id']}，completed/success；60 个步骤 success，20 个可选发布步骤 skipped，0 个 artifact。完整 job 日志与每项响应已保存。

Li Yu Dao static checks 在本提交没有 run。按该提交的实际 workflow paths 和 8 个未截断 Git tree，变更仅在 docs/li-yu-dao/README.md 和新 R0006 验收报告树；mod_li_yu_dao、共享读取器、专题 workflow 与其指定 R0002 报告树都没有变化。因此为 NOT_TRIGGERED_DOCS_ONLY，绝非专题 CI PASS。

5 个 workflow 定义保存为实际 UTF-8 字节，并逐项核验 GitHub 返回的文件长度与 Git blob SHA-1；另保存 SHA-256。GitHub 连接器不提供 HTTP 原始传输字节或 headers，包内 body 是工具实际暴露的 UTF-8 字符串字节，response 是完整连接器结果的 JSON 序列化。

workflow registry GET 被连接器白名单拒绝，原始失败响应保留。commit detail 的 300 个文件记录不被当作完整 1170 文件列表；所有路径结论由未截断 tree 验证。

此包不证明新 70 文件候选源、CK3 实机、反复合流/分裂、领袖或重载通过。未触发任何 workflow_dispatch/rerun，未修改 Git、主树、Steam 或游戏。

实际 run：{run['html_url']}
'''
    raw(ROOT / 'REPORT.md', text.encode('utf-8'))
    index = {'schema': 'lyd-external-evidence-index/v1', 'index_excludes_self': True,
             'created_at_utc': datetime.now(timezone.utc).isoformat(), 'files': []}
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and path.name != 'INDEX.json':
            body = path.read_bytes()
            index['files'].append({'path': path.relative_to(ROOT).as_posix(), 'bytes': len(body), 'sha256': sha(body)})
    dump(ROOT / 'INDEX.json', index)
    print(json.dumps({'file_count': len(index['files']), 'report_sha256': sha((ROOT / 'REPORT.json').read_bytes()),
                      'index_sha256': sha((ROOT / 'INDEX.json').read_bytes()), 'overall': 'GENERAL_CI_PASS_LYD_NOT_TRIGGERED'}, ensure_ascii=False))


if __name__ == '__main__':
    main()

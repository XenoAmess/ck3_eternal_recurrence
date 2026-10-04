"""Read-only validation of preserved GitHub GET results; write NEW local proof only."""
from __future__ import annotations
import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/workspace/ck3_eternal_recurrence')
COMMIT = '3d3305e75cf642a7a82bef5f9aee03dc76b3c10e'
PRODUCT_TREE = '2e290b9b7fca02c38a33e4c73f5c46e7060dc9fa'
REQUIRED = {
    '.github/workflows/static-ci.yml': 37200670917,
    '.github/workflows/li-yu-dao-static.yml': 37200670823,
}

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def write_new(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(data)

def write_json(path: Path, value) -> None:
    write_new(path, (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8'))

def git(*args: str) -> bytes:
    result = subprocess.run(['git', '-C', str(REPO), *args], capture_output=True, check=True)
    return result.stdout

def materialize(connector: Path):
    envelope = json.loads(connector.read_bytes())
    assert envelope.get('isError') is False, connector
    content = envelope['structuredContent']['content']
    # This is exact UTF-8 encoding of the connector's returned content string,
    # without an appended newline. It is not a claim about HTTP wire bytes.
    raw = content.encode('utf-8')
    write_new(connector.with_name(connector.name.replace('.connector.json', '.content.bin')), raw)
    return json.loads(content)

def main() -> None:
    assert not (ROOT / 'report.json').exists(), 'frozen report already exists'
    identity = git('rev-parse', 'HEAD', 'HEAD:mod_li_yu_dao').decode().splitlines()
    assert identity == [COMMIT, PRODUCT_TREE], identity
    write_new(ROOT / 'source' / 'git-exact-head.stdout.bin', git('rev-parse', 'HEAD', 'HEAD:mod_li_yu_dao'))
    write_new(ROOT / 'source' / 'git-status.stdout.bin', git('status', '--porcelain=v1'))
    for workflow in REQUIRED:
        write_new(ROOT / 'source' / workflow, git('show', f'{COMMIT}:{workflow}'))
    parsed = {str(p.relative_to(ROOT)): materialize(p) for p in sorted(ROOT.rglob('*.connector.json'))}
    first = parsed['poll-001/runs.connector.json']
    assert first['total_count'] == len(first['workflow_runs']) == 2
    assert all(r['head_sha'] == COMMIT for r in first['workflow_runs'])
    first_by_id = {r['id']: r for r in first['workflow_runs']}
    summaries = []
    for workflow, run_id in REQUIRED.items():
        run = parsed[f'terminal-001/run-{run_id}.connector.json']
        jobs = parsed[f'terminal-001/jobs-{run_id}.connector.json']
        assert run['head_sha'] == COMMIT and run['path'] == workflow
        assert run['head_branch'] == 'master' and run['event'] == 'push'
        assert run['run_attempt'] == 1 and run['status'] == 'completed' and run['conclusion'] == 'success'
        assert jobs['total_count'] == len(jobs['jobs']) == 1, 'all jobs fit first page'
        job_summaries = []
        for job in jobs['jobs']:
            assert job['run_id'] == run_id and job['head_sha'] == COMMIT
            assert job['status'] == 'completed' and job['conclusion'] == 'success'
            assert all(step['status'] == 'completed' and step['conclusion'] in ('success', 'skipped') for step in job['steps'])
            job_summaries.append({key: job.get(key) for key in ('id', 'name', 'head_sha', 'run_attempt', 'status', 'conclusion', 'html_url', 'started_at', 'completed_at')})
            job_summaries[-1]['step_outcomes'] = dict(Counter(s['conclusion'] for s in job['steps']))
            job_summaries[-1]['skipped_steps'] = [s['name'] for s in job['steps'] if s['conclusion'] == 'skipped']
        summaries.append({
            'path': workflow, 'run_id': run_id, 'name': run['name'],
            'head_sha': run['head_sha'], 'html_url': run['html_url'],
            'run_attempt': run['run_attempt'], 'event': run['event'],
            'first_status': first_by_id[run_id]['status'], 'first_conclusion': first_by_id[run_id]['conclusion'],
            'status': run['status'], 'conclusion': run['conclusion'],
            'created_at': run['created_at'], 'updated_at': run['updated_at'],
            'jobs': job_summaries,
        })
    report = {
        'schema': 'lyd.exact-head-ci-readonly.report.v1',
        'generated_utc': datetime.now(timezone.utc).isoformat(),
        'repository': 'XenoAmess/ck3_eternal_recurrence', 'commit': COMMIT,
        'product_tree': PRODUCT_TREE, 'result': 'PASS_TWO_REQUIRED_EXACT_HEAD_RUNS_AND_JOBS',
        'required_workflows': summaries, 'mutating_github_operations': [],
        'clean_checkout_observed': not (ROOT / 'source/git-status.stdout.bin').read_bytes(),
        'scope': 'Static official GitHub Windows runner checks only. No CK3 campaign, save-state, desktop, MCP or R6 acceptance credit.',
        'payload_boundary': 'Full connector envelopes and exact UTF-8 structured-content strings preserved. No HTTP transport/header/wire-byte claim.',
    }
    write_json(ROOT / 'report.json', report)
    lines = [
        '# Exact HEAD CI evidence', '',
        f'Commit: `{COMMIT}`. LYD product tree: `{PRODUCT_TREE}`.', '',
        'Both required push workflows and all their jobs completed successfully, attempt 1. This is static CI evidence; R6 native acceptance is pending.', '',
    ]
    for r in summaries:
        j = r['jobs'][0]
        lines.append(f"- [{r['name']}]({r['html_url']}): run `{r['run_id']}`, job `{j['id']}`, `success`; {j['step_outcomes']}.")
    lines += ['', 'Official optional/manual/tagged release steps were skipped; their names remain in report.json. No retry, dispatch, cancellation or other CI mutation was performed.', '',
              'See [report.json](report.json), [collection-receipts.json](collection-receipts.json), [INDEX.json](INDEX.json), `poll-001/`, `terminal-001/`, and exact workflow snapshots under `source/`.', '',
              'Each `*.content.bin` preserves the exact UTF-8 encoding of the connector-returned structured content string without a trailing newline. The connector envelope and readable JSON are retained separately. Transport headers and HTTP wire bytes were unavailable.', '']
    write_new(ROOT / 'README.md', '\n'.join(lines).encode())
    artifacts = []
    for p in sorted(ROOT.rglob('*')):
        if p.is_file():
            raw = p.read_bytes()
            artifacts.append({'path': str(p.relative_to(ROOT)).replace('\\', '/'), 'bytes': len(raw), 'sha256': sha(raw)})
    write_json(ROOT / 'INDEX.json', {'schema': 'lyd.readonly-evidence-index.v1', 'commit': COMMIT, 'product_tree': PRODUCT_TREE, 'artifacts': artifacts})
    print(json.dumps({'result': report['result'], 'report_sha256': sha((ROOT / 'report.json').read_bytes()), 'index_sha256': sha((ROOT / 'INDEX.json').read_bytes()), 'path': str(ROOT)}, indent=2))

if __name__ == '__main__':
    main()

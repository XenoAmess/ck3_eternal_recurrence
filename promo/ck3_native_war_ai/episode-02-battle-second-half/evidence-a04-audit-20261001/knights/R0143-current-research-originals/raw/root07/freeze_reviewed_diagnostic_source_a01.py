"""Freeze only reviewed diagnostic and artifact projection repairs privately."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
SOURCE = Path('C:/w/e2research1001')
FROZEN = Path('C:/w/e2cap1001e')
OLD_HEAD = '4ad477ee33e15a93e412f711c7b05b216a2e6651'
RECEIPTS = [
 (Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0142-trace-publish-diagnostic-repair-attempt-01/source-freeze-a01/source-ready-and-test-receipt-a01.json'), 'CB565DF800F661F47C4D7510091DD7E68F95E5E0B54F99E4CD9F6F4A6DB7FC32'),
 (Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/knight-death-artifact-wire-repair-attempt-01/source-freeze-a01/source-ready-and-test-receipt-a01.json'), '43CEFBD381A874FE38A3F48D344080E7A206B7008BDB2D84E1D3F74640A34315')]
def require(ok, msg):
    if not ok: raise RuntimeError(msg)
def identity(p):
    p = Path(p).resolve()
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}
def write(name, value):
    with (ROOT / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
def git(*args):
    return subprocess.check_output(['git', *args], cwd=SOURCE).decode('utf-8').strip()
require(git('rev-parse', 'HEAD') == OLD_HEAD and git('branch', '--show-current') == 'codex/war-e2-mechanism-closure-20261001', 'Private source moved')
rows = git('status', '--porcelain=v1').splitlines()
files = {row[3:] for row in rows}
require(len(files) == 12 and all(row[:3] in (' M ', '?? ') for row in rows), 'Unexpected source changes')
bound = {}
def visit(v):
    if isinstance(v, dict):
        if isinstance(v.get('path'), str) and 'bytes' in v and 'sha256' in v:
            p = Path(v['path']).resolve()
            if p in {(SOURCE / n).resolve() for n in files}:
                now = identity(p)
                require(now['bytes'] == v['bytes'] and now['sha256'] == v['sha256'].upper(), 'Reviewed source bytes differ')
                bound[p] = now
        for x in v.values(): visit(x)
    elif isinstance(v, list):
        for x in v: visit(x)
for p, sha in RECEIPTS:
    require(identity(p)['sha256'] == sha, 'Ready receipt changed')
    visit(json.loads(p.read_text(encoding='utf-8')))
require(len(bound) == 12, 'Not all source files have READY hash bindings')
require(not FROZEN.exists(), 'New frozen checkout already exists')
write('private-source-freeze-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
      'predecessor': OLD_HEAD, 'source_inputs': list(bound.values()),
      'ready_receipts': [identity(p) for p, _ in RECEIPTS],
      'root_review': 'Reviewed additive diagnostic gates, original RED parsed return retention, native caps/flags unchanged and artifact field exact original null/non-null projection. Actual focused tests already passed; full Release link pending.',
      'master_intake': False, 'video_changed': False, 'live_pending': True})
commands = [['git', 'diff', '--check'], ['git', 'add', '--', *sorted(files)],
            ['git', 'diff', '--cached', '--check'], ['git', 'commit', '-m', 'Preserve native scoped trace failures and correct exact artifact tuple projection'],
            ['git', 'worktree', 'add', '-b', 'codex/war-e2-trace-diagnostic-capture-20261001', str(FROZEN), 'HEAD']]
for i, argv in enumerate(commands, 1):
    result = subprocess.run(argv, cwd=SOURCE, capture_output=True)
    for suffix, data in [('stdout', result.stdout), ('stderr', result.stderr)]:
        with (ROOT / f'private-source-step-{i}-{suffix}.bin').open('xb') as f: f.write(data)
    write(f'private-source-step-{i}.json', {'argv': argv, 'returncode': result.returncode,
          'stdout': identity(ROOT / f'private-source-step-{i}-stdout.bin'), 'stderr': identity(ROOT / f'private-source-step-{i}-stderr.bin')})
    require(result.returncode == 0, 'Private freeze failed; original outputs retained')
head = git('rev-parse', 'HEAD')
require(not git('status', '--porcelain=v1'), 'Committed source dirty')
require(set(git('diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()) == files, 'Commit scope differs')
require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=FROZEN).decode().strip() == head and not subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=FROZEN).strip(), 'Frozen runtime not exact clean source')
write('private-source-commit-and-runtime-freeze.json', {'source_commit': head, 'source': str(SOURCE), 'frozen_source': str(FROZEN),
      'source_branch': git('branch', '--show-current'), 'runtime_branch': 'codex/war-e2-trace-diagnostic-capture-20261001',
      'source_files': sorted(files), 'clean_source_and_runtime': True, 'no_master_intake': True, 'video_changed': False, 'live_pending': True})
with (ROOT / 'reviewed-native-targets-a02.json').open('xb') as f:
    f.write((ROOT.parent / 'root-attempt-06-hidden-modal-ui/reviewed-native-targets-a02.json').read_bytes())
print(head)

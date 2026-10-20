from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent
W=ROOT.parent/'integration-worktree'
HEAD='f960a1b4b46efa5359e403c9d308b2a808a2f7d0'
path='.github/workflows/static-ci.yml'
assert datetime.now(timezone.utc)<datetime(2026,10,20,14,45,tzinfo=timezone.utc)
r=subprocess.run(['git','-C',str(W),'show',HEAD+':'+path],capture_output=True,check=True)
raw=r.stdout;text=raw.decode('utf8');lines=text.splitlines()
for i,line in enumerate(lines):
    if 'pip install' in line and ('mcp' in line or 'pytest' in line):
        print('\n'.join(f'{n+1}: {lines[n]}' for n in range(max(0,i-3),min(len(lines),i+5))))
(ROOT/'WORKFLOW-DEPENDENCY-SOURCE.actual.json').write_bytes((json.dumps(dict(
    machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
    exact_head=HEAD,repository_path=path,blob_bytes=len(raw),blob_sha256=hashlib.sha256(raw).hexdigest(),
    matching_lines=[dict(number=i+1,text=s) for i,s in enumerate(lines) if 'mcp' in s or 'R08' in s],
    source='local Git object read; no checkout or fetch'),indent=2)+'\n').encode('utf8'))
dependency='          python -m pip install mcp==2.0.0 pytest==9.1.1\n          if not "%errorlevel%"=="0" exit /b %errorlevel%\n'
anchor='      - name: Test public R08 single writer opportunity refusals\n        run: |\n'
assert text.count(dependency)==1 and text.count(anchor)==1
updated=text.replace(dependency,'').replace(anchor,anchor+dependency)
patch=''.join(difflib.unified_diff(text.splitlines(keepends=True),updated.splitlines(keepends=True),
    fromfile='a/'+path,tofile='b/'+path))
target=ROOT/'R08-CI-DEPENDENCIES-BEFORE-SMOKE.candidate.patch';target.write_bytes(patch.encode('utf8'))
argv=['git','-C',str(W),'apply','--check','--whitespace=error',str(target)]
check=subprocess.run(argv,capture_output=True,text=True)
def pin(p):
    b=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
value=dict(machine_id='desktop-3fevhd2-1c74096080',observed_at_utc=datetime.now(timezone.utc).isoformat(),
    cause='Actual failed-step log: MCP missing before registered-tool smoke; parent actor test passed',
    runner_python='3.13.16 from actual log; no observed Python-version incompatibility',
    patch=pin(target),original_log_excerpt=pin(ROOT/'FAILED-STEP-EXCERPT.actual.log'),
    source_index=pin(ROOT/'WORKFLOW-DEPENDENCY-SOURCE.actual.json'),
    change='Move existing identical pinned mcp==2.0.0 pytest==9.1.1 installation+error guard from later public-CUnit step to start of R08 step; no added package/version or test skip',
    check_argv=argv,check_original_returncode=check.returncode,check_stdout=check.stdout,check_stderr=check.stderr,
    validation='Read-only patch check only. Requires new exact-head official CI after approved integration; no local test rerun/download/install.',
    diagnostic_attempt='First gh client refused terminal ANSI escape output before providing body; one successful retrieval with --allow-escape-sequences, only f960 job; no fe log read',
    D_W_source_writes=False,SDK_game_CI_rerun_download_tool=False)
receipt=ROOT/'ROOT-CAUSE-AND-PATCH.actual.json';receipt.write_bytes((json.dumps(value,indent=2)+'\n').encode('utf8'))
assert sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())<=65536
print(json.dumps({'patch':pin(target),'receipt':pin(receipt),'check_returncode':check.returncode,
    'lane_bytes':sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())}))

"""Append-only, bounded compile and synthetic ABI fixture; no game contact."""
from pathlib import Path
import concurrent.futures
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import argparse
ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, default=ROOT.parents[3])
parser.add_argument('--build-dir', type=Path, required=True)
parser.add_argument('--source-overlay', type=Path,
                    help='Optional explicit repo-shaped candidate; absent paths use repo sources')
parser.add_argument('--plan-only', action='store_true', help='Print declared scope without creating a build or resolving MSVC')
args = parser.parse_args()
REPO = args.repo.resolve()
DEST = args.build_dir.resolve()
OVERLAY = args.source_overlay.resolve() if args.source_overlay else None
NATIVE_REL = Path('ck3_autonomous_player/native_bridge')
def source_path(relative):
    candidate = OVERLAY/relative if OVERLAY else None
    return candidate if candidate is not None and candidate.is_file() else REPO/relative
if args.plan_only:
    print(json.dumps({'mode':'PLAN_ONLY_NO_BUILD', 'repo':str(REPO), 'build_dir':str(DEST),
                      'sources':[str(NATIVE_REL/'src'/name) for name in
                                 ['war_payment_passive_12004.cpp','war_payment_json_12004.cpp','war_payment_runtime_12004.cpp']],
                      'fixture':'ck3_autonomous_player/native_bridge/tests/war_payment_generic_context/generic_context_fixture.cpp',
                      'scope':'3 compile TUs + runtime OFF/ON syntax + exact-registered synthetic EXE; no game or full bridge'}))
    raise SystemExit(0)
def require(ok, message):
    if not ok:
        raise RuntimeError(message)
def pin(path):
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
def save(path, value):
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')
def budget():
    scopes = [ROOT] + ([] if DEST.is_relative_to(ROOT) else [DEST])
    files = [p for scope in scopes for p in scope.rglob('*') if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    require(size < 64 * 1024**2, 'Focused source/build lane exceeded64MiB')
    return {'files':len(files),'bytes':size,'maximum_bytes':64*1024**2}
require(not DEST.exists(), 'New native attempt required')
DEST.mkdir()
sys.pycache_prefix = str(DEST / '.python-cache')
sys.path.insert(0, str(REPO / 'tools'))
import run_native_msvc as msvc
import register_project_exe_exclusions as defender
from ck3_live_run_id import current_machine_id
report = {'schema':'xar.generic-wallet-context.focused-native-check.v1',
          'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
          'machine_id':current_machine_id(),'main_tree_writes':0,
          'game_contact':False,'full_bridge_build':False,'dll_deployed':False,
          'attempt':str(DEST),'commands':[],'checks':[]}
try:
    freeze = DEST / 'source-freeze'
    include = freeze / 'include'
    candidate = OVERLAY/NATIVE_REL if OVERLAY else REPO/NATIVE_REL
    repo_include = REPO/NATIVE_REL/'include'
    sources = [source_path(NATIVE_REL/'src/war_payment_passive_12004.cpp'),
               source_path(NATIVE_REL/'src/war_payment_json_12004.cpp'),
               source_path(NATIVE_REL/'src/war_payment_runtime_12004.cpp'),
               ROOT/'generic_context_fixture.cpp']
    freeze.mkdir()
    shutil.copyfile(Path(__file__),DEST/'runner-source.py')
    pending = []
    frozen_sources = []
    for path in sources:
        dest = freeze / path.name
        shutil.copyfile(path, dest)
        frozen_sources.append(dest)
        pending.append((path, dest))
    headers = {}
    pattern = re.compile(r'^\s*#include\s+"([^"\n]+)"', re.M)
    while pending:
        origin, frozen = pending.pop()
        for name in pattern.findall(frozen.read_text(encoding='utf-8-sig')):
            if name in headers:
                continue
            path = next((p for p in [candidate/'include'/name, origin.parent/name, repo_include/name] if p.is_file()), None)
            require(path is not None, 'Unresolved exact quoted include: ' + name)
            require(len(headers) < 128, 'Reached header count budget')
            dest = include / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
            headers[name] = {'original':str(path),**pin(dest)}
            require(sum(row['bytes'] for row in headers.values()) < 2*1024**2, 'Reached header bytes budget')
            pending.append((path,dest))
    report['frozen_sources']=[pin(p) for p in frozen_sources]
    report['frozen_reached_headers']=list(headers.values())
    save(DEST/'SOURCE-FREEZE.actual.json', {k:report[k] for k in ['machine_id','created_utc','frozen_sources','frozen_reached_headers']})
    environment = msvc.child_environment(DEST)
    installation = msvc.visual_studio_installation(None,environment)
    environment, tools = msvc.initialize_msvc(installation,DEST,environment)
    report['tools']=tools
    base = [tools['cl'],'/nologo','/std:c++20','/EHsc','/W4','/WX','/O2','/MD','/Gy','/utf-8','/DNOMINMAX','/DWIN32_LEAN_AND_MEAN','/I'+str(include)]
    def run(label, argv):
        result=subprocess.run(argv,cwd=DEST,env=environment,capture_output=True,check=False)
        out=DEST/(label+'.stdout.bin');err=DEST/(label+'.stderr.bin')
        out.write_bytes(result.stdout);err.write_bytes(result.stderr)
        row={'label':label,'argv':argv,'return_code':result.returncode,'stdout':pin(out),'stderr':pin(err)}
        save(DEST/(label+'.command.actual.json'),row)
        return row
    commands=[]
    compile_sources=[frozen_sources[0],frozen_sources[1],frozen_sources[3]]
    for source in compile_sources:
        commands.append((source.stem,base+['/c',str(source),'/Fo'+str(DEST/(source.stem+'.obj'))]))
    commands += [('runtime-default-off-Zs',base+['/Zs',str(frozen_sources[2])]),
                 ('runtime-enabled-Zs',base+['/DXAR_ENABLE_WAR_PAYMENT_GENERIC_CONTEXT_12004=1','/Zs',str(frozen_sources[2])])]
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures=[pool.submit(run,label,argv) for label,argv in commands]
        report['commands']=[f.result() for f in futures]
    for row in report['commands']:
        print(row['label'], 'rc',row['return_code'],flush=True)
        if row['return_code']:
            print(Path(row['stdout']['path']).read_bytes().decode('mbcs',errors='replace'),flush=True)
            print(Path(row['stderr']['path']).read_bytes().decode('mbcs',errors='replace'),flush=True)
    require(all(row['return_code']==0 for row in report['commands']), 'Focused compiler check failed; attempt retained')
    link = str(Path(tools['cl']).with_name('link.exe'))
    exe=DEST/'generic_context_fixture.exe'
    linkargv=[link,'/nologo','/INCREMENTAL:NO','/OPT:REF','/OPT:ICF',
              *[str(DEST/(p.stem+'.obj')) for p in compile_sources],'/OUT:'+str(exe),'kernel32.lib','user32.lib']
    linked=run('link-fixture',linkargv);report['commands'].append(linked)
    require(linked['return_code']==0,'Focused fixture link failed')
    report['fixture_exe']=pin(exe)
    registration=defender.after_successful_command_build(
        REPO,freeze,DEST,linkargv,[exe],
        external_candidate='offline generic-wallet raw-context candidate; bounded source-qualified .4; synthetic ABI fixture only',
        return_code=0,source_commands=[{'argv':row['argv'],'return_code':row['return_code']} for row in report['commands'][:3]])
    report['defender_exclusions']=registration
    save(DEST/'DEFENDER-REGISTRATION.actual.json',registration)
    require(registration['status']=='verified','Exact fixture EXE Defender registration not verified; no execution')
    wire=DEST/'serialized-generic-context-wire.actual.json'
    executed=run('execute-fixture',[str(exe),str(wire)]);report['commands'].append(executed)
    report['fixture_summary']=json.loads(Path(executed['stdout']['path']).read_text(encoding='utf-8').strip())
    require(executed['return_code']==0 and report['fixture_summary'].get('failures')==0,'Actual synthetic native fixture failed')
    require(report['fixture_summary'].get('case_count')==16,'Unexpected native case count')
    report['wire']=pin(wire)
    report['status']='PASS'
except Exception as error:
    report['status']='RED'
    report['error']={'type':type(error).__name__,'message':str(error)}
finally:
    report['budget']=budget()
    report['completed_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    save(DEST/'RESULT.actual.json',report)
    print(json.dumps({'status':report['status'],'report':pin(DEST/'RESULT.actual.json'),
                      'wire':report.get('wire'),'error':report.get('error'),'budget':report['budget']},ensure_ascii=False),flush=True)
raise SystemExit(0 if report['status']=='PASS' else 1)

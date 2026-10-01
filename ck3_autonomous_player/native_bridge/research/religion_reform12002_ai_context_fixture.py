"""Build/run actual AI holder reader and its frozen schedule consumption once."""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess
from pathlib import Path
def main()->int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    native=Path(__file__).resolve().parents[1];root=native.parents[1]
    out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True);tmp=out/'tmp';tmp.mkdir(exist_ok=True)
    where=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.run([str(where),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(install)/'VC/Auxiliary/Build/vcvars64.bat'
    sources=[native/'src'/x for x in ['religion_reform12002_ai_context.cpp','religion_reform12002_ai_context_test.cpp','religion_reform12002_schedule.cpp']]
    exe=out/'reform-ai-context-test.exe'
    command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/utf-8','/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(exe)])
    batch=out/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf8')
    env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp))
    build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=out,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
    (out/'build.log').write_text(build.stdout+build.stderr,encoding='utf8')
    if build.returncode:raise RuntimeError(str(out/'build.log'))
    run=subprocess.run([str(exe)],cwd=out,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
    (out/'test.log').write_text(run.stdout+run.stderr,encoding='utf8')
    if run.returncode:raise RuntimeError(str(out/'test.log'))
    wire=json.loads(next(line[5:] for line in run.stdout.splitlines() if line.startswith('wire:')))
    if not wire['available'] or len(wire['controllers'])!=2 or any('actual_ai' in row for row in wire['controllers']):raise ValueError('Actual serializer wire')
    pins=sources+[native/'include/xar_bridge/religion_reform12002_ai_context.hpp']
    result={'status':'GREEN','readiness':'static-ready','local_ck3_touched':False,'live_verified':False,
        'mode':'O2','compiler':'MSVC /W4 /WX','actual_cases':9,'actual_serializer_wire':wire,
        'frozen_schedule_consumption_cases':2,'stdout':run.stdout.strip(),
        'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),
        'source_sha256':{x.relative_to(root).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in pins}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2));return 0
if __name__=='__main__':raise SystemExit(main())

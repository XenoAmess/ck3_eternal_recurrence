"""Build/run the actual main Rite unreformed reader in MSVC Od and O2."""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess
from pathlib import Path
def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True,type=Path);a=p.parse_args()
    native=Path(__file__).resolve().parents[1];root=native.parents[1];out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    where=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
    install=subprocess.run([str(where),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
    vcvars=Path(install)/'VC/Auxiliary/Build/vcvars64.bat'
    sources=[native/'src'/x for x in ['religion_reform12002_willingness.cpp','religion_reform12002_willingness_test.cpp']]
    runs=[]
    for mode in ['Od','O2']:
        target=out/mode;target.mkdir(exist_ok=True);temp=target/'tmp';temp.mkdir(exist_ok=True)
        exe=target/'reform-main-rite-test.exe'
        command=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/'+mode,'/W4','/WX','/utf-8','/I'+str(native/'include'),*map(str,sources),'/Fe:'+str(exe)])
        batch=target/'build.cmd';batch.write_text('@echo off\ncall "'+str(vcvars)+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+command+'\nexit /b %errorlevel%\n',encoding='utf8')
        env=dict(os.environ,TEMP=str(temp),TMP=str(temp))
        build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=target,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
        (target/'build.log').write_text(build.stdout+build.stderr,encoding='utf8')
        if build.returncode:raise RuntimeError(str(target/'build.log'))
        run=subprocess.run([str(exe)],cwd=target,env=env,capture_output=True,text=True,encoding='utf8',errors='replace')
        (target/'test.log').write_text(run.stdout+run.stderr,encoding='utf8')
        if run.returncode:raise RuntimeError(str(target/'test.log'))
        runs.append({'mode':mode,'returncode':run.returncode,'stdout':run.stdout.strip(),'executable_sha256':hashlib.sha256(exe.read_bytes()).hexdigest()})
        print(mode,run.stdout.strip())
    pins=sources+[native/'include/xar_bridge/religion_reform12002_willingness.hpp']
    result={'status':'GREEN','readiness':'static-ready','local_ck3_touched':False,'live_verified':False,'provider':'ReadFaithMainRiteUnreformed12002','actual_cases_per_mode':8,'runs':runs,
            'source_sha256':{x.relative_to(root).as_posix():hashlib.sha256(x.read_bytes()).hexdigest() for x in pins}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');return 0
if __name__=='__main__':raise SystemExit(main())

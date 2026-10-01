"""Build the real clergy provider with fixture-owned memory; no CK3 access."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
NATIVE=HERE.parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts',type=Path,required=True)
    a=p.parse_args(); a.artifacts.mkdir(parents=True,exist_ok=True)
    vcvars=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars64.bat')
    rows=[]
    for mode,flag in [('Od','/Od'),('O2','/O2 /DNDEBUG')]:
        out=a.artifacts/mode; out.mkdir(exist_ok=True); wire=out/'wire'; wire.mkdir(exist_ok=True)
        script=out/'build.cmd'
        sources=['ck3_12002.cpp','religion_rite_governance12002_clergy.cpp','religion_rite_governance12002_clergy_test.cpp']
        command='cl /nologo /std:c++20 /EHsc /W4 /WX '+flag+' /I "'+str(NATIVE/'include')+'" '
        command+=' '.join('"'+str(NATIVE/'src'/s)+'"' for s in sources)+' /Fe:"'+str(out/'clergy_test.exe')+'"'
        script.write_text('@echo off\ncall "'+str(vcvars)+'"\n'+command+'\nexit /b %errorlevel%\n',encoding='utf-8')
        env=os.environ.copy(); env['TEMP']=str(out); env['TMP']=str(out)
        build=subprocess.run(['cmd.exe','/d','/c',str(script)],cwd=out,env=env,capture_output=True)
        (out/'build.log').write_bytes(build.stdout+build.stderr)
        if build.returncode:
            rows.append(dict(mode=mode,returncode=build.returncode,stage='compile',output=str(out/'build.log')))
            break
        run=subprocess.run([str(out/'clergy_test.exe'),str(wire)],cwd=out,env=env,capture_output=True)
        (out/'run.log').write_bytes(run.stdout+run.stderr)
        rows.append(dict(mode=mode,returncode=run.returncode,output=run.stdout.decode('utf-8','replace').strip(),
                         executable_sha256=sha(out/'clergy_test.exe'),
                         wire=[dict(path=str(path),sha256=sha(path)) for path in sorted(wire.glob('*.json'))]))
        if run.returncode:
            break
    result=dict(schema='xar.ck3.religion-clergy-appointment-fixture/v1',status='GREEN' if len(rows)==2 and all(r['returncode']==0 for r in rows) else 'RED',
                time_utc=datetime.now(timezone.utc).isoformat(),live_verified=False,configurations=rows,
                source_pins=[dict(path=str(NATIVE/'src'/s),sha256=sha(NATIVE/'src'/s)) for s in sources])
    (a.artifacts/'fixture-result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=result['status'],configurations=[dict(mode=r['mode'],output=r['output'],returncode=r['returncode']) for r in rows])))
    return 0 if result['status']=='GREEN' else 1

if __name__=='__main__':
    raise SystemExit(main())

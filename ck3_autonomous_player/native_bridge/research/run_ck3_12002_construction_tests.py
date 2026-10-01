"""Run isolated construction provider fixtures; never connects to CK3."""
from pathlib import Path
import argparse,json,os,shutil,subprocess

HERE=Path(__file__).resolve().parent
NATIVE=HERE.parent
def run(build:Path)->None:
    build.mkdir(parents=True,exist_ok=True)
    temporary=build/'tmp';temporary.mkdir(exist_ok=True)
    os.environ['TEMP']=str(temporary);os.environ['TMP']=str(temporary)
    from run_domain_construction_cost_legality_live_observer_v1_tests import _visual_studio_environment
    env=_visual_studio_environment();compiler=shutil.which('cl.exe',path=env.get('PATH'))
    if compiler is None:raise RuntimeError('MSVC cl.exe unavailable')
    suites=[]
    for name,flags in [('Debug',['/Od','/MDd']),('Release',['/O2','/MD'])]:
        output=build/f'construction-provider-{name}.exe'
        cmd=[compiler,'/nologo','/std:c++20','/W4','/WX','/permissive-','/EHsc','/DNOMINMAX','/DWIN32_LEAN_AND_MEAN',*flags,
             f'/I{NATIVE / "src"}',f'/I{NATIVE / "include"}',
             *(str(NATIVE/'src'/s) for s in ['ck3_12002_construction.cpp','ck3_12002_construction_held.cpp','ck3_12002_construction_test.cpp']),f'/Fe:{output}']
        cp=subprocess.run(cmd,cwd=build,env=env,capture_output=True,text=True)
        (build/f'compile-{name}.log').write_text(cp.stdout+cp.stderr,encoding='utf8')
        if cp.returncode:raise RuntimeError(f'compile RED {name}: {cp.stdout[-5000:]}{cp.stderr[-5000:]}')
        cp=subprocess.run([str(output)],cwd=build,env=env,capture_output=True,text=True)
        (build/f'run-{name}.log').write_text(cp.stdout+cp.stderr,encoding='utf8')
        if cp.returncode:raise RuntimeError(f'fixture RED {name}: {cp.stdout}{cp.stderr}')
        suites.append({'mode':name,'status':'GREEN','output':cp.stdout.strip()});print(name,cp.stdout.strip())
        process_output=build/f'construction-process-{name}.exe'
        process_cmd=[compiler,'/nologo','/std:c++20','/W4','/WX','/permissive-','/EHsc','/DNOMINMAX','/DWIN32_LEAN_AND_MEAN',*flags,
             f'/I{NATIVE / "src"}',f'/I{NATIVE / "include"}',
             *(str(NATIVE/'src'/s) for s in ['ck3_12002.cpp','ck3_12002_construction_process.cpp','ck3_12002_construction_process_test.cpp']),f'/Fe:{process_output}']
        cp=subprocess.run(process_cmd,cwd=build,env=env,capture_output=True,text=True)
        (build/f'process-compile-{name}.log').write_text(cp.stdout+cp.stderr,encoding='utf8')
        if cp.returncode:raise RuntimeError(f'process compile RED {name}: {cp.stdout}{cp.stderr}')
        cp=subprocess.run([str(process_output)],cwd=build,env=env,capture_output=True,text=True)
        (build/f'process-run-{name}.log').write_text(cp.stdout+cp.stderr,encoding='utf8')
        if cp.returncode:raise RuntimeError(f'process fixture RED {name}: {cp.stdout}{cp.stderr}')
        suites.append({'mode':name,'status':'GREEN','output':cp.stdout.strip()});print(name,cp.stdout.strip())
    (build/'result.json').write_text(json.dumps({'status':'GREEN','evidence_scope':'isolated synthetic memory/callbacks','game_process_started':False,'suites':suites},indent=2)+'\n',encoding='utf8')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--build-root',type=Path,required=True);args=p.parse_args();run(args.build_root.resolve())

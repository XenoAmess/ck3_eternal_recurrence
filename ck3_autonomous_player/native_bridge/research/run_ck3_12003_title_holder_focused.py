"""Build title-holder production reader/serializer and compile its live wiring.

Only compiler child processes and an isolated synthetic memory fixture run.
This helper does not access CK3, its SDK/pipe, desktop windows or Git.
"""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
NATIVE=ROOT/'ck3_autonomous_player/native_bridge'

def pin(path:Path)->dict:
    data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}

def main()->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir',type=Path,required=True)
    parser.add_argument('--reuse-green-build',type=Path)
    args=parser.parse_args()
    output=args.build_dir.resolve()
    output.mkdir(parents=True,exist_ok=False)
    wire=output/'wire'; wire.mkdir()
    sys.path.insert(0,str(ROOT/'tools'))
    from run_native_msvc import child_environment,initialize_msvc,visual_studio_installation
    env=child_environment(output)
    env,compiler=initialize_msvc(visual_studio_installation(None,env),output,env)
    linked=['ck3_12002_province.cpp','ck3_12003_title_holder.cpp',
            'title_holder_v1_serializer.cpp','ck3_12003_title_holder_test.cpp']
    wiring=['game_adapter.cpp','ck3_12002_adapter.cpp',
            'ck3_12002_semantic_adapter.cpp','ck3_12003_adapter.cpp','bridge.cpp']
    paths=[NATIVE/'src'/name for name in linked+wiring]
    source_pins=[pin(path) for path in paths]
    headers=[NATIVE/'include/xar_bridge'/name for name in
             ['title_holder_v1.hpp','ck3_12003_title_holder.hpp','title_holder_v1_serializer.hpp',
              'game_adapter.hpp','ck3_12002_semantic_adapter.hpp']]
    report={'schema':'ck3-12003-title-holder-focused/v1','status':'HARNESS-RED',
            'readiness':'source-ready','source_pins':source_pins,'header_pins':[pin(path) for path in headers],
            'compiler_argv':[],'native_cases':None,'native_assertions':None,
            'whole_dll_built':False,'ck3_access':False,'sdk_calls':0,'pipe_operations':0,
            'window_operations':0,'git_operations':0,
            'fixture_scope':'synthetic native component memory and liege getter seams; actual production reader and serializer',
            'exact_build':{'version':'1.20.0.3','steam_build_id':'25652598',
                           'sha256':'94B55397ABB687A3DCD436805A5D885E6BE90FA6C693FEB44A9E3BBEEADE02A6'}}
    options=['/nologo','/std:c++20','/EHsc','/O2','/DNDEBUG','/W4','/WX',
             '/permissive-','/utf-8','/DNOMINMAX','/DWIN32_LEAN_AND_MEAN',
             '/DUNICODE','/D_UNICODE','/Gy','/MD','/I'+str(NATIVE/'include'),
             '/I'+str(NATIVE/'src'),'/I'+str(NATIVE/'research')]
    started=time.perf_counter()
    try:
        commands=[]
        for path in paths:
            obj=output/(path.stem+'.obj')
            extra=['/DXAR_BRIDGE_VERSION="0.1.0"'] if path.name=='bridge.cpp' else []
            commands.append((path,[compiler['cl'],*options,*extra,'/c',str(path),'/Fo:'+str(obj)]))
        report['compiler_argv']=[command for _,command in commands]
        prior=None
        if args.reuse_green_build:
            previous=args.reuse_green_build.resolve()
            prior=json.loads((previous/'RESULT.json').read_text(encoding='utf-8'))
            if prior['source_pins']!=source_pins or prior['header_pins']!=report['header_pins']:
                raise RuntimeError('reused green objects have different source/header inputs')
        def compile_one(item):
            path,command=item
            if prior is not None:
                row=next(row for row in prior['compiles'] if row['source']==str(path))
                old_object=previous/(path.stem+'.obj')
                if row['exit_code']==0 and old_object.is_file():
                    shutil.copy2(old_object,output/old_object.name)
                    return {**row,'reused_green_object':pin(old_object),
                            'reused_green_receipt':str(previous/'RESULT.json')}
            built=subprocess.run(command,cwd=output,env=env,capture_output=True,timeout=240)
            log=output/(path.stem+'-compile.log')
            log.write_bytes(built.stdout+built.stderr)
            return {'source':str(path),'exit_code':built.returncode,'log':pin(log)}
        with ThreadPoolExecutor(max_workers=len(commands)) as pool:
            report['compiles']=list(pool.map(compile_one,commands))
        if any(row['exit_code'] for row in report['compiles']):
            raise RuntimeError('strict focused source/wiring compile failed')
        exe=output/'title-holder-focused.exe'
        link=[compiler['cl'],'/nologo',*[str(output/(Path(name).stem+'.obj')) for name in linked],
              '/Fe:'+str(exe),'/link','/OPT:REF']
        report['link_argv']=link
        linked_result=subprocess.run(link,cwd=output,env=env,capture_output=True,timeout=60)
        (output/'link.log').write_bytes(linked_result.stdout+linked_result.stderr)
        report['link_exit']=linked_result.returncode
        report['link_log']=pin(output/'link.log')
        if linked_result.returncode:
            raise RuntimeError('focused production fixture link failed')
        report['status']='FIXTURE-RED'
        run=subprocess.run([str(exe),str(wire)],cwd=output,env=env,capture_output=True,timeout=30)
        (output/'run.log').write_bytes(run.stdout+run.stderr)
        report.update(run_exit=run.returncode,run_log=pin(output/'run.log'),executable=pin(exe))
        if run.returncode:
            raise RuntimeError('production title-holder fixture failed')
        counts=re.search(rb'PASS checks=(\d+) cases=(\d+)',run.stdout)
        payloads=sorted(wire.glob('*.json'))
        if counts is None or len(payloads)!=int(counts[2]):
            raise RuntimeError('focused fixture did not emit complete real wire')
        report.update(native_assertions=int(counts[1]),native_cases=int(counts[2]),
                      native_json=[pin(path) for path in payloads])
        for path in payloads:
            frame=json.loads(path.read_text(encoding='utf-8'))
            if frame['result']['title_holder']['schema']!='xar.ck3.title-holder.v1':
                raise RuntimeError('production wire schema mismatch')
        if source_pins!=[pin(path) for path in paths]:
            raise RuntimeError('focused sources changed during run')
        report.update(status='NATIVE-GREEN',readiness='static-ready')
    except Exception as error:
        report['error']=repr(error)
    report['elapsed_seconds']=time.perf_counter()-started
    (output/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':report['status'],'receipt':str(output/'RESULT.json'),
                      'error':report.get('error'),'native_cases':report['native_cases'],
                      'native_assertions':report['native_assertions']},indent=2))
    return 0 if report['status']=='NATIVE-GREEN' else 1

if __name__=='__main__':
    raise SystemExit(main())

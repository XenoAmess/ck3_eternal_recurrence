"""Run only the new actual third-default-Tenet-slot production fixture.

The immutable old eight-case matrix is not run. Default reused objects are
the already-GREEN Tenet source O2 fixture's core/window/key-copy production objects.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path,required=True)
 p.add_argument('--reused-object-dir',type=Path,default=Path(r'Z:\ck3_mod_rewrite\artifacts\g2-offline-2026-10-01\religion-reform\tenet-sources\fixture'))
 a=p.parse_args();native=Path(__file__).resolve().parents[1];out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
 vswhere=Path(os.environ.get('ProgramFiles(x86)',r'C:\Program Files (x86)'))/'Microsoft Visual Studio/Installer/vswhere.exe'
 installed=subprocess.run([str(vswhere),'-latest','-products','*','-requires','Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-property','installationPath'],capture_output=True,text=True,check=True).stdout.strip()
 sources=[native/'src/religion_reform12002_tenet_sources.cpp',native/'src/religion_reform12002_tenet_sources_blank_slot_test.cpp']
 objects=[a.reused_object_dir/(name+'.obj')for name in ('ck3_12002','religion_reform12002_window','religion_doctrine12002_tenet_rows')]
 exe=out/'blank-slot-test.exe';cmd=subprocess.list2cmdline(['cl.exe','/nologo','/std:c++20','/EHsc','/O2','/W4','/WX','/utf-8','/I'+str(native/'include'),*map(str,sources),*map(str,objects),'/Fe:'+str(exe)])
 batch=out/'build.cmd';batch.write_text('@echo off\ncall "'+str(Path(installed)/'VC/Auxiliary/Build/vcvars64.bat')+'" >nul\nif errorlevel 1 exit /b %errorlevel%\n'+cmd+'\nexit /b %errorlevel%\n',encoding='utf-8')
 tmp=out/'tmp';tmp.mkdir(exist_ok=True);env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp))
 build=subprocess.run(['cmd.exe','/d','/c',str(batch)],cwd=out,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8')
 if build.returncode:raise RuntimeError('compile failed '+str(out/'build.log'))
 run=subprocess.run([str(exe),str(out)],cwd=out,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace');(out/'test.log').write_text(run.stdout+run.stderr,encoding='utf-8')
 if run.returncode:raise RuntimeError('new blank-slot fixture failed '+str(out/'test.log'))
 wire=out/'native-default-third-slot.json';value=json.loads(wire.read_text(encoding='utf-8'))
 assert value['available'] and value['tenet_gates_complete'] and len(value['slots'])==3 and len(value['sources'])==8
 assert value['slots'][2]=={'slot_index':2,'selected_tenet_key':None} and value['sources'][3]['final_selectable']
 result={'status':'GREEN','readiness':'static-ready','native_calls_stubbed':True,'local_ck3_touched':False,'new_case_count':1,'old_eight_case_matrix_run':False,'actual_provider_and_serializer':True,'compiler':'MSVC O2 W4 WX','stdout':run.stdout.strip(),'wire':{'path':str(wire),'sha256':hashlib.sha256(wire.read_bytes()).hexdigest()},'files':[{'path':str(x),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in sources+[native/'include/xar_bridge/religion_reform12002_tenet_sources.hpp']],'reused_O2_objects':[{'path':str(x),'sha256':hashlib.sha256(x.read_bytes()).hexdigest()}for x in objects]}
 (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(run.stdout.strip())


if __name__=='__main__':main()

from pathlib import Path
import datetime, hashlib, importlib.util, json, os, shutil, subprocess, sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
RUN=HERE/'build-attempt-02-paused-original-ui-owner';RUN.mkdir(exist_ok=False)
SRC=Path('C:/w/e2research1001')
NATIVE=SRC/'ck3_autonomous_player/native_bridge'
BUILD=RUN/'build'
PY=Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
CMAKE=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin/cmake.exe')
NINJA=CMAKE.parent.parent.parent/'Ninja/ninja.exe'
CTEST=CMAKE.parent/'ctest.exe'
def ident(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def write(n,v):
 with (RUN/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def phase(name,argv,env=None,cwd=NATIVE):
 write(name+'-argv.json',{'argv':argv,'cwd':str(cwd),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 with (RUN/(name+'-stdout.bin')).open('xb') as out,(RUN/(name+'-stderr.bin')).open('xb') as err:
  r=subprocess.run(argv,cwd=cwd,env=env,stdout=out,stderr=err)
 write(name+'-result.json',{'exit_code':r.returncode,'stdout':ident(RUN/(name+'-stdout.bin')),'stderr':ident(RUN/(name+'-stderr.bin'))})
 print(name,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(name+' failed; original attempt preserved')
assert Path(sys.executable).resolve()==PY.resolve()
vcvars=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars64.bat')
env=dict(os.environ);env['CK3_UI_REPAIR_VS_ENV_PATH']=str(RUN/'vs-environment-selected.json')
vscommand='call "'+str(vcvars)+'" && "'+str(PY)+'" -X utf8 "'+str(HERE/'export_vs_environment.py')+'"'
phase('vs-environment',['cmd.exe','/d','/c',str(HERE/'enter_vs_environment_a02.cmd')],env=env)
env.update(json.loads((RUN/'vs-environment-selected.json').read_text(encoding='utf-8')))
env.update(PYTHONUTF8='0',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',VSLANG='1033')
spec=importlib.util.spec_from_file_location('offline_build_fresh',NATIVE/'tools/build_fresh.py')
helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
fingerprint=helper.native_bridge_source_fingerprint(NATIVE)
changed=['ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp','ck3_autonomous_player/native_bridge/src/frontend_gui_route_v1.cpp',
 'ck3_autonomous_player/native_bridge/tests/ingame_ui_navigation_v1_test.cpp',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py',
 'ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py']
before=[ident(SRC/p) for p in changed]
write('source-and-environment.json',{'source_fingerprint_sha256':fingerprint,'modified_source_identities':before,
 'python':ident(PY),'python_version':sys.version,'compiler':ident(Path(shutil.which('cl',path=env['PATH']))),
 'mcp_module_probe':importlib.util.find_spec('mcp').origin,'isolated_worktree_relative_venv':'absent; main worktree interpreter explicitly verified',
 'no_git_game_screen_bus_or_video':True,'vs_environment_selected_keys_only':True})
phase('configure',[str(CMAKE),'-S',str(NATIVE),'-B',str(BUILD),'-G','Ninja','-DCMAKE_BUILD_TYPE=Release',
 '-DXAR_CK3_ENABLE_EXPERIMENTAL_COMBAT_PHASE_TRACE_MANAGED_V1=ON','-DCMAKE_MAKE_PROGRAM='+str(NINJA),
 '-DPython3_EXECUTABLE='+str(PY),'-DXAR_CK3_EXECUTABLE_PATH=C:/SteamLibrary/steamapps/common/CRUSAD~1/binaries/ck3.exe'],env=env)
write('dependency-prefix.json',{'mode':helper.repair_ninja_msvc_dependency_prefix(BUILD,Path(shutil.which('cl',path=env['PATH'])))})
phase('actual-three-tus-and-native-ui-fixture',[str(CMAKE),'--build',str(BUILD),'--parallel','2','--target',
 'CMakeFiles/xar_ck3_bridge.dir/src/frontend_gui_route_v1.cpp.obj',
 'CMakeFiles/xar_ck3_bridge.dir/src/ingame_ui_navigation_v1.cpp.obj',
 'CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj','xar_ck3_ingame_ui_navigation_v1_test'],env=env)
phase('native-ui-ctest',[str(CTEST),'--test-dir',str(BUILD),'-R','^xar_ck3_ingame_ui_navigation_v1_test$',
 '--output-on-failure','--output-junit',str(RUN/'native-ui-ctest-junit.xml')],env=env)
phase('native-ui-fixture',[str(BUILD/'xar_ck3_ingame_ui_navigation_v1_test.exe')],env=env)
phase('python-ui-tests',[str(PY),'-X','utf8','-B','-m','unittest','discover','-s',str(SRC/'ck3_autonomous_player/tests/unit'),
 '-p','test_ingame_ui_navigation_v1.py'],env=env,cwd=SRC)
phase('python-capture-service-tests',[str(PY),'-X','utf8','-B','-m','unittest','discover','-s',str(SRC/'promo/ck3_native_war_ai/integration'),
 '-p','test_capture_hot_service.py'],env=env,cwd=SRC)
after=[ident(SRC/p) for p in changed]
assert before==after and fingerprint==helper.native_bridge_source_fingerprint(NATIVE)
write('actual-offline-receipt.json',{'status':'ACTUAL_THREE_RELEASE_TUS_NATIVE_UI_FIXTURE_PYTHON_UI_CAPTURE_TESTS_PASS',
 'source_fingerprint_sha256':fingerprint,'sources_unchanged_during_validation':True,
 'native_objects':[ident(BUILD/('CMakeFiles/xar_ck3_bridge.dir/src/'+n+'.cpp.obj')) for n in ['frontend_gui_route_v1','ingame_ui_navigation_v1','bridge']],
 'no_full_dll_link_or_game_claim':True,'R0140_RED_preserved':True})

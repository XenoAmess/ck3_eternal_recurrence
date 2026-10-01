from pathlib import Path
import datetime, hashlib, json, os, subprocess, sys
OUT=Path(__file__).parent/'build-attempt-01-original-hidden-modal'
OUT.mkdir(exist_ok=False)
ROOT=Path('C:/w/e2research1001');SOURCE=ROOT/'ck3_autonomous_player/native_bridge'
CMROOT=Path('C:/Program Files/Microsoft Visual Studio/18/Community/Common7/IDE/CommonExtensions/Microsoft/CMake')
CMAKE=CMROOT/'CMake/bin/cmake.exe';CTEST=CMROOT/'CMake/bin/ctest.exe';NINJA=CMROOT/'Ninja/ninja.exe'
BUILD=OUT/'build';PYTHON=Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
def ident(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def write(p,data):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
env=dict(os.environ);env.update(VSLANG='1033',PYTHONUTF8='0',PYTHONIOENCODING='utf-8')
write(OUT/'selected-build-environment.json',{k:env.get(k) for k in ['PATH','INCLUDE','LIB','LIBPATH','VSCMD_ARG_TGT_ARCH','VSCMD_ARG_HOST_ARCH','VSCMD_VER','VSLANG','PYTHONUTF8','PYTHONIOENCODING']})
rels=['include/xar_bridge/ingame_ui_navigation_v1.hpp','src/ingame_ui_navigation_v1.cpp','tests/ingame_ui_navigation_v1_test.cpp','research/ingame_ui_navigation_v1_abi.json','src/frontend_gui_route_v1.cpp','src/bridge.cpp','include/xar_bridge/zhongguo_scoreboard_state_v1.hpp','src/zhongguo_scoreboard_state_v1.cpp','src/zhongguo_scoreboard_action_v1.cpp','src/protocol.cpp','CMakeLists.txt']
before=[ident(SOURCE/r) for r in rels];write(OUT/'sources-before.json',before)
results=[]
def run(name,argv,cwd):
    write(OUT/(name+'-argv.json'),{'argv':[str(x) for x in argv],'cwd':str(cwd),'shell':False,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
    p=subprocess.run([str(x) for x in argv],cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
    for label,body in [('stdout',p.stdout),('stderr',p.stderr)]:
        with (OUT/(name+'-'+label+'.bin')).open('xb') as f:f.write(body)
    result={'name':name,'returncode':p.returncode,'stdout':ident(OUT/(name+'-stdout.bin')),'stderr':ident(OUT/(name+'-stderr.bin'))}
    write(OUT/(name+'-result.json'),result);results.append(result)
    print(json.dumps({'stage':name,'returncode':p.returncode}),flush=True)
    return p.returncode
assert CMAKE.is_file() and CTEST.is_file() and NINJA.is_file() and PYTHON.is_file()
assert Path(sys.executable).resolve()==PYTHON.resolve()
rc=run('cmake-configure',[CMAKE,'-S',SOURCE,'-B',BUILD,'-G','Ninja','-DCMAKE_MAKE_PROGRAM='+str(NINJA),'-DCMAKE_BUILD_TYPE=Release','-DBUILD_TESTING=ON','-DXAR_CK3_EXECUTABLE_PATH=C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe'],SOURCE)
if rc==0:
    rc=run('actual-three-TUs-and-fixture',[CMAKE,'--build',BUILD,'--parallel','2','--target','CMakeFiles/xar_ck3_bridge.dir/src/ingame_ui_navigation_v1.cpp.obj','CMakeFiles/xar_ck3_bridge.dir/src/frontend_gui_route_v1.cpp.obj','CMakeFiles/xar_ck3_bridge.dir/src/bridge.cpp.obj','xar_ck3_ingame_ui_navigation_v1_test'],SOURCE)
if rc==0:
    rc=run('native-UI-CTest',[CTEST,'--test-dir',BUILD,'-R','^xar_ck3_ingame_ui_navigation_v1_test$','--output-on-failure','--output-junit',OUT/'ctest-junit.xml'],SOURCE)
if rc==0:
    rc=run('native-UI-fixture-original-stdout',[BUILD/'xar_ck3_ingame_ui_navigation_v1_test.exe'],SOURCE)
if rc==0:
    pyenv=dict(env);pyenv['PYTHONPATH']=str(ROOT/'ck3_autonomous_player/src');env=pyenv
    rc=run('python-UI-tests',[PYTHON,'-X','utf8','-B','-m','unittest','discover','-s','tests/unit','-p','test_ingame_ui_navigation_v1.py','-v'],ROOT/'ck3_autonomous_player')
after=[ident(SOURCE/r) for r in rels];write(OUT/'sources-after.json',after)
same=before==after
receipt={'schema':'ck3.R0141.original-hidden-modal-build-receipt/v1','status':'ACTUAL_3_RELEASE_TUS_UI_CTEST_FIXTURE_PYTHON_PASS' if rc==0 and same else 'RED','steps':results,'sources_unchanged_during_validation':same,'interpreter':str(sys.executable),'python_version':sys.version,'actual_native_objects':[ident(BUILD/'CMakeFiles/xar_ck3_bridge.dir/src'/name) for name in ['ingame_ui_navigation_v1.cpp.obj','frontend_gui_route_v1.cpp.obj','bridge.cpp.obj'] if (BUILD/'CMakeFiles/xar_ck3_bridge.dir/src'/name).exists()],'full_DLL_linked':False,'new_live_pass_claim':False,'R0141_original_unavailable_preserved':True}
write(OUT/'actual-offline-receipt.json',receipt)
print(json.dumps(ident(OUT/'actual-offline-receipt.json')),flush=True)
sys.exit(0 if rc==0 and same else 2)

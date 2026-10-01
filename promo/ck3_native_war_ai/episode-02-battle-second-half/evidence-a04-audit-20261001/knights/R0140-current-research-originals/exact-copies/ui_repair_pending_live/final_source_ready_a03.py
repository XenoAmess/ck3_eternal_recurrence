from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys
sys.dont_write_bytecode=True
HERE=Path(__file__).parent
SRC=Path('C:/w/e2research1001')
RUN=HERE/'final-python-validation-attempt-04';RUN.mkdir(exist_ok=False)
FREEZE=HERE/'source-freeze-ui-paused-owner-a03';FREEZE.mkdir(exist_ok=False)
PY=Path('D:/workspace/ck3_eternal_recurrence/tools/.venv/Scripts/python.exe')
changed=['ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp','ck3_autonomous_player/native_bridge/src/frontend_gui_route_v1.cpp',
 'ck3_autonomous_player/native_bridge/tests/ingame_ui_navigation_v1_test.cpp',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py','ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py',
 'ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py']
deps=['ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/zhongguo_scoreboard_state_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/main_thread_query_mailbox_v1.cpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/main_thread_query_mailbox_v1.hpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/frontend_gui_route_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/bridge.cpp',
 'ck3_autonomous_player/native_bridge/CMakeLists.txt',
 'promo/ck3_native_war_ai/integration/capture_session.py',
 'promo/ck3_native_war_ai/integration/test_capture_hot_service.py']
def ident(p):
 b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def write(folder,name,v):
 with (folder/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
all_paths=changed+deps
before=[ident(SRC/p) for p in all_paths]
env=dict(os.environ);env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
for name,directory,pattern in [('python-ui-tests',SRC/'ck3_autonomous_player/tests/unit','test_ingame_ui_navigation_v1.py'),
 ('python-capture-service-tests',SRC/'promo/ck3_native_war_ai/integration','test_capture_hot_service.py')]:
 argv=[str(PY),'-X','utf8','-B','-m','unittest','discover','-s',str(directory),'-p',pattern]
 write(RUN,name+'-argv.json',{'argv':argv,'cwd':str(SRC),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 with (RUN/(name+'-stdout.bin')).open('xb') as out,(RUN/(name+'-stderr.bin')).open('xb') as err:
  r=subprocess.run(argv,cwd=SRC,env=env,stdout=out,stderr=err)
 write(RUN,name+'-result.json',{'exit_code':r.returncode,'stdout':ident(RUN/(name+'-stdout.bin')),'stderr':ident(RUN/(name+'-stderr.bin'))})
 print(name,r.returncode,flush=True)
 if r.returncode:raise RuntimeError(name+' failed; preserved')
assert before==[ident(SRC/p) for p in all_paths]
records=[]
for relative in all_paths:
 original=SRC/relative;target=FREEZE/'sources'/relative;target.parent.mkdir(parents=True,exist_ok=True)
 with target.open('xb') as f:f.write(original.read_bytes())
 assert ident(original)['sha256']==ident(target)['sha256']
 records.append({'relative_path':relative,'modified_this_UI_repair':relative in changed,'original':ident(original),'frozen_copy':ident(target)})
native=HERE/'build-attempt-03-paused-original-ui-owner'
native_receipt=json.loads((native/'actual-offline-receipt.json').read_text(encoding='utf-8'))
native_input=json.loads((native/'source-and-environment.json').read_text(encoding='utf-8'))
native_paths=set(changed[:4])
for item in native_input['modified_source_identities']:
 rel=str(Path(item['path']).relative_to(SRC)).replace('\\','/')
 if rel in native_paths:assert ident(Path(item['path']))==item
evidence_files=[native/'actual-offline-receipt.json',native/'actual-three-tus-and-native-ui-fixture-result.json',
 native/'native-ui-ctest-result.json',native/'native-ui-ctest-junit.xml',native/'native-ui-fixture-result.json',
 native/'native-ui-fixture-stdout.bin',HERE/'offline-exact-frontend-branch-attempt-01/exact-source-extraction.json',
 HERE/'offline-exact-frontend-branch-attempt-01/compile-result.json',HERE/'offline-exact-frontend-branch-attempt-01/execute-result.json',
 HERE/'offline-exact-frontend-branch-attempt-01/execute-stdout.bin',RUN/'python-ui-tests-result.json',RUN/'python-ui-tests-stderr.bin',
 RUN/'python-capture-service-tests-result.json',RUN/'python-capture-service-tests-stderr.bin',
 HERE.parent/'R0140-ui-binding-diagnosis-other-a01/readonly-diagnosis-a01.json']
receipt={'schema':'xar.ck3.ui-paused-original-owner-source-ready/v1',
 'status':'SOURCE_READY_FOR_FRESH_FULL_DLL_BUILD_AND_NEW_LIVE_UI_ATTEMPT',
 'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'writable_source':str(SRC),'private_baseline_head_parent_reported':'0bb (not independently queried; no Git used)',
 'sources':records,'native_fingerprint_sha256':native_receipt['source_fingerprint_sha256'],
 'validation':{'three_actual_Release_TUs':['frontend_gui_route_v1.cpp','ingame_ui_navigation_v1.cpp','bridge.cpp'],
 'native_UI_CTest':'PASS 1/1','exact_verbatim_frontend_UI_branch_cases':'PASS 30; original snapshot/GUI/navigation calls are explicit offline stubs',
 'native_UI_fixture':'PASS parser/fullID/RTTI, production paused-owner gateway, RNG0/foreign diagnostic, GUI double-read/replacement negative cases; no game calls',
 'final_Python_UI_MCP_tests':'PASS 24','final_capture_service_tests':'PASS (exact count in stdio)',
 'compiled_native_source_bytes_equal_final_frozen_source':True,'full_DLL_link_and_live_game':'NOT_RUN_BY_THIS_AGENT; root mandatory next step'},
 'evidence':[ident(p) for p in evidence_files],
 'interface_delta':{'tools_and_arguments':'Unchanged seven explicit MCP tools; character33437/killer34120 IDs require each fresh public revision',
 'new_fields':{'application_owner_thread_verified':'bool; actual original SDL/TLS/ticket/thread/paused proof',
 'gui_owner_binding_verified':'bool; actual original current GUI context+owner before/after equal',
 'gui_context_address':'uint64 original singleton-chain context pointer, never caller input',
 'gui_owner_address':'uint64 original singleton-chain owner pointer, never RNG thread',
 'rng_owner_thread_id':'uint32 diagnostic; zero/foreign can coexist with valid UI ownership',
 'rng_owner_is_ui_admission_gate':'always false'},
 'new_UI_dispatch_precondition':'Actual driver state_dir and evidence directory must exist/be creatable before the original UI action is sent.',
 'raw_return_storage':'state_dir/native-session/ingame-ui-native-results/native-ui-<uuid>.json; xb, parsed request/command_result and actual pre-submission snapshot saved before ok/result/UI normalization; no wire byte claim',
 'raw_failure_history':'raw_native_ui_result retained on later identity/session/normalization failure; native RED frame retained in original parsed-return file',
 'metadata':'Date/pause/thread/pump from actual original execution stamp and actor from actual successful fresh snapshot; never from requested expected date.'},
 'guards_preserved':['exact executing ticket/executor/context/state/stop/failure','original event-boundary TLS/current thread and both owner epoch minima',
 'before actual snapshot equals expected; paused map actor and original stamp date','original GUI-chain context/owner fresh double reads before, immediate pre-navigation and after',
 'handler RTTI/vtable/modal/full-ID/actor scope','post native snapshot equals pre; unchanged mailbox post-stamp proof','query/ACK remain pending and non-pixel; actual WGC/manual review still needed'],
 'historical_RED_preserved':['R0140 actual UI date_raw failure/no day advance','build-attempt-01 environment quoting RED',
 'build-attempt-02 3TU compiled PASS but stale-GUI fixture had invalid prior request, CTest RED; corrected explicit fixture request only in attempt03'],
 'no_game_screen_bus_Git_master_video_cloud_changes':True,'all_source_writes_stopped':True,
 'not_proven':['character/knight/full-panel actual UI pixels','live navigation ABI successful execution','death/weapon/event mechanism closure','full DLL linked by this agent']}
target='source-ready-and-test-receipt.json'
write(FREEZE,target,receipt)
print(json.dumps(ident(FREEZE/target),ensure_ascii=False))

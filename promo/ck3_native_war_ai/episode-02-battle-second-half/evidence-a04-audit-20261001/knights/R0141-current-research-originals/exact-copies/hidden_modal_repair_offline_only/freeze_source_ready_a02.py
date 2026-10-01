from pathlib import Path
import datetime,hashlib,json,sys
OUT=Path(__file__).parent
ROOT=Path('C:/w/e2research1001');OLD=Path('C:/w/e2cap1001c')
FREEZE=OUT/'source-freeze-ui-hidden-modal-a02';FREEZE.mkdir(exist_ok=False)
def ident(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def put(p,data):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
BUILD=OUT/'build-attempt-01-original-hidden-modal'
receipt=json.loads((BUILD/'actual-offline-receipt.json').read_text('utf-8'))
assert receipt['status']=='ACTUAL_3_RELEASE_TUS_UI_CTEST_FIXTURE_PYTHON_PASS' and receipt['sources_unchanged_during_validation']
before=json.loads((BUILD/'sources-before.json').read_text('utf-8'))
after=json.loads((BUILD/'sources-after.json').read_text('utf-8'));assert before==after
assert all(ident(Path(i['path']))==i for i in after)
changed=[
 'ck3_autonomous_player/native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp',
 'ck3_autonomous_player/native_bridge/tests/ingame_ui_navigation_v1_test.cpp',
 'ck3_autonomous_player/native_bridge/research/ingame_ui_navigation_v1_abi.json']
dependencies=[
 'ck3_autonomous_player/native_bridge/src/frontend_gui_route_v1.cpp',
 'ck3_autonomous_player/native_bridge/src/bridge.cpp',
 'ck3_autonomous_player/native_bridge/include/xar_bridge/zhongguo_scoreboard_state_v1.hpp',
 'ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_state_v1.cpp',
 'ck3_autonomous_player/native_bridge/src/zhongguo_scoreboard_action_v1.cpp',
 'ck3_autonomous_player/native_bridge/src/protocol.cpp',
 'ck3_autonomous_player/native_bridge/CMakeLists.txt',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py',
 'ck3_autonomous_player/src/xar_autoplayer/bridge/ingame_ui_contract.py',
 'ck3_autonomous_player/tests/unit/test_ingame_ui_navigation_v1.py']
sources=[]
for rel in changed+dependencies:
    p=ROOT/rel;d=FREEZE/'source'/rel;d.parent.mkdir(parents=True,exist_ok=True)
    with d.open('xb') as f:f.write(p.read_bytes())
    current=ident(p);copy=ident(d);original=ident(OLD/rel)
    assert current['sha256']==copy['sha256']
    if rel in dependencies:assert current['sha256']==original['sha256']
    else:assert current['sha256']!=original['sha256']
    sources.append({'relative_path':rel,'changed':rel in changed,'current':current,'frozen_copy':copy,'previous_fda':original,'same_current_copy_bytes':True})
native_stdout=BUILD/'native-UI-fixture-original-stdout-stdout.bin'
text=native_stdout.read_bytes().decode('utf-8',errors='replace')
assert '15 bounded/hidden/visible/mixed/null/unreadable cases and 2 actual serializer checks PASS' in text
python_stderr=BUILD/'python-UI-tests-stderr.bin'
python_text=python_stderr.read_bytes().decode('utf-8',errors='replace').replace('\r\n','\n');assert '\nOK\n' in python_text
record={
 'schema':'ck3.R0141.ui-hidden-modal-source-ready/v1','status':'SOURCE_READY; OFFLINE_ONLY; NEW_FROZEN_FULL_DLL_AND_LIVE_REQUIRED',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'private_source_base':'fda53e7b3e83053f235be3d5725a6238b89db9f0',
 'writable_source':str(ROOT),'source_stopped_writing':True,'four_changed_sources':changed,'sources':sources,
 'diagnosis_receipt':ident(Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/R0141-modal-admission-diagnosis-other-a01/readonly-diagnosis-a01.json')),
 'source_change_intent':ident(OUT/'source-change-intent-a01.json'),
 'verification':{'actual_build_receipt':ident(BUILD/'actual-offline-receipt.json'),'actual_three_TUs_argv':ident(BUILD/'actual-three-TUs-and-fixture-argv.json'),'actual_three_TUs_stdout':ident(BUILD/'actual-three-TUs-and-fixture-stdout.bin'),'actual_three_TUs_stderr':ident(BUILD/'actual-three-TUs-and-fixture-stderr.bin'),'actual_Release_objects':receipt['actual_native_objects'],'CTest_JUnit':ident(BUILD/'ctest-junit.xml'),'native_fixture_original_stdout':ident(native_stdout),'native_fixture_original_stderr':ident(BUILD/'native-UI-fixture-original-stdout-stderr.bin'),'python_UI_stderr':ident(python_stderr),'Python_UI_summary':python_text.splitlines()[-4:],'sources_before':ident(BUILD/'sources-before.json'),'sources_after':ident(BUILD/'sources-after.json'),'all_current_test_bound_sources_match':True},
 'behavior':['Every action including hover/fit shares the same production modal helper after fresh GUI context/owner equality. Query has no modal admission attempt.','Actual signed int32 count 0..256; vector/entries/flags reads bounded and mandatory; repeat header pointer/count equality; refuse any effective-visible receiver, including visible earlier entry with hidden absolute top; all-hidden allowed with no name exception.','Actual original-return modal_admission diagnostics include null count for unread header and raw addresses/flags; native_driver pre-validation create-only persistence unchanged. No new public MCP parameter or arbitrary pointer route.','Existing exact-build/main-thread ticket/native TLS/actual thread/verified paused epochs/date/fullID/played actor/GUI double reads and after equality untouched.','Default source ABI legacy world_guard prose is inherited from the old initial ABI; actual application-owner/RNG-diagnostic implementation is pinned by unchanged frontend and header/fixtures. New modal_admission_revision_v2 documents this modal delta only.'],
 'limits':{'full_DLL_linked_here':False,'new_game_run':False,'live_UI_success':False,'R0141_failed_original_unchanged':True,'R0141_date_advancement':0,'six_items_closed':False,'global_mutable_bundle_complete':False,'producer_path_closed':False,'human_approval_created':False,'video_modified':False,'frozen_e2cap1001c_modified':False,'Git_or_master_action':False},
 'interpreter':str(sys.executable),'script':ident(Path(__file__))
}
target=FREEZE/'source-ready-and-test-receipt.json';put(target,record)
print(json.dumps({'receipt':ident(target),'changed_sources':[{ 'path':s['current']['path'],'bytes':s['current']['bytes'],'sha256':s['current']['sha256']} for s in sources if s['changed']]},ensure_ascii=False))

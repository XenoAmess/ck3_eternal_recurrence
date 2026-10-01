from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

OUT = Path(__file__).parent
LIVE = Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a04')
SRC = Path('C:/w/e2research1001/ck3_autonomous_player')

def identity(p):
    b = p.read_bytes()
    return {'path': str(p).replace('\\','/'), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest().upper()}

def readjson(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def nodes(obj, path='$'):
    yield path,obj
    if isinstance(obj,dict):
        for k,v in obj.items(): yield from nodes(v,path+'/'+k)
    elif isinstance(obj,list):
        for i,v in enumerate(obj): yield from nodes(v,path+'/'+str(i))

response = LIVE/'ck3-output/interactive-requests-responses/before-victim-character-open.json'
original = readjson(response)
hb = original['driver_state']['last_heartbeat']['main_thread_query_mailbox_v1']
before = LIVE/'ck3-output/interactive-requests-responses/before-victim-character-source-snapshot.json'
beforej=readjson(before)
snapshots=[]
for loc,val in nodes(beforej):
    if isinstance(val,dict) and val.get('snapshot_id') and 'native_revision' in val and 'date_raw' in val:
        snapshots.append({'json_path':loc, 'values':{k:val.get(k) for k in ['snapshot_id','revision','native_revision','date_raw','paused','map_ready','episode_run_id']},
                          'played_character':val.get('played_character'),
                          'diagnostics':{k:val.get('diagnostics',{}).get(k) for k in ['bridge_pid','connection_generation']}})

lines=(LIVE/'ck3-output/mcp-calls.jsonl').read_bytes().splitlines()
selected=[]
for i,raw in enumerate(lines,1):
    call=json.loads(raw)
    if call.get('tool')=='ck3_open_character_window_v1':
        selected.append({'line':i,'line_sha256':hashlib.sha256(raw).hexdigest().upper(),'call':call})

sources={name:identity(SRC/p) for name,p in {
    'frontend_cpp':'native_bridge/src/frontend_gui_route_v1.cpp',
    'frontend_hpp':'native_bridge/include/xar_bridge/frontend_gui_route_v1.hpp',
    'mailbox_cpp':'native_bridge/src/main_thread_query_mailbox_v1.cpp',
    'mailbox_hpp':'native_bridge/include/xar_bridge/main_thread_query_mailbox_v1.hpp',
    'ui_cpp':'native_bridge/src/ingame_ui_navigation_v1.cpp',
    'ui_hpp':'native_bridge/include/xar_bridge/ingame_ui_navigation_v1.hpp',
    'gui_cpp':'native_bridge/src/zhongguo_scoreboard_state_v1.cpp',
    'gui_hpp':'native_bridge/include/xar_bridge/zhongguo_scoreboard_state_v1.hpp',
    'bridge_cpp':'native_bridge/src/bridge.cpp',
    'python_contract':'src/xar_autoplayer/bridge/ingame_ui_contract.py',
    'python_driver':'src/xar_autoplayer/bridge/native_driver.py',
}.items()}
assert sources['frontend_cpp']['sha256']=='3CD2E4070C8108A1AE043A86213BC6464815E4DF58EAD93803A140C1DD9ED73D'
assert sources['ui_cpp']['sha256']=='08700667087FC791D8670040F01D91EE40A8E4FB89DB065BA4040F9C845B02C5'
assert sources['bridge_cpp']['sha256']=='CA9687A443FFDBE668F947C7BD3EFC60C1FF08720991BFC3D98698DEB8D80445'
assert hb['rng_owner_tid']==0 and hb['current_tid']==hb['owner_tid']==13000
assert hb['date_raw']==53146848 and hb['paused'] is True
assert hb['published_sequence']==hb['completed_sequence']==hb['executor_started_sequence']==2
assert hb['failure']==0 and hb['consecutive_verified']>=2
assert selected and selected[0]['call']['arguments']=={'character_id':33437,'expected_revision':5}

report={
 'schema':'xar.ck3.r0140-ui-binding-readonly-diagnosis/v1',
 'generated_at':datetime.now(timezone.utc).isoformat(),
 'scope':'Read-only R0140 failure diagnosis; no source, frozen consumer, game, Git, screen, bus or native request changed.',
 'status':'CONCRETE_UI_ADMISSION_CONTRACT_DEFECT; REPAIR_RECOMMENDED_NOT_APPLIED',
 'sources':sources,'actual_evidence':[identity(response),identity(before)],
 'mcp_call_selected_lines':selected,'before_snapshots':snapshots,
 'actual_heartbeat':hb,
 'findings':[
  {'id':'UI-DATE-01','status':'CONFIRMED_FROM_ACTUAL_VALUES_AND_SOURCE',
   'source_locator':'frontend_gui_route_v1.cpp:635-645',
   'claim':'UI-specific admission requires rng_owner_thread_id==thread_id. R0140 observes 0 versus 13000; this necessary condition is false and the branch cannot reach ExecuteIngameUiNavigationV1.',
   'evidence_limit':'Heartbeat observed at failed-call envelope follows executor pump23345 by one pump; no per-ticket raw result or exact execution stamp survives in this envelope. The necessary false condition is demonstrated by original observations and exact source; wire unavailable_reason is reconstructed, not directly read back.'},
  {'id':'UI-DATE-02','status':'CONFIRMED_STATIC_CONTROL_FLOW',
   'source_locator':'frontend_gui_route_v1.cpp:644-645; ingame_ui_navigation_v1.cpp:454-455,553-564; ingame_ui_contract.py:28-37',
   'claim':'The early branch writes only owner_fresh_snapshot_admission_failed into default IngameUiResult. It leaves date_raw0/pausedfalse/played_character-1/pump0/thread0. Bridge serializes completed unavailable result; strict Python identity comparison encounters date_raw first and hides original unavailable reason.',
   'no_default_fill':'Do not fill date from requested/expected snapshot. Any response metadata must come from the actual admitted execution stamp and an actual successful fresh snapshot.'},
  {'id':'UI-OWNER-03','status':'CONFIRMED_STATIC_CONTRACT_CONFLICT',
   'source_locator':'main_thread_query_mailbox_v1.hpp:44-58; main_thread_query_mailbox_v1.cpp:245-262,322-357; frontend_gui_route_v1.cpp:31-55,635-645',
   'claim':'Global RNG wrapper is a subsystem-scoped diagnostic, explicitly excluded from application main-thread admission. The added UI gate wrongly requires diagnostic wrapper/state/owner availability/equality despite existing original application event boundary and TLS proof.'},
  {'id':'UI-EVIDENCE-04','status':'LIMITATION',
   'claim':'Original failing MCP envelope records error, driver heartbeat and command history, but no raw native command_result body. Keep original R0140 RED. Add raw-result preservation on future validation failure rather than rewriting this attempt.'}
 ],
 'minimal_repair_recommendation':{
  'replace_only_ui_rng_gate':'Keep RNG wrapper/state/owner as diagnostics; replace their ingame UI admission requirement with explicit current original GUI context/owner binding. Do not change simulation/trace RNG contracts.',
  'application_owner_proof_to_keep':['exact-build SDL dispatch/IAT anchors and original return address whitelist','native TLS initialized=1 and main-thread marker=1','GetCurrentThreadId()==stamp.thread_id==mailbox.owner_thread_id','exact executing ticket/executor/context and failure/stop flags','at least two independently verified application owner and paused owner epochs'],
  'gui_object_owner_binding':'ResolveZhongguoScoreboardNativeGuiContextAndOwnerV1 on the proven application thread before invocation; original GUI global RVA576CC68 -> first+1B8 -> second+58 => context; context+3D0 -> host+08 => owner. Re-read both before/after and require identical non-null current context/owner. This owner is an object pointer, never an RNG thread ID.',
  'existing_business_guards_to_keep':['fresh actual snapshot equals expected snapshot','paused/map_ready/played actor and date_raw equals actual execution stamp','exact IngameHandler RTTI/vtable and live modal count','original full CharacterID/ArmyID/CombatID joins and actor scope','post snapshot equals pre snapshot; mailbox post stamp unchanged','fresh downstream query and explicit original WGC/manual review remain required'],
  'failure_reporting':'Retain structured unavailable reason and actual raw native result on future failure. Metadata from actual stamp/fresh read only; any failed binding still fails. No expected date substitution.',
  'next_validation':['pure offline original gate reproduces 0 versus13000 rejection','zero or foreign RNG owner may be admitted only with all independent native UI owner/paused/GUI gates satisfied','negative TLS/ticket/current thread/paused epoch/GUI replacement/stale snapshot must fail before dispatch','actual Release full-DLL build required','new live attempt required for real role UI readback/pixels; do not retry ambiguous action in R0140']
 },
 'not_claimed':['exact per-ticket raw unavailable_reason readback','successful character UI dispatch','any day advance','knight roster/full battle panel pixels','mechanism causality closure'],
 'source_writes':False,'live_operations':False,
}
target=OUT/'readonly-diagnosis-a01.json'
with target.open('x',encoding='utf-8',newline='\n') as f:
    json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(identity(target),ensure_ascii=False))

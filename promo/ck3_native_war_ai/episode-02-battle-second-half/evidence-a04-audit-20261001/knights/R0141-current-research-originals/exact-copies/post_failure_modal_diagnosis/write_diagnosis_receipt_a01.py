from pathlib import Path
import datetime, hashlib, json, subprocess
OUT=Path(__file__).parent
def identity(p):
    b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest().upper()}
def exactcopy(p,relative):
    d=OUT/relative;d.parent.mkdir(parents=True,exist_ok=True)
    with d.open('xb') as f:f.write(p.read_bytes())
    original=identity(p);copy=identity(d);assert original['sha256']==copy['sha256']
    return {'original':original,'copy':copy,'same_bytes':True}
rpm_path=OUT/'readonly-modal-receivers-a01.json';rpm=json.loads(rpm_path.read_text('utf-8'))
static_path=OUT/'static-modal-anchors-a01.json';static=json.loads(static_path.read_text('utf-8'))
assert rpm['status']=='READONLY_CURRENT_MEMORY_CAPTURED' and rpm['two_passes_stable']
run=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a05')
raw=Path(rpm['raw_parsed_native_result']['path'])
copies=[exactcopy(raw,'actual-parsed-return-exact-copy.json')]
diagnostic=run/'scoped-ui-research-attempt-01/modal-rejection-diagnostic.json'
if diagnostic.exists():copies.append(exactcopy(diagnostic,'root-modal-rejection-diagnostic-exact-copy.json'))
gui_root=Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/game/gui')
argv=['rg','-n','-F','JominiMultiplayerEndPreparationConfirmation',str(gui_root)]
process=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=False)
for name,content in [('stock-gui-rg-stdout.bin',process.stdout),('stock-gui-rg-stderr.bin',process.stderr)]:
    with (OUT/name).open('xb') as f:f.write(content)
rg_receipt={'argv':argv,'shell':False,'returncode':process.returncode,'stdout':identity(OUT/'stock-gui-rg-stdout.bin'),'stderr':identity(OUT/'stock-gui-rg-stderr.bin')}
first=rpm['passes'][0]
report={
 'schema':'ck3.R0141.modal-admission-readonly-diagnosis/v1',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'source_private_commit':'fda53e7b3e83053f235be3d5725a6238b89db9f0',
 'status':'CONCRETE_CURRENT_MODAL_VECTOR_MISCLASSIFICATION; SOURCE_FIX_NOT_APPLIED',
 'scope':{'game_api_called':False,'native_function_invoked':False,'process_write':False,'desktop_or_input':False,'game_day_command':False,'source_modified':False,'git_modified':False,'approval_or_signoff_created':False},
 'existing_MCP_diagnostic_gap':{
   'registered_scoreboard_query':{'name':'ck3_query_zhongguo_scoreboard_state_v1','signature':'request_nonce: str, expected_revision: int'},
   'reason_not_invoked':'Public scoreboard DTO/serializer expose widgets, ACL, actions, readiness and semantic fingerprints. Actual modal count, vector entries and receiver addresses are not public fields. +0x290/+0x29C appear only as provenance offset strings. Fixed mod-specific allowlist cannot be substituted for the requested global modal diagnostic.',
   'other_queries':'query_ingame_ui_window_v1 and ck3_inspect_frontend_gui_tree_v1 do not publish global modal count/vector. Local callable ALL_TOOLS CK3 GUI inventory was empty; source registry is authoritative for root SDK calls.',
   'source_anchors':[
     'native_bridge/src/zhongguo_scoreboard_state_v1_serializer.cpp:304-407 public serialization',
     'native_bridge/src/zhongguo_scoreboard_state_v1.cpp:844-889 fixed-widget scope',
     'native_bridge/src/zhongguo_scoreboard_state_v1.cpp:1363-1394 modal relation independent fingerprint input; modal_blocking explicitly unfrozen',
     'src/xar_autoplayer/bridge/mcp_server.py:2037-2047 registered call signature'
   ]
 },
 'original_action_actual_return':rpm['original_failed_action_fields'],
 'actual_current_RPM':{
   'evidence':identity(rpm_path),'PID':rpm['pid'],'process_creation_filetime_100ns':rpm['process_creation_filetime_100ns'],'actual_executable':rpm['actual_process_executable'],'actual_module':rpm['actual_main_module'],
   'process_access':rpm['process_access'],'total_RPM_bytes':rpm['total_RPM_bytes'],'raw_read_records':len(rpm['reads']),
   'two_passes_stable':True,'matches_original_action_GUI_context_and_owner':True,
   'context':first['context'],'owner':first['owner'],'vector_data':first['modal_vector_data_address'],'count_int32':first['modal_receiver_count_int32_at_29C'],
   'receivers':first['receivers'],
   'temporal_limit':'These are two later readonly process-memory observations. The original failed native return did not serialize the count/vector; the RPM must not be labelled its exact execution-time wire evidence. No fresh game snapshot/date/pause was read by this RPM.'
 },
 'exact_original_static_anchors':{
   'evidence':identity(static_path),'executable_sha256':static['executable']['sha256'],
   'DefaultOnCharacterClick':{'span':'RVA 0xA04530..0xA045D9','bytes':169,'observation':'No +0x29C modal-count condition within this original function. Full CharacterID lookup and handler-mode routing then tail-call 0xA7EFA0 or 0xA78BB0. This does not prove all downstream functions lack independent modal policy.'},
   'NativeShortcutManagerActivate':{'span':'RVA 0x36E1C40..0x36E1D35','bytes':245,'observations':['0x36E1C70: signed count from GUI context+0x29C.','0x36E1C80: vector data from context+0x290.','0x36E1C90..0x36E1CA6: reverse scan each receiver+D0 effective-hidden bit08; if all hidden, proceeds directly to 0x36E1CB9.','If any receiver is effective-visible, 0x36E1CAB takes absolute vector[count-1] and invokes original StrictDescendant 0x369E620. It does not equate every registered receiver to a visible blocking modal.']},
   'existing_exact_build_bridge_match':'zhongguo_scoreboard_action_v1.cpp:189-223 reproduces original count bounds/vector reads/effective-hidden scan/absolute-top descendant condition.'
 },
 'current_source_error':{
   'path':'C:/w/e2cap1001c/ck3_autonomous_player/native_bridge/src/ingame_ui_navigation_v1.cpp',
   'sha256':'E3897DB2839882C7D3D9A03280F6EEEA73F8B427EAAD55627ECBAE659AB8E29B',
   'lines':'497-502',
   'actual_rule':'Reject any uint32 modal_count != 0, without examining original vector or receiver effective visibility.',
   'why_wrong':'Current stable count1 consists solely of an effective-hidden CPdxGuiWidget named JominiMultiplayerEndPreparationConfirmation (raw D0=B8; bit08 set). Original native shortcut routing allows an all-hidden vector. Existing docs also explicitly leave generic modal_blocking unfrozen.',
   'original_call_cause_confidence':'Strong source + matching current-memory inference; original execution-time count/read-success was not emitted. Other branches sharing modal_context_blocks_navigation were resolver failure, pointer drift and failed Value read.'
 },
 'minimal_defensible_followup':[
   'Retain exact build, fresh snapshots, same paused date/full IDs, application owner/TLS/ticket/thread epochs and GUI context/owner binding.',
   'Read original signed int32 count, bounded 0..256, and vector pointer; reject failed reads, negative/excessive count, missing data/non-null entries and invalid flag reads.',
   'For global typed navigation conservatively reject ANY effective-visible receiver (D0 bit08 clear). Permit count0 or a fully validated all-hidden vector. This is more restrictive than native descendant allowance and needs no arbitrary target or exception by widget name.',
   'Re-read current GUI context/owner and bounded vector/flags immediately at action admission; preserve actual diagnostic reason/count/addresses/flags in the existing create-only parsed native result. Do not substitute expected/default values for reads.',
   'Meaningful offline cases: hidden-count1 eligible; zero eligible; visible-count1 refused; mixed visible/hidden refused even when absolute top is hidden; negative/count257/vector missing/entry missing/read failure refused; current context/owner drift refused.',
   'Source change requires parent authorization and new freeze/build/run. Preserve R0141 unavailable, no-day state and all original inputs; no resend into current run.'
 ],
 'still_unproven':['Exact execution-time modal header/entry fields of the already-failed call.','Hidden receiver registration/unregistration lifecycle or why it remains in the vector.','Successful character/army/combat/knights/fit/hover live postconditions.','Six-item mechanism/UI closure; global_mutable_bundle_complete remains false.'],
 'stock_gui_search':rg_receipt,'exact_copies':copies,'machine_read_does_not_equal_human_review':True,
 'script':identity(Path(__file__))
}
dest=OUT/'readonly-diagnosis-a01.json'
with dest.open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':identity(dest),'stock_gui_search':{'rc':process.returncode,'stdout':process.stdout.decode('utf-8',errors='backslashreplace')[:5000]},'count':report['actual_current_RPM']['count_int32']},ensure_ascii=False))

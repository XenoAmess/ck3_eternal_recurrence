"""Append actual normal-exit RED and model both sides of the same production brace bug."""
from pathlib import Path
import hashlib,json,re
OUT=Path(__file__).resolve().parent
def ref(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def need(ok,message):
 if not ok:raise ValueError(message)
def put(name,value):
 p=OUT/name;b=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
 with p.open('xb') as f:f.write(b)
 return ref(p)
basis=(OUT/'author_minimal_candidate.py').read_text(encoding='utf-8')
basis=basis.replace('  start=i;line=lines[i]\n',"  parent=all(s['active'] for s in stack)\n  start=i;line=lines[i]\n",1)
ns={'__name__':'source_model_import_only','__file__':str(OUT/'author_minimal_candidate.py')}
exec(compile(basis,str(OUT/'author_minimal_candidate.py'),'exec'),ns)
original=ns['SOURCE'].read_text(encoding='utf-8');candidate=(OUT/'bridge.cpp.candidate').read_text(encoding='utf-8')
oldproof=json.loads((OUT/'OFFLINE-BRACE-MODEL.actual.json').read_bytes())
enabled=set(oldproof['actual_flags_on'])
op,oc=ns['brace_graph'](ns['active_source'](original,enabled));cp,cc=ns['brace_graph'](ns['active_source'](candidate,enabled))
need(op[22730]==14775 and cp[22729]==20143,'Actual active wrong/fixed attachment required')
checks=[]
def model(parent,handled):
 # Conditions of the segment3 query chain and the AI-owned step are false for
 # both select-event-option-3 and normal-exit-map-v1. Use parsed production
 # brace attachment to decide which if owns the fallback reset.
 attached_inside=parent in {20143}
 marker=handled
 if not marker:
  marker=True
  if attached_inside:marker=False
 elif not attached_inside:
  marker=False
 # All later query/battle branches are nonmatches for these two exact steps.
 tail_reached=not marker
 return {'handled_after_segment3':marker,'tail_reached':tail_reached,'response_site_count':int(handled)+int(tail_reached)}
cases=[('original_unmatched_event',op[22730],False,False,0),('candidate_unmatched_event',cp[22729],False,True,1),
       ('original_already_handled_normal_exit',op[22730],True,True,2),('candidate_already_handled_normal_exit',cp[22729],True,False,1)]
for label,parent,handled,tail,count in cases:
 actual=model(parent,handled)
 for key,expected in [('tail_reached',tail),('response_site_count',count)]:
  need(actual[key]==expected,label+': '+key);checks.append({'case':label,'check':key,'expected':expected,'actual':actual[key],'passed':True})
proof=put('NORMAL-EXIT-FALLTHROUGH-MODEL.actual.json',{'status':'PASS_SOURCE_CONTROL_FLOW_MODEL_ONLY','checks':checks,'passed':len(checks),
 'basis_source':ref(ns['SOURCE']),'candidate_source':ref(OUT/'bridge.cpp.candidate'),'existing_patch':ref(OUT/'CANDIDATE.incremental.patch'),
 'actual_enabled_flags':sorted(enabled),'actual_native_callbacks_executed':0,'C++_compiled':False,'extra_production_hunks_needed':False})
client=Path('C:/workspace/ck3_lyd_runtime_20261004/live-attempt-017/mcp-client-001')
normal=client/'0024-r17-026-normal-exit-confirm-desktop.native-01.json'
observe=client/'0025-r17-027-normal-exit-observe.native-01.json'
n=json.loads(normal.read_bytes());o=json.loads(observe.read_bytes());nr=n['result'];orr=o['result']
need('unsupported native gameplay step' in nr['reason'] and nr['typed_normal_exit_observed'] is False and nr['native_observation'] is None,'Actual terminal reply RED required')
need(orr['process_exit_observed'] is True and orr['exit_code']==0 and orr['typed_normal_exit_observed'] is False and orr['native_observation'] is None and orr['autosave_verified'] is False,'Exact original HANDLE exit0 with typed response still false required')
driver=Path('C:/lr17s1/ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py')
drivertext=driver.read_text(encoding='utf-8');need('self._command_results[request_id] = dict(frame)' in drivertext,'Actual response map assignment required')
rawrefs=[ref(p) for p in sorted(client.iterdir()) if p.name.startswith(('0024-','0025-')) and ('.native-01.json' in p.name or '.sdk-result.json' in p.name)]
append=put('NORMAL-EXIT-APPENDIX.INDEX.json',{'status':'ACTUAL_TERMINAL_REPLY_RED_SAME_BRACE_DEFECT_SOURCE_FIX_ONLY','original_candidate_index':ref(OUT/'INDEX.json'),
 'source_model':proof,'actual_receipts':rawrefs,'actual_qualified_native_normal_exit':False,'actual_native_normal_exit_observation':None,
 'actual_game_original_handle_exit0':True,'actual_autosave_verified':False,'extra_production_patch':None,
 'response_overwrite_source':ref(driver),'response_overwrite_line':1026,'response_wait_pop_line':1213,
 'actual_raw_pipe_two_frame_log':None,'cause':'Premature outer segment3 closure resets an already handled command to unhandled, allowing a second unsupported tail response. The same request-ID map may overwrite the earlier response before the waiter consumes it.',
 'closure_scope':'Game exit0 observed, but Client/keeper/CAS closure is not inferred here. Original qualified/native null states remain unchanged.',
 'native_builds':0,'SDK_calls':0,'game_calls':0,'bus_calls':0,'main_writes':0})
print(json.dumps({'appendix':append,'new_source_model':proof,'checks_passed':len(checks),'existing_patch_unchanged':ref(OUT/'CANDIDATE.incremental.patch'),'extra_production_patch':None}))

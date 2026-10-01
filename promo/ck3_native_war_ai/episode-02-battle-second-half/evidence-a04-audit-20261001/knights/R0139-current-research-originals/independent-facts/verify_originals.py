from __future__ import annotations
import hashlib,importlib.util,json,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
OUT=Path(__file__).resolve().parent
ROOT=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a02')
PAIR=ROOT/'research-pair-attempt-02'
SRC=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001/reinforcement-attempt-12-R0129-native-center-diagnostic/source')
RAKALY=Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-effect-save-attempt-008/rakaly-0.8.19-x86_64-pc-windows-msvc/rakaly.exe')
PARSER=SRC/'ck3_autonomous_player/tools/project_native_phase_event_save_feedback.py'
def ident(p):
 p=Path(p).resolve()
 with p.open('rb') as f:s=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return {'path':str(p),'bytes':p.stat().st_size,'sha256':s}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(p,v):
 with Path(p).open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
checks=[]
def gate(name,condition):
 checks.append({'name':name,'pass':bool(condition)})
 if not condition:raise ValueError(name)
def bound(row):
 p=Path(row['path']).resolve();got=ident(p)
 gate('exact bytes '+str(p),got['bytes']==row['bytes'] and got['sha256']==row['sha256'].upper());return p
receipt={'schema':'ck3.R0139.knight-readonly-facts.v1','created_at_utc':datetime.now(timezone.utc).isoformat(),'source_head':'1901473429deb1297be7d5d4451169082629858b','ck3_launches':0,'desktop_inputs':0,'master_intake':False,'status':'UNKNOWN','limits':{'old_a02_closed':False,'sole_cause_proven':False,'full_mutable_bundle_proven':False,'character_ui_proven':False,'full_battle_panel_proven':False}}
try:
 before=read(PAIR/'before-pair.json');after=read(PAIR/'after-pair.json')
 gate('same new episode run',before['episode_run_id']==after['episode_run_id'])
 receipt['episode_run_id']=before['episode_run_id'];receipt['pair_originals']=[ident(PAIR/'before-pair.json'),ident(PAIR/'after-pair.json')]
 binding=before['source_binding']
 gate('source exact head190',binding['source_head']==receipt['source_head'])
 for item in binding['declared_pins']:bound(item)
 for key in ('preflight','readback'):bound(binding[key])
 gate('new live R0139',binding['live_identity']['identities'][0]['sequence']==139)
 receipt['run_id']=binding['live_identity']['identities'][0]['run_id']
 tf=ROOT/'ck3-output/interactive-requests-responses/knight-new-trace-finish.json';tr=read(tf)
 gate('native trace call completed',tr['result']=='CALL_COMPLETED' and tr['body']['accepted'] is True)
 trace=tr['body']['managed_trace']['trace'];checkpoint=tr['body']['managed_trace']['managed_checkpoint'];receipt['trace_original']=ident(tf)
 gate('trace status captured flags0',trace['status']=='captured' and trace['failure_flags']==0)
 gate('all seven boundary flags0',trace['record_count']==7 and len(trace['records'])==7 and all(r['capture_failure_flags']==0 for r in trace['records']))
 gate('native exactly one day',checkpoint['exact_one_day_observed'] is True and checkpoint['after']['date_raw']-checkpoint['before']['date_raw']==24 and checkpoint['before']['date_raw']==53146848 and checkpoint['after']['date_raw']==53146872)
 gate('same token thread combat',all(checkpoint['before'][k]==checkpoint['after'][k] for k in ('managed_daily_sequence_token','thread_id','combat_id')))
 gate('paused checkpoint+uninstalled',checkpoint['before']['paused'] and checkpoint['after']['paused'] and checkpoint['detours_uninstalled'])
 gate('global full bundle stays false',trace['readiness']['full_mutable_transition_bundle_complete'] is False and all(r['full_mutable_transition_bundle_complete'] is False for r in trace['records']))
 receipt['managed_checkpoint']=checkpoint;receipt['trace_readiness']=trace['readiness']
 receipt['native_trace_nonrecord_fields']={k:v for k,v in trace.items() if k!='records'}
 receipt['boundaries']=[]
 for r in trace['records']:
  receipt['boundaries'].append({'boundary':r['boundary'],'capture_failure_flags':r['capture_failure_flags'],'date_raw':r['native_date_raw'],'phase_day':r['phase_day'],'characters':[c for c in r.get('characters',[]) if c.get('character_id') in (33437,34120)],'side1_knights':r['sides'][1]['knights'],'side1_scheduled_knights':r['sides'][1]['scheduled_knights'],'battle_events':r.get('battle_events',[])})
 gate('pinned Rakaly',ident(RAKALY)['sha256']=='E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D')
 gate('pinned source parser',ident(PARSER)['sha256']=='E80A2C025584528766B4C4BB73C8696B39525FCA52F27454B1FB26C9B4B52F30')
 spec=importlib.util.spec_from_file_location('frozen_save_parser_R0139',PARSER);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 receipt['saved_states']=[]
 connections=[]
 for label,pair,date in [('before',before,53146848),('after',after,53146872)]:
  raw=bound(pair['immutable']);savepath=bound(pair['save']);save=read(savepath)
  b=save['body'];ck=b['checkpoint']
  gate(label+' native saved same episode actor date bytes',save['result']=='CALL_COMPLETED' and b['accepted'] is True and ck['status']=='saved' and ck['episode_run_id']==before['episode_run_id'] and ck['episode_character_id']==29829 and ck['date_raw']==date and ck['size']==raw.stat().st_size and ck['sha256'].upper()==ident(raw)['sha256'])
  request=Path(save['request']['path']);gate(label+' request below same root',request.resolve().is_relative_to(ROOT.resolve()))
  req=read(request);gate(label+' revision bound',req['tool']=='ck3_save_checkpoint' and req['arguments']['expected_revision']==read(bound(pair['snapshot']))['body']['revision'])
  d=save['driver_state'];connections.append(tuple(d[k] for k in ('pipe_name','connection_generation','bridge_pid')))
  melted=OUT/(label+'-melted.ck3');argv=[str(RAKALY),'melt',str(raw),'--unknown-key','stringify','--format','ck3','--out',str(melted)]
  write(OUT/(label+'-melt-command.json'),{'argv':argv,'raw':ident(raw),'rakaly':ident(RAKALY)})
  with (OUT/(label+'-melt.stdout.log')).open('xb') as stdout,(OUT/(label+'-melt.stderr.log')).open('xb')as stderr:proc=subprocess.run(argv,stdout=stdout,stderr=stderr,check=False)
  write(OUT/(label+'-melt-process.json'),{'returncode':proc.returncode,'stdout':ident(OUT/(label+'-melt.stdout.log')),'stderr':ident(OUT/(label+'-melt.stderr.log'))})
  gate(label+' actual Rakaly exit0',proc.returncode==0 and melted.is_file())
  states=[]
  text=melted.read_text(encoding='utf-8-sig')
  for character_id in (33437,34120):
   s=module._character_snapshot(text,character_id)
   gate(label+' unique life blocks '+str(character_id),type(s['alive_data_present'])is bool and type(s['dead_data_present'])is bool and s['alive_data_present']!=s['dead_data_present'])
   states.append(s)
  receipt['saved_states'].append({'label':label,'raw':ident(raw),'melted':ident(melted),'native_save_receipt':ident(savepath),'request':ident(request),'characters':states})
 gate('same native connection before after',len(set(connections))==1)
 receipt['native_connection']=connections[0]
 b,a=[s['characters'][0] for s in receipt['saved_states']]
 gate('33437 ALIVE regiment65 to DEAD',b['alive_data_present'] and not b['dead_data_present'] and b['regiment_id']==65 and a['dead_data_present'] and not a['alive_data_present'])
 gate('actual saved death case identity',a['death_date']=='1066.12.30' and a['death_reason']=='death_battle' and a['killer_character_id']==34120 and a['regiment_id'] is None)
 receipt['parser']=ident(PARSER);receipt['rakaly']=ident(RAKALY);receipt['status']='PASS_SCOPED_SAME_RUN_TRACE_AND_SAVED_STATES'
except Exception as exc:receipt['error']=f'{type(exc).__name__}: {exc}'
receipt['checks']=checks
write(OUT/'R0139-readonly-facts-a01.json',receipt)
print(json.dumps({'status':receipt['status'],'error':receipt.get('error'),'trace_keys':list(receipt.get('native_trace_nonrecord_fields',{})),'checks':len(checks),'receipt':ident(OUT/'R0139-readonly-facts-a01.json')},ensure_ascii=False))
raise SystemExit(0 if receipt['status'].startswith('PASS') else 2)

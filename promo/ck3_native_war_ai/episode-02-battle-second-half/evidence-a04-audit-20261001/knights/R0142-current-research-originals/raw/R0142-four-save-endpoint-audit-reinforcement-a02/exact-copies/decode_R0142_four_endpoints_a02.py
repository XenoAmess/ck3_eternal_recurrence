"""R0142 saved endpoints only; no original trace substitutes or native requests."""
from pathlib import Path
import collections,hashlib,importlib.util,json,re,subprocess,sys,datetime
BASE=Path('C:/Users/1/ck3-a04-mechanism-evidence-20261001')
OUT=BASE/'R0142-four-save-endpoint-audit-reinforcement-a01'
LIVE=Path('C:/Users/1/AppData/Local/ck3-capture-preparation/episode02-e2-05-d26-six-gap-ui-live-20261001-a06')
PAIR=LIVE/'scoped-ui-research-attempt-01'
ROOT=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-06-hidden-modal-ui')
RUNTIME=Path('C:/w/e2cap1001d')
RAKALY=Path('D:/workspace/ck3_native_war_ai_promo_work/episode01-effect-save-attempt-008/rakaly-0.8.19-x86_64-pc-windows-msvc/rakaly.exe')
RAKALY_SHA='E154AF990AAED2C2F44284946772188C9749AD3F6B641B41F6C23456A6F1633D'
LABELS=['before-pre-ui-checkpoint','before','after-pre-ui-checkpoint','after']
def ident(p):
 p=Path(p).resolve()
 with p.open('rb')as f:d=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return{'path':str(p),'bytes':p.stat().st_size,'sha256':d}
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,v):
 p=OUT/name
 with p.open('x',encoding='utf-8',newline='\n')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 return ident(p)
def checked(pin):
 p=Path(pin['path']);got=ident(p)
 if got['bytes']!=pin['bytes']or got['sha256']!=pin['sha256'].upper():raise ValueError('Original pinned bytes changed: '+str(p))
 return p
def freeze(p,name):
 p=Path(p);before=ident(p);out=OUT/'exact-copies'/name;out.parent.mkdir(parents=True,exist_ok=True)
 with p.open('rb')as i,out.open('xb')as o:
  while b:=i.read(1048576):o.write(b)
 assert ident(p)==before and ident(out)['sha256']==before['sha256']
 return{'original':before,'copy':ident(out)}
def process(label,argv):
 write(label+'-argv.json',{'argv':argv,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
 with(OUT/(label+'.stdout.bin')).open('xb')as o,(OUT/(label+'.stderr.bin')).open('xb')as e:r=subprocess.run(argv,stdout=o,stderr=e,check=False)
 result={'argv':argv,'exit_code':r.returncode,'stdout':ident(OUT/(label+'.stdout.bin')),'stderr':ident(OUT/(label+'.stderr.bin'))}
 write(label+'-process.json',result)
 return result
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
 sys.stdout.reconfigure(encoding='utf-8');sys.dont_write_bytecode=True
 (OUT/'exact-copies').mkdir(exist_ok=True)
 report={'kind':'R0142_FOUR_ORIGINAL_SAVED_ENDPOINTS_ONLY','status':'PENDING','checks':[],'runtime_trace_available':False,'monitor_complete':False,'global_bundle_complete':False,'case_13_domain_complete':False,'sole_death_cause_proven':False}
 def gate(n,v):
  report['checks'].append({'name':n,'pass':bool(v)})
  if not v:raise ValueError(n)
 try:
  config_path=ROOT/'current-run-bindings.json';config=read(config_path);cpin=ident(config_path)
  report['configuration']=freeze(config_path,'current-run-bindings.json')
  report['configuration_pins']=[ident(checked(pin))for pin in config['pins']]
  gate('Runtime explicitly4ad, R0142, current live only',config['source_commit']=='4ad477ee33e15a93e412f711c7b05b216a2e6651' and str(LIVE.resolve())==str(Path(config['live_root']).resolve()) and config['run_id'].endswith('R0142'))
  report['runtime_source_head']=config['source_commit'];report['runtime_dll']=ident(Path(config['bridge_dll']))
  parser_path=RUNTIME/'ck3_autonomous_player/src/xar_autoplayer/simulation/knight_causal_save_projection.py'
  selector_path=parser_path.with_name('knight_selector_replay.py')
  report['parser_sources']=[freeze(parser_path,'knight_causal_save_projection.py'),freeze(selector_path,'knight_selector_replay.py')]
  sys.path.insert(0,str(RUNTIME/'ck3_autonomous_player/src'))
  from xar_autoplayer.simulation.knight_causal_save_projection import character_snapshot,parse_block,block_body,extract_exact_indented_block,find_key_blocks,delta,one
  rng_path=BASE/'knight-selector-causality-research-attempt-01/saved_rng_endpoint_inventory_a01.py'
  report['rng_reader_source']=freeze(rng_path,'saved_rng_endpoint_inventory_a01.py')
  rngreader=load('R0142_saved_rng_endpoint_reader',rng_path)
  gate('Pinned actual Rakaly executable',ident(RAKALY)['sha256']==RAKALY_SHA)
  report['rakaly']=freeze(RAKALY,'rakaly.exe')
  report['interpreter']={'path':sys.executable,'version':sys.version,'probe':process('verified-python',[sys.executable,'-X','utf8=0','-B','--version'])}
  copies=[];states=[];connections=[]
  for index,label in enumerate(LABELS):
   path=PAIR/(label+'-saved-pair.json');pair=read(path);sv=pair['source_values'];date=config['before_date_raw']if index<2 else config['after_date_raw']
   copies.append(freeze(path,label+'-saved-pair.json'))
   gate(label+' exactsourcebinding',pair['source_binding']==cpin)
   raw=checked(pair['immutable']);gate(label+' immutable current-slotpath',raw.resolve()==(PAIR/(label+'-immutable.ck3')).resolve())
   receipt_path=checked(pair['save']['response']);receipt=read(receipt_path);snap_path=checked(pair['snapshot']['response']);snap=read(snap_path);sbody=snap['body']
   request_path=checked(pair['save']['request']);request=read(request_path)
   gate(label+' original save nativeaccepted/saved',receipt['result']=='CALL_COMPLETED'and receipt['body']['accepted']is True and receipt['body']['checkpoint']['status']=='saved'and pair['save_body']==receipt['body'])
   save=receipt['body']['checkpoint']
   gate(label+' actual raw saved receiptSHA/date/actor/session',save['size']==ident(raw)['bytes']and save['sha256'].upper()==ident(raw)['sha256']and save['date_raw']==date and save['episode_character_id']==config['actor_id']and save['episode_run_id']==config['native_session_binding']['episode_run_id'])
   gate(label+' pausedsourceactualsnapshot',snap['result']=='CALL_COMPLETED'and sv['date_raw']==sbody['date_raw']==date and sv['paused']is True and sbody['paused']is True and sv['actor']==sbody['played_character']['character_id']==config['actor_id']and all(sv[k]==sbody[k]for k in ['revision','native_revision','snapshot_id']))
   gate(label+' source Army18combat actualsnapshot',sv['army_id']==config['public_unit_id']and sv['army_state']=='combat'and any(a['army_id']==config['public_unit_id']and a['state']=='combat'for a in sbody['player_armies']))
   gate(label+' native save request revision',request['tool']=='ck3_save_checkpoint'and request['arguments']['expected_revision']==sbody['revision'])
   conn=tuple(receipt['driver_state'][k]for k in ['pipe_name','connection_generation','bridge_pid']);connections.append(conn)
   gate(label+' snapshot/save processconnection',conn==tuple(snap['driver_state'][k]for k in ['pipe_name','connection_generation','bridge_pid'])and conn[1:]==(config['native_session_binding']['connection_generation'],config['native_session_binding']['bridge_pid']))
   for name,p in [('save-response',receipt_path),('save-request',request_path),('snapshot-response',snap_path),('snapshot-request',checked(pair['snapshot']['request']))]:copies.append(freeze(p,label+'-'+name+'.json'))
   if 'post_snapshot'in pair:
    post_path=checked(pair['post_snapshot']['response']);post=read(post_path)['body'];copies.append(freeze(post_path,label+'-post-snapshot-response.json'))
    gate(label+' preUI post-save date/identity paused stable',post['date_raw']==date and post['played_character']['character_id']==config['actor_id']and post['paused']is True)
   melted=OUT/(label+'-melted.ck3');argv=[str(RAKALY),'melt',str(raw),'--unknown-key','stringify','--format','ck3','--out',str(melted)]
   write(label+'-decoder-binding.json',{'argv':argv,'raw':ident(raw),'rakaly':ident(RAKALY)})
   run=process(label+'-melt',argv);gate(label+' real decoderexit0',run['exit_code']==0 and melted.is_file())
   original_text=melted.read_text(encoding='utf-8-sig')
   chars=[]
   for cid in [config['victim_id'],config['killer_id']]:
    char=character_snapshot(original_text,cid);exact=OUT/(label+'-character-'+str(cid)+'-exact.txt')
    with exact.open('x',encoding='utf-8',newline='\n')as f:f.write(char.pop('raw_block')+'\n')
    char['exact_extract']=ident(exact);chars.append(char)
   objects={}
   for domain in ['combats','house_relations']:
    block=extract_exact_indented_block(original_text,domain,0);exact=OUT/(label+'-'+domain+'-exact.txt')
    with exact.open('x',encoding='utf-8',newline='\n')as f:f.write(block+'\n')
    ast=parse_block(block_body(block));objects[domain]={'exact_extract':ident(exact),'entries':ast}
    if domain=='combats':
     objects['matched_combat_blocks']=find_key_blocks(ast,str(config['combat_id']));gate(label+' saved fullCombat16777218',bool(objects['matched_combat_blocks']))
   accolades=[m.group(1)for m in re.finditer(r'^(\w*accolade\w*)=\{',original_text,re.M)]
   objects['accolade_top_level_names']=accolades
   for name in accolades:
    block=extract_exact_indented_block(original_text,name,0);exact=OUT/(label+'-'+name+'-exact.txt')
    with exact.open('x',encoding='utf-8',newline='\n')as f:f.write(block+'\n')
    objects[name]={'exact_extract':ident(exact),'entries':parse_block(block_body(block))}
   rng=rngreader.inventory(melted);rng_id=write(label+'-RNG-inventory.json',rng)
   projection={'label':label,'date_raw':date,'source_values':sv,'immutable':ident(raw),'melted':ident(melted),'decoder':run,'characters':chars,'objects':objects,'rng_inventory':rng_id,'rng_top_level':rng['top_level']}
   projection_id=write(label+'-full-selected-saved-projection.json',projection);projection['projection_receipt']=projection_id;states.append(projection)
   print('Actual decode/project '+label+' complete',flush=True)
   del original_text
  gate('all4 originals exactsameprocess',len(set(connections))==1)
  gate('one original native daydelta24',states[2]['date_raw']-states[1]['date_raw']==24)
  report['exact_original_copies']=copies
  intervals=[]
  for left,right,title in [(0,1,'before_UI_saved_endpoints'),(1,2,'single_day_saved_endpoints'),(2,3,'after_UI_saved_endpoints')]:
   a,b=states[left],states[right]
   chars=[{'character_id':cid,'full_scalar_leaf_deltas':delta(a['characters'][j]['entries'],b['characters'][j]['entries'])}for j,cid in enumerate([config['victim_id'],config['killer_id']])]
   combat_a={row['path']:row['entries']for row in a['objects']['matched_combat_blocks']};combat_b={row['path']:row['entries']for row in b['objects']['matched_combat_blocks']}
   gate(title+' savedcombatpaths stable',combat_a.keys()==combat_b.keys())
   comparison={key:{'before':a['rng_top_level'][key]['uint32'],'after':b['rng_top_level'][key]['uint32'],'equal':a['rng_top_level'][key]['uint32']==b['rng_top_level'][key]['uint32'],'uint32_delta_modulo':(b['rng_top_level'][key]['uint32']-a['rng_top_level'][key]['uint32'])%2**32}for key in ['random_seed','random_count']}
   interval={'interval':title,'before':a['projection_receipt'],'after':b['projection_receipt'],'full_character_deltas':chars,'full_case_combat_deltas':[{'path':key,'all_scalar_leaf_deltas':delta(combat_a[key],combat_b[key])}for key in combat_a], 'full_house_DB_deltas':delta(a['objects']['house_relations']['entries'],b['objects']['house_relations']['entries']), 'saved_top_level_RNG_comparison':comparison,'all_engine_or_context_RNG_unchanged':'UNKNOWN','time_resolution':'endpoint only'}
   interval['accolade_section_deltas']=[{'name':name,'all_scalar_leaf_deltas':delta(a['objects'].get(name,{}).get('entries',[]),b['objects'].get(name,{}).get('entries',[]))}for name in sorted(set(a['objects']['accolade_top_level_names'])|set(b['objects']['accolade_top_level_names']))]
   intervals.append({'interval':title,'receipt':write(title+'-complete-endpoint-deltas.json',interval),'summary':{'character_delta_counts':[len(row['full_scalar_leaf_deltas'])for row in chars],'case_combat_delta_counts':[len(row['all_scalar_leaf_deltas'])for row in interval['full_case_combat_deltas']],'RNG':comparison}})
  report['saved_states']=[{'label':s['label'],'projection':s['projection_receipt'],'immutable':s['immutable'],'source_values':s['source_values'],'character_endpoint_summary':[{k:v for k,v in c.items()if k not in ['entries','exact_extract']}for c in s['characters']]}for s in states]
  report['three_intervals']=intervals
  report['monitor_schema_inspection']=ident(OUT/'monitor-original-schema-inspection.json')
  report['daily_finish_original']=freeze(PAIR/'one-day-finished.json','one-day-finished.json')
  finish=read(PAIR/'one-day-finished.json')
  report['daily_finish_fields']={k:v for k,v in finish.items()if k in ['phase','trace_error','error','after_values','before_values','trace_finish_body']}
  report['partial_monitor_original']=freeze(LIVE/'ck3-output/interactive-requests-responses/variable-monitor-finish-once.json','variable-monitor-finish-once.json')
  report['status']='PASS_ORIGINAL_FOUR_SAVE_BINDINGS_AND_ENDPOINT_PROJECTIONS_ONLY'
  report['limits']=['These are actual R0142 saved endpoints, not full intraday causal coverage.', 'Daily managed DTO unavailable; no old trace used, no selector/case-sole-cause check run.', 'Independent monitor nativefailed/flags8/truncated128; no full monitor/weapon-producer closure.', 'Equal endpoint fields do not exclude transient writes or RNG advancement/restoration.', 'Saved trait ordinals require original lookup mapping; base6skills differ from nativeeffective battleentries.', 'No UI approval, fullpanel or video completion is inferred.']
  for pin in config['pins']:checked(pin)
  for row in copies:gate('original stable '+row['original']['path'],ident(row['original']['path'])==row['original'])
 except Exception as error:
  report['status']='RED_SAVED_ENDPOINT_INPUT_GATE';report['error']=type(error).__name__+': '+str(error)
 receipt=write('R0142-four-save-endpoint-verification.json',report)
 print(json.dumps({'status':report['status'],'error':report.get('error'),'receipt':receipt},ensure_ascii=False),flush=True)
 return 0 if report['status'].startswith('PASS_')else 2
if __name__=='__main__':raise SystemExit(main())

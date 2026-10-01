from pathlib import Path
from decimal import Decimal
import difflib,hashlib,json,re,sys
import pefile
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,'C:/w/e2research1001/ck3_autonomous_player/src')
from xar_autoplayer.simulation.knight_causal_save_projection import extract_exact_indented_block,parse_block,block_body,delta,find_key_blocks,text_sha256
ROOT=Path(__file__).resolve().parent
IN=ROOT/'continuation-a02'
OUT=ROOT/'full-block-projection-a01'
OUT.mkdir(exist_ok=False)
def ident(p):
 with p.open('rb')as f:h=hashlib.file_digest(f,'sha256').hexdigest().upper()
 return {'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':h}
def write(path,j):
 with path.open('x',encoding='utf-8',newline='\n')as f:json.dump(j,f,ensure_ascii=False,indent=2);f.write('\n')
def textfile(path,text):
 with path.open('x',encoding='utf-8',newline='\n')as f:f.write(text)
facts_path=IN/'R0139-readonly-facts-a01.json'
facts=json.loads(facts_path.read_text())
assert ident(facts_path)['sha256']=='68C10AC7E866026DD387427CE132F4C1FE86AD45292D991ABD35DE4E0994DB1C'
assert len(facts['checks'])==39 and all(r['pass'] for r in facts['checks'])
trace_path=Path(facts['trace_original']['path'])
assert ident(trace_path)==facts['trace_original']
trace=json.loads(trace_path.read_text())['body']['managed_trace']['trace']
pe=pefile.PE('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe')
def rtti_name(vt):
 import struct
 col=struct.unpack('<Q',pe.get_data(vt-8,8))[0]-pe.OPTIONAL_HEADER.ImageBase
 td=struct.unpack('<I',pe.get_data(col+12,4))[0]
 return pe.get_data(td+16,400).split(b'\0')[0].decode('ascii')
nodes=[dict(row,type_name=rtti_name(row['node_vtable_rva']))for row in trace['effect_node_draws']]
body_pairs={};snapshots=[]
for label,state in zip(('before','after'),facts['saved_states']):
 for key in ('raw','melted'):
  actual=ident(Path(state[key]['path']))
  assert actual==state[key],(key,actual,state[key])
 text=Path(state['melted']['path']).read_text(encoding='utf-8-sig')
 blocks={}
 for cid in (33437,34120):
  raw=extract_exact_indented_block(text,str(cid),1)
  target=OUT/f'{label}-character-{cid}-exact.txt';textfile(target,raw+'\n')
  entries=parse_block(block_body(raw));blocks[str(cid)]={'raw_text':raw,'original_extract':ident(target),'entries':entries}
 combats=extract_exact_indented_block(text,'combats',0)
 entries=parse_block(block_body(combats))
 matched=find_key_blocks(entries,str(facts['managed_checkpoint']['before']['combat_id']))
 if not matched:raise ValueError('saved native combat ID missing')
 blocks['combat']={'matched_paths':[m['path']for m in matched],'matches':matched}
 for i,m in enumerate(matched):
  out=OUT/f'{label}-combat-{facts["managed_checkpoint"]["before"]["combat_id"]}-match-{i}.json'
  write(out,m);m['exact_parsed_extract']=ident(out)
 body_pairs[label]=blocks
 snapshots.append({'label':label,'saved_source':state,'characters':{k:{x:v for x,v in b.items()if x!='raw_text'}for k,b in blocks.items()if k!='combat'},'combat':blocks['combat']})
char_diffs={}
for cid in ('33437','34120'):
 b=body_pairs['before'][cid];a=body_pairs['after'][cid]
 changed=delta(b['entries'],a['entries'])
 difftext=''.join(difflib.unified_diff(b['raw_text'].splitlines(keepends=True),a['raw_text'].splitlines(keepends=True),fromfile='before-'+cid,tofile='after-'+cid))
 path=OUT/f'character-{cid}-complete-diff.txt';textfile(path,difftext)
 char_diffs[cid]={'all_scalar_leaf_deltas':changed,'line_diff':ident(path)}
combats=[]
before={m['path']:m for m in body_pairs['before']['combat']['matches']}
after={m['path']:m for m in body_pairs['after']['combat']['matches']}
assert before.keys()==after.keys()
for p,b in before.items():
 a=after[p];combats.append({'path':p,'all_scalar_leaf_deltas':delta(b['entries'],a['entries'])})
records=trace['records']
native_diffs=[]
def jsondelta(left,right,path=''):
 if isinstance(left,dict)and isinstance(right,dict):
  out=[]
  for k in sorted(left.keys()|right.keys()):
   if k not in left or k not in right:out.append({'path':path+'/'+k,'before_present':k in left,'before':left.get(k),'after_present':k in right,'after':right.get(k)})
   else:out.extend(jsondelta(left[k],right[k],path+'/'+k))
  return out
 if left!=right:return [{'path':path,'before':left,'after':right}]
 return []
for b,a in zip(records,records[1:]):
 native_diffs.append({'before_boundary':b['boundary'],'after_boundary':a['boundary'],'side_deltas':jsondelta(b['sides'],a['sides']),'character_deltas':jsondelta(b.get('characters',[]),a.get('characters',[])),'accolade_deltas':jsondelta(b.get('accolades',[]),a.get('accolades',[])),'battle_event_deltas':jsondelta(b.get('battle_events',[]),a.get('battle_events',[]))})
consumer=Path('C:/Users/1/ck3-e2-six-gap-research-20261001/root-attempt-02/knight_research_pair_a02.py')
source_delta=consumer.with_name('current-research-consumer-delta.json')
report={'schema':'ck3.R0139.complete-saved-case-block-projection.v1','status':'PROJECTED_EXACT_ORIGINAL_BLOCKS','run_id':facts['run_id'],'episode_run_id':facts['episode_run_id'],'source_head':facts['source_head'],'date_raw_pair':[53146848,53146872],'calendar_pair':['1066.12.29','1066.12.30'],'case_day_names_are_not_calendar_days':True,'strict_receipt':ident(facts_path),'trace_source':ident(trace_path),'actual_consumer':ident(consumer),'consumer_delta':ident(source_delta),'projector':ident(Path(__file__)),'pure_parser':ident(Path('C:/w/e2research1001/ck3_autonomous_player/src/xar_autoplayer/simulation/knight_causal_save_projection.py')),'executable':ident(Path('C:/SteamLibrary/steamapps/common/Crusader Kings III/binaries/ck3.exe')),'complete_character_blocks':snapshots,'complete_character_diffs':char_diffs,'saved_combat_case_diffs':combats,'native_all_boundary_state_diffs':native_diffs,'native_full_records':records,'actual_nested_node_draws_with_stock_type':nodes,'actual_selector':trace['knight_selects'],'prestige_saved_delta':{key:str(Decimal(facts['saved_states'][1]['characters'][1][key])-Decimal(facts['saved_states'][0]['characters'][1][key]))for key in ('prestige_currency','prestige_accumulated')},'limits':{'saved_all_scalar_fields_in_selected_blocks_projected':True,'other_characters_or_global_state_complete':False,'per_write_runtime_cause_proven':False,'full_mutable_transition_bundle_complete':False,'sole_cause_proven':False,'old_a02_unknown_closed':False,'character_ui_proven':False,'full_battle_panel_proven':False,'nested_node_coverage':'190 stores only nested nodes whose RNG counter/salt changed; absent entries are not proof of nonexecution','death_node':'generic CCharacterDeathEffect call38 executing under event11 is proven; typed victim/reason/request/queue/commit tuple is not yet observed'}}
write(OUT/'R0139-full-block-sourcebound-projection-a01.json',report)
print(json.dumps({'projection':ident(OUT/'R0139-full-block-sourcebound-projection-a01.json'),'combat_paths':list(before),'character_scalar_delta_counts':{k:len(v['all_scalar_leaf_deltas'])for k,v in char_diffs.items()},'combat_scalar_delta_counts':[len(c['all_scalar_leaf_deltas'])for c in combats]},ensure_ascii=False))

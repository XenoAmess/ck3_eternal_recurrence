"""Narrow saved top-level fields and current actor domain titles; no game calls."""
from pathlib import Path
import json,hashlib,sys,re
BASE=Path('C:/workspace/ck3_lyd_runtime_20261004')
READER=BASE/'r9-c2-incremental-readback-helper-20261005-001/review-package-002'
sys.path.insert(0,str(READER))
import read_r8_c2 as m
def ref(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(r):
 m.closed(r,('path','bytes','sha256'),'supplement immutable reference')
 p=Path(r['path']).resolve();m.need(BASE.resolve() in p.parents,'external input required')
 raw=p.read_bytes();m.need(len(raw)==r['bytes'] and m.sha(raw)==r['sha256'],'supplement reference differs')
 return raw
def write(p,d):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,indent=2);f.write('\n')
def run(reqpath):
 req=json.loads(Path(reqpath).read_bytes())
 m.closed(req,('schema','core_readback','before_protection','output'),'selected supplement request')
 m.need(req['schema']=='lyd.r9.selected-protection-request.v1','supplement schema differs')
 m.need(ref(READER/'read_r8_c2.py')['sha256']=='cfee520abacd426b7b73b1e91da3fa1abe2ad44d67d3e50af758a1dcdeb7b2e4','frozen reader differs')
 for row in json.loads((READER/'BINDINGS.json').read_bytes())['dependencies']:
  m.need(m.sha((READER/'dependencies'/row['path']).read_bytes())==row['sha256'],'frozen parser differs')
 core=json.loads(read(req['core_readback']));cached=json.loads(read(req['before_protection']))
 m.need(core['schema']=='lyd.r9.c2.actual-increment-readback.v2' and core['sdk_success_credit'] is False and core['after_sdk'] is None and core['source_head']=='54457b371e947edb86903c2ebd578034f02695db',
        'actual R9 core report source differs')
 m.need(core['after_state']['played_character_id']==31254,'actual full actor differs')
 old=cached['after'];cache={}
 raw=m.bytesref(core['after_artifact'],cache,saved=True)
 text=raw.decode('utf-8-sig').replace('\r\n','\n')
 living=m.section(text,'living','dead_unprunable')
 current={'char_protections':{},'actor_landed_protections':{},'field_presence':{}}
 for cid in ('31254','65865','65866'):
  fields=m.parse(m.extract_exact_indented_block(living,cid,0))
  current['char_protections'][cid]={k:m.asthash(m.one(fields,k)) for k in old['char_protections'][cid]}
  current['field_presence'][cid]={k:m.one(fields,k) is not None for k in old['char_protections'][cid]}
  if cid=='31254':
   landed=m.one(fields,'landed_data',required=True)
   current['actor_landed_protections']={k:m.asthash(m.one(landed,k)) for k in old['actor_landed_protections']}
   domain=m.one(landed,'domain',required=True)
   ids=[x['value'] for x in domain]
   m.need(bool(ids) and len(ids)==len(set(ids)) and all(x.isdigit() for x in ids),'actual domain missing/duplicate')
   current['domain_ids']=ids
 # CK3 save title numeric records are physically at indent0 after title metadata.
 # Bound the title text to the next exact top-level dynasties section.
 titletext=m.section(text,'landed_titles','dynasties')
 current['titles']={}
 for tid in current['domain_ids']:
  rows=m.parse(m.extract_exact_indented_block(titletext,tid,0))
  current['titles'][tid]={'key':m.scalar(rows,'key',True),'holder':m.scalar(rows,'holder',True),
    'actual_complete_AST_sha256':m.asthash(rows)}
 current['actual_selected_title_count']=len(current['titles'])
 title_equal=current['titles']==old['titles']
 char_equal=current['char_protections']==old['char_protections']
 landed_equal=current['actor_landed_protections']==old['actor_landed_protections']
 holder_ok=all(t['holder']=='31254' for t in current['titles'].values())
 out=Path(req['output']).resolve()
 m.need(BASE.resolve() in out.parents and not out.exists(),'new external output required')
 out.mkdir()
 report={'schema':'lyd.r9.actual-selected-protections.v1',
  'status':'ACTUAL_SELECTED_PROTECTIONS_MATCH' if title_equal and char_equal and landed_equal and holder_ok else 'ACTUAL_SELECTED_PROTECTIONS_DIFFERENCES',
  'core_readback':req['core_readback'],'after_save':core['after_artifact'],
  'before_protection_cache':req['before_protection'],'after':current,
  'selected_complete_title_AST_equal':title_equal,'actual_selected_title_count':current['actual_selected_title_count'],
  'actual_selected_title_holders_all_actor':holder_ok,'actual_domain_ids_equal':current['domain_ids']==old['domain_ids'],
  'selected_family_court_namedbranches_equal':char_equal,'selected_domain_government_laws_equal':landed_equal,
  'field_presence_disclosed':current['field_presence'],'scope':'Only actual actor domain titles and three exact role characters. No entire title or world character AST parsing.',
  'whole_world_characters_scanned':False,'whole_world_political_titles_scanned':False,
  'sdk_success_credit':False,'native_ACK_business_credit':False,'full_cycle_credit':False,'game_called':False,
  'supplement_source':ref(Path(__file__))}
 write(out/'REPORT.json',report)
 write(out/'INDEX.json',{'schema':'lyd.r9.c2.selected-protection-index.v1','files':[
  {'path':'REPORT.json','bytes':ref(out/'REPORT.json')['bytes'],'sha256':ref(out/'REPORT.json')['sha256']}]})
 print(json.dumps({'status':report['status'],'count':report['actual_selected_title_count'],
  'title_equal':title_equal,'char_equal':char_equal,'landed_equal':landed_equal,
  'report':ref(out/'REPORT.json'),'index':ref(out/'INDEX.json')}))
 return report
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: supplement_selected_protections.py REQUEST.json')
 run(sys.argv[1])

"""Portable stdlib verifier: exact JSON field excerpts and pinned production math.

Does not execute relay stages, import SDK, or read whole originals by default.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,sys,zipfile
sys.dont_write_bytecode=True
def need(x,s):
 if not x:raise ValueError(s)
def sha(b):return hashlib.sha256(b).hexdigest()
def run(archive,repo):
 with zipfile.ZipFile(archive) as z:
  expected={'recovered-supply.json','raw-slices.json','agent-decision.json'}
  need(set(z.namelist())==expected and len(z.infolist())==3,'Archive members differ')
  need(sum(i.file_size for i in z.infolist())<=128*1024 and all(i.file_size<=64*1024 for i in z.infolist()),'Bounded metadata archive required')
  values={n:json.loads(z.read(n)) for n in expected}
 facts=values['recovered-supply.json'];slices=values['raw-slices.json'];decision=values['agent-decision.json'];count=0
 need(facts['stage_order']==['baseline','post_split','post_merge'],'Stage order differs')
 for group in slices['groups']:
  stage=facts['stages'][group['stage']];need(group['whole_original']['bytes']<=64*1024**2,'Historical whole input bound differs')
  for s in group['slices']:
   b=s['raw_utf8'].encode('utf-8');need(len(b)==s['bytes'] and sha(b)==s['sha256'],'Exact excerpt bytes changed')
   need(0<=s['offset']<s['offset']+len(b)<=group['whole_original']['bytes'],'Excerpt offset outside original')
   field=s['pointer'].split('/')[-1];need(json.loads(b'{'+b+b'}')=={field:s['expected_value']},'Excerpt JSON literal differs')
   if s['pointer'].startswith('/army_strengths/'):
    ordinal=int(s['pointer'].split('/')[2]);rows=[r for r in stage['rows'] if r['source_array_index']==ordinal];need(len(rows)==1 and rows[0][field]==s['expected_value'],'Excerpt row/path differs from consumer input')
   else:need(stage['frame'][field]==s['expected_value'],'Excerpt frame differs from consumer input')
   count+=1
 ref=facts['production_comparison'];p=Path(repo)/ref['repo_path'];b=p.read_bytes();need(len(b)==ref['bytes'] and sha(b)==ref['sha256'],'Exact production consumer source differs')
 spec=importlib.util.spec_from_file_location('r09_portable_supply_production_only',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 def packet(stage):return {'query':{'army_strengths':facts['stages'][stage]['rows']}}
 result=m.compare_merge_supply(packet('post_split'),packet('post_merge'),[93,162]);need(result==facts['merge_supply'],'Production comparison does not reproduce frozen result')
 need(result['status']=='NATIVE_WEIGHTED_SUPPLY_MATCH' and result['upper_clamp_observed'] is False and result['preclamp_raw']==result['post_actual_capacity_raw']==result['actual_stock_raw']==10000000,'Equal-cap non-clamp conclusion differs')
 physical=[facts['stages'][s]['selected_unique_physical_current_max'] for s in facts['stage_order']];need(physical==[[250,250]]*3,'Referenced physical scalar differs')
 need(all(facts[k] is False for k in ['strict_unrelated_freeze_pass','independent_reverse_sameS0_observed','dynamic_video_qualified','R09_full_card_closed']),'Historical refusal or unqualified requirement was overwritten')
 need(decision['R09_full_card_closed'] is False and decision['upper_clamp_observed'] is False,'Agent decision overstates qualification')
 cohort=facts['existing_literal_cohort_evidence'];p=Path(repo)/cohort['repo_path'];b=p.read_bytes();need(len(b)==cohort['bytes'] and sha(b)==cohort['sha256'],'Existing canonical cohort projection differs')
 return {'status':'EXACT_EXCERPTS_AND_PRODUCTION_SUPPLY_COMPARISON_REPRODUCED','slice_count':count,'production_comparison':result,'existing_literal_projection_SHA_matched':True,'whole_originals_body_read':False,'whole_original_SHA_recomputed_from_slices':False,'physical_whole_fixture_rerun':False,'R09_full_card_closed':False,'SDK_or_game_actions':0}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--archive',type=Path,required=True);p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();v=run(a.archive,a.repo)
 with a.output.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps(v,ensure_ascii=False))
if __name__=='__main__':main()

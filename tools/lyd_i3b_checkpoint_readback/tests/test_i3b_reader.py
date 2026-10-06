"""Small authored fixtures only; no actual checkpoint body is opened."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).parents[1]/'reader'))
import i3b_checkpoint_reader as reader

A=31254
POLITICAL=[2230,2231,2232,2235,2262,2263,2264]
TITLE_TYPE='synthetic_native_title_reference'

def E(key,value): return {'key':key,'value':value}
def n(value): return [E('type','value'),E('identity',str(value*100000))]
def ref(kind,value): return [E('type',kind),E('identity',str(value))]
def variables(values,collections=None):
 rows=[]
 for key,value in values.items():
  data=ref(*value) if isinstance(value,tuple) else n(value)
  rows.append(E(None,[E('flag',json.dumps(key)),E('data',data)]))
 lists=[]
 for key,items in (collections or {}).items():
  lists.append(E(None,[E('name',json.dumps(key))]+[E('item',ref(*item)) for item in items]))
 return [E('data',rows),E('list',lists)]
def render(entries,depth=0):
 lines=['{']
 for row in entries:
  key='' if row['key'] is None else str(row['key'])+'='
  if isinstance(row['value'],list):
   body=render(row['value'],depth+1)
   lines.append('\t'*(depth+1)+key+body[0])
   lines.extend(body[1:])
  else: lines.append('\t'*(depth+1)+key+str(row['value']))
 lines.append('\t'*depth+'}')
 return lines
def block(key,entries):
 lines=render(entries)
 return key+'='+lines[0]+'\n'+'\n'.join(lines[1:])+'\n'

def fixture(stage='signed_precommit'):
 post=stage.endswith('postcommit')
 members=[(A,169),(65865,169),(65866,169),(70001,170),(70002,170),(70003,170)]
 chars={}
 for cid,rid in members:
  values={} if post else {'lyd_i3b_member_owner':('char',A),'lyd_i3b_member_serial':5,'lyd_i3b_member_rite':('rite',rid),'lyd_i3b_was_elector':1,
       'lyd_i3b_was_player':int(cid in (A,65865)),'lyd_i3b_player_yes':0 if stage=='proposal' else int(cid in (A,65865)),
       'lyd_i3b_vote':-1 if stage=='proposal' else int(cid not in (65866,70003))}
  if cid==A:
   values.update({'lyd_i3b_serial':5,'lyd_i3b_nonce':7,'lyd_i3b_faith':('faith',107),'lyd_i3b_main':('rite',169)})
   if post:
    values.update({'lyd_i3b_result_serial':5,'lyd_i3b_result_nonce':7,'lyd_i3b_result_code':1,'lyd_i3b_result_authority_mode':1,'lyd_i3b_result_native_hor':('char',A),
                   'lyd_i3b_result_head_title':(TITLE_TYPE,90001),'lyd_c3_office_faith':('faith',107)})
   else:
    values.update({'lyd_i3b_active':1,'lyd_i3b_phase':1 if stage=='proposal' else 2,'lyd_i3b_authority_mode':1,'lyd_i3b_required_native_hor':('char',A)})
  collections={'lyd_i3b_members':[('char',i)for i,_ in members],'lyd_i3b_rites':[('rite',169),('rite',170),('rite',171)],'lyd_i3b_political_titles':[(TITLE_TYPE,i) for i in POLITICAL]} if cid==A and not post else {}
  alive=[E('rite',str(rid)),E('variables',variables(values,collections)),E('literal',json.dumps('braces } { remain quoted'))]
  chars[cid]=[E('first_name',json.dumps('fixture_'+str(cid))),E('alive_data',alive),E('landed_data',[E('domain',[E(None,str(i)) for i in POLITICAL])])]
 # Unrelated living character and zero-valued registry ID must not break scan.
 chars[80001]=[E('alive_data',[E('rite','0')])]
 graph_f={}
 graph_r={}
 for fid,main in ((0,0),(104,159),(106,187),(107,169)):
  doctrine='doctrine_temporal_head' if post and fid==107 else 'doctrine_no_head'
  rows=[E('main_rite',str(main)),E('tenet','lyd_tenet_synthetic_core'),E('tenets',[E(None,[E('tenet','lyd_tenet_synthetic_allowed'),E('status','permitted')])]),E('doctrine',doctrine)]
  if post and fid==107:
   rows.extend([E('religious_head',str(A)),E('religious_head_title','90001'),E('variables',variables({'lyd_c3_recognized_leader':('char',A)}))])
  graph_f[fid]=rows
 for rid,parent in ((0,0),(159,104),(187,106),(169,107),(170,107),(171,107)):
  doctrine='doctrine_temporal_head' if post and parent==107 else 'doctrine_no_head'
  rows=[E('faith',str(parent)),E('tenet','lyd_tenet_synthetic_core'),E('tenets',[E(None,[E('tenet','lyd_tenet_synthetic_allowed'),E('status','permitted')])]),E('doctrine',doctrine)]
  if rid==169: rows.append(E('head_of_rite',str(A)))
  if not post and parent==107:
   dormant=int(rid==171)
   school={'lyd_i3b_owner':('char',A),'lyd_i3b_serial':5,'lyd_i3b_members_total':0 if dormant else 3,'lyd_i3b_total':0 if dormant else 3,
     'lyd_i3b_yes':0 if dormant or stage=='proposal' else 2,'lyd_i3b_signed':0 if dormant or stage=='proposal' else 1,'lyd_i3b_dormant':dormant,'lyd_i3b_counties':0 if dormant else 1}
   if not dormant: school['lyd_i3b_delegate']=('char',A if rid==169 else 70001)
   rows.append(E('variables',variables(school)))
  graph_r[rid]=rows
 titles={i:[E('key','synthetic_political_'+str(i)),E('holder',str(A)),E('history',[E('1066.1.1',str(A))])] for i in POLITICAL}
 if post:
  titles[90001]=[E('key','d_synthetic_runtime_title'),E('holder',str(A)),E('variables',variables({'lyd_c2_owned_head_title':1,'lyd_c2_owner_faith':('faith',107)})),
   E('synthetic_laws',[E(None,'temporal_head_of_faith_succession_law')]),E('synthetic_destroy','on'),E('synthetic_no_claims','on'),E('synthetic_form','on'),E('synthetic_primary_heir','on')]
 baseline_f=copy.deepcopy(graph_f);baseline_r=copy.deepcopy(graph_r)
 if post:
  for fid in (107,):
   baseline_f[fid]=[r for r in baseline_f[fid] if r['key'] not in ('religious_head','religious_head_title','variables')]
   for r in baseline_f[fid]:
    if r['key']=='doctrine':r['value']='doctrine_no_head'
  for rid in (169,170,171):
   for r in baseline_r[rid]:
    if r['key']=='doctrine':r['value']='doctrine_no_head'
 def baseline_graph(rows):
  return {str(i):{'AST_sha256':reader.ast_sha(e),'tenet_doctrine_rows':[r for r in e if r['key'] in ('tenets','tenet','doctrine','doctrines')]} for i,e in rows.items()}
 request={'schema':'lyd.i3b.checkpoint-reader-request.v1','mode':'synthetic_fixture','source_head':reader.HEAD,'stage':stage,
  'identity':{'actor_id':A,'faith_id':107,'main_rite_id':169,'pid':None,'session_id':None,'revision':None,'checkpoint_id':None},
  'save':None,'expected':{'serial':5,'nonce':7,'phase':1 if stage=='proposal' else 2},
  'native_reference_binding':{'schema':'lyd.saved-native-reference-binding.v1','source_head':reader.HEAD,'evidence_sha256':'1'*64,'title_type':TITLE_TYPE},
  'native_title_binding':None,'native_predicates':None,'output':None,
  'baseline':{'actual_faith_rite_ids':[169,170,171],'political_title_ids':POLITICAL,'political_titles':{str(i):{'AST_sha256':reader.ast_sha(e),'holder':A}for i,e in titles.items() if i in POLITICAL},'graphs':{'faiths':baseline_graph(baseline_f),'rites':baseline_graph(baseline_r)}}}
 request['native_predicates']={'schema':'lyd.i3b.native-predicates.v1','source_head':reader.HEAD,'checkpoint_sha256':None,'identity':request['identity'],
    'complete_current_faith_roster':True,'human_character_ids':[A,65865],
    'characters':[{'character_id':cid,'alive':True,'adult':True,'imprisoned':False,'incapable':False,'learning':15,'is_ai':cid not in(A,65865)}for cid,_ in members],
    'rite_counties':{'169':1,'170':1,'171':0},'evidence_sha256':'2'*64}
 if post:
  request['native_predicates']=None
  request['native_title_binding']={'schema':'lyd.native-title.saved-field-binding.v1','source_head':reader.HEAD,'evidence_sha256':'3'*64,
    'law':{'path':['synthetic_laws'],'shape':'bare_scalar_list'},
    'properties':{name:{'path':[key],'true_token':'on','false_token':'off'}for name,key in zip(('destroy_if_invalid_heir','no_automatic_claims','definitive_form','always_follows_primary_heir'),('synthetic_destroy','synthetic_no_claims','synthetic_form','synthetic_primary_heir'))}}
 return {'characters':chars,'faiths':graph_f,'rites':graph_r,'titles':titles,'request':request,'current_humans':[A,65865]}

def save_text(data):
 return ('SAVsynthetic\n'+block('faiths',[E('database',[E(str(i),e)for i,e in data['faiths'].items()])])+block('rites',[E('database',[E(str(i),e)for i,e in data['rites'].items()])])+
   'living={\n'+''.join(block(str(i),e) for i,e in data['characters'].items())+'}\n'+'dead_unprunable={\n}\n'+
   'landed_titles={\n'+''.join(block(str(i),e)for i,e in data['titles'].items())+'}\n'+'dynasties={\n}\n'+block('currently_played_characters',[E(None,str(i))for i in data['current_humans']]))
def run(data):
 text=save_text(data);sha=hashlib.sha256(text.encode()).hexdigest()
 if data['request']['native_predicates'] is not None:data['request']['native_predicates']['checkpoint_sha256']=sha
 return reader.observe_text(text,data['request'],sha)
def change_var(entries,name,value):
 alive=reader.one(entries,'alive_data') if reader.one(entries,'alive_data') is not None else entries
 rows=reader.one(reader.one(alive,'variables'),'data')
 for row in rows:
  if json.loads(reader.one(row['value'],'flag'))==name:
   for field in row['value']:
    if field['key']=='data':field['value']=ref(*value) if isinstance(value,tuple)else n(value)
   return
 raise AssertionError('no fixture var '+name)

class ReaderTests(unittest.TestCase):
 def test_proposal_has_no_ballot_or_human_authority(self):
  d=fixture('proposal');self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MATCH')
  change_var(d['characters'][A],'lyd_i3b_player_yes',1)
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
 def test_signed_two_schools_full_roster_and_human412(self):
  state=run(fixture())
  self.assertEqual(state['assessment'],'OBSERVED_CONTRACT_MATCH')
  self.assertEqual(state['roster']['living_records_scanned'],7)
  self.assertEqual([r['quorum_numerator']for r in state['schools']],[0,0,0])
  self.assertEqual(state['roster']['saved_current_human_faith_ids'],[A,65865])
  self.assertIsNone(state['actual_pass'])
 def test_each_school_quorum_not_aggregate(self):
  d=fixture();change_var(d['characters'][65866],'lyd_i3b_vote',1);change_var(d['rites'][169],'lyd_i3b_yes',3)
  change_var(d['characters'][70002],'lyd_i3b_vote',0);change_var(d['rites'][170],'lyd_i3b_yes',1)
  s=run(d);self.assertEqual(s['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  self.assertFalse(next(r['matches']for r in s['checks']if r['name']=='rite_170_independent_two_thirds'))
 def test_npc_signature_not_human_consent(self):
  d=fixture();change_var(d['characters'][65865],'lyd_i3b_player_yes',0)
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
 def test_extra_living_uncaptured_and_unclassified(self):
  for rite in ('169',None):
   d=fixture();d['characters'][81234]=[E('alive_data',[] if rite is None else[E('rite',rite)])]
   s=run(d);self.assertEqual(s['assessment'],'OBSERVED_CONTRACT_MISMATCH')
   self.assertEqual(s['roster']['faith_classification_complete'],rite is not None)
 def test_old_nonce_wrong_owner_and_vote_count_fails(self):
  cases=[lambda d:d['request']['expected'].update(nonce=6),lambda d:change_var(d['characters'][70001],'lyd_i3b_member_owner',('char',65865)),lambda d:change_var(d['rites'][170],'lyd_i3b_yes',3)]
  for mutate in cases:
   d=fixture();mutate(d);self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
 def test_native_qualification_drift_and_absence_not_stamps(self):
  for key,value in (('learning',14),('incapable',True),('adult',False),('imprisoned',True),('is_ai',True)):
   d=fixture();d['request']['native_predicates']['characters'][0][key]=value
   self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  d=fixture();d['request']['native_predicates']=None
  self.assertEqual(run(d)['assessment'],'INCOMPLETE_NATIVE_QUALIFICATION')
 def test_zero_scholars_wrong_rite_delegate_and_nonfinite_learning(self):
  d=fixture()
  for cid in (70001,70002,70003):
   change_var(d['characters'][cid],'lyd_i3b_was_elector',0);change_var(d['characters'][cid],'lyd_i3b_vote',-1)
  change_var(d['rites'][170],'lyd_i3b_total',0);change_var(d['rites'][170],'lyd_i3b_yes',0)
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  d=fixture();change_var(d['rites'][170],'lyd_i3b_delegate',('char',A))
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  for bad in (float('nan'),float('inf'),15.5):
   d=fixture();d['request']['native_predicates']['characters'][0]['learning']=bad
   with self.assertRaises(reader.ReadbackError):run(d)
 def test_partial_factory_state_preserved_without_success_credit(self):
  d=fixture('partial_postcommit');change_var(d['characters'][A],'lyd_i3b_result_code',3)
  alive=reader.one(d['characters'][A],'alive_data');rows=reader.one(reader.one(alive,'variables'),'data')
  rows[:]=[r for r in rows if json.loads(reader.one(r['value'],'flag'))!='lyd_i3b_result_head_title']
  s=run(d);self.assertEqual(s['partial_actual_title_observation']['faith_title_id'],90001)
  self.assertIsNone(s['native_title']);self.assertEqual(s['partial_native_title']['title_id'],90001)
  self.assertIsNone(s['actual_pass']);self.assertIsNone(s['formal_mandate_credit'])
 def test_stale_native_witness_and_duplicate_typed_reference_rejected(self):
  d=fixture();d['request']['native_predicates']['identity']=dict(d['request']['identity'],revision=99)
  with self.assertRaises(reader.ReadbackError):run(d)
  d=fixture();alive=reader.one(d['characters'][A],'alive_data');ls=reader.one(reader.one(alive,'variables'),'list')
  row=next(r['value']for r in ls if json.loads(reader.one(r['value'],'name'))=='lyd_i3b_members')
  row.append(E('item',ref('char',A)))
  with self.assertRaises(reader.ReadbackError):run(d)
 def test_actual_title_discovered_from_result_not_fixed_id(self):
  d=fixture('success_postcommit');s=run(d)
  self.assertEqual(s['assessment'],'OBSERVED_CONTRACT_MATCH');self.assertEqual(s['native_title']['title_id'],90001)
  self.assertEqual(s['native_title']['holder'],A);self.assertIsNone(s['formal_mandate_credit'])
  d['titles'][91234]=d['titles'].pop(90001);change_var(d['characters'][A],'lyd_i3b_result_head_title',(TITLE_TYPE,91234))
  for r in d['faiths'][107]:
   if r['key']=='religious_head_title':r['value']='91234'
  self.assertEqual(run(d)['native_title']['title_id'],91234)
 def test_wrong_actual_title_holder_owner_law_properties_and_hof_fail(self):
  cases=[lambda d:d['titles'][90001].__setitem__(1,E('holder','65865')),
   lambda d:change_var(d['titles'][90001],'lyd_c2_owner_faith',('faith',106)),
   lambda d:next(r for r in d['titles'][90001]if r['key']=='synthetic_laws')['value'].__setitem__(0,E(None,'wrong_law')),
   lambda d:next(r for r in d['titles'][90001]if r['key']=='synthetic_form').update(value='off'),
   lambda d:next(r for r in d['faiths'][107]if r['key']=='religious_head').update(value='65865')]
  for mutate in cases:
   d=fixture('success_postcommit');mutate(d);self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
 def test_unknown_title_discriminator_and_mapping_not_real_facts(self):
  for key in ('native_reference_binding','native_title_binding'):
   d=fixture('success_postcommit');d['request'][key]=None;s=run(d)
   self.assertEqual(s['assessment'],'INCOMPLETE_NATIVE_QUALIFICATION');self.assertIsNone(s['actual_pass'])
  d=fixture('success_postcommit');change_var(d['characters'][A],'lyd_i3b_result_head_title',('faith',107))
  with self.assertRaises(reader.ReadbackError):run(d)
 def test_political_full_ast_and_complete_tenet_status_protection(self):
  d=fixture('success_postcommit');d['titles'][2230].append(E('law','political_changed'))
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
 def test_added_faith_rite_and_omitted_protected_baseline_rejected(self):
  d=fixture('success_postcommit');d['rites'][172]=[E('faith','107'),E('doctrine','doctrine_no_head')]
  s=run(d);self.assertEqual(s['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  self.assertFalse(next(r['matches']for r in s['checks']if r['name']=='all_actual_rite_172_native_temporal_doctrine'))
  d=fixture();del d['request']['baseline']['graphs']['faiths']['106'];del d['request']['baseline']['graphs']['rites']['187']
  d['faiths'][106].append(E('drift','changed'))
  with self.assertRaises(reader.ReadbackError):run(d)
  d=fixture('success_postcommit');next(r for r in d['rites'][170]if r['key']=='tenets')['value'][0]['value'][1]['value']='core'
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
  d=fixture();d['faiths'][106].append(E('main_drift','bad'))
  self.assertEqual(run(d)['assessment'],'OBSERVED_CONTRACT_MISMATCH')
 def test_pending_actual_refused_before_any_save_open(self):
  d=fixture();r=d['request'];r['mode']='future_actual';r['save']={'path':'DO_NOT_OPEN.ck3','bytes':91669783,'sha256':'0'*64}
  with patch.object(Path,'read_bytes',side_effect=AssertionError('body opened')):
   with self.assertRaises(reader.ReadbackError):reader.read_checkpoint(r)
 def test_duplicate_records_and_truncated_record_fail_closed(self):
  d=fixture();t=save_text(d);bad=t.replace('dead_unprunable={','31254={\n\talive_data={\n\t}\n}\ndead_unprunable={')
  with self.assertRaises(reader.ReadbackError):reader.observe_text(bad,d['request'],'4'*64)
  with self.assertRaises((reader.ReadbackError,ValueError)):list(reader.records('123={\n\talive_data={\n','living'))

if __name__=='__main__':unittest.main(verbosity=2)

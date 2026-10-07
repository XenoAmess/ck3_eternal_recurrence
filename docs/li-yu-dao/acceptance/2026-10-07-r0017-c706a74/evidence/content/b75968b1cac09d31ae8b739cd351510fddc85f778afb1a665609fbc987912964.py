"""Pure isolated fixtures. Actual SDK/profile/session are inputs; synthetic I4 contexts have no runtime credit."""
from pathlib import Path
from hashlib import sha256
import argparse,ast,copy,json,subprocess,sys,unittest
O=Path(__file__).parent;B=O.parent;RUN=B/'live-attempt-017'
P=argparse.ArgumentParser();P.add_argument('--candidate',required=True,type=Path);P.add_argument('--label',required=True);A=P.parse_args()
SUITE=O/A.label;SUITE.mkdir(exist_ok=False);OUT=SUITE/'mirror/run';OUT.mkdir(parents=True)
def ref(p):
 p=Path(p);b=p.read_bytes();return {'path':p.as_posix(),'bytes':len(b),'sha256':sha256(b).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def put(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(p)
M=load(O/'FIXTURE-MIRROR.json');C=load(M['synthetic_mirror_consumer']['path']);C['run_root']=OUT.as_posix()
consumer=SUITE/'mirror/consumer';consumer.mkdir();ci=put(consumer/'INDEX.json',C)
pre=load(M['synthetic_mirror_PREPARED']['path']);pr=put(OUT/'PREPARED.json',pre)
original_wrapper=load(M['original_snapshot_SDK']['path'])
native=next(json.loads(x['text']) for x in original_wrapper['content'] if x.get('type')=='text' and 'ck3.native-profile-receipt.v1' in x.get('text',''))
session=native['session_id'];profile_sha=native['profile_sha256'];snapshot=native['snapshot']
actor=snapshot['played_character']['character_id'];rev=snapshot['revision'];nr=snapshot['native_revision'];date=snapshot['date_raw']
guard=load(pre['guard']['path']);pid=guard['target']['pid']
g2=load(RUN/'mcp-client-001/0004-r17-006-baseline-g2.native-01.json')['result'];generation=g2['connection_generation']
ready=load(RUN/'mcp-client-001/ready.json');author=B/'r17-formal-original0240-source-20261007-002/author_formal_request.py'
base=['--consumer-source',consumer.as_posix(),'--consumer-index-sha256',ci['sha256'],'--request-author',author.as_posix(),'--request-author-sha256',ref(author)['sha256'],'--prepared',pr['path'],'--prepared-sha256',pr['sha256'],'--session-id',session]
tools={x['name']:x for x in load(C['actual_metadata']['path']) and load(load(C['actual_metadata']['path'])['metadata']['path'])}
CALLS=[]
def wrapper_for(body):
    return {'content':[{'type':'text','text':json.dumps(body,ensure_ascii=False)}],'structuredContent':body,'isError':False}
def event_receipt(definition='lyd.106',instance=901,index=8):
    return {'schema':'ck3.native-profile-receipt.v1','session_id':session,'profile_sha256':profile_sha,'status':'native_event_query_verified','result':{'queried_revision':rev,'queried_native_revision':nr,'queried_snapshot_id':snapshot['snapshot_id'],'date_raw':date,'current_event_window_context':{'event_definition_key':definition,'current_event_instance_id':instance,'root_scope':{'typed_identity':{'character_id':actor}},'options':[{'native_option_index':index,'shown':True,'enabled':True}]}}}
def decision_receipt():
    return {'schema':'ck3.native-profile-receipt.v1','session_id':session,'profile_sha256':profile_sha,'status':'native_decision_query_observed','result':{'game_pid':pid,'native_revision':nr,'connection_generation':generation,'date_raw':date,'played_character_id':actor,'available':True,'matching_row_count':1,'row_context_reference_key':actor,'detail_root_visible':True,'detail_definition_matches_target':True,'detail_actor_binding_verified':True,'detail_actor_reference_key':actor,'detail_decision_key':'lyd_study_decision'}}
def call(name,mode,positive=True,query=None,change_snapshot=None,change_wrapper=None,extra=None,override=None):
    folder=SUITE/'fixtures'/name;folder.mkdir(parents=True,exist_ok=False)
    b=copy.deepcopy(native)
    if query and query.get('status')=='native_event_query_verified':b['snapshot']['active_event']={'instance_id':901}
    if change_snapshot:change_snapshot(b)
    w=wrapper_for(b)
    if change_wrapper:change_wrapper(w)
    sr=put(folder/'SYNTHETIC-snapshot-sdk.json',w)
    argv=[sys.executable,'-B','-X','utf8',str(A.candidate),*base,'--snapshot-sdk',sr['path'],'--snapshot-sdk-sha256',sr['sha256'],'--mode',mode]
    if query:
        qr=put(folder/'SYNTHETIC-query-sdk.json',wrapper_for(query));argv+=['--query-sdk',qr['path'],'--query-sdk-sha256',qr['sha256']]
    if extra:argv+=extra
    if override:
        for key,value in override.items():argv[argv.index(key)+1]=str(value)
    output=OUT/name;argv+=['--output',output.as_posix()]
    result=subprocess.run(argv,capture_output=True)
    (folder/'stdout.original').write_bytes(result.stdout);(folder/'stderr.original').write_bytes(result.stderr)
    row={'name':name,'argv':argv,'expected_accept':positive,'actual_exit':result.returncode,'stdout':ref(folder/'stdout.original'),'stderr':ref(folder/'stderr.original'),'output_exists':output.exists(),'fixture_is_synthetic_I4_not_actualquery':True,'original_actual28_profile_session_refs':ref(O/'ACTUAL-SOURCE-INTERFACE-REFS.json'),'runtime_or_formal_credit':None}
    if result.returncode==0:
        arguments=load(output/'ARGUMENTS.actual.json');record=load(output/'RESULT.source-only.json');schema=tools[record['tool']]['inputSchema']
        assert set(schema.get('required',[]))<=set(arguments)<=set(schema.get('properties',{}))
        for key,value in arguments.items():
            prop=schema['properties'][key]
            if prop.get('type')=='integer':assert type(value) is int
            if prop.get('type')=='string':assert type(value) is str
            if 'enum' in prop:assert value in prop['enum']
        row['generated_arguments']=arguments
    put(folder/'INVOCATION.fixture.json',row);CALLS.append(row)
    if positive:
        assert result.returncode==0,result.stderr.decode('utf-8','replace')
        return load(output/'ARGUMENTS.actual.json')
    assert result.returncode!=0,'Unexpectedly accepted invalid fixture'
    assert not output.exists(),'Refused fixture wrote output'

EVENT=['--event-definition','lyd.106','--source-option-key','lyd_practice_zhuxi_c','--native-index','8']
class Contract(unittest.TestCase):
 def test_01_actual28_final10_session_open(self):self.assertEqual(call('actual-interface-open','open-decisions'),{'expected_revision':rev})
 def test_02_paid_actual_index_not_source_ordinal(self):self.assertEqual(call('paid-index8','select-event',query=event_receipt(),extra=EVENT)['option_number'],9)
 def test_03_lastpage_school(self):self.assertEqual(call('school-lastpage','select-event',query=event_receipt('lyd.14'),extra=['--event-definition','lyd.14','--source-option-key','lyd_adopt_jingshi','--native-index','8'])['option_number'],9)
 def test_04_cancel(self):self.assertEqual(call('cancel','select-event',query=event_receipt(),extra=['--event-definition','lyd.106','--source-option-key','lyd_cancel','--native-index','8'])['option_number'],9)
 def test_05_decision_select(self):call('decision-select','select-decision',query=decision_receipt(),extra=['--decision-key','lyd_study_decision'])
 def test_06_decision_confirm(self):call('decision-confirm','confirm-decision',query=decision_receipt(),extra=['--decision-key','lyd_study_decision','--event-definition','lyd.106'])
 def test_07_running_pause(self):call('running-pause','simulation',change_snapshot=lambda b:b['snapshot'].update(paused=False),extra=['--simulation-action','pause'])
 def test_08_bootstrap_event_query(self):self.assertEqual(call('bootstrap-query','query-event',change_snapshot=lambda b:b['snapshot'].update(active_event={'instance_id':901}),extra=['--event-definition','lyd.106'])['event_instance_id'],901)
 def test_09_wrong_client_vs_native_session(self):call('wrong-client-session','open-decisions',False,override={'--session-id':ready['client_session_id']})
 def test_10_wrong_profile(self):call('wrong-profile','open-decisions',False,change_snapshot=lambda b:b.update(profile_sha256='0'*64))
 def test_11_structured_diff(self):call('structured-mismatch','open-decisions',False,change_wrapper=lambda w:w['structuredContent'].update(status='forged'))
 def test_12_public_native_mismatch(self):call('wrong-frame','open-decisions',False,change_snapshot=lambda b:b['snapshot'].update(revision=rev+1))
 def test_13_unpaused_effect(self):call('unpaused-select','select-event',False,query=event_receipt(),change_snapshot=lambda b:b['snapshot'].update(paused=False),extra=EVENT)
 def test_14_stale_event_query(self):
  q=event_receipt();q['result']['queried_revision']+=1;call('stale-query','select-event',False,query=q,extra=EVENT)
 def test_15_event_root(self):
  q=event_receipt();q['result']['current_event_window_context']['root_scope']['typed_identity']['character_id']=actor+1;call('wrong-root','select-event',False,query=q,extra=EVENT)
 def test_16_event_definition(self):call('wrong-definition','select-event',False,query=event_receipt('lyd.135'),extra=EVENT)
 def test_17_event_instance(self):call('wrong-instance','select-event',False,query=event_receipt(instance=902),extra=EVENT)
 def test_18_disabled_option(self):
  q=event_receipt();q['result']['current_event_window_context']['options'][0]['enabled']=False;call('disabled','select-event',False,query=q,extra=EVENT)
 def test_19_hidden_option(self):
  q=event_receipt();q['result']['current_event_window_context']['options'][0]['shown']=False;call('hidden','select-event',False,query=q,extra=EVENT)
 def test_20_duplicate_native_index(self):
  q=event_receipt();q['result']['current_event_window_context']['options']*=2;call('duplicate-index','select-event',False,query=q,extra=EVENT)
 def test_21_wrong_source_key(self):call('wrong-source-key','select-event',False,query=event_receipt(),extra=['--event-definition','lyd.106','--source-option-key','lyd_practice_jingshi_b','--native-index','8'])
 def test_22_old_pid_decision(self):
  q=decision_receipt();q['result']['game_pid']=14776;call('old-pid','select-decision',False,query=q,extra=['--decision-key','lyd_study_decision'])
 def test_23_decision_actor(self):
  q=decision_receipt();q['result']['row_context_reference_key']=actor+1;call('wrong-decision-actor','select-decision',False,query=q,extra=['--decision-key','lyd_study_decision'])
 def test_24_detail_key(self):
  q=decision_receipt();q['result']['detail_decision_key']='lyd_change_school_decision';call('wrong-detail-key','confirm-decision',False,query=q,extra=['--decision-key','lyd_study_decision','--event-definition','lyd.106'])
 def test_25_no_query_business(self):call('missing-query','select-event',False,extra=EVENT)
 def test_26_stale_date(self):
  q=event_receipt();q['result']['date_raw']=date+1;call('stale-date','select-event',False,query=q,extra=EVENT)

ast.parse(A.candidate.read_bytes(),filename=str(A.candidate))
help_argv=[sys.executable,'-B','-X','utf8',str(A.candidate),'--help'];h=subprocess.run(help_argv,capture_output=True)
(SUITE/'help.stdout.original').write_bytes(h.stdout);(SUITE/'help.stderr.original').write_bytes(h.stderr)
with (SUITE/'unittest.stderr.original').open('w',encoding='utf-8',newline='\n') as f:r=unittest.TextTestRunner(stream=f,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Contract))
summary={'candidate':ref(A.candidate),'test_source':ref(Path(__file__)),'tests_run':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'passed':r.testsRun-len(r.failures)-len(r.errors),'AST_parse':True,'help_exit':h.returncode,'help_stdout':ref(SUITE/'help.stdout.original'),'help_stderr':ref(SUITE/'help.stderr.original'),'unittest_stderr':ref(SUITE/'unittest.stderr.original'),'calls':CALLS,'actual_I4_query':None,'futureT':None,'fixture_runtime_or_formal_credit':None,'SDK_native_game_calls':0,'save_body_reads':0,'main_writes':0}
summaryref=put(SUITE/'RESULT.fixture.json',summary)
print(json.dumps({'summary':summaryref,'tests_run':r.testsRun,'passed':summary['passed'],'failures':len(r.failures),'errors':len(r.errors),'failed_tests':[x[0].id() for x in r.failures+r.errors],'help_exit':h.returncode,'AST':True}));raise SystemExit(0 if r.wasSuccessful() and h.returncode==0 else 1)

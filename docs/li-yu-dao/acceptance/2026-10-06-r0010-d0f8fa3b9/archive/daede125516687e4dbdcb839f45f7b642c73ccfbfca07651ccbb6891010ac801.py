"""Focused offline tests of new assembler against preserved actual R10 data."""
from pathlib import Path
import copy, importlib.util, json, sys, traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parent;B=ROOT.parent
spec=importlib.util.spec_from_file_location('_proposal_file_assembler',ROOT/'assemble_proposal_inputs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def load(path):return json.loads(Path(path).read_bytes())
flow=load(B/'r10-fifth-proposal-proof-inputs-20261005-002/FLOW-REQUEST.actual-post-bind.json')
em=load(B/'r10-fifth-proposal-proof-inputs-20261005-002/EMIT-REQUEST.actual.json')
before=load(em['before_artifact']['path']);after=load(em['after_artifact']['path'])
req={'schema':'lyd.r10.proposal-input-assembly-request.v1','phase':'finish_emit',
    'claim':flow['claim'],'packet':flow['packet'],'native_result':flow['native_result'],
    'before_save':before['save'],'before_checkpoint_sdk':flow['before_checkpoint_sdk'],
    'after_save':after['save'],'after_checkpoint_sdk':flow['after_checkpoint_sdk'],
    'first_query_sdk':flow['first_query_sdk'],'first_query_frame_sdk':flow['first_query_frame_sdk'],
    'current_query_sdk':flow['current_query_sdk'],'current_query_frame_sdk':flow['current_query_frame_sdk'],
    'bound_index':em['bound_verifier_index'],'output':str(ROOT/'offline-finish-assembly'),
    'bound_output':flow['bound_output'],'flow_output':str(ROOT/'offline-unused-flow'),
    'evidence_output':str(ROOT/'offline-unused-evidence'),'operator_id':flow['operator_id'],
    'next_intent_id':flow['next_intent_id'],'open_readback':None}
results=[]
try:
    checked=m.validate(req);results.append({'case':'actual_ordinal4_finish_validate','PASS':True,'ordinal':checked['claim']['claim_ordinal']})
    bind=copy.deepcopy(req);bind['phase']='prepare_bind';bind['bound_index']=None;bind['bound_output']=str(ROOT/'offline-never-created-bound');bind['output']=str(ROOT/'offline-bind-assembly');bind['current_query_sdk']=None;bind['current_query_frame_sdk']=None;bind['next_intent_id']=None
    m.validate(bind);results.append({'case':'actual_ordinal4_prepare_bind_validate','PASS':True})
    cases=[
        ('unknown_auto_select',lambda r:r.__setitem__('auto_select',True)),
        ('saved_bool_bytes',lambda r:r['before_save'].__setitem__('bytes',True)),
        ('wrong_bound_SHA',lambda r:r['bound_index'].__setitem__('sha256','0'*64)),
        ('stale_current_first_query',lambda r:(r.__setitem__('current_query_sdk',r['first_query_sdk']),r.__setitem__('current_query_frame_sdk',r['first_query_frame_sdk']))),
        ('wrong_current_frame',lambda r:r.__setitem__('current_query_frame_sdk',r['first_query_frame_sdk'])),
        ('wrong_prior_packet',lambda r:r.__setitem__('packet',load(B/'r10-fourth-proposal-proof-inputs-20261005-002/FLOW-REQUEST.actual-post-bind.json')['packet'])),
        ('wrong_prior_first_query',lambda r:(r.__setitem__('first_query_sdk',load(B/'r10-fourth-proposal-proof-inputs-20261005-002/FLOW-REQUEST.actual-post-bind.json')['first_query_sdk']),r.__setitem__('first_query_frame_sdk',load(B/'r10-fourth-proposal-proof-inputs-20261005-002/FLOW-REQUEST.actual-post-bind.json')['first_query_frame_sdk']))),
        ('reuse_request_as_next_intent',lambda r:r.__setitem__('next_intent_id',checked['claim']['request_id'])),
        ('live_runtime_write_target',lambda r:r.__setitem__('output',str(B/'live-attempt-010/forbidden-helper-output'))),
        ('missing_finish_current',lambda r:(r.__setitem__('current_query_sdk',None),r.__setitem__('current_query_frame_sdk',None)))]
    for label,mutate in cases:
        bad=copy.deepcopy(req);mutate(bad)
        try:m.validate(bad)
        except ValueError as error:results.append({'case':label,'PASS':True,'rejected_reason':str(error)})
        else:raise ValueError('invalid control accepted: '+label)
    for request in (bind,req):
        result=m.assemble(request);results.append({'case':request['phase']+'_actual_offline_file_assembly','PASS':True,'result':result})
    finish=Path(req['output']);generated=load(finish/'EMIT-REQUEST.actual.json')
    if generated['bound_verifier_index']!=em['bound_verifier_index'] or generated['claim']!=em['claim']:raise ValueError('actual source/claim index changed')
    for role in ('before','after'):
        original=before if role=='before' else after
        if load(finish/(role.upper()+'-OBSERVATION.actual.json'))!=original:raise ValueError('actual observation semantic fields changed')
    results.append({'case':'actual_emission_and_observation_fields_match_manual_fifth','PASS':True})
    status='PASS'
except Exception:
    status='FAIL';results.append({'case':'failure','traceback':traceback.format_exc()})
with (ROOT/'FOCUSED-RESULT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump({'status':status,'scope':'NEW_ASSEMBLER_ACTUAL_PRESERVED_DATA_ONLY_NO_GAME_OR_BUSINESS_VERIFIER','results':results,'binder_emitter_release_MCP_calls':0},f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':status,'checks':len(results),'report':str(ROOT/'FOCUSED-RESULT.json')}))
raise SystemExit(0 if status=='PASS' else 1)

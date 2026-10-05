"""Only new metadata gates: preserved actual SDK contexts with inert SDK seam."""
from pathlib import Path
import copy,hashlib,importlib.util,json,sys,traceback
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent
spec=importlib.util.spec_from_file_location('_assembler003',P/'assemble_proposal_inputs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def load(path):return json.loads(Path(path).read_bytes())
flow=load(B/'r10-fifth-proposal-proof-inputs-20261005-002/FLOW-REQUEST.actual-post-bind.json')
claim=load(flow['claim']['path']);identity=claim['action_identity'];provenance=claim['host_provenance']
qref=flow['current_query_sdk'];fref=flow['current_query_frame_sdk'];qactual=load(qref['path'])['structuredContent'];factual=load(fref['path'])['structuredContent']
inputs=[]
for ref in (qref,fref,flow['claim']):
    raw=Path(ref['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==ref['sha256'];inputs.append(dict(ref,bytes=len(raw)))
results=[]
def invoke(q,f,*,own=False):
    fixtures={qref['path']:q,fref['path']:f}
    def inert_sdk(ref,cache):return copy.deepcopy(fixtures[ref['path']])
    m.sdk=inert_sdk
    return m.query(qref,None if own else fref,{},identity,provenance)
def reject(label,q,f):
    try:invoke(q,f)
    except ValueError as e:results.append({'case':label,'PASS':True,'rejected_reason':str(e)})
    else:raise ValueError('wrong metadata admitted: '+label)
try:
    got=invoke(qactual,factual);assert got['revision']==59 and got['native_revision']==58
    results.append({'case':'actual_preserved_external_frame_positive','PASS':True})
    both=copy.deepcopy(qactual);both['snapshot']=copy.deepcopy(factual['snapshot_after']);invoke(both,factual,own=True)
    results.append({'case':'actual_metadata_own_frame_shape_positive','PASS':True})
    for key in ('profile_sha256','session_id','pipe_name'):
        q=copy.deepcopy(qactual);f=copy.deepcopy(factual);f[key]='foreign-'+key;reject('foreign_frame_'+key,q,f)
    controls=[
        ('wrong_full_frame_actor',lambda q,f:f['snapshot_after']['played_character'].__setitem__('character_id',65866)),
        ('frame_actor_dead',lambda q,f:f['snapshot_after']['played_character'].__setitem__('alive',False)),
        ('frame_actor_bool_fullID',lambda q,f:f['snapshot_after']['played_character'].__setitem__('character_id',True)),
        ('frame_actor_non_native',lambda q,f:f['snapshot_after']['played_character'].__setitem__('source','fixture')),
        ('context_actor_dead',lambda q,f:q['result']['character_interaction_ordinary_context'].__setitem__('actor_alive',False)),
        ('context_recipient_dead',lambda q,f:q['result']['character_interaction_ordinary_context'].__setitem__('recipient_alive',False)),
        ('frame_non_native_source',lambda q,f:f['snapshot_after'].__setitem__('source','fixture')),
        ('frame_wrong_backend',lambda q,f:f['snapshot_after'].__setitem__('backend_id','fixture')),
        ('frame_bool_format',lambda q,f:f['snapshot_after'].__setitem__('format_version',True)),
        ('context_non_native_source',lambda q,f:q['result']['character_interaction_ordinary_context'].__setitem__('source','fixture')),
        ('frame_disconnected',lambda q,f:f['snapshot_after']['diagnostics'].__setitem__('connected',False)),
        ('frame_wrong_pipe',lambda q,f:f['snapshot_after']['diagnostics'].__setitem__('pipe_name','foreign-pipe')),
        ('frame_bool_generation',lambda q,f:f['snapshot_after']['diagnostics'].__setitem__('connection_generation',True)),
        ('frame_active_event',lambda q,f:f['snapshot_after'].__setitem__('active_event',{'instance_id':1})),
        ('frame_pending_incoming',lambda q,f:f['snapshot_after'].__setitem__('pending_character_interaction',{'instance_id':1})),
        ('frame_bool_date',lambda q,f:f['snapshot_after'].__setitem__('date_raw',True)),
        ('context_not_ready_control',lambda q,f:q['result']['character_interaction_ordinary_context'].__setitem__('ready_to_initiate',False))]
    for label,mutate in controls:
        q=copy.deepcopy(qactual);f=copy.deepcopy(factual);mutate(q,f);reject(label,q,f)
    base={'phase':'prepare_bind','output':str(P/'never-created-assembly'),'flow_output':str(P/'never-created-flow'),'evidence_output':str(P/'never-created-evidence'),'bound_output':str(P/'never-created-bound')}
    m.distinct_output_paths(base);results.append({'case':'fresh_distinct_outputs_positive','PASS':True})
    finished=dict(base,phase='finish_emit',bound_output=flow['bound_output']);m.distinct_output_paths(finished);results.append({'case':'finished_bound_separate_from_fresh_outputs_positive','PASS':True})
    for label,field,target in (('assembly_flow_alias','flow_output','output'),('flow_evidence_alias','evidence_output','flow_output'),('assembly_bound_alias','bound_output','output'),('canonical_alias','flow_output','output')):
        r=dict(base);r[field]=r[target] if label!='canonical_alias' else str(Path(r[target])/'..'/Path(r[target]).name)
        try:m.distinct_output_paths(r)
        except ValueError as e:results.append({'case':label,'PASS':True,'rejected_reason':str(e)})
        else:raise ValueError('output alias admitted: '+label)
    status='PASS'
except Exception:
    status='FAIL';results.append({'case':'failure','traceback':traceback.format_exc()})
report={'status':status,'scope':'NEW_ACTUAL_QUERY_FRAME_METADATA_GATES_AND_DISTINCT_PATHS_ONLY','source_sha256':hashlib.sha256((P/'assemble_proposal_inputs.py').read_bytes()).hexdigest(),'actual_preserved_input_refs':inputs,'actual_functions':['query','frame_identity','distinct_output_paths','output_path'],'seam':'SDK raw reads replaced with deep-copied preserved structured metadata; core validation functions actual candidate','results':results,'old_tests_run':0,'full_validate_or_assemble_calls':0,'save_AST_or_raw_save_hash_reads':0,'provider_binder_emitter_host_MCP_game_calls':0,'actual_business_or_consumption_credit':False}
with (P/'DIRECTED-RESULT.json').open('x',encoding='utf-8',newline='\n') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps({'status':status,'checks':len(results),'report':str(P/'DIRECTED-RESULT.json')}))
raise SystemExit(0 if status=='PASS' else 1)

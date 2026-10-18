"""Same public CaseClient, original MCP query, full result from its existing wire.

This common case adapter neither opens an SDK nor
changes the original common runtime, Driver or MCP result. Derived queried_*
fields explicitly bind the two actual host frames; they are not a Driver copy.
"""
from pathlib import Path
import copy,hashlib,json

def require(ok,why):
    if not ok:raise ValueError(why)

def bind_common_frame(frame,expected_run_id):
    # A derived consumer view; the original native/public row is retained unchanged.
    binding=frame.get('managed_campaign_run_binding')
    require(isinstance(binding,dict) and binding.get('run_id')==expected_run_id,
        'actual managed campaign run binding differs')
    episode=frame.get('episode_run_id')
    require(episode is None or episode==expected_run_id,'top-level episode conflicts with actual managed run binding')
    return {**frame,'episode_run_id':expected_run_id,
        'research_derived_episode_binding':{'source':'managed_campaign_run_binding.run_id',
            'run_id':expected_run_id,'original_top_level_episode_present':'episode_run_id' in frame,
            'original_public_snapshot_modified':False}}

def identity(f):
    d=f.get('diagnostics',{});p=f.get('played_character',{})
    return (d.get('bridge_pid'),d.get('connection_generation'),p.get('character_id'),f.get('episode_run_id'))

def normalized_full(raw,compact,before,after,*,army_ids,profile):
    from xar_autoplayer.bridge.army_strengths_manager_shared_wire import expand_army_strengths_manager_inputs
    from xar_autoplayer.bridge.army_strengths_profile_contract import validate_army_strengths_profile_coverage
    from xar_autoplayer.bridge.war_contract import army_strength_scope,normalize_army_strengths,army_strength_query_status
    require(all(f.get('paused') is True and f.get('map_ready') is True and f.get('played_character',{}).get('alive') is True for f in (before,after)),
        'full wire recovery requires actual living paused ready frames')
    require(identity(before)==identity(after) and all(before.get(k)==after.get(k) for k in ('revision','native_revision','snapshot_id','date_raw')),
        'native army-strength query crossed a snapshot revision')
    scope=army_strength_scope(before);require(scope==army_strength_scope(after),'full wire recovery published scope changed')
    selected={x['army_id']:x for x in scope}
    require(len(set(army_ids))==len(army_ids) and all(i in selected for i in army_ids),'full wire recovery Army scope differs')
    require(compact.get('result_location')=='compact_mcp_summary' and compact.get('source')=={'revision':before['revision'],'native_revision':before['native_revision']},
        'actual compact source does not match its paired frames')
    require(raw.get('step')=='query-army-strengths-v1' and raw.get('accepted') is True and raw.get('status') in ('available','partial') and
        raw.get('query_sequence')==compact.get('query_sequence') and raw.get('army_strengths_profile')==profile,'native full query status/sequence differs')
    echo=raw.get('army_strengths_query_scope')
    require(isinstance(echo,dict) and echo.get('army_ids')==army_ids and echo.get('published_scope_status') in ('available','partial'),
        'native full query scope echo differs')
    expanded=expand_army_strengths_manager_inputs(raw,detached=False)
    validate_army_strengths_profile_coverage(expanded,expected_profile=profile)
    rows=normalize_army_strengths(expanded.get('army_strengths'),expected_scope=[selected[i] for i in army_ids])
    status=army_strength_query_status(rows);require(status==raw['status']==compact['status'],'native full query row status differs')
    result={**expanded,'army_strengths':rows,'status':status,
        'queried_snapshot_id':before['snapshot_id'],'queried_revision':before['revision'],
        'queried_native_revision':before['native_revision'],'queried_date_raw':before['date_raw'],
        'queried_connection_generation':before['diagnostics']['connection_generation'],'queried_episode_run_id':before['episode_run_id']}
    return result

class FullArmyResultClient:
    """Delegate every operation to the original public queue; never create SDK."""
    def __init__(self,client,wire_module=None,*,prefix=""):
        if wire_module is None:
            import ck3_mod_acceptance_army_wire as wire_module
        require(not prefix or prefix.replace('-','').replace('_','').isalnum(),'invalid common control prefix')
        self.client=client;self.wire=wire_module;self.prefix=prefix;self.frames={};self.serial=0;self.full_proofs=[]
        self.expected_run_id=client.selection.run_dir.name
    def __getattr__(self,key):return getattr(self.client,key)
    def snapshot(self,allow_actor_change=False,require_event_free=True):
        self.serial+=1;name='snapshot-'+str(self.serial).zfill(4)
        rows=self.execute_plan([{'id':name,'tool':'ck3_take_snapshot','args':{'include_native_command_history':False},'fresh_revision':True}],name)
        return self.client.validate_frame(rows[0]['result'],allow_actor_change,require_event_free)
    def execute_plan(self,steps,name,timeout=None,reserve=90):
        require(len(steps)==1,'continuation submits one original step at a time')
        step=copy.deepcopy(steps[0]);old_id=step['id'];step['id']=(self.prefix+'-' if self.prefix else '')+old_id
        plan_name=(self.prefix+'-' if self.prefix else '')+name
        full=(step.get('tool')=='ck3_query_army_strengths' and step.get('args',{}).get('profile')=='observed_history_full_v1')
        if full:
            args=step['args'];before=self.frames.get(args['expected_revision'])
            require(before is not None,'full query requires its own captured actual fresh frame')
            bookmark=self.wire.mark(self.client.report_path.with_suffix('.native-wire.jsonl'))
        rows=self.client.execute_plan([step],plan_name,timeout=timeout,reserve=reserve)
        require(len(rows)==1 and rows[0].get('id')==step['id'],'actual continuation row identity differs')
        row=rows[0]
        if row.get('ok') is True and not row.get('error'):
            if step.get('tool')=='ck3_take_snapshot':
                f=bind_common_frame(row['result'],self.expected_run_id);self.frames[f['revision']]=f
                row={**row,'result':f}
            if full:
                compact=row['result'];after=row.get('after_snapshot')
                require(isinstance(after,dict),'actual original full query has no host after_snapshot')
                after=bind_common_frame(after,self.expected_run_id)
                self.client.validate_frame(before,require_event_free=False);self.client.validate_frame(after,require_event_free=False)
                raw,proof=self.wire.recover(bookmark,compact,native_revision=before['native_revision'],army_ids=args['army_ids'],profile=args['profile'])
                proof.update(public_step_id=step['id'],public_control_name=plan_name,
                    public_original=str(self.client.output/(plan_name+'.actual-results.json')),
                    representation='derived production-normalized native wire result plus actual paired host frames; not complete Driver packet',
                    normalized_source_binding={'before':{k:before[k] for k in ('revision','native_revision','snapshot_id','date_raw','episode_run_id')},
                        'after':{k:after[k] for k in ('revision','native_revision','snapshot_id','date_raw','episode_run_id')}})
                try:
                    normalized=normalized_full(raw,compact,before,after,army_ids=args['army_ids'],profile=args['profile'])
                except ValueError as error:
                    if str(error)!='native army-strength query crossed a snapshot revision':
                        raise
                    # Preserve the accepted original public row and both frames.
                    # Only this derived full consumer failed. Existing R05
                    # readonly recovery can then apply its single-fresh-query
                    # same-date/identity contract; this helper never retries.
                    proof['derived_error']=str(error)
                    proof['original_public_row_ok']=row['ok']
                    self.full_proofs.append(proof)
                    self.client.checkpoint(plan_name+'-full-wire-proof',proof)
                    row={**row,'ok':False,'error':str(error),'derived_full_result_error':True,'wire_full_result_proof':proof}
                else:
                    self.full_proofs.append(proof)
                    self.client.checkpoint(plan_name+'-full-wire-proof',proof)
                    # The original compact control receipt remains unchanged.
                    self.client.checkpoint(plan_name+'-derived-normalized-full',normalized)
                    row={**row,'result':normalized,'wire_full_result_proof':proof}
        elif full:
            from xar_autoplayer.bridge.r05_supply_observation_case import classify_strength_pre_snapshot_not_started
            diagnostic=classify_strength_pre_snapshot_not_started(row)
            if diagnostic is not None:
                proof={'diagnostic':diagnostic,'source':'completed_native_pre_snapshot_rejected_before_submit',
                    'public_step_id':step['id'],'public_control_name':plan_name,
                    'public_original':str(self.client.output/(plan_name+'.actual-results.json')),
                    'query_reissued':False,'native_query_started':False}
                self.client.checkpoint(plan_name+'-not-started-proof',proof)
                row={**row,'full_query_not_started_v1':proof}
        # Consumers retain their original stepID semantics; physical public row
        # and control-plan IDs are separately pinned in the original receipt.
        return [{**row,'id':old_id,'continuation_public_step_id':step['id']}]

def ensure_common_full_army_client(client):
    """Wrap the actual compact public CaseClient once; retain injected full DTO boundaries."""
    if isinstance(client,FullArmyResultClient):
        return client
    from ck3_mod_acceptance_client import CaseClient
    if isinstance(client,CaseClient):
        return FullArmyResultClient(client)
    # Existing adapters' dependency injection can already supply full DTOs.
    # An InitializerBudget delegates to its already wrapped common client.
    return client

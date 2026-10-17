"""Stdlib replay of the complete portable R194 census and production consumer.

No SDK, source discovery, EXE or Driver read. Explicit checks remain under -O.
"""
from __future__ import annotations
import hashlib,importlib.util,json,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
CHILD='definition_frontier_continuation_depth8_12'
def need(ok,why):
    if not ok:raise ValueError(why)
def unique(pairs):
    value={}
    for key,item in pairs:
        need(key not in value,'duplicate JSON key: '+key);value[key]=item
    return value
def load(name):return json.loads((HERE/name).read_bytes(),object_pairs_hook=unique)
def main():
    pins=load('PORTABLE-PINS.actual.json')
    for row in pins['files']:
        p=(HERE/row['relative_path']).resolve()
        need(p.is_relative_to(HERE),'portable file escaped root')
        raw=p.read_bytes()
        need(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'portable pin differs '+row['relative_path'])
    package=types.ModuleType('r194_production_consumer');package.__path__=[str(HERE/'consumer')];sys.modules[package.__name__]=package
    from r194_production_consumer.gui_callback_binding_12004_contract import SOURCE_RECEIVER_12004,normalize_callback_binding_rows_12004
    from r194_production_consumer.gui_refill_receiver_candidates_12004_contract import normalize_receiver_frame
    identity=load('IDENTITY.actual.json');request=load('OPENER-REQUEST.actual.json');endpoint=load('OPENER-ENDPOINT.actual.json')
    before=load('BEFORE-FRAME.actual.json');fence=load('FENCE-FRAME.actual.json');run=load('OPENER-RESULT.actual.json');saved=load('FRONTIER.actual.json')
    machine='desktop-3fevhd2-1c74096080';head='d7135ca3bf40c33c2d5416242ce844077f1e8cbe'
    need(all(x['machine_id']==machine for x in (identity,endpoint,before,fence,run,saved)),'machine mismatch')
    need(identity['source_head']==identity['native_build_source_head']==run['source_head']==head,'runtime source mismatch')
    need(identity['pid']==30444 and identity['process_creation_filetime_100ns']==134366683524856952 and identity['connection_generation']==1,'process lifetime mismatch')
    need(identity['actual_runtime_character_full_id']==31254 and identity['episode_run_id']=='native-31254-1aff01c8cf5c','actor/episode mismatch')
    need(before['frame']==fence['frame'],'independent before/fence mismatch')
    public=before['frame'].copy();date=public.pop('date_raw')
    need(public==dict(snapshot_id='native:5',revision=6,native_revision=5,episode_run_id=identity['episode_run_id']) and date==53146632,'actual public/date differs')
    need(request==dict(request_id='r0194-r06-postfilm-a01-open-once',tool='ck3_execute_step',arguments=dict(step='activate-ingame-military-v1',expected_revision=6)),'not the single admitted request')
    body=endpoint['body'];tree=body['later_military_tree']
    need(endpoint['is_error'] is False and endpoint['request_id']==request['request_id'],'opener response identity')
    need(body['status']=='verified_visible' and body['postcondition_verified'] is True and body['verification_pending'] is False and body['queried_revision']==6 and body['episode_run_id']==public['episode_run_id'],'opener postcondition')
    need(run['status']=='OPENER_VERIFIED_AND_FENCED_SOURCE_ONLY' and run['SDK_relay_top_level_requests']==3 and run['top_level_opener_calls']==1 and run['fence_verified'] is True,'three-request actual execution not verified')
    for key in ('tree_query_submitted','Move_or_Resume_submitted','close_attempted','Driver_raw_read','provider_execution','native_receiver_selected'):
        need(run[key] is False,'unadmitted operation claimed '+key)
    endpoint_pin=next(row for row in pins['files'] if row['relative_path']=='OPENER-ENDPOINT.actual.json')
    need(all(run['endpoint'][k]==endpoint_pin[k] for k in ('bytes','sha256')),'Root result endpoint pin differs')
    projection=endpoint['projection']
    need(projection['all_callback_rows_retained'] is True and projection['retained_widget_count']==len(tree['widgets']) and projection['Driver_raw_read'] is False,'complete census projection not retained')
    need(tree['callback_binding_source_12004']==SOURCE_RECEIVER_12004 and tree['root_available'] is True and tree['truncated'] is False,'exact complete military source')
    frame=normalize_receiver_frame(tree['refill_receiver_frame_12004'])
    need(all(frame[k]==v and type(frame[k]) is type(v) for k,v in dict(game_pid=30444,connection_generation=1,native_revision=5,played_character_full_id=31254,date_raw=date).items()),'native family frame mismatch')
    need(tree['refill_receiver_public_binding_12004']==public and saved['frame']==frame and saved['public_binding']==public,'family public binding mismatch')
    clean=normalize_callback_binding_rows_12004(tree,{'widgets':[dict(w) for w in tree['widgets']]})
    matches=[]
    for index,widget in enumerate(clean['widgets']):
        for callback in widget['standard_click_binding_12004']['callbacks']:
            expression=callback.get('indirect_target_3aa30e0',{}).get('expression_3a9f960',{})
            full=expression.get('receiver_entry_candidates_12004')
            if full is not None:matches.append((index,widget,callback,full))
    need(len(matches)==2 and len(saved['candidates'])==2,'actual fixed source leaf count differs')
    source_results=[]
    for (index,widget,callback,full),result in zip(matches,saved['candidates'],strict=True):
        need(full['status']=='unavailable' and full['unavailable_reason']=='candidate_parent_depth_exhausted','legacy full failure was changed')
        failure=full['failure_diagnostic']
        need((failure['capture_pass'],failure['read_ordinal'],failure['ancestor_depth'])==(1,51,8),'legacy failure diagnostic differs')
        prefix=full['definition_chain_prefix_depth8'];tail=full[CHILD]
        need(prefix['status']=='available' and prefix['stable_double_read'] is True and [r['ancestor_depth'] for r in prefix['rows']]==list(range(8)),'stable original prefix missing')
        need(all(r['parent_edge']=='context_e8' and r['parent_present'] is True for r in prefix['rows']),'observed prefix edges differ')
        need(tail['status']=='available' and tail['stable_double_read'] is True and tail['stop_depth']==8 and tail['stop_reason']=='static_direct_terminal' and tail['next_context_present'] is None,'new actual static stop differs')
        need(len(tail['rows'])==1,'native static stop must not read descendants9..11')
        row=tail['rows'][0]
        need((row['ancestor_depth'],row['definition_present'],row['raw_definition_entry_count'],row['first_match_entry_index'],row['parent_edge'],row['parent_present'])==(8,True,3,0,'not_read_native_static_stop',None),'actual depth8 source differs')
        need(len(row['entries'])==1,'only first key635 match may be published')
        entry=row['entries'][0]
        need(entry==dict(ancestor_depth=8,entry_type_48=635,entry_mode_40=1,entry_flag_4c=1,direct_value_present=True,provider_present=False,provider_vtable_rva=None,provider_slot2_rva=None,direct_owner_full_id=31254,direct_owner_identity_verified=True),'actual direct branch differs')
        need(all(tail[k] is False for k in ('current_variable_table_observed','native_receiver_selected','provider_invoked')),'source segment overclaims executed receiver')
        need(result['widget_index']==index and result['callback_index']==callback['index'] and result['prefix']==prefix and result['continuation']==tail,'saved extraction differs from complete census strict result')
        source_results.append(dict(widget_index=index,child_path=widget['child_path'],effective_visible=widget['effective_visible'],depth=8,static_direct_owner_full_id=31254,parent_not_read_after_native_static_stop=True))
    need([(r['widget_index'],r['effective_visible']) for r in source_results]==[(220,True),(238,False)],'actual visible/hidden source leaves differ')
    need(saved['status']=='GUI_FAMILY_STRICTLY_CONSUMED' and saved['eligible_source_provider_slot2_rvas']==[] and saved['eligible_source_provider_slot2_rvas_hex']==[],'provider RVA collection differs')
    need(saved['used_family_source']=='endpoint' and not any(r['role']=='driver' for r in saved['input_reads']),'Driver fallback was used')
    need(all(r['body_read_count']==1 and r['hash_and_parse_use_same_bytes'] is True for r in saved['input_reads']),'analysis read/parse contract differs')
    need(saved['actual_budget_totals_exported'] is False and all(saved[k] is None for k in ('actual_total_reads','actual_total_bytes','actual_elapsed_ms')),'unobserved budget totals fabricated')
    print(json.dumps(dict(status='PASS',evidence_layer='actual source segment and independent frame fence; no executed receiver or refill business qualification',machine_id=machine,all_census_rows_strictly_consumed=len(clean['widgets']),source_results=source_results,eligible_provider_RVAs=[],source_qualified_static_direct_matches=2,Driver_reads=0,SDK_calls=0,assert_required=False),ensure_ascii=False))
if __name__=='__main__':main()

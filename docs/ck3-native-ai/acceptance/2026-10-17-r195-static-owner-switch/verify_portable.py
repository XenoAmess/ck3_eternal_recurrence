"""Replay exact gzipped original bytes with copied production strict consumer.

Stdlib only. No SDK/Driver/EXE lookup. Every check survives python -O.
"""
import gzip,hashlib,json,pathlib,sys,types
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
def need(ok,why):
    if not ok:raise ValueError(why)
def unique(pairs):
    out={}
    for key,value in pairs:
        need(key not in out,'duplicate JSON key');out[key]=value
    return out
def load(name):return json.loads((HERE/name).read_bytes(),object_pairs_hook=unique)
def main():
    pins=load('PORTABLE-PINS.actual.json')
    for item in pins['files']:
        path=(HERE/item['relative_path']).resolve();need(path.is_relative_to(HERE),'portable source escaped root')
        raw=path.read_bytes();need(len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'portable pin changed '+item['relative_path'])
    packet=load('PACKET.actual.json');original=packet['raw_endpoint_pin']
    need(original['bytes']==239540 and original['sha256']=='4327754594ed01fa69d74589cb7a49f23b0e425c2146548c687cdda010d9ecdf','Root endpoint source pin differs')
    with gzip.open(HERE/packet['gzip_file'],'rb') as stream:raw=stream.read(original['bytes']+1)
    need(len(raw)==original['bytes'] and hashlib.sha256(raw).hexdigest()==original['sha256'],'gzip did not preserve original endpoint bytes')
    endpoint=json.loads(raw,object_pairs_hook=unique)
    before=load('BEFORE-FRAME.actual.json');fence=load('FENCE-FRAME.actual.json');proof=load('IDENTITY.actual.json');result=load('RESULT.actual.json');request=load('REQUEST.actual.json');claim=load('CLAIM.actual.json');saved=load('ACTUAL.json')
    machine='desktop-3fevhd2-1c74096080';source='611bc985ae95f477dd7314df11f8602cd1e595f3'
    need(all(row['machine_id']==machine for row in (packet,endpoint,before,fence,proof,result,claim,saved)),'machine mismatch')
    need(proof['source_head']==proof['native_build_source_head']==result['source_head']==source==saved['source_head'],'runtime/native source mismatch')
    need(proof['pid']==29000 and proof['process_creation_filetime_100ns']==134366728035105406 and proof['connection_generation']==1 and proof['actual_runtime_character_full_id']==31254,'actual lifetime/actor mismatch')
    need(before['frame']==fence['frame'],'independent Root frame fence mismatch')
    public=before['frame'].copy();date=public.pop('date_raw')
    need(date==53148960 and public==dict(snapshot_id='native:109',revision=110,native_revision=109,episode_run_id='native-31254-d5ea28d864bc') and proof['episode_run_id']==public['episode_run_id'],'actual frame differs')
    need(result['status']=='OPENER_VERIFIED_AND_FENCED_SOURCE_ONLY' and result['SDK_relay_top_level_requests']==3 and result['top_level_opener_calls']==1 and result['fence_verified'] is True,'original actual transaction incomplete')
    for key in ('Driver_raw_read','tree_query_submitted','Move_or_Resume_submitted','close_attempted','provider_execution','native_receiver_selected'):
        need(result[key] is False,'unadmitted actual operation '+key)
    need(all(result['endpoint'][k]==original[k] for k in ('bytes','sha256')),'result endpoint pin mismatch')
    need(request==dict(request_id='r0195-r06-control-a01-open-once',tool='ck3_execute_step',arguments=dict(step='activate-ingame-military-v1',expected_revision=110)),'actual request mismatch')
    need(endpoint['request_id']==request['request_id'] and endpoint['is_error'] is False,'actual endpoint response mismatch')
    body=endpoint['body'];tree=body['later_military_tree']
    need(body['status']=='verified_visible' and body['postcondition_verified'] is True and body['verification_pending'] is False and body['queried_revision']==110 and body['episode_run_id']==public['episode_run_id'],'actual military opener postcondition')
    need(endpoint['projection']['all_callback_rows_retained'] is True and endpoint['projection']['retained_widget_count']==len(tree['widgets']) and endpoint['projection']['Driver_raw_read'] is False,'entire callback census not preserved')
    module=types.ModuleType('portable_r195_consumer');module.__path__=[str(HERE/'consumer')];sys.modules[module.__name__]=module
    from portable_r195_consumer.gui_callback_binding_12004_contract import SOURCE_RECEIVER_12004,normalize_callback_binding_rows_12004
    from portable_r195_consumer.gui_refill_receiver_candidates_12004_contract import normalize_receiver_frame
    need(tree['callback_binding_source_12004']==SOURCE_RECEIVER_12004 and tree['root_available'] is True and tree['truncated'] is False,'complete exact receiver family differs')
    frame=normalize_receiver_frame(tree['refill_receiver_frame_12004'])
    expected=dict(game_pid=29000,connection_generation=1,native_revision=109,played_character_full_id=31254,date_raw=53148960)
    need(all(type(frame[k]) is type(value) and frame[k]==value for k,value in expected.items()) and tree['refill_receiver_public_binding_12004']==public,'GUI native/public frame mismatch')
    clean=normalize_callback_binding_rows_12004(tree,{'widgets':[dict(w) for w in tree['widgets']]})
    need(len(clean['widgets'])==507,'all actual census rows required')
    observed=[]
    for index,widget in enumerate(clean['widgets']):
        for callback in widget['standard_click_binding_12004']['callbacks']:
            expression=callback.get('indirect_target_3aa30e0',{}).get('expression_3a9f960',{});full=expression.get('receiver_entry_candidates_12004')
            if full is None:continue
            need(full['status']=='unavailable' and full['unavailable_reason']=='candidate_parent_depth_exhausted','legacy full candidate improperly promoted')
            fail=full['failure_diagnostic'];need((fail['ancestor_depth'],fail['read_ordinal'],fail['capture_pass'])==(8,51,1),'legacy failure changed')
            tail=full['definition_frontier_continuation_depth8_12'];leaf=tail['static_direct_owner_switch_12004']
            need(tail['status']=='available' and tail['stable_double_read'] is True and tail['stop_reason']=='static_direct_terminal' and tail['stop_depth']==8 and len(tail['rows'])==1,'actual source static terminal differs')
            row=tail['rows'][0];entry=row['entries'][0]
            need(row['first_match_entry_index']==0 and row['raw_definition_entry_count']==3 and row['parent_edge']=='not_read_native_static_stop' and row['parent_present'] is None,'actual depth8 first match differs')
            need(entry['entry_mode_40']==1 and entry['entry_flag_4c']==1 and entry['direct_value_present'] is True and entry['provider_present'] is True and entry['provider_vtable_rva'] is None and entry['provider_slot2_rva'] is None and entry['direct_owner_full_id']==31254 and entry['direct_owner_identity_verified'] is True,'actual mode1/direct/provider-presence distinction differs')
            need(leaf['status']=='available' and leaf['stable_double_read'] is True and leaf['ancestor_depth']==8 and leaf['owner_full_id']==31254 and leaf['military_component_present'] is True and leaf['raw_byte_4a9']==1 and leaf['enabled'] is True and leaf['value_basis']=='raw_military_byte','actual source owner switch differs')
            need(all(leaf[k] is False and tail[k] is False for k in ('current_variable_table_observed','native_receiver_selected','provider_invoked')),'source leaf overclaims final receiver execution')
            observed.append((index,widget['effective_visible'],tail,leaf))
    need([(row[0],row[1]) for row in observed]==[(220,True),(238,False)],'actual visible/hidden source positions differ')
    need(saved['all_census_rows']==507 and saved['frame']==frame and saved['public_binding']==public and saved['new_available_leaf_count']==2,'saved actual summary differs')
    for got,expected in zip(observed,saved['candidates'],strict=True):
        need(got[0]==expected['widget_index'] and got[2]==expected['continuation'] and got[3]==expected['new_switch'],'saved strict source summary mismatch')
    need(all(row['body_reads']==1 and row['same_bytes_hash_and_parse'] is True for row in saved['input_reads']),'actual analysis input contract differs')
    need(saved['Driver_reads']==0 and saved['SDK_calls_by_consumer']==0 and saved['actual_budget_totals_exported'] is False,'unobserved Driver/budget facts fabricated')
    print(json.dumps(dict(status='PASS_ACTUAL_FULL_CENSUS_STATIC_SOURCE_SWITCH',machine_id=machine,census_rows=507,available_source_switches=2,raw_byte_4a9=1,enabled=True,owner_full_id=31254,source_only=True,provider_pointer_present_but_mode1_not_dispatched=True,selected_receiver_qualified=False,toggle_or_ADD_qualified=False,Driver_reads=0,SDK_calls=0,assert_required=False)))
if __name__=='__main__':main()

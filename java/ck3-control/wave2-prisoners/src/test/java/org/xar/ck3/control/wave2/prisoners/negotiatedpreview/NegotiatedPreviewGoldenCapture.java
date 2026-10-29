package org.xar.ck3.control.wave2.prisoners.negotiatedpreview;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.TimeUnit;

/** Explicit original contract capture; normal JUnit never launches Python. */
public final class NegotiatedPreviewGoldenCapture {
    private NegotiatedPreviewGoldenCapture() { }

    private static final String SCRIPT = """
            import copy,datetime,hashlib,json,pathlib,sys
            root, machine = pathlib.Path(sys.argv[1]), sys.argv[2]
            sys.path.insert(0,str(root/'ck3_autonomous_player/src'))
            from xar_autoplayer.bridge.prisoner_negotiated_preview_contract_12003 import normalize_prisoner_negotiated_preview_12003,release_option_mask_12003
            from xar_autoplayer.bridge.prisoner_release_preview_contract_12003 import RELEASE_OPTION_KEYS_12003,RELEASE_COST_KEYS_12003
            from xar_autoplayer.bridge.prisoner_selected_quote_source_contract_12004 import normalize_prisoner_selected_quote_source_12004,SHA
            from xar_autoplayer.bridge.prisoner_negotiated_quote_result_12004 import consume_prisoner_negotiated_quote_result_12004
            frame=dict(native_revision=1014,date_raw=53286360,player_character_id=29829,prisoner_character_id=61540,requested_option_mask_bits=8)
            def seed():
                return dict(private_build=True,read_only=True,advertised=False,action_surface_present=False,status='available',requested_option_mask_bits=8,snapshot_id='native:1014',public_revision=1014,native_revision=1014,proof_epoch=721,date_raw=53286360,definition=dict(canonical_key='release_from_prison_interaction',deterministic_key_hash=0x51520123,runtime_ordinal=186),payload_shape='two_role_selected_release_options',roles=dict(actor_character_id=29829,recipient_character_id=61540),puppet_or_actor_character_id=29829,option_keys=list(RELEASE_OPTION_KEYS_12003),selected_option_mask_bits=8,can_send=True,costs=dict(raw_scale=100000,payer_role='actor',application_timing='on_send',entries=[dict(resource_key=key,raw=100001*(i+1)) for i,key in enumerate(RELEASE_COST_KEYS_12003)]),acceptance=dict(kind='native_answer',auto_accept=False,raw_scale=100000,recipient_acceptance_score_raw=5000001,recipient_answer_status_raw=0,would_accept_now=True),readiness={key:True for key in ('definition_ready','actor_ready','recipient_ready','finalized_context_ready','can_send_ready','costs_ready','acceptance_ready','same_frame_ready')})
            cases=[]
            baseline=json.dumps(seed(),ensure_ascii=False,separators=(',',':'))
            def capture(name,value,args=None,raw=None):
                args=copy.deepcopy(frame if args is None else args)
                text=json.dumps(value,ensure_ascii=False,separators=(',',':')) if raw is None else raw
                prefix=0
                while prefix<min(len(baseline),len(text)) and baseline[prefix]==text[prefix]:prefix+=1
                suffix=0
                while suffix<min(len(baseline)-prefix,len(text)-prefix) and baseline[-suffix-1]==text[-suffix-1]:suffix+=1
                end=len(text)-suffix if suffix else len(text)
                case=dict(id=name,frame=args,input_patch=dict(prefix_chars=prefix,replace_chars=len(baseline)-prefix-suffix,replacement=text[prefix:end]))
                try:
                    expected=normalize_prisoner_negotiated_preview_12003(json.loads(text),**args)
                    case['expected_canonical_sha256']=hashlib.sha256(json.dumps(expected,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()
                except ValueError as error: case.update(rejected=True,legacy_error=str(error))
                cases.append(case)
            capture('gain_hook_accepted',seed())
            p=seed();p['acceptance'].update(recipient_acceptance_score_raw=-5000002,recipient_answer_status_raw=2,would_accept_now=False);capture('gain_hook_refused',p)
            p=seed();p['can_send']=False;p['acceptance']=dict(kind='not_evaluated_unsendable',auto_accept=False);p['readiness']['acceptance_ready']=False;capture('gain_hook_native_false',p)
            p=copy.deepcopy(p);p['acceptance']['auto_accept']=True;capture('unsendable_preserves_observed_auto_accept',p)
            p={key:seed()[key] for key in ('private_build','read_only','advertised','action_surface_present','requested_option_mask_bits')};p.update(status='unavailable',unavailable_reason='not_evaluated');capture('unavailable_no_answer_fields',p)
            p=copy.deepcopy(p);p.update(unavailable_reason='requested_release_options_not_retained',observed_option_mask_bits=0);capture('gain_hook_mask_changed',p)
            p=seed();p['requested_option_mask_bits']=p['selected_option_mask_bits']=10;p['acceptance'].update(recipient_acceptance_score_raw=2500003,recipient_answer_status_raw=1);a={**frame,'requested_option_mask_bits':10};capture('renounce_claims_gain_hook',p,a)
            p=seed();p['requested_option_mask_bits']=p['selected_option_mask_bits']=32;p['acceptance']=dict(kind='auto_accept',auto_accept=True,would_accept_now=True);capture('change_prison_auto_accept',p,{**frame,'requested_option_mask_bits':32})
            p=seed();p['native_revision']=p['public_revision']=(1<<64)-1;p['snapshot_id']='native:'+str((1<<64)-1);p['proof_epoch']=(1<<64)-1;p['roles']=dict(actor_character_id=(1<<32)-1,recipient_character_id=(1<<32)-2);p['puppet_or_actor_character_id']=(1<<32)-1;p['date_raw']=-(1<<31);p['acceptance']['recipient_acceptance_score_raw']=-(1<<63);p['costs']['entries'][0]['raw']=-(1<<63);p['costs']['entries'][-1]['raw']=(1<<63)-1;capture('native_integer_width_extremes',p,{**frame,'native_revision':(1<<64)-1,'date_raw':-(1<<31),'player_character_id':(1<<32)-1,'prisoner_character_id':(1<<32)-2})
            mutations=[('missing_costs',['costs'],'remove',None),('null_costs',['costs'],'set',None),('extra_top',['unexpected'],'set',True),('advertised_true',['advertised'],'set',True),('request_mask_bool',['requested_option_mask_bits'],'set',True),('wrong_selected_mask',['selected_option_mask_bits'],'set',10),('snapshot_changed',['snapshot_id'],'set','native:1015'),('revision_float',['native_revision'],'set',1014.0),('revision_bool',['public_revision'],'set',True),('revision_string',['native_revision'],'set','1014'),('proof_zero',['proof_epoch'],'set',0),('proof_overflow',['proof_epoch'],'set',1<<64),('role_swapped',['roles','recipient_character_id'],'set',29829),('role_extra',['roles','unexpected'],'set',0),('definition_key_changed',['definition','canonical_key'],'set','ransom_interaction'),('hash_float',['definition','deterministic_key_hash'],'set',1.0),('cost_scale_float',['costs','raw_scale'],'set',100000.0),('cost_wrong_payer',['costs','payer_role'],'set','recipient'),('cost_wrong_timing',['costs','application_timing'],'set','on_accept'),('cost_raw_bool',['costs','entries',0,'raw'],'set',False),('cost_raw_float',['costs','entries',0,'raw'],'set',100001.0),('cost_raw_overflow',['costs','entries',0,'raw'],'set',1<<63),('cost_resource_changed',['costs','entries',0,'resource_key'],'set','prestige'),('answer_float',['acceptance','recipient_answer_status_raw'],'set',0.0),('answer_unknown',['acceptance','recipient_answer_status_raw'],'set',3),('answer_would_accept_conflict',['acceptance','would_accept_now'],'set',False),('score_float',['acceptance','recipient_acceptance_score_raw'],'set',5000001.0),('score_null',['acceptance','recipient_acceptance_score_raw'],'set',None),('readiness_false',['readiness','costs_ready'],'set',False),('acceptance_readiness_false',['readiness','acceptance_ready'],'set',False),('options_reordered',['option_keys'],'set',list(reversed(RELEASE_OPTION_KEYS_12003)))]
            for name,path,action,value in mutations:
                p=seed();parent=p
                for key in path[:-1]:parent=parent[key]
                if action=='remove':del parent[path[-1]]
                else:parent[path[-1]]=value
                capture(name,p)
            p=seed();capture('frame_revision_float',p,{**frame,'native_revision':1014.0})
            p=seed();capture('same_actor_and_prisoner',p,{**frame,'prisoner_character_id':29829})
            p=dict(private_build=True,read_only=True,advertised=False,action_surface_present=False,status='unavailable',requested_option_mask_bits=8,unavailable_reason='requested_release_options_not_retained',observed_option_mask_bits=8);capture('unchanged_mask_diagnostic_rejected',p)
            masks=[]
            for keys in [['gain_hook'],['renounce_claims','gain_hook'],['change_prison'],list(RELEASE_OPTION_KEYS_12003),[],['gain_hook','gain_hook'],['unknown'],[True],None]:
                row=dict(keys=keys)
                try:row['expected_mask']=release_option_mask_12003(keys)
                except ValueError as error:row.update(rejected=True,legacy_error=str(error))
                masks.append(row)
            def source_seed():
                definition,context=0x180000000,0x190000000
                native_costs=[100001*(i+1) for i in range(10)]
                copied_frame=dict(executable_sha256=SHA,module_base=0x140000000,native_revision=1014,query_sequence=23,proof_epoch=721,date_raw=53286360,jailer_full_id=29829,prisoner_full_id=61540,recipient_full_id=61540,definition_identity=definition,interaction_context_identity=context,original_scope_identity=context+8,roles_verified_in_owned_context=True,same_frame_confirmed=True)
                score=dict(producer_rva=0x3761780,score_block_identity=definition+0x1918,base_q64=5000001,modifiers_data_identity=0,modifier_count_raw_i32=0,raw_inputs_complete=True,numeric_source_ready=True,projected_q64=5000001,native_getter_called=True,native_getter_returned_output_pointer=True,native_final_output_q64=5000001,projected_value_matches_native_final=True,unavailable_reason=None,ordered_modifier_occurrences=[])
                block=definition+0x40
                costs=dict(cost_block_identity=block,numeric_source_ready=True,native_getter_called=True,clamp_nonnegative_raw_u8=0,round_raw_u8=0,projected_q64=native_costs,native_final_q64=native_costs,original_output_copied=True,original_output_q64=[0]*10,unavailable_reason=None,lanes=[dict(lane_index=i,lane_identity=block+0x40+i*0xF0,mode_c0_i32=0,raw_temp_q64=native_costs[i],branch='synthetic-copied-static',unavailable_reason=None) for i in range(10)])
                sample=dict(sample_index=0,frame=copied_frame,copied_at_existing_query_call=True,source_answer_raw_u8=0,native_answer_raw_u8=0,answer_source_ready=True,answer_effects_source_ready=False,source_auto_accept=False,native_auto_accept=False,recipient_score=score,actor_on_send_costs=costs)
                return dict(schema='prisoner-selected-quote-source-12004',schema_version=1,source_ordinal=2,quote_kind='negotiated_preview',selected_query_completed=True,unavailable_reason=None,read_only=True,native_callbacks_added=0,samples=[sample])
            source_baseline=json.dumps(source_seed(),ensure_ascii=False,separators=(',',':'))
            quote_cases=[]
            def quote_capture(name,source,preview=None):
                preview=seed() if preview is None else preview
                row=dict(id=name,source_present=source is not None)
                preview_text=json.dumps(preview,ensure_ascii=False,separators=(',',':'))
                if preview_text!=baseline:row['preview_json']=preview_text
                if source is not None:
                    text=json.dumps(source,ensure_ascii=False,separators=(',',':'))
                    prefix=0
                    while prefix<min(len(source_baseline),len(text)) and source_baseline[prefix]==text[prefix]:prefix+=1
                    suffix=0
                    while suffix<min(len(source_baseline)-prefix,len(text)-prefix) and source_baseline[-suffix-1]==text[-suffix-1]:suffix+=1
                    end=len(text)-suffix if suffix else len(text)
                    row['source_patch']=dict(prefix_chars=prefix,replace_chars=len(source_baseline)-prefix-suffix,replacement=text[prefix:end])
                try:
                    normalized=normalize_prisoner_negotiated_preview_12003(preview,**frame)
                    if source is not None: source=normalize_prisoner_selected_quote_source_12004(source,native_revision=1014,query_sequence=23,proof_epoch=721,date_raw=53286360,jailer_full_id=29829,prisoner_full_id=61540,source_ordinal=2,quote_kind='negotiated_preview')
                    row['expected']=consume_prisoner_negotiated_quote_result_12004(normalized,source,native_revision=1014,query_sequence=23,proof_epoch=721,date_raw=53286360,player_character_id=29829,prisoner_character_id=61540,source_ordinal=2,requested_option_mask_bits=8)
                except ValueError as error:row.update(rejected=True,legacy_error=str(error))
                quote_cases.append(row)
            quote_capture('same_native_and_copied_operands',source_seed())
            quote_capture('source_absent_is_not_false',None)
            s=source_seed();s['samples'][0]['recipient_score'].update(native_final_output_q64=-9,projected_value_matches_native_final=False);quote_capture('different_copied_score_does_not_override_native',s)
            s=source_seed();s['samples'][0]['actor_on_send_costs']['native_final_q64']=list(range(10));quote_capture('different_copied_costs_are_diagnostic',s)
            s=source_seed();sample=s['samples'][0];sample['frame']['date_raw']=None;sample.update(source_answer_raw_u8=None,answer_source_ready=False,source_auto_accept=None);sample['recipient_score'].update(projected_q64=None,numeric_source_ready=False,projected_value_matches_native_final=None,unavailable_reason='source_frame_date_unavailable');sample['actor_on_send_costs'].update(projected_q64=None,numeric_source_ready=False,unavailable_reason='source_frame_date_unavailable');quote_capture('partial_source_preserves_unknown_projection',s)
            s=source_seed();s['samples'][0].update(source_answer_raw_u8=None,native_answer_raw_u8=None,answer_source_ready=False,source_auto_accept=None,native_auto_accept=None,recipient_score=None,actor_on_send_costs=None);quote_capture('null_copies_remain_unknown',s)
            s=source_seed();s['samples']=[];s.update(selected_query_completed=False,unavailable_reason='selected_query_unavailable');quote_capture('empty_copied_samples',s)
            s=source_seed();s['samples']=[copy.deepcopy(s['samples'][0]) for _ in range(4)]
            for i,sample in enumerate(s['samples']):sample['sample_index']=i
            quote_capture('four_ordered_samples',s)
            p=seed();p['can_send']=False;p['acceptance']=dict(kind='not_evaluated_unsendable',auto_accept=False);p['readiness']['acceptance_ready']=False;quote_capture('unsendable_native_answer_stays_null',source_seed(),p)
            p=seed();p['acceptance']=dict(kind='auto_accept',auto_accept=True,would_accept_now=True);quote_capture('autoaccept_no_invented_native_score',source_seed(),p)
            p=dict(private_build=True,read_only=True,advertised=False,action_surface_present=False,status='unavailable',requested_option_mask_bits=8,unavailable_reason='not_evaluated');quote_capture('unavailable_omits_available_source_fields',source_seed(),p)
            source_mutations=[('copied_sha_changed',['samples',0,'frame','executable_sha256'],'set','0'*64),('copied_revision_float',['samples',0,'frame','native_revision'],'set',1014.0),('copied_sequence_changed',['samples',0,'frame','query_sequence'],'set',24),('copied_prisoner_changed',['samples',0,'frame','prisoner_full_id'],'set',61541),('copied_scope_changed',['samples',0,'frame','original_scope_identity'],'set',0),('copied_recipient_changed',['samples',0,'frame','recipient_full_id'],'set',29829),('copied_date_changed',['samples',0,'frame','date_raw'],'set',1),('missing_copied_date',['samples',0,'frame','date_raw'],'remove',None),('source_answer_readiness_conflict',['samples',0,'answer_source_ready'],'set',False),('getter_output_without_call',['samples',0,'recipient_score','native_getter_called'],'set',False),('score_complete_count_mismatch',['samples',0,'recipient_score','modifier_count_raw_i32'],'set',1),('score_float',['samples',0,'recipient_score','base_q64'],'set',5000001.0),('score_compare_conflict',['samples',0,'recipient_score','projected_value_matches_native_final'],'set',False),('cost_original_copy_conflict',['samples',0,'actor_on_send_costs','original_output_copied'],'set',False),('cost_projected_arithmetic_changed',['samples',0,'actor_on_send_costs','projected_q64',0],'set',0),('cost_lane_pointer_changed',['samples',0,'actor_on_send_costs','lanes',0,'lane_identity'],'set',1),('cost_temp_float',['samples',0,'actor_on_send_costs','lanes',0,'raw_temp_q64'],'set',100001.0),('source_extra_field',['unexpected'],'set',True)]
            for name,path,action,value in source_mutations:
                s=source_seed();parent=s
                for key in path[:-1]:parent=parent[key]
                if action=='remove':del parent[path[-1]]
                else:parent[path[-1]]=value
                quote_capture(name,s)
            # Exercise the original signed wrapping/rounding parent on extreme operands.
            from xar_autoplayer.bridge.prisoner_selected_quote_source_contract_12004 import _round,_wrap
            round_cases=[dict(raw=value,expected=_round(value)) for value in [-(1<<63),-(1<<63)+50000,-250001,-150000,-50000,-1,0,1,49999,50000,150000,250001,(1<<63)-50001,(1<<63)-1]]
            s=source_seed();cost=s['samples'][0]['actor_on_send_costs'];cost.update(round_raw_u8=1,clamp_nonnegative_raw_u8=0,original_output_q64=[(1<<63)-1,-(1<<63)]+[0]*8)
            for i,lane in enumerate(cost['lanes']):lane['raw_temp_q64']=[1,-1,-150000,-50000,50000,150000,250001,-250001,0,1][i]
            cost['projected_q64']=[_round(_wrap(a+lane['raw_temp_q64'])) for a,lane in zip(cost['original_output_q64'],cost['lanes'])];quote_capture('native_cost_wrap_and_round',s)
            # One unchanged transport invocation using a complete synthetic native envelope.
            # Endpoint forwarding does not evaluate native code or submit a game action.
            from xar_autoplayer.bridge.player_prisoner_collection_private_transport import query_player_prisoner_collection_private_v1
            ordinary=dict(private_build=True,read_only=True,advertised=False,action_surface_present=False,status='unavailable',unavailable_reason='not_evaluated')
            native_row=dict(source_ordinal=0,prisoner_character_id=61540,collection_owner_character_id=29829,jailer_character_id=29829,custody_relation_verified=True,unconditional_release_preview=ordinary,negotiated_release_preview=seed())
            native_collection=dict(schema='player-prisoner-collection-private-v1',schema_version=2,snapshot_revision=1014,status='available',unavailable_reason=None,date_raw=53286360,played_character_id=29829,total_count=1,returned_count=1,collection_complete=True,prisoners=[native_row])
            native_source=source_seed();native_source['source_ordinal']=0
            native_envelope=dict(step='query-player-prisoner-collection-private-v1',accepted=True,status='available',query_sequence=23,observation_revision=721,snapshot_revision=1014,player_prisoner_collection=native_collection,private_build=True,read_only=True,advertised=False,backend_id='native-headless',prisoner_negotiated_quote_source_12004=native_source)
            before=dict(snapshot_id='native:1014',revision=1014,native_revision=1014,date_raw=53286360,paused=True,map_ready=True,played_character=dict(character_id=29829,alive=True),diagnostics=dict(hello=dict(expected_ck3_version='1.20.0.4',expected_ck3_sha256=SHA)))
            class Endpoint:
                request=None
                def send(self,request):self.request=copy.deepcopy(request)
            class State:
                def wait_for_command_result(self,request_id,timeout):return dict(type='command_result',protocol_version=1,request_id=request_id,ok=True,result=copy.deepcopy(native_envelope))
            class Driver:
                allow_private_prisoner_collection_query=True
                endpoint=Endpoint();state=State()
                def take_internal_semantic_snapshot(self):return copy.deepcopy(before)
            driver=Driver()
            normalized_collection=query_player_prisoner_collection_private_v1(driver,expected_revision=1014,release_option_keys=['gain_hook'])
            if driver.endpoint.request['release_option_mask_bits']!=8:raise RuntimeError('actual transport did not bind authored options to mask8')
            collection_capture=dict(native_fixture_is_synthetic=True,original_transport_executed=True,native_calls=0,game_actions=0,normalized_response_json=json.dumps(normalized_collection,ensure_ascii=False,separators=(',',':')))
            paths=['ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_negotiated_preview_contract_12003.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_release_preview_contract_12003.py','ck3_autonomous_player/src/xar_autoplayer/bridge/player_prisoner_collection_private_transport.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_negotiated_quote_result_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_selected_quote_source_contract_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/prisoner_release_action_private_12004.py','ck3_autonomous_player/src/xar_autoplayer/prisoner_release_formal_consumer.py','ck3_autonomous_player/native_bridge/src/ck3_12003_prisoner_negotiated_preview_serializer.inc','ck3_autonomous_player/native_bridge/src/ck3_12003_prisoner_negotiated_preview_test.cpp']
            sources=[dict(path=path,bytes=len((root/path).read_bytes()),sha256=hashlib.sha256((root/path).read_bytes()).hexdigest()) for path in paths]
            output=dict(schema='xar.java.negotiated-preview-original-producer-golden.v1',machine_id=machine,observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),evidence_scope='Unchanged original Python preview/source normalizers, mask producer, negotiated result consumer and private collection transport on synthetic current-format inputs; no native callbacks, game, release or payment executed.',native_whole_producer_executed=False,production_cutover=False,sources=sources,base_preview_json=baseline,cases=cases,option_mask_cases=masks,source_base_json=source_baseline,quote_result_cases=quote_cases,native_round_cases=round_cases,collection_capture=collection_capture)
            raw=json.dumps(output,ensure_ascii=False,separators=(',',':')).encode('utf-8')
            if len(raw)>98304:raise RuntimeError('golden exceeds declared 96 KiB bound')
            sys.stdout.buffer.write(raw)
            """;

    public static void main(String[] args) throws Exception {
        if (args.length != 4) { throw new IllegalArgumentException("python-exe repo-root new-output machine-id required"); }
        Path root = Path.of(args[1]).toAbsolutePath().normalize();
        Path output = Path.of(args[2]).toAbsolutePath().normalize();
        Path allowed = Path.of("D:/codex-ck3-demos/2026-10-22-java-phase1").toAbsolutePath().normalize();
        if (!output.startsWith(allowed) || Files.exists(output) || args[3].isBlank()) {
            throw new IllegalArgumentException("new permitted D output and verified machine identity required");
        }
        Files.createDirectories(output.getParent());
        ProcessBuilder builder = new ProcessBuilder(args[0], "-B", "-", root.toString(), args[3]);
        builder.directory(root.toFile());
        builder.environment().put("PYTHONDONTWRITEBYTECODE", "1");
        builder.redirectOutput(output.toFile()).redirectError(ProcessBuilder.Redirect.INHERIT);
        Process process = builder.start();
        try (var input = process.getOutputStream()) {
            input.write(SCRIPT.getBytes(StandardCharsets.UTF_8));
        } catch (IOException error) {
            process.destroyForcibly();
            process.waitFor();
            throw error;
        }
        if (!process.waitFor(30, TimeUnit.SECONDS)) {
            process.destroyForcibly();
            process.waitFor();
            throw new IOException("original producer timed out; partial evidence retained");
        }
        if (process.exitValue() != 0 || Files.size(output) == 0 || Files.size(output) > 98_304) {
            throw new IOException("original producer failed or exceeded finite capture budget");
        }
        System.out.println("Captured unchanged negotiated preview producer: " + Files.size(output) + " bytes");
    }
}

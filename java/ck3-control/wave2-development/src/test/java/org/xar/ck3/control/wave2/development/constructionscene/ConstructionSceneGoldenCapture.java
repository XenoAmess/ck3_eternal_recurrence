package org.xar.ck3.control.wave2.development.constructionscene;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit offline original-producer capture. Only the shared qualified Job owner executes it. */
public final class ConstructionSceneGoldenCapture {
    private ConstructionSceneGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("output must be new"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-", arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).redirectOutput(ProcessBuilder.Redirect.INHERIT)
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!child.waitFor(100, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IllegalStateException("capture timeout; shared Job owns whole tree");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("original producer capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) <= 0 || Files.size(output) > 90_000) {
            throw new IllegalStateException("bounded nonempty original producer golden required");
        }
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,tempfile,io,unittest
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2])
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                from test_construction_monthly_budget_v1 import cash_fixture
                from xar_autoplayer.construction_scene_scope_v1 import same_frame_construction_scope_v1,clan_construction_cash_frame_reason_v1
                from xar_autoplayer.lifestyle_formal_consumer import _same_frame_feudal_scope
                from xar_autoplayer.construction_formal_consumer import SUBMIT_STEP,ROOT_QUERY_STEP
                from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
                import ast
                from types import SimpleNamespace
                original_data_path=repo/'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt'
                original_data_bytes=original_data_path.read_bytes()
                if hashlib.sha256(original_data_bytes).hexdigest()!='aba97265f08a8b75437858189b7fca48e5372fa9df1d5c80252d1c459c39e79f':raise ValueError('fixed original data fixture drift')
                original_data={'Path':Path,'transport':SimpleNamespace(QUERY_NATIVE='g2_player_construction_view_probe_v1',ACTION_NATIVE='g2_player_world_building_action_private_v1'),'deepcopy':copy.deepcopy}
                exec(compile(original_data_bytes,str(original_data_path),'exec'),original_data)
                frame,root=original_data['frame'],original_data['root']
                from construction_python_oracle_v1 import _compile_wrapper_v1
                original_plan_tree=ast.parse((oracle.fixtures/'construction_formal_consumer.py.txt').read_text(encoding='utf-8'))
                original_plan=next(node for node in original_plan_tree.body if isinstance(node,ast.FunctionDef) and node.name=='plan_construction_private')
                start=next(index for index,node in enumerate(original_plan.body) if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='scope' for target in node.targets))
                prefix=original_plan.body[start:start+3]
                if len(prefix)!=3 or not all(isinstance(node,ast.If) for node in prefix[1:]):raise ValueError('original scope prefix drift')
                helpers=[node for node in original_plan.body if isinstance(node,ast.FunctionDef) and node.name in {'prewar_unchanged','optional_spend_deferred'}]
                if len(helpers)!=2:raise ValueError('original scope helper drift')
                original_scope=dict(oracle.namespace);original_scope['same_frame_construction_scope_v1']=same_frame_construction_scope_v1
                seam=ast.parse("plan=planned['plan']\\noriginal_step=plan.get('selected_step')\\nprewar=False").body
                _compile_wrapper_v1(original_scope,'def historical_scope_prefix(planned,snapshot,history,available_steps)',seam+helpers+prefix,'None')
                cases=[]
                def scope_case(name,change=None,strict=False):
                    snapshot=frame();history=root()
                    if change:change(snapshot,history)
                    request={'schema':'xar.construction-scene-input.v1','snapshot':snapshot,'history':history}
                    expected=same_frame_construction_scope_v1(snapshot,history)
                    feudal=_same_frame_feudal_scope(snapshot,history,require_peace=False)
                    cases.append({'name':name,'kind':'scene','input_json':json.dumps(request,ensure_ascii=False,separators=(',',':')),
                        'expected':expected,'java_strict_reject':strict,'feudal_delegate_expected':feudal})
                def government(history,key,flags):history[-1]['result']['campaign_root_context']['government']={'key':key,'flags':flags}
                scope_case('feudal_peace')
                scope_case('feudal_war',lambda s,h:s.update(active_wars=[{'war_id':117440524}]))
                scope_case('clan_peace',lambda s,h:government(h,'clan_government',['government_is_clan']))
                scope_case('clan_war',lambda s,h:(government(h,'clan_government',['government_is_clan']),s.update(active_wars=[{'war_id':117440524}])))
                scope_case('tribal_outside',lambda s,h:government(h,'tribal_government',['government_is_tribal']))
                scope_case('clan_flag_absent',lambda s,h:government(h,'clan_government',[]))
                scope_case('feudal_flag_absent',lambda s,h:government(h,'feudal_government',[]))
                scope_case('clan_key_wrong',lambda s,h:government(h,'other_government',['government_is_clan']))
                scope_case('unpaused',lambda s,h:s.update(paused=False))
                scope_case('paused_missing',lambda s,h:s.pop('paused'))
                scope_case('wars_missing',lambda s,h:s.pop('active_wars'))
                scope_case('wars_null',lambda s,h:s.update(active_wars=None))
                scope_case('actor_missing',lambda s,h:s['played_character'].pop('character_id'))
                scope_case('native_revision_zero',lambda s,h:s.update(native_revision=0))
                scope_case('public_revision_zero',lambda s,h:s.update(revision=0))
                scope_case('snapshot_id_mismatch',lambda s,h:s.update(snapshot_id='native:4'))
                scope_case('root_missing',lambda s,h:h.clear())
                scope_case('root_failed',lambda s,h:h[-1].update(ok=False))
                scope_case('root_unavailable',lambda s,h:h[-1]['result']['campaign_root_context'].update(status='unavailable'))
                scope_case('root_other_actor',lambda s,h:h[-1]['result']['campaign_root_context'].update(player_character_id=44))
                scope_case('root_stale_revision',lambda s,h:h[-1]['result']['campaign_root_context'].update(snapshot_revision=2))
                scope_case('root_stale_date',lambda s,h:h[-1]['result']['campaign_root_context'].update(date_raw=53178311))
                scope_case('government_null',lambda s,h:h[-1]['result']['campaign_root_context'].update(government=None))
                scope_case('government_flags_missing',lambda s,h:h[-1]['result']['campaign_root_context']['government'].pop('flags'))
                scope_case('latest_matching_root_wins',lambda s,h:(h.append(copy.deepcopy(h[0])),government(h,'tribal_government',['government_is_tribal'])))
                scope_case('later_stale_root_skipped',lambda s,h:(h.append(copy.deepcopy(h[0])),h[-1]['result']['campaign_root_context'].update(snapshot_revision=2)))
                scope_case('later_failed_root_skipped',lambda s,h:(h.append(copy.deepcopy(h[0])),h[-1].update(ok=False)))
                scope_case('unrelated_unknown_action_not_replayed',lambda s,h:h.append({'command':SUBMIT_STEP,'ok':True,'result':{'status':'action_state_unknown','episode_run_id':s['episode_run_id']}}))
                def council(s,h,positions):h[-1]['result']['campaign_root_context']['council']={'status':'available','positions':positions}
                steward={'position_key':'councillor_steward','incumbent_character_id':44,'task_key':'task_collect_taxes','frozen':False}
                scope_case('collect_taxes_true',lambda s,h:council(s,h,[copy.deepcopy(steward)]))
                scope_case('collect_taxes_frozen',lambda s,h:council(s,h,[{**steward,'frozen':True}]))
                scope_case('collect_taxes_vacant',lambda s,h:council(s,h,[{**steward,'incumbent_character_id':None}]))
                scope_case('collect_taxes_other_task',lambda s,h:council(s,h,[{**steward,'task_key':'task_develop_county'}]))
                scope_case('collect_taxes_duplicate_steward',lambda s,h:council(s,h,[copy.deepcopy(steward),copy.deepcopy(steward)]))
                scope_case('collect_taxes_no_steward',lambda s,h:council(s,h,[]))
                scope_case('sdk_extensions',lambda s,h:(s.update(future_snapshot_component={'extra':True}),h[-1]['result']['campaign_root_context'].update(future_root_component={'extra':True})))
                for label,value in [('boolean',True),('float',3.0),('exponent',3e0),('string','3')]:
                    scope_case('native_revision_'+label,lambda s,h,value=value:s.update(native_revision=value),True)
                    if label=='exponent':cases[-1]['input_json']=cases[-1]['input_json'].replace('"native_revision":3.0','"native_revision":3e0')
                scope_case('root_revision_float',lambda s,h:h[-1]['result']['campaign_root_context'].update(snapshot_revision=3.0),True)
                scope_case('date_boolean',lambda s,h:s.update(date_raw=True),True)
                scope_case('root_actor_float',lambda s,h:h[-1]['result']['campaign_root_context'].update(player_character_id=29829.0),True)
                def cash_case(name,change=None,strict=False):
                    snapshot=frame();original=cash_fixture(gold=50000000,gross=450000,expenses=380000,current=200000,all_raised=500000)
                    original.update(snapshot_revision=snapshot['native_revision'],date_raw=snapshot['date_raw'])
                    packet={key:original[key] for key in ['played_character_id','snapshot_revision','date_raw','game_version','read_only','readiness','monthly_income_semantics']}
                    observation={'current_cash_scenarios':{'source_cash_resources':packet}}
                    if change:change(snapshot,observation,packet)
                    request={'schema':'xar.construction-clan-cash-frame-input.v1','snapshot':snapshot,'observation':observation}
                    expected={'reason':clan_construction_cash_frame_reason_v1(snapshot,observation)}
                    cases.append({'name':name,'kind':'cash','input_json':json.dumps(request,ensure_ascii=False,separators=(',',':')),'expected':expected,'java_strict_reject':strict})
                cash_case('cash_observed_net')
                cash_case('cash_packet_missing',lambda s,o,p:o['current_cash_scenarios'].pop('source_cash_resources'))
                cash_case('cash_packet_null',lambda s,o,p:o['current_cash_scenarios'].update(source_cash_resources=None))
                cash_case('cash_budget_missing',lambda s,o,p:o.pop('current_cash_scenarios'))
                cash_case('cash_wrong_actor',lambda s,o,p:p.update(played_character_id=44))
                cash_case('cash_stale_revision',lambda s,o,p:p.update(snapshot_revision=2))
                cash_case('cash_stale_date',lambda s,o,p:p.update(date_raw=53178311))
                cash_case('cash_wrong_version',lambda s,o,p:p.update(game_version='1.20.1'))
                cash_case('cash_not_read_only',lambda s,o,p:p.update(read_only=False))
                cash_case('cash_readiness_missing',lambda s,o,p:p.pop('readiness'))
                cash_case('cash_semantics_missing',lambda s,o,p:p.pop('monthly_income_semantics'))
                cash_case('cash_semantics_null',lambda s,o,p:p.update(monthly_income_semantics=None))
                cash_case('cash_semantics_empty_object',lambda s,o,p:p.update(monthly_income_semantics={}))
                for flag in ['same_frame_ready','current_treasury_ready','monthly_gross_income_ready','monthly_total_expenses_ready','monthly_net_income_ready']:
                    cash_case('cash_'+flag+'_false',lambda s,o,p,flag=flag:p['readiness'].update({flag:False}))
                cash_case('cash_extensions',lambda s,o,p:p.update(future_cash_field={'extra':True}))
                cash_case('cash_actor_float',lambda s,o,p:p.update(played_character_id=29829.0),True)
                cash_case('cash_read_only_integer',lambda s,o,p:p.update(read_only=1),True)
                cash_case('cash_ready_integer',lambda s,o,p:p['readiness'].update(monthly_net_income_ready=1),True)
                consumers=[]
                for name,kind,root_available in [('root_query','missing',True),('root_query_unavailable','missing',False),('outside_scene','tribal',True),('scope_unavailable','unpaused',True),('feudal_continues','feudal',True)]:
                    history=root();snapshot=frame()
                    if kind=='missing':history=[]
                    if kind=='tribal':government(history,'tribal_government',['government_is_tribal'])
                    if kind=='unpaused':snapshot['paused']=False
                    baseline={'revision':3,'plan':{'policy':'one-life-turn-v1','selected_step':'life-advance'}}
                    before=copy.deepcopy(baseline);steps={'life-advance',SUBMIT_STEP}
                    if root_available:steps.add(ROOT_QUERY_STEP)
                    selected=original_scope['historical_scope_prefix'](baseline,snapshot,history,steps)
                    if before!=baseline:raise ValueError('original scope prefix mutated baseline')
                    consumers.append({'name':name,'scene_input_json':json.dumps({'schema':'xar.construction-scene-input.v1','snapshot':snapshot,'history':history},separators=(',',':')),
                        'root_query_available':root_available,'original_scope_prefix_result':selected,'native_queries_executed':0})
                sources=['ck3_autonomous_player/src/xar_autoplayer/construction_scene_scope_v1.py','ck3_autonomous_player/src/xar_autoplayer/lifestyle_formal_consumer.py',
                    'ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/campaign_root_context_contract.py',
                    'ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py','ck3_autonomous_player/tests/unit/test_construction_monthly_budget_v1.py',
                    'ck3_autonomous_player/tests/unit/test_clan_construction_scope_cash_compound_v1.py','tools/ck3_live_run_id.py']
                result={'schema':'xar.construction-scene-original-producer-golden.v2','machine_id':current_machine_id(),
                    'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_refs':oracle.capture_source_refs_v1(sources),
                    'capture_scope':'Unchanged actual scope and Clan cash producer; actual construction planner scope call sites and existing ten-case Clan/feudal quote/cash compound. Synthetic paused fixtures; no Game, RPC, submit or ledger change.',
                    'existing_compound':{'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_clan_construction_scope_cash_compound_v1.py'],'declared_scenarios':10},'cases':cases,'consumer_cases':consumers}
                result['producer_role']='REFERENCE_ORACLE'
                result['current_consumer_validation']='REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1([*sources,'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt'])
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>90000:raise ValueError('golden exceeds 90000-byte hard cap')
                output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('xb') as handle:handle.write(raw)
                print(json.dumps({'machine_id':result['machine_id'],'cases':len(cases),'consumer_cases':len(consumers),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
            """;
}

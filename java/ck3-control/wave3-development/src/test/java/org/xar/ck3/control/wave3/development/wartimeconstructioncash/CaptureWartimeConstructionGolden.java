package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Original policy and its actual priority call, executed only by the shared bounded Job owner. */
public final class CaptureWartimeConstructionGolden {
    private CaptureWartimeConstructionGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("repo python new-output required");
        Path output = Path.of(args[2]).toAbsolutePath();
        if (Files.exists(output)) throw new IllegalArgumentException("new output required");
        Process child = new ProcessBuilder(List.of(args[1], "-B", "-", args[0], output.toString()))
                .directory(Path.of(args[0]).toFile()).redirectOutput(ProcessBuilder.Redirect.INHERIT)
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!child.waitFor(90, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IllegalStateException("capture timeout"); }
        if (child.exitValue() != 0) throw new IllegalStateException("capture exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) > 32000) throw new IllegalStateException("capture output budget");
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,gzip,tempfile
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                import ast
                from types import SimpleNamespace
                original_data_path=repo/'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt'
                original_data_bytes=original_data_path.read_bytes()
                if hashlib.sha256(original_data_bytes).hexdigest()!='aba97265f08a8b75437858189b7fca48e5372fa9df1d5c80252d1c459c39e79f':raise ValueError('fixed original data fixture drift')
                original_data={'Path':Path,'transport':SimpleNamespace(QUERY_NATIVE='g2_player_construction_view_probe_v1',ACTION_NATIVE='g2_player_world_building_action_private_v1'),'deepcopy':copy.deepcopy}
                exec(compile(original_data_bytes,str(original_data_path),'exec'),original_data)
                from collections.abc import Mapping
                from types import ModuleType
                from xar_autoplayer.bridge.version_identity import CK3_12004
                from xar_autoplayer.m5_observed_opportunity_selector import observed_frame
                from xar_autoplayer.war_political_survival_stakes_v1 import observe_political_survival_stakes_v1,political_survival_stakes_qualified_v1
                original_data.update(CK3_12004=CK3_12004,observed_frame=observed_frame)
                WarDriver,company,inputs=original_data['WarDriver'],original_data['company'],original_data['inputs']
                # Only the isolated historical producer's unchanged local import uses this package.
                historical_package='xar_construction_reference_original_v1'
                package=ModuleType(historical_package);package.__path__=[];sys.modules[historical_package]=package
                priority=ModuleType(historical_package+'.war_reinforcement_tradeoff_v1')
                priority.__package__=historical_package;sys.modules[priority.__name__]=priority
                priority.__dict__.update(Mapping=Mapping,observe_political_survival_stakes_v1=observe_political_survival_stakes_v1,political_survival_stakes_qualified_v1=political_survival_stakes_qualified_v1)
                realm_path=repo/'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/nonleading-player-realm-siege-original.py.txt';realm_bytes=realm_path.read_bytes()
                if hashlib.sha256(realm_bytes).hexdigest()!='3f5103e42c8d7d785aa7680d19be592407a55b8e3d6bb4fb55159817fbe925e6':raise ValueError('fixed original realm predicate drift')
                exec(compile(realm_bytes,str(realm_path),'exec'),priority.__dict__)
                source_path=repo/'ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py';source=source_path.read_bytes()
                if hashlib.sha256(source).hexdigest()!='d9f32c208fa47a0b2007f4a5194462a9929fac2f636c8e58ba25a8cffb1a089c':raise ValueError('original spending priority drift')
                tree=ast.parse(source)
                names={'_armies','_count','_current_root','observe_war_spending_priority_v1'}
                nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
                if len(nodes)!=len(names):raise ValueError('original spending closure drift')
                exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source_path),'exec'),priority.__dict__)
                wartime_namespace={'__package__':historical_package,'Mapping':Mapping,'observed_frame':observed_frame}
                source_path=repo/'ck3_autonomous_player/src/xar_autoplayer/wartime_construction_cash_v1.py';source=source_path.read_bytes()
                if hashlib.sha256(source).hexdigest()!='9eb2f93a573e2c6f467e6ff478c50d9856350cb4c436b5403fd0dd70351b772e':raise ValueError('original wartime policy drift')
                tree=ast.parse(source)
                nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='observe_wartime_construction_cash_v1']
                nodes += [node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in {'CONSTRUCTION_KINDS','AMPLE_FIXED_BUFFER_RAW','AMPLE_MAXIMUM_MAINTENANCE_MONTHS'} for target in node.targets)]
                exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source_path),'exec'),wartime_namespace)
                observe_wartime_construction_cash_v1=wartime_namespace['observe_wartime_construction_cash_v1']
                cases=[]
                with tempfile.TemporaryDirectory(prefix='wartime-construction-',dir=output.parent) as temporary:
                    def add(name,change=None,kind='new_building',cost=23000000,procurement=None):
                        d=WarDriver(Path(temporary)); values=inputs(d)
                        values['spending']['budget']['reserved_raw']['gold']=7000000
                        if change: change(d.snapshot,values)
                        request={'schema':'xar.wartime-construction-cash-input.v1','snapshot':d.snapshot,'kind':kind,'construction_gold_raw':cost,**values,'procurement_decision':procurement}
                        expected=observe_wartime_construction_cash_v1(d.snapshot,kind=kind,construction_gold_raw=cost,**values,procurement_decision=procurement)
                        if d.requests or d.query_count or d.hire_count: raise ValueError('offline observation unexpectedly dispatched')
                        cases.append({'name':name,'request':copy.deepcopy(request),'expected':copy.deepcopy(expected)})
                    add('exact_ample_threshold')
                    add('one_raw_unit_below_threshold',cost=23000001)
                    add('upgrade_ample',kind='upgrade_building')
                    add('new_holding_no_interface',kind='new_holding',cost=1)
                    add('unidentified_kind',kind='unidentified')
                    add('outside_wartime',lambda s,v:s.update(active_wars=[]))
                    add('unknown_wars',lambda s,v:s.update(active_wars=None))
                    add('unknown_quote',cost=None)
                    add('maintenance_unavailable',lambda s,v:v['root']['player_max_monthly_gold_maintenance_v1'].update(status='unavailable'))
                    add('market_unavailable',lambda s,v:v.update(market=None))
                    add('market_frame_old',lambda s,v:v['market_source_frame'].update(native_revision=1))
                    def all_terms(key,value):
                        return lambda s,v:[row['final_terms'].update({key:value}) for row in v['market']['rows']]
                    add('cannot_hire',all_terms('can_hire',False))
                    add('cannot_afford',all_terms('can_afford',False))
                    add('cost_vector_incomplete',all_terms('resource_costs_raw',[10000000]))
                    add('spending_unavailable',lambda s,v:v.update(spending={'status':'unavailable'}))
                    add('mercenary_pending_unknown',lambda s,v:v['mercenary_ledger'].update(pending={'status':'submission_unresolved'}))
                    add('hostile_spawn',lambda s,v:[row['location'].update(hire_auto_raise_province_id=s['active_wars'][0]['enemy_armies'][0]['current_province_id']) for row in v['market']['rows']])
                    add('maximum_military_not_war_multiplied',lambda s,v:v['root']['player_max_monthly_gold_maintenance_v1']['value'].update(raw=4000000),cost=0)
                    def deficit(s,v):
                        s['active_wars'][0]['player_relative_war_score']=-60
                        s['player_armies'][0]['soldiers']=800
                    add('cheapest_adequate_quote',deficit,cost=0)
                    def weak(s,v):
                        deficit(s,v); v['market']['rows'][0]['troop_strength']['current_soldiers']=50
                    add('weak_cheap_cannot_replace_adequate',weak,cost=0)
                    def assessed(s,v):
                        deficit(s,v)
                    d=WarDriver(Path(temporary)); values=inputs(d); f=values['market_source_frame']
                    selected={'selected_candidate':{'company_id':8,'gold_cost_raw':30000000,'rejection_reasons':[],'purpose_war_ids':[d.snapshot['active_wars'][0]['war_id']],'finance':{'source_frame':{'actor_character_id':f['played_character_id'],'native_revision':f['native_revision'],'date_raw':f['date_raw']}}}}
                    add('current_assessed_suitable_quote',assessed,cost=0,procurement=selected)
                    old=copy.deepcopy(selected); old['selected_candidate']['finance']['source_frame']['native_revision']-=1
                    add('old_procurement_cannot_override',assessed,cost=0,procurement=old)
                    add('complete_empty_market',lambda s,v:v['market'].update(rows=[]),cost=0)
                    add('nonmapping_market_rows_are_not_empty',lambda s,v:v['market'].update(rows=[None]),cost=0)
                    add('missing_native_group_reason',lambda s,v:[row.pop('location') for row in v['market']['rows']],cost=0)
                    add('equal_price_tie_larger_id',lambda s,v:v['market'].update(rows=[company(1,10000000,2000,9998),company(9,10000000,2000,9999)]),cost=0)
                    add('arbitrary_precision_quote_outlay',cost=10**30)
                    def two_wars(s,v):
                        s['active_wars'].append({**copy.deepcopy(s['active_wars'][0]),'war_id':991}); v['spending']['budget']['active_war_count']=2
                    add('two_wars_one_buffer',two_wars,cost=0)
                    add('unknown_treasury',lambda s,v:s['played_character_gold'].update(raw=None),cost=0)
                    add('root_missing',lambda s,v:v.update(root=None),cost=0)
                    add('zero_company_zero_cost_native_quote',lambda s,v:v['market'].update(rows=[company(0,0,1400,9999)]),cost=0)
                sources=['ck3_autonomous_player/src/xar_autoplayer/wartime_construction_cash_v1.py','ck3_autonomous_player/src/xar_autoplayer/war_reinforcement_tradeoff_v1.py','ck3_autonomous_player/src/xar_autoplayer/m5_observed_opportunity_selector.py','ck3_autonomous_player/src/xar_autoplayer/nonleading_player_realm_siege_v1.py','ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/tests/unit/test_wartime_construction_cash_v1.py','ck3_autonomous_player/tests/unit/test_war_reinforcement_tradeoff_v1.py','ck3_autonomous_player/tests/unit/test_g2_wartime_construction_service_compound_v1.py','tools/ck3_live_run_id.py']
                result={'schema':'xar.wartime-construction-original-producer-golden.v2','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':[{'path':'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/nonleading-player-realm-siege-original.py.txt','bytes':len(realm_bytes),'sha256':'3f5103e42c8d7d785aa7680d19be592407a55b8e3d6bb4fb55159817fbe925e6'} if path=='ck3_autonomous_player/src/xar_autoplayer/nonleading_player_realm_siege_v1.py' else oracle.capture_source_refs_v1([path])[0] for path in sources],'capture_method':'Unchanged observe_wartime_construction_cash_v1 including real observe_war_spending_priority_v1 call, with existing controlled WarDriver/market fixtures. Policy vectors perform zero query/action. Two complete original consumer regressions use isolated temporary fixture ledgers/callbacks only; no production pending/canonical, Game/Steam/native RPC or runtime qualification.','original_consumer_regressions':{'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_wartime_construction_cash_v1.py'],'declared_test_names':['test_winning_or_unknown_war_advance_continues_without_optional_queries','test_submit_rechecks_current_inputs_before_creating_intent_or_native_send']},'cases':cases}
                result['producer_role']='REFERENCE_ORACLE'
                result['current_consumer_validation']='REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1([*sources,'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt','ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/nonleading-player-realm-siege-original.py.txt','ck3_autonomous_player/src/xar_autoplayer/war_political_survival_stakes_v1.py'])
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\\n').encode()
                if len(raw)>524288: raise ValueError('expanded golden budget exceeded '+str(len(raw)))
                compressed=gzip.compress(raw,mtime=0)
                if len(compressed)>32000: raise ValueError('compressed golden budget exceeded')
                with output.open('xb') as f: f.write(compressed)
                print(json.dumps({'cases':len(cases),'bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'machine_id':result['machine_id'],'observed_at_utc':result['observed_at_utc']}))
            """;
}

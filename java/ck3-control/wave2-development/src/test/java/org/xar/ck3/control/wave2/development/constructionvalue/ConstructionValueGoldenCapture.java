package org.xar.ck3.control.wave2.development.constructionvalue;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Bounded explicit original-producer capture, executed only by the shared qualified Job owner. */
public final class ConstructionValueGoldenCapture {
    private ConstructionValueGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath();
        if (Files.exists(output)) { throw new IllegalArgumentException("capture output must be new"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-", arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).redirectOutput(ProcessBuilder.Redirect.INHERIT)
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!child.waitFor(100, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IllegalStateException("producer timeout; shared Job owns process tree");
        }
        if (child.exitValue() != 0) { throw new IllegalStateException("original producer capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) <= 0 || Files.size(output) > 90_000) {
            throw new IllegalStateException("bounded nonempty golden required");
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
                from xar_autoplayer.bridge import construction_economic_value_v1 as values
                from xar_autoplayer.bridge import domain_construction_private_transport_v1 as transport
                from xar_autoplayer.bridge.version_identity import CK3_11906,CK3_12002,CK3_12003,CK3_12004
                from test_construction_same_slot_value_v1 import _world,_cereal,_farm_downgrade,_farm_occupant,_completed,ACTUAL_CEREAL_HOLDING
                builds=['1.19.0.6','1.20.0.2','1.20.0.3','1.20.0.4']
                keys=sorted(set(values._AUTHOR_MONTHLY_INCOME_HUNDREDTHS)|set(values._AUTHOR_EXISTING_MONTHLY_INCOME_HUNDREDTHS_12003)|set(values._AUTHOR_UPGRADE_MONTHLY_INCOME_HUNDREDTHS_12004)|{'castle_01','farm_estates_09','unknown_building'})
                matrix=[{'key':key,'target':[values.authored_monthly_income_hundredths(key,exact_ck3_build=build) for build in builds],
                    'existing':[values.authored_existing_monthly_income_hundredths(key,exact_ck3_build=build) for build in builds]} for key in keys]
                lookups=[]
                for kind,producer in [('target',values.authored_monthly_income_hundredths),('existing',values.authored_existing_monthly_income_hundredths)]:
                    for label,key,build in [('missing',None,None),('null',None,'1.20.0.4'),('empty','',None),('unsupported','farm_estates_01','1.20.1'),('tier_two_default','farm_estates_02',None),('zero_income','military_camps_01','1.20.0.3')]:
                        request={'schema':'xar.construction-authored-income-input.v1','kind':kind}
                        if label!='missing':request['building_key']=key
                        if build is not None:request['exact_ck3_build']=build
                        expected=producer(key,**({'exact_ck3_build':build} if build is not None else {}))
                        lookups.append({'name':kind+'_'+label,'input_json':json.dumps(request,separators=(',',':')),'expected':{'authored_monthly_income_hundredths':expected}})
                cases=[];consumer_worlds=[]
                def add(name,world=None,change=None,build='1.20.0.3',strict=False,consumer=False):
                    world=copy.deepcopy(world if world is not None else _world([_farm_downgrade(),_cereal()],[_farm_occupant()]))
                    if change:change(world)
                    request={'schema':'xar.construction-value-selection-input.v1','world':world,'exact_ck3_build':build}
                    cases.append({'name':name,'input_json':json.dumps(request,ensure_ascii=False,separators=(',',':')),
                        'expected':oracle.original('_candidate',(world,),{'exact_ck3_build':build}),'java_strict_reject':strict})
                    if consumer:consumer_worlds.append((name,world,build,cases[-1]['input_json']))
                add('actual_downgrade_yields_to_empty_cereal',consumer=True)
                add('equal_gain_cost_prefers_observed_empty',_world([_cereal(2),_cereal(4)],[_completed(ACTUAL_CEREAL_HOLDING,2,'military_camps_01')]),consumer=True)
                add('negative_and_zero_replacement',_world([_farm_downgrade(),_cereal()],[_farm_occupant(),_completed(ACTUAL_CEREAL_HOLDING,4,'paddy_fields_01')]),consumer=True)
                add('unknown_occupied_is_not_empty',_world([_cereal(2),_cereal(4)],[_completed(ACTUAL_CEREAL_HOLDING,2,None)]),consumer=True)
                add('separate_gross_and_positive_delta',_world([_cereal(2)],[_completed(ACTUAL_CEREAL_HOLDING,2,'pastures_01')]),consumer=True)
                add('covered_no_candidate',change=lambda w:w.update(legal_samples=[],positive_income_coverage_complete=True),consumer=True)
                add('uncovered_no_candidate',change=lambda w:w.update(legal_samples=[]),consumer=True)
                add('missing_gold',change=lambda w:w.pop('player_gold_raw'))
                add('gold_null',change=lambda w:w.update(player_gold_raw=None))
                add('gold_float',change=lambda w:w.update(player_gold_raw=120659426.0),strict=True)
                add('active_missing',change=lambda w:w.pop('active_constructions'))
                add('samples_missing',change=lambda w:w.pop('legal_samples'))
                add('inventory_missing_no_empty_assumption',change=lambda w:(w.pop('completed_buildings'),w.update(completed_buildings_observed=False)))
                add('unobserved_inventory_retains_observed_occupant',_world([_cereal(2)],[_completed(ACTUAL_CEREAL_HOLDING,2,'pastures_01')]),change=lambda w:w.update(completed_buildings_observed=False))
                add('duplicate_occupants_defer',_world([_cereal(2)],[_completed(ACTUAL_CEREAL_HOLDING,2,'military_camps_01'),_completed(ACTUAL_CEREAL_HOLDING,2,'military_camps_01')]),consumer=True)
                add('busy_holding_excluded',change=lambda w:[row.update(active=True) for row in w['active_constructions']],consumer=True)
                add('unknown_target_key',change=lambda w:[row.update(building_key='castle_01') for row in w['legal_samples']],consumer=True)
                add('cost_unobserved',change=lambda w:[row.update(native_cost_observed=False) for row in w['legal_samples']])
                add('non_gold_cost',change=lambda w:[row['cost_raw_native'].__setitem__(1,100000) for row in w['legal_samples']],consumer=True)
                add('negative_non_gold_cost',change=lambda w:[row['cost_raw_native'].__setitem__(2,-1) for row in w['legal_samples']])
                add('short_cost_vector',change=lambda w:[row.update(cost_raw_native=[1]) for row in w['legal_samples']])
                add('zero_gold_cost',change=lambda w:[row['cost_raw_native'].__setitem__(0,0) for row in w['legal_samples']])
                add('reserve_exact_threshold',_world([_cereal()],[]),change=lambda w:w.update(player_gold_raw=34250000),consumer=True)
                add('reserve_one_below',_world([_cereal()],[]),change=lambda w:w.update(player_gold_raw=34249999),consumer=True)
                add('cheaper_same_gain_wins',_world([_cereal(2),{**_cereal(4),'cost_raw_native':[10000000]+[0]*9}],[]),consumer=True)
                add('all_tuple_tie_breakers',_world([_cereal(4),_cereal(2)],[]),consumer=True)
                add('old_build_tier_two_not_target',_world([{**_cereal(),'building_key':'common_tradeport_02'}],[]),build='1.20.0.2',consumer=True)
                add('exact4_tier_eight_target',_world([{**_cereal(),'building_key':'farm_estates_08'}],[]),build='1.20.0.4',consumer=True)
                add('exact3_tier_eight_unknown',_world([{**_cereal(),'building_key':'farm_estates_08'}],[]),build='1.20.0.3',consumer=True)
                add('unsupported_build',build='1.20.1')
                add('float_identity_raw',change=lambda w:w['legal_samples'][1].update(building_type_id=604.0),strict=True)
                add('boolean_slot_raw',change=lambda w:w['legal_samples'][1].update(slot_index=True),strict=True)
                add('float_cost_raw',change=lambda w:w['legal_samples'][1]['cost_raw_native'].__setitem__(0,14250000.0),strict=True)
                add('sdk_extension',change=lambda w:w.update(future_world={'unconsumed':1.25}),consumer=True)
                from types import SimpleNamespace
                consumers=[]
                for name,world,build,input_json in consumer_worlds:
                    selected=oracle.original('value_consumer_original_v1',(world,SimpleNamespace(game_version=build),{}, {},'REFERENCE_ORACLE',{'proof_epoch':1},{'snapshot_id':'REFERENCE_ORACLE','date_raw':1,'played_character':{'character_id':1}},'REFERENCE_ORACLE',1,1))
                    consumers.append({'name':name,'input_json':input_json,'expected':{key:selected[key] for key in ['status','candidate','reason'] if key in selected}})
                consumer_requirement={'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_construction_same_slot_value_v1.py']}
                sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/construction_economic_value_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py',
                    'ck3_autonomous_player/tests/unit/test_construction_same_slot_value_v1.py','ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py','tools/ck3_live_run_id.py']
                result={'schema':'xar.construction-value-original-producer-golden.v2','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_refs':oracle.capture_source_refs_v1(sources),
                    'capture_scope':'Unchanged authored functions across every retained key/build, complete _candidate producer, and actual query_construction_private consumer with one original simulated native read. Actual downgrade fixture provenance retained; no Game, RPC, submit or canonical ledger.',
                    'actual_material_provenance':{'source':'m4-council/role-coverage/robert-v19-412-actual-01/construction/query-source.json','sha256':'4fd9fa8b7fb971b6473fd80f2beb3abccf12edfc63bb38f5f56dcc3360fcb662','machine_id':'unknown','available_original_not_reverified':True},
                    'existing_tests':consumer_requirement,
                    'builds':builds,'lookup_matrix':matrix,'lookup_cases':lookups,'cases':cases,'consumer_cases':consumers}
                result['producer_role']='REFERENCE_ORACLE'
                result['current_consumer_validation']='REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1(sources)
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>90000:raise ValueError('golden exceeds hard cap')
                output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('xb') as handle:handle.write(raw)
                print(json.dumps({'machine_id':result['machine_id'],'cases':len(cases),'consumer_cases':len(consumers),'table_keys':len(keys),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}))
            """;
}

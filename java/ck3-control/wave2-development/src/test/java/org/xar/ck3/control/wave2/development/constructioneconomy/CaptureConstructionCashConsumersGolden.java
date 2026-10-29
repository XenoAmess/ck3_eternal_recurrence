package org.xar.ck3.control.wave2.development.constructioneconomy;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Original formal-consumer capture; scheduled with other captures by the shared Job owner. */
public final class CaptureConstructionCashConsumersGolden {
    private CaptureConstructionCashConsumersGolden() { }
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
        try (var compressed = Files.newInputStream(output)) {
            if (ConstructionCashCaptureContract.decodeGzip(compressed).version()
                    != ConstructionCashCaptureContract.Version.REFERENCE_V2) {
                throw new IllegalStateException("current capture must emit reference v2");
            }
        }
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,gzip,tempfile,os
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                from test_construction_monthly_budget_v1 import cash_fixture
                from xar_autoplayer.bridge.construction_monthly_budget_v1 import project_construction_monthly_budget_v1
                cases=[]
                def quote_case(name,*,cash=None,observation='known',wartime=False,same=False,frame=2,quote_gold=None):
                    c=cash_fixture() if cash is None else cash
                    quote={'status':'selected','candidate':{'barony_title_id':2103,'province_id':2635,'stock_gold_cost_raw':1000000,'gold_before_raw':c['current_treasury']['raw'] if quote_gold is None else quote_gold},'source_frame':{'actor_character_id':29829,'native_revision':frame,'date_raw':c['date_raw']},'sdk_extension':{'explicit_null':None,'empty_rows':[]}}
                    packet=None if observation=='missing' else {} if observation=='unavailable' else {'current_cash_scenarios':project_construction_monthly_budget_v1(c,construction_gold_cost_raw=0,reserve_gold_raw=3000000,existing_commitment_gold_raw=0,horizon_months=1)}
                    projected,reason=oracle.original('project_construction_quote_current_cash',(quote,packet),{'wartime':wartime,'require_same_frame':same})
                    cases.append({'kind':'quote','name':name,'request':{'quote':quote,'cash':c,'observation':observation,'reserve_gold_raw':3000000,'wartime':wartime,'require_same_frame':same},'expected':{'quote':projected,'deferred_reason':reason}})
                quote_case('no_observation_peace',observation='missing')
                quote_case('no_observation_war',observation='missing',wartime=True)
                quote_case('unavailable_observation',observation='unavailable')
                quote_case('observed_peace')
                quote_case('wallet_differs',quote_gold=1)
                quote_case('war_frame_differs',frame=1,wartime=True)
                quote_case('required_frame_differs',frame=1,same=True)
                quote_case('peace_does_not_require_source_frame',frame=1)
                quote_case('current_floor_defers',cash=cash_fixture(gold=5000000,expenses=3000000))
                quote_case('war_allraised_floor_defers',cash=cash_fixture(gold=5000000,all_raised=4000000),wartime=True)
                import ast
                from types import SimpleNamespace
                original_data_path=repo/'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt'
                original_data_bytes=original_data_path.read_bytes()
                if hashlib.sha256(original_data_bytes).hexdigest()!='aba97265f08a8b75437858189b7fca48e5372fa9df1d5c80252d1c459c39e79f':raise ValueError('fixed original data fixture drift')
                original_data={'Path':Path,'transport':SimpleNamespace(QUERY_NATIVE='g2_player_construction_view_probe_v1',ACTION_NATIVE='g2_player_world_building_action_private_v1'),'deepcopy':copy.deepcopy}
                exec(compile(original_data_bytes,str(original_data_path),'exec'),original_data)
                from textwrap import dedent
                from construction_python_oracle_v1 import _compile_wrapper_v1
                from test_construction_economic_outcome_v1 import completed_receipt
                setup_path=repo/'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-cash-setup.py.txt';setup_bytes=setup_path.read_bytes()
                if hashlib.sha256(setup_bytes).hexdigest()!='1f0989d17ee20d29f5e1c92639855db3d3d855b70e82c688be4fbaac12f6fe84':raise ValueError('fixed original cash fixture drift')
                setup_namespace={'completed_receipt':completed_receipt}
                _compile_wrapper_v1(setup_namespace,'def original_cash_receipt_setup(driver,route)',ast.parse(dedent(setup_bytes.decode('utf-8'))).body,'receipt')
                for expenses,selected_step,phase in [(380000,'private-submit-player-construction-v1','m5_joint_construction_typed_submit'),(20450000,'life-advance','m5_joint_construction_cash_budget_deferred')]:
                    snapshot=original_data['frame']()
                    receipt=setup_namespace['original_cash_receipt_setup'](SimpleNamespace(snapshot=snapshot),'m5')
                    cash=cash_fixture(gold=50000000,gross=450000,expenses=expenses,current=200000,all_raised=500000)
                    cash.update(snapshot_revision=snapshot['native_revision'],date_raw=snapshot['date_raw'])
                    request={'receipt':receipt,'cash':cash,'expected_revision':3,'reserve_gold_raw':20000000,'existing_commitment_gold_raw':0,'horizon_months':1}
                    query=oracle._query(request)
                    baseline={'selected_step':selected_step,'phase':phase,'construction_receipt_consumed':copy.deepcopy(receipt),'kept_extension':{'empty':[],'null':None}}
                    request['baseline']=baseline;request['receipt']=query['material_receipt']
                    expected=oracle.original('m5_enrich_original_v1',(copy.deepcopy(baseline),query))
                    cases.append({'kind':'m5','name':'original_m5_enrichment_'+str(expenses),'request':request,'expected':expected})
                consumer_requirement={'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_construction_cash_formal_decision_v1.py'],'declared_routes':4}
                sources=['ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/src/xar_autoplayer/construction_economic_outcome_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/construction_monthly_budget_v1.py','ck3_autonomous_player/tests/unit/test_construction_cash_formal_decision_v1.py','ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py','ck3_autonomous_player/tests/unit/test_construction_monthly_budget_v1.py','ck3_autonomous_player/tests/unit/test_construction_economic_outcome_v1.py','tools/ck3_live_run_id.py']
                result={'schema':'@CASH_CAPTURE_SCHEMA@','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':oracle.capture_source_refs_v1(sources),'capture_method':'Unchanged formal quote consumer and complete existing whole-cash-wire formal standalone/M5 test (4 routes), plus missing-post-cash M5 priority delegation negative. Only two M5 cash enrichment projections retained; no Game/Steam/native RPC or gameplay qualification. Controlled fixture Driver stays offline.','whole_consumer_fixture_output':consumer_requirement,'missing_post_cash_priority_regression':{'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_construction_cash_formal_decision_v1.py']},'cases':cases}
                result['producer_role']='REFERENCE_ORACLE'
                result['current_consumer_validation']='REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1([*sources,'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt','ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-cash-setup.py.txt'])
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                encoded=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\\n').encode()
                if len(encoded)>160000: raise ValueError('expanded consumer golden budget exceeded '+str(len(encoded)))
                compressed=gzip.compress(encoded,mtime=0)
                if len(compressed)>32000: raise ValueError('compressed consumer golden budget exceeded')
                with output.open('xb') as f: f.write(compressed)
                print(json.dumps({'cases':len(cases),'bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),'uncompressed_bytes':len(encoded),'uncompressed_sha256':hashlib.sha256(encoded).hexdigest(),'whole_consumer_fixture_output':consumer_requirement,'machine_id':result['machine_id'],'observed_at_utc':result['observed_at_utc']}))
            """.replace("@CASH_CAPTURE_SCHEMA@", ConstructionCashCaptureContract.REFERENCE_SCHEMA);
}

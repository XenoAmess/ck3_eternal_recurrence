package org.xar.ck3.control.wave2.development.constructioneconomy;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Offline original-producer capture; run only by the shared bounded Win32 Job owner. */
public final class CaptureConstructionEconomyGolden {
    private CaptureConstructionEconomyGolden() { }
    public static void main(String[] args) throws IOException, InterruptedException {
        if (args.length != 3) throw new IllegalArgumentException("repo python new-output required");
        Path repo = Path.of(args[0]).toAbsolutePath(), output = Path.of(args[2]).toAbsolutePath();
        if (Files.exists(output)) throw new IllegalArgumentException("output must be a new file");
        Process child = new ProcessBuilder(List.of(args[1], "-B", "-", repo.toString(), output.toString()))
                .directory(repo.toFile()).redirectOutput(ProcessBuilder.Redirect.INHERIT)
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!child.waitFor(90, TimeUnit.SECONDS)) {
            child.destroyForcibly(); throw new IllegalStateException("capture timeout; enclosing Job owns descendants");
        }
        if (child.exitValue() != 0) throw new IllegalStateException("capture exit " + child.exitValue());
        if (!Files.isRegularFile(output) || Files.size(output) == 0 || Files.size(output) > 32_000)
            throw new IllegalStateException("nonempty bounded producer output required");
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,gzip
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path.insert(0,str(repo/'ck3_autonomous_player/src'))
            sys.path.insert(0,str(repo/'ck3_autonomous_player/tests/unit'))
            sys.path.insert(0,str(repo/'tools'))
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                from test_construction_economic_outcome_v1 import completed_receipt
                from test_construction_monthly_budget_v1 import cash_fixture
                from xar_autoplayer.construction_economic_outcome_v1 import construction_economic_outcome_v1,prepare_construction_cash_fields_v1,completed_construction_cash_fields_v1,query_construction_cash_outcome_private_v1
                from xar_autoplayer.bridge.construction_monthly_budget_v1 import project_construction_monthly_budget_v1
                from xar_autoplayer.bridge.version_identity import CK3_12003
                cases=[]
                def add(name,receipt=None,build='1.20.0.4',pre=None,post=None):
                    r=completed_receipt() if receipt is None else receipt
                    request={'receipt':r,'exact_ck3_build':build,'pre_cash_v2':pre,'post_cash_v2':post}
                    expected=construction_economic_outcome_v1(r,exact_ck3_build=build,pre_cash_v2=pre,post_cash_v2=post)
                    cases.append({'kind':'outcome','name':name,'request':copy.deepcopy(request),'expected':copy.deepcopy(expected)})
                add('completed_gross_province_aggregate')
                r=completed_receipt(); r['observed_player_monthly_gold_income_raw']=400000; r['construction_province_income_observation']['native_province_monthly_income_raw']=86000
                add('zero_and_negative_aggregate',r)
                r=completed_receipt(); r['income_observed_date_raw']=199; r['construction_province_income_observation']['date_raw']=199
                add('precompletion_income_unusable',r)
                r=completed_receipt(); r['completion_status']='in_progress'; r['construction_progress_observation']={'native_remaining_work_raw':0}
                add('zero_work_still_active',r)
                r=completed_receipt(); r['postcondition_verified']=False
                add('applied_ack_without_verified_material',r)
                r=completed_receipt(); r.update(status='observed_mismatched_construction',observed_material_tuple={'building_type_id':55,'province_id':2635})
                add('mismatched_completed',r)
                r['completion_status']='in_progress'; add('mismatched_in_progress',r)
                r=completed_receipt(); r['status']='restored_before_action'; add('restored_before_action',r)
                add('legacy_gross_unqualified',build='1.19.0.6')
                r=completed_receipt(); r['pre_player_monthly_gold_income_raw']=None; r['pre_province_income_observation']=None
                add('missing_baseline_cannot_be_recreated',r)
                r=completed_receipt(); r['construction_province_income_observation']['barony_title_id']=2104
                add('province_identity_mismatch',r)
                r=completed_receipt(); r['pre_player_monthly_gold_income_raw']=-(1<<63); r['observed_player_monthly_gold_income_raw']=(1<<63)-1
                add('aggregate_delta_wider_than_i64',r)
                def interval_receipt():
                    r=completed_receipt(); r.update(actor_character_id=29829,pre_date_raw=100,action_request_id='controlled-once',episode_run_id='controlled-episode')
                    r['candidate'].update(stock_gold_cost_raw=14250000,gold_before_raw=100000000)
                    r['start_receipt']={'status':'applied','postcondition_verified':True,'action_request_id':'controlled-once','post_player_gold_raw':85750000}
                    return r
                def interval_cash(date,gold,expenses):
                    c=cash_fixture(gold=gold,gross=450000,expenses=expenses); c['date_raw']=date
                    return c
                pre=interval_cash(100,100000000,400000); post=interval_cash(224,90000000,380000)
                add('cash_net_and_wallet_verified_debit',interval_receipt(),pre=pre,post=post)
                r=interval_receipt(); r['start_receipt']['postcondition_verified']=False
                add('cash_wallet_without_verified_start_debit',r,pre=pre,post=post)
                bad=copy.deepcopy(post); bad['played_character_id']=29830
                add('cash_actor_interval_unbound',interval_receipt(),pre=pre,post=bad)
                r=interval_receipt(); r['pre_cash_v2']=copy.deepcopy(pre); r['post_cash_v2']=copy.deepcopy(post)
                add('cash_persisted_packet_fallback',r)
                def budget(name,cash,**policy):
                    request={'cash':cash,'construction_gold_cost_raw':1000000,'reserve_gold_raw':3000000,'existing_commitment_gold_raw':2000000,'horizon_months':4,**policy}
                    args={k:v for k,v in request.items() if k!='cash'}
                    cases.append({'kind':'budget','name':name,'request':request,'expected':project_construction_monthly_budget_v1(cash,**args)})
                budget('negative_net_raised_once',cash_fixture())
                budget('positive_income_not_borrowed',cash_fixture(gross=1200000,current=300000),construction_gold_cost_raw=4000000,existing_commitment_gold_raw=1000000)
                c=cash_fixture(); c['readiness']['all_raised_military_expenses_ready']=False
                c['military_expenses']['all_raised'].update(status='unavailable',unavailable_reason='native_all_raised_maintenance_unavailable',resource_raw_native=None,gold_raw=None,treasury_raw=None)
                budget('independent_current_when_raised_unknown',c)
                budget('strict_floor_first_breach',cash_fixture(gold=5000000,gross=500000),reserve_gold_raw=2000000,existing_commitment_gold_raw=1000000)
                budget('exact3_build',cash_fixture(build=CK3_12003))
                budget('arbitrary_precision_upfront_policy',cash_fixture(),construction_gold_cost_raw=10**30,existing_commitment_gold_raw=10**29)
                r=interval_receipt()
                policy={'reserve_gold_raw':3000000,'existing_commitment_gold_raw':2000000,'horizon_months':4}
                prepared=prepare_construction_cash_fields_v1(r['candidate'],pre,**policy)
                cases.append({'kind':'prepare','name':'formal_quote_prepare','request':{'receipt':r,'cash':pre,**policy},'expected':prepared})
                attached=completed_construction_cash_fields_v1(r,post,exact_ck3_build='1.20.0.4')
                cases.append({'kind':'completed','name':'material_completion_attach','request':{'receipt':r,'cash':post,'exact_ck3_build':'1.20.0.4'},'expected':attached})
                class Reader:
                    def __init__(self): self.calls=[]
                    def query_war_cash_current_resources_private_v1(self,*,expected_revision):
                        self.calls.append(expected_revision); return copy.deepcopy(post)
                driver=Reader()
                queried=query_construction_cash_outcome_private_v1(driver,expected_revision=3,material_receipt=r,**policy)
                cases.append({'kind':'query','name':'single_read_current_zero_new_spend','request':{'receipt':r,'cash':post,'expected_revision':3,**policy},'expected':queried,'expected_reader_calls':driver.calls})
                sources=['ck3_autonomous_player/src/xar_autoplayer/construction_economic_outcome_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/construction_monthly_budget_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/war_cash_private_transport_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/m5_formal_proposal_collector.py','ck3_autonomous_player/tests/unit/test_construction_economic_outcome_v1.py','ck3_autonomous_player/tests/unit/test_construction_monthly_budget_v1.py','tools/ck3_live_run_id.py']
                bindings=oracle.capture_source_refs_v1(sources)
                result={'schema':'xar.construction-economy-original-producer-golden.v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':bindings,'capture_method':'Unchanged original economic producer, monthly budget, prepare/completed and one-read query entry points; existing controlled test fixtures. No Game/Steam/native RPC or runtime qualification. Reader is an explicitly controlled offline fixture.','cases':cases}
                result['producer_role']='REFERENCE_ORACLE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1(sources)
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>160000: raise ValueError('uncompressed golden exceeds 160000 bytes: '+str(len(raw)))
                compressed=gzip.compress(raw,mtime=0)
                if len(compressed)>32000: raise ValueError('compressed golden exceeds 32000 bytes')
                output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('xb') as f: f.write(compressed)
                print(json.dumps({'cases':len(cases),'bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'machine_id':result['machine_id'],'observed_at_utc':result['observed_at_utc']}))
            """;
}

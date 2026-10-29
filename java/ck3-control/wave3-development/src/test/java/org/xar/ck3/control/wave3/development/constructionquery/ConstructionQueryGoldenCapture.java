package org.xar.ck3.control.wave3.development.constructionquery;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit original single-provider query capture; the managed shared Job is the only executor. */
public final class ConstructionQueryGoldenCapture {
    private ConstructionQueryGoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath(); if (Files.exists(output)) { throw new IllegalArgumentException("new output required"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-", arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).redirectOutput(ProcessBuilder.Redirect.INHERIT)
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!child.waitFor(100, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IllegalStateException("capture timeout; qualified Job owns tree"); }
        if (child.exitValue() != 0) { throw new IllegalStateException("actual query producer capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) <= 0 || Files.size(output) > 40_000) { throw new IllegalStateException("bounded gzip capture required"); }
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,tempfile,gzip,unittest,io
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2])
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                from xar_autoplayer.bridge.version_identity import CK3_12002,CK3_12003,CK3_12004
                import ast
                from types import SimpleNamespace
                original_data_path=repo/'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt'
                original_data_bytes=original_data_path.read_bytes()
                if hashlib.sha256(original_data_bytes).hexdigest()!='aba97265f08a8b75437858189b7fca48e5372fa9df1d5c80252d1c459c39e79f':raise ValueError('fixed original data fixture drift')
                original_data={'Path':Path,'transport':SimpleNamespace(QUERY_NATIVE='g2_player_construction_view_probe_v1',ACTION_NATIVE='g2_player_world_building_action_private_v1'),'deepcopy':copy.deepcopy}
                exec(compile(original_data_bytes,str(original_data_path),'exec'),original_data)
                import math,time,uuid
                from collections.abc import Mapping
                from xar_autoplayer.bridge.driver import BridgeUnavailableError
                from xar_autoplayer.bridge.nonwar_private_build import private_native_build_identity,private_native_provenance
                from xar_autoplayer.bridge.construction_owner_mode3_inputs_12004 import normalize_mode3_world_observation_12004
                from xar_autoplayer.bridge.version_identity import CK3_11906
                original_transport=dict(oracle.namespace)
                original_transport.update(Mapping=Mapping,json=json,math=math,time=time,uuid=uuid,BridgeUnavailableError=BridgeUnavailableError,
                    private_native_build_identity=private_native_build_identity,private_native_provenance=private_native_provenance,
                    normalize_mode3_world_observation_12004=normalize_mode3_world_observation_12004,CK3_11906=CK3_11906)
                tree=ast.parse((oracle.fixtures/'domain_construction_private_transport_v1.py.txt').read_text(encoding='utf-8'))
                names={'_positive','_query_context_snapshot','_binding','_diagnostic_scalar','_construction_failure_diagnostic','_send','query_construction_private'}
                nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
                nodes += [node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in {'QUERY_NATIVE','_CONSTRUCTION_DIAGNOSTIC_MARKER','_CONSTRUCTION_DIAGNOSTIC_LIMIT'} for target in node.targets)]
                if len([node for node in nodes if isinstance(node,ast.FunctionDef)])!=len(names):raise ValueError('fixed original query function closure drift')
                exec(compile(ast.Module(body=nodes,type_ignores=[]),'fixed-original-construction-query-producer','exec'),original_transport)
                transport=SimpleNamespace(QUERY_NATIVE=original_transport['QUERY_NATIVE'],query_construction_private=original_transport['query_construction_private'])
                Driver=original_data['Driver']
                fixture_path='ck3_autonomous_player/tests/unit/fixtures/construction_material_outside_projection.json'
                fixture=json.loads((repo/fixture_path).read_text(encoding='utf-8'))
                class ObservedDriver(Driver):
                    def __init__(self,directory,envelope_change=None,ending_change=None):
                        super().__init__(directory);self.envelope_change=envelope_change;self.ending_change=ending_change;self.actual_envelope=None
                    def wait_for_command_result(self,request_id,timeout):
                        response=super().wait_for_command_result(request_id,timeout)
                        if self.envelope_change:self.envelope_change(response)
                        self.actual_envelope=copy.deepcopy(response)
                        if self.ending_change:self.ending_change(self.snapshot)
                        return response
                cases=[]
                def world(response):return response['result']['private_probe']['player_world_building_sources']
                def probe(response):return response['result']['private_probe']
                def add(name,setup=None,envelope_change=None,ending_change=None,material=False,wartime=False,strict=False,build=None):
                    with tempfile.TemporaryDirectory(prefix='construction-query-') as work:
                        driver=ObservedDriver(Path(work),envelope_change,ending_change)
                        if build is not None:driver.snapshot['diagnostics']={'hello':{'expected_ck3_version':build.game_version,'expected_ck3_sha256':build.executable_sha256}}
                        if setup:setup(driver)
                        starting=driver.take_snapshot()
                        try:expected=transport.query_construction_private(driver,expected_revision=3,material_receipt=material,wartime_observation=wartime)
                        except (ValueError,RuntimeError) as error:expected={'status':'read_rejected','reason':str(error)}
                        ending=driver.take_snapshot();request_id=driver.requests[-1]['request_id'] if driver.requests else 'not-dispatched'
                        if any(row['step']!=transport.QUERY_NATIVE for row in driver.requests):raise ValueError('actual fixture emitted a non-read request')
                        request={'schema':'xar.construction-query-observation-input.v1','starting_snapshot':starting,'ending_snapshot':ending,
                            'native_envelope':driver.actual_envelope,'expected_revision':3,'native_query_request_id':request_id,
                            'material_receipt':material,'wartime_observation':wartime}
                        cases.append({'name':name,'input_json':json.dumps(request,ensure_ascii=False,separators=(',',':')),'expected':expected,'java_strict_reject':strict,
                            'actual_native_request_count':len(driver.requests),'actual_native_steps':[row['step'] for row in driver.requests]})
                add('legacy_original_source')
                add('exact2_original_source',build=CK3_12002)
                add('exact3_original_source',build=CK3_12003)
                add('exact4_original_source',build=CK3_12004)
                add('invalid_combined_modes',material=True,wartime=True)
                add('unpaused_before_dispatch',setup=lambda d:d.snapshot.update(paused=False))
                add('map_not_ready_before_dispatch',setup=lambda d:d.snapshot.update(map_ready=False))
                add('event_blocks_before_dispatch',setup=lambda d:d.snapshot.update(active_event={'event_id':'test'}))
                add('wrong_expected_public_revision',setup=lambda d:d.snapshot.update(revision=4))
                add('missing_episode_ordinary',setup=lambda d:d.snapshot.pop('episode_run_id'))
                add('missing_episode_wartime_observation',setup=lambda d:d.snapshot.pop('episode_run_id'),wartime=True)
                add('material_cost_not_evaluated',setup=lambda d:setattr(d,'r0080_material_without_cost',True),material=True)
                add('material_no_new_samples',envelope_change=lambda r:world(r).update(legal_samples=[],native_cost_evaluated=False),material=True)
                add('ordinary_cost_not_evaluated',envelope_change=lambda r:world(r).update(native_cost_evaluated=False))
                add('covered_no_candidate',envelope_change=lambda r:world(r).update(legal_samples=[]))
                add('incomplete_no_candidate',envelope_change=lambda r:world(r).update(legal_samples=[],positive_income_coverage_complete=False))
                add('unknown_wallet_source_red',setup=lambda d:setattr(d,'unknown_gold',True))
                add('wrong_actor_source_red',envelope_change=lambda r:world(r).update(player_character_id=44))
                add('stale_world_revision',envelope_change=lambda r:world(r).update(snapshot_revision=2))
                add('stale_probe_date',envelope_change=lambda r:probe(r).update(date_raw=53178311))
                add('missing_final_legality',envelope_change=lambda r:world(r).update(native_final_legality_evaluated=False))
                add('wrong_result_step',envelope_change=lambda r:r['result'].update(step='other'))
                add('rejected_result',envelope_change=lambda r:r['result'].update(accepted=False))
                add('zero_proof_epoch',envelope_change=lambda r:probe(r).update(proof_epoch=0))
                add('changed_ending_snapshot',ending_change=lambda s:s.update(snapshot_id='native:4'))
                add('changed_ending_public_revision',ending_change=lambda s:s.update(revision=4))
                add('changed_ending_episode',ending_change=lambda s:s.update(episode_run_id='another'))
                add('envelope_failed',envelope_change=lambda r:r.update(ok=False))
                add('envelope_wrong_request',envelope_change=lambda r:r.update(request_id='other'))
                add('envelope_wrong_type',envelope_change=lambda r:r.update(type='other'))
                add('raw_float_protocol',envelope_change=lambda r:r.update(protocol_version=1.0),strict=True)
                add('raw_float_world_revision',envelope_change=lambda r:world(r).update(snapshot_revision=3.0),strict=True)
                add('raw_float_wallet',envelope_change=lambda r:world(r).update(player_gold_raw=50000000.0),strict=True)
                add('sdk_fraction_extension',envelope_change=lambda r:world(r).update(unconsumed={'fraction':1.25}))
                def mode3(response):
                    packet=copy.deepcopy(fixture['material']['world']['native_mode3_inputs']);row=packet['holdings'][0];packet['holdings']=[row]
                    packet.update(snapshot_revision=3,date_raw=53178312,player_character_id=29829)
                    row.update(barony_title_id=2103,province_id=2635);row['inputs'].update(snapshot_revision=3,province_id=2635)
                    world(response)['native_mode3_inputs']=packet
                add('independent_mode3_available',envelope_change=mode3,build=CK3_12004)
                add('independent_mode3_null',envelope_change=lambda r:world(r).update(native_mode3_inputs=None),build=CK3_12004)
                add('independent_mode3_bad_claim_keeps_candidate',envelope_change=lambda r:(mode3(r),world(r)['native_mode3_inputs']['holdings'][0]['inputs'].update(per_building_attribution=True)),build=CK3_12004)
                add('independent_mode3_float_keeps_candidate',envelope_change=lambda r:(mode3(r),world(r)['native_mode3_inputs']['holdings'][0]['inputs'].update(context_factor_raw=60000.0)),build=CK3_12004)
                names=['test_blocked_war_plan_still_observes_same_frame_m5_building','test_wartime_construction_observes_native_choice_without_spend',
                    'test_wartime_one_shot_can_include_source_world_without_spend','test_formal_service_retains_war_step_with_read_only_building_observation',
                    'test_r753_truncated_scan_keeps_six_native_legal_cost_samples','test_r0080_material_mode_still_rejects_unknown_gold',
                    'test_unknown_gold_is_red_not_no_legal_building','test_r0060_public_revision_after_native_root_query_reaches_construction']
                consumer_requirement={'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_construction_formal_private_consumer.py'],'declared_test_names':names}
                sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/nonwar_private_build.py',
                    'ck3_autonomous_player/src/xar_autoplayer/bridge/construction_economic_value_v1.py','ck3_autonomous_player/src/xar_autoplayer/bridge/construction_owner_mode3_inputs_12004.py',
                    'ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py',fixture_path,'tools/ck3_live_run_id.py']
                result={'schema':'xar.construction-query-original-producer-golden.v2','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_refs':oracle.capture_source_refs_v1(sources),
                    'capture_scope':'Unchanged full query_construction_private with original deterministic read Driver and actual returned envelope/request IDs. Real planner/service/M5 consumer regressions executed separately; selected compatibility cases are not complete Python CI. No Game, native pipe, submit or canonical ledger.',
                    'consumer_regressions':consumer_requirement,'cases':cases}
                result['producer_role']='REFERENCE_ORACLE'
                result['current_consumer_validation']='REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1([*sources,'ck3_autonomous_player/tests/fixtures/construction_python_oracle_v1/construction-original-data-fixtures.py.txt'])
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>786432:raise ValueError('bounded decompressed capture exceeded')
                compressed=gzip.compress(raw,mtime=0)
                if len(compressed)>40000:raise ValueError('compressed capture exceeded')
                output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('xb') as handle:handle.write(compressed)
                print(json.dumps({'machine_id':result['machine_id'],'cases':len(cases),'bytes':len(compressed),'decompressed_bytes':len(raw),'sha256':hashlib.sha256(compressed).hexdigest()}))
            """;
}

package org.xar.ck3.control.wave2.development.constructionmode3;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Explicit bounded capture of the unchanged independent native copied-input producer and both consumers. */
public final class ConstructionMode3GoldenCapture {
    private ConstructionMode3GoldenCapture() { }
    public static void main(String[] arguments) throws IOException, InterruptedException {
        if (arguments.length != 3) { throw new IllegalArgumentException("repo python new-gzip-output required"); }
        Path output = Path.of(arguments[2]).toAbsolutePath(); if (Files.exists(output)) { throw new IllegalArgumentException("new output required"); }
        Process child = new ProcessBuilder(List.of(arguments[1], "-", arguments[0], output.toString()))
                .directory(Path.of(arguments[0]).toFile()).redirectOutput(ProcessBuilder.Redirect.INHERIT)
                .redirectError(ProcessBuilder.Redirect.INHERIT).start();
        try (var input = child.getOutputStream()) { input.write(SCRIPT.getBytes(StandardCharsets.UTF_8)); }
        if (!child.waitFor(100, TimeUnit.SECONDS)) { child.destroyForcibly(); throw new IllegalStateException("capture timeout; parent Job owns tree"); }
        if (child.exitValue() != 0) { throw new IllegalStateException("actual producer capture exit " + child.exitValue()); }
        if (!Files.isRegularFile(output) || Files.size(output) <= 0 || Files.size(output) > 32_000) { throw new IllegalStateException("bounded compressed capture required"); }
    }
    private static final String SCRIPT = """
            import sys,json,copy,hashlib,datetime,gzip
            from pathlib import Path
            repo=Path(sys.argv[1]);output=Path(sys.argv[2])
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'tools')]
            sys.path.insert(0,str(repo/'ck3_autonomous_player/tests/unit'))
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                from xar_autoplayer.bridge import construction_owner_mode3_inputs_12004 as module
                from xar_autoplayer.bridge.version_identity import CK3_12004,NativeBuildIdentity
                fixture_path='ck3_autonomous_player/tests/unit/fixtures/construction_material_outside_projection.json'
                fixture=json.loads((repo/fixture_path).read_text(encoding='utf-8'))['material']
                base={key:copy.deepcopy(fixture['world'][key]) for key in ['snapshot_revision','date_raw','player_character_id','native_mode3_inputs']}
                base['active_constructions']=[{key:row[key] for key in ['barony_title_id','province_id']} for row in fixture['world']['active_constructions']]
                cases=[]
                def add(name,change=None,barony=2232,province=2619):
                    request={'schema':'xar.construction-mode3-input.v1','world':copy.deepcopy(base),'source_frame':copy.deepcopy(fixture['source_frame']),
                        'build':{'game_version':CK3_12004.game_version,'executable_sha256':CK3_12004.executable_sha256},'barony_title_id':barony,'province_id':province}
                    if change:change(request)
                    world,observation=module.normalize_mode3_world_observation_12004(request['world'],source_frame=request['source_frame'],build=NativeBuildIdentity(**request['build']))
                    source={'world':world,'source_frame':request['source_frame'],**observation}
                    selected=module.mode3_province_observation_12004(source,barony_title_id=barony,province_id=province)
                    cases.append({'name':name,'input_json':json.dumps(request,ensure_ascii=False,separators=(',',':')),
                        'expected':{'world':world,'observation':observation,'province_observation':selected}})
                def packet(r):return r['world']['native_mode3_inputs']
                def inputs(r):return packet(r)['holdings'][0]['inputs']
                add('actual_conditional_projection')
                add('actual_second_holding_nullable_child',barony=2235,province=2617)
                add('different_holding_not_attributed',barony=2192,province=2635)
                add('packet_absent',lambda r:r['world'].pop('native_mode3_inputs'))
                add('packet_null',lambda r:r['world'].update(native_mode3_inputs=None))
                add('unobserved_frame',lambda r:packet(r).update(current_frame_observed=False,failure='paused_frame',snapshot_revision=None,date_raw=None,player_character_id=None,holdings=[]))
                add('unobserved_invented_metadata',lambda r:packet(r).update(current_frame_observed=False))
                add('wrong_build_version',lambda r:r['build'].update(game_version='1.20.1'))
                add('wrong_build_sha',lambda r:r['build'].update(executable_sha256='0'*64))
                add('wrong_packet_sha',lambda r:packet(r).update(source_executable_sha256='0'*64))
                add('wrong_packet_schema',lambda r:packet(r).update(schema='other'))
                add('unknown_native_failure',lambda r:packet(r).update(failure='unreviewed'))
                add('packet_source_frame_mismatch',lambda r:packet(r).update(snapshot_revision=512))
                add('packet_world_frame_mismatch',lambda r:r['world'].update(snapshot_revision=512))
                add('held_identity_missing',lambda r:r['world'].update(active_constructions=[]))
                add('world_duplicate_identity',lambda r:r['world']['active_constructions'].append(copy.deepcopy(r['world']['active_constructions'][0])))
                add('packet_duplicate_holding',lambda r:packet(r)['holdings'].append(copy.deepcopy(packet(r)['holdings'][0])))
                add('inputs_revision_mismatch',lambda r:inputs(r).update(snapshot_revision=512))
                add('inputs_province_mismatch',lambda r:inputs(r).update(province_id=2618))
                add('inputs_frame_metadata_null',lambda r:inputs(r).update(snapshot_revision=None))
                add('inputs_unobserved',lambda r:inputs(r).update(inputs_observed=False))
                add('reached_inputs_incomplete',lambda r:inputs(r).update(all_reached_inputs_observed=False))
                add('aggregate_null',lambda r:inputs(r).update(conditional_aggregate_raw=None))
                add('observed_zero_aggregate',lambda r:inputs(r).update(conditional_aggregate_raw=0))
                add('component_order_retained',lambda r:inputs(r)['components'].reverse())
                add('signed_q64_boundaries',lambda r:inputs(r).update(factor_before_context=-(2**63),owner_factor_raw=2**63-1))
                add('unsigned_key_max',lambda r:inputs(r).update(context_dynamic_key=65535))
                def max_revision(r):
                    packet(r)['snapshot_revision']=2**64-1;r['source_frame']['native_revision']=2**64-1;r['world']['snapshot_revision']=2**64-1
                    for row in packet(r)['holdings']:row['inputs']['snapshot_revision']=2**64-1
                add('unsigned_revision_max',max_revision)
                for flag in ['observed_native_producer_call','per_building_attribution','realized_holder_net']:
                    add('reject_claim_'+flag,lambda r,flag=flag:inputs(r).update({flag:True}))
                add('raw_boolean_revision',lambda r:packet(r).update(snapshot_revision=True))
                add('raw_float_q64',lambda r:inputs(r).update(context_factor_raw=60000.0))
                add('raw_exponent_q64',lambda r:inputs(r).update(context_factor_raw=60000.0))
                cases[-1]['input_json']=cases[-1]['input_json'].replace('"context_factor_raw":60000.0','"context_factor_raw":6e4')
                add('raw_string_key',lambda r:inputs(r).update(context_dynamic_key='1400'))
                add('out_of_range_key',lambda r:inputs(r).update(context_dynamic_key=65536))
                add('out_of_range_q64',lambda r:inputs(r).update(owner_factor_raw=2**63))
                add('component_unknown_field',lambda r:inputs(r)['components'][0].update(extra=True))
                add('component_missing_field',lambda r:inputs(r)['components'][0].pop('reached'))
                add('holding_unknown_field',lambda r:packet(r)['holdings'][0].update(extra=True))
                add('sdk_extension_fraction',lambda r:r['world'].update(unconsumed_extension={'fraction':1.25,'native_future_component':'retained'}))
                sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/construction_owner_mode3_inputs_12004.py','ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py',fixture_path,'ck3_autonomous_player/src/xar_autoplayer/bridge/version_identity.py','tools/ck3_live_run_id.py']
                result={'schema':'xar.construction-mode3-original-producer-golden.v1','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_refs':oracle.capture_source_refs_v1(sources),
                    'capture_scope':'Unchanged actual copied-input normalizer, independent world status consumer and per-province consumer. Exact retained actual material packet; consumed world projection with explicit controlled variants. No Game/native call/attribution/realised net.',
                    'historical_material_machine_id':'unknown','cases':cases}
                result['producer_role']='REFERENCE_ORACLE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1(sources)
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\\n').encode('utf-8')
                if len(raw)>524288:raise ValueError('bounded decompressed golden cap exceeded')
                compressed=gzip.compress(raw,mtime=0)
                if len(compressed)>32000:raise ValueError('compressed golden cap exceeded')
                output.parent.mkdir(parents=True,exist_ok=True)
                with output.open('xb') as handle:handle.write(compressed)
                print(json.dumps({'machine_id':result['machine_id'],'cases':len(cases),'bytes':len(compressed),'decompressed_bytes':len(raw),'sha256':hashlib.sha256(compressed).hexdigest()}))
            """;
}

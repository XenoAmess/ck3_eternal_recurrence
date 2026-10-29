package org.xar.ck3.control.wave3.development.constructiondiagnostics;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.concurrent.TimeUnit;

/** Original bounded failure producer plus registered synthetic consumer; shared Job execution only. */
public final class CaptureConstructionDiagnosticGolden {
    private CaptureConstructionDiagnosticGolden() { }
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
            import sys,json,copy,hashlib,datetime,gzip,tempfile,os
            from pathlib import Path
            repo=Path(sys.argv[1]); output=Path(sys.argv[2])
            sys.path[:0]=[str(repo/'ck3_autonomous_player/src'),str(repo/'ck3_autonomous_player/tests/unit'),str(repo/'tools')]
            from construction_python_oracle_v1 import ConstructionPythonOracleV1
            from construction_java_fixture_v1 import construction_reference_oracle_context_v1
            oracle=ConstructionPythonOracleV1(repo)
            with construction_reference_oracle_context_v1(oracle.reference_exchange()):
                from ck3_live_run_id import current_machine_id
                import ast,math
                from collections.abc import Mapping
                original_diagnostic={'Mapping':Mapping,'json':json,'math':math}
                tree=ast.parse((oracle.fixtures/'domain_construction_private_transport_v1.py.txt').read_text(encoding='utf-8'))
                names={'_construction_failure_diagnostic','_diagnostic_scalar','construction_transport_diagnostic'}
                nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
                nodes += [node for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in {'_CONSTRUCTION_DIAGNOSTIC_MARKER','_CONSTRUCTION_DIAGNOSTIC_LIMIT'} for target in node.targets)]
                if len([node for node in nodes if isinstance(node,ast.FunctionDef)])!=len(names):raise ValueError('fixed original diagnostic closure drift')
                exec(compile(ast.Module(body=nodes,type_ignores=[]),'fixed-original-construction-diagnostics','exec'),original_diagnostic)
                _construction_failure_diagnostic=original_diagnostic['_construction_failure_diagnostic'];_diagnostic_scalar=original_diagnostic['_diagnostic_scalar'];construction_transport_diagnostic=original_diagnostic['construction_transport_diagnostic']
                cases=[]
                def base():
                    return {'type':'command_result','protocol_version':1,'request_id':'controlled-request','ok':False,'error':'native rejection '+('界'*3000),'result':{'step':'native-test','accepted':False},'private_probe':{'status':'unavailable','failure':'controlled_source_read_failed','schema_version':1,'advertised':False,'snapshot_revision':3,'date_raw':53290296,'proof_epoch':30,'player_model_sources':{'status':'unavailable','failure':'model_failed','snapshot_revision':3,'date_raw':53290296,'player_character_id':29829},'player_world_building_sources':{'status':'unavailable','failure':'definition_identity','definition_identity_diagnostic':{'stage':'selected_definition_identity','failed_index':7},'unknown_rows':[{'payload':'not diagnostic truth'}]}}}
                def add(name,frame,*,revision=3,request_id='controlled-request',step='query-player-domain-construction-v1',timeout=17.0,elapsed=0.123456789,changed=False):
                    result=frame.get('result') if isinstance(frame,dict) else None
                    request={'schema':'xar.construction-diagnostic-input.v1','frame':frame,'step':step,'revision':revision,'request_id':request_id,'timeout_seconds':timeout,'wait_elapsed_seconds':elapsed,'frame_python_type':type(frame).__name__,'result_python_type':type(result).__name__}
                    expected=_construction_failure_diagnostic(frame,step=step,revision=revision,request_id=request_id,timeout_seconds=timeout,wait_elapsed_seconds=elapsed)
                    if len(json.dumps(expected,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode())>4096: raise ValueError('original diagnostic exceeded source budget')
                    cases.append({'kind':'projection','name':name,'request_json':json.dumps(request,ensure_ascii=True,separators=(',',':'),allow_nan=False),'expected':expected,'intentional_strict_protocol_change':changed})
                add('matched_native_rejected',base())
                add('absent_result_unknown',None)
                add('list_frame',[])
                add('boolean_frame',True)
                add('integer_frame',17)
                add('float_frame',1.25)
                add('text_frame','malformed')
                f=base(); f['request_id']='foreign'; add('foreign_request_hides_native_fields',f)
                f=base(); f['type']='unexpected'; add('foreign_type_hides_native_fields',f)
                f=base(); f['protocol_version']=2; add('foreign_protocol_hides_native_fields',f)
                f=base(); f['protocol_version']=True; add('legacy_bool_protocol_rejected_in_java',f,changed=True)
                f=base(); f['protocol_version']=1.0; add('legacy_float_protocol_rejected_in_java',f,changed=True)
                f=base(); f['ok']=True; f['result']=[]; add('invalid_result_array',f)
                f=base(); f['ok']=None; f.pop('result'); add('invalid_result_absent',f)
                f=base(); f['result']={'step':{'unexpected':True},'accepted':[1]}; f['error']={'unexpected':'object'}; add('container_values_not_copied',f)
                f=base(); f['private_probe']['proof_epoch']=1<<63; f['private_probe']['schema_version']=-(1<<63); add('int64_scalar_boundary',f,revision=(1<<64)-1)
                f=base(); f['error']='\\ud800'*20; add('malformed_surrogate_replaced',f)
                f=base(); f['private_probe']['failure']='😀'*300; f['error']='界😀'*1000; add('utf8_cut_never_splits_character',f)
                f=base(); f['private_probe']['player_world_building_sources']['unknown_rows']=[{'payload':'x'*256} for _ in range(2500)]; add('large_unknown_world_rows_not_retained',f)
                f=base(); f['request_id']='長'*300; add('long_identity_matches_before_output_clipping',f,request_id=f['request_id'],step='步'*1000)
                LongFrame=type('F'*160,(dict,),{}); LongResult=type('R'*160,(dict,),{})
                f=LongFrame(base()); f['result']=LongResult({'step':'x'*5000,'accepted':'x'*5000}); f['error']='x'*5000
                for key in ['status','failure','schema_version','advertised','snapshot_revision','date_raw','proof_epoch']: f['private_probe'][key]='x'*5000
                for key in ['status','failure','snapshot_revision','date_raw','player_character_id']: f['private_probe']['player_model_sources'][key]='x'*5000
                for key in ['status','failure']: f['private_probe']['player_world_building_sources'][key]='x'*5000
                f['private_probe']['player_world_building_sources']['definition_identity_diagnostic']={'stage':'x'*5000,'failed_index':'x'*5000}
                f['request_id']='x'*5000; add('maximum_scalar_text_bounded_mapping_types',f,request_id=f['request_id'],step='x'*5000,timeout='x'*5000,elapsed=1.7976931348623157e308)
                for value in [0.0000005,1.2345665,-0.0000001,1e20,1e-7]: add('rounded_elapsed_'+repr(value),base(),elapsed=value,timeout=value)
                for name,value,limit in [('null',None,128),('bool',True,128),('i64max',(1<<63)-1,128),('over_i64',1<<63,128),('negative_i64',-(1<<63),128),('float',1.25,128),('utf8','界'*200,128),('emoji','😀'*10,5),('object',{'not':'copied'},128),('array',[1,2],128)]:
                    cases.append({'kind':'scalar','name':'scalar_'+name,'value':value,'text_limit':limit,'expected':_diagnostic_scalar(value,limit)})
                for label,value in [('nan',float('nan')),('positive_infinity',float('inf')),('negative_infinity',float('-inf'))]:
                    cases.append({'kind':'nonfinite_scalar','name':'scalar_'+label,'label':label,'expected':_diagnostic_scalar(value)})
                attached=_construction_failure_diagnostic(base(),step='query-test',revision=3,request_id='controlled-request',timeout_seconds=1.0,wait_elapsed_seconds=0.1)
                error=RuntimeError('original fixture'); error._construction_transport_diagnostic=attached
                cases.append({'kind':'attachment','name':'original_exception_attachment','value':attached,'expected':construction_transport_diagnostic(error)})
                sources=['ck3_autonomous_player/src/xar_autoplayer/bridge/domain_construction_private_transport_v1.py','ck3_autonomous_player/src/xar_autoplayer/construction_formal_consumer.py','ck3_autonomous_player/src/xar_autoplayer/bridge/service.py','ck3_autonomous_player/tests/unit/test_construction_failure_diagnostic_registered_consumer.py','ck3_autonomous_player/tests/unit/test_construction_formal_private_consumer.py','tools/ck3_live_run_id.py']
                result={'schema':'xar.construction-diagnostic-original-producer-golden.v2','machine_id':current_machine_id(),'observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_bindings':oracle.capture_source_refs_v1(sources),'capture_method':'Unchanged three original diagnostic functions, then complete registered in-process MCP synthetic consumer regression (three failure modes, pending unchanged, no resubmit). Endpoint callbacks are controlled fixtures; no Game/Steam/native pipe/production ledger or source qualification. Two captured legacy protocol type bugs are retained explicitly for Java strict-int rejection.','registered_consumer_regression':{'status':'NOT_EXECUTED_REFERENCE_CAPTURE','required_actual_host_modules':['test_construction_failure_diagnostic_registered_consumer.py'],'declared_failure_modes':3},'cases':cases}
                result['producer_role']='REFERENCE_ORACLE'
                result['current_consumer_validation']='REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE'
                result['reference_oracle']={'kind':'fixed-original-python-source-ast/v1','Java_calls':0,'actual_HTTP_calls':0,'grants_runtime_qualification':False,'original_source_sha256':list(oracle.reference_exchange().original_source_sha256),'fixture_exchange_calls':len(oracle.calls)}
                result['execution_source_refs']=oracle.capture_execution_refs_v1(sources)
                result['original_source_metadata_ref']=oracle.capture_execution_refs_v1([])[-1]
                for capture_description in ('capture_scope','capture_method'):
                    if capture_description in result: result[capture_description]='REFERENCE_ORACLE: fixed original Python producers and exact historical AST/data fixtures only. Current production consumers require the unified actual Java host full suite. Zero Java/actual HTTP/native/Game qualification; not complete Python CI.'
                raw=(json.dumps(result,ensure_ascii=True,sort_keys=True,separators=(',',':'),allow_nan=False)+'\\n').encode('ascii')
                if len(raw)>1572864: raise ValueError('expanded diagnostic golden budget exceeded '+str(len(raw)))
                compressed=gzip.compress(raw,mtime=0)
                if len(compressed)>32000: raise ValueError('compressed diagnostic golden budget exceeded')
                with output.open('xb') as f: f.write(compressed)
                print(json.dumps({'cases':len(cases),'bytes':len(compressed),'sha256':hashlib.sha256(compressed).hexdigest(),'uncompressed_bytes':len(raw),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'machine_id':result['machine_id'],'observed_at_utc':result['observed_at_utc']}))
            """;
}

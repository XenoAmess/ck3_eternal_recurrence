package org.xar.ck3.control.wave3.runtime.childexports;

/**
 * Regression fixture source consumed by the existing coordinated capture/stdio harness.
 * No main, subprocess launcher or independent service is supplied.
 */
public final class ChildExportCallbackDifferentialFixture {
    private ChildExportCallbackDifferentialFixture() { }

    public static String pythonSource() { return PROGRAM; }

    /** Mechanical binding to the single existing source-qualified client; no HTTP implementation or retry. */
    public static String sharedClientBindingSource() { return CLIENT_BINDING; }

    private static final String CLIENT_BINDING = """
            def run_child_export_callback_with_current_projection_client(request_id_prefix: str) -> dict[str, object]:
                from tools.g2_saved_campaign.java_map_admission_client_v1 import (
                    ProjectionOperation, call_projection_v1, require_current_projection_config_v1, require_result_context_v1,
                    qualify_projection_service_v1, encode_projection_payload_v1, decode_projection_json_v1)
                if type(request_id_prefix) is not str or not request_id_prefix or len(request_id_prefix)>80:
                    raise ValueError('finite explicit child callback request identity required')
                config=require_current_projection_config_v1()
                qualify_projection_service_v1(config)
                calls=[0]
                def dispatch(payload):
                    calls[0]+=1
                    operation=ProjectionOperation.CHILD_EXPORT_PROJECT
                    raw_payload=encode_projection_payload_v1(payload,maximum_bytes=32768)
                    request_id=request_id_prefix+'-'+str(calls[0])
                    result=call_projection_v1(config=config,operation=operation,payload=raw_payload,request_id=request_id)
                    require_result_context_v1(result,config=config,operation=operation,request_id=request_id,payload=raw_payload)
                    result.require_success()
                    reply=decode_projection_json_v1(result.result_bytes,maximum_bytes=32768)
                    if type(reply) is not dict:raise TypeError('actual Java child callback result object required')
                    return reply
                # Only the existing client's actual domain-rejection ValueError is caught in token cases.
                # Transport/source/PID unavailability stays its RuntimeError branch and aborts this fixture.
                return run_child_export_callback_differential(dispatch)
            """;

    private static final String PROGRAM = """
            from collections.abc import Callable
            from typing import TypedDict,Literal,TypeVar
            _ChildExportStageValue=TypeVar('_ChildExportStageValue')
            
            class _ChildWirePayload(TypedDict):
                schema: Literal['xar.java.child-export-callback-input/v1']
                operation: Literal['CANONICALIZE_WIRE']
                retained_role: str
                wire_base64: str
            
            class _ChildReadbackPayload(TypedDict):
                schema: Literal['xar.java.child-export-callback-input/v1']
                operation: Literal['VALIDATE_READBACKS']
                retained_role: str
                keys_json_base64: str
            
            def run_child_export_callback_differential(dispatch: Callable[[_ChildWirePayload | _ChildReadbackPayload], dict[str, object]]) -> dict[str, object]:
                import base64,ctypes,json,threading,sys,inspect
                from types import SimpleNamespace,FrameType,FunctionType
                from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as contract
                from xar_autoplayer.bridge import native_loaded_provider_origin_v1 as origin
                from xar_autoplayer.bridge.native_loaded_provider_origin_io_v1 import OriginKernelIOV1
                from xar_autoplayer.bridge import native_loaded_provider_origin_io_v1 as origin_io
                from tools.g2_saved_campaign import canonical_native_provider_chain_v1 as chain
                from tools.g2_saved_campaign.java_map_admission_client_v1 import ProjectionDomainRejected
                callback_rows=[]
                methods=[]
                production_rows=[]
                production_stages=[]
                helper=getattr(origin_io,'_call_child_exports_projection_v1',None)
                if not isinstance(helper,FunctionType) or helper.__module__!=origin_io.__name__:
                    raise AssertionError('actual SDK Java callback helper required; legacy Python-only baseline is not admitted')
                for helper_name in ('_qualified_child_exports_config_v1','_child_export_wire_v1','_validate_child_readbacks_via_java_v1'):
                    actual_helper=getattr(origin_io,helper_name,None)
                    if not isinstance(actual_helper,FunctionType) or actual_helper.__module__!=origin_io.__name__:
                        raise AssertionError('complete original SDK mechanical Java callbacks required: '+helper_name)
                if not {'child_exports_role','projection_config'}.issubset(inspect.signature(OriginKernelIOV1.recv).parameters):
                    raise AssertionError('actual SDK private-receive Java callback parameters required')
                if (getattr(chain,'_qualified_child_exports_config_v1',None) is not getattr(origin_io,'_qualified_child_exports_config_v1',None)
                    or getattr(origin,'_qualified_child_exports_config_v1',None) is not getattr(origin_io,'_qualified_child_exports_config_v1',None)
                    or getattr(chain,'_child_export_wire_v1',None) is not getattr(origin_io,'_child_export_wire_v1',None)
                    or getattr(origin,'_validate_child_readbacks_via_java_v1',None) is not getattr(origin_io,'_validate_child_readbacks_via_java_v1',None)):
                    raise AssertionError('original imported SDK callbacks must retain the same mechanical Java helpers')
                helper_code=helper.__code__
                def production_stage(name: str,expected: tuple[tuple[str,str],...],invoke: Callable[[],_ChildExportStageValue]) -> _ChildExportStageValue:
                    previous=sys.getprofile()
                    if previous is not None:raise RuntimeError('actual callback profiler is already occupied')
                    attempted=[]
                    completed=[]
                    def observe(frame: FrameType,event: str,value: object) -> None:
                        if frame.f_code is not helper_code or event not in ('call','return'):return
                        payload=frame.f_locals.get('payload')
                        if type(payload) is not dict:raise AssertionError('actual production callback payload object required')
                        operation=payload.get('operation');role=payload.get('retained_role')
                        if type(operation) is not str or type(role) is not str:raise AssertionError('actual production callback identity required')
                        if event=='call':attempted.append((operation,role))
                        elif type(value) is dict:
                            completed.append((operation,role))
                            production_rows.append(dict(stage=name,payload=dict(payload),java_result=dict(value)))
                    try:
                        sys.setprofile(observe)
                        result=invoke()
                    finally:sys.setprofile(previous)
                    if tuple(attempted)!=expected or tuple(completed)!=expected:
                        raise AssertionError('actual SDK stage did not consume every original issued Java callback exactly once: '+name)
                    production_stages.append(dict(stage=name,attempted_callbacks=len(attempted),completed_callbacks=len(completed)))
                    return result
                birth=134368602545256921
                identities={}
                for index,pid in enumerate((71,72,73)):
                    identities[1001+index]=contract._ProcessReadbackV1(pid,birth+index,'2026-10-19T05:10:54.525692'+str(index+1)+'Z','C:/own/python.exe',True)
                def wire_call(role,raw):
                    payload=dict(schema='xar.java.child-export-callback-input/v1',operation='CANONICALIZE_WIRE',retained_role=role,wire_base64=base64.b64encode(raw).decode('ascii'))
                    result=dispatch(payload)
                    if set(result)!={'schema','operation','retained_role','wire_base64','export_count'}:raise AssertionError('actual child callback reply fields differ')
                    if result['schema']!='xar.java.child-export-callback-result/v1' or result['operation']!='CANONICALIZE_WIRE' or result['retained_role']!=role:raise AssertionError('actual child callback reply identity differs')
                    if type(result['export_count']) is not int:raise AssertionError('actual export count token type differs')
                    raw_result=base64.b64decode(result['wire_base64'],validate=True)
                    callback_rows.append(dict(payload=payload,java_result=result))
                    return raw_result
                def readback_call(role,keys):
                    raw=json.dumps(keys,separators=(',',':')).encode()
                    payload=dict(schema='xar.java.child-export-callback-input/v1',operation='VALIDATE_READBACKS',retained_role=role,keys_json_base64=base64.b64encode(raw).decode('ascii'))
                    result=dispatch(payload)
                    if result!={'schema':'xar.java.child-export-callback-result/v1','operation':'VALIDATE_READBACKS','retained_role':role,'process_count':len(keys)}:raise AssertionError('actual child callback readback reply differs')
                    callback_rows.append(dict(payload=payload,java_result=result))
                def make_io():
                    io=object.__new__(OriginKernelIOV1)
                    pending={}
                    sent=[]
                    observed=dict(identities)
                    next_handle=[2001]
                    counts=dict(synthetic_duplicate_calls=0,original_send_calls=0,original_recv_calls=0)
                    def ok(value,why):
                        if not value:raise ValueError(why)
                        return value
                    def duplicate(source_process,remote_location,target_process,out,access,inherit,options):
                        if type(remote_location) is not int or remote_location<=0:return False
                        identity=observed.get(remote_location,identities[1003])
                        handle=next_handle[0]
                        next_handle[0]+=1
                        observed[handle]=identity
                        out._obj.value=handle
                        counts['synthetic_duplicate_calls']+=1
                        return True
                    api=SimpleNamespace(current=lambda:-1,duplicate=duplicate,PROCESS_READ_ACCESS=0x100410,_ok=ok)
                    facade=SimpleNamespace(_lock=threading.RLock(),_owned={},observe_process=lambda handle:observed[int(handle)])
                    io.api=api
                    io.facade=facade
                    io.timeout=.5
                    io.startup_timeout=.5
                    io.rx={}
                    io._holders={}
                    def write(handle,raw,length,count,unused):
                        sent.append((handle,bytes(raw[:length])))
                        count._obj.value=length
                        counts['original_send_calls']+=1
                        return True
                    def peek(handle,unused0,unused1,unused2,count,unused3):
                        count._obj.value=len(pending.get(handle,b''))
                        return True
                    def read(handle,buffer,maximum,count,unused):
                        raw=pending.pop(handle,b'')[:maximum]
                        ctypes.memmove(buffer,raw,len(raw))
                        count._obj.value=len(raw)
                        counts['original_recv_calls']+=1
                        return True
                    io._write=write
                    io._peek=peek
                    io._read=read
                    return io,pending,sent,observed,counts
                io,pending,sent,observed,counts=make_io()
                app_holder=SimpleNamespace(_creation_role_v1='MCPApp',_owned=[])
                handles=production_stage('app_export',(('PRODUCE_WIRE','MCPApp'),),
                    lambda:chain.export_actual_child_chain_v1(SimpleNamespace(holder=app_holder),io,801))
                methods.append('canonical_native_provider_chain_v1.export_actual_child_chain_v1:MCPApp')
                if handles!=():raise AssertionError('App must export no descendant handles')
                original=sent[-1][1]
                current=wire_call('MCPApp',original)
                if current!=original:raise AssertionError('Java changed the actual App producer bytes')
                for exporting_role,child_role,child_handle in (('Queue','MCPApp',1003),('owner','Queue',1002)):
                    holder=SimpleNamespace(_creation_role_v1=exporting_role,_owned=[])
                    control=802 if child_role=='MCPApp' else 803
                    pending[control]=current
                    edge=origin._ChildEdgeV1(holder,io,SimpleNamespace(),child_handle,observed[child_handle],control,child_role,contract._RESOURCE_SEAL)
                    handles=production_stage(exporting_role.lower()+'_export',
                        (('CANONICALIZE_WIRE',child_role),('VALIDATE_READBACKS',child_role),('PRODUCE_WIRE',exporting_role)),
                        lambda:chain.export_actual_child_chain_v1(SimpleNamespace(holder=holder),io,804,edge))
                    methods.extend(('native_loaded_provider_origin_v1._pull_actual_chain_v1:'+child_role,'canonical_native_provider_chain_v1.export_actual_child_chain_v1:'+exporting_role))
                    if handles!=edge.chain_handles:raise AssertionError('actual original callback lost the actual child-chain handles')
                    readback_call(child_role,[origin._process_key(observed[handle]) for handle in handles])
                    original=sent[-1][1]
                    current=wire_call(exporting_role,original)
                    if current!=original:raise AssertionError('Java changed actual upward original producer bytes')
                supervisor_holder=SimpleNamespace(_owned=[])
                pending[805]=current
                owner_edge=origin._ChildEdgeV1(supervisor_holder,io,SimpleNamespace(),1001,observed[1001],805,'owner',contract._RESOURCE_SEAL)
                original_owner=object.__new__(origin._CanonicalOriginV1)
                original_owner.holder=supervisor_holder
                original_owner.io=io
                original_owner.lock=threading.RLock()
                original_owner.chain=None
                original_owner.active=True
                original_owner.ready=threading.Event()
                original_owner.final_handle=None
                production_stage('supervisor_bind',(('CANONICALIZE_WIRE','owner'),('VALIDATE_READBACKS','owner')),
                    lambda:original_owner.bind_actual_chain(owner_edge))
                methods.append('native_loaded_provider_origin_v1._CanonicalOriginV1.bind_actual_chain')
                final_keys=[origin._process_key(process) for handle,process in original_owner.chain]
                readback_call('owner',final_keys)
                final_pids=[row[0] for row in final_keys]
                if final_pids!=[71,72,73] or not original_owner.ready.is_set():raise AssertionError('actual final original consumer did not bind the ordered software fixture chain')
                token_cases=[]
                for name,token in [('int_1100','1'+'0'*1099),('negative_1100','-1'+'0'*1099),('int_4300','1'+'0'*4299),('negative_4300','-1'+'0'*4299),('int_4301','1'+'0'*4300),('negative_4301','-1'+'0'*4300),('float','501.0'),('true','true'),('false','false'),('string','"501"')]:
                    raw=('{"kind":"actual_child_exports","exports":[{"role":"MCPApp","location":'+token+'}]}\\n').encode()
                    trial,trial_pending,trial_sent,trial_observed,trial_counts=make_io()
                    holder=SimpleNamespace(_owned=[])
                    trial_pending[901]=raw
                    edge=origin._ChildEdgeV1(holder,trial,SimpleNamespace(),1002,trial_observed[1002],901,'Queue',contract._RESOURCE_SEAL)
                    try:
                        consumer_handles=origin._pull_actual_chain_v1(edge)
                    except ValueError as error:
                        consumer_accepted=False
                        consumer_error_type=type(error).__name__
                    else:
                        consumer_accepted=True
                        consumer_error_type=None
                        if len(consumer_handles)!=2:raise AssertionError('original Queue consumer shape differs')
                    try:
                        java_wire=wire_call('Queue',raw)
                    except ProjectionDomainRejected:
                        java_accepted=False
                    else:
                        java_accepted=True
                        if java_wire!=raw:raise AssertionError('Java callback changed legal large original integer bytes')
                    if consumer_accepted!=java_accepted:raise AssertionError('postpatch SDK consumer/Java callback token acceptance differs: '+name)
                    expected=name in ('int_1100','int_4300')
                    if java_accepted!=expected:raise AssertionError('actual callback numeric/token boundary differs: '+name)
                    token_cases.append(dict(name=name,wire_base64=base64.b64encode(raw).decode('ascii'),accepted=java_accepted,consumer_error_type=consumer_error_type))
                return dict(schema='xar.java.actual-child-exports-callback-chain-golden/v1',scope='postpatch imported original SDK methods consuming real issued Java delegate results with passive original-code observation; synthetic process/HANDLE/pipe fixtures; independent unmodified Python value baseline is the separate pure producer corpus; native_os_calls covers only synthetic domain HANDLE/pipe IO, excluding actual HTTP sockets and kernel PID/birth/source metadata guards; no native SDK/provider/Game qualification',production_projection_post_calls=len(production_rows),production_callback_rows=production_rows,production_stages=production_stages,independent_python_baseline_resource='/childexports/child-exports-golden.json',callback_rows=callback_rows,token_cases=token_cases,final_pids=final_pids,final_process_keys=final_keys,actual_original_methods=methods,software_fixture_io_counts=counts,game_rpc_calls=0,native_os_calls=0,ledger_writes=0,saved_day_credit=0)
            
            """;
}


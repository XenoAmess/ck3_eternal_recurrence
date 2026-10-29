package org.xar.ck3.control.wave3.runtime.childexports;

/** Original staged callback fault injection consumed by the existing shared harness, without a runner. */
public final class ChildExportCallbackFailureFixture {
    private ChildExportCallbackFailureFixture() { }
    public static String pythonSource() { return PROGRAM; }
    private static final String PROGRAM = """
            def run_child_export_failure_differential(unknown_error: 'ProjectionUnavailable',unsupported_error: 'ProjectionRejected') -> dict[str, object]:
                import ctypes
                from types import SimpleNamespace
                from unittest.mock import patch
                from tools.g2_saved_campaign.java_map_admission_client_v1 import (
                    ProjectionUnavailable,ProjectionRejected,ProjectionDomainRejected,require_current_projection_config_v1)
                from tools.g2_saved_campaign import canonical_native_provider_chain_v1 as chain
                from tools.g2_saved_campaign.canonical_c17_outer_binding_v1 import OuterBindingV1
                from xar_autoplayer.bridge import native_loaded_provider_origin_v1 as origin
                from xar_autoplayer.bridge import native_loaded_provider_origin_io_v1 as origin_io
                from xar_autoplayer.bridge import native_loaded_provider_custody_v1 as contract
                if not isinstance(unknown_error,ProjectionUnavailable) or isinstance(unknown_error,ValueError):
                    raise TypeError('actual unknown-branch exception required')
                if not isinstance(unsupported_error,ProjectionRejected) or isinstance(unsupported_error,ValueError):
                    raise TypeError('actual non-domain unsupported exception required')
                for supplied in (unknown_error,unsupported_error):
                    if supplied.http_call is None or supplied.http_call.transport_kind!='injected-test/v1':
                        raise TypeError('existing shared-client injected-response exception object required; no actual HTTP failure qualification')
                config=require_current_projection_config_v1()
                rows=[]
                for name,error in [('unavailable',unknown_error),('unsupported',unsupported_error)]:
                    effects=dict(duplicate=0,send=0,read=0,cleanup=0)
                    def forbidden(*args,**kwargs):
                        raise AssertionError('preflight failure reached a native adapter')
                    io=SimpleNamespace(duplicate=forbidden,send=forbidden,facade=SimpleNamespace(observe_process=forbidden))
                    holder=SimpleNamespace(_creation_role_v1='owner',_owned=[])
                    result=SimpleNamespace(holder=holder)
                    with patch.object(chain,'_qualified_child_exports_config_v1',side_effect=error):
                        try:chain.export_actual_child_chain_v1(result,io,701,object())
                        except ProjectionUnavailable as observed:
                            if observed is not error:raise AssertionError('producer replaced actual unavailable/unsupported exception')
                        else:raise AssertionError('producer swallowed preflight unavailable/unsupported')
                    edge=origin._ChildEdgeV1(holder,io,SimpleNamespace(),1001,SimpleNamespace(),702,'owner',contract._RESOURCE_SEAL)
                    with patch.object(origin,'_qualified_child_exports_config_v1',side_effect=error):
                        try:origin._pull_actual_chain_v1(edge)
                        except ProjectionUnavailable as observed:
                            if observed is not error:raise AssertionError('consumer replaced actual preflight exception')
                        else:raise AssertionError('consumer swallowed preflight unavailable/unsupported')
                    rows.append(dict(name=name,phase='preflight',native_duplicate_calls=0,native_send_calls=0,native_read_calls=0,propagated_original_exception=True))
                    actual=object.__new__(origin_io.OriginKernelIOV1)
                    actual.timeout=1.0
                    actual.startup_timeout=1.0
                    actual.rx={}
                    raw=b'{"kind":"actual_child_exports","exports":[]}\\n'
                    pending=[raw]
                    def ok(value,why):
                        if not value:raise ValueError(why)
                        return value
                    def peek(handle,unused0,unused1,unused2,count,unused3):
                        count._obj.value=len(pending[0])
                        return True
                    def read(handle,buffer,maximum,count,unused):
                        value=pending[0]
                        pending[0]=b''
                        ctypes.memmove(buffer,value,len(value))
                        count._obj.value=len(value)
                        effects['read']+=1
                        return True
                    actual.api=SimpleNamespace(_ok=ok)
                    actual._peek=peek
                    actual._read=read
                    binding=object.__new__(OuterBindingV1)
                    binding.factory=None
                    binding.owner=None
                    def cleanup():
                        effects['cleanup']+=1
                    binding.result=SimpleNamespace(holder=SimpleNamespace(close=cleanup))
                    with patch.object(origin_io,'_child_export_wire_v1',side_effect=error) as projected:
                        try:
                            actual.recv(703,startup=True,child_exports_role='MCPApp',projection_config=config)
                        except ProjectionUnavailable as observed:
                            if observed is not error:raise AssertionError('actual receive replaced unavailable/unsupported')
                        else:raise AssertionError('actual receive swallowed unavailable/unsupported after consumption')
                        finally:
                            binding.close()
                        if projected.call_count!=1:raise AssertionError('private Java projection retried')
                    if effects!=dict(duplicate=0,send=0,read=1,cleanup=1):raise AssertionError('private consumed-unknown path retried or cleanup count differs')
                    rows.append(dict(name=name,phase='after_private_receive',native_duplicate_calls=0,native_send_calls=0,synthetic_private_reads=1,original_outer_cleanup_calls=1,projection_calls=1,propagated_original_exception=True))
                return dict(schema='xar.java.child-export-callback-failure-golden/v1',scope='actual staged SDK entry/recv/outer cleanup methods with existing shared-client injected-response exception objects and explicit software pipe; native_os_calls covers domain HANDLE/pipe fixture IO only; no actual host non-domain HTTP failure or native SDK/provider/Game qualification',synthetic_error_injection=True,actual_projection_http_failure_proved=False,error_transport_kind='injected-test/v1',cases=rows,native_os_calls=0,game_rpc_calls=0,ledger_writes=0)
            
            """;
}


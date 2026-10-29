package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** The actual software RPC session is exercised. This explicit SOFTWARE_ONLY directory models
 * metadata failure, never a qualified Inputs/Complete, private Root, Native read or Game action. */
final class PublicMcpMetadataGuardTest {
    private enum Metadata {
        TOOLS("tools/list","tools"),RESOURCES("resources/list","resources");
        final String method,field;
        Metadata(String method,String field){this.method=method;this.field=field;}
    }
    private enum Fault { IO,CHANGED }
    private static final class Directory implements PublicMcpDirectory {
        private final PublicMcpDirectory actual;
        private final Metadata selected;
        private final Fault fault;
        private int failAt=Integer.MAX_VALUE;
        private final AtomicInteger toolLists=new AtomicInteger(),resourceLists=new AtomicInteger();
        private final AtomicInteger applicationCalls=new AtomicInteger(),resourceCalls=new AtomicInteger();
        private Directory(PublicMcpDirectory actual,Metadata selected,Fault fault){this.actual=actual;this.selected=selected;this.fault=fault;}
        @Override public Scope scope(){return actual.scope();}
        private <T> List<T> checked(Metadata kind,AtomicInteger counter,List<T> values) {
            int count=counter.incrementAndGet();
            if(kind==selected&&count==failAt) {
                if(fault==Fault.IO)throw new UncheckedIOException("synthetic metadata source expired",new IOException("DATA failure only"));
                return List.of();
            }
            return values;
        }
        @Override public List<ToolDescriptor> tools(){return checked(Metadata.TOOLS,toolLists,actual.tools());}
        @Override public List<ResourceDescriptor> resources(){return checked(Metadata.RESOURCES,resourceLists,actual.resources());}
        @Override public CallResult invoke(ToolCall call)throws ToolFailure,RpcFailure {applicationCalls.incrementAndGet();return actual.invoke(call);}
        @Override public ResourceResult read(ResourceCall call)throws ToolFailure,RpcFailure {resourceCalls.incrementAndGet();return actual.read(call);}
        private int count(){return (selected==Metadata.TOOLS?toolLists:resourceLists).get();}
    }
    @Test void sourceFailureBeforeOrAfterMetadataConstructionNeverPublishesCachedMetadataOrTerminatesRpc()throws Exception {
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN))for(var metadata:Metadata.values())for(int phase:List.of(1,2)) {
            var actual=PublicMcpProtocolTest.directory();assertEquals(Scope.SOFTWARE_ONLY,actual.scope());
            var directory=new Directory(actual,metadata,Fault.IO);
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                if(!version.equals(PublicMcpSession.MODERN))peer.initialize(version);directory.failAt=directory.count()+phase;
                peer.send(PublicMcpProtocolTest.request(version,"1",metadata.method,""));var response=peer.receive();
                assertEquals(-32603,response.get("error").get("code").intValue());assertFalse(response.has("result"));
                assertTrue(response.get("error").get("message").textValue().contains("metadata inputs unavailable"));
                assertEquals(directory.failAt,directory.count());
                peer.send(PublicMcpProtocolTest.request(version,"2","ping",""));assertTrue(peer.receive().has("result"));
                assertEquals(0,directory.applicationCalls.get());assertEquals(0,directory.resourceCalls.get());
            }
        }
    }
    @Test void changedMetadataIsRejectedRatherThanReplacingTheAdmittedListWithAnEmptyFallback()throws Exception {
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN))for(var metadata:Metadata.values()) {
            var actual=PublicMcpProtocolTest.directory();assertFalse(actual.tools().isEmpty());assertFalse(actual.resources().isEmpty());
            var directory=new Directory(actual,metadata,Fault.CHANGED);
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                if(!version.equals(PublicMcpSession.MODERN))peer.initialize(version);directory.failAt=directory.count()+1;
                peer.send(PublicMcpProtocolTest.request(version,"1",metadata.method,""));var response=peer.receive();
                assertEquals(-32603,response.get("error").get("code").intValue());assertFalse(response.has("result"));
                assertTrue(response.get("error").get("message").textValue().contains("metadata changed"));
                assertEquals(0,directory.applicationCalls.get());assertEquals(0,directory.resourceCalls.get());
            }
        }
    }
    @Test void originalPaginationErrorsPrecedeMetadataAccessAndValidListsReenterBothGuards()throws Exception {
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN))for(var metadata:Metadata.values()) {
            var actual=PublicMcpProtocolTest.directory();var directory=new Directory(actual,metadata,Fault.IO);
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                if(!version.equals(PublicMcpSession.MODERN))peer.initialize(version);int before=directory.count();directory.failAt=before+1;
                peer.send(PublicMcpProtocolTest.request(version,"1",metadata.method,"\"cursor\":true"));var invalid=peer.receive();
                assertEquals(-32602,invalid.get("error").get("code").intValue());assertEquals(before,directory.count());
                directory.failAt=Integer.MAX_VALUE;
                peer.send(PublicMcpProtocolTest.request(version,"2",metadata.method,""));var response=peer.receive();
                int expected=metadata==Metadata.TOOLS?actual.tools().size():actual.resources().size();
                assertEquals(expected,response.get("result").get(metadata.field).size());assertEquals(before+2,directory.count());
                assertEquals(0,directory.applicationCalls.get());assertEquals(0,directory.resourceCalls.get());
            }
        }
    }
}

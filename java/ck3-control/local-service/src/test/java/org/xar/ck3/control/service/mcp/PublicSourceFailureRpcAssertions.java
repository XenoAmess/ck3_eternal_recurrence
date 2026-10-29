package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;

/** One software boundary invocation over an already produced actual source failure.
 * No current, archive, lease, receipt, native action or successful business result is manufactured. */
public final class PublicSourceFailureRpcAssertions {
    private PublicSourceFailureRpcAssertions() { }
    private record Input() { }

    public static Optional<PublicServiceFailure> assertOriginal(PublicPlanningRpcAssertions.Consumer consumer,
            String name,String originalArguments,RuntimeException original,
            Optional<PublicServiceFailure.Kind> expectedKind) throws Exception {
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
        var invoked=new AtomicInteger();var encoded=new AtomicInteger();
        var bindings=PublicMcpBindingTest.oneAdmitted(name);
        bindings.registerDirect(RootPublicCatalogCodec.executableTool(descriptor),PublicMcpBindings.Kind.APPLICATION_COMPOSITE,
                Input.class,RawJson.class,request->{invoked.incrementAndGet();throw original;},call->new Input(),
                result->{encoded.incrementAndGet();return CallResult.fromBusinessJson(result);},PublicMcpProtocolTest.target());
        var directory=bindings.freezeSoftwareScope();
        Optional<PublicServiceFailure> retained=Optional.empty();
        if(consumer==PublicPlanningRpcAssertions.Consumer.DIRECTORY) {
            var failure=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(name,originalArguments)));
            assertEquals(original.getMessage(),failure.getMessage());
            if(expectedKind.isPresent()) {
                var service=assertInstanceOf(PublicServiceFailure.class,failure.getCause());
                assertEquals(expectedKind.orElseThrow(),service.kind());
                assertSame(original,service.getCause());assertSame(original,service.originalFailure().orElseThrow());
                retained=Optional.of(service);
            } else assertSame(original,failure.getCause(),"unclassified source must not acquire an inferred public exception class");
        } else {
            String version=switch(consumer) {
                case LEGACY_RPC->"2025-11-25";
                case MODERN_RPC->PublicMcpSession.MODERN;
                case DIRECTORY->throw new AssertionError("Directory is handled above");
            };
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",
                        "\"name\":\""+name+"\",\"arguments\":"+originalArguments));
                var response=peer.receive();assertFalse(response.has("error"));var result=response.get("result");
                assertTrue(result.get("isError").booleanValue());assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool "+name+": "+original.getMessage(),
                        result.get("content").get(0).get("text").textValue());
            }
        }
        assertEquals(1,invoked.get());assertEquals(0,encoded.get());
        return retained;
    }
}

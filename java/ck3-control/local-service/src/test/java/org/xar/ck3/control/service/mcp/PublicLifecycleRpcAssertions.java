package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Test-only lifecycle producer -> identical installed direct binder -> Directory and both RPC versions. */
public final class PublicLifecycleRpcAssertions {
    private PublicLifecycleRpcAssertions() { }

    private static <Q,R> PublicMcpDirectory directory(McpExecutableDirectory.DirectBinding<Q,R> actual) throws Exception {
        var original=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(actual.name())).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+actual.name()));
        var bindings=PublicMcpBindingTest.oneAdmitted(actual.name());
        bindings.registerDirect(RootPublicCatalogCodec.executableTool(original),actual.kind(),actual.requestType(),actual.resultType(),
                actual.actual(),actual.decoder(),actual.encoder(),actual.target());
        return bindings.freezeSoftwareScope();
    }

    public static <Q,R> void assertDirectResult(McpExecutableDirectory.DirectBinding<Q,R> actual,
            String arguments,RawJson expectedBusiness) throws Exception {
        var directory=directory(actual);
        assertEnvelope(expectedBusiness,directory.invoke(PublicMcpBindingTest.call(actual.name(),arguments)));
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN)) {
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",fields(actual.name(),arguments)));
                var response=peer.receive();assertFalse(response.has("error"));
                assertEnvelope(expectedBusiness,new CallResult(McpJson.encode(response.get("result"))));
            }
        }
    }

    public static <Q,R> void assertDirectFailure(McpExecutableDirectory.DirectBinding<Q,R> actual,
            String arguments,PublicServiceFailure expectedFault) throws Exception {
        var directory=directory(actual);
        var failure=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(actual.name(),arguments)));
        assertEquals(expectedFault.getMessage(),failure.getMessage());assertSame(expectedFault,failure.getCause());
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN)) {
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",fields(actual.name(),arguments)));
                var response=peer.receive();assertFalse(response.has("error"));var result=response.get("result");
                assertTrue(result.path("isError").booleanValue());assertFalse(result.has("structuredContent"));
                assertEquals("Error executing tool "+actual.name()+": "+expectedFault.getMessage(),
                        result.get("content").get(0).get("text").textValue());
            }
        }
    }

    private static String fields(String name,String arguments) {
        return "\"name\":\""+name+"\",\"arguments\":"+arguments;
    }
    private static void assertEnvelope(RawJson expectedBusiness,CallResult actual) {
        var expected=PublicDataJson.object(expectedBusiness);var envelope=McpJson.parseResult(actual.bytes());
        assertFalse(envelope.path("isError").booleanValue());assertEquals(expected,envelope.get("structuredContent"));
        assertEquals(1,envelope.get("content").size());var text=envelope.get("content").get(0);
        assertEquals("text",text.get("type").textValue());
        assertEquals(expected,McpJson.parseResult(text.get("text").textValue().getBytes(StandardCharsets.UTF_8)));
    }
}

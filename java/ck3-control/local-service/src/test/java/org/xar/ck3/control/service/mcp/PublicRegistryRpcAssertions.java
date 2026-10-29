package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Test-only cross-package bridge from the real Registry handler fixture to the real MCP adapter.
 * Callers supply their existing actual typed handler result; no Root or producer is substituted here. */
public final class PublicRegistryRpcAssertions {
    private PublicRegistryRpcAssertions() { }

    public static void assertRegistryRpc(PublicBindings actual, String name, String arguments,
            RawJson expectedBusiness) throws Exception {
        if (!(actual.lookup(PublicMcpNativeAdapter.expectedServiceMethod(name)).orElseThrow()
                instanceof PublicBindings.TypedBinding<?,?> binding))
            throw new IllegalStateException("actual Registry handler is not its registered typed binding");
        verify(binding, name, arguments, expectedBusiness);
    }

    private static <Q,R> void verify(PublicBindings.TypedBinding<Q,R> binding, String name,
            String arguments, RawJson expectedBusiness) throws Exception {
        var descriptor=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
        var directoryBindings=PublicMcpBindingTest.oneAdmitted(name);
        PublicMcpNativeAdapter.register(directoryBindings,RootPublicCatalogCodec.executableTool(descriptor),binding);
        var directory=directoryBindings.freezeSoftwareScope();
        assertEnvelope(expectedBusiness,directory.invoke(PublicMcpBindingTest.call(name,arguments)));
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN)) {
            try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                if (!version.equals(PublicMcpSession.MODERN)) peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",
                        "\"name\":\""+name+"\",\"arguments\":"+arguments));
                var response=peer.receive();assertFalse(response.has("error"));
                assertEnvelope(expectedBusiness,new CallResult(McpJson.encode(response.get("result"))));
            }
        }
    }

    private static void assertEnvelope(RawJson expectedBusiness, CallResult actual) {
        var expected=PublicDataJson.object(expectedBusiness);
        var envelope=McpJson.parseResult(actual.bytes());
        assertFalse(envelope.path("isError").booleanValue());
        assertEquals(expected,envelope.get("structuredContent"));
        assertEquals(1,envelope.get("content").size());
        assertEquals("text",envelope.get("content").get(0).get("type").textValue());
        byte[] text=envelope.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8);
        assertEquals(expected,McpJson.parseResult(text));
    }
}

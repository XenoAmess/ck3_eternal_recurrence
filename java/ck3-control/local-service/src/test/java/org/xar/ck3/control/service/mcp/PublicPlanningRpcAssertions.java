package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

import java.nio.charset.StandardCharsets;
import java.util.Objects;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;

/** One actual registered PLAN/EXECUTE invocation per consumer assertion.
 * Mutation/UNKNOWN scenarios must supply independent actual fixtures for different consumers.
 * The helper never calls a producer for an expected value, retries it, or supplies a Ready/result. */
public final class PublicPlanningRpcAssertions {
    public enum Consumer { DIRECTORY, LEGACY_RPC, MODERN_RPC }
    public record ExpectedFailure(PublicServiceFailure.Kind kind,String originalMessage,Optional<ExactRef> originalCandidate) {
        public ExpectedFailure {
            Objects.requireNonNull(kind);Objects.requireNonNull(originalMessage);Objects.requireNonNull(originalCandidate);
            if(originalMessage.isEmpty())throw new IllegalArgumentException("original public failure message required");
        }
    }
    private PublicPlanningRpcAssertions() { }

    public static CallResult assertRegisteredResult(Consumer consumer,PublicBindings actualRegistry,String name,
            String originalArguments,RawJson expectedBusiness) throws Exception {
        Objects.requireNonNull(expectedBusiness);
        var directory=directory(actualRegistry,name);
        CallResult actual=call(consumer,directory,name,originalArguments);
        var envelope=McpJson.parseResult(actual.bytes());
        assertFalse(envelope.path("isError").booleanValue());assertTrue(envelope.has("structuredContent"));
        assertEquals(1,envelope.get("content").size());var text=envelope.get("content").get(0);
        assertEquals("text",text.get("type").textValue());
        var expected=DriverJson.object(expectedBusiness.bytes(),RawJson.MAXIMUM_BYTES);
        var structured=DriverJson.object(McpJson.tokenResult(actual.bytes(),"structuredContent"),RawJson.MAXIMUM_BYTES);
        var textual=DriverJson.object(text.get("text").textValue().getBytes(StandardCharsets.UTF_8),RawJson.MAXIMUM_BYTES);
        assertEquals(expected,structured);assertEquals(expected,textual);
        assertArrayEquals(DriverJson.encode(expected),DriverJson.encode(structured));
        assertArrayEquals(DriverJson.encode(expected),DriverJson.encode(textual));
        assertArrayEquals(actual.bytes(),new CallResult(actual.bytes()).bytes());
        return actual;
    }

    public static void assertRegisteredFailure(Consumer consumer,PublicBindings actualRegistry,String name,
            String originalArguments,ExpectedFailure expected) throws Exception {
        Objects.requireNonNull(expected);var directory=directory(actualRegistry,name);
        if(consumer==Consumer.DIRECTORY) {
            var failure=assertThrows(ToolFailure.class,
                    ()->directory.invoke(PublicMcpBindingTest.call(name,originalArguments)));
            var source=assertInstanceOf(PublicServiceFailure.class,failure.getCause());
            assertEquals(expected.kind(),source.kind());assertEquals(expected.originalMessage(),source.getMessage());
            assertEquals(expected.originalCandidate(),source.originalCandidate());
            assertEquals(source.getMessage(),failure.getMessage());
            return;
        }
        var actual=call(consumer,directory,name,originalArguments);var envelope=McpJson.parseResult(actual.bytes());
        assertTrue(envelope.path("isError").booleanValue());assertFalse(envelope.has("structuredContent"));
        assertEquals(1,envelope.get("content").size());
        assertEquals("Error executing tool "+name+": "+expected.originalMessage(),
                envelope.get("content").get(0).get("text").textValue());
        assertArrayEquals(actual.bytes(),new CallResult(actual.bytes()).bytes());
    }

    private static CallResult call(Consumer consumer,PublicMcpDirectory directory,String name,
            String originalArguments) throws Exception {
        Objects.requireNonNull(consumer);Objects.requireNonNull(originalArguments);
        if(consumer==Consumer.DIRECTORY)return directory.invoke(PublicMcpBindingTest.call(name,originalArguments));
        String version=switch(consumer) {
            case LEGACY_RPC -> "2025-11-25";
            case MODERN_RPC -> PublicMcpSession.MODERN;
            case DIRECTORY -> throw new AssertionError("Directory has already been consumed");
        };
        try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
            peer.initialize(version);
            peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",
                    "\"name\":\""+name+"\",\"arguments\":"+originalArguments));
            // Consume the actual bytes before any JsonNode re-encoding can normalize decimal tokens.
            byte[] response=peer.lines.poll(3,TimeUnit.SECONDS);assertNotNull(response,"actual planning RPC response required");
            assertEquals('\n',response[response.length-1]);
            assertFalse(McpJson.parseResult(response).has("error"));
            return new CallResult(McpJson.tokenResult(response,"result"));
        }
    }

    private static PublicMcpDirectory directory(PublicBindings registry,String name) throws Exception {
        Objects.requireNonNull(registry);
        PublicMethod method=switch(name) {
            case "ck3_plan_turn" -> PublicMethod.PLAN_TURN;
            case "ck3_execute_step" -> PublicMethod.EXECUTE_STEP;
            default -> throw new IllegalArgumentException("original public PLAN or EXECUTE tool required");
        };
        if(!(registry.lookup(method).orElseThrow() instanceof PublicBindings.TypedBinding<?,?> actual))
            throw new IllegalStateException("original planning producer is not its actual registered typed binding");
        return directory(actual,name);
    }

    private static <Q,R> PublicMcpDirectory directory(PublicBindings.TypedBinding<Q,R> actual,String name) throws Exception {
        var original=RootOriginalPublicTestInputs.tools().stream().filter(tool->tool.name().equals(name)).findFirst()
                .orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_TOOL: "+name));
        var bindings=PublicMcpBindingTest.oneAdmitted(name);
        PublicMcpNativeAdapter.register(bindings,RootPublicCatalogCodec.executableTool(original),actual);
        return bindings.freezeSoftwareScope();
    }
}

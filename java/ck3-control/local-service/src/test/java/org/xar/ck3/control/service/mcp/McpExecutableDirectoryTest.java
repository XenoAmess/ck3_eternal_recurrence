package org.xar.ck3.control.service.mcp;

import com.fasterxml.jackson.databind.JsonNode;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicRoutes;
import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

final class McpExecutableDirectoryTest {
    record Empty() { }
    static List<ToolDescriptor> descriptors() throws Exception {
        try(InputStream in=McpExecutableDirectoryTest.class.getResourceAsStream("/mcp/original-executable-descriptors.json")) {
            assertNotNull(in);List<ToolDescriptor> result=new ArrayList<>();
            for(JsonNode row:McpJson.parse(in.readAllBytes()).get("descriptors"))result.add(new ToolDescriptor(row.get("name").textValue(),new RawJson(McpJson.encode(row))));return List.copyOf(result);
        }
    }
    static List<ResourceDescriptor> resources() throws Exception {
        List<ResourceDescriptor> result=new ArrayList<>();for(JsonNode row:PublicMcpProtocolTest.oracle().get("resources"))result.add(new ResourceDescriptor(row.get("uri").textValue(),new RawJson(McpJson.encode(row))));return List.copyOf(result);
    }
    static List<McpCoverage.Decision> decisions() throws Exception {
        return PublicMcpProtocolTest.catalog().declarations().stream().map(row -> new McpCoverage.Decision(row.name(),
                Set.of("ck3_get_capabilities","ck3_take_snapshot").contains(row.name())?McpCoverage.Admission.ADMITTED:McpCoverage.Admission.UNMIGRATED,row.source(),"software producer consumer regression scope")).toList();
    }
    static void method(PublicBindings registry,PublicMethod method,AtomicInteger invocations) {
        registry.register(method,Empty.class,RawJson.class,request->{invocations.incrementAndGet();return new RawJson(McpJson.utf8("{\"actual_identity\":\"18446744073709551615\"}"));},
                arguments -> new Empty(),value -> value,PublicMcpProtocolTest.target(),PublicRoutes.Status.IMPLEMENTED,"software typed producer only");
    }
    @Test void bothResourcesUseTheSameFrozenActualToolProvidersWithoutExtraDispatch() throws Exception {
        PublicBindings actual=new PublicBindings();AtomicInteger capabilities=new AtomicInteger(),snapshot=new AtomicInteger();
        method(actual,PublicMethod.CAPABILITIES,capabilities);method(actual,PublicMethod.SNAPSHOT,snapshot);actual.freeze(Set.of(PublicMethod.CAPABILITIES,PublicMethod.SNAPSHOT));
        var result=assertInstanceOf(McpExecutableDirectory.Partial.class,McpExecutableDirectory.assemble(PublicMcpProtocolTest.catalog(),decisions(),descriptors(),resources(),actual,List.of()));
        assertEquals(2,result.coverage().boundTools());assertEquals(2,result.coverage().boundResources());assertFalse(result.coverage().completeMigration());assertEquals(318,result.missing().size());
        var directory=result.softwareDirectory();
        directory.invoke(PublicMcpBindingTest.call("ck3_get_capabilities","{}"));assertEquals(1,capabilities.get());
        var resource=directory.read(new ResourceCall("ck3://capabilities",Optional.empty(),new McpCancellation()));assertEquals(2,capabilities.get());
        assertTrue(new String(resource.bytes(),java.nio.charset.StandardCharsets.UTF_8).contains("18446744073709551615"));
        directory.read(new ResourceCall("ck3://state/current",Optional.empty(),new McpCancellation()));assertEquals(1,snapshot.get());
    }
    @Test void missingActualMethodsProduceExactGapsAndNoPlaceholderHandlers() throws Exception {
        PublicBindings none=new PublicBindings();none.freeze(Set.of());
        var partial=assertInstanceOf(McpExecutableDirectory.Partial.class,McpExecutableDirectory.assemble(PublicMcpProtocolTest.catalog(),decisions(),descriptors(),resources(),none,List.of()));
        assertEquals(0,partial.coverage().boundTools());assertEquals(0,partial.coverage().boundResources());assertEquals(322,partial.missing().size());
        assertTrue(partial.missing().contains(new McpExecutableDirectory.Missing("ck3_get_capabilities",McpExecutableDirectory.MissingReason.NO_ACTUAL_METHOD)));
        assertTrue(partial.missing().contains(new McpExecutableDirectory.Missing("ck3://state/current",McpExecutableDirectory.MissingReason.NO_ACTUAL_RESOURCE_PROVIDER)));
    }
    @Test void actualActivityArgumentsRejectWrongTypesAndPreserveNullOptionalSemantics() {
        var request=RootMcpActivityReads.decode(Query.GUEST_OPINION,OriginalMcpPresenterTestArguments.value("{\"expected_revision\":9,\"guest_character_id\":2,\"activity_id\":null}"));
        assertFalse(request.arguments().members().containsKey("activity_id"));assertEquals(java.math.BigInteger.valueOf(9),request.expectedRevision());
        for(String json:List.of("{\"expected_revision\":true,\"guest_character_id\":2}","{\"expected_revision\":9.0,\"guest_character_id\":2}","{\"expected_revision\":9,\"guest_character_id\":true}","{\"expected_revision\":9,\"guest_character_id\":2,\"alias\":1}"))
            assertThrows(IllegalArgumentException.class,()->RootMcpActivityReads.decode(Query.GUEST_OPINION,OriginalMcpPresenterTestArguments.value(json)));
        assertThrows(IllegalArgumentException.class,()->RootMcpActivityReads.publicName(Query.DIAGNOSTIC));
        assertEquals("ck3_query_activity_feast_guest_rule_provenance_private_v1",RootMcpActivityReads.publicName(Query.GUEST_RULE_PROVENANCE));
    }
    @Test void actualMatchedRejectionIsDiagnosticOnlyAndMismatchedPacketCannotMintIt() {
        var failure=McpAutoFailure.fromAck(rejection("r1"));JsonNode result=McpJson.parse(failure.result().bytes());
        assertTrue(result.get("isError").booleanValue());JsonNode diagnostics=result.get("structuredContent").get("diagnostics");
        assertEquals("18446744073709551615",diagnostics.get("native_command_rejection").get("expected_native_revision").textValue());
        assertFalse(diagnostics.get("campaign_root_readonly_retry_v1").get("retry_authorized").booleanValue());
        assertEquals("evidence_absent",diagnostics.get("campaign_root_readonly_retry_v1").get("status").textValue());
        var original=rejection("r1");
        var wrong=new NativeActionPort.AckReceived("r2",false,Optional.empty(),original.originalFrame(),original.originalPacket(),Optional.of(new NativeActionPort.OutboundPacket("r2",original.outbound().orElseThrow().originalPacket())));
        assertThrows(IllegalArgumentException.class,()->McpAutoFailure.fromAck(wrong));
    }
    @Test void typedAutoFailurePassesTheRealBindingEncoderWithoutLosingStructuredEvidence() throws Exception {
        PublicMcpBindings destination=PublicMcpBindingTest.oneAdmitted("ck3_auto_turn");AtomicInteger invocations=new AtomicInteger();
        ToolDescriptor descriptor=OriginalMcpPresenterTestDescriptor.auto();
        destination.registerDirect(descriptor,PublicMcpBindings.Kind.APPLICATION_COMPOSITE,Empty.class,RawJson.class,request->{invocations.incrementAndGet();throw McpAutoFailure.fromAck(rejection("r1"));},
                call -> new Empty(),CallResult::fromBusinessJson,PublicMcpProtocolTest.target());
        var actual=McpJson.parse(destination.freezeSoftwareScope().invoke(PublicMcpBindingTest.call("ck3_auto_turn","{}")).bytes());
        assertTrue(actual.get("isError").booleanValue());assertTrue(actual.get("structuredContent").get("diagnostics").has("native_command_rejection"));assertEquals(1,invocations.get());
    }
    static NativeActionPort.AckReceived rejection(String requestId) {
        String request="{\"type\":\"execute_step\",\"protocol_version\":1,\"request_id\":\""+requestId+"\",\"step\":\"query-campaign-root-context-v1\",\"expected_revision\":18446744073709551615}";
        RawJson response=new RawJson(McpJson.utf8("{\"type\":\"command_result\",\"protocol_version\":1,\"request_id\":\""+requestId+"\",\"ok\":false,\"error\":\"campaign-root snapshot changed or is not ready\"}"));
        return new NativeActionPort.AckReceived(requestId,false,Optional.empty(),response,packet(response.bytes()),Optional.of(new NativeActionPort.OutboundPacket(requestId,packet(McpJson.utf8(request)))));
    }
    static byte[] packet(byte[] body) {return ByteBuffer.allocate(body.length+4).order(ByteOrder.LITTLE_ENDIAN).putInt(body.length).put(body).array();}
    static final class OriginalMcpPresenterTestArguments {static Arguments value(String json){return new Arguments(Presence.VALUE,Optional.of(new RawJson(McpJson.utf8(json))));}}
    static final class OriginalMcpPresenterTestDescriptor {static ToolDescriptor auto()throws Exception {try(InputStream in=McpExecutableDirectoryTest.class.getResourceAsStream("/mcp/original-presenter-oracle.json")){assertNotNull(in);for(JsonNode row:McpJson.parse(in.readAllBytes()).get("descriptors"))if(row.path("name").asText().equals("ck3_auto_turn"))return new ToolDescriptor("ck3_auto_turn",new RawJson(McpJson.encode(row)));throw new IllegalArgumentException("actual auto descriptor absent");}}}
}

package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityReadCodec;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

/** Original mandatory SDK metadata and sole production codecs. Software JSON checks issue no Root,
 * current observation, native permission or actual business qualification. */
public final class PublicActivityDescriptorConsumerTest {
    @TempDir Path temporary;
    private static final String MAX="18446744073709551615";
    private static final List<Query> QUERIES=List.of(Query.START_INPUTS,Query.HOSTED,Query.FULL_COST,
            Query.GUEST_CANDIDATE,Query.GUEST_OPINION,Query.GUEST_TARGET,Query.GUEST_ROUTE_PROOF,Query.GUEST_RULE_PROVENANCE);
    @Test void originalSdkSchemasReachAllEightActualRootRequestCodecsAndKeepEveryOtherField()throws Exception {
        for(Query query:QUERIES) {
            var original=original(query);byte[] retained=original.original().bytes();
            var projected=RootPublicCatalogCodec.executableTool(original);
            var before=node(original.original()).get("inputSchema");var after=node(projected.original()).get("inputSchema");
            assertEquals(before.get("required"),after.get("required"));
            var prior=(ObjectNode)before.get("properties").deepCopy();var revised=(ObjectNode)after.get("properties").deepCopy();
            prior.remove("expected_revision");revised.remove("expected_revision");assertEquals(prior,revised);
            for(String revision:query==Query.GUEST_RULE_PROVENANCE?List.of("1","4294967295",quoted("4294967295")):List.of("1","9007199254740991",quoted(MAX))) {
                var args=input(query);args.set("expected_revision",token(revision));
                if(args.get("expected_revision").isIntegralNumber())original.validateArguments(arguments(args));
                else assertThrows(IllegalArgumentException.class,()->original.validateArguments(arguments(args)));
                projected.validateArguments(arguments(args));var typed=RootMcpActivityReads.decode(query,arguments(args));
                assertEquals(new BigInteger(args.get("expected_revision").asText()),typed.expectedRevision());
                RawJson encoded=RootMcpActivityReads.encodeRequest(typed);projected.validateArguments(arguments(node(encoded)));
                assertEquals(typed,RootMcpActivityReads.decode(query,arguments(node(encoded))));
                assertEquals(typed.expectedRevision().toString(),node(encoded).get("expected_revision").textValue());
                for(String field:List.of("guest_character_id","target_character_id","candidate_character_id","activity_id"))
                    if(args.has(field)&&!args.get(field).isNull())assertTrue(node(encoded).get(field).isIntegralNumber());
            }
            if(query==Query.GUEST_RULE_PROVENANCE) {
                var boundary=input(query).put("expected_revision","4294967295").put("candidate_character_id",4294967295L);
                projected.validateArguments(arguments(boundary));var decoded=RootMcpActivityReads.decode(query,arguments(boundary));
                assertEquals(4294967295L,node(RootMcpActivityReads.encodeRequest(decoded)).get("candidate_character_id").longValue());
            }
            assertArrayEquals(retained,original.original().bytes());
        }
    }
    @Test void widthAndPresenceErrorsNeverReachAnActivityInvocationAndOptionalActivityNullKeepsItsOriginalMeaning()throws Exception {
        for(Query query:QUERIES) {
            var projected=RootPublicCatalogCodec.executableTool(original(query));
            var invoked=new AtomicInteger();
            // Synthetic method metadata only; this software directory issues no Root/source/native permission.
            var directory=software(query,request->{invoked.incrementAndGet();throw new AssertionError("invalid request entered Activity");},
                    new ExactRef("D:/software-only/activity-request.java",1,"a".repeat(64)));
            var badRevisions=new java.util.ArrayList<>(List.of("0","true","null","1.0","9007199254740992",quoted("0"),quoted("01"),quoted("+1"),quoted("-1"),quoted("18446744073709551616"),quoted("")));
            if(query==Query.GUEST_RULE_PROVENANCE)badRevisions.addAll(List.of("4294967296",quoted("4294967296"),quoted(MAX),"9007199254740991"));
            for(String wrong:badRevisions) {
                var args=input(query);args.set("expected_revision",token(wrong));
                assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(args)));
                assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(RootMcpActivityReads.publicName(query),new String(raw(args).bytes(),java.nio.charset.StandardCharsets.UTF_8))));
                if(wrong.equals("9007199254740992"))assertThrows(IllegalArgumentException.class,()->RootMcpActivityReads.decode(query,arguments(args)));
                else assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,assertThrows(PublicServiceFailure.class,
                        ()->RootMcpActivityReads.decode(query,arguments(args))).kind());
            }
            var absent=input(query);absent.remove("expected_revision");
            assertThrows(IllegalArgumentException.class,()->projected.validateArguments(arguments(absent)));
            assertThrows(IllegalArgumentException.class,()->RootMcpActivityReads.decode(query,arguments(absent)));
            assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(RootMcpActivityReads.publicName(query),new String(raw(absent).bytes(),java.nio.charset.StandardCharsets.UTF_8))));
            for(Presence presence:List.of(Presence.MISSING,Presence.NULL))assertThrows(ToolFailure.class,()->directory.invoke(new ToolCall(
                    RootMcpActivityReads.publicName(query),new Arguments(presence,Optional.empty()),Optional.empty(),new McpCancellation())));
            for(String field:List.of("guest_character_id","target_character_id","candidate_character_id"))if(input(query).has(field)) {
                for(String wrong:List.of("null","true","1.0",quoted("1"))) {
                    var args=input(query);args.set(field,token(wrong));
                    assertEquals(PublicServiceFailure.Kind.VALUE_ERROR,assertThrows(PublicServiceFailure.class,
                            ()->RootMcpActivityReads.decode(query,arguments(args))).kind());
                }
            }
            var extra=input(query).put("unexpected_argument",1);
            assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(RootMcpActivityReads.publicName(query),new String(raw(extra).bytes(),java.nio.charset.StandardCharsets.UTF_8))));
            assertEquals(0,invoked.get());
        }
        var absent=input(Query.GUEST_OPINION);absent.remove("activity_id");var explicitNull=absent.deepCopy().putNull("activity_id");
        var descriptor=RootPublicCatalogCodec.executableTool(original(Query.GUEST_OPINION));
        descriptor.validateArguments(arguments(absent));descriptor.validateArguments(arguments(explicitNull));
        assertEquals(RootMcpActivityReads.decode(Query.GUEST_OPINION,arguments(absent)),RootMcpActivityReads.decode(Query.GUEST_OPINION,arguments(explicitNull)));
    }
    private static ObjectNode input(Query query) {
        var row=StrictJson.object().put("expected_revision",1);
        switch(query) {
            case GUEST_OPINION->row.put("guest_character_id",11).put("activity_id",12);
            case GUEST_TARGET->row.put("target_character_id",11);
            case GUEST_RULE_PROVENANCE->row.put("authored_rule_key","activity_invite_rule_regular").put("candidate_character_id",11);
            default->{ }
        }return row;
    }
    private static String quoted(String text){return Character.toString((char)34)+text+(char)34;}
    private static ToolDescriptor original(Query query)throws Exception {return RootOriginalPublicTestInputs.tools().stream().filter(x->x.name().equals(RootMcpActivityReads.publicName(query))).findFirst().orElseThrow(()->new IllegalStateException("NOT_RUN_REQUIRED_ACTUAL_ORIGINAL_ACTIVITY_TOOL: "+RootMcpActivityReads.publicName(query)));}
    private static ObjectNode node(RawJson value){return PublicDataJson.object(value);}
    private static RawJson raw(JsonNode value){return PublicDataJson.encode(value);}
    private static JsonNode token(String value){return StrictJson.parse(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
    private static Arguments arguments(JsonNode value){return new Arguments(Presence.VALUE,Optional.of(raw(value)));}

    @Test void actualOriginalPacketsCrossTheProductionBinderDirectoryAndBothRpcVersionsWithFullWidthResults()throws Exception {
        for(JsonNode original:RootMcpActivityReadsTest.originalCases()) {
            Query query=Query.valueOf(original.path("query").textValue());var packet=RootMcpActivityReadsTest.actualPacket(original,temporary.resolve("sdk-"+query.name()));
            var request=new RootMcpActivityReads.Request(query,packet.receipt().request().before().frame().revision(),packet.receipt().request().arguments());
            RawJson encoded=RootMcpActivityReads.encodeRequest(request);var descriptor=RootPublicCatalogCodec.executableTool(original(query));
            descriptor.validateArguments(arguments(node(encoded)));byte[] nativeBefore=ActivityReadCodec.encode(packet.payload());
            RawJson expected=ActivityNativeContracts.normalizedForPublic(packet);var invoked=new AtomicInteger();
            var directory=software(query,typed->{invoked.incrementAndGet();assertEquals(request,typed);
                return RootMcpActivityReads.present(query,new PlanningReadResult.Known<>(packet,packet.receipt(),packet.receipt().before().binding().nativeEvidence()));
            },packet.receipt().request().source().sourceRef());
            assertEquals(Scope.SOFTWARE_ONLY,directory.scope());String name=RootMcpActivityReads.publicName(query);
            var actual=directory.invoke(PublicMcpBindingTest.call(name,new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8)));
            descriptor.validateResult(actual);assertEnvelope(node(expected),node(new RawJson(actual.bytes())));
            for(String version:List.of("2025-11-25",PublicMcpSession.MODERN))try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",rpcFields(name,encoded)));
                var received=peer.receive();assertFalse(received.has("error"));assertEnvelope(node(expected),(ObjectNode)received.get("result"));
            }
            assertEquals(3,invoked.get());assertArrayEquals(nativeBefore,ActivityReadCodec.encode(packet.payload()));
        }
    }
    @Test void originalNativeRedUsesItsRealTypedRootFaultAndTheStandardRpcErrorWithoutProducingBusinessJson()throws Exception {
        for(JsonNode original:RootMcpActivityReadsTest.originalCases()) {
            Query query=Query.valueOf(original.path("query").textValue());var packet=RootMcpActivityReadsTest.actualPacket(original,temporary.resolve("red-"+query.name()));
            var request=new RootMcpActivityReads.Request(query,packet.receipt().request().before().frame().revision(),packet.receipt().request().arguments());
            RawJson encoded=RootMcpActivityReads.encodeRequest(request);var returned=original.path("red").path("returned");
            var ack=new NativeActionPort.AckReceived(returned.path("request_id").textValue(),false,Optional.empty(),raw(returned),NativeWire.packet(raw(returned).bytes()));
            var unavailable=new PlanningReadResult.Unavailable<ActivityNativeContracts.Packet>("actual retained original native RED",Optional.of(ack));
            String message=original.path("red").path("message").textValue();var invoked=new AtomicInteger();
            var directory=software(query,typed->{invoked.incrementAndGet();assertEquals(request,typed);return RootMcpActivityReads.present(query,unavailable);},packet.receipt().request().source().sourceRef());
            String name=RootMcpActivityReads.publicName(query);
            var failure=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(name,new String(encoded.bytes(),java.nio.charset.StandardCharsets.UTF_8))));
            var typed=assertInstanceOf(PublicServiceFailure.class,failure.getCause());assertEquals(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,typed.kind());
            assertEquals(original.path("red").path("kind").textValue(),typed.kind().pythonClassName());assertEquals(message,typed.getMessage());assertEquals(message,failure.getMessage());
            var cause=assertInstanceOf(RootMcpActivityReads.ActualReadFailure.class,typed.getCause());
            assertEquals(query,cause.evidence().query());assertEquals(RootMcpActivityReads.FailureStage.NATIVE_RED,cause.evidence().stage());
            assertSame(ack,cause.evidence().original().orElseThrow());assertTrue(typed.originalCandidate().isEmpty());
            for(String version:List.of("2025-11-25",PublicMcpSession.MODERN))try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                peer.initialize(version);peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",rpcFields(name,encoded)));
                var response=peer.receive();assertFalse(response.has("error"));var result=response.get("result");assertTrue(result.get("isError").booleanValue());
                assertFalse(result.has("structuredContent"));assertEquals("Error executing tool "+name+": "+message,result.get("content").get(0).get("text").textValue());
            }
            assertEquals(3,invoked.get());
        }
    }
    private static PublicMcpDirectory software(Query query,RootMcpActivityReads.Reader reader,ExactRef softwareSource)throws Exception {
        String name=RootMcpActivityReads.publicName(query);var destination=PublicMcpBindingTest.oneAdmitted(name);
        var binding=RootMcpActivityReads.componentMethods(reader,softwareSource).stream().filter(value->value.name().equals(name)).findFirst().orElseThrow();
        register(destination,RootPublicCatalogCodec.executableTool(original(query)),binding);return destination.freezeSoftwareScope();
    }
    private static <Q,R> void register(PublicMcpBindings destination,ToolDescriptor descriptor,McpExecutableDirectory.DirectBinding<Q,R> binding) {
        destination.registerDirect(descriptor,binding.kind(),binding.requestType(),binding.resultType(),binding.actual(),binding.decoder(),binding.encoder(),binding.target());
    }
    private static String rpcFields(String name,RawJson encoded) {
        var fields=StrictJson.object().put("name",name);fields.set("arguments",node(encoded));
        String value=new String(McpJson.encode(fields),java.nio.charset.StandardCharsets.UTF_8);return value.substring(1,value.length()-1);
    }
    private static void assertEnvelope(ObjectNode expected,ObjectNode envelope) {
        assertFalse(envelope.get("isError").booleanValue());assertEquals(expected,envelope.get("structuredContent"));
        var content=envelope.get("content");assertEquals(1,content.size());assertEquals("text",content.get(0).get("type").textValue());
        assertEquals(expected,node(new RawJson(content.get(0).get("text").textValue().getBytes(java.nio.charset.StandardCharsets.UTF_8))));
    }
}

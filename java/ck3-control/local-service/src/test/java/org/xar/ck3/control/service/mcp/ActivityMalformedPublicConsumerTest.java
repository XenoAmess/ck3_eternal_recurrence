package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.NativeWire;
import org.xar.ck3.control.nativebridge.capabilities.activity.*;
import org.xar.ck3.control.nativebridge.capabilities.activity.ActivityNativeContracts.Query;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;

/** Original Python malformed packets enter the same decoder, binder and both RPC wire versions.
 * Software fixtures do not grant a Root observation, private read permission or Game custody. */
final class ActivityMalformedPublicConsumerTest {
    @TempDir Path temporary;

    @Test void originalMalformedPayloadKindAndMessageSurviveActualDecoderDirectoryAndBothRpcVersions()throws Exception {
        int cases=0;
        for(JsonNode original:RootMcpActivityReadsTest.originalCases()) {
            Query query=Query.valueOf(original.path("query").textValue());
            var packet=RootMcpActivityReadsTest.actualPacket(original,temporary.resolve(query.name()));
            var receipt=packet.receipt();
            var request=new RootMcpActivityReads.Request(query,receipt.request().before().frame().revision(),receipt.request().arguments());
            var installed=new ActivityNativeContracts.Installation(Arrays.stream(Query.values()).map(value->new ActivityNativeContracts.Source(value,receipt.request().source().sourceRef())).toList(),(value,read)->{});
            for(JsonNode malformed:original.path("malformed")) {
                cases++;JsonNode returned=malformed.get("returned");String id=returned.path("request_id").textValue();
                var ack=new NativeActionPort.AckReceived(id,true,Optional.of(raw(returned.get("result"))),raw(returned),NativeWire.packet(raw(returned).bytes()));
                var broken=new PlanningReadReceipt(receipt.request(),receipt.contractId(),id,receipt.before(),receipt.after(),ack);
                String message=malformed.path("message").textValue();
                var decoded=assertThrows(ActivityNativeContracts.LivePayloadFailure.class,()->installed.contract(query).decode(broken));
                assertEquals(message,decoded.getMessage(),query+"/"+malformed.path("case").asText());
                decoded.requireOriginal(installed.contract(query),broken.request(),broken);
                if(query==Query.HOSTED){
                    var replayed=assertThrows(ActivityReadCodec.MalformedPayload.class,()->installed.contract(query).replay(broken));
                    assertFalse(OriginalReadDecodeFailure.class.isInstance(replayed),"pure replay cannot mint live decoder custody");
                }
                var unavailable=new PlanningReadResult.Unavailable<ActivityNativeContracts.Packet>("actual original native decoder rejected this payload",Optional.of(ack),Optional.of(decoded));
                var failure=assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.present(query,unavailable));
                assertEquals(malformed.path("kind").textValue(),failure.kind().pythonClassName());assertEquals(message,failure.getMessage());
                var evidence=assertInstanceOf(RootMcpActivityReads.ActualReadFailure.class,failure.getCause());
                assertEquals(RootMcpActivityReads.FailureStage.PAYLOAD_MALFORMED,evidence.evidence().stage());assertSame(ack,evidence.evidence().original().orElseThrow());
                assertSame(decoded,evidence.getCause());assertInstanceOf(ActivityReadCodec.MalformedPayload.class,decoded.getCause());
                var invoked=new AtomicInteger();
                var directory=software(query,typed->{invoked.incrementAndGet();assertEquals(request,typed);return RootMcpActivityReads.present(query,unavailable);},receipt.request().source().sourceRef());
                String name=RootMcpActivityReads.publicName(query);RawJson encoded=RootMcpActivityReads.encodeRequest(request);
                var direct=assertThrows(ToolFailure.class,()->directory.invoke(PublicMcpBindingTest.call(name,new String(encoded.bytes(),StandardCharsets.UTF_8))));
                var typed=assertInstanceOf(PublicServiceFailure.class,direct.getCause());assertEquals(failure.kind(),typed.kind());assertEquals(message,direct.getMessage());
                for(String version:List.of("2025-11-25",PublicMcpSession.MODERN))try(var peer=new PublicMcpProtocolTest.Peer(directory)) {
                    peer.initialize(version);peer.send(PublicMcpProtocolTest.request(version,"1","tools/call",rpcFields(name,encoded)));
                    var response=peer.receive();assertFalse(response.has("error"));JsonNode result=response.get("result");
                    assertTrue(result.path("isError").booleanValue());assertFalse(result.has("structuredContent"));
                    assertEquals("Error executing tool "+name+": "+message,result.path("content").get(0).path("text").textValue());
                }
                assertEquals(3,invoked.get(),"one actual invocation per direct/RPC call; diagnostic pass does not resend");
            }
            var validButUnavailable=new PlanningReadResult.Unavailable<ActivityNativeContracts.Packet>("actual source guard unavailable despite parseable payload",Optional.of(receipt.original()));
            var originalFailure=assertThrows(PublicServiceFailure.class,()->RootMcpActivityReads.present(query,validButUnavailable));
            assertEquals(RootMcpActivityReads.FailureStage.READ_UNAVAILABLE,assertInstanceOf(RootMcpActivityReads.ActualReadFailure.class,originalFailure.getCause()).evidence().stage());
            assertTrue(originalFailure.getMessage().contains(validButUnavailable.reason()));
        }
        assertEquals(45,cases);
    }
    private static PublicMcpDirectory software(Query query,RootMcpActivityReads.Reader reader,ExactRef source)throws Exception {
        String name=RootMcpActivityReads.publicName(query);var destination=PublicMcpBindingTest.oneAdmitted(name);
        var descriptor=RootPublicCatalogCodec.executableTool(RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(name)).findFirst().orElseThrow());
        var binding=RootMcpActivityReads.componentMethods(reader,source).stream().filter(value->value.name().equals(name)).findFirst().orElseThrow();
        register(destination,descriptor,binding);return destination.freezeSoftwareScope();
    }
    private static <Q,R> void register(PublicMcpBindings destination,ToolDescriptor descriptor,McpExecutableDirectory.DirectBinding<Q,R> binding) {
        destination.registerDirect(descriptor,binding.kind(),binding.requestType(),binding.resultType(),binding.actual(),binding.decoder(),binding.encoder(),binding.target());
    }
    private static RawJson raw(JsonNode value){return new RawJson(StrictJson.canonical(value));}
    private static String rpcFields(String name,RawJson encoded) {
        ObjectNode fields=StrictJson.object().put("name",name);fields.set("arguments",McpJson.parse(encoded.bytes()));
        String text=new String(McpJson.encode(fields),StandardCharsets.UTF_8);return text.substring(1,text.length()-1);
    }
}

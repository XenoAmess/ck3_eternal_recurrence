package org.xar.ck3.control.service.mcp;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.PublicDataJson;
import org.xar.ck3.control.service.root.RootDriverLifecyclePublicCodec;
import org.xar.ck3.control.service.root.RootDriverLifecyclePublicSupplier;
import org.xar.ck3.control.service.root.RootDriverLifecycleResumeCodec;
import org.xar.ck3.control.service.root.RootOriginalPublicTestInputs;
import org.xar.ck3.control.service.root.RootPublicCatalogCodec;

/** Software RPC DATA only. The mandatory original SDK descriptor is never replaced by a fixture. */
final class PublicMcpFullMaterialResponseTest {
    private static final String NAME="ck3_resume_successor_ui_v1";
    private static RawJson snapshot() {
        var original=DriverJson.object(("{\"snapshot_id\":\"snapshot\",\"revision\":1,\"native_revision\":1,\"date_raw\":4,\"paused\":true,\"map_ready\":true,\"speed\":1,\"episode_run_id\":\"run\",\"episode_character_id\":12,\"played_character\":{\"character_id\":12,\"alive\":true},\"active_wars\":[],\"player_armies\":[],\"diagnostics\":{\"bridge_pid\":7,\"connection_generation\":1},\"active_event\":null,\"pending_character_interaction\":null,\"one_life_terminal\":false,\"one_life_terminal_reason\":null}").getBytes(StandardCharsets.UTF_8),8192);
        return PublicDataJson.encodeFullMaterial(original.with("format_version",new IntegerValue(BigInteger.ONE)).with("native_command_history",new Arr(List.of(new Obj(Map.of("opaque_long_decimal",new DecimalValue("0."+"0".repeat(5000)+"1"))),new DecimalValue("-0.0")))));
    }
    @Test void completeResumeMaterialSurvivesActualLegacyAndModernRpcDecoratorsWithoutWideningInputs()throws Exception {
        var actual=RootDriverLifecycleResumeCodec.clear(snapshot());var expected=DriverJson.object(RootDriverLifecycleResumeCodec.encode(actual).bytes(),RawJson.MAXIMUM_BYTES);
        var original=RootOriginalPublicTestInputs.tools().stream().filter(value->value.name().equals(NAME)).findFirst().orElseThrow();var descriptor=RootPublicCatalogCodec.executableTool(original);
        for(String version:List.of("2025-11-25",PublicMcpSession.MODERN)) {
            var calls=new AtomicInteger();var production=RootDriverLifecyclePublicSupplier.resumeBinding(PublicMcpProtocolTest.target().implementationSource(),request->{calls.incrementAndGet();return actual;});
            var registry=PublicMcpBindingTest.oneAdmitted(NAME);
            registry.registerDirect(descriptor,PublicMcpBindings.Kind.DRIVER_DIRECT,RootDriverLifecyclePublicCodec.Resume.class,RootDriverLifecycleResumeCodec.ResumeResult.class,
                    request->production.actual().invoke(request),production.decoder(),production.encoder(),PublicMcpProtocolTest.target());
            try(var peer=new PublicMcpProtocolTest.Peer(registry.freezeSoftwareScope())) {
                if(!version.equals(PublicMcpSession.MODERN))peer.initialize(version);
                peer.send(PublicMcpProtocolTest.request(version,"1","tools/call","\"name\":\""+NAME+"\",\"arguments\":{}"));
                byte[] wire=peer.lines.poll(3,TimeUnit.SECONDS);assertNotNull(wire);assertEquals(1,calls.get());assertThrows(IllegalArgumentException.class,()->McpJson.parse(wire));
                var rpc=McpJson.object(McpJson.parseResult(wire));assertFalse(rpc.has("error"));var result=rpc.get("result");assertFalse(result.get("isError").booleanValue());
                byte[] business=McpJson.tokenResult(McpJson.tokenResult(wire,"result"),"structuredContent");assertEquals(expected,DriverJson.object(business,RawJson.MAXIMUM_BYTES));
                byte[] text=result.get("content").get(0).get("text").textValue().getBytes(StandardCharsets.UTF_8);assertEquals(expected,DriverJson.object(text,RawJson.MAXIMUM_BYTES));
                assertEquals(expected,DriverJson.object(RootDriverLifecycleResumeCodec.encode(RootDriverLifecycleResumeCodec.decode(RawJson.fullMaterial(business))).bytes(),RawJson.MAXIMUM_BYTES));
            }
        }
        var unknown=new Obj(Map.of("unsafe_unknown_identity",new IntegerValue(BigInteger.ONE.shiftLeft(63))));
        assertThrows(IllegalArgumentException.class,()->PublicMcpDirectory.CallResult.fromBusinessJson(PublicDataJson.encodeFullMaterial(unknown)));
        assertThrows(IllegalArgumentException.class,()->new RawJson(snapshot().bytes()));
    }
}

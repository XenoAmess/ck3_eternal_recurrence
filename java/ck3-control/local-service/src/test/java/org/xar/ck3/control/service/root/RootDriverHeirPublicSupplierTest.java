package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.service.mcp.PublicMcpDirectory.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.service.mcp.*;
import org.xar.ck3.control.service.mcp.FirstHeirRelationshipPublicCodec.*;

/** Real direct binding and sole argument/serde boundary. Stop before mandatory actual Root authority; no mocked Ready. */
final class RootDriverHeirPublicSupplierTest {
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    @Test void actualOriginalNameIsDriverDirectAndItsTypedMethodConsumesTheSoleDecoder()throws Exception {
        var calls=new AtomicInteger();var stop=new IllegalStateException("actual Root required");
        var binding=RootDriverHeirPublicSupplier.binding(new ExactRef("software/RootDriverHeirPublicSupplier.java",1,"a".repeat(64)),request->{calls.incrementAndGet();assertEquals(BigInteger.valueOf(7),request.expectedNativeRevision());throw stop;});
        assertEquals("ck3_query_current_first_heir_relationship_private_v1",binding.name());assertEquals(PublicMcpBindings.Kind.DRIVER_DIRECT,binding.kind());
        var call=new ToolCall(binding.name(),new Arguments(Presence.VALUE,Optional.of(raw("{\"expected_native_revision\":7}"))),Optional.empty(),new McpCancellation());
        Request request=binding.decoder().decode(call);assertSame(stop,assertThrows(IllegalStateException.class,()->binding.actual().invoke(request)));assertEquals(1,calls.get());
        assertEquals("queryCurrentFirstHeirRelationship",binding.target().actualMethod());
    }
    @Test void ordinaryAndCaptureBranchesRoundTripWithExplicitSafeRevisionAndOriginalDefaultTimeout(){
        for(String input:List.of("{\"expected_native_revision\":7}","{\"expected_native_revision\":\"18446744073709551615\",\"guardian_capture_output_directory\":null}",
                "{\"expected_native_revision\":7,\"guardian_capture_output_directory\":\"D:/capture/new-leaf\",\"guardian_capture_owned_game_pid\":59077}",
                "{\"expected_native_revision\":\"7\",\"guardian_capture_output_directory\":\"D:/capture/new-leaf\",\"guardian_capture_owned_game_pid\":59077,\"guardian_capture_timeout_seconds\":12.25}")){
            Request request=FirstHeirRelationshipPublicCodec.decode(raw(input));assertEquals(request,FirstHeirRelationshipPublicCodec.decode(FirstHeirRelationshipPublicCodec.encodeRequest(request)));
        }
        var capture=FirstHeirRelationshipPublicCodec.decode(raw("{\"expected_native_revision\":7,\"guardian_capture_output_directory\":\"D:/capture/new-leaf\",\"guardian_capture_owned_game_pid\":59077}"));
        assertEquals(java.time.Duration.ofSeconds(360),capture.capture().orElseThrow().timeout());
        assertThrows(IllegalArgumentException.class,()->capture.requireCurrent(BigInteger.valueOf(8)));
    }
    @Test void wrongMissingNullFloatingUnsafeAndUnknownFieldsNeverReachTheCurrentHandler(){
        for(String input:List.of("{}","{\"expected_native_revision\":null}","{\"expected_native_revision\":true}","{\"expected_native_revision\":7.0}",
                "{\"expected_native_revision\":9007199254740992}","{\"expected_native_revision\":\"07\"}","{\"expected_native_revision\":\"18446744073709551616\"}",
                "{\"expected_native_revision\":7,\"first_heir_id\":42}","{\"expected_native_revision\":7,\"guardian_capture_output_directory\":\"D:/capture/new\"}",
                "{\"expected_native_revision\":7,\"guardian_capture_output_directory\":\"D:/capture/new\",\"guardian_capture_owned_game_pid\":true}",
                "{\"expected_native_revision\":7,\"guardian_capture_output_directory\":\"D:/capture/new\",\"guardian_capture_owned_game_pid\":59077,\"guardian_capture_timeout_seconds\":0}"))
            assertThrows(IllegalArgumentException.class,()->FirstHeirRelationshipPublicCodec.decode(raw(input)),input);
    }
}

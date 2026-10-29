package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicBindings;
import org.xar.ck3.control.nativebridge.capabilities.registry.PublicMethod;
import org.xar.ck3.control.service.mcp.CheckpointPublicCodec;

/** Actual shared registry/codec DATA boundary only: no private Restored binding, Root, SAVE or Host is fabricated. */
final class RootRestoreCheckpointPublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("restore-protocol-data-only",1,"a".repeat(64));
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    @Test void actualRegistryConsumesTheSharedThreeRevisionBranchesAndPreservesUnconfirmedData()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RawJson unconfirmed=raw("{\"step\":\"restore-checkpoint\",\"status\":\"restore_unknown\",\"accepted\":false,\"never_replay\":true,\"revision\":\"18446744073709551615\"}");
        RootRestoreCheckpointPublicProducts.register(registry,input->{calls.incrementAndGet();
            var wire=CheckpointPublicCodec.encodeRequest(input);
            assertEquals(input,CheckpointPublicCodec.decode(PublicBindings.present(wire)));
            return unconfirmed;
        },SOURCE);
        registry.freeze(Set.of(PublicMethod.RESTORE_CHECKPOINT));var route=registry.lookup(PublicMethod.RESTORE_CHECKPOINT).orElseThrow();
        for(String input:List.of("{}","{\"expected_revision\":null}","{\"expected_revision\":\"18446744073709551615\"}")) {
            var result=route.invoke(PublicBindings.present(raw(input)));
            assertArrayEquals(unconfirmed.bytes(),result.bytes());var row=StrictJson.parse(result.bytes());
            assertFalse(row.get("accepted").booleanValue());assertTrue(row.get("never_replay").booleanValue());
            assertEquals("18446744073709551615",row.get("revision").textValue());
        }
        assertEquals(3,calls.get());assertTrue(registry.lookup(PublicMethod.SAVE_CHECKPOINT).isEmpty());
        assertTrue(registry.lookup(PublicMethod.START_NEXT_EPISODE).isEmpty());
    }
    @Test void malformedArgumentsStopAtTheSharedDecoderBeforeTheOnlyTypedHandler()throws Exception {
        var registry=new PublicBindings();var calls=new AtomicInteger();
        RootRestoreCheckpointPublicProducts.register(registry,input->{calls.incrementAndGet();throw new AssertionError("invalid input entered the actual restore route");},SOURCE);
        registry.freeze(Set.of(PublicMethod.RESTORE_CHECKPOINT));var route=registry.lookup(PublicMethod.RESTORE_CHECKPOINT).orElseThrow();
        for(String input:List.of("null","[]","{\"expected_revision\":true}","{\"expected_revision\":1.0}",
                "{\"expected_revision\":9007199254740992}","{\"expected_revision\":\"01\"}","{\"expected_revision\":\"18446744073709551616\"}",
                "{\"expected_revision\":null,\"expected_revision\":null}","{\"caller_authorized\":true}"))
            assertThrows(IllegalArgumentException.class,()->route.invoke(PublicBindings.present(raw(input))));
        assertEquals(0,calls.get());
    }
}

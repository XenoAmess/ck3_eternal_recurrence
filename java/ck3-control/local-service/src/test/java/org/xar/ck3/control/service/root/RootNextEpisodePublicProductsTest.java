package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.LifecycleExpectedPostcondition.Operation;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.registry.*;
import org.xar.ck3.control.service.mcp.LifecyclePublicCodec;

/** Actual shared registry/codec protocol DATA. No fake Core, ManagedGame or private applied lifecycle proof. */
final class RootNextEpisodePublicProductsTest {
    private static final ExactRef SOURCE=new ExactRef("protocol-only-next-products-source",1,"a".repeat(64));
    private static final ExactRef RECEIPT=new ExactRef("protocol-only-original-unknown-receipt",1,"b".repeat(64));
    private static RawJson raw(String value){return new RawJson(value.getBytes(StandardCharsets.UTF_8));}
    private static LifecyclePublicCodec.Payload unknown() {
        return new LifecyclePublicCodec.Unconfirmed(Operation.START_NEXT_EPISODE,ActionReceipt.Outcome.UNRESOLVED,false,
                "original-protocol-action","c".repeat(64),RECEIPT,"protocol-only-machine",Instant.parse("2026-10-24T02:00:00Z"));
    }
    private static PublicBindings.BoundBinding register(List<LifecyclePublicCodec.Request> received) {
        var registry=new PublicBindings();
        var installed=RootNextEpisodePublicProducts.register(registry,input->{received.add(input);return unknown();},SOURCE);
        registry.freeze(Set.of(PublicMethod.START_NEXT_EPISODE));
        assertEquals(installed,registry.lookup(PublicMethod.START_NEXT_EPISODE).orElseThrow());
        assertTrue(registry.lookup(PublicMethod.ONE_LIFE_SETTLEMENT).isEmpty());
        assertTrue(registry.lookup(PublicMethod.SETTLE_ONE_LIFE).isEmpty());
        assertEquals(LifecyclePublicCodec.Request.class,installed.requestType());assertEquals(LifecyclePublicCodec.Payload.class,installed.resultType());
        return installed;
    }

    @Test void missingNullObjectAndExplicitNullRevisionRetainTheirOriginalSharedRequestStates() throws Exception {
        var received=new ArrayList<LifecyclePublicCodec.Request>();var binding=register(received);
        for(var arguments:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),new PublicBindings.Null(),
                PublicBindings.present(raw("{}")),PublicBindings.present(raw("{\"expected_revision\":null}")))) {
            var expected=LifecyclePublicCodec.decodeRequest(arguments);
            var encoded=binding.invoke(arguments);
            assertEquals(expected,received.getLast());assertEquals(arguments,LifecyclePublicCodec.encodeRequest(expected));
            assertTrue(expected.expected().isEmpty());
            var output=StrictJson.parse(encoded.bytes());assertEquals("action_state_unknown",output.get("status").textValue());
            assertTrue(output.get("never_replay").booleanValue());assertFalse(output.get("material_result_available").booleanValue());
            assertEquals(RECEIPT.toJson(),output.get("original_receipt"));assertEquals("start-next-episode",output.get("step").textValue());
        }
        assertEquals(4,received.size());assertNotEquals(received.getFirst(),received.get(1));assertNotEquals(received.get(2),received.getLast());
    }
    @Test void exactUint64RevisionSurvivesTheSameRegistryDecoderAndSharedRequestRoundtrip() throws Exception {
        var received=new ArrayList<LifecyclePublicCodec.Request>();var binding=register(received);
        var arguments=PublicBindings.present(raw("{\"expected_revision\":\"18446744073709551615\"}"));
        binding.invoke(arguments);var request=received.getFirst();assertEquals(new BigInteger("18446744073709551615"),request.expected().orElseThrow());
        assertEquals(arguments,LifecyclePublicCodec.encodeRequest(request));
        assertEquals(request,LifecyclePublicCodec.decodeRequest(LifecyclePublicCodec.encodeRequest(request)));
    }
    @Test void wrongTypesAliasesDuplicatesAndOverflowFailBeforeTheActualHandler() {
        var calls=new AtomicInteger();var registry=new PublicBindings();
        var binding=RootNextEpisodePublicProducts.register(registry,input->{calls.incrementAndGet();return unknown();},SOURCE);
        registry.freeze(Set.of(PublicMethod.START_NEXT_EPISODE));
        for(var value:List.of("{\"expected_revision\":true}","{\"expected_revision\":7}","{\"expected_revision\":7.0}",
                "{\"expected_revision\":\"07\"}","{\"expected_revision\":\"18446744073709551616\"}",
                "{\"expected_revision\":\"7\",\"native_revision\":\"7\"}","{\"expected_revision\":\"7\",\"expected_revision\":\"8\"}","[]"))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(value))));
        assertEquals(0,calls.get());
    }
}

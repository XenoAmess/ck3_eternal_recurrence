package org.xar.ck3.control.service.mcp;

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

/** Actual production registration/codec DATA seam only. No Core, ManagedGame or private lifecycle proof is fabricated. */
class RootMcpLifecycleBindingTest {
    private static final ExactRef SOURCE=new ExactRef("protocol-only-death-adapter-source",1,"a".repeat(64));
    private static final ExactRef RECEIPT=new ExactRef("protocol-only-original-unknown-receipt",1,"b".repeat(64));
    private static RawJson raw(String body){return new RawJson(body.getBytes(StandardCharsets.UTF_8));}
    private static LifecyclePublicCodec.Payload unknown(){return new LifecyclePublicCodec.Unconfirmed(Operation.DEATH_TERMINAL,
            ActionReceipt.Outcome.UNRESOLVED,false,"original-protocol-action","c".repeat(64),RECEIPT,
            "protocol-only-machine",Instant.parse("2026-10-24T03:00:00Z"));}
    @Test void sameRegisteredDeathDecoderAndEncoderPreserveOptionalRevisionAndUnknownOriginalReference()throws Exception {
        var requests=new ArrayList<LifecyclePublicCodec.Request>();var registry=new PublicBindings();
        var binding=RootMcpLifecycle.registerSettlement(registry,input->{requests.add(input);return unknown();},SOURCE);
        registry.freeze(Set.of(PublicMethod.SETTLE_ONE_LIFE));
        assertSame(binding,registry.lookup(PublicMethod.SETTLE_ONE_LIFE).orElseThrow());
        assertTrue(registry.lookup(PublicMethod.START_NEXT_EPISODE).isEmpty());
        for(var input:List.<PublicBindings.Arguments>of(new PublicBindings.Missing(),new PublicBindings.Null(),
                PublicBindings.present(raw("{\"expected_revision\":\"18446744073709551615\"}")))) {
            var encoded=binding.invoke(input);assertEquals(input,LifecyclePublicCodec.encodeRequest(requests.getLast()));
            var output=StrictJson.parse(encoded.bytes());assertEquals("death-terminal",output.get("step").textValue());
            assertEquals("action_state_unknown",output.get("status").textValue());assertTrue(output.get("never_replay").booleanValue());
            assertFalse(output.get("material_result_available").booleanValue());assertEquals(RECEIPT.toJson(),output.get("original_receipt"));
        }
        assertNotEquals(requests.getFirst(),requests.get(1));
        assertEquals(new BigInteger("18446744073709551615"),requests.getLast().expected().orElseThrow());
    }
    @Test void invalidRevisionDoesNotReachTheRegisteredDeathDelegate() {
        var calls=new AtomicInteger();var registry=new PublicBindings();
        var binding=RootMcpLifecycle.registerSettlement(registry,input->{calls.incrementAndGet();return unknown();},SOURCE);
        registry.freeze(Set.of(PublicMethod.SETTLE_ONE_LIFE));
        for(var body:List.of("{\"expected_revision\":true}","{\"expected_revision\":7.0}",
                "{\"expected_revision\":\"07\"}","{\"expected_revision\":\"18446744073709551616\"}"))
            assertThrows(IllegalArgumentException.class,()->binding.invoke(PublicBindings.present(raw(body))));
        assertEquals(0,calls.get());
    }
}

package org.xar.ck3.control.wave3.development.wartimesequencing;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.locks.ReentrantLock;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave3.development.constructionquery.ConstructionQuoteIdentity;

/** Actual producer -> original-lock consumer -> serialized final review, using the unchanged original corpus fixture. */
final class ConstructionFreshQuoteConsumerTest {
    @Test void aFreshNativeRequestAndProofReachTheOriginalAuthorityOnceUnderItsExistingLock() throws Exception {
        ObjectNode original = OrdinaryWartimeConstructionTest.complete();
        var planned = OrdinaryWartimeConstruction.compose(OrdinaryWartimeConstructionCodec.decode(StrictJson.canonical(original)));
        ObjectNode fresh = original.deepCopy();
        fresh.withObject("/quoted_outlay/query_observation").put("native_query_request_id", "actual-second-native-read");
        fresh.withObject("/quoted_outlay/query_observation/native_envelope").put("request_id", "actual-second-native-read");
        fresh.withObject("/quoted_outlay/query_observation/native_envelope/result/private_probe").put("proof_epoch", 2);
        var observed = new OrdinaryWartimeConstructionCodec.ObservedRequest(StrictJson.canonical(fresh));
        ReentrantLock lock = new ReentrantLock(); AtomicInteger calls = new AtomicInteger();
        var accepted = OrdinaryWartimeConstructionConsumer.withCurrentBeforeIntent(planned, lock, () -> observed, result -> {
            assertTrue(lock.isHeldByCurrentThread()); calls.incrementAndGet(); return "original-intent-authority";
        });
        assertEquals(OrdinaryWartimeConstructionConsumer.FinalStatus.EXISTING_AUTHORITY_CALLED, accepted.status());
        assertEquals(Optional.of("original-intent-authority"), accepted.existingAuthorityResult()); assertEquals(1, calls.get());
        assertFalse(lock.isLocked()); assertFalse(accepted.nativeActionAppliedVerified());
        var restored = OrdinaryWartimeConstructionCodec.decodeFinalReview(OrdinaryWartimeConstructionCodec.encodeFinalReview(accepted.review()), Optional.of(observed.input()));
        assertEquals(accepted.status(), restored.status()); assertFalse(restored.nativeActionAppliedVerified());
    }
    @Test void aChangedNativeWorldNeverUsesTheTransportRefreshException() throws Exception {
        ObjectNode original = OrdinaryWartimeConstructionTest.complete();
        var planned = OrdinaryWartimeConstruction.compose(OrdinaryWartimeConstructionCodec.decode(StrictJson.canonical(original)));
        ObjectNode changed = original.deepCopy();
        changed.withObject("/quoted_outlay/query_observation").put("native_query_request_id", "fresh-world-read");
        changed.withObject("/quoted_outlay/query_observation/native_envelope").put("request_id", "fresh-world-read");
        changed.withObject("/quoted_outlay/query_observation/native_envelope/result/private_probe").put("proof_epoch", 2);
        changed.withObject("/quoted_outlay/query_observation/native_envelope/result/private_probe/player_world_building_sources").put("new_native_extension", true);
        AtomicInteger calls = new AtomicInteger();
        var rejected = OrdinaryWartimeConstructionConsumer.withCurrentBeforeIntent(planned, new ReentrantLock(),
                () -> new OrdinaryWartimeConstructionCodec.ObservedRequest(StrictJson.canonical(changed)), result -> { calls.incrementAndGet(); return "bad"; });
        assertEquals(OrdinaryWartimeConstructionConsumer.FinalStatus.CURRENT_QUOTE_CHANGED, rejected.status()); assertEquals(0, calls.get());
    }
    @Test void proofTokensAreExactIntegersAndCannotRegress() {
        byte[] original = "{\"native_query_request_id\":\"first\",\"proof_epoch\":2,\"candidate\":{},\"world\":{}}".getBytes(java.nio.charset.StandardCharsets.UTF_8);
        for (String invalid : java.util.List.of("true", "2.0", "\"2\"", "0", "1")) {
            byte[] next = ("{\"native_query_request_id\":\"second\",\"proof_epoch\":" + invalid + ",\"candidate\":{},\"world\":{}}").getBytes(java.nio.charset.StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> ConstructionQuoteIdentity.same(original, next));
        }
    }
}

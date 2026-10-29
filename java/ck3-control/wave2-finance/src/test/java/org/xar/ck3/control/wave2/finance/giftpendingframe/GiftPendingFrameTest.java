package org.xar.ck3.control.wave2.finance.giftpendingframe;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;

final class GiftPendingFrameTest {
    private static JsonNode golden() throws IOException {
        try (var stream = GiftPendingFrameTest.class.getResourceAsStream("/giftpendingframe/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual old producer/consumer golden is required"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static byte[] wire(JsonNode node) { return StrictJson.canonical(node); }
    @Test void actualOldProducerAndProofConsumerAgreeForReadyForeignAndTimeoutFrames() throws IOException {
        JsonNode golden = golden(); var pending = GiftPendingCodec.decodeLedger(wire(golden.get("pending_ledger"))).pending().orElseThrow();
        assertEquals(12, golden.path("cases").size());
        for (JsonNode test : golden.get("cases")) {
            var source = GiftPendingFrameCodec.decodeSnapshot(wire(test.get("source_snapshot")));
            var fresh = GiftPendingFrameCodec.decodeSnapshot(wire(test.get("fresh_snapshot")));
            assertEquals(test.path("trace").path("predicate_result").booleanValue(), GiftPendingFramePolicy.changedOrReady(pending, source, fresh), test.path("name").asText());
            AtomicInteger calls = new AtomicInteger();
            GiftPendingFramePolicy.ExistingSnapshotWaitPort port = (before, predicate, timeout) -> {
                calls.incrementAndGet(); assertEquals(source, before); assertEquals(Duration.ofSeconds(5), timeout);
                assertEquals(test.path("trace").path("predicate_result").booleanValue(), predicate.test(fresh)); return fresh;
            };
            if (test.path("expected").path("accepted").booleanValue()) {
                var proof = GiftPendingFramePolicy.awaitFresh(pending, source, port);
                assertEquals(test.path("expected").path("proof"), StrictJson.parse(GiftPendingFrameCodec.encodeProof(proof)));
                assertEquals(test.path("expected").path("consumer"), StrictJson.parse(GiftPendingFrameCodec.classifyProof(proof)));
                assertEquals(proof, GiftPendingFrameCodec.decodeProof(GiftPendingFrameCodec.encodeProof(proof)));
                assertFalse(proof.businessSubmissionAttempted()); assertFalse(proof.receiptQueryAttempted()); assertFalse(proof.giftSubmissionReplayed());
            } else {
                var error = assertThrows(IllegalArgumentException.class, () -> GiftPendingFramePolicy.awaitFresh(pending, source, port));
                assertEquals(test.path("expected").path("error").textValue(), error.getMessage(), test.path("name").asText());
            }
            assertEquals(1, calls.get(), "one bounded read-only wait");
        }
    }
    @Test void alteredUnknownAndRawFloatProofsCannotQualifyReadOnlyReplan() throws IOException {
        JsonNode original = golden().path("cases").get(0).path("expected").path("proof");
        for (String flag : List.of("business_submission_attempted", "receipt_query_attempted", "gift_submission_replayed")) {
            ObjectNode proof = original.deepCopy(); proof.put(flag, true);
            assertThrows(IllegalArgumentException.class, () -> GiftPendingFrameCodec.decodeProof(wire(proof)));
        }
        ObjectNode extra = original.deepCopy(); extra.put("unreviewed", true);
        assertThrows(IllegalArgumentException.class, () -> GiftPendingFrameCodec.decodeProof(wire(extra)));
        String raw = new String(wire(original), StandardCharsets.UTF_8);
        String floatRevision = raw.replace("\"pre_native_revision\":" + original.get("pre_native_revision"), "\"pre_native_revision\":1.0");
        assertThrows(IllegalArgumentException.class, () -> GiftPendingFrameCodec.decodeProof(floatRevision.getBytes(StandardCharsets.UTF_8)));
        ObjectNode changedOwner = original.deepCopy(); ((ObjectNode) changedOwner.get("fresh_frame")).put("bridge_pid", 999);
        assertThrows(IllegalArgumentException.class, () -> GiftPendingFrameCodec.decodeProof(wire(changedOwner)));
    }
    @Test void unavailableSourceCannotEnterWaitAndResourcesDoNotTriggerPrematureWakeup() throws IOException {
        JsonNode golden = golden(); var pending = GiftPendingCodec.decodeLedger(wire(golden.get("pending_ledger"))).pending().orElseThrow();
        ObjectNode bad = golden.path("cases").get(0).path("source_snapshot").deepCopy(); bad.put("paused", false);
        var frame = GiftPendingFrameCodec.decodeSnapshot(wire(bad)); AtomicInteger calls = new AtomicInteger();
        assertThrows(IllegalArgumentException.class, () -> GiftPendingFramePolicy.awaitFresh(pending, frame, (source, predicate, timeout) -> {
            calls.incrementAndGet(); return source;
        }));
        assertEquals(0, calls.get());
        ObjectNode sameRevision = golden.path("cases").get(0).path("source_snapshot").deepCopy();
        var source = GiftPendingFrameCodec.decodeSnapshot(wire(sameRevision));
        sameRevision.putObject("played_character_gold").put("raw", 1);
        sameRevision.put("new_opinion_extension", 99);
        assertFalse(GiftPendingFramePolicy.changedOrReady(pending, source, GiftPendingFrameCodec.decodeSnapshot(wire(sameRevision))));
        assertTrue(pending.baseline().nativeSnapshotRevision().signum() > 0);
    }
}

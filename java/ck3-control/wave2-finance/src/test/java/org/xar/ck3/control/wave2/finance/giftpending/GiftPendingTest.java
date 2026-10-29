package org.xar.ck3.control.wave2.finance.giftpending;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.PendingStatus;

final class GiftPendingTest {
    private static JsonNode golden() throws IOException {
        try (var stream = GiftPendingTest.class.getResourceAsStream("/giftpending/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("original producer capture is required; do not count an absent golden as skipped"); }
            return StrictJson.parse(stream.readAllBytes(), 98_304);
        }
    }
    private static byte[] wire(JsonNode value) { return GiftPendingCodec.json(value); }
    private static JsonNode tree(byte[] value) { return StrictJson.parse(value, 98_304); }
    private static byte[] ledger(JsonNode golden, String state) { return wire(golden.path("ledgers").path(state)); }

    @Test void originalProducerCompleteTransitionChainAndEveryPersistenceRoundTrip() throws IOException {
        JsonNode original = golden();
        assertEquals("xar.giftpending.original-producer-golden/v1", original.path("schema").textValue());
        assertFalse(original.path("machine_id").textValue().isEmpty()); assertEquals(10, original.path("source_refs").size());
        byte[] begun = GiftPendingTransitionAdapter.begin(ledger(original, "empty"), wire(original.get("begin")));
        assertEquals(original.path("ledgers").path("begun"), tree(begun));
        byte[] acknowledged = GiftPendingTransitionAdapter.markAck(begun, "gift-real-1", wire(original.get("ack")));
        assertEquals(original.path("ledgers").path("acknowledged"), tree(acknowledged));
        byte[] restored = GiftPendingTransitionAdapter.markRestore(acknowledged, "gift-real-1");
        assertEquals(original.path("ledgers").path("restored"), tree(restored));
        byte[] completed = GiftPendingTransitionAdapter.complete(restored, "gift-real-1", wire(original.get("receipt")));
        assertEquals(original.path("ledgers").path("completed"), tree(completed));
        for (JsonNode state : original.get("ledgers")) {
            Ledger model = GiftPendingCodec.decodeLedger(wire(state));
            assertEquals(model, GiftPendingCodec.decodeLedger(GiftPendingCodec.encodeLedger(model)));
        }
        byte[] withBom = ("\ufeff" + new String(begun, StandardCharsets.UTF_8)).getBytes(StandardCharsets.UTF_8);
        assertEquals(GiftPendingCodec.decodeLedger(begun), GiftPendingCodec.decodeLedger(withBom));
        JsonNode extension = tree(acknowledged).path("pending").path("ack").path("native_extension");
        assertTrue(extension.path("float_extension").isFloatingPointNumber());
        assertEquals(new BigInteger("18446744073709551615"), extension.path("exact_integer").bigIntegerValue());
        assertTrue(extension.path("nullable").isNull()); assertTrue(extension.path("empty").isArray());
    }
    @Test void unresolvedAndRetiredIdentitiesNeverSubmitAgain() throws IOException {
        JsonNode original = golden(); byte[] begin = wire(original.get("begin"));
        assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.begin(ledger(original, "begun"), begin));
        assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.begin(ledger(original, "completed"), begin));
        Ledger initial = GiftPendingCodec.decodeLedger(ledger(original, "begun"));
        for (JsonNode item : original.get("cold_cases")) {
            var input = GiftColdRecoveryCodec.decodeRecovery(wire(item.get("recovery")));
            var result = GiftColdRecovery.resolve(initial, "gift-real-1", input);
            assertEquals(item.get("expected"), tree(GiftColdRecoveryCodec.encodeResult(result.result())), item.path("name").asText());
            assertEquals(item.get("resolved_result"), tree(GiftColdRecoveryCodec.encodeResolution(result)), item.path("name").asText());
            assertEquals(item.get("ledger_after"), tree(GiftPendingCodec.encodeLedger(result.ledger())));
            assertFalse(result.result().originalRequestReplayAllowed());
            if (result.result() instanceof GiftColdRecovery.Unresolved) { assertSame(initial, result.ledger()); }
            else { assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.begin(GiftPendingCodec.encodeLedger(result.ledger()), begin)); }
        }
    }
    @Test void knownEmptyVectorAndAckCannotSettlePending() throws IOException {
        JsonNode original = golden(); byte[] pending = ledger(original, "acknowledged");
        assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.complete(pending, "gift-real-1", wire(original.get("ack"))));
        var missingPost = GiftColdRecoveryCodec.decodeRecovery("{\"targeting_factions\":[]}".getBytes(StandardCharsets.UTF_8));
        Ledger model = GiftPendingCodec.decodeLedger(pending);
        var result = GiftColdRecovery.resolve(model, "gift-real-1", missingPost);
        assertTrue(result.result() instanceof GiftColdRecovery.Unresolved); assertSame(model, result.ledger());
        assertFalse(result.result().actionRetryAllowed());
    }
    @Test void receiptBindsEveryIdentityAndMaterialFactBeforeCandidateRetirement() throws IOException {
        JsonNode original = golden(); byte[] pending = ledger(original, "begun");
        for (String field : List.of("request_id", "source_faction_id", "recipient_character_id", "player_character_id", "post_snapshot_revision",
                "post_native_snapshot_revision", "post_observed_date_raw", "post_player_gold_raw", "post_gift_opinion_modifier_value")) {
            ObjectNode receipt = original.get("receipt").deepCopy();
            if (field.equals("request_id")) { receipt.put(field, "other-request"); } else { receipt.put(field, -1); }
            assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.complete(pending, "gift-real-1", wire(receipt)), field);
        }
        ObjectNode unchangedGold = original.get("receipt").deepCopy(); unchangedGold.put("post_player_gold_raw", 25_000_000);
        assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.complete(pending, "gift-real-1", wire(unchangedGold)));
        assertEquals(PendingStatus.SUBMISSION_STARTED_UNCONFIRMED, GiftPendingCodec.decodeLedger(pending).pending().orElseThrow().status());
    }
    @Test void exactLedgerAndRawTokenGuardsRejectMalformedOrAmbiguousData() throws IOException {
        JsonNode original = golden(); String valid = new String(ledger(original, "begun"), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "\"1\"", "null")) {
            String raw = valid.replace("\"format_version\":1", "\"format_version\":" + token);
            assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(raw.getBytes(StandardCharsets.UTF_8)), token);
        }
        for (String field : List.of("source_faction_id", "source_bridge_pid", "pre_date_raw", "pre_snapshot_revision", "opinion_delta", "pre_recipient_opinion_of_player")) {
            ObjectNode ledger = original.path("ledgers").path("begun").deepCopy(); ObjectNode pending = (ObjectNode) ledger.get("pending");
            pending.put(field, true); assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(wire(ledger)), field);
            String raw = valid.replace("\"" + field + "\":" + original.path("ledgers").path("begun").path("pending").get(field),
                    "\"" + field + "\":1.0");
            assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(raw.getBytes(StandardCharsets.UTF_8)), field);
            pending.remove(field); assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(wire(ledger)), field);
        }
        ObjectNode extra = original.path("ledgers").path("begun").deepCopy(); extra.put("unexpected", 1);
        assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(wire(extra)));
        assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger((valid + " {}").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(valid.replace("\"format_version\":1", "\"format_version\":1,\"format_version\":1").getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeLedger(new byte[]{(byte) 0xc3, 0x28}));
        String ack = new String(wire(original.get("ack")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "1.0", "\"1\"", "null", "2")) {
            String raw = "{\"schema_version\":" + token + "," + ack.substring(1);
            assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeAck(raw.getBytes(StandardCharsets.UTF_8)), token);
        }
    }
    @Test void preSubmitReserveAndMembershipGuardPreventAnyCandidate() throws IOException {
        JsonNode original = golden(); ObjectNode begin = original.get("begin").deepCopy();
        ((ObjectNode) begin.path("observation").path("gift_preview")).put("gold_cost_raw", 20_000_000);
        assertThrows(IllegalArgumentException.class, () -> GiftPendingTransitionAdapter.begin(ledger(original, "empty"), wire(begin)));
        ObjectNode missingRecipient = original.get("begin").deepCopy();
        ((ObjectNode) missingRecipient.get("observation")).putArray("source_faction_member_character_ids").add(999);
        assertThrows(IllegalArgumentException.class, () -> GiftPendingCodec.decodeBegin(wire(missingRecipient)));
        assertTrue(GiftPendingCodec.decodeLedger(ledger(original, "empty")).pending().isEmpty());
    }
    @Test void commonReaderProjectionPreservesBlockingAndReobservationEquality() throws IOException {
        JsonNode original = golden(); var view = GiftPendingConsumerAdapter.read(ledger(original, "restored"));
        assertTrue(view.spendingBlocked()); assertFalse(view.giftSubmissionEnabled()); assertFalse(view.publicCapabilityAdvertised());
        assertEquals("gift-real-1", view.recovery().orElseThrow().requestId());
        assertTrue(view.sameLedgerAs(GiftPendingCodec.decodeLedger(ledger(original, "restored"))));
        assertFalse(view.sameLedgerAs(GiftPendingCodec.decodeLedger(ledger(original, "completed"))));
        assertFalse(GiftPendingConsumerAdapter.read(ledger(original, "completed")).spendingBlocked());
        var members = view.ledger().pending().orElseThrow().baseline().sourceFactionMemberCharacterIds();
        assertThrows(UnsupportedOperationException.class, () -> members.add(BigInteger.ONE));
        assertThrows(UnsupportedOperationException.class, () -> view.ledger().resolvedRequestOutcomes().put("x", GiftPendingModel.ResolvedOutcome.APPLIED));
    }
    @Test void missingNullAndEmptyRemainDistinctAtColdBoundary() {
        var missing = GiftColdRecoveryCodec.decodeRecovery("{}".getBytes(StandardCharsets.UTF_8));
        var nil = GiftColdRecoveryCodec.decodeRecovery("{\"post_observation\":null}".getBytes(StandardCharsets.UTF_8));
        var empty = GiftColdRecoveryCodec.decodeRecovery("{\"post_observation\":{}}".getBytes(StandardCharsets.UTF_8));
        assertNotEquals(missing.postObservation(), nil.postObservation()); assertTrue(empty.postObservation().known());
        assertEquals(GiftColdRecovery.Presence.MISSING, empty.postObservation().value().sourceFactionMemberCharacterIds().presence());
        assertThrows(IllegalArgumentException.class, () -> GiftColdRecoveryCodec.decodeRecovery("{\"new_bridge_pid\":1.0}".getBytes(StandardCharsets.UTF_8)));
    }
}

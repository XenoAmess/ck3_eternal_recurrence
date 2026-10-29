package org.xar.ck3.control.wave2.finance.giftpendingreaders;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingCodec;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingConsumerAdapter;
import org.xar.ck3.control.wave2.finance.giftpending.GiftPendingTransitionAdapter;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeCodec;
import org.xar.ck3.control.wave2.finance.giftoutcome.GiftOutcomeQuery;

final class GiftPendingReadersTest {
    @Test void sameActualProducerLedgerFlowsThroughEveryExistingDirectReader() throws IOException {
        com.fasterxml.jackson.databind.JsonNode golden;
        try (var stream = GiftPendingReadersTest.class.getResourceAsStream("/giftpendingreaders/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual complete ledger reader capture required"); }
            golden = StrictJson.parse(stream.readAllBytes());
        }
        byte[] javaProduced = GiftPendingTransitionAdapter.begin(GiftPendingCodec.encodeLedger(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger.empty()),
                StrictJson.canonical(golden.get("begin")));
        assertEquals(golden.get("ledger"), StrictJson.parse(javaProduced));
        var view = GiftPendingConsumerAdapter.read(javaProduced);
        assertTrue(view.spendingBlocked()); assertFalse(view.giftSubmissionEnabled());
        assertEquals("faction_gift_pending", golden.path("feast_budget").path("reason").textValue());
        assertTrue(golden.path("feast_budget").path("budget").isNull());
        var identity = view.recovery().orElseThrow(); var augmented = golden.path("plan_augmentation").path("plan").path("faction_gift_private_candidate_v1");
        assertEquals("pending_recovery_required", augmented.path("status").textValue());
        assertEquals(identity.requestId(), augmented.path("request_id").textValue());
        assertEquals(identity.sourceFactionId(), augmented.path("source_faction_id").bigIntegerValue());
        assertEquals(identity.recipientCharacterId(), augmented.path("recipient_character_id").bigIntegerValue());
        assertEquals("M5 peacetime source has an unresolved faction gift action", golden.path("peacetime_guard").path("error").textValue());
        var collectorPlan = golden.path("formal_collector").path("plan");
        assertEquals("private-query-faction-gift-receipt-v1", collectorPlan.path("selected_step").textValue());
        assertEquals("faction_gift_pending_verification", collectorPlan.path("phase").textValue());
        assertEquals(golden.path("ledger").path("pending"), collectorPlan.path("faction_gift_pending_action"));
        assertEquals(0, golden.path("new_proposal_source_reads").intValue());
        assertEquals(golden.path("ledger_sha256_before"), golden.path("ledger_sha256_after"));
        assertTrue(view.sameLedgerAs(GiftPendingCodec.decodeLedger(javaProduced)));
    }
    @Test void javaPendingProducerAndMaterialRetirementFeedActualResolvedHistoryConsumer() throws IOException {
        com.fasterxml.jackson.databind.JsonNode golden;
        try (var stream = GiftPendingReadersTest.class.getResourceAsStream("/giftpending/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("actual pending producer golden required"); }
            golden = StrictJson.parse(stream.readAllBytes(), 98_304);
        }
        byte[] begun = GiftPendingTransitionAdapter.begin(GiftPendingCodec.encodeLedger(org.xar.ck3.control.wave2.finance.giftpending.GiftPendingModel.Ledger.empty()),
                StrictJson.canonical(golden.get("begin")));
        var pending = GiftPendingCodec.decodeLedger(begun).pending().orElseThrow();
        byte[] completed = GiftPendingTransitionAdapter.complete(begun, pending.requestId(), StrictJson.canonical(golden.get("receipt")));
        assertTrue(GiftPendingCodec.decodeLedger(completed).pending().isEmpty());
        var submit = StrictJson.object(); submit.put("ok", true); submit.put("command", "private-submit-faction-gift-member-v1");
        submit.putObject("result").set("pending_ledger", StrictJson.parse(begun));
        var receipt = StrictJson.object(); receipt.put("ok", true); receipt.put("command", "private-query-faction-gift-receipt-v1");
        receipt.putObject("result").set("receipt", golden.get("receipt"));
        var snapshot = StrictJson.object(); snapshot.put("snapshot_id", "native:415"); snapshot.put("revision", 413); snapshot.put("native_revision", 415);
        snapshot.put("date_raw", pending.baseline().dateRaw()); snapshot.put("episode_run_id", pending.episodeRunId());
        snapshot.put("paused", true); snapshot.put("map_ready", true); snapshot.putNull("active_event"); snapshot.putNull("pending_character_interaction");
        var actor = snapshot.putObject("played_character"); actor.put("character_id", pending.baseline().playerCharacterId()); actor.put("alive", true);
        var original = GiftOutcomeQuery.original(List.of(GiftOutcomeCodec.historyEntry(StrictJson.canonical(submit)).orElseThrow(),
                GiftOutcomeCodec.historyEntry(StrictJson.canonical(receipt)).orElseThrow()), pending.requestId(),
                GiftOutcomeCodec.snapshot(StrictJson.canonical(snapshot))).orElseThrow();
        assertEquals(pending.requestId(), original.requestId()); assertEquals(pending.baseline().playerCharacterId(), original.actorId());
        assertEquals(pending.baseline().sourceFactionId(), original.sourceFactionId()); assertEquals(pending.baseline().recipientCharacterId(), original.recipientId());
        assertEquals(pending.baseline().dateRaw(), original.actionDateRaw().orElseThrow()); assertEquals(pending.baseline().dateRaw(), original.materialDateRaw());
        assertEquals(pending.baseline().goldCostRaw(), original.goldCostRaw().orElseThrow()); assertEquals(pending.baseline().opinionDelta(), original.opinionDelta().orElseThrow());
        assertEquals(pending.baseline().recipientOpinionOfPlayer(), original.preRecipientOpinion().orElseThrow());
        assertEquals(pending.baseline().sourceFactionPowerRaw(), original.preFactionPower().orElseThrow());
        assertEquals(pending.baseline().sourceFactionDiscontentRaw(), original.preFactionDiscontent().orElseThrow());
    }
}

package org.xar.ck3.control.g2.m4;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.common.G2Wire;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4LoanInputProducer;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4OriginalCorpus;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.M4WartimeInputProducer.Outlay;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionCodec;
import org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.Reason;
import org.xar.ck3.control.wave2.planning.warcashprovenance.FinancingGapCodec;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers.CurrentInput;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers.Evaluation;
import org.xar.ck3.control.g2.m4.M4ConstructionConsumers.Stage;
import static org.junit.jupiter.api.Assertions.*;

/** Full copied producer -> real M4 domain -> three consumers -> common-wire persistence chain. */
public final class M4ConstructionIntegrationTest {
    private static final M4Research DOMAIN = new M4Research();

    @Test public void everyOriginalProducerVectorTraversesCommonRequestConsumerAndCheckpoint() throws Exception {
        JsonNode corpus = M4OriginalCorpus.wartime();
        assertEquals(31, corpus.path("cases").size());
        int ordinal = 0;
        for (JsonNode vector : corpus.path("cases")) {
            JsonNode input = vector.get("request");
            String id = "m4-original-" + (++ordinal);
            Evaluation evaluation = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                    () -> current(input, id), id, M4OriginalCorpus.outlay(input));
            assertEquals(vector.get("expected"), StrictJson.parse(evaluation.response().result().bytes()), vector.path("name").textValue());
            assertEquals(vector.get("expected").get("new_spend_allowed").booleanValue(), evaluation.decision().newSpendAllowed());
            Evaluation restored = M4ConstructionCheckpoint.decode(M4ConstructionCheckpoint.encode(evaluation, 262144), 262144);
            assertEquals(Stage.AFTER_NATIVE_QUOTE, restored.stage());
            assertEquals(evaluation.request().requestId(), restored.request().requestId());
            assertEquals(evaluation.request().source(), restored.request().source());
            assertArrayEquals(evaluation.request().payload().bytes(), restored.request().payload().bytes());
            assertArrayEquals(evaluation.response().result().bytes(), restored.response().result().bytes());
            assertEquals(evaluation.decision(), restored.decision());
        }
        assertEquals(31, ordinal);
    }

    @Test public void prequeryZeroQuoteWholeOutlayAndFinalFreshReadUseOneSharedDomain() throws Exception {
        JsonNode ample = named("exact_ample_threshold"), missing = named("market_unavailable");
        AtomicInteger reads = new AtomicInteger(), projections = new AtomicInteger();
        M4ConstructionConsumers.ProjectionPort realDomain = request -> { projections.incrementAndGet(); return DOMAIN.evaluate(request); };
        Evaluation pre = M4ConstructionConsumers.beforeOptionalQuery(realDomain,
                () -> { reads.incrementAndGet(); return current(ample, "pre"); }, "m4-pre", "new_building");
        assertEquals(BigInteger.ZERO, StrictJson.parse(pre.request().payload().bytes()).get("construction_gold_raw").bigIntegerValue());
        assertTrue(pre.decision().newSpendAllowed());
        Evaluation quote = M4ConstructionConsumers.afterNativeQuote(realDomain,
                () -> { reads.incrementAndGet(); return current(ample, "quote"); }, "m4-quote", M4OriginalCorpus.outlay(ample));
        assertEquals(BigInteger.valueOf(23000000), StrictJson.parse(quote.request().payload().bytes()).get("construction_gold_raw").bigIntegerValue());
        assertTrue(quote.decision().newSpendAllowed());
        var refusal = assertThrows(M4ConstructionConsumers.DeferredConstructionException.class,
                () -> M4ConstructionConsumers.requireCurrentBeforeIntent(realDomain,
                        () -> { reads.incrementAndGet(); return current(missing, "fresh-final"); },
                        "m4-final", M4OriginalCorpus.outlay(missing)));
        assertEquals(Stage.BEFORE_EXISTING_INTENT, refusal.evaluation().stage());
        assertEquals(Reason.MARKET, refusal.evaluation().decision().reason().orElseThrow());
        assertEquals(3, reads.get()); assertEquals(3, projections.get());
        // Restoring an earlier observation does not create an API that can pass it as final permission.
        Evaluation old = M4ConstructionCheckpoint.decode(M4ConstructionCheckpoint.encode(quote, 262144), 262144);
        assertTrue(old.decision().newSpendAllowed());
        assertThrows(M4ConstructionConsumers.DeferredConstructionException.class,
                () -> M4ConstructionConsumers.requireCurrentBeforeIntent(realDomain,
                        () -> { reads.incrementAndGet(); return current(missing, "fresh-after-restore"); },
                        "m4-final-after-restore", M4OriginalCorpus.outlay(missing)));
        assertEquals(4, reads.get()); assertEquals(4, projections.get());
    }

    @Test public void existingCommitmentsMissingMarketAndUnknownMercenarySubmissionDeferWithoutFundingOrReplay() throws Exception {
        for (String name : List.of("market_unavailable", "complete_empty_market", "mercenary_pending_unknown",
                "one_raw_unit_below_threshold")) {
            JsonNode input = named(name);
            Evaluation result = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                    () -> current(input, name), "m4-unknown-" + name, M4OriginalCorpus.outlay(input));
            assertFalse(result.decision().newSpendAllowed(), name);
            JsonNode output = StrictJson.parse(result.response().result().bytes());
            assertEquals(BigInteger.ZERO, output.get("future_income_credited_raw").bigIntegerValue());
            assertEquals(BigInteger.ZERO, output.get("loan_or_refund_credited_raw").bigIntegerValue());
            assertTrue(output.get("does_not_open_or_refresh_mercenary_procurement_epoch").booleanValue());
            if (name.equals("mercenary_pending_unknown")) {
                assertEquals(Reason.MERCENARY, result.decision().reason().orElseThrow());
            }
        }
        JsonNode ample = named("exact_ample_threshold");
        Evaluation result = M4ConstructionConsumers.requireCurrentBeforeIntent(DOMAIN::evaluate,
                () -> current(ample, "paid-once"), "m4-paid-once", M4OriginalCorpus.outlay(ample));
        JsonNode output = StrictJson.parse(result.response().result().bytes());
        assertTrue(output.get("paid_contracts_already_reflected_in_current_wallet_not_deducted_twice").booleanValue());
        assertEquals(namedVector("exact_ample_threshold").get("expected").get("required_remaining_gold_raw"), output.get("required_remaining_gold_raw"));
    }

    @Test public void planAndQueryAttachmentPreserveOriginalPendingReceiptAndJsonKinds() throws Exception {
        JsonNode input = named("exact_ample_threshold");
        Evaluation result = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                () -> current(input, "attach"), "m4-attach", M4OriginalCorpus.outlay(input));
        byte[] original = ("{\"selected_step\":\"life-advance\",\"construction_pending_action\":{\"status\":\"action_state_unknown\"},"
                + "\"sdk_extension\":{\"fraction\":1.0,\"explicit_null\":null,\"empty\":[]}}").getBytes(StandardCharsets.UTF_8);
        ProjectionJson plan = ProjectionJson.object(original, 65536);
        var planAttachment = M4ConstructionConsumers.attach(result, plan, 131072);
        var queryAttachment = M4ConstructionConsumers.attach(result, plan, 131072);
        assertArrayEquals(original, planAttachment.originalUtf8());
        assertArrayEquals(planAttachment.enrichedUtf8(), queryAttachment.enrichedUtf8());
        JsonNode before = StrictJson.parse(original), after = StrictJson.parse(planAttachment.enrichedUtf8(), 131072);
        assertEquals(before.get("selected_step"), after.get("selected_step"));
        assertEquals(before.get("construction_pending_action"), after.get("construction_pending_action"));
        assertEquals(before.get("sdk_extension"), after.get("sdk_extension"));
        assertTrue(after.path("sdk_extension").get("fraction").isFloatingPointNumber());
        assertTrue(after.path("sdk_extension").get("explicit_null").isNull());
        assertFalse(after.path("sdk_extension").has("missing"));
        assertEquals(StrictJson.parse(result.response().result().bytes()), after.get(M4ConstructionConsumers.ATTACHMENT_FIELD));
        byte[] copy = planAttachment.originalUtf8(); copy[0] = '[';
        assertArrayEquals(original, planAttachment.originalUtf8());
        assertFalse(before.has(M4ConstructionConsumers.ATTACHMENT_FIELD));
    }

    @Test public void outerWrongRequestSourceAndInnerWrongFrameCannotBeAttachedOrPersisted() throws Exception {
        JsonNode input = named("exact_ample_threshold");
        for (String violation : List.of("request", "source", "inner_frame", "bool", "future_funds")) {
            M4ConstructionConsumers.ProjectionPort malformedBoundary = request -> {
                G2Response response = DOMAIN.evaluate(request);
                if (violation.equals("request")) return new G2Response("different-request", Milestone.M4, response.source(), response.result());
                if (violation.equals("source")) {
                    G2Source old = response.source();
                    return new G2Response(response.requestId(), Milestone.M4,
                            new G2Source(old.machineId(), old.observedAtUtc(), "different-build", old.sourceRef()), response.result());
                }
                ObjectNode body = (ObjectNode) StrictJson.parse(response.result().bytes());
                switch (violation) {
                    case "inner_frame" -> ((ObjectNode) body.get("source_frame")).put("native_revision", true);
                    case "bool" -> body.put("new_spend_allowed", 1);
                    case "future_funds" -> body.put("loan_or_refund_credited_raw", 1);
                    default -> throw new IllegalArgumentException("unexpected violation");
                }
                return new G2Response(response.requestId(), response.milestone(), response.source(),
                        ProjectionJson.value(M4OriginalCorpus.wire(body), WartimeConstructionCodec.MAX_BYTES));
            };
            assertThrows(IllegalArgumentException.class, () -> M4ConstructionConsumers.afterNativeQuote(malformedBoundary,
                    () -> current(input, violation), "m4-malformed-" + violation, M4OriginalCorpus.outlay(input)), violation);
        }
    }

    @Test public void transportUnknownPropagatesOnceWithoutFallbackResponseOrRetry() throws Exception {
        JsonNode input = named("exact_ample_threshold");
        AtomicInteger calls = new AtomicInteger();
        IllegalStateException unknown = new IllegalStateException("transport unknown: no action or retry authority");
        var thrown = assertThrows(IllegalStateException.class, () -> M4ConstructionConsumers.afterNativeQuote(request -> {
            calls.incrementAndGet(); throw unknown;
        }, () -> current(input, "unknown-transport"), "m4-transport-unknown", M4OriginalCorpus.outlay(input)));
        assertSame(unknown, thrown); assertEquals(1, calls.get());
    }

    @Test public void checkpointRejectsWrongVersionMissingFieldAndForgedPrequeryStage() throws Exception {
        JsonNode input = named("exact_ample_threshold");
        Evaluation result = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                () -> current(input, "checkpoint"), "m4-checkpoint", M4OriginalCorpus.outlay(input));
        byte[] good = M4ConstructionCheckpoint.encode(result, 262144);
        ObjectNode version = (ObjectNode) StrictJson.parse(good, 262144); version.put("schema", "xar.ck3.g2.m4.construction-gate-checkpoint/v2");
        assertThrows(IllegalArgumentException.class, () -> M4ConstructionCheckpoint.decode(M4OriginalCorpus.wire(version), 262144));
        ObjectNode missing = (ObjectNode) StrictJson.parse(good, 262144); missing.remove("response_wire_base64");
        assertThrows(IllegalArgumentException.class, () -> M4ConstructionCheckpoint.decode(M4OriginalCorpus.wire(missing), 262144));
        ObjectNode stage = (ObjectNode) StrictJson.parse(good, 262144); stage.put("stage", Stage.BEFORE_OPTIONAL_QUERY.name());
        assertThrows(IllegalArgumentException.class, () -> M4ConstructionCheckpoint.decode(M4OriginalCorpus.wire(stage), 262144));
        assertThrows(IllegalArgumentException.class, () -> M4ConstructionCheckpoint.decode("{} {}".getBytes(StandardCharsets.UTF_8), 262144));
    }

    @Test public void validLargeCopiedContextUsesWholeCheckpointBudgetRatherThanIdentifierTextLimit() throws Exception {
        ObjectNode input = (ObjectNode) named("exact_ample_threshold").deepCopy();
        ((ObjectNode) input.get("snapshot")).put("fixture_extension", "z".repeat(26000));
        Evaluation result = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                () -> current(input, "large-checkpoint"), "m4-large-checkpoint", M4OriginalCorpus.outlay(input));
        assertTrue(G2Wire.encodeRequest(result.request()).length > 24576,
                "wire base64 must exercise more than the ordinary text identifier limit");
        byte[] checkpoint = M4ConstructionCheckpoint.encode(result, 262144);
        Evaluation restored = M4ConstructionCheckpoint.decode(checkpoint, 262144);
        assertArrayEquals(result.request().payload().bytes(), restored.request().payload().bytes());
        assertArrayEquals(result.response().result().bytes(), restored.response().result().bytes());
        assertThrows(IllegalArgumentException.class, () -> M4ConstructionCheckpoint.encode(result, 1024));
    }

    @Test public void originalLoanProducerThroughM4PreservesAllNativeCostsAndZeroSpendableFunds() throws Exception {
        int projected = 0;
        for (var vector : M4OriginalCorpus.loan().vectors()) {
            if (!vector.operation().equals("project") || !vector.expectedKind().equals("result")) continue;
            JsonNode arguments = StrictJson.parse(vector.requestUtf8()).get("arguments");
            ObjectNode frame = StrictJson.object();
            frame.set("played_character_id", arguments.get("expected_played_character_id"));
            frame.set("date_raw", arguments.get("expected_date_raw"));
            frame.set("capture_epoch", arguments.get("expected_capture_epoch"));
            var producer = M4LoanInputProducer.produce(M4OriginalCorpus.wire(arguments.get("value")), M4OriginalCorpus.wire(frame));
            G2Request request = new G2Request("m4-loan-" + (++projected), Milestone.M4,
                    source(producer.utf8(), "loan-" + projected), ProjectionJson.object(producer.utf8(), 131072));
            G2Request restoredRequest = G2Wire.decodeRequest(G2Wire.encodeRequest(request));
            assertArrayEquals(producer.utf8(), restoredRequest.payload().bytes());
            G2Response response = G2Wire.decodeResponse(G2Wire.encodeResponse(DOMAIN.evaluate(restoredRequest)));
            JsonNode output = StrictJson.parse(response.result().bytes(), 131072);
            assertEquals(vector.expected(), output);
            assertEquals(BigInteger.ZERO, output.get("funding_credit_raw").bigIntegerValue());
            assertFalse(output.get("submission_qualified").booleanValue());
            assertFalse(output.get("complete_loan_terms").booleanValue());
            assertFalse(output.get("received_funds_verified").booleanValue());
            assertTrue(output.get("principal_quote_raw").isNull());
            assertTrue(output.get("repayment_total_outlay_raw").isNull());
            assertTrue(output.get("selected_action").isNull());
        }
        assertTrue(projected > 0, "original valid loan producer vectors required; missing is not a skip");
    }

    @Test public void publicRevisionAndNativeRevisionStayDistinctAcrossProducerConsumerAndPersistence() throws Exception {
        ObjectNode input = (ObjectNode) named("exact_ample_threshold").deepCopy();
        ((ObjectNode) input.get("snapshot")).put("revision", 42);
        ((ObjectNode) input.get("market_source_frame")).put("revision", 42);
        Evaluation result = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                () -> current(input, "split-revision"), "m4-split-revision", M4OriginalCorpus.outlay(input));
        assertTrue(result.decision().newSpendAllowed());
        JsonNode frame = StrictJson.parse(result.response().result().bytes()).get("source_frame");
        assertEquals(BigInteger.valueOf(42), frame.get("revision").bigIntegerValue());
        assertEquals(BigInteger.valueOf(3), frame.get("native_revision").bigIntegerValue());
        Evaluation restored = M4ConstructionCheckpoint.decode(M4ConstructionCheckpoint.encode(result, 262144), 262144);
        assertArrayEquals(result.request().payload().bytes(), restored.request().payload().bytes());
        ObjectNode wrongNative = input.deepCopy();
        ((ObjectNode) wrongNative.get("market_source_frame")).put("native_revision", 42);
        Evaluation stale = M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                () -> current(wrongNative, "split-wrong-native"), "m4-split-wrong-native", M4OriginalCorpus.outlay(wrongNative));
        assertFalse(stale.decision().newSpendAllowed(), "public revision cannot qualify the native market frame");
        ObjectNode boolPublic = input.deepCopy(); ((ObjectNode) boolPublic.get("snapshot")).put("revision", true);
        assertThrows(IllegalArgumentException.class, () -> M4ConstructionConsumers.afterNativeQuote(DOMAIN::evaluate,
                () -> current(boolPublic, "boolean-public"), "m4-boolean-public", M4OriginalCorpus.outlay(boolPublic)));
    }

    @Test public void originalFinancingGapConsumerPreservesUnknownRefundAndDebtWithoutSubmissionOrFunding() throws Exception {
        JsonNode base = named("exact_ample_threshold");
        ObjectNode gap = StrictJson.object(); gap.put("schema", FinancingGapCodec.REQUEST_SCHEMA);
        ObjectNode snapshot = base.get("snapshot").deepCopy();
        ((ObjectNode) snapshot.get("played_character_gold")).put("raw", 0);
        gap.set("snapshot", snapshot);
        ObjectNode priority = StrictJson.object();
        priority.putArray("wars").addObject().put("war_id", 100663323).put("primary_player_war", true)
                .put("player_relative_war_score", -87).put("raised_force_deficit", true);
        gap.set("priority", priority); gap.set("root", base.get("root"));
        gap.putObject("construction_ledger").putObject("pending").put("status", "action_state_unknown");
        gap.putArray("bridge_capabilities").add(FinancingGapCodec.CAPABILITY);
        byte[] input = M4OriginalCorpus.wire(gap);
        G2Request request = G2Wire.decodeRequest(G2Wire.encodeRequest(new G2Request("m4-financing-gap", Milestone.M4,
                source(input, "financing-gap"), ProjectionJson.object(input, 65536))));
        G2Response response = G2Wire.decodeResponse(G2Wire.encodeResponse(DOMAIN.evaluate(request)));
        assertTrue(FinancingGapCodec.decodeResult(response.result().bytes()).isPresent());
        JsonNode result = StrictJson.parse(response.result().bytes());
        assertTrue(result.get("cancel_construction").get("refund_quote_raw").isNull());
        assertFalse(result.get("cancel_construction").get("submit_planned").booleanValue());
        assertTrue(result.get("legal_debt").get("principal_quote_raw").isNull());
        assertFalse(result.get("legal_debt").get("current_build_full_terms_verified").booleanValue());
        assertFalse(result.get("legal_debt").get("independently_attributed_received_funds_verified").booleanValue());
        assertFalse(result.get("legal_debt").get("submit_planned").booleanValue());
        assertEquals(BigInteger.ZERO, result.get("unreceived_funding_credited_raw").bigIntegerValue());
        assertTrue(result.get("selected_action").isNull());
        assertTrue(result.get("unknown_submission_must_not_be_replayed").booleanValue());
        assertTrue(result.get("future_funding_receipts_must_keep_same_procurement_epoch").booleanValue());
        assertTrue(result.get("continue_existing_war_action").booleanValue());
        ObjectNode forged = result.deepCopy();
        ((ObjectNode) forged.get("cancel_construction")).put("refund_quote_raw", 0);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decodeResult(M4OriginalCorpus.wire(forged)));
        ObjectNode replay = result.deepCopy(); replay.put("unknown_submission_must_not_be_replayed", false);
        assertThrows(IllegalArgumentException.class, () -> FinancingGapCodec.decodeResult(M4OriginalCorpus.wire(replay)));
    }

    private static JsonNode namedVector(String name) throws Exception { return M4OriginalCorpus.wartimeCase(name); }
    private static JsonNode named(String name) throws Exception { return namedVector(name).get("request"); }
    private static CurrentInput current(JsonNode input, String label) {
        return new CurrentInput(source(M4OriginalCorpus.wire(input), label), M4OriginalCorpus.context(input));
    }
    private static G2Source source(byte[] input, String label) {
        try {
            String sha = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(input));
            return new G2Source("xenoamess-full-tower-eb9d2c1186", "2026-10-22T20:45:06.087062400Z", "1.20.0.4",
                    new ExactRef("fixture://m4/" + label, input.length, sha));
        } catch (java.security.NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
}

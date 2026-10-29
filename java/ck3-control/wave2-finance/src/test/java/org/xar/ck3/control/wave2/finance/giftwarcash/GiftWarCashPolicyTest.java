package org.xar.ck3.control.wave2.finance.giftwarcash;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.BooleanNode;
import com.fasterxml.jackson.databind.node.DecimalNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.databind.node.TextNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Decision;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Presence;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Reason;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashModel.Request;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashObserver.NoStateDirectory;
import org.xar.ck3.control.wave2.finance.giftwarcash.GiftWarCashObserver.StoredInputs;

final class GiftWarCashPolicyTest {
    private static JsonNode golden() throws IOException {
        try (InputStream stream = GiftWarCashPolicyTest.class.getResourceAsStream("/giftwarcash/original-producer-golden.json")) {
            if (stream == null) { throw new IOException("committed original producer golden required; capture is a separate task"); }
            byte[] bytes = stream.readAllBytes();
            if (bytes.length == 0 || bytes.length > 90_000) { throw new IOException("bounded golden artifact required"); }
            return new ObjectMapper(JsonFactory.builder().enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
                    .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
                    .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS).readTree(bytes);
        }
    }
    private static ObjectNode request(String name) throws IOException {
        for (JsonNode vector : golden().get("cases")) {
            if (name.equals(vector.get("name").textValue())) { return ((ObjectNode) vector.get("request")).deepCopy(); }
        }
        throw new IOException("missing producer case " + name);
    }
    private static ObjectNode object(ObjectNode root, String... fields) {
        JsonNode node = root; for (String field : fields) { node = node.get(field); } return (ObjectNode) node;
    }
    private static byte[] bytes(JsonNode node) { return node.toString().getBytes(StandardCharsets.UTF_8); }
    private static Request parsed(String name) throws IOException { return GiftWarCashCodec.decode(bytes(request(name))); }
    private static Decision assess(String name) throws IOException { return GiftWarCashPolicy.assess(parsed(name)); }

    @Test void allThirtyTwoRealProducerCasesMatchAndTypedDecisionRoundTrips() throws IOException {
        JsonNode captured = golden();
        assertEquals("xar.gift-war-cash-original-producer-golden.v1", captured.get("schema").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", captured.get("machine_id").textValue());
        assertEquals(6, captured.get("source_bindings").size()); assertEquals(32, captured.get("cases").size());
        for (JsonNode vector : captured.get("cases")) {
            Decision decision = GiftWarCashPolicy.assess(GiftWarCashCodec.decode(bytes(vector.get("request"))));
            byte[] output = GiftWarCashCodec.encode(decision);
            assertArrayEquals(StrictJson.canonical(vector.get("expected")), output, vector.get("name").textValue());
            assertEquals(decision, GiftWarCashCodec.decodeDecision(output), vector.get("name").textValue());
            assertArrayEquals(output, GiftWarCashCodec.encode(GiftWarCashCodec.decodeDecision(output)));
        }
    }

    @Test void lowerBoundFailureDoesNotInventUnknownCostsOrAskTheCurrentInputPort() throws IOException {
        Request request = parsed("actual4276_floor_failure"); AtomicInteger reads = new AtomicInteger();
        Decision decision = GiftWarCashObserver.observe(request.snapshot(), request.candidate(), request.root(), (snapshot, root) -> {
            reads.incrementAndGet(); throw new AssertionError("floor rejection must precede local ledger/history reads");
        });
        assertEquals(0, reads.get()); assertEquals(Reason.MILITARY_FLOOR, decision.reason());
        assertEquals(new BigInteger("19727866"), decision.treasury().afterGiftRaw()); assertFalse(decision.newGiftSpendingAllowed());
        assertEquals(null, decision.reserve());
    }

    @Test void portReusesOriginalInputsOnceAndPropagatesReaderFailures() throws IOException {
        Request request = parsed("complete_ample_cash"); AtomicInteger reads = new AtomicInteger();
        Decision observed = GiftWarCashObserver.observe(request.snapshot(), request.candidate(), request.root(), (snapshot, root) -> {
            reads.incrementAndGet();
            assertEquals(request.snapshot(), snapshot); assertEquals(request.root(), root);
            return new StoredInputs(request.spending(), request.market(), request.marketSourceFrame(), request.mercenaryPending());
        });
        assertEquals(1, reads.get()); assertEquals(GiftWarCashPolicy.assess(request), observed);
        Decision missingDirectory = GiftWarCashObserver.observe(request.snapshot(), request.candidate(), request.root(),
                (snapshot, root) -> new NoStateDirectory());
        assertEquals(Reason.SPENDING, missingDirectory.reason());
        assertThrows(IllegalStateException.class, () -> GiftWarCashObserver.observe(request.snapshot(), request.candidate(),
                request.root(), (snapshot, root) -> { throw new IllegalStateException("actual reader failure"); }));
        Request peace = parsed("outside_wartime");
        assertTrue(GiftWarCashObserver.observe(peace.snapshot(), peace.candidate(), peace.root(),
                (snapshot, root) -> { throw new AssertionError("peace does not read additional input"); }).newGiftSpendingAllowed());
    }

    @Test void packageComparisonIsInclusiveAndChoosesMaximumQualifiedQuote() throws IOException {
        assertTrue(assess("exact_package_threshold").newGiftSpendingAllowed());
        assertFalse(assess("one_gold_below_package").newGiftSpendingAllowed());
        assertEquals(BigInteger.TEN, assess("tie_chooses_larger_id").reserve().emergencyQuote().companyId());
        Decision largest = assess("maximum_quote_not_cheapest");
        assertEquals(BigInteger.valueOf(11), largest.reserve().emergencyQuote().companyId());
        assertEquals(new BigInteger("40000000"), largest.reserve().emergencyQuote().completeContractGoldRaw());
        assertEquals(2, largest.reserve().qualifiedQuoteCount());
    }

    @Test void uint64SizedMaintenanceIsExactAndNoFutureIncomeOrVictoryIsClaimed() throws IOException {
        Decision decision = assess("maintenance_uint64");
        assertEquals(new BigInteger("332041393326771929070"), decision.reserve().militaryBufferRaw());
        assertEquals(new BigInteger("332041393326806929070"), decision.reserve().requiredRaw());
        assertFalse(decision.newGiftSpendingAllowed());
        JsonNode output = StrictJson.parse(GiftWarCashCodec.encode(decision));
        assertEquals(BigInteger.ZERO, output.get("future_income_or_unreceived_financing_credited_raw").bigIntegerValue());
        assertFalse(output.get("arrival_or_victory_verified").booleanValue());
        assertFalse(output.get("thresholds_are_native_or_user_hard_limits").booleanValue());
    }

    @Test void actualIntegerTokensRejectBooleanFloatAndStringSubstitutes() throws IOException {
        for (JsonNode wrong : List.of(BooleanNode.TRUE, DecimalNode.valueOf(new BigDecimal("100000.0")), TextNode.valueOf("100000"))) {
            ObjectNode input = request("complete_ample_cash"); object(input, "candidate", "choice").set("gold_cost_raw", wrong);
            assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(bytes(input)));
            ObjectNode rate = request("complete_ample_cash");
            object(rate, "root", "player_max_monthly_gold_maintenance_v1", "value").set("scale", wrong);
            assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(bytes(rate)));
            ObjectNode frame = request("complete_ample_cash"); object(frame, "snapshot").set("native_revision", wrong);
            assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(bytes(frame)));
        }
    }

    @Test void wrapperMissingDuplicateFieldsAndUnobservedPendingNeverApprove() throws IOException {
        ObjectNode missing = request("complete_ample_cash"); missing.remove("root");
        assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(bytes(missing)));
        ObjectNode unknown = request("complete_ample_cash"); unknown.put("fallback_allowed", true);
        assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(bytes(unknown)));
        ObjectNode ledger = request("complete_ample_cash"); object(ledger, "mercenary_ledger").remove("pending");
        assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(bytes(ledger)));
        assertEquals(Presence.NULL, parsed("complete_ample_cash").mercenaryPending().value());
        assertEquals(Presence.VALUE, parsed("pending_mercenary_unknown").mercenaryPending().value());
        assertFalse(assess("pending_mercenary_unknown").newGiftSpendingAllowed());
        String original = new String(bytes(request("complete_ample_cash")), StandardCharsets.UTF_8);
        String duplicate = "{\"schema\":\"xar.gift-war-cash-input.v1\"," + original.substring(1);
        assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decode(duplicate.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void sdkExtensionsDoNotInvalidateProjectionButFrameExtrasRemainUnequal() throws IOException {
        ObjectNode input = request("complete_ample_cash"); byte[] baseline = GiftWarCashCodec.assess(bytes(input));
        object(input, "snapshot").put("future_extension_float", new BigDecimal("0.25"));
        object(input, "candidate").put("source_extension", "allowed SDK field");
        assertArrayEquals(baseline, GiftWarCashCodec.assess(bytes(input)));
        object(input, "market_source_frame").put("extra_frame_identity", 1);
        assertEquals(Reason.MARKET, GiftWarCashPolicy.assess(GiftWarCashCodec.decode(bytes(input))).reason());
    }

    @Test void persistedDecisionCannotFlipDeferredSpendOrCreditUnreceivedFinance() throws IOException {
        ObjectNode output = (ObjectNode) StrictJson.parse(GiftWarCashCodec.encode(assess("one_gold_below_package")));
        output.put("new_gift_spending_allowed", true);
        assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decodeDecision(bytes(output)));
        ObjectNode finance = (ObjectNode) StrictJson.parse(GiftWarCashCodec.encode(assess("complete_ample_cash")));
        finance.put("future_income_or_unreceived_financing_credited_raw", 1);
        assertThrows(ContractViolationException.class, () -> GiftWarCashCodec.decodeDecision(bytes(finance)));
    }

    @Test void sharedContextAndNativeQuoteConsumerDoNotNeedASyntheticGift() throws IOException {
        ObjectNode input = request("complete_ample_cash"); Request gift = GiftWarCashCodec.decode(bytes(input));
        input.remove("candidate"); input.put("schema", "xar.native-spending-context.v1");
        GiftWarCashModel.CashContext context = GiftWarCashCodec.decodeCashContext(bytes(input));
        assertEquals(gift.snapshot(), context.snapshot()); assertEquals(gift.root(), context.root());
        assertEquals(gift.market(), context.market()); assertEquals(gift.spending(), context.spending());
        GiftWarCashModel.QuoteRow row = context.market().value().rows().value().getFirst();
        assertTrue(GiftWarCashPolicy.usableEmergencyQuote(row, Set.of()));
        assertFalse(GiftWarCashPolicy.usableEmergencyQuote(row, Set.of(row.spawnProvince().value())));
        GiftWarCashModel.QuoteRow denied = parsed("cannot_afford_quote").market().value().rows().value().getFirst();
        assertFalse(GiftWarCashPolicy.usableEmergencyQuote(denied, Set.of()));
    }
}

package org.xar.ck3.control.wave3.development.wartimeconstructioncash;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave3.development.wartimeconstructioncash.WartimeConstructionModel.*;

final class WartimeConstructionCashTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void originalPolicyWithActualPriorityMatchesEveryFullOutput() throws IOException {
        JsonNode golden = golden();
        boolean referenceV2 = referenceCaptureV2(golden, "xar.wartime-construction-original-producer-golden");
        assertFalse(golden.path("machine_id").asText().isBlank());
        assertFalse(golden.path("observed_at_utc").asText().isBlank());
        assertEquals(10, golden.path("source_bindings").size());
        if (referenceV2) {
            requiresActualHostModule(golden, "original_consumer_regressions", "test_wartime_construction_cash_v1.py");
            assertEquals(2, golden.path("original_consumer_regressions").path("declared_test_names").size());
        } else { assertEquals(2, golden.path("original_consumer_regressions").size()); }
        assertEquals(31, golden.path("cases").size());
        for (JsonNode vector : golden.path("cases")) {
            Input input = WartimeConstructionCodec.decode(bytes(vector.get("request")));
            JsonNode actual = JSON.readTree(WartimeConstructionCodec.encode(WartimeConstructionCash.observe(input)));
            assertEquals(vector.get("expected"), actual, vector.path("name").asText());
        }
    }

    @Test void rawFloatBooleanAndStringCannotBecomeCurrentAmountsOrIdentities() throws IOException {
        String raw = JSON.writeValueAsString(named("exact_ample_threshold").get("request"));
        assertTrue(raw.contains("\"construction_gold_raw\":23000000"));
        for (String token : new String[]{"23000000.0", "true", "\"23000000\""}) {
            byte[] malformed = raw.replace("\"construction_gold_raw\":23000000", "\"construction_gold_raw\":" + token).getBytes(StandardCharsets.UTF_8);
            assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(malformed));
        }
        assertTrue(raw.contains("\"native_revision\":"));
        byte[] floatingSnapshotRevision = raw.replaceFirst("\"native_revision\":([0-9]+)", "\"native_revision\":1.0").getBytes(StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(floatingSnapshotRevision));
        ObjectNode node = named("exact_ample_threshold").get("request").deepCopy();
        ((ObjectNode) node.get("snapshot")).put("native_revision", true);
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(bytes(node)));
        ObjectNode cost = named("exact_ample_threshold").get("request").deepCopy();
        ((ObjectNode) cost.get("market").get("rows").get(0).get("final_terms")).put("resource_scale", 100000.0);
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(bytes(cost)));
    }

    @Test void envelopeCannotSupplyAFakePriorityOrGreenAndRejectsDuplicateTrailingBadUtf8() throws IOException {
        ObjectNode unknown = named("exact_ample_threshold").get("request").deepCopy();
        unknown.put("priority_ready", true);
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(bytes(unknown)));
        ObjectNode missing = named("exact_ample_threshold").get("request").deepCopy(); missing.remove("root");
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(bytes(missing)));
        ObjectNode version = named("exact_ample_threshold").get("request").deepCopy(); version.put("schema", "xar.wartime-construction-cash-input.v2");
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(bytes(version)));
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode("{\"schema\":1,\"schema\":2}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> WartimeConstructionCodec.decode(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test void selectionUsesCurrentSuitableAssessmentOrCheapestAdequateThenConservativeMaximum() throws IOException {
        Decision assessed = observe("current_assessed_suitable_quote");
        assertEquals(SelectionBasis.ASSESSED, assessed.reserve().orElseThrow().basis());
        assertEquals(BigInteger.valueOf(8), assessed.reserve().orElseThrow().selected().companyId().value());
        Decision stale = observe("old_procurement_cannot_override");
        assertEquals(SelectionBasis.CHEAPEST_ADEQUATE, stale.reserve().orElseThrow().basis());
        assertEquals(BigInteger.valueOf(7), stale.reserve().orElseThrow().selected().companyId().value());
        Decision weak = observe("weak_cheap_cannot_replace_adequate");
        assertEquals(BigInteger.valueOf(8), weak.reserve().orElseThrow().selected().companyId().value());
        Decision maximum = observe("equal_price_tie_larger_id");
        assertEquals(SelectionBasis.CONSERVATIVE_MAXIMUM, maximum.reserve().orElseThrow().basis());
        assertEquals(BigInteger.valueOf(9), maximum.reserve().orElseThrow().selected().companyId().value());
        assertEquals(BigInteger.ZERO, observe("zero_company_zero_cost_native_quote").reserve().orElseThrow().selected().companyId().value());
    }

    @Test void prequoteAndFinalSubmissionGuardReadAgainAndDoNotReuseAnEarlierAdmission() throws IOException {
        Input current = input("exact_ample_threshold"), missing = input("market_unavailable");
        AtomicInteger reads = new AtomicInteger();
        Decision before = WartimeConstructionConsumers.observeBeforeOptionalQuery(() -> { reads.incrementAndGet(); return current; });
        assertEquals(BigInteger.ZERO, before.quotedCost().value());
        assertTrue(before.newSpendAllowed());
        Decision quoted = WartimeConstructionConsumers.observeQuotedOutlay(() -> { reads.incrementAndGet(); return current; });
        assertTrue(quoted.newSpendAllowed()); assertEquals(BigInteger.valueOf(23000000), quoted.quotedCost().value());
        WartimeConstructionConsumers.DeferredConstructionException rejected = assertThrows(
                WartimeConstructionConsumers.DeferredConstructionException.class,
                () -> WartimeConstructionConsumers.requireCurrentBeforeIntent(() -> { reads.incrementAndGet(); return missing; }));
        assertEquals(Reason.MARKET, rejected.decision().reason().orElseThrow()); assertEquals(3, reads.get());
    }

    @Test void missingOrEmptyMarketDefersOptionalOutlayAndOnlyNativeObservedWalletFundsIt() throws IOException {
        assertEquals(Reason.MARKET, observe("market_unavailable").reason().orElseThrow());
        assertEquals(Reason.EMPTY_MARKET, observe("complete_empty_market").reason().orElseThrow());
        assertEquals(Reason.NO_USABLE, observe("nonmapping_market_rows_are_not_empty").reason().orElseThrow());
        assertEquals(Reason.MERCENARY, observe("mercenary_pending_unknown").reason().orElseThrow());
        assertFalse(observe("one_raw_unit_below_threshold").newSpendAllowed());
        assertTrue(observe("exact_ample_threshold").newSpendAllowed());
        assertEquals(new BigInteger("1000000000000000000000000000000"), observe("arbitrary_precision_quote_outlay").quotedCost().value());
        for (String name : new String[]{"exact_ample_threshold", "cheapest_adequate_quote", "current_assessed_suitable_quote"}) {
            JsonNode encoded = JSON.readTree(WartimeConstructionCodec.encode(observe(name)));
            assertEquals(BigInteger.ZERO, encoded.path("future_income_credited_raw").bigIntegerValue());
            assertEquals(BigInteger.ZERO, encoded.path("loan_or_refund_credited_raw").bigIntegerValue());
            assertTrue(encoded.path("arrival_eta_days").isNull()); assertTrue(encoded.path("battle_win_probability").isNull());
            assertFalse(encoded.path("quoted_company_arrival_or_combat_usefulness_verified").booleanValue());
            assertTrue(encoded.path("does_not_open_or_refresh_mercenary_procurement_epoch").booleanValue());
            assertTrue(encoded.path("paid_contracts_already_reflected_in_current_wallet_not_deducted_twice").booleanValue());
        }
    }

    private static Decision observe(String name) throws IOException { return WartimeConstructionCash.observe(input(name)); }
    private static Input input(String name) throws IOException { return WartimeConstructionCodec.decode(bytes(named(name).get("request"))); }
    private static JsonNode named(String name) throws IOException {
        for (JsonNode item : golden().path("cases")) if (item.path("name").asText().equals(name)) return item;
        throw new IllegalArgumentException("no original vector " + name);
    }
    private static JsonNode golden() throws IOException {
        InputStream resource = WartimeConstructionCashTest.class.getResourceAsStream("/wartimeconstructioncash/original-producer-golden.json.gz");
        assertNotNull(resource, "actual original producer golden is required; absent is not skipped");
        try (InputStream original = resource; GZIPInputStream gzip = new GZIPInputStream(original)) {
            byte[] raw = gzip.readNBytes(524289); assertTrue(raw.length <= 524288, "bounded golden expansion"); return JSON.readTree(raw);
        }
    }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); } catch (IOException failure) { throw new IllegalStateException(failure); }
    }
    private static boolean referenceCaptureV2(JsonNode root, String baseSchema) {
        String schema = root.path("schema").asText();
        if ((baseSchema + ".v1").equals(schema)) { return false; }
        assertEquals(baseSchema + ".v2", schema, "unsupported reference capture version");
        assertEquals("REFERENCE_ORACLE", root.path("producer_role").asText());
        assertEquals("REQUIRES_UNIFIED_ACTUAL_HOST_FULL_SUITE", root.path("current_consumer_validation").asText());
        return true;
    }

    private static void requiresActualHostModule(JsonNode root, String field, String module) {
        JsonNode evidence = root.path(field);
        assertTrue(evidence.isObject());
        assertEquals("NOT_EXECUTED_REFERENCE_CAPTURE", evidence.path("status").asText());
        assertEquals(1, evidence.path("required_actual_host_modules").size());
        assertEquals(module, evidence.path("required_actual_host_modules").get(0).asText());
        for (String oldCredit : new String[]{"completed", "run", "failures", "errors", "skipped"}) {
            assertFalse(evidence.has(oldCredit), "reference producer cannot claim a current consumer run");
        }
    }

}

package org.xar.ck3.control.wave2.development.constructioneconomy;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.zip.GZIPInputStream;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.wave2.development.constructioneconomy.ConstructionEconomyModel.*;

final class ConstructionEconomyTest {
    private static final ObjectMapper JSON = new ObjectMapper().enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS);

    @Test void originalProducerMatchesOutcomeBudgetAndEveryAssemblyEntryPoint() throws IOException {
        JsonNode fixture = golden();
        assertEquals("xar.construction-economy-original-producer-golden.v1", fixture.path("schema").textValue());
        assertFalse(fixture.path("machine_id").asText().isBlank());
        assertFalse(fixture.path("observed_at_utc").asText().isBlank());
        assertEquals(9, fixture.path("source_bindings").size());
        for (JsonNode source : fixture.path("source_bindings")) assertTrue(source.path("sha256").asText().matches("[0-9a-f]{64}"));
        assertEquals(25, fixture.path("cases").size());
        for (JsonNode vector : fixture.path("cases")) {
            JsonNode request = vector.get("request");
            byte[] actual = switch (vector.path("kind").asText()) {
                case "outcome" -> ConstructionEconomyCodec.encodeOutcome(ConstructionEconomy.classify(
                        ConstructionEconomyCodec.decodeOutcomeRequest(outcomeBytes(request))));
                case "budget" -> {
                    BudgetRequest parsed = ConstructionEconomyCodec.decodeBudgetRequest(budgetBytes(request));
                    yield ConstructionEconomyCodec.encodeBudget(ConstructionEconomy.projectBudget(parsed.cash(), parsed.policy()));
                }
                case "prepare" -> ConstructionEconomyCodec.encodePrepared(ConstructionEconomyAdapters.prepare(
                        receipt(request).candidate(), cash(request), integer(request, "reserve_gold_raw"),
                        integer(request, "existing_commitment_gold_raw"), request.path("horizon_months").intValue()));
                case "completed" -> ConstructionEconomyCodec.encodeCompleted(ConstructionEconomyAdapters.completed(
                        receipt(request), cash(request), request.path("exact_ck3_build").asText()));
                case "query" -> {
                    AtomicInteger calls = new AtomicInteger();
                    QueryOutcome result = ConstructionEconomyAdapters.queryOutcome(revision -> {
                        assertEquals(integer(request, "expected_revision"), revision); calls.incrementAndGet(); return cash(request);
                    }, integer(request, "expected_revision"), receipt(request), integer(request, "reserve_gold_raw"),
                            integer(request, "existing_commitment_gold_raw"), request.path("horizon_months").intValue());
                    assertEquals(vector.path("expected_reader_calls").size(), calls.get());
                    yield ConstructionEconomyCodec.encodeQueryOutcome(result);
                }
                default -> throw new IllegalArgumentException("unknown golden kind");
            };
            assertEquals(vector.get("expected"), JSON.readTree(actual), vector.path("name").asText());
        }
    }

    @Test void originalFormalAndM5ConsumersUseTheSameTypedCashResults() throws IOException {
        JsonNode fixture = golden("original-consumers-golden.json.gz");
        ConstructionCashCaptureContract.validate(fixture);
        assertEquals(12, fixture.path("cases").size());
        for (JsonNode vector : fixture.path("cases")) {
            JsonNode request = vector.get("request");
            byte[] actual;
            if (vector.path("kind").asText().equals("quote")) {
                QuoteCashObservation observation = switch (request.path("observation").asText()) {
                    case "missing" -> new NoCashObservation();
                    case "unavailable" -> new UnavailableCashObservation();
                    case "known" -> new ObservedCash(cash(request), integer(request, "reserve_gold_raw"));
                    default -> throw new IllegalArgumentException("unknown fixture cash observation");
                };
                actual = ConstructionEconomyCodec.encodeQuoteProjection(ConstructionEconomyAdapters.projectQuote(
                        ConstructionEconomyCodec.decodeQuote(bytes(request.get("quote"))), observation,
                        request.path("wartime").booleanValue(), request.path("require_same_frame").booleanValue()));
            } else {
                QueryOutcome observation = query(request);
                actual = ConstructionEconomyCodec.encodeEnrichedPlan(ConstructionEconomyAdapters.enrichM5Plan(
                        ConstructionEconomyCodec.decodePlan(bytes(request.get("baseline"))), observation));
            }
            assertEquals(vector.get("expected"), JSON.readTree(actual), vector.path("name").asText());
        }
    }

    @Test void m5DifferentActionKeepsThePriorReceiptAndOutcome() throws IOException {
        JsonNode vector = golden("original-consumers-golden.json.gz").path("cases").get(10);
        JsonNode request = vector.get("request");
        ObjectNode baseline = request.get("baseline").deepCopy();
        ((ObjectNode) baseline.get("construction_receipt_consumed")).put("action_request_id", "different-action");
        baseline.putObject("construction_economic_outcome").put("kept_prior", true);
        QueryOutcome observation = query(request);
        JsonNode encoded = JSON.readTree(ConstructionEconomyCodec.encodeEnrichedPlan(ConstructionEconomyAdapters.enrichM5Plan(
                ConstructionEconomyCodec.decodePlan(bytes(baseline)), observation)));
        assertEquals(baseline.get("construction_receipt_consumed"), encoded.get("construction_receipt_consumed"));
        assertEquals(baseline.get("construction_economic_outcome"), encoded.get("construction_economic_outcome"));
        assertTrue(encoded.has("construction_cash_outcome"));
    }

    @Test void rawBooleanFloatAndStringTokensCannotBecomeIdsDatesOrAmounts() throws IOException {
        for (String token : new String[]{"true", "1.0", "\"1\""}) {
            for (String key : new String[]{"actor_character_id", "completion_observed_date_raw", "pre_player_monthly_gold_income_raw"}) {
                byte[] raw = ("{\"" + key + "\":" + token + "}").getBytes(StandardCharsets.UTF_8);
                assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeReceipt(raw), key + token);
            }
        }
        ObjectNode request = budgetVector().deepCopy();
        request.put("schema", "xar.ck3.construction-monthly-budget-input.v1");
        String policyRaw = JSON.writeValueAsString(request);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeBudgetRequest(
                policyRaw.replace("\"horizon_months\":4", "\"horizon_months\":1.0").getBytes(StandardCharsets.UTF_8)));
        String cashRaw = JSON.writeValueAsString(request.get("cash"));
        assertTrue(cashRaw.contains("\"raw\":800000"));
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeCash(
                cashRaw.replace("\"raw\":800000", "\"raw\":800000.0").getBytes(StandardCharsets.UTF_8)));
    }

    @Test void strictEnvelopesAndExactBuildNetSemanticsRejectMalformedInputs() throws IOException {
        JsonNode vector = golden().path("cases").get(0).get("request");
        ObjectNode extra = vector.deepCopy(); extra.put("unexpected", true);
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeOutcomeRequest(outcomeBytes(extra)));
        ObjectNode missing = vector.deepCopy(); missing.remove("receipt");
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeOutcomeRequest(outcomeBytes(missing)));
        ObjectNode wrongVersion = vector.deepCopy(); wrongVersion.put("schema", "xar.ck3.construction-economy-input.v2");
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeOutcomeRequest(bytes(wrongVersion)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeReceipt("{\"status\":null,\"status\":\"applied\"}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeReceipt("{} {}".getBytes(StandardCharsets.UTF_8)));
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeReceipt(new byte[]{(byte) 0xc3, 0x28}));
        for (String violation : new String[]{"sha", "net", "marker", "scale"}) {
            ObjectNode c = budgetVector().path("cash").deepCopy();
            switch (violation) {
                case "sha" -> c.put("executable_sha256", "0".repeat(64));
                case "net" -> ((ObjectNode) c.get("player_monthly_net_income")).put("raw", 800000);
                case "marker" -> ((ObjectNode) c.get("monthly_income_semantics")).put("military_expenses_included", false);
                case "scale" -> ((ObjectNode) c.get("current_treasury")).put("scale", 1000);
                default -> throw new IllegalArgumentException("unknown test violation");
            }
            assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyCodec.decodeCash(bytes(c)), violation);
        }
    }

    @Test void aggregateDeltaMayExceedInt64ButNeverGrantsAttributionOrReplay() throws IOException {
        JsonNode vector = named("aggregate_delta_wider_than_i64");
        Outcome result = ConstructionEconomy.classify(ConstructionEconomyCodec.decodeOutcomeRequest(outcomeBytes(vector.get("request"))));
        assertEquals(new BigInteger("18446744073709551615"), result.gross().values().delta().orElseThrow());
        JsonNode encoded = JSON.readTree(ConstructionEconomyCodec.encodeOutcome(result));
        assertFalse(encoded.path("readiness").path("building_attribution_ready").booleanValue());
        assertFalse(encoded.path("readiness").path("net_benefit_ready").booleanValue());
        assertFalse(encoded.path("readiness").path("m5_realized_value_ready").booleanValue());
        assertFalse(encoded.path("formal_action_ready").booleanValue());
        Outcome ack = ConstructionEconomy.classify(ConstructionEconomyCodec.decodeOutcomeRequest(outcomeBytes(named("applied_ack_without_verified_material").get("request"))));
        assertFalse(ack.materialCompleted()); assertEquals(Phase.PENDING, ack.phase());
    }

    @Test void completedAttachmentPreservesExtensibleReceiptAndDefensiveCopies() throws IOException {
        ObjectNode request = named("material_completion_attach").path("request").deepCopy();
        ObjectNode receipt = (ObjectNode) request.get("receipt");
        receipt.putObject("sdk_extension").put("fraction", 1.0).putNull("explicit_null").putArray("empty_rows");
        Receipt parsed = receipt(request);
        byte[] exposed = parsed.original().bytes(); exposed[0] = 0;
        CompletedFields fields = ConstructionEconomyAdapters.completed(parsed, cash(request), "1.20.0.4");
        JsonNode attached = JSON.readTree(ConstructionEconomyCodec.encodeCompleted(fields)).path("receipt");
        assertEquals(receipt.get("sdk_extension"), attached.get("sdk_extension"));
        assertTrue(attached.path("sdk_extension").has("explicit_null"));
        assertFalse(attached.path("sdk_extension").has("missing"));
        assertTrue(attached.path("sdk_extension").get("fraction").isFloatingPointNumber());
        assertFalse(receipt.has("post_cash_v2"));
    }

    @Test void invalidPolicyFailsBeforeReaderAndCurrentBudgetDoesNotRequireIntervalBaseline() throws IOException {
        AtomicInteger calls = new AtomicInteger();
        CashPacket packet = cash(named("single_read_current_zero_new_spend").path("request"));
        assertThrows(IllegalArgumentException.class, () -> ConstructionEconomyAdapters.queryOutcome(revision -> {
            calls.incrementAndGet(); return packet;
        }, BigInteger.valueOf(3), receipt(named("single_read_current_zero_new_spend").path("request")), BigInteger.ZERO, BigInteger.ZERO, 0));
        assertEquals(0, calls.get());
        QueryOutcome query = ConstructionEconomyAdapters.queryOutcome(revision -> { calls.incrementAndGet(); return packet; },
                BigInteger.valueOf(3), receipt(named("single_read_current_zero_new_spend").path("request")), BigInteger.ZERO, BigInteger.ZERO, 1);
        assertEquals(1, calls.get()); assertTrue(query.currentScenarios().current().ready());
        assertFalse(query.completed().outcome().cash().observed());
        assertEquals(Optional.of("pre_submit_cash_v2_unavailable"), query.completed().outcome().cash().unavailableReason());
        assertEquals(BigInteger.ZERO, query.currentScenarios().policy().constructionCost());
    }

    private static JsonNode golden() throws IOException { return golden("original-producer-golden.json.gz"); }
    private static JsonNode golden(String name) throws IOException {
        InputStream resource = ConstructionEconomyTest.class.getResourceAsStream("/constructioneconomy/" + name);
        assertNotNull(resource, "actual original-producer capture is required; absent is not a skip");
        try (InputStream compressed = resource; GZIPInputStream gzip = new GZIPInputStream(compressed)) {
            byte[] raw = gzip.readNBytes(160001); assertTrue(raw.length <= 160000, "bounded golden expansion");
            if ("original-consumers-golden.json.gz".equals(name)) {
                raw = ConstructionCashCaptureContract.decode(raw).bytes();
            }
            return JSON.readTree(raw);
        }
    }
    private static QueryOutcome query(JsonNode request) {
        AtomicInteger calls = new AtomicInteger();
        QueryOutcome result = ConstructionEconomyAdapters.queryOutcome(revision -> { calls.incrementAndGet(); return cash(request); },
                integer(request, "expected_revision"), receipt(request), integer(request, "reserve_gold_raw"),
                integer(request, "existing_commitment_gold_raw"), request.path("horizon_months").intValue());
        assertEquals(1, calls.get()); return result;
    }
    private static JsonNode named(String name) throws IOException {
        for (JsonNode vector : golden().path("cases")) if (vector.path("name").asText().equals(name)) return vector;
        throw new IllegalArgumentException("golden not found: " + name);
    }
    private static JsonNode budgetVector() throws IOException { return named("negative_net_raised_once").get("request"); }
    private static Receipt receipt(JsonNode request) { return ConstructionEconomyCodec.decodeReceipt(bytes(request.get("receipt"))); }
    private static CashPacket cash(JsonNode request) { return ConstructionEconomyCodec.decodeCash(bytes(request.get("cash"))); }
    private static BigInteger integer(JsonNode request, String key) { return request.get(key).bigIntegerValue(); }
    private static byte[] outcomeBytes(JsonNode request) {
        ObjectNode wire = request.deepCopy(); wire.put("schema", "xar.ck3.construction-economy-input.v1"); return bytes(wire);
    }
    private static byte[] budgetBytes(JsonNode request) {
        ObjectNode wire = request.deepCopy(); wire.put("schema", "xar.ck3.construction-monthly-budget-input.v1"); return bytes(wire);
    }
    private static byte[] bytes(JsonNode value) {
        try { return JSON.writeValueAsBytes(value); } catch (IOException failure) { throw new IllegalStateException(failure); }
    }
}

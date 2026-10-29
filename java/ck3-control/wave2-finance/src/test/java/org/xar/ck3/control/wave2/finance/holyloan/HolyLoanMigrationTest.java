package org.xar.ck3.control.wave2.finance.holyloan;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.zip.GZIPInputStream;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ExpectedFrame;
import org.xar.ck3.control.wave2.finance.holyloan.HolyLoanModel.ObservedDecision;
import org.xar.ck3.control.wave2.finance.rawcash.RawCashCodec;

final class HolyLoanMigrationTest {
    @Test void captureRefusesRepositoryScratchAndOutputBeforeStartingOriginalProducer() {
        Path repository = Path.of(".").toAbsolutePath().normalize();
        String[] arguments = {repository.toString(), "must-not-start", "synthetic-fixture-machine",
                repository.resolve("forbidden-capture-scratch").toString(),
                repository.resolve("forbidden-golden.jsonl.gz").toString()};
        assertThrows(IllegalArgumentException.class, () -> HolyLoanCapture.main(arguments));
    }
    private record Vector(String kind, byte[] request, JsonNode expected) { }
    private record Corpus(JsonNode header, List<Vector> vectors) { }
    private static Corpus corpus() throws Exception {
        var source = HolyLoanMigrationTest.class.getResourceAsStream("/holyloan/original-v1.jsonl.gz");
        assertNotNull(source, "Original producer capture is required; missing environment/corpus is not PASS");
        try (var reader = new BufferedReader(new InputStreamReader(new GZIPInputStream(source), StandardCharsets.UTF_8))) {
            String headerLine = reader.readLine(); assertNotNull(headerLine); JsonNode header = StrictJson.parse(headerLine.getBytes(StandardCharsets.UTF_8));
            assertEquals("xar.holyloan-rawcash-original-golden.v1", header.path("schema").asText());
            assertFalse(header.path("machine_id").asText().isBlank()); assertNotNull(header.get("observed_at_utc"));
            assertTrue(header.path("source_sha256").size() >= 15); assertEquals(0, header.path("skips").intValue());
            List<Vector> vectors = new ArrayList<>(); String metadata;
            while ((metadata = reader.readLine()) != null) {
                JsonNode meta = StrictJson.parse(metadata.getBytes(StandardCharsets.UTF_8)); String request = reader.readLine(), expected = reader.readLine();
                assertNotNull(request); assertNotNull(expected); assertEquals(vectors.size() + 1, meta.path("ordinal").intValue());
                vectors.add(new Vector(meta.path("expected_kind").asText(), request.getBytes(StandardCharsets.UTF_8), StrictJson.parse(expected.getBytes(StandardCharsets.UTF_8))));
                assertTrue(vectors.size() <= 1000, "bounded committed corpus");
            }
            assertEquals(header.path("vector_count").intValue(), vectors.size()); return new Corpus(header, List.copyOf(vectors));
        }
    }
    @Test void replaysEveryOriginalProducerVectorAndAllCapturedConsumerPaths() throws Exception {
        Corpus corpus = corpus(); Set<String> operations = new HashSet<>();
        for (Vector vector : corpus.vectors()) {
            operations.add(StrictJson.parse(vector.request()).path("operation").asText());
            if (vector.kind().equals("invalid_contract")) { assertThrows(IllegalArgumentException.class, () -> HolyLoanHarness.evaluate(vector.request())); }
            else { assertEquals(vector.expected(), StrictJson.parse(HolyLoanHarness.evaluate(vector.request())), new String(vector.request(), StandardCharsets.UTF_8)); }
        }
        assertEquals(Set.of("project", "normalize", "monthly", "financing"), operations);
        assertTrue(corpus.header().path("passed").intValue() > 100);
    }
    @Test void projectedOutputsRoundTripAndNeverSupplyMoneyOrSubmissionAuthority() throws Exception {
        for (Vector vector : corpus().vectors()) {
            JsonNode request = StrictJson.parse(vector.request());
            if (!vector.kind().equals("result") || !request.path("operation").asText().equals("project")) { continue; }
            byte[] output = HolyLoanHarness.evaluate(vector.request());
            assertEquals(StrictJson.parse(output), StrictJson.parse(HolyLoanCodec.encode(HolyLoanCodec.decodeObservation(output))));
            JsonNode parsed = StrictJson.parse(output); assertFalse(parsed.get("submission_qualified").booleanValue());
            assertFalse(parsed.get("received_funds_verified").booleanValue()); assertFalse(parsed.get("complete_loan_terms").booleanValue());
            assertEquals(0, parsed.get("funding_credit_raw").intValue()); assertTrue(parsed.get("principal_quote_raw").isNull());
        }
    }
    @Test void nativeIntegerTokensRejectRawFloatBooleanAndStringBeforeModelConstruction() throws Exception {
        ObjectNode request = firstRequest("project"); JsonNode args = request.get("arguments");
        ExpectedFrame frame = expected(args); String original = new String(HolyLoanHarness.wire(args.get("value")), StandardCharsets.UTF_8);
        for (String token : List.of("true", "123.0", "\"123\"")) {
            String changed = original.replaceFirst("\"capture_epoch\":123", "\"capture_epoch\":" + token);
            assertFalse(changed.equals(original));
            assertThrows(IllegalArgumentException.class, () -> HolyLoanCodec.project(changed.getBytes(StandardCharsets.UTF_8), frame));
        }
        String raw = original.replaceFirst("\"raw_scale\":100000", "\"raw_scale\":100000.0");
        assertThrows(IllegalArgumentException.class, () -> HolyLoanCodec.project(raw.getBytes(StandardCharsets.UTF_8), frame));
    }
    @Test void fullUnsignedCaptureAndSignedCostBoundariesSurviveSerialization() throws Exception {
        ObjectNode request = firstRequest("project"), args = (ObjectNode) request.get("arguments"), nativeValue = (ObjectNode) args.get("value");
        nativeValue.put("capture_epoch", HolyLoanModel.UINT64_MAX); args.put("expected_capture_epoch", HolyLoanModel.UINT64_MAX);
        ObjectNode borrow = (ObjectNode) nativeValue.get("borrow_decision"); var costs = borrow.putArray("costs_raw_by_native_index");
        costs.add(Long.MIN_VALUE); costs.add(Long.MAX_VALUE); for (int index = 2; index < 10; index++) { costs.add(0); }
        var result = HolyLoanCodec.project(HolyLoanHarness.wire(nativeValue), expected(args));
        assertEquals(HolyLoanModel.UINT64_MAX, result.source().captureEpoch());
        assertEquals(List.of(Long.MIN_VALUE, Long.MAX_VALUE), ((ObservedDecision) result.borrowDecision()).declaredCostsRaw().subList(0, 2));
        assertThrows(UnsupportedOperationException.class, () -> ((ObservedDecision) result.borrowDecision()).declaredCostsRaw().add(1L));
        assertEquals(result, HolyLoanCodec.decodeObservation(HolyLoanCodec.encode(result)));
    }
    @Test void sdkExtensionsRemainPermittedWhileRawContextLeafRequiresExactFields() throws Exception {
        ObjectNode request = firstRequest("normalize"), args = (ObjectNode) request.get("arguments"), value = (ObjectNode) args.get("value");
        value.put("unrelated_sdk_extension", "retained");
        var normalized = RawCashCodec.normalize(HolyLoanHarness.wire(value), HolyLoanHarness.wire(args.get("snapshot")));
        assertEquals("retained", StrictJson.parse(normalized.toJson()).path("unrelated_sdk_extension").asText());
        byte[] copy = normalized.toJson(); copy[0] = 'X'; assertEquals((byte) '{', normalized.toJson()[0]);
        assertThrows(UnsupportedOperationException.class, () -> normalized.activeWarIds().clear());
    }
    @Test void serializedProjectionCannotManufacturePrincipalDebtOrReceivedFunds() throws Exception {
        JsonNode projected = StrictJson.parse(HolyLoanHarness.evaluate(HolyLoanHarness.wire(firstRequest("project"))));
        for (String field : List.of("principal_quote_raw", "existing_debt_principal_raw", "repayment_total_outlay_raw", "funding_credit_raw")) {
            ObjectNode changed = ((ObjectNode) projected).deepCopy(); changed.put(field, 1);
            assertThrows(IllegalArgumentException.class, () -> HolyLoanCodec.decodeObservation(HolyLoanHarness.wire(changed)));
        }
    }
    @Test void rawFloatCostSurvivesSdkSubtreeHandoffAndOnlyDiscardsLoanCostChild() throws Exception {
        ObjectNode request = null;
        for (Vector vector : corpus().vectors()) {
            JsonNode value = StrictJson.parse(vector.request());
            if (vector.kind().equals("result") && value.path("operation").asText().equals("normalize")
                    && vector.expected().path(RawCashCodec.LOAN_KEY).path("status").asText().equals("available")
                    && vector.expected().path(RawCashCodec.LOAN_KEY).path("principal_quote_raw").isIntegralNumber()) {
                request = ((ObjectNode) value).deepCopy(); break;
            }
        }
        assertNotNull(request); JsonNode arguments = request.get("arguments");
        String current = new String(HolyLoanHarness.wire(arguments.get("value")), StandardCharsets.UTF_8);
        String changed = current.replaceFirst("\"costs_raw_by_native_index\":\\[-5", "\"costs_raw_by_native_index\":[1.0");
        assertFalse(current.equals(changed));
        var normalized = RawCashCodec.normalize(changed.getBytes(StandardCharsets.UTF_8), HolyLoanHarness.wire(arguments.get("snapshot")));
        JsonNode loan = StrictJson.parse(normalized.toJson()).get(RawCashCodec.LOAN_KEY);
        assertEquals("partial", loan.path("status").asText()); assertEquals(0, loan.path("principal_quote_raw").longValue());
        assertTrue(loan.get("decision_observation").isNull()); assertTrue(loan.get("borrow_eligible").isNull());
        assertEquals("loan_decision_child_malformed_or_mismatched", loan.path("decision_costs_unavailable_reason").asText());
        assertEquals(RawCashCodec.BorrowEligibility.UNKNOWN, normalized.loanObservation().value().borrowEligibility());
        assertFalse(normalized.loanObservation().value().receivedFundsVerified());
    }
    private static ExpectedFrame expected(JsonNode arguments) {
        return new ExpectedFrame(arguments.get("expected_played_character_id").intValue(), arguments.get("expected_date_raw").intValue(),
                arguments.get("expected_capture_epoch").bigIntegerValue());
    }
    private static ObjectNode firstRequest(String operation) throws Exception {
        for (Vector vector : corpus().vectors()) {
            JsonNode node = StrictJson.parse(vector.request());
            if (vector.kind().equals("result") && operation.equals(node.path("operation").asText())) { return ((ObjectNode) node).deepCopy(); }
        }
        throw new IllegalStateException("required original vector absent: " + operation);
    }
}

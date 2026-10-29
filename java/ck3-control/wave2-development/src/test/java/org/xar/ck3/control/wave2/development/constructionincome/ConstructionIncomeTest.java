package org.xar.ck3.control.wave2.development.constructionincome;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

class ConstructionIncomeTest {
    @Test
    void originalObserverAndActualReceiptCarryStatementsMatchAllVectors() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.ck3.constructionincome-golden/v1", golden.path("schema").textValue());
        assertEquals("xenoamess-full-tower-eb9d2c1186", golden.path("machine_id").textValue());
        assertEquals(22, golden.path("cases").size());
        assertEquals("90ff70251640abd243bea7a0194f057ab80b719899569e4ca3feaf53c29b9e3e",
                golden.path("source_refs").get(0).path("sha256").textValue());
        assertEquals("c36fd21d16b897304c08cd8f0a9b9d26b19178c2fbeb3e1fbcc7a4f0d456dd2e",
                golden.path("source_refs").get(1).path("sha256").textValue());
        assertEquals(998, golden.path("receipt_segment_first_line").intValue());
        assertEquals(1008, golden.path("receipt_segment_last_line").intValue());
        for (JsonNode row : golden.path("cases")) {
            JsonNode actual = StrictJson.parse(ConstructionIncomeJson.project(request(row)));
            assertEquals(row.get("expected"), actual, row.path("name").textValue());
            assertEquals(actual, StrictJson.parse(StrictJson.canonical(actual)), "tuple/list JSON roundtrip");
        }
    }

    @Test
    void sampleTakenBeforeMaterialQueryDoesNotObserveLaterHistoryRows() throws IOException {
        JsonNode row = named("latest-matching-root-wins");
        var frame = ConstructionIncomeJson.frame(row.get("snapshot"));
        var rows = new ArrayList<>(ConstructionIncomeJson.history(row.get("history")));
        var sample = ConstructionIncomeConsumers.sampleStarting(frame, rows);
        assertEquals(BigInteger.valueOf(2), ConstructionIncomeConsumers.preSubmitIncome(sample));
        rows.clear();
        rows.add(new SameFrameConstructionIncome.HistoryRow(SameFrameConstructionIncome.ROOT_QUERY_STEP,
                org.xar.ck3.control.wave2.development.constructionintent.ConstructionIntentContinuity.Evidence.TRUE,
                new SameFrameConstructionIncome.RootContext("available", frame,
                        new SameFrameConstructionIncome.Income(BigInteger.valueOf(9), SameFrameConstructionIncome.INCOME_SCALE))));
        assertEquals(BigInteger.valueOf(9), SameFrameConstructionIncome.observe(frame, rows).incomeRaw());
        var prior = new ConstructionIncomeConsumers.PriorReceipt("completed", BigInteger.valueOf(99),
                new ConstructionIncomeConsumers.PriorObservedDate(false, null), BigInteger.ONE);
        var receipt = ConstructionIncomeConsumers.receiptIncome(sample, prior, true, true);
        assertEquals(BigInteger.valueOf(2), receipt.observedIncomeRaw());
        assertEquals(frame.dateRaw(), receipt.incomeObservedDateRaw());
    }

    @Test
    void latestMatchingUnknownIncomeIsObservedWithoutFallbackToEarlierIncome() throws IOException {
        JsonNode output = StrictJson.parse(ConstructionIncomeJson.project(request(named("latest-invalid-scale-does-not-fall-back"))));
        assertTrue(output.get(0).booleanValue());
        assertTrue(output.get(1).isNull());
        JsonNode absent = StrictJson.parse(ConstructionIncomeJson.project(request(named("empty-history"))));
        assertFalse(absent.get(0).booleanValue());
        assertTrue(absent.get(1).isNull());
    }

    @Test
    void strictOriginalRawTokensRejectFloatBoolAndStringIntegerSubstitutes() throws IOException {
        String base = new String(request(named("zero-income-is-observed")), StandardCharsets.UTF_8);
        for (String token : new String[]{"0.0", "true", "\"0\""}) {
            String changed = base.replace("\"raw\":0", "\"raw\":" + token);
            assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(changed)), token);
        }
        assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(
                base.replace("\"scale\":100000", "\"scale\":100000.0"))));
        assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(
                base.replace("\"ok\":true", "\"ok\":1"))));
        assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(
                base.replace("\"native_revision\":2", "\"native_revision\":true"))));
    }

    @Test
    void unrelatedCommandPayloadsRemainOpaqueWhileNewWrapperIsExact() throws IOException {
        String base = new String(request(named("unrelated-payload-is-opaque")), StandardCharsets.UTF_8);
        String extended = base.replace("\"opaque unused extension\"", "{\"sdk_float\":1.25,\"sdk_null\":null,\"sdk_empty\":[]}");
        assertEquals(StrictJson.parse(ConstructionIncomeJson.project(utf8(base))),
                StrictJson.parse(ConstructionIncomeJson.project(utf8(extended))));
        assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(base + " []")));
        assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(
                base.replaceFirst("\\{", "{\"unexpected\":true,"))));
        assertThrows(ContractViolationException.class, () -> ConstructionIncomeJson.project(utf8(
                base.replaceFirst("\\{", "{\"operation\":\"observe\","))));
        ObjectNode missing = (ObjectNode) StrictJson.parse(utf8(base));
        missing.remove("history");
        assertThrows(ContractViolationException.class,
                () -> ConstructionIncomeJson.project(StrictJson.canonical(missing)));
        assertThrows(ContractViolationException.class,
                () -> ConstructionIncomeJson.project(new byte[]{(byte) 0xc3, 0x28}));
    }

    @Test
    void exactLegacyIncomeIntRoundtripDoesNotUseFloatingPointOrLong() throws IOException {
        String raw = new String(request(named("zero-income-is-observed")), StandardCharsets.UTF_8)
                .replace("\"raw\":0", "\"raw\":18446744073709551616");
        JsonNode output = StrictJson.parse(ConstructionIncomeJson.project(utf8(raw)));
        assertTrue(output.get(0).booleanValue());
        assertEquals(new BigInteger("18446744073709551616"), output.get(1).bigIntegerValue());
        var history = ConstructionIncomeJson.history(named("zero-income-is-observed").get("history"));
        assertThrows(UnsupportedOperationException.class, history::clear);
    }

    private static byte[] request(JsonNode row) {
        ObjectNode request = (ObjectNode) row.deepCopy();
        request.remove("name");
        request.remove("expected");
        request.put("schema", ConstructionIncomeJson.SCHEMA);
        return StrictJson.canonical(request);
    }
    private static JsonNode named(String name) throws IOException {
        for (JsonNode row : golden().path("cases")) {
            if (name.equals(row.path("name").textValue())) { return row; }
        }
        throw new IllegalStateException("missing income golden: " + name);
    }
    private static JsonNode golden() throws IOException {
        try (InputStream stream = ConstructionIncomeTest.class.getResourceAsStream("/constructionincome/golden.json")) {
            assertNotNull(stream, "original observer/consumer capture is required");
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static byte[] utf8(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

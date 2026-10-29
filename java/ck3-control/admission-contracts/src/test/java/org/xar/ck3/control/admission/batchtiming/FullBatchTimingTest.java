package org.xar.ck3.control.admission.batchtiming;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class FullBatchTimingTest {
    private static final ObjectMapper WRITER = new ObjectMapper();
    private static final BigInteger CONTROL = BigInteger.valueOf(100);

    @Test void matchesAllCommittedActualProducerCasesAndRoundTrips() throws IOException {
        JsonNode golden = golden();
        assertEquals("xar.java.batch-timing-producer-golden/v1", golden.get("schema").textValue());
        assertEquals(17, golden.get("cases").size());
        for (JsonNode entry : golden.get("cases")) {
            FullBatchTimingCodec.Input input = FullBatchTimingCodec.decodeInput(raw(entry.get("input")));
            FullBatchTiming.Summary summary = FullBatchTimingCodec.evaluate(input);
            assertNumericJson(entry.get("expected_summary"), FullBatchTimingCodec.summaryNode(summary), entry.get("name").asText());
            assertEquals(summary, FullBatchTimingCodec.decodeSummary(FullBatchTimingCodec.encodeSummary(summary)));
            FullBatchTiming.Wall wall = FullBatchTimingCodec.decodeWall(entry.get("wall"));
            assertEquals(wall, FullBatchTimingCodec.decodeWall(FullBatchTimingCodec.encodeWall(wall)));
            assertNumericJson(entry.get("expected_combined"),
                    FullBatchTimingCodec.combinedNode(FullBatchTiming.combine(summary, wall)), entry.get("name").asText());
        }
    }

    @Test void lifecycleMatchesProducerSingleConsumptionFailureAndFollowCases() throws IOException {
        JsonNode cases = golden().get("lifecycle_cases");
        assertEquals(6, cases.size());
        for (JsonNode entry : cases) {
            FullLifecycleTiming timer = new FullLifecycleTiming(entry.get("enabled").booleanValue());
            List<JsonNode> actual = new ArrayList<>();
            for (JsonNode event : entry.get("events")) {
                String operation = event.get(0).textValue();
                if (operation.equals("discard")) { timer.discard(); continue; }
                BigInteger sequence = event.get(1).bigIntegerValue();
                BigInteger timestamp = event.get(2).isNull() ? null : event.get(2).bigIntegerValue();
                if (operation.equals("before")) { timer.beforePublish(sequence, timestamp); }
                else {
                    Optional<FullBatchTiming.Wall> wall = timer.afterReceipt(sequence, timestamp);
                    actual.add(wall.isPresent() ? FullBatchTimingCodec.wallNode(wall.orElseThrow()) : StrictJson.object());
                }
            }
            assertEquals(entry.get("expected").size(), actual.size());
            for (int index = 0; index < actual.size(); index++) {
                assertNumericJson(entry.get("expected").get(index), actual.get(index), entry.get("name").asText());
            }
        }
    }

    @Test void rejectsBooleanFloatingStringAndMissingSequences() throws IOException {
        ObjectNode valid = (ObjectNode) golden().get("cases").get(1).get("input");
        for (String value : List.of("true", "100.0", "\"100\"", "null", "0", "-1")) {
            ObjectNode copy = valid.deepCopy();
            copy.set("control_sequence", StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(raw(copy)));
            ObjectNode nested = valid.deepCopy();
            ((ObjectNode) nested.get("observations").get(0).get("request")).set("sequence",
                    StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(raw(nested)));
        }
        ObjectNode missing = valid.deepCopy();
        missing.remove("control_sequence");
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(raw(missing)));
    }

    @Test void rejectsWrongTypesMissingNullableFieldsAndUnknownFields() throws IOException {
        ObjectNode valid = (ObjectNode) golden().get("cases").get(1).get("input");
        for (String field : List.of("elapsed_seconds", "monotonic_start_seconds", "result_is_error", "client_error_present")) {
            ObjectNode copy = valid.deepCopy();
            ((ObjectNode) copy.get("observations").get(0)).remove(field);
            assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(raw(copy)));
        }
        for (String value : List.of("true", "\"1.0\"", "[]", "{}")) {
            ObjectNode copy = valid.deepCopy();
            ((ObjectNode) copy.get("observations").get(0)).set("elapsed_seconds",
                    StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(raw(copy)));
        }
        ObjectNode unknown = valid.deepCopy(); unknown.put("budget_reserve", 0);
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(raw(unknown)));
        String duplicate = "{\"control_sequence\":100,\"control_sequence\":101,\"observations\":[]}";
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeInput(duplicate.getBytes(StandardCharsets.UTF_8)));
    }

    @Test void rejectsUtcAsMonotonicAndForgedNullableOrCounterTotals() throws IOException {
        JsonNode entry = golden().get("cases").get(1);
        for (String value : List.of("\"2026-10-22T00:00:00Z\"", "true", "1.0", "\"1\"")) {
            ObjectNode wall = entry.get("wall").deepCopy();
            wall.set("full_submit_monotonic_ns", StrictJson.parse(value.getBytes(StandardCharsets.UTF_8)));
            assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeWall(wall));
        }
        ObjectNode wall = entry.get("wall").deepCopy(); wall.put("full_timing_clock", "UTC");
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeWall(wall));
        ObjectNode partial = entry.get("wall").deepCopy(); partial.putNull("full_wall_ns");
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeWall(partial));
        ObjectNode summary = entry.get("expected_summary").deepCopy(); summary.put("row_count", 5);
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeSummary(summary));
        ObjectNode cpu = entry.get("expected_summary").deepCopy(); cpu.put("CPU_attribution", "Python");
        assertThrows(ContractViolationException.class, () -> FullBatchTimingCodec.decodeSummary(cpu));
    }

    @Test void intervalFragmentLimitKeepsAllRowsAndUnknownUnion() {
        FullBatchTiming.Accumulator accumulator = new FullBatchTiming.Accumulator(CONTROL);
        for (int index = 0; index < FullBatchTiming.INTERVAL_LIMIT + 1; index++) {
            FullBatchTiming.Request request = new FullBatchTiming.Request(BigInteger.valueOf(index + 1L),
                    "ck3_auto_turn", StrictJson.object());
            accumulator.record(new FullBatchTiming.Observation(request, request, 1.0, index * 2.0, false, false));
        }
        FullBatchTiming.Summary summary = accumulator.summary();
        assertEquals(2_049, summary.rowCount());
        assertEquals(2_049.0, summary.elapsedSecondsSum());
        assertNull(summary.intervalUnionSeconds());
        assertNull(summary.overlapSeconds());
    }

    @Test void failedElapsedCannotBecomeZeroAndDuplicateCannotRetry() {
        FullBatchTiming.Accumulator accumulator = new FullBatchTiming.Accumulator(CONTROL);
        FullBatchTiming.Request request = new FullBatchTiming.Request(BigInteger.valueOf(101),
                "ck3_auto_turn", StrictJson.object());
        accumulator.record(new FullBatchTiming.Observation(request, request, Double.NaN, 1.0, true, true));
        accumulator.record(new FullBatchTiming.Observation(request, request, 10.0, 1.0, false, false));
        FullBatchTiming.Summary summary = accumulator.summary();
        assertEquals(1, summary.rowCount()); assertEquals(1, summary.duplicateRowsIgnored());
        assertEquals(1, summary.invalidElapsedRows()); assertNull(summary.intervalUnionSeconds());
        assertEquals(1, summary.tools().get(FullBatchTiming.Tool.AUTO).errorCount());
        assertEquals(0.0, summary.elapsedSecondsSum());
    }

    @Test void followingCannotObserveNewOriginOrAttachAnotherFullSummary() {
        FullLifecycleTiming timer = new FullLifecycleTiming(true);
        timer.beforePublish(CONTROL, BigInteger.ONE);
        FullBatchTiming.Wall wrong = timer.afterReceipt(BigInteger.valueOf(200), BigInteger.TEN).orElseThrow();
        assertEquals(FullBatchTiming.Origin.SUBMISSION_NOT_OBSERVED, wrong.origin());
        assertNull(timer.afterReceipt(CONTROL, BigInteger.TEN).orElseThrow().wallNs());
        FullBatchTiming.Summary summary = new FullBatchTiming.Accumulator(CONTROL).summary();
        FullBatchTiming.Combined combined = FullBatchTiming.combine(summary, wrong);
        assertFalse(combined.summary().isPresent());
        assertFalse(FullBatchTimingCodec.combinedNode(combined).has("full_rpc_rows_v1"));
        assertTrue(FullBatchTimingCodec.summaryNode(summary).get("zero_day_rows_included").booleanValue());
        assertNull(FullBatchTimingCodec.summaryNode(summary).get("CPU_attribution").textValue());
    }

    @Test void malformedOptionalSummaryKeepsValidatedWallWithoutBlockingBusiness() {
        FullBatchTiming.Wall wall = FullBatchTiming.Wall.unobserved(CONTROL);
        for (String invalid : List.of("{}", "[]", "null", "{\"CPU_attribution\":\"Python\"}", "{broken")) {
            FullBatchTiming.Combined result = FullBatchTimingCodec.composeOptionalSummary(
                    invalid.getBytes(StandardCharsets.UTF_8), wall);
            assertEquals(wall, result.wall());
            assertTrue(result.summary().isEmpty());
            assertNumericJson(FullBatchTimingCodec.wallNode(wall), FullBatchTimingCodec.combinedNode(result), invalid);
        }
    }

    private static JsonNode golden() throws IOException {
        try (InputStream stream = FullBatchTimingTest.class.getResourceAsStream("/batchtiming/producer-golden.json")) {
            if (stream == null) { throw new IOException("required committed producer golden missing; no skip"); }
            return StrictJson.parse(stream.readAllBytes());
        }
    }
    private static byte[] raw(JsonNode value) throws IOException { return WRITER.writeValueAsBytes(value); }
    private static void assertNumericJson(JsonNode expected, JsonNode actual, String context) {
        if (expected.isNumber() && actual.isNumber()) {
            if (expected.isIntegralNumber() && actual.isIntegralNumber()) {
                assertEquals(expected.bigIntegerValue(), actual.bigIntegerValue(), context);
            } else { assertEquals(expected.doubleValue(), actual.doubleValue(), context); }
        } else if (expected.isObject() && actual.isObject()) {
            assertEquals(expected.size(), actual.size(), context);
            expected.properties().forEach(field -> {
                assertTrue(actual.has(field.getKey()), context + ": " + field.getKey());
                assertNumericJson(field.getValue(), actual.get(field.getKey()), context + "/" + field.getKey());
            });
        } else if (expected.isArray() && actual.isArray()) {
            assertEquals(expected.size(), actual.size(), context);
            for (int index = 0; index < expected.size(); index++) {
                assertNumericJson(expected.get(index), actual.get(index), context + "/" + index);
            }
        } else { assertEquals(expected, actual, context); }
    }
}

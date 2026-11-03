package org.xar.ck3.control.contracts.metrics;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrowsExactly;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.charset.StandardCharsets;
import java.time.DateTimeException;
import java.time.Instant;
import java.time.format.DateTimeParseException;
import java.util.List;
import java.util.Optional;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;

public class DecisionMetricsUtcParsingPublicBoundaryTest {
    @Test
    public void publicProducersAndBothDecodersRetainPrecisionAndWideYears() {
        Instant[] times = {
                Instant.ofEpochSecond(0, 1),
                Instant.ofEpochSecond(-62_167_219_200L, 999_999_999),
                Instant.ofEpochSecond(253_402_300_800L, 123_456_789)
        };
        for (Instant time : times) {
            DecisionMetrics.Snapshot expected = snapshot(time);
            assertEquals(expected, decodeStable(false, DecisionMetrics.encode(expected)));
            BatchDecisionMetrics.Batch batch = batch(expected);
            assertEquals(batch, decodeStable(true, BatchDecisionMetrics.encode(batch)));
        }

        for (String time : new String[] {
                "1970-01-01T00:00:00.000000001+00:00",
                "1970-01-01t00:00:00.000000001z"
        }) {
            String began = tick(time, "c", "0", "1", "null");
            DecisionMetrics.Snapshot decoded = (DecisionMetrics.Snapshot) decodeStable(false, document(false, began));
            assertEquals(Instant.ofEpochSecond(0, 1), decoded.spans().get(0).began().utc());
            assertTrue(decoded.spans().get(0).utcRegressed());
            BatchDecisionMetrics.Batch decodedBatch = (BatchDecisionMetrics.Batch) decodeStable(true, document(true, began));
            assertEquals(Instant.ofEpochSecond(0, 1), decodedBatch.window().began().utc());
            assertEquals(Instant.EPOCH, decodedBatch.window().ended().utc());
        }
    }

    @Test
    public void everyTickFieldKeepsItsOriginalFailurePriorityAndCalendarCause() {
        String invalidDate = "2026-02-30T12:34:56Z";
        String tooLarge = "9223372036854775808";
        String[][] cases = {
                {"", "00", invalidDate, tooLarge, "{}", "nonempty bounded text required"},
                {"c", "00", invalidDate, tooLarge, "{}", "canonical decimal string required for 64-bit metric"},
                {"c", "0", "1970-01-01T00:00:00Z", tooLarge, "{}", "signed monotonic domain exceeded"},
                {"c", "0", "1970-01-01T00:00:00Z", "1", "{}", "JSON string required"},
                {"c", "0", "1970-01-01T00:00:00Z", "0", "{}", "JSON string required"},
                {"c", "0", "1970-01-01T00:00:00Z", "0", "null",
                        "nonnegative local monotonic tick and owner thread required"}
        };
        for (String[] row : cases) {
            simpleFailureBoth(tick(row[2], row[0], row[1], row[3], row[4]), row[5]);
        }

        for (boolean isBatch : new boolean[] {false, true}) {
            DateTimeParseException cause = isoFailure(isBatch,
                    document(isBatch, tick(invalidDate, "c", "0", tooLarge, "{}")), invalidDate);
            assertEquals("Text '2026-02-30T12:34:56Z' could not be parsed: Invalid date 'FEBRUARY 30'",
                    cause.getMessage());
            assertEquals(0, cause.getErrorIndex());
            assertEquals(DateTimeException.class, cause.getCause().getClass());
            assertEquals("Invalid date 'FEBRUARY 30'", cause.getCause().getMessage());
            assertNull(cause.getCause().getCause());
        }
    }

    @Test
    public void originalNormalizationAndInstantSpecialCasesKeepTheirFailureContracts() {
        simpleFailureBoth(tick("1970-01-01T00:00:00+01:00", "c", "0", "1", "null"),
                "UTC offset zero required");

        String[] targetFailures = {"19700101T00:00:00Z", "1970-01-01T00:00Z"};
        int[] errorIndices = {0, 16};
        for (int index = 0; index < targetFailures.length; index++) {
            String time = targetFailures[index];
            for (boolean isBatch : new boolean[] {false, true}) {
                byte[] raw = document(isBatch, tick(time, "c", "0", "1", "null"));
                DateTimeParseException failure = assertThrowsExactly(DateTimeParseException.class,
                        () -> decodeStable(isBatch, raw));
                assertEquals(time, failure.getParsedString());
                assertEquals(errorIndices[index], failure.getErrorIndex());
                assertEquals("Text '" + time + "' could not be parsed at index " + errorIndices[index],
                        failure.getMessage());
                assertNull(failure.getCause());
            }
        }

        for (String time : new String[] {"2016-12-31T23:59:60Z", "1970-01-01T24:00:00Z"}) {
            for (boolean isBatch : new boolean[] {false, true}) {
                isoFailure(isBatch, document(isBatch, tick(time, "c", "0", "1", "null")), time);
            }
        }

        // Public Tick construction accepts these Instants; the original decoder still rejects their local-year domain.
        for (Instant extreme : new Instant[] {Instant.MIN, Instant.MAX}) {
            DecisionMetrics.Snapshot source = snapshot(extreme);
            isoFailure(false, DecisionMetrics.encode(source), extreme.toString());
            isoFailure(true, BatchDecisionMetrics.encode(batch(source)), extreme.toString());
        }
    }

    private static DecisionMetrics.Snapshot snapshot(Instant time) {
        DecisionMetrics.Context context = new DecisionMetrics.Context("m", "s", "b", "r", "c");
        DecisionMetrics.Tick began = new DecisionMetrics.Tick("c", 7, time, 3, OptionalLong.of(17));
        DecisionMetrics.Tick ended = new DecisionMetrics.Tick("c", 9, time, 3, OptionalLong.of(18));
        DecisionMetrics.Span span = new DecisionMetrics.Span(DecisionMetrics.Stage.QUEUED, began, ended,
                DecisionMetrics.Terminal.RETURNED);
        return new DecisionMetrics.Snapshot(context, List.of(span), Optional.empty(), Optional.empty(), Optional.empty());
    }

    private static BatchDecisionMetrics.Batch batch(DecisionMetrics.Snapshot request) {
        DecisionMetrics.Span span = request.spans().get(0);
        BatchDecisionMetrics.Context context = new BatchDecisionMetrics.Context("m", "s", "b", "c");
        BatchDecisionMetrics.Window window = new BatchDecisionMetrics.Window(span.began(), span.ended(),
                DecisionMetrics.Terminal.RETURNED);
        return new BatchDecisionMetrics.Batch(context, window, List.of(request));
    }

    private static String tick(String time, String clock, String elapsed, String thread, String cpuJson) {
        return "{\"clock_domain_id\":\"" + clock + "\",\"elapsed_nanos\":\"" + elapsed
                + "\",\"utc\":\"" + time + "\",\"thread_id\":\"" + thread
                + "\",\"thread_cpu_nanos\":" + cpuJson + "}";
    }

    private static byte[] document(boolean isBatch, String began) {
        String ended = tick("1970-01-01T00:00:00Z", "c", "1", "1", "null");
        String json;
        if (isBatch) {
            json = "{\"schema\":\"xar.batch-decision-metrics/v1\","
                    + "\"context\":{\"machine_id\":\"m\",\"scope_id\":\"s\",\"batch_id\":\"b\",\"clock_domain_id\":\"c\"},"
                    + "\"window\":{\"began\":" + began + ",\"ended\":" + ended
                    + ",\"terminal\":\"RETURNED\"},\"requests\":[]}";
        } else {
            json = "{\"schema\":\"xar.decision-metrics/v2\","
                    + "\"context\":{\"machine_id\":\"m\",\"scope_id\":\"s\",\"batch_id\":\"b\","
                    + "\"request_id\":\"r\",\"clock_domain_id\":\"c\"},"
                    + "\"spans\":[{\"stage\":\"QUEUED\",\"terminal\":\"RETURNED\",\"began\":" + began
                    + ",\"ended\":" + ended + "}],"
                    + "\"acknowledgements\":null,\"native_observation\":null,\"saved_window\":null}";
        }
        return json.getBytes(StandardCharsets.UTF_8);
    }

    private static Object decodeStable(boolean isBatch, byte[] raw) {
        byte[] before = raw.clone();
        try {
            return isBatch ? BatchDecisionMetrics.decode(raw) : DecisionMetrics.decode(raw);
        } finally {
            assertArrayEquals(before, raw);
        }
    }

    private static void simpleFailureBoth(String began, String expected) {
        for (boolean isBatch : new boolean[] {false, true}) {
            byte[] raw = document(isBatch, began);
            ContractViolationException failure = assertThrowsExactly(ContractViolationException.class,
                    () -> decodeStable(isBatch, raw));
            assertEquals(expected, failure.getMessage());
            assertNull(failure.getCause());
        }
    }

    private static DateTimeParseException isoFailure(boolean isBatch, byte[] raw, String originalTime) {
        ContractViolationException failure = assertThrowsExactly(ContractViolationException.class,
                () -> decodeStable(isBatch, raw));
        assertEquals("ISO UTC observation time required", failure.getMessage());
        assertNotNull(failure.getCause());
        assertEquals(DateTimeParseException.class, failure.getCause().getClass());
        DateTimeParseException cause = (DateTimeParseException) failure.getCause();
        assertEquals(originalTime, cause.getParsedString());
        assertTrue(cause.getCause() instanceof DateTimeException);
        return cause;
    }
}

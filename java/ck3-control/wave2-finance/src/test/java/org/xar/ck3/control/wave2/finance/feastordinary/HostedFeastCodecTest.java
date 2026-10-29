package org.xar.ck3.control.wave2.finance.feastordinary;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.IOException;
import java.io.InputStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;
import java.util.stream.StreamSupport;
import org.junit.jupiter.api.DynamicTest;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.TestFactory;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.Activity;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampAbsent;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampObserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.StampUnobserved;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.TerminalAbsent;
import org.xar.ck3.control.wave2.finance.feastordinary.HostedFeastActivities.TerminalObserved;

final class HostedFeastCodecTest {
    private static final ObjectMapper JSON = new ObjectMapper();
    private static final String SOURCE_SHA = "656b02666880395c1bc1e0e3de4d9ff9d1a0d30e1393fc69e1d930aef43b8f3f";
    private static final String IDENTITY = "\"activity_id\":18,\"host_character_id\":29829,\"activity_type_key\":\"activity_feast\"";

    @TestFactory
    Stream<DynamicTest> comparesOriginalProducerRawTokensAndRoundTripsEveryAcceptedRow() throws IOException {
        JsonNode root = golden();
        assertEquals("xar.feast-ordinary-hosted-golden/v1", root.get("schema").textValue());
        assertEquals(54, root.get("cases").size());
        return StreamSupport.stream(root.get("cases").spliterator(), false).map(row ->
                DynamicTest.dynamicTest(row.get("name").textValue(), () -> {
                    byte[] raw = row.get("input_json").textValue().getBytes(StandardCharsets.UTF_8);
                    if (!row.get("accepted").booleanValue()) {
                        assertThrows(IllegalArgumentException.class, () -> HostedFeastCodec.decode(raw));
                        return;
                    }
                    HostedFeastActivities result = HostedFeastCodec.decode(raw);
                    byte[] encoded = HostedFeastCodec.encode(result);
                    assertEquals(row.get("result"), JSON.readTree(encoded));
                    assertEquals(result, HostedFeastCodec.decode(encoded));
                }));
    }

    @Test
    void bindsActualSourceAndExistingTestExecutionWithoutImportingPython() throws IOException {
        JsonNode root = golden();
        assertEquals("xenoamess-full-tower-eb9d2c1186", root.get("machine_id").textValue());
        assertEquals(SOURCE_SHA, root.get("source_refs").get(0).get("sha256").textValue());
        assertEquals(4, root.get("existing_tests").get("run").intValue());
        assertEquals(0, root.get("existing_tests").get("failures").intValue());
        assertEquals(0, root.get("existing_tests").get("errors").intValue());
        assertEquals(0, root.get("existing_tests").get("skipped").intValue());
        assertTrue(root.get("capture_scope").textValue().startsWith("actual _hosted producer invoked"));
    }

    @Test
    void preservesAbsenceUnobservedAndObservedZeroAsSeparateBranches() {
        HostedFeastActivities missing = decode("[{" + IDENTITY + "}]");
        HostedFeastActivities unknown = decode("[{" + IDENTITY + ",\"native_completion_stamp_observed\":false,\"native_completion_stamp_raw\":null}]");
        HostedFeastActivities zero = decode("[{" + IDENTITY + ",\"native_completion_stamp_observed\":true,\"native_completion_stamp_raw\":0}]");
        assertInstanceOf(StampAbsent.class, missing.activities().getFirst().completionStamp());
        assertInstanceOf(StampUnobserved.class, unknown.activities().getFirst().completionStamp());
        assertEquals(new StampObserved(BigInteger.ZERO), zero.activities().getFirst().completionStamp());
        assertFalse(missing.equals(unknown)); assertFalse(unknown.equals(zero));
        assertInstanceOf(TerminalAbsent.class, missing.activities().getFirst().terminal());
    }

    @Test
    void rejectsRawFloatExponentBooleanAndStringIdentityTokens() {
        for (String token : List.of("18.0", "18e0", "true", "\"18\"", "null")) {
            String raw = "[{\"activity_id\":" + token + ",\"host_character_id\":29829,\"activity_type_key\":\"activity_feast\"}]";
            assertThrows(IllegalArgumentException.class, () -> decode(raw), token);
        }
        for (String token : List.of("1.0", "1e0", "true", "\"1\"", "-1", "18446744073709551616")) {
            String raw = "[{" + IDENTITY + ",\"native_completion_stamp_observed\":true,\"native_completion_stamp_raw\":" + token + "}]";
            assertThrows(IllegalArgumentException.class, () -> decode(raw), token);
        }
    }

    @Test
    void rejectsDuplicateKeysTrailingValuesMalformedUtf8AndOversize() {
        assertThrows(IllegalArgumentException.class, () -> decode("[{" + IDENTITY + ",\"activity_id\":19}]"));
        assertThrows(IllegalArgumentException.class, () -> decode("[] []"));
        assertThrows(IllegalArgumentException.class, () -> HostedFeastCodec.decode(new byte[] {(byte) 0xC3, 0x28}));
        assertThrows(IllegalArgumentException.class, () -> HostedFeastCodec.decode(new byte[HostedFeastCodec.MAX_BYTES + 1]));
        assertThrows(IllegalArgumentException.class, () -> HostedFeastCodec.decode(new byte[0]));
    }

    @Test
    void validatesDirectConstructionAndDefensivelyCopiesCollections() {
        Activity first = new Activity(18, 29829, "activity_feast", new TerminalAbsent(), new StampAbsent());
        ArrayList<Activity> mutable = new ArrayList<>(List.of(first));
        HostedFeastActivities value = new HostedFeastActivities(mutable);
        mutable.clear(); assertEquals(1, value.activities().size());
        assertThrows(UnsupportedOperationException.class, () -> value.activities().clear());
        assertThrows(IllegalArgumentException.class, () -> new HostedFeastActivities(List.of(first, first)));
        assertThrows(IllegalArgumentException.class, () -> new Activity(0, 29829, "activity_feast", new TerminalAbsent(), new StampAbsent()));
        assertThrows(IllegalArgumentException.class, () -> new Activity(18, 4_294_967_296L, "activity_feast", new TerminalAbsent(), new StampAbsent()));
        assertThrows(IllegalArgumentException.class, () -> new StampObserved(BigInteger.ONE.shiftLeft(64)));
        assertThrows(IllegalArgumentException.class, () -> new StampObserved(BigInteger.valueOf(-1)));
    }

    @Test
    void terminalFlagsRemainCurrentFactsRatherThanCompletionCredit() {
        HostedFeastActivities current = decode("[{" + IDENTITY + ",\"terminal_flags_observed\":true,\"native_completed\":false,\"native_invalidated\":false}]");
        assertEquals(new TerminalObserved(false, false), current.activities().getFirst().terminal());
        HostedFeastActivities both = decode("[{" + IDENTITY + ",\"terminal_flags_observed\":true,\"native_completed\":true,\"native_invalidated\":true}]");
        assertEquals(new TerminalObserved(true, true), both.activities().getFirst().terminal());
        assertThrows(IllegalArgumentException.class, () -> decode("[{" + IDENTITY + ",\"terminal_flags_observed\":false,\"native_completed\":false,\"native_invalidated\":false}]"));
    }

    @Test
    void acceptsFullLegalRowCountWithEveryOptionalFieldAndEscapedUnicode() {
        String escapedKey = "\\uD83D\\uDD25".repeat(63);
        StringBuilder raw = new StringBuilder("[");
        for (int index = 1; index <= 64; index++) {
            if (index != 1) raw.append(", ");
            raw.append("{\"activity_id\": ").append(HostedFeastActivities.MAX_U32 - 64 + index)
                    .append(", \"host_character_id\": 4294967295, \"activity_type_key\": \"").append(escapedKey)
                    .append("\", \"terminal_flags_observed\": true, \"native_completed\": true, \"native_invalidated\": true, ")
                    .append("\"native_completion_stamp_observed\": true, \"native_completion_stamp_raw\": 18446744073709551615}");
        }
        raw.append(']');
        byte[] bytes = raw.toString().getBytes(StandardCharsets.UTF_8);
        assertTrue(bytes.length > 65_536, "legal full-domain rows exceed the smaller generic byte limit");
        assertTrue(bytes.length <= HostedFeastCodec.MAX_BYTES);
        HostedFeastActivities value = HostedFeastCodec.decode(bytes);
        assertEquals(64, value.activities().size());
        assertEquals(63, value.activities().getFirst().activityTypeKey().codePointCount(0, value.activities().getFirst().activityTypeKey().length()));
    }

    @Test
    void requiresRealBooleanTokensForEveryObservationFlag() {
        for (String token : List.of("1", "1.0", "\"true\"", "null")) {
            String terminal = "[{" + IDENTITY + ",\"terminal_flags_observed\":" + token
                    + ",\"native_completed\":false,\"native_invalidated\":false}]";
            String stamp = "[{" + IDENTITY + ",\"native_completion_stamp_observed\":" + token
                    + ",\"native_completion_stamp_raw\":null}]";
            assertThrows(IllegalArgumentException.class, () -> decode(terminal), token);
            assertThrows(IllegalArgumentException.class, () -> decode(stamp), token);
        }
    }

    private static HostedFeastActivities decode(String raw) { return HostedFeastCodec.decode(raw.getBytes(StandardCharsets.UTF_8)); }
    private static JsonNode golden() throws IOException {
        try (InputStream input = HostedFeastCodecTest.class.getResourceAsStream("/feastordinary/hosted-producer-golden-v1.json")) {
            if (input == null) throw new IOException("required actual producer golden unavailable; capture is not a default-test fallback");
            return JSON.readTree(input.readAllBytes());
        }
    }
}

package org.xar.ck3.control.continuity;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.StrictJson;

final class ContinuityJsonValidation331Test {
    // This is the unchanged original second-pass configuration. The first pass
    // deliberately calls the unchanged public StrictJson.parse, not validate.
    private static final ObjectMapper ORIGINAL_SECOND = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION).build())
            .enable(DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS);

    @Test
    void validObjectsKeepBinary64AndCanonicalBytes() {
        List<String> values = List.of(
                "{}", " {\"a\":[null,true,false,0,1,-1,\"\",{\"x\":\"\\u20ac\"}]} ",
                "{\"v\":-0.0}", "{\"v\":0.0}", "{\"v\":1.2300}",
                "{\"v\":1e6}", "{\"v\":1e-5}", "{\"v\":1e-400}",
                "{\"v\":-1e-400}", "{\"v\":5e-324}", "{\"v\":1e308}",
                "{\"a\":9007199254740991,\"b\":-9007199254740991}",
                "{\"a\":{\"x\":1},\"b\":{\"x\":2}}",
                "{\"v\":[1.0,-0.0,1.25,2e-4,1e16]}",
                "{\"s\":\"\\\"\\\\\\b\\f\\n\\r\\t\\u0000\"}",
                "{\"\\ud800\\udc00\":1,\"\\ue000\":2,\"a\":\"\u20ac\"}");
        for (String value : values) { assertAcceptedSame(bytes(value), 65_536); }

        ObjectNode negativeZero = ContinuityJson.parseObject(bytes("{\"v\":-0.0}"), 65_536);
        assertTrue(negativeZero.get("v").isDouble());
        assertEquals(0x8000000000000000L, Double.doubleToRawLongBits(negativeZero.get("v").doubleValue()));
        assertArrayEquals(bytes("{\"v\":-0.0}"), ContinuityJson.canonical(negativeZero));
        assertArrayEquals(bytes("{\"v\":1.23}"),
                ContinuityJson.canonical(ContinuityJson.parseObject(bytes("{\"v\":1.2300}"), 65_536)));
        assertArrayEquals(bytes("{\"v\":1000000.0}"),
                ContinuityJson.canonical(ContinuityJson.parseObject(bytes("{\"v\":1e6}"), 65_536)));
        assertTrue(StrictJson.parse(bytes("{\"v\":-0.0}")).get("v").isBigDecimal());

        byte[] inclusive = bytes("{\"s\":\"" + "a".repeat(65_528) + "\"}");
        assertEquals(65_536, inclusive.length);
        assertAcceptedSame(inclusive, inclusive.length);
        byte[] explicit = bytes("{\"s\":\"" + "a".repeat(65_529) + "\"}");
        assertEquals(65_537, explicit.length);
        assertAcceptedSame(explicit, explicit.length);
        assertRejectedSame(explicit, 65_536, "bounded nonempty UTF-8 JSON required");

        ObjectNode mutable = ContinuityJson.parseObject(bytes("{\"v\":1.0}"), 65_536);
        mutable.put("v", 2.5);
        assertArrayEquals(bytes("{\"v\":2.5}"), ContinuityJson.canonical(mutable));
    }

    @Test
    void invalidInputsRetainOriginalFirstFailureAndCause() {
        assertRejectedSame(null, 0, "explicit JSON input byte budget");
        assertRejectedSame(null, 65_536, "bounded nonempty UTF-8 JSON required");
        assertRejectedSame(new byte[0], 65_536, "bounded nonempty UTF-8 JSON required");
        assertRejectedSame(bytes("{}"), 1, "bounded nonempty UTF-8 JSON required");
        assertRejectedSame(bytes("{}"), 1_048_577, "explicit JSON input byte budget");
        assertRejectedSame(new byte[] {(byte) 0xc3, 0x28}, 65_536, "invalid UTF-8 JSON");
        assertRejectedSame(new byte[] {(byte) 0xff, (byte) 0xfe, '{', 0, '}', 0},
                65_536, "invalid UTF-8 JSON");
        assertRejectedSame(bytes("{\"n\":1e400,\"a\":0,\"a\":1}"), 65_536,
                "invalid or duplicate JSON fields");
        assertRejectedSame(bytes("{\"v\":1e400}"), 65_536, "finite continuity JSON number");
        assertRejectedSame(bytes("[1e400]"), 65_536, "continuity JSON object required");
        assertRejectedSame(bytes("{\"v\":9007199254740992}"), 65_536, "integer outside contract range");
        assertRejectedSame(bytes("{\"v\":1e6}"), 9, "continuity JSON exceeds byte budget");
        assertRejectedSame(bytes("{\"s\":\"\\ud800\"}"), 65_536,
                "unpaired continuity Unicode surrogate");
        assertRejectedSame(bytes("{\"\\udc00\":0}"), 65_536,
                "invalid continuity JSON");

        List<String> malformed = new ArrayList<>(List.of(
                " ", "null", "true", "1.0", "\"s\"", "[]", "{} {}", "{} 0", "{} true",
                "{\"a\":[1,null", "{\"a\":{\"x\":1,\"x\":2}}", "{\"a\":1,}",
                "{\"s\":\"\\q\",\"a\":1,\"a\":2}", "{\"v\":01}", "{\"a\":]}",
                "{\"v\":1e2147483648}", "{\"v\":1e-2147483648}",
                "{\"v\":1e2147483647}", "{\"v\":1e400} false",
                "{\"s\":\"\\ud800\",\"a\":0,\"a\":1}",
                "{\"v\":" + "7".repeat(1_100) + "}",
                "{\"v\":" + "[".repeat(1_100) + "0" + "]".repeat(1_100) + "}"));
        for (String value : malformed) { assertFailureSame(bytes(value), 65_536); }
        assertRejectedSame(new byte[] {(byte) 0xef, (byte) 0xbb, (byte) 0xbf, '{', '}'}, 65_536, null);
    }

    private static ObjectNode original(byte[] raw, int maximum) {
        StrictJson.parse(raw, maximum);
        try {
            ObjectNode row = ContinuityJson.object(ORIGINAL_SECOND.readTree(raw));
            ContinuityJson.canonical(row, maximum);
            return row;
        } catch (IOException error) {
            throw new ContractViolationException("invalid continuity JSON", error);
        }
    }

    private static void assertAcceptedSame(byte[] raw, int maximum) {
        ObjectNode expected = original(raw, maximum);
        ObjectNode actual = ContinuityJson.parseObject(raw, maximum);
        assertTree(expected, actual);
        assertArrayEquals(ContinuityJson.canonical(expected, maximum), ContinuityJson.canonical(actual, maximum));
    }

    private static void assertTree(JsonNode expected, JsonNode actual) {
        assertEquals(expected.getClass(), actual.getClass());
        assertEquals(expected, actual);
        if (expected.isFloatingPointNumber()) {
            assertEquals(Double.doubleToRawLongBits(expected.doubleValue()),
                    Double.doubleToRawLongBits(actual.doubleValue()));
        } else if (expected.isObject()) {
            expected.fieldNames().forEachRemaining(key -> assertTree(expected.get(key), actual.get(key)));
        } else if (expected.isArray()) {
            for (int i = 0; i < expected.size(); i++) { assertTree(expected.get(i), actual.get(i)); }
        }
    }

    private static void assertRejectedSame(byte[] raw, int maximum, String expectedMessage) {
        ContractViolationException expected = assertThrows(ContractViolationException.class,
                () -> original(raw, maximum));
        ContractViolationException actual = assertThrows(ContractViolationException.class,
                () -> ContinuityJson.parseObject(raw, maximum));
        assertEquals(expected.getMessage(), actual.getMessage());
        if (expectedMessage != null) { assertEquals(expectedMessage, expected.getMessage()); }
        assertCause(expected.getCause(), actual.getCause());
    }

    private static void assertFailureSame(byte[] raw, int maximum) {
        RuntimeException expected = assertThrows(RuntimeException.class, () -> original(raw, maximum));
        RuntimeException actual = assertThrows(RuntimeException.class,
                () -> ContinuityJson.parseObject(raw, maximum));
        assertEquals(expected.getClass(), actual.getClass());
        assertEquals(expected.getMessage(), actual.getMessage());
        assertCause(expected.getCause(), actual.getCause());
    }

    private static void assertCause(Throwable expected, Throwable actual) {
        if (expected == null) { assertNull(actual); return; }
        assertNotNull(actual);
        assertEquals(expected.getClass(), actual.getClass());
        assertEquals(expected.getMessage(), actual.getMessage());
        assertCause(expected.getCause(), actual.getCause());
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

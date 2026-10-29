package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.List;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class StrictJsonChildExportsProfileTest {
    private static final StrictJson.NumericProfile PROFILE =
            StrictJson.NumericProfile.PYTHON_CHILD_EXPORTS_4300;

    @Test void explicitProfileAcceptsOriginal1100And4300DigitValuesWhileDefaultStillRejectsThem() {
        for (int digits : List.of(1_100, 4_300)) {
            String decimal = "1" + "0".repeat(digits - 1);
            for (String sign : List.of("", "-")) {
                byte[] raw = bytes("{\"location\":" + sign + decimal + "}");
                JsonNode privateValue = StrictJson.parse(raw, 16_384, PROFILE);
                assertTrue(privateValue.get("location").isIntegralNumber());
                assertEquals(new BigInteger(sign + decimal), privateValue.get("location").bigIntegerValue());
                assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw));
                assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw, 16_384));
            }
        }
        assertEquals(7, StrictJson.parse(bytes("{\"location\":7}")).get("location").intValue());
    }

    @Test void original4301DigitWireValueIsRejectedWithoutNarrowingTheMemoryDomain() {
        BigInteger memoryOnly = BigInteger.TEN.pow(4_300);
        assertEquals(4_301, memoryOnly.toString().length());
        for (String sign : List.of("", "-")) {
            byte[] raw = bytes("{\"location\":" + sign + memoryOnly + "}");
            assertThrows(ContractViolationException.class, () -> StrictJson.parse(raw, 16_384, PROFILE));
        }
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(bytes("{}"), 16_384, null));
    }

    @Test void profileRetainsRawTokenKindsAndStrictFramingAndUtf8Boundaries() {
        JsonNode bool = StrictJson.parse(bytes("true"), 16_384, PROFILE);
        JsonNode floating = StrictJson.parse(bytes("501.0"), 16_384, PROFILE);
        JsonNode text = StrictJson.parse(bytes("\"501\""), 16_384, PROFILE);
        assertTrue(bool.isBoolean());
        assertTrue(floating.isFloatingPointNumber());
        assertFalse(floating.isIntegralNumber());
        assertTrue(text.isTextual());
        for (String wire : List.of("{\"x\":1,\"x\":2}", "{} {}", "")) {
            assertThrows(ContractViolationException.class, () -> StrictJson.parse(bytes(wire), 16_384, PROFILE));
        }
        assertThrows(ContractViolationException.class,
                () -> StrictJson.parse(new byte[] {(byte) 0xc3, (byte) 0x28}, 16_384, PROFILE));
    }

    @Test void independentPrivateByteCapIncludesWhitespaceAndFinalLf() {
        String prefix = "{\"location\":1" + "0".repeat(4_299) + "}";
        byte[] exact = bytes(prefix + " ".repeat(16_383 - prefix.length()) + "\n");
        assertEquals(16_384, exact.length);
        assertEquals(4_300, StrictJson.parse(exact, 16_384, PROFILE).get("location").asText().length());
        byte[] extra = bytes(new String(exact, StandardCharsets.UTF_8) + " ");
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(extra, 16_384, PROFILE));
        assertThrows(ContractViolationException.class, () -> StrictJson.parse(exact, 0, PROFILE));
        assertThrows(ContractViolationException.class,
                () -> StrictJson.parse(exact, StrictJson.EXPLICIT_MAX_BYTES + 1, PROFILE));
    }

    private static byte[] bytes(String value) { return value.getBytes(StandardCharsets.UTF_8); }
}

package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.FullJsonTree;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Public DEATH DATA contract from the original codec; no lifecycle authority is constructed. */
public final class LifecycleDeathPublicDataOwner61Test {
    private static final int FIXTURE_BYTES = 16_384;
    private static final String DECODE_ROLE_ERROR =
            "public lifecycle revision requires a canonical decimal string";
    private static final String ENCODE_ROLE_ERROR =
            "original lifecycle revision must be an exact nonnegative integer";

    @Test
    void optionalRevisionAndOriginalDataSurviveIndependentDeathProjections() {
        String[] revisionFields = {
                "", "\"revision\":null,", "\"revision\":0,",
                "\"revision\":18446744073709551615,"
        };
        String[] revisionText = {null, null, "0", "18446744073709551615"};
        RawJson[] originals = new RawJson[revisionFields.length];
        RawJson[] publicValues = new RawJson[revisionFields.length];
        RawJson[] restored = new RawJson[revisionFields.length];
        byte[][] originalBytes = new byte[revisionFields.length][];
        byte[][] publicBytes = new byte[revisionFields.length][];
        byte[][] restoredBytes = new byte[revisionFields.length][];

        for (int index = 0; index < revisionFields.length; index++) {
            String marker = "death-" + index;
            originals[index] = raw("{" + revisionFields[index] + payload(marker) + "}");
            originalBytes[index] = originals[index].bytes();
            publicValues[index] = LifecyclePublicResultCodec.encodeSettlementInspection(originals[index]);
            publicBytes[index] = publicValues[index].bytes();
            restored[index] = LifecyclePublicResultCodec.decodeSettlementInspection(publicValues[index]);
            restoredBytes[index] = restored[index].bytes();

            JsonNode publicTree = tree(publicValues[index]);
            JsonNode restoredTree = tree(restored[index]);
            assertPayload(publicTree, marker);
            assertPayload(restoredTree, marker);
            if (index == 0) {
                assertFalse(publicTree.has("revision"));
                assertFalse(restoredTree.has("revision"));
            } else if (index == 1) {
                assertTrue(publicTree.has("revision"));
                assertTrue(publicTree.get("revision").isNull());
                assertTrue(restoredTree.has("revision"));
                assertTrue(restoredTree.get("revision").isNull());
            } else {
                assertTrue(publicTree.get("revision").isTextual());
                assertEquals(revisionText[index], publicTree.get("revision").textValue());
                assertTrue(restoredTree.get("revision").isIntegralNumber());
                assertEquals(new BigInteger(revisionText[index]), restoredTree.get("revision").bigIntegerValue());
            }
            assertSameData(originals[index], restored[index]);
        }

        // Revisit every retained value after the other projections, then decode the first again.
        for (int index = 0; index < originals.length; index++) {
            assertArrayEquals(originalBytes[index], originals[index].bytes());
            assertArrayEquals(publicBytes[index], publicValues[index].bytes());
            assertArrayEquals(restoredBytes[index], restored[index].bytes());
            assertPayload(tree(publicValues[index]), "death-" + index);
        }
        RawJson firstAgain = LifecyclePublicResultCodec.decodeSettlementInspection(publicValues[0]);
        assertSameData(originals[0], firstAgain);
        assertArrayEquals(publicBytes[0], publicValues[0].bytes());
        assertArrayEquals(originalBytes[0], originals[0].bytes());
    }

    @Test
    void publicRevisionRequiresItsOriginalCanonicalDecimalRoleAndLengthBound() {
        String boundary = "1" + "0".repeat(4299);
        for (String valid : new String[] {"0", "1", boundary}) {
            RawJson publicValue = raw("{\"revision\":\"" + valid + "\",\"opaque\":\"00042\"}");
            byte[] before = publicValue.bytes();
            RawJson restored = LifecyclePublicResultCodec.decodeSettlementInspection(publicValue);
            JsonNode restoredTree = tree(restored);
            assertTrue(restoredTree.get("revision").isIntegralNumber());
            assertEquals(new BigInteger(valid), restoredTree.get("revision").bigIntegerValue());
            assertTrue(restoredTree.get("opaque").isTextual());
            assertEquals("00042", restoredTree.get("opaque").textValue());
            RawJson encodedAgain = LifecyclePublicResultCodec.encodeSettlementInspection(restored);
            assertEquals(valid, tree(encodedAgain).get("revision").textValue());
            assertArrayEquals(before, publicValue.bytes());
        }

        String[] invalidValues = {
                "1", "false", "\"\"", "\"00\"", "\"01\"", "\"+1\"", "\"-1\"",
                "\"1e0\"", "\" 1\"", "\"1\\n\"", "\"\\u0661\"", "\"\\uff11\"",
                "\"" + "1".repeat(4301) + "\""
        };
        for (String value : invalidValues) {
            assertDecodeRoleFailure("{\"revision\":" + value + ",\"count\":7}");
        }
        for (String value : new String[] {"-1", "1.0", "\"1\""}) {
            assertEncodeRoleFailure("{\"revision\":" + value + ",\"count\":7}");
        }
    }

    @Test
    void finiteDoubleCannotEraseOriginalDecimalScaleFailureOrLexeme() {
        String validToken = "12e-2147483647";
        RawJson numericControl = raw("{\"revision\":1,\"score\":" + validToken + ",\"zero\":-0.0}");
        RawJson publicControl = raw("{\"revision\":\"1\",\"score\":" + validToken + ",\"zero\":-0.0}");
        byte[] numericControlBytes = numericControl.bytes();
        byte[] publicControlBytes = publicControl.bytes();
        RawJson encodedControl = LifecyclePublicResultCodec.encodeSettlementInspection(numericControl);
        RawJson decodedControl = LifecyclePublicResultCodec.decodeSettlementInspection(publicControl);
        assertEquals(validToken, decimalToken(tree(encodedControl).get("score")));
        assertEquals(validToken, decimalToken(tree(decodedControl).get("score")));
        assertEquals("-0.0", decimalToken(tree(encodedControl).get("zero")));
        assertEquals("-0.0", decimalToken(tree(decodedControl).get("zero")));
        assertSameData(numericControl, decodedControl);

        String invalidToken = "12e-2147483648";
        // Construction and token inspection happen outside the public-call exception assertions.
        RawJson numeric = raw("{\"revision\":1,\"score\":" + invalidToken + "}");
        RawJson publicValue = raw("{\"revision\":\"1\",\"score\":" + invalidToken + "}");
        assertEquals(invalidToken, decimalToken(tree(numeric).get("score")));
        assertEquals(invalidToken, decimalToken(tree(publicValue).get("score")));
        byte[] numericBytes = numeric.bytes();
        byte[] publicBytes = publicValue.bytes();

        NumberFormatException encodeFailure = assertThrows(NumberFormatException.class,
                () -> LifecyclePublicResultCodec.encodeSettlementInspection(numeric));
        assertEquals(NumberFormatException.class, encodeFailure.getClass());
        assertEquals("Exponent overflow.", encodeFailure.getMessage());
        assertNull(encodeFailure.getCause());
        assertArrayEquals(numericBytes, numeric.bytes());

        NumberFormatException decodeFailure = assertThrows(NumberFormatException.class,
                () -> LifecyclePublicResultCodec.decodeSettlementInspection(publicValue));
        assertEquals(NumberFormatException.class, decodeFailure.getClass());
        assertEquals("Exponent overflow.", decodeFailure.getMessage());
        assertNull(decodeFailure.getCause());
        assertArrayEquals(publicBytes, publicValue.bytes());

        // The original role error precedes decimal preservation even with the same extreme token.
        assertEncodeRoleFailure("{\"revision\":-1,\"score\":" + invalidToken + "}");
        assertDecodeRoleFailure("{\"revision\":\"01\",\"score\":" + invalidToken + "}");
        assertArrayEquals(numericControlBytes, numericControl.bytes());
        assertArrayEquals(publicControlBytes, publicControl.bytes());
    }

    private static String payload(String marker) {
        return "\"marker\":\"" + marker + "\",\"count\":7,\"opaque_digits\":\"00042\","
                + "\"label\":\"火焰🌍\",\"items\":[{\"zero\":-0.0,\"coefficient\":1.2500e+2},true,3]";
    }

    private static void assertPayload(JsonNode value, String marker) {
        assertEquals(marker, value.get("marker").textValue());
        assertTrue(value.get("count").isIntegralNumber());
        assertEquals(BigInteger.valueOf(7), value.get("count").bigIntegerValue());
        assertTrue(value.get("opaque_digits").isTextual());
        assertEquals("00042", value.get("opaque_digits").textValue());
        assertEquals("火焰🌍", value.get("label").textValue());
        JsonNode items = value.get("items");
        assertTrue(items.isArray());
        assertEquals(3, items.size());
        assertEquals("-0.0", decimalToken(items.get(0).get("zero")));
        assertEquals("1.2500e+2", decimalToken(items.get(0).get("coefficient")));
        assertTrue(items.get(1).isBoolean());
        assertTrue(items.get(1).booleanValue());
        assertTrue(items.get(2).isIntegralNumber());
        assertEquals(BigInteger.valueOf(3), items.get(2).bigIntegerValue());
    }

    private static RawJson raw(String text) {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        assertTrue(bytes.length <= FIXTURE_BYTES, "fixture must stay within its small DATA budget");
        RawJson result = RawJson.fullMaterial(bytes);
        assertArrayEquals(bytes, result.bytes());
        return result;
    }

    private static JsonNode tree(RawJson raw) {
        JsonNode result = FullJsonTree.parse(raw.bytes(), FIXTURE_BYTES);
        assertTrue(result.isObject());
        return result;
    }

    private static String decimalToken(JsonNode value) {
        assertTrue(value instanceof DecimalTokenNode);
        return ((DecimalTokenNode) value).originalToken();
    }

    private static void assertSameData(RawJson expected, RawJson actual) {
        assertEquals(DriverJson.object(expected.bytes(), FIXTURE_BYTES),
                DriverJson.object(actual.bytes(), FIXTURE_BYTES));
    }

    private static void assertDecodeRoleFailure(String text) {
        RawJson input = raw(text);
        byte[] before = input.bytes();
        ContractViolationException failure = assertThrows(ContractViolationException.class,
                () -> LifecyclePublicResultCodec.decodeSettlementInspection(input));
        assertEquals(ContractViolationException.class, failure.getClass());
        assertEquals(DECODE_ROLE_ERROR, failure.getMessage());
        assertNull(failure.getCause());
        assertArrayEquals(before, input.bytes());
    }

    private static void assertEncodeRoleFailure(String text) {
        RawJson input = raw(text);
        byte[] before = input.bytes();
        ContractViolationException failure = assertThrows(ContractViolationException.class,
                () -> LifecyclePublicResultCodec.encodeSettlementInspection(input));
        assertEquals(ContractViolationException.class, failure.getClass());
        assertEquals(ENCODE_ROLE_ERROR, failure.getMessage());
        assertNull(failure.getCause());
        assertArrayEquals(before, input.bytes());
    }
}

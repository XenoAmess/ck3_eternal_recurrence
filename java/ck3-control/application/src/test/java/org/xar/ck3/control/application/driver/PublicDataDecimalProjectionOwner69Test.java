package org.xar.ck3.control.application.driver;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.nio.charset.StandardCharsets;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.ContractViolationException;
import org.xar.ck3.control.contracts.DecimalTokenNode;
import org.xar.ck3.control.contracts.FullJsonTree;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** Direct public projection DATA contract, derived from the original implementation. */
public final class PublicDataDecimalProjectionOwner69Test {
    private static final int FIXTURE_BYTES = 16_384;
    private static final String INVALID_SCALE_TOKEN = "12e-2147483648";

    @Test
    void originalDecimalScaleAndLexemeRemainObservableInBothPublicEntries() {
        for (boolean fullMaterial : new boolean[] {false, true}) {
            RawJson invalidOriginal = raw("{\"score\":" + INVALID_SCALE_TOKEN + "}");
            ObjectNode invalidProjection = scoreProjection(INVALID_SCALE_TOKEN);
            assertEquals(INVALID_SCALE_TOKEN, decimalToken(tree(invalidOriginal).get("score")));
            assertEquals(INVALID_SCALE_TOKEN, decimalToken(invalidProjection.get("score")));
            assertScaleFailure(fullMaterial, invalidProjection, invalidOriginal);

            // This adjacent representable scale must not be rejected with the invalid token.
            assertSuccessfulProjection(fullMaterial, "12e-2147483647", "12e-2147483647");
            // Numerically equal projected text does not replace the original source lexeme.
            assertSuccessfulProjection(fullMaterial, "1.00", "1.0");
        }
    }

    @Test
    void changedValueAndCategoryKeepTheOriginalContainingPathAndFailureOrder() {
        for (boolean fullMaterial : new boolean[] {false, true}) {
            RawJson original = raw("{\"outer\":{\"score\":1.00}}");
            ObjectNode changedValue = nestedScore(new DecimalTokenNode("1.01"));
            assertContractFailure(fullMaterial, changedValue, original,
                    "original decimal value changed at /outer/score");

            ObjectNode changedCategory = nestedScore(JsonNodeFactory.instance.numberNode(1));
            assertContractFailure(fullMaterial, changedCategory, original,
                    "original decimal category changed at /outer/score");

            // Category validation precedes original BigDecimal construction at the same path.
            RawJson invalidScale = raw("{\"outer\":{\"score\":" + INVALID_SCALE_TOKEN + "}}");
            assertEquals(INVALID_SCALE_TOKEN,
                    decimalToken(tree(invalidScale).get("outer").get("score")));
            assertContractFailure(fullMaterial, changedCategory, invalidScale,
                    "original decimal category changed at /outer/score");
        }
    }

    @Test
    void callerProjectionFaultPrecedesPrivateOriginalDecimalComparison() {
        for (boolean fullMaterial : new boolean[] {false, true}) {
            RawJson original = raw("{\"score\":" + INVALID_SCALE_TOKEN + ",\"z_tail\":0}");
            byte[] originalBytes = original.bytes();
            assertEquals(INVALID_SCALE_TOKEN, decimalToken(tree(original).get("score")));

            ObjectNode ordinary = scoreProjection(INVALID_SCALE_TOKEN);
            ordinary.put("z_tail", 0);
            assertScaleFailure(fullMaterial, ordinary, original);

            IllegalStateException sentinel = new IllegalStateException("caller projected tail read");
            TailFaultObjectNode projected = new TailFaultObjectNode(sentinel);
            assertEquals(INVALID_SCALE_TOKEN, decimalToken(projected.get("score")));
            IllegalStateException failure = assertThrows(IllegalStateException.class,
                    () -> preserve(fullMaterial, projected, original));
            assertSame(sentinel, failure);
            assertArrayEquals(originalBytes, original.bytes());
            assertEquals(INVALID_SCALE_TOKEN, decimalToken(projected.get("score")));
        }
    }

    private static void assertSuccessfulProjection(boolean fullMaterial, String originalToken,
            String projectedToken) {
        RawJson original = raw("{\"score\":" + originalToken + "}");
        ObjectNode projected = scoreProjection(projectedToken);
        byte[] originalBytes = original.bytes();
        byte[] projectedBytes = FullJsonTree.encode(projected, FIXTURE_BYTES);
        RawJson result = preserve(fullMaterial, projected, original);
        JsonNode resultTree = tree(result);
        assertEquals(1, resultTree.size());
        assertEquals(originalToken, decimalToken(resultTree.get("score")));
        assertEquals(projectedToken, decimalToken(projected.get("score")));
        assertArrayEquals(originalBytes, original.bytes());
        assertArrayEquals(projectedBytes, FullJsonTree.encode(projected, FIXTURE_BYTES));
    }

    private static void assertScaleFailure(boolean fullMaterial, ObjectNode projected, RawJson original) {
        byte[] originalBytes = original.bytes();
        byte[] projectedBytes = FullJsonTree.encode(projected, FIXTURE_BYTES);
        NumberFormatException failure = assertThrows(NumberFormatException.class,
                () -> preserve(fullMaterial, projected, original));
        assertEquals(NumberFormatException.class, failure.getClass());
        assertEquals("Exponent overflow.", failure.getMessage());
        assertNull(failure.getCause());
        assertArrayEquals(originalBytes, original.bytes());
        assertArrayEquals(projectedBytes, FullJsonTree.encode(projected, FIXTURE_BYTES));
    }

    private static void assertContractFailure(boolean fullMaterial, ObjectNode projected,
            RawJson original, String expectedMessage) {
        byte[] originalBytes = original.bytes();
        byte[] projectedBytes = FullJsonTree.encode(projected, FIXTURE_BYTES);
        ContractViolationException failure = assertThrows(ContractViolationException.class,
                () -> preserve(fullMaterial, projected, original));
        assertEquals(ContractViolationException.class, failure.getClass());
        assertEquals(expectedMessage, failure.getMessage());
        assertNull(failure.getCause());
        assertArrayEquals(originalBytes, original.bytes());
        assertArrayEquals(projectedBytes, FullJsonTree.encode(projected, FIXTURE_BYTES));
    }

    private static RawJson preserve(boolean fullMaterial, JsonNode projected, RawJson original) {
        return fullMaterial ? PublicDataJson.encodePreservingFullMaterial(projected, original)
                : PublicDataJson.encodePreservingDecimals(projected, original);
    }

    private static ObjectNode scoreProjection(String token) {
        ObjectNode projected = JsonNodeFactory.instance.objectNode();
        projected.set("score", new DecimalTokenNode(token));
        return projected;
    }

    private static ObjectNode nestedScore(JsonNode score) {
        ObjectNode projected = JsonNodeFactory.instance.objectNode();
        ObjectNode outer = JsonNodeFactory.instance.objectNode();
        outer.set("score", score);
        projected.set("outer", outer);
        return projected;
    }

    private static RawJson raw(String text) {
        byte[] bytes = text.getBytes(StandardCharsets.UTF_8);
        assertTrue(bytes.length <= FIXTURE_BYTES, "small public DATA fixture required");
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

    // Jackson ObjectNode inherits JsonNode's generic deepCopy bridge.
    // This fixture adds no casts or deepCopy override.
    @SuppressWarnings("unchecked")
    private static final class TailFaultObjectNode extends ObjectNode {
        private static final long serialVersionUID = 1L;
        private final IllegalStateException sentinel;

        private TailFaultObjectNode(IllegalStateException sentinel) {
            super(JsonNodeFactory.instance);
            this.sentinel = sentinel;
            set("score", new DecimalTokenNode(INVALID_SCALE_TOKEN));
            put("z_tail", 0);
        }

        @Override
        public JsonNode get(String propertyName) {
            if ("z_tail".equals(propertyName)) throw sentinel;
            return super.get(propertyName);
        }
    }
}

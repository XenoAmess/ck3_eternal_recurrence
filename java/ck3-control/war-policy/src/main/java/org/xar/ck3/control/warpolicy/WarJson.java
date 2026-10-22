package org.xar.ck3.control.warpolicy;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Locale;
import org.xar.ck3.control.contracts.StrictJson;

/** Narrow legacy SDK JSON boundary; exact outer/query schemas are checked separately. */
final class WarJson {
    static final BigInteger INT32_MIN = BigInteger.valueOf(Integer.MIN_VALUE);
    static final BigInteger INT32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    static final BigInteger UINT32_MAX = new BigInteger("4294967295");
    static final String GAME_VERSION = "1.20.0.4";
    static final String EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    static final String ROOT_BACKEND = "ck3-1.20.0.4-native-campaign-root-context-v1";

    private WarJson() { }

    static ObjectNode record(JsonNode value, String name) {
        require(value instanceof ObjectNode, name + " must be a JSON object");
        return (ObjectNode) value;
    }

    static ArrayNode array(JsonNode value, String name) {
        require(value instanceof ArrayNode, name + " must be a JSON array");
        return (ArrayNode) value;
    }

    static int positive32(JsonNode value) {
        return StrictJson.integer(value, BigInteger.ONE, INT32_MAX).intValueExact();
    }

    static int signed32(JsonNode value) {
        return StrictJson.integer(value, INT32_MIN, INT32_MAX).intValueExact();
    }

    static int nonnegative32(JsonNode value) {
        return StrictJson.integer(value, BigInteger.ZERO, INT32_MAX).intValueExact();
    }

    static BigInteger positive64(JsonNode value) {
        return StrictJson.integer(value, BigInteger.ONE, StrictJson.UINT64_MAX);
    }

    static boolean bool(JsonNode value) {
        require(value != null && value.isBoolean(), "exact JSON boolean required");
        return value.booleanValue();
    }

    static boolean actualTrue(JsonNode value) {
        return value != null && value.isBoolean() && value.booleanValue();
    }

    static boolean actualFalse(JsonNode value) {
        return value != null && value.isBoolean() && !value.booleanValue();
    }

    static boolean nullValue(JsonNode value) {
        return value == null || value.isNull();
    }

    static String sha(JsonNode value) {
        String text = StrictJson.text(value);
        require(text.matches("[0-9a-fA-F]{64}"), "SHA-256 required");
        return text.toLowerCase(Locale.ROOT);
    }

    static boolean textEquals(JsonNode value, String expected) {
        return value != null && value.isTextual() && expected.equals(value.textValue());
    }
}

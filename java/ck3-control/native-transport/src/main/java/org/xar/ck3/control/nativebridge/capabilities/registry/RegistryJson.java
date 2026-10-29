package org.xar.ck3.control.nativebridge.capabilities.registry;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.StreamReadConstraints;
import com.fasterxml.jackson.core.StreamReadFeature;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;

/** Strict Native boundary; no missing/null or integer/boolean coercions. */
final class RegistryJson {
    static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    static final String EXE = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    private static final ObjectMapper JSON = new ObjectMapper(JsonFactory.builder()
            .enable(StreamReadFeature.STRICT_DUPLICATE_DETECTION)
            .streamReadConstraints(StreamReadConstraints.builder().maxStringLength(RawJson.MAXIMUM_BYTES)
                    .maxNumberLength(4300).maxNestingDepth(1000).build()).build())
            .enable(DeserializationFeature.FAIL_ON_TRAILING_TOKENS,
                    DeserializationFeature.USE_BIG_INTEGER_FOR_INTS, DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
    private RegistryJson() { }
    static void require(boolean ok, String reason) { if (!ok) throw new IllegalArgumentException(reason); }
    static ObjectNode object(RawJson input) {
        try { JsonNode value = JSON.readTree(input.bytes()); return object(value); }
        catch (IOException failure) { throw new IllegalArgumentException("invalid original Native object", failure); }
    }
    static ObjectNode object(JsonNode input) { require(input instanceof ObjectNode, "object required"); return (ObjectNode) input; }
    static JsonNode field(ObjectNode value, String name) { require(value.has(name), "missing field: " + name); return value.get(name); }
    static String text(JsonNode value) { require(value != null && value.isTextual() && !value.textValue().isEmpty(), "nonempty text required"); return value.textValue(); }
    static boolean bool(JsonNode value) { require(value != null && value.isBoolean(), "boolean required"); return value.booleanValue(); }
    static BigInteger integer(JsonNode value, BigInteger low, BigInteger high) {
        require(value != null && value.isIntegralNumber(), "exact JSON integer required");
        BigInteger result = value.bigIntegerValue();
        require(result.compareTo(low) >= 0 && (high == null || result.compareTo(high) <= 0), "integer outside range"); return result;
    }
    static int int32(JsonNode value) { return integer(value, BigInteger.valueOf(Integer.MIN_VALUE), BigInteger.valueOf(Integer.MAX_VALUE)).intValueExact(); }
    static void keys(ObjectNode value, Set<String> expected) {
        Set<String> actual = new HashSet<>(); value.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(expected), "exact named fields required: " + expected);
    }
    static List<JsonNode> array(JsonNode value) {
        require(value != null && value.isArray(), "array required");
        java.util.ArrayList<JsonNode> rows = new java.util.ArrayList<>(); value.forEach(rows::add); return List.copyOf(rows);
    }
    static RawJson encode(Object value) {
        try { return new RawJson(JSON.writeValueAsBytes(value)); }
        catch (IOException failure) { throw new IllegalArgumentException("typed JSON serialization failed", failure); }
    }
}


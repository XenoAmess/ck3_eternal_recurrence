package org.xar.ck3.control.application.effects;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** One strict token boundary; missing/null/empty, integer/bool/decimal remain distinct. */
final class EffectJson {
    private static final com.fasterxml.jackson.databind.ObjectMapper NATIVE_JSON = new com.fasterxml.jackson.databind.ObjectMapper(
            com.fasterxml.jackson.core.JsonFactory.builder().enable(com.fasterxml.jackson.core.StreamReadFeature.STRICT_DUPLICATE_DETECTION)
                    .streamReadConstraints(com.fasterxml.jackson.core.StreamReadConstraints.builder().maxStringLength(RawJson.MAXIMUM_BYTES)
                            .maxNumberLength(4300).maxNestingDepth(1000).build()).build())
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_INTEGER_FOR_INTS)
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.USE_BIG_DECIMAL_FOR_FLOATS)
            .enable(com.fasterxml.jackson.databind.DeserializationFeature.FAIL_ON_TRAILING_TOKENS);
    private EffectJson() { }
    static ObjectNode object(JsonNode value) {
        StrictJson.require(value instanceof ObjectNode, "actual Native object required"); return (ObjectNode) value;
    }
    static ObjectNode object(OpportunityJson.Obj value) { return object(parse(new RawJson(OpportunityJson.encode(value)))); }
    static JsonNode parse(RawJson value) {
        // RawJson already validates the exact UTF-8/token/duplicate domain. Keep the same explicit 64 MiB/4300-digit lane.
        // This application codec does not depend backwards on native-transport.
        try { return NATIVE_JSON.readTree(value.bytes()); }
        catch (java.io.IOException error) { throw new IllegalArgumentException("invalid original Native token", error); }
    }
    static BigInteger integer(JsonNode value) { return StrictJson.integer(value, BigInteger.valueOf(Long.MIN_VALUE), StrictJson.UINT64_MAX); }
    static long id(JsonNode value) { return StrictJson.integer(value, 1, Integer.MAX_VALUE); }
    static long nonnegative(JsonNode value) { return StrictJson.integer(value, 0, Integer.MAX_VALUE); }
    static boolean bool(JsonNode value) {
        StrictJson.require(value != null && value.isBoolean(), "actual JSON boolean required"); return value.booleanValue();
    }
    static List<JsonNode> rows(JsonNode value) {
        StrictJson.require(value != null && value.isArray() && value.size() <= 65536, "bounded actual Native rows required");
        java.util.ArrayList<JsonNode> result = new java.util.ArrayList<>(); value.forEach(row -> { object(row); result.add(row); });
        return List.copyOf(result);
    }
    static JsonNode unique(List<JsonNode> rows, String idField, long id) {
        Set<BigInteger> ids = new HashSet<>(); JsonNode selected = null;
        for (JsonNode row : rows) {
            BigInteger actual = integer(row.get(idField)); StrictJson.require(ids.add(actual), "duplicate Native full identity");
            if (actual.equals(BigInteger.valueOf(id))) selected = row;
        }
        return selected;
    }
    static RawJson raw(JsonNode value) { return new RawJson(StrictJson.canonical(value, StrictJson.EXPLICIT_MAX_BYTES)); }
}

package org.xar.ck3.control.wave2.events.eventmaterial;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** Narrow JSON boundary shared by the dedicated event materials. No coercions. */
final class MaterialJson {
    static final BigInteger I32 = BigInteger.valueOf(Integer.MAX_VALUE);
    static final BigInteger U32 = BigInteger.ONE.shiftLeft(32).subtract(BigInteger.ONE);
    static final BigInteger U64 = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);
    static final BigInteger I64_MIN = BigInteger.ONE.shiftLeft(63).negate();
    static final BigInteger I64_MAX = BigInteger.ONE.shiftLeft(63).subtract(BigInteger.ONE);
    private MaterialJson() { }
    static JsonNode get(JsonNode node, String name) { return node == null || node.isNull() ? null : object(node).get(name); }
    static JsonNode object(JsonNode node) {
        StrictJson.require(node != null && node.isObject(), "event material object required"); return node;
    }
    static JsonNode nullableObject(JsonNode node) { return node == null || node.isNull() ? null : object(node); }
    static BigInteger integer(JsonNode node, String name) {
        JsonNode value = get(node,name); if (value == null || value.isNull()) return null;
        StrictJson.require(value.isIntegralNumber(), "integer token required, no bool/float/string: " + name);
        return value.bigIntegerValue();
    }
    static String text(JsonNode node, String name) {
        JsonNode value = get(node,name); if (value == null || value.isNull()) return null;
        StrictJson.require(value.isTextual(), "string token required: " + name); return value.textValue();
    }
    static Boolean bool(JsonNode node, String name) {
        JsonNode value = get(node,name); if (value == null || value.isNull()) return null;
        StrictJson.require(value.isBoolean(), "boolean token required: " + name); return value.booleanValue();
    }
    static List<JsonNode> rows(JsonNode value) {
        if (value == null || value.isNull()) return null;
        StrictJson.require(value.isArray() && value.size() <= 16384, "bounded event material array required");
        List<JsonNode> rows = new ArrayList<>(); value.forEach(rows::add); return List.copyOf(rows);
    }
    static boolean range(BigInteger value, BigInteger min, BigInteger max) {
        return value != null && value.compareTo(min) >= 0 && value.compareTo(max) <= 0;
    }
    static boolean i32(BigInteger value, int minimum) { return range(value,BigInteger.valueOf(minimum),I32); }
    static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    static boolean nonempty(String value) { return value != null && !value.isEmpty(); }
    static boolean equal(Object left, Object right) { return Objects.equals(left,right); }
    static boolean newer(BigInteger after, BigInteger before) { return after != null && before != null && after.compareTo(before) > 0; }
    static void exact(JsonNode node, Set<String> fields) { StrictJson.object(node,fields); }
    static ObjectNode base(String event, int nativeIndex, String metric, String relation) {
        return StrictJson.object().put("schema","xar.ck3.vanilla-event-material-postcondition").put("schema_version",1)
            .put("event_definition_key",event).put("selected_option_number",nativeIndex+1).put("selected_native_option_index",nativeIndex)
            .put("metric",metric).put("expected_relation",relation).put("material_change_required_for_evidence",true);
    }
    static void validateBase(JsonNode node, String event, int nativeIndex, String metric, String relation) {
        StrictJson.require("xar.ck3.vanilla-event-material-postcondition".equals(text(node,"schema"))
            && BigInteger.ONE.equals(integer(node,"schema_version")) && event.equals(text(node,"event_definition_key"))
            && BigInteger.valueOf(nativeIndex+1L).equals(integer(node,"selected_option_number"))
            && BigInteger.valueOf(nativeIndex).equals(integer(node,"selected_native_option_index"))
            && metric.equals(text(node,"metric")) && relation.equals(text(node,"expected_relation"))
            && Boolean.TRUE.equals(bool(node,"material_change_required_for_evidence")), "exact reviewed material identity required");
    }
    static void nullable(ObjectNode node, String name, Boolean value) { if(value==null)node.putNull(name);else node.put(name,value); }
    static void sameJson(JsonNode raw, byte[] encoded) {
        StrictJson.require(raw.equals(StrictJson.parse(encoded)), "material canonical fields or binding differ");
    }
}

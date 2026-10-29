package org.xar.ck3.control.application.lifecycle;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HexFormat;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;

/** One strict JSON integer/decimal domain for original lifecycle business values. */
final class LifecycleJson {
    private LifecycleJson() { }
    static ObjectNode parse(byte[] raw, int limit) {
        return object(org.xar.ck3.control.contracts.FullJsonTree.parse(raw,limit));
    }
    static ObjectNode object(JsonNode value) { StrictJson.require(value instanceof ObjectNode, "lifecycle object required"); return (ObjectNode)value; }
    static ObjectNode row() { return com.fasterxml.jackson.databind.node.JsonNodeFactory.instance.objectNode(); }
    static byte[] bytes(JsonNode value) { return org.xar.ck3.control.contracts.FullJsonTree.encode(value,org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES); }
    static String sha(byte[] raw) { try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw)); } catch (NoSuchAlgorithmException impossible) { throw new IllegalStateException(impossible); } }
    static String text(JsonNode value) { return StrictJson.text(value); }
    static BigInteger integer(JsonNode value, BigInteger minimum) {
        StrictJson.require(value != null && value.isIntegralNumber(), "integer token required");
        BigInteger result = value.bigIntegerValue(); StrictJson.require(result.compareTo(minimum) >= 0, "integer below minimum"); return result;
    }
    static boolean bool(JsonNode value) { StrictJson.require(value != null && value.isBoolean(), "boolean token required"); return value.booleanValue(); }
    static void exact(ObjectNode row, Set<String> keys) { var actual = new java.util.HashSet<String>(); row.fieldNames().forEachRemaining(actual::add); StrictJson.require(actual.equals(keys), "lifecycle fields differ: " + actual); }
    static boolean same(JsonNode left, JsonNode right) {
        if (left == null || right == null) return left == right;
        if (left.isIntegralNumber() && right.isIntegralNumber()) return left.bigIntegerValue().equals(right.bigIntegerValue());
        if (left.isNumber() && right.isNumber()) return left.decimalValue().compareTo(right.decimalValue()) == 0;
        if (left.isObject() && right.isObject()) {
            if (left.size() != right.size()) return false;
            for (var entry : left.properties()) if (!same(entry.getValue(), right.get(entry.getKey()))) return false;
            return true;
        }
        if (left.isArray() && right.isArray()) {
            if (left.size() != right.size()) return false;
            for (int i=0;i<left.size();i++) if (!same(left.get(i),right.get(i))) return false;
            return true;
        }
        return left.equals(right);
    }
    static org.xar.ck3.control.planning.opportunity.OpportunityJson.Value immutable(JsonNode value) {
        return org.xar.ck3.control.application.driver.DriverJson.fromNormalizedNode(value);
    }
}

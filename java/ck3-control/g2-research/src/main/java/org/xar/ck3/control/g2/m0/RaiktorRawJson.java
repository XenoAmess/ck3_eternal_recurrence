package org.xar.ck3.control.g2.m0;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;

/** Narrow runtime validation shared only by the actual M0 producer boundary. */
final class RaiktorRawJson {
    private RaiktorRawJson() { }
    static ObjectNode object(JsonNode value, String name) {
        require(value instanceof ObjectNode, name + " must be an object");
        return (ObjectNode) value;
    }
    static ObjectNode exact(JsonNode value, Set<String> keys, String name) {
        ObjectNode row = object(value, name);
        Set<String> actual = new HashSet<>();
        row.fieldNames().forEachRemaining(actual::add);
        require(actual.equals(keys), name + " keys differ");
        return row;
    }
    static String text(JsonNode value, String name) {
        require(value != null && value.isTextual() && !value.textValue().strip().isEmpty(),
                name + " must be a nonempty string");
        return value.textValue();
    }
    static boolean bool(JsonNode value, String name) {
        require(value != null && value.isBoolean(), name + " must be a boolean");
        return value.booleanValue();
    }
    static BigInteger integer(JsonNode value, String name) {
        require(value != null && value.isIntegralNumber(), name + " must be an integer");
        return value.bigIntegerValue();
    }
    static long number(JsonNode value, long low, long high, String name) {
        BigInteger number = integer(value, name);
        require(number.compareTo(BigInteger.valueOf(low)) >= 0
                && number.compareTo(BigInteger.valueOf(high)) <= 0, name + " outside integer range");
        return number.longValueExact();
    }
    static int i32(JsonNode value, String name) {
        return Math.toIntExact(number(value, Integer.MIN_VALUE, Integer.MAX_VALUE, name));
    }
    static int positive32(JsonNode value, String name) {
        return Math.toIntExact(number(value, 1, Integer.MAX_VALUE, name));
    }
    static int fullId(JsonNode value, String name) {
        int id = i32(value, name); require(id != -1, name + " is the invalid full-generation ID"); return id;
    }
    static long positive64(JsonNode value, String name) { return number(value, 1, Long.MAX_VALUE, name); }
    static long nonnegative(JsonNode value, String name) { return number(value, 0, Long.MAX_VALUE, name); }
    static ArrayNode array(JsonNode value, String name) {
        require(value instanceof ArrayNode, name + " must be an array");
        return (ArrayNode) value;
    }
    static List<String> strings(JsonNode value, String name) {
        List<String> result = new ArrayList<>();
        for (JsonNode item : array(value, name)) result.add(text(item, name + "[]"));
        return List.copyOf(result);
    }
    static void strings(ObjectNode row, String key, List<String> values) {
        ArrayNode array = row.putArray(key); values.forEach(array::add);
    }
    static String sha(JsonNode value, String name) {
        String text = text(value, name); require(text.matches("[0-9A-F]{64}"), name + " must be uppercase SHA-256");
        return text;
    }
    static String hash(JsonNode value) {
        byte[] raw = RaiktorExitObservationCodec.encodeWire(value);
        return RetainedJson.pythonCanonical(RetainedJson.parse(raw),
                new RetainedJson.CanonicalBudget(StrictJson.EXPLICIT_MAX_BYTES, 100_000, 128))
                .sha256().toUpperCase(Locale.ROOT);
    }
    static boolean same(JsonNode left, JsonNode right) {
        if (left == null || right == null) return false;
        if (left.isIntegralNumber() && right.isIntegralNumber()) return left.bigIntegerValue().equals(right.bigIntegerValue());
        if (left.isArray() && right.isArray()) {
            if (left.size() != right.size()) return false;
            for (int index = 0; index < left.size(); index++) if (!same(left.get(index), right.get(index))) return false;
            return true;
        }
        if (left.isObject() && right.isObject()) {
            if (left.size() != right.size()) return false;
            var fields = left.fields();
            while (fields.hasNext()) { var entry = fields.next(); if (!same(entry.getValue(), right.get(entry.getKey()))) return false; }
            return true;
        }
        return left.equals(right);
    }
    static JsonNode copy(JsonNode value) { return value == null ? null : value.deepCopy(); }
}

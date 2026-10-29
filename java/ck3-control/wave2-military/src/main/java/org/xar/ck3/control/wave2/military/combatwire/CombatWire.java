package org.xar.ck3.control.wave2.military.combatwire;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.JsonNodeFactory;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** The sole dynamic JSON boundary for exact combat input contracts. */
public final class CombatWire {
    private CombatWire() { }
    public static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }
    public static ObjectNode object(JsonNode value, Set<String> required, Set<String> optional, String name) {
        require(value instanceof ObjectNode, "native " + name + " schema is malformed");
        ObjectNode row = (ObjectNode) value;
        Set<String> keys = new HashSet<>(); row.fieldNames().forEachRemaining(keys::add);
        Set<String> permitted = new HashSet<>(required); permitted.addAll(optional);
        require(keys.containsAll(required) && permitted.containsAll(keys), "native " + name + " schema is malformed");
        return row;
    }
    public static ObjectNode object(JsonNode value, String keys, String name) {
        return object(value, Set.of(keys.split(" ")), Set.of(), name);
    }
    public static ArrayNode array(JsonNode value, String name) {
        require(value instanceof ArrayNode, "native " + name + " must be an array"); return (ArrayNode) value;
    }
    public static boolean nil(JsonNode value) { return value == null || value.isNull(); }
    public static String text(JsonNode value, String name) {
        require(value != null && value.isTextual() && !value.textValue().isEmpty(), "native " + name + " must be a non-empty string"); return value.textValue();
    }
    public static String nullableText(JsonNode value, String name) { return nil(value) ? null : text(value, name); }
    public static String token(JsonNode value, String name, String... values) {
        require(value != null && value.isTextual() && List.of(values).contains(value.textValue()), "native " + name + " is malformed"); return value.textValue();
    }
    public static boolean bool(JsonNode value, String name) {
        require(value != null && value.isBoolean(), "native " + name + " must be boolean"); return value.booleanValue();
    }
    public static long integer(JsonNode value, int bits, long minimum, String name) {
        BigInteger max = BigInteger.ONE.shiftLeft(bits - 1).subtract(BigInteger.ONE);
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().compareTo(BigInteger.valueOf(minimum)) >= 0
            && value.bigIntegerValue().compareTo(max) <= 0, "native " + name + " must be signed int" + bits);
        return value.longValue();
    }
    public static int i32(JsonNode value, String name) { return (int) integer(value, 32, Integer.MIN_VALUE, name); }
    public static int nonnegative(JsonNode value, String name) { int n = i32(value, name); require(n >= 0, "native " + name + " must be non-negative"); return n; }
    public static int positive(JsonNode value, String name) { int n = i32(value, name); require(n > 0, name + " must be a positive signed int32"); return n; }
    public static long i64(JsonNode value, String name) { return integer(value, 64, Long.MIN_VALUE, name); }
    public static long nonnegative64(JsonNode value, String name) { long n = i64(value,name); require(n >= 0, "native " + name + " must be non-negative"); return n; }
    public static Integer optionalInt(JsonNode value, boolean positive, String name) { return nil(value) ? null : positive ? positive(value,name) : nonnegative(value,name); }
    public static Long conditional(JsonNode value, boolean available, int bits, boolean nonnegative, boolean positive, String name) {
        if (!available) { require(nil(value), "native " + name + " must be null when unavailable"); return null; }
        if (bits == 32) return (long) (positive ? positive(value,name) : nonnegative ? nonnegative(value,name) : i32(value,name));
        return nonnegative ? nonnegative64(value,name) : i64(value,name);
    }
    public static void conditionalField(ObjectNode row, String field, boolean available, int bits, boolean nonnegative, boolean positive, String name) {
        conditional(row.get(field), available, bits, nonnegative, positive, name + "." + field);
    }
    public static void scale(JsonNode value, String name) {
        require(value != null && value.isIntegralNumber() && value.bigIntegerValue().equals(BigInteger.valueOf(100000)), "native " + name + " must be 100000");
    }
    public static String status(ObjectNode row, boolean absent, String name) {
        return absent ? token(row.get("status"), name + ".status", "available", "absent", "unavailable")
            : token(row.get("status"), name + ".status", "available", "unavailable");
    }
    public static String reason(String status, JsonNode value, String name) {
        if (status.equals("unavailable")) return text(value,name + ".unavailable_reason");
        require(nil(value), "native " + name + ".unavailable_reason must be null"); return null;
    }
    public static String statusAndReason(ObjectNode row, boolean absent, String name) {
        String status = status(row,absent,name); reason(status,row.get("unavailable_reason"),name); return status;
    }
    public static List<Integer> ids(JsonNode value, boolean positive, boolean nonempty, String name) {
        ArrayNode list = array(value,name); require(!nonempty || !list.isEmpty(), name + " must be a nonempty list");
        List<Integer> result = new ArrayList<>(); Set<Integer> seen = new HashSet<>();
        for (int i=0;i<list.size();i++) { int id = positive ? positive(list.get(i), name + "[" + i + "]") : nonnegative(list.get(i), name + "[" + i + "]");
            require(seen.add(id), "native " + name + " contains duplicate IDs"); result.add(id); }
        return List.copyOf(result);
    }
    public static List<String> strings(JsonNode value, String name) {
        List<String> result = new ArrayList<>(); ArrayNode list = array(value,name);
        for(int i=0;i<list.size();i++) result.add(text(list.get(i),name+"["+i+"]")); return List.copyOf(result);
    }
    public static void eq(JsonNode value, String expected, String message) {
        require(value != null && value.isTextual() && value.textValue().equals(expected), message);
    }
    public static ObjectNode empty() { return JsonNodeFactory.instance.objectNode(); }
    public static ArrayNode jsonIds(List<Integer> ids) { ArrayNode row=JsonNodeFactory.instance.arrayNode(); ids.forEach(row::add); return row; }
}


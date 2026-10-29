package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/** Narrow immutable JSON helpers for the existing source-review contract. */
final class SourceReviewJson {
    private SourceReviewJson() { }
    record Field(String name, Value value) { }
    static Field f(String name, Value value) { return new Field(name, value); }
    static ObjectValue obj(Field... fields) {
        Map<String, Value> values = new LinkedHashMap<>();
        for (Field field : fields) values.put(field.name(), Objects.requireNonNull(field.value()));
        return new ObjectValue(values);
    }
    static ObjectValue put(ObjectValue original, Field... fields) {
        ObjectValue value = original;
        for (Field field : fields) value = value.with(field.name(), field.value());
        return value;
    }
    static Value s(String value) { return RetainedJson.value(value); }
    static Value i(long value) { return new IntegerValue(BigInteger.valueOf(value)); }
    static Value b(boolean value) { return new BooleanValue(value); }
    static ObjectValue o(Value value) { return value instanceof ObjectValue object ? object : null; }
    static ObjectValue o(ObjectValue value, String key) { return value == null ? null : o(value.get(key)); }
    static Value v(ObjectValue value, String key) { return value == null ? NULL : value.getOrNull(key); }
    static String text(ObjectValue value, String key) { return RetainedJson.string(v(value, key)); }
    static BigInteger number(ObjectValue value, String key) { return RetainedJson.integer(v(value, key)); }
    static boolean yes(ObjectValue value, String key) { return Boolean.TRUE.equals(RetainedJson.bool(v(value, key))); }
    static boolean eq(ObjectValue value, String key, Value expected) { return v(value, key).equals(expected); }
    static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    static List<Value> array(ObjectValue value, String key) {
        Value raw = v(value, key); require(raw instanceof ArrayValue, "array required: " + key); return ((ArrayValue) raw).values();
    }
    static List<ObjectValue> objects(ObjectValue value, String key) {
        List<ObjectValue> rows = new ArrayList<>();
        for (Value row : array(value, key)) { require(row instanceof ObjectValue, "object row required: " + key); rows.add((ObjectValue) row); }
        return List.copyOf(rows);
    }
    static Map<String, ObjectValue> roles(ObjectValue context, boolean unique, boolean identifiers) {
        Map<String, ObjectValue> result = new LinkedHashMap<>();
        for (ObjectValue row : objects(context, "saved_scopes")) {
            String name = text(row, "name"); require(name != null, "saved role name required");
            if (identifiers) require(positive(number(row, "name_identifier")), "saved role identifier required");
            if (unique) require(!result.containsKey(name), "saved role name duplicated");
            result.put(name, row);
        }
        return result;
    }
    static BigInteger identity(ObjectValue scope, String kind, String field) {
        ObjectValue identity = o(scope, "typed_identity");
        if (!eq(scope, "status", s("available")) || !eq(scope, "type_key", s(kind))
                || !eq(identity, "status", s("available")) || !eq(identity, "kind", s(kind))) return null;
        BigInteger value = number(identity, field); return positive(value) ? value : null;
    }
    static String sha(byte[] bytes) {
        try { return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)); }
        catch (NoSuchAlgorithmException error) { throw new IllegalStateException(error); }
    }
    static String fingerprint(Value value) { return sha(canonical(value).getBytes(StandardCharsets.UTF_8)); }
    /** Original json.dumps(sort_keys=True, separators=(",", ":")), including ensure_ascii=True. */
    static String canonical(Value value) {
        return switch (value) {
            case NullValue ignored -> "null";
            case BooleanValue flag -> flag.value() ? "true" : "false";
            case IntegerValue integer -> integer.value().toString();
            case StringValue string -> quote(string.value());
            case ArrayValue array -> "[" + String.join(",", array.values().stream().map(SourceReviewJson::canonical).toList()) + "]";
            case ObjectValue object -> {
                List<String> fields = new ArrayList<>();
                object.fields().keySet().stream().sorted(CODE_POINTS).forEach(key -> fields.add(quote(key) + ":" + canonical(object.get(key))));
                yield "{" + String.join(",", fields) + "}";
            }
            case FloatingValue ignored -> throw new IllegalArgumentException("source-review binding and option facts cannot contain floating identities");
        };
    }
    private static String quote(String value) {
        StringBuilder result = new StringBuilder("\""); String hex = "0123456789abcdef";
        for (int index = 0; index < value.length(); index++) {
            char current = value.charAt(index);
            switch (current) {
                case '"' -> result.append("\\\""); case '\\' -> result.append("\\\\");
                case '\b' -> result.append("\\b"); case '\f' -> result.append("\\f");
                case '\n' -> result.append("\\n"); case '\r' -> result.append("\\r"); case '\t' -> result.append("\\t");
                default -> {
                    if (current < 0x20 || current >= 0x7f) {
                        result.append("\\u").append(hex.charAt((current >>> 12) & 15)).append(hex.charAt((current >>> 8) & 15))
                            .append(hex.charAt((current >>> 4) & 15)).append(hex.charAt(current & 15));
                    } else result.append(current);
                }
            }
        }
        return result.append('"').toString();
    }
    private static final Comparator<String> CODE_POINTS = (left, right) -> {
        int a = 0, c = 0;
        while (a < left.length() && c < right.length()) {
            int x = left.codePointAt(a), y = right.codePointAt(c);
            if (x != y) return Integer.compare(x, y);
            a += Character.charCount(x); c += Character.charCount(y);
        }
        return Integer.compare(left.length() - a, right.length() - c);
    };
    static void require(boolean condition, String message) { if (!condition) throw new IllegalArgumentException(message); }
}

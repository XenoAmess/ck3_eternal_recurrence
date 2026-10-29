package org.xar.ck3.control.wave2.events.registered;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;

/** Narrow immutable JSON boundary; numeric identities never coerce bool, float, or text. */
final class RegistryJson {
    private RegistryJson() { }
    static final ObjectValue EMPTY = new ObjectValue(Map.of());
    static Value get(Value value, String name) { return value instanceof ObjectValue object ? object.getOrNull(name) : RetainedJson.NULL; }
    static ObjectValue obj(Value value) { return value instanceof ObjectValue object ? object : EMPTY; }
    static List<Value> seq(Value value) { return value instanceof ArrayValue array ? array.values() : List.of(); }
    static boolean array(Value value) { return value instanceof ArrayValue; }
    static boolean object(Value value) { return value instanceof ObjectValue; }
    static String text(Value value) { return value instanceof StringValue string ? string.value() : null; }
    static String str(Value value) { String result = text(value); return result == null ? "" : result; }
    static BigInteger integer(Value value) { return value instanceof IntegerValue number ? number.value() : null; }
    static boolean positive(Value value) { BigInteger number = integer(value); return number != null && number.signum() > 0; }
    static boolean eq(Value left, Value right) { return Objects.equals(left == null ? RetainedJson.NULL : left, right == null ? RetainedJson.NULL : right); }
    static boolean is(Value value, String expected) { return expected.equals(text(value)); }
    static boolean is(Value value, long expected) { return BigInteger.valueOf(expected).equals(integer(value)); }
    static boolean yes(Value value) { return value instanceof BooleanValue bool && bool.value(); }
    static boolean no(Value value) { return value instanceof BooleanValue bool && !bool.value(); }
    static boolean nil(Value value) { return value == null || value instanceof NullValue; }
    static boolean active(Value value) {
        return !nil(value) && !no(value) && !is(value, 0)
                && !(value instanceof FloatingValue number && number.value() == 0)
                && !(value instanceof ArrayValue array && array.values().isEmpty())
                && !(value instanceof ObjectValue object && object.fields().isEmpty());
    }
    static Value v(String value) { return RetainedJson.value(value); }
    static Value v(BigInteger value) { return RetainedJson.value(value); }
    static Value v(long value) { return v(BigInteger.valueOf(value)); }
    static Value v(boolean value) { return new BooleanValue(value); }
    static ArrayValue arr(List<? extends Value> values) { return new ArrayValue(new ArrayList<>(values)); }
    static ArrayValue arr(Value... values) { return new ArrayValue(List.of(values)); }
    static Value json(String value) { return RetainedJson.parse(value.getBytes(StandardCharsets.UTF_8)); }
    static ObjectValue jsonObject(String value) { return RetainedJson.object(json(value)); }
    static ObjectValue remove(ObjectValue value, String name) { var copy = new LinkedHashMap<>(value.fields()); copy.remove(name); return new ObjectValue(copy); }
    static ObjectValue merge(ObjectValue left, ObjectValue right) { var copy = new LinkedHashMap<>(left.fields()); copy.putAll(right.fields()); return new ObjectValue(copy); }
    static Set<Value> values(Value value) { return new LinkedHashSet<>(seq(value)); }
    static Set<String> names(Value value) { return obj(value).fields().keySet(); }
    static Map<String, Value> scopes(Value context) {
        Map<String, Value> result = new LinkedHashMap<>();
        for (Value row : seq(get(context, "saved_scopes"))) {
            String name = text(get(row, "name"));
            if (object(row) && name != null) result.put(name, get(row, "scope"));
        }
        return result;
    }
    static BigInteger character(Value value) {
        Value identity = get(value, "typed_identity"); Value id = get(identity, "character_id");
        return is(get(value, "status"), "available") && is(get(value, "type_key"), "character")
                && is(get(identity, "status"), "available") && is(get(identity, "kind"), "character") && positive(id) ? integer(id) : null;
    }
    static Value materialize(Value value, BigInteger player) {
        if (is(value, "$player")) return v(player);
        if (value instanceof ArrayValue array) return arr(array.values().stream().map(item -> materialize(item, player)).toList());
        if (value instanceof ObjectValue object) {
            Map<String, Value> copy = new LinkedHashMap<>(); object.fields().forEach((key,item) -> copy.put(key, materialize(item, player))); return new ObjectValue(copy);
        }
        return value;
    }
    static boolean all(Map<String, Boolean> checks) { return checks.values().stream().allMatch(Boolean::booleanValue); }
    static ObjectValue checks(Map<String, Boolean> checks) { Map<String,Value> result = new LinkedHashMap<>(); checks.forEach((key,value) -> result.put(key,v(value))); return new ObjectValue(result); }
    static ArrayValue failed(Map<String, Boolean> checks) { return arr(checks.entrySet().stream().filter(row -> !row.getValue()).map(Map.Entry::getKey).sorted().map(RegistryJson::v).toList()); }
    static ObjectValue onlyPresent(ObjectValue fields, Set<String> names) {
        Map<String,Value> copy = new LinkedHashMap<>(); fields.fields().forEach((key,value) -> { if (names.contains(key)) copy.put(key,value); }); return new ObjectValue(copy);
    }
    static final class Builder {
        private final Map<String,Value> fields = new LinkedHashMap<>();
        Builder set(String key, Value value) { fields.put(key,value == null ? RetainedJson.NULL : value); return this; }
        Builder set(String key, String value) { return set(key,v(value)); }
        Builder set(String key, long value) { return set(key,v(value)); }
        Builder set(String key, BigInteger value) { return set(key,v(value)); }
        Builder set(String key, boolean value) { return set(key,v(value)); }
        ObjectValue build() { return new ObjectValue(fields); }
    }
    static Builder b() { return new Builder(); }
}

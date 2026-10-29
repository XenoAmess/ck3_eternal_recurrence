package org.xar.ck3.control.application.planning.warentry;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Narrow JSON boundary. Missing values stay absent until an explicit projection asks for null. */
final class WarEntryJson {
    private WarEntryJson() { }
    static Obj object(Value value) { return value instanceof Obj object ? object : null; }
    static Obj child(Obj value, String key) { return value == null ? null : object(value.get(key)); }
    static Value get(Obj value, String key) { return value == null ? null : value.get(key); }
    static Value nullable(Value value) { return value == null ? Nil.INSTANCE : value; }
    static List<Value> array(Value value) { return value instanceof Arr array ? array.items() : List.of(); }
    static List<Obj> objects(Value value) { return array(value).stream().filter(Obj.class::isInstance).map(Obj.class::cast).toList(); }
    static String text(Value value) { return value instanceof Text text ? text.value() : null; }
    static boolean is(Value value, String text) { return value instanceof Text actual && actual.value().equals(text); }
    static boolean yes(Value value) { return value instanceof Bool bool && bool.value(); }
    static boolean no(Value value) { return value instanceof Bool bool && !bool.value(); }
    static BigInteger integer(Value value) { return value instanceof IntegerValue number ? number.value() : null; }
    static BigInteger number(Obj object, String key) { return integer(get(object, key)); }
    static BigInteger required(Obj object, String key) { return Objects.requireNonNull(number(object, key), "integer required: " + key); }
    static boolean positive(Value value) { BigInteger n = integer(value); return n != null && n.signum() > 0; }
    static boolean eq(Value value, long expected) { return BigInteger.valueOf(expected).equals(integer(value)); }
    static boolean same(Value left, Value right) { return Objects.equals(left, right); }
    static Arr strings(List<String> values) { return new Arr(values.stream().map(Text::new).map(Value.class::cast).toList()); }
    static Arr rows(List<Obj> values) { return new Arr(new ArrayList<>(values)); }
    static Arr numbers(List<BigInteger> values) { return new Arr(values.stream().map(IntegerValue::new).map(Value.class::cast).toList()); }
    static Obj project(Obj source, String... keys) { Builder b = obj(); for (String key : keys) b.value(key, get(source, key)); return b.build(); }
    static Obj parse(byte[] raw) { return OpportunityJson.object(OpportunityJson.parse(raw), "war-entry object"); }
    static Builder obj() { return new Builder(); }
    static final class Builder {
        private final Map<String, Value> values = new LinkedHashMap<>();
        Builder value(String key, Value value) { values.put(key, nullable(value)); return this; }
        Builder text(String key, String value) { return value(key, value == null ? Nil.INSTANCE : new Text(value)); }
        Builder number(String key, BigInteger value) { return value(key, value == null ? Nil.INSTANCE : new IntegerValue(value)); }
        Builder number(String key, long value) { return number(key, BigInteger.valueOf(value)); }
        Builder bool(String key, boolean value) { return value(key, new Bool(value)); }
        Builder decimal(String key, double value) { return value(key, new DecimalValue(Double.toString(value))); }
        Builder merge(Obj object) { values.putAll(object.members()); return this; }
        Obj build() { return new Obj(values); }
    }
}

package org.xar.ck3.control.application.capabilities;

import static org.xar.ck3.control.contracts.StrictJson.require;
import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Objects;
import java.util.Optional;

/** Narrow, typed JSON inspection shared by the capability boundary and its factual selectors. */
final class CapabilityJson {
    static final BigInteger INT32_MAX = BigInteger.valueOf(Integer.MAX_VALUE);
    private CapabilityJson() { }
    static Optional<Obj> obj(Value value) { return value instanceof Obj row ? Optional.of(row) : Optional.empty(); }
    static boolean yes(Obj row, String field) { return row != null && new Bool(true).equals(row.get(field)); }
    static boolean no(Obj row, String field) { return row != null && new Bool(false).equals(row.get(field)); }
    static boolean nil(Obj row, String field) { return row != null && (row.get(field) == null || row.get(field) == Nil.INSTANCE); }
    static String textOrNull(Obj row, String field) { return row != null && row.get(field) instanceof Text s ? s.value() : null; }
    static String lower(Obj row, String field) { String s = textOrNull(row, field); return s == null ? null : s.toLowerCase(Locale.ROOT); }
    static Optional<BigInteger> number(Value value) { return value instanceof IntegerValue i ? Optional.of(i.value()) : Optional.empty(); }
    static boolean positive(Value value) { return value instanceof IntegerValue i && i.value().signum() > 0; }
    static boolean int32Id(Value value) { return positive(value) && ((IntegerValue)value).value().compareTo(INT32_MAX) <= 0; }
    static boolean unitId(Value value) { return value instanceof IntegerValue i && i.value().signum() >= 0 && i.value().compareTo(INT32_MAX) <= 0; }
    static BigInteger integerAt(Obj row, String field) { return integer(row.get(field), field); }
    static int idAt(Obj row, String field) { require(int32Id(row.get(field)), "positive int32 identity required: " + field); return integerAt(row,field).intValueExact(); }
    static boolean eq(Obj row, String field, Value expected) { return row != null && Objects.equals(row.get(field), expected); }
    static boolean equalField(Obj a, String aKey, Obj b, String bKey) {
        return a != null && b != null && a.members().containsKey(aKey) && b.members().containsKey(bKey) && Objects.equals(a.get(aKey), b.get(bKey));
    }
    static boolean named(Obj row, String key, String expected) { return expected.equals(textOrNull(row,key)); }
    static boolean emptyArray(Obj row, String key) { return row != null && row.get(key) instanceof Arr a && a.items().isEmpty(); }
    static Optional<List<Value>> arrayOrEmpty(Value value) { return value instanceof Arr a ? Optional.of(a.items()) : Optional.empty(); }
    static List<Obj> rows(Value value) {
        if (!(value instanceof Arr a)) return List.of();
        List<Obj> rows = new ArrayList<>();
        for (Value item : a.items()) if (item instanceof Obj row) rows.add(row);
        return List.copyOf(rows);
    }
    static List<Obj> requiredRows(Obj row, String field) {
        List<Value> array = array(row.get(field),field);
        List<Obj> result = new ArrayList<>();
        for (Value item : array) result.add(object(item,field + "[]"));
        return List.copyOf(result);
    }
    static List<Integer> requiredIds(Value raw, boolean publicUnits) {
        List<Integer> ids = new ArrayList<>();
        for (Value value : array(raw,"identity array")) {
            require(publicUnits ? unitId(value) : int32Id(value),"canonical integer identities required");
            ids.add(integer(value,"identity").intValueExact());
        }
        return List.copyOf(ids);
    }
    static Arr integers(List<Integer> values) { return new Arr(values.stream().map(v -> (Value)new IntegerValue(BigInteger.valueOf(v))).toList()); }
    static Value present(Obj row, String key) { require(row.members().containsKey(key), "missing capability field: " + key); return row.get(key); }
}

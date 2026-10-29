package org.xar.ck3.control.wave3.governance.betrothalvalue;

import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** One narrow JSON evidence boundary; no coercion and no untyped Java object maps. */
final class ValueFields {
    private ValueFields() { }
    static WireValue get(ObjectValue object, String key) { return object.values().getOrDefault(key, NullValue.INSTANCE); }
    static boolean nil(WireValue value) { return value == null || value == NullValue.INSTANCE; }
    static ObjectValue object(WireValue value) { require(value instanceof ObjectValue, "object required"); return (ObjectValue) value; }
    static String text(WireValue value) { require(value instanceof TextValue, "string required"); return ((TextValue) value).value(); }
    static String nullableText(WireValue value) { return nil(value) ? null : text(value); }
    static BigInteger integer(WireValue value) { require(value instanceof IntegerValue, "exact integer token required"); return ((IntegerValue) value).value(); }
    static BigInteger nullableInteger(WireValue value) { return nil(value) ? null : integer(value); }
    static boolean bool(WireValue value) { require(value instanceof BooleanValue, "boolean token required"); return ((BooleanValue) value).value(); }
    static Boolean nullableBoolean(WireValue value) { return nil(value) ? null : bool(value); }
    static BigInteger signed(WireValue value, int bits) {
        BigInteger number = integer(value); require(number.bitLength() <= bits - 1, "signed integer out of range"); return number;
    }
    static BigInteger character(WireValue value) {
        if (nil(value)) { return null; }
        BigInteger number = integer(value); require(number.signum() > 0 && number.bitLength() <= 31, "CharacterID out of range"); return number;
    }
    static List<BigInteger> characters(WireValue value) {
        require(value instanceof ArrayValue, "CharacterID array required");
        List<BigInteger> result = new ArrayList<>();
        for (WireValue item : ((ArrayValue) value).values()) { BigInteger id = character(item); require(id != null, "null CharacterID"); result.add(id); }
        return List.copyOf(result);
    }
    static boolean positive(BigInteger number) { return number != null && number.signum() > 0; }
    static WireValue wire(BigInteger number) { return number == null ? NullValue.INSTANCE : new IntegerValue(number); }
    static WireValue wire(Boolean value) { return value == null ? NullValue.INSTANCE : new BooleanValue(value); }
    static ObjectValue empty() { return new ObjectValue(Map.of()); }
    static void require(boolean condition, String message) { if (!condition) { throw new ProjectionDomainRejection(message); } }
}

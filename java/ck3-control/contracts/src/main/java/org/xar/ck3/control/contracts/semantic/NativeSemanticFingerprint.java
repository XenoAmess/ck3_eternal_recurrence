package org.xar.ck3.control.contracts.semantic;

import com.fasterxml.jackson.databind.JsonNode;
import java.math.BigDecimal;
import java.math.BigInteger;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Python semantic-dictionary equality for revision comparison only; never an input type validator. */
public final class NativeSemanticFingerprint {
    private NativeSemanticFingerprint() { }
    public static boolean equivalent(JsonNode first, JsonNode second) {
        return second != null && compare(Objects.requireNonNull(first), second, 0);
    }
    private static boolean compare(JsonNode first, JsonNode second, int depth) {
        StrictJson.require(depth <= 64, "bounded semantic fingerprint required");
        if (numeric(first) && numeric(second)) return numbers(first, second);
        if (first.isObject() && second.isObject()) {
            if (first.size() != second.size()) return false;
            var names = first.fieldNames();
            while (names.hasNext()) {
                String name = names.next();
                if (!second.has(name) || !compare(first.get(name), second.get(name), depth + 1)) return false;
            }
            return true;
        }
        if (first.isArray() && second.isArray()) {
            if (first.size() != second.size()) return false;
            for (int index = 0; index < first.size(); index++)
                if (!compare(first.get(index), second.get(index), depth + 1)) return false;
            return true;
        }
        return first.equals(second);
    }
    private static boolean numeric(JsonNode value) { return value.isNumber() || value.isBoolean(); }
    private static BigInteger integer(JsonNode value) {
        return value.isBoolean() ? (value.booleanValue() ? BigInteger.ONE : BigInteger.ZERO) : value.bigIntegerValue();
    }
    private static boolean numbers(JsonNode first, JsonNode second) {
        boolean firstFloat = first.isFloatingPointNumber(), secondFloat = second.isFloatingPointNumber();
        if (!firstFloat && !secondFloat) return integer(first).equals(integer(second));
        if (firstFloat && secondFloat) return first.doubleValue() == second.doubleValue();
        JsonNode floating = firstFloat ? first : second;
        BigInteger exactInteger = integer(firstFloat ? second : first);
        double rounded = floating.doubleValue();
        // Python compares int with the exact binary64 value, not a rounded conversion of the int.
        if (!Double.isFinite(rounded) || rounded != Math.rint(rounded)) return false;
        return new BigDecimal(rounded).toBigIntegerExact().equals(exactInteger);
    }
}

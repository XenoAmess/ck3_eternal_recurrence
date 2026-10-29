package org.xar.ck3.control.contracts;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.util.Objects;

/** Public DATA representation only; parsing an integer grants no source or execution authority. */
public final class PublicUnsigned64 {
    public static final BigInteger MAXIMUM = new BigInteger("18446744073709551615");
    public static final BigInteger MAXIMUM_SAFE_NUMBER = new BigInteger("9007199254740991");
    public enum Minimum { ZERO, ONE }
    public enum NumericInput { SAFE_INTEGER_OR_DECIMAL, DECIMAL_ONLY }
    public sealed interface Field permits Missing, NullValue, Value { }
    public record Missing() implements Field { }
    public record NullValue() implements Field { }
    public record Value(BigInteger value) implements Field {
        public Value { validate(value, Minimum.ZERO); }
    }
    private PublicUnsigned64() { }

    /** Retains the syntactic absence/null distinction; required/nullable policy belongs to the owner. */
    public static Field read(ObjectNode object, String field, Minimum minimum, NumericInput numbers) {
        Objects.requireNonNull(object); Objects.requireNonNull(field);
        Objects.requireNonNull(minimum); Objects.requireNonNull(numbers);
        if (!object.has(field)) return new Missing();
        if (object.get(field).isNull()) return new NullValue();
        return new Value(parse(object.get(field), minimum, numbers));
    }

    public static BigInteger parse(JsonNode token, Minimum minimum, NumericInput numbers) {
        Objects.requireNonNull(minimum); Objects.requireNonNull(numbers);
        StrictJson.require(token != null && !token.isNull(), "required public uint64 value is missing or null");
        BigInteger value;
        if (token.isTextual()) {
            String text = token.textValue();
            StrictJson.require(text.matches("0|[1-9][0-9]{0,19}"), "canonical public uint64 decimal string required");
            value = new BigInteger(text);
        } else {
            StrictJson.require(numbers == NumericInput.SAFE_INTEGER_OR_DECIMAL && token.isIntegralNumber(),
                    "public uint64 requires canonical decimal text or an allowed safe integer token");
            value = token.bigIntegerValue();
            StrictJson.require(value.signum() >= 0 && value.compareTo(MAXIMUM_SAFE_NUMBER) <= 0,
                    "unsafe public numeric uint64 requires canonical decimal text");
        }
        validate(value, minimum); return value;
    }

    public static String canonical(BigInteger value, Minimum minimum) {
        validate(value, minimum); return value.toString();
    }

    private static void validate(BigInteger value, Minimum minimum) {
        Objects.requireNonNull(value); Objects.requireNonNull(minimum);
        StrictJson.require(value.signum() >= (minimum == Minimum.ONE ? 1 : 0)
                && value.compareTo(MAXIMUM) <= 0, "public uint64 is outside its declared range");
    }
}

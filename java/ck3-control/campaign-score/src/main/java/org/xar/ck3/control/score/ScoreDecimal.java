package org.xar.ck3.control.score;

import java.math.BigDecimal;
import java.math.BigInteger;
import java.math.MathContext;
import java.math.RoundingMode;
import java.util.Objects;
import org.xar.ck3.control.contracts.StrictJson;

/** Finite Python Decimal value, including the sign of zero and its exponent. */
public record ScoreDecimal(BigDecimal value, boolean negativeZero) implements Comparable<ScoreDecimal> {
    static final MathContext CONTEXT_40 = new MathContext(40, RoundingMode.HALF_EVEN);
    static final MathContext CONTEXT_80 = new MathContext(80, RoundingMode.HALF_EVEN);
    public static final ScoreDecimal ZERO = integer(0);
    public static final ScoreDecimal HUNDRED = integer(100);

    public ScoreDecimal {
        Objects.requireNonNull(value, "finite decimal required");
        StrictJson.require(!negativeZero || value.signum() == 0, "negative-zero sign requires zero value");
        // Bounded leaf ABI; this does not widen the surrounding 64 KiB JSON contract.
        StrictJson.require(value.precision() <= 8192 && Math.abs((long) value.scale()) <= 8192,
                "decimal exceeds explicit arithmetic leaf resource domain");
    }

    public static ScoreDecimal parse(String text) {
        StrictJson.require(text != null && !text.isEmpty() && text.length() <= 8192, "bounded decimal text required");
        String normalized = text.strip().replace("_", "");
        StringBuilder ascii = new StringBuilder();
        normalized.codePoints().forEach(point -> {
            int digit = Character.digit(point, 10);
            if (digit >= 0) { ascii.append((char) ('0' + digit)); }
            else { ascii.appendCodePoint(point); }
        });
        String number = ascii.toString();
        StrictJson.require(number.matches("[+-]?(?:[0-9]+(?:\\.[0-9]*)?|\\.[0-9]+)(?:[eE][+-]?[0-9]+)?"),
                "finite decimal syntax required");
        try {
            BigDecimal value = new BigDecimal(number);
            return new ScoreDecimal(value, value.signum() == 0 && number.startsWith("-"));
        } catch (NumberFormatException failure) {
            throw new org.xar.ck3.control.contracts.ContractViolationException("invalid decimal", failure);
        }
    }

    public static ScoreDecimal integer(long value) { return new ScoreDecimal(BigDecimal.valueOf(value), false); }
    public static ScoreDecimal integer(BigInteger value) { return new ScoreDecimal(new BigDecimal(value), false); }

    /** Original Python fmt: fixed fractions stripped, positive exponent preserved. */
    public String lexical() {
        String result;
        if (value.scale() > 0) {
            result = value.toPlainString();
            int end = result.length();
            while (end > 0 && result.charAt(end - 1) == '0') { end--; }
            if (end > 0 && result.charAt(end - 1) == '.') { end--; }
            result = result.substring(0, end);
        } else { result = value.toString(); }
        return negativeZero ? "-" + result : result;
    }

    @Override public int compareTo(ScoreDecimal other) { return value.compareTo(other.value); }
    @Override public boolean equals(Object other) {
        return other instanceof ScoreDecimal decimal && compareTo(decimal) == 0;
    }
    @Override public int hashCode() { return value.stripTrailingZeros().hashCode(); }
    boolean negative() { return value.signum() < 0 || negativeZero; }

    ScoreDecimal add(ScoreDecimal other, MathContext context) {
        BigDecimal result = value.add(other.value, context);
        return new ScoreDecimal(result, result.signum() == 0 && negative() && other.negative());
    }
    ScoreDecimal multiply(ScoreDecimal other, MathContext context) {
        BigDecimal result = value.multiply(other.value, context);
        return new ScoreDecimal(result, result.signum() == 0 && negative() != other.negative());
    }
    ScoreDecimal divide(ScoreDecimal other, MathContext context) {
        StrictJson.require(other.value.signum() != 0, "nonzero decimal divisor required");
        BigDecimal result = value.divide(other.value, context);
        return new ScoreDecimal(result, result.signum() == 0 && negative() != other.negative());
    }
    String fixed(int places, RoundingMode rounding) {
        StrictJson.require(places >= 0 && places <= 80, "display places outside leaf contract");
        BigDecimal result = value.setScale(places, rounding);
        StrictJson.require(result.precision() <= 80, "display quantize exceeds original Decimal80 context");
        return result.signum() == 0 && negative() ? "-" + result.toPlainString() : result.toPlainString();
    }
}

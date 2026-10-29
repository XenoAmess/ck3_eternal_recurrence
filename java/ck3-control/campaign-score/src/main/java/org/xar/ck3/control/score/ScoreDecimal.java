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
        // CPython numeric_as_ascii strips Unicode whitespace before removing
        // underscores, then transforms Unicode decimal digits/spaces. Java
        // String.strip omits NBSP/NEL. Never strip again after underscores.
        int start = 0, end = text.length();
        while (start < end && pythonSpace(text.codePointAt(start))) { start += Character.charCount(text.codePointAt(start)); }
        while (end > start && pythonSpace(text.codePointBefore(end))) { end -= Character.charCount(text.codePointBefore(end)); }
        StringBuilder ascii = new StringBuilder();
        text.substring(start, end).codePoints().forEach(point -> {
            if (point == '_') { return; }
            if (Character.getType(point) == Character.DECIMAL_DIGIT_NUMBER) {
                ascii.append((char) ('0' + Character.digit(point, 10)));
            }
            else if (point >= 128 && pythonSpace(point)) {
                ascii.append(' ');
            }
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

    private static boolean pythonSpace(int point) {
        return Character.isWhitespace(point) || Character.isSpaceChar(point) || point == 0x85;
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

    public ScoreDecimal add(ScoreDecimal other, MathContext context) {
        BigDecimal result = value.add(other.value, context);
        return new ScoreDecimal(result, result.signum() == 0 && negative() && other.negative());
    }
    public ScoreDecimal multiply(ScoreDecimal other, MathContext context) {
        BigDecimal result = value.multiply(other.value, context);
        return new ScoreDecimal(result, result.signum() == 0 && negative() != other.negative());
    }
    public ScoreDecimal divide(ScoreDecimal other, MathContext context) {
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

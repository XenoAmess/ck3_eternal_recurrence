package org.xar.ck3.control.wave2.military.forecast;

import java.math.BigInteger;

/** Python integer intermediates, with wrapping only at the original explicit x64 sites. */
public final class CombatNumbers {
    private CombatNumbers() { }
    public static final BigInteger ZERO = BigInteger.ZERO;
    public static final BigInteger ONE = BigInteger.ONE;
    public static final BigInteger SCALE = BigInteger.valueOf(100_000);
    public static final BigInteger U64_MASK = ONE.shiftLeft(64).subtract(ONE);
    public static BigInteger n(long value) { return BigInteger.valueOf(value); }
    public static BigInteger div(BigInteger numerator, BigInteger denominator) { return numerator.divide(denominator); }
    public static BigInteger mul(BigInteger left, BigInteger right) { return div(left.multiply(right), SCALE); }
    public static BigInteger fixedDiv(BigInteger numerator, BigInteger denominator) {
        return denominator.signum() == 0 ? n(-1) : div(numerator.multiply(SCALE), denominator);
    }
    public static BigInteger wrap64(BigInteger value) {
        BigInteger bits = value.and(U64_MASK);
        return bits.testBit(63) ? bits.subtract(ONE.shiftLeft(64)) : bits;
    }
    public static BigInteger clamp(BigInteger value, BigInteger lower, BigInteger upper) { return value.min(upper).max(lower); }
    public static boolean positive(BigInteger value) { return value.signum() > 0; }
    public static boolean negative(BigInteger value) { return value.signum() < 0; }
    /** Correctly rounded Python int/int binary64, including subnormals and ties. */
    public static double binary64Ratio(BigInteger numerator, BigInteger denominator) {
        if (denominator.signum() == 0) throw new ArithmeticException("integer division by zero");
        boolean negative = numerator.signum() < 0 ^ denominator.signum() < 0;
        BigInteger dividend = numerator.abs(), divisor = denominator.abs();
        long sign = negative ? Long.MIN_VALUE : 0L;
        if (dividend.signum() == 0) return Double.longBitsToDouble(sign);
        int exponent = dividend.bitLength() - divisor.bitLength();
        int comparison = exponent >= 0 ? dividend.compareTo(divisor.shiftLeft(exponent))
                : dividend.shiftLeft(-exponent).compareTo(divisor);
        if (comparison < 0) exponent--;
        if (exponent > 1023) throw new ArithmeticException("integer division result too large for a float");
        if (exponent < -1075) return Double.longBitsToDouble(sign);
        int shift = exponent < -1022 ? 1074 : 52 - exponent;
        BigInteger[] qr = shift >= 0 ? dividend.shiftLeft(shift).divideAndRemainder(divisor)
                : dividend.divideAndRemainder(divisor.shiftLeft(-shift));
        BigInteger scaledDivisor = shift >= 0 ? divisor : divisor.shiftLeft(-shift);
        int midpoint = qr[1].shiftLeft(1).compareTo(scaledDivisor);
        BigInteger rounded = midpoint > 0 || midpoint == 0 && qr[0].testBit(0) ? qr[0].add(ONE) : qr[0];
        if (exponent < -1022) return Double.longBitsToDouble(sign | rounded.longValueExact());
        if (rounded.bitLength() > 53) { rounded = rounded.shiftRight(1); exponent++; }
        if (exponent > 1023) throw new ArithmeticException("integer division result too large for a float");
        long bits = ((long) exponent + 1023) << 52 | rounded.subtract(ONE.shiftLeft(52)).longValueExact();
        return Double.longBitsToDouble(sign | bits);
    }
    public static void require(boolean value, String message) { if (!value) throw new CombatInputException(message); }
}

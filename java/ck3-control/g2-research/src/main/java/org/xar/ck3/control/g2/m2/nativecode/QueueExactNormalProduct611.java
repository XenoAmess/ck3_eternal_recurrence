package org.xar.ck3.control.g2.m2.nativecode;

import java.util.OptionalInt;

public final class QueueExactNormalProduct611 {
    private QueueExactNormalProduct611() { }

    public static OptionalInt encode(QueueFiniteProduct606.Product exact) {
        long coeff = exact.coefficient();
        int exp2 = exact.exponent2();
        boolean neg = exact.negative();

        if (coeff == 0) {
            return OptionalInt.of(neg ? 0x80000000 : 0);
        }

        int top = 63 - Long.numberOfLeadingZeros(coeff);
        int shift = Math.max(0, top - 23);
        long significand = top <= 23 ? coeff << (23 - top) : coeff >>> shift;
        long remainder = coeff & ((1L << shift) - 1);

        if (remainder != 0) {
            return OptionalInt.empty();
        }

        int exponent = top + exp2;

        if (exponent < -126 || exponent > 127) {
            return OptionalInt.empty();
        }

        int bits = (neg ? 0x80000000 : 0) | ((exponent + 127) << 23) | (int)(significand & 0x7FFFFF);
        return OptionalInt.of(bits);
    }
}
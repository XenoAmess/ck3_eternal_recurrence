package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;

public final class QueueFiniteProduct606 {
    private QueueFiniteProduct606() { }

    public record Product(boolean negative, long coefficient, int exponent2) {
        public Product {
            if (coefficient < 0 || coefficient > 0x80000000L * 0xFFFFFFL) {
                throw new IllegalArgumentException("coefficient out of range");
            }
            if (exponent2 < -149 || exponent2 > 104) {
                throw new IllegalArgumentException("exponent2 out of range");
            }
        }
    }

    public static Product multiply(long integerLeft, int factorBits) {
        if (integerLeft < -0x80000000L || integerLeft > 0x80000000L) {
            throw new IllegalArgumentException("integerLeft out of range");
        }

        int expField = (factorBits >>> 23) & 0xFF;
        if (expField == 0xFF) {
            throw new IllegalArgumentException("factorBits is not finite");
        }

        int factorSign = (factorBits >>> 31) & 1;
        int fraction = factorBits & 0x7FFFFF;

        long significand;
        int factorExponent;

        if (expField == 0) {
            significand = fraction;
            factorExponent = -149;
        } else {
            significand = 0x800000L | fraction;
            factorExponent = expField - 150;
        }

        long magnitudeLeft = integerLeft < 0 ? -integerLeft : integerLeft;
        long coefficient = magnitudeLeft * significand;
        boolean negative = (integerLeft < 0) ^ (factorSign != 0);
        int exponent2 = factorExponent;

        return new Product(negative, coefficient, exponent2);
    }
}
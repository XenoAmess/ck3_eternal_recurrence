package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;

public final class QueueFiniteTruncate607 {
    private QueueFiniteTruncate607() { }

    public sealed interface Result permits Integral, OutOfRange { }

    public record Integral(int valueBits, boolean inexact) implements Result {
        public Integral { Objects.requireNonNull(valueBits); }
    }

    public record OutOfRange() implements Result { }

    public static Result truncate(int finiteBits) {
        int sign = (finiteBits >>> 31) & 1;
        int expField = (finiteBits >>> 23) & 0xFF;
        int fraction = finiteBits & 0x7FFFFF;

        if (expField == 0xFF) {
            throw new IllegalArgumentException("Non-finite binary32");
        }

        long magnitude;
        int exponent;

        if (expField == 0) {
            if (fraction == 0) {
                return new Integral(0, false);
            }
            magnitude = fraction;
            exponent = -149;
        } else {
            magnitude = 0x800000L | fraction;
            exponent = expField - 150;
        }

        long intPart;
        boolean inexact;

        if (exponent >= 0) {
            // Check if magnitude << exponent overflows long or exceeds signed32 range
            // Max signed32 magnitude is 2^31 (for -2^31). 2^31 fits in long.
            // If exponent > 31, magnitude << exponent will definitely exceed 2^31 unless magnitude is 0 (handled above).
            // Actually, if exponent >= 32, the result is at least 2^32 which is > 2^31.
            if (exponent > 31) {
                return new OutOfRange();
            }
            // If exponent <= 31, check if magnitude << exponent fits in signed32 range
            // We need to ensure magnitude << exponent doesn't overflow long first, but since exponent <= 31 and magnitude <= 2^24,
            // magnitude << exponent <= 2^55 which fits in long.
            intPart = magnitude << exponent;
            inexact = false;
        } else {
            int shift = -exponent;
            if (shift >= 64) {
                intPart = 0;
                inexact = magnitude != 0;
            } else {
                intPart = magnitude >>> shift;
                long mask = (1L << shift) - 1;
                inexact = (magnitude & mask) != 0;
            }
        }

        // Check signed32 range
        // Positive: max 2^31 - 1 = 0x7FFFFFFF
        // Negative: min -2^31 = -0x80000000, magnitude max 0x80000000
        if (sign == 0) {
            if (intPart > 0x7FFFFFFFL) {
                return new OutOfRange();
            }
            return new Integral((int)intPart, inexact);
        } else {
            if (intPart > 0x80000000L) {
                return new OutOfRange();
            }
            return new Integral((int)(-intPart), inexact);
        }
    }
}
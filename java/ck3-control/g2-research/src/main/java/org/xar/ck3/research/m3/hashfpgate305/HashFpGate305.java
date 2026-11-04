package org.xar.ck3.research.m3.hashfpgate305;

import java.util.Objects;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueGrowthCvtdq605;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCaller153Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Registers;

/**
 * Only the held seven-instruction block [C39CF4,C39D11).
 * Zero divisors and NaN/subnormal thresholds are explicit software boundaries.
 * A condition snapshot does not establish native exception delivery or full Hash188.
 */
public final class HashFpGate305 {
    private HashFpGate305() { }

    public record Input(QueueFp604Api.Input base, long originCallSiteRva) {
        public Input { Objects.requireNonNull(base); }
    }

    /** Ordered COMISS relation: PF=0; CF is LESS and ZF is EQUAL. */
    public enum Relation { LESS, EQUAL, GREATER }

    public sealed interface Result permits Continued, NotCompleted { }

    public record Continued(QueueFp604Api.Snapshot snapshot, Relation relation) implements Result {
        public Continued {
            Objects.requireNonNull(snapshot);
            Objects.requireNonNull(relation);
            long expected = relation == Relation.GREATER ? 0xC39F28L : 0xC39D11L;
            if (snapshot.instructionRva() != expected) {
                throw new IllegalArgumentException("Continuation does not match JA");
            }
        }
    }

    public record NotCompleted(QueueFp604Api.Stopped stopped) implements Result {
        public NotCompleted { Objects.requireNonNull(stopped); }
    }

    public static Result execute(Input input, GovernmentCaller153Api.Memory memory) {
        Objects.requireNonNull(input);
        var base = input.base();
        var entry = base.base().entry();
        long image = entry.imageBaseBits();
        boolean df = base.base().directionFlagSet();
        long origin = input.originCallSiteRva();
        QueueFp604Api.Mxcsr state = base.mxcsr();
        Registers r = registers(entry);

        // CF4, then CF8. MOVD commits before any conversion qualification stop.
        r.x0 = movd(r.rcx);
        var first = QueueGrowthCvtdq605.execute(image, r, df, state, origin);
        if (first instanceof QueueGrowthCvtdq605.NotCompleted stopped) {
            return conversionStop(image, r, df, 0xC39CF8L, stopped.stopped());
        }
        state = ((QueueGrowthCvtdq605.Completed) first).mxcsr();

        // CFB, then CFF. The private kernel bank is an operand remapping only.
        r.x1 = movd(r.rax);
        Registers kernel = registers(current(image, r));
        kernel.x0 = r.x1;
        var second = QueueGrowthCvtdq605.execute(image, kernel, df, state, origin);
        if (second instanceof QueueGrowthCvtdq605.NotCompleted stopped) {
            return conversionStop(image, r, df, 0xC39CFFL, stopped.stopped());
        }
        r.x1 = kernel.x0;
        state = ((QueueGrowthCvtdq605.Completed) second).mxcsr();

        // D02 operands are finite integer-valued binary32 scalars from the two CVTs.
        int denominatorBits = (int) r.x0.lowBits();
        int numeratorBits = (int) r.x1.lowBits();
        long denominator = integerMagnitude(denominatorBits);
        long numerator = integerMagnitude(numeratorBits);
        if (denominator == 0) {
            return stop(image, r, df, state, 0xC39D02L, origin,
                    QueueFp604Api.StopReason.UNSUPPORTED_FP_DOMAIN, 0);
        }

        int sign = (numeratorBits ^ denominatorBits) & 0x80000000;
        int resultBits;
        if (numerator == 0) {
            resultBits = sign;
        } else {
            int exponent = (63 - Long.numberOfLeadingZeros(numerator))
                    - (63 - Long.numberOfLeadingZeros(denominator));
            if (exponent >= 0) {
                if (numerator < (denominator << exponent)) exponent--;
            } else if ((numerator << -exponent) < denominator) {
                exponent--;
            }

            // In this source domain these scaled positive integers fit within 55 bits.
            int shift = 23 - exponent;
            long scaledNumerator = shift >= 0 ? numerator << shift : numerator;
            long scaledDenominator = shift < 0 ? denominator << -shift : denominator;
            long significand = scaledNumerator / scaledDenominator;
            long remainder = scaledNumerator % scaledDenominator;

            if (remainder != 0) {
                if ((state.knownMaskBits() & 0x1000) == 0) {
                    return stop(image, r, df, state, 0xC39D02L, origin,
                            QueueFp604Api.StopReason.MISSING_FP_INPUT, 0);
                }
                var post = new QueueFp604Api.Mxcsr(
                        state.valueBits() | 0x20, state.knownMaskBits() | 0x20);
                if ((state.valueBits() & 0x1000) == 0) {
                    return stop(image, r, df, post, 0xC39D02L, origin,
                            QueueFp604Api.StopReason.ARCHITECTURAL_FP_CONDITION, 0x20);
                }
                if ((state.knownMaskBits() & 0x6000) != 0x6000) {
                    // Conservative declared policy: no partial execution/PE commit here.
                    return stop(image, r, df, state, 0xC39D02L, origin,
                            QueueFp604Api.StopReason.MISSING_FP_INPUT, 0);
                }
                int rounding = (state.valueBits() >>> 13) & 3;
                boolean increment = switch (rounding) {
                    case 0 -> remainder * 2 > scaledDenominator
                            || (remainder * 2 == scaledDenominator && (significand & 1) != 0);
                    case 1 -> sign != 0;
                    case 2 -> sign == 0;
                    default -> false;
                };
                if (increment) significand++;
                state = post;
            }
            if (significand == (1L << 24)) {
                significand >>>= 1;
                exponent++;
            }
            resultBits = sign | ((exponent + 127) << 23) | ((int) significand & 0x7FFFFF);
        }

        // DIVSS commits only the low DWORD; successful CFF already established upper96.
        r.x1 = new Bits128((r.x1.lowBits() & 0xFFFFFFFF00000000L)
                | Integer.toUnsignedLong(resultBits), r.x1.highBits());

        // D06: one fresh operand fetch, after the committed FP prefix. No catch or retry.
        int threshold = Objects.requireNonNull(memory).readDword(r.r14 + 0x1CL);
        int absolute = threshold & 0x7FFFFFFF;
        int thresholdExponent = absolute >>> 23;
        int thresholdFraction = absolute & 0x7FFFFF;
        if ((thresholdExponent == 0 && thresholdFraction != 0)
                || (thresholdExponent == 0xFF && thresholdFraction != 0)) {
            return stop(image, r, df, state, 0xC39D06L, origin,
                    QueueFp604Api.StopReason.UNSUPPORTED_FP_DOMAIN, 0);
        }
        Relation relation = compareOrdered(resultBits, threshold);
        long continuation = relation == Relation.GREATER ? 0xC39F28L : 0xC39D11L;
        return new Continued(new QueueFp604Api.Snapshot(
                current(image, r), continuation, df, state), relation);
    }

    private static Bits128 movd(long source) {
        return new Bits128(Integer.toUnsignedLong((int) source), 0);
    }

    private static Registers registers(GovernmentCrtBoundary185Api.Entry entry) {
        return GovernmentCallee164Api.registers(new GovernmentCallee164Api.Entry(
                entry.imageBaseBits(), entry.rspBits(), entry.volatileBits(), entry.nonvolatileBits()));
    }

    private static GovernmentCrtBoundary185Api.Entry current(long image, Registers r) {
        return new GovernmentCrtBoundary185Api.Entry(
                image, r.rsp, r.volatileBits(), r.nonvolatileBits());
    }

    private static NotCompleted conversionStop(long image, Registers real, boolean df,
            long pc, QueueFp604Api.Stopped kernelStop) {
        return stop(image, real, df, kernelStop.snapshot().mxcsr(), pc,
                kernelStop.originCallSiteRva(), kernelStop.reason(), kernelStop.raisedConditionBits());
    }

    private static NotCompleted stop(long image, Registers r, boolean df,
            QueueFp604Api.Mxcsr state, long pc, long origin,
            QueueFp604Api.StopReason reason, int conditions) {
        return new NotCompleted(new QueueFp604Api.Stopped(reason,
                new QueueFp604Api.Snapshot(current(image, r), pc, df, state), conditions, origin));
    }

    /** The successful signed-DWORD conversion domain guarantees zero or an integer magnitude <=2^31. */
    private static long integerMagnitude(int bits) {
        int absolute = bits & 0x7FFFFFFF;
        if (absolute == 0) return 0;
        int exponent = (absolute >>> 23) - 127;
        long significand = 0x800000L | (absolute & 0x7FFFFF);
        return exponent >= 23 ? significand << (exponent - 23) : significand >>> (23 - exponent);
    }

    /** Caller has excluded NaN/subnormal thresholds and the quotient is normal finite or signed zero. */
    private static Relation compareOrdered(int left, int right) {
        int leftAbsolute = left & 0x7FFFFFFF;
        int rightAbsolute = right & 0x7FFFFFFF;
        if ((leftAbsolute == 0 && rightAbsolute == 0) || left == right) return Relation.EQUAL;
        if ((left < 0) != (right < 0)) return left < 0 ? Relation.LESS : Relation.GREATER;
        int comparison = Integer.compareUnsigned(leftAbsolute, rightAbsolute);
        if (left < 0) comparison = -comparison;
        return comparison < 0 ? Relation.LESS : comparison > 0 ? Relation.GREATER : Relation.EQUAL;
    }
}

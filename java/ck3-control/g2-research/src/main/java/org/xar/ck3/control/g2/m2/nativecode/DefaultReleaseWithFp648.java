package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.study.m6.full224.DefaultObject185Wrappers224;

/** Explicit FP/DF carrier for only the held 14-byte normal body at 8571C0. */
public final class DefaultReleaseWithFp648 {
    private DefaultReleaseWithFp648() { }

    private static final class StoppedCarrier extends RuntimeException {
        private static final long serialVersionUID = 1L;
        private transient final QueueFp604Api.Stopped outcome;

        private StoppedCarrier(QueueFp604Api.Stopped outcome) {
            super(null, null, false, false);
            this.outcome = outcome;
        }
    }

    /** Reuses old224 once; a reached foreign tail owns its complete outcome. */
    public static QueueFp604Api.Outcome fromSlot10(
            DefaultStaticFp648Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory,
            DefaultStaticFp648Api.Calls calls) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);

        final QueueFp604Api.Normal[] tailNormal = new QueueFp604Api.Normal[1];
        GovernmentCrtBoundary185Api.Calls bridge = new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(
                    GovernmentCrtBoundary185Api.Call call) {
                throw new UnsupportedOperationException("No CALL in held8571C0");
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(
                    GovernmentCrtBoundary185Api.Tail transfer) {
                DefaultStaticFp648Api.TailFrame frame = new DefaultStaticFp648Api.TailFrame(
                        transfer, input.directionFlagSet(), input.mxcsr());
                QueueFp604Api.Outcome outcome = Objects.requireNonNull(calls).tail(frame);
                if (outcome instanceof QueueFp604Api.Normal normal) {
                    tailNormal[0] = normal;
                    return normal.base().normalReturn();
                }
                if (outcome instanceof QueueFp604Api.Stopped stopped) {
                    throw new StoppedCarrier(stopped);
                }
                throw new NullPointerException("Null tail outcome");
            }

            @Override
            public long readGsQword58() {
                throw new UnsupportedOperationException("No GS read in held8571C0");
            }
        };

        try {
            GovernmentCrtBoundary185Api.NormalReturn oldNormal =
                    DefaultObject185Wrappers224.fromSlot10(input.entry(), memory, bridge);
            if (tailNormal[0] != null) {
                return tailNormal[0];
            }
            return new QueueFp604Api.Normal(
                    new FullCopy437Api.CallResult(oldNormal, input.directionFlagSet()),
                    input.mxcsr());
        } catch (StoppedCarrier stopped) {
            return stopped.outcome;
        }
    }
}

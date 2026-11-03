package org.xar.ck3.control.g2.m2.nativecode;

import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.control.g2.m2.nativecode.QueueFp604Api;
import org.xar.ck3.control.g2.m2.nativecode.DefaultStaticFp648Api;
import org.xar.ck3.control.g2.m2.nativecode.KnownHeapAllocateFp623;
import org.xar.ck3.research.m4.Allocate94FullState282;

public final class Allocate94EntryFp650 {
    private Allocate94EntryFp650() { }

    private static final class StoppedCarrier extends RuntimeException {
        private static final long serialVersionUID = 1L;
        transient final QueueFp604Api.Stopped outcome;

        StoppedCarrier(QueueFp604Api.Stopped outcome) {
            super(null, null, false, false);
            this.outcome = outcome;
        }
    }

    public static QueueFp604Api.Outcome execute(
            DefaultStaticFp648Api.Input input,
            GovernmentCrtBoundary185Api.Memory memory,
            KnownHeapAllocateFp623.AllocateCalls calls,
            GovernmentCrtBoundary185Api.LoopBudget budget) {
        Objects.requireNonNull(input);
        Objects.requireNonNull(memory);
        Objects.requireNonNull(calls);
        Objects.requireNonNull(budget);

        final boolean[] currentDF = new boolean[1];
        currentDF[0] = input.directionFlagSet();
        final QueueFp604Api.Mxcsr[] currentFP = new QueueFp604Api.Mxcsr[1];
        currentFP[0] = input.mxcsr();

        GovernmentCrtBoundary185Api.Calls narrowCalls = new GovernmentCrtBoundary185Api.Calls() {
            @Override
            public GovernmentPrimaryTail155Api.VolatileBits invoke(GovernmentCrtBoundary185Api.Call call) {
                Objects.requireNonNull(call);

                long imageBase = input.entry().imageBaseBits();
                long childRsp = call.rspBits() - 8L;
                GovernmentCrtBoundary185Api.Entry childEntry = new GovernmentCrtBoundary185Api.Entry(
                        imageBase, childRsp, call.volatileBits(), call.nonvolatileBits());

                KnownHeapAllocateFp623.AllocateCall allocateFrame = new KnownHeapAllocateFp623.AllocateCall(
                        call, childEntry, currentDF[0], currentFP[0]);

                QueueFp604Api.Outcome outcome = calls.invoke(allocateFrame);
                if (outcome == null) {
                    throw new NullPointerException("Null outcome from AllocateCalls");
                }

                if (outcome instanceof QueueFp604Api.Normal normal) {
                    allocateFrame.checkNormalReturn(normal.base());
                    currentDF[0] = normal.base().postDirectionFlagSet();
                    currentFP[0] = normal.postMxcsr();
                    return normal.base().normalReturn().volatileBits();
                } else if (outcome instanceof QueueFp604Api.Stopped stopped) {
                    throw new StoppedCarrier(stopped);
                } else {
                    throw new IllegalStateException("Unknown outcome type");
                }
            }

            @Override
            public GovernmentCrtBoundary185Api.NormalReturn tail(GovernmentCrtBoundary185Api.Tail transfer) {
                throw new UnsupportedOperationException("Tail not expected in Allocate94EntryFp650");
            }

            @Override
            public long readGsQword58() {
                throw new UnsupportedOperationException("GS read not expected in Allocate94EntryFp650");
            }
        };

        try {
            GovernmentCrtBoundary185Api.NormalReturn nr = Allocate94FullState282.execute(
                    input.entry(), memory, narrowCalls, budget);

            FullCopy437Api.CallResult baseResult = new FullCopy437Api.CallResult(nr, currentDF[0]);
            return new QueueFp604Api.Normal(baseResult, currentFP[0]);
        } catch (StoppedCarrier e) {
            return e.outcome;
        }
    }
}